"""
CodeTrellis JavaScript Extractors Module v1.0

Provides comprehensive extractors for JavaScript language constructs:

Core Type Extractors:
- JavaScriptTypeExtractor: ES6+ classes, prototype-based types, symbols, constants

Function Extractors:
- JavaScriptFunctionExtractor: functions, arrow functions, generators,
                                async functions, IIFEs, closures, methods

API/Framework Extractors:
- JavaScriptAPIExtractor: Express/Fastify/Koa/Hapi routes, middleware,
                           WebSocket handlers, GraphQL resolvers

Model/Data Extractors:
- JavaScriptModelExtractor: Mongoose schemas/models, Sequelize models,
                             Prisma integration, Knex migrations, TypeORM

Attribute Extractors:
- JavaScriptAttributeExtractor: ES6 imports/exports, CommonJS require/module.exports,
                                  dynamic imports, JSDoc comments, decorators

Part of CodeTrellis v4.30 - JavaScript Language Support
"""

from .type_extractor import (
    JavaScriptTypeExtractor,
    JSClassInfo,
    JSPrototypeInfo,
    JSConstantInfo,
    JSSymbolInfo,
    JSPropertyInfo,
)
from .function_extractor import (
    JavaScriptFunctionExtractor,
    JSFunctionInfo,
    JSParameterInfo,
    JSArrowFunctionInfo,
    JSGeneratorInfo,
)
from .api_extractor import (
    JavaScriptAPIExtractor,
    JSRouteInfo,
    JSMiddlewareInfo,
    JSWebSocketInfo,
    JSGraphQLResolverInfo,
)
from .model_extractor import (
    JavaScriptModelExtractor,
    JSModelInfo,
    JSSchemaFieldInfo,
    JSMigrationInfo,
    JSRelationInfo,
)
from .attribute_extractor import (
    JavaScriptAttributeExtractor,
    JSImportInfo,
    JSExportInfo,
    JSJSDocInfo,
    JSDecoratorInfo,
    JSDynamicImportInfo,
)

__all__ = [
    # Type extractor
    'JavaScriptTypeExtractor',
    'JSClassInfo',
    'JSPrototypeInfo',
    'JSConstantInfo',
    'JSSymbolInfo',
    'JSPropertyInfo',
    # Function extractor
    'JavaScriptFunctionExtractor',
    'JSFunctionInfo',
    'JSParameterInfo',
    'JSArrowFunctionInfo',
    'JSGeneratorInfo',
    # API extractor
    'JavaScriptAPIExtractor',
    'JSRouteInfo',
    'JSMiddlewareInfo',
    'JSWebSocketInfo',
    'JSGraphQLResolverInfo',
    # Model extractor
    'JavaScriptModelExtractor',
    'JSModelInfo',
    'JSSchemaFieldInfo',
    'JSMigrationInfo',
    'JSRelationInfo',
    # Attribute extractor
    'JavaScriptAttributeExtractor',
    'JSImportInfo',
    'JSExportInfo',
    'JSJSDocInfo',
    'JSDecoratorInfo',
    'JSDynamicImportInfo',
]
