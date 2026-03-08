"""
CodeTrellis NgRx Extractors Module v1.0

Provides comprehensive extractors for NgRx state management framework constructs:

Store Extractor:
- NgrxStoreExtractor: StoreModule.forRoot/forFeature, provideStore/provideState,
                       StoreDevtoolsModule, provideStoreDevtools,
                       store.dispatch(), store.select(), store.pipe(),
                       ComponentStore (setState, patchState, updater, select, effect),
                       SignalStore (signalStore, withState, withComputed, withMethods,
                       withHooks, patchState, signalStoreFeature)

Effect Extractor:
- NgrxEffectExtractor: createEffect, Actions service, ofType operator,
                        concatLatestFrom/concatMap/switchMap/mergeMap/exhaustMap,
                        dispatch: false (non-dispatching), functional effects (v16+),
                        effect lifecycle (OnInitEffects, OnRunEffects, OnIdentifyEffects),
                        ComponentStore effects (this.effect()), root effects

Selector Extractor:
- NgrxSelectorExtractor: createSelector, createFeatureSelector,
                          feature selectors, selector composition,
                          props selectors (deprecated v13+), memoization,
                          selectSignal (v16+), store.selectSignal()

Action Extractor:
- NgrxActionExtractor: createAction, createActionGroup, props<T>(),
                        emptyProps(), action creators, action types,
                        [Source] Event pattern naming

API Extractor:
- NgrxApiExtractor: @ngrx/store, @ngrx/effects, @ngrx/entity,
                     @ngrx/store-devtools, @ngrx/router-store,
                     @ngrx/component-store, @ngrx/signals,
                     @ngrx/operators, @ngrx/eslint-plugin,
                     @ngrx/schematics, ngrx-store-freeze

Part of CodeTrellis v4.53 - NgRx Framework Support
"""

from .store_extractor import (
    NgrxStoreExtractor,
    NgrxStoreInfo,
    NgrxComponentStoreInfo,
    NgrxSignalStoreInfo,
    NgrxDevToolsConfig,
)
from .effect_extractor import (
    NgrxEffectExtractor,
    NgrxEffectInfo,
    NgrxComponentStoreEffectInfo,
)
from .selector_extractor import (
    NgrxSelectorExtractor,
    NgrxSelectorInfo,
    NgrxFeatureSelectorInfo,
)
from .action_extractor import (
    NgrxActionExtractor,
    NgrxActionInfo,
    NgrxActionGroupInfo,
)
from .api_extractor import (
    NgrxApiExtractor,
    NgrxEntityInfo,
    NgrxRouterStoreInfo,
)

__all__ = [
    # Store
    "NgrxStoreExtractor",
    "NgrxStoreInfo",
    "NgrxComponentStoreInfo",
    "NgrxSignalStoreInfo",
    "NgrxDevToolsConfig",
    # Effect
    "NgrxEffectExtractor",
    "NgrxEffectInfo",
    "NgrxComponentStoreEffectInfo",
    # Selector
    "NgrxSelectorExtractor",
    "NgrxSelectorInfo",
    "NgrxFeatureSelectorInfo",
    # Action
    "NgrxActionExtractor",
    "NgrxActionInfo",
    "NgrxActionGroupInfo",
    # API
    "NgrxApiExtractor",
    "NgrxEntityInfo",
    "NgrxRouterStoreInfo",
]
