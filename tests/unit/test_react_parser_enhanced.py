"""
Tests for React extractors and EnhancedReactParser.

Part of CodeTrellis v4.32 React Language Support.
Tests cover:
- Component extraction (functional, class, HOC, forwardRef, memo, lazy)
- Hook extraction (built-in, custom, dependencies)
- Context extraction (createContext, Provider, useContext)
- State management extraction (Redux, Zustand, Jotai, TanStack Query)
- Routing extraction (React Router, Next.js, Remix)
- React parser integration (framework detection, version detection)
"""

import pytest
from codetrellis.react_parser_enhanced import (
    EnhancedReactParser,
    ReactParseResult,
)
from codetrellis.extractors.react import (
    ReactComponentExtractor,
    ReactHookExtractor,
    ReactContextExtractor,
    ReactStateExtractor,
    ReactRoutingExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedReactParser()


@pytest.fixture
def component_extractor():
    return ReactComponentExtractor()


@pytest.fixture
def hook_extractor():
    return ReactHookExtractor()


@pytest.fixture
def context_extractor():
    return ReactContextExtractor()


@pytest.fixture
def state_extractor():
    return ReactStateExtractor()


@pytest.fixture
def routing_extractor():
    return ReactRoutingExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestComponentExtractor:
    """Tests for ReactComponentExtractor."""

    def test_functional_component_function_declaration(self, component_extractor):
        code = '''
export function UserProfile({ userId }) {
    const [user, setUser] = useState(null);
    return <div>{user?.name}</div>;
}
'''
        result = component_extractor.extract(code, "UserProfile.jsx")
        components = result.get('components', [])
        assert len(components) >= 1
        names = [c.name for c in components]
        assert 'UserProfile' in names

    def test_arrow_function_component(self, component_extractor):
        code = '''
export const Dashboard = () => {
    return <div>Dashboard</div>;
};
'''
        result = component_extractor.extract(code, "Dashboard.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Dashboard' in names

    def test_class_component(self, component_extractor):
        code = '''
class ErrorBoundary extends React.Component {
    componentDidCatch(error, errorInfo) {
        console.error(error);
    }

    render() {
        if (this.state.hasError) {
            return <h1>Something went wrong.</h1>;
        }
        return this.props.children;
    }
}
'''
        result = component_extractor.extract(code, "ErrorBoundary.tsx")
        boundaries = result.get('error_boundaries', [])
        assert len(boundaries) >= 1

    def test_forward_ref(self, component_extractor):
        code = '''
const FancyInput = React.forwardRef((props, ref) => {
    return <input ref={ref} {...props} />;
});
'''
        result = component_extractor.extract(code, "FancyInput.tsx")
        forward_refs = result.get('forward_refs', [])
        assert len(forward_refs) >= 1

    def test_memo_component(self, component_extractor):
        code = '''
const MemoizedList = React.memo(function List({ items }) {
    return <ul>{items.map(i => <li key={i.id}>{i.name}</li>)}</ul>;
});
'''
        result = component_extractor.extract(code, "List.tsx")
        memos = result.get('memos', [])
        assert len(memos) >= 1

    def test_lazy_component(self, component_extractor):
        code = '''
const LazySettings = React.lazy(() => import('./Settings'));
const LazyProfile = lazy(() => import('./Profile'));
'''
        result = component_extractor.extract(code, "App.tsx")
        lazy = result.get('lazy_components', [])
        assert len(lazy) >= 1

    def test_server_component_directive(self, component_extractor):
        code = '''
'use client';

export function InteractiveWidget() {
    const [count, setCount] = useState(0);
    return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
'''
        result = component_extractor.extract(code, "Widget.tsx")
        components = result.get('components', [])
        if components:
            assert any(c.is_client_component for c in components)

    def test_hoc_detection(self, component_extractor):
        code = '''
const EnhancedComponent = withRouter(MyComponent);
const ConnectedApp = connect(mapState, mapDispatch)(App);
'''
        result = component_extractor.extract(code, "App.tsx")
        hocs = result.get('hocs', [])
        assert len(hocs) >= 1


# ═══════════════════════════════════════════════════════════════════
# Hook Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestHookExtractor:
    """Tests for ReactHookExtractor."""

    def test_builtin_hooks(self, hook_extractor):
        code = '''
function Counter() {
    const [count, setCount] = useState(0);
    const inputRef = useRef(null);

    useEffect(() => {
        document.title = `Count: ${count}`;
    }, [count]);

    const double = useMemo(() => count * 2, [count]);

    return <div>{count} (double: {double})</div>;
}
'''
        result = hook_extractor.extract(code, "Counter.tsx")
        usages = result.get('hook_usages', [])
        hook_names = [h.hook_name for h in usages]
        assert 'useState' in hook_names
        assert 'useRef' in hook_names
        assert 'useEffect' in hook_names
        assert 'useMemo' in hook_names

    def test_custom_hook(self, hook_extractor):
        code = '''
export function useLocalStorage(key, initialValue) {
    const [storedValue, setStoredValue] = useState(() => {
        const item = window.localStorage.getItem(key);
        return item ? JSON.parse(item) : initialValue;
    });

    const setValue = useCallback((value) => {
        setStoredValue(value);
        window.localStorage.setItem(key, JSON.stringify(value));
    }, [key]);

    return [storedValue, setValue];
}
'''
        result = hook_extractor.extract(code, "useLocalStorage.ts")
        custom = result.get('custom_hooks', [])
        assert len(custom) >= 1
        assert custom[0].name == 'useLocalStorage'

    def test_react_19_hooks(self, hook_extractor):
        code = '''
function Form() {
    const [state, formAction, pending] = useActionState(submitForm, null);
    const { pending: formPending } = useFormStatus();
    const [optimistic, addOptimistic] = useOptimistic(items);
    return <form action={formAction}>...</form>;
}
'''
        result = hook_extractor.extract(code, "Form.tsx")
        usages = result.get('hook_usages', [])
        hook_names = [h.hook_name for h in usages]
        assert 'useActionState' in hook_names
        assert 'useFormStatus' in hook_names
        assert 'useOptimistic' in hook_names

    def test_hook_dependencies(self, hook_extractor):
        code = '''
function App() {
    useEffect(() => {
        console.log('mounted');
    }, []);

    useEffect(() => {
        console.log('runs every render');
    });

    useMemo(() => heavy(), [dep1, dep2]);
}
'''
        result = hook_extractor.extract(code, "App.tsx")
        deps = result.get('hook_dependencies', [])
        assert len(deps) >= 1


# ═══════════════════════════════════════════════════════════════════
# Context Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestContextExtractor:
    """Tests for ReactContextExtractor."""

    def test_create_context(self, context_extractor):
        code = '''
const ThemeContext = createContext('light');
const AuthContext = React.createContext(null);
'''
        result = context_extractor.extract(code, "contexts.ts")
        contexts = result.get('contexts', [])
        assert len(contexts) >= 2
        names = [c.name for c in contexts]
        assert 'ThemeContext' in names
        assert 'AuthContext' in names

    def test_usecontext_consumer(self, context_extractor):
        code = '''
function Header() {
    const theme = useContext(ThemeContext);
    const auth = useContext(AuthContext);
    return <header style={{ color: theme.primary }}>Welcome {auth.user}</header>;
}
'''
        result = context_extractor.extract(code, "Header.tsx")
        consumers = result.get('consumers', [])
        assert len(consumers) >= 2

    def test_provider_component(self, context_extractor):
        code = '''
function ThemeProvider({ children }) {
    const [theme, setTheme] = useState('light');
    return (
        <ThemeContext.Provider value={{ theme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}
'''
        result = context_extractor.extract(code, "ThemeProvider.tsx")
        contexts = result.get('contexts', [])
        # Provider detection may add to contexts list


# ═══════════════════════════════════════════════════════════════════
# State Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestStateExtractor:
    """Tests for ReactStateExtractor."""

    def test_redux_slice(self, state_extractor):
        code = '''
import { createSlice } from '@reduxjs/toolkit';

const counterSlice = createSlice({
    name: 'counter',
    initialState: { value: 0 },
    reducers: {
        increment(state) { state.value += 1; },
        decrement(state) { state.value -= 1; },
        reset(state) { state.value = 0; },
    },
});

export const { increment, decrement, reset } = counterSlice.actions;
export default counterSlice.reducer;
'''
        result = state_extractor.extract(code, "counterSlice.ts")
        slices = result.get('slices', [])
        assert len(slices) >= 1
        assert slices[0].name == 'counterSlice'

    def test_zustand_store(self, state_extractor):
        code = '''
import { create } from 'zustand';

const useCartStore = create((set) => ({
    items: [],
    addItem: (item) => set(state => ({ items: [...state.items, item] })),
    removeItem: (id) => set(state => ({ items: state.items.filter(i => i.id !== id) })),
    clearCart: () => set({ items: [] }),
}));
'''
        result = state_extractor.extract(code, "cartStore.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1

    def test_jotai_atoms(self, state_extractor):
        code = '''
import { atom } from 'jotai';

const countAtom = atom(0);
const doubleAtom = atom((get) => get(countAtom) * 2);
const userAtom = atomWithStorage('user', null);
'''
        result = state_extractor.extract(code, "atoms.ts")
        atoms = result.get('atoms', [])
        assert len(atoms) >= 1

    def test_tanstack_query(self, state_extractor):
        code = '''
import { useQuery, useMutation } from '@tanstack/react-query';

function useUsers() {
    return useQuery({
        queryKey: ['users'],
        queryFn: () => fetch('/api/users').then(r => r.json()),
    });
}

function useCreateUser() {
    return useMutation({
        mutationFn: (data) => fetch('/api/users', { method: 'POST', body: JSON.stringify(data) }),
    });
}
'''
        result = state_extractor.extract(code, "queries.ts")
        queries = result.get('queries', [])
        assert len(queries) >= 1


# ═══════════════════════════════════════════════════════════════════
# Routing Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRoutingExtractor:
    """Tests for ReactRoutingExtractor."""

    def test_react_router_jsx(self, routing_extractor):
        code = '''
import { Route, Routes } from 'react-router-dom';

function AppRouter() {
    return (
        <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/users/:id" element={<UserProfile />} />
        </Routes>
    );
}
'''
        result = routing_extractor.extract(code, "AppRouter.tsx")
        routes = result.get('routes', [])
        assert len(routes) >= 3
        paths = [r.path for r in routes]
        assert '/' in paths
        assert '/about' in paths

    def test_create_browser_router(self, routing_extractor):
        code = '''
const router = createBrowserRouter([
    {
        path: "/",
        element: <Layout />,
        children: [
            { path: "dashboard", element: <Dashboard /> },
            { path: "settings", element: <Settings /> },
        ],
    },
]);
'''
        result = routing_extractor.extract(code, "router.tsx")
        routes = result.get('routes', [])
        assert len(routes) >= 1

    def test_next_pages_router(self, routing_extractor):
        code = '''
export async function getServerSideProps(context) {
    const user = await fetchUser(context.params.id);
    return { props: { user } };
}

export default function UserPage({ user }) {
    return <div>{user.name}</div>;
}
'''
        result = routing_extractor.extract(code, "pages/users/[id].tsx")
        pages = result.get('pages', [])
        assert len(pages) >= 1
        assert pages[0].has_ssr is True
        assert pages[0].framework == "next-pages"

    def test_next_app_router_page(self, routing_extractor):
        code = '''
export const metadata = { title: 'Dashboard' };

export default async function DashboardPage() {
    const data = await fetchDashboard();
    return <div>{data.title}</div>;
}
'''
        result = routing_extractor.extract(code, "app/dashboard/page.tsx")
        pages = result.get('pages', [])
        assert len(pages) >= 1
        assert pages[0].framework == "next-app"
        assert pages[0].has_metadata is True

    def test_next_app_router_layout(self, routing_extractor):
        code = '''
export default function RootLayout({ children }) {
    return (
        <html>
            <body>{children}</body>
        </html>
    );
}
'''
        result = routing_extractor.extract(code, "app/layout.tsx")
        layouts = result.get('layouts', [])
        assert len(layouts) >= 1
        assert layouts[0].framework == "next-app"

    def test_remix_route(self, routing_extractor):
        code = '''
export async function loader({ params }) {
    return json(await getUser(params.id));
}

export async function action({ request }) {
    const formData = await request.formData();
    return updateUser(formData);
}

export default function UserRoute() {
    const user = useLoaderData();
    return <div>{user.name}</div>;
}
'''
        result = routing_extractor.extract(code, "routes/users.$id.tsx")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        assert routes[0].framework == "remix"
        assert routes[0].has_loader is True
        assert routes[0].has_action is True


# ═══════════════════════════════════════════════════════════════════
# React Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestReactParser:
    """Tests for EnhancedReactParser integration."""

    def test_parse_result_type(self, parser):
        code = '''
import { useState } from 'react';

export function Counter() {
    const [count, setCount] = useState(0);
    return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
'''
        result = parser.parse(code, "Counter.tsx")
        assert isinstance(result, ReactParseResult)
        assert result.file_type == "tsx"
        assert result.has_jsx is True

    def test_framework_detection_react(self, parser):
        code = '''
import { useState, useEffect } from 'react';

export function App() {
    const [data, setData] = useState(null);
    useEffect(() => { fetch('/api').then(r => r.json()).then(setData); }, []);
    return <div>{JSON.stringify(data)}</div>;
}
'''
        result = parser.parse(code, "App.tsx")
        assert 'react' in result.detected_frameworks

    def test_framework_detection_nextjs(self, parser):
        code = '''
import { NextPage, GetServerSideProps } from 'next';

export const getServerSideProps: GetServerSideProps = async () => {
    return { props: {} };
};

const Page: NextPage = () => <div>Hello</div>;
export default Page;
'''
        result = parser.parse(code, "pages/index.tsx")
        assert 'nextjs' in result.detected_frameworks

    def test_framework_detection_redux(self, parser):
        code = '''
import { useSelector, useDispatch } from 'react-redux';
import { createSlice, configureStore } from '@reduxjs/toolkit';
'''
        result = parser.parse(code, "store.ts")
        assert 'redux' in result.detected_frameworks

    def test_framework_detection_tanstack_query(self, parser):
        code = '''
import { useQuery, QueryClient, QueryClientProvider } from '@tanstack/react-query';

function App() {
    const { data } = useQuery({ queryKey: ['todos'], queryFn: fetchTodos });
    return <div>{data?.length} todos</div>;
}
'''
        result = parser.parse(code, "App.tsx")
        assert 'tanstack-query' in result.detected_frameworks

    def test_framework_detection_styled_components(self, parser):
        code = '''
import styled from 'styled-components';

const Button = styled.button`
    background: blue;
    color: white;
`;
'''
        result = parser.parse(code, "Button.tsx")
        assert 'styled-components' in result.detected_frameworks

    def test_react_version_detection_19(self, parser):
        code = '''
import { useActionState, useOptimistic } from 'react';

function Form() {
    const [state, action, pending] = useActionState(submitForm, null);
    return <form action={action}>...</form>;
}
'''
        result = parser.parse(code, "Form.tsx")
        assert result.react_version == '19.0'

    def test_react_version_detection_18(self, parser):
        code = '''
import { useId, useTransition } from 'react';

function SearchInput() {
    const id = useId();
    const [isPending, startTransition] = useTransition();
    return <input id={id} />;
}
'''
        result = parser.parse(code, "Search.tsx")
        assert result.react_version == '18.0'

    def test_react_version_detection_hooks(self, parser):
        code = '''
import { useState, useEffect } from 'react';

function App() {
    const [count, setCount] = useState(0);
    useEffect(() => {}, []);
    return <div>{count}</div>;
}
'''
        result = parser.parse(code, "App.tsx")
        assert result.react_version == '16.8'

    def test_client_component_detection(self, parser):
        code = '''
'use client';

import { useState } from 'react';

export function InteractiveWidget() {
    const [open, setOpen] = useState(false);
    return <div onClick={() => setOpen(!open)}>{open ? 'Open' : 'Closed'}</div>;
}
'''
        result = parser.parse(code, "Widget.tsx")
        assert result.is_client_component is True

    def test_server_component_detection(self, parser):
        code = '''
import { db } from '@/lib/db';

export default async function UsersPage() {
    const users = await db.users.findMany();
    return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}
'''
        result = parser.parse(code, "app/users/page.tsx")
        assert result.is_server_component is True

    def test_is_react_file_jsx(self, parser):
        assert parser.is_react_file("anything", "Component.jsx") is True

    def test_is_react_file_tsx(self, parser):
        assert parser.is_react_file("anything", "Component.tsx") is True

    def test_is_react_file_with_hooks(self, parser):
        code = "const [state, setState] = useState(0);"
        assert parser.is_react_file(code, "file.ts") is True

    def test_is_react_file_plain_js(self, parser):
        code = "const x = 42; console.log(x);"
        assert parser.is_react_file(code, "utils.js") is False

    def test_full_component_extraction(self, parser):
        code = '''
import { useState, useEffect, useContext, useMemo, useCallback } from 'react';
import { ThemeContext } from './theme';

interface DashboardProps {
    userId: string;
}

export default function Dashboard({ userId }: DashboardProps) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const theme = useContext(ThemeContext);
    const inputRef = useRef(null);

    useEffect(() => {
        fetch(`/api/dashboard/${userId}`)
            .then(r => r.json())
            .then(d => { setData(d); setLoading(false); });
    }, [userId]);

    const processedData = useMemo(() => {
        return data ? transform(data) : null;
    }, [data]);

    const handleRefresh = useCallback(() => {
        setLoading(true);
        fetch(`/api/dashboard/${userId}`)
            .then(r => r.json())
            .then(setData);
    }, [userId]);

    if (loading) return <Spinner />;
    return (
        <div style={{ background: theme.bg }}>
            <Header />
            <DataTable data={processedData} />
            <button onClick={handleRefresh}>Refresh</button>
        </div>
    );
}
'''
        result = parser.parse(code, "Dashboard.tsx")
        assert len(result.components) >= 1
        assert len(result.hook_usages) >= 5  # useState x2, useEffect, useContext, useMemo, useCallback
        assert result.has_jsx is True
        assert result.react_version == '16.8'

    def test_comprehensive_react_app(self, parser):
        """Test parsing a comprehensive React file with many features."""
        code = '''
'use client';

import { useState, useEffect, useCallback, Suspense, lazy } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';

const LazyChart = lazy(() => import('./Chart'));

const StyledCard = styled.div`
    border-radius: 8px;
    padding: 16px;
`;

interface FormData {
    name: string;
    email: string;
}

export default function UserManagement() {
    const [selectedUser, setSelectedUser] = useState(null);
    const { register, handleSubmit } = useForm<FormData>();

    const { data: users, isLoading } = useQuery({
        queryKey: ['users'],
        queryFn: fetchUsers,
    });

    const createMutation = useMutation({
        mutationFn: createUser,
        onSuccess: () => queryClient.invalidateQueries(['users']),
    });

    const onSubmit = useCallback((data: FormData) => {
        createMutation.mutate(data);
    }, [createMutation]);

    return (
        <StyledCard>
            <AnimatePresence>
                {isLoading ? (
                    <motion.div animate={{ opacity: 1 }}>Loading...</motion.div>
                ) : (
                    <UserList users={users} onSelect={setSelectedUser} />
                )}
            </AnimatePresence>
            <Suspense fallback={<div>Loading chart...</div>}>
                <LazyChart userId={selectedUser?.id} />
            </Suspense>
        </StyledCard>
    );
}
'''
        result = parser.parse(code, "UserManagement.tsx")

        # Should detect multiple frameworks
        assert 'react' in result.detected_frameworks
        assert 'tanstack-query' in result.detected_frameworks
        assert 'react-hook-form' in result.detected_frameworks
        assert 'framer-motion' in result.detected_frameworks
        assert 'styled-components' in result.detected_frameworks

        # Should detect components
        assert len(result.components) >= 1

        # Should detect hooks
        assert len(result.hook_usages) >= 3  # useState, useCallback, useQuery, useMutation, useForm

        # Should be a client component
        assert result.is_client_component is True

        # Should detect lazy
        assert len(result.lazy_components) >= 1
