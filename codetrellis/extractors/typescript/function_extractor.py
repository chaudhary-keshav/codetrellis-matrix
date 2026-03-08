"""
TypeScript Function Extractor for CodeTrellis

Extracts function definitions from TypeScript source code:
- Typed function declarations with return types
- Arrow functions with type annotations
- Generic functions
- Function overloads
- Type guard functions (x is Type)
- Assertion functions (asserts x is Type)
- Async functions and generators
- Method signatures with access modifiers
- Decorator factories (functions returning decorators)
- Standalone type predicates (TS 5.5+)

Supports TypeScript 2.0 through 5.7+:
- TS 2.0: Function types, optional/default params with types
- TS 3.0: Rest elements in tuple types, unknown return
- TS 3.4: const assertions in functions
- TS 3.7: Assertion functions (asserts param is Type)
- TS 4.0: Variadic tuple types in function params
- TS 4.1: Template literal types in generics
- TS 4.7: Instantiation expressions
- TS 5.0: const type parameters
- TS 5.5: Inferred type predicates

Part of CodeTrellis v4.31 - TypeScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TSParameterInfo:
    """Information about a TypeScript function parameter."""
    name: str
    type: str = ""
    default_value: Optional[str] = None
    is_optional: bool = False
    is_rest: bool = False
    is_destructured: bool = False
    is_readonly: bool = False
    access_modifier: str = ""  # public, private, protected (constructor params)
    line_number: int = 0


@dataclass
class TSFunctionInfo:
    """Information about a TypeScript function definition."""
    name: str
    file: str = ""
    line_number: int = 0
    function_type: str = "function"  # function, arrow, method, getter, setter
    return_type: str = ""
    is_async: bool = False
    is_generator: bool = False
    is_exported: bool = False
    is_default_export: bool = False
    is_type_guard: bool = False  # x is Type
    is_assertion: bool = False  # asserts x is Type
    generics: List[str] = field(default_factory=list)  # generic type params
    parameters: List[TSParameterInfo] = field(default_factory=list)
    overloads: int = 0  # number of overload signatures
    decorators: List[str] = field(default_factory=list)
    scope: str = ""  # module-level, class, namespace


@dataclass
class TSOverloadInfo:
    """Information about a function overload signature."""
    name: str
    file: str = ""
    line_number: int = 0
    parameters: List[TSParameterInfo] = field(default_factory=list)
    return_type: str = ""


@dataclass
class TSMethodInfo:
    """Information about a class/interface method."""
    name: str
    file: str = ""
    line_number: int = 0
    return_type: str = ""
    is_async: bool = False
    is_static: bool = False
    is_abstract: bool = False
    access_modifier: str = ""
    is_override: bool = False
    generics: List[str] = field(default_factory=list)
    parameters: List[TSParameterInfo] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)


class TypeScriptFunctionExtractor:
    """
    Extracts function definitions from TypeScript source code.

    Detects:
    - Typed function declarations and expressions
    - Arrow functions with type annotations
    - Generic functions with constraints
    - Function overloads
    - Type guard functions
    - Assertion functions
    - Async generators
    - Decorator factory functions
    """

    # Function declaration with type annotation
    FUNCTION_DECL_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:async\s+)?'
        r'(?:function\s*\*?\s+)'
        r'(\w+)'
        r'(?:<([^>]+)>)?'             # generics
        r'\s*\(([^)]*)\)'             # params
        r'(?:\s*:\s*([^\n{]+?))?'     # return type
        r'\s*\{',
        re.MULTILINE
    )

    # Arrow function with type annotation
    ARROW_FUNCTION_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+(\w+)'
        r'(?:\s*:\s*[^=]+?)?\s*=\s*'
        r'(?:async\s+)?'
        r'(?:<([^>]+)>)?'             # generics
        r'\s*\(([^)]*)\)'             # params
        r'(?:\s*:\s*([^\n=>]+?))?'    # return type
        r'\s*=>\s*',
        re.MULTILINE
    )

    # Function overload signature (no body)
    OVERLOAD_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+)?'
        r'(?:function\s+)?'
        r'(\w+)'
        r'(?:<[^>]+>)?'
        r'\s*\([^)]*\)\s*:\s*[^{]+?;\s*$',
        re.MULTILINE
    )

    # Type guard pattern (matches return type like "value is string")
    TYPE_GUARD_PATTERN = re.compile(
        r'\w+\s+is\s+\w',
    )

    # Assertion function pattern (matches return type like "asserts value is T")
    ASSERTION_PATTERN = re.compile(
        r'asserts\s+\w',
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all function definitions from TypeScript source code.

        Returns dict with keys: functions, overloads
        """
        functions = self._extract_functions(content, file_path)
        arrow_functions = self._extract_arrow_functions(content, file_path)
        overloads = self._extract_overloads(content, file_path)

        # Count overloads per function
        overload_counts = {}
        for ovl in overloads:
            overload_counts[ovl.name] = overload_counts.get(ovl.name, 0) + 1

        for func in functions:
            if func.name in overload_counts:
                func.overloads = overload_counts[func.name]

        return {
            'functions': functions + arrow_functions,
            'overloads': overloads,
        }

    def _extract_functions(self, content: str, file_path: str) -> List[TSFunctionInfo]:
        """Extract typed function declarations."""
        functions = []
        seen_names = set()

        for match in self.FUNCTION_DECL_PATTERN.finditer(content):
            name = match.group(1)
            generics_str = match.group(2) or ""
            params_str = match.group(3) or ""
            return_type = (match.group(4) or "").strip()
            line_num = content[:match.start()].count('\n') + 1

            if name in seen_names:
                continue
            seen_names.add(name)

            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))
            is_default = bool(re.search(r'\bexport\s+default\b', line_text))
            is_async = bool(re.search(r'\basync\b', line_text))
            is_generator = bool(re.search(r'function\s*\*', line_text))

            # Parse generics
            generics = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []

            # Parse parameters
            parameters = self._parse_parameters(params_str)

            # Check for type guard / assertion
            is_type_guard = bool(self.TYPE_GUARD_PATTERN.search(return_type)) if return_type else False
            is_assertion = bool(self.ASSERTION_PATTERN.search(return_type)) if return_type else False

            functions.append(TSFunctionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                function_type='generator' if is_generator else 'function',
                return_type=return_type,
                is_async=is_async,
                is_generator=is_generator,
                is_exported=is_exported,
                is_default_export=is_default,
                is_type_guard=is_type_guard,
                is_assertion=is_assertion,
                generics=generics,
                parameters=parameters,
            ))

        return functions

    def _extract_arrow_functions(self, content: str, file_path: str) -> List[TSFunctionInfo]:
        """Extract typed arrow function declarations."""
        functions = []
        seen_names = set()

        for match in self.ARROW_FUNCTION_PATTERN.finditer(content):
            name = match.group(1)
            generics_str = match.group(2) or ""
            params_str = match.group(3) or ""
            return_type = (match.group(4) or "").strip()
            line_num = content[:match.start()].count('\n') + 1

            if name in seen_names:
                continue
            seen_names.add(name)

            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))
            is_async = bool(re.search(r'\basync\b', line_text))

            generics = [g.strip() for g in generics_str.split(',') if g.strip()] if generics_str else []
            parameters = self._parse_parameters(params_str)

            is_type_guard = bool(self.TYPE_GUARD_PATTERN.search(return_type)) if return_type else False

            functions.append(TSFunctionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                function_type='arrow',
                return_type=return_type,
                is_async=is_async,
                is_exported=is_exported,
                is_type_guard=is_type_guard,
                generics=generics,
                parameters=parameters,
            ))

        return functions

    def _extract_overloads(self, content: str, file_path: str) -> List[TSOverloadInfo]:
        """Extract function overload signatures."""
        overloads = []

        for match in self.OVERLOAD_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Skip if this is a method call or variable declaration
            full_line = match.group(0).strip()
            if not re.match(r'(?:export\s+)?(?:function\s+)?\w+\s*(?:<[^>]*>)?\s*\([^)]*\)\s*:', full_line):
                continue

            overloads.append(TSOverloadInfo(
                name=name,
                file=file_path,
                line_number=line_num,
            ))

        return overloads

    def _parse_parameters(self, params_str: str) -> List[TSParameterInfo]:
        """Parse function parameter list with TypeScript type annotations."""
        parameters = []
        if not params_str.strip():
            return parameters

        # Simple split by comma (doesn't handle nested generics perfectly)
        depth = 0
        current = ""
        for ch in params_str:
            if ch in ('<', '(', '[', '{'):
                depth += 1
                current += ch
            elif ch in ('>', ')', ']', '}'):
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                param = self._parse_single_parameter(current.strip())
                if param:
                    parameters.append(param)
                current = ""
            else:
                current += ch

        if current.strip():
            param = self._parse_single_parameter(current.strip())
            if param:
                parameters.append(param)

        return parameters

    def _parse_single_parameter(self, param_str: str) -> Optional[TSParameterInfo]:
        """Parse a single TypeScript function parameter."""
        if not param_str:
            return None

        # Check for access modifier (constructor parameter property)
        access = ""
        for mod in ('public', 'private', 'protected'):
            if param_str.startswith(mod + ' '):
                access = mod
                param_str = param_str[len(mod):].strip()
                break

        # Check readonly
        is_readonly = False
        if param_str.startswith('readonly '):
            is_readonly = True
            param_str = param_str[9:].strip()

        # Check rest parameter
        is_rest = param_str.startswith('...')
        if is_rest:
            param_str = param_str[3:]

        # Check destructured parameter
        is_destructured = param_str.startswith('{') or param_str.startswith('[')

        # Parse name, optional marker, type, default
        m = re.match(r'(\w+|\{[^}]+\}|\[[^\]]+\])(\?)?\s*(?::\s*(.+?))?(?:\s*=\s*(.+))?$', param_str)
        if m:
            name = m.group(1)
            is_optional = bool(m.group(2))
            param_type = (m.group(3) or "").strip()
            default_val = (m.group(4) or "").strip() or None

            if default_val:
                is_optional = True

            return TSParameterInfo(
                name=name,
                type=param_type,
                default_value=default_val,
                is_optional=is_optional,
                is_rest=is_rest,
                is_destructured=is_destructured,
                is_readonly=is_readonly,
                access_modifier=access,
            )

        return TSParameterInfo(name=param_str)
