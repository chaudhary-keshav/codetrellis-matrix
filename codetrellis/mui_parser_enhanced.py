"""
EnhancedMuiParser v1.0 - Comprehensive Material UI (MUI) parser using all extractors.

This parser integrates all MUI extractors to provide complete parsing of
Material UI usage across React/TypeScript source files (.jsx, .tsx, .js, .ts).
It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting MUI-specific semantics.

Supports:
- Material UI v0.x (material-ui legacy, pre-rename)
- Material UI v4.x (@material-ui/core, @material-ui/icons, @material-ui/lab,
    @material-ui/styles, @material-ui/system, @material-ui/utils,
    makeStyles, withStyles, createMuiTheme, ThemeProvider)
- Material UI v5.x (@mui/material, @mui/icons-material, @mui/lab, @mui/system,
    @mui/styles, @mui/base, @mui/joy, @mui/utils, styled API, sx prop,
    createTheme, ThemeProvider, emotion integration, CSS variables,
    component slots API, unstyled/headless via @mui/base)
- Material UI v6.x (@mui/material v6, Pigment CSS engine, zero-runtime CSS-in-JS,
    @pigment-css/react, @pigment-css/nextjs-plugin, container queries,
    color-mix(), enhanced Grid v2, improved theme types)

Component Detection:
- 130+ MUI core components across 7 categories (layout, input, display,
    feedback, navigation, surface, utility)
- MUI X premium components (DataGrid, DatePicker, TreeView, Charts)
- Custom styled components (styled(), makeStyles, withStyles)
- Component slots and overrides
- Import patterns across all MUI versions

Theme System:
- createTheme / createMuiTheme / extendTheme detection
- Palette extraction (primary, secondary, error, warning, info, success, custom)
- Typography system (font families, variants, responsive)
- Breakpoints (custom values, up/down/between/only)
- Component style overrides (MuiButton, MuiTextField, etc.)
- CSS variables theme (cssVariables option in v5.1+)
- Color schemes (light/dark mode via colorSchemes in v6)
- Joy UI theme (extendTheme from @mui/joy)

Hook Patterns:
- Theme hooks (useTheme, useThemeProps, useColorScheme)
- Media hooks (useMediaQuery)
- Form hooks (useFormControl, useInput, useAutocomplete)
- Headless hooks (useMenu, useSelect, useSlider, useSwitch, useTabs, etc.)
- MUI X hooks (useGridApiRef, useGridSelector, useDateField, useTreeItem)
- 50+ known MUI hooks across 8 categories

Style System:
- sx prop detection (theme callbacks, responsive arrays, conditional, nested)
- styled() API (with name, slot, shouldForwardProp, overridesResolver)
- makeStyles / withStyles (v4 legacy + tss-react migration)
- Pigment CSS (v6 zero-runtime: css, keyframes, styled from @pigment-css/react)
- System props (responsive shorthand: p, m, display, width, etc.)

API Patterns:
- MUI X DataGrid (columns, sorting, filtering, pagination, editing, server-side)
- Form patterns (controlled, validation, FormControl, error states)
- Dialog patterns (confirmation, form, full-screen, responsive)
- Navigation patterns (Drawer, AppBar, Tabs, Stepper, Breadcrumbs)

Framework Ecosystem Detection (30+ patterns):
- Core: @mui/material, @mui/system, @mui/base, @mui/joy
- X Premium: @mui/x-data-grid, @mui/x-date-pickers, @mui/x-tree-view, @mui/x-charts
- Styling: @mui/styled-engine, @emotion/react, @emotion/styled, tss-react
- Legacy: @material-ui/core, @material-ui/icons, @material-ui/styles
- Pigment CSS: @pigment-css/react, @pigment-css/nextjs-plugin
- Companion: @mui/icons-material, @mui/lab, @mui/utils

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.36 - Material UI (MUI) Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all MUI extractors
from .extractors.mui import (
    MuiComponentExtractor, MuiComponentInfo, MuiCustomComponentInfo, MuiSlotInfo,
    MuiThemeExtractor, MuiThemeInfo, MuiPaletteInfo, MuiTypographyInfo,
    MuiBreakpointInfo, MuiComponentOverrideInfo,
    MuiHookExtractor, MuiHookUsageInfo, MuiCustomHookInfo,
    MuiStyleExtractor, MuiSxUsageInfo, MuiStyledComponentInfo,
    MuiMakeStylesInfo,
    MuiApiExtractor, MuiDataGridInfo, MuiFormPatternInfo,
    MuiDialogPatternInfo, MuiNavigationInfo,
)


@dataclass
class MuiParseResult:
    """Complete parse result for a file with MUI usage."""
    file_path: str
    file_type: str = "jsx"  # jsx, tsx

    # Components
    components: List[MuiComponentInfo] = field(default_factory=list)
    custom_components: List[MuiCustomComponentInfo] = field(default_factory=list)
    slots: List[MuiSlotInfo] = field(default_factory=list)

    # Theme
    themes: List[MuiThemeInfo] = field(default_factory=list)
    palettes: List[MuiPaletteInfo] = field(default_factory=list)
    typography_configs: List[MuiTypographyInfo] = field(default_factory=list)
    breakpoints: List[MuiBreakpointInfo] = field(default_factory=list)
    component_overrides: List[MuiComponentOverrideInfo] = field(default_factory=list)

    # Hooks
    hook_usages: List[MuiHookUsageInfo] = field(default_factory=list)
    custom_hooks: List[MuiCustomHookInfo] = field(default_factory=list)

    # Styles
    sx_usages: List[MuiSxUsageInfo] = field(default_factory=list)
    styled_components: List[MuiStyledComponentInfo] = field(default_factory=list)
    make_styles: List[MuiMakeStylesInfo] = field(default_factory=list)

    # API patterns
    data_grids: List[MuiDataGridInfo] = field(default_factory=list)
    forms: List[MuiFormPatternInfo] = field(default_factory=list)
    dialogs: List[MuiDialogPatternInfo] = field(default_factory=list)
    navigations: List[MuiNavigationInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    mui_version: str = ""  # Detected MUI version (v0, v4, v5, v6)
    has_sx_prop: bool = False
    has_styled_api: bool = False
    has_make_styles: bool = False
    has_theme: bool = False
    has_css_variables: bool = False
    has_pigment_css: bool = False
    has_joy_ui: bool = False
    has_mui_x: bool = False
    detected_features: List[str] = field(default_factory=list)


class EnhancedMuiParser:
    """
    Enhanced Material UI parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    (and potentially alongside the React parser) when MUI framework is detected.
    It extracts MUI-specific semantics that the language/React parsers cannot capture.

    Framework detection supports 30+ MUI ecosystem patterns across:
    - Core (@mui/material, @mui/system, @mui/base, @mui/joy)
    - X Premium (@mui/x-data-grid, @mui/x-date-pickers, @mui/x-tree-view, @mui/x-charts)
    - Styling (@emotion/react, @emotion/styled, tss-react, @pigment-css/react)
    - Legacy (@material-ui/core, @material-ui/icons, @material-ui/styles)
    - Icons (@mui/icons-material, @material-ui/icons)
    - Lab (@mui/lab, @material-ui/lab)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # MUI ecosystem framework / library detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core MUI v5+ ──────────────────────────────────────────
        'mui-material': re.compile(
            r"from\s+['\"]@mui/material['/\"]|"
            r"require\(['\"]@mui/material['/\"]\)",
            re.MULTILINE
        ),
        'mui-system': re.compile(
            r"from\s+['\"]@mui/system['/\"]|"
            r"require\(['\"]@mui/system['/\"]\)",
            re.MULTILINE
        ),
        'mui-base': re.compile(
            r"from\s+['\"]@mui/base['/\"]|"
            r"require\(['\"]@mui/base['/\"]\)",
            re.MULTILINE
        ),
        'mui-joy': re.compile(
            r"from\s+['\"]@mui/joy['/\"]|"
            r"require\(['\"]@mui/joy['/\"]\)",
            re.MULTILINE
        ),
        'mui-utils': re.compile(
            r"from\s+['\"]@mui/utils['/\"]",
            re.MULTILINE
        ),

        # ── MUI X Premium ────────────────────────────────────────
        'mui-x-data-grid': re.compile(
            r"from\s+['\"]@mui/x-data-grid['/\"]|"
            r"from\s+['\"]@mui/x-data-grid-pro['/\"]|"
            r"from\s+['\"]@mui/x-data-grid-premium['/\"]",
            re.MULTILINE
        ),
        'mui-x-date-pickers': re.compile(
            r"from\s+['\"]@mui/x-date-pickers['/\"]|"
            r"from\s+['\"]@mui/x-date-pickers-pro['/\"]",
            re.MULTILINE
        ),
        'mui-x-tree-view': re.compile(
            r"from\s+['\"]@mui/x-tree-view['/\"]",
            re.MULTILINE
        ),
        'mui-x-charts': re.compile(
            r"from\s+['\"]@mui/x-charts['/\"]",
            re.MULTILINE
        ),

        # ── Styling Engine ────────────────────────────────────────
        'mui-styled-engine': re.compile(
            r"from\s+['\"]@mui/styled-engine['/\"]|"
            r"from\s+['\"]@mui/styled-engine-sc['/\"]",
            re.MULTILINE
        ),
        'emotion-react': re.compile(
            r"from\s+['\"]@emotion/react['\"]|"
            r"from\s+['\"]@emotion/styled['\"]|"
            r"/\*\*\s*@jsxImportSource\s+@emotion/react\s*\*/",
            re.MULTILINE
        ),
        'tss-react': re.compile(
            r"from\s+['\"]tss-react['/\"]|"
            r"from\s+['\"]tss-react/mui['\"]",
            re.MULTILINE
        ),
        'pigment-css': re.compile(
            r"from\s+['\"]@pigment-css/react['/\"]|"
            r"from\s+['\"]@pigment-css/nextjs-plugin['\"]|"
            r"from\s+['\"]@pigment-css/vite-plugin['\"]",
            re.MULTILINE
        ),

        # ── Icons ─────────────────────────────────────────────────
        'mui-icons': re.compile(
            r"from\s+['\"]@mui/icons-material['/\"]|"
            r"from\s+['\"]@material-ui/icons['/\"]",
            re.MULTILINE
        ),

        # ── Lab ───────────────────────────────────────────────────
        'mui-lab': re.compile(
            r"from\s+['\"]@mui/lab['/\"]|"
            r"from\s+['\"]@material-ui/lab['/\"]",
            re.MULTILINE
        ),

        # ── Legacy v4 ────────────────────────────────────────────
        'material-ui-core': re.compile(
            r"from\s+['\"]@material-ui/core['/\"]|"
            r"require\(['\"]@material-ui/core['/\"]\)",
            re.MULTILINE
        ),
        'material-ui-styles': re.compile(
            r"from\s+['\"]@material-ui/styles['/\"]",
            re.MULTILINE
        ),
        'material-ui-system': re.compile(
            r"from\s+['\"]@material-ui/system['/\"]",
            re.MULTILINE
        ),

        # ── Legacy v0.x ──────────────────────────────────────────
        'material-ui-legacy': re.compile(
            r"from\s+['\"]material-ui['/\"]|"
            r"require\(['\"]material-ui['/\"]\)",
            re.MULTILINE
        ),

        # ── Companion Libraries ───────────────────────────────────
        'mui-toolpad': re.compile(
            r"from\s+['\"]@mui/toolpad['/\"]",
            re.MULTILINE
        ),
        'mui-material-next': re.compile(
            r"from\s+['\"]@mui/material-nextjs['/\"]",
            re.MULTILINE
        ),
        'notistack': re.compile(
            r"from\s+['\"]notistack['\"]|useSnackbar|SnackbarProvider",
            re.MULTILINE
        ),
        'mui-datatables': re.compile(
            r"from\s+['\"]mui-datatables['\"]|MUIDataTable",
            re.MULTILINE
        ),
    }

    # MUI version detection from import patterns and APIs
    MUI_VERSION_INDICATORS = {
        # v6 indicators (Pigment CSS, container queries)
        '@pigment-css/react': 'v6',
        '@pigment-css/nextjs-plugin': 'v6',
        '@pigment-css/vite-plugin': 'v6',
        'colorSchemes': 'v6',

        # v5 indicators (@mui/* namespace)
        '@mui/material': 'v5',
        '@mui/system': 'v5',
        '@mui/base': 'v5',
        '@mui/joy': 'v5',
        '@mui/icons-material': 'v5',
        '@mui/lab': 'v5',
        '@mui/styled-engine': 'v5',
        '@mui/x-data-grid': 'v5',
        '@mui/x-date-pickers': 'v5',
        'cssVariables': 'v5',

        # v4 indicators (@material-ui/* namespace)
        '@material-ui/core': 'v4',
        '@material-ui/icons': 'v4',
        '@material-ui/styles': 'v4',
        '@material-ui/lab': 'v4',
        '@material-ui/system': 'v4',
        'createMuiTheme': 'v4',
        'makeStyles': 'v4',
        'withStyles': 'v4',

        # v0.x indicators
        'material-ui/lib': 'v0',
    }

    # Priority ordering for version comparison
    VERSION_PRIORITY = {'v6': 6, 'v5': 5, 'v4': 4, 'v0': 0}

    def __init__(self):
        """Initialize the parser with all MUI extractors."""
        self.component_extractor = MuiComponentExtractor()
        self.theme_extractor = MuiThemeExtractor()
        self.hook_extractor = MuiHookExtractor()
        self.style_extractor = MuiStyleExtractor()
        self.api_extractor = MuiApiExtractor()

    def parse(self, content: str, file_path: str = "") -> MuiParseResult:
        """
        Parse source code and extract all MUI-specific information.

        This should be called AFTER the JavaScript/TypeScript parser has run,
        when MUI framework is detected. It extracts component usage, theme
        configuration, hook patterns, styling approaches, and API patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            MuiParseResult with all extracted MUI information
        """
        result = MuiParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        elif file_path.endswith('.ts'):
            result.file_type = "tsx"
        else:
            result.file_type = "jsx"

        # ── Detect frameworks ─────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract components ────────────────────────────────────
        comp_result = self.component_extractor.extract(content, file_path)
        result.components = comp_result.get('components', [])
        result.custom_components = comp_result.get('custom_components', [])
        result.slots = comp_result.get('slots', [])

        # ── Extract theme ─────────────────────────────────────────
        theme_result = self.theme_extractor.extract(content, file_path)
        result.themes = theme_result.get('themes', [])
        result.palettes = theme_result.get('palettes', [])
        result.typography_configs = theme_result.get('typography_configs', [])
        result.breakpoints = theme_result.get('breakpoints', [])
        result.component_overrides = theme_result.get('component_overrides', [])

        # ── Extract hooks ─────────────────────────────────────────
        hook_result = self.hook_extractor.extract(content, file_path)
        result.hook_usages = hook_result.get('hook_usages', [])
        result.custom_hooks = hook_result.get('custom_hooks', [])

        # ── Extract styles ────────────────────────────────────────
        style_result = self.style_extractor.extract(content, file_path)
        result.sx_usages = style_result.get('sx_usages', [])
        result.styled_components = style_result.get('styled_components', [])
        result.make_styles = style_result.get('make_styles', [])

        # ── Extract API patterns ──────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.data_grids = api_result.get('data_grids', [])
        result.forms = api_result.get('forms', [])
        result.dialogs = api_result.get('dialogs', [])
        result.navigations = api_result.get('navigations', [])

        # ── Compute metadata flags ────────────────────────────────
        result.has_sx_prop = len(result.sx_usages) > 0
        result.has_styled_api = len(result.styled_components) > 0
        result.has_make_styles = len(result.make_styles) > 0
        result.has_theme = len(result.themes) > 0
        result.has_css_variables = any(t.has_css_variables for t in result.themes)
        result.has_pigment_css = 'pigment-css' in result.detected_frameworks
        result.has_joy_ui = 'mui-joy' in result.detected_frameworks
        result.has_mui_x = any(
            fw.startswith('mui-x-') for fw in result.detected_frameworks
        )

        # ── Detect MUI version ────────────────────────────────────
        result.mui_version = self._detect_mui_version(content, result)

        # ── Detect features ───────────────────────────────────────
        result.detected_features = self._detect_features(content, result)

        return result

    def is_mui_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains MUI code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains MUI code
        """
        if not content:
            return False

        # Check for MUI v5+ imports (@mui/*)
        if re.search(r"from\s+['\"]@mui/", content):
            return True

        # Check for MUI v4 imports (@material-ui/*)
        if re.search(r"from\s+['\"]@material-ui/", content):
            return True

        # Check for legacy material-ui imports
        if re.search(r"from\s+['\"]material-ui['/\"]", content):
            return True

        # Check for Pigment CSS imports
        if re.search(r"from\s+['\"]@pigment-css/", content):
            return True

        # Check for createTheme / createMuiTheme
        if re.search(r'\bcreateTheme\s*\(|\bcreateMuiTheme\s*\(|\bextendTheme\s*\(', content):
            return True

        # Check for makeStyles / withStyles (strong MUI v4 indicator)
        if re.search(r'\bmakeStyles\s*\(|\bwithStyles\s*\(', content):
            return True

        # Check for MUI-specific ThemeProvider import
        if re.search(
            r"ThemeProvider.*from\s+['\"]@mui/|ThemeProvider.*from\s+['\"]@material-ui/",
            content
        ):
            return True

        return False

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which MUI ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return sorted(frameworks)

    def _detect_mui_version(self, content: str, result: MuiParseResult) -> str:
        """
        Detect the MUI version from imports and API patterns.

        Returns version string: 'v0', 'v4', 'v5', 'v6'
        """
        detected_version = ''
        max_priority = -1

        for indicator, version in self.MUI_VERSION_INDICATORS.items():
            if indicator in content:
                priority = self.VERSION_PRIORITY.get(version, 0)
                if priority > max_priority:
                    max_priority = priority
                    detected_version = version

        # Override: Pigment CSS is a definitive v6 indicator
        if result.has_pigment_css:
            return 'v6'

        # Override: Joy UI implies v5+
        if result.has_joy_ui and detected_version == '':
            return 'v5'

        # Theme-based detection
        for theme in result.themes:
            if theme.mui_version:
                v = theme.mui_version
                v_priority = self.VERSION_PRIORITY.get(v, 0)
                if v_priority > max_priority:
                    max_priority = v_priority
                    detected_version = v

        return detected_version

    def _detect_features(self, content: str, result: MuiParseResult) -> List[str]:
        """Detect MUI features used in the file."""
        features: List[str] = []

        # Component-level features
        if result.components:
            features.append('mui_components')
            categories = set(c.category for c in result.components if c.category)
            for cat in sorted(categories):
                features.append(f'mui_category_{cat}')

        if result.custom_components:
            features.append('custom_styled_components')

        if result.slots:
            features.append('component_slots')

        # Theme features
        if result.has_theme:
            features.append('theme_configuration')
        if result.palettes:
            features.append('custom_palette')
        if result.typography_configs:
            features.append('custom_typography')
        if result.breakpoints:
            features.append('custom_breakpoints')
        if result.component_overrides:
            features.append('component_overrides')
        if result.has_css_variables:
            features.append('css_variables_theme')

        # Style features
        if result.has_sx_prop:
            features.append('sx_prop')
        if result.has_styled_api:
            features.append('styled_api')
        if result.has_make_styles:
            features.append('make_styles_legacy')
        if result.has_pigment_css:
            features.append('pigment_css')

        # Hook features
        if result.hook_usages:
            hook_categories = set(h.category for h in result.hook_usages if h.category)
            for cat in sorted(hook_categories):
                features.append(f'hooks_{cat}')

        # API features
        if result.data_grids:
            features.append('data_grid')
            for grid in result.data_grids:
                if grid.has_server_side:
                    features.append('data_grid_server_side')
                if grid.has_cell_editing:
                    features.append('data_grid_editing')
                if grid.has_row_grouping:
                    features.append('data_grid_grouping')
                if grid.has_tree_data:
                    features.append('data_grid_tree')
                if grid.has_aggregation:
                    features.append('data_grid_aggregation')

        if result.forms:
            features.append('form_patterns')
            for form in result.forms:
                if form.has_validation:
                    features.append('form_validation')
                if form.integration:
                    features.append(f'form_{form.integration}')

        if result.dialogs:
            features.append('dialog_patterns')
            for dlg in result.dialogs:
                if dlg.dialog_type:
                    features.append(f'dialog_{dlg.dialog_type}')

        if result.navigations:
            features.append('navigation_patterns')
            nav_types = set(n.pattern_type for n in result.navigations)
            for nt in sorted(nav_types):
                features.append(f'nav_{nt}')

        # Joy UI
        if result.has_joy_ui:
            features.append('joy_ui')

        # MUI X
        if result.has_mui_x:
            features.append('mui_x')

        # Remove duplicates while preserving order
        seen = set()
        unique_features = []
        for f in features:
            if f not in seen:
                seen.add(f)
                unique_features.append(f)

        return unique_features
