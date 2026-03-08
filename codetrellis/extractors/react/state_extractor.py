"""
React State Management Extractor for CodeTrellis

Extracts state management patterns from React codebases:
- Redux Toolkit (createSlice, createAsyncThunk, configureStore, RTK Query)
- Zustand (create stores)
- Jotai (atoms, derived atoms, atomWithStorage)
- Recoil (atom, selector, atomFamily)
- MobX (makeObservable, makeAutoObservable, observer)
- Valtio (proxy, snapshot, useSnapshot)
- XState (createMachine, useMachine)
- TanStack Query (useQuery, useMutation, queryClient)
- SWR (useSWR, mutate)
- React Query v5 patterns

Part of CodeTrellis v4.32 - React Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReactStoreInfo:
    """Information about a state management store definition."""
    name: str
    file: str = ""
    line_number: int = 0
    library: str = ""  # redux, zustand, mobx, valtio, xstate
    store_type: str = ""  # slice, store, machine, proxy
    state_shape: List[str] = field(default_factory=list)  # State property names
    actions: List[str] = field(default_factory=list)  # Action/method names
    selectors: List[str] = field(default_factory=list)  # Selector names
    middleware: List[str] = field(default_factory=list)  # Middleware applied
    is_exported: bool = False


@dataclass
class ReactSliceInfo:
    """Information about a Redux Toolkit slice."""
    name: str
    file: str = ""
    line_number: int = 0
    slice_name: str = ""  # name field value
    initial_state_fields: List[str] = field(default_factory=list)
    reducers: List[str] = field(default_factory=list)
    extra_reducers: List[str] = field(default_factory=list)
    async_thunks: List[str] = field(default_factory=list)
    selectors: List[str] = field(default_factory=list)
    is_exported: bool = False


@dataclass
class ReactAtomInfo:
    """Information about a Jotai/Recoil atom."""
    name: str
    file: str = ""
    line_number: int = 0
    library: str = ""  # jotai, recoil
    atom_type: str = "primitive"  # primitive, derived, family, async, writable
    key: str = ""  # Recoil atom key
    default_value: str = ""
    is_exported: bool = False
    dependencies: List[str] = field(default_factory=list)  # For derived atoms


@dataclass
class ReactQueryInfo:
    """Information about a TanStack Query / SWR usage."""
    name: str
    file: str = ""
    line_number: int = 0
    library: str = ""  # tanstack-query, swr
    query_type: str = ""  # query, mutation, infinite, prefetch
    query_key: str = ""
    endpoint: str = ""  # API endpoint being called
    is_enabled: bool = True
    has_error_handling: bool = False
    has_retry: bool = False
    stale_time: str = ""
    cache_time: str = ""


class ReactStateExtractor:
    """
    Extracts state management patterns from React source code.

    Detects:
    - Redux Toolkit slices, async thunks, configureStore
    - Zustand store creation
    - Jotai atoms and derived atoms
    - Recoil atoms, selectors, atomFamily
    - MobX stores and observable patterns
    - Valtio proxy stores
    - XState machines
    - TanStack Query / SWR hooks
    """

    # Redux Toolkit - createSlice
    CREATE_SLICE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createSlice\s*\(\s*\{',
        re.MULTILINE
    )

    # Redux Toolkit - createAsyncThunk
    ASYNC_THUNK_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createAsyncThunk\s*(?:<[^>]*>)?\s*\(\s*'
        r'[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )

    # Redux Toolkit - configureStore
    CONFIGURE_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'configureStore\s*\(\s*\{',
        re.MULTILINE
    )

    # Zustand store
    ZUSTAND_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'create\s*(?:<[^>]*>)?\s*\(\s*'
        r'(?:\(\s*set\s*(?:,\s*get)?\s*\)\s*=>|'
        r'(?:immer|devtools|persist|subscribeWithSelector)\s*\()',
        re.MULTILINE
    )

    # Jotai atoms
    JOTAI_ATOM_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(atom|atomWithStorage|atomWithDefault|atomFamily|selectAtom|atomWithReducer|focusAtom|splitAtom)\s*'
        r'(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # Recoil atoms/selectors
    RECOIL_ATOM_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(atom|selector|atomFamily|selectorFamily)\s*'
        r'(?:<[^>]*>)?\s*\(\s*\{\s*'
        r'key\s*:\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )

    # MobX store
    MOBX_STORE_PATTERN = re.compile(
        r'(?:makeObservable|makeAutoObservable)\s*\(\s*this',
        re.MULTILINE
    )

    MOBX_CLASS_PATTERN = re.compile(
        r'class\s+(\w+(?:Store|State|Model))\s*(?:extends\s+\w+)?\s*\{',
        re.MULTILINE
    )

    # Valtio proxy
    VALTIO_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'proxy\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # XState machine
    XSTATE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:createMachine|Machine)\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # TanStack Query - useQuery
    USE_QUERY_PATTERN = re.compile(
        r'(?:(?:const|let)\s+(?:\{[^}]*\}|\w+)\s*=\s*|return\s+)?'
        r'(useQuery|useMutation|useInfiniteQuery|useSuspenseQuery|usePrefetchQuery)\s*'
        r'(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # SWR
    USE_SWR_PATTERN = re.compile(
        r'(?:const|let)\s+(?:\{[^}]*\}|\w+)\s*=\s*'
        r'(useSWR|useSWRMutation|useSWRInfinite)\s*'
        r'(?:<[^>]*>)?\s*\(\s*'
        r'(?:[\'"`]([^\'"`]+)[\'"`]|(\w+))',
        re.MULTILINE
    )

    # RTK Query - createApi
    RTK_QUERY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createApi\s*\(\s*\{',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract state management patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'stores', 'slices', 'atoms', 'queries'
        """
        stores = []
        slices = []
        atoms = []
        queries = []

        # ── Redux Toolkit Slices ──────────────────────────────────
        for m in self.CREATE_SLICE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            body_start = m.end() - 1  # Start from the {
            body = self._extract_balanced_braces(content[body_start:])

            # Extract slice name
            slice_name_match = re.search(r'name\s*:\s*[\'"]([^\'"]+)[\'"]', body)
            slice_name = slice_name_match.group(1) if slice_name_match else ""

            # Extract initial state fields
            state_fields = self._extract_initial_state_fields(body)

            # Extract reducers
            reducers = self._extract_reducers(body)

            # Extract extra reducers references
            extra_reducers = re.findall(r'\.(?:addCase|addMatcher)\s*\(\s*(\w+)', body)

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            slices.append(ReactSliceInfo(
                name=name,
                file=file_path,
                line_number=line,
                slice_name=slice_name,
                initial_state_fields=state_fields[:20],
                reducers=reducers[:20],
                extra_reducers=extra_reducers[:10],
                is_exported=is_exported,
            ))

        # ── Redux Toolkit Async Thunks ────────────────────────────
        for m in self.ASYNC_THUNK_PATTERN.finditer(content):
            name = m.group(1)
            action_type = m.group(2)
            line = content[:m.start()].count('\n') + 1

            # Attach to nearest slice
            for sl in slices:
                sl.async_thunks.append(name)

        # ── Redux configureStore ──────────────────────────────────
        for m in self.CONFIGURE_STORE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            body_start = m.end() - 1
            body = self._extract_balanced_braces(content[body_start:])

            # Extract middleware
            middleware = re.findall(r'(?:\.concat|\.prepend)\s*\(\s*(\w+)', body)

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            stores.append(ReactStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                library="redux",
                store_type="configureStore",
                middleware=middleware[:10],
                is_exported=is_exported,
            ))

        # ── Zustand Stores ────────────────────────────────────────
        for m in self.ZUSTAND_STORE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            body_start = m.end()
            body_snippet = content[body_start:body_start + 2000]

            state_fields = []
            actions = []
            for prop_match in re.finditer(r'(\w+)\s*:', body_snippet):
                prop_name = prop_match.group(1)
                after = body_snippet[prop_match.end():prop_match.end() + 50]
                if re.match(r'\s*\(', after) or re.match(r'\s*(?:async\s+)?\(', after):
                    actions.append(prop_name)
                else:
                    state_fields.append(prop_name)

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            stores.append(ReactStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                library="zustand",
                store_type="store",
                state_shape=state_fields[:20],
                actions=actions[:20],
                is_exported=is_exported,
            ))

        # ── Jotai Atoms ──────────────────────────────────────────
        for m in self.JOTAI_ATOM_PATTERN.finditer(content):
            name = m.group(1)
            atom_func = m.group(2)
            line = content[:m.start()].count('\n') + 1

            atom_type = "primitive"
            if atom_func in ('atomWithStorage', 'atomWithDefault'):
                atom_type = 'persistent'
            elif atom_func == 'atomFamily':
                atom_type = 'family'
            elif atom_func in ('selectAtom', 'focusAtom', 'splitAtom'):
                atom_type = 'derived'

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            atoms.append(ReactAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                library="jotai",
                atom_type=atom_type,
                is_exported=is_exported,
            ))

        # ── Recoil Atoms/Selectors ────────────────────────────────
        for m in self.RECOIL_ATOM_PATTERN.finditer(content):
            name = m.group(1)
            recoil_type = m.group(2)
            key = m.group(3)
            line = content[:m.start()].count('\n') + 1

            atom_type = "primitive"
            if recoil_type == 'selector':
                atom_type = 'derived'
            elif recoil_type == 'atomFamily':
                atom_type = 'family'
            elif recoil_type == 'selectorFamily':
                atom_type = 'family'

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            atoms.append(ReactAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                library="recoil",
                atom_type=atom_type,
                key=key,
                is_exported=is_exported,
            ))

        # ── MobX Stores ──────────────────────────────────────────
        for m in self.MOBX_CLASS_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            body_start = m.end()
            body_snippet = content[body_start:body_start + 3000]

            if not self.MOBX_STORE_PATTERN.search(body_snippet):
                continue

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            stores.append(ReactStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                library="mobx",
                store_type="class",
                is_exported=is_exported,
            ))

        # ── Valtio Proxies ────────────────────────────────────────
        for m in self.VALTIO_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            stores.append(ReactStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                library="valtio",
                store_type="proxy",
                is_exported=is_exported,
            ))

        # ── XState Machines ───────────────────────────────────────
        for m in self.XSTATE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            stores.append(ReactStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                library="xstate",
                store_type="machine",
                is_exported=is_exported,
            ))

        # ── TanStack Query ────────────────────────────────────────
        for m in self.USE_QUERY_PATTERN.finditer(content):
            hook_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            query_type = "query"
            if "Mutation" in hook_name:
                query_type = "mutation"
            elif "Infinite" in hook_name:
                query_type = "infinite"
            elif "Prefetch" in hook_name:
                query_type = "prefetch"
            elif "Suspense" in hook_name:
                query_type = "suspense"

            # Try to extract query key
            after = content[m.end():m.end() + 300]
            key_match = re.search(r'\{\s*queryKey\s*:\s*\[([^\]]+)\]', after)
            query_key = key_match.group(1).strip() if key_match else ""

            queries.append(ReactQueryInfo(
                name=hook_name,
                file=file_path,
                line_number=line,
                library="tanstack-query",
                query_type=query_type,
                query_key=query_key[:100],
            ))

        # ── SWR ───────────────────────────────────────────────────
        for m in self.USE_SWR_PATTERN.finditer(content):
            hook_name = m.group(1)
            key_literal = m.group(2) or m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            query_type = "query"
            if "Mutation" in hook_name:
                query_type = "mutation"
            elif "Infinite" in hook_name:
                query_type = "infinite"

            queries.append(ReactQueryInfo(
                name=hook_name,
                file=file_path,
                line_number=line,
                library="swr",
                query_type=query_type,
                query_key=key_literal[:100],
            ))

        # ── RTK Query API ─────────────────────────────────────────
        for m in self.RTK_QUERY_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            stores.append(ReactStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                library="rtk-query",
                store_type="api",
                is_exported=is_exported,
            ))

        return {
            'stores': stores,
            'slices': slices,
            'atoms': atoms,
            'queries': queries,
        }

    def _extract_balanced_braces(self, text: str, max_len: int = 5000) -> str:
        """Extract content within balanced braces."""
        depth = 0
        start = None
        for i, ch in enumerate(text[:max_len]):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start:i + 1]
        return text[:max_len] if start is None else text[start:max_len]

    def _extract_initial_state_fields(self, body: str) -> List[str]:
        """Extract field names from initialState object."""
        state_match = re.search(r'initialState\s*[:=]\s*\{([^}]+)\}', body)
        if state_match:
            fields = re.findall(r'(\w+)\s*:', state_match.group(1))
            return fields
        return []

    def _extract_reducers(self, body: str) -> List[str]:
        """Extract reducer names from a createSlice body."""
        reducers_match = re.search(r'reducers\s*:\s*\{', body)
        if reducers_match:
            start = reducers_match.end() - 1
            reducers_body = self._extract_balanced_braces(body[start:])
            return re.findall(r'(\w+)\s*(?:\(|:)', reducers_body)
        return []
