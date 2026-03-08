"""
Valtio Proxy Extractor for CodeTrellis

Extracts Valtio proxy() state definitions and configuration patterns:
- proxy() / proxy<T>() state object definitions
- State shape analysis (fields, nested objects, arrays)
- Computed properties (getter-based derived state)
- ref() usage for non-proxied references
- proxyMap() / proxySet() collection utilities
- Nested proxy composition
- TypeScript generic type annotations
- Module-level state patterns

Supports:
- Valtio v1.x (proxy, useSnapshot, subscribe, snapshot, ref, derive, watch)
- Valtio v2.x (React 18+ useSyncExternalStore, proxyMap/proxySet rewrite,
                vanilla subpath exports, unstable_deepProxy, useProxy,
                deprecated derive/watch, unstable_enableOp)

Part of CodeTrellis v4.56 - Valtio Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValtioProxyInfo:
    """Information about a Valtio proxy() state definition."""
    name: str
    file: str = ""
    line_number: int = 0
    state_fields: List[str] = field(default_factory=list)
    computed_getters: List[str] = field(default_factory=list)
    has_typescript: bool = False
    type_name: str = ""  # TypeScript interface/type for state
    is_exported: bool = False
    is_module_level: bool = False  # defined at module scope
    has_nested_proxy: bool = False
    has_ref: bool = False
    has_async_value: bool = False  # Promise values in state
    initial_value_type: str = ""  # object, array, empty


@dataclass
class ValtioRefInfo:
    """Information about a Valtio ref() usage."""
    name: str
    file: str = ""
    line_number: int = 0
    ref_target: str = ""  # What is being wrapped in ref()
    parent_proxy: str = ""  # Which proxy contains this ref
    is_dom_ref: bool = False


@dataclass
class ValtioProxyCollectionInfo:
    """Information about a Valtio proxyMap() or proxySet() usage."""
    name: str
    file: str = ""
    line_number: int = 0
    collection_type: str = ""  # proxyMap, proxySet
    has_initial_values: bool = False
    key_type: str = ""  # TypeScript key type
    value_type: str = ""  # TypeScript value type
    is_nested: bool = False  # Inside another proxy
    is_exported: bool = False


class ValtioProxyExtractor:
    """
    Extracts Valtio proxy() definitions from source code.

    Detects:
    - proxy() state definitions with state shape
    - proxy<T>() TypeScript generic types
    - Computed getters (get fieldName() { return ... })
    - ref() usage for non-reactive references
    - proxyMap() / proxySet() collections
    - Nested proxy composition
    - Module-level vs function-level state
    """

    # proxy() definition: const state = proxy({...})
    PROXY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'proxy\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # ref() usage: ref(something)
    REF_PATTERN = re.compile(
        r'(\w+)\s*:\s*ref\s*\(\s*([^)]+?)\s*\)',
        re.MULTILINE
    )

    # Standalone ref: const x = ref(...)
    REF_STANDALONE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*ref\s*\(\s*([^)]+?)\s*\)',
        re.MULTILINE
    )

    # proxyMap() usage
    PROXY_MAP_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'proxyMap\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # proxySet() usage
    PROXY_SET_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'proxySet\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Computed getter: get fieldName() { return ... }
    COMPUTED_GETTER_PATTERN = re.compile(
        r'get\s+(\w+)\s*\(\s*\)\s*\{',
        re.MULTILINE
    )

    # State field extraction (within proxy body)
    STATE_FIELD_PATTERN = re.compile(
        r'^\s+(\w+)\s*:\s*(?!function|get\s)',
        re.MULTILINE
    )

    # Nested proxy: field: proxy({...})
    NESTED_PROXY_PATTERN = re.compile(
        r'(\w+)\s*:\s*proxy\s*\(',
        re.MULTILINE
    )

    # Async value: field: fetch(...).then(...)
    ASYNC_VALUE_PATTERN = re.compile(
        r'(\w+)\s*:\s*(?:fetch|Promise|async|new\s+Promise)\s*\(',
        re.MULTILINE
    )

    # proxyMap/proxySet nested inside proxy
    NESTED_COLLECTION_PATTERN = re.compile(
        r'(\w+)\s*:\s*(proxyMap|proxySet)\s*\(',
        re.MULTILINE
    )

    def __init__(self) -> None:
        """Initialize the proxy extractor."""

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Valtio proxy patterns from source code.

        Args:
            content: Source code content.
            file_path: Path to source file.

        Returns:
            Dictionary with 'proxies', 'refs', and 'collections' lists.
        """
        proxies: List[ValtioProxyInfo] = []
        refs: List[ValtioRefInfo] = []
        collections: List[ValtioProxyCollectionInfo] = []

        lines = content.split('\n')

        # Extract proxy() definitions
        for match in self.PROXY_PATTERN.finditer(content):
            name = match.group(1)
            ts_type = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start() + 10]

            # Determine if module-level (not inside function/class)
            line_text = lines[line_num - 1] if line_num <= len(lines) else ""
            indent_level = len(line_text) - len(line_text.lstrip())
            is_module_level = indent_level == 0

            # Extract state fields from proxy body
            state_fields = self._extract_state_fields(content, match.end())
            computed_getters = self._extract_computed_getters(content, match.end())

            # Check for nested proxy, ref, async
            body = self._extract_body(content, match.end())
            has_nested = bool(self.NESTED_PROXY_PATTERN.search(body))
            has_ref = 'ref(' in body
            has_async = bool(self.ASYNC_VALUE_PATTERN.search(body))

            # Determine initial value type
            initial_type = "object"
            after_paren = content[match.end():match.end() + 5].strip()
            if after_paren.startswith('['):
                initial_type = "array"
            elif after_paren.startswith('{') and after_paren == '{}':
                initial_type = "empty"

            proxies.append(ValtioProxyInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                state_fields=state_fields,
                computed_getters=computed_getters,
                has_typescript=bool(ts_type),
                type_name=ts_type,
                is_exported=is_exported,
                is_module_level=is_module_level,
                has_nested_proxy=has_nested,
                has_ref=has_ref,
                has_async_value=has_async,
                initial_value_type=initial_type,
            ))

            # Extract nested collections from this proxy body
            for coll_match in self.NESTED_COLLECTION_PATTERN.finditer(body):
                coll_name = coll_match.group(1)
                coll_type = coll_match.group(2)
                collections.append(ValtioProxyCollectionInfo(
                    name=coll_name,
                    file=file_path,
                    line_number=line_num,
                    collection_type=coll_type,
                    is_nested=True,
                ))

        # Extract ref() usages within proxy bodies
        for match in self.REF_PATTERN.finditer(content):
            field_name = match.group(1)
            ref_target = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1
            is_dom = any(kw in ref_target.lower() for kw in ['document', 'window', 'element', 'dom', 'canvas'])

            refs.append(ValtioRefInfo(
                name=field_name,
                file=file_path,
                line_number=line_num,
                ref_target=ref_target[:80],
                is_dom_ref=is_dom,
            ))

        # Extract standalone ref() usages
        for match in self.REF_STANDALONE_PATTERN.finditer(content):
            ref_name = match.group(1)
            ref_target = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1

            refs.append(ValtioRefInfo(
                name=ref_name,
                file=file_path,
                line_number=line_num,
                ref_target=ref_target[:80],
            ))

        # Extract standalone proxyMap() definitions
        for match in self.PROXY_MAP_PATTERN.finditer(content):
            name = match.group(1)
            ts_types = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start() + 10]

            key_type, value_type = "", ""
            if ts_types and ',' in ts_types:
                parts = ts_types.split(',', 1)
                key_type = parts[0].strip()
                value_type = parts[1].strip()

            after_paren = content[match.end():match.end() + 10].strip()
            has_initial = not after_paren.startswith(')')

            collections.append(ValtioProxyCollectionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                collection_type="proxyMap",
                has_initial_values=has_initial,
                key_type=key_type,
                value_type=value_type,
                is_nested=False,
                is_exported=is_exported,
            ))

        # Extract standalone proxySet() definitions
        for match in self.PROXY_SET_PATTERN.finditer(content):
            name = match.group(1)
            ts_type = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start() + 10]

            after_paren = content[match.end():match.end() + 10].strip()
            has_initial = not after_paren.startswith(')')

            collections.append(ValtioProxyCollectionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                collection_type="proxySet",
                has_initial_values=has_initial,
                value_type=ts_type,
                is_nested=False,
                is_exported=is_exported,
            ))

        return {
            'proxies': proxies,
            'refs': refs,
            'collections': collections,
        }

    def _extract_state_fields(self, content: str, start_pos: int) -> List[str]:
        """Extract state field names from proxy body."""
        body = self._extract_body(content, start_pos)
        fields = []
        for match in self.STATE_FIELD_PATTERN.finditer(body):
            field_name = match.group(1)
            if field_name not in ('get', 'set', 'return', 'if', 'else', 'for', 'while', 'switch', 'case', 'default', 'try', 'catch'):
                fields.append(field_name)
        return list(dict.fromkeys(fields))[:30]

    def _extract_computed_getters(self, content: str, start_pos: int) -> List[str]:
        """Extract computed getter names from proxy body."""
        body = self._extract_body(content, start_pos)
        getters = []
        for match in self.COMPUTED_GETTER_PATTERN.finditer(body):
            getters.append(match.group(1))
        return getters[:15]

    def _extract_body(self, content: str, start_pos: int) -> str:
        """Extract the body of a proxy/function call starting from open paren."""
        # Find the opening brace/bracket
        depth = 1
        i = start_pos
        # Skip to first meaningful char after (
        while i < len(content) and content[i] in ' \t\n\r':
            i += 1
        if i >= len(content):
            return ""

        open_char = content[i]
        if open_char == '{':
            close_char = '}'
        elif open_char == '[':
            close_char = ']'
        else:
            return content[start_pos:min(start_pos + 500, len(content))]

        start = i
        i += 1
        while i < len(content) and depth > 0:
            ch = content[i]
            if ch == open_char:
                depth += 1
            elif ch == close_char:
                depth -= 1
            elif ch in ('"', "'", '`'):
                i = self._skip_string(content, i)
                continue
            i += 1

        return content[start:i]

    @staticmethod
    def _skip_string(content: str, pos: int) -> int:
        """Skip past a string literal."""
        quote = content[pos]
        i = pos + 1
        while i < len(content):
            if content[i] == '\\':
                i += 2
                continue
            if content[i] == quote:
                if quote == '`':
                    return i
                return i
            i += 1
        return i
