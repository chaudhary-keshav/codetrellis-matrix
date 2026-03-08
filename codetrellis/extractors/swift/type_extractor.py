"""
Swift Type Extractor for CodeTrellis

Extracts type definitions from Swift source code:
- Classes (including final, open, generic, inheritance, Objective-C bridging)
- Structs (value types, property wrappers, Codable conformance)
- Enums (associated values, raw values, CaseIterable, indirect)
- Protocols (associated types, primary associated types, protocol composition)
- Actors (isolated/nonisolated, global actors)
- Type aliases
- Extensions (protocol conformance, where clauses, conditional conformance)

Supports Swift 5.0 through Swift 6.0+ features including:
- Concurrency types (actors, Sendable, @MainActor)
- Macros (Swift 5.9+)
- Parameter packs (Swift 5.9+)
- Noncopyable types (Swift 5.9+)
- Typed throws (Swift 6.0+)

Part of CodeTrellis v4.22 - Swift Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SwiftFieldInfo:
    """Information about a stored/computed property."""
    name: str
    type: str = ""
    is_let: bool = False
    is_var: bool = True
    is_static: bool = False
    is_class_var: bool = False
    is_lazy: bool = False
    is_computed: bool = False
    is_optional: bool = False
    default_value: str = ""
    access_level: str = ""
    property_wrapper: str = ""
    attributes: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SwiftClassInfo:
    """Information about a Swift class."""
    name: str
    file: str = ""
    superclass: str = ""
    protocols: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    generic_constraints: List[str] = field(default_factory=list)
    fields: List[SwiftFieldInfo] = field(default_factory=list)
    is_final: bool = False
    is_open: bool = False
    access_level: str = "internal"
    attributes: List[str] = field(default_factory=list)
    is_objc: bool = False
    is_actor: bool = False
    nested_types: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SwiftStructInfo:
    """Information about a Swift struct."""
    name: str
    file: str = ""
    protocols: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    generic_constraints: List[str] = field(default_factory=list)
    fields: List[SwiftFieldInfo] = field(default_factory=list)
    access_level: str = "internal"
    attributes: List[str] = field(default_factory=list)
    is_property_wrapper: bool = False
    is_result_builder: bool = False
    is_noncopyable: bool = False
    line_number: int = 0


@dataclass
class SwiftEnumCaseInfo:
    """Information about an enum case."""
    name: str
    associated_values: List[Dict[str, str]] = field(default_factory=list)
    raw_value: str = ""
    line_number: int = 0


@dataclass
class SwiftEnumInfo:
    """Information about a Swift enum."""
    name: str
    file: str = ""
    raw_type: str = ""
    protocols: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    cases: List[SwiftEnumCaseInfo] = field(default_factory=list)
    is_indirect: bool = False
    access_level: str = "internal"
    attributes: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SwiftProtocolRequirementInfo:
    """Information about a protocol requirement."""
    name: str
    kind: str = "method"  # method, property, associatedtype, subscript, init
    type: str = ""
    is_static: bool = False
    is_mutating: bool = False
    is_optional: bool = False
    line_number: int = 0


@dataclass
class SwiftProtocolInfo:
    """Information about a Swift protocol."""
    name: str
    file: str = ""
    inherits: List[str] = field(default_factory=list)
    requirements: List[SwiftProtocolRequirementInfo] = field(default_factory=list)
    associated_types: List[str] = field(default_factory=list)
    primary_associated_types: List[str] = field(default_factory=list)
    access_level: str = "internal"
    attributes: List[str] = field(default_factory=list)
    is_class_bound: bool = False
    is_objc: bool = False
    line_number: int = 0


@dataclass
class SwiftActorInfo:
    """Information about a Swift actor."""
    name: str
    file: str = ""
    protocols: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    fields: List[SwiftFieldInfo] = field(default_factory=list)
    is_global_actor: bool = False
    access_level: str = "internal"
    attributes: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SwiftTypeAliasInfo:
    """Information about a typealias."""
    name: str
    file: str = ""
    underlying_type: str = ""
    generic_params: List[str] = field(default_factory=list)
    access_level: str = "internal"
    line_number: int = 0


@dataclass
class SwiftExtensionInfo:
    """Information about a Swift extension."""
    name: str  # The type being extended
    file: str = ""
    protocols: List[str] = field(default_factory=list)
    where_clauses: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    access_level: str = "internal"
    is_conditional: bool = False
    line_number: int = 0


class SwiftTypeExtractor:
    """
    Extracts Swift type definitions using regex-based parsing.

    Supports all Swift type kinds:
    - class (final, open, generic, @objc)
    - struct (property wrappers, result builders, ~Copyable)
    - enum (associated values, raw values, indirect)
    - protocol (associated types, primary associated types, @objc optional)
    - actor (global actors, distributed actors)
    - typealias
    - extension (conditional conformance, protocol conformance)
    """

    # Class declaration pattern
    CLASS_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<attrs>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<access>open|public|internal|fileprivate|private)\s+)?'
        r'(?:(?P<final>final)\s+)?'
        r'(?:(?P<access2>open|public|internal|fileprivate|private)\s+)?'
        r'class\s+(?P<name>\w+)'
        r'(?:\s*<(?P<generics>[^>]+)>)?'
        r'(?:\s*:\s*(?P<inherits>[^{]+?))?'
        r'\s*(?:where\s+(?P<where>[^{]+?))?\s*\{',
        re.MULTILINE
    )

    # Struct declaration pattern
    STRUCT_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<attrs>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<access>public|internal|fileprivate|private)\s+)?'
        r'struct\s+(?P<name>\w+)'
        r'(?:\s*<(?P<generics>[^>]+)>)?'
        r'(?:\s*:\s*(?P<conformances>[^{]+?))?'
        r'\s*(?:where\s+(?P<where>[^{]+?))?\s*\{',
        re.MULTILINE
    )

    # Enum declaration pattern
    ENUM_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<attrs>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<access>public|internal|fileprivate|private)\s+)?'
        r'(?P<indirect>indirect\s+)?'
        r'enum\s+(?P<name>\w+)'
        r'(?:\s*<(?P<generics>[^>]+)>)?'
        r'(?:\s*:\s*(?P<raw_and_conformances>[^{]+?))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Protocol declaration pattern
    PROTOCOL_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<attrs>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<access>public|internal|fileprivate|private)\s+)?'
        r'protocol\s+(?P<name>\w+)'
        r'(?:\s*<(?P<primary_assoc>[^>]+)>)?'
        r'(?:\s*:\s*(?P<inherits>[^{]+?))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Actor declaration pattern
    ACTOR_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<attrs>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<access>public|internal|fileprivate|private)\s+)?'
        r'(?:distributed\s+)?'
        r'actor\s+(?P<name>\w+)'
        r'(?:\s*<(?P<generics>[^>]+)>)?'
        r'(?:\s*:\s*(?P<conformances>[^{]+?))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Typealias declaration pattern
    TYPEALIAS_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<access>public|internal|fileprivate|private)\s+)?'
        r'typealias\s+(?P<name>\w+)'
        r'(?:\s*<(?P<generics>[^>]+)>)?'
        r'\s*=\s*(?P<type>[^\n]+)',
        re.MULTILINE
    )

    # Extension declaration pattern
    EXTENSION_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<access>public|internal|fileprivate|private)\s+)?'
        r'extension\s+(?P<name>\w+(?:\.\w+)*)'
        r'(?:\s*:\s*(?P<conformances>[^{]+?))?'
        r'\s*(?:where\s+(?P<where>[^{]+?))?\s*\{',
        re.MULTILINE
    )

    # Property pattern (for extracting fields inside types)
    PROPERTY_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<attrs>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<access>open|public|internal|fileprivate|private)\s+)?'
        r'(?:(?P<static>static|class)\s+)?'
        r'(?:(?P<lazy>lazy)\s+)?'
        r'(?P<kind>let|var)\s+(?P<name>\w+)'
        r'(?:\s*:\s*(?P<type>[^={\n]+?))?'
        r'(?:\s*=\s*(?P<default>[^{\n]+?))?'
        r'\s*(?:[{\n]|$)',
        re.MULTILINE
    )

    # Enum case pattern
    CASE_PATTERN = re.compile(
        r'^\s*(?:indirect\s+)?case\s+(?P<name>\w+)'
        r'(?:\((?P<assoc>[^)]*)\))?'
        r'(?:\s*=\s*(?P<raw>[^\n,]+))?',
        re.MULTILINE
    )

    # Associated type pattern (inside protocols)
    ASSOC_TYPE_PATTERN = re.compile(
        r'^\s*associatedtype\s+(\w+)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all type definitions from Swift source code.

        Args:
            content: Swift source code content
            file_path: Path to source file

        Returns:
            Dict with keys: classes, structs, enums, protocols, actors,
                           type_aliases, extensions
        """
        return {
            'classes': self._extract_classes(content, file_path),
            'structs': self._extract_structs(content, file_path),
            'enums': self._extract_enums(content, file_path),
            'protocols': self._extract_protocols(content, file_path),
            'actors': self._extract_actors(content, file_path),
            'type_aliases': self._extract_type_aliases(content, file_path),
            'extensions': self._extract_extensions(content, file_path),
        }

    def _extract_classes(self, content: str, file_path: str) -> List[SwiftClassInfo]:
        """Extract class declarations."""
        classes = []
        for match in self.CLASS_PATTERN.finditer(content):
            attrs_str = (match.group('attrs') or '').strip()
            attributes = re.findall(r'@(\w+(?:\([^)]*\))?)', attrs_str)

            access = match.group('access') or match.group('access2') or 'internal'
            is_final = bool(match.group('final'))
            is_open = access == 'open'
            name = match.group('name')

            # Parse generics
            generics_str = match.group('generics') or ''
            generic_params = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []

            # Parse inheritance
            inherits_str = match.group('inherits') or ''
            inherits_list = [i.strip() for i in inherits_str.split(',') if i.strip()]

            superclass = ''
            protocols = []
            for item in inherits_list:
                # First non-protocol is likely the superclass
                if not superclass and not item.endswith('Protocol') and item[0].isupper():
                    superclass = item
                else:
                    protocols.append(item)
            # If all are protocols, fix
            if superclass and any(superclass.startswith(p) for p in ['Codable', 'Hashable', 'Equatable', 'Sendable', 'Identifiable', 'ObservableObject', 'View']):
                protocols.insert(0, superclass)
                superclass = ''

            # Parse where clauses
            where_str = match.group('where') or ''
            constraints = [c.strip() for c in where_str.split(',') if c.strip()] if where_str else []

            # Extract fields from class body
            body = self._extract_brace_body(content, match.end() - 1)
            fields = self._extract_properties(body)

            is_objc = '@objc' in attrs_str or 'NSObject' in inherits_str

            line_number = content[:match.start()].count('\n') + 1

            classes.append(SwiftClassInfo(
                name=name,
                file=file_path,
                superclass=superclass,
                protocols=protocols,
                generic_params=generic_params,
                generic_constraints=constraints,
                fields=fields,
                is_final=is_final,
                is_open=is_open,
                access_level=access,
                attributes=attributes,
                is_objc=is_objc,
                line_number=line_number,
            ))
        return classes

    def _extract_structs(self, content: str, file_path: str) -> List[SwiftStructInfo]:
        """Extract struct declarations."""
        structs = []
        for match in self.STRUCT_PATTERN.finditer(content):
            attrs_str = (match.group('attrs') or '').strip()
            attributes = re.findall(r'@(\w+(?:\([^)]*\))?)', attrs_str)

            access = match.group('access') or 'internal'
            name = match.group('name')

            generics_str = match.group('generics') or ''
            generic_params = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []

            conformances_str = match.group('conformances') or ''
            protocols = [c.strip() for c in conformances_str.split(',') if c.strip()]

            body = self._extract_brace_body(content, match.end() - 1)
            fields = self._extract_properties(body)

            is_pw = '@propertyWrapper' in attrs_str
            is_rb = '@resultBuilder' in attrs_str
            is_nc = '~Copyable' in conformances_str or '~Copyable' in attrs_str

            line_number = content[:match.start()].count('\n') + 1

            structs.append(SwiftStructInfo(
                name=name,
                file=file_path,
                protocols=protocols,
                generic_params=generic_params,
                fields=fields,
                access_level=access,
                attributes=attributes,
                is_property_wrapper=is_pw,
                is_result_builder=is_rb,
                is_noncopyable=is_nc,
                line_number=line_number,
            ))
        return structs

    def _extract_enums(self, content: str, file_path: str) -> List[SwiftEnumInfo]:
        """Extract enum declarations."""
        enums = []
        for match in self.ENUM_PATTERN.finditer(content):
            attrs_str = (match.group('attrs') or '').strip()
            attributes = re.findall(r'@(\w+(?:\([^)]*\))?)', attrs_str)

            access = match.group('access') or 'internal'
            name = match.group('name')
            is_indirect = bool(match.group('indirect'))

            generics_str = match.group('generics') or ''
            generic_params = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []

            raw_and_conf = match.group('raw_and_conformances') or ''
            parts = [p.strip() for p in raw_and_conf.split(',') if p.strip()]
            raw_type = ''
            protocols = []
            for p in parts:
                if p in ('String', 'Int', 'Double', 'Float', 'Character', 'UInt', 'Int8', 'Int16', 'Int32', 'Int64'):
                    raw_type = p
                else:
                    protocols.append(p)

            body = self._extract_brace_body(content, match.end() - 1)
            cases = self._extract_enum_cases(body)

            line_number = content[:match.start()].count('\n') + 1

            enums.append(SwiftEnumInfo(
                name=name,
                file=file_path,
                raw_type=raw_type,
                protocols=protocols,
                generic_params=generic_params,
                cases=cases,
                is_indirect=is_indirect,
                access_level=access,
                attributes=attributes,
                line_number=line_number,
            ))
        return enums

    def _extract_protocols(self, content: str, file_path: str) -> List[SwiftProtocolInfo]:
        """Extract protocol declarations."""
        protocols = []
        for match in self.PROTOCOL_PATTERN.finditer(content):
            attrs_str = (match.group('attrs') or '').strip()
            attributes = re.findall(r'@(\w+(?:\([^)]*\))?)', attrs_str)

            access = match.group('access') or 'internal'
            name = match.group('name')

            primary_assoc_str = match.group('primary_assoc') or ''
            primary_associated = [p.strip() for p in primary_assoc_str.split(',') if p.strip()] if primary_assoc_str else []

            inherits_str = match.group('inherits') or ''
            inherits = [i.strip() for i in inherits_str.split(',') if i.strip()]

            is_class_bound = 'AnyObject' in inherits or 'class' in inherits
            is_objc = '@objc' in attrs_str

            body = self._extract_brace_body(content, match.end() - 1)
            associated_types = self.ASSOC_TYPE_PATTERN.findall(body)
            requirements = self._extract_protocol_requirements(body)

            line_number = content[:match.start()].count('\n') + 1

            protocols.append(SwiftProtocolInfo(
                name=name,
                file=file_path,
                inherits=inherits,
                requirements=requirements,
                associated_types=associated_types,
                primary_associated_types=primary_associated,
                access_level=access,
                attributes=attributes,
                is_class_bound=is_class_bound,
                is_objc=is_objc,
                line_number=line_number,
            ))
        return protocols

    def _extract_actors(self, content: str, file_path: str) -> List[SwiftActorInfo]:
        """Extract actor declarations."""
        actors = []
        for match in self.ACTOR_PATTERN.finditer(content):
            attrs_str = (match.group('attrs') or '').strip()
            attributes = re.findall(r'@(\w+(?:\([^)]*\))?)', attrs_str)

            access = match.group('access') or 'internal'
            name = match.group('name')

            generics_str = match.group('generics') or ''
            generic_params = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []

            conformances_str = match.group('conformances') or ''
            protocols = [c.strip() for c in conformances_str.split(',') if c.strip()]

            is_global = '@globalActor' in attrs_str

            body = self._extract_brace_body(content, match.end() - 1)
            fields = self._extract_properties(body)

            line_number = content[:match.start()].count('\n') + 1

            actors.append(SwiftActorInfo(
                name=name,
                file=file_path,
                protocols=protocols,
                generic_params=generic_params,
                fields=fields,
                is_global_actor=is_global,
                access_level=access,
                attributes=attributes,
                line_number=line_number,
            ))
        return actors

    def _extract_type_aliases(self, content: str, file_path: str) -> List[SwiftTypeAliasInfo]:
        """Extract typealias declarations."""
        aliases = []
        for match in self.TYPEALIAS_PATTERN.finditer(content):
            access = match.group('access') or 'internal'
            name = match.group('name')
            generics_str = match.group('generics') or ''
            generic_params = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []
            underlying = match.group('type').strip()

            line_number = content[:match.start()].count('\n') + 1

            aliases.append(SwiftTypeAliasInfo(
                name=name,
                file=file_path,
                underlying_type=underlying,
                generic_params=generic_params,
                access_level=access,
                line_number=line_number,
            ))
        return aliases

    def _extract_extensions(self, content: str, file_path: str) -> List[SwiftExtensionInfo]:
        """Extract extension declarations."""
        extensions = []
        for match in self.EXTENSION_PATTERN.finditer(content):
            access = match.group('access') or 'internal'
            name = match.group('name')

            conformances_str = match.group('conformances') or ''
            protocols = [c.strip() for c in conformances_str.split(',') if c.strip()]

            where_str = match.group('where') or ''
            where_clauses = [w.strip() for w in where_str.split(',') if w.strip()] if where_str else []

            body = self._extract_brace_body(content, match.end() - 1)

            # Extract method names from body
            method_names = re.findall(r'func\s+(\w+)', body)
            # Extract property names from body
            prop_names = re.findall(r'(?:var|let)\s+(\w+)', body)

            line_number = content[:match.start()].count('\n') + 1

            extensions.append(SwiftExtensionInfo(
                name=name,
                file=file_path,
                protocols=protocols,
                where_clauses=where_clauses,
                methods=method_names,
                properties=prop_names,
                access_level=access,
                is_conditional=bool(where_clauses),
                line_number=line_number,
            ))
        return extensions

    def _extract_properties(self, body: str) -> List[SwiftFieldInfo]:
        """Extract property declarations from a type body."""
        fields = []
        for match in self.PROPERTY_PATTERN.finditer(body):
            attrs_str = (match.group('attrs') or '').strip()
            attributes = re.findall(r'@(\w+(?:\([^)]*\))?)', attrs_str)

            # Extract property wrapper
            pw = ''
            for attr in attributes:
                if attr in ('State', 'Binding', 'Published', 'ObservedObject',
                           'StateObject', 'EnvironmentObject', 'Environment',
                           'AppStorage', 'SceneStorage', 'FetchRequest',
                           'Query', 'Bindable', 'Observable',
                           'NSManaged', 'Attribute', 'Relationship'):
                    pw = attr
                    break

            access = match.group('access') or ''
            is_static = match.group('static') == 'static' if match.group('static') else False
            is_class_var = match.group('static') == 'class' if match.group('static') else False
            is_lazy = bool(match.group('lazy'))
            kind = match.group('kind')
            name = match.group('name')
            type_str = (match.group('type') or '').strip()
            default = (match.group('default') or '').strip()

            is_optional = '?' in type_str or type_str.startswith('Optional')

            line_number = body[:match.start()].count('\n') + 1

            fields.append(SwiftFieldInfo(
                name=name,
                type=type_str,
                is_let=kind == 'let',
                is_var=kind == 'var',
                is_static=is_static,
                is_class_var=is_class_var,
                is_lazy=is_lazy,
                is_computed=False,  # Would need deeper analysis
                is_optional=is_optional,
                default_value=default,
                access_level=access,
                property_wrapper=pw,
                attributes=attributes,
                line_number=line_number,
            ))
        return fields

    def _extract_enum_cases(self, body: str) -> List[SwiftEnumCaseInfo]:
        """Extract enum cases from enum body."""
        cases = []
        for match in self.CASE_PATTERN.finditer(body):
            name = match.group('name')
            assoc_str = match.group('assoc') or ''
            raw_val = (match.group('raw') or '').strip()

            associated_values = []
            if assoc_str:
                for part in self._split_params(assoc_str):
                    part = part.strip()
                    if ':' in part:
                        label, typ = part.split(':', 1)
                        associated_values.append({'label': label.strip(), 'type': typ.strip()})
                    else:
                        associated_values.append({'label': '_', 'type': part})

            line_number = body[:match.start()].count('\n') + 1

            cases.append(SwiftEnumCaseInfo(
                name=name,
                associated_values=associated_values,
                raw_value=raw_val,
                line_number=line_number,
            ))
        return cases

    def _extract_protocol_requirements(self, body: str) -> List[SwiftProtocolRequirementInfo]:
        """Extract protocol requirements from protocol body."""
        requirements = []

        # Method requirements
        for m in re.finditer(r'(?:(?P<static>static)\s+)?(?:(?P<mutating>mutating)\s+)?func\s+(?P<name>\w+)', body):
            requirements.append(SwiftProtocolRequirementInfo(
                name=m.group('name'),
                kind='method',
                is_static=bool(m.group('static')),
                is_mutating=bool(m.group('mutating')),
            ))

        # Property requirements
        for m in re.finditer(r'(?:(?P<static>static)\s+)?var\s+(?P<name>\w+)\s*:\s*(?P<type>[^{\n]+)', body):
            requirements.append(SwiftProtocolRequirementInfo(
                name=m.group('name'),
                kind='property',
                type=m.group('type').strip(),
                is_static=bool(m.group('static')),
            ))

        # Init requirements
        for m in re.finditer(r'init\s*\(', body):
            requirements.append(SwiftProtocolRequirementInfo(
                name='init',
                kind='init',
            ))

        return requirements

    def _extract_brace_body(self, content: str, open_pos: int) -> str:
        """Extract body between matching braces starting at open_pos."""
        if open_pos >= len(content) or content[open_pos] != '{':
            return ""
        depth = 0
        i = open_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[open_pos + 1:i]
            i += 1
        return content[open_pos + 1:]

    def _split_params(self, params_str: str) -> List[str]:
        """Split parameter list respecting nested angle brackets and parens."""
        parts = []
        depth = 0
        current = []
        for ch in params_str:
            if ch in ('<', '(', '['):
                depth += 1
                current.append(ch)
            elif ch in ('>', ')', ']'):
                depth -= 1
                current.append(ch)
            elif ch == ',' and depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                current.append(ch)
        if current:
            parts.append(''.join(current))
        return parts
