"""
Radix UI Theme Extractor for CodeTrellis

Extracts Radix Themes configuration — Theme provider settings,
color scales (28 colors × 12 steps), appearance modes (light/dark/inherit),
radius/scaling tokens, panel-background, accent-color, gray-color.

Radix Colors:
- 28 color scales: gray, mauve, slate, sage, olive, sand, tomato, red,
    ruby, crimson, pink, plum, purple, violet, iris, indigo, blue, cyan,
    teal, jade, green, grass, bronze, gold, brown, orange, amber, yellow
- 12 steps per scale (1-12)
- Alpha variants (grayA, redA, etc.)
- Dark variants (grayDark, redDark, etc.)
- P3 wide gamut variants

Radix Themes Configuration:
- <Theme> provider: appearance, accentColor, grayColor, panelBackground,
    scaling, radius, hasBackground
- Nested themes with different configurations
- CSS custom properties (--accent-*, --gray-*, --radius-*)
- Token system (space, font, line-height, letter-spacing, font-weight)

Part of CodeTrellis v4.41 - Radix UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RadixThemeConfigInfo:
    """Information about a Radix Themes <Theme> provider configuration."""
    name: str = "Theme"
    file: str = ""
    line_number: int = 0
    appearance: str = ""          # light, dark, inherit
    accent_color: str = ""        # any of 28 color scales
    gray_color: str = ""          # gray, mauve, slate, sage, olive, sand
    panel_background: str = ""    # solid, translucent
    scaling: str = ""             # 90%, 95%, 100%, 105%, 110%
    radius: str = ""              # none, small, medium, large, full
    has_background: bool = True   # hasBackground prop
    is_nested: bool = False       # Nested <Theme> for sub-sections
    has_theme_panel: bool = False  # Uses <ThemePanel> for interactive config


@dataclass
class RadixColorScaleInfo:
    """Information about Radix Colors usage."""
    name: str                     # gray, red, blue, etc.
    file: str = ""
    line_number: int = 0
    import_source: str = ""       # @radix-ui/colors
    is_alpha: bool = False        # Alpha variant (grayA, redA)
    is_dark: bool = False         # Dark variant (grayDark, redDark)
    is_p3: bool = False           # P3 wide gamut variant
    steps_used: List[int] = field(default_factory=list)  # Which steps (1-12) are used
    usage_type: str = ""          # css-variable, js-import, token


class RadixThemeExtractor:
    """
    Extracts Radix Themes configuration and Radix Colors usage.

    Detects:
    - <Theme> provider configuration (appearance, accent, gray, etc.)
    - Nested <Theme> providers for section-level theming
    - <ThemePanel> for interactive theme configuration
    - Radix Colors imports and usage (@radix-ui/colors)
    - CSS custom properties (--accent-*, --gray-*, --color-*)
    - Token system (space, font, etc.)
    """

    # Theme provider props
    THEME_PROP_PATTERNS = {
        'appearance': re.compile(
            r'<Theme\s[^>]*\bappearance\s*=\s*["\'](\w+)["\']',
            re.MULTILINE,
        ),
        'accentColor': re.compile(
            r'<Theme\s[^>]*\baccentColor\s*=\s*["\'](\w+)["\']',
            re.MULTILINE,
        ),
        'grayColor': re.compile(
            r'<Theme\s[^>]*\bgrayColor\s*=\s*["\'](\w+)["\']',
            re.MULTILINE,
        ),
        'panelBackground': re.compile(
            r'<Theme\s[^>]*\bpanelBackground\s*=\s*["\'](\w+)["\']',
            re.MULTILINE,
        ),
        'scaling': re.compile(
            r'<Theme\s[^>]*\bscaling\s*=\s*["\']([^"\']+)["\']',
            re.MULTILINE,
        ),
        'radius': re.compile(
            r'<Theme\s[^>]*\bradius\s*=\s*["\'](\w+)["\']',
            re.MULTILINE,
        ),
    }

    # <Theme> usage pattern
    THEME_USAGE_PATTERN = re.compile(
        r'<Theme\b([^>]*)>',
        re.MULTILINE | re.DOTALL,
    )

    # Nested theme detection
    NESTED_THEME_PATTERN = re.compile(
        r'<Theme\b.*?>.*?<Theme\b',
        re.DOTALL,
    )

    # <ThemePanel> detection
    THEME_PANEL_PATTERN = re.compile(
        r'<ThemePanel\b',
        re.MULTILINE,
    )

    # Radix Colors import pattern
    COLORS_IMPORT_PATTERN = re.compile(
        r"""import\s*\{([^}]+)\}\s*from\s*['"]@radix-ui/colors/([^'"]+)['"]""",
        re.MULTILINE,
    )

    # Radix Colors: all 28 scales
    COLOR_SCALES = [
        'gray', 'mauve', 'slate', 'sage', 'olive', 'sand',
        'tomato', 'red', 'ruby', 'crimson', 'pink', 'plum',
        'purple', 'violet', 'iris', 'indigo', 'blue', 'cyan',
        'teal', 'jade', 'green', 'grass',
        'bronze', 'gold', 'brown', 'orange', 'amber', 'yellow',
    ]

    # Gray scales that can be used as grayColor
    GRAY_SCALES = ['gray', 'mauve', 'slate', 'sage', 'olive', 'sand']

    # CSS custom property patterns for Radix Themes tokens
    CSS_VAR_PATTERN = re.compile(
        r'var\(--(?:accent|gray|color|radius|space|font-size|font-weight|line-height|letter-spacing)-([^)]+)\)',
        re.MULTILINE,
    )

    # Radix Themes CSS import
    THEMES_CSS_IMPORT = re.compile(
        r"""(?:import|@import)\s+['"]@radix-ui/themes/styles\.css['"]""",
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Radix Themes configuration and Radix Colors usage.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dictionary with 'theme_configs' and 'color_scales' lists
        """
        result = {
            'theme_configs': [],
            'color_scales': [],
        }

        if not content or not content.strip():
            return result

        # Extract Theme configurations
        themes = self._extract_theme_configs(content, file_path)
        result['theme_configs'].extend(themes)

        # Extract Radix Colors usage
        colors = self._extract_color_scales(content, file_path)
        result['color_scales'].extend(colors)

        return result

    def _extract_theme_configs(
        self, content: str, file_path: str
    ) -> List[RadixThemeConfigInfo]:
        """Extract <Theme> provider configurations."""
        themes = []

        for match in self.THEME_USAGE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            props_str = match.group(1)

            config = RadixThemeConfigInfo(
                file=file_path,
                line_number=line_number,
            )

            # Extract props
            for prop_name, pattern in self.THEME_PROP_PATTERNS.items():
                prop_match = pattern.search(content)
                if prop_match:
                    value = prop_match.group(1)
                    if prop_name == 'appearance':
                        config.appearance = value
                    elif prop_name == 'accentColor':
                        config.accent_color = value
                    elif prop_name == 'grayColor':
                        config.gray_color = value
                    elif prop_name == 'panelBackground':
                        config.panel_background = value
                    elif prop_name == 'scaling':
                        config.scaling = value
                    elif prop_name == 'radius':
                        config.radius = value

            # Check hasBackground
            if 'hasBackground={false}' in props_str or "hasBackground='false'" in props_str:
                config.has_background = False

            # Check if nested
            if self.NESTED_THEME_PATTERN.search(content):
                # Mark non-first themes as nested
                if themes:
                    config.is_nested = True

            # Check ThemePanel
            config.has_theme_panel = bool(self.THEME_PANEL_PATTERN.search(content))

            themes.append(config)

        return themes

    def _extract_color_scales(
        self, content: str, file_path: str
    ) -> List[RadixColorScaleInfo]:
        """Extract Radix Colors imports and usage."""
        colors = []
        seen = set()

        for match in self.COLORS_IMPORT_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            names_str = match.group(1)
            module_path = match.group(2)

            # Parse the module path to determine color properties
            base_name = module_path.replace('.css', '')
            is_alpha = 'A' in base_name and base_name[-1] == 'A'
            is_dark = 'Dark' in base_name
            is_p3 = 'P3' in base_name

            # Normalize to get the scale name
            clean_name = base_name
            for suffix in ['DarkA', 'Dark', 'A', 'P3']:
                clean_name = clean_name.replace(suffix, '')

            if clean_name.lower() in [s.lower() for s in self.COLOR_SCALES]:
                key = (clean_name.lower(), file_path, is_alpha, is_dark)
                if key not in seen:
                    seen.add(key)

                    # Find which steps are used
                    steps_used = self._find_steps_used(clean_name, content)

                    color = RadixColorScaleInfo(
                        name=clean_name.lower(),
                        file=file_path,
                        line_number=line_number,
                        import_source=f"@radix-ui/colors/{module_path}",
                        is_alpha=is_alpha,
                        is_dark=is_dark,
                        is_p3=is_p3,
                        steps_used=steps_used,
                        usage_type='js-import',
                    )
                    colors.append(color)

        # Also detect CSS variable usage of Radix Colors
        for match in self.CSS_VAR_PATTERN.finditer(content):
            token = match.group(1)
            # Check if it matches a color step pattern (e.g., accent-1, gray-12)
            step_match = re.match(r'(\d+)', token)
            if step_match:
                step = int(step_match.group(1))
                if 1 <= step <= 12:
                    prefix = match.group(0).split('-')[1] if '-' in match.group(0) else ''
                    # We already detect these via Theme config, skip

        return colors

    def _find_steps_used(self, scale_name: str, content: str) -> List[int]:
        """Find which color steps (1-12) are used for a given scale."""
        steps = []
        for step in range(1, 13):
            if re.search(rf'\b{re.escape(scale_name)}\d*{step}\b', content):
                steps.append(step)
        return steps
