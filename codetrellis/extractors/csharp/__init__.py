"""
CodeTrellis C# Extractors Module v1.0

Provides comprehensive extractors for C# language constructs:

Core Type Extractors:
- CSharpTypeExtractor: classes, interfaces, structs, records, enums, delegates
- CSharpFunctionExtractor: methods, constructors, properties, events, indexers
- CSharpEnumExtractor: enum definitions with members

API/Framework Extractors:
- CSharpAPIExtractor: ASP.NET Core controllers, Minimal APIs, gRPC, SignalR
- CSharpModelExtractor: Entity Framework entities, DbContext, repositories
- CSharpAttributeExtractor: attribute usage detection and categorization

Part of CodeTrellis v4.13 - C# Language Support
"""

from .type_extractor import (
    CSharpTypeExtractor,
    CSharpClassInfo,
    CSharpInterfaceInfo,
    CSharpStructInfo,
    CSharpRecordInfo,
    CSharpDelegateInfo,
    CSharpFieldInfo,
    CSharpPropertyInfo,
    CSharpGenericParam,
)
from .function_extractor import (
    CSharpFunctionExtractor,
    CSharpMethodInfo,
    CSharpConstructorInfo,
    CSharpParameterInfo,
    CSharpEventInfo,
)
from .enum_extractor import (
    CSharpEnumExtractor,
    CSharpEnumInfo,
    CSharpEnumMember,
)
from .api_extractor import (
    CSharpAPIExtractor,
    CSharpEndpointInfo,
    CSharpGRPCServiceInfo,
    CSharpSignalRHubInfo,
)
from .model_extractor import (
    CSharpModelExtractor,
    CSharpEntityInfo,
    CSharpDbContextInfo,
    CSharpDTOInfo,
    CSharpRepositoryInfo,
)
from .attribute_extractor import (
    CSharpAttributeExtractor,
    CSharpAttributeInfo,
    CSharpCustomAttributeInfo,
)

__all__ = [
    # Type extractor
    'CSharpTypeExtractor',
    'CSharpClassInfo', 'CSharpInterfaceInfo', 'CSharpStructInfo',
    'CSharpRecordInfo', 'CSharpDelegateInfo', 'CSharpFieldInfo',
    'CSharpPropertyInfo', 'CSharpGenericParam',
    # Function extractor
    'CSharpFunctionExtractor',
    'CSharpMethodInfo', 'CSharpConstructorInfo', 'CSharpParameterInfo',
    'CSharpEventInfo',
    # Enum extractor
    'CSharpEnumExtractor',
    'CSharpEnumInfo', 'CSharpEnumMember',
    # API extractor
    'CSharpAPIExtractor',
    'CSharpEndpointInfo', 'CSharpGRPCServiceInfo', 'CSharpSignalRHubInfo',
    # Model extractor
    'CSharpModelExtractor',
    'CSharpEntityInfo', 'CSharpDbContextInfo',
    'CSharpDTOInfo', 'CSharpRepositoryInfo',
    # Attribute extractor
    'CSharpAttributeExtractor',
    'CSharpAttributeInfo', 'CSharpCustomAttributeInfo',
]
