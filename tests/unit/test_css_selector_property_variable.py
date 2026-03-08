"""Unit tests for CSS selector, property, and variable extractors."""

import pytest

from codetrellis.extractors.css.selector_extractor import CSSSelectorExtractor
from codetrellis.extractors.css.property_extractor import CSSPropertyExtractor
from codetrellis.extractors.css.variable_extractor import CSSVariableExtractor


class TestCSSSelectorExtractor:
    """Tests for CSSSelectorExtractor."""

    def setup_method(self):
        self.extractor = CSSSelectorExtractor()

    def test_basic_class_selector(self):
        css = ".button { color: red; }"
        result = self.extractor.extract(css)
        assert len(result['selectors']) >= 1
        found = [s for s in result['selectors'] if '.button' in s.selector]
        assert len(found) >= 1
        assert found[0].selector_type == 'class'

    def test_id_selector(self):
        css = "#main-nav { display: flex; }"
        result = self.extractor.extract(css)
        found = [s for s in result['selectors'] if '#main-nav' in s.selector]
        assert len(found) >= 1
        assert found[0].selector_type == 'id'

    def test_element_selector(self):
        css = "body { margin: 0; }"
        result = self.extractor.extract(css)
        found = [s for s in result['selectors'] if 'body' in s.selector]
        assert len(found) >= 1
        assert found[0].selector_type == 'element'

    def test_pseudo_class_selector(self):
        css = "a:hover { color: blue; }"
        result = self.extractor.extract(css)
        found = [s for s in result['selectors'] if ':hover' in s.selector]
        assert len(found) >= 1
        assert found[0].selector_type == 'pseudo_class'

    def test_pseudo_element_selector(self):
        css = "p::first-line { font-weight: bold; }"
        result = self.extractor.extract(css)
        found = [s for s in result['selectors'] if '::first-line' in s.selector]
        assert len(found) >= 1
        assert found[0].selector_type == 'pseudo_element'

    def test_attribute_selector(self):
        css = 'input[type="text"] { border: 1px solid; }'
        result = self.extractor.extract(css)
        found = [s for s in result['selectors'] if '[type' in s.selector]
        assert len(found) >= 1
        assert found[0].selector_type == 'attribute'

    def test_nested_selector(self):
        css = """.card {
            color: black;
            & .title { font-size: 1.2rem; }
        }"""
        result = self.extractor.extract(css)
        assert result['stats'].get('has_nesting', False) is True

    def test_css4_has_selector(self):
        css = "div:has(> img) { padding: 1rem; }"
        result = self.extractor.extract(css)
        found = [s for s in result['selectors'] if ':has(' in s.selector]
        assert len(found) >= 1

    def test_specificity_calculation(self):
        """Test that specificity is computed as (id, class, element)."""
        css = "#main .nav a { color: blue; }"
        result = self.extractor.extract(css)
        found = [s for s in result['selectors'] if '#main' in s.selector]
        assert len(found) >= 1
        spec = found[0].specificity
        # #main = 1 id, .nav = 1 class, a = 1 element
        assert spec[0] >= 1  # at least 1 id
        assert spec[1] >= 1  # at least 1 class
        assert spec[2] >= 1  # at least 1 element

    def test_multiple_selectors(self):
        css = """
        .header { background: #fff; }
        .footer { background: #333; }
        .sidebar { width: 300px; }
        """
        result = self.extractor.extract(css)
        assert len(result['selectors']) >= 3

    def test_at_rule_detection(self):
        css = "@media (max-width: 768px) { .mobile { display: block; } }"
        result = self.extractor.extract(css)
        assert len(result['rules']) >= 1

    def test_stats_output(self):
        css = """.a { } .b { } #c { } div { }"""
        result = self.extractor.extract(css)
        assert 'total_selectors' in result['stats']
        assert result['stats']['total_selectors'] >= 3


