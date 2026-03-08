"""
CSharpEnumExtractor - Extracts C# enum definitions.

Extracts:
- Enum definitions with members and explicit values
- Flags enums ([Flags] attribute)
- Underlying type specification (: byte, : int, etc.)

Part of CodeTrellis v4.13 - C# Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSharpEnumMember:
    """Information about a C# enum member."""
    name: str
    value: Optional[str] = None  # Explicit value if provided
    attributes: List[str] = field(default_factory=list)
    xml_doc: Optional[str] = None


@dataclass
class CSharpEnumInfo:
    """Information about a C# enum."""
    name: str
    members: List[CSharpEnumMember] = field(default_factory=list)
    underlying_type: Optional[str] = None  # byte, int, long, etc.
    attributes: List[str] = field(default_factory=list)
    is_flags: bool = False
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    namespace: str = ""
    modifiers: List[str] = field(default_factory=list)


class CSharpEnumExtractor:
    """
    Extracts C# enum definitions from source code.

    Handles:
    - Simple enums with auto values
    - Enums with explicit values (= 0, = 1, = 0x01)
    - [Flags] attribute detection
    - Underlying type (: byte, : ushort, : int, : uint, : long, : ulong)
    - XML documentation comments
    - Access modifiers
    """

    # Enum pattern
    ENUM_PATTERN = re.compile(
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'              # Attributes
        r'((?:public|private|protected|internal|new)\s+)*'  # Modifiers
        r'enum\s+'
        r'(\w+)'                                          # Enum name
        r'(?:\s*:\s*(\w+))?'                              # Optional underlying type
        r'\s*\{([^}]*)\}',                                # Members
        re.MULTILINE | re.DOTALL
    )

    # Namespace pattern
    NAMESPACE_PATTERN = re.compile(r'namespace\s+([\w.]+)\s*[{;]', re.MULTILINE)
    FILE_SCOPED_NS = re.compile(r'^\s*namespace\s+([\w.]+)\s*;', re.MULTILINE)

    # Member pattern (within enum body)
    MEMBER_PATTERN = re.compile(
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'              # Optional attributes
        r'(\w+)'                                          # Member name
        r'(?:\s*=\s*([^,\n}]+))?',                       # Optional explicit value
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> List[CSharpEnumInfo]:
        """
        Extract all enum definitions from C# source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            List of CSharpEnumInfo objects
        """
        results = []

        # Detect namespace
        namespace = ""
        m = self.FILE_SCOPED_NS.search(content)
        if m:
            namespace = m.group(1)
        else:
            m = self.NAMESPACE_PATTERN.search(content)
            if m:
                namespace = m.group(1)

        for match in self.ENUM_PATTERN.finditer(content):
            enum = self._parse_enum(match, file_path, namespace, content)
            if enum:
                results.append(enum)

        return results

    def _parse_enum(self, match, file_path: str, namespace: str,
                    content: str) -> Optional[CSharpEnumInfo]:
        """Parse an enum definition."""
        try:
            attr_str = match.group(1) or ""
            mod_str = match.group(2) or ""
            name = match.group(3)
            underlying = match.group(4)
            members_str = match.group(5) or ""

            # Parse attributes
            attributes = []
            is_flags = False
            for a in re.finditer(r'\[(\w+)', attr_str):
                attr_name = a.group(1)
                attributes.append(attr_name)
                if attr_name == 'Flags':
                    is_flags = True

            modifiers = [m.strip() for m in (mod_str or "").split() if m.strip()]

            # Parse members
            members = self._parse_members(members_str)

            line_number = content[:match.start()].count('\n') + 1

            is_exported = 'public' in modifiers or 'internal' in modifiers or not any(
                m in modifiers for m in ('private', 'protected')
            )

            return CSharpEnumInfo(
                name=name,
                members=members,
                underlying_type=underlying,
                attributes=attributes,
                is_flags=is_flags,
                file=file_path,
                line_number=line_number,
                is_exported=is_exported,
                namespace=namespace,
                modifiers=modifiers,
            )
        except Exception:
            return None

    def _parse_members(self, members_str: str) -> List[CSharpEnumMember]:
        """Parse enum members from body string."""
        members = []
        # Remove comments
        cleaned = re.sub(r'//[^\n]*', '', members_str)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

        for line in cleaned.split(','):
            line = line.strip()
            if not line:
                continue

            # Parse attributes on member
            attrs = []
            attr_match = re.match(r'((?:\[[\w.,\s()="\[\]]+\]\s*)+)', line)
            if attr_match:
                for a in re.finditer(r'\[(\w+)', attr_match.group()):
                    attrs.append(a.group(1))
                line = line[attr_match.end():].strip()

            # Parse name = value
            parts = line.split('=', 1)
            name = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else None

            if name and re.match(r'^\w+$', name):
                members.append(CSharpEnumMember(
                    name=name,
                    value=value,
                    attributes=attrs,
                ))

        return members
