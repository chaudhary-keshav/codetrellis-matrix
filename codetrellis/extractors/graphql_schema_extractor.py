"""
CodeTrellis GraphQL Schema Extractor — Phase 3 of v5.0 Universal Scanner
==========================================================================

Parses GraphQL schema files (.graphql, .gql) and introspection JSON to extract:
- Types (object, input, enum, union, interface, scalar)
- Query / Mutation / Subscription operations
- Field-level relationships and directives
- Schema stitching / federation hints

Handles both SDL-first and code-first (via introspection JSON) schemas.

Part of CodeTrellis v5.0 — Universal Scanner
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from codetrellis.file_classifier import GitignoreFilter


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class GraphQLField:
    """A field in a GraphQL type."""
    name: str
    type_ref: str            # "String!", "[User!]!", "ID"
    description: Optional[str] = None
    arguments: List[Dict[str, str]] = field(default_factory=list)
    directives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type_ref": self.type_ref,
            "description": self.description,
            "arguments": self.arguments,
            "directives": self.directives,
        }


@dataclass
class GraphQLType:
    """A GraphQL type definition."""
    name: str
    kind: str               # "type", "input", "enum", "union", "interface", "scalar"
    fields: List[GraphQLField] = field(default_factory=list)
    description: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    enum_values: List[str] = field(default_factory=list)
    union_types: List[str] = field(default_factory=list)
    directives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "kind": self.kind,
        }
        if self.description:
            result["description"] = self.description
        if self.fields:
            result["fields"] = [f.to_dict() for f in self.fields]
        if self.implements:
            result["implements"] = self.implements
        if self.enum_values:
            result["enum_values"] = self.enum_values
        if self.union_types:
            result["union_types"] = self.union_types
        if self.directives:
            result["directives"] = self.directives
        return result


@dataclass
class GraphQLOperation:
    """A query, mutation, or subscription field."""
    operation_type: str      # "query", "mutation", "subscription"
    name: str
    return_type: str
    arguments: List[Dict[str, str]] = field(default_factory=list)
    description: Optional[str] = None
    directives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_type": self.operation_type,
            "name": self.name,
            "return_type": self.return_type,
            "arguments": self.arguments,
            "description": self.description,
            "directives": self.directives,
        }


@dataclass
class GraphQLSchemaInfo:
    """Complete parsed GraphQL schema."""
    files: List[str] = field(default_factory=list)
    types: List[GraphQLType] = field(default_factory=list)
    operations: List[GraphQLOperation] = field(default_factory=list)
    directives: List[str] = field(default_factory=list)
    is_federation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files": self.files,
            "types": [t.to_dict() for t in self.types],
            "operations": [o.to_dict() for o in self.operations],
            "directives": self.directives,
            "is_federation": self.is_federation,
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format."""
        lines = []
        lines.append(f"# GraphQL Schema ({len(self.files)} file(s))")
        if self.is_federation:
            lines.append("# Apollo Federation detected")

        # Operations
        op_groups: Dict[str, List[GraphQLOperation]] = {}
        for op in self.operations:
            if op.operation_type not in op_groups:
                op_groups[op.operation_type] = []
            op_groups[op.operation_type].append(op)

        for op_type, ops in op_groups.items():
            lines.append(f"## {op_type.capitalize()}s ({len(ops)})")
            for op in ops:
                args = ', '.join(f"{a['name']}:{a['type']}" for a in op.arguments[:5])
                more = f",+{len(op.arguments)-5}" if len(op.arguments) > 5 else ""
                desc = f" # {op.description}" if op.description else ""
                lines.append(f"  {op.name}({args}{more}) -> {op.return_type}{desc}")

        # Types
        type_groups: Dict[str, List[GraphQLType]] = {}
        for t in self.types:
            if t.kind not in type_groups:
                type_groups[t.kind] = []
            type_groups[t.kind].append(t)

        for kind, types in type_groups.items():
            lines.append(f"## {kind.capitalize()}s ({len(types)})")
            for t in types:
                if kind == 'enum':
                    vals = ', '.join(t.enum_values[:8])
                    more = f",+{len(t.enum_values)-8}" if len(t.enum_values) > 8 else ""
                    lines.append(f"  {t.name}: {vals}{more}")
                elif kind == 'union':
                    lines.append(f"  {t.name} = {' | '.join(t.union_types)}")
                elif kind == 'scalar':
                    lines.append(f"  {t.name}")
                else:
                    field_str = ', '.join(f"{f.name}:{f.type_ref}" for f in t.fields[:8])
                    more = f",+{len(t.fields)-8}" if len(t.fields) > 8 else ""
                    impl = f" implements {','.join(t.implements)}" if t.implements else ""
                    lines.append(f"  {t.name}{impl}: {field_str}{more}")

        return '\n'.join(lines)


