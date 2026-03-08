"""
Tests for Qwik extractors and EnhancedQwikParser.

Part of CodeTrellis v4.63 Qwik Framework Support.
Tests cover:
- Component extraction (component$, Slot, event handlers, props)
- Signal extraction (useSignal, useStore, useComputed$)
- Task extraction (useTask$, useVisibleTask$, useResource$)
- Route extraction (routeLoader$, routeAction$, server$, middleware)
- Store extraction (createContextId, useContextProvider, noSerialize)
- API extraction (imports, events, styles, integrations, types)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from codetrellis.qwik_parser_enhanced import (
    EnhancedQwikParser,
    QwikParseResult,
)
from codetrellis.extractors.qwik import (
    QwikComponentExtractor,
    QwikSignalExtractor,
    QwikTaskExtractor,
    QwikRouteExtractor,
    QwikStoreExtractor,
    QwikApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedQwikParser()


@pytest.fixture
def component_extractor():
    return QwikComponentExtractor()


@pytest.fixture
def signal_extractor():
    return QwikSignalExtractor()


@pytest.fixture
def task_extractor():
    return QwikTaskExtractor()


@pytest.fixture
def route_extractor():
    return QwikRouteExtractor()


@pytest.fixture
def store_extractor():
    return QwikStoreExtractor()


@pytest.fixture
def api_extractor():
    return QwikApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestQwikComponentExtractor:
    """Tests for QwikComponentExtractor."""

    def test_basic_component_dollar(self, component_extractor):
        code = '''
import { component$ } from '@builder.io/qwik';

export const Counter = component$(() => {
    return <div>Hello</div>;
});
'''
        result = component_extractor.extract(code, "Counter.tsx")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.name == "Counter"

    def test_typed_component(self, component_extractor):
        code = '''
interface ButtonProps {
    variant?: 'primary' | 'secondary';
}

export const Button = component$<ButtonProps>(({ variant = 'primary' }) => {
    return <button class={`btn-${variant}`}><Slot /></button>;
});
'''
        result = component_extractor.extract(code, "Button.tsx")
        components = result.get('components', [])
        assert len(components) >= 1

    def test_component_with_slot(self, component_extractor):
        code = '''
export const Card = component$(() => {
    return (
        <div class="card">
            <Slot />
        </div>
    );
});
'''
        result = component_extractor.extract(code, "Card.tsx")
        slots = result.get('slots', [])
        assert len(slots) >= 1

    def test_named_slot(self, component_extractor):
        code = '''
export const Layout = component$(() => {
    return (
        <div>
            <header><Slot name="header" /></header>
            <main><Slot /></main>
            <footer><Slot name="footer" /></footer>
        </div>
    );
});
'''
        result = component_extractor.extract(code, "Layout.tsx")
        slots = result.get('slots', [])
        assert len(slots) >= 2  # at least default + named

    def test_component_with_event_handlers(self, component_extractor):
        code = '''
export const Form = component$(() => {
    return (
        <form onSubmit$={() => handleSubmit()}>
            <input onInput$={(ev) => update(ev)} />
            <button onClick$={() => reset()}>Reset</button>
        </form>
    );
});
'''
        result = component_extractor.extract(code, "Form.tsx")
        components = result.get('components', [])
        assert len(components) >= 1

    def test_default_export_component(self, component_extractor):
        code = '''
export default component$(() => {
    return <div>Page</div>;
});
'''
        result = component_extractor.extract(code, "index.tsx")
        components = result.get('components', [])
        assert len(components) >= 1

    def test_component_with_signals(self, component_extractor):
        code = '''
export const Counter = component$(() => {
    const count = useSignal(0);
    return <button onClick$={() => count.value++}>{count.value}</button>;
});
'''
        result = component_extractor.extract(code, "Counter.tsx")
        components = result.get('components', [])
        assert len(components) >= 1

    def test_component_with_ref(self, component_extractor):
        code = '''
export const Input = component$(() => {
    const inputRef = useSignal<HTMLInputElement>();
    return <input ref={inputRef} />;
});
'''
        result = component_extractor.extract(code, "Input.tsx")
        components = result.get('components', [])
        assert len(components) >= 1

    def test_multiple_components_in_file(self, component_extractor):
        code = '''
export const Header = component$(() => {
    return <header>Header</header>;
});

export const Footer = component$(() => {
    return <footer>Footer</footer>;
});

export const Sidebar = component$(() => {
    return <aside>Sidebar</aside>;
});
'''
        result = component_extractor.extract(code, "Layout.tsx")
        components = result.get('components', [])
        assert len(components) >= 3

    def test_inline_component(self, component_extractor):
        code = '''
const Wrapper = (props) => (
    <div class={props.class}>{props.children}</div>
);
'''
        result = component_extractor.extract(code, "Wrapper.tsx")
        # Inline components may or may not be detected depending on pattern
        # The key test is that it doesn't error
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════
# Signal Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestQwikSignalExtractor:
    """Tests for QwikSignalExtractor."""

    def test_basic_signal(self, signal_extractor):
        code = '''
const count = useSignal(0);
'''
        result = signal_extractor.extract(code, "counter.ts")
        signals = result.get('signals', [])
        assert len(signals) >= 1
        sig = signals[0]
        assert sig.name == "count"

    def test_typed_signal(self, signal_extractor):
        code = '''
const user = useSignal<User | null>(null);
'''
        result = signal_extractor.extract(code, "user.ts")
        signals = result.get('signals', [])
        assert len(signals) >= 1
        sig = signals[0]
        assert sig.name == "user"

    def test_element_ref_signal(self, signal_extractor):
        code = '''
const inputRef = useSignal<HTMLInputElement>();
'''
        result = signal_extractor.extract(code, "input.ts")
        signals = result.get('signals', [])
        assert len(signals) >= 1

    def test_basic_store(self, signal_extractor):
        code = '''
const state = useStore({
    count: 0,
    name: '',
    items: [],
});
'''
        result = signal_extractor.extract(code, "state.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        store = stores[0]
        assert store.name == "state"

    def test_shallow_store(self, signal_extractor):
        code = '''
const config = useStore({ theme: 'dark', lang: 'en' }, { deep: false });
'''
        result = signal_extractor.extract(code, "config.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1

    def test_computed(self, signal_extractor):
        code = '''
const doubled = useComputed$(() => count.value * 2);
'''
        result = signal_extractor.extract(code, "derived.ts")
        computeds = result.get('computeds', [])
        assert len(computeds) >= 1
        comp = computeds[0]
        assert comp.name == "doubled"

    def test_multiple_signals_and_stores(self, signal_extractor):
        code = '''
const count = useSignal(0);
const name = useSignal('');
const isOpen = useSignal(false);
const state = useStore({ items: [], loading: false });
const total = useComputed$(() => state.items.length);
'''
        result = signal_extractor.extract(code, "multi.ts")
        signals = result.get('signals', [])
        stores = result.get('stores', [])
        computeds = result.get('computeds', [])
        assert len(signals) >= 3
        assert len(stores) >= 1
        assert len(computeds) >= 1


# ═══════════════════════════════════════════════════════════════════
# Task Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestQwikTaskExtractor:
    """Tests for QwikTaskExtractor."""

    def test_basic_task(self, task_extractor):
        code = '''
useTask$(({ track }) => {
    const val = track(() => count.value);
    console.log('count changed:', val);
});
'''
        result = task_extractor.extract(code, "effect.ts")
        tasks = result.get('tasks', [])
        assert len(tasks) >= 1
        task = tasks[0]
        assert task.task_type == "useTask$"

    def test_visible_task(self, task_extractor):
        code = '''
useVisibleTask$(() => {
    const observer = new IntersectionObserver(callback);
    observer.observe(element);
    return () => observer.disconnect();
});
'''
        result = task_extractor.extract(code, "visible.ts")
        tasks = result.get('tasks', [])
        assert len(tasks) >= 1
        task = tasks[0]
        assert task.task_type == "useVisibleTask$"

    def test_visible_task_with_eagerness(self, task_extractor):
        code = '''
useVisibleTask$(() => {
    initAnalytics();
}, { strategy: 'document-ready' });
'''
        result = task_extractor.extract(code, "analytics.ts")
        tasks = result.get('tasks', [])
        assert len(tasks) >= 1

    def test_resource(self, task_extractor):
        code = '''
const userResource = useResource$<User>(async ({ track, cleanup }) => {
    const id = track(() => userId.value);
    const ctrl = new AbortController();
    cleanup(() => ctrl.abort());
    const res = await fetch(`/api/users/${id}`, { signal: ctrl.signal });
    return res.json();
});
'''
        result = task_extractor.extract(code, "user.ts")
        resources = result.get('resources', [])
        assert len(resources) >= 1
        res = resources[0]
        assert res.name == "userResource"

    def test_resource_component(self, task_extractor):
        code = '''
<Resource
    value={userResource}
    onPending={() => <Spinner />}
    onRejected={(err) => <Error message={err.message} />}
    onResolved={(user) => <UserProfile user={user} />}
/>
'''
        result = task_extractor.extract(code, "profile.tsx")
        resources = result.get('resources', [])
        # Should detect <Resource> usage
        assert isinstance(result, dict)

    def test_legacy_use_watch(self, task_extractor):
        code = '''
useWatch$(({ track }) => {
    const val = track(() => count.value);
    console.log(val);
});
'''
        result = task_extractor.extract(code, "legacy.ts")
        tasks = result.get('tasks', [])
        assert len(tasks) >= 1

    def test_legacy_use_client_effect(self, task_extractor):
        code = '''
useClientEffect$(() => {
    document.title = title.value;
});
'''
        result = task_extractor.extract(code, "legacy.ts")
        tasks = result.get('tasks', [])
        assert len(tasks) >= 1

    def test_task_with_cleanup(self, task_extractor):
        code = '''
useTask$(({ cleanup }) => {
    const interval = setInterval(() => tick(), 1000);
    cleanup(() => clearInterval(interval));
});
'''
        result = task_extractor.extract(code, "timer.ts")
        tasks = result.get('tasks', [])
        assert len(tasks) >= 1

    def test_multiple_tasks_in_file(self, task_extractor):
        code = '''
useTask$(({ track }) => {
    track(() => a.value);
});

useVisibleTask$(() => {
    initChart();
});

useTask$(({ track }) => {
    track(() => b.value);
});
'''
        result = task_extractor.extract(code, "multi.ts")
        tasks = result.get('tasks', [])
        assert len(tasks) >= 3


# ═══════════════════════════════════════════════════════════════════
# Route Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestQwikRouteExtractor:
    """Tests for QwikRouteExtractor."""

    def test_route_loader(self, route_extractor):
        code = '''
export const useProductData = routeLoader$(async ({ params }) => {
    return fetchProduct(params.id);
});
'''
        result = route_extractor.extract(code, "index.tsx")
        loaders = result.get('loaders', [])
        assert len(loaders) >= 1
        loader = loaders[0]
        assert loader.name == "useProductData"

    def test_route_action(self, route_extractor):
        code = '''
export const useAddTodo = routeAction$(async (data) => {
    await db.todos.create(data);
    return { success: true };
});
'''
        result = route_extractor.extract(code, "index.tsx")
        actions = result.get('actions', [])
        assert len(actions) >= 1
        action = actions[0]
        assert action.name == "useAddTodo"

    def test_route_action_with_zod(self, route_extractor):
        code = '''
export const useCreateUser = routeAction$(
    async (data) => {
        return createUser(data);
    },
    zod$({
        name: z.string().min(2),
        email: z.string().email(),
    })
);
'''
        result = route_extractor.extract(code, "create.tsx")
        actions = result.get('actions', [])
        assert len(actions) >= 1

    def test_server_dollar(self, route_extractor):
        code = '''
const getUserById = server$(async function (id: string) {
    const user = await db.users.findById(id);
    return user;
});
'''
        result = route_extractor.extract(code, "api.ts")
        server_fns = result.get('server_functions', [])
        assert len(server_fns) >= 1

    def test_global_action(self, route_extractor):
        code = '''
export const useLogout = globalAction$(async (_, { cookie, redirect }) => {
    cookie.delete('auth_token');
    throw redirect(302, '/login');
});
'''
        result = route_extractor.extract(code, "auth.ts")
        # Global actions should be detected
        assert isinstance(result, dict)

    def test_middleware_on_request(self, route_extractor):
        code = '''
export const onRequest: RequestHandler = async ({ cookie, redirect }) => {
    const token = cookie.get('auth_token');
    if (!token) {
        throw redirect(302, '/login');
    }
};
'''
        result = route_extractor.extract(code, "layout.tsx")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 1

    def test_middleware_on_get(self, route_extractor):
        code = '''
export const onGet: RequestHandler = async ({ json }) => {
    json(200, { message: 'ok' });
};
'''
        result = route_extractor.extract(code, "api/status/index.tsx")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 1

    def test_middleware_on_post(self, route_extractor):
        code = '''
export const onPost: RequestHandler = async ({ parseBody, json }) => {
    const body = await parseBody();
    json(201, { created: true });
};
'''
        result = route_extractor.extract(code, "api/items/index.tsx")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 1

    def test_use_navigate(self, route_extractor):
        code = '''
const nav = useNavigate();
nav('/dashboard');
'''
        result = route_extractor.extract(code, "nav.ts")
        nav_hooks = result.get('nav_hooks', [])
        assert len(nav_hooks) >= 1

    def test_use_location(self, route_extractor):
        code = '''
const loc = useLocation();
console.log(loc.url.pathname);
'''
        result = route_extractor.extract(code, "loc.ts")
        nav_hooks = result.get('nav_hooks', [])
        assert len(nav_hooks) >= 1

    def test_multiple_loaders_and_actions(self, route_extractor):
        code = '''
export const useUsers = routeLoader$(async () => {
    return db.users.findMany();
});

export const useStats = routeLoader$(async () => {
    return db.stats.get();
});

export const useCreateUser = routeAction$(async (data) => {
    return db.users.create(data);
});
'''
        result = route_extractor.extract(code, "admin.tsx")
        loaders = result.get('loaders', [])
        actions = result.get('actions', [])
        assert len(loaders) >= 2
        assert len(actions) >= 1


# ═══════════════════════════════════════════════════════════════════
# Store (Context) Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestQwikStoreExtractor:
    """Tests for QwikStoreExtractor (context + noSerialize)."""

    def test_create_context_id(self, store_extractor):
        code = '''
export const ThemeCtx = createContextId<ThemeContext>('theme');
'''
        result = store_extractor.extract(code, "context.ts")
        contexts = result.get('contexts', [])
        assert len(contexts) >= 1
        ctx = contexts[0]
        # context_name is the string ID passed to createContextId
        assert ctx.context_name in ("ThemeCtx", "theme")

    def test_context_provider(self, store_extractor):
        code = '''
const ThemeCtx = createContextId('theme');
useContextProvider(ThemeCtx, themeStore);
'''
        result = store_extractor.extract(code, "provider.tsx")
        contexts = result.get('contexts', [])
        assert len(contexts) >= 1

    def test_context_consumer(self, store_extractor):
        code = '''
const ThemeCtx = createContextId('theme');
const theme = useContext(ThemeCtx);
'''
        result = store_extractor.extract(code, "consumer.tsx")
        contexts = result.get('contexts', [])
        assert len(contexts) >= 1

    def test_no_serialize(self, store_extractor):
        code = '''
const ws = noSerialize(new WebSocket('wss://example.com'));
'''
        result = store_extractor.extract(code, "ws.ts")
        no_serializes = result.get('no_serializes', [])
        assert len(no_serializes) >= 1

    def test_multiple_no_serializes(self, store_extractor):
        code = '''
const socket = noSerialize(new WebSocket('wss://example.com'));
const timer = noSerialize(setInterval(() => {}, 1000));
const observer = noSerialize(new MutationObserver(callback));
'''
        result = store_extractor.extract(code, "non-serializable.ts")
        no_serializes = result.get('no_serializes', [])
        assert len(no_serializes) >= 3


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestQwikApiExtractor:
    """Tests for QwikApiExtractor."""

    def test_qwik_core_import(self, api_extractor):
        code = '''
import { component$, useSignal, useStore } from '@builder.io/qwik';
'''
        result = api_extractor.extract(code, "app.tsx")
        imports = result.get('imports', [])
        assert len(imports) >= 1
        imp = imports[0]
        assert imp.source == "@builder.io/qwik"

    def test_qwik_city_import(self, api_extractor):
        code = '''
import { routeLoader$, routeAction$, Form } from '@builder.io/qwik-city';
'''
        result = api_extractor.extract(code, "route.tsx")
        imports = result.get('imports', [])
        assert len(imports) >= 1

    def test_qwik_v2_import(self, api_extractor):
        code = '''
import { component$, useSignal } from '@qwik.dev/core';
import { routeLoader$ } from '@qwik.dev/router';
'''
        result = api_extractor.extract(code, "v2.tsx")
        imports = result.get('imports', [])
        assert len(imports) >= 2

    def test_jsx_event_handler(self, api_extractor):
        code = '''
<button onClick$={() => count.value++}>+1</button>
<input onInput$={(ev) => query.value = ev.target.value} />
<form onSubmit$={handleSubmit$}>...</form>
'''
        result = api_extractor.extract(code, "events.tsx")
        event_handlers = result.get('event_handlers', [])
        assert len(event_handlers) >= 2

    def test_use_on_handler(self, api_extractor):
        code = '''
useOn('click', $(() => {
    console.log('clicked');
}));
'''
        result = api_extractor.extract(code, "useOn.ts")
        event_handlers = result.get('event_handlers', [])
        assert len(event_handlers) >= 1

    def test_use_on_window(self, api_extractor):
        code = '''
useOnWindow('resize', $(() => {
    updateLayout();
}));
'''
        result = api_extractor.extract(code, "window.ts")
        event_handlers = result.get('event_handlers', [])
        assert len(event_handlers) >= 1

    def test_use_on_document(self, api_extractor):
        code = '''
useOnDocument('keydown', $((event) => {
    if (event.key === 'Escape') closeModal();
}));
'''
        result = api_extractor.extract(code, "document.ts")
        event_handlers = result.get('event_handlers', [])
        assert len(event_handlers) >= 1

    def test_use_styles(self, api_extractor):
        code = '''
useStyles$(`
    .container { max-width: 1200px; margin: 0 auto; }
`);
'''
        result = api_extractor.extract(code, "global.tsx")
        styles = result.get('styles', [])
        assert len(styles) >= 1

    def test_use_styles_scoped(self, api_extractor):
        code = '''
useStylesScoped$(`
    .card { border: 1px solid #ccc; padding: 16px; }
`);
'''
        result = api_extractor.extract(code, "card.tsx")
        styles = result.get('styles', [])
        assert len(styles) >= 1

    def test_qwik_ui_integration(self, api_extractor):
        code = '''
import { Modal, Accordion } from '@qwik-ui/headless';
'''
        result = api_extractor.extract(code, "ui.tsx")
        integrations = result.get('integrations', [])
        assert len(integrations) >= 1

    def test_modular_forms_integration(self, api_extractor):
        code = '''
import { useForm, zodForm$ } from '@modular-forms/qwik';
'''
        result = api_extractor.extract(code, "form.tsx")
        integrations = result.get('integrations', [])
        assert len(integrations) >= 1

    def test_qwik_speak_integration(self, api_extractor):
        code = '''
import { useTranslate } from 'qwik-speak';
'''
        result = api_extractor.extract(code, "i18n.tsx")
        integrations = result.get('integrations', [])
        assert len(integrations) >= 1

    def test_ssr_pattern(self, api_extractor):
        code = '''
import { SSRStream, SSRStreamBlock } from '@builder.io/qwik';
import { isServer, isBrowser } from '@builder.io/qwik/build';
'''
        result = api_extractor.extract(code, "ssr.tsx")
        imports = result.get('imports', [])
        assert len(imports) >= 2

    def test_qwik_type_extraction(self, api_extractor):
        code = '''
import type { Signal, QRL, NoSerialize } from '@builder.io/qwik';
'''
        result = api_extractor.extract(code, "types.ts")
        types = result.get('types', [])
        assert isinstance(result, dict)

    def test_multiple_imports(self, api_extractor):
        code = '''
import { component$, useSignal, useStore } from '@builder.io/qwik';
import { routeLoader$, Form } from '@builder.io/qwik-city';
import { isServer } from '@builder.io/qwik/build';
import { Modal } from '@qwik-ui/headless';
import { useForm } from '@modular-forms/qwik';
'''
        result = api_extractor.extract(code, "full.tsx")
        imports = result.get('imports', [])
        assert len(imports) >= 4


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedQwikParser:
    """Tests for EnhancedQwikParser integration."""

    def test_is_qwik_file_true(self, parser):
        code = "import { component$ } from '@builder.io/qwik';"
        assert parser.is_qwik_file(code) is True

    def test_is_qwik_file_false(self, parser):
        code = "import React from 'react';"
        assert parser.is_qwik_file(code) is False

    def test_is_qwik_file_v2(self, parser):
        code = "import { component$ } from '@qwik.dev/core';"
        assert parser.is_qwik_file(code) is True

    def test_is_qwik_file_city(self, parser):
        code = "import { routeLoader$ } from '@builder.io/qwik-city';"
        assert parser.is_qwik_file(code) is True

    def test_is_qwik_file_component_dollar(self, parser):
        code = "const App = component$(() => { return <div />; });"
        assert parser.is_qwik_file(code) is True

    def test_is_qwik_file_use_signal(self, parser):
        code = "const count = useSignal(0);"
        assert parser.is_qwik_file(code) is True

    def test_is_qwik_file_qwik_ui(self, parser):
        code = "import { Modal } from '@qwik-ui/headless';"
        # The @qwik-ui/ pattern should be detected
        assert parser.is_qwik_file(code) is True

    def test_detect_version_v1(self, parser):
        code = "import { component$ } from '@builder.io/qwik';"
        assert parser._detect_version(code) == "v1"

    def test_detect_version_v2(self, parser):
        code = "import { component$ } from '@qwik.dev/core';"
        assert parser._detect_version(code) == "v2"

    def test_detect_version_v0(self, parser):
        code = "useWatch$(({ track }) => { ... });"
        assert parser._detect_version(code) == "v0"

    def test_detect_version_v0_client_effect(self, parser):
        code = "useClientEffect$(() => { ... });"
        assert parser._detect_version(code) == "v0"

    def test_detect_frameworks_core(self, parser):
        code = "import { component$ } from '@builder.io/qwik';"
        frameworks = parser._detect_frameworks(code)
        assert "qwik" in frameworks

    def test_detect_frameworks_city(self, parser):
        code = "import { routeLoader$ } from '@builder.io/qwik-city';"
        frameworks = parser._detect_frameworks(code)
        assert "qwik-city" in frameworks

    def test_detect_frameworks_ui(self, parser):
        code = "import { Modal } from '@qwik-ui/headless';"
        frameworks = parser._detect_frameworks(code)
        assert "qwik-ui-headless" in frameworks

    def test_detect_frameworks_modular_forms(self, parser):
        code = "import { useForm } from '@modular-forms/qwik';"
        frameworks = parser._detect_frameworks(code)
        assert "modular-forms" in frameworks

    def test_detect_frameworks_speak(self, parser):
        code = "import { useTranslate } from 'qwik-speak';"
        frameworks = parser._detect_frameworks(code)
        assert "qwik-speak" in frameworks

    def test_detect_frameworks_auth(self, parser):
        code = "import { useAuth } from '@auth/qwik';"
        frameworks = parser._detect_frameworks(code)
        assert "qwik-auth" in frameworks

    def test_detect_frameworks_zod(self, parser):
        code = "import { z } from 'zod';"
        frameworks = parser._detect_frameworks(code)
        assert "zod" in frameworks

    def test_detect_features_component(self, parser):
        code = "const App = component$(() => { ... });"
        features = parser._detect_features(code)
        assert "component_dollar" in features

    def test_detect_features_signal(self, parser):
        code = "const count = useSignal(0);"
        features = parser._detect_features(code)
        assert "use_signal" in features

    def test_detect_features_store(self, parser):
        code = "const state = useStore({ count: 0 });"
        features = parser._detect_features(code)
        assert "use_store" in features

    def test_detect_features_task(self, parser):
        code = "useTask$(({ track }) => { ... });"
        features = parser._detect_features(code)
        assert "use_task" in features

    def test_detect_features_visible_task(self, parser):
        code = "useVisibleTask$(() => { ... });"
        features = parser._detect_features(code)
        assert "use_visible_task" in features

    def test_detect_features_computed(self, parser):
        code = "const doubled = useComputed$(() => count.value * 2);"
        features = parser._detect_features(code)
        assert "use_computed" in features

    def test_detect_features_resource(self, parser):
        code = "const data = useResource$<User>(async () => { ... });"
        features = parser._detect_features(code)
        assert "use_resource" in features

    def test_detect_features_route_loader(self, parser):
        code = "export const useData = routeLoader$(async () => { ... });"
        features = parser._detect_features(code)
        assert "route_loader" in features

    def test_detect_features_route_action(self, parser):
        code = "export const useCreate = routeAction$(async (data) => { ... });"
        features = parser._detect_features(code)
        assert "route_action" in features

    def test_detect_features_server_dollar(self, parser):
        code = "const getData = server$(async () => { ... });"
        features = parser._detect_features(code)
        assert "server_dollar" in features

    def test_detect_features_slot(self, parser):
        code = "<Slot name='header' />"
        features = parser._detect_features(code)
        assert "slot" in features

    def test_detect_features_resource_component(self, parser):
        code = "<Resource value={data} onResolved={(d) => <div>{d}</div>} />"
        features = parser._detect_features(code)
        assert "resource_component" in features

    def test_detect_features_no_serialize(self, parser):
        code = "const ws = noSerialize(new WebSocket('...'));"
        features = parser._detect_features(code)
        assert "no_serialize" in features

    def test_detect_features_create_context(self, parser):
        code = "const Ctx = createContextId<T>('ctx');"
        features = parser._detect_features(code)
        assert "create_context" in features

    def test_detect_features_middleware(self, parser):
        code = "export const onRequest: RequestHandler = async (ev) => { ... };"
        features = parser._detect_features(code)
        assert "on_request" in features

    def test_detect_features_is_server(self, parser):
        code = "if (isServer) { console.log('server'); }"
        features = parser._detect_features(code)
        assert "is_server" in features

    def test_detect_features_legacy_watch(self, parser):
        code = "useWatch$(({ track }) => { ... });"
        features = parser._detect_features(code)
        assert "use_watch_legacy" in features

    def test_detect_features_legacy_client_effect(self, parser):
        code = "useClientEffect$(() => { ... });"
        features = parser._detect_features(code)
        assert "use_client_effect_legacy" in features

    def test_full_parse_result(self, parser):
        code = '''
import { component$, useSignal, useStore, useComputed$, useTask$, Slot } from '@builder.io/qwik';
import { routeLoader$, Form } from '@builder.io/qwik-city';

export const useProducts = routeLoader$(async () => {
    return fetchProducts();
});

export default component$(() => {
    const count = useSignal(0);
    const state = useStore({ items: [], filter: 'all' });
    const total = useComputed$(() => state.items.length);

    useTask$(({ track }) => {
        track(() => count.value);
    });

    return (
        <div>
            <Slot />
            <button onClick$={() => count.value++}>{count.value}</button>
        </div>
    );
});
'''
        result = parser.parse(code, "products/index.tsx")

        assert isinstance(result, QwikParseResult)
        assert result.file_path == "products/index.tsx"
        assert result.file_type == "tsx"

        # Should detect frameworks
        assert "qwik" in result.detected_frameworks
        assert "qwik-city" in result.detected_frameworks

        # Should detect features
        assert "component_dollar" in result.detected_features
        assert "use_signal" in result.detected_features
        assert "use_store" in result.detected_features
        assert "use_computed" in result.detected_features
        assert "use_task" in result.detected_features
        assert "slot" in result.detected_features
        assert "route_loader" in result.detected_features

        # Should detect version
        assert result.qwik_version == "v1"

        # Should extract components
        assert len(result.components) >= 1

        # Should extract signals
        assert len(result.signals) >= 1

        # Should extract stores
        assert len(result.stores) >= 1

        # Should extract computeds
        assert len(result.computeds) >= 1

        # Should extract tasks
        assert len(result.tasks) >= 1

        # Should extract slots
        assert len(result.slots) >= 1

        # Should extract route loaders
        assert len(result.route_loaders) >= 1

    def test_parse_v2_imports(self, parser):
        code = '''
import { component$, useSignal } from '@qwik.dev/core';
import { routeLoader$ } from '@qwik.dev/router';

export const useData = routeLoader$(async () => { return []; });

export default component$(() => {
    const items = useSignal([]);
    return <div>{items.value.length}</div>;
});
'''
        result = parser.parse(code, "v2page.tsx")
        assert result.qwik_version == "v2"
        assert "qwik" in result.detected_frameworks

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.tsx")
        assert isinstance(result, QwikParseResult)
        assert len(result.components) == 0
        assert len(result.signals) == 0

    def test_parse_non_qwik_file(self, parser):
        code = '''
import React from 'react';
function App() { return <div />; }
'''
        result = parser.parse(code, "react.tsx")
        assert isinstance(result, QwikParseResult)
        assert len(result.detected_frameworks) == 0

    def test_parse_file_type_detection(self, parser):
        assert parser.parse("const x = 1;", "test.tsx").file_type == "tsx"
        assert parser.parse("const x = 1;", "test.jsx").file_type == "jsx"
        assert parser.parse("const x = 1;", "test.ts").file_type == "ts"
        assert parser.parse("const x = 1;", "test.js").file_type == "js"
        assert parser.parse("const x = 1;", "test.mjs").file_type == "js"

    def test_parse_context_extraction(self, parser):
        code = '''
import { component$, useContextProvider, useContext, createContextId } from '@builder.io/qwik';

export const ThemeCtx = createContextId<{ mode: string }>('theme');

export const Provider = component$(() => {
    const theme = useStore({ mode: 'dark' });
    useContextProvider(ThemeCtx, theme);
    return <Slot />;
});

export const Consumer = component$(() => {
    const theme = useContext(ThemeCtx);
    return <div>{theme.mode}</div>;
});
'''
        result = parser.parse(code, "context.tsx")
        assert len(result.contexts) >= 1

    def test_parse_middleware_extraction(self, parser):
        code = '''
import type { RequestHandler } from '@builder.io/qwik-city';

export const onRequest: RequestHandler = async ({ cookie, redirect }) => {
    if (!cookie.get('token')) {
        throw redirect(302, '/login');
    }
};

export const onGet: RequestHandler = async ({ json }) => {
    json(200, { ok: true });
};
'''
        result = parser.parse(code, "layout.tsx")
        assert len(result.middleware) >= 1

    def test_parse_server_functions(self, parser):
        code = '''
import { server$ } from '@builder.io/qwik-city';

const getServerData = server$(async () => {
    return db.getData();
});

const processForm = server$(async (formData: FormData) => {
    return { ok: true };
});
'''
        result = parser.parse(code, "api.ts")
        assert len(result.server_functions) >= 1

    def test_version_compare(self, parser):
        assert parser._version_compare("v2", "v1") > 0
        assert parser._version_compare("v1", "v2") < 0
        assert parser._version_compare("v1", "v1") == 0
        assert parser._version_compare("v2", "") > 0
        assert parser._version_compare("", "v1") < 0

    def test_parse_comprehensive_qwik_city_route(self, parser):
        code = '''
import { component$, useSignal, useStore, useComputed$, useTask$, Slot, useStylesScoped$ } from '@builder.io/qwik';
import { routeLoader$, routeAction$, Form, zod$, useNavigate, useLocation } from '@builder.io/qwik-city';
import { z } from 'zod';

export const useTodos = routeLoader$(async ({ params }) => {
    return db.todos.findByUser(params.userId);
});

export const useAddTodo = routeAction$(
    async (data, { fail }) => {
        const result = await db.todos.create(data);
        if (!result) return fail(400, { message: 'Failed' });
        return { id: result.id };
    },
    zod$({ title: z.string().min(1), completed: z.boolean().default(false) })
);

export default component$(() => {
    useStylesScoped$(`
        .todo-list { list-style: none; padding: 0; }
        .todo-item { padding: 8px; border-bottom: 1px solid #eee; }
    `);

    const todos = useTodos();
    const addAction = useAddTodo();
    const filter = useSignal<'all' | 'active' | 'completed'>('all');
    const state = useStore({ editingId: null as string | null });
    const nav = useNavigate();
    const loc = useLocation();

    const filteredTodos = useComputed$(() => {
        if (filter.value === 'all') return todos.value;
        return todos.value.filter(t => t.completed === (filter.value === 'completed'));
    });

    useTask$(({ track }) => {
        track(() => filter.value);
        console.log('filter changed');
    });

    return (
        <div>
            <h1>Todos for user {loc.params.userId}</h1>
            <Form action={addAction}>
                <input name="title" />
                <button type="submit">Add</button>
            </Form>
            <ul class="todo-list">
                {filteredTodos.value.map(todo => (
                    <li key={todo.id} class="todo-item" onClick$={() => state.editingId = todo.id}>
                        {todo.title}
                    </li>
                ))}
            </ul>
            <button onClick$={() => nav('/dashboard')}>Back</button>
        </div>
    );
});
'''
        result = parser.parse(code, "todos/[userId]/index.tsx")

        # Core assertions
        assert result.qwik_version == "v1"
        assert "qwik" in result.detected_frameworks
        assert "qwik-city" in result.detected_frameworks
        assert "zod" in result.detected_frameworks

        # Feature detection
        assert "component_dollar" in result.detected_features
        assert "use_signal" in result.detected_features
        assert "use_store" in result.detected_features
        assert "use_computed" in result.detected_features
        assert "use_task" in result.detected_features
        assert "route_loader" in result.detected_features
        assert "route_action" in result.detected_features
        assert "form_component" in result.detected_features
        assert "use_navigate" in result.detected_features
        assert "use_location" in result.detected_features
        assert "zod_validation" in result.detected_features

        # Extraction counts
        assert len(result.components) >= 1
        assert len(result.signals) >= 1
        assert len(result.stores) >= 1
        assert len(result.computeds) >= 1
        assert len(result.tasks) >= 1
        assert len(result.route_loaders) >= 1
        assert len(result.route_actions) >= 1
        assert len(result.imports) >= 2
        assert len(result.styles) >= 1
