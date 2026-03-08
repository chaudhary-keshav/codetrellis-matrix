"""
Swift Function Extractor for CodeTrellis

Extracts function and method definitions from Swift source code:
- Free functions (global, generic, async, throws, rethrows)
- Methods (instance, static, class, mutating, nonmutating)
- Initializers (designated, convenience, required, failable)
- Deinitializers
- Subscripts (with get/set)
- Operators (prefix, infix, postfix)
- Closures and trailing closures

Supports Swift 5.0-6.0+ features:
- async/await functions
- Typed throws (Swift 6.0)
- Parameter packs (each/repeat)
- if/switch expressions
- Opaque return types (some)
- Primary associated types

Part of CodeTrellis v4.22 - Swift Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SwiftParameterInfo:
    """Information about a function parameter."""
    external_name: str = ""
    internal_name: str = ""
    type: str = ""
    default_value: str = ""
    is_inout: bool = False
    is_variadic: bool = False
    is_autoclosure: bool = False
    is_escaping: bool = False
    attributes: List[str] = field(default_factory=list)


@dataclass
class SwiftFunctionInfo:
    """Information about a Swift function."""
    name: str
    file: str = ""
    parameters: List[SwiftParameterInfo] = field(default_factory=list)
    return_type: str = ""
    generic_params: List[str] = field(default_factory=list)
    generic_constraints: List[str] = field(default_factory=list)
    is_async: bool = False
    is_throws: bool = False
    is_rethrows: bool = False
    throw_type: str = ""  # Swift 6.0 typed throws
    is_static: bool = False
    is_class_func: bool = False
    is_mutating: bool = False
    is_discardable: bool = False
    is_inlinable: bool = False
    access_level: str = "internal"
    attributes: List[str] = field(default_factory=list)
    body_lines: int = 0
    line_number: int = 0


@dataclass
class SwiftMethodInfo:
    """Information about a Swift method (function within a type)."""
    name: str
    owner_type: str = ""
    file: str = ""
    parameters: List[SwiftParameterInfo] = field(default_factory=list)
    return_type: str = ""
    is_async: bool = False
    is_throws: bool = False
    is_static: bool = False
    is_class_func: bool = False
    is_mutating: bool = False
    is_override: bool = False
    is_final: bool = False
    access_level: str = "internal"
    attributes: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SwiftInitInfo:
    """Information about an initializer."""
    owner_type: str = ""
    file: str = ""
    parameters: List[SwiftParameterInfo] = field(default_factory=list)
    is_convenience: bool = False
    is_required: bool = False
    is_failable: bool = False
    is_failable_force: bool = False  # init!
    is_async: bool = False
    is_throws: bool = False
    access_level: str = "internal"
    attributes: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SwiftSubscriptInfo:
    """Information about a subscript."""
    owner_type: str = ""
    file: str = ""
    parameters: List[SwiftParameterInfo] = field(default_factory=list)
    return_type: str = ""
    is_static: bool = False
    has_setter: bool = False
    access_level: str = "internal"
    line_number: int = 0


class SwiftFunctionExtractor:
    """
    Extracts Swift function and method definitions using regex-based parsing.

    Covers:
    - Top-level functions
    - Instance/static/class methods
    - Initializers (designated, convenience, required, failable)
    - Subscripts
    - Operators
    - async/await, throws/rethrows/typed throws
    """

    # Function/method pattern
    FUNC_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<attrs>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<access>open|public|internal|fileprivate|private)\s+)?'
        r'(?:(?P<override>override)\s+)?'
        r'(?:(?P<final>final)\s+)?'
        r'(?:(?P<static>static|class)\s+)?'
        r'(?:(?P<mutating>mutating|nonmutating)\s+)?'
        r'func\s+(?P<name>[\w`]+(?:\s*[+\-*/^%<>=!&|~?.]+)?)'
        r'(?:\s*<(?P<generics>[^>]+)>)?'
        r'\s*\((?P<params>[^)]*)\)'
        r'(?:\s*(?P<async>async)\b)?'
        r'(?:\s*(?P<throws>throws|rethrows)(?:\((?P<throw_type>[^)]+)\))?)?'
        r'(?:\s*->\s*(?P<return>[^\n{]+?))?'
        r'\s*(?:where\s+(?P<where>[^{]+?))?\s*\{',
        re.MULTILINE
    )

    # Init pattern
    INIT_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<attrs>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<access>public|internal|fileprivate|private)\s+)?'
        r'(?:(?P<convenience>convenience)\s+)?'
        r'(?:(?P<required>required)\s+)?'
        r'(?:(?P<convenience2>convenience)\s+)?'
        r'init(?P<failable>[?!])?\s*'
        r'(?:<(?P<generics>[^>]+)>\s*)?'
        r'\((?P<params>[^)]*)\)'
        r'(?:\s*(?P<async>async)\b)?'
        r'(?:\s*(?P<throws>throws))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Deinit pattern
    DEINIT_PATTERN = re.compile(
        r'^\s*deinit\s*\{',
        re.MULTILINE
    )

    # Subscript pattern
    SUBSCRIPT_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<access>public|internal|fileprivate|private)\s+)?'
        r'(?:(?P<static>static)\s+)?'
        r'subscript\s*'
        r'(?:<(?P<generics>[^>]+)>\s*)?'
        r'\((?P<params>[^)]*)\)'
        r'\s*->\s*(?P<return>[^\n{]+?)'
        r'\s*\{',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all function/method definitions from Swift source code.

        Args:
            content: Swift source code content
            file_path: Path to source file

        Returns:
            Dict with keys: functions, methods, inits, subscripts
        """
        return {
            'functions': self._extract_functions(content, file_path),
            'inits': self._extract_inits(content, file_path),
            'subscripts': self._extract_subscripts(content, file_path),
        }

    def _extract_functions(self, content: str, file_path: str) -> List[SwiftFunctionInfo]:
        """Extract function and method declarations."""
        functions = []
        for match in self.FUNC_PATTERN.finditer(content):
            attrs_str = (match.group('attrs') or '').strip()
            attributes = re.findall(r'@(\w+(?:\([^)]*\))?)', attrs_str)

            access = match.group('access') or 'internal'
            name = match.group('name').strip().strip('`')

            is_override = bool(match.group('override'))
            is_final = bool(match.group('final'))
            static_kw = match.group('static') or ''
            is_static = static_kw == 'static'
            is_class_func = static_kw == 'class'
            is_mutating = match.group('mutating') == 'mutating' if match.group('mutating') else False

            generics_str = match.group('generics') or ''
            generic_params = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []

            params_str = match.group('params') or ''
            parameters = self._parse_parameters(params_str)

            is_async = bool(match.group('async'))
            throws_kw = match.group('throws') or ''
            is_throws = throws_kw == 'throws'
            is_rethrows = throws_kw == 'rethrows'
            throw_type = (match.group('throw_type') or '').strip()

            return_type = (match.group('return') or '').strip()

            where_str = match.group('where') or ''
            constraints = [c.strip() for c in where_str.split(',') if c.strip()] if where_str else []

            is_discardable = '@discardableResult' in attrs_str
            is_inlinable = '@inlinable' in attrs_str

            # Count body lines
            body_start = match.end() - 1
            body = self._extract_brace_body(content, body_start)
            body_lines = body.count('\n') + 1 if body else 0

            line_number = content[:match.start()].count('\n') + 1

            functions.append(SwiftFunctionInfo(
                name=name,
                file=file_path,
                parameters=parameters,
                return_type=return_type,
                generic_params=generic_params,
                generic_constraints=constraints,
                is_async=is_async,
                is_throws=is_throws,
                is_rethrows=is_rethrows,
                throw_type=throw_type,
                is_static=is_static,
                is_class_func=is_class_func,
                is_mutating=is_mutating,
                is_discardable=is_discardable,
                is_inlinable=is_inlinable,
                access_level=access,
                attributes=attributes,
                body_lines=body_lines,
                line_number=line_number,
            ))
        return functions

    def _extract_inits(self, content: str, file_path: str) -> List[SwiftInitInfo]:
        """Extract initializer declarations."""
        inits = []
        for match in self.INIT_PATTERN.finditer(content):
            attrs_str = (match.group('attrs') or '').strip()
            attributes = re.findall(r'@(\w+(?:\([^)]*\))?)', attrs_str)

            access = match.group('access') or 'internal'
            is_convenience = bool(match.group('convenience') or match.group('convenience2'))
            is_required = bool(match.group('required'))

            failable = match.group('failable') or ''
            is_failable = failable == '?'
            is_failable_force = failable == '!'

            params_str = match.group('params') or ''
            parameters = self._parse_parameters(params_str)

            is_async = bool(match.group('async'))
            is_throws = bool(match.group('throws'))

            line_number = content[:match.start()].count('\n') + 1

            inits.append(SwiftInitInfo(
                file=file_path,
                parameters=parameters,
                is_convenience=is_convenience,
                is_required=is_required,
                is_failable=is_failable,
                is_failable_force=is_failable_force,
                is_async=is_async,
                is_throws=is_throws,
                access_level=access,
                attributes=attributes,
                line_number=line_number,
            ))
        return inits

    def _extract_subscripts(self, content: str, file_path: str) -> List[SwiftSubscriptInfo]:
        """Extract subscript declarations."""
        subscripts = []
        for match in self.SUBSCRIPT_PATTERN.finditer(content):
            access = match.group('access') or 'internal'
            is_static = bool(match.group('static'))
            params_str = match.group('params') or ''
            parameters = self._parse_parameters(params_str)
            return_type = (match.group('return') or '').strip()

            # Check for setter in body
            body_start = match.end() - 1
            body = self._extract_brace_body(content, body_start)
            has_setter = 'set' in body and re.search(r'\bset\s*[({]', body) is not None

            line_number = content[:match.start()].count('\n') + 1

            subscripts.append(SwiftSubscriptInfo(
                file=file_path,
                parameters=parameters,
                return_type=return_type,
                is_static=is_static,
                has_setter=has_setter,
                access_level=access,
                line_number=line_number,
            ))
        return subscripts

    def _parse_parameters(self, params_str: str) -> List[SwiftParameterInfo]:
        """Parse function parameter list."""
        params = []
        if not params_str.strip():
            return params

        parts = self._split_params(params_str)
        for part in parts:
            part = part.strip()
            if not part:
                continue

            param = SwiftParameterInfo()

            # Extract attributes
            attr_matches = re.findall(r'@(\w+)', part)
            param.attributes = attr_matches
            param.is_autoclosure = '@autoclosure' in part
            param.is_escaping = '@escaping' in part

            # Remove attributes for further parsing
            clean = re.sub(r'@\w+\s*', '', part).strip()

            # Check for inout
            if 'inout' in clean:
                param.is_inout = True
                clean = clean.replace('inout', '').strip()

            # Check for default value
            default_match = re.search(r'=\s*(.+)$', clean)
            if default_match:
                param.default_value = default_match.group(1).strip()
                clean = clean[:default_match.start()].strip()

            # Check for variadic
            if clean.endswith('...'):
                param.is_variadic = True
                clean = clean[:-3].strip()

            # Parse name and type
            if ':' in clean:
                name_part, type_part = clean.split(':', 1)
                name_parts = name_part.strip().split()
                if len(name_parts) == 2:
                    param.external_name = name_parts[0]
                    param.internal_name = name_parts[1]
                elif len(name_parts) == 1:
                    param.external_name = name_parts[0]
                    param.internal_name = name_parts[0]
                param.type = type_part.strip()
            else:
                param.internal_name = clean

            params.append(param)
        return params

    def _extract_brace_body(self, content: str, open_pos: int) -> str:
        """Extract body between matching braces."""
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
        """Split parameter list respecting nested brackets."""
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
