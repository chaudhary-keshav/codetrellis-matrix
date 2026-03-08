"""
Scala Type Extractor for CodeTrellis

Extracts type definitions from Scala source code:
- Classes (regular, abstract, case, value, sealed)
- Traits (regular, sealed, transparent Scala 3)
- Objects (companion, standalone, package objects)
- Enums (Scala 3 enum, Scala 2 sealed trait pattern)
- Type aliases and opaque types (Scala 3)
- Given/using instances (Scala 3)
- Extension methods (Scala 3)

Supports: Scala 2.10 through 3.5+
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ScalaFieldInfo:
    """Information about a Scala field/parameter."""
    name: str
    type: str = ""
    is_val: bool = True
    is_var: bool = False
    is_lazy: bool = False
    is_override: bool = False
    is_private: bool = False
    is_protected: bool = False
    is_implicit: bool = False
    default_value: Optional[str] = None
    annotations: List[str] = field(default_factory=list)
    comment: Optional[str] = None


@dataclass
class ScalaClassInfo:
    """Information about a Scala class."""
    name: str
    kind: str = "class"  # class, abstract_class, case_class, value_class
    fields: List[ScalaFieldInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    extends: Optional[str] = None
    mixins: List[str] = field(default_factory=list)  # with Trait1 with Trait2
    annotations: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    companion_object: Optional[str] = None
    nested_types: List[str] = field(default_factory=list)
    is_sealed: bool = False
    is_final: bool = False
    is_abstract: bool = False
    is_case: bool = False
    is_value_class: bool = False  # extends AnyVal
    is_implicit: bool = False  # implicit class
    is_open: bool = False  # Scala 3 open class
    visibility: str = "public"
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None
    constructor_params: List[ScalaFieldInfo] = field(default_factory=list)
    self_type: Optional[str] = None  # self: SomeType =>


@dataclass
class ScalaTraitInfo:
    """Information about a Scala trait."""
    name: str
    methods: List[str] = field(default_factory=list)
    abstract_members: List[str] = field(default_factory=list)
    extends: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    is_sealed: bool = False
    is_transparent: bool = False  # Scala 3 transparent trait
    visibility: str = "public"
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None
    self_type: Optional[str] = None


@dataclass
class ScalaObjectInfo:
    """Information about a Scala object (singleton)."""
    name: str
    kind: str = "object"  # object, case_object, package_object
    extends: Optional[str] = None
    mixins: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    fields: List[ScalaFieldInfo] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    is_case: bool = False
    is_package_object: bool = False
    is_companion: bool = False
    visibility: str = "public"
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class ScalaEnumInfo:
    """Information about a Scala enum (Scala 3) or sealed hierarchy."""
    name: str
    cases: List[str] = field(default_factory=list)
    extends: Optional[str] = None
    generic_params: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    is_scala3_enum: bool = False
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class ScalaTypeAliasInfo:
    """Information about a Scala type alias or opaque type."""
    name: str
    target_type: str = ""
    generic_params: List[str] = field(default_factory=list)
    is_opaque: bool = False  # Scala 3 opaque type
    visibility: str = "public"
    file: str = ""
    line_number: int = 0


@dataclass
class ScalaGivenInfo:
    """Information about a Scala 3 given/using instance."""
    name: str
    type: str = ""
    is_given: bool = True
    is_using: bool = False
    file: str = ""
    line_number: int = 0


class ScalaTypeExtractor:
    """
    Extracts type definitions from Scala source code.

    Supports Scala 2.10 through Scala 3.5+:
    - Regular and abstract classes
    - Case classes with parameter lists
    - Value classes (extends AnyVal)
    - Traits (sealed, transparent)
    - Objects (companion, package)
    - Scala 3 enums
    - Type aliases and opaque types
    - Given/using instances (Scala 3)
    """

    # ── Patterns ────────────────────────────────────────────────
    CLASS_PATTERN = re.compile(
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?[\s\n]*)+)\s*)?'
        r'(?P<modifiers>(?:(?:sealed|final|abstract|implicit|open|private|protected|override|lazy)\s+)*)'
        r'(?P<case>case\s+)?class\s+'
        r'(?P<name>\w+)'
        r'(?:\s*\[(?P<generics>[^\]]+)\])?'
        r'(?:\s*\((?P<params>[^)]*(?:\)[\s\n]*\([^)]*)*)\))?'
        r'(?:\s+extends\s+(?P<extends>[^\s{]+(?:\[[^\]]*\])?))?'
        r'(?:\s+with\s+(?P<mixins>[^{]+?))?'
        r'(?:\s*\{)?',
        re.MULTILINE
    )

    TRAIT_PATTERN = re.compile(
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?[\s\n]*)+)\s*)?'
        r'(?P<modifiers>(?:(?:sealed|transparent|private|protected)\s+)*)'
        r'trait\s+'
        r'(?P<name>\w+)'
        r'(?:\s*\[(?P<generics>[^\]]+)\])?'
        r'(?:\s+extends\s+(?P<extends>[^\s{]+(?:\[[^\]]*\])?))?'
        r'(?:\s+with\s+(?P<mixins>[^{]+?))?'
        r'(?:\s*\{)?',
        re.MULTILINE
    )

    OBJECT_PATTERN = re.compile(
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?[\s\n]*)+)\s*)?'
        r'(?P<case>case\s+)?object\s+'
        r'(?P<name>\w+)'
        r'(?:\s+extends\s+(?P<extends>[^\s{]+(?:\[[^\]]*\])?))?'
        r'(?:\s+with\s+(?P<mixins>[^{]+?))?'
        r'(?:\s*\{)?',
        re.MULTILINE
    )

    PACKAGE_OBJECT_PATTERN = re.compile(
        r'package\s+object\s+(?P<name>\w+)'
        r'(?:\s+extends\s+(?P<extends>[^\s{]+))?'
        r'(?:\s+with\s+(?P<mixins>[^{]+?))?',
        re.MULTILINE
    )

    # Scala 3 enum
    ENUM_PATTERN = re.compile(
        r'(?:(?P<modifiers>(?:(?:sealed|private|protected)\s+)*))?'
        r'enum\s+(?P<name>\w+)'
        r'(?:\s*\[(?P<generics>[^\]]+)\])?'
        r'(?:\s+extends\s+(?P<extends>[^\s{]+))?',
        re.MULTILINE
    )

    ENUM_CASE_PATTERN = re.compile(
        r'case\s+(?P<name>\w+)(?:\s*\((?P<params>[^)]*)\))?',
        re.MULTILINE
    )

    TYPE_ALIAS_PATTERN = re.compile(
        r'(?P<opaque>opaque\s+)?type\s+(?P<name>\w+)'
        r'(?:\s*\[(?P<generics>[^\]]+)\])?\s*=\s*(?P<target>[^\n]+)',
        re.MULTILINE
    )

    GIVEN_PATTERN = re.compile(
        r'given\s+(?:(?P<name>\w+)\s*:\s*)?(?P<type>[^\s=]+(?:\[[^\]]*\])?)'
        r'(?:\s+with\s+|\s*=)',
        re.MULTILINE
    )

    SELF_TYPE_PATTERN = re.compile(
        r'self\s*:\s*([^=]+?)\s*=>',
        re.MULTILINE
    )

    DOC_COMMENT_PATTERN = re.compile(
        r'/\*\*\s*(.*?)\s*\*/',
        re.DOTALL
    )

    def __init__(self):
        """Initialize the Scala type extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all type definitions from Scala source code.

        Args:
            content: Scala source code
            file_path: Path to the source file

        Returns:
            Dictionary with keys: classes, traits, objects, enums, type_aliases, givens
        """
        result = {
            'classes': [],
            'traits': [],
            'objects': [],
            'enums': [],
            'type_aliases': [],
            'givens': [],
        }

        # Extract doc comments for attaching to types
        doc_comments = self._extract_doc_comments(content)

        result['classes'] = self._extract_classes(content, file_path, doc_comments)
        result['traits'] = self._extract_traits(content, file_path, doc_comments)
        result['objects'] = self._extract_objects(content, file_path, doc_comments)
        result['enums'] = self._extract_enums(content, file_path, doc_comments)
        result['type_aliases'] = self._extract_type_aliases(content, file_path)
        result['givens'] = self._extract_givens(content, file_path)

        return result

    def _extract_doc_comments(self, content: str) -> Dict[int, str]:
        """Extract Scaladoc comments mapped by end line."""
        comments = {}
        for match in self.DOC_COMMENT_PATTERN.finditer(content):
            end_line = content[:match.end()].count('\n') + 1
            doc = match.group(1).strip()
            # Clean up * prefixes
            lines = []
            for line in doc.split('\n'):
                cleaned = re.sub(r'^\s*\*\s?', '', line).strip()
                if cleaned:
                    lines.append(cleaned)
            comments[end_line] = ' '.join(lines)[:300]
        return comments

    def _get_doc_for_line(self, doc_comments: Dict[int, str], line: int) -> Optional[str]:
        """Find the doc comment that immediately precedes a given line."""
        # Check the line immediately before
        for offset in range(1, 5):
            if (line - offset) in doc_comments:
                return doc_comments[line - offset]
        return None

    def _extract_classes(self, content: str, file_path: str,
                         doc_comments: Dict[int, str]) -> List[ScalaClassInfo]:
        """Extract class definitions."""
        classes = []
        for match in self.CLASS_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            if not name or name in ('extends', 'with', 'new'):
                continue

            modifiers = match.group('modifiers') or ''
            is_case = bool(match.group('case'))
            extends_raw = match.group('extends') or ''
            mixins_raw = match.group('mixins') or ''
            generics_raw = match.group('generics') or ''
            annotations_raw = match.group('annotations') or ''
            params_raw = match.group('params') or ''

            # Determine kind
            if is_case:
                kind = 'case_class'
            elif 'abstract' in modifiers:
                kind = 'abstract_class'
            else:
                kind = 'class'

            # Parse extends - check for AnyVal (value class)
            is_value_class = extends_raw.strip() == 'AnyVal'

            # Parse mixins
            mixins = [m.strip() for m in re.split(r'\s+with\s+', mixins_raw) if m.strip()] if mixins_raw else []

            # Parse generics
            generics = [g.strip() for g in generics_raw.split(',') if g.strip()] if generics_raw else []

            # Parse annotations
            annotations = re.findall(r'@(\w+(?:\([^)]*\))?)', annotations_raw)

            # Parse constructor parameters
            constructor_params = self._parse_params(params_raw) if params_raw else []

            cls = ScalaClassInfo(
                name=name,
                kind=kind,
                extends=extends_raw.strip() if extends_raw else None,
                mixins=mixins,
                generic_params=generics,
                annotations=annotations,
                is_sealed='sealed' in modifiers,
                is_final='final' in modifiers,
                is_abstract='abstract' in modifiers,
                is_case=is_case,
                is_value_class=is_value_class,
                is_implicit='implicit' in modifiers,
                is_open='open' in modifiers,
                visibility=self._get_visibility(modifiers),
                constructor_params=constructor_params,
                file=file_path,
                line_number=line_number,
                doc_comment=self._get_doc_for_line(doc_comments, line_number),
            )
            classes.append(cls)

        return classes

    def _extract_traits(self, content: str, file_path: str,
                        doc_comments: Dict[int, str]) -> List[ScalaTraitInfo]:
        """Extract trait definitions."""
        traits = []
        for match in self.TRAIT_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            if not name:
                continue

            modifiers = match.group('modifiers') or ''
            extends_raw = match.group('extends') or ''
            mixins_raw = match.group('mixins') or ''
            generics_raw = match.group('generics') or ''
            annotations_raw = match.group('annotations') or ''

            extends_list = []
            if extends_raw.strip():
                extends_list.append(extends_raw.strip())
            if mixins_raw:
                extends_list.extend([m.strip() for m in re.split(r'\s+with\s+', mixins_raw) if m.strip()])

            generics = [g.strip() for g in generics_raw.split(',') if g.strip()] if generics_raw else []
            annotations = re.findall(r'@(\w+(?:\([^)]*\))?)', annotations_raw)

            trait = ScalaTraitInfo(
                name=name,
                extends=extends_list,
                generic_params=generics,
                annotations=annotations,
                is_sealed='sealed' in modifiers,
                is_transparent='transparent' in modifiers,
                visibility=self._get_visibility(modifiers),
                file=file_path,
                line_number=line_number,
                doc_comment=self._get_doc_for_line(doc_comments, line_number),
            )
            traits.append(trait)

        return traits

    def _extract_objects(self, content: str, file_path: str,
                         doc_comments: Dict[int, str]) -> List[ScalaObjectInfo]:
        """Extract object definitions (singletons, companions, package objects)."""
        objects = []

        # Package objects
        for match in self.PACKAGE_OBJECT_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            extends_raw = match.group('extends') or ''
            mixins_raw = match.group('mixins') or ''

            mixins = [m.strip() for m in re.split(r'\s+with\s+', mixins_raw) if m.strip()] if mixins_raw else []

            obj = ScalaObjectInfo(
                name=name,
                kind='package_object',
                extends=extends_raw.strip() if extends_raw else None,
                mixins=mixins,
                is_package_object=True,
                file=file_path,
                line_number=line_number,
                doc_comment=self._get_doc_for_line(doc_comments, line_number),
            )
            objects.append(obj)

        # Regular objects
        for match in self.OBJECT_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            if not name:
                continue

            is_case = bool(match.group('case'))
            extends_raw = match.group('extends') or ''
            mixins_raw = match.group('mixins') or ''
            annotations_raw = match.group('annotations') or ''

            mixins = [m.strip() for m in re.split(r'\s+with\s+', mixins_raw) if m.strip()] if mixins_raw else []
            annotations = re.findall(r'@(\w+(?:\([^)]*\))?)', annotations_raw)

            obj = ScalaObjectInfo(
                name=name,
                kind='case_object' if is_case else 'object',
                extends=extends_raw.strip() if extends_raw else None,
                mixins=mixins,
                annotations=annotations,
                is_case=is_case,
                file=file_path,
                line_number=line_number,
                doc_comment=self._get_doc_for_line(doc_comments, line_number),
            )
            objects.append(obj)

        return objects

    def _extract_enums(self, content: str, file_path: str,
                       doc_comments: Dict[int, str]) -> List[ScalaEnumInfo]:
        """Extract Scala 3 enum definitions."""
        enums = []
        for match in self.ENUM_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            if not name:
                continue

            generics_raw = match.group('generics') or ''
            generics = [g.strip() for g in generics_raw.split(',') if g.strip()] if generics_raw else []
            extends_raw = match.group('extends') or ''

            # Extract enum body for cases
            body = self._extract_brace_body(content, match.end())
            cases = []
            if body:
                for case_match in self.ENUM_CASE_PATTERN.finditer(body):
                    cases.append(case_match.group('name'))

            enum = ScalaEnumInfo(
                name=name,
                cases=cases,
                extends=extends_raw.strip() if extends_raw else None,
                generic_params=generics,
                is_scala3_enum=True,
                file=file_path,
                line_number=line_number,
                doc_comment=self._get_doc_for_line(doc_comments, line_number),
            )
            enums.append(enum)

        return enums

    def _extract_type_aliases(self, content: str, file_path: str) -> List[ScalaTypeAliasInfo]:
        """Extract type aliases and opaque types."""
        aliases = []
        for match in self.TYPE_ALIAS_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            target = match.group('target').strip()
            is_opaque = bool(match.group('opaque'))
            generics_raw = match.group('generics') or ''
            generics = [g.strip() for g in generics_raw.split(',') if g.strip()] if generics_raw else []

            alias = ScalaTypeAliasInfo(
                name=name,
                target_type=target,
                generic_params=generics,
                is_opaque=is_opaque,
                file=file_path,
                line_number=line_number,
            )
            aliases.append(alias)

        return aliases

    def _extract_givens(self, content: str, file_path: str) -> List[ScalaGivenInfo]:
        """Extract Scala 3 given instances."""
        givens = []
        for match in self.GIVEN_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name') or f"given_{match.group('type')}"
            given_type = match.group('type')

            given = ScalaGivenInfo(
                name=name,
                type=given_type,
                is_given=True,
                file=file_path,
                line_number=line_number,
            )
            givens.append(given)

        return givens

    def _parse_params(self, params_raw: str) -> List[ScalaFieldInfo]:
        """Parse constructor/method parameters."""
        params = []
        if not params_raw.strip():
            return params

        # Handle multiple parameter lists (curried)
        all_params = params_raw.replace(')', '').replace('(', ',')
        for param_str in all_params.split(','):
            param_str = param_str.strip()
            if not param_str:
                continue

            # Parse modifiers
            is_val = 'val ' in param_str
            is_var = 'var ' in param_str
            is_implicit = 'implicit ' in param_str or 'using ' in param_str
            is_override = 'override ' in param_str
            is_private = 'private ' in param_str
            is_lazy = 'lazy ' in param_str

            # Clean modifiers
            cleaned = re.sub(
                r'\b(val|var|implicit|using|override|private|protected|lazy)\b\s*',
                '', param_str
            ).strip()

            # Extract annotations
            annotations = re.findall(r'@(\w+)', cleaned)
            cleaned = re.sub(r'@\w+\s*', '', cleaned).strip()

            # Parse name: type = default
            default_value = None
            if '=' in cleaned:
                parts = cleaned.split('=', 1)
                cleaned = parts[0].strip()
                default_value = parts[1].strip()

            if ':' in cleaned:
                name_part, type_part = cleaned.split(':', 1)
                name = name_part.strip()
                ptype = type_part.strip()
            else:
                name = cleaned
                ptype = ""

            if name and name not in ('val', 'var', 'implicit', 'using'):
                params.append(ScalaFieldInfo(
                    name=name,
                    type=ptype,
                    is_val=is_val,
                    is_var=is_var,
                    is_implicit=is_implicit,
                    is_override=is_override,
                    is_private=is_private,
                    is_lazy=is_lazy,
                    default_value=default_value,
                    annotations=annotations,
                ))

        return params

    def _get_visibility(self, modifiers: str) -> str:
        """Determine visibility from modifiers string."""
        if 'private' in modifiers:
            return 'private'
        if 'protected' in modifiers:
            return 'protected'
        return 'public'

    def _extract_brace_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content within braces, handling nesting."""
        # Find first opening brace after start_pos
        idx = start_pos
        while idx < len(content) and content[idx] != '{':
            if content[idx] == '\n':
                # No opening brace on same line, might be braceless
                return None
            idx += 1

        if idx >= len(content):
            return None

        depth = 1
        start = idx + 1
        idx += 1
        in_string = False
        string_char = None
        in_comment = False
        in_block_comment = False

        while idx < len(content) and depth > 0:
            ch = content[idx]

            if in_block_comment:
                if ch == '*' and idx + 1 < len(content) and content[idx + 1] == '/':
                    in_block_comment = False
                    idx += 1
            elif in_comment:
                if ch == '\n':
                    in_comment = False
            elif in_string:
                if ch == '\\':
                    idx += 1
                elif ch == string_char:
                    in_string = False
            else:
                if ch == '/' and idx + 1 < len(content):
                    if content[idx + 1] == '/':
                        in_comment = True
                    elif content[idx + 1] == '*':
                        in_block_comment = True
                elif ch in ('"', '\''):
                    in_string = True
                    string_char = ch
                elif ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1

            idx += 1

        if depth == 0:
            return content[start:idx - 1]
        return None
