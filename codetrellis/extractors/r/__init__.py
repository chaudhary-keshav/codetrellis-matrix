"""
CodeTrellis R Extractors Module v1.0

Provides comprehensive extractors for R language constructs:

Core Type Extractors:
- RTypeExtractor: R6 classes, R5 Reference classes, S4 classes, S3 constructors,
  S7/R7 classes (R 4.3+), S4 generics/methods, environments as modules

Function Extractors:
- RFunctionExtractor: function definitions, S3 methods, operators (%op%),
  lambda syntax (R 4.1+), roxygen documentation, NSE detection, pipe chains

API/Framework Extractors:
- RAPIExtractor: Plumber REST API routes, Shiny server/UI/modules,
  RestRserve, Ambiorix, Fiery, httpuv, Golem/Rhino

Model/ORM Extractors:
- RModelExtractor: DBI connections, dbplyr tables, dplyr pipelines,
  data.table operations, Arrow/Parquet, sparklyr, database queries

Attribute Extractors:
- RAttributeExtractor: DESCRIPTION parsing, NAMESPACE exports,
  library/require calls, renv.lock, options, env vars, lifecycle hooks

Part of CodeTrellis v4.26 - R Language Support
"""

from .type_extractor import (
    RTypeExtractor,
    RClassInfo,
    RFieldInfo,
    RGenericInfo,
    RS4MethodInfo,
    REnvironmentInfo,
)
from .function_extractor import (
    RFunctionExtractor,
    RFunctionInfo,
    RParameterInfo,
    RPipeChainInfo,
)
from .api_extractor import (
    RAPIExtractor,
    RRouteInfo,
    RShinyComponentInfo,
    RAPIEndpointInfo,
)
from .model_extractor import (
    RModelExtractor,
    RDataModelInfo,
    RDBConnectionInfo,
    RDBQueryInfo,
    RDataPipelineInfo,
)
from .attribute_extractor import (
    RAttributeExtractor,
    RPackageDepInfo,
    RExportInfo,
    RConfigInfo,
    RLifecycleHookInfo,
    RPackageMetadataInfo,
)

__all__ = [
    # Type extractors
    'RTypeExtractor', 'RClassInfo', 'RFieldInfo',
    'RGenericInfo', 'RS4MethodInfo', 'REnvironmentInfo',
    # Function extractors
    'RFunctionExtractor', 'RFunctionInfo', 'RParameterInfo',
    'RPipeChainInfo',
    # API extractors
    'RAPIExtractor', 'RRouteInfo', 'RShinyComponentInfo',
    'RAPIEndpointInfo',
    # Model/ORM extractors
    'RModelExtractor', 'RDataModelInfo', 'RDBConnectionInfo',
    'RDBQueryInfo', 'RDataPipelineInfo',
    # Attribute extractors
    'RAttributeExtractor', 'RPackageDepInfo', 'RExportInfo',
    'RConfigInfo', 'RLifecycleHookInfo', 'RPackageMetadataInfo',
]
