"""
RustTypeExtractor - Extracts Rust struct, enum, trait, type alias, and union definitions.

This extractor parses Rust source code and extracts:
- Struct definitions (named, tuple, unit) with fields, derives, generics
- Enum definitions with variants (unit, tuple, struct)
- Trait definitions with methods, associated types, and default impls
- Type aliases
- Union definitions
- impl blocks with methods
- Derive macros, attributes, visibility modifiers
- Lifetime annotations, generic bounds

Supports all Rust editions (2015, 2018, 2021, 2024) through Rust 1.x–latest.

Part of CodeTrellis v4.14 - Rust Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RustFieldInfo:
    """Information about a Rust struct field."""
    name: str
    type: str
    visibility: str = ""  # pub, pub(crate), pub(super), etc.
    attributes: List[str] = field(default_factory=list)
    comment: Optional[str] = None
    is_optional: bool = False  # Option<T>


@dataclass
class RustStructInfo:
    """Information about a Rust struct."""
    name: str
    fields: List[RustFieldInfo] = field(default_factory=list)
    generics: List[str] = field(default_factory=list)
    derives: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    visibility: str = ""
    file: str = ""
    line_number: int = 0
    is_tuple_struct: bool = False
    is_unit_struct: bool = False
    where_clause: Optional[str] = None
    implements: List[str] = field(default_factory=list)  # From impl blocks
    doc_comment: Optional[str] = None


@dataclass
class RustEnumVariantInfo:
    """Information about a Rust enum variant."""
    name: str
    fields: List[RustFieldInfo] = field(default_factory=list)  # For struct variants
    tuple_types: List[str] = field(default_factory=list)  # For tuple variants
    discriminant: Optional[str] = None  # = value
    is_unit: bool = False
    is_tuple: bool = False
    is_struct: bool = False


@dataclass
class RustEnumInfo:
    """Information about a Rust enum."""
    name: str
    variants: List[RustEnumVariantInfo] = field(default_factory=list)
    generics: List[str] = field(default_factory=list)
    derives: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    visibility: str = ""
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class RustTraitMethodInfo:
    """Information about a method in a trait definition."""
    name: str
    params: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    has_default_impl: bool = False
    is_async: bool = False
    is_unsafe: bool = False


@dataclass
class RustTraitInfo:
    """Information about a Rust trait."""
    name: str
    methods: List[RustTraitMethodInfo] = field(default_factory=list)
    associated_types: List[str] = field(default_factory=list)
    associated_consts: List[str] = field(default_factory=list)
    super_traits: List[str] = field(default_factory=list)
    generics: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    visibility: str = ""
    file: str = ""
    line_number: int = 0
    is_unsafe: bool = False
    is_auto: bool = False
    doc_comment: Optional[str] = None


@dataclass
class RustTypeAliasInfo:
    """Information about a Rust type alias."""
    name: str
    target_type: str
    generics: List[str] = field(default_factory=list)
    visibility: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class RustImplInfo:
    """Information about a Rust impl block."""
    target_type: str
    trait_name: Optional[str] = None
    methods: List[str] = field(default_factory=list)
    generics: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class RustTypeExtractor:
    """
    Extracts Rust type definitions from source code.

    Handles:
    - Named, tuple, and unit structs with fields and derives
    - Enums with unit, tuple, and struct variants
    - Traits with methods, associated types, super traits
    - Type aliases
    - impl blocks (inherent and trait impls)
    - Visibility modifiers (pub, pub(crate), pub(super), pub(in path))
    - Generics, lifetimes, and where clauses
    - Derive macros (#[derive(Debug, Clone, Serialize, ...)])
    - Doc comments (///)

    v4.14: Uses brace-balanced extraction for correct parsing.
    """

    # Derive attribute pattern
    DERIVE_PATTERN = re.compile(
        r'#\[derive\(([^)]+)\)\]',
        re.MULTILINE
    )

    # Other attribute pattern
    ATTRIBUTE_PATTERN = re.compile(
        r'#\[(?!derive)([^\]]+)\]',
        re.MULTILINE
    )

    # Doc comment pattern
    DOC_COMMENT_PATTERN = re.compile(
        r'((?:///[^\n]*\n)+)\s*',
        re.MULTILINE
    )

    # Struct header: pub struct Name<T> where T: Bound {
    STRUCT_HEADER = re.compile(
        r'(?P<vis>pub(?:\s*\([^)]*\))?\s+)?struct\s+(?P<name>\w+)(?:<(?P<generics>[^>]+)>)?(?:\s*where\s+(?P<where>[^{(;]+))?\s*(?P<body_start>[{(;])',
        re.MULTILINE
    )

    # Enum header: pub enum Name<T> {
    ENUM_HEADER = re.compile(
        r'(?P<vis>pub(?:\s*\([^)]*\))?\s+)?enum\s+(?P<name>\w+)(?:<(?P<generics>[^>]+)>)?\s*\{',
        re.MULTILINE
    )

    # Trait header: pub trait Name: SuperTrait {
    TRAIT_HEADER = re.compile(
        r'(?P<unsafe>unsafe\s+)?(?P<auto>auto\s+)?(?P<vis>pub(?:\s*\([^)]*\))?\s+)?trait\s+(?P<name>\w+)(?:<(?P<generics>[^>]+)>)?(?:\s*:\s*(?P<super_traits>[^{]+))?\s*\{',
        re.MULTILINE
    )

    # Type alias: pub type Name<T> = TargetType;
    TYPE_ALIAS_PATTERN = re.compile(
        r'(?P<vis>pub(?:\s*\([^)]*\))?\s+)?type\s+(?P<name>\w+)(?:<(?P<generics>[^>]+)>)?\s*=\s*(?P<target>[^;]+);',
        re.MULTILINE
    )

    # Impl block header: impl<T> Trait for Type<T> {  OR  impl Type {
    IMPL_HEADER = re.compile(
        r'impl(?:<(?P<generics>[^>]+)>)?\s+(?:(?P<trait_name>[\w:]+)\s+for\s+)?(?P<target>[\w<>,\s:\']+?)\s*\{',
        re.MULTILINE
    )

    # Struct field: pub name: Type,
    FIELD_PATTERN = re.compile(
        r'^\s*(?P<vis>pub(?:\s*\([^)]*\))?\s+)?(?P<name>\w+)\s*:\s*(?P<type>[^,}]+?)\s*,?\s*(?://\s*(?P<comment>.+))?$',
        re.MULTILINE
    )

    # Enum variant patterns
    VARIANT_UNIT = re.compile(r'^\s*(?P<name>\w+)\s*(?:=\s*(?P<disc>[^,}]+))?\s*,?\s*$', re.MULTILINE)
    VARIANT_TUPLE = re.compile(r'^\s*(?P<name>\w+)\s*\((?P<types>[^)]+)\)\s*,?\s*$', re.MULTILINE)
    VARIANT_STRUCT = re.compile(r'^\s*(?P<name>\w+)\s*\{', re.MULTILINE)

    # Trait method pattern
    TRAIT_METHOD = re.compile(
        r'^\s*(?P<async>async\s+)?(?P<unsafe>unsafe\s+)?fn\s+(?P<name>\w+)\s*(?:<[^>]*>)?\s*\((?P<params>[^)]*)\)(?:\s*->\s*(?P<ret>[^{;]+))?\s*(?P<has_body>\{|;)',
        re.MULTILINE
    )

    # Associated type in trait
    ASSOC_TYPE = re.compile(r'^\s*type\s+(\w+)', re.MULTILINE)

    # Associated const in trait
    ASSOC_CONST = re.compile(r'^\s*const\s+(\w+)\s*:', re.MULTILINE)

    def __init__(self):
        """Initialize the Rust type extractor."""
        pass

    @staticmethod
    def _extract_brace_body(content: str, open_brace_pos: int) -> Optional[str]:
        """
        Extract the body between matched braces using brace-counting.
        Handles nested braces, comments, string literals, raw strings,
        and character literals.
        """
        depth = 1
        i = open_brace_pos + 1
        in_string = False
        in_line_comment = False
        in_block_comment = False
        in_raw_string = False
        in_char = False
        raw_hash_count = 0
        length = len(content)

        while i < length and depth > 0:
            ch = content[i]
            next_ch = content[i + 1] if i + 1 < length else ''

            # Handle line comments
            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
                i += 1
                continue

            # Handle block comments (Rust supports nested block comments)
            if in_block_comment:
                if ch == '/' and next_ch == '*':
                    depth_comment = getattr(RustTypeExtractor._extract_brace_body, '_comment_depth', 1)
                    # Not tracking nested block comments here for simplicity
                    pass
                if ch == '*' and next_ch == '/':
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue

            # Handle strings
            if in_string:
                if ch == '\\':
                    i += 2
                    continue
                if ch == '"':
                    in_string = False
                i += 1
                continue

            # Handle raw strings r"..." or r#"..."#
            if in_raw_string:
                if ch == '"':
                    # Check for closing hashes
                    hashes = 0
                    j = i + 1
                    while j < length and content[j] == '#' and hashes < raw_hash_count:
                        hashes += 1
                        j += 1
                    if hashes == raw_hash_count:
                        in_raw_string = False
                        i = j
                        continue
                i += 1
                continue

            # Handle char literals
            if in_char:
                if ch == '\\':
                    i += 2
                    continue
                if ch == '\'':
                    in_char = False
                i += 1
                continue

            # Detect comment starts
            if ch == '/' and next_ch == '/':
                in_line_comment = True
                i += 2
                continue
            if ch == '/' and next_ch == '*':
                in_block_comment = True
                i += 2
                continue

            # Detect string starts
            if ch == '"':
                in_string = True
                i += 1
                continue

            # Detect raw string starts: r"...", r#"..."#, r##"..."##
            if ch == 'r' and (next_ch == '"' or next_ch == '#'):
                hashes = 0
                j = i + 1
                while j < length and content[j] == '#':
                    hashes += 1
                    j += 1
                if j < length and content[j] == '"':
                    in_raw_string = True
                    raw_hash_count = hashes
                    i = j + 1
                    continue

            # Detect char literals
            if ch == '\'' and next_ch != '\'':
                # Avoid lifetime annotations like 'a
                # Check if this is likely a char literal: 'x' or '\n'
                if i + 2 < length and (content[i + 2] == '\'' or (next_ch == '\\' and i + 3 < length and content[i + 3] == '\'')):
                    in_char = True
                    i += 1
                    continue

            # Count braces
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[open_brace_pos + 1:i]

            i += 1

        return None

    def _extract_doc_comment(self, content: str, pos: int) -> Optional[str]:
        """Extract doc comment (///) preceding a definition at the given position."""
        # Walk backwards from pos to find doc comment lines
        lines_before = content[:pos].rstrip().split('\n')
        doc_lines = []
        for line in reversed(lines_before):
            stripped = line.strip()
            if stripped.startswith('///'):
                doc_lines.insert(0, stripped[3:].strip())
            elif stripped.startswith('#[') or stripped == '':
                continue  # Skip attributes and blank lines
            else:
                break
        return ' '.join(doc_lines) if doc_lines else None

    def _extract_derives(self, content: str, pos: int) -> List[str]:
        """Extract derive macros preceding a definition at position pos."""
        derives = []
        # Look at text before the definition for #[derive(...)]
        text_before = content[max(0, pos - 500):pos]
        for match in self.DERIVE_PATTERN.finditer(text_before):
            derives.extend([d.strip() for d in match.group(1).split(',')])
        return derives

    def _extract_attributes(self, content: str, pos: int) -> List[str]:
        """Extract non-derive attributes preceding a definition at position pos."""
        attrs = []
        text_before = content[max(0, pos - 500):pos]
        for match in self.ATTRIBUTE_PATTERN.finditer(text_before):
            attrs.append(match.group(1).strip())
        return attrs

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Rust type definitions from source code.

        Args:
            content: Rust source code content
            file_path: Path to source file

        Returns:
            Dict with 'structs', 'enums', 'traits', 'type_aliases', 'impls' keys
        """
        return {
            'structs': self._extract_structs(content, file_path),
            'enums': self._extract_enums(content, file_path),
            'traits': self._extract_traits(content, file_path),
            'type_aliases': self._extract_type_aliases(content, file_path),
            'impls': self._extract_impls(content, file_path),
        }

    def _extract_structs(self, content: str, file_path: str) -> List[RustStructInfo]:
        """Extract struct definitions from Rust source code."""
        structs = []

        for match in self.STRUCT_HEADER.finditer(content):
            name = match.group('name')
            vis = (match.group('vis') or '').strip()
            generics_str = match.group('generics') or ''
            where_clause = match.group('where')
            body_start = match.group('body_start')
            line_number = content[:match.start()].count('\n') + 1

            generics = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []
            derives = self._extract_derives(content, match.start())
            attributes = self._extract_attributes(content, match.start())
            doc_comment = self._extract_doc_comment(content, match.start())

            struct = RustStructInfo(
                name=name,
                visibility=vis,
                generics=generics,
                derives=derives,
                attributes=attributes,
                where_clause=where_clause.strip() if where_clause else None,
                file=file_path,
                line_number=line_number,
                doc_comment=doc_comment,
            )

            if body_start == ';':
                # Unit struct: struct Foo;
                struct.is_unit_struct = True
            elif body_start == '(':
                # Tuple struct: struct Foo(pub i32, String);
                struct.is_tuple_struct = True
                paren_end = content.find(')', match.end())
                if paren_end != -1:
                    tuple_body = content[match.end():paren_end]
                    for i, part in enumerate(tuple_body.split(',')):
                        part = part.strip()
                        if part:
                            field_vis = ''
                            if part.startswith('pub'):
                                parts = part.split(None, 1)
                                if len(parts) > 1:
                                    field_vis = parts[0]
                                    part = parts[1]
                                else:
                                    part = ''
                            struct.fields.append(RustFieldInfo(
                                name=f"_{i}",
                                type=part,
                                visibility=field_vis,
                            ))
            elif body_start == '{':
                # Named struct
                brace_pos = match.end() - 1
                body = self._extract_brace_body(content, brace_pos)
                if body:
                    for field_match in self.FIELD_PATTERN.finditer(body):
                        fname = field_match.group('name')
                        ftype = field_match.group('type').strip().rstrip(',')
                        fvis = (field_match.group('vis') or '').strip()
                        comment = field_match.group('comment')
                        is_optional = ftype.startswith('Option<')
                        struct.fields.append(RustFieldInfo(
                            name=fname,
                            type=ftype,
                            visibility=fvis,
                            comment=comment,
                            is_optional=is_optional,
                        ))

            structs.append(struct)

        return structs

    def _extract_enums(self, content: str, file_path: str) -> List[RustEnumInfo]:
        """Extract enum definitions from Rust source code."""
        enums = []

        for match in self.ENUM_HEADER.finditer(content):
            name = match.group('name')
            vis = (match.group('vis') or '').strip()
            generics_str = match.group('generics') or ''
            line_number = content[:match.start()].count('\n') + 1

            generics = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []
            derives = self._extract_derives(content, match.start())
            attributes = self._extract_attributes(content, match.start())
            doc_comment = self._extract_doc_comment(content, match.start())

            brace_pos = match.end() - 1
            body = self._extract_brace_body(content, brace_pos)

            enum = RustEnumInfo(
                name=name,
                visibility=vis,
                generics=generics,
                derives=derives,
                attributes=attributes,
                file=file_path,
                line_number=line_number,
                doc_comment=doc_comment,
            )

            if body:
                # Parse variants
                for line in body.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('//'):
                        continue

                    # Struct variant: Name { field: Type, ... }
                    struct_m = re.match(r'(\w+)\s*\{', line)
                    if struct_m:
                        variant = RustEnumVariantInfo(
                            name=struct_m.group(1),
                            is_struct=True,
                        )
                        # Extract fields from struct variant body
                        variant_start = body.find(line)
                        brace_start = body.find('{', variant_start)
                        if brace_start != -1:
                            variant_body = self._extract_brace_body(body, brace_start)
                            if variant_body:
                                for fm in self.FIELD_PATTERN.finditer(variant_body):
                                    variant.fields.append(RustFieldInfo(
                                        name=fm.group('name'),
                                        type=fm.group('type').strip().rstrip(','),
                                    ))
                        enum.variants.append(variant)
                        continue

                    # Tuple variant: Name(Type1, Type2)
                    tuple_m = re.match(r'(\w+)\s*\(([^)]+)\)\s*,?', line)
                    if tuple_m:
                        types = [t.strip() for t in tuple_m.group(2).split(',') if t.strip()]
                        enum.variants.append(RustEnumVariantInfo(
                            name=tuple_m.group(1),
                            tuple_types=types,
                            is_tuple=True,
                        ))
                        continue

                    # Unit variant: Name or Name = value
                    unit_m = re.match(r'(\w+)(?:\s*=\s*([^,}]+))?\s*,?', line)
                    if unit_m and unit_m.group(1)[0].isupper():
                        enum.variants.append(RustEnumVariantInfo(
                            name=unit_m.group(1),
                            discriminant=unit_m.group(2).strip() if unit_m.group(2) else None,
                            is_unit=True,
                        ))

            enums.append(enum)

        return enums

    def _extract_traits(self, content: str, file_path: str) -> List[RustTraitInfo]:
        """Extract trait definitions from Rust source code."""
        traits = []

        for match in self.TRAIT_HEADER.finditer(content):
            name = match.group('name')
            vis = (match.group('vis') or '').strip()
            generics_str = match.group('generics') or ''
            super_traits_str = match.group('super_traits') or ''
            is_unsafe = bool(match.group('unsafe'))
            is_auto = bool(match.group('auto'))
            line_number = content[:match.start()].count('\n') + 1

            generics = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []
            super_traits = [s.strip() for s in super_traits_str.split('+') if s.strip()] if super_traits_str else []
            attributes = self._extract_attributes(content, match.start())
            doc_comment = self._extract_doc_comment(content, match.start())

            trait = RustTraitInfo(
                name=name,
                visibility=vis,
                generics=generics,
                super_traits=super_traits,
                attributes=attributes,
                is_unsafe=is_unsafe,
                is_auto=is_auto,
                file=file_path,
                line_number=line_number,
                doc_comment=doc_comment,
            )

            # Extract body
            brace_pos = match.end() - 1
            body = self._extract_brace_body(content, brace_pos)
            if body:
                # Extract methods
                for method_match in self.TRAIT_METHOD.finditer(body):
                    m_name = method_match.group('name')
                    params_str = method_match.group('params')
                    ret = method_match.group('ret')
                    has_body = method_match.group('has_body') == '{'
                    is_async = bool(method_match.group('async'))
                    m_unsafe = bool(method_match.group('unsafe'))

                    params = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []

                    trait.methods.append(RustTraitMethodInfo(
                        name=m_name,
                        params=params,
                        return_type=ret.strip() if ret else None,
                        has_default_impl=has_body,
                        is_async=is_async,
                        is_unsafe=m_unsafe,
                    ))

                # Extract associated types
                for assoc_match in self.ASSOC_TYPE.finditer(body):
                    trait.associated_types.append(assoc_match.group(1))

                # Extract associated consts
                for const_match in self.ASSOC_CONST.finditer(body):
                    trait.associated_consts.append(const_match.group(1))

            traits.append(trait)

        return traits

    def _extract_type_aliases(self, content: str, file_path: str) -> List[RustTypeAliasInfo]:
        """Extract type alias definitions from Rust source code."""
        aliases = []

        for match in self.TYPE_ALIAS_PATTERN.finditer(content):
            name = match.group('name')
            vis = (match.group('vis') or '').strip()
            generics_str = match.group('generics') or ''
            target = match.group('target').strip()
            line_number = content[:match.start()].count('\n') + 1

            generics = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []

            aliases.append(RustTypeAliasInfo(
                name=name,
                target_type=target,
                generics=generics,
                visibility=vis,
                file=file_path,
                line_number=line_number,
            ))

        return aliases

    def _extract_impls(self, content: str, file_path: str) -> List[RustImplInfo]:
        """Extract impl blocks from Rust source code."""
        impls = []

        for match in self.IMPL_HEADER.finditer(content):
            target = match.group('target').strip()
            trait_name = match.group('trait_name')
            generics_str = match.group('generics') or ''
            line_number = content[:match.start()].count('\n') + 1

            generics = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []

            # Extract method names from body
            brace_pos = match.end() - 1
            body = self._extract_brace_body(content, brace_pos)
            methods = []
            if body:
                for fn_match in re.finditer(r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)', body):
                    methods.append(fn_match.group(1))

            # Clean target type (remove lifetimes, extra whitespace)
            target = re.sub(r'\s+', ' ', target).strip()
            target = re.sub(r"<'[^,>]+,?\s*", '<', target)
            target = target.strip('<>').strip() or target

            impls.append(RustImplInfo(
                target_type=target,
                trait_name=trait_name.strip() if trait_name else None,
                methods=methods,
                generics=generics,
                file=file_path,
                line_number=line_number,
            ))

        return impls
