"""
Elixir Extractors for CodeTrellis

Provides extraction of Elixir language constructs:
- type_extractor: Modules, structs, protocols, behaviours, typespecs
- function_extractor: Functions, macros, guards, callbacks
- api_extractor: Plugs, pipelines, endpoints
- model_extractor: Schemas, changesets, migrations
- attribute_extractor: Module attributes, use/import/alias/require

Part of CodeTrellis - Elixir Language Support
"""

from .type_extractor import (
    ElixirTypeExtractor,
    ElixirModuleInfo,
    ElixirStructInfo,
    ElixirProtocolInfo,
    ElixirBehaviourInfo,
    ElixirTypespecInfo,
    ElixirExceptionInfo,
)

from .function_extractor import (
    ElixirFunctionExtractor,
    ElixirFunctionInfo,
    ElixirMacroInfo,
    ElixirGuardInfo,
    ElixirCallbackInfo,
)

from .api_extractor import (
    ElixirAPIExtractor,
    ElixirPlugInfo,
    ElixirPipelineInfo,
    ElixirEndpointInfo,
)

from .model_extractor import (
    ElixirModelExtractor,
    ElixirSchemaFieldInfo,
    ElixirSchemaInfo,
    ElixirChangesetInfo,
    ElixirGenServerStateInfo,
)

from .attribute_extractor import (
    ElixirAttributeExtractor,
    ElixirModuleAttributeInfo,
    ElixirUseDirectiveInfo,
)

__all__ = [
    # Type extractor
    "ElixirTypeExtractor",
    "ElixirModuleInfo", "ElixirStructInfo", "ElixirProtocolInfo",
    "ElixirBehaviourInfo", "ElixirTypespecInfo", "ElixirExceptionInfo",
    # Function extractor
    "ElixirFunctionExtractor",
    "ElixirFunctionInfo", "ElixirMacroInfo", "ElixirGuardInfo",
    "ElixirCallbackInfo",
    # API extractor
    "ElixirAPIExtractor",
    "ElixirPlugInfo", "ElixirPipelineInfo", "ElixirEndpointInfo",
    # Model extractor
    "ElixirModelExtractor",
    "ElixirSchemaFieldInfo", "ElixirSchemaInfo", "ElixirChangesetInfo",
    "ElixirGenServerStateInfo",
    # Attribute extractor
    "ElixirAttributeExtractor",
    "ElixirModuleAttributeInfo", "ElixirUseDirectiveInfo",
]
