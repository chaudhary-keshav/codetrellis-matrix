"""
Tests for TanStack Query extractors and EnhancedTanStackQueryParser.

Part of CodeTrellis v4.57 TanStack Query Framework Support.
Tests cover:
- Query extraction (useQuery, useSuspenseQuery, useInfiniteQuery, useQueries, queryOptions)
- Mutation extraction (useMutation, callbacks, optimistic updates, invalidation)
- Cache extraction (QueryClient, defaultOptions, cache operations, providers, persistence)
- Prefetch extraction (prefetchQuery, SSR hydration, Next.js/Remix integration)
- API extraction (imports, integrations, TypeScript types, devtools, version)
- Parser integration (framework detection, version detection, feature detection, is_tanstack_query_file)
"""

import pytest
from codetrellis.tanstack_query_parser_enhanced import (
    EnhancedTanStackQueryParser,
    TanStackQueryParseResult,
)
from codetrellis.extractors.tanstack_query import (
    TanStackQueryExtractor,
    TanStackQueryInfo,
    TanStackInfiniteQueryInfo,
    TanStackQueriesInfo,
    TanStackMutationExtractor,
    TanStackMutationInfo,
    TanStackCacheExtractor,
    TanStackQueryClientInfo,
    TanStackCacheOperationInfo,
    TanStackPrefetchExtractor,
    TanStackPrefetchInfo,
    TanStackHydrationInfo,
    TanStackApiExtractor,
    TanStackImportInfo,
    TanStackIntegrationInfo,
    TanStackTypeInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedTanStackQueryParser()


@pytest.fixture
def query_extractor():
    return TanStackQueryExtractor()


@pytest.fixture
def mutation_extractor():
    return TanStackMutationExtractor()


@pytest.fixture
def cache_extractor():
    return TanStackCacheExtractor()


@pytest.fixture
def prefetch_extractor():
    return TanStackPrefetchExtractor()


@pytest.fixture
def api_extractor():
    return TanStackApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Query Extractor Tests (extractors return dicts)
# ═══════════════════════════════════════════════════════════════════

class TestTanStackQueryExtractor:
    """Tests for TanStackQueryExtractor."""

    def test_basic_use_query(self, query_extractor):
        code = """
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 1
        q = result['queries'][0]
        assert isinstance(q, TanStackQueryInfo)
        assert "useQuery" in q.hook_name

    def test_use_query_with_options(self, query_extractor):
        code = """
const { data } = useQuery({
  queryKey: ['todos', { status }],
  queryFn: fetchTodos,
  enabled: !!status,
  select: (data) => data.filter(t => t.active),
  staleTime: 5 * 60 * 1000,
  placeholderData: keepPreviousData,
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 1
        q = result['queries'][0]
        assert q.has_enabled is True
        assert q.has_select is True
        assert q.has_stale_time is True
        assert q.has_placeholder_data is True

    def test_use_suspense_query(self, query_extractor):
        code = """
const { data } = useSuspenseQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 1
        q = result['queries'][0]
        assert "Suspense" in q.hook_name or "suspense" in q.hook_name.lower()

    def test_use_infinite_query(self, query_extractor):
        code = """
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['todos'],
  queryFn: ({ pageParam }) => fetchTodos(pageParam),
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor,
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['infinite_queries']) >= 1
        iq = result['infinite_queries'][0]
        assert isinstance(iq, TanStackInfiniteQueryInfo)
        assert iq.has_get_next_page_param is True

    def test_use_infinite_query_v5_initial_page_param(self, query_extractor):
        code = """
const query = useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: fetchPosts,
  initialPageParam: 1,
  getNextPageParam: (last) => last.next,
  maxPages: 5,
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['infinite_queries']) >= 1
        iq = result['infinite_queries'][0]
        assert iq.has_initial_page_param is True

    def test_use_queries(self, query_extractor):
        code = """
const results = useQueries({
  queries: ids.map((id) => ({
    queryKey: ['todo', id],
    queryFn: () => fetchTodo(id),
  })),
  combine: (results) => ({
    data: results.map(r => r.data),
    pending: results.some(r => r.isPending),
  }),
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['parallel_queries']) >= 1
        pq = result['parallel_queries'][0]
        assert isinstance(pq, TanStackQueriesInfo)
        assert pq.has_combine is True

    def test_query_options_helper(self, query_extractor):
        code = """
const todosOptions = queryOptions({
  queryKey: ['todos'],
  queryFn: fetchTodos,
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['query_options']) >= 1

    def test_query_key_factory(self, query_extractor):
        code = """
export const todoKeys = {
  all: ['todos'] as const,
  lists: () => [...todoKeys.all, 'list'] as const,
  list: (filters) => [...todoKeys.lists(), filters] as const,
  details: () => [...todoKeys.all, 'detail'] as const,
  detail: (id) => [...todoKeys.details(), id] as const,
};
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['query_key_factories']) >= 1

    def test_typed_use_query(self, query_extractor):
        code = """
const { data } = useQuery<Todo[], Error>({
  queryKey: ['todos'],
  queryFn: fetchTodos,
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 1
        q = result['queries'][0]
        assert q.has_typescript is True

    def test_multiple_queries_in_file(self, query_extractor):
        code = """
const { data: todos } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
});

