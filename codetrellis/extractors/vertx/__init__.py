"""
CodeTrellis Vert.x Extractors Module v1.0

Provides comprehensive extractors for Vert.x framework constructs:

- VertxVerticleExtractor: Verticle definitions, deployment, worker verticles
- VertxRouteExtractor: HTTP routes, Router, sub-routers, handlers, middleware
- VertxEventBusExtractor: Event bus consumers, publishers, request-reply, codecs
- VertxDataExtractor: SQL clients, Mongo client, Redis client, reactive drivers
- VertxApiExtractor: WebSocket handlers, auth providers, cluster, service proxy

Part of CodeTrellis v4.95 - Vert.x Framework Support
"""

from .verticle_extractor import (
    VertxVerticleExtractor,
    VertxVerticleInfo,
    VertxDeploymentInfo,
)
from .route_extractor import (
    VertxRouteExtractor,
    VertxRouteInfo,
    VertxHandlerInfo,
    VertxSubRouterInfo,
)
from .eventbus_extractor import (
    VertxEventBusExtractor,
    VertxEventBusConsumerInfo,
    VertxEventBusPublisherInfo,
    VertxCodecInfo,
)
from .data_extractor import (
    VertxDataExtractor,
    VertxSQLClientInfo,
    VertxMongoClientInfo,
    VertxRedisClientInfo,
)
from .api_extractor import (
    VertxApiExtractor,
    VertxWebSocketInfo,
    VertxAuthProviderInfo,
    VertxClusterInfo,
    VertxServiceProxyInfo,
)

__all__ = [
    'VertxVerticleExtractor', 'VertxVerticleInfo', 'VertxDeploymentInfo',
    'VertxRouteExtractor', 'VertxRouteInfo', 'VertxHandlerInfo', 'VertxSubRouterInfo',
    'VertxEventBusExtractor', 'VertxEventBusConsumerInfo', 'VertxEventBusPublisherInfo', 'VertxCodecInfo',
    'VertxDataExtractor', 'VertxSQLClientInfo', 'VertxMongoClientInfo', 'VertxRedisClientInfo',
    'VertxApiExtractor', 'VertxWebSocketInfo', 'VertxAuthProviderInfo', 'VertxClusterInfo', 'VertxServiceProxyInfo',
]
