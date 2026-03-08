"""
CodeTrellis Pinia Extractors Module v1.0

Provides comprehensive extractors for Pinia state management constructs:

Store Extractor:
- PiniaStoreExtractor: defineStore() with Options API and Setup (Composition) API,
                        store IDs, state/getters/actions, storeToRefs, $patch, $reset,
                        $subscribe, $onAction, acceptHMR, plugin support,
                        TypeScript generic stores, version detection (v0.x-v3.x)

Getter Extractor:
- PiniaGetterExtractor: Computed getters (Options API), derived refs (Setup API),
                         getter arguments, cross-store getters, cached getters,
                         storeToRefs destructuring

Action Extractor:
- PiniaActionExtractor: Options API actions, Setup API functions, async actions,
                         $patch (object/function), $reset, $subscribe, $onAction,
                         cross-store actions, optimistic updates, error handling

Plugin Extractor:
- PiniaPluginExtractor: createPinia(), plugin registration (pinia.use()),
                         pinia-plugin-persistedstate, pinia-plugin-debounce,
                         pinia-orm, custom plugins, store augmentation,
                         context properties (store, app, pinia, options)

API Extractor:
- PiniaApiExtractor: Import patterns (pinia, @pinia/nuxt, pinia-plugin-persistedstate),
                      TypeScript types (StoreDefinition, Store, StateTree,
                      PiniaPluginContext, DefineStoreOptions, _GettersTree,
                      _ActionsTree, StoreGeneric), integrations (Nuxt, Vue DevTools,
                      testing with createTestingPinia, @pinia/testing)

Part of CodeTrellis v4.52 - Pinia State Management Framework Support
"""

from .store_extractor import (
    PiniaStoreExtractor,
    PiniaStoreInfo,
)
from .getter_extractor import (
    PiniaGetterExtractor,
    PiniaGetterInfo,
    PiniaStoreToRefsInfo,
)
from .action_extractor import (
    PiniaActionExtractor,
    PiniaActionInfo,
    PiniaPatchInfo,
    PiniaSubscriptionInfo,
)
from .plugin_extractor import (
    PiniaPluginExtractor,
    PiniaPluginInfo,
    PiniaInstanceInfo,
)
from .api_extractor import (
    PiniaApiExtractor,
    PiniaImportInfo,
    PiniaIntegrationInfo,
    PiniaTypeInfo,
)

__all__ = [
    # Store
    "PiniaStoreExtractor",
    "PiniaStoreInfo",
    # Getter
    "PiniaGetterExtractor",
    "PiniaGetterInfo",
    "PiniaStoreToRefsInfo",
    # Action
    "PiniaActionExtractor",
    "PiniaActionInfo",
    "PiniaPatchInfo",
    "PiniaSubscriptionInfo",
    # Plugin
    "PiniaPluginExtractor",
    "PiniaPluginInfo",
    "PiniaInstanceInfo",
    # API
    "PiniaApiExtractor",
    "PiniaImportInfo",
    "PiniaIntegrationInfo",
    "PiniaTypeInfo",
]
