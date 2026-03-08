"""
EnhancedSolidParser v1.0 - Comprehensive Solid.js parser using all extractors.

This parser integrates all Solid.js extractors to provide complete parsing of
Solid.js framework usage across TypeScript/JavaScript/JSX/TSX source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript parsers,
extracting Solid.js-specific semantics.

Supports:
- Solid.js v1.0 (initial API: createSignal, createEffect, createMemo, JSX)
- Solid.js v1.1 (startTransition, createDeferred, Suspense improvements)
- Solid.js v1.2-v1.3 (improved hydration, ErrorBoundary, streaming SSR)
- Solid.js v1.4-v1.5 (external sources via from(), improved compilation)
- Solid.js v1.6-v1.7 (partial hydration, improved store, createResource)
- Solid.js v1.8 (Transition API refinements, server functions prep)
- Solid.js v2.0 (SolidStart 1.0, async primitives, improved compilation)

Reactive Primitives:
- createSignal<T>(initialValue) -> [getter, setter]
- createMemo<T>(() => computation)
- createEffect(() => sideEffect)
- createComputed(() => synchronousEffect) (deprecated v2)
- createRenderEffect(() => renderPhaseEffect)
- createReaction(tracking, effect)
- on(deps, fn) explicit dependency tracking
- batch(() => { ... }) batched updates
- untrack(() => value) untracked access
- createRoot(dispose => { ... }) manual root scopes
- observable(accessor) RxJS interop
- from(producer) external reactive sources (v1.4+)
- mapArray / indexArray reactive list mapping

Components:
- Functional components with JSX
- Component<Props> / ParentComponent / FlowComponent / VoidComponent types
- mergeProps / splitProps / children() utilities
- lazy(() => import(...)) code splitting
- <Dynamic component={...} /> dynamic rendering
- Control flow: <Show>, <For>, <Switch>, <Match>, <Index>, <Portal>
- <Suspense>, <ErrorBoundary>

Stores (solid-js/store):
- createStore<T>(initialValue) -> [store, setStore]
- createMutable<T>(initialValue) -> mutable proxy
- produce() for Immer-like updates
- reconcile() for diffing
- unwrap() for raw values
- Path-based setters: setStore('key', 'nested', value)

Resources & Data:
- createResource(fetcher) / createResource(source, fetcher)
- createAsync() (SolidStart v1.0+)
- server$() / createServerData$() / createServerAction$() (SolidStart v0.x)
- cache() / action() / redirect() (SolidStart v1.0+)
- createRouteData / useRouteData / routeData

Routing (@solidjs/router):
- <Route path="..." component={...} /> declarative routes
- useRoutes() config-based routing
- useParams / useNavigate / useLocation / useSearchParams / useMatch
- useBeforeLeave route guards
- Data loading / preload functions

Context:
- createContext<T>(defaultValue)
- useContext(Context)
- Context.Provider

Lifecycle:
- onMount(() => { ... })
- onCleanup(() => { ... })
- onError((err, reset) => { ... })

Ecosystem Detection (30+ patterns):
- Core: solid-js, solid-js/store, solid-js/web, solid-js/html
- Router: @solidjs/router, solid-app-router (legacy)
- Start: solid-start, @solidjs/start, vinxi
- Testing: @solidjs/testing-library, solid-testing-library
- Primitives: @solid-primitives/* (30+ packages)
- UI: @kobalte/core, @ark-ui/solid, solid-headless, solid-toast, solid-icons
- Data: @tanstack/solid-query, @tanstack/solid-table, @tanstack/solid-virtual
- Styling: solid-styled-components, solid-styled, @vanilla-extract/css
- Animation: solid-transition-group, @motionone/solid
- Meta: solid-meta, @solidjs/meta
- Build: vite-plugin-solid, vinxi
- DevTools: solid-devtools

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.62 - Solid.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Solid.js extractors
from .extractors.solidjs import (
    SolidComponentExtractor, SolidComponentInfo, SolidControlFlowInfo,
    SolidSignalExtractor, SolidSignalInfo, SolidMemoInfo, SolidEffectInfo, SolidReactiveUtilInfo,
    SolidStoreExtractor, SolidStoreInfo, SolidStoreUpdateInfo,
    SolidResourceExtractor, SolidResourceInfo, SolidServerFunctionInfo, SolidRouteDataInfo,
    SolidRouterExtractor, SolidRouteInfo, SolidRouterHookInfo,
    SolidApiExtractor, SolidImportInfo, SolidContextInfo, SolidLifecycleInfo, SolidIntegrationInfo, SolidTypeInfo,
)


@dataclass
class SolidParseResult:
    """Complete parse result for a file with Solid.js usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, ts, js

    # Components
    components: List[SolidComponentInfo] = field(default_factory=list)
    control_flows: List[SolidControlFlowInfo] = field(default_factory=list)

    # Signals & Reactivity
    signals: List[SolidSignalInfo] = field(default_factory=list)
    memos: List[SolidMemoInfo] = field(default_factory=list)
    effects: List[SolidEffectInfo] = field(default_factory=list)
    reactive_utils: List[SolidReactiveUtilInfo] = field(default_factory=list)

    # Stores
    stores: List[SolidStoreInfo] = field(default_factory=list)
    store_updates: List[SolidStoreUpdateInfo] = field(default_factory=list)

    # Resources & Data
    resources: List[SolidResourceInfo] = field(default_factory=list)
    server_functions: List[SolidServerFunctionInfo] = field(default_factory=list)
    route_data: List[SolidRouteDataInfo] = field(default_factory=list)

    # Router
    routes: List[SolidRouteInfo] = field(default_factory=list)
    router_hooks: List[SolidRouterHookInfo] = field(default_factory=list)

    # API
    imports: List[SolidImportInfo] = field(default_factory=list)
    contexts: List[SolidContextInfo] = field(default_factory=list)
    lifecycles: List[SolidLifecycleInfo] = field(default_factory=list)
    integrations: List[SolidIntegrationInfo] = field(default_factory=list)
    types: List[SolidTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    solid_version: str = ""  # v1, v1.1, v1.4, v1.6, v1.8, v2


class EnhancedSolidParser:
    """
    Enhanced Solid.js parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript parser when Solid.js
    framework is detected. It extracts Solid.js-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 30+ Solid.js ecosystem libraries.

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Solid.js ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'solid-js': re.compile(
            r"from\s+['\"]solid-js['\"]|require\(['\"]solid-js['\"]\)",
            re.MULTILINE
        ),
        'solid-js-store': re.compile(
            r"from\s+['\"]solid-js/store['\"]",
            re.MULTILINE
        ),
        'solid-js-web': re.compile(
            r"from\s+['\"]solid-js/web['\"]",
            re.MULTILINE
        ),
        'solid-js-html': re.compile(
            r"from\s+['\"]solid-js/html['\"]",
            re.MULTILINE
        ),

        # ── Router ────────────────────────────────────────────────
        'solidjs-router': re.compile(
            r"from\s+['\"]@solidjs/router['\"]",
            re.MULTILINE
        ),
        'solid-app-router': re.compile(
            r"from\s+['\"]solid-app-router['\"]",
            re.MULTILINE
        ),

        # ── SolidStart ────────────────────────────────────────────
        'solid-start': re.compile(
            r"from\s+['\"]solid-start['\"]|from\s+['\"]@solidjs/start['\"]",
            re.MULTILINE
        ),
        'vinxi': re.compile(
            r"from\s+['\"]vinxi['\"]",
            re.MULTILINE
        ),

        # ── Testing ───────────────────────────────────────────────
        'solidjs-testing': re.compile(
            r"from\s+['\"]@solidjs/testing-library['\"]|from\s+['\"]solid-testing-library['\"]",
            re.MULTILINE
        ),

        # ── Primitives ────────────────────────────────────────────
        'solid-primitives': re.compile(
            r"from\s+['\"]@solid-primitives/",
            re.MULTILINE
        ),

        # ── UI Libraries ─────────────────────────────────────────
        'kobalte': re.compile(
            r"from\s+['\"]@kobalte/core['\"]",
            re.MULTILINE
        ),
        'ark-ui-solid': re.compile(
            r"from\s+['\"]@ark-ui/solid['\"]",
            re.MULTILINE
        ),
        'solid-headless': re.compile(
            r"from\s+['\"]solid-headless['\"]",
            re.MULTILINE
        ),

        # ── Data ──────────────────────────────────────────────────
        'tanstack-solid-query': re.compile(
            r"from\s+['\"]@tanstack/solid-query['\"]",
            re.MULTILINE
        ),
        'tanstack-solid-table': re.compile(
            r"from\s+['\"]@tanstack/solid-table['\"]",
            re.MULTILINE
        ),

        # ── Styling ───────────────────────────────────────────────
        'solid-styled-components': re.compile(
            r"from\s+['\"]solid-styled-components['\"]",
            re.MULTILINE
        ),
        'solid-styled': re.compile(
            r"from\s+['\"]solid-styled['\"]",
            re.MULTILINE
        ),

        # ── Animation ─────────────────────────────────────────────
        'solid-transition-group': re.compile(
            r"from\s+['\"]solid-transition-group['\"]",
            re.MULTILINE
        ),
        'motionone-solid': re.compile(
            r"from\s+['\"]@motionone/solid['\"]",
            re.MULTILINE
        ),

        # ── Meta ──────────────────────────────────────────────────
        'solid-meta': re.compile(
            r"from\s+['\"]solid-meta['\"]|from\s+['\"]@solidjs/meta['\"]",
            re.MULTILINE
        ),

        # ── Build ─────────────────────────────────────────────────
        'vite-plugin-solid': re.compile(
            r"from\s+['\"]vite-plugin-solid['\"]|solid\s*\(\s*\)",
            re.MULTILINE
        ),

        # ── DevTools ──────────────────────────────────────────────
        'solid-devtools': re.compile(
            r"from\s+['\"]solid-devtools['\"]",
            re.MULTILINE
        ),

        # ── Markdown ──────────────────────────────────────────────
        'solid-markdown': re.compile(
            r"from\s+['\"]solid-markdown['\"]",
            re.MULTILINE
        ),

        # ── Icons ─────────────────────────────────────────────────
        'solid-icons': re.compile(
            r"from\s+['\"]solid-icons/",
            re.MULTILINE
        ),

        # ── Toast ─────────────────────────────────────────────────
        'solid-toast': re.compile(
            r"from\s+['\"]solid-toast['\"]",
            re.MULTILINE
        ),

        # ── i18n ──────────────────────────────────────────────────
        'solid-i18n': re.compile(
            r"from\s+['\"]@solid-primitives/i18n['\"]|from\s+['\"]solid-i18n['\"]",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'create_signal': re.compile(r'createSignal\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'create_memo': re.compile(r'createMemo\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'create_effect': re.compile(r'createEffect\s*\(', re.MULTILINE),
        'create_computed': re.compile(r'createComputed\s*\(', re.MULTILINE),
        'create_render_effect': re.compile(r'createRenderEffect\s*\(', re.MULTILINE),
        'create_reaction': re.compile(r'createReaction\s*\(', re.MULTILINE),
        'create_resource': re.compile(r'createResource\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'create_store': re.compile(r'createStore\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'create_mutable': re.compile(r'createMutable\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'create_context': re.compile(r'createContext\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'create_root': re.compile(r'createRoot\s*\(', re.MULTILINE),
        'create_deferred': re.compile(r'createDeferred\s*\(', re.MULTILINE),
        'on_mount': re.compile(r'onMount\s*\(', re.MULTILINE),
        'on_cleanup': re.compile(r'onCleanup\s*\(', re.MULTILINE),
        'on_error': re.compile(r'onError\s*\(', re.MULTILINE),
        'on_wrapper': re.compile(r'\bon\s*\(\s*(?:\[|[a-zA-Z])', re.MULTILINE),
        'batch': re.compile(r'batch\s*\(', re.MULTILINE),
        'untrack': re.compile(r'untrack\s*\(', re.MULTILINE),
        'observable': re.compile(r'observable\s*\(', re.MULTILINE),
        'from_external': re.compile(r'from\s*\(\s*(?:\w|\()', re.MULTILINE),
        'produce': re.compile(r'produce\s*\(', re.MULTILINE),
        'reconcile': re.compile(r'reconcile\s*\(', re.MULTILINE),
        'merge_props': re.compile(r'mergeProps\s*\(', re.MULTILINE),
        'split_props': re.compile(r'splitProps\s*\(', re.MULTILINE),
        'children_helper': re.compile(r'children\s*\(\s*\(\)\s*=>', re.MULTILINE),
        'lazy': re.compile(r'lazy\s*\(\s*\(\)', re.MULTILINE),
        'dynamic': re.compile(r'<Dynamic\s+', re.MULTILINE),
        'show': re.compile(r'<Show\b', re.MULTILINE),
        'for_loop': re.compile(r'<For\b', re.MULTILINE),
        'switch_match': re.compile(r'<Switch\b', re.MULTILINE),
        'index': re.compile(r'<Index\b', re.MULTILINE),
        'portal': re.compile(r'<Portal\b', re.MULTILINE),
        'suspense': re.compile(r'<Suspense\b', re.MULTILINE),
        'error_boundary': re.compile(r'<ErrorBoundary\b', re.MULTILINE),
        'transition': re.compile(r'(?:startTransition|useTransition)\s*\(', re.MULTILINE),
        'server_function': re.compile(r'server\$\s*\(', re.MULTILINE),
        'ssr': re.compile(r'(?:renderToString|renderToStream|isServer)\b', re.MULTILINE),
        'map_array': re.compile(r'(?:mapArray|indexArray)\s*\(', re.MULTILINE),
        'create_async': re.compile(r'createAsync\s*\(', re.MULTILINE),
        'cache_action': re.compile(r'(?:cache|action)\s*\(', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all Solid.js extractors."""
        self.component_extractor = SolidComponentExtractor()
        self.signal_extractor = SolidSignalExtractor()
        self.store_extractor = SolidStoreExtractor()
        self.resource_extractor = SolidResourceExtractor()
        self.router_extractor = SolidRouterExtractor()
        self.api_extractor = SolidApiExtractor()

    def is_solid_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Solid.js code.

        Returns True if the file imports from Solid.js ecosystem
        or uses Solid.js patterns (createSignal, etc.)
        """
        solid_indicators = [
            'solid-js', 'solid-js/', '@solidjs/',
            'solid-start', '@solid-primitives/',
            'createSignal(', 'createEffect(',
            'createMemo(', 'createResource(',
            'createStore(', 'createMutable(',
            "from 'solid-js", 'from "solid-js',
            "from '@solidjs/", 'from "@solidjs/',
            'solid-app-router',
            '<Show ', '<For ', '<Switch ',
            'onMount(', 'onCleanup(',
            '@kobalte/core', '@ark-ui/solid',
            'vite-plugin-solid', 'vinxi',
        ]
        return any(ind in content for ind in solid_indicators)

    def parse(self, content: str, file_path: str = "") -> SolidParseResult:
        """
        Parse a source file for Solid.js patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            SolidParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = SolidParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.solid_version = self._detect_version(content)

        # ── Component extraction ───────────────────────────────────
        try:
            comp_result = self.component_extractor.extract(content, file_path)
            result.components = comp_result.get('components', [])
            result.control_flows = comp_result.get('control_flows', [])
        except Exception:
            pass

        # ── Signal extraction ──────────────────────────────────────
        try:
            sig_result = self.signal_extractor.extract(content, file_path)
            result.signals = sig_result.get('signals', [])
            result.memos = sig_result.get('memos', [])
            result.effects = sig_result.get('effects', [])
            result.reactive_utils = sig_result.get('reactive_utils', [])
        except Exception:
            pass

        # ── Store extraction ───────────────────────────────────────
        try:
            store_result = self.store_extractor.extract(content, file_path)
            result.stores = store_result.get('stores', [])
            result.store_updates = store_result.get('store_updates', [])
        except Exception:
            pass

        # ── Resource extraction ────────────────────────────────────
        try:
            res_result = self.resource_extractor.extract(content, file_path)
            result.resources = res_result.get('resources', [])
            result.server_functions = res_result.get('server_functions', [])
            result.route_data = res_result.get('route_data', [])
        except Exception:
            pass

        # ── Router extraction ──────────────────────────────────────
        try:
            router_result = self.router_extractor.extract(content, file_path)
            result.routes = router_result.get('routes', [])
            result.router_hooks = router_result.get('router_hooks', [])
        except Exception:
            pass

        # ── API extraction ─────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.contexts = api_result.get('contexts', [])
            result.lifecycles = api_result.get('lifecycles', [])
            result.integrations = api_result.get('integrations', [])
            result.types = api_result.get('types', [])
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Solid.js ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Solid.js features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Solid.js version based on API usage patterns.

        Returns:
            - 'v2' if Solid.js v2+ / SolidStart v1.0+ patterns detected
            - 'v1.8' if v1.8 patterns detected
            - 'v1.4' if v1.4+ patterns detected (from(), external sources)
            - 'v1.1' if v1.1+ patterns detected (startTransition, createDeferred)
            - 'v1' if basic Solid patterns
            - '' if unknown
        """
        # v2 / SolidStart v1.0+ indicators
        v2_indicators = [
            'createAsync',          # SolidStart v1.0+ / Solid v2
            '@solidjs/start',       # SolidStart v1.0+
            'vinxi',                # SolidStart v1.0+ build tool
        ]
        if any(ind in content for ind in v2_indicators):
            return "v2"

        # v1.8 indicators
        v1_8_indicators = [
            'server$',              # Server functions (SolidStart pre-v1)
        ]
        if any(ind in content for ind in v1_8_indicators):
            return "v1.8"

        # v1.4+ indicators (from() for external reactive sources)
        v1_4_indicators = [
            "from(", "from (",      # from() utility (v1.4+)
        ]
        if any(ind in content for ind in v1_4_indicators):
            return "v1.4"

        # v1.1+ indicators
        v1_1_indicators = [
            'startTransition',      # Concurrent features (v1.1+)
            'useTransition',        # Concurrent features (v1.1+)
            'createDeferred',       # Deferred signals (v1.1+)
        ]
        if any(ind in content for ind in v1_1_indicators):
            return "v1.1"

        # Basic Solid present = v1
        if 'createSignal' in content or 'solid-js' in content:
            return "v1"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'v1': 1, 'v1.1': 2, 'v1.4': 3, 'v1.6': 4, 'v1.8': 5, 'v2': 6}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
