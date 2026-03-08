"""Unit tests for the EnhancedSassParser integration."""

import pytest

from codetrellis.sass_parser_enhanced import EnhancedSassParser, SassParseResult


class TestEnhancedSassParser:
    """Tests for the full EnhancedSassParser orchestration."""

    def setup_method(self):
        self.parser = EnhancedSassParser()

    # ── Basic Parsing ─────────────────────────────────────────────

    def test_empty_content(self):
        result = self.parser.parse("")
        assert isinstance(result, SassParseResult)
        assert result.variables == []
        assert result.mixin_definitions == []

    def test_scss_file_type(self):
        scss = "$color: red;\n.btn { color: $color; }\n"
        result = self.parser.parse(scss, "style.scss")
        assert result.file_type == "scss"

    def test_sass_file_type(self):
        sass = "$color: red\n.btn\n  color: $color\n"
        result = self.parser.parse(sass, "style.sass")
        assert result.file_type == "sass"

    # ── Variables ─────────────────────────────────────────────────

    def test_variable_extraction(self):
        scss = """
$primary-color: #3498db;
$font-size-base: 16px;
$is-dark: true;
"""
        result = self.parser.parse(scss, "vars.scss")
        assert len(result.variables) == 3
        names = [v.name for v in result.variables]
        assert "$primary-color" in names
        assert "$font-size-base" in names
        assert "$is-dark" in names

    def test_variable_default_flag(self):
        scss = "$primary: #3498db !default;\n$secondary: #2ecc71;\n"
        result = self.parser.parse(scss, "vars.scss")
        defaults = [v for v in result.variables if v.is_default]
        non_defaults = [v for v in result.variables if not v.is_default]
        assert len(defaults) >= 1
        assert len(non_defaults) >= 1

    def test_variable_global_flag(self):
        scss = """
.component {
  $theme-color: red !global;
}
"""
        result = self.parser.parse(scss, "comp.scss")
        globals_list = [v for v in result.variables if v.is_global]
        assert len(globals_list) >= 1

    def test_color_type_detection(self):
        scss = """
$primary: #3498db;
$accent: rgb(46, 204, 113);
$bg: hsl(0, 0%, 95%);
"""
        result = self.parser.parse(scss, "colors.scss")
        color_vars = [v for v in result.variables if v.data_type == "color"]
        assert len(color_vars) >= 2

    # ── Maps ──────────────────────────────────────────────────────

    def test_map_extraction(self):
        scss = """
$colors: (
  primary: #3498db,
  secondary: #2ecc71,
  danger: #e74c3c,
);
"""
        result = self.parser.parse(scss, "maps.scss")
        assert len(result.maps) >= 1
        color_map = result.maps[0]
        assert color_map.name == "$colors"
        assert "primary" in color_map.keys
        assert color_map.entry_count >= 3

    def test_nested_map(self):
        scss = """
$theme: (
  light: (bg: #fff, text: #333),
  dark: (bg: #1a1a1a, text: #eee),
);
"""
        result = self.parser.parse(scss, "theme.scss")
        assert len(result.maps) >= 1

    # ── Lists ─────────────────────────────────────────────────────

    def test_list_extraction(self):
        scss = "$breakpoints: 320px, 768px, 1024px, 1440px;\n"
        result = self.parser.parse(scss, "lists.scss")
        assert len(result.lists) >= 1

    # ── Mixin Definitions ─────────────────────────────────────────

    def test_mixin_definition(self):
        scss = """
@mixin flex-center($direction: row) {
  display: flex;
  flex-direction: $direction;
  align-items: center;
  justify-content: center;
}
"""
        result = self.parser.parse(scss, "mixins.scss")
        assert len(result.mixin_definitions) >= 1
        mixin = result.mixin_definitions[0]
        assert mixin.name == "flex-center"
        assert len(mixin.parameters) >= 1

    def test_mixin_with_content(self):
        scss = """
@mixin respond-to($bp) {
  @media (min-width: $bp) {
    @content;
  }
}
"""
        result = self.parser.parse(scss, "responsive.scss")
        assert len(result.mixin_definitions) >= 1
        mixin = result.mixin_definitions[0]
        assert mixin.name == "respond-to"
        assert mixin.has_content_block is True

    def test_mixin_with_rest_args(self):
        scss = """
@mixin transition($props...) {
  transition: $props;
}
"""
        result = self.parser.parse(scss, "util.scss")
        assert len(result.mixin_definitions) >= 1
        mixin = result.mixin_definitions[0]
        assert mixin.has_rest_args is True

    # ── Mixin Usages ──────────────────────────────────────────────

    def test_mixin_include(self):
        scss = """
.card {
  @include flex-center;
  @include respond-to(768px) {
    flex-direction: row;
  }
}
"""
        result = self.parser.parse(scss, "comp.scss")
        assert len(result.mixin_usages) >= 2
        names = [u.name for u in result.mixin_usages]
        assert "flex-center" in names
        assert "respond-to" in names

    def test_namespaced_mixin_include(self):
        scss = """
@use "mixins";
.card {
  @include mixins.flex-center;
}
"""
        result = self.parser.parse(scss, "comp.scss")
        assert len(result.mixin_usages) >= 1
        usage = result.mixin_usages[0]
        assert usage.name == "flex-center"
        assert usage.namespace == "mixins"

    # ── Function Definitions ──────────────────────────────────────

    def test_function_definition(self):
        scss = """
@function to-rem($px) {
  @return $px / 16 * 1rem;
}
"""
        result = self.parser.parse(scss, "funcs.scss")
        assert len(result.function_definitions) >= 1
        func = result.function_definitions[0]
        assert func.name == "to-rem"
        assert len(func.parameters) >= 1

    def test_function_multiple_returns(self):
        scss = """
@function spacing($size) {
  @if $size == 'sm' { @return 4px; }
  @if $size == 'md' { @return 8px; }
  @if $size == 'lg' { @return 16px; }
  @return 0;
}
"""
        result = self.parser.parse(scss, "spacing.scss")
        assert len(result.function_definitions) >= 1
        func = result.function_definitions[0]
        assert func.return_count >= 3

    # ── Function Calls ────────────────────────────────────────────

    def test_builtin_function_calls(self):
        scss = """
.box {
  width: percentage(0.5);
  color: lighten($primary, 10%);
  font-size: round(14.5px);
}
"""
        result = self.parser.parse(scss, "funcs.scss")
        assert len(result.function_calls) >= 2
        categories = set(fc.category for fc in result.function_calls)
        assert len(categories) >= 1  # at least some categorized

    def test_namespaced_function_calls(self):
        scss = """
@use "sass:math";
@use "sass:color";
.box {
  width: math.div(100%, 3);
  color: color.adjust($primary, $lightness: 10%);
}
"""
        result = self.parser.parse(scss, "modern.scss")
        namespaced = [fc for fc in result.function_calls if fc.namespace]
        assert len(namespaced) >= 2

    # ── @use Module System ────────────────────────────────────────

    def test_use_statement(self):
        scss = """
@use "sass:math";
@use "sass:color" as c;
@use "variables" as vars;
"""
        result = self.parser.parse(scss, "mod.scss")
        assert len(result.uses) >= 3
        builtins = [u for u in result.uses if u.is_builtin]
        assert len(builtins) >= 2

    def test_use_with_show_hide(self):
        scss = """
@use "helpers" hide _internal, _debug;
@use "colors" show $primary, $secondary;
"""
        result = self.parser.parse(scss, "mod.scss")
        hiders = [u for u in result.uses if u.hide_members]
        showers = [u for u in result.uses if u.show_members]
        assert len(hiders) >= 1
        assert len(showers) >= 1

    def test_use_with_configuration(self):
        scss = """
@use "bootstrap" with (
  $primary: #custom-blue,
  $enable-rounded: false,
);
"""
        result = self.parser.parse(scss, "main.scss")
        uses_with_config = [u for u in result.uses if u.with_config]
        assert len(uses_with_config) >= 1

    # ── @forward ──────────────────────────────────────────────────

    def test_forward_statement(self):
        scss = """
@forward "variables";
@forward "mixins";
@forward "functions";
"""
        result = self.parser.parse(scss, "_index.scss")
        assert len(result.forwards) >= 3

    def test_forward_with_prefix(self):
        scss = '@forward "colors" as color-*;\n'
        result = self.parser.parse(scss, "_index.scss")
        assert len(result.forwards) >= 1
        fwd = result.forwards[0]
        assert fwd.prefix == "color-*"

    # ── Legacy @import ────────────────────────────────────────────

    def test_legacy_import(self):
        scss = """
@import "variables";
@import "mixins";
@import "base/reset";
"""
        result = self.parser.parse(scss, "main.scss")
        assert len(result.imports) >= 3

    def test_partial_import(self):
        scss = '@import "base/_variables";\n@import "base/_mixins";\n'
        result = self.parser.parse(scss, "main.scss")
        partials = [i for i in result.imports if i.is_partial]
        assert len(partials) >= 2

    # ── @extend ───────────────────────────────────────────────────

    def test_extend_class(self):
        scss = """
.error-message {
  @extend .message;
  color: red;
}
"""
        result = self.parser.parse(scss, "comp.scss")
        assert len(result.extends) >= 1
        ext = result.extends[0]
        assert ext.is_placeholder is False

    def test_extend_placeholder(self):
        scss = """
%visually-hidden {
  position: absolute;
  overflow: hidden;
}
.sr-only {
  @extend %visually-hidden;
}
"""
        result = self.parser.parse(scss, "util.scss")
        assert len(result.placeholders) >= 1
        assert len(result.extends) >= 1
        ext = result.extends[0]
        assert ext.is_placeholder is True

    def test_extend_optional(self):
        scss = ".btn { @extend .base-btn !optional; }\n"
        result = self.parser.parse(scss, "btn.scss")
        assert len(result.extends) >= 1
        ext = result.extends[0]
        assert ext.is_optional is True

    # ── Nesting Depth ─────────────────────────────────────────────

    def test_nesting_depth(self):
        scss = """
.page {
  .content {
    .card {
      .title { font-weight: bold; }
    }
  }
}
"""
        result = self.parser.parse(scss, "deep.scss")
        assert len(result.nesting) >= 1
        max_depth = max(n.depth for n in result.nesting)
        assert max_depth >= 3

    def test_bem_pattern_detection(self):
        scss = """
.card {
  &__header { padding: 1rem; }
  &__body { padding: 1rem; }
  &--featured { border-color: gold; }
}
"""
        result = self.parser.parse(scss, "card.scss")
        bem_patterns = [n for n in result.nesting if n.is_bem_pattern]
        assert len(bem_patterns) >= 2

    def test_parent_selector_detection(self):
        scss = """
.btn {
  &:hover { background: darken($primary, 10%); }
  &.active { font-weight: bold; }
}
"""
        result = self.parser.parse(scss, "btn.scss")
        parent_sels = [n for n in result.nesting if n.has_parent_selector]
        assert len(parent_sels) >= 1

    # ── @at-root ──────────────────────────────────────────────────

    def test_at_root(self):
        scss = """
.card {
  @at-root {
    .card-overlay {
      position: fixed;
    }
  }
}
"""
        result = self.parser.parse(scss, "card.scss")
        assert len(result.at_roots) >= 1

    def test_at_root_with_query(self):
        scss = """
.card {
  @at-root (without: media) {
    .card-title { font-size: 2rem; }
  }
}
"""
        result = self.parser.parse(scss, "card.scss")
        at_roots_with_query = [a for a in result.at_roots if a.has_query]
        assert len(at_roots_with_query) >= 1

    # ── Version Detection ─────────────────────────────────────────

    def test_dart_sass_detection(self):
        scss = """
@use "sass:math";
@use "sass:color";
.box { width: math.div(100%, 3); }
"""
        result = self.parser.parse(scss, "modern.scss")
        assert "dart_sass" in result.sass_version or result.module_system == "dart_sass"

    def test_legacy_sass_detection(self):
        scss = """
@import "variables";
@import "mixins";
.box { width: 100% / 3; }
"""
        result = self.parser.parse(scss, "legacy.scss")
        assert result.module_system == "legacy"

    # ── Feature Detection ─────────────────────────────────────────

    def test_feature_detection(self):
        scss = """
$color: #3498db;
@mixin flex-center { display: flex; align-items: center; }
@function to-rem($px) { @return $px / 16 * 1rem; }
$map: (a: 1, b: 2);
.btn { @extend %base; }
"""
        result = self.parser.parse(scss, "features.scss")
        assert len(result.detected_features) >= 3

    # ── Framework Detection ───────────────────────────────────────

    def test_bootstrap_detection(self):
        scss = """
@import "bootstrap/scss/variables";
@import "bootstrap/scss/mixins";
.custom-btn {
  @include button-variant($primary, $primary);
}
"""
        result = self.parser.parse(scss, "custom.scss")
        assert "bootstrap" in result.detected_frameworks

    def test_bourbon_detection(self):
        scss = """
@import "bourbon";
.box {
  @include size(100px);
  @include clearfix;
}
"""
        result = self.parser.parse(scss, "styled.scss")
        assert "bourbon" in result.detected_libraries or "bourbon" in result.detected_frameworks

    # ── Comprehensive File ────────────────────────────────────────

    def test_comprehensive_scss(self):
        """Test a comprehensive SCSS file with all feature types."""
        scss = """
@use "sass:math";
@use "sass:color";
@use "config" as cfg;

// Variables
$primary: #3498db !default;
$spacing: 8px;
$breakpoints: (sm: 576px, md: 768px, lg: 992px, xl: 1200px);
$font-stack: 'Helvetica', 'Arial', sans-serif;

// Function
@function spacing($multiplier) {
  @return $spacing * $multiplier;
}

// Mixin
@mixin respond-to($breakpoint) {
  @media (min-width: map-get($breakpoints, $breakpoint)) {
    @content;
  }
}

// Placeholder
%flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

// Component
.card {
  @extend %flex-center;
  padding: spacing(2);
  color: color.adjust($primary, $lightness: 10%);

  &__header {
    font-family: $font-stack;
  }

  &__body {
    padding: spacing(1);
  }

  &--featured {
    border: 2px solid $primary;
  }

  @include respond-to(md) {
    flex-direction: row;
  }
}
"""
        result = self.parser.parse(scss, "component.scss")

        # Variables
        assert len(result.variables) >= 3
        # Maps
        assert len(result.maps) >= 1
        # Functions
        assert len(result.function_definitions) >= 1
        # Mixins
        assert len(result.mixin_definitions) >= 1
        assert len(result.mixin_usages) >= 1
        # @use
        assert len(result.uses) >= 3
        # Extend / Placeholders
        assert len(result.placeholders) >= 1
        assert len(result.extends) >= 1
        # Nesting with BEM
        bem = [n for n in result.nesting if n.is_bem_pattern]
        assert len(bem) >= 2
        # Module system
        assert result.module_system == "dart_sass"
        # Features detected
        assert len(result.detected_features) >= 3

    def test_indented_sass_syntax(self):
        """Test .sass indented syntax parsing."""
        sass_content = """$color: red
$size: 16px

=flex-center
  display: flex
  align-items: center

.card
  +flex-center
  color: $color
  font-size: $size

  &__header
    font-weight: bold
"""
        result = self.parser.parse(sass_content, "style.sass")
        assert result.file_type == "sass"
        assert len(result.variables) >= 2
        # Indented mixin syntax (=mixin, +include)
        assert len(result.mixin_definitions) >= 1
        assert len(result.mixin_usages) >= 1


