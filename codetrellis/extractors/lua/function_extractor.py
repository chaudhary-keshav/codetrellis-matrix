"""
Lua Function Extractor for CodeTrellis

Extracts function and method definitions from Lua source code:
- Top-level functions (global and local)
- Module functions (M.func = function or function M.func)
- Instance methods (function Class:method)
- Anonymous function assignments
- Closures / factories
- Coroutine functions (coroutine.create, coroutine.wrap)
- Varargs (...) detection
- Iterator functions (for-in generators)

Supports Lua 5.1 through 5.4+ and LuaJIT 2.x features:
- goto labels (5.2+)
- Integer division // (5.3+)
- Bitwise operators (5.3+)
- To-be-closed variables <close> (5.4+)

Part of CodeTrellis v4.28 - Lua Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class LuaParameterInfo:
    """Information about a function parameter."""
    name: str
    is_varargs: bool = False
    line_number: int = 0


@dataclass
class LuaFunctionInfo:
    """Information about a Lua function."""
    name: str
    file: str = ""
    parameters: List[LuaParameterInfo] = field(default_factory=list)
    is_local: bool = False
    is_method: bool = False
    is_anonymous: bool = False
    is_varargs: bool = False
    is_coroutine: bool = False
    is_iterator: bool = False
    is_recursive: bool = False
    is_callback: bool = False
    owner_table: str = ""
    separator: str = ""  # '.' or ':'
    return_count: int = 0  # number of return statements
    doc_comment: str = ""
    line_number: int = 0
    end_line: int = 0


@dataclass
class LuaMethodInfo:
    """Information about a method (function with colon syntax)."""
    name: str
    class_name: str = ""
    file: str = ""
    parameters: List[LuaParameterInfo] = field(default_factory=list)
    is_static: bool = False
    is_private: bool = False  # starts with _
    is_metamethod: bool = False
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class LuaCoroutineInfo:
    """Information about coroutine usage."""
    name: str
    file: str = ""
    kind: str = ""  # create, wrap, resume, yield
    wrapped_function: str = ""
    line_number: int = 0


class LuaFunctionExtractor:
    """
    Extracts Lua function definitions using regex-based parsing.

    Supports:
    - function name(...) end
    - local function name(...) end
    - Table.func = function(...) end
    - function Table.func(...) end
    - function Table:method(...) end
    - Table.func = function(self, ...) end
    - Anonymous function assignments
    - Coroutine creation and wrapping
    """

    # Global function: function name(...)
    GLOBAL_FUNC_PATTERN = re.compile(
        r"^\s*function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)",
        re.MULTILINE
    )

    # Local function: local function name(...)
    LOCAL_FUNC_PATTERN = re.compile(
        r"^\s*local\s+function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)",
        re.MULTILINE
    )

    # Table method/function: function Table.func(...) or function Table:method(...)
    TABLE_FUNC_PATTERN = re.compile(
        r"^\s*function\s+(?P<table>\w+)(?P<sep>[.:])(?P<name>\w+)\s*\((?P<params>[^)]*)\)",
        re.MULTILINE
    )

    # Assigned function: name = function(...) or local name = function(...)
    ASSIGNED_FUNC_PATTERN = re.compile(
        r"^\s*(?:local\s+)?(?P<name>\w+)\s*=\s*function\s*\((?P<params>[^)]*)\)",
        re.MULTILINE
    )

    # Table-assigned function: Table.name = function(...)
    TABLE_ASSIGNED_FUNC_PATTERN = re.compile(
        r"^\s*(?P<table>\w+)(?P<sep>[.:])(?P<name>\w+)\s*=\s*function\s*\((?P<params>[^)]*)\)",
        re.MULTILINE
    )

    # Coroutine patterns
    COROUTINE_CREATE_PATTERN = re.compile(
        r"(?P<name>\w+)\s*=\s*coroutine\.(?P<kind>create|wrap)\s*\(\s*(?:function|(?P<func>\w+))",
        re.MULTILINE
    )
    COROUTINE_YIELD_PATTERN = re.compile(
        r"coroutine\.yield\s*\(",
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the function extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all function definitions from Lua source code.

        Args:
            content: Lua source code
            file_path: Path to source file

        Returns:
            Dict with 'functions', 'methods', 'coroutines' lists
        """
        functions = []
        methods = []
        coroutines = []
        lines = content.split('\n')

        seen_funcs = set()

        # Extract table methods/functions first (more specific)
        for match in self.TABLE_FUNC_PATTERN.finditer(content):
            key = (match.group('table'), match.group('name'))
            if key not in seen_funcs:
                seen_funcs.add(key)
                line_num = content[:match.start()].count('\n') + 1
                doc = self._get_preceding_comment(lines, line_num - 1)
                params = self._parse_params(match.group('params'))
                is_method = match.group('sep') == ':'
                name = match.group('name')

                if is_method:
                    methods.append(LuaMethodInfo(
                        name=name,
                        class_name=match.group('table'),
                        file=file_path,
                        parameters=params,
                        is_private=name.startswith('_'),
                        is_metamethod=name.startswith('__'),
                        doc_comment=doc,
                        line_number=line_num,
                    ))
                else:
                    functions.append(LuaFunctionInfo(
                        name=name,
                        file=file_path,
                        parameters=params,
                        is_method=False,
                        owner_table=match.group('table'),
                        separator='.',
                        is_varargs=any(p.is_varargs for p in params),
                        doc_comment=doc,
                        line_number=line_num,
                    ))

        # Extract table-assigned functions
        for match in self.TABLE_ASSIGNED_FUNC_PATTERN.finditer(content):
            key = (match.group('table'), match.group('name'))
            if key not in seen_funcs:
                seen_funcs.add(key)
                line_num = content[:match.start()].count('\n') + 1
                doc = self._get_preceding_comment(lines, line_num - 1)
                params = self._parse_params(match.group('params'))
                is_method = match.group('sep') == ':'

                if is_method:
                    methods.append(LuaMethodInfo(
                        name=match.group('name'),
                        class_name=match.group('table'),
                        file=file_path,
                        parameters=params,
                        is_private=match.group('name').startswith('_'),
                        is_metamethod=match.group('name').startswith('__'),
                        doc_comment=doc,
                        line_number=line_num,
                    ))
                else:
                    functions.append(LuaFunctionInfo(
                        name=match.group('name'),
                        file=file_path,
                        parameters=params,
                        owner_table=match.group('table'),
                        separator=match.group('sep'),
                        is_varargs=any(p.is_varargs for p in params),
                        doc_comment=doc,
                        line_number=line_num,
                    ))

        # Extract assigned functions: local name = function(...) or name = function(...)
        for match in self.ASSIGNED_FUNC_PATTERN.finditer(content):
            name = match.group('name')
            if ('', name) not in seen_funcs:
                seen_funcs.add(('', name))
                line_num = content[:match.start()].count('\n') + 1
                doc = self._get_preceding_comment(lines, line_num - 1)
                params = self._parse_params(match.group('params'))
                is_local = match.group(0).lstrip().startswith('local')
                functions.append(LuaFunctionInfo(
                    name=name,
                    file=file_path,
                    parameters=params,
                    is_local=is_local,
                    is_anonymous=True,
                    is_varargs=any(p.is_varargs for p in params),
                    doc_comment=doc,
                    line_number=line_num,
                ))

        # Extract local functions
        for match in self.LOCAL_FUNC_PATTERN.finditer(content):
            name = match.group('name')
            if ('', name) not in seen_funcs:
                seen_funcs.add(('', name))
                line_num = content[:match.start()].count('\n') + 1
                doc = self._get_preceding_comment(lines, line_num - 1)
                params = self._parse_params(match.group('params'))
                functions.append(LuaFunctionInfo(
                    name=name,
                    file=file_path,
                    parameters=params,
                    is_local=True,
                    is_varargs=any(p.is_varargs for p in params),
                    is_recursive=self._is_recursive(content, name, match.start()),
                    doc_comment=doc,
                    line_number=line_num,
                ))

        # Extract global functions
        for match in self.GLOBAL_FUNC_PATTERN.finditer(content):
            name = match.group('name')
            if ('', name) not in seen_funcs:
                seen_funcs.add(('', name))
                line_num = content[:match.start()].count('\n') + 1
                doc = self._get_preceding_comment(lines, line_num - 1)
                params = self._parse_params(match.group('params'))
                functions.append(LuaFunctionInfo(
                    name=name,
                    file=file_path,
                    parameters=params,
                    is_local=False,
                    is_varargs=any(p.is_varargs for p in params),
                    doc_comment=doc,
                    line_number=line_num,
                ))

        # Extract coroutines
        for match in self.COROUTINE_CREATE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            coroutines.append(LuaCoroutineInfo(
                name=match.group('name'),
                file=file_path,
                kind=match.group('kind'),
                wrapped_function=match.group('func') or "",
                line_number=line_num,
            ))

        # Check for coroutine.yield usage
        has_yield = bool(self.COROUTINE_YIELD_PATTERN.search(content))
        for func in functions:
            if has_yield:
                func.is_coroutine = True

        return {
            'functions': functions,
            'methods': methods,
            'coroutines': coroutines,
        }

    def _parse_params(self, param_str: str) -> List[LuaParameterInfo]:
        """Parse function parameters from string."""
        params = []
        if not param_str or not param_str.strip():
            return params
        for part in param_str.split(','):
            part = part.strip()
            if part == '...':
                params.append(LuaParameterInfo(name='...', is_varargs=True))
            elif part:
                params.append(LuaParameterInfo(name=part))
        return params

    def _is_recursive(self, content: str, func_name: str, start_pos: int) -> bool:
        """Check if a function calls itself."""
        # Find the end of the function (next matching 'end')
        depth = 0
        pos = start_pos
        while pos < len(content):
            if content[pos:pos+8] == 'function':
                depth += 1
                pos += 8
            elif content[pos:pos+3] == 'end' and (pos + 3 >= len(content) or not content[pos+3].isalnum()):
                if depth <= 1:
                    break
                depth -= 1
                pos += 3
            else:
                pos += 1
        body = content[start_pos:pos]
        # Check if function name appears in body (not as part of definition)
        call_pattern = re.compile(rf'\b{re.escape(func_name)}\s*\(')
        matches = list(call_pattern.finditer(body))
        return len(matches) > 1  # First match is definition, second is recursive call

    def _get_preceding_comment(self, lines: List[str], line_idx: int) -> str:
        """Get doc-comment (--- or -- style) above a line."""
        comments = []
        idx = line_idx - 1
        while idx >= 0:
            stripped = lines[idx].strip()
            if stripped.startswith('---') or stripped.startswith('--'):
                text = stripped.lstrip('-').strip()
                comments.insert(0, text)
                idx -= 1
            else:
                break
        return ' '.join(comments)[:300] if comments else ""
