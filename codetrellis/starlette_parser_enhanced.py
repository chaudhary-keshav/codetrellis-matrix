"""
EnhancedStarletteParser - Deep extraction for Starlette framework projects.

Extracts:
- Routes (path-based, method-based, Mount sub-apps)
- Middleware (ASGI middleware, BaseHTTPMiddleware, built-in)
- WebSocket endpoints
- Lifespan handlers (on_startup, on_shutdown, lifespan context)
- Static file mounts
- Authentication & permissions (AuthenticationBackend, requires decorator)
- Exception handlers
- Test client usage
- Template/Jinja2 configuration
- Session/cookie configuration
- GraphQL mounts (if Ariadne/Strawberry detected)

Supports Starlette 0.12.x through 0.40.x+ (latest).

Part of CodeTrellis v4.33 - Python Framework Support.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any


# ═══════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════

@dataclass
class StarletteRouteInfo:
    """Information about a Starlette route."""
    path: str
    endpoint: str
    methods: List[str] = field(default_factory=list)
    name: Optional[str] = None
    is_async: bool = False
    line_number: int = 0


@dataclass
class StarletteMountInfo:
    """Information about a Starlette Mount (sub-application)."""
    path: str
    app_name: str
    mount_type: str = "app"  # app, static, graphql
    line_number: int = 0


@dataclass
class StarletteMiddlewareInfo:
    """Information about Starlette middleware."""
    name: str
    middleware_type: str = "custom"  # cors, trustedhost, gzip, httpsredirect, sessions, authentication, custom
    kwargs: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0


@dataclass
class StarletteWebSocketInfo:
    """Information about a Starlette WebSocket endpoint."""
    path: str
    endpoint: str
    is_async: bool = True
    line_number: int = 0


@dataclass
class StarletteLifespanInfo:
    """Information about a Starlette lifespan/event handler."""
    event: str  # startup, shutdown, lifespan
    handler: str
    is_async: bool = True
    line_number: int = 0


@dataclass
class StarletteExceptionHandlerInfo:
    """Information about a Starlette exception handler."""
    exception_class: str
    handler: str
    line_number: int = 0


@dataclass
class StarletteAuthBackendInfo:
    """Information about a Starlette AuthenticationBackend."""
    name: str
    file: str = ""
    line_number: int = 0


@dataclass
class StarletteStaticFilesInfo:
    """Information about static file serving configuration."""
    path: str
    directory: str
    html: bool = False
    line_number: int = 0


@dataclass
class StarletteParseResult:
    """Complete parse result for a Starlette file."""
    file_path: str
    file_type: str = "module"  # app, router, middleware, model, test

    # Core extraction
    routes: List[StarletteRouteInfo] = field(default_factory=list)
    mounts: List[StarletteMountInfo] = field(default_factory=list)
    middleware: List[StarletteMiddlewareInfo] = field(default_factory=list)
    websocket_routes: List[StarletteWebSocketInfo] = field(default_factory=list)
    lifespan_handlers: List[StarletteLifespanInfo] = field(default_factory=list)
    exception_handlers: List[StarletteExceptionHandlerInfo] = field(default_factory=list)
    auth_backends: List[StarletteAuthBackendInfo] = field(default_factory=list)
    static_files: List[StarletteStaticFilesInfo] = field(default_factory=list)

    # Aggregate
    detected_frameworks: List[str] = field(default_factory=list)
    starlette_version: str = ""
    total_routes: int = 0
    total_middleware: int = 0


# ═══════════════════════════════════════════════════════════════════
# Parser
# ═══════════════════════════════════════════════════════════════════

class EnhancedStarletteParser:
    """
    Enhanced Starlette parser v1.0 for deep framework extraction.

    Supports Starlette 0.12.x through 0.40.x+ with extraction of:
    - Route(), Mount(), WebSocketRoute()
    - Middleware stack (add_middleware, Middleware())
    - Lifespan protocol (on_startup/on_shutdown/lifespan context manager)
    - AuthenticationBackend and @requires decorator
    - StaticFiles, Jinja2Templates
    - Exception handlers
    """

    # ── Starlette ecosystem detection patterns ────────────────────
    FRAMEWORK_PATTERNS = {
        # Core Starlette
        'starlette': re.compile(
            r'from\s+starlette\s+import|import\s+starlette|from\s+starlette\.',
            re.MULTILINE,
        ),
        'starlette.applications': re.compile(
            r'from\s+starlette\.applications\s+import|Starlette\s*\(',
            re.MULTILINE,
        ),
        'starlette.routing': re.compile(
            r'from\s+starlette\.routing\s+import|Route\s*\(|Mount\s*\(|WebSocketRoute\s*\(',
            re.MULTILINE,
        ),
        'starlette.middleware': re.compile(
            r'from\s+starlette\.middleware|Middleware\s*\(',
            re.MULTILINE,
        ),
        'starlette.authentication': re.compile(
            r'from\s+starlette\.authentication|AuthenticationBackend|AuthCredentials|@requires',
            re.MULTILINE,
        ),
        'starlette.staticfiles': re.compile(
            r'from\s+starlette\.staticfiles|StaticFiles\s*\(',
            re.MULTILINE,
        ),
        'starlette.templating': re.compile(
            r'from\s+starlette\.templating|Jinja2Templates\s*\(',
            re.MULTILINE,
        ),
        'starlette.testclient': re.compile(
            r'from\s+starlette\.testclient|TestClient\s*\(',
            re.MULTILINE,
        ),
        'starlette.websockets': re.compile(
            r'from\s+starlette\.websockets|WebSocket\b',
            re.MULTILINE,
        ),
        'starlette.responses': re.compile(
            r'from\s+starlette\.responses|JSONResponse|HTMLResponse|PlainTextResponse|StreamingResponse|RedirectResponse|FileResponse',
            re.MULTILINE,
        ),
        'starlette.requests': re.compile(
            r'from\s+starlette\.requests\s+import|Request\b',
            re.MULTILINE,
        ),
        # Sessions
        'starlette.sessions': re.compile(
            r'from\s+starlette\.middleware\.sessions|SessionMiddleware',
            re.MULTILINE,
        ),
        # CORS
        'starlette.cors': re.compile(
            r'from\s+starlette\.middleware\.cors|CORSMiddleware',
            re.MULTILINE,
        ),
        # Database integration (encode/databases)
        'databases': re.compile(
            r'from\s+databases\s+import|import\s+databases',
            re.MULTILINE,
        ),
        # GraphQL
        'graphql': re.compile(
            r'from\s+ariadne\.asgi|from\s+strawberry\.asgi|GraphQL\s*\(',
            re.MULTILINE,
        ),
        # Deployment
        'uvicorn': re.compile(
            r'import\s+uvicorn|uvicorn\.run',
            re.MULTILINE,
        ),
        'gunicorn': re.compile(
            r'import\s+gunicorn|gunicorn',
            re.MULTILINE,
        ),
    }

    # ── Route extraction patterns ─────────────────────────────────
    # Route("path", endpoint=handler) or Route("path", handler)
    ROUTE_PATTERN = re.compile(
        r'Route\s*\(\s*["\']([^"\']+)["\']\s*,\s*'
        r'(?:endpoint\s*=\s*)?(\w+)'
        r'(?:\s*,\s*methods\s*=\s*\[([^\]]*)\])?'
        r'(?:\s*,\s*name\s*=\s*["\']([^"\']+)["\'])?',
        re.MULTILINE,
    )

    # Mount("path", app=SomeApp) or Mount("path", routes=[...])
    MOUNT_PATTERN = re.compile(
        r'Mount\s*\(\s*["\']([^"\']+)["\']\s*,\s*'
        r'(?:app\s*=\s*)?(\w[\w.]*(?:\([^)]*\))?)',
        re.MULTILINE,
    )

    # WebSocketRoute("path", endpoint=handler)
    WEBSOCKET_ROUTE_PATTERN = re.compile(
        r'WebSocketRoute\s*\(\s*["\']([^"\']+)["\']\s*,\s*'
        r'(?:endpoint\s*=\s*)?(\w+)',
        re.MULTILINE,
    )

    # ── Middleware patterns ────────────────────────────────────────
    # app.add_middleware(CORSMiddleware, ...)
    ADD_MIDDLEWARE_PATTERN = re.compile(
        r'(\w+)\.add_middleware\s*\(\s*(\w+)(?:\s*,\s*([^)]+))?\s*\)',
        re.MULTILINE,
    )

    # Middleware(CORSMiddleware, ...) in middleware stack
    MIDDLEWARE_STACK_PATTERN = re.compile(
        r'Middleware\s*\(\s*(\w+)(?:\s*,\s*([^)]+))?\s*\)',
        re.MULTILINE,
    )

    # ── Lifespan/Event patterns ───────────────────────────────────
    # on_startup=[func1, func2]
    ON_EVENT_LIST_PATTERN = re.compile(
        r'on_(startup|shutdown)\s*=\s*\[([^\]]*)\]',
        re.MULTILINE,
    )

    # @app.on_event("startup")
    ON_EVENT_DECORATOR_PATTERN = re.compile(
        r'@(\w+)\.on_event\s*\(\s*["\'](\w+)["\']\s*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # lifespan context manager
    LIFESPAN_PATTERN = re.compile(
        r'@asynccontextmanager\s*\n\s*async\s+def\s+(\w+)\s*\(\s*(?:app|_)',
        re.MULTILINE,
    )

    # ── Exception handler patterns ────────────────────────────────
    EXCEPTION_HANDLER_DICT_PATTERN = re.compile(
        r'(\d+|Exception|\w+Error|\w+Exception)\s*:\s*(\w+)',
        re.MULTILINE,
    )

    # ── Auth patterns ─────────────────────────────────────────────
    AUTH_BACKEND_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*AuthenticationBackend\s*\)',
        re.MULTILINE,
    )

    REQUIRES_PATTERN = re.compile(
        r'@requires\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE,
    )

    # ── Static files pattern ──────────────────────────────────────
    STATIC_FILES_PATTERN = re.compile(
        r'StaticFiles\s*\(\s*directory\s*=\s*["\']([^"\']+)["\']'
        r'(?:\s*,\s*html\s*=\s*(True|False))?',
        re.MULTILINE,
    )

    # ── Starlette app instantiation ───────────────────────────────
    STARLETTE_APP_PATTERN = re.compile(
        r'(\w+)\s*=\s*Starlette\s*\(',
        re.MULTILINE,
    )

    # ── Endpoint decorator @app.route ─────────────────────────────
    DECORATOR_ROUTE_PATTERN = re.compile(
        r'@(\w+)\.route\s*\(\s*["\']([^"\']+)["\']\s*'
        r'(?:,\s*methods\s*=\s*\[([^\]]*)\])?\s*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # ── Endpoint decorator @app.websocket_route ───────────────────
    DECORATOR_WS_ROUTE_PATTERN = re.compile(
        r'@(\w+)\.websocket_route\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # ── Version feature detection ─────────────────────────────────
    STARLETTE_VERSION_FEATURES = {
        'lifespan': '0.20',
        'Route': '0.12',
        'Mount': '0.12',
        'WebSocketRoute': '0.12',
        'Middleware': '0.14',
        'AuthenticationBackend': '0.14',
        '@requires': '0.14',
        'SessionMiddleware': '0.14',
        'StaticFiles': '0.12',
        'Jinja2Templates': '0.12',
        'TestClient': '0.12',
        'StreamingResponse': '0.12',
        'FileResponse': '0.13',
        '@asynccontextmanager': '0.20',
        'on_startup': '0.12',
        'on_shutdown': '0.12',
    }

    def __init__(self):
        """Initialize the enhanced Starlette parser."""
        pass

    def parse(self, content: str, file_path: str = "") -> StarletteParseResult:
        """
        Parse Starlette source code and extract all Starlette-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            StarletteParseResult with all extracted information
        """
        result = StarletteParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Routes ───────────────────────────────────────────────
        self._extract_routes(content, result)
        self._extract_decorator_routes(content, result)

        # ── Mounts ───────────────────────────────────────────────
        self._extract_mounts(content, result)

        # ── WebSocket routes ─────────────────────────────────────
        self._extract_websocket_routes(content, result)
        self._extract_decorator_ws_routes(content, result)

        # ── Middleware ───────────────────────────────────────────
        self._extract_middleware(content, result)

        # ── Lifespan / Events ────────────────────────────────────
        self._extract_lifespan(content, result)

        # ── Exception handlers ───────────────────────────────────
        self._extract_exception_handlers(content, result)

        # ── Auth backends ────────────────────────────────────────
        self._extract_auth_backends(content, result)

        # ── Static files ─────────────────────────────────────────
        self._extract_static_files(content, result)

        # Aggregates
        result.total_routes = len(result.routes) + len(result.websocket_routes)
        result.total_middleware = len(result.middleware)
        result.starlette_version = self._detect_starlette_version(content)

        return result

    # ─── Extraction methods ───────────────────────────────────────

    def _extract_routes(self, content: str, result: StarletteParseResult):
        """Extract Route() definitions."""
        for match in self.ROUTE_PATTERN.finditer(content):
            path = match.group(1)
            endpoint = match.group(2)
            methods_str = match.group(3) or ""
            name = match.group(4)

            methods = []
            if methods_str:
                methods = [m.strip().strip('"\'') for m in methods_str.split(',') if m.strip()]

            # Check if endpoint is async
            is_async = self._is_async_function(content, endpoint)

            result.routes.append(StarletteRouteInfo(
                path=path,
                endpoint=endpoint,
                methods=methods if methods else ['GET'],
                name=name,
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_decorator_routes(self, content: str, result: StarletteParseResult):
        """Extract @app.route() decorator-style routes."""
        for match in self.DECORATOR_ROUTE_PATTERN.finditer(content):
            path = match.group(2)
            methods_str = match.group(3) or ""
            is_async = match.group(4) is not None
            endpoint = match.group(5)

            methods = []
            if methods_str:
                methods = [m.strip().strip('"\'') for m in methods_str.split(',') if m.strip()]

            result.routes.append(StarletteRouteInfo(
                path=path,
                endpoint=endpoint,
                methods=methods if methods else ['GET'],
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_mounts(self, content: str, result: StarletteParseResult):
        """Extract Mount() definitions."""
        for match in self.MOUNT_PATTERN.finditer(content):
            path = match.group(1)
            app_name = match.group(2)

            # Determine mount type
            mount_type = "app"
            if 'StaticFiles' in app_name:
                mount_type = "static"
            elif 'GraphQL' in app_name:
                mount_type = "graphql"

            result.mounts.append(StarletteMountInfo(
                path=path,
                app_name=app_name,
                mount_type=mount_type,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_websocket_routes(self, content: str, result: StarletteParseResult):
        """Extract WebSocketRoute() definitions."""
        for match in self.WEBSOCKET_ROUTE_PATTERN.finditer(content):
            path = match.group(1)
            endpoint = match.group(2)

            result.websocket_routes.append(StarletteWebSocketInfo(
                path=path,
                endpoint=endpoint,
                is_async=self._is_async_function(content, endpoint),
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_decorator_ws_routes(self, content: str, result: StarletteParseResult):
        """Extract @app.websocket_route() decorator-style WS routes."""
        for match in self.DECORATOR_WS_ROUTE_PATTERN.finditer(content):
            path = match.group(2)
            is_async = match.group(3) is not None
            endpoint = match.group(4)

            result.websocket_routes.append(StarletteWebSocketInfo(
                path=path,
                endpoint=endpoint,
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_middleware(self, content: str, result: StarletteParseResult):
        """Extract middleware from add_middleware() and Middleware() stack."""
        # add_middleware pattern
        for match in self.ADD_MIDDLEWARE_PATTERN.finditer(content):
            mw_class = match.group(2)
            kwargs_str = match.group(3) or ""
            kwargs = self._parse_kwargs(kwargs_str)
            mw_type = self._classify_middleware(mw_class)

            result.middleware.append(StarletteMiddlewareInfo(
                name=mw_class,
                middleware_type=mw_type,
                kwargs=kwargs,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Middleware() stack pattern
        for match in self.MIDDLEWARE_STACK_PATTERN.finditer(content):
            mw_class = match.group(1)
            kwargs_str = match.group(2) or ""
            kwargs = self._parse_kwargs(kwargs_str)
            mw_type = self._classify_middleware(mw_class)

            # Avoid duplicate if already captured via add_middleware
            already = any(m.name == mw_class and m.line_number == content[:match.start()].count('\n') + 1
                         for m in result.middleware)
            if not already:
                result.middleware.append(StarletteMiddlewareInfo(
                    name=mw_class,
                    middleware_type=mw_type,
                    kwargs=kwargs,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

    def _extract_lifespan(self, content: str, result: StarletteParseResult):
        """Extract lifespan handlers (on_startup, on_shutdown, lifespan context)."""
        # on_startup=[func1, func2] / on_shutdown=[...]
        for match in self.ON_EVENT_LIST_PATTERN.finditer(content):
            event = match.group(1)
            funcs_str = match.group(2)
            for func_name in re.findall(r'(\w+)', funcs_str):
                result.lifespan_handlers.append(StarletteLifespanInfo(
                    event=event,
                    handler=func_name,
                    is_async=self._is_async_function(content, func_name),
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        # @app.on_event("startup") decorator
        for match in self.ON_EVENT_DECORATOR_PATTERN.finditer(content):
            event = match.group(2)
            is_async = match.group(3) is not None
            handler = match.group(4)

            result.lifespan_handlers.append(StarletteLifespanInfo(
                event=event,
                handler=handler,
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @asynccontextmanager lifespan pattern
        lifespan_match = self.LIFESPAN_PATTERN.search(content)
        if lifespan_match:
            result.lifespan_handlers.append(StarletteLifespanInfo(
                event='lifespan',
                handler=lifespan_match.group(1),
                is_async=True,
                line_number=content[:lifespan_match.start()].count('\n') + 1,
            ))

    def _extract_exception_handlers(self, content: str, result: StarletteParseResult):
        """Extract exception handlers from exception_handlers dict."""
        # Look for exception_handlers = { ... }
        exc_block = re.search(
            r'exception_handlers\s*=\s*\{([^}]+)\}',
            content,
            re.MULTILINE,
        )
        if exc_block:
            block_content = exc_block.group(1)
            for match in self.EXCEPTION_HANDLER_DICT_PATTERN.finditer(block_content):
                exc_class = match.group(1)
                handler = match.group(2)
                result.exception_handlers.append(StarletteExceptionHandlerInfo(
                    exception_class=exc_class,
                    handler=handler,
                    line_number=content[:exc_block.start()].count('\n') + 1,
                ))

    def _extract_auth_backends(self, content: str, result: StarletteParseResult):
        """Extract AuthenticationBackend subclasses."""
        for match in self.AUTH_BACKEND_PATTERN.finditer(content):
            result.auth_backends.append(StarletteAuthBackendInfo(
                name=match.group(1),
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_static_files(self, content: str, result: StarletteParseResult):
        """Extract StaticFiles configurations."""
        for match in self.STATIC_FILES_PATTERN.finditer(content):
            directory = match.group(1)
            html = match.group(2) == 'True' if match.group(2) else False
            # Try to find the mount path by looking at context
            mount_path = "/static"
            # Check if this is inside a Mount()
            before = content[:match.start()]
            mount_check = re.search(r'Mount\s*\(\s*["\']([^"\']+)["\']', before[max(0, len(before) - 200):])
            if mount_check:
                mount_path = mount_check.group(1)

            result.static_files.append(StarletteStaticFilesInfo(
                path=mount_path,
                directory=directory,
                html=html,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    # ─── Helper methods ───────────────────────────────────────────

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a Starlette file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        if basename in ('main.py', 'app.py', 'application.py', '__init__.py'):
            if 'Starlette(' in content:
                return 'app'
        if 'middleware' in basename:
            return 'middleware'
        if 'route' in basename or 'endpoint' in basename or 'view' in basename:
            return 'router'
        if 'model' in basename or 'schema' in basename:
            return 'model'
        if 'test' in basename:
            return 'test'
        if 'auth' in basename:
            return 'auth'

        if '/middleware/' in normalized:
            return 'middleware'
        if '/routes/' in normalized or '/endpoints/' in normalized or '/views/' in normalized:
            return 'router'
        if '/models/' in normalized or '/schemas/' in normalized:
            return 'model'

        return 'module'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Starlette ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _classify_middleware(self, mw_class: str) -> str:
        """Classify middleware by name."""
        mw_lower = mw_class.lower()
        if 'cors' in mw_lower:
            return 'cors'
        if 'trustedhost' in mw_lower:
            return 'trustedhost'
        if 'gzip' in mw_lower:
            return 'gzip'
        if 'httpsredirect' in mw_lower:
            return 'httpsredirect'
        if 'session' in mw_lower:
            return 'sessions'
        if 'authentication' in mw_lower or 'auth' in mw_lower:
            return 'authentication'
        return 'custom'

    def _parse_kwargs(self, kwargs_str: str) -> Dict[str, str]:
        """Parse keyword arguments from a string."""
        kwargs = {}
        for kv in re.finditer(r'(\w+)\s*=\s*([^,\)]+)', kwargs_str):
            kwargs[kv.group(1)] = kv.group(2).strip()
        return kwargs

    def _is_async_function(self, content: str, func_name: str) -> bool:
        """Check if a function is async by searching its definition."""
        pattern = re.compile(rf'async\s+def\s+{re.escape(func_name)}\s*\(', re.MULTILINE)
        return bool(pattern.search(content))

    def _detect_starlette_version(self, content: str) -> str:
        """Detect minimum Starlette version required based on features used."""
        max_version = '0.0'
        for feature, version in self.STARLETTE_VERSION_FEATURES.items():
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

    def is_starlette_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a Starlette-specific file.
        Returns True if the file uses Starlette directly (not via FastAPI).
        """
        # Direct starlette imports
        if re.search(r'from\s+starlette\.\w+\s+import|from\s+starlette\s+import', content):
            # Exclude if this is primarily a FastAPI file
            if re.search(r'from\s+fastapi\s+import|import\s+fastapi', content):
                return False
            return True
        # Starlette app instantiation
        if re.search(r'Starlette\s*\(', content):
            return True
        # Starlette routing constructs (without FastAPI)
        if re.search(r'from\s+starlette\.routing\s+import', content):
            return True
        return False

    def to_codetrellis_format(self, result: StarletteParseResult) -> str:
        """Convert parse result to CodeTrellis compressed format."""
        lines = []

        if result.file_path:
            lines.append(f"[FILE:{Path(result.file_path).name}|type:{result.file_type}]")
        if result.detected_frameworks:
            lines.append(f"[STARLETTE_ECOSYSTEM:{','.join(result.detected_frameworks)}]")
        if result.starlette_version:
            lines.append(f"[STARLETTE_VERSION:>={result.starlette_version}]")
        lines.append("")

        # Routes
        if result.routes:
            lines.append("=== STARLETTE_ROUTES ===")
            for r in result.routes:
                methods_str = ",".join(r.methods) if r.methods else "GET"
                async_str = "|async" if r.is_async else ""
                name_str = f"|name:{r.name}" if r.name else ""
                lines.append(f"  {methods_str} {r.path} → {r.endpoint}{async_str}{name_str}")
            lines.append("")

        # Mounts
        if result.mounts:
            lines.append("=== STARLETTE_MOUNTS ===")
            for m in result.mounts:
                lines.append(f"  {m.path} → {m.app_name}[{m.mount_type}]")
            lines.append("")

        # WebSocket routes
        if result.websocket_routes:
            lines.append("=== STARLETTE_WEBSOCKET ===")
            for ws in result.websocket_routes:
                lines.append(f"  WS {ws.path} → {ws.endpoint}")
            lines.append("")

        # Middleware
        if result.middleware:
            lines.append("=== STARLETTE_MIDDLEWARE ===")
            for mw in result.middleware:
                kwargs_str = ",".join(f"{k}={v}" for k, v in list(mw.kwargs.items())[:3])
                lines.append(f"  {mw.name}[{mw.middleware_type}]({kwargs_str})")
            lines.append("")

        # Lifespan handlers
        if result.lifespan_handlers:
            lines.append("=== STARLETTE_LIFESPAN ===")
            for lh in result.lifespan_handlers:
                lines.append(f"  @{lh.event} → {lh.handler}")
            lines.append("")

        # Exception handlers
        if result.exception_handlers:
            lines.append("=== STARLETTE_EXCEPTIONS ===")
            for ex in result.exception_handlers:
                lines.append(f"  {ex.exception_class} → {ex.handler}")
            lines.append("")

        # Auth backends
        if result.auth_backends:
            lines.append("=== STARLETTE_AUTH ===")
            for ab in result.auth_backends:
                lines.append(f"  AuthBackend:{ab.name}")
            lines.append("")

        # Static files
        if result.static_files:
            lines.append("=== STARLETTE_STATIC ===")
            for sf in result.static_files:
                html_str = "|html" if sf.html else ""
                lines.append(f"  {sf.path} → dir:{sf.directory}{html_str}")
            lines.append("")

        return '\n'.join(lines)
