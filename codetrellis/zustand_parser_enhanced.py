"""
EnhancedZustandParser v1.0 - Comprehensive Zustand parser using all extractors.

This parser integrates all Zustand extractors to provide complete parsing of
Zustand state management usage across React/TypeScript/JavaScript source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting Zustand-specific semantics.

Supports:
- Zustand v1.x (basic create with setState/getState, minimal API)
- Zustand v2.x (slices pattern emergence, middleware concept)
- Zustand v3.x (stable API, middleware ecosystem: persist/devtools/immer/combine,
                  zustand/context for SSR/testing, subscribeWithSelector v3.7+)
- Zustand v4.x (core refactor, subpath exports: zustand/middleware,
                  zustand/shallow, zustand/vanilla, zustand/context,
                  createWithEqualityFn, shallow comparison import,
                  improved TypeScript support, React 18 useSyncExternalStore)
- Zustand v5.x (React 19 support, use() hook integration, getInitialState,
                  useShallow from zustand/react, zustand/react as primary export,
                  enhanced TypeScript types, removed deprecated APIs)

State Management Patterns:
- Store definitions (create, createStore, createWithEqualityFn)
- State + actions composition in single store
- Slice pattern (composable store pieces via StateCreator)
- Context-based stores (SSR-safe, per-request state)
- Factory stores (parameterized store creation)

Selector Patterns:
- Inline selectors (useStore(s => s.field))
- Named selectors (const selectField = (s) => s.field)
- Shallow equality (shallow from zustand/shallow)
- useShallow hook (v5: zustand/react/shallow)
- Auto-generated selectors (createSelectors utility)
- Subscription selectors (store.subscribe with selector)

Middleware:
- persist (localStorage, sessionStorage, AsyncStorage, createJSONStorage,
           partialize, version, migrate, merge, skipHydration)
- devtools (Redux DevTools integration, name, enabled, serialize)
- subscribeWithSelector (selective subscriptions)
- immer (immutable updates with produce)
- combine (state + actions merging)
- redux (dispatch/action pattern)
- Custom middleware (enhancer pattern)

Third-party Ecosystem:
- zundo/temporal (undo/redo/time-travel)
- zustand-computed (derived state)
- zustand-broadcast (cross-tab sync)
- zustand-optics (lens-based state access)
- zustand-middleware-* (community middleware)

Framework Ecosystem Detection (20+ patterns):
- Core: zustand, zustand/react, zustand/vanilla
- Middleware: zustand/middleware, zustand/middleware/immer
- Utilities: zustand/shallow, zustand/context (deprecated v4+)
- Third-party: zundo, zustand-computed, zustand-broadcast, zustand-optics
- Ecosystem: react, react-dom, @tanstack/react-query, react-hook-form,
              next, immer, @testing-library/react, vitest, jest

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.48 - Zustand Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Zustand extractors
from .extractors.zustand import (
    ZustandStoreExtractor, ZustandStoreInfo, ZustandSliceInfo, ZustandContextStoreInfo,
    ZustandSelectorExtractor, ZustandSelectorInfo, ZustandHookUsageInfo,
    ZustandMiddlewareExtractor, ZustandPersistInfo, ZustandDevtoolsInfo, ZustandCustomMiddlewareInfo,
    ZustandActionExtractor, ZustandActionInfo, ZustandSubscriptionInfo, ZustandImperativeInfo,
    ZustandApiExtractor, ZustandImportInfo, ZustandIntegrationInfo, ZustandTypeInfo,
)


@dataclass
class ZustandParseResult:
    """Complete parse result for a file with Zustand usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, ts, js

    # Store
    stores: List[ZustandStoreInfo] = field(default_factory=list)
    slices: List[ZustandSliceInfo] = field(default_factory=list)
    context_stores: List[ZustandContextStoreInfo] = field(default_factory=list)

    # Selectors
    selectors: List[ZustandSelectorInfo] = field(default_factory=list)
    hook_usages: List[ZustandHookUsageInfo] = field(default_factory=list)

    # Middleware
    persist_configs: List[ZustandPersistInfo] = field(default_factory=list)
    devtools_configs: List[ZustandDevtoolsInfo] = field(default_factory=list)
    custom_middleware: List[ZustandCustomMiddlewareInfo] = field(default_factory=list)

    # Actions
    actions: List[ZustandActionInfo] = field(default_factory=list)
    subscriptions: List[ZustandSubscriptionInfo] = field(default_factory=list)
    imperative_usages: List[ZustandImperativeInfo] = field(default_factory=list)

    # API
    imports: List[ZustandImportInfo] = field(default_factory=list)
    integrations: List[ZustandIntegrationInfo] = field(default_factory=list)
    types: List[ZustandTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    zustand_version: str = ""  # v1, v2, v3, v4, v5


class EnhancedZustandParser:
    """
    Enhanced Zustand parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript/React parser
    when Zustand framework is detected. It extracts Zustand-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 20+ Zustand ecosystem libraries across:
    - Core (zustand, zustand/react, zustand/vanilla)
    - Middleware (zustand/middleware, zustand/middleware/immer)
    - Utilities (zustand/shallow, zustand/context)
    - Third-party (zundo, zustand-computed, zustand-broadcast)
    - Testing (@testing-library/react, vitest, jest)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Zustand ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'zustand': re.compile(
            r"from\s+['\"]zustand['\"]|require\(['\"]zustand['\"]\)|"
            r"from\s+['\"]zustand/react['\"]",
            re.MULTILINE
        ),
        'zustand-vanilla': re.compile(
            r"from\s+['\"]zustand/vanilla['\"]|"
            r"createStore\s*\(",
            re.MULTILINE
        ),

        # ── Middleware ────────────────────────────────────────────
        'zustand-middleware': re.compile(
            r"from\s+['\"]zustand/middleware['\"]|"
            r"from\s+['\"]zustand/middleware/immer['\"]",
            re.MULTILINE
        ),
        'zustand-persist': re.compile(
            r"persist\s*\(\s*(?:\([^)]*\)\s*=>\s*|create|$)",
            re.MULTILINE
        ),
        'zustand-devtools': re.compile(
            r"devtools\s*\(\s*(?:\([^)]*\)\s*=>\s*|create|$)",
            re.MULTILINE
        ),
        'zustand-immer': re.compile(
            r"from\s+['\"]zustand/middleware/immer['\"]|"
            r"immer\s*\(\s*\(",
            re.MULTILINE
        ),

        # ── Utilities ─────────────────────────────────────────────
        'zustand-shallow': re.compile(
            r"from\s+['\"]zustand/shallow['\"]|"
            r"from\s+['\"]zustand/react['\"].*useShallow",
            re.MULTILINE
        ),
        'zustand-context': re.compile(
            r"from\s+['\"]zustand/context['\"]|"
            r"createContext\s*<",
            re.MULTILINE
        ),

        # ── Third-party ──────────────────────────────────────────
        'zundo': re.compile(
            r"from\s+['\"]zundo['\"]|require\(['\"]zundo['\"]\)|"
            r"temporal\s*\(|\.temporal\.getState",
            re.MULTILINE
        ),
        'zustand-computed': re.compile(
            r"from\s+['\"]zustand-computed['\"]",
            re.MULTILINE
        ),
        'zustand-broadcast': re.compile(
            r"from\s+['\"]zustand-broadcast['\"]",
            re.MULTILINE
        ),
        'zustand-optics': re.compile(
            r"from\s+['\"]zustand-optics['\"]|optic\s*\(",
            re.MULTILINE
        ),
        'zustand-query': re.compile(
            r"from\s+['\"]zustand-query['\"]",
            re.MULTILINE
        ),

        # ── Ecosystem Integration ─────────────────────────────────
        'immer': re.compile(
            r"from\s+['\"]immer['\"]|produce\s*\(",
            re.MULTILINE
        ),
        'react-query': re.compile(
            r"from\s+['\"]@tanstack/react-query['\"]|from\s+['\"]react-query['\"]",
            re.MULTILINE
        ),
        'react-hook-form': re.compile(
            r"from\s+['\"]react-hook-form['\"]",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'create_store': re.compile(r'create\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'create_vanilla': re.compile(r'createStore\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'create_with_equality': re.compile(r'createWithEqualityFn\s*\(', re.MULTILINE),
        'persist': re.compile(r'persist\s*\(', re.MULTILINE),
        'devtools': re.compile(r'devtools\s*\(', re.MULTILINE),
        'subscribe_with_selector': re.compile(r'subscribeWithSelector\s*\(', re.MULTILINE),
        'immer_middleware': re.compile(r'immer\s*\(', re.MULTILINE),
        'combine': re.compile(r'combine\s*\(', re.MULTILINE),
        'redux_middleware': re.compile(r'redux\s*\(', re.MULTILINE),
        'shallow': re.compile(r'(?:shallow|useShallow)\s*\(', re.MULTILINE),
        'use_shallow': re.compile(r'useShallow\s*\(', re.MULTILINE),
        'get_initial_state': re.compile(r'getInitialState\s*\(', re.MULTILINE),
        'temporal': re.compile(r'temporal\s*\(|\.temporal\.', re.MULTILINE),
        'context_store': re.compile(r'createContext\s*\(', re.MULTILINE),
        'slice_pattern': re.compile(r'StateCreator\s*<|[Ss]lice', re.MULTILINE),
        'computed': re.compile(r'zustand-computed|computed\s*\(', re.MULTILINE),
        'broadcast': re.compile(r'zustand-broadcast|broadcast\s*\(', re.MULTILINE),
        'imperative_api': re.compile(r'\.getState\s*\(\)|\.setState\s*\(|\.subscribe\s*\(', re.MULTILINE),
        'factory_store': re.compile(r'=>\s*create\s*\(', re.MULTILINE),
        'skip_hydration': re.compile(r'skipHydration', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all Zustand extractors."""
        self.store_extractor = ZustandStoreExtractor()
        self.selector_extractor = ZustandSelectorExtractor()
        self.middleware_extractor = ZustandMiddlewareExtractor()
        self.action_extractor = ZustandActionExtractor()
        self.api_extractor = ZustandApiExtractor()

    def is_zustand_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Zustand code.

        Returns True if the file imports from Zustand ecosystem
        or uses Zustand patterns (create, useStore, etc.)
        """
        zustand_indicators = [
            'zustand', 'create(', 'createStore(',
            'createWithEqualityFn(', 'useShallow(',
            "from 'zustand", 'from "zustand',
            "from 'zustand/", 'from "zustand/',
            'zustand/middleware', 'zustand/shallow',
            'zustand/vanilla', 'zustand/react',
            'zundo', 'temporal(',
        ]
        return any(ind in content for ind in zustand_indicators)

    def parse(self, content: str, file_path: str = "") -> ZustandParseResult:
        """
        Parse a source file for Zustand patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            ZustandParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = ZustandParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.zustand_version = self._detect_version(content)

        # ── Store extraction ───────────────────────────────────────
        try:
            store_result = self.store_extractor.extract(content, file_path)
            result.stores = store_result.get('stores', [])
            result.slices = store_result.get('slices', [])
            result.context_stores = store_result.get('context_stores', [])
        except Exception:
            pass

        # ── Selector extraction ───────────────────────────────────
        try:
            sel_result = self.selector_extractor.extract(content, file_path)
            result.selectors = sel_result.get('selectors', [])
            result.hook_usages = sel_result.get('hook_usages', [])
        except Exception:
            pass

        # ── Middleware extraction ──────────────────────────────────
        try:
            mw_result = self.middleware_extractor.extract(content, file_path)
            result.persist_configs = mw_result.get('persist_configs', [])
            result.devtools_configs = mw_result.get('devtools_configs', [])
            result.custom_middleware = mw_result.get('custom_middleware', [])
        except Exception:
            pass

        # ── Action extraction ─────────────────────────────────────
        try:
            action_result = self.action_extractor.extract(content, file_path)
            result.actions = action_result.get('actions', [])
            result.subscriptions = action_result.get('subscriptions', [])
            result.imperative_usages = action_result.get('imperative_usages', [])
        except Exception:
            pass

        # ── API extraction ────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.integrations = api_result.get('integrations', [])
            result.types = api_result.get('types', [])
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Zustand ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Zustand features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Zustand version based on API usage patterns.

        Returns:
            - 'v5' if Zustand v5+ patterns detected
            - 'v4' if Zustand v4 patterns detected
            - 'v3' if Zustand v3 patterns detected
            - 'v2' if only basic patterns
            - '' if unknown
        """
        # v5 indicators
        v5_indicators = [
            'useShallow',           # useShallow from zustand/react
            'getInitialState',      # store.getInitialState()
            "zustand/react'",       # zustand/react export
            'zustand/react"',       # zustand/react export
        ]
        if any(ind in content for ind in v5_indicators):
            return "v5"

        # v4 indicators
        v4_indicators = [
            'zustand/shallow',          # subpath export
            'zustand/middleware',        # subpath export
            'zustand/vanilla',           # subpath export
            'createWithEqualityFn',      # v4.4+
            'subscribeWithSelector',     # moved to middleware in v4
            'shallow',                   # shallow import pattern
        ]
        if any(ind in content for ind in v4_indicators):
            return "v4"

        # v3 indicators
        v3_indicators = [
            'zustand/context',          # context API (v3)
            'devtools(',                # middleware (popular from v3)
            'persist(',                 # middleware (popular from v3)
        ]
        if any(ind in content for ind in v3_indicators):
            return "v3"

        # Basic create present = at least v2+
        if 'create(' in content or "from 'zustand'" in content or 'from "zustand"' in content:
            return "v3"  # Most common version

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'v1': 1, 'v2': 2, 'v3': 3, 'v4': 4, 'v5': 5}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
