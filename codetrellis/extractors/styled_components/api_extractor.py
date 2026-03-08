"""
Styled Components API Extractor for CodeTrellis

Extracts API-level patterns from styled-components usage:
- ServerStyleSheet (SSR: Server-Side Rendering)
- StyleSheetManager (configuration provider)
- isStyledComponent utility
- css prop (babel plugin feature)
- babel-plugin-styled-components / SWC plugin patterns
- Jest/testing-library styled-components testing utilities
- Next.js/Gatsby/Remix integration patterns
- Strict mode / concurrent features

Part of CodeTrellis v4.42 - Styled Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class StyledSSRPatternInfo:
    """Information about SSR (Server-Side Rendering) patterns."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    ssr_method: str = ""    # ServerStyleSheet, sc.ServerStyleSheet
    framework: str = ""     # next.js, gatsby, remix, express
    has_collect_styles: bool = False
    has_interleave: bool = False
    has_streaming: bool = False


@dataclass
class StyledConfigPatternInfo:
    """Information about styled-components configuration/tooling patterns."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    config_type: str = ""      # babel-plugin, swc-plugin, StyleSheetManager
    has_display_name: bool = False
    has_ssr: bool = False
    has_minify: bool = False
    has_pure: bool = False
    has_namespace: bool = False
    options: List[str] = field(default_factory=list)


@dataclass
class StyledTestPatternInfo:
    """Information about styled-components testing patterns."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    test_method: str = ""      # toHaveStyleRule, jest-styled-components, snapshot
    has_theme_wrapper: bool = False
    framework: str = ""        # jest, testing-library, enzyme


