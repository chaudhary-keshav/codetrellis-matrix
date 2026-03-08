"""
Solid.js Store Extractor for CodeTrellis

Extracts Solid.js store patterns and state management:
- createStore(initialValue) for nested reactive state
- produce() for Immer-like mutations
- reconcile() for diffing/replacing store values
- unwrap() for getting raw values
- Store path-based setters (setStore('key', 'nested', value))
- Store with TypeScript types
- createMutable() for mutable proxy stores

Supports:
- Solid.js v1.0+ (createStore from solid-js/store)
- Store utilities: produce, reconcile, unwrap, createMutable
- Path-based setter patterns
- Nested store updates

Part of CodeTrellis v4.62 - Solid.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SolidStoreInfo:
    """Information about a Solid.js store (createStore)."""
    name: str  # The store getter name
    setter_name: str = ""  # The store setter name
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""  # TypeScript type
    initial_fields: List[str] = field(default_factory=list)
    is_exported: bool = False
    store_type: str = "store"  # store, mutable
    uses_produce: bool = False
    uses_reconcile: bool = False
    uses_unwrap: bool = False


@dataclass
class SolidStoreUpdateInfo:
    """Information about a store setter/update call."""
    setter_name: str
    file: str = ""
    line_number: int = 0
    update_type: str = ""  # path, produce, reconcile, direct
    path: List[str] = field(default_factory=list)  # Path segments for path-based updates


class SolidStoreExtractor:
    """
    Extracts Solid.js store patterns from source code.

    Detects:
    - createStore<T>(initialValue) -> [store, setStore]
    - createMutable<T>(initialValue) -> mutable proxy
    - produce(fn) for Immer-like mutations
    - reconcile(value) for replacing store contents
    - unwrap(store) for raw values
    - Path-based setter calls: setStore('key', value)
    - Nested path updates: setStore('users', idx, 'name', newName)
    """

    # createStore<T>(initialValue)
    CREATE_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+\[(\w+),\s*(\w+)\]\s*=\s*'
        r'createStore\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # createMutable<T>(initialValue)
    CREATE_MUTABLE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createMutable\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # produce() usage
    PRODUCE_PATTERN = re.compile(
        r'produce\s*\(\s*(?:\(\w+\)\s*=>|function)',
        re.MULTILINE
    )

    # reconcile() usage
    RECONCILE_PATTERN = re.compile(
        r'reconcile\s*\(',
        re.MULTILINE
    )

    # unwrap() usage
    UNWRAP_PATTERN = re.compile(
        r'unwrap\s*\(',
        re.MULTILINE
    )

    # Store setter call: setStore(...) or setX(...)
    STORE_SETTER_PATTERN = re.compile(
        r'(set\w+)\s*\(\s*(?:'
        r"['\"](\w+)['\"]"  # String path key
        r'|produce\s*\('    # produce() argument
        r'|reconcile\s*\('  # reconcile() argument
        r')',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Solid.js store patterns from source code."""
        stores = []
        store_updates = []

        has_produce = bool(self.PRODUCE_PATTERN.search(content))
        has_reconcile = bool(self.RECONCILE_PATTERN.search(content))
        has_unwrap = bool(self.UNWRAP_PATTERN.search(content))

        # ── createStore ───────────────────────────────────────────
        for m in self.CREATE_STORE_PATTERN.finditer(content):
            store_name = m.group(1)
            setter_name = m.group(2)
            type_ann = m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            # Try to extract initial state fields
            initial_fields = []
            init_start = m.end()
            init_body = content[init_start:min(len(content), init_start + 500)]
            field_matches = re.findall(r'(\w+)\s*:', init_body[:200])
            initial_fields = field_matches[:15]

            stores.append(SolidStoreInfo(
                name=store_name,
                setter_name=setter_name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                initial_fields=initial_fields,
                is_exported=is_exported,
                store_type="store",
                uses_produce=has_produce,
                uses_reconcile=has_reconcile,
                uses_unwrap=has_unwrap,
            ))

        # ── createMutable ─────────────────────────────────────────
        for m in self.CREATE_MUTABLE_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            stores.append(SolidStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                is_exported=is_exported,
                store_type="mutable",
            ))

        # ── Store updates ─────────────────────────────────────────
        for m in self.STORE_SETTER_PATTERN.finditer(content):
            setter_name = m.group(1)
            path_key = m.group(2) if m.group(2) else ""
            line = content[:m.start()].count('\n') + 1

            # Determine update type
            full_match = m.group(0)
            if 'produce(' in full_match:
                update_type = "produce"
            elif 'reconcile(' in full_match:
                update_type = "reconcile"
            elif path_key:
                update_type = "path"
            else:
                update_type = "direct"

            store_updates.append(SolidStoreUpdateInfo(
                setter_name=setter_name,
                file=file_path,
                line_number=line,
                update_type=update_type,
                path=[path_key] if path_key else [],
            ))

        return {
            "stores": stores,
            "store_updates": store_updates,
        }
