"""
CodeTrellis Dart Extractors Module v1.0

Provides comprehensive extractors for Dart language constructs:

Core Type Extractors:
- DartTypeExtractor: classes, mixins, enums, extensions, extension types, typedefs

Function Extractors:
- DartFunctionExtractor: functions, methods, constructors, getters/setters

API/Framework Extractors:
- DartAPIExtractor: Flutter widgets, shelf/dart_frog routes, state management,
                    gRPC services, Flutter navigation

Model/ORM Extractors:
- DartModelExtractor: Drift/Floor/Isar/Hive/ObjectBox models, Freezed/JsonSerializable
                      data classes, migrations

Attribute Extractors:
- DartAttributeExtractor: annotations, imports/exports, parts, isolates,
                          platform channels, null safety, Dart 3 features

Part of CodeTrellis v4.27 - Dart Language Support
"""

from .type_extractor import (
    DartTypeExtractor,
    DartClassInfo,
    DartMixinInfo,
    DartEnumInfo,
    DartEnumCaseInfo,
    DartExtensionInfo,
    DartTypedefInfo,
    DartFieldInfo,
)
from .function_extractor import (
    DartFunctionExtractor,
    DartFunctionInfo,
    DartMethodInfo,
    DartConstructorInfo,
    DartParameterInfo,
)
from .api_extractor import (
    DartAPIExtractor,
    DartWidgetInfo,
    DartRouteInfo,
    DartStateInfo,
    DartGRPCServiceInfo,
)
from .model_extractor import (
    DartModelExtractor,
    DartModelInfo,
    DartDataClassInfo,
    DartMigrationInfo,
)
from .attribute_extractor import (
    DartAttributeExtractor,
    DartAnnotationInfo,
    DartImportInfo,
    DartPartInfo,
    DartIsolateInfo,
    DartPlatformChannelInfo,
    DartNullSafetyInfo,
)

__all__ = [
    # Type extractor
    "DartTypeExtractor",
    "DartClassInfo",
    "DartMixinInfo",
    "DartEnumInfo",
    "DartEnumCaseInfo",
    "DartExtensionInfo",
    "DartTypedefInfo",
    "DartFieldInfo",
    # Function extractor
    "DartFunctionExtractor",
    "DartFunctionInfo",
    "DartMethodInfo",
    "DartConstructorInfo",
    "DartParameterInfo",
    # API extractor
    "DartAPIExtractor",
    "DartWidgetInfo",
    "DartRouteInfo",
    "DartStateInfo",
    "DartGRPCServiceInfo",
    # Model extractor
    "DartModelExtractor",
    "DartModelInfo",
    "DartDataClassInfo",
    "DartMigrationInfo",
    # Attribute extractor
    "DartAttributeExtractor",
    "DartAnnotationInfo",
    "DartImportInfo",
    "DartPartInfo",
    "DartIsolateInfo",
    "DartPlatformChannelInfo",
    "DartNullSafetyInfo",
]
