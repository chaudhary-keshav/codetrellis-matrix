"""
CodeTrellis Ruby Extractors Module v1.0

Provides comprehensive extractors for Ruby language constructs:

Core Type Extractors:
- RubyTypeExtractor: classes, modules, structs (Struct.new), mixins, reopened classes

Function Extractors:
- RubyFunctionExtractor: methods (def/define_method), blocks, procs, lambdas, attr_*

API/Framework Extractors:
- RubyAPIExtractor: Rails routes, Sinatra DSL, Grape, Hanami, gRPC, GraphQL

Model/ORM Extractors:
- RubyModelExtractor: ActiveRecord, Sequel, Mongoid, ROM, DataMapper, migrations

Attribute Extractors:
- RubyAttributeExtractor: gems, Bundler, DSL macros, concerns, hooks, callbacks

Part of CodeTrellis v4.23 - Ruby Language Support
"""

from .type_extractor import (
    RubyTypeExtractor,
    RubyClassInfo,
    RubyModuleInfo,
    RubyStructInfo,
    RubyFieldInfo,
    RubyMixinInfo,
)
from .function_extractor import (
    RubyFunctionExtractor,
    RubyMethodInfo,
    RubyParameterInfo,
    RubyBlockInfo,
    RubyAccessorInfo,
)
from .api_extractor import (
    RubyAPIExtractor,
    RubyRouteInfo,
    RubyGRPCServiceInfo,
    RubyGraphQLInfo,
    RubyControllerInfo,
)
from .model_extractor import (
    RubyModelExtractor,
    RubyModelInfo,
    RubyMigrationInfo,
    RubyAssociationInfo,
    RubyValidationInfo,
    RubyScopeInfo,
)
from .attribute_extractor import (
    RubyAttributeExtractor,
    RubyGemInfo,
    RubyCallbackInfo,
    RubyConcernInfo,
    RubyDSLMacroInfo,
    RubyMetaprogrammingInfo,
)

__all__ = [
    # Type extractors
    'RubyTypeExtractor', 'RubyClassInfo', 'RubyModuleInfo', 'RubyStructInfo',
    'RubyFieldInfo', 'RubyMixinInfo',
    # Function extractors
    'RubyFunctionExtractor', 'RubyMethodInfo', 'RubyParameterInfo',
    'RubyBlockInfo', 'RubyAccessorInfo',
    # API extractors
    'RubyAPIExtractor', 'RubyRouteInfo', 'RubyGRPCServiceInfo',
    'RubyGraphQLInfo', 'RubyControllerInfo',
    # Model/ORM extractors
    'RubyModelExtractor', 'RubyModelInfo', 'RubyMigrationInfo',
    'RubyAssociationInfo', 'RubyValidationInfo', 'RubyScopeInfo',
    # Attribute extractors
    'RubyAttributeExtractor', 'RubyGemInfo', 'RubyCallbackInfo',
    'RubyConcernInfo', 'RubyDSLMacroInfo', 'RubyMetaprogrammingInfo',
]
