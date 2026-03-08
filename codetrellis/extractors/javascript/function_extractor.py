"""
JavaScript Function Extractor for CodeTrellis

Extracts function definitions from JavaScript source code:
- Function declarations (named, anonymous)
- Arrow functions (const/let/var assigned)
- Generator functions (function*)
- Async functions and async generators
- IIFEs (Immediately Invoked Function Expressions)
- Object method shorthand
- Computed property methods

Supports ES5 through ES2024+:
- ES5: function declarations, function expressions
- ES6 (2015): arrow functions, default parameters, rest params, destructuring
- ES2017: async/await
- ES2018: async generators, for-await-of
- ES2020: optional chaining in function bodies
- ES2022: top-level await

Part of CodeTrellis v4.30 - JavaScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JSParameterInfo:
    """Information about a JavaScript function parameter."""
    name: str
    type: str = ""  # JSDoc or inferred type
    default_value: Optional[str] = None
    is_rest: bool = False
    is_destructured: bool = False
    line_number: int = 0


@dataclass
class JSFunctionInfo:
    """Information about a JavaScript function definition."""
    name: str
    file: str = ""
    line_number: int = 0
    function_type: str = "function"  # function, arrow, method, getter, setter
    is_async: bool = False
    is_generator: bool = False
    is_exported: bool = False
    is_default_export: bool = False
    is_iife: bool = False
    parameters: List[JSParameterInfo] = field(default_factory=list)
    return_type: str = ""  # JSDoc @returns type
    jsdoc_description: str = ""
    decorators: List[str] = field(default_factory=list)
    scope: str = ""  # module-level, class method, object method


@dataclass
class JSArrowFunctionInfo:
    """Information about a named arrow function assignment."""
    name: str
    file: str = ""
    line_number: int = 0
    is_async: bool = False
    is_exported: bool = False
    is_default_export: bool = False
    parameters: List[JSParameterInfo] = field(default_factory=list)
    return_type: str = ""


@dataclass
class JSGeneratorInfo:
    """Information about a generator function."""
    name: str
    file: str = ""
    line_number: int = 0
    is_async: bool = False
    is_exported: bool = False
    parameters: List[JSParameterInfo] = field(default_factory=list)


class JavaScriptFunctionExtractor:
    """
    Extracts function definitions from JavaScript source code.

    Detects:
    - Named function declarations
    - Arrow function assignments (const/let/var)
    - Generator functions (function*)
    - Async functions and async generators
    - Method definitions in object literals
    - IIFEs
    - Exported functions
    """

    # Standard function declaration
    FUNC_DECL_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:async\s+)?'
        r'function\s*(\*?)\s*(\w+)\s*'
        r'\(([^)]*)\)\s*\{',
        re.MULTILINE
    )

    # Arrow function assigned to const/let/var
    ARROW_FUNC_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:async\s+)?'
        r'(?:\([^)]*\)|[\w$]+)\s*=>\s*',
        re.MULTILINE
    )

    # Exported arrow / function expression (module.exports or exports.name)
    CJS_EXPORT_FUNC_PATTERN = re.compile(
        r'^[ \t]*(?:module\.)?exports(?:\.(\w+))?\s*=\s*'
        r'(?:async\s+)?'
        r'(?:function\s*\*?\s*(\w+)?\s*\([^)]*\)|'
        r'(?:\([^)]*\)|[\w$]+)\s*=>)',
        re.MULTILINE
    )

    # Object method shorthand: methodName(args) { ... }
    OBJECT_METHOD_PATTERN = re.compile(
        r'^[ \t]*(?:async\s+)?(?:(\*)\s*)?(\w+)\s*\(([^)]*)\)\s*\{',
        re.MULTILINE
    )

    # IIFE pattern
    IIFE_PATTERN = re.compile(
        r'\(\s*(?:async\s+)?function\s*\w?\s*\([^)]*\)\s*\{',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all function definitions from JavaScript source code.

        Returns dict with keys: functions, arrow_functions, generators
        """
        functions = self._extract_functions(content, file_path)
        arrow_functions = self._extract_arrow_functions(content, file_path)
        generators = self._extract_generators(content, file_path)

        return {
            'functions': functions,
            'arrow_functions': arrow_functions,
            'generators': generators,
        }

    def _extract_functions(self, content: str, file_path: str) -> List[JSFunctionInfo]:
        """Extract standard function declarations."""
        functions = []
        seen = set()

        for match in self.FUNC_DECL_PATTERN.finditer(content):
            is_generator = match.group(1) == '*'
            name = match.group(2)
            params_str = match.group(3)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))
            is_default = bool(re.search(r'\bexport\s+default\b', line_text))
            is_async = bool(re.search(r'\basync\b', line_text))

            parameters = self._parse_params(params_str)

            functions.append(JSFunctionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                function_type='generator' if is_generator else 'function',
                is_async=is_async,
                is_generator=is_generator,
                is_exported=is_exported,
                is_default_export=is_default,
                parameters=parameters,
                scope='module',
            ))

        # IIFE detection
        for match in self.IIFE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            is_async = 'async' in match.group(0)
            functions.append(JSFunctionInfo(
                name='<IIFE>',
                file=file_path,
                line_number=line_num,
                function_type='iife',
                is_async=is_async,
                is_iife=True,
                scope='module',
            ))

        # CommonJS exported functions: module.exports = function name(...) {}
        for match in self.CJS_EXPORT_FUNC_PATTERN.finditer(content):
            export_name = match.group(1)  # exports.name (or None for module.exports)
            func_name = match.group(2)    # function name (or None for anonymous)
            name = func_name or export_name or '<anonymous>'
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            match_text = match.group(0)
            is_async = 'async' in match_text
            is_generator = '*' in match_text

            # Try to extract params
            params_match = re.search(r'\(([^)]*)\)', match_text)
            parameters = self._parse_params(params_match.group(1)) if params_match else []

            functions.append(JSFunctionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                function_type='function',
                is_async=is_async,
                is_generator=is_generator,
                is_exported=True,
                is_default_export=(export_name is None),
                parameters=parameters,
                scope='module',
            ))

        return functions

    def _extract_arrow_functions(self, content: str, file_path: str) -> List[JSArrowFunctionInfo]:
        """Extract named arrow function assignments."""
        arrows = []
        seen = set()

        for match in self.ARROW_FUNC_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))
            is_default = bool(re.search(r'\bexport\s+default\b', line_text))
            is_async = bool(re.search(r'\basync\b', line_text))

            # Try to extract params from the arrow function
            params_match = re.search(r'\(([^)]*)\)\s*=>', match.group(0))
            params = []
            if params_match:
                params = self._parse_params(params_match.group(1))

            arrows.append(JSArrowFunctionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_async=is_async,
                is_exported=is_exported,
                is_default_export=is_default,
                parameters=params,
            ))

        return arrows

    def _extract_generators(self, content: str, file_path: str) -> List[JSGeneratorInfo]:
        """Extract generator functions (function*)."""
        generators = []
        seen = set()

        pattern = re.compile(
            r'^[ \t]*(?:export\s+(?:default\s+)?)?'
            r'(?:async\s+)?function\s*\*\s*(\w+)\s*\(([^)]*)\)',
            re.MULTILINE
        )

        for match in pattern.finditer(content):
            name = match.group(1)
            params_str = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))
            is_async = bool(re.search(r'\basync\b', line_text))

            generators.append(JSGeneratorInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_async=is_async,
                is_exported=is_exported,
                parameters=self._parse_params(params_str),
            ))

        return generators

    def _parse_params(self, params_str: str) -> List[JSParameterInfo]:
        """Parse function parameter string into parameter list."""
        params = []
        if not params_str or not params_str.strip():
            return params

        # Split by comma, handling nested structures
        depth = 0
        current = ""
        for ch in params_str:
            if ch in ('(', '[', '{'):
                depth += 1
                current += ch
            elif ch in (')', ']', '}'):
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                if current.strip():
                    params.append(self._parse_single_param(current.strip()))
                current = ""
            else:
                current += ch

        if current.strip():
            params.append(self._parse_single_param(current.strip()))

        return params

    def _parse_single_param(self, param: str) -> JSParameterInfo:
        """Parse a single parameter string."""
        is_rest = param.startswith('...')
        if is_rest:
            param = param[3:]

        is_destructured = param.startswith('{') or param.startswith('[')

        # Handle default value
        default_value = None
        if '=' in param and not is_destructured:
            parts = param.split('=', 1)
            param = parts[0].strip()
            default_value = parts[1].strip()

        name = param if not is_destructured else param[:30]

        return JSParameterInfo(
            name=name,
            is_rest=is_rest,
            is_destructured=is_destructured,
            default_value=default_value,
        )
