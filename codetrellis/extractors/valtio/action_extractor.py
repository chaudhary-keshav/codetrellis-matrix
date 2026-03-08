"""
Valtio Action Extractor for CodeTrellis

Extracts Valtio action/mutation patterns:
- Direct mutations: state.field = value
- Array mutations: state.arr.push(...), state.arr.splice(...)
- Nested mutations: state.obj.nested = value
- Delete operations: delete state.field
- Async actions: async function that mutates proxy state
- devtools() connections for Redux DevTools integration
- Named action functions (functions that receive/close over proxy state and mutate it)

Supports:
- Valtio v1.x (devtools from 'valtio/utils')
- Valtio v2.x (devtools from 'valtio/vanilla/utils')

Part of CodeTrellis v4.56 - Valtio Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValtioActionInfo:
    """Information about a Valtio action (state mutation function)."""
    file: str = ""
    line_number: int = 0
    name: str = ""  # Function/arrow function name
    proxy_name: str = ""  # Which proxy is mutated
    is_async: bool = False
    mutation_count: int = 0  # Approximate number of mutations
    mutations: List[str] = field(default_factory=list)  # e.g. ["state.count", "state.items"]
    is_exported: bool = False
    is_method: bool = False  # Defined as method on proxy object itself


@dataclass
class ValtioDevtoolsInfo:
    """Information about a devtools() connection."""
    file: str = ""
    line_number: int = 0
    proxy_name: str = ""  # Which proxy is connected
    label: str = ""  # devtools label/name
    has_enabled_option: bool = False


class ValtioActionExtractor:
    """
    Extracts Valtio action/mutation patterns from source code.

    Detects:
    - Named mutation functions that modify proxy state
    - Direct state mutations (state.x = y)
    - Array/object mutation methods (push, splice, delete)
    - Async actions
    - devtools() connections
    - Method-style actions defined within proxy object
    """

    # Direct mutation: state.field = value (assignment)
    MUTATION_ASSIGNMENT_PATTERN = re.compile(
        r'(\w+)\.(\w[\w.]*)\s*(?:=|\+=|-=|\*=|/=|%=|\?\?=|&&=|\|\|=)\s*',
        re.MULTILINE
    )

    # Array mutations: state.arr.push(...), .splice(...), .pop(), .shift(), .unshift(...)
    ARRAY_MUTATION_PATTERN = re.compile(
        r'(\w+)\.(\w[\w.]*)\.(push|pop|shift|unshift|splice|sort|reverse|fill|copyWithin)\s*\(',
        re.MULTILINE
    )

    # Delete mutation: delete state.field
    DELETE_MUTATION_PATTERN = re.compile(
        r'delete\s+(\w+)\.(\w[\w.]*)',
        re.MULTILINE
    )

    # Increment/decrement: state.count++ or ++state.count
    INCREMENT_PATTERN = re.compile(
        r'(?:(\w+)\.(\w[\w.]*)\s*\+\+|\+\+\s*(\w+)\.(\w[\w.]*))',
        re.MULTILINE
    )

    DECREMENT_PATTERN = re.compile(
        r'(?:(\w+)\.(\w[\w.]*)\s*--|-\s*-\s*(\w+)\.(\w[\w.]*))',
        re.MULTILINE
    )

    # Named function definitions (including async, exported)
    FUNCTION_PATTERN = re.compile(
        r'(?:(export)\s+)?'
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*(async\s+)?(?:function\s*)?(?:\([^)]*\)|\w+)\s*=>|'
        r'(async\s+)?function\s+(\w+)\s*\()',
        re.MULTILINE
    )

    # Arrow function with body (for action detection)
    ARROW_FUNCTION_BODY_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*(async\s+)?\([^)]*\)\s*=>\s*\{',
        re.MULTILINE
    )

    # devtools(state, { name: 'label', enabled: true })
    DEVTOOLS_PATTERN = re.compile(
        r'devtools\s*\(\s*(\w+)\s*(?:,\s*\{([^}]*)\})?',
        re.MULTILINE
    )

    # devtools name/label option
    DEVTOOLS_NAME_PATTERN = re.compile(
        r'''name\s*:\s*['"]([\w\s-]+)['"]''',
        re.MULTILINE
    )

    # devtools enabled option
    DEVTOOLS_ENABLED_PATTERN = re.compile(
        r'enabled\s*:',
        re.MULTILINE
    )

    # Method-style actions inside proxy({ ... increment() { ... } })
    METHOD_ACTION_PATTERN = re.compile(
        r'^\s+(async\s+)?(\w+)\s*\([^)]*\)\s*\{',
        re.MULTILINE
    )

    def __init__(self) -> None:
        """Initialize the action extractor."""

    def extract(self, content: str, file_path: str = "",
                known_proxies: Optional[List[str]] = None) -> dict:
        """Extract Valtio action patterns from source code.

        Args:
            content: Source code content.
            file_path: Path to source file.
            known_proxies: List of known proxy variable names for context.

        Returns:
            Dictionary with 'actions' and 'devtools' lists.
        """
        actions: List[ValtioActionInfo] = []
        devtools_items: List[ValtioDevtoolsInfo] = []
        proxy_names = set(known_proxies or [])

        # Collect all mutations referencing known proxy names
        all_mutations = self._collect_mutations(content, proxy_names)

        # Find named functions that contain proxy mutations
        for match in self.FUNCTION_PATTERN.finditer(content):
            is_exported = bool(match.group(1))
            func_name = match.group(2) or match.group(5) or ""
            is_async = bool(match.group(3) or match.group(4))
            line_num = content[:match.start()].count('\n') + 1

            if not func_name:
                continue

            # Extract function body (approximate)
            body = self._extract_body(content, match.end())
            if not body:
                continue

            # Check if body contains mutations to any known proxy
            func_mutations = self._find_mutations_in_body(body, proxy_names)
            if not func_mutations:
                continue

            proxy_ref = func_mutations[0][0] if func_mutations else ""
            actions.append(ValtioActionInfo(
                file=file_path,
                line_number=line_num,
                name=func_name,
                proxy_name=proxy_ref,
                is_async=is_async,
                mutation_count=len(func_mutations),
                mutations=[f"{p}.{f}" for p, f in func_mutations[:10]],
                is_exported=is_exported,
                is_method=False,
            ))

        # Also check arrow functions
        for match in self.ARROW_FUNCTION_BODY_PATTERN.finditer(content):
            func_name = match.group(1) or ""
            is_async = bool(match.group(2))
            line_num = content[:match.start()].count('\n') + 1

            body = self._extract_body(content, match.end())
            if not body:
                continue

            func_mutations = self._find_mutations_in_body(body, proxy_names)
            if not func_mutations:
                continue

            # Avoid duplicates from FUNCTION_PATTERN
            if any(a.name == func_name and a.line_number == line_num for a in actions):
                continue

            proxy_ref = func_mutations[0][0] if func_mutations else ""
            line_text = content.split('\n')[line_num - 1] if line_num > 0 else ""
            is_exported = 'export' in line_text

            actions.append(ValtioActionInfo(
                file=file_path,
                line_number=line_num,
                name=func_name,
                proxy_name=proxy_ref,
                is_async=is_async,
                mutation_count=len(func_mutations),
                mutations=[f"{p}.{f}" for p, f in func_mutations[:10]],
                is_exported=is_exported,
                is_method=False,
            ))

        # Extract devtools() connections
        for match in self.DEVTOOLS_PATTERN.finditer(content):
            proxy_name = match.group(1)
            options = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1

            label = ""
            name_match = self.DEVTOOLS_NAME_PATTERN.search(options)
            if name_match:
                label = name_match.group(1)

            devtools_items.append(ValtioDevtoolsInfo(
                file=file_path,
                line_number=line_num,
                proxy_name=proxy_name,
                label=label,
                has_enabled_option=bool(self.DEVTOOLS_ENABLED_PATTERN.search(options)),
            ))

        return {
            'actions': actions,
            'devtools': devtools_items,
        }

    def _collect_mutations(self, content: str, proxy_names: set) -> List[tuple]:
        """Collect all mutations in the entire file."""
        mutations = []
        for match in self.MUTATION_ASSIGNMENT_PATTERN.finditer(content):
            obj = match.group(1)
            if proxy_names and obj in proxy_names:
                mutations.append((obj, match.group(2).split('.')[0]))
        return mutations

    def _find_mutations_in_body(self, body: str,
                                proxy_names: set) -> List[tuple]:
        """Find proxy mutations within a function body.

        Returns:
            List of (proxy_name, field_name) tuples.
        """
        mutations = []
        seen = set()

        for pattern in [self.MUTATION_ASSIGNMENT_PATTERN,
                        self.ARRAY_MUTATION_PATTERN,
                        self.DELETE_MUTATION_PATTERN,
                        self.INCREMENT_PATTERN,
                        self.DECREMENT_PATTERN]:
            for match in pattern.finditer(body):
                obj = match.group(1) or match.group(3) or ""
                fld = match.group(2) or match.group(4) or ""
                if obj and (not proxy_names or obj in proxy_names):
                    key = (obj, fld.split('.')[0])
                    if key not in seen:
                        seen.add(key)
                        mutations.append(key)

        return mutations

    def _extract_body(self, content: str, start_pos: int) -> str:
        """Extract the body of a function starting after '{'."""
        # Find the opening brace
        brace_pos = content.rfind('{', max(0, start_pos - 5), start_pos + 5)
        if brace_pos == -1:
            brace_pos = content.find('{', start_pos)
        if brace_pos == -1:
            return ""

        depth = 1
        pos = brace_pos + 1
        length = len(content)

        while pos < length and depth > 0:
            ch = content[pos]
            if ch in ('"', "'", '`'):
                pos = self._skip_string(content, pos)
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            pos += 1

        return content[brace_pos + 1:pos - 1] if depth == 0 else ""

    @staticmethod
    def _skip_string(content: str, pos: int) -> int:
        """Skip past a string literal."""
        quote = content[pos]
        pos += 1
        length = len(content)
        while pos < length:
            ch = content[pos]
            if ch == '\\':
                pos += 2
                continue
            if ch == quote:
                if quote == '`':
                    return pos + 1
                return pos + 1
            pos += 1
        return pos
