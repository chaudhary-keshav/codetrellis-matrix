"""
CodeTrellis Emotion CSS-in-JS Extractors Module v1.0

Provides comprehensive extractors for Emotion CSS-in-JS framework
constructs across all versions (v9 legacy through v11.x+).

Core Extractors:
- EmotionComponentExtractor: styled() API usage (via @emotion/styled),
                              component creation, extending, withComponent,
                              shouldForwardProp, as prop polymorphism
- EmotionThemeExtractor: ThemeProvider (@emotion/react), useTheme hook,
                          withTheme HOC, theme function interpolations,
                          Global component, design tokens
- EmotionStyleExtractor: css prop styling (string & object), css() function
                          (@emotion/css), cx() composition, ClassNames render
                          prop, keyframes, CSS properties, media queries,
                          pseudo-selectors, dynamic props, nesting
- EmotionAnimationExtractor: keyframes() definitions, animation composition,
                              CSS transitions, CSS animations usage
- EmotionApiExtractor: @emotion/cache (createCache, CacheProvider), SSR
                        (@emotion/server extractCritical, renderStylesToString,
                        renderStylesToNodeStream, constructStyleTagsFromChunks),
                        babel-plugin-emotion, @emotion/babel-plugin, SWC
                        compiler, jest @emotion/jest, snapshot serializer

Part of CodeTrellis v4.43 - Emotion CSS-in-JS Framework Support
"""

from .component_extractor import (
    EmotionComponentExtractor,
    EmotionStyledComponentInfo,
    EmotionExtendedComponentInfo,
)
from .theme_extractor import (
    EmotionThemeExtractor,
    EmotionThemeProviderInfo,
    EmotionGlobalStyleInfo,
    EmotionThemeUsageInfo,
)
from .style_extractor import (
    EmotionStyleExtractor,
    EmotionCssPropInfo,
    EmotionCssFunctionInfo,
    EmotionClassNamesInfo,
    EmotionStylePatternInfo,
    EmotionDynamicPropInfo,
    EmotionMediaQueryInfo,
)
from .animation_extractor import (
    EmotionAnimationExtractor,
    EmotionKeyframesInfo,
    EmotionAnimationUsageInfo,
)
from .api_extractor import (
    EmotionApiExtractor,
    EmotionCacheInfo,
    EmotionSSRPatternInfo,
    EmotionBabelConfigInfo,
    EmotionTestPatternInfo,
)

__all__ = [
    # Component extractor
    "EmotionComponentExtractor",
    "EmotionStyledComponentInfo",
    "EmotionExtendedComponentInfo",
    # Theme extractor
    "EmotionThemeExtractor",
    "EmotionThemeProviderInfo",
    "EmotionGlobalStyleInfo",
    "EmotionThemeUsageInfo",
    # Style extractor
    "EmotionStyleExtractor",
    "EmotionCssPropInfo",
    "EmotionCssFunctionInfo",
    "EmotionClassNamesInfo",
    "EmotionStylePatternInfo",
    "EmotionDynamicPropInfo",
    "EmotionMediaQueryInfo",
    # Animation extractor
    "EmotionAnimationExtractor",
    "EmotionKeyframesInfo",
    "EmotionAnimationUsageInfo",
    # API extractor
    "EmotionApiExtractor",
    "EmotionCacheInfo",
    "EmotionSSRPatternInfo",
    "EmotionBabelConfigInfo",
    "EmotionTestPatternInfo",
]
