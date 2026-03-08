"""
CodeTrellis Qwik Extractors Module v1.0

Provides comprehensive extractors for Qwik framework constructs:

Component Extractor:
- QwikComponentExtractor: component$(), inline components, <Slot>,
                          polymorphic components, PropsOf<>, QRL,
                          TypeScript Component generics

Signal Extractor:
- QwikSignalExtractor: useSignal(), useStore(), useComputed$(),
                        noSerialize(), Signal<T>, ReadonlySignal<T>,
                        deep vs shallow stores, QRL-based methods

Task Extractor:
- QwikTaskExtractor: useTask$(), useVisibleTask$(), useResource$(),
                      <Resource />, track(), cleanup(),
                      server-side vs client-side tasks

Route Extractor:
- QwikRouteExtractor: routeLoader$(), routeAction$(), server$(),
                       Form, zod() validation, file-based routing,
                       layout.tsx, index.tsx, [params], [...catchall],
                       middleware (onRequest/onGet/onPost)

Store Extractor:
- QwikStoreExtractor: useStore() deep/shallow reactivity, useSignal() patterns,
                       createContextId(), useContextProvider(), useContext(),
                       noSerialize(), QRL methods on stores

API Extractor:
- QwikApiExtractor: Import patterns (@builder.io/qwik, @builder.io/qwik-city,
                     @qwik.dev/core, @qwik.dev/router),
                     event handlers (onClick$, onInput$, useOn, useOnWindow, useOnDocument),
                     styles (useStyles$, useStylesScoped$),
                     SSR patterns, testing, ecosystem integrations

Supports:
- Qwik v0.x (early API: component$, useStore, useClientEffect$)
- Qwik v1.x (stable: useSignal, useTask$, useVisibleTask$, useComputed$, Qwik City)
- Qwik v2.x (@qwik.dev/core, @qwik.dev/router, signal improvements)

Part of CodeTrellis v4.63 - Qwik Framework Support
"""

from .component_extractor import (
    QwikComponentExtractor,
    QwikComponentInfo,
    QwikSlotInfo,
)
from .signal_extractor import (
    QwikSignalExtractor,
    QwikSignalInfo,
    QwikStoreInfo,
    QwikComputedInfo,
)
from .task_extractor import (
    QwikTaskExtractor,
    QwikTaskInfo,
    QwikResourceInfo,
)
from .route_extractor import (
    QwikRouteExtractor,
    QwikRouteLoaderInfo,
    QwikRouteActionInfo,
    QwikMiddlewareInfo,
)
from .store_extractor import (
    QwikStoreExtractor,
    QwikContextInfo,
    QwikNoSerializeInfo,
)
from .api_extractor import (
    QwikApiExtractor,
    QwikImportInfo,
    QwikEventHandlerInfo,
    QwikStyleInfo,
    QwikIntegrationInfo,
    QwikTypeInfo,
)

__all__ = [
    # Component
    "QwikComponentExtractor",
    "QwikComponentInfo",
    "QwikSlotInfo",
    # Signal
    "QwikSignalExtractor",
    "QwikSignalInfo",
    "QwikStoreInfo",
    "QwikComputedInfo",
    # Task
    "QwikTaskExtractor",
    "QwikTaskInfo",
    "QwikResourceInfo",
    # Route
    "QwikRouteExtractor",
    "QwikRouteLoaderInfo",
    "QwikRouteActionInfo",
    "QwikMiddlewareInfo",
    # Store / Context
    "QwikStoreExtractor",
    "QwikContextInfo",
    "QwikNoSerializeInfo",
    # API
    "QwikApiExtractor",
    "QwikImportInfo",
    "QwikEventHandlerInfo",
    "QwikStyleInfo",
    "QwikIntegrationInfo",
    "QwikTypeInfo",
]
