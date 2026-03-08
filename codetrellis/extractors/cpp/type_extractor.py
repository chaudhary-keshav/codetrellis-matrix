"""
CppTypeExtractor - Extracts C++ class, struct, union, enum, and template definitions.

This extractor parses C++ source code and extracts:
- Class definitions with inheritance, access specifiers, virtual methods
- Struct definitions with fields
- Union definitions
- Enum definitions (both C-style and enum class/struct)
- Template classes and structs (class templates, partial/full specializations)
- Concept definitions (C++20)
- Type aliases (using, typedef)
- Forward declarations
- Nested types
- CRTP patterns
- Namespace-scoped types

Supports all C++ standards: C++98, C++03, C++11, C++14, C++17, C++20, C++23, C++26.

Part of CodeTrellis v4.20 - C++ Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CppFieldInfo:
    """Information about a C++ class/struct/union field."""
    name: str
    type: str
    access: str = "public"  # public, protected, private
    is_static: bool = False
    is_const: bool = False
    is_constexpr: bool = False
    is_inline: bool = False  # C++17 inline static
    is_mutable: bool = False
    is_volatile: bool = False
    is_pointer: bool = False
    is_reference: bool = False
    is_array: bool = False
    array_size: Optional[str] = None
    is_bitfield: bool = False
    bitfield_width: Optional[int] = None
    default_value: Optional[str] = None
    comment: Optional[str] = None


@dataclass
class CppBaseClassInfo:
    """Information about a C++ base class."""
    name: str
    access: str = "public"  # public, protected, private
    is_virtual: bool = False
    is_template: bool = False
    template_args: Optional[str] = None


@dataclass
class CppClassInfo:
    """Information about a C++ class."""
    name: str
    kind: str = "class"  # class, struct
    fields: List[CppFieldInfo] = field(default_factory=list)
    bases: List[CppBaseClassInfo] = field(default_factory=list)
    nested_types: List[str] = field(default_factory=list)
    is_template: bool = False
    template_params: Optional[str] = None
    is_abstract: bool = False
    is_final: bool = False
    is_struct: bool = False
    is_pod: bool = False
    is_aggregate: bool = False
    namespace: Optional[str] = None
    attributes: List[str] = field(default_factory=list)
    has_virtual_destructor: bool = False
    has_default_constructor: bool = False
    has_copy_constructor: bool = False
    has_move_constructor: bool = False
    is_crtp: bool = False  # Curiously Recurring Template Pattern
    friend_classes: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class CppUnionInfo:
    """Information about a C++ union."""
    name: str
    fields: List[CppFieldInfo] = field(default_factory=list)
    is_template: bool = False
    template_params: Optional[str] = None
    is_anonymous: bool = False
    namespace: Optional[str] = None
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class CppEnumConstantInfo:
    """Information about a C++ enum constant."""
    name: str
    value: Optional[str] = None
    comment: Optional[str] = None


@dataclass
class CppEnumInfo:
    """Information about a C++ enum."""
    name: str
    constants: List[CppEnumConstantInfo] = field(default_factory=list)
    is_scoped: bool = False  # enum class / enum struct
    underlying_type: Optional[str] = None  # enum Foo : uint8_t
    is_anonymous: bool = False
    namespace: Optional[str] = None
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class CppTypeAliasInfo:
    """Information about a C++ type alias (using/typedef)."""
    name: str
    underlying_type: str
    is_using: bool = False  # using X = Y (vs typedef)
    is_template: bool = False  # template<typename T> using X = ...
    template_params: Optional[str] = None
    is_function_pointer: bool = False
    namespace: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CppConceptInfo:
    """Information about a C++20 concept."""
    name: str
    template_params: Optional[str] = None
    constraint_expr: Optional[str] = None
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class CppForwardDeclInfo:
    """Information about a C++ forward declaration."""
    name: str
    kind: str = "class"  # class, struct, union, enum
    namespace: Optional[str] = None
    is_template: bool = False
    template_params: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CppNamespaceInfo:
    """Information about a C++ namespace."""
    name: str
    is_inline: bool = False
    is_anonymous: bool = False
    file: str = ""
    line_number: int = 0


class CppTypeExtractor:
    """
    Extracts C++ class, struct, union, enum, and type alias definitions.

    Handles:
    - Named and anonymous class/struct/union/enum
    - Template classes/structs with parameters
    - Concept definitions (C++20)
    - enum class / enum struct (C++11)
    - using type aliases (C++11)
    - Template aliases (C++11)
    - Inheritance (single, multiple, virtual)
    - Final classes/structs (C++11)
    - Nested types
    - Forward declarations
    - Namespace tracking
    - CRTP detection
    - Attributes ([[nodiscard]], [[deprecated]], etc.)
    """

    # Class/struct pattern
    CLASS_PATTERN = re.compile(
        r'(?:(?P<template>template\s*<[^>]*(?:<[^>]*>[^>]*)*>)\s+)?'
        r'(?P<attrs>(?:\[\[[^\]]*\]\]\s*)*)'
        r'(?P<kind>class|struct)\s+'
        r'(?P<attrs2>(?:\[\[[^\]]*\]\]\s*)*)'
        r'(?P<declspec>(?:__declspec\s*\([^)]*\)\s*)*)'
        r'(?P<name>\w+)'
        r'(?:\s+(?P<final>final))?'
        r'(?:\s*:\s*(?P<bases>[^{]+?))?'
        r'\s*\{',
        re.MULTILINE | re.DOTALL
    )

    # Union pattern
    UNION_PATTERN = re.compile(
        r'(?:(?P<template>template\s*<[^>]*(?:<[^>]*>[^>]*)*>)\s+)?'
        r'union\s+(?P<name>\w+)?\s*\{',
        re.MULTILINE | re.DOTALL
    )

    # Enum pattern (both C-style and scoped enums)
    ENUM_PATTERN = re.compile(
        r'enum\s+(?P<scoped>class|struct)?\s*(?P<name>\w+)?'
        r'(?:\s*:\s*(?P<underlying>\w[\w:]*))?\s*\{'
        r'(?P<body>[^}]*)'
        r'\}',
        re.MULTILINE | re.DOTALL
    )

    # Using type alias: using Name = Type;
    USING_ALIAS_PATTERN = re.compile(
        r'(?:(?P<template>template\s*<[^>]*(?:<[^>]*>[^>]*)*>)\s+)?'
        r'using\s+(?P<name>\w+)\s*=\s*(?P<type>[^;]+);',
        re.MULTILINE
    )

    # Typedef pattern
    TYPEDEF_PATTERN = re.compile(
        r'^typedef\s+(?P<type>[^;{]+?)\s+(?P<name>\w+)\s*;',
        re.MULTILINE
    )

    # Function pointer typedef: typedef ret_type (*name)(params);
    FUNC_PTR_TYPEDEF = re.compile(
        r'typedef\s+(?P<ret>[^(]+?)\s*\(\s*\*\s*(?P<name>\w+)\s*\)\s*\((?P<params>[^)]*)\)\s*;',
        re.MULTILINE
    )

    # Concept definition (C++20)
    CONCEPT_PATTERN = re.compile(
        r'(?P<template>template\s*<[^>]*(?:<[^>]*>[^>]*)*>)\s+'
        r'concept\s+(?P<name>\w+)\s*=\s*(?P<expr>[^;]+);',
        re.MULTILINE | re.DOTALL
    )

    # Forward declaration
    FORWARD_DECL = re.compile(
        r'^(?:(?P<template>template\s*<[^>]*>)\s+)?'
        r'(?P<kind>class|struct|union|enum)\s+(?P<name>\w+)\s*;',
        re.MULTILINE
    )

    # Namespace pattern
    NAMESPACE_PATTERN = re.compile(
        r'(?P<inline>inline\s+)?namespace\s+(?P<name>[\w:]+)?\s*\{',
        re.MULTILINE
    )

    # Base class parser
    BASE_CLASS_PATTERN = re.compile(
        r'(?P<access>public|protected|private)?\s*(?P<virtual>virtual\s+)?'
        r'(?P<name>[\w:]+(?:<[^>]*>)?)',
    )

    # Field pattern within class/struct body
    FIELD_PATTERN = re.compile(
        r'(?P<qualifiers>(?:(?:static|mutable|inline|constexpr|const|volatile|thread_local)\s+)*)'
        r'(?P<type>(?:(?:unsigned|signed|long|short|struct|class|enum|typename)\s+)*[\w:]+(?:<[^>]*>)?[\s*&]*?)'
        r'\s+(?P<stars>[*&]*)(?P<name>\w+)'
        r'(?:\[(?P<arrsize>[^\]]*)\])?'
        r'(?:\s*:\s*(?P<bitwidth>\d+))?'
        r'(?:\s*=\s*(?P<default>[^;,}]+))?'
        r'\s*[;,]',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the C++ type extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all type definitions from C++ source code.

        Args:
            content: C++ source code content
            file_path: Path to source file

        Returns:
            Dict with 'classes', 'unions', 'enums', 'type_aliases', 'concepts',
            'forward_decls', 'namespaces' lists
        """
        result = {
            'classes': [],
            'unions': [],
            'enums': [],
            'type_aliases': [],
            'concepts': [],
            'forward_decls': [],
            'namespaces': [],
        }

        # Extract namespaces first (for context)
        result['namespaces'] = self._extract_namespaces(content, file_path)

        # Extract forward declarations (before full types to avoid double-counting)
        result['forward_decls'] = self._extract_forward_decls(content, file_path)

        # Extract classes and structs
        result['classes'] = self._extract_classes(content, file_path)

        # Extract unions
        result['unions'] = self._extract_unions(content, file_path)

        # Extract enums (both scoped and unscoped)
        result['enums'] = self._extract_enums(content, file_path)

        # Extract type aliases (using and typedef)
        result['type_aliases'] = self._extract_type_aliases(content, file_path)

        # Extract concepts (C++20)
        result['concepts'] = self._extract_concepts(content, file_path)

        return result

    def _extract_classes(self, content: str, file_path: str) -> List[CppClassInfo]:
        """Extract class and struct definitions."""
        classes = []
        lines = content.split('\n')

        for match in self.CLASS_PATTERN.finditer(content):
            name = match.group('name')
            kind = match.group('kind')
            is_template = match.group('template') is not None
            template_params = match.group('template') if is_template else None
            is_final = match.group('final') is not None
            bases_str = match.group('bases')

            # Get line number
            line_num = content[:match.start()].count('\n') + 1

            # Parse doc comment (line above)
            doc_comment = self._get_doc_comment(lines, line_num - 1)

            # Parse base classes
            bases = []
            if bases_str:
                bases = self._parse_bases(bases_str.strip())

            # Check for attributes
            attrs = []
            attr_str = match.group('attrs') or ''
            attr_str += match.group('attrs2') or ''
            if attr_str:
                for attr_match in re.finditer(r'\[\[([^\]]*)\]\]', attr_str):
                    attrs.append(attr_match.group(1))

            # Extract class body
            body_start = match.end() - 1  # position of '{'
            body = self._extract_brace_body(content, body_start)

            # Detect virtual destructor
            has_virtual_dtor = bool(re.search(r'virtual\s+~' + re.escape(name), body)) if body else False

            # Detect abstract class (has pure virtual methods)
            is_abstract = bool(re.search(r'=\s*0\s*;', body)) if body else False

            # Detect special member functions
            has_default_ctor = bool(re.search(r'\b' + re.escape(name) + r'\s*\(\s*\)', body)) if body else False
            has_copy_ctor = bool(re.search(r'\b' + re.escape(name) + r'\s*\(\s*(?:const\s+)?' + re.escape(name) + r'\s*&', body)) if body else False
            has_move_ctor = bool(re.search(r'\b' + re.escape(name) + r'\s*\(\s*' + re.escape(name) + r'\s*&&', body)) if body else False

            # Detect friends
            friends = re.findall(r'friend\s+(?:class|struct)\s+(\w+)', body) if body else []

            # Detect nested types
            nested = re.findall(r'(?:class|struct|enum|union)\s+(\w+)\s*[:{]', body) if body else []

            # Detect CRTP: class X : public Base<X>
            is_crtp = any(name in b.name for b in bases if '<' in b.name)

            # Extract fields
            fields = self._extract_fields(body, kind) if body else []

            info = CppClassInfo(
                name=name,
                kind=kind,
                fields=fields,
                bases=bases,
                nested_types=nested,
                is_template=is_template,
                template_params=template_params,
                is_abstract=is_abstract,
                is_final=is_final,
                is_struct=(kind == 'struct'),
                attributes=attrs,
                has_virtual_destructor=has_virtual_dtor,
                has_default_constructor=has_default_ctor,
                has_copy_constructor=has_copy_ctor,
                has_move_constructor=has_move_ctor,
                is_crtp=is_crtp,
                friend_classes=friends,
                file=file_path,
                line_number=line_num,
                doc_comment=doc_comment,
            )
            classes.append(info)

        return classes

    def _extract_unions(self, content: str, file_path: str) -> List[CppUnionInfo]:
        """Extract union definitions."""
        unions = []
        for match in self.UNION_PATTERN.finditer(content):
            name = match.group('name') or '<anonymous>'
            is_template = match.group('template') is not None
            template_params = match.group('template') if is_template else None
            line_num = content[:match.start()].count('\n') + 1

            body_start = match.end() - 1
            body = self._extract_brace_body(content, body_start)
            fields = self._extract_fields(body, 'union') if body else []

            unions.append(CppUnionInfo(
                name=name,
                fields=fields,
                is_template=is_template,
                template_params=template_params,
                is_anonymous=(name == '<anonymous>'),
                file=file_path,
                line_number=line_num,
            ))
        return unions

    def _extract_enums(self, content: str, file_path: str) -> List[CppEnumInfo]:
        """Extract enum definitions (both scoped and unscoped)."""
        enums = []
        for match in self.ENUM_PATTERN.finditer(content):
            name = match.group('name') or '<anonymous>'
            is_scoped = match.group('scoped') is not None
            underlying = match.group('underlying')
            body = match.group('body')
            line_num = content[:match.start()].count('\n') + 1

            constants = self._parse_enum_body(body)

            enums.append(CppEnumInfo(
                name=name,
                constants=constants,
                is_scoped=is_scoped,
                underlying_type=underlying,
                is_anonymous=(name == '<anonymous>'),
                file=file_path,
                line_number=line_num,
            ))
        return enums

    def _extract_type_aliases(self, content: str, file_path: str) -> List[CppTypeAliasInfo]:
        """Extract using and typedef type aliases."""
        aliases = []

        # Using aliases
        for match in self.USING_ALIAS_PATTERN.finditer(content):
            name = match.group('name')
            underlying = match.group('type').strip()
            is_template = match.group('template') is not None
            template_params = match.group('template') if is_template else None
            line_num = content[:match.start()].count('\n') + 1

            # Skip using namespace declarations
            if underlying.startswith('namespace'):
                continue

            aliases.append(CppTypeAliasInfo(
                name=name,
                underlying_type=underlying,
                is_using=True,
                is_template=is_template,
                template_params=template_params,
                file=file_path,
                line_number=line_num,
            ))

        # Function pointer typedefs
        for match in self.FUNC_PTR_TYPEDEF.finditer(content):
            name = match.group('name')
            ret = match.group('ret').strip()
            params = match.group('params').strip()
            line_num = content[:match.start()].count('\n') + 1
            aliases.append(CppTypeAliasInfo(
                name=name,
                underlying_type=f"{ret}(*)({params})",
                is_function_pointer=True,
                file=file_path,
                line_number=line_num,
            ))

        # Regular typedefs (not function pointers, not struct/class/enum/union)
        for match in self.TYPEDEF_PATTERN.finditer(content):
            name = match.group('name')
            underlying = match.group('type').strip()
            line_num = content[:match.start()].count('\n') + 1

            # Skip if already captured as struct/union/enum typedef or function pointer
            if re.search(r'\(\s*\*', underlying):
                continue
            if re.match(r'(?:struct|union|enum|class)\s+\w+\s*\{', underlying):
                continue

            aliases.append(CppTypeAliasInfo(
                name=name,
                underlying_type=underlying,
                is_using=False,
                file=file_path,
                line_number=line_num,
            ))

        return aliases

    def _extract_concepts(self, content: str, file_path: str) -> List[CppConceptInfo]:
        """Extract C++20 concept definitions."""
        concepts = []
        for match in self.CONCEPT_PATTERN.finditer(content):
            name = match.group('name')
            template_params = match.group('template')
            constraint_expr = match.group('expr').strip()
            line_num = content[:match.start()].count('\n') + 1

            lines = content.split('\n')
            doc_comment = self._get_doc_comment(lines, line_num - 1)

            concepts.append(CppConceptInfo(
                name=name,
                template_params=template_params,
                constraint_expr=constraint_expr[:200] if constraint_expr else None,
                file=file_path,
                line_number=line_num,
                doc_comment=doc_comment,
            ))
        return concepts

    def _extract_forward_decls(self, content: str, file_path: str) -> List[CppForwardDeclInfo]:
        """Extract forward declarations."""
        decls = []
        for match in self.FORWARD_DECL.finditer(content):
            name = match.group('name')
            kind = match.group('kind')
            is_template = match.group('template') is not None
            template_params = match.group('template') if is_template else None
            line_num = content[:match.start()].count('\n') + 1

            decls.append(CppForwardDeclInfo(
                name=name,
                kind=kind,
                is_template=is_template,
                template_params=template_params,
                file=file_path,
                line_number=line_num,
            ))
        return decls

    def _extract_namespaces(self, content: str, file_path: str) -> List[CppNamespaceInfo]:
        """Extract namespace definitions."""
        namespaces = []
        for match in self.NAMESPACE_PATTERN.finditer(content):
            name = match.group('name') or '<anonymous>'
            is_inline = match.group('inline') is not None
            line_num = content[:match.start()].count('\n') + 1

            namespaces.append(CppNamespaceInfo(
                name=name,
                is_inline=is_inline,
                is_anonymous=(name == '<anonymous>'),
                file=file_path,
                line_number=line_num,
            ))
        return namespaces

    def _parse_bases(self, bases_str: str) -> List[CppBaseClassInfo]:
        """Parse base class list from class definition."""
        bases = []
        # Split by comma, but not inside angle brackets
        parts = self._split_outside_angles(bases_str)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            match = self.BASE_CLASS_PATTERN.match(part)
            if match:
                access = match.group('access') or 'private'
                is_virtual = match.group('virtual') is not None
                name = match.group('name')
                is_template = '<' in name
                template_args = None
                if is_template:
                    idx = name.index('<')
                    template_args = name[idx:]
                    # keep full name for identification
                bases.append(CppBaseClassInfo(
                    name=name,
                    access=access,
                    is_virtual=is_virtual,
                    is_template=is_template,
                    template_args=template_args,
                ))
        return bases

    def _parse_enum_body(self, body: str) -> List[CppEnumConstantInfo]:
        """Parse enum body to extract constants."""
        constants = []
        if not body:
            return constants

        for line in body.split(','):
            line = line.strip()
            if not line:
                continue
            # Remove trailing comments
            comment = None
            comment_match = re.search(r'//(.*)$|/\*(.+?)\*/', line)
            if comment_match:
                comment = (comment_match.group(1) or comment_match.group(2)).strip()
                line = line[:comment_match.start()].strip()

            if not line:
                continue

            # Parse name = value
            if '=' in line:
                parts = line.split('=', 1)
                name = parts[0].strip()
                value = parts[1].strip()
            else:
                name = line.strip()
                value = None

            if name and re.match(r'^\w+$', name):
                constants.append(CppEnumConstantInfo(
                    name=name,
                    value=value,
                    comment=comment,
                ))
        return constants

    def _extract_fields(self, body: str, kind: str) -> List[CppFieldInfo]:
        """Extract field declarations from class/struct/union body."""
        fields = []
        if not body:
            return fields

        current_access = 'public' if kind in ('struct', 'union') else 'private'

        for line in body.split('\n'):
            stripped = line.strip()

            # Track access specifiers
            access_match = re.match(r'(public|protected|private)\s*:', stripped)
            if access_match:
                current_access = access_match.group(1)
                continue

            # Skip method declarations, nested types, etc
            if re.match(r'(?:virtual|static|inline|constexpr|explicit)?\s*(?:~?\w+\s*\(|operator)', stripped):
                continue
            if re.match(r'(?:class|struct|enum|union|template|friend|using|typedef)\s', stripped):
                continue
            if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                continue

            match = self.FIELD_PATTERN.match(stripped)
            if match:
                qualifiers = match.group('qualifiers') or ''
                ftype = match.group('type').strip()
                stars = match.group('stars') or ''
                fname = match.group('name')
                arr_size = match.group('arrsize')
                bitwidth = match.group('bitwidth')
                default = match.group('default')

                fields.append(CppFieldInfo(
                    name=fname,
                    type=ftype + stars,
                    access=current_access,
                    is_static='static' in qualifiers,
                    is_const='const' in qualifiers or 'const' in ftype,
                    is_constexpr='constexpr' in qualifiers,
                    is_inline='inline' in qualifiers,
                    is_mutable='mutable' in qualifiers,
                    is_volatile='volatile' in qualifiers,
                    is_pointer='*' in stars,
                    is_reference='&' in stars,
                    is_array=arr_size is not None,
                    array_size=arr_size,
                    is_bitfield=bitwidth is not None,
                    bitfield_width=int(bitwidth) if bitwidth else None,
                    default_value=default.strip() if default else None,
                ))

        return fields

    def _extract_brace_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content between matching braces."""
        if start_pos >= len(content) or content[start_pos] != '{':
            return None

        depth = 0
        i = start_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[start_pos + 1:i]
            i += 1
        return None

    def _split_outside_angles(self, s: str) -> List[str]:
        """Split string by commas, but not inside angle brackets."""
        parts = []
        depth = 0
        current = []
        for ch in s:
            if ch == '<':
                depth += 1
            elif ch == '>':
                depth -= 1
            elif ch == ',' and depth == 0:
                parts.append(''.join(current))
                current = []
                continue
            current.append(ch)
        if current:
            parts.append(''.join(current))
        return parts

    def _get_doc_comment(self, lines: List[str], line_idx: int) -> Optional[str]:
        """Extract doc comment from lines above a definition."""
        if line_idx <= 0 or line_idx >= len(lines):
            return None

        comments = []
        i = line_idx - 1
        while i >= 0:
            stripped = lines[i].strip()
            if stripped.startswith('///') or stripped.startswith('//!'):
                comments.insert(0, stripped.lstrip('/!').strip())
            elif stripped.endswith('*/'):
                # Multi-line comment block
                while i >= 0:
                    stripped = lines[i].strip()
                    comments.insert(0, stripped.lstrip('/*! ').rstrip('*/').strip())
                    if stripped.startswith('/**') or stripped.startswith('/*!') or stripped.startswith('/*'):
                        break
                    i -= 1
                break
            elif stripped.startswith('*'):
                comments.insert(0, stripped.lstrip('* ').strip())
            else:
                break
            i -= 1

        return ' '.join(comments)[:500] if comments else None
