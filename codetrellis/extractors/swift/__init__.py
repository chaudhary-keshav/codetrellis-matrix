"""
CodeTrellis Swift Extractors Module v1.0

Provides comprehensive extractors for Swift language constructs:

Core Type Extractors:
- SwiftTypeExtractor: classes, structs, enums, protocols, actors, type aliases, extensions

Function Extractors:
- SwiftFunctionExtractor: functions, methods, closures, operators, subscripts, inits/deinits

API/Framework Extractors:
- SwiftAPIExtractor: Vapor routes, SwiftUI views, URLSession, Combine publishers, SwiftNIO

Model/ORM Extractors:
- SwiftModelExtractor: Core Data entities, SwiftData models, GRDB, Codable types

Attribute Extractors:
- SwiftAttributeExtractor: property wrappers, result builders, macros, access control,
                           availability, Swift concurrency (async/await, actors, Sendable)

Part of CodeTrellis v4.22 - Swift Language Support
"""

from .type_extractor import (
    SwiftTypeExtractor,
    SwiftClassInfo,
    SwiftStructInfo,
    SwiftEnumInfo,
    SwiftProtocolInfo,
    SwiftActorInfo,
    SwiftTypeAliasInfo,
    SwiftExtensionInfo,
    SwiftFieldInfo,
    SwiftEnumCaseInfo,
    SwiftProtocolRequirementInfo,
)
from .function_extractor import (
    SwiftFunctionExtractor,
    SwiftFunctionInfo,
    SwiftMethodInfo,
    SwiftInitInfo,
    SwiftSubscriptInfo,
    SwiftParameterInfo,
)
from .api_extractor import (
    SwiftAPIExtractor,
    SwiftRouteInfo,
    SwiftViewInfo,
    SwiftPublisherInfo,
    SwiftGRPCServiceInfo,
)
from .model_extractor import (
    SwiftModelExtractor,
    SwiftModelInfo,
    SwiftMigrationInfo,
    SwiftCodableInfo,
)
from .attribute_extractor import (
    SwiftAttributeExtractor,
    SwiftPropertyWrapperInfo,
    SwiftResultBuilderInfo,
    SwiftMacroInfo,
    SwiftAvailabilityInfo,
    SwiftConcurrencyInfo,
)

__all__ = [
    # Type extractor
    "SwiftTypeExtractor",
    "SwiftClassInfo",
    "SwiftStructInfo",
    "SwiftEnumInfo",
    "SwiftProtocolInfo",
    "SwiftActorInfo",
    "SwiftTypeAliasInfo",
    "SwiftExtensionInfo",
    "SwiftFieldInfo",
    "SwiftEnumCaseInfo",
    "SwiftProtocolRequirementInfo",
    # Function extractor
    "SwiftFunctionExtractor",
    "SwiftFunctionInfo",
    "SwiftMethodInfo",
    "SwiftInitInfo",
    "SwiftSubscriptInfo",
    "SwiftParameterInfo",
    # API extractor
    "SwiftAPIExtractor",
    "SwiftRouteInfo",
    "SwiftViewInfo",
    "SwiftPublisherInfo",
    "SwiftGRPCServiceInfo",
    # Model extractor
    "SwiftModelExtractor",
    "SwiftModelInfo",
    "SwiftMigrationInfo",
    "SwiftCodableInfo",
    # Attribute extractor
    "SwiftAttributeExtractor",
    "SwiftPropertyWrapperInfo",
    "SwiftResultBuilderInfo",
    "SwiftMacroInfo",
    "SwiftAvailabilityInfo",
    "SwiftConcurrencyInfo",
]
