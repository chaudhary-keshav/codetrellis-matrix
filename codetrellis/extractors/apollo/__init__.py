"""
CodeTrellis Apollo Client Extractors Module v1.0

Provides comprehensive extractors for Apollo Client GraphQL constructs:

Query Extractor:
- ApolloQueryExtractor: useQuery(), useLazyQuery(), useSuspenseQuery(),
                         useBackgroundQuery(), useReadQuery(), client.query(),
                         client.watchQuery(), graphql() HOC, gql tagged templates,
                         query variables, fetchPolicy, pollInterval, skip,
                         error policies, TypeScript generics

Mutation Extractor:
- ApolloMutationExtractor: useMutation(), client.mutate(), optimisticResponse,
                            update function (cache.readQuery/writeQuery),
                            refetchQueries, awaitRefetchQueries, onCompleted,
                            onError, errorPolicy, context headers

Cache Extractor:
- ApolloCacheExtractor: InMemoryCache, typePolicies, field policies (read/merge),
                         keyFields, cache.readQuery/writeQuery/readFragment/
                         writeFragment, cache.modify, cache.evict, cache.gc(),
                         makeVar() reactive variables, possibleTypes (unions/interfaces),
                         fetchPolicy options

Subscription Extractor:
- ApolloSubscriptionExtractor: useSubscription(), client.subscribe(),
                                WebSocketLink, GraphQLWsLink, split() link routing,
                                subscribeToMore(), onSubscriptionData/onData (v3.8+),
                                subscription variables, fetchPolicy

API Extractor:
- ApolloApiExtractor: ApolloClient constructor, ApolloProvider, HttpLink,
                       ApolloLink (from/split/concat), ErrorLink (onError),
                       RetryLink, RestLink, BatchHttpLink, SchemaLink,
                       PersistedQueryLink, @apollo/client imports, apollo-boost,
                       @apollo/react-hooks (v2), graphql-tag, @graphql-codegen,
                       TypeScript types, version detection (v1, v2, v3)

Part of CodeTrellis v4.59 - Apollo Client Framework Support
"""

from .query_extractor import (
    ApolloQueryExtractor,
    ApolloQueryInfo,
    ApolloLazyQueryInfo,
    ApolloGqlTagInfo,
)
from .mutation_extractor import (
    ApolloMutationExtractor,
    ApolloMutationInfo,
    ApolloOptimisticResponseInfo,
)
from .cache_extractor import (
    ApolloCacheExtractor,
    ApolloCacheConfigInfo,
    ApolloTypePolicyInfo,
    ApolloReactiveVarInfo,
    ApolloCacheOperationInfo,
)
from .subscription_extractor import (
    ApolloSubscriptionExtractor,
    ApolloSubscriptionInfo,
    ApolloSubscribeToMoreInfo,
)
from .api_extractor import (
    ApolloApiExtractor,
    ApolloImportInfo,
    ApolloLinkInfo,
    ApolloClientConfigInfo,
    ApolloIntegrationInfo,
    ApolloTypeInfo,
)

__all__ = [
    # Query
    "ApolloQueryExtractor",
    "ApolloQueryInfo",
    "ApolloLazyQueryInfo",
    "ApolloGqlTagInfo",
    # Mutation
    "ApolloMutationExtractor",
    "ApolloMutationInfo",
    "ApolloOptimisticResponseInfo",
    # Cache
    "ApolloCacheExtractor",
    "ApolloCacheConfigInfo",
    "ApolloTypePolicyInfo",
    "ApolloReactiveVarInfo",
    "ApolloCacheOperationInfo",
    # Subscription
    "ApolloSubscriptionExtractor",
    "ApolloSubscriptionInfo",
    "ApolloSubscribeToMoreInfo",
    # API
    "ApolloApiExtractor",
    "ApolloImportInfo",
    "ApolloLinkInfo",
    "ApolloClientConfigInfo",
    "ApolloIntegrationInfo",
    "ApolloTypeInfo",
]
