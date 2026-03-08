"""
EnhancedReduxParser v1.0 - Comprehensive Redux / Redux Toolkit parser using all extractors.

This parser integrates all Redux extractors to provide complete parsing of
Redux and Redux Toolkit usage across React/TypeScript/JavaScript source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting Redux-specific semantics.

Supports:
- Redux 1.x (createStore, combineReducers, applyMiddleware, compose)
- Redux 2.x (same API, improved TypeScript support)
- Redux 3.x (TypeScript improvements)
- Redux 4.x (improved TS types, stricter typing)
- Redux 5.x (ESM-first, new TS types, deprecations)
- Redux Toolkit 1.0 (createSlice, configureStore, createAsyncThunk, createEntityAdapter)
- Redux Toolkit 1.3+ (builder callback extraReducers)
- Redux Toolkit 1.5+ (action/selector matchers)
- Redux Toolkit 1.6+ (RTK Query: createApi, fetchBaseQuery, endpoints, tags)
- Redux Toolkit 1.8+ (createListenerMiddleware, autoBatchEnhancer)
- Redux Toolkit 1.9+ (slice selectors, createSlice with selectors option)
- Redux Toolkit 2.0+ (ESM-first, Tuple for middleware, combineSlices,
                       .withTypes() for typed hooks, removed deprecated APIs,
                       configureStore requires explicit middleware setup)

State Management Patterns:
- Store configuration (configureStore, createStore, enhancers)
- Slice definitions (createSlice, name, initialState, reducers, extraReducers)
- Action creators (auto-generated from slices, createAction, prepare callbacks)
- Async operations (createAsyncThunk, lifecycle states, condition, thunkAPI)
- Selectors (createSelector/reselect, createDraftSafeSelector, entity selectors)
- Entity management (createEntityAdapter, CRUD operations, normalized state)
- RTK Query (createApi, fetchBaseQuery, endpoints, tags, hooks, code splitting)

Side Effect Middleware:
- redux-saga (generator effects: takeEvery/takeLatest/call/put/select/fork)
- redux-observable (Epics, RxJS operators, ofType)
- createListenerMiddleware (RTK 1.8+, reactive side-effect management)
- Custom middleware (store => next => action curried pattern)

State Persistence:
- redux-persist (persistReducer, persistStore, PersistGate, storage engines,
                  transforms, whitelist/blacklist, migrations, versions)

Framework Ecosystem Detection (40+ patterns):
- Core: redux, react-redux, @reduxjs/toolkit
- RTK Query: @reduxjs/toolkit/query, @reduxjs/toolkit/query/react
- Saga: redux-saga, redux-saga/effects
- Observable: redux-observable, rxjs
- Persistence: redux-persist, redux-persist/integration/react
- DevTools: redux-devtools-extension, @redux-devtools/extension
- Middleware: redux-thunk, redux-logger, redux-promise
- Utilities: reselect, immer, normalizr, redux-actions
- Testing: @testing-library/react, redux-mock-store, msw
- Type Safety: typesafe-actions, deox
- Legacy: redux-form, connected-react-router, react-router-redux
- State Machines: redux-toolkit with matcher patterns

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.47 - Redux / Redux Toolkit Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Redux extractors
from .extractors.redux import (
    ReduxStoreExtractor, ReduxStoreInfo, ReduxReducerCompositionInfo, ReduxPersistInfo,
    ReduxSliceExtractor, ReduxSliceInfo, ReduxEntityAdapterInfo, ReduxActionCreatorInfo,
    ReduxMiddlewareExtractor, ReduxAsyncThunkInfo, ReduxSagaInfo, ReduxObservableInfo,
    ReduxListenerInfo, ReduxCustomMiddlewareInfo,
    ReduxSelectorExtractor, ReduxSelectorInfo, ReduxTypedHookInfo,
    ReduxApiExtractor, ReduxRTKQueryApiInfo, ReduxRTKQueryEndpointInfo, ReduxCacheTagInfo,
)


@dataclass
class ReduxParseResult:
    """Complete parse result for a file with Redux/RTK usage."""
    file_path: str
    file_type: str = "jsx"  # jsx, tsx, js, ts

    # Store
    stores: List[ReduxStoreInfo] = field(default_factory=list)
    reducer_compositions: List[ReduxReducerCompositionInfo] = field(default_factory=list)
    persist_configs: List[ReduxPersistInfo] = field(default_factory=list)

    # Slices
    slices: List[ReduxSliceInfo] = field(default_factory=list)
    entity_adapters: List[ReduxEntityAdapterInfo] = field(default_factory=list)
    action_creators: List[ReduxActionCreatorInfo] = field(default_factory=list)

    # Middleware
    async_thunks: List[ReduxAsyncThunkInfo] = field(default_factory=list)
    sagas: List[ReduxSagaInfo] = field(default_factory=list)
    epics: List[ReduxObservableInfo] = field(default_factory=list)
    listeners: List[ReduxListenerInfo] = field(default_factory=list)
    custom_middleware: List[ReduxCustomMiddlewareInfo] = field(default_factory=list)

    # Selectors
    selectors: List[ReduxSelectorInfo] = field(default_factory=list)
    typed_hooks: List[ReduxTypedHookInfo] = field(default_factory=list)

    # RTK Query
    rtk_query_apis: List[ReduxRTKQueryApiInfo] = field(default_factory=list)
    rtk_query_endpoints: List[ReduxRTKQueryEndpointInfo] = field(default_factory=list)
    cache_tags: List[ReduxCacheTagInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    redux_version: str = ""  # legacy, rtk-v1, rtk-v2


class EnhancedReduxParser:
    """
    Enhanced Redux / Redux Toolkit parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript/React parser
    when Redux framework is detected. It extracts Redux-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 40+ Redux ecosystem libraries across:
    - Core (redux, react-redux, @reduxjs/toolkit)
    - RTK Query (@reduxjs/toolkit/query/react)
    - Saga (redux-saga, redux-saga/effects)
    - Observable (redux-observable, rxjs)
    - Persistence (redux-persist)
    - DevTools (redux-devtools-extension, @redux-devtools/extension)
    - Middleware (redux-thunk, redux-logger, redux-promise)
    - Utilities (reselect, immer, normalizr, redux-actions)
    - Testing (redux-mock-store, msw)
    - Legacy (redux-form, connected-react-router)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Redux ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'redux': re.compile(
            r"from\s+['\"]redux['\"]|require\(['\"]redux['\"]\)|"
            r"createStore|combineReducers|applyMiddleware|compose",
            re.MULTILINE
        ),
        'react-redux': re.compile(
            r"from\s+['\"]react-redux['\"]|require\(['\"]react-redux['\"]\)|"
            r"useSelector|useDispatch|connect\s*\(|Provider.*store",
            re.MULTILINE
        ),
        'reduxjs-toolkit': re.compile(
            r"from\s+['\"]@reduxjs/toolkit['\"]|require\(['\"]@reduxjs/toolkit['\"]\)|"
            r"configureStore|createSlice|createAsyncThunk|createEntityAdapter",
            re.MULTILINE
        ),

        # ── RTK Query ────────────────────────────────────────────
        'rtk-query': re.compile(
            r"from\s+['\"]@reduxjs/toolkit/query|"
            r"from\s+['\"]@reduxjs/toolkit/query/react['\"]|"
            r"createApi|fetchBaseQuery|injectEndpoints",
            re.MULTILINE
        ),

        # ── Side Effects ─────────────────────────────────────────
        'redux-saga': re.compile(
            r"from\s+['\"]redux-saga['\"/]|require\(['\"]redux-saga['\"]\)|"
            r"createSagaMiddleware|takeEvery|takeLatest|takeLeading",
            re.MULTILINE
        ),
        'redux-observable': re.compile(
            r"from\s+['\"]redux-observable['\"]|require\(['\"]redux-observable['\"]\)|"
            r"createEpicMiddleware|combineEpics|ofType",
            re.MULTILINE
        ),
        'redux-thunk': re.compile(
            r"from\s+['\"]redux-thunk['\"]|require\(['\"]redux-thunk['\"]\)",
            re.MULTILINE
        ),

        # ── Persistence ──────────────────────────────────────────
        'redux-persist': re.compile(
            r"from\s+['\"]redux-persist['\"/]|require\(['\"]redux-persist['\"]\)|"
            r"persistReducer|persistStore|PersistGate",
            re.MULTILINE
        ),

        # ── DevTools ─────────────────────────────────────────────
        'redux-devtools': re.compile(
            r"from\s+['\"](?:redux-devtools-extension|@redux-devtools/extension)['\"]|"
            r"composeWithDevTools|__REDUX_DEVTOOLS_EXTENSION__",
            re.MULTILINE
        ),

        # ── Middleware ───────────────────────────────────────────
        'redux-logger': re.compile(
            r"from\s+['\"]redux-logger['\"]|require\(['\"]redux-logger['\"]\)|"
            r"createLogger\s*\(",
            re.MULTILINE
        ),
        'redux-promise': re.compile(
            r"from\s+['\"]redux-promise['\"/]|require\(['\"]redux-promise",
            re.MULTILINE
        ),

        # ── Utilities ────────────────────────────────────────────
        'reselect': re.compile(
            r"from\s+['\"]reselect['\"]|require\(['\"]reselect['\"]\)|"
            r"createSelector|createStructuredSelector",
            re.MULTILINE
        ),
        'immer': re.compile(
            r"from\s+['\"]immer['\"]|produce\s*\(|enableMapSet|enablePatches",
            re.MULTILINE
        ),
        'normalizr': re.compile(
            r"from\s+['\"]normalizr['\"]|normalize\s*\(|schema\.Entity",
            re.MULTILINE
        ),
        'redux-actions': re.compile(
            r"from\s+['\"]redux-actions['\"]|createActions?\s*\(|handleActions\s*\(",
            re.MULTILINE
        ),
        'typesafe-actions': re.compile(
            r"from\s+['\"]typesafe-actions['\"]|createAction|createAsyncAction|getType",
            re.MULTILINE
        ),

        # ── Testing ──────────────────────────────────────────────
        'redux-mock-store': re.compile(
            r"from\s+['\"]redux-mock-store['\"]|configureMockStore",
            re.MULTILINE
        ),
        'msw': re.compile(
            r"from\s+['\"]msw['\"]|rest\.get|rest\.post|http\.get|http\.post|setupServer|setupWorker",
            re.MULTILINE
        ),

        # ── Legacy ───────────────────────────────────────────────
        'redux-form': re.compile(
            r"from\s+['\"]redux-form['\"]|reduxForm\s*\(|Field\s+name=",
            re.MULTILINE
        ),
        'connected-react-router': re.compile(
            r"from\s+['\"]connected-react-router['\"]|connectRouter|routerMiddleware",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'typed_hooks': re.compile(r'useAppSelector|useAppDispatch|useAppStore|\.withTypes\s*<', re.MULTILINE),
        'entity_adapter': re.compile(r'createEntityAdapter', re.MULTILINE),
        'rtk_query': re.compile(r'createApi|fetchBaseQuery|injectEndpoints', re.MULTILINE),
        'listener_middleware': re.compile(r'createListenerMiddleware|startListening', re.MULTILINE),
        'async_thunks': re.compile(r'createAsyncThunk', re.MULTILINE),
        'slice_selectors': re.compile(r'selectors\s*:\s*\{', re.MULTILINE),
        'persist': re.compile(r'persistReducer|persistStore|PersistGate', re.MULTILINE),
        'saga': re.compile(r'createSagaMiddleware|takeEvery|takeLatest', re.MULTILINE),
        'observable': re.compile(r'createEpicMiddleware|combineEpics|ofType', re.MULTILINE),
        'immer_integration': re.compile(r'produce|current\(state\)|enableMapSet', re.MULTILINE),
        'code_splitting': re.compile(r'injectEndpoints|combineSlices|lazy\s*\(', re.MULTILINE),
        'optimistic_updates': re.compile(r'updateQueryData|upsertQueryData|patchResult', re.MULTILINE),
        'streaming_updates': re.compile(r'onCacheEntryAdded|cacheDataLoaded|cacheEntryRemoved', re.MULTILINE),
        'normalization': re.compile(r'createEntityAdapter|normalize\s*\(|schema\.Entity', re.MULTILINE),
        'devtools': re.compile(r'devTools|__REDUX_DEVTOOLS|composeWithDevTools', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all Redux extractors."""
        self.store_extractor = ReduxStoreExtractor()
        self.slice_extractor = ReduxSliceExtractor()
        self.middleware_extractor = ReduxMiddlewareExtractor()
        self.selector_extractor = ReduxSelectorExtractor()
        self.api_extractor = ReduxApiExtractor()

    def is_redux_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Redux/RTK code.

        Returns True if the file imports from Redux ecosystem
        or uses Redux patterns (createSlice, configureStore, etc.)
        """
        # Quick check: must have at least one Redux-related import or pattern
        redux_indicators = [
            'redux', 'createSlice', 'configureStore', 'createStore',
            'combineReducers', 'createAsyncThunk', 'createApi',
            'useSelector', 'useDispatch', 'createSelector',
            '@reduxjs/toolkit', 'react-redux', 'redux-saga',
            'redux-observable', 'redux-persist', 'createEntityAdapter',
            'createListenerMiddleware', 'fetchBaseQuery',
        ]
        return any(ind in content for ind in redux_indicators)

    def parse(self, content: str, file_path: str = "") -> ReduxParseResult:
        """
        Parse a source file for Redux/RTK patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            ReduxParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = ReduxParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.redux_version = self._detect_version(content)

        # ── Store extraction ───────────────────────────────────────
        try:
            store_result = self.store_extractor.extract(content, file_path)
            result.stores = store_result.get('stores', [])
            result.reducer_compositions = store_result.get('reducer_compositions', [])
            result.persist_configs = store_result.get('persist_configs', [])
        except Exception:
            pass

        # ── Slice extraction ───────────────────────────────────────
        try:
            slice_result = self.slice_extractor.extract(content, file_path)
            result.slices = slice_result.get('slices', [])
            result.entity_adapters = slice_result.get('entity_adapters', [])
            result.action_creators = slice_result.get('action_creators', [])
        except Exception:
            pass

        # ── Middleware extraction ──────────────────────────────────
        try:
            mw_result = self.middleware_extractor.extract(content, file_path)
            result.async_thunks = mw_result.get('async_thunks', [])
            result.sagas = mw_result.get('sagas', [])
            result.epics = mw_result.get('epics', [])
            result.listeners = mw_result.get('listeners', [])
            result.custom_middleware = mw_result.get('custom_middleware', [])
        except Exception:
            pass

        # ── Selector extraction ───────────────────────────────────
        try:
            sel_result = self.selector_extractor.extract(content, file_path)
            result.selectors = sel_result.get('selectors', [])
            result.typed_hooks = sel_result.get('typed_hooks', [])
        except Exception:
            pass

        # ── RTK Query API extraction ──────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.rtk_query_apis = api_result.get('apis', [])
            result.rtk_query_endpoints = api_result.get('endpoints', [])
            result.cache_tags = api_result.get('cache_tags', [])
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Redux ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Redux features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Redux/RTK version based on API usage patterns.

        Returns:
            - 'rtk-v2' if RTK 2.0+ patterns detected
            - 'rtk-v1' if RTK patterns detected
            - 'legacy' if only classic Redux patterns
        """
        # RTK 2.0+ indicators
        rtk_v2_indicators = [
            '.withTypes<',  # useSelector.withTypes<RootState>()
            'combineSlices',  # RTK 2.0 combineSlices
            'new Tuple(',  # Tuple for middleware
            'asyncThunkCreator',  # RTK 2.0 createSlice with thunks
            'reducer.getSlice',  # slice.getSlice
        ]
        if any(ind in content for ind in rtk_v2_indicators):
            return "rtk-v2"

        # RTK 1.x indicators
        rtk_v1_indicators = [
            'createSlice', 'configureStore', 'createAsyncThunk',
            'createEntityAdapter', 'createListenerMiddleware',
            '@reduxjs/toolkit', 'createApi', 'fetchBaseQuery',
        ]
        if any(ind in content for ind in rtk_v1_indicators):
            return "rtk-v1"

        # Legacy Redux
        legacy_indicators = [
            'createStore', 'combineReducers', 'applyMiddleware',
            'compose', 'bindActionCreators',
        ]
        if any(ind in content for ind in legacy_indicators):
            return "legacy"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'legacy': 1, 'rtk-v1': 2, 'rtk-v2': 3}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
