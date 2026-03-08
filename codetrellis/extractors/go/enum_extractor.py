"""
GoEnumExtractor - Extracts Go const blocks (iota enum patterns).

This extractor parses Go source code and extracts:
- Const blocks with iota patterns (Go's enum equivalent)
- Individual const declarations
- Typed const groups

Part of CodeTrellis v4.5 - Go Language Support (G-17)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class GoConstValueInfo:
    """Information about a single const value."""
    name: str
    value: Optional[str] = None
    is_iota: bool = False
    is_exported: bool = False


@dataclass
class GoConstBlockInfo:
    """Information about a const block (Go enum equivalent)."""
    type_name: Optional[str] = None
    values: List[GoConstValueInfo] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    uses_iota: bool = False


class GoEnumExtractor:
    """
    Extracts Go const blocks from source code.

    Go doesn't have native enums; instead, it uses const blocks with iota.
    This extractor detects:
    - const ( ... ) blocks with iota
    - Typed const groups (type Status int; const ( Active Status = iota; ... ))
    - Individual const declarations
    """

    # Const block pattern: const ( ... )
    CONST_BLOCK_PATTERN = re.compile(
        r'const\s*\(\s*\n((?:.*\n)*?)\s*\)',
        re.MULTILINE
    )

    # Individual const: const Name Type = Value
    CONST_SINGLE_PATTERN = re.compile(
        r'^const\s+(\w+)\s+(?:(\w+)\s*=\s*)?(.+?)$',
        re.MULTILINE
    )

    # Const value line inside a block: Name Type = iota or Name = value
    CONST_VALUE_PATTERN = re.compile(
        r'^\s+(\w+)\s*(?:(\w+)\s*)?(?:=\s*(.+?))?\s*(?://.*)?$',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Go enum extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> List[GoConstBlockInfo]:
        """
        Extract all const blocks (enum equivalents) from Go source code.

        Args:
            content: Go source code content
            file_path: Path to source file

        Returns:
            List of GoConstBlockInfo objects
        """
        results = []

        # Extract const blocks
        for match in self.CONST_BLOCK_PATTERN.finditer(content):
            body = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            values = []
            type_name = None
            uses_iota = 'iota' in body

            for value_match in self.CONST_VALUE_PATTERN.finditer(body):
                name = value_match.group(1)
                type_hint = value_match.group(2)
                value = value_match.group(3)

                # Skip blank lines and comments
                if name in ('_', ''):
                    continue

                # Detect type from first value in block
                if type_hint and type_hint[0].isupper():
                    type_name = type_hint

                is_iota = value is not None and 'iota' in value if value else False

                values.append(GoConstValueInfo(
                    name=name,
                    value=value.strip() if value else None,
                    is_iota=is_iota,
                    is_exported=name[0].isupper() if name else False,
                ))

            if values:
                results.append(GoConstBlockInfo(
                    type_name=type_name,
                    values=values,
                    file=file_path,
                    line_number=line_number,
                    uses_iota=uses_iota,
                ))

        return results
