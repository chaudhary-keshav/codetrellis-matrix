"""
PythonTypeAliasExtractor - Extracts type aliases from Python source code.

This extractor parses Python type alias definitions and extracts:
- TypeAlias declarations (PEP 613)
- Simple type aliases (Type = OtherType)
- Union types (Type = X | Y)
- Literal types
- Generic type aliases
- TypeVar definitions

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class TypeAliasKind(Enum):
    """Kind of type alias."""
    SIMPLE = "simple"
    UNION = "union"
    LITERAL = "literal"
    GENERIC = "generic"
    TYPEVAR = "typevar"
    CALLABLE = "callable"
    OPTIONAL = "optional"


@dataclass
class PythonTypeAliasInfo:
    """Complete information about a Python type alias."""
    name: str
    type: str
    kind: TypeAliasKind = TypeAliasKind.SIMPLE
    generics: List[str] = field(default_factory=list)
    is_exported: bool = True  # Python doesn't have export, always True
    line_number: int = 0


class PythonTypeAliasExtractor:
    """
    Extracts Python type alias definitions from source code.

    Handles:
    - TypeAlias annotation: UserId: TypeAlias = int
    - Simple aliases: UserId = int
    - Union types: Result = str | int | None
    - Literal types: Status = Literal["a", "b", "c"]
    - Generic aliases: Response = dict[str, T]
    - TypeVar: T = TypeVar("T", bound=int)
    """

    # Pattern for TypeAlias annotation
    TYPEALIAS_PATTERN = re.compile(
        r'^(\w+)\s*:\s*TypeAlias\s*=\s*(.+)$',
        re.MULTILINE
    )

    # Pattern for simple type alias (must look like a type, not a value)
    SIMPLE_ALIAS_PATTERN = re.compile(
        r'^(\w+)\s*=\s*((?!TypeVar)[A-Z][\w\[\], |]+)$',
        re.MULTILINE
    )

    # Pattern for TypeVar
    TYPEVAR_PATTERN = re.compile(
        r'^(\w+)\s*=\s*TypeVar\s*\(\s*[\'"](\w+)[\'"](?:,\s*(.+))?\)',
        re.MULTILINE
    )

    # Pattern for Literal type
    LITERAL_PATTERN = re.compile(
        r'^(\w+)\s*(?::\s*TypeAlias)?\s*=\s*Literal\[([^\]]+)\]',
        re.MULTILINE
    )

    # Pattern for Union type (using |)
    UNION_PATTERN = re.compile(
        r'^(\w+)\s*(?::\s*TypeAlias)?\s*=\s*([^=\n]+\|[^=\n]+)$',
        re.MULTILINE
    )

    # Pattern for Optional
    OPTIONAL_PATTERN = re.compile(
        r'^(\w+)\s*(?::\s*TypeAlias)?\s*=\s*Optional\[([^\]]+)\]',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the type alias extractor."""
        pass

    def extract(self, content: str) -> List[PythonTypeAliasInfo]:
        """
        Extract all type aliases from Python content.

        Args:
            content: Python source code

        Returns:
            List of PythonTypeAliasInfo objects
        """
        type_aliases = []
        seen_names = set()

        # Extract TypeVars first (they're special)
        for match in self.TYPEVAR_PATTERN.finditer(content):
            name = match.group(1)
            if name in seen_names:
                continue
            seen_names.add(name)

            typevar_name = match.group(2)
            constraints = match.group(3) or ""

            # Parse bound
            bound = None
            if 'bound=' in constraints:
                bound_match = re.search(r'bound\s*=\s*(\w+)', constraints)
                if bound_match:
                    bound = bound_match.group(1)

            type_str = "TypeVar"
            if bound:
                type_str = f"TypeVar(bound={bound})"

            type_aliases.append(PythonTypeAliasInfo(
                name=name,
                type=type_str,
                kind=TypeAliasKind.TYPEVAR,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Extract Literal types
        for match in self.LITERAL_PATTERN.finditer(content):
            name = match.group(1)
            if name in seen_names:
                continue
            seen_names.add(name)

            values = match.group(2)
            type_str = f"Literal[{values}]"

            type_aliases.append(PythonTypeAliasInfo(
                name=name,
                type=type_str,
                kind=TypeAliasKind.LITERAL,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Extract Optional types
        for match in self.OPTIONAL_PATTERN.finditer(content):
            name = match.group(1)
            if name in seen_names:
                continue
            seen_names.add(name)

            inner_type = match.group(2).strip()
            type_str = f"{inner_type} | None"

            type_aliases.append(PythonTypeAliasInfo(
                name=name,
                type=type_str,
                kind=TypeAliasKind.OPTIONAL,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Extract Union types (using |)
        for match in self.UNION_PATTERN.finditer(content):
            name = match.group(1)
            if name in seen_names:
                continue
            seen_names.add(name)

            type_str = match.group(2).strip()

            # Determine if it's Optional (has None)
            kind = TypeAliasKind.UNION
            if 'None' in type_str and type_str.count('|') == 1:
                kind = TypeAliasKind.OPTIONAL

            type_aliases.append(PythonTypeAliasInfo(
                name=name,
                type=type_str,
                kind=kind,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Extract TypeAlias annotated aliases
        for match in self.TYPEALIAS_PATTERN.finditer(content):
            name = match.group(1)
            if name in seen_names:
                continue
            seen_names.add(name)

            type_str = match.group(2).strip()
            kind = self._determine_kind(type_str)
            generics = self._extract_generics(type_str)

            type_aliases.append(PythonTypeAliasInfo(
                name=name,
                type=type_str,
                kind=kind,
                generics=generics,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Extract simple aliases (careful to not catch regular assignments)
        for match in self.SIMPLE_ALIAS_PATTERN.finditer(content):
            name = match.group(1)
            if name in seen_names:
                continue

            type_str = match.group(2).strip()

            # Skip if it looks like a value assignment
            if type_str.startswith('"') or type_str.startswith("'"):
                continue
            if type_str.isdigit():
                continue
            if type_str in ('True', 'False', 'None'):
                continue

            seen_names.add(name)
            kind = self._determine_kind(type_str)
            generics = self._extract_generics(type_str)

            type_aliases.append(PythonTypeAliasInfo(
                name=name,
                type=type_str,
                kind=kind,
                generics=generics,
                line_number=content[:match.start()].count('\n') + 1
            ))

        return type_aliases

    def _determine_kind(self, type_str: str) -> TypeAliasKind:
        """Determine the kind of type alias."""
        if '|' in type_str:
            if 'None' in type_str and type_str.count('|') == 1:
                return TypeAliasKind.OPTIONAL
            return TypeAliasKind.UNION

        if 'Literal[' in type_str:
            return TypeAliasKind.LITERAL

        if 'Callable[' in type_str:
            return TypeAliasKind.CALLABLE

        if 'Optional[' in type_str:
            return TypeAliasKind.OPTIONAL

        if '[' in type_str:
            return TypeAliasKind.GENERIC

        return TypeAliasKind.SIMPLE

    def _extract_generics(self, type_str: str) -> List[str]:
        """Extract generic type parameters."""
        generics = []

        # Look for TypeVar references
        typevar_refs = re.findall(r'\b([A-Z])\b', type_str)
        for ref in typevar_refs:
            if ref not in generics and len(ref) == 1:
                generics.append(ref)

        return generics

    def to_codetrellis_format(self, type_aliases: List[PythonTypeAliasInfo]) -> str:
        """
        Convert extracted type aliases to CodeTrellis format.

        Args:
            type_aliases: List of PythonTypeAliasInfo objects

        Returns:
            CodeTrellis formatted string
        """
        if not type_aliases:
            return ""

        lines = ["[TYPE_ALIASES]"]

        for ta in type_aliases:
            parts = [ta.name]

            # Add generics if present
            if ta.generics:
                parts[0] = f"{ta.name}<{','.join(ta.generics)}>"

            # Add type definition
            parts.append(f"={ta.type}")

            # Add kind
            parts.append(f"kind:{ta.kind.value}")

            lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_type_aliases(content: str) -> List[PythonTypeAliasInfo]:
    """Extract type aliases from Python content."""
    extractor = PythonTypeAliasExtractor()
    return extractor.extract(content)
