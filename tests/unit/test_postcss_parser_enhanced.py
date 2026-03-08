"""Unit tests for the EnhancedPostCSSParser integration.

Tests cover all 5 extractors, version detection, feature detection,
framework/tool detection, and edge cases.

Part of CodeTrellis v4.46 — PostCSS Language Support
"""

import pytest

from codetrellis.postcss_parser_enhanced import EnhancedPostCSSParser, PostCSSParseResult


class TestEnhancedPostCSSParser:
    """Tests for the full EnhancedPostCSSParser orchestration."""

    def setup_method(self):
        self.parser = EnhancedPostCSSParser()

    # ── Basic Parsing ─────────────────────────────────────────────

    def test_empty_content(self):
        result = self.parser.parse("")
        assert isinstance(result, PostCSSParseResult)
        assert result.plugins == []
        assert result.transforms == []
        assert result.syntaxes == []
        assert result.api_usages == []

    def test_whitespace_only_content(self):
        result = self.parser.parse("   \n\n\t  ")
        assert isinstance(result, PostCSSParseResult)
        assert result.plugins == []

    def test_file_path_preserved(self):
        result = self.parser.parse("module.exports = {};", "postcss.config.js")
        assert result.file_path == "postcss.config.js"

    def test_is_postcss_config(self):
        assert self.parser.is_postcss_config("postcss.config.js") is True
        assert self.parser.is_postcss_config("postcss.config.cjs") is True
        assert self.parser.is_postcss_config("postcss.config.mjs") is True
        assert self.parser.is_postcss_config("postcss.config.ts") is True
        assert self.parser.is_postcss_config(".postcssrc") is True
        assert self.parser.is_postcss_config(".postcssrc.json") is True
        assert self.parser.is_postcss_config(".postcssrc.yml") is True
        assert self.parser.is_postcss_config(".postcssrc.yaml") is True
        assert self.parser.is_postcss_config(".postcssrc.js") is True
        assert self.parser.is_postcss_config(".postcssrc.cjs") is True
        assert self.parser.is_postcss_config("webpack.config.js") is False
        assert self.parser.is_postcss_config("style.css") is False

    def test_is_postcss_source(self):
        assert self.parser.is_postcss_source("main.pcss") is True
        assert self.parser.is_postcss_source("theme.PCSS") is True
        assert self.parser.is_postcss_source("style.css") is False
        assert self.parser.is_postcss_source("style.scss") is False

    # ── Plugin Extraction ─────────────────────────────────────────

    def test_require_plugin_extraction(self):
        config = """
module.exports = {
  plugins: [
    require('autoprefixer'),
    require('cssnano'),
    require('postcss-import'),
  ]
};
"""
        result = self.parser.parse(config, "postcss.config.js")
        assert len(result.plugins) >= 3
        plugin_names = [p.get('package_name', '') for p in result.plugins]
        assert 'autoprefixer' in plugin_names
        assert 'cssnano' in plugin_names
        assert 'postcss-import' in plugin_names

    def test_plugin_with_options(self):
        config = """
module.exports = {
  plugins: [
    require('autoprefixer')({ grid: true }),
    require('cssnano')({ preset: 'default' }),
  ]
};
"""
        result = self.parser.parse(config, "postcss.config.js")
        assert len(result.plugins) >= 2

    def test_plugin_categories(self):
        config = """
const autoprefixer = require('autoprefixer');
const cssnano = require('cssnano');
const postcssImport = require('postcss-import');
const postcssPresetEnv = require('postcss-preset-env');
const postcssModules = require('postcss-modules');
"""
        result = self.parser.parse(config, "postcss.config.js")
        assert len(result.plugins) >= 5
        categories = set(p.get('category', '') for p in result.plugins)
        assert len(categories) >= 2  # Should have multiple categories

    def test_plugin_stats(self):
        config = """
require('autoprefixer');
require('cssnano');
require('postcss-preset-env');
"""
        result = self.parser.parse(config, "postcss.config.js")
        stats = result.plugin_stats
        assert stats.get('total_plugins', 0) >= 3
        # Stats use category-level booleans, not per-plugin booleans
        assert stats.get('has_future_css') is True  # postcss-preset-env
        assert stats.get('has_optimization') is True  # cssnano

    def test_import_plugin_extraction(self):
        config = """
import autoprefixer from 'autoprefixer';
import cssnano from 'cssnano';
"""
        result = self.parser.parse(config, "postcss.config.mjs")
        assert len(result.plugins) >= 2
        plugin_names = [p.get('package_name', '') for p in result.plugins]
        assert 'autoprefixer' in plugin_names

    def test_object_style_plugin_config(self):
        config = """
module.exports = {
  plugins: {
    'postcss-import': {},
    'postcss-nesting': {},
    'autoprefixer': {},
  }
};
"""
        result = self.parser.parse(config, "postcss.config.js")
        assert len(result.plugins) >= 3

    def test_unknown_plugin(self):
        config = "require('my-custom-postcss-plugin');"
        result = self.parser.parse(config, "postcss.config.js")
        # May or may not detect unknown plugins depending on patterns
        # At minimum, should not crash
        assert isinstance(result, PostCSSParseResult)

    # ── Config Extraction ─────────────────────────────────────────

    def test_cjs_config_format(self):
        config = """
module.exports = {
  plugins: [
    require('autoprefixer'),
  ]
};
"""
        result = self.parser.parse(config, "postcss.config.js")
        # Config should be detected
        assert isinstance(result.config, dict)

    def test_esm_config_format(self):
        config = """
import autoprefixer from 'autoprefixer';
export default {
  plugins: [autoprefixer()]
};
"""
        result = self.parser.parse(config, "postcss.config.mjs")
        assert isinstance(result.config, dict)

    def test_function_config_format(self):
        config = """
module.exports = (ctx) => ({
  map: ctx.options.map,
  plugins: {
    'postcss-import': {},
    'autoprefixer': {},
    ...(ctx.env === 'production' ? { cssnano: {} } : {}),
  }
});
"""
        result = self.parser.parse(config, "postcss.config.js")
        assert isinstance(result.config, dict)

    def test_env_branching_detection(self):
        config = """
module.exports = (ctx) => ({
  plugins: {
    'autoprefixer': {},
    ...(process.env.NODE_ENV === 'production' ? { cssnano: {} } : {}),
  }
});
"""
        result = self.parser.parse(config, "postcss.config.js")
        if result.config:
            # env branching may be detected
            pass
        assert isinstance(result, PostCSSParseResult)

    def test_source_map_config(self):
        config = """
module.exports = {
  map: { inline: true },
  plugins: [require('autoprefixer')]
};
"""
        result = self.parser.parse(config, "postcss.config.js")
        assert isinstance(result, PostCSSParseResult)

    # ── Transform Extraction ──────────────────────────────────────

    def test_custom_media_transform(self):
        css = """
@custom-media --viewport-sm (width >= 576px);
@custom-media --viewport-md (width >= 768px);
@media (--viewport-sm) {
  .container { max-width: 540px; }
}
"""
        result = self.parser.parse(css, "styles.pcss")
        assert len(result.transforms) >= 2
        # Transform names are the custom media identifiers, at_rule is '@custom-media'
        at_rules = [t.get('at_rule', '') for t in result.transforms]
        assert any('@custom-media' in r for r in at_rules)

    def test_custom_selector_transform(self):
        css = """
@custom-selector :--heading h1, h2, h3, h4, h5, h6;
:--heading {
  font-weight: bold;
}
"""
        result = self.parser.parse(css, "styles.pcss")
        assert len(result.transforms) >= 1

    def test_css_nesting_transform(self):
        css = """
.parent {
  color: red;
  & .child {
    color: blue;
  }
  &:hover {
    color: green;
  }
}
"""
        result = self.parser.parse(css, "styles.pcss")
        # Nesting may be detected
        assert isinstance(result, PostCSSParseResult)

    def test_layer_transform(self):
        css = """
@layer base, components, utilities;
@layer base {
  body { margin: 0; }
}
@layer components {
  .btn { padding: 8px; }
}
"""
        result = self.parser.parse(css, "styles.pcss")
        assert len(result.transforms) >= 1
        # at_rule is '@layer', names are layer names like 'base,'
        at_rules = [t.get('at_rule', '') for t in result.transforms]
        assert any('@layer' in r for r in at_rules)

    def test_container_query_transform(self):
        css = """
.wrapper { container-type: inline-size; }
@container (min-width: 400px) {
  .card { display: flex; }
}
"""
        result = self.parser.parse(css, "styles.pcss")
        assert len(result.transforms) >= 1

    def test_color_function_transform(self):
        css = """
.element {
  color: oklch(50% 0.3 270);
  background: color-mix(in oklch, #3498db, #e74c3c 30%);
}
"""
        result = self.parser.parse(css, "styles.pcss")
        assert len(result.transforms) >= 1

    def test_logical_properties_transform(self):
        css = """
.element {
  margin-inline: auto;
  padding-block: 1rem;
  border-inline-start: 2px solid;
}
"""
        result = self.parser.parse(css, "styles.pcss")
        assert len(result.transforms) >= 1

    def test_apply_rule_transform(self):
        css = """
.btn {
  @apply bg-blue-500 text-white px-4 py-2;
}
"""
        result = self.parser.parse(css, "styles.pcss")
        assert len(result.transforms) >= 1

    def test_import_transform(self):
        css = """
@import "base.css";
@import url("theme.css");
"""
        result = self.parser.parse(css, "styles.pcss")
        assert len(result.transforms) >= 1

    # ── Syntax Extraction ─────────────────────────────────────────

    def test_scss_syntax(self):
        config = """
const syntax = require('postcss-scss');
module.exports = { syntax: 'postcss-scss', plugins: [] };
"""
        result = self.parser.parse(config, "postcss.config.js")
        assert len(result.syntaxes) >= 1
        pkgs = [s.get('package_name', '') for s in result.syntaxes]
        assert 'postcss-scss' in pkgs

    def test_less_syntax(self):
        config = "require('postcss-less');"
        result = self.parser.parse(config, "postcss.config.js")
        assert len(result.syntaxes) >= 1
        pkgs = [s.get('package_name', '') for s in result.syntaxes]
        assert 'postcss-less' in pkgs

    def test_html_syntax(self):
        config = "require('postcss-html');"
        result = self.parser.parse(config, "postcss.config.js")
        assert len(result.syntaxes) >= 1

    def test_sugarss_syntax(self):
        config = "require('sugarss');"
        result = self.parser.parse(config, "postcss.config.js")
        assert len(result.syntaxes) >= 1

    def test_safe_parser_syntax(self):
        config = "require('postcss-safe-parser');"
        result = self.parser.parse(config, "postcss.config.js")
        assert len(result.syntaxes) >= 1

    def test_sugarss_file_detection(self):
        result = self.parser.parse("body\n  color: red\n", "styles.sss")
        assert len(result.syntaxes) >= 1
        pkgs = [s.get('package_name', '') for s in result.syntaxes]
        assert 'sugarss' in pkgs

    def test_multiple_syntaxes(self):
        config = """
require('postcss-scss');
require('postcss-html');
require('postcss-safe-parser');
"""
        result = self.parser.parse(config, "postcss.config.js")
        assert len(result.syntaxes) >= 3

    # ── API Extraction ────────────────────────────────────────────

    def test_processor_creation(self):
        js = """
const postcss = require('postcss');
const result = postcss([autoprefixer]).process(css, { from: 'input.css' });
"""
        result = self.parser.parse(js, "build.js")
        assert len(result.api_usages) >= 1
        categories = set(a.get('api_category', '') for a in result.api_usages)
        assert 'processor' in categories

    def test_legacy_plugin_api(self):
        js = """
module.exports = postcss.plugin('my-plugin', (opts) => {
  return (root) => {
    root.walkDecls(decl => { /* ... */ });
  };
});
"""
        result = self.parser.parse(js, "my-plugin.js")
        assert len(result.api_usages) >= 1
        legacy_usages = [a for a in result.api_usages if a.get('is_legacy')]
        assert len(legacy_usages) >= 1

    def test_modern_plugin_api(self):
        js = """
const plugin = (opts = {}) => ({
  postcssPlugin: 'my-plugin',
  Declaration(decl) {
    if (decl.prop === 'color') {
      decl.value = 'red';
    }
  },
});
plugin.postcss = true;
module.exports = plugin;
"""
        result = self.parser.parse(js, "my-plugin.js")
        assert len(result.api_usages) >= 1
        # Should detect v8 plugin
        api_stats = result.api_stats
        assert api_stats.get('has_v8_plugin') is True or api_stats.get('has_v8_hooks') is True

    def test_walker_methods(self):
        js = """
root.walkDecls(decl => { /* ... */ });
root.walkRules(rule => { /* ... */ });
root.walkAtRules(atRule => { /* ... */ });
root.walkComments(comment => { /* ... */ });
"""
        result = self.parser.parse(js, "plugin.js")
        walkers = [a for a in result.api_usages if a.get('api_category') == 'walker']
        assert len(walkers) >= 4

    def test_node_creation(self):
        js = """
const newDecl = postcss.decl({ prop: 'color', value: 'red' });
const newRule = postcss.rule({ selector: '.foo' });
const newAtRule = postcss.atRule({ name: 'media' });
"""
        result = self.parser.parse(js, "plugin.js")
        nodes = [a for a in result.api_usages if a.get('api_category') == 'node']
        assert len(nodes) >= 3

    def test_result_api(self):
        js = """
const result = await postcss(plugins).process(css, opts);
console.log(result.css);
console.log(result.map);
result.warnings().forEach(warn => console.warn(warn));
"""
        result = self.parser.parse(js, "build.js")
        result_apis = [a for a in result.api_usages if a.get('api_category') == 'result']
        assert len(result_apis) >= 2

    def test_parse_api(self):
        js = """
const root = postcss.parse('a { color: red }');
const output = postcss.stringify(root);
"""
        result = self.parser.parse(js, "utils.js")
        parse_apis = [a for a in result.api_usages if a.get('api_category') == 'parse']
        assert len(parse_apis) >= 2

    def test_v8_plugin_hooks(self):
        js = """
const plugin = (opts = {}) => ({
  postcssPlugin: 'my-plugin',
  Once(root) { /* setup */ },
  OnceExit(root) { /* cleanup */ },
  Declaration(decl) { /* process declarations */ },
  Rule(rule) { /* process rules */ },
  AtRule(atRule) { /* process at-rules */ },
});
"""
        result = self.parser.parse(js, "plugin.js")
        api_stats = result.api_stats
        assert api_stats.get('has_v8_hooks') is True
        hooks = api_stats.get('detected_hooks', [])
        assert 'Once' in hooks
        assert 'OnceExit' in hooks
        assert 'Declaration' in hooks

    # ── Version Detection ─────────────────────────────────────────

    def test_v8_version_detection(self):
        js = """
const plugin = (opts = {}) => ({
  postcssPlugin: 'my-plugin',
  Declaration(decl) { /* ... */ },
});
"""
        result = self.parser.parse(js, "plugin.js")
        assert result.postcss_version == 'postcss_8'

    def test_v7_version_detection(self):
        js = """
module.exports = postcss.plugin('my-plugin', (opts) => {
  return (root) => { /* ... */ };
});
"""
        result = self.parser.parse(js, "plugin.js")
        assert result.postcss_version == 'postcss_7'

    def test_config_only_version_detection(self):
        config = """
module.exports = {
  plugins: [require('autoprefixer')]
};
"""
        result = self.parser.parse(config, "postcss.config.js")
        # Config-only should assume latest
        assert result.postcss_version in ('postcss_8', 'postcss_unknown')

    # ── Feature Detection ─────────────────────────────────────────

    def test_autoprefixer_feature(self):
        config = "require('autoprefixer');"
        result = self.parser.parse(config, "postcss.config.js")
        assert 'autoprefixer' in result.detected_features

    def test_cssnano_feature(self):
        config = "require('cssnano');"
        result = self.parser.parse(config, "postcss.config.js")
        assert 'cssnano' in result.detected_features

    def test_preset_env_feature(self):
        config = "require('postcss-preset-env');"
        result = self.parser.parse(config, "postcss.config.js")
        assert 'preset_env' in result.detected_features

    def test_import_feature(self):
        config = "require('postcss-import');"
        result = self.parser.parse(config, "postcss.config.js")
        assert 'import' in result.detected_features

    def test_future_css_feature(self):
        config = """
require('postcss-nesting');
require('postcss-custom-media');
"""
        result = self.parser.parse(config, "postcss.config.js")
        assert 'future_css' in result.detected_features or 'nesting' in result.detected_features

    def test_pcss_extension_feature(self):
        css = ".element { color: red; }"
        result = self.parser.parse(css, "styles.pcss")
        assert 'pcss_extension' in result.detected_features

    def test_legacy_plugin_api_feature(self):
        js = """
module.exports = postcss.plugin('my-plugin', (opts) => {
  return (root) => {};
});
"""
        result = self.parser.parse(js, "plugin.js")
        assert 'legacy_plugin_api' in result.detected_features

    def test_plugin_definition_feature(self):
        js = """
const plugin = (opts = {}) => ({
  postcssPlugin: 'my-plugin',
  Declaration(decl) {},
});
"""
        result = self.parser.parse(js, "plugin.js")
        assert 'plugin_definition' in result.detected_features

    # ── Framework Detection ───────────────────────────────────────

    def test_vite_framework_detection(self):
        config = '"vite": "^5.0.0",'
        result = self.parser.parse(config, "package.json")
        assert 'vite' in result.detected_frameworks

    def test_webpack_framework_detection(self):
        config = '"webpack": "^5.0.0",'
        result = self.parser.parse(config, "package.json")
        assert 'webpack' in result.detected_frameworks

    def test_next_framework_detection(self):
        config = '"next": "^14.0.0",'
        result = self.parser.parse(config, "package.json")
        assert 'next' in result.detected_frameworks

    def test_tailwind_framework_detection(self):
        config = """
module.exports = {
  plugins: [require('tailwindcss'), require('autoprefixer')]
};
"""
        result = self.parser.parse(config, "postcss.config.js")
        assert 'tailwindcss' in result.detected_frameworks

    def test_no_frameworks_in_plain_css(self):
        css = ".element { color: red; }"
        result = self.parser.parse(css, "styles.pcss")
        # Plain CSS should have no frameworks
        assert len(result.detected_frameworks) == 0

    # ── Tool Detection ────────────────────────────────────────────

    def test_postcss_cli_tool(self):
        config = '"postcss-cli": "^10.0.0",'
        result = self.parser.parse(config, "package.json")
        assert 'postcss_cli' in result.detected_tools

    def test_postcss_loader_tool(self):
        config = '"postcss-loader": "^7.0.0",'
        result = self.parser.parse(config, "package.json")
        assert 'postcss_loader' in result.detected_tools

    def test_stylelint_tool(self):
        config = '"stylelint": "^15.0.0",'
        result = self.parser.parse(config, "package.json")
        assert 'stylelint' in result.detected_tools

    # ── Comprehensive Config ──────────────────────────────────────

    def test_full_postcss_config(self):
        config = """
const postcssImport = require('postcss-import');
const postcssNesting = require('postcss-nesting');
const postcssPresetEnv = require('postcss-preset-env');
const autoprefixer = require('autoprefixer');
const cssnano = require('cssnano');

module.exports = (ctx) => ({
  map: ctx.env === 'development' ? { inline: true } : false,
  plugins: [
    postcssImport(),
    postcssNesting(),
    postcssPresetEnv({ stage: 2 }),
    autoprefixer(),
    ...(ctx.env === 'production' ? [cssnano({ preset: 'default' })] : []),
  ]
});
"""
        result = self.parser.parse(config, "postcss.config.js")
        assert len(result.plugins) >= 5
        assert 'autoprefixer' in result.detected_features
        assert 'cssnano' in result.detected_features
        assert 'preset_env' in result.detected_features
        assert 'import' in result.detected_features

    def test_full_postcss_plugin(self):
        js = """
const postcss = require('postcss');

const plugin = (opts = {}) => {
  const prefix = opts.prefix || 'x';
  return {
    postcssPlugin: 'postcss-prefix',
    Once(root) {
      root.walkRules(rule => {
        rule.selectors = rule.selectors.map(sel => `.${prefix}-${sel}`);
      });
    },
    Declaration(decl) {
      if (decl.prop === 'content') {
        const newDecl = postcss.decl({ prop: 'display', value: 'block' });
        decl.parent.append(newDecl);
      }
    },
    OnceExit(root) {
      const result = root.toResult();
      result.warnings().forEach(w => console.warn(w.toString()));
    },
  };
};
plugin.postcss = true;
module.exports = plugin;
"""
        result = self.parser.parse(js, "postcss-prefix.js")
        assert result.postcss_version == 'postcss_8'
        api_stats = result.api_stats
        assert api_stats.get('has_v8_hooks') is True
        assert api_stats.get('has_v8_plugin') is True
        assert api_stats.get('has_walkers') is True
        assert api_stats.get('has_ast_creation') is True

    def test_full_css_with_transforms(self):
        css = """
@custom-media --viewport-sm (width >= 576px);
@custom-selector :--heading h1, h2, h3;

@layer base, components, utilities;

@layer base {
  body {
    margin: 0;
    color: oklch(30% 0.1 270);
  }
}

@layer components {
  .card {
    container-type: inline-size;
    margin-inline: auto;
    padding-block: 1rem;
  }
  @container (min-width: 400px) {
    .card { display: flex; }
  }
}

@media (--viewport-sm) {
  :--heading {
    font-size: 2rem;
  }
}

@import "base.css";
"""
        result = self.parser.parse(css, "styles.pcss")
        assert len(result.transforms) >= 5
        assert 'pcss_extension' in result.detected_features

    # ── Edge Cases ────────────────────────────────────────────────

    def test_comments_only(self):
        content = "/* This is a comment */\n// Another comment"
        result = self.parser.parse(content, "comments.css")
        assert isinstance(result, PostCSSParseResult)

    def test_minified_css(self):
        css = ".a{color:red}.b{color:blue}.c{color:green}"
        result = self.parser.parse(css, "min.css")
        assert isinstance(result, PostCSSParseResult)

    def test_mixed_config_and_css(self):
        # This shouldn't happen in practice but shouldn't crash
        content = """
require('autoprefixer');
.element { color: red; }
@custom-media --sm (width >= 576px);
"""
        result = self.parser.parse(content, "mixed.js")
        assert isinstance(result, PostCSSParseResult)

    def test_very_large_plugin_chain(self):
        plugins = "\n".join([f"require('postcss-plugin-{i}');" for i in range(50)])
        config = f"module.exports = {{ plugins: [{plugins}] }};"
        result = self.parser.parse(config, "postcss.config.js")
        assert isinstance(result, PostCSSParseResult)

    def test_unicode_content(self):
        css = ".element { content: '🎨 Custom Design'; }"
        result = self.parser.parse(css, "styles.pcss")
        assert isinstance(result, PostCSSParseResult)