class TestCSSPropertyExtractor:
    """Tests for CSSPropertyExtractor."""

    def setup_method(self):
        self.extractor = CSSPropertyExtractor()

    def test_basic_properties(self):
        css = ".box { color: red; margin: 10px; padding: 5px; }"
        result = self.extractor.extract(css)
        names = [p.property_name for p in result['properties']]
        assert 'color' in names
        assert 'margin' in names

    def test_shorthand_detection(self):
        css = ".box { margin: 10px 20px; border: 1px solid black; }"
        result = self.extractor.extract(css)
        shorthands = [p for p in result['properties'] if p.is_shorthand]
        assert len(shorthands) >= 1

    def test_important_detection(self):
        css = ".override { color: red !important; }"
        result = self.extractor.extract(css)
        important = [p for p in result['properties'] if p.is_important]
        assert len(important) >= 1

    def test_vendor_prefix_detection(self):
        css = ".anim { -webkit-transform: rotate(45deg); }"
        result = self.extractor.extract(css)
        prefixed = [p for p in result['properties'] if p.is_vendor_prefixed]
        assert len(prefixed) >= 1

    def test_logical_property_detection(self):
        css = ".box { margin-inline: 1rem; padding-block-start: 0.5rem; }"
        result = self.extractor.extract(css)
        logical = [p for p in result['properties'] if p.is_logical_property]
        assert len(logical) >= 1

    def test_property_categories(self):
        css = """
        .box {
            display: flex;
            color: red;
            font-size: 16px;
            transition: all 0.3s;
        }"""
        result = self.extractor.extract(css)
        categories = set(p.category for p in result['properties'])
        assert len(categories) >= 2

    def test_stats_output(self):
        css = ".box { color: red; margin: 10px; }"
        result = self.extractor.extract(css)
        assert 'total_properties' in result['stats']


class TestCSSVariableExtractor:
    """Tests for CSSVariableExtractor."""

    def setup_method(self):
        self.extractor = CSSVariableExtractor()

    def test_root_variables(self):
        css = """:root {
            --color-primary: #3498db;
            --spacing-md: 1rem;
        }"""
        result = self.extractor.extract(css)
        assert len(result['variables']) >= 2
        names = [v.name for v in result['variables']]
        assert '--color-primary' in names
        assert '--spacing-md' in names

    def test_component_scoped_variables(self):
        css = """.card {
            --card-bg: white;
            --card-border: 1px solid #eee;
        }"""
        result = self.extractor.extract(css)
        found = [v for v in result['variables'] if '--card-bg' in v.name]
        assert len(found) >= 1
        assert found[0].scope == '.card'

    def test_dark_mode_theme(self):
        css = """
        :root { --bg: white; --text: #333; }
        @media (prefers-color-scheme: dark) {
            :root { --bg: #1a1a1a; --text: #eee; }
        }"""
        result = self.extractor.extract(css)
        assert result['stats'].get('has_dark_mode', False) is True

    def test_variable_categories(self):
        css = """:root {
            --color-primary: #3498db;
            --spacing-md: 1rem;
            --font-size-base: 16px;
        }"""
        result = self.extractor.extract(css)
        categories = set(v.category for v in result['variables'])
        assert 'color' in categories

    def test_scss_variables(self):
        scss = "$primary: #3498db;\n$spacing: 1rem;"
        result = self.extractor.extract(scss, "style.scss")
        found = [v for v in result['preprocessor_vars'] if '$primary' in v.name]
        assert len(found) >= 1

    def test_theme_detection(self):
        css = """:root {
            --color-primary: #333;
            --color-secondary: #666;
            --color-accent: #0077cc;
        }"""
        result = self.extractor.extract(css)
        # Should have at least some variables
        assert len(result['variables']) >= 3

    def test_stats_output(self):
        css = ":root { --a: 1; --b: 2; }"
        result = self.extractor.extract(css)
        assert 'total_variables' in result['stats']
