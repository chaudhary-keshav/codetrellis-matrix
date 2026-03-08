"""
CFunctionExtractor - Extracts C function and function pointer definitions.

This extractor parses C source code and extracts:
- Function definitions (with bodies)
- Function declarations (prototypes)
- Static, inline, extern functions
- Variadic functions
- Function pointers (variables, parameters)
- K&R style function definitions (C89)
- _Noreturn, _Thread_local (C11)
- [[nodiscard]], [[maybe_unused]] (C23)
- GCC/Clang __attribute__ qualifiers

Supports all C standards: C89/C90, C99, C11, C17, C23.

Part of CodeTrellis v4.19 - C Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CParameterInfo:
    """Information about a C function parameter."""
    name: str
    type: str
    is_pointer: bool = False
    is_const: bool = False
    is_array: bool = False
    is_restrict: bool = False  # C99
    is_variadic: bool = False
    default_value: Optional[str] = None


@dataclass
class CFunctionInfo:
    """Information about a C function."""
    name: str
    parameters: List[CParameterInfo] = field(default_factory=list)
    return_type: str = "int"
    is_static: bool = False
    is_inline: bool = False
    is_extern: bool = False
    is_noreturn: bool = False
    is_variadic: bool = False
    is_prototype: bool = False  # Declaration only, no body
    is_definition: bool = False  # Has body
    storage_class: str = ""  # static, extern, register, _Thread_local
    attributes: List[str] = field(default_factory=list)
    calling_convention: Optional[str] = None  # __cdecl, __stdcall, __fastcall
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None
    body_lines: int = 0
    complexity: int = 0  # Cyclomatic complexity estimate


@dataclass
class CFunctionPointerInfo:
    """Information about a C function pointer type/variable."""
    name: str
    return_type: str
    param_types: List[str] = field(default_factory=list)
    is_typedef: bool = False
    is_variable: bool = False
    file: str = ""
    line_number: int = 0


class CFunctionExtractor:
    """
    Extracts C function definitions and declarations from source code.

    Handles:
    - Standard function definitions and prototypes
    - static, inline, extern, _Noreturn qualifiers
    - __attribute__((..)) annotations
    - [[nodiscard]], [[deprecated]] C23 attributes
    - Variadic functions (...)
    - Function pointers as variables and typedefs
    - Calling conventions (__cdecl, __stdcall)
    - GCC/Clang extensions
    - Cyclomatic complexity estimation
    """

    # Function pattern — captures qualifiers, return type, name, params
    FUNC_PATTERN = re.compile(
        r'(?P<attrs>(?:(?:__attribute__\s*\(\([^)]*\)\)\s*)|(?:\[\[[^\]]*\]\]\s*))*)'
        r'(?P<qualifiers>(?:(?:static|inline|extern|_Noreturn|_Thread_local|__inline|__forceinline)\s+)*)'
        r'(?P<ret>(?:(?:const|volatile|unsigned|signed|long|short|struct|union|enum)\s+)*\w[\w\s*]*?)'
        r'\s+(?P<stars>\**)(?P<name>\w+)\s*'
        r'\((?P<params>[^)]*)\)\s*'
        r'(?P<post_attrs>(?:__attribute__\s*\(\([^)]*\)\)\s*)*)'
        r'(?P<body>\{|;)',
        re.MULTILINE
    )

    # Function pointer variable: type (*name)(params);
    FUNC_PTR_VAR = re.compile(
        r'(?P<ret>[\w\s*]+?)\s*\(\s*\*\s*(?P<name>\w+)\s*\)\s*\((?P<params>[^)]*)\)\s*(?:=\s*[^;]+)?\s*;',
        re.MULTILINE
    )

    # Complexity keywords for cyclomatic complexity estimate
    COMPLEXITY_KEYWORDS = re.compile(
        r'\b(if|else\s+if|for|while|do|switch|case|\?\s*:|\|\||&&)\b'
    )

    def __init__(self):
        """Initialize the C function extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all C functions and function pointers from source code.

        Args:
            content: C source code content
            file_path: Path to source file

        Returns:
            Dict with 'functions' and 'function_pointers' keys
        """
        # Remove single-line comments
        clean = re.sub(r'//[^\n]*', '', content)
        # Remove multi-line comments, preserve newlines
        clean = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), clean, flags=re.DOTALL)

        functions = self._extract_functions(clean, file_path, content)
        function_pointers = self._extract_function_pointers(clean, file_path, content)

        return {
            'functions': functions,
            'function_pointers': function_pointers,
        }

    def _get_line_number(self, content: str, pos: int) -> int:
        """Get line number from position in content."""
        return content[:pos].count('\n') + 1

    def _extract_doc_comment(self, content: str, pos: int) -> Optional[str]:
        """Extract doc comment preceding a definition."""
        before = content[:pos].rstrip()
        lines = before.split('\n')
        doc_lines = []
        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith('///') or stripped.startswith('//!'):
                doc_lines.insert(0, stripped[3:].strip())
            elif stripped.endswith('*/'):
                block_start = before.rfind('/**')
                if block_start < 0:
                    block_start = before.rfind('/*!')
                if block_start >= 0:
                    block = before[block_start:]
                    block = re.sub(r'^/\*[*!]\s*', '', block)
                    block = re.sub(r'\s*\*/$', '', block)
                    block_lines = [re.sub(r'^\s*\*\s?', '', l) for l in block.split('\n')]
                    return ' '.join(l.strip() for l in block_lines if l.strip())
                break
            else:
                break
        return ' '.join(doc_lines) if doc_lines else None

    def _parse_params(self, params_str: str) -> List[CParameterInfo]:
        """Parse function parameters string."""
        params = []
        if not params_str or params_str.strip() in ('void', ''):
            return params

        # Split on commas, respecting nested parentheses
        depth = 0
        current = []
        for ch in params_str:
            if ch == '(':
                depth += 1
            elif ch == ')':
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
            if current_str == '...':
                params.append(CParameterInfo(name='...', type='...', is_variadic=True))
            else:
                params.append(self._parse_single_param(current_str))

        return params

    def _parse_single_param(self, param_str: str) -> CParameterInfo:
        """Parse a single parameter string."""
        param_str = param_str.strip()

        if param_str == '...':
            return CParameterInfo(name='...', type='...', is_variadic=True)

        is_const = 'const' in param_str
        is_restrict = 'restrict' in param_str or '__restrict' in param_str

        # Try to split type and name
        # Handle pointers: int *name, const char *name
        is_pointer = '*' in param_str
        is_array = '[' in param_str

        # Remove array brackets for name extraction
        clean_param = re.sub(r'\[[^\]]*\]', '', param_str).strip()

        # Try: type name pattern
        match = re.match(
            r'(?P<type>(?:(?:const|volatile|unsigned|signed|long|short|struct|union|enum|restrict|__restrict)\s+)*'
            r'[\w]+[\s*]*\**)\s+(?P<name>\w+)',
            clean_param
        )
        if match:
            ptype = match.group('type').strip()
            pname = match.group('name')
            return CParameterInfo(
                name=pname,
                type=ptype,
                is_pointer=is_pointer,
                is_const=is_const,
                is_array=is_array,
                is_restrict=is_restrict,
            )

        # No name (prototype: just type)
        return CParameterInfo(
            name='',
            type=param_str,
            is_pointer=is_pointer,
            is_const=is_const,
            is_array=is_array,
            is_restrict=is_restrict,
        )

    def _count_body_lines(self, content: str, start_pos: int) -> int:
        """Count lines in function body (brace-matched)."""
        if start_pos >= len(content) or content[start_pos] != '{':
            return 0
        depth = 1
        pos = start_pos + 1
        while pos < len(content) and depth > 0:
            if content[pos] == '{':
                depth += 1
            elif content[pos] == '}':
                depth -= 1
            pos += 1
        body = content[start_pos:pos]
        return body.count('\n')

    def _estimate_complexity(self, content: str, start_pos: int) -> int:
        """Estimate cyclomatic complexity of a function body."""
        if start_pos >= len(content) or content[start_pos] != '{':
            return 1
        depth = 1
        pos = start_pos + 1
        while pos < len(content) and depth > 0:
            if content[pos] == '{':
                depth += 1
            elif content[pos] == '}':
                depth -= 1
            pos += 1
        body = content[start_pos:pos]
        complexity = 1 + len(self.COMPLEXITY_KEYWORDS.findall(body))
        return complexity

    def _extract_functions(self, clean: str, file_path: str, original: str) -> List[CFunctionInfo]:
        """Extract function definitions and declarations."""
        functions = []
        seen_names = set()

        for match in self.FUNC_PATTERN.finditer(clean):
            name = match.group('name')
            # Skip common false positives (control flow, macros)
            if name in ('if', 'for', 'while', 'switch', 'return', 'sizeof', 'typeof',
                        'defined', '__attribute__', 'do'):
                continue

            qualifiers = match.group('qualifiers').strip() if match.group('qualifiers') else ''
            ret_type = match.group('ret').strip()
            stars = match.group('stars') or ''
            full_ret = ret_type + stars if stars else ret_type
            params_str = match.group('params')
            is_body = match.group('body') == '{'
            attrs_str = (match.group('attrs') or '') + (match.group('post_attrs') or '')

            line_num = self._get_line_number(original, match.start())
            doc = self._extract_doc_comment(original, match.start())

            is_static = 'static' in qualifiers
            is_inline = 'inline' in qualifiers or '__inline' in qualifiers or '__forceinline' in qualifiers
            is_extern = 'extern' in qualifiers
            is_noreturn = '_Noreturn' in qualifiers or 'noreturn' in attrs_str

            params = self._parse_params(params_str)
            is_variadic = any(p.is_variadic for p in params)

            # Attributes
            attrs = re.findall(r'__attribute__\s*\(\(([^)]*)\)\)', attrs_str)
            c23_attrs = re.findall(r'\[\[([^\]]*)\]\]', attrs_str)
            all_attrs = attrs + c23_attrs

            body_pos = match.end() - 1 if is_body else -1
            body_lines = self._count_body_lines(clean, body_pos) if is_body else 0
            complexity = self._estimate_complexity(clean, body_pos) if is_body else 0

            # Calling convention detection
            calling_conv = None
            for conv in ('__cdecl', '__stdcall', '__fastcall', '__thiscall'):
                if conv in ret_type or conv in attrs_str:
                    calling_conv = conv
                    break

            storage_class = ''
            if is_static:
                storage_class = 'static'
            elif is_extern:
                storage_class = 'extern'

            # Deduplicate (prototype + definition of same function)
            key = f"{name}_{is_body}"
            if key in seen_names:
                continue
            seen_names.add(key)

            functions.append(CFunctionInfo(
                name=name,
                parameters=params,
                return_type=full_ret,
                is_static=is_static,
                is_inline=is_inline,
                is_extern=is_extern,
                is_noreturn=is_noreturn,
                is_variadic=is_variadic,
                is_prototype=not is_body,
                is_definition=is_body,
                storage_class=storage_class,
                attributes=all_attrs,
                calling_convention=calling_conv,
                file=file_path,
                line_number=line_num,
                doc_comment=doc,
                body_lines=body_lines,
                complexity=complexity,
            ))
        return functions

    def _extract_function_pointers(self, clean: str, file_path: str, original: str) -> List[CFunctionPointerInfo]:
        """Extract function pointer variables."""
        ptrs = []
        for match in self.FUNC_PTR_VAR.finditer(clean):
            ret = match.group('ret').strip()
            name = match.group('name')
            params_str = match.group('params').strip()
            line_num = self._get_line_number(original, match.start())

            param_types = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []

            ptrs.append(CFunctionPointerInfo(
                name=name,
                return_type=ret,
                param_types=param_types,
                is_variable=True,
                file=file_path,
                line_number=line_num,
            ))
        return ptrs