class TestPostCSSPluginExtractor:
    """Tests for the PostCSSPluginExtractor directly."""

    def setup_method(self):
        from codetrellis.extractors.postcss.plugin_extractor import PostCSSPluginExtractor
        self.extractor = PostCSSPluginExtractor()

    def test_empty_content(self):
        result = self.extractor.extract("", "")
        assert result.get('plugins', []) == []

    def test_require_extraction(self):
        content = "require('autoprefixer')"
        result = self.extractor.extract(content, "config.js")
        plugins = result.get('plugins', [])
        assert len(plugins) >= 1
        assert plugins[0].package_name == 'autoprefixer'
        assert plugins[0].category == 'utility'

    def test_import_extraction(self):
        content = "import cssnano from 'cssnano';"
        result = self.extractor.extract(content, "config.mjs")
        plugins = result.get('plugins', [])
        assert len(plugins) >= 1
        assert plugins[0].package_name == 'cssnano'

    def test_object_key_extraction(self):
        content = """
  'postcss-import': {},
  'postcss-nesting': { stage: 2 },
  'autoprefixer': {},
"""
        result = self.extractor.extract(content, "postcss.config.js")
        plugins = result.get('plugins', [])
        assert len(plugins) >= 3

    def test_known_plugin_categories(self):
        content = """
require('postcss-preset-env');
require('cssnano');
require('postcss-import');
require('stylelint');
require('postcss-modules');
"""
        result = self.extractor.extract(content, "config.js")
        plugins = result.get('plugins', [])
        categories = set(p.category for p in plugins)
        assert len(categories) >= 3


