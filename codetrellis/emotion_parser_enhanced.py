"""
EnhancedEmotionParser v1.0 - Comprehensive Emotion CSS-in-JS parser.

This parser integrates all Emotion extractors to provide complete parsing
of Emotion CSS-in-JS usage across React/TypeScript source files
(.jsx, .tsx, .js, .ts).

It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting Emotion-specific semantics.

Supports:
- @emotion/react v11.x+ (css prop, Global, ClassNames, keyframes,
    ThemeProvider, useTheme, CacheProvider)
- @emotion/styled v11.x+ (styled API, compatible with styled-components,
    shouldForwardProp, as prop, object syntax, string element syntax)
- @emotion/css v11.x+ (framework-agnostic css(), cx(), keyframes(),
    injectGlobal(), cache)
- @emotion/cache v11.x+ (createCache, CacheProvider, custom nonce/prepend/
    container, stylis plugins)
- @emotion/server v11.x+ (extractCritical, extractCriticalToChunks,
    renderStylesToString, renderStylesToNodeStream,
    constructStyleTagsFromChunks)
- @emotion/jest (createSerializer, toHaveStyleRule matcher)
- emotion v10.x (emotion-theming, @emotion/core → @emotion/react migration)
- emotion v9.x (legacy: single emotion package, injectGlobal, hydrate)

CSS-in-JS Features:
- css prop (the signature Emotion feature — both string & object syntax)
- css`` tagged template helper
- css() function call
- cx() composition utility (className composition)
- ClassNames render prop component
- keyframes`` animation definitions
- Global component (replaces injectGlobal)
- ThemeProvider + useTheme hook + withTheme HOC
- createCache + CacheProvider (custom cache instances)
- SSR support (extractCritical, streaming, Next.js _document integration)
- JSX pragma: /** @jsxImportSource @emotion/react */
- Babel plugin: @emotion/babel-plugin (auto-label, source maps)
- SWC plugin: @swc/plugin-emotion
- Next.js compiler.emotion integration
- Gatsby gatsby-plugin-emotion
- Facepaint responsive styles

Framework Ecosystem Detection (30+ patterns):
- Core: @emotion/react, @emotion/styled, @emotion/css, @emotion/cache,
    @emotion/server, @emotion/jest, @emotion/hash, @emotion/serialize,
    @emotion/utils, @emotion/sheet, @emotion/weak-memoize
- Legacy: emotion, react-emotion, emotion-theming, @emotion/core,
    create-emotion, create-emotion-server
- Build: @emotion/babel-plugin, babel-plugin-emotion,
    @emotion/babel-preset-css-prop, @swc/plugin-emotion
- Utilities: facepaint, emotion-reset, polished, twin.macro
- Testing: @emotion/jest, jest-emotion
- Frameworks: next, gatsby-plugin-emotion, @remix-run/react

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.43 - Emotion CSS-in-JS Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Emotion extractors
from .extractors.emotion import (
    EmotionComponentExtractor, EmotionStyledComponentInfo,
    EmotionExtendedComponentInfo,
    EmotionThemeExtractor, EmotionThemeProviderInfo,
    EmotionGlobalStyleInfo, EmotionThemeUsageInfo,
    EmotionStyleExtractor, EmotionCssPropInfo, EmotionCssFunctionInfo,
    EmotionClassNamesInfo, EmotionStylePatternInfo,
    EmotionDynamicPropInfo, EmotionMediaQueryInfo,
    EmotionAnimationExtractor, EmotionKeyframesInfo,
    EmotionAnimationUsageInfo,
    EmotionApiExtractor, EmotionCacheInfo, EmotionSSRPatternInfo,
    EmotionBabelConfigInfo, EmotionTestPatternInfo,
)


@dataclass
class EmotionParseResult:
    """Complete parse result for a file with Emotion CSS-in-JS usage."""
    file_path: str
    file_type: str = "jsx"  # jsx, tsx, js, ts

    # Components (from @emotion/styled)
    components: List[EmotionStyledComponentInfo] = field(default_factory=list)
    extended_components: List[EmotionExtendedComponentInfo] = field(default_factory=list)

    # Theme
    providers: List[EmotionThemeProviderInfo] = field(default_factory=list)
    global_styles: List[EmotionGlobalStyleInfo] = field(default_factory=list)
    theme_usages: List[EmotionThemeUsageInfo] = field(default_factory=list)

    # Styles (css prop, css function, ClassNames)
    css_props: List[EmotionCssPropInfo] = field(default_factory=list)
    css_functions: List[EmotionCssFunctionInfo] = field(default_factory=list)
    classnames: List[EmotionClassNamesInfo] = field(default_factory=list)
    style_patterns: List[EmotionStylePatternInfo] = field(default_factory=list)
    dynamic_props: List[EmotionDynamicPropInfo] = field(default_factory=list)
    media_queries: List[EmotionMediaQueryInfo] = field(default_factory=list)

    # Animations
    keyframes: List[EmotionKeyframesInfo] = field(default_factory=list)
    animation_usages: List[EmotionAnimationUsageInfo] = field(default_factory=list)

    # API patterns
    caches: List[EmotionCacheInfo] = field(default_factory=list)
    ssr_patterns: List[EmotionSSRPatternInfo] = field(default_factory=list)
    babel_configs: List[EmotionBabelConfigInfo] = field(default_factory=list)
    test_patterns: List[EmotionTestPatternInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    emotion_version: str = ""       # v9, v10, v11
    emotion_packages: List[str] = field(default_factory=list)
    has_css_prop: bool = False
    has_styled: bool = False
    has_theme_provider: bool = False
    has_global_styles: bool = False
    has_ssr: bool = False
    has_cache: bool = False
    has_dynamic_styling: bool = False
    has_media_queries: bool = False
    has_keyframes: bool = False
    has_classnames: bool = False
    has_cx: bool = False
    has_pragma: bool = False
    detected_features: List[str] = field(default_factory=list)


class EnhancedEmotionParser:
    """
    Enhanced Emotion CSS-in-JS parser using all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    when Emotion (@emotion/react, @emotion/styled, @emotion/css, or legacy
    emotion) is detected.

    Framework detection supports 30+ Emotion ecosystem patterns across:
    - Core (@emotion/react, @emotion/styled, @emotion/css, @emotion/cache, @emotion/server)
    - Legacy (emotion, react-emotion, emotion-theming, @emotion/core)
    - Build tools (@emotion/babel-plugin, babel-plugin-emotion, @swc/plugin-emotion)
    - Utilities (facepaint, emotion-reset, polished, twin.macro)
    - Testing (@emotion/jest, jest-emotion)
    - SSR (Next.js, Gatsby, Remix, Express)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Emotion ecosystem framework / library detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core @emotion packages (v11+) ────────────────────────
        'emotion-react': re.compile(
            r"from\s+['\"]@emotion/react['/\"]|"
            r"require\(['\"]@emotion/react['\"]\)",
            re.MULTILINE
        ),
        'emotion-styled': re.compile(
            r"from\s+['\"]@emotion/styled['/\"]|"
            r"require\(['\"]@emotion/styled['\"]\)",
            re.MULTILINE
        ),
        'emotion-css': re.compile(
            r"from\s+['\"]@emotion/css['/\"]|"
            r"require\(['\"]@emotion/css['\"]\)",
            re.MULTILINE
        ),
        'emotion-cache': re.compile(
            r"from\s+['\"]@emotion/cache['/\"]|"
            r"require\(['\"]@emotion/cache['\"]\)",
            re.MULTILINE
        ),
        'emotion-server': re.compile(
            r"from\s+['\"]@emotion/server['/\"]|"
            r"from\s+['\"]@emotion/server/create-instance['/\"]|"
            r"require\(['\"]@emotion/server['\"]\)",
            re.MULTILINE
        ),
        'emotion-jest': re.compile(
            r"from\s+['\"]@emotion/jest['/\"]|"
            r"require\(['\"]@emotion/jest['\"]\)",
            re.MULTILINE
        ),
        'emotion-hash': re.compile(
            r"from\s+['\"]@emotion/hash['/\"]",
            re.MULTILINE
        ),
        'emotion-serialize': re.compile(
            r"from\s+['\"]@emotion/serialize['/\"]",
            re.MULTILINE
        ),
        'emotion-utils': re.compile(
            r"from\s+['\"]@emotion/utils['/\"]",
            re.MULTILINE
        ),
        'emotion-sheet': re.compile(
            r"from\s+['\"]@emotion/sheet['/\"]",
            re.MULTILINE
        ),
        'emotion-weak-memoize': re.compile(
            r"from\s+['\"]@emotion/weak-memoize['/\"]",
            re.MULTILINE
        ),

        # ── Legacy emotion packages (v9-v10) ─────────────────────
        'emotion-legacy': re.compile(
            r"from\s+['\"]emotion['/\"]|"
            r"require\(['\"]emotion['\"]\)",
            re.MULTILINE
        ),
        'react-emotion': re.compile(
            r"from\s+['\"]react-emotion['/\"]",
            re.MULTILINE
        ),
        'emotion-theming': re.compile(
            r"from\s+['\"]emotion-theming['/\"]",
            re.MULTILINE
        ),
        'emotion-core': re.compile(
            r"from\s+['\"]@emotion/core['/\"]",
            re.MULTILINE
        ),
        'create-emotion': re.compile(
            r"from\s+['\"]create-emotion['/\"]",
            re.MULTILINE
        ),
        'create-emotion-server': re.compile(
            r"from\s+['\"]create-emotion-server['/\"]",
            re.MULTILINE
        ),

        # ── Build tools ──────────────────────────────────────────
        'emotion-babel-plugin': re.compile(
            r"@emotion/babel-plugin|babel-plugin-emotion|"
            r"@emotion/babel-preset-css-prop",
            re.MULTILINE
        ),
        'swc-plugin-emotion': re.compile(
            r"@swc/plugin-emotion|emotion.*compiler|compiler.*emotion",
            re.MULTILINE
        ),

        # ── Utilities ────────────────────────────────────────────
        'facepaint': re.compile(
            r"from\s+['\"]facepaint['/\"]|require\(['\"]facepaint['\"]\)",
            re.MULTILINE
        ),
        'emotion-reset': re.compile(
            r"from\s+['\"]emotion-reset['/\"]",
            re.MULTILINE
        ),
        'polished': re.compile(
            r"from\s+['\"]polished['/\"]|require\(['\"]polished['\"]\)",
            re.MULTILINE
        ),
        'twin-macro': re.compile(
            r"from\s+['\"]twin\.macro['/\"]",
            re.MULTILINE
        ),

        # ── Testing ──────────────────────────────────────────────
        'jest-emotion': re.compile(
            r"from\s+['\"]jest-emotion['/\"]",
            re.MULTILINE
        ),

        # ── SSR Frameworks ───────────────────────────────────────
        'next-js': re.compile(
            r"from\s+['\"]next['/\"]|"
            r"getInitialProps|getServerSideProps|_document",
            re.MULTILINE
        ),
        'gatsby-plugin-emotion': re.compile(
            r"gatsby-plugin-emotion|"
            r"from\s+['\"]gatsby['/\"]",
            re.MULTILINE
        ),
        'remix': re.compile(
            r"from\s+['\"]@remix-run/react['/\"]",
            re.MULTILINE
        ),

        # ── Styled-components (co-existence detection) ───────────
        'styled-components': re.compile(
            r"from\s+['\"]styled-components['/\"]|"
            r"require\(['\"]styled-components['\"]\)",
            re.MULTILINE
        ),
    }

    # Version detection based on import patterns
    VERSION_INDICATORS = {
        'v11': [
            r"from\s+['\"]@emotion/react['/\"]",
            r"from\s+['\"]@emotion/styled['/\"]",
            r"from\s+['\"]@emotion/css['/\"]",
            r"from\s+['\"]@emotion/cache['/\"]",
            r"from\s+['\"]@emotion/server['/\"]",
            r"jsxImportSource\s+@emotion/react",
            r"@swc/plugin-emotion",
        ],
        'v10': [
            r"from\s+['\"]@emotion/core['/\"]",
            r"from\s+['\"]emotion-theming['/\"]",
            r"@emotion/babel-preset-css-prop",
        ],
        'v9': [
            r"from\s+['\"]emotion['/\"]",
            r"from\s+['\"]react-emotion['/\"]",
            r"from\s+['\"]create-emotion['/\"]",
            r"injectGlobal",
            r"hydrate\s*\(",
        ],
    }

    VERSION_PRIORITY = {'v11': 3, 'v10': 2, 'v9': 1}

    def __init__(self):
        """Initialize the parser with all Emotion extractors."""
        self.component_extractor = EmotionComponentExtractor()
        self.theme_extractor = EmotionThemeExtractor()
        self.style_extractor = EmotionStyleExtractor()
        self.animation_extractor = EmotionAnimationExtractor()
        self.api_extractor = EmotionApiExtractor()

    def parse(self, content: str, file_path: str = "") -> EmotionParseResult:
        """
        Parse source code and extract all Emotion CSS-in-JS information.

        This should be called AFTER the JavaScript/TypeScript parser has run,
        when Emotion is detected.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            EmotionParseResult with all extracted information
        """
        result = EmotionParseResult(file_path=file_path)

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

        # ── Detect Emotion packages ───────────────────────────────
        result.emotion_packages = self._detect_packages(content)

        # ── Extract components (@emotion/styled) ─────────────────
        comp_result = self.component_extractor.extract(content, file_path)
        result.components = comp_result.get('components', [])
        result.extended_components = comp_result.get('extended_components', [])

        # ── Extract theme ─────────────────────────────────────────
        theme_result = self.theme_extractor.extract(content, file_path)
        result.providers = theme_result.get('providers', [])
        result.global_styles = theme_result.get('global_styles', [])
        result.theme_usages = theme_result.get('theme_usages', [])

        # ── Extract styles ────────────────────────────────────────
        style_result = self.style_extractor.extract(content, file_path)
        result.css_props = style_result.get('css_props', [])
        result.css_functions = style_result.get('css_functions', [])
        result.classnames = style_result.get('classnames', [])
        result.style_patterns = style_result.get('style_patterns', [])
        result.dynamic_props = style_result.get('dynamic_props', [])
        result.media_queries = style_result.get('media_queries', [])

        # ── Extract animations ────────────────────────────────────
        anim_result = self.animation_extractor.extract(content, file_path)
        result.keyframes = anim_result.get('keyframes', [])
        result.animation_usages = anim_result.get('animation_usages', [])

        # ── Extract API patterns ──────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.caches = api_result.get('caches', [])
        result.ssr_patterns = api_result.get('ssr_patterns', [])
        result.babel_configs = api_result.get('babel_configs', [])
        result.test_patterns = api_result.get('test_patterns', [])

        # ── Compute metadata flags ────────────────────────────────
        result.has_css_prop = len(result.css_props) > 0
        result.has_styled = len(result.components) > 0
        result.has_theme_provider = len(result.providers) > 0
        result.has_global_styles = len(result.global_styles) > 0
        result.has_ssr = len(result.ssr_patterns) > 0
        result.has_cache = len(result.caches) > 0
        result.has_dynamic_styling = len(result.dynamic_props) > 0
        result.has_media_queries = len(result.media_queries) > 0
        result.has_keyframes = len(result.keyframes) > 0
        result.has_classnames = len(result.classnames) > 0
        result.has_cx = any(cn.has_cx_call for cn in result.classnames)
        result.has_pragma = any(
            bc.has_import_source for bc in result.babel_configs
        )

        # ── Detect version ────────────────────────────────────────
        result.emotion_version = self._detect_version(content)

        # ── Detect features ───────────────────────────────────────
        result.detected_features = self._detect_features(content, result)

        return result

    def is_emotion_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Emotion CSS-in-JS code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Emotion CSS-in-JS code
        """
        if not content:
            return False

        # Check for @emotion/* imports
        if re.search(r"from\s+['\"]@emotion/(?:react|styled|css|cache|core)['/\"]", content):
            return True

        # Check for legacy emotion imports
        if re.search(r"from\s+['\"](?:emotion|react-emotion|emotion-theming)['/\"]", content):
            return True

        # Check for require('@emotion/*')
        if re.search(r"require\(['\"]@emotion/(?:react|styled|css|cache)['/\"]", content):
            return True

        # Check for JSX pragma
        if re.search(r"@jsxImportSource\s+@emotion/react|@jsx\s+jsx", content):
            return True

        # Check for css prop with emotion import context
        if re.search(r"\bcss\s*=\s*\{", content) and re.search(r"@emotion|emotion", content):
            return True

        # Check for Global component
        if re.search(r"<Global\s+styles\s*=", content):
            return True

        # Check for ClassNames component
        if re.search(r"<ClassNames\b", content) and re.search(r"@emotion", content):
            return True

        # Check for CacheProvider
        if re.search(r"<CacheProvider\b", content):
            return True

        return False

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Emotion ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return sorted(frameworks)

    def _detect_packages(self, content: str) -> List[str]:
        """Detect which @emotion packages are imported."""
        packages = []
        pkg_patterns = {
            '@emotion/react': r"from\s+['\"]@emotion/react",
            '@emotion/styled': r"from\s+['\"]@emotion/styled",
            '@emotion/css': r"from\s+['\"]@emotion/css",
            '@emotion/cache': r"from\s+['\"]@emotion/cache",
            '@emotion/server': r"from\s+['\"]@emotion/server",
            '@emotion/jest': r"from\s+['\"]@emotion/jest",
            '@emotion/core': r"from\s+['\"]@emotion/core",
            '@emotion/babel-plugin': r"@emotion/babel-plugin",
            'emotion': r"from\s+['\"]emotion['/\"]",
            'react-emotion': r"from\s+['\"]react-emotion",
            'emotion-theming': r"from\s+['\"]emotion-theming",
        }
        for pkg, pattern in pkg_patterns.items():
            if re.search(pattern, content):
                packages.append(pkg)
        return sorted(packages)

    def _detect_version(self, content: str) -> str:
        """Detect the Emotion version from import patterns."""
        max_version = ''
        max_priority = -1

        for version, indicators in self.VERSION_INDICATORS.items():
            for indicator in indicators:
                if re.search(indicator, content):
                    priority = self.VERSION_PRIORITY.get(version, 0)
                    if priority > max_priority:
                        max_version = version
                        max_priority = priority
                    break

        return max_version

    def _detect_features(
        self, content: str, result: EmotionParseResult
    ) -> List[str]:
        """Detect Emotion features used in the file."""
        features: List[str] = []

        # css prop (signature Emotion feature)
        if result.has_css_prop:
            features.append('css_prop')
            syntaxes = set(cp.syntax for cp in result.css_props)
            for s in sorted(syntaxes):
                features.append(f'css_prop_{s}')

        # @emotion/styled components
        if result.has_styled:
            features.append('styled_components')
            methods = set(c.method for c in result.components)
            for m in sorted(methods):
                cleaned = m.replace("(", "_").replace(")", "").replace(".", "_").replace("'", "")
                features.append(f'styled_{cleaned}')

        # css function / template
        if result.css_functions:
            features.append('css_function')
            syntaxes = set(cf.syntax for cf in result.css_functions)
            for s in sorted(syntaxes):
                features.append(f'css_{s}')

        # ClassNames render prop
        if result.has_classnames:
            features.append('classnames_component')

        # cx composition
        if result.has_cx:
            features.append('cx_composition')

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

        # Media queries
        if result.has_media_queries:
            features.append('media_queries')
            if any(mq.approach == 'facepaint' for mq in result.media_queries):
                features.append('facepaint')

        # Animations
        if result.has_keyframes:
            features.append('keyframes_animations')

        # Cache
        if result.has_cache:
            features.append('custom_cache')

        # SSR
        if result.has_ssr:
            features.append('server_side_rendering')
            for ssr in result.ssr_patterns:
                if ssr.framework:
                    features.append(f'ssr_{ssr.framework}')

        # Pragma
        if result.has_pragma:
            features.append('jsx_pragma')

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
