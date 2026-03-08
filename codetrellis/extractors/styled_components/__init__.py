"""
CodeTrellis Styled Components Extractors Module v1.0

Provides comprehensive extractors for styled-components and CSS-in-JS
framework constructs across all versions (v1.x through v6.x).

Core Extractors:
- StyledComponentExtractor: styled() API usage, component creation,
                             extending, attrs, .withConfig, as prop,
                             forwardRef, shouldForwardProp, transient props ($-prefix)
- StyledThemeExtractor: ThemeProvider, createGlobalStyle, useTheme,
                         withTheme HOC, theme functions, design tokens,
                         dark/light mode, theme nesting
- StyledMixinExtractor: css`` helper, keyframes``, mixin patterns,
                         interpolation functions, tagged template patterns,
                         shared style fragments, polished helpers
- StyledStyleExtractor: CSS properties, nesting, media queries, pseudo selectors,
                         dynamic props, conditional styles, responsive patterns,
                         CSS variables, animation keyframes
- StyledApiExtractor: ServerStyleSheet (SSR), StyleSheetManager,
                       createGlobalStyle, isStyledComponent, css prop,
                       babel plugin patterns, SWC plugin, jest testing

Part of CodeTrellis v4.42 - Styled Components Framework Support
"""

from .component_extractor import (
    StyledComponentExtractor,
    StyledComponentInfo,
    StyledExtendedComponentInfo,
)
from .theme_extractor import (
    StyledThemeExtractor,
    StyledThemeProviderInfo,
    StyledGlobalStyleInfo,
    StyledThemeUsageInfo,
)
from .mixin_extractor import (
    StyledMixinExtractor,
    StyledCssHelperInfo,
    StyledKeyframesInfo,
    StyledMixinInfo,
)
from .style_extractor import (
    StyledStyleExtractor,
    StyledStylePatternInfo,
    StyledDynamicPropInfo,
    StyledMediaQueryInfo,
)
from .api_extractor import (
    StyledApiExtractor,
    StyledSSRPatternInfo,
    StyledConfigPatternInfo,
    StyledTestPatternInfo,
)

__all__ = [
    # Component extractor
    "StyledComponentExtractor",
    "StyledComponentInfo",
    "StyledExtendedComponentInfo",
    # Theme extractor
    "StyledThemeExtractor",
    "StyledThemeProviderInfo",
    "StyledGlobalStyleInfo",
    "StyledThemeUsageInfo",
    # Mixin extractor
    "StyledMixinExtractor",
    "StyledCssHelperInfo",
    "StyledKeyframesInfo",
    "StyledMixinInfo",
    # Style extractor
    "StyledStyleExtractor",
    "StyledStylePatternInfo",
    "StyledDynamicPropInfo",
    "StyledMediaQueryInfo",
    # API extractor
    "StyledApiExtractor",
    "StyledSSRPatternInfo",
    "StyledConfigPatternInfo",
    "StyledTestPatternInfo",
]
