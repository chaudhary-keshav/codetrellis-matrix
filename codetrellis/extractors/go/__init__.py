"""
CodeTrellis Go Extractors Module v1.0

Provides comprehensive extractors for Go language constructs:

Core Type Extractors:
- GoTypeExtractor: structs, interfaces, type aliases
- GoFunctionExtractor: functions, methods, receivers
- GoEnumExtractor: const blocks (iota patterns)

API/Framework Extractors:
- GoAPIExtractor: net/http handlers, Gin routes, Echo routes, gRPC services

Part of CodeTrellis v4.5 - Go Language Support (G-17)
"""

from .type_extractor import GoTypeExtractor, GoStructInfo, GoInterfaceInfo, GoTypeAliasInfo, GoFieldInfo
from .function_extractor import GoFunctionExtractor, GoFunctionInfo, GoMethodInfo, GoParameterInfo
from .enum_extractor import GoEnumExtractor, GoConstBlockInfo, GoConstValueInfo
from .api_extractor import GoAPIExtractor, GoRouteInfo, GoGRPCServiceInfo, GoHandlerInfo

__all__ = [
    # Type extractors
    'GoTypeExtractor', 'GoStructInfo', 'GoInterfaceInfo', 'GoTypeAliasInfo', 'GoFieldInfo',
    # Function extractors
    'GoFunctionExtractor', 'GoFunctionInfo', 'GoMethodInfo', 'GoParameterInfo',
    # Enum/const extractors
    'GoEnumExtractor', 'GoConstBlockInfo', 'GoConstValueInfo',
    # API extractors
    'GoAPIExtractor', 'GoRouteInfo', 'GoGRPCServiceInfo', 'GoHandlerInfo',
]
