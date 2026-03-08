"""
tRPC extractors for CodeTrellis.

Provides router, procedure, middleware, context, and API extraction
for tRPC applications across versions 9.x through 11.x.
"""

from .router_extractor import (
    TRPCRouterExtractor,
    TRPCRouterInfo,
    TRPCProcedureInfo,
    TRPCMergedRouterInfo,
)
from .middleware_extractor import (
    TRPCMiddlewareExtractor,
    TRPCMiddlewareInfo,
    TRPCMiddlewareStackInfo,
)
from .context_extractor import (
    TRPCContextExtractor,
    TRPCContextInfo,
    TRPCInputInfo,
    TRPCOutputInfo,
)
from .config_extractor import (
    TRPCConfigExtractor,
    TRPCAdapterInfo,
    TRPCLinkInfo,
    TRPCConfigSummary,
)
from .api_extractor import (
    TRPCApiExtractor,
    TRPCImportInfo,
    TRPCClientInfo,
    TRPCApiSummary,
)

__all__ = [
    # Router
    "TRPCRouterExtractor",
    "TRPCRouterInfo",
    "TRPCProcedureInfo",
    "TRPCMergedRouterInfo",
    # Middleware
    "TRPCMiddlewareExtractor",
    "TRPCMiddlewareInfo",
    "TRPCMiddlewareStackInfo",
    # Context
    "TRPCContextExtractor",
    "TRPCContextInfo",
    "TRPCInputInfo",
    "TRPCOutputInfo",
    # Config
    "TRPCConfigExtractor",
    "TRPCAdapterInfo",
    "TRPCLinkInfo",
    "TRPCConfigSummary",
    # API
    "TRPCApiExtractor",
    "TRPCImportInfo",
    "TRPCClientInfo",
    "TRPCApiSummary",
]
