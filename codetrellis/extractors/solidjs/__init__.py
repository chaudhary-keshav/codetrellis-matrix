"""
CodeTrellis Solid.js Extractors Module v1.0

Provides comprehensive extractors for Solid.js framework constructs:

Component Extractor:
- SolidComponentExtractor: Functional components, lazy components,
                            Dynamic components, control flow (Show, For,
                            Switch, Match, Index, Portal, Suspense, ErrorBoundary),
                            mergeProps/splitProps, children helper,
                            TypeScript Component/ParentComponent/FlowComponent/VoidComponent types

Signal Extractor:
- SolidSignalExtractor: createSignal, createMemo, createEffect, createComputed,
                         createRenderEffect, createReaction, on() wrapper,
                         batch(), untrack(), createRoot(), createDeferred(),
                         startTransition/useTransition, observable(), from(),
                         mapArray/indexArray

Store Extractor:
- SolidStoreExtractor: createStore, createMutable, produce, reconcile,
                        unwrap, path-based setters, nested store updates

Resource Extractor:
- SolidResourceExtractor: createResource, createAsync, server$,
                           createServerData$/createServerAction$ (SolidStart v0.x),
                           cache/action/redirect (SolidStart v1.0+),
                           createRouteData/useRouteData, route data patterns

Router Extractor:
- SolidRouterExtractor: Route definitions (declarative/config/file-based),
                         router hooks (useParams/useNavigate/useLocation/
                         useSearchParams/useMatch/useBeforeLeave),
                         route data loading, actions, navigation

API Extractor:
- SolidApiExtractor: Import patterns (solid-js, solid-js/store, solid-js/web,
                      @solidjs/router, @solidjs/testing-library, solid-start,
                      @solid-primitives/*, @tanstack/solid-query, @kobalte/core),
                      createContext/useContext, lifecycle hooks (onMount/onCleanup/onError),
                      TypeScript types (Accessor/Setter/Component/JSX.Element),
                      SSR patterns, testing, ecosystem integrations

Part of CodeTrellis v4.62 - Solid.js Framework Support
"""

from .component_extractor import (
    SolidComponentExtractor,
    SolidComponentInfo,
    SolidControlFlowInfo,
)
from .signal_extractor import (
    SolidSignalExtractor,
    SolidSignalInfo,
    SolidMemoInfo,
    SolidEffectInfo,
    SolidReactiveUtilInfo,
)
from .store_extractor import (
    SolidStoreExtractor,
    SolidStoreInfo,
    SolidStoreUpdateInfo,
)
from .resource_extractor import (
    SolidResourceExtractor,
    SolidResourceInfo,
    SolidServerFunctionInfo,
    SolidRouteDataInfo,
)
from .router_extractor import (
    SolidRouterExtractor,
    SolidRouteInfo,
    SolidRouterHookInfo,
)
from .api_extractor import (
    SolidApiExtractor,
    SolidImportInfo,
    SolidContextInfo,
    SolidLifecycleInfo,
    SolidIntegrationInfo,
    SolidTypeInfo,
)

__all__ = [
    # Component
    "SolidComponentExtractor",
    "SolidComponentInfo",
    "SolidControlFlowInfo",
    # Signal
    "SolidSignalExtractor",
    "SolidSignalInfo",
    "SolidMemoInfo",
    "SolidEffectInfo",
    "SolidReactiveUtilInfo",
    # Store
    "SolidStoreExtractor",
    "SolidStoreInfo",
    "SolidStoreUpdateInfo",
    # Resource
    "SolidResourceExtractor",
    "SolidResourceInfo",
    "SolidServerFunctionInfo",
    "SolidRouteDataInfo",
    # Router
    "SolidRouterExtractor",
    "SolidRouteInfo",
    "SolidRouterHookInfo",
    # API
    "SolidApiExtractor",
    "SolidImportInfo",
    "SolidContextInfo",
    "SolidLifecycleInfo",
    "SolidIntegrationInfo",
    "SolidTypeInfo",
]
