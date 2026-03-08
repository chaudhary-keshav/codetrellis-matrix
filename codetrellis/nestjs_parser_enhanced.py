"""
EnhancedNestJSParser v1.0 - Comprehensive per-file NestJS parser using all extractors.

This parser integrates all NestJS enhanced extractors to provide complete per-file
parsing of NestJS application files. It runs as a supplementary layer on top of the
TypeScript parser, extracting NestJS-specific semantics.

Complements the existing project-level NestJSExtractor with content-based per-file
analysis. The project-level extractor handles module graph construction, while this
parser extracts rich per-file details for controllers, providers, DTOs, etc.

Supports:
- NestJS 7.x (Initial framework patterns, basic decorators)
- NestJS 8.x (Standalone apps, enhanced module system, ConfigModule improvements)
- NestJS 9.x (REPL, SWC compiler, improved DI, Fastify 4 support)
- NestJS 10.x (Cache manager v5, Redis v4, SWC improvements, decorator metadata)

NestJS-specific extraction:
- Modules: @Module() decorator, imports/providers/controllers/exports,
           @Global(), dynamic modules (forRoot, forFeature, registerAsync)
- Controllers: @Controller() with path, HTTP method decorators, @UseGuards,
               @UseInterceptors, @UsePipes, parameter decorators, versioning
- Providers: @Injectable() services/guards/interceptors/pipes/middleware/filters,
             constructor injection, @Inject() tokens, @Optional(), scopes
- Config: ConfigModule.forRoot(), ConfigService.get/getOrThrow, process.env,
          registerAs factories, Joi validation schemas
- API/Swagger: @ApiTags, @ApiOperation, @ApiResponse, @ApiProperty, DTOs,
               auth decorators, class-validator integration

Framework detection (40+ NestJS ecosystem patterns):
- Core: @nestjs/common, @nestjs/core, @nestjs/platform-express/fastify
- Database: @nestjs/typeorm, @nestjs/mongoose, @nestjs/sequelize, prisma
- Auth: @nestjs/passport, @nestjs/jwt, passport-jwt, passport-local
- Config: @nestjs/config, dotenv, joi
- Cache: @nestjs/cache-manager, cache-manager
- Queue: @nestjs/bull, @nestjs/bullmq, bull, bullmq
- Scheduling: @nestjs/schedule, cron
- WebSockets: @nestjs/websockets, @nestjs/platform-socket.io, socket.io
- GraphQL: @nestjs/graphql, @nestjs/apollo, @nestjs/mercurius
- Microservices: @nestjs/microservices, gRPC, MQTT, RabbitMQ, Kafka, NATS, Redis
- CQRS: @nestjs/cqrs
- Event Emitter: @nestjs/event-emitter
- Health: @nestjs/terminus
- Swagger: @nestjs/swagger
- Testing: @nestjs/testing, supertest
- Throttle: @nestjs/throttler
- Serve Static: @nestjs/serve-static

Optional AST support via tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.33 - NestJS Enhanced Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all NestJS enhanced extractors
from .extractors.nestjs_enhanced import (
    NestModuleExtractor, NestModuleDecoratorInfo, NestProviderInfo, NestDynamicModuleInfo,
    NestControllerExtractor, NestControllerInfo, NestEndpointInfo, NestParamDecoratorInfo,
    NestProviderExtractor, NestInjectableInfo, NestInjectionInfo, NestCustomProviderInfo,
    NestConfigExtractor, NestConfigModuleInfo, NestEnvVarInfo, NestConfigServiceUsageInfo,
    NestApiExtractor, NestSwaggerInfo, NestApiPropertyInfo, NestDtoInfo, NestApiSummary,
)


@dataclass
class NestJSEnhancedParseResult:
    """Complete parse result for a NestJS file."""
    file_path: str
    file_type: str = "service"  # module, controller, service, guard, interceptor, pipe,
                                 # middleware, filter, gateway, dto, config, test, main

    # Modules
    modules: List[NestModuleDecoratorInfo] = field(default_factory=list)
    module_providers: List[NestProviderInfo] = field(default_factory=list)
    dynamic_modules: List[NestDynamicModuleInfo] = field(default_factory=list)

    # Controllers
    controllers: List[NestControllerInfo] = field(default_factory=list)
    param_decorators: List[NestParamDecoratorInfo] = field(default_factory=list)

    # Providers
    injectables: List[NestInjectableInfo] = field(default_factory=list)
    injections: List[NestInjectionInfo] = field(default_factory=list)
    custom_providers: List[NestCustomProviderInfo] = field(default_factory=list)

    # Config
    config_modules: List[NestConfigModuleInfo] = field(default_factory=list)
    env_vars: List[NestEnvVarInfo] = field(default_factory=list)
    config_usages: List[NestConfigServiceUsageInfo] = field(default_factory=list)

    # API/Swagger
    swagger_decorators: List[NestSwaggerInfo] = field(default_factory=list)
    api_properties: List[NestApiPropertyInfo] = field(default_factory=list)
    dtos: List[NestDtoInfo] = field(default_factory=list)
    api_summary: Optional[NestApiSummary] = None

    # Aggregate signals
    detected_frameworks: List[str] = field(default_factory=list)
    nestjs_version: str = ""
    total_endpoints: int = 0
    total_injectables: int = 0
    total_injections: int = 0
    has_swagger: bool = False
    has_validation: bool = False


class EnhancedNestJSParser:
    """
    Enhanced per-file NestJS parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the TypeScript parser when NestJS
    framework is detected. It extracts NestJS-specific semantics per-file.

    Complements the existing NestJSExtractor (project-level) with detailed
    per-file content analysis.
    """

    # NestJS ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core NestJS ───────────────────────────────────────────
        'nestjs-common': re.compile(
            r"from\s+['\"]@nestjs/common['\"]",
            re.MULTILINE
        ),
        'nestjs-core': re.compile(
            r"from\s+['\"]@nestjs/core['\"]",
            re.MULTILINE
        ),
        'nestjs-platform-express': re.compile(
            r"from\s+['\"]@nestjs/platform-express['\"]|NestExpressApplication",
            re.MULTILINE
        ),
        'nestjs-platform-fastify': re.compile(
            r"from\s+['\"]@nestjs/platform-fastify['\"]|NestFastifyApplication|FastifyAdapter",
            re.MULTILINE
        ),

        # ── Database ─────────────────────────────────────────────
        'nestjs-typeorm': re.compile(
            r"from\s+['\"]@nestjs/typeorm['\"]|TypeOrmModule|InjectRepository",
            re.MULTILINE
        ),
        'nestjs-mongoose': re.compile(
            r"from\s+['\"]@nestjs/mongoose['\"]|MongooseModule|InjectModel|@Schema\(",
            re.MULTILINE
        ),
        'nestjs-sequelize': re.compile(
            r"from\s+['\"]@nestjs/sequelize['\"]|SequelizeModule|InjectModel",
            re.MULTILINE
        ),
        'prisma': re.compile(
            r"from\s+['\"]@prisma/client['\"]|PrismaClient|PrismaService|prisma\.\w+",
            re.MULTILINE
        ),

        # ── Auth ─────────────────────────────────────────────────
        'nestjs-passport': re.compile(
            r"from\s+['\"]@nestjs/passport['\"]|PassportModule|AuthGuard",
            re.MULTILINE
        ),
        'nestjs-jwt': re.compile(
            r"from\s+['\"]@nestjs/jwt['\"]|JwtModule|JwtService|JwtAuthGuard",
            re.MULTILINE
        ),

        # ── Config ───────────────────────────────────────────────
        'nestjs-config': re.compile(
            r"from\s+['\"]@nestjs/config['\"]|ConfigModule|ConfigService",
            re.MULTILINE
        ),

        # ── Cache ────────────────────────────────────────────────
        'nestjs-cache': re.compile(
            r"from\s+['\"]@nestjs/cache-manager['\"]|CacheModule|CacheInterceptor|"
            r"@CacheKey|@CacheTTL|CACHE_MANAGER",
            re.MULTILINE
        ),

        # ── Queue ────────────────────────────────────────────────
        'nestjs-bull': re.compile(
            r"from\s+['\"]@nestjs/bull(?:mq)?['\"]|BullModule|@Processor|@Process|"
            r"InjectQueue|@OnQueueEvent",
            re.MULTILINE
        ),

        # ── Scheduling ───────────────────────────────────────────
        'nestjs-schedule': re.compile(
            r"from\s+['\"]@nestjs/schedule['\"]|ScheduleModule|@Cron|@Interval|@Timeout",
            re.MULTILINE
        ),

        # ── WebSockets ───────────────────────────────────────────
        'nestjs-websockets': re.compile(
            r"from\s+['\"]@nestjs/websockets['\"]|from\s+['\"]@nestjs/platform-socket.io['\"]|"
            r"@WebSocketGateway|@SubscribeMessage|@WebSocketServer",
            re.MULTILINE
        ),

        # ── GraphQL ──────────────────────────────────────────────
        'nestjs-graphql': re.compile(
            r"from\s+['\"]@nestjs/graphql['\"]|from\s+['\"]@nestjs/apollo['\"]|"
            r"from\s+['\"]@nestjs/mercurius['\"]|"
            r"@Resolver|@Query\(\)|@Mutation|@Subscription|@InputType|@ObjectType|"
            r"@Field\(|GraphQLModule",
            re.MULTILINE
        ),

        # ── Microservices ────────────────────────────────────────
        'nestjs-microservices': re.compile(
            r"from\s+['\"]@nestjs/microservices['\"]|"
            r"@MessagePattern|@EventPattern|ClientProxy|Transport\.",
            re.MULTILINE
        ),

        # ── CQRS ────────────────────────────────────────────────
        'nestjs-cqrs': re.compile(
            r"from\s+['\"]@nestjs/cqrs['\"]|"
            r"@CommandHandler|@QueryHandler|@EventHandler|CommandBus|QueryBus|EventBus",
            re.MULTILINE
        ),

        # ── Event Emitter ────────────────────────────────────────
        'nestjs-event-emitter': re.compile(
            r"from\s+['\"]@nestjs/event-emitter['\"]|"
            r"EventEmitterModule|@OnEvent|EventEmitter2",
            re.MULTILINE
        ),

        # ── Health ───────────────────────────────────────────────
        'nestjs-terminus': re.compile(
            r"from\s+['\"]@nestjs/terminus['\"]|"
            r"TerminusModule|HealthCheckService|HealthCheck",
            re.MULTILINE
        ),

        # ── Swagger ──────────────────────────────────────────────
        'nestjs-swagger': re.compile(
            r"from\s+['\"]@nestjs/swagger['\"]|"
            r"SwaggerModule|DocumentBuilder|ApiTags|ApiProperty|ApiOperation",
            re.MULTILINE
        ),

        # ── Testing ──────────────────────────────────────────────
        'nestjs-testing': re.compile(
            r"from\s+['\"]@nestjs/testing['\"]|Test\.createTestingModule|TestingModule",
            re.MULTILINE
        ),

        # ── Throttle ────────────────────────────────────────────
        'nestjs-throttler': re.compile(
            r"from\s+['\"]@nestjs/throttler['\"]|ThrottlerModule|ThrottlerGuard|@Throttle",
            re.MULTILINE
        ),

        # ── Serve Static ────────────────────────────────────────
        'nestjs-serve-static': re.compile(
            r"from\s+['\"]@nestjs/serve-static['\"]|ServeStaticModule",
            re.MULTILINE
        ),

        # ── Mapped Types ────────────────────────────────────────
        'nestjs-mapped-types': re.compile(
            r"from\s+['\"]@nestjs/mapped-types['\"]|PartialType|PickType|OmitType|IntersectionType",
            re.MULTILINE
        ),

        # ── CLI ──────────────────────────────────────────────────
        'nestjs-cli': re.compile(
            r"nest-cli\.json|@nestjs/cli",
            re.MULTILINE
        ),
    }

    # NestJS version detection from features
    NESTJS_VERSION_FEATURES = {
        # NestJS 10.x features
        'SWC': '10.0',
        '@nestjs/cache-manager': '10.0',

        # NestJS 9.x features
        'REPL': '9.0',
        'ConfigurableModuleBuilder': '9.0',
        'LazyModuleLoader': '9.0',

        # NestJS 8.x features
        'standalone application': '8.0',
        'NestFactory.createApplicationContext': '8.0',

        # NestJS 7.x features
        '@nestjs/common': '7.0',
        '@Module': '7.0',
        '@Controller': '7.0',
        '@Injectable': '7.0',
    }

    def __init__(self):
        """Initialize the parser with all NestJS enhanced extractors."""
        self.module_extractor = NestModuleExtractor()
        self.controller_extractor = NestControllerExtractor()
        self.provider_extractor = NestProviderExtractor()
        self.config_extractor = NestConfigExtractor()
        self.api_extractor = NestApiExtractor()

    def parse(self, content: str, file_path: str = "") -> NestJSEnhancedParseResult:
        """
        Parse NestJS source code and extract all NestJS-specific information.

        This should be called AFTER the TypeScript parser has run, when
        NestJS framework is detected.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            NestJSEnhancedParseResult with all extracted NestJS information
        """
        result = NestJSEnhancedParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Modules ──────────────────────────────────────────────
        mod_result = self.module_extractor.extract(content, file_path)
        result.modules = mod_result.get('modules', [])
        result.module_providers = mod_result.get('providers', [])
        result.dynamic_modules = mod_result.get('dynamic_modules', [])

        # ── Controllers ──────────────────────────────────────────
        ctrl_result = self.controller_extractor.extract(content, file_path)
        result.controllers = ctrl_result.get('controllers', [])
        result.param_decorators = ctrl_result.get('param_decorators', [])
        result.total_endpoints = sum(c.total_endpoints for c in result.controllers)

        # ── Providers ────────────────────────────────────────────
        prov_result = self.provider_extractor.extract(content, file_path)
        result.injectables = prov_result.get('injectables', [])
        result.injections = prov_result.get('injections', [])
        result.custom_providers = prov_result.get('custom_providers', [])
        result.total_injectables = len(result.injectables)
        result.total_injections = len(result.injections)

        # ── Config ───────────────────────────────────────────────
        cfg_result = self.config_extractor.extract(content, file_path)
        result.config_modules = cfg_result.get('config_modules', [])
        result.env_vars = cfg_result.get('env_vars', [])
        result.config_usages = cfg_result.get('config_usages', [])

        # ── API/Swagger ──────────────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.swagger_decorators = api_result.get('swagger_decorators', [])
        result.api_properties = api_result.get('api_properties', [])
        result.dtos = api_result.get('dtos', [])
        result.api_summary = api_result.get('summary')
        result.has_swagger = result.api_summary.has_swagger if result.api_summary else False
        result.has_validation = result.api_summary.has_validation if result.api_summary else False

        # ── Version detection ────────────────────────────────────
        result.nestjs_version = self._detect_nestjs_version(content)

        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a NestJS file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        # By NestJS filename conventions
        if '.module.' in basename:
            return 'module'
        if '.controller.' in basename:
            return 'controller'
        if '.service.' in basename:
            return 'service'
        if '.guard.' in basename:
            return 'guard'
        if '.interceptor.' in basename:
            return 'interceptor'
        if '.pipe.' in basename:
            return 'pipe'
        if '.middleware.' in basename:
            return 'middleware'
        if '.filter.' in basename or '.exception-filter.' in basename:
            return 'filter'
        if '.gateway.' in basename:
            return 'gateway'
        if '.dto.' in basename:
            return 'dto'
        if '.entity.' in basename or '.schema.' in basename:
            return 'entity'
        if '.resolver.' in basename:
            return 'resolver'
        if '.spec.' in basename or '.test.' in basename:
            return 'test'
        if basename == 'main.ts' or basename == 'main.js':
            return 'main'

        # By content
        if '@Module(' in content:
            return 'module'
        if '@Controller(' in content:
            return 'controller'
        if '@Injectable(' in content:
            return 'service'
        if '@Resolver(' in content:
            return 'resolver'
        if '@WebSocketGateway' in content:
            return 'gateway'

        return 'service'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which NestJS ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_nestjs_version(self, content: str) -> str:
        """Detect the minimum NestJS version required."""
        max_version = '0.0'
        for feature, version in self.NESTJS_VERSION_FEATURES.items():
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

    def is_nestjs_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a NestJS-specific file worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file contains NestJS-specific patterns
        """
        # NestJS imports
        if re.search(r"from\s+['\"]@nestjs/", content):
            return True

        # NestJS decorators
        nestjs_decorators = [
            '@Module(', '@Controller(', '@Injectable(', '@Inject(',
            '@Get(', '@Post(', '@Put(', '@Delete(', '@Patch(',
            '@UseGuards(', '@UseInterceptors(', '@UsePipes(',
            '@WebSocketGateway', '@SubscribeMessage(',
            '@Resolver(', '@Query()', '@Mutation(',
            '@MessagePattern(', '@EventPattern(',
            '@ApiTags(', '@ApiProperty(',
        ]
        for decorator in nestjs_decorators:
            if decorator in content:
                return True

        # NestJS filename conventions
        normalized = file_path.replace('\\', '/').lower()
        nestjs_suffixes = [
            '.module.ts', '.controller.ts', '.service.ts',
            '.guard.ts', '.interceptor.ts', '.pipe.ts',
            '.middleware.ts', '.filter.ts', '.gateway.ts',
            '.dto.ts', '.entity.ts', '.resolver.ts',
        ]
        for suffix in nestjs_suffixes:
            if normalized.endswith(suffix):
                return True

        return False
