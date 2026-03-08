"""
Stimulus Value Extractor for CodeTrellis

Extracts Stimulus value definitions from JavaScript/TypeScript and HTML:
- static values = { name: Type } declarations in controllers
- Value types: String, Number, Boolean, Array, Object
- Default values: { type: Number, default: 0 }
- data-*-value HTML attributes for setting values
- Value change callbacks: nameValueChanged()
- Value getter/setter usage: this.nameValue, this.nameValue = x

Supports:
- Stimulus v2.x (values API introduced)
- Stimulus v3.x (values API enhanced)

Part of CodeTrellis v4.68 - Stimulus / Hotwire Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StimulusValueInfo:
    """Information about a Stimulus value definition or usage."""
    name: str  # Value name (e.g., "url", "count")
    file: str = ""
    line_number: int = 0
    value_type: str = ""  # String, Number, Boolean, Array, Object
    default_value: str = ""  # Default value if specified
    value_usage: str = ""  # declaration, html_attribute, getter, setter, callback
    controller_name: str = ""  # Associated controller identifier
    has_change_callback: bool = False  # nameValueChanged() exists
    is_complex_type: bool = False  # { type: X, default: Y } format
    version_hint: str = ""  # v2, v3


# HTML: data-controller-name-value="foo"
HTML_VALUE_PATTERN = re.compile(
    r'data-(?P<controller>[\w-]+)-(?P<name>[\w-]+)-value\s*=\s*["\'](?P<value>[^"\']*)["\']',
    re.IGNORECASE
)

# JS: static values = { name: Type, ... }
STATIC_VALUES_PATTERN = re.compile(
    r'static\s+values\s*=\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
    re.DOTALL
)

# Inside static values: name: Type  or  name: { type: Type, default: value }
SIMPLE_VALUE_ENTRY = re.compile(
    r'(\w+)\s*:\s*(String|Number|Boolean|Array|Object)\b'
)

COMPLEX_VALUE_ENTRY = re.compile(
    r'(\w+)\s*:\s*\{\s*type\s*:\s*(String|Number|Boolean|Array|Object)'
    r'(?:\s*,\s*default\s*:\s*([^}]*))?'
    r'\s*\}',
    re.DOTALL
)

# JS: this.nameValue (getter)
VALUE_GETTER_PATTERN = re.compile(
    r'this\.(?P<name>\w+)Value\b(?!\s*=)',
)

# JS: this.nameValue = expr (setter)
VALUE_SETTER_PATTERN = re.compile(
    r'this\.(?P<name>\w+)Value\s*=',
)

# JS: nameValueChanged(value, previousValue)
VALUE_CHANGED_PATTERN = re.compile(
    r'(?P<name>\w+)ValueChanged\s*\(',
    re.MULTILINE
)

# Known Stimulus value types
STIMULUS_VALUE_TYPES = {'String', 'Number', 'Boolean', 'Array', 'Object'}


class StimulusValueExtractor:
    """Extracts Stimulus value definitions and usage."""

    def extract(self, content: str, file_path: str = "") -> List[StimulusValueInfo]:
        """Extract Stimulus value definitions from source code or HTML.

        Args:
            content: File content to parse.
            file_path: Path to the file (for metadata).

        Returns:
            List of StimulusValueInfo objects.
        """
        if not content or not content.strip():
            return []

        values: List[StimulusValueInfo] = []

        # HTML value attributes: data-controller-name-value="foo"
        for match in HTML_VALUE_PATTERN.finditer(content):
            controller = match.group('controller')
            name = match.group('name')
            value = match.group('value')
            line = content[:match.start()].count('\n') + 1
            values.append(StimulusValueInfo(
                name=name,
                file=file_path,
                line_number=line,
                value_usage="html_attribute",
                controller_name=controller,
                default_value=value[:200],
                version_hint="v2",
            ))

        # JS: static values = { ... }
        for sv_match in STATIC_VALUES_PATTERN.finditer(content):
            body = sv_match.group(1)
            base_line = content[:sv_match.start()].count('\n') + 1

            # Complex entries first: name: { type: Type, default: value }
            found_names = set()
            for cv in COMPLEX_VALUE_ENTRY.finditer(body):
                name = cv.group(1)
                vtype = cv.group(2)
                default = (cv.group(3) or '').strip().rstrip(',')
                found_names.add(name)
                values.append(StimulusValueInfo(
                    name=name,
                    file=file_path,
                    line_number=base_line,
                    value_type=vtype,
                    default_value=default[:200],
                    value_usage="declaration",
                    is_complex_type=True,
                    version_hint="v2",
                ))

            # Simple entries: name: Type
            for sv in SIMPLE_VALUE_ENTRY.finditer(body):
                name = sv.group(1)
                vtype = sv.group(2)
                if name not in found_names and name != 'type':
                    values.append(StimulusValueInfo(
                        name=name,
                        file=file_path,
                        line_number=base_line,
                        value_type=vtype,
                        value_usage="declaration",
                        version_hint="v2",
                    ))

        # JS: this.nameValue (getter)
        for match in VALUE_GETTER_PATTERN.finditer(content):
            name = match.group('name')
            line = content[:match.start()].count('\n') + 1
            values.append(StimulusValueInfo(
                name=name,
                file=file_path,
                line_number=line,
                value_usage="getter",
            ))

        # JS: this.nameValue = expr (setter)
        for match in VALUE_SETTER_PATTERN.finditer(content):
            name = match.group('name')
            line = content[:match.start()].count('\n') + 1
            values.append(StimulusValueInfo(
                name=name,
                file=file_path,
                line_number=line,
                value_usage="setter",
            ))

        # JS: nameValueChanged() callbacks
        for match in VALUE_CHANGED_PATTERN.finditer(content):
            name = match.group('name')
            line = content[:match.start()].count('\n') + 1
            # Lowercase first letter
            if name:
                name = name[0].lower() + name[1:]
            values.append(StimulusValueInfo(
                name=name,
                file=file_path,
                line_number=line,
                value_usage="callback",
                has_change_callback=True,
            ))

        return values
