"""
Hapi.js extractors for CodeTrellis.

Provides comprehensive extraction of @hapi/hapi ecosystem patterns:
- Route extraction (server.route(), route config, path parameters, validation)
- Plugin extraction (server.register(), plugin lifecycle, dependencies)
- Auth extraction (server.auth.strategy/scheme/default, cookie/bearer/basic/jwt)
- Server/Config extraction (server options, cache/catbox, server methods, ext points)
- API extraction (imports, ecosystem packages, version detection)

Supports @hapi/hapi v17 through v21+ (modern async/await API).
Also supports legacy hapi (pre-v17) patterns.
"""

from .route_extractor import (
    HapiRouteExtractor,
    HapiRouteInfo,
    HapiRouteConfigInfo,
    HapiValidationInfo,
)
from .plugin_extractor import (
    HapiPluginExtractor,
    HapiPluginInfo,
    HapiPluginDependencyInfo,
)
from .auth_extractor import (
    HapiAuthExtractor,
    HapiAuthStrategyInfo,
    HapiAuthSchemeInfo,
    HapiAuthScopeInfo,
)
from .server_extractor import (
    HapiServerExtractor,
    HapiServerConfigInfo,
    HapiCacheInfo,
    HapiServerMethodInfo,
    HapiExtPointInfo,
)
from .api_extractor import (
    HapiApiExtractor,
    HapiImportInfo,
    HapiApiSummary,
)

__all__ = [
    # Route
    'HapiRouteExtractor',
    'HapiRouteInfo',
    'HapiRouteConfigInfo',
    'HapiValidationInfo',
    # Plugin
    'HapiPluginExtractor',
    'HapiPluginInfo',
    'HapiPluginDependencyInfo',
    # Auth
    'HapiAuthExtractor',
    'HapiAuthStrategyInfo',
    'HapiAuthSchemeInfo',
    'HapiAuthScopeInfo',
    # Server
    'HapiServerExtractor',
    'HapiServerConfigInfo',
    'HapiCacheInfo',
    'HapiServerMethodInfo',
    'HapiExtPointInfo',
    # API
    'HapiApiExtractor',
    'HapiImportInfo',
    'HapiApiSummary',
]
