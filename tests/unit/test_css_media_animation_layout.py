"""Unit tests for CSS media, animation, layout, function, and preprocessor extractors."""

import pytest

from codetrellis.extractors.css.media_extractor import CSSMediaExtractor
from codetrellis.extractors.css.animation_extractor import CSSAnimationExtractor
from codetrellis.extractors.css.layout_extractor import CSSLayoutExtractor
from codetrellis.extractors.css.function_extractor import CSSFunctionExtractor
from codetrellis.extractors.css.preprocessor_extractor import CSSPreprocessorExtractor


class TestCSSMediaExtractor:
    """Tests for CSSMediaExtractor."""

    def setup_method(self):
        self.extractor = CSSMediaExtractor()

    def test_basic_media_query(self):
        css = "@media (max-width: 768px) { .mobile { display: block; } }"
        result = self.extractor.extract(css)
        assert len(result['media_queries']) >= 1
        assert 'max-width' in result['media_queries'][0].query

    def test_range_syntax_media_query(self):
        css = "@media (width >= 768px) { .desktop { display: flex; } }"
        result = self.extractor.extract(css)
        assert len(result['media_queries']) >= 1
        assert result['stats'].get('has_range_syntax', False) is True

    def test_prefers_color_scheme(self):
        css = "@media (prefers-color-scheme: dark) { body { background: #000; } }"
        result = self.extractor.extract(css)
        assert len(result['media_queries']) >= 1

    def test_prefers_reduced_motion(self):
        css = "@media (prefers-reduced-motion: reduce) { * { animation: none; } }"
        result = self.extractor.extract(css)
        assert len(result['media_queries']) >= 1

    def test_supports_query(self):
        css = "@supports (display: grid) { .grid { display: grid; } }"
        result = self.extractor.extract(css)
        assert len(result['supports']) >= 1

    def test_cascade_layer(self):
        css = "@layer base, components, utilities;"
        result = self.extractor.extract(css)
        assert len(result['layers']) >= 1

    def test_container_query(self):
        css = """
        .wrapper { container-type: inline-size; }
        @container (min-width: 400px) { .card { flex-direction: row; } }
        """
        result = self.extractor.extract(css)
        assert len(result['container_queries']) >= 1

    def test_houdini_property(self):
        css = """@property --my-color {
            syntax: '<color>';
            inherits: false;
            initial-value: red;
        }"""
        result = self.extractor.extract(css)
        assert result['stats'].get('has_houdini', False) is True

    def test_stats_output(self):
        css = "@media (max-width: 768px) { .a { } }"
        result = self.extractor.extract(css)
        assert 'total_media_queries' in result['stats']


class TestCSSAnimationExtractor:
    """Tests for CSSAnimationExtractor."""

    def setup_method(self):
        self.extractor = CSSAnimationExtractor()

    def test_keyframes_extraction(self):
        css = """@keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }"""
        result = self.extractor.extract(css)
        assert len(result['keyframes']) >= 1
        assert result['keyframes'][0].name == 'fadeIn'

    def test_vendor_prefix_keyframes(self):
        css = """@-webkit-keyframes slideIn {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(0); }
        }"""
        result = self.extractor.extract(css)
        assert len(result['keyframes']) >= 1

    def test_transition_extraction(self):
        css = ".button { transition: all 0.3s ease; }"
        result = self.extractor.extract(css)
        assert len(result['transitions']) >= 1

    def test_animation_usage(self):
        css = ".spinner { animation: rotate 1s linear infinite; }"
        result = self.extractor.extract(css)
        assert len(result['animations']) >= 1

    def test_scroll_driven_animation(self):
        css = ".hero { animation-timeline: view(); }"
        result = self.extractor.extract(css)
        assert result['stats'].get('has_scroll_driven', False) is True

    def test_will_change(self):
        css = ".animated { will-change: transform, opacity; }"
        result = self.extractor.extract(css)
        assert result['stats'].get('has_will_change', False) is True

    def test_stats_output(self):
        css = "@keyframes a { from {} to {} }"
        result = self.extractor.extract(css)
        assert 'total_keyframes' in result['stats']


class TestCSSLayoutExtractor:
    """Tests for CSSLayoutExtractor."""

    def setup_method(self):
        self.extractor = CSSLayoutExtractor()

    def test_flexbox_detection(self):
        css = """.container {
            display: flex;
            flex-direction: row;
            justify-content: center;
            align-items: center;
            gap: 1rem;
        }"""
        result = self.extractor.extract(css)
        assert len(result['flexbox']) >= 1
        fb = result['flexbox'][0]
        assert fb.direction == 'row'
        assert fb.justify_content == 'center'

    def test_grid_detection(self):
        css = """.grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            grid-template-rows: auto;
            gap: 16px;
        }"""
        result = self.extractor.extract(css)
        assert len(result['grid']) >= 1
        assert 'repeat(3, 1fr)' in result['grid'][0].template_columns

    def test_subgrid_detection(self):
        css = """.subgrid-item {
            display: grid;
            grid-template-columns: subgrid;
        }"""
        result = self.extractor.extract(css)
        assert len(result['grid']) >= 1
        assert result['grid'][0].is_subgrid is True

    def test_multi_column_detection(self):
        css = """.text { column-count: 3; column-gap: 2rem; }"""
        result = self.extractor.extract(css)
        assert len(result['multi_column']) >= 1

    def test_stats(self):
        css = ".a { display: flex; } .b { display: grid; }"
        result = self.extractor.extract(css)
        assert result['stats']['flexbox_count'] >= 1
        assert result['stats']['grid_count'] >= 1