# =============================================================================
# Regex Patterns (SDL-first parsing without requiring graphql-core)
# =============================================================================

# Block-level patterns
TYPE_DEF_PATTERN = re.compile(
    r'(?:"""(?P<desc>.*?)"""\s*)?'
    r'(?:extend\s+)?'
    r'(?P<kind>type|input|interface)\s+'
    r'(?P<name>\w+)'
    r'(?:\s+implements\s+(?P<implements>[&\w\s]+?))?'
    r'(?:\s+@[\w()":\s,]+)*'
    r'\s*\{',
    re.DOTALL
)

ENUM_DEF_PATTERN = re.compile(
    r'(?:"""(?P<desc>.*?)"""\s*)?'
    r'enum\s+(?P<name>\w+)\s*\{(?P<body>[^}]*)\}',
    re.DOTALL
)

UNION_DEF_PATTERN = re.compile(
    r'(?:"""(?P<desc>.*?)"""\s*)?'
    r'union\s+(?P<name>\w+)\s*=\s*(?P<types>[|\w\s]+)',
    re.DOTALL
)

SCALAR_DEF_PATTERN = re.compile(
    r'scalar\s+(?P<name>\w+)',
)

FIELD_PATTERN = re.compile(
    r'(?:"""(?P<desc>.*?)"""\s*)?'
    r'(?:"(?P<desc2>[^"]+)"\s*)?'
    r'(?P<name>\w+)'
    r'(?:\((?P<args>[^)]*)\))?'
    r'\s*:\s*'
    r'(?P<type>[!\[\]\w]+)'
    r'(?P<directives>(?:\s+@\w+(?:\([^)]*\))?)*)',
    re.DOTALL
)

DIRECTIVE_PATTERN = re.compile(r'@(\w+)')

# Federation directives
FEDERATION_DIRECTIVES = {'key', 'extends', 'external', 'requires', 'provides'}


# =============================================================================
# GraphQL Schema Extractor
# =============================================================================

