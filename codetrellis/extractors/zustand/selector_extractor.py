"""
Zustand Selector Extractor for CodeTrellis

Extracts Zustand selector patterns and hook usage:
- Inline selectors in useStore(state => state.x)
- Named selector functions (selectX = (state) => state.x)
- Shallow comparison selectors (shallow from zustand/shallow)
- useShallow() hook (v5+)
- Custom equality functions
- Derived/computed selectors
- Auto-generated selectors (createSelectors pattern)
- Multiple field selectors

Supports:
- Zustand v1-v3 (basic selector pattern)
- Zustand v4 (shallow import, subscribeWithSelector middleware)
- Zustand v5 (useShallow hook, zustand/react import)

Part of CodeTrellis v4.48 - Zustand Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ZustandSelectorInfo:
    """Information about a Zustand selector."""
    name: str
    file: str = ""
    line_number: int = 0
    selector_type: str = ""  # inline, named, shallow, useShallow, auto
    state_path: str = ""  # state.user.name path
    is_memoized: bool = False
    has_shallow: bool = False
    has_custom_equality: bool = False
    fields_selected: List[str] = field(default_factory=list)
    is_exported: bool = False


@dataclass
class ZustandHookUsageInfo:
    """Information about Zustand hook usage (useStore calls)."""
    hook_name: str
    file: str = ""
    line_number: int = 0
    store_name: str = ""  # Which store is being used
    selector_type: str = ""  # none, inline, named, destructured
    selected_fields: List[str] = field(default_factory=list)
    has_shallow: bool = False
    has_equality_fn: bool = False


class ZustandSelectorExtractor:
    """
    Extracts Zustand selector patterns and hook usage.

    Detects:
    - Inline selectors: useStore(state => state.count)
    - Destructured: const { count, increment } = useStore()
    - Named selectors: const selectCount = (state) => state.count
    - Shallow equality: useStore(selector, shallow)
    - useShallow: useStore(useShallow(state => ({...})))
    - Auto selectors: createSelectors pattern
    - Subscriptions: store.subscribe(selector, callback)
    """

    # Named selector: const selectX = (state: T) => state.x
    NAMED_SELECTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(select\w+|get\w+)\s*=\s*'
        r'\(\s*(?:state|s)\s*(?::\s*\w+)?\s*\)\s*=>\s*'
        r'(state|s)\.([\w.]+)',
        re.MULTILINE
    )

    # Multi-field named selector: const selectUser = (state) => ({ name: state.name, email: state.email })
    MULTI_FIELD_SELECTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(select\w+|get\w+)\s*=\s*'
        r'\(\s*(?:state|s)\s*(?::\s*\w+)?\s*\)\s*=>\s*'
        r'\(\s*\{([^}]+)\}\s*\)',
        re.MULTILINE
    )

    # Hook usage: useStore(state => state.x)
    HOOK_INLINE_SELECTOR_PATTERN = re.compile(
        r'(\w+)\s*\(\s*(?:\(\s*)?(?:state|s)\s*(?::\s*\w+)?\s*\)?\s*=>\s*'
        r'(?:state|s)\.([\w.]+)',
        re.MULTILINE
    )

    # Hook usage with shallow: useStore(selector, shallow)
    HOOK_SHALLOW_PATTERN = re.compile(
        r'(\w+)\s*\([^,]+,\s*shallow\s*\)',
        re.MULTILINE
    )

    # Hook usage with useShallow (v5): useStore(useShallow(state => ({...})))
    HOOK_USE_SHALLOW_PATTERN = re.compile(
        r'(\w+)\s*\(\s*useShallow\s*\(',
        re.MULTILINE
    )

    # Destructured usage: const { x, y } = useStore()
    HOOK_DESTRUCTURED_PATTERN = re.compile(
        r'const\s+\{\s*([^}]+)\}\s*=\s*(\w+)\s*\(\s*\)',
        re.MULTILINE
    )

    # Auto selectors pattern: createSelectors(useStore)
    AUTO_SELECTORS_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createSelectors?\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # subscribe with selector: store.subscribe(selector, callback)
    SUBSCRIBE_SELECTOR_PATTERN = re.compile(
        r'(\w+)\.subscribe\s*\(\s*'
        r'(?:\(\s*)?(?:state|s)\s*(?::\s*\w+)?\s*\)?\s*=>\s*'
        r'(?:state|s)\.([\w.]+)',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Zustand selector patterns from source code."""
        selectors = []
        hook_usages = []

        # ── Named selectors ───────────────────────────────────────
        for m in self.NAMED_SELECTOR_PATTERN.finditer(content):
            name = m.group(1)
            state_path = m.group(3)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            selectors.append(ZustandSelectorInfo(
                name=name,
                file=file_path,
                line_number=line,
                selector_type="named",
                state_path=state_path,
                fields_selected=[state_path.split('.')[0]],
                is_exported=is_exported,
            ))

        # ── Multi-field selectors ─────────────────────────────────
        for m in self.MULTI_FIELD_SELECTOR_PATTERN.finditer(content):
            name = m.group(1)
            body = m.group(2)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            # Extract field names from destructured object
            fields = re.findall(r'(?:state|s)\.(\w+)', body)

            selectors.append(ZustandSelectorInfo(
                name=name,
                file=file_path,
                line_number=line,
                selector_type="named",
                state_path="multi",
                fields_selected=fields[:15],
                is_exported=is_exported,
            ))

        # ── Auto selectors ────────────────────────────────────────
        for m in self.AUTO_SELECTORS_PATTERN.finditer(content):
            name = m.group(1)
            store_name = m.group(2)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            selectors.append(ZustandSelectorInfo(
                name=name,
                file=file_path,
                line_number=line,
                selector_type="auto",
                state_path=store_name,
                is_exported=is_exported,
            ))

        # ── Hook usages ──────────────────────────────────────────
        # Inline selectors
        for m in self.HOOK_INLINE_SELECTOR_PATTERN.finditer(content):
            hook_name = m.group(1)
            state_path = m.group(2)
            line = content[:m.start()].count('\n') + 1

            # Skip non-store hooks
            if hook_name in ('useSelector', 'useCallback', 'useMemo', 'useEffect', 'useState'):
                continue

            hook_usages.append(ZustandHookUsageInfo(
                hook_name=hook_name,
                file=file_path,
                line_number=line,
                store_name=hook_name,
                selector_type="inline",
                selected_fields=[state_path.split('.')[0]],
            ))

        # Shallow usage
        for m in self.HOOK_SHALLOW_PATTERN.finditer(content):
            hook_name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            if hook_name in ('useSelector', 'useCallback', 'useMemo', 'useEffect', 'useState'):
                continue

            hook_usages.append(ZustandHookUsageInfo(
                hook_name=hook_name,
                file=file_path,
                line_number=line,
                store_name=hook_name,
                selector_type="shallow",
                has_shallow=True,
            ))

        # useShallow usage (v5)
        for m in self.HOOK_USE_SHALLOW_PATTERN.finditer(content):
            hook_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            hook_usages.append(ZustandHookUsageInfo(
                hook_name=hook_name,
                file=file_path,
                line_number=line,
                store_name=hook_name,
                selector_type="useShallow",
                has_shallow=True,
            ))

        # Destructured usage
        for m in self.HOOK_DESTRUCTURED_PATTERN.finditer(content):
            fields_str = m.group(1)
            hook_name = m.group(2)
            line = content[:m.start()].count('\n') + 1

            if hook_name in ('useSelector', 'useCallback', 'useMemo', 'useEffect', 'useState', 'useRef'):
                continue

            fields = [f.strip().split(':')[0].strip() for f in fields_str.split(',') if f.strip()]

            hook_usages.append(ZustandHookUsageInfo(
                hook_name=hook_name,
                file=file_path,
                line_number=line,
                store_name=hook_name,
                selector_type="destructured",
                selected_fields=fields[:15],
            ))

        # Subscribe with selector
        for m in self.SUBSCRIBE_SELECTOR_PATTERN.finditer(content):
            store_name = m.group(1)
            state_path = m.group(2)
            line = content[:m.start()].count('\n') + 1

            selectors.append(ZustandSelectorInfo(
                name=f"{store_name}.subscribe",
                file=file_path,
                line_number=line,
                selector_type="subscription",
                state_path=state_path,
                fields_selected=[state_path.split('.')[0]],
            ))

        return {
            'selectors': selectors,
            'hook_usages': hook_usages,
        }
