"""
CodeTrellis SWR Extractors Module v1.0

Provides comprehensive extractors for SWR (Vercel) data fetching constructs:

Hook Extractor:
- SWRHookExtractor: useSWR(), useSWRImmutable(), useSWRInfinite(),
                     useSWRSubscription(), configuration options (revalidateOnFocus,
                     refreshInterval, suspense, fallbackData, keepPreviousData),
                     conditional/dependent fetching, TypeScript generics

Cache Extractor:
- SWRCacheExtractor: SWRConfig provider, global fetcher, cache provider (Map/localStorage),
                      global and bound mutate(), preload() (v2+), useSWRConfig(),
                      fallback data patterns

Mutation Extractor:
- SWRMutationExtractor: useSWRMutation() (v2+), optimistic updates (optimisticData,
                          rollbackOnError, populateCache), bound mutate with data

Middleware Extractor:
- SWRMiddlewareExtractor: Custom middleware definitions, use option,
                           built-in middleware (serialize), logger patterns

API Extractor:
- SWRApiExtractor: Import patterns (swr, swr/infinite, swr/mutation, swr/subscription,
                    swr/immutable, swr/_internal), TypeScript types (SWRResponse,
                    SWRConfiguration, Key, Fetcher, Middleware, Cache), HTTP client
                    integrations (fetch, axios, ky, got), Next.js SSR integration,
                    React Native, testing patterns, version detection (v0.x, v1.x, v2.x)

Part of CodeTrellis v4.58 - SWR Framework Support
"""

from .hook_extractor import (
    SWRHookExtractor,
    SWRHookInfo,
    SWRInfiniteInfo,
    SWRSubscriptionInfo,
)
from .mutation_extractor import (
    SWRMutationExtractor,
    SWRMutationHookInfo,
    SWROptimisticUpdateInfo,
)
from .cache_extractor import (
    SWRCacheExtractor,
    SWRConfigInfo,
    SWRMutateInfo,
    SWRPreloadInfo,
)
from .middleware_extractor import (
    SWRMiddlewareExtractor,
    SWRMiddlewareInfo,
)
from .api_extractor import (
    SWRApiExtractor,
    SWRImportInfo,
    SWRIntegrationInfo,
    SWRTypeInfo,
)

__all__ = [
    # Hook
    "SWRHookExtractor",
    "SWRHookInfo",
    "SWRInfiniteInfo",
    "SWRSubscriptionInfo",
    # Mutation
    "SWRMutationExtractor",
    "SWRMutationHookInfo",
    "SWROptimisticUpdateInfo",
    # Cache
    "SWRCacheExtractor",
    "SWRConfigInfo",
    "SWRMutateInfo",
    "SWRPreloadInfo",
    # Middleware
    "SWRMiddlewareExtractor",
    "SWRMiddlewareInfo",
    # API
    "SWRApiExtractor",
    "SWRImportInfo",
    "SWRIntegrationInfo",
    "SWRTypeInfo",
]
