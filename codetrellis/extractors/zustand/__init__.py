"""
CodeTrellis Zustand Extractors Module v1.0

Provides comprehensive extractors for Zustand state management constructs:

Store Extractor:
- ZustandStoreExtractor: create(), createStore() (vanilla), createWithEqualityFn(),
                          store definitions with state/actions, middleware chains,
                          TypeScript generics, slice patterns, context-based stores,
                          factory patterns, version detection (v1-v5)

Selector Extractor:
- ZustandSelectorExtractor: Named selectors (selectX = state => state.x),
                             inline selectors (useStore(s => s.x)), shallow equality,
                             useShallow (v5), destructured usage, auto selectors,
                             subscription selectors, multi-field selectors

Middleware Extractor:
- ZustandMiddlewareExtractor: persist (storage, partialize, version, migrate),
                               devtools (name, enabled, serialize), subscribeWithSelector,
                               immer, combine, redux, custom middleware,
                               third-party (zundo/temporal, broadcast, computed)

Action Extractor:
- ZustandActionExtractor: set()/get() patterns, async actions, imperative API
                           (getState/setState/subscribe/destroy/getInitialState),
                           temporal actions (undo/redo/clear from zundo),
                           subscription management

API Extractor:
- ZustandApiExtractor: Import patterns (zustand, zustand/middleware, zustand/shallow,
                        zustand/react, zustand/vanilla), TypeScript types
                        (StateCreator, StoreApi, UseBoundStore, ExtractState),
                        integrations (React Query, React Hook Form, Next.js, SSR),
                        testing patterns, deprecated API detection, migration patterns

Part of CodeTrellis v4.48 - Zustand Framework Support
"""

from .store_extractor import (
    ZustandStoreExtractor,
    ZustandStoreInfo,
    ZustandSliceInfo,
    ZustandContextStoreInfo,
)
from .selector_extractor import (
    ZustandSelectorExtractor,
    ZustandSelectorInfo,
    ZustandHookUsageInfo,
)
from .middleware_extractor import (
    ZustandMiddlewareExtractor,
    ZustandPersistInfo,
    ZustandDevtoolsInfo,
    ZustandCustomMiddlewareInfo,
)
from .action_extractor import (
    ZustandActionExtractor,
    ZustandActionInfo,
    ZustandSubscriptionInfo,
    ZustandImperativeInfo,
)
from .api_extractor import (
    ZustandApiExtractor,
    ZustandImportInfo,
    ZustandIntegrationInfo,
    ZustandTypeInfo,
)

__all__ = [
    # Store
    "ZustandStoreExtractor",
    "ZustandStoreInfo",
    "ZustandSliceInfo",
    "ZustandContextStoreInfo",
    # Selector
    "ZustandSelectorExtractor",
    "ZustandSelectorInfo",
    "ZustandHookUsageInfo",
    # Middleware
    "ZustandMiddlewareExtractor",
    "ZustandPersistInfo",
    "ZustandDevtoolsInfo",
    "ZustandCustomMiddlewareInfo",
    # Action
    "ZustandActionExtractor",
    "ZustandActionInfo",
    "ZustandSubscriptionInfo",
    "ZustandImperativeInfo",
    # API
    "ZustandApiExtractor",
    "ZustandImportInfo",
    "ZustandIntegrationInfo",
    "ZustandTypeInfo",
]
