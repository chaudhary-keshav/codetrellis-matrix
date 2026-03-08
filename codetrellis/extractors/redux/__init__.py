"""
CodeTrellis Redux / Redux Toolkit Extractors Module v1.0

Provides comprehensive extractors for Redux and Redux Toolkit framework constructs:

Store Extractor:
- ReduxStoreExtractor: configureStore, createStore (legacy), store enhancers,
                        reducer composition (combineReducers), store setup
                        patterns, persistor/rehydration (redux-persist),
                        devtools configuration, preloadedState

Slice Extractor:
- ReduxSliceExtractor: createSlice definitions, reducers (sync), extraReducers
                        (async thunk lifecycle), prepare callbacks, createEntityAdapter
                        (CRUD operations, selectAll/selectById), initial state shape,
                        action creators (auto-generated + exported), selector generation

Middleware Extractor:
- ReduxMiddlewareExtractor: createAsyncThunk, createListenerMiddleware (v1.8+),
                             redux-thunk, redux-saga (generator effects: takeEvery,
                             takeLatest, call, put, select, fork, all, race),
                             redux-observable (Epics, ofType, mergeMap, switchMap),
                             custom middleware (store => next => action),
                             RTK listener API (startListening, addListener, effect)

Selector Extractor:
- ReduxSelectorExtractor: createSelector (reselect), createDraftSafeSelector,
                            createEntityAdapter selectors (selectAll, selectById,
                            selectIds, selectEntities, selectTotal),
                            useSelector hook usage, typed hooks (useAppSelector),
                            selector composition/memoization patterns,
                            createStructuredSelector, input/output selectors

API Extractor:
- ReduxApiExtractor: RTK Query (createApi, fetchBaseQuery, endpoints: query/mutation,
                      cache tags (providesTags/invalidatesTags), cache lifecycle
                      (onCacheEntryAdded, onQueryStarted), code generation,
                      transformResponse/transformErrorResponse, polling,
                      streaming updates, optimistic updates, prefetching,
                      injectEndpoints, enhanceEndpoints)

Part of CodeTrellis v4.47 - Redux / Redux Toolkit Framework Support
"""

from .store_extractor import (
    ReduxStoreExtractor,
    ReduxStoreInfo,
    ReduxReducerCompositionInfo,
    ReduxPersistInfo,
)
from .slice_extractor import (
    ReduxSliceExtractor,
    ReduxSliceInfo,
    ReduxEntityAdapterInfo,
    ReduxActionCreatorInfo,
)
from .middleware_extractor import (
    ReduxMiddlewareExtractor,
    ReduxAsyncThunkInfo,
    ReduxSagaInfo,
    ReduxObservableInfo,
    ReduxListenerInfo,
    ReduxCustomMiddlewareInfo,
)
from .selector_extractor import (
    ReduxSelectorExtractor,
    ReduxSelectorInfo,
    ReduxTypedHookInfo,
)
from .api_extractor import (
    ReduxApiExtractor,
    ReduxRTKQueryApiInfo,
    ReduxRTKQueryEndpointInfo,
    ReduxCacheTagInfo,
)

__all__ = [
    # Store
    "ReduxStoreExtractor",
    "ReduxStoreInfo",
    "ReduxReducerCompositionInfo",
    "ReduxPersistInfo",
    # Slice
    "ReduxSliceExtractor",
    "ReduxSliceInfo",
    "ReduxEntityAdapterInfo",
    "ReduxActionCreatorInfo",
    # Middleware
    "ReduxMiddlewareExtractor",
    "ReduxAsyncThunkInfo",
    "ReduxSagaInfo",
    "ReduxObservableInfo",
    "ReduxListenerInfo",
    "ReduxCustomMiddlewareInfo",
    # Selector
    "ReduxSelectorExtractor",
    "ReduxSelectorInfo",
    "ReduxTypedHookInfo",
    # API (RTK Query)
    "ReduxApiExtractor",
    "ReduxRTKQueryApiInfo",
    "ReduxRTKQueryEndpointInfo",
    "ReduxCacheTagInfo",
]