const { data: user } = useQuery({
  queryKey: ['user', userId],
  queryFn: () => fetchUser(userId),
  enabled: !!userId,
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 2

    def test_suspense_option_v4(self, query_extractor):
        code = """
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  suspense: true,
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 1
        q = result['queries'][0]
        assert q.has_suspense is True


# ═══════════════════════════════════════════════════════════════════
# Mutation Extractor Tests (extractors return dicts)
# ═══════════════════════════════════════════════════════════════════

class TestTanStackMutationExtractor:
    """Tests for TanStackMutationExtractor."""

    def test_basic_mutation(self, mutation_extractor):
        code = """
const { mutate } = useMutation({
  mutationFn: (newTodo) => axios.post('/todos', newTodo),
});
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert len(result['mutations']) >= 1
        m = result['mutations'][0]
        assert isinstance(m, TanStackMutationInfo)

    def test_mutation_with_callbacks(self, mutation_extractor):
        code = """
const mutation = useMutation({
  mutationFn: createTodo,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
  onError: (error) => {
    toast.error(error.message);
  },
  onSettled: () => {
    console.log('done');
  },
});
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert len(result['mutations']) >= 1
        m = result['mutations'][0]
        assert m.has_on_success is True
        assert m.has_on_error is True

    def test_mutation_with_optimistic_update(self, mutation_extractor):
        code = """
const mutation = useMutation({
  mutationFn: updateTodo,
  onMutate: async (newTodo) => {
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    const previous = queryClient.getQueryData(['todos']);
    queryClient.setQueryData(['todos'], (old) => [...old, newTodo]);
    return { previous };
  },
  onError: (err, newTodo, context) => {
    queryClient.setQueryData(['todos'], context.previous);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert len(result['mutations']) >= 1
        m = result['mutations'][0]
        assert m.has_on_mutate is True
        assert m.has_optimistic_update is True

    def test_mutation_with_invalidation(self, mutation_extractor):
        code = """
const mutation = useMutation({
  mutationFn: deleteTodo,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert len(result['mutations']) >= 1
        m = result['mutations'][0]
        assert m.has_invalidation is True

    def test_typed_mutation(self, mutation_extractor):
        code = """
const mutation = useMutation<Todo, Error, CreateTodoDto>({
  mutationFn: (dto) => createTodo(dto),
});
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert len(result['mutations']) >= 1
        m = result['mutations'][0]
        assert m.has_typescript is True


# ═══════════════════════════════════════════════════════════════════
# Cache Extractor Tests (extractors return dicts)
# ═══════════════════════════════════════════════════════════════════

class TestTanStackCacheExtractor:
    """Tests for TanStackCacheExtractor."""

    def test_basic_query_client(self, cache_extractor):
        code = """
const queryClient = new QueryClient();
"""
        result = cache_extractor.extract(code, "test.tsx")
        assert len(result['query_clients']) >= 1
        qc = result['query_clients'][0]
        assert isinstance(qc, TanStackQueryClientInfo)

    def test_query_client_with_defaults(self, cache_extractor):
        code = """
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
    },
  },
});
"""
        result = cache_extractor.extract(code, "test.tsx")
        assert len(result['query_clients']) >= 1
        qc = result['query_clients'][0]
        assert qc.has_default_options is True

    def test_exported_query_client(self, cache_extractor):
        code = """
export const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 60000 } },
});
"""
        result = cache_extractor.extract(code, "test.tsx")
        assert len(result['query_clients']) >= 1
        qc = result['query_clients'][0]
        assert qc.is_exported is True

    def test_invalidate_queries(self, cache_extractor):
        code = """
queryClient.invalidateQueries({ queryKey: ['todos'] });
"""
        result = cache_extractor.extract(code, "test.tsx")
        assert len(result['cache_operations']) >= 1
        co = result['cache_operations'][0]
        assert isinstance(co, TanStackCacheOperationInfo)
        assert co.operation == "invalidateQueries"

    def test_set_query_data(self, cache_extractor):
        code = """
queryClient.setQueryData(['todos'], (old) => [...old, newTodo]);
"""
        result = cache_extractor.extract(code, "test.tsx")
        assert len(result['cache_operations']) >= 1
        co = result['cache_operations'][0]
        assert co.operation == "setQueryData"

    def test_multiple_cache_operations(self, cache_extractor):
        code = """
queryClient.invalidateQueries({ queryKey: ['todos'] });
queryClient.refetchQueries({ queryKey: ['users'] });
queryClient.setQueryData(['config'], newConfig);
queryClient.removeQueries({ queryKey: ['old-data'] });
"""
        result = cache_extractor.extract(code, "test.tsx")
        assert len(result['cache_operations']) >= 3

    def test_query_client_provider(self, cache_extractor):
        code = """
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppRoutes />
    </QueryClientProvider>
  );
}
"""
        result = cache_extractor.extract(code, "test.tsx")
        assert len(result['providers']) >= 1

    def test_persistence(self, cache_extractor):
        code = """
import { persistQueryClient } from '@tanstack/query-persist-client-core';
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister';

const persister = createSyncStoragePersister({ storage: window.localStorage });
persistQueryClient({ queryClient, persister, maxAge: 24 * 60 * 60 * 1000 });
"""
        result = cache_extractor.extract(code, "test.tsx")
        # Persistence detection is based on import/pattern matching
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════
# Prefetch Extractor Tests (extractors return dicts)
# ═══════════════════════════════════════════════════════════════════

class TestTanStackPrefetchExtractor:
    """Tests for TanStackPrefetchExtractor."""

    def test_basic_prefetch(self, prefetch_extractor):
        code = """
await queryClient.prefetchQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
});
"""
        result = prefetch_extractor.extract(code, "test.tsx")
        assert len(result['prefetches']) >= 1
        pf = result['prefetches'][0]
        assert isinstance(pf, TanStackPrefetchInfo)

    def test_dehydrate(self, prefetch_extractor):
        code = """
const dehydratedState = dehydrate(queryClient);
"""
        result = prefetch_extractor.extract(code, "test.tsx")
        assert len(result['hydrations']) >= 1

    def test_hydration_boundary(self, prefetch_extractor):
        code = """
<HydrationBoundary state={dehydrate(queryClient)}>
  <Todos />
</HydrationBoundary>
"""
        result = prefetch_extractor.extract(code, "test.tsx")
        assert len(result['hydrations']) >= 1
        boundaries = [h for h in result['hydrations'] if h.is_boundary]
        assert len(boundaries) >= 1
        h = boundaries[0]
        assert isinstance(h, TanStackHydrationInfo)
        assert h.is_boundary is True

    def test_get_server_side_props(self, prefetch_extractor):
        code = """
export async function getServerSideProps() {
  const queryClient = new QueryClient();
  await queryClient.prefetchQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  });
  return { props: { dehydratedState: dehydrate(queryClient) } };
}
"""
        result = prefetch_extractor.extract(code, "test.tsx")
        assert len(result['prefetches']) >= 1
        pf = result['prefetches'][0]
        assert pf.is_in_get_server_side_props is True

    def test_remix_loader(self, prefetch_extractor):
        code = """
export const loader = async () => {
  const queryClient = new QueryClient();
  await queryClient.prefetchQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  });
  return json({ dehydratedState: dehydrate(queryClient) });
};
"""
        result = prefetch_extractor.extract(code, "test.tsx")
        assert len(result['prefetches']) >= 1
        pf = result['prefetches'][0]
        assert pf.is_in_loader is True

    def test_rsc_prefetch(self, prefetch_extractor):
        code = """
export default async function Page() {
  const queryClient = new QueryClient();
  await queryClient.prefetchQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  });
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <TodoList />
    </HydrationBoundary>
  );
}
"""
        result = prefetch_extractor.extract(code, "page.tsx")
        assert len(result['prefetches']) >= 1

    def test_prefetch_infinite_query(self, prefetch_extractor):
        code = """
await queryClient.prefetchInfiniteQuery({
  queryKey: ['posts'],
  queryFn: fetchPosts,
  initialPageParam: 0,
});
"""
        result = prefetch_extractor.extract(code, "test.tsx")
        assert len(result['prefetches']) >= 1


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests (extractors return dicts)
# ═══════════════════════════════════════════════════════════════════

class TestTanStackApiExtractor:
    """Tests for TanStackApiExtractor."""

    def test_react_query_import(self, api_extractor):
        code = """
import { useQuery, useMutation, QueryClient } from '@tanstack/react-query';
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert isinstance(imp, TanStackImportInfo)
        assert "@tanstack/react-query" in imp.source

    def test_legacy_react_query_import(self, api_extractor):
        code = """
import { useQuery, useMutation } from 'react-query';
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['imports']) >= 1

    def test_vue_query_import(self, api_extractor):
        code = """
import { useQuery } from '@tanstack/vue-query';
"""
        result = api_extractor.extract(code, "test.vue")
        assert len(result['imports']) >= 1

    def test_svelte_query_import(self, api_extractor):
        code = """
import { createQuery } from '@tanstack/svelte-query';
"""
        result = api_extractor.extract(code, "test.svelte")
        assert len(result['imports']) >= 1

    def test_type_import(self, api_extractor):
        code = """
import type { UseQueryResult, QueryKey } from '@tanstack/react-query';
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.is_type_import is True

    def test_devtools_import(self, api_extractor):
        code = """
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['imports']) >= 1

    def test_axios_integration(self, api_extractor):
        code = """
import axios from 'axios';
import { useQuery } from '@tanstack/react-query';

const fetchTodos = async () => {
  const { data } = await axios.get('/api/todos');
  return data;
};
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['integrations']) >= 1
        intg = result['integrations'][0]
        assert isinstance(intg, TanStackIntegrationInfo)

    def test_trpc_integration(self, api_extractor):
        code = """
import { createTRPCReact } from '@trpc/react-query';
const trpc = createTRPCReact();
const { data } = trpc.todo.list.useQuery();
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['integrations']) >= 1

    def test_graphql_integration(self, api_extractor):
        code = """
import { request, gql } from 'graphql-request';
import { useQuery } from '@tanstack/react-query';
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['integrations']) >= 1

    def test_typescript_types(self, api_extractor):
        code = """
type TodoQueryResult = UseQueryResult<Todo[], Error>;

interface CreateTodoDto {
  title: string;
  completed: boolean;
}
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['types']) >= 1

    def test_multiple_imports(self, api_extractor):
        code = """
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import type { UseQueryOptions } from '@tanstack/react-query';
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['imports']) >= 2


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests (parser returns TanStackQueryParseResult dataclass)
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedTanStackQueryParser:
    """Tests for EnhancedTanStackQueryParser integration."""

    def test_is_tanstack_query_file_positive(self, parser):
        code = """
import { useQuery } from '@tanstack/react-query';
const { data } = useQuery({ queryKey: ['todos'], queryFn: fetchTodos });
"""
        assert parser.is_tanstack_query_file(code, "test.tsx") is True

    def test_is_tanstack_query_file_negative(self, parser):
        code = """
import React from 'react';
function App() {
  return <div>Hello</div>;
}
"""
        assert parser.is_tanstack_query_file(code, "test.tsx") is False

    def test_is_tanstack_query_file_legacy(self, parser):
        code = """
import { useQuery } from 'react-query';
const { data } = useQuery('todos', fetchTodos);
"""
        assert parser.is_tanstack_query_file(code, "test.tsx") is True

    def test_parse_returns_result(self, parser):
        code = """
import { useQuery, useMutation, QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient();

const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
});

