"""
EnhancedTanStackQueryParser v1.0 - Comprehensive TanStack Query parser using all extractors.

This parser integrates all TanStack Query extractors to provide complete parsing of
TanStack Query (React Query) data fetching usage across React/TypeScript/JavaScript
and multi-framework (Vue, Svelte, Solid, Angular) source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting TanStack Query-specific semantics.

Supports:
- react-query v1.x (legacy QueryCache-based API, string query keys)
- react-query v2.x (useQuery/useMutation stabilized, ReactQueryConfigProvider)
- react-query v3.x (QueryClient, query keys as arrays, Hydrate SSR,
                      useQueries, onSuccess/onError/onSettled on useQuery)
- @tanstack/react-query v4.x (scoped @tanstack package, cacheTime, keepPreviousData,
                                useErrorBoundary, React 18 support, Hydrate component)
- @tanstack/react-query v5.x (gcTime replaces cacheTime, placeholderData replaces
                                keepPreviousData, throwOnError replaces useErrorBoundary,
                                queryOptions() helper, useSuspenseQuery, HydrationBoundary
                                replaces Hydrate, initialPageParam required for infinite,
                                TypeScript-first with improved generic inference,
                                removed onSuccess/onError/onSettled from useQuery)

Multi-Framework Adapters:
- @tanstack/react-query (React 16.8+, 17, 18, 19)
- @tanstack/vue-query (Vue 3.x with Composition API)
- @tanstack/svelte-query (Svelte 3/4/5, SvelteKit)
- @tanstack/solid-query (SolidJS)
- @tanstack/angular-query-experimental (Angular 16+, signal-based)

Query Patterns:
- useQuery / useSuspenseQuery (data fetching)
- useInfiniteQuery / useSuspenseInfiniteQuery (pagination)
- useQueries (parallel queries, combine v5)
- queryOptions / infiniteQueryOptions (v5 type-safe helpers)
- Query key factories (structured key management)

Mutation Patterns:
- useMutation (data modification)
- Optimistic updates (onMutate + setQueryData + rollback)
- Cache invalidation (invalidateQueries in callbacks)
- Mutation callbacks (onSuccess, onError, onSettled, onMutate)

Cache Management:
- QueryClient configuration (defaultOptions, staleTime, gcTime)
- QueryClientProvider
- Cache operations (invalidateQueries, refetchQueries, setQueryData, etc.)
- ensureQueryData (v5)
- Custom QueryCache / MutationCache with global error handlers

SSR / Prefetching:
- dehydrate / hydrate / HydrationBoundary (v5) / Hydrate (v4)
- prefetchQuery / prefetchInfiniteQuery
- Next.js integration (getServerSideProps, getStaticProps, RSC)
- Remix loader integration
- ensureQueryData for RSC

Ecosystem Detection (30+ patterns):
- Core: @tanstack/react-query, @tanstack/vue-query, @tanstack/svelte-query,
         @tanstack/solid-query, @tanstack/angular-query-experimental
- DevTools: @tanstack/react-query-devtools
- Persistence: @tanstack/query-persist-client-core,
               @tanstack/query-sync-storage-persister,
               @tanstack/query-async-storage-persister
- HTTP Clients: axios, ky, fetch, got, ofetch, superagent
- tRPC: @trpc/client, @trpc/react-query, @trpc/next
- GraphQL: graphql-request, @graphql-codegen, urql
- Testing: @testing-library/react, msw, vitest, jest
- Legacy: react-query (v1-v3)

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.57 - TanStack Query Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all TanStack Query extractors
from .extractors.tanstack_query import (
    TanStackQueryExtractor, TanStackQueryInfo, TanStackInfiniteQueryInfo, TanStackQueriesInfo,
    TanStackMutationExtractor, TanStackMutationInfo,
    TanStackCacheExtractor, TanStackQueryClientInfo, TanStackCacheOperationInfo,
    TanStackPrefetchExtractor, TanStackPrefetchInfo, TanStackHydrationInfo,
    TanStackApiExtractor, TanStackImportInfo, TanStackIntegrationInfo, TanStackTypeInfo,
)


@dataclass
class TanStackQueryParseResult:
    """Complete parse result for a file with TanStack Query usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, ts, js, vue, svelte

    # Queries
    queries: List[TanStackQueryInfo] = field(default_factory=list)
    infinite_queries: List[TanStackInfiniteQueryInfo] = field(default_factory=list)
    parallel_queries: List[TanStackQueriesInfo] = field(default_factory=list)
    query_options: List[Dict] = field(default_factory=list)
    query_key_factories: List[Dict] = field(default_factory=list)

    # Mutations
    mutations: List[TanStackMutationInfo] = field(default_factory=list)

    # Cache
    query_clients: List[TanStackQueryClientInfo] = field(default_factory=list)
    cache_operations: List[TanStackCacheOperationInfo] = field(default_factory=list)
    providers: List[Dict] = field(default_factory=list)
    query_client_hooks: List[Dict] = field(default_factory=list)

    # Prefetch / SSR
    prefetches: List[TanStackPrefetchInfo] = field(default_factory=list)
    hydrations: List[TanStackHydrationInfo] = field(default_factory=list)

    # API
    imports: List[TanStackImportInfo] = field(default_factory=list)
    integrations: List[TanStackIntegrationInfo] = field(default_factory=list)
    types: List[TanStackTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    tanstack_query_version: str = ""  # v3, v4, v5 (or legacy for v1/v2)


class EnhancedTanStackQueryParser:
    """
    Enhanced TanStack Query parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript/React parser
    when TanStack Query framework is detected. It extracts TanStack Query-specific
    semantics that the language parsers cannot capture.

    Framework detection supports 30+ TanStack Query ecosystem libraries across:
    - Core (@tanstack/react-query, @tanstack/vue-query, etc.)
    - DevTools (@tanstack/react-query-devtools)
    - Persistence (@tanstack/query-persist-client-core)
    - HTTP Clients (axios, ky, fetch, got)
    - tRPC (@trpc/client, @trpc/react-query)
    - GraphQL (graphql-request, @graphql-codegen)
    - Testing (@testing-library/react, msw, vitest, jest)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # ── Framework Detection Patterns ──────────────────────────────

    FRAMEWORK_PATTERNS = {
        # ── Core Adapters ─────────────────────────────────────────
        'tanstack-react-query': re.compile(
            r"from\s+['\"]@tanstack/react-query['\"]|"
            r"require\(['\"]@tanstack/react-query['\"]\)",
            re.MULTILINE
        ),
        'tanstack-vue-query': re.compile(
            r"from\s+['\"]@tanstack/vue-query['\"]|"
            r"require\(['\"]@tanstack/vue-query['\"]\)",
            re.MULTILINE
        ),
        'tanstack-svelte-query': re.compile(
            r"from\s+['\"]@tanstack/svelte-query['\"]|"
            r"require\(['\"]@tanstack/svelte-query['\"]\)",
            re.MULTILINE
        ),
        'tanstack-solid-query': re.compile(
            r"from\s+['\"]@tanstack/solid-query['\"]|"
            r"require\(['\"]@tanstack/solid-query['\"]\)",
            re.MULTILINE
        ),
        'tanstack-angular-query': re.compile(
            r"from\s+['\"]@tanstack/angular-query-experimental['\"]",
            re.MULTILINE
        ),

        # ── Legacy ────────────────────────────────────────────────
        'react-query-legacy': re.compile(
            r"from\s+['\"]react-query['\"]|require\(['\"]react-query['\"]\)",
            re.MULTILINE
        ),
        'react-query-devtools-legacy': re.compile(
            r"from\s+['\"]react-query/devtools['\"]",
            re.MULTILINE
        ),

        # ── DevTools ──────────────────────────────────────────────
        'tanstack-devtools': re.compile(
            r"from\s+['\"]@tanstack/react-query-devtools['\"]|"
            r"<ReactQueryDevtools\b",
            re.MULTILINE
        ),

        # ── Persistence ──────────────────────────────────────────
        'tanstack-persist': re.compile(
            r"from\s+['\"]@tanstack/(?:react-query-persist-client|"
            r"query-persist-client-core|query-sync-storage-persister|"
            r"query-async-storage-persister)['\"]",
            re.MULTILINE
        ),

        # ── tRPC ──────────────────────────────────────────────────
        'trpc': re.compile(
            r"from\s+['\"]@trpc/(?:client|react-query|react|next|server)['\"]",
            re.MULTILINE
        ),

        # ── HTTP Clients ──────────────────────────────────────────
        'axios': re.compile(
            r"from\s+['\"]axios['\"]|require\(['\"]axios['\"]\)",
            re.MULTILINE
        ),
        'ky': re.compile(
            r"from\s+['\"]ky['\"]",
            re.MULTILINE
        ),
        'graphql-request': re.compile(
            r"from\s+['\"]graphql-request['\"]",
            re.MULTILINE
        ),

        # ── Ecosystem ────────────────────────────────────────────
        'react': re.compile(
            r"from\s+['\"]react['\"]|require\(['\"]react['\"]\)",
            re.MULTILINE
        ),
        'next': re.compile(
            r"from\s+['\"]next[/'\"]|require\(['\"]next['\"]\)",
            re.MULTILINE
        ),
        'msw': re.compile(
            r"from\s+['\"]msw['\"]|from\s+['\"]@mswjs/data['\"]",
            re.MULTILINE
        ),
    }

    # ── Feature Detection Patterns ────────────────────────────────

    FEATURE_PATTERNS = {
        'use_query': re.compile(r'useQuery\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_suspense_query': re.compile(r'useSuspenseQuery\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_infinite_query': re.compile(r'useInfiniteQuery\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_suspense_infinite_query': re.compile(r'useSuspenseInfiniteQuery\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_queries': re.compile(r'useQueries\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_mutation': re.compile(r'useMutation\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_query_client': re.compile(r'useQueryClient\s*\(', re.MULTILINE),
        'use_is_fetching': re.compile(r'useIsFetching\s*\(', re.MULTILINE),
        'use_is_mutating': re.compile(r'useIsMutating\s*\(', re.MULTILINE),
        'query_client': re.compile(r'new\s+QueryClient\s*\(', re.MULTILINE),
        'query_client_provider': re.compile(r'<QueryClientProvider\b', re.MULTILINE),
        'query_options': re.compile(r'queryOptions\s*\(', re.MULTILINE),
        'infinite_query_options': re.compile(r'infiniteQueryOptions\s*\(', re.MULTILINE),
        'invalidate_queries': re.compile(r'\.invalidateQueries\s*\(', re.MULTILINE),
        'set_query_data': re.compile(r'\.setQueryData\s*\(', re.MULTILINE),
        'get_query_data': re.compile(r'\.getQueryData\s*\(', re.MULTILINE),
        'prefetch_query': re.compile(r'\.prefetchQuery\s*\(', re.MULTILINE),
        'ensure_query_data': re.compile(r'\.ensureQueryData\s*\(', re.MULTILINE),
        'dehydrate': re.compile(r'dehydrate\s*\(', re.MULTILINE),
        'hydration_boundary': re.compile(r'<HydrationBoundary\b', re.MULTILINE),
        'hydrate_component': re.compile(r'<Hydrate\b', re.MULTILINE),
        'gc_time': re.compile(r'\bgcTime\s*:', re.MULTILINE),
        'cache_time': re.compile(r'\bcacheTime\s*:', re.MULTILINE),
        'stale_time': re.compile(r'\bstaleTime\s*:', re.MULTILINE),
        'placeholder_data': re.compile(r'\bplaceholderData\s*:', re.MULTILINE),
        'keep_previous_data': re.compile(r'\bkeepPreviousData\b', re.MULTILINE),
        'throw_on_error': re.compile(r'\bthrowOnError\s*:', re.MULTILINE),
        'use_error_boundary': re.compile(r'\buseErrorBoundary\s*:', re.MULTILINE),
        'initial_page_param': re.compile(r'\binitialPageParam\s*:', re.MULTILINE),
        'optimistic_update': re.compile(r'onMutate\s*:.*setQueryData', re.DOTALL),
        'suspense_config': re.compile(r'\bsuspense\s*:\s*true', re.MULTILINE),
        'persist_query_client': re.compile(r'persistQueryClient\s*\(', re.MULTILINE),
        'query_key_factory': re.compile(
            r'(?:const|let|var)\s+\w+(?:Keys?|QueryKeys?|queries)\s*=\s*\{', re.MULTILINE
        ),
    }

    def __init__(self):
        """Initialize all TanStack Query extractors."""
        self.query_extractor = TanStackQueryExtractor()
        self.mutation_extractor = TanStackMutationExtractor()
        self.cache_extractor = TanStackCacheExtractor()
        self.prefetch_extractor = TanStackPrefetchExtractor()
        self.api_extractor = TanStackApiExtractor()

    def is_tanstack_query_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains TanStack Query code.

        Returns True if the file imports from TanStack Query ecosystem
        or uses TanStack Query patterns (useQuery, useMutation, etc.)
        """
        tanstack_indicators = [
            '@tanstack/react-query', '@tanstack/vue-query',
            '@tanstack/svelte-query', '@tanstack/solid-query',
            '@tanstack/angular-query', 'react-query',
            'useQuery(', 'useMutation(', 'useInfiniteQuery(',
            'useSuspenseQuery(', 'QueryClient(',
            'QueryClientProvider', 'queryOptions(',
            'useQueryClient(', 'useQueries(',
            '@tanstack/react-query-devtools',
            'prefetchQuery(', 'dehydrate(',
            'HydrationBoundary', 'invalidateQueries(',
        ]
        return any(ind in content for ind in tanstack_indicators)

    def parse(self, content: str, file_path: str = "") -> TanStackQueryParseResult:
        """
        Parse a source file for TanStack Query patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            TanStackQueryParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"
        elif file_path.endswith('.vue'):
            file_type = "vue"
        elif file_path.endswith('.svelte'):
            file_type = "svelte"

        result = TanStackQueryParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.tanstack_query_version = self._detect_version(content)

        # ── Query extraction ──────────────────────────────────────
        try:
            query_result = self.query_extractor.extract(content, file_path)
            result.queries = query_result.get('queries', [])
            result.infinite_queries = query_result.get('infinite_queries', [])
            result.parallel_queries = query_result.get('parallel_queries', [])
            result.query_options = query_result.get('query_options', [])
            result.query_key_factories = query_result.get('query_key_factories', [])
        except Exception:
            pass

        # ── Mutation extraction ───────────────────────────────────
        try:
            mut_result = self.mutation_extractor.extract(content, file_path)
            result.mutations = mut_result.get('mutations', [])
        except Exception:
            pass

        # ── Cache extraction ──────────────────────────────────────
        try:
            cache_result = self.cache_extractor.extract(content, file_path)
            result.query_clients = cache_result.get('query_clients', [])
            result.cache_operations = cache_result.get('cache_operations', [])
            result.providers = cache_result.get('providers', [])
            result.query_client_hooks = cache_result.get('query_client_hooks', [])
        except Exception:
            pass

        # ── Prefetch / SSR extraction ─────────────────────────────
        try:
            pf_result = self.prefetch_extractor.extract(content, file_path)
            result.prefetches = pf_result.get('prefetches', [])
            result.hydrations = pf_result.get('hydrations', [])
        except Exception:
            pass

        # ── API extraction ────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.integrations = api_result.get('integrations', [])
            result.types = api_result.get('types', [])
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which TanStack Query ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which TanStack Query features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect TanStack Query version based on API usage patterns.

        Returns:
            - 'v5' if @tanstack/react-query v5 patterns detected
            - 'v4' if @tanstack/react-query v4 patterns detected
            - 'v3' if react-query v3 patterns detected
            - 'legacy' if react-query v1/v2 patterns detected
            - '' if unknown
        """
        # v5 indicators (features introduced in v5)
        v5_indicators = [
            'useSuspenseQuery',         # new in v5
            'useSuspenseInfiniteQuery',  # new in v5
            'HydrationBoundary',         # replaces Hydrate in v5
            'queryOptions(',             # new helper in v5
            'infiniteQueryOptions(',     # new helper in v5
            'ensureQueryData',           # new in v5
            'throwOnError',              # replaces useErrorBoundary in v5
            'initialPageParam',          # required in v5 for infinite
            'gcTime',                    # replaces cacheTime in v5
        ]
        if any(ind in content for ind in v5_indicators):
            return "v5"

        # v4 indicators (@tanstack scoped package)
        v4_indicators = [
            '@tanstack/react-query',     # scoped package
            '@tanstack/vue-query',       # scoped package
            '@tanstack/svelte-query',    # scoped package
            '@tanstack/solid-query',     # scoped package
            'keepPreviousData',          # v4 (replaced in v5)
            'cacheTime',                 # v4 (renamed to gcTime in v5)
            'useErrorBoundary',          # v4 (renamed to throwOnError in v5)
        ]
        if any(ind in content for ind in v4_indicators):
            return "v4"

        # v3 indicators
        v3_indicators = [
            "from 'react-query'",        # non-scoped package
            'from "react-query"',        # non-scoped package
            'QueryClient',               # introduced in v3
            'useQueries',                # introduced in v3
        ]
        if any(ind in content for ind in v3_indicators):
            return "v3"

        # Legacy (v1/v2)
        legacy_indicators = [
            'ReactQueryConfigProvider',  # v1/v2
            'queryCache',                # v1/v2 direct cache usage
            'makeQueryCache',            # v1
        ]
        if any(ind in content for ind in legacy_indicators):
            return "legacy"

        # If we see useQuery/useMutation but no version specifics
        if 'useQuery' in content or 'useMutation' in content:
            return "v4"  # Most common current version

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'legacy': 1, 'v3': 3, 'v4': 4, 'v5': 5}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
