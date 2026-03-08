"""
Spring Boot Bean Extractor v1.0

Extracts Spring Boot bean definitions, configurations, profiles, and conditions.
Covers Spring Boot 1.x through 3.x patterns.

Extracts:
- @Component, @Service, @Repository, @Controller, @RestController beans
- @Configuration classes with @Bean factory methods
- @Profile annotations and conditional beans
- @ConditionalOn* conditions (class, property, bean, missing, etc.)
- Bean scopes (@Scope, @RequestScope, @SessionScope)
- Lifecycle callbacks (@PostConstruct, @PreDestroy)
- Import configurations (@Import, @ImportResource)

Part of CodeTrellis v4.94 - Spring Boot Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class SpringBootBeanInfo:
    """A Spring-managed bean (component, service, repository, controller)."""
    name: str
    bean_type: str = ""  # component, service, repository, controller, rest_controller
    scope: str = "singleton"  # singleton, prototype, request, session
    profiles: List[str] = field(default_factory=list)
    qualifiers: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    extends: str = ""
    has_constructor_injection: bool = False
    injected_dependencies: List[str] = field(default_factory=list)
    lifecycle_callbacks: List[str] = field(default_factory=list)  # postConstruct, preDestroy
    is_primary: bool = False
    is_lazy: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootConfigurationInfo:
    """A @Configuration class."""
    name: str
    is_proxy: bool = True  # @Configuration(proxyBeanMethods=true)
    imports: List[str] = field(default_factory=list)  # @Import classes
    import_resources: List[str] = field(default_factory=list)  # @ImportResource
    component_scans: List[str] = field(default_factory=list)  # @ComponentScan base packages
    profiles: List[str] = field(default_factory=list)
    property_sources: List[str] = field(default_factory=list)  # @PropertySource
    bean_methods: List[str] = field(default_factory=list)  # names of @Bean methods
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootBeanMethodInfo:
    """A @Bean factory method inside a @Configuration class."""
    name: str
    return_type: str = ""
    bean_name: str = ""  # explicit @Bean("name") or method name
    init_method: str = ""
    destroy_method: str = ""
    scope: str = "singleton"
    profiles: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    is_primary: bool = False
    annotations: List[str] = field(default_factory=list)
    config_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootProfileInfo:
    """Profile-specific configuration."""
    profile_name: str
    target_type: str = ""  # class, method, bean
    target_name: str = ""
    is_negated: bool = False  # @Profile("!test")
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootConditionInfo:
    """@ConditionalOn* condition."""
    condition_type: str = ""  # onClass, onMissingClass, onProperty, onBean, onMissingBean, etc.
    value: str = ""
    target_name: str = ""
    file: str = ""
    line_number: int = 0


class SpringBootBeanExtractor:
    """Extracts Spring Boot bean definitions, configurations, and DI patterns."""

    # Stereotype annotations
    STEREOTYPE_PATTERN = re.compile(
        r'@(Component|Service|Repository|Controller|RestController)'
        r'(?:\(\s*(?:"([^"]*)")?\s*\))?\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    # Configuration class
    CONFIG_PATTERN = re.compile(
        r'@Configuration'
        r'(?:\(\s*proxyBeanMethods\s*=\s*(true|false)\s*\))?\s*\n'
        r'((?:@\w+(?:\([^)]*\))?\s*\n)*)'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    # @Bean method
    BEAN_METHOD_PATTERN = re.compile(
        r'((?:[ \t]*@\w+(?:\([^)]*\))?\s*\n)*)'
        r'[ \t]*@Bean'
        r'(?:\(\s*(?:name\s*=\s*)?(?:"([^"]*)"|\{[^}]*\})?\s*'
        r'(?:,\s*initMethod\s*=\s*"([^"]*)")?\s*'
        r'(?:,\s*destroyMethod\s*=\s*"([^"]*)")?\s*\))?\s*\n'
        r'(?:[ \t]*@\w+(?:\([^)]*\))?\s*\n)*'
        r'[ \t]*(?:public\s+)?(\w[\w<>,\s?]*?)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # Profile
    PROFILE_PATTERN = re.compile(
        r'@Profile\(\s*(?:"([^"]*)"|\{([^}]*)\})\s*\)',
        re.MULTILINE
    )

    # Scope
    SCOPE_PATTERN = re.compile(
        r'@(Scope|RequestScope|SessionScope|ApplicationScope)'
        r'(?:\(\s*(?:"([^"]*)")?\s*\))?',
        re.MULTILINE
    )

    # Conditional annotations
    CONDITIONAL_PATTERN = re.compile(
        r'@Conditional(OnClass|OnMissingClass|OnBean|OnMissingBean|'
        r'OnProperty|OnResource|OnExpression|OnWebApplication|'
        r'OnNotWebApplication|OnCloudPlatform|OnJava|OnJndi|'
        r'OnSingleCandidate|OnWarDeployment)'
        r'\(\s*(?:name\s*=\s*)?(?:"([^"]*)"|\{[^}]*\}|[^)]*)\s*\)',
        re.MULTILINE
    )

    # Constructor injection
    CONSTRUCTOR_INJECTION_PATTERN = re.compile(
        r'(?:@Autowired\s+)?(?:public\s+)?(\w+)\s*\(\s*'
        r'((?:(?:@\w+(?:\([^)]*\))?\s+)?(?:final\s+)?[\w<>,\s?]+\s+\w+\s*,?\s*)+)\)',
        re.MULTILINE
    )

    # @Autowired field injection
    FIELD_INJECTION_PATTERN = re.compile(
        r'@Autowired\s+(?:@\w+(?:\([^)]*\))?\s+)*'
        r'(?:private|protected)?\s*(?:final\s+)?([\w<>,?]+)\s+(\w+)\s*;',
        re.MULTILINE
    )

    # @Value injection
    VALUE_INJECTION_PATTERN = re.compile(
        r'@Value\(\s*"([^"]*)"\s*\)\s+(?:private|protected)?\s*(?:final\s+)?([\w<>,?]+)\s+(\w+)',
        re.MULTILINE
    )

    # Qualifier
    QUALIFIER_PATTERN = re.compile(
        r'@Qualifier\(\s*"([^"]*)"\s*\)',
        re.MULTILINE
    )

    # Lifecycle
    LIFECYCLE_PATTERN = re.compile(
        r'@(PostConstruct|PreDestroy)\s+(?:public\s+)?void\s+(\w+)',
        re.MULTILINE
    )

    # @Primary, @Lazy
    PRIMARY_PATTERN = re.compile(r'@Primary\b')
    LAZY_PATTERN = re.compile(r'@Lazy\b')

    # DependsOn
    DEPENDS_ON_PATTERN = re.compile(
        r'@DependsOn\(\s*(?:"([^"]*)"|\{([^}]*)\})\s*\)',
        re.MULTILINE
    )

    # Import
    IMPORT_PATTERN = re.compile(
        r'@Import\(\s*(?:\{([^}]*)\}|(\w+(?:\.\w+)*\.class))\s*\)',
        re.MULTILINE
    )

    # ImportResource
    IMPORT_RESOURCE_PATTERN = re.compile(
        r'@ImportResource\(\s*(?:"([^"]*)"|\{([^}]*)\})\s*\)',
        re.MULTILINE
    )

    # ComponentScan
    COMPONENT_SCAN_PATTERN = re.compile(
        r'@ComponentScan\(\s*(?:basePackages\s*=\s*)?(?:"([^"]*)"|\{([^}]*)\})\s*\)',
        re.MULTILINE
    )

    # PropertySource
    PROPERTY_SOURCE_PATTERN = re.compile(
        r'@PropertySource\(\s*(?:value\s*=\s*)?(?:"([^"]*)"|\{([^}]*)\})\s*\)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all Spring Boot bean definitions from Java source code."""
        result: Dict[str, Any] = {
            'beans': [],
            'configurations': [],
            'bean_methods': [],
            'profiles': [],
            'conditions': [],
        }

        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract stereotype beans
        for match in self.STEREOTYPE_PATTERN.finditer(content):
            stereotype = match.group(1).lower()
            bean_name_explicit = match.group(2) or ""
            class_name = match.group(3)

            bean_type_map = {
                'component': 'component',
                'service': 'service',
                'repository': 'repository',
                'controller': 'controller',
                'restcontroller': 'rest_controller',
            }

            # Get annotations preceding the class
            context_start = max(0, match.start() - 500)
            context = content[context_start:match.end()]

            profiles = self._extract_profiles(context)
            scope = self._extract_scope(context)
            is_primary = bool(self.PRIMARY_PATTERN.search(context))
            is_lazy = bool(self.LAZY_PATTERN.search(context))
            qualifiers = [m.group(1) for m in self.QUALIFIER_PATTERN.finditer(context)]
            depends_on = self._extract_depends_on(context)
            lifecycle = [(m.group(1), m.group(2)) for m in self.LIFECYCLE_PATTERN.finditer(content)]

            # Extract constructor injection
            has_ctor_injection = False
            injected_deps = []
            ctor_match = self.CONSTRUCTOR_INJECTION_PATTERN.search(content)
            if ctor_match and ctor_match.group(1) == class_name:
                has_ctor_injection = True
                params_text = ctor_match.group(2)
                for param in re.finditer(r'([\w<>,?]+)\s+(\w+)', params_text):
                    injected_deps.append(param.group(1))

            # Field injection
            for fm in self.FIELD_INJECTION_PATTERN.finditer(content):
                injected_deps.append(fm.group(1))

            bean = SpringBootBeanInfo(
                name=class_name,
                bean_type=bean_type_map.get(stereotype, 'component'),
                scope=scope,
                profiles=profiles,
                qualifiers=qualifiers,
                depends_on=depends_on,
                annotations=[stereotype.capitalize()],
                has_constructor_injection=has_ctor_injection,
                injected_dependencies=injected_deps,
                lifecycle_callbacks=[f"{cb[0]}:{cb[1]}" for cb in lifecycle],
                is_primary=is_primary,
                is_lazy=is_lazy,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            )
            result['beans'].append(bean)

        # Extract configurations
        for match in self.CONFIG_PATTERN.finditer(content):
            proxy = match.group(1) != 'false' if match.group(1) else True
            between_anns = match.group(2) or ""
            class_name = match.group(3)

            context_start = max(0, match.start() - 500)
            context = content[context_start:match.end()]

            profiles = self._extract_profiles(context)
            imports = self._extract_imports(context)
            import_resources = self._extract_import_resources(context)
            comp_scans = self._extract_component_scans(context)
            prop_sources = self._extract_property_sources(context)

            # Find bean methods in this config class
            bean_names = []
            for bm in self.BEAN_METHOD_PATTERN.finditer(content):
                bean_names.append(bm.group(6))

            config = SpringBootConfigurationInfo(
                name=class_name,
                is_proxy=proxy,
                imports=imports,
                import_resources=import_resources,
                component_scans=comp_scans,
                profiles=profiles,
                property_sources=prop_sources,
                bean_methods=bean_names,
                annotations=['Configuration'],
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            )
            result['configurations'].append(config)

        # Extract @Bean methods
        for match in self.BEAN_METHOD_PATTERN.finditer(content):
            preceding_anns = match.group(1) or ""
            bean_name = match.group(2) or match.group(6)
            init_method = match.group(3) or ""
            destroy_method = match.group(4) or ""
            return_type = match.group(5).strip()
            method_name = match.group(6)

            context = preceding_anns
            profiles = self._extract_profiles(context)
            conditions = [m.group(1) for m in self.CONDITIONAL_PATTERN.finditer(context)]
            is_primary = bool(self.PRIMARY_PATTERN.search(context))
            scope = self._extract_scope(context)

            bm = SpringBootBeanMethodInfo(
                name=method_name,
                return_type=return_type,
                bean_name=bean_name,
                init_method=init_method,
                destroy_method=destroy_method,
                scope=scope,
                profiles=profiles,
                conditions=conditions,
                is_primary=is_primary,
                annotations=['Bean'],
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            )
            result['bean_methods'].append(bm)

        # Extract profiles
        for match in self.PROFILE_PATTERN.finditer(content):
            profile_val = match.group(1) or match.group(2)
            if profile_val:
                for p in re.findall(r'"?(!?\w+)"?', profile_val):
                    is_negated = p.startswith('!')
                    pname = p.lstrip('!')
                    result['profiles'].append(SpringBootProfileInfo(
                        profile_name=pname,
                        is_negated=is_negated,
                        file=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                    ))

        # Extract conditions
        for match in self.CONDITIONAL_PATTERN.finditer(content):
            cond_type = match.group(1)
            value = match.group(2) or ""
            result['conditions'].append(SpringBootConditionInfo(
                condition_type=f"on{cond_type}",
                value=value,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return result

    def _extract_profiles(self, text: str) -> List[str]:
        profiles = []
        for m in self.PROFILE_PATTERN.finditer(text):
            val = m.group(1) or m.group(2)
            if val:
                for p in re.findall(r'"?(!?\w+)"?', val):
                    profiles.append(p)
        return profiles

    def _extract_scope(self, text: str) -> str:
        m = self.SCOPE_PATTERN.search(text)
        if m:
            if m.group(1) == 'RequestScope':
                return 'request'
            elif m.group(1) == 'SessionScope':
                return 'session'
            elif m.group(1) == 'ApplicationScope':
                return 'application'
            elif m.group(2):
                return m.group(2)
        return 'singleton'

    def _extract_depends_on(self, text: str) -> List[str]:
        deps = []
        for m in self.DEPENDS_ON_PATTERN.finditer(text):
            val = m.group(1) or m.group(2)
            if val:
                for d in re.findall(r'"(\w+)"', val):
                    deps.append(d)
        return deps

    def _extract_imports(self, text: str) -> List[str]:
        imports = []
        for m in self.IMPORT_PATTERN.finditer(text):
            val = m.group(1) or m.group(2)
            if val:
                for i in re.findall(r'(\w+)\.class', val):
                    imports.append(i)
        return imports

    def _extract_import_resources(self, text: str) -> List[str]:
        resources = []
        for m in self.IMPORT_RESOURCE_PATTERN.finditer(text):
            val = m.group(1) or m.group(2)
            if val:
                for r_val in re.findall(r'"([^"]*)"', val):
                    resources.append(r_val)
        return resources

    def _extract_component_scans(self, text: str) -> List[str]:
        scans = []
        for m in self.COMPONENT_SCAN_PATTERN.finditer(text):
            val = m.group(1) or m.group(2)
            if val:
                for s in re.findall(r'"([^"]*)"', val):
                    scans.append(s)
        return scans

    def _extract_property_sources(self, text: str) -> List[str]:
        sources = []
        for m in self.PROPERTY_SOURCE_PATTERN.finditer(text):
            val = m.group(1) or m.group(2)
            if val:
                for s in re.findall(r'"([^"]*)"', val):
                    sources.append(s)
        return sources