class TestCSSFunctionExtractor:
    """Tests for CSSFunctionExtractor."""

    def setup_method(self):
        self.extractor = CSSFunctionExtractor()

    def test_calc_function(self):
        css = ".box { width: calc(100% - 2rem); }"
        result = self.extractor.extract(css)
        found = [f for f in result['functions'] if f.function_name == 'calc']
        assert len(found) >= 1
        assert found[0].category == 'math'

    def test_clamp_function(self):
        css = "h1 { font-size: clamp(1.5rem, 5vw, 3rem); }"
        result = self.extractor.extract(css)
        found = [f for f in result['functions'] if f.function_name == 'clamp']
        assert len(found) >= 1

    def test_var_function(self):
        css = ".text { color: var(--text-color, #333); }"
        result = self.extractor.extract(css)
        found = [f for f in result['functions'] if f.function_name == 'var']
        assert len(found) >= 1
        assert found[0].category == 'reference'

    def test_gradient_function(self):
        css = ".bg { background: linear-gradient(to right, red, blue); }"
        result = self.extractor.extract(css)
        found = [f for f in result['functions'] if f.function_name == 'linear-gradient']
        assert len(found) >= 1
        assert found[0].category == 'gradient'

    def test_color_functions(self):
        css = ".a { color: oklch(0.7 0.15 250); }"
        result = self.extractor.extract(css)
        found = [f for f in result['functions'] if f.function_name == 'oklch']
        assert len(found) >= 1
        assert result['stats']['has_modern_color'] is True

    def test_nested_functions(self):
        css = ".box { width: calc(100% - var(--spacing)); }"
        result = self.extractor.extract(css)
        # var should be nested inside calc
        var_fn = [f for f in result['functions'] if f.function_name == 'var']
        if var_fn:
            assert var_fn[0].is_nested is True

    def test_stats(self):
        css = ".a { width: calc(100%); color: var(--c); }"
        result = self.extractor.extract(css)
        assert result['stats']['total_function_calls'] >= 2
        assert result['stats']['has_math_functions'] is True


class TestCSSPreprocessorExtractor:
    """Tests for CSSPreprocessorExtractor."""

    def setup_method(self):
        self.extractor = CSSPreprocessorExtractor()

    def test_scss_variables(self):
        scss = "$primary: #3498db;\n$font-size: 16px;"
        result = self.extractor.extract(scss, "style.scss")
        assert len(result['variables']) >= 2

    def test_scss_mixin_definition(self):
        scss = """@mixin flex-center($direction: row) {
            display: flex;
            flex-direction: $direction;
            justify-content: center;
            align-items: center;
        }"""
        result = self.extractor.extract(scss, "mixins.scss")
        defs = [m for m in result['mixins'] if not m.is_usage]
        assert len(defs) >= 1
        assert defs[0].name == 'flex-center'
        assert len(defs[0].parameters) >= 1

    def test_scss_mixin_usage(self):
        scss = ".container { @include flex-center(column); }"
        result = self.extractor.extract(scss, "style.scss")
        usages = [m for m in result['mixins'] if m.is_usage]
        assert len(usages) >= 1
        assert usages[0].name == 'flex-center'

    def test_scss_extend(self):
        scss = """%visually-hidden { position: absolute; }
        .sr-only { @extend %visually-hidden; }"""
        result = self.extractor.extract(scss, "style.scss")
        assert len(result['extends']) >= 1
        placeholders = [e for e in result['extends'] if e.is_placeholder]
        assert len(placeholders) >= 1

    def test_scss_function(self):
        scss = """@function rem($px) {
            @return $px / 16 * 1rem;
        }"""
        result = self.extractor.extract(scss, "functions.scss")
        defs = [f for f in result['functions'] if not f.is_usage]
        assert len(defs) >= 1
        assert defs[0].name == 'rem'

    def test_scss_use_forward(self):
        scss = """@use 'variables' as vars;
        @forward 'mixins';"""
        result = self.extractor.extract(scss, "style.scss")
        uses = [i for i in result['imports'] if i.import_type == 'use']
        forwards = [i for i in result['imports'] if i.import_type == 'forward']
        assert len(uses) >= 1
        assert len(forwards) >= 1

    def test_less_variables(self):
        less = "@primary: #3498db;\n@font-size: 16px;"
        result = self.extractor.extract(less, "style.less")
        assert len(result['variables']) >= 2

    def test_less_mixin(self):
        less = """.border-radius(@radius) {
            border-radius: @radius;
        }"""
        result = self.extractor.extract(less, "style.less")
        defs = [m for m in result['mixins'] if not m.is_usage]
        assert len(defs) >= 1

    def test_less_extend(self):
        less = ".nav:extend(.clearfix) { }"
        result = self.extractor.extract(less, "style.less")
        assert len(result['extends']) >= 1

    def test_import_detection(self):
        scss = "@import 'variables';\n@import 'mixins';"
        result = self.extractor.extract(scss, "style.scss")
        imports = [i for i in result['imports'] if i.import_type == 'import']
        assert len(imports) >= 2

    def test_preprocessor_detection(self):
        scss = "$color: red;\n@mixin test { color: $color; }"
        result = self.extractor.extract(scss, "style.scss")
        assert result['stats']['preprocessor'] == 'scss'

    def test_module_system_detection(self):
        scss = "@use 'sass:math';"
        result = self.extractor.extract(scss, "style.scss")
        assert result['stats']['has_module_system'] is True

    def test_stats(self):
        scss = """$a: 1;
        @mixin test { display: flex; }
        .box { @include test; }"""
        result = self.extractor.extract(scss, "style.scss")
        assert result['stats']['total_variables'] >= 1
        assert result['stats']['total_mixins'] >= 1
        assert result['stats']['total_mixin_usages'] >= 1