class TestSassExtractors:
    """Targeted tests for individual extractor edge cases."""

    def setup_method(self):
        self.parser = EnhancedSassParser()

    def test_variable_namespace(self):
        scss = """
@use "sass:math";
.box { width: math.$pi * 2; }
"""
        result = self.parser.parse(scss, "ns.scss")
        # Should detect math namespace usage
        assert len(result.uses) >= 1

    def test_map_with_many_keys(self):
        scss = """
$z-index: (
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modal-backdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
);
"""
        result = self.parser.parse(scss, "zindex.scss")
        assert len(result.maps) >= 1
        m = result.maps[0]
        assert m.entry_count >= 7

    def test_multiple_mixins_in_file(self):
        scss = """
@mixin visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}

@mixin clearfix {
  &::after {
    content: "";
    display: table;
    clear: both;
  }
}

@mixin truncate($width: 100%) {
  max-width: $width;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
"""
        result = self.parser.parse(scss, "mixins.scss")
        assert len(result.mixin_definitions) >= 3
        names = [m.name for m in result.mixin_definitions]
        assert "visually-hidden" in names
        assert "clearfix" in names
        assert "truncate" in names

    def test_forward_show_hide(self):
        scss = """
@forward "helpers" hide _internal;
@forward "colors" show $primary, $secondary;
"""
        result = self.parser.parse(scss, "_index.scss")
        assert len(result.forwards) >= 2
        hiders = [f for f in result.forwards if f.hide_members]
        showers = [f for f in result.forwards if f.show_members]
        assert len(hiders) >= 1
        assert len(showers) >= 1

    def test_builtin_module_detection(self):
        scss = """
@use "sass:math";
@use "sass:color";
@use "sass:string";
@use "sass:list";
@use "sass:map";
@use "sass:selector";
@use "sass:meta";
"""
        result = self.parser.parse(scss, "builtins.scss")
        builtins = [u for u in result.uses if u.is_builtin]
        assert len(builtins) >= 7

    def test_placeholder_definitions(self):
        scss = """
%clearfix {
  &::after { content: ""; display: table; clear: both; }
}
%flex-center {
  display: flex; align-items: center; justify-content: center;
}
%screen-reader-only {
  position: absolute; width: 1px; height: 1px;
}
"""
        result = self.parser.parse(scss, "placeholders.scss")
        assert len(result.placeholders) >= 3
        names = [p.name for p in result.placeholders]
        assert "%clearfix" in names
        assert "%flex-center" in names

    def test_css_import_detection(self):
        scss = """
@import url("https://fonts.googleapis.com/css2?family=Inter");
@import "variables";
@import "base/reset.css";
"""
        result = self.parser.parse(scss, "main.scss")
        css_imports = [i for i in result.imports if i.is_css_import]
        sass_imports = [i for i in result.imports if not i.is_css_import]
        assert len(css_imports) >= 1
        assert len(sass_imports) >= 1

    def test_color_function_categories(self):
        scss = """
.box {
  color: lighten($primary, 10%);
  background: darken($bg, 5%);
  border-color: mix($a, $b, 50%);
  outline: saturate($color, 20%);
}
"""
        result = self.parser.parse(scss, "colors.scss")
        color_calls = [fc for fc in result.function_calls if fc.category == "color"]
        assert len(color_calls) >= 3

    def test_math_function_category(self):
        scss = """
@use "sass:math";
.box {
  width: math.div(100%, 3);
  height: math.round(14.5px);
  padding: math.ceil(3.2px);
}
"""
        result = self.parser.parse(scss, "math.scss")
        math_calls = [fc for fc in result.function_calls
                      if fc.category == "math" or fc.namespace == "math"]
        assert len(math_calls) >= 2
