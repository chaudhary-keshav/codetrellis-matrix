"""
EnhancedAdonisJSParser v1.0 - Comprehensive AdonisJS parser using all extractors.

This parser integrates all AdonisJS extractors to provide complete parsing of
AdonisJS application files. It runs as a supplementary layer on top of the
JavaScript/TypeScript parsers, extracting AdonisJS-specific semantics.

Supports:
- AdonisJS v4.x (legacy, CommonJS, class-based, use() imports)
- AdonisJS v5.x (TypeScript-first, IoC container, decorators, @ioc: imports)
- AdonisJS v6.x (ESM, Vite, subpath imports #, vine validators, edge 6)

AdonisJS-specific extraction:
- Routes: Route.get/post/resource/group, route params, middleware, naming
- Controllers: class-based, actions (CRUD), DI, validators
- Middleware: global, named, route middleware, kernel config
- Models: Lucid ORM, relationships, hooks, computed, scopes, soft deletes
- Auth: auth middleware, guards, providers
- Providers: service providers, IoC container bindings
- Validators: Joi (v4), schema (v5), vine (v6) validators

Framework detection (30+ AdonisJS ecosystem patterns):
- Core: @adonisjs/core, @adonisjs/http-server, @adonisjs/router
- ORM: @adonisjs/lucid, BaseModel, relationships, hooks
- Auth: @adonisjs/auth, guards, providers
- Security: @adonisjs/shield, @adonisjs/bouncer
- Services: @adonisjs/mail, @adonisjs/drive, @adonisjs/ally
- Real-time: @adonisjs/transmit, @adonisjs/redis
- Build: @adonisjs/vite, @adonisjs/assembler

Optional AST support via tree-sitter-typescript / tree-sitter-javascript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.85 - AdonisJS Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all AdonisJS extractors
from .extractors.adonisjs import (
    AdonisRouteExtractor, AdonisRouteInfo, AdonisRouteGroupInfo, AdonisResourceRouteInfo,
    AdonisControllerExtractor, AdonisControllerInfo, AdonisActionInfo,
    AdonisMiddlewareExtractor, AdonisMiddlewareInfo, AdonisMiddlewareKernelInfo,
    AdonisModelExtractor, AdonisModelInfo, AdonisRelationshipInfo, AdonisModelHookInfo,
    AdonisApiExtractor, AdonisImportInfo, AdonisProviderInfo, AdonisApiSummary,
)


@dataclass
class AdonisJSParseResult:
    """Complete parse result for an AdonisJS file."""
    file_path: str
    file_type: str = "route"    # route, controller, middleware, model, provider, config, validator, test

    # Routes
    routes: List[AdonisRouteInfo] = field(default_factory=list)
    route_groups: List[AdonisRouteGroupInfo] = field(default_factory=list)
    resource_routes: List[AdonisResourceRouteInfo] = field(default_factory=list)

    # Controllers
    controllers: List[AdonisControllerInfo] = field(default_factory=list)

    # Middleware
    middleware: List[AdonisMiddlewareInfo] = field(default_factory=list)
    middleware_kernel: Optional[AdonisMiddlewareKernelInfo] = None

    # Models
    models: List[AdonisModelInfo] = field(default_factory=list)

    # API
    imports: List[AdonisImportInfo] = field(default_factory=list)
    providers: List[AdonisProviderInfo] = field(default_factory=list)
    api_summary: Optional[AdonisApiSummary] = None

    # Aggregate signals
    detected_frameworks: List[str] = field(default_factory=list)
    adonis_version: str = ""
    is_typescript: bool = False
    is_legacy: bool = False     # v4
    total_routes: int = 0
    total_controllers: int = 0
    total_models: int = 0
    total_middleware: int = 0


class EnhancedAdonisJSParser:
    """
    Enhanced AdonisJS parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript/TypeScript parsers
    when AdonisJS framework is detected. It extracts AdonisJS-specific semantics
    that the language parsers cannot capture.

    Optional AST: tree-sitter-typescript / tree-sitter-javascript
    Optional LSP: typescript-language-server (tsserver)
    """

    # AdonisJS ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ─────────────────────────────────────────────────
        '@adonisjs/core': re.compile(
            r"from\s+['\"]@adonisjs/core['\"/]|require\(['\"]@adonisjs/core['\"]\)",
            re.MULTILINE,
        ),
        '@adonisjs/http-server': re.compile(
            r"from\s+['\"]@adonisjs/http-server['\"]|HttpContext",
            re.MULTILINE,
        ),
        '@adonisjs/router': re.compile(
            r"from\s+['\"]@adonisjs/router['\"]|Route\.\w+\s*\(",
            re.MULTILINE,
        ),
        'adonis-v4': re.compile(
            r"use\s*\(\s*['\"]Adonis/|use\s*\(\s*['\"]App/|"
            r"require\(['\"]@adonisjs/framework['\"]\)",
            re.MULTILINE,
        ),

        # ── ORM ──────────────────────────────────────────────────
        '@adonisjs/lucid': re.compile(
            r"from\s+['\"]@adonisjs/lucid['\"/]|extends\s+BaseModel|"
            r"use\s*\(\s*['\"]Database['\"]",
            re.MULTILINE,
        ),

        # ── Auth ─────────────────────────────────────────────────
        '@adonisjs/auth': re.compile(
            r"from\s+['\"]@adonisjs/auth['\"/]|auth\.\w+\s*\(|AuthMiddleware",
            re.MULTILINE,
        ),

        # ── Security ────────────────────────────────────────────
        '@adonisjs/shield': re.compile(
            r"from\s+['\"]@adonisjs/shield['\"]",
            re.MULTILINE,
        ),
        '@adonisjs/bouncer': re.compile(
            r"from\s+['\"]@adonisjs/bouncer['\"]|bouncer\.\w+\(",
            re.MULTILINE,
        ),

        # ── Services ────────────────────────────────────────────
        '@adonisjs/mail': re.compile(
            r"from\s+['\"]@adonisjs/mail['\"]|Mail\.send\(",
            re.MULTILINE,
        ),
        '@adonisjs/drive': re.compile(
            r"from\s+['\"]@adonisjs/drive['\"]|Drive\.\w+\(",
            re.MULTILINE,
        ),
        '@adonisjs/ally': re.compile(
            r"from\s+['\"]@adonisjs/ally['\"]|ally\.\w+\(",
            re.MULTILINE,
        ),
        '@adonisjs/redis': re.compile(
            r"from\s+['\"]@adonisjs/redis['\"]|Redis\.\w+\(",
            re.MULTILINE,
        ),

        # ── Session ──────────────────────────────────────────────
        '@adonisjs/session': re.compile(
            r"from\s+['\"]@adonisjs/session['\"]|session\.\w+\(",
            re.MULTILINE,
        ),

        # ── Views ────────────────────────────────────────────────
        '@adonisjs/view': re.compile(
            r"from\s+['\"]@adonisjs/view['\"]|view\.render\(",
            re.MULTILINE,
        ),
        'edge': re.compile(
            r"from\s+['\"]edge\.js['\"]|edge\.\w+\(",
            re.MULTILINE,
        ),
        '@adonisjs/inertia': re.compile(
            r"from\s+['\"]@adonisjs/inertia['\"]|inertia\.render\(",
            re.MULTILINE,
        ),

        # ── Real-time ───────────────────────────────────────────
        '@adonisjs/transmit': re.compile(
            r"from\s+['\"]@adonisjs/transmit['\"]|transmit\.\w+\(",
            re.MULTILINE,
        ),

        # ── i18n ─────────────────────────────────────────────────
        '@adonisjs/i18n': re.compile(
            r"from\s+['\"]@adonisjs/i18n['\"]",
            re.MULTILINE,
        ),

        # ── Build ────────────────────────────────────────────────
        '@adonisjs/vite': re.compile(
            r"from\s+['\"]@adonisjs/vite['\"]",
            re.MULTILINE,
        ),
        '@adonisjs/assembler': re.compile(
            r"from\s+['\"]@adonisjs/assembler['\"]",
            re.MULTILINE,
        ),

        # ── Testing ──────────────────────────────────────────────
        '@japa/runner': re.compile(
            r"from\s+['\"]@japa/runner['\"]|test\.\w+\(",
            re.MULTILINE,
        ),
        '@japa/browser-client': re.compile(
            r"from\s+['\"]@japa/browser-client['\"]",
            re.MULTILINE,
        ),

        # ── Validation ──────────────────────────────────────────
        'vine': re.compile(
            r"vine\.compile|vine\.\w+\(|from\s+['\"]@vinejs/vine['\"]",
            re.MULTILINE,
        ),
        '@adonisjs/validator': re.compile(
            r"from\s+['\"]@adonisjs/validator['\"]|schema\.\w+\(",
            re.MULTILINE,
        ),

        # ── Limiter ──────────────────────────────────────────────
        '@adonisjs/limiter': re.compile(
            r"from\s+['\"]@adonisjs/limiter['\"]|limiter\.\w+\(",
            re.MULTILINE,
        ),

        # ── Health ───────────────────────────────────────────────
        '@adonisjs/health': re.compile(
            r"from\s+['\"]@adonisjs/health['\"]",
            re.MULTILINE,
        ),
    }

    # Version detection from features/patterns
    ADONIS_VERSION_FEATURES = {
        # v4 features
        "use('App/": 'v4',
        "use('Adonis/": 'v4',
        'module.exports = class': 'v4',
        'Route.on(': 'v4',
        'Route.render(': 'v4',
        # v5 features
        '@ioc:': 'v5',
        'ApplicationContract': 'v5',
        'HttpContextContract': 'v5',
        # v6 features
        'vine.compile': 'v6',
        '@adonisjs/vite': 'v6',
        "from '#": 'v6',  # subpath imports
        'defineConfig': 'v6',
    }

    def __init__(self):
        """Initialize the parser with all AdonisJS extractors."""
        self.route_extractor = AdonisRouteExtractor()
        self.controller_extractor = AdonisControllerExtractor()
        self.middleware_extractor = AdonisMiddlewareExtractor()
        self.model_extractor = AdonisModelExtractor()
        self.api_extractor = AdonisApiExtractor()

    def parse(self, content: str, file_path: str = "") -> AdonisJSParseResult:
        """
        Parse AdonisJS source code and extract all AdonisJS-specific information.

        This should be called AFTER the JS/TS parsers have run, when
        AdonisJS framework is detected.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            AdonisJSParseResult with all extracted information
        """
        result = AdonisJSParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # TypeScript detection
        result.is_typescript = file_path.endswith(('.ts', '.tsx'))

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Legacy detection
        result.is_legacy = self._is_legacy_adonis(content)

        # ── Routes ───────────────────────────────────────────────
        route_result = self.route_extractor.extract(content, file_path)
        result.routes = route_result.get('routes', [])
        result.route_groups = route_result.get('groups', [])
        result.resource_routes = route_result.get('resources', [])
        result.total_routes = len(result.routes)

        # ── Controllers ──────────────────────────────────────────
        ctrl_result = self.controller_extractor.extract(content, file_path)
        result.controllers = ctrl_result.get('controllers', [])
        result.total_controllers = len(result.controllers)

        # ── Middleware ────────────────────────────────────────────
        mw_result = self.middleware_extractor.extract(content, file_path)
        result.middleware = mw_result.get('middleware', [])
        result.middleware_kernel = mw_result.get('kernel')
        result.total_middleware = len(result.middleware)

        # ── Models ───────────────────────────────────────────────
        model_result = self.model_extractor.extract(content, file_path)
        result.models = model_result.get('models', [])
        result.total_models = len(result.models)

        # ── API / Imports ────────────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.imports = api_result.get('imports', [])
        result.providers = api_result.get('providers', [])
        result.api_summary = api_result.get('summary')

        # ── Version detection ────────────────────────────────────
        result.adonis_version = self._detect_adonis_version(content)

        # Update API summary with totals
        if result.api_summary:
            result.api_summary.total_routes = result.total_routes
            result.api_summary.total_controllers = result.total_controllers
            result.api_summary.total_models = result.total_models
            result.api_summary.total_middleware = result.total_middleware

        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify an AdonisJS file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        # By directory conventions (AdonisJS has strict directory structure)
        if '/routes/' in normalized or '/start/routes' in normalized:
            return 'route'
        if '/controllers/' in normalized or 'controller' in basename:
            return 'controller'
        if '/middleware/' in normalized or 'middleware' in basename:
            return 'middleware'
        if '/models/' in normalized or 'model' in basename:
            return 'model'
        if '/providers/' in normalized or 'provider' in basename:
            return 'provider'
        if '/validators/' in normalized or 'validator' in basename:
            return 'validator'
        if '/config/' in normalized:
            return 'config'
        if 'kernel' in basename:
            return 'middleware'  # kernel is middleware config
        if '/tests/' in normalized or '/test/' in normalized or 'test' in basename or 'spec' in basename:
            return 'test'

        # By content
        if 'Route.get(' in content or 'Route.post(' in content or 'Route.resource(' in content:
            return 'route'
        if 'router.get(' in content or 'router.post(' in content:
            return 'route'
        if 'Controller' in basename:
            return 'controller'
        if 'extends BaseModel' in content or 'extends Model' in content:
            return 'model'
        if 'Middleware' in basename or 'async handle(' in content:
            return 'middleware'

        return 'route'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which AdonisJS ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_adonis_version(self, content: str) -> str:
        """
        Detect the AdonisJS version based on code patterns.

        Returns version string (e.g., 'v6', 'v5', 'v4').
        """
        # Check from newest to oldest
        for feature, version in self.ADONIS_VERSION_FEATURES.items():
            if feature in content:
                if version == 'v6':
                    return 'v6'

        for feature, version in self.ADONIS_VERSION_FEATURES.items():
            if feature in content:
                if version == 'v5':
                    return 'v5'

        for feature, version in self.ADONIS_VERSION_FEATURES.items():
            if feature in content:
                if version == 'v4':
                    return 'v4'

        return ''

    def _is_legacy_adonis(self, content: str) -> bool:
        """Check if the file uses legacy (v4) AdonisJS patterns."""
        legacy_signals = [
            "use('App/",
            "use('Adonis/",
            'module.exports = class',
            "const { ServiceProvider }",
        ]
        return any(signal in content for signal in legacy_signals)

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        try:
            n1 = int(v1.replace('v', ''))
            n2 = int(v2.replace('v', ''))
            return n1 - n2
        except (ValueError, AttributeError):
            return 0

    def is_adonisjs_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is an AdonisJS-specific file worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file contains AdonisJS-specific patterns
        """
        # @adonisjs/* imports
        if re.search(r"from\s+['\"]@adonisjs/", content):
            return True

        # v4 use() imports
        if re.search(r"use\s*\(\s*['\"](?:App/|Adonis/)", content):
            return True

        # v6 subpath imports (#controllers/, #models/, etc.)
        if re.search(r"from\s+['\"]#(?:controllers|models|middleware|validators|services)/", content):
            return True

        # Route definitions
        if re.search(r'Route\.(?:get|post|put|patch|delete|resource|group)\s*\(', content):
            return True

        # router.* (v6)
        if re.search(r'router\.(?:get|post|put|patch|delete|resource|group)\s*\(', content):
            return True

        # AdonisJS controller pattern
        if re.search(r'class\s+\w+Controller\s+', content):
            if re.search(r'HttpContext|request\.|response\.|auth\.', content):
                return True

        # Lucid model
        if re.search(r'extends\s+BaseModel\s*\{', content):
            return True

        # AdonisJS middleware
        if re.search(r'class\s+\w+Middleware\s*\{', content):
            if re.search(r'handle\s*\(', content):
                return True

        # Middleware kernel
        if re.search(r'Server\.middleware\.register|router\.named\s*\(', content):
            return True

        # @japa test runner
        if re.search(r"from\s+['\"]@japa/runner['\"]", content):
            return True

        # Vine validator (v6)
        if re.search(r'vine\.compile|vine\.\w+\(', content):
            return True

        # AdonisJS config files
        if re.search(r"from\s+['\"]@adonisjs/core/.*defineConfig['\"]", content):
            return True

        # Edge templates reference
        if re.search(r"view\.render\s*\(|response\.download\s*\(", content):
            if re.search(r"@adonisjs/", content):
                return True

        # Check file path for AdonisJS conventions
        if file_path:
            lower_path = file_path.lower().replace('\\', '/')
            adonis_dirs = [
                '/app/controllers/', '/app/models/', '/app/middleware/',
                '/app/validators/', '/app/services/', '/app/policies/',
                '/start/routes', '/start/kernel', '/config/',
                '/providers/',
            ]
            if any(d in lower_path for d in adonis_dirs):
                # Additional check: must have some AdonisJS signal
                if re.search(r'@adonisjs/|HttpContext|BaseModel|Route\.|router\.', content):
                    return True

        return False
