"""
Tailwind CSS Theme Extractor v1.0

Extracts Tailwind theme configuration: design tokens, color palettes,
spacing scales, typography settings, and screen breakpoints.

Supports:
- v1-v3: theme/extend in tailwind.config.js/ts
- v4: @theme directive in CSS, CSS custom properties
- Color palette extraction (named colors, custom colors)
- Spacing scale extraction
- Screen breakpoint extraction
- Typography / font family extraction
- Animation / keyframe theme tokens

Part of CodeTrellis v4.35 - Tailwind CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class TailwindThemeTokenInfo:
    """Information about a Tailwind theme token."""
    key: str = ""
    value: str = ""
    category: str = ""  # colors, spacing, screens, fontSize, fontFamily, etc.
    is_extended: bool = False  # True if in theme.extend, False if override
    is_css_variable: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class TailwindColorInfo:
    """Information about a Tailwind color definition."""
    name: str = ""
    shades: Dict[str, str] = field(default_factory=dict)  # { "50": "#...", "100": "#...", ... }
    is_custom: bool = False
    color_format: str = ""  # hex, rgb, hsl, oklch
    file: str = ""
    line_number: int = 0


@dataclass
class TailwindScreenInfo:
    """Information about a Tailwind screen/breakpoint."""
    name: str = ""
    value: str = ""
    min_width: str = ""
    max_width: str = ""
    is_custom: bool = False
    file: str = ""
    line_number: int = 0


class TailwindThemeExtractor:
    """
    Extracts Tailwind theme configuration and design tokens.

    Detects:
    - Color palettes (custom and extended)
    - Spacing scales
    - Screen breakpoints
    - Typography tokens (font families, font sizes)
    - Border radius tokens
    - Animation tokens
    - v4 @theme directive tokens (CSS custom properties)
    """

    # Default Tailwind screens
    DEFAULT_SCREENS = {
        'sm': '640px', 'md': '768px', 'lg': '1024px',
        'xl': '1280px', '2xl': '1536px',
    }

    # Default Tailwind colors
    DEFAULT_COLORS = {
        'slate', 'gray', 'zinc', 'neutral', 'stone',
        'red', 'orange', 'amber', 'yellow', 'lime',
        'green', 'emerald', 'teal', 'cyan', 'sky',
        'blue', 'indigo', 'violet', 'purple', 'fuchsia',
        'pink', 'rose', 'white', 'black', 'transparent',
        'current', 'inherit',
    }

    # Theme key patterns in config
    THEME_KEY_PATTERN = re.compile(
        r'(\w+)\s*:\s*(?:\{|\[|["\'])',
        re.MULTILINE
    )

    # CSS variable pattern for v4 @theme
    CSS_VAR_PATTERN = re.compile(
        r'--(\w[\w-]*)\s*:\s*([^;]+);',
        re.MULTILINE
    )

    # Color hex pattern
    COLOR_HEX_PATTERN = re.compile(
        r'["\']?(\w+)["\']?\s*:\s*["\']?(#[0-9a-fA-F]{3,8})["\']?',
        re.MULTILINE
    )

    # Color shade object pattern
    COLOR_SHADE_PATTERN = re.compile(
        r'["\']?(\w+)["\']?\s*:\s*\{([^}]+)\}',
        re.MULTILINE | re.DOTALL
    )

    # Screen definition pattern
    SCREEN_PATTERN = re.compile(
        r'["\']?(\w+)["\']?\s*:\s*["\']?(\d+(?:px|rem|em))["\']?',
        re.MULTILINE
    )

    # Font family pattern
    FONT_FAMILY_PATTERN = re.compile(
        r'["\']?(\w+)["\']?\s*:\s*\[([^\]]+)\]',
        re.MULTILINE | re.DOTALL
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Tailwind theme tokens from content.

        Args:
            content: Config file or CSS content.
            file_path: Path to the file.

        Returns:
            Dict with extracted theme info.
        """
        result: Dict[str, Any] = {
            'tokens': [],
            'colors': [],
            'screens': [],
            'stats': {},
        }

        if not content or not content.strip():
            return result

        is_css = file_path.lower().endswith('.css') if file_path else False

        if is_css:
            result['tokens'] = self._extract_css_theme_tokens(content, file_path)
        else:
            result['tokens'] = self._extract_js_theme_tokens(content, file_path)

        result['colors'] = self._extract_colors(content, file_path)
        result['screens'] = self._extract_screens(content, file_path)

        # Stats
        result['stats'] = {
            'total_tokens': len(result['tokens']),
            'total_custom_colors': len(result['colors']),
            'total_screens': len(result['screens']),
            'token_categories': list(set(t.category for t in result['tokens'] if t.category)),
        }

        return result

    def _extract_css_theme_tokens(self, content: str, file_path: str) -> List[TailwindThemeTokenInfo]:
        """Extract theme tokens from v4 CSS @theme blocks."""
        results: List[TailwindThemeTokenInfo] = []

        # Find @theme blocks
        theme_pattern = re.compile(r'@theme\s*(?:inline\s*)?\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
                                   re.MULTILINE | re.DOTALL)

        for tm in theme_pattern.finditer(content):
            body = tm.group(1)
            base_line = content[:tm.start()].count('\n') + 1

            for vm in self.CSS_VAR_PATTERN.finditer(body):
                var_name = vm.group(1)
                var_value = vm.group(2).strip()
                line_num = base_line + body[:vm.start()].count('\n')

                # Categorize by variable name prefix
                category = self._categorize_css_var(var_name)

                results.append(TailwindThemeTokenInfo(
                    key=f"--{var_name}",
                    value=var_value[:60],
                    category=category,
                    is_css_variable=True,
                    file=file_path,
                    line_number=line_num,
                ))

        return results

    def _extract_js_theme_tokens(self, content: str, file_path: str) -> List[TailwindThemeTokenInfo]:
        """Extract theme tokens from JS/TS config."""
        results: List[TailwindThemeTokenInfo] = []

        # Find theme.extend block
        extend_match = re.search(
            r'extend\s*:\s*\{',
            content
        )
        if extend_match:
            start = extend_match.end()
            brace_count = 1
            pos = start
            while pos < len(content) and brace_count > 0:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                pos += 1

            if brace_count == 0:
                body = content[start:pos - 1]
                base_line = content[:extend_match.start()].count('\n') + 1

                # Extract top-level keys
                for km in self.THEME_KEY_PATTERN.finditer(body):
                    key = km.group(1)
                    line_num = base_line + body[:km.start()].count('\n')
                    results.append(TailwindThemeTokenInfo(
                        key=key,
                        category=self._categorize_theme_key(key),
                        is_extended=True,
                        file=file_path,
                        line_number=line_num,
                    ))

        return results

    def _extract_colors(self, content: str, file_path: str) -> List[TailwindColorInfo]:
        """Extract custom color definitions."""
        results: List[TailwindColorInfo] = []

        # Find colors block in theme
        colors_match = re.search(
            r'colors\s*:\s*\{',
            content
        )
        if not colors_match:
            return results

        start = colors_match.end()
        brace_count = 1
        pos = start
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1

        if brace_count != 0:
            return results

        body = content[start:pos - 1]
        base_line = content[:colors_match.start()].count('\n') + 1

        # Extract shade objects
        for m in self.COLOR_SHADE_PATTERN.finditer(body):
            name = m.group(1)
            shades_str = m.group(2)
            shades = {}
            for sm in re.finditer(r'["\']?(\w+)["\']?\s*:\s*["\']([^"\']+)["\']', shades_str):
                shades[sm.group(1)] = sm.group(2)

            if shades:
                line_num = base_line + body[:m.start()].count('\n')
                is_custom = name not in self.DEFAULT_COLORS
                # Detect color format
                first_val = list(shades.values())[0] if shades else ''
                color_format = self._detect_color_format(first_val)

                results.append(TailwindColorInfo(
                    name=name,
                    shades=shades,
                    is_custom=is_custom,
                    color_format=color_format,
                    file=file_path,
                    line_number=line_num,
                ))

        # Extract simple color values (not shade objects)
        for m in self.COLOR_HEX_PATTERN.finditer(body):
            name = m.group(1)
            value = m.group(2)
            # Skip if already captured as shade
            if not any(c.name == name for c in results):
                line_num = base_line + body[:m.start()].count('\n')
                results.append(TailwindColorInfo(
                    name=name,
                    shades={'DEFAULT': value},
                    is_custom=name not in self.DEFAULT_COLORS,
                    color_format=self._detect_color_format(value),
                    file=file_path,
                    line_number=line_num,
                ))

        return results

    def _extract_screens(self, content: str, file_path: str) -> List[TailwindScreenInfo]:
        """Extract screen/breakpoint definitions."""
        results: List[TailwindScreenInfo] = []

        # Find screens block in theme
        screens_match = re.search(
            r'screens\s*:\s*\{',
            content
        )
        if not screens_match:
            return results

        start = screens_match.end()
        brace_count = 1
        pos = start
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1

        if brace_count != 0:
            return results

        body = content[start:pos - 1]
        base_line = content[:screens_match.start()].count('\n') + 1

        for m in self.SCREEN_PATTERN.finditer(body):
            name = m.group(1)
            value = m.group(2)
            line_num = base_line + body[:m.start()].count('\n')
            is_custom = name not in self.DEFAULT_SCREENS
            results.append(TailwindScreenInfo(
                name=name,
                value=value,
                min_width=value,
                is_custom=is_custom,
                file=file_path,
                line_number=line_num,
            ))

        return results

    def _categorize_css_var(self, var_name: str) -> str:
        """Categorize a CSS variable from @theme by name prefix."""
        name = var_name.lower()
        if 'color' in name:
            return 'colors'
        elif 'spacing' in name or 'space' in name:
            return 'spacing'
        elif 'font' in name or 'text' in name:
            return 'typography'
        elif 'radius' in name:
            return 'borderRadius'
        elif 'shadow' in name:
            return 'boxShadow'
        elif 'screen' in name or 'breakpoint' in name:
            return 'screens'
        elif 'animate' in name or 'animation' in name or 'keyframe' in name:
            return 'animation'
        elif 'transition' in name:
            return 'transition'
        elif 'container' in name:
            return 'container'
        return 'other'

    def _categorize_theme_key(self, key: str) -> str:
        """Categorize a theme key from JS config."""
        mapping = {
            'colors': 'colors', 'backgroundColor': 'colors',
            'textColor': 'colors', 'borderColor': 'colors',
            'gradientColorStops': 'colors', 'ringColor': 'colors',
            'divideColor': 'colors', 'placeholderColor': 'colors',
            'spacing': 'spacing', 'padding': 'spacing',
            'margin': 'spacing', 'gap': 'spacing',
            'width': 'sizing', 'height': 'sizing',
            'maxWidth': 'sizing', 'maxHeight': 'sizing',
            'minWidth': 'sizing', 'minHeight': 'sizing',
            'fontSize': 'typography', 'fontFamily': 'typography',
            'fontWeight': 'typography', 'letterSpacing': 'typography',
            'lineHeight': 'typography',
            'screens': 'screens', 'container': 'container',
            'borderRadius': 'borderRadius', 'borderWidth': 'borders',
            'boxShadow': 'boxShadow', 'dropShadow': 'boxShadow',
            'opacity': 'opacity',
            'zIndex': 'zIndex',
            'animation': 'animation', 'keyframes': 'animation',
            'transitionDuration': 'transition',
            'transitionTimingFunction': 'transition',
        }
        return mapping.get(key, 'other')

    def _detect_color_format(self, value: str) -> str:
        """Detect the format of a color value."""
        value = value.strip()
        if value.startswith('#'):
            return 'hex'
        elif value.startswith('rgb'):
            return 'rgb'
        elif value.startswith('hsl'):
            return 'hsl'
        elif value.startswith('oklch'):
            return 'oklch'
        elif value.startswith('oklab'):
            return 'oklab'
        return 'other'
