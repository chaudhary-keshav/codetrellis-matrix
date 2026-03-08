"""
Alpine.js Store Extractor for CodeTrellis

Extracts Alpine.js store definitions and usage patterns:
- Alpine.store('name', { ... }) definitions
- Store state fields
- Store methods
- Store getters
- $store.name access patterns in HTML and JS
- Cross-store references
- Persistent stores (@alpinejs/persist)

Supports:
- Alpine.js v3.x (Alpine.store() API only — not available in v1/v2)

Part of CodeTrellis v4.66 - Alpine.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class AlpineStoreInfo:
    """Information about an Alpine.js store definition."""
    name: str  # Store name (first argument to Alpine.store())
    file: str = ""
    line_number: int = 0
    state_fields: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    getters: List[str] = field(default_factory=list)
    has_init: bool = False
    has_persist: bool = False  # Uses @alpinejs/persist ($persist)
    access_count: int = 0  # Number of $store.name accesses found


class AlpineStoreExtractor:
    """
    Extracts Alpine.js store definitions and access patterns.

    Detects:
    - Alpine.store('name', { state, methods, getters, init }) definitions
    - Alpine.store('name') getter calls (reading store without defining)
    - $store.name access in HTML attributes and JS code
    - $persist() usage for persistent state
    """

    # Alpine.store('name', { ... }) definition
    STORE_DEF_PATTERN = re.compile(
        r"""Alpine\.store\(\s*['"](\w+)['"]\s*,\s*\{""",
        re.MULTILINE
    )

    # Alpine.store('name') getter (no second argument)
    STORE_GET_PATTERN = re.compile(
        r"""Alpine\.store\(\s*['"](\w+)['"]\s*\)""",
        re.MULTILINE
    )

    # $store.name access patterns
    STORE_ACCESS_PATTERN = re.compile(
        r"""\$store\.(\w+)""",
        re.MULTILINE
    )

    # $persist() usage
    PERSIST_PATTERN = re.compile(
        r"""\$persist\(""",
        re.MULTILINE
    )

    # Method pattern inside store object
    METHOD_PATTERN = re.compile(
        r"""(?:^|\s+)(\w+)\s*\([^)]*\)\s*\{""",
        re.MULTILINE
    )

    # Getter pattern
    GETTER_PATTERN = re.compile(
        r"""get\s+(\w+)\s*\(\s*\)\s*\{""",
        re.MULTILINE
    )

    # State field pattern
    STATE_FIELD_PATTERN = re.compile(
        r"""(\w+)\s*:\s*(?!function)""",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> List[AlpineStoreInfo]:
        """Extract Alpine.js store definitions and usage.

        Args:
            content: Source code content.
            file_path: Path to the source file.

        Returns:
            List of AlpineStoreInfo objects.
        """
        stores: List[AlpineStoreInfo] = []
        store_names: Dict[str, AlpineStoreInfo] = {}

        # Extract store definitions
        for match in self.STORE_DEF_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            body = self._extract_body(content, match.end() - 1)
            state_fields = self._extract_state_fields(body)
            methods = self._extract_methods(body)
            getters = self._extract_getters(body)
            has_init = 'init' in methods
            has_persist = bool(self.PERSIST_PATTERN.search(body))

            store = AlpineStoreInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                state_fields=state_fields,
                methods=methods,
                getters=getters,
                has_init=has_init,
                has_persist=has_persist,
                access_count=0,
            )
            stores.append(store)
            store_names[name] = store

        # Count $store.name accesses
        for match in self.STORE_ACCESS_PATTERN.finditer(content):
            name = match.group(1)
            if name in store_names:
                store_names[name].access_count += 1
            else:
                # Store referenced but not defined in this file
                line_num = content[:match.start()].count('\n') + 1
                store = AlpineStoreInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    access_count=1,
                )
                stores.append(store)
                store_names[name] = store

        return stores

    def _extract_body(self, content: str, start: int) -> str:
        """Extract balanced braces body from content.

        Args:
            content: Full source code.
            start: Position of opening brace.

        Returns:
            Body string within braces.
        """
        depth = 0
        for i in range(start, min(start + 5000, len(content))):
            ch = content[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[start:i + 1]
        return content[start:min(start + 5000, len(content))]

    def _extract_state_fields(self, body: str) -> List[str]:
        """Extract state field names from store body.

        Args:
            body: Store body text.

        Returns:
            List of state field names.
        """
        fields: List[str] = []
        for match in self.STATE_FIELD_PATTERN.finditer(body):
            name = match.group(1)
            if name not in ('get', 'set', 'async', 'function', 'class', 'return', 'if', 'for', 'init'):
                if name not in fields:
                    fields.append(name)
        return fields[:20]

    def _extract_methods(self, body: str) -> List[str]:
        """Extract method names from store body.

        Args:
            body: Store body text.

        Returns:
            List of method names.
        """
        methods: List[str] = []
        for match in self.METHOD_PATTERN.finditer(body):
            name = match.group(1)
            if name not in ('if', 'for', 'while', 'switch', 'catch', 'function', 'class', 'return', 'get'):
                if name not in methods:
                    methods.append(name)
        return methods

    def _extract_getters(self, body: str) -> List[str]:
        """Extract getter names from store body.

        Args:
            body: Store body text.

        Returns:
            List of getter names.
        """
        return [m.group(1) for m in self.GETTER_PATTERN.finditer(body)]
