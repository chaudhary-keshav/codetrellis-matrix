"""
Quarkus Config Extractor v1.0 - MicroProfile Config, ConfigMapping, config profiles.
Part of CodeTrellis v4.94 - Quarkus Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class QuarkusConfigPropertyInfo:
    """A @ConfigProperty injection."""
    name: str
    property_key: str = ""
    default_value: str = ""
    field_type: str = ""
    is_optional: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class QuarkusConfigMappingInfo:
    """A @ConfigMapping interface."""
    name: str
    prefix: str = ""
    properties: List[str] = field(default_factory=list)
    nested_groups: List[str] = field(default_factory=list)
    naming_strategy: str = ""
    file: str = ""
    line_number: int = 0


class QuarkusConfigExtractor:
    """Extracts Quarkus/MicroProfile Config patterns."""

    CONFIG_PROPERTY_PATTERN = re.compile(
        r'@ConfigProperty\(\s*name\s*=\s*"([^"]+)"'
        r'(?:\s*,\s*defaultValue\s*=\s*"([^"]*)")?'
        r'\s*\)\s*\n'
        r'\s*(?:(?:private|protected|public)\s+)?(?:final\s+)?([\w<>,?\[\]]+)\s+(\w+)\s*;',
        re.MULTILINE
    )

    CONFIG_MAPPING_PATTERN = re.compile(
        r'@ConfigMapping\(\s*prefix\s*=\s*"([^"]+)"'
        r'(?:\s*,\s*namingStrategy\s*=\s*NamingStrategy\.(\w+))?'
        r'\s*\)\s*\n'
        r'(?:public\s+)?interface\s+(\w+)',
        re.MULTILINE
    )

    CONFIG_MAPPING_METHOD_PATTERN = re.compile(
        r'(?:@WithName\("([^"]+)"\)\s+)?'
        r'(?:@WithDefault\("([^"]+)"\)\s+)?'
        r'([\w<>,?\[\]]+)\s+(\w+)\(\)',
        re.MULTILINE
    )

    APPLICATION_PROPERTIES_PATTERN = re.compile(
        r'^([\w.]+(?:\[\d+\])?[\w.]*)\s*=\s*(.+)$',
        re.MULTILINE
    )

    PROFILE_PATTERN = re.compile(r'^%(\w+)\.([\w.]+)\s*=\s*(.+)$', re.MULTILINE)

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'config_properties': [], 'config_mappings': [], 'app_properties': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract @ConfigProperty injections
        for match in self.CONFIG_PROPERTY_PATTERN.finditer(content):
            prop_key = match.group(1)
            default_value = match.group(2) or ""
            field_type = match.group(3)
            field_name = match.group(4)
            is_optional = 'Optional' in field_type

            result['config_properties'].append(QuarkusConfigPropertyInfo(
                name=field_name, property_key=prop_key,
                default_value=default_value, field_type=field_type,
                is_optional=is_optional,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract @ConfigMapping interfaces
        for match in self.CONFIG_MAPPING_PATTERN.finditer(content):
            prefix = match.group(1)
            naming_strategy = match.group(2) or "KEBAB_CASE"
            interface_name = match.group(3)

            # Find methods in interface body
            interface_start = match.end()
            brace_count = 0
            interface_end = interface_start
            for i, ch in enumerate(content[interface_start:], interface_start):
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        interface_end = i
                        break

            interface_body = content[interface_start:interface_end]
            properties = []
            nested_groups = []
            for m in self.CONFIG_MAPPING_METHOD_PATTERN.finditer(interface_body):
                return_type = m.group(3)
                method_name = m.group(4)
                if return_type[0].isupper() and return_type not in ('String', 'Integer', 'Long', 'Boolean', 'Double', 'Float', 'Optional', 'List', 'Map', 'Set'):
                    nested_groups.append(method_name)
                else:
                    properties.append(method_name)

            result['config_mappings'].append(QuarkusConfigMappingInfo(
                name=interface_name, prefix=prefix,
                properties=properties, nested_groups=nested_groups,
                naming_strategy=naming_strategy,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract application.properties entries
        if file_path.endswith('.properties'):
            for match in self.PROFILE_PATTERN.finditer(content):
                result['app_properties'].append({
                    'profile': match.group(1),
                    'key': match.group(2),
                    'value': match.group(3).strip(),
                })
            for match in self.APPLICATION_PROPERTIES_PATTERN.finditer(content):
                if not match.group(1).startswith('%'):
                    result['app_properties'].append({
                        'key': match.group(1),
                        'value': match.group(2).strip(),
                    })

        return result
