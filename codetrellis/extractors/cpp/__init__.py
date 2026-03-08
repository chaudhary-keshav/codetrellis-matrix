"""
CodeTrellis C++ Extractors Module v1.0

Provides comprehensive extractors for C++ language constructs across all C++ standards
(C++98, C++03, C++11, C++14, C++17, C++20, C++23, C++26):

Core Type Extractors:
- CppTypeExtractor: classes, structs, unions, enums (scoped/unscoped), concepts,
  type aliases, forward declarations, namespaces, templates

Function Extractors:
- CppFunctionExtractor: methods, free functions, constructors, destructors,
  operators, lambdas, coroutines, template functions, constexpr/consteval

API/Framework Extractors:
- CppAPIExtractor: REST endpoints (Crow/Pistache/httplib/Beast/Drogon),
  gRPC services, Qt signals/slots, Boost.Asio, WebSocket, IPC, callbacks

Model/Data Extractors:
- CppModelExtractor: STL containers, smart pointers, RAII patterns,
  global variables, constants, design pattern detection

Attribute/Preprocessor Extractors:
- CppAttributeExtractor: includes, macros, conditionals, pragmas,
  C++ attributes, static_assert, C++20 modules

Part of CodeTrellis v4.20 - C++ Language Support
"""

from .type_extractor import (
    CppTypeExtractor,
    CppClassInfo,
    CppUnionInfo,
    CppEnumInfo,
    CppEnumConstantInfo,
    CppTypeAliasInfo,
    CppConceptInfo,
    CppForwardDeclInfo,
    CppNamespaceInfo,
    CppFieldInfo,
    CppBaseClassInfo,
)
from .function_extractor import (
    CppFunctionExtractor,
    CppMethodInfo,
    CppLambdaInfo,
    CppParameterInfo,
)
from .api_extractor import (
    CppAPIExtractor,
    CppEndpointInfo,
    CppGrpcServiceInfo,
    CppSignalSlotInfo,
    CppCallbackInfo,
    CppNetworkingInfo,
    CppIPCInfo,
)
from .model_extractor import (
    CppModelExtractor,
    CppContainerUsageInfo,
    CppSmartPointerInfo,
    CppRAIIInfo,
    CppGlobalVarInfo,
    CppConstantInfo,
    CppDesignPatternInfo,
)
from .attribute_extractor import (
    CppAttributeExtractor,
    CppIncludeInfo,
    CppMacroDefInfo,
    CppConditionalBlockInfo,
    CppPragmaInfo,
    CppAttributeInfo,
    CppStaticAssertInfo,
    CppModuleInfo,
)

__all__ = [
    # Type extractor
    'CppTypeExtractor', 'CppClassInfo', 'CppUnionInfo', 'CppEnumInfo',
    'CppEnumConstantInfo', 'CppTypeAliasInfo', 'CppConceptInfo',
    'CppForwardDeclInfo', 'CppNamespaceInfo', 'CppFieldInfo', 'CppBaseClassInfo',
    # Function extractor
    'CppFunctionExtractor', 'CppMethodInfo', 'CppLambdaInfo', 'CppParameterInfo',
    # API extractor
    'CppAPIExtractor', 'CppEndpointInfo', 'CppGrpcServiceInfo',
    'CppSignalSlotInfo', 'CppCallbackInfo', 'CppNetworkingInfo', 'CppIPCInfo',
    # Model extractor
    'CppModelExtractor', 'CppContainerUsageInfo', 'CppSmartPointerInfo',
    'CppRAIIInfo', 'CppGlobalVarInfo', 'CppConstantInfo', 'CppDesignPatternInfo',
    # Attribute extractor
    'CppAttributeExtractor', 'CppIncludeInfo', 'CppMacroDefInfo',
    'CppConditionalBlockInfo', 'CppPragmaInfo', 'CppAttributeInfo',
    'CppStaticAssertInfo', 'CppModuleInfo',
]
