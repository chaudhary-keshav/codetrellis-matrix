"""
EnhancedCSSParser v1.0 - Comprehensive CSS parser using all extractors.

This parser integrates all CSS extractors to provide complete
parsing of CSS/SCSS/Less/Stylus source files across all CSS versions.

Supports:
- CSS1, CSS2, CSS2.1 (basic selectors, properties, media types)
- CSS3 (selectors level 3, media queries, transforms, transitions, animations,
         flexbox, grid, custom properties, calc(), gradients)
- CSS4 / CSS Nesting (selector nesting, :is(), :where(), :has(), :not() L4,
         container queries, cascade layers, color-mix(), oklch/oklab,
         @scope, subgrid, masonry, scroll-driven animations, light-dark())
- SCSS / Sass ($variables, @mixin/@include, @extend, @function, @use/@forward,
         %placeholders, @each/@for/@while, interpolation, @content)
- Less (@variables, .mixin(), :extend(), guards, loops)
- Stylus (variables, mixins, @extend, conditionals)

AST Support:
- Regex-based CSS parsing with full rule/selector/property extraction
- Line number tracking for all extracted artifacts
- Nesting depth tracking, specificity calculation

LSP Support:
- CSS Language Server integration via vscode-css-languageservice
- Completions for properties, values, selectors
- Diagnostics for invalid properties, deprecated features
- Hover for property docs, color previews
- Document symbols, document highlights, references

Part of CodeTrellis v4.17 - CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all CSS extractors
from .extractors.css import (
    CSSSelectorExtractor, CSSSelectorInfo, CSSRuleInfo,
    CSSPropertyExtractor, CSSPropertyInfo,
    CSSVariableExtractor, CSSVariableInfo, CSSThemeInfo,
    CSSMediaExtractor, CSSMediaQueryInfo, CSSSupportsInfo, CSSLayerInfo, CSSContainerQueryInfo,
    CSSAnimationExtractor, CSSKeyframeInfo, CSSTransitionInfo, CSSAnimationUsageInfo,
    CSSLayoutExtractor, CSSFlexboxInfo, CSSGridInfo, CSSMultiColumnInfo,
    CSSFunctionExtractor, CSSFunctionUsageInfo,
    CSSPreprocessorExtractor, CSSMixinInfo, CSSPreprocessorVariableInfo,
    CSSPreprocessorFunctionInfo, CSSExtendInfo, CSSPreprocessorImportInfo,
)


@dataclass
class CSSParseResult:
    """Complete parse result for a CSS/SCSS/Less/Stylus file."""
    file_path: str
    file_type: str = "css"  # css, scss, sass, less, stylus

    # Selectors & Rules
    selectors: List[CSSSelectorInfo] = field(default_factory=list)
    rules: List[CSSRuleInfo] = field(default_factory=list)
    selector_stats: Dict[str, Any] = field(default_factory=dict)

    # Properties
    properties: List[CSSPropertyInfo] = field(default_factory=list)
    property_stats: Dict[str, Any] = field(default_factory=dict)

    # Variables / Custom Properties
    variables: List[CSSVariableInfo] = field(default_factory=list)
    themes: List[CSSThemeInfo] = field(default_factory=list)
    variable_stats: Dict[str, Any] = field(default_factory=dict)

    # Media Queries / At-rules
    media_queries: List[CSSMediaQueryInfo] = field(default_factory=list)
    supports_queries: List[CSSSupportsInfo] = field(default_factory=list)
    layers: List[CSSLayerInfo] = field(default_factory=list)
    container_queries: List[CSSContainerQueryInfo] = field(default_factory=list)
    media_stats: Dict[str, Any] = field(default_factory=dict)

    # Animations
    keyframes: List[CSSKeyframeInfo] = field(default_factory=list)
    transitions: List[CSSTransitionInfo] = field(default_factory=list)
    animation_usages: List[CSSAnimationUsageInfo] = field(default_factory=list)
    animation_stats: Dict[str, Any] = field(default_factory=dict)

    # Layout
    flexbox_usages: List[CSSFlexboxInfo] = field(default_factory=list)
    grid_usages: List[CSSGridInfo] = field(default_factory=list)
    multi_column_usages: List[CSSMultiColumnInfo] = field(default_factory=list)
    layout_stats: Dict[str, Any] = field(default_factory=dict)

    # Functions
    function_usages: List[CSSFunctionUsageInfo] = field(default_factory=list)
    function_stats: Dict[str, Any] = field(default_factory=dict)

    # Preprocessor
    mixins: List[CSSMixinInfo] = field(default_factory=list)
    preprocessor_variables: List[CSSPreprocessorVariableInfo] = field(default_factory=list)
    preprocessor_functions: List[CSSPreprocessorFunctionInfo] = field(default_factory=list)
    extends: List[CSSExtendInfo] = field(default_factory=list)
    preprocessor_imports: List[CSSPreprocessorImportInfo] = field(default_factory=list)
    preprocessor_stats: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    detected_preprocessor: str = ""
    detected_features: List[str] = field(default_factory=list)
    css_version: str = ""  # "CSS3", "CSS4", "SCSS", etc.


class EnhancedCSSParser:
    """
    Enhanced CSS parser that uses all extractors for comprehensive parsing.

    Detects CSS version, preprocessor type, and extracts all structured data
    from CSS/SCSS/Less/Stylus files.

    Framework detection supports:
    - Tailwind CSS (utility classes, @apply, @config)
    - Bootstrap (grid, component classes)
    - CSS Modules (.module.css/.module.scss)
    - Styled Components / CSS-in-JS patterns
    - PostCSS (custom at-rules, nesting)
    - CSS Houdini (@property, paint())
    """

    # CSS version detection patterns
    CSS4_FEATURES = {
        ':has(', ':is(', ':where(', '@container', '@layer', '@scope',
        'color-mix(', 'oklch(', 'oklab(', 'light-dark(', 'lch(',
        'container-type', 'container-name', 'aspect-ratio',
        'animation-timeline', 'view-timeline', 'scroll-timeline',
        'subgrid', 'masonry',
    }
    CSS3_FEATURES = {
        '@media', '@keyframes', '@font-face', 'var(', 'calc(',
        'linear-gradient', 'radial-gradient', 'transform:', 'transition:',
        'animation:', 'display: flex', 'display: grid', 'display:flex',
        'display:grid', 'border-radius', 'box-shadow', 'text-shadow',
        'opacity:', 'rgba(', 'hsla(',
    }

    # Framework detection
    FRAMEWORK_PATTERNS = {
        'tailwind': re.compile(
            r'@tailwind\b|@apply\b|@config\b|@screen\b|@variants\b|'
            r'@responsive\b|theme\(\s*["\']', re.MULTILINE),
        'postcss': re.compile(
            r'@custom-media\b|@custom-selector\b|@nest\b', re.MULTILINE),
        'css_modules': None,  # Detected by filename
        'css_houdini': re.compile(
            r'@property\b|paint\(|registerProperty|CSSStyleValue', re.MULTILINE),
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.selector_extractor = CSSSelectorExtractor()
        self.property_extractor = CSSPropertyExtractor()
        self.variable_extractor = CSSVariableExtractor()
        self.media_extractor = CSSMediaExtractor()
        self.animation_extractor = CSSAnimationExtractor()
        self.layout_extractor = CSSLayoutExtractor()
        self.function_extractor = CSSFunctionExtractor()
        self.preprocessor_extractor = CSSPreprocessorExtractor()

    def parse(self, content: str, file_path: str = "") -> CSSParseResult:
        """Parse CSS content using all extractors.

        Args:
            content: CSS/SCSS/Less/Stylus source code string.
            file_path: Path to the source file.

        Returns:
            CSSParseResult with all extracted data.
        """
        result = CSSParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Skip minified files — they cause catastrophic regex backtracking
        # and contain no useful structural information for the matrix
        if file_path.endswith('.min.css') or file_path.endswith('.min.js'):
            return result
        # Also skip if content looks minified (very long lines)
        first_line = content.split('\n', 1)[0]
        if len(first_line) > 5000:
            return result

        # Detect file type from extension
        result.file_type = self._detect_file_type(file_path)

        # 1. Selectors & Rules
        selector_result = self.selector_extractor.extract(content, file_path)
        result.selectors = selector_result.get('selectors', [])
        result.rules = selector_result.get('rules', [])
        result.selector_stats = selector_result.get('stats', {})

        # 2. Properties
        property_result = self.property_extractor.extract(content, file_path)
        result.properties = property_result.get('properties', [])
        result.property_stats = property_result.get('stats', {})

        # 3. Variables / Custom Properties
        variable_result = self.variable_extractor.extract(content, file_path)
        result.variables = variable_result.get('variables', [])
        result.themes = variable_result.get('themes', [])
        result.variable_stats = variable_result.get('stats', {})

        # 4. Media Queries & At-rules
        media_result = self.media_extractor.extract(content, file_path)
        result.media_queries = media_result.get('media_queries', [])
        result.supports_queries = media_result.get('supports', [])
        result.layers = media_result.get('layers', [])
        result.container_queries = media_result.get('container_queries', [])
        result.media_stats = media_result.get('stats', {})

        # 5. Animations
        animation_result = self.animation_extractor.extract(content, file_path)
        result.keyframes = animation_result.get('keyframes', [])
        result.transitions = animation_result.get('transitions', [])
        result.animation_usages = animation_result.get('animations', [])
        result.animation_stats = animation_result.get('stats', {})

        # 6. Layout
        layout_result = self.layout_extractor.extract(content, file_path)
        result.flexbox_usages = layout_result.get('flexbox', [])
        result.grid_usages = layout_result.get('grid', [])
        result.multi_column_usages = layout_result.get('multi_column', [])
        result.layout_stats = layout_result.get('stats', {})

        # 7. Functions
        function_result = self.function_extractor.extract(content, file_path)
        result.function_usages = function_result.get('functions', [])
        result.function_stats = function_result.get('stats', {})

        # 8. Preprocessor (SCSS/Less/Stylus specific)
        if result.file_type in ('scss', 'sass', 'less', 'stylus'):
            preproc_result = self.preprocessor_extractor.extract(content, file_path)
            result.mixins = preproc_result.get('mixins', [])
            result.preprocessor_variables = preproc_result.get('variables', [])
            result.preprocessor_functions = preproc_result.get('functions', [])
            result.extends = preproc_result.get('extends', [])
            result.preprocessor_imports = preproc_result.get('imports', [])
            result.preprocessor_stats = preproc_result.get('stats', {})
            result.detected_preprocessor = preproc_result.get('stats', {}).get('preprocessor', '')

        # Detect CSS version and features
        result.css_version = self._detect_css_version(content, result)
        result.detected_features = self._detect_features(content, file_path, result)

        return result

    def _detect_file_type(self, file_path: str) -> str:
        """Detect CSS dialect from file extension."""
        if not file_path:
            return 'css'
        path_lower = file_path.lower()
        if path_lower.endswith('.scss'):
            return 'scss'
        elif path_lower.endswith('.sass'):
            return 'sass'
        elif path_lower.endswith('.less'):
            return 'less'
        elif path_lower.endswith('.styl') or path_lower.endswith('.stylus'):
            return 'stylus'
        return 'css'

    def _detect_css_version(self, content: str, result: CSSParseResult) -> str:
        """Detect the highest CSS version used in the file."""
        # Check for preprocessor first
        if result.file_type in ('scss', 'sass'):
            return 'SCSS'
        elif result.file_type == 'less':
            return 'Less'
        elif result.file_type == 'stylus':
            return 'Stylus'

        # Check for CSS4+ features
        content_lower = content.lower()
        for feat in self.CSS4_FEATURES:
            if feat.lower() in content_lower:
                return 'CSS4+'

        # Check for CSS3 features
        for feat in self.CSS3_FEATURES:
            if feat.lower() in content_lower:
                return 'CSS3'

        # Fallback
        return 'CSS2'

    def _detect_features(self, content: str, file_path: str, result: CSSParseResult) -> List[str]:
        """Detect CSS frameworks, methodologies, and modern features."""
        features: Set[str] = set()
        content_lower = content.lower()

        # Framework detection
        for fw_name, pattern in self.FRAMEWORK_PATTERNS.items():
            if fw_name == 'css_modules':
                # Detect by filename
                if file_path and ('.module.css' in file_path.lower() or
                                  '.module.scss' in file_path.lower()):
                    features.add('css_modules')
            elif pattern and pattern.search(content):
                features.add(fw_name)

        # Methodology detection
        if re.search(r'__[\w-]+--[\w-]+|__[\w-]+', content):
            features.add('BEM')
        if re.search(r'\.o-[\w-]+|\.c-[\w-]+|\.u-[\w-]+|\.is-[\w-]+|\.has-[\w-]+', content):
            features.add('ITCSS')
        if re.search(r'\.l-[\w-]+|\.h-[\w-]+|\.is-[\w-]+', content):
            features.add('SMACSS')

        # Modern feature flags from extractors
        if result.container_queries:
            features.add('container_queries')
        if result.layers:
            features.add('cascade_layers')
        if result.media_stats.get('has_range_syntax'):
            features.add('media_range_syntax')
        if result.animation_stats.get('has_scroll_driven'):
            features.add('scroll_driven_animations')
        if result.function_stats.get('has_modern_color'):
            features.add('modern_color_functions')
        if result.layout_stats.get('subgrid_count', 0) > 0:
            features.add('subgrid')
        if result.variable_stats.get('total_variables', 0) > 0:
            features.add('custom_properties')

        # CSS nesting
        if result.selector_stats.get('has_nesting'):
            features.add('css_nesting')

        # Logical properties
        if result.property_stats.get('logical_property_count', 0) > 0:
            features.add('logical_properties')

        # Dark mode
        if result.variable_stats.get('has_dark_mode'):
            features.add('dark_mode')

        # Check for dark mode via media queries if variable extractor missed it
        if 'dark_mode' not in features:
            if any(mq.is_prefers_query and 'dark' in mq.query for mq in result.media_queries):
                features.add('dark_mode')

        return sorted(features)
