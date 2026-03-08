"""
DataclassExtractor - Extracts Python @dataclass definitions from source code.

This extractor parses Python dataclass declarations and extracts:
- Class name and decorators
- Field names, types, and defaults
- Field metadata (default_factory, field options)
- Class inheritance
- Dataclass options (frozen, slots, kw_only, etc.)

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DataclassFieldInfo:
    """Information about a dataclass field."""
    name: str
    type: str
    default: Optional[str] = None
    default_factory: Optional[str] = None
    required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataclassInfo:
    """Complete information about a Python dataclass."""
    name: str
    fields: List[DataclassFieldInfo] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)
    line_number: int = 0


class DataclassExtractor:
    """
    Extracts Python @dataclass definitions from source code.

    Handles:
    - Simple dataclasses with type annotations
    - Dataclasses with default values
    - Dataclasses with field() factory
    - Dataclass options (frozen, slots, kw_only, order, etc.)
    - Inheritance from other dataclasses
    - Multiple decorators
    """

    # Regex patterns
    DATACLASS_DECORATOR_PATTERN = re.compile(
        r'@dataclass(?:\(([^)]*)\))?\s*\n',
        re.MULTILINE
    )

    CLASS_PATTERN = re.compile(
        r'class\s+(\w+)(?:\(([^)]*)\))?:',
        re.MULTILINE
    )

    FIELD_PATTERN = re.compile(
        r'^\s+(\w+)\s*:\s*([^=\n]+?)(?:\s*=\s*(.+?))?$',
        re.MULTILINE
    )

    FIELD_FACTORY_PATTERN = re.compile(
        r'field\s*\(\s*([^)]*)\s*\)'
    )

    def __init__(self):
        """Initialize the dataclass extractor."""
        pass

    def extract(self, content: str) -> List[DataclassInfo]:
        """
        Extract all dataclasses from Python content.

        Args:
            content: Python source code

        Returns:
            List of DataclassInfo objects
        """
        dataclasses = []

        # Find all @dataclass decorators
        for decorator_match in self.DATACLASS_DECORATOR_PATTERN.finditer(content):
            decorator_options = decorator_match.group(1) or ""
            decorator_end = decorator_match.end()

            # Find the class definition following the decorator
            remaining_content = content[decorator_end:]
            class_match = self.CLASS_PATTERN.search(remaining_content)

            if not class_match:
                continue

            # Make sure the class immediately follows the decorator
            # (allowing for other decorators in between)
            between = remaining_content[:class_match.start()]
            if between.strip() and not all(
                line.strip().startswith('@') or line.strip() == ''
                for line in between.split('\n')
            ):
                continue

            class_name = class_match.group(1)
            bases_str = class_match.group(2) or ""

            # Parse bases
            bases = [b.strip() for b in bases_str.split(',') if b.strip()]

            # Parse decorator options
            options = self._parse_decorator_options(decorator_options)

            # Get additional decorators between @dataclass and class
            additional_decorators = self._extract_additional_decorators(between)

            # Calculate line number
            line_number = content[:decorator_match.start()].count('\n') + 1

            # Extract class body
            class_body_start = decorator_end + class_match.end()
            class_body = self._extract_class_body(content, class_body_start)

            if class_body is None:
                continue

            # Parse fields from class body
            fields = self._parse_fields(class_body)

            dataclass_info = DataclassInfo(
                name=class_name,
                fields=fields,
                bases=bases,
                decorators=['dataclass'] + additional_decorators,
                options=options,
                line_number=line_number
            )

            dataclasses.append(dataclass_info)

        return dataclasses

    def _parse_decorator_options(self, options_str: str) -> Dict[str, Any]:
        """Parse dataclass decorator options."""
        options = {}

        if not options_str:
            return options

        # Common dataclass options
        option_patterns = {
            'frozen': r'frozen\s*=\s*(True|False)',
            'slots': r'slots\s*=\s*(True|False)',
            'kw_only': r'kw_only\s*=\s*(True|False)',
            'order': r'order\s*=\s*(True|False)',
            'eq': r'eq\s*=\s*(True|False)',
            'repr': r'repr\s*=\s*(True|False)',
            'init': r'init\s*=\s*(True|False)',
            'unsafe_hash': r'unsafe_hash\s*=\s*(True|False)',
            'match_args': r'match_args\s*=\s*(True|False)',
        }

        for opt_name, pattern in option_patterns.items():
            match = re.search(pattern, options_str)
            if match:
                options[opt_name] = match.group(1) == 'True'

        return options

    def _extract_additional_decorators(self, between_str: str) -> List[str]:
        """Extract additional decorators between @dataclass and class."""
        decorators = []

        for line in between_str.split('\n'):
            line = line.strip()
            if line.startswith('@'):
                # Extract decorator name
                decorator_match = re.match(r'@(\w+)', line)
                if decorator_match:
                    decorators.append(decorator_match.group(1))

        return decorators

    def _extract_class_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract the body of a class by indentation."""
        lines = content[start_pos:].split('\n')

        if not lines:
            return None

        body_lines = []
        base_indent = None

        for i, line in enumerate(lines):
            # Skip empty lines at the start
            if not line.strip():
                if base_indent is not None:
                    body_lines.append('')
                continue

            current_indent = len(line) - len(line.lstrip())

            # First non-empty line sets the base indent
            if base_indent is None:
                base_indent = current_indent
                body_lines.append(line)
                continue

            # If indent is less than base, we've exited the class
            if current_indent < base_indent and line.strip():
                break

            body_lines.append(line)

        return '\n'.join(body_lines)

    def _parse_fields(self, class_body: str) -> List[DataclassFieldInfo]:
        """Parse fields from class body."""
        fields = []

        for match in self.FIELD_PATTERN.finditer(class_body):
            field_name = match.group(1)
            field_type = match.group(2).strip()
            default_value = match.group(3)

            # Skip class variables that aren't fields (like ClassVar)
            if 'ClassVar' in field_type:
                continue

            # Skip methods (lines with 'def')
            if field_name == 'def' or field_type.startswith('def'):
                continue

            # Parse the default value
            default = None
            default_factory = None
            required = True
            metadata = {}

            if default_value:
                default_value = default_value.strip()
                required = False

                # Check if it's a field() call
                factory_match = self.FIELD_FACTORY_PATTERN.search(default_value)
                if factory_match:
                    field_args = factory_match.group(1)

                    # Extract default_factory
                    factory_pattern = r'default_factory\s*=\s*(\w+)'
                    factory_fn_match = re.search(factory_pattern, field_args)
                    if factory_fn_match:
                        default_factory = factory_fn_match.group(1)

                    # Extract default
                    default_pattern = r'default\s*=\s*([^,)]+)'
                    default_match = re.search(default_pattern, field_args)
                    if default_match:
                        default = default_match.group(1).strip()

                    # Check if it's still required (no default or default_factory)
                    if 'default' not in field_args and 'default_factory' not in field_args:
                        required = True

                    # Extract metadata
                    metadata_pattern = r'metadata\s*=\s*(\{[^}]+\})'
                    metadata_match = re.search(metadata_pattern, field_args)
                    if metadata_match:
                        try:
                            metadata = eval(metadata_match.group(1))
                        except Exception:
                            pass
                else:
                    default = default_value

            field_info = DataclassFieldInfo(
                name=field_name,
                type=field_type,
                default=default,
                default_factory=default_factory,
                required=required,
                metadata=metadata
            )

            fields.append(field_info)

        return fields

    def to_codetrellis_format(self, dataclasses: List[DataclassInfo]) -> str:
        """
        Convert extracted dataclasses to CodeTrellis format.

        Args:
            dataclasses: List of DataclassInfo objects

        Returns:
            CodeTrellis formatted string
        """
        if not dataclasses:
            return ""

        lines = ["[DATACLASSES]"]

        for dc in dataclasses:
            parts = [dc.name]

            # Add bases
            if dc.bases:
                parts.append(f"extends:{','.join(dc.bases)}")

            # Add fields
            field_strs = []
            for f in dc.fields:
                field_str = f"{f.name}:{f.type}"
                if f.required:
                    field_str += "!"
                elif f.default_factory:
                    field_str += f"=factory({f.default_factory})"
                elif f.default:
                    field_str += f"={f.default}"
                field_strs.append(field_str)

            if field_strs:
                parts.append(f"fields:[{','.join(field_strs)}]")

            # Add options
            if dc.options:
                opt_strs = [k for k, v in dc.options.items() if v]
                if opt_strs:
                    parts.append(f"options:[{','.join(opt_strs)}]")

            lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_dataclasses(content: str) -> List[DataclassInfo]:
    """Extract dataclasses from Python content."""
    extractor = DataclassExtractor()
    return extractor.extract(content)
