"""
EnhancedApolloParser v1.0 - Comprehensive Apollo Client parser using all extractors.

This parser integrates all Apollo Client extractors to provide complete parsing of
Apollo Client GraphQL usage across React/TypeScript/JavaScript source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting Apollo-specific semantics.

Supports:
- Apollo Client v1.x (apollo-client, graphql-tag, apollo-link-*)
  - Basic queries/mutations via client.query()/client.mutate()
  - graphql() HOC from react-apollo
  - InMemoryCache with dataIdFromObject
  - Apollo Link chain (HttpLink, WebSocketLink)

- Apollo Client v2.x (apollo-boost, @apollo/react-hooks, react-apollo)
  - useQuery/useMutation/useSubscription hooks (@apollo/react-hooks)
  - apollo-boost for zero-config setup
  - IntrospectionFragmentMatcher
  - Local state with resolvers/typeDefs

- Apollo Client v3.x (@apollo/client unified package)
  - All hooks from single @apollo/client import
  - InMemoryCache typePolicies with field policies (read/merge/keyArgs)
  - makeVar() reactive variables
  - cache.modify() / cache.evict() / cache.gc()
  - useSuspenseQuery / useBackgroundQuery / useReadQuery (v3.8+)
  - useFragment (v3.8+)
  - GraphQLWsLink (graphql-ws protocol, replacing subscriptions-transport-ws)
  - Improved TypeScript: TypedDocumentNode
  - @apollo/client/link/* subpackage imports

Key Patterns:
- useQuery(QUERY_DOC, { variables, fetchPolicy, pollInterval, skip })
- useMutation(MUTATION_DOC, { optimisticResponse, update, refetchQueries })
- useSubscription(SUB_DOC, { variables, onData })
- useLazyQuery / useSuspenseQuery / useBackgroundQuery + useReadQuery
- new ApolloClient({ link, cache, uri, defaultOptions })
- new InMemoryCache({ typePolicies, possibleTypes })
- makeVar(initialValue) for reactive variables
- ApolloLink.from([errorLink, httpLink]) link chain
- split(isSubscription, wsLink, httpLink) for transport routing
- gql`query { ... }` tagged template literals

Ecosystem Detection (20+ patterns):
- Core: @apollo/client, apollo-boost, apollo-client, react-apollo
- Links: apollo-link-http, apollo-link-error, apollo-link-ws, apollo-link-rest
- GraphQL: graphql-tag, graphql, graphql-ws, subscriptions-transport-ws
- Codegen: @graphql-codegen/*, @graphql-typed-document-node/core
- Testing: @apollo/client/testing, MockedProvider, MockLink
- SSR: @apollo/client/react/ssr, getDataFromTree
- React: react, react-dom
- Next.js: next (SSR/SSG with Apollo)

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.59 - Apollo Client Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Apollo extractors
from .extractors.apollo import (
    ApolloQueryExtractor, ApolloQueryInfo, ApolloLazyQueryInfo, ApolloGqlTagInfo,
    ApolloMutationExtractor, ApolloMutationInfo, ApolloOptimisticResponseInfo,
    ApolloCacheExtractor, ApolloCacheConfigInfo, ApolloTypePolicyInfo,
    ApolloReactiveVarInfo, ApolloCacheOperationInfo,
    ApolloSubscriptionExtractor, ApolloSubscriptionInfo, ApolloSubscribeToMoreInfo,
    ApolloApiExtractor, ApolloImportInfo, ApolloLinkInfo,
    ApolloClientConfigInfo, ApolloIntegrationInfo, ApolloTypeInfo,
)


@dataclass
class ApolloParseResult:
    """Complete parse result for a file with Apollo Client usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, ts, js

    # Queries
    queries: List[ApolloQueryInfo] = field(default_factory=list)
    lazy_queries: List[ApolloLazyQueryInfo] = field(default_factory=list)
    gql_tags: List[ApolloGqlTagInfo] = field(default_factory=list)

    # Mutations
    mutations: List[ApolloMutationInfo] = field(default_factory=list)
    optimistic_responses: List[ApolloOptimisticResponseInfo] = field(default_factory=list)

    # Cache
    cache_configs: List[ApolloCacheConfigInfo] = field(default_factory=list)
    type_policies: List[ApolloTypePolicyInfo] = field(default_factory=list)
    reactive_vars: List[ApolloReactiveVarInfo] = field(default_factory=list)
    cache_operations: List[ApolloCacheOperationInfo] = field(default_factory=list)

    # Subscriptions
    subscriptions: List[ApolloSubscriptionInfo] = field(default_factory=list)
    subscribe_to_more: List[ApolloSubscribeToMoreInfo] = field(default_factory=list)
    has_ws_link: bool = False
    ws_link_type: str = ""  # WebSocketLink or GraphQLWsLink

    # API
    imports: List[ApolloImportInfo] = field(default_factory=list)
    links: List[ApolloLinkInfo] = field(default_factory=list)
    client_configs: List[ApolloClientConfigInfo] = field(default_factory=list)
    integrations: List[ApolloIntegrationInfo] = field(default_factory=list)
    types: List[ApolloTypeInfo] = field(default_factory=list)
    has_provider: bool = False

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    apollo_version: str = ""  # v1, v2, v3


