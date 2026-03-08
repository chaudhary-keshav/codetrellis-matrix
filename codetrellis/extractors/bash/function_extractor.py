"""
Bash/Shell Function Extractor for CodeTrellis

Extracts function definitions from Bash/Shell source files.

Supports:
- POSIX function syntax: func_name() { ... }
- Bash function keyword: function func_name { ... }
- Combined syntax: function func_name() { ... }
- Local variable declarations inside functions
- Parameter references ($1, $2, $@, $*, $#)
- Return statements and exit codes
- Function documentation (preceding comments)

Bash versions: sh, bash (2.x-5.x), zsh, ksh, dash, ash, fish (partial)

Part of CodeTrellis v4.18 - Bash/Shell Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BashParameterInfo:
    """Information about a function parameter reference."""
    name: str = ""                 # $1, $2, $@, $*, $#, named via getopts
    position: int = 0              # Positional index (1-based)
    description: str = ""          # From comments/docs
    is_required: bool = False
    default_value: str = ""


@dataclass
class BashFunctionInfo:
    """Information about a Bash function."""
    name: str = ""
    line_number: int = 0
    end_line: int = 0
    syntax: str = "posix"          # "posix", "bash_keyword", "combined"
    local_variables: List[str] = field(default_factory=list)
    parameters: List[BashParameterInfo] = field(default_factory=list)
    calls_functions: List[str] = field(default_factory=list)
    return_codes: List[int] = field(default_factory=list)
    has_subshell: bool = False
    has_pipe: bool = False
    body_lines: int = 0
    docstring: str = ""            # Preceding comment block
    is_exported: bool = False      # export -f
    is_recursive: bool = False
    complexity: int = 0            # Cyclomatic complexity estimate


class BashFunctionExtractor:
    """
    Extracts function definitions from Bash/Shell scripts.

    Handles all major function definition syntaxes across bash versions.
    """

    # Function definition patterns
    # POSIX: name() { ... }
    POSIX_FUNC = re.compile(
        r'^[ \t]*(\w[\w-]*)[ \t]*\(\)[ \t]*\{',
        re.MULTILINE
    )

    # Bash keyword: function name { ... }
    BASH_KEYWORD_FUNC = re.compile(
        r'^[ \t]*function[ \t]+(\w[\w-]*)[ \t]*(?:\(\))?[ \t]*\{',
        re.MULTILINE
    )

    # Combined pattern for both syntaxes (used for finding line numbers)
    ALL_FUNC_PATTERN = re.compile(
        r'^[ \t]*(?:function[ \t]+)?(\w[\w-]*)[ \t]*\(\)[ \t]*\{|'
        r'^[ \t]*function[ \t]+(\w[\w-]*)[ \t]*\{',
        re.MULTILINE
    )

    # Local variable declarations
    LOCAL_VAR = re.compile(r'\blocal\s+(\w+)(?:\s*=)?')

    # declare/typeset variables
    DECLARE_VAR = re.compile(r'\b(?:declare|typeset)\s+(?:-[a-zA-Z]+\s+)*(\w+)')

    # Parameter references
    PARAM_REF = re.compile(r'\$\{?(\d+|[@*#?!])\}?')

    # getopts pattern
    GETOPTS_PATTERN = re.compile(r'getopts\s+"([^"]+)"\s+(\w+)')

    # Return statement
    RETURN_PATTERN = re.compile(r'\breturn\s+(\d+)')

    # Subshell detection
    SUBSHELL_PATTERN = re.compile(r'\$\(|`[^`]+`')

    # Pipe detection
    PIPE_PATTERN = re.compile(r'[^|]\|[^|]')

    # export -f
    EXPORT_FUNC = re.compile(r'export\s+-f\s+(\w[\w-]*)')

    # Function call pattern (approximate)
    FUNC_CALL = re.compile(r'\b(\w[\w-]*)\b')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all function definitions from Bash/Shell source.

        Args:
            content: Shell script content
            file_path: Path to source file

        Returns:
            Dict with 'functions' key containing list of BashFunctionInfo
        """
        functions = []
        lines = content.split('\n')

        # Find all exported functions
        exported_funcs = set()
        for m in self.EXPORT_FUNC.finditer(content):
            exported_funcs.add(m.group(1))

        # Collect all function names for cross-reference
        all_func_names = set()
        for m in self.ALL_FUNC_PATTERN.finditer(content):
            name = m.group(1) or m.group(2)
            if name:
                all_func_names.add(name)

        # Extract each function
        for match in self.ALL_FUNC_PATTERN.finditer(content):
            func_name = match.group(1) or match.group(2)
            if not func_name:
                continue

            start_pos = match.start()
            line_num = content[:start_pos].count('\n') + 1

            # Determine syntax type
            match_str = match.group(0).strip()
            if match_str.startswith('function') and '()' in match_str:
                syntax = "combined"
            elif match_str.startswith('function'):
                syntax = "bash_keyword"
            else:
                syntax = "posix"

            # Find function body (brace-balanced)
            body, end_line = self._extract_body(content, match.end() - 1)

            info = BashFunctionInfo(
                name=func_name,
                line_number=line_num,
                end_line=end_line if end_line else line_num,
                syntax=syntax,
                is_exported=func_name in exported_funcs,
            )

            if body:
                info.body_lines = body.count('\n') + 1

                # Extract local variables
                for lv in self.LOCAL_VAR.finditer(body):
                    info.local_variables.append(lv.group(1))
                for dv in self.DECLARE_VAR.finditer(body):
                    info.local_variables.append(dv.group(1))

                # Extract parameter references
                param_positions = set()
                for pr in self.PARAM_REF.finditer(body):
                    ref = pr.group(1)
                    if ref.isdigit():
                        pos = int(ref)
                        if pos > 0 and pos not in param_positions:
                            param_positions.add(pos)
                            info.parameters.append(BashParameterInfo(
                                name=f"${ref}",
                                position=pos,
                                is_required=True,
                            ))
                    elif ref in ('@', '*'):
                        info.parameters.append(BashParameterInfo(
                            name=f"${ref}", position=0,
                        ))

                # Extract getopts usage
                for gm in self.GETOPTS_PATTERN.finditer(body):
                    optstring = gm.group(1)
                    for ch in optstring:
                        if ch != ':':
                            info.parameters.append(BashParameterInfo(
                                name=f"-{ch}",
                                position=0,
                            ))

                # Return codes
                for rm in self.RETURN_PATTERN.finditer(body):
                    code = int(rm.group(1))
                    if code not in info.return_codes:
                        info.return_codes.append(code)

                # Subshell and pipe detection
                info.has_subshell = bool(self.SUBSHELL_PATTERN.search(body))
                info.has_pipe = bool(self.PIPE_PATTERN.search(body))

                # Cross-function calls
                called = set()
                for fc in self.FUNC_CALL.finditer(body):
                    called_name = fc.group(1)
                    if called_name in all_func_names and called_name != func_name:
                        called.add(called_name)
                info.calls_functions = sorted(called)

                # Recursion check
                info.is_recursive = func_name in [fc.group(1) for fc in self.FUNC_CALL.finditer(body)]

                # Complexity estimate (ifs, cases, loops)
                info.complexity = self._estimate_complexity(body)

            # Extract preceding docstring (comments)
            info.docstring = self._extract_docstring(lines, line_num - 1)

            functions.append(info)

        return {'functions': functions}

    def _extract_body(self, content: str, brace_pos: int):
        """Extract brace-balanced function body starting at opening brace."""
        if brace_pos >= len(content) or content[brace_pos] != '{':
            return "", 0

        depth = 0
        i = brace_pos
        in_string = False
        string_char = ''
        in_comment = False

        while i < len(content):
            ch = content[i]

            if in_comment:
                if ch == '\n':
                    in_comment = False
                i += 1
                continue

            if in_string:
                if ch == '\\' and i + 1 < len(content):
                    i += 2
                    continue
                if ch == string_char:
                    in_string = False
                i += 1
                continue

            if ch == '#' and (i == 0 or content[i - 1] != '$'):
                in_comment = True
                i += 1
                continue

            if ch in ('"', "'"):
                in_string = True
                string_char = ch
                i += 1
                continue

            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    body = content[brace_pos + 1:i]
                    end_line = content[:i].count('\n') + 1
                    return body, end_line

            i += 1

        return "", 0

    def _estimate_complexity(self, body: str) -> int:
        """Estimate cyclomatic complexity of a function body."""
        complexity = 1  # Base
        # Count decision points
        patterns = [
            r'\bif\b', r'\belif\b', r'\bwhile\b', r'\bfor\b',
            r'\buntil\b', r'\bcase\b', r'\b\|\|\b', r'\b&&\b',
        ]
        for pat in patterns:
            complexity += len(re.findall(pat, body))
        return complexity

    def _extract_docstring(self, lines: List[str], func_line_idx: int) -> str:
        """Extract comment block preceding a function definition."""
        doc_lines = []
        i = func_line_idx - 1
        while i >= 0:
            line = lines[i].strip()
            if line.startswith('#'):
                doc_lines.insert(0, line.lstrip('#').strip())
                i -= 1
            else:
                break
        return '\n'.join(doc_lines) if doc_lines else ""
