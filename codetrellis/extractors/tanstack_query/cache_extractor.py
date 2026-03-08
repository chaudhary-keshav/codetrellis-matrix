"""
TanStack Query Cache Extractor for CodeTrellis

Extracts TanStack Query cache management and QueryClient patterns:
- QueryClient instantiation and configuration
- QueryClientProvider usage
- Default options (queries: staleTime, gcTime, retry; mutations: retry)
- Cache operations: invalidateQueries, refetchQueries, resetQueries,
  removeQueries, cancelQueries
- Data operations: setQueryData, getQueryData, setQueriesData,
  getQueriesData, getQueryState
- Prefetch operations: prefetchQuery, prefetchInfiniteQuery,
  fetchQuery, fetchInfiniteQuery, ensureQueryData (v5)
- Cache persistence: persistQueryClient, createSyncStoragePersister,
  createAsyncStoragePersister
- Query cache / Mutation cache event listeners

Supports:
- react-query v3 (QueryClient with cacheTime)
- @tanstack/react-query v4 (QueryClient refined)
- @tanstack/react-query v5 (gcTime, ensureQueryData, improved types)

Part of CodeTrellis v4.57 - TanStack Query Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TanStackQueryClientInfo:
    """Information about a QueryClient instantiation."""
    name: str
    file: str = ""
    line_number: int = 0
    has_default_options: bool = False
    default_stale_time: str = ""  # e.g., "5 * 60 * 1000", "Infinity"
    default_gc_time: str = ""
    default_cache_time: str = ""  # v4 (renamed to gcTime in v5)
    default_retry: str = ""
    has_query_cache: bool = False  # Custom QueryCache
    has_mutation_cache: bool = False  # Custom MutationCache
    has_persistence: bool = False  # persistQueryClient
    persistence_type: str = ""  # sync, async
    is_exported: bool = False


@dataclass
class TanStackCacheOperationInfo:
    """Information about a cache operation."""
    operation: str  # invalidateQueries, refetchQueries, setQueryData, etc.
    file: str = ""
    line_number: int = 0
    target_key: str = ""  # Query key being targeted
    is_exact: bool = False  # { exact: true }
    client_name: str = ""  # queryClient variable name
    is_in_callback: bool = False  # Inside onSuccess/onSettled callback


class TanStackCacheExtractor:
    """
    Extracts TanStack Query cache management patterns.

    Detects:
    - QueryClient creation and configuration
    - QueryClientProvider wrapping
    - Cache invalidation and refetching
    - Data prefetching and manual cache updates
    - Cache persistence (localStorage, AsyncStorage)
    - Custom QueryCache / MutationCache with event listeners
    """

    # QueryClient instantiation
    QUERY_CLIENT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*new\s+QueryClient\s*\(',
        re.MULTILINE
    )

    # QueryClientProvider
    PROVIDER_PATTERN = re.compile(
        r'<QueryClientProvider\s+client\s*=\s*\{(\w+)\}',
        re.MULTILINE
    )

    # Cache operations
    CACHE_OP_PATTERN = re.compile(
        r'(\w+)\s*\.\s*(invalidateQueries|refetchQueries|resetQueries|'
        r'removeQueries|cancelQueries|setQueryData|getQueryData|'
        r'setQueriesData|getQueriesData|getQueryState|'
        r'prefetchQuery|prefetchInfiniteQuery|fetchQuery|'
        r'fetchInfiniteQuery|ensureQueryData|ensureInfiniteQueryData)\s*\(',
        re.MULTILINE
    )

    # useQueryClient hook
    USE_QUERY_CLIENT_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*useQueryClient\s*\(\s*\)',
        re.MULTILINE
    )

    # Persistence patterns
    PERSIST_PATTERN = re.compile(
        r'(?:persistQueryClient|createSyncStoragePersister|createAsyncStoragePersister)\s*\(',
        re.MULTILINE
    )

    # Custom QueryCache / MutationCache
    CUSTOM_CACHE_PATTERN = re.compile(
        r'new\s+(QueryCache|MutationCache)\s*\(',
        re.MULTILINE
    )

    # defaultOptions pattern
    DEFAULT_OPTIONS_PATTERN = re.compile(
        r'defaultOptions\s*:\s*\{',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all TanStack Query cache patterns from source code."""
        result: Dict[str, Any] = {
            'query_clients': [],
            'cache_operations': [],
            'providers': [],
            'query_client_hooks': [],
        }

        # Extract QueryClient instantiations
        for match in self.QUERY_CLIENT_PATTERN.finditer(content):
            client_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            # Check for export in both the match itself and the preceding text
            matched_text = match.group(0)
            preceding = content[max(0, match.start() - 20):match.start()]
            is_exported = 'export' in matched_text or 'export' in preceding

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 1000)
            context = content[ctx_start:ctx_end]

            client = TanStackQueryClientInfo(
                name=client_name,
                file=file_path,
                line_number=line_num,
                is_exported=is_exported,
            )

            # Check default options
            if self.DEFAULT_OPTIONS_PATTERN.search(context):
                client.has_default_options = True

                # Extract specific defaults
                stale_match = re.search(r'staleTime\s*:\s*([^,}\n]+)', context)
                if stale_match:
                    client.default_stale_time = stale_match.group(1).strip()

                gc_match = re.search(r'gcTime\s*:\s*([^,}\n]+)', context)
                if gc_match:
                    client.default_gc_time = gc_match.group(1).strip()

                cache_match = re.search(r'cacheTime\s*:\s*([^,}\n]+)', context)
                if cache_match:
                    client.default_cache_time = cache_match.group(1).strip()

                retry_match = re.search(r'retry\s*:\s*([^,}\n]+)', context)
                if retry_match:
                    client.default_retry = retry_match.group(1).strip()

            # Check for custom caches
            if 'new QueryCache' in context or 'queryCache' in context:
                client.has_query_cache = True
            if 'new MutationCache' in context or 'mutationCache' in context:
                client.has_mutation_cache = True

            # Check for persistence
            if 'persist' in context.lower():
                client.has_persistence = True
                if 'createSyncStoragePersister' in content:
                    client.persistence_type = "sync"
                elif 'createAsyncStoragePersister' in content:
                    client.persistence_type = "async"

            result['query_clients'].append(client)

        # Extract cache operations
        for match in self.CACHE_OP_PATTERN.finditer(content):
            client_name = match.group(1)
            operation = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 300)
            context = content[ctx_start:ctx_end]

            # Check for target key
            target_key = ""
            key_match = re.search(r'queryKey\s*:\s*(\[[^\]]*\]|\w+)', context)
            if key_match:
                target_key = key_match.group(1).strip()
            else:
                # v3/v4 positional argument
                arg_match = re.search(r'\(\s*(\[[^\]]*\]|\w+Keys?\.\w+)', context)
                if arg_match:
                    target_key = arg_match.group(1).strip()

            is_exact = 'exact' in context and 'true' in context

            # Check if inside a callback
            line_start = content.rfind('\n', 0, match.start())
            prev_context = content[max(0, line_start - 200):match.start()]
            is_in_callback = bool(re.search(r'on(?:Success|Error|Settled|Mutate)\s*:', prev_context))

            op = TanStackCacheOperationInfo(
                operation=operation,
                file=file_path,
                line_number=line_num,
                target_key=target_key,
                is_exact=is_exact,
                client_name=client_name,
                is_in_callback=is_in_callback,
            )
            result['cache_operations'].append(op)

        # Extract QueryClientProvider
        for match in self.PROVIDER_PATTERN.finditer(content):
            client_ref = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            result['providers'].append({
                'client': client_ref,
                'file': file_path,
                'line_number': line_num,
            })

        # Extract useQueryClient hook
        for match in self.USE_QUERY_CLIENT_PATTERN.finditer(content):
            var_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            result['query_client_hooks'].append({
                'name': var_name,
                'file': file_path,
                'line_number': line_num,
            })

        return result
