"""
EnhancedFastifyParser v1.0 - Comprehensive Fastify parser using all extractors.

This parser integrates all Fastify extractors to provide complete parsing of
Fastify application files. It runs as a supplementary layer on top of the
JavaScript/TypeScript parsers, extracting Fastify-specific semantics.

Supports:
- Fastify 3.x (JSON Schema validation, decorators, hooks, plugins, serialization)
- Fastify 4.x (Type providers, improved plugin system, logging improvements,
                new hooks, better TypeScript support, encapsulation context)
- Fastify 5.x (Breaking changes: removed deprecated APIs, improved types,
                better async support, updated plugin interface)

Fastify-specific extraction:
- Routes: Shorthand (get/post/put/delete), fastify.route(), prefixed routes
- Plugins: fastify.register(), fastify-plugin (fp), encapsulation, @fastify/autoload
- Hooks: Request lifecycle (onRequest→preParsing→preValidation→preHandler→
         preSerialization→onSend→onResponse), application hooks (onReady, onClose)
- Schemas: JSON Schema validation (body, querystring, params, headers, response),
           addSchema(), $ref references, shared schemas
- Type Providers: TypeBox, Zod, JSON Schema to TypeScript, Fluent JSON Schema
- Decorators: fastify.decorate(), decorateRequest(), decorateReply()
- Serialization: Schema-based serialization, custom serializer compilers

Framework detection (30+ Fastify ecosystem patterns):
- Core: fastify, @fastify/*, fastify-plugin
- Security: @fastify/helmet, @fastify/cors, @fastify/rate-limit, @fastify/csrf-protection
- Auth: @fastify/jwt, @fastify/cookie, @fastify/session, @fastify/passport,
        @fastify/auth, @fastify/bearer-auth, @fastify/oauth2
- Database: @fastify/mongodb, @fastify/postgres, @fastify/mysql, @fastify/redis
- Validation: TypeBox, Zod, Fluent JSON Schema, Ajv
- Documentation: @fastify/swagger, @fastify/swagger-ui
- WebSockets: @fastify/websocket
- GraphQL: mercurius, @fastify/mercurius
- File Upload: @fastify/multipart
- Static Files: @fastify/static, @fastify/view
- Caching: @fastify/caching, @fastify/etag
- Compression: @fastify/compress
- Monitoring: fastify-metrics, pino (built-in logging)
- Testing: fastify.inject(), light-my-request

Optional AST support via tree-sitter-typescript / tree-sitter-javascript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.33 - Fastify Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Fastify extractors
from .extractors.fastify import (
    FastifyRouteExtractor, FastifyRouteInfo, FastifyRouteOptionsInfo,
    FastifyPluginExtractor, FastifyPluginInfo, FastifyPluginRegistrationInfo, FastifyDecoratorInfo,
    FastifyHookExtractor, FastifyHookInfo, FastifyHookSummary,
    FastifySchemaExtractor, FastifySchemaInfo, FastifyTypeProviderInfo,
    FastifyApiExtractor, FastifyResourceInfo, FastifySerializerInfo, FastifyApiSummary,
)


@dataclass
class FastifyParseResult:
    """Complete parse result for a Fastify file."""
    file_path: str
    file_type: str = "route"  # route, plugin, hook, schema, config, app, test

    # Routes
    routes: List[FastifyRouteInfo] = field(default_factory=list)
    route_options: List[FastifyRouteOptionsInfo] = field(default_factory=list)

    # Plugins
    plugins: List[FastifyPluginInfo] = field(default_factory=list)
    registrations: List[FastifyPluginRegistrationInfo] = field(default_factory=list)
    decorators: List[FastifyDecoratorInfo] = field(default_factory=list)

    # Hooks
    hooks: List[FastifyHookInfo] = field(default_factory=list)
    hook_summary: Optional[FastifyHookSummary] = None

    # Schemas
    schemas: List[FastifySchemaInfo] = field(default_factory=list)
    type_providers: List[FastifyTypeProviderInfo] = field(default_factory=list)

    # API Patterns
    resources: List[FastifyResourceInfo] = field(default_factory=list)
    serializers: List[FastifySerializerInfo] = field(default_factory=list)
    api_summary: Optional[FastifyApiSummary] = None

    # Aggregate signals
    detected_frameworks: List[str] = field(default_factory=list)
    fastify_version: str = ""
    is_typescript: bool = False
    total_routes: int = 0
    total_plugins: int = 0
    total_hooks: int = 0
    total_schemas: int = 0


class EnhancedFastifyParser:
    """
    Enhanced Fastify parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript/TypeScript parsers
    when Fastify framework is detected.
    """

    # Fastify ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core Fastify ──────────────────────────────────────────
        'fastify': re.compile(
            r"from\s+['\"]fastify['\"]|require\(['\"]fastify['\"]\)|"
            r"Fastify\(|fastify\(",
            re.MULTILINE
        ),
        'fastify-plugin': re.compile(
            r"from\s+['\"]fastify-plugin['\"]|require\(['\"]fastify-plugin['\"]\)|"
            r"fp\(",
            re.MULTILINE
        ),

        # ── Security ─────────────────────────────────────────────
        'fastify-helmet': re.compile(
            r"from\s+['\"]@fastify/helmet['\"]|require\(['\"]@fastify/helmet['\"]\)|"
            r"fastifyHelmet",
            re.MULTILINE
        ),
        'fastify-cors': re.compile(
            r"from\s+['\"]@fastify/cors['\"]|require\(['\"]@fastify/cors['\"]\)|"
            r"fastifyCors",
            re.MULTILINE
        ),
        'fastify-rate-limit': re.compile(
            r"from\s+['\"]@fastify/rate-limit['\"]|require\(['\"]@fastify/rate-limit['\"]\)|"
            r"fastifyRateLimit",
            re.MULTILINE
        ),
        'fastify-csrf': re.compile(
            r"from\s+['\"]@fastify/csrf-protection['\"]|fastifyCsrf",
            re.MULTILINE
        ),

        # ── Auth ─────────────────────────────────────────────────
        'fastify-jwt': re.compile(
            r"from\s+['\"]@fastify/jwt['\"]|require\(['\"]@fastify/jwt['\"]\)|"
            r"fastifyJwt|jwtVerify|jwtSign",
            re.MULTILINE
        ),
        'fastify-cookie': re.compile(
            r"from\s+['\"]@fastify/cookie['\"]|require\(['\"]@fastify/cookie['\"]\)|"
            r"fastifyCookie",
            re.MULTILINE
        ),
        'fastify-session': re.compile(
            r"from\s+['\"]@fastify/session['\"]|require\(['\"]@fastify/session['\"]\)|"
            r"fastifySession",
            re.MULTILINE
        ),
        'fastify-passport': re.compile(
            r"from\s+['\"]@fastify/passport['\"]|fastifyPassport",
            re.MULTILINE
        ),
        'fastify-auth': re.compile(
            r"from\s+['\"]@fastify/auth['\"]|fastifyAuth",
            re.MULTILINE
        ),
        'fastify-bearer': re.compile(
            r"from\s+['\"]@fastify/bearer-auth['\"]|fastifyBearerAuth",
            re.MULTILINE
        ),
        'fastify-oauth2': re.compile(
            r"from\s+['\"]@fastify/oauth2['\"]|fastifyOAuth2",
            re.MULTILINE
        ),

        # ── Database ─────────────────────────────────────────────
        'fastify-mongodb': re.compile(
            r"from\s+['\"]@fastify/mongodb['\"]|fastifyMongo",
            re.MULTILINE
        ),
        'fastify-postgres': re.compile(
            r"from\s+['\"]@fastify/postgres['\"]|fastifyPostgres",
            re.MULTILINE
        ),
        'fastify-mysql': re.compile(
            r"from\s+['\"]@fastify/mysql['\"]|fastifyMysql",
            re.MULTILINE
        ),
        'fastify-redis': re.compile(
            r"from\s+['\"]@fastify/redis['\"]|fastifyRedis",
            re.MULTILINE
        ),
        'prisma': re.compile(
            r"from\s+['\"]@prisma/client['\"]|PrismaClient",
            re.MULTILINE
        ),

        # ── Validation/Type Providers ────────────────────────────
        'typebox': re.compile(
            r"from\s+['\"]@sinclair/typebox['\"]|Type\.\w+\(|TypeBoxTypeProvider",
            re.MULTILINE
        ),
        'zod': re.compile(
            r"from\s+['\"]zod['\"]|ZodTypeProvider|serializerCompiler.*zod",
            re.MULTILINE
        ),
        'fluent-json-schema': re.compile(
            r"from\s+['\"]fluent-json-schema['\"]|S\.object|S\.string",
            re.MULTILINE
        ),
        'ajv': re.compile(
            r"from\s+['\"]ajv['\"]|new\s+Ajv",
            re.MULTILINE
        ),

        # ── Documentation ────────────────────────────────────────
        'fastify-swagger': re.compile(
            r"from\s+['\"]@fastify/swagger['\"]|require\(['\"]@fastify/swagger['\"]\)|"
            r"fastifySwagger",
            re.MULTILINE
        ),
        'fastify-swagger-ui': re.compile(
            r"from\s+['\"]@fastify/swagger-ui['\"]|fastifySwaggerUi",
            re.MULTILINE
        ),

        # ── WebSockets ───────────────────────────────────────────
        'fastify-websocket': re.compile(
            r"from\s+['\"]@fastify/websocket['\"]|require\(['\"]@fastify/websocket['\"]\)|"
            r"fastifyWebsocket",
            re.MULTILINE
        ),

        # ── GraphQL ──────────────────────────────────────────────
        'mercurius': re.compile(
            r"from\s+['\"]mercurius['\"]|from\s+['\"]@fastify/mercurius['\"]|"
            r"require\(['\"]mercurius['\"]\)",
            re.MULTILINE
        ),

        # ── File Upload ──────────────────────────────────────────
        'fastify-multipart': re.compile(
            r"from\s+['\"]@fastify/multipart['\"]|fastifyMultipart",
            re.MULTILINE
        ),

        # ── Static Files ─────────────────────────────────────────
        'fastify-static': re.compile(
            r"from\s+['\"]@fastify/static['\"]|fastifyStatic",
            re.MULTILINE
        ),
        'fastify-view': re.compile(
            r"from\s+['\"]@fastify/view['\"]|fastifyView|point-of-view",
            re.MULTILINE
        ),

        # ── Caching ──────────────────────────────────────────────
        'fastify-caching': re.compile(
            r"from\s+['\"]@fastify/caching['\"]|fastifyCaching",
            re.MULTILINE
        ),
        'fastify-etag': re.compile(
            r"from\s+['\"]@fastify/etag['\"]|fastifyEtag",
            re.MULTILINE
        ),

        # ── Compression ──────────────────────────────────────────
        'fastify-compress': re.compile(
            r"from\s+['\"]@fastify/compress['\"]|fastifyCompress",
            re.MULTILINE
        ),

        # ── Monitoring ───────────────────────────────────────────
        'fastify-metrics': re.compile(
            r"from\s+['\"]fastify-metrics['\"]|fastifyMetrics",
            re.MULTILINE
        ),
        'pino': re.compile(
            r"from\s+['\"]pino['\"]|pino\(|logger:\s*true|logger:\s*\{",
            re.MULTILINE
        ),

        # ── Autoload ─────────────────────────────────────────────
        'fastify-autoload': re.compile(
            r"from\s+['\"]@fastify/autoload['\"]|require\(['\"]@fastify/autoload['\"]\)|"
            r"fastifyAutoload",
            re.MULTILINE
        ),

        # ── Sensible (utilities) ─────────────────────────────────
        'fastify-sensible': re.compile(
            r"from\s+['\"]@fastify/sensible['\"]|fastifySensible",
            re.MULTILINE
        ),

        # ── Form parsing ─────────────────────────────────────────
        'fastify-formbody': re.compile(
            r"from\s+['\"]@fastify/formbody['\"]|fastifyFormbody",
            re.MULTILINE
        ),
    }

    # Fastify version detection from features
    FASTIFY_VERSION_FEATURES = {
        # Fastify 5.x features
        'setValidatorCompiler': '5.0',
        'setSerializerCompiler': '4.0',

        # Fastify 4.x features
        'TypeBoxTypeProvider': '4.0',
        'ZodTypeProvider': '4.0',
        'JsonSchemaToTsProvider': '4.0',
        '@fastify/': '4.0',
        'encapsulation': '4.0',

        # Fastify 3.x features
        'addSchema': '3.0',
        'fastify.register': '3.0',
        'addHook': '3.0',
    }

    def __init__(self):
        """Initialize the parser with all Fastify extractors."""
        self.route_extractor = FastifyRouteExtractor()
        self.plugin_extractor = FastifyPluginExtractor()
        self.hook_extractor = FastifyHookExtractor()
        self.schema_extractor = FastifySchemaExtractor()
        self.api_extractor = FastifyApiExtractor()

    def parse(self, content: str, file_path: str = "") -> FastifyParseResult:
        """
        Parse Fastify source code and extract all Fastify-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            FastifyParseResult with all extracted Fastify information
        """
        result = FastifyParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # TypeScript detection
        result.is_typescript = file_path.endswith(('.ts', '.tsx'))

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Routes ───────────────────────────────────────────────
        route_result = self.route_extractor.extract(content, file_path)
        result.routes = route_result.get('routes', [])
        result.route_options = route_result.get('route_options', [])
        result.total_routes = len(result.routes)

        # ── Plugins ──────────────────────────────────────────────
        plugin_result = self.plugin_extractor.extract(content, file_path)
        result.plugins = plugin_result.get('plugins', [])
        result.registrations = plugin_result.get('registrations', [])
        result.decorators = plugin_result.get('decorators', [])
        result.total_plugins = len(result.registrations)

        # ── Hooks ────────────────────────────────────────────────
        hook_result = self.hook_extractor.extract(content, file_path)
        result.hooks = hook_result.get('hooks', [])
        result.hook_summary = hook_result.get('summary')
        result.total_hooks = len(result.hooks)

        # ── Schemas ──────────────────────────────────────────────
        schema_result = self.schema_extractor.extract(content, file_path)
        result.schemas = schema_result.get('schemas', [])
        result.type_providers = schema_result.get('type_providers', [])
        result.total_schemas = len(result.schemas)

        # ── API Patterns ─────────────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.resources = api_result.get('resources', [])
        result.serializers = api_result.get('serializers', [])
        result.api_summary = api_result.get('summary')

        # ── Version detection ────────────────────────────────────
        result.fastify_version = self._detect_fastify_version(content)

        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a Fastify file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        if 'app.' in basename or 'server.' in basename or 'index.' in basename:
            if 'fastify' in content or 'Fastify' in content:
                return 'app'
        if 'route' in basename:
            return 'route'
        if 'plugin' in basename:
            return 'plugin'
        if 'hook' in basename:
            return 'hook'
        if 'schema' in basename:
            return 'schema'
        if 'config' in basename:
            return 'config'
        if 'test' in basename or 'spec' in basename:
            return 'test'

        # By directory
        if '/routes/' in normalized:
            return 'route'
        if '/plugins/' in normalized:
            return 'plugin'
        if '/hooks/' in normalized:
            return 'hook'
        if '/schemas/' in normalized:
            return 'schema'

        # By content
        if 'fastify.register' in content or '.register(' in content:
            return 'plugin'
        if '.addHook(' in content:
            return 'hook'
        if 'addSchema' in content:
            return 'schema'
        if re.search(r'\.\s*(?:get|post|put|delete|patch)\s*\(', content):
            return 'route'

        return 'route'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Fastify ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_fastify_version(self, content: str) -> str:
        """Detect the minimum Fastify version required."""
        max_version = '0.0'
        for feature, version in self.FASTIFY_VERSION_FEATURES.items():
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

    def is_fastify_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a Fastify-specific file worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file contains Fastify-specific patterns
        """
        # Direct fastify imports
        if re.search(r"from\s+['\"]fastify['\"]|require\(['\"]fastify['\"]\)", content):
            return True

        # Fastify instance creation
        if re.search(r'[Ff]astify\s*\(', content):
            return True

        # fastify-plugin
        if re.search(r"from\s+['\"]fastify-plugin['\"]|require\(['\"]fastify-plugin['\"]\)", content):
            return True

        # @fastify/ scoped packages
        if re.search(r"['\"]@fastify/", content):
            return True

        # Fastify-specific APIs
        if re.search(r'\.addHook\s*\(\s*[\'"](?:onRequest|preHandler|onSend)', content):
            return True

        if re.search(r'\.addSchema\s*\(', content):
            return True

        if re.search(r'\.decorateRequest\s*\(|\.decorateReply\s*\(', content):
            return True

        # Fastify-specific type imports
        if re.search(r'FastifyInstance|FastifyRequest|FastifyReply|FastifyPluginCallback|'
                     r'FastifyPluginAsync|FastifyPluginOptions|RouteShorthandOptions', content):
            return True

        # Plugin export with fastify instance param
        if re.search(r'(?:async\s+)?function\s*\(\s*(?:fastify|app|instance|server)\s*,\s*(?:opts|options)', content):
            if 'express' not in content.lower() and 'koa' not in content.lower():
                return True

        return False
