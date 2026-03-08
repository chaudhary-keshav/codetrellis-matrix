"""
Emotion Theme Extractor for CodeTrellis

Extracts Emotion theme system patterns from JS/TS source code.
Covers @emotion/react ThemeProvider, useTheme hook, withTheme HOC,
Global component for global CSS injection, and theme interpolation patterns.

Supports:
- ThemeProvider from @emotion/react (v11+) and emotion-theming (v10)
- useTheme() hook (v11+)
- withTheme() HOC (v10/v11)
- Global component for global CSS (replaces injectGlobal)
- Theme function interpolation in css prop and styled
- Design tokens (colors, spacing, fonts, breakpoints, shadows, etc.)
- Nested ThemeProvider for theme overrides
- Dark/light mode theme switching

Part of CodeTrellis v4.43 - Emotion CSS-in-JS Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EmotionThemeProviderInfo:
    """Information about a ThemeProvider usage."""
    name: str
    file: str = ""
    line_number: int = 0
    theme_variable: str = ""
    has_inline_theme: bool = False
    is_nested: bool = False
    import_source: str = ""     # @emotion/react, emotion-theming
    token_categories: List[str] = field(default_factory=list)


@dataclass
class EmotionGlobalStyleInfo:
    """Information about a Global component usage (global CSS injection)."""
    name: str
    file: str = ""
    line_number: int = 0
    method: str = ""            # Global, css-prop-global, injectGlobal
    has_theme_usage: bool = False
    has_css_reset: bool = False
    has_font_face: bool = False
    has_css_variables: bool = False
    import_source: str = ""


@dataclass
class EmotionThemeUsageInfo:
    """Information about theme usage in code."""
    file: str = ""
    line_number: int = 0
    method: str = ""            # useTheme, withTheme, interpolation, props.theme
    hook_name: str = ""
    theme_paths: List[str] = field(default_factory=list)


class EmotionThemeExtractor:
    """
    Extracts Emotion theme patterns from JS/TS/JSX/TSX source code.

    Detects:
    - ThemeProvider from @emotion/react or emotion-theming
    - useTheme() hook
    - withTheme() HOC
    - Global component for global CSS
    - Theme interpolation in css prop ${theme => ...}
    - Design token categories
    - Theme nesting
    """

    # Regex: ThemeProvider component usage
    RE_THEME_PROVIDER = re.compile(
        r"<ThemeProvider\s+theme\s*=\s*\{?\s*(\w+)?",
        re.MULTILINE
    )

    # Regex: Global component usage
    RE_GLOBAL = re.compile(
        r"<Global\s+styles\s*=\s*\{",
        re.MULTILINE
    )

    # Regex: css`...` with global-like content (body, html, *)
    RE_GLOBAL_CSS = re.compile(
        r"(?:injectGlobal|Global)\s*(?:`|\s*styles\s*=)",
        re.MULTILINE
    )

    # Regex: useTheme hook
    RE_USE_THEME = re.compile(
        r"(?:const|let|var)\s+(\w+)\s*=\s*useTheme\s*\(",
        re.MULTILINE
    )

    # Regex: withTheme HOC — matches withTheme(Component) or withTheme((...) => ...)
    RE_WITH_THEME = re.compile(
        r"withTheme\s*\(",
        re.MULTILINE
    )

    # Regex: Theme interpolation in tagged template ${props => props.theme...}
    RE_THEME_INTERPOLATION = re.compile(
        r"(?:props\.theme|theme\.)(\.\w+)+",
        re.MULTILINE
    )

    # Regex: Theme path access patterns
    RE_THEME_PATH = re.compile(
        r"theme\.(\w+(?:\.\w+)*)",
        re.MULTILINE
    )

    # Token category detection
    TOKEN_CATEGORIES = {
        'colors': re.compile(r'theme\.(?:colors?|palette)', re.I),
        'spacing': re.compile(r'theme\.(?:spacing?|space|gaps?)', re.I),
        'fonts': re.compile(r'theme\.(?:fonts?|typography|fontSizes?|fontWeights?|lineHeights?|letterSpacings?)', re.I),
        'breakpoints': re.compile(r'theme\.(?:breakpoints?|mediaQueries?|screens?)', re.I),
        'shadows': re.compile(r'theme\.(?:shadows?|boxShadows?|elevation)', re.I),
        'borders': re.compile(r'theme\.(?:borders?|borderWidths?|borderStyles?|radii|borderRadius)', re.I),
        'sizes': re.compile(r'theme\.(?:sizes?|widths?|heights?|maxWidths?)', re.I),
        'zIndices': re.compile(r'theme\.(?:zIndices|zIndex)', re.I),
        'transitions': re.compile(r'theme\.(?:transitions?|durations?|easings?)', re.I),
        'opacity': re.compile(r'theme\.(?:opacity|opacities)', re.I),
    }

    # CSS reset patterns
    RE_CSS_RESET = re.compile(
        r"(?:normalize|reset|box-sizing\s*:\s*border-box|\*\s*\{|margin\s*:\s*0|padding\s*:\s*0)",
        re.IGNORECASE
    )

    # Font face pattern
    RE_FONT_FACE = re.compile(r"@font-face\s*\{", re.IGNORECASE)

    # CSS variable pattern
    RE_CSS_VARIABLE = re.compile(r"--[\w-]+\s*:", re.MULTILINE)

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Emotion theme patterns.

        Returns:
            Dict with 'providers', 'global_styles', 'theme_usages' lists.
        """
        providers: List[EmotionThemeProviderInfo] = []
        global_styles: List[EmotionGlobalStyleInfo] = []
        theme_usages: List[EmotionThemeUsageInfo] = []

        if not content or not content.strip():
            return {
                'providers': providers,
                'global_styles': global_styles,
                'theme_usages': theme_usages,
            }

        import_source = self._detect_theme_import(content)

        # ── ThemeProvider ────────────────────────────────────────
        for match in self.RE_THEME_PROVIDER.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            theme_var = match.group(1) or ""

            # Detect inline theme
            rest = content[match.start():match.start() + 300]
            has_inline = bool(re.search(r'theme\s*=\s*\{\s*\{', rest))

            # Detect nesting (multiple ThemeProvider in same file)
            is_nested = len(self.RE_THEME_PROVIDER.findall(content)) > 1

            # Detect token categories used
            token_cats = self._detect_token_categories(content)

            providers.append(EmotionThemeProviderInfo(
                name="ThemeProvider",
                file=file_path,
                line_number=line_num,
                theme_variable=theme_var,
                has_inline_theme=has_inline,
                is_nested=is_nested,
                import_source=import_source,
                token_categories=token_cats,
            ))

        # ── Global component ────────────────────────────────────
        for match in self.RE_GLOBAL.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            # Extract global styles context
            context = content[match.start():match.start() + 500]

            global_styles.append(EmotionGlobalStyleInfo(
                name="Global",
                file=file_path,
                line_number=line_num,
                method="Global",
                has_theme_usage=bool(self.RE_THEME_INTERPOLATION.search(context)),
                has_css_reset=bool(self.RE_CSS_RESET.search(context)),
                has_font_face=bool(self.RE_FONT_FACE.search(context)),
                has_css_variables=bool(self.RE_CSS_VARIABLE.search(context)),
                import_source=import_source,
            ))

        # ── injectGlobal (legacy emotion v9) ────────────────────
        inject_matches = re.finditer(r"injectGlobal\s*`", content)
        for match in inject_matches:
            line_num = content[:match.start()].count('\n') + 1
            context = content[match.start():match.start() + 500]

            global_styles.append(EmotionGlobalStyleInfo(
                name="injectGlobal",
                file=file_path,
                line_number=line_num,
                method="injectGlobal",
                has_theme_usage=False,
                has_css_reset=bool(self.RE_CSS_RESET.search(context)),
                has_font_face=bool(self.RE_FONT_FACE.search(context)),
                has_css_variables=bool(self.RE_CSS_VARIABLE.search(context)),
                import_source="emotion",
            ))

        # ── useTheme hook ────────────────────────────────────────
        for match in self.RE_USE_THEME.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            var_name = match.group(1)

            # Find theme paths used after the hook
            paths = self._find_theme_paths(content[match.end():], var_name)

            theme_usages.append(EmotionThemeUsageInfo(
                file=file_path,
                line_number=line_num,
                method="useTheme",
                hook_name="useTheme",
                theme_paths=paths[:10],
            ))

        # ── withTheme HOC ────────────────────────────────────────
        for match in self.RE_WITH_THEME.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            theme_usages.append(EmotionThemeUsageInfo(
                file=file_path,
                line_number=line_num,
                method="withTheme",
                hook_name="withTheme",
            ))

        # ── Theme interpolation in css/styled ────────────────────
        theme_interp_matches = list(self.RE_THEME_INTERPOLATION.finditer(content))
        if theme_interp_matches and not theme_usages:
            # Group theme interpolations into a single usage
            paths = sorted(set(
                match.group(0) for match in self.RE_THEME_PATH.finditer(content)
            ))

            theme_usages.append(EmotionThemeUsageInfo(
                file=file_path,
                line_number=content[:theme_interp_matches[0].start()].count('\n') + 1,
                method="interpolation",
                theme_paths=paths[:10],
            ))

        return {
            'providers': providers,
            'global_styles': global_styles,
            'theme_usages': theme_usages,
        }

    def _detect_theme_import(self, content: str) -> str:
        """Detect the import source for theme utilities."""
        if re.search(r"from\s+['\"]@emotion/react['/\"]", content):
            return "@emotion/react"
        if re.search(r"from\s+['\"]emotion-theming['/\"]", content):
            return "emotion-theming"
        if re.search(r"from\s+['\"]emotion['/\"]", content):
            return "emotion"
        return ""

    def _detect_token_categories(self, content: str) -> List[str]:
        """Detect design token categories used via theme access."""
        categories = []
        for cat, pattern in self.TOKEN_CATEGORIES.items():
            if pattern.search(content):
                categories.append(cat)
        return sorted(categories)

    def _find_theme_paths(self, content: str, var_name: str) -> List[str]:
        """Find theme property paths accessed after a useTheme call."""
        pattern = re.compile(rf'{re.escape(var_name)}\.(\w+(?:\.\w+)*)')
        paths = sorted(set(match.group(1) for match in pattern.finditer(content[:1000])))
        return paths