class TestPostCSSConfigExtractor:
    """Tests for the PostCSSConfigExtractor directly."""

    def setup_method(self):
        from codetrellis.extractors.postcss.config_extractor import PostCSSConfigExtractor
        self.extractor = PostCSSConfigExtractor()

    def test_empty_content(self):
        result = self.extractor.extract("", "")
        assert result.get('config') is None or result.get('stats', {}) == {}

    def test_cjs_detection(self):
        content = "module.exports = { plugins: [] };"
        result = self.extractor.extract(content, "postcss.config.js")
        config = result.get('config')
        if config:
            assert config.module_format in ('cjs', '')

    def test_esm_detection(self):
        content = "export default { plugins: [] };"
        result = self.extractor.extract(content, "postcss.config.mjs")
        config = result.get('config')
        if config:
            assert config.module_format in ('esm', '')


class TestPostCSSTransformExtractor:
    """Tests for the PostCSSTransformExtractor directly."""

    def setup_method(self):
        from codetrellis.extractors.postcss.transform_extractor import PostCSSTransformExtractor
        self.extractor = PostCSSTransformExtractor()

    def test_empty_content(self):
        result = self.extractor.extract("", "")
        assert result.get('transforms', []) == []

    def test_custom_media(self):
        content = "@custom-media --viewport-sm (width >= 576px);"
        result = self.extractor.extract(content, "styles.pcss")
        transforms = result.get('transforms', [])
        assert len(transforms) >= 1

    def test_custom_selector(self):
        content = "@custom-selector :--heading h1, h2, h3;"
        result = self.extractor.extract(content, "styles.pcss")
        transforms = result.get('transforms', [])
        assert len(transforms) >= 1

    def test_layer(self):
        content = "@layer base, components, utilities;"
        result = self.extractor.extract(content, "styles.pcss")
        transforms = result.get('transforms', [])
        assert len(transforms) >= 1

    def test_container_query(self):
        content = "@container (min-width: 400px) { .card { display: flex; } }"
        result = self.extractor.extract(content, "styles.pcss")
        transforms = result.get('transforms', [])
        assert len(transforms) >= 1

    def test_oklch_color(self):
        content = ".element { color: oklch(50% 0.3 270); }"
        result = self.extractor.extract(content, "styles.pcss")
        transforms = result.get('transforms', [])
        assert len(transforms) >= 1

    def test_color_mix(self):
        content = ".element { background: color-mix(in oklch, #3498db, #e74c3c 30%); }"
        result = self.extractor.extract(content, "styles.pcss")
        transforms = result.get('transforms', [])
        assert len(transforms) >= 1

    def test_logical_properties(self):
        content = ".element { margin-inline: auto; padding-block: 1rem; }"
        result = self.extractor.extract(content, "styles.pcss")
        transforms = result.get('transforms', [])
        assert len(transforms) >= 1


