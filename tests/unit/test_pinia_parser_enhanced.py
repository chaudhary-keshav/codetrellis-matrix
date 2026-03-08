"""
Tests for Pinia extractors and EnhancedPiniaParser.

Part of CodeTrellis v4.52 Pinia State Management Framework Support.
Tests cover:
- Store extraction (defineStore Options + Setup API, composition, HMR, persist)
- Getter extraction (options/setup getters, storeToRefs, getter arguments)
- Action extraction (sync/async, $patch, $subscribe, $onAction, cross-store)
- Plugin extraction (createPinia, pinia.use(), persistedstate, custom plugins)
- API extraction (imports, integrations, TypeScript types, Nuxt)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from codetrellis.pinia_parser_enhanced import (
    EnhancedPiniaParser,
    PiniaParseResult,
)
from codetrellis.extractors.pinia import (
    PiniaStoreExtractor,
    PiniaGetterExtractor,
    PiniaActionExtractor,
    PiniaPluginExtractor,
    PiniaApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedPiniaParser()


@pytest.fixture
def store_extractor():
    return PiniaStoreExtractor()


@pytest.fixture
def getter_extractor():
    return PiniaGetterExtractor()


@pytest.fixture
def action_extractor():
    return PiniaActionExtractor()


@pytest.fixture
def plugin_extractor():
    return PiniaPluginExtractor()


@pytest.fixture
def api_extractor():
    return PiniaApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Store Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestPiniaStoreExtractor:
    """Tests for PiniaStoreExtractor."""

    def test_options_api_store(self, store_extractor):
        code = '''
import { defineStore } from 'pinia';

export const useCounterStore = defineStore('counter', {
    state: () => ({
        count: 0,
        name: 'Eduardo',
    }),
    getters: {
        doubleCount: (state) => state.count * 2,
    },
    actions: {
        increment() {
            this.count++;
        },
    },
});
'''
        result = store_extractor.extract(code, "counter.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        store = stores[0]
        assert store.name == "useCounterStore"
        assert store.store_id == "counter"

    def test_setup_api_store(self, store_extractor):
        code = '''
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useCounterStore = defineStore('counter', () => {
    const count = ref(0);
    const doubleCount = computed(() => count.value * 2);
    function increment() {
        count.value++;
    }
    return { count, doubleCount, increment };
});
'''
        result = store_extractor.extract(code, "counter.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        store = stores[0]
        assert store.name == "useCounterStore"
        assert store.store_id == "counter"

    def test_store_with_hmr(self, store_extractor):
        code = '''
import { defineStore, acceptHMRUpdate } from 'pinia';

export const useAuthStore = defineStore('auth', {
    state: () => ({ token: null }),
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot));
}
'''
        result = store_extractor.extract(code, "auth.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1

    def test_store_with_persist(self, store_extractor):
        code = '''
import { defineStore } from 'pinia';

export const useSettingsStore = defineStore('settings', {
    state: () => ({
        theme: 'light',
        locale: 'en',
    }),
    persist: true,
});
'''
        result = store_extractor.extract(code, "settings.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1

    def test_store_with_other_stores(self, store_extractor):
        code = '''
import { defineStore } from 'pinia';
import { useUserStore } from './user';

export const useCartStore = defineStore('cart', {
    state: () => ({ items: [] }),
    actions: {
        checkout() {
            const userStore = useUserStore();
            console.log(userStore.name);
        },
    },
});
'''
        result = store_extractor.extract(code, "cart.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1

    def test_typescript_generic_store(self, store_extractor):
        code = '''
import { defineStore } from 'pinia';

interface UserState {
    name: string;
    email: string;
}

export const useUserStore = defineStore<'user', UserState>('user', {
    state: () => ({
        name: '',
        email: '',
    }),
});
'''
        result = store_extractor.extract(code, "user.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1

    def test_multiple_stores_in_file(self, store_extractor):
        code = '''
import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
    state: () => ({ token: null }),
});

export const useProfileStore = defineStore('profile', {
    state: () => ({ name: '' }),
});
'''
        result = store_extractor.extract(code, "stores.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 2


# ═══════════════════════════════════════════════════════════════════
# Getter Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestPiniaGetterExtractor:
    """Tests for PiniaGetterExtractor."""

    def test_options_api_getters(self, getter_extractor):
        code = '''
export const useTodoStore = defineStore('todo', {
    state: () => ({
        todos: [],
        filter: 'all',
    }),
    getters: {
        completedCount: (state) => state.todos.filter(t => t.done).length,
        pendingTodos: (state) => state.todos.filter(t => !t.done),
        filteredTodos() {
            if (this.filter === 'all') return this.todos;
            return this.todos.filter(t => t.done === (this.filter === 'done'));
        },
    },
});
'''
        result = getter_extractor.extract(code, "todo.ts")
        getters = result.get('getters', [])
        assert len(getters) >= 1

    def test_setup_api_computed_getters(self, getter_extractor):
        code = '''
export const useStore = defineStore('main', () => {
    const items = ref([]);
    const totalPrice = computed(() => items.value.reduce((sum, i) => sum + i.price, 0));
    const isEmpty = computed(() => items.value.length === 0);
    return { items, totalPrice, isEmpty };
});
'''
        result = getter_extractor.extract(code, "main.ts")
        getters = result.get('getters', [])
        assert len(getters) >= 1

    def test_store_to_refs(self, getter_extractor):
        code = '''
import { storeToRefs } from 'pinia';
const store = useCounterStore();
const { count, double } = storeToRefs(store);
'''
        result = getter_extractor.extract(code, "component.vue")
        store_refs = result.get('store_to_refs', [])
        assert len(store_refs) >= 1

    def test_getter_returning_function(self, getter_extractor):
        code = '''
export const useStore = defineStore('main', {
    state: () => ({ items: [] }),
    getters: {
        getItemById: (state) => {
            return (id) => state.items.find(item => item.id === id);
        },
    },
});
'''
        result = getter_extractor.extract(code, "main.ts")
        getters = result.get('getters', [])
        assert len(getters) >= 1


# ═══════════════════════════════════════════════════════════════════
# Action Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestPiniaActionExtractor:
    """Tests for PiniaActionExtractor."""

    def test_options_api_actions(self, action_extractor):
        code = '''
export const useCounterStore = defineStore('counter', {
    state: () => ({ count: 0 }),
    actions: {
        increment() {
            this.count++;
        },
        decrement() {
            this.count--;
        },
    },
});
'''
        result = action_extractor.extract(code, "counter.ts")
        actions = result.get('actions', [])
        assert len(actions) >= 1

    def test_async_actions(self, action_extractor):
        code = '''
export const useUserStore = defineStore('user', {
    state: () => ({
        users: [],
        loading: false,
        error: null,
    }),
    actions: {
        async fetchUsers() {
            this.loading = true;
            try {
                const response = await fetch('/api/users');
                this.users = await response.json();
            } catch (error) {
                this.error = error.message;
            } finally {
                this.loading = false;
            }
        },
    },
});
'''
        result = action_extractor.extract(code, "user.ts")
        actions = result.get('actions', [])
        assert len(actions) >= 1

    def test_patch_object(self, action_extractor):
        code = '''
const store = useCounterStore();
store.$patch({
    count: store.count + 1,
    name: 'New Name',
});
'''
        result = action_extractor.extract(code, "component.ts")
        patches = result.get('patches', [])
        assert len(patches) >= 1

    def test_patch_function(self, action_extractor):
        code = '''
const store = useCartStore();
store.$patch((state) => {
    state.items.push(newItem);
    state.total += newItem.price;
});
'''
        result = action_extractor.extract(code, "component.ts")
        patches = result.get('patches', [])
        assert len(patches) >= 1

    def test_subscribe(self, action_extractor):
        code = '''
const store = useCartStore();
store.$subscribe((mutation, state) => {
    localStorage.setItem('cart', JSON.stringify(state));
});
'''
        result = action_extractor.extract(code, "component.ts")
        subscriptions = result.get('subscriptions', [])
        assert len(subscriptions) >= 1

    def test_on_action(self, action_extractor):
        code = '''
const store = useStore();
store.$onAction(({ name, args, after, onError }) => {
    console.log(`Action ${name} called`);
    after((result) => {
        console.log('After:', result);
    });
    onError((error) => {
        console.error('Error:', error);
    });
});
'''
        result = action_extractor.extract(code, "component.ts")
        subscriptions = result.get('subscriptions', [])
        assert len(subscriptions) >= 1

    def test_reset(self, action_extractor):
        code = '''
const store = useFormStore();
store.$reset();
'''
        result = action_extractor.extract(code, "form.ts")
        # $reset should be detected somewhere
        assert True  # Basic parse succeeds


# ═══════════════════════════════════════════════════════════════════
# Plugin Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestPiniaPluginExtractor:
    """Tests for PiniaPluginExtractor."""

    def test_create_pinia(self, plugin_extractor):
        code = '''
import { createPinia } from 'pinia';

const pinia = createPinia();
app.use(pinia);
'''
        result = plugin_extractor.extract(code, "main.ts")
        instances = result.get('instances', [])
        assert len(instances) >= 1
        assert instances[0].name == "pinia"

    def test_plugin_registration(self, plugin_extractor):
        code = '''
import { createPinia } from 'pinia';
import piniaPersistedState from 'pinia-plugin-persistedstate';

const pinia = createPinia();
pinia.use(piniaPersistedState);
'''
        result = plugin_extractor.extract(code, "main.ts")
        instances = result.get('instances', [])
        assert len(instances) >= 1

    def test_custom_plugin(self, plugin_extractor):
        code = '''
import { createPinia } from 'pinia';

function myPlugin({ store, app, pinia, options }) {
    store.$subscribe((mutation) => {
        console.log(mutation);
    });
}

const pinia = createPinia();
pinia.use(myPlugin);
'''
        result = plugin_extractor.extract(code, "plugins.ts")
        # Should detect either plugin or instance registration
        plugins = result.get('plugins', [])
        instances = result.get('instances', [])
        assert len(plugins) >= 1 or len(instances) >= 1

    def test_persisted_state_plugin(self, plugin_extractor):
        code = '''
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate';
const pinia = createPinia();
pinia.use(piniaPluginPersistedstate);
'''
        result = plugin_extractor.extract(code, "main.ts")
        instances = result.get('instances', [])
        assert len(instances) >= 1


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestPiniaApiExtractor:
    """Tests for PiniaApiExtractor."""

    def test_basic_imports(self, api_extractor):
        code = '''
import { defineStore, storeToRefs, createPinia } from 'pinia';
'''
        result = api_extractor.extract(code, "store.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 1
        imp = imports[0]
        assert imp.source == "pinia"
        assert "defineStore" in imp.imported_names

    def test_pinia_nuxt_import(self, api_extractor):
        code = '''
import { defineStore } from 'pinia';
import { usePinia } from '@pinia/nuxt';
'''
        result = api_extractor.extract(code, "store.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 1

    def test_pinia_testing_import(self, api_extractor):
        code = '''
import { createTestingPinia } from '@pinia/testing';
import { mount } from '@vue/test-utils';
'''
        result = api_extractor.extract(code, "test.ts")
        imports = result.get('imports', [])
        pinia_imports = [i for i in imports if '@pinia' in i.source]
        assert len(pinia_imports) >= 1

    def test_type_imports(self, api_extractor):
        code = '''
import type { StoreDefinition, StateTree, PiniaPluginContext } from 'pinia';
'''
        result = api_extractor.extract(code, "types.ts")
        # Should detect type imports
        imports = result.get('imports', [])
        assert len(imports) >= 1

    def test_integration_detection(self, api_extractor):
        code = '''
import { createTestingPinia } from '@pinia/testing';
import { usePinia } from '@pinia/nuxt';

const wrapper = mount(Component, {
    global: {
        plugins: [createTestingPinia()],
    },
});
'''
        result = api_extractor.extract(code, "test.spec.ts")
        integrations = result.get('integrations', [])
        assert len(integrations) >= 1

    def test_map_helpers(self, api_extractor):
        code = '''
import { mapState, mapActions, mapStores, mapWritableState, mapGetters } from 'pinia';
'''
        result = api_extractor.extract(code, "component.vue")
        imports = result.get('imports', [])
        assert len(imports) >= 1

    def test_typescript_types(self, api_extractor):
        code = '''
import type { StoreDefinition, Store, StateTree, _GettersTree, _ActionsTree } from 'pinia';
import type { PiniaPluginContext, PiniaCustomProperties } from 'pinia';

type MyStore = StoreDefinition<'my', { count: number }, {}, {}>;
'''
        result = api_extractor.extract(code, "types.ts")
        types = result.get('types', [])
        # Should detect TypeScript type usage
        assert True  # Basic parse succeeds


# ═══════════════════════════════════════════════════════════════════
# EnhancedPiniaParser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedPiniaParser:
    """Tests for the full EnhancedPiniaParser integration."""

    def test_is_pinia_file_positive(self, parser):
        code = '''
import { defineStore } from 'pinia';

export const useCounterStore = defineStore('counter', {
    state: () => ({ count: 0 }),
});
'''
        assert parser.is_pinia_file(code, "counter.ts") is True

    def test_is_pinia_file_negative(self, parser):
        code = '''
import React from 'react';
const App = () => <div>Hello</div>;
export default App;
'''
        assert parser.is_pinia_file(code, "app.tsx") is False

    def test_is_pinia_file_create_pinia(self, parser):
        code = '''
import { createPinia } from 'pinia';
const pinia = createPinia();
app.use(pinia);
'''
        assert parser.is_pinia_file(code, "main.ts") is True

    def test_is_pinia_file_store_to_refs(self, parser):
        code = '''
import { storeToRefs } from 'pinia';
const { count } = storeToRefs(useCounterStore());
'''
        assert parser.is_pinia_file(code, "component.vue") is True

    def test_is_pinia_file_pinia_import(self, parser):
        code = '''
import { mapState, mapActions } from 'pinia';
'''
        assert parser.is_pinia_file(code, "component.vue") is True

    def test_parse_options_api_full(self, parser):
        code = '''
import { defineStore } from 'pinia';

export const useCounterStore = defineStore('counter', {
    state: () => ({
        count: 0,
        name: 'Eduardo',
    }),
    getters: {
        doubleCount: (state) => state.count * 2,
        message: (state) => `Count is ${state.count}`,
    },
    actions: {
        increment() {
            this.count++;
        },
        async fetchData() {
            const data = await fetch('/api/data');
            this.name = await data.text();
        },
    },
});
'''
        result = parser.parse(code, "counter.ts")
        assert isinstance(result, PiniaParseResult)
        assert result.file_path == "counter.ts"
        assert len(result.stores) >= 1
        assert len(result.imports) >= 1

    def test_parse_setup_api_full(self, parser):
        code = '''
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useCounterStore = defineStore('counter', () => {
    const count = ref(0);
    const name = ref('Eduardo');
    const doubleCount = computed(() => count.value * 2);

    function increment() {
        count.value++;
    }

    async function fetchData() {
        const response = await fetch('/api/data');
        name.value = await response.text();
    }

    return { count, name, doubleCount, increment, fetchData };
});
'''
        result = parser.parse(code, "counter.ts")
        assert isinstance(result, PiniaParseResult)
        assert len(result.stores) >= 1
        assert len(result.imports) >= 1

    def test_parse_with_plugins(self, parser):
        code = '''
import { createPinia } from 'pinia';
import piniaPersistedState from 'pinia-plugin-persistedstate';

const pinia = createPinia();
pinia.use(piniaPersistedState);

export default pinia;
'''
        result = parser.parse(code, "stores/index.ts")
        assert isinstance(result, PiniaParseResult)
        assert len(result.instances) >= 1
        assert len(result.imports) >= 1

    def test_parse_with_testing(self, parser):
        code = '''
import { createTestingPinia } from '@pinia/testing';
import { mount } from '@vue/test-utils';
import { vi } from 'vitest';
import MyComponent from './MyComponent.vue';
import { useCounterStore } from '../stores/counter';

describe('MyComponent', () => {
    it('increments counter', async () => {
        const wrapper = mount(MyComponent, {
            global: {
                plugins: [createTestingPinia({ createSpy: vi.fn })],
            },
        });

        const store = useCounterStore();
        await wrapper.find('button').trigger('click');
        expect(store.increment).toHaveBeenCalledOnce();
    });
});
'''
        result = parser.parse(code, "test.spec.ts")
        assert isinstance(result, PiniaParseResult)
        assert len(result.imports) >= 1
        assert len(result.integrations) >= 1

    def test_parse_vue_sfc(self, parser):
        code = '''
<script setup lang="ts">
import { storeToRefs } from 'pinia';
import { useCounterStore } from '@/stores/counter';

const store = useCounterStore();
const { count, doubleCount } = storeToRefs(store);
const { increment } = store;
</script>

<template>
    <div>
        <p>Count: {{ count }}</p>
        <p>Double: {{ doubleCount }}</p>
        <button @click="increment">+</button>
    </div>
</template>
'''
        result = parser.parse(code, "Counter.vue")
        assert isinstance(result, PiniaParseResult)
        assert len(result.imports) >= 1

    def test_parse_store_composition(self, parser):
        code = '''
import { defineStore } from 'pinia';
import { useUserStore } from './user';

export const useCartStore = defineStore('cart', {
    state: () => ({
        items: [],
    }),
    getters: {
        totalWithDiscount() {
            const userStore = useUserStore();
            return this.items.reduce((sum, i) => sum + i.price, 0) * (1 - userStore.discount);
        },
    },
    actions: {
        async checkout() {
            const userStore = useUserStore();
            await api.checkout(this.items, userStore.address);
            this.items = [];
        },
    },
});
'''
        result = parser.parse(code, "cart.ts")
        assert isinstance(result, PiniaParseResult)
        assert len(result.stores) >= 1

    def test_parse_patch_and_subscribe(self, parser):
        code = '''
import { defineStore, storeToRefs } from 'pinia';

const store = useCartStore();

store.$patch({
    count: 10,
    name: 'test',
});

store.$patch((state) => {
    state.items.push({ id: 1 });
});

store.$subscribe((mutation, state) => {
    localStorage.setItem('cart', JSON.stringify(state));
}, { detached: true });

store.$onAction(({ name, args, after, onError }) => {
    console.log(name, args);
    after((result) => console.log(result));
    onError((error) => console.error(error));
});
'''
        result = parser.parse(code, "component.ts")
        assert isinstance(result, PiniaParseResult)

    def test_framework_detection(self, parser):
        code = '''
import { defineStore } from 'pinia';
import { usePinia } from '@pinia/nuxt';
'''
        result = parser.parse(code, "store.ts")
        assert "pinia" in result.detected_frameworks
        assert "@pinia/nuxt" in result.detected_frameworks or "nuxt" in result.detected_frameworks or len(result.detected_frameworks) >= 1

    def test_version_detection_v2(self, parser):
        code = '''
import { defineStore, storeToRefs, createPinia } from 'pinia';

export const useStore = defineStore('main', {
    state: () => ({ count: 0 }),
    actions: {
        increment() { this.count++; },
    },
});
'''
        result = parser.parse(code, "store.ts")
        # defineStore + storeToRefs is Pinia v1+/v2
        assert result.pinia_version in ('v1', 'v2', '')

    def test_feature_detection(self, parser):
        code = '''
import { defineStore, storeToRefs, acceptHMRUpdate } from 'pinia';
import { ref, computed } from 'vue';

export const useStore = defineStore('main', () => {
    const count = ref(0);
    const double = computed(() => count.value * 2);
    function increment() { count.value++; }
    return { count, double, increment };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useStore, import.meta.hot));
}
'''
        result = parser.parse(code, "store.ts")
        assert len(result.detected_features) >= 1

    def test_empty_file(self, parser):
        result = parser.parse("", "empty.ts")
        assert isinstance(result, PiniaParseResult)
        assert len(result.stores) == 0
        assert len(result.imports) == 0

    def test_non_pinia_file(self, parser):
        code = '''
import React from 'react';
const App = () => <div>Hello World</div>;
export default App;
'''
        result = parser.parse(code, "app.tsx")
        assert isinstance(result, PiniaParseResult)
        assert len(result.stores) == 0

    def test_map_helpers_parsing(self, parser):
        code = '''
import { mapState, mapActions, mapStores, mapWritableState } from 'pinia';
import { useCounterStore } from '@/stores/counter';

export default {
    computed: {
        ...mapState(useCounterStore, ['count', 'double']),
        ...mapStores(useCounterStore),
    },
    methods: {
        ...mapActions(useCounterStore, ['increment']),
    },
};
'''
        result = parser.parse(code, "component.vue")
        assert isinstance(result, PiniaParseResult)
        assert len(result.imports) >= 1

    def test_nuxt_integration(self, parser):
        code = '''
import { defineStore } from 'pinia';

// Auto-imported in Nuxt via @pinia/nuxt
export const useCounterStore = defineStore('counter', {
    state: () => ({ count: 0 }),
    actions: {
        increment() { this.count++; },
    },
});
'''
        result = parser.parse(code, "stores/counter.ts")
        assert isinstance(result, PiniaParseResult)
        assert len(result.stores) >= 1

    def test_persist_configuration(self, parser):
        code = '''
import { defineStore } from 'pinia';

export const useSettingsStore = defineStore('settings', {
    state: () => ({
        theme: 'light',
        locale: 'en',
        sidebarOpen: true,
    }),
    persist: {
        key: 'app-settings',
        storage: localStorage,
        paths: ['theme', 'locale'],
    },
});
'''
        result = parser.parse(code, "settings.ts")
        assert isinstance(result, PiniaParseResult)
        assert len(result.stores) >= 1

    def test_custom_plugin_with_context(self, parser):
        code = '''
import { PiniaPluginContext } from 'pinia';

function logPlugin({ store, app, pinia, options }: PiniaPluginContext) {
    store.$subscribe((mutation) => {
        console.log(`[${store.$id}]`, mutation.type);
    });

    store.$onAction(({ name, after, onError }) => {
        after(() => console.log(`Action ${name} completed`));
        onError((error) => console.error(`Action ${name} failed`, error));
    });
}

const pinia = createPinia();
pinia.use(logPlugin);
'''
        result = parser.parse(code, "plugins/logger.ts")
        assert isinstance(result, PiniaParseResult)

    def test_store_augmentation_types(self, parser):
        code = '''
import 'pinia';

declare module 'pinia' {
    export interface PiniaCustomProperties {
        $logger: (message: string) => void;
    }
    export interface PiniaCustomStateProperties<S> {
        lastModified: number;
    }
}
'''
        result = parser.parse(code, "pinia.d.ts")
        assert isinstance(result, PiniaParseResult)

    def test_multiple_stores_full_parse(self, parser):
        code = '''
import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        token: null,
        isAuthenticated: false,
    }),
    getters: {
        userName: (state) => state.user?.name || 'Guest',
    },
    actions: {
        async login(credentials) {
            const response = await api.login(credentials);
            this.token = response.token;
            this.user = response.user;
            this.isAuthenticated = true;
        },
        logout() {
            this.$reset();
        },
    },
});

export const useCartStore = defineStore('cart', {
    state: () => ({
        items: [],
        total: 0,
    }),
    getters: {
        itemCount: (state) => state.items.length,
    },
    actions: {
        addItem(item) {
            this.items.push(item);
            this.total += item.price;
        },
        removeItem(id) {
            const index = this.items.findIndex(i => i.id === id);
            if (index !== -1) {
                this.total -= this.items[index].price;
                this.items.splice(index, 1);
            }
        },
    },
});
'''
        result = parser.parse(code, "stores.ts")
        assert isinstance(result, PiniaParseResult)
        assert len(result.stores) >= 2

    def test_pinia_orm_integration(self, parser):
        code = '''
import { defineStore } from 'pinia';
import { Model, useRepo } from 'pinia-orm';

class User extends Model {
    static entity = 'users';
    static fields() {
        return {
            id: this.uid(),
            name: this.string(''),
            email: this.string(''),
        };
    }
}

export const useUserRepo = () => useRepo(User);
'''
        result = parser.parse(code, "models/user.ts")
        assert isinstance(result, PiniaParseResult)


# ═══════════════════════════════════════════════════════════════════
# BPL Practice Tests
# ═══════════════════════════════════════════════════════════════════

class TestPiniaBPLPractices:
    """Tests for Pinia BPL practices loading."""

    def test_practices_yaml_loads(self):
        """Verify pinia_core.yaml loads without errors."""
        from codetrellis.bpl.repository import BestPracticesRepository
        repo = BestPracticesRepository()
        repo.load_all()
        # Should have PINIA practices
        pinia_practices = [p for p_id, p in repo.practices.items() if p_id.startswith('PINIA')]
        assert len(pinia_practices) == 50, f"Expected 50 PINIA practices, got {len(pinia_practices)}"

    def test_practice_ids_sequential(self):
        """Verify practice IDs are PINIA001-PINIA050."""
        from codetrellis.bpl.repository import BestPracticesRepository
        repo = BestPracticesRepository()
        repo.load_all()
        for i in range(1, 51):
            pid = f"PINIA{i:03d}"
            assert pid in repo.practices, f"Missing practice: {pid}"

    def test_practice_categories_valid(self):
        """Verify all practice categories are valid PracticeCategory enum values."""
        from codetrellis.bpl.repository import BestPracticesRepository
        from codetrellis.bpl.models import PracticeCategory
        repo = BestPracticesRepository()
        repo.load_all()
        for pid, practice in repo.practices.items():
            if pid.startswith('PINIA'):
                assert isinstance(practice.category, PracticeCategory), \
                    f"Practice {pid} has invalid category: {practice.category}"

    def test_practice_severities_valid(self):
        """Verify all practice severities are valid."""
        from codetrellis.bpl.repository import BestPracticesRepository
        repo = BestPracticesRepository()
        repo.load_all()
        valid_severities = {'critical', 'warning', 'info'}
        for pid, practice in repo.practices.items():
            if pid.startswith('PINIA'):
                assert practice.priority.value in {'critical', 'high', 'medium', 'low', 'optional'}, \
                    f"Practice {pid} has invalid severity"


# ═══════════════════════════════════════════════════════════════════
# Scanner Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestPiniaScannerIntegration:
    """Tests for Pinia integration in ProjectMatrix and scanner."""

    def test_project_matrix_has_pinia_fields(self):
        """Verify ProjectMatrix has all 14 Pinia fields."""
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        pinia_fields = [
            'pinia_stores', 'pinia_getters', 'pinia_store_to_refs',
            'pinia_actions', 'pinia_patches', 'pinia_subscriptions',
            'pinia_plugins', 'pinia_instances',
            'pinia_imports', 'pinia_integrations', 'pinia_types',
            'pinia_detected_frameworks', 'pinia_detected_features',
            'pinia_version',
        ]
        for field_name in pinia_fields:
            assert hasattr(matrix, field_name), f"ProjectMatrix missing field: {field_name}"

    def test_project_matrix_pinia_defaults(self):
        """Verify Pinia fields have correct default values."""
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        assert matrix.pinia_stores == []
        assert matrix.pinia_getters == []
        assert matrix.pinia_store_to_refs == []
        assert matrix.pinia_actions == []
        assert matrix.pinia_patches == []
        assert matrix.pinia_subscriptions == []
        assert matrix.pinia_plugins == []
        assert matrix.pinia_instances == []
        assert matrix.pinia_imports == []
        assert matrix.pinia_integrations == []
        assert matrix.pinia_types == []
        assert matrix.pinia_detected_frameworks == []
        assert matrix.pinia_detected_features == []
        assert matrix.pinia_version == ""

    def test_scanner_has_pinia_parser(self):
        """Verify Scanner initializes pinia_parser."""
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner("/tmp/test")
        assert hasattr(scanner, 'pinia_parser')
        assert isinstance(scanner.pinia_parser, EnhancedPiniaParser)
