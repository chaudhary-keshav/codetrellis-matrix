"""
PythonEnumExtractor - Extracts Enum definitions from Python source code.

This extractor parses Python enum declarations and extracts:
- Enum, IntEnum, StrEnum, Flag, IntFlag
- Enum members with values
- auto() values
- Combined flag values

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum as PyEnum


class EnumType(PyEnum):
    """Type of Python enum."""
    ENUM = "Enum"
    INT_ENUM = "IntEnum"
    STR_ENUM = "StrEnum"
    FLAG = "Flag"
    INT_FLAG = "IntFlag"


@dataclass
class EnumMemberInfo:
    """Information about an enum member."""
    name: str
    value: str
    is_auto: bool = False


@dataclass
class PythonEnumInfo:
    """Complete information about a Python enum."""
    name: str
    enum_type: EnumType = EnumType.ENUM
    members: List[EnumMemberInfo] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    line_number: int = 0


class PythonEnumExtractor:
    """
    Extracts Python Enum definitions from source code.

    Handles:
    - Enum, IntEnum, StrEnum
    - Flag, IntFlag
    - auto() values
    - String and integer values
    - Combined flag values (READ | WRITE)
    """

    # Pattern for enum class definition
    ENUM_CLASS_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(([^)]*(?:Enum|Flag)[^)]*)\):',
        re.MULTILINE
    )

    # Pattern for enum member
    MEMBER_PATTERN = re.compile(
        r'^\s+(\w+)\s*=\s*(.+?)$',
        re.MULTILINE
    )

    # Pattern for functional enum definition
    FUNCTIONAL_ENUM_PATTERN = re.compile(
        r'(\w+)\s*=\s*(Enum|IntEnum|StrEnum|Flag|IntFlag)\s*\(\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the enum extractor."""
        pass

    def extract(self, content: str) -> List[PythonEnumInfo]:
        """
        Extract all enums from Python content.

        Args:
            content: Python source code

        Returns:
            List of PythonEnumInfo objects
        """
        enums = []

        # Extract class-based enums
        for match in self.ENUM_CLASS_PATTERN.finditer(content):
            enum_name = match.group(1)
            bases_str = match.group(2)

            # Determine enum type
            enum_type = self._determine_enum_type(bases_str)
            bases = self._parse_bases(bases_str)

            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            # Extract class body
            class_body_start = match.end()
            class_body = self._extract_class_body(content, class_body_start)

            if class_body is None:
                continue

            # Parse members
            members = self._parse_members(class_body, enum_type)

            enum_info = PythonEnumInfo(
                name=enum_name,
                enum_type=enum_type,
                members=members,
                bases=bases,
                line_number=line_number
            )

            enums.append(enum_info)

        # Extract functional enums
        for match in self.FUNCTIONAL_ENUM_PATTERN.finditer(content):
            var_name = match.group(1)
            enum_type_str = match.group(2)

            enum_type = EnumType(enum_type_str)

            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            # Try to extract members from the functional call
            # This is complex, so we'll just note that it exists
            enum_info = PythonEnumInfo(
                name=var_name,
                enum_type=enum_type,
                members=[],
                bases=[],
                line_number=line_number
            )

            enums.append(enum_info)

        return enums

    def _determine_enum_type(self, bases_str: str) -> EnumType:
        """Determine the type of enum from bases."""
        if 'StrEnum' in bases_str:
            return EnumType.STR_ENUM
        elif 'IntEnum' in bases_str:
            return EnumType.INT_ENUM
        elif 'IntFlag' in bases_str:
            return EnumType.INT_FLAG
        elif 'Flag' in bases_str:
            return EnumType.FLAG
        else:
            return EnumType.ENUM

    def _parse_bases(self, bases_str: str) -> List[str]:
        """Parse non-enum bases."""
        bases = []
        for base in bases_str.split(','):
            base = base.strip()
            if base and base not in ('Enum', 'IntEnum', 'StrEnum', 'Flag', 'IntFlag'):
                bases.append(base)
        return bases

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

    def _parse_members(self, class_body: str, enum_type: EnumType) -> List[EnumMemberInfo]:
        """Parse enum members from class body."""
        members = []

        for match in self.MEMBER_PATTERN.finditer(class_body):
            member_name = match.group(1)
            member_value = match.group(2).strip()

            # Skip methods and special attributes
            if member_name.startswith('_') or member_name == 'def':
                continue

            # Check for auto()
            is_auto = 'auto()' in member_value

            # Clean up the value for display
            if is_auto:
                display_value = "auto"
            elif member_value.startswith('"') or member_value.startswith("'"):
                # String value - extract the string
                string_match = re.match(r'[\'"](.+)[\'"]', member_value)
                if string_match:
                    display_value = string_match.group(1)
                else:
                    display_value = member_value
            else:
                display_value = member_value

            members.append(EnumMemberInfo(
                name=member_name,
                value=display_value,
                is_auto=is_auto
            ))

        return members

    def to_codetrellis_format(self, enums: List[PythonEnumInfo]) -> str:
        """
        Convert extracted enums to CodeTrellis format.

        Args:
            enums: List of PythonEnumInfo objects

        Returns:
            CodeTrellis formatted string
        """
        if not enums:
            return ""

        lines = ["[ENUMS]"]

        for enum in enums:
            parts = [enum.name]

            # Add enum type
            parts.append(f"type:{enum.enum_type.value}")

            # Add members
            if enum.members:
                member_strs = []
                for m in enum.members:
                    if m.is_auto:
                        member_strs.append(f"{m.name}=auto")
                    else:
                        member_strs.append(f"{m.name}={m.value}")
                parts.append(f"values:[{','.join(member_strs)}]")

            lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_enums(content: str) -> List[PythonEnumInfo]:
    """Extract enums from Python content."""
    extractor = PythonEnumExtractor()
    return extractor.extract(content)