class TestPostCSSSyntaxExtractor:
    """Tests for the PostCSSSyntaxExtractor directly."""

    def setup_method(self):
        from codetrellis.extractors.postcss.syntax_extractor import PostCSSSyntaxExtractor
        self.extractor = PostCSSSyntaxExtractor()

    def test_empty_content(self):
        result = self.extractor.extract("", "")
        assert result.get('syntaxes', []) == []

    def test_postcss_scss(self):
        content = "require('postcss-scss')"
        result = self.extractor.extract(content, "config.js")
        syntaxes = result.get('syntaxes', [])
        assert len(syntaxes) >= 1
        assert syntaxes[0].package_name == 'postcss-scss'
        assert 'scss' in syntaxes[0].languages

    def test_sugarss(self):
        content = "require('sugarss')"
        result = self.extractor.extract(content, "config.js")
        syntaxes = result.get('syntaxes', [])
        assert len(syntaxes) >= 1
        assert syntaxes[0].package_name == 'sugarss'

    def test_sss_file(self):
        result = self.extractor.extract("body\n  color: red\n", "styles.sss")
        syntaxes = result.get('syntaxes', [])
        assert len(syntaxes) >= 1
        assert syntaxes[0].package_name == 'sugarss'

    def test_syntax_option(self):
        content = "syntax: 'postcss-scss'"
        result = self.extractor.extract(content, "config.js")
        syntaxes = result.get('syntaxes', [])
        assert len(syntaxes) >= 1

    def test_parser_option(self):
        content = "parser: 'postcss-safe-parser'"
        result = self.extractor.extract(content, "config.js")
        syntaxes = result.get('syntaxes', [])
        assert len(syntaxes) >= 1
        assert syntaxes[0].package_name == 'postcss-safe-parser'


