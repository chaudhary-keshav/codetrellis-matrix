"""
PostCSS Plugin Extractor for CodeTrellis

Extracts PostCSS plugin declarations, configurations, and usage patterns
from JavaScript/TypeScript config files and CSS source files.

Supports:
- Plugin require/import patterns (require('autoprefixer'), import cssnano from 'cssnano')
- Plugin function calls (autoprefixer(), cssnano({ preset: 'default' }))
- Plugin options extraction
- 100+ known PostCSS plugins across categories:
  - Future CSS: postcss-preset-env, postcss-custom-properties, postcss-nesting
  - Optimization: cssnano, postcss-merge-rules, postcss-discard-comments
  - Utilities: autoprefixer, postcss-pxtorem, postcss-flexbugs-fixes
  - Linting: stylelint, postcss-reporter
  - Syntax: postcss-scss, postcss-less, postcss-html, sugarss
  - Modules: postcss-modules, css-modules-flow-types
  - Naming: postcss-bem-linter, postcss-bem
  - Typography: postcss-font-magician, postcss-responsive-type
  - Color: postcss-color-function, postcss-color-mod-function
  - Media: postcss-custom-media, postcss-media-minmax

Part of CodeTrellis v4.46 — PostCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PostCSSPluginInfo:
    """Information about a PostCSS plugin."""
    name: str
    package_name: str = ""        # npm package name
    category: str = ""             # future_css, optimization, utility, linting, syntax, etc.
    has_options: bool = False
    options_summary: str = ""      # Brief description of configured options
    import_style: str = ""         # require, import, inline
    is_builtin: bool = False       # Built into postcss-preset-env or similar
    version_constraint: str = ""   # Detected version constraint if any
    file: str = ""
    line_number: int = 0


# Known PostCSS plugins categorized
KNOWN_PLUGINS: Dict[str, Dict[str, str]] = {
    # Future CSS / Spec Compliance
    "postcss-preset-env": {"category": "future_css", "desc": "Future CSS features polyfill"},
    "postcss-custom-properties": {"category": "future_css", "desc": "CSS custom properties fallback"},
    "postcss-nesting": {"category": "future_css", "desc": "CSS nesting spec"},
    "postcss-custom-media": {"category": "future_css", "desc": "Custom media queries"},
    "postcss-custom-selectors": {"category": "future_css", "desc": "Custom selectors"},
    "postcss-color-function": {"category": "future_css", "desc": "CSS color() function"},
    "postcss-color-mod-function": {"category": "future_css", "desc": "color-mod() function"},
    "postcss-logical": {"category": "future_css", "desc": "Logical properties/values"},
    "postcss-dir-pseudo-class": {"category": "future_css", "desc": ":dir() pseudo-class"},
    "postcss-env-function": {"category": "future_css", "desc": "env() function"},
    "postcss-focus-visible": {"category": "future_css", "desc": ":focus-visible polyfill"},
    "postcss-focus-within": {"category": "future_css", "desc": ":focus-within polyfill"},
    "postcss-gap-properties": {"category": "future_css", "desc": "gap shorthand fallback"},
    "postcss-image-set-function": {"category": "future_css", "desc": "image-set() function"},
    "postcss-lab-function": {"category": "future_css", "desc": "lab() / lch() functions"},
    "postcss-overflow-shorthand": {"category": "future_css", "desc": "overflow shorthand"},
    "postcss-place": {"category": "future_css", "desc": "place-* properties"},
    "postcss-is-pseudo-class": {"category": "future_css", "desc": ":is() pseudo-class"},
    "postcss-cascade-layers": {"category": "future_css", "desc": "@layer cascade layers"},
    "postcss-double-position-gradients": {"category": "future_css", "desc": "Double-position gradient"},
    "postcss-oklab-function": {"category": "future_css", "desc": "oklab()/oklch() functions"},
    "postcss-trigonometric-functions": {"category": "future_css", "desc": "sin()/cos()/tan()"},
    "postcss-media-minmax": {"category": "future_css", "desc": "Media query ranges"},
    "postcss-selector-not": {"category": "future_css", "desc": ":not() list argument"},
    "postcss-initial": {"category": "future_css", "desc": "initial keyword fallback"},
    "postcss-pseudo-class-any-link": {"category": "future_css", "desc": ":any-link polyfill"},
    "postcss-attribute-case-insensitive": {"category": "future_css", "desc": "Case-insensitive attrs"},
    "postcss-clamp": {"category": "future_css", "desc": "clamp() function fallback"},
    "postcss-font-variant": {"category": "future_css", "desc": "font-variant shorthand"},
    "postcss-hwb-function": {"category": "future_css", "desc": "hwb() function"},
    "postcss-color-hex-alpha": {"category": "future_css", "desc": "#RRGGBBAA hex colors"},
    "postcss-color-rebeccapurple": {"category": "future_css", "desc": "rebeccapurple color"},
    "postcss-has-pseudo": {"category": "future_css", "desc": ":has() pseudo-class"},
    "postcss-normalize-display-values": {"category": "future_css", "desc": "Two-value display"},
    "postcss-stepped-value-functions": {"category": "future_css", "desc": "round()/mod()/rem()"},
    "postcss-unset-value": {"category": "future_css", "desc": "unset keyword fallback"},

    # Optimization / Minification
    "cssnano": {"category": "optimization", "desc": "CSS minifier & optimizer"},
    "postcss-merge-rules": {"category": "optimization", "desc": "Merge adjacent rules"},
    "postcss-discard-comments": {"category": "optimization", "desc": "Remove comments"},
    "postcss-discard-duplicates": {"category": "optimization", "desc": "Remove duplicates"},
    "postcss-discard-empty": {"category": "optimization", "desc": "Remove empty rules"},
    "postcss-discard-overridden": {"category": "optimization", "desc": "Remove overridden at-rules"},
    "postcss-merge-longhand": {"category": "optimization", "desc": "Merge longhand to shorthand"},
    "postcss-minify-font-values": {"category": "optimization", "desc": "Minify font values"},
    "postcss-minify-gradients": {"category": "optimization", "desc": "Minify gradient values"},
    "postcss-minify-params": {"category": "optimization", "desc": "Minify at-rule params"},
    "postcss-minify-selectors": {"category": "optimization", "desc": "Minify selectors"},
    "postcss-normalize-charset": {"category": "optimization", "desc": "Normalize @charset"},
    "postcss-normalize-positions": {"category": "optimization", "desc": "Normalize positions"},
    "postcss-normalize-repeat-style": {"category": "optimization", "desc": "Normalize repeat"},
    "postcss-normalize-string": {"category": "optimization", "desc": "Normalize string quotes"},
    "postcss-normalize-timing-functions": {"category": "optimization", "desc": "Normalize easing"},
    "postcss-normalize-unicode": {"category": "optimization", "desc": "Normalize unicode-range"},
    "postcss-normalize-url": {"category": "optimization", "desc": "Normalize URLs"},
    "postcss-normalize-whitespace": {"category": "optimization", "desc": "Normalize whitespace"},
    "postcss-ordered-values": {"category": "optimization", "desc": "Sort values consistently"},
    "postcss-reduce-initial": {"category": "optimization", "desc": "Reduce initial keyword"},
    "postcss-reduce-transforms": {"category": "optimization", "desc": "Reduce transform values"},
    "postcss-svgo": {"category": "optimization", "desc": "Optimize inline SVG"},
    "postcss-unique-selectors": {"category": "optimization", "desc": "Deduplicate selectors"},
    "postcss-calc": {"category": "optimization", "desc": "Reduce calc() expressions"},
    "postcss-zindex": {"category": "optimization", "desc": "Rebase z-index values"},
    "postcss-sort-media-queries": {"category": "optimization", "desc": "Sort media queries"},
    "@fullhuman/postcss-purgecss": {"category": "optimization", "desc": "Remove unused CSS"},
    "postcss-uncss": {"category": "optimization", "desc": "Remove unused CSS"},

    # Utilities
    "autoprefixer": {"category": "utility", "desc": "Add vendor prefixes"},
    "postcss-pxtorem": {"category": "utility", "desc": "px to rem conversion"},
    "postcss-px-to-viewport": {"category": "utility", "desc": "px to viewport units"},
    "postcss-flexbugs-fixes": {"category": "utility", "desc": "Flexbox bug fixes"},
    "postcss-100vh-fix": {"category": "utility", "desc": "100vh fix for mobile"},
    "postcss-normalize": {"category": "utility", "desc": "CSS normalize/reset"},
    "postcss-import": {"category": "utility", "desc": "Inline @import rules"},
    "postcss-url": {"category": "utility", "desc": "Rebase/inline/copy URLs"},
    "postcss-assets": {"category": "utility", "desc": "Asset management"},
    "postcss-copy": {"category": "utility", "desc": "Copy referenced assets"},
    "postcss-inline-svg": {"category": "utility", "desc": "Inline SVG files"},
    "postcss-responsive-type": {"category": "utility", "desc": "Responsive typography"},
    "postcss-font-magician": {"category": "utility", "desc": "Auto @font-face"},
    "postcss-utilities": {"category": "utility", "desc": "Utility mixins"},
    "postcss-simple-vars": {"category": "utility", "desc": "Sass-like variables"},
    "postcss-mixins": {"category": "utility", "desc": "Sass-like mixins"},
    "postcss-nested": {"category": "utility", "desc": "Sass-like nesting"},
    "postcss-extend": {"category": "utility", "desc": "Sass-like @extend"},
    "postcss-extend-rule": {"category": "utility", "desc": "@extend rule"},
    "postcss-each": {"category": "utility", "desc": "@each iteration"},
    "postcss-for": {"category": "utility", "desc": "@for iteration"},
    "postcss-conditionals": {"category": "utility", "desc": "@if/@else conditionals"},
    "postcss-define-property": {"category": "utility", "desc": "Define custom properties"},
    "postcss-property-lookup": {"category": "utility", "desc": "Reference other properties"},
    "postcss-size": {"category": "utility", "desc": "size shorthand"},
    "postcss-aspect-ratio": {"category": "utility", "desc": "Aspect ratio shorthand"},
    "postcss-autoreset": {"category": "utility", "desc": "Auto CSS reset"},
    "postcss-short": {"category": "utility", "desc": "Shorthand properties"},
    "postcss-easings": {"category": "utility", "desc": "Named easing functions"},
    "postcss-will-change": {"category": "utility", "desc": "Auto will-change"},
    "postcss-hexrgba": {"category": "utility", "desc": "RGBA from hex"},
    "postcss-selector-matches": {"category": "utility", "desc": ":matches() polyfill"},
    "postcss-apply": {"category": "utility", "desc": "@apply custom property sets"},
    "postcss-rtlcss": {"category": "utility", "desc": "RTL CSS generation"},
    "postcss-rtl": {"category": "utility", "desc": "RTL CSS alternative"},

    # Linting / Analysis
    "stylelint": {"category": "linting", "desc": "CSS linter"},
    "postcss-reporter": {"category": "linting", "desc": "Log PostCSS messages"},
    "postcss-browser-reporter": {"category": "linting", "desc": "Browser error overlay"},
    "postcss-bem-linter": {"category": "linting", "desc": "BEM convention linter"},
    "doiuse": {"category": "linting", "desc": "Browser support linter"},

    # Custom Syntax / Parsers
    "postcss-scss": {"category": "syntax", "desc": "SCSS syntax parser"},
    "postcss-less": {"category": "syntax", "desc": "Less syntax parser"},
    "postcss-html": {"category": "syntax", "desc": "HTML/Vue/Svelte/PHP parser"},
    "postcss-markdown": {"category": "syntax", "desc": "Markdown embedded CSS"},
    "postcss-jsx": {"category": "syntax", "desc": "JSX/TSX CSS-in-JS parser"},
    "postcss-styled-syntax": {"category": "syntax", "desc": "Tagged template literal"},
    "postcss-syntax": {"category": "syntax", "desc": "Auto-detect syntax"},
    "sugarss": {"category": "syntax", "desc": "Indent-based CSS syntax"},
    "postcss-safe-parser": {"category": "syntax", "desc": "Fault-tolerant CSS parser"},
    "postcss-comment": {"category": "syntax", "desc": "// comment support"},
    "postcss-strip-inline-comments": {"category": "syntax", "desc": "Strip // comments"},

    # CSS Modules
    "postcss-modules": {"category": "modules", "desc": "CSS Modules scoping"},
    "postcss-icss-values": {"category": "modules", "desc": "ICSS :import/:export"},
    "postcss-icss-selectors": {"category": "modules", "desc": "ICSS selector scoping"},
    "postcss-icss-composes": {"category": "modules", "desc": "ICSS composes"},
    "css-modules-flow-types": {"category": "modules", "desc": "Flow types for CSS Modules"},

    # Framework integrations
    "tailwindcss": {"category": "framework", "desc": "Tailwind CSS utility framework"},
    "@tailwindcss/nesting": {"category": "framework", "desc": "Tailwind nesting plugin"},
    "@tailwindcss/typography": {"category": "framework", "desc": "Tailwind typography"},
    "@tailwindcss/forms": {"category": "framework", "desc": "Tailwind form styles"},
    "@tailwindcss/container-queries": {"category": "framework", "desc": "Container queries"},
    "@tailwindcss/aspect-ratio": {"category": "framework", "desc": "Aspect ratio"},
    "postcss-windicss": {"category": "framework", "desc": "Windi CSS integration"},
}


class PostCSSPluginExtractor:
    """
    Extracts PostCSS plugin declarations from config files and source.

    Detects:
    - require('plugin-name') patterns
    - import plugin from 'plugin-name' patterns
    - Plugin function calls in config arrays
    - Plugin options/configuration
    - Known vs unknown plugins
    """

    # require('postcss-*') or require("postcss-*")
    REQUIRE_PATTERN = re.compile(
        r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""",
        re.MULTILINE
    )

    # import ... from 'postcss-*'
    IMPORT_PATTERN = re.compile(
        r"""import\s+(?:\{[^}]+\}|(\w+))\s+from\s+['"]([^'"]+)['"]""",
        re.MULTILINE
    )

    # Dynamic import: const x = require('postcss-*')
    CONST_REQUIRE_PATTERN = re.compile(
        r"""(?:const|let|var)\s+(\w+)\s*=\s*require\s*\(\s*['"]([^'"]+)['"]\s*\)""",
        re.MULTILINE
    )

    # Plugin in config array: 'postcss-import' or "autoprefixer"
    CONFIG_STRING_PLUGIN = re.compile(
        r"""['"]([a-z@][a-z0-9_./@-]*)['"]""",
        re.MULTILINE | re.IGNORECASE
    )

    # Plugin function call: autoprefixer({ ... }) or cssnano()
    PLUGIN_CALL_PATTERN = re.compile(
        r"""(\w+)\s*\(\s*(?:\{[^}]*\}|[^)]*)\s*\)""",
        re.MULTILINE
    )

    # package.json postcss plugins section
    PACKAGE_JSON_POSTCSS = re.compile(
        r'"postcss"\s*:\s*\{[^}]*"plugins"\s*:\s*\{([^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    def __init__(self):
        """Initialize the plugin extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract PostCSS plugin information from source content.

        Args:
            content: Source code content (JS/TS config or package.json).
            file_path: Path to source file.

        Returns:
            Dict with 'plugins' list and 'stats' dict.
        """
        plugins: List[PostCSSPluginInfo] = []
        seen_names: set = set()

        # Extract from require() calls
        for match in self.REQUIRE_PATTERN.finditer(content):
            pkg_name = match.group(1)
            if self._is_postcss_related(pkg_name) and pkg_name not in seen_names:
                seen_names.add(pkg_name)
                info = self._create_plugin_info(pkg_name, 'require', content, match, file_path)
                plugins.append(info)

        # Extract from import statements
        for match in self.IMPORT_PATTERN.finditer(content):
            pkg_name = match.group(2)
            if self._is_postcss_related(pkg_name) and pkg_name not in seen_names:
                seen_names.add(pkg_name)
                info = self._create_plugin_info(pkg_name, 'import', content, match, file_path)
                plugins.append(info)

        # Extract from const/let/var = require()
        for match in self.CONST_REQUIRE_PATTERN.finditer(content):
            pkg_name = match.group(2)
            if self._is_postcss_related(pkg_name) and pkg_name not in seen_names:
                seen_names.add(pkg_name)
                info = self._create_plugin_info(pkg_name, 'require', content, match, file_path)
                plugins.append(info)

        # Extract from package.json postcss section
        if 'postcss' in file_path.lower() or file_path.endswith('package.json'):
            for match in self.PACKAGE_JSON_POSTCSS.finditer(content):
                plugins_section = match.group(1)
                for plugin_match in self.CONFIG_STRING_PLUGIN.finditer(plugins_section):
                    pkg_name = plugin_match.group(1)
                    if pkg_name not in seen_names:
                        seen_names.add(pkg_name)
                        info = self._create_plugin_info(pkg_name, 'config', content, match, file_path)
                        plugins.append(info)

        # Extract from string literals in config arrays (plugins: ['autoprefixer'])
        if self._is_postcss_config(file_path):
            for match in self.CONFIG_STRING_PLUGIN.finditer(content):
                pkg_name = match.group(1)
                if self._is_postcss_related(pkg_name) and pkg_name not in seen_names:
                    seen_names.add(pkg_name)
                    info = self._create_plugin_info(pkg_name, 'config', content, match, file_path)
                    plugins.append(info)

        # Stats
        stats = {
            "total_plugins": len(plugins),
            "categories": list(set(p.category for p in plugins if p.category)),
            "has_optimization": any(p.category == "optimization" for p in plugins),
            "has_future_css": any(p.category == "future_css" for p in plugins),
            "has_linting": any(p.category == "linting" for p in plugins),
            "has_syntax": any(p.category == "syntax" for p in plugins),
            "has_modules": any(p.category == "modules" for p in plugins),
            "has_framework": any(p.category == "framework" for p in plugins),
        }

        return {"plugins": plugins, "stats": stats}

    def _is_postcss_related(self, name: str) -> bool:
        """Check if a package name is PostCSS-related."""
        if name in KNOWN_PLUGINS:
            return True
        postcss_prefixes = ('postcss-', 'postcss_', '@postcss/', 'css', 'autoprefixer',
                           'cssnano', 'stylelint', 'sugarss', 'tailwindcss',
                           '@tailwindcss/', '@fullhuman/postcss-')
        return any(name.startswith(p) or name == p for p in postcss_prefixes)

    def _is_postcss_config(self, file_path: str) -> bool:
        """Check if file is a PostCSS config file."""
        config_names = (
            'postcss.config.js', 'postcss.config.cjs', 'postcss.config.mjs',
            'postcss.config.ts', 'postcss.config.cts', 'postcss.config.mts',
            '.postcssrc', '.postcssrc.js', '.postcssrc.cjs', '.postcssrc.mjs',
            '.postcssrc.json', '.postcssrc.yaml', '.postcssrc.yml',
        )
        return any(file_path.endswith(n) for n in config_names)

    def _create_plugin_info(self, pkg_name: str, import_style: str,
                           content: str, match: re.Match,
                           file_path: str) -> PostCSSPluginInfo:
        """Create a PostCSSPluginInfo from match data."""
        known = KNOWN_PLUGINS.get(pkg_name, {})
        line_number = content[:match.start()].count('\n') + 1

        # Check for options (look for function call with object arg nearby)
        has_options = bool(re.search(
            re.escape(pkg_name.split('/')[-1].replace('-', '_').replace('postcss_', '').replace('postcss-', ''))
            + r'\s*\(\s*\{',
            content
        )) if pkg_name else False

        return PostCSSPluginInfo(
            name=known.get('desc', pkg_name) if known else pkg_name,
            package_name=pkg_name,
            category=known.get('category', ''),
            has_options=has_options,
            import_style=import_style,
            is_builtin=False,
            file=file_path,
            line_number=line_number,
        )
