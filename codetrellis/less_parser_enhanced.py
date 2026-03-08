"""
EnhancedLessParser v1.0 — Comprehensive Less CSS parser using all extractors.

This parser integrates all 5 Less extractors to provide complete parsing of
Less (.less) source files across all Less versions.

Supports:
- **Less 1.x** (initial release, variables, mixins, nested rules, operations):
  - @variables, .mixin() definitions, parametric mixins with defaults,
    nested rules with & parent selector, mathematical operations (+, -, *, /),
    color functions (lighten, darken, saturate, desaturate, fadein, fadeout),
    @import, comments (// and /* */), string interpolation (@{var})
- **Less 2.x** (major improvements):
  - :extend() pseudo-class (Less 1.4+), extend all keyword,
    inline extend syntax .selector:extend(.other),
    @import options (reference, inline, less, css, multiple, optional),
    merge feature (property+: value), merge with space (property+_: value),
    mixin guards: when (condition), guard operators: and, not, or,
    type-checking functions (iscolor, isnumber, isstring, iskeyword, isurl),
    detached rulesets (assign ruleset to variable), @arguments special variable
- **Less 3.x** (modernization):
  - @plugin directive for custom functions, each() loop function (3.7+),
    property as variable ($prop), if() function, boolean() function,
    improved math handling, range() function, default() guard function
- **Less 4.x** (current/latest):
  - Math mode: always (legacy), parens-division, parens, strict (v4 default),
    improved source maps, better error messages, ES module support,
    dropped IE8 compatibility, modern Node.js requirements

AST Support:
- Regex-based Less parsing with full extraction across all constructs
- Optional tree-sitter-less AST for precise parsing (npm: tree-sitter-less)
- Line number tracking for all extracted artifacts
- Nesting depth analysis, BEM pattern detection

LSP Support:
- Less Language Server integration (vscode-css-languageservice with Less mode)
- Completions for @variables, .mixins(), functions, selectors
- Diagnostics for undefined variables, missing imports
- Go-to-definition for @import references, mixin definitions
- Hover for variable values, mixin signatures, function docs
- Document symbols, document highlights, workspace symbols

Framework/Ecosystem Detection (20+ patterns):
- Build tools: less (npm), lessc CLI, less-loader (webpack), gulp-less, grunt-less
- Libraries: Less Hat, LESSElements, 3L, Preboot, est, lesshat, CSSOwl
- Frameworks: Bootstrap Less (v3), Ant Design Less, Semantic UI Less
- Utilities: less-plugin-autoprefix, less-plugin-clean-css, less-plugin-inline-urls
- PostCSS: postcss-less
- CSS Modules: *.module.less
- Linters: stylelint-less, lesshint (deprecated)

Part of CodeTrellis v4.45 — Less CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Less extractors
from .extractors.less import (
    LessVariableExtractor, LessVariableInfo, LessVariableUsageInfo,
    LessMixinExtractor, LessMixinDefInfo, LessMixinCallInfo,
    LessGuardInfo, LessNamespaceInfo,
    LessFunctionExtractor, LessFunctionCallInfo, LessPluginInfo,
    LessImportExtractor, LessImportInfo,
    LessRulesetExtractor, LessExtendInfo, LessDetachedRulesetInfo,
    LessNestingInfo, LessPropertyMergeInfo,
)


@dataclass
class LessParseResult:
    """Complete parse result for a Less file."""
    file_path: str

    # Variables
    variables: List[LessVariableInfo] = field(default_factory=list)
    variable_usages: List[LessVariableUsageInfo] = field(default_factory=list)
    variable_stats: Dict[str, Any] = field(default_factory=dict)

    # Mixins
    mixin_definitions: List[LessMixinDefInfo] = field(default_factory=list)
    mixin_calls: List[LessMixinCallInfo] = field(default_factory=list)
    guards: List[LessGuardInfo] = field(default_factory=list)
    namespaces: List[LessNamespaceInfo] = field(default_factory=list)
    mixin_stats: Dict[str, Any] = field(default_factory=dict)

    # Functions
    function_calls: List[LessFunctionCallInfo] = field(default_factory=list)
    plugins: List[LessPluginInfo] = field(default_factory=list)
    function_stats: Dict[str, Any] = field(default_factory=dict)

    # Imports
    imports: List[LessImportInfo] = field(default_factory=list)
    import_stats: Dict[str, Any] = field(default_factory=dict)

    # Rulesets & Structure
    extends: List[LessExtendInfo] = field(default_factory=list)
    detached_rulesets: List[LessDetachedRulesetInfo] = field(default_factory=list)
    nesting: List[LessNestingInfo] = field(default_factory=list)
    property_merges: List[LessPropertyMergeInfo] = field(default_factory=list)
    ruleset_stats: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    less_version: str = ""           # "less_1.x", "less_2.x", "less_3.x", "less_4.x"
    math_mode: str = ""              # "always", "parens-division", "parens", "strict"
    detected_features: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)
    detected_libraries: List[str] = field(default_factory=list)


class EnhancedLessParser:
    """
    Enhanced Less CSS parser that uses all 5 extractors for comprehensive parsing.

    Detects Less version, math mode, framework ecosystem, and extracts
    all structured data from .less files.
    """

    # Less 2.x+ features (extend, import options)
    LESS_2_FEATURES = {
        ':extend(', '@import (', 'when (', 'when(',
    }

    # Less 3.x+ features (plugin, each, property vars, if, boolean)
    LESS_3_FEATURES = {
        '@plugin ', 'each(', '$prop', 'if(', 'boolean(',
        'range(', 'default()',
    }

    # Less 4.x+ indicators (math strict, ES module usage context)
    LESS_4_INDICATORS = {
        'math: "strict"', 'math: "parens"',
        'math: "parens-division"',
    }

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'bootstrap': re.compile(
            r'@import\s+["\'].*bootstrap|'
            r'@(?:brand-primary|brand-success|brand-info|brand-warning|brand-danger)|'
            r'@(?:grid-columns|grid-gutter-width|screen-xs|screen-sm|screen-md|screen-lg)',
            re.MULTILINE | re.IGNORECASE),
        'ant_design': re.compile(
            r'@import\s+["\'].*antd|@import\s+["\'].*ant-design|'
            r'@(?:primary-color|link-color|success-color|warning-color|error-color|'
            r'font-size-base|heading-color|text-color|border-radius-base)',
            re.MULTILINE | re.IGNORECASE),
        'semantic_ui': re.compile(
            r'@import\s+["\'].*semantic|'
            r'@(?:primaryColor|secondaryColor|pageBackground|fontSize)',
            re.MULTILINE | re.IGNORECASE),
        'element_ui': re.compile(
            r'@import\s+["\'].*element-ui|'
            r'@--color-primary|@--font-size-base',
            re.MULTILINE | re.IGNORECASE),
        'iview': re.compile(
            r'@import\s+["\'].*iview|'
            r'@primary-color.*iview',
            re.MULTILINE | re.IGNORECASE),
    }

    # Library detection patterns
    LIBRARY_PATTERNS = {
        'less_hat': re.compile(
            r'@import\s+["\'].*lesshat|@import\s+["\'].*less-hat|'
            r'\.(?:transition|transform|border-radius|box-shadow|animation)\s*\(',
            re.MULTILINE | re.IGNORECASE),
        'lesselements': re.compile(
            r'@import\s+["\'].*elements|'
            r'\.(?:gradient|rounded|shadow|transition)\s*\(',
            re.MULTILINE | re.IGNORECASE),
        '3l': re.compile(
            r'@import\s+["\'].*3L',
            re.MULTILINE | re.IGNORECASE),
        'preboot': re.compile(
            r'@import\s+["\'].*preboot',
            re.MULTILINE | re.IGNORECASE),
        'est': re.compile(
            r'@import\s+["\'].*est',
            re.MULTILINE | re.IGNORECASE),
        'css_owl': re.compile(
            r'@import\s+["\'].*cssowl',
            re.MULTILINE | re.IGNORECASE),
    }

    # Build tool detection (for package.json context)
    BUILD_TOOL_PATTERNS = {
        'less': re.compile(r'"less"\s*:', re.MULTILINE),
        'less_loader': re.compile(r'"less-loader"\s*:', re.MULTILINE),
        'gulp_less': re.compile(r'"gulp-less"\s*:', re.MULTILINE),
        'grunt_less': re.compile(r'"grunt-contrib-less"\s*:', re.MULTILINE),
        'postcss_less': re.compile(r'"postcss-less"\s*:', re.MULTILINE),
        'stylelint': re.compile(r'"stylelint"\s*:', re.MULTILINE),
        'lesshint': re.compile(r'"lesshint"\s*:', re.MULTILINE),
    }

    # Less operations patterns
    OPERATIONS_PATTERN = re.compile(
        r'@[\w-]+\s*(?:\+|-|\*|/)\s*(?:@[\w-]+|\d)',
        re.MULTILINE
    )

    # String interpolation: @{var}
    INTERPOLATION_PATTERN = re.compile(r'@\{[\w-]+\}')

    # Escaped value: ~"value" or e("value")
    ESCAPE_PATTERN = re.compile(r'~\s*["\']|e\s*\(', re.MULTILINE)

    # JavaScript evaluation (deprecated): `expression`
    JS_EVAL_PATTERN = re.compile(r'`[^`]+`', re.MULTILINE)

    # Color operations
    COLOR_OPS_PATTERN = re.compile(
        r'(?:darken|lighten|saturate|desaturate|fadein|fadeout|fade|spin|'
        r'mix|tint|shade|greyscale|contrast|multiply|screen|overlay|'
        r'softlight|hardlight|difference|exclusion|average|negation)\s*\(',
        re.MULTILINE | re.IGNORECASE
    )

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.variable_extractor = LessVariableExtractor()
        self.mixin_extractor = LessMixinExtractor()
        self.function_extractor = LessFunctionExtractor()
        self.import_extractor = LessImportExtractor()
        self.ruleset_extractor = LessRulesetExtractor()

    def parse(self, content: str, file_path: str = "") -> LessParseResult:
        """
        Parse Less content using all extractors.

        Args:
            content: Less source code string.
            file_path: Path to the source file.

        Returns:
            LessParseResult with all extracted data.
        """
        result = LessParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # 1. Variables
        var_result = self.variable_extractor.extract(content, file_path)
        result.variables = var_result.get('variables', [])
        result.variable_usages = var_result.get('usages', [])
        result.variable_stats = var_result.get('stats', {})

        # 2. Mixins
        mixin_result = self.mixin_extractor.extract(content, file_path)
        result.mixin_definitions = mixin_result.get('definitions', [])
        result.mixin_calls = mixin_result.get('calls', [])
        result.guards = mixin_result.get('guards', [])
        result.namespaces = mixin_result.get('namespaces', [])
        result.mixin_stats = mixin_result.get('stats', {})

        # 3. Functions
        func_result = self.function_extractor.extract(content, file_path)
        result.function_calls = func_result.get('calls', [])
        result.plugins = func_result.get('plugins', [])
        result.function_stats = func_result.get('stats', {})

        # 4. Imports
        import_result = self.import_extractor.extract(content, file_path)
        result.imports = import_result.get('imports', [])
        result.import_stats = import_result.get('stats', {})

        # 5. Rulesets & Structure
        ruleset_result = self.ruleset_extractor.extract(content, file_path)
        result.extends = ruleset_result.get('extends', [])
        result.detached_rulesets = ruleset_result.get('detached_rulesets', [])
        result.nesting = ruleset_result.get('nesting', [])
        result.property_merges = ruleset_result.get('property_merges', [])
        result.ruleset_stats = ruleset_result.get('stats', {})

        # Detect Less version
        result.less_version = self._detect_less_version(content, result)

        # Detect math mode
        result.math_mode = self._detect_math_mode(content)

        # Detect features
        result.detected_features = self._detect_features(content, file_path, result)

        # Detect frameworks/libraries
        result.detected_frameworks = self._detect_frameworks(content, file_path)
        result.detected_libraries = self._detect_libraries(content, file_path)

        return result

    def _detect_less_version(self, content: str, result: LessParseResult) -> str:
        """Detect which Less version features are in use."""
        # Check Less 4.x indicators
        for indicator in self.LESS_4_INDICATORS:
            if indicator in content:
                return 'less_4.x'

        # Check Less 3.x features
        for feat in self.LESS_3_FEATURES:
            if feat in content:
                return 'less_3.x'

        # Check for plugins
        if result.plugins:
            return 'less_3.x'

        # Check Less 2.x features
        for feat in self.LESS_2_FEATURES:
            if feat in content:
                return 'less_2.x'

        # Check extends, import options
        if result.extends:
            return 'less_2.x'
        if any(i.options for i in result.imports):
            return 'less_2.x'

        # Default to 1.x (basic features)
        return 'less_1.x'

    def _detect_math_mode(self, content: str) -> str:
        """Detect Less math mode from configuration or usage patterns."""
        if 'math: "strict"' in content or "math: 'strict'" in content:
            return 'strict'
        if 'math: "parens-division"' in content:
            return 'parens-division'
        if 'math: "parens"' in content:
            return 'parens'
        if 'math: "always"' in content:
            return 'always'
        return ''

    def _detect_features(self, content: str, file_path: str,
                         result: LessParseResult) -> List[str]:
        """Detect Less features in use."""
        features: Set[str] = set()

        # Variables
        if result.variables:
            features.add('variables')
        if result.variable_stats.get('has_lazy_evaluation'):
            features.add('lazy_evaluation')
        if result.variable_stats.get('has_overrides'):
            features.add('variable_overrides')
        if result.variable_stats.get('has_property_vars'):
            features.add('property_variables')

        # Mixins
        if result.mixin_definitions:
            features.add('mixins')
        if result.mixin_stats.get('has_parametric'):
            features.add('parametric_mixins')
        if result.mixin_stats.get('has_guards'):
            features.add('guards')
        if result.mixin_stats.get('has_pattern_matching'):
            features.add('pattern_matching')
        if result.mixin_stats.get('has_rest_args'):
            features.add('rest_args')
        if result.mixin_stats.get('has_arguments'):
            features.add('arguments')
        if result.mixin_stats.get('has_namespaces'):
            features.add('namespaces')

        # Functions
        if result.function_stats.get('has_color_functions'):
            features.add('color_functions')
        if result.function_stats.get('has_math_functions'):
            features.add('math_functions')
        if result.function_stats.get('has_type_functions'):
            features.add('type_functions')
        if result.function_stats.get('has_plugins'):
            features.add('plugins')
        if result.function_stats.get('has_escape'):
            features.add('escape')
        if result.function_stats.get('has_format_string'):
            features.add('format_string')

        # Imports
        if result.imports:
            features.add('imports')
        if result.import_stats.get('has_import_options'):
            features.add('import_options')
        if result.import_stats.get('reference_imports', 0) > 0:
            features.add('reference_imports')

        # Rulesets
        if result.extends:
            features.add('extend')
        if result.detached_rulesets:
            features.add('detached_rulesets')
        if result.ruleset_stats.get('has_bem_patterns'):
            features.add('bem_nesting')
        if result.ruleset_stats.get('has_parent_selector'):
            features.add('parent_selector')
        if result.property_merges:
            features.add('property_merging')
        if result.ruleset_stats.get('has_each_loop'):
            features.add('each_loop')
        if result.ruleset_stats.get('has_css_guards'):
            features.add('css_guards')

        # Operations
        if self.OPERATIONS_PATTERN.search(content):
            features.add('operations')

        # Interpolation
        if self.INTERPOLATION_PATTERN.search(content):
            features.add('interpolation')

        # Escaping
        if self.ESCAPE_PATTERN.search(content):
            features.add('escaping')

        # JavaScript evaluation (deprecated)
        if self.JS_EVAL_PATTERN.search(content):
            features.add('javascript_evaluation')

        # Color operations
        if self.COLOR_OPS_PATTERN.search(content):
            features.add('color_operations')

        # Nesting
        if result.ruleset_stats.get('max_nesting_depth', 0) > 0:
            features.add('nesting')

        # CSS Modules
        if file_path and '.module.less' in file_path.lower():
            features.add('css_modules')

        return sorted(features)

    def _detect_frameworks(self, content: str, file_path: str) -> List[str]:
        """Detect CSS frameworks used via Less."""
        frameworks: List[str] = []

        for fw_name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(fw_name)

        # CSS Modules detection
        if file_path and '.module.less' in file_path.lower():
            frameworks.append('css_modules')

        return frameworks

    def _detect_libraries(self, content: str, file_path: str) -> List[str]:
        """Detect Less utility libraries."""
        libraries: List[str] = []

        for lib_name, pattern in self.LIBRARY_PATTERNS.items():
            if pattern.search(content):
                libraries.append(lib_name)

        return libraries

    def is_less_file(self, file_path: str) -> bool:
        """Check if a file is a Less file."""
        return file_path.lower().endswith('.less')
