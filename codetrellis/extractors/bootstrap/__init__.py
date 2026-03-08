"""
CodeTrellis Bootstrap Extractors Module v1.0

Provides comprehensive extractors for Bootstrap framework constructs
across all versions (v3.x, v4.x, v5.x).

Core Extractors:
- BootstrapComponentExtractor: Component usage from HTML classes and
                                React-Bootstrap/reactstrap JSX components
                                (50+ components across 8 categories:
                                layout, forms, data-display, feedback,
                                navigation, overlay, disclosure, content)
- BootstrapGridExtractor: Grid system (container/row/col patterns,
                           responsive breakpoints, gutters, ordering,
                           offsets, nesting, CSS Grid mode)
- BootstrapThemeExtractor: Theme customization (SCSS variable overrides,
                            CSS custom properties --bs-*, Bootswatch themes,
                            Bootstrap 5.3+ color modes data-bs-theme)
- BootstrapUtilityExtractor: Utility class detection and analysis
                              (spacing, display, flex, sizing, colors,
                              borders, shadows, position, overflow, opacity)
- BootstrapPluginExtractor: JavaScript plugin usage (Bootstrap 5 vanilla JS
                              constructors, jQuery plugins, data attributes,
                              event listeners, CDN/npm inclusion detection)

Part of CodeTrellis v4.40 - Bootstrap Framework Support
"""

from .component_extractor import (
    BootstrapComponentExtractor,
    BootstrapComponentInfo,
    BootstrapCustomComponentInfo,
)
from .grid_extractor import (
    BootstrapGridExtractor,
    BootstrapGridInfo,
    BootstrapBreakpointInfo,
)
from .theme_extractor import (
    BootstrapThemeExtractor,
    BootstrapThemeInfo,
    BootstrapVariableInfo,
    BootstrapColorModeInfo,
)
from .utility_extractor import (
    BootstrapUtilityExtractor,
    BootstrapUtilityInfo,
    BootstrapUtilitySummary,
)
from .plugin_extractor import (
    BootstrapPluginExtractor,
    BootstrapPluginInfo,
    BootstrapEventInfo,
    BootstrapCDNInfo,
)

__all__ = [
    # Component extractor
    "BootstrapComponentExtractor",
    "BootstrapComponentInfo",
    "BootstrapCustomComponentInfo",
    # Grid extractor
    "BootstrapGridExtractor",
    "BootstrapGridInfo",
    "BootstrapBreakpointInfo",
    # Theme extractor
    "BootstrapThemeExtractor",
    "BootstrapThemeInfo",
    "BootstrapVariableInfo",
    "BootstrapColorModeInfo",
    # Utility extractor
    "BootstrapUtilityExtractor",
    "BootstrapUtilityInfo",
    "BootstrapUtilitySummary",
    # Plugin extractor
    "BootstrapPluginExtractor",
    "BootstrapPluginInfo",
    "BootstrapEventInfo",
    "BootstrapCDNInfo",
]
