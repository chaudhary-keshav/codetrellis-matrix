"""
CodeTrellis CSS Extractors Module v1.0

Provides comprehensive extractors for CSS language constructs across
all CSS versions (CSS1, CSS2, CSS2.1, CSS3 modules, CSS4/future specs)
and preprocessors (SCSS/Sass, Less, Stylus, PostCSS).

Core Extractors:
- CSSSelectorExtractor: Selectors (class, ID, element, pseudo, combinators, nesting)
- CSSPropertyExtractor: Properties, shorthands, custom properties (CSS variables)
- CSSVariableExtractor: Custom properties (--var), :root declarations, theming
- CSSMediaExtractor: Media queries, @supports, container queries, @layer
- CSSAnimationExtractor: @keyframes, transitions, animations, scroll-driven
- CSSLayoutExtractor: Flexbox, Grid, multi-column, subgrid, container queries
- CSSFunctionExtractor: CSS functions (calc, clamp, min, max, var, color-mix, etc.)
- CSSPreprocessorExtractor: SCSS/Less/Stylus mixins, variables, functions, extends

Part of CodeTrellis v4.17 - CSS Language Support
"""

from .selector_extractor import (
    CSSSelectorExtractor,
    CSSSelectorInfo,
    CSSRuleInfo,
)
from .property_extractor import (
    CSSPropertyExtractor,
    CSSPropertyInfo,
    CSSDeclarationBlockInfo,
)
from .variable_extractor import (
    CSSVariableExtractor,
    CSSVariableInfo,
    CSSThemeInfo,
)
from .media_extractor import (
    CSSMediaExtractor,
    CSSMediaQueryInfo,
    CSSSupportsInfo,
    CSSLayerInfo,
    CSSContainerQueryInfo,
)
from .animation_extractor import (
    CSSAnimationExtractor,
    CSSKeyframeInfo,
    CSSTransitionInfo,
    CSSAnimationUsageInfo,
)
from .layout_extractor import (
    CSSLayoutExtractor,
    CSSFlexboxInfo,
    CSSGridInfo,
    CSSMultiColumnInfo,
)
from .function_extractor import (
    CSSFunctionExtractor,
    CSSFunctionUsageInfo,
)
from .preprocessor_extractor import (
    CSSPreprocessorExtractor,
    CSSMixinInfo,
    CSSPreprocessorVariableInfo,
    CSSPreprocessorFunctionInfo,
    CSSExtendInfo,
    CSSPreprocessorImportInfo,
)

__all__ = [
    # Selector
    "CSSSelectorExtractor", "CSSSelectorInfo", "CSSRuleInfo",
    # Property
    "CSSPropertyExtractor", "CSSPropertyInfo", "CSSDeclarationBlockInfo",
    # Variable
    "CSSVariableExtractor", "CSSVariableInfo", "CSSThemeInfo",
    # Media
    "CSSMediaExtractor", "CSSMediaQueryInfo", "CSSSupportsInfo",
    "CSSLayerInfo", "CSSContainerQueryInfo",
    # Animation
    "CSSAnimationExtractor", "CSSKeyframeInfo", "CSSTransitionInfo",
    "CSSAnimationUsageInfo",
    # Layout
    "CSSLayoutExtractor", "CSSFlexboxInfo", "CSSGridInfo", "CSSMultiColumnInfo",
    # Function
    "CSSFunctionExtractor", "CSSFunctionUsageInfo",
    # Preprocessor
    "CSSPreprocessorExtractor", "CSSMixinInfo", "CSSPreprocessorVariableInfo",
    "CSSPreprocessorFunctionInfo", "CSSExtendInfo", "CSSPreprocessorImportInfo",
]
