"""
Tests for Vue.js extractors and EnhancedVueParser.

Part of CodeTrellis v4.34 Vue.js Language Support.
Tests cover:
- Component extraction (SFC, Options API, Composition API, <script setup>)
- Composable extraction (refs, computed, watchers, lifecycle hooks, custom composables)
- Directive extraction (custom directives, transitions)
- Plugin extraction (plugins, global registrations)
- Routing extraction (routes, navigation guards, RouterView)
- Vue parser integration (framework detection, version detection)
"""

import pytest
from codetrellis.vue_parser_enhanced import (
    EnhancedVueParser,
    VueParseResult,
)
from codetrellis.extractors.vue import (
    VueComponentExtractor,
    VueComposableExtractor,
    VueDirectiveExtractor,
    VuePluginExtractor,
    VueRoutingExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedVueParser()


@pytest.fixture
def component_extractor():
    return VueComponentExtractor()


@pytest.fixture
def composable_extractor():
    return VueComposableExtractor()


@pytest.fixture
def directive_extractor():
    return VueDirectiveExtractor()


@pytest.fixture
def plugin_extractor():
    return VuePluginExtractor()


@pytest.fixture
def routing_extractor():
    return VueRoutingExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestVueComponentExtractor:
    """Tests for VueComponentExtractor."""

    def test_script_setup_component(self, component_extractor):
        code = '''
<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
    title: string
    count?: number
}>()

const emit = defineEmits<{
    (e: 'update', value: number): void
}>()

const localCount = ref(props.count ?? 0)
const doubled = computed(() => localCount.value * 2)
</script>

<template>
    <div>{{ title }}</div>
</template>

<style scoped>
div { color: red; }
</style>
'''
        result = component_extractor.extract(code, "MyComponent.vue")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.has_template
        assert comp.has_style
        assert comp.style_scoped

    def test_options_api_component(self, component_extractor):
        code = '''
export default {
    name: 'UserProfile',
    props: {
        userId: { type: String, required: true },
        showAvatar: { type: Boolean, default: true },
    },
    data() {
        return {
            user: null,
            loading: false,
        }
    },
    computed: {
        fullName() {
            return `${this.user?.firstName} ${this.user?.lastName}`
        },
    },
    methods: {
        async fetchUser() {
            this.loading = true
            this.user = await api.getUser(this.userId)
            this.loading = false
        },
    },
    watch: {
        userId: 'fetchUser',
    },
    mounted() {
        this.fetchUser()
    },
}
'''
        result = component_extractor.extract(code, "UserProfile.vue")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.name == 'UserProfile'
        assert len(comp.props) >= 2
        assert len(comp.data_keys) >= 2
        assert 'fullName' in comp.computed_keys
        assert 'fetchUser' in comp.methods

    def test_composition_api_component(self, component_extractor):
        code = '''
import { defineComponent, ref, computed, onMounted } from 'vue'

export default defineComponent({
    name: 'Counter',
    props: {
        initialCount: { type: Number, default: 0 },
    },
    setup(props) {
        const count = ref(props.initialCount)
        const doubled = computed(() => count.value * 2)

        function increment() {
            count.value++
        }

        onMounted(() => {
            console.log('Counter mounted')
        })

        return { count, doubled, increment }
    },
})
'''
        result = component_extractor.extract(code, "Counter.vue")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.name == 'Counter'

    def test_async_component(self, component_extractor):
        code = '''
import { defineAsyncComponent } from 'vue'

const AsyncModal = defineAsyncComponent(() =>
    import('./components/Modal.vue')
)

const AsyncChart = defineAsyncComponent({
    loader: () => import('./components/HeavyChart.vue'),
    loadingComponent: LoadingSpinner,
    delay: 200,
    timeout: 10000,
})
'''
        result = component_extractor.extract(code, "async-components.ts")
        # Should detect async components
        assert len(result) >= 1

    def test_functional_component_vue2(self, component_extractor):
        code = '''
export default {
    name: 'FunctionalItem',
    functional: true,
    props: {
        text: String,
    },
    render(h, { props }) {
        return h('div', props.text)
    },
}
'''
        result = component_extractor.extract(code, "FunctionalItem.vue")
        assert len(result) >= 1

    def test_define_emits_extraction(self, component_extractor):
        code = '''
<script setup>
const emit = defineEmits(['submit', 'cancel', 'validate'])
</script>
'''
        result = component_extractor.extract(code, "Form.vue")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert len(comp.emits) >= 3

    def test_define_slots(self, component_extractor):
        code = '''
<script setup lang="ts">
defineSlots<{
    default(props: { item: Item }): any
    header(): any
    footer(): any
}>()
</script>
'''
        result = component_extractor.extract(code, "SlotComponent.vue")
        assert len(result) >= 1

    def test_provide_inject(self, component_extractor):
        code = '''
export default {
    name: 'Provider',
    provide() {
        return {
            theme: this.theme,
            locale: this.locale,
        }
    },
    inject: ['config', 'logger'],
}
'''
        result = component_extractor.extract(code, "Provider.vue")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert len(comp.provides) >= 2
        assert len(comp.injects) >= 2

    def test_mixins(self, component_extractor):
        code = '''
import { validationMixin } from '@/mixins/validation'
import { paginationMixin } from '@/mixins/pagination'

export default {
    name: 'UserList',
    mixins: [validationMixin, paginationMixin],
    data() {
        return { users: [] }
    },
}
'''
        result = component_extractor.extract(code, "UserList.vue")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert len(comp.mixins) >= 2

    def test_define_model(self, component_extractor):
        code = '''
<script setup lang="ts">
const modelValue = defineModel<string>({ required: true })
const title = defineModel<string>('title')
</script>
'''
        result = component_extractor.extract(code, "ModelComp.vue")
        assert len(result) >= 1


# ═══════════════════════════════════════════════════════════════════
# Composable Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestVueComposableExtractor:
    """Tests for VueComposableExtractor."""

    def test_custom_composable(self, composable_extractor):
        code = '''
import { ref, computed, onMounted, onUnmounted } from 'vue'

export function useCounter(initial = 0) {
    const count = ref(initial)
    const doubled = computed(() => count.value * 2)

    function increment() { count.value++ }
    function decrement() { count.value-- }

    return { count, doubled, increment, decrement }
}
'''
        result = composable_extractor.extract(code, "useCounter.ts")
        assert len(result.get('composables', [])) >= 1
        comp = result['composables'][0]
        assert comp.name == 'useCounter'
        assert comp.is_exported

    def test_ref_extraction(self, composable_extractor):
        code = '''
import { ref, shallowRef, reactive } from 'vue'

const count = ref(0)
const name = ref<string>('')
const items = shallowRef<Item[]>([])
const state = reactive({ loading: false, error: null })
'''
        result = composable_extractor.extract(code, "component.vue")
        refs = result.get('refs', [])
        assert len(refs) >= 3

    def test_computed_extraction(self, composable_extractor):
        code = '''
import { computed } from 'vue'

const fullName = computed(() => `${first.value} ${last.value}`)
const total = computed<number>(() => items.value.reduce((s, i) => s + i.price, 0))
const writableComputed = computed({
    get: () => model.value,
    set: (val) => { model.value = val },
})
'''
        result = composable_extractor.extract(code, "component.vue")
        computeds = result.get('computeds', [])
        assert len(computeds) >= 3

    def test_watcher_extraction(self, composable_extractor):
        code = '''
import { watch, watchEffect, watchPostEffect, watchSyncEffect } from 'vue'

watch(source, (newVal, oldVal) => {
    console.log('changed')
})

watch(source, handler, { immediate: true, deep: true })

watchEffect(() => {
    console.log(count.value)
})

watchPostEffect(() => {
    document.title = title.value
})
'''
        result = composable_extractor.extract(code, "component.vue")
        watchers = result.get('watchers', [])
        assert len(watchers) >= 3

    def test_lifecycle_hook_extraction(self, composable_extractor):
        code = '''
import { onMounted, onUnmounted, onUpdated, onBeforeMount, onActivated } from 'vue'

onMounted(() => {
    console.log('mounted')
})

onUnmounted(() => {
    clearInterval(timer)
})

onUpdated(() => {
    console.log('updated')
})

onBeforeMount(() => {
    fetchData()
})

onActivated(() => {
    refreshData()
})
'''
        result = composable_extractor.extract(code, "component.vue")
        hooks = result.get('lifecycle_hooks', [])
        assert len(hooks) >= 5

    def test_composable_with_lifecycle(self, composable_extractor):
        code = '''
export function useEventListener(target, event, handler) {
    onMounted(() => target.addEventListener(event, handler))
    onUnmounted(() => target.removeEventListener(event, handler))
}
'''
        result = composable_extractor.extract(code, "useEventListener.ts")
        composables = result.get('composables', [])
        assert len(composables) >= 1
        comp = composables[0]
        assert comp.name == 'useEventListener'


# ═══════════════════════════════════════════════════════════════════
# Directive Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestVueDirectiveExtractor:
    """Tests for VueDirectiveExtractor."""

    def test_global_directive(self, directive_extractor):
        code = '''
app.directive('focus', {
    mounted(el) {
        el.focus()
    },
})
'''
        result = directive_extractor.extract(code, "main.ts")
        directives = result.get('directives', [])
        assert len(directives) >= 1
        d = directives[0]
        assert d.name == 'focus'
        assert d.is_global

    def test_exported_directive(self, directive_extractor):
        code = '''
export const vClickOutside = {
    mounted(el, binding) {
        el._handler = (event) => {
            if (!el.contains(event.target)) {
                binding.value(event)
            }
        }
        document.addEventListener('click', el._handler)
    },
    unmounted(el) {
        document.removeEventListener('click', el._handler)
    },
}
'''
        result = directive_extractor.extract(code, "directives.ts")
        directives = result.get('directives', [])
        assert len(directives) >= 1

    def test_vue2_directive(self, directive_extractor):
        code = '''
Vue.directive('tooltip', {
    bind(el, binding) {
        el.title = binding.value
    },
    update(el, binding) {
        el.title = binding.value
    },
})
'''
        result = directive_extractor.extract(code, "directives.js")
        directives = result.get('directives', [])
        assert len(directives) >= 1

    def test_transition_extraction(self, directive_extractor):
        code = '''
<template>
    <Transition name="fade" mode="out-in">
        <div v-if="show">Content</div>
    </Transition>

    <TransitionGroup name="list" tag="ul">
        <li v-for="item in items" :key="item.id">{{ item.text }}</li>
    </TransitionGroup>
</template>
'''
        result = directive_extractor.extract(code, "Animated.vue")
        transitions = result.get('transitions', [])
        assert len(transitions) >= 2


# ═══════════════════════════════════════════════════════════════════
# Plugin Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestVuePluginExtractor:
    """Tests for VuePluginExtractor."""

    def test_plugin_with_install(self, plugin_extractor):
        code = '''
export const MyPlugin = {
    install(app, options) {
        app.component('GlobalButton', Button)
        app.directive('tooltip', tooltipDirective)
        app.provide('config', options)
        app.config.globalProperties.$api = api
    },
}
'''
        result = plugin_extractor.extract(code, "my-plugin.ts")
        plugins = result.get('plugins', [])
        assert len(plugins) >= 1
        plugin = plugins[0]
        assert plugin.has_install

    def test_global_component_registration(self, plugin_extractor):
        code = '''
app.component('BaseButton', BaseButton)
app.component('BaseIcon', BaseIcon)
app.component('BaseInput', BaseInput)
'''
        result = plugin_extractor.extract(code, "main.ts")
        registrations = result.get('global_registrations', [])
        assert len(registrations) >= 3

    def test_app_use(self, plugin_extractor):
        code = '''
const app = createApp(App)
app.use(router)
app.use(pinia)
app.use(i18n)
app.use(VueFire, { firebaseApp })
app.mount('#app')
'''
        result = plugin_extractor.extract(code, "main.ts")
        app_uses = result.get('app_uses', [])
        assert len(app_uses) >= 4

    def test_global_properties(self, plugin_extractor):
        code = '''
app.config.globalProperties.$http = axios
app.config.globalProperties.$bus = emitter
'''
        result = plugin_extractor.extract(code, "main.ts")
        registrations = result.get('global_registrations', [])
        assert len(registrations) >= 2


# ═══════════════════════════════════════════════════════════════════
# Routing Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestVueRoutingExtractor:
    """Tests for VueRoutingExtractor."""

    def test_basic_routes(self, routing_extractor):
        code = '''
const routes = [
    {
        path: '/',
        name: 'home',
        component: Home,
    },
    {
        path: '/about',
        name: 'about',
        component: () => import('./views/About.vue'),
    },
    {
        path: '/users/:id',
        name: 'user-detail',
        component: () => import('./views/UserDetail.vue'),
        props: true,
    },
]
'''
        result = routing_extractor.extract(code, "router.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 3

    def test_nested_routes(self, routing_extractor):
        code = '''
const routes = [
    {
        path: '/dashboard',
        component: DashboardLayout,
        children: [
            { path: '', component: DashboardHome },
            { path: 'analytics', component: Analytics },
            { path: 'settings', component: Settings },
        ],
    },
]
'''
        result = routing_extractor.extract(code, "router.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 1

    def test_navigation_guards(self, routing_extractor):
        code = '''
router.beforeEach(async (to, from) => {
    const auth = useAuthStore()
    if (to.meta.requiresAuth && !auth.isAuthenticated) {
        return { name: 'login' }
    }
})

router.afterEach((to, from) => {
    document.title = to.meta.title || 'App'
})

router.beforeResolve(async (to) => {
    if (to.meta.requiresData) {
        await fetchData()
    }
})
'''
        result = routing_extractor.extract(code, "router.ts")
        guards = result.get('guards', [])
        assert len(guards) >= 3

    def test_lazy_loaded_routes(self, routing_extractor):
        code = '''
const routes = [
    {
        path: '/admin',
        component: () => import('./views/Admin.vue'),
    },
    {
        path: '/reports',
        component: () => import(/* webpackChunkName: "reports" */ './views/Reports.vue'),
    },
]
'''
        result = routing_extractor.extract(code, "router.ts")
        routes = result.get('routes', [])
        lazy_routes = [r for r in routes if r.is_lazy]
        assert len(lazy_routes) >= 2

    def test_route_meta(self, routing_extractor):
        code = '''
const routes = [
    {
        path: '/admin',
        meta: {
            requiresAuth: true,
            roles: ['admin'],
            title: 'Admin Panel',
        },
        component: Admin,
    },
]
'''
        result = routing_extractor.extract(code, "router.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 1

    def test_router_view_extraction(self, routing_extractor):
        code = '''
<template>
    <div>
        <RouterView />
        <RouterView name="sidebar" />
        <router-view name="footer" />
    </div>
</template>
'''
        result = routing_extractor.extract(code, "App.vue")
        views = result.get('router_views', [])
        assert len(views) >= 2


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedVueParser:
    """Tests for the main EnhancedVueParser."""

    def test_is_vue_file_sfc(self, parser):
        code = '''
<template>
    <div>Hello</div>
</template>

<script setup>
import { ref } from 'vue'
const msg = ref('hello')
</script>
'''
        assert parser.is_vue_file(code, "Hello.vue")

    def test_is_vue_file_js_with_vue_imports(self, parser):
        code = '''
import { createApp } from 'vue'
import App from './App.vue'

const app = createApp(App)
app.mount('#app')
'''
        assert parser.is_vue_file(code, "main.js")

    def test_is_not_vue_file(self, parser):
        code = '''
function add(a, b) {
    return a + b;
}
'''
        assert not parser.is_vue_file(code, "utils.js")

    def test_parse_sfc(self, parser):
        code = '''
<template>
    <div class="counter">
        <p>{{ count }}</p>
        <button @click="increment">+</button>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)

function increment() {
    count.value++
}
</script>

<style scoped>
.counter { padding: 1rem; }
</style>
'''
        result = parser.parse(code, "Counter.vue")
        assert isinstance(result, VueParseResult)
        assert len(result.components) >= 1
        assert len(result.refs) >= 1
        assert len(result.computeds) >= 1

    def test_framework_detection_pinia(self, parser):
        code = '''
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', () => {
    const user = ref(null)
    return { user }
})
'''
        result = parser.parse(code, "stores/user.ts")
        assert 'pinia' in result.detected_frameworks

    def test_framework_detection_vuetify(self, parser):
        code = '''
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
'''
        result = parser.parse(code, "plugins/vuetify.ts")
        assert 'vuetify' in result.detected_frameworks

    def test_framework_detection_nuxt(self, parser):
        code = '''
import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
    modules: ['@nuxt/ui'],
})
'''
        result = parser.parse(code, "nuxt.config.ts")
        assert any('nuxt' in fw for fw in result.detected_frameworks)

    def test_framework_detection_vue_router(self, parser):
        code = '''
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory(),
    routes: [],
})
'''
        result = parser.parse(code, "router/index.ts")
        assert 'vue-router' in result.detected_frameworks

    def test_framework_detection_element_plus(self, parser):
        code = '''
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
'''
        result = parser.parse(code, "main.ts")
        assert 'element-plus' in result.detected_frameworks

    def test_framework_detection_vueuse(self, parser):
        code = '''
import { useMouse, useWindowSize, useDark } from '@vueuse/core'
'''
        result = parser.parse(code, "composables/use-ui.ts")
        assert 'vueuse' in result.detected_frameworks

    def test_vue_version_detection_3_0(self, parser):
        code = '''
import { createApp, defineComponent, ref, reactive } from 'vue'
'''
        result = parser.parse(code, "main.ts")
        assert result.vue_version >= "3.0"

    def test_vue_version_detection_3_3(self, parser):
        code = '''
<script setup lang="ts">
const props = defineProps<{ name: string }>()
defineOptions({ name: 'MyComponent' })
</script>
'''
        result = parser.parse(code, "Comp.vue")
        assert result.vue_version >= "3.3"

    def test_vue_version_detection_3_4(self, parser):
        code = '''
<script setup>
const model = defineModel()
</script>
'''
        result = parser.parse(code, "Model.vue")
        assert result.vue_version >= "3.4"

    def test_vue_version_detection_3_5(self, parser):
        code = '''
<script setup>
import { useTemplateRef, useId } from 'vue'
const input = useTemplateRef('input')
const id = useId()
</script>
'''
        result = parser.parse(code, "Modern.vue")
        assert result.vue_version >= "3.5"

    def test_api_style_options(self, parser):
        code = '''
export default {
    data() { return { count: 0 } },
    methods: { increment() { this.count++ } },
}
'''
        result = parser.parse(code, "Counter.vue")
        assert result.api_style == "options"

    def test_api_style_composition(self, parser):
        code = '''
import { defineComponent, ref } from 'vue'

export default defineComponent({
    setup() {
        const count = ref(0)
        return { count }
    },
})
'''
        result = parser.parse(code, "Counter.vue")
        assert result.api_style in ("composition", "script-setup")

    def test_api_style_script_setup(self, parser):
        code = '''
<script setup>
import { ref } from 'vue'
const count = ref(0)
</script>
'''
        result = parser.parse(code, "Counter.vue")
        assert result.api_style == "script-setup"

    def test_full_sfc_parse(self, parser):
        code = '''
<template>
    <div class="todo-app">
        <input v-model="newTodo" @keyup.enter="addTodo" />
        <TransitionGroup name="list" tag="ul">
            <li v-for="todo in filteredTodos" :key="todo.id">
                <input type="checkbox" v-model="todo.done" />
                <span :class="{ done: todo.done }">{{ todo.text }}</span>
                <button @click="removeTodo(todo.id)">×</button>
            </li>
        </TransitionGroup>
        <p>{{ remaining }} remaining</p>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Todo {
    id: number
    text: string
    done: boolean
}

const props = defineProps<{ filter?: string }>()
const emit = defineEmits<{ (e: 'change', count: number): void }>()

const todos = ref<Todo[]>([])
const newTodo = ref('')

const filteredTodos = computed(() => {
    if (props.filter === 'active') return todos.value.filter(t => !t.done)
    if (props.filter === 'done') return todos.value.filter(t => t.done)
    return todos.value
})

const remaining = computed(() => todos.value.filter(t => !t.done).length)

function addTodo() {
    if (!newTodo.value.trim()) return
    todos.value.push({ id: Date.now(), text: newTodo.value, done: false })
    newTodo.value = ''
    emit('change', remaining.value)
}

function removeTodo(id: number) {
    todos.value = todos.value.filter(t => t.id !== id)
    emit('change', remaining.value)
}
</script>

<style scoped lang="scss">
.todo-app {
    max-width: 400px;
    .done { text-decoration: line-through; }
}
</style>
'''
        result = parser.parse(code, "TodoApp.vue")

        # Should extract component
        assert len(result.components) >= 1
        comp = result.components[0]
        assert comp.has_template
        assert comp.has_style
        assert comp.style_scoped
        assert comp.style_lang == "scss"

        # Should extract refs and computeds
        assert len(result.refs) >= 2
        assert len(result.computeds) >= 2

        # Should detect API style
        assert result.api_style == "script-setup"

    def test_multiple_framework_detection(self, parser):
        code = '''
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { createHead } from '@vueuse/head'
import { createI18n } from 'vue-i18n'
'''
        result = parser.parse(code, "main.ts")
        assert len(result.detected_frameworks) >= 3

    def test_parse_returns_result(self, parser):
        code = '''
<template><div>Hello</div></template>
<script setup>
import { ref } from 'vue'
const msg = ref('hello')
</script>
'''
        result = parser.parse(code, "Hello.vue")
        assert isinstance(result, VueParseResult)
        assert result.file_path == "Hello.vue"

    def test_empty_content(self, parser):
        result = parser.parse("", "empty.vue")
        assert isinstance(result, VueParseResult)
        # Parser may create a stub component for .vue files; no crash
        assert result.file_path == "empty.vue"

    def test_quasar_detection(self, parser):
        code = '''
import { QBtn, QInput, QPage } from 'quasar'
'''
        result = parser.parse(code, "comp.vue")
        assert 'quasar' in result.detected_frameworks

    def test_primevue_detection(self, parser):
        code = '''
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
'''
        result = parser.parse(code, "comp.vue")
        assert 'primevue' in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# BPL Practice YAML Tests
# ═══════════════════════════════════════════════════════════════════

class TestVueBPLPractices:
    """Tests for Vue.js BPL practices YAML file."""

    def test_practices_load(self):
        """Ensure vue_core.yaml loads without errors."""
        from codetrellis.bpl.repository import BestPracticesRepository
        repo = BestPracticesRepository()
        repo.load_all()
        all_practices = repo.get_all()
        vue_practices = [p for p in all_practices if p.id.startswith("VUE")]
        assert len(vue_practices) == 50, f"Expected 50 Vue practices, got {len(vue_practices)}"

    def test_practice_ids_sequential(self):
        """Ensure all VUE001-VUE050 IDs exist."""
        from codetrellis.bpl.repository import BestPracticesRepository
        repo = BestPracticesRepository()
        repo.load_all()
        all_practices = repo.get_all()
        vue_ids = {p.id for p in all_practices if p.id.startswith("VUE")}
        for i in range(1, 51):
            expected_id = f"VUE{i:03d}"
            assert expected_id in vue_ids, f"Missing practice {expected_id}"

    def test_practice_categories_valid(self):
        """Ensure all Vue practice categories are valid PracticeCategory values."""
        from codetrellis.bpl.repository import BestPracticesRepository
        from codetrellis.bpl.models import PracticeCategory
        repo = BestPracticesRepository()
        repo.load_all()
        all_practices = repo.get_all()
        vue_practices = [p for p in all_practices if p.id.startswith("VUE")]
        valid_categories = {c.value for c in PracticeCategory}
        for practice in vue_practices:
            assert practice.category.value in valid_categories, (
                f"Practice {practice.id} has invalid category: {practice.category}"
            )


# ═══════════════════════════════════════════════════════════════════
# Scanner Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestVueScannerIntegration:
    """Tests for Vue.js scanner integration."""

    def test_scanner_has_vue_parser(self):
        """Ensure scanner initializes Vue parser."""
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        assert hasattr(scanner, 'vue_parser')
        assert isinstance(scanner.vue_parser, EnhancedVueParser)

    def test_scanner_vue_file_type(self):
        """Ensure .vue maps to 'vue' file type."""
        from codetrellis.scanner import ProjectScanner
        assert ProjectScanner.FILE_TYPES.get('.vue') == 'vue'

    def test_matrix_has_vue_fields(self):
        """Ensure ProjectMatrix has Vue fields."""
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        assert hasattr(matrix, 'vue_components')
        assert hasattr(matrix, 'vue_composables')
        assert hasattr(matrix, 'vue_refs')
        assert hasattr(matrix, 'vue_computeds')
        assert hasattr(matrix, 'vue_watchers')
        assert hasattr(matrix, 'vue_lifecycle_hooks')
        assert hasattr(matrix, 'vue_directives')
        assert hasattr(matrix, 'vue_transitions')
        assert hasattr(matrix, 'vue_plugins')
        assert hasattr(matrix, 'vue_global_registrations')
        assert hasattr(matrix, 'vue_app_uses')
        assert hasattr(matrix, 'vue_routes')
        assert hasattr(matrix, 'vue_guards')
        assert hasattr(matrix, 'vue_router_views')
        assert hasattr(matrix, 'vue_detected_frameworks')
        assert hasattr(matrix, 'vue_version')
        assert hasattr(matrix, 'vue_api_style')
        assert hasattr(matrix, 'vue_async_components')
        assert hasattr(matrix, 'vue_custom_elements')
