"""Unit tests for the EnhancedCSSParser integration."""

import pytest

from codetrellis.css_parser_enhanced import EnhancedCSSParser, CSSParseResult


class TestEnhancedCSSParser:
    """Tests for the full EnhancedCSSParser orchestration."""

    def setup_method(self):
        self.parser = EnhancedCSSParser()

    def test_empty_content(self):
        result = self.parser.parse("")
        assert isinstance(result, CSSParseResult)
        assert result.selectors == []

    def test_basic_css_file(self):
        css = """
        body { margin: 0; font-family: sans-serif; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #333; color: white; }
        """
        result = self.parser.parse(css, "style.css")
        assert result.file_type == 'css'
        assert len(result.selectors) >= 3
        assert len(result.properties) >= 3

    def test_css3_version_detection(self):
        css = """
        .box {
            display: flex;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        """
        result = self.parser.parse(css, "style.css")
        assert result.css_version == 'CSS3'

    def test_css4_version_detection(self):
        css = """
        .card:has(> img) { padding: 0; }
        @container (min-width: 400px) { .card { flex-direction: row; } }
        @layer base, components;
        """
        result = self.parser.parse(css, "style.css")
        assert result.css_version == 'CSS4+'

    def test_scss_version_detection(self):
        scss = """$primary: #3498db;
        .button { color: $primary; }
        """
        result = self.parser.parse(scss, "style.scss")
        assert result.file_type == 'scss'
        assert result.css_version == 'SCSS'

    def test_less_detection(self):
        less = "@primary: #3498db;\n.button { color: @primary; }"
        result = self.parser.parse(less, "style.less")
        assert result.file_type == 'less'
        assert result.css_version == 'Less'

    def test_stylus_detection(self):
        styl = "primary = #3498db"
        result = self.parser.parse(styl, "style.styl")
        assert result.file_type == 'stylus'

    def test_full_feature_css(self):
        """Test a comprehensive CSS file with many features."""
        css = """
        :root {
            --color-primary: oklch(0.7 0.15 250);
            --spacing-md: 1rem;
            --font-size-base: 16px;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --color-primary: oklch(0.8 0.12 250);
            }
        }

        @layer base, components, utilities;

        @layer base {
            body { margin: 0; font-size: var(--font-size-base); }
        }

        @layer components {
            .card {
                display: flex;
                flex-direction: column;
                gap: var(--spacing-md);
                border-radius: 8px;
            }

            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
            }
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .animate { animation: fadeIn 0.3s ease-in; }

        @container (min-width: 400px) {
            .card { flex-direction: row; }
        }

        h1 { font-size: clamp(1.5rem, 5vw, 3rem); }
        """
        result = self.parser.parse(css, "app.css")
        assert result.css_version == 'CSS4+'
        assert len(result.variables) >= 3
        assert len(result.media_queries) >= 1
        assert len(result.layers) >= 1
        assert len(result.keyframes) >= 1
        assert len(result.flexbox_usages) >= 1
        assert len(result.grid_usages) >= 1
        assert len(result.container_queries) >= 1
        assert len(result.function_usages) >= 1

    def test_scss_full_features(self):
        """Test SCSS file with preprocessor features."""
        scss = """
        $primary: #3498db;
        $spacing: 1rem;

        @mixin flex-center($direction: row) {
            display: flex;
            flex-direction: $direction;
            justify-content: center;
            align-items: center;
        }

        @function rem($px) {
            @return $px / 16 * 1rem;
        }

        .container {
            @include flex-center(column);
            max-width: 1200px;
            padding: $spacing;
        }

        %visually-hidden {
            position: absolute;
            width: 1px;
            height: 1px;
        }

        .sr-only {
            @extend %visually-hidden;
        }

        @use 'variables' as vars;
        """
        result = self.parser.parse(scss, "style.scss")
        assert result.file_type == 'scss'
        assert result.detected_preprocessor == 'scss'
        assert len(result.preprocessor_variables) >= 2
        assert len(result.mixins) >= 1
        assert len(result.preprocessor_functions) >= 1
        assert len(result.extends) >= 1

    def test_feature_detection_bem(self):
        css = """.card__header--active { color: red; }
        .card__body { padding: 1rem; }"""
        result = self.parser.parse(css, "components.css")
        assert 'BEM' in result.detected_features

    def test_feature_detection_tailwind(self):
        css = "@tailwind base;\n@tailwind components;\n@apply flex items-center;"
        result = self.parser.parse(css, "style.css")
        assert 'tailwind' in result.detected_features

    def test_feature_detection_css_modules(self):
        css = ".title { composes: heading from './typography.css'; }"
        result = self.parser.parse(css, "Card.module.css")
        assert 'css_modules' in result.detected_features

    def test_feature_detection_custom_properties(self):
        css = ":root { --color: red; }\n.a { color: var(--color); }"
        result = self.parser.parse(css, "style.css")
        assert 'custom_properties' in result.detected_features

    def test_feature_detection_container_queries(self):
        css = "@container (min-width: 400px) { .a { flex: 1; } }"
        result = self.parser.parse(css, "style.css")
        assert 'container_queries' in result.detected_features

    def test_feature_detection_cascade_layers(self):
        css = "@layer base, components;"
        result = self.parser.parse(css, "style.css")
        assert 'cascade_layers' in result.detected_features

    def test_feature_detection_dark_mode(self):
        css = """
        :root { --bg: white; }
        @media (prefers-color-scheme: dark) { :root { --bg: black; } }
        """
        result = self.parser.parse(css, "style.css")
        assert 'dark_mode' in result.detected_features

    def test_parse_result_dataclass_fields(self):
        """Ensure CSSParseResult has all expected fields."""
        result = CSSParseResult(file_path="test.css")
        assert hasattr(result, 'selectors')
        assert hasattr(result, 'properties')
        assert hasattr(result, 'variables')
        assert hasattr(result, 'media_queries')
        assert hasattr(result, 'keyframes')
        assert hasattr(result, 'flexbox_usages')
        assert hasattr(result, 'grid_usages')
        assert hasattr(result, 'function_usages')
        assert hasattr(result, 'mixins')
        assert hasattr(result, 'detected_features')
        assert hasattr(result, 'css_version')

    def test_file_path_tracking(self):
        css = ".a { color: red; }"
        result = self.parser.parse(css, "/src/styles/app.css")
        assert result.file_path == "/src/styles/app.css"
        for sel in result.selectors:
            assert sel.file == "/src/styles/app.css"

    def test_minified_css_handled(self):
        """Test that CSS with no newlines can still be parsed."""
        css = ".a{color:red}.b{margin:0}.c{display:flex;gap:1rem}"
        result = self.parser.parse(css, "min.css")
        assert len(result.selectors) >= 2
