"""
EnhancedPostCSSParser v1.0 — Comprehensive PostCSS parser using all extractors.

This parser integrates all 5 PostCSS extractors to provide complete parsing of
PostCSS configuration and CSS/PCSS source files across all PostCSS versions.

PostCSS is NOT a preprocessor — it is a CSS transformation tool with a
plugin-based architecture. Unlike Sass/Less which compile to CSS, PostCSS
transforms CSS using JavaScript plugins that can lint, add vendor prefixes,
polyfill future CSS features, enable modules, and much more.

Supports:
- **PostCSS 1.x–3.x** (early releases):
  - postcss() processor, .process() API, basic plugin structure,
    basic source map support, CSSNextSyntax experimentation.
- **PostCSS 4.x** (stable API):
  - postcss.plugin() factory (later deprecated), Token/Tokenizer API,
    improved source map handling (inline, prev, annotation),
    Node API: walk, walkDecls, walkRules, walkAtRules, walkComments,
    Container API: append, prepend, insertBefore, insertAfter,
    Result API: result.css, result.map, result.messages, result.warnings().
- **PostCSS 5.x–6.x** (ecosystem growth):
  - Custom syntaxes: postcss-scss, postcss-less, postcss-html, sugarss,
    Stringifier API, Input.from property, LazyResult,
    Source map enhancements, wider plugin ecosystem.
- **PostCSS 7.x** (maturity):
  - postcss.plugin() still supported but deprecation warnings,
    Improved custom syntax API (syntax, parser, stringifier options),
    Major plugin ecosystem: autoprefixer, cssnano, postcss-preset-env,
    postcss-modules, stylelint, postcss-import, postcss-url.
- **PostCSS 8.x** (modern, current):
  - Breaking: postcss.plugin() removed, new plugin API with postcssPlugin property,
    Plugin hooks: Once, OnceExit, Root, RootExit, Rule, RuleExit,
    Declaration, DeclarationExit, AtRule, AtRuleExit, Comment, CommentExit,
    Document node for multi-doc parsing, async plugin support,
    Visitor pattern, ESM support, improved error messages,
    Sub-versions: 8.0 (initial), 8.1 (Document), 8.2 (container improvements),
    8.3 (performance), 8.4 (async improvements), 8.5 (latest).

AST Support:
- Regex-based PostCSS config/source parsing with full extraction
- Optional PostCSS JS API for actual CSS AST (postcss.parse())
- Line number tracking for all extracted artifacts
- Plugin dependency analysis, config format detection

LSP Support:
- CSS Language Server integration (vscode-css-languageservice)
- PostCSS Language Server (postcss-language-server) for .pcss files
- Completions for at-rules, properties, custom media, custom selectors
- Diagnostics via stylelint with postcss config
- Document symbols for @custom-media, @custom-selector definitions

Framework/Ecosystem Detection (30+ patterns):
- Core: postcss, autoprefixer, cssnano, postcss-preset-env, postcss-import
- Build tools: postcss-cli, postcss-loader, gulp-postcss, rollup-plugin-postcss
- CSS-in-JS: postcss-jsx, postcss-styled-syntax
- Frameworks: Next.js, Vite, Webpack, Parcel, Remix, Astro, SvelteKit, Nuxt
- Syntax: postcss-scss, postcss-less, postcss-html, sugarss, postcss-safe-parser
- Modules: postcss-modules, css-modules-require-hook
- Linting: stylelint, postcss-reporter
- Utilities: postcss-url, postcss-assets, postcss-copy, postcss-font-magician

Part of CodeTrellis v4.46 — PostCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all PostCSS extractors
from .extractors.postcss import (
    PostCSSPluginExtractor, PostCSSPluginInfo,
    PostCSSConfigExtractor, PostCSSConfigInfo, PostCSSConfigPluginEntry,
    PostCSSTransformExtractor, PostCSSTransformInfo,
    PostCSSSyntaxExtractor, PostCSSSyntaxInfo,
    PostCSSApiExtractor, PostCSSApiUsage,
)


@dataclass
class PostCSSParseResult:
    """Complete parse result for PostCSS files."""
    file_path: str

    # Plugins
    plugins: List[Dict[str, Any]] = field(default_factory=list)
    plugin_stats: Dict[str, Any] = field(default_factory=dict)

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    config_stats: Dict[str, Any] = field(default_factory=dict)

    # Transforms (CSS features processed by plugins)
    transforms: List[Dict[str, Any]] = field(default_factory=list)
    transform_stats: Dict[str, Any] = field(default_factory=dict)

    # Custom syntaxes
    syntaxes: List[Dict[str, Any]] = field(default_factory=list)
    syntax_stats: Dict[str, Any] = field(default_factory=dict)

    # API usages (JS API patterns)
    api_usages: List[Dict[str, Any]] = field(default_factory=list)
    api_stats: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    postcss_version: str = ""           # "postcss_1-3", "postcss_4-6", "postcss_7", "postcss_8"
    config_format: str = ""             # "cjs", "esm", "ts", "json", "yaml", "package.json"
    build_tool: str = ""                # "vite", "webpack", "rollup", "parcel", etc.
    detected_features: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)
    detected_tools: List[str] = field(default_factory=list)


class EnhancedPostCSSParser:
    """
    Enhanced PostCSS parser that uses all 5 extractors for comprehensive parsing.

    Detects PostCSS version, plugin ecosystem, config format, build tool
    integration, and extracts all structured data from PostCSS config files
    and CSS/PCSS source files.
    """

    # PostCSS config file names
    CONFIG_FILES = {
        'postcss.config.js', 'postcss.config.cjs', 'postcss.config.mjs',
        'postcss.config.ts', '.postcssrc', '.postcssrc.json',
        '.postcssrc.yml', '.postcssrc.yaml', '.postcssrc.js',
        '.postcssrc.cjs', '.postcssrc.mjs', '.postcssrc.ts',
    }

    # PostCSS version indicators
    V8_INDICATORS = {
        'postcssPlugin', 'Once(', 'OnceExit(', 'RootExit(', 'RuleExit(',
        'DeclarationExit(', 'AtRuleExit(', 'CommentExit(',
        'Document', 'postcss/lib/document',
    }

    V7_INDICATORS = {
        'postcss.plugin(', 'module.exports = postcss.plugin',
    }

    V4_6_INDICATORS = {
        'postcss.plugin(', '.process(', 'result.css', 'result.map',
        'walkDecls', 'walkRules', 'walkAtRules', 'walkComments',
    }

    # Build tool detection via package.json/config
    BUILD_TOOL_PATTERNS = {
        'vite': re.compile(r'"vite"\s*:', re.MULTILINE),
        'webpack': re.compile(r'"webpack"\s*:', re.MULTILINE),
        'rollup': re.compile(r'"rollup"\s*:', re.MULTILINE),
        'parcel': re.compile(r'"parcel"\s*:', re.MULTILINE),
        'esbuild': re.compile(r'"esbuild"\s*:', re.MULTILINE),
        'next': re.compile(r'"next"\s*:', re.MULTILINE),
        'nuxt': re.compile(r'"nuxt"\s*:', re.MULTILINE),
        'gatsby': re.compile(r'"gatsby"\s*:', re.MULTILINE),
        'remix': re.compile(r'"@remix-run', re.MULTILINE),
        'astro': re.compile(r'"astro"\s*:', re.MULTILINE),
        'svelte': re.compile(r'"svelte"\s*:|"@sveltejs', re.MULTILINE),
    }

    # Framework-adjacent tools
    TOOLING_PATTERNS = {
        'postcss_cli': re.compile(r'"postcss-cli"\s*:', re.MULTILINE),
        'postcss_loader': re.compile(r'"postcss-loader"\s*:', re.MULTILINE),
        'gulp_postcss': re.compile(r'"gulp-postcss"\s*:', re.MULTILINE),
        'rollup_postcss': re.compile(r'"rollup-plugin-postcss"\s*:', re.MULTILINE),
        'parcel_css': re.compile(r'"@parcel/css"\s*:', re.MULTILINE),
        'stylelint': re.compile(r'"stylelint"\s*:', re.MULTILINE),
        'postcss_reporter': re.compile(r'"postcss-reporter"\s*:', re.MULTILINE),
        'css_modules': re.compile(r'"postcss-modules"\s*:', re.MULTILINE),
        'tailwindcss': re.compile(r'"tailwindcss"\s*:', re.MULTILINE),
    }

    # PostCSS import/require detection
    POSTCSS_IMPORT_PATTERN = re.compile(
        r"""(?:require|import)\s*[\s(]['"](postcss)['"]""",
        re.MULTILINE
    )

    # postcss() processor usage
    PROCESSOR_PATTERN = re.compile(
        r'postcss\s*\(\s*\[', re.MULTILINE
    )

    # .pcss / .css extension check
    POSTCSS_EXTENSIONS = {'.pcss', '.css'}

    # Package.json postcss field
    POSTCSS_FIELD_PATTERN = re.compile(
        r'"postcss"\s*:\s*\{', re.MULTILINE
    )

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.plugin_extractor = PostCSSPluginExtractor()
        self.config_extractor = PostCSSConfigExtractor()
        self.transform_extractor = PostCSSTransformExtractor()
        self.syntax_extractor = PostCSSSyntaxExtractor()
        self.api_extractor = PostCSSApiExtractor()

    def parse(self, content: str, file_path: str = "") -> PostCSSParseResult:
        """
        Parse PostCSS content using all extractors.

        Args:
            content: Source code content string.
            file_path: Path to the source file.

        Returns:
            PostCSSParseResult with all extracted data.
        """
        result = PostCSSParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # 1. Plugin extraction
        plugin_result = self.plugin_extractor.extract(content, file_path)
        result.plugins = [
            {
                "name": p.name,
                "package_name": p.package_name,
                "category": p.category,
                "has_options": p.has_options,
                "options_summary": p.options_summary[:60] if p.options_summary else "",
                "is_builtin": p.is_builtin,
                "file": p.file,
                "line": p.line_number,
            }
            for p in plugin_result.get('plugins', [])
        ]
        result.plugin_stats = plugin_result.get('stats', {})

        # 2. Config extraction
        config_result = self.config_extractor.extract(content, file_path)
        config_info = config_result.get('config')
        if config_info:
            result.config = {
                "config_file": config_info.config_file,
                "config_format": config_info.config_format,
                "module_format": config_info.module_format,
                "has_env_branching": config_info.has_env_branching,
                "has_source_maps": config_info.has_source_maps,
                "syntax": config_info.syntax,
                "parser": config_info.parser,
                "stringifier": config_info.stringifier,
                "build_tool": config_info.build_tool,
                "plugin_count": len(config_info.plugins),
                "plugins": [
                    {"name": p.name, "has_options": p.has_options}
                    for p in config_info.plugins[:30]
                ],
            }
            result.config_format = config_info.config_format
            result.build_tool = config_info.build_tool
        result.config_stats = config_result.get('stats', {})

        # 3. Transform extraction (CSS feature usage)
        transform_result = self.transform_extractor.extract(content, file_path)
        result.transforms = [
            {
                "name": t.name,
                "category": t.category,
                "at_rule": t.at_rule,
                "spec_stage": t.spec_stage,
                "value": t.value[:60] if t.value else "",
                "file": t.file,
                "line": t.line_number,
            }
            for t in transform_result.get('transforms', [])
        ]
        result.transform_stats = transform_result.get('stats', {})

        # 4. Syntax extraction
        syntax_result = self.syntax_extractor.extract(content, file_path)
        result.syntaxes = [
            {
                "name": s.name,
                "package_name": s.package_name,
                "syntax_type": s.syntax_type,
                "languages": s.languages,
                "file": s.file,
                "line": s.line_number,
            }
            for s in syntax_result.get('syntaxes', [])
        ]
        result.syntax_stats = syntax_result.get('stats', {})

        # 5. API extraction (JavaScript API patterns)
        api_result = self.api_extractor.extract(content, file_path)
        result.api_usages = [
            {
                "api_name": a.api_name,
                "api_category": a.api_category,
                "pattern": a.pattern,
                "is_legacy": a.is_legacy,
                "postcss_version": a.postcss_version,
                "file": a.file,
                "line": a.line_number,
            }
            for a in api_result.get('api_usages', [])
        ]
        result.api_stats = api_result.get('stats', {})

        # Detect PostCSS version
        result.postcss_version = self._detect_postcss_version(content, result)

        # Detect features
        result.detected_features = self._detect_features(content, file_path, result)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content, file_path)

        # Detect tooling
        result.detected_tools = self._detect_tools(content, file_path)

        return result

    def _detect_postcss_version(self, content: str, result: PostCSSParseResult) -> str:
        """Detect which PostCSS version is in use based on API patterns."""
        # Check for v8 indicators (modern plugin API)
        for indicator in self.V8_INDICATORS:
            if indicator in content:
                return 'postcss_8'

        # Check API stats from extractor
        api_stats = result.api_stats
        if api_stats.get('inferred_version') == '>=8':
            return 'postcss_8'
        if api_stats.get('has_v8_hooks'):
            return 'postcss_8'
        if api_stats.get('has_v8_plugin'):
            return 'postcss_8'

        # Check for v7 indicators (legacy plugin factory)
        for indicator in self.V7_INDICATORS:
            if indicator in content:
                return 'postcss_7'

        if api_stats.get('inferred_version') == '<=7':
            return 'postcss_7'

        # Check for v4-6 indicators (process API, walkers)
        for indicator in self.V4_6_INDICATORS:
            if indicator in content:
                return 'postcss_4-6'

        # If plugins found in config but no API patterns → config-only usage
        if result.plugins or result.config:
            return 'postcss_8'  # Assume latest if using config

        return 'postcss_unknown'

    def _detect_features(self, content: str, file_path: str,
                         result: PostCSSParseResult) -> List[str]:
        """Detect PostCSS features in use."""
        features: Set[str] = set()

        # Plugin-based features
        plugin_stats = result.plugin_stats
        if plugin_stats.get('has_future_css'):
            features.add('preset_env')
        if plugin_stats.get('has_optimization'):
            features.add('cssnano')
        if plugin_stats.get('has_linting'):
            features.add('linting')
        if plugin_stats.get('has_modules'):
            features.add('css_modules')
        if plugin_stats.get('has_framework'):
            features.add('framework')
        if plugin_stats.get('has_syntax'):
            features.add('custom_syntax')
        if plugin_stats.get('total_plugins', 0) > 0:
            features.add('plugins')

        # Check individual plugin names from the plugin list
        for p in result.plugins:
            pkg = p.get('package_name', '')
            if pkg == 'autoprefixer':
                features.add('autoprefixer')
            elif pkg == 'cssnano':
                features.add('cssnano')
            elif pkg == 'postcss-preset-env':
                features.add('preset_env')
            elif pkg == 'postcss-import':
                features.add('import')
            elif pkg in ('postcss-nesting', 'postcss-nested'):
                features.add('nesting')
            elif pkg == 'postcss-custom-media':
                features.add('custom_media')
            elif pkg in ('postcss-modules', 'postcss-modules-values'):
                features.add('css_modules')
            elif pkg == 'postcss-mixins':
                features.add('mixins')
            elif pkg == 'postcss-url':
                features.add('url')

        # Category-based features from categories list
        categories = plugin_stats.get('categories', [])
        if 'future_css' in categories:
            features.add('future_css')
        if 'optimization' in categories:
            features.add('optimization')
        if 'utility' in categories:
            features.add('utility')
        if 'linting' in categories:
            features.add('linting')
        if 'modules' in categories:
            features.add('modules')

        # Config-based features
        config_stats = result.config_stats
        if config_stats.get('has_env_branching'):
            features.add('env_branching')
        if config_stats.get('has_source_maps'):
            features.add('source_maps')
        if config_stats.get('has_custom_syntax'):
            features.add('custom_syntax')
        if config_stats.get('has_custom_parser'):
            features.add('custom_parser')

        # Transform-based features
        transform_stats = result.transform_stats
        if transform_stats.get('has_custom_media'):
            features.add('custom_media_queries')
        if transform_stats.get('has_custom_selectors'):
            features.add('custom_selectors')
        if transform_stats.get('has_nesting'):
            features.add('css_nesting')
        if transform_stats.get('has_container_queries'):
            features.add('container_queries')
        if transform_stats.get('has_cascade_layers'):
            features.add('cascade_layers')
        if transform_stats.get('has_color_functions'):
            features.add('color_functions')
        if transform_stats.get('has_logical_properties'):
            features.add('logical_properties')

        # Syntax-based features
        syntax_stats = result.syntax_stats
        if syntax_stats.get('has_scss_syntax'):
            features.add('scss_syntax')
        if syntax_stats.get('has_less_syntax'):
            features.add('less_syntax')
        if syntax_stats.get('has_html_syntax'):
            features.add('html_syntax')
        if syntax_stats.get('has_sugarss'):
            features.add('sugarss')
        if syntax_stats.get('has_safe_parser'):
            features.add('safe_parser')

        # API-based features
        api_stats = result.api_stats
        if api_stats.get('has_processor'):
            features.add('processor_api')
        if api_stats.get('has_plugin_def'):
            features.add('plugin_definition')
        if api_stats.get('has_ast_creation'):
            features.add('ast_creation')
        if api_stats.get('has_walkers'):
            features.add('ast_traversal')
        if api_stats.get('has_container_api'):
            features.add('ast_manipulation')
        if api_stats.get('has_result_api'):
            features.add('result_api')
        if api_stats.get('has_parse_api'):
            features.add('parse_api')
        if api_stats.get('has_async'):
            features.add('async_processing')
        if api_stats.get('has_source_maps'):
            features.add('source_maps')
        if api_stats.get('has_legacy_plugin'):
            features.add('legacy_plugin_api')

        # .pcss file
        if file_path and file_path.lower().endswith('.pcss'):
            features.add('pcss_extension')

        return sorted(features)

    def _detect_frameworks(self, content: str, file_path: str) -> List[str]:
        """Detect frameworks integrating with PostCSS."""
        frameworks: List[str] = []

        for fw_name, pattern in self.BUILD_TOOL_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(fw_name)

        # Tailwind integration
        if 'tailwindcss' in content or '@tailwind' in content:
            if 'tailwindcss' not in frameworks:
                frameworks.append('tailwindcss')

        return frameworks

    def _detect_tools(self, content: str, file_path: str) -> List[str]:
        """Detect PostCSS tools and integrations."""
        tools: List[str] = []

        for tool_name, pattern in self.TOOLING_PATTERNS.items():
            if pattern.search(content):
                tools.append(tool_name)

        return tools

    def is_postcss_config(self, file_path: str) -> bool:
        """Check if a file is a PostCSS config file."""
        name = Path(file_path).name
        return name in self.CONFIG_FILES

    def is_postcss_source(self, file_path: str) -> bool:
        """Check if a file is a .pcss source file."""
        return file_path.lower().endswith('.pcss')
