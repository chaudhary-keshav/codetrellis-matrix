"""
CodeTrellis shadcn/ui Extractors Module v1.0

Provides comprehensive extractors for shadcn/ui framework constructs
across all versions (v0.x initial, v1.x-v2.x stable, v3.x/latest with
registry support, CLI improvements, and new components).

shadcn/ui is a collection of re-usable components built using Radix UI
and Tailwind CSS. Unlike traditional component libraries, shadcn/ui is
NOT installed as an npm package. Instead, components are copied directly
into the project via the CLI and can be fully customized.

Core Extractors:
- ShadcnComponentExtractor: Component usage detection (40+ components),
    Radix UI primitives, custom variants via class-variance-authority (CVA),
    component composition patterns, cn() utility usage
- ShadcnThemeExtractor: Theme configuration via CSS variables in globals.css,
    tailwind.config.{js,ts,mjs}, components.json registry config,
    dark mode via class strategy, HSL color tokens, border-radius tokens,
    chart color tokens, sidebar tokens
- ShadcnHookExtractor: shadcn/ui hooks (useToast, useMobile, useIsMobile,
    useTheme, useMediaQuery), Radix UI hooks, custom hooks wrapping
    shadcn/ui components
- ShadcnStyleExtractor: Tailwind CSS utility classes in shadcn components,
    cn() merge utility (clsx + tailwind-merge), CVA variant definitions,
    CSS variable usage, responsive patterns, dark mode classes
- ShadcnApiExtractor: Form patterns (react-hook-form + zod integration),
    Dialog/Sheet/Drawer patterns, Toast/Sonner patterns, Command/Combobox
    patterns, DataTable patterns, navigation patterns

Part of CodeTrellis v4.39 - shadcn/ui Framework Support
"""

from .component_extractor import (
    ShadcnComponentExtractor,
    ShadcnComponentInfo,
    ShadcnRegistryComponentInfo,
)
from .theme_extractor import (
    ShadcnThemeExtractor,
    ShadcnThemeInfo,
    ShadcnCSSVariableInfo,
    ShadcnComponentsJsonInfo,
)
from .hook_extractor import (
    ShadcnHookExtractor,
    ShadcnHookUsageInfo,
    ShadcnCustomHookInfo,
)
from .style_extractor import (
    ShadcnStyleExtractor,
    ShadcnCnUsageInfo,
    ShadcnCvaInfo,
    ShadcnTailwindPatternInfo,
)
from .api_extractor import (
    ShadcnApiExtractor,
    ShadcnFormPatternInfo,
    ShadcnDialogPatternInfo,
    ShadcnToastPatternInfo,
    ShadcnDataTablePatternInfo,
)

__all__ = [
    # Component extractor
    "ShadcnComponentExtractor",
    "ShadcnComponentInfo",
    "ShadcnRegistryComponentInfo",
    # Theme extractor
    "ShadcnThemeExtractor",
    "ShadcnThemeInfo",
    "ShadcnCSSVariableInfo",
    "ShadcnComponentsJsonInfo",
    # Hook extractor
    "ShadcnHookExtractor",
    "ShadcnHookUsageInfo",
    "ShadcnCustomHookInfo",
    # Style extractor
    "ShadcnStyleExtractor",
    "ShadcnCnUsageInfo",
    "ShadcnCvaInfo",
    "ShadcnTailwindPatternInfo",
    # API extractor
    "ShadcnApiExtractor",
    "ShadcnFormPatternInfo",
    "ShadcnDialogPatternInfo",
    "ShadcnToastPatternInfo",
    "ShadcnDataTablePatternInfo",
]
