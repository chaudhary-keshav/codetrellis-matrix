"""
CodeTrellis TypeScript Extractors Module v1.0

Provides comprehensive extractors for TypeScript language constructs:

Core Type Extractors:
- TypeScriptTypeExtractor: Classes with access modifiers, abstract classes,
                            interfaces, type aliases, enums, generics,
                            conditional types, mapped types, utility types

Function Extractors:
- TypeScriptFunctionExtractor: Functions with type annotations, overloads,
                                 generic functions, type guards, assertion
                                 functions, decorator factories

API/Framework Extractors:
- TypeScriptAPIExtractor: NestJS controllers/decorators, Express typed routes,
                           tRPC routers, GraphQL (type-graphql/typegraphql),
                           Angular HTTP, Fastify typed routes

Model/Data Extractors:
- TypeScriptModelExtractor: TypeORM entities, MikroORM entities, Prisma
                              generated types, Sequelize-typescript models,
                              Drizzle ORM schemas, class-validator DTOs

Attribute Extractors:
- TypeScriptAttributeExtractor: ES module imports/exports with type-only,
                                   decorators (experimental & TC39),
                                   namespace declarations, declaration merging,
                                   triple-slash directives, JSDoc/TSDoc

Part of CodeTrellis v4.31 - TypeScript Language Support
"""

from .type_extractor import (
    TypeScriptTypeExtractor,
    TSClassInfo,
    TSInterfaceInfo,
    TSTypeAliasInfo,
    TSEnumInfo,
    TSEnumMemberInfo,
    TSPropertyInfo,
    TSGenericParam,
)
from .function_extractor import (
    TypeScriptFunctionExtractor,
    TSFunctionInfo,
    TSParameterInfo,
    TSOverloadInfo,
    TSMethodInfo,
)
from .api_extractor import (
    TypeScriptAPIExtractor,
    TSRouteInfo,
    TSMiddlewareInfo,
    TSWebSocketInfo,
    TSGraphQLResolverInfo,
    TSTRPCRouterInfo,
)
from .model_extractor import (
    TypeScriptModelExtractor,
    TSModelInfo,
    TSFieldInfo,
    TSRelationInfo,
    TSMigrationInfo,
    TSDTOInfo,
)
from .attribute_extractor import (
    TypeScriptAttributeExtractor,
    TSImportInfo,
    TSExportInfo,
    TSDecoratorInfo,
    TSNamespaceInfo,
    TSTripleSlashDirective,
    TSTSDocInfo,
)

__all__ = [
    # Type extractor
    "TypeScriptTypeExtractor",
    "TSClassInfo",
    "TSInterfaceInfo",
    "TSTypeAliasInfo",
    "TSEnumInfo",
    "TSEnumMemberInfo",
    "TSPropertyInfo",
    "TSGenericParam",
    # Function extractor
    "TypeScriptFunctionExtractor",
    "TSFunctionInfo",
    "TSParameterInfo",
    "TSOverloadInfo",
    "TSMethodInfo",
    # API extractor
    "TypeScriptAPIExtractor",
    "TSRouteInfo",
    "TSMiddlewareInfo",
    "TSWebSocketInfo",
    "TSGraphQLResolverInfo",
    "TSTRPCRouterInfo",
    # Model extractor
    "TypeScriptModelExtractor",
    "TSModelInfo",
    "TSFieldInfo",
    "TSRelationInfo",
    "TSMigrationInfo",
    "TSDTOInfo",
    # Attribute extractor
    "TypeScriptAttributeExtractor",
    "TSImportInfo",
    "TSExportInfo",
    "TSDecoratorInfo",
    "TSNamespaceInfo",
    "TSTripleSlashDirective",
    "TSTSDocInfo",
]
