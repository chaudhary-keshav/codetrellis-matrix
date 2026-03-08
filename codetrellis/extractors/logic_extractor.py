"""
Logic Extractor for CodeTrellis

Extracts implementation details and code logic from source files.
This addresses the limitation where CodeTrellis loses exact implementation details
and AI can't see specific code logic.

The Logic Extractor captures:
- Function bodies (compressed to key logic)
- Business logic patterns
- Algorithm implementations
- Control flow structures
- Key decision points
- Data transformations

Output is token-efficient while preserving semantic meaning.

Part of CodeTrellis v4.1 - Implementation Logic Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path


@dataclass
class LogicSnippet:
    """A captured piece of implementation logic."""
    name: str  # Function/method/class name
    file_path: str
    snippet_type: str  # 'function', 'method', 'class', 'algorithm', 'handler'
    signature: str  # Full signature
    logic_summary: str  # Compressed representation of logic
    key_operations: List[str] = field(default_factory=list)  # Important operations
    control_flow: List[str] = field(default_factory=list)  # if/for/while/try patterns
    api_calls: List[str] = field(default_factory=list)  # External/internal calls
    data_transforms: List[str] = field(default_factory=list)  # Data manipulations
    complexity_indicator: str = "simple"  # simple, moderate, complex
    line_count: int = 0
    line_number: int = 0


@dataclass
class LogicFileInfo:
    """Logic extraction results for a file."""
    file_path: str
    language: str  # 'typescript', 'python', etc.
    snippets: List[LogicSnippet] = field(default_factory=list)
    total_functions: int = 0
    complex_functions: int = 0  # Functions with high cyclomatic complexity


class LogicExtractor:
    """
    Extracts implementation logic from source code in a token-efficient manner.

    Strategy:
    1. Identify function/method bodies
    2. Extract key operations (assignments, calls, returns)
    3. Capture control flow patterns
    4. Summarize logic while preserving semantic meaning

    This allows AI to understand WHAT the code does, not just its signature.
    """

    # TypeScript/JavaScript patterns
    TS_FUNCTION_BODY = re.compile(
        r'(?:(?:async\s+)?function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]*)\s*=>|(\w+)\s*(?:<[^>]+>)?\s*\([^)]*\)\s*(?::\s*[^{]+)?)\s*\{',
        re.MULTILINE
    )

    TS_METHOD_BODY = re.compile(
        r'^\s*(?:(?:public|private|protected|static|async|readonly)\s+)*(\w+)\s*(?:<[^>]+>)?\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{',
        re.MULTILINE
    )

    # Python patterns
    PY_FUNCTION_DEF = re.compile(
        r'^(\s*)(async\s+)?def\s+(\w+)\s*\([^)]*\)(?:\s*->\s*[^:]+)?\s*:',
        re.MULTILINE
    )

    PY_CLASS_DEF = re.compile(
        r'^(\s*)class\s+(\w+)(?:\s*\([^)]*\))?\s*:',
        re.MULTILINE
    )

    # Common logic patterns to extract
    CONTROL_FLOW_KEYWORDS = {
        'typescript': ['if', 'else', 'for', 'while', 'switch', 'try', 'catch', 'finally', 'throw'],
        'python': ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'raise', 'with', 'match', 'case'],
        'go': ['if', 'else', 'for', 'range', 'switch', 'select', 'case', 'defer', 'go', 'return', 'panic', 'recover'],
    }

    # Go patterns
    GO_FUNC_DEF = re.compile(
        r'^func\s+(?:\(\s*(\w+)\s+\*?(\w+)\s*\)\s+)?(\w+)\s*\(([^)]*)\)(?:\s*(?:\(([^)]*)\)|(\S[^{]*?)))?\s*\{',
        re.MULTILINE
    )

    # API/Service call patterns
    API_CALL_PATTERN = re.compile(
        r'(?:this\.)?(?:http|fetch|axios|request|api)\s*\.\s*(get|post|put|patch|delete|request)\s*[<(]',
        re.IGNORECASE
    )

    # Data transformation patterns
    DATA_TRANSFORM_PATTERNS = [
        (r'\.map\s*\(', 'map'),
        (r'\.filter\s*\(', 'filter'),
        (r'\.reduce\s*\(', 'reduce'),
        (r'\.sort\s*\(', 'sort'),
        (r'\.find\s*\(', 'find'),
        (r'\.forEach\s*\(', 'forEach'),
        (r'Object\.keys\s*\(', 'Object.keys'),
        (r'Object\.values\s*\(', 'Object.values'),
        (r'Object\.entries\s*\(', 'Object.entries'),
        (r'Array\.from\s*\(', 'Array.from'),
        (r'\.pipe\s*\(', 'RxJS.pipe'),
        (r'\.subscribe\s*\(', 'RxJS.subscribe'),
        (r'await\s+', 'await'),
    ]

    def __init__(self, max_body_lines: int = 50, include_full_bodies: bool = False):
        """
        Initialize Logic Extractor.

        Args:
            max_body_lines: Max lines to capture per function (for summarization)
            include_full_bodies: If True, include complete function bodies (high token cost)
        """
        self.max_body_lines = max_body_lines
        self.include_full_bodies = include_full_bodies

    def extract_typescript(self, content: str, file_path: str = "") -> LogicFileInfo:
        """Extract logic from TypeScript/JavaScript content."""
        result = LogicFileInfo(file_path=file_path, language='typescript')

        # Find all function/method bodies
        snippets = []

        # Extract class methods
        class_pattern = re.compile(
            r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[^{]+)?\s*\{',
            re.MULTILINE
        )

        for class_match in class_pattern.finditer(content):
            class_name = class_match.group(1)
            class_body = self._extract_brace_content(content, class_match.end() - 1)
            if class_body:
                # Extract methods from class
                snippets.extend(self._extract_ts_methods(class_body, class_name, file_path, class_match.start()))

        # Extract standalone functions
        standalone_funcs = self._extract_ts_standalone_functions(content, file_path)
        snippets.extend(standalone_funcs)

        result.snippets = snippets
        result.total_functions = len(snippets)
        result.complex_functions = sum(1 for s in snippets if s.complexity_indicator == 'complex')

        return result

    def extract_python(self, content: str, file_path: str = "") -> LogicFileInfo:
        """Extract logic from Python content."""
        result = LogicFileInfo(file_path=file_path, language='python')

        snippets = []
        lines = content.split('\n')

        # Track current class context
        current_class = None
        class_indent = 0

        for i, line in enumerate(lines):
            # Check for class definition
            class_match = self.PY_CLASS_DEF.match(line)
            if class_match:
                current_class = class_match.group(2)
                class_indent = len(class_match.group(1))

            # Check for function definition
            func_match = self.PY_FUNCTION_DEF.match(line)
            if func_match:
                indent = len(func_match.group(1))
                is_async = bool(func_match.group(2))
                func_name = func_match.group(3)

                # Determine if method or standalone
                is_method = current_class and indent > class_indent

                # Extract function body
                body_lines = self._extract_python_body(lines, i, indent)
                body = '\n'.join(body_lines)

                snippet = self._analyze_python_logic(
                    func_name,
                    body,
                    is_method,
                    is_async,
                    current_class if is_method else None,
                    file_path,
                    i + 1  # line number (1-indexed)
                )
                snippets.append(snippet)

        result.snippets = snippets
        result.total_functions = len(snippets)
        result.complex_functions = sum(1 for s in snippets if s.complexity_indicator == 'complex')

        return result

    def extract_go(self, content: str, file_path: str = "") -> LogicFileInfo:
        """Extract logic from Go source files."""
        result = LogicFileInfo(file_path=file_path, language='go')

        snippets = []

        for match in self.GO_FUNC_DEF.finditer(content):
            receiver_var = match.group(1)   # e.g., 'app' in (app *BaseApp)
            receiver_type = match.group(2)  # e.g., 'BaseApp'
            func_name = match.group(3)      # e.g., 'Start'
            params = match.group(4) or ''
            multi_return = match.group(5)   # multiple return values in parens
            single_return = match.group(6)  # single return value

            # Determine return type
            return_type = ''
            if multi_return:
                return_type = f"({multi_return.strip()})"
            elif single_return:
                return_type = single_return.strip()

            # Build full name and signature
            if receiver_type:
                full_name = f"{receiver_type}.{func_name}"
                sig = f"func ({receiver_var} *{receiver_type}) {func_name}({self._simplify_go_params(params)})"
            else:
                full_name = func_name
                sig = f"func {func_name}({self._simplify_go_params(params)})"

            if return_type:
                sig += f" {return_type}"

            # Extract function body
            body = self._extract_brace_content(content, match.end() - 1)
            if not body:
                continue

            snippet = self._analyze_go_logic(
                full_name, body, sig, file_path, match.start(),
                is_method=receiver_type is not None
            )
            snippets.append(snippet)

        result.snippets = snippets
        result.total_functions = len(snippets)
        result.complex_functions = sum(1 for s in snippets if s.complexity_indicator == 'complex')

        return result

    def _extract_ts_methods(self, class_body: str, class_name: str, file_path: str, class_start: int) -> List[LogicSnippet]:
        """Extract methods from a TypeScript class body."""
        snippets = []

        # Pattern for class methods
        method_pattern = re.compile(
            r'(?:(?:public|private|protected|static|async|readonly|override)\s+)*(\w+)\s*(?:<[^>]+>)?\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{',
            re.MULTILINE
        )

        for match in method_pattern.finditer(class_body):
            method_name = match.group(1)
            params = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else 'void'

            # Skip constructor getters/setters for brevity
            if method_name in ['constructor', 'get', 'set']:
                continue

            # Get method body
            body = self._extract_brace_content(class_body, match.end() - 1)
            if not body:
                continue

            snippet = self._analyze_ts_logic(
                f"{class_name}.{method_name}",
                body,
                f"{method_name}({self._simplify_params(params)}): {return_type}",
                file_path,
                class_start + match.start()
            )
            snippets.append(snippet)

        return snippets

    def _extract_ts_standalone_functions(self, content: str, file_path: str) -> List[LogicSnippet]:
        """Extract standalone functions (not inside classes)."""
        snippets = []

        # Named function declarations
        func_pattern = re.compile(
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*(?:<[^>]+>)?\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{',
            re.MULTILINE
        )

        for match in func_pattern.finditer(content):
            func_name = match.group(1)
            params = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else 'void'

            body = self._extract_brace_content(content, match.end() - 1)
            if not body:
                continue

            snippet = self._analyze_ts_logic(
                func_name,
                body,
                f"function {func_name}({self._simplify_params(params)}): {return_type}",
                file_path,
                match.start()
            )
            snippets.append(snippet)

        # Arrow functions assigned to const
        arrow_pattern = re.compile(
            r'(?:export\s+)?const\s+(\w+)\s*(?::\s*[^=]+)?\s*=\s*(?:async\s+)?\([^)]*\)(?:\s*:\s*[^=]+)?\s*=>\s*\{',
            re.MULTILINE
        )

        for match in arrow_pattern.finditer(content):
            func_name = match.group(1)
            body = self._extract_brace_content(content, match.end() - 1)
            if not body:
                continue

            snippet = self._analyze_ts_logic(
                func_name,
                body,
                f"const {func_name} = (...) => {{...}}",
                file_path,
                match.start()
            )
            snippets.append(snippet)

        return snippets

    def _analyze_ts_logic(self, name: str, body: str, signature: str, file_path: str, position: int) -> LogicSnippet:
        """Analyze TypeScript/JavaScript function body and create logic summary."""

        # Extract key operations
        key_operations = []

        # Return statements
        returns = re.findall(r'return\s+([^;]+);', body)
        for ret in returns[:3]:  # Limit to 3 returns
            ret_clean = ret.strip()[:60]  # Truncate long returns
            if ret_clean:
                key_operations.append(f"return {ret_clean}")

        # Assignments to important variables
        assignments = re.findall(r'(?:const|let|var)\s+(\w+)\s*=\s*([^;]+);', body)
        for var, val in assignments[:5]:  # Limit to 5
            val_clean = val.strip()[:40]
            key_operations.append(f"{var} = {val_clean}")

        # Extract control flow
        control_flow = self._extract_control_flow(body, 'typescript')

        # Extract API calls
        api_calls = self._extract_api_calls(body)

        # Extract data transformations
        data_transforms = self._extract_data_transforms(body)

        # Calculate complexity
        complexity = self._calculate_complexity(body, control_flow)

        # Generate logic summary
        logic_summary = self._generate_logic_summary(
            body, key_operations, control_flow, api_calls, data_transforms
        )

        return LogicSnippet(
            name=name,
            file_path=file_path,
            snippet_type='method' if '.' in name else 'function',
            signature=signature,
            logic_summary=logic_summary,
            key_operations=key_operations[:8],  # Limit to 8
            control_flow=control_flow,
            api_calls=api_calls,
            data_transforms=data_transforms,
            complexity_indicator=complexity,
            line_count=body.count('\n') + 1,
            line_number=position
        )

    def _analyze_python_logic(self, name: str, body: str, is_method: bool, is_async: bool,
                              class_name: Optional[str], file_path: str, line_number: int) -> LogicSnippet:
        """Analyze Python function body and create logic summary."""

        full_name = f"{class_name}.{name}" if class_name else name

        # Build signature
        async_prefix = "async " if is_async else ""
        signature = f"{async_prefix}def {name}(...)"

        # Extract key operations
        key_operations = []

        # Return statements
        returns = re.findall(r'return\s+(.+?)(?:\n|$)', body)
        for ret in returns[:3]:
            ret_clean = ret.strip()[:60]
            if ret_clean:
                key_operations.append(f"return {ret_clean}")

        # Assignments
        assignments = re.findall(r'^(\s*)(\w+)\s*=\s*(.+?)(?:\n|$)', body, re.MULTILINE)
        for indent, var, val in assignments[:5]:
            if not var.startswith('_'):  # Skip private vars
                val_clean = val.strip()[:40]
                key_operations.append(f"{var} = {val_clean}")

        # Extract control flow
        control_flow = self._extract_control_flow(body, 'python')

        # Extract API/external calls (common Python patterns)
        api_calls = []
        api_patterns = [
            (r'requests\.(get|post|put|delete|patch)\s*\(', 'requests'),
            (r'httpx\.(get|post|put|delete|patch)\s*\(', 'httpx'),
            (r'aiohttp\.\w+\.(get|post|put|delete|patch)\s*\(', 'aiohttp'),
            (r'\.query\s*\(', 'db.query'),
            (r'\.execute\s*\(', 'db.execute'),
            (r'\.find\s*\(', 'db.find'),
            (r'\.insert\s*\(', 'db.insert'),
            (r'\.update\s*\(', 'db.update'),
            (r'\.delete\s*\(', 'db.delete'),
        ]
        for pattern, label in api_patterns:
            if re.search(pattern, body):
                api_calls.append(label)

        # Extract data transformations (Python-specific)
        data_transforms = []
        py_transforms = [
            (r'\[.*for\s+\w+\s+in\s+', 'list comprehension'),
            (r'\{.*for\s+\w+\s+in\s+', 'dict/set comprehension'),
            (r'map\s*\(', 'map'),
            (r'filter\s*\(', 'filter'),
            (r'sorted\s*\(', 'sorted'),
            (r'\.sort\s*\(', 'sort'),
            (r'pd\.\w+', 'pandas'),
            (r'np\.\w+', 'numpy'),
            (r'await\s+', 'await'),
        ]
        for pattern, label in py_transforms:
            if re.search(pattern, body):
                data_transforms.append(label)

        # Calculate complexity
        complexity = self._calculate_complexity(body, control_flow)

        # Generate logic summary
        logic_summary = self._generate_logic_summary(
            body, key_operations, control_flow, api_calls, data_transforms
        )

        return LogicSnippet(
            name=full_name,
            file_path=file_path,
            snippet_type='method' if is_method else 'function',
            signature=signature,
            logic_summary=logic_summary,
            key_operations=key_operations[:8],
            control_flow=control_flow,
            api_calls=api_calls,
            data_transforms=data_transforms,
            complexity_indicator=complexity,
            line_count=body.count('\n') + 1,
            line_number=line_number
        )

    def _analyze_go_logic(self, name: str, body: str, signature: str,
                          file_path: str, position: int, is_method: bool = False) -> LogicSnippet:
        """Analyze Go function body and create logic summary."""

        key_operations = []

        # Return statements
        returns = re.findall(r'return\s+(.+?)(?:\n|$)', body)
        for ret in returns[:3]:
            ret_clean = ret.strip()[:60]
            if ret_clean:
                key_operations.append(f"return {ret_clean}")

        # Variable declarations (short and var)
        short_decls = re.findall(r'(\w+)\s*:=\s*(.+?)(?:\n|$)', body)
        for var, val in short_decls[:5]:
            val_clean = val.strip()[:40]
            key_operations.append(f"{var} := {val_clean}")

        # Extract control flow
        control_flow = self._extract_control_flow(body, 'go')

        # Extract Go-specific API/external calls
        api_calls = []
        go_api_patterns = [
            (r'http\.(Get|Post|Head|ListenAndServe)\s*\(', 'net/http'),
            (r'\.GET\s*\(', 'GET'),
            (r'\.POST\s*\(', 'POST'),
            (r'\.PUT\s*\(', 'PUT'),
            (r'\.DELETE\s*\(', 'DELETE'),
            (r'\.PATCH\s*\(', 'PATCH'),
            (r'\.Handle\s*\(', 'Handle'),
            (r'\.HandleFunc\s*\(', 'HandleFunc'),
            (r'\.Query\s*\(', 'db.Query'),
            (r'\.Exec\s*\(', 'db.Exec'),
            (r'\.QueryRow\s*\(', 'db.QueryRow'),
            (r'\.Find\s*\(', 'db.Find'),
            (r'\.Create\s*\(', 'db.Create'),
            (r'\.Save\s*\(', 'db.Save'),
            (r'\.Delete\s*\(', 'db.Delete'),
            (r'grpc\.NewServer\s*\(', 'gRPC'),
            (r'\.SendMsg\s*\(', 'gRPC.Send'),
            (r'\.RecvMsg\s*\(', 'gRPC.Recv'),
        ]
        for pattern, label in go_api_patterns:
            if re.search(pattern, body):
                api_calls.append(label)

        # Extract Go-specific data transformations
        data_transforms = []
        go_transforms = [
            (r'make\s*\(', 'make'),
            (r'append\s*\(', 'append'),
            (r'copy\s*\(', 'copy'),
            (r'len\s*\(', 'len'),
            (r'json\.Marshal\s*\(', 'json.Marshal'),
            (r'json\.Unmarshal\s*\(', 'json.Unmarshal'),
            (r'json\.NewDecoder\s*\(', 'json.Decode'),
            (r'json\.NewEncoder\s*\(', 'json.Encode'),
            (r'fmt\.Sprintf\s*\(', 'fmt.Sprintf'),
            (r'strings\.\w+\s*\(', 'strings'),
            (r'sort\.\w+\s*\(', 'sort'),
            (r'sync\.(?:Mutex|WaitGroup|Once)\b', 'sync'),
            (r'<-\s*\w+|chan\s+', 'channel'),
            (r'go\s+\w+', 'goroutine'),
            (r'context\.\w+\s*\(', 'context'),
        ]
        for pattern, label in go_transforms:
            if re.search(pattern, body):
                data_transforms.append(label)

        # Calculate complexity
        complexity = self._calculate_complexity(body, control_flow)

        # Generate logic summary
        logic_summary = self._generate_logic_summary(
            body, key_operations, control_flow, api_calls, data_transforms
        )

        return LogicSnippet(
            name=name,
            file_path=file_path,
            snippet_type='method' if is_method else 'function',
            signature=signature,
            logic_summary=logic_summary,
            key_operations=key_operations[:8],
            control_flow=control_flow,
            api_calls=api_calls,
            data_transforms=data_transforms,
            complexity_indicator=complexity,
            line_count=body.count('\n') + 1,
            line_number=position
        )

    def _simplify_go_params(self, params: str) -> str:
        """Simplify Go parameter list for signature."""
        if not params.strip():
            return ""

        # Count parameters
        param_count = params.count(',') + 1

        if param_count <= 3:
            # Remove package prefixes for brevity (e.g., context.Context -> Context)
            cleaned = re.sub(r'\w+\.(\w+)', r'\1', params)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            return cleaned
        else:
            return f"...{param_count} params"

    def _extract_control_flow(self, body: str, language: str) -> List[str]:
        """Extract control flow patterns from code."""
        control_flow = []
        keywords = self.CONTROL_FLOW_KEYWORDS.get(language, [])

        for keyword in keywords:
            # Count occurrences
            if language in ('typescript', 'go'):
                pattern = rf'\b{keyword}\s*[\({{:\s]'
            else:  # python
                pattern = rf'\b{keyword}\b\s*[:\(]?'

            matches = re.findall(pattern, body, re.IGNORECASE)
            if matches:
                count = len(matches)
                if count == 1:
                    control_flow.append(keyword)
                else:
                    control_flow.append(f"{keyword}×{count}")

        return control_flow

    def _extract_api_calls(self, body: str) -> List[str]:
        """Extract HTTP/API calls from TypeScript/JavaScript."""
        api_calls = []

        # HTTP methods
        http_patterns = [
            (r'\.get\s*[<(]', 'GET'),
            (r'\.post\s*[<(]', 'POST'),
            (r'\.put\s*[<(]', 'PUT'),
            (r'\.patch\s*[<(]', 'PATCH'),
            (r'\.delete\s*[<(]', 'DELETE'),
        ]

        for pattern, method in http_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                api_calls.append(method)

        return list(set(api_calls))  # Dedupe

    def _extract_data_transforms(self, body: str) -> List[str]:
        """Extract data transformation operations."""
        transforms = []

        for pattern, name in self.DATA_TRANSFORM_PATTERNS:
            if re.search(pattern, body):
                transforms.append(name)

        return list(set(transforms))  # Dedupe

    def _calculate_complexity(self, body: str, control_flow: List[str]) -> str:
        """Calculate a simple complexity indicator."""
        # Count control flow elements
        cf_count = len(control_flow)

        # Count nesting (rough approximation)
        max_indent = 0
        for line in body.split('\n'):
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
                max_indent = max(max_indent, indent)

        # Line count
        line_count = body.count('\n') + 1

        # Simple heuristic
        if cf_count >= 6 or max_indent >= 16 or line_count > 50:
            return 'complex'
        elif cf_count >= 3 or max_indent >= 8 or line_count > 20:
            return 'moderate'
        else:
            return 'simple'

    def _generate_logic_summary(self, body: str, key_ops: List[str],
                                control_flow: List[str], api_calls: List[str],
                                data_transforms: List[str]) -> str:
        """Generate a concise logic summary."""
        parts = []

        # Control flow summary
        if control_flow:
            parts.append(f"flow:[{','.join(control_flow[:4])}]")

        # API calls
        if api_calls:
            parts.append(f"api:[{','.join(api_calls)}]")

        # Data transforms
        if data_transforms:
            parts.append(f"transforms:[{','.join(data_transforms[:4])}]")

        # Key operations (abbreviated)
        if key_ops:
            # Take first 2 operations
            for op in key_ops[:2]:
                # Truncate long operations
                if len(op) > 30:
                    op = op[:27] + "..."
                parts.append(op)

        return ' | '.join(parts) if parts else "simple logic"

    def _extract_brace_content(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content between matching braces starting at start_pos."""
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

    def _extract_python_body(self, lines: List[str], start_idx: int, base_indent: int) -> List[str]:
        """Extract Python function body based on indentation."""
        body_lines = []

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                body_lines.append(line)
                continue

            # Check indentation
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            # If we encounter a line with same or less indentation, body is done
            if indent <= base_indent and stripped:
                break

            body_lines.append(line)

        return body_lines

    def _simplify_params(self, params: str) -> str:
        """Simplify parameter list for signature."""
        if not params.strip():
            return ""

        # Count parameters
        param_count = params.count(',') + 1

        if param_count <= 3:
            # Clean up types for brevity
            cleaned = re.sub(r':\s*[^,)]+', '', params)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            return cleaned
        else:
            return f"...{param_count} params"

    def to_codetrellis_format(self, info: LogicFileInfo) -> str:
        """Convert LogicFileInfo to CodeTrellis format."""
        lines = []

        rel_path = Path(info.file_path).name if info.file_path else "unknown"
        lines.append(f"# {rel_path} ({info.total_functions} functions, {info.complex_functions} complex)")

        for snippet in info.snippets:
            # Format: name|signature|summary|complexity
            line_parts = [
                f"  {snippet.name}",
                snippet.signature,
            ]

            # Add logic summary
            if snippet.logic_summary:
                line_parts.append(snippet.logic_summary)

            # Add complexity if not simple
            if snippet.complexity_indicator != 'simple':
                line_parts.append(f"[{snippet.complexity_indicator}]")

            lines.append('|'.join(line_parts))

        return '\n'.join(lines)
