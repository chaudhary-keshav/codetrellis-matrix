"""
Apollo Client API Extractor for CodeTrellis

Extracts Apollo Client API usage, imports, links, and integration patterns:
- ApolloClient constructor configuration
- ApolloProvider component usage
- Link chain: HttpLink, BatchHttpLink, ApolloLink, ErrorLink (onError),
  RetryLink, RestLink, SchemaLink, PersistedQueryLink, split/concat/from
- Import patterns from @apollo/client, apollo-boost, @apollo/react-hooks,
  react-apollo, graphql-tag, apollo-link-*, @graphql-codegen/*
- TypeScript types (ApolloClient, ApolloError, DocumentNode, TypedDocumentNode,
  QueryResult, MutationResult, OperationVariables, gql)
- Version detection (v1: apollo-client, v2: apollo-boost/@apollo/react-hooks,
  v3: @apollo/client unified)
- Integrations: React, Next.js, SSR, testing, graphql-codegen, graphql-ws

Supports:
- Apollo Client v1.x (apollo-client, graphql-tag, apollo-link-http)
- Apollo Client v2.x (apollo-boost, @apollo/react-hooks, react-apollo)
- Apollo Client v3.x (@apollo/client, v3.8+ Suspense hooks)

Part of CodeTrellis v4.59 - Apollo Client Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ApolloImportInfo:
    """Information about an Apollo-related import."""
    source: str  # Package name (e.g., '@apollo/client')
    file: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    is_default_import: bool = False
    is_type_import: bool = False


@dataclass
class ApolloLinkInfo:
    """Information about an Apollo Link instantiation."""
    link_type: str  # HttpLink, BatchHttpLink, ErrorLink, etc.
    file: str = ""
    line_number: int = 0
    has_uri: bool = False
    has_credentials: bool = False
    has_headers: bool = False
    has_fetch: bool = False  # Custom fetch implementation
    is_in_chain: bool = False  # Part of ApolloLink.from([...])


@dataclass
class ApolloClientConfigInfo:
    """Information about ApolloClient constructor configuration."""
    file: str = ""
    line_number: int = 0
    has_link: bool = False
    has_cache: bool = False
    has_uri: bool = False  # Direct URI (auto HttpLink)
    has_default_options: bool = False
    has_connect_to_dev_tools: bool = False
    has_name: bool = False
    has_version: bool = False
    has_query_deduplication: bool = False
    has_ssr_mode: bool = False
    has_ssr_forced_resolvers: bool = False
    has_assumed_immutable_results: bool = False
    has_resolvers: bool = False  # Local state resolvers (v2)
    has_type_defs: bool = False  # Local state type defs (v2)


@dataclass
class ApolloIntegrationInfo:
    """Information about an Apollo integration or ecosystem tool."""
    integration_type: str  # e.g., 'graphql-codegen', 'next-ssr', 'testing', 'react-native'
    file: str = ""
    line_number: int = 0
    details: str = ""  # Additional details


@dataclass
class ApolloTypeInfo:
    """Information about Apollo TypeScript type usage."""
    type_name: str  # e.g., 'ApolloClient', 'DocumentNode', 'TypedDocumentNode'
    file: str = ""
    line_number: int = 0
    source: str = ""  # Import source


class ApolloApiExtractor:
    """
    Extracts Apollo Client API patterns from source code.

    Detects:
    - ApolloClient constructor configuration
    - ApolloProvider usage
    - Link chain composition
    - Import patterns for version detection
    - TypeScript type usage
    - Integration patterns (SSR, codegen, testing, etc.)
    """

    # ── Import Patterns ───────────────────────────────────────────

    # ESM import pattern
    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:type\s+)?)\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # Default import
    DEFAULT_IMPORT_PATTERN = re.compile(
        r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # require() pattern
    REQUIRE_PATTERN = re.compile(
        r"(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\(['\"]([^'\"]+)['\"]\)",
        re.MULTILINE
    )

    # Apollo-related package patterns
    APOLLO_PACKAGES = {
        '@apollo/client',
        '@apollo/client/link/http',
        '@apollo/client/link/error',
        '@apollo/client/link/retry',
        '@apollo/client/link/batch-http',
        '@apollo/client/link/schema',
        '@apollo/client/link/persisted-queries',
        '@apollo/client/link/rest',
        '@apollo/client/link/ws',
        '@apollo/client/link/context',
        '@apollo/client/link/remove-typename',
        '@apollo/client/utilities',
        '@apollo/client/testing',
        '@apollo/client/cache',
        '@apollo/client/core',
        '@apollo/client/react',
        '@apollo/client/react/ssr',
        '@apollo/react-hooks',
        '@apollo/react-components',
        '@apollo/react-hoc',
        '@apollo/react-ssr',
        '@apollo/react-testing',
        'apollo-boost',
        'apollo-client',
        'apollo-cache-inmemory',
        'apollo-link',
        'apollo-link-http',
        'apollo-link-error',
        'apollo-link-ws',
        'apollo-link-context',
        'apollo-link-retry',
        'apollo-link-rest',
        'apollo-link-batch-http',
        'apollo-link-persisted-queries',
        'apollo-link-state',
        'apollo-utilities',
        'react-apollo',
        'graphql-tag',
        'graphql',
        'graphql-ws',
        'subscriptions-transport-ws',
        '@graphql-codegen/cli',
        '@graphql-codegen/typescript',
        '@graphql-codegen/typescript-operations',
        '@graphql-codegen/typescript-react-apollo',
        '@graphql-typed-document-node/core',
    }

    # ── Link Patterns ─────────────────────────────────────────────

    LINK_INSTANTIATION_PATTERN = re.compile(
        r'new\s+(HttpLink|BatchHttpLink|RetryLink|RestLink|SchemaLink|'
        r'WebSocketLink|GraphQLWsLink|PersistedQueryLink)\s*\(',
        re.MULTILINE
    )

    # ApolloLink.from / ApolloLink.split / ApolloLink.concat
    APOLLO_LINK_COMPOSITION_PATTERN = re.compile(
        r'ApolloLink\s*\.\s*(from|split|concat)\s*\(',
        re.MULTILINE
    )

    # onError (ErrorLink)
    ON_ERROR_LINK_PATTERN = re.compile(
        r'onError\s*\(\s*(?:\(|function)',
        re.MULTILINE
    )

    # setContext (Context Link)
    SET_CONTEXT_LINK_PATTERN = re.compile(
        r'setContext\s*\(\s*(?:\(|function|async)',
        re.MULTILINE
    )

    # createPersistedQueryLink
    PERSISTED_QUERY_LINK_PATTERN = re.compile(
        r'createPersistedQueryLink\s*\(',
        re.MULTILINE
    )

    # ── ApolloClient Config ───────────────────────────────────────

    APOLLO_CLIENT_PATTERN = re.compile(
        r'new\s+ApolloClient\s*\(\s*\{',
        re.MULTILINE
    )

    # ApolloProvider
    APOLLO_PROVIDER_PATTERN = re.compile(
        r'<ApolloProvider\b',
        re.MULTILINE
    )

    # ── TypeScript Types ──────────────────────────────────────────

    APOLLO_TYPES = {
        'ApolloClient', 'ApolloError', 'ApolloCache', 'ApolloLink',
        'ApolloProvider', 'ApolloConsumer',
        'DocumentNode', 'TypedDocumentNode',
        'QueryResult', 'MutationResult', 'SubscriptionResult',
        'OperationVariables', 'FetchResult', 'FetchPolicy',
        'ErrorPolicy', 'WatchQueryFetchPolicy', 'MutationFetchPolicy',
        'NetworkStatus', 'NormalizedCacheObject', 'InMemoryCache',
        'Reference', 'StoreObject', 'FieldPolicy', 'TypePolicy',
        'ObservableQuery', 'Observable', 'MutationOptions',
        'QueryOptions', 'SubscriptionOptions',
        'MutationHookOptions', 'QueryHookOptions',
        'LazyQueryHookOptions', 'SubscriptionHookOptions',
        'BaseMutationOptions', 'BaseQueryOptions',
        'ReactiveVar', 'makeVar',
        'useQuery', 'useMutation', 'useLazyQuery', 'useSubscription',
        'useSuspenseQuery', 'useBackgroundQuery', 'useReadQuery',
        'useApolloClient', 'useReactiveVar', 'useFragment',
        'gql',
    }

    # ── Integration Patterns ──────────────────────────────────────

    # GraphQL codegen
    CODEGEN_PATTERN = re.compile(
        r"from\s+['\"][^'\"]*generated[^'\"]*['\"]|"
        r"@graphql-codegen|"
        r"\.graphql\.ts['\"]|"
        r"TypedDocumentNode",
        re.MULTILINE
    )

    # Apollo testing utilities
    TESTING_PATTERN = re.compile(
        r'MockedProvider|MockLink|InMemoryCache.*addTypename.*false|'
        r'@apollo/client/testing|@apollo/react-testing',
        re.MULTILINE
    )

    # SSR patterns
    SSR_PATTERN = re.compile(
        r'getDataFromTree|getMarkupFromTree|renderToStringWithData|'
        r'getServerSideProps.*apolloClient|'
        r'ssrMode\s*:\s*true|'
        r'@apollo/client/react/ssr',
        re.MULTILINE
    )

    # React Native
    REACT_NATIVE_PATTERN = re.compile(
        r"from\s+['\"]react-native['\"]",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Apollo API patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'imports', 'links', 'client_configs', 'integrations',
                       'types', 'has_provider' keys
        """
        imports: List[ApolloImportInfo] = []
        links: List[ApolloLinkInfo] = []
        client_configs: List[ApolloClientConfigInfo] = []
        integrations: List[ApolloIntegrationInfo] = []
        types: List[ApolloTypeInfo] = []
        has_provider = False

        # ── Extract imports ────────────────────────────────────────
        for match in self.IMPORT_PATTERN.finditer(content):
            named = match.group(1).strip()
            source = match.group(2).strip()
            if source in self.APOLLO_PACKAGES or source.startswith('@apollo/') or source.startswith('apollo-') or source == 'graphql-tag' or source == 'graphql' or source.startswith('graphql-') or source == 'subscriptions-transport-ws':
                named_imports = [n.strip().split(' as ')[0].strip() for n in named.split(',') if n.strip()]
                line_num = content[:match.start()].count('\n') + 1
                is_type = 'import type' in content[max(0, match.start() - 15):match.start() + 15]
                imports.append(ApolloImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_num,
                    named_imports=named_imports,
                    is_type_import=is_type,
                ))

                # Track TypeScript types
                for ni in named_imports:
                    if ni in self.APOLLO_TYPES:
                        types.append(ApolloTypeInfo(
                            type_name=ni,
                            file=file_path,
                            line_number=line_num,
                            source=source,
                        ))

        # Default imports
        for match in self.DEFAULT_IMPORT_PATTERN.finditer(content):
            name = match.group(1)
            source = match.group(2).strip()
            if source in self.APOLLO_PACKAGES or source.startswith('@apollo/') or source.startswith('apollo-') or source == 'graphql-tag':
                line_num = content[:match.start()].count('\n') + 1
                imports.append(ApolloImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_num,
                    named_imports=[name],
                    is_default_import=True,
                ))

        # require() imports
        for match in self.REQUIRE_PATTERN.finditer(content):
            named = match.group(1) or ""
            default_name = match.group(2) or ""
            source = match.group(3).strip()
            if source in self.APOLLO_PACKAGES or source.startswith('@apollo/') or source.startswith('apollo-') or source == 'graphql-tag':
                line_num = content[:match.start()].count('\n') + 1
                named_imports = []
                if named:
                    named_imports = [n.strip().split(':')[0].strip() for n in named.split(',') if n.strip()]
                elif default_name:
                    named_imports = [default_name]
                imports.append(ApolloImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_num,
                    named_imports=named_imports,
                    is_default_import=bool(default_name),
                ))

        # ── Extract Links ──────────────────────────────────────────
        for match in self.LINK_INSTANTIATION_PATTERN.finditer(content):
            link_type = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.end()
            ctx_end = min(ctx_start + 400, len(content))
            ctx = content[ctx_start:ctx_end]

            links.append(ApolloLinkInfo(
                link_type=link_type,
                file=file_path,
                line_number=line_num,
                has_uri='uri' in ctx[:200],
                has_credentials='credentials' in ctx[:200],
                has_headers='headers' in ctx[:200],
                has_fetch='fetch' in ctx[:200] and ('fetch:' in ctx[:200] or 'fetchOptions' in ctx[:200]),
            ))

        # ErrorLink via onError
        if self.ON_ERROR_LINK_PATTERN.search(content):
            line_num = content[:self.ON_ERROR_LINK_PATTERN.search(content).start()].count('\n') + 1
            links.append(ApolloLinkInfo(
                link_type="ErrorLink",
                file=file_path,
                line_number=line_num,
            ))

        # Context Link via setContext
        if self.SET_CONTEXT_LINK_PATTERN.search(content):
            line_num = content[:self.SET_CONTEXT_LINK_PATTERN.search(content).start()].count('\n') + 1
            links.append(ApolloLinkInfo(
                link_type="ContextLink",
                file=file_path,
                line_number=line_num,
            ))

        # Persisted query link
        if self.PERSISTED_QUERY_LINK_PATTERN.search(content):
            line_num = content[:self.PERSISTED_QUERY_LINK_PATTERN.search(content).start()].count('\n') + 1
            links.append(ApolloLinkInfo(
                link_type="PersistedQueryLink",
                file=file_path,
                line_number=line_num,
            ))

        # Detect link composition
        for match in self.APOLLO_LINK_COMPOSITION_PATTERN.finditer(content):
            # Mark all links as part of chain
            for link in links:
                if link.file == file_path:
                    link.is_in_chain = True

        # ── Extract ApolloClient config ────────────────────────────
        for match in self.APOLLO_CLIENT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.end()
            ctx_end = min(ctx_start + 800, len(content))
            ctx = content[ctx_start:ctx_end]

            client_configs.append(ApolloClientConfigInfo(
                file=file_path,
                line_number=line_num,
                has_link='link' in ctx[:300] and ('link:' in ctx[:300] or 'link :' in ctx[:300]),
                has_cache='cache' in ctx[:300] and ('cache:' in ctx[:300] or 'cache :' in ctx[:300]),
                has_uri='uri' in ctx[:200] and ('uri:' in ctx[:200] or 'uri :' in ctx[:200]),
                has_default_options='defaultOptions' in ctx[:400],
                has_connect_to_dev_tools='connectToDevTools' in ctx[:400],
                has_name='name:' in ctx[:200] or 'name :' in ctx[:200],
                has_version='version:' in ctx[:200] or 'version :' in ctx[:200],
                has_query_deduplication='queryDeduplication' in ctx[:400],
                has_ssr_mode='ssrMode' in ctx[:300],
                has_ssr_forced_resolvers='ssrForcedResolvers' in ctx[:400],
                has_assumed_immutable_results='assumeImmutableResults' in ctx[:400],
                has_resolvers='resolvers' in ctx[:300] and 'resolvers:' in ctx[:300],
                has_type_defs='typeDefs' in ctx[:300] and 'typeDefs:' in ctx[:300],
            ))

        # ── Detect ApolloProvider ──────────────────────────────────
        if self.APOLLO_PROVIDER_PATTERN.search(content):
            has_provider = True

        # ── Detect integrations ────────────────────────────────────
        if self.CODEGEN_PATTERN.search(content):
            line_num = content[:self.CODEGEN_PATTERN.search(content).start()].count('\n') + 1
            integrations.append(ApolloIntegrationInfo(
                integration_type="graphql-codegen",
                file=file_path,
                line_number=line_num,
                details="GraphQL Code Generator integration",
            ))

        if self.TESTING_PATTERN.search(content):
            line_num = content[:self.TESTING_PATTERN.search(content).start()].count('\n') + 1
            integrations.append(ApolloIntegrationInfo(
                integration_type="testing",
                file=file_path,
                line_number=line_num,
                details="Apollo testing utilities (MockedProvider/MockLink)",
            ))

        if self.SSR_PATTERN.search(content):
            line_num = content[:self.SSR_PATTERN.search(content).start()].count('\n') + 1
            integrations.append(ApolloIntegrationInfo(
                integration_type="ssr",
                file=file_path,
                line_number=line_num,
                details="Server-side rendering integration",
            ))

        if self.REACT_NATIVE_PATTERN.search(content):
            integrations.append(ApolloIntegrationInfo(
                integration_type="react-native",
                file=file_path,
                details="React Native integration",
            ))

        return {
            'imports': imports,
            'links': links,
            'client_configs': client_configs,
            'integrations': integrations,
            'types': types,
            'has_provider': has_provider,
        }
