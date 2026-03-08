"""
Micronaut Config Extractor v1.0 - @ConfigurationProperties, @EachProperty, env-based config.
Part of CodeTrellis v4.94 - Micronaut Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class MicronautConfigPropsInfo:
    """A @ConfigurationProperties class."""
    name: str
    prefix: str = ""
    properties: List[str] = field(default_factory=list)
    nested_configs: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class MicronautEachPropertyInfo:
    """An @EachProperty class (dynamic per-instance config)."""
    name: str
    prefix: str = ""
    primary: str = ""
    properties: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class MicronautConfigExtractor:
    """Extracts Micronaut configuration patterns."""

    CONFIG_PROPS_PATTERN = re.compile(
        r'@ConfigurationProperties\(\s*"([^"]+)"\s*\)\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    EACH_PROPERTY_PATTERN = re.compile(
        r'@EachProperty\(\s*(?:value\s*=\s*)?"([^"]+)"'
        r'(?:\s*,\s*primary\s*=\s*"([^"]*)")?\s*\)\s*\n'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    PROPERTY_FIELD_PATTERN = re.compile(
        r'(?:private|protected)\s+([\w<>,?\[\]]+)\s+(\w+)\s*(?:=\s*[^;]+)?;',
        re.MULTILINE
    )

    SETTER_PATTERN = re.compile(
        r'public\s+void\s+set(\w+)\s*\(\s*([\w<>,?\[\]]+)\s+\w+\s*\)',
        re.MULTILINE
    )

    VALUE_PATTERN = re.compile(
        r'@Value\(\s*"\$\{([^}]+)\}"\s*\)\s*\n'
        r'\s*(?:(?:private|protected|public)\s+)?(?:final\s+)?([\w<>,?\[\]]+)\s+(\w+)',
        re.MULTILINE
    )

    PROPERTY_SOURCE_PATTERN = re.compile(
        r'@PropertySource\(\s*\{([^}]+)\}\s*\)',
        re.MULTILINE
    )

    APPLICATION_YML_KEY = re.compile(r'^(\s*)([\w-]+)\s*:', re.MULTILINE)

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'config_properties': [], 'each_properties': [], 'value_injections': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract @ConfigurationProperties
        for match in self.CONFIG_PROPS_PATTERN.finditer(content):
            prefix = match.group(1)
            class_name = match.group(2)

            # Find the class body
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
            properties = [m.group(2) for m in self.PROPERTY_FIELD_PATTERN.finditer(class_body)]
            setters = [m.group(1)[0].lower() + m.group(1)[1:] for m in self.SETTER_PATTERN.finditer(class_body)]
            all_props = list(set(properties + setters))

            result['config_properties'].append(MicronautConfigPropsInfo(
                name=class_name, prefix=prefix,
                properties=all_props,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract @EachProperty
        for match in self.EACH_PROPERTY_PATTERN.finditer(content):
            prefix = match.group(1)
            primary = match.group(2) or ""
            class_name = match.group(3)

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
            properties = [m.group(2) for m in self.PROPERTY_FIELD_PATTERN.finditer(class_body)]

            result['each_properties'].append(MicronautEachPropertyInfo(
                name=class_name, prefix=prefix, primary=primary,
                properties=properties,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract @Value injections
        for match in self.VALUE_PATTERN.finditer(content):
            result['value_injections'].append({
                'property_key': match.group(1),
                'type': match.group(2),
                'field_name': match.group(3),
                'file': file_path,
                'line_number': content[:match.start()].count('\n') + 1,
            })

        return result
