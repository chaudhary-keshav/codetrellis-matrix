"""
Tests for Recoil extractors and EnhancedRecoilParser.

Part of CodeTrellis v4.50 Recoil State Management Framework Support.
Tests cover:
- Atom extraction (atom, atomFamily, effects, dangerouslyAllowMutability)
- Selector extraction (selector, selectorFamily, constSelector, errorSelector,
                       waitForAll, waitForAny, waitForNone, waitForAllSettled, noWait)
- Effect extraction (persistence, logging, validation, sync, broadcast, custom)
- Hook extraction (useRecoilState, useRecoilValue, useSetRecoilState,
                   useResetRecoilState, useRecoilStateLoadable,
                   useRecoilValueLoadable, useRecoilCallback,
                   useRecoilTransaction_UNSTABLE, useRecoilRefresher_UNSTABLE,
                   useRecoilBridgeAcrossReactRoots_UNSTABLE)
- API extraction (imports, Snapshot API, RecoilRoot, TypeScript types, recoil-sync)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from pathlib import Path
from codetrellis.recoil_parser_enhanced import (
    EnhancedRecoilParser,
    RecoilParseResult,
)
from codetrellis.extractors.recoil import (
    RecoilAtomExtractor,
    RecoilSelectorExtractor,
    RecoilEffectExtractor,
    RecoilHookExtractor,
    RecoilApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedRecoilParser()


@pytest.fixture
def atom_extractor():
    return RecoilAtomExtractor()


@pytest.fixture
def selector_extractor():
    return RecoilSelectorExtractor()


@pytest.fixture
def effect_extractor():
    return RecoilEffectExtractor()


@pytest.fixture
def hook_extractor():
    return RecoilHookExtractor()


@pytest.fixture
def api_extractor():
    return RecoilApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Atom Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRecoilAtomExtractor:
    """Tests for RecoilAtomExtractor."""

    def test_basic_atom_number_default(self, atom_extractor):
        code = '''
import { atom } from 'recoil';

const countAtom = atom({
  key: 'count',
  default: 0,
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        a = result['atoms'][0]
        assert a.name == "countAtom"
        assert a.key == "count"

    def test_basic_atom_string_default(self, atom_extractor):
        code = '''
import { atom } from 'recoil';

const nameAtom = atom({
  key: 'name',
  default: '',
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        assert result['atoms'][0].name == "nameAtom"
        assert result['atoms'][0].key == "name"

    def test_basic_atom_boolean_default(self, atom_extractor):
        code = '''
import { atom } from 'recoil';

const isDarkAtom = atom({
  key: 'isDark',
  default: false,
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        assert result['atoms'][0].name == "isDarkAtom"

    def test_atom_with_null_default(self, atom_extractor):
        code = '''
import { atom } from 'recoil';

const userAtom = atom({
  key: 'currentUser',
  default: null,
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        assert result['atoms'][0].name == "userAtom"
        assert result['atoms'][0].key == "currentUser"

    def test_atom_with_array_default(self, atom_extractor):
        code = '''
import { atom } from 'recoil';

const itemsAtom = atom({
  key: 'items',
  default: [],
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        assert result['atoms'][0].name == "itemsAtom"

    def test_atom_with_effects(self, atom_extractor):
        code = '''
import { atom } from 'recoil';

const persistedAtom = atom({
  key: 'persisted',
  default: '',
  effects: [
    ({ setSelf, onSet }) => {
      setSelf(localStorage.getItem('persisted') ?? '');
      onSet((newValue) => localStorage.setItem('persisted', newValue));
    },
  ],
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        a = result['atoms'][0]
        assert a.name == "persistedAtom"
        assert a.has_effects is True

    def test_atom_with_dangerously_allow_mutability(self, atom_extractor):
        code = '''
import { atom } from 'recoil';

const mapAtom = atom({
  key: 'myMap',
  default: new Map(),
  dangerouslyAllowMutability: true,
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        a = result['atoms'][0]
        assert a.name == "mapAtom"
        assert a.has_dangerously_allow_mutability is True

    def test_atom_with_typescript_generic(self, atom_extractor):
        code = '''
import { atom } from 'recoil';

const userAtom = atom<User | null>({
  key: 'user',
  default: null,
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 1
        assert result['atoms'][0].name == "userAtom"

    def test_atom_family_basic(self, atom_extractor):
        code = '''
import { atomFamily } from 'recoil';

const todoAtom = atomFamily({
  key: 'todo',
  default: (id) => ({ id, text: '', completed: false }),
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atom_families']) >= 1
        af = result['atom_families'][0]
        assert af.name == "todoAtom"
        assert af.key == "todo"

    def test_atom_family_with_typescript_generics(self, atom_extractor):
        code = '''
import { atomFamily } from 'recoil';

const itemAtom = atomFamily<ItemState, string>({
  key: 'item',
  default: { quantity: 0, price: 0 },
});
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atom_families']) >= 1
        assert result['atom_families'][0].name == "itemAtom"

    def test_multiple_atoms(self, atom_extractor):
        code = '''
import { atom } from 'recoil';

const countAtom = atom({ key: 'count', default: 0 });
const nameAtom = atom({ key: 'name', default: '' });
const isDarkAtom = atom({ key: 'isDark', default: false });
'''
        result = atom_extractor.extract(code, "atoms.ts")
        assert len(result['atoms']) >= 3


# ═══════════════════════════════════════════════════════════════════
# Selector Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRecoilSelectorExtractor:
    """Tests for RecoilSelectorExtractor."""

    def test_basic_read_only_selector(self, selector_extractor):
        code = '''
import { selector } from 'recoil';

const filteredTodosSelector = selector({
  key: 'filteredTodos',
  get: ({ get }) => {
    const filter = get(filterAtom);
    const todos = get(todosAtom);
    return todos.filter(t => filter === 'all' || t.status === filter);
  },
});
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['selectors']) >= 1
        s = result['selectors'][0]
        assert s.name == "filteredTodosSelector"
        assert s.key == "filteredTodos"
        assert s.is_writable is False

    def test_writable_selector(self, selector_extractor):
        code = '''
import { selector, DefaultValue } from 'recoil';

const tempFSelector = selector({
  key: 'tempFahrenheit',
  get: ({ get }) => get(tempCAtom) * 9/5 + 32,
  set: ({ set }, newValue) => {
    if (newValue instanceof DefaultValue) { set(tempCAtom, newValue); return; }
    set(tempCAtom, (newValue - 32) * 5/9);
  },
});
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['selectors']) >= 1
        s = result['selectors'][0]
        assert s.name == "tempFSelector"
        assert s.is_writable is True

    def test_async_selector(self, selector_extractor):
        code = '''
import { selector } from 'recoil';

const userDataSelector = selector({
  key: 'userData',
  get: async ({ get }) => {
    const userId = get(userIdAtom);
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
  },
});
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['selectors']) >= 1
        s = result['selectors'][0]
        assert s.name == "userDataSelector"
        assert s.is_async is True

    def test_selector_family(self, selector_extractor):
        code = '''
import { selectorFamily } from 'recoil';

const todoByIdSelector = selectorFamily({
  key: 'todoById',
  get: (id) => ({ get }) => get(todoListAtom).find(t => t.id === id),
});
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['selector_families']) >= 1
        sf = result['selector_families'][0]
        assert sf.name == "todoByIdSelector"
        assert sf.key == "todoById"

    def test_const_selector(self, selector_extractor):
        code = '''
import { constSelector } from 'recoil';

const alwaysZero = constSelector(0);
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['selectors']) >= 1

    def test_error_selector(self, selector_extractor):
        code = '''
import { errorSelector } from 'recoil';

const alwaysFails = errorSelector(new Error('Not implemented'));
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['selectors']) >= 1

    def test_wait_for_all(self, selector_extractor):
        code = '''
import { selector, waitForAll } from 'recoil';

const dashboardSelector = selector({
  key: 'dashboard',
  get: ({ get }) => {
    const [user, posts] = get(waitForAll([userSelector, postsSelector]));
    return { user, posts };
  },
});
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['selectors']) >= 1

    def test_no_wait(self, selector_extractor):
        code = '''
import { selector, noWait } from 'recoil';

const statusSelector = selector({
  key: 'status',
  get: ({ get }) => {
    const loadable = get(noWait(asyncDataSelector));
    return loadable.state === 'hasValue' ? loadable.contents : 'Loading...';
  },
});
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['selectors']) >= 1

    def test_selector_with_typescript_generic(self, selector_extractor):
        code = '''
import { selectorFamily } from 'recoil';

const userByIdSelector = selectorFamily<User | undefined, string>({
  key: 'userById',
  get: (id) => ({ get }) => get(usersAtom).find(u => u.id === id),
});
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['selector_families']) >= 1

    def test_wait_for_all_settled(self, selector_extractor):
        code = '''
import { selector, waitForAllSettled } from 'recoil';

const resilientSelector = selector({
  key: 'resilient',
  get: ({ get }) => {
    const loadables = get(waitForAllSettled([apiA, apiB, apiC]));
    return loadables.filter(l => l.state === 'hasValue').map(l => l.contents);
  },
});
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['selectors']) >= 1

    def test_wait_for_any(self, selector_extractor):
        code = '''
import { selector, waitForAny } from 'recoil';

const fastestSelector = selector({
  key: 'fastest',
  get: ({ get }) => get(waitForAny([sourceA, sourceB])),
});
'''
        result = selector_extractor.extract(code, "selectors.ts")
        assert len(result['selectors']) >= 1


# ═══════════════════════════════════════════════════════════════════
# Effect Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRecoilEffectExtractor:
    """Tests for RecoilEffectExtractor."""

    def test_local_storage_effect(self, effect_extractor):
        code = '''
const localStorageEffect = (key) => ({ setSelf, onSet }) => {
  const saved = localStorage.getItem(key);
  if (saved != null) setSelf(JSON.parse(saved));
  onSet((newValue, _, isReset) => {
    isReset ? localStorage.removeItem(key) : localStorage.setItem(key, JSON.stringify(newValue));
  });
};
'''
        result = effect_extractor.extract(code, "effects.ts")
        assert len(result['effects']) >= 1
        eff = result['effects'][0]
        assert eff.name == "localStorageEffect"
        assert eff.effect_type == "persistence"

    def test_logging_effect(self, effect_extractor):
        code = '''
const loggingEffect = ({ onSet }) => {
  onSet((newValue, oldValue) => {
    console.log('State changed:', oldValue, '->', newValue);
  });
};
'''
        result = effect_extractor.extract(code, "effects.ts")
        assert len(result['effects']) >= 1
        eff = result['effects'][0]
        assert eff.name == "loggingEffect"

    def test_effect_with_cleanup(self, effect_extractor):
        code = '''
const wsEffect = ({ setSelf }) => {
  const ws = new WebSocket('ws://example.com');
  ws.onmessage = (e) => setSelf(JSON.parse(e.data));
  return () => ws.close();
};
'''
        result = effect_extractor.extract(code, "effects.ts")
        assert len(result['effects']) >= 1
        eff = result['effects'][0]
        assert eff.name == "wsEffect"
        assert eff.has_cleanup is True

    def test_parameterized_effect(self, effect_extractor):
        code = '''
const syncEffect = (url) => ({ setSelf, onSet }) => {
  fetch(url).then(r => r.json()).then(data => setSelf(data));
  onSet((newValue) => {
    fetch(url, { method: 'PUT', body: JSON.stringify(newValue) });
  });
};
'''
        result = effect_extractor.extract(code, "effects.ts")
        assert len(result['effects']) >= 1
        eff = result['effects'][0]
        assert eff.is_factory is True

    def test_effect_with_on_set_and_set_self(self, effect_extractor):
        code = '''
const persistEffect = ({ setSelf, onSet, resetSelf }) => {
  const saved = sessionStorage.getItem('key');
  if (saved != null) setSelf(JSON.parse(saved));
  onSet((newValue) => {
    sessionStorage.setItem('key', JSON.stringify(newValue));
  });
};
'''
        result = effect_extractor.extract(code, "effects.ts")
        assert len(result['effects']) >= 1
        eff = result['effects'][0]
        assert eff.has_on_set is True
        assert eff.has_set_self is True

    def test_validation_effect(self, effect_extractor):
        code = '''
const validationEffect = ({ onSet }) => {
  onSet((newValue) => {
    if (!isValid(newValue)) {
      throw new Error('Invalid state');
    }
  });
};
'''
        result = effect_extractor.extract(code, "effects.ts")
        assert len(result['effects']) >= 1


# ═══════════════════════════════════════════════════════════════════
# Hook Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRecoilHookExtractor:
    """Tests for RecoilHookExtractor."""

    def test_use_recoil_state(self, hook_extractor):
        code = '''
import { useRecoilState } from 'recoil';

function Counter() {
  const [count, setCount] = useRecoilState(countAtom);
  return <div>{count}</div>;
}
'''
        result = hook_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 1
        hu = result['hook_usages'][0]
        assert hu.hook_name == "useRecoilState"
        assert hu.atom_name == "countAtom"

    def test_use_recoil_value(self, hook_extractor):
        code = '''
import { useRecoilValue } from 'recoil';

function Display() {
  const count = useRecoilValue(countAtom);
  return <div>{count}</div>;
}
'''
        result = hook_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 1
        hu = result['hook_usages'][0]
        assert hu.hook_name == "useRecoilValue"
        assert hu.atom_name == "countAtom"

    def test_use_set_recoil_state(self, hook_extractor):
        code = '''
import { useSetRecoilState } from 'recoil';

function Incrementer() {
  const setCount = useSetRecoilState(countAtom);
  return <button onClick={() => setCount(c => c + 1)}>+</button>;
}
'''
        result = hook_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 1
        hu = result['hook_usages'][0]
        assert hu.hook_name == "useSetRecoilState"

    def test_use_reset_recoil_state(self, hook_extractor):
        code = '''
import { useResetRecoilState } from 'recoil';

function ResetButton() {
  const resetCount = useResetRecoilState(countAtom);
  return <button onClick={resetCount}>Reset</button>;
}
'''
        result = hook_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 1
        hu = result['hook_usages'][0]
        assert hu.hook_name == "useResetRecoilState"

    def test_use_recoil_state_loadable(self, hook_extractor):
        code = '''
import { useRecoilStateLoadable } from 'recoil';

function AsyncComponent() {
  const [userLoadable, setUser] = useRecoilStateLoadable(userSelector);
  if (userLoadable.state === 'loading') return <Spinner />;
  return <div>{userLoadable.contents.name}</div>;
}
'''
        result = hook_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 1
        hu = result['hook_usages'][0]
        assert hu.hook_name == "useRecoilStateLoadable"

    def test_use_recoil_value_loadable(self, hook_extractor):
        code = '''
import { useRecoilValueLoadable } from 'recoil';

function AsyncDisplay() {
  const dataLoadable = useRecoilValueLoadable(asyncSelector);
  switch (dataLoadable.state) {
    case 'hasValue': return <div>{dataLoadable.contents}</div>;
    case 'loading': return <Spinner />;
    case 'hasError': return <Error />;
  }
}
'''
        result = hook_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 1
        hu = result['hook_usages'][0]
        assert hu.hook_name == "useRecoilValueLoadable"

    def test_use_recoil_callback(self, hook_extractor):
        code = '''
import { useRecoilCallback } from 'recoil';

function SaveButton() {
  const saveAll = useRecoilCallback(({ snapshot, set }) => async () => {
    const items = await snapshot.getPromise(itemsAtom);
    await api.save(items);
    set(lastSavedAtom, new Date());
  });
  return <button onClick={saveAll}>Save</button>;
}
'''
        result = hook_extractor.extract(code, "component.tsx")
        assert len(result['callbacks']) >= 1
        cb = result['callbacks'][0]
        assert cb.callback_type == "callback"
        assert cb.uses_snapshot is True
        assert cb.uses_set is True

    def test_use_recoil_transaction(self, hook_extractor):
        code = '''
import { useRecoilTransaction_UNSTABLE } from 'recoil';

function ResetAll() {
  const resetAll = useRecoilTransaction_UNSTABLE(({ set, reset }) => () => {
    reset(countAtom);
    reset(nameAtom);
    set(timestampAtom, Date.now());
  });
  return <button onClick={resetAll}>Reset All</button>;
}
'''
        result = hook_extractor.extract(code, "component.tsx")
        assert len(result['callbacks']) >= 1
        cb = result['callbacks'][0]
        assert cb.callback_type == "transaction"

    def test_use_recoil_refresher(self, hook_extractor):
        code = '''
import { useRecoilRefresher_UNSTABLE } from 'recoil';

function RefreshButton() {
  const refreshUser = useRecoilRefresher_UNSTABLE(userSelector);
  return <button onClick={refreshUser}>Refresh</button>;
}
'''
        result = hook_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 1
        hu = result['hook_usages'][0]
        assert hu.hook_name == "useRecoilRefresher_UNSTABLE"

    def test_use_recoil_bridge(self, hook_extractor):
        code = '''
import { useRecoilBridgeAcrossReactRoots_UNSTABLE } from 'recoil';

function ParentApp() {
  const RecoilBridge = useRecoilBridgeAcrossReactRoots_UNSTABLE();
  return <RecoilBridge><ChildApp /></RecoilBridge>;
}
'''
        result = hook_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 1
        hu = result['hook_usages'][0]
        assert hu.hook_name == "useRecoilBridgeAcrossReactRoots_UNSTABLE"

    def test_multiple_hooks_in_component(self, hook_extractor):
        code = '''
import { useRecoilState, useRecoilValue, useSetRecoilState } from 'recoil';

function MyComponent() {
  const [count, setCount] = useRecoilState(countAtom);
  const name = useRecoilValue(nameAtom);
  const setDark = useSetRecoilState(isDarkAtom);
  return <div>{count} {name}</div>;
}
'''
        result = hook_extractor.extract(code, "component.tsx")
        assert len(result['hook_usages']) >= 3


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRecoilApiExtractor:
    """Tests for RecoilApiExtractor."""

    def test_recoil_import(self, api_extractor):
        code = '''
import { atom, selector, useRecoilState, useRecoilValue } from 'recoil';
'''
        result = api_extractor.extract(code, "atoms.ts")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.module == "recoil"
        assert "atom" in imp.imports
        assert "selector" in imp.imports

    def test_recoil_sync_import(self, api_extractor):
        code = '''
import { syncEffect, urlSyncEffect } from 'recoil-sync';
'''
        result = api_extractor.extract(code, "sync.ts")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.module == "recoil-sync"

    def test_recoil_relay_import(self, api_extractor):
        code = '''
import { graphQLSelector } from 'recoil-relay';
'''
        result = api_extractor.extract(code, "relay.ts")
        assert len(result['imports']) >= 1

    def test_recoil_nexus_import(self, api_extractor):
        code = '''
import { getRecoil, setRecoil, resetRecoil } from 'recoil-nexus';
'''
        result = api_extractor.extract(code, "nexus.ts")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.module == "recoil-nexus"

    def test_recoil_persist_import(self, api_extractor):
        code = '''
import { recoilPersist } from 'recoil-persist';
'''
        result = api_extractor.extract(code, "persist.ts")
        assert len(result['imports']) >= 1

    def test_refine_import(self, api_extractor):
        code = '''
import { string, number, object } from '@recoiljs/refine';
'''
        result = api_extractor.extract(code, "refine.ts")
        assert len(result['imports']) >= 1
        assert result['imports'][0].module == "@recoiljs/refine"

    def test_type_import(self, api_extractor):
        code = '''
import type { RecoilState, RecoilValue } from 'recoil';
'''
        result = api_extractor.extract(code, "types.ts")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.is_type_import is True

    def test_snapshot_usage(self, api_extractor):
        code = '''
import { useRecoilSnapshot, useGotoRecoilSnapshot } from 'recoil';

function Debugger() {
  const snapshot = useRecoilSnapshot();
  const gotoSnapshot = useGotoRecoilSnapshot();
}
'''
        result = api_extractor.extract(code, "debugger.tsx")
        assert len(result['snapshot_usages']) >= 1

    def test_snapshot_unstable(self, api_extractor):
        code = '''
import { snapshot_UNSTABLE } from 'recoil';

test('selector test', () => {
  const snapshot = snapshot_UNSTABLE(({ set }) => {
    set(countAtom, 5);
  });
  expect(snapshot.getLoadable(doubledSelector).getValue()).toBe(10);
});
'''
        result = api_extractor.extract(code, "test.ts")
        assert len(result['snapshot_usages']) >= 1

    def test_recoil_root_detection(self, api_extractor):
        code = '''
import { RecoilRoot } from 'recoil';

function App() {
  return (
    <RecoilRoot initializeState={({ set }) => { set(countAtom, 0); }}>
      <Main />
    </RecoilRoot>
  );
}
'''
        result = api_extractor.extract(code, "app.tsx")
        # RecoilRoot should be detected
        assert len(result['imports']) >= 1

    def test_typescript_types(self, api_extractor):
        code = '''
import type {
  RecoilState,
  RecoilValue,
  RecoilValueReadOnly,
  Loadable,
  AtomEffect,
  Snapshot,
  CallbackInterface,
} from 'recoil';
'''
        result = api_extractor.extract(code, "types.ts")
        assert len(result['types']) >= 1

    def test_recoil_sync_components(self, api_extractor):
        code = '''
import { syncEffect } from 'recoil-sync';
import { RecoilURLSyncJSON } from 'recoil-sync';

const filterAtom = atom({
  key: 'filter',
  default: 'all',
  effects: [syncEffect({ refine: string() })],
});
'''
        result = api_extractor.extract(code, "sync.ts")
        assert len(result['imports']) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedRecoilParser:
    """Tests for EnhancedRecoilParser integration."""

    def test_is_recoil_file_positive(self, parser):
        code = '''
import { atom, useRecoilState } from 'recoil';
'''
        assert parser.is_recoil_file(code) is True

    def test_is_recoil_file_negative(self, parser):
        code = '''
import { useState } from 'react';
const count = useState(0);
'''
        assert parser.is_recoil_file(code) is False

    def test_is_recoil_file_recoil_sync(self, parser):
        code = '''
import { syncEffect } from 'recoil-sync';
'''
        assert parser.is_recoil_file(code) is True

    def test_is_recoil_file_recoil_nexus(self, parser):
        code = '''
import { getRecoil, setRecoil } from 'recoil-nexus';
'''
        assert parser.is_recoil_file(code) is True

    def test_is_recoil_file_recoil_persist(self, parser):
        code = '''
import { recoilPersist } from 'recoil-persist';
'''
        assert parser.is_recoil_file(code) is True

    def test_is_recoil_file_hook_usage(self, parser):
        code = '''
const [count, setCount] = useRecoilState(countAtom);
'''
        assert parser.is_recoil_file(code) is True

    def test_is_recoil_file_recoil_root(self, parser):
        code = '''
<RecoilRoot>
  <App />
</RecoilRoot>
'''
        assert parser.is_recoil_file(code) is True

    def test_parse_result_type(self, parser):
        code = '''
import { atom, useRecoilState } from 'recoil';

const countAtom = atom({ key: 'count', default: 0 });
'''
        result = parser.parse(code, "atoms.ts")
        assert isinstance(result, RecoilParseResult)

    def test_parse_file_type_tsx(self, parser):
        result = parser.parse("", "component.tsx")
        assert result.file_type == "tsx"

    def test_parse_file_type_jsx(self, parser):
        result = parser.parse("", "component.jsx")
        assert result.file_type == "jsx"

    def test_parse_file_type_ts(self, parser):
        result = parser.parse("", "atoms.ts")
        assert result.file_type == "ts"

    def test_parse_file_type_js(self, parser):
        result = parser.parse("", "atoms.js")
        assert result.file_type == "js"

    # ── Framework Detection ──────────────────────────────────────

    def test_detect_frameworks_recoil_core(self, parser):
        code = '''import { atom } from 'recoil';'''
        frameworks = parser._detect_frameworks(code)
        assert "recoil" in frameworks

    def test_detect_frameworks_recoil_sync(self, parser):
        code = '''import { syncEffect } from 'recoil-sync';'''
        frameworks = parser._detect_frameworks(code)
        assert "recoil-sync" in frameworks

    def test_detect_frameworks_recoil_relay(self, parser):
        code = '''import { graphQLSelector } from 'recoil-relay';'''
        frameworks = parser._detect_frameworks(code)
        assert "recoil-relay" in frameworks

    def test_detect_frameworks_recoil_nexus(self, parser):
        code = '''import { getRecoil } from 'recoil-nexus';'''
        frameworks = parser._detect_frameworks(code)
        assert "recoil-nexus" in frameworks

    def test_detect_frameworks_recoil_persist(self, parser):
        code = '''import { recoilPersist } from 'recoil-persist';'''
        frameworks = parser._detect_frameworks(code)
        assert "recoil-persist" in frameworks

    def test_detect_frameworks_refine(self, parser):
        code = '''import { string } from '@recoiljs/refine';'''
        frameworks = parser._detect_frameworks(code)
        assert "@recoiljs/refine" in frameworks

    def test_detect_frameworks_react(self, parser):
        code = '''import React from 'react';'''
        frameworks = parser._detect_frameworks(code)
        assert "react" in frameworks

    def test_detect_frameworks_react_native(self, parser):
        code = '''import { View } from 'react-native';'''
        frameworks = parser._detect_frameworks(code)
        assert "react-native" in frameworks

    def test_detect_frameworks_testing_library(self, parser):
        code = '''import { render } from '@testing-library/react';'''
        frameworks = parser._detect_frameworks(code)
        assert "testing-library" in frameworks

    # ── Feature Detection ────────────────────────────────────────

    def test_detect_features_atom(self, parser):
        code = '''const countAtom = atom({ key: 'count', default: 0 });'''
        features = parser._detect_features(code)
        assert "atom" in features

    def test_detect_features_atom_family(self, parser):
        code = '''const todoAtom = atomFamily({ key: 'todo', default: 0 });'''
        features = parser._detect_features(code)
        assert "atom_family" in features

    def test_detect_features_selector(self, parser):
        code = '''const totalSelector = selector({ key: 'total', get: ({get}) => 0 });'''
        features = parser._detect_features(code)
        assert "selector" in features

    def test_detect_features_selector_family(self, parser):
        code = '''const byIdSelector = selectorFamily({ key: 'byId', get: (id) => ({get}) => null });'''
        features = parser._detect_features(code)
        assert "selector_family" in features

    def test_detect_features_atom_effects(self, parser):
        code = '''effects: [({ setSelf }) => { setSelf(0); }]'''
        features = parser._detect_features(code)
        assert "atom_effects" in features

    def test_detect_features_use_recoil_state(self, parser):
        code = '''const [count, setCount] = useRecoilState(countAtom);'''
        features = parser._detect_features(code)
        assert "use_recoil_state" in features

    def test_detect_features_use_recoil_value(self, parser):
        code = '''const count = useRecoilValue(countAtom);'''
        features = parser._detect_features(code)
        assert "use_recoil_value" in features

    def test_detect_features_use_recoil_callback(self, parser):
        code = '''const cb = useRecoilCallback(({snapshot}) => async () => {});'''
        features = parser._detect_features(code)
        assert "use_recoil_callback" in features

    def test_detect_features_recoil_root(self, parser):
        code = '''<RecoilRoot><App /></RecoilRoot>'''
        features = parser._detect_features(code)
        assert "recoil_root" in features

    def test_detect_features_wait_for_all(self, parser):
        code = '''get(waitForAll([a, b, c]))'''
        features = parser._detect_features(code)
        assert "wait_for_all" in features

    def test_detect_features_no_wait(self, parser):
        code = '''get(noWait(asyncSelector))'''
        features = parser._detect_features(code)
        assert "no_wait" in features

    def test_detect_features_recoil_sync(self, parser):
        code = '''effects: [syncEffect({ refine: string() })]'''
        features = parser._detect_features(code)
        assert "recoil_sync" in features

    def test_detect_features_loadable(self, parser):
        code = '''if (loadable.state === 'hasValue') return loadable.contents;'''
        features = parser._detect_features(code)
        assert "loadable" in features

    def test_detect_features_default_value(self, parser):
        code = '''if (newValue instanceof DefaultValue) return;'''
        features = parser._detect_features(code)
        assert "default_value" in features

    def test_detect_features_dangerously_allow_mutability(self, parser):
        code = '''dangerouslyAllowMutability: true'''
        features = parser._detect_features(code)
        assert "dangerously_allow_mutability" in features

    # ── Version Detection ────────────────────────────────────────

    def test_detect_version_0_0_basic(self, parser):
        code = '''
import { atom, useRecoilState } from 'recoil';
const countAtom = atom({ key: 'count', default: 0 });
'''
        version = parser._detect_version(code)
        assert version == "0.0"

    def test_detect_version_0_1_atom_family(self, parser):
        code = '''
import { atomFamily, selectorFamily } from 'recoil';
const todoAtom = atomFamily({ key: 'todo', default: '' });
'''
        version = parser._detect_version(code)
        assert version == "0.1"

    def test_detect_version_0_2_effects(self, parser):
        code = '''
const persistedAtom = atom({
  key: 'persisted',
  default: '',
  effects: [
    ({ setSelf, onSet }) => {
      setSelf(localStorage.getItem('key') ?? '');
      onSet((val) => localStorage.setItem('key', val));
    },
  ],
});
'''
        version = parser._detect_version(code)
        assert version == "0.2"

    def test_detect_version_0_3_wait_for_all_settled(self, parser):
        code = '''
const results = get(waitForAllSettled([a, b, c]));
'''
        version = parser._detect_version(code)
        assert version == "0.3"

    def test_detect_version_0_3_wait_for_any(self, parser):
        code = '''
const fastest = get(waitForAny([sourceA, sourceB]));
'''
        version = parser._detect_version(code)
        assert version == "0.3"

    def test_detect_version_0_4_snapshot_unstable(self, parser):
        code = '''
const snap = snapshot_UNSTABLE(({ set }) => { set(countAtom, 5); });
'''
        version = parser._detect_version(code)
        assert version == "0.4"

    def test_detect_version_0_4_goto_snapshot(self, parser):
        code = '''
const gotoSnapshot = useGotoRecoilSnapshot();
'''
        version = parser._detect_version(code)
        assert version == "0.4"

    def test_detect_version_0_5_refresher(self, parser):
        code = '''
const refreshUser = useRecoilRefresher_UNSTABLE(userSelector);
'''
        version = parser._detect_version(code)
        assert version == "0.5"

    def test_detect_version_0_6_store_id(self, parser):
        code = '''
effects: [({ storeID, setSelf }) => {
  const key = `${storeID}_myAtom`;
  setSelf(localStorage.getItem(key));
}]
'''
        version = parser._detect_version(code)
        assert version == "0.6"

    def test_detect_version_0_7_bridge(self, parser):
        code = '''
const RecoilBridge = useRecoilBridgeAcrossReactRoots_UNSTABLE();
'''
        version = parser._detect_version(code)
        assert version == "0.7"

    def test_detect_version_empty(self, parser):
        code = '''
console.log('no recoil');
'''
        version = parser._detect_version(code)
        assert version == ""

    # ── Version Compare ──────────────────────────────────────────

    def test_version_compare_equal(self, parser):
        assert parser._version_compare("0.3", "0.3") == 0

    def test_version_compare_greater(self, parser):
        assert parser._version_compare("0.7", "0.3") > 0

    def test_version_compare_less(self, parser):
        assert parser._version_compare("0.1", "0.5") < 0

    def test_version_compare_empty(self, parser):
        assert parser._version_compare("", "0.3") < 0
        assert parser._version_compare("0.3", "") > 0

    # ── Full Parse Integration ───────────────────────────────────

    def test_full_parse_comprehensive(self, parser):
        """Test full parsing of a comprehensive Recoil file."""
        code = '''
import { atom, selector, useRecoilState, useRecoilValue, atomFamily, selectorFamily, useRecoilCallback } from 'recoil';
import type { RecoilState, Snapshot } from 'recoil';

// Atoms
const countAtom = atom({
  key: 'count',
  default: 0,
});

const userAtom = atom<User | null>({
  key: 'user',
  default: null,
});

const itemsAtom = atom({
  key: 'items',
  default: [],
  effects: [
    ({ setSelf, onSet }) => {
      const saved = localStorage.getItem('items');
      if (saved) setSelf(JSON.parse(saved));
      onSet((val) => localStorage.setItem('items', JSON.stringify(val)));
    },
  ],
});

// Atom family
const todoAtom = atomFamily({
  key: 'todo',
  default: (id) => ({ id, text: '', done: false }),
});

// Selectors
const totalSelector = selector({
  key: 'total',
  get: ({ get }) => get(itemsAtom).reduce((sum, i) => sum + i.price, 0),
});

const asyncUserSelector = selector({
  key: 'asyncUser',
  get: async ({ get }) => {
    const userId = get(userIdAtom);
    return fetch('/api/users/' + userId).then(r => r.json());
  },
});

// Selector family
const todoByStatusSelector = selectorFamily({
  key: 'todoByStatus',
  get: (status) => ({ get }) => get(todosAtom).filter(t => t.status === status),
});

// Component
function App() {
  const [count, setCount] = useRecoilState(countAtom);
  const total = useRecoilValue(totalSelector);
  const saveAll = useRecoilCallback(({ snapshot, set }) => async () => {
    const items = await snapshot.getPromise(itemsAtom);
    await api.save(items);
  });
  return <div>{count} - {total}</div>;
}
'''
        result = parser.parse(code, "app.tsx")

        # Verify structure
        assert isinstance(result, RecoilParseResult)
        assert result.file_path == "app.tsx"
        assert result.file_type == "tsx"

        # Verify atoms found
        assert len(result.atoms) >= 2  # countAtom, userAtom, itemsAtom

        # Verify atom families found
        assert len(result.atom_families) >= 1

        # Verify selectors found
        assert len(result.selectors) >= 1

        # Verify selector families found
        assert len(result.selector_families) >= 1

        # Verify hooks found
        assert len(result.hook_usages) >= 2

        # Verify callbacks found
        assert len(result.callbacks) >= 1

        # Verify imports found
        assert len(result.imports) >= 1

        # Verify framework detection
        assert "recoil" in result.detected_frameworks

        # Verify feature detection
        assert len(result.detected_features) > 0

        # Verify version detection (effects → at least 0.2)
        assert result.recoil_version != ""

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.ts")
        assert isinstance(result, RecoilParseResult)
        assert len(result.atoms) == 0
        assert len(result.selectors) == 0

    def test_parse_non_recoil_file(self, parser):
        code = '''
import React from 'react';
function App() { return <div>Hello</div>; }
'''
        result = parser.parse(code, "app.tsx")
        assert isinstance(result, RecoilParseResult)
        assert len(result.atoms) == 0
        assert len(result.selectors) == 0

    def test_parse_recoil_sync_file(self, parser):
        code = '''
import { atom } from 'recoil';
import { syncEffect } from 'recoil-sync';
import { string } from '@recoiljs/refine';
import { RecoilURLSyncJSON } from 'recoil-sync';

const filterAtom = atom({
  key: 'filter',
  default: 'all',
  effects: [syncEffect({ refine: string() })],
});
'''
        result = parser.parse(code, "sync.ts")
        assert "recoil" in result.detected_frameworks
        assert "recoil-sync" in result.detected_frameworks
        assert "@recoiljs/refine" in result.detected_frameworks

    def test_parse_effects_file(self, parser):
        code = '''
const localStorageEffect = (key) => ({ setSelf, onSet }) => {
  const saved = localStorage.getItem(key);
  if (saved != null) setSelf(JSON.parse(saved));
  onSet((newValue, _, isReset) => {
    isReset ? localStorage.removeItem(key) : localStorage.setItem(key, JSON.stringify(newValue));
  });
};

const loggingEffect = ({ onSet }) => {
  onSet((newValue, oldValue) => {
    console.log('Changed:', oldValue, '->', newValue);
  });
};
'''
        result = parser.parse(code, "effects.ts")
        assert len(result.effects) >= 1

    def test_parse_snapshot_testing_file(self, parser):
        code = '''
import { snapshot_UNSTABLE } from 'recoil';

test('totalSelector computes sum', () => {
  const snapshot = snapshot_UNSTABLE(({ set }) => {
    set(itemsAtom, [{ price: 10 }, { price: 20 }]);
  });
  expect(snapshot.getLoadable(totalSelector).getValue()).toBe(30);
});
'''
        result = parser.parse(code, "test.ts")
        assert len(result.snapshot_usages) >= 1
        assert result.recoil_version in ["0.4", "0.5", "0.6", "0.7"]
