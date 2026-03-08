"""
Tests for Redux / Redux Toolkit extractors and EnhancedReduxParser.

Part of CodeTrellis v4.47 Redux / Redux Toolkit Framework Support.
Tests cover:
- Store extraction (configureStore, createStore, combineReducers, redux-persist)
- Slice extraction (createSlice, reducers, extraReducers, entity adapters)
- Middleware extraction (createAsyncThunk, sagas, epics, listeners, custom)
- Selector extraction (createSelector, typed hooks, entity selectors)
- RTK Query extraction (createApi, endpoints, cache tags, generated hooks)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from codetrellis.redux_parser_enhanced import (
    EnhancedReduxParser,
    ReduxParseResult,
)
from codetrellis.extractors.redux import (
    ReduxStoreExtractor,
    ReduxSliceExtractor,
    ReduxMiddlewareExtractor,
    ReduxSelectorExtractor,
    ReduxApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedReduxParser()


@pytest.fixture
def store_extractor():
    return ReduxStoreExtractor()


@pytest.fixture
def slice_extractor():
    return ReduxSliceExtractor()


@pytest.fixture
def middleware_extractor():
    return ReduxMiddlewareExtractor()


@pytest.fixture
def selector_extractor():
    return ReduxSelectorExtractor()


@pytest.fixture
def api_extractor():
    return ReduxApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Store Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestReduxStoreExtractor:
    """Tests for ReduxStoreExtractor."""

    def test_configure_store(self, store_extractor):
        code = '''
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import postsReducer from './postsSlice';

export const store = configureStore({
    reducer: {
        auth: authReducer,
        posts: postsReducer,
    },
    devTools: process.env.NODE_ENV !== 'production',
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
'''
        result = store_extractor.extract(code, "store.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        store = stores[0]
        assert store.creation_method == 'configureStore'

    def test_legacy_create_store(self, store_extractor):
        code = '''
import { createStore, applyMiddleware, compose } from 'redux';
import rootReducer from './rootReducer';
import thunk from 'redux-thunk';

const store = createStore(
    rootReducer,
    applyMiddleware(thunk)
);
'''
        result = store_extractor.extract(code, "store.js")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        store = stores[0]
        assert store.creation_method == 'createStore'

    def test_combine_reducers(self, store_extractor):
        code = '''
import { combineReducers } from 'redux';
import usersReducer from './usersReducer';
import postsReducer from './postsReducer';
import commentsReducer from './commentsReducer';

const rootReducer = combineReducers({
    users: usersReducer,
    posts: postsReducer,
    comments: commentsReducer,
});

export default rootReducer;
'''
        result = store_extractor.extract(code, "rootReducer.ts")
        compositions = result.get('reducer_compositions', [])
        assert len(compositions) >= 1

    def test_redux_persist(self, store_extractor):
        code = '''
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import rootReducer from './rootReducer';

const persistConfig = {
    key: 'root',
    storage,
    whitelist: ['auth', 'settings'],
    blacklist: ['form'],
    version: 1,
};

const persistedReducer = persistReducer(persistConfig, rootReducer);
'''
        result = store_extractor.extract(code, "store.ts")
        persist_configs = result.get('persist_configs', [])
        assert len(persist_configs) >= 1

    def test_root_state_type(self, store_extractor):
        code = '''
import { configureStore } from '@reduxjs/toolkit';

const store = configureStore({ reducer: rootReducer });
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
'''
        result = store_extractor.extract(code, "store.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1


# ═══════════════════════════════════════════════════════════════════
# Slice Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestReduxSliceExtractor:
    """Tests for ReduxSliceExtractor."""

    def test_basic_create_slice(self, slice_extractor):
        code = '''
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface CounterState {
    value: number;
}

const initialState: CounterState = { value: 0 };

const counterSlice = createSlice({
    name: 'counter',
    initialState,
    reducers: {
        incremented(state) {
            state.value += 1;
        },
        decremented(state) {
            state.value -= 1;
        },
        amountAdded(state, action: PayloadAction<number>) {
            state.value += action.payload;
        },
    },
});

export const { incremented, decremented, amountAdded } = counterSlice.actions;
export default counterSlice.reducer;
'''
        result = slice_extractor.extract(code, "counterSlice.ts")
        slices = result.get('slices', [])
        assert len(slices) >= 1
        sl = slices[0]
        assert sl.slice_name == 'counter'
        assert 'incremented' in sl.reducers
        assert 'decremented' in sl.reducers

    def test_slice_with_extra_reducers(self, slice_extractor):
        code = '''
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

const fetchUser = createAsyncThunk('users/fetch', async (userId) => {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
});

const usersSlice = createSlice({
    name: 'users',
    initialState: { entities: [], loading: false, error: null },
    reducers: {},
    extraReducers: (builder) => {
        builder
            .addCase(fetchUser.pending, (state) => {
                state.loading = true;
            })
            .addCase(fetchUser.fulfilled, (state, action) => {
                state.loading = false;
                state.entities.push(action.payload);
            })
            .addCase(fetchUser.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message;
            });
    },
});
'''
        result = slice_extractor.extract(code, "usersSlice.ts")
        slices = result.get('slices', [])
        assert len(slices) >= 1
        assert slices[0].slice_name == 'users'

    def test_entity_adapter(self, slice_extractor):
        code = '''
import { createSlice, createEntityAdapter } from '@reduxjs/toolkit';

const booksAdapter = createEntityAdapter({
    selectId: (book) => book.isbn,
    sortComparer: (a, b) => a.title.localeCompare(b.title),
});

const booksSlice = createSlice({
    name: 'books',
    initialState: booksAdapter.getInitialState({ loading: false }),
    reducers: {
        bookAdded: booksAdapter.addOne,
        booksReceived: booksAdapter.setAll,
        bookUpdated: booksAdapter.updateOne,
    },
});
'''
        result = slice_extractor.extract(code, "booksSlice.ts")
        entity_adapters = result.get('entity_adapters', [])
        assert len(entity_adapters) >= 1

    def test_prepare_callback(self, slice_extractor):
        code = '''
import { createSlice, nanoid } from '@reduxjs/toolkit';

const todosSlice = createSlice({
    name: 'todos',
    initialState: [],
    reducers: {
        todoAdded: {
            reducer(state, action) {
                state.push(action.payload);
            },
            prepare(text) {
                return { payload: { id: nanoid(), text, completed: false } };
            },
        },
    },
});
'''
        result = slice_extractor.extract(code, "todosSlice.ts")
        slices = result.get('slices', [])
        assert len(slices) >= 1

    def test_rtk_v2_slice_selectors(self, slice_extractor):
        code = '''
import { createSlice } from '@reduxjs/toolkit';

const counterSlice = createSlice({
    name: 'counter',
    initialState: { value: 0 },
    reducers: {
        incremented: (state) => { state.value += 1; },
    },
    selectors: {
        selectCount: (state) => state.value,
        selectIsPositive: (state) => state.value > 0,
    },
});

export const { selectCount, selectIsPositive } = counterSlice.selectors;
'''
        result = slice_extractor.extract(code, "counterSlice.ts")
        slices = result.get('slices', [])
        assert len(slices) >= 1


# ═══════════════════════════════════════════════════════════════════
# Middleware Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestReduxMiddlewareExtractor:
    """Tests for ReduxMiddlewareExtractor."""

    def test_create_async_thunk(self, middleware_extractor):
        code = '''
import { createAsyncThunk } from '@reduxjs/toolkit';

export const fetchUsers = createAsyncThunk(
    'users/fetchAll',
    async (_, { rejectWithValue }) => {
        try {
            const response = await fetch('/api/users');
            return await response.json();
        } catch (err) {
            return rejectWithValue(err.message);
        }
    }
);

export const createUser = createAsyncThunk(
    'users/create',
    async (userData, thunkAPI) => {
        const response = await fetch('/api/users', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
        return await response.json();
    },
    {
        condition: (_, { getState }) => {
            const { users } = getState();
            return !users.loading;
        },
    }
);
'''
        result = middleware_extractor.extract(code, "usersThunks.ts")
        thunks = result.get('async_thunks', [])
        assert len(thunks) >= 2
        names = [t.name for t in thunks]
        assert 'fetchUsers' in names
        assert 'createUser' in names

    def test_redux_saga(self, middleware_extractor):
        code = '''
import { takeEvery, takeLatest, call, put, select } from 'redux-saga/effects';
import { fetchUsersSuccess, fetchUsersFailure } from './usersSlice';
import api from '../api';

function* fetchUsersSaga() {
    try {
        const users = yield call(api.getUsers);
        yield put(fetchUsersSuccess(users));
    } catch (error) {
        yield put(fetchUsersFailure(error.message));
    }
}

function* watchFetchUsers() {
    yield takeLatest('users/fetchRequested', fetchUsersSaga);
}

export default function* rootSaga() {
    yield all([
        watchFetchUsers(),
    ]);
}
'''
        result = middleware_extractor.extract(code, "usersSaga.ts")
        sagas = result.get('sagas', [])
        assert len(sagas) >= 1

    def test_redux_observable_epic(self, middleware_extractor):
        code = '''
import { ofType } from 'redux-observable';
import { mergeMap, map, catchError } from 'rxjs/operators';
import { of, from } from 'rxjs';

const fetchUsersEpic = (action$) =>
    action$.pipe(
        ofType('users/fetch'),
        mergeMap((action) =>
            from(api.fetchUsers()).pipe(
                map((users) => fetchUsersSuccess(users)),
                catchError((error) => of(fetchUsersFailure(error.message)))
            )
        )
    );
'''
        result = middleware_extractor.extract(code, "usersEpic.ts")
        epics = result.get('epics', [])
        assert len(epics) >= 1

    def test_create_listener_middleware(self, middleware_extractor):
        code = '''
import { createListenerMiddleware } from '@reduxjs/toolkit';

const listenerMiddleware = createListenerMiddleware();

listenerMiddleware.startListening({
    actionCreator: userLoggedIn,
    effect: async (action, listenerApi) => {
        const { userId } = action.payload;
        listenerApi.dispatch(fetchUserProfile(userId));
        listenerApi.cancelActiveListeners();
    },
});

listenerMiddleware.startListening({
    matcher: isAnyOf(userLoggedIn, userUpdated),
    effect: async (action, listenerApi) => {
        listenerApi.dispatch(refreshDashboard());
    },
});
'''
        result = middleware_extractor.extract(code, "listeners.ts")
        listeners = result.get('listeners', [])
        assert len(listeners) >= 1

    def test_custom_middleware(self, middleware_extractor):
        code = '''
const loggerMiddleware = (store) => (next) => (action) => {
    console.log('dispatching', action);
    const result = next(action);
    console.log('next state', store.getState());
    return result;
};

const crashReporter = (store) => (next) => (action) => {
    try {
        return next(action);
    } catch (err) {
        console.error('Caught exception', err);
        throw err;
    }
};
'''
        result = middleware_extractor.extract(code, "middleware.ts")
        custom = result.get('custom_middleware', [])
        assert len(custom) >= 1


# ═══════════════════════════════════════════════════════════════════
# Selector Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestReduxSelectorExtractor:
    """Tests for ReduxSelectorExtractor."""

    def test_create_selector(self, selector_extractor):
        code = '''
import { createSelector } from '@reduxjs/toolkit';

const selectUsers = (state) => state.users.entities;
const selectFilter = (state) => state.users.filter;

export const selectFilteredUsers = createSelector(
    [selectUsers, selectFilter],
    (users, filter) => users.filter((u) => u.role === filter)
);

export const selectActiveUserCount = createSelector(
    selectUsers,
    (users) => users.filter((u) => u.isActive).length
);
'''
        result = selector_extractor.extract(code, "selectors.ts")
        selectors = result.get('selectors', [])
        assert len(selectors) >= 2

    def test_simple_state_selectors(self, selector_extractor):
        code = '''
export const selectAllUsers = (state) => state.users.entities;
export const selectUserById = (state, id) => state.users.entities[id];
export const selectIsLoading = (state) => state.users.loading;
'''
        result = selector_extractor.extract(code, "selectors.ts")
        selectors = result.get('selectors', [])
        assert len(selectors) >= 1

    def test_typed_hooks(self, selector_extractor):
        code = '''
import { useSelector, useDispatch } from 'react-redux';
import type { TypedUseSelectorHook } from 'react-redux';
import type { RootState, AppDispatch } from './store';

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
'''
        result = selector_extractor.extract(code, "hooks.ts")
        typed_hooks = result.get('typed_hooks', [])
        assert len(typed_hooks) >= 1

    def test_rtk_v2_with_types(self, selector_extractor):
        code = '''
import { useSelector, useDispatch, useStore } from 'react-redux';

export const useAppSelector = useSelector.withTypes<RootState>();
export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppStore = useStore.withTypes<AppStore>();
'''
        result = selector_extractor.extract(code, "hooks.ts")
        typed_hooks = result.get('typed_hooks', [])
        assert len(typed_hooks) >= 1


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests (RTK Query)
# ═══════════════════════════════════════════════════════════════════

class TestReduxApiExtractor:
    """Tests for ReduxApiExtractor (RTK Query)."""

    def test_create_api(self, api_extractor):
        code = '''
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const api = createApi({
    reducerPath: 'api',
    baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
    tagTypes: ['Post', 'User', 'Comment'],
    endpoints: (builder) => ({
        getPosts: builder.query({
            query: () => '/posts',
            providesTags: ['Post'],
        }),
        getPost: builder.query({
            query: (id) => `/posts/${id}`,
            providesTags: (result, error, id) => [{ type: 'Post', id }],
        }),
        addPost: builder.mutation({
            query: (body) => ({ url: '/posts', method: 'POST', body }),
            invalidatesTags: ['Post'],
        }),
        updatePost: builder.mutation({
            query: ({ id, ...patch }) => ({
                url: `/posts/${id}`,
                method: 'PATCH',
                body: patch,
            }),
            invalidatesTags: (result, error, { id }) => [{ type: 'Post', id }],
        }),
    }),
});

export const {
    useGetPostsQuery,
    useGetPostQuery,
    useAddPostMutation,
    useUpdatePostMutation,
} = api;
'''
        result = api_extractor.extract(code, "postsApi.ts")
        apis = result.get('apis', [])
        assert len(apis) >= 1
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 2

    def test_inject_endpoints(self, api_extractor):
        code = '''
import { baseApi } from './baseApi';

export const usersApi = baseApi.injectEndpoints({
    endpoints: (builder) => ({
        getUsers: builder.query({
            query: () => '/users',
        }),
        getUserById: builder.query({
            query: (id) => `/users/${id}`,
        }),
    }),
});

export const { useGetUsersQuery, useGetUserByIdQuery } = usersApi;
'''
        result = api_extractor.extract(code, "usersApi.ts")
        # injectEndpoints should also be detected
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 1

    def test_on_query_started(self, api_extractor):
        code = '''
const api = createApi({
    reducerPath: 'api',
    baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
    endpoints: (builder) => ({
        updateTodo: builder.mutation({
            query: ({ id, ...patch }) => ({ url: `/todos/${id}`, method: 'PATCH', body: patch }),
            async onQueryStarted({ id, ...patch }, { dispatch, queryFulfilled }) {
                const patchResult = dispatch(
                    api.util.updateQueryData('getTodos', undefined, (draft) => {
                        const todo = draft.find((t) => t.id === id);
                        if (todo) Object.assign(todo, patch);
                    })
                );
                try { await queryFulfilled; }
                catch { patchResult.undo(); }
            },
        }),
    }),
});
'''
        result = api_extractor.extract(code, "todosApi.ts")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 1


# ═══════════════════════════════════════════════════════════════════
# Enhanced Redux Parser Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedReduxParser:
    """Tests for EnhancedReduxParser integration."""

    def test_is_redux_file_positive(self, parser):
        code = '''
import { configureStore, createSlice } from '@reduxjs/toolkit';
'''
        assert parser.is_redux_file(code)

    def test_is_redux_file_negative(self, parser):
        code = '''
import React from 'react';
function App() { return <div>Hello</div>; }
'''
        assert not parser.is_redux_file(code)

    def test_is_redux_file_react_redux(self, parser):
        code = '''
import { useSelector, useDispatch } from 'react-redux';
'''
        assert parser.is_redux_file(code)

    def test_detect_frameworks_core(self, parser):
        code = '''
import { configureStore, createSlice } from '@reduxjs/toolkit';
import { useSelector, useDispatch } from 'react-redux';
'''
        result = parser.parse(code, "store.ts")
        assert 'reduxjs-toolkit' in result.detected_frameworks
        assert 'react-redux' in result.detected_frameworks

    def test_detect_frameworks_saga(self, parser):
        code = '''
import { takeEvery, call, put } from 'redux-saga/effects';
import createSagaMiddleware from 'redux-saga';
'''
        result = parser.parse(code, "saga.ts")
        assert 'redux-saga' in result.detected_frameworks

    def test_detect_frameworks_observable(self, parser):
        code = '''
import { ofType } from 'redux-observable';
import { createEpicMiddleware, combineEpics } from 'redux-observable';
'''
        result = parser.parse(code, "epics.ts")
        assert 'redux-observable' in result.detected_frameworks

    def test_detect_frameworks_persist(self, parser):
        code = '''
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
'''
        result = parser.parse(code, "persist.ts")
        assert 'redux-persist' in result.detected_frameworks

    def test_detect_frameworks_rtk_query(self, parser):
        code = '''
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
'''
        result = parser.parse(code, "api.ts")
        assert 'rtk-query' in result.detected_frameworks

    def test_version_detection_rtk_v2(self, parser):
        code = '''
import { configureStore, Tuple, combineSlices } from '@reduxjs/toolkit';
const useAppSelector = useSelector.withTypes<RootState>();
'''
        result = parser.parse(code, "store.ts")
        assert result.redux_version == 'rtk-v2'

    def test_version_detection_rtk_v1(self, parser):
        code = '''
import { configureStore, createSlice } from '@reduxjs/toolkit';
const store = configureStore({ reducer: rootReducer });
'''
        result = parser.parse(code, "store.ts")
        assert result.redux_version == 'rtk-v1'

    def test_version_detection_legacy(self, parser):
        code = '''
import { createStore, combineReducers, applyMiddleware } from 'redux';
'''
        result = parser.parse(code, "store.js")
        assert result.redux_version == 'legacy'

    def test_feature_detection(self, parser):
        code = '''
import { createSlice, createEntityAdapter, createAsyncThunk } from '@reduxjs/toolkit';
import { createSelector } from 'reselect';

const adapter = createEntityAdapter();
const fetchUsers = createAsyncThunk('users/fetch', async () => {});
export const useAppSelector = useSelector;
'''
        result = parser.parse(code, "features.ts")
        assert 'entity_adapter' in result.detected_features
        assert 'async_thunks' in result.detected_features

    def test_file_type_detection(self, parser):
        assert parser.parse("", "App.tsx").file_type == 'tsx'
        assert parser.parse("", "App.jsx").file_type == 'jsx'
        assert parser.parse("", "App.ts").file_type == 'ts'
        assert parser.parse("", "App.js").file_type == 'js'
        assert parser.parse("", "App.mjs").file_type == 'js'

    def test_full_store_parse(self, parser):
        code = '''
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './features/auth/authSlice';
import postsReducer from './features/posts/postsSlice';

export const store = configureStore({
    reducer: {
        auth: authReducer,
        posts: postsReducer,
    },
    devTools: process.env.NODE_ENV !== 'production',
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
'''
        result = parser.parse(code, "store.ts")
        assert isinstance(result, ReduxParseResult)
        assert result.file_type == 'ts'
        assert len(result.stores) >= 1
        assert 'reduxjs-toolkit' in result.detected_frameworks
        assert result.redux_version == 'rtk-v1'

    def test_full_slice_parse(self, parser):
        code = '''
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

export const fetchPosts = createAsyncThunk(
    'posts/fetchAll',
    async () => {
        const response = await fetch('/api/posts');
        return response.json();
    }
);

const postsSlice = createSlice({
    name: 'posts',
    initialState: { entities: [], loading: false, error: null },
    reducers: {
        postAdded(state, action) {
            state.entities.push(action.payload);
        },
        postUpdated(state, action) {
            const index = state.entities.findIndex(p => p.id === action.payload.id);
            if (index >= 0) state.entities[index] = action.payload;
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchPosts.pending, (state) => { state.loading = true; })
            .addCase(fetchPosts.fulfilled, (state, action) => {
                state.loading = false;
                state.entities = action.payload;
            })
            .addCase(fetchPosts.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message;
            });
    },
});

export const { postAdded, postUpdated } = postsSlice.actions;
export default postsSlice.reducer;
'''
        result = parser.parse(code, "postsSlice.ts")
        assert isinstance(result, ReduxParseResult)
        assert len(result.slices) >= 1
        assert len(result.async_thunks) >= 1
        assert result.slices[0].slice_name == 'posts'
        assert 'postAdded' in result.slices[0].reducers

    def test_full_rtk_query_parse(self, parser):
        code = '''
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const postsApi = createApi({
    reducerPath: 'postsApi',
    baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
    tagTypes: ['Post'],
    endpoints: (builder) => ({
        getPosts: builder.query({
            query: () => '/posts',
            providesTags: ['Post'],
        }),
        addPost: builder.mutation({
            query: (body) => ({ url: '/posts', method: 'POST', body }),
            invalidatesTags: ['Post'],
        }),
    }),
});

export const { useGetPostsQuery, useAddPostMutation } = postsApi;
'''
        result = parser.parse(code, "postsApi.ts")
        assert isinstance(result, ReduxParseResult)
        assert len(result.rtk_query_apis) >= 1
        assert 'rtk-query' in result.detected_frameworks
        assert 'rtk_query' in result.detected_features

    def test_empty_file(self, parser):
        result = parser.parse("", "empty.ts")
        assert isinstance(result, ReduxParseResult)
        assert len(result.stores) == 0
        assert len(result.slices) == 0
        assert len(result.async_thunks) == 0

    def test_non_redux_file(self, parser):
        code = '''
import React from 'react';
function App() {
    const [count, setCount] = React.useState(0);
    return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
'''
        result = parser.parse(code, "App.tsx")
        assert isinstance(result, ReduxParseResult)
        assert len(result.stores) == 0
        assert len(result.slices) == 0

    def test_mixed_framework_detection(self, parser):
        code = '''
import { configureStore, createSlice } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import createSagaMiddleware from 'redux-saga';
import { createSelector } from 'reselect';
'''
        result = parser.parse(code, "app.ts")
        assert 'reduxjs-toolkit' in result.detected_frameworks
        assert 'redux-persist' in result.detected_frameworks
        assert 'rtk-query' in result.detected_frameworks
        assert 'redux-saga' in result.detected_frameworks
        assert 'reselect' in result.detected_frameworks

    def test_redux_devtools_detection(self, parser):
        code = '''
import { composeWithDevTools } from '@redux-devtools/extension';
const store = createStore(rootReducer, composeWithDevTools(applyMiddleware(thunk)));
'''
        result = parser.parse(code, "store.js")
        assert 'redux-devtools' in result.detected_frameworks

    def test_feature_listener_middleware(self, parser):
        code = '''
import { createListenerMiddleware } from '@reduxjs/toolkit';
const listenerMiddleware = createListenerMiddleware();
listenerMiddleware.startListening({
    actionCreator: userLoggedIn,
    effect: async (action, api) => { api.dispatch(loadProfile()); },
});
'''
        result = parser.parse(code, "listeners.ts")
        assert 'listener_middleware' in result.detected_features

    def test_feature_persist(self, parser):
        code = '''
import { persistReducer, persistStore, PersistGate } from 'redux-persist';
'''
        result = parser.parse(code, "persist.ts")
        assert 'persist' in result.detected_features

    def test_redux_form_detection(self, parser):
        code = '''
import { reduxForm, Field } from 'redux-form';
const MyForm = reduxForm({ form: 'myForm' })(FormComponent);
'''
        result = parser.parse(code, "form.tsx")
        assert 'redux-form' in result.detected_frameworks

    def test_immer_detection(self, parser):
        code = '''
import { produce, enableMapSet } from 'immer';
const nextState = produce(state, draft => { draft.items.push(newItem); });
'''
        result = parser.parse(code, "utils.ts")
        assert 'immer' in result.detected_frameworks
