"""
R Function Extractor for CodeTrellis

Extracts function definitions from R source code:
- Regular function definitions (name <- function(...))
- S3 method definitions (method.class <- function(...))
- Lambda/anonymous functions (\\(x) x + 1 in R 4.1+)
- Operator definitions (%op% <- function(...))
- Exported vs internal functions
- Roxygen documentation parsing
- Function parameters with defaults
- Pipe chain analysis (|>, %>%)

Supports: R 2.x through R 4.4+
Part of CodeTrellis v4.26 - R Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RParameterInfo:
    """Information about an R function parameter."""
    name: str
    type: str = ""  # From Roxygen @param annotation
    default_value: Optional[str] = None
    has_default: bool = False
    is_dots: bool = False  # ... parameter


@dataclass
class RFunctionInfo:
    """Information about an R function."""
    name: str
    parameters: List[RParameterInfo] = field(default_factory=list)
    return_type: str = ""  # From Roxygen @return
    is_exported: bool = False
    is_s3_method: bool = False
    s3_generic: str = ""  # e.g., "print" from print.MyClass
    s3_class: str = ""  # e.g., "MyClass" from print.MyClass
    is_operator: bool = False  # %op%
    is_lambda: bool = False  # \\(x) style
    is_recursive: bool = False
    is_internal: bool = False  # starts with .
    uses_nse: bool = False  # Non-Standard Evaluation (substitute, deparse, enquo)
    decorators: List[str] = field(default_factory=list)  # Roxygen tags
    roxygen_tags: Dict[str, str] = field(default_factory=dict)
    complexity: str = "simple"  # simple, moderate, complex
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None
    package: str = ""
    calls: List[str] = field(default_factory=list)  # Functions called within


@dataclass
class RPipeChainInfo:
    """Information about a pipe chain (|> or %>%)."""
    start_function: str
    chain_functions: List[str] = field(default_factory=list)
    pipe_type: str = "|>"  # |> (base) or %>% (magrittr)
    file: str = ""
    line_number: int = 0

    @property
    def length(self) -> int:
        """Total number of steps in the pipe chain (start + chain functions)."""
        return 1 + len(self.chain_functions)


class RFunctionExtractor:
    """
    Extracts R function definitions from source code.

    Detects:
    - Standard function assignments: name <- function(...)
    - S3 method patterns: generic.class <- function(...)
    - Operators: `%op%` <- function(...)
    - Lambda syntax: \\(x) x + 1 (R 4.1+)
    - Roxygen documentation (@param, @return, @export, @examples)
    - NSE usage (substitute, deparse, quo, enquo, !!, {{)
    - Pipe chains (|>, %>%)
    """

    # Standard function definition: name <- function(...)  or  name = function(...)
    FUNC_DEF_PATTERN = re.compile(
        r'^(\s*)([\w.]+)\s*(?:<-|=)\s*function\s*\((.*?)\)',
        re.MULTILINE | re.DOTALL
    )

    # Lambda function (R 4.1+): \(x) expr
    LAMBDA_PATTERN = re.compile(
        r'\\\s*\((.*?)\)\s*(?:\{|[^\n{])',
        re.MULTILINE
    )

    # Operator definition: `%op%` <- function(...)
    OPERATOR_PATTERN = re.compile(
        r'[`"\'](%[^%\s]+%)[`"\']\s*(?:<-|=)\s*function\s*\((.*?)\)',
        re.MULTILINE | re.DOTALL
    )

    # S3 method pattern: generic.class
    S3_METHOD_PATTERN = re.compile(
        r'^([\w]+)\.([\w.]+)\s*(?:<-|=)\s*function\s*\(',
        re.MULTILINE
    )

    # Roxygen tags
    ROXYGEN_EXPORT = re.compile(r"#'\s*@export")
    ROXYGEN_PARAM = re.compile(r"#'\s*@param\s+(\w+)\s+(.*)")
    ROXYGEN_RETURN = re.compile(r"#'\s*@return\s+(.*)")
    ROXYGEN_TITLE = re.compile(r"#'\s*@title\s+(.*)")
    ROXYGEN_DESCRIPTION = re.compile(r"#'\s+(\S.*)")
    ROXYGEN_TAG = re.compile(r"#'\s*@(\w+)\s*(.*)")

    # NSE patterns
    NSE_PATTERNS = [
        re.compile(r'\bsubstitute\s*\('),
        re.compile(r'\bdeparse\s*\('),
        re.compile(r'\benquo\s*\('),
        re.compile(r'\benquos\s*\('),
        re.compile(r'\bquo\s*\('),
        re.compile(r'\bquos\s*\('),
        re.compile(r'\b!!\s*'),
        re.compile(r'\{\{'),
        re.compile(r'\brlang::'),
        re.compile(r'\bmatch\.arg\s*\('),
    ]

    # Pipe patterns
    PIPE_BASE = re.compile(r'\|>')
    PIPE_MAGRITTR = re.compile(r'%>%')

    # Common S3 generics to recognize
    KNOWN_S3_GENERICS = {
        'print', 'summary', 'plot', 'format', 'as', 'is', 'c',
        'str', 'length', 'dim', 'names', 'subset', 'transform',
        'merge', 'predict', 'coef', 'residuals', 'fitted',
        'update', 'anova', 'confint', 'vcov', 'logLik', 'AIC', 'BIC',
        'model', 'tidy', 'glance', 'augment',
    }

    # NAMESPACE export pattern
    NAMESPACE_EXPORT = re.compile(r'export\s*\(\s*(\w+)')

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all R function definitions from source code."""
        result = {
            "functions": [],
            "pipe_chains": [],
        }

        lines = content.split('\n')

        # Check for NAMESPACE exports (if this is a NAMESPACE file)
        exported_names = set()
        if file_path.endswith('NAMESPACE'):
            for m in self.NAMESPACE_EXPORT.finditer(content):
                exported_names.add(m.group(1))
            return result  # NAMESPACE files don't have function defs

        # Extract roxygen blocks and associate with functions
        roxygen_blocks = self._extract_roxygen_blocks(lines)

        # Extract standard function definitions
        result["functions"].extend(
            self._extract_functions(content, file_path, lines, roxygen_blocks, exported_names)
        )

        # Extract operator definitions
        result["functions"].extend(
            self._extract_operators(content, file_path, lines, roxygen_blocks)
        )

        # Extract lambda function assignments
        result["functions"].extend(
            self._extract_lambdas(content, file_path, lines)
        )

        # Extract pipe chains
        result["pipe_chains"].extend(
            self._extract_pipe_chains(content, file_path)
        )

        return result

    def _extract_roxygen_blocks(self, lines: List[str]) -> Dict[int, Dict]:
        """Extract roxygen documentation blocks and their ending line numbers."""
        blocks = {}
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith("#'"):
                block_start = i
                tags = {}
                params = {}
                is_exported = False
                title = ""
                description_lines = []

                while i < len(lines) and lines[i].strip().startswith("#'"):
                    line = lines[i].strip()

                    export_m = self.ROXYGEN_EXPORT.match(line)
                    if export_m:
                        is_exported = True

                    param_m = self.ROXYGEN_PARAM.match(line)
                    if param_m:
                        params[param_m.group(1)] = param_m.group(2)

                    return_m = self.ROXYGEN_RETURN.match(line)
                    if return_m:
                        tags['return'] = return_m.group(1)

                    tag_m = self.ROXYGEN_TAG.match(line)
                    if tag_m:
                        tag_name = tag_m.group(1)
                        tag_val = tag_m.group(2)
                        tags[tag_name] = tag_val
                    elif not line.strip().startswith("#' @"):
                        desc = line.strip()[2:].strip()
                        if desc:
                            description_lines.append(desc)

                    i += 1

                # Store the block keyed by the line AFTER it ends (the function def line)
                blocks[i] = {
                    "is_exported": is_exported,
                    "params": params,
                    "tags": tags,
                    "title": title or (description_lines[0] if description_lines else ""),
                    "description": '\n'.join(description_lines),
                }
            else:
                i += 1
        return blocks

    def _extract_functions(self, content: str, file_path: str, lines: List[str],
                           roxygen_blocks: Dict, exported_names: set) -> List[RFunctionInfo]:
        """Extract standard function definitions."""
        functions = []
        seen = set()

        for m in self.FUNC_DEF_PATTERN.finditer(content):
            name = m.group(2)
            params_str = m.group(3)
            line_num = content[:m.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            func = RFunctionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
            )

            # Parse parameters
            func.parameters = self._parse_parameters(params_str)

            # Check if internal (starts with .)
            if name.startswith('.'):
                func.is_internal = True

            # Check S3 method pattern
            s3_m = re.match(r'^([\w]+)\.([\w.]+)$', name)
            if s3_m and s3_m.group(1) in self.KNOWN_S3_GENERICS:
                func.is_s3_method = True
                func.s3_generic = s3_m.group(1)
                func.s3_class = s3_m.group(2)

            # Associate with roxygen block
            # line_num is 1-based, roxygen_blocks keys are 0-based line indices
            roxygen = roxygen_blocks.get(line_num - 1)
            if roxygen:
                func.is_exported = roxygen.get("is_exported", False)
                func.doc_comment = roxygen.get("description", "")
                func.return_type = roxygen.get("tags", {}).get("return", "")
                func.roxygen_tags = roxygen.get("tags", {})
                # Enrich parameter types from roxygen
                for p in func.parameters:
                    if p.name in roxygen.get("params", {}):
                        p.type = roxygen["params"][p.name]

            # Check if exported by name
            if name in exported_names:
                func.is_exported = True

            # Check NSE usage in function body
            func_body = self._get_function_body(content, m.end())
            if func_body:
                for nse_pat in self.NSE_PATTERNS:
                    if nse_pat.search(func_body):
                        func.uses_nse = True
                        break

                # Estimate complexity
                func.complexity = self._estimate_complexity(func_body)

                # Extract function calls
                func.calls = self._extract_calls(func_body)

            functions.append(func)
        return functions

    def _extract_operators(self, content: str, file_path: str, lines: List[str],
                           roxygen_blocks: Dict) -> List[RFunctionInfo]:
        """Extract operator definitions (%op%)."""
        operators = []
        for m in self.OPERATOR_PATTERN.finditer(content):
            name = m.group(1)
            params_str = m.group(2)
            line_num = content[:m.start()].count('\n') + 1

            func = RFunctionInfo(
                name=name,
                is_operator=True,
                file=file_path,
                line_number=line_num,
                parameters=self._parse_parameters(params_str),
            )

            roxygen = roxygen_blocks.get(line_num - 1)
            if roxygen:
                func.is_exported = roxygen.get("is_exported", False)
                func.doc_comment = roxygen.get("description", "")

            operators.append(func)
        return operators

    def _extract_lambdas(self, content: str, file_path: str, lines: List[str]) -> List[RFunctionInfo]:
        """Extract lambda function assignments (R 4.1+): name <- \\(x) expr."""
        lambdas = []
        # Pattern: name <- \(params) body
        lambda_assign = re.compile(
            r'^(\s*)([\w.]+)\s*(?:<-|=)\s*\\\s*\((.*?)\)',
            re.MULTILINE
        )
        for m in lambda_assign.finditer(content):
            name = m.group(2)
            params_str = m.group(3)
            line_num = content[:m.start()].count('\n') + 1

            func = RFunctionInfo(
                name=name,
                is_lambda=True,
                file=file_path,
                line_number=line_num,
                parameters=self._parse_parameters(params_str),
            )
            lambdas.append(func)
        return lambdas

    def _extract_pipe_chains(self, content: str, file_path: str) -> List[RPipeChainInfo]:
        """Extract significant pipe chains (single-line and multi-line)."""
        chains = []
        lines = content.split('\n')

        # Merge multi-line pipe chains into logical blocks
        merged_blocks = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.rstrip()
            if '|>' in stripped or '%>%' in stripped:
                block_start = i
                block = stripped
                # Continue accumulating lines while the current line ends with a pipe
                # or the next line starts with a pipe or continuation
                while i < len(lines):
                    current = lines[i].rstrip()
                    if i > block_start:
                        block += ' ' + current.lstrip()
                    # Check if this line ends with a pipe operator (indicating continuation)
                    if current.rstrip().endswith('|>') or current.rstrip().endswith('%>%'):
                        i += 1
                        continue
                    # Check if next line starts with a pipe (continuation from previous)
                    if i + 1 < len(lines):
                        next_stripped = lines[i + 1].strip()
                        if next_stripped.startswith('|>') or next_stripped.startswith('%>%'):
                            i += 1
                            continue
                    break
                merged_blocks.append((block_start + 1, block))  # 1-based line number
                i += 1
            else:
                i += 1

        for line_num, block in merged_blocks:
            pipe_type = '|>' if '|>' in block else '%>%'
            parts = re.split(r'\|>|%>%', block)
            funcs = []
            for part in parts:
                func_m = re.search(r'(\w+)\s*\(', part.strip())
                if func_m:
                    funcs.append(func_m.group(1))
            if len(funcs) >= 2:
                chains.append(RPipeChainInfo(
                    start_function=funcs[0] if funcs else "",
                    chain_functions=funcs[1:],
                    pipe_type=pipe_type,
                    file=file_path,
                    line_number=line_num,
                ))
        return chains

    def _parse_parameters(self, params_str: str) -> List[RParameterInfo]:
        """Parse function parameter string into structured info."""
        params = []
        if not params_str or not params_str.strip():
            return params

        # Split on commas, respecting nested structures
        parts = self._split_params(params_str)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if part == '...':
                params.append(RParameterInfo(name='...', is_dots=True))
                continue

            # name = default_value
            eq_match = re.match(r'(\w+)\s*=\s*(.*)', part, re.DOTALL)
            if eq_match:
                params.append(RParameterInfo(
                    name=eq_match.group(1),
                    default_value=eq_match.group(2).strip(),
                    has_default=True,
                ))
            else:
                name_match = re.match(r'(\w+)', part)
                if name_match:
                    params.append(RParameterInfo(name=name_match.group(1)))

        return params

    def _split_params(self, params_str: str) -> List[str]:
        """Split parameter string on commas, respecting nested parens/brackets."""
        parts = []
        depth = 0
        current = []
        for c in params_str:
            if c in ('(', '[', '{'):
                depth += 1
                current.append(c)
            elif c in (')', ']', '}'):
                depth -= 1
                current.append(c)
            elif c == ',' and depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                current.append(c)
        if current:
            parts.append(''.join(current))
        return parts

    def _get_function_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract function body after the parameter list."""
        # Find the opening brace
        idx = start_pos
        while idx < len(content) and content[idx] in (' ', '\t', '\n', '\r'):
            idx += 1

        if idx < len(content) and content[idx] == '{':
            depth = 0
            i = idx
            while i < len(content):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        return content[idx:i + 1]
                i += 1

        return None

    def _estimate_complexity(self, body: str) -> str:
        """Estimate function complexity from body."""
        score = 0
        score += len(re.findall(r'\bif\s*\(', body))
        score += len(re.findall(r'\belse\b', body))
        score += len(re.findall(r'\bfor\s*\(', body))
        score += len(re.findall(r'\bwhile\s*\(', body))
        score += len(re.findall(r'\brepeat\b', body))
        score += len(re.findall(r'\bswitch\s*\(', body))
        score += len(re.findall(r'\btryCatch\s*\(', body))
        score += len(re.findall(r'\btryCatch\s*\(', body))
        score += len(re.findall(r'\bwithCallingHandlers\s*\(', body))

        if score <= 2:
            return "simple"
        elif score <= 6:
            return "moderate"
        else:
            return "complex"

    def _extract_calls(self, body: str) -> List[str]:
        """Extract function call names from body."""
        calls = set()
        for m in re.finditer(r'\b(\w+(?:\.\w+)*)\s*\(', body):
            name = m.group(1)
            # Skip control flow keywords
            if name not in ('if', 'for', 'while', 'function', 'switch', 'return',
                            'repeat', 'next', 'break', 'tryCatch', 'withCallingHandlers'):
                calls.add(name)
        return sorted(list(calls))[:20]  # Limit to 20 most important
