"""
Tests for SWR extractors and EnhancedSWRParser.

Part of CodeTrellis v4.58 SWR Framework Support.
Tests cover:
- Hook extraction (useSWR, useSWRImmutable, useSWRInfinite, useSWRSubscription)
- Mutation extraction (useSWRMutation, optimistic updates)
- Cache extraction (SWRConfig, global/bound mutate, preload)
- Middleware extraction (custom middleware, use option)
- API extraction (imports, integrations, TypeScript types)
- Parser integration (framework detection, version detection, feature detection, is_swr_file)
"""

import pytest
from codetrellis.swr_parser_enhanced import (
    EnhancedSWRParser,
    SWRParseResult,
)
from codetrellis.extractors.swr import (
    SWRHookExtractor,
    SWRHookInfo,
    SWRInfiniteInfo,
    SWRSubscriptionInfo,
    SWRMutationExtractor,
    SWRMutationHookInfo,
    SWROptimisticUpdateInfo,
    SWRCacheExtractor,
    SWRConfigInfo,
    SWRMutateInfo,
    SWRPreloadInfo,
    SWRMiddlewareExtractor,
    SWRMiddlewareInfo,
    SWRApiExtractor,
    SWRImportInfo,
    SWRIntegrationInfo,
    SWRTypeInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedSWRParser()


@pytest.fixture
def hook_extractor():
    return SWRHookExtractor()


@pytest.fixture
def mutation_extractor():
    return SWRMutationExtractor()


@pytest.fixture
def cache_extractor():
    return SWRCacheExtractor()


@pytest.fixture
def middleware_extractor():
    return SWRMiddlewareExtractor()


@pytest.fixture
def api_extractor():
    return SWRApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Hook Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSWRHookExtractor:
    """Tests for SWRHookExtractor."""

    def test_basic_use_swr(self, hook_extractor):
        content = """
import useSWR from 'swr';

function UserProfile() {
  const { data, error } = useSWR('/api/user', fetcher);
  return <div>{data?.name}</div>;
}
"""
        result = hook_extractor.extract(content, "user.tsx")
        assert len(result['hooks']) > 0
        hook = result['hooks'][0]
        assert isinstance(hook, SWRHookInfo)

    def test_use_swr_with_config(self, hook_extractor):
        content = """
const { data } = useSWR('/api/data', fetcher, {
  revalidateOnFocus: false,
  refreshInterval: 3000,
  suspense: true,
  dedupingInterval: 5000,
});
"""
        result = hook_extractor.extract(content, "data.tsx")
        hooks = result['hooks']
        assert len(hooks) > 0

    def test_use_swr_immutable(self, hook_extractor):
        content = """
import useSWRImmutable from 'swr/immutable';
const { data } = useSWRImmutable('/api/config', fetcher);
"""
        result = hook_extractor.extract(content, "config.tsx")
        hooks = result['hooks']
        assert len(hooks) > 0

    def test_use_swr_conditional_null_key(self, hook_extractor):
        content = """
const { data } = useSWR(isLoggedIn ? '/api/user' : null, fetcher);
"""
        result = hook_extractor.extract(content, "cond.tsx")
        hooks = result['hooks']
        assert len(hooks) > 0

    def test_use_swr_with_typescript_generics(self, hook_extractor):
        content = """
const { data } = useSWR<User, Error>('/api/user', fetcher);
"""
        result = hook_extractor.extract(content, "user.tsx")
        hooks = result['hooks']
        assert len(hooks) > 0

    def test_use_swr_infinite(self, hook_extractor):
        content = """
import useSWRInfinite from 'swr/infinite';

const getKey = (pageIndex, previousPageData) => {
  if (previousPageData && !previousPageData.length) return null;
  return `/api/users?page=${pageIndex}`;
};

const { data, size, setSize } = useSWRInfinite(getKey, fetcher);
"""
        result = hook_extractor.extract(content, "infinite.tsx")
        infinite_hooks = result['infinite_hooks']
        assert len(infinite_hooks) > 0
        assert isinstance(infinite_hooks[0], SWRInfiniteInfo)

    def test_use_swr_subscription(self, hook_extractor):
        content = """
import useSWRSubscription from 'swr/subscription';

const { data } = useSWRSubscription('wss://stream', (key, { next }) => {
  const ws = new WebSocket(key);
  ws.onmessage = (e) => next(null, JSON.parse(e.data));
  ws.onerror = (e) => next(e.error);
  return () => ws.close();
});
"""
        result = hook_extractor.extract(content, "stream.tsx")
        subscription_hooks = result['subscription_hooks']
        assert len(subscription_hooks) > 0
        assert isinstance(subscription_hooks[0], SWRSubscriptionInfo)

    def test_multiple_hooks_in_one_file(self, hook_extractor):
        content = """
import useSWR from 'swr';

function Dashboard() {
  const { data: user } = useSWR('/api/user', fetcher);
  const { data: projects } = useSWR('/api/projects', fetcher);
  const { data: settings } = useSWR('/api/settings', fetcher);
}
"""
        result = hook_extractor.extract(content, "dashboard.tsx")
        assert len(result['hooks']) >= 3

    def test_dependent_fetching(self, hook_extractor):
        content = """
const { data: user } = useSWR('/api/user', fetcher);
const { data: projects } = useSWR(() => '/api/projects?uid=' + user.id, fetcher);
"""
        result = hook_extractor.extract(content, "dependent.tsx")
        assert len(result['hooks']) >= 1

    def test_fallback_data_option(self, hook_extractor):
        content = """
const { data } = useSWR('/api/user', fetcher, {
  fallbackData: serverData,
});
"""
        result = hook_extractor.extract(content, "fallback.tsx")
        assert len(result['hooks']) > 0

    def test_keep_previous_data(self, hook_extractor):
        content = """
const { data } = useSWR(`/api/users?page=${page}`, fetcher, {
  keepPreviousData: true,
});
"""
        result = hook_extractor.extract(content, "pagination.tsx")
        assert len(result['hooks']) > 0


# ═══════════════════════════════════════════════════════════════════
# Mutation Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSWRMutationExtractor:
    """Tests for SWRMutationExtractor."""

    def test_basic_use_swr_mutation(self, mutation_extractor):
        content = """
import useSWRMutation from 'swr/mutation';

const { trigger, isMutating } = useSWRMutation(
  '/api/user',
  (url, { arg }) => fetch(url, { method: 'POST', body: JSON.stringify(arg) })
);
"""
        result = mutation_extractor.extract(content, "mutation.tsx")
        assert len(result['mutation_hooks']) > 0
        mut = result['mutation_hooks'][0]
        assert isinstance(mut, SWRMutationHookInfo)

    def test_mutation_with_optimistic_data(self, mutation_extractor):
        content = """
const { trigger } = useSWRMutation('/api/todos', addTodo, {
  optimisticData: (current) => [...current, newTodo],
  rollbackOnError: true,
  populateCache: true,
  revalidate: false,
});
"""
        result = mutation_extractor.extract(content, "optimistic.tsx")
        assert len(result['mutation_hooks']) > 0

    def test_optimistic_update_pattern(self, mutation_extractor):
        content = """
const { trigger } = useSWRMutation('/api/todos', addTodo, {
  optimisticData: [...currentData, optimisticTodo],
  rollbackOnError: true,
  revalidate: false,
});
"""
        result = mutation_extractor.extract(content, "opt-update.tsx")
        # The mutation hook itself captures the optimistic pattern
        mutation_hooks = result['mutation_hooks']
        assert len(mutation_hooks) > 0

    def test_mutation_with_throw_on_error(self, mutation_extractor):
        content = """
const { trigger } = useSWRMutation('/api/user', updateUser, {
  throwOnError: true,
});
"""
        result = mutation_extractor.extract(content, "throw.tsx")
        assert len(result['mutation_hooks']) > 0

    def test_mutation_with_typescript(self, mutation_extractor):
        content = """
const { trigger } = useSWRMutation<User, Error, string, CreateUserArg>(
  '/api/users',
  (url, { arg }) => fetch(url, { method: 'POST', body: JSON.stringify(arg) })
);
"""
        result = mutation_extractor.extract(content, "typed-mut.tsx")
        assert len(result['mutation_hooks']) > 0


# ═══════════════════════════════════════════════════════════════════
# Cache Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSWRCacheExtractor:
    """Tests for SWRCacheExtractor."""

    def test_swr_config_basic(self, cache_extractor):
        content = """
<SWRConfig value={{
  fetcher: (url) => fetch(url).then(r => r.json()),
  revalidateOnFocus: true,
}}>
  <App />
</SWRConfig>
"""
        result = cache_extractor.extract(content, "app.tsx")
        configs = result['configs']
        assert len(configs) > 0
        assert isinstance(configs[0], SWRConfigInfo)

    def test_swr_config_with_fallback(self, cache_extractor):
        content = """
<SWRConfig value={{
  fallback: { '/api/user': userData },
  suspense: true,
}}>
  <App />
</SWRConfig>
"""
        result = cache_extractor.extract(content, "ssr.tsx")
        configs = result['configs']
        assert len(configs) > 0

    def test_swr_config_with_provider(self, cache_extractor):
        content = """
<SWRConfig value={{
  provider: () => new Map(),
}}>
  <App />
</SWRConfig>
"""
        result = cache_extractor.extract(content, "cache.tsx")
        configs = result['configs']
        assert len(configs) > 0

    def test_global_mutate(self, cache_extractor):
        content = """
import { mutate } from 'swr';

mutate('/api/user');
mutate((key) => key.startsWith('/api/'));
"""
        result = cache_extractor.extract(content, "global.tsx")
        mutate_calls = result['mutate_calls']
        assert len(mutate_calls) > 0

    def test_preload(self, cache_extractor):
        content = """
import { preload } from 'swr';

preload('/api/user', fetcher);
"""
        result = cache_extractor.extract(content, "preload.tsx")
        preloads = result['preloads']
        assert len(preloads) > 0
        assert isinstance(preloads[0], SWRPreloadInfo)

    def test_use_swr_config_hook(self, cache_extractor):
        content = """
import { useSWRConfig } from 'swr';

function LogoutButton() {
  const { cache, mutate } = useSWRConfig();
  return <button onClick={() => cache.delete('/api/user')}>Logout</button>;
}
"""
        result = cache_extractor.extract(content, "logout.tsx")
        config_hooks = result['config_hooks']
        assert len(config_hooks) > 0


# ═══════════════════════════════════════════════════════════════════
# Middleware Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSWRMiddlewareExtractor:
    """Tests for SWRMiddlewareExtractor."""

    def test_custom_middleware_definition(self, middleware_extractor):
        content = """
function logger(useSWRNext) {
  return (key, fetcher, config) => {
    const swr = useSWRNext(key, fetcher, config);
    console.log('SWR:', key, swr.data);
    return swr;
  };
}
"""
        result = middleware_extractor.extract(content, "logger.ts")
        middlewares = result['middlewares']
        assert len(middlewares) > 0
        assert isinstance(middlewares[0], SWRMiddlewareInfo)

    def test_middleware_use_option(self, middleware_extractor):
        content = """
useSWR('/api/data', fetcher, {
  use: [logger, authMiddleware, serialize],
});
"""
        result = middleware_extractor.extract(content, "mw.tsx")
        middlewares = result['middlewares']
        assert len(middlewares) > 0

    def test_arrow_function_middleware(self, middleware_extractor):
        content = """
const myMiddleware = (useSWRNext) => (key, fetcher, config) => {
  const swr = useSWRNext(key, fetcher, config);
  return { ...swr, data: transform(swr.data) };
};
"""
        result = middleware_extractor.extract(content, "mw-arrow.ts")
        middlewares = result['middlewares']
        assert len(middlewares) > 0


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSWRApiExtractor:
    """Tests for SWRApiExtractor."""

    def test_swr_import(self, api_extractor):
        content = """
import useSWR from 'swr';
"""
        result = api_extractor.extract(content, "imp.tsx")
        imports = result['imports']
        assert len(imports) > 0
        assert isinstance(imports[0], SWRImportInfo)

    def test_swr_subpackage_imports(self, api_extractor):
        content = """
import useSWRInfinite from 'swr/infinite';
import useSWRMutation from 'swr/mutation';
import useSWRSubscription from 'swr/subscription';
import useSWRImmutable from 'swr/immutable';
"""
        result = api_extractor.extract(content, "imports.tsx")
        imports = result['imports']
        assert len(imports) >= 4

    def test_named_imports(self, api_extractor):
        content = """
import { SWRConfig, mutate, preload } from 'swr';
"""
        result = api_extractor.extract(content, "named.tsx")
        imports = result['imports']
        assert len(imports) > 0

    def test_axios_integration(self, api_extractor):
        content = """
import useSWR from 'swr';
import axios from 'axios';

const fetcher = (url) => axios.get(url).then(r => r.data);
const { data } = useSWR('/api/user', fetcher);
"""
        result = api_extractor.extract(content, "axios.tsx")
        integrations = result['integrations']
        assert any(i.integration_type == 'http-client' for i in integrations)

    def test_nextjs_integration(self, api_extractor):
        content = """
import useSWR from 'swr';
import { GetServerSideProps } from 'next';

export const getServerSideProps: GetServerSideProps = async () => {
  const data = await fetchUser();
  return { props: { fallback: { '/api/user': data } } };
};
"""
        result = api_extractor.extract(content, "page.tsx")
        integrations = result['integrations']
        assert any(i.integration_type == 'nextjs' for i in integrations)

    def test_graphql_integration(self, api_extractor):
        content = """
import useSWR from 'swr';
import { request } from 'graphql-request';

const fetcher = (query) => request('/graphql', query);
"""
        result = api_extractor.extract(content, "graphql.tsx")
        integrations = result['integrations']
        assert any(i.integration_type == 'graphql' for i in integrations)

    def test_typescript_types(self, api_extractor):
        content = """
import type { SWRConfiguration, SWRResponse, Key } from 'swr';

type UserResponse = SWRResponse<User, Error>;
type AppConfig = SWRConfiguration<UserData>;
"""
        result = api_extractor.extract(content, "types.ts")
        types = result['types']
        assert len(types) > 0

    def test_msw_testing_integration(self, api_extractor):
        content = """
import useSWR from 'swr';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
"""
        result = api_extractor.extract(content, "test.tsx")
        integrations = result['integrations']
        assert any(i.integration_type == 'testing' for i in integrations)


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedSWRParser:
    """Tests for EnhancedSWRParser full integration."""

    def test_is_swr_file_positive(self, parser):
        content = """import useSWR from 'swr';"""
        assert parser.is_swr_file(content) is True

    def test_is_swr_file_negative(self, parser):
        content = """import React from 'react';"""
        assert parser.is_swr_file(content) is False

    def test_is_swr_file_mutation_import(self, parser):
        content = """import useSWRMutation from 'swr/mutation';"""
        assert parser.is_swr_file(content) is True

    def test_is_swr_file_infinite_import(self, parser):
        content = """import useSWRInfinite from 'swr/infinite';"""
        assert parser.is_swr_file(content) is True

    def test_is_swr_file_subscription_import(self, parser):
        content = """import useSWRSubscription from 'swr/subscription';"""
        assert parser.is_swr_file(content) is True

    def test_is_swr_file_config(self, parser):
        content = """<SWRConfig value={{}}>"""
        assert parser.is_swr_file(content) is True

    def test_parse_returns_parse_result(self, parser):
        content = """import useSWR from 'swr';
const { data } = useSWR('/api/user', fetcher);"""
        result = parser.parse(content, "test.tsx")
        assert isinstance(result, SWRParseResult)
        assert result.file_path == "test.tsx"
        assert result.file_type == "tsx"

    def test_parse_detects_file_type_tsx(self, parser):
        result = parser.parse("", "component.tsx")
        assert result.file_type == "tsx"

    def test_parse_detects_file_type_ts(self, parser):
        result = parser.parse("", "util.ts")
        assert result.file_type == "ts"

    def test_parse_detects_file_type_jsx(self, parser):
        result = parser.parse("", "page.jsx")
        assert result.file_type == "jsx"

    def test_parse_detects_file_type_js(self, parser):
        result = parser.parse("", "index.js")
        assert result.file_type == "js"

    # ── Framework Detection ────────────────────────────────────────

    def test_detect_swr_framework(self, parser):
        content = """import useSWR from 'swr';"""
        result = parser.parse(content, "test.tsx")
        assert 'swr' in result.detected_frameworks

    def test_detect_swr_infinite_framework(self, parser):
        content = """import useSWRInfinite from 'swr/infinite';"""
        result = parser.parse(content, "test.tsx")
        assert 'swr-infinite' in result.detected_frameworks

    def test_detect_swr_mutation_framework(self, parser):
        content = """import useSWRMutation from 'swr/mutation';"""
        result = parser.parse(content, "test.tsx")
        assert 'swr-mutation' in result.detected_frameworks

    def test_detect_swr_subscription_framework(self, parser):
        content = """import useSWRSubscription from 'swr/subscription';"""
        result = parser.parse(content, "test.tsx")
        assert 'swr-subscription' in result.detected_frameworks

    def test_detect_axios_framework(self, parser):
        content = """import useSWR from 'swr';
import axios from 'axios';"""
        result = parser.parse(content, "test.tsx")
        assert 'axios' in result.detected_frameworks

    def test_detect_react_framework(self, parser):
        content = """import useSWR from 'swr';
import React from 'react';"""
        result = parser.parse(content, "test.tsx")
        assert 'react' in result.detected_frameworks

    def test_detect_next_framework(self, parser):
        content = """import useSWR from 'swr';
import { GetServerSideProps } from 'next';"""
        result = parser.parse(content, "test.tsx")
        assert 'next' in result.detected_frameworks

    # ── Feature Detection ──────────────────────────────────────────

    def test_detect_use_swr_feature(self, parser):
        content = """const { data } = useSWR('/api/data', fetcher);"""
        result = parser.parse(content, "test.tsx")
        assert 'use_swr' in result.detected_features

    def test_detect_use_swr_infinite_feature(self, parser):
        content = """const { data } = useSWRInfinite(getKey, fetcher);"""
        result = parser.parse(content, "test.tsx")
        assert 'use_swr_infinite' in result.detected_features

    def test_detect_use_swr_mutation_feature(self, parser):
        content = """const { trigger } = useSWRMutation('/api', fn);"""
        result = parser.parse(content, "test.tsx")
        assert 'use_swr_mutation' in result.detected_features

    def test_detect_suspense_feature(self, parser):
        content = """useSWR('/api', fetcher, { suspense: true });"""
        result = parser.parse(content, "test.tsx")
        assert 'suspense' in result.detected_features

    def test_detect_swr_config_feature(self, parser):
        content = """<SWRConfig value={{ fetcher }}><App /></SWRConfig>"""
        result = parser.parse(content, "test.tsx")
        assert 'swr_config' in result.detected_features

    def test_detect_fallback_data_feature(self, parser):
        content = """useSWR('/api', fetcher, { fallbackData: data });"""
        result = parser.parse(content, "test.tsx")
        assert 'fallback_data' in result.detected_features

    def test_detect_keep_previous_data_feature(self, parser):
        content = """useSWR('/api', fetcher, { keepPreviousData: true });"""
        result = parser.parse(content, "test.tsx")
        assert 'keep_previous_data' in result.detected_features

    def test_detect_middleware_feature(self, parser):
        content = """useSWR('/api', fetcher, { use: [logger] });"""
        result = parser.parse(content, "test.tsx")
        assert 'middleware' in result.detected_features

    def test_detect_conditional_fetching_feature(self, parser):
        content = """useSWR(null, fetcher);"""
        result = parser.parse(content, "test.tsx")
        assert 'conditional_fetching' in result.detected_features

    def test_detect_refresh_interval_feature(self, parser):
        content = """useSWR('/api', fetcher, { refreshInterval: 3000 });"""
        result = parser.parse(content, "test.tsx")
        assert 'refresh_interval' in result.detected_features

    def test_detect_preload_feature(self, parser):
        content = """preload('/api/user', fetcher);"""
        result = parser.parse(content, "test.tsx")
        assert 'preload' in result.detected_features

    # ── Version Detection ──────────────────────────────────────────

    def test_detect_v2_useSWRMutation(self, parser):
        content = """
import useSWRMutation from 'swr/mutation';
const { trigger } = useSWRMutation('/api', fn);
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v2"

    def test_detect_v2_useSWRSubscription(self, parser):
        content = """
import useSWRSubscription from 'swr/subscription';
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v2"

    def test_detect_v2_preload(self, parser):
        content = """
import { preload } from 'swr';
preload('/api/data', fetcher);
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v2"

    def test_detect_v2_keep_previous_data(self, parser):
        content = """
useSWR('/api', fetcher, { keepPreviousData: true });
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v2"

    def test_detect_v2_optimistic_data(self, parser):
        content = """
mutate('/api', newData, { optimisticData: data, rollbackOnError: true });
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v2"

    def test_detect_v2_throw_on_error(self, parser):
        content = """
useSWR('/api', fetcher, { throwOnError: true });
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v2"

    def test_detect_v1_swr_config(self, parser):
        content = """
<SWRConfig value={{ fetcher }}>
  <App />
</SWRConfig>
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v1"

    def test_detect_v1_fallback_data(self, parser):
        content = """
useSWR('/api', fetcher, { fallbackData: data });
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v1"

    def test_detect_v1_immutable(self, parser):
        content = """
import useSWRImmutable from 'swr/immutable';
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v1"

    def test_detect_v0_initial_data(self, parser):
        content = """
useSWR('/api', fetcher, { initialData: data });
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v0"

    def test_v2_takes_priority_over_v1(self, parser):
        content = """
import useSWRMutation from 'swr/mutation';
<SWRConfig value={{ fetcher }}>
  <App />
</SWRConfig>
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v2"

    def test_detect_default_v2_with_just_useSWR(self, parser):
        content = """
useSWR('/api/user', fetcher);
"""
        result = parser.parse(content, "test.tsx")
        assert result.swr_version == "v2"

    def test_empty_file(self, parser):
        result = parser.parse("", "test.tsx")
        assert result.swr_version == ""
        assert result.detected_frameworks == []
        assert result.detected_features == []

    # ── Full Integration Parse ─────────────────────────────────────

    def test_full_parse_comprehensive(self, parser):
        content = """
import useSWR, { SWRConfig, mutate, preload } from 'swr';
import useSWRMutation from 'swr/mutation';
import useSWRInfinite from 'swr/infinite';
import axios from 'axios';

const fetcher = (url) => axios.get(url).then(r => r.data);

function App({ fallback }) {
  return (
    <SWRConfig value={{ fetcher, fallback, suspense: true }}>
      <Dashboard />
    </SWRConfig>
  );
}

function Dashboard() {
  const { data: user } = useSWR<User>('/api/user', fetcher, {
    revalidateOnFocus: false,
    fallbackData: defaultUser,
  });

  const { data: projects, size, setSize } = useSWRInfinite(
    (i, prev) => prev && !prev.length ? null : `/api/projects?page=${i}`,
    fetcher
  );

  const { trigger } = useSWRMutation('/api/user', updateUser, {
    optimisticData: (current) => ({ ...current, name: 'Updated' }),
    rollbackOnError: true,
    populateCache: true,
  });

  return <div>{user?.name}</div>;
}

preload('/api/user', fetcher);
mutate('/api/user');
"""
        result = parser.parse(content, "dashboard.tsx")

        # Framework detection
        assert 'swr' in result.detected_frameworks
        assert 'swr-mutation' in result.detected_frameworks
        assert 'swr-infinite' in result.detected_frameworks
        assert 'axios' in result.detected_frameworks

        # Feature detection
        assert 'use_swr' in result.detected_features
        assert 'use_swr_mutation' in result.detected_features
        assert 'use_swr_infinite' in result.detected_features
        assert 'swr_config' in result.detected_features
        assert 'suspense' in result.detected_features
        assert 'preload' in result.detected_features
        assert 'fallback_data' in result.detected_features
        assert 'optimistic_data' in result.detected_features

        # Version
        assert result.swr_version == "v2"

        # Hooks (should have at least the useSWR calls)
        assert len(result.hooks) > 0

        # Infinite hooks
        assert len(result.infinite_hooks) > 0

        # Mutation hooks
        assert len(result.mutation_hooks) > 0

        # Configs
        assert len(result.configs) > 0

        # Preloads
        assert len(result.preloads) > 0

        # Imports
        assert len(result.imports) > 0

    def test_parse_error_resilience(self, parser):
        """Parser should not crash on malformed content."""
        content = """
useSWR('/api' fetcher {});
<SWRConfig
const { = useSWRMutation(
"""
        result = parser.parse(content, "malformed.tsx")
        assert isinstance(result, SWRParseResult)

    def test_parse_empty_file(self, parser):
        """Parser handles empty content gracefully."""
        result = parser.parse("", "empty.tsx")
        assert isinstance(result, SWRParseResult)
        assert result.hooks == []
        assert result.mutation_hooks == []
        assert result.configs == []

    def test_parse_no_swr_content(self, parser):
        """Parser handles non-SWR React code."""
        content = """
import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
"""
        result = parser.parse(content, "counter.tsx")
        assert isinstance(result, SWRParseResult)
        assert result.hooks == []

    # ── Version Compare ────────────────────────────────────────────

    def test_version_compare(self):
        assert EnhancedSWRParser._version_compare('v2', 'v1') > 0
        assert EnhancedSWRParser._version_compare('v1', 'v2') < 0
        assert EnhancedSWRParser._version_compare('v1', 'v1') == 0
        assert EnhancedSWRParser._version_compare('v0', 'v2') < 0
        assert EnhancedSWRParser._version_compare('', 'v0') < 0


# ═══════════════════════════════════════════════════════════════════
# Middleware + Real-time patterns (v2)
# ═══════════════════════════════════════════════════════════════════

class TestSWRAdvancedPatterns:
    """Tests for advanced SWR patterns."""

    def test_websocket_subscription(self, parser):
        content = """
import useSWRSubscription from 'swr/subscription';

function PriceTracker() {
  const { data: price } = useSWRSubscription('wss://prices', (key, { next }) => {
    const ws = new WebSocket(key);
    ws.onmessage = (e) => next(null, JSON.parse(e.data));
    ws.onerror = (e) => next(e.error);
    return () => ws.close();
  });
  return <span>${price}</span>;
}
"""
        result = parser.parse(content, "prices.tsx")
        assert result.swr_version == "v2"
        assert 'swr-subscription' in result.detected_frameworks

    def test_nextjs_ssr_integration(self, parser):
        content = """
import useSWR, { SWRConfig } from 'swr';
import { GetServerSideProps } from 'next';

export const getServerSideProps: GetServerSideProps = async () => {
  const data = await fetchUser();
  return { props: { fallback: { '/api/user': data } } };
};

function Page({ fallback }) {
  return (
    <SWRConfig value={{ fallback }}>
      <UserProfile />
    </SWRConfig>
  );
}

function UserProfile() {
  const { data } = useSWR('/api/user');
  return <div>{data?.name}</div>;
}
"""
        result = parser.parse(content, "page.tsx")
        assert 'next' in result.detected_frameworks
        assert 'swr' in result.detected_frameworks

    def test_react_native_detection(self, parser):
        content = """
import useSWR from 'swr';
import { View, Text } from 'react-native';

function UserScreen() {
  const { data } = useSWR('/api/user', fetcher);
  return <View><Text>{data?.name}</Text></View>;
}
"""
        result = parser.parse(content, "UserScreen.tsx")
        assert 'react-native' in result.detected_frameworks

    def test_custom_cache_provider(self, parser):
        content = """
import { SWRConfig } from 'swr';

function localStorageProvider() {
  const map = new Map(JSON.parse(localStorage.getItem('swr-cache') || '[]'));
  window.addEventListener('beforeunload', () => {
    localStorage.setItem('swr-cache', JSON.stringify(Array.from(map.entries())));
  });
  return map;
}

<SWRConfig value={{ provider: localStorageProvider }}>
  <App />
</SWRConfig>
"""
        result = parser.parse(content, "app.tsx")
        assert len(result.configs) > 0
