"""
Less CSS Extractors for CodeTrellis

This package provides 5 dedicated extractors for comprehensive Less CSS analysis:

1. **LessVariableExtractor** — @variables, lazy evaluation, scope, property merging
2. **LessMixinExtractor** — .mixin() definitions, parametric mixins, guards, namespaces
3. **LessFunctionExtractor** — Built-in functions, custom plugins, Less functions
4. **LessImportExtractor** — @import with (reference)/(inline)/(less)/(css)/(multiple)/(optional)
5. **LessRulesetExtractor** — :extend(), detached rulesets, nesting, & parent selector

Supports Less versions:
- Less 1.x (early features, guards, mixins)
- Less 2.x (extend, import options, plugins)
- Less 3.x (improved guard behavior, each loops, @plugin)
- Less 4.x+ (latest, math mode strict, property merging+)

Part of CodeTrellis v4.45 — Less CSS Language Support
"""

from .variable_extractor import (
    LessVariableExtractor,
    LessVariableInfo,
    LessVariableUsageInfo,
)
from .mixin_extractor import (
    LessMixinExtractor,
    LessMixinDefInfo,
    LessMixinCallInfo,
    LessGuardInfo,
    LessNamespaceInfo,
)
from .function_extractor import (
    LessFunctionExtractor,
    LessFunctionCallInfo,
    LessPluginInfo,
)
from .import_extractor import (
    LessImportExtractor,
    LessImportInfo,
)
from .ruleset_extractor import (
    LessRulesetExtractor,
    LessExtendInfo,
    LessDetachedRulesetInfo,
    LessNestingInfo,
    LessPropertyMergeInfo,
)

__all__ = [
    # Variable extractor
    'LessVariableExtractor', 'LessVariableInfo', 'LessVariableUsageInfo',
    # Mixin extractor
    'LessMixinExtractor', 'LessMixinDefInfo', 'LessMixinCallInfo',
    'LessGuardInfo', 'LessNamespaceInfo',
    # Function extractor
    'LessFunctionExtractor', 'LessFunctionCallInfo', 'LessPluginInfo',
    # Import extractor
    'LessImportExtractor', 'LessImportInfo',
    # Ruleset extractor
    'LessRulesetExtractor', 'LessExtendInfo', 'LessDetachedRulesetInfo',
    'LessNestingInfo', 'LessPropertyMergeInfo',
]
