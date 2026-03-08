"""
RustFunctionExtractor - Extracts Rust function and method definitions.

This extractor parses Rust source code and extracts:
- Top-level function definitions
- Methods in impl blocks
- Async functions
- Unsafe functions
- Const functions
- Generic functions with lifetime annotations
- Closures and closure types
- Function visibility (pub, pub(crate), etc.)

Supports all Rust editions (2015, 2018, 2021, 2024).

Part of CodeTrellis v4.14 - Rust Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RustParameterInfo:
    """Information about a Rust function parameter."""
    name: str
    type: str
    is_mutable: bool = False
    is_self: bool = False
    is_ref: bool = False


@dataclass
class RustFunctionInfo:
    """Information about a Rust function."""
    name: str
    parameters: List[RustParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    visibility: str = ""
    generics: List[str] = field(default_factory=list)
    is_async: bool = False
    is_unsafe: bool = False
    is_const: bool = False
    is_extern: bool = False
    is_test: bool = False
    is_pub: bool = False
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None
    attributes: List[str] = field(default_factory=list)
    where_clause: Optional[str] = None


@dataclass
class RustMethodInfo:
    """Information about a Rust method in an impl block."""
    name: str
    impl_type: str = ""
    trait_name: Optional[str] = None
    parameters: List[RustParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    visibility: str = ""
    is_async: bool = False
    is_unsafe: bool = False
    is_const: bool = False
    is_static: bool = False  # No self parameter
    self_kind: str = ""  # &self, &mut self, self, etc.
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None
    attributes: List[str] = field(default_factory=list)


class RustFunctionExtractor:
    """
    Extracts Rust function and method definitions from source code.

    Handles:
    - Top-level fn declarations
    - pub/pub(crate) visibility
    - async, unsafe, const, extern modifiers
    - Generic parameters with lifetime bounds
    - Where clauses
    - Return types including impl Trait
    - Self parameters (&self, &mut self, self)
    - #[test] and #[cfg(test)] attributes
    """

    # Top-level function pattern
    FUNC_PATTERN = re.compile(
        r'(?:(?P<attrs>(?:#\[[^\]]*\]\s*)*)'
        r'(?P<vis>pub(?:\s*\([^)]*\))?\s+)?'
        r'(?P<const>const\s+)?'
        r'(?P<async>async\s+)?'
        r'(?P<unsafe>unsafe\s+)?'
        r'(?P<extern>extern\s+(?:"[^"]*"\s+)?)?'
        r'fn\s+(?P<name>\w+)'
        r'(?:<(?P<generics>[^>]+)>)?'
        r'\s*\((?P<params>[^)]*)\)'
        r'(?:\s*->\s*(?P<ret>[^{;]+?))?'
        r'(?:\s*where\s+(?P<where>[^{]+?))?'
        r'\s*\{)',
        re.MULTILINE | re.DOTALL
    )

    # Impl block for context
    IMPL_BLOCK = re.compile(
        r'impl(?:<[^>]*>)?\s+(?:(?P<trait>[\w:]+)\s+for\s+)?(?P<type>[\w<>,\s:\']+?)\s*\{',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Rust function extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Rust functions and methods from source code.

        Args:
            content: Rust source code content
            file_path: Path to source file

        Returns:
            Dict with 'functions' and 'methods' keys
        """
        functions = self._extract_functions(content, file_path)
        methods = self._extract_methods(content, file_path)

        return {
            'functions': functions,
            'methods': methods,
        }

    def _parse_params(self, params_str: str) -> List[RustParameterInfo]:
        """Parse function parameters string into RustParameterInfo list."""
        params = []
        if not params_str or not params_str.strip():
            return params

        # Split on commas, but respect nested angle brackets and parentheses
        depth = 0
        current = []
        for ch in params_str:
            if ch in '<(':
                depth += 1
            elif ch in '>)':
                depth -= 1
            elif ch == ',' and depth == 0:
                current_str = ''.join(current).strip()
                if current_str:
                    params.append(self._parse_single_param(current_str))
                current = []
                continue
            current.append(ch)

        current_str = ''.join(current).strip()
        if current_str:
            params.append(self._parse_single_param(current_str))

        return params

    def _parse_single_param(self, param_str: str) -> RustParameterInfo:
        """Parse a single parameter string."""
        param_str = param_str.strip()

        # self parameter variants
        if param_str in ('self', 'mut self'):
            return RustParameterInfo(name='self', type='Self', is_self=True, is_mutable='mut' in param_str)
        if param_str in ('&self', '&mut self'):
            return RustParameterInfo(name='self', type='&Self', is_self=True, is_ref=True, is_mutable='mut' in param_str)
        if re.match(r'self\s*:', param_str):
            parts = param_str.split(':', 1)
            return RustParameterInfo(name='self', type=parts[1].strip(), is_self=True)

        # Regular parameter: name: Type or mut name: Type
        is_mutable = False
        if param_str.startswith('mut '):
            is_mutable = True
            param_str = param_str[4:]

        if ':' in param_str:
            parts = param_str.split(':', 1)
            name = parts[0].strip()
            ptype = parts[1].strip()
            is_ref = ptype.startswith('&')
            return RustParameterInfo(
                name=name,
                type=ptype,
                is_mutable=is_mutable,
                is_ref=is_ref,
            )

        # Pattern parameter without type annotation (rare in Rust)
        return RustParameterInfo(name=param_str, type='_', is_mutable=is_mutable)

    def _extract_doc_comment(self, content: str, pos: int) -> Optional[str]:
        """Extract doc comment (///) preceding a definition."""
        lines_before = content[:pos].rstrip().split('\n')
        doc_lines = []
        for line in reversed(lines_before):
            stripped = line.strip()
            if stripped.startswith('///'):
                doc_lines.insert(0, stripped[3:].strip())
            elif stripped.startswith('#[') or stripped == '':
                continue
            else:
                break
        return ' '.join(doc_lines) if doc_lines else None

    def _extract_attributes(self, content: str, pos: int) -> List[str]:
        """Extract attributes preceding a function definition."""
        attrs = []
        text_before = content[max(0, pos - 500):pos]
        for match in re.finditer(r'#\[([^\]]+)\]', text_before):
            attrs.append(match.group(1).strip())
        return attrs

    def _extract_functions(self, content: str, file_path: str) -> List[RustFunctionInfo]:
        """Extract top-level function definitions (not inside impl blocks)."""
        functions = []

        # Find all impl block ranges to exclude methods
        impl_ranges = []
        for impl_match in self.IMPL_BLOCK.finditer(content):
            start = impl_match.start()
            brace_pos = impl_match.end() - 1
            body = self._extract_brace_body_static(content, brace_pos)
            if body is not None:
                end = brace_pos + len(body) + 2
                impl_ranges.append((start, end))

        for match in self.FUNC_PATTERN.finditer(content):
            pos = match.start()

            # Skip if inside an impl block
            in_impl = False
            for impl_start, impl_end in impl_ranges:
                if impl_start < pos < impl_end:
                    in_impl = True
                    break
            if in_impl:
                continue

            name = match.group('name')
            vis = (match.group('vis') or '').strip()
            params_str = match.group('params') or ''
            ret = match.group('ret')
            generics_str = match.group('generics') or ''
            where_clause = match.group('where')
            is_async = bool(match.group('async'))
            is_unsafe = bool(match.group('unsafe'))
            is_const = bool(match.group('const'))
            is_extern = bool(match.group('extern'))
            line_number = content[:pos].count('\n') + 1

            generics = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []
            params = self._parse_params(params_str)
            attributes = self._extract_attributes(content, pos)
            # Also extract attributes from the regex-matched attrs group
            attrs_text = match.group('attrs') or ''
            if attrs_text:
                for attr_match in re.finditer(r'#\[([^\]]+)\]', attrs_text):
                    attr_val = attr_match.group(1).strip()
                    if attr_val not in attributes:
                        attributes.append(attr_val)
            doc_comment = self._extract_doc_comment(content, pos)

            is_test = any('test' in a for a in attributes)

            functions.append(RustFunctionInfo(
                name=name,
                parameters=params,
                return_type=ret.strip() if ret else None,
                visibility=vis,
                generics=generics,
                is_async=is_async,
                is_unsafe=is_unsafe,
                is_const=is_const,
                is_extern=is_extern,
                is_test=is_test,
                is_pub=vis.startswith('pub') if vis else False,
                file=file_path,
                line_number=line_number,
                doc_comment=doc_comment,
                attributes=attributes,
                where_clause=where_clause.strip() if where_clause else None,
            ))

        return functions

    def _extract_methods(self, content: str, file_path: str) -> List[RustMethodInfo]:
        """Extract methods from impl blocks."""
        methods = []

        for impl_match in self.IMPL_BLOCK.finditer(content):
            impl_type = impl_match.group('type').strip()
            trait_name = impl_match.group('trait')
            brace_pos = impl_match.end() - 1
            body = self._extract_brace_body_static(content, brace_pos)

            if not body:
                continue

            # Clean impl_type
            impl_type = re.sub(r'\s+', ' ', impl_type).strip()

            # Find functions in the impl body
            for fn_match in self.FUNC_PATTERN.finditer(body):
                name = fn_match.group('name')
                vis = (fn_match.group('vis') or '').strip()
                params_str = fn_match.group('params') or ''
                ret = fn_match.group('ret')
                is_async = bool(fn_match.group('async'))
                is_unsafe = bool(fn_match.group('unsafe'))
                is_const = bool(fn_match.group('const'))
                line_number = content[:impl_match.start()].count('\n') + body[:fn_match.start()].count('\n') + 1

                params = self._parse_params(params_str)
                attributes = self._extract_attributes(body, fn_match.start())

                # Determine self kind
                self_kind = ""
                is_static = True
                for p in params:
                    if p.is_self:
                        is_static = False
                        if p.is_ref:
                            self_kind = "&mut self" if p.is_mutable else "&self"
                        else:
                            self_kind = "mut self" if p.is_mutable else "self"
                        break

                # Filter out self param from displayed params
                non_self_params = [p for p in params if not p.is_self]

                methods.append(RustMethodInfo(
                    name=name,
                    impl_type=impl_type,
                    trait_name=trait_name.strip() if trait_name else None,
                    parameters=non_self_params,
                    return_type=ret.strip() if ret else None,
                    visibility=vis,
                    is_async=is_async,
                    is_unsafe=is_unsafe,
                    is_const=is_const,
                    is_static=is_static,
                    self_kind=self_kind,
                    file=file_path,
                    line_number=line_number,
                    attributes=attributes,
                ))

        return methods

    @staticmethod
    def _extract_brace_body_static(content: str, open_brace_pos: int) -> Optional[str]:
        """Static version of brace body extraction."""
        depth = 1
        i = open_brace_pos + 1
        in_string = False
        in_line_comment = False
        in_block_comment = False
        in_raw_string = False
        raw_hash_count = 0
        length = len(content)

        while i < length and depth > 0:
            ch = content[i]
            next_ch = content[i + 1] if i + 1 < length else ''

            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
                i += 1
                continue

            if in_block_comment:
                if ch == '*' and next_ch == '/':
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue

            if in_string:
                if ch == '\\':
                    i += 2
                    continue
                if ch == '"':
                    in_string = False
                i += 1
                continue

            if in_raw_string:
                if ch == '"':
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

            if ch == '/' and next_ch == '/':
                in_line_comment = True
                i += 2
                continue
            if ch == '/' and next_ch == '*':
                in_block_comment = True
                i += 2
                continue

            if ch == '"':
                in_string = True
                i += 1
                continue

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

            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[open_brace_pos + 1:i]

            i += 1

        return None
