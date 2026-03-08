"""
CodeTrellis Radix UI Extractors Module v1.0

Provides comprehensive extractors for Radix UI framework constructs
across all versions (Radix Primitives v0.x-v1.x, Radix Themes v1.x-v4.x,
Radix Colors v1.x-v3.x).

Radix UI is a low-level, unstyled, accessible component library for React.
Each primitive is a separate npm package installed as @radix-ui/react-*.
Radix Themes is a styled layer on top of Radix Primitives.

Core Extractors:
- RadixComponentExtractor: Primitive usage detection (30+ primitives),
    Radix Themes components (50+ styled), sub-component composition,
    data attribute state management, portal/overlay patterns
- RadixPrimitiveExtractor: Low-level primitive analysis — Slot/Compose,
    asChild pattern, Presence, FocusScope, VisuallyHidden, Portal,
    DismissableLayer, FocusGuards, Popper, Arrow, Collection
- RadixThemeExtractor: Radix Themes configuration — Theme provider,
    color scales (28 colors, 12 steps), appearance modes (light/dark/inherit),
    radius/scaling, panel-background, accent-color, gray-color
- RadixStyleExtractor: Styling detection — CSS modules, styled-components,
    Stitches, Tailwind CSS, vanilla-extract, data-attribute selectors,
    CSS variable usage
- RadixApiExtractor: Composition patterns — controlled/uncontrolled,
    onOpenChange/onValueChange, asChild prop forwarding, portal usage,
    animation integration (framer-motion, react-spring)

Part of CodeTrellis v4.41 - Radix UI Framework Support
"""

from .component_extractor import (
    RadixComponentExtractor,
    RadixComponentInfo,
    RadixThemesComponentInfo,
)
from .primitive_extractor import (
    RadixPrimitiveExtractor,
    RadixPrimitiveInfo,
    RadixSlotInfo,
)
from .theme_extractor import (
    RadixThemeExtractor,
    RadixThemeConfigInfo,
    RadixColorScaleInfo,
)
from .style_extractor import (
    RadixStyleExtractor,
    RadixStylePatternInfo,
    RadixDataAttributeInfo,
)
from .api_extractor import (
    RadixApiExtractor,
    RadixCompositionPatternInfo,
    RadixControlledPatternInfo,
    RadixPortalPatternInfo,
)

__all__ = [
    # Component extractor
    "RadixComponentExtractor",
    "RadixComponentInfo",
    "RadixThemesComponentInfo",
    # Primitive extractor
    "RadixPrimitiveExtractor",
    "RadixPrimitiveInfo",
    "RadixSlotInfo",
    # Theme extractor
    "RadixThemeExtractor",
    "RadixThemeConfigInfo",
    "RadixColorScaleInfo",
    # Style extractor
    "RadixStyleExtractor",
    "RadixStylePatternInfo",
    "RadixDataAttributeInfo",
    # API extractor
    "RadixApiExtractor",
    "RadixCompositionPatternInfo",
    "RadixControlledPatternInfo",
    "RadixPortalPatternInfo",
]
