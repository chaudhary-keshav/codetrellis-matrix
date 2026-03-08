"""
EnhancedHtmxParser v1.0 - Comprehensive HTMX parser using all extractors.

This parser integrates all HTMX extractors to provide complete parsing of
HTMX framework usage across HTML, JavaScript, and TypeScript source files.
It runs as a supplementary layer on top of the HTML/JavaScript/TypeScript parsers,
extracting HTMX-specific semantics.

Supports:
- HTMX v1.x (htmx.org v1.*, data-hx-* prefix, legacy extension paths,
              intercooler.js migration patterns, built-in SSE/WS)
- HTMX v2.x (htmx.org v2.*, hx-on:* inline event syntax, hx-disabled-elt,
              hx-inherit, head-support default, improved WebSocket/SSE,
              response-targets, htmx:historyCacheMiss, htmx-ext/* packages,
              idiomorph default swap, relaxed hx-on:: syntax)

Core Attributes:
- hx-get / hx-post / hx-put / hx-patch / hx-delete — AJAX requests
- hx-swap — swap strategy (innerHTML, outerHTML, beforebegin, afterbegin,
            beforeend, afterend, delete, none, morph)
- hx-target — CSS selector for swap target (this, closest, find, next, previous)
- hx-trigger — event specification with modifiers (changed, delay, throttle,
              from, target, consume, queue, once, every, load, revealed, intersect)
- hx-select — CSS selector to pick from response
- hx-select-oob — out-of-band select
- hx-swap-oob — out-of-band swap
- hx-boost — progressive enhancement (all links/forms become AJAX)
- hx-push-url / hx-replace-url — history management
- hx-indicator — loading indicator selector
- hx-vals — additional request values (JSON or js:expression)
- hx-headers — additional request headers (JSON)
- hx-include — additional inputs to include (CSS selector)
- hx-params — parameter filtering (*, none, not <list>, <list>)
- hx-confirm — confirmation dialog
- hx-prompt — prompt dialog
- hx-disable / hx-disabled-elt — disable elements during request
- hx-disinherit / hx-inherit — inheritance control
- hx-preserve — preserve element across swaps
- hx-sync — request synchronization (drop, abort, queue)
- hx-validate — trigger validation
- hx-encoding — request encoding (multipart/form-data)
- hx-ext — extension registration
- hx-history / hx-history-elt — history integration
- hx-on:event — inline event handler (v2)

Extensions:
- SSE (Server-Sent Events): sse-connect, sse-swap
- WebSocket: ws-connect, ws-send
- json-enc — JSON-encoded body
- class-tools — CSS class manipulation
- debug — console logging
- loading-states — loading indicators
- head-support — head tag merging
- preload — link preloading
- response-targets — error code targeting
- multi-swap — multiple swap targets
- path-deps — path-based dependencies
- remove-me — auto-removing elements
- restored — restoration handling
- alpine-morph — Alpine.js morphing
- idiomorph — morphing swap strategy (v2 default)
- client-side-templates — Mustache/Handlebars/Nunjucks

Event System:
- htmx:afterOnLoad, htmx:afterProcessNode, htmx:afterRequest,
  htmx:afterSettle, htmx:afterSwap, htmx:beforeCleanupElement,
  htmx:beforeOnLoad, htmx:beforeProcessNode, htmx:beforeRequest,
  htmx:beforeSend, htmx:beforeSwap, htmx:beforeTransition,
  htmx:configRequest, htmx:confirm, htmx:historyCacheMiss,
  htmx:historyRestore, htmx:load, htmx:prompt, htmx:responseError,
  htmx:sendError, htmx:sseError, htmx:swapError, htmx:targetError,
  htmx:timeout, htmx:validation:failed, htmx:validation:halted,
  htmx:xhr:abort, htmx:xhr:progress

JS API:
- htmx.ajax(), htmx.process(), htmx.on(), htmx.off(), htmx.trigger(),
  htmx.find(), htmx.findAll(), htmx.closest(), htmx.values(),
  htmx.remove(), htmx.addClass(), htmx.removeClass(), htmx.toggleClass(),
  htmx.takeClass(), htmx.swap(), htmx.defineExtension(), htmx.logAll(),
  htmx.logger, htmx.config.*

Ecosystem Integration Detection:
- Alpine.js (x-data, Alpine.*)
- _hyperscript (hyperscript.org, _="...")
- Django ({% url %}, {% csrf_token %})
- Flask/Jinja2 ({{ url_for() }})
- Rails/ERB (<%= ... %>)
- Laravel/Blade (@csrf, @section)
- FastAPI/Starlette (Jinja2 templates)
- Go (templ, echo, gin)
- ASP.NET (Razor, Blazor)
- Spring/Thymeleaf (th:*)
- Phoenix/LiveView (phx-*)
- Tailwind CSS (utility classes)

Optional AST support via tree-sitter-javascript / tree-sitter-html.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.67 - HTMX Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all HTMX extractors
from .extractors.htmx import (
    HtmxAttributeExtractor, HtmxAttributeInfo,
    HtmxRequestExtractor, HtmxRequestInfo,
    HtmxEventExtractor, HtmxEventInfo,
    HtmxExtensionExtractor, HtmxExtensionInfo,
    HtmxApiExtractor, HtmxImportInfo, HtmxIntegrationInfo, HtmxConfigInfo, HtmxCDNInfo,
)


@dataclass
class HtmxParseResult:
    """Complete parse result for a file with HTMX usage."""
    file_path: str
    file_type: str = "html"  # html, js, ts, blade.php, etc.

    # Attributes
    attributes: List[HtmxAttributeInfo] = field(default_factory=list)

    # Requests
    requests: List[HtmxRequestInfo] = field(default_factory=list)

    # Events
    events: List[HtmxEventInfo] = field(default_factory=list)

    # Extensions
    extensions: List[HtmxExtensionInfo] = field(default_factory=list)

    # API
    imports: List[HtmxImportInfo] = field(default_factory=list)
    integrations: List[HtmxIntegrationInfo] = field(default_factory=list)
    configs: List[HtmxConfigInfo] = field(default_factory=list)
    cdns: List[HtmxCDNInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    htmx_version: str = ""  # v1, v2


class EnhancedHtmxParser:
    """
    Enhanced HTMX parser that uses all extractors.

    This parser runs AFTER the HTML/JavaScript/TypeScript parser when HTMX
    framework is detected. It extracts HTMX-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 20+ HTMX ecosystem libraries.

    Optional AST: tree-sitter-html / tree-sitter-javascript
    Optional LSP: typescript-language-server (tsserver)
    """

    # HTMX ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'htmx': re.compile(
            r"""(?:from\s+['"]htmx\.org['"]|require\(['"]htmx\.org['"]\)|"""
            r"""<script[^>]*htmx[^>]*>|hx-(?:get|post|put|patch|delete)\s*=)""",
            re.MULTILINE | re.IGNORECASE
        ),

        # ── Companion libraries ──────────────────────────────────
        'hyperscript': re.compile(
            r"""(?:hyperscript\.org|_hyperscript|<script[^>]*hyperscript[^>]*>)""",
            re.MULTILINE | re.IGNORECASE
        ),

        # ── Backend frameworks ───────────────────────────────────
        'django': re.compile(
            r"""(?:\{%\s*(?:url|csrf_token|load|block|extends)|django\.contrib)""",
            re.MULTILINE
        ),
        'flask': re.compile(
            r"""(?:\{\{\s*url_for\(|from\s+flask\s+import)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'rails': re.compile(
            r"""(?:<%=?\s*|\.erb\b|rails\.|turbo-frame\s)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'laravel': re.compile(
            r"""(?:@csrf|@section|@extends|\.blade\.php|Livewire)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'fastapi': re.compile(
            r"""(?:from\s+fastapi|FastAPI\(\)|Jinja2Templates)""",
            re.MULTILINE
        ),
        'go_templ': re.compile(
            r"""(?:templ\s+\w+\(|\.templ\b|echo\.Context|gin\.H\{)""",
            re.MULTILINE
        ),
        'aspnet': re.compile(
            r"""(?:@Html\.|asp-route|\.cshtml|\.razor)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'spring': re.compile(
            r"""(?:th:|xmlns:th=|thymeleaf)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'phoenix': re.compile(
            r"""(?:phx-|LiveView|\.heex\b|~H\[)""",
            re.MULTILINE
        ),

        # ── Frontend libraries ───────────────────────────────────
        'alpinejs': re.compile(
            r"""(?:x-data\s*=|from\s+['"]alpinejs['"]|Alpine\.)""",
            re.MULTILINE
        ),
        'tailwind': re.compile(
            r"""(?:tailwindcss|@tailwind\s|class="[^"]*(?:flex|grid|text-|bg-|p-\d|m-\d|w-\d|h-\d))""",
            re.MULTILINE
        ),

        # ── HTMX extensions (official) ──────────────────────────
        'htmx-sse': re.compile(
            r"""(?:hx-ext="[^"]*sse|sse-connect\s*=)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'htmx-ws': re.compile(
            r"""(?:hx-ext="[^"]*ws|ws-connect\s*=)""",
            re.MULTILINE | re.IGNORECASE
        ),
        'htmx-json-enc': re.compile(
            r"""hx-ext="[^"]*json-enc""",
            re.MULTILINE
        ),
        'htmx-response-targets': re.compile(
            r"""(?:hx-ext="[^"]*response-targets|hx-target-\d)""",
            re.MULTILINE
        ),
        'htmx-preload': re.compile(
            r"""hx-ext="[^"]*preload""",
            re.MULTILINE
        ),
        'htmx-idiomorph': re.compile(
            r"""(?:hx-ext="[^"]*idiomorph|hx-swap="[^"]*morph)""",
            re.MULTILINE | re.IGNORECASE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        # Core request attributes
        'hx-get': re.compile(r"""(?:data-)?hx-get\s*=""", re.MULTILINE),
        'hx-post': re.compile(r"""(?:data-)?hx-post\s*=""", re.MULTILINE),
        'hx-put': re.compile(r"""(?:data-)?hx-put\s*=""", re.MULTILINE),
        'hx-patch': re.compile(r"""(?:data-)?hx-patch\s*=""", re.MULTILINE),
        'hx-delete': re.compile(r"""(?:data-)?hx-delete\s*=""", re.MULTILINE),

        # Swap / targeting
        'hx-swap': re.compile(r"""(?:data-)?hx-swap\s*=""", re.MULTILINE),
        'hx-target': re.compile(r"""(?:data-)?hx-target\s*=""", re.MULTILINE),
        'hx-select': re.compile(r"""(?:data-)?hx-select\s*=""", re.MULTILINE),
        'hx-select-oob': re.compile(r"""(?:data-)?hx-select-oob\s*=""", re.MULTILINE),
        'hx-swap-oob': re.compile(r"""(?:data-)?hx-swap-oob\s*=""", re.MULTILINE),

        # Navigation / history
        'hx-boost': re.compile(r"""(?:data-)?hx-boost\s*=""", re.MULTILINE),
        'hx-push-url': re.compile(r"""(?:data-)?hx-push-url\s*=""", re.MULTILINE),
        'hx-replace-url': re.compile(r"""(?:data-)?hx-replace-url\s*=""", re.MULTILINE),

        # Request modifiers
        'hx-vals': re.compile(r"""(?:data-)?hx-vals\s*=""", re.MULTILINE),
        'hx-headers': re.compile(r"""(?:data-)?hx-headers\s*=""", re.MULTILINE),
        'hx-include': re.compile(r"""(?:data-)?hx-include\s*=""", re.MULTILINE),
        'hx-params': re.compile(r"""(?:data-)?hx-params\s*=""", re.MULTILINE),
        'hx-encoding': re.compile(r"""(?:data-)?hx-encoding\s*=""", re.MULTILINE),

        # UX
        'hx-indicator': re.compile(r"""(?:data-)?hx-indicator\s*=""", re.MULTILINE),
        'hx-confirm': re.compile(r"""(?:data-)?hx-confirm\s*=""", re.MULTILINE),
        'hx-prompt': re.compile(r"""(?:data-)?hx-prompt\s*=""", re.MULTILINE),
        'hx-disable': re.compile(r"""(?:data-)?hx-disable[\s=>]""", re.MULTILINE),
        'hx-disabled-elt': re.compile(r"""(?:data-)?hx-disabled-elt\s*=""", re.MULTILINE),

        # Trigger
        'hx-trigger': re.compile(r"""(?:data-)?hx-trigger\s*=""", re.MULTILINE),

        # Sync / preservation
        'hx-sync': re.compile(r"""(?:data-)?hx-sync\s*=""", re.MULTILINE),
        'hx-preserve': re.compile(r"""(?:data-)?hx-preserve""", re.MULTILINE),
        'hx-validate': re.compile(r"""(?:data-)?hx-validate""", re.MULTILINE),

        # Inheritance
        'hx-disinherit': re.compile(r"""(?:data-)?hx-disinherit\s*=""", re.MULTILINE),
        'hx-inherit': re.compile(r"""(?:data-)?hx-inherit\s*=""", re.MULTILINE),

        # Extensions
        'hx-ext': re.compile(r"""(?:data-)?hx-ext\s*=""", re.MULTILINE),

        # Event handlers (v2)
        'hx-on': re.compile(r"""(?:data-)?hx-on:""", re.MULTILINE),

        # SSE
        'sse-connect': re.compile(r"""(?:data-)?sse-connect\s*=""", re.MULTILINE),
        'sse-swap': re.compile(r"""(?:data-)?sse-swap\s*=""", re.MULTILINE),

        # WebSocket
        'ws-connect': re.compile(r"""(?:data-)?ws-connect\s*=""", re.MULTILINE),
        'ws-send': re.compile(r"""(?:data-)?ws-send""", re.MULTILINE),

        # JS API
        'htmx_ajax': re.compile(r"""htmx\.ajax\(""", re.MULTILINE),
        'htmx_process': re.compile(r"""htmx\.process\(""", re.MULTILINE),
        'htmx_on': re.compile(r"""htmx\.on\(""", re.MULTILINE),
        'htmx_trigger': re.compile(r"""htmx\.trigger\(""", re.MULTILINE),
        'htmx_config': re.compile(r"""htmx\.config\.""", re.MULTILINE),
        'htmx_logAll': re.compile(r"""htmx\.logAll\(""", re.MULTILINE),
        'htmx_defineExtension': re.compile(r"""htmx\.defineExtension\(""", re.MULTILINE),

        # v1 legacy patterns
        'data_hx_prefix': re.compile(r"""data-hx-""", re.MULTILINE),

        # Hyperscript
        'hyperscript': re.compile(r"""(?:_\s*=\s*['"]|hyperscript\.org)""", re.MULTILINE | re.IGNORECASE),
    }

    # Version precedence
    VERSION_ORDER = ['v1', 'v2']

    def __init__(self):
        """Initialize the HTMX parser with all extractors."""
        self.attribute_extractor = HtmxAttributeExtractor()
        self.request_extractor = HtmxRequestExtractor()
        self.event_extractor = HtmxEventExtractor()
        self.extension_extractor = HtmxExtensionExtractor()
        self.api_extractor = HtmxApiExtractor()

    def is_htmx_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file contains HTMX code.

        Args:
            content: Source code content.
            file_path: Path to the source file.

        Returns:
            True if the file uses HTMX.
        """
        if not content or not content.strip():
            return False

        # Check for hx-* attributes
        if re.search(r'(?:data-)?hx-(?:get|post|put|patch|delete|swap|target|trigger|boost)\s*=', content):
            return True

        # Check for HTMX imports (JS/TS files)
        if re.search(r"""(?:from\s+['"]htmx\.org['"]|require\(['"]htmx\.org['"]\))""", content):
            return True

        # Check for htmx.* API calls
        if re.search(r'htmx\.(ajax|process|on|off|trigger|find|config|logAll|defineExtension)\s*[.(]', content):
            return True

        # Check for CDN script tag
        if re.search(r'<script[^>]*htmx[^>]*>', content, re.IGNORECASE):
            return True

        # Check for SSE/WS extension attributes
        if re.search(r'(?:sse-connect|ws-connect)\s*=', content):
            return True

        # Check for hx-on: (v2 event syntax)
        if re.search(r'hx-on:', content):
            return True

        return False

    def parse(self, content: str, file_path: str = "") -> HtmxParseResult:
        """Parse a file for HTMX usage.

        Args:
            content: Source code content.
            file_path: Path to the source file.

        Returns:
            HtmxParseResult with all extracted information.
        """
        file_type = self._detect_file_type(file_path)
        result = HtmxParseResult(file_path=file_path, file_type=file_type)

        if not content or not content.strip():
            return result

        # Run all extractors
        result.attributes = self.attribute_extractor.extract(content, file_path)
        result.requests = self.request_extractor.extract(content, file_path)
        result.events = self.event_extractor.extract(content, file_path)
        result.extensions = self.extension_extractor.extract(content, file_path)

        imports, integrations, configs, cdns = self.api_extractor.extract(content, file_path)
        result.imports = imports
        result.integrations = integrations
        result.configs = configs
        result.cdns = cdns

        # Detect frameworks and features
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)

        # Detect version
        result.htmx_version = self._detect_version(content, result)

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
        if fp.endswith('.heex'):
            return 'heex'
        if fp.endswith('.templ'):
            return 'templ'
        if fp.endswith('.cshtml') or fp.endswith('.razor'):
            return 'razor'
        return 'html'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect HTMX ecosystem frameworks in content.

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
        """Detect HTMX features used in content.

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

    def _detect_version(self, content: str, result: HtmxParseResult) -> str:
        """Detect the HTMX version from content and parse results.

        Args:
            content: Source code content.
            result: Current parse result.

        Returns:
            Version string (e.g., 'v2', 'v1').
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
        v2_features = {
            'hx-on', 'hx-disabled-elt', 'hx-inherit',
        }
        v1_features = {'data_hx_prefix'}

        detected = set(result.detected_features)

        if detected & v2_features:
            if self._version_compare('v2', version) > 0:
                version = 'v2'
        elif detected & v1_features:
            if not version:
                version = 'v1'
        elif any(f in detected for f in (
            'hx-get', 'hx-post', 'hx-swap', 'hx-target', 'hx-trigger',
            'hx-boost',
        )):
            if not version:
                version = 'v1'  # Default to v1 if basic attrs found but no v2 features

        # Import-based detection (npm package htmx.org)
        for imp in result.imports:
            src = imp.source
            # Check for v2 in import path
            if '2' in src:
                if self._version_compare('v2', version) > 0:
                    version = 'v2'
            elif 'htmx' in src and not version:
                version = 'v1'

        # hx-on:event (v2 exclusive syntax)
        for evt in result.events:
            if evt.version_hint == 'v2':
                if self._version_compare('v2', version) > 0:
                    version = 'v2'
                break

        # Attribute version hints
        for attr in result.attributes:
            if attr.version_hint == 'v2':
                if self._version_compare('v2', version) > 0:
                    version = 'v2'
                break

        return version

    def _version_compare(self, v1: str, v2: str) -> int:
        """Compare two version strings.

        Args:
            v1: First version (e.g., 'v2').
            v2: Second version (e.g., 'v1').

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
