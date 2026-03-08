"""
Sass/SCSS Extractors for CodeTrellis

This package provides 5 dedicated extractors for comprehensive Sass/SCSS analysis:

1. **SassVariableExtractor** — $variables, maps, lists, default/global flags
2. **SassMixinExtractor** — @mixin definitions, @include usages, @content blocks
3. **SassFunctionExtractor** — @function definitions, @return, built-in function calls
4. **SassModuleExtractor** — @use/@forward/@import, namespaces, show/hide, partials
5. **SassNestingExtractor** — nesting depth, @extend, %placeholders, selectors, @at-root

Supports Sass/SCSS versions:
- Sass 1.x (Dart Sass — current reference implementation)
- LibSass (deprecated but still widely deployed)
- Ruby Sass (original, deprecated since March 2019)
- Indented syntax (.sass) and SCSS syntax (.scss)

Part of CodeTrellis v4.44 — Sass/SCSS Language Support
"""

from .variable_extractor import (
    SassVariableExtractor,
    SassVariableInfo,
    SassMapInfo,
    SassListInfo,
)
from .mixin_extractor import (
    SassMixinExtractor,
    SassMixinDefInfo,
    SassMixinUsageInfo,
)
from .function_extractor import (
    SassFunctionExtractor,
    SassFunctionDefInfo,
    SassFunctionCallInfo,
)
from .module_extractor import (
    SassModuleExtractor,
    SassUseInfo,
    SassForwardInfo,
    SassImportInfo,
    SassPartialInfo,
)
from .nesting_extractor import (
    SassNestingExtractor,
    SassNestingInfo,
    SassExtendInfo,
    SassPlaceholderInfo,
    SassAtRootInfo,
)

__all__ = [
    # Variable extractor
    'SassVariableExtractor', 'SassVariableInfo', 'SassMapInfo', 'SassListInfo',
    # Mixin extractor
    'SassMixinExtractor', 'SassMixinDefInfo', 'SassMixinUsageInfo',
    # Function extractor
    'SassFunctionExtractor', 'SassFunctionDefInfo', 'SassFunctionCallInfo',
    # Module extractor
    'SassModuleExtractor', 'SassUseInfo', 'SassForwardInfo',
    'SassImportInfo', 'SassPartialInfo',
    # Nesting extractor
    'SassNestingExtractor', 'SassNestingInfo', 'SassExtendInfo',
    'SassPlaceholderInfo', 'SassAtRootInfo',
]
