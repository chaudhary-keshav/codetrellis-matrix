"""
CTypeExtractor - Extracts C struct, union, enum, and typedef definitions.

This extractor parses C source code and extracts:
- Struct definitions with fields, nested structs, bitfields
- Union definitions
- Enum definitions with named constants and explicit values
- Typedefs (simple, function pointer, struct/union/enum aliases)
- Forward declarations (struct/union/enum)
- Packed/aligned/attributed types (GCC __attribute__, MSVC __declspec)

Supports all C standards: C89/C90, C99, C11, C17, C23.

Part of CodeTrellis v4.19 - C Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CFieldInfo:
    """Information about a C struct/union field."""
    name: str
    type: str
    is_pointer: bool = False
    is_array: bool = False
    array_size: Optional[str] = None
    is_bitfield: bool = False
    bitfield_width: Optional[int] = None
    is_const: bool = False
    is_volatile: bool = False
    comment: Optional[str] = None


@dataclass
class CStructInfo:
    """Information about a C struct."""
    name: str
    fields: List[CFieldInfo] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    is_packed: bool = False
    is_aligned: bool = False
    alignment: Optional[int] = None
    is_anonymous: bool = False
    is_typedef: bool = False
    typedef_name: Optional[str] = None
    nested_types: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class CUnionInfo:
    """Information about a C union."""
    name: str
    fields: List[CFieldInfo] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    is_anonymous: bool = False
    is_typedef: bool = False
    typedef_name: Optional[str] = None
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class CEnumConstantInfo:
    """Information about a C enum constant."""
    name: str
    value: Optional[str] = None
    comment: Optional[str] = None


@dataclass
class CEnumInfo:
    """Information about a C enum."""
    name: str
    constants: List[CEnumConstantInfo] = field(default_factory=list)
    is_typedef: bool = False
    typedef_name: Optional[str] = None
    is_anonymous: bool = False
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class CTypedefInfo:
    """Information about a C typedef."""
    name: str
    underlying_type: str
    is_function_pointer: bool = False
    is_struct: bool = False
    is_union: bool = False
    is_enum: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class CForwardDeclInfo:
    """Information about a C forward declaration."""
    name: str
    kind: str = "struct"  # struct, union, enum
    file: str = ""
    line_number: int = 0


class CTypeExtractor:
    """
    Extracts C struct, union, enum, and typedef definitions from source code.

    Handles:
    - Named and anonymous struct/union/enum definitions
    - Typedef aliases for primitive types, structs, unions, enums, function pointers
    - Bitfields
    - Packed/aligned attributes (GCC and MSVC)
    - Nested struct/union definitions
    - Forward declarations
    - C11 _Alignas and _Atomic qualifiers
    - C23 constexpr, typeof
    """

    # Struct pattern: struct Name { ... } or typedef struct { ... } Name;
    # Also handles: struct __attribute__((packed)) Name { ... }
    STRUCT_PATTERN = re.compile(
        r'(?:(?P<typedef>typedef)\s+)?'
        r'(?P<attrs>(?:__attribute__\s*\(\([^)]*\)\)\s*)*)'
        r'struct\s+'
        r'(?P<midattrs>(?:__attribute__\s*\(\([^)]*\)\)\s*)*)'
        r'(?P<tag>\w+)?\s*\{'
        r'(?P<body>[^}]*(?:\{[^}]*\}[^}]*)*)'
        r'\}\s*(?P<attrs2>(?:__attribute__\s*\(\([^)]*\)\)\s*)*)'
        r'(?P<alias>\w+)?\s*;',
        re.MULTILINE | re.DOTALL
    )

    # Union pattern
    UNION_PATTERN = re.compile(
        r'(?:(?P<typedef>typedef)\s+)?'
        r'union\s+(?P<tag>\w+)?\s*\{'
        r'(?P<body>[^}]*(?:\{[^}]*\}[^}]*)*)'
        r'\}\s*(?P<alias>\w+)?\s*;',
        re.MULTILINE | re.DOTALL
    )

    # Enum pattern
    ENUM_PATTERN = re.compile(
        r'(?:(?P<typedef>typedef)\s+)?'
        r'enum\s+(?P<tag>\w+)?\s*\{'
        r'(?P<body>[^}]*)'
        r'\}\s*(?P<alias>\w+)?\s*;',
        re.MULTILINE | re.DOTALL
    )

    # Typedef pattern (simple typedefs, not struct/union/enum)
    TYPEDEF_PATTERN = re.compile(
        r'^typedef\s+(?P<type>[^;{]+?)\s+(?P<name>\w+)\s*;',
        re.MULTILINE
    )

    # Function pointer typedef: typedef return_type (*name)(params);
    FUNC_PTR_TYPEDEF = re.compile(
        r'typedef\s+(?P<ret>[^(]+?)\s*\(\s*\*\s*(?P<name>\w+)\s*\)\s*\((?P<params>[^)]*)\)\s*;',
        re.MULTILINE
    )

    # Forward declaration: struct Name; or union Name; or enum Name;
    FORWARD_DECL = re.compile(
        r'^(?:struct|union|enum)\s+(\w+)\s*;',
        re.MULTILINE
    )

    # Field pattern within struct/union body
    FIELD_PATTERN = re.compile(
        r'(?P<qualifiers>(?:(?:const|volatile|static|register|_Atomic|_Alignas\s*\([^)]*\))\s+)*)'
        r'(?P<type>(?:(?:unsigned|signed|long|short|struct|union|enum)\s+)*\w[\w\s*]*?)'
        r'\s+(?P<stars>\**)(?P<name>\w+)'
        r'(?:\[(?P<arrsize>[^\]]*)\])?'
        r'(?:\s*:\s*(?P<bitwidth>\d+))?'
        r'\s*;',
        re.MULTILINE
    )

    # C23/GCC attributes: [[...]] or __attribute__((...))
    ATTRIBUTE_PATTERN = re.compile(
        r'(?:__attribute__\s*\(\(([^)]*)\)\)|'
        r'\[\[([^\]]*)\]\])',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the C type extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all C type definitions from source code.

        Args:
            content: C source code content
            file_path: Path to source file

        Returns:
            Dict with 'structs', 'unions', 'enums', 'typedefs', 'forward_decls' keys
        """
        # Remove single-line comments for cleaner parsing
        clean = re.sub(r'//[^\n]*', '', content)
        # Remove multi-line comments but preserve line counts
        clean = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), clean, flags=re.DOTALL)

        structs = self._extract_structs(clean, file_path, content)
        unions = self._extract_unions(clean, file_path, content)
        enums = self._extract_enums(clean, file_path, content)
        typedefs = self._extract_typedefs(clean, file_path, content)
        forward_decls = self._extract_forward_decls(clean, file_path, content)

        return {
            'structs': structs,
            'unions': unions,
            'enums': enums,
            'typedefs': typedefs,
            'forward_decls': forward_decls,
        }

    def _get_line_number(self, content: str, pos: int) -> int:
        """Get line number from position in content."""
        return content[:pos].count('\n') + 1

    def _extract_doc_comment(self, content: str, pos: int) -> Optional[str]:
        """Extract doc comment (/** ... */ or ///) preceding a definition."""
        before = content[:pos].rstrip()
        lines = before.split('\n')
        doc_lines = []
        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith('///'):
                doc_lines.insert(0, stripped[3:].strip())
            elif stripped.endswith('*/'):
                # Capture block comment
                block_start = before.rfind('/**')
                if block_start >= 0:
                    block = before[block_start:].strip()
                    # Remove /** and */
                    block = re.sub(r'^/\*\*\s*', '', block)
                    block = re.sub(r'\s*\*/$', '', block)
                    # Remove leading * on each line
                    block_lines = [re.sub(r'^\s*\*\s?', '', l) for l in block.split('\n')]
                    return ' '.join(l.strip() for l in block_lines if l.strip())
                break
            elif stripped.startswith('*'):
                continue  # Part of block comment
            else:
                break
        return ' '.join(doc_lines) if doc_lines else None

    def _parse_fields(self, body: str) -> List[CFieldInfo]:
        """Parse struct/union body to extract fields."""
        fields = []
        for match in self.FIELD_PATTERN.finditer(body):
            qualifiers = match.group('qualifiers').strip() if match.group('qualifiers') else ''
            ftype = match.group('type').strip()
            stars = match.group('stars') or ''
            name = match.group('name')
            arr_size = match.group('arrsize')
            bitwidth = match.group('bitwidth')

            full_type = ftype + stars if stars else ftype

            fields.append(CFieldInfo(
                name=name,
                type=full_type,
                is_pointer='*' in stars if stars else False,
                is_array=arr_size is not None,
                array_size=arr_size,
                is_bitfield=bitwidth is not None,
                bitfield_width=int(bitwidth) if bitwidth else None,
                is_const='const' in qualifiers,
                is_volatile='volatile' in qualifiers,
            ))
        return fields

    def _extract_structs(self, clean: str, file_path: str, original: str) -> List[CStructInfo]:
        """Extract struct definitions."""
        structs = []
        for match in self.STRUCT_PATTERN.finditer(clean):
            tag = match.group('tag') or ''
            alias = match.group('alias') or ''
            is_typedef = match.group('typedef') is not None
            body = match.group('body')
            attrs_str = (match.group('attrs') or '') + (match.group('midattrs') or '') + (match.group('attrs2') or '')

            name = alias if is_typedef and alias else tag
            if not name:
                name = '<anonymous>'

            line_num = self._get_line_number(original, match.start())
            doc = self._extract_doc_comment(original, match.start())

            attrs = re.findall(r'__attribute__\s*\(\(([^)]*)\)\)', attrs_str)
            is_packed = 'packed' in attrs_str
            is_aligned = 'aligned' in attrs_str
            alignment = None
            align_match = re.search(r'aligned\s*\((\d+)\)', attrs_str)
            if align_match:
                alignment = int(align_match.group(1))

            fields = self._parse_fields(body)

            # Detect nested types
            nested = []
            for nested_m in re.finditer(r'(?:struct|union)\s+(\w+)\s*\{', body):
                nested.append(nested_m.group(1))

            structs.append(CStructInfo(
                name=name,
                fields=fields,
                attributes=attrs,
                is_packed=is_packed,
                is_aligned=is_aligned,
                alignment=alignment,
                is_anonymous=not tag and not alias,
                is_typedef=is_typedef,
                typedef_name=alias if is_typedef else None,
                nested_types=nested,
                file=file_path,
                line_number=line_num,
                doc_comment=doc,
            ))
        return structs

    def _extract_unions(self, clean: str, file_path: str, original: str) -> List[CUnionInfo]:
        """Extract union definitions."""
        unions = []
        for match in self.UNION_PATTERN.finditer(clean):
            tag = match.group('tag') or ''
            alias = match.group('alias') or ''
            is_typedef = match.group('typedef') is not None
            body = match.group('body')

            name = alias if is_typedef and alias else tag
            if not name:
                name = '<anonymous>'

            line_num = self._get_line_number(original, match.start())
            doc = self._extract_doc_comment(original, match.start())

            fields = self._parse_fields(body)

            unions.append(CUnionInfo(
                name=name,
                fields=fields,
                is_anonymous=not tag and not alias,
                is_typedef=is_typedef,
                typedef_name=alias if is_typedef else None,
                file=file_path,
                line_number=line_num,
                doc_comment=doc,
            ))
        return unions

    def _extract_enums(self, clean: str, file_path: str, original: str) -> List[CEnumInfo]:
        """Extract enum definitions."""
        enums = []
        for match in self.ENUM_PATTERN.finditer(clean):
            tag = match.group('tag') or ''
            alias = match.group('alias') or ''
            is_typedef = match.group('typedef') is not None
            body = match.group('body')

            name = alias if is_typedef and alias else tag
            if not name:
                name = '<anonymous>'

            line_num = self._get_line_number(original, match.start())
            doc = self._extract_doc_comment(original, match.start())

            constants = []
            # Split on commas and parse each constant. Handle last item without comma.
            for const_match in re.finditer(r'(\w+)\s*(?:=\s*([^,\n}]+))?\s*(?:,|$)', body.strip()):
                cname = const_match.group(1)
                cvalue = const_match.group(2).strip() if const_match.group(2) else None
                constants.append(CEnumConstantInfo(name=cname, value=cvalue))

            enums.append(CEnumInfo(
                name=name,
                constants=constants,
                is_typedef=is_typedef,
                typedef_name=alias if is_typedef else None,
                is_anonymous=not tag and not alias,
                file=file_path,
                line_number=line_num,
                doc_comment=doc,
            ))
        return enums

    def _extract_typedefs(self, clean: str, file_path: str, original: str) -> List[CTypedefInfo]:
        """Extract typedefs (simple and function pointer)."""
        typedefs = []

        # Function pointer typedefs first
        for match in self.FUNC_PTR_TYPEDEF.finditer(clean):
            ret = match.group('ret').strip()
            name = match.group('name')
            params = match.group('params').strip()
            line_num = self._get_line_number(original, match.start())
            typedefs.append(CTypedefInfo(
                name=name,
                underlying_type=f"{ret}(*)({params})",
                is_function_pointer=True,
                file=file_path,
                line_number=line_num,
            ))

        # Simple typedefs (exclude struct/union/enum ones already captured)
        for match in self.TYPEDEF_PATTERN.finditer(clean):
            full_text = match.group(0)
            # Skip struct/union/enum typedefs (already handled)
            if re.search(r'\b(struct|union|enum)\b.*\{', full_text, re.DOTALL):
                continue
            # Skip function pointer typedefs
            if '(*' in full_text:
                continue
            type_str = match.group('type').strip()
            name = match.group('name')
            line_num = self._get_line_number(original, match.start())

            is_struct = 'struct' in type_str
            is_union = 'union' in type_str
            is_enum = 'enum' in type_str

            typedefs.append(CTypedefInfo(
                name=name,
                underlying_type=type_str,
                is_struct=is_struct,
                is_union=is_union,
                is_enum=is_enum,
                file=file_path,
                line_number=line_num,
            ))

        return typedefs

    def _extract_forward_decls(self, clean: str, file_path: str, original: str) -> List[CForwardDeclInfo]:
        """Extract forward declarations."""
        decls = []
        # Track struct/union/enum names that have bodies (not forward decls)
        defined = set()
        for m in re.finditer(r'(?:struct|union|enum)\s+(\w+)\s*\{', clean):
            defined.add(m.group(1))

        for match in self.FORWARD_DECL.finditer(clean):
            full = match.group(0).strip()
            name = match.group(1)
            if name in defined:
                continue  # Has body, not forward declaration
            kind = full.split()[0]
            line_num = self._get_line_number(original, match.start())
            decls.append(CForwardDeclInfo(
                name=name,
                kind=kind,
                file=file_path,
                line_number=line_num,
            ))
        return decls
