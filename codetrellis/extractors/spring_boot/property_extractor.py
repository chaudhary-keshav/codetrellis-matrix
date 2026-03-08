"""
Spring Boot Property Extractor v1.0

Extracts Spring Boot property configurations, @ConfigurationProperties, and profiles.

Extracts:
- application.properties / application.yml entries
- @ConfigurationProperties binding classes
- @Value("${...}") injections
- Profile-specific config (application-{profile}.properties)
- @PropertySource declarations
- Environment-based properties
- Spring Boot built-in property categories (server, spring.datasource, etc.)

Part of CodeTrellis v4.94 - Spring Boot Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class SpringBootPropertyInfo:
    """A Spring Boot property entry."""
    key: str
    value: str = ""
    source: str = ""  # application.properties, application.yml, @Value, env
    category: str = ""  # server, datasource, jpa, security, actuator, custom
    profile: str = ""  # default, dev, prod, test
    is_secret: bool = False  # password, secret, key, token
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootConfigPropsInfo:
    """A @ConfigurationProperties binding class."""
    name: str
    prefix: str = ""  # @ConfigurationProperties(prefix="app.mail")
    fields: List[Dict[str, str]] = field(default_factory=list)  # [{name, type, default}]
    nested_classes: List[str] = field(default_factory=list)
    is_validated: bool = False  # @Validated
    is_constructor_binding: bool = False
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootProfileConfigInfo:
    """Profile-specific configuration metadata."""
    profile: str
    config_file: str = ""  # application-{profile}.properties
    active_profiles: List[str] = field(default_factory=list)
    include_profiles: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class SpringBootPropertyExtractor:
    """Extracts Spring Boot property configurations."""

    # @ConfigurationProperties
    CONFIG_PROPS_PATTERN = re.compile(
        r'@ConfigurationProperties\(\s*(?:prefix\s*=\s*)?'
        r'"([^"]*)"\s*\)\s*\n'
        r'((?:@\w+(?:\([^)]*\))?\s*\n)*)'
        r'(?:public\s+)?(?:record\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    # @Value injection
    VALUE_PATTERN = re.compile(
        r'@Value\(\s*"\$\{([^}]+)\}(?::([^"]*))?"?\s*\)\s+'
        r'(?:private|protected|public)?\s*(?:final\s+)?([\w<>,?]+)\s+(\w+)',
        re.MULTILINE
    )

    # Properties file entries (key=value or key: value)
    PROP_ENTRY_PATTERN = re.compile(
        r'^([\w.{}-]+)\s*[=:]\s*(.*)$',
        re.MULTILINE
    )

    # YAML-style properties (simplified)
    YAML_ENTRY_PATTERN = re.compile(
        r'^(\s*)([\w-]+):\s*(.+)?$',
        re.MULTILINE
    )

    # Profile from filename: application-{profile}.properties
    PROFILE_FILE_PATTERN = re.compile(
        r'application-(\w+)\.(properties|yml|yaml)$'
    )

    # spring.profiles.active
    ACTIVE_PROFILES_PATTERN = re.compile(
        r'spring\.profiles\.active\s*[=:]\s*(.+)',
    )

    # @Validated
    VALIDATED_PATTERN = re.compile(r'@Validated\b')

    # @ConstructorBinding
    CONSTRUCTOR_BINDING_PATTERN = re.compile(r'@ConstructorBinding\b')

    # Field extraction in config props class
    FIELD_PATTERN = re.compile(
        r'(?:private|protected)?\s*(?:final\s+)?([\w<>,?]+)\s+(\w+)\s*(?:=\s*([^;]+))?\s*;',
        re.MULTILINE
    )

    # Secret property patterns
    SECRET_KEYS = re.compile(
        r'(password|secret|key|token|credential|api[_-]?key|private[_-]?key)',
        re.IGNORECASE
    )

    # Property categories
    CATEGORY_PREFIXES = {
        'server': 'server',
        'spring.datasource': 'datasource',
        'spring.jpa': 'jpa',
        'spring.data': 'data',
        'spring.security': 'security',
        'spring.kafka': 'messaging',
        'spring.rabbitmq': 'messaging',
        'spring.mail': 'mail',
        'spring.cache': 'cache',
        'spring.redis': 'cache',
        'management': 'actuator',
        'logging': 'logging',
        'spring.cloud': 'cloud',
        'eureka': 'cloud',
        'spring.flyway': 'migration',
        'spring.liquibase': 'migration',
        'spring.servlet': 'web',
        'spring.mvc': 'web',
        'spring.webflux': 'web',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Spring Boot property configurations."""
        result: Dict[str, Any] = {
            'properties': [],
            'config_props_classes': [],
            'profile_configs': [],
        }

        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Detect if this is a properties/yaml file or Java source
        is_props_file = file_path.endswith('.properties')
        is_yaml_file = file_path.endswith(('.yml', '.yaml'))
        is_java = file_path.endswith('.java')

        if is_props_file:
            self._extract_properties_file(content, file_path, result)
        elif is_yaml_file:
            self._extract_yaml_file(content, file_path, result)
        elif is_java:
            self._extract_java_source(content, file_path, result)

        return result

    def _extract_properties_file(self, content: str, file_path: str, result: Dict):
        """Extract from .properties file."""
        # Detect profile
        profile = ""
        pm = self.PROFILE_FILE_PATTERN.search(file_path)
        if pm:
            profile = pm.group(1)

        for match in self.PROP_ENTRY_PATTERN.finditer(content):
            key = match.group(1).strip()
            value = match.group(2).strip()

            if not key or key.startswith('#'):
                continue

            category = self._categorize_property(key)
            is_secret = bool(self.SECRET_KEYS.search(key))

            result['properties'].append(SpringBootPropertyInfo(
                key=key,
                value=value if not is_secret else '***',
                source='application.properties',
                category=category,
                profile=profile or 'default',
                is_secret=is_secret,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Active profiles
        ap_match = self.ACTIVE_PROFILES_PATTERN.search(content)
        if ap_match:
            profiles = [p.strip() for p in ap_match.group(1).split(',')]
            result['profile_configs'].append(SpringBootProfileConfigInfo(
                profile=profile or 'default',
                config_file=file_path.split('/')[-1] if '/' in file_path else file_path,
                active_profiles=profiles,
                file=file_path,
                line_number=content[:ap_match.start()].count('\n') + 1,
            ))

    def _extract_yaml_file(self, content: str, file_path: str, result: Dict):
        """Extract from .yml/.yaml file (simplified key detection)."""
        profile = ""
        pm = self.PROFILE_FILE_PATTERN.search(file_path)
        if pm:
            profile = pm.group(1)

        # Build flat key-value pairs from YAML (simplified)
        key_stack = []
        prev_indent = -1

        for match in self.YAML_ENTRY_PATTERN.finditer(content):
            indent = len(match.group(1))
            key = match.group(2)
            value = (match.group(3) or "").strip()

            # Adjust stack based on indentation
            while key_stack and indent <= prev_indent:
                key_stack.pop()
                prev_indent -= 2

            if value and not value.startswith('#'):
                full_key = '.'.join(key_stack + [key])
                category = self._categorize_property(full_key)
                is_secret = bool(self.SECRET_KEYS.search(full_key))

                result['properties'].append(SpringBootPropertyInfo(
                    key=full_key,
                    value=value if not is_secret else '***',
                    source='application.yml',
                    category=category,
                    profile=profile or 'default',
                    is_secret=is_secret,
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))
            else:
                key_stack.append(key)
                prev_indent = indent

    def _extract_java_source(self, content: str, file_path: str, result: Dict):
        """Extract from Java source file."""
        # @ConfigurationProperties classes
        for match in self.CONFIG_PROPS_PATTERN.finditer(content):
            prefix = match.group(1)
            between = match.group(2) or ""
            class_name = match.group(3)

            is_validated = bool(self.VALIDATED_PATTERN.search(between))
            is_ctor = bool(self.CONSTRUCTOR_BINDING_PATTERN.search(between))

            # Find class body for fields
            class_start = match.end()
            brace_count = 0
            class_end = class_start
            for i, ch in enumerate(content[class_start:], class_start):
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        class_end = i
                        break

            class_body = content[class_start:class_end]
            fields = []
            for fm in self.FIELD_PATTERN.finditer(class_body):
                fields.append({
                    'type': fm.group(1),
                    'name': fm.group(2),
                    'default': fm.group(3).strip() if fm.group(3) else '',
                })

            result['config_props_classes'].append(SpringBootConfigPropsInfo(
                name=class_name,
                prefix=prefix,
                fields=fields[:20],
                is_validated=is_validated,
                is_constructor_binding=is_ctor,
                annotations=['ConfigurationProperties'],
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @Value injections
        for match in self.VALUE_PATTERN.finditer(content):
            key = match.group(1)
            default_val = match.group(2) or ""
            field_type = match.group(3)
            field_name = match.group(4)

            category = self._categorize_property(key)
            is_secret = bool(self.SECRET_KEYS.search(key))

            result['properties'].append(SpringBootPropertyInfo(
                key=key,
                value=default_val if not is_secret else '***',
                source='@Value',
                category=category,
                is_secret=is_secret,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _categorize_property(self, key: str) -> str:
        """Categorize a property key by its prefix."""
        for prefix, category in self.CATEGORY_PREFIXES.items():
            if key.startswith(prefix):
                return category
        return 'custom'
