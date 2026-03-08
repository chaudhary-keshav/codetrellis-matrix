"""
EnhancedStyledComponentsParser v1.0 - Comprehensive styled-components parser.

This parser integrates all Styled Components extractors to provide complete
parsing of styled-components / CSS-in-JS usage across React/TypeScript
source files (.jsx, .tsx, .js, .ts).

It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting styled-components-specific semantics.

Supports:
- styled-components v1.x (original tagged template API, injectGlobal)
- styled-components v2.x (withComponent, .extend, innerRef→forwardRef)
- styled-components v3.x (.extend deprecated, createGlobalStyle replaces
    injectGlobal, StyleSheetManager, ServerStyleSheet streaming SSR)
- styled-components v4.x (forwardRef by default, as prop, shouldForwardProp,
    .withComponent removed, createGlobalStyle, attrs new syntax, macro support)
- styled-components v5.x (useTheme hook, .withConfig, performance improvements,
    zero-config SSR streaming, StyleSheetManager enhancements, React 18 concurrent
    mode, transient $-prefixed props)
- styled-components v6.x (SSR revamp with useServerInsertedHTML for Next.js App
    Router, stylis v4 upgrade, shouldForwardProp on styled(), TS improvements,
    withConfig displayName/componentId/shouldForwardProp, no .extend, no
    .withComponent, createGlobalStyle improvements, full ES modules,
    new compiler: @swc/plugin-styled-components)

CSS-in-JS Ecosystem:
- @emotion/styled (API-compatible, css prop, Global component)
- linaria (zero-runtime static CSS extraction, css``, styled``)
- goober (1KB alternative, css``, styled``)
- stitches (@stitches/react, css(), styled(), variants, compound variants)

Component Detection:
- styled.element`` tagged template (div, span, button, h1, etc. — 100+ HTML elements)
- styled(Component)`` extending patterns
- .attrs({}) / .attrs(props => ({})) default prop injection
- .withConfig({displayName, componentId, shouldForwardProp})
- Object-style syntax: styled.div({property: value})
- Transient props ($propName) for non-DOM forwarding (v5.1+)
- as prop for element polymorphism
- forwardRef integration

Theme System:
- ThemeProvider wrapping with theme objects
- createGlobalStyle`` for global CSS injection
- useTheme() hook (v5+)
- withTheme() HOC (v3-v4)
- Theme function interpolation ${({ theme }) => theme.colors.primary}
- Design tokens (colors, fonts, spacing, breakpoints, etc.)
- Dark/light mode theme switching
- Nested ThemeProvider for theme overrides

Mixin / Helper Patterns:
- css`` tagged template helper for reusable style fragments
- keyframes`` for CSS animation definitions
- Mixin functions returning css`` fragments
- polished utility library (lighten, darken, transparentize, etc.)
- Interpolation functions for conditional/dynamic styles
- Shared style composition via template literal inclusion

Style Patterns:
- CSS property detection (layout, typography, color, spacing, etc.)
- Media query patterns (mobile-first, desktop-first, breakpoints)
- Pseudo-selector usage (:hover, :focus, ::before, ::after, etc.)
- CSS nesting with & parent selector (up to arbitrary depth)
- Dynamic prop-based conditional styles ${props => ...}
- CSS custom properties (variables)
- Flexbox and CSS Grid patterns
- Animation keyframes and transitions

API Patterns:
- ServerStyleSheet (SSR with Express, Next.js Pages Router)
- StyleSheetManager (configuration provider, stylis plugins)
- isStyledComponent utility
- css prop (babel plugin feature)
- babel-plugin-styled-components configuration
- @swc/plugin-styled-components (v6+)
- jest-styled-components / toHaveStyleRule testing
- Next.js compiler.styledComponents (v12+ SWC compiler)
- Gatsby gatsby-plugin-styled-components
- Remix integration

Framework Ecosystem Detection (30+ patterns):
- Core: styled-components, @emotion/styled, goober, linaria,
    @stitches/react, @vanilla-extract/css
- Babel: babel-plugin-styled-components, babel-plugin-macros
- SWC: @swc/plugin-styled-components
- SSR: next, gatsby, remix, express
- Testing: jest-styled-components, @testing-library/react
- Utilities: polished, styled-system, styled-tools, styled-normalize,
    xstyled, rebass, styled-media-query, styled-breakpoints
- TypeScript: styled-components/native, csstype

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.42 - Styled Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Styled Components extractors
from .extractors.styled_components import (
    StyledComponentExtractor, StyledComponentInfo, StyledExtendedComponentInfo,
    StyledThemeExtractor, StyledThemeProviderInfo, StyledGlobalStyleInfo,
    StyledThemeUsageInfo,
    StyledMixinExtractor, StyledCssHelperInfo, StyledKeyframesInfo,
    StyledMixinInfo,
    StyledStyleExtractor, StyledStylePatternInfo, StyledDynamicPropInfo,
    StyledMediaQueryInfo,
    StyledApiExtractor, StyledSSRPatternInfo, StyledConfigPatternInfo,
    StyledTestPatternInfo,
)


@dataclass
class StyledComponentsParseResult:
    """Complete parse result for a file with styled-components usage."""
    file_path: str
    file_type: str = "jsx"  # jsx, tsx, js, ts

    # Components
    components: List[StyledComponentInfo] = field(default_factory=list)
    extended_components: List[StyledExtendedComponentInfo] = field(default_factory=list)

    # Theme
    providers: List[StyledThemeProviderInfo] = field(default_factory=list)
    global_styles: List[StyledGlobalStyleInfo] = field(default_factory=list)
    theme_usages: List[StyledThemeUsageInfo] = field(default_factory=list)

    # Mixins / Helpers
    css_helpers: List[StyledCssHelperInfo] = field(default_factory=list)
    keyframes: List[StyledKeyframesInfo] = field(default_factory=list)
    mixins: List[StyledMixinInfo] = field(default_factory=list)

    # Styles
    style_patterns: List[StyledStylePatternInfo] = field(default_factory=list)
    dynamic_props: List[StyledDynamicPropInfo] = field(default_factory=list)
    media_queries: List[StyledMediaQueryInfo] = field(default_factory=list)

    # API patterns
    ssr_patterns: List[StyledSSRPatternInfo] = field(default_factory=list)
    config_patterns: List[StyledConfigPatternInfo] = field(default_factory=list)
    test_patterns: List[StyledTestPatternInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    sc_version: str = ""  # Detected styled-components version (v1-v6)
    css_in_js_library: str = ""  # styled-components, @emotion/styled, etc.
    has_theme_provider: bool = False
    has_global_styles: bool = False
    has_ssr: bool = False
    has_dynamic_styling: bool = False
    has_media_queries: bool = False
    has_keyframes: bool = False
    has_css_helpers: bool = False
    has_transient_props: bool = False
    has_polished: bool = False
    has_css_prop: bool = False
    detected_features: List[str] = field(default_factory=list)


class EnhancedStyledComponentsParser:
    """
    Enhanced styled-components parser using all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    (and potentially alongside the React parser) when styled-components or
    compatible CSS-in-JS library is detected.

    Framework detection supports 30+ styled-components ecosystem patterns across:
    - Core (styled-components, @emotion/styled, goober, linaria, stitches)
    - Build tools (babel-plugin, @swc/plugin, macros)
    - Utilities (polished, styled-system, styled-tools, rebass)
    - Testing (jest-styled-components, @testing-library)
    - SSR (Next.js, Gatsby, Remix, Express)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Styled-components ecosystem framework / library detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core styled-components ────────────────────────────────
        'styled-components': re.compile(
            r"from\s+['\"]styled-components['/\"]|"
            r"require\(['\"]styled-components['\"]\)",
            re.MULTILINE
        ),
        'styled-components-native': re.compile(
            r"from\s+['\"]styled-components/native['/\"]",
            re.MULTILINE
        ),

        # ── Emotion (API-compatible) ─────────────────────────────
        'emotion-styled': re.compile(
            r"from\s+['\"]@emotion/styled['/\"]|"
            r"require\(['\"]@emotion/styled['\"]\)",
            re.MULTILINE
        ),
        'emotion-react': re.compile(
            r"from\s+['\"]@emotion/react['/\"]",
            re.MULTILINE
        ),
        'emotion-css': re.compile(
            r"from\s+['\"]@emotion/css['/\"]",
            re.MULTILINE
        ),

        # ── Linaria (zero-runtime) ───────────────────────────────
        'linaria': re.compile(
            r"from\s+['\"]@linaria/react['/\"]|"
            r"from\s+['\"]@linaria/core['/\"]|"
            r"from\s+['\"]linaria['/\"]",
            re.MULTILINE
        ),

        # ── Goober (1KB) ─────────────────────────────────────────
        'goober': re.compile(
            r"from\s+['\"]goober['/\"]",
            re.MULTILINE
        ),

        # ── Stitches ─────────────────────────────────────────────
        'stitches': re.compile(
            r"from\s+['\"]@stitches/react['/\"]|"
            r"from\s+['\"]@stitches/core['/\"]",
            re.MULTILINE
        ),

        # ── Vanilla Extract ──────────────────────────────────────
        'vanilla-extract': re.compile(
            r"from\s+['\"]@vanilla-extract/css['/\"]|"
            r"from\s+['\"]@vanilla-extract/recipes['/\"]",
            re.MULTILINE
        ),

        # ── Build tools ──────────────────────────────────────────
        'babel-plugin-styled-components': re.compile(
            r"babel-plugin-styled-components",
            re.MULTILINE
        ),
        'babel-plugin-macros': re.compile(
            r"from\s+['\"]styled-components/macro['/\"]",
            re.MULTILINE
        ),
        'swc-plugin': re.compile(
            r"@swc/plugin-styled-components|"
            r"styledComponents.*compiler|compiler.*styledComponents",
            re.MULTILINE
        ),

        # ── Utilities ────────────────────────────────────────────
        'polished': re.compile(
            r"from\s+['\"]polished['/\"]|require\(['\"]polished['\"]\)",
            re.MULTILINE
        ),
        'styled-system': re.compile(
            r"from\s+['\"]styled-system['/\"]",
            re.MULTILINE
        ),
        'styled-tools': re.compile(
            r"from\s+['\"]styled-tools['/\"]",
            re.MULTILINE
        ),
        'styled-normalize': re.compile(
            r"from\s+['\"]styled-normalize['/\"]",
            re.MULTILINE
        ),
        'xstyled': re.compile(
            r"from\s+['\"]@xstyled/styled-components['/\"]|"
            r"from\s+['\"]@xstyled/emotion['/\"]",
            re.MULTILINE
        ),
        'rebass': re.compile(
            r"from\s+['\"]rebass['/\"]|from\s+['\"]rebass/styled-components['/\"]",
            re.MULTILINE
        ),
        'styled-media-query': re.compile(
            r"from\s+['\"]styled-media-query['/\"]",
            re.MULTILINE
        ),
        'styled-breakpoints': re.compile(
            r"from\s+['\"]styled-breakpoints['/\"]",
            re.MULTILINE
        ),

        # ── Testing ──────────────────────────────────────────────
        'jest-styled-components': re.compile(
            r"jest-styled-components|toHaveStyleRule",
            re.MULTILINE
        ),

        # ── SSR Frameworks ───────────────────────────────────────
        'next-js': re.compile(
            r"from\s+['\"]next['/\"]|"
            r"getInitialProps|getServerSideProps|_document",
            re.MULTILINE
        ),
        'gatsby': re.compile(
            r"gatsby-plugin-styled-components|"
            r"from\s+['\"]gatsby['/\"]",
            re.MULTILINE
        ),
        'remix': re.compile(
            r"from\s+['\"]@remix-run/react['/\"]",
            re.MULTILINE
        ),

        # ── React Native ─────────────────────────────────────────
        'react-native': re.compile(
            r"from\s+['\"]react-native['/\"]",
            re.MULTILINE
        ),

        # ── Theme / Design System ────────────────────────────────
        'theme-ui': re.compile(
            r"from\s+['\"]theme-ui['/\"]",
            re.MULTILINE
        ),
    }

    # Version detection based on API usage patterns
    SC_VERSION_INDICATORS = {
        # v6 indicators
        'useServerInsertedHTML': 'v6',
        '@swc/plugin-styled-components': 'v6',
        'compiler.*styledComponents': 'v6',

        # v5 indicators
        'useTheme': 'v5',
        '$': 'v5',  # Transient props (checked contextually)

        # v4 indicators
        'as=': 'v4',
        'forwardRef': 'v4',

        # v3 indicators
        'createGlobalStyle': 'v3',
        'StyleSheetManager': 'v3',

        # v2 indicators
        '.extend': 'v2',
        'withComponent': 'v2',

        # v1 indicators
        'injectGlobal': 'v1',
    }

    VERSION_PRIORITY = {'v6': 6, 'v5': 5, 'v4': 4, 'v3': 3, 'v2': 2, 'v1': 1}

    def __init__(self):
        """Initialize the parser with all styled-components extractors."""
        self.component_extractor = StyledComponentExtractor()
        self.theme_extractor = StyledThemeExtractor()
        self.mixin_extractor = StyledMixinExtractor()
        self.style_extractor = StyledStyleExtractor()
        self.api_extractor = StyledApiExtractor()

    def parse(self, content: str, file_path: str = "") -> StyledComponentsParseResult:
        """
        Parse source code and extract all styled-components information.

        This should be called AFTER the JavaScript/TypeScript parser has run,
        when styled-components or compatible CSS-in-JS is detected.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            StyledComponentsParseResult with all extracted information
        """
        result = StyledComponentsParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        elif file_path.endswith('.ts'):
            result.file_type = "ts"
        else:
            result.file_type = "js"

        # ── Detect frameworks ─────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Detect CSS-in-JS library ──────────────────────────────
        result.css_in_js_library = self._detect_library(content)

        # ── Extract components ────────────────────────────────────
        comp_result = self.component_extractor.extract(content, file_path)
        result.components = comp_result.get('components', [])
        result.extended_components = comp_result.get('extended_components', [])

        # ── Extract theme ─────────────────────────────────────────
        theme_result = self.theme_extractor.extract(content, file_path)
        result.providers = theme_result.get('providers', [])
        result.global_styles = theme_result.get('global_styles', [])
        result.theme_usages = theme_result.get('theme_usages', [])

        # ── Extract mixins ────────────────────────────────────────
        mixin_result = self.mixin_extractor.extract(content, file_path)
        result.css_helpers = mixin_result.get('css_helpers', [])
        result.keyframes = mixin_result.get('keyframes', [])
        result.mixins = mixin_result.get('mixins', [])

        # ── Extract styles ────────────────────────────────────────
        style_result = self.style_extractor.extract(content, file_path)
        result.style_patterns = style_result.get('style_patterns', [])
        result.dynamic_props = style_result.get('dynamic_props', [])
        result.media_queries = style_result.get('media_queries', [])

        # ── Extract API patterns ──────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.ssr_patterns = api_result.get('ssr_patterns', [])
        result.config_patterns = api_result.get('config_patterns', [])
        result.test_patterns = api_result.get('test_patterns', [])

        # ── Compute metadata flags ────────────────────────────────
        result.has_theme_provider = len(result.providers) > 0
        result.has_global_styles = len(result.global_styles) > 0
        result.has_ssr = len(result.ssr_patterns) > 0
        result.has_dynamic_styling = len(result.dynamic_props) > 0
        result.has_media_queries = len(result.media_queries) > 0
        result.has_keyframes = len(result.keyframes) > 0
        result.has_css_helpers = len(result.css_helpers) > 0
        result.has_transient_props = any(
            c.has_transient_props for c in result.components
        )
        result.has_polished = 'polished' in result.detected_frameworks
        result.has_css_prop = any(
            c.config_type == 'css-prop' for c in result.config_patterns
        )

        # ── Detect version ────────────────────────────────────────
        result.sc_version = self._detect_version(content, result)

        # ── Detect features ───────────────────────────────────────
        result.detected_features = self._detect_features(content, result)

        return result

    def is_styled_components_file(
        self, content: str, file_path: str = ""
    ) -> bool:
        """
        Determine if a file contains styled-components code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains styled-components code
        """
        if not content:
            return False

        # Check for styled-components imports
        if re.search(r"from\s+['\"]styled-components['/\"]", content):
            return True

        # Check for @emotion/styled imports
        if re.search(r"from\s+['\"]@emotion/styled['/\"]", content):
            return True

        # Check for require('styled-components')
        if re.search(r"require\(['\"]styled-components['\"]\)", content):
            return True

        # Check for styled.xxx`` pattern (the hallmark of styled-components)
        if re.search(r"styled\s*\.\s*\w+\s*`", content):
            return True

        # Check for styled(Component)`` pattern
        if re.search(r"styled\s*\(\s*\w+\s*\)\s*`", content):
            return True

        # Check for createGlobalStyle
        if re.search(r"createGlobalStyle\s*`", content):
            return True

        # Check for keyframes``
        if re.search(r"keyframes\s*`", content):
            return True

        # Check for css`` helper (from styled-components or @emotion)
        if re.search(r"\bcss\s*`", content) and re.search(
            r"styled-components|@emotion|from\s+['\"]goober", content
        ):
            return True

        # Check for linaria
        if re.search(r"from\s+['\"]@linaria/react['/\"]", content):
            return True

        # Check for goober
        if re.search(r"from\s+['\"]goober['/\"]", content):
            return True

        # Check for stitches
        if re.search(r"from\s+['\"]@stitches/react['/\"]", content):
            return True

        return False

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which styled-components ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return sorted(frameworks)

    def _detect_library(self, content: str) -> str:
        """Detect which CSS-in-JS library is the primary one."""
        if re.search(r"from\s+['\"]styled-components['/\"]", content):
            return "styled-components"
        if re.search(r"from\s+['\"]@emotion/styled['/\"]", content):
            return "@emotion/styled"
        if re.search(r"from\s+['\"]goober['/\"]", content):
            return "goober"
        if re.search(r"from\s+['\"]@stitches/react['/\"]", content):
            return "@stitches/react"
        if re.search(r"from\s+['\"]@linaria/react['/\"]", content):
            return "@linaria/react"
        if re.search(r"from\s+['\"]@vanilla-extract/css['/\"]", content):
            return "@vanilla-extract/css"
        # Fallback: check for styled`` usage without explicit import
        if re.search(r"styled\s*\.\s*\w+\s*`|styled\s*\(\s*\w+\s*\)\s*`", content):
            return "styled-components"
        return ""

    def _detect_version(
        self, content: str, result: StyledComponentsParseResult
    ) -> str:
        """Detect the styled-components version from API patterns."""
        detected_version = ''
        max_priority = -1

        # v6: useServerInsertedHTML, @swc/plugin, compiler.styledComponents
        if re.search(r'useServerInsertedHTML|@swc/plugin-styled-components', content):
            return 'v6'
        if re.search(r'compiler.*styledComponents|styledComponents.*compiler', content):
            return 'v6'

        # v5: useTheme hook, transient $ props
        if 'useTheme' in content and 'styled-components' in content:
            detected_version = 'v5'
            max_priority = 5
        if result.has_transient_props:
            if self.VERSION_PRIORITY.get('v5', 0) > max_priority:
                detected_version = 'v5'
                max_priority = 5

        # v4: as prop, forwardRef built-in
        if max_priority < 4:
            if re.search(r'\bas\s*=\s*["\'{]', content) and \
               re.search(r'styled', content):
                detected_version = 'v4'
                max_priority = 4

        # v3: createGlobalStyle, StyleSheetManager
        if max_priority < 3:
            if 'createGlobalStyle' in content:
                detected_version = 'v3'
                max_priority = 3
            elif 'StyleSheetManager' in content:
                detected_version = 'v3'
                max_priority = 3

        # v2: .extend, withComponent
        if max_priority < 2:
            if re.search(r'\.extend\s*`', content) or 'withComponent' in content:
                detected_version = 'v2'
                max_priority = 2

        # v1: injectGlobal
        if max_priority < 1:
            if 'injectGlobal' in content:
                detected_version = 'v1'
                max_priority = 1

        # Default to v5 (most common) if we have styled usage but can't determine
        if not detected_version and result.components:
            detected_version = 'v5'

        return detected_version

    def _detect_features(
        self, content: str, result: StyledComponentsParseResult
    ) -> List[str]:
        """Detect styled-components features used in the file."""
        features: List[str] = []

        # Component features
        if result.components:
            features.append('styled_components')
            # Count by method
            element_count = sum(1 for c in result.components
                               if c.method == 'styled.element')
            extend_count = sum(1 for c in result.components
                              if c.method == 'styled(Component)')
            if element_count > 0:
                features.append('styled_elements')
            if extend_count > 0:
                features.append('component_extending')

        if result.extended_components:
            features.append('style_inheritance')

        # Attrs
        if any(c.has_attrs for c in result.components):
            features.append('attrs_api')

        # shouldForwardProp
        if any(c.has_should_forward_prop for c in result.components):
            features.append('should_forward_prop')

        # Transient props
        if result.has_transient_props:
            features.append('transient_props')

        # Theme features
        if result.has_theme_provider:
            features.append('theme_provider')
        if result.has_global_styles:
            features.append('global_styles')
        if result.theme_usages:
            methods = set(u.method for u in result.theme_usages)
            for m in sorted(methods):
                features.append(f'theme_{m}')

        # Dynamic styling
        if result.has_dynamic_styling:
            features.append('dynamic_styling')
            patterns = set(d.pattern for d in result.dynamic_props)
            for p in sorted(patterns):
                features.append(f'dynamic_{p}')

        # Theme usage in interpolations
        if any(c.has_theme_usage for c in result.components):
            features.append('theme_interpolation')

        # Media queries
        if result.has_media_queries:
            features.append('media_queries')
            if any(mq.is_mobile_first for mq in result.media_queries):
                features.append('mobile_first')

        # Animations
        if result.has_keyframes:
            features.append('keyframes_animations')

        # CSS helpers / mixins
        if result.has_css_helpers:
            features.append('css_helpers')
        if result.mixins:
            mixin_types = set(m.mixin_type for m in result.mixins)
            for mt in sorted(mixin_types):
                features.append(f'mixin_{mt}')

        # SSR
        if result.has_ssr:
            features.append('server_side_rendering')
            for ssr in result.ssr_patterns:
                if ssr.framework:
                    features.append(f'ssr_{ssr.framework}')

        # Polished
        if result.has_polished:
            features.append('polished_utilities')

        # CSS prop
        if result.has_css_prop:
            features.append('css_prop')

        # Nesting
        if any(p.has_nesting for p in result.style_patterns):
            features.append('css_nesting')

        # CSS variables
        if any(p.has_css_variables for p in result.style_patterns):
            features.append('css_variables')

        # Flexbox / Grid
        if any(p.has_flexbox for p in result.style_patterns):
            features.append('flexbox_layout')
        if any(p.has_grid for p in result.style_patterns):
            features.append('grid_layout')

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for f in features:
            if f not in seen:
                seen.add(f)
                unique.append(f)

        return unique
