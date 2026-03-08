"""
CodeTrellis Scala Extractors Module v1.0

Provides comprehensive extractors for Scala language constructs:

Core Type Extractors:
- ScalaTypeExtractor: classes, traits, objects, case classes, sealed traits,
  enums (Scala 3), abstract types, type aliases, given/using instances

Function Extractors:
- ScalaFunctionExtractor: def methods, val functions, extension methods (Scala 3),
  higher-order functions, curried functions, pattern matching, for-comprehensions

API/Framework Extractors:
- ScalaAPIExtractor: Play Framework routes, Akka HTTP, http4s, Finch, Scalatra,
  gRPC (ScalaPB/Akka gRPC), Sangria GraphQL, Caliban GraphQL

Model/ORM Extractors:
- ScalaModelExtractor: Slick, Doobie, Quill, Skunk, ScalikeJDBC, Phantom (Cassandra),
  Circe/Play JSON codecs, Protobuf messages

Attribute Extractors:
- ScalaAttributeExtractor: annotations, implicits/givens, macros, compiler plugins,
  SBT dependencies, build.sbt parsing

Part of CodeTrellis v4.25 - Scala Language Support
"""

from .type_extractor import (
    ScalaTypeExtractor,
    ScalaClassInfo,
    ScalaTraitInfo,
    ScalaObjectInfo,
    ScalaEnumInfo,
    ScalaTypeAliasInfo,
    ScalaFieldInfo,
    ScalaGivenInfo,
)
from .function_extractor import (
    ScalaFunctionExtractor,
    ScalaMethodInfo,
    ScalaParameterInfo,
)
from .api_extractor import (
    ScalaAPIExtractor,
    ScalaRouteInfo,
    ScalaGRPCServiceInfo,
    ScalaGraphQLInfo,
    ScalaControllerInfo,
)
from .model_extractor import (
    ScalaModelExtractor,
    ScalaModelInfo,
    ScalaMigrationInfo,
    ScalaCodecInfo,
)
from .attribute_extractor import (
    ScalaAttributeExtractor,
    ScalaAnnotationInfo,
    ScalaImplicitInfo,
    ScalaMacroInfo,
    ScalaDependencyInfo,
)

__all__ = [
    # Type extractors
    'ScalaTypeExtractor', 'ScalaClassInfo', 'ScalaTraitInfo', 'ScalaObjectInfo',
    'ScalaEnumInfo', 'ScalaTypeAliasInfo', 'ScalaFieldInfo', 'ScalaGivenInfo',
    # Function extractors
    'ScalaFunctionExtractor', 'ScalaMethodInfo', 'ScalaParameterInfo',
    # API extractors
    'ScalaAPIExtractor', 'ScalaRouteInfo', 'ScalaGRPCServiceInfo',
    'ScalaGraphQLInfo', 'ScalaControllerInfo',
    # Model/ORM extractors
    'ScalaModelExtractor', 'ScalaModelInfo', 'ScalaMigrationInfo',
    'ScalaCodecInfo',
    # Attribute extractors
    'ScalaAttributeExtractor', 'ScalaAnnotationInfo', 'ScalaImplicitInfo',
    'ScalaMacroInfo', 'ScalaDependencyInfo',
]
