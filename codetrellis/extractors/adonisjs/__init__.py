"""
AdonisJS extractors for CodeTrellis.

Provides comprehensive extraction of AdonisJS ecosystem patterns:
- Route extraction (Route.get/post/resource/group, route params, middleware binding)
- Controller extraction (handle methods, resourceful actions, dependency injection)
- Middleware extraction (global, named, route, groups, kernel registration)
- Model extraction (Lucid ORM models, relationships, hooks, scopes, computed)
- API extraction (imports, @adonisjs/* packages, version detection, providers)

Supports AdonisJS v4 (legacy), v5 (TypeScript-first), and v6 (ESM, Vite).
"""

from .route_extractor import (
    AdonisRouteExtractor,
    AdonisRouteInfo,
    AdonisRouteGroupInfo,
    AdonisResourceRouteInfo,
)
from .controller_extractor import (
    AdonisControllerExtractor,
    AdonisControllerInfo,
    AdonisActionInfo,
)
from .middleware_extractor import (
    AdonisMiddlewareExtractor,
    AdonisMiddlewareInfo,
    AdonisMiddlewareKernelInfo,
)
from .model_extractor import (
    AdonisModelExtractor,
    AdonisModelInfo,
    AdonisRelationshipInfo,
    AdonisModelHookInfo,
)
from .api_extractor import (
    AdonisApiExtractor,
    AdonisImportInfo,
    AdonisProviderInfo,
    AdonisApiSummary,
)

__all__ = [
    # Route
    'AdonisRouteExtractor',
    'AdonisRouteInfo',
    'AdonisRouteGroupInfo',
    'AdonisResourceRouteInfo',
    # Controller
    'AdonisControllerExtractor',
    'AdonisControllerInfo',
    'AdonisActionInfo',
    # Middleware
    'AdonisMiddlewareExtractor',
    'AdonisMiddlewareInfo',
    'AdonisMiddlewareKernelInfo',
    # Model
    'AdonisModelExtractor',
    'AdonisModelInfo',
    'AdonisRelationshipInfo',
    'AdonisModelHookInfo',
    # API
    'AdonisApiExtractor',
    'AdonisImportInfo',
    'AdonisProviderInfo',
    'AdonisApiSummary',
]
