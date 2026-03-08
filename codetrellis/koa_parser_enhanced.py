"""
EnhancedKoaParser v1.0 - Comprehensive Koa.js parser using all extractors.

This parser integrates all Koa.js extractors to provide complete parsing of
Koa.js application files. It runs as a supplementary layer on top of the
JavaScript/TypeScript parsers, extracting Koa.js-specific semantics.

Supports:
- Koa v1.x (generator middleware via co, this.body, this.status, this.throw,
             generator-based flow control, koa-route, koa-router v5-v7)
- Koa v2.x (async/await middleware, ctx.body, ctx.status, ctx.throw,
             @koa/router v8-v13, koa-router v7+, modern middleware composition,
             cascading middleware, context delegation, koa-compose)

Koa-specific extraction:
- Routes: koa-router, @koa/router, koa-route, koa-tree-router, koa-better-router
- Middleware: app.use(), koa-compose, global/route middleware, ordering
- Context: ctx.body, ctx.status, ctx.throw, ctx.assert, ctx.state, ctx.cookies,
           ctx.request, ctx.response, custom context extensions
- Configuration: app.keys, app.proxy, app.subdomainOffset, app.env, listen()
- API Patterns: RESTful resources, versioning, imports, ecosystem packages

Framework detection (30+ Koa ecosystem patterns):
- Core: koa, @koa/router, koa-router, koa-route, koa-compose, koa-convert
- Body Parsing: koa-body, koa-bodyparser, @koa/multer, koa-better-body, koa-json-body
- Security: @koa/cors, koa-helmet, koa-jwt, koa-csrf, koa-ratelimit
- Session/Auth: koa-session, koa-passport, koa-generic-session, koa-redis
- Static/Views: koa-static, koa-views, koa-ejs, koa-pug
- Logging: koa-logger, koa-morgan, koa-pino-logger
- Validation: koa-joi-router, koa-bouncer, koa-validate
- WebSockets: koa-websocket, koa-easy-ws
- Database: koa-mongoose, koa-knex
- Error: koa-json-error, koa-error, koa-onerror
- Other: koa-etag, koa-conditional-get, koa-compress, koa-mount, koa-send, koa-range

Optional AST support via tree-sitter-typescript / tree-sitter-javascript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.33 - Koa.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Koa.js extractors
from .extractors.koa import (
    KoaRouteExtractor, KoaRouteInfo, KoaRouterInfo, KoaParamInfo,
    KoaMiddlewareExtractor, KoaMiddlewareInfo, KoaMiddlewareStackInfo,
    KoaContextExtractor, KoaContextUsageInfo, KoaErrorThrowInfo, KoaCustomContextInfo,
    KoaConfigExtractor, KoaAppInfo, KoaServerInfo, KoaSettingInfo, KoaConfigSummary,
    KoaApiExtractor, KoaResourceInfo, KoaImportInfo, KoaApiSummary,
)


@dataclass
class KoaParseResult:
    """Complete parse result for a Koa.js file."""
    file_path: str
    file_type: str = "route"  # route, middleware, config, controller, model, service, app, test

    # Routes
    routes: List[KoaRouteInfo] = field(default_factory=list)
    routers: List[KoaRouterInfo] = field(default_factory=list)
    params: List[KoaParamInfo] = field(default_factory=list)

    # Middleware
    middleware: List[KoaMiddlewareInfo] = field(default_factory=list)
    middleware_stack: Optional[KoaMiddlewareStackInfo] = None

    # Context
    context_usages: List[KoaContextUsageInfo] = field(default_factory=list)
    error_throws: List[KoaErrorThrowInfo] = field(default_factory=list)
    custom_context: List[KoaCustomContextInfo] = field(default_factory=list)

    # Configuration
    settings: List[KoaSettingInfo] = field(default_factory=list)
    apps: List[KoaAppInfo] = field(default_factory=list)
    servers: List[KoaServerInfo] = field(default_factory=list)
    config_summary: Optional[KoaConfigSummary] = None

    # API Patterns
    resources: List[KoaResourceInfo] = field(default_factory=list)
    imports: List[KoaImportInfo] = field(default_factory=list)
    api_summary: Optional[KoaApiSummary] = None

    # Aggregate signals
    detected_frameworks: List[str] = field(default_factory=list)
    koa_version: str = ""  # Detected minimum Koa version
    is_typescript: bool = False
    total_routes: int = 0
    total_middleware: int = 0
    uses_generator_middleware: bool = False  # Koa v1 style


class EnhancedKoaParser:
    """
    Enhanced Koa.js parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript/TypeScript parsers
    when Koa framework is detected. It extracts Koa-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 30+ Koa ecosystem libraries across:
    - Core (koa, @koa/router, koa-router, koa-compose)
    - Body Parsing (koa-body, koa-bodyparser, @koa/multer)
    - Security (@koa/cors, koa-helmet, koa-jwt, koa-csrf)
    - Session/Auth (koa-session, koa-passport)
    - Static/Views (koa-static, koa-views, koa-ejs)
    - Logging (koa-logger, koa-morgan, koa-pino-logger)
    - Validation (koa-joi-router, koa-bouncer)
    - WebSockets (koa-websocket, koa-easy-ws)
    - Error (koa-json-error, koa-onerror)

    Optional AST: tree-sitter-typescript / tree-sitter-javascript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Koa ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core Koa ──────────────────────────────────────────────
        'koa': re.compile(
            r"from\s+['\"]koa['\"]|require\(['\"]koa['\"]\)|"
            r"new\s+Koa\s*\(",
            re.MULTILINE
        ),
        '@koa/router': re.compile(
            r"from\s+['\"]@koa/router['\"]|require\(['\"]@koa/router['\"]\)|"
            r"new\s+Router\s*\(",
            re.MULTILINE
        ),
        'koa-router': re.compile(
            r"from\s+['\"]koa-router['\"]|require\(['\"]koa-router['\"]\)",
            re.MULTILINE
        ),
        'koa-route': re.compile(
            r"from\s+['\"]koa-route['\"]|require\(['\"]koa-route['\"]\)",
            re.MULTILINE
        ),
        'koa-compose': re.compile(
            r"from\s+['\"]koa-compose['\"]|require\(['\"]koa-compose['\"]\)|"
            r"compose\s*\(\s*\[",
            re.MULTILINE
        ),
        'koa-convert': re.compile(
            r"from\s+['\"]koa-convert['\"]|require\(['\"]koa-convert['\"]\)|"
            r"convert\s*\(",
            re.MULTILINE
        ),
        'koa-mount': re.compile(
            r"from\s+['\"]koa-mount['\"]|require\(['\"]koa-mount['\"]\)|"
            r"mount\s*\(\s*['\"]",
            re.MULTILINE
        ),
        'koa-tree-router': re.compile(
            r"from\s+['\"]koa-tree-router['\"]|require\(['\"]koa-tree-router['\"]\)",
            re.MULTILINE
        ),
        'koa-better-router': re.compile(
            r"from\s+['\"]koa-better-router['\"]|require\(['\"]koa-better-router['\"]\)",
            re.MULTILINE
        ),

        # ── Body Parsing ─────────────────────────────────────────
        'koa-body': re.compile(
            r"from\s+['\"]koa-body['\"]|require\(['\"]koa-body['\"]\)|"
            r"koaBody\s*\(",
            re.MULTILINE
        ),
        'koa-bodyparser': re.compile(
            r"from\s+['\"]koa-bodyparser['\"]|require\(['\"]koa-bodyparser['\"]\)|"
            r"bodyparser\s*\(",
            re.MULTILINE
        ),
        '@koa/multer': re.compile(
            r"from\s+['\"]@koa/multer['\"]|require\(['\"]@koa/multer['\"]\)|"
            r"multer\s*\(",
            re.MULTILINE
        ),
        'koa-better-body': re.compile(
            r"from\s+['\"]koa-better-body['\"]|require\(['\"]koa-better-body['\"]\)",
            re.MULTILINE
        ),
        'koa-json-body': re.compile(
            r"from\s+['\"]koa-json-body['\"]|require\(['\"]koa-json-body['\"]\)",
            re.MULTILINE
        ),

        # ── Security ─────────────────────────────────────────────
        '@koa/cors': re.compile(
            r"from\s+['\"]@koa/cors['\"]|require\(['\"]@koa/cors['\"]\)|"
            r"cors\s*\(",
            re.MULTILINE
        ),
        'koa-helmet': re.compile(
            r"from\s+['\"]koa-helmet['\"]|require\(['\"]koa-helmet['\"]\)|"
            r"helmet\s*\(",
            re.MULTILINE
        ),
        'koa-jwt': re.compile(
            r"from\s+['\"]koa-jwt['\"]|require\(['\"]koa-jwt['\"]\)|"
            r"jwt\s*\(\s*\{",
            re.MULTILINE
        ),
        'koa-csrf': re.compile(
            r"from\s+['\"]koa-csrf['\"]|require\(['\"]koa-csrf['\"]\)|"
            r"new\s+CSRF\s*\(",
            re.MULTILINE
        ),
        'koa-ratelimit': re.compile(
            r"from\s+['\"]koa-ratelimit['\"]|require\(['\"]koa-ratelimit['\"]\)|"
            r"ratelimit\s*\(",
            re.MULTILINE
        ),

        # ── Session / Auth ───────────────────────────────────────
        'koa-session': re.compile(
            r"from\s+['\"]koa-session['\"]|require\(['\"]koa-session['\"]\)|"
            r"session\s*\(\s*(?:app|\{)",
            re.MULTILINE
        ),
        'koa-passport': re.compile(
            r"from\s+['\"]koa-passport['\"]|require\(['\"]koa-passport['\"]\)|"
            r"passport\.authenticate",
            re.MULTILINE
        ),
        'koa-generic-session': re.compile(
            r"from\s+['\"]koa-generic-session['\"]|require\(['\"]koa-generic-session['\"]\)",
            re.MULTILINE
        ),
        'koa-redis': re.compile(
            r"from\s+['\"]koa-redis['\"]|require\(['\"]koa-redis['\"]\)",
            re.MULTILINE
        ),
        'jsonwebtoken': re.compile(
            r"from\s+['\"]jsonwebtoken['\"]|require\(['\"]jsonwebtoken['\"]\)|"
            r"jwt\.sign|jwt\.verify|jwt\.decode",
            re.MULTILINE
        ),

        # ── Static / Views ───────────────────────────────────────
        'koa-static': re.compile(
            r"from\s+['\"]koa-static['\"]|require\(['\"]koa-static['\"]\)|"
            r"serve\s*\(\s*['\"]",
            re.MULTILINE
        ),
        'koa-views': re.compile(
            r"from\s+['\"]koa-views['\"]|require\(['\"]koa-views['\"]\)|"
            r"views\s*\(\s*['\"]",
            re.MULTILINE
        ),
        'koa-ejs': re.compile(
            r"from\s+['\"]koa-ejs['\"]|require\(['\"]koa-ejs['\"]\)",
            re.MULTILINE
        ),
        'koa-pug': re.compile(
            r"from\s+['\"]koa-pug['\"]|require\(['\"]koa-pug['\"]\)",
            re.MULTILINE
        ),

        # ── Logging ──────────────────────────────────────────────
        'koa-logger': re.compile(
            r"from\s+['\"]koa-logger['\"]|require\(['\"]koa-logger['\"]\)|"
            r"logger\s*\(",
            re.MULTILINE
        ),
        'koa-morgan': re.compile(
            r"from\s+['\"]koa-morgan['\"]|require\(['\"]koa-morgan['\"]\)",
            re.MULTILINE
        ),
        'koa-pino-logger': re.compile(
            r"from\s+['\"]koa-pino-logger['\"]|require\(['\"]koa-pino-logger['\"]\)",
            re.MULTILINE
        ),

        # ── Validation ───────────────────────────────────────────
        'koa-joi-router': re.compile(
            r"from\s+['\"]koa-joi-router['\"]|require\(['\"]koa-joi-router['\"]\)",
            re.MULTILINE
        ),
        'koa-bouncer': re.compile(
            r"from\s+['\"]koa-bouncer['\"]|require\(['\"]koa-bouncer['\"]\)",
            re.MULTILINE
        ),
        'koa-validate': re.compile(
            r"from\s+['\"]koa-validate['\"]|require\(['\"]koa-validate['\"]\)",
            re.MULTILINE
        ),

        # ── Database ─────────────────────────────────────────────
        'mongoose': re.compile(
            r"from\s+['\"]mongoose['\"]|require\(['\"]mongoose['\"]\)|"
            r"mongoose\.connect|mongoose\.model",
            re.MULTILINE
        ),
        'sequelize': re.compile(
            r"from\s+['\"]sequelize['\"]|require\(['\"]sequelize['\"]\)|"
            r"Sequelize",
            re.MULTILINE
        ),
        'typeorm': re.compile(
            r"from\s+['\"]typeorm['\"]|@Entity|@Column|getRepository",
            re.MULTILINE
        ),
        'prisma': re.compile(
            r"from\s+['\"]@prisma/client['\"]|PrismaClient|prisma\.\w+",
            re.MULTILINE
        ),
        'knex': re.compile(
            r"from\s+['\"]knex['\"]|require\(['\"]knex['\"]\)|knex\(",
            re.MULTILINE
        ),

        # ── WebSockets ───────────────────────────────────────────
        'koa-websocket': re.compile(
            r"from\s+['\"]koa-websocket['\"]|require\(['\"]koa-websocket['\"]\)|"
            r"websockify\s*\(",
            re.MULTILINE
        ),
        'koa-easy-ws': re.compile(
            r"from\s+['\"]koa-easy-ws['\"]|require\(['\"]koa-easy-ws['\"]\)",
            re.MULTILINE
        ),

        # ── Error Handling ───────────────────────────────────────
        'koa-json-error': re.compile(
            r"from\s+['\"]koa-json-error['\"]|require\(['\"]koa-json-error['\"]\)",
            re.MULTILINE
        ),
        'koa-onerror': re.compile(
            r"from\s+['\"]koa-onerror['\"]|require\(['\"]koa-onerror['\"]\)|"
            r"onerror\s*\(\s*app\s*\)",
            re.MULTILINE
        ),
        'koa-error': re.compile(
            r"from\s+['\"]koa-error['\"]|require\(['\"]koa-error['\"]\)",
            re.MULTILINE
        ),

        # ── Caching / ETag ───────────────────────────────────────
        'koa-etag': re.compile(
            r"from\s+['\"]koa-etag['\"]|require\(['\"]koa-etag['\"]\)",
            re.MULTILINE
        ),
        'koa-conditional-get': re.compile(
            r"from\s+['\"]koa-conditional-get['\"]|require\(['\"]koa-conditional-get['\"]\)",
            re.MULTILINE
        ),
        'koa-compress': re.compile(
            r"from\s+['\"]koa-compress['\"]|require\(['\"]koa-compress['\"]\)|"
            r"compress\s*\(",
            re.MULTILINE
        ),

        # ── File Serving ─────────────────────────────────────────
        'koa-send': re.compile(
            r"from\s+['\"]koa-send['\"]|require\(['\"]koa-send['\"]\)|"
            r"send\s*\(\s*ctx",
            re.MULTILINE
        ),
        'koa-range': re.compile(
            r"from\s+['\"]koa-range['\"]|require\(['\"]koa-range['\"]\)",
            re.MULTILINE
        ),

        # ── Testing ──────────────────────────────────────────────
        'supertest': re.compile(
            r"from\s+['\"]supertest['\"]|require\(['\"]supertest['\"]\)|"
            r"request\(app|supertest\(",
            re.MULTILINE
        ),

        # ── Process Management ───────────────────────────────────
        'pm2': re.compile(
            r"pm2|ecosystem\.config",
            re.MULTILINE
        ),
        'cluster': re.compile(
            r"require\(['\"]cluster['\"]\)|from\s+['\"]cluster['\"]|"
            r"cluster\.fork|cluster\.isMaster|cluster\.isPrimary",
            re.MULTILINE
        ),

        # ── Monitoring ───────────────────────────────────────────
        'koa-response-time': re.compile(
            r"from\s+['\"]koa-response-time['\"]|require\(['\"]koa-response-time['\"]\)",
            re.MULTILINE
        ),
    }

    # Koa version detection from features
    KOA_VERSION_FEATURES = {
        # Koa v1.x features (generator-based)
        'function *': '1.0',
        'function*': '1.0',
        'this.body': '1.0',
        'this.status': '1.0',
        'this.throw': '1.0',
        'this.redirect': '1.0',
        'this.set': '1.0',
        'this.get': '1.0',
        'this.cookies': '1.0',
        # Koa v2.x features (async/await, ctx-based)
        'ctx.body': '2.0',
        'ctx.status': '2.0',
        'ctx.throw': '2.0',
        'ctx.state': '2.0',
        'ctx.assert': '2.0',
        'ctx.respond': '2.0',
        'async (ctx': '2.0',
        'async (ctx,': '2.0',
        'async ctx =>': '2.0',
        '@koa/router': '2.0',
        'koa-convert': '2.0',
    }

    def __init__(self):
        """Initialize the parser with all Koa.js extractors."""
        self.route_extractor = KoaRouteExtractor()
        self.middleware_extractor = KoaMiddlewareExtractor()
        self.context_extractor = KoaContextExtractor()
        self.config_extractor = KoaConfigExtractor()
        self.api_extractor = KoaApiExtractor()

    def parse(self, content: str, file_path: str = "") -> KoaParseResult:
        """
        Parse Koa.js source code and extract all Koa-specific information.

        This should be called AFTER the JS/TS parsers have run, when
        Koa framework is detected. It extracts Koa-specific semantics.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            KoaParseResult with all extracted Koa information
        """
        result = KoaParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # TypeScript detection
        result.is_typescript = file_path.endswith(('.ts', '.tsx'))

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Koa v1 generator detection
        result.uses_generator_middleware = bool(
            re.search(r'function\s*\*\s*\(', content) and
            re.search(r'\bthis\s*\.\s*(?:body|status|throw|redirect)\b', content)
        )

        # ── Routes ───────────────────────────────────────────────
        route_result = self.route_extractor.extract(content, file_path)
        result.routes = route_result.get('routes', [])
        result.routers = route_result.get('routers', [])
        result.params = route_result.get('params', [])
        result.total_routes = len(result.routes)

        # ── Middleware ───────────────────────────────────────────
        mw_result = self.middleware_extractor.extract(content, file_path)
        result.middleware = mw_result.get('middleware', [])
        result.middleware_stack = mw_result.get('stack')
        result.total_middleware = len(result.middleware)

        # ── Context ──────────────────────────────────────────────
        ctx_result = self.context_extractor.extract(content, file_path)
        result.context_usages = ctx_result.get('context_usages', [])
        result.error_throws = ctx_result.get('error_throws', [])
        result.custom_context = ctx_result.get('custom_context', [])

        # ── Configuration ────────────────────────────────────────
        config_result = self.config_extractor.extract(content, file_path)
        result.settings = config_result.get('settings', [])
        result.apps = config_result.get('apps', [])
        result.servers = config_result.get('servers', [])
        result.config_summary = config_result.get('summary')

        # ── API Patterns ─────────────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.resources = api_result.get('resources', [])
        result.imports = api_result.get('imports', [])
        result.api_summary = api_result.get('summary')

        # ── Version detection ────────────────────────────────────
        result.koa_version = self._detect_koa_version(content)

        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a Koa.js file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        # By filename conventions
        if 'app.' in basename or 'server.' in basename or 'index.' in basename:
            if 'Koa' in content or 'koa' in content or 'app.listen' in content:
                return 'app'
        if 'route' in basename:
            return 'route'
        if 'middleware' in basename:
            return 'middleware'
        if 'controller' in basename:
            return 'controller'
        if 'model' in basename:
            return 'model'
        if 'service' in basename:
            return 'service'
        if 'config' in basename:
            return 'config'
        if 'test' in basename or 'spec' in basename:
            return 'test'

        # By directory conventions
        if '/routes/' in normalized or '/router/' in normalized:
            return 'route'
        if '/middleware/' in normalized or '/middlewares/' in normalized:
            return 'middleware'
        if '/controllers/' in normalized:
            return 'controller'
        if '/models/' in normalized:
            return 'model'
        if '/services/' in normalized:
            return 'service'
        if '/config/' in normalized:
            return 'config'

        # By content
        if 'Router()' in content and ('router.get' in content or 'router.post' in content):
            return 'route'
        if re.search(r'async\s*\(\s*ctx\s*,\s*next\s*\)', content):
            if 'module.exports' in content or 'export' in content:
                return 'middleware'

        return 'route'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Koa ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_koa_version(self, content: str) -> str:
        """
        Detect the minimum Koa version required by the file.

        Returns version string (e.g., '2.0', '1.0').
        Detection is based on features used in the code.

        Koa v1 uses generator middleware (function *, this.body).
        Koa v2 uses async/await middleware (ctx.body).
        """
        has_v1_features = False
        has_v2_features = False

        for feature, version in self.KOA_VERSION_FEATURES.items():
            if feature in content:
                if version == '1.0':
                    has_v1_features = True
                elif version == '2.0':
                    has_v2_features = True

        if has_v2_features:
            return '2.0'
        if has_v1_features:
            return '1.0'
        return ''

    def is_koa_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a Koa-specific file worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file contains Koa-specific patterns
        """
        # Direct koa imports
        if re.search(r"from\s+['\"]koa['\"]|require\(['\"]koa['\"]\)", content):
            return True

        # Koa app creation
        if re.search(r'new\s+Koa\s*\(', content):
            return True

        # @koa/router or koa-router
        if re.search(r"from\s+['\"]@koa/router['\"]|require\(['\"]@koa/router['\"]\)", content):
            return True
        if re.search(r"from\s+['\"]koa-router['\"]|require\(['\"]koa-router['\"]\)", content):
            return True

        # Koa middleware signature: async (ctx, next)
        if re.search(r'async\s*\(\s*ctx\s*(?:,\s*next)?\s*\)\s*(?:=>|{)', content):
            # Extra check for Koa-specific context usage
            if re.search(r'ctx\s*\.\s*(?:body|status|throw|state|request|response|assert)', content):
                return True

        # Koa v1 generator middleware
        if re.search(r'function\s*\*\s*\(', content):
            if re.search(r'\bthis\s*\.\s*(?:body|status|throw)\b', content):
                return True

        # Koa-specific packages
        koa_packages = [
            'koa-router', '@koa/router', 'koa-body', 'koa-bodyparser',
            'koa-compose', 'koa-session', 'koa-passport', 'koa-static',
            'koa-views', 'koa-logger', '@koa/cors', 'koa-helmet',
            'koa-jwt', 'koa-mount', 'koa-send', 'koa-convert',
            'koa-json-error', 'koa-onerror', 'koa-etag',
            'koa-conditional-get', 'koa-compress', 'koa-ratelimit',
            'koa-websocket', 'koa-easy-ws', 'koa-better-body',
            'koa-json-body', 'koa-joi-router', 'koa-bouncer',
            'koa-validate', 'koa-pino-logger', 'koa-morgan',
        ]
        for pkg in koa_packages:
            if pkg in content:
                return True

        # File path conventions for Koa projects
        normalized = file_path.replace('\\', '/').lower()
        if any(p in normalized for p in ['/routes/', '/middleware/', '/controllers/']):
            if re.search(r'\bctx\b', content):
                return True

        return False
