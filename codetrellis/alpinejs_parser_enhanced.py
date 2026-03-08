"""
EnhancedAlpineParser v1.0 - Comprehensive Alpine.js parser using all extractors.

This parser integrates all Alpine.js extractors to provide complete parsing of
Alpine.js framework usage across HTML, JavaScript, and TypeScript source files.
It runs as a supplementary layer on top of the HTML/JavaScript/TypeScript parsers,
extracting Alpine.js-specific semantics.

Supports:
- Alpine.js v1.x (legacy, CDN only, no Alpine.start(), x-spread)
- Alpine.js v2.x (CDN, component objects, x-data, x-ref)
- Alpine.js v3.x (npm ESM, Alpine.start(), Alpine.data(), Alpine.store(),
                   Alpine.directive(), Alpine.magic(), Alpine.plugin(),
                   x-effect, x-teleport, x-id, x-ignore, x-modelable)
- Alpine.js v3.10+ (Alpine.bind(), improved reactivity)
- Alpine.js v3.14+ (x-sort plugin, enhanced features)

Core Directives:
- x-data — component data/scope
- x-bind / : — reactive attribute binding
- x-on / @ — event listener binding
- x-model — two-way data binding
- x-show — toggle visibility (display:none)
- x-if — conditional rendering (removes from DOM)
- x-for — list iteration
- x-transition — CSS transition helpers
- x-effect — reactive side effects (v3+)
- x-ref — element reference ($refs)
- x-text — reactive text content
- x-html — reactive inner HTML
- x-init — initialization hook
- x-cloak — hide until Alpine initializes
- x-teleport — portal/teleport (v3+)
- x-ignore — skip Alpine initialization (v3+)
- x-id — scoped ID generation (v3+)

Magics:
- $el — current DOM element
- $refs — named element references
- $store — global store access
- $watch — reactive watcher
- $dispatch — dispatch custom events
- $nextTick — defer until next DOM update
- $root — root x-data element
- $data — reactive data proxy
- $id — scoped unique IDs

Plugins (@alpinejs/*):
- @alpinejs/mask — input masking (x-mask)
- @alpinejs/intersect — intersection observer (x-intersect)
- @alpinejs/persist — localStorage persistence ($persist)
- @alpinejs/morph — DOM morphing
- @alpinejs/focus — focus management (x-trap)
- @alpinejs/collapse — collapse transitions (x-collapse)
- @alpinejs/anchor — anchor positioning (x-anchor)
- @alpinejs/sort — sortable lists (x-sort)
- @alpinejs/ui — headless UI components
- @alpinejs/resize — resize observer (x-resize)

Ecosystem Integration Detection:
- HTMX (hx-* attributes, htmx.org)
- Laravel Livewire (wire:*, @livewire)
- Hotwire/Turbo (turbo-frame, turbo-stream)
- Tailwind CSS (utility classes)
- Laravel Blade (@@csrf, @@section)
- Django Templates ({{% %}})
- Rails ERB (<%=)
- Phoenix LiveView (phx-*)

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.66 - Alpine.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Alpine.js extractors
from .extractors.alpinejs import (
    AlpineDirectiveExtractor, AlpineDirectiveInfo,
    AlpineComponentExtractor, AlpineComponentInfo, AlpineMethodInfo,
    AlpineStoreExtractor, AlpineStoreInfo,
    AlpinePluginExtractor, AlpinePluginInfo, AlpineCustomDirectiveInfo, AlpineCustomMagicInfo,
    AlpineApiExtractor, AlpineImportInfo, AlpineIntegrationInfo, AlpineTypeInfo, AlpineCDNInfo,
)


@dataclass
class AlpineParseResult:
    """Complete parse result for a file with Alpine.js usage."""
    file_path: str
    file_type: str = "html"  # html, js, ts, blade.php, etc.

    # Directives
    directives: List[AlpineDirectiveInfo] = field(default_factory=list)

    # Components
    components: List[AlpineComponentInfo] = field(default_factory=list)
    methods: List[AlpineMethodInfo] = field(default_factory=list)

    # Stores
    stores: List[AlpineStoreInfo] = field(default_factory=list)

    # Plugins
    plugins: List[AlpinePluginInfo] = field(default_factory=list)
    custom_directives: List[AlpineCustomDirectiveInfo] = field(default_factory=list)
    custom_magics: List[AlpineCustomMagicInfo] = field(default_factory=list)

    # API
    imports: List[AlpineImportInfo] = field(default_factory=list)
    integrations: List[AlpineIntegrationInfo] = field(default_factory=list)
    types: List[AlpineTypeInfo] = field(default_factory=list)
    cdns: List[AlpineCDNInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    alpine_version: str = ""  # v1, v2, v3


class EnhancedAlpineParser:
    """
    Enhanced Alpine.js parser that uses all extractors.

    This parser runs AFTER the HTML/JavaScript/TypeScript parser when Alpine.js
    framework is detected. It extracts Alpine.js-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 30+ Alpine.js ecosystem libraries.

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Alpine.js ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'alpinejs': re.compile(
            r"""(?:from\s+['"]alpinejs['"]|require\(['"]alpinejs['"]\)|"""
            r"""<script[^>]*alpinejs[^>]*>)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'alpine-csp': re.compile(
            r"""(?:from\s+['"]@alpinejs/csp['"]|alpinejs/csp)""",
            re.MULTILINE
        ),

        # ── Official plugins ─────────────────────────────────────
        'alpine-mask': re.compile(
            r"""(?:from\s+['"]@alpinejs/mask['"]|x-mask)""",
            re.MULTILINE
        ),
        'alpine-intersect': re.compile(
            r"""(?:from\s+['"]@alpinejs/intersect['"]|x-intersect)""",
            re.MULTILINE
        ),
        'alpine-persist': re.compile(
            r"""(?:from\s+['"]@alpinejs/persist['"]|\$persist)""",
            re.MULTILINE
        ),
        'alpine-morph': re.compile(
            r"""from\s+['"]@alpinejs/morph['"]""",
            re.MULTILINE
        ),
        'alpine-focus': re.compile(
            r"""(?:from\s+['"]@alpinejs/focus['"]|x-trap)""",
            re.MULTILINE
        ),
        'alpine-collapse': re.compile(
            r"""(?:from\s+['"]@alpinejs/collapse['"]|x-collapse)""",
            re.MULTILINE
        ),
        'alpine-anchor': re.compile(
            r"""(?:from\s+['"]@alpinejs/anchor['"]|x-anchor)""",
            re.MULTILINE
        ),
        'alpine-sort': re.compile(
            r"""(?:from\s+['"]@alpinejs/sort['"]|x-sort)""",
            re.MULTILINE
        ),
        'alpine-ui': re.compile(
            r"""from\s+['"]@alpinejs/ui['"]""",
            re.MULTILINE
        ),
        'alpine-resize': re.compile(
            r"""(?:from\s+['"]@alpinejs/resize['"]|x-resize)""",
            re.MULTILINE
        ),

        # ── Ecosystem ────────────────────────────────────────────
        'htmx': re.compile(
            r"""(?:from\s+['"]htmx\.org['"]|hx-(?:get|post|put|delete|patch|swap|trigger|target))""",
            re.MULTILINE | re.IGNORECASE
        ),
        'livewire': re.compile(
            r"""(?:@livewire|wire:|Livewire\.)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'turbo': re.compile(
            r"""(?:@hotwired/turbo|turbo-frame|turbo-stream)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'stimulus': re.compile(
            r"""(?:@hotwired/stimulus|data-controller|data-action)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'tailwind': re.compile(
            r"""(?:tailwindcss|@tailwind\s|class="[^"]*(?:flex|grid|text-|bg-|p-\d|m-\d|w-\d|h-\d))""",
            re.MULTILINE
        ),

        # ── Third-party plugins ──────────────────────────────────
        'alpine-clipboard': re.compile(
            r"""(?:alpine-clipboard|x-clipboard)""",
            re.MULTILINE
        ),
        'alpine-tooltip': re.compile(
            r"""(?:alpine-tooltip|x-tooltip)""",
            re.MULTILINE
        ),
        'alpine-turbo-drive': re.compile(
            r"""alpine-turbo-drive-adapter""",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        # Core directives
        'x-data': re.compile(r"""x-data\s*=""", re.MULTILINE),
        'x-bind': re.compile(r"""(?:x-bind:|:[a-zA-Z])""", re.MULTILINE),
        'x-on': re.compile(r"""(?:x-on:|@[a-zA-Z])""", re.MULTILINE),
        'x-model': re.compile(r"""x-model""", re.MULTILINE),
        'x-show': re.compile(r"""x-show""", re.MULTILINE),
        'x-if': re.compile(r"""x-if""", re.MULTILINE),
        'x-for': re.compile(r"""x-for""", re.MULTILINE),
        'x-transition': re.compile(r"""x-transition""", re.MULTILINE),
        'x-text': re.compile(r"""x-text""", re.MULTILINE),
        'x-html': re.compile(r"""x-html""", re.MULTILINE),
        'x-ref': re.compile(r"""x-ref""", re.MULTILINE),
        'x-init': re.compile(r"""x-init""", re.MULTILINE),
        'x-cloak': re.compile(r"""x-cloak""", re.MULTILINE),

        # v3 features
        'x-effect': re.compile(r"""x-effect""", re.MULTILINE),
        'x-teleport': re.compile(r"""x-teleport""", re.MULTILINE),
        'x-ignore': re.compile(r"""x-ignore""", re.MULTILINE),
        'x-id': re.compile(r"""x-id""", re.MULTILINE),
        'x-modelable': re.compile(r"""x-modelable""", re.MULTILINE),
        'alpine_start': re.compile(r"""Alpine\.start\(\)""", re.MULTILINE),
        'alpine_data': re.compile(r"""Alpine\.data\(""", re.MULTILINE),
        'alpine_store': re.compile(r"""Alpine\.store\(""", re.MULTILINE),
        'alpine_directive': re.compile(r"""Alpine\.directive\(""", re.MULTILINE),
        'alpine_magic': re.compile(r"""Alpine\.magic\(""", re.MULTILINE),
        'alpine_plugin': re.compile(r"""Alpine\.plugin\(""", re.MULTILINE),
        'alpine_bind': re.compile(r"""Alpine\.bind\(""", re.MULTILINE),

        # Magics
        'magic_refs': re.compile(r"""\$refs""", re.MULTILINE),
        'magic_el': re.compile(r"""\$el""", re.MULTILINE),
        'magic_store': re.compile(r"""\$store""", re.MULTILINE),
        'magic_watch': re.compile(r"""\$watch""", re.MULTILINE),
        'magic_dispatch': re.compile(r"""\$dispatch""", re.MULTILINE),
        'magic_nextTick': re.compile(r"""\$nextTick""", re.MULTILINE),
        'magic_root': re.compile(r"""\$root""", re.MULTILINE),
        'magic_data': re.compile(r"""\$data""", re.MULTILINE),
        'magic_id': re.compile(r"""\$id""", re.MULTILINE),
        'magic_persist': re.compile(r"""\$persist""", re.MULTILINE),

        # Plugin directives
        'x-mask': re.compile(r"""x-mask""", re.MULTILINE),
        'x-intersect': re.compile(r"""x-intersect""", re.MULTILINE),
        'x-trap': re.compile(r"""x-trap""", re.MULTILINE),
        'x-collapse': re.compile(r"""x-collapse""", re.MULTILINE),
        'x-anchor': re.compile(r"""x-anchor""", re.MULTILINE),
        'x-sort': re.compile(r"""x-sort""", re.MULTILINE),
        'x-resize': re.compile(r"""x-resize""", re.MULTILINE),

        # Modifiers
        'event_modifiers': re.compile(r"""@\w+\.(prevent|stop|window|document|self|away|once|debounce|throttle)""", re.MULTILINE),
        'transition_modifiers': re.compile(r"""x-transition\.(enter|leave|duration|opacity|scale)""", re.MULTILINE),
        'model_modifiers': re.compile(r"""x-model\.(debounce|throttle|number|lazy|fill)""", re.MULTILINE),

        # v1 legacy
        'x-spread': re.compile(r"""x-spread""", re.MULTILINE),
    }

    # Version precedence (higher index = newer version)
    VERSION_ORDER = ['v1', 'v2', 'v3']

    def __init__(self):
        """Initialize the Alpine.js parser with all extractors."""
        self.directive_extractor = AlpineDirectiveExtractor()
        self.component_extractor = AlpineComponentExtractor()
        self.store_extractor = AlpineStoreExtractor()
        self.plugin_extractor = AlpinePluginExtractor()
        self.api_extractor = AlpineApiExtractor()

    def is_alpine_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file contains Alpine.js code.

        Args:
            content: Source code content.
            file_path: Path to the source file.

        Returns:
            True if the file uses Alpine.js.
        """
        if not content or not content.strip():
            return False

        # Check for Alpine.js imports (JS/TS files)
        if any(p.search(content) for key, p in self.FRAMEWORK_PATTERNS.items()
               if key in ('alpinejs', 'alpine-csp')):
            return True

        # Check for x-data attribute (HTML files)
        if re.search(r'x-data\s*=', content):
            return True

        # Check for Alpine.* API calls
        if re.search(r'Alpine\.(start|store|data|directive|magic|plugin)\s*\(', content):
            return True

        # Check for CDN script tag
        if re.search(r'<script[^>]*alpinejs[^>]*>', content, re.IGNORECASE):
            return True

        # Check for document.addEventListener('alpine:init')
        if re.search(r"alpine:init", content):
            return True

        return False

    def parse(self, content: str, file_path: str = "") -> AlpineParseResult:
        """Parse a file for Alpine.js usage.

        Args:
            content: Source code content.
            file_path: Path to the source file.

        Returns:
            AlpineParseResult with all extracted information.
        """
        file_type = self._detect_file_type(file_path)
        result = AlpineParseResult(file_path=file_path, file_type=file_type)

        if not content or not content.strip():
            return result

        # Run all extractors
        result.directives = self.directive_extractor.extract(content, file_path)

        components, methods = self.component_extractor.extract(content, file_path)
        result.components = components
        result.methods = methods

        result.stores = self.store_extractor.extract(content, file_path)

        plugins, custom_dirs, custom_mags = self.plugin_extractor.extract(content, file_path)
        result.plugins = plugins
        result.custom_directives = custom_dirs
        result.custom_magics = custom_mags

        imports, integrations, types, cdns = self.api_extractor.extract(content, file_path)
        result.imports = imports
        result.integrations = integrations
        result.types = types
        result.cdns = cdns

        # Detect frameworks and features
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)

        # Detect version
        result.alpine_version = self._detect_version(content, result)

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
        if fp.endswith('.astro'):
            return 'astro'
        if fp.endswith('.njk') or fp.endswith('.nunjucks'):
            return 'nunjucks'
        if fp.endswith('.hbs') or fp.endswith('.handlebars'):
            return 'handlebars'
        if fp.endswith('.ejs'):
            return 'ejs'
        if fp.endswith('.erb'):
            return 'erb'
        if fp.endswith('.jinja') or fp.endswith('.jinja2') or fp.endswith('.j2'):
            return 'jinja'
        return 'html'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Alpine.js ecosystem frameworks in content.

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
        """Detect Alpine.js features used in content.

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

    def _detect_version(self, content: str, result: AlpineParseResult) -> str:
        """Detect the Alpine.js version from content and parse results.

        Args:
            content: Source code content.
            result: Current parse result.

        Returns:
            Version string (e.g., 'v3', 'v2', 'v1').
        """
        version = ""

        # CDN version detection
        for cdn in result.cdns:
            if cdn.version:
                major = cdn.version.split('.')[0]
                cdn_version = f"v{major}"
                if self._version_compare(cdn_version, version) > 0:
                    version = cdn_version

        # Feature-based version detection
        v3_features = {
            'x-effect', 'x-teleport', 'x-ignore', 'x-id', 'x-modelable',
            'alpine_start', 'alpine_data', 'alpine_store',
            'alpine_directive', 'alpine_magic', 'alpine_plugin', 'alpine_bind',
        }
        v1_features = {'x-spread'}

        detected = set(result.detected_features)

        if detected & v3_features:
            if self._version_compare('v3', version) > 0:
                version = 'v3'
        elif detected & v1_features:
            if not version:
                version = 'v1'
        elif any(f in detected for f in ('x-data', 'x-bind', 'x-on', 'x-model')):
            if not version:
                version = 'v2'  # Default to v2 if basic directives found but no v3 features

        # Import-based detection
        if any(imp.source == 'alpinejs' for imp in result.imports):
            # npm package = v3+
            if self._version_compare('v3', version) > 0:
                version = 'v3'

        if any(imp.source.startswith('@alpinejs/') for imp in result.imports):
            if self._version_compare('v3', version) > 0:
                version = 'v3'

        return version

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
