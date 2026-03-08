"""
CodeTrellis Quarkus Extractors Module v1.0

Provides extractors for Quarkus framework constructs:

- QuarkusCDIExtractor: CDI beans, @ApplicationScoped, @RequestScoped, @Inject, producers
- QuarkusRESTExtractor: RESTEasy Reactive, JAX-RS endpoints, @Path, @GET/@POST etc.
- QuarkusPanacheExtractor: Panache entities/repositories, active record vs repository pattern
- QuarkusConfigExtractor: MicroProfile Config, @ConfigProperty, application.properties
- QuarkusExtensionExtractor: Extension detection, native build hints, health/metrics

Part of CodeTrellis v4.94 - Quarkus Framework Support
"""

from .cdi_extractor import (
    QuarkusCDIExtractor,
    QuarkusCDIBeanInfo,
    QuarkusProducerInfo,
    QuarkusInterceptorInfo,
)
from .rest_extractor import (
    QuarkusRESTExtractor,
    QuarkusEndpointInfo,
    QuarkusResourceInfo,
    QuarkusFilterInfo,
)
from .panache_extractor import (
    QuarkusPanacheExtractor,
    QuarkusPanacheEntityInfo,
    QuarkusPanacheRepoInfo,
)
from .config_extractor import (
    QuarkusConfigExtractor,
    QuarkusConfigPropertyInfo,
    QuarkusConfigMappingInfo,
)
from .extension_extractor import (
    QuarkusExtensionExtractor,
    QuarkusExtensionInfo,
    QuarkusNativeHintInfo,
    QuarkusHealthInfo,
)

__all__ = [
    'QuarkusCDIExtractor', 'QuarkusCDIBeanInfo', 'QuarkusProducerInfo', 'QuarkusInterceptorInfo',
    'QuarkusRESTExtractor', 'QuarkusEndpointInfo', 'QuarkusResourceInfo', 'QuarkusFilterInfo',
    'QuarkusPanacheExtractor', 'QuarkusPanacheEntityInfo', 'QuarkusPanacheRepoInfo',
    'QuarkusConfigExtractor', 'QuarkusConfigPropertyInfo', 'QuarkusConfigMappingInfo',
    'QuarkusExtensionExtractor', 'QuarkusExtensionInfo', 'QuarkusNativeHintInfo', 'QuarkusHealthInfo',
]