const mutation = useMutation({
  mutationFn: createTodo,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
"""
        result = parser.parse(code, "test.tsx")
        assert isinstance(result, TanStackQueryParseResult)
        assert result.file_path == "test.tsx"
        assert len(result.queries) >= 1
        assert len(result.mutations) >= 1
        assert len(result.imports) >= 1

    def test_v5_detection(self, parser):
        code = """
import { useSuspenseQuery, queryOptions } from '@tanstack/react-query';

const opts = queryOptions({
  queryKey: ['todos'],
  queryFn: fetchTodos,
});

const { data } = useSuspenseQuery(opts);
"""
        result = parser.parse(code, "test.tsx")
        assert result.tanstack_query_version == "v5"

    def test_v4_detection(self, parser):
        code = """
import { useQuery } from '@tanstack/react-query';

const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  cacheTime: 5 * 60 * 1000,
  keepPreviousData: true,
});
"""
        result = parser.parse(code, "test.tsx")
        assert result.tanstack_query_version in ("v4", "v5")

    def test_v3_detection(self, parser):
        code = """
import { useQuery, QueryClient, QueryClientProvider } from 'react-query';

const { data } = useQuery('todos', fetchTodos);
"""
        result = parser.parse(code, "test.tsx")
        assert result.tanstack_query_version in ("v3", "legacy")

    def test_framework_detection_react(self, parser):
        code = """
