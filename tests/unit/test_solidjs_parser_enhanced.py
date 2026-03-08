"""
Tests for Solid.js extractors and EnhancedSolidParser.

Part of CodeTrellis v4.62 Solid.js Framework Support.
Tests cover:
- Component extraction (functional, typed, control flow, lazy, dynamic)
- Signal extraction (createSignal, createMemo, createEffect, reactive utils)
- Store extraction (createStore, createMutable, produce, reconcile)
- Resource extraction (createResource, server$, cache, action, route data)
- Router extraction (routes, hooks, navigation)
- API extraction (imports, contexts, lifecycles, integrations, types)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from codetrellis.solidjs_parser_enhanced import (
    EnhancedSolidParser,
    SolidParseResult,
)
from codetrellis.extractors.solidjs import (
    SolidComponentExtractor,
    SolidSignalExtractor,
    SolidStoreExtractor,
    SolidResourceExtractor,
    SolidRouterExtractor,
    SolidApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedSolidParser()


@pytest.fixture
def component_extractor():
    return SolidComponentExtractor()


@pytest.fixture
def signal_extractor():
    return SolidSignalExtractor()


@pytest.fixture
def store_extractor():
    return SolidStoreExtractor()


@pytest.fixture
def resource_extractor():
    return SolidResourceExtractor()


@pytest.fixture
def router_extractor():
    return SolidRouterExtractor()


@pytest.fixture
def api_extractor():
    return SolidApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSolidComponentExtractor:
    """Tests for SolidComponentExtractor."""

    def test_basic_functional_component(self, component_extractor):
        code = '''
import { createSignal } from 'solid-js';

function Counter() {
    const [count, setCount] = createSignal(0);
    return <div>{count()}</div>;
}
'''
        result = component_extractor.extract(code, "Counter.tsx")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.name == "Counter"

    def test_arrow_function_component(self, component_extractor):
        code = '''
const Greeting = (props) => {
    return <h1>Hello, {props.name}!</h1>;
};
'''
        result = component_extractor.extract(code, "Greeting.tsx")
        components = result.get('components', [])
        assert len(components) >= 1
        assert components[0].name == "Greeting"

    def test_typed_component(self, component_extractor):
        code = '''
import { Component } from 'solid-js';

const App: Component<{ title: string }> = (props) => {
    return <main>{props.title}</main>;
};
'''
        result = component_extractor.extract(code, "App.tsx")
        components = result.get('components', [])
        assert len(components) >= 1

    def test_control_flow_show(self, component_extractor):
        code = '''
import { Show } from 'solid-js';

function ConditionalView() {
    return (
        <Show when={isLoggedIn()} fallback={<Login />}>
            <Dashboard />
        </Show>
    );
}
'''
        result = component_extractor.extract(code, "View.tsx")
        control_flows = result.get('control_flows', [])
        assert len(control_flows) >= 1
        cf = control_flows[0]
        assert cf.name == "Show"

    def test_control_flow_for(self, component_extractor):
        code = '''
import { For } from 'solid-js';

function TodoList() {
    return (
        <ul>
            <For each={todos()}>{(todo) => <li>{todo.text}</li>}</For>
        </ul>
    );
}
'''
        result = component_extractor.extract(code, "TodoList.tsx")
        control_flows = result.get('control_flows', [])
        assert any(cf.name == "For" for cf in control_flows)

    def test_control_flow_switch_match(self, component_extractor):
        code = '''
import { Switch, Match } from 'solid-js';

function StatusView() {
    return (
        <Switch>
            <Match when={status() === 'loading'}>Loading...</Match>
            <Match when={status() === 'error'}>Error!</Match>
            <Match when={status() === 'ready'}>Ready</Match>
        </Switch>
    );
}
'''
        result = component_extractor.extract(code, "Status.tsx")
        control_flows = result.get('control_flows', [])
        assert any(cf.name == "Switch" for cf in control_flows)

    def test_lazy_component(self, component_extractor):
        code = '''
import { lazy } from 'solid-js';

const Dashboard = lazy(() => import('./Dashboard'));
'''
        result = component_extractor.extract(code, "app.tsx")
        components = result.get('components', [])
        assert any(c.name == "Dashboard" for c in components)

    def test_suspense_and_error_boundary(self, component_extractor):
        code = '''
import { Suspense, ErrorBoundary } from 'solid-js';

function App() {
    return (
        <ErrorBoundary fallback={<p>Error!</p>}>
            <Suspense fallback={<p>Loading...</p>}>
                <Content />
            </Suspense>
        </ErrorBoundary>
    );
}
'''
        result = component_extractor.extract(code, "App.tsx")
        control_flows = result.get('control_flows', [])
        flow_names = [cf.name for cf in control_flows]
        assert "Suspense" in flow_names
        assert "ErrorBoundary" in flow_names

    def test_portal_component(self, component_extractor):
        code = '''
import { Portal } from 'solid-js/web';

function Modal() {
    return (
        <Portal>
            <div class="modal">Hello</div>
        </Portal>
    );
}
'''
        result = component_extractor.extract(code, "Modal.tsx")
        control_flows = result.get('control_flows', [])
        assert any(cf.name == "Portal" for cf in control_flows)

    def test_dynamic_component(self, component_extractor):
        code = '''
import { Dynamic } from 'solid-js/web';

function DynamicView() {
    return <Dynamic component={components[type()]} />;
}
'''
        result = component_extractor.extract(code, "Dynamic.tsx")
        components = result.get('components', [])
        assert len(components) >= 1


# ═══════════════════════════════════════════════════════════════════
# Signal Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSolidSignalExtractor:
    """Tests for SolidSignalExtractor."""

    def test_basic_signal(self, signal_extractor):
        code = '''
import { createSignal } from 'solid-js';

const [count, setCount] = createSignal(0);
'''
        result = signal_extractor.extract(code, "counter.ts")
        signals = result.get('signals', [])
        assert len(signals) >= 1
        sig = signals[0]
        assert sig.name == "count"
        assert sig.setter_name == "setCount"

    def test_typed_signal(self, signal_extractor):
        code = '''
const [user, setUser] = createSignal<User | null>(null);
'''
        result = signal_extractor.extract(code, "user.ts")
        signals = result.get('signals', [])
        assert len(signals) >= 1
        sig = signals[0]
        assert sig.name == "user"

    def test_create_memo(self, signal_extractor):
        code = '''
import { createMemo } from 'solid-js';

const doubled = createMemo(() => count() * 2);
'''
        result = signal_extractor.extract(code, "derived.ts")
        memos = result.get('memos', [])
        assert len(memos) >= 1
        assert memos[0].name == "doubled"

    def test_create_effect(self, signal_extractor):
        code = '''
import { createEffect } from 'solid-js';

createEffect(() => {
    console.log('count changed:', count());
});
'''
        result = signal_extractor.extract(code, "effect.ts")
        effects = result.get('effects', [])
        assert len(effects) >= 1
        assert effects[0].effect_type == "createEffect"

    def test_create_render_effect(self, signal_extractor):
        code = '''
import { createRenderEffect } from 'solid-js';

createRenderEffect(() => {
    ref.style.color = color();
});
'''
        result = signal_extractor.extract(code, "render-effect.ts")
        effects = result.get('effects', [])
        assert len(effects) >= 1
        assert effects[0].effect_type == "createRenderEffect"

    def test_create_computed(self, signal_extractor):
        code = '''
import { createComputed } from 'solid-js';

createComputed(() => {
    setTotal(count() * price());
});
'''
        result = signal_extractor.extract(code, "computed.ts")
        effects = result.get('effects', [])
        assert len(effects) >= 1
        assert effects[0].effect_type == "createComputed"

    def test_effect_with_on_wrapper(self, signal_extractor):
        code = '''
import { createEffect, on } from 'solid-js';

createEffect(on(count, (value, prev) => {
    console.log('changed from', prev, 'to', value);
}));
'''
        result = signal_extractor.extract(code, "on-effect.ts")
        effects = result.get('effects', [])
        assert len(effects) >= 1

    def test_batch_util(self, signal_extractor):
        code = '''
import { batch } from 'solid-js';

batch(() => {
    setCount(1);
    setName('hello');
});
'''
        result = signal_extractor.extract(code, "batch.ts")
        utils = result.get('reactive_utils', [])
        assert any(u.util_type == "batch" for u in utils)

    def test_untrack_util(self, signal_extractor):
        code = '''
import { untrack } from 'solid-js';

const value = untrack(() => name());
'''
        result = signal_extractor.extract(code, "untrack.ts")
        utils = result.get('reactive_utils', [])
        assert any(u.util_type == "untrack" for u in utils)

    def test_create_reaction(self, signal_extractor):
        code = '''
import { createReaction } from 'solid-js';

const track = createReaction(() => save(state()));
track(() => state.count);
'''
        result = signal_extractor.extract(code, "reaction.ts")
        effects = result.get('effects', [])
        assert any(e.effect_type == "createReaction" for e in effects)

    def test_map_array(self, signal_extractor):
        code = '''
import { mapArray } from 'solid-js';

const mapped = mapArray(items, (item, index) => ({
    ...item, doubled: () => item.value * 2
}));
'''
        result = signal_extractor.extract(code, "map.ts")
        utils = result.get('reactive_utils', [])
        assert any(u.util_type == "mapArray" for u in utils)


# ═══════════════════════════════════════════════════════════════════
# Store Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSolidStoreExtractor:
    """Tests for SolidStoreExtractor."""

    def test_basic_store(self, store_extractor):
        code = '''
import { createStore } from 'solid-js/store';

const [state, setState] = createStore({
    user: { name: 'Alice' },
    items: [],
});
'''
        result = store_extractor.extract(code, "store.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        store = stores[0]
        assert store.name == "state"
        assert store.setter_name == "setState"

    def test_typed_store(self, store_extractor):
        code = '''
const [state, setState] = createStore<AppState>({
    count: 0,
    items: [],
});
'''
        result = store_extractor.extract(code, "typed-store.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1

    def test_create_mutable(self, store_extractor):
        code = '''
import { createMutable } from 'solid-js/store';

const state = createMutable({
    count: 0,
    name: 'test',
});
'''
        result = store_extractor.extract(code, "mutable.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        assert stores[0].store_type == "mutable"

    def test_produce_usage(self, store_extractor):
        code = '''
import { createStore, produce } from 'solid-js/store';

const [state, setState] = createStore({ items: [] });

setState(produce((draft) => {
    draft.items.push({ id: 1 });
}));
'''
        result = store_extractor.extract(code, "produce.ts")
        stores = result.get('stores', [])
        updates = result.get('store_updates', [])
        assert len(stores) >= 1

    def test_reconcile_usage(self, store_extractor):
        code = '''
import { createStore, reconcile } from 'solid-js/store';

const [state, setState] = createStore({ todos: [] });
setState('todos', reconcile(serverData));
'''
        result = store_extractor.extract(code, "reconcile.ts")
        stores = result.get('stores', [])
        updates = result.get('store_updates', [])
        assert len(stores) >= 1


# ═══════════════════════════════════════════════════════════════════
# Resource Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSolidResourceExtractor:
    """Tests for SolidResourceExtractor."""

    def test_basic_resource(self, resource_extractor):
        code = '''
import { createResource } from 'solid-js';

const [data] = createResource(fetchData);
'''
        result = resource_extractor.extract(code, "resource.ts")
        resources = result.get('resources', [])
        assert len(resources) >= 1
        assert resources[0].name == "data"

    def test_resource_with_source(self, resource_extractor):
        code = '''
const [user] = createResource(userId, fetchUser);
'''
        result = resource_extractor.extract(code, "user-resource.ts")
        resources = result.get('resources', [])
        assert len(resources) >= 1

    def test_typed_resource(self, resource_extractor):
        code = '''
const [products] = createResource<Product[]>(fetchProducts);
'''
        result = resource_extractor.extract(code, "typed-resource.ts")
        resources = result.get('resources', [])
        assert len(resources) >= 1

    def test_server_function(self, resource_extractor):
        code = '''
import server$ from 'solid-start/server';

const getData = server$(async () => {
    return await db.query('SELECT * FROM users');
});
'''
        result = resource_extractor.extract(code, "server.ts")
        server_fns = result.get('server_functions', [])
        assert len(server_fns) >= 1

    def test_create_async_v2(self, resource_extractor):
        code = '''
import { createAsync } from '@solidjs/start';

const user = createAsync(() => getUser(params.id));
'''
        result = resource_extractor.extract(code, "async.ts")
        resources = result.get('resources', [])
        assert len(resources) >= 1

    def test_cache_function(self, resource_extractor):
        code = '''
import { cache } from '@solidjs/start';

const getUser = cache(async (id) => {
    'use server';
    return db.user.findUnique({ where: { id } });
}, 'user');
'''
        result = resource_extractor.extract(code, "cache.ts")
        server_fns = result.get('server_functions', [])
        assert len(server_fns) >= 1

    def test_action_function(self, resource_extractor):
        code = '''
import { action } from '@solidjs/start';

const updateUser = action(async (formData) => {
    'use server';
    await db.user.update({ ... });
});
'''
        result = resource_extractor.extract(code, "action.ts")
        server_fns = result.get('server_functions', [])
        assert len(server_fns) >= 1

    def test_route_data(self, resource_extractor):
        code = '''
import { createRouteData } from 'solid-start';

export function routeData() {
    return createRouteData(async () => {
        return await fetchPosts();
    });
}
'''
        result = resource_extractor.extract(code, "route-data.ts")
        route_data = result.get('route_data', [])
        assert len(route_data) >= 1


# ═══════════════════════════════════════════════════════════════════
# Router Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSolidRouterExtractor:
    """Tests for SolidRouterExtractor."""

    def test_declarative_route(self, router_extractor):
        code = '''
import { Route } from '@solidjs/router';

<Route path="/users/:id" component={UserProfile} />
'''
        result = router_extractor.extract(code, "routes.tsx")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        route = routes[0]
        assert route.path == "/users/:id"

    def test_multiple_routes(self, router_extractor):
        code = '''
<Route path="/" component={Home} />
<Route path="/about" component={About} />
<Route path="/users/:id" component={UserProfile} />
<Route path="*404" component={NotFound} />
'''
        result = router_extractor.extract(code, "routes.tsx")
        routes = result.get('routes', [])
        assert len(routes) >= 4

    def test_use_params_hook(self, router_extractor):
        code = '''
import { useParams } from '@solidjs/router';

function UserProfile() {
    const params = useParams();
    return <div>{params.id}</div>;
}
'''
        result = router_extractor.extract(code, "user.tsx")
        hooks = result.get('router_hooks', [])
        assert any(h.hook_name == "useParams" for h in hooks)

    def test_use_navigate_hook(self, router_extractor):
        code = '''
import { useNavigate } from '@solidjs/router';

function LoginButton() {
    const navigate = useNavigate();
    return <button onClick={() => navigate('/dashboard')}>Login</button>;
}
'''
        result = router_extractor.extract(code, "login.tsx")
        hooks = result.get('router_hooks', [])
        assert any(h.hook_name == "useNavigate" for h in hooks)

    def test_use_location_hook(self, router_extractor):
        code = '''
import { useLocation } from '@solidjs/router';

const location = useLocation();
'''
        result = router_extractor.extract(code, "nav.tsx")
        hooks = result.get('router_hooks', [])
        assert any(h.hook_name == "useLocation" for h in hooks)

    def test_use_search_params(self, router_extractor):
        code = '''
import { useSearchParams } from '@solidjs/router';

const searchParams = useSearchParams();
'''
        result = router_extractor.extract(code, "search.tsx")
        hooks = result.get('router_hooks', [])
        assert any(h.hook_name == "useSearchParams" for h in hooks)


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSolidApiExtractor:
    """Tests for SolidApiExtractor."""

    def test_solid_js_import(self, api_extractor):
        code = '''
import { createSignal, createEffect, createMemo, onMount } from 'solid-js';
'''
        result = api_extractor.extract(code, "app.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 1
        imp = imports[0]
        assert imp.source == "solid-js"
        assert "createSignal" in imp.named_imports

    def test_store_import(self, api_extractor):
        code = '''
import { createStore, produce, reconcile } from 'solid-js/store';
'''
        result = api_extractor.extract(code, "store.ts")
        imports = result.get('imports', [])
        assert any(imp.source == "solid-js/store" for imp in imports)

    def test_router_import(self, api_extractor):
        code = '''
import { Router, Route, useParams, useNavigate } from '@solidjs/router';
'''
        result = api_extractor.extract(code, "router.ts")
        imports = result.get('imports', [])
        assert any(imp.source == "@solidjs/router" for imp in imports)

    def test_create_context(self, api_extractor):
        code = '''
import { createContext, useContext } from 'solid-js';

const ThemeContext = createContext({ theme: 'light' });
'''
        result = api_extractor.extract(code, "context.ts")
        contexts = result.get('contexts', [])
        assert len(contexts) >= 1
        assert contexts[0].name == "ThemeContext"

    def test_on_mount_lifecycle(self, api_extractor):
        code = '''
import { onMount, onCleanup, onError } from 'solid-js';

onMount(() => {
    console.log('mounted');
});

onCleanup(() => {
    console.log('cleanup');
});
'''
        result = api_extractor.extract(code, "lifecycle.ts")
        lifecycles = result.get('lifecycles', [])
        assert len(lifecycles) >= 2

    def test_kobalte_integration(self, api_extractor):
        code = '''
import { Button, Dialog } from '@kobalte/core';
'''
        result = api_extractor.extract(code, "ui.tsx")
        integrations = result.get('integrations', [])
        assert len(integrations) >= 1

    def test_tanstack_query_integration(self, api_extractor):
        code = '''
import { createQuery, QueryClient } from '@tanstack/solid-query';
'''
        result = api_extractor.extract(code, "query.ts")
        integrations = result.get('integrations', [])
        assert len(integrations) >= 1

    def test_solid_primitives_integration(self, api_extractor):
        code = '''
import { createLocalStorage } from '@solid-primitives/storage';
import { createMediaQuery } from '@solid-primitives/media';
'''
        result = api_extractor.extract(code, "primitives.ts")
        integrations = result.get('integrations', [])
        assert len(integrations) >= 2

    def test_typescript_types(self, api_extractor):
        code = '''
import type { Component, Accessor, Setter, JSX } from 'solid-js';

const App: Component<{ name: string }> = (props) => {
    return <div>{props.name}</div>;
};
'''
        result = api_extractor.extract(code, "typed.tsx")
        types = result.get('types', [])
        assert len(types) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedSolidParser:
    """Tests for EnhancedSolidParser integration."""

    def test_is_solid_file_positive(self, parser):
        code = '''
import { createSignal } from 'solid-js';
const [count, setCount] = createSignal(0);
'''
        assert parser.is_solid_file(code) is True

    def test_is_solid_file_negative(self, parser):
        code = '''
import React from 'react';
function App() { return <div>Hello</div>; }
'''
        assert parser.is_solid_file(code) is False

    def test_is_solid_file_store_import(self, parser):
        code = '''
import { createStore } from 'solid-js/store';
'''
        assert parser.is_solid_file(code) is True

    def test_is_solid_file_router(self, parser):
        code = '''
import { Route } from '@solidjs/router';
'''
        assert parser.is_solid_file(code) is True

    def test_is_solid_file_solidstart(self, parser):
        code = '''
import { cache, action } from '@solidjs/start';
'''
        assert parser.is_solid_file(code) is True

    def test_is_solid_file_kobalte(self, parser):
        code = '''
import { Button } from '@kobalte/core';
'''
        assert parser.is_solid_file(code) is True

    def test_parse_full_component(self, parser):
        code = '''
import { createSignal, createEffect, onMount, onCleanup, Show, For } from 'solid-js';
import { createStore } from 'solid-js/store';
import { useParams, useNavigate } from '@solidjs/router';

function TodoApp() {
    const [todos, setTodos] = createStore([]);
    const [filter, setFilter] = createSignal('all');
    const params = useParams();
    const navigate = useNavigate();

    const filteredTodos = createMemo(() => {
        if (filter() === 'all') return todos;
        return todos.filter(t => t.done === (filter() === 'done'));
    });

    onMount(() => {
        console.log('mounted');
    });

    createEffect(() => {
        document.title = `Todos (${todos.length})`;
    });

    onCleanup(() => {
        console.log('cleanup');
    });

    return (
        <div>
            <Show when={todos.length > 0} fallback={<p>No todos</p>}>
                <For each={filteredTodos()}>
                    {(todo) => <div>{todo.text}</div>}
                </For>
            </Show>
        </div>
    );
}
'''
        result = parser.parse(code, "TodoApp.tsx")
        assert isinstance(result, SolidParseResult)
        assert result.file_path == "TodoApp.tsx"
        assert result.file_type == "tsx"

        # Should detect signals
        assert len(result.signals) >= 1

        # Should detect stores
        assert len(result.stores) >= 1

        # Should detect effects
        assert len(result.effects) >= 1

        # Should detect router hooks
        assert len(result.router_hooks) >= 2

        # Should detect control flows
        assert len(result.control_flows) >= 2

        # Should detect lifecycles
        assert len(result.lifecycles) >= 2

        # Should detect frameworks
        assert len(result.detected_frameworks) >= 1

    def test_framework_detection_core(self, parser):
        code = '''
import { createSignal } from 'solid-js';
import { createStore } from 'solid-js/store';
'''
        result = parser.parse(code, "app.ts")
        assert "solid-js" in result.detected_frameworks
        assert "solid-js-store" in result.detected_frameworks

    def test_framework_detection_router(self, parser):
        code = '''
import { Router, Route } from '@solidjs/router';
'''
        result = parser.parse(code, "router.tsx")
        assert "solidjs-router" in result.detected_frameworks

    def test_framework_detection_start(self, parser):
        code = '''
import { cache, action } from '@solidjs/start';
'''
        result = parser.parse(code, "start.ts")
        assert "solid-start" in result.detected_frameworks

    def test_framework_detection_kobalte(self, parser):
        code = '''
import { Button } from '@kobalte/core';
'''
        result = parser.parse(code, "ui.tsx")
        assert "kobalte" in result.detected_frameworks

    def test_framework_detection_tanstack_query(self, parser):
        code = '''
import { createQuery } from '@tanstack/solid-query';
'''
        result = parser.parse(code, "query.ts")
        assert "tanstack-solid-query" in result.detected_frameworks

    def test_framework_detection_solid_primitives(self, parser):
        code = '''
import { createLocalStorage } from '@solid-primitives/storage';
'''
        result = parser.parse(code, "storage.ts")
        assert "solid-primitives" in result.detected_frameworks

    def test_framework_detection_testing(self, parser):
        code = '''
import { render, screen } from '@solidjs/testing-library';
'''
        result = parser.parse(code, "test.ts")
        assert "solidjs-testing" in result.detected_frameworks

    def test_framework_detection_devtools(self, parser):
        code = '''
import { attachDevtools } from 'solid-devtools';
'''
        result = parser.parse(code, "dev.ts")
        assert "solid-devtools" in result.detected_frameworks

    def test_feature_detection(self, parser):
        code = '''
import { createSignal, createMemo, createEffect, batch, untrack, onMount, onCleanup } from 'solid-js';

const [count, setCount] = createSignal(0);
const doubled = createMemo(() => count() * 2);

createEffect(() => {
    document.title = `Count: ${count()}`;
});

batch(() => {
    setCount(1);
});

const raw = untrack(() => count());

onMount(() => {});
onCleanup(() => {});
'''
        result = parser.parse(code, "features.ts")
        features = result.detected_features
        assert "create_signal" in features
        assert "create_memo" in features
        assert "create_effect" in features
        assert "batch" in features
        assert "untrack" in features
        assert "on_mount" in features
        assert "on_cleanup" in features

    def test_feature_detection_control_flow(self, parser):
        code = '''
<Show when={visible()}>Content</Show>
<For each={items()}>{(item) => <div>{item}</div>}</For>
<Switch>
    <Match when={true}>Yes</Match>
</Switch>
<Index each={cells()}>{(cell) => <td>{cell()}</td>}</Index>
<Portal><div>Modal</div></Portal>
<Suspense fallback={<p>Loading</p>}>Content</Suspense>
<ErrorBoundary fallback={<p>Error</p>}>Content</ErrorBoundary>
'''
        result = parser.parse(code, "control.tsx")
        features = result.detected_features
        assert "show" in features
        assert "for_loop" in features
        assert "switch_match" in features
        assert "index" in features
        assert "portal" in features
        assert "suspense" in features
        assert "error_boundary" in features

    def test_feature_detection_stores(self, parser):
        code = '''
import { createStore, produce, reconcile } from 'solid-js/store';

const [state, setState] = createStore({ count: 0 });
setState(produce((draft) => { draft.count++; }));
setState('todos', reconcile(data));
'''
        result = parser.parse(code, "store-features.ts")
        features = result.detected_features
        assert "create_store" in features
        assert "produce" in features
        assert "reconcile" in features

    def test_version_detection_v1(self, parser):
        code = '''
import { createSignal } from 'solid-js';
const [count, setCount] = createSignal(0);
'''
        result = parser.parse(code, "v1.ts")
        assert result.solid_version == "v1"

    def test_version_detection_v1_1(self, parser):
        code = '''
import { createSignal, startTransition } from 'solid-js';
const [count, setCount] = createSignal(0);
startTransition(() => setCount(1));
'''
        result = parser.parse(code, "v1.1.ts")
        assert result.solid_version == "v1.1"

    def test_version_detection_v2(self, parser):
        code = '''
import { createAsync } from '@solidjs/start';
const user = createAsync(() => getUser(params.id));
'''
        result = parser.parse(code, "v2.ts")
        assert result.solid_version == "v2"

    def test_version_detection_v2_solidjs_start(self, parser):
        code = '''
import { cache, action } from '@solidjs/start';
'''
        result = parser.parse(code, "start-v1.ts")
        assert result.solid_version == "v2"

    def test_version_detection_v1_8(self, parser):
        code = '''
import server$ from 'solid-start/server';
const getData = server$(async () => {});
'''
        result = parser.parse(code, "v1.8.ts")
        assert result.solid_version == "v1.8"

    def test_file_type_detection(self, parser):
        assert parser.parse("", "app.tsx").file_type == "tsx"
        assert parser.parse("", "app.jsx").file_type == "jsx"
        assert parser.parse("", "app.ts").file_type == "ts"
        assert parser.parse("", "app.js").file_type == "js"
        assert parser.parse("", "app.mjs").file_type == "js"

    def test_parse_result_dataclass(self, parser):
        code = '''
import { createSignal } from 'solid-js';
const [x, setX] = createSignal(0);
'''
        result = parser.parse(code, "test.tsx")
        assert isinstance(result, SolidParseResult)
        assert isinstance(result.signals, list)
        assert isinstance(result.memos, list)
        assert isinstance(result.effects, list)
        assert isinstance(result.stores, list)
        assert isinstance(result.resources, list)
        assert isinstance(result.routes, list)
        assert isinstance(result.imports, list)
        assert isinstance(result.detected_frameworks, list)
        assert isinstance(result.detected_features, list)

    def test_empty_content(self, parser):
        result = parser.parse("", "empty.tsx")
        assert isinstance(result, SolidParseResult)
        assert len(result.signals) == 0
        assert len(result.components) == 0

    def test_non_solid_content(self, parser):
        code = '''
import React from 'react';
function App() {
    const [count, setCount] = React.useState(0);
    return <div>{count}</div>;
}
'''
        result = parser.parse(code, "react-app.tsx")
        assert len(result.detected_frameworks) == 0

    def test_version_compare_utility(self, parser):
        assert parser._version_compare("v2", "v1") > 0
        assert parser._version_compare("v1", "v2") < 0
        assert parser._version_compare("v1.1", "v1") > 0
        assert parser._version_compare("v1.4", "v1.1") > 0
        assert parser._version_compare("v1", "v1") == 0
        assert parser._version_compare("", "v1") < 0

    def test_solid_start_comprehensive(self, parser):
        code = '''
import { createAsync, cache, action } from '@solidjs/start';
import { useParams, useNavigate } from '@solidjs/router';
import { createSignal, createEffect, Show, Suspense } from 'solid-js';
import { createStore } from 'solid-js/store';

const getUser = cache(async (id: string) => {
    'use server';
    return db.user.findUnique({ where: { id } });
}, 'user');

const updateUser = action(async (formData: FormData) => {
    'use server';
    await db.user.update({});
});

export default function UserPage() {
    const params = useParams<{ id: string }>();
    const user = createAsync(() => getUser(params.id));
    const [editing, setEditing] = createSignal(false);
    const navigate = useNavigate();

    return (
        <Suspense fallback={<p>Loading...</p>}>
            <Show when={user()}>
                {(u) => <div>{u().name}</div>}
            </Show>
        </Suspense>
    );
}
'''
        result = parser.parse(code, "user.tsx")
        assert result.solid_version == "v2"
        assert "solid-start" in result.detected_frameworks
        assert "solidjs-router" in result.detected_frameworks
        assert "solid-js" in result.detected_frameworks
        assert "solid-js-store" in result.detected_frameworks
        assert len(result.signals) >= 1
        assert len(result.server_functions) >= 1
        assert len(result.router_hooks) >= 2
        assert len(result.control_flows) >= 2

    def test_multiple_frameworks_detected(self, parser):
        code = '''
import { createSignal } from 'solid-js';
import { createStore } from 'solid-js/store';
import { Route } from '@solidjs/router';
import { Button } from '@kobalte/core';
import { createQuery } from '@tanstack/solid-query';
import { createLocalStorage } from '@solid-primitives/storage';
import { render } from '@solidjs/testing-library';
'''
        result = parser.parse(code, "app.tsx")
        assert "solid-js" in result.detected_frameworks
        assert "solid-js-store" in result.detected_frameworks
        assert "solidjs-router" in result.detected_frameworks
        assert "kobalte" in result.detected_frameworks
        assert "tanstack-solid-query" in result.detected_frameworks
        assert "solid-primitives" in result.detected_frameworks
        assert "solidjs-testing" in result.detected_frameworks
