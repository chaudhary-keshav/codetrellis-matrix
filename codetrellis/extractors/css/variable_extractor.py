"""
CSS Variable Extractor for CodeTrellis

Extracts CSS custom properties (CSS variables), :root declarations,
theming patterns, and design token definitions.

Supports:
- CSS Custom Properties (--var-name)
- :root variable declarations
- var() function usage
- Theming via data attributes / media queries (prefers-color-scheme)
- Design token patterns
- Fallback values in var()
- SCSS $variables, Less @variables
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSSVariableInfo:
    """Information about a CSS variable (custom property)."""
    name: str
    value: str = ""
    file: str = ""
    line_number: int = 0
    scope: str = ":root"  # :root, element, media-query, etc.
    fallback: str = ""
    is_color: bool = False
    is_spacing: bool = False
    is_typography: bool = False
    is_theme_variable: bool = False
    category: str = ""  # color, spacing, typography, sizing, other
    usage_count: int = 0


@dataclass
class CSSThemeInfo:
    """Information about CSS theming patterns."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    strategy: str = ""  # data-attribute, media-query, class-based
    variables: List[str] = field(default_factory=list)
    supports_dark_mode: bool = False
    supports_light_mode: bool = False
    color_scheme_values: List[str] = field(default_factory=list)


class CSSVariableExtractor:
    """
    Extracts CSS custom properties and theming patterns.

    Detects:
    - CSS custom property declarations (--name: value)
    - var() usage with fallback values
    - :root scope variables (design tokens)
    - Theme switching via prefers-color-scheme
    - Theme switching via data-theme / data-color-scheme attributes
    - Color, spacing, typography token patterns
    """

    # Custom property declaration
    VAR_DECLARATION = re.compile(
        r'(--[\w-]+)\s*:\s*([^;{}]+?)\s*;',
        re.MULTILINE
    )

    # var() usage
    VAR_USAGE = re.compile(r'var\(\s*(--[\w-]+)(?:\s*,\s*([^)]+))?\s*\)')

    # :root block
    ROOT_BLOCK = re.compile(r':root\s*\{([^}]+)\}', re.DOTALL)

    # Dark mode patterns
    DARK_MODE_PATTERNS = [
        re.compile(r'@media\s*\(\s*prefers-color-scheme\s*:\s*dark\s*\)'),
        re.compile(r'\[data-theme\s*=\s*["\']dark["\']\]'),
        re.compile(r'\[data-color-scheme\s*=\s*["\']dark["\']\]'),
        re.compile(r'\.dark\s*\{'),
        re.compile(r'\.theme-dark\s*\{'),
    ]

    LIGHT_MODE_PATTERNS = [
        re.compile(r'@media\s*\(\s*prefers-color-scheme\s*:\s*light\s*\)'),
        re.compile(r'\[data-theme\s*=\s*["\']light["\']\]'),
        re.compile(r'\[data-color-scheme\s*=\s*["\']light["\']\]'),
        re.compile(r'\.light\s*\{'),
        re.compile(r'\.theme-light\s*\{'),
    ]

    # Color value patterns
    COLOR_PATTERNS = re.compile(
        r'(?:#[0-9a-fA-F]{3,8}|rgba?\s*\(|hsla?\s*\(|oklch\s*\(|oklab\s*\(|lch\s*\(|lab\s*\(|'
        r'color\s*\(|color-mix\s*\(|(?:transparent|currentColor|inherit)\b)',
        re.IGNORECASE
    )

    # Spacing patterns
    SPACING_PATTERNS = re.compile(r'(?:\d+(?:\.\d+)?(?:px|rem|em|vh|vw|%|ch|ex|vmin|vmax|cqi|cqb))')

    # Typography patterns
    TYPOGRAPHY_KEYWORDS = {'font-size', 'font-family', 'font-weight', 'line-height',
                           'letter-spacing', 'text'}

    # SCSS variable
    SCSS_VAR = re.compile(r'(\$[\w-]+)\s*:\s*([^;]+?)\s*;', re.MULTILINE)

    # Less variable
    LESS_VAR = re.compile(r'(@[\w-]+)\s*:\s*([^;]+?)\s*;', re.MULTILINE)

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract CSS variables, themes, and design tokens.

        Returns dict with:
          - variables: List[CSSVariableInfo]
          - themes: List[CSSThemeInfo]
          - var_usage: Dict mapping var name -> usage count
          - preprocessor_vars: List[CSSVariableInfo] (SCSS/Less)
          - stats: Dict with counts
        """
        variables: List[CSSVariableInfo] = []
        themes: List[CSSThemeInfo] = []
        var_usage: Dict[str, int] = {}
        preprocessor_vars: List[CSSVariableInfo] = []

        # Remove comments
        clean = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        clean = re.sub(r'//[^\n]*', '', clean)

        # Extract CSS custom property declarations
        for match in self.VAR_DECLARATION.finditer(clean):
            name = match.group(1)
            value = match.group(2).strip()
            line_num = clean[:match.start()].count('\n') + 1

            # Determine scope
            scope = self._determine_scope(clean, match.start())

            # Classify variable type
            is_color = bool(self.COLOR_PATTERNS.search(value))
            is_spacing = bool(self.SPACING_PATTERNS.search(value)) and any(
                kw in name for kw in ['spacing', 'space', 'gap', 'margin', 'padding', 'size']
            )
            is_typography = any(kw in name for kw in self.TYPOGRAPHY_KEYWORDS)
            is_theme = 'theme' in name or 'color' in name or 'bg' in name

            # Determine category
            category = "other"
            if is_color or 'color' in name or 'bg' in name or 'shadow' in name:
                category = "color"
            elif is_spacing or any(kw in name for kw in ['spacing', 'space', 'gap', 'margin', 'padding']):
                category = "spacing"
            elif is_typography or any(kw in name for kw in ['font', 'text', 'line-height', 'letter']):
                category = "typography"
            elif any(kw in name for kw in ['size', 'width', 'height', 'radius', 'border']):
                category = "sizing"

            var_info = CSSVariableInfo(
                name=name,
                value=value[:80],
                file=file_path,
                line_number=line_num,
                scope=scope,
                is_color=is_color,
                is_spacing=is_spacing,
                is_typography=is_typography,
                is_theme_variable=is_theme,
                category=category,
            )
            variables.append(var_info)

        # Count var() usage
        for match in self.VAR_USAGE.finditer(clean):
            var_name = match.group(1)
            var_usage[var_name] = var_usage.get(var_name, 0) + 1

        # Update usage counts on declarations
        for v in variables:
            v.usage_count = var_usage.get(v.name, 0)

        # Detect themes
        theme = self._detect_themes(clean, file_path)
        if theme:
            themes.append(theme)

        # Extract preprocessor variables
        ext = file_path.lower().rsplit('.', 1)[-1] if '.' in file_path else ''
        if ext in ('scss', 'sass'):
            for match in self.SCSS_VAR.finditer(clean):
                preprocessor_vars.append(CSSVariableInfo(
                    name=match.group(1),
                    value=match.group(2).strip()[:80],
                    file=file_path,
                    line_number=clean[:match.start()].count('\n') + 1,
                    scope="scss",
                ))
        elif ext == 'less':
            for match in self.LESS_VAR.finditer(clean):
                # Skip @media, @import, @keyframes etc
                name = match.group(1)
                if name.startswith('@media') or name.startswith('@import') or name.startswith('@keyframes'):
                    continue
                preprocessor_vars.append(CSSVariableInfo(
                    name=name,
                    value=match.group(2).strip()[:80],
                    file=file_path,
                    line_number=clean[:match.start()].count('\n') + 1,
                    scope="less",
                ))

        stats = {
            "total_variables": len(variables),
            "root_variables": sum(1 for v in variables if v.scope == ":root"),
            "color_variables": sum(1 for v in variables if v.is_color),
            "spacing_variables": sum(1 for v in variables if v.is_spacing),
            "theme_variables": sum(1 for v in variables if v.is_theme_variable),
            "preprocessor_variables": len(preprocessor_vars),
            "var_usage_count": sum(var_usage.values()),
            "has_dark_mode": any(t.supports_dark_mode for t in themes),
            "has_light_mode": any(t.supports_light_mode for t in themes),
        }

        return {
            "variables": variables,
            "themes": themes,
            "var_usage": var_usage,
            "preprocessor_vars": preprocessor_vars,
            "stats": stats,
        }

    def _determine_scope(self, content: str, pos: int) -> str:
        """Determine the scope context of a variable declaration."""
        # Look backwards for the nearest selector/block
        before = content[:pos]
        # Find last opening brace context
        last_root = before.rfind(':root')
        last_brace = before.rfind('{')
        if last_root != -1 and (last_brace == -1 or last_root > last_brace - 20):
            return ":root"

        # Check for media query scope
        last_media = before.rfind('@media')
        if last_media != -1 and last_media > last_brace - 100:
            return "media-query"

        # Try to find the selector
        lines_before = before.split('\n')
        for line in reversed(lines_before[-5:]):
            stripped = line.strip()
            if stripped and not stripped.startswith('--') and '{' in stripped:
                selector = stripped.split('{')[0].strip()
                if selector:
                    return selector[:50]

        return "block"

    def _detect_themes(self, content: str, file_path: str) -> Optional[CSSThemeInfo]:
        """Detect theming patterns in CSS."""
        has_dark = any(p.search(content) for p in self.DARK_MODE_PATTERNS)
        has_light = any(p.search(content) for p in self.LIGHT_MODE_PATTERNS)

        if not has_dark and not has_light:
            return None

        # Determine strategy
        strategy = "unknown"
        if re.search(r'prefers-color-scheme', content):
            strategy = "media-query"
        elif re.search(r'data-theme|data-color-scheme', content):
            strategy = "data-attribute"
        elif re.search(r'\.dark\b|\.light\b|\.theme-', content):
            strategy = "class-based"

        # Collect theme variables
        theme_vars = []
        for match in self.VAR_DECLARATION.finditer(content):
            name = match.group(1)
            if any(kw in name for kw in ['color', 'bg', 'text', 'border', 'shadow', 'theme']):
                theme_vars.append(name)

        color_schemes = []
        if has_dark:
            color_schemes.append("dark")
        if has_light:
            color_schemes.append("light")

        return CSSThemeInfo(
            name="theme",
            file=file_path,
            strategy=strategy,
            variables=theme_vars[:20],
            supports_dark_mode=has_dark,
            supports_light_mode=has_light,
            color_scheme_values=color_schemes,
        )
