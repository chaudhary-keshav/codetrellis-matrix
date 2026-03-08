"""
CodeTrellis Material UI (MUI) Extractors Module v1.0

Provides comprehensive extractors for Material UI framework constructs
across all versions (v0.x legacy, v4.x @material-ui/*, v5.x @mui/*,
v6.x @mui/* with Pigment CSS).

Core Extractors:
- MuiComponentExtractor: Component usage, custom styled components,
                          component composition, slot/slotProps patterns,
                          Data Grid, Date Picker, Tree View, advanced components
- MuiThemeExtractor: createTheme, ThemeProvider, palette, typography,
                      breakpoints, component overrides, CSS variables,
                      custom theme tokens, dark/light mode, Joy UI themes
- MuiHookExtractor: Built-in MUI hooks (useTheme, useMediaQuery,
                     useAutocomplete, useScrollTrigger, etc.), custom MUI hooks
- MuiStyleExtractor: sx prop usage, styled() API, makeStyles (v4 legacy),
                      CSS theme variables, tss-react migration patterns,
                      Emotion/styled-components theming, Pigment CSS (v6)
- MuiApiExtractor: DataGrid column definitions, form patterns, dialog
                    patterns, navigation (Drawer, AppBar, Tabs), system
                    utility props, MUI X components

Part of CodeTrellis v4.36 - Material UI (MUI) Framework Support
"""

from .component_extractor import (
    MuiComponentExtractor,
    MuiComponentInfo,
    MuiCustomComponentInfo,
    MuiSlotInfo,
)
from .theme_extractor import (
    MuiThemeExtractor,
    MuiThemeInfo,
    MuiPaletteInfo,
    MuiTypographyInfo,
    MuiBreakpointInfo,
    MuiComponentOverrideInfo,
)
from .hook_extractor import (
    MuiHookExtractor,
    MuiHookUsageInfo,
    MuiCustomHookInfo,
)
from .style_extractor import (
    MuiStyleExtractor,
    MuiSxUsageInfo,
    MuiStyledComponentInfo,
    MuiMakeStylesInfo,
)
from .api_extractor import (
    MuiApiExtractor,
    MuiDataGridInfo,
    MuiFormPatternInfo,
    MuiDialogPatternInfo,
    MuiNavigationInfo,
)

__all__ = [
    # Component extractor
    "MuiComponentExtractor",
    "MuiComponentInfo",
    "MuiCustomComponentInfo",
    "MuiSlotInfo",
    # Theme extractor
    "MuiThemeExtractor",
    "MuiThemeInfo",
    "MuiPaletteInfo",
    "MuiTypographyInfo",
    "MuiBreakpointInfo",
    "MuiComponentOverrideInfo",
    # Hook extractor
    "MuiHookExtractor",
    "MuiHookUsageInfo",
    "MuiCustomHookInfo",
    # Style extractor
    "MuiStyleExtractor",
    "MuiSxUsageInfo",
    "MuiStyledComponentInfo",
    "MuiMakeStylesInfo",
    # API extractor
    "MuiApiExtractor",
    "MuiDataGridInfo",
    "MuiFormPatternInfo",
    "MuiDialogPatternInfo",
    "MuiNavigationInfo",
]