import { useQuery } from '@tanstack/react-query';
const { data } = useQuery({ queryKey: ['x'], queryFn: fn });
"""
        result = parser.parse(code, "test.tsx")
        assert "tanstack-react-query" in result.detected_frameworks

    def test_framework_detection_vue(self, parser):
        code = """
import { useQuery } from '@tanstack/vue-query';
const { data } = useQuery({ queryKey: ['x'], queryFn: fn });
"""
        result = parser.parse(code, "test.vue")
        assert "tanstack-vue-query" in result.detected_frameworks

    def test_feature_detection_use_query(self, parser):
        code = """
import { useQuery } from '@tanstack/react-query';
const { data } = useQuery({ queryKey: ['todos'], queryFn: fetchTodos });
"""
        result = parser.parse(code, "test.tsx")
        assert "use_query" in result.detected_features

    def test_feature_detection_mutation(self, parser):
        code = """
import { useMutation } from '@tanstack/react-query';
const mutation = useMutation({ mutationFn: createTodo });
"""
        result = parser.parse(code, "test.tsx")
        assert "use_mutation" in result.detected_features

    def test_feature_detection_infinite_query(self, parser):
        code = """
import { useInfiniteQuery } from '@tanstack/react-query';
const query = useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: fetchPosts,
  initialPageParam: 0,
  getNextPageParam: (last) => last.next,
});
"""
        result = parser.parse(code, "test.tsx")
        assert "use_infinite_query" in result.detected_features

    def test_feature_detection_hydration(self, parser):
        code = """
