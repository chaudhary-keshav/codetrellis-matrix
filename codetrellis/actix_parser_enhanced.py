"""
EnhancedActixParser v1.0 - Comprehensive Actix Web framework parser.

Extracts Actix Web-specific patterns from Rust source files:
- Route handlers (#[get], #[post], web::resource, web::scope)
- Middleware (wrap, wrap_fn, Transform trait)
- Extractors (web::Json, web::Path, web::Query, web::Data)
- Application state (web::Data<T>, App::app_data)
- Error handling (ResponseError, error::ErrorXxx)
- Guards (guard::Get, guard::fn_guard)
- WebSocket actors
- Configuration (HttpServer, App::configure)
- Service configuration
- Test utilities (test::init_service, test::call_service)

Supports Actix Web 0.x through 4.x+.

Part of CodeTrellis - Rust Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# ─── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class ActixRouteInfo:
    """Actix Web route definition."""
    method: str
    path: str
    handler: str
    file: str = ""
    line_number: int = 0
    is_async: bool = True
    extractors: List[str] = field(default_factory=list)
    guards: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    response_type: str = ""


@dataclass
class ActixScopeInfo:
    """Actix Web scope/resource grouping."""
    path: str
    routes: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    guards: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class ActixMiddlewareInfo:
    """Actix Web middleware definition."""
    name: str
    kind: str = ""  # wrap, wrap_fn, transform, from_fn
    file: str = ""
    line_number: int = 0
    is_custom: bool = False


@dataclass
class ActixExtractorUsage:
    """Actix Web extractor usage in handlers."""
    extractor_type: str  # Json, Path, Query, Data, Form, Bytes, etc.
    inner_type: str = ""
    handler: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class ActixStateInfo:
    """Actix Web application state."""
    type_name: str
    registration: str = ""  # app_data, data, configure
    file: str = ""
    line_number: int = 0


@dataclass
class ActixErrorHandlerInfo:
    """Actix Web error handling."""
    name: str
    kind: str = ""  # ResponseError impl, error handler, JsonConfig error
    status_code: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class ActixWebSocketInfo:
    """Actix Web WebSocket endpoint."""
    handler: str
    path: str = ""
    actor: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class ActixConfigInfo:
    """Actix Web server/app configuration."""
    kind: str  # server, app, service, json, cors
    setting: str = ""
    value: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class ActixTestInfo:
    """Actix Web test utility usage."""
    kind: str  # init_service, call_service, TestRequest, test_app
    handler: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class ActixParseResult:
    """Complete parse result for Actix Web framework analysis."""
    file_path: str
    file_type: str = "rust"

    # Routes
    routes: List[ActixRouteInfo] = field(default_factory=list)
    scopes: List[ActixScopeInfo] = field(default_factory=list)

    # Middleware
    middleware: List[ActixMiddlewareInfo] = field(default_factory=list)

    # Extractors
    extractors: List[ActixExtractorUsage] = field(default_factory=list)

    # State
    app_state: List[ActixStateInfo] = field(default_factory=list)

    # Error handling
    error_handlers: List[ActixErrorHandlerInfo] = field(default_factory=list)

    # WebSockets
    websockets: List[ActixWebSocketInfo] = field(default_factory=list)

    # Configuration
    configs: List[ActixConfigInfo] = field(default_factory=list)

    # Tests
    tests: List[ActixTestInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    actix_version: str = ""


# ─── Parser ─────────────────────────────────────────────────────────────────────

class EnhancedActixParser:
    """
    Enhanced Actix Web parser for comprehensive framework analysis.

    Supports Actix Web 0.x through 4.x+:
    - v0.x-1.x: actix-web with Actor system
    - v2.x: Major API redesign, async handlers
    - v3.x: actix-rt 2.x, improved middleware
    - v4.x: Extractors overhaul, new middleware API, improved guards
    """

    # Detection: is this file using Actix Web?
    ACTIX_DETECT = re.compile(
        r'(?:use\s+actix_web|actix_web::|actix_rt|HttpServer::new|#\[actix_web::)',
        re.MULTILINE
    )

    # Framework ecosystem detection
    FRAMEWORK_PATTERNS = {
        'actix-web': re.compile(r'\bactix_web\b'),
        'actix-rt': re.compile(r'\bactix_rt\b'),
        'actix-files': re.compile(r'\bactix_files\b'),
        'actix-multipart': re.compile(r'\bactix_multipart\b'),
        'actix-session': re.compile(r'\bactix_session\b'),
        'actix-identity': re.compile(r'\bactix_identity\b'),
        'actix-cors': re.compile(r'\bactix_cors\b'),
        'actix-ws': re.compile(r'\bactix_ws\b'),
        'actix-web-actors': re.compile(r'\bactix_web_actors\b'),
        'actix-web-httpauth': re.compile(r'\bactix_web_httpauth\b'),
        'actix-protobuf': re.compile(r'\bactix_protobuf\b'),
        'actix-limitation': re.compile(r'\bactix_limitation\b'),
    }

    # Route attribute macros: #[get("/path")], #[post("/path")], etc.
    ROUTE_ATTR = re.compile(
        r'#\[(?:actix_web::)?(?P<method>get|post|put|delete|patch|head|options)\s*\(\s*"(?P<path>[^"]+)"',
        re.MULTILINE
    )

    # Generic route macro: #[route("/path", method = "GET")]
    ROUTE_GENERIC = re.compile(
        r'#\[route\s*\(\s*"(?P<path>[^"]+)"\s*,\s*method\s*=\s*"(?P<method>[A-Z]+)"',
        re.MULTILINE
    )

    # Handler function after route attr
    HANDLER_FN = re.compile(
        r'(?:pub\s+)?(?:async\s+)?fn\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)',
        re.MULTILINE
    )

    # web::resource / web::scope
    RESOURCE_SCOPE = re.compile(
        r'web::(?P<kind>resource|scope)\s*\(\s*"(?P<path>[^"]+)"',
        re.MULTILINE
    )

    # Service registration: .service(xxx)
    SERVICE_REG = re.compile(
        r'\.service\s*\(\s*(?:web::(?:resource|scope)\s*\(\s*"(?P<path>[^"]+)")?(?P<handler>\w+)?',
        re.MULTILINE
    )

    # .route() on resource: .route(web::get().to(handler))
    RESOURCE_ROUTE = re.compile(
        r'\.route\s*\(\s*web::(?P<method>get|post|put|delete|patch|head)\s*\(\s*\)\s*\.to\s*\(\s*(?P<handler>\w+)',
        re.MULTILINE
    )

    # Middleware: .wrap() / .wrap_fn()
    WRAP_MIDDLEWARE = re.compile(
        r'\.(?P<kind>wrap|wrap_fn)\s*\(\s*(?P<middleware>[^)]+)',
        re.MULTILINE
    )

    # from_fn middleware (v4+)
    FROM_FN_MIDDLEWARE = re.compile(
        r'middleware::from_fn\s*\(\s*(?P<name>\w+)',
        re.MULTILINE
    )

    # Extractors in function params
    EXTRACTOR_PATTERN = re.compile(
        r'(?:web::)?(?P<type>Json|Path|Query|Data|Form|Bytes|Payload|HttpRequest|HttpResponse)\s*<\s*(?P<inner>[^>]+)>',
        re.MULTILINE
    )

    # App data / state registration
    APP_DATA = re.compile(
        r'\.(?P<reg>app_data|data)\s*\(\s*(?:web::Data::new\s*\(\s*)?(?P<type>\w+)',
        re.MULTILINE
    )

    # ResponseError impl
    RESPONSE_ERROR = re.compile(
        r'impl\s+(?:actix_web::)?ResponseError\s+for\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # error:: factory functions
    ERROR_FACTORY = re.compile(
        r'error::(?P<kind>Error\w+)\s*\(',
        re.MULTILINE
    )

    # HttpServer config
    SERVER_CONFIG = re.compile(
        r'HttpServer::new\s*\(|\.bind\s*\(\s*"(?P<addr>[^"]+)"|\.'
        r'(?P<setting>workers|keep_alive|client_request_timeout|shutdown_timeout)\s*\(\s*(?P<value>[^)]+)',
        re.MULTILINE
    )

    # WebSocket
    WS_START = re.compile(
        r'(?:ws::start|actix_ws::handle|web::Payload)\s*.*?\bws\b',
        re.MULTILINE
    )

    # Test utilities
    TEST_UTIL = re.compile(
        r'(?:actix_web::)?test::(?P<kind>init_service|call_service|TestRequest|read_body|read_body_json)',
        re.MULTILINE
    )

    # Guard patterns
    GUARD_PATTERN = re.compile(
        r'\.guard\s*\(\s*(?:guard::)?(?P<guard>\w+)',
        re.MULTILINE
    )

    # App::configure
    CONFIGURE = re.compile(
        r'\.configure\s*\(\s*(?P<fn>\w+)',
        re.MULTILINE
    )

    # CORS config
    CORS_CONFIG = re.compile(
        r'Cors::(?P<kind>default|permissive)\s*\(\)|\.allowed_origin|\.allowed_methods|\.max_age',
        re.MULTILINE
    )

    # Version detection features
    VERSION_FEATURES = {
        '4.0': [r'middleware::from_fn', r'web::Redirect', r'#\[actix_web::test\]'],
        '3.0': [r'actix_rt::main', r'#\[actix_web::main\]', r'App::new\(\)\.app_data'],
        '2.0': [r'HttpServer::new', r'web::Json', r'web::Data'],
        '1.0': [r'actix_web::server', r'App::with_state'],
    }

    def __init__(self):
        """Initialize the parser."""
        pass

    def parse(self, content: str, file_path: str = "") -> ActixParseResult:
        """Parse Rust file for Actix Web patterns."""
        result = ActixParseResult(file_path=file_path)

        # Self-selection: only parse if Actix Web is detected
        if not self.ACTIX_DETECT.search(content):
            return result

        # Detect ecosystem
        result.detected_frameworks = self._detect_frameworks(content)
        result.actix_version = self._detect_version(content)

        # Extract routes
        result.routes = self._extract_routes(content, file_path)
        result.scopes = self._extract_scopes(content, file_path)

        # Extract middleware
        result.middleware = self._extract_middleware(content, file_path)

        # Extract extractors
        result.extractors = self._extract_extractors(content, file_path)

        # Extract app state
        result.app_state = self._extract_state(content, file_path)

        # Extract error handling
        result.error_handlers = self._extract_errors(content, file_path)

        # Extract WebSocket endpoints
        result.websockets = self._extract_websockets(content, file_path)

        # Extract configuration
        result.configs = self._extract_configs(content, file_path)

        # Extract test utilities
        result.tests = self._extract_tests(content, file_path)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_version(self, content: str) -> str:
        for version, patterns in self.VERSION_FEATURES.items():
            for pat in patterns:
                if re.search(pat, content):
                    return version
        return ""

    def _extract_routes(self, content: str, file_path: str) -> List[ActixRouteInfo]:
        routes = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Attribute route macros
            m = self.ROUTE_ATTR.search(line)
            if m:
                method = m.group('method').upper()
                path = m.group('path')
                # Find handler on next lines
                handler = ""
                extractors = []
                for j in range(i, min(i + 5, len(lines) + 1)):
                    hm = self.HANDLER_FN.search(lines[j - 1])
                    if hm:
                        handler = hm.group('name')
                        params = hm.group('params')
                        extractors = self._parse_extractor_params(params)
                        break
                routes.append(ActixRouteInfo(
                    method=method, path=path, handler=handler,
                    file=file_path, line_number=i, extractors=extractors,
                ))
                continue

            # Generic #[route] macro
            m = self.ROUTE_GENERIC.search(line)
            if m:
                handler = ""
                for j in range(i, min(i + 5, len(lines) + 1)):
                    hm = self.HANDLER_FN.search(lines[j - 1])
                    if hm:
                        handler = hm.group('name')
                        break
                routes.append(ActixRouteInfo(
                    method=m.group('method'), path=m.group('path'),
                    handler=handler, file=file_path, line_number=i,
                ))
                continue

            # Resource route: .route(web::get().to(handler))
            m = self.RESOURCE_ROUTE.search(line)
            if m:
                routes.append(ActixRouteInfo(
                    method=m.group('method').upper(),
                    path="", handler=m.group('handler'),
                    file=file_path, line_number=i,
                ))

        return routes

    def _extract_scopes(self, content: str, file_path: str) -> List[ActixScopeInfo]:
        scopes = []
        for m in self.RESOURCE_SCOPE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            scopes.append(ActixScopeInfo(
                path=m.group('path'),
                file=file_path, line_number=line_num,
            ))
        return scopes

    def _extract_middleware(self, content: str, file_path: str) -> List[ActixMiddlewareInfo]:
        middleware = []
        seen = set()

        for m in self.WRAP_MIDDLEWARE.finditer(content):
            name = m.group('middleware').strip().split('(')[0].strip()
            if name and name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                middleware.append(ActixMiddlewareInfo(
                    name=name, kind=m.group('kind'),
                    file=file_path, line_number=line_num,
                ))

        for m in self.FROM_FN_MIDDLEWARE.finditer(content):
            name = m.group('name')
            if name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                middleware.append(ActixMiddlewareInfo(
                    name=name, kind='from_fn', is_custom=True,
                    file=file_path, line_number=line_num,
                ))

        # Transform trait implementations
        transform_re = re.compile(
            r'impl\s+(?:<[^>]+>\s+)?Transform\s*<[^>]+>\s+for\s+(\w+)',
            re.MULTILINE
        )
        for m in transform_re.finditer(content):
            name = m.group(1)
            if name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                middleware.append(ActixMiddlewareInfo(
                    name=name, kind='transform', is_custom=True,
                    file=file_path, line_number=line_num,
                ))

        return middleware

    def _extract_extractors(self, content: str, file_path: str) -> List[ActixExtractorUsage]:
        extractors = []
        for m in self.EXTRACTOR_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            extractors.append(ActixExtractorUsage(
                extractor_type=m.group('type'),
                inner_type=m.group('inner').strip(),
                file=file_path, line_number=line_num,
            ))
        return extractors

    def _extract_state(self, content: str, file_path: str) -> List[ActixStateInfo]:
        states = []
        seen = set()
        for m in self.APP_DATA.finditer(content):
            type_name = m.group('type')
            if type_name not in seen:
                seen.add(type_name)
                line_num = content[:m.start()].count('\n') + 1
                states.append(ActixStateInfo(
                    type_name=type_name, registration=m.group('reg'),
                    file=file_path, line_number=line_num,
                ))
        return states

    def _extract_errors(self, content: str, file_path: str) -> List[ActixErrorHandlerInfo]:
        errors = []
        for m in self.RESPONSE_ERROR.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            errors.append(ActixErrorHandlerInfo(
                name=m.group('name'), kind='ResponseError',
                file=file_path, line_number=line_num,
            ))
        for m in self.ERROR_FACTORY.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            errors.append(ActixErrorHandlerInfo(
                name=m.group('kind'), kind='error_factory',
                file=file_path, line_number=line_num,
            ))
        return errors

    def _extract_websockets(self, content: str, file_path: str) -> List[ActixWebSocketInfo]:
        websockets = []
        for m in self.WS_START.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            websockets.append(ActixWebSocketInfo(
                handler='ws_handler', file=file_path, line_number=line_num,
            ))
        return websockets

    def _extract_configs(self, content: str, file_path: str) -> List[ActixConfigInfo]:
        configs = []
        for m in self.SERVER_CONFIG.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            setting = m.group('setting') or 'bind'
            value = m.group('value') or m.group('addr') or ''
            configs.append(ActixConfigInfo(
                kind='server', setting=setting, value=value.strip(),
                file=file_path, line_number=line_num,
            ))

        for m in self.CORS_CONFIG.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            configs.append(ActixConfigInfo(
                kind='cors', setting=m.group('kind') if m.group('kind') else 'custom',
                file=file_path, line_number=line_num,
            ))

        for m in self.CONFIGURE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            configs.append(ActixConfigInfo(
                kind='app', setting='configure', value=m.group('fn'),
                file=file_path, line_number=line_num,
            ))

        return configs

    def _extract_tests(self, content: str, file_path: str) -> List[ActixTestInfo]:
        tests = []
        for m in self.TEST_UTIL.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            tests.append(ActixTestInfo(
                kind=m.group('kind'), file=file_path, line_number=line_num,
            ))
        return tests

    def _parse_extractor_params(self, params: str) -> List[str]:
        """Parse handler function params to find extractor types."""
        extractors = []
        for m in self.EXTRACTOR_PATTERN.finditer(params):
            extractors.append(f"{m.group('type')}<{m.group('inner').strip()}>")
        return extractors
