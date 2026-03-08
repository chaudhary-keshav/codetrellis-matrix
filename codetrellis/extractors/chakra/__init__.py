"""
CodeTrellis Chakra UI Extractors Module v1.0

Provides comprehensive extractors for Chakra UI framework constructs
across all versions (v1.x, v2.x, v3.x/Ark UI).

Core Extractors:
- ChakraComponentExtractor: Component usage, custom wrappers,
                             70+ core components across 8 categories
                             (layout, forms, data-display, feedback,
                             navigation, overlay, media, typography)
- ChakraThemeExtractor: extendTheme/createSystem, tokens, semantic tokens,
                         color mode, component style overrides,
                         responsive styles, recipes (v3)
- ChakraHookExtractor: Built-in hooks (useDisclosure, useToast,
                        useColorMode, useBreakpointValue, useMediaQuery,
                        useClipboard, useBoolean, useControllable),
                        custom hooks wrapping Chakra
- ChakraStyleExtractor: Style props detection, sx prop, CSS variables,
                         @emotion/styled integration, Panda CSS (v3),
                         responsive array/object syntax,
                         pseudo-style props (_hover, _focus, etc.)
- ChakraApiExtractor: Form patterns, Modal/Drawer/Popover patterns,
                       Toast patterns, Tab patterns, Menu patterns,
                       Accordion/Stepper patterns

Part of CodeTrellis v4.38 - Chakra UI Framework Support
"""

from .component_extractor import (
    ChakraComponentExtractor,
    ChakraComponentInfo,
    ChakraCustomComponentInfo,
)
from .theme_extractor import (
    ChakraThemeExtractor,
    ChakraThemeInfo,
    ChakraTokenInfo,
    ChakraSemanticTokenInfo,
    ChakraComponentStyleInfo,
)
from .hook_extractor import (
    ChakraHookExtractor,
    ChakraHookUsageInfo,
    ChakraCustomHookInfo,
)
from .style_extractor import (
    ChakraStyleExtractor,
    ChakraStylePropInfo,
    ChakraSxUsageInfo,
    ChakraResponsiveInfo,
)
from .api_extractor import (
    ChakraApiExtractor,
    ChakraFormPatternInfo,
    ChakraModalPatternInfo,
    ChakraToastPatternInfo,
    ChakraMenuPatternInfo,
)

__all__ = [
    # Component extractor
    "ChakraComponentExtractor",
    "ChakraComponentInfo",
    "ChakraCustomComponentInfo",
    # Theme extractor
    "ChakraThemeExtractor",
    "ChakraThemeInfo",
    "ChakraTokenInfo",
    "ChakraSemanticTokenInfo",
    "ChakraComponentStyleInfo",
    # Hook extractor
    "ChakraHookExtractor",
    "ChakraHookUsageInfo",
    "ChakraCustomHookInfo",
    # Style extractor
    "ChakraStyleExtractor",
    "ChakraStylePropInfo",
    "ChakraSxUsageInfo",
    "ChakraResponsiveInfo",
    # API extractor
    "ChakraApiExtractor",
    "ChakraFormPatternInfo",
    "ChakraModalPatternInfo",
    "ChakraToastPatternInfo",
    "ChakraMenuPatternInfo",
]
