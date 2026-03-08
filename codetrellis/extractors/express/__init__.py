"""
Express.js extractors for CodeTrellis.

Provides route, middleware, error handling, configuration, and API extraction
for Express.js applications across versions 3.x through 5.x.
"""

from .route_extractor import (
    ExpressRouteExtractor,
    ExpressRouteInfo,
    ExpressRouterInfo,
    ExpressParamInfo,
)
from .middleware_extractor import (
    ExpressMiddlewareExtractor,
    ExpressMiddlewareInfo,
    ExpressMiddlewareStackInfo,
)
from .error_extractor import (
    ExpressErrorExtractor,
    ExpressErrorHandlerInfo,
    ExpressCustomErrorInfo,
    ExpressErrorSummary,
)
from .config_extractor import (
    ExpressConfigExtractor,
    ExpressSettingInfo,
    ExpressAppInfo,
    ExpressServerInfo,
    ExpressConfigSummary,
)
from .api_extractor import (
    ExpressApiExtractor,
    ExpressResourceInfo,
    ExpressResponsePatternInfo,
    ExpressApiVersionInfo,
    ExpressApiSummary,
)

__all__ = [
    # Route
    "ExpressRouteExtractor",
    "ExpressRouteInfo",
    "ExpressRouterInfo",
    "ExpressParamInfo",
    # Middleware
    "ExpressMiddlewareExtractor",
    "ExpressMiddlewareInfo",
    "ExpressMiddlewareStackInfo",
    # Error
    "ExpressErrorExtractor",
    "ExpressErrorHandlerInfo",
    "ExpressCustomErrorInfo",
    "ExpressErrorSummary",
    # Config
    "ExpressConfigExtractor",
    "ExpressSettingInfo",
    "ExpressAppInfo",
    "ExpressServerInfo",
    "ExpressConfigSummary",
    # API
    "ExpressApiExtractor",
    "ExpressResourceInfo",
    "ExpressResponsePatternInfo",
    "ExpressApiVersionInfo",
    "ExpressApiSummary",
]
