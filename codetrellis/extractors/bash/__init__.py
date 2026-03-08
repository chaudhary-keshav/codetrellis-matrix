"""
CodeTrellis Bash/Shell Extractors Module v1.0

Provides comprehensive extractors for Bash/Shell language constructs:

Core Extractors:
- BashFunctionExtractor: functions, their parameters, local variables
- BashVariableExtractor: global variables, exports, arrays, associative arrays
- BashAliasExtractor: aliases, sourced files, shebang detection
- BashCommandExtractor: pipelines, subshells, process substitution, traps
- BashAPIExtractor: curl/wget/httpie calls, cron jobs, systemd units

Part of CodeTrellis v4.18 - Bash/Shell Language Support
"""

from .function_extractor import (
    BashFunctionExtractor,
    BashFunctionInfo,
    BashParameterInfo,
)
from .variable_extractor import (
    BashVariableExtractor,
    BashVariableInfo,
    BashArrayInfo,
    BashExportInfo,
)
from .alias_extractor import (
    BashAliasExtractor,
    BashAliasInfo,
    BashSourceInfo,
    BashShebangInfo,
)
from .command_extractor import (
    BashCommandExtractor,
    BashPipelineInfo,
    BashTrapInfo,
    BashSubshellInfo,
    BashHereDocInfo,
    BashRedirectInfo,
)
from .api_extractor import (
    BashAPIExtractor,
    BashHTTPCallInfo,
    BashCronJobInfo,
    BashServiceInfo,
)

__all__ = [
    # Function extractors
    'BashFunctionExtractor', 'BashFunctionInfo', 'BashParameterInfo',
    # Variable extractors
    'BashVariableExtractor', 'BashVariableInfo', 'BashArrayInfo', 'BashExportInfo',
    # Alias extractors
    'BashAliasExtractor', 'BashAliasInfo', 'BashSourceInfo', 'BashShebangInfo',
    # Command extractors
    'BashCommandExtractor', 'BashPipelineInfo', 'BashTrapInfo',
    'BashSubshellInfo', 'BashHereDocInfo', 'BashRedirectInfo',
    # API extractors
    'BashAPIExtractor', 'BashHTTPCallInfo', 'BashCronJobInfo', 'BashServiceInfo',
]
