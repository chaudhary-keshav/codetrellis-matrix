"""
Apache Camel extractors for CodeTrellis.

Provides specialized extractors for Apache Camel:
- Route: RouteBuilder, route definitions, from/to endpoints
- Component: Camel component usage (file, http, jms, kafka, etc.)
- Processor: Processors, beans, EIP patterns (split, aggregate, filter, etc.)
- ErrorHandler: Error handling, dead letter channels, retry policies, exception clauses
- RestDSL: REST DSL definitions, OpenAPI integration, data formats
"""

from .route_extractor import (
    CamelRouteExtractor,
    CamelRouteInfo,
    CamelEndpointInfo,
)
from .component_extractor import (
    CamelComponentExtractor,
    CamelComponentInfo,
    CamelDataFormatInfo,
)
from .processor_extractor import (
    CamelProcessorExtractor,
    CamelProcessorInfo,
    CamelEIPInfo,
)
from .error_handler_extractor import (
    CamelErrorHandlerExtractor,
    CamelErrorHandlerInfo,
    CamelExceptionClauseInfo,
)
from .rest_dsl_extractor import (
    CamelRestDSLExtractor,
    CamelRestInfo,
    CamelRestOperationInfo,
)

__all__ = [
    # Route
    'CamelRouteExtractor', 'CamelRouteInfo', 'CamelEndpointInfo',
    # Component
    'CamelComponentExtractor', 'CamelComponentInfo', 'CamelDataFormatInfo',
    # Processor
    'CamelProcessorExtractor', 'CamelProcessorInfo', 'CamelEIPInfo',
    # Error Handler
    'CamelErrorHandlerExtractor', 'CamelErrorHandlerInfo', 'CamelExceptionClauseInfo',
    # REST DSL
    'CamelRestDSLExtractor', 'CamelRestInfo', 'CamelRestOperationInfo',
]
