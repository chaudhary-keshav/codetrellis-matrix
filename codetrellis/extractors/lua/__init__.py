"""
CodeTrellis Lua Extractors Module v1.0

Provides comprehensive extractors for Lua language constructs:

Core Type Extractors:
- LuaTypeExtractor: classes/metatables, modules, OOP patterns

Function Extractors:
- LuaFunctionExtractor: functions, methods, closures, coroutines

API/Framework Extractors:
- LuaAPIExtractor: LÖVE2D callbacks, OpenResty routes, Lapis routes,
                   Turbo.lua handlers, Sailor routes, Redis commands,
                   Nginx directives, game loops, event handlers

Model/ORM Extractors:
- LuaModelExtractor: Lapis models, pgmoon queries, luasql,
                      redis data structures, Tarantool spaces

Attribute Extractors:
- LuaAttributeExtractor: require imports, module definitions,
                          metatable operations, coroutine patterns,
                          FFI declarations, LuaRocks dependencies

Part of CodeTrellis v4.28 - Lua Language Support
"""

from .type_extractor import (
    LuaTypeExtractor,
    LuaClassInfo,
    LuaModuleInfo,
    LuaFieldInfo,
    LuaMetatableInfo,
)
from .function_extractor import (
    LuaFunctionExtractor,
    LuaFunctionInfo,
    LuaMethodInfo,
    LuaParameterInfo,
    LuaCoroutineInfo,
)
from .api_extractor import (
    LuaAPIExtractor,
    LuaRouteInfo,
    LuaCallbackInfo,
    LuaEventHandlerInfo,
    LuaCommandInfo,
)
from .model_extractor import (
    LuaModelExtractor,
    LuaModelInfo,
    LuaQueryInfo,
    LuaSchemaInfo,
)
from .attribute_extractor import (
    LuaAttributeExtractor,
    LuaImportInfo,
    LuaModuleDefInfo,
    LuaFFIInfo,
    LuaDependencyInfo,
    LuaMetaMethodInfo,
)

__all__ = [
    # Type extractor
    "LuaTypeExtractor",
    "LuaClassInfo",
    "LuaModuleInfo",
    "LuaFieldInfo",
    "LuaMetatableInfo",
    # Function extractor
    "LuaFunctionExtractor",
    "LuaFunctionInfo",
    "LuaMethodInfo",
    "LuaParameterInfo",
    "LuaCoroutineInfo",
    # API extractor
    "LuaAPIExtractor",
    "LuaRouteInfo",
    "LuaCallbackInfo",
    "LuaEventHandlerInfo",
    "LuaCommandInfo",
    # Model extractor
    "LuaModelExtractor",
    "LuaModelInfo",
    "LuaQueryInfo",
    "LuaSchemaInfo",
    # Attribute extractor
    "LuaAttributeExtractor",
    "LuaImportInfo",
    "LuaModuleDefInfo",
    "LuaFFIInfo",
    "LuaDependencyInfo",
    "LuaMetaMethodInfo",
]
