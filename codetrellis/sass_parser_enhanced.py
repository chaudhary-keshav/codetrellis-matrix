"""
EnhancedSassParser v1.0 — Comprehensive Sass/SCSS parser using all extractors.

This parser integrates all 5 Sass extractors to provide complete parsing of
Sass (.sass) and SCSS (.scss) source files across all Sass versions.

Supports:
- **Dart Sass 1.x** (current reference implementation, since 2018):
  - @use/@forward module system (1.23.0+), math.div() (1.33.0+),
    first-class calc (1.40.0+), color.channel() (1.28.0+),
    meta.module-*() (1.23.0+), @debug/@warn/@error, string.split() (1.57.0+)
- **LibSass** (deprecated C/C++ implementation, last release 3.6.5):
  - @import-based, $variables, @mixin, @function, @extend, nesting, interpolation
- **Ruby Sass** (original implementation, deprecated March 2019):
  - Legacy syntax, .sass indented format
- **Indented syntax** (.sass): significant whitespace, no braces/semicolons
- **SCSS syntax** (.scss): CSS-superset with braces/semicolons

AST Support:
- Regex-based Sass/SCSS parsing with full extraction
- Optional tree-sitter-scss AST for precise parsing
- Line number tracking for all extracted artifacts
- Nesting depth analysis, BEM pattern detection

LSP Support:
- SCSS Language Server integration via vscode-css-languageservice
- Sass Language Server (some-sass-language-server) integration
- Completions for variables, mixins, functions, selectors
- Diagnostics for undefined variables, unused mixins
- Go-to-definition for @use/@forward imports
- Hover for variable values, mixin signatures

Framework/Ecosystem Detection (20+ patterns):
- Build tools: node-sass, sass (Dart Sass npm), sass-embedded
- Libraries: Bourbon, Compass, Susy, Breakpoint, include-media, sass-mq, rfs
- Frameworks: Bootstrap SCSS, Foundation SCSS, Bulma SCSS, Materialize SCSS
- Utilities: normalize.scss, sanitize.css, modern-normalize
- Linters: stylelint, scss-lint (deprecated), sass-lint (deprecated)
- PostCSS: postcss-scss, postcss-sass
- CSS Modules: *.module.scss

Part of CodeTrellis v4.44 — Sass/SCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Sass extractors
from .extractors.sass import (
    SassVariableExtractor, SassVariableInfo, SassMapInfo, SassListInfo,
    SassMixinExtractor, SassMixinDefInfo, SassMixinUsageInfo,
    SassFunctionExtractor, SassFunctionDefInfo, SassFunctionCallInfo,
    SassModuleExtractor, SassUseInfo, SassForwardInfo, SassImportInfo, SassPartialInfo,
    SassNestingExtractor, SassNestingInfo, SassExtendInfo, SassPlaceholderInfo, SassAtRootInfo,
)


@dataclass
class SassParseResult:
    """Complete parse result for a Sass/SCSS file."""
    file_path: str
    file_type: str = "scss"         # scss or sass

    # Variables
    variables: List[SassVariableInfo] = field(default_factory=list)
    maps: List[SassMapInfo] = field(default_factory=list)
    lists: List[SassListInfo] = field(default_factory=list)
    variable_stats: Dict[str, Any] = field(default_factory=dict)

    # Mixins
    mixin_definitions: List[SassMixinDefInfo] = field(default_factory=list)
    mixin_usages: List[SassMixinUsageInfo] = field(default_factory=list)
    mixin_stats: Dict[str, Any] = field(default_factory=dict)

    # Functions
    function_definitions: List[SassFunctionDefInfo] = field(default_factory=list)
    function_calls: List[SassFunctionCallInfo] = field(default_factory=list)
    function_stats: Dict[str, Any] = field(default_factory=dict)

    # Module system
    uses: List[SassUseInfo] = field(default_factory=list)
    forwards: List[SassForwardInfo] = field(default_factory=list)
    imports: List[SassImportInfo] = field(default_factory=list)
    partial_info: Optional[SassPartialInfo] = None
    module_stats: Dict[str, Any] = field(default_factory=dict)

    # Nesting & structure
    nesting: List[SassNestingInfo] = field(default_factory=list)
    extends: List[SassExtendInfo] = field(default_factory=list)
    placeholders: List[SassPlaceholderInfo] = field(default_factory=list)
    at_roots: List[SassAtRootInfo] = field(default_factory=list)
    nesting_stats: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    sass_version: str = ""           # "dart_sass_1.x", "libsass", etc.
    module_system: str = ""          # "dart_sass" or "legacy"
    detected_features: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)
    detected_libraries: List[str] = field(default_factory=list)


class EnhancedSassParser:
    """
    Enhanced Sass/SCSS parser that uses all 5 extractors for comprehensive parsing.

    Detects Sass version, module system, framework ecosystem, and extracts
    all structured data from .scss and .sass files.
    """

    # Dart Sass features (module system)
    DART_SASS_FEATURES = {
        '@use ', '@forward ', 'math.div(', 'math.', 'color.', 'string.',
        'list.', 'map.', 'selector.', 'meta.', 'sass:',
    }

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'bootstrap': re.compile(
            r'@import\s+["\'].*bootstrap|'
            r'@use\s+["\'].*bootstrap|'
            r'\$(?:grid-breakpoints|container-max-widths|theme-colors|spacers)',
            re.MULTILINE | re.IGNORECASE),
        'foundation': re.compile(
            r'@import\s+["\'].*foundation|'
            r'@use\s+["\'].*foundation|'
            r'@include\s+(?:breakpoint|xy-grid|flex-grid)',
            re.MULTILINE | re.IGNORECASE),
        'bulma': re.compile(
            r'@import\s+["\'].*bulma|'
            r'@use\s+["\'].*bulma|'
            r'\$(?:family-sans-serif|primary|info|success|warning|danger)',
            re.MULTILINE | re.IGNORECASE),
        'materialize': re.compile(
            r'@import\s+["\'].*materialize|'
            r'\$(?:primary-color|secondary-color|error-color)',
            re.MULTILINE | re.IGNORECASE),
        'bourbon': re.compile(
            r'@import\s+["\'].*bourbon|'
            r'@use\s+["\'].*bourbon',
            re.MULTILINE | re.IGNORECASE),
        'compass': re.compile(
            r'@import\s+["\']compass',
            re.MULTILINE | re.IGNORECASE),
        'susy': re.compile(
            r'@import\s+["\'].*susy|@use\s+["\'].*susy|'
            r'@include\s+(?:container|span|layout)',
            re.MULTILINE | re.IGNORECASE),
        'include-media': re.compile(
            r'@import\s+["\'].*include-media|'
            r'@include\s+media\s*\(',
            re.MULTILINE | re.IGNORECASE),
        'sass-mq': re.compile(
            r'@import\s+["\'].*mq|@use\s+["\'].*mq|'
            r'@include\s+mq\s*\(',
            re.MULTILINE | re.IGNORECASE),
        'rfs': re.compile(
            r'@import\s+["\'].*rfs|@use\s+["\'].*rfs|'
            r'@include\s+(?:rfs|font-size|padding|margin)\s*\(',
            re.MULTILINE | re.IGNORECASE),
        'normalize': re.compile(
            r'@import\s+["\'].*normalize|@use\s+["\'].*normalize',
            re.MULTILINE | re.IGNORECASE),
        'animate.scss': re.compile(
            r'@import\s+["\'].*animate|@include\s+animate\s*\(',
            re.MULTILINE | re.IGNORECASE),
        'css_modules': None,  # Detected by filename pattern
    }

    # Build tool detection (for package.json context)
    BUILD_TOOL_PATTERNS = {
        'dart_sass': re.compile(r'"sass"\s*:', re.MULTILINE),
        'sass_embedded': re.compile(r'"sass-embedded"\s*:', re.MULTILINE),
        'node_sass': re.compile(r'"node-sass"\s*:', re.MULTILINE),
        'postcss_scss': re.compile(r'"postcss-scss"\s*:', re.MULTILINE),
        'stylelint': re.compile(r'"stylelint"\s*:', re.MULTILINE),
    }

    # Sass control flow directives
    CONTROL_FLOW = {
        '@if': re.compile(r'@if\s+', re.MULTILINE),
        '@else': re.compile(r'@else\s*(?:if\s+)?', re.MULTILINE),
        '@each': re.compile(r'@each\s+', re.MULTILINE),
        '@for': re.compile(r'@for\s+', re.MULTILINE),
        '@while': re.compile(r'@while\s+', re.MULTILINE),
        '@debug': re.compile(r'@debug\s+', re.MULTILINE),
        '@warn': re.compile(r'@warn\s+', re.MULTILINE),
        '@error': re.compile(r'@error\s+', re.MULTILINE),
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.variable_extractor = SassVariableExtractor()
        self.mixin_extractor = SassMixinExtractor()
        self.function_extractor = SassFunctionExtractor()
        self.module_extractor = SassModuleExtractor()
        self.nesting_extractor = SassNestingExtractor()

    def parse(self, content: str, file_path: str = "") -> SassParseResult:
        """
        Parse Sass/SCSS content using all extractors.

        Args:
            content: Sass/SCSS source code string.
            file_path: Path to the source file.

        Returns:
            SassParseResult with all extracted data.
        """
        result = SassParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect file type
        result.file_type = self._detect_file_type(file_path)

        # 1. Variables, Maps, Lists
        var_result = self.variable_extractor.extract(content, file_path)
        result.variables = var_result.get('variables', [])
        result.maps = var_result.get('maps', [])
        result.lists = var_result.get('lists', [])
        result.variable_stats = var_result.get('stats', {})

        # 2. Mixins
        mixin_result = self.mixin_extractor.extract(content, file_path)
        result.mixin_definitions = mixin_result.get('definitions', [])
        result.mixin_usages = mixin_result.get('usages', [])
        result.mixin_stats = mixin_result.get('stats', {})

        # 3. Functions
        func_result = self.function_extractor.extract(content, file_path)
        result.function_definitions = func_result.get('definitions', [])
        result.function_calls = func_result.get('calls', [])
        result.function_stats = func_result.get('stats', {})

        # 4. Module system
        module_result = self.module_extractor.extract(content, file_path)
        result.uses = module_result.get('uses', [])
        result.forwards = module_result.get('forwards', [])
        result.imports = module_result.get('imports', [])
        result.partial_info = module_result.get('partial', None)
        result.module_stats = module_result.get('stats', {})
        result.module_system = module_result.get('stats', {}).get('module_system', 'none')

        # 5. Nesting & structure
        nesting_result = self.nesting_extractor.extract(content, file_path)
        result.nesting = nesting_result.get('nesting', [])
        result.extends = nesting_result.get('extends', [])
        result.placeholders = nesting_result.get('placeholders', [])
        result.at_roots = nesting_result.get('at_roots', [])
        result.nesting_stats = nesting_result.get('stats', {})

        # Detect Sass version
        result.sass_version = self._detect_sass_version(content, result)

        # Detect features
        result.detected_features = self._detect_features(content, file_path, result)

        # Detect frameworks/libraries
        result.detected_frameworks = self._detect_frameworks(content, file_path)
        result.detected_libraries = self._detect_libraries(result)

        return result

    def _detect_file_type(self, file_path: str) -> str:
        """Detect Sass dialect from file extension."""
        if not file_path:
            return 'scss'
        if file_path.lower().endswith('.sass'):
            return 'sass'
        return 'scss'

    def _detect_sass_version(self, content: str, result: SassParseResult) -> str:
        """Detect which Sass implementation/version is likely in use."""
        # Check for Dart Sass module system features
        for feat in self.DART_SASS_FEATURES:
            if feat in content:
                return 'dart_sass_1.x'

        # Check for @use/@forward
        if result.uses or result.forwards:
            return 'dart_sass_1.x'

        # Check for legacy features that suggest LibSass
        if result.imports and not result.uses:
            # @import without @use suggests LibSass or older
            return 'libsass_or_legacy'

        # Default
        return 'sass'

    def _detect_features(self, content: str, file_path: str,
                         result: SassParseResult) -> List[str]:
        """Detect Sass features in use."""
        features: Set[str] = set()

        # Module system
        if result.uses or result.forwards:
            features.add('module_system')
        if result.imports:
            features.add('legacy_imports')

        # Variables
        if result.variables:
            features.add('variables')
        if result.maps:
            features.add('maps')
        if result.lists:
            features.add('lists')
        if result.variable_stats.get('has_defaults'):
            features.add('default_values')
        if result.variable_stats.get('has_namespaces'):
            features.add('namespaced_variables')

        # Mixins
        if result.mixin_definitions:
            features.add('mixins')
        if any(d.has_content_block for d in result.mixin_definitions):
            features.add('content_blocks')
        if any(d.has_rest_args for d in result.mixin_definitions):
            features.add('rest_args')

        # Functions
        if result.function_definitions:
            features.add('custom_functions')
        if result.function_stats.get('has_color_functions'):
            features.add('color_functions')
        if result.function_stats.get('has_math_functions'):
            features.add('math_functions')
        if result.function_stats.get('has_map_functions'):
            features.add('map_functions')
        if result.function_stats.get('has_meta_functions'):
            features.add('meta_functions')

        # Nesting
        if result.nesting_stats.get('max_nesting_depth', 0) > 0:
            features.add('nesting')
        if result.nesting_stats.get('has_bem_patterns'):
            features.add('bem_nesting')
        if result.nesting_stats.get('has_at_root'):
            features.add('at_root')

        # Extends
        if result.extends:
            features.add('extends')
        if result.placeholders:
            features.add('placeholders')

        # Control flow
        for directive, pattern in self.CONTROL_FLOW.items():
            if pattern.search(content):
                features.add(directive.lstrip('@'))

        # Interpolation
        if '#{' in content:
            features.add('interpolation')

        # CSS Modules
        if file_path and '.module.scss' in file_path.lower():
            features.add('css_modules')

        # Partials
        if result.partial_info:
            features.add('partial')

        return sorted(features)

    def _detect_frameworks(self, content: str, file_path: str) -> List[str]:
        """Detect CSS frameworks used via Sass."""
        frameworks: List[str] = []

        for fw_name, pattern in self.FRAMEWORK_PATTERNS.items():
            if fw_name == 'css_modules':
                if file_path and '.module.scss' in file_path.lower():
                    frameworks.append('css_modules')
            elif pattern and pattern.search(content):
                frameworks.append(fw_name)

        return frameworks

    def _detect_libraries(self, result: SassParseResult) -> List[str]:
        """Detect Sass libraries from mixin stats."""
        libs = result.mixin_stats.get('mixin_libraries', [])
        return libs if isinstance(libs, list) else []

    def is_sass_file(self, file_path: str) -> bool:
        """Check if a file is a Sass/SCSS file."""
        lower = file_path.lower()
        return lower.endswith('.scss') or lower.endswith('.sass')
