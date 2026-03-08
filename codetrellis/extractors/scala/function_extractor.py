"""
ScalaFunctionExtractor - Extracts Scala method, function, and val definitions.

This extractor parses Scala source code and extracts:
- def methods (instance, override, abstract)
- val/lazy val function-like definitions
- Extension methods (Scala 3)
- Implicit defs and conversions (Scala 2)
- Higher-order functions
- Curried parameters
- Pattern matching extractors (unapply)
- Partial functions
- By-name parameters
- Macro definitions

Supports Scala 2.10 through Scala 3.5+ features including:
- Extension methods (Scala 3)
- Inline/transparent inline (Scala 3)
- Context functions (Scala 3)
- Polymorphic function types (Scala 3)

Part of CodeTrellis v4.25 - Scala Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ScalaParameterInfo:
    """Information about a Scala method parameter."""
    name: str
    type: str = ""
    kind: str = "positional"  # positional, by_name, repeated, implicit, using, context
    default_value: Optional[str] = None
    is_implicit: bool = False
    is_using: bool = False
    is_by_name: bool = False  # => Type
    is_repeated: bool = False  # Type*
    annotations: List[str] = field(default_factory=list)


@dataclass
class ScalaMethodInfo:
    """Information about a Scala method/function."""
    name: str
    parameters: List[ScalaParameterInfo] = field(default_factory=list)
    parameter_lists: int = 1  # Number of curried parameter lists
    return_type: Optional[str] = None
    visibility: str = "public"  # public, private, protected, private[scope]
    file: str = ""
    line_number: int = 0
    is_override: bool = False
    is_abstract: bool = False
    is_final: bool = False
    is_implicit: bool = False  # implicit def (Scala 2)
    is_inline: bool = False  # inline def (Scala 3)
    is_transparent: bool = False  # transparent inline (Scala 3)
    is_extension: bool = False  # extension method (Scala 3)
    is_macro: bool = False  # macro def
    is_lazy: bool = False
    is_tailrec: bool = False  # @tailrec
    is_extractor: bool = False  # unapply/unapplySeq
    generic_params: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    owner_class: Optional[str] = None
    doc_comment: Optional[str] = None
    throws: List[str] = field(default_factory=list)  # @throws annotations


class ScalaFunctionExtractor:
    """
    Extracts Scala method and function definitions from source code.

    Handles:
    - def methods with all modifier combinations
    - val/lazy val with function types
    - Extension methods (Scala 3)
    - Implicit definitions and conversions (Scala 2)
    - Inline/transparent inline (Scala 3)
    - Multiple parameter lists (currying)
    - By-name parameters (=> Type)
    - Varargs (Type*)
    - Type parameters with bounds
    - Pattern matching extractors (unapply/unapplySeq)
    - @tailrec, @throws annotations
    - Abstract methods in traits
    """

    # Method definition pattern
    METHOD_PATTERN = re.compile(
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?[\s\n]*)+)\s*)?'
        r'(?P<modifiers>(?:(?:override|final|abstract|implicit|inline|transparent|private|protected|lazy)\s+)*)'
        r'def\s+(?P<name>\w+)'
        r'(?:\s*\[(?P<generics>[^\]]+)\])?'
        r'(?P<param_lists>(?:\s*\([^)]*\))+)?'
        r'(?:\s*:\s*(?P<return_type>[^\s={]+(?:\[[^\]]*\])?))?',
        re.MULTILINE
    )

    # Extension method (Scala 3)
    EXTENSION_PATTERN = re.compile(
        r'extension\s*(?:\[(?P<generics>[^\]]+)\])?\s*\((?P<self_param>[^)]+)\)\s*',
        re.MULTILINE
    )

    # Extension single-method shorthand
    EXTENSION_DEF_PATTERN = re.compile(
        r'extension\s*(?:\[[^\]]+\])?\s*\([^)]+\)\s+'
        r'def\s+(?P<name>\w+)'
        r'(?:\s*\[(?P<generics>[^\]]+)\])?'
        r'(?:\s*\((?P<params>[^)]*)\))?'
        r'(?:\s*:\s*(?P<return_type>[^\s={]+(?:\[[^\]]*\])?))?',
        re.MULTILINE
    )

    # Val/var function definitions
    VAL_FUNC_PATTERN = re.compile(
        r'(?P<modifiers>(?:(?:override|final|private|protected|lazy|implicit)\s+)*)'
        r'(?P<kind>val|var)\s+(?P<name>\w+)\s*:\s*'
        r'(?P<type>(?:\([^)]*\)\s*=>|[\w\[\],\s]+\s*=>)\s*[^\s=]+(?:\[[^\]]*\])?)',
        re.MULTILINE
    )

    # Implicit class pattern (Scala 2)
    IMPLICIT_CLASS_PATTERN = re.compile(
        r'implicit\s+class\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Partial function
    PARTIAL_FUNC_PATTERN = re.compile(
        r'(?P<name>\w+)\s*:\s*PartialFunction\[',
        re.MULTILINE
    )

    DOC_COMMENT_PATTERN = re.compile(
        r'/\*\*\s*(.*?)\s*\*/',
        re.DOTALL
    )

    def __init__(self):
        """Initialize the Scala function extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all function/method definitions from Scala source code.

        Args:
            content: Scala source code
            file_path: Path to the source file

        Returns:
            Dictionary with keys: methods, extension_methods, val_functions
        """
        result = {
            'methods': [],
            'extension_methods': [],
            'val_functions': [],
        }

        doc_comments = self._extract_doc_comments(content)

        result['methods'] = self._extract_methods(content, file_path, doc_comments)
        result['extension_methods'] = self._extract_extension_methods(content, file_path, doc_comments)
        result['val_functions'] = self._extract_val_functions(content, file_path)

        return result

    def _extract_doc_comments(self, content: str) -> Dict[int, str]:
        """Extract Scaladoc comments mapped by end line."""
        comments = {}
        for match in self.DOC_COMMENT_PATTERN.finditer(content):
            end_line = content[:match.end()].count('\n') + 1
            doc = match.group(1).strip()
            lines = []
            for line in doc.split('\n'):
                cleaned = re.sub(r'^\s*\*\s?', '', line).strip()
                if cleaned:
                    lines.append(cleaned)
            comments[end_line] = ' '.join(lines)[:300]
        return comments

    def _get_doc_for_line(self, doc_comments: Dict[int, str], line: int) -> Optional[str]:
        """Find doc comment preceding a given line."""
        for offset in range(1, 5):
            if (line - offset) in doc_comments:
                return doc_comments[line - offset]
        return None

    def _extract_methods(self, content: str, file_path: str,
                         doc_comments: Dict[int, str]) -> List[ScalaMethodInfo]:
        """Extract def method definitions."""
        methods = []
        for match in self.METHOD_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            if not name:
                continue

            modifiers = match.group('modifiers') or ''
            annotations_raw = match.group('annotations') or ''
            generics_raw = match.group('generics') or ''
            param_lists_raw = match.group('param_lists') or ''
            return_type = match.group('return_type')

            # Parse annotations
            annotations = re.findall(r'@(\w+(?:\([^)]*\))?)', annotations_raw)

            # Detect special annotations
            is_tailrec = any('tailrec' in a for a in annotations)
            throws = [a for a in annotations if a.startswith('throws')]

            # Parse generic params
            generics = [g.strip() for g in generics_raw.split(',') if g.strip()] if generics_raw else []

            # Parse parameter lists (detect currying)
            all_params = []
            param_list_count = 0
            if param_lists_raw:
                param_sections = re.findall(r'\(([^)]*)\)', param_lists_raw)
                param_list_count = len(param_sections)
                for section in param_sections:
                    all_params.extend(self._parse_params(section))
            param_list_count = max(param_list_count, 1)

            method = ScalaMethodInfo(
                name=name,
                parameters=all_params,
                parameter_lists=param_list_count,
                return_type=return_type.strip() if return_type else None,
                visibility=self._get_visibility(modifiers),
                is_override='override' in modifiers,
                is_abstract='abstract' in modifiers,
                is_final='final' in modifiers,
                is_implicit='implicit' in modifiers,
                is_inline='inline' in modifiers,
                is_transparent='transparent' in modifiers,
                is_macro='macro' in modifiers,
                is_lazy='lazy' in modifiers,
                is_tailrec=is_tailrec,
                is_extractor=name in ('unapply', 'unapplySeq'),
                generic_params=generics,
                annotations=annotations,
                throws=throws,
                file=file_path,
                line_number=line_number,
                doc_comment=self._get_doc_for_line(doc_comments, line_number),
            )
            methods.append(method)

        return methods

    def _extract_extension_methods(self, content: str, file_path: str,
                                   doc_comments: Dict[int, str]) -> List[ScalaMethodInfo]:
        """Extract Scala 3 extension methods."""
        methods = []

        # Single-method extension
        for match in self.EXTENSION_DEF_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            params_raw = match.group('params') or ''
            return_type = match.group('return_type')
            generics_raw = match.group('generics') or ''

            params = self._parse_params(params_raw) if params_raw else []
            generics = [g.strip() for g in generics_raw.split(',') if g.strip()] if generics_raw else []

            method = ScalaMethodInfo(
                name=name,
                parameters=params,
                return_type=return_type.strip() if return_type else None,
                is_extension=True,
                generic_params=generics,
                file=file_path,
                line_number=line_number,
                doc_comment=self._get_doc_for_line(doc_comments, line_number),
            )
            methods.append(method)

        # Multi-method extension block
        for match in self.EXTENSION_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            body_start = match.end()

            # Find the body of the extension block
            body = self._extract_brace_body(content, body_start)
            if body:
                for def_match in re.finditer(
                    r'def\s+(?P<name>\w+)'
                    r'(?:\s*\[(?P<generics>[^\]]+)\])?'
                    r'(?:\s*\((?P<params>[^)]*)\))?'
                    r'(?:\s*:\s*(?P<return_type>[^\s={]+(?:\[[^\]]*\])?))?',
                    body
                ):
                    m_name = def_match.group('name')
                    m_params = self._parse_params(def_match.group('params') or '')
                    m_return = def_match.group('return_type')
                    m_generics_raw = def_match.group('generics') or ''
                    m_generics = [g.strip() for g in m_generics_raw.split(',') if g.strip()] if m_generics_raw else []

                    method = ScalaMethodInfo(
                        name=m_name,
                        parameters=m_params,
                        return_type=m_return.strip() if m_return else None,
                        is_extension=True,
                        generic_params=m_generics,
                        file=file_path,
                        line_number=line_number + body[:def_match.start()].count('\n'),
                        doc_comment=self._get_doc_for_line(doc_comments, line_number),
                    )
                    methods.append(method)

        return methods

    def _extract_val_functions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract val/var definitions with function types."""
        functions = []
        for match in self.VAL_FUNC_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            func_type = match.group('type').strip()
            kind = match.group('kind')
            modifiers = match.group('modifiers') or ''

            functions.append({
                'name': name,
                'type': func_type,
                'kind': kind,
                'is_lazy': 'lazy' in modifiers,
                'visibility': self._get_visibility(modifiers),
                'file': file_path,
                'line_number': line_number,
            })

        return functions

    def _parse_params(self, params_raw: str) -> List[ScalaParameterInfo]:
        """Parse method parameter string into ScalaParameterInfo list."""
        params = []
        if not params_raw.strip():
            return params

        # Detect implicit/using prefix for entire list
        list_implicit = False
        list_using = False
        stripped = params_raw.strip()
        if stripped.startswith('implicit '):
            list_implicit = True
            stripped = stripped[9:]
        elif stripped.startswith('using '):
            list_using = True
            stripped = stripped[6:]

        for param_str in self._split_params(stripped):
            param_str = param_str.strip()
            if not param_str:
                continue

            # Per-parameter modifiers
            is_implicit = list_implicit or 'implicit ' in param_str
            is_using = list_using or 'using ' in param_str

            # Remove modifiers
            cleaned = re.sub(r'\b(implicit|using)\b\s*', '', param_str).strip()

            # Extract annotations
            annotations = re.findall(r'@(\w+)', cleaned)
            cleaned = re.sub(r'@\w+\s*', '', cleaned).strip()

            # Default value
            default_value = None
            if '=' in cleaned:
                parts = cleaned.split('=', 1)
                cleaned = parts[0].strip()
                default_value = parts[1].strip()

            # Name: Type
            is_by_name = False
            is_repeated = False
            ptype = ""
            if ':' in cleaned:
                name_part, type_part = cleaned.split(':', 1)
                name = name_part.strip()
                ptype = type_part.strip()

                # By-name parameter: => Type
                if ptype.startswith('=>'):
                    is_by_name = True
                    ptype = ptype[2:].strip()

                # Repeated parameter: Type*
                if ptype.endswith('*'):
                    is_repeated = True
                    ptype = ptype[:-1].strip()
            else:
                name = cleaned
                ptype = ""

            if name:
                kind = "positional"
                if is_by_name:
                    kind = "by_name"
                elif is_repeated:
                    kind = "repeated"
                elif is_implicit:
                    kind = "implicit"
                elif is_using:
                    kind = "using"

                params.append(ScalaParameterInfo(
                    name=name,
                    type=ptype,
                    kind=kind,
                    default_value=default_value,
                    is_implicit=is_implicit,
                    is_using=is_using,
                    is_by_name=is_by_name,
                    is_repeated=is_repeated,
                    annotations=annotations,
                ))

        return params

    def _split_params(self, params_str: str) -> List[str]:
        """Split parameters respecting nested brackets."""
        parts = []
        depth = 0
        current = []
        for ch in params_str:
            if ch in ('[', '('):
                depth += 1
                current.append(ch)
            elif ch in (']', ')'):
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

    def _get_visibility(self, modifiers: str) -> str:
        """Determine visibility from modifiers."""
        if 'private' in modifiers:
            # Check for scoped private: private[scope]
            scope_match = re.search(r'private\[(\w+)\]', modifiers)
            if scope_match:
                return f"private[{scope_match.group(1)}]"
            return 'private'
        if 'protected' in modifiers:
            scope_match = re.search(r'protected\[(\w+)\]', modifiers)
            if scope_match:
                return f"protected[{scope_match.group(1)}]"
            return 'protected'
        return 'public'

    def _extract_brace_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content within braces, handling nesting."""
        idx = start_pos
        while idx < len(content) and content[idx] != '{':
            if content[idx] == '\n':
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
