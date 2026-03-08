"""
EnhancedHonoParser v1.0 - Comprehensive Hono parser using all extractors.

This parser integrates all Hono extractors to provide complete parsing of
Hono application files. It runs as a supplementary layer on top of the
JavaScript/TypeScript parsers, extracting Hono-specific semantics.

Supports:
- Hono v1.x (basic routing, middleware, c.json/c.text)
- Hono v2.x (improved typing, hono/validator, basic middleware)
- Hono v3.x (hono/jsx, streaming, cookie helpers, validator overhaul)
- Hono v4.x (hono/css, improved streaming, contextStorage, requestId,
             timeout, ipRestriction, enhanced RPC, hono/dev)

Multi-runtime support:
- Cloudflare Workers / Pages (export default app, c.env bindings)
- Deno / Deno Deploy (Deno.serve, import from npm:hono)
- Bun (export default { port, fetch })
- Node.js (@hono/node-server serve())
- AWS Lambda (hono/aws-lambda, handle(event, context))
- Vercel Edge (hono/vercel, export GET/POST)
- Netlify Edge (hono/netlify)
- Fastly Compute (hono/fastly)

Hono-specific extraction:
- Routes: app.get/post/put/delete/patch/options/head/all(), app.route(), basePath()
- Middleware: 20+ built-in (cors, jwt, basicAuth, logger, etc.), @hono/* third-party
- Context: c.json(), c.text(), c.html(), c.req.*, c.env.*, c.var, c.set/get
- Configuration: router selection, generics, runtime, serve/export patterns
- API Patterns: REST resources, RPC mode (hc), OpenAPI, GraphQL, WebSocket, Streaming

Framework detection (30+ Hono ecosystem patterns):
- Core: hono, hono/router/*, hono/factory, hono/client
- Middleware: hono/cors, hono/jwt, hono/basic-auth, hono/bearer-auth, hono/logger, etc.
- Helpers: hono/html, hono/css, hono/jsx, hono/streaming, hono/cookie
- Validation: @hono/zod-validator, @hono/valibot-validator, @hono/typebox-validator
- Third-party: @hono/sentry, @hono/prometheus, @hono/graphql-server, @hono/swagger-ui
- Adapters: @hono/node-server, @hono/node-ws, @hono/clerk-auth, @hono/auth-js

Optional AST support via tree-sitter-typescript / tree-sitter-javascript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.33 - Hono Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Hono extractors
from .extractors.hono import (
    HonoRouteExtractor, HonoRouteInfo, HonoRouterInfo, HonoParamInfo,
    HonoMiddlewareExtractor, HonoMiddlewareInfo, HonoMiddlewareStackInfo,
    HonoContextExtractor, HonoContextUsageInfo, HonoResponseInfo, HonoEnvBindingInfo,
    HonoConfigExtractor, HonoAppInfo, HonoServerInfo, HonoConfigSummary,
    HonoApiExtractor, HonoResourceInfo, HonoImportInfo, HonoRuntimeInfo, HonoApiSummary,
)


@dataclass
class HonoParseResult:
    """Complete parse result for a Hono file."""
    file_path: str
    file_type: str = "route"  # route, middleware, config, controller, model, service, app, test

    # Routes
    routes: List[HonoRouteInfo] = field(default_factory=list)
    routers: List[HonoRouterInfo] = field(default_factory=list)
    params: List[HonoParamInfo] = field(default_factory=list)

    # Middleware
    middleware: List[HonoMiddlewareInfo] = field(default_factory=list)
    middleware_stack: Optional[HonoMiddlewareStackInfo] = None

    # Context
    context_usages: List[HonoContextUsageInfo] = field(default_factory=list)
    responses: List[HonoResponseInfo] = field(default_factory=list)
    env_bindings: List[HonoEnvBindingInfo] = field(default_factory=list)

    # Configuration
    apps: List[HonoAppInfo] = field(default_factory=list)
    servers: List[HonoServerInfo] = field(default_factory=list)
    config_summary: Optional[HonoConfigSummary] = None

    # API Patterns
    resources: List[HonoResourceInfo] = field(default_factory=list)
    imports: List[HonoImportInfo] = field(default_factory=list)
    runtime: Optional[HonoRuntimeInfo] = None
    api_summary: Optional[HonoApiSummary] = None

    # Aggregate signals
    detected_frameworks: List[str] = field(default_factory=list)
    hono_version: str = ""  # Detected minimum Hono version
    is_typescript: bool = False
    total_routes: int = 0
    total_middleware: int = 0
    detected_runtime: str = ""


class EnhancedHonoParser:
    """
    Enhanced Hono parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript/TypeScript parsers
    when Hono framework is detected. It extracts Hono-specific semantics
    that the language parsers cannot capture.

    Multi-runtime detection:
    - Cloudflare Workers / Pages
    - Deno / Deno Deploy
    - Bun
    - Node.js (@hono/node-server)
    - AWS Lambda
    - Vercel Edge
    - Netlify Edge
    - Fastly Compute

    Optional AST: tree-sitter-typescript / tree-sitter-javascript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Hono ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core Hono ─────────────────────────────────────────────
        'hono': re.compile(
            r"from\s+['\"]hono['\"]|require\(['\"]hono['\"]\)|"
            r"new\s+Hono\s*[<(]",
            re.MULTILINE
        ),
        'hono/factory': re.compile(
            r"from\s+['\"]hono/factory['\"]|createFactory|createMiddleware",
            re.MULTILINE
        ),
        'hono/client': re.compile(
            r"from\s+['\"]hono/client['\"]|hc\s*[<(]",
            re.MULTILINE
        ),

        # ── Routers ──────────────────────────────────────────────
        'RegExpRouter': re.compile(
            r"from\s+['\"]hono/router/reg-exp-router['\"]|RegExpRouter",
            re.MULTILINE
        ),
        'TrieRouter': re.compile(
            r"from\s+['\"]hono/router/trie-router['\"]|TrieRouter",
            re.MULTILINE
        ),
        'SmartRouter': re.compile(
            r"from\s+['\"]hono/router/smart-router['\"]|SmartRouter",
            re.MULTILINE
        ),
        'LinearRouter': re.compile(
            r"from\s+['\"]hono/router/linear-router['\"]|LinearRouter",
            re.MULTILINE
        ),
        'PatternRouter': re.compile(
            r"from\s+['\"]hono/router/pattern-router['\"]|PatternRouter",
            re.MULTILINE
        ),

        # ── Built-in Middleware ───────────────────────────────────
        'hono/cors': re.compile(
            r"from\s+['\"]hono/cors['\"]|require\(['\"]hono/cors['\"]\)",
            re.MULTILINE
        ),
        'hono/jwt': re.compile(
            r"from\s+['\"]hono/jwt['\"]|require\(['\"]hono/jwt['\"]\)",
            re.MULTILINE
        ),
        'hono/basic-auth': re.compile(
            r"from\s+['\"]hono/basic-auth['\"]|require\(['\"]hono/basic-auth['\"]\)",
            re.MULTILINE
        ),
        'hono/bearer-auth': re.compile(
            r"from\s+['\"]hono/bearer-auth['\"]|require\(['\"]hono/bearer-auth['\"]\)",
            re.MULTILINE
        ),
        'hono/logger': re.compile(
            r"from\s+['\"]hono/logger['\"]|require\(['\"]hono/logger['\"]\)",
            re.MULTILINE
        ),
        'hono/pretty-json': re.compile(
            r"from\s+['\"]hono/pretty-json['\"]|require\(['\"]hono/pretty-json['\"]\)",
            re.MULTILINE
        ),
        'hono/secure-headers': re.compile(
            r"from\s+['\"]hono/secure-headers['\"]|require\(['\"]hono/secure-headers['\"]\)",
            re.MULTILINE
        ),
        'hono/cache': re.compile(
            r"from\s+['\"]hono/cache['\"]|require\(['\"]hono/cache['\"]\)",
            re.MULTILINE
        ),
        'hono/compress': re.compile(
            r"from\s+['\"]hono/compress['\"]|require\(['\"]hono/compress['\"]\)",
            re.MULTILINE
        ),
        'hono/etag': re.compile(
            r"from\s+['\"]hono/etag['\"]|require\(['\"]hono/etag['\"]\)",
            re.MULTILINE
        ),
        'hono/timing': re.compile(
            r"from\s+['\"]hono/timing['\"]|require\(['\"]hono/timing['\"]\)",
            re.MULTILINE
        ),
        'hono/body-limit': re.compile(
            r"from\s+['\"]hono/body-limit['\"]|require\(['\"]hono/body-limit['\"]\)",
            re.MULTILINE
        ),
        'hono/csrf': re.compile(
            r"from\s+['\"]hono/csrf['\"]|require\(['\"]hono/csrf['\"]\)",
            re.MULTILINE
        ),
        'hono/powered-by': re.compile(
            r"from\s+['\"]hono/powered-by['\"]|require\(['\"]hono/powered-by['\"]\)",
            re.MULTILINE
        ),
        'hono/trailing-slash': re.compile(
            r"from\s+['\"]hono/trailing-slash['\"]|require\(['\"]hono/trailing-slash['\"]\)",
            re.MULTILINE
        ),
        'hono/request-id': re.compile(
            r"from\s+['\"]hono/request-id['\"]|require\(['\"]hono/request-id['\"]\)",
            re.MULTILINE
        ),
        'hono/timeout': re.compile(
            r"from\s+['\"]hono/timeout['\"]|require\(['\"]hono/timeout['\"]\)",
            re.MULTILINE
        ),
        'hono/ip-restriction': re.compile(
            r"from\s+['\"]hono/ip-restriction['\"]|require\(['\"]hono/ip-restriction['\"]\)",
            re.MULTILINE
        ),
        'hono/context-storage': re.compile(
            r"from\s+['\"]hono/context-storage['\"]|require\(['\"]hono/context-storage['\"]\)",
            re.MULTILINE
        ),

        # ── Helpers ──────────────────────────────────────────────
        'hono/html': re.compile(
            r"from\s+['\"]hono/html['\"]|require\(['\"]hono/html['\"]\)",
            re.MULTILINE
        ),
        'hono/css': re.compile(
            r"from\s+['\"]hono/css['\"]|require\(['\"]hono/css['\"]\)",
            re.MULTILINE
        ),
        'hono/jsx': re.compile(
            r"from\s+['\"]hono/jsx['\"]|from\s+['\"]hono/jsx/dom['\"]",
            re.MULTILINE
        ),
        'hono/streaming': re.compile(
            r"from\s+['\"]hono/streaming['\"]|require\(['\"]hono/streaming['\"]\)",
            re.MULTILINE
        ),
        'hono/cookie': re.compile(
            r"from\s+['\"]hono/cookie['\"]|require\(['\"]hono/cookie['\"]\)|"
            r"getCookie|setCookie|deleteCookie",
            re.MULTILINE
        ),
        'hono/validator': re.compile(
            r"from\s+['\"]hono/validator['\"]|require\(['\"]hono/validator['\"]\)|"
            r"validator\s*\(",
            re.MULTILINE
        ),
        'hono/testing': re.compile(
            r"from\s+['\"]hono/testing['\"]|testClient",
            re.MULTILINE
        ),

        # ── Third-party (@hono/*) ────────────────────────────────
        '@hono/zod-validator': re.compile(
            r"from\s+['\"]@hono/zod-validator['\"]|zValidator",
            re.MULTILINE
        ),
        '@hono/valibot-validator': re.compile(
            r"from\s+['\"]@hono/valibot-validator['\"]|vValidator",
            re.MULTILINE
        ),
        '@hono/typebox-validator': re.compile(
            r"from\s+['\"]@hono/typebox-validator['\"]|tbValidator",
            re.MULTILINE
        ),
        '@hono/graphql-server': re.compile(
            r"from\s+['\"]@hono/graphql-server['\"]|graphqlServer",
            re.MULTILINE
        ),
        '@hono/swagger-ui': re.compile(
            r"from\s+['\"]@hono/swagger-ui['\"]|swaggerUI",
            re.MULTILINE
        ),
        '@hono/node-server': re.compile(
            r"from\s+['\"]@hono/node-server['\"]|require\(['\"]@hono/node-server['\"]\)",
            re.MULTILINE
        ),
        '@hono/sentry': re.compile(
            r"from\s+['\"]@hono/sentry['\"]|sentry\(",
            re.MULTILINE
        ),
        '@hono/prometheus': re.compile(
            r"from\s+['\"]@hono/prometheus['\"]|prometheus\(",
            re.MULTILINE
        ),
        '@hono/trpc-server': re.compile(
            r"from\s+['\"]@hono/trpc-server['\"]|trpcServer",
            re.MULTILINE
        ),
        '@hono/clerk-auth': re.compile(
            r"from\s+['\"]@hono/clerk-auth['\"]|clerkAuth",
            re.MULTILINE
        ),
        '@hono/auth-js': re.compile(
            r"from\s+['\"]@hono/auth-js['\"]|authHandler|verifyAuth",
            re.MULTILINE
        ),
        '@hono/node-ws': re.compile(
            r"from\s+['\"]@hono/node-ws['\"]|createNodeWebSocket",
            re.MULTILINE
        ),
        '@hono/zod-openapi': re.compile(
            r"from\s+['\"]@hono/zod-openapi['\"]|OpenAPIHono|createRoute",
            re.MULTILINE
        ),

        # ── Database ─────────────────────────────────────────────
        'drizzle': re.compile(
            r"from\s+['\"]drizzle-orm['\"]|drizzle\(",
            re.MULTILINE
        ),
        'prisma': re.compile(
            r"from\s+['\"]@prisma/client['\"]|PrismaClient",
            re.MULTILINE
        ),

        # ── Validation ───────────────────────────────────────────
        'zod': re.compile(
            r"from\s+['\"]zod['\"]|z\.\w+\(",
            re.MULTILINE
        ),
        'valibot': re.compile(
            r"from\s+['\"]valibot['\"]|v\.\w+\(",
            re.MULTILINE
        ),
    }

    # Hono version detection from features
    HONO_VERSION_FEATURES = {
        # Hono v1.x (basic features)
        'c.json': '1.0',
        'c.text': '1.0',
        'c.html': '1.0',
        'c.redirect': '1.0',
        'c.req.param': '1.0',
        'c.req.query': '1.0',
        # Hono v2.x (improved typing, validator)
        'hono/validator': '2.0',
        'c.req.valid': '2.0',
        # Hono v3.x (jsx, streaming, cookies)
        'hono/jsx': '3.0',
        'hono/streaming': '3.0',
        'hono/cookie': '3.0',
        'hono/adapter': '3.0',
        'c.stream': '3.0',
        'c.streamText': '3.0',
        'c.streamSSE': '3.0',
        'c.render': '3.0',
        'c.setRenderer': '3.0',
        # Hono v4.x (css, contextStorage, requestId, timeout, ipRestriction)
        'hono/css': '4.0',
        'hono/context-storage': '4.0',
        'hono/request-id': '4.0',
        'hono/timeout': '4.0',
        'hono/ip-restriction': '4.0',
        'hono/dev': '4.0',
    }

    def __init__(self):
        """Initialize the parser with all Hono extractors."""
        self.route_extractor = HonoRouteExtractor()
        self.middleware_extractor = HonoMiddlewareExtractor()
        self.context_extractor = HonoContextExtractor()
        self.config_extractor = HonoConfigExtractor()
        self.api_extractor = HonoApiExtractor()

    def parse(self, content: str, file_path: str = "") -> HonoParseResult:
        """
        Parse Hono source code and extract all Hono-specific information.

        This should be called AFTER the JS/TS parsers have run, when
        Hono framework is detected. It extracts Hono-specific semantics.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            HonoParseResult with all extracted Hono information
        """
        result = HonoParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # TypeScript detection
        result.is_typescript = file_path.endswith(('.ts', '.tsx'))

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

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
        result.responses = ctx_result.get('responses', [])
        result.env_bindings = ctx_result.get('env_bindings', [])

        # ── Configuration ────────────────────────────────────────
        config_result = self.config_extractor.extract(content, file_path)
        result.apps = config_result.get('apps', [])
        result.servers = config_result.get('servers', [])
        result.config_summary = config_result.get('summary')

        # ── API Patterns ─────────────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.resources = api_result.get('resources', [])
        result.imports = api_result.get('imports', [])
        result.runtime = api_result.get('runtime')
        result.api_summary = api_result.get('summary')

        # Runtime from API or config
        if result.runtime:
            result.detected_runtime = result.runtime.runtime
        elif result.config_summary:
            result.detected_runtime = result.config_summary.runtime

        # ── Version detection ────────────────────────────────────
        result.hono_version = self._detect_hono_version(content)

        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a Hono file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        # By filename conventions
        if 'app.' in basename or 'server.' in basename or 'index.' in basename:
            if 'Hono' in content or 'new Hono' in content:
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
        if 'config' in basename or 'worker' in basename:
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
        if 'new Hono(' in content and ('export default' in content or 'app.listen' in content):
            return 'app'
        if '.get(' in content or '.post(' in content:
            return 'route'

        return 'route'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Hono ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_hono_version(self, content: str) -> str:
        """
        Detect the minimum Hono version required by the file.

        Returns version string (e.g., '4.0', '3.0', '2.0', '1.0').
        Detection is based on features used in the code.
        """
        max_version = '0.0'

        for feature, version in self.HONO_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version

        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_hono_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a Hono-specific file worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file contains Hono-specific patterns
        """
        # Direct hono imports
        if re.search(r"from\s+['\"]hono['\"]|require\(['\"]hono['\"]\)", content):
            return True

        # Hono app creation
        if re.search(r'new\s+Hono\s*[<(]', content):
            return True

        # Hono sub-packages
        if re.search(r"from\s+['\"]hono/\w", content):
            return True

        # @hono/* packages
        if re.search(r"from\s+['\"]@hono/", content):
            return True

        # Hono-specific context patterns: c.json(), c.text(), c.html()
        if re.search(r'\bc\s*\.\s*(?:json|text|html|redirect|notFound)\s*\(', content):
            if re.search(r'\bc\s*\.\s*req\s*\.', content):
                return True

        # Hono RPC client
        if re.search(r'hc\s*<\w', content):
            return True

        # Hono-specific packages
        hono_packages = [
            'hono/cors', 'hono/jwt', 'hono/basic-auth', 'hono/bearer-auth',
            'hono/logger', 'hono/pretty-json', 'hono/secure-headers',
            'hono/cache', 'hono/compress', 'hono/etag', 'hono/timing',
            'hono/body-limit', 'hono/csrf', 'hono/cookie', 'hono/html',
            'hono/css', 'hono/jsx', 'hono/streaming', 'hono/validator',
            'hono/factory', 'hono/client', 'hono/testing', 'hono/adapter',
            '@hono/node-server', '@hono/zod-validator', '@hono/swagger-ui',
        ]
        for pkg in hono_packages:
            if pkg in content:
                return True

        return False