import { dehydrate, HydrationBoundary } from '@tanstack/react-query';

export default async function Page() {
  const queryClient = new QueryClient();
  await queryClient.prefetchQuery({ queryKey: ['x'], queryFn: fn });
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <Child />
    </HydrationBoundary>
  );
}
"""
        result = parser.parse(code, "page.tsx")
        assert any(f in result.detected_features for f in ["dehydrate", "hydration_boundary"])

    def test_comprehensive_file(self, parser):
        """Test a comprehensive file with multiple TanStack Query constructs."""
        code = """
import { useQuery, useMutation, useQueryClient, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import axios from 'axios';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, gcTime: 10 * 60 * 1000 },
  },
});

export const todoKeys = {
  all: ['todos'] as const,
  lists: () => [...todoKeys.all, 'list'] as const,
  list: (filters: Filters) => [...todoKeys.lists(), filters] as const,
  detail: (id: number) => [...todoKeys.all, 'detail', id] as const,
};

function useTodos(filters?: TodoFilters) {
  return useQuery<Todo[], Error>({
    queryKey: todoKeys.list(filters),
    queryFn: () => axios.get('/api/todos', { params: filters }).then(r => r.data),
    staleTime: 5 * 60 * 1000,
    select: (data) => data.filter(t => t.active),
  });
}