class StyledApiExtractor:
    """
    Extracts API-level patterns from styled-components.

    Detects:
    - SSR patterns (ServerStyleSheet, collectStyles, interleaveWithNodeStream)
    - StyleSheetManager configuration
    - Babel/SWC plugin configuration
    - Testing patterns (jest-styled-components, toHaveStyleRule)
    - Framework integrations (Next.js, Gatsby, Remix)
    - css prop usage
    - isStyledComponent checks
    """

    # ServerStyleSheet usage
    RE_SERVER_STYLE_SHEET = re.compile(
        r"(?:new\s+)?ServerStyleSheet\s*\(\s*\)|"
        r"(?:const|let|var)\s+(\w+)\s*=\s*new\s+ServerStyleSheet",
        re.MULTILINE
    )

    # collectStyles / interleaveWithNodeStream
    RE_COLLECT_STYLES = re.compile(
        r"\.collectStyles\s*\(|sheet\.collectStyles",
        re.MULTILINE
    )

    RE_INTERLEAVE = re.compile(
        r"\.interleaveWithNodeStream\s*\(|sheet\.interleaveWithNodeStream",
        re.MULTILINE
    )

    # StyleSheetManager
    RE_STYLESHEET_MANAGER = re.compile(
        r"<StyleSheetManager\s+([^>]*?)>|"
        r"<StyleSheetManager>",
        re.MULTILINE
    )

    # css prop usage
    RE_CSS_PROP = re.compile(
        r'css=\{|css=`|css=\{\{',
        re.MULTILINE
    )

    # isStyledComponent
    RE_IS_STYLED = re.compile(
        r"isStyledComponent\s*\(\s*(\w+)\s*\)",
        re.MULTILINE
    )

    # Babel plugin in config
    RE_BABEL_PLUGIN = re.compile(
        r"babel-plugin-styled-components|"
        r"\[?['\"]babel-plugin-styled-components['\"]",
        re.MULTILINE
    )

    # SWC plugin
    RE_SWC_PLUGIN = re.compile(
        r"@swc/plugin-styled-components|"
        r"styledComponents.*swc|"
        r"swc.*styledComponents",
        re.MULTILINE
    )

    # Jest styled-components
    RE_JEST_STYLED = re.compile(
        r"jest-styled-components|"
        r"toHaveStyleRule\s*\(|"
        r"import\s+['\"]jest-styled-components['\"]",
        re.MULTILINE
    )

    # Next.js integration patterns
    RE_NEXTJS_STYLED = re.compile(
        r"styledComponents.*compiler|"
        r"compiler.*styledComponents|"
        r"next.*config.*styled|"
        r"styled.*components.*next",
        re.MULTILINE
    )

    # Gatsby integration
    RE_GATSBY_STYLED = re.compile(
        r"gatsby-plugin-styled-components",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract API-level patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'ssr_patterns', 'config_patterns', 'test_patterns' lists
        """
        ssr_patterns: List[StyledSSRPatternInfo] = []
        config_patterns: List[StyledConfigPatternInfo] = []
        test_patterns: List[StyledTestPatternInfo] = []

        if not content or not content.strip():
            return {
                'ssr_patterns': ssr_patterns,
                'config_patterns': config_patterns,
                'test_patterns': test_patterns,
            }

        # ── SSR Patterns ──────────────────────────────────────────
        for m in self.RE_SERVER_STYLE_SHEET.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            name = m.group(1) or "sheet"

            # Detect framework
            framework = ""
            if re.search(r'getInitialProps|_document|next', content, re.IGNORECASE):
                framework = "next.js"
            elif re.search(r'wrapRootElement|gatsby', content, re.IGNORECASE):
                framework = "gatsby"
            elif re.search(r'express|createServer|renderToString', content, re.IGNORECASE):
                framework = "express"

            ssr_patterns.append(StyledSSRPatternInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                ssr_method="ServerStyleSheet",
                framework=framework,
                has_collect_styles=bool(self.RE_COLLECT_STYLES.search(content)),
                has_interleave=bool(self.RE_INTERLEAVE.search(content)),
                has_streaming='interleaveWithNodeStream' in content,
            ))

        # ── StyleSheetManager ─────────────────────────────────────
        for m in self.RE_STYLESHEET_MANAGER.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            props_str = m.group(1) or ""

            options = []
            if 'disableVendorPrefixes' in props_str:
                options.append('disableVendorPrefixes')
            if 'enableVendorPrefixes' in props_str:
                options.append('enableVendorPrefixes')
            if 'disableCSSOMInjection' in props_str:
                options.append('disableCSSOMInjection')
            if 'stylisPlugins' in props_str:
                options.append('stylisPlugins')
            if 'target' in props_str:
                options.append('target')
            if 'sheet' in props_str:
                options.append('sheet')

            config_patterns.append(StyledConfigPatternInfo(
                name="StyleSheetManager",
                file=file_path,
                line_number=line_num,
                config_type="StyleSheetManager",
                has_ssr='target' in props_str,
                options=options,
            ))

        # ── Babel plugin configuration ────────────────────────────
        if self.RE_BABEL_PLUGIN.search(content):
            line_num = 0
            for i, line in enumerate(content.split('\n'), 1):
                if 'babel-plugin-styled-components' in line:
                    line_num = i
                    break

            config_patterns.append(StyledConfigPatternInfo(
                name="babel-plugin-styled-components",
                file=file_path,
                line_number=line_num,
                config_type="babel-plugin",
                has_display_name='displayName' in content,
                has_ssr='ssr' in content.lower(),
                has_minify='minify' in content.lower(),
                has_pure='pure' in content,
                has_namespace='namespace' in content,
            ))

        # ── SWC plugin ────────────────────────────────────────────
        if self.RE_SWC_PLUGIN.search(content):
            line_num = 0
            for i, line in enumerate(content.split('\n'), 1):
                if 'swc' in line.lower() and 'styled' in line.lower():
                    line_num = i
                    break

            config_patterns.append(StyledConfigPatternInfo(
                name="swc-plugin-styled-components",
                file=file_path,
                line_number=line_num,
                config_type="swc-plugin",
                has_display_name='displayName' in content,
                has_ssr='ssr' in content.lower(),
            ))

        # ── Testing patterns ──────────────────────────────────────
        if self.RE_JEST_STYLED.search(content):
            line_num = 0
            for i, line in enumerate(content.split('\n'), 1):
                if 'jest-styled-components' in line or 'toHaveStyleRule' in line:
                    line_num = i
                    break

            has_theme_wrapper = bool(re.search(
                r'ThemeProvider|renderWithTheme|withTheme|theme\s*=', content
            ))

            # Detect test framework
            test_fw = "jest"
            if '@testing-library' in content:
                test_fw = "testing-library"
            elif 'enzyme' in content:
                test_fw = "enzyme"

            test_method = "toHaveStyleRule" if 'toHaveStyleRule' in content else "snapshot"

            test_patterns.append(StyledTestPatternInfo(
                name="jest-styled-components",
                file=file_path,
                line_number=line_num,
                test_method=test_method,
                has_theme_wrapper=has_theme_wrapper,
                framework=test_fw,
            ))

        # ── css prop usage ────────────────────────────────────────
        css_prop_count = len(self.RE_CSS_PROP.findall(content))
        if css_prop_count > 0:
            config_patterns.append(StyledConfigPatternInfo(
                name="css-prop",
                file=file_path,
                line_number=0,
                config_type="css-prop",
                options=[f"count:{css_prop_count}"],
            ))

        return {
            'ssr_patterns': ssr_patterns,
            'config_patterns': config_patterns,
            'test_patterns': test_patterns,
        }
