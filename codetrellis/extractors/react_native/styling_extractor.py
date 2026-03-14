"""
React Native Styling Extractor for CodeTrellis

Extracts styling patterns from React Native source code:
- StyleSheet.create blocks with style definitions
- Inline styles and dynamic style patterns
- styled-components/native usage
- NativeWind / Tailwind CSS for RN
- Theme patterns (useTheme, ThemeProvider)
- Responsive styling (Dimensions, useWindowDimensions, PixelRatio)
- Platform-specific styles (Platform.select in styles)

Supports React Native styling ecosystem from StyleSheet through modern CSS-in-JS.

Part of CodeTrellis v5.6 - React Native Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class RNStyleSheetInfo:
    """Information about a StyleSheet.create definition."""
    name: str
    file: str = ""
    line_number: int = 0
    style_names: List[str] = field(default_factory=list)
    uses_absolute_fill: bool = False
    style_count: int = 0


@dataclass
class RNDynamicStyleInfo:
    """Information about dynamic styling patterns."""
    name: str
    file: str = ""
    line_number: int = 0
    style_type: str = ""  # inline, conditional, platform_select, responsive, animated
    depends_on: List[str] = field(default_factory=list)  # theme, dimension, state, etc.


@dataclass
class RNThemeInfo:
    """Information about theming patterns."""
    name: str
    file: str = ""
    line_number: int = 0
    theme_library: str = ""  # custom, react-native-paper, restyle, nativewind, tamagui
    has_dark_mode: bool = False
    has_provider: bool = False
    theme_values: List[str] = field(default_factory=list)


class ReactNativeStylingExtractor:
    """
    Extracts styling and theming patterns from React Native source code.

    Detects:
    - StyleSheet.create definitions with named styles
    - Dynamic and conditional styles
    - styled-components/native wrappers
    - NativeWind className-based styling
    - Theme providers and useTheme hooks
    - Responsive patterns (Dimensions, useWindowDimensions)
    - react-native-paper theming
    - Shopify Restyle patterns
    - Tamagui styling
    """

    # StyleSheet.create
    STYLESHEET_CREATE = re.compile(
        r"(?:const|let|var)\s+(\w+)\s*=\s*StyleSheet\.create\s*\(\s*\{",
        re.MULTILINE
    )

    # Style names inside StyleSheet.create (simplified extraction)
    STYLE_NAME = re.compile(
        r"^\s+(\w+)\s*:\s*\{",
        re.MULTILINE
    )

    # StyleSheet.absoluteFill / absoluteFillObject / flatten / compose / hairlineWidth
    STYLESHEET_UTILS = re.compile(
        r"StyleSheet\.(absoluteFill|absoluteFillObject|flatten|compose|hairlineWidth)",
        re.MULTILINE
    )

    # styled-components/native
    STYLED_NATIVE = re.compile(
        r"from\s+['\"]styled-components/native['\"]|"
        r"styled\.(\w+)`|styled\((\w+)\)`",
        re.MULTILINE
    )

    # NativeWind / className
    NATIVEWIND = re.compile(
        r"from\s+['\"]nativewind['\"]|"
        r"className\s*=\s*['\"]|"
        r"from\s+['\"]twrnc['\"]",
        re.MULTILINE
    )

    # Tamagui
    TAMAGUI = re.compile(
        r"from\s+['\"]tamagui['\"]|from\s+['\"]@tamagui/",
        re.MULTILINE
    )

    # react-native-paper theme
    RN_PAPER_THEME = re.compile(
        r"from\s+['\"]react-native-paper['\"]|useTheme\s*\(\)|"
        r"PaperProvider|DefaultTheme|MD3DarkTheme|MD3LightTheme",
        re.MULTILINE
    )

    # Shopify Restyle
    RESTYLE = re.compile(
        r"from\s+['\"]@shopify/restyle['\"]|"
        r"createTheme\s*\(|createBox\s*\(|createText\s*\(|createRestyleComponent",
        re.MULTILINE
    )

    # Dimensions / useWindowDimensions
    DIMENSIONS = re.compile(
        r"Dimensions\.get\s*\(\s*['\"](?:window|screen)['\"]|"
        r"useWindowDimensions\s*\(|"
        r"PixelRatio\.\w+\s*\(",
        re.MULTILINE
    )

    # Platform.select in style context
    PLATFORM_STYLE = re.compile(
        r"Platform\.select\s*\(\s*\{",
        re.MULTILINE
    )

    # Inline style with spread or conditional
    INLINE_DYNAMIC = re.compile(
        r"style\s*=\s*\{?\s*\[|"
        r"style\s*=\s*\{\s*\.\.\.|"
        r"style\s*=\s*\{[^}]*\?",
        re.MULTILINE
    )

    # Theme-related hooks and patterns
    USE_THEME = re.compile(
        r"useTheme\s*\(|useColorScheme\s*\(|"
        r"Appearance\.getColorScheme\s*\(",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract styling information from source code.

        Returns:
            Dict with keys: stylesheets, dynamic_styles, themes
        """
        stylesheets = []
        dynamic_styles = []
        themes = []

        # StyleSheet.create blocks
        for match in self.STYLESHEET_CREATE.finditer(content):
            var_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Extract style names from the block
            block_start = match.start()
            brace_count = 0
            block_end = block_start
            started = False
            for i, ch in enumerate(content[block_start:], block_start):
                if ch == '{':
                    brace_count += 1
                    started = True
                elif ch == '}':
                    brace_count -= 1
                    if started and brace_count == 0:
                        block_end = i + 1
                        break

            block = content[block_start:block_end]
            style_names = []
            depth = 0
            for sm in re.finditer(r'[{}\n]|^\s+(\w+)\s*:', block, re.MULTILINE):
                if sm.group(0) == '{':
                    depth += 1
                elif sm.group(0) == '}':
                    depth -= 1
                elif depth == 2 and sm.group(1):  # Top-level keys inside create({})
                    style_names.append(sm.group(1))

            uses_abs = bool(re.search(r'StyleSheet\.absoluteFill|\.\.\.StyleSheet\.absoluteFillObject', block))

            stylesheets.append(RNStyleSheetInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                style_names=style_names[:30],
                uses_absolute_fill=uses_abs,
                style_count=len(style_names),
            ))

        # Dynamic / conditional styles
        for match in self.INLINE_DYNAMIC.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            depends = []
            context = content[max(0, match.start()-100):match.start()+200]
            if 'theme' in context.lower():
                depends.append('theme')
            if 'Dimensions' in context or 'windowDimensions' in context or 'width' in context:
                depends.append('dimensions')
            if 'Platform' in context:
                depends.append('platform')
            dynamic_styles.append(RNDynamicStyleInfo(
                name=f"dynamic_style_L{line_num}",
                file=file_path,
                line_number=line_num,
                style_type="conditional",
                depends_on=depends,
            ))

        # Platform.select styles
        for match in self.PLATFORM_STYLE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            dynamic_styles.append(RNDynamicStyleInfo(
                name=f"platform_select_L{line_num}",
                file=file_path,
                line_number=line_num,
                style_type="platform_select",
                depends_on=["platform"],
            ))

        # Responsive styles
        for match in self.DIMENSIONS.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            dynamic_styles.append(RNDynamicStyleInfo(
                name=f"responsive_L{line_num}",
                file=file_path,
                line_number=line_num,
                style_type="responsive",
                depends_on=["dimensions"],
            ))

        # Theme detection
        # NativeWind
        if self.NATIVEWIND.search(content):
            m = self.NATIVEWIND.search(content)
            themes.append(RNThemeInfo(
                name="NativeWind",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                theme_library="nativewind",
                has_dark_mode=bool(re.search(r'dark:|darkMode|colorScheme', content)),
            ))

        # styled-components/native
        if self.STYLED_NATIVE.search(content):
            m = self.STYLED_NATIVE.search(content)
            has_theme = 'ThemeProvider' in content or 'useTheme' in content
            themes.append(RNThemeInfo(
                name="StyledComponents",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                theme_library="styled-components",
                has_provider=has_theme,
                has_dark_mode=bool(re.search(r'dark|mode|scheme', content, re.IGNORECASE)),
            ))

        # Tamagui
        if self.TAMAGUI.search(content):
            m = self.TAMAGUI.search(content)
            themes.append(RNThemeInfo(
                name="Tamagui",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                theme_library="tamagui",
                has_dark_mode=bool(re.search(r'dark|light|scheme', content, re.IGNORECASE)),
            ))

        # react-native-paper
        if self.RN_PAPER_THEME.search(content):
            m = self.RN_PAPER_THEME.search(content)
            themes.append(RNThemeInfo(
                name="RNPaper",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                theme_library="react-native-paper",
                has_dark_mode=bool(re.search(r'MD3DarkTheme|DarkTheme|dark', content)),
                has_provider='PaperProvider' in content or 'Provider' in content,
            ))

        # Shopify Restyle
        if self.RESTYLE.search(content):
            m = self.RESTYLE.search(content)
            themes.append(RNThemeInfo(
                name="Restyle",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                theme_library="restyle",
                has_provider='ThemeProvider' in content,
            ))

        # Custom theme hook (useTheme / useColorScheme)
        if self.USE_THEME.search(content) and not any(t.theme_library != 'custom' for t in themes):
            m = self.USE_THEME.search(content)
            themes.append(RNThemeInfo(
                name="CustomTheme",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                theme_library="custom",
                has_dark_mode=bool(re.search(r'colorScheme|dark|light', content, re.IGNORECASE)),
            ))

        return {
            'stylesheets': stylesheets,
            'dynamic_styles': dynamic_styles,
            'themes': themes,
        }
