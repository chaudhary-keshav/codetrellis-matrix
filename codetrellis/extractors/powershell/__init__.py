"""
CodeTrellis PowerShell Extractors Module v1.0

Provides comprehensive extractors for PowerShell language constructs:

Core Type Extractors:
- PowerShellTypeExtractor: classes, enums, DSC resources, CIM classes

Function Extractors:
- PowerShellFunctionExtractor: functions, cmdlets, filters, workflows,
                                script blocks, parameter sets

API/Framework Extractors:
- PowerShellAPIExtractor: REST API endpoints, DSC configurations,
                           Pester tests, module commands, pipeline commands

Model/Data Extractors:
- PowerShellModelExtractor: module manifests, DSC configurations,
                             data models, registry operations

Attribute Extractors:
- PowerShellAttributeExtractor: using statements, Import-Module,
                                  dot-sourcing, parameter attributes,
                                  comment-based help, requires statements

Part of CodeTrellis v4.29 - PowerShell Language Support
"""

from .type_extractor import (
    PowerShellTypeExtractor,
    PSClassInfo,
    PSEnumInfo,
    PSInterfaceInfo,
    PSDSCResourceInfo,
    PSPropertyInfo,
)
from .function_extractor import (
    PowerShellFunctionExtractor,
    PSFunctionInfo,
    PSParameterInfo,
    PSScriptBlockInfo,
    PSPipelineInfo,
)
from .api_extractor import (
    PowerShellAPIExtractor,
    PSRouteInfo,
    PSCmdletBindingInfo,
    PSDSCConfigInfo,
    PSPesterTestInfo,
)
from .model_extractor import (
    PowerShellModelExtractor,
    PSModuleManifestInfo,
    PSDataModelInfo,
    PSRegistryOpInfo,
    PSDSCNodeInfo,
)
from .attribute_extractor import (
    PowerShellAttributeExtractor,
    PSImportInfo,
    PSUsingInfo,
    PSRequiresInfo,
    PSCommentHelpInfo,
    PSDotSourceInfo,
)

__all__ = [
    # Type extractor
    'PowerShellTypeExtractor',
    'PSClassInfo',
    'PSEnumInfo',
    'PSInterfaceInfo',
    'PSDSCResourceInfo',
    'PSPropertyInfo',
    # Function extractor
    'PowerShellFunctionExtractor',
    'PSFunctionInfo',
    'PSParameterInfo',
    'PSScriptBlockInfo',
    'PSPipelineInfo',
    # API extractor
    'PowerShellAPIExtractor',
    'PSRouteInfo',
    'PSCmdletBindingInfo',
    'PSDSCConfigInfo',
    'PSPesterTestInfo',
    # Model extractor
    'PowerShellModelExtractor',
    'PSModuleManifestInfo',
    'PSDataModelInfo',
    'PSRegistryOpInfo',
    'PSDSCNodeInfo',
    # Attribute extractor
    'PowerShellAttributeExtractor',
    'PSImportInfo',
    'PSUsingInfo',
    'PSRequiresInfo',
    'PSCommentHelpInfo',
    'PSDotSourceInfo',
]
