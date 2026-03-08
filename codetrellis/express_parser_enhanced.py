"""
EnhancedExpressParser v1.0 - Comprehensive Express.js parser using all extractors.

This parser integrates all Express.js extractors to provide complete parsing of
Express.js application files. It runs as a supplementary layer on top of the
JavaScript/TypeScript parsers, extracting Express.js-specific semantics.

Supports:
- Express.js 3.x (basic routing, connect-based middleware, app.configure())
- Express.js 4.x (Router, modular middleware, no built-in body-parser/cookie-parser,
                   app.route(), express.static(), sub-apps, middleware composition)
- Express.js 5.x (async/await route handlers, improved path matching, req.query
                   parser, promise-based middleware, rejected promise handling)

Express.js-specific extraction:
- Routes: app.get/post/put/delete/patch/options/head/all(), Router(), app.route()
- Middleware: app.use(), global/route/error middleware, ordering, built-in + third-party
- Error Handling: (err, req, res, next) handlers, custom error classes, async errors
- Configuration: app.set(), app.enable/disable(), view engines, trust proxy, listen
- API Patterns: RESTful resources, versioning, response types, validation, pagination

Framework detection (30+ Express.js ecosystem patterns):
- Core: express, express.Router, express.json, express.urlencoded, express.static
- Security: helmet, cors, csurf, hpp, express-mongo-sanitize, xss-clean
- Auth: passport, express-jwt, jsonwebtoken, express-session, connect-redis
- Validation: express-validator, joi, yup, zod, celebrate
- Database: mongoose, sequelize, typeorm, knex, prisma, pg, mysql2, mongodb
- Logging: morgan, winston, pino, bunyan
- Testing: supertest, chai-http, jest
- Documentation: swagger-ui-express, express-openapi-validator, tsoa
- File Upload: multer, busboy, formidable
- Rate Limiting: express-rate-limit, express-slow-down
- Template Engines: ejs, pug, handlebars, mustache, nunjucks
- WebSockets: socket.io, ws, express-ws
- Process: pm2, cluster, nodemon
- Monitoring: express-status-monitor, response-time, express-prometheus-middleware

Optional AST support via tree-sitter-typescript / tree-sitter-javascript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.33 - Express.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Express.js extractors
from .extractors.express import (
    ExpressRouteExtractor, ExpressRouteInfo, ExpressRouterInfo, ExpressParamInfo,
    ExpressMiddlewareExtractor, ExpressMiddlewareInfo, ExpressMiddlewareStackInfo,
    ExpressErrorExtractor, ExpressErrorHandlerInfo, ExpressCustomErrorInfo, ExpressErrorSummary,
    ExpressConfigExtractor, ExpressSettingInfo, ExpressAppInfo, ExpressServerInfo, ExpressConfigSummary,
    ExpressApiExtractor, ExpressResourceInfo, ExpressResponsePatternInfo, ExpressApiVersionInfo, ExpressApiSummary,
)


@dataclass
class ExpressParseResult:
    """Complete parse result for an Express.js file."""
    file_path: str
    file_type: str = "route"  # route, middleware, config, error, controller, model, service, app, test

    # Routes
    routes: List[ExpressRouteInfo] = field(default_factory=list)
    routers: List[ExpressRouterInfo] = field(default_factory=list)
    params: List[ExpressParamInfo] = field(default_factory=list)

    # Middleware
    middleware: List[ExpressMiddlewareInfo] = field(default_factory=list)
    middleware_stack: Optional[ExpressMiddlewareStackInfo] = None

    # Error Handling
    error_handlers: List[ExpressErrorHandlerInfo] = field(default_factory=list)
    custom_errors: List[ExpressCustomErrorInfo] = field(default_factory=list)
    error_summary: Optional[ExpressErrorSummary] = None

    # Configuration
    settings: List[ExpressSettingInfo] = field(default_factory=list)
    apps: List[ExpressAppInfo] = field(default_factory=list)
    servers: List[ExpressServerInfo] = field(default_factory=list)
    config_summary: Optional[ExpressConfigSummary] = None

    # API Patterns
    resources: List[ExpressResourceInfo] = field(default_factory=list)
    response_patterns: List[ExpressResponsePatternInfo] = field(default_factory=list)
    api_versions: List[ExpressApiVersionInfo] = field(default_factory=list)
    api_summary: Optional[ExpressApiSummary] = None

    # Aggregate signals
    detected_frameworks: List[str] = field(default_factory=list)
    express_version: str = ""  # Detected minimum Express.js version
    is_typescript: bool = False
    total_routes: int = 0
    total_middleware: int = 0
    total_error_handlers: int = 0


class EnhancedExpressParser:
    """
    Enhanced Express.js parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript/TypeScript parsers
    when Express.js framework is detected. It extracts Express.js-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 30+ Express.js ecosystem libraries across:
    - Core (express, express.Router)
    - Security (helmet, cors, csurf, hpp)
    - Auth (passport, express-jwt, jsonwebtoken, express-session)
    - Validation (express-validator, joi, yup, zod, celebrate)
    - Database (mongoose, sequelize, typeorm, knex, prisma)
    - Logging (morgan, winston, pino)
    - Documentation (swagger-ui-express, tsoa)
    - File Upload (multer, busboy)
    - Rate Limiting (express-rate-limit)
    - Template Engines (ejs, pug, handlebars)
    - WebSockets (socket.io, ws, express-ws)

    Optional AST: tree-sitter-typescript / tree-sitter-javascript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Express.js ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core Express.js ───────────────────────────────────────
        'express': re.compile(
            r"from\s+['\"]express['\"]|require\(['\"]express['\"]\)|"
            r"express\(\)|express\.Router|express\.json|express\.urlencoded|"
            r"express\.static",
            re.MULTILINE
        ),

        # ── Security ─────────────────────────────────────────────
        'helmet': re.compile(
            r"from\s+['\"]helmet['\"]|require\(['\"]helmet['\"]\)|helmet\(",
            re.MULTILINE
        ),
        'cors': re.compile(
            r"from\s+['\"]cors['\"]|require\(['\"]cors['\"]\)|cors\(",
            re.MULTILINE
        ),
        'csurf': re.compile(
            r"from\s+['\"]csurf['\"]|require\(['\"]csurf['\"]\)|csrf\(",
            re.MULTILINE
        ),
        'hpp': re.compile(
            r"from\s+['\"]hpp['\"]|require\(['\"]hpp['\"]\)|hpp\(",
            re.MULTILINE
        ),

        # ── Auth ─────────────────────────────────────────────────
        'passport': re.compile(
            r"from\s+['\"]passport['\"]|require\(['\"]passport['\"]\)|"
            r"passport\.authenticate|passport\.initialize|passport\.session|"
            r"passport\.use",
            re.MULTILINE
        ),
        'express-jwt': re.compile(
            r"from\s+['\"]express-jwt['\"]|require\(['\"]express-jwt['\"]\)|"
            r"expressjwt\(|jwt\({",
            re.MULTILINE
        ),
        'jsonwebtoken': re.compile(
            r"from\s+['\"]jsonwebtoken['\"]|require\(['\"]jsonwebtoken['\"]\)|"
            r"jwt\.sign|jwt\.verify|jwt\.decode",
            re.MULTILINE
        ),
        'express-session': re.compile(
            r"from\s+['\"]express-session['\"]|require\(['\"]express-session['\"]\)|"
            r"session\({.*(?:secret|store)",
            re.MULTILINE
        ),
        'connect-redis': re.compile(
            r"from\s+['\"]connect-redis['\"]|require\(['\"]connect-redis['\"]\)|"
            r"RedisStore",
            re.MULTILINE
        ),

        # ── Validation ───────────────────────────────────────────
        'express-validator': re.compile(
            r"from\s+['\"]express-validator['\"]|require\(['\"]express-validator['\"]\)|"
            r"body\(|param\(|query\(|check\(|validationResult",
            re.MULTILINE
        ),
        'joi': re.compile(
            r"from\s+['\"]joi['\"]|require\(['\"]joi['\"]\)|Joi\.",
            re.MULTILINE
        ),
        'zod': re.compile(
            r"from\s+['\"]zod['\"]|require\(['\"]zod['\"]\)|z\.\w+\(",
            re.MULTILINE
        ),
        'celebrate': re.compile(
            r"from\s+['\"]celebrate['\"]|require\(['\"]celebrate['\"]\)|"
            r"celebrate\(|Segments\.",
            re.MULTILINE
        ),

        # ── Database ─────────────────────────────────────────────
        'mongoose': re.compile(
            r"from\s+['\"]mongoose['\"]|require\(['\"]mongoose['\"]\)|"
            r"mongoose\.connect|mongoose\.model|Schema\(|new\s+Schema",
            re.MULTILINE
        ),
        'sequelize': re.compile(
            r"from\s+['\"]sequelize['\"]|require\(['\"]sequelize['\"]\)|"
            r"Sequelize|sequelize\.define|Model\.init",
            re.MULTILINE
        ),
        'typeorm': re.compile(
            r"from\s+['\"]typeorm['\"]|@Entity|@Column|@PrimaryGeneratedColumn|"
            r"getRepository|createConnection",
            re.MULTILINE
        ),
        'knex': re.compile(
            r"from\s+['\"]knex['\"]|require\(['\"]knex['\"]\)|knex\(",
            re.MULTILINE
        ),
        'prisma': re.compile(
            r"from\s+['\"]@prisma/client['\"]|PrismaClient|prisma\.\w+",
            re.MULTILINE
        ),
        'pg': re.compile(
            r"from\s+['\"]pg['\"]|require\(['\"]pg['\"]\)|new\s+Pool\(|"
            r"pool\.query",
            re.MULTILINE
        ),
        'mysql2': re.compile(
            r"from\s+['\"]mysql2['\"]|require\(['\"]mysql2['\"]\)|"
            r"mysql\.createConnection|mysql\.createPool",
            re.MULTILINE
        ),
        'mongodb': re.compile(
            r"from\s+['\"]mongodb['\"]|require\(['\"]mongodb['\"]\)|"
            r"MongoClient|new\s+MongoClient",
            re.MULTILINE
        ),

        # ── Logging ──────────────────────────────────────────────
        'morgan': re.compile(
            r"from\s+['\"]morgan['\"]|require\(['\"]morgan['\"]\)|morgan\(",
            re.MULTILINE
        ),
        'winston': re.compile(
            r"from\s+['\"]winston['\"]|require\(['\"]winston['\"]\)|"
            r"winston\.createLogger|winston\.format",
            re.MULTILINE
        ),
        'pino': re.compile(
            r"from\s+['\"]pino['\"]|from\s+['\"]pino-http['\"]|"
            r"require\(['\"]pino['\"]\)|pino\(|pinoHttp\(",
            re.MULTILINE
        ),
        'bunyan': re.compile(
            r"from\s+['\"]bunyan['\"]|require\(['\"]bunyan['\"]\)|"
            r"bunyan\.createLogger",
            re.MULTILINE
        ),

        # ── Testing ──────────────────────────────────────────────
        'supertest': re.compile(
            r"from\s+['\"]supertest['\"]|require\(['\"]supertest['\"]\)|"
            r"request\(app\)|supertest\(",
            re.MULTILINE
        ),

        # ── Documentation ────────────────────────────────────────
        'swagger-ui-express': re.compile(
            r"from\s+['\"]swagger-ui-express['\"]|require\(['\"]swagger-ui-express['\"]\)|"
            r"swaggerUi\.setup|swaggerUi\.serve",
            re.MULTILINE
        ),
        'tsoa': re.compile(
            r"from\s+['\"]tsoa['\"]|@Route\(|@Get\(|@Post\(|@Controller\(",
            re.MULTILINE
        ),
        'express-openapi-validator': re.compile(
            r"from\s+['\"]express-openapi-validator['\"]|OpenApiValidator",
            re.MULTILINE
        ),

        # ── File Upload ──────────────────────────────────────────
        'multer': re.compile(
            r"from\s+['\"]multer['\"]|require\(['\"]multer['\"]\)|"
            r"multer\(|upload\.single|upload\.array|upload\.fields",
            re.MULTILINE
        ),
        'busboy': re.compile(
            r"from\s+['\"]busboy['\"]|require\(['\"]busboy['\"]\)",
            re.MULTILINE
        ),

        # ── Rate Limiting ────────────────────────────────────────
        'express-rate-limit': re.compile(
            r"from\s+['\"]express-rate-limit['\"]|require\(['\"]express-rate-limit['\"]\)|"
            r"rateLimit\(|rateLimiter",
            re.MULTILINE
        ),

        # ── Template Engines ─────────────────────────────────────
        'ejs': re.compile(
            r"from\s+['\"]ejs['\"]|require\(['\"]ejs['\"]\)|"
            r"set\(['\"]view engine['\"],\s*['\"]ejs['\"]\)",
            re.MULTILINE
        ),
        'pug': re.compile(
            r"from\s+['\"]pug['\"]|require\(['\"]pug['\"]\)|"
            r"set\(['\"]view engine['\"],\s*['\"]pug['\"]\)",
            re.MULTILINE
        ),
        'handlebars': re.compile(
            r"from\s+['\"]express-handlebars['\"]|require\(['\"]express-handlebars['\"]\)|"
            r"exphbs|hbs|handlebars",
            re.MULTILINE
        ),

        # ── WebSockets ───────────────────────────────────────────
        'socket.io': re.compile(
            r"from\s+['\"]socket\.io['\"]|require\(['\"]socket\.io['\"]\)|"
            r"new\s+Server\(.*http|io\.on\(",
            re.MULTILINE
        ),
        'ws': re.compile(
            r"from\s+['\"]ws['\"]|require\(['\"]ws['\"]\)|"
            r"new\s+WebSocket\.Server|WebSocketServer",
            re.MULTILINE
        ),
        'express-ws': re.compile(
            r"from\s+['\"]express-ws['\"]|require\(['\"]express-ws['\"]\)|"
            r"expressWs\(|\.ws\(",
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
        'express-status-monitor': re.compile(
            r"from\s+['\"]express-status-monitor['\"]|require\(['\"]express-status-monitor['\"]\)",
            re.MULTILINE
        ),
        'response-time': re.compile(
            r"from\s+['\"]response-time['\"]|require\(['\"]response-time['\"]\)|"
            r"responseTime\(",
            re.MULTILINE
        ),

        # ── Compression ──────────────────────────────────────────
        'compression': re.compile(
            r"from\s+['\"]compression['\"]|require\(['\"]compression['\"]\)|"
            r"compression\(",
            re.MULTILINE
        ),

        # ── Cookie/Session ───────────────────────────────────────
        'cookie-parser': re.compile(
            r"from\s+['\"]cookie-parser['\"]|require\(['\"]cookie-parser['\"]\)|"
            r"cookieParser\(",
            re.MULTILINE
        ),
    }

    # Express.js version detection from features
    EXPRESS_VERSION_FEATURES = {
        # Express 5.x features
        'app.router': '5.0',  # removed in 5.x
        'req.hostname': '5.0',
        'express.urlencoded': '4.16',
        'express.json': '4.16',
        'express.Router': '4.0',
        'router.route': '4.0',
        'app.route': '4.0',
        'express.static': '4.0',
    }

    def __init__(self):
        """Initialize the parser with all Express.js extractors."""
        self.route_extractor = ExpressRouteExtractor()
        self.middleware_extractor = ExpressMiddlewareExtractor()
        self.error_extractor = ExpressErrorExtractor()
        self.config_extractor = ExpressConfigExtractor()
        self.api_extractor = ExpressApiExtractor()

    def parse(self, content: str, file_path: str = "") -> ExpressParseResult:
        """
        Parse Express.js source code and extract all Express.js-specific information.

        This should be called AFTER the JS/TS parsers have run, when
        Express.js framework is detected. It extracts Express.js-specific semantics.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            ExpressParseResult with all extracted Express.js information
        """
        result = ExpressParseResult(file_path=file_path)

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

        # ── Error Handling ───────────────────────────────────────
        error_result = self.error_extractor.extract(content, file_path)
        result.error_handlers = error_result.get('error_handlers', [])
        result.custom_errors = error_result.get('custom_errors', [])
        result.error_summary = error_result.get('summary')
        result.total_error_handlers = len(result.error_handlers)

        # ── Configuration ────────────────────────────────────────
        config_result = self.config_extractor.extract(content, file_path)
        result.settings = config_result.get('settings', [])
        result.apps = config_result.get('apps', [])
        result.servers = config_result.get('servers', [])
        result.config_summary = config_result.get('summary')

        # ── API Patterns ─────────────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.resources = api_result.get('resources', [])
        result.response_patterns = api_result.get('response_patterns', [])
        result.api_versions = api_result.get('api_versions', [])
        result.api_summary = api_result.get('summary')

        # ── Version detection ────────────────────────────────────
        result.express_version = self._detect_express_version(content)

        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify an Express.js file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        # By filename conventions
        if 'app.' in basename or 'server.' in basename or 'index.' in basename:
            if 'express' in content or 'app.listen' in content or 'createServer' in content:
                return 'app'
        if 'route' in basename:
            return 'route'
        if 'middleware' in basename:
            return 'middleware'
        if 'error' in basename:
            return 'error'
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
        if '/errors/' in normalized:
            return 'error'

        # By content
        if 'Router()' in content or 'express.Router' in content:
            return 'route'
        if re.search(r'\(err\w*,\s*req\w*,\s*res\w*,\s*next\)', content):
            return 'error'

        return 'route'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Express.js ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_express_version(self, content: str) -> str:
        """
        Detect the minimum Express.js version required by the file.

        Returns version string (e.g., '5.0', '4.16', '4.0').
        Detection is based on features used in the code.
        """
        max_version = '0.0'

        for feature, version in self.EXPRESS_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version

        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1>v2, <0 if v1<v2, 0 if equal."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_express_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is an Express.js-specific file worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file contains Express.js-specific patterns
        """
        # Direct express imports
        if re.search(r"from\s+['\"]express['\"]|require\(['\"]express['\"]\)", content):
            return True

        # Express app creation
        if re.search(r'express\(\)', content):
            return True

        # Express Router
        if re.search(r'express\.Router\(\)|Router\(\)', content):
            return True

        # Express middleware patterns
        if re.search(r'express\.json\(|express\.urlencoded\(|express\.static\(', content):
            return True

        # Route definitions with common Express receiver names
        if re.search(r'(?:app|router|server)\s*\.\s*(?:get|post|put|delete|patch|all|use)\s*\(', content):
            # Additional check: must also have req/res in scope
            if re.search(r'\b(?:req|res|next)\b', content):
                return True

        # Error handler signature
        if re.search(r'\(\s*err\w*\s*,\s*req\w*\s*,\s*res\w*\s*,\s*next\w*\s*\)', content):
            return True

        # Express-specific packages
        express_packages = [
            'express-validator', 'express-session', 'express-rate-limit',
            'express-jwt', 'express-ws', 'express-async-errors',
            'express-openapi-validator', 'express-status-monitor',
        ]
        for pkg in express_packages:
            if pkg in content:
                return True

        # File path conventions for Express projects
        normalized = file_path.replace('\\', '/').lower()
        if any(p in normalized for p in ['/routes/', '/middleware/', '/controllers/']):
            if re.search(r'\b(?:req|res|next)\b', content):
                return True

        return False
