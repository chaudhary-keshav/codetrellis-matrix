"""
TypedDictExtractor - Extracts TypedDict definitions from Python source code.

This extractor parses TypedDict declarations and extracts:
- TypedDict names and keys
- Key types and required/optional status
- Inheritance from other TypedDicts
- Both class-based and function-based syntax

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TypedDictKeyInfo:
    """Information about a TypedDict key."""
    name: str
    type: str
    required: bool = True


@dataclass
class TypedDictInfo:
    """Complete information about a TypedDict."""
    name: str
    keys: List[TypedDictKeyInfo] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    total: bool = True
    line_number: int = 0


class TypedDictExtractor:
    """
    Extracts TypedDict definitions from Python source code.

    Handles:
    - Class-based syntax: class Movie(TypedDict): ...
    - Function-based syntax: Movie = TypedDict('Movie', {...})
    - Required and NotRequired markers
    - total=True/False parameter
    - Inheritance from other TypedDicts
    """

    # Class-based TypedDict pattern
    CLASS_TYPEDDICT_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(([^)]*TypedDict[^)]*)\):',
        re.MULTILINE
    )

    # Function-based TypedDict pattern
    FUNC_TYPEDDICT_PATTERN = re.compile(
        r'(\w+)\s*=\s*TypedDict\s*\(\s*[\'"](\w+)[\'"]\s*,\s*(\{[^}]+\})',
        re.MULTILINE
    )

    # Key pattern for class-based TypedDict
    KEY_PATTERN = re.compile(
        r'^\s+(\w+)\s*:\s*(.+?)$',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the TypedDict extractor."""
        pass

    def extract(self, content: str) -> List[TypedDictInfo]:
        """
        Extract all TypedDicts from Python content.

        Args:
            content: Python source code

        Returns:
            List of TypedDictInfo objects
        """
        typeddicts = []

        # Extract class-based TypedDicts
        for match in self.CLASS_TYPEDDICT_PATTERN.finditer(content):
            td_name = match.group(1)
            bases_str = match.group(2)

            # Parse bases and check for total parameter
            bases = []
            total = True

            for base in bases_str.split(','):
                base = base.strip()
                if 'total=' in base:
                    total = 'True' in base
                elif base and base != 'TypedDict':
                    bases.append(base)

            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            # Extract class body
            class_body_start = match.end()
            class_body = self._extract_class_body(content, class_body_start)

            if class_body is None:
                continue

            # Parse keys
            keys = self._parse_keys(class_body, total)

            typeddict_info = TypedDictInfo(
                name=td_name,
                keys=keys,
                bases=bases,
                total=total,
                line_number=line_number
            )

            typeddicts.append(typeddict_info)

        # Extract function-based TypedDicts
        for match in self.FUNC_TYPEDDICT_PATTERN.finditer(content):
            var_name = match.group(1)
            td_name = match.group(2)
            keys_dict = match.group(3)

            # Parse keys from dict literal
            keys = self._parse_dict_keys(keys_dict)

            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            typeddict_info = TypedDictInfo(
                name=var_name,  # Use variable name, not string name
                keys=keys,
                bases=[],
                total=True,
                line_number=line_number
            )

            typeddicts.append(typeddict_info)

        return typeddicts

    def _extract_class_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract the body of a class by indentation."""
        lines = content[start_pos:].split('\n')

        if not lines:
            return None

        body_lines = []
        base_indent = None

        for line in lines:
            if not line.strip():
                if base_indent is not None:
                    body_lines.append('')
                continue

            current_indent = len(line) - len(line.lstrip())

            if base_indent is None:
                base_indent = current_indent
                body_lines.append(line)
                continue

            if current_indent < base_indent and line.strip():
                break

            body_lines.append(line)

        return '\n'.join(body_lines)

    def _parse_keys(self, class_body: str, default_total: bool) -> List[TypedDictKeyInfo]:
        """Parse keys from class body."""
        keys = []

        for match in self.KEY_PATTERN.finditer(class_body):
            key_name = match.group(1)
            key_type = match.group(2).strip()

            # Skip if it looks like a method
            if key_name == 'def' or '(' in key_type:
                continue

            # Determine if required
            required = default_total

            # Check for Required/NotRequired wrappers
            if 'NotRequired[' in key_type:
                required = False
                key_type = re.sub(r'NotRequired\[(.+)\]', r'\1', key_type)
            elif 'Required[' in key_type:
                required = True
                key_type = re.sub(r'Required\[(.+)\]', r'\1', key_type)

            keys.append(TypedDictKeyInfo(
                name=key_name,
                type=key_type,
                required=required
            ))

        return keys

    def _parse_dict_keys(self, dict_str: str) -> List[TypedDictKeyInfo]:
        """Parse keys from dict literal string."""
        keys = []

        # Pattern for 'key': Type
        key_pattern = re.compile(r'[\'"](\w+)[\'"]\s*:\s*([^,}]+)')

        for match in key_pattern.finditer(dict_str):
            key_name = match.group(1)
            key_type = match.group(2).strip()

            keys.append(TypedDictKeyInfo(
                name=key_name,
                type=key_type,
                required=True  # Function-based TypedDicts are always total=True by default
            ))

        return keys

    def to_codetrellis_format(self, typeddicts: List[TypedDictInfo]) -> str:
        """
        Convert extracted TypedDicts to CodeTrellis format.

        Args:
            typeddicts: List of TypedDictInfo objects

        Returns:
            CodeTrellis formatted string
        """
        if not typeddicts:
            return ""

        lines = ["[TYPED_DICTS]"]

        for td in typeddicts:
            parts = [td.name]

            # Add bases
            if td.bases:
                parts.append(f"extends:{','.join(td.bases)}")

            # Add keys
            key_strs = []
            for k in td.keys:
                key_str = f"{k.name}:{k.type}"
                if k.required:
                    key_str += "!"
                else:
                    key_str += "?"
                key_strs.append(key_str)

            if key_strs:
                parts.append(f"keys:[{','.join(key_strs)}]")

            # Add total flag
            parts.append(f"total:{td.total}")

            lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_typeddicts(content: str) -> List[TypedDictInfo]:
    """Extract TypedDicts from Python content."""
    extractor = TypedDictExtractor()
    return extractor.extract(content)
