"""
Akka extractors for CodeTrellis.

Provides specialized extractors for Akka toolkit:
- Actor: Classic/Typed actors, behaviors, supervision, lifecycle
- Stream: Akka Streams (Source, Flow, Sink, Graph DSL)
- HTTP: Akka HTTP routes, directives, marshalling
- Cluster: Cluster sharding, singleton, distributed pub/sub, CRDT
- Persistence: Event sourcing, durable state, snapshots, projections
"""

from .actor_extractor import (
    AkkaActorExtractor,
    AkkaActorInfo,
    AkkaMessageInfo,
    AkkaSupervisionInfo,
)
from .stream_extractor import (
    AkkaStreamExtractor,
    AkkaStreamStageInfo,
    AkkaStreamGraphInfo,
)
from .http_extractor import (
    AkkaHttpExtractor,
    AkkaHttpRouteInfo,
    AkkaHttpDirectiveInfo,
)
from .cluster_extractor import (
    AkkaClusterExtractor,
    AkkaClusterShardingInfo,
    AkkaClusterSingletonInfo,
    AkkaClusterPubSubInfo,
)
from .persistence_extractor import (
    AkkaPersistenceExtractor,
    AkkaPersistenceActorInfo,
    AkkaSnapshotInfo,
    AkkaProjectionInfo,
)

__all__ = [
    # Actor
    'AkkaActorExtractor', 'AkkaActorInfo', 'AkkaMessageInfo', 'AkkaSupervisionInfo',
    # Stream
    'AkkaStreamExtractor', 'AkkaStreamStageInfo', 'AkkaStreamGraphInfo',
    # HTTP
    'AkkaHttpExtractor', 'AkkaHttpRouteInfo', 'AkkaHttpDirectiveInfo',
    # Cluster
    'AkkaClusterExtractor', 'AkkaClusterShardingInfo',
    'AkkaClusterSingletonInfo', 'AkkaClusterPubSubInfo',
    # Persistence
    'AkkaPersistenceExtractor', 'AkkaPersistenceActorInfo',
    'AkkaSnapshotInfo', 'AkkaProjectionInfo',
]
