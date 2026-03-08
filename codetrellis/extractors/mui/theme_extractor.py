"""
MUI Theme Extractor for CodeTrellis

Extracts Material UI theming configuration from React/TypeScript source code.
Covers MUI v4.x through v6.x theming:
- createTheme / createMuiTheme (v4 legacy)
- ThemeProvider / MuiThemeProvider
- Palette customization (primary, secondary, error, warning, info, success, custom)
- Typography customization (fontFamily, variants, responsive typography)
- Breakpoint customization (keys, values, custom breakpoints)
- Component style overrides (styleOverrides, defaultProps, variants)
- CSS variables (cssVariables option in v6, experimental in v5)
- Dark/light mode (mode, useColorScheme, ColorSchemeProvider)
- Joy UI theming (extendTheme, CssVarsProvider)
- Custom theme tokens / augmentColor
- Spacing, shape, transitions, z-index customization
- Theme composition / mergeThemes

Part of CodeTrellis v4.36 - Material UI (MUI) Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class MuiThemeInfo:
    """Information about a MUI theme configuration."""
    name: str = ""               # Variable name for the theme
    file: str = ""
    line_number: int = 0
    method: str = ""             # createTheme, extendTheme, createMuiTheme
    has_palette: bool = False
    has_typography: bool = False
    has_breakpoints: bool = False
    has_components: bool = False  # v5+ component overrides
    has_overrides: bool = False   # v4 overrides
    has_css_variables: bool = False  # v5 experimental / v6 default
    has_color_schemes: bool = False  # v6+ colorSchemes
    has_dark_mode: bool = False
    has_spacing: bool = False
    has_shape: bool = False
    has_transitions: bool = False
    has_z_index: bool = False
    has_mixins: bool = False
    has_shadows: bool = False
    palette_colors: List[str] = field(default_factory=list)    # primary, secondary, etc.
    custom_tokens: List[str] = field(default_factory=list)     # custom added keys
    component_overrides: List[str] = field(default_factory=list)  # MuiButton, MuiTextField, etc.
    mui_version: str = ""        # Detected MUI version (4, 5, 6)


@dataclass
class MuiPaletteInfo:
    """Information about a MUI palette color."""
    color_name: str = ""         # primary, secondary, error, custom
    main: str = ""
    light: str = ""
    dark: str = ""
    contrast_text: str = ""
    is_custom: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class MuiTypographyInfo:
    """Information about MUI typography configuration."""
    variant: str = ""            # h1, h2, body1, custom
    font_family: str = ""
    font_size: str = ""
    font_weight: str = ""
    line_height: str = ""
    is_custom_variant: bool = False
    is_responsive: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class MuiBreakpointInfo:
    """Information about MUI breakpoint configuration."""
    name: str = ""               # xs, sm, md, lg, xl, custom
    value: str = ""              # pixel value
    is_custom: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class MuiComponentOverrideInfo:
    """Information about MUI component style override."""
    component_name: str = ""     # MuiButton, MuiTextField, etc.
    has_style_overrides: bool = False
    has_default_props: bool = False
    has_variants: bool = False
    overridden_slots: List[str] = field(default_factory=list)  # root, label, etc.
    file: str = ""
    line_number: int = 0


class MuiThemeExtractor:
    """
    Extracts MUI theme configuration from source code.

    Detects:
    - createTheme / createMuiTheme / extendTheme calls
    - ThemeProvider / CssVarsProvider usage
    - Palette, typography, breakpoints, component overrides
    - Dark mode / color scheme configuration
    - CSS variables mode (v5 experimental / v6 default)
    - Custom theme tokens
    - Joy UI theme extensions
    """

    # Theme creation patterns
    THEME_CREATION = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
        r"(createTheme|createMuiTheme|extendTheme|responsiveFontSizes)\s*\(",
        re.MULTILINE
    )

    # Theme provider patterns
    THEME_PROVIDER = re.compile(
        r"<(ThemeProvider|MuiThemeProvider|CssVarsProvider|Experimental_CssVarsProvider)\s",
        re.MULTILINE
    )

    # Standard palette colors
    STANDARD_PALETTE_COLORS = {
        'primary', 'secondary', 'error', 'warning', 'info', 'success',
        'text', 'background', 'action', 'divider', 'grey',
    }

    # Standard typography variants
    STANDARD_TYPOGRAPHY_VARIANTS = {
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'subtitle1', 'subtitle2',
        'body1', 'body2',
        'button', 'caption', 'overline',
    }

    # Known MUI component names for overrides
    MUI_COMPONENT_PATTERN = re.compile(r'Mui\w+')

    def __init__(self):
        """Initialize the MUI theme extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all MUI theme configuration from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'themes', 'palettes', 'typographies', 'breakpoints', 'overrides'
        """
        themes: List[MuiThemeInfo] = []
        palettes: List[MuiPaletteInfo] = []
        typographies: List[MuiTypographyInfo] = []
        breakpoints: List[MuiBreakpointInfo] = []
        overrides: List[MuiComponentOverrideInfo] = []

        # Extract theme creation calls
        for match in self.THEME_CREATION.finditer(content):
            theme_name = match.group(1)
            method = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            # Look ahead into the theme body (brace-balanced, up to 3000 chars)
            theme_body = self._extract_body(content, match.end())

            theme_info = MuiThemeInfo(
                name=theme_name,
                file=file_path,
                line_number=line_number,
                method=method,
            )

            # Detect features in theme body
            if theme_body:
                theme_info.has_palette = 'palette' in theme_body
                theme_info.has_typography = bool(re.search(r'\btypography\b', theme_body))
                theme_info.has_breakpoints = 'breakpoints' in theme_body
                theme_info.has_components = bool(re.search(r'\bcomponents\s*:', theme_body))
                theme_info.has_overrides = bool(re.search(r'\boverrides\s*:', theme_body))
                theme_info.has_css_variables = bool(re.search(
                    r'cssVariables\s*:|cssVarPrefix|experimental_css', theme_body, re.IGNORECASE
                ))
                theme_info.has_color_schemes = 'colorSchemes' in theme_body
                theme_info.has_dark_mode = bool(re.search(
                    r"mode\s*:\s*['\"]dark['\"]|palette\s*:\s*\{[^}]*mode\s*:",
                    theme_body
                ))
                theme_info.has_spacing = 'spacing' in theme_body
                theme_info.has_shape = 'shape' in theme_body
                theme_info.has_transitions = 'transitions' in theme_body
                theme_info.has_z_index = 'zIndex' in theme_body
                theme_info.has_mixins = 'mixins' in theme_body
                theme_info.has_shadows = 'shadows' in theme_body

                # Extract palette color names
                palette_match = re.findall(r"palette\s*:\s*\{", theme_body)
                if palette_match:
                    # Find color keys in palette
                    palette_section = self._extract_section(theme_body, 'palette')
                    if palette_section:
                        color_keys = re.findall(r'(\w+)\s*:', palette_section)
                        for key in color_keys:
                            if key in self.STANDARD_PALETTE_COLORS or key not in (
                                'mode', 'contrastThreshold', 'tonalOffset',
                                'getContrastText', 'augmentColor'
                            ):
                                theme_info.palette_colors.append(key)
                                is_custom = key not in self.STANDARD_PALETTE_COLORS
                                palettes.append(MuiPaletteInfo(
                                    color_name=key,
                                    is_custom=is_custom,
                                    file=file_path,
                                    line_number=line_number,
                                ))

                # Extract component override names
                comp_section = self._extract_section(theme_body, 'components')
                if comp_section:
                    comp_names = self.MUI_COMPONENT_PATTERN.findall(comp_section)
                    for cname in comp_names:
                        if cname not in theme_info.component_overrides:
                            theme_info.component_overrides.append(cname)
                            # Check override details
                            override_section = self._extract_section(comp_section, cname)
                            if override_section:
                                overrides.append(MuiComponentOverrideInfo(
                                    component_name=cname,
                                    has_style_overrides='styleOverrides' in override_section,
                                    has_default_props='defaultProps' in override_section,
                                    has_variants=bool(re.search(r'\bvariants\s*:', override_section)),
                                    file=file_path,
                                    line_number=line_number,
                                ))

                # Extract typography variants
                typo_section = self._extract_section(theme_body, 'typography')
                if typo_section:
                    # Detect fontFamily
                    ff_match = re.search(r"fontFamily\s*:\s*['\"]([^'\"]+)['\"]", typo_section)
                    if ff_match:
                        typographies.append(MuiTypographyInfo(
                            variant='fontFamily',
                            font_family=ff_match.group(1),
                            file=file_path,
                            line_number=line_number,
                        ))
                    # Detect variant customizations
                    variant_keys = re.findall(r'(\w+)\s*:\s*\{', typo_section)
                    for vk in variant_keys:
                        if vk in self.STANDARD_TYPOGRAPHY_VARIANTS or vk.startswith('custom'):
                            is_custom = vk not in self.STANDARD_TYPOGRAPHY_VARIANTS
                            typographies.append(MuiTypographyInfo(
                                variant=vk,
                                is_custom_variant=is_custom,
                                file=file_path,
                                line_number=line_number,
                            ))

                # Extract breakpoints
                bp_section = self._extract_section(theme_body, 'breakpoints')
                if bp_section:
                    bp_values = re.findall(r"(\w+)\s*:\s*(\d+)", bp_section)
                    for bp_name, bp_val in bp_values:
                        default_bps = {'xs': '0', 'sm': '600', 'md': '900', 'lg': '1200', 'xl': '1536'}
                        is_custom = bp_name not in default_bps or default_bps.get(bp_name) != bp_val
                        breakpoints.append(MuiBreakpointInfo(
                            name=bp_name,
                            value=bp_val,
                            is_custom=is_custom,
                            file=file_path,
                            line_number=line_number,
                        ))

                # Detect MUI version from method and features
                if method == 'createMuiTheme':
                    theme_info.mui_version = 'v4'
                elif method == 'extendTheme':
                    theme_info.mui_version = 'v5'  # Joy UI or experimental
                elif theme_info.has_css_variables and theme_info.has_color_schemes:
                    theme_info.mui_version = 'v6'
                elif theme_info.has_components:
                    theme_info.mui_version = 'v5'
                elif theme_info.has_overrides:
                    theme_info.mui_version = 'v4'
                else:
                    theme_info.mui_version = 'v5'

                # Extract custom tokens
                custom_keys = re.findall(r'(\w+)\s*:', theme_body)
                known_keys = {
                    'palette', 'typography', 'breakpoints', 'components', 'overrides',
                    'spacing', 'shape', 'transitions', 'zIndex', 'mixins', 'shadows',
                    'direction', 'props', 'cssVariables', 'colorSchemes', 'defaultColorScheme',
                }
                for key in custom_keys:
                    if key not in known_keys and not key.startswith('Mui'):
                        if key not in theme_info.custom_tokens:
                            theme_info.custom_tokens.append(key)

            themes.append(theme_info)

        return {
            'themes': themes,
            'palettes': palettes,
            'typographies': typographies,
            'breakpoints': breakpoints,
            'overrides': overrides,
        }

    def _extract_body(self, content: str, start_pos: int, max_chars: int = 5000) -> str:
        """Extract the brace-balanced body starting from start_pos.
        
        start_pos is expected to be right after the opening '(' of the
        function call (e.g. createTheme( ... )).  We track matching '(' / ')'
        pairs so that the outer call is fully captured, while also keeping
        the inner braces that contain the theme config.
        """
        depth = 1  # We are already inside the opening '('
        result_chars = []
        for ch in content[start_pos:start_pos + max_chars]:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    break
            result_chars.append(ch)
        return ''.join(result_chars)

    def _extract_section(self, body: str, key: str) -> str:
        """Extract a key: { ... } section from a body string."""
        pattern = re.compile(rf'\b{re.escape(key)}\s*:\s*\{{')
        match = pattern.search(body)
        if not match:
            return ""
        depth = 0
        start = match.start()
        for i, ch in enumerate(body[match.end() - 1:match.end() + 3000]):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return body[start:match.end() + i]
        return body[start:start + 1000]
