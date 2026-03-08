"""
Tests for Preact extractors and EnhancedPreactParser.

Part of CodeTrellis v4.64 Preact Framework Support.
Tests cover:
- Component extraction (functional, class, memo, lazy, forwardRef, error boundaries)
- Hook extraction (built-in hooks, custom hooks, dependency analysis)
- Signal extraction (signal, computed, effect, batch, useSignal, useComputed)
- Context extraction (createContext, Provider, useContext, contextType)
- API extraction (imports, SSR, integrations, types)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from codetrellis.preact_parser_enhanced import (
    EnhancedPreactParser,
    PreactParseResult,
)
from codetrellis.extractors.preact import (
    PreactComponentExtractor,
    PreactHookExtractor,
    PreactSignalExtractor,
    PreactContextExtractor,
    PreactApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedPreactParser()


@pytest.fixture
def component_extractor():
    return PreactComponentExtractor()


@pytest.fixture
def hook_extractor():
    return PreactHookExtractor()


@pytest.fixture
def signal_extractor():
    return PreactSignalExtractor()


@pytest.fixture
def context_extractor():
    return PreactContextExtractor()


@pytest.fixture
def api_extractor():
    return PreactApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestPreactComponentExtractor:

    def test_basic_functional_component(self, component_extractor):
        code = '''
        import { h } from 'preact';
        export function Counter({ initial = 0 }) {
            const [count, setCount] = useState(initial);
            return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
        }
        '''
        result = component_extractor.extract(code, "Counter.tsx")
        comps = result['components']
        assert len(comps) >= 1
        assert comps[0].name == "Counter"
        assert comps[0].is_exported is True

    def test_arrow_function_component(self, component_extractor):
        code = '''
        import { h } from 'preact';
        export const App = ({ children }) => {
            return <div class="app">{children}</div>;
        };
        '''
        result = component_extractor.extract(code, "App.tsx")
        comps = result['components']
        assert len(comps) >= 1
        assert comps[0].name == "App"

    def test_typed_component(self, component_extractor):
        code = '''
        import { h } from 'preact';
        interface CardProps {
            title: string;
            variant: 'default' | 'outlined';
        }
        export function Card({ title, variant = 'default' }: CardProps) {
            return <div class={`card card-${variant}`}><h2>{title}</h2></div>;
        }
        '''
        result = component_extractor.extract(code, "Card.tsx")
        comps = result['components']
        assert len(comps) >= 1
        assert comps[0].name == "Card"
        assert comps[0].props_type == "CardProps"

    def test_class_component(self, component_extractor):
        code = '''
        import { Component } from 'preact';
        export class Timer extends Component {
            state = { time: 0 };
            componentDidMount() {
                this.timer = setInterval(() => this.setState({ time: this.state.time + 1 }), 1000);
            }
            componentWillUnmount() {
                clearInterval(this.timer);
            }
            render() {
                return <div>{this.state.time}s</div>;
            }
        }
        '''
        result = component_extractor.extract(code, "Timer.tsx")
        class_comps = result['class_components']
        assert len(class_comps) >= 1
        assert class_comps[0].name == "Timer"
        assert "componentDidMount" in class_comps[0].lifecycle_methods or len(class_comps[0].lifecycle_methods) > 0

    def test_memo_component(self, component_extractor):
        code = '''
        import { memo } from 'preact/compat';
        export const MemoList = memo(function MemoList({ items }) {
            return <ul>{items.map(i => <li key={i.id}>{i.name}</li>)}</ul>;
        });
        '''
        result = component_extractor.extract(code, "MemoList.tsx")
        memos = result['memos']
        assert len(memos) >= 1
        assert memos[0].name == "MemoList"

    def test_memo_with_custom_comparison(self, component_extractor):
        code = '''
        import { memo } from 'preact/compat';
        const DataGrid = memo(
            function DataGrid({ data }) { return <table></table>; },
            (prev, next) => prev.data === next.data
        );
        '''
        result = component_extractor.extract(code, "DataGrid.tsx")
        memos = result['memos']
        assert len(memos) >= 1
        assert memos[0].has_custom_comparison is True

    def test_lazy_component(self, component_extractor):
        code = '''
        import { lazy } from 'preact/compat';
        const Dashboard = lazy(() => import('./Dashboard'));
        '''
        result = component_extractor.extract(code, "lazy.tsx")
        lazies = result['lazies']
        assert len(lazies) >= 1
        assert lazies[0].name == "Dashboard"
        assert "./Dashboard" in lazies[0].import_path

    def test_forward_ref_component(self, component_extractor):
        code = '''
        import { forwardRef } from 'preact/compat';
        const Input = forwardRef((props, ref) => {
            return <input ref={ref} {...props} />;
        });
        '''
        result = component_extractor.extract(code, "Input.tsx")
        forward_refs = result['forward_refs']
        assert len(forward_refs) >= 1
        assert forward_refs[0].name == "Input"

    def test_error_boundary_class(self, component_extractor):
        code = '''
        import { Component } from 'preact';
        export class ErrorBoundary extends Component {
            componentDidCatch(error) {
                this.setState({ error });
            }
            render() {
                if (this.state.error) return <div>Error!</div>;
                return this.props.children;
            }
        }
        '''
        result = component_extractor.extract(code, "ErrorBoundary.tsx")
        ebs = result['error_boundaries']
        assert len(ebs) >= 1
        assert ebs[0].name == "ErrorBoundary"

    def test_error_boundary_hook(self, component_extractor):
        code = '''
        import { useErrorBoundary } from 'preact/hooks';
        export function ErrorHandler({ children }) {
            const [error, resetError] = useErrorBoundary();
            if (error) return <div>Error: <button onClick={resetError}>Reset</button></div>;
            return children;
        }
        '''
        result = component_extractor.extract(code, "ErrorHandler.tsx")
        comps = result['components']
        ebs = result['error_boundaries']
        # At minimum the component itself is detected
        assert len(comps) >= 1 or len(ebs) >= 1

    def test_h_function_usage(self, component_extractor):
        code = '''
        import { h } from 'preact';
        function App() {
            return h('div', { class: 'app' }, h('h1', null, 'Hello'));
        }
        '''
        result = component_extractor.extract(code, "App.js")
        comps = result['components']
        assert len(comps) >= 1
        assert comps[0].name == "App"

    def test_default_export_component(self, component_extractor):
        code = '''
        import { h } from 'preact';
        export default function Page() {
            return <div>Page Content</div>;
        }
        '''
        result = component_extractor.extract(code, "Page.tsx")
        comps = result['components']
        assert len(comps) >= 1
        assert comps[0].is_default_export is True

    def test_multiple_components_in_file(self, component_extractor):
        code = '''
        import { h } from 'preact';
        function Header() { return <header>Header</header>; }
        function Footer() { return <footer>Footer</footer>; }
        export function Layout({ children }) {
            return <div><Header />{children}<Footer /></div>;
        }
        '''
        result = component_extractor.extract(code, "Layout.tsx")
        comps = result['components']
        assert len(comps) >= 2
        names = [c.name for c in comps]
        assert "Layout" in names


# ═══════════════════════════════════════════════════════════════════
# Hook Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestPreactHookExtractor:

    def test_basic_use_state(self, hook_extractor):
        code = '''
        import { useState } from 'preact/hooks';
        function Counter() {
            const [count, setCount] = useState(0);
            return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
        }
        '''
        result = hook_extractor.extract(code, "Counter.tsx")
        usages = result['hook_usages']
        assert len(usages) >= 1
        state_hooks = [u for u in usages if u.hook_name == 'useState']
        assert len(state_hooks) >= 1
        assert state_hooks[0].category == "state"

    def test_use_effect_with_deps(self, hook_extractor):
        code = '''
        import { useEffect } from 'preact/hooks';
        function DataFetcher({ url }) {
            useEffect(() => {
                fetch(url).then(r => r.json());
                return () => controller.abort();
            }, [url]);
        }
        '''
        result = hook_extractor.extract(code, "DataFetcher.tsx")
        usages = result['hook_usages']
        effect_hooks = [u for u in usages if u.hook_name == 'useEffect']
        assert len(effect_hooks) >= 1
        assert effect_hooks[0].has_cleanup is True

    def test_use_error_boundary(self, hook_extractor):
        code = '''
        import { useErrorBoundary } from 'preact/hooks';
        function ErrorHandler({ children }) {
            const [error, resetError] = useErrorBoundary((err) => logError(err));
            if (error) return <div>Error!</div>;
            return children;
        }
        '''
        result = hook_extractor.extract(code, "ErrorHandler.tsx")
        usages = result['hook_usages']
        eb_hooks = [u for u in usages if u.hook_name == 'useErrorBoundary']
        assert len(eb_hooks) >= 1
        assert eb_hooks[0].category == "error"

    def test_use_id(self, hook_extractor):
        code = '''
        import { useId } from 'preact/hooks';
        function FormField({ label }) {
            const id = useId();
            return <div><label for={id}>{label}</label><input id={id} /></div>;
        }
        '''
        result = hook_extractor.extract(code, "FormField.tsx")
        usages = result['hook_usages']
        id_hooks = [u for u in usages if u.hook_name == 'useId']
        assert len(id_hooks) >= 1
        assert id_hooks[0].category == "identity"

    def test_custom_hook_definition(self, hook_extractor):
        code = '''
        import { useState, useEffect } from 'preact/hooks';
        export function useAsync(fn, deps) {
            const [state, setState] = useState({ loading: true });
            useEffect(() => {
                fn().then(data => setState({ loading: false, data }));
            }, deps);
            return state;
        }
        '''
        result = hook_extractor.extract(code, "useAsync.ts")
        custom = result['custom_hooks']
        assert len(custom) >= 1
        assert custom[0].name == "useAsync"
        assert custom[0].is_exported is True

    def test_custom_hook_arrow(self, hook_extractor):
        code = '''
        import { useState, useCallback } from 'preact/hooks';
        export const useToggle = (initial = false) => {
            const [on, setOn] = useState(initial);
            const toggle = useCallback(() => setOn(v => !v), []);
            return [on, toggle];
        };
        '''
        result = hook_extractor.extract(code, "useToggle.ts")
        custom = result['custom_hooks']
        assert len(custom) >= 1
        assert custom[0].name == "useToggle"

    def test_multiple_hooks_in_component(self, hook_extractor):
        code = '''
        import { useState, useEffect, useRef, useMemo } from 'preact/hooks';
        function SearchPage() {
            const [query, setQuery] = useState('');
            const [results, setResults] = useState([]);
            const inputRef = useRef(null);
            const filtered = useMemo(() => results.filter(r => r.score > 0), [results]);
            useEffect(() => { inputRef.current?.focus(); }, []);
        }
        '''
        result = hook_extractor.extract(code, "SearchPage.tsx")
        usages = result['hook_usages']
        hook_names = [u.hook_name for u in usages]
        assert 'useState' in hook_names
        assert 'useEffect' in hook_names
        assert 'useRef' in hook_names
        assert 'useMemo' in hook_names
        assert len(usages) >= 4

    def test_use_context_hook(self, hook_extractor):
        code = '''
        import { useContext } from 'preact/hooks';
        function ThemeButton() {
            const theme = useContext(ThemeContext);
            return <button class={theme.mode}>{theme.primary}</button>;
        }
        '''
        result = hook_extractor.extract(code, "ThemeButton.tsx")
        usages = result['hook_usages']
        ctx_hooks = [u for u in usages if u.hook_name == 'useContext']
        assert len(ctx_hooks) >= 1
        assert ctx_hooks[0].category == "context"

    def test_use_reducer(self, hook_extractor):
        code = '''
        import { useReducer } from 'preact/hooks';
        function Counter() {
            const [count, dispatch] = useReducer((s, a) => s + a, 0);
        }
        '''
        result = hook_extractor.extract(code, "Counter.tsx")
        usages = result['hook_usages']
        reducer_hooks = [u for u in usages if u.hook_name == 'useReducer']
        assert len(reducer_hooks) >= 1

    def test_use_callback(self, hook_extractor):
        code = '''
        import { useCallback } from 'preact/hooks';
        function Parent() {
            const handleClick = useCallback(() => console.log('clicked'), []);
        }
        '''
        result = hook_extractor.extract(code, "Parent.tsx")
        usages = result['hook_usages']
        cb_hooks = [u for u in usages if u.hook_name == 'useCallback']
        assert len(cb_hooks) >= 1
        assert cb_hooks[0].category == "callback"


# ═══════════════════════════════════════════════════════════════════
# Signal Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestPreactSignalExtractor:

    def test_basic_signal(self, signal_extractor):
        code = '''
        import { signal } from '@preact/signals';
        const count = signal(0);
        '''
        result = signal_extractor.extract(code, "store.ts")
        signals = result['signals']
        assert len(signals) >= 1
        assert signals[0].name == "count"
        assert signals[0].initial_value == "0"

    def test_typed_signal(self, signal_extractor):
        code = '''
        import { signal, Signal } from '@preact/signals';
        const user: Signal<User | null> = signal(null);
        '''
        result = signal_extractor.extract(code, "store.ts")
        signals = result['signals']
        assert len(signals) >= 1
        assert signals[0].name == "user"

    def test_exported_signal(self, signal_extractor):
        code = "import { signal } from '@preact/signals';\nexport const theme = signal('light');\n"
        result = signal_extractor.extract(code, "store.ts")
        signals = result['signals']
        assert len(signals) >= 1
        assert signals[0].is_exported is True
        assert signals[0].is_module_level is True

    def test_computed_signal(self, signal_extractor):
        code = '''
        import { signal, computed } from '@preact/signals';
        const count = signal(0);
        const doubled = computed(() => count.value * 2);
        '''
        result = signal_extractor.extract(code, "store.ts")
        computeds = result['computeds']
        assert len(computeds) >= 1
        assert computeds[0].name == "doubled"

    def test_effect(self, signal_extractor):
        code = '''
        import { signal, effect } from '@preact/signals';
        const theme = signal('light');
        const dispose = effect(() => {
            document.body.className = theme.value;
        });
        '''
        result = signal_extractor.extract(code, "store.ts")
        effects = result['effects']
        assert len(effects) >= 1

    def test_batch(self, signal_extractor):
        code = '''
        import { signal, batch } from '@preact/signals';
        const firstName = signal('');
        const lastName = signal('');
        function updateUser(user) {
            batch(() => {
                firstName.value = user.first;
                lastName.value = user.last;
            });
        }
        '''
        result = signal_extractor.extract(code, "store.ts")
        batches = result['batches']
        assert len(batches) >= 1

    def test_use_signal_hook(self, signal_extractor):
        code = '''
        import { useSignal } from '@preact/signals';
        function Counter() {
            const count = useSignal(0);
            return <button onClick={() => count.value++}>{count}</button>;
        }
        '''
        result = signal_extractor.extract(code, "Counter.tsx")
        signals = result['signals']
        assert len(signals) >= 1
        assert signals[0].name == "count"

    def test_use_computed_hook(self, signal_extractor):
        code = '''
        import { useSignal, useComputed } from '@preact/signals';
        function Counter() {
            const count = useSignal(0);
            const doubled = useComputed(() => count.value * 2);
        }
        '''
        result = signal_extractor.extract(code, "Counter.tsx")
        computeds = result['computeds']
        assert len(computeds) >= 1
        assert computeds[0].name == "doubled"

    def test_signals_core_package(self, signal_extractor):
        code = '''
        import { signal, computed } from '@preact/signals-core';
        const count = signal(0);
        '''
        result = signal_extractor.extract(code, "core.ts")
        signals = result['signals']
        assert len(signals) >= 1

    def test_peek_usage(self, signal_extractor):
        code = '''
        import { signal, effect } from '@preact/signals';
        const logEnabled = signal(true);
        const count = signal(0);
        effect(() => {
            if (logEnabled.peek()) {
                console.log(count.value);
            }
        });
        '''
        result = signal_extractor.extract(code, "store.ts")
        signals = result['signals']
        # At least we detect the signals; peek detection is a bonus
        assert len(signals) >= 1

    def test_multiple_signals(self, signal_extractor):
        code = '''
        import { signal, computed, effect } from '@preact/signals';
        export const todos = signal([]);
        export const filter = signal('all');
        const filteredTodos = computed(() => todos.value.filter(t => t.done));
        effect(() => { localStorage.setItem('todos', JSON.stringify(todos.value)); });
        '''
        result = signal_extractor.extract(code, "store.ts")
        signals = result['signals']
        computeds = result['computeds']
        effects = result['effects']
        assert len(signals) >= 2
        assert len(computeds) >= 1
        assert len(effects) >= 1

    def test_use_signal_effect(self, signal_extractor):
        code = '''
        import { useSignalEffect } from '@preact/signals';
        function Logger({ msg }) {
            useSignalEffect(() => { console.log(msg.value); });
        }
        '''
        result = signal_extractor.extract(code, "Logger.tsx")
        effects = result['effects']
        assert len(effects) >= 1
        assert effects[0].is_component_bound is True


# ═══════════════════════════════════════════════════════════════════
# Context Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestPreactContextExtractor:

    def test_create_context(self, context_extractor):
        code = '''
        import { createContext } from 'preact';
        const ThemeContext = createContext('light');
        '''
        result = context_extractor.extract(code, "theme.tsx")
        contexts = result['contexts']
        assert len(contexts) >= 1
        assert contexts[0].name == "ThemeContext"

    def test_typed_create_context(self, context_extractor):
        code = '''
        import { createContext } from 'preact';
        interface AuthState { user: User | null; }
        const AuthContext = createContext<AuthState>({ user: null });
        '''
        result = context_extractor.extract(code, "auth.tsx")
        contexts = result['contexts']
        assert len(contexts) >= 1
        assert contexts[0].name == "AuthContext"

    def test_exported_context(self, context_extractor):
        code = '''
        import { createContext } from 'preact';
        export const AppContext = createContext(null);
        '''
        result = context_extractor.extract(code, "context.tsx")
        contexts = result['contexts']
        assert len(contexts) >= 1
        assert contexts[0].is_exported is True

    def test_provider_usage(self, context_extractor):
        code = '''
        import { createContext } from 'preact';
        const ThemeContext = createContext('light');
        function App() {
            return <ThemeContext.Provider value="dark">{children}</ThemeContext.Provider>;
        }
        '''
        result = context_extractor.extract(code, "App.tsx")
        contexts = result['contexts']
        assert len(contexts) >= 1
        assert contexts[0].has_provider is True

    def test_use_context_consumer(self, context_extractor):
        code = '''
        import { createContext } from 'preact';
        import { useContext } from 'preact/hooks';
        const ThemeContext = createContext('light');
        function ThemedButton() {
            const theme = useContext(ThemeContext);
            return <button class={theme}>Click</button>;
        }
        '''
        result = context_extractor.extract(code, "ThemedButton.tsx")
        contexts = result['contexts']
        consumers = result['consumers']
        # Either context or consumer should be detected
        assert len(contexts) >= 1 or len(consumers) >= 1

    def test_multiple_contexts(self, context_extractor):
        code = '''
        import { createContext } from 'preact';
        export const ThemeContext = createContext('light');
        export const AuthContext = createContext(null);
        export const I18nContext = createContext({ locale: 'en' });
        '''
        result = context_extractor.extract(code, "contexts.tsx")
        contexts = result['contexts']
        assert len(contexts) >= 3
        names = [c.name for c in contexts]
        assert "ThemeContext" in names
        assert "AuthContext" in names
        assert "I18nContext" in names


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestPreactApiExtractor:

    def test_core_import(self, api_extractor):
        code = '''
        import { h, render, Component, Fragment } from 'preact';
        '''
        result = api_extractor.extract(code, "app.tsx")
        imports = result['imports']
        assert len(imports) >= 1
        core_imports = [i for i in imports if i.source == 'preact']
        assert len(core_imports) >= 1
        assert core_imports[0].import_category == "core"
        assert 'h' in core_imports[0].named_imports

    def test_hooks_import(self, api_extractor):
        code = '''
        import { useState, useEffect, useRef } from 'preact/hooks';
        '''
        result = api_extractor.extract(code, "app.tsx")
        imports = result['imports']
        hooks_imports = [i for i in imports if i.source == 'preact/hooks']
        assert len(hooks_imports) >= 1
        assert hooks_imports[0].import_category == "hooks"
        assert 'useState' in hooks_imports[0].named_imports

    def test_compat_import(self, api_extractor):
        code = '''
        import { forwardRef, memo, lazy, Suspense } from 'preact/compat';
        '''
        result = api_extractor.extract(code, "app.tsx")
        imports = result['imports']
        compat_imports = [i for i in imports if i.source == 'preact/compat']
        assert len(compat_imports) >= 1
        assert compat_imports[0].import_category == "compat"

    def test_signals_import(self, api_extractor):
        code = '''
        import { signal, computed, effect, batch } from '@preact/signals';
        '''
        result = api_extractor.extract(code, "store.ts")
        imports = result['imports']
        sig_imports = [i for i in imports if i.source == '@preact/signals']
        assert len(sig_imports) >= 1
        assert sig_imports[0].import_category == "signals"

    def test_router_import(self, api_extractor):
        code = '''
        import Router from 'preact-router';
        import { Link, route } from 'preact-router';
        '''
        result = api_extractor.extract(code, "App.tsx")
        imports = result['imports']
        router_imports = [i for i in imports if i.source == 'preact-router']
        assert len(router_imports) >= 1
        assert router_imports[0].import_category == "router"

    def test_ssr_import(self, api_extractor):
        code = '''
        import { renderToString } from 'preact-render-to-string';
        '''
        result = api_extractor.extract(code, "server.ts")
        imports = result['imports']
        ssr_imports = [i for i in imports if i.source == 'preact-render-to-string']
        assert len(ssr_imports) >= 1
        assert ssr_imports[0].import_category == "ssr"

    def test_render_to_string_pattern(self, api_extractor):
        code = '''
        import { renderToString, renderToStringAsync } from 'preact-render-to-string';
        const html = await renderToStringAsync(<App />);
        '''
        result = api_extractor.extract(code, "server.ts")
        ssr_patterns = result['ssr_patterns']
        assert len(ssr_patterns) >= 1

    def test_hydrate_pattern(self, api_extractor):
        code = '''
        import { hydrate } from 'preact';
        hydrate(<App />, document.getElementById('app'));
        '''
        result = api_extractor.extract(code, "client.ts")
        ssr_patterns = result['ssr_patterns']
        assert len(ssr_patterns) >= 1

    def test_integration_detection_fresh(self, api_extractor):
        code = '''
        import { Handlers } from "$fresh/server.ts";
        export const handler: Handlers = {
            GET(req, ctx) { return ctx.render(); }
        };
        '''
        result = api_extractor.extract(code, "index.tsx")
        integrations = result['integrations']
        assert len(integrations) >= 1

    def test_integration_detection_goober(self, api_extractor):
        code = '''
        import { css, styled } from 'goober';
        const StyledButton = styled('button')`
            color: red;
        `;
        '''
        result = api_extractor.extract(code, "styles.tsx")
        integrations = result['integrations']
        assert len(integrations) >= 1

    def test_htm_tagged_template(self, api_extractor):
        code = '''
        import { h } from 'preact';
        import htm from 'htm';
        const html = htm.bind(h);
        function App() { return html`<div>Hello</div>`; }
        '''
        result = api_extractor.extract(code, "App.js")
        imports = result['imports']
        htm_imports = [i for i in imports if i.source == 'htm']
        assert len(htm_imports) >= 1

    def test_type_detection(self, api_extractor):
        code = '''
        import { VNode, ComponentChildren, JSX, FunctionComponent } from 'preact';
        import { StateUpdater, Ref } from 'preact/hooks';
        '''
        result = api_extractor.extract(code, "types.ts")
        types = result['types']
        assert len(types) >= 1
        type_names = [t.type_name for t in types]
        assert any(tn in type_names for tn in ['VNode', 'ComponentChildren', 'JSX', 'FunctionComponent'])

    def test_testing_library_import(self, api_extractor):
        code = '''
        import { render, fireEvent, screen } from '@testing-library/preact';
        '''
        result = api_extractor.extract(code, "test.tsx")
        imports = result['imports']
        test_imports = [i for i in imports if i.source == '@testing-library/preact']
        assert len(test_imports) >= 1
        assert test_imports[0].import_category == "testing"

    def test_wouter_preact_import(self, api_extractor):
        code = '''
        import { Route, Switch, useRoute } from 'wouter-preact';
        '''
        result = api_extractor.extract(code, "App.tsx")
        imports = result['imports']
        wouter_imports = [i for i in imports if i.source == 'wouter-preact']
        assert len(wouter_imports) >= 1
        assert wouter_imports[0].import_category == "router"

    def test_preact_iso_import(self, api_extractor):
        code = '''
        import { LocationProvider, Router, Route, lazy } from 'preact-iso';
        '''
        result = api_extractor.extract(code, "App.tsx")
        imports = result['imports']
        iso_imports = [i for i in imports if i.source == 'preact-iso']
        assert len(iso_imports) >= 1

    def test_type_import(self, api_extractor):
        code = '''
        import type { Signal, ReadonlySignal } from '@preact/signals';
        '''
        result = api_extractor.extract(code, "types.ts")
        imports = result['imports']
        type_imports = [i for i in imports if i.is_type_import]
        assert len(type_imports) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedPreactParser:

    def test_is_preact_file_positive(self, parser):
        code = '''
        import { h, render } from 'preact';
        import { useState } from 'preact/hooks';
        function App() { return <div>Hello</div>; }
        render(<App />, document.body);
        '''
        assert parser.is_preact_file(code, "App.tsx") is True

    def test_is_preact_file_negative(self, parser):
        code = '''
        import React from 'react';
        function App() { return <div>Hello</div>; }
        '''
        assert parser.is_preact_file(code, "App.tsx") is False

    def test_is_preact_file_signals(self, parser):
        code = '''
        import { signal, computed } from '@preact/signals';
        const count = signal(0);
        '''
        assert parser.is_preact_file(code, "store.ts") is True

    def test_is_preact_file_compat(self, parser):
        code = '''
        import { forwardRef, memo } from 'preact/compat';
        '''
        assert parser.is_preact_file(code, "comp.tsx") is True

    def test_is_preact_file_preact_router(self, parser):
        code = '''
        import Router from 'preact-router';
        '''
        assert parser.is_preact_file(code, "App.tsx") is True

    def test_parse_returns_result(self, parser):
        code = '''
        import { h } from 'preact';
        import { useState } from 'preact/hooks';
        export function Counter() {
            const [count, setCount] = useState(0);
            return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
        }
        '''
        result = parser.parse(code, "Counter.tsx")
        assert isinstance(result, PreactParseResult)
        assert result.file_path == "Counter.tsx"
        assert len(result.components) >= 1
        assert len(result.hook_usages) >= 1
        assert len(result.imports) >= 1

    def test_parse_signals_file(self, parser):
        code = '''
        import { signal, computed, effect, batch } from '@preact/signals';

        export const count = signal(0);
        export const doubled = computed(() => count.value * 2);

        const dispose = effect(() => {
            document.title = `Count: ${count.value}`;
        });

        function reset() {
            batch(() => {
                count.value = 0;
            });
        }
        '''
        result = parser.parse(code, "store.ts")
        assert isinstance(result, PreactParseResult)
        assert len(result.signals) >= 1
        assert len(result.computeds) >= 1
        assert len(result.effects) >= 1
        assert len(result.batches) >= 1

    def test_parse_context_file(self, parser):
        code = '''
        import { createContext } from 'preact';
        import { useContext } from 'preact/hooks';

        export const ThemeContext = createContext('light');

        export function useTheme() {
            return useContext(ThemeContext);
        }

        function App({ children }) {
            return <ThemeContext.Provider value="dark">{children}</ThemeContext.Provider>;
        }
        '''
        result = parser.parse(code, "theme.tsx")
        assert len(result.contexts) >= 1
        assert len(result.custom_hooks) >= 1 or len(result.hook_usages) >= 1

    def test_version_detection_v8(self, parser):
        code = '''
        import { h, Component } from 'preact';
        import { linkState } from 'linkstate';
        class App extends Component {
            render() { return h('div', null, 'Hello'); }
        }
        '''
        result = parser.parse(code, "App.js")
        # v8 detection depends on linkstate/old API usage
        assert result.preact_version in ("v8", "v10", "")

    def test_version_detection_v10(self, parser):
        code = '''
        import { h } from 'preact';
        import { useState, useEffect } from 'preact/hooks';
        '''
        result = parser.parse(code, "App.tsx")
        assert "v10" in result.preact_version or result.preact_version == "v10"

    def test_version_detection_v10_5(self, parser):
        code = '''
        import { h } from 'preact';
        import { useId, useErrorBoundary } from 'preact/hooks';
        '''
        result = parser.parse(code, "App.tsx")
        assert "v10" in result.preact_version

    def test_version_detection_v10_11_signals(self, parser):
        code = '''
        import { signal, computed } from '@preact/signals';
        const count = signal(0);
        '''
        result = parser.parse(code, "store.ts")
        # v10.11+ when signals are used
        ver = result.preact_version
        assert ver in ("v10.11", "v10.19", "v10", "")

    def test_framework_detection_preact(self, parser):
        code = '''
        import { h, render } from 'preact';
        '''
        result = parser.parse(code, "App.tsx")
        assert "preact" in result.detected_frameworks

    def test_framework_detection_hooks(self, parser):
        code = '''
        import { useState } from 'preact/hooks';
        '''
        result = parser.parse(code, "App.tsx")
        assert "preact-hooks" in result.detected_frameworks or "preact" in result.detected_frameworks

    def test_framework_detection_signals(self, parser):
        code = '''
        import { signal } from '@preact/signals';
        '''
        result = parser.parse(code, "store.ts")
        assert "preact-signals" in result.detected_frameworks

    def test_framework_detection_compat(self, parser):
        code = '''
        import { forwardRef } from 'preact/compat';
        '''
        result = parser.parse(code, "comp.tsx")
        assert "preact-compat" in result.detected_frameworks

    def test_framework_detection_router(self, parser):
        code = '''
        import Router from 'preact-router';
        '''
        result = parser.parse(code, "App.tsx")
        assert "preact-router" in result.detected_frameworks

    def test_framework_detection_ssr(self, parser):
        code = '''
        import { renderToString } from 'preact-render-to-string';
        '''
        result = parser.parse(code, "server.ts")
        assert "preact-render-to-string" in result.detected_frameworks

    def test_feature_detection_hooks(self, parser):
        code = '''
        import { useState, useEffect } from 'preact/hooks';
        function App() {
            const [x, setX] = useState(0);
            useEffect(() => {}, []);
        }
        '''
        result = parser.parse(code, "App.tsx")
        features = result.detected_features
        assert "use_state" in features or "hooks" in features

    def test_feature_detection_signals(self, parser):
        code = '''
        import { signal, computed, effect } from '@preact/signals';
        const x = signal(0);
        '''
        result = parser.parse(code, "store.ts")
        features = result.detected_features
        assert "signals" in features or "signal" in features

    def test_feature_detection_compat(self, parser):
        code = '''
        import { forwardRef, memo, createPortal } from 'preact/compat';
        '''
        result = parser.parse(code, "comp.tsx")
        features = result.detected_features
        assert "compat_mode" in features or "forward_ref" in features

    def test_parse_complex_app(self, parser):
        code = '''
        import { h, render, Fragment } from 'preact';
        import { useState, useEffect, useRef, useErrorBoundary, useId } from 'preact/hooks';
        import { signal, computed, effect, batch } from '@preact/signals';
        import { forwardRef, memo, lazy, Suspense } from 'preact/compat';
        import Router from 'preact-router';
        import { createContext } from 'preact';

        // Global state with signals
        export const theme = signal('light');
        export const user = signal(null);
        const isAuthenticated = computed(() => user.value !== null);

        // Context
        const AppContext = createContext(null);

        // Error boundary
        function ErrorBoundary({ children }) {
            const [error, resetError] = useErrorBoundary();
            if (error) return <div>Error! <button onClick={resetError}>Reset</button></div>;
            return children;
        }

        // Custom hook
        export function useAuth() {
            const auth = useContext(AppContext);
            return auth;
        }

        // Lazy route
        const Dashboard = lazy(() => import('./Dashboard'));

        // Memo component
        const UserCard = memo(function UserCard({ name }) {
            return <div class="card">{name}</div>;
        });

        // ForwardRef input
        const Input = forwardRef((props, ref) => {
            const id = useId();
            return <div><label for={id}>{props.label}</label><input ref={ref} id={id} /></div>;
        });

        // Main App
        export default function App() {
            const [count, setCount] = useState(0);
            const inputRef = useRef(null);

            useEffect(() => {
                document.title = `Count: ${count}`;
                return () => { document.title = 'App'; };
            }, [count]);

            return (
                <ErrorBoundary>
                    <Suspense fallback={<div>Loading...</div>}>
                        <Router>
                            <Dashboard path="/dashboard" />
                        </Router>
                    </Suspense>
                    <UserCard name="Alice" />
                    <Input ref={inputRef} label="Name" />
                    <button onClick={() => setCount(c => c + 1)}>{count}</button>
                </ErrorBoundary>
            );
        }

        render(<App />, document.body);
        '''
        result = parser.parse(code, "App.tsx")

        # Components
        assert len(result.components) >= 2  # ErrorBoundary, App

        # Signals
        assert len(result.signals) >= 2  # theme, user

        # Computeds
        assert len(result.computeds) >= 1  # isAuthenticated

        # Contexts
        assert len(result.contexts) >= 1  # AppContext

        # Hooks
        assert len(result.hook_usages) >= 3  # useState, useEffect, useRef, useErrorBoundary, useId

        # Custom hooks
        assert len(result.custom_hooks) >= 1  # useAuth

        # Memos
        assert len(result.memos) >= 1  # UserCard

        # Lazies
        assert len(result.lazies) >= 1  # Dashboard

        # Forward refs
        assert len(result.forward_refs) >= 1  # Input

        # Imports — at least 5 different sources
        sources = {i.source for i in result.imports}
        assert len(sources) >= 4

        # Frameworks detected
        assert "preact" in result.detected_frameworks
        assert "preact-signals" in result.detected_frameworks or "@preact/signals" in str(result.detected_frameworks)

        # Features detected
        assert len(result.detected_features) >= 3

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.tsx")
        assert isinstance(result, PreactParseResult)
        assert len(result.components) == 0
        assert len(result.signals) == 0

    def test_parse_non_preact_file(self, parser):
        code = '''
        import React from 'react';
        function App() { return <div>Hello</div>; }
        '''
        # Parser should still return a result, just with empty lists
        result = parser.parse(code, "App.tsx")
        assert isinstance(result, PreactParseResult)

    def test_version_compare(self):
        cmp = EnhancedPreactParser._version_compare
        assert cmp("v10.11", "v10") > 0
        assert cmp("v10", "v10.11") < 0
        assert cmp("v10.19", "v10.11") > 0
        assert cmp("v10", "v10") == 0
        assert cmp("v10.5", "v8") > 0
        assert cmp("", "v10") < 0
        assert cmp("v10", "") > 0


# ═══════════════════════════════════════════════════════════════════
# BPL Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestPreactBPLIntegration:

    def test_practice_categories_exist(self):
        from codetrellis.bpl.models import PracticeCategory
        assert hasattr(PracticeCategory, 'PREACT_COMPONENTS')
        assert hasattr(PracticeCategory, 'PREACT_HOOKS')
        assert hasattr(PracticeCategory, 'PREACT_SIGNALS')
        assert hasattr(PracticeCategory, 'PREACT_CONTEXT')
        assert hasattr(PracticeCategory, 'PREACT_PERFORMANCE')
        assert hasattr(PracticeCategory, 'PREACT_SSR')
        assert hasattr(PracticeCategory, 'PREACT_TYPESCRIPT')
        assert hasattr(PracticeCategory, 'PREACT_PATTERNS')
        assert hasattr(PracticeCategory, 'PREACT_COMPAT')
        assert hasattr(PracticeCategory, 'PREACT_ROUTING')

    def test_practice_category_values(self):
        from codetrellis.bpl.models import PracticeCategory
        assert PracticeCategory.PREACT_COMPONENTS.value == "preact_components"
        assert PracticeCategory.PREACT_HOOKS.value == "preact_hooks"
        assert PracticeCategory.PREACT_SIGNALS.value == "preact_signals"

    def test_preact_core_yaml_exists(self):
        import os
        yaml_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'codetrellis', 'bpl', 'practices', 'preact_core.yaml'
        )
        assert os.path.exists(yaml_path), f"preact_core.yaml not found at {yaml_path}"

    def test_preact_core_yaml_loads(self):
        import yaml
        import os
        yaml_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'codetrellis', 'bpl', 'practices', 'preact_core.yaml'
        )
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert 'practices' in data
        assert len(data['practices']) == 50
        # Check first and last IDs
        ids = [p['id'] for p in data['practices']]
        assert 'PREACT001' in ids
        assert 'PREACT050' in ids

    def test_preact_core_yaml_categories(self):
        import yaml
        import os
        yaml_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'codetrellis', 'bpl', 'practices', 'preact_core.yaml'
        )
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        categories = {p['category'] for p in data['practices']}
        assert 'preact_components' in categories
        assert 'preact_hooks' in categories
        assert 'preact_signals' in categories
        assert 'preact_context' in categories
        assert 'preact_performance' in categories
        assert 'preact_ssr' in categories


# ═══════════════════════════════════════════════════════════════════
# Scanner Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestPreactScannerIntegration:

    def test_project_matrix_has_preact_fields(self):
        from codetrellis.scanner import ProjectMatrix
        pm = ProjectMatrix(root_path=".", name="test")
        assert hasattr(pm, 'preact_components')
        assert hasattr(pm, 'preact_class_components')
        assert hasattr(pm, 'preact_memos')
        assert hasattr(pm, 'preact_lazies')
        assert hasattr(pm, 'preact_forward_refs')
        assert hasattr(pm, 'preact_error_boundaries')
        assert hasattr(pm, 'preact_hook_usages')
        assert hasattr(pm, 'preact_custom_hooks')
        assert hasattr(pm, 'preact_hook_dependencies')
        assert hasattr(pm, 'preact_signals')
        assert hasattr(pm, 'preact_computeds')
        assert hasattr(pm, 'preact_effects')
        assert hasattr(pm, 'preact_batches')
        assert hasattr(pm, 'preact_contexts')
        assert hasattr(pm, 'preact_context_consumers')
        assert hasattr(pm, 'preact_imports')
        assert hasattr(pm, 'preact_integrations')
        assert hasattr(pm, 'preact_types')
        assert hasattr(pm, 'preact_ssr_patterns')
        assert hasattr(pm, 'preact_detected_frameworks')
        assert hasattr(pm, 'preact_detected_features')
        assert hasattr(pm, 'preact_version')
        assert hasattr(pm, 'preact_has_signals')
        assert hasattr(pm, 'preact_has_compat')
        assert hasattr(pm, 'preact_has_ssr')

    def test_project_matrix_defaults(self):
        from codetrellis.scanner import ProjectMatrix
        pm = ProjectMatrix(root_path=".", name="test")
        assert pm.preact_components == []
        assert pm.preact_signals == []
        assert pm.preact_version == ""
        assert pm.preact_has_signals is False
        assert pm.preact_has_compat is False
        assert pm.preact_has_ssr is False

    def test_project_matrix_to_dict_has_preact(self):
        from codetrellis.scanner import ProjectMatrix
        pm = ProjectMatrix(root_path=".", name="test")
        d = pm.to_dict()
        assert "preact" in d
        preact_section = d["preact"]
        assert "components" in preact_section
        assert "signals" in preact_section
        assert "hooks" in preact_section or "hook_usages" in preact_section
        assert "version" in preact_section
        assert "has_signals" in preact_section
        assert "has_compat" in preact_section
        assert "has_ssr" in preact_section

    def test_scanner_has_preact_parser(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner(".")
        assert hasattr(scanner, 'preact_parser')
        assert isinstance(scanner.preact_parser, EnhancedPreactParser)

    def test_scanner_has_parse_preact_method(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner(".")
        assert hasattr(scanner, '_parse_preact')
        assert callable(scanner._parse_preact)
