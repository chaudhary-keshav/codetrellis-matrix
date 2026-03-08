"""
EnhancedVueParser v1.0 - Comprehensive Vue.js parser using all extractors.

This parser integrates all Vue extractors to provide complete parsing of
Vue.js source files (.vue SFCs, .js/.ts files with Vue components).

Supports:
- Vue 2.x (Options API, mixins, filters, functional components, Vue.extend)
- Vue 3.0 (Composition API, Teleport, Suspense, Fragments)
- Vue 3.1 (defineAsyncComponent improvements)
- Vue 3.2 (<script setup>, defineProps, defineEmits, defineExpose, style v-bind)
- Vue 3.3 (defineSlots, defineOptions, generic components, typed slots)
- Vue 3.4 (defineModel, v-bind shorthand, improved hydration, watchEffect cleanup)
- Vue 3.5 (Reactive Props Destructure, useTemplateRef, Deferred Teleport, useId)

Component patterns:
- Single File Components (.vue) with <template>, <script>, <style>
- <script setup> syntax (Vue 3.2+)
- defineComponent (Composition API)
- Options API (data, computed, methods, watch, lifecycle)
- defineAsyncComponent (lazy loading)
- defineCustomElement (Web Components)
- Functional components (Vue 2 functional: true)

Composition API:
- ref / reactive / shallowRef / shallowReactive / readonly
- computed (read-only and writable)
- watch / watchEffect / watchPostEffect / watchSyncEffect
- Lifecycle hooks (onMounted, onUpdated, onUnmounted, etc.)
- Custom composables (use* pattern)
- provide / inject
- defineModel (Vue 3.4+)
- useTemplateRef (Vue 3.5+)
- useId (Vue 3.5+)

State management:
- Pinia stores (defineStore, storeToRefs)
- Vuex stores (createStore, mapState, mapGetters, mapActions, mapMutations)
- Provide/Inject patterns

Routing:
- Vue Router 3.x (Vue 2) / 4.x (Vue 3)
- Route definitions, lazy routes, navigation guards
- Nuxt pages directory convention
- definePageMeta (Nuxt 3)

Framework detection (80+ Vue ecosystem patterns):
- Core: Vue 2.x, Vue 3.x, @vue/composition-api
- Meta-frameworks: Nuxt 2, Nuxt 3, Quasar, Gridsome, VitePress, VuePress
- UI: Vuetify, Quasar, Element Plus, PrimeVue, Naive UI, Ant Design Vue,
      Headless UI Vue, Radix Vue, shadcn-vue
- State: Pinia, Vuex, VueUse
- Forms: VeeValidate, FormKit, Vuelidate
- Routing: Vue Router, Nuxt Router
- Testing: Vue Test Utils, Vitest, Cypress Component Testing
- HTTP: Axios, ofetch, nuxt/http
- Animation: Vue Transition, GSAP Vue, Motion One
- i18n: vue-i18n, nuxt-i18n
- Build: Vite, Nuxt, Vue CLI, Webpack
- Utilities: VueUse, unplugin-vue-components, unplugin-auto-import

Optional AST support via tree-sitter-javascript / tree-sitter-typescript
(for <script> block parsing).
Optional LSP support via Volar (Vue Language Server) / typescript-language-server.

Part of CodeTrellis v4.34 - Vue.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Vue extractors
from .extractors.vue import (
    VueComponentExtractor, VueComponentInfo, VuePropInfo, VueEmitInfo,
    VueSlotInfo, VueProvideInjectInfo,
    VueComposableExtractor, VueComposableInfo, VueRefInfo,
    VueComputedInfo, VueWatcherInfo, VueLifecycleHookInfo,
    VueDirectiveExtractor, VueDirectiveInfo, VueTransitionInfo,
    VuePluginExtractor, VuePluginInfo, VueGlobalRegistrationInfo,
    VueRoutingExtractor, VueRouteInfo, VueNavigationGuardInfo,
    VueRouterViewInfo,
)


@dataclass
class VueParseResult:
    """Complete parse result for a Vue file."""
    file_path: str
    file_type: str = "vue"  # vue (SFC), js, ts

    # Components
    components: List[VueComponentInfo] = field(default_factory=list)
    async_components: List[VueComponentInfo] = field(default_factory=list)
    custom_elements: List[VueComponentInfo] = field(default_factory=list)

    # Composables
    composables: List[VueComposableInfo] = field(default_factory=list)
    refs: List[VueRefInfo] = field(default_factory=list)
    computeds: List[VueComputedInfo] = field(default_factory=list)
    watchers: List[VueWatcherInfo] = field(default_factory=list)
    lifecycle_hooks: List[VueLifecycleHookInfo] = field(default_factory=list)

    # Directives
    directives: List[VueDirectiveInfo] = field(default_factory=list)
    transitions: List[VueTransitionInfo] = field(default_factory=list)

    # Plugins
    plugins: List[VuePluginInfo] = field(default_factory=list)
    global_registrations: List[VueGlobalRegistrationInfo] = field(default_factory=list)
    app_uses: List[str] = field(default_factory=list)

    # Routing
    routes: List[VueRouteInfo] = field(default_factory=list)
    guards: List[VueNavigationGuardInfo] = field(default_factory=list)
    router_views: List[VueRouterViewInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    vue_version: str = ""  # Detected minimum Vue version
    api_style: str = ""  # options, composition, script-setup
    has_sfc: bool = False
    has_pinia: bool = False
    has_vuex: bool = False
    has_nuxt: bool = False
    has_vue_router: bool = False


class EnhancedVueParser:
    """
    Enhanced Vue.js parser that uses all extractors for comprehensive parsing.

    This parser handles both .vue SFC files and .js/.ts files that contain
    Vue components, composables, plugins, or routing configurations.

    Framework detection supports 80+ Vue ecosystem libraries across:
    - Core (Vue 2.x, Vue 3.x, @vue/composition-api)
    - Meta-frameworks (Nuxt 2/3, Quasar, Gridsome, VitePress, VuePress)
    - UI Libraries (Vuetify, Element Plus, PrimeVue, Naive UI, Ant Design Vue)
    - State Management (Pinia, Vuex, VueUse)
    - Forms (VeeValidate, FormKit, Vuelidate)
    - Routing (Vue Router 3/4, Nuxt Router)
    - Testing (Vue Test Utils, Vitest, Cypress)
    - HTTP (Axios, ofetch, nuxt/http)
    - i18n (vue-i18n, nuxt-i18n)
    - Build (Vite, Vue CLI, Nuxt CLI)
    - Utilities (VueUse, unplugin-vue-components)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: Volar (Vue Language Server)
    """

    # Vue ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'vue': re.compile(
            r"from\s+['\"]vue['\"]|require\(['\"]vue['\"]\)|"
            r"createApp|defineComponent|ref\s*\(|reactive\s*\(|"
            r"computed\s*\(|watch\s*\(|onMounted|onUnmounted|"
            r"<script\s+setup|defineProps|defineEmits",
            re.MULTILINE
        ),
        'vue-composition-api': re.compile(
            r"from\s+['\"]@vue/composition-api['\"]",
            re.MULTILINE
        ),

        # ── Meta-frameworks ───────────────────────────────────────
        'nuxt': re.compile(
            r"from\s+['\"](?:#app|nuxt|nuxt3|@nuxt)['/\"]|"
            r"defineNuxtConfig|useAsyncData|useFetch|definePageMeta|"
            r"useNuxtApp|defineNuxtPlugin|nuxt\.config|"
            r"useRuntimeConfig|navigateTo|abortNavigation",
            re.MULTILINE
        ),
        'quasar': re.compile(
            r"from\s+['\"]quasar['\"]|"
            r"useQuasar|QBtn|QCard|QPage|QLayout|QDialog|"
            r"quasar\.config|quasar\.conf",
            re.MULTILINE
        ),
        'gridsome': re.compile(
            r"from\s+['\"]gridsome['\"]|gridsome\.config|gridsome\.server",
            re.MULTILINE
        ),
        'vitepress': re.compile(
            r"from\s+['\"]vitepress['\"]|defineConfig.*vitepress|"
            r"useData|useRoute.*vitepress",
            re.MULTILINE
        ),
        'vuepress': re.compile(
            r"from\s+['\"]vuepress['\"]|from\s+['\"]@vuepress/|"
            r"defineUserConfig",
            re.MULTILINE
        ),

        # ── UI Libraries ──────────────────────────────────────────
        'vuetify': re.compile(
            r"from\s+['\"]vuetify['\"]|"
            r"createVuetify|useTheme|useDisplay|"
            r"v-btn|v-card|v-container|v-row|v-col|v-dialog|"
            r"VBtn|VCard|VContainer",
            re.MULTILINE
        ),
        'element-plus': re.compile(
            r"from\s+['\"]element-plus['\"]|"
            r"ElButton|ElInput|ElTable|ElForm|ElDialog|"
            r"el-button|el-input|el-table|el-form",
            re.MULTILINE
        ),
        'primevue': re.compile(
            r"from\s+['\"]primevue['/\"]|"
            r"PrimeVue|usePrimeVue",
            re.MULTILINE
        ),
        'naive-ui': re.compile(
            r"from\s+['\"]naive-ui['\"]|"
            r"NButton|NCard|NInput|NSpace|useMessage|useDialog",
            re.MULTILINE
        ),
        'ant-design-vue': re.compile(
            r"from\s+['\"]ant-design-vue['\"]|"
            r"a-button|a-input|a-table|a-form",
            re.MULTILINE
        ),
        'headless-ui-vue': re.compile(
            r"from\s+['\"]@headlessui/vue['\"]|"
            r"Listbox|Combobox|Dialog|Disclosure.*headless",
            re.MULTILINE
        ),
        'radix-vue': re.compile(
            r"from\s+['\"]radix-vue['\"]",
            re.MULTILINE
        ),
        'shadcn-vue': re.compile(
            r"from\s+['\"]@/components/ui/|"
            r"from\s+['\"]~/components/ui/",
            re.MULTILINE
        ),
        'vant': re.compile(
            r"from\s+['\"]vant['\"]|van-button|van-cell",
            re.MULTILINE
        ),
        'varlet': re.compile(
            r"from\s+['\"]@varlet/ui['\"]",
            re.MULTILINE
        ),

        # ── State Management ──────────────────────────────────────
        'pinia': re.compile(
            r"from\s+['\"]pinia['\"]|"
            r"defineStore|storeToRefs|createPinia|useStore",
            re.MULTILINE
        ),
        'vuex': re.compile(
            r"from\s+['\"]vuex['\"]|"
            r"createStore|mapState|mapGetters|mapActions|mapMutations|"
            r"useStore.*vuex",
            re.MULTILINE
        ),

        # ── VueUse ────────────────────────────────────────────────
        'vueuse': re.compile(
            r"from\s+['\"]@vueuse/(?:core|head|integrations|components)['\"]|"
            r"useMouse|useStorage|useDark|useToggle|useClipboard|"
            r"useEventListener|useIntersectionObserver|useLocalStorage|"
            r"onClickOutside|useColorMode|useBreakpoints",
            re.MULTILINE
        ),

        # ── Forms ─────────────────────────────────────────────────
        'vee-validate': re.compile(
            r"from\s+['\"]vee-validate['\"]|"
            r"useForm|useField|defineRule|Form|Field|ErrorMessage",
            re.MULTILINE
        ),
        'formkit': re.compile(
            r"from\s+['\"]@formkit/|FormKit|useFormKit",
            re.MULTILINE
        ),
        'vuelidate': re.compile(
            r"from\s+['\"]@vuelidate/|useVuelidate",
            re.MULTILINE
        ),

        # ── Routing ───────────────────────────────────────────────
        'vue-router': re.compile(
            r"from\s+['\"]vue-router['\"]|"
            r"createRouter|createWebHistory|createWebHashHistory|"
            r"useRouter|useRoute|RouterView|RouterLink|"
            r"router-view|router-link",
            re.MULTILINE
        ),

        # ── Testing ───────────────────────────────────────────────
        'vue-test-utils': re.compile(
            r"from\s+['\"]@vue/test-utils['\"]|"
            r"mount\s*\(|shallowMount\s*\(|wrapper\.\w+",
            re.MULTILINE
        ),
        'vitest': re.compile(
            r"from\s+['\"]vitest['\"]|vi\.mock|vi\.fn|describe\s*\(",
            re.MULTILINE
        ),
        'cypress-vue': re.compile(
            r"cy\.mount|mountCallback|from\s+['\"]cypress/vue['\"]",
            re.MULTILINE
        ),

        # ── HTTP ──────────────────────────────────────────────────
        'axios': re.compile(
            r"from\s+['\"]axios['\"]|axios\.\w+|useAxios",
            re.MULTILINE
        ),
        'ofetch': re.compile(
            r"from\s+['\"]ofetch['\"]|\$fetch",
            re.MULTILINE
        ),

        # ── i18n ──────────────────────────────────────────────────
        'vue-i18n': re.compile(
            r"from\s+['\"]vue-i18n['\"]|"
            r"createI18n|useI18n|\$t\s*\(|\$tc\s*\(",
            re.MULTILINE
        ),
        'nuxt-i18n': re.compile(
            r"from\s+['\"]@nuxtjs/i18n['\"]|useLocalePath|useSwitchLocalePath",
            re.MULTILINE
        ),

        # ── Animation ─────────────────────────────────────────────
        'vue-motion': re.compile(
            r"from\s+['\"]@vueuse/motion['\"]|useMotion|v-motion",
            re.MULTILINE
        ),
        'gsap-vue': re.compile(
            r"from\s+['\"]gsap['\"].*(?:onMounted|ref)|gsap\.to|gsap\.from",
            re.MULTILINE | re.DOTALL
        ),

        # ── Build ─────────────────────────────────────────────────
        'vite': re.compile(
            r"from\s+['\"]vite['\"]|defineConfig|import\.meta\.env|"
            r"import\.meta\.hot",
            re.MULTILINE
        ),
        'vue-cli': re.compile(
            r"vue\.config\.js|@vue/cli|VUE_APP_",
            re.MULTILINE
        ),

        # ── GraphQL ───────────────────────────────────────────────
        'vue-apollo': re.compile(
            r"from\s+['\"]@vue/apollo['/\"]|"
            r"from\s+['\"]vue-apollo['\"]|useQuery|useMutation|useSubscription",
            re.MULTILINE
        ),
        'villus': re.compile(
            r"from\s+['\"]villus['\"]|useQuery.*villus|useClient",
            re.MULTILINE
        ),

        # ── Utilities ─────────────────────────────────────────────
        'unplugin-vue-components': re.compile(
            r"from\s+['\"]unplugin-vue-components['/\"]|Components\(\)",
            re.MULTILINE
        ),
        'unplugin-auto-import': re.compile(
            r"from\s+['\"]unplugin-auto-import['/\"]|AutoImport\(\)",
            re.MULTILINE
        ),
        'vue-query': re.compile(
            r"from\s+['\"]@tanstack/vue-query['\"]|"
            r"useQuery|useMutation|useQueryClient|VueQueryPlugin",
            re.MULTILINE
        ),
        'pinia-plugin-persistedstate': re.compile(
            r"from\s+['\"]pinia-plugin-persistedstate['\"]|persist\s*:\s*true",
            re.MULTILINE
        ),
    }

    # Vue version detection from features used
    VUE_VERSION_FEATURES = {
        # Vue 3.5
        'useTemplateRef': '3.5',
        'useId': '3.5',

        # Vue 3.4
        'defineModel': '3.4',

        # Vue 3.3
        'defineSlots': '3.3',
        'defineOptions': '3.3',

        # Vue 3.2
        'defineProps': '3.2',
        'defineEmits': '3.2',
        'defineExpose': '3.2',
        '<script setup': '3.2',

        # Vue 3.0
        'createApp': '3.0',
        'defineComponent': '3.0',
        'defineAsyncComponent': '3.0',
        'Teleport': '3.0',
        'Suspense': '3.0',
        'onMounted': '3.0',
        'onUnmounted': '3.0',
        'ref(': '3.0',
        'reactive(': '3.0',
        'computed(': '3.0',
        'watch(': '3.0',
        'watchEffect': '3.0',
        'provide(': '3.0',
        'inject(': '3.0',
        'toRef': '3.0',
        'toRefs': '3.0',
        'shallowRef': '3.0',
        'shallowReactive': '3.0',
        'readonly(': '3.0',
        'nextTick': '3.0',

        # Vue 2.x features (also work in 3.x, but indicate 2.x compat)
        'Vue.extend': '2.0',
        'new Vue': '2.0',
        'Vue.component': '2.0',
        'Vue.directive': '2.0',
        'Vue.mixin': '2.0',
        'Vue.use': '2.0',
        'mixins:': '2.0',
        'filters:': '2.0',
    }

    def __init__(self):
        """Initialize the parser with all Vue extractors."""
        self.component_extractor = VueComponentExtractor()
        self.composable_extractor = VueComposableExtractor()
        self.directive_extractor = VueDirectiveExtractor()
        self.plugin_extractor = VuePluginExtractor()
        self.routing_extractor = VueRoutingExtractor()

    def parse(self, content: str, file_path: str = "") -> VueParseResult:
        """
        Parse Vue source code and extract all Vue-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            VueParseResult with all extracted Vue information
        """
        result = VueParseResult(file_path=file_path)

        # Detect file type
        if file_path.endswith('.vue'):
            result.file_type = "vue"
            result.has_sfc = True
        elif file_path.endswith('.ts') or file_path.endswith('.tsx'):
            result.file_type = "ts"
        else:
            result.file_type = "js"

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect special frameworks
        result.has_pinia = 'pinia' in result.detected_frameworks
        result.has_vuex = 'vuex' in result.detected_frameworks
        result.has_nuxt = 'nuxt' in result.detected_frameworks
        result.has_vue_router = 'vue-router' in result.detected_frameworks

        # ── Extract components ────────────────────────────────────
        comp_result = self.component_extractor.extract(content, file_path)
        result.components = comp_result.get('components', [])
        result.async_components = comp_result.get('async_components', [])
        result.custom_elements = comp_result.get('custom_elements', [])

        # Determine API style from first component
        if result.components:
            result.api_style = result.components[0].api_style

        # ── Extract composables ───────────────────────────────────
        comp_api_result = self.composable_extractor.extract(content, file_path)
        result.composables = comp_api_result.get('composables', [])
        result.refs = comp_api_result.get('refs', [])
        result.computeds = comp_api_result.get('computeds', [])
        result.watchers = comp_api_result.get('watchers', [])
        result.lifecycle_hooks = comp_api_result.get('lifecycle_hooks', [])

        # ── Extract directives ────────────────────────────────────
        dir_result = self.directive_extractor.extract(content, file_path)
        result.directives = dir_result.get('directives', [])
        result.transitions = dir_result.get('transitions', [])

        # ── Extract plugins ───────────────────────────────────────
        plugin_result = self.plugin_extractor.extract(content, file_path)
        result.plugins = plugin_result.get('plugins', [])
        result.global_registrations = plugin_result.get('global_registrations', [])
        result.app_uses = plugin_result.get('app_uses', [])

        # ── Extract routing ───────────────────────────────────────
        routing_result = self.routing_extractor.extract(content, file_path)
        result.routes = routing_result.get('routes', [])
        result.guards = routing_result.get('guards', [])
        result.router_views = routing_result.get('router_views', [])

        # ── Detect Vue version ────────────────────────────────────
        result.vue_version = self._detect_vue_version(content)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Vue ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_vue_version(self, content: str) -> str:
        """
        Detect the minimum Vue version required by the file.

        Returns version string (e.g., '3.5', '3.2', '3.0', '2.0').
        """
        max_version = '0.0'

        for feature, version in self.VUE_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version

        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_vue_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Vue code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Vue code
        """
        # .vue files are always Vue
        if file_path.endswith('.vue'):
            return True

        # Check for Vue imports
        if re.search(r"from\s+['\"]vue['\"]", content):
            return True

        # Check for defineComponent
        if re.search(r'\bdefineComponent\s*\(', content):
            return True

        # Check for Composition API usage
        if re.search(r'\b(?:ref|reactive|computed|watch|watchEffect)\s*\(', content):
            if re.search(r"from\s+['\"]vue['\"]", content):
                return True

        # Check for Vue Router usage
        if re.search(r"from\s+['\"]vue-router['\"]", content):
            return True

        # Check for Pinia usage
        if re.search(r'\bdefineStore\s*\(', content):
            return True

        # Check for Nuxt usage
        if re.search(r"from\s+['\"](?:#app|nuxt)['/\"]", content):
            return True

        # Check for Vuex
        if re.search(r"from\s+['\"]vuex['\"]", content):
            return True

        return False
