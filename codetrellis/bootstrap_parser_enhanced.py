"""
EnhancedBootstrapParser v1.0 - Comprehensive Bootstrap parser using all extractors.

This parser integrates all Bootstrap extractors to provide complete parsing of
Bootstrap usage across HTML, CSS/SCSS, JavaScript/TypeScript, and JSX/TSX files.
It runs as a supplementary layer on top of language-specific parsers when
Bootstrap framework is detected.

Supports:
- Bootstrap v3.x (jQuery-based, 4-tier grid, panels/wells/glyphicons)
- Bootstrap v4.x (flexbox grid, cards, utility-first, jQuery plugins)
- Bootstrap v5.x (vanilla JS, 6-tier grid, RTL support, CSS custom properties,
    color modes, expanded utilities, updated forms, offcanvas)
- Bootstrap v5.3+ (color modes via data-bs-theme, dark mode, focus ring utilities,
    link utilities, icon link, new z-index utilities)

Component Detection:
- 50+ Bootstrap components across 8 categories (layout, forms, data-display,
    feedback, navigation, overlay, disclosure, content/utility)
- React-Bootstrap components (react-bootstrap, reactstrap)
- Angular Bootstrap (ng-bootstrap, ngx-bootstrap)
- Vue Bootstrap (bootstrap-vue, bootstrap-vue-next)
- Data-attribute initialization (data-bs-toggle, data-bs-target)
- jQuery plugin initialization ($().modal(), .tooltip(), etc.)
- Vanilla JS initialization (new bootstrap.Modal(), etc.)

Grid System:
- Container types (fixed, fluid, responsive per-breakpoint)
- Row/Col with responsive breakpoints (xs, sm, md, lg, xl, xxl)
- Gutters (g-*, gx-*, gy-*), Row-cols, Ordering, Offsets
- CSS Grid option (Bootstrap 5.1+)
- Nested grids

Theme System:
- SCSS variable overrides ($primary, $body-bg, $font-family-base, etc.)
- CSS custom properties (--bs-primary, --bs-body-font-family, etc.)
- Bootswatch themes (26+ themes)
- Bootstrap 5.3+ color modes (data-bs-theme, prefers-color-scheme)
- Enable/disable flags ($enable-rounded, $enable-shadows, etc.)

Utility Classes:
- Spacing (m-*, p-*), Display (d-*), Flex (flex-*, justify-content-*, align-items-*)
- Sizing (w-*, h-*), Colors (text-*, bg-*), Borders, Rounded, Shadow
- Position, Overflow, Opacity, Z-index, Object-fit, Float, Visibility
- Responsive variants for all utility categories

JavaScript Plugins:
- Alert, Button, Carousel, Collapse, Dropdown, Modal
- Offcanvas, Popover, ScrollSpy, Tab, Toast, Tooltip
- Event listeners (show.bs.*, shown.bs.*, hide.bs.*, hidden.bs.*)
- CDN/npm package detection

Framework Ecosystem Detection (20+ patterns):
- Core: bootstrap, bootstrap/dist/css, bootstrap/dist/js
- React: react-bootstrap, reactstrap
- Angular: @ng-bootstrap/ng-bootstrap, ngx-bootstrap
- Vue: bootstrap-vue, bootstrap-vue-next, bootstrap-vue-3
- Icons: bootstrap-icons, @fortawesome/fontawesome-free
- Themes: bootswatch
- Build: @popperjs/core, sass, postcss, autoprefixer
- Companion: jquery, @popperjs/core, popper.js

Optional AST support via tree-sitter-javascript / tree-sitter-html.
Optional LSP support via typescript-language-server (tsserver) / html-languageserver.

Part of CodeTrellis v4.40 - Bootstrap Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Bootstrap extractors
from .extractors.bootstrap import (
    BootstrapComponentExtractor, BootstrapComponentInfo,
    BootstrapCustomComponentInfo,
    BootstrapGridExtractor, BootstrapGridInfo, BootstrapBreakpointInfo,
    BootstrapThemeExtractor, BootstrapThemeInfo, BootstrapVariableInfo,
    BootstrapColorModeInfo,
    BootstrapUtilityExtractor, BootstrapUtilityInfo, BootstrapUtilitySummary,
    BootstrapPluginExtractor, BootstrapPluginInfo, BootstrapEventInfo,
    BootstrapCDNInfo,
)


@dataclass
class BootstrapParseResult:
    """Complete parse result for a file with Bootstrap usage."""
    file_path: str
    file_type: str = "html"  # html, jsx, tsx, js, ts, scss, css

    # Components
    components: List[BootstrapComponentInfo] = field(default_factory=list)
    custom_components: List[BootstrapCustomComponentInfo] = field(default_factory=list)

    # Grid
    grids: List[BootstrapGridInfo] = field(default_factory=list)
    breakpoints: List[BootstrapBreakpointInfo] = field(default_factory=list)

    # Theme
    themes: List[BootstrapThemeInfo] = field(default_factory=list)
    variables: List[BootstrapVariableInfo] = field(default_factory=list)
    color_modes: List[BootstrapColorModeInfo] = field(default_factory=list)

    # Utilities
    utilities: List[BootstrapUtilityInfo] = field(default_factory=list)
    utility_summary: List[BootstrapUtilitySummary] = field(default_factory=list)

    # Plugins / JS
    plugins: List[BootstrapPluginInfo] = field(default_factory=list)
    events: List[BootstrapEventInfo] = field(default_factory=list)
    cdn_includes: List[BootstrapCDNInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    bootstrap_version: str = ""
    has_grid: bool = False
    has_custom_theme: bool = False
    has_dark_mode: bool = False
    has_responsive: bool = False
    has_js_plugins: bool = False
    has_utilities: bool = False
    has_react_bootstrap: bool = False
    has_bootswatch: bool = False
    detected_features: List[str] = field(default_factory=list)


class EnhancedBootstrapParser:
    """
    Enhanced Bootstrap parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER language-specific parsers when Bootstrap
    framework is detected. It extracts Bootstrap-specific semantics that language
    parsers cannot capture.

    Framework detection supports 20+ Bootstrap ecosystem patterns across:
    - Core (bootstrap, bootstrap/dist/css, bootstrap/dist/js)
    - React (react-bootstrap, reactstrap)
    - Angular (@ng-bootstrap/ng-bootstrap, ngx-bootstrap)
    - Vue (bootstrap-vue, bootstrap-vue-next)
    - Icons (bootstrap-icons, @fortawesome/fontawesome-free)
    - Themes (bootswatch)
    - Build (@popperjs/core, sass, autoprefixer)

    Optional AST: tree-sitter-javascript / tree-sitter-html
    Optional LSP: typescript-language-server / html-languageserver
    """

    # Bootstrap ecosystem framework / library detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core Bootstrap ────────────────────────────────────────
        'bootstrap': re.compile(
            r"from\s+['\"]bootstrap['/\"]|"
            r"require\(['\"]bootstrap['/\"]\)|"
            r"import\s+['\"]bootstrap(?:/dist)?/(?:css|js)/bootstrap",
            re.MULTILINE
        ),
        'bootstrap-css': re.compile(
            r"bootstrap(?:\.min)?\.css|"
            r"href=['\"][^'\"]*bootstrap[^'\"]*\.css['\"]",
            re.MULTILINE | re.IGNORECASE
        ),
        'bootstrap-js': re.compile(
            r"bootstrap(?:\.bundle)?(?:\.min)?\.js|"
            r"src=['\"][^'\"]*bootstrap[^'\"]*\.js['\"]",
            re.MULTILINE | re.IGNORECASE
        ),

        # ── React Bootstrap ───────────────────────────────────────
        'react-bootstrap': re.compile(
            r"from\s+['\"]react-bootstrap['/\"]|"
            r"require\(['\"]react-bootstrap['/\"]\)",
            re.MULTILINE
        ),
        'reactstrap': re.compile(
            r"from\s+['\"]reactstrap['/\"]|"
            r"require\(['\"]reactstrap['/\"]\)",
            re.MULTILINE
        ),

        # ── Angular Bootstrap ─────────────────────────────────────
        'ng-bootstrap': re.compile(
            r"from\s+['\"]@ng-bootstrap/ng-bootstrap['/\"]|"
            r"NgbModule",
            re.MULTILINE
        ),
        'ngx-bootstrap': re.compile(
            r"from\s+['\"]ngx-bootstrap['/\"]|"
            r"BsModalService|BsDropdownDirective",
            re.MULTILINE
        ),

        # ── Vue Bootstrap ─────────────────────────────────────────
        'bootstrap-vue': re.compile(
            r"from\s+['\"]bootstrap-vue['/\"]|"
            r"from\s+['\"]bootstrap-vue-next['/\"]|"
            r"from\s+['\"]bootstrap-vue-3['/\"]|"
            r"BootstrapVue",
            re.MULTILINE
        ),

        # ── Icons ─────────────────────────────────────────────────
        'bootstrap-icons': re.compile(
            r"from\s+['\"]bootstrap-icons['/\"]|"
            r"bi-\w+|bootstrap-icons",
            re.MULTILINE
        ),
        'fontawesome': re.compile(
            r"from\s+['\"]@fortawesome/|"
            r"fa-\w+\b|font-awesome",
            re.MULTILINE
        ),

        # ── Themes ────────────────────────────────────────────────
        'bootswatch': re.compile(
            r"bootswatch|from\s+['\"]bootswatch",
            re.MULTILINE | re.IGNORECASE
        ),

        # ── Build Tools ───────────────────────────────────────────
        'popper': re.compile(
            r"from\s+['\"]@popperjs/core['/\"]|"
            r"from\s+['\"]popper\.js['/\"]|"
            r"Popper\.",
            re.MULTILINE
        ),
        'sass': re.compile(
            r"@import\s+['\"].*bootstrap.*['\"]|"
            r"@use\s+['\"].*bootstrap.*['\"]",
            re.MULTILINE
        ),

        # ── jQuery ────────────────────────────────────────────────
        'jquery': re.compile(
            r"from\s+['\"]jquery['/\"]|"
            r"require\(['\"]jquery['/\"]\)|"
            r"\$\(|jQuery\(",
            re.MULTILINE
        ),

        # ── CDN ───────────────────────────────────────────────────
        'bootstrap-cdn': re.compile(
            r"cdn\.jsdelivr\.net/npm/bootstrap|"
            r"cdnjs\.cloudflare\.com/ajax/libs/bootstrap|"
            r"stackpath\.bootstrapcdn\.com|"
            r"maxcdn\.bootstrapcdn\.com",
            re.MULTILINE | re.IGNORECASE
        ),
    }

    # Bootstrap version detection indicators
    BOOTSTRAP_VERSION_INDICATORS = {
        # v5 indicators
        'data-bs-toggle': 'v5', 'data-bs-target': 'v5',
        'data-bs-dismiss': 'v5', 'data-bs-theme': 'v5',
        'new bootstrap.': 'v5',
        'bootstrap.Modal': 'v5', 'bootstrap.Toast': 'v5',
        'bootstrap.Tooltip': 'v5', 'bootstrap.Popover': 'v5',
        'bootstrap.Carousel': 'v5', 'bootstrap.Collapse': 'v5',
        'bootstrap.Dropdown': 'v5', 'bootstrap.Offcanvas': 'v5',
        'offcanvas': 'v5',
        'col-xxl-': 'v5',
        '--bs-': 'v5',
        'form-floating': 'v5',
        'vstack': 'v5', 'hstack': 'v5',

        # v5.3 indicators
        'data-bs-theme="dark"': 'v5.3',
        'data-bs-theme="light"': 'v5.3',
        'color-mode': 'v5.3',
        'icon-link': 'v5.3',
        'focus-ring': 'v5.3',

        # v4 indicators
        'data-toggle': 'v4', 'data-target': 'v4',
        'data-dismiss': 'v4', 'data-backdrop': 'v4',
        'badge-pill': 'v4', 'card-deck': 'v4',
        'form-row': 'v4', 'custom-select': 'v4',
        'custom-checkbox': 'v4', 'custom-radio': 'v4',

        # v3 indicators
        'col-xs-': 'v3', 'panel': 'v3', 'well': 'v3',
        'glyphicon': 'v3', 'label-default': 'v3',
        'img-responsive': 'v3', 'btn-default': 'v3',
        'panel-heading': 'v3', 'panel-body': 'v3',
        'text-justify': 'v3', 'pull-left': 'v3', 'pull-right': 'v3',
    }

    VERSION_PRIORITY = {'v5.3': 53, 'v5': 50, 'v4': 40, 'v3': 30}

    def __init__(self):
        """Initialize the parser with all Bootstrap extractors."""
        self.component_extractor = BootstrapComponentExtractor()
        self.grid_extractor = BootstrapGridExtractor()
        self.theme_extractor = BootstrapThemeExtractor()
        self.utility_extractor = BootstrapUtilityExtractor()
        self.plugin_extractor = BootstrapPluginExtractor()

    def parse(self, content: str, file_path: str = "") -> BootstrapParseResult:
        """
        Parse source code and extract all Bootstrap-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            BootstrapParseResult with all extracted information
        """
        result = BootstrapParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        elif file_path.endswith('.ts'):
            result.file_type = "ts"
        elif file_path.endswith('.js'):
            result.file_type = "js"
        elif file_path.endswith(('.scss', '.sass')):
            result.file_type = "scss"
        elif file_path.endswith('.css'):
            result.file_type = "css"
        else:
            result.file_type = "html"

        # ── Detect frameworks ─────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract components ────────────────────────────────────
        comp_result = self.component_extractor.extract(content, file_path)
        result.components = comp_result.get('components', [])
        result.custom_components = comp_result.get('custom_components', [])

        # ── Extract grid ──────────────────────────────────────────
        grid_result = self.grid_extractor.extract(content, file_path)
        result.grids = grid_result.get('grids', [])
        result.breakpoints = grid_result.get('breakpoints', [])

        # ── Extract theme ─────────────────────────────────────────
        theme_result = self.theme_extractor.extract(content, file_path)
        result.themes = theme_result.get('themes', [])
        result.variables = theme_result.get('variables', [])
        result.color_modes = theme_result.get('color_modes', [])

        # ── Extract utilities ─────────────────────────────────────
        utility_result = self.utility_extractor.extract(content, file_path)
        result.utilities = utility_result.get('utilities', [])
        result.utility_summary = utility_result.get('summary', [])

        # ── Extract plugins/JS ────────────────────────────────────
        plugin_result = self.plugin_extractor.extract(content, file_path)
        result.plugins = plugin_result.get('plugins', [])
        result.events = plugin_result.get('events', [])
        result.cdn_includes = plugin_result.get('cdn_includes', [])

        # ── Compute metadata flags ────────────────────────────────
        result.has_grid = len(result.grids) > 0
        result.has_custom_theme = len(result.themes) > 0
        result.has_dark_mode = any(
            cm.mode == 'dark' or cm.mode == 'auto' for cm in result.color_modes
        )
        result.has_responsive = any(
            bp for bp in result.breakpoints
        ) or any(c.has_responsive for c in result.components)
        result.has_js_plugins = len(result.plugins) > 0
        result.has_utilities = len(result.utilities) > 0
        result.has_react_bootstrap = any(
            fw in ('react-bootstrap', 'reactstrap')
            for fw in result.detected_frameworks
        )
        result.has_bootswatch = any(
            t.method == 'bootswatch' for t in result.themes
        )

        # ── Detect Bootstrap version ──────────────────────────────
        result.bootstrap_version = self._detect_bootstrap_version(
            content, result
        )

        # ── Detect features ───────────────────────────────────────
        result.detected_features = self._detect_features(content, result)

        return result

    def is_bootstrap_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Bootstrap code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Bootstrap code
        """
        if not content:
            return False

        # Check for react-bootstrap/reactstrap imports
        if re.search(
            r"from\s+['\"](?:react-bootstrap|reactstrap)['/\"]",
            content
        ):
            return True

        # Check for bootstrap imports (JS/TS)
        if re.search(
            r"from\s+['\"]bootstrap['/\"]|"
            r"require\(['\"]bootstrap['/\"]\)",
            content
        ):
            return True

        # Check for bootstrap CSS/JS includes
        if re.search(
            r'bootstrap(?:\.bundle)?(?:\.min)?\.(?:css|js)',
            content, re.IGNORECASE
        ):
            return True

        # Check for Bootstrap CDN links
        if re.search(
            r'bootstrapcdn\.com|cdn\.jsdelivr\.net/npm/bootstrap',
            content, re.IGNORECASE
        ):
            return True

        # Check for data-bs-* attributes (v5)
        if re.search(r'data-bs-toggle|data-bs-target|data-bs-dismiss', content):
            return True

        # Check for data-toggle (v3/v4)
        if re.search(r'data-toggle\s*=', content):
            return True

        # Check for Bootstrap-specific CSS classes (common patterns)
        bootstrap_classes = (
            r'\bcontainer\b.*\brow\b.*\bcol-',
            r'\bbtn\s+btn-(?:primary|secondary|success|danger|warning|info)',
            r'\bnavbar\b.*\bnavbar-',
            r'\bmodal\b.*\bmodal-dialog',
            r'\bcard\b.*\bcard-body',
            r'\bform-control\b',
            r'\balert\s+alert-',
            r'\baccordion\b.*\baccordion-item',
        )
        for pattern in bootstrap_classes:
            if re.search(pattern, content, re.DOTALL):
                return True

        # Check for SCSS Bootstrap imports
        if re.search(
            r"@import\s+['\"].*bootstrap|@use\s+['\"].*bootstrap",
            content
        ):
            return True

        # Check for --bs- CSS custom properties
        if re.search(r'--bs-\w+', content):
            return True

        # Check for new bootstrap.* (vanilla JS)
        if re.search(r'new\s+bootstrap\.\w+', content):
            return True

        # Check for ng-bootstrap
        if re.search(r'@ng-bootstrap|NgbModule', content):
            return True

        # Check for bootstrap-vue
        if re.search(r'bootstrap-vue|BootstrapVue', content):
            return True

        return False

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Bootstrap ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return sorted(frameworks)

    def _detect_bootstrap_version(
        self, content: str, result: BootstrapParseResult
    ) -> str:
        """
        Detect the Bootstrap version from content patterns.

        Returns version string: 'v3', 'v4', 'v5', 'v5.3'
        """
        detected_version = ''
        max_priority = -1

        for indicator, version in self.BOOTSTRAP_VERSION_INDICATORS.items():
            if indicator in content:
                priority = self.VERSION_PRIORITY.get(version, 0)
                if priority > max_priority:
                    max_priority = priority
                    detected_version = version

        # Check CDN includes for explicit version
        for cdn in result.cdn_includes:
            if cdn.version:
                major = cdn.version.split('.')[0]
                minor = cdn.version.split('.')[1] if '.' in cdn.version else '0'
                if major == '5' and int(minor) >= 3:
                    return 'v5.3'
                elif major == '5':
                    return 'v5'
                elif major == '4':
                    return 'v4'
                elif major == '3':
                    return 'v3'

        # Default to v5 if we detect Bootstrap but can't determine version
        if not detected_version and (
            result.components or result.plugins or result.utilities
        ):
            detected_version = 'v5'

        return detected_version

    def _detect_features(
        self, content: str, result: BootstrapParseResult
    ) -> List[str]:
        """Detect Bootstrap features used in the file."""
        features: List[str] = []

        # Component-level features
        if result.components:
            features.append('bootstrap_components')
            categories = set(
                c.category for c in result.components if c.category
            )
            for cat in sorted(categories):
                features.append(f'bs_category_{cat}')

        if result.custom_components:
            features.append('custom_wrapped_components')

        # Grid features
        if result.has_grid:
            features.append('grid_system')
            if any(g.is_nested for g in result.grids):
                features.append('nested_grid')
            if any(g.grid_type == 'css-grid' for g in result.grids):
                features.append('css_grid_mode')

        # Responsive
        if result.has_responsive:
            features.append('responsive_design')
            bp_set = set()
            for bp in result.breakpoints:
                bp_set.add(bp.breakpoint)
            for bp in sorted(bp_set):
                features.append(f'breakpoint_{bp}')

        # Theme
        if result.has_custom_theme:
            features.append('custom_theme')
        if result.has_bootswatch:
            features.append('bootswatch_theme')
        if result.has_dark_mode:
            features.append('dark_mode')
        if result.variables:
            features.append('theme_variables')
            var_cats = set(v.category for v in result.variables if v.category)
            for cat in sorted(var_cats):
                features.append(f'theme_{cat}')

        # Utilities
        if result.has_utilities:
            features.append('utility_classes')
            for summary in result.utility_summary:
                features.append(f'utility_{summary.category}')

        # JavaScript plugins
        if result.has_js_plugins:
            features.append('js_plugins')
            plugin_names = set(p.plugin_name for p in result.plugins)
            for pn in sorted(plugin_names):
                features.append(f'plugin_{pn}')

        # Events
        if result.events:
            features.append('bootstrap_events')

        # React-Bootstrap
        if result.has_react_bootstrap:
            features.append('react_bootstrap')

        # CDN usage
        if result.cdn_includes:
            sources = set(c.source for c in result.cdn_includes)
            for s in sorted(sources):
                features.append(f'source_{s}')

        # Remove duplicates preserving order
        seen = set()
        unique_features = []
        for f in features:
            if f not in seen:
                seen.add(f)
                unique_features.append(f)

        return unique_features
