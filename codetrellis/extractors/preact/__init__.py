"""
CodeTrellis Preact Extractors Module v1.0

Provides comprehensive extractors for Preact framework constructs:

Component Extractor:
- PreactComponentExtractor: Functional components, class components (Component/PureComponent),
                             forwardRef, memo, lazy, Fragment, createContext,
                             h() / createElement, JSX, Preact/compat compatibility

Hook Extractor:
- PreactHookExtractor: Built-in hooks from preact/hooks (useState, useEffect, useContext,
                        useReducer, useRef, useMemo, useCallback, useLayoutEffect,
                        useImperativeHandle, useDebugValue, useErrorBoundary, useId),
                        custom hooks (use* convention), hook dependency analysis

Signal Extractor:
- PreactSignalExtractor: @preact/signals (signal(), computed(), effect(), batch()),
                          @preact/signals-core (low-level signal APIs),
                          Signal<T> / ReadonlySignal<T> TypeScript types,
                          .value access patterns, signal-based state management

Context Extractor:
- PreactContextExtractor: createContext(), Provider/Consumer, useContext(),
                           contextType class pattern, nested providers

API Extractor:
- PreactApiExtractor: Import patterns (preact, preact/hooks, preact/compat,
                       @preact/signals, @preact/signals-core, preact-router,
                       preact-render-to-string, preact-iso, htm),
                       ecosystem integrations (Fresh/Deno, WMR, Preact CLI,
                       Astro, Vite), TypeScript types, SSR/hydration patterns

Supports:
- Preact 8.x (classic API: h, Component, linked state, preact-compat)
- Preact X / 10.x (hooks via preact/hooks, createContext, Fragment, compat)
- Preact 10.5+ (useId, useErrorBoundary)
- Preact 10.11+ (signals support via @preact/signals)
- Preact 10.19+ (improved signals integration)
- @preact/signals v1.x-v2.x (signal/computed/effect/batch/untracked)
- @preact/signals-core v1.x (low-level signal primitives)

Part of CodeTrellis v4.64 - Preact Framework Support
"""

from .component_extractor import (
    PreactComponentExtractor,
    PreactComponentInfo,
    PreactClassComponentInfo,
    PreactMemoInfo,
    PreactLazyInfo,
    PreactForwardRefInfo,
    PreactErrorBoundaryInfo,
)
from .hook_extractor import (
    PreactHookExtractor,
    PreactHookUsageInfo,
    PreactCustomHookInfo,
    PreactHookDependencyInfo,
)
from .signal_extractor import (
    PreactSignalExtractor,
    PreactSignalInfo,
    PreactComputedInfo,
    PreactEffectInfo,
    PreactBatchInfo,
)
from .context_extractor import (
    PreactContextExtractor,
    PreactContextInfo,
    PreactContextConsumerInfo,
)
from .api_extractor import (
    PreactApiExtractor,
    PreactImportInfo,
    PreactIntegrationInfo,
    PreactTypeInfo,
    PreactSSRInfo,
)

__all__ = [
    # Component
    "PreactComponentExtractor",
    "PreactComponentInfo",
    "PreactClassComponentInfo",
    "PreactMemoInfo",
    "PreactLazyInfo",
    "PreactForwardRefInfo",
    "PreactErrorBoundaryInfo",
    # Hook
    "PreactHookExtractor",
    "PreactHookUsageInfo",
    "PreactCustomHookInfo",
    "PreactHookDependencyInfo",
    # Signal
    "PreactSignalExtractor",
    "PreactSignalInfo",
    "PreactComputedInfo",
    "PreactEffectInfo",
    "PreactBatchInfo",
    # Context
    "PreactContextExtractor",
    "PreactContextInfo",
    "PreactContextConsumerInfo",
    # API
    "PreactApiExtractor",
    "PreactImportInfo",
    "PreactIntegrationInfo",
    "PreactTypeInfo",
    "PreactSSRInfo",
]