class EnhancedApolloParser:
    """
    Enhanced Apollo Client parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript/React parser
    when Apollo Client framework is detected. It extracts Apollo-specific
    semantics that the language parsers cannot capture.

    Framework detection supports 20+ Apollo ecosystem libraries across:
    - Core (@apollo/client, apollo-boost, apollo-client, react-apollo)
    - Links (http, error, ws, rest, batch, retry, persisted-queries)
    - GraphQL (graphql-tag, graphql, graphql-ws, subscriptions-transport-ws)
    - Codegen (@graphql-codegen/*)
    - Testing (MockedProvider, MockLink)
    - SSR (getDataFromTree, ssrMode)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # ── Framework Detection Patterns ──────────────────────────────

    FRAMEWORK_PATTERNS = {
        # ── Core Apollo ───────────────────────────────────────────
        'apollo-client-v3': re.compile(
            r"from\s+['\"]@apollo/client['\"/]|require\(['\"]@apollo/client['\"]\)",
            re.MULTILINE
        ),
        'apollo-boost': re.compile(
            r"from\s+['\"]apollo-boost['\"]|require\(['\"]apollo-boost['\"]\)",
            re.MULTILINE
        ),
        'apollo-client-v1': re.compile(
            r"from\s+['\"]apollo-client['\"]|require\(['\"]apollo-client['\"]\)",
            re.MULTILINE
        ),
        'react-apollo': re.compile(
            r"from\s+['\"]react-apollo['\"]|require\(['\"]react-apollo['\"]\)",
            re.MULTILINE
        ),
        'apollo-react-hooks': re.compile(
            r"from\s+['\"]@apollo/react-hooks['\"]",
            re.MULTILINE
        ),

        # ── Links ─────────────────────────────────────────────────
        'apollo-link-http': re.compile(
            r"from\s+['\"](?:@apollo/client/link/http|apollo-link-http)['\"]",
            re.MULTILINE
        ),
        'apollo-link-error': re.compile(
            r"from\s+['\"](?:@apollo/client/link/error|apollo-link-error)['\"]",
            re.MULTILINE
        ),
        'apollo-link-ws': re.compile(
            r"from\s+['\"](?:@apollo/client/link/ws|apollo-link-ws)['\"]",
            re.MULTILINE
        ),
        'apollo-link-rest': re.compile(
            r"from\s+['\"](?:@apollo/client/link/rest|apollo-link-rest)['\"]",
            re.MULTILINE
        ),
        'apollo-link-retry': re.compile(
            r"from\s+['\"](?:@apollo/client/link/retry|apollo-link-retry)['\"]",
            re.MULTILINE
        ),
        'apollo-link-context': re.compile(
            r"from\s+['\"](?:@apollo/client/link/context|apollo-link-context)['\"]",
            re.MULTILINE
        ),
        'apollo-link-persisted-queries': re.compile(
            r"from\s+['\"](?:@apollo/client/link/persisted-queries|apollo-link-persisted-queries)['\"]",
            re.MULTILINE
        ),
        'apollo-link-batch-http': re.compile(
            r"from\s+['\"](?:@apollo/client/link/batch-http|apollo-link-batch-http)['\"]",
            re.MULTILINE
        ),

        # ── GraphQL ───────────────────────────────────────────────
        'graphql-tag': re.compile(
            r"from\s+['\"]graphql-tag['\"]|require\(['\"]graphql-tag['\"]\)",
            re.MULTILINE
        ),
        'graphql': re.compile(
            r"from\s+['\"]graphql['\"]|require\(['\"]graphql['\"]\)",
            re.MULTILINE
        ),
        'graphql-ws': re.compile(
            r"from\s+['\"]graphql-ws['\"]",
            re.MULTILINE
        ),
        'subscriptions-transport-ws': re.compile(
            r"from\s+['\"]subscriptions-transport-ws['\"]",
            re.MULTILINE
        ),

        # ── Codegen ───────────────────────────────────────────────
        'graphql-codegen': re.compile(
            r"from\s+['\"]@graphql-codegen/|@graphql-typed-document-node",
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
        'react-native': re.compile(
            r"from\s+['\"]react-native['\"]",
            re.MULTILINE
        ),
    }

    # ── Feature Detection Patterns ────────────────────────────────

    FEATURE_PATTERNS = {
        'use_query': re.compile(r'useQuery\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_lazy_query': re.compile(r'useLazyQuery\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_mutation': re.compile(r'useMutation\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_subscription': re.compile(r'useSubscription\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_suspense_query': re.compile(r'useSuspenseQuery\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_background_query': re.compile(r'useBackgroundQuery\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_read_query': re.compile(r'useReadQuery\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_fragment': re.compile(r'useFragment\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_reactive_var': re.compile(r'useReactiveVar\s*\(', re.MULTILINE),
        'use_apollo_client': re.compile(r'useApolloClient\s*\(', re.MULTILINE),
        'gql_tag': re.compile(r'gql\s*`', re.MULTILINE),
        'apollo_provider': re.compile(r'<ApolloProvider\b', re.MULTILINE),
        'apollo_client': re.compile(r'new\s+ApolloClient\s*\(', re.MULTILINE),
        'in_memory_cache': re.compile(r'new\s+InMemoryCache\s*\(', re.MULTILINE),
        'type_policies': re.compile(r'typePolicies\s*:', re.MULTILINE),
        'make_var': re.compile(r'makeVar\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'optimistic_response': re.compile(r'optimisticResponse\s*:', re.MULTILINE),
        'refetch_queries': re.compile(r'refetchQueries\s*:', re.MULTILINE),
        'fetch_policy': re.compile(r'fetchPolicy\s*:', re.MULTILINE),
        'error_policy': re.compile(r'errorPolicy\s*:', re.MULTILINE),
        'cache_read_write': re.compile(r'cache\.\s*(?:readQuery|writeQuery|readFragment|writeFragment)\s*\(', re.MULTILINE),
        'cache_modify': re.compile(r'cache\.\s*modify\s*\(', re.MULTILINE),
        'cache_evict': re.compile(r'cache\.\s*evict\s*\(', re.MULTILINE),
        'subscribe_to_more': re.compile(r'subscribeToMore\s*\(', re.MULTILINE),
        'on_error_link': re.compile(r'onError\s*\(\s*\(', re.MULTILINE),
        'set_context': re.compile(r'setContext\s*\(', re.MULTILINE),
        'split_link': re.compile(r'(?:ApolloLink\.)?split\s*\(', re.MULTILINE),
        'client_directive': re.compile(r'@client\b', re.MULTILINE),
        'mocked_provider': re.compile(r'MockedProvider|MockLink', re.MULTILINE),
        'ssr_mode': re.compile(r'ssrMode\s*:\s*true', re.MULTILINE),
        'typed_document_node': re.compile(r'TypedDocumentNode', re.MULTILINE),
    }

    def __init__(self) -> None:
        """Initialize all Apollo extractors."""
        self.query_extractor = ApolloQueryExtractor()
        self.mutation_extractor = ApolloMutationExtractor()
        self.cache_extractor = ApolloCacheExtractor()
        self.subscription_extractor = ApolloSubscriptionExtractor()
        self.api_extractor = ApolloApiExtractor()

    def is_apollo_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Apollo Client code.

        Returns True if the file imports from Apollo packages or uses Apollo patterns.
        """
        apollo_indicators = [
            "@apollo/client", "@apollo/react-hooks", "@apollo/react-components",
            "apollo-boost", "apollo-client", "react-apollo",
            "apollo-link", "apollo-cache",
            "from 'graphql-tag'", 'from "graphql-tag"',
            "useQuery(", "useMutation(", "useSubscription(",
            "useLazyQuery(", "useSuspenseQuery(", "useBackgroundQuery(",
            "useReadQuery(", "useFragment(",
            "useApolloClient(", "useReactiveVar(",
            "ApolloProvider", "ApolloClient(",
            "new InMemoryCache(",
            "makeVar(", "makeVar<",
            "gql`",
            "client.query(", "client.mutate(",
            "client.subscribe(",
            "graphql(", "graphql`",
        ]
        return any(ind in content for ind in apollo_indicators)

    def parse(self, content: str, file_path: str = "") -> ApolloParseResult:
        """
        Parse a source file for Apollo Client patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            ApolloParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = ApolloParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.apollo_version = self._detect_version(content)

        # ── Query extraction ──────────────────────────────────────
        try:
            query_result = self.query_extractor.extract(content, file_path)
            result.queries = query_result.get('queries', [])
            result.lazy_queries = query_result.get('lazy_queries', [])
            result.gql_tags = query_result.get('gql_tags', [])
        except Exception:
            pass

        # ── Mutation extraction ───────────────────────────────────
        try:
            mut_result = self.mutation_extractor.extract(content, file_path)
            result.mutations = mut_result.get('mutations', [])
            result.optimistic_responses = mut_result.get('optimistic_responses', [])
        except Exception:
            pass

        # ── Cache extraction ──────────────────────────────────────
        try:
            cache_result = self.cache_extractor.extract(content, file_path)
            result.cache_configs = cache_result.get('cache_configs', [])
            result.type_policies = cache_result.get('type_policies', [])
            result.reactive_vars = cache_result.get('reactive_vars', [])
            result.cache_operations = cache_result.get('cache_operations', [])
        except Exception:
            pass

        # ── Subscription extraction ───────────────────────────────
        try:
            sub_result = self.subscription_extractor.extract(content, file_path)
            result.subscriptions = sub_result.get('subscriptions', [])
            result.subscribe_to_more = sub_result.get('subscribe_to_more', [])
            result.has_ws_link = sub_result.get('has_ws_link', False)
            result.ws_link_type = sub_result.get('ws_link_type', "")
        except Exception:
            pass

        # ── API extraction ────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.links = api_result.get('links', [])
            result.client_configs = api_result.get('client_configs', [])
            result.integrations = api_result.get('integrations', [])
            result.types = api_result.get('types', [])
            result.has_provider = api_result.get('has_provider', False)
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Apollo ecosystem frameworks are used."""
        detected: List[str] = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Apollo Client features are used."""
        detected: List[str] = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Apollo Client version based on API usage patterns.

        Returns:
            - 'v3' if Apollo Client v3 patterns detected
            - 'v2' if Apollo Client v2 patterns detected
            - 'v1' if Apollo Client v1 patterns detected
            - '' if unknown
        """
        # v3 indicators (features introduced or changed in v3)
        v3_indicators = [
            '@apollo/client',          # Unified package in v3
            'useSuspenseQuery',        # v3.8+
            'useBackgroundQuery',      # v3.8+
            'useReadQuery',            # v3.8+
            'useFragment',             # v3.8+
            'typePolicies',            # v3 cache API
            'makeVar',                 # v3 reactive variables
            'cache.modify',            # v3 cache API
            'cache.evict',             # v3 cache API
            'GraphQLWsLink',           # v3 WebSocket link
            'TypedDocumentNode',       # v3 TypeScript
            'onQueryUpdated',          # v3 mutation option
            'onData',                  # v3.8+ subscription callback
            '@apollo/client/link/',    # v3 subpackage imports
        ]
        if any(ind in content for ind in v3_indicators):
            return "v3"

        # v2 indicators
        v2_indicators = [
            'apollo-boost',            # v2 zero-config package
            '@apollo/react-hooks',     # v2 hooks package
            '@apollo/react-components', # v2 components package
            '@apollo/react-hoc',       # v2 HOC package
            'react-apollo',            # v2 (also v1)
            'IntrospectionFragmentMatcher',  # v2 legacy
            'dataIdFromObject',        # v2 legacy cache
            'apollo-link-state',       # v2 local state
            'cacheRedirects',          # v2 legacy cache
            'onSubscriptionData',      # v2/early v3 (deprecated v3.8+)
        ]
        if any(ind in content for ind in v2_indicators):
            return "v2"

        # v1 indicators
        v1_indicators = [
            'apollo-client',           # v1 package name (without @apollo scope)
            'apollo-cache-inmemory',   # v1 cache package
            'apollo-link-http',        # v1 link package (as standalone)
        ]
        if any(ind in content for ind in v1_indicators):
            # Distinguish v1 vs v2 by checking if v2 patterns are absent
            if 'useQuery' not in content and 'useMutation' not in content:
                return "v1"
            return "v2"

        # If we see Apollo hooks but no version specifics, assume v3 (current)
        if 'useQuery' in content or 'useMutation' in content:
            return "v3"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'v1': 1, 'v2': 2, 'v3': 3}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
