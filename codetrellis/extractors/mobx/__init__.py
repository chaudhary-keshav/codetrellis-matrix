"""
CodeTrellis MobX Extractors Module v1.0

Provides comprehensive extractors for MobX state management constructs:

Observable Extractor:
- MobXObservableExtractor: makeObservable(), makeAutoObservable(), observable(),
                            observable.ref, observable.shallow, observable.deep,
                            observable.struct, @observable decorator, observable maps/sets/arrays,
                            observable class fields, TypeScript generics

Computed Extractor:
- MobXComputedExtractor: computed(), computed.struct, @computed decorator,
                          computed getters, keepAlive, requiresReaction,
                          equals comparers, computed with setter

Action Extractor:
- MobXActionExtractor: action(), action.bound, @action, @action.bound,
                        runInAction(), flow(), flow.bound, @flow, flowResult(),
                        async actions, action wrapping patterns

Reaction Extractor:
- MobXReactionExtractor: autorun(), reaction(), when(), observe(), intercept(),
                          onBecomeObserved(), onBecomeUnobserved(),
                          disposer patterns, reaction options (delay, fireImmediately, scheduler)

API Extractor:
- MobXApiExtractor: Import patterns (mobx, mobx-react, mobx-react-lite),
                      configure() settings (enforceActions, computedRequiresReaction, etc.),
                      TypeScript types (IObservableValue, IComputedValue, IReactionDisposer, etc.),
                      ecosystem detection (mobx-state-tree, mobx-keystone, mobx-utils, etc.),
                      Provider/inject patterns, observer() HOC, useLocalObservable()

Part of CodeTrellis v4.51 - MobX Framework Support
"""

from .observable_extractor import (
    MobXObservableExtractor,
    MobXObservableInfo,
    MobXAutoObservableInfo,
    MobXDecoratorObservableInfo,
)
from .computed_extractor import (
    MobXComputedExtractor,
    MobXComputedInfo,
)
from .action_extractor import (
    MobXActionExtractor,
    MobXActionInfo,
    MobXFlowInfo,
)
from .reaction_extractor import (
    MobXReactionExtractor,
    MobXReactionInfo,
)
from .api_extractor import (
    MobXApiExtractor,
    MobXImportInfo,
    MobXConfigureInfo,
    MobXTypeInfo,
    MobXIntegrationInfo,
)

__all__ = [
    # Observable extractor
    "MobXObservableExtractor",
    "MobXObservableInfo",
    "MobXAutoObservableInfo",
    "MobXDecoratorObservableInfo",
    # Computed extractor
    "MobXComputedExtractor",
    "MobXComputedInfo",
    # Action extractor
    "MobXActionExtractor",
    "MobXActionInfo",
    "MobXFlowInfo",
    # Reaction extractor
    "MobXReactionExtractor",
    "MobXReactionInfo",
    # API extractor
    "MobXApiExtractor",
    "MobXImportInfo",
    "MobXConfigureInfo",
    "MobXTypeInfo",
    "MobXIntegrationInfo",
]
