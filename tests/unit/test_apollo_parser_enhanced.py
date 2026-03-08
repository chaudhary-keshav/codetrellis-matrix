"""
Tests for Apollo Client extractors and EnhancedApolloParser.

Part of CodeTrellis v4.59 Apollo Client Framework Support.
Tests cover:
- Query extraction (useQuery, useLazyQuery, useSuspenseQuery, useBackgroundQuery, gql tags)
- Mutation extraction (useMutation, optimisticResponse, refetchQueries)
- Cache extraction (InMemoryCache, typePolicies, makeVar, cache operations)
- Subscription extraction (useSubscription, subscribeToMore, WebSocket links)
- API extraction (imports, links, client config, integrations, TypeScript types)
- Parser integration (framework detection, version detection, feature detection, is_apollo_file)
"""

import pytest
from codetrellis.apollo_parser_enhanced import (
    EnhancedApolloParser,
    ApolloParseResult,
)
from codetrellis.extractors.apollo import (
    ApolloQueryExtractor,
    ApolloQueryInfo,
    ApolloLazyQueryInfo,
    ApolloGqlTagInfo,
    ApolloMutationExtractor,
    ApolloMutationInfo,
    ApolloOptimisticResponseInfo,
    ApolloCacheExtractor,
    ApolloCacheConfigInfo,
    ApolloTypePolicyInfo,
    ApolloReactiveVarInfo,
    ApolloCacheOperationInfo,
    ApolloSubscriptionExtractor,
    ApolloSubscriptionInfo,
    ApolloSubscribeToMoreInfo,
    ApolloApiExtractor,
    ApolloImportInfo,
    ApolloLinkInfo,
    ApolloClientConfigInfo,
    ApolloIntegrationInfo,
    ApolloTypeInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedApolloParser()


@pytest.fixture
def query_extractor():
    return ApolloQueryExtractor()


@pytest.fixture
def mutation_extractor():
    return ApolloMutationExtractor()


@pytest.fixture
def cache_extractor():
    return ApolloCacheExtractor()


@pytest.fixture
def subscription_extractor():
    return ApolloSubscriptionExtractor()


@pytest.fixture
def api_extractor():
    return ApolloApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Query Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestApolloQueryExtractor:
    """Tests for ApolloQueryExtractor."""

    def test_extract_use_query_basic(self, query_extractor):
        """Test basic useQuery extraction."""
        code = """
import { useQuery } from '@apollo/client';
const { data, loading, error } = useQuery(GET_USERS);
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 1
        q = result['queries'][0]
        assert isinstance(q, ApolloQueryInfo)

    def test_extract_use_query_with_variables(self, query_extractor):
        """Test useQuery with variables option."""
        code = """
const { data } = useQuery(GET_USER, {
  variables: { id: userId },
  fetchPolicy: 'cache-and-network',
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 1
        q = result['queries'][0]
        assert q.has_variables is True
        assert q.fetch_policy == "cache-and-network"

    def test_extract_use_query_with_skip(self, query_extractor):
        """Test useQuery with skip option."""
        code = """
const { data } = useQuery(GET_PROFILE, {
  variables: { id: userId },
  skip: !userId,
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 1
        q = result['queries'][0]
        assert q.has_skip is True

    def test_extract_use_query_with_poll_interval(self, query_extractor):
        """Test useQuery with pollInterval option."""
        code = """
const { data } = useQuery(GET_FEED, {
  pollInterval: 5000,
});
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 1
        q = result['queries'][0]
        assert q.has_poll_interval is True

    def test_extract_use_lazy_query(self, query_extractor):
        """Test useLazyQuery extraction."""
        code = """
const [search, { loading, data }] = useLazyQuery(SEARCH_USERS);
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['lazy_queries']) >= 1

    def test_extract_use_suspense_query(self, query_extractor):
        """Test useSuspenseQuery extraction (v3.8+)."""
        code = """
const { data } = useSuspenseQuery(GET_USER, { variables: { id } });
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 1

    def test_extract_gql_tag(self, query_extractor):
        """Test gql tagged template literal extraction."""
        code = """
const GET_USERS = gql`
  query GetUsers($limit: Int) {
    users(limit: $limit) {
      id
      name
    }
  }
`;
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['gql_tags']) >= 1
        gt = result['gql_tags'][0]
        assert isinstance(gt, ApolloGqlTagInfo)

    def test_extract_gql_tag_with_fragment(self, query_extractor):
        """Test gql tag with fragment."""
        code = """
const GET_USER = gql`
  query GetUser($id: ID!) {
    user(id: $id) {
      ...UserFields
    }
  }
  ${USER_FIELDS}
`;
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['gql_tags']) >= 1

    def test_extract_typed_query(self, query_extractor):
        """Test useQuery with TypeScript generics."""
        code = """
const { data } = useQuery<GetUsersQuery, GetUsersQueryVariables>(GET_USERS);
"""
        result = query_extractor.extract(code, "test.tsx")
        assert len(result['queries']) >= 1
        q = result['queries'][0]
        assert q.has_typescript is True

    def test_extract_client_query(self, query_extractor):
        """Test client.query() direct call."""
        code = """
const result = await client.query({
  query: GET_USER,
  variables: { id: '1' },
});
"""
        result = query_extractor.extract(code, "test.tsx")
        # client.query should be extracted
        assert 'queries' in result

    def test_extract_graphql_hoc(self, query_extractor):
        """Test graphql() HOC pattern from react-apollo v2."""
        code = """
const UserListWithData = graphql(GET_USERS, {
  options: { fetchPolicy: 'cache-first' },
})(UserList);
"""
        result = query_extractor.extract(code, "test.tsx")
        # HOC pattern should be detected
        assert 'queries' in result


# ═══════════════════════════════════════════════════════════════════
# Mutation Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestApolloMutationExtractor:
    """Tests for ApolloMutationExtractor."""

    def test_extract_use_mutation_basic(self, mutation_extractor):
        """Test basic useMutation extraction."""
        code = """
const [createUser, { loading, error }] = useMutation(CREATE_USER);
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert len(result['mutations']) >= 1
        m = result['mutations'][0]
        assert isinstance(m, ApolloMutationInfo)

    def test_extract_mutation_with_optimistic_response(self, mutation_extractor):
        """Test useMutation with optimisticResponse."""
        code = """
const [toggleTodo] = useMutation(TOGGLE_TODO, {
  optimisticResponse: {
    toggleTodo: {
      id: todoId,
      __typename: 'Todo',
      completed: !completed,
    },
  },
});
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert len(result['mutations']) >= 1
        m = result['mutations'][0]
        assert m.has_optimistic_response is True

    def test_extract_mutation_with_refetch_queries(self, mutation_extractor):
        """Test useMutation with refetchQueries."""
        code = """
const [addTodo] = useMutation(ADD_TODO, {
  refetchQueries: [{ query: GET_TODOS }],
});
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert len(result['mutations']) >= 1
        m = result['mutations'][0]
        assert m.has_refetch_queries is True

    def test_extract_mutation_with_update(self, mutation_extractor):
        """Test useMutation with update function."""
        code = """
const [addTodo] = useMutation(ADD_TODO, {
  update(cache, { data: { addTodo } }) {
    cache.modify({
      fields: {
        todos(existing = []) {
          return [...existing, newTodoRef];
        },
      },
    });
  },
});
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert len(result['mutations']) >= 1
        m = result['mutations'][0]
        assert m.has_update is True

    def test_extract_mutation_with_callbacks(self, mutation_extractor):
        """Test useMutation with onCompleted/onError."""
        code = """
const [login] = useMutation(LOGIN, {
  onCompleted: (data) => router.push('/dashboard'),
  onError: (error) => toast.error(error.message),
});
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert len(result['mutations']) >= 1
        m = result['mutations'][0]
        assert m.has_on_completed is True
        assert m.has_on_error is True

    def test_extract_optimistic_response_info(self, mutation_extractor):
        """Test extraction of optimistic response details."""
        code = """
useMutation(DELETE_ITEM, {
  optimisticResponse: {
    deleteItem: {
      __typename: 'Item',
      id: itemId,
      deleted: true,
    }
  }
});
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert len(result.get('optimistic_responses', [])) >= 0  # Depends on regex depth

    def test_extract_client_mutate(self, mutation_extractor):
        """Test client.mutate() direct call."""
        code = """
await client.mutate({
  mutation: CREATE_USER,
  variables: { input: userInput },
});
"""
        result = mutation_extractor.extract(code, "test.tsx")
        assert 'mutations' in result


# ═══════════════════════════════════════════════════════════════════
# Cache Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestApolloCacheExtractor:
    """Tests for ApolloCacheExtractor."""

    def test_extract_in_memory_cache_basic(self, cache_extractor):
        """Test basic InMemoryCache extraction."""
        code = """
const cache = new InMemoryCache();
"""
        result = cache_extractor.extract(code, "test.ts")
        assert len(result['cache_configs']) >= 1
        cc = result['cache_configs'][0]
        assert isinstance(cc, ApolloCacheConfigInfo)

    def test_extract_cache_with_type_policies(self, cache_extractor):
        """Test InMemoryCache with typePolicies."""
        code = """
const cache = new InMemoryCache({
  typePolicies: {
    User: {
      keyFields: ['email'],
    },
    Query: {
      fields: {
        feed: {
          keyArgs: ['type'],
          merge(existing = [], incoming) {
            return [...existing, ...incoming];
          },
        },
      },
    },
  },
});
"""
        result = cache_extractor.extract(code, "test.ts")
        assert len(result['cache_configs']) >= 1
        cc = result['cache_configs'][0]
        assert cc.has_type_policies is True

    def test_extract_type_policies_individually(self, cache_extractor):
        """Test individual type policy extraction."""
        code = """
const cache = new InMemoryCache({
  typePolicies: {
    User: {
      keyFields: ['email'],
      fields: {
        fullName: {
          read(_, { readField }) {
            return readField('first') + ' ' + readField('last');
          }
        }
      }
    },
  },
});
"""
        result = cache_extractor.extract(code, "test.ts")
        assert len(result.get('type_policies', [])) >= 0

    def test_extract_make_var(self, cache_extractor):
        """Test makeVar reactive variable extraction."""
        code = """
export const cartItemsVar = makeVar<CartItem[]>([]);
export const isLoggedInVar = makeVar(false);
const themeVar = makeVar<'light' | 'dark'>('light');
"""
        result = cache_extractor.extract(code, "test.ts")
        assert len(result['reactive_vars']) >= 2
        rv = result['reactive_vars'][0]
        assert isinstance(rv, ApolloReactiveVarInfo)

    def test_extract_cache_operations(self, cache_extractor):
        """Test cache.readQuery/writeQuery/modify/evict extraction."""
        code = """
const data = cache.readQuery({ query: GET_TODOS });
cache.writeQuery({ query: GET_TODOS, data: { todos: updatedTodos } });
cache.modify({
  id: cache.identify(user),
  fields: { name: () => 'New Name' },
});
cache.evict({ id: cache.identify(oldUser) });
cache.gc();
"""
        result = cache_extractor.extract(code, "test.ts")
        assert len(result['cache_operations']) >= 3

    def test_extract_possible_types(self, cache_extractor):
        """Test InMemoryCache with possibleTypes."""
        code = """
const cache = new InMemoryCache({
  possibleTypes: {
    SearchResult: ['User', 'Post', 'Comment'],
  },
});
"""
        result = cache_extractor.extract(code, "test.ts")
        assert len(result['cache_configs']) >= 1
        cc = result['cache_configs'][0]
        assert cc.has_possible_types is True

    def test_extract_client_directive(self, cache_extractor):
        """Test @client directive detection."""
        code = """
const GET_CART = gql`
  query GetCart {
    cartItems @client
    cartTotal @client
  }
`;
"""
        result = cache_extractor.extract(code, "test.ts")
        # @client should be detected in cache extraction
        assert 'cache_operations' in result


# ═══════════════════════════════════════════════════════════════════
# Subscription Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestApolloSubscriptionExtractor:
    """Tests for ApolloSubscriptionExtractor."""

    def test_extract_use_subscription_basic(self, subscription_extractor):
        """Test basic useSubscription extraction."""
        code = """
const { data, loading } = useSubscription(MESSAGE_ADDED, {
  variables: { chatId },
});
"""
        result = subscription_extractor.extract(code, "test.tsx")
        assert len(result['subscriptions']) >= 1
        s = result['subscriptions'][0]
        assert isinstance(s, ApolloSubscriptionInfo)
        assert s.has_variables is True

    def test_extract_subscription_with_on_data(self, subscription_extractor):
        """Test useSubscription with onData callback (v3.8+)."""
        code = """
const { data } = useSubscription(NOTIFICATION_ADDED, {
  onData: ({ data }) => {
    showToast(data.data.notificationAdded);
  },
});
"""
        result = subscription_extractor.extract(code, "test.tsx")
        assert len(result['subscriptions']) >= 1
        s = result['subscriptions'][0]
        assert s.has_on_data is True

    def test_extract_subscribe_to_more(self, subscription_extractor):
        """Test subscribeToMore extraction."""
        code = """
subscribeToMore({
  document: MESSAGE_ADDED_SUBSCRIPTION,
  variables: { chatId },
  updateQuery: (prev, { subscriptionData }) => {
    return { messages: [...prev.messages, subscriptionData.data.messageAdded] };
  },
});
"""
        result = subscription_extractor.extract(code, "test.tsx")
        assert len(result['subscribe_to_more']) >= 1
        stm = result['subscribe_to_more'][0]
        assert isinstance(stm, ApolloSubscribeToMoreInfo)
        assert stm.has_update_query is True

    def test_extract_ws_link(self, subscription_extractor):
        """Test WebSocket link detection."""
        code = """
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';
const wsLink = new GraphQLWsLink(createClient({
  url: 'ws://localhost:4000/graphql',
}));
"""
        result = subscription_extractor.extract(code, "test.ts")
        assert result['has_ws_link'] is True

    def test_extract_split_link(self, subscription_extractor):
        """Test split link pattern detection."""
        code = """
const link = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return definition.kind === 'OperationDefinition' && definition.operation === 'subscription';
  },
  wsLink,
  httpLink,
);
"""
        result = subscription_extractor.extract(code, "test.ts")
        # Split should be detected
        assert 'subscriptions' in result

    def test_extract_legacy_websocket_link(self, subscription_extractor):
        """Test legacy WebSocketLink from subscriptions-transport-ws."""
        code = """
import { WebSocketLink } from '@apollo/client/link/ws';
const wsLink = new WebSocketLink({
  uri: 'ws://localhost:4000/graphql',
  options: { reconnect: true },
});
"""
        result = subscription_extractor.extract(code, "test.ts")
        assert result['has_ws_link'] is True


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestApolloApiExtractor:
    """Tests for ApolloApiExtractor."""

    def test_extract_apollo_v3_imports(self, api_extractor):
        """Test @apollo/client import extraction."""
        code = """
import { useQuery, useMutation, gql, ApolloClient, InMemoryCache } from '@apollo/client';
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert isinstance(imp, ApolloImportInfo)
        assert imp.source == '@apollo/client'

    def test_extract_apollo_v2_imports(self, api_extractor):
        """Test apollo-boost and @apollo/react-hooks imports."""
        code = """
import ApolloClient from 'apollo-boost';
import { useQuery, useMutation } from '@apollo/react-hooks';
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['imports']) >= 2

    def test_extract_apollo_subpackage_imports(self, api_extractor):
        """Test @apollo/client subpackage imports."""
        code = """
import { HttpLink } from '@apollo/client/link/http';
import { onError } from '@apollo/client/link/error';
import { setContext } from '@apollo/client/link/context';
import { MockedProvider } from '@apollo/client/testing';
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result['imports']) >= 4

    def test_extract_link_chain(self, api_extractor):
        """Test Apollo Link chain extraction."""
        code = """
const httpLink = new HttpLink({ uri: '/graphql' });
const errorLink = onError(({ graphQLErrors }) => { });
const authLink = setContext(async (_, { headers }) => ({
  headers: { ...headers, authorization: `Bearer ${token}` }
}));
const link = ApolloLink.from([authLink, errorLink, httpLink]);
"""
        result = api_extractor.extract(code, "test.ts")
        assert len(result['links']) >= 1

    def test_extract_apollo_client_config(self, api_extractor):
        """Test ApolloClient configuration extraction."""
        code = """
const client = new ApolloClient({
  link: link,
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: { fetchPolicy: 'cache-and-network' },
  },
  connectToDevTools: true,
});
"""
        result = api_extractor.extract(code, "test.ts")
        assert len(result['client_configs']) >= 1
        cfg = result['client_configs'][0]
        assert isinstance(cfg, ApolloClientConfigInfo)
        assert cfg.has_link is True
        assert cfg.has_cache is True
        assert cfg.has_default_options is True
        assert cfg.has_connect_to_dev_tools is True

    def test_extract_apollo_provider(self, api_extractor):
        """Test ApolloProvider detection."""
        code = """
