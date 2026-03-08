"""
Bootstrap Theme Extractor for CodeTrellis

Extracts Bootstrap theming and customization from source code.
Covers Bootstrap v3.x through v5.x theming systems:

SCSS/Sass Variables:
- $primary, $secondary, $success, $info, $warning, $danger, $light, $dark
- $body-bg, $body-color, $font-family-base, $font-size-base
- $spacer, $border-radius, $box-shadow, $transition-base
- $grid-breakpoints, $container-max-widths, $grid-gutter-width
- $enable-rounded, $enable-shadows, $enable-gradients, etc.

CSS Custom Properties (v5):
- --bs-primary, --bs-secondary, --bs-*-rgb
- --bs-body-font-family, --bs-body-font-size
- --bs-border-width, --bs-border-radius
- Theme colors, spacing scale, component tokens

Bootstrap Themes:
- Bootswatch (26+ free themes)
- Bootstrap 5 color modes (data-bs-theme="dark")
- Custom theme builds

Part of CodeTrellis v4.40 - Bootstrap Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BootstrapThemeInfo:
    """Information about Bootstrap theme configuration."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    method: str = ""              # scss-variables, css-variables, bootswatch, color-modes
    bootstrap_version: str = ""
    has_custom_colors: bool = False
    has_custom_breakpoints: bool = False
    has_custom_spacing: bool = False
    has_custom_typography: bool = False
    has_dark_mode: bool = False
    has_color_modes: bool = False
    variable_count: int = 0
    custom_properties: List[str] = field(default_factory=list)


@dataclass
class BootstrapVariableInfo:
    """Information about a Bootstrap SCSS/CSS variable override."""
    variable_name: str = ""
    file: str = ""
    line_number: int = 0
    value: str = ""
    category: str = ""           # colors, typography, spacing, borders, shadows, grid, components
    is_custom_property: bool = False
    is_override: bool = False


@dataclass
class BootstrapColorModeInfo:
    """Information about Bootstrap color mode usage."""
    mode: str = ""               # light, dark, auto, custom
    file: str = ""
    line_number: int = 0
    method: str = ""             # data-bs-theme, prefers-color-scheme, js-toggle
    has_toggle: bool = False


