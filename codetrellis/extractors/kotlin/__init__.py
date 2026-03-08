"""
CodeTrellis Kotlin Extractors Module v2.0

Provides extractors for Kotlin language constructs:

Core Type Extractors:
- KotlinTypeExtractor: classes, data classes, sealed classes, objects, interfaces, enums
- KotlinFunctionExtractor: functions, extension functions, constructors, suspend functions

API Extractors:
- KotlinAPIExtractor: Ktor routes, Spring MVC/WebFlux, Micronaut, gRPC, GraphQL, WebSocket

Model Extractors:
- KotlinModelExtractor: JPA entities, repositories, Exposed tables, Room, kotlinx.serialization, DTOs

Attribute Extractors:
- KotlinAttributeExtractor: annotations, DI bindings, delegation, multiplatform, context receivers, contracts

Part of CodeTrellis v4.21 - Kotlin Language Support Upgrade
"""

from .type_extractor import (
    KotlinTypeExtractor,
    KotlinClassInfo,
    KotlinObjectInfo,
    KotlinInterfaceInfo,
    KotlinEnumInfo,
    KotlinPropertyInfo,
)
from .function_extractor import (
    KotlinFunctionExtractor,
    KotlinFunctionInfo,
    KotlinParameterInfo,
)
from .api_extractor import (
    KotlinAPIExtractor,
    KotlinEndpointInfo,
    KotlinWebSocketInfo,
    KotlinGRPCServiceInfo,
    KotlinGraphQLInfo,
)
from .model_extractor import (
    KotlinModelExtractor,
    KotlinEntityInfo,
    KotlinRepositoryInfo,
    KotlinExposedTableInfo,
    KotlinSerializableInfo,
    KotlinDTOInfo,
)
from .attribute_extractor import (
    KotlinAttributeExtractor,
    KotlinAnnotationDefInfo,
    KotlinAnnotationUsageInfo,
    KotlinDelegationInfo,
    KotlinDIBindingInfo,
    KotlinMultiplatformDeclInfo,
    KotlinContextReceiverInfo,
    KotlinContractInfo,
)

__all__ = [
    # Type extractor
    'KotlinTypeExtractor',
    'KotlinClassInfo',
    'KotlinObjectInfo',
    'KotlinInterfaceInfo',
    'KotlinEnumInfo',
    'KotlinPropertyInfo',
    # Function extractor
    'KotlinFunctionExtractor',
    'KotlinFunctionInfo',
    'KotlinParameterInfo',
    # API extractor
    'KotlinAPIExtractor',
    'KotlinEndpointInfo',
    'KotlinWebSocketInfo',
    'KotlinGRPCServiceInfo',
    'KotlinGraphQLInfo',
    # Model extractor
    'KotlinModelExtractor',
    'KotlinEntityInfo',
    'KotlinRepositoryInfo',
    'KotlinExposedTableInfo',
    'KotlinSerializableInfo',
    'KotlinDTOInfo',
    # Attribute extractor
    'KotlinAttributeExtractor',
    'KotlinAnnotationDefInfo',
    'KotlinAnnotationUsageInfo',
    'KotlinDelegationInfo',
    'KotlinDIBindingInfo',
    'KotlinMultiplatformDeclInfo',
    'KotlinContextReceiverInfo',
    'KotlinContractInfo',
]
