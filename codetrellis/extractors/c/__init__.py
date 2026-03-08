"""
CodeTrellis C Extractors Module v1.0

Provides comprehensive extractors for C language constructs across all C standards
(C89/C90, C99, C11, C17, C23):

Core Type Extractors:
- CTypeExtractor: structs, unions, enums, typedefs, forward declarations

Function Extractors:
- CFunctionExtractor: functions, function pointers, static/inline/extern qualifiers

API/Framework Extractors:
- CAPIExtractor: socket APIs, HTTP handlers, IPC, signal handlers

Model/Data Extractors:
- CModelExtractor: linked lists, trees, hash tables, data structures

Attribute/Macro Extractors:
- CAttributeExtractor: preprocessor macros, #define, #ifdef, attributes, pragmas

Part of CodeTrellis v4.19 - C Language Support
"""

from .type_extractor import (
    CTypeExtractor,
    CStructInfo,
    CUnionInfo,
    CEnumInfo,
    CTypedefInfo,
    CFieldInfo,
    CEnumConstantInfo,
    CForwardDeclInfo,
)
from .function_extractor import (
    CFunctionExtractor,
    CFunctionInfo,
    CFunctionPointerInfo,
    CParameterInfo,
)
from .api_extractor import (
    CAPIExtractor,
    CSocketAPIInfo,
    CSignalHandlerInfo,
    CIPCInfo,
    CCallbackInfo,
)
from .model_extractor import (
    CModelExtractor,
    CDataStructureInfo,
    CGlobalVarInfo,
    CConstantInfo,
)
from .attribute_extractor import (
    CAttributeExtractor,
    CMacroDefInfo,
    CIncludeInfo,
    CConditionalBlockInfo,
    CPragmaInfo,
    CAttributeInfo,
    CStaticAssertInfo,
)

__all__ = [
    'CTypeExtractor', 'CStructInfo', 'CUnionInfo', 'CEnumInfo',
    'CTypedefInfo', 'CFieldInfo', 'CEnumConstantInfo', 'CForwardDeclInfo',
    'CFunctionExtractor', 'CFunctionInfo', 'CFunctionPointerInfo', 'CParameterInfo',
    'CAPIExtractor', 'CSocketAPIInfo', 'CSignalHandlerInfo', 'CIPCInfo', 'CCallbackInfo',
    'CModelExtractor', 'CDataStructureInfo', 'CGlobalVarInfo', 'CConstantInfo',
    'CAttributeExtractor', 'CMacroDefInfo', 'CIncludeInfo',
    'CConditionalBlockInfo', 'CPragmaInfo', 'CAttributeInfo', 'CStaticAssertInfo',
]
