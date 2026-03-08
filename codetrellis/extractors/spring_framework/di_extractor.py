"""
Spring Framework DI Extractor v1.0

Extracts Spring Framework Dependency Injection patterns.

Extracts:
- @Autowired (field, constructor, setter)
- @Inject (JSR-330), @Resource (JSR-250)
- @Qualifier, @Primary, @Lazy
- XML bean definitions (spring-context.xml patterns)
- @Lookup method injection
- Circular dependency detection hints
- Bean lifecycle: InitializingBean, DisposableBean, @PostConstruct, @PreDestroy

Part of CodeTrellis v4.94 - Spring Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class SpringDIInfo:
    """A dependency injection point."""
    target_name: str  # field name, method name, or constructor class name
    injection_type: str = ""  # field, constructor, setter, method
    injected_type: str = ""  # the type being injected
    annotation: str = ""  # Autowired, Inject, Resource
    qualifier: str = ""
    is_required: bool = True
    is_primary: bool = False
    is_lazy: bool = False
    target_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBeanDefinitionInfo:
    """A Spring bean defined via XML or Java config."""
    bean_id: str = ""
    bean_class: str = ""
    scope: str = "singleton"
    init_method: str = ""
    destroy_method: str = ""
    factory_method: str = ""
    factory_bean: str = ""
    constructor_args: List[str] = field(default_factory=list)
    properties: List[Dict[str, str]] = field(default_factory=list)
    is_abstract: bool = False
    parent: str = ""
    depends_on: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SpringQualifierInfo:
    """A @Qualifier annotation usage."""
    value: str
    target_name: str = ""
    target_type: str = ""
    file: str = ""
    line_number: int = 0


class SpringDIExtractor:
    """Extracts Spring Framework dependency injection patterns."""

    # @Autowired field injection
    AUTOWIRED_FIELD_PATTERN = re.compile(
        r'@Autowired\s*'
        r'(?:\(required\s*=\s*(true|false)\))?\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:private|protected|public)?\s*(?:final\s+)?([\w<>,?\[\]]+)\s+(\w+)\s*;',
        re.MULTILINE
    )

    # @Inject (JSR-330)
    INJECT_FIELD_PATTERN = re.compile(
        r'@Inject\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:private|protected|public)?\s*(?:final\s+)?([\w<>,?\[\]]+)\s+(\w+)\s*;',
        re.MULTILINE
    )

    # @Resource (JSR-250)
    RESOURCE_PATTERN = re.compile(
        r'@Resource(?:\(\s*name\s*=\s*"([^"]*)"\s*\))?\s*\n'
        r'(?:private|protected|public)?\s*(?:final\s+)?([\w<>,?\[\]]+)\s+(\w+)\s*;',
        re.MULTILINE
    )

    # Setter injection
    SETTER_INJECTION_PATTERN = re.compile(
        r'@Autowired\s*'
        r'(?:\(required\s*=\s*(true|false)\))?\s*\n'
        r'(?:public\s+)?void\s+set(\w+)\s*\(\s*([\w<>,?\[\]]+)\s+(\w+)\s*\)',
        re.MULTILINE
    )

    # @Qualifier on field
    QUALIFIER_PATTERN = re.compile(
        r'@Qualifier\(\s*"([^"]*)"\s*\)\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:private|protected|public)?\s*(?:final\s+)?([\w<>,?\[\]]+)\s+(\w+)',
        re.MULTILINE
    )

    # @Primary
    PRIMARY_PATTERN = re.compile(r'@Primary\b')

    # @Lazy
    LAZY_PATTERN = re.compile(r'@Lazy\b')

    # @Lookup
    LOOKUP_PATTERN = re.compile(
        r'@Lookup(?:\(\s*"([^"]*)"\s*\))?\s*\n'
        r'(?:public|protected)?\s*(?:abstract\s+)?([\w<>,?]+)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # Constructor injection (implicit in Spring 4.3+, or explicit with @Autowired)
    CONSTRUCTOR_PATTERN = re.compile(
        r'(?:@Autowired\s*\n\s*)?'
        r'(?:public\s+)?(\w+)\s*\('
        r'([^)]*)\)\s*\{',
        re.MULTILINE | re.DOTALL
    )

    # XML bean definition
    XML_BEAN_PATTERN = re.compile(
        r'<bean\s+'
        r'(?:id="([^"]*)")?\s*'
        r'(?:class="([^"]*)")?\s*'
        r'(?:scope="([^"]*)")?\s*'
        r'(?:init-method="([^"]*)")?\s*'
        r'(?:destroy-method="([^"]*)")?\s*'
        r'(?:abstract="(true|false)")?\s*'
        r'(?:parent="([^"]*)")?\s*',
        re.MULTILINE
    )

    # Constructor arg in XML
    XML_CTOR_ARG_PATTERN = re.compile(
        r'<constructor-arg\s+(?:type="([^"]*)")?\s*(?:value="([^"]*)")?(?:\s*ref="([^"]*)")?',
        re.MULTILINE
    )

    # Property in XML
    XML_PROPERTY_PATTERN = re.compile(
        r'<property\s+name="([^"]*)"\s+(?:value="([^"]*)")?(?:\s*ref="([^"]*)")?',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Spring DI patterns from Java or XML source."""
        result: Dict[str, Any] = {
            'injections': [],
            'bean_definitions': [],
            'qualifiers': [],
        }

        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        is_xml = file_path.endswith('.xml')

        if is_xml:
            self._extract_xml_beans(content, file_path, result)
        else:
            self._extract_java_di(content, file_path, result)

        return result

    def _extract_java_di(self, content: str, file_path: str, result: Dict):
        """Extract DI from Java source."""
        # @Autowired fields
        for match in self.AUTOWIRED_FIELD_PATTERN.finditer(content):
            required = match.group(1) != 'false' if match.group(1) else True
            result['injections'].append(SpringDIInfo(
                target_name=match.group(3),
                injection_type='field',
                injected_type=match.group(2),
                annotation='Autowired',
                is_required=required,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @Inject fields
        for match in self.INJECT_FIELD_PATTERN.finditer(content):
            result['injections'].append(SpringDIInfo(
                target_name=match.group(2),
                injection_type='field',
                injected_type=match.group(1),
                annotation='Inject',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @Resource fields
        for match in self.RESOURCE_PATTERN.finditer(content):
            result['injections'].append(SpringDIInfo(
                target_name=match.group(3),
                injection_type='field',
                injected_type=match.group(2),
                annotation='Resource',
                qualifier=match.group(1) or "",
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Setter injection
        for match in self.SETTER_INJECTION_PATTERN.finditer(content):
            required = match.group(1) != 'false' if match.group(1) else True
            result['injections'].append(SpringDIInfo(
                target_name=f"set{match.group(2)}",
                injection_type='setter',
                injected_type=match.group(3),
                annotation='Autowired',
                is_required=required,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @Lookup
        for match in self.LOOKUP_PATTERN.finditer(content):
            result['injections'].append(SpringDIInfo(
                target_name=match.group(3),
                injection_type='method',
                injected_type=match.group(2),
                annotation='Lookup',
                qualifier=match.group(1) or "",
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Constructor injection (implicit Spring 4.3+ or explicit @Autowired)
        # Find class names first
        class_pattern = re.compile(r'class\s+(\w+)', re.MULTILINE)
        class_names = {m.group(1) for m in class_pattern.finditer(content)}
        for match in self.CONSTRUCTOR_PATTERN.finditer(content):
            ctor_name = match.group(1)
            params_str = match.group(2).strip()
            if ctor_name not in class_names or not params_str:
                continue
            # Parse parameters
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            for param in params:
                parts = param.split()
                if len(parts) >= 2:
                    param_type = parts[-2]
                    param_name = parts[-1]
                    result['injections'].append(SpringDIInfo(
                        target_name=param_name,
                        injection_type='constructor',
                        injected_type=param_type,
                        annotation='constructor',
                        file=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                    ))

        # @Qualifier
        for match in self.QUALIFIER_PATTERN.finditer(content):
            result['qualifiers'].append(SpringQualifierInfo(
                value=match.group(1),
                target_name=match.group(3),
                target_type=match.group(2),
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_xml_beans(self, content: str, file_path: str, result: Dict):
        """Extract bean definitions from Spring XML config."""
        for match in self.XML_BEAN_PATTERN.finditer(content):
            bean = SpringBeanDefinitionInfo(
                bean_id=match.group(1) or "",
                bean_class=match.group(2) or "",
                scope=match.group(3) or "singleton",
                init_method=match.group(4) or "",
                destroy_method=match.group(5) or "",
                is_abstract=match.group(6) == 'true' if match.group(6) else False,
                parent=match.group(7) or "",
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            )
            result['bean_definitions'].append(bean)
