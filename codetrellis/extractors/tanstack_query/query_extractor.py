"""
TanStack Query Query Extractor for CodeTrellis

Extracts TanStack Query (React Query) query definitions and usage patterns:
- useQuery() hook calls with query key and query function
- useSuspenseQuery() for Suspense-based queries (v5+)
- useQueries() for parallel queries
- useInfiniteQuery() for paginated/infinite data
- useSuspenseInfiniteQuery() (v5+)
- queryOptions() helper (v5+)
- infiniteQueryOptions() helper (v5+)
- Query key factories (structured key patterns)
- Query configuration: enabled, select, staleTime, gcTime, refetchInterval,
  refetchOnWindowFocus, placeholderData, initialData, retry, retryDelay,
  keepPreviousData (v4), placeholderData (v5)

Supports:
- react-query v1-v2 (legacy useQuery with inline config)
- react-query v3 (useQuery with object config, query keys as arrays)
- @tanstack/react-query v4 (keepPreviousData, cacheTime, useQueryClient)
- @tanstack/react-query v5 (gcTime replaces cacheTime, queryOptions(),
                              useSuspenseQuery, placeholderData replaces
                              keepPreviousData, throwOnError replaces useErrorBoundary)

Part of CodeTrellis v4.57 - TanStack Query Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TanStackQueryInfo:
    """Information about a TanStack Query useQuery() call."""
    name: str  # Variable name or inferred name
    file: str = ""
    line_number: int = 0
    query_key: str = ""  # Query key expression
    query_fn: str = ""  # Query function name or expression
    hook_name: str = "useQuery"  # useQuery, useSuspenseQuery
    has_enabled: bool = False
    has_select: bool = False
    has_stale_time: bool = False
    has_gc_time: bool = False
    has_cache_time: bool = False  # v4 (renamed to gcTime in v5)
    has_refetch_interval: bool = False
    has_refetch_on_window_focus: bool = False
    has_placeholder_data: bool = False
    has_initial_data: bool = False
    has_keep_previous_data: bool = False  # v4 (replaced by placeholderData in v5)
    has_retry: bool = False
    has_error_boundary: bool = False  # useErrorBoundary (v4) / throwOnError (v5)
    has_suspense: bool = False  # suspense: true (v4) / useSuspenseQuery (v5)
    has_typescript: bool = False
    type_params: str = ""  # TypeScript generic parameters
    is_exported: bool = False
    uses_query_options: bool = False  # queryOptions() helper (v5)


@dataclass
class TanStackInfiniteQueryInfo:
    """Information about a TanStack Query useInfiniteQuery() call."""
    name: str
    file: str = ""
    line_number: int = 0
    query_key: str = ""
    query_fn: str = ""
    hook_name: str = "useInfiniteQuery"  # useInfiniteQuery, useSuspenseInfiniteQuery
    has_get_next_page_param: bool = False
    has_get_previous_page_param: bool = False
    has_initial_page_param: bool = False  # v5 required
    has_max_pages: bool = False
    has_enabled: bool = False
    has_select: bool = False
    has_typescript: bool = False
    type_params: str = ""
    is_exported: bool = False


@dataclass
class TanStackQueriesInfo:
    """Information about a useQueries() parallel query call."""
    name: str
    file: str = ""
    line_number: int = 0
    query_count: int = 0  # Number of queries in the array
    has_combine: bool = False  # combine option (v5)
    has_typescript: bool = False
    is_exported: bool = False


class TanStackQueryExtractor:
    """
    Extracts TanStack Query query definitions from source code.

    Detects:
    - useQuery() calls with configuration
    - useSuspenseQuery() calls (v5+)
    - useQueries() parallel queries
    - useInfiniteQuery() paginated queries
    - useSuspenseInfiniteQuery() (v5+)
    - queryOptions() helper usage (v5+)
    - infiniteQueryOptions() helper (v5+)
    - Query key factory patterns
    - TypeScript generic annotations
    """

    # useQuery / useSuspenseQuery patterns
    USE_QUERY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\{[^}]+\}|\w+)\s*=\s*'
        r'(useQuery|useSuspenseQuery)\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # useInfiniteQuery / useSuspenseInfiniteQuery patterns
    USE_INFINITE_QUERY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\{[^}]+\}|\w+)\s*=\s*'
        r'(useInfiniteQuery|useSuspenseInfiniteQuery)\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # useQueries pattern
    USE_QUERIES_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useQueries\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # queryOptions / infiniteQueryOptions (v5 helper)
    QUERY_OPTIONS_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(queryOptions|infiniteQueryOptions)\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Query key factory pattern: const queryKeys = { all: [...], detail: (id) => [...] }
    QUERY_KEY_FACTORY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+(?:Keys?|QueryKeys?|queries))\s*=\s*\{',
        re.MULTILINE
    )

    # Standalone useQuery without destructuring
    STANDALONE_QUERY_PATTERN = re.compile(
        r'(useQuery|useSuspenseQuery)\s*(?:<([^>]*)>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # Query configuration keys
    QUERY_CONFIG_KEYS = {
        'enabled': 'has_enabled',
        'select': 'has_select',
        'staleTime': 'has_stale_time',
        'gcTime': 'has_gc_time',
        'cacheTime': 'has_cache_time',
        'refetchInterval': 'has_refetch_interval',
        'refetchOnWindowFocus': 'has_refetch_on_window_focus',
        'placeholderData': 'has_placeholder_data',
        'initialData': 'has_initial_data',
        'keepPreviousData': 'has_keep_previous_data',
        'retry': 'has_retry',
        'useErrorBoundary': 'has_error_boundary',
        'throwOnError': 'has_error_boundary',
        'suspense': 'has_suspense',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all TanStack Query query patterns from source code."""
        result: Dict[str, Any] = {
            'queries': [],
            'infinite_queries': [],
            'parallel_queries': [],
            'query_key_factories': [],
            'query_options': [],
        }

        lines = content.split('\n')

        # Extract useQuery / useSuspenseQuery
        for match in self.USE_QUERY_PATTERN.finditer(content):
            var_name = match.group(1).strip('{}').strip().split(',')[0].strip()
            hook_name = match.group(2)
            type_params = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start()]

            # Get surrounding context for config detection
            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 800)
            context = content[ctx_start:ctx_end]

            query = TanStackQueryInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                hook_name=hook_name,
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
                has_suspense=hook_name == "useSuspenseQuery",
            )

            # Detect query key
            qk_match = re.search(r'queryKey\s*:\s*(\[[^\]]*\]|\w+)', context)
            if qk_match:
                query.query_key = qk_match.group(1).strip()

            # Detect query function
            qf_match = re.search(r'queryFn\s*:\s*(\w+|(?:async\s*)?\([^)]*\)\s*=>)', context)
            if qf_match:
                query.query_fn = qf_match.group(1).strip()

            # Detect queryOptions helper usage
            if 'queryOptions' in context[:100]:
                query.uses_query_options = True

            # Detect configuration keys
            for key, attr in self.QUERY_CONFIG_KEYS.items():
                if re.search(rf'\b{key}\s*:', context):
                    setattr(query, attr, True)

            result['queries'].append(query)

        # Track matched positions to avoid duplicates
        matched_positions = {q.line_number for q in result['queries']}

        # Extract standalone useQuery / useSuspenseQuery (e.g. return useQuery(...))
        for match in self.STANDALONE_QUERY_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            if line_num in matched_positions:
                continue
            matched_positions.add(line_num)

            hook_name = match.group(1)
            type_params = match.group(2) or ""

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 800)
            context = content[ctx_start:ctx_end]

            # Try to infer name from enclosing function
            before_context = content[max(0, match.start() - 300):match.start()]
            name_match = re.search(r'(?:function|const|let|var)\s+(\w+)', before_context)
            var_name = name_match.group(1) if name_match else "anonymous"

            query = TanStackQueryInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                hook_name=hook_name,
                has_typescript=bool(type_params),
                type_params=type_params,
                has_suspense=hook_name == "useSuspenseQuery",
            )

            # Detect query key
            qk_match = re.search(r'queryKey\s*:\s*(\[[^\]]*\]|\w+)', context)
            if qk_match:
                query.query_key = qk_match.group(1).strip()

            # Detect query function
            qf_match = re.search(r'queryFn\s*:\s*(\w+|(?:async\s*)?\([^)]*\)\s*=>)', context)
            if qf_match:
                query.query_fn = qf_match.group(1).strip()

            # Detect configuration keys
            for key, attr in self.QUERY_CONFIG_KEYS.items():
                if re.search(rf'\b{key}\s*:', context):
                    setattr(query, attr, True)

            result['queries'].append(query)

        # Extract useInfiniteQuery / useSuspenseInfiniteQuery
        for match in self.USE_INFINITE_QUERY_PATTERN.finditer(content):
            var_name = match.group(1).strip('{}').strip().split(',')[0].strip()
            hook_name = match.group(2)
            type_params = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start()]

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 800)
            context = content[ctx_start:ctx_end]

            iq = TanStackInfiniteQueryInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                hook_name=hook_name,
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
            )

            # Detect query key
            qk_match = re.search(r'queryKey\s*:\s*(\[[^\]]*\]|\w+)', context)
            if qk_match:
                iq.query_key = qk_match.group(1).strip()

            # Detect query function
            qf_match = re.search(r'queryFn\s*:\s*(\w+|(?:async\s*)?\([^)]*\)\s*=>)', context)
            if qf_match:
                iq.query_fn = qf_match.group(1).strip()

            # Infinite-specific options
            if re.search(r'getNextPageParam\s*:', context):
                iq.has_get_next_page_param = True
            if re.search(r'getPreviousPageParam\s*:', context):
                iq.has_get_previous_page_param = True
            if re.search(r'initialPageParam\s*:', context):
                iq.has_initial_page_param = True
            if re.search(r'maxPages\s*:', context):
                iq.has_max_pages = True
            if re.search(r'\benabled\s*:', context):
                iq.has_enabled = True
            if re.search(r'\bselect\s*:', context):
                iq.has_select = True

            result['infinite_queries'].append(iq)

        # Extract useQueries
        for match in self.USE_QUERIES_PATTERN.finditer(content):
            var_name = match.group(1)
            type_params = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start()]

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 600)
            context = content[ctx_start:ctx_end]

            # Count queries in array
            query_count = context.count('queryKey')

            pq = TanStackQueriesInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                query_count=max(query_count, 1),
                has_combine='combine' in context,
                has_typescript=bool(type_params),
                is_exported=is_exported,
            )
            result['parallel_queries'].append(pq)

        # Extract queryOptions / infiniteQueryOptions (v5)
        for match in self.QUERY_OPTIONS_PATTERN.finditer(content):
            var_name = match.group(1)
            helper_name = match.group(2)
            type_params = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1

            result['query_options'].append({
                'name': var_name,
                'helper': helper_name,
                'file': file_path,
                'line_number': line_num,
                'has_typescript': bool(type_params),
                'type_params': type_params,
            })

        # Extract query key factories
        for match in self.QUERY_KEY_FACTORY_PATTERN.finditer(content):
            factory_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 600)
            context = content[ctx_start:ctx_end]

            # Extract key names from factory
            key_names = re.findall(r'(\w+)\s*:\s*(?:\[|[\(\)]|\w)', context)

            result['query_key_factories'].append({
                'name': factory_name,
                'file': file_path,
                'line_number': line_num,
                'keys': key_names[:15],
            })

        return result
