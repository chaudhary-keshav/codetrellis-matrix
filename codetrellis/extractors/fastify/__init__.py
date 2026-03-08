"""
Fastify extractors for CodeTrellis.

Provides route, plugin, hook, schema, and API extraction
for Fastify applications across versions 3.x through 5.x.
"""

from .route_extractor import (
    FastifyRouteExtractor,
    FastifyRouteInfo,
    FastifyRouteOptionsInfo,
)
from .plugin_extractor import (
    FastifyPluginExtractor,
    FastifyPluginInfo,
    FastifyPluginRegistrationInfo,
    FastifyDecoratorInfo,
)
from .hook_extractor import (
    FastifyHookExtractor,
    FastifyHookInfo,
    FastifyHookSummary,
)
from .schema_extractor import (
    FastifySchemaExtractor,
    FastifySchemaInfo,
    FastifyTypeProviderInfo,
)
from .api_extractor import (
    FastifyApiExtractor,
    FastifyResourceInfo,
    FastifySerializerInfo,
    FastifyApiSummary,
)

__all__ = [
    # Route
    "FastifyRouteExtractor",
    "FastifyRouteInfo",
    "FastifyRouteOptionsInfo",
    # Plugin
    "FastifyPluginExtractor",
    "FastifyPluginInfo",
    "FastifyPluginRegistrationInfo",
    "FastifyDecoratorInfo",
    # Hook
    "FastifyHookExtractor",
    "FastifyHookInfo",
    "FastifyHookSummary",
    # Schema
    "FastifySchemaExtractor",
    "FastifySchemaInfo",
    "FastifyTypeProviderInfo",
    # API
    "FastifyApiExtractor",
    "FastifyResourceInfo",
    "FastifySerializerInfo",
    "FastifyApiSummary",
]
