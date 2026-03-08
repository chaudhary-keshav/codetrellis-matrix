"""
Dart Type Extractor for CodeTrellis

Extracts type definitions from Dart source code:
- Classes (abstract, sealed, base, interface, final, mixin classes)
- Mixins (with on-clause constraints)
- Enums (enhanced enums with members, Dart 2.17+)
- Extensions (extension methods, extension types Dart 3.3+)
- Typedefs (function typedefs, generic typedefs)
- Abstract interfaces

Supports Dart 2.0 through Dart 3.x+ features including:
- Null safety (Dart 2.12+)
- Class modifiers: sealed, base, interface, final, mixin (Dart 3.0+)
- Extension types (Dart 3.3+)
- Records (Dart 3.0+)
- Patterns and pattern matching (Dart 3.0+)

Part of CodeTrellis v4.27 - Dart Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DartFieldInfo:
    """Information about a class/mixin field."""
    name: str
    type: str = ""
    is_final: bool = False
    is_late: bool = False
    is_static: bool = False
    is_const: bool = False
    is_nullable: bool = False
    is_required: bool = False
    default_value: str = ""
    access_level: str = "public"  # public or private (starts with _)
    annotations: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class DartClassInfo:
    """Information about a Dart class."""
    name: str
    file: str = ""
    superclass: str = ""
    interfaces: List[str] = field(default_factory=list)
    mixins: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    fields: List[DartFieldInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    is_abstract: bool = False
    is_sealed: bool = False
    is_base: bool = False
    is_interface: bool = False
    is_final: bool = False
    is_mixin_class: bool = False
    annotations: List[str] = field(default_factory=list)
    nested_types: List[str] = field(default_factory=list)
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class DartMixinInfo:
    """Information about a Dart mixin."""
    name: str
    file: str = ""
    on_types: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    fields: List[DartFieldInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class DartEnumCaseInfo:
    """Information about an enum value."""
    name: str
    arguments: List[str] = field(default_factory=list)
    constructor_args: str = ""
    line_number: int = 0


@dataclass
class DartEnumInfo:
    """Information about a Dart enum (enhanced enum, Dart 2.17+)."""
    name: str
    file: str = ""
    interfaces: List[str] = field(default_factory=list)
    mixins: List[str] = field(default_factory=list)
    cases: List[DartEnumCaseInfo] = field(default_factory=list)
    values: List['DartEnumCaseInfo'] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    has_members: bool = False
    is_enhanced: bool = False
    annotations: List[str] = field(default_factory=list)
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class DartExtensionInfo:
    """Information about a Dart extension (or extension type)."""
    name: str
    file: str = ""
    on_type: str = ""
    is_extension_type: bool = False
    representation_type: str = ""  # For extension types
    interfaces: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class DartTypedefInfo:
    """Information about a typedef."""
    name: str
    file: str = ""
    target_type: str = ""
    is_function_typedef: bool = False
    generic_params: List[str] = field(default_factory=list)
    doc_comment: str = ""
    line_number: int = 0


class DartTypeExtractor:
    """
    Extracts Dart type definitions using regex-based parsing.

    Supports all Dart type kinds:
    - class (abstract, sealed, base, interface, final, mixin class)
    - mixin (with on-clause)
    - enum (enhanced enums with members)
    - extension / extension type
    - typedef
    """

    # Class declaration pattern (handles Dart 3.0 modifiers)
    CLASS_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<sealed>sealed)\s+)?'
        r'(?:(?P<base>base)\s+)?'
        r'(?:(?P<interface>interface)\s+)?'
        r'(?:(?P<final>final)\s+)?'
        r'(?:(?P<abstract>abstract)\s+)?'
        r'(?:(?P<mixin_class>mixin)\s+)?'
        r'class\s+(?P<name>\w+)'
        r'(?:\s*<(?P<generics>[^>]+)>)?'
        r'(?:\s+extends\s+(?P<extends>\w+(?:<[^>]+>)?))?'
        r'(?:\s+with\s+(?P<with>[^{]+?))?'
        r'(?:\s+implements\s+(?P<implements>[^{]+?))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Mixin declaration pattern
    MIXIN_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<base>base)\s+)?'
        r'mixin\s+(?P<name>\w+)'
        r'(?:\s*<(?P<generics>[^>]+)>)?'
        r'(?:\s+on\s+(?P<on>[^{]+?))?'
        r'(?:\s+implements\s+(?P<implements>[^{]+?))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Enum declaration pattern (enhanced enums)
    ENUM_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'enum\s+(?P<name>\w+)'
        r'(?:\s+with\s+(?P<with>[^{]+?))?'
        r'(?:\s+implements\s+(?P<implements>[^{]+?))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Extension declaration pattern
    EXTENSION_PATTERN = re.compile(
        r'^\s*extension\s+(?P<name>\w+)?\s+on\s+(?P<on_type>[^{]+?)\s*\{',
        re.MULTILINE
    )

    # Extension type pattern (Dart 3.3+)
    EXTENSION_TYPE_PATTERN = re.compile(
        r'^\s*extension\s+type\s+(?:const\s+)?(?P<name>\w+)'
        r'(?:\s*<(?P<generics>[^>]+)>)?'
        r'\s*\((?P<rep_type>[^)]+)\)'
        r'(?:\s+implements\s+(?P<implements>[^{]+?))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Typedef pattern
    TYPEDEF_PATTERN = re.compile(
        r'^\s*typedef\s+(?P<name>\w+)'
        r'(?:\s*<(?P<generics>[^>]+)>)?'
        r'\s*=\s*(?P<type>[^;]+);',
        re.MULTILINE
    )

    # Legacy typedef (function type)
    TYPEDEF_FUNC_PATTERN = re.compile(
        r'^\s*typedef\s+(?P<return_type>\w+(?:<[^>]+>)?)\s+'
        r'(?P<name>\w+)'
        r'(?:\s*<(?P<generics>[^>]+)>)?'
        r'\s*\((?P<params>[^)]*)\)\s*;',
        re.MULTILINE
    )

    # Field pattern (instance variables)
    FIELD_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<static>static)\s+)?'
        r'(?:(?P<late>late)\s+)?'
        r'(?:(?P<final>final)\s+)?'
        r'(?:(?P<const>const)\s+)?'
        r'(?:(?P<type>\w+(?:<[^>]+>)?(?:\?)?)\s+)?'
        r'(?P<name>_?\w+)'
        r'(?:\s*=\s*(?P<default>[^;]+))?;',
        re.MULTILINE
    )

    # Enum value pattern
    ENUM_VALUE_PATTERN = re.compile(
        r'^\s*(?P<name>\w+)(?:\((?P<args>[^)]*)\))?\s*[,;]',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all type definitions from Dart source code.

        Returns:
            Dict with 'classes', 'mixins', 'enums', 'extensions',
            'extension_types', 'typedefs' lists.
        """
        result: Dict[str, Any] = {
            'classes': [],
            'mixins': [],
            'enums': [],
            'extensions': [],
            'extension_types': [],
            'typedefs': [],
        }

        result['classes'] = self._extract_classes(content, file_path)
        result['mixins'] = self._extract_mixins(content, file_path)
        result['enums'] = self._extract_enums(content, file_path)
        result['extensions'] = self._extract_extensions(content, file_path)
        result['extension_types'] = self._extract_extension_types(content, file_path)
        result['typedefs'] = self._extract_typedefs(content, file_path)

        return result

    def _extract_classes(self, content: str, file_path: str) -> List[DartClassInfo]:
        """Extract class declarations."""
        classes = []
        for match in self.CLASS_PATTERN.finditer(content):
            # Skip if this is actually a mixin class and already matched as mixin
            name = match.group('name')

            generics = []
            if match.group('generics'):
                generics = [g.strip() for g in match.group('generics').split(',')]

            interfaces = []
            if match.group('implements'):
                interfaces = [i.strip() for i in match.group('implements').split(',')]

            mixins = []
            if match.group('with'):
                mixins = [m.strip() for m in match.group('with').split(',')]

            annotations = []
            if match.group('annotations'):
                annotations = re.findall(r'@(\w+)', match.group('annotations'))

            # Extract fields from class body
            class_start = match.end()
            class_body = self._extract_body(content, class_start - 1)
            fields = self._extract_fields(class_body) if class_body else []

            cls = DartClassInfo(
                name=name,
                file=file_path,
                superclass=match.group('extends') or "",
                interfaces=interfaces,
                mixins=mixins,
                generic_params=generics,
                fields=fields,
                is_abstract=bool(match.group('abstract')),
                is_sealed=bool(match.group('sealed')),
                is_base=bool(match.group('base')),
                is_interface=bool(match.group('interface')),
                is_final=bool(match.group('final')),
                is_mixin_class=bool(match.group('mixin_class')),
                annotations=annotations,
                line_number=content[:match.start()].count('\n') + 1,
            )
            classes.append(cls)

        return classes

    def _extract_mixins(self, content: str, file_path: str) -> List[DartMixinInfo]:
        """Extract mixin declarations."""
        mixins = []
        for match in self.MIXIN_PATTERN.finditer(content):
            # Check if this is a "mixin class" — already handled in _extract_classes
            pre_text = content[max(0, match.start() - 20):match.start()]
            if 'class' in content[match.end():match.end() + 5]:
                continue

            name = match.group('name')
            generics = []
            if match.group('generics'):
                generics = [g.strip() for g in match.group('generics').split(',')]

            on_types = []
            if match.group('on'):
                on_types = [o.strip() for o in match.group('on').split(',')]

            interfaces = []
            if match.group('implements'):
                interfaces = [i.strip() for i in match.group('implements').split(',')]

            annotations = []
            if match.group('annotations'):
                annotations = re.findall(r'@(\w+)', match.group('annotations'))

            mixin_start = match.end()
            mixin_body = self._extract_body(content, mixin_start - 1)
            fields = self._extract_fields(mixin_body) if mixin_body else []

            m = DartMixinInfo(
                name=name,
                file=file_path,
                on_types=on_types,
                interfaces=interfaces,
                generic_params=generics,
                fields=fields,
                annotations=annotations,
                line_number=content[:match.start()].count('\n') + 1,
            )
            mixins.append(m)

        return mixins

    def _extract_enums(self, content: str, file_path: str) -> List[DartEnumInfo]:
        """Extract enum declarations (including enhanced enums)."""
        enums = []
        for match in self.ENUM_PATTERN.finditer(content):
            name = match.group('name')

            interfaces = []
            if match.group('implements'):
                interfaces = [i.strip() for i in match.group('implements').split(',')]

            with_mixins = []
            if match.group('with'):
                with_mixins = [m.strip() for m in match.group('with').split(',')]

            annotations = []
            if match.group('annotations'):
                annotations = re.findall(r'@(\w+)', match.group('annotations'))

            # Extract enum body to get values
            enum_start = match.end()
            enum_body = self._extract_body(content, enum_start - 1)
            cases = self._extract_enum_values(enum_body) if enum_body else []

            # Check if it has members (methods/fields beyond values)
            has_members = ';' in (enum_body or '') and any(
                kw in (enum_body or '') for kw in ['void ', 'String ', 'int ', 'double ',
                                                     'bool ', 'factory ', 'const ', '@override']
            )

            e = DartEnumInfo(
                name=name,
                file=file_path,
                interfaces=interfaces,
                mixins=with_mixins,
                cases=cases,
                has_members=has_members,
                annotations=annotations,
                line_number=content[:match.start()].count('\n') + 1,
            )
            enums.append(e)

        return enums

    def _extract_extensions(self, content: str, file_path: str) -> List[DartExtensionInfo]:
        """Extract extension declarations."""
        extensions = []
        for match in self.EXTENSION_PATTERN.finditer(content):
            name = match.group('name') or ""
            on_type = match.group('on_type').strip()

            ext_start = match.end()
            ext_body = self._extract_body(content, ext_start - 1)
            methods = self._extract_method_names(ext_body) if ext_body else []

            ext = DartExtensionInfo(
                name=name,
                file=file_path,
                on_type=on_type,
                methods=methods,
                line_number=content[:match.start()].count('\n') + 1,
            )
            extensions.append(ext)

        return extensions

    def _extract_extension_types(self, content: str, file_path: str) -> List[DartExtensionInfo]:
        """Extract extension type declarations (Dart 3.3+)."""
        ext_types = []
        for match in self.EXTENSION_TYPE_PATTERN.finditer(content):
            name = match.group('name')
            rep_type = match.group('rep_type').strip() if match.group('rep_type') else ""

            interfaces = []
            if match.group('implements'):
                interfaces = [i.strip() for i in match.group('implements').split(',')]

            ext_start = match.end()
            ext_body = self._extract_body(content, ext_start - 1)
            methods = self._extract_method_names(ext_body) if ext_body else []

            et = DartExtensionInfo(
                name=name,
                file=file_path,
                is_extension_type=True,
                representation_type=rep_type,
                interfaces=interfaces,
                methods=methods,
                line_number=content[:match.start()].count('\n') + 1,
            )
            ext_types.append(et)

        return ext_types

    def _extract_typedefs(self, content: str, file_path: str) -> List[DartTypedefInfo]:
        """Extract typedef declarations."""
        typedefs = []

        # Modern typedef: typedef Name = Type;
        for match in self.TYPEDEF_PATTERN.finditer(content):
            name = match.group('name')
            generics = []
            if match.group('generics'):
                generics = [g.strip() for g in match.group('generics').split(',')]

            td = DartTypedefInfo(
                name=name,
                file=file_path,
                target_type=match.group('type').strip(),
                generic_params=generics,
                line_number=content[:match.start()].count('\n') + 1,
            )
            typedefs.append(td)

        # Legacy function typedef
        for match in self.TYPEDEF_FUNC_PATTERN.finditer(content):
            name = match.group('name')
            # Skip if already found as modern typedef
            if any(t.name == name for t in typedefs):
                continue

            generics = []
            if match.group('generics'):
                generics = [g.strip() for g in match.group('generics').split(',')]

            ret_type = match.group('return_type')
            params = match.group('params')
            target = f"{ret_type} Function({params})"

            td = DartTypedefInfo(
                name=name,
                file=file_path,
                target_type=target,
                generic_params=generics,
                line_number=content[:match.start()].count('\n') + 1,
            )
            typedefs.append(td)

        return typedefs

    def _extract_body(self, content: str, brace_pos: int) -> Optional[str]:
        """Extract the body between balanced braces starting from brace_pos."""
        if brace_pos >= len(content) or content[brace_pos] != '{':
            return None

        depth = 0
        i = brace_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[brace_pos + 1:i]
            i += 1
        return None

    def _extract_fields(self, body: str) -> List[DartFieldInfo]:
        """Extract field declarations from a class/mixin body."""
        fields = []
        if not body:
            return fields

        for line in body.split('\n'):
            line_stripped = line.strip()
            # Skip empty lines, comments, methods, constructors
            if not line_stripped or line_stripped.startswith('//') or line_stripped.startswith('/*'):
                continue
            if line_stripped.startswith('void ') or line_stripped.startswith('Future<'):
                continue
            if '(' in line_stripped and ')' in line_stripped and '{' in line_stripped:
                continue
            if line_stripped.startswith(('factory ', 'static ', '@')):
                if line_stripped.startswith('static '):
                    # Static field, continue to parse
                    pass
                else:
                    continue

            match = self.FIELD_PATTERN.match(line_stripped)
            if match and match.group('name'):
                name = match.group('name')
                # Skip constructor or method names
                if name in ('super', 'this', 'return', 'if', 'else', 'for', 'while', 'switch', 'try', 'catch'):
                    continue

                field_type = match.group('type') or ""
                is_nullable = field_type.endswith('?') if field_type else False

                f = DartFieldInfo(
                    name=name,
                    type=field_type,
                    is_final=bool(match.group('final')),
                    is_late=bool(match.group('late')),
                    is_static=bool(match.group('static')),
                    is_const=bool(match.group('const')),
                    is_nullable=is_nullable,
                    default_value=match.group('default') or "",
                    access_level="private" if name.startswith('_') else "public",
                    line_number=0,
                )
                fields.append(f)

        return fields[:30]  # Limit

    def _extract_enum_values(self, body: str) -> List[DartEnumCaseInfo]:
        """Extract enum values from enum body."""
        cases = []
        if not body:
            return cases

        # Enum values come before the first semicolon
        parts = body.split(';', 1)
        values_section = parts[0]

        for match in self.ENUM_VALUE_PATTERN.finditer(values_section):
            name = match.group('name')
            if name in ('const', 'factory', 'static', 'final', 'void', 'String', 'int', 'double', 'bool'):
                continue
            args = []
            if match.group('args'):
                args = [a.strip() for a in match.group('args').split(',')]
            cases.append(DartEnumCaseInfo(
                name=name,
                arguments=args,
            ))

        return cases[:30]

    def _extract_method_names(self, body: str) -> List[str]:
        """Extract method names from a body (for extensions)."""
        methods = []
        if not body:
            return methods

        method_pattern = re.compile(
            r'^\s*(?:static\s+)?(?:\w+(?:<[^>]+>)?\s+)?(\w+)\s*\(',
            re.MULTILINE
        )
        for match in method_pattern.finditer(body):
            name = match.group(1)
            if name not in ('if', 'else', 'for', 'while', 'switch', 'try', 'catch', 'return'):
                methods.append(name)

        return methods[:20]
