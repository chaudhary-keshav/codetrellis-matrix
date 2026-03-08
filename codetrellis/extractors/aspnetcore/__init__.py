"""
ASP.NET Core extractors for CodeTrellis.

Provides specialized extraction for ASP.NET Core framework patterns including:
- Controllers and endpoints (MVC + Minimal APIs)
- Middleware pipeline
- Dependency injection configuration
- Authentication/Authorization
- Health checks
- API versioning
- Configuration binding
- Filters and action results

Supports ASP.NET Core 2.x through 9.x.

Part of CodeTrellis v4.96 - .NET Framework Enhanced Support
"""

from .controller_extractor import (
    AspNetCoreControllerExtractor,
    AspNetControllerInfo,
    AspNetEndpointInfo,
    AspNetMinimalApiInfo,
    AspNetFilterInfo,
)
from .middleware_extractor import (
    AspNetCoreMiddlewareExtractor,
    AspNetMiddlewareInfo,
    AspNetMiddlewarePipelineInfo,
)
from .di_extractor import (
    AspNetCoreDIExtractor,
    AspNetServiceRegistration,
    AspNetDIContainerInfo,
)
from .config_extractor import (
    AspNetCoreConfigExtractor,
    AspNetConfigBindingInfo,
    AspNetOptionsPatternInfo,
)
from .auth_extractor import (
    AspNetCoreAuthExtractor,
    AspNetAuthSchemeInfo,
    AspNetAuthPolicyInfo,
)

__all__ = [
    'AspNetCoreControllerExtractor',
    'AspNetControllerInfo',
    'AspNetEndpointInfo',
    'AspNetMinimalApiInfo',
    'AspNetFilterInfo',
    'AspNetCoreMiddlewareExtractor',
    'AspNetMiddlewareInfo',
    'AspNetMiddlewarePipelineInfo',
    'AspNetCoreDIExtractor',
    'AspNetServiceRegistration',
    'AspNetDIContainerInfo',
    'AspNetCoreConfigExtractor',
    'AspNetConfigBindingInfo',
    'AspNetOptionsPatternInfo',
    'AspNetCoreAuthExtractor',
    'AspNetAuthSchemeInfo',
    'AspNetAuthPolicyInfo',
]
