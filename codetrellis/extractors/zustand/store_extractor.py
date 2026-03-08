"""
Zustand Store Extractor for CodeTrellis

Extracts Zustand store definitions and configuration patterns:
- create() / create<T>() store definitions (v3+)
- createStore() for vanilla (non-React) stores
- createWithEqualityFn() for custom equality (v4.4+)
- useStore() hook bindings
- Store initial state shape and fields
- Store actions (set, get, subscribe patterns)
- Immer integration (set with produce)
- Combined stores (via middleware or manual composition)
- Store factory patterns (parameterized stores)
- Context-based stores (createContext for SSR/testing)

Supports:
- Zustand v1.x (basic create with setState/getState)
- Zustand v2.x (slices pattern emergence)
- Zustand v3.x (stable API, middleware ecosystem)
- Zustand v4.x (useBoundStore, subscribeWithSelector, core refactor,
                  createWithEqualityFn, shallow from zustand/shallow)
- Zustand v5.x (React 19 support, use() hook, getInitialState,
                  TypeScript improvements, zustand/react export)

Part of CodeTrellis v4.48 - Zustand Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ZustandStoreInfo:
    """Information about a Zustand store definition."""
    name: str
    file: str = ""
    line_number: int = 0
    creation_method: str = ""  # create, createStore, createWithEqualityFn
    state_fields: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    has_typescript: bool = False
    type_name: str = ""  # TypeScript interface/type for state
    has_immer: bool = False
    has_devtools: bool = False
    has_persist: bool = False
    has_subscribeWithSelector: bool = False
    is_exported: bool = False
    is_vanilla: bool = False  # createStore (no React)
    is_factory: bool = False  # store factory pattern
    has_get_initial_state: bool = False  # v5 getInitialState
    zustand_version: str = ""  # v1, v2, v3, v4, v5


@dataclass
class ZustandSliceInfo:
    """Information about a Zustand slice (composable store piece)."""
    name: str
    file: str = ""
    line_number: int = 0
    state_fields: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    slice_type: str = ""  # function, object, StateCreator
    has_typescript: bool = False
    type_name: str = ""


@dataclass
class ZustandContextStoreInfo:
    """Information about a Zustand context-based store (SSR/testing)."""
    name: str
    file: str = ""
    line_number: int = 0
    store_name: str = ""
    provider_name: str = ""
    hook_name: str = ""
    is_exported: bool = False


class ZustandStoreExtractor:
    """
    Extracts Zustand store definitions from source code.

    Detects:
    - create() store definitions with state + actions
    - createStore() vanilla stores
    - createWithEqualityFn() custom equality stores (v4.4+)
    - Slice patterns (composable store pieces)
    - Context-based stores (createContext)
    - Store factory patterns
    - Middleware chains (devtools, persist, subscribeWithSelector, immer)
    - TypeScript generic type annotations
    """

    # create() / create<T>() store (React hook-based)
    CREATE_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'create\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # createStore() vanilla store
    CREATE_VANILLA_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createStore\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # createWithEqualityFn() (v4.4+)
    CREATE_WITH_EQUALITY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createWithEqualityFn\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # createContext() for context-based stores (v5+, previously zustand/context)
    CREATE_CONTEXT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+'
        r'(?:\{([^}]+)\}|(\w+))\s*=\s*'
        r'createContext\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # Slice pattern: const createXSlice = (set, get, api) => ({...})
    SLICE_FUNCTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w*[Ss]lice\w*)\s*[:=]\s*'
        r'(?:\([^)]*\)|(?:set|get|store))\s*(?:=>|:)',
        re.MULTILINE
    )

    # StateCreator type slice: const xSlice: StateCreator<...> = (set, get) => ({...})
    STATE_CREATOR_SLICE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*:\s*'
        r'StateCreator\s*<[^>]*>\s*=\s*\(',
        re.MULTILINE
    )

    # Store factory pattern: const createXStore = (...) => create(...)
    STORE_FACTORY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var|function)\s+(\w+)\s*[:=]?\s*'
        r'(?:\([^)]*\))\s*(?:=>|:)?\s*(?:{[^}]*)?create\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # Middleware detection patterns
    MIDDLEWARE_PATTERNS = {
        'devtools': re.compile(r'devtools\s*\(', re.MULTILINE),
        'persist': re.compile(r'persist\s*\(', re.MULTILINE),
        'subscribeWithSelector': re.compile(r'subscribeWithSelector\s*\(', re.MULTILINE),
        'immer': re.compile(r'immer\s*\(', re.MULTILINE),
        'combine': re.compile(r'combine\s*\(', re.MULTILINE),
        'redux': re.compile(r'redux\s*\(', re.MULTILINE),
        'lens': re.compile(r'lens\s*\(', re.MULTILINE),
    }

    # TypeScript type extraction
    TS_TYPE_PATTERN = re.compile(
        r'create\s*<\s*(\w+)(?:\s*&\s*\w+)*\s*>',
        re.MULTILINE
    )

    # State field extraction (within store body)
    STATE_FIELD_PATTERN = re.compile(
        r'^\s+(\w+)\s*:\s*(?!function)',
        re.MULTILINE
    )

    # Action/method extraction (within store body)
    ACTION_PATTERN = re.compile(
        r'^\s+(\w+)\s*:\s*(?:\([^)]*\)|)\s*(?:=>|\{)',
        re.MULTILINE
    )

    # set() call extraction
    SET_CALL_PATTERN = re.compile(
        r'set\s*\(\s*(?:\(|{|\w)',
        re.MULTILINE
    )

    # get() call extraction
    GET_CALL_PATTERN = re.compile(
        r'get\s*\(\s*\)',
        re.MULTILINE
    )

    # getInitialState (v5)
    GET_INITIAL_STATE_PATTERN = re.compile(
        r'getInitialState\s*\(',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Zustand store patterns from source code."""
        stores = []
        slices = []
        context_stores = []

        # ── create() stores (React hook-based) ────────────────────
        for m in self.CREATE_STORE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            body_start = m.end() - 1
            body = self._extract_balanced_parens(content[body_start:])

            # Detect middleware
            middleware = self._detect_middleware(content[m.start():m.start() + len(body) + 200])

            # Detect TypeScript type
            ts_type_match = re.search(r'create\s*<\s*(\w+)', content[max(0, m.start() - 5):m.end() + 50])
            type_name = ts_type_match.group(1) if ts_type_match else ""
            has_ts = bool(type_name)

            # Extract state fields and actions
            state_fields, actions = self._extract_state_and_actions(body)

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            # Detect version signals
            zustand_version = self._detect_version_from_body(body, content)

            stores.append(ZustandStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                creation_method="create",
                state_fields=state_fields[:30],
                actions=actions[:30],
                middleware=middleware,
                has_typescript=has_ts,
                type_name=type_name,
                has_immer='immer' in middleware,
                has_devtools='devtools' in middleware,
                has_persist='persist' in middleware,
                has_subscribeWithSelector='subscribeWithSelector' in middleware,
                is_exported=is_exported,
                is_vanilla=False,
                is_factory=False,
                has_get_initial_state=bool(self.GET_INITIAL_STATE_PATTERN.search(body)),
                zustand_version=zustand_version,
            ))

        # ── createStore() vanilla stores ──────────────────────────
        for m in self.CREATE_VANILLA_STORE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            body_start = m.end() - 1
            body = self._extract_balanced_parens(content[body_start:])

            middleware = self._detect_middleware(content[m.start():m.start() + len(body) + 200])
            state_fields, actions = self._extract_state_and_actions(body)
            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            stores.append(ZustandStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                creation_method="createStore",
                state_fields=state_fields[:30],
                actions=actions[:30],
                middleware=middleware,
                has_immer='immer' in middleware,
                has_devtools='devtools' in middleware,
                has_persist='persist' in middleware,
                has_subscribeWithSelector='subscribeWithSelector' in middleware,
                is_exported=is_exported,
                is_vanilla=True,
                is_factory=False,
                zustand_version=self._detect_version_from_body(body, content),
            ))

        # ── createWithEqualityFn() stores ─────────────────────────
        for m in self.CREATE_WITH_EQUALITY_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            body_start = m.end() - 1
            body = self._extract_balanced_parens(content[body_start:])

            middleware = self._detect_middleware(content[m.start():m.start() + len(body) + 200])
            state_fields, actions = self._extract_state_and_actions(body)
            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            stores.append(ZustandStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                creation_method="createWithEqualityFn",
                state_fields=state_fields[:30],
                actions=actions[:30],
                middleware=middleware,
                has_immer='immer' in middleware,
                has_devtools='devtools' in middleware,
                has_persist='persist' in middleware,
                has_subscribeWithSelector='subscribeWithSelector' in middleware,
                is_exported=is_exported,
                is_vanilla=False,
                is_factory=False,
                zustand_version="v4",
            ))

        # ── Context-based stores ──────────────────────────────────
        for m in self.CREATE_CONTEXT_PATTERN.finditer(content):
            destructured = m.group(1)
            direct_name = m.group(2)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            if destructured:
                names = [n.strip() for n in destructured.split(',') if n.strip()]
                provider = next((n for n in names if 'Provider' in n), "")
                hook = next((n for n in names if n.startswith('use')), "")
                store_name = next((n for n in names if n not in (provider, hook)), names[0] if names else "")
            else:
                store_name = direct_name or ""
                provider = ""
                hook = ""

            context_stores.append(ZustandContextStoreInfo(
                name=store_name,
                file=file_path,
                line_number=line,
                store_name=store_name,
                provider_name=provider,
                hook_name=hook,
                is_exported=is_exported,
            ))

        # ── Slice patterns ────────────────────────────────────────
        for m in self.SLICE_FUNCTION_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            # Grab a chunk after the match for field extraction
            chunk_end = min(len(content), m.end() + 500)
            chunk = content[m.end():chunk_end]
            state_fields, actions = self._extract_state_and_actions(chunk)

            slices.append(ZustandSliceInfo(
                name=name,
                file=file_path,
                line_number=line,
                state_fields=state_fields[:20],
                actions=actions[:20],
                slice_type="function",
            ))

        for m in self.STATE_CREATOR_SLICE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            chunk_end = min(len(content), m.end() + 500)
            chunk = content[m.end():chunk_end]
            state_fields, actions = self._extract_state_and_actions(chunk)

            slices.append(ZustandSliceInfo(
                name=name,
                file=file_path,
                line_number=line,
                state_fields=state_fields[:20],
                actions=actions[:20],
                slice_type="StateCreator",
                has_typescript=True,
            ))

        return {
            'stores': stores,
            'slices': slices,
            'context_stores': context_stores,
        }

    def _detect_middleware(self, text: str) -> List[str]:
        """Detect middleware used in a store definition."""
        detected = []
        for name, pattern in self.MIDDLEWARE_PATTERNS.items():
            if pattern.search(text):
                detected.append(name)
        return detected

    def _detect_version_from_body(self, body: str, full_content: str) -> str:
        """Detect Zustand version from API usage patterns."""
        # v5 indicators
        v5_indicators = [
            'getInitialState',
            'zustand/react',
            'createWithEqualityFn',
            'useShallow',
        ]
        if any(ind in full_content for ind in v5_indicators):
            return "v5"

        # v4 indicators
        v4_indicators = [
            'subscribeWithSelector',
            'shallow',
            'zustand/shallow',
            'zustand/middleware',
            'zustand/vanilla',
            'createWithEqualityFn',
        ]
        if any(ind in full_content for ind in v4_indicators):
            return "v4"

        # v3 indicators (stable create API)
        if 'create' in full_content:
            return "v3"

        return ""

    def _extract_state_and_actions(self, body: str) -> tuple:
        """Extract state fields and action methods from a store body."""
        state_fields = []
        actions = []

        lines = body.split('\n')
        for line in lines[:60]:  # Limit to first 60 lines of body
            stripped = line.strip()
            if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
                continue

            # Action: name: (args) => ... or name: function ...
            action_match = re.match(
                r'(\w+)\s*:\s*(?:async\s+)?(?:\([^)]*\)|(?:\w+))\s*=>',
                stripped
            )
            if action_match:
                action_name = action_match.group(1)
                if action_name not in ('get', 'set'):
                    actions.append(action_name)
                continue

            # State field: name: value (not a function)
            field_match = re.match(
                r'(\w+)\s*:\s*(?:\'[^\']*\'|"[^"]*"|`[^`]*`|\d+|true|false|null|undefined|\[|\{|0)',
                stripped
            )
            if field_match:
                state_fields.append(field_match.group(1))
                continue

        return state_fields, actions

    @staticmethod
    def _extract_balanced_parens(text: str, max_len: int = 3000) -> str:
        """Extract text within balanced parentheses."""
        if not text or text[0] != '(':
            return text[:500]

        depth = 0
        for i, ch in enumerate(text[:max_len]):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    return text[:i + 1]
        return text[:min(len(text), max_len)]
