"""
EnhancedTailwindParser v1.0 - Comprehensive Tailwind CSS parser using all extractors.

This parser integrates all Tailwind extractors to provide complete parsing of
Tailwind CSS configuration and usage across CSS, HTML, JSX/TSX, and config files.

Supports:
- Tailwind CSS v1.x (basic utility-first, @tailwind directives, @apply)
- Tailwind CSS v2.x (dark mode, ring utilities, JIT mode, @variants, @responsive)
- Tailwind CSS v3.x (JIT engine default, arbitrary values, arbitrary properties,
    important modifier, @layer, content configuration, print variant, aspect-ratio,
    columns, container queries plugin, scroll-snap, touch-action, will-change,
    accent-color, break-after/before/inside, decoration utilities, outline utilities)
- Tailwind CSS v4.x (CSS-first configuration, @theme directive, @utility directive,
    @variant directive, @source directive, @plugin directive, @config directive,
    @import "tailwindcss", zero-config, native CSS nesting, light-dark(),
    container queries built-in, 3D transforms, @starting-style, field-sizing,
    color-scheme, interpolate-size, @property, not-* variants, in-* variants)

Utility Detection:
- All Tailwind utility categories (layout, spacing, typography, colors, borders,
    effects, filters, transforms, transitions, interactivity, accessibility)
- Responsive variants (sm:, md:, lg:, xl:, 2xl:)
- State variants (hover:, focus:, active:, dark:, group-*, peer-*, etc.)
- Arbitrary values (w-[100px], text-[#1da1f2], [mask-type:luminance])
- Negative values (-mt-4, -translate-x-1/2)
- Important modifier (!text-red-500)

Configuration:
- tailwind.config.js / tailwind.config.ts / tailwind.config.mjs / tailwind.config.cjs
- content paths, theme.extend, darkMode, plugins, presets
- v4 CSS-first config (@import "tailwindcss", @theme, @source)

Design Tokens / Theme:
- Color palettes (custom + default), spacing scales, screen breakpoints
- Typography tokens, border radius, box shadow, animation
- v4 @theme CSS custom property tokens

Plugin Ecosystem:
- Official: @tailwindcss/typography, forms, aspect-ratio, container-queries
- Community: daisyUI, tailwindcss-animate, headlessui, flowbite, preline
- Custom: plugin(), plugin.withOptions(), addUtilities, addVariant, etc.
- v4: @plugin CSS directive

AST Support:
- Regex-based CSS/HTML/JSX/TSX parsing with full extraction
- Line number tracking for all extracted artifacts

LSP Support:
- Tailwind CSS IntelliSense integration via @tailwindcss/language-server
- Class name completion, hover documentation, linting/diagnostics
- Config file detection and custom class resolution

Part of CodeTrellis v4.35 - Tailwind CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Tailwind extractors
from .extractors.tailwind import (
    TailwindUtilityExtractor, TailwindUtilityInfo,
    TailwindApplyInfo, TailwindArbitraryInfo,
    TailwindComponentExtractor, TailwindComponentInfo,
    TailwindLayerInfo, TailwindDirectiveInfo,
    TailwindConfigExtractor, TailwindConfigInfo,
    TailwindContentPathInfo, TailwindPluginConfigInfo,
    TailwindThemeExtractor, TailwindThemeTokenInfo,
    TailwindColorInfo, TailwindScreenInfo,
    TailwindPluginExtractor, TailwindPluginInfo,
    TailwindCustomUtilityInfo, TailwindCustomVariantInfo,
)


@dataclass
class TailwindParseResult:
    """Complete parse result for a Tailwind CSS file or project."""
    file_path: str
    file_type: str = "css"  # css, config, template

    # Utility patterns
    apply_directives: List[TailwindApplyInfo] = field(default_factory=list)
    arbitrary_values: List[TailwindArbitraryInfo] = field(default_factory=list)
    tailwind_directives: List[str] = field(default_factory=list)
    screen_directives: List[str] = field(default_factory=list)
    theme_functions: List[str] = field(default_factory=list)

    # v4 features
    v4_utilities: List[Dict[str, Any]] = field(default_factory=list)
    v4_variants: List[Dict[str, Any]] = field(default_factory=list)
    v4_themes: List[Dict[str, Any]] = field(default_factory=list)
    v4_sources: List[Dict[str, Any]] = field(default_factory=list)
    v4_plugins: List[Dict[str, Any]] = field(default_factory=list)
    v4_configs: List[Dict[str, Any]] = field(default_factory=list)

    # Component patterns
    components: List[TailwindComponentInfo] = field(default_factory=list)
    layers: List[TailwindLayerInfo] = field(default_factory=list)
    all_directives: List[TailwindDirectiveInfo] = field(default_factory=list)
    layer_order: List[str] = field(default_factory=list)

    # Config
    config: Optional[TailwindConfigInfo] = None
    content_paths: List[TailwindContentPathInfo] = field(default_factory=list)
    config_plugins: List[TailwindPluginConfigInfo] = field(default_factory=list)

    # Theme / Design Tokens
    theme_tokens: List[TailwindThemeTokenInfo] = field(default_factory=list)
    colors: List[TailwindColorInfo] = field(default_factory=list)
    screens: List[TailwindScreenInfo] = field(default_factory=list)

    # Plugins
    plugins: List[TailwindPluginInfo] = field(default_factory=list)
    custom_utilities: List[TailwindCustomUtilityInfo] = field(default_factory=list)
    custom_variants: List[TailwindCustomVariantInfo] = field(default_factory=list)

    # Metadata
    version_detected: str = ""  # v1, v2, v3, v4
    detected_features: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)
    has_v4_features: bool = False


class EnhancedTailwindParser:
    """
    Enhanced Tailwind CSS parser that uses all extractors for comprehensive parsing.

    Detects Tailwind version, configuration patterns, and extracts all structured data
    from CSS files, config files, and template files using Tailwind.

    Framework detection supports:
    - Tailwind CSS v1.x through v4.x
    - PostCSS + Tailwind
    - Tailwind UI
    - Headless UI
    - daisyUI
    - Flowbite
    - Preline
    - NextUI
    - shadcn/ui (with Tailwind)
    - Radix + Tailwind
    - twin.macro (Tailwind-in-JS)
    - Windi CSS (Tailwind-compatible)
    - UnoCSS (Tailwind preset)
    """

    # Config file patterns
    CONFIG_FILE_PATTERNS = {
        'tailwind.config.js', 'tailwind.config.ts',
        'tailwind.config.mjs', 'tailwind.config.cjs',
    }

    # PostCSS config patterns (may reference Tailwind)
    POSTCSS_CONFIG_PATTERNS = {
        'postcss.config.js', 'postcss.config.cjs',
        'postcss.config.mjs', 'postcss.config.ts',
        '.postcssrc', '.postcssrc.json', '.postcssrc.yml',
    }

    # Tailwind detection patterns in CSS content
    TAILWIND_CSS_PATTERNS = re.compile(
        r'@tailwind\b|@apply\b|@config\b|@screen\b|@variants\b|'
        r'@responsive\b|@utility\b|@variant\b|@theme\b|@source\b|@plugin\b|'
        r'theme\(\s*["\']|@import\s+["\']tailwindcss["\']',
        re.MULTILINE
    )

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'tailwind_ui': re.compile(
            r'@headlessui/|@heroicons/|tailwindui\.com', re.MULTILINE),
        'daisyui': re.compile(
            r'daisyui|daisy-ui', re.MULTILINE),
        'flowbite': re.compile(
            r'flowbite', re.MULTILINE),
        'preline': re.compile(
            r'preline', re.MULTILINE),
        'nextui': re.compile(
            r'@nextui-org/', re.MULTILINE),
        'shadcn': re.compile(
            r'@/components/ui/|shadcn|class-variance-authority|clsx.*tailwind-merge',
            re.MULTILINE),
        'twin_macro': re.compile(
            r'twin\.macro|tw`|tw\s*\(', re.MULTILINE),
        'headlessui': re.compile(
            r'@headlessui/', re.MULTILINE),
        'radix_tailwind': re.compile(
            r'@radix-ui/.*tailwind|tailwindcss-radix', re.MULTILINE),
        'tailwind_animate': re.compile(
            r'tailwindcss-animate', re.MULTILINE),
        'tailwind_merge': re.compile(
            r'tailwind-merge|twMerge|twJoin', re.MULTILINE),
        'tailwind_variants': re.compile(
            r'tailwind-variants|tv\(', re.MULTILINE),
        'cva': re.compile(
            r'class-variance-authority|cva\(', re.MULTILINE),
    }

    # Tailwind v4 detection patterns
    V4_PATTERNS = re.compile(
        r'@import\s+["\']tailwindcss["\']|@theme\s*(?:inline\s*)?\{|'
        r'@utility\s+[\w-]+|@variant\s+[\w-]+|@source\s+["\']|@plugin\s+["\']',
        re.MULTILINE
    )

    # Version detection patterns
    V3_PATTERNS = re.compile(
        r'content\s*:\s*\[|@layer\s+(base|components|utilities)',
        re.MULTILINE
    )

    V2_PATTERNS = re.compile(
        r'purge\s*:\s*\[|mode\s*:\s*["\']jit["\']|darkMode\s*:',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.utility_extractor = TailwindUtilityExtractor()
        self.component_extractor = TailwindComponentExtractor()
        self.config_extractor = TailwindConfigExtractor()
        self.theme_extractor = TailwindThemeExtractor()
        self.plugin_extractor = TailwindPluginExtractor()

    def parse(self, content: str, file_path: str = "") -> TailwindParseResult:
        """Parse Tailwind CSS content using all extractors.

        Args:
            content: CSS/JS/TS source code string.
            file_path: Path to the source file.

        Returns:
            TailwindParseResult with all extracted data.
        """
        result = TailwindParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect file type
        result.file_type = self._detect_file_type(file_path)

        # 1. Utility extraction (from CSS files with @apply, @tailwind, etc.)
        if result.file_type in ('css', 'template'):
            utility_result = self.utility_extractor.extract(content, file_path)
            result.apply_directives = utility_result.get('apply_directives', [])
            result.arbitrary_values = utility_result.get('arbitrary_values', [])
            result.tailwind_directives = utility_result.get('tailwind_directives', [])
            result.screen_directives = utility_result.get('screen_directives', [])
            result.theme_functions = utility_result.get('theme_functions', [])
            result.v4_utilities = utility_result.get('v4_utilities', [])
            result.v4_variants = utility_result.get('v4_variants', [])
            result.v4_themes = utility_result.get('v4_themes', [])
            result.v4_sources = utility_result.get('v4_sources', [])
            result.v4_plugins = utility_result.get('v4_plugins', [])
            result.v4_configs = utility_result.get('v4_configs', [])

        # 2. Component extraction (from CSS files)
        if result.file_type == 'css':
            component_result = self.component_extractor.extract(content, file_path)
            result.components = component_result.get('components', [])
            result.layers = component_result.get('layers', [])
            result.all_directives = component_result.get('directives', [])
            result.layer_order = component_result.get('layer_order', [])

        # 3. Config extraction (from config files)
        if result.file_type == 'config':
            config_result = self.config_extractor.extract(content, file_path)
            result.config = config_result.get('config')
            result.content_paths = config_result.get('content_paths', [])
            result.config_plugins = config_result.get('plugins', [])

            # Also extract theme from config
            theme_result = self.theme_extractor.extract(content, file_path)
            result.theme_tokens = theme_result.get('tokens', [])
            result.colors = theme_result.get('colors', [])
            result.screens = theme_result.get('screens', [])

            # Plugin detection from config
            plugin_result = self.plugin_extractor.extract(content, file_path)
            result.plugins = plugin_result.get('plugins', [])
            result.custom_utilities = plugin_result.get('custom_utilities', [])
            result.custom_variants = plugin_result.get('custom_variants', [])

        # 4. v4 CSS-first config (also extract theme from CSS @theme blocks)
        if result.file_type == 'css' and self.V4_PATTERNS.search(content):
            theme_result = self.theme_extractor.extract(content, file_path)
            result.theme_tokens = theme_result.get('tokens', [])

        # Detect version and features
        result.version_detected = self._detect_version(content, result)
        # Compute has_v4_features BEFORE _detect_features so it can use it
        result.has_v4_features = bool(
            result.v4_utilities or result.v4_variants or
            result.v4_themes or result.v4_sources or
            result.v4_plugins or result.v4_configs
        )
        result.detected_features = self._detect_features(content, file_path, result)
        result.detected_frameworks = self._detect_frameworks(content, file_path)

        return result

    def is_tailwind_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file contains Tailwind CSS patterns.

        Args:
            content: File content.
            file_path: Path to the file.

        Returns:
            True if Tailwind patterns are detected.
        """
        if not content:
            return False

        # Config files
        fname = Path(file_path).name if file_path else ""
        if fname in self.CONFIG_FILE_PATTERNS:
            return True

        # CSS content with Tailwind directives
        if self.TAILWIND_CSS_PATTERNS.search(content):
            return True

        return False

    def _detect_file_type(self, file_path: str) -> str:
        """Detect the type of Tailwind file."""
        if not file_path:
            return 'css'

        fname = Path(file_path).name
        ext = Path(file_path).suffix.lower()

        # Config files
        if fname in self.CONFIG_FILE_PATTERNS:
            return 'config'

        # CSS/SCSS/PostCSS
        if ext in ('.css', '.scss', '.sass', '.less', '.pcss', '.postcss'):
            return 'css'

        # Template files (for class extraction)
        if ext in ('.html', '.htm', '.jsx', '.tsx', '.vue', '.svelte',
                   '.blade.php', '.erb', '.ejs', '.hbs', '.njk', '.astro'):
            return 'template'

        # JS/TS (could be config or plugin)
        if ext in ('.js', '.ts', '.mjs', '.cjs'):
            return 'config'

        return 'css'

    def _detect_version(self, content: str, result: TailwindParseResult) -> str:
        """Detect the Tailwind CSS version from content patterns."""
        # v4 features
        if self.V4_PATTERNS.search(content):
            return 'v4'

        # v3 features (content array, @layer)
        if self.V3_PATTERNS.search(content):
            return 'v3'

        # v2 features (purge, JIT, darkMode)
        if self.V2_PATTERNS.search(content):
            return 'v2'

        # Config-based detection
        if result.config and result.config.version_detected:
            return result.config.version_detected

        # Default for files with Tailwind directives
        if result.tailwind_directives:
            return 'v3'

        return ''

    def _detect_features(self, content: str, file_path: str,
                        result: TailwindParseResult) -> List[str]:
        """Detect Tailwind features used in the file."""
        features: Set[str] = set()

        # Directives
        if result.tailwind_directives:
            features.add('tailwind_directives')
        if result.apply_directives:
            features.add('apply_directive')
        if result.screen_directives:
            features.add('screen_directive')
        if result.arbitrary_values:
            features.add('arbitrary_values')
        if result.theme_functions:
            features.add('theme_function')

        # v4 features
        if result.has_v4_features:
            features.add('v4_css_first')
        if result.v4_utilities:
            features.add('v4_utility_directive')
        if result.v4_variants:
            features.add('v4_variant_directive')
        if result.v4_themes:
            features.add('v4_theme_directive')
        if result.v4_sources:
            features.add('v4_source_directive')

        # Layers
        if result.layers:
            features.add('layer_directive')
            layer_names = set(l.name for l in result.layers)
            if 'components' in layer_names:
                features.add('component_layer')
            if 'utilities' in layer_names:
                features.add('utility_layer')
            if 'base' in layer_names:
                features.add('base_layer')

        # Components
        if result.components:
            features.add('component_composition')

        # Config features
        if result.config:
            if result.config.dark_mode:
                features.add(f'dark_mode_{result.config.dark_mode}')
            if result.config.prefix:
                features.add('custom_prefix')
            if result.config.important:
                features.add('important_config')
            if result.config.presets:
                features.add('presets')

        # Plugins
        if result.plugins:
            for p in result.plugins:
                if p.is_official:
                    features.add(f'plugin_{p.name}')

        # Content patterns
        if '@tailwind base' in content or 'base' in result.tailwind_directives:
            features.add('base_styles')
        if '@tailwind components' in content or 'components' in result.tailwind_directives:
            features.add('components_layer')
        if '@tailwind utilities' in content or 'utilities' in result.tailwind_directives:
            features.add('utilities_layer')

        # Dark mode in CSS
        if 'dark:' in content:
            features.add('dark_mode')

        # Responsive utilities in CSS
        for variant in ('sm:', 'md:', 'lg:', 'xl:', '2xl:'):
            if variant in content:
                features.add('responsive_utilities')
                break

        return sorted(features)

    def _detect_frameworks(self, content: str, file_path: str) -> List[str]:
        """Detect Tailwind ecosystem frameworks and libraries."""
        frameworks: Set[str] = set()

        frameworks.add('tailwind')

        for fw_name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.add(fw_name)

        return sorted(frameworks)
