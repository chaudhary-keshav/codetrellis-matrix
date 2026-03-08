"""
EnhancedStimulusParser v1.0 - Comprehensive Stimulus/Hotwire parser using all extractors.

This parser integrates all Stimulus/Hotwire extractors to provide complete parsing of
Stimulus framework usage across HTML, JavaScript, and TypeScript source files.
It runs as a supplementary layer on top of the HTML/JavaScript/TypeScript parsers,
extracting Stimulus-specific semantics.

Supports:
- Stimulus v1.x (stimulus npm package, data-target="controller.name",
                  deprecated lifecycle: initialize/connect/disconnect only)
- Stimulus v2.x (@hotwired/stimulus, data-controller-target="name",
                  values API, classes API)
- Stimulus v3.x (@hotwired/stimulus v3.x, outlets API, afterLoad,
                  multiple-event actions, :prevent/:stop/:self/:once options,
                  keyboard event filters)
- Turbo v7.x-v8.x (@hotwired/turbo, turbo-frame, turbo-stream,
                     Turbo.visit(), Turbo Drive, Turbo Streams, morphing v8)
- Turbo Rails (@hotwired/turbo-rails, turbo_frame_tag, turbo_stream_from)
- Strada v1.x (@hotwired/strada, BridgeComponent, BridgeElement)

Core Concepts:
- Controllers — class extending Controller with lifecycle (initialize,
                connect, disconnect), plus v2+ (connected/disconnected
                callbacks for targets, values, outlets)
- Targets — named element references via data-controller-target (v2+)
             or data-target="controller.name" (v1)
- Actions — event handlers via data-action="event->controller#method"
             with modifiers (:prevent, :stop, :self, :once),
             keyboard filters (keydown.enter, keydown.tab),
             and global targets (@window, @document)
- Values — typed reactive properties via static values = { ... },
            HTML data-controller-name-value="...",
            valueChanged callbacks, get/set accessors
- Classes — CSS class tokens via static classes = [ ... ],
             this.nameClass, this.hasNameClass
- Outlets — cross-controller references via static outlets = [ ... ],
              this.nameOutlet, this.nameOutlets, this.hasNameOutlet,
              nameOutletConnected/Disconnected callbacks

Turbo Integration:
- turbo-frame — frame-based page fragments
- turbo-stream — server-side rendering actions (append, prepend, replace,
                  update, remove, before, after, morph, refresh)
- Turbo Drive — page-level navigation (Turbo.visit())
- Turbo Events — turbo:load, turbo:before-visit, turbo:submit-start, etc.
- Turbo Morphing — morph refresh mode (v8)

Strada Integration:
- BridgeComponent — native mobile bridge controller
- BridgeElement — custom element for bridge communication
- Native callbacks — bridgeDidConnect, bridgeDidDisconnect

Ecosystem Integration Detection:
- Rails (Importmap, Propshaft, Sprockets, Webpacker, UJS)
- Laravel (Vite plugin, Mix)
- Django (django-stimulus, templates)
- Phoenix (LiveView, Hooks)
- Spring Boot (Thymeleaf + Stimulus)
- Webpack (stimulus-webpack-helpers, definitionsFromContext)
- Vite (stimulus-vite-helpers, import.meta.glob)
- esbuild / Rollup / Parcel integration
- Alpine.js coexistence
- HTMX coexistence
- Tailwind CSS

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.68 - Stimulus / Hotwire Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Stimulus extractors
from .extractors.stimulus import (
    StimulusControllerExtractor, StimulusControllerInfo,
    StimulusTargetExtractor, StimulusTargetInfo,
    StimulusActionExtractor, StimulusActionInfo,
    StimulusValueExtractor, StimulusValueInfo,
    StimulusApiExtractor, StimulusImportInfo, StimulusIntegrationInfo,
    StimulusConfigInfo, StimulusCDNInfo,
)


@dataclass
class StimulusParseResult:
    """Complete parse result for a file with Stimulus/Hotwire usage."""
    file_path: str
    file_type: str = "html"  # html, js, ts, erb, blade.php, etc.

    # Controllers
    controllers: List[StimulusControllerInfo] = field(default_factory=list)

    # Targets
    targets: List[StimulusTargetInfo] = field(default_factory=list)

    # Actions
    actions: List[StimulusActionInfo] = field(default_factory=list)

    # Values
    values: List[StimulusValueInfo] = field(default_factory=list)

    # API / Ecosystem
    imports: List[StimulusImportInfo] = field(default_factory=list)
    integrations: List[StimulusIntegrationInfo] = field(default_factory=list)
    configs: List[StimulusConfigInfo] = field(default_factory=list)
    cdns: List[StimulusCDNInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    stimulus_version: str = ""  # v1, v2, v3
    has_turbo: bool = False
    has_strada: bool = False


class EnhancedStimulusParser:
    """
    Enhanced Stimulus/Hotwire parser that uses all extractors.

    This parser runs AFTER the HTML/JavaScript/TypeScript parser when Stimulus
    framework is detected. It extracts Stimulus-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 20+ Stimulus/Hotwire ecosystem libraries.

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Stimulus/Hotwire ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'stimulus': re.compile(
            r"""(?:from\s+['"]@hotwired/stimulus['"]|"""
            r"""from\s+['"]stimulus['"]|"""
            r"""require\(['"]@hotwired/stimulus['"]\)|"""
            r"""require\(['"]stimulus['"]\)|"""
            r"""data-controller\s*=)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'turbo': re.compile(
            r"""(?:from\s+['"]@hotwired/turbo['"]|"""
            r"""require\(['"]@hotwired/turbo['"]\)|"""
            r"""<turbo-frame|<turbo-stream|"""
            r"""Turbo\.visit\(|Turbo\.connectStreamSource\()""",
            re.MULTILINE | re.IGNORECASE
        ),
        'turbo-rails': re.compile(
            r"""(?:from\s+['"]@hotwired/turbo-rails['"]|"""
            r"""turbo_frame_tag|turbo_stream_from|"""
            r"""turbo_stream\.)""",
            re.MULTILINE
        ),
        'strada': re.compile(
            r"""(?:from\s+['"]@hotwired/strada['"]|"""
            r"""BridgeComponent|BridgeElement)""",
            re.MULTILINE
        ),

        # ── Bundler helpers ──────────────────────────────────────
        'stimulus-webpack-helpers': re.compile(
            r"""(?:stimulus-webpack-helpers|definitionsFromContext)""",
            re.MULTILINE
        ),
        'stimulus-vite-helpers': re.compile(
            r"""(?:stimulus-vite-helpers|registerControllers)""",
            re.MULTILINE
        ),
        'stimulus-loading': re.compile(
            r"""(?:@hotwired/stimulus-loading|eagerControllersFrom|lazyControllersFrom)""",
            re.MULTILINE
        ),

        # ── Stimulus community components ────────────────────────
        'stimulus-use': re.compile(
            r"""(?:from\s+['"]stimulus-use['"]|"""
            r"""useClickOutside|useDebounce|useThrottle|useMutation|"""
            r"""useResize|useIntersection|useVisibility|useIdle|"""
            r"""useHover|useTransition|useWindowResize|useWindowFocus|"""
            r"""useDispatch|useApplication|useMeta)""",
            re.MULTILINE
        ),
        'stimulus-components': re.compile(
            r"""stimulus-components|"""
            r"""stimulus-autocomplete|stimulus-sortable|"""
            r"""stimulus-dropdown|stimulus-flatpickr|"""
            r"""stimulus-content-loader|stimulus-reveal|"""
            r"""stimulus-checkbox-select-all|stimulus-character-counter|"""
            r"""stimulus-textarea-autogrow|stimulus-rails-nested-form""",
            re.MULTILINE
        ),

        # ── Backend frameworks ───────────────────────────────────
        'rails': re.compile(
            r"""(?:turbo_frame_tag|turbo_stream_from|"""
            r"""stimulus_controller|<%=|\.html\.erb|"""
            r"""Turbo::StreamsChannel|ActionCable|"""
            r"""pin\s+['"]@hotwired)""",
            re.MULTILINE
        ),
        'laravel': re.compile(
            r"""(?:@vite|laravel-vite-plugin|"""
            r"""stimulus-laravel|\.blade\.php)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'django': re.compile(
            r"""(?:django-stimulus|{%\s*load\s+stimulus|"""
            r"""django\.stimulus|stimulus_js)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'phoenix': re.compile(
            r"""(?:phx-|phoenix_live_view|LiveView|"""
            r"""phoenix.*stimulus|stimulus.*phoenix)""",
            re.MULTILINE | re.IGNORECASE
        ),

        # ── Coexistence ──────────────────────────────────────────
        'alpinejs': re.compile(
            r"""(?:from\s+['"]alpinejs['"]|x-data\s*=|Alpine\.)""",
            re.MULTILINE
        ),
        'htmx': re.compile(
            r"""(?:from\s+['"]htmx\.org['"]|hx-(?:get|post|put|delete|swap|trigger|target))""",
            re.MULTILINE | re.IGNORECASE
        ),
        'tailwind': re.compile(
            r"""(?:tailwindcss|@tailwind\s|class="[^"]*(?:flex|grid|text-|bg-|p-\d|m-\d|w-\d|h-\d))""",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        # Controller lifecycle
        'controller-class': re.compile(
            r"""class\s+\w+\s+extends\s+(?:Controller|ApplicationController|BaseController)""",
            re.MULTILINE
        ),
        'lifecycle-connect': re.compile(r"""\bconnect\s*\(""", re.MULTILINE),
        'lifecycle-disconnect': re.compile(r"""\bdisconnect\s*\(""", re.MULTILINE),
        'lifecycle-initialize': re.compile(r"""\binitialize\s*\(""", re.MULTILINE),

        # Targets
        'static-targets': re.compile(r"""static\s+targets\s*=""", re.MULTILINE),
        'target-getter': re.compile(r"""this\.\w+Target\b""", re.MULTILINE),
        'target-callback': re.compile(r"""\w+TargetConnected\b""", re.MULTILINE),
        'html-target-v2': re.compile(r"""data-\w+-target\s*=""", re.MULTILINE),
        'html-target-v1': re.compile(r"""data-target\s*=""", re.MULTILINE),

        # Actions
        'html-action': re.compile(r"""data-action\s*=""", re.MULTILINE),
        'action-options': re.compile(r""":(?:prevent|stop|self|once)\b""", re.MULTILINE),
        'keyboard-filter': re.compile(r"""keydown\.\w+->""", re.MULTILINE),
        'global-action': re.compile(r"""@(?:window|document)""", re.MULTILINE),
        'action-params': re.compile(r"""data-\w+-\w+-param\s*=""", re.MULTILINE),

        # Values
        'static-values': re.compile(r"""static\s+values\s*=""", re.MULTILINE),
        'value-changed': re.compile(r"""\w+ValueChanged\b""", re.MULTILINE),
        'html-value': re.compile(r"""data-\w+-\w+-value\s*=""", re.MULTILINE),
        'value-getter': re.compile(r"""this\.\w+Value\b""", re.MULTILINE),

        # Classes (v2+)
        'static-classes': re.compile(r"""static\s+classes\s*=""", re.MULTILINE),
        'class-getter': re.compile(r"""this\.\w+Class\b""", re.MULTILINE),

        # Outlets (v3+)
        'static-outlets': re.compile(r"""static\s+outlets\s*=""", re.MULTILINE),
        'outlet-getter': re.compile(r"""this\.\w+Outlet\b""", re.MULTILINE),
        'outlet-callback': re.compile(r"""\w+OutletConnected\b""", re.MULTILINE),

        # afterLoad (v3+)
        'afterLoad': re.compile(r"""static\s+afterLoad\b""", re.MULTILINE),

        # Application API
        'app-start': re.compile(r"""Application\.start\(""", re.MULTILINE),
        'app-register': re.compile(r"""\.register\s*\(""", re.MULTILINE),
        'app-load': re.compile(r"""\.load\s*\(""", re.MULTILINE),

        # Turbo features
        'turbo-frame': re.compile(r"""<turbo-frame""", re.IGNORECASE),
        'turbo-stream': re.compile(r"""<turbo-stream""", re.IGNORECASE),
        'turbo-visit': re.compile(r"""Turbo\.visit\(""", re.MULTILINE),
        'turbo-drive': re.compile(r"""Turbo\.session\.drive""", re.MULTILINE),
        'turbo-events': re.compile(r"""turbo:[\w-]+""", re.MULTILINE),
        'turbo-morph': re.compile(r"""(?:action="morph"|morph:\s*true|turbo:morph)""", re.MULTILINE | re.IGNORECASE),
        'turbo-stream-source': re.compile(r"""Turbo\.connectStreamSource\(""", re.MULTILINE),

        # Strada features
        'bridge-component': re.compile(r"""BridgeComponent""", re.MULTILINE),
        'bridge-element': re.compile(r"""BridgeElement""", re.MULTILINE),
        'bridge-callback': re.compile(r"""bridgeDidConnect|bridgeDidDisconnect""", re.MULTILINE),

        # Registration patterns
        'definitions-from-context': re.compile(r"""definitionsFromContext""", re.MULTILINE),
        'import-meta-glob': re.compile(r"""import\.meta\.glob""", re.MULTILINE),
        'eager-controllers': re.compile(r"""eagerControllers""", re.MULTILINE),
        'lazy-controllers': re.compile(r"""lazyControllers""", re.MULTILINE),
    }

    # Version precedence (higher index = newer version)
    VERSION_ORDER = ['v1', 'v2', 'v3']

    def __init__(self):
        """Initialize the Stimulus parser with all extractors."""
        self.controller_extractor = StimulusControllerExtractor()
        self.target_extractor = StimulusTargetExtractor()
        self.action_extractor = StimulusActionExtractor()
        self.value_extractor = StimulusValueExtractor()
        self.api_extractor = StimulusApiExtractor()

    def is_stimulus_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file contains Stimulus/Hotwire code.

        Args:
            content: Source code content.
            file_path: Path to the source file.

        Returns:
            True if the file uses Stimulus/Hotwire.
        """
        if not content or not content.strip():
            return False

        # Check for Stimulus imports (JS/TS files)
        if re.search(
            r"""(?:from\s+['"]@hotwired/stimulus['"]|"""
            r"""from\s+['"]stimulus['"]|"""
            r"""require\(['"]@hotwired/stimulus['"]\)|"""
            r"""require\(['"]stimulus['"]\))""",
            content
        ):
            return True

        # Check for data-controller attribute (HTML files)
        if re.search(r'data-controller\s*=', content):
            return True

        # Check for data-action attribute
        if re.search(r'data-action\s*=', content):
            return True

        # Check for Controller class extension
        if re.search(r'class\s+\w+\s+extends\s+Controller\b', content):
            return True

        # Check for Turbo elements
        if re.search(r'<turbo-(?:frame|stream)\b', content, re.IGNORECASE):
            return True

        # Check for Strada
        if re.search(r'BridgeComponent|@hotwired/strada', content):
            return True

        # Check for CDN script tag
        if re.search(
            r'<script[^>]*(?:@hotwired/stimulus|stimulus\.min\.js|turbo\.es)',
            content, re.IGNORECASE
        ):
            return True

        # Check for Turbo imports
        if re.search(
            r"""(?:from\s+['"]@hotwired/turbo['"]|"""
            r"""from\s+['"]@hotwired/turbo-rails['"]|"""
            r"""import\s+['"]@hotwired/turbo['"]|"""
            r"""import\s+['"]@hotwired/turbo-rails['"])""",
            content
        ):
            return True

        return False

    def parse(self, content: str, file_path: str = "") -> StimulusParseResult:
        """Parse a file for Stimulus/Hotwire usage.

        Args:
            content: Source code content.
            file_path: Path to the source file.

        Returns:
            StimulusParseResult with all extracted information.
        """
        file_type = self._detect_file_type(file_path)
        result = StimulusParseResult(file_path=file_path, file_type=file_type)

        if not content or not content.strip():
            return result

        # Run all extractors
        result.controllers = self.controller_extractor.extract(content, file_path)
        result.targets = self.target_extractor.extract(content, file_path)
        result.actions = self.action_extractor.extract(content, file_path)
        result.values = self.value_extractor.extract(content, file_path)

        result.imports = self.api_extractor.extract_imports(content, file_path)
        result.integrations = self.api_extractor.extract_integrations(content, file_path)
        result.configs = self.api_extractor.extract_configs(content, file_path)
        result.cdns = self.api_extractor.extract_cdns(content, file_path)

        # Detect frameworks and features
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)

        # Detect version
        result.stimulus_version = self._detect_version(content, result)

        # Detect Turbo presence
        result.has_turbo = self._has_turbo(content, result)

        # Detect Strada presence
        result.has_strada = self._has_strada(content, result)

        return result

    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from extension.

        Args:
            file_path: Path to the source file.

        Returns:
            File type string.
        """
        fp = file_path.lower()
        if fp.endswith('.html') or fp.endswith('.htm'):
            return 'html'
        if fp.endswith('.html.erb') or fp.endswith('.erb'):
            return 'erb'
        if fp.endswith('.blade.php'):
            return 'blade'
        if fp.endswith('.tsx'):
            return 'tsx'
        if fp.endswith('.ts'):
            return 'ts'
        if fp.endswith('.jsx'):
            return 'jsx'
        if fp.endswith('.js') or fp.endswith('.mjs') or fp.endswith('.cjs'):
            return 'js'
        if fp.endswith('.vue'):
            return 'vue'
        if fp.endswith('.svelte'):
            return 'svelte'
        if fp.endswith('.njk') or fp.endswith('.nunjucks'):
            return 'nunjucks'
        if fp.endswith('.hbs') or fp.endswith('.handlebars'):
            return 'handlebars'
        if fp.endswith('.ejs'):
            return 'ejs'
        if fp.endswith('.jinja') or fp.endswith('.jinja2') or fp.endswith('.j2'):
            return 'jinja'
        if fp.endswith('.haml'):
            return 'haml'
        if fp.endswith('.slim'):
            return 'slim'
        if fp.endswith('.heex'):
            return 'heex'
        return 'html'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Stimulus/Hotwire ecosystem frameworks in content.

        Args:
            content: Source code content.

        Returns:
            List of detected framework names.
        """
        frameworks: List[str] = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_features(self, content: str) -> List[str]:
        """Detect Stimulus/Hotwire features used in content.

        Args:
            content: Source code content.

        Returns:
            List of detected feature names.
        """
        features: List[str] = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                features.append(name)
        return features

    def _detect_version(self, content: str, result: StimulusParseResult) -> str:
        """Detect the Stimulus version from content and parse results.

        Args:
            content: Source code content.
            result: Current parse result.

        Returns:
            Version string (e.g., 'v3', 'v2', 'v1').
        """
        version = ""

        # CDN version detection
        for cdn in result.cdns:
            if cdn.version and cdn.package == 'stimulus':
                major = cdn.version.split('.')[0]
                cdn_version = f"v{major}"
                if self._version_compare(cdn_version, version) > 0:
                    version = cdn_version

        # Import-based detection
        for imp in result.imports:
            if imp.version_hint:
                if self._version_compare(imp.version_hint, version) > 0:
                    version = imp.version_hint

        # Controller version hints
        for ctrl in result.controllers:
            if ctrl.version_hint:
                if self._version_compare(ctrl.version_hint, version) > 0:
                    version = ctrl.version_hint

        # Feature-based version detection
        v3_features = {
            'static-outlets', 'outlet-getter', 'outlet-callback',
            'afterLoad', 'action-options', 'keyboard-filter',
        }
        v2_features = {
            'static-targets', 'static-values', 'static-classes',
            'target-callback', 'value-changed', 'html-target-v2',
        }
        v1_features = {
            'html-target-v1',
        }

        detected = set(result.detected_features)

        if detected & v3_features:
            if self._version_compare('v3', version) > 0:
                version = 'v3'
        elif detected & v2_features:
            if self._version_compare('v2', version) > 0:
                version = 'v2'
        elif detected & v1_features:
            if not version:
                version = 'v1'
        elif any(f in detected for f in ('controller-class', 'html-action', 'app-start')):
            if not version:
                version = 'v2'  # Default to v2 if basic patterns found

        return version

    def _has_turbo(self, content: str, result: StimulusParseResult) -> bool:
        """Detect if Turbo is used in the file.

        Args:
            content: Source code content.
            result: Current parse result.

        Returns:
            True if Turbo is detected.
        """
        # Check imports
        for imp in result.imports:
            if 'turbo' in imp.source.lower():
                return True

        # Check integrations
        for integ in result.integrations:
            if integ.integration_type == 'turbo':
                return True

        # Check framework detection
        if 'turbo' in result.detected_frameworks or 'turbo-rails' in result.detected_frameworks:
            return True

        # Direct content check
        if re.search(r'<turbo-(?:frame|stream)\b', content, re.IGNORECASE):
            return True
        if re.search(r'Turbo\.', content):
            return True

        return False

    def _has_strada(self, content: str, result: StimulusParseResult) -> bool:
        """Detect if Strada is used in the file.

        Args:
            content: Source code content.
            result: Current parse result.

        Returns:
            True if Strada is detected.
        """
        # Check imports
        for imp in result.imports:
            if 'strada' in imp.source.lower():
                return True

        # Check integrations
        for integ in result.integrations:
            if integ.name == 'strada':
                return True

        # Check framework detection
        if 'strada' in result.detected_frameworks:
            return True

        # Direct content check
        if re.search(r'BridgeComponent|BridgeElement', content):
            return True

        return False

    def _version_compare(self, v1: str, v2: str) -> int:
        """Compare two version strings.

        Args:
            v1: First version (e.g., 'v3').
            v2: Second version (e.g., 'v2').

        Returns:
            1 if v1 > v2, -1 if v1 < v2, 0 if equal.
        """
        if not v1 and not v2:
            return 0
        if not v2:
            return 1
        if not v1:
            return -1

        order = self.VERSION_ORDER
        idx1 = order.index(v1) if v1 in order else -1
        idx2 = order.index(v2) if v2 in order else -1

        if idx1 > idx2:
            return 1
        if idx1 < idx2:
            return -1
        return 0
