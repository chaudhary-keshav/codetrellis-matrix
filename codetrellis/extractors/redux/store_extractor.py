"""
Redux Store Extractor for CodeTrellis

Extracts Redux store configuration and setup patterns:
- configureStore (Redux Toolkit) with reducer map, middleware, devTools, preloadedState
- createStore (legacy Redux) with enhancers and applyMiddleware
- combineReducers composition patterns
- redux-persist (persistStore, persistReducer, storage engines, transforms)
- Store enhancers (batched subscribe, devtools extension)
- Store typing (RootState, AppDispatch, TypedUseSelectorHook)

Supports:
- Redux 1.x-5.x (createStore, combineReducers, compose, applyMiddleware)
- Redux Toolkit 1.0-2.x (configureStore, getDefaultMiddleware, Tuple)
- redux-persist v5/v6 (persistReducer, persistStore, PersistGate)
- Redux DevTools Extension (window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__)

Part of CodeTrellis v4.47 - Redux / Redux Toolkit Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReduxStoreInfo:
    """Information about a Redux store configuration."""
    name: str
    file: str = ""
    line_number: int = 0
    creation_method: str = ""  # configureStore, createStore, legacy
    reducer_count: int = 0
    reducer_names: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    has_devtools: bool = False
    has_preloaded_state: bool = False
    has_persist: bool = False
    persist_config: str = ""  # storage engine name
    enhancers: List[str] = field(default_factory=list)
    is_exported: bool = False
    rtk_version: str = ""  # v1 or v2 based on patterns


@dataclass
class ReduxReducerCompositionInfo:
    """Information about combineReducers usage."""
    name: str
    file: str = ""
    line_number: int = 0
    slice_names: List[str] = field(default_factory=list)
    is_root_reducer: bool = False
    is_exported: bool = False


@dataclass
class ReduxPersistInfo:
    """Information about redux-persist configuration."""
    name: str
    file: str = ""
    line_number: int = 0
    storage_engine: str = ""  # localStorage, sessionStorage, AsyncStorage, etc.
    whitelist: List[str] = field(default_factory=list)
    blacklist: List[str] = field(default_factory=list)
    transforms: List[str] = field(default_factory=list)
    has_migration: bool = False
    version: int = 0
    is_exported: bool = False


class ReduxStoreExtractor:
    """
    Extracts Redux store configuration patterns from source code.

    Detects:
    - configureStore (RTK) with full option extraction
    - createStore (legacy) with enhancers
    - combineReducers composition
    - redux-persist setup
    - Store type definitions (RootState, AppDispatch)
    - DevTools configuration
    """

    # configureStore (RTK)
    CONFIGURE_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'configureStore\s*(?:<[^>]*>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # createStore (legacy Redux)
    CREATE_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createStore\s*\(\s*',
        re.MULTILINE
    )

    # combineReducers
    COMBINE_REDUCERS_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'combineReducers\s*(?:<[^>]*>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # persistReducer
    PERSIST_REDUCER_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'persistReducer\s*(?:<[^>]*>)?\s*\(\s*',
        re.MULTILINE
    )

    # persistStore
    PERSIST_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'persistStore\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # RootState / AppDispatch type
    ROOT_STATE_PATTERN = re.compile(
        r'(?:export\s+)?type\s+(RootState|AppState)\s*=\s*'
        r'ReturnType\s*<\s*typeof\s+(\w+)\.getState\s*>',
        re.MULTILINE
    )

    APP_DISPATCH_PATTERN = re.compile(
        r'(?:export\s+)?type\s+(AppDispatch)\s*=\s*'
        r'typeof\s+(\w+)\.dispatch',
        re.MULTILINE
    )

    # applyMiddleware (legacy)
    APPLY_MIDDLEWARE_PATTERN = re.compile(
        r'applyMiddleware\s*\(\s*([^)]+)\)',
        re.MULTILINE
    )

    # compose / composeWithDevTools
    COMPOSE_PATTERN = re.compile(
        r'(?:composeWithDevTools|compose|__REDUX_DEVTOOLS_EXTENSION_COMPOSE__)\s*\(',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Redux store patterns from source code."""
        stores = []
        reducer_compositions = []
        persist_configs = []

        # ── configureStore (RTK) ──────────────────────────────────
        for m in self.CONFIGURE_STORE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            body_start = m.end() - 1
            body = self._extract_balanced_braces(content[body_start:])

            # Extract reducer map
            reducer_names = self._extract_reducer_map(body)

            # Extract middleware
            middleware = self._extract_middleware_config(body)

            # Detect devTools option
            has_devtools = bool(re.search(r'devTools\s*:', body))

            # Detect preloadedState
            has_preloaded = bool(re.search(r'preloadedState\s*:', body))

            # Detect RTK v2 patterns (Tuple instead of array)
            rtk_version = "v2" if 'Tuple' in body or 'new Tuple' in body else "v1"

            # Detect enhancers
            enhancers = []
            enh_match = re.search(r'enhancers\s*:\s*(?:\(.*?\)\s*=>\s*)?[\[\(]([^)\]]+)', body)
            if enh_match:
                enhancers = [e.strip() for e in enh_match.group(1).split(',') if e.strip()]

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            stores.append(ReduxStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                creation_method="configureStore",
                reducer_count=len(reducer_names),
                reducer_names=reducer_names[:30],
                middleware=middleware[:15],
                has_devtools=has_devtools,
                has_preloaded_state=has_preloaded,
                enhancers=enhancers[:10],
                is_exported=is_exported,
                rtk_version=rtk_version,
            ))

        # ── createStore (legacy) ──────────────────────────────────
        for m in self.CREATE_STORE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            after = content[m.end():m.end() + 500]

            # Detect enhancers via applyMiddleware/compose
            middleware = []
            mw_match = self.APPLY_MIDDLEWARE_PATTERN.search(after)
            if mw_match:
                middleware = [mw.strip() for mw in mw_match.group(1).split(',') if mw.strip()]

            has_devtools = bool(self.COMPOSE_PATTERN.search(after))
            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            stores.append(ReduxStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                creation_method="createStore",
                middleware=middleware[:15],
                has_devtools=has_devtools,
                is_exported=is_exported,
                rtk_version="legacy",
            ))

        # ── combineReducers ───────────────────────────────────────
        for m in self.COMBINE_REDUCERS_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            body_start = m.end() - 1
            body = self._extract_balanced_braces(content[body_start:])

            slice_names = re.findall(r'(\w+)\s*(?::\s*\w+)?(?:,|\})', body)
            is_root = 'root' in name.lower() or name == 'rootReducer'
            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            reducer_compositions.append(ReduxReducerCompositionInfo(
                name=name,
                file=file_path,
                line_number=line,
                slice_names=slice_names[:30],
                is_root_reducer=is_root,
                is_exported=is_exported,
            ))

        # ── persistReducer ────────────────────────────────────────
        for m in self.PERSIST_REDUCER_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            after = content[m.end():m.end() + 1000]

            # Look for persist config object
            storage_engine = ""
            storage_match = re.search(r'storage\s*:\s*(\w+)', after)
            if storage_match:
                storage_engine = storage_match.group(1)

            whitelist = []
            wl_match = re.search(r'whitelist\s*:\s*\[([^\]]+)\]', after)
            if wl_match:
                whitelist = [w.strip().strip("'\"") for w in wl_match.group(1).split(',')]

            blacklist = []
            bl_match = re.search(r'blacklist\s*:\s*\[([^\]]+)\]', after)
            if bl_match:
                blacklist = [b.strip().strip("'\"") for b in bl_match.group(1).split(',')]

            transforms = re.findall(r'(createTransform|createFilter|createWhitelistFilter|createBlacklistFilter|encryptTransform)\s*\(', after)

            has_migration = bool(re.search(r'migrate\s*:', after))
            version_match = re.search(r'version\s*:\s*(\d+)', after)
            version = int(version_match.group(1)) if version_match else 0

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            persist_configs.append(ReduxPersistInfo(
                name=name,
                file=file_path,
                line_number=line,
                storage_engine=storage_engine,
                whitelist=whitelist[:20],
                blacklist=blacklist[:20],
                transforms=transforms[:10],
                has_migration=has_migration,
                version=version,
                is_exported=is_exported,
            ))

        # Check for persist on stores
        for m in self.PERSIST_STORE_PATTERN.finditer(content):
            store_name = m.group(2)
            for store in stores:
                if store.name == store_name:
                    store.has_persist = True

        return {
            'stores': stores,
            'reducer_compositions': reducer_compositions,
            'persist_configs': persist_configs,
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

    def _extract_reducer_map(self, body: str) -> List[str]:
        """Extract reducer names from configureStore reducer map."""
        reducer_match = re.search(r'reducer\s*:\s*\{', body)
        if reducer_match:
            start = reducer_match.end() - 1
            reducer_body = self._extract_balanced_braces(body[start:])
            # Extract key names
            return re.findall(r'(\w+)\s*(?::\s*(?:\w+\.reducer|\w+Reducer|\w+))', reducer_body)
        # Single reducer case
        single_match = re.search(r'reducer\s*:\s*(\w+)', body)
        if single_match:
            return [single_match.group(1)]
        return []

    def _extract_middleware_config(self, body: str) -> List[str]:
        """Extract middleware from configureStore."""
        middleware = []
        # RTK v2 Tuple style
        tuple_match = re.search(r'middleware\s*:\s*\(\s*\)\s*=>\s*new\s+Tuple\s*\(\s*([^)]+)', body)
        if tuple_match:
            return [mw.strip() for mw in tuple_match.group(1).split(',') if mw.strip()]

        # getDefaultMiddleware().concat(...)
        concat_matches = re.findall(r'\.concat\s*\(\s*([^)]+)\)', body)
        for cm in concat_matches:
            middleware.extend([mw.strip() for mw in cm.split(',') if mw.strip()])

        # getDefaultMiddleware().prepend(...)
        prepend_matches = re.findall(r'\.prepend\s*\(\s*([^)]+)\)', body)
        for pm in prepend_matches:
            middleware.extend([mw.strip() for mw in pm.split(',') if mw.strip()])

        # Direct middleware array
        array_match = re.search(r'middleware\s*:\s*\[([^\]]+)\]', body)
        if array_match and not middleware:
            middleware = [mw.strip() for mw in array_match.group(1).split(',') if mw.strip()]

        return middleware
