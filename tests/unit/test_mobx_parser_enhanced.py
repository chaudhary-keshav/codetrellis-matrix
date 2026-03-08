"""
Tests for MobX extractors and EnhancedMobXParser.

Part of CodeTrellis v4.51 MobX State Management Framework Support.
Tests cover:
- Observable extraction (makeObservable, makeAutoObservable, @observable,
                         observable.ref, observable.shallow, observable.deep,
                         observable.struct, observable maps/sets/arrays)
- Computed extraction (computed, computed.struct, @computed, keepAlive,
                       requiresReaction, computed with setter)
- Action extraction (action, action.bound, @action, @action.bound,
                     runInAction, flow, flow.bound, @flow, flowResult)
- Reaction extraction (autorun, reaction, when, observe, intercept,
                        onBecomeObserved, disposer patterns, options)
- API extraction (imports, configure, observer/inject/Provider,
                   useLocalObservable, TypeScript types, ecosystem detection)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from codetrellis.mobx_parser_enhanced import (
    EnhancedMobXParser,
    MobXParseResult,
)
from codetrellis.extractors.mobx import (
    MobXObservableExtractor,
    MobXComputedExtractor,
    MobXActionExtractor,
    MobXReactionExtractor,
    MobXApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedMobXParser()


@pytest.fixture
def observable_extractor():
    return MobXObservableExtractor()


@pytest.fixture
def computed_extractor():
    return MobXComputedExtractor()


@pytest.fixture
def action_extractor():
    return MobXActionExtractor()


@pytest.fixture
def reaction_extractor():
    return MobXReactionExtractor()


@pytest.fixture
def api_extractor():
    return MobXApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Observable Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMobXObservableExtractor:
    """Tests for MobXObservableExtractor."""

    def test_make_observable_basic(self, observable_extractor):
        code = '''
import { makeObservable, observable, action, computed } from 'mobx';

class TodoStore {
  todos = [];

  constructor() {
    makeObservable(this, {
      todos: observable,
      addTodo: action,
      count: computed,
    });
  }
}
'''
        result = observable_extractor.extract(code, "store.ts")
        assert len(result['observables']) >= 1
        obs = result['observables'][0]
        assert obs.line > 0

    def test_make_auto_observable(self, observable_extractor):
        code = '''
import { makeAutoObservable } from 'mobx';

class CounterStore {
  count = 0;
  name = 'counter';

  constructor() {
    makeAutoObservable(this);
  }

  increment() {
    this.count++;
  }
}
'''
        result = observable_extractor.extract(code, "counter.ts")
        assert len(result['auto_observables']) >= 1
        ao = result['auto_observables'][0]
        assert ao.line > 0

    def test_make_auto_observable_with_overrides(self, observable_extractor):
        code = '''
import { makeAutoObservable } from 'mobx';

class ApiStore {
  data = [];
  apiClient;

  constructor(client) {
    this.apiClient = client;
    makeAutoObservable(this, {
      apiClient: false,
    });
  }
}
'''
        result = observable_extractor.extract(code, "api-store.ts")
        assert len(result['auto_observables']) >= 1

    def test_make_auto_observable_with_auto_bind(self, observable_extractor):
        code = '''
import { makeAutoObservable } from 'mobx';

class FormStore {
  value = '';

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }
}
'''
        result = observable_extractor.extract(code, "form.ts")
        assert len(result['auto_observables']) >= 1

    def test_decorator_observable(self, observable_extractor):
        code = '''
import { observable } from 'mobx';

class Store {
  @observable count = 0;
  @observable name = '';
}
'''
        result = observable_extractor.extract(code, "store.ts")
        assert len(result['decorator_observables']) >= 1

    def test_decorator_observable_ref(self, observable_extractor):
        code = '''
import { observable } from 'mobx';

class Store {
  @observable.ref editor = null;
}
'''
        result = observable_extractor.extract(code, "store.ts")
        assert len(result['decorator_observables']) >= 1
        dobs = result['decorator_observables'][0]
        assert dobs.modifier == 'ref'

    def test_decorator_observable_shallow(self, observable_extractor):
        code = '''
import { observable } from 'mobx';

class Store {
  @observable.shallow items = [];
}
'''
        result = observable_extractor.extract(code, "store.ts")
        assert len(result['decorator_observables']) >= 1
        dobs = result['decorator_observables'][0]
        assert dobs.modifier == 'shallow'

    def test_decorator_observable_struct(self, observable_extractor):
        code = '''
import { observable } from 'mobx';

class Store {
  @observable.struct position = { x: 0, y: 0 };
}
'''
        result = observable_extractor.extract(code, "store.ts")
        assert len(result['decorator_observables']) >= 1
        dobs = result['decorator_observables'][0]
        assert dobs.modifier == 'struct'

    def test_observable_object(self, observable_extractor):
        code = '''
import { observable } from 'mobx';

const state = observable({
  count: 0,
  name: 'test',
});
'''
        result = observable_extractor.extract(code, "state.ts")
        assert len(result['observables']) >= 1

    def test_make_observable_with_modifiers(self, observable_extractor):
        code = '''
import { makeObservable, observable } from 'mobx';

class Store {
  items = [];
  config = {};

  constructor() {
    makeObservable(this, {
      items: observable.shallow,
      config: observable.ref,
    });
  }
}
'''
        result = observable_extractor.extract(code, "store.ts")
        assert len(result['observables']) >= 1


# ═══════════════════════════════════════════════════════════════════
# Computed Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMobXComputedExtractor:
    """Tests for MobXComputedExtractor."""

    def test_computed_function(self, computed_extractor):
        code = '''
import { computed, observable } from 'mobx';

const total = computed(() => store.items.reduce((s, i) => s + i.price, 0));
'''
        result = computed_extractor.extract(code, "computed.ts")
        assert len(result['computeds']) >= 1

    def test_computed_decorator(self, computed_extractor):
        code = '''
import { computed, observable } from 'mobx';

class Store {
  items = [];

  @computed get total() {
    return this.items.reduce((s, i) => s + i.price, 0);
  }
}
'''
        result = computed_extractor.extract(code, "store.ts")
        assert len(result['computeds']) >= 1

    def test_computed_struct(self, computed_extractor):
        code = '''
import { computed, makeObservable } from 'mobx';

class Store {
  constructor() {
    makeObservable(this, {
      activeFilters: computed.struct,
    });
  }

  get activeFilters() {
    return { type: this.type, status: this.status };
  }
}
'''
        result = computed_extractor.extract(code, "store.ts")
        assert len(result['computeds']) >= 1

    def test_computed_with_options(self, computed_extractor):
        code = '''
import { computed } from 'mobx';

const expensive = computed(() => heavyCalc(), { keepAlive: true });
'''
        result = computed_extractor.extract(code, "store.ts")
        assert len(result['computeds']) >= 1

    def test_computed_in_annotation_map(self, computed_extractor):
        code = '''
import { makeObservable, computed } from 'mobx';

class Store {
  get double() { return this.count * 2; }

  constructor() {
    makeObservable(this, {
      double: computed,
    });
  }
}
'''
        result = computed_extractor.extract(code, "store.ts")
        assert len(result['computeds']) >= 1


# ═══════════════════════════════════════════════════════════════════
# Action Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMobXActionExtractor:
    """Tests for MobXActionExtractor."""

    def test_action_function(self, action_extractor):
        code = '''
import { action } from 'mobx';

const increment = action(() => {
  store.count++;
});
'''
        result = action_extractor.extract(code, "actions.ts")
        assert len(result['actions']) >= 1

    def test_action_bound_decorator(self, action_extractor):
        code = '''
import { action, makeObservable, observable } from 'mobx';

class Store {
  count = 0;

  constructor() {
    makeObservable(this, {
      count: observable,
      handleClick: action.bound,
    });
  }

  handleClick() {
    this.count++;
  }
}
'''
        result = action_extractor.extract(code, "store.ts")
        assert len(result['actions']) >= 1

    def test_action_decorator(self, action_extractor):
        code = '''
import { action } from 'mobx';

class Store {
  @action increment() {
    this.count++;
  }

  @action.bound handleChange(e) {
    this.value = e.target.value;
  }
}
'''
        result = action_extractor.extract(code, "store.ts")
        assert len(result['actions']) >= 1

    def test_run_in_action(self, action_extractor):
        code = '''
import { runInAction } from 'mobx';

async function fetchData() {
  const data = await api.fetch();
  runInAction(() => {
    store.data = data;
    store.loading = false;
  });
}
'''
        result = action_extractor.extract(code, "fetch.ts")
        assert len(result['actions']) >= 1

    def test_flow_function(self, action_extractor):
        code = '''
import { flow, makeAutoObservable } from 'mobx';

class Store {
  data = [];
  state = 'idle';

  constructor() { makeAutoObservable(this); }

  fetchData = flow(function* () {
    this.state = 'loading';
    this.data = yield api.fetch();
    this.state = 'done';
  });
}
'''
        result = action_extractor.extract(code, "store.ts")
        assert len(result['flows']) >= 1

    def test_flow_decorator(self, action_extractor):
        code = '''
import { flow } from 'mobx';

class Store {
  @flow *fetchItems() {
    this.items = yield api.getItems();
  }
}
'''
        result = action_extractor.extract(code, "store.ts")
        assert len(result['flows']) >= 1

    def test_named_action(self, action_extractor):
        code = '''
import { action } from 'mobx';

const reset = action('resetStore', () => {
  store.count = 0;
  store.name = '';
});
'''
        result = action_extractor.extract(code, "actions.ts")
        assert len(result['actions']) >= 1

    def test_action_in_annotation_map(self, action_extractor):
        code = '''
import { makeObservable, action } from 'mobx';

class Store {
  constructor() {
    makeObservable(this, {
      increment: action,
      decrement: action,
      reset: action.bound,
    });
  }
}
'''
        result = action_extractor.extract(code, "store.ts")
        assert len(result['actions']) >= 1


# ═══════════════════════════════════════════════════════════════════
# Reaction Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMobXReactionExtractor:
    """Tests for MobXReactionExtractor."""

    def test_autorun(self, reaction_extractor):
        code = '''
import { autorun } from 'mobx';

const dispose = autorun(() => {
  console.log(store.count);
});
'''
        result = reaction_extractor.extract(code, "reactions.ts")
        assert len(result['reactions']) >= 1
        rxn = result['reactions'][0]
        assert rxn.reaction_type == 'autorun'

    def test_reaction(self, reaction_extractor):
        code = '''
import { reaction } from 'mobx';

const dispose = reaction(
  () => store.query,
  (query) => {
    store.search(query);
  }
);
'''
        result = reaction_extractor.extract(code, "reactions.ts")
        assert len(result['reactions']) >= 1
        rxn = result['reactions'][0]
        assert rxn.reaction_type == 'reaction'

    def test_when(self, reaction_extractor):
        code = '''
import { when } from 'mobx';

when(
  () => store.isReady,
  () => store.initialize()
);
'''
        result = reaction_extractor.extract(code, "reactions.ts")
        assert len(result['reactions']) >= 1
        rxn = result['reactions'][0]
        assert rxn.reaction_type == 'when'

    def test_autorun_with_delay(self, reaction_extractor):
        code = '''
import { autorun } from 'mobx';

const dispose = autorun(
  () => store.sync(),
  { delay: 300 }
);
'''
        result = reaction_extractor.extract(code, "reactions.ts")
        assert len(result['reactions']) >= 1

    def test_reaction_with_fire_immediately(self, reaction_extractor):
        code = '''
import { reaction } from 'mobx';

reaction(
  () => store.theme,
  (theme) => applyTheme(theme),
  { fireImmediately: true }
);
'''
        result = reaction_extractor.extract(code, "reactions.ts")
        assert len(result['reactions']) >= 1

    def test_observe(self, reaction_extractor):
        code = '''
import { observe } from 'mobx';

const dispose = observe(store.items, (change) => {
  console.log('Items changed:', change);
});
'''
        result = reaction_extractor.extract(code, "reactions.ts")
        assert len(result['reactions']) >= 1
        rxn = result['reactions'][0]
        assert rxn.reaction_type == 'observe'

    def test_intercept(self, reaction_extractor):
        code = '''
import { intercept } from 'mobx';

const dispose = intercept(store, 'count', (change) => {
  if (change.newValue < 0) return null;
  return change;
});
'''
        result = reaction_extractor.extract(code, "reactions.ts")
        assert len(result['reactions']) >= 1
        rxn = result['reactions'][0]
        assert rxn.reaction_type == 'intercept'

    def test_disposer_stored(self, reaction_extractor):
        code = '''
import { autorun } from 'mobx';

const myDisposer = autorun(() => {
  document.title = store.title;
});
'''
        result = reaction_extractor.extract(code, "reactions.ts")
        assert len(result['reactions']) >= 1
        rxn = result['reactions'][0]
        assert rxn.has_disposer is True

    def test_reaction_in_use_effect(self, reaction_extractor):
        code = '''
import { autorun } from 'mobx';

useEffect(() => {
  const dispose = autorun(() => {
    console.log(store.value);
  });
  return () => dispose();
}, []);
'''
        result = reaction_extractor.extract(code, "component.tsx")
        assert len(result['reactions']) >= 1

    def test_reaction_with_on_error(self, reaction_extractor):
        code = '''
import { autorun } from 'mobx';

autorun(
  () => store.riskyOperation(),
  { onError: (err) => console.error(err) }
);
'''
        result = reaction_extractor.extract(code, "reactions.ts")
        assert len(result['reactions']) >= 1


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMobXApiExtractor:
    """Tests for MobXApiExtractor."""

    def test_import_from_mobx(self, api_extractor):
        code = '''
import { makeAutoObservable, observable, action, computed } from 'mobx';
'''
        result = api_extractor.extract(code, "store.ts")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.source == 'mobx'

    def test_import_from_mobx_react(self, api_extractor):
        code = '''
import { observer } from 'mobx-react';
'''
        result = api_extractor.extract(code, "app.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.source == 'mobx-react'

    def test_import_from_mobx_react_lite(self, api_extractor):
        code = '''
import { observer, useLocalObservable } from 'mobx-react-lite';
'''
        result = api_extractor.extract(code, "app.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.source == 'mobx-react-lite'

    def test_import_from_mobx_state_tree(self, api_extractor):
        code = '''
import { types, flow as mstFlow } from 'mobx-state-tree';
'''
        result = api_extractor.extract(code, "model.ts")
        assert len(result['imports']) >= 1

    def test_import_from_mobx_utils(self, api_extractor):
        code = '''
import { fromPromise, keepAlive } from 'mobx-utils';
'''
        result = api_extractor.extract(code, "utils.ts")
        assert len(result['imports']) >= 1

    def test_configure_enforce_actions(self, api_extractor):
        code = '''
import { configure } from 'mobx';

configure({
  enforceActions: 'always',
  computedRequiresReaction: true,
  reactionRequiresObservable: true,
});
'''
        result = api_extractor.extract(code, "config.ts")
        assert len(result['configures']) >= 1

    def test_configure_use_proxies(self, api_extractor):
        code = '''
import { configure } from 'mobx';

configure({
  useProxies: 'never',
  isolateGlobalState: true,
});
'''
        result = api_extractor.extract(code, "config.ts")
        assert len(result['configures']) >= 1

    def test_observer_integration(self, api_extractor):
        code = '''
import { observer } from 'mobx-react-lite';

const TodoList = observer(({ store }) => (
  <ul>
    {store.todos.map(todo => <li key={todo.id}>{todo.text}</li>)}
  </ul>
));
'''
        result = api_extractor.extract(code, "list.tsx")
        assert len(result['integrations']) >= 1

    def test_inject_integration(self, api_extractor):
        code = '''
import { inject, observer } from 'mobx-react';

@inject('store')
@observer
class TodoList extends React.Component {
  render() { return <div>{this.props.store.todos}</div>; }
}
'''
        result = api_extractor.extract(code, "list.tsx")
        assert len(result['integrations']) >= 1

    def test_provider_integration(self, api_extractor):
        code = '''
import { Provider } from 'mobx-react';
import store from './store';

const App = () => (
  <Provider store={store}>
    <TodoList />
  </Provider>
);
'''
        result = api_extractor.extract(code, "app.tsx")
        assert len(result['integrations']) >= 1

    def test_use_local_observable(self, api_extractor):
        code = '''
import { observer, useLocalObservable } from 'mobx-react-lite';

const SearchBox = observer(() => {
  const state = useLocalObservable(() => ({
    query: '',
    setQuery(q) { state.query = q; },
  }));
  return <input value={state.query} />;
});
'''
        result = api_extractor.extract(code, "search.tsx")
        assert len(result['integrations']) >= 1

    def test_typescript_types(self, api_extractor):
        code = '''
import { IObservableValue, IComputedValue, IReactionDisposer } from 'mobx';

const counter: IObservableValue<number> = observable.box(0);
const disposer: IReactionDisposer = autorun(() => {});
'''
        result = api_extractor.extract(code, "types.ts")
        assert len(result['types']) >= 1

    def test_ecosystem_detection(self, api_extractor):
        code = '''
import { makeAutoObservable } from 'mobx';
import { observer } from 'mobx-react-lite';
import { types } from 'mobx-state-tree';
import { fromPromise } from 'mobx-utils';
'''
        result = api_extractor.extract(code, "full.ts")
        assert len(result['imports']) >= 3


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedMobXParser:
    """Tests for EnhancedMobXParser integration."""

    def test_is_mobx_file_true(self, parser):
        code = '''
import { makeAutoObservable } from 'mobx';

class Store {
  count = 0;
  constructor() { makeAutoObservable(this); }
}
'''
        assert parser.is_mobx_file(code, "store.ts") is True

    def test_is_mobx_file_false(self, parser):
        code = '''
import React from 'react';

const App = () => <div>Hello</div>;
'''
        assert parser.is_mobx_file(code, "app.tsx") is False

    def test_is_mobx_file_react_import(self, parser):
        code = '''
import { observer } from 'mobx-react-lite';
const List = observer(() => <ul></ul>);
'''
        assert parser.is_mobx_file(code, "list.tsx") is True

    def test_is_mobx_file_state_tree(self, parser):
        code = '''
import { types } from 'mobx-state-tree';
const Todo = types.model('Todo', { text: types.string });
'''
        assert parser.is_mobx_file(code, "model.ts") is True

    def test_parse_result_type(self, parser):
        code = '''
import { makeAutoObservable } from 'mobx';
class Store { count = 0; constructor() { makeAutoObservable(this); } }
'''
        result = parser.parse(code, "store.ts")
        assert isinstance(result, MobXParseResult)

    def test_parse_observables(self, parser):
        code = '''
import { makeObservable, observable, action } from 'mobx';

class TodoStore {
  todos = [];

  constructor() {
    makeObservable(this, {
      todos: observable,
      addTodo: action,
    });
  }

  addTodo(text) { this.todos.push({ text }); }
}
'''
        result = parser.parse(code, "store.ts")
        assert len(result.observables) >= 1

    def test_parse_auto_observables(self, parser):
        code = '''
import { makeAutoObservable } from 'mobx';

class Store {
  count = 0;
  constructor() { makeAutoObservable(this); }
  increment() { this.count++; }
}
'''
        result = parser.parse(code, "store.ts")
        assert len(result.auto_observables) >= 1

    def test_parse_computeds(self, parser):
        code = '''
import { makeAutoObservable, computed } from 'mobx';

class Store {
  items = [];
  constructor() { makeAutoObservable(this); }
  get total() { return this.items.reduce((s, i) => s + i.price, 0); }
}

const double = computed(() => store.count * 2);
'''
        result = parser.parse(code, "store.ts")
        assert len(result.computeds) >= 1

    def test_parse_actions(self, parser):
        code = '''
import { makeAutoObservable, runInAction, action } from 'mobx';

class Store {
  data = [];
  constructor() { makeAutoObservable(this); }
  fetchData() {
    api.fetch().then(data => {
      runInAction(() => { this.data = data; });
    });
  }
}

const reset = action(() => { store.count = 0; });
'''
        result = parser.parse(code, "store.ts")
        assert len(result.actions) >= 1

    def test_parse_flows(self, parser):
        code = '''
import { flow, makeAutoObservable } from 'mobx';

class DataStore {
  data = [];
  constructor() { makeAutoObservable(this); }
  fetchData = flow(function* () {
    this.data = yield api.fetch();
  });
}
'''
        result = parser.parse(code, "store.ts")
        assert len(result.flows) >= 1

    def test_parse_reactions(self, parser):
        code = '''
import { autorun, reaction, when } from 'mobx';

const dispose1 = autorun(() => console.log(store.count));
const dispose2 = reaction(() => store.query, (q) => store.search(q));
when(() => store.isReady, () => store.init());
'''
        result = parser.parse(code, "reactions.ts")
        assert len(result.reactions) >= 1

    def test_parse_imports(self, parser):
        code = '''
import { makeAutoObservable, observable, action, computed, flow } from 'mobx';
import { observer } from 'mobx-react-lite';
'''
        result = parser.parse(code, "store.ts")
        assert len(result.imports) >= 1

    def test_parse_configures(self, parser):
        code = '''
import { configure } from 'mobx';

configure({
  enforceActions: 'always',
});
'''
        result = parser.parse(code, "config.ts")
        assert len(result.configures) >= 1

    def test_parse_integrations(self, parser):
        code = '''
import { observer } from 'mobx-react-lite';
import { inject, Provider } from 'mobx-react';

const List = observer(() => <ul></ul>);
'''
        result = parser.parse(code, "app.tsx")
        assert len(result.integrations) >= 1

    def test_detect_version_v6(self, parser):
        code = '''
import { makeAutoObservable } from 'mobx';
class Store { constructor() { makeAutoObservable(this); } }
'''
        result = parser.parse(code, "store.ts")
        assert result.mobx_version == 'v6'

    def test_detect_version_v6_make_observable(self, parser):
        code = '''
import { makeObservable, observable } from 'mobx';
class Store { constructor() { makeObservable(this, { count: observable }); } }
'''
        result = parser.parse(code, "store.ts")
        assert result.mobx_version == 'v6'

    def test_detect_version_v4_decorators(self, parser):
        code = '''
import { observable, action, computed } from 'mobx';

class Store {
  @observable count = 0;
  @computed get double() { return this.count * 2; }
  @action increment() { this.count++; }
}
'''
        result = parser.parse(code, "store.ts")
        assert result.mobx_version == 'v4'

    def test_detect_features(self, parser):
        code = '''
import { makeAutoObservable, configure, flow, autorun } from 'mobx';
import { observer } from 'mobx-react-lite';

configure({ enforceActions: 'always' });

class Store {
  constructor() { makeAutoObservable(this); }
  fetchData = flow(function* () { yield api.fetch(); });
}

const App = observer(() => <div></div>);
'''
        result = parser.parse(code, "app.tsx")
        assert len(result.detected_features) >= 1

    def test_detect_frameworks(self, parser):
        code = '''
import { makeAutoObservable } from 'mobx';
import { observer } from 'mobx-react-lite';
import { types } from 'mobx-state-tree';
'''
        result = parser.parse(code, "full.ts")
        # detected_frameworks comes from api_extractor.detected_ecosystems
        assert isinstance(result.detected_frameworks, list)

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.ts")
        assert isinstance(result, MobXParseResult)
        assert len(result.observables) == 0
        assert len(result.actions) == 0

    def test_parse_non_mobx_file(self, parser):
        code = '''
import React from 'react';
const App = () => <div>Hello World</div>;
export default App;
'''
        result = parser.parse(code, "app.tsx")
        assert isinstance(result, MobXParseResult)

    def test_version_compare(self, parser):
        assert parser._version_compare('v6', 'v5') > 0
        assert parser._version_compare('v5', 'v6') < 0
        assert parser._version_compare('v6', 'v6') == 0
        assert parser._version_compare('v6', '') > 0
        assert parser._version_compare('', 'v6') < 0

    def test_dataclass_to_dict(self, parser):
        from codetrellis.extractors.mobx import MobXObservableInfo
        info = MobXObservableInfo(name="test", line=1)
        d = parser._dataclass_to_dict(info)
        assert isinstance(d, dict)
        assert d['name'] == 'test'
        assert d['line'] == 1


# ═══════════════════════════════════════════════════════════════════
# Full Integration Test
# ═══════════════════════════════════════════════════════════════════

class TestMobXFullIntegration:
    """Full integration tests with comprehensive MobX code samples."""

    def test_full_store_v6(self, parser):
        """Test a full MobX v6 store with all features."""
        code = '''
import { makeAutoObservable, runInAction, flow, autorun, reaction, configure } from 'mobx';
import { observer } from 'mobx-react-lite';

configure({ enforceActions: 'always' });

class TodoStore {
  todos = [];
  filter = 'all';
  isLoading = false;

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get filteredTodos() {
    switch (this.filter) {
      case 'active': return this.todos.filter(t => !t.done);
      case 'completed': return this.todos.filter(t => t.done);
      default: return this.todos;
    }
  }

  get completedCount() {
    return this.todos.filter(t => t.done).length;
  }

  addTodo(text) {
    this.todos.push({ id: Date.now(), text, done: false });
  }

  toggleTodo(id) {
    const todo = this.todos.find(t => t.id === id);
    if (todo) todo.done = !todo.done;
  }

  setFilter(filter) {
    this.filter = filter;
  }

  async fetchTodos() {
    this.isLoading = true;
    try {
      const data = await api.getTodos();
      runInAction(() => {
        this.todos = data;
      });
    } finally {
      runInAction(() => {
        this.isLoading = false;
      });
    }
  }

  saveTodos = flow(function* () {
    yield api.saveTodos(this.todos);
  });
}

const store = new TodoStore();

const dispose = autorun(() => {
  localStorage.setItem('todos', JSON.stringify(store.todos));
});

reaction(
  () => store.filter,
  (filter) => analytics.track('filter_changed', { filter }),
);

const TodoList = observer(() => (
  <ul>
    {store.filteredTodos.map(todo => (
      <li key={todo.id} onClick={() => store.toggleTodo(todo.id)}>
        {todo.text}
      </li>
    ))}
  </ul>
));

export default TodoList;
'''
        result = parser.parse(code, "todo-store.tsx")
        assert result.mobx_version == 'v6'
        assert len(result.auto_observables) >= 1
        assert len(result.actions) >= 1  # runInAction
        assert len(result.flows) >= 1
        assert len(result.reactions) >= 1  # autorun + reaction
        assert len(result.imports) >= 1
        assert len(result.configures) >= 1
        assert len(result.integrations) >= 1  # observer
        assert len(result.detected_features) >= 1

    def test_full_store_v4_decorators(self, parser):
        """Test a MobX v4 store with decorators."""
        code = '''
import { observable, action, computed } from 'mobx';
import { observer, inject } from 'mobx-react';

class UserStore {
  @observable users = [];
  @observable selectedId = null;

  @computed get selectedUser() {
    return this.users.find(u => u.id === this.selectedId);
  }

  @action setSelected(id) {
    this.selectedId = id;
  }

  @action.bound async fetchUsers() {
    const data = await api.getUsers();
    this.users = data;
  }
}

@inject('userStore')
@observer
class UserList extends React.Component {
  render() {
    return <div>{this.props.userStore.users.length}</div>;
  }
}
'''
        result = parser.parse(code, "user-store.tsx")
        assert result.mobx_version == 'v4'
        assert len(result.decorator_observables) >= 1
        assert len(result.computeds) >= 1
        assert len(result.actions) >= 1
        assert len(result.integrations) >= 1

    def test_full_store_with_make_observable(self, parser):
        """Test MobX v6 store with explicit makeObservable annotations."""
        code = '''
import { makeObservable, observable, action, computed, flow } from 'mobx';

class CartStore {
  items = [];
  discount = 0;

  constructor() {
    makeObservable(this, {
      items: observable,
      discount: observable,
      subtotal: computed,
      total: computed.struct,
      addItem: action,
      removeItem: action,
      applyDiscount: action.bound,
      checkout: flow,
    });
  }

  get subtotal() {
    return this.items.reduce((sum, item) => sum + item.price * item.qty, 0);
  }

  get total() {
    return this.subtotal * (1 - this.discount);
  }

  addItem(item) {
    this.items.push(item);
  }

  removeItem(id) {
    this.items = this.items.filter(i => i.id !== id);
  }

  applyDiscount(rate) {
    this.discount = rate;
  }

  *checkout() {
    yield api.processPayment(this.total);
    this.items = [];
  }
}
'''
        result = parser.parse(code, "cart-store.ts")
        assert result.mobx_version == 'v6'
        assert len(result.observables) >= 1
        assert len(result.computeds) >= 1
        assert len(result.actions) >= 1
        assert len(result.flows) >= 1
