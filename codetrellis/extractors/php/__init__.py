"""
CodeTrellis PHP Extractors Module v1.0

Provides comprehensive extractors for PHP language constructs:

Core Type Extractors:
- PhpTypeExtractor: classes, interfaces, traits, enums (PHP 8.1+), abstract classes

Function Extractors:
- PhpFunctionExtractor: functions, methods, closures, arrow functions, named arguments

API/Framework Extractors:
- PhpAPIExtractor: Laravel/Symfony/Slim/Lumen/CakePHP/CodeIgniter routes, controllers, middleware, gRPC, GraphQL

Model/ORM Extractors:
- PhpModelExtractor: Eloquent, Doctrine, Propel models, migrations, repositories

Attribute Extractors:
- PhpAttributeExtractor: composer.json parsing, PHP attributes (8.0+), annotations, dependency injection

Part of CodeTrellis v4.24 - PHP Language Support
"""

from .type_extractor import (
    PhpTypeExtractor,
    PhpClassInfo,
    PhpInterfaceInfo,
    PhpTraitInfo,
    PhpEnumInfo,
    PhpFieldInfo,
    PhpConstantInfo,
)
from .function_extractor import (
    PhpFunctionExtractor,
    PhpMethodInfo,
    PhpFunctionInfo,
    PhpParameterInfo,
    PhpClosureInfo,
)
from .api_extractor import (
    PhpAPIExtractor,
    PhpRouteInfo,
    PhpControllerInfo,
    PhpMiddlewareInfo,
    PhpGRPCServiceInfo,
    PhpGraphQLInfo,
)
from .model_extractor import (
    PhpModelExtractor,
    PhpModelInfo,
    PhpMigrationInfo,
    PhpRelationInfo,
    PhpRepositoryInfo,
)
from .attribute_extractor import (
    PhpAttributeExtractor,
    PhpPackageInfo,
    PhpAnnotationInfo,
    PhpAttributeInfo,
    PhpDIBindingInfo,
    PhpEventListenerInfo,
)

__all__ = [
    # Type extractors
    'PhpTypeExtractor', 'PhpClassInfo', 'PhpInterfaceInfo', 'PhpTraitInfo',
    'PhpEnumInfo', 'PhpFieldInfo', 'PhpConstantInfo',
    # Function extractors
    'PhpFunctionExtractor', 'PhpMethodInfo', 'PhpFunctionInfo',
    'PhpParameterInfo', 'PhpClosureInfo',
    # API extractors
    'PhpAPIExtractor', 'PhpRouteInfo', 'PhpControllerInfo',
    'PhpMiddlewareInfo', 'PhpGRPCServiceInfo', 'PhpGraphQLInfo',
    # Model/ORM extractors
    'PhpModelExtractor', 'PhpModelInfo', 'PhpMigrationInfo',
    'PhpRelationInfo', 'PhpRepositoryInfo',
    # Attribute extractors
    'PhpAttributeExtractor', 'PhpPackageInfo', 'PhpAnnotationInfo',
    'PhpAttributeInfo', 'PhpDIBindingInfo', 'PhpEventListenerInfo',
]
