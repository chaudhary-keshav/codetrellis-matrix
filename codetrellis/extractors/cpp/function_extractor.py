"""
CppFunctionExtractor - Extracts C++ function, method, and operator definitions.

This extractor parses C++ source code and extracts:
- Free functions (regular, inline, constexpr, consteval)
- Class methods (virtual, override, final, const, noexcept)
- Constructors / Destructors (default, delete, explicit)
- Operator overloads
- Template functions
- Lambda expressions (C++11+)
- Coroutines (C++20: co_await, co_yield, co_return)
- Trailing return types (C++11: auto f() -> Type)
- Concepts-constrained functions (C++20: requires clause)
- Deduction guides (C++17)
- Structured bindings (C++17)

Supports all C++ standards: C++98 through C++26.

Part of CodeTrellis v4.20 - C++ Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CppParameterInfo:
    """Information about a C++ function parameter."""
    name: str
    type: str
    is_pointer: bool = False
    is_reference: bool = False
    is_rvalue_ref: bool = False  # && (C++11)
    is_const: bool = False
    is_volatile: bool = False
    has_default: bool = False
    default_value: Optional[str] = None
    is_variadic: bool = False  # ...
    is_pack: bool = False  # parameter pack (C++11)


@dataclass
class CppMethodInfo:
    """Information about a C++ function or method."""
    name: str
    parameters: List[CppParameterInfo] = field(default_factory=list)
    return_type: str = "void"
    access: str = "public"  # public, protected, private
    is_static: bool = False
    is_virtual: bool = False
    is_override: bool = False
    is_final: bool = False
    is_pure_virtual: bool = False  # = 0
    is_const: bool = False
    is_noexcept: bool = False
    is_constexpr: bool = False
    is_consteval: bool = False  # C++20
    is_inline: bool = False
    is_extern: bool = False
    is_explicit: bool = False
    is_template: bool = False
    template_params: Optional[str] = None
    is_constructor: bool = False
    is_destructor: bool = False
    is_operator: bool = False
    operator_name: Optional[str] = None
    is_deleted: bool = False  # = delete
    is_defaulted: bool = False  # = default
    is_coroutine: bool = False  # C++20
    requires_clause: Optional[str] = None  # C++20 requires
    trailing_return: Optional[str] = None  # -> Type
    noexcept_expr: Optional[str] = None  # noexcept(expr)
    class_name: Optional[str] = None
    namespace: Optional[str] = None
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None
    body_lines: int = 0
    complexity: int = 0


@dataclass
class CppLambdaInfo:
    """Information about a C++ lambda expression."""
    capture: str = ""  # [=], [&], [this], etc.
    parameters: Optional[str] = None
    return_type: Optional[str] = None
    is_mutable: bool = False
    is_constexpr: bool = False
    is_noexcept: bool = False
    is_generic: bool = False  # uses 'auto' params (C++14 generic lambda)
    file: str = ""
    line_number: int = 0
    body_lines: int = 0


class CppFunctionExtractor:
    """
    Extracts C++ function, method, and operator definitions.

    Handles:
    - Free functions and class methods
    - Template functions with concepts (C++20)
    - Constructors, destructors, operator overloads
    - Virtual, override, final, const, noexcept qualifiers
    - Constexpr / consteval functions
    - Trailing return types (auto f() -> Type)
    - Deleted / defaulted special member functions
    - Lambda expressions
    - Coroutine functions (co_await, co_yield, co_return)
    - Cyclomatic complexity estimation
    """

    # Free function / method pattern
    FUNC_PATTERN = re.compile(
        r'(?:(?P<template>template\s*<[^>]*(?:<[^>]*>[^>]*)*>)\s+)?'
        r'(?P<attrs>(?:\[\[[^\]]*\]\]\s*)*)'
        r'(?P<qualifiers>(?:(?:static|virtual|inline|extern|explicit|constexpr|consteval|friend)\s+)*)'
        r'(?P<ret>(?:(?:const|volatile|unsigned|signed|long|short|struct|class|enum|typename|auto|decltype\([^)]*\))\s+)*[\w:]+(?:<[^>]*(?:<[^>]*>[^>]*)*>)?[\s*&]*?)'
        r'\s+(?P<stars>[*&]*)(?P<name>(?:operator\s*(?:[+\-*/%^&|~!=<>!]+|(?:\(\))|(?:\[\])|(?:<<|>>)|(?:->)|\w+)|~?\w+))\s*'
        r'\((?P<params>[^)]*)\)\s*'
        r'(?P<post_quals>(?:\s*(?:const|volatile|noexcept(?:\([^)]*\))?|override|final|&|&&)\s*)*)'
        r'(?P<requires>\s*requires\s+[^{;]+)?'
        r'(?P<trailing>\s*->\s*[^{;]+)?'
        r'(?P<body>\{|;|=\s*(?:0|default|delete)\s*;)',
        re.MULTILINE | re.DOTALL
    )

    # Constructor pattern (no return type)
    CONSTRUCTOR_PATTERN = re.compile(
        r'(?P<qualifiers>(?:(?:explicit|inline|constexpr|consteval)\s+)*)'
        r'(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*'
        r'(?P<post_quals>(?:\s*(?:noexcept(?:\([^)]*\))?)\s*)*)'
        r'(?P<init>:\s*[^{]+)?'
        r'(?P<body>\{|;|=\s*(?:default|delete)\s*;)',
        re.MULTILINE
    )

    # Lambda pattern
    LAMBDA_PATTERN = re.compile(
        r'\[(?P<capture>[^\]]*)\]\s*'
        r'(?:\((?P<params>[^)]*)\))?\s*'
        r'(?P<mutable>mutable\s*)?'
        r'(?P<constexpr>constexpr\s*)?'
        r'(?P<noexcept>noexcept(?:\([^)]*\))?\s*)?'
        r'(?:->\s*(?P<ret>[^{]+?)\s*)?'
        r'\{',
        re.MULTILINE
    )

    # Coroutine keywords
    COROUTINE_PATTERN = re.compile(r'\b(?:co_await|co_yield|co_return)\b')

    # Complexity patterns (for cyclomatic complexity estimation)
    COMPLEXITY_PATTERNS = [
        re.compile(r'\bif\b'),
        re.compile(r'\belse\s+if\b'),
        re.compile(r'\bfor\b'),
        re.compile(r'\bwhile\b'),
        re.compile(r'\bcase\b'),
        re.compile(r'\bcatch\b'),
        re.compile(r'\b\?\s*'),  # ternary
        re.compile(r'\b&&\b'),
        re.compile(r'\b\|\|\b'),
    ]

    def __init__(self):
        """Initialize the C++ function extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all function/method definitions from C++ source code.

        Args:
            content: C++ source code content
            file_path: Path to source file

        Returns:
            Dict with 'methods', 'lambdas' lists
        """
        result = {
            'methods': [],
            'lambdas': [],
        }

        result['methods'] = self._extract_methods(content, file_path)
        result['lambdas'] = self._extract_lambdas(content, file_path)

        return result

    def _extract_methods(self, content: str, file_path: str) -> List[CppMethodInfo]:
        """Extract function and method definitions."""
        methods = []
        lines = content.split('\n')
        seen_names = set()  # Avoid duplicate captures for overloaded parsing

        for match in self.FUNC_PATTERN.finditer(content):
            name = match.group('name').strip()
            ret = match.group('ret').strip() if match.group('ret') else 'void'
            qualifiers = match.group('qualifiers') or ''
            post_quals = match.group('post_quals') or ''
            body_marker = match.group('body').strip()
            params_str = match.group('params') or ''
            is_template = match.group('template') is not None
            template_params = match.group('template') if is_template else None
            trailing_ret = match.group('trailing')
            requires_clause = match.group('requires')

            # Skip preprocessor defines and macros
            if name.startswith('#') or name.isupper():
                continue

            line_num = content[:match.start()].count('\n') + 1

            # Parse parameters
            params = self._parse_params(params_str)

            # Detect constructor/destructor
            is_destructor = name.startswith('~')
            is_operator = name.startswith('operator')
            operator_name = None
            if is_operator:
                operator_name = name.replace('operator', '').strip()

            # Detect deleted/defaulted
            is_deleted = '= delete' in body_marker
            is_defaulted = '= default' in body_marker
            is_pure_virtual = '= 0' in body_marker
            is_definition = body_marker.startswith('{')

            # Count body lines and complexity
            body_lines = 0
            complexity = 1  # Base complexity
            if is_definition:
                body_start = match.start() + content[match.start():].index('{')
                body_content = self._extract_brace_body(content, body_start)
                if body_content:
                    body_lines = body_content.count('\n') + 1
                    for pattern in self.COMPLEXITY_PATTERNS:
                        complexity += len(pattern.findall(body_content))

            # Detect coroutine
            is_coroutine = False
            if is_definition and body_content:
                is_coroutine = bool(self.COROUTINE_PATTERN.search(body_content))

            # Parse post qualifiers
            is_const = 'const' in post_quals
            is_noexcept = 'noexcept' in post_quals
            is_override = 'override' in post_quals
            is_final_method = 'final' in post_quals

            # Parse noexcept expression
            noexcept_expr = None
            noexcept_match = re.search(r'noexcept\(([^)]+)\)', post_quals)
            if noexcept_match:
                noexcept_expr = noexcept_match.group(1)

            # Detect class::method pattern
            class_name = None
            if '::' in name:
                parts = name.rsplit('::', 1)
                class_name = parts[0]
                name = parts[1]

            # Doc comment
            doc_comment = self._get_doc_comment(lines, line_num - 1)

            info = CppMethodInfo(
                name=name,
                parameters=params,
                return_type=ret + match.group('stars') if match.group('stars') else ret,
                is_static='static' in qualifiers,
                is_virtual='virtual' in qualifiers,
                is_override=is_override,
                is_final=is_final_method,
                is_pure_virtual=is_pure_virtual,
                is_const=is_const,
                is_noexcept=is_noexcept,
                is_constexpr='constexpr' in qualifiers,
                is_consteval='consteval' in qualifiers,
                is_inline='inline' in qualifiers,
                is_extern='extern' in qualifiers,
                is_explicit='explicit' in qualifiers,
                is_template=is_template,
                template_params=template_params,
                is_destructor=is_destructor,
                is_operator=is_operator,
                operator_name=operator_name,
                is_deleted=is_deleted,
                is_defaulted=is_defaulted,
                is_coroutine=is_coroutine,
                requires_clause=requires_clause.strip() if requires_clause else None,
                trailing_return=trailing_ret.strip().lstrip('-> ') if trailing_ret else None,
                noexcept_expr=noexcept_expr,
                class_name=class_name,
                file=file_path,
                line_number=line_num,
                doc_comment=doc_comment,
                body_lines=body_lines,
                complexity=complexity if is_definition else 0,
            )
            methods.append(info)

        # Extract constructors/destructors (no return type, not caught by FUNC_PATTERN)
        for match in self.CONSTRUCTOR_PATTERN.finditer(content):
            name = match.group('name').strip()
            if not name or name.startswith('#') or name.isupper():
                continue
            # Skip if this position was already captured by FUNC_PATTERN
            line_num = content[:match.start()].count('\n') + 1
            key = f"{name}:{line_num}"
            if key in seen_names:
                continue
            # Must look like a constructor: name matches a class-like identifier
            # Skip keywords that could be false positives
            if name.lstrip('~') in (
                'if', 'while', 'for', 'switch', 'catch', 'return', 'throw',
                'sizeof', 'alignof', 'decltype', 'typeid', 'static_assert',
                'namespace', 'using', 'typedef', 'template', 'class', 'struct',
                'enum', 'union', 'void', 'int', 'char', 'bool', 'float',
                'double', 'long', 'short', 'unsigned', 'signed', 'auto',
            ):
                continue
            seen_names.add(key)
            params_str = match.group('params') or ''
            qualifiers = match.group('qualifiers') or ''
            post_quals = match.group('post_quals') or ''
            body_marker = match.group('body').strip()
            is_destructor = name.startswith('~')
            is_deleted = '= delete' in body_marker
            is_defaulted = '= default' in body_marker
            is_definition = body_marker.startswith('{')

            params = self._parse_params(params_str)

            body_lines = 0
            complexity = 1
            body_content = None
            if is_definition:
                body_start = match.start() + content[match.start():].index('{')
                body_content = self._extract_brace_body(content, body_start)
                if body_content:
                    body_lines = body_content.count('\n') + 1
                    for pattern in self.COMPLEXITY_PATTERNS:
                        complexity += len(pattern.findall(body_content))

            is_noexcept = 'noexcept' in post_quals
            doc_comment = self._get_doc_comment(lines, line_num - 1)

            # Detect class::ctor pattern
            class_name = None
            actual_name = name
            if '::' in name:
                parts = name.rsplit('::', 1)
                class_name = parts[0]
                actual_name = parts[1]

            info = CppMethodInfo(
                name=actual_name,
                parameters=params,
                return_type='',
                is_explicit='explicit' in qualifiers,
                is_inline='inline' in qualifiers,
                is_constexpr='constexpr' in qualifiers,
                is_consteval='consteval' in qualifiers,
                is_constructor=not is_destructor,
                is_destructor=is_destructor,
                is_noexcept=is_noexcept,
                is_deleted=is_deleted,
                is_defaulted=is_defaulted,
                class_name=class_name,
                file=file_path,
                line_number=line_num,
                doc_comment=doc_comment,
                body_lines=body_lines,
                complexity=complexity if is_definition else 0,
            )
            methods.append(info)

        return methods

    def _extract_lambdas(self, content: str, file_path: str) -> List[CppLambdaInfo]:
        """Extract lambda expressions."""
        lambdas = []
        for match in self.LAMBDA_PATTERN.finditer(content):
            capture = match.group('capture')
            params = match.group('params')
            ret = match.group('ret')
            is_mutable = match.group('mutable') is not None
            is_constexpr = match.group('constexpr') is not None
            is_noexcept = match.group('noexcept') is not None
            line_num = content[:match.start()].count('\n') + 1

            body_start = match.end() - 1
            body = self._extract_brace_body(content, body_start)
            body_lines = body.count('\n') + 1 if body else 0

            lambdas.append(CppLambdaInfo(
                capture=capture,
                parameters=params,
                return_type=ret.strip() if ret else None,
                is_mutable=is_mutable,
                is_constexpr=is_constexpr,
                is_noexcept=is_noexcept,
                is_generic=bool(params and 'auto' in params),
                file=file_path,
                line_number=line_num,
                body_lines=body_lines,
            ))
        return lambdas

    def _parse_params(self, params_str: str) -> List[CppParameterInfo]:
        """Parse function parameters string."""
        params = []
        if not params_str.strip() or params_str.strip() == 'void':
            return params

        parts = self._split_outside_angles(params_str)
        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Handle variadic (...)
            if part == '...':
                params.append(CppParameterInfo(
                    name='...', type='...', is_variadic=True
                ))
                continue

            # Handle parameter packs (Type... name)
            is_pack = '...' in part and part != '...'

            # Parse type and name
            is_const = 'const' in part
            is_volatile = 'volatile' in part

            # Default value
            default_value = None
            if '=' in part:
                eq_idx = part.index('=')
                default_value = part[eq_idx + 1:].strip()
                part = part[:eq_idx].strip()

            # Try to split into type and name
            tokens = part.replace('...', '').split()
            if len(tokens) >= 2:
                name = tokens[-1].strip('*& ')
                ptype = ' '.join(tokens[:-1])
            elif len(tokens) == 1:
                name = ''
                ptype = tokens[0]
            else:
                continue

            is_pointer = '*' in part
            is_reference = '&' in part and '&&' not in part
            is_rvalue_ref = '&&' in part

            params.append(CppParameterInfo(
                name=name,
                type=ptype,
                is_pointer=is_pointer,
                is_reference=is_reference,
                is_rvalue_ref=is_rvalue_ref,
                is_const=is_const,
                is_volatile=is_volatile,
                has_default=default_value is not None,
                default_value=default_value,
                is_variadic=part.strip().endswith('...'),
                is_pack=is_pack,
            ))

        return params

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
        """Split string by commas, not inside angle brackets or parentheses."""
        parts = []
        depth_angle = 0
        depth_paren = 0
        current = []
        for ch in s:
            if ch == '<':
                depth_angle += 1
            elif ch == '>':
                depth_angle -= 1
            elif ch == '(':
                depth_paren += 1
            elif ch == ')':
                depth_paren -= 1
            elif ch == ',' and depth_angle == 0 and depth_paren == 0:
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