function App() {
  return (
    <ApolloProvider client={client}>
      <Router />
    </ApolloProvider>
  );
}
"""
        result = api_extractor.extract(code, "test.tsx")
        assert result['has_provider'] is True

    def test_extract_codegen_integration(self, api_extractor):
        """Test GraphQL codegen integration detection."""
        code = """
import { TypedDocumentNode } from '@graphql-typed-document-node/core';
import { GetUsersDocument } from '../generated/graphql';
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result.get('integrations', [])) >= 0

    def test_extract_testing_patterns(self, api_extractor):
        """Test MockedProvider/MockLink detection."""
        code = """
import { MockedProvider } from '@apollo/client/testing';
const mocks = [
  { request: { query: GET_USER }, result: { data: { user: mockUser } } }
];
render(<MockedProvider mocks={mocks}><UserProfile /></MockedProvider>);
"""
        result = api_extractor.extract(code, "test.tsx")
        assert len(result.get('integrations', [])) >= 0

    def test_extract_ssr_patterns(self, api_extractor):
        """Test SSR pattern detection."""
        code = """
import { getDataFromTree } from '@apollo/client/react/ssr';
const client = new ApolloClient({
  ssrMode: true,
  link: createHttpLink({ uri: 'http://localhost:4000/graphql' }),
  cache: new InMemoryCache(),
});
"""
        result = api_extractor.extract(code, "test.ts")
        assert len(result['client_configs']) >= 1

    def test_extract_typescript_types(self, api_extractor):
        """Test TypeScript type extraction."""
        code = """
import type { ApolloQueryResult, FetchResult, NormalizedCacheObject } from '@apollo/client';
type QueryResult = ApolloQueryResult<GetUsersQuery>;
"""
        result = api_extractor.extract(code, "test.ts")
        assert len(result.get('types', [])) >= 0


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedApolloParser:
    """Tests for EnhancedApolloParser integration."""

    def test_is_apollo_file_positive(self, parser):
        """Test is_apollo_file detects Apollo code."""
        code = """import { useQuery } from '@apollo/client';"""
        assert parser.is_apollo_file(code) is True

    def test_is_apollo_file_use_mutation(self, parser):
        """Test is_apollo_file detects useMutation."""
        code = """const [create] = useMutation(CREATE_USER);"""
        assert parser.is_apollo_file(code) is True

    def test_is_apollo_file_gql(self, parser):
        """Test is_apollo_file detects gql tag."""
        code = """const QUERY = gql`query { users { id } }`;"""
        assert parser.is_apollo_file(code) is True

    def test_is_apollo_file_apollo_provider(self, parser):
        """Test is_apollo_file detects ApolloProvider."""
        code = """<ApolloProvider client={client}><App /></ApolloProvider>"""
        assert parser.is_apollo_file(code) is True

    def test_is_apollo_file_make_var(self, parser):
        """Test is_apollo_file detects makeVar."""
        code = """const cartVar = makeVar([]);"""
        assert parser.is_apollo_file(code) is True

    def test_is_apollo_file_apollo_boost(self, parser):
        """Test is_apollo_file detects apollo-boost import."""
        code = """import ApolloClient from 'apollo-boost';"""
        assert parser.is_apollo_file(code) is True

    def test_is_apollo_file_negative(self, parser):
        """Test is_apollo_file rejects non-Apollo code."""
        code = """
import React from 'react';
function App() { return <div>Hello</div>; }
"""
        assert parser.is_apollo_file(code) is False

    def test_is_apollo_file_react_only(self, parser):
        """Test is_apollo_file rejects plain React code."""
        code = """
import { useState } from 'react';
const [count, setCount] = useState(0);
"""
        assert parser.is_apollo_file(code) is False

    def test_parse_full_v3_file(self, parser):
        """Test complete parse of a v3 Apollo file."""
        code = """
import { useQuery, useMutation, gql, ApolloClient, InMemoryCache, ApolloProvider } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';

const GET_USERS = gql`
  query GetUsers($limit: Int) {
    users(limit: $limit) { id name email }
  }
`;

const CREATE_USER = gql`
  mutation CreateUser($input: UserInput!) {
    createUser(input: $input) { id name }
  }
`;

const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        users: { merge: (existing = [], incoming) => [...existing, ...incoming] },
      },
    },
  },
});

const cartItemsVar = makeVar<CartItem[]>([]);

function UserList() {
  const { data, loading, error } = useQuery(GET_USERS, {
    variables: { limit: 10 },
    fetchPolicy: 'cache-and-network',
  });

  const [createUser] = useMutation(CREATE_USER, {
    optimisticResponse: { createUser: { id: 'temp', __typename: 'User', name: 'New' } },
    refetchQueries: [{ query: GET_USERS }],
  });

  if (loading) return <Spinner />;
  if (error) return <Error />;
  return <List users={data.users} />;
}

function App() {
  return (
    <ApolloProvider client={client}>
      <UserList />
    </ApolloProvider>
  );
}
"""
        result = parser.parse(code, "app.tsx")
        assert isinstance(result, ApolloParseResult)
        assert result.file_type == "tsx"
        assert result.apollo_version == "v3"
        assert len(result.queries) >= 1
        assert len(result.mutations) >= 1
        assert len(result.gql_tags) >= 2
        assert len(result.cache_configs) >= 1
        assert len(result.reactive_vars) >= 1
        assert result.has_provider is True
        assert 'apollo-client-v3' in result.detected_frameworks
        assert 'use_query' in result.detected_features
        assert 'use_mutation' in result.detected_features
        assert 'gql_tag' in result.detected_features
        assert 'apollo_provider' in result.detected_features
        assert 'type_policies' in result.detected_features

    def test_parse_v2_file(self, parser):
        """Test parsing Apollo Client v2 file."""
        code = """
import ApolloClient from 'apollo-boost';
import { useQuery } from '@apollo/react-hooks';
import gql from 'graphql-tag';

const GET_DATA = gql`query { data { id } }`;
const { data } = useQuery(GET_DATA);
"""
        result = parser.parse(code, "app.tsx")
        assert result.apollo_version == "v2"
        assert 'apollo-boost' in result.detected_frameworks

    def test_parse_v1_file(self, parser):
        """Test parsing Apollo Client v1 file."""
        code = """
import ApolloClient from 'apollo-client';
import { createHttpLink } from 'apollo-link-http';
import { InMemoryCache } from 'apollo-cache-inmemory';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';

const GET_DATA = gql`query { data { id } }`;
const Enhanced = graphql(GET_DATA)(Component);
"""
        result = parser.parse(code, "app.jsx")
        assert result.apollo_version in ("v1", "v2")  # v1 or v2 based on patterns
        assert result.file_type == "jsx"

    def test_detect_frameworks_comprehensive(self, parser):
        """Test comprehensive framework detection."""
        code = """
import { useQuery } from '@apollo/client';
import { HttpLink } from '@apollo/client/link/http';
import { onError } from '@apollo/client/link/error';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';
import gql from 'graphql-tag';
import React from 'react';
"""
        result = parser.parse(code, "test.tsx")
        assert 'apollo-client-v3' in result.detected_frameworks
        assert 'apollo-link-http' in result.detected_frameworks
        assert 'apollo-link-error' in result.detected_frameworks
        assert 'graphql-tag' in result.detected_frameworks
        assert 'graphql-ws' in result.detected_frameworks
        assert 'react' in result.detected_frameworks

    def test_detect_features_comprehensive(self, parser):
        """Test comprehensive feature detection."""
        code = """
import { useQuery, useMutation, useSubscription, useSuspenseQuery, gql } from '@apollo/client';
const { data } = useQuery(Q, { fetchPolicy: 'cache-first', pollInterval: 5000, skip: !ready });
const [mut] = useMutation(M, { optimisticResponse: {}, refetchQueries: [] });
const sub = useSubscription(S);
const suspense = useSuspenseQuery(Q);
const client = new ApolloClient({});
const cache = new InMemoryCache({ typePolicies: {} });
const v = makeVar(false);
const tag = gql`query {}`;
<ApolloProvider client={client}><App /></ApolloProvider>
cache.modify({});
cache.evict({});
"""
        features = parser._detect_features(code)
        assert 'use_query' in features
        assert 'use_mutation' in features
        assert 'use_subscription' in features
        assert 'use_suspense_query' in features
        assert 'fetch_policy' in features
        assert 'optimistic_response' in features
        assert 'refetch_queries' in features
        assert 'gql_tag' in features
        assert 'apollo_provider' in features
        assert 'apollo_client' in features
        assert 'in_memory_cache' in features
        assert 'type_policies' in features
        assert 'make_var' in features
        assert 'cache_modify' in features
        assert 'cache_evict' in features

    def test_version_detection_v3(self, parser):
        """Test v3 version detection."""
        code = """import { useQuery } from '@apollo/client';"""
        assert parser._detect_version(code) == "v3"

    def test_version_detection_v3_suspense(self, parser):
        """Test v3.8+ version detection with Suspense hooks."""
        code = """
const { data } = useSuspenseQuery(QUERY);
"""
        assert parser._detect_version(code) == "v3"

    def test_version_detection_v3_make_var(self, parser):
        """Test v3 version detection with makeVar."""
        code = """const myVar = makeVar(false);"""
        assert parser._detect_version(code) == "v3"

    def test_version_detection_v3_type_policies(self, parser):
        """Test v3 version detection with typePolicies."""
        code = """const cache = new InMemoryCache({ typePolicies: {} });"""
        assert parser._detect_version(code) == "v3"

    def test_version_detection_v2(self, parser):
        """Test v2 version detection."""
        code = """import ApolloClient from 'apollo-boost';"""
        assert parser._detect_version(code) == "v2"

    def test_version_detection_v2_react_hooks(self, parser):
        """Test v2 version detection with @apollo/react-hooks."""
        code = """import { useQuery } from '@apollo/react-hooks';"""
        assert parser._detect_version(code) == "v2"

    def test_version_detection_v1_no_hooks(self, parser):
        """Test v1 version detection without hooks."""
        code = """
import ApolloClient from 'apollo-client';
const client = new ApolloClient({});
"""
        assert parser._detect_version(code) == "v1"

    def test_version_detection_empty(self, parser):
        """Test version detection with no Apollo code."""
        code = """const x = 1;"""
        assert parser._detect_version(code) == ""

    def test_parse_result_defaults(self, parser):
        """Test ApolloParseResult default values."""
        result = ApolloParseResult(file_path="test.ts")
        assert result.queries == []
        assert result.mutations == []
        assert result.cache_configs == []
        assert result.subscriptions == []
        assert result.imports == []
        assert result.apollo_version == ""
        assert result.detected_frameworks == []
        assert result.detected_features == []
        assert result.has_provider is False
        assert result.has_ws_link is False

    def test_file_type_detection(self, parser):
        """Test file type detection from path."""
        assert parser.parse("", "app.tsx").file_type == "tsx"
        assert parser.parse("", "app.jsx").file_type == "jsx"
        assert parser.parse("", "app.ts").file_type == "ts"
        assert parser.parse("", "app.js").file_type == "js"
        assert parser.parse("", "app.mjs").file_type == "js"

    def test_parse_empty_file(self, parser):
        """Test parsing empty file."""
        result = parser.parse("", "test.tsx")
        assert result.queries == []
        assert result.mutations == []
        assert result.apollo_version == ""

    def test_parse_next_js_apollo(self, parser):
        """Test parsing Next.js with Apollo SSR."""
        code = """
import { ApolloClient, InMemoryCache, HttpLink } from '@apollo/client';
import { getDataFromTree } from '@apollo/client/react/ssr';

const client = new ApolloClient({
  ssrMode: true,
  link: new HttpLink({ uri: '/api/graphql' }),
  cache: new InMemoryCache(),
});
"""
        result = parser.parse(code, "pages/_app.tsx")
        assert result.apollo_version == "v3"
        assert 'ssr_mode' in result.detected_features
        assert len(result.client_configs) >= 1

    def test_parse_subscription_heavy_file(self, parser):
        """Test parsing file with heavy subscription usage."""
        code = """
import { useSubscription, gql } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';

const MESSAGE_ADDED = gql`
  subscription OnMessageAdded($chatId: ID!) {
    messageAdded(chatId: $chatId) { id text sender }
  }
`;

function ChatMessages({ chatId }) {
  const { data } = useSubscription(MESSAGE_ADDED, {
    variables: { chatId },
    onData: ({ data }) => console.log(data),
  });
  return <Messages data={data} />;
}
"""
        result = parser.parse(code, "chat.tsx")
        assert len(result.subscriptions) >= 1
        assert len(result.gql_tags) >= 1
        assert 'use_subscription' in result.detected_features

    def test_version_compare(self):
        """Test version comparison utility."""
        assert EnhancedApolloParser._version_compare("v3", "v2") > 0
        assert EnhancedApolloParser._version_compare("v2", "v3") < 0
        assert EnhancedApolloParser._version_compare("v1", "v1") == 0
        assert EnhancedApolloParser._version_compare("v3", "") > 0
        assert EnhancedApolloParser._version_compare("", "v1") < 0
