"""
EnhancedHapiParser v1.0 - Comprehensive Hapi.js parser using all extractors.

This parser integrates all Hapi extractors to provide complete parsing of
@hapi/hapi application files. It runs as a supplementary layer on top of the
JavaScript/TypeScript parsers, extracting Hapi-specific semantics.

Supports:
- @hapi/hapi v17.x (initial scoped packages, async/await API, server.register)
- @hapi/hapi v18.x (improved TypeScript support, ESM start)
- @hapi/hapi v19.x (node 12+ requirement, security updates)
- @hapi/hapi v20.x (node 14+ requirement, improved perf)
- @hapi/hapi v21.x (node 16+ requirement, modern ES features)
- Legacy hapi (pre-v17, require('hapi'), connection-based)

Hapi-specific extraction:
- Routes: server.route({ method, path, handler, options })
- Plugins: server.register(), plugin lifecycle, dependencies
- Auth: server.auth.strategy/scheme/default, JWT/cookie/bearer/basic/bell
- Server: server config, catbox caching, server.method, ext points
- Validation: Joi schemas on params/query/payload/headers
- Decorations: server.decorate(), request decorators

Framework detection (25+ Hapi ecosystem patterns):
- Core: @hapi/hapi, @hapi/boom, @hapi/joi, @hapi/hoek
- Plugins: @hapi/inert, @hapi/vision, @hapi/cookie, @hapi/bell
- Auth: @hapi/jwt, @hapi/basic, hapi-auth-jwt2, hapi-auth-bearer-token
- Cache: @hapi/catbox, catbox-redis, catbox-memcached
- Community: hapi-swagger, hapi-pino, schmervice, haute-couture

Optional AST support via tree-sitter-typescript / tree-sitter-javascript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.85 - Hapi Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Hapi extractors
from .extractors.hapi import (
    HapiRouteExtractor, HapiRouteInfo, HapiRouteConfigInfo, HapiValidationInfo,
    HapiPluginExtractor, HapiPluginInfo, HapiPluginDependencyInfo,
    HapiAuthExtractor, HapiAuthStrategyInfo, HapiAuthSchemeInfo, HapiAuthScopeInfo,
    HapiServerExtractor, HapiServerConfigInfo, HapiCacheInfo, HapiServerMethodInfo, HapiExtPointInfo,
    HapiApiExtractor, HapiImportInfo, HapiApiSummary,
)


@dataclass
class HapiParseResult:
    """Complete parse result for a Hapi file."""
    file_path: str
    file_type: str = "route"    # route, plugin, auth, server, config, test

    # Routes
    routes: List[HapiRouteInfo] = field(default_factory=list)

    # Plugins
    plugins: List[HapiPluginInfo] = field(default_factory=list)
    plugin_dependencies: List[HapiPluginDependencyInfo] = field(default_factory=list)

    # Auth
    auth_strategies: List[HapiAuthStrategyInfo] = field(default_factory=list)
    auth_schemes: List[HapiAuthSchemeInfo] = field(default_factory=list)
    default_auth_strategy: str = ""

    # Server
    server_config: Optional[HapiServerConfigInfo] = None
    caches: List[HapiCacheInfo] = field(default_factory=list)
    server_methods: List[HapiServerMethodInfo] = field(default_factory=list)
    ext_points: List[HapiExtPointInfo] = field(default_factory=list)

    # API
    imports: List[HapiImportInfo] = field(default_factory=list)
    api_summary: Optional[HapiApiSummary] = None

    # Aggregate signals
    detected_frameworks: List[str] = field(default_factory=list)
    hapi_version: str = ""
    is_typescript: bool = False
    is_legacy: bool = False     # pre-v17 hapi
    total_routes: int = 0
    total_plugins: int = 0
    total_strategies: int = 0


class EnhancedHapiParser:
    """
    Enhanced Hapi parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript/TypeScript parsers
    when Hapi framework is detected. It extracts Hapi-specific semantics
    that the language parsers cannot capture.

    Optional AST: tree-sitter-typescript / tree-sitter-javascript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Hapi ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ─────────────────────────────────────────────────
        '@hapi/hapi': re.compile(
            r"from\s+['\"]@hapi/hapi['\"]|require\(['\"]@hapi/hapi['\"]\)|"
            r"Hapi\.server\s*\(|new\s+Hapi\.Server\s*\(",
            re.MULTILINE,
        ),
        'hapi-legacy': re.compile(
            r"require\(['\"]hapi['\"]\)|from\s+['\"]hapi['\"]",
            re.MULTILINE,
        ),
        '@hapi/boom': re.compile(
            r"from\s+['\"]@hapi/boom['\"]|require\(['\"]@hapi/boom['\"]\)|Boom\.\w+\(",
            re.MULTILINE,
        ),
        '@hapi/joi': re.compile(
            r"from\s+['\"]@hapi/joi['\"]|require\(['\"]@hapi/joi['\"]\)|Joi\.\w+\(",
            re.MULTILINE,
        ),
        'joi': re.compile(
            r"from\s+['\"]joi['\"]|require\(['\"]joi['\"]\)",
            re.MULTILINE,
        ),
        '@hapi/hoek': re.compile(
            r"from\s+['\"]@hapi/hoek['\"]|require\(['\"]@hapi/hoek['\"]\)",
            re.MULTILINE,
        ),

        # ── Plugins ──────────────────────────────────────────────
        '@hapi/inert': re.compile(
            r"from\s+['\"]@hapi/inert['\"]|require\(['\"]@hapi/inert['\"]\)",
            re.MULTILINE,
        ),
        '@hapi/vision': re.compile(
            r"from\s+['\"]@hapi/vision['\"]|require\(['\"]@hapi/vision['\"]\)",
            re.MULTILINE,
        ),
        '@hapi/cookie': re.compile(
            r"from\s+['\"]@hapi/cookie['\"]|require\(['\"]@hapi/cookie['\"]\)",
            re.MULTILINE,
        ),
        '@hapi/bell': re.compile(
            r"from\s+['\"]@hapi/bell['\"]|require\(['\"]@hapi/bell['\"]\)",
            re.MULTILINE,
        ),

        # ── Auth ─────────────────────────────────────────────────
        '@hapi/jwt': re.compile(
            r"from\s+['\"]@hapi/jwt['\"]|require\(['\"]@hapi/jwt['\"]\)",
            re.MULTILINE,
        ),
        '@hapi/basic': re.compile(
            r"from\s+['\"]@hapi/basic['\"]|require\(['\"]@hapi/basic['\"]\)",
            re.MULTILINE,
        ),
        'hapi-auth-jwt2': re.compile(
            r"from\s+['\"]hapi-auth-jwt2['\"]|require\(['\"]hapi-auth-jwt2['\"]\)",
            re.MULTILINE,
        ),
        'hapi-auth-bearer-token': re.compile(
            r"from\s+['\"]hapi-auth-bearer-token['\"]|require\(['\"]hapi-auth-bearer-token['\"]\)",
            re.MULTILINE,
        ),

        # ── Cache ────────────────────────────────────────────────
        '@hapi/catbox': re.compile(
            r"from\s+['\"]@hapi/catbox['\"]|require\(['\"]@hapi/catbox['\"]\)",
            re.MULTILINE,
        ),
        'catbox-redis': re.compile(
            r"from\s+['\"](?:@hapi/)?catbox-redis['\"]|require\(['\"](?:@hapi/)?catbox-redis['\"]\)",
            re.MULTILINE,
        ),
        'catbox-memcached': re.compile(
            r"from\s+['\"](?:@hapi/)?catbox-memcached['\"]",
            re.MULTILINE,
        ),

        # ── WebSocket ────────────────────────────────────────────
        '@hapi/nes': re.compile(
            r"from\s+['\"]@hapi/nes['\"]|require\(['\"]@hapi/nes['\"]\)",
            re.MULTILINE,
        ),

        # ── Community ────────────────────────────────────────────
        'hapi-swagger': re.compile(
            r"from\s+['\"]hapi-swagger['\"]|require\(['\"]hapi-swagger['\"]\)",
            re.MULTILINE,
        ),
        'hapi-pino': re.compile(
            r"from\s+['\"]hapi-pino['\"]|require\(['\"]hapi-pino['\"]\)",
            re.MULTILINE,
        ),
        'schmervice': re.compile(
            r"from\s+['\"]schmervice['\"]|require\(['\"]schmervice['\"]\)",
            re.MULTILINE,
        ),
        'haute-couture': re.compile(
            r"from\s+['\"]haute-couture['\"]|require\(['\"]haute-couture['\"]\)",
            re.MULTILINE,
        ),
        '@hapi/glue': re.compile(
            r"from\s+['\"]@hapi/glue['\"]|require\(['\"]@hapi/glue['\"]\)|Glue\.compose\(",
            re.MULTILINE,
        ),

        # ── HTTP client ──────────────────────────────────────────
        '@hapi/wreck': re.compile(
            r"from\s+['\"]@hapi/wreck['\"]|require\(['\"]@hapi/wreck['\"]\)|Wreck\.\w+\(",
            re.MULTILINE,
        ),

        # ── Testing ──────────────────────────────────────────────
        '@hapi/lab': re.compile(
            r"from\s+['\"]@hapi/lab['\"]|require\(['\"]@hapi/lab['\"]\)",
            re.MULTILINE,
        ),
        '@hapi/code': re.compile(
            r"from\s+['\"]@hapi/code['\"]|require\(['\"]@hapi/code['\"]\)",
            re.MULTILINE,
        ),
    }

    # Version detection from patterns
    HAPI_VERSION_FEATURES = {
        # Legacy (pre-v17): connection-based, callback API
        'server.connection': 'pre-17',
        'server.start(function': 'pre-17',
        'reply(': 'pre-17',
        'reply.continue': 'pre-17',
        # v17+: async/await, scoped packages
        '@hapi/hapi': '17',
        'Hapi.server(': '17',
        'await server.start': '17',
        'h.response': '17',
        'h.continue': '17',
        # v20+: improved server.options
        '@hapi/jwt': '20',
        # v21+: Node 16+ only
        'structuredClone': '21',
    }

    def __init__(self):
        """Initialize the parser with all Hapi extractors."""
        self.route_extractor = HapiRouteExtractor()
        self.plugin_extractor = HapiPluginExtractor()
        self.auth_extractor = HapiAuthExtractor()
        self.server_extractor = HapiServerExtractor()
        self.api_extractor = HapiApiExtractor()

    def parse(self, content: str, file_path: str = "") -> HapiParseResult:
        """
        Parse Hapi source code and extract all Hapi-specific information.

        This should be called AFTER the JS/TS parsers have run, when
        Hapi framework is detected.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            HapiParseResult with all extracted Hapi information
        """
        result = HapiParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # TypeScript detection
        result.is_typescript = file_path.endswith(('.ts', '.tsx'))

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Legacy detection
        result.is_legacy = self._is_legacy_hapi(content)

        # ── Routes ───────────────────────────────────────────────
        route_result = self.route_extractor.extract(content, file_path)
        result.routes = route_result.get('routes', [])
        result.total_routes = len(result.routes)

        # ── Plugins ──────────────────────────────────────────────
        plugin_result = self.plugin_extractor.extract(content, file_path)
        result.plugins = plugin_result.get('plugins', [])
        result.plugin_dependencies = plugin_result.get('dependencies', [])
        result.total_plugins = len(result.plugins)

        # ── Auth ─────────────────────────────────────────────────
        auth_result = self.auth_extractor.extract(content, file_path)
        result.auth_strategies = auth_result.get('strategies', [])
        result.auth_schemes = auth_result.get('schemes', [])
        result.default_auth_strategy = auth_result.get('default_strategy', '')
        result.total_strategies = len(result.auth_strategies)

        # ── Server Config ────────────────────────────────────────
        server_result = self.server_extractor.extract(content, file_path)
        result.server_config = server_result.get('config')
        result.caches = server_result.get('caches', [])
        result.server_methods = server_result.get('methods', [])
        result.ext_points = server_result.get('ext_points', [])

        # ── API / Imports ────────────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.imports = api_result.get('imports', [])
        result.api_summary = api_result.get('summary')

        # ── Version detection ────────────────────────────────────
        result.hapi_version = self._detect_hapi_version(content)

        # Update API summary with totals
        if result.api_summary:
            result.api_summary.total_routes = result.total_routes
            result.api_summary.total_plugins = result.total_plugins
            result.api_summary.total_strategies = result.total_strategies
            result.api_summary.total_methods = len(result.server_methods)
            result.api_summary.total_ext_points = len(result.ext_points)

        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a Hapi file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        # By filename conventions
        if 'route' in basename:
            return 'route'
        if 'plugin' in basename:
            return 'plugin'
        if 'auth' in basename:
            return 'auth'
        if 'server' in basename:
            return 'server'
        if 'config' in basename:
            return 'config'
        if 'test' in basename or 'spec' in basename:
            return 'test'

        # By directory conventions
        if '/routes/' in normalized or '/route/' in normalized:
            return 'route'
        if '/plugins/' in normalized or '/plugin/' in normalized:
            return 'plugin'
        if '/auth/' in normalized:
            return 'auth'

        # By content
        if 'server.route(' in content:
            return 'route'
        if 'server.register(' in content:
            return 'plugin'
        if 'server.auth.' in content:
            return 'auth'
        if 'Hapi.server(' in content or 'new Hapi.Server(' in content:
            return 'server'
        if 'exports.plugin' in content or 'module.exports' in content:
            if 'register' in content:
                return 'plugin'

        return 'route'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Hapi ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_hapi_version(self, content: str) -> str:
        """
        Detect the Hapi version based on code patterns.

        Returns version string (e.g., '21', '17', 'pre-17').
        """
        max_version = ''

        for feature, version in self.HAPI_VERSION_FEATURES.items():
            if feature in content:
                if version == 'pre-17':
                    if not max_version or max_version == 'pre-17':
                        max_version = 'pre-17'
                else:
                    version_num = int(version)
                    if not max_version or max_version == 'pre-17':
                        max_version = version
                    elif max_version != 'pre-17':
                        if version_num > int(max_version):
                            max_version = version

        return max_version

    def _is_legacy_hapi(self, content: str) -> bool:
        """Check if the file uses legacy (pre-v17) Hapi patterns."""
        legacy_signals = [
            'server.connection(',
            'reply(',
            'reply.continue',
            "require('hapi')",
            'require("hapi")',
        ]
        return any(signal in content for signal in legacy_signals)

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            for a, b in zip(parts1, parts2):
                if a != b:
                    return a - b
            return len(parts1) - len(parts2)
        except (ValueError, AttributeError):
            return 0

    def is_hapi_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a Hapi-specific file worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file contains Hapi-specific patterns
        """
        # @hapi/* imports
        if re.search(r"from\s+['\"]@hapi/", content):
            return True

        # Legacy hapi import
        if re.search(r"require\(['\"]hapi['\"]\)|from\s+['\"]hapi['\"]", content):
            return True

        # Hapi server creation
        if re.search(r'Hapi\.server\s*\(|new\s+Hapi\.Server\s*\(', content):
            return True

        # server.route() — core Hapi pattern
        if re.search(r'server\.route\s*\(', content):
            return True

        # server.register() — plugin system
        if re.search(r'server\.register\s*\(', content):
            return True

        # server.auth.strategy/scheme
        if re.search(r'server\.auth\.(?:strategy|scheme|default)\s*\(', content):
            return True

        # server.ext() — lifecycle hooks
        if re.search(r'server\.ext\s*\(', content):
            return True

        # server.method() — server methods
        if re.search(r'server\.method\s*\(', content):
            return True

        # Plugin definition: exports.plugin = { name, register }
        if re.search(r'exports\.plugin\s*=\s*\{[^}]*register', content, re.DOTALL):
            return True

        # Boom error objects
        if re.search(r'Boom\.\w+\(', content):
            if re.search(r"@hapi/boom|require\(['\"]boom['\"]\)", content):
                return True

        # Joi validation
        if re.search(r"from\s+['\"]@hapi/joi['\"]|require\(['\"]@hapi/joi['\"]\)", content):
            return True

        # hapi-* community plugins
        if re.search(r"from\s+['\"]hapi-|require\(['\"]hapi-", content):
            return True

        # @hapi/glue compose
        if re.search(r'Glue\.compose\(', content):
            return True

        return False