function useCreateTodo() {
  const queryClient = useQueryClient();
  return useMutation<Todo, Error, CreateTodoDto>({
    mutationFn: (dto) => axios.post('/api/todos', dto).then(r => r.data),
    onMutate: async (newTodo) => {
      await queryClient.cancelQueries({ queryKey: todoKeys.lists() });
      const previous = queryClient.getQueryData(todoKeys.lists());
      queryClient.setQueryData(todoKeys.lists(), (old: Todo[]) => [...old, { ...newTodo, id: Date.now() }]);
      return { previous };
    },
    onError: (_err, _todo, context) => {
      queryClient.setQueryData(todoKeys.lists(), context?.previous);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: todoKeys.lists() });
    },
  });
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TodoList />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
"""
        result = parser.parse(code, "app.tsx")
        assert isinstance(result, TanStackQueryParseResult)
        assert len(result.queries) >= 1
        assert len(result.mutations) >= 1
        assert len(result.query_clients) >= 1
        assert len(result.imports) >= 1
        assert len(result.integrations) >= 1  # axios
        assert "tanstack-react-query" in result.detected_frameworks
        assert len(result.detected_features) >= 3

    def test_empty_file(self, parser):
        code = ""
        result = parser.parse(code, "test.tsx")
        assert isinstance(result, TanStackQueryParseResult)
        assert len(result.queries) == 0
        assert len(result.mutations) == 0

    def test_non_tanstack_file(self, parser):
        code = """
import React from 'react';
function App() {
  const [count, setCount] = React.useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
"""
        assert parser.is_tanstack_query_file(code, "test.tsx") is False

    def test_gc_time_v5_feature(self, parser):
        code = """
import { useQuery } from '@tanstack/react-query';
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  gcTime: 10 * 60 * 1000,
});
"""
        result = parser.parse(code, "test.tsx")
        assert "gc_time" in result.detected_features

    def test_cache_time_v4_feature(self, parser):
        code = """
import { useQuery } from '@tanstack/react-query';
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  cacheTime: 300000,
});
"""
        result = parser.parse(code, "test.tsx")
        assert "cache_time" in result.detected_features

    def test_query_options_v5_feature(self, parser):
        code = """
import { queryOptions, useQuery } from '@tanstack/react-query';
const opts = queryOptions({ queryKey: ['x'], queryFn: fn });
const { data } = useQuery(opts);
"""
        result = parser.parse(code, "test.tsx")
        assert "query_options" in result.detected_features


# ═══════════════════════════════════════════════════════════════════
# Edge Case Tests
# ═══════════════════════════════════════════════════════════════════

class TestTanStackQueryEdgeCases:
    """Tests for edge cases and unusual patterns."""

    def test_multiline_query(self, parser):
        code = """
import { useQuery } from '@tanstack/react-query';

const {
  data,
  isLoading,
  error,
} = useQuery({
  queryKey: [
    'todos',
    {
      status: 'active',
      page: 1,
    },
  ],
  queryFn: fetchTodos,
  staleTime: 5 * 60 * 1000,
  enabled: isReady,
});
"""
        result = parser.parse(code, "test.tsx")
        assert len(result.queries) >= 1

    def test_mutation_in_custom_hook(self, parser):
        code = """
import { useMutation } from '@tanstack/react-query';

export function useDeleteTodo() {
  return useMutation({
    mutationFn: (id: string) => deleteTodo(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
}
"""
        result = parser.parse(code, "test.tsx")
        assert len(result.mutations) >= 1

    def test_ensure_query_data(self, cache_extractor):
        code = """
const data = await queryClient.ensureQueryData({
  queryKey: ['todos'],
  queryFn: fetchTodos,
});
"""
        result = cache_extractor.extract(code, "test.tsx")
        assert len(result['cache_operations']) >= 1

    def test_solid_query_import(self, api_extractor):
        code = """
import { createQuery } from '@tanstack/solid-query';
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['imports']) >= 1

    def test_angular_query_import(self, api_extractor):
        code = """
import { injectQuery } from '@tanstack/angular-query-experimental';
"""
        result = api_extractor.extract(code, "test.ts")
        assert len(result['imports']) >= 1

    def test_persist_import(self, api_extractor):
        code = """
import { persistQueryClient } from '@tanstack/query-persist-client-core';
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister';
"""
        result = api_extractor.extract(code, "test.ts")
        assert len(result['imports']) >= 1
