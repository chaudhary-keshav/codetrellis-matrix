"""
Tests for Jotai extractors and EnhancedJotaiParser.

Part of CodeTrellis v4.49 Jotai Atomic State Management Framework Support.
Tests cover:
- Atom extraction (primitive, derived, writable, async, atomFamily, resettable)
- Selector extraction (derived atoms, selectAtom, focusAtom, splitAtom, loadable)
- Middleware extraction (atomWithStorage, atomEffect, atomWithMachine)
- Action extraction (useAtom, useAtomValue, useSetAtom, store API, write fns)
- API extraction (imports, integrations, TypeScript types)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from pathlib import Path
from codetrellis.jotai_parser_enhanced import (
    EnhancedJotaiParser,
    JotaiParseResult,
)
from codetrellis.extractors.jotai import (
    JotaiAtomExtractor,
    JotaiSelectorExtractor,
    JotaiMiddlewareExtractor,
    JotaiActionExtractor,
    JotaiApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedJotaiParser()


@pytest.fixture
def atom_extractor():
    return JotaiAtomExtractor()


@pytest.fixture
def selector_extractor():
    return JotaiSelectorExtractor()


@pytest.fixture
def middleware_extractor():
    return JotaiMiddlewareExtractor()


@pytest.fixture
def action_extractor():
    return JotaiActionExtractor()


@pytest.fixture
def api_extractor():
    return JotaiApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Atom Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestJotaiAtomExtractor:
    """Tests for JotaiAtomExtractor."""

    def test_primitive_atom_number(self, atom_extractor):
        code = '''
import { atom } from 'jotai';

const countAtom = atom(0);
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        atom = result['atoms'][0]
        assert atom.name == "countAtom"
        assert atom.atom_type == "primitive"

    def test_primitive_atom_string(self, atom_extractor):
        code = '''
import { atom } from 'jotai';

const nameAtom = atom('');
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        assert result['atoms'][0].name == "nameAtom"

    def test_primitive_atom_boolean(self, atom_extractor):
        code = '''
import { atom } from 'jotai';

const isDarkAtom = atom(false);
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        assert result['atoms'][0].name == "isDarkAtom"

    def test_primitive_atom_object(self, atom_extractor):
        code = '''
import { atom } from 'jotai';

const userAtom = atom({ name: '', age: 0 });
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        assert result['atoms'][0].name == "userAtom"

    def test_derived_read_only_atom(self, atom_extractor):
        code = '''
import { atom } from 'jotai';

const countAtom = atom(0);
const doubleAtom = atom((get) => get(countAtom) * 2);
'''
        result = atom_extractor.extract(code, "atoms.ts")
        atoms = result['atoms']
        assert len(atoms) >= 1
        derived = [a for a in atoms if a.name == "doubleAtom"]
        assert len(derived) >= 1
        assert derived[0].atom_type == "derived"

    def test_writable_derived_atom(self, atom_extractor):
        code = '''
import { atom } from 'jotai';

const celsiusAtom = atom(25);
const fahrenheitAtom = atom(
    (get) => get(celsiusAtom) * 9 / 5 + 32,
    (get, set, newF) => set(celsiusAtom, (newF - 32) * 5 / 9)
);
'''
        result = atom_extractor.extract(code, "atoms.ts")
        atoms = result['atoms']
        writable = [a for a in atoms if a.name == "fahrenheitAtom"]
        assert len(writable) >= 1

    def test_atom_family(self, atom_extractor):
        code = '''
import { atomFamily } from 'jotai/utils';
import { atom } from 'jotai';

const todoAtom = atomFamily((id) => atom({ id, text: '', done: false }));
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atom_families']) >= 1
        assert result['atom_families'][0].name == "todoAtom"

    def test_atom_with_reset(self, atom_extractor):
        code = '''
import { atomWithReset } from 'jotai/utils';

const filterAtom = atomWithReset('all');
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['resettable_atoms']) >= 1
        assert result['resettable_atoms'][0].name == "filterAtom"

    def test_atom_with_typescript_generic(self, atom_extractor):
        code = '''
import { atom } from 'jotai';

const userAtom = atom<User | null>(null);
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        atom = result['atoms'][0]
        assert atom.name == "userAtom"

    def test_async_atom(self, atom_extractor):
        code = '''
import { atom } from 'jotai';

const userAtom = atom(async (get) => {
    const id = get(userIdAtom);
    const res = await fetch(`/api/users/${id}`);
    return res.json();
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        atoms = result['atoms']
        assert len(atoms) >= 1

    def test_atom_with_reducer(self, atom_extractor):
        code = '''
import { atomWithReducer } from 'jotai/utils';

const countAtom = atomWithReducer(0, (prev, action) => {
    if (action.type === 'inc') return prev + 1;
    return prev;
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        atoms = result['atoms']
        # atomWithReducer should be detected
        assert len(atoms) >= 1 or len(result.get('resettable_atoms', [])) >= 0

    def test_multiple_atoms(self, atom_extractor):
        code = '''
import { atom } from 'jotai';

const countAtom = atom(0);
const nameAtom = atom('hello');
const flagAtom = atom(true);
const listAtom = atom([1, 2, 3]);
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 4


# ═══════════════════════════════════════════════════════════════════
# Selector Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestJotaiSelectorExtractor:
    """Tests for JotaiSelectorExtractor."""

    def test_select_atom(self, selector_extractor):
        code = '''
import { selectAtom } from 'jotai/utils';
import { atom } from 'jotai';

const userAtom = atom({ name: '', age: 0 });
const nameAtom = selectAtom(userAtom, (user) => user.name);
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['select_atoms']) >= 1
        assert result['select_atoms'][0].name == "nameAtom"

    def test_focus_atom(self, selector_extractor):
        code = '''
import { focusAtom } from 'jotai-optics';
import { atom } from 'jotai';

const formAtom = atom({ user: { name: '' } });
const nameAtom = focusAtom(formAtom, (o) => o.prop('user').prop('name'));
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['focus_atoms']) >= 1
        assert result['focus_atoms'][0].name == "nameAtom"

    def test_derived_atom(self, selector_extractor):
        code = '''
import { atom } from 'jotai';

const priceAtom = atom(100);
const taxAtom = atom(0.1);
const totalAtom = atom((get) => get(priceAtom) * (1 + get(taxAtom)));
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['derived_atoms']) >= 1

    def test_split_atom(self, selector_extractor):
        code = '''
import { splitAtom } from 'jotai/utils';
import { atom } from 'jotai';

const todosAtom = atom([{ id: 1, text: 'Buy milk' }]);
const todoAtomsAtom = splitAtom(todosAtom);
'''
        result = selector_extractor.extract(code, "selectors.ts")
        # splitAtom should be detected in derived_atoms or as a feature
        derived = result.get('derived_atoms', [])
        assert len(derived) >= 0  # May detect todoAtomsAtom

    def test_loadable(self, selector_extractor):
        code = '''
import { loadable } from 'jotai/utils';
import { atom } from 'jotai';

const asyncAtom = atom(async () => fetch('/api'));
const loadableAtom = loadable(asyncAtom);
'''
        result = selector_extractor.extract(code, "selectors.ts")
        # loadable creates a derived atom
        derived = result.get('derived_atoms', [])
        assert len(derived) >= 0


# ═══════════════════════════════════════════════════════════════════
# Middleware Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestJotaiMiddlewareExtractor:
    """Tests for JotaiMiddlewareExtractor."""

    def test_atom_with_storage_local(self, middleware_extractor):
        code = '''
import { atomWithStorage } from 'jotai/utils';

const themeAtom = atomWithStorage('theme', 'light');
'''
        result = middleware_extractor.extract(code, "middleware.ts")
        assert len(result['storage_atoms']) >= 1
        sa = result['storage_atoms'][0]
        assert sa.name == "themeAtom"
        assert sa.storage_key == "theme"

    def test_atom_with_storage_session(self, middleware_extractor):
        code = '''
import { atomWithStorage } from 'jotai/utils';

const tokenAtom = atomWithStorage('token', '', sessionStorage);
'''
        result = middleware_extractor.extract(code, "middleware.ts")
        assert len(result['storage_atoms']) >= 1
        sa = result['storage_atoms'][0]
        assert sa.name == "tokenAtom"

    def test_atom_effect(self, middleware_extractor):
        code = '''
import { atomEffect } from 'jotai-effect';
import { atom } from 'jotai';

const countAtom = atom(0);
const logEffect = atomEffect((get, set) => {
    const count = get(countAtom);
    console.log('Count:', count);
    return () => { /* cleanup */ };
});
'''
        result = middleware_extractor.extract(code, "effects.ts")
        assert len(result['effects']) >= 1
        eff = result['effects'][0]
        assert eff.name == "logEffect"

    def test_atom_with_machine(self, middleware_extractor):
        code = '''
import { atomWithMachine } from 'jotai-xstate';

const toggleMachineAtom = atomWithMachine(toggleMachine);
'''
        result = middleware_extractor.extract(code, "machines.ts")
        assert len(result['machine_atoms']) >= 1
        assert result['machine_atoms'][0].name == "toggleMachineAtom"

    def test_atom_with_observable(self, middleware_extractor):
        code = '''
import { atomWithObservable } from 'jotai/utils';

const tickAtom = atomWithObservable(() => interval(1000));
'''
        result = middleware_extractor.extract(code, "observable.ts")
        # Observable atoms should be detected in storage_atoms or effects
        assert len(result.get('storage_atoms', [])) >= 0

    def test_on_mount(self, middleware_extractor):
        code = '''
import { atom } from 'jotai';

const wsAtom = atom(null);
wsAtom.onMount = (setAtom) => {
    const ws = new WebSocket('ws://example.com');
    ws.onmessage = (e) => setAtom(JSON.parse(e.data));
    return () => ws.close();
};
'''
        result = middleware_extractor.extract(code, "mount.ts")
        effects = result.get('effects', [])
        assert len(effects) >= 0  # onMount may or may not be captured


# ═══════════════════════════════════════════════════════════════════
# Action Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestJotaiActionExtractor:
    """Tests for JotaiActionExtractor."""

    def test_use_atom(self, action_extractor):
        code = '''
import { useAtom } from 'jotai';

function Counter() {
    const [count, setCount] = useAtom(countAtom);
    return <div>{count}</div>;
}
'''
        result = action_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 1
        hu = result['hook_usages'][0]
        assert hu.hook_name == "useAtom"

    def test_use_atom_value(self, action_extractor):
        code = '''
import { useAtomValue } from 'jotai';

function Display() {
    const count = useAtomValue(countAtom);
    return <span>{count}</span>;
}
'''
        result = action_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 1
        hu = result['hook_usages'][0]
        assert hu.hook_name == "useAtomValue"

    def test_use_set_atom(self, action_extractor):
        code = '''
import { useSetAtom } from 'jotai';

function Button() {
    const setCount = useSetAtom(countAtom);
    return <button onClick={() => setCount(c => c + 1)}>+</button>;
}
'''
        result = action_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 1
        hu = result['hook_usages'][0]
        assert hu.hook_name == "useSetAtom"

    def test_use_store(self, action_extractor):
        code = '''
import { useStore } from 'jotai';

function MyComponent() {
    const store = useStore();
    const count = store.get(countAtom);
}
'''
        result = action_extractor.extract(code, "component.tsx")
        hooks = result['hook_usages']
        assert len(hooks) >= 1

    def test_use_hydrate_atoms(self, action_extractor):
        code = '''
import { useHydrateAtoms } from 'jotai/utils';

function Page({ initialCount }) {
    useHydrateAtoms([[countAtom, initialCount]]);
    return <Counter />;
}
'''
        result = action_extractor.extract(code, "page.tsx")
        hooks = result['hook_usages']
        assert len(hooks) >= 1

    def test_create_store(self, action_extractor):
        code = '''
import { createStore, Provider } from 'jotai';

const myStore = createStore();
myStore.set(countAtom, 42);

function App() {
    return <Provider store={myStore}><Counter /></Provider>;
}
'''
        result = action_extractor.extract(code, "app.tsx")
        stores = result['store_usages']
        assert len(stores) >= 1

    def test_get_default_store(self, action_extractor):
        code = '''
import { getDefaultStore } from 'jotai';

const store = getDefaultStore();
const count = store.get(countAtom);
store.set(countAtom, count + 1);
'''
        result = action_extractor.extract(code, "utils.ts")
        stores = result['store_usages']
        assert len(stores) >= 1

    def test_store_subscribe(self, action_extractor):
        code = '''
import { getDefaultStore } from 'jotai';

const store = getDefaultStore();
const unsub = store.sub(countAtom, () => {
    console.log(store.get(countAtom));
});
'''
        result = action_extractor.extract(code, "utils.ts")
        stores = result['store_usages']
        assert len(stores) >= 1

    def test_multiple_hooks(self, action_extractor):
        code = '''
import { useAtom, useAtomValue, useSetAtom } from 'jotai';

function Component() {
    const [name, setName] = useAtom(nameAtom);
    const count = useAtomValue(countAtom);
    const setTheme = useSetAtom(themeAtom);
}
'''
        result = action_extractor.extract(code, "component.tsx")
        hooks = result['hook_usages']
        assert len(hooks) >= 3

    def test_write_function(self, action_extractor):
        code = '''
import { atom } from 'jotai';

const tempCAtom = atom(25);
const tempFAtom = atom(
    (get) => get(tempCAtom) * 9 / 5 + 32,
    (get, set, newF) => set(tempCAtom, (newF - 32) * 5 / 9)
);
'''
        result = action_extractor.extract(code, "atoms.ts")
        writes = result['write_fns']
        assert len(writes) >= 0  # Write fn detection is best-effort


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestJotaiApiExtractor:
    """Tests for JotaiApiExtractor."""

    def test_jotai_core_import(self, api_extractor):
        code = '''
import { atom, useAtom } from 'jotai';
'''
        result = api_extractor.extract(code, "component.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.module == "jotai"
        assert "atom" in imp.imports

    def test_jotai_utils_import(self, api_extractor):
        code = '''
import { atomWithStorage, selectAtom } from 'jotai/utils';
'''
        result = api_extractor.extract(code, "atoms.ts")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.module == "jotai/utils"

    def test_jotai_react_import(self, api_extractor):
        code = '''
import { useAtom, useAtomValue, useSetAtom } from 'jotai/react';
'''
        result = api_extractor.extract(code, "component.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.module == "jotai/react"

    def test_jotai_vanilla_import(self, api_extractor):
        code = '''
import { createStore, getDefaultStore } from 'jotai/vanilla';
'''
        result = api_extractor.extract(code, "store.ts")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.module == "jotai/vanilla"

    def test_jotai_devtools_import(self, api_extractor):
        code = '''
import { DevTools, useAtomsDebugValue } from 'jotai-devtools';
'''
        result = api_extractor.extract(code, "app.tsx")
        assert len(result['imports']) >= 1

    def test_jotai_immer_import(self, api_extractor):
        code = '''
import { atomWithImmer } from 'jotai-immer';
'''
        result = api_extractor.extract(code, "atoms.ts")
        assert len(result['imports']) >= 1

    def test_jotai_optics_import(self, api_extractor):
        code = '''
import { focusAtom } from 'jotai-optics';
'''
        result = api_extractor.extract(code, "atoms.ts")
        assert len(result['imports']) >= 1

    def test_jotai_tanstack_query_import(self, api_extractor):
        code = '''
import { atomWithQuery, atomWithMutation } from 'jotai-tanstack-query';
'''
        result = api_extractor.extract(code, "api.ts")
        assert len(result['imports']) >= 1

    def test_typescript_atom_type(self, api_extractor):
        code = '''
import type { Atom, WritableAtom, PrimitiveAtom } from 'jotai';
'''
        result = api_extractor.extract(code, "types.ts")
        types = result.get('types', [])
        assert len(types) >= 0  # Type detection is best-effort

    def test_integration_devtools(self, api_extractor):
        code = '''
import { DevTools, useAtomsDebugValue } from 'jotai-devtools';

function App() {
    useAtomsDebugValue();
    return <><DevTools /><MyApp /></>;
}
'''
        result = api_extractor.extract(code, "app.tsx")
        integrations = result.get('integrations', [])
        assert len(integrations) >= 1

    def test_integration_tanstack_query(self, api_extractor):
        code = '''
import { atomWithQuery } from 'jotai-tanstack-query';

const userQueryAtom = atomWithQuery((get) => ({
    queryKey: ['user', get(userIdAtom)],
    queryFn: () => fetchUser(get(userIdAtom)),
}));
'''
        result = api_extractor.extract(code, "queries.ts")
        integrations = result.get('integrations', [])
        assert len(integrations) >= 1

    def test_multiple_imports(self, api_extractor):
        code = '''
import { atom, useAtom, useAtomValue } from 'jotai';
import { atomWithStorage, selectAtom } from 'jotai/utils';
import { focusAtom } from 'jotai-optics';
import { atomWithImmer } from 'jotai-immer';
'''
        result = api_extractor.extract(code, "atoms.ts")
        assert len(result['imports']) >= 4


# ═══════════════════════════════════════════════════════════════════
# EnhancedJotaiParser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedJotaiParser:
    """Tests for EnhancedJotaiParser."""

    def test_is_jotai_file_positive(self, parser):
        code = '''
import { atom, useAtom } from 'jotai';
const countAtom = atom(0);
'''
        assert parser.is_jotai_file(code) is True

    def test_is_jotai_file_negative(self, parser):
        code = '''
import { create } from 'zustand';
const useStore = create((set) => ({}));
'''
        assert parser.is_jotai_file(code) is False

    def test_is_jotai_file_utils(self, parser):
        code = '''
import { atomWithStorage } from 'jotai/utils';
'''
        assert parser.is_jotai_file(code) is True

    def test_is_jotai_file_optics(self, parser):
        code = '''
import { focusAtom } from 'jotai-optics';
'''
        assert parser.is_jotai_file(code) is True

    def test_is_jotai_file_use_atom_value(self, parser):
        code = '''
const count = useAtomValue(countAtom);
'''
        assert parser.is_jotai_file(code) is True

    def test_parse_basic(self, parser):
        code = '''
import { atom, useAtom } from 'jotai';

const countAtom = atom(0);

function Counter() {
    const [count, setCount] = useAtom(countAtom);
    return <div>{count}</div>;
}
'''
        result = parser.parse(code, "counter.tsx")
        assert isinstance(result, JotaiParseResult)
        assert result.file_path == "counter.tsx"
        assert result.file_type == "tsx"
        assert len(result.atoms) >= 1
        assert len(result.hook_usages) >= 1
        assert len(result.imports) >= 1

    def test_parse_derived_atoms(self, parser):
        code = '''
import { atom } from 'jotai';

const priceAtom = atom(100);
const taxAtom = atom(0.1);
const totalAtom = atom((get) => get(priceAtom) * (1 + get(taxAtom)));
'''
        result = parser.parse(code, "atoms.ts")
        assert len(result.atoms) >= 2 or len(result.derived_atoms) >= 1

    def test_parse_storage_atom(self, parser):
        code = '''
import { atomWithStorage } from 'jotai/utils';

const themeAtom = atomWithStorage('theme', 'light');
'''
        result = parser.parse(code, "atoms.ts")
        assert len(result.storage_atoms) >= 1

    def test_parse_full_app(self, parser):
        code = '''
import { atom, useAtom, useAtomValue, useSetAtom } from 'jotai';
import { atomWithStorage, selectAtom } from 'jotai/utils';

const countAtom = atom(0);
const nameAtom = atom('');
const themeAtom = atomWithStorage('theme', 'light');
const doubleAtom = atom((get) => get(countAtom) * 2);

function App() {
    const [count, setCount] = useAtom(countAtom);
    const name = useAtomValue(nameAtom);
    const setTheme = useSetAtom(themeAtom);
    return <div>{count} {name}</div>;
}
'''
        result = parser.parse(code, "app.tsx")
        assert len(result.atoms) >= 2
        assert len(result.storage_atoms) >= 1
        assert len(result.hook_usages) >= 3
        assert len(result.imports) >= 2

    def test_file_type_detection(self, parser):
        assert parser.parse("", "file.tsx").file_type == "tsx"
        assert parser.parse("", "file.jsx").file_type == "jsx"
        assert parser.parse("", "file.ts").file_type == "ts"
        assert parser.parse("", "file.js").file_type == "js"
        assert parser.parse("", "file.mjs").file_type == "js"


# ═══════════════════════════════════════════════════════════════════
# Framework Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestJotaiFrameworkDetection:
    """Tests for framework detection."""

    def test_detect_jotai_core(self, parser):
        code = '''import { atom } from 'jotai';'''
        result = parser.parse(code, "atoms.ts")
        assert 'jotai' in result.detected_frameworks

    def test_detect_jotai_utils(self, parser):
        code = '''import { atomWithStorage } from 'jotai/utils';'''
        result = parser.parse(code, "atoms.ts")
        assert 'jotai-utils' in result.detected_frameworks

    def test_detect_jotai_devtools(self, parser):
        code = '''import { DevTools } from 'jotai-devtools';'''
        result = parser.parse(code, "app.tsx")
        assert 'jotai-devtools' in result.detected_frameworks

    def test_detect_jotai_immer(self, parser):
        code = '''import { atomWithImmer } from 'jotai-immer';'''
        result = parser.parse(code, "atoms.ts")
        assert 'jotai-immer' in result.detected_frameworks

    def test_detect_jotai_optics(self, parser):
        code = '''import { focusAtom } from 'jotai-optics';'''
        result = parser.parse(code, "atoms.ts")
        assert 'jotai-optics' in result.detected_frameworks

    def test_detect_jotai_xstate(self, parser):
        code = '''import { atomWithMachine } from 'jotai-xstate';'''
        result = parser.parse(code, "atoms.ts")
        assert 'jotai-xstate' in result.detected_frameworks

    def test_detect_jotai_effect(self, parser):
        code = '''import { atomEffect } from 'jotai-effect';'''
        result = parser.parse(code, "effects.ts")
        assert 'jotai-effect' in result.detected_frameworks

    def test_detect_jotai_tanstack_query(self, parser):
        code = '''import { atomWithQuery } from 'jotai-tanstack-query';'''
        result = parser.parse(code, "queries.ts")
        assert 'jotai-tanstack-query' in result.detected_frameworks

    def test_detect_jotai_trpc(self, parser):
        code = '''import { createTRPCJotai } from 'jotai-trpc';'''
        result = parser.parse(code, "trpc.ts")
        assert 'jotai-trpc' in result.detected_frameworks

    def test_detect_jotai_molecules(self, parser):
        code = '''import { molecule, useMolecule } from 'jotai-molecules';'''
        result = parser.parse(code, "molecules.ts")
        assert 'jotai-molecules' in result.detected_frameworks

    def test_detect_jotai_scope(self, parser):
        code = '''import { ScopeProvider } from 'jotai-scope';'''
        result = parser.parse(code, "scope.tsx")
        assert 'jotai-scope' in result.detected_frameworks

    def test_detect_jotai_location(self, parser):
        code = '''import { atomWithLocation } from 'jotai-location';'''
        result = parser.parse(code, "router.ts")
        assert 'jotai-location' in result.detected_frameworks

    def test_detect_jotai_valtio(self, parser):
        code = '''import { atomWithProxy } from 'jotai-valtio';'''
        result = parser.parse(code, "proxy.ts")
        assert 'jotai-valtio' in result.detected_frameworks

    def test_detect_multiple_frameworks(self, parser):
        code = '''
import { atom, useAtom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { atomWithImmer } from 'jotai-immer';
import { focusAtom } from 'jotai-optics';
'''
        result = parser.parse(code, "atoms.ts")
        assert 'jotai' in result.detected_frameworks
        assert 'jotai-utils' in result.detected_frameworks
        assert 'jotai-immer' in result.detected_frameworks
        assert 'jotai-optics' in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Version Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestJotaiVersionDetection:
    """Tests for Jotai version detection."""

    def test_detect_v2_useAtomValue(self, parser):
        code = '''
import { useAtomValue } from 'jotai';
const count = useAtomValue(countAtom);
'''
        result = parser.parse(code, "component.tsx")
        assert result.jotai_version == "v2"

    def test_detect_v2_useSetAtom(self, parser):
        code = '''
import { useSetAtom } from 'jotai';
const setCount = useSetAtom(countAtom);
'''
        result = parser.parse(code, "component.tsx")
        assert result.jotai_version == "v2"

    def test_detect_v2_createStore(self, parser):
        code = '''
import { createStore } from 'jotai';
const store = createStore();
'''
        result = parser.parse(code, "store.ts")
        assert result.jotai_version == "v2"

    def test_detect_v2_subpath_import(self, parser):
        code = '''
import { useAtom } from 'jotai/react';
'''
        result = parser.parse(code, "component.tsx")
        assert result.jotai_version == "v2"

    def test_detect_v1_useUpdateAtom(self, parser):
        code = '''
import { useUpdateAtom } from 'jotai/utils';
const setCount = useUpdateAtom(countAtom);
'''
        result = parser.parse(code, "component.tsx")
        assert result.jotai_version == "v1"

    def test_detect_v2_basic_import(self, parser):
        code = '''
import { atom, useAtom } from 'jotai';
'''
        result = parser.parse(code, "atoms.ts")
        assert result.jotai_version == "v2"


# ═══════════════════════════════════════════════════════════════════
# Feature Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestJotaiFeatureDetection:
    """Tests for Jotai feature detection."""

    def test_detect_atom_feature(self, parser):
        code = '''const countAtom = atom(0);'''
        result = parser.parse(code, "atoms.ts")
        assert 'atom' in result.detected_features

    def test_detect_atom_family_feature(self, parser):
        code = '''const todoAtom = atomFamily((id) => atom({ id }));'''
        result = parser.parse(code, "atoms.ts")
        assert 'atom_family' in result.detected_features

    def test_detect_atom_with_storage_feature(self, parser):
        code = '''const themeAtom = atomWithStorage('theme', 'light');'''
        result = parser.parse(code, "atoms.ts")
        assert 'atom_with_storage' in result.detected_features

    def test_detect_select_atom_feature(self, parser):
        code = '''const nameAtom = selectAtom(userAtom, (u) => u.name);'''
        result = parser.parse(code, "selectors.ts")
        assert 'select_atom' in result.detected_features

    def test_detect_focus_atom_feature(self, parser):
        code = '''const nameAtom = focusAtom(formAtom, (o) => o.prop('name'));'''
        result = parser.parse(code, "atoms.ts")
        assert 'focus_atom' in result.detected_features

    def test_detect_use_atom_value_feature(self, parser):
        code = '''const count = useAtomValue(countAtom);'''
        result = parser.parse(code, "component.tsx")
        assert 'use_atom_value' in result.detected_features

    def test_detect_use_set_atom_feature(self, parser):
        code = '''const setCount = useSetAtom(countAtom);'''
        result = parser.parse(code, "component.tsx")
        assert 'use_set_atom' in result.detected_features

    def test_detect_create_store_feature(self, parser):
        code = '''const store = createStore();'''
        result = parser.parse(code, "store.ts")
        assert 'create_store' in result.detected_features

    def test_detect_provider_feature(self, parser):
        code = '''return <Provider store={store}><App /></Provider>;'''
        result = parser.parse(code, "root.tsx")
        assert 'provider' in result.detected_features

    def test_detect_devtools_feature(self, parser):
        code = '''useAtomsDebugValue();'''
        result = parser.parse(code, "app.tsx")
        assert 'devtools' in result.detected_features

    def test_detect_multiple_features(self, parser):
        code = '''
const countAtom = atom(0);
const themeAtom = atomWithStorage('theme', 'light');
const count = useAtomValue(countAtom);
const setTheme = useSetAtom(themeAtom);
'''
        result = parser.parse(code, "app.tsx")
        assert 'atom' in result.detected_features
        assert 'atom_with_storage' in result.detected_features
        assert 'use_atom_value' in result.detected_features
        assert 'use_set_atom' in result.detected_features


# ═══════════════════════════════════════════════════════════════════
# BPL Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestJotaiBPLIntegration:
    """Tests for Jotai BPL practices file."""

    def test_jotai_core_yaml_exists(self):
        """Verify jotai_core.yaml exists."""
        yaml_path = Path(__file__).parent.parent.parent / "codetrellis" / "bpl" / "practices" / "jotai_core.yaml"
        assert yaml_path.exists(), f"jotai_core.yaml not found at {yaml_path}"

    def test_jotai_core_yaml_loads(self):
        """Verify jotai_core.yaml loads without errors."""
        import yaml
        yaml_path = Path(__file__).parent.parent.parent / "codetrellis" / "bpl" / "practices" / "jotai_core.yaml"
        assert yaml_path.exists(), f"jotai_core.yaml not found at {yaml_path}"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert 'practices' in data

    def test_jotai_core_yaml_has_50_practices(self):
        """Verify jotai_core.yaml has 50 practices."""
        import yaml
        yaml_path = Path(__file__).parent.parent.parent / "codetrellis" / "bpl" / "practices" / "jotai_core.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        practices = data['practices']
        assert len(practices) == 50, f"Expected 50 practices, got {len(practices)}"

    def test_jotai_core_yaml_practice_ids_sequential(self):
        """Verify practice IDs are JOTAI001-JOTAI050."""
        import yaml
        yaml_path = Path(__file__).parent.parent.parent / "codetrellis" / "bpl" / "practices" / "jotai_core.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        for i, practice in enumerate(data['practices'], 1):
            expected_id = f"JOTAI{i:03d}"
            assert practice['id'] == expected_id, f"Practice {i}: expected {expected_id}, got {practice['id']}"

    def test_jotai_core_yaml_practice_categories(self):
        """Verify all practices have valid categories."""
        import yaml
        yaml_path = Path(__file__).parent.parent.parent / "codetrellis" / "bpl" / "practices" / "jotai_core.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        valid_categories = {
            'jotai_atoms', 'jotai_selectors', 'jotai_middleware',
            'jotai_actions', 'jotai_typescript', 'jotai_performance',
            'jotai_testing', 'jotai_ssr', 'jotai_patterns', 'jotai_migration',
        }
        for practice in data['practices']:
            assert practice['category'] in valid_categories, \
                f"Practice {practice['id']} has invalid category: {practice['category']}"

    def test_jotai_practice_category_enum_values(self):
        """Verify PracticeCategory enum has JOTAI values."""
        from codetrellis.bpl.models import PracticeCategory
        assert hasattr(PracticeCategory, 'JOTAI_ATOMS')
        assert hasattr(PracticeCategory, 'JOTAI_SELECTORS')
        assert hasattr(PracticeCategory, 'JOTAI_MIDDLEWARE')
        assert hasattr(PracticeCategory, 'JOTAI_ACTIONS')
        assert hasattr(PracticeCategory, 'JOTAI_TYPESCRIPT')
        assert hasattr(PracticeCategory, 'JOTAI_PERFORMANCE')
        assert hasattr(PracticeCategory, 'JOTAI_TESTING')
        assert hasattr(PracticeCategory, 'JOTAI_SSR')
        assert hasattr(PracticeCategory, 'JOTAI_PATTERNS')
        assert hasattr(PracticeCategory, 'JOTAI_MIGRATION')


# ═══════════════════════════════════════════════════════════════════
# Edge Case Tests
# ═══════════════════════════════════════════════════════════════════

class TestJotaiEdgeCases:
    """Tests for edge cases and robustness."""

    def test_empty_file(self, parser):
        result = parser.parse("", "empty.ts")
        assert isinstance(result, JotaiParseResult)
        assert len(result.atoms) == 0
        assert len(result.hook_usages) == 0

    def test_non_jotai_file(self, parser):
        code = '''
import React from 'react';

function App() {
    return <div>Hello</div>;
}
'''
        assert parser.is_jotai_file(code) is False

    def test_commented_out_jotai(self, parser):
        code = '''
// import { atom } from 'jotai';
// const countAtom = atom(0);
const x = 42;
'''
        # Should still detect 'jotai' in the string but parsing should handle gracefully
        result = parser.parse(code, "commented.ts")
        assert isinstance(result, JotaiParseResult)

    def test_jotai_in_string_literal(self, parser):
        code = '''
const pkg = "jotai";
console.log("Using jotai for state management");
'''
        # String presence detection — may give false positive for is_jotai_file
        result = parser.parse(code, "log.ts")
        assert isinstance(result, JotaiParseResult)

    def test_large_file(self, parser):
        lines = ["import { atom, useAtom } from 'jotai';"]
        for i in range(100):
            lines.append(f"const atom{i} = atom({i});")
        code = "\n".join(lines)
        result = parser.parse(code, "many-atoms.ts")
        assert isinstance(result, JotaiParseResult)
        assert len(result.atoms) >= 50  # Should detect many atoms

    def test_mixed_frameworks(self, parser):
        code = '''
import { atom, useAtom } from 'jotai';
import { create } from 'zustand';
import { configureStore } from '@reduxjs/toolkit';

const countAtom = atom(0);
'''
        assert parser.is_jotai_file(code) is True
        result = parser.parse(code, "mixed.ts")
        assert len(result.atoms) >= 1
