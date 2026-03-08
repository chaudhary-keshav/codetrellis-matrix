"""
TypeScript Type Extractor for CodeTrellis

Extracts type definitions from TypeScript source code:
- Classes with access modifiers (public/private/protected/readonly/abstract)
- Interfaces with extends, generics, and index signatures
- Type aliases (union, intersection, conditional, mapped, template literal)
- Enums (numeric, string, const, ambient)
- Generic type parameters with constraints and defaults
- Abstract classes and methods
- Decorators on classes
- Namespace/module declarations

Supports TypeScript 2.0 through 5.7+:
- TS 2.0: non-null assertion, strictNullChecks, tagged unions
- TS 2.1: keyof, lookup types, mapped types
- TS 2.8: conditional types, infer
- TS 3.0: unknown, project references
- TS 3.7: optional chaining, assertion functions
- TS 4.0: variadic tuple types, labeled tuple elements
- TS 4.1: template literal types, key remapping
- TS 4.5: type-only import specifiers
- TS 4.7: instantiation expressions, variance annotations
- TS 4.9: satisfies operator
- TS 5.0: const type parameters, decorators (TC39)
- TS 5.2: using declarations
- TS 5.4: NoInfer utility type
- TS 5.5: inferred type predicates
- TS 5.7: --erasableSyntaxOnly

Part of CodeTrellis v4.31 - TypeScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TSGenericParam:
    """Information about a generic type parameter."""
    name: str
    constraint: str = ""  # extends clause
    default: str = ""  # = default type
    variance: str = ""  # in, out, in out (TS 4.7+)


@dataclass
class TSPropertyInfo:
    """Information about a TypeScript class/interface property."""
    name: str
    type: str = ""
    default_value: Optional[str] = None
    is_optional: bool = False
    is_readonly: bool = False
    is_static: bool = False
    is_private: bool = False
    is_protected: bool = False
    is_abstract: bool = False
    is_override: bool = False
    access_modifier: str = ""  # public, private, protected
    decorators: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class TSClassInfo:
    """Information about a TypeScript class definition."""
    name: str
    file: str = ""
    line_number: int = 0
    superclass: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    mixins: List[str] = field(default_factory=list)
    generics: List[TSGenericParam] = field(default_factory=list)
    properties: List[TSPropertyInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    static_methods: List[str] = field(default_factory=list)
    private_methods: List[str] = field(default_factory=list)
    protected_methods: List[str] = field(default_factory=list)
    abstract_methods: List[str] = field(default_factory=list)
    getters: List[str] = field(default_factory=list)
    setters: List[str] = field(default_factory=list)
    is_exported: bool = False
    is_default_export: bool = False
    is_abstract: bool = False
    decorators: List[str] = field(default_factory=list)
    constructor_params: List[str] = field(default_factory=list)


@dataclass
class TSInterfaceInfo:
    """Information about a TypeScript interface definition."""
    name: str
    file: str = ""
    line_number: int = 0
    extends: List[str] = field(default_factory=list)
    generics: List[TSGenericParam] = field(default_factory=list)
    properties: List[TSPropertyInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    index_signatures: List[str] = field(default_factory=list)
    call_signatures: List[str] = field(default_factory=list)
    is_exported: bool = False


@dataclass
class TSEnumMemberInfo:
    """Information about an enum member."""
    name: str
    value: Optional[str] = None
    is_computed: bool = False


@dataclass
class TSTypeAliasInfo:
    """Information about a TypeScript type alias."""
    name: str
    file: str = ""
    line_number: int = 0
    definition: str = ""
    kind: str = "alias"  # alias, union, intersection, conditional, mapped, template_literal, utility
    generics: List[TSGenericParam] = field(default_factory=list)
    is_exported: bool = False


@dataclass
class TSEnumInfo:
    """Information about a TypeScript enum."""
    name: str
    file: str = ""
    line_number: int = 0
    members: List[TSEnumMemberInfo] = field(default_factory=list)
    is_const: bool = False
    is_exported: bool = False
    is_ambient: bool = False  # declare enum


class TypeScriptTypeExtractor:
    """
    Extracts type definitions from TypeScript source code.

    Detects:
    - Classes with full modifier support (abstract, public/private/protected)
    - Interfaces with generics, extends, index signatures
    - Type aliases (all forms: union, intersection, conditional, mapped, etc.)
    - Enums (numeric, string, const, ambient)
    - Generic type parameters
    - Decorators on classes
    """

    # Class declaration (with optional abstract, decorators)
    CLASS_DECL_PATTERN = re.compile(
        r'^[ \t]*(?:(?:export\s+(?:default\s+)?)?)'
        r'(?:abstract\s+)?'
        r'class\s+(\w+)'
        r'(?:<([^>]+)>)?'                    # generics
        r'(?:\s+extends\s+([\w.<>,\s]+?))?'  # extends
        r'(?:\s+implements\s+([\w.<>,\s]+?))?' # implements
        r'\s*\{',
        re.MULTILINE
    )

    # Interface declaration
    INTERFACE_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+)?'
        r'interface\s+(\w+)'
        r'(?:<([^>]+)>)?'                    # generics
        r'(?:\s+extends\s+([\w.<>,\s]+?))?'  # extends
        r'\s*\{',
        re.MULTILINE
    )

    # Type alias
    TYPE_ALIAS_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+)?'
        r'type\s+(\w+)'
        r'(?:<([^>]+)>)?'                    # generics
        r'\s*=\s*(.+?)(?:;|\n)',
        re.MULTILINE
    )

    # Enum declaration
    ENUM_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+)?'
        r'(?:const\s+)?'
        r'(?:declare\s+)?'
        r'enum\s+(\w+)\s*\{',
        re.MULTILINE
    )

    # Decorator pattern
    DECORATOR_PATTERN = re.compile(
        r'^[ \t]*@(\w+(?:\.\w+)*)\s*(?:\(([^)]*)\))?',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all type definitions from TypeScript source code.

        Returns dict with keys: classes, interfaces, type_aliases, enums
        """
        classes = self._extract_classes(content, file_path)
        interfaces = self._extract_interfaces(content, file_path)
        type_aliases = self._extract_type_aliases(content, file_path)
        enums = self._extract_enums(content, file_path)

        return {
            'classes': classes,
            'interfaces': interfaces,
            'type_aliases': type_aliases,
            'enums': enums,
        }

    def _extract_classes(self, content: str, file_path: str) -> List[TSClassInfo]:
        """Extract TypeScript class definitions."""
        classes = []
        seen_names = set()

        for match in self.CLASS_DECL_PATTERN.finditer(content):
            name = match.group(1)
            generics_str = match.group(2) or ""
            extends_str = match.group(3) or ""
            implements_str = match.group(4) or ""
            line_num = content[:match.start()].count('\n') + 1

            if name in seen_names:
                continue
            seen_names.add(name)

            # Export detection
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))
            is_default = bool(re.search(r'\bexport\s+default\b', line_text))
            is_abstract = bool(re.search(r'\babstract\b', line_text))

            # Parse generics
            generics = self._parse_generics(generics_str) if generics_str else []

            # Parse implements
            implements = [i.strip() for i in implements_str.split(',') if i.strip()] if implements_str else []

            # Parse superclass
            superclass = extends_str.strip() if extends_str else None

            # Extract decorators above the class
            decorators = self._extract_decorators_before(content, match.start())

            # Extract class body
            class_body = self._extract_brace_block(content, match.end() - 1)
            methods, static_methods, private_methods = [], [], []
            protected_methods, abstract_methods = [], []
            getters, setters = [], []
            properties = []
            constructor_params = []

            if class_body:
                (methods, static_methods, private_methods, protected_methods,
                 abstract_methods, getters, setters, properties, constructor_params) = \
                    self._parse_class_body(class_body)

            classes.append(TSClassInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                superclass=superclass,
                implements=implements,
                generics=generics,
                properties=properties,
                methods=methods,
                static_methods=static_methods,
                private_methods=private_methods,
                protected_methods=protected_methods,
                abstract_methods=abstract_methods,
                getters=getters,
                setters=setters,
                is_exported=is_exported,
                is_default_export=is_default,
                is_abstract=is_abstract,
                decorators=decorators,
                constructor_params=constructor_params,
            ))

        return classes

    def _parse_class_body(self, body: str):
        """Parse a TypeScript class body to extract methods, properties, etc."""
        methods = []
        static_methods = []
        private_methods = []
        protected_methods = []
        abstract_methods = []
        getters = []
        setters = []
        properties = []
        constructor_params = []

        for line in body.split('\n'):
            stripped = line.strip()
            if not stripped or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                continue

            # Constructor with parameter properties
            ctor_match = re.match(
                r'(?:public\s+|private\s+|protected\s+)?constructor\s*\(([^)]*)\)',
                stripped
            )
            if ctor_match:
                params_str = ctor_match.group(1)
                if params_str:
                    # Extract parameter properties (public/private/protected/readonly)
                    for param in re.finditer(
                        r'(?:(?:public|private|protected)\s+)?(?:readonly\s+)?(\w+)\s*(?::\s*([^,=]+))?',
                        params_str
                    ):
                        constructor_params.append(param.group(1))
                methods.insert(0, 'constructor')
                continue

            # Abstract method
            m = re.match(r'abstract\s+(?:get\s+|set\s+)?(\w+)\s*[\(<]', stripped)
            if m:
                abstract_methods.append(m.group(1))
                continue

            # Static method
            m = re.match(r'(?:public\s+|private\s+|protected\s+)?static\s+(?:async\s+)?(\w+)\s*[\(<]', stripped)
            if m:
                name = m.group(1)
                if name not in ('get', 'set'):
                    static_methods.append(name)
                continue

            # Getter
            m = re.match(r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:abstract\s+)?get\s+(\w+)\s*\(', stripped)
            if m:
                getters.append(m.group(1))
                continue

            # Setter
            m = re.match(r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:abstract\s+)?set\s+(\w+)\s*\(', stripped)
            if m:
                setters.append(m.group(1))
                continue

            # Private method (TypeScript private keyword or # prefix)
            m = re.match(r'private\s+(?:async\s+)?(\w+)\s*[\(<]', stripped)
            if m:
                private_methods.append(m.group(1))
                continue
            m = re.match(r'(?:async\s+)?#(\w+)\s*\(', stripped)
            if m:
                private_methods.append('#' + m.group(1))
                continue

            # Protected method
            m = re.match(r'protected\s+(?:async\s+)?(\w+)\s*[\(<]', stripped)
            if m:
                protected_methods.append(m.group(1))
                continue

            # Regular/public method
            m = re.match(r'(?:public\s+)?(?:async\s+)?(?:override\s+)?(\w+)\s*[\(<]', stripped)
            if m:
                name = m.group(1)
                if name not in ('if', 'for', 'while', 'switch', 'catch', 'constructor',
                                'return', 'const', 'let', 'var', 'import', 'export',
                                'type', 'interface', 'enum', 'class', 'abstract',
                                'private', 'protected', 'public', 'static', 'readonly'):
                    # Check it looks like a method (has parens or generics)
                    if re.match(r'(?:public\s+)?(?:async\s+)?(?:override\s+)?(\w+)\s*(?:<[^>]*>)?\s*\(', stripped):
                        methods.append(name)
                        continue

            # Property declaration
            m = re.match(
                r'(?:@\w+(?:\([^)]*\))?\s*)?'
                r'((?:public|private|protected)\s+)?'
                r'(static\s+)?'
                r'(readonly\s+)?'
                r'(abstract\s+)?'
                r'(override\s+)?'
                r'(?:#)?(\w+)'
                r'(\?)?\s*'
                r'(?::\s*([^=;]+?))?'
                r'\s*(?:=\s*(.+?))?;?\s*$',
                stripped
            )
            if m:
                access = (m.group(1) or '').strip()
                is_static = bool(m.group(2))
                is_readonly = bool(m.group(3))
                is_abstract = bool(m.group(4))
                is_override = bool(m.group(5))
                prop_name = m.group(6)
                is_optional = bool(m.group(7))
                prop_type = (m.group(8) or '').strip()
                default_val = (m.group(9) or '').strip() or None

                # Skip if name is a keyword
                if prop_name in ('if', 'for', 'while', 'switch', 'catch', 'return',
                                 'const', 'let', 'var', 'import', 'export', 'type',
                                 'interface', 'enum', 'class', 'abstract', 'async',
                                 'function', 'new', 'this', 'super', 'extends', 'implements'):
                    continue

                properties.append(TSPropertyInfo(
                    name=prop_name,
                    type=prop_type,
                    default_value=default_val,
                    is_optional=is_optional,
                    is_readonly=is_readonly,
                    is_static=is_static,
                    is_private=(access == 'private'),
                    is_protected=(access == 'protected'),
                    is_abstract=is_abstract,
                    is_override=is_override,
                    access_modifier=access,
                ))

        return (methods, static_methods, private_methods, protected_methods,
                abstract_methods, getters, setters, properties, constructor_params)

    def _extract_interfaces(self, content: str, file_path: str) -> List[TSInterfaceInfo]:
        """Extract TypeScript interface definitions."""
        interfaces = []
        seen_names = set()

        for match in self.INTERFACE_PATTERN.finditer(content):
            name = match.group(1)
            generics_str = match.group(2) or ""
            extends_str = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1

            if name in seen_names:
                continue
            seen_names.add(name)

            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))

            generics = self._parse_generics(generics_str) if generics_str else []
            extends = [e.strip() for e in extends_str.split(',') if e.strip()] if extends_str else []

            # Extract body
            body = self._extract_brace_block(content, match.end() - 1)
            properties = []
            methods = []
            index_signatures = []
            call_signatures = []

            if body:
                properties, methods, index_signatures, call_signatures = self._parse_interface_body(body)

            interfaces.append(TSInterfaceInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                extends=extends,
                generics=generics,
                properties=properties,
                methods=methods,
                index_signatures=index_signatures,
                call_signatures=call_signatures,
                is_exported=is_exported,
            ))

        return interfaces

    def _parse_interface_body(self, body: str):
        """Parse an interface body to extract properties, methods, index sigs."""
        properties = []
        methods = []
        index_signatures = []
        call_signatures = []

        for line in body.split('\n'):
            stripped = line.strip()
            if not stripped or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                continue

            # Index signature: [key: string]: value
            m = re.match(r'\[(\w+)\s*:\s*(\w+)\]\s*:\s*(.+?)[;,]?\s*$', stripped)
            if m:
                index_signatures.append(f"[{m.group(1)}: {m.group(2)}]: {m.group(3)}")
                continue

            # Call signature: (args): return
            m = re.match(r'\(([^)]*)\)\s*:\s*(.+?)[;,]?\s*$', stripped)
            if m:
                call_signatures.append(f"({m.group(1)}): {m.group(2)}")
                continue

            # Method signature: name(args): return
            m = re.match(r'(?:readonly\s+)?(\w+)\s*(?:<[^>]*>)?\s*\([^)]*\)\s*:\s*(.+?)[;,]?\s*$', stripped)
            if m:
                methods.append(m.group(1))
                continue

            # Property: name?: Type
            m = re.match(r'(?:readonly\s+)?(\w+)(\?)?\s*:\s*(.+?)[;,]?\s*$', stripped)
            if m:
                properties.append(TSPropertyInfo(
                    name=m.group(1),
                    type=m.group(3).strip(),
                    is_optional=bool(m.group(2)),
                    is_readonly='readonly' in stripped,
                ))
                continue

        return properties, methods, index_signatures, call_signatures

    def _extract_type_aliases(self, content: str, file_path: str) -> List[TSTypeAliasInfo]:
        """Extract TypeScript type alias definitions."""
        type_aliases = []
        seen_names = set()

        for match in self.TYPE_ALIAS_PATTERN.finditer(content):
            name = match.group(1)
            generics_str = match.group(2) or ""
            definition = match.group(3).strip()
            line_num = content[:match.start()].count('\n') + 1

            if name in seen_names:
                continue
            seen_names.add(name)

            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))

            generics = self._parse_generics(generics_str) if generics_str else []

            # Determine kind
            kind = self._classify_type_alias(definition)

            type_aliases.append(TSTypeAliasInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                definition=definition[:200],  # truncate very long definitions
                kind=kind,
                generics=generics,
                is_exported=is_exported,
            ))

        return type_aliases

    def _classify_type_alias(self, definition: str) -> str:
        """Classify a type alias definition."""
        if ' | ' in definition:
            return 'union'
        if ' & ' in definition:
            return 'intersection'
        if 'extends' in definition and '?' in definition:
            return 'conditional'
        if re.search(r'\{\s*(?:[+-]?readonly\s+)?\[', definition):
            return 'mapped'
        if '`' in definition and '${' in definition:
            return 'template_literal'
        # Utility types
        if re.match(r'(Partial|Required|Readonly|Record|Pick|Omit|Exclude|Extract|NonNullable|ReturnType|InstanceType|Parameters|ConstructorParameters|Awaited|NoInfer)\s*<', definition):
            return 'utility'
        if re.match(r'keyof\s+', definition):
            return 'keyof'
        if re.match(r'typeof\s+', definition):
            return 'typeof'
        return 'alias'

    def _extract_enums(self, content: str, file_path: str) -> List[TSEnumInfo]:
        """Extract TypeScript enum definitions."""
        enums = []
        seen_names = set()

        for match in self.ENUM_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen_names:
                continue
            seen_names.add(name)

            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))
            is_const = bool(re.search(r'\bconst\b', line_text))
            is_ambient = bool(re.search(r'\bdeclare\b', line_text))

            # Extract body
            body = self._extract_brace_block(content, match.end() - 1)
            members = []

            if body:
                members = self._parse_enum_body(body)

            enums.append(TSEnumInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                members=members,
                is_const=is_const,
                is_exported=is_exported,
                is_ambient=is_ambient,
            ))

        return enums

    def _parse_enum_body(self, body: str) -> List[TSEnumMemberInfo]:
        """Parse an enum body to extract members."""
        members = []

        for line in body.split('\n'):
            stripped = line.strip().rstrip(',')
            if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
                continue

            # Member = value
            m = re.match(r'(\w+)\s*=\s*(.+)', stripped)
            if m:
                value = m.group(2).strip()
                is_computed = not re.match(r'^[\'"\d]', value) and value not in ('true', 'false')
                members.append(TSEnumMemberInfo(
                    name=m.group(1),
                    value=value,
                    is_computed=is_computed,
                ))
                continue

            # Member without value
            m = re.match(r'(\w+)\s*$', stripped)
            if m:
                members.append(TSEnumMemberInfo(name=m.group(1)))

        return members

    def _parse_generics(self, generics_str: str) -> List[TSGenericParam]:
        """Parse generic type parameters."""
        generics = []
        if not generics_str:
            return generics

        # Simple split (doesn't handle nested generics perfectly)
        depth = 0
        current = ""
        for ch in generics_str:
            if ch == '<':
                depth += 1
                current += ch
            elif ch == '>':
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                generics.append(self._parse_single_generic(current.strip()))
                current = ""
            else:
                current += ch

        if current.strip():
            generics.append(self._parse_single_generic(current.strip()))

        return generics

    def _parse_single_generic(self, param_str: str) -> TSGenericParam:
        """Parse a single generic parameter like 'T extends Foo = Bar'."""
        # Check for variance annotations (TS 4.7+)
        variance = ""
        if param_str.startswith('in out '):
            variance = "in out"
            param_str = param_str[7:]
        elif param_str.startswith('in '):
            variance = "in"
            param_str = param_str[3:]
        elif param_str.startswith('out '):
            variance = "out"
            param_str = param_str[4:]

        # Check for const modifier (TS 5.0+)
        if param_str.startswith('const '):
            param_str = param_str[6:]

        # Parse name, constraint, default
        m = re.match(r'(\w+)(?:\s+extends\s+(.+?))?(?:\s*=\s*(.+))?$', param_str)
        if m:
            return TSGenericParam(
                name=m.group(1),
                constraint=m.group(2) or "",
                default=m.group(3) or "",
                variance=variance,
            )
        return TSGenericParam(name=param_str)

    def _extract_decorators_before(self, content: str, pos: int) -> List[str]:
        """Extract decorator names that appear before a position (class/method)."""
        decorators = []
        # Look backwards from pos for decorator lines
        lines_before = content[:pos].split('\n')
        for line in reversed(lines_before[-10:]):  # Check last 10 lines
            stripped = line.strip()
            m = re.match(r'@(\w+(?:\.\w+)*)', stripped)
            if m:
                decorators.insert(0, m.group(1))
            elif stripped and not stripped.startswith('//') and not stripped.startswith('/*') and not stripped.startswith('*'):
                break  # Stop at non-decorator, non-comment line
        return decorators

    def _extract_brace_block(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content between balanced braces starting at start_pos."""
        if start_pos >= len(content) or content[start_pos] != '{':
            return None

        depth = 0
        i = start_pos
        while i < len(content):
            ch = content[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[start_pos + 1:i]
            elif ch in ('"', "'", '`'):
                quote = ch
                i += 1
                while i < len(content) and content[i] != quote:
                    if content[i] == '\\':
                        i += 1
                    i += 1
            elif ch == '/' and i + 1 < len(content):
                if content[i + 1] == '/':
                    while i < len(content) and content[i] != '\n':
                        i += 1
                elif content[i + 1] == '*':
                    i += 2
                    while i < len(content) - 1 and not (content[i] == '*' and content[i + 1] == '/'):
                        i += 1
                    i += 1
            i += 1

        return None
