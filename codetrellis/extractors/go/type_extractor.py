"""
GoTypeExtractor - Extracts Go struct, interface, and type alias definitions.

This extractor parses Go source code and extracts:
- Struct definitions with fields, tags, and embedded types
- Interface definitions with method signatures
- Type aliases and type definitions

Part of CodeTrellis v4.5 - Go Language Support (G-17)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class GoFieldInfo:
    """Information about a Go struct field."""
    name: str
    type: str
    tag: Optional[str] = None
    is_embedded: bool = False
    comment: Optional[str] = None


@dataclass
class GoStructInfo:
    """Information about a Go struct."""
    name: str
    fields: List[GoFieldInfo] = field(default_factory=list)
    embedded_types: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    comment: Optional[str] = None
    is_exported: bool = False


@dataclass
class GoInterfaceInfo:
    """Information about a Go interface."""
    name: str
    methods: List[Dict[str, Any]] = field(default_factory=list)
    embedded_interfaces: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    comment: Optional[str] = None
    is_exported: bool = False


@dataclass
class GoTypeAliasInfo:
    """Information about a Go type alias / type definition."""
    name: str
    underlying_type: str
    file: str = ""
    line_number: int = 0
    is_exported: bool = False


class GoTypeExtractor:
    """
    Extracts Go type definitions from source code.

    Handles:
    - Named structs with fields and struct tags
    - Interfaces with method sets
    - Embedded types (composition)
    - Type aliases (type X = Y) and type definitions (type X Y)
    - Exported vs unexported detection

    v4.8: Uses brace-balanced extraction instead of [^}]* regex
    to correctly handle nested braces, multi-line comments, and
    large type definitions (fixes 44% struct loss, 50% interface loss).
    """

    # Header patterns - find the start of struct/interface, then use brace-balancing for body
    STRUCT_HEADER = re.compile(
        r'(?:(//.+)\n\s*)?type\s+(\w+)\s+struct\s*\{',
        re.MULTILINE
    )

    INTERFACE_HEADER = re.compile(
        r'(?:(//.+)\n\s*)?type\s+(\w+)\s+interface\s*\{',
        re.MULTILINE
    )

    # Type alias/definition: type Name SomeType  or  type Name = SomeType
    TYPE_ALIAS_PATTERN = re.compile(
        r'^type\s+(\w+)\s*(=)?\s*([^\s{][^\n]*?)$',
        re.MULTILINE
    )

    # Struct field: Name Type `json:"name"` // comment
    FIELD_PATTERN = re.compile(
        r'^\s+(\w+)\s+([\w\[\]\*\.]+(?:\s*(?:map|chan|func)\s*[\w\[\]\*\.\{\}\(\),\s]*)?)\s*(?:`([^`]+)`)?\s*(?://\s*(.+))?$',
        re.MULTILINE
    )

    # Embedded type (no field name, just a type): SomeType or *SomeType
    EMBEDDED_PATTERN = re.compile(
        r'^\s+(\*?\w+(?:\.\w+)?)\s*$',
        re.MULTILINE
    )

    # Interface method: MethodName(params) (returns)
    INTERFACE_METHOD_PATTERN = re.compile(
        r'^\s+(\w+)\(([^)]*)\)\s*(.*?)$',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Go type extractor."""
        pass

    @staticmethod
    def _extract_brace_body(content: str, open_brace_pos: int) -> Optional[str]:
        """
        Extract the body between matched braces using brace-counting.

        This is the GENERIC fix for the [^}]* regex problem. It correctly
        handles nested braces, comments containing braces, and string
        literals — works for ANY language with brace-delimited blocks.

        Args:
            content: Full source code
            open_brace_pos: Position of the opening '{' character

        Returns:
            Body text between the braces, or None if unbalanced
        """
        depth = 1
        i = open_brace_pos + 1
        in_string = False
        in_line_comment = False
        in_block_comment = False
        in_raw_string = False
        length = len(content)

        while i < length and depth > 0:
            ch = content[i]
            next_ch = content[i + 1] if i + 1 < length else ''

            # Handle line comments
            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
                i += 1
                continue

            # Handle block comments
            if in_block_comment:
                if ch == '*' and next_ch == '/':
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue

            # Handle strings
            if in_string:
                if ch == '\\':
                    i += 2  # Skip escaped char
                    continue
                if ch == '"':
                    in_string = False
                i += 1
                continue

            # Handle raw strings (backtick in Go)
            if in_raw_string:
                if ch == '`':
                    in_raw_string = False
                i += 1
                continue

            # Detect comment starts
            if ch == '/' and next_ch == '/':
                in_line_comment = True
                i += 2
                continue
            if ch == '/' and next_ch == '*':
                in_block_comment = True
                i += 2
                continue

            # Detect string starts
            if ch == '"':
                in_string = True
                i += 1
                continue
            if ch == '`':
                in_raw_string = True
                i += 1
                continue

            # Count braces
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[open_brace_pos + 1:i]

            i += 1

        return None  # Unbalanced braces

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Go types from source code.

        Args:
            content: Go source code content
            file_path: Path to source file

        Returns:
            Dict with 'structs', 'interfaces', 'type_aliases' keys
        """
        return {
            'structs': self._extract_structs(content, file_path),
            'interfaces': self._extract_interfaces(content, file_path),
            'type_aliases': self._extract_type_aliases(content, file_path),
        }

    def _extract_structs(self, content: str, file_path: str) -> List[GoStructInfo]:
        """Extract all struct definitions using brace-balanced parsing."""
        results = []

        for match in self.STRUCT_HEADER.finditer(content):
            comment = match.group(1)
            name = match.group(2)
            # Find the opening brace position (end of match - 1)
            open_brace = match.end() - 1
            body = self._extract_brace_body(content, open_brace)
            if body is None:
                continue  # Unbalanced braces, skip
            line_number = content[:match.start()].count('\n') + 1

            fields = []
            embedded_types = []

            # Extract named fields
            for field_match in self.FIELD_PATTERN.finditer(body):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                tag = field_match.group(3)
                field_comment = field_match.group(4)

                fields.append(GoFieldInfo(
                    name=field_name,
                    type=field_type,
                    tag=tag,
                    is_embedded=False,
                    comment=field_comment.strip() if field_comment else None,
                ))

            # Extract embedded types (lines with just a type name)
            for embed_match in self.EMBEDDED_PATTERN.finditer(body):
                embedded_name = embed_match.group(1).strip()
                # Skip if it was already caught as a field
                if embedded_name and not any(f.name == embedded_name for f in fields):
                    embedded_types.append(embedded_name)
                    fields.append(GoFieldInfo(
                        name=embedded_name,
                        type=embedded_name,
                        is_embedded=True,
                    ))

            info = GoStructInfo(
                name=name,
                fields=fields,
                embedded_types=embedded_types,
                file=file_path,
                line_number=line_number,
                comment=comment.strip().lstrip('/ ') if comment else None,
                is_exported=name[0].isupper() if name else False,
            )
            results.append(info)

        return results

    def _extract_interfaces(self, content: str, file_path: str) -> List[GoInterfaceInfo]:
        """Extract all interface definitions using brace-balanced parsing."""
        results = []

        for match in self.INTERFACE_HEADER.finditer(content):
            comment = match.group(1)
            name = match.group(2)
            open_brace = match.end() - 1
            body = self._extract_brace_body(content, open_brace)
            if body is None:
                continue
            line_number = content[:match.start()].count('\n') + 1

            methods = []
            embedded_interfaces = []

            # Extract methods
            for method_match in self.INTERFACE_METHOD_PATTERN.finditer(body):
                method_name = method_match.group(1)
                params = method_match.group(2).strip()
                returns = method_match.group(3).strip()

                methods.append({
                    'name': method_name,
                    'params': params,
                    'returns': returns,
                })

            # Extract embedded interfaces (lines with just a type name)
            for embed_match in self.EMBEDDED_PATTERN.finditer(body):
                embedded_name = embed_match.group(1).strip()
                if embedded_name and not any(m['name'] == embedded_name for m in methods):
                    embedded_interfaces.append(embedded_name)

            info = GoInterfaceInfo(
                name=name,
                methods=methods,
                embedded_interfaces=embedded_interfaces,
                file=file_path,
                line_number=line_number,
                comment=comment.strip().lstrip('/ ') if comment else None,
                is_exported=name[0].isupper() if name else False,
            )
            results.append(info)

        return results

    def _extract_type_aliases(self, content: str, file_path: str) -> List[GoTypeAliasInfo]:
        """Extract type aliases and type definitions (not structs/interfaces)."""
        results = []

        for match in self.TYPE_ALIAS_PATTERN.finditer(content):
            name = match.group(1)
            underlying = match.group(3).strip()

            # Skip struct and interface definitions (handled separately)
            if underlying.startswith('struct') or underlying.startswith('interface'):
                continue

            line_number = content[:match.start()].count('\n') + 1

            info = GoTypeAliasInfo(
                name=name,
                underlying_type=underlying,
                file=file_path,
                line_number=line_number,
                is_exported=name[0].isupper() if name else False,
            )
            results.append(info)

        return results
