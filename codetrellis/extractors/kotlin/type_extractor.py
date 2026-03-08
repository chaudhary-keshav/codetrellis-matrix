"""
KotlinTypeExtractor - Extracts Kotlin type definitions.

Extracts:
- Classes (data, sealed, abstract, open, inner, value/inline)
- Objects (companion, regular)
- Interfaces
- Enum classes with entries
- Type aliases
- Annotation classes

Part of CodeTrellis v4.12 - Kotlin Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KotlinPropertyInfo:
    """Information about a Kotlin property."""
    name: str
    type: str = ""
    is_val: bool = True  # val (immutable) vs var (mutable)
    is_lateinit: bool = False
    is_override: bool = False
    annotations: List[str] = field(default_factory=list)
    default_value: Optional[str] = None


@dataclass
class KotlinClassInfo:
    """Information about a Kotlin class."""
    name: str
    kind: str = "class"  # class, data_class, sealed_class, abstract_class, value_class, inner_class, annotation_class
    primary_constructor_params: List[Dict[str, str]] = field(default_factory=list)
    properties: List[KotlinPropertyInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    companion_object: Optional[str] = None
    nested_classes: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True  # Kotlin classes are public by default
    is_sealed: bool = False
    is_data: bool = False
    is_abstract: bool = False
    is_open: bool = False
    is_inner: bool = False
    visibility: str = "public"  # public, internal, protected, private


@dataclass
class KotlinObjectInfo:
    """Information about a Kotlin object (singleton)."""
    name: str
    kind: str = "object"  # object, companion_object
    implements: List[str] = field(default_factory=list)
    extends: Optional[str] = None
    methods: List[str] = field(default_factory=list)
    properties: List[KotlinPropertyInfo] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True


@dataclass
class KotlinInterfaceInfo:
    """Information about a Kotlin interface."""
    name: str
    methods: List[str] = field(default_factory=list)
    properties: List[KotlinPropertyInfo] = field(default_factory=list)
    extends: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    is_functional: bool = False
    is_sealed: bool = False


@dataclass
class KotlinEnumInfo:
    """Information about a Kotlin enum class."""
    name: str
    entries: List[str] = field(default_factory=list)  # Enum entries (constants)
    implements: List[str] = field(default_factory=list)
    properties: List[KotlinPropertyInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True


class KotlinTypeExtractor:
    """
    Extracts Kotlin type definitions from source code.

    Handles:
    - Regular, data, sealed, abstract, open, inner, value/inline classes
    - Object declarations (singletons) and companion objects
    - Interfaces (including sealed interfaces)
    - Enum classes with entries and members
    - Annotation classes
    - Type aliases
    - Primary constructors with val/var properties
    - Generic type parameters with variance (in/out)
    """

    # Annotations before a class/interface/object
    ANNOTATION_PATTERN = re.compile(
        r'@(\w+)(?:\([^)]*\))?'
    )

    # Class declaration pattern (handles data, sealed, abstract, open, inner, value, annotation)
    # NOTE: Constructor is NOT captured inline because it may contain annotations
    # with parentheses (e.g. @Column(nullable = false)) that break [^)]* matching.
    # Constructor is extracted separately using balanced-paren logic.
    CLASS_PATTERN = re.compile(
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'(?:(public|internal|protected|private)\s+)?'
        r'(?:(data|sealed|abstract|open|inner|value|inline|annotation)\s+)*'
        r'class\s+(\w+)'
        r'(?:\s*<([^>]+)>)?',  # Generic params only; rest handled in extract()
        re.MULTILINE
    )

    # Object declaration pattern
    OBJECT_PATTERN = re.compile(
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'(?:(public|internal|protected|private)\s+)?'
        r'(?:companion\s+)?'
        r'object\s+(\w+)'
        r'(?:\s*:\s*([^\{]+?))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Companion object (no name or named)
    COMPANION_PATTERN = re.compile(
        r'companion\s+object\s*(?:(\w+)\s*)?\{',
    )

    # Interface declaration
    INTERFACE_PATTERN = re.compile(
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'(?:(public|internal|protected|private)\s+)?'
        r'(?:(sealed|fun)\s+)?'
        r'interface\s+(\w+)'
        r'(?:\s*<([^>]+)>)?'
        r'(?:\s*:\s*([^\{]+?))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Enum class declaration
    ENUM_PATTERN = re.compile(
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'(?:(public|internal|protected|private)\s+)?'
        r'enum\s+class\s+(\w+)'
        r'(?:\s*\(([^)]*)\))?'  # Primary constructor
        r'(?:\s*:\s*([^\{]+?))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Enum entry
    ENUM_ENTRY_PATTERN = re.compile(
        r'^\s+(\w+)(?:\([^)]*\))?\s*[,;]?\s*$',
        re.MULTILINE
    )

    # Type alias
    TYPE_ALIAS_PATTERN = re.compile(
        r'(?:(public|internal|protected|private)\s+)?'
        r'typealias\s+(\w+)(?:<[^>]+>)?\s*=\s*(.+)',
    )

    # Property declarations (val/var)
    PROPERTY_PATTERN = re.compile(
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'(?:override\s+)?'
        r'(?:lateinit\s+)?'
        r'(val|var)\s+(\w+)\s*:\s*([\w<>,.\s?*]+)',
    )

    # Method declaration inside body (fun keyword)
    METHOD_IN_BODY_PATTERN = re.compile(
        r'(?:override\s+)?'
        r'(?:suspend\s+)?'
        r'fun\s+(?:<[^>]+>\s*)?'
        r'(?:\w+\.)?'  # extension receiver
        r'(\w+)\s*\(',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all type definitions from Kotlin source code.

        Returns dict with keys: classes, objects, interfaces, enums, type_aliases
        """
        result = {
            'classes': [],
            'objects': [],
            'interfaces': [],
            'enums': [],
            'type_aliases': [],
        }

        if not content or not content.strip():
            return result

        # Extract classes
        for match in self.CLASS_PATTERN.finditer(content):
            # Skip enum classes — they are handled by ENUM_PATTERN
            before_match = content[max(0, match.start() - 10):match.start()]
            if 'enum ' in before_match or 'enum\n' in before_match:
                continue

            visibility = match.group(1) or 'public'
            modifiers_str = match.group(2) or ''
            name = match.group(3)
            generics_str = match.group(4) or ''

            # Extract constructor and supertypes from text after class name + generics
            after_name = content[match.end():]
            ctor_params_str = ''
            supertypes_str = ''

            # Look for primary constructor (balanced parentheses)
            rest = after_name.lstrip()
            if rest.startswith('('):
                ctor_content, end_idx = self._extract_balanced_parens(rest)
                ctor_params_str = ctor_content
                rest = rest[end_idx:].lstrip()

            # Look for supertypes (: SuperClass, Interface1, Interface2)
            if rest.startswith(':'):
                rest = rest[1:].lstrip()
                # Everything up to { or end of line
                brace_idx = rest.find('{')
                if brace_idx >= 0:
                    supertypes_str = rest[:brace_idx].strip()
                else:
                    # May end without braces (e.g., sealed class with no body)
                    nl_idx = rest.find('\n')
                    if nl_idx >= 0:
                        supertypes_str = rest[:nl_idx].strip()
                    else:
                        supertypes_str = rest.strip()

            # Determine kind
            modifiers = modifiers_str.split() if modifiers_str else []
            kind = 'class'
            is_data = 'data' in modifiers
            is_sealed = 'sealed' in modifiers
            is_abstract = 'abstract' in modifiers
            is_open = 'open' in modifiers
            is_inner = 'inner' in modifiers
            is_annotation = 'annotation' in modifiers

            if is_data:
                kind = 'data_class'
            elif is_sealed:
                kind = 'sealed_class'
            elif is_abstract:
                kind = 'abstract_class'
            elif is_annotation:
                kind = 'annotation_class'
            elif 'value' in modifiers or 'inline' in modifiers:
                kind = 'value_class'
            elif is_inner:
                kind = 'inner_class'

            # Parse primary constructor params
            ctor_params = self._parse_constructor_params(ctor_params_str)

            # Parse generic params
            generic_params = [g.strip() for g in generics_str.split(',')] if generics_str else []

            # Parse supertypes
            extends, implements = self._parse_supertypes(supertypes_str)

            # Extract annotations before the class
            annotations = self._extract_annotations_before(content, match.start())

            # Extract body — find the opening brace from after match
            body = ''
            brace_pos = content.find('{', match.end())
            if brace_pos >= 0:
                body = self._extract_body(content, brace_pos)
            properties = self._extract_properties(body)
            methods = self._extract_methods(body)

            # Check for companion object
            companion = None
            comp_match = self.COMPANION_PATTERN.search(body)
            if comp_match:
                companion = comp_match.group(1) or 'Companion'

            line_number = content[:match.start()].count('\n') + 1

            result['classes'].append(KotlinClassInfo(
                name=name,
                kind=kind,
                primary_constructor_params=ctor_params,
                properties=properties,
                methods=methods,
                extends=extends,
                implements=implements,
                annotations=annotations,
                generic_params=generic_params,
                companion_object=companion,
                file=file_path,
                line_number=line_number,
                is_exported=visibility in ('public', 'internal'),
                is_sealed=is_sealed,
                is_data=is_data,
                is_abstract=is_abstract,
                is_open=is_open,
                is_inner=is_inner,
                visibility=visibility,
            ))

        # Extract objects (skip companion objects matched inside classes)
        for match in self.OBJECT_PATTERN.finditer(content):
            full_text = content[max(0, match.start() - 20):match.start()]
            if 'companion' in full_text:
                continue  # Skip companion objects

            visibility = match.group(1) or 'public'
            name = match.group(2)
            supertypes_str = match.group(3) or ''
            extends, implements = self._parse_supertypes(supertypes_str)
            annotations = self._extract_annotations_before(content, match.start())
            body = self._extract_body(content, match.end() - 1)
            methods = self._extract_methods(body)
            properties = self._extract_properties(body)
            line_number = content[:match.start()].count('\n') + 1

            result['objects'].append(KotlinObjectInfo(
                name=name,
                kind='object',
                implements=implements,
                extends=extends,
                methods=methods,
                properties=properties,
                annotations=annotations,
                file=file_path,
                line_number=line_number,
                is_exported=visibility in ('public', 'internal'),
            ))

        # Extract interfaces
        for match in self.INTERFACE_PATTERN.finditer(content):
            visibility = match.group(1) or 'public'
            modifier = match.group(2) or ''
            name = match.group(3)
            generics_str = match.group(4) or ''
            supertypes_str = match.group(5) or ''

            _, extends_list = self._parse_supertypes(supertypes_str)
            annotations = self._extract_annotations_before(content, match.start())
            body = self._extract_body(content, match.end() - 1)
            methods = self._extract_methods(body)
            properties = self._extract_properties(body)
            generic_params = [g.strip() for g in generics_str.split(',')] if generics_str else []
            line_number = content[:match.start()].count('\n') + 1

            is_functional = modifier == 'fun'
            is_sealed = modifier == 'sealed'

            result['interfaces'].append(KotlinInterfaceInfo(
                name=name,
                methods=methods,
                properties=properties,
                extends=extends_list,
                annotations=annotations,
                generic_params=generic_params,
                file=file_path,
                line_number=line_number,
                is_exported=visibility in ('public', 'internal'),
                is_functional=is_functional,
                is_sealed=is_sealed,
            ))

        # Extract enum classes
        for match in self.ENUM_PATTERN.finditer(content):
            visibility = match.group(1) or 'public'
            name = match.group(2)
            annotations = self._extract_annotations_before(content, match.start())
            body = self._extract_body(content, match.end() - 1)
            line_number = content[:match.start()].count('\n') + 1

            # Extract enum entries (before the semicolon)
            entries = self._extract_enum_entries(body)
            # Extract methods (after the semicolon)
            methods = self._extract_methods(body)
            properties = self._extract_properties(body)

            _, implements = self._parse_supertypes(match.group(4) or '')

            result['enums'].append(KotlinEnumInfo(
                name=name,
                entries=entries,
                implements=implements,
                properties=properties,
                methods=methods,
                annotations=annotations,
                file=file_path,
                line_number=line_number,
                is_exported=visibility in ('public', 'internal'),
            ))

        # Extract type aliases
        for match in self.TYPE_ALIAS_PATTERN.finditer(content):
            result['type_aliases'].append({
                'name': match.group(2),
                'definition': match.group(3).strip(),
                'visibility': match.group(1) or 'public',
            })

        return result

    def _parse_constructor_params(self, params_str: str) -> List[Dict[str, str]]:
        """Parse primary constructor parameters."""
        params = []
        if not params_str or not params_str.strip():
            return params

        # Split on commas respecting nested angle brackets
        for param in self._split_params(params_str):
            param = param.strip()
            if not param:
                continue

            # Check for val/var prefix
            is_val = False
            is_var = False
            if param.startswith('val '):
                is_val = True
                param = param[4:]
            elif param.startswith('var '):
                is_var = True
                param = param[4:]

            # Remove annotations
            annotations = []
            while param.startswith('@'):
                ann_match = re.match(r'@(\w+)(?:\([^)]*\))?\s*', param)
                if ann_match:
                    annotations.append(ann_match.group(1))
                    param = param[ann_match.end():]
                else:
                    break

            # Split name: type
            if ':' in param:
                name, type_str = param.split(':', 1)
                name = name.strip()
                type_str = type_str.strip()
                # Handle default value
                if '=' in type_str:
                    type_str = type_str.split('=')[0].strip()
                params.append({
                    'name': name,
                    'type': type_str,
                    'is_val': is_val,
                    'is_var': is_var,
                    'annotations': annotations,
                })
            else:
                params.append({
                    'name': param.strip(),
                    'type': '',
                    'is_val': is_val,
                    'is_var': is_var,
                    'annotations': annotations,
                })

        return params

    def _parse_supertypes(self, supertypes_str: str):
        """Parse supertype list into extends (class) and implements (interfaces)."""
        extends = None
        implements = []

        if not supertypes_str or not supertypes_str.strip():
            return extends, implements

        parts = self._split_params(supertypes_str)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # If it has () it's a class constructor call
            if '(' in part:
                extends = re.match(r'([\w<>,.\s?*]+)', part)
                if extends:
                    extends = extends.group(1).strip()
            else:
                implements.append(part.strip())

        return extends, implements

    def _extract_annotations_before(self, content: str, pos: int) -> List[str]:
        """Extract annotations that appear before a declaration."""
        annotations = []
        # Look at the 500 chars before the position
        before = content[max(0, pos - 500):pos]
        # Walk backwards through lines until we hit a non-annotation line
        lines = before.split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('@'):
                ann_match = re.match(r'@(\w+)', line)
                if ann_match:
                    annotations.insert(0, ann_match.group(1))
            elif not line:
                continue
            else:
                break
        return annotations

    def _extract_balanced_parens(self, text: str) -> tuple:
        """
        Extract content inside balanced parentheses, handling nested parens.
        
        Args:
            text: String starting with '('
            
        Returns:
            Tuple of (inner_content, end_index_after_closing_paren)
        """
        if not text or text[0] != '(':
            return ('', 0)
        
        depth = 0
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    return (text[1:i], i + 1)
            elif ch == '"':
                # Skip strings
                i += 1
                while i < len(text) and text[i] != '"':
                    if text[i] == '\\':
                        i += 1
                    i += 1
            i += 1
        # Unbalanced — return what we have
        return (text[1:], len(text))

    def _extract_body(self, content: str, brace_pos: int) -> str:
        """Extract the body of a class/object/interface starting from the opening brace."""
        if brace_pos >= len(content) or content[brace_pos] != '{':
            return ""

        depth = 0
        i = brace_pos
        while i < len(content):
            ch = content[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[brace_pos + 1:i]
            elif ch == '"':
                # Skip strings
                i += 1
                while i < len(content) and content[i] != '"':
                    if content[i] == '\\':
                        i += 1
                    i += 1
            elif ch == '/' and i + 1 < len(content):
                if content[i + 1] == '/':
                    # Skip line comment
                    while i < len(content) and content[i] != '\n':
                        i += 1
                elif content[i + 1] == '*':
                    # Skip block comment
                    i += 2
                    while i < len(content) - 1 and not (content[i] == '*' and content[i + 1] == '/'):
                        i += 1
                    i += 1
            i += 1
        return content[brace_pos + 1:]

    def _extract_properties(self, body: str) -> List[KotlinPropertyInfo]:
        """Extract property declarations from a body."""
        properties = []
        for match in self.PROPERTY_PATTERN.finditer(body):
            val_or_var = match.group(1)
            name = match.group(2)
            type_str = match.group(3).strip()
            is_override = 'override' in body[max(0, match.start() - 30):match.start()]
            is_lateinit = 'lateinit' in body[max(0, match.start() - 30):match.start()]
            annotations = []
            before = body[max(0, match.start() - 100):match.start()]
            for ann in self.ANNOTATION_PATTERN.finditer(before):
                annotations.append(ann.group(1))

            properties.append(KotlinPropertyInfo(
                name=name,
                type=type_str,
                is_val=val_or_var == 'val',
                is_lateinit=is_lateinit,
                is_override=is_override,
                annotations=annotations,
            ))
        return properties

    def _extract_methods(self, body: str) -> List[str]:
        """Extract method names from a body."""
        methods = []
        for match in self.METHOD_IN_BODY_PATTERN.finditer(body):
            name = match.group(1)
            if name not in methods:
                methods.append(name)
        return methods

    def _extract_enum_entries(self, body: str) -> List[str]:
        """Extract enum entries from an enum class body."""
        entries = []
        # Enum entries are before the first semicolon or before methods/properties
        semicolon_pos = body.find(';')
        # Also check for first 'fun ' or 'val ' or 'var ' as delimiter
        fun_pos = body.find('\n    fun ')
        if fun_pos < 0:
            fun_pos = body.find('\nfun ')
        delimiter = len(body)
        if semicolon_pos >= 0:
            delimiter = min(delimiter, semicolon_pos)
        if fun_pos >= 0:
            delimiter = min(delimiter, fun_pos)

        entry_section = body[:delimiter]

        # Skip keywords
        skip_words = {'val', 'var', 'fun', 'override', 'companion', 'object',
                      'class', 'interface', 'enum', 'sealed', 'data', 'abstract',
                      'private', 'protected', 'internal', 'public', 'open', 'final',
                      'suspend', 'inline', 'operator', 'infix', 'tailrec'}

        # Try multi-line first: each entry on its own line
        for match in re.finditer(r'^\s*(\w+)(?:\s*\([^)]*\))?\s*[,;]?\s*$', entry_section, re.MULTILINE):
            name = match.group(1)
            if name not in skip_words:
                entries.append(name)

        # If no entries found, try comma-separated on single/few lines
        if not entries:
            # Extract identifiers that look like enum entries (UPPER_CASE or PascalCase)
            for match in re.finditer(r'\b([A-Z]\w*)\b', entry_section):
                name = match.group(1)
                if name not in skip_words and name not in entries:
                    entries.append(name)

        return entries

    def _split_params(self, text: str) -> List[str]:
        """Split parameters respecting nested angle brackets and parentheses."""
        parts = []
        depth = 0
        current = []
        for ch in text:
            if ch in ('<', '('):
                depth += 1
                current.append(ch)
            elif ch in ('>', ')'):
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
