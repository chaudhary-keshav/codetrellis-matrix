"""
CodeTrellis Tailwind CSS Extractors Module v1.0

Provides comprehensive extractors for Tailwind CSS utility-first framework
across all versions (v1.x, v2.x, v3.x, v4.x).

Core Extractors:
- TailwindUtilityExtractor: Utility class usage, @apply directives, arbitrary values
- TailwindComponentExtractor: Component patterns, @layer components, class compositions
- TailwindConfigExtractor: tailwind.config.js/ts/mjs parsing, theme overrides, plugins
- TailwindThemeExtractor: Design tokens, color palettes, spacing scales, typography
- TailwindPluginExtractor: Plugin detection, custom utilities, custom variants

Part of CodeTrellis v4.35 - Tailwind CSS Language Support
"""

from .utility_extractor import (
    TailwindUtilityExtractor,
    TailwindUtilityInfo,
    TailwindApplyInfo,
    TailwindArbitraryInfo,
)
from .component_extractor import (
    TailwindComponentExtractor,
    TailwindComponentInfo,
    TailwindLayerInfo,
    TailwindDirectiveInfo,
)
from .config_extractor import (
    TailwindConfigExtractor,
    TailwindConfigInfo,
    TailwindContentPathInfo,
    TailwindPluginConfigInfo,
)
from .theme_extractor import (
    TailwindThemeExtractor,
    TailwindThemeTokenInfo,
    TailwindColorInfo,
    TailwindScreenInfo,
)
from .plugin_extractor import (
    TailwindPluginExtractor,
    TailwindPluginInfo,
    TailwindCustomUtilityInfo,
    TailwindCustomVariantInfo,
)

__all__ = [
    # Utility
    "TailwindUtilityExtractor", "TailwindUtilityInfo",
    "TailwindApplyInfo", "TailwindArbitraryInfo",
    # Component
    "TailwindComponentExtractor", "TailwindComponentInfo",
    "TailwindLayerInfo", "TailwindDirectiveInfo",
    # Config
    "TailwindConfigExtractor", "TailwindConfigInfo",
    "TailwindContentPathInfo", "TailwindPluginConfigInfo",
    # Theme
    "TailwindThemeExtractor", "TailwindThemeTokenInfo",
    "TailwindColorInfo", "TailwindScreenInfo",
    # Plugin
    "TailwindPluginExtractor", "TailwindPluginInfo",
    "TailwindCustomUtilityInfo", "TailwindCustomVariantInfo",
]
