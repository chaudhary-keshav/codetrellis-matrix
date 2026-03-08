"""
EnhancedPreactParser v1.0 - Comprehensive Preact parser using all extractors.

This parser integrates all Preact extractors to provide complete parsing of
Preact framework usage across TypeScript/JavaScript/JSX/TSX source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript parsers,
extracting Preact-specific semantics.

Supports:
- Preact 8.x (classic API: h, Component, linked state, preact-compat)
- Preact X / 10.0 (hooks via preact/hooks, createContext, Fragment, compat)
- Preact 10.5+ (useId, useErrorBoundary)
- Preact 10.11+ (@preact/signals integration)
- Preact 10.19+ (improved signals, TypeScript enhancements)
- Preact 11.x (signals-first architecture, planned)

Core API:
- h(type, props, ...children) — hyperscript virtual DOM creation
- render(vnode, container) — mount/update root component
- Component class — base class for class components
- createContext(defaultValue) — context creation
- createRef() — create ref object
- Fragment / <> — fragment support
- cloneElement, toChildArray, isValidElement — utilities

Hooks (preact/hooks):
- useState(initialState) — reactive state
- useEffect(fn, deps) — side effects
- useContext(Context) — context consumption
- useReducer(reducer, initialState) — complex state
- useRef(initialValue) — mutable ref
- useMemo(fn, deps) — memoized values
- useCallback(fn, deps) — memoized callbacks
- useLayoutEffect(fn, deps) — synchronous effects
- useImperativeHandle(ref, fn) — customize ref handle
- useDebugValue(value) — DevTools display value
- useErrorBoundary(cb) — error boundary hook (Preact-specific)
- useId() — unique ID generation

Signals (@preact/signals):
- signal(initialValue) — reactive signal primitive
- computed(() => derivedValue) — derived computed signal
- effect(() => sideEffect) — reactive side effect
- batch(() => { ... }) — batched signal updates
- untracked(() => value) — untracked read (v2)
- useSignal(initial) — component-scoped signal hook
- useComputed(fn) — component-scoped computed hook
- useSignalEffect(fn) — component-scoped effect hook
- Signal<T> / ReadonlySignal<T> — TypeScript types
- .value — signal value access
- .peek() — untracked signal read

Compatibility (preact/compat):
- React API compatibility layer
- React.createElement, React.Component, React.PureComponent
- React.forwardRef, React.memo, React.lazy, React.Suspense
- React.createPortal, React.StrictMode
- Drop-in replacement for react/react-dom imports

SSR (preact-render-to-string):
- renderToString(vnode) — synchronous SSR
- renderToStringAsync(vnode) — async SSR with Suspense
- renderToReadableStream(vnode) — streaming SSR
- hydrate(vnode, container) — client hydration

Routing:
- preact-router: Router, Route, Link, route() navigate
- wouter-preact: useRoute, useLocation, Link, Switch
- preact-iso: lazy, LocationProvider, ErrorBoundary

Ecosystem Detection (25+ patterns):
- Core: preact, preact/hooks, preact/compat, preact/debug
- Signals: @preact/signals, @preact/signals-core
- Router: preact-router, wouter-preact
- SSR: preact-render-to-string, preact-iso, preact/compat + hydrate
- Build: @preact/preset-vite, preact-cli, WMR
- Frameworks: Fresh (Deno), Astro (@astrojs/preact)
- Styling: goober (CSS-in-JS optimized for Preact)
- Testing: @testing-library/preact, enzyme-adapter-preact
- Utilities: htm (tagged templates), preact-markup, preact-portal
- i18n: preact-i18n
- Web Components: preact-custom-element

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.64 - Preact Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Preact extractors
from .extractors.preact import (
    PreactComponentExtractor, PreactComponentInfo, PreactClassComponentInfo,
    PreactMemoInfo, PreactLazyInfo, PreactForwardRefInfo, PreactErrorBoundaryInfo,
    PreactHookExtractor, PreactHookUsageInfo, PreactCustomHookInfo, PreactHookDependencyInfo,
    PreactSignalExtractor, PreactSignalInfo, PreactComputedInfo, PreactEffectInfo, PreactBatchInfo,
    PreactContextExtractor, PreactContextInfo, PreactContextConsumerInfo,
    PreactApiExtractor, PreactImportInfo, PreactIntegrationInfo, PreactTypeInfo, PreactSSRInfo,
)


@dataclass
class PreactParseResult:
    """Complete parse result for a file with Preact usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, ts, js

    # Components
    components: List[PreactComponentInfo] = field(default_factory=list)
    class_components: List[PreactClassComponentInfo] = field(default_factory=list)
    memos: List[PreactMemoInfo] = field(default_factory=list)
    lazies: List[PreactLazyInfo] = field(default_factory=list)
    forward_refs: List[PreactForwardRefInfo] = field(default_factory=list)
    error_boundaries: List[PreactErrorBoundaryInfo] = field(default_factory=list)

    # Hooks
    hook_usages: List[PreactHookUsageInfo] = field(default_factory=list)
    custom_hooks: List[PreactCustomHookInfo] = field(default_factory=list)
    hook_dependencies: List[PreactHookDependencyInfo] = field(default_factory=list)

    # Signals
    signals: List[PreactSignalInfo] = field(default_factory=list)
    computeds: List[PreactComputedInfo] = field(default_factory=list)
    effects: List[PreactEffectInfo] = field(default_factory=list)
    batches: List[PreactBatchInfo] = field(default_factory=list)

    # Context
    contexts: List[PreactContextInfo] = field(default_factory=list)
    context_consumers: List[PreactContextConsumerInfo] = field(default_factory=list)

    # API
    imports: List[PreactImportInfo] = field(default_factory=list)
    integrations: List[PreactIntegrationInfo] = field(default_factory=list)
    types: List[PreactTypeInfo] = field(default_factory=list)
    ssr_patterns: List[PreactSSRInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    preact_version: str = ""  # v8, v10, v10.5, v10.11, v10.19


class EnhancedPreactParser:
    """
    Enhanced Preact parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript parser when Preact
    framework is detected. It extracts Preact-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 25+ Preact ecosystem libraries.

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Preact ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'preact': re.compile(
            r"from\s+['\"]preact['\"]|require\(['\"]preact['\"]\)",
            re.MULTILINE
        ),
        'preact-hooks': re.compile(
            r"from\s+['\"]preact/hooks['\"]",
            re.MULTILINE
        ),
        'preact-compat': re.compile(
            r"from\s+['\"]preact/compat['\"]|from\s+['\"]preact-compat['\"]",
            re.MULTILINE
        ),
        'preact-debug': re.compile(
            r"from\s+['\"]preact/debug['\"]|import\s+['\"]preact/debug['\"]",
            re.MULTILINE
        ),
        'preact-devtools': re.compile(
            r"from\s+['\"]preact/devtools['\"]",
            re.MULTILINE
        ),

        # ── Signals ───────────────────────────────────────────────
        'preact-signals': re.compile(
            r"from\s+['\"]@preact/signals['\"]",
            re.MULTILINE
        ),
        'preact-signals-core': re.compile(
            r"from\s+['\"]@preact/signals-core['\"]",
            re.MULTILINE
        ),

        # ── Routing ───────────────────────────────────────────────
        'preact-router': re.compile(
            r"from\s+['\"]preact-router['\"]|from\s+['\"]preact-router/",
            re.MULTILINE
        ),
        'wouter-preact': re.compile(
            r"from\s+['\"]wouter-preact['\"]|from\s+['\"]wouter/preact['\"]",
            re.MULTILINE
        ),

        # ── SSR ───────────────────────────────────────────────────
        'preact-render-to-string': re.compile(
            r"from\s+['\"]preact-render-to-string",
            re.MULTILINE
        ),
        'preact-iso': re.compile(
            r"from\s+['\"]preact-iso['\"]",
            re.MULTILINE
        ),

        # ── Build Tools ───────────────────────────────────────────
        'preact-preset-vite': re.compile(
            r"from\s+['\"]@preact/preset-vite['\"]|preact\(\)",
            re.MULTILINE
        ),
        'preact-cli': re.compile(
            r"preact\.config\b|from\s+['\"]preact-cli",
            re.MULTILINE
        ),
        'wmr': re.compile(
            r"from\s+['\"]wmr['\"]",
            re.MULTILINE
        ),

        # ── Frameworks ────────────────────────────────────────────
        'fresh': re.compile(
            r"from\s+['\"](\$fresh|\$fresh/|fresh/)",
            re.MULTILINE
        ),
        'astro-preact': re.compile(
            r"@astrojs/preact",
            re.MULTILINE
        ),

        # ── Styling ───────────────────────────────────────────────
        'goober': re.compile(
            r"from\s+['\"]goober['\"]|from\s+['\"]goober/",
            re.MULTILINE
        ),

        # ── htm ───────────────────────────────────────────────────
        'htm': re.compile(
            r"from\s+['\"]htm['\"]|from\s+['\"]htm/preact['\"]",
            re.MULTILINE
        ),

        # ── Testing ───────────────────────────────────────────────
        'preact-testing-library': re.compile(
            r"from\s+['\"]@testing-library/preact['\"]",
            re.MULTILINE
        ),

        # ── Utilities ─────────────────────────────────────────────
        'preact-markup': re.compile(
            r"from\s+['\"]preact-markup['\"]",
            re.MULTILINE
        ),
        'preact-custom-element': re.compile(
            r"from\s+['\"]preact-custom-element['\"]",
            re.MULTILINE
        ),
        'preact-i18n': re.compile(
            r"from\s+['\"]preact-i18n['\"]",
            re.MULTILINE
        ),

        # ── Vite ──────────────────────────────────────────────────
        'vite': re.compile(
            r"from\s+['\"]vite['\"]",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'h_function': re.compile(r'\bh\s*\(\s*[\'"]?\w+', re.MULTILINE),
        'render': re.compile(r'\brender\s*\(\s*(?:h\(|<)', re.MULTILINE),
        'hydrate': re.compile(r'\bhydrate\s*\(', re.MULTILINE),
        'create_context': re.compile(r'createContext\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'create_ref': re.compile(r'createRef\s*\(', re.MULTILINE),
        'fragment': re.compile(r'<Fragment\b|<>', re.MULTILINE),
        'clone_element': re.compile(r'cloneElement\s*\(', re.MULTILINE),
        'to_child_array': re.compile(r'toChildArray\s*\(', re.MULTILINE),
        'use_state': re.compile(r'useState\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_effect': re.compile(r'useEffect\s*\(', re.MULTILINE),
        'use_context': re.compile(r'useContext\s*\(', re.MULTILINE),
        'use_reducer': re.compile(r'useReducer\s*\(', re.MULTILINE),
        'use_ref': re.compile(r'useRef\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_memo': re.compile(r'useMemo\s*\(', re.MULTILINE),
        'use_callback': re.compile(r'useCallback\s*\(', re.MULTILINE),
        'use_layout_effect': re.compile(r'useLayoutEffect\s*\(', re.MULTILINE),
        'use_imperative_handle': re.compile(r'useImperativeHandle\s*\(', re.MULTILINE),
        'use_debug_value': re.compile(r'useDebugValue\s*\(', re.MULTILINE),
        'use_error_boundary': re.compile(r'useErrorBoundary\s*\(', re.MULTILINE),
        'use_id': re.compile(r'useId\s*\(', re.MULTILINE),
        'signal': re.compile(r'\bsignal\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'computed': re.compile(r'\bcomputed\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'effect': re.compile(r'\beffect\s*\(\s*(?:async\s+)?(?:\(\)\s*=>|function)', re.MULTILINE),
        'batch': re.compile(r'\bbatch\s*\(', re.MULTILINE),
        'use_signal': re.compile(r'useSignal\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_computed': re.compile(r'useComputed\s*\(', re.MULTILINE),
        'use_signal_effect': re.compile(r'useSignalEffect\s*\(', re.MULTILINE),
        'memo': re.compile(r'\bmemo\s*\(', re.MULTILINE),
        'lazy': re.compile(r'\blazy\s*\(', re.MULTILINE),
        'forward_ref': re.compile(r'forwardRef\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'render_to_string': re.compile(r'renderToString\s*\(', re.MULTILINE),
        'render_to_string_async': re.compile(r'renderToStringAsync\s*\(', re.MULTILINE),
        'linked_state': re.compile(r'linkState\s*\(', re.MULTILINE),
        'htm_tagged': re.compile(r'\bhtml\s*`', re.MULTILINE),
        'class_component': re.compile(r'extends\s+(?:Preact\.)?Component\b', re.MULTILINE),
        'compat_mode': re.compile(r"preact/compat|preact-compat", re.MULTILINE),
        'peek': re.compile(r'\.peek\s*\(\s*\)', re.MULTILINE),
        'untracked': re.compile(r'\buntracked\s*\(', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all Preact extractors."""
        self.component_extractor = PreactComponentExtractor()
        self.hook_extractor = PreactHookExtractor()
        self.signal_extractor = PreactSignalExtractor()
        self.context_extractor = PreactContextExtractor()
        self.api_extractor = PreactApiExtractor()

    def is_preact_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Preact code.

        Returns True if the file imports from Preact ecosystem
        or uses Preact-specific patterns.
        """
        preact_indicators = [
            "from 'preact'", 'from "preact"',
            "from 'preact/hooks'", 'from "preact/hooks"',
            "from 'preact/compat'", 'from "preact/compat"',
            "from 'preact-compat'", 'from "preact-compat"',
            "from '@preact/signals'", 'from "@preact/signals"',
            "from '@preact/signals-core'", 'from "@preact/signals-core"',
            "from 'preact-router'", 'from "preact-router"',
            "from 'preact-render-to-string'", 'from "preact-render-to-string"',
            "from 'preact-iso'", 'from "preact-iso"',
            "from 'htm/preact'", 'from "htm/preact"',
            "from 'goober'", 'from "goober"',
            "from '@preact/preset-vite'", 'from "@preact/preset-vite"',
            "from 'wouter-preact'", 'from "wouter-preact"',
            "from '$fresh/", 'from "$fresh/',
            "from 'preact/debug'", 'from "preact/debug"',
            "from '@testing-library/preact'", 'from "@testing-library/preact"',
            "from 'preact-custom-element'", 'from "preact-custom-element"',
            "require('preact')", 'require("preact")',
            'useSignal(', 'useComputed(', 'useSignalEffect(',
            '@preact/', '@astrojs/preact',
        ]
        return any(ind in content for ind in preact_indicators)

    def parse(self, content: str, file_path: str = "") -> PreactParseResult:
        """
        Parse a source file for Preact patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            PreactParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = PreactParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.preact_version = self._detect_version(content)

        # ── Component extraction ───────────────────────────────────
        try:
            comp_result = self.component_extractor.extract(content, file_path)
            result.components = comp_result.get('components', [])
            result.class_components = comp_result.get('class_components', [])
            result.memos = comp_result.get('memos', [])
            result.lazies = comp_result.get('lazies', [])
            result.forward_refs = comp_result.get('forward_refs', [])
            result.error_boundaries = comp_result.get('error_boundaries', [])
        except Exception:
            pass

        # ── Hook extraction ────────────────────────────────────────
        try:
            hook_result = self.hook_extractor.extract(content, file_path)
            result.hook_usages = hook_result.get('hook_usages', [])
            result.custom_hooks = hook_result.get('custom_hooks', [])
            result.hook_dependencies = hook_result.get('hook_dependencies', [])
        except Exception:
            pass

        # ── Signal extraction ──────────────────────────────────────
        try:
            sig_result = self.signal_extractor.extract(content, file_path)
            result.signals = sig_result.get('signals', [])
            result.computeds = sig_result.get('computeds', [])
            result.effects = sig_result.get('effects', [])
            result.batches = sig_result.get('batches', [])
        except Exception:
            pass

        # ── Context extraction ─────────────────────────────────────
        try:
            ctx_result = self.context_extractor.extract(content, file_path)
            result.contexts = ctx_result.get('contexts', [])
            result.context_consumers = ctx_result.get('consumers', [])
        except Exception:
            pass

        # ── API extraction ─────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.integrations = api_result.get('integrations', [])
            result.types = api_result.get('types', [])
            result.ssr_patterns = api_result.get('ssr_patterns', [])
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Preact ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Preact features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Preact version based on API usage and import patterns.

        Returns:
            - 'v10.19' if latest signals integration features
            - 'v10.11' if @preact/signals imports detected
            - 'v10.5' if useId or useErrorBoundary
            - 'v10' if preact/hooks or preact/compat imports
            - 'v8' if preact-compat (no slash) or linkState
            - '' if unknown
        """
        # v10.19+ indicators: latest signal integration
        v10_19_indicators = [
            'useSignalEffect(',
            '@preact/signals-react',
        ]
        if any(ind in content for ind in v10_19_indicators):
            return "v10.19"

        # v10.11+ indicators: @preact/signals
        v10_11_indicators = [
            '@preact/signals',
            '@preact/signals-core',
            'useSignal(',
            'useComputed(',
        ]
        if any(ind in content for ind in v10_11_indicators):
            return "v10.11"

        # v10.5+ indicators
        v10_5_indicators = [
            'useId(',
            'useErrorBoundary(',
        ]
        if any(ind in content for ind in v10_5_indicators):
            return "v10.5"

        # v10 indicators: modern API
        v10_indicators = [
            'preact/hooks',
            'preact/compat',
            'preact/debug',
            'preact/jsx-runtime',
        ]
        if any(ind in content for ind in v10_indicators):
            return "v10"

        # v8 indicators: legacy API
        v8_indicators = [
            'preact-compat',
            'linkState(',
            'this.linkState',
        ]
        if any(ind in content for ind in v8_indicators):
            return "v8"

        # Basic Preact present
        if "from 'preact'" in content or 'from "preact"' in content:
            return "v10"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {
            '': 0, 'v8': 1, 'v10': 2, 'v10.5': 3,
            'v10.11': 4, 'v10.19': 5,
        }
        return version_order.get(v1, 0) - version_order.get(v2, 0)
