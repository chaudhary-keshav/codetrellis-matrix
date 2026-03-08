"""
CodeTrellis Rust Extractors Module v1.0

Provides comprehensive extractors for Rust language constructs:

Core Type Extractors:
- RustTypeExtractor: structs, enums, traits, type aliases, impl blocks

Function Extractors:
- RustFunctionExtractor: functions, methods, async/unsafe/const

API/Framework Extractors:
- RustAPIExtractor: actix-web, rocket, axum, warp, tide routes; tonic gRPC; async-graphql

Model/ORM Extractors:
- RustModelExtractor: Diesel, SeaORM, SQLx models; schema! macros

Attribute Extractors:
- RustAttributeExtractor: derive macros, proc macros, cfg flags, serde attrs

Part of CodeTrellis v4.14 - Rust Language Support
"""

from .type_extractor import (
    RustTypeExtractor,
    RustStructInfo,
    RustEnumInfo,
    RustTraitInfo,
    RustTypeAliasInfo,
    RustImplInfo,
    RustFieldInfo,
    RustEnumVariantInfo,
    RustTraitMethodInfo,
)
from .function_extractor import (
    RustFunctionExtractor,
    RustFunctionInfo,
    RustMethodInfo,
    RustParameterInfo,
)
from .api_extractor import (
    RustAPIExtractor,
    RustRouteInfo,
    RustGRPCServiceInfo,
    RustGraphQLInfo,
)
from .model_extractor import (
    RustModelExtractor,
    RustModelInfo,
    RustSchemaInfo,
    RustMigrationInfo,
)
from .attribute_extractor import (
    RustAttributeExtractor,
    RustDeriveInfo,
    RustFeatureFlagInfo,
    RustMacroUsageInfo,
    RustCrateAttributeInfo,
)

__all__ = [
    # Type extractors
    'RustTypeExtractor', 'RustStructInfo', 'RustEnumInfo', 'RustTraitInfo',
    'RustTypeAliasInfo', 'RustImplInfo', 'RustFieldInfo', 'RustEnumVariantInfo',
    'RustTraitMethodInfo',
    # Function extractors
    'RustFunctionExtractor', 'RustFunctionInfo', 'RustMethodInfo', 'RustParameterInfo',
    # API extractors
    'RustAPIExtractor', 'RustRouteInfo', 'RustGRPCServiceInfo', 'RustGraphQLInfo',
    # Model/ORM extractors
    'RustModelExtractor', 'RustModelInfo', 'RustSchemaInfo', 'RustMigrationInfo',
    # Attribute extractors
    'RustAttributeExtractor', 'RustDeriveInfo', 'RustFeatureFlagInfo',
    'RustMacroUsageInfo', 'RustCrateAttributeInfo',
]