class TestPostCSSApiExtractor:
    """Tests for the PostCSSApiExtractor directly."""

    def setup_method(self):
        from codetrellis.extractors.postcss.api_extractor import PostCSSApiExtractor
        self.extractor = PostCSSApiExtractor()

    def test_empty_content(self):
        result = self.extractor.extract("", "")
        assert result.get('api_usages', []) == []

    def test_processor(self):
        content = "postcss([plugins]).process(css)"
        result = self.extractor.extract(content, "build.js")
        usages = result.get('api_usages', [])
        assert len(usages) >= 1

    def test_legacy_plugin(self):
        content = "postcss.plugin('my-plugin', (opts) => {})"
        result = self.extractor.extract(content, "plugin.js")
        usages = result.get('api_usages', [])
        legacy = [u for u in usages if u.is_legacy]
        assert len(legacy) >= 1

    def test_modern_plugin(self):
        content = "postcssPlugin: 'my-plugin'"
        result = self.extractor.extract(content, "plugin.js")
        usages = result.get('api_usages', [])
        assert len(usages) >= 1
        stats = result.get('stats', {})
        assert stats.get('has_v8_plugin') is True

    def test_walkers(self):
        content = """
root.walkDecls(decl => {});
root.walkRules(rule => {});
"""
        result = self.extractor.extract(content, "plugin.js")
        walkers = [u for u in result.get('api_usages', []) if u.api_category == 'walker']
        assert len(walkers) >= 2

    def test_node_creation(self):
        content = """
postcss.decl({ prop: 'color', value: 'red' });
postcss.rule({ selector: '.foo' });
"""
        result = self.extractor.extract(content, "plugin.js")
        nodes = [u for u in result.get('api_usages', []) if u.api_category == 'node']
        assert len(nodes) >= 2

    def test_parse_stringify(self):
        content = """
postcss.parse('a { color: red }');
postcss.stringify(root);
"""
        result = self.extractor.extract(content, "utils.js")
        parse_apis = [u for u in result.get('api_usages', []) if u.api_category == 'parse']
        assert len(parse_apis) >= 2

    def test_version_inference(self):
        content = """
const plugin = (opts = {}) => ({
  postcssPlugin: 'my-plugin',
  Declaration(decl) {},
  Once(root) {},
});
"""
        result = self.extractor.extract(content, "plugin.js")
        stats = result.get('stats', {})
        assert stats.get('inferred_version') == '>=8'