class BootstrapThemeExtractor:
    """
    Extracts Bootstrap theming and customization from source code.

    Detects:
    - SCSS variable overrides ($primary, $body-bg, etc.)
    - CSS custom property overrides (--bs-primary, etc.)
    - Bootswatch themes
    - Bootstrap 5 color modes (data-bs-theme, prefers-color-scheme)
    - Custom theme configurations
    """

    # Bootstrap SCSS variable categories
    SCSS_VARIABLE_CATEGORIES = {
        # Colors
        'primary': 'colors', 'secondary': 'colors', 'success': 'colors',
        'info': 'colors', 'warning': 'colors', 'danger': 'colors',
        'light': 'colors', 'dark': 'colors',
        'blue': 'colors', 'indigo': 'colors', 'purple': 'colors',
        'pink': 'colors', 'red': 'colors', 'orange': 'colors',
        'yellow': 'colors', 'green': 'colors', 'teal': 'colors',
        'cyan': 'colors', 'white': 'colors', 'gray': 'colors',
        'body-bg': 'colors', 'body-color': 'colors',
        'link-color': 'colors', 'link-hover-color': 'colors',
        'theme-colors': 'colors', 'grays': 'colors',
        'color-mode-type': 'colors',

        # Typography
        'font-family-base': 'typography', 'font-family-sans-serif': 'typography',
        'font-family-monospace': 'typography', 'font-family-code': 'typography',
        'font-size-base': 'typography', 'font-size-sm': 'typography',
        'font-size-lg': 'typography', 'font-weight-base': 'typography',
        'font-weight-bold': 'typography', 'font-weight-bolder': 'typography',
        'font-weight-light': 'typography', 'font-weight-lighter': 'typography',
        'font-weight-normal': 'typography',
        'line-height-base': 'typography', 'line-height-sm': 'typography',
        'line-height-lg': 'typography',
        'h1-font-size': 'typography', 'h2-font-size': 'typography',
        'h3-font-size': 'typography', 'h4-font-size': 'typography',
        'h5-font-size': 'typography', 'h6-font-size': 'typography',
        'headings-font-family': 'typography', 'headings-font-weight': 'typography',
        'headings-color': 'typography', 'headings-line-height': 'typography',
        'display-font-sizes': 'typography', 'display-font-weight': 'typography',
        'lead-font-size': 'typography', 'lead-font-weight': 'typography',
        'small-font-size': 'typography',

        # Spacing
        'spacer': 'spacing', 'spacers': 'spacing',

        # Grid
        'grid-columns': 'grid', 'grid-gutter-width': 'grid',
        'grid-row-columns': 'grid',
        'grid-breakpoints': 'grid', 'container-max-widths': 'grid',
        'container-padding-x': 'grid',

        # Borders
        'border-width': 'borders', 'border-color': 'borders',
        'border-style': 'borders',
        'border-radius': 'borders', 'border-radius-sm': 'borders',
        'border-radius-lg': 'borders', 'border-radius-xl': 'borders',
        'border-radius-xxl': 'borders', 'border-radius-pill': 'borders',

        # Shadows
        'box-shadow': 'shadows', 'box-shadow-sm': 'shadows',
        'box-shadow-lg': 'shadows', 'box-shadow-inset': 'shadows',

        # Components
        'btn-padding-y': 'components', 'btn-padding-x': 'components',
        'btn-font-size': 'components', 'btn-border-radius': 'components',
        'input-padding-y': 'components', 'input-padding-x': 'components',
        'input-font-size': 'components', 'input-border-radius': 'components',
        'input-bg': 'components', 'input-color': 'components',
        'input-border-color': 'components',
        'card-spacer-y': 'components', 'card-spacer-x': 'components',
        'card-border-radius': 'components', 'card-border-width': 'components',
        'card-bg': 'components', 'card-cap-bg': 'components',
        'modal-inner-padding': 'components', 'modal-content-border-radius': 'components',
        'navbar-padding-y': 'components', 'navbar-padding-x': 'components',
        'nav-link-padding-y': 'components', 'nav-link-padding-x': 'components',
        'alert-padding-y': 'components', 'alert-padding-x': 'components',
        'alert-border-radius': 'components',
        'tooltip-padding-y': 'components', 'tooltip-padding-x': 'components',
        'dropdown-padding-y': 'components', 'dropdown-min-width': 'components',

        # Enable flags
        'enable-rounded': 'flags', 'enable-shadows': 'flags',
        'enable-gradients': 'flags', 'enable-transitions': 'flags',
        'enable-reduced-motion': 'flags', 'enable-smooth-scroll': 'flags',
        'enable-grid-classes': 'flags', 'enable-container-classes': 'flags',
        'enable-caret': 'flags', 'enable-button-pointers': 'flags',
        'enable-rfs': 'flags', 'enable-validation-icons': 'flags',
        'enable-negative-margins': 'flags', 'enable-deprecation-messages': 'flags',
        'enable-important-utilities': 'flags', 'enable-dark-mode': 'flags',
        'enable-cssgrid': 'flags',

        # Transitions
        'transition-base': 'transitions', 'transition-fade': 'transitions',
        'transition-collapse': 'transitions', 'transition-collapse-width': 'transitions',
    }

    # Bootswatch theme names
    BOOTSWATCH_THEMES = [
        'cerulean', 'cosmo', 'cyborg', 'darkly', 'flatly',
        'journal', 'litera', 'lumen', 'lux', 'materia',
        'minty', 'morph', 'pulse', 'quartz', 'sandstone',
        'simplex', 'sketchy', 'slate', 'solar', 'spacelab',
        'superhero', 'united', 'vapor', 'yeti', 'zephyr',
    ]

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Bootstrap theme customization from source code.

        Args:
            content: Source code content (SCSS, CSS, HTML, JS)
            file_path: Path to source file

        Returns:
            Dict with 'themes', 'variables', 'color_modes' keys
        """
        themes: List[BootstrapThemeInfo] = []
        variables: List[BootstrapVariableInfo] = []
        color_modes: List[BootstrapColorModeInfo] = []

        if not content or not content.strip():
            return {
                'themes': themes,
                'variables': variables,
                'color_modes': color_modes,
            }

        # Extract SCSS variable overrides
        if file_path.endswith(('.scss', '.sass')):
            self._extract_scss_variables(content, file_path, variables)

        # Extract CSS custom properties
        self._extract_css_custom_properties(content, file_path, variables)

        # Detect Bootswatch
        self._detect_bootswatch(content, file_path, themes)

        # Detect color modes
        self._extract_color_modes(content, file_path, color_modes)

        # Build theme info from variables
        if variables:
            has_custom_colors = any(
                v.category == 'colors' for v in variables
            )
            has_custom_typography = any(
                v.category == 'typography' for v in variables
            )
            has_custom_spacing = any(
                v.category == 'spacing' for v in variables
            )
            has_custom_breakpoints = any(
                v.category == 'grid' for v in variables
            )

            theme = BootstrapThemeInfo(
                name="custom",
                file=file_path,
                line_number=variables[0].line_number if variables else 0,
                method="scss-variables" if any(
                    not v.is_custom_property for v in variables
                ) else "css-variables",
                has_custom_colors=has_custom_colors,
                has_custom_breakpoints=has_custom_breakpoints,
                has_custom_spacing=has_custom_spacing,
                has_custom_typography=has_custom_typography,
                has_dark_mode=any(cm.mode == 'dark' for cm in color_modes),
                has_color_modes=len(color_modes) > 0,
                variable_count=len(variables),
                custom_properties=[v.variable_name for v in variables[:20]],
            )
            themes.append(theme)

        return {
            'themes': themes,
            'variables': variables,
            'color_modes': color_modes,
        }

    def _extract_scss_variables(
        self, content: str, file_path: str,
        variables: List[BootstrapVariableInfo]
    ):
        """Extract SCSS variable overrides."""
        # Pattern: $variable-name: value;
        var_pattern = re.compile(
            r'^\s*\$([a-zA-Z][\w-]*)\s*:\s*(.+?)\s*(?:!default\s*)?;',
            re.MULTILINE
        )

        for m in var_pattern.finditer(content):
            var_name = m.group(1)
            value = m.group(2).strip()
            line_num = content[:m.start()].count('\n') + 1

            # Determine category
            category = ''
            for key, cat in self.SCSS_VARIABLE_CATEGORIES.items():
                if var_name == key or var_name.startswith(key + '-'):
                    category = cat
                    break

            # Check if it's a Bootstrap override
            is_override = '!default' not in m.group(0)

            variables.append(BootstrapVariableInfo(
                variable_name=f'${var_name}',
                file=file_path,
                line_number=line_num,
                value=value[:100],
                category=category,
                is_custom_property=False,
                is_override=is_override,
            ))

    def _extract_css_custom_properties(
        self, content: str, file_path: str,
        variables: List[BootstrapVariableInfo]
    ):
        """Extract CSS custom property overrides."""
        # Pattern: --bs-variable: value;
        var_pattern = re.compile(
            r'--bs-([\w-]+)\s*:\s*([^;]+);',
            re.MULTILINE
        )

        for m in var_pattern.finditer(content):
            var_name = m.group(1)
            value = m.group(2).strip()
            line_num = content[:m.start()].count('\n') + 1

            # Determine category
            category = ''
            for key, cat in self.SCSS_VARIABLE_CATEGORIES.items():
                if var_name == key or var_name.startswith(key + '-'):
                    category = cat
                    break
            if not category:
                if 'color' in var_name or 'rgb' in var_name:
                    category = 'colors'
                elif 'font' in var_name:
                    category = 'typography'
                elif 'border' in var_name or 'radius' in var_name:
                    category = 'borders'
                elif 'shadow' in var_name:
                    category = 'shadows'

            variables.append(BootstrapVariableInfo(
                variable_name=f'--bs-{var_name}',
                file=file_path,
                line_number=line_num,
                value=value[:100],
                category=category,
                is_custom_property=True,
                is_override=True,
            ))

    def _detect_bootswatch(
        self, content: str, file_path: str,
        themes: List[BootstrapThemeInfo]
    ):
        """Detect Bootswatch theme usage."""
        # Check for bootswatch import
        bootswatch_pattern = re.compile(
            r"bootswatch[/\\]dist[/\\](\w+)|"
            r"from\s+['\"]bootswatch['/\"]|"
            r"require\(['\"]bootswatch|"
            r"@import\s+['\"].*bootswatch.*(\w+)",
            re.IGNORECASE
        )
        for m in bootswatch_pattern.finditer(content):
            theme_name = m.group(1) or m.group(2) or 'unknown'
            line_num = content[:m.start()].count('\n') + 1
            themes.append(BootstrapThemeInfo(
                name=f'bootswatch-{theme_name}',
                file=file_path,
                line_number=line_num,
                method='bootswatch',
            ))

        # Check for CDN links to bootswatch
        cdn_pattern = re.compile(
            r'bootswatch\.com[/\\](\d+(?:\.\d+)*)[/\\](\w+)',
            re.IGNORECASE
        )
        for m in cdn_pattern.finditer(content):
            version = m.group(1)
            theme_name = m.group(2)
            line_num = content[:m.start()].count('\n') + 1
            themes.append(BootstrapThemeInfo(
                name=f'bootswatch-{theme_name}',
                file=file_path,
                line_number=line_num,
                method='bootswatch',
                bootstrap_version=f'v{version.split(".")[0]}',
            ))

    def _extract_color_modes(
        self, content: str, file_path: str,
        color_modes: List[BootstrapColorModeInfo]
    ):
        """Extract Bootstrap 5.3+ color mode usage."""
        # data-bs-theme attribute
        theme_attr_pattern = re.compile(
            r'data-bs-theme\s*=\s*["\'](\w+)["\']',
            re.IGNORECASE
        )
        for m in theme_attr_pattern.finditer(content):
            mode = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            color_modes.append(BootstrapColorModeInfo(
                mode=mode,
                file=file_path,
                line_number=line_num,
                method='data-bs-theme',
            ))

        # prefers-color-scheme in CSS
        if 'prefers-color-scheme' in content:
            pcs_pattern = re.compile(
                r'prefers-color-scheme\s*:\s*(\w+)',
                re.IGNORECASE
            )
            for m in pcs_pattern.finditer(content):
                mode = m.group(1)
                line_num = content[:m.start()].count('\n') + 1
                color_modes.append(BootstrapColorModeInfo(
                    mode=mode,
                    file=file_path,
                    line_number=line_num,
                    method='prefers-color-scheme',
                ))

        # JavaScript theme toggle
        js_toggle_pattern = re.compile(
            r'(?:setAttribute|dataset)\s*[.(]\s*["\']'
            r'(?:data-bs-theme|bsTheme)["\']',
            re.IGNORECASE
        )
        for m in js_toggle_pattern.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            color_modes.append(BootstrapColorModeInfo(
                mode='auto',
                file=file_path,
                line_number=line_num,
                method='js-toggle',
                has_toggle=True,
            ))
