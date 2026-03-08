"""
CodeTrellis TanStack Query Extractors Module v1.0

Provides comprehensive extractors for TanStack Query (React Query) data fetching constructs:

Query Extractor:
- TanStackQueryExtractor: useQuery(), useSuspenseQuery(), useQueries(),
                           useInfiniteQuery(), useSuspenseInfiniteQuery(),
                           queryOptions(), infiniteQueryOptions(),
                           query key factories, enabled/select/placeholderData,
                           TypeScript generics, staleTime/gcTime configuration

Mutation Extractor:
- TanStackMutationExtractor: useMutation(), mutation callbacks (onSuccess/onError/
                              onSettled/onMutate), optimistic updates, invalidation
                              on success, retry config, TypeScript generics

Cache Extractor:
- TanStackCacheExtractor: QueryClient configuration, QueryClientProvider,
                           defaultOptions (queries/mutations), cache invalidation
                           (invalidateQueries/refetchQueries/resetQueries/removeQueries),
                           prefetchQuery, setQueryData, getQueryData,
                           cache persistence (persistQueryClient/createSyncStoragePersister)

Prefetch Extractor:
- TanStackPrefetchExtractor: prefetchQuery/prefetchInfiniteQuery, SSR hydration
                              (dehydrate/hydrate/HydrationBoundary), Next.js integration
                              (getServerSideProps/getStaticProps/RSC), Remix/loader,
                              initialData patterns, placeholder patterns

API Extractor:
- TanStackApiExtractor: Import patterns (@tanstack/react-query, @tanstack/vue-query,
                          @tanstack/svelte-query, @tanstack/solid-query,
                          @tanstack/angular-query-experimental, react-query legacy),
                          TypeScript types (UseQueryResult, UseMutationResult, QueryKey,
                          QueryFunction, QueryOptions), devtools (@tanstack/react-query-devtools),
                          integrations (axios, ky, fetch, tRPC, GraphQL, MSW),
                          version detection (v3, v4, v5)

Part of CodeTrellis v4.57 - TanStack Query Framework Support
"""

from .query_extractor import (
    TanStackQueryExtractor,
    TanStackQueryInfo,
    TanStackInfiniteQueryInfo,
    TanStackQueriesInfo,
)
from .mutation_extractor import (
    TanStackMutationExtractor,
    TanStackMutationInfo,
)
from .cache_extractor import (
    TanStackCacheExtractor,
    TanStackQueryClientInfo,
    TanStackCacheOperationInfo,
)
from .prefetch_extractor import (
    TanStackPrefetchExtractor,
    TanStackPrefetchInfo,
    TanStackHydrationInfo,
)
from .api_extractor import (
    TanStackApiExtractor,
    TanStackImportInfo,
    TanStackIntegrationInfo,
    TanStackTypeInfo,
)

__all__ = [
    # Query
    "TanStackQueryExtractor",
    "TanStackQueryInfo",
    "TanStackInfiniteQueryInfo",
    "TanStackQueriesInfo",
    # Mutation
    "TanStackMutationExtractor",
    "TanStackMutationInfo",
    # Cache
    "TanStackCacheExtractor",
    "TanStackQueryClientInfo",
    "TanStackCacheOperationInfo",
    # Prefetch
    "TanStackPrefetchExtractor",
    "TanStackPrefetchInfo",
    "TanStackHydrationInfo",
    # API
    "TanStackApiExtractor",
    "TanStackImportInfo",
    "TanStackIntegrationInfo",
    "TanStackTypeInfo",
]
