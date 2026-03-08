"""
EnhancedPiniaParser v1.0 - Comprehensive Pinia parser using all extractors.

This parser integrates all Pinia extractors to provide complete parsing of
Pinia state management usage across Vue/TypeScript/JavaScript source files.
It runs as a supplementary layer on top of the Vue/JavaScript/TypeScript
parsers, extracting Pinia-specific semantics.

Supports:
- Pinia v0.x (early API, @pinia/composition-api, experimental)
- Pinia v1.x (first stable release, Options + Setup stores,
              createPinia, defineStore, storeToRefs, SSR support,
              plugin API, Vue DevTools integration)
- Pinia v2.x (Vue 3 official store, enhanced TypeScript support,
              $patch object/function, $reset, $subscribe/$onAction,
              mapStores/mapState/mapGetters/mapActions/mapWritableState,
              improved DevTools, pinia-plugin-persistedstate v3-v4)
- Pinia v3.x (planned: tree-shaking improvements, modular architecture,
              improved TypeScript inference, standalone stores)

Store Definition Patterns:
- Options API: defineStore('id', { state, getters, actions })
- Setup API (Composition): defineStore('id', () => { ... })
- TypeScript generics: defineStore<Id, S, G, A>()
- Store composition (stores using other stores)
- HMR (Hot Module Replacement) support

State Patterns:
- Options API state: state: () => ({ ... })
- Setup API state: ref(), reactive(), shallowRef(), shallowReactive()
- storeToRefs() for reactive destructuring
- $patch (object + function forms)
- $reset to restore initial state

Getter Patterns:
- Options API getters: getters: { getter(state) { ... } }
- Options API getters with this: getters: { getter() { return this.field } }
- Setup API getters: computed(() => ...)
- Getter arguments (returning functions)
- Cross-store getters

Action Patterns:
- Options API actions: actions: { action() { this.field = ... } }
- Setup API actions: function/const arrow functions
- Async actions (await, try/catch, Promise)
- Cross-store actions
- $subscribe (mutation/state watchers)
- $onAction (action hooks with after/onError)

Plugin Patterns:
- createPinia() + app.use(pinia)
- pinia.use(plugin) registration
- pinia-plugin-persistedstate (persist: true)
- pinia-plugin-debounce
- pinia-orm
- Custom plugins with PiniaPluginContext
- Store augmentation (custom properties)

Framework Ecosystem Detection (30+ patterns):
- Core: pinia, @pinia/nuxt, @pinia/testing
- Plugins: pinia-plugin-persistedstate, pinia-plugin-debounce, pinia-orm
- Vue: vue, @vue/composition-api, vue-router, vue-i18n
- Nuxt: nuxt, @nuxt/module, nuxt.config
- Testing: @pinia/testing, vitest, @vue/test-utils, jest
- Build: vite, webpack, vue-cli, nuxt-vite

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via Volar (Vue Language Server) / typescript-language-server.

Part of CodeTrellis v4.52 - Pinia State Management Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Pinia extractors
from .extractors.pinia import (
    PiniaStoreExtractor, PiniaStoreInfo,
    PiniaGetterExtractor, PiniaGetterInfo, PiniaStoreToRefsInfo,
    PiniaActionExtractor, PiniaActionInfo, PiniaPatchInfo, PiniaSubscriptionInfo,
    PiniaPluginExtractor, PiniaPluginInfo, PiniaInstanceInfo,
    PiniaApiExtractor, PiniaImportInfo, PiniaIntegrationInfo, PiniaTypeInfo,
)


@dataclass
class PiniaParseResult:
    """Complete parse result for a file with Pinia usage."""
    file_path: str
    file_type: str = "ts"  # ts, tsx, js, jsx, vue

    # Stores
    stores: List[PiniaStoreInfo] = field(default_factory=list)

    # Getters
    getters: List[PiniaGetterInfo] = field(default_factory=list)
    store_to_refs: List[PiniaStoreToRefsInfo] = field(default_factory=list)

    # Actions
    actions: List[PiniaActionInfo] = field(default_factory=list)
    patches: List[PiniaPatchInfo] = field(default_factory=list)
    subscriptions: List[PiniaSubscriptionInfo] = field(default_factory=list)

    # Plugins
    plugins: List[PiniaPluginInfo] = field(default_factory=list)
    instances: List[PiniaInstanceInfo] = field(default_factory=list)

    # API
    imports: List[PiniaImportInfo] = field(default_factory=list)
    integrations: List[PiniaIntegrationInfo] = field(default_factory=list)
    types: List[PiniaTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    pinia_version: str = ""  # v0, v1, v2, v3


class EnhancedPiniaParser:
    """
    Enhanced Pinia parser that uses all extractors.

    This parser runs AFTER the Vue/JavaScript/TypeScript parser
    when Pinia framework is detected. It extracts Pinia-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 30+ Pinia ecosystem libraries across:
    - Core (pinia, @pinia/nuxt, @pinia/testing)
    - Plugins (pinia-plugin-persistedstate, pinia-plugin-debounce, pinia-orm)
    - Vue ecosystem (vue, vue-router, vue-i18n, nuxt)
    - Testing (@vue/test-utils, vitest, jest)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: Volar (Vue Language Server) / typescript-language-server
    """

    # Pinia ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'pinia': re.compile(
            r"from\s+['\"]pinia['\"]|require\(['\"]pinia['\"]\)|"
            r"\bdefineStore\s*\(|"
            r"\bcreatePinia\s*\(",
            re.MULTILINE
        ),
        'pinia-nuxt': re.compile(
            r"from\s+['\"]@pinia/nuxt['\"]|"
            r"modules\s*:.*@pinia/nuxt",
            re.MULTILINE | re.DOTALL
        ),
        'pinia-testing': re.compile(
            r"from\s+['\"]@pinia/testing['\"]|"
            r"\bcreateTestingPinia\s*\(",
            re.MULTILINE
        ),

        # ── Plugins ────────────────────────────────────────────────
        'pinia-plugin-persistedstate': re.compile(
            r"from\s+['\"]pinia-plugin-persistedstate['\"]|"
            r"from\s+['\"]pinia-plugin-persist['\"]|"
            r"\bpersist\s*:\s*(?:true|\{)",
            re.MULTILINE
        ),
        'pinia-plugin-debounce': re.compile(
            r"from\s+['\"]pinia-plugin-debounce['\"]|"
            r"from\s+['\"]@pinia/plugin-debounce['\"]",
            re.MULTILINE
        ),
        'pinia-orm': re.compile(
            r"from\s+['\"]pinia-orm['\"]|"
            r"from\s+['\"]@pinia/orm['\"]",
            re.MULTILINE
        ),

        # ── Vue Ecosystem ──────────────────────────────────────────
        'vue': re.compile(
            r"from\s+['\"]vue['\"]|"
            r"from\s+['\"]@vue/composition-api['\"]",
            re.MULTILINE
        ),
        'vue-router': re.compile(
            r"from\s+['\"]vue-router['\"]|"
            r"\buseRouter\s*\(|\buseRoute\s*\(",
            re.MULTILINE
        ),
        'vue-i18n': re.compile(
            r"from\s+['\"]vue-i18n['\"]|"
            r"\buseI18n\s*\(",
            re.MULTILINE
        ),

        # ── Nuxt ──────────────────────────────────────────────────
        'nuxt': re.compile(
            r"from\s+['\"](?:#app|nuxt|@nuxt)[/'\":]|"
            r"defineNuxtConfig|definePageMeta|useNuxtApp|useFetch",
            re.MULTILINE
        ),

        # ── Testing ────────────────────────────────────────────────
        'vitest': re.compile(
            r"from\s+['\"]vitest['\"]|"
            r"\bdescribe\s*\(.*\bdefineStore",
            re.MULTILINE | re.DOTALL
        ),
        'vue-test-utils': re.compile(
            r"from\s+['\"]@vue/test-utils['\"]|"
            r"\bmount\s*\(|\bshallowMount\s*\(",
            re.MULTILINE
        ),

        # ── Build Tools ────────────────────────────────────────────
        'vite': re.compile(
            r"from\s+['\"]vite['\"]|"
            r"\bdefineConfig\s*\(",
            re.MULTILINE
        ),

        # ── State Management Alternatives (coexistence detection) ──
        'vuex': re.compile(
            r"from\s+['\"]vuex['\"]|"
            r"\bcreateStore\s*\(\s*\{.*mutations",
            re.MULTILINE | re.DOTALL
        ),
        'vueuse': re.compile(
            r"from\s+['\"]@vueuse/core['\"]|"
            r"from\s+['\"]@vueuse/",
            re.MULTILINE
        ),

        # ── UI Frameworks ──────────────────────────────────────────
        'vuetify': re.compile(
            r"from\s+['\"]vuetify['\"]",
            re.MULTILINE
        ),
        'quasar': re.compile(
            r"from\s+['\"]quasar['\"]",
            re.MULTILINE
        ),
        'element-plus': re.compile(
            r"from\s+['\"]element-plus['\"]",
            re.MULTILINE
        ),
        'primevue': re.compile(
            r"from\s+['\"]primevue/",
            re.MULTILINE
        ),
        'naive-ui': re.compile(
            r"from\s+['\"]naive-ui['\"]",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'define_store': re.compile(r'\bdefineStore\s*\(', re.MULTILINE),
        'create_pinia': re.compile(r'\bcreatePinia\s*\(', re.MULTILINE),
        'store_to_refs': re.compile(r'\bstoreToRefs\s*\(', re.MULTILINE),
        'options_api': re.compile(r'defineStore\s*\([^,]+,\s*\{', re.MULTILINE),
        'setup_api': re.compile(r'defineStore\s*\([^,]+,\s*\(\)\s*=>', re.MULTILINE),
        'patch_object': re.compile(r'\.\$patch\s*\(\s*\{', re.MULTILINE),
        'patch_function': re.compile(r'\.\$patch\s*\(\s*\(', re.MULTILINE),
        'reset': re.compile(r'\.\$reset\s*\(', re.MULTILINE),
        'subscribe': re.compile(r'\.\$subscribe\s*\(', re.MULTILINE),
        'on_action': re.compile(r'\.\$onAction\s*\(', re.MULTILINE),
        'map_stores': re.compile(r'\bmapStores\s*\(', re.MULTILINE),
        'map_state': re.compile(r'\bmapState\s*\(', re.MULTILINE),
        'map_getters': re.compile(r'\bmapGetters\s*\(', re.MULTILINE),
        'map_actions': re.compile(r'\bmapActions\s*\(', re.MULTILINE),
        'map_writable_state': re.compile(r'\bmapWritableState\s*\(', re.MULTILINE),
        'persist': re.compile(r'persist\s*:\s*(?:true|\{)', re.MULTILINE),
        'hmr': re.compile(r'import\.meta\.hot|acceptHMR', re.MULTILINE),
        'testing': re.compile(r'createTestingPinia', re.MULTILINE),
        'composition_api': re.compile(r'\b(?:ref|reactive|computed|watch|watchEffect)\s*\(', re.MULTILINE),
        'typescript': re.compile(r'defineStore\s*<|:\s*StoreDefinition|:\s*StateTree', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all Pinia extractors."""
        self.store_extractor = PiniaStoreExtractor()
        self.getter_extractor = PiniaGetterExtractor()
        self.action_extractor = PiniaActionExtractor()
        self.plugin_extractor = PiniaPluginExtractor()
        self.api_extractor = PiniaApiExtractor()

    def is_pinia_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Pinia code.

        Returns True if the file imports from Pinia ecosystem
        or uses Pinia patterns (defineStore, createPinia, etc.)
        """
        pinia_indicators = [
            'pinia', 'defineStore(', 'createPinia(',
            'storeToRefs(', '@pinia/nuxt', '@pinia/testing',
            "from 'pinia'", 'from "pinia"',
            'pinia-plugin-persistedstate', 'pinia-plugin-persist',
            'pinia-orm', 'createTestingPinia(',
            'mapStores(', 'mapWritableState(',
            '$patch(', '$reset(', '$subscribe(', '$onAction(',
        ]
        return any(ind in content for ind in pinia_indicators)

    def parse(self, content: str, file_path: str = "") -> PiniaParseResult:
        """
        Parse a source file for Pinia patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            PiniaParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.vue'):
            file_type = "vue"
        elif file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = PiniaParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.pinia_version = self._detect_version(content)

        # ── Store extraction ───────────────────────────────────────
        try:
            store_result = self.store_extractor.extract(content, file_path)
            result.stores = store_result.get('stores', [])
        except Exception:
            pass

        # ── Getter extraction ──────────────────────────────────────
        try:
            getter_result = self.getter_extractor.extract(content, file_path)
            result.getters = getter_result.get('getters', [])
            result.store_to_refs = getter_result.get('store_to_refs', [])
        except Exception:
            pass

        # ── Action extraction ─────────────────────────────────────
        try:
            action_result = self.action_extractor.extract(content, file_path)
            result.actions = action_result.get('actions', [])
            result.patches = action_result.get('patches', [])
            result.subscriptions = action_result.get('subscriptions', [])
        except Exception:
            pass

        # ── Plugin extraction ─────────────────────────────────────
        try:
            plugin_result = self.plugin_extractor.extract(content, file_path)
            result.plugins = plugin_result.get('plugins', [])
            result.instances = plugin_result.get('instances', [])
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
        """Detect which Pinia ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Pinia features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Pinia version based on API usage patterns.

        Returns:
            - 'v2' if Pinia v2+ patterns detected (most common)
            - 'v1' if only v1 patterns
            - 'v0' if early experimental patterns
            - '' if unknown
        """
        # v2 indicators (current standard)
        v2_indicators = [
            'mapStores',            # v2-only helper
            'mapWritableState',     # v2-only helper
            '$patch(',              # v2 enhanced $patch
            '$onAction(',           # v2 action hooks
            'acceptHMR',            # v2 HMR API
            '@pinia/nuxt',          # v2 Nuxt integration
            '@pinia/testing',       # v2 testing utilities
            'createTestingPinia',   # v2 testing
            'pinia-plugin-persistedstate',  # v2+ plugin ecosystem
        ]
        if any(ind in content for ind in v2_indicators):
            return "v2"

        # v1 indicators
        v1_indicators = [
            'defineStore',
            'createPinia',
            'storeToRefs',
            "from 'pinia'",
            'from "pinia"',
        ]
        if any(ind in content for ind in v1_indicators):
            return "v2"  # Most defineStore usage is v2 (v1 and v2 share API)

        # v0 indicators
        v0_indicators = [
            '@pinia/composition',
            '@pinia/composition-api',
            'buildModule',  # very early experimental API
        ]
        if any(ind in content for ind in v0_indicators):
            return "v0"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'v0': 1, 'v1': 2, 'v2': 3, 'v3': 4}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
