"""
Svelte Store Extractor for CodeTrellis

Extracts store definitions from Svelte/SvelteKit source code:
- writable() stores (svelte/store)
- readable() stores (svelte/store)
- derived() stores (dependent on other stores)
- Custom stores (objects implementing store contract: subscribe method)
- Store subscriptions ($store auto-subscription syntax)
- Svelte 5 alternatives ($state in .svelte.ts/.svelte.js files)
- SvelteKit page/navigating/updated stores

Supports Svelte 3.x through 5.x:
- Svelte 3/4: writable, readable, derived, get, custom stores
- Svelte 5: $state in .svelte.ts files as module-level reactive state

Part of CodeTrellis v4.35 - Svelte/SvelteKit Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SvelteStoreInfo:
    """Information about a Svelte store definition."""
    name: str
    store_type: str = ""  # writable, readable, derived, custom, state
    file: str = ""
    line_number: int = 0
    is_exported: bool = False
    initial_value: Optional[str] = None
    type_param: str = ""  # TypeScript generic type
    depends_on: List[str] = field(default_factory=list)  # for derived stores
    has_start_function: bool = False  # readable/writable with start function
    methods: List[str] = field(default_factory=list)  # custom store methods


@dataclass
class SvelteStoreSubscriptionInfo:
    """Information about store subscription usage."""
    store_name: str
    is_auto: bool = True  # $store syntax
    file: str = ""
    line_number: int = 0


class SvelteStoreExtractor:
    """
    Extracts Svelte store definitions and subscriptions.

    Handles:
    - writable/readable/derived store factories
    - Custom stores with subscribe contract
    - Auto-subscription syntax ($store)
    - Svelte 5 .svelte.ts reactive state
    """

    # Store creation patterns
    WRITABLE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*writable\s*(?:<([^>]+)>)?\s*\(\s*([^)]*)\)',
        re.MULTILINE
    )
    READABLE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*readable\s*(?:<([^>]+)>)?\s*\(\s*([^)]*)\)',
        re.MULTILINE
    )
    DERIVED_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*derived\s*(?:<([^>]+)>)?\s*\(\s*'
        r'(?:\[([^\]]+)\]|(\w+))',
        re.MULTILINE
    )

    # Custom store pattern (function that returns { subscribe, ... })
    CUSTOM_STORE_PATTERN = re.compile(
        r'(?:export\s+)?function\s+(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{[^}]*'
        r'(?:subscribe|writable|readable)',
        re.MULTILINE | re.DOTALL
    )
    CUSTOM_STORE_ARROW_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:\([^)]*\)|)\s*(?:=>|function)\s*'
        r'[^{]*\{[^}]*(?:subscribe|writable|readable)',
        re.MULTILINE | re.DOTALL
    )

    # Auto-subscription pattern
    AUTO_SUBSCRIBE_PATTERN = re.compile(
        r'\$(\w+)',
        re.MULTILINE
    )

    # Store import pattern
    STORE_IMPORT_PATTERN = re.compile(
        r"from\s+['\"]svelte/store['\"]",
        re.MULTILINE
    )

    # Svelte 5 .svelte.ts state pattern
    SVELTE_STATE_MODULE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*\$state\s*(?:<([^>]+)>)?\s*\(',
        re.MULTILINE
    )

    # Export detection
    EXPORT_PATTERN = re.compile(
        r'export\s+(?:const|let|function)\s+(\w+)',
        re.MULTILINE
    )

    # Known Svelte built-in stores (not user-defined)
    BUILTIN_STORES = {'page', 'navigating', 'updated'}

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract store definitions and subscriptions.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'stores' and 'subscriptions' lists
        """
        stores = []
        subscriptions = []

        exported_names = set(self.EXPORT_PATTERN.findall(content))

        # Writable stores
        for match in self.WRITABLE_PATTERN.finditer(content):
            name = match.group(1)
            type_param = match.group(2) or ''
            initial = match.group(3).strip() if match.group(3) else None
            stores.append(SvelteStoreInfo(
                name=name,
                store_type='writable',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                is_exported=name in exported_names or 'export' in content[max(0, match.start()-10):match.start()],
                initial_value=initial,
                type_param=type_param,
            ))

        # Readable stores
        for match in self.READABLE_PATTERN.finditer(content):
            name = match.group(1)
            type_param = match.group(2) or ''
            initial = match.group(3).strip() if match.group(3) else None
            stores.append(SvelteStoreInfo(
                name=name,
                store_type='readable',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                is_exported=name in exported_names or 'export' in content[max(0, match.start()-10):match.start()],
                initial_value=initial,
                type_param=type_param,
                has_start_function=',' in (match.group(3) or ''),
            ))

        # Derived stores
        for match in self.DERIVED_PATTERN.finditer(content):
            name = match.group(1)
            type_param = match.group(2) or ''
            deps_array = match.group(3) or ''
            deps_single = match.group(4) or ''

            deps = []
            if deps_array:
                deps = [d.strip() for d in deps_array.split(',') if d.strip()]
            elif deps_single:
                deps = [deps_single]

            stores.append(SvelteStoreInfo(
                name=name,
                store_type='derived',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                is_exported=name in exported_names or 'export' in content[max(0, match.start()-10):match.start()],
                type_param=type_param,
                depends_on=deps,
            ))

        # Custom stores (function-based)
        for match in self.CUSTOM_STORE_PATTERN.finditer(content):
            name = match.group(1)
            # Avoid duplicates with writable/readable/derived
            if not any(s.name == name for s in stores):
                stores.append(SvelteStoreInfo(
                    name=name,
                    store_type='custom',
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    is_exported=name in exported_names,
                ))

        # Svelte 5 .svelte.ts module state
        if file_path.endswith('.svelte.ts') or file_path.endswith('.svelte.js'):
            for match in self.SVELTE_STATE_MODULE_PATTERN.finditer(content):
                name = match.group(1)
                type_param = match.group(2) or ''
                stores.append(SvelteStoreInfo(
                    name=name,
                    store_type='state',
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    is_exported=name in exported_names,
                    type_param=type_param,
                ))

        # Auto-subscriptions ($store syntax) - only in .svelte files
        if file_path.endswith('.svelte'):
            seen = set()
            for match in self.AUTO_SUBSCRIBE_PATTERN.finditer(content):
                store_name = match.group(1)
                # Filter out runes and built-in variables
                if store_name in ('state', 'derived', 'effect', 'props',
                                  'bindable', 'inspect', 'host', 'app',
                                  'env', 'lib', 'page', 'navigating', 'updated'):
                    continue
                if store_name not in seen:
                    seen.add(store_name)
                    subscriptions.append(SvelteStoreSubscriptionInfo(
                        store_name=store_name,
                        is_auto=True,
                        file=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                    ))

        return {'stores': stores, 'subscriptions': subscriptions}
