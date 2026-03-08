"""
Styled Components Theme Extractor for CodeTrellis

Extracts theme-related patterns from styled-components usage:
- ThemeProvider wrapping (standard and nested)
- createGlobalStyle`` (global CSS injection)
- useTheme() hook (v5+)
- withTheme() HOC (v3-v4)
- Theme object structure (colors, fonts, breakpoints, spacing, etc.)
- Theme function interpolation ${({ theme }) => theme.colors.primary}
- Dark/light mode theme switching
- Theme nesting / overriding patterns
- Design token usage

Part of CodeTrellis v4.42 - Styled Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class StyledThemeProviderInfo:
    """Information about a ThemeProvider usage."""
    name: str = "ThemeProvider"
    file: str = ""
    line_number: int = 0
    theme_object_name: str = ""      # Variable name of theme object
    is_nested: bool = False
    has_dark_mode: bool = False
    has_custom_breakpoints: bool = False
    token_categories: List[str] = field(default_factory=list)


@dataclass
class StyledGlobalStyleInfo:
    """Information about createGlobalStyle usage."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    has_theme_usage: bool = False
    has_reset: bool = False         # CSS reset/normalize patterns
    has_font_face: bool = False
    has_css_variables: bool = False
    property_count: int = 0


@dataclass
class StyledThemeUsageInfo:
    """Information about theme consumption (useTheme/withTheme)."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    method: str = ""                # useTheme, withTheme, ThemeContext
    theme_properties: List[str] = field(default_factory=list)


class StyledThemeExtractor:
    """
    Extracts styled-components theme patterns from JS/TS source code.

    Detects:
    - ThemeProvider component usage
    - createGlobalStyle`` global styles
    - useTheme() hook (v5+)
    - withTheme() HOC (v3-v4)
    - Theme object definitions with design tokens
    - Dark/light mode patterns
    """

    # ThemeProvider usage
    RE_THEME_PROVIDER = re.compile(
        r"<ThemeProvider\s+(?:theme\s*=\s*\{?\s*(\w+)\s*\}?)?",
        re.MULTILINE
    )

    # createGlobalStyle
    RE_CREATE_GLOBAL_STYLE = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*createGlobalStyle\s*`",
        re.MULTILINE
    )

    # useTheme hook
    RE_USE_THEME = re.compile(
        r"(?:const|let|var)\s+(\w+)\s*=\s*useTheme\s*\(\s*\)",
        re.MULTILINE
    )

    # withTheme HOC
    RE_WITH_THEME = re.compile(
        r"(?:export\s+default\s+)?withTheme\s*\(\s*(\w+)\s*\)|"
        r"(?:const|let|var)\s+(\w+)\s*=\s*withTheme\s*\(",
        re.MULTILINE
    )

    # Theme object definitions
    RE_THEME_OBJECT = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::\s*\w+)?\s*=\s*\{",
        re.MULTILINE
    )

    # Theme token categories (within theme objects)
    THEME_TOKEN_CATEGORIES = {
        'colors', 'fonts', 'fontSizes', 'fontWeights', 'lineHeights',
        'space', 'spacing', 'sizes', 'breakpoints', 'borders', 'borderWidths',
        'borderStyles', 'radii', 'shadows', 'zIndices', 'transitions',
        'letterSpacings', 'mediaQueries', 'palette', 'typography',
    }

    # CSS reset indicators
    RESET_INDICATORS = [
        'box-sizing: border-box', 'margin: 0', 'padding: 0',
        'normalize', '*,', '::before', '::after', 'line-height: 1',
    ]

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract theme-related patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'providers', 'global_styles', 'theme_usages' lists
        """
        providers: List[StyledThemeProviderInfo] = []
        global_styles: List[StyledGlobalStyleInfo] = []
        theme_usages: List[StyledThemeUsageInfo] = []

        if not content or not content.strip():
            return {
                'providers': providers,
                'global_styles': global_styles,
                'theme_usages': theme_usages,
            }

        # ── ThemeProvider ─────────────────────────────────────────
        for m in self.RE_THEME_PROVIDER.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            theme_name = m.group(1) or ""

            # Check for nested ThemeProvider
            is_nested = content.count('<ThemeProvider') > 1

            # Check for dark mode patterns near theme definition
            has_dark = bool(re.search(
                r"dark[Mm]ode|darkTheme|dark_theme|isDark|colorMode|"
                r"prefers-color-scheme:\s*dark|ThemeMode|theme.*dark",
                content
            ))

            # Detect token categories in the theme object
            tokens = []
            if theme_name:
                for cat in self.THEME_TOKEN_CATEGORIES:
                    if re.search(rf'\b{cat}\b\s*:', content):
                        tokens.append(cat)

            providers.append(StyledThemeProviderInfo(
                file=file_path,
                line_number=line_num,
                theme_object_name=theme_name,
                is_nested=is_nested,
                has_dark_mode=has_dark,
                has_custom_breakpoints='breakpoints' in tokens,
                token_categories=sorted(tokens),
            ))

        # ── createGlobalStyle ─────────────────────────────────────
        for m in self.RE_CREATE_GLOBAL_STYLE.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Get the template literal block
            block_start = m.end()
            block_end = content.find('`', block_start)
            block = content[block_start:block_end] if block_end != -1 else ""

            has_theme = bool(re.search(r'theme\.|useTheme|\$\{.*theme', block))
            has_reset = any(ind in block.lower() for ind in self.RESET_INDICATORS)
            has_font_face = '@font-face' in block
            has_css_vars = bool(re.search(r'--[\w-]+\s*:', block))
            prop_count = sum(1 for line in block.split('\n')
                           if line.strip() and ':' in line.strip()
                           and not line.strip().startswith('//'))

            global_styles.append(StyledGlobalStyleInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                has_theme_usage=has_theme,
                has_reset=has_reset,
                has_font_face=has_font_face,
                has_css_variables=has_css_vars,
                property_count=prop_count,
            ))

        # ── useTheme hook ─────────────────────────────────────────
        for m in self.RE_USE_THEME.finditer(content):
            var_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Find theme properties accessed via this variable
            props = set()
            for prop_m in re.finditer(rf'{var_name}\.(\w+)', content):
                props.add(prop_m.group(1))

            theme_usages.append(StyledThemeUsageInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                method="useTheme",
                theme_properties=sorted(props)[:15],
            ))

        # ── withTheme HOC ─────────────────────────────────────────
        for m in self.RE_WITH_THEME.finditer(content):
            comp_name = m.group(1) or m.group(2) or ""
            line_num = content[:m.start()].count('\n') + 1

            theme_usages.append(StyledThemeUsageInfo(
                name=comp_name,
                file=file_path,
                line_number=line_num,
                method="withTheme",
                theme_properties=[],
            ))

        return {
            'providers': providers,
            'global_styles': global_styles,
            'theme_usages': theme_usages,
        }
