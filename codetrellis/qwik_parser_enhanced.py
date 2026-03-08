"""
EnhancedQwikParser v1.0 - Comprehensive Qwik parser using all extractors.

This parser integrates all Qwik extractors to provide complete parsing of
Qwik framework usage across TypeScript/JavaScript/JSX/TSX source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript parsers,
extracting Qwik-specific semantics.

Supports:
- Qwik v0.x (early API: component$, useStore, useWatch$, useClientEffect$)
- Qwik v1.x (stable API: useSignal, useTask$, useVisibleTask$, useComputed$)
  - Qwik City v1.x (routeLoader$, routeAction$, server$, Form)
  - File-based routing with layout.tsx, index.tsx, [param], [...catchall]
  - Middleware: onRequest, onGet, onPost, etc.
- Qwik v2.x (@qwik.dev/core, @qwik.dev/router, improved signal types)
  - New package scoped imports
  - Enhanced TypeScript types

Core Concepts:
- component$() — lazy-loaded component wrapper via Optimizer
- useSignal(initialValue) -> Signal<T> with .value access
- useStore(initialObject) -> deep reactive proxy store
- useComputed$(() => derived) -> ReadonlySignal<T>
- useTask$(() => { track, cleanup }) — server + client lifecycle
- useVisibleTask$(() => { ... }) — browser-only after visible
- useResource$<T>(() => { track, cleanup }) — async data loading
- <Resource> component for rendering resource states
- <Slot> content projection (named/default)
- $ suffix for lazy-loadable boundaries (QRL)
- noSerialize() for non-serializable values

Qwik City / Router:
- routeLoader$() — server-side data loaders
- routeAction$() — server-side form actions
- server$() — RPC-style server functions
- globalAction$() — global server actions
- Form component with action binding
- zod() validation integration
- useNavigate(), useLocation(), useContent()
- Middleware: onRequest, onGet, onPost, onPut, onDelete
- File-based routing: layout.tsx, index.tsx, [param], [...catchall]

Context:
- createContextId<T>('identifier')
- useContextProvider(CTX, value)
- useContext(CTX)

Events:
- JSX handlers: onClick$, onInput$, onChange$, onKeyDown$, etc.
- useOn('event', handler$)
- useOnWindow('event', handler$)
- useOnDocument('event', handler$)

Styles:
- useStyles$(styles)
- useStylesScoped$(styles)

SSR:
- SSRStream, SSRStreamBlock
- renderToString, renderToStream
- isServer, isBrowser

Ecosystem Detection (20+ patterns):
- Core: @builder.io/qwik, @builder.io/qwik-city, @builder.io/qwik/build
- V2: @qwik.dev/core, @qwik.dev/router
- UI: @qwik-ui/headless, @qwik-ui/styled, qwik-ui
- Forms: @modular-forms/qwik
- i18n: qwik-speak
- Auth: @auth/qwik, @builder.io/qwik-auth
- Media: @unpic/qwik, qwik-image
- Validation: zod, valibot (with Qwik integration)
- Testing: @builder.io/qwik/testing
- Build: vite, @builder.io/qwik/optimizer

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.63 - Qwik Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Qwik extractors
from .extractors.qwik import (
    QwikComponentExtractor, QwikComponentInfo, QwikSlotInfo,
    QwikSignalExtractor, QwikSignalInfo, QwikStoreInfo, QwikComputedInfo,
    QwikTaskExtractor, QwikTaskInfo, QwikResourceInfo,
    QwikRouteExtractor, QwikRouteLoaderInfo, QwikRouteActionInfo, QwikMiddlewareInfo,
    QwikStoreExtractor, QwikContextInfo, QwikNoSerializeInfo,
    QwikApiExtractor, QwikImportInfo, QwikEventHandlerInfo, QwikStyleInfo, QwikIntegrationInfo, QwikTypeInfo,
)


@dataclass
class QwikParseResult:
    """Complete parse result for a file with Qwik usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, ts, js

    # Components
    components: List[QwikComponentInfo] = field(default_factory=list)
    slots: List[QwikSlotInfo] = field(default_factory=list)

    # Signals & State
    signals: List[QwikSignalInfo] = field(default_factory=list)
    stores: List[QwikStoreInfo] = field(default_factory=list)
    computeds: List[QwikComputedInfo] = field(default_factory=list)

    # Tasks & Lifecycle
    tasks: List[QwikTaskInfo] = field(default_factory=list)
    resources: List[QwikResourceInfo] = field(default_factory=list)

    # Routing
    route_loaders: List[QwikRouteLoaderInfo] = field(default_factory=list)
    route_actions: List[QwikRouteActionInfo] = field(default_factory=list)
    server_functions: List[dict] = field(default_factory=list)
    middleware: List[QwikMiddlewareInfo] = field(default_factory=list)
    nav_hooks: List[dict] = field(default_factory=list)

    # Context
    contexts: List[QwikContextInfo] = field(default_factory=list)
    no_serializes: List[QwikNoSerializeInfo] = field(default_factory=list)

    # API
    imports: List[QwikImportInfo] = field(default_factory=list)
    event_handlers: List[QwikEventHandlerInfo] = field(default_factory=list)
    styles: List[QwikStyleInfo] = field(default_factory=list)
    integrations: List[QwikIntegrationInfo] = field(default_factory=list)
    types: List[QwikTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    qwik_version: str = ""  # v0, v1, v2


class EnhancedQwikParser:
    """
    Enhanced Qwik parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript parser when Qwik
    framework is detected. It extracts Qwik-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 20+ Qwik ecosystem libraries.

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Qwik ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'qwik': re.compile(
            r"from\s+['\"]@builder\.io/qwik['\"]|"
            r"from\s+['\"]@qwik\.dev/core['\"]|"
            r"require\(['\"]@builder\.io/qwik['\"]\)",
            re.MULTILINE
        ),
        'qwik-city': re.compile(
            r"from\s+['\"]@builder\.io/qwik-city['\"]|"
            r"from\s+['\"]@qwik\.dev/router['\"]",
            re.MULTILINE
        ),
        'qwik-build': re.compile(
            r"from\s+['\"]@builder\.io/qwik/build['\"]",
            re.MULTILINE
        ),
        'qwik-server': re.compile(
            r"from\s+['\"]@builder\.io/qwik/server['\"]",
            re.MULTILINE
        ),
        'qwik-optimizer': re.compile(
            r"from\s+['\"]@builder\.io/qwik/optimizer['\"]",
            re.MULTILINE
        ),

        # ── Testing ───────────────────────────────────────────────
        'qwik-testing': re.compile(
            r"from\s+['\"]@builder\.io/qwik/testing['\"]",
            re.MULTILINE
        ),

        # ── UI Libraries ─────────────────────────────────────────
        'qwik-ui-headless': re.compile(
            r"from\s+['\"]@qwik-ui/headless['\"]",
            re.MULTILINE
        ),
        'qwik-ui-styled': re.compile(
            r"from\s+['\"]@qwik-ui/styled['\"]",
            re.MULTILINE
        ),
        'qwik-ui': re.compile(
            r"from\s+['\"]qwik-ui['\"]",
            re.MULTILINE
        ),

        # ── Forms ─────────────────────────────────────────────────
        'modular-forms': re.compile(
            r"from\s+['\"]@modular-forms/qwik['\"]",
            re.MULTILINE
        ),

        # ── i18n ──────────────────────────────────────────────────
        'qwik-speak': re.compile(
            r"from\s+['\"]qwik-speak['\"]",
            re.MULTILINE
        ),

        # ── Auth ──────────────────────────────────────────────────
        'qwik-auth': re.compile(
            r"from\s+['\"]@auth/qwik['\"]|from\s+['\"]@builder\.io/qwik-auth['\"]",
            re.MULTILINE
        ),

        # ── Media ─────────────────────────────────────────────────
        'unpic-qwik': re.compile(
            r"from\s+['\"]@unpic/qwik['\"]",
            re.MULTILINE
        ),

        # ── Validation ────────────────────────────────────────────
        'zod': re.compile(
            r"from\s+['\"]zod['\"]",
            re.MULTILINE
        ),
        'valibot': re.compile(
            r"from\s+['\"]valibot['\"]",
            re.MULTILINE
        ),

        # ── Icons ─────────────────────────────────────────────────
        'qwik-icon': re.compile(
            r"from\s+['\"]qwik-icon",
            re.MULTILINE
        ),

        # ── Build tools ──────────────────────────────────────────
        'vite': re.compile(
            r"from\s+['\"]vite['\"]|qwikVite\s*\(",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'component_dollar': re.compile(r'component\$\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_signal': re.compile(r'useSignal\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_store': re.compile(r'useStore\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_computed': re.compile(r'useComputed\$\s*\(', re.MULTILINE),
        'use_task': re.compile(r'useTask\$\s*\(', re.MULTILINE),
        'use_visible_task': re.compile(r'useVisibleTask\$\s*\(', re.MULTILINE),
        'use_resource': re.compile(r'useResource\$\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'route_loader': re.compile(r'routeLoader\$\s*\(', re.MULTILINE),
        'route_action': re.compile(r'routeAction\$\s*\(', re.MULTILINE),
        'server_dollar': re.compile(r'server\$\s*\(', re.MULTILINE),
        'global_action': re.compile(r'globalAction\$\s*\(', re.MULTILINE),
        'slot': re.compile(r'<Slot\b', re.MULTILINE),
        'resource_component': re.compile(r'<Resource\b', re.MULTILINE),
        'form_component': re.compile(r'<Form\b', re.MULTILINE),
        'create_context': re.compile(r'createContextId\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_context': re.compile(r'useContext\s*\(', re.MULTILINE),
        'use_context_provider': re.compile(r'useContextProvider\s*\(', re.MULTILINE),
        'no_serialize': re.compile(r'noSerialize\s*\(', re.MULTILINE),
        'use_navigate': re.compile(r'useNavigate\s*\(', re.MULTILINE),
        'use_location': re.compile(r'useLocation\s*\(', re.MULTILINE),
        'use_styles': re.compile(r'useStyles\$\s*\(', re.MULTILINE),
        'use_styles_scoped': re.compile(r'useStylesScoped\$\s*\(', re.MULTILINE),
        'use_on': re.compile(r'useOn\s*\(', re.MULTILINE),
        'use_on_window': re.compile(r'useOnWindow\s*\(', re.MULTILINE),
        'use_on_document': re.compile(r'useOnDocument\s*\(', re.MULTILINE),
        'use_id': re.compile(r'useId\s*\(', re.MULTILINE),
        'use_error_boundary': re.compile(r'useErrorBoundary\s*\(', re.MULTILINE),
        'qrl': re.compile(r'\$\s*\(', re.MULTILINE),
        'ssr_stream': re.compile(r'<SSRStream\b', re.MULTILINE),
        'ssr_stream_block': re.compile(r'<SSRStreamBlock\b', re.MULTILINE),
        'is_server': re.compile(r'\bisServer\b', re.MULTILINE),
        'is_browser': re.compile(r'\bisBrowser\b', re.MULTILINE),
        'render_to_string': re.compile(r'renderToString\s*\(', re.MULTILINE),
        'render_to_stream': re.compile(r'renderToStream\s*\(', re.MULTILINE),
        'on_request': re.compile(r'\bonRequest\b', re.MULTILINE),
        'on_get': re.compile(r'\bonGet\b', re.MULTILINE),
        'on_post': re.compile(r'\bonPost\b', re.MULTILINE),
        'zod_validation': re.compile(r'zod\$?\s*\(', re.MULTILINE),
        'deep_false': re.compile(r'deep\s*:\s*false', re.MULTILINE),
        'use_watch_legacy': re.compile(r'useWatch\$\s*\(', re.MULTILINE),
        'use_client_effect_legacy': re.compile(r'useClientEffect\$\s*\(', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all Qwik extractors."""
        self.component_extractor = QwikComponentExtractor()
        self.signal_extractor = QwikSignalExtractor()
        self.task_extractor = QwikTaskExtractor()
        self.route_extractor = QwikRouteExtractor()
        self.store_extractor = QwikStoreExtractor()
        self.api_extractor = QwikApiExtractor()

    def is_qwik_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Qwik code.

        Returns True if the file imports from Qwik ecosystem
        or uses Qwik patterns (component$, useSignal, etc.)
        """
        qwik_indicators = [
            '@builder.io/qwik', '@builder.io/qwik-city',
            '@qwik.dev/core', '@qwik.dev/router',
            'component$(', 'useSignal(',
            'useStore(', 'useTask$(',
            'useVisibleTask$(', 'useResource$(',
            'routeLoader$(', 'routeAction$(',
            'server$(', 'globalAction$(',
            "from '@builder.io/qwik", 'from "@builder.io/qwik',
            "from '@qwik.dev/", 'from "@qwik.dev/',
            '@qwik-ui/', 'useComputed$(',
            'createContextId(', 'useContextProvider(',
            '@modular-forms/qwik', 'qwik-speak',
            'useStylesScoped$(', 'useStyles$(',
        ]
        return any(ind in content for ind in qwik_indicators)

    def parse(self, content: str, file_path: str = "") -> QwikParseResult:
        """
        Parse a source file for Qwik patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            QwikParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = QwikParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.qwik_version = self._detect_version(content)

        # ── Component extraction ───────────────────────────────────
        try:
            comp_result = self.component_extractor.extract(content, file_path)
            result.components = comp_result.get('components', [])
            result.slots = comp_result.get('slots', [])
        except Exception:
            pass

        # ── Signal extraction ──────────────────────────────────────
        try:
            sig_result = self.signal_extractor.extract(content, file_path)
            result.signals = sig_result.get('signals', [])
            result.stores = sig_result.get('stores', [])
            result.computeds = sig_result.get('computeds', [])
        except Exception:
            pass

        # ── Task extraction ────────────────────────────────────────
        try:
            task_result = self.task_extractor.extract(content, file_path)
            result.tasks = task_result.get('tasks', [])
            result.resources = task_result.get('resources', [])
        except Exception:
            pass

        # ── Route extraction ───────────────────────────────────────
        try:
            route_result = self.route_extractor.extract(content, file_path)
            result.route_loaders = route_result.get('loaders', [])
            result.route_actions = route_result.get('actions', [])
            result.server_functions = route_result.get('server_functions', [])
            result.middleware = route_result.get('middleware', [])
            result.nav_hooks = route_result.get('nav_hooks', [])
        except Exception:
            pass

        # ── Store/Context extraction ──────────────────────────────
        try:
            store_result = self.store_extractor.extract(content, file_path)
            result.contexts = store_result.get('contexts', [])
            result.no_serializes = store_result.get('no_serializes', [])
        except Exception:
            pass

        # ── API extraction ─────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.event_handlers = api_result.get('event_handlers', [])
            result.styles = api_result.get('styles', [])
            result.integrations = api_result.get('integrations', [])
            result.types = api_result.get('types', [])
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Qwik ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Qwik features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Qwik version based on API usage and import patterns.

        Returns:
            - 'v2' if @qwik.dev/* imports detected (Qwik v2)
            - 'v1' if @builder.io/qwik imports with modern API (useSignal, useTask$)
            - 'v0' if legacy API (useWatch$, useClientEffect$)
            - '' if unknown
        """
        # v2 indicators: @qwik.dev/* package scope
        v2_indicators = [
            '@qwik.dev/core',
            '@qwik.dev/router',
        ]
        if any(ind in content for ind in v2_indicators):
            return "v2"

        # v1 indicators: stable @builder.io/qwik API
        v1_indicators = [
            '@builder.io/qwik',
            '@builder.io/qwik-city',
            'useSignal(',
            'useTask$(',
            'useVisibleTask$(',
            'routeLoader$(',
            'routeAction$(',
        ]
        if any(ind in content for ind in v1_indicators):
            return "v1"

        # v0 indicators: legacy API names
        v0_indicators = [
            'useWatch$(',
            'useClientEffect$(',
        ]
        if any(ind in content for ind in v0_indicators):
            return "v0"

        # Basic Qwik present
        if 'component$(' in content:
            return "v1"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'v0': 1, 'v1': 2, 'v2': 3}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
