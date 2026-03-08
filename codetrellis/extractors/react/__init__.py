"""
CodeTrellis React Extractors Module v1.0

Provides comprehensive extractors for React framework constructs:

Component Extractors:
- ReactComponentExtractor: Functional components, class components, HOCs,
                            forwardRef, memo, lazy, Suspense, ErrorBoundary,
                            Server Components, Client Components (React 18/19)

Hook Extractors:
- ReactHookExtractor: Built-in hooks (useState, useEffect, useContext, etc.),
                       custom hooks, hook dependencies, React 18/19 hooks
                       (useTransition, useDeferredValue, useId, use, useFormStatus,
                        useOptimistic, useActionState)

Context Extractors:
- ReactContextExtractor: Context creation, Provider/Consumer trees,
                           useContext usage, context composition patterns

State Management Extractors:
- ReactStateExtractor: Redux (toolkit), Zustand, Jotai, Recoil, MobX,
                        Valtio, XState, TanStack Query, SWR stores/atoms

Routing Extractors:
- ReactRoutingExtractor: React Router v5/v6, Next.js pages/app router,
                           TanStack Router, Remix routes, file-based routing

Part of CodeTrellis v4.32 - React Language Support
"""

from .component_extractor import (
    ReactComponentExtractor,
    ReactComponentInfo,
    ReactHOCInfo,
    ReactForwardRefInfo,
    ReactMemoInfo,
    ReactLazyInfo,
    ReactErrorBoundaryInfo,
    ReactProviderInfo,
)
from .hook_extractor import (
    ReactHookExtractor,
    ReactHookUsageInfo,
    ReactCustomHookInfo,
    ReactHookDependencyInfo,
)
from .context_extractor import (
    ReactContextExtractor,
    ReactContextInfo,
    ReactContextConsumerInfo,
)
from .state_extractor import (
    ReactStateExtractor,
    ReactStoreInfo,
    ReactAtomInfo,
    ReactSliceInfo,
    ReactQueryInfo,
)
from .routing_extractor import (
    ReactRoutingExtractor,
    ReactRouteInfo,
    ReactLayoutInfo,
    ReactPageInfo,
)

__all__ = [
    # Component extractor
    "ReactComponentExtractor",
    "ReactComponentInfo",
    "ReactHOCInfo",
    "ReactForwardRefInfo",
    "ReactMemoInfo",
    "ReactLazyInfo",
    "ReactErrorBoundaryInfo",
    "ReactProviderInfo",
    # Hook extractor
    "ReactHookExtractor",
    "ReactHookUsageInfo",
    "ReactCustomHookInfo",
    "ReactHookDependencyInfo",
    # Context extractor
    "ReactContextExtractor",
    "ReactContextInfo",
    "ReactContextConsumerInfo",
    # State extractor
    "ReactStateExtractor",
    "ReactStoreInfo",
    "ReactAtomInfo",
    "ReactSliceInfo",
    "ReactQueryInfo",
    # Routing extractor
    "ReactRoutingExtractor",
    "ReactRouteInfo",
    "ReactLayoutInfo",
    "ReactPageInfo",
]
