"""
NestJS Enhanced extractors for CodeTrellis.

Provides per-file module, controller, provider, config, and API extraction
for NestJS applications. Complements the existing project-level NestJSExtractor
with content-based per-file analysis.

Supports NestJS 7.x through 10.x.
"""

from .module_extractor import (
    NestModuleExtractor,
    NestModuleDecoratorInfo,
    NestProviderInfo,
    NestDynamicModuleInfo,
)
from .controller_extractor import (
    NestControllerExtractor,
    NestControllerInfo,
    NestEndpointInfo,
    NestParamDecoratorInfo,
)
from .provider_extractor import (
    NestProviderExtractor,
    NestInjectableInfo,
    NestInjectionInfo,
    NestCustomProviderInfo,
)
from .config_extractor import (
    NestConfigExtractor,
    NestConfigModuleInfo,
    NestEnvVarInfo,
    NestConfigServiceUsageInfo,
)
from .api_extractor import (
    NestApiExtractor,
    NestSwaggerInfo,
    NestApiPropertyInfo,
    NestDtoInfo,
    NestApiSummary,
)

__all__ = [
    # Module
    "NestModuleExtractor",
    "NestModuleDecoratorInfo",
    "NestProviderInfo",
    "NestDynamicModuleInfo",
    # Controller
    "NestControllerExtractor",
    "NestControllerInfo",
    "NestEndpointInfo",
    "NestParamDecoratorInfo",
    # Provider
    "NestProviderExtractor",
    "NestInjectableInfo",
    "NestInjectionInfo",
    "NestCustomProviderInfo",
    # Config
    "NestConfigExtractor",
    "NestConfigModuleInfo",
    "NestEnvVarInfo",
    "NestConfigServiceUsageInfo",
    # API
    "NestApiExtractor",
    "NestSwaggerInfo",
    "NestApiPropertyInfo",
    "NestDtoInfo",
    "NestApiSummary",
]
