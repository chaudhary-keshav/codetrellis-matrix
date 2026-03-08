"""
shadcn/ui Theme Extractor for CodeTrellis

Extracts shadcn/ui theme configuration from:
- components.json (shadcn/ui registry configuration)
- CSS variables in globals.css / app.css (HSL color tokens)
- tailwind.config.{js,ts,mjs,cjs} with shadcn/ui extensions
- Dark mode configuration (class-based via next-themes or manual)

Theme system:
- CSS variables for colors using HSL format (--background, --foreground,
    --primary, --secondary, --destructive, --muted, --accent, --popover,
    --card, --border, --input, --ring, --chart-1..5)
- Dark mode via .dark class selector
- Tailwind CSS integration with CSS variable references
- components.json config: style, rsc, tsx, aliases, tailwind config

Supports:
- shadcn/ui v0.x (initial release with manual theme setup)
- shadcn/ui v1.x-v2.x (components.json, CSS variable theming)
- shadcn/ui v3.x/latest (new CSS variables for charts, sidebar, registry)

Part of CodeTrellis v4.39 - shadcn/ui Framework Support
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ShadcnThemeInfo:
    """Information about shadcn/ui theme configuration."""
    name: str = "default"
    file: str = ""
    line_number: int = 0
    style: str = ""              # "default" or "new-york" (v2+)
    has_dark_mode: bool = False
    has_css_variables: bool = False
    has_chart_colors: bool = False
    has_sidebar_tokens: bool = False
    color_tokens: List[str] = field(default_factory=list)  # --background, --primary, etc.
    radius_token: str = ""       # --radius value
    font_tokens: List[str] = field(default_factory=list)
    custom_tokens: List[str] = field(default_factory=list)


@dataclass
class ShadcnCSSVariableInfo:
    """Information about a CSS variable used in shadcn/ui theming."""
    variable_name: str           # --background, --primary, etc.
    file: str = ""
    line_number: int = 0
    value: str = ""              # HSL value or reference
    category: str = ""           # color, spacing, radius, font
    is_dark_mode: bool = False   # Defined in .dark {} scope
    is_chart: bool = False       # Chart color (--chart-1..5)
    is_sidebar: bool = False     # Sidebar token (--sidebar-*)


@dataclass
class ShadcnComponentsJsonInfo:
    """Information from components.json registry configuration."""
    file: str = ""
    style: str = ""              # "default", "new-york"
    rsc: bool = False            # React Server Components support
    tsx: bool = True             # TypeScript support
    tailwind_css: str = ""       # Path to tailwind CSS file
    tailwind_config: str = ""    # Path to tailwind config
    tailwind_prefix: str = ""    # Tailwind prefix (if any)
    tailwind_base_color: str = "" # Base color (slate, gray, zinc, etc.)
    components_alias: str = ""   # @/components
    utils_alias: str = ""        # @/lib/utils
    ui_alias: str = ""           # @/components/ui
    hooks_alias: str = ""        # @/hooks
    lib_alias: str = ""          # @/lib
    icon_library: str = ""       # lucide (default) or other
    registry_url: str = ""       # Custom registry URL


class ShadcnThemeExtractor:
    """
    Extracts shadcn/ui theme configuration from CSS and config files.

    Detects:
    - CSS variables in :root and .dark selectors
    - components.json registry configuration
    - Tailwind CSS config with shadcn/ui extensions
    - Theme color tokens (HSL format)
    - Border radius tokens
    - Chart color tokens
    - Sidebar tokens
    """

    # CSS variable pattern for shadcn/ui tokens
    CSS_VAR_RE = re.compile(
        r'--(\w[\w-]*)\s*:\s*([^;]+);',
        re.MULTILINE,
    )

    # Dark mode selector
    DARK_MODE_RE = re.compile(
        r'\.dark\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
        re.DOTALL,
    )

    # Root selector for light mode vars
    ROOT_SELECTOR_RE = re.compile(
        r':root\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
        re.DOTALL,
    )

    # @layer base pattern for modern CSS
    LAYER_BASE_RE = re.compile(
        r'@layer\s+base\s*\{([\s\S]*?)\}(?:\s*\})?',
        re.DOTALL,
    )

    # shadcn/ui core CSS variable names
    CORE_CSS_VARIABLES = {
        'background', 'foreground',
        'card', 'card-foreground',
        'popover', 'popover-foreground',
        'primary', 'primary-foreground',
        'secondary', 'secondary-foreground',
        'muted', 'muted-foreground',
        'accent', 'accent-foreground',
        'destructive', 'destructive-foreground',
        'border', 'input', 'ring',
        'radius',
    }

    # Chart CSS variables (v2+)
    CHART_CSS_VARIABLES = {
        'chart-1', 'chart-2', 'chart-3', 'chart-4', 'chart-5',
    }

    # Sidebar CSS variables (v2+)
    SIDEBAR_CSS_VARIABLES = {
        'sidebar-background', 'sidebar-foreground',
        'sidebar-primary', 'sidebar-primary-foreground',
        'sidebar-accent', 'sidebar-accent-foreground',
        'sidebar-border', 'sidebar-ring',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract shadcn/ui theme information from source content.

        Args:
            content: Source file content (CSS, JSON, or JS/TS config)
            file_path: Path to source file

        Returns:
            Dict with theme info, CSS variables, and components.json info
        """
        result: Dict[str, Any] = {
            'themes': [],
            'css_variables': [],
            'components_json': None,
        }

        if not content or not content.strip():
            return result

        normalized_path = file_path.replace('\\', '/')

        # Parse components.json
        if normalized_path.endswith('components.json'):
            comp_json = self._parse_components_json(content, file_path)
            if comp_json:
                result['components_json'] = comp_json
            return result

        # Parse CSS files for theme variables
        if any(normalized_path.endswith(ext) for ext in (
            '.css', '.scss', '.sass', '.less'
        )):
            theme, css_vars = self._extract_css_theme(content, file_path)
            if theme:
                result['themes'].append(theme)
            result['css_variables'] = css_vars
            return result

        # Parse tailwind config for shadcn/ui extensions
        if 'tailwind.config' in normalized_path:
            theme = self._extract_tailwind_theme(content, file_path)
            if theme:
                result['themes'].append(theme)

        return result

    def _parse_components_json(
        self, content: str, file_path: str
    ) -> Optional[ShadcnComponentsJsonInfo]:
        """Parse shadcn/ui components.json configuration."""
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return None

        info = ShadcnComponentsJsonInfo(file=file_path)

        # Core fields
        info.style = data.get('style', '')
        info.rsc = data.get('rsc', False)
        info.tsx = data.get('tsx', True)
        info.icon_library = data.get('iconLibrary', '')
        info.registry_url = data.get('registryUrl', '')

        # Tailwind config
        tailwind = data.get('tailwind', {})
        if isinstance(tailwind, dict):
            info.tailwind_config = tailwind.get('config', '')
            info.tailwind_css = tailwind.get('css', '')
            info.tailwind_prefix = tailwind.get('prefix', '')
            info.tailwind_base_color = tailwind.get('baseColor', '')

        # Aliases
        aliases = data.get('aliases', {})
        if isinstance(aliases, dict):
            info.components_alias = aliases.get('components', '')
            info.utils_alias = aliases.get('utils', '')
            info.ui_alias = aliases.get('ui', '')
            info.hooks_alias = aliases.get('hooks', '')
            info.lib_alias = aliases.get('lib', '')

        return info

    def _extract_css_theme(
        self, content: str, file_path: str
    ) -> tuple:
        """Extract theme info and CSS variables from CSS file."""
        theme = ShadcnThemeInfo(file=file_path)
        css_vars: List[ShadcnCSSVariableInfo] = []

        # Check for :root variables
        root_match = self.ROOT_SELECTOR_RE.search(content)
        if not root_match:
            # Try @layer base
            layer_match = self.LAYER_BASE_RE.search(content)
            if layer_match:
                layer_content = layer_match.group(1)
                root_in_layer = re.search(
                    r':root\s*\{([^}]+)\}', layer_content, re.DOTALL
                )
                if root_in_layer:
                    root_match = root_in_layer

        if root_match:
            root_content = root_match.group(1)
            for var_match in self.CSS_VAR_RE.finditer(root_content):
                var_name = var_match.group(1)
                var_value = var_match.group(2).strip()

                if var_name in self.CORE_CSS_VARIABLES:
                    theme.has_css_variables = True
                    theme.color_tokens.append(f"--{var_name}")

                    if var_name == 'radius':
                        theme.radius_token = var_value

                category = self._categorize_variable(var_name)
                is_chart = var_name in self.CHART_CSS_VARIABLES
                is_sidebar = var_name in self.SIDEBAR_CSS_VARIABLES

                if is_chart:
                    theme.has_chart_colors = True
                if is_sidebar:
                    theme.has_sidebar_tokens = True

                line_num = content[:var_match.start()].count('\n') + 1
                css_vars.append(ShadcnCSSVariableInfo(
                    variable_name=f"--{var_name}",
                    file=file_path,
                    line_number=line_num,
                    value=var_value,
                    category=category,
                    is_dark_mode=False,
                    is_chart=is_chart,
                    is_sidebar=is_sidebar,
                ))

        # Check for dark mode variables
        dark_match = self.DARK_MODE_RE.search(content)
        if not dark_match:
            # Try inside @layer base
            layer_match = self.LAYER_BASE_RE.search(content)
            if layer_match:
                dark_in_layer = re.search(
                    r'\.dark\s*\{([^}]+)\}', layer_match.group(1), re.DOTALL
                )
                if dark_in_layer:
                    dark_match = dark_in_layer

        if dark_match:
            theme.has_dark_mode = True
            dark_content = dark_match.group(1)
            for var_match in self.CSS_VAR_RE.finditer(dark_content):
                var_name = var_match.group(1)
                var_value = var_match.group(2).strip()

                category = self._categorize_variable(var_name)
                is_chart = var_name in self.CHART_CSS_VARIABLES
                is_sidebar = var_name in self.SIDEBAR_CSS_VARIABLES

                css_vars.append(ShadcnCSSVariableInfo(
                    variable_name=f"--{var_name}",
                    file=file_path,
                    line_number=0,
                    value=var_value,
                    category=category,
                    is_dark_mode=True,
                    is_chart=is_chart,
                    is_sidebar=is_sidebar,
                ))

        # Detect shadcn/ui style
        if any(v.variable_name == '--radius' for v in css_vars):
            theme.style = 'default'
        if theme.has_css_variables:
            theme.line_number = 1

        return (theme if theme.has_css_variables else None, css_vars)

    def _extract_tailwind_theme(
        self, content: str, file_path: str
    ) -> Optional[ShadcnThemeInfo]:
        """Extract shadcn/ui theme config from tailwind.config file."""
        # Check for shadcn/ui CSS variable references in tailwind config
        has_shadcn = (
            'hsl(var(--' in content or
            'var(--' in content or
            'shadcn' in content.lower() or
            'cssVariables' in content
        )

        if not has_shadcn:
            return None

        theme = ShadcnThemeInfo(
            name="tailwind-config",
            file=file_path,
            line_number=1,
        )

        # Detect CSS variable references
        var_refs = re.findall(r'hsl\(var\(--(\w[\w-]*)\)', content)
        for var_name in set(var_refs):
            theme.color_tokens.append(f"--{var_name}")
            if var_name in self.CORE_CSS_VARIABLES:
                theme.has_css_variables = True
            if var_name in self.CHART_CSS_VARIABLES:
                theme.has_chart_colors = True
            if var_name in self.SIDEBAR_CSS_VARIABLES:
                theme.has_sidebar_tokens = True

        # darkMode detection
        if re.search(r"""darkMode\s*:\s*['"\[]*class""", content):
            theme.has_dark_mode = True
        elif 'class' in content and 'darkMode' in content:
            theme.has_dark_mode = True

        return theme

    def _categorize_variable(self, var_name: str) -> str:
        """Categorize a CSS variable name."""
        if var_name in ('radius',):
            return 'radius'
        if var_name.startswith('chart-'):
            return 'chart'
        if var_name.startswith('sidebar-'):
            return 'sidebar'
        if 'font' in var_name:
            return 'font'
        if var_name in ('border', 'input', 'ring'):
            return 'border'
        return 'color'
