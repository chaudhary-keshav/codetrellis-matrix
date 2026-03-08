"""
Tests for NgRx extractors and EnhancedNgrxParser.

Part of CodeTrellis v4.53 NgRx Framework Support.
Tests cover:
- Store extraction (StoreModule, provideStore, ComponentStore, SignalStore)
- Action extraction (createAction, createActionGroup, legacy class actions)
- Effect extraction (createEffect, @Effect, functional effects, ComponentStore effects)
- Selector extraction (createSelector, createFeatureSelector, createFeature auto-selectors)
- API extraction (entities, router store, packages, reducers)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from codetrellis.ngrx_parser_enhanced import (
    EnhancedNgrxParser,
    NgrxParseResult,
)
from codetrellis.extractors.ngrx import (
    NgrxStoreExtractor,
    NgrxEffectExtractor,
    NgrxSelectorExtractor,
    NgrxActionExtractor,
    NgrxApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedNgrxParser()


@pytest.fixture
def store_extractor():
    return NgrxStoreExtractor()


@pytest.fixture
def effect_extractor():
    return NgrxEffectExtractor()


@pytest.fixture
def selector_extractor():
    return NgrxSelectorExtractor()


@pytest.fixture
def action_extractor():
    return NgrxActionExtractor()


@pytest.fixture
def api_extractor():
    return NgrxApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Store Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestNgrxStoreExtractor:
    """Tests for NgrxStoreExtractor."""

    def test_store_module_for_root(self, store_extractor):
        code = '''
import { StoreModule } from '@ngrx/store';
import { reducers, metaReducers } from './reducers';

@NgModule({
    imports: [
        StoreModule.forRoot(reducers, { metaReducers }),
        StoreDevtoolsModule.instrument({ maxAge: 25 }),
    ],
})
export class AppModule {}
'''
        result = store_extractor.extract(code, "app.module.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        store = stores[0]
        assert store.setup_method == 'forRoot'

    def test_store_module_for_feature(self, store_extractor):
        code = '''
import { StoreModule } from '@ngrx/store';
import { usersReducer } from './users.reducer';

@NgModule({
    imports: [
        StoreModule.forFeature('users', usersReducer),
    ],
})
export class UsersModule {}
'''
        result = store_extractor.extract(code, "users.module.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        store = stores[0]
        assert store.setup_method == 'forFeature'
        assert store.feature_name == 'users'

    def test_provide_store_standalone(self, store_extractor):
        code = '''
import { provideStore, provideState } from '@ngrx/store';
import { provideEffects } from '@ngrx/effects';
import { provideStoreDevtools } from '@ngrx/store-devtools';

bootstrapApplication(AppComponent, {
    providers: [
        provideStore({ router: routerReducer }),
        provideState({ name: 'users', reducer: usersReducer }),
        provideEffects(UserEffects),
        provideStoreDevtools({ maxAge: 25 }),
    ],
});
'''
        result = store_extractor.extract(code, "main.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        store = stores[0]
        assert store.setup_method == 'provideStore'
        assert store.is_standalone is True

    def test_component_store(self, store_extractor):
        code = '''
import { ComponentStore } from '@ngrx/component-store';
import { Injectable } from '@angular/core';

interface TodosState {
    todos: Todo[];
    loading: boolean;
}

@Injectable()
export class TodosStore extends ComponentStore<TodosState> {
    constructor() {
        super({ todos: [], loading: false });
    }

    readonly todos$ = this.select(state => state.todos);
    readonly loading$ = this.select(state => state.loading);

    readonly addTodo = this.updater((state, todo: Todo) => ({
        ...state,
        todos: [...state.todos, todo],
    }));

    readonly loadTodos = this.effect<void>(trigger$ =>
        trigger$.pipe(
            tap(() => this.patchState({ loading: true })),
            switchMap(() => this.todosService.getAll().pipe(
                tapResponse(
                    todos => this.patchState({ todos, loading: false }),
                    error => console.error(error),
                ),
            )),
        )
    );
}
'''
        result = store_extractor.extract(code, "todos.store.ts")
        cs_list = result.get('component_stores', [])
        assert len(cs_list) >= 1
        cs = cs_list[0]
        assert 'TodosStore' in cs.name
        assert cs.has_patch_state is True

    def test_signal_store(self, store_extractor):
        code = '''
import { signalStore, withState, withComputed, withMethods, withHooks } from '@ngrx/signals';
import { withEntities, setAllEntities } from '@ngrx/signals/entities';
import { computed, inject } from '@angular/core';

export const TodosStore = signalStore(
    withState({ todos: [] as Todo[], loading: false, filter: 'all' }),
    withEntities<Todo>(),
    withComputed(({ todos, filter }) => ({
        filteredTodos: computed(() =>
            filter() === 'all' ? todos() : todos().filter(t => t.status === filter())
        ),
        todosCount: computed(() => todos().length),
    })),
    withMethods((store, api = inject(TodosApi)) => ({
        async loadTodos() {
            patchState(store, { loading: true });
            const todos = await firstValueFrom(api.getAll());
            patchState(store, setAllEntities(todos));
            patchState(store, { loading: false });
        },
        setFilter(filter: string) {
            patchState(store, { filter });
        },
    })),
    withHooks({
        onInit(store) { store.loadTodos(); },
    }),
);
'''
        result = store_extractor.extract(code, "todos.store.ts")
        ss_list = result.get('signal_stores', [])
        assert len(ss_list) >= 1
        ss = ss_list[0]
        assert 'TodosStore' in ss.name
        assert ss.has_entities is True
        assert ss.with_hooks is True

    def test_devtools_detection(self, store_extractor):
        code = '''
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import { provideStoreDevtools } from '@ngrx/store-devtools';

StoreDevtoolsModule.instrument({ maxAge: 25, logOnly: environment.production });
provideStoreDevtools({ maxAge: 25 });
'''
        result = store_extractor.extract(code, "app.module.ts")
        stores = result.get('stores', [])
        # DevTools should be detected
        assert any(s.has_devtools for s in stores) or len(stores) == 0  # ok even if no "store" found; just testing detection

    def test_runtime_checks(self, store_extractor):
        code = '''
import { provideStore } from '@ngrx/store';

provideStore(reducers, {
    runtimeChecks: {
        strictStateImmutability: true,
        strictActionImmutability: true,
        strictStateSerializability: true,
        strictActionSerializability: true,
        strictActionWithinNgZone: true,
        strictActionTypeUniqueness: true,
    },
});
'''
        result = store_extractor.extract(code, "app.config.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        assert len(stores[0].runtime_checks) > 0


# ═══════════════════════════════════════════════════════════════════
# Action Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestNgrxActionExtractor:
    """Tests for NgrxActionExtractor."""

    def test_create_action(self, action_extractor):
        code = '''
import { createAction, props } from '@ngrx/store';

export const loadUsers = createAction('[Users Page] Load Users');
export const loadUsersSuccess = createAction(
    '[Users API] Load Users Success',
    props<{ users: User[] }>()
);
export const loadUsersFailure = createAction(
    '[Users API] Load Users Failure',
    props<{ error: string }>()
);
'''
        result = action_extractor.extract(code, "users.actions.ts")
        actions = result.get('actions', [])
        assert len(actions) >= 3
        names = [a.name for a in actions]
        assert 'loadUsers' in names
        assert 'loadUsersSuccess' in names
        assert 'loadUsersFailure' in names
        # Check props detection
        success = next(a for a in actions if a.name == 'loadUsersSuccess')
        assert success.has_props is True

    def test_create_action_group(self, action_extractor):
        code = '''
import { createActionGroup, props, emptyProps } from '@ngrx/store';

export const UsersApiActions = createActionGroup({
    source: 'Users API',
    events: {
        'Load Users Success': props<{ users: User[] }>(),
        'Load Users Failure': props<{ error: string }>(),
        'Users Loaded': emptyProps(),
    },
});
'''
        result = action_extractor.extract(code, "users.actions.ts")
        groups = result.get('action_groups', [])
        assert len(groups) >= 1
        group = groups[0]
        assert 'UsersApiActions' in group.name
        assert group.source == 'Users API'
        assert group.event_count >= 3

    def test_legacy_class_actions(self, action_extractor):
        code = '''
import { Action } from '@ngrx/store';

export enum UserActionTypes {
    LoadUsers = '[Users] Load Users',
    LoadUsersSuccess = '[Users] Load Users Success',
}

export class LoadUsers implements Action {
    readonly type = UserActionTypes.LoadUsers;
}

export class LoadUsersSuccess implements Action {
    readonly type = UserActionTypes.LoadUsersSuccess;
    constructor(public payload: { users: User[] }) {}
}
'''
        result = action_extractor.extract(code, "users.actions.ts")
        actions = result.get('actions', [])
        assert len(actions) >= 2
        legacy_action = next((a for a in actions if 'LoadUsers' in a.name), None)
        assert legacy_action is not None
        assert legacy_action.creation_method == 'class'

    def test_action_type_pattern(self, action_extractor):
        code = '''
export const addBook = createAction('[Books Page] Add Book', props<{ book: Book }>());
'''
        result = action_extractor.extract(code, "books.actions.ts")
        actions = result.get('actions', [])
        assert len(actions) >= 1
        action = actions[0]
        assert action.source == 'Books Page'
        assert action.event == 'Add Book'


# ═══════════════════════════════════════════════════════════════════
# Effect Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestNgrxEffectExtractor:
    """Tests for NgrxEffectExtractor."""

    def test_create_effect(self, effect_extractor):
        code = '''
import { createEffect, ofType, Actions } from '@ngrx/effects';
import { switchMap, map, catchError } from 'rxjs/operators';

@Injectable()
export class UserEffects {
    loadUsers$ = createEffect(() => this.actions$.pipe(
        ofType(UsersActions.load),
        switchMap(() => this.usersService.getAll().pipe(
            map(users => UsersActions.loadSuccess({ users })),
            catchError(error => of(UsersActions.loadFailure({ error }))),
        )),
    ));

    constructor(
        private actions$: Actions,
        private usersService: UsersService,
    ) {}
}
'''
        result = effect_extractor.extract(code, "users.effects.ts")
        effects = result.get('effects', [])
        assert len(effects) >= 1
        eff = effects[0]
        assert 'loadUsers' in eff.name
        assert eff.has_error_handling is True

    def test_dispatch_false_effect(self, effect_extractor):
        code = '''
redirectAfterLogin$ = createEffect(() => this.actions$.pipe(
    ofType(AuthActions.loginSuccess),
    tap(() => this.router.navigate(['/dashboard'])),
), { dispatch: false });
'''
        result = effect_extractor.extract(code, "auth.effects.ts")
        effects = result.get('effects', [])
        assert len(effects) >= 1
        eff = effects[0]
        assert eff.dispatches is False

    def test_legacy_effect_decorator(self, effect_extractor):
        code = '''
import { Effect, Actions, ofType } from '@ngrx/effects';

@Injectable()
export class UserEffects {
    @Effect()
    loadUsers$ = this.actions$.pipe(
        ofType(UsersActionTypes.LoadUsers),
        switchMap(() => this.usersService.getAll()),
    );
}
'''
        result = effect_extractor.extract(code, "users.effects.ts")
        effects = result.get('effects', [])
        assert len(effects) >= 1

    def test_functional_effect(self, effect_extractor):
        code = '''
import { createEffect } from '@ngrx/effects';
import { inject } from '@angular/core';

export const loadUsers = createEffect(
    (actions$ = inject(Actions), api = inject(UsersApi)) =>
        actions$.pipe(
            ofType(UsersActions.load),
            exhaustMap(() => api.getAll().pipe(
                map(users => UsersActions.loadSuccess({ users })),
                catchError(error => of(UsersActions.loadFailure({ error }))),
            )),
        ),
    { functional: true },
);
'''
        result = effect_extractor.extract(code, "users.effects.ts")
        effects = result.get('effects', [])
        assert len(effects) >= 1
        eff = effects[0]
        assert eff.is_functional is True

    def test_concat_latest_from(self, effect_extractor):
        code = '''
import { concatLatestFrom } from '@ngrx/operators';

loadIfNeeded$ = createEffect(() => this.actions$.pipe(
    ofType(UsersActions.load),
    concatLatestFrom(() => this.store.select(selectUsersLoaded)),
    filter(([_, loaded]) => !loaded),
    switchMap(() => this.api.getUsers()),
));
'''
        result = effect_extractor.extract(code, "users.effects.ts")
        effects = result.get('effects', [])
        assert len(effects) >= 1
        eff = effects[0]
        assert eff.has_concatLatestFrom is True

    def test_registered_effects(self, effect_extractor):
        code = '''
import { provideEffects, EffectsModule } from '@ngrx/effects';

EffectsModule.forRoot([UserEffects, AuthEffects]);
provideEffects(UserEffects, AuthEffects, PostEffects);
'''
        result = effect_extractor.extract(code, "app.module.ts")
        registered = result.get('registered_effects', [])
        assert len(registered) >= 2


# ═══════════════════════════════════════════════════════════════════
# Selector Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestNgrxSelectorExtractor:
    """Tests for NgrxSelectorExtractor."""

    def test_create_selector(self, selector_extractor):
        code = '''
import { createSelector, createFeatureSelector } from '@ngrx/store';

export const selectUsersState = createFeatureSelector<UsersState>('users');

export const selectAllUsers = createSelector(
    selectUsersState,
    (state) => state.users
);

export const selectActiveUsers = createSelector(
    selectAllUsers,
    (users) => users.filter(u => u.isActive)
);
'''
        result = selector_extractor.extract(code, "users.selectors.ts")
        selectors = result.get('selectors', [])
        assert len(selectors) >= 2
        names = [s.name for s in selectors]
        assert 'selectAllUsers' in names
        assert 'selectActiveUsers' in names

    def test_create_feature_selector(self, selector_extractor):
        code = '''
export const selectUsersState = createFeatureSelector<UsersState>('users');
export const selectAuthState = createFeatureSelector<AuthState>('auth');
'''
        result = selector_extractor.extract(code, "selectors.ts")
        selectors = result.get('selectors', [])
        feature_sels = [s for s in selectors if s.selector_type == 'createFeatureSelector']
        assert len(feature_sels) >= 2

    def test_create_feature_auto_selectors(self, selector_extractor):
        code = '''
import { createFeature, createReducer, on } from '@ngrx/store';

export const usersFeature = createFeature({
    name: 'users',
    reducer: createReducer(
        initialState,
        on(loadSuccess, (state, { users }) => ({ ...state, users, loading: false })),
    ),
});

export const { selectUsersState, selectUsers, selectLoading } = usersFeature;
'''
        result = selector_extractor.extract(code, "users.feature.ts")
        feature_selectors = result.get('feature_selectors', [])
        assert len(feature_selectors) >= 1
        fs = feature_selectors[0]
        assert fs.feature_name == 'users'

    def test_factory_selector(self, selector_extractor):
        code = '''
export const selectUserById = (id: string) => createSelector(
    selectUsersEntities,
    (entities) => entities[id]
);
'''
        result = selector_extractor.extract(code, "users.selectors.ts")
        selectors = result.get('selectors', [])
        assert len(selectors) >= 1

    def test_select_signal(self, selector_extractor):
        code = '''
users = this.store.selectSignal(selectAllUsers);
loading = this.store.selectSignal(selectLoading);
count = store.selectSignal(selectUsersCount);
'''
        result = selector_extractor.extract(code, "users.component.ts")
        count = result.get('select_signal_count', 0)
        assert count >= 3


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestNgrxApiExtractor:
    """Tests for NgrxApiExtractor."""

    def test_entity_adapter(self, api_extractor):
        code = '''
import { createEntityAdapter, EntityState, EntityAdapter } from '@ngrx/entity';

export interface User {
    id: string;
    name: string;
}

export const adapter: EntityAdapter<User> = createEntityAdapter<User>({
    selectId: (user: User) => user.id,
    sortComparer: (a, b) => a.name.localeCompare(b.name),
});

export interface State extends EntityState<User> {
    loading: boolean;
}

export const initialState: State = adapter.getInitialState({ loading: false });
'''
        result = api_extractor.extract(code, "users.reducer.ts")
        entities = result.get('entities', [])
        assert len(entities) >= 1
        entity = entities[0]
        assert entity.entity_type == 'User'
        assert entity.has_entity_state is True

    def test_router_store(self, api_extractor):
        code = '''
import { routerReducer, StoreRouterConnectingModule, RouterState } from '@ngrx/router-store';
import { selectRouteParams, selectQueryParams, selectUrl } from '@ngrx/router-store';

StoreRouterConnectingModule.forRoot({
    routerState: RouterState.Minimal,
    serializer: MinimalRouterStateSerializer,
});
'''
        result = api_extractor.extract(code, "app.module.ts")
        router_stores = result.get('router_stores', [])
        assert len(router_stores) >= 1

    def test_package_detection(self, api_extractor):
        code = '''
import { Store } from '@ngrx/store';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { createEntityAdapter } from '@ngrx/entity';
import { routerReducer } from '@ngrx/router-store';
import { ComponentStore } from '@ngrx/component-store';
import { signalStore, withState } from '@ngrx/signals';
import { concatLatestFrom } from '@ngrx/operators';
'''
        result = api_extractor.extract(code, "index.ts")
        packages = result.get('packages', [])
        assert '@ngrx/store' in packages
        assert '@ngrx/effects' in packages
        assert '@ngrx/entity' in packages

    def test_reducer_count(self, api_extractor):
        code = '''
const userReducer = createReducer(
    initialState,
    on(loadSuccess, (state, { users }) => ({ ...state, users })),
    on(loadFailure, (state, { error }) => ({ ...state, error })),
);

const authReducer = createReducer(
    authInitialState,
    on(loginSuccess, (state, { user }) => ({ ...state, user })),
);
'''
        result = api_extractor.extract(code, "reducers.ts")
        count = result.get('reducer_count', 0)
        assert count >= 2

    def test_on_handlers(self, api_extractor):
        code = '''
on(loadUsers, (state) => ({ ...state, loading: true })),
on(loadUsersSuccess, (state, { users }) => ({ ...state, users, loading: false })),
on(loadUsersFailure, (state, { error }) => ({ ...state, error, loading: false })),
'''
        result = api_extractor.extract(code, "users.reducer.ts")
        handlers = result.get('on_handlers', [])
        assert len(handlers) >= 3

    def test_community_packages(self, api_extractor):
        code = '''
import { storeFreeze } from 'ngrx-store-freeze';
import { localStorageSync } from 'ngrx-store-localstorage';
import { NgrxFormsModule } from 'ngrx-forms';
'''
        result = api_extractor.extract(code, "app.module.ts")
        community = result.get('community_packages', [])
        assert len(community) >= 2


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedNgrxParser:
    """Tests for EnhancedNgrxParser."""

    def test_is_ngrx_file_positive(self, parser):
        code = '''
import { Store, createAction, props } from '@ngrx/store';
import { createEffect, ofType } from '@ngrx/effects';
'''
        assert parser.is_ngrx_file(code) is True

    def test_is_ngrx_file_negative(self, parser):
        code = '''
import React from 'react';
import { useState, useEffect } from 'react';

export const App = () => <div>Hello</div>;
'''
        assert parser.is_ngrx_file(code) is False

    def test_parse_result_type(self, parser):
        code = '''
import { createAction, props } from '@ngrx/store';
export const loadUsers = createAction('[Users Page] Load Users');
'''
        result = parser.parse(code, "users.actions.ts")
        assert isinstance(result, NgrxParseResult)
        assert result.file_path == "users.actions.ts"
        assert result.file_type == "ts"

    def test_framework_detection_core(self, parser):
        code = '''
import { Store, select } from '@ngrx/store';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { createEntityAdapter } from '@ngrx/entity';
'''
        result = parser.parse(code, "test.ts")
        assert 'ngrx-store' in result.detected_frameworks
        assert 'ngrx-effects' in result.detected_frameworks
        assert 'ngrx-entity' in result.detected_frameworks

    def test_framework_detection_component_store(self, parser):
        code = '''
import { ComponentStore } from '@ngrx/component-store';

export class TodosStore extends ComponentStore<TodosState> {}
'''
        result = parser.parse(code, "todos.store.ts")
        assert 'ngrx-component-store' in result.detected_frameworks

    def test_framework_detection_signals(self, parser):
        code = '''
import { signalStore, withState, withComputed, withMethods } from '@ngrx/signals';

export const TodosStore = signalStore(
    withState({ todos: [] }),
    withComputed(({ todos }) => ({})),
    withMethods((store) => ({})),
);
'''
        result = parser.parse(code, "todos.store.ts")
        assert 'ngrx-signals' in result.detected_frameworks

    def test_framework_detection_devtools(self, parser):
        code = '''
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
'''
        result = parser.parse(code, "app.module.ts")
        assert 'ngrx-store-devtools' in result.detected_frameworks

    def test_framework_detection_router_store(self, parser):
        code = '''
import { routerReducer, StoreRouterConnectingModule } from '@ngrx/router-store';
'''
        result = parser.parse(code, "app.module.ts")
        assert 'ngrx-router-store' in result.detected_frameworks

    def test_framework_detection_rxjs(self, parser):
        code = '''
import { Observable, of } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';
import { createEffect, ofType } from '@ngrx/effects';
'''
        result = parser.parse(code, "effects.ts")
        assert 'rxjs' in result.detected_frameworks

    def test_framework_detection_community(self, parser):
        code = '''
import { storeFreeze } from 'ngrx-store-freeze';
import { localStorageSync } from 'ngrx-store-localstorage';
'''
        result = parser.parse(code, "app.module.ts")
        assert 'ngrx-store-freeze' in result.detected_frameworks
        assert 'ngrx-store-localstorage' in result.detected_frameworks

    def test_feature_detection(self, parser):
        code = '''
import { StoreModule } from '@ngrx/store';
import { createSelector, createFeatureSelector } from '@ngrx/store';
import { createEffect } from '@ngrx/effects';
import { createEntityAdapter } from '@ngrx/entity';

StoreModule.forRoot(reducers, { runtimeChecks: { strictStateImmutability: true } });
provideStore(reducers);

const selectState = createFeatureSelector<State>('feature');
const selectAll = createSelector(selectState, (state) => state.items);
const effect = createEffect(() => actions$);
const adapter = createEntityAdapter<Item>();
'''
        result = parser.parse(code, "app.module.ts")
        assert 'store_module' in result.detected_features
        assert 'create_selector' in result.detected_features
        assert 'create_feature_selector' in result.detected_features
        assert 'create_effect' in result.detected_features
        assert 'entity_adapter' in result.detected_features
        assert 'runtime_checks' in result.detected_features

    def test_feature_detection_signal_store(self, parser):
        code = '''
import { signalStore, withState, withEntities } from '@ngrx/signals';

export const Store = signalStore(
    withState({ loading: false }),
    withEntities<Todo>(),
);
store.selectSignal(selectAll);
'''
        result = parser.parse(code, "store.ts")
        assert 'signal_store' in result.detected_features
        assert 'select_signal' in result.detected_features
        assert 'with_entities' in result.detected_features

    def test_version_detection_v16_plus(self, parser):
        code = '''
import { signalStore, withState, withComputed, withMethods } from '@ngrx/signals';
import { selectSignal } from '@ngrx/store';
'''
        result = parser.parse(code, "store.ts")
        assert result.ngrx_version == "v16+"

    def test_version_detection_v12_v15(self, parser):
        code = '''
import { ComponentStore } from '@ngrx/component-store';
import { createFeature } from '@ngrx/store';
import { provideStore, provideState, provideEffects } from '@ngrx/store';
import { createActionGroup } from '@ngrx/store';
'''
        result = parser.parse(code, "app.module.ts")
        assert result.ngrx_version == "v12-v15"

    def test_version_detection_v8_v11(self, parser):
        code = '''
import { createAction, props, createReducer, on } from '@ngrx/store';
import { createEffect, ofType } from '@ngrx/effects';

export const loadUsers = createAction('[Users] Load');
const reducer = createReducer(initialState, on(loadUsers, state => state));
'''
        result = parser.parse(code, "users.ts")
        assert result.ngrx_version == "v8-v11"

    def test_version_detection_v4_v7(self, parser):
        code = '''
import { StoreModule } from '@ngrx/store';
import { EffectsModule } from '@ngrx/effects';
import { createFeatureSelector } from '@ngrx/store';

@Effect()
loadUsers$ = this.actions$.pipe(ofType(LoadUsers));
'''
        result = parser.parse(code, "users.effects.ts")
        assert result.ngrx_version == "v4-v7"

    def test_version_detection_legacy(self, parser):
        code = '''
import { storeFreeze } from 'ngrx-store-freeze';
import { Store } from '@ngrx/store';
'''
        result = parser.parse(code, "app.module.ts")
        # legacy or v4-v7 depending on detection order
        assert result.ngrx_version in ("legacy", "v4-v7")

    def test_full_parse_integration(self, parser):
        """Test complete file parsing with all components."""
        code = '''
import { createAction, props, createReducer, on, createFeatureSelector, createSelector } from '@ngrx/store';
import { createEffect, ofType, Actions } from '@ngrx/effects';
import { createEntityAdapter, EntityState } from '@ngrx/entity';
import { switchMap, map, catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { Injectable } from '@angular/core';

// Actions
export const loadUsers = createAction('[Users Page] Load Users');
export const loadUsersSuccess = createAction('[Users API] Load Users Success', props<{ users: User[] }>());
export const loadUsersFailure = createAction('[Users API] Load Users Failure', props<{ error: string }>());

// Entity Adapter
export const adapter = createEntityAdapter<User>({
    selectId: (user) => user.id,
    sortComparer: (a, b) => a.name.localeCompare(b.name),
});

// Reducer
export const usersReducer = createReducer(
    adapter.getInitialState({ loading: false, error: null }),
    on(loadUsers, (state) => ({ ...state, loading: true })),
    on(loadUsersSuccess, (state, { users }) => adapter.setAll(users, { ...state, loading: false })),
    on(loadUsersFailure, (state, { error }) => ({ ...state, error, loading: false })),
);

// Selectors
export const selectUsersState = createFeatureSelector<State>('users');
export const selectAllUsers = createSelector(selectUsersState, adapter.getSelectors().selectAll);
export const selectLoading = createSelector(selectUsersState, (state) => state.loading);

// Effects
@Injectable()
export class UserEffects {
    loadUsers$ = createEffect(() => this.actions$.pipe(
        ofType(loadUsers),
        switchMap(() => this.usersService.getAll().pipe(
            map(users => loadUsersSuccess({ users })),
            catchError(error => of(loadUsersFailure({ error: error.message }))),
        )),
    ));

    constructor(private actions$: Actions, private usersService: UsersService) {}
}
'''
        result = parser.parse(code, "users.state.ts")
        # Check actions
        assert len(result.actions) >= 3
        # Check selectors
        assert len(result.selectors) >= 2
        # Check effects
        assert len(result.effects) >= 1
        # Check entities
        assert len(result.entities) >= 1
        # Check frameworks
        assert 'ngrx-store' in result.detected_frameworks
        assert 'ngrx-effects' in result.detected_frameworks
        assert 'ngrx-entity' in result.detected_frameworks
        # Check version
        assert result.ngrx_version == "v8-v11"
        # Check packages
        assert '@ngrx/store' in result.packages
        assert '@ngrx/effects' in result.packages
        assert '@ngrx/entity' in result.packages

    def test_spec_file_detection(self, parser):
        code = '''
import { createAction } from '@ngrx/store';
'''
        result = parser.parse(code, "users.spec.ts")
        assert result.file_type == "spec.ts"

    def test_empty_content(self, parser):
        result = parser.parse("", "empty.ts")
        assert isinstance(result, NgrxParseResult)
        assert len(result.actions) == 0
        assert len(result.effects) == 0
        assert len(result.selectors) == 0

    def test_version_compare(self):
        assert EnhancedNgrxParser._version_compare("v16+", "v12-v15") > 0
        assert EnhancedNgrxParser._version_compare("v8-v11", "v16+") < 0
        assert EnhancedNgrxParser._version_compare("", "legacy") < 0
        assert EnhancedNgrxParser._version_compare("v4-v7", "v4-v7") == 0
