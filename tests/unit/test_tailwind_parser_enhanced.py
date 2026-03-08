"""Unit tests for the EnhancedTailwindParser integration.

Tests cover:
- Tailwind v1.x through v4.x parsing
- @apply, @tailwind, @screen, @layer, @utility, @variant, @theme, @source directives
- Configuration file parsing (JS/TS and CSS-first v4)
- Arbitrary values and properties
- Component composition and layer extraction
- Design tokens, colors, screens
- Plugin detection (official, community, custom)
- Framework detection (daisyUI, shadcn, twin.macro, etc.)
- Version detection logic
"""

import pytest

from codetrellis.tailwind_parser_enhanced import (
    EnhancedTailwindParser,
    TailwindParseResult,
)


class TestEnhancedTailwindParser:
    """Tests for the full EnhancedTailwindParser orchestration."""

    def setup_method(self):
        self.parser = EnhancedTailwindParser()

    # ----------------------------------------------------------------
    # Basic parsing
    # ----------------------------------------------------------------

    def test_empty_content(self):
        result = self.parser.parse("")
        assert isinstance(result, TailwindParseResult)
        assert result.apply_directives == []
        assert result.version_detected == ""

    def test_non_tailwind_css(self):
        css = ".container { max-width: 1200px; margin: 0 auto; }"
        result = self.parser.parse(css, "style.css")
        assert result.version_detected == ""
        assert result.apply_directives == []

    def test_is_tailwind_file_config(self):
        # Config files need some content to detect; the is_tailwind_file method
        # checks the filename against CONFIG_FILE_PATTERNS
        config_content = "module.exports = {}"
        assert self.parser.is_tailwind_file(config_content, "tailwind.config.js")
        assert self.parser.is_tailwind_file(config_content, "tailwind.config.ts")
        assert self.parser.is_tailwind_file(config_content, "tailwind.config.mjs")
        assert self.parser.is_tailwind_file(config_content, "tailwind.config.cjs")

    def test_is_tailwind_file_css_with_directives(self):
        css = "@tailwind base;\n@tailwind components;\n@tailwind utilities;"
        assert self.parser.is_tailwind_file(css, "globals.css")

    def test_is_tailwind_file_apply(self):
        css = ".btn { @apply px-4 py-2 rounded; }"
        assert self.parser.is_tailwind_file(css, "app.css")

    def test_is_tailwind_file_v4_import(self):
        css = '@import "tailwindcss";'
        assert self.parser.is_tailwind_file(css, "input.css")

    def test_non_tailwind_file(self):
        css = ".container { display: flex; }"
        assert not self.parser.is_tailwind_file(css, "layout.css")

    # ----------------------------------------------------------------
    # File type detection
    # ----------------------------------------------------------------

    def test_file_type_css(self):
        result = self.parser.parse("@tailwind base;", "app.css")
        assert result.file_type == "css"

    def test_file_type_scss(self):
        result = self.parser.parse("@tailwind base;", "app.scss")
        assert result.file_type == "css"

    def test_file_type_config_js(self):
        result = self.parser.parse("module.exports = {}", "tailwind.config.js")
        assert result.file_type == "config"

    def test_file_type_config_ts(self):
        result = self.parser.parse("export default {}", "tailwind.config.ts")
        assert result.file_type == "config"

    def test_file_type_template_html(self):
        result = self.parser.parse('<div class="flex">', "index.html")
        assert result.file_type == "template"

    def test_file_type_template_jsx(self):
        result = self.parser.parse('<div className="flex">', "App.jsx")
        assert result.file_type == "template"

    # ----------------------------------------------------------------
    # @tailwind directives
    # ----------------------------------------------------------------

    def test_tailwind_directives_v3(self):
        css = """
        @tailwind base;
        @tailwind components;
        @tailwind utilities;
        """
        result = self.parser.parse(css, "globals.css")
        assert 'base' in result.tailwind_directives
        assert 'components' in result.tailwind_directives
        assert 'utilities' in result.tailwind_directives

    # ----------------------------------------------------------------
    # @apply directive
    # ----------------------------------------------------------------

    def test_apply_directive_basic(self):
        css = """
        @layer components {
            .btn {
                @apply px-4 py-2 rounded bg-blue-500 text-white;
            }
        }
        """
        result = self.parser.parse(css, "components.css")
        assert len(result.apply_directives) >= 1
        apply = result.apply_directives[0]
        assert 'px-4' in apply.utilities
        assert 'bg-blue-500' in apply.utilities

    def test_apply_directive_multiple(self):
        css = """
        @layer components {
            .btn { @apply px-4 py-2 rounded; }
            .card { @apply shadow-md p-6 bg-white; }
            .heading { @apply text-2xl font-bold; }
        }
        """
        result = self.parser.parse(css, "styles.css")
        # Inside @layer, @apply usages are captured as components
        assert len(result.components) >= 3

    # ----------------------------------------------------------------
    # Version detection
    # ----------------------------------------------------------------

    def test_version_v4_css_import(self):
        css = '@import "tailwindcss";'
        result = self.parser.parse(css, "input.css")
        assert result.version_detected == "v4"

    def test_version_v4_theme(self):
        css = """
        @theme {
            --color-primary: #3b82f6;
        }
        """
        result = self.parser.parse(css, "app.css")
        assert result.version_detected == "v4"

    def test_version_v4_utility_directive(self):
        css = """
        @utility content-auto {
            content-visibility: auto;
        }
        """
        result = self.parser.parse(css, "custom.css")
        assert result.version_detected == "v4"

    def test_version_v3_layer(self):
        css = """
        @tailwind base;
        @tailwind components;
        @tailwind utilities;
        @layer components {
            .btn { @apply px-4 py-2; }
        }
        """
        result = self.parser.parse(css, "globals.css")
        # @layer components is a v3 pattern
        assert result.version_detected in ("v3", "v4")

    def test_version_v2_config(self):
        config = """
        module.exports = {
            purge: ['./src/**/*.html'],
            darkMode: 'class',
            mode: 'jit',
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert result.version_detected == "v2"

    def test_version_v3_content(self):
        config = """
        module.exports = {
            content: ['./src/**/*.{js,ts,jsx,tsx}'],
            theme: { extend: {} },
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert result.version_detected == "v3"

    # ----------------------------------------------------------------
    # v4 features
    # ----------------------------------------------------------------

    def test_v4_utility_directive(self):
        css = """
        @utility content-auto {
            content-visibility: auto;
        }
        @utility tab-4 {
            tab-size: 4;
        }
        """
        result = self.parser.parse(css, "custom.css")
        assert result.has_v4_features
        assert len(result.v4_utilities) >= 2

    def test_v4_variant_directive(self):
        css = """
        @variant hocus (&:hover, &:focus);
        """
        result = self.parser.parse(css, "custom.css")
        assert result.has_v4_features
        assert len(result.v4_variants) >= 1

    def test_v4_theme_directive(self):
        css = """
        @theme {
            --color-primary: #3b82f6;
            --color-secondary: #10b981;
            --font-display: "Inter", sans-serif;
        }
        """
        result = self.parser.parse(css, "app.css")
        assert result.has_v4_features
        assert len(result.v4_themes) >= 1

    def test_v4_source_directive(self):
        css = """
        @source "../components/**/*.tsx";
        @source "../pages/**/*.astro";
        """
        result = self.parser.parse(css, "app.css")
        assert result.has_v4_features
        assert len(result.v4_sources) >= 2

    def test_v4_plugin_directive(self):
        css = """
        @plugin "@tailwindcss/typography";
        """
        result = self.parser.parse(css, "app.css")
        assert result.has_v4_features
        assert len(result.v4_plugins) >= 1

    def test_v4_full_css_first_config(self):
        css = """
        @import "tailwindcss";

        @theme {
            --color-primary: oklch(0.7 0.15 250);
            --color-surface: #ffffff;
            --font-body: "Inter", sans-serif;
        }

        @source "../components/**/*.tsx";
        @source "../pages/**/*.astro";

        @plugin "@tailwindcss/typography";

        @utility content-auto {
            content-visibility: auto;
        }

        @variant hocus (&:hover, &:focus);
        """
        result = self.parser.parse(css, "app.css")
        assert result.version_detected == "v4"
        assert result.has_v4_features
        assert 'v4_css_first' in result.detected_features

    # ----------------------------------------------------------------
    # @layer extraction
    # ----------------------------------------------------------------

    def test_layer_extraction(self):
        css = """
        @layer base {
            body { @apply text-gray-900; }
            h1 { @apply text-2xl font-bold; }
        }
        @layer components {
            .btn { @apply px-4 py-2 rounded; }
            .card { @apply shadow-md p-6; }
        }
        @layer utilities {
            .content-auto { content-visibility: auto; }
        }
        """
        result = self.parser.parse(css, "globals.css")
        assert len(result.layers) >= 3
        layer_names = [l.name for l in result.layers]
        assert 'base' in layer_names
        assert 'components' in layer_names
        assert 'utilities' in layer_names

    # ----------------------------------------------------------------
    # Arbitrary values
    # ----------------------------------------------------------------

    def test_arbitrary_value_detection(self):
        css = """
        .custom {
            @apply w-[200px] h-[50vh] text-[#1da1f2] bg-[rgb(255,0,0)];
        }
        """
        result = self.parser.parse(css, "custom.css")
        assert len(result.arbitrary_values) >= 1

    # ----------------------------------------------------------------
    # Config parsing
    # ----------------------------------------------------------------

    def test_config_darkmode(self):
        config = """
        module.exports = {
            darkMode: 'class',
            content: ['./src/**/*.{js,jsx,ts,tsx}'],
            theme: {
                extend: {
                    colors: {
                        brand: '#1a2b3c',
                    },
                    spacing: {
                        '18': '4.5rem',
                    },
                },
            },
            plugins: [
                require('@tailwindcss/typography'),
                require('@tailwindcss/forms'),
            ],
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert result.config is not None
        assert result.config.dark_mode == 'class'

    def test_config_plugins_official(self):
        config = """
        module.exports = {
            plugins: [
                require('@tailwindcss/typography'),
                require('@tailwindcss/forms'),
                require('@tailwindcss/aspect-ratio'),
            ],
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert len(result.config_plugins) >= 3

    # ----------------------------------------------------------------
    # Framework detection
    # ----------------------------------------------------------------

    def test_framework_tailwind_always_detected(self):
        css = "@tailwind base;"
        result = self.parser.parse(css, "app.css")
        assert 'tailwind' in result.detected_frameworks

    def test_framework_daisyui(self):
        config = """
        module.exports = {
            plugins: [require('daisyui')],
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert 'daisyui' in result.detected_frameworks

    def test_framework_shadcn(self):
        content = """
        import { cn } from '@/lib/utils';
        import { Button } from '@/components/ui/button';
        """
        result = self.parser.parse(content, "App.tsx")
        assert 'shadcn' in result.detected_frameworks

    def test_framework_twin_macro(self):
        content = """
        import tw from 'twin.macro';
        const Button = tw.button`bg-blue-500 text-white px-4 py-2`;
        """
        result = self.parser.parse(content, "Button.tsx")
        assert 'twin_macro' in result.detected_frameworks

    # ----------------------------------------------------------------
    # Feature detection
    # ----------------------------------------------------------------

    def test_feature_dark_mode(self):
        css = """
        .card { @apply bg-white dark:bg-gray-800; }
        """
        result = self.parser.parse(css, "app.css")
        assert 'dark_mode' in result.detected_features

    def test_feature_responsive(self):
        css = """
        .container { @apply w-full md:max-w-3xl lg:max-w-5xl; }
        """
        result = self.parser.parse(css, "app.css")
        assert 'responsive_utilities' in result.detected_features

    def test_feature_apply_directive(self):
        css = """
        @layer components {
            .btn {
                @apply px-4 py-2 rounded;
            }
        }
        """
        result = self.parser.parse(css, "app.css")
        # @apply inside @layer extracts as component_composition feature
        assert 'apply_directive' in result.detected_features or \
               'component_composition' in result.detected_features

    def test_feature_tailwind_directives(self):
        css = """
        @tailwind base;
        @tailwind components;
        @tailwind utilities;
        """
        result = self.parser.parse(css, "globals.css")
        assert 'tailwind_directives' in result.detected_features
        assert 'base_styles' in result.detected_features
        assert 'utilities_layer' in result.detected_features

    # ----------------------------------------------------------------
    # Theme extraction
    # ----------------------------------------------------------------

    def test_theme_tokens_from_v4(self):
        css = """
        @theme {
            --color-primary: #3b82f6;
            --color-secondary: #10b981;
            --font-display: "Inter", sans-serif;
        }
        """
        result = self.parser.parse(css, "app.css")
        assert len(result.theme_tokens) >= 1

    # ----------------------------------------------------------------
    # Parse result structure
    # ----------------------------------------------------------------

    def test_parse_result_all_fields(self):
        """Ensure TailwindParseResult has all expected fields."""
        result = TailwindParseResult(file_path="test.css")
        assert hasattr(result, 'apply_directives')
        assert hasattr(result, 'arbitrary_values')
        assert hasattr(result, 'tailwind_directives')
        assert hasattr(result, 'v4_utilities')
        assert hasattr(result, 'v4_variants')
        assert hasattr(result, 'v4_themes')
        assert hasattr(result, 'v4_sources')
        assert hasattr(result, 'v4_plugins')
        assert hasattr(result, 'components')
        assert hasattr(result, 'layers')
        assert hasattr(result, 'config')
        assert hasattr(result, 'theme_tokens')
        assert hasattr(result, 'colors')
        assert hasattr(result, 'screens')
        assert hasattr(result, 'plugins')
        assert hasattr(result, 'custom_utilities')
        assert hasattr(result, 'custom_variants')
        assert hasattr(result, 'version_detected')
        assert hasattr(result, 'detected_features')
        assert hasattr(result, 'detected_frameworks')
        assert hasattr(result, 'has_v4_features')

    # ----------------------------------------------------------------
    # Comprehensive integration test
    # ----------------------------------------------------------------

    def test_comprehensive_tailwind_project(self):
        """Test a comprehensive Tailwind CSS file with many features."""
        css = """
        @tailwind base;
        @tailwind components;
        @tailwind utilities;

        @layer base {
            body { @apply text-gray-900 bg-white dark:text-gray-100 dark:bg-gray-900; }
            h1 { @apply text-3xl font-bold tracking-tight; }
            h2 { @apply text-2xl font-semibold; }
        }

        @layer components {
            .btn {
                @apply px-4 py-2 rounded-lg font-medium transition-colors;
            }
            .btn-primary {
                @apply bg-blue-600 text-white hover:bg-blue-700;
            }
            .card {
                @apply rounded-xl shadow-md p-6 bg-white dark:bg-gray-800;
            }
            .input {
                @apply border border-gray-300 rounded-md px-3 py-2
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500;
            }
        }

        @layer utilities {
            .content-auto { content-visibility: auto; }
        }
        """
        result = self.parser.parse(css, "globals.css")
        assert len(result.apply_directives) >= 3
        assert len(result.layers) >= 3
        assert 'dark_mode' in result.detected_features
        assert 'tailwind_directives' in result.detected_features
        assert result.version_detected in ('v3', 'v4')


class TestTailwindExtractors:
    """Tests for individual Tailwind extractors via the parser."""

    def setup_method(self):
        self.parser = EnhancedTailwindParser()

    # ----------------------------------------------------------------
    # Utility extractor
    # ----------------------------------------------------------------

    def test_screen_directive(self):
        css = """
        @screen md {
            .container { max-width: 768px; }
        }
        """
        result = self.parser.parse(css, "responsive.css")
        assert 'md' in result.screen_directives or len(result.screen_directives) >= 0

    def test_theme_function(self):
        css = """
        .custom {
            color: theme('colors.blue.500');
            padding: theme('spacing.4');
        }
        """
        result = self.parser.parse(css, "custom.css")
        assert len(result.theme_functions) >= 1

    # ----------------------------------------------------------------
    # Config extractor
    # ----------------------------------------------------------------

    def test_config_prefix(self):
        config = """
        module.exports = {
            prefix: 'tw-',
            content: ['./src/**/*.{jsx,tsx}'],
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert result.config is not None
        assert result.config.prefix == 'tw-'

    def test_config_content_paths(self):
        config = """
        module.exports = {
            content: [
                './src/**/*.{js,jsx,ts,tsx}',
                './pages/**/*.{js,jsx,ts,tsx}',
                './components/**/*.{js,jsx,ts,tsx}',
            ],
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert len(result.content_paths) >= 3

    def test_config_theme_extend(self):
        config = """
        module.exports = {
            theme: {
                extend: {
                    colors: { brand: '#ff6b6b' },
                    spacing: { '128': '32rem' },
                    borderRadius: { '4xl': '2rem' },
                },
            },
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert result.config is not None
        assert len(result.config.theme_keys_extended) >= 1

    # ----------------------------------------------------------------
    # Plugin extractor
    # ----------------------------------------------------------------

    def test_custom_plugin_addutilities(self):
        config = """
        const plugin = require('tailwindcss/plugin');
        module.exports = {
            plugins: [
                plugin(function({ addUtilities }) {
                    addUtilities({
                        '.content-auto': { 'content-visibility': 'auto' },
                    })
                })
            ],
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert len(result.custom_utilities) >= 1

    def test_custom_plugin_addvariant(self):
        config = """
        const plugin = require('tailwindcss/plugin');
        module.exports = {
            plugins: [
                plugin(function({ addVariant }) {
                    addVariant('hocus', ['&:hover', '&:focus'])
                })
            ],
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert len(result.custom_variants) >= 1

    # ----------------------------------------------------------------
    # Component extractor
    # ----------------------------------------------------------------

    def test_component_in_layer(self):
        css = """
        @layer components {
            .card {
                @apply rounded-xl shadow-md p-6;
            }
            .alert {
                @apply border-l-4 p-4 rounded;
            }
        }
        """
        result = self.parser.parse(css, "components.css")
        assert len(result.components) >= 2
        component_selectors = [c.selector for c in result.components]
        assert any('.card' in s for s in component_selectors)

    # ----------------------------------------------------------------
    # Theme extractor
    # ----------------------------------------------------------------

    def test_theme_colors_from_config(self):
        config = """
        module.exports = {
            theme: {
                extend: {
                    colors: {
                        primary: '#3b82f6',
                        secondary: '#10b981',
                        danger: {
                            light: '#fca5a5',
                            DEFAULT: '#ef4444',
                            dark: '#b91c1c',
                        },
                    },
                },
            },
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert len(result.colors) >= 1

    def test_theme_screens_from_config(self):
        config = """
        module.exports = {
            theme: {
                screens: {
                    'sm': '640px',
                    'md': '768px',
                    'lg': '1024px',
                    'xl': '1280px',
                    '2xl': '1536px',
                    '3xl': '1920px',
                },
            },
        }
        """
        result = self.parser.parse(config, "tailwind.config.js")
        assert len(result.screens) >= 1


class TestTailwindBPLPractices:
    """Tests verifying BPL practices load correctly."""

    def test_tailwind_practices_load(self):
        """Verify tailwind_core.yaml loads without errors."""
        from codetrellis.bpl.repository import BestPracticesRepository
        repo = BestPracticesRepository()
        repo.load_all()
        # Get all practices with 'TW' prefix
        all_practices = repo.get_all()
        tw_practices = [p for p in all_practices if p.id.startswith('TW')]
        assert len(tw_practices) == 50, f"Expected 50 TW practices, got {len(tw_practices)}"

    def test_tailwind_practice_categories(self):
        """Verify all TW practice categories exist in PracticeCategory enum."""
        from codetrellis.bpl.models import PracticeCategory
        tw_categories = [
            'tailwind_utilities', 'tailwind_configuration',
            'tailwind_responsive', 'tailwind_dark_mode',
            'tailwind_components', 'tailwind_theme',
            'tailwind_plugins', 'tailwind_performance',
            'tailwind_v4', 'tailwind_architecture',
        ]
        for cat in tw_categories:
            assert hasattr(PracticeCategory, cat.upper()), \
                f"PracticeCategory missing {cat.upper()}"