class GraphQLSchemaExtractor:
    """
    Parse GraphQL SDL files (.graphql, .gql) and introspection JSON.

    Does NOT require graphql-core; uses regex for SDL parsing.
    """

    # Root operation type names — not included as data types
    ROOT_TYPES = {'Query', 'Mutation', 'Subscription'}

    # Built-in scalars to ignore
    BUILTIN_SCALARS = {'String', 'Int', 'Float', 'Boolean', 'ID'}

    def can_extract(self, file_path: Path) -> bool:
        """Check if this is a GraphQL schema file."""
        name = file_path.name.lower()
        suffix = file_path.suffix.lower()

        # .graphql / .gql files
        if suffix in ('.graphql', '.gql'):
            return True

        # Introspection JSON
        if name in ('schema.json', 'graphql-schema.json', 'introspection.json'):
            return True

        return False

    def extract_from_directory(self, root_dir: Path,
                               gitignore_filter: Optional[GitignoreFilter] = None,
                               ) -> Optional[GraphQLSchemaInfo]:
        """
        Find and parse all GraphQL schema files in a project.

        Args:
            root_dir: Root directory to scan
            gitignore_filter: Optional GitignoreFilter to respect .gitignore rules

        Returns:
            GraphQLSchemaInfo or None if no schemas found
        """
        schema_files: List[Path] = []

        ignore_dirs = {
            'node_modules', '.git', 'dist', 'build', '__pycache__',
            'vendor', '.next', 'coverage',
        }

        gi = gitignore_filter

        for root, dirs, files in Path.walk(root_dir) if hasattr(Path, 'walk') else _walk_compat(root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs
                       and not (gi and not gi.is_empty and gi.should_ignore(
                           os.path.relpath(os.path.join(str(root), d), str(root_dir)),
                           is_dir=True))]
            for f in files:
                fp = root / f
                if self.can_extract(fp):
                    schema_files.append(fp)

        if not schema_files:
            return None

        result = GraphQLSchemaInfo()
        seen_types: Set[str] = set()

        for sf in schema_files:
            result.files.append(str(sf))
            try:
                content = sf.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue

            if sf.suffix.lower() == '.json':
                self._parse_introspection(content, result, seen_types)
            else:
                self._parse_sdl(content, result, seen_types)

        return result if (result.types or result.operations) else None

    def extract_from_file(self, file_path: Path) -> Optional[GraphQLSchemaInfo]:
        """Parse a single GraphQL file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            return None

        result = GraphQLSchemaInfo(files=[str(file_path)])

        if file_path.suffix.lower() == '.json':
            self._parse_introspection(content, result, set())
        else:
            self._parse_sdl(content, result, set())

        return result if (result.types or result.operations) else None

    # -----------------------------------------------------------------
    # SDL Parsing
    # -----------------------------------------------------------------

    def _parse_sdl(self, content: str, result: GraphQLSchemaInfo, seen: Set[str]) -> None:
        """Parse SDL (Schema Definition Language) text."""

        # Detect federation
        found_directives = set(DIRECTIVE_PATTERN.findall(content))
        if found_directives & FEDERATION_DIRECTIVES:
            result.is_federation = True

        # All unique directives
        for d in found_directives:
            if d not in result.directives:
                result.directives.append(d)

        # --- Enums ---
        for m in ENUM_DEF_PATTERN.finditer(content):
            name = m.group('name')
            if name in seen or name in self.BUILTIN_SCALARS:
                continue
            seen.add(name)
            body = m.group('body')
            values = [v.strip() for v in re.findall(r'(\w+)', body)]
            result.types.append(GraphQLType(
                name=name,
                kind='enum',
                enum_values=values,
                description=m.group('desc'),
            ))

        # --- Unions ---
        for m in UNION_DEF_PATTERN.finditer(content):
            name = m.group('name')
            if name in seen:
                continue
            seen.add(name)
            types_str = m.group('types')
            union_types = [t.strip() for t in types_str.split('|') if t.strip()]
            result.types.append(GraphQLType(
                name=name,
                kind='union',
                union_types=union_types,
                description=m.group('desc'),
            ))

        # --- Scalars ---
        for m in SCALAR_DEF_PATTERN.finditer(content):
            name = m.group('name')
            if name in seen or name in self.BUILTIN_SCALARS:
                continue
            seen.add(name)
            result.types.append(GraphQLType(name=name, kind='scalar'))

        # --- Types / Inputs / Interfaces ---
        for m in TYPE_DEF_PATTERN.finditer(content):
            name = m.group('name')
            kind = m.group('kind')

            # Extract the body between { and matching }
            start = m.end()
            body = self._extract_block(content, start)
            if body is None:
                continue

            # Parse implements
            implements = []
            impl_str = m.group('implements')
            if impl_str:
                implements = [t.strip() for t in re.split(r'[&\s]+', impl_str) if t.strip()]

            # Parse fields
            fields = self._parse_fields(body)

            # Root types → operations
            if name in self.ROOT_TYPES:
                op_type = name.lower()
                for f in fields:
                    result.operations.append(GraphQLOperation(
                        operation_type=op_type,
                        name=f.name,
                        return_type=f.type_ref,
                        arguments=f.arguments,
                        description=f.description,
                        directives=f.directives,
                    ))
                continue

            if name in seen:
                continue
            seen.add(name)

            result.types.append(GraphQLType(
                name=name,
                kind=kind,
                fields=fields,
                description=m.group('desc'),
                implements=implements,
                directives=list(DIRECTIVE_PATTERN.findall(m.group(0))),
            ))

    def _extract_block(self, text: str, start: int) -> Optional[str]:
        """Extract content between balanced braces starting at position start."""
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
            i += 1
        if depth != 0:
            return None
        return text[start:i - 1]

    def _parse_fields(self, body: str) -> List[GraphQLField]:
        """Parse fields from a type body."""
        fields = []
        for m in FIELD_PATTERN.finditer(body):
            name = m.group('name')
            if name.startswith('__'):
                continue

            # Arguments
            args = []
            args_str = m.group('args')
            if args_str:
                for arg_m in re.finditer(r'(\w+)\s*:\s*([!\[\]\w]+)', args_str):
                    args.append({"name": arg_m.group(1), "type": arg_m.group(2)})

            # Directives
            directives_str = m.group('directives') or ''
            directives = DIRECTIVE_PATTERN.findall(directives_str)

            description = m.group('desc') or m.group('desc2')

            fields.append(GraphQLField(
                name=name,
                type_ref=m.group('type'),
                description=description,
                arguments=args,
                directives=directives,
            ))

        return fields

    # -----------------------------------------------------------------
    # Introspection JSON Parsing
    # -----------------------------------------------------------------

    def _parse_introspection(self, content: str, result: GraphQLSchemaInfo, seen: Set[str]) -> None:
        """Parse a GraphQL introspection JSON response."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return

        # Introspection result may be wrapped in { "data": { "__schema": ... } }
        schema = data
        if 'data' in data:
            schema = data['data']
        if '__schema' in schema:
            schema = schema['__schema']

        types = schema.get('types', [])
        root_type_names: Set[str] = set()

        # Identify root operation types
        for root_key in ('queryType', 'mutationType', 'subscriptionType'):
            rt = schema.get(root_key)
            if rt and rt.get('name'):
                root_type_names.add(rt['name'])

        for t in types:
            name = t.get('name', '')
            kind = t.get('kind', '').lower()

            # Skip internal types
            if name.startswith('__'):
                continue

            # Map kind
            kind_map = {
                'object': 'type',
                'input_object': 'input',
                'interface': 'interface',
                'enum': 'enum',
                'union': 'union',
                'scalar': 'scalar',
            }
            mapped_kind = kind_map.get(kind, kind)

            # Root types → operations
            if name in root_type_names:
                op_type_map = {'Query': 'query', 'Mutation': 'mutation', 'Subscription': 'subscription'}
                op_type = op_type_map.get(name, name.lower())
                for f in t.get('fields', []):
                    args = [
                        {"name": a.get('name', ''), "type": self._unpack_introspection_type(a.get('type', {}))}
                        for a in f.get('args', [])
                    ]
                    result.operations.append(GraphQLOperation(
                        operation_type=op_type,
                        name=f.get('name', ''),
                        return_type=self._unpack_introspection_type(f.get('type', {})),
                        arguments=args,
                        description=f.get('description'),
                    ))
                continue

            if name in seen or name in self.BUILTIN_SCALARS:
                continue
            seen.add(name)

            gql_type = GraphQLType(
                name=name,
                kind=mapped_kind,
                description=t.get('description'),
            )

            if mapped_kind == 'enum':
                gql_type.enum_values = [v.get('name', '') for v in t.get('enumValues', [])]
            elif mapped_kind == 'union':
                gql_type.union_types = [pt.get('name', '') for pt in t.get('possibleTypes', [])]
            elif mapped_kind in ('type', 'input', 'interface'):
                gql_type.implements = [
                    iface.get('name', '') for iface in t.get('interfaces', [])
                ]
                for f in t.get('fields', t.get('inputFields', [])) or []:
                    args = [
                        {"name": a.get('name', ''), "type": self._unpack_introspection_type(a.get('type', {}))}
                        for a in f.get('args', [])
                    ]
                    gql_type.fields.append(GraphQLField(
                        name=f.get('name', ''),
                        type_ref=self._unpack_introspection_type(f.get('type', {})),
                        description=f.get('description'),
                        arguments=args,
                    ))

            result.types.append(gql_type)

    def _unpack_introspection_type(self, type_obj: Dict) -> str:
        """Recursively unpack an introspection __Type object into a string like '[User!]!'."""
        if not type_obj:
            return '?'
        kind = type_obj.get('kind', '')
        name = type_obj.get('name')
        of_type = type_obj.get('ofType')

        if kind == 'NON_NULL':
            inner = self._unpack_introspection_type(of_type or {})
            return f"{inner}!"
        elif kind == 'LIST':
            inner = self._unpack_introspection_type(of_type or {})
            return f"[{inner}]"
        elif name:
            return name
        return '?'


# =============================================================================
# Compatibility helper for Python < 3.12
# =============================================================================

def _walk_compat(root: Path):
    """os.walk wrapper that yields (Path, dirs, files)."""
    import os
    for dirpath, dirs, files in os.walk(root):
        yield Path(dirpath), dirs, files
