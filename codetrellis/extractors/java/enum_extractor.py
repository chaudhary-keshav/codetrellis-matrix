"""
JavaEnumExtractor - Extracts Java enum definitions.

Extracts:
- Enum constants with arguments and body
- Enum fields and methods
- Implemented interfaces
- Annotations on enum types

Part of CodeTrellis v4.12 - Java Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class JavaEnumConstant:
    """Information about a single Java enum constant."""
    name: str
    arguments: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    javadoc: Optional[str] = None


@dataclass
class JavaEnumInfo:
    """Information about a Java enum."""
    name: str
    constants: List[JavaEnumConstant] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    fields: List[Dict[str, str]] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    javadoc: Optional[str] = None


class JavaEnumExtractor:
    """
    Extracts Java enum definitions from source code.

    Handles:
    - Simple enums (constants only)
    - Complex enums with constructors, fields, methods
    - Enum constants with arguments
    - Enums implementing interfaces
    - Annotated enums
    """

    ENUM_HEADER = re.compile(
        r'(?:(/\*\*.*?\*/)\s*)?'
        r'((?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'((?:public|protected|private|static|strictfp)\s+)*'
        r'enum\s+(\w+)'
        r'(?:\s+implements\s+([\w.<>,\s?]+?))?'
        r'\s*\{',
        re.MULTILINE | re.DOTALL
    )

    def __init__(self):
        pass

    @staticmethod
    def _extract_brace_body(content: str, open_brace_pos: int) -> Optional[str]:
        """Extract body between matched braces using brace-counting."""
        depth = 1
        i = open_brace_pos + 1
        in_string = False
        in_char = False
        in_line_comment = False
        in_block_comment = False
        length = len(content)

        while i < length and depth > 0:
            ch = content[i]
            next_ch = content[i + 1] if i + 1 < length else ''

            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
                i += 1
                continue
            if in_block_comment:
                if ch == '*' and next_ch == '/':
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue
            if in_string:
                if ch == '\\':
                    i += 2
                    continue
                if ch == '"':
                    in_string = False
                i += 1
                continue
            if in_char:
                if ch == '\\':
                    i += 2
                    continue
                if ch == "'":
                    in_char = False
                i += 1
                continue

            if ch == '/' and next_ch == '/':
                in_line_comment = True
                i += 2
                continue
            if ch == '/' and next_ch == '*':
                in_block_comment = True
                i += 2
                continue
            if ch == '"':
                in_string = True
                i += 1
                continue
            if ch == "'":
                in_char = True
                i += 1
                continue

            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[open_brace_pos + 1:i]
            i += 1
        return None

    def _parse_enum_constants(self, body: str) -> List[JavaEnumConstant]:
        """Parse enum constants from the body text (portion before the first semicolon at depth 0)."""
        constants = []

        # Find the constant section (before first ';' at depth 0)
        depth = 0
        const_end = len(body)
        i = 0
        in_string = False
        in_char = False

        while i < len(body):
            ch = body[i]
            if ch == '"' and not in_char:
                in_string = not in_string
            elif ch == "'" and not in_string:
                in_char = not in_char
            elif not in_string and not in_char:
                if ch in ('{', '('):
                    depth += 1
                elif ch in ('}', ')'):
                    depth -= 1
                elif ch == ';' and depth == 0:
                    const_end = i
                    break
            i += 1

        const_section = body[:const_end].strip()
        if not const_section:
            return constants

        # Parse individual constants
        # Split on ',' at depth 0
        items = []
        depth = 0
        current = ""
        for ch in const_section:
            if ch in ('{', '(', '<', '['):
                depth += 1
                current += ch
            elif ch in ('}', ')', '>', ']'):
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                items.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            items.append(current.strip())

        for item in items:
            item = item.strip()
            if not item:
                continue

            # Remove annotations before name
            annotations = []
            while item.startswith('@'):
                ann_match = re.match(r'@(\w+(?:\([^)]*\))?)\s*', item)
                if ann_match:
                    annotations.append(ann_match.group(1))
                    item = item[ann_match.end():]
                else:
                    break

            # Parse name and optional arguments
            const_match = re.match(r'(\w+)(?:\s*\(([^)]*)\))?', item)
            if const_match:
                name = const_match.group(1)
                args_str = const_match.group(2)
                args = []
                if args_str:
                    args = [a.strip() for a in args_str.split(',') if a.strip()]

                constants.append(JavaEnumConstant(
                    name=name,
                    arguments=args,
                    annotations=annotations,
                ))

        return constants

    def extract(self, content: str, file_path: str = "") -> List[JavaEnumInfo]:
        """Extract all enum definitions from Java source code."""
        enums = []

        for match in self.ENUM_HEADER.finditer(content):
            javadoc = match.group(1)
            annotations_str = match.group(2) or ""
            modifiers_str = match.group(3) or ""
            enum_name = match.group(4)
            implements_str = match.group(5)

            brace_pos = match.end() - 1
            body = self._extract_brace_body(content, brace_pos)

            modifiers = modifiers_str.split() if modifiers_str else []
            annotations = re.findall(r'@(\w+(?:\([^)]*\))?)', annotations_str)
            implements = [s.strip() for s in implements_str.split(',')] if implements_str else []

            constants = self._parse_enum_constants(body) if body else []

            # Extract method names from body (after the constants section)
            methods = []
            if body:
                method_pattern = re.compile(
                    r'(?:public|protected|private|static|final|abstract|synchronized)\s+'
                    r'(?:[\w<>\[\].,?\s]+?)\s+(\w+)\s*\([^)]*\)',
                    re.MULTILINE
                )
                for m in method_pattern.finditer(body):
                    name = m.group(1)
                    if name not in ('if', 'for', 'while', 'switch', 'try', 'catch', 'return'):
                        methods.append(name)

            javadoc_text = None
            if javadoc:
                cleaned = re.sub(r'/\*\*|\*/|\*', '', javadoc).strip()
                lines = [l.strip() for l in cleaned.split('\n') if l.strip() and not l.strip().startswith('@')]
                if lines:
                    javadoc_text = lines[0][:200]

            line_number = content[:match.start()].count('\n') + 1

            enums.append(JavaEnumInfo(
                name=enum_name,
                constants=constants,
                implements=implements,
                annotations=annotations,
                methods=methods,
                file=file_path,
                line_number=line_number,
                is_exported='public' in modifiers,
                javadoc=javadoc_text,
            ))

        return enums
