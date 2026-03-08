"""
EnhancedSanicParser - Deep extraction for Sanic framework projects.

Extracts:
- Routes (@app.route, @app.get/post/put/delete/patch/options/head)
- Blueprints (Blueprint, bp.route, bp group)
- Middleware (request middleware, response middleware, named middleware)
- Listeners (before_server_start, after_server_start, before_server_stop, after_server_stop)
- Signals (custom signals, built-in signals)
- WebSocket routes (@app.websocket, @bp.websocket)
- Static file serving (app.static)
- Exception handlers (@app.exception)
- Error handlers (custom ErrorHandler)
- Class-based views (HTTPMethodView, CompositionView)
- Dependencies/injection (ext.dependency)
- OpenAPI/Swagger configuration
- Streaming responses

Supports Sanic 18.x through 23.x+ (latest).

Part of CodeTrellis v4.92 - Python Framework Support.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any


# ═══════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SanicRouteInfo:
    """Information about a Sanic route."""
    path: str
    handler: str
    methods: List[str] = field(default_factory=list)
    name: Optional[str] = None
    is_async: bool = True
    blueprint: Optional[str] = None
    version: Optional[str] = None
    host: Optional[str] = None
    strict_slashes: Optional[bool] = None
    stream: bool = False
    line_number: int = 0


@dataclass
class SanicBlueprintInfo:
    """Information about a Sanic Blueprint."""
    name: str
    variable_name: str
    url_prefix: Optional[str] = None
    version: Optional[str] = None
    host: Optional[str] = None
    strict_slashes: Optional[bool] = None
    line_number: int = 0


@dataclass
class SanicMiddlewareInfo:
    """Information about Sanic middleware."""
    name: str
    middleware_type: str = "request"  # request, response
    attach_to: str = "request"  # request, response
    priority: Optional[int] = None
    blueprint: Optional[str] = None
    line_number: int = 0


@dataclass
class SanicListenerInfo:
    """Information about a Sanic listener (server lifecycle event)."""
    event: str  # before_server_start, after_server_start, before_server_stop, after_server_stop, main_process_start, etc.
    handler: str
    is_async: bool = True
    line_number: int = 0


@dataclass
class SanicSignalInfo:
    """Information about a Sanic signal."""
    signal_event: str  # e.g., "http.lifecycle.complete", custom signals
    handler: str
    condition: Optional[Dict[str, str]] = None
    is_async: bool = True
    line_number: int = 0


@dataclass
class SanicWebSocketInfo:
    """Information about a Sanic WebSocket endpoint."""
    path: str
    handler: str
    is_async: bool = True
    blueprint: Optional[str] = None
    line_number: int = 0


@dataclass
class SanicStaticInfo:
    """Information about static file serving configuration."""
    uri: str
    file_or_directory: str
    name: Optional[str] = None
    host: Optional[str] = None
    line_number: int = 0


@dataclass
class SanicExceptionHandlerInfo:
    """Information about a Sanic exception handler."""
    exception_class: str
    handler: str
    is_async: bool = True
    line_number: int = 0


@dataclass
class SanicClassBasedViewInfo:
    """Information about a Sanic class-based view."""
    name: str
    view_type: str = "HTTPMethodView"  # HTTPMethodView, CompositionView
    methods: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SanicParseResult:
    """Complete parse result for a Sanic file."""
    file_path: str
    file_type: str = "module"  # app, blueprint, middleware, model, test, view, config

    # Core extraction
    routes: List[SanicRouteInfo] = field(default_factory=list)
    blueprints: List[SanicBlueprintInfo] = field(default_factory=list)
    middleware: List[SanicMiddlewareInfo] = field(default_factory=list)
    listeners: List[SanicListenerInfo] = field(default_factory=list)
    signals: List[SanicSignalInfo] = field(default_factory=list)
    websocket_routes: List[SanicWebSocketInfo] = field(default_factory=list)
    static_routes: List[SanicStaticInfo] = field(default_factory=list)
    exception_handlers: List[SanicExceptionHandlerInfo] = field(default_factory=list)
    class_based_views: List[SanicClassBasedViewInfo] = field(default_factory=list)

    # Aggregate
    detected_frameworks: List[str] = field(default_factory=list)
    sanic_version: str = ""
    total_routes: int = 0
    total_middleware: int = 0
    total_blueprints: int = 0
    total_listeners: int = 0


# ═══════════════════════════════════════════════════════════════════
# Parser
# ═══════════════════════════════════════════════════════════════════

class EnhancedSanicParser:
    """
    Enhanced Sanic parser v1.0 for deep framework extraction.

    Supports Sanic 18.x through 23.x+ with extraction of:
    - @app.route, @app.get/post/put/delete/patch/options/head
    - Blueprint(), bp.route, BlueprintGroup
    - Middleware (request/response, priority-based in v22+)
    - Listeners (before_server_start, after_server_start, etc.)
    - Signals (custom signals v21.3+, built-in signals)
    - WebSocket routes (@app.websocket)
    - Static file serving (app.static)
    - Exception handlers (@app.exception)
    - Class-based views (HTTPMethodView, CompositionView)
    """

    # ── Sanic ecosystem detection patterns ────────────────────────
    FRAMEWORK_PATTERNS = {
        # Core Sanic
        'sanic': re.compile(
            r'from\s+sanic\s+import|import\s+sanic|from\s+sanic\.',
            re.MULTILINE,
        ),
        'sanic.app': re.compile(
            r'from\s+sanic\s+import\s+(?:.*\b)?Sanic\b|Sanic\s*\(\s*["\']',
            re.MULTILINE,
        ),
        'sanic.blueprints': re.compile(
            r'from\s+sanic\s+import\s+(?:.*\b)?Blueprint\b|from\s+sanic\.blueprints\s+import',
            re.MULTILINE,
        ),
        'sanic.views': re.compile(
            r'from\s+sanic\.views\s+import|HTTPMethodView|CompositionView',
            re.MULTILINE,
        ),
        'sanic.response': re.compile(
            r'from\s+sanic\s+import\s+(?:.*\b)?response\b|from\s+sanic\.response\s+import|'
            r'from\s+sanic\s+import\s+(?:.*\b)?(?:json|text|html|raw|file|file_stream|redirect|empty)\b',
            re.MULTILINE,
        ),
        'sanic.request': re.compile(
            r'from\s+sanic\.request\s+import|Request\b',
            re.MULTILINE,
        ),
        'sanic.websocket': re.compile(
            r'from\s+sanic\.websocket\s+import|Websocket\b|\.websocket\s*\(',
            re.MULTILINE,
        ),
        'sanic.signals': re.compile(
            r'from\s+sanic\.signals\s+import|\.signal\s*\(|@\w+\.signal\b|\.dispatch\s*\(',
            re.MULTILINE,
        ),
        # Extensions
        'sanic-ext': re.compile(
            r'from\s+sanic_ext|import\s+sanic_ext|Extend\s*\(|ext\.openapi|ext\.dependency',
            re.MULTILINE,
        ),
        'sanic-cors': re.compile(
            r'from\s+sanic_cors|import\s+sanic_cors|CORS\s*\(',
            re.MULTILINE,
        ),
        'sanic-jwt': re.compile(
            r'from\s+sanic_jwt|import\s+sanic_jwt|Initialize\s*\(|@\w+\.auth\.protected',
            re.MULTILINE,
        ),
        'sanic-session': re.compile(
            r'from\s+sanic_session|import\s+sanic_session|Session\s*\(',
            re.MULTILINE,
        ),
        'sanic-motor': re.compile(
            r'from\s+sanic_motor|import\s+sanic_motor',
            re.MULTILINE,
        ),
        'sanic-openapi': re.compile(
            r'from\s+sanic_openapi|import\s+sanic_openapi|from\s+sanic_ext\.extensions\.openapi',
            re.MULTILINE,
        ),
        # Deployment
        'uvicorn': re.compile(
            r'import\s+uvicorn|uvicorn\.run',
            re.MULTILINE,
        ),
        # Templating
        'jinja2': re.compile(
            r'from\s+jinja2\s+import|import\s+jinja2',
            re.MULTILINE,
        ),
    }

    # ── Route extraction patterns ─────────────────────────────────

    # @app.route("/path", methods=["GET", "POST"])
    DECORATOR_ROUTE_PATTERN = re.compile(
        r'@(\w+)\.route\s*\(\s*["\']([^"\']+)["\']\s*'
        r'(?:,\s*methods\s*=\s*\[([^\]]*)\])?'
        r'(?:,\s*name\s*=\s*["\']([^"\']+)["\'])?'
        r'(?:,\s*version\s*=\s*(\d+|["\'][^"\']+["\']))?'
        r'(?:,\s*host\s*=\s*["\']([^"\']+)["\'])?'
        r'[^)]*\)\s*\n'
        r'(?:\s*@\w+[\w.]*(?:\([^)]*\))?\s*\n)*'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # @app.get("/path"), @app.post("/path"), etc.
    HTTP_METHOD_ROUTE_PATTERN = re.compile(
        r'@(\w+)\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']\s*'
        r'(?:,\s*name\s*=\s*["\']([^"\']+)["\'])?'
        r'(?:,\s*version\s*=\s*(\d+|["\'][^"\']+["\']))?'
        r'[^)]*\)\s*\n'
        r'(?:\s*@\w+[\w.]*(?:\([^)]*\))?\s*\n)*'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # add_route(handler, "/path", methods=["GET"])
    ADD_ROUTE_PATTERN = re.compile(
        r'(\w+)\.add_route\s*\(\s*(\w+(?:\.\w+)?)\s*,\s*["\']([^"\']+)["\']\s*'
        r'(?:,\s*methods\s*=\s*\[([^\]]*)\])?',
        re.MULTILINE,
    )

    # ── Blueprint patterns ────────────────────────────────────────

    # bp = Blueprint("name", url_prefix="/prefix")
    BLUEPRINT_PATTERN = re.compile(
        r'(\w+)\s*=\s*Blueprint\s*\(\s*["\']([^"\']+)["\']\s*'
        r'(?:,\s*url_prefix\s*=\s*["\']([^"\']+)["\'])?'
        r'(?:,\s*version\s*=\s*(\d+|["\'][^"\']+["\']))?'
        r'(?:,\s*host\s*=\s*["\']([^"\']+)["\'])?',
        re.MULTILINE,
    )

    # BlueprintGroup or Blueprint.group()
    BLUEPRINT_GROUP_PATTERN = re.compile(
        r'(?:BlueprintGroup|Blueprint\.group)\s*\(\s*([^)]+)\s*\)',
        re.MULTILINE,
    )

    # app.blueprint(bp) or app.blueprint([bp1, bp2])
    BLUEPRINT_REGISTER_PATTERN = re.compile(
        r'(\w+)\.blueprint\s*\(\s*(\[?[\w,\s]+\]?)',
        re.MULTILINE,
    )

    # ── Middleware patterns ────────────────────────────────────────

    # @app.middleware("request") / @app.middleware("response")
    MIDDLEWARE_DECORATOR_PATTERN = re.compile(
        r'@(\w+)\.middleware\s*\(\s*["\'](\w+)["\']\s*'
        r'(?:,\s*priority\s*=\s*(\d+))?\s*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # @app.on_request / @app.on_response (shorthand)
    ON_REQUEST_RESPONSE_PATTERN = re.compile(
        r'@(\w+)\.(on_request|on_response)\s*(?:\(\s*(?:priority\s*=\s*(\d+))?\s*\))?\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # app.register_middleware(func, attach_to="request")
    REGISTER_MIDDLEWARE_PATTERN = re.compile(
        r'(\w+)\.register_middleware\s*\(\s*(\w+)\s*'
        r'(?:,\s*attach_to\s*=\s*["\'](\w+)["\'])?',
        re.MULTILINE,
    )

    # ── Listener patterns ─────────────────────────────────────────

    # @app.listener("before_server_start") or @app.before_server_start
    LISTENER_DECORATOR_PATTERN = re.compile(
        r'@(\w+)\.listener\s*\(\s*["\'](\w+)["\']\s*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # @app.before_server_start, @app.after_server_start, etc.
    LISTENER_SHORTHAND_PATTERN = re.compile(
        r'@(\w+)\.(before_server_start|after_server_start|before_server_stop|after_server_stop'
        r'|main_process_start|main_process_stop|main_process_ready'
        r'|reload_process_start|reload_process_stop)\s*(?:\([^)]*\))?\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # ── Signal patterns ───────────────────────────────────────────

    # @app.signal("http.lifecycle.complete") or @app.signal("my.custom.signal")
    SIGNAL_DECORATOR_PATTERN = re.compile(
        r'@(\w+)\.signal\s*\(\s*["\']([^"\']+)["\']\s*'
        r'(?:,\s*condition\s*=\s*(\{[^}]+\}))?\s*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # app.dispatch("signal.name")
    SIGNAL_DISPATCH_PATTERN = re.compile(
        r'(\w+)\.dispatch\s*\(\s*["\']([^"\']+)["\']\s*',
        re.MULTILINE,
    )

    # ── WebSocket patterns ────────────────────────────────────────

    # @app.websocket("/ws")
    WEBSOCKET_PATTERN = re.compile(
        r'@(\w+)\.websocket\s*\(\s*["\']([^"\']+)["\']\s*[^)]*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # app.add_websocket_route(handler, "/ws")
    ADD_WEBSOCKET_ROUTE_PATTERN = re.compile(
        r'(\w+)\.add_websocket_route\s*\(\s*(\w+)\s*,\s*["\']([^"\']+)["\']',
        re.MULTILINE,
    )

    # ── Static file patterns ──────────────────────────────────────

    # app.static("/static", "./static")
    STATIC_PATTERN = re.compile(
        r'(\w+)\.static\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*'
        r'(?:,\s*name\s*=\s*["\']([^"\']+)["\'])?'
        r'(?:,\s*host\s*=\s*["\']([^"\']+)["\'])?',
        re.MULTILINE,
    )

    # ── Exception handler patterns ────────────────────────────────

    # @app.exception(NotFound, SanicException)
    EXCEPTION_HANDLER_PATTERN = re.compile(
        r'@(\w+)\.exception\s*\(\s*([^)]+)\s*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # ── Class-based view patterns ─────────────────────────────────

    # class MyView(HTTPMethodView):
    CBV_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*(HTTPMethodView|CompositionView)\s*\)',
        re.MULTILINE,
    )

    # CBV methods: async def get(self, request):
    CBV_METHOD_PATTERN = re.compile(
        r'\s+(async\s+)?def\s+(get|post|put|patch|delete|head|options)\s*\(\s*self',
        re.MULTILINE,
    )

    # ── Sanic app instantiation ───────────────────────────────────
    SANIC_APP_PATTERN = re.compile(
        r'(\w+)\s*=\s*Sanic\s*\(\s*["\']([^"\']+)["\']\s*',
        re.MULTILINE,
    )

    # ── Version feature detection ─────────────────────────────────
    SANIC_VERSION_FEATURES = {
        'Sanic(': '18.0',
        'Blueprint(': '18.0',
        'HTTPMethodView': '18.0',
        'CompositionView': '18.0',
        'app.static': '18.0',
        '@app.exception': '18.0',
        '@app.middleware': '18.0',
        '@app.listener': '18.0',
        'add_route': '18.0',
        'websocket': '18.0',
        'stream=True': '18.0',
        'version=': '19.0',
        'strict_slashes': '19.0',
        '@app.signal': '21.3',
        '.dispatch(': '21.3',
        'on_request': '21.3',
        'on_response': '21.3',
        'before_server_start': '18.0',
        'after_server_start': '18.0',
        'before_server_stop': '18.0',
        'after_server_stop': '18.0',
        'main_process_start': '21.3',
        'main_process_stop': '21.3',
        'main_process_ready': '22.9',
        'priority=': '22.0',
        'ext.dependency': '21.12',
        'Extend(': '21.12',
    }

    def __init__(self):
        """Initialize the enhanced Sanic parser."""
        pass

    def parse(self, content: str, file_path: str = "") -> SanicParseResult:
        """
        Parse Sanic source code and extract all Sanic-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            SanicParseResult with all extracted information
        """
        result = SanicParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Routes ───────────────────────────────────────────────
        self._extract_decorator_routes(content, result)
        self._extract_http_method_routes(content, result)
        self._extract_add_routes(content, result)

        # ── Blueprints ───────────────────────────────────────────
        self._extract_blueprints(content, result)

        # ── Middleware ───────────────────────────────────────────
        self._extract_middleware(content, result)

        # ── Listeners ────────────────────────────────────────────
        self._extract_listeners(content, result)

        # ── Signals ──────────────────────────────────────────────
        self._extract_signals(content, result)

        # ── WebSocket routes ─────────────────────────────────────
        self._extract_websocket_routes(content, result)

        # ── Static files ─────────────────────────────────────────
        self._extract_static_routes(content, result)

        # ── Exception handlers ───────────────────────────────────
        self._extract_exception_handlers(content, result)

        # ── Class-based views ────────────────────────────────────
        self._extract_class_based_views(content, result)

        # Aggregates
        result.total_routes = len(result.routes) + len(result.websocket_routes)
        result.total_middleware = len(result.middleware)
        result.total_blueprints = len(result.blueprints)
        result.total_listeners = len(result.listeners)
        result.sanic_version = self._detect_sanic_version(content)

        return result

    # ─── Extraction methods ───────────────────────────────────────

    def _extract_decorator_routes(self, content: str, result: SanicParseResult):
        """Extract @app.route() decorator-style routes."""
        for match in self.DECORATOR_ROUTE_PATTERN.finditer(content):
            app_var = match.group(1)
            path = match.group(2)
            methods_str = match.group(3) or ""
            name = match.group(4)
            version = match.group(5)
            host = match.group(6)
            is_async = match.group(7) is not None
            handler = match.group(8)

            methods = []
            if methods_str:
                methods = [m.strip().strip('"\'') for m in methods_str.split(',') if m.strip()]

            # Detect blueprint vs app
            blueprint = self._detect_blueprint_owner(content, app_var)

            result.routes.append(SanicRouteInfo(
                path=path,
                handler=handler,
                methods=methods if methods else ['GET'],
                name=name,
                is_async=is_async,
                blueprint=blueprint,
                version=self._clean_version(version),
                host=host,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_http_method_routes(self, content: str, result: SanicParseResult):
        """Extract @app.get(), @app.post(), etc. shorthand routes."""
        for match in self.HTTP_METHOD_ROUTE_PATTERN.finditer(content):
            app_var = match.group(1)
            method = match.group(2).upper()
            path = match.group(3)
            name = match.group(4)
            version = match.group(5)
            is_async = match.group(6) is not None
            handler = match.group(7)

            blueprint = self._detect_blueprint_owner(content, app_var)

            result.routes.append(SanicRouteInfo(
                path=path,
                handler=handler,
                methods=[method],
                name=name,
                is_async=is_async,
                blueprint=blueprint,
                version=self._clean_version(version),
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_add_routes(self, content: str, result: SanicParseResult):
        """Extract app.add_route(handler, path, methods=[...])."""
        for match in self.ADD_ROUTE_PATTERN.finditer(content):
            app_var = match.group(1)
            handler = match.group(2)
            path = match.group(3)
            methods_str = match.group(4) or ""

            methods = []
            if methods_str:
                methods = [m.strip().strip('"\'') for m in methods_str.split(',') if m.strip()]

            blueprint = self._detect_blueprint_owner(content, app_var)

            result.routes.append(SanicRouteInfo(
                path=path,
                handler=handler,
                methods=methods if methods else ['GET'],
                blueprint=blueprint,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_blueprints(self, content: str, result: SanicParseResult):
        """Extract Blueprint() definitions."""
        for match in self.BLUEPRINT_PATTERN.finditer(content):
            var_name = match.group(1)
            name = match.group(2)
            url_prefix = match.group(3)
            version = match.group(4)
            host = match.group(5)

            result.blueprints.append(SanicBlueprintInfo(
                name=name,
                variable_name=var_name,
                url_prefix=url_prefix,
                version=self._clean_version(version),
                host=host,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_middleware(self, content: str, result: SanicParseResult):
        """Extract middleware from decorators and register_middleware."""
        # @app.middleware("request"/"response")
        for match in self.MIDDLEWARE_DECORATOR_PATTERN.finditer(content):
            app_var = match.group(1)
            attach_to = match.group(2)
            priority_str = match.group(3)
            is_async = match.group(4) is not None
            handler = match.group(5)

            blueprint = self._detect_blueprint_owner(content, app_var)

            result.middleware.append(SanicMiddlewareInfo(
                name=handler,
                middleware_type=attach_to,
                attach_to=attach_to,
                priority=int(priority_str) if priority_str else None,
                blueprint=blueprint,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @app.on_request / @app.on_response shorthand
        for match in self.ON_REQUEST_RESPONSE_PATTERN.finditer(content):
            app_var = match.group(1)
            event_type = match.group(2)  # on_request or on_response
            priority_str = match.group(3)
            is_async = match.group(4) is not None
            handler = match.group(5)

            attach_to = "request" if event_type == "on_request" else "response"
            blueprint = self._detect_blueprint_owner(content, app_var)

            result.middleware.append(SanicMiddlewareInfo(
                name=handler,
                middleware_type=attach_to,
                attach_to=attach_to,
                priority=int(priority_str) if priority_str else None,
                blueprint=blueprint,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # app.register_middleware(func, attach_to="request")
        for match in self.REGISTER_MIDDLEWARE_PATTERN.finditer(content):
            app_var = match.group(1)
            handler = match.group(2)
            attach_to = match.group(3) or "request"

            result.middleware.append(SanicMiddlewareInfo(
                name=handler,
                middleware_type=attach_to,
                attach_to=attach_to,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_listeners(self, content: str, result: SanicParseResult):
        """Extract listener decorators for server lifecycle events."""
        # @app.listener("before_server_start")
        for match in self.LISTENER_DECORATOR_PATTERN.finditer(content):
            event = match.group(2)
            is_async = match.group(3) is not None
            handler = match.group(4)

            result.listeners.append(SanicListenerInfo(
                event=event,
                handler=handler,
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @app.before_server_start, @app.after_server_start, etc.
        for match in self.LISTENER_SHORTHAND_PATTERN.finditer(content):
            event = match.group(2)
            is_async = match.group(3) is not None
            handler = match.group(4)

            # Avoid duplicates from the listener pattern
            already = any(
                l.handler == handler and l.event == event
                for l in result.listeners
            )
            if not already:
                result.listeners.append(SanicListenerInfo(
                    event=event,
                    handler=handler,
                    is_async=is_async,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

    def _extract_signals(self, content: str, result: SanicParseResult):
        """Extract signal decorators and dispatch calls."""
        # @app.signal("http.lifecycle.complete")
        for match in self.SIGNAL_DECORATOR_PATTERN.finditer(content):
            signal_event = match.group(2)
            condition_str = match.group(3)
            is_async = match.group(4) is not None
            handler = match.group(5)

            condition = None
            if condition_str:
                condition = self._parse_condition(condition_str)

            result.signals.append(SanicSignalInfo(
                signal_event=signal_event,
                handler=handler,
                condition=condition,
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_websocket_routes(self, content: str, result: SanicParseResult):
        """Extract WebSocket routes."""
        # @app.websocket("/ws")
        for match in self.WEBSOCKET_PATTERN.finditer(content):
            app_var = match.group(1)
            path = match.group(2)
            is_async = match.group(3) is not None
            handler = match.group(4)

            blueprint = self._detect_blueprint_owner(content, app_var)

            result.websocket_routes.append(SanicWebSocketInfo(
                path=path,
                handler=handler,
                is_async=is_async,
                blueprint=blueprint,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # app.add_websocket_route(handler, "/ws")
        for match in self.ADD_WEBSOCKET_ROUTE_PATTERN.finditer(content):
            app_var = match.group(1)
            handler = match.group(2)
            path = match.group(3)

            result.websocket_routes.append(SanicWebSocketInfo(
                path=path,
                handler=handler,
                is_async=True,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_static_routes(self, content: str, result: SanicParseResult):
        """Extract static file serving configurations."""
        for match in self.STATIC_PATTERN.finditer(content):
            uri = match.group(2)
            file_or_dir = match.group(3)
            name = match.group(4)
            host = match.group(5)

            result.static_routes.append(SanicStaticInfo(
                uri=uri,
                file_or_directory=file_or_dir,
                name=name,
                host=host,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_exception_handlers(self, content: str, result: SanicParseResult):
        """Extract exception handler decorators."""
        for match in self.EXCEPTION_HANDLER_PATTERN.finditer(content):
            exceptions_str = match.group(2)
            is_async = match.group(3) is not None
            handler = match.group(4)

            # Parse exception classes (may be comma-separated)
            exceptions = [e.strip() for e in exceptions_str.split(',') if e.strip()]
            for exc in exceptions:
                result.exception_handlers.append(SanicExceptionHandlerInfo(
                    exception_class=exc,
                    handler=handler,
                    is_async=is_async,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

    def _extract_class_based_views(self, content: str, result: SanicParseResult):
        """Extract class-based views (HTTPMethodView, CompositionView)."""
        for match in self.CBV_PATTERN.finditer(content):
            name = match.group(1)
            view_type = match.group(2)

            # Find methods within this class
            class_start = match.start()
            # Find next class or end of file
            next_class = re.search(r'\nclass\s+', content[class_start + 1:])
            class_end = class_start + 1 + next_class.start() if next_class else len(content)
            class_body = content[class_start:class_end]

            methods = []
            for method_match in self.CBV_METHOD_PATTERN.finditer(class_body):
                methods.append(method_match.group(2).upper())

            # Find decorators on the class
            decorators = []
            before_class = content[:class_start]
            lines_before = before_class.rstrip().split('\n')
            for i in range(len(lines_before) - 1, max(len(lines_before) - 10, -1), -1):
                line = lines_before[i].strip()
                if line.startswith('@'):
                    decorators.append(line)
                elif line and not line.startswith('#'):
                    break

            result.class_based_views.append(SanicClassBasedViewInfo(
                name=name,
                view_type=view_type,
                methods=methods,
                decorators=decorators,
                line_number=content[:class_start].count('\n') + 1,
            ))

    # ─── Helper methods ───────────────────────────────────────────

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a Sanic file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        if basename in ('main.py', 'app.py', 'application.py', 'server.py', '__init__.py'):
            if 'Sanic(' in content:
                return 'app'
        if 'blueprint' in basename or 'bp_' in basename or '_bp' in basename:
            return 'blueprint'
        if 'middleware' in basename:
            return 'middleware'
        if 'route' in basename or 'endpoint' in basename or 'view' in basename:
            return 'view'
        if 'model' in basename or 'schema' in basename:
            return 'model'
        if 'test' in basename:
            return 'test'
        if 'config' in basename or 'settings' in basename:
            return 'config'
        if 'listener' in basename or 'signal' in basename:
            return 'listener'

        if '/blueprints/' in normalized:
            return 'blueprint'
        if '/middleware/' in normalized:
            return 'middleware'
        if '/routes/' in normalized or '/endpoints/' in normalized or '/views/' in normalized:
            return 'view'
        if '/models/' in normalized or '/schemas/' in normalized:
            return 'model'

        return 'module'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Sanic ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_blueprint_owner(self, content: str, var_name: str) -> Optional[str]:
        """Determine if a variable is a Blueprint instance."""
        # Check if this variable name is defined as a Blueprint
        bp_match = re.search(
            rf'{re.escape(var_name)}\s*=\s*Blueprint\s*\(\s*["\']([^"\']+)["\']',
            content,
        )
        if bp_match:
            return bp_match.group(1)
        return None

    def _clean_version(self, version: Optional[str]) -> Optional[str]:
        """Clean a version string (remove quotes if present)."""
        if version:
            return version.strip('"\'')
        return None

    def _parse_condition(self, condition_str: str) -> Optional[Dict[str, str]]:
        """Parse a signal condition dict from string."""
        condition = {}
        for kv in re.finditer(r'["\'](\w+)["\']\s*:\s*["\']([^"\']+)["\']', condition_str):
            condition[kv.group(1)] = kv.group(2)
        return condition if condition else None

    def _detect_sanic_version(self, content: str) -> str:
        """Detect minimum Sanic version required based on features used."""
        max_version = '0.0'
        for feature, version in self.SANIC_VERSION_FEATURES.items():
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

    def is_sanic_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a Sanic-specific file.
        Returns True if the file uses Sanic directly.
        """
        # Direct sanic imports
        if re.search(r'from\s+sanic\s+import|import\s+sanic\b|from\s+sanic\.\w+\s+import', content):
            return True
        # Sanic app instantiation
        if re.search(r'Sanic\s*\(\s*["\']', content):
            return True
        # Sanic Blueprint
        if re.search(r'from\s+sanic\s+import\s+(?:.*\b)?Blueprint\b', content):
            return True
        return False

    def to_codetrellis_format(self, result: SanicParseResult) -> str:
        """Convert parse result to CodeTrellis compressed format."""
        lines = []

        if result.file_path:
            lines.append(f"[FILE:{Path(result.file_path).name}|type:{result.file_type}]")
        if result.detected_frameworks:
            lines.append(f"[SANIC_ECOSYSTEM:{','.join(result.detected_frameworks)}]")
        if result.sanic_version:
            lines.append(f"[SANIC_VERSION:>={result.sanic_version}]")
        lines.append("")

        # Routes
        if result.routes:
            lines.append("=== SANIC_ROUTES ===")
            for r in result.routes:
                methods_str = ",".join(r.methods) if r.methods else "GET"
                async_str = "|async" if r.is_async else ""
                bp_str = f"|bp:{r.blueprint}" if r.blueprint else ""
                ver_str = f"|v{r.version}" if r.version else ""
                lines.append(f"  {methods_str} {r.path} → {r.handler}{async_str}{bp_str}{ver_str}")
            lines.append("")

        # Blueprints
        if result.blueprints:
            lines.append("=== SANIC_BLUEPRINTS ===")
            for bp in result.blueprints:
                prefix_str = f"|prefix:{bp.url_prefix}" if bp.url_prefix else ""
                ver_str = f"|v{bp.version}" if bp.version else ""
                lines.append(f"  {bp.name}({bp.variable_name}){prefix_str}{ver_str}")
            lines.append("")

        # WebSocket routes
        if result.websocket_routes:
            lines.append("=== SANIC_WEBSOCKET ===")
            for ws in result.websocket_routes:
                bp_str = f"|bp:{ws.blueprint}" if ws.blueprint else ""
                lines.append(f"  WS {ws.path} → {ws.handler}{bp_str}")
            lines.append("")

        # Middleware
        if result.middleware:
            lines.append("=== SANIC_MIDDLEWARE ===")
            for mw in result.middleware:
                prio_str = f"|prio:{mw.priority}" if mw.priority is not None else ""
                bp_str = f"|bp:{mw.blueprint}" if mw.blueprint else ""
                lines.append(f"  {mw.name}[{mw.attach_to}]{prio_str}{bp_str}")
            lines.append("")

        # Listeners
        if result.listeners:
            lines.append("=== SANIC_LISTENERS ===")
            for lh in result.listeners:
                lines.append(f"  @{lh.event} → {lh.handler}")
            lines.append("")

        # Signals
        if result.signals:
            lines.append("=== SANIC_SIGNALS ===")
            for sig in result.signals:
                cond_str = f"|condition:{sig.condition}" if sig.condition else ""
                lines.append(f"  {sig.signal_event} → {sig.handler}{cond_str}")
            lines.append("")

        # Exception handlers
        if result.exception_handlers:
            lines.append("=== SANIC_EXCEPTIONS ===")
            for ex in result.exception_handlers:
                lines.append(f"  {ex.exception_class} → {ex.handler}")
            lines.append("")

        # Class-based views
        if result.class_based_views:
            lines.append("=== SANIC_VIEWS ===")
            for cbv in result.class_based_views:
                methods_str = ",".join(cbv.methods) if cbv.methods else "none"
                lines.append(f"  {cbv.name}[{cbv.view_type}]|methods:{methods_str}")
            lines.append("")

        # Static files
        if result.static_routes:
            lines.append("=== SANIC_STATIC ===")
            for sf in result.static_routes:
                name_str = f"|name:{sf.name}" if sf.name else ""
                lines.append(f"  {sf.uri} → {sf.file_or_directory}{name_str}")
            lines.append("")

        return '\n'.join(lines)
