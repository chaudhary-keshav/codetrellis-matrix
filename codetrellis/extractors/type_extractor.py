"""
TypeExtractor - Extracts TypeScript type aliases from source code.

This extractor parses TypeScript type alias declarations and extracts:
- Type names and export status
- Simple type aliases (type X = string)
- Union types (type X = 'a' | 'b' | 'c')
- Intersection types (type X = A & B)
- Generic type aliases (type X<T> = T | null)
- Function types (type X = (a: A) => B)
- Object literal types (type X = { a: string; b: number })
- Tuple types (type X = [string, number])
- Conditional types (type X = T extends U ? A : B)
- Mapped types (type X = { [K in keyof T]: T[K] })
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TypeAliasInfo:
    """Complete information about a TypeScript type alias."""
    name: str
    type: str
    generics: List[str] = field(default_factory=list)
    is_exported: bool = False
    description: str = ""
    line_number: int = 0
    kind: str = "simple"  # simple, union, intersection, function, object, tuple, conditional, mapped


class TypeExtractor:
    """
    Extracts TypeScript type alias definitions from source code.

    Handles:
    - Simple type aliases
    - Union and intersection types
    - Generic type aliases
    - Function type aliases
    - Object literal types
    - Tuple types
    - Conditional types
    - Mapped types
    """

    # Regex pattern for type alias declarations
    TYPE_ALIAS_PATTERN = re.compile(
        r'(?P<jsdoc>/\*\*[\s\S]*?\*/\s*)?'  # Optional JSDoc
        r'(?P<export>export\s+)?'            # Optional export
        r'type\s+'                            # type keyword
        r'(?P<name>\w+)'                      # Type name
        r'(?:<(?P<generics>[^>=]+)>)?'        # Optional generics (stop at = or >)
        r'\s*=\s*'                            # Assignment
        r'(?P<type_def>.+?)'                  # Type definition (non-greedy)
        r'(?=\s*(?:;|$|\nexport|\ntype|\ninterface|\nclass|\nfunction|\nconst|\nlet|\nvar|\n\n))',  # Lookahead for termination
        re.MULTILINE | re.DOTALL
    )

    def __init__(self):
        """Initialize the type extractor."""
        self._comment_ranges: List[tuple] = []

    def extract(self, content: str) -> List[TypeAliasInfo]:
        """
        Extract all type aliases from TypeScript content.

        Args:
            content: TypeScript source code

        Returns:
            List of TypeAliasInfo objects
        """
        # Find comment ranges to skip
        self._find_comment_ranges(content)

        types = []

        # Use a more reliable line-by-line approach for type extraction
        types = self._extract_types_linewise(content)

        return types

    def _find_comment_ranges(self, content: str) -> None:
        """Find all comment ranges to skip during parsing."""
        self._comment_ranges = []

        # Single line comments
        for match in re.finditer(r'//[^\n]*', content):
            self._comment_ranges.append((match.start(), match.end()))

        # Multi-line comments (but not JSDoc)
        for match in re.finditer(r'/\*(?!\*)[\s\S]*?\*/', content):
            self._comment_ranges.append((match.start(), match.end()))

    def _is_in_comment(self, position: int) -> bool:
        """Check if a position is inside a comment."""
        for start, end in self._comment_ranges:
            if start <= position < end:
                return True
        return False

    def _extract_types_linewise(self, content: str) -> List[TypeAliasInfo]:
        """Extract type aliases using line-by-line parsing."""
        types = []
        lines = content.split('\n')

        i = 0
        current_jsdoc = ""

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Capture JSDoc
            if '/**' in stripped:
                jsdoc_lines = [line]
                while '*/' not in lines[i]:
                    i += 1
                    if i < len(lines):
                        jsdoc_lines.append(lines[i])
                current_jsdoc = '\n'.join(jsdoc_lines)
                i += 1
                continue

            # Check for type declaration
            type_match = re.match(
                r'^(?P<export>export\s+)?type\s+(?P<name>\w+)(?:<(?P<generics>[^>]+)>)?\s*=\s*(?P<start>.*)',
                stripped
            )

            if type_match:
                name = type_match.group('name')
                is_exported = type_match.group('export') is not None
                generics_str = type_match.group('generics') or ""
                generics = [g.strip() for g in generics_str.split(',')] if generics_str else []

                # Get the type definition - may span multiple lines
                type_def = type_match.group('start')

                # If the type definition doesn't end with ; and has unbalanced brackets, continue
                if not self._is_complete_type(type_def):
                    j = i + 1
                    while j < len(lines) and not self._is_complete_type(type_def):
                        type_def += '\n' + lines[j]
                        j += 1
                    i = j - 1

                # Clean up the type definition
                type_def = type_def.strip()
                if type_def.endswith(';'):
                    type_def = type_def[:-1].strip()

                # Determine the kind of type
                kind = self._determine_type_kind(type_def)

                # Parse JSDoc description
                description = self._parse_jsdoc_description(current_jsdoc)

                types.append(TypeAliasInfo(
                    name=name,
                    type=type_def,
                    generics=generics,
                    is_exported=is_exported,
                    description=description,
                    line_number=i + 1,
                    kind=kind
                ))

                current_jsdoc = ""

            i += 1

        return types

    def _is_complete_type(self, type_def: str) -> bool:
        """Check if a type definition is complete (balanced brackets and ends properly)."""
        # Count brackets
        brackets = {'(': 0, '[': 0, '{': 0, '<': 0}
        closing = {')': '(', ']': '[', '}': '{', '>': '<'}

        in_string = False
        string_char = None

        for char in type_def:
            # Handle strings
            if char in '"\'`' and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
                string_char = None
            elif not in_string:
                if char in brackets:
                    brackets[char] += 1
                elif char in closing:
                    brackets[closing[char]] -= 1

        # Check if all brackets are balanced
        all_balanced = all(count == 0 for count in brackets.values())

        # Check if it ends with a semicolon or looks complete
        stripped = type_def.strip()
        ends_properly = stripped.endswith(';') or stripped.endswith('}') or stripped.endswith(')') or stripped.endswith('>') or stripped.endswith(']') or stripped.endswith("'") or stripped.endswith('"')

        return all_balanced and (stripped.endswith(';') or all_balanced)

    def _determine_type_kind(self, type_def: str) -> str:
        """Determine the kind of type alias."""
        type_def = type_def.strip()

        # Check for mapped type: { [K in keyof T]: ... }
        if re.search(r'\[\s*\w+\s+in\s+', type_def):
            return "mapped"

        # Check for conditional type: T extends U ? A : B
        if re.search(r'\bextends\b.*\?.*:', type_def):
            return "conditional"

        # Check for tuple type: [A, B, C]
        if type_def.startswith('[') and type_def.endswith(']'):
            return "tuple"

        # Check for object literal type: { ... }
        if type_def.startswith('{') and type_def.endswith('}'):
            return "object"

        # Check for function type: (...) => ...
        if '=>' in type_def and '(' in type_def:
            return "function"

        # Check for intersection type: A & B
        if ' & ' in type_def or type_def.startswith('(') and ' & ' in type_def:
            return "intersection"

        # Check for union type: A | B or 'a' | 'b'
        if ' | ' in type_def or re.search(r"'\w+'\s*\|", type_def):
            return "union"

        return "simple"

    def _parse_jsdoc_description(self, jsdoc: str) -> str:
        """Extract description from JSDoc comment."""
        if not jsdoc:
            return ""

        # Remove /** and */
        content = jsdoc.replace('/**', '').replace('*/', '')

        # Remove leading * from each line
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('*'):
                line = line[1:].strip()
            # Skip @tags
            if line.startswith('@'):
                continue
            if line:
                lines.append(line)

        return ' '.join(lines)

    def to_codetrellis_format(self, types: List[TypeAliasInfo]) -> str:
        """
        Convert extracted types to CodeTrellis format.

        Args:
            types: List of extracted type aliases

        Returns:
            CodeTrellis formatted string
        """
        if not types:
            return ""

        lines = ["[TYPES]"]

        for type_info in types:
            export_marker = "export " if type_info.is_exported else ""
            generics = f"<{', '.join(type_info.generics)}>" if type_info.generics else ""

            # Format based on kind
            if type_info.kind == "union":
                # For union types, format each option on a line or compact
                lines.append(f"  {export_marker}type {type_info.name}{generics} = {type_info.type}")
            else:
                lines.append(f"  {export_marker}type {type_info.name}{generics} = {type_info.type}")

        return '\n'.join(lines)

    def extract_union_values(self, type_info: TypeAliasInfo) -> List[str]:
        """
        Extract individual values from a union type.

        Args:
            type_info: A union type alias

        Returns:
            List of union member values
        """
        if type_info.kind != "union":
            return [type_info.type]

        # Split by | but be careful of nested types
        values = []
        current = ""
        depth = 0

        for char in type_info.type:
            if char in '(<{':
                depth += 1
                current += char
            elif char in ')>}':
                depth -= 1
                current += char
            elif char == '|' and depth == 0:
                values.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            values.append(current.strip())

        return values


# Convenience function
def extract_types(content: str) -> List[TypeAliasInfo]:
    """
    Convenience function to extract type aliases from content.

    Args:
        content: TypeScript source code

    Returns:
        List of TypeAliasInfo objects
    """
    extractor = TypeExtractor()
    return extractor.extract(content)
