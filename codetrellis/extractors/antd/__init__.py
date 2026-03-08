"""
CodeTrellis Ant Design (antd) Extractors Module v1.0

Provides comprehensive extractors for Ant Design framework constructs
across all versions (v1.x legacy, v2.x, v3.x, v4.x, v5.x latest).

Core Extractors:
- AntdComponentExtractor: Component usage, custom wrappers,
                           Pro components, layout patterns,
                           80+ core components across 10 categories
- AntdThemeExtractor: ConfigProvider, theme tokens (v5), less variables (v3/v4),
                       dark mode, compact algorithm, CSS variables,
                       component-level token customization
- AntdHookExtractor: Built-in hooks (useApp, useMessage, useNotification,
                      useModal, useBreakpoint, useToken, useWatch),
                      form hooks (useForm, useFormInstance)
- AntdStyleExtractor: CSS-in-JS (v5 createStyles), less/sass theming (v3/v4),
                       CSS modules, styled-components integration,
                       antd-style library patterns
- AntdApiExtractor: Table/ProTable column definitions, form patterns,
                     modal patterns, drawer patterns, upload patterns,
                     menu/navigation patterns

Part of CodeTrellis v4.37 - Ant Design Framework Support
"""

from .component_extractor import (
    AntdComponentExtractor,
    AntdComponentInfo,
    AntdCustomComponentInfo,
    AntdProComponentInfo,
)
from .theme_extractor import (
    AntdThemeExtractor,
    AntdThemeInfo,
    AntdTokenInfo,
    AntdLessVariableInfo,
    AntdComponentTokenInfo,
)
from .hook_extractor import (
    AntdHookExtractor,
    AntdHookUsageInfo,
    AntdCustomHookInfo,
)
from .style_extractor import (
    AntdStyleExtractor,
    AntdCSSInJSInfo,
    AntdLessStyleInfo,
    AntdStyleOverrideInfo,
)
from .api_extractor import (
    AntdApiExtractor,
    AntdTableInfo,
    AntdFormPatternInfo,
    AntdModalPatternInfo,
    AntdMenuPatternInfo,
)

__all__ = [
    # Component extractor
    "AntdComponentExtractor",
    "AntdComponentInfo",
    "AntdCustomComponentInfo",
    "AntdProComponentInfo",
    # Theme extractor
    "AntdThemeExtractor",
    "AntdThemeInfo",
    "AntdTokenInfo",
    "AntdLessVariableInfo",
    "AntdComponentTokenInfo",
    # Hook extractor
    "AntdHookExtractor",
    "AntdHookUsageInfo",
    "AntdCustomHookInfo",
    # Style extractor
    "AntdStyleExtractor",
    "AntdCSSInJSInfo",
    "AntdLessStyleInfo",
    "AntdStyleOverrideInfo",
    # API extractor
    "AntdApiExtractor",
    "AntdTableInfo",
    "AntdFormPatternInfo",
    "AntdModalPatternInfo",
    "AntdMenuPatternInfo",
]
