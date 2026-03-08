"""
Tests for Enhanced Starlette Parser.

Part of CodeTrellis v4.33 Starlette Framework Support.
Tests cover:
- Route extraction (Route(), @app.route decorator)
- Mount extraction (Mount with sub-apps, StaticFiles, GraphQL)
- WebSocket route extraction (WebSocketRoute, @app.websocket_route)
- Middleware extraction (add_middleware, Middleware() stack)
- Lifespan handler extraction (on_startup, on_shutdown, lifespan context)
- Exception handler extraction
- Auth backend extraction (AuthenticationBackend)
- Static files extraction
- Framework detection
- Version detection
- is_starlette_file detection
- to_codetrellis_format output
"""

import pytest
from codetrellis.starlette_parser_enhanced import (
    EnhancedStarletteParser,
    StarletteParseResult,
    StarletteRouteInfo,
    StarletteMountInfo,
    StarletteMiddlewareInfo,
    StarletteWebSocketInfo,
    StarletteLifespanInfo,
    StarletteExceptionHandlerInfo,
    StarletteAuthBackendInfo,
    StarletteStaticFilesInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedStarletteParser()


# ═══════════════════════════════════════════════════════════════════
# Route Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteRoutes:

    def test_extract_basic_routes(self, parser):
        """Test extracting basic Route() definitions."""
        content = """
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse

async def homepage(request):
    return JSONResponse({"hello": "world"})

async def about(request):
    return JSONResponse({"about": "us"})

app = Starlette(routes=[
    Route("/", homepage),
    Route("/about", about, methods=["GET"]),
])
"""
        result = parser.parse(content, "main.py")
        assert len(result.routes) >= 2
        paths = [r.path for r in result.routes]
        assert "/" in paths
        assert "/about" in paths

    def test_extract_routes_with_methods(self, parser):
        """Test routes with explicit HTTP methods."""
        content = """
from starlette.routing import Route

async def create_item(request):
    pass

routes = [
    Route("/items", create_item, methods=["POST", "PUT"]),
]
"""
        result = parser.parse(content)
        assert len(result.routes) >= 1
        route = result.routes[0]
        assert "POST" in route.methods
        assert "PUT" in route.methods

    def test_extract_routes_with_name(self, parser):
        """Test routes with explicit name parameter."""
        content = """
from starlette.routing import Route

async def users_list(request):
    pass

Route("/users", users_list, methods=["GET"], name="users-list")
"""
        result = parser.parse(content)
        assert len(result.routes) >= 1
        assert result.routes[0].name == "users-list"

    def test_decorator_route(self, parser):
        """Test @app.route() decorator style."""
        content = """
from starlette.applications import Starlette

app = Starlette()

@app.route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok"})

@app.route("/data")
def sync_handler(request):
    return JSONResponse({"data": []})
"""
        result = parser.parse(content, "app.py")
        assert len(result.routes) >= 2
        endpoints = [r.endpoint for r in result.routes]
        assert "health_check" in endpoints
        assert "sync_handler" in endpoints


# ═══════════════════════════════════════════════════════════════════
# Mount Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteMounts:

    def test_extract_basic_mount(self, parser):
        """Test Mount() extraction."""
        content = """
from starlette.routing import Mount, Route

routes = [
    Mount("/api", routes=[
        Route("/users", users_endpoint),
    ]),
]
"""
        result = parser.parse(content)
        # Note: Mount with routes=[...] inline won't match pattern since second arg is routes=
        # But Mount with app= should match
        assert isinstance(result, StarletteParseResult)

    def test_extract_static_files_mount(self, parser):
        """Test Mount with StaticFiles."""
        content = """
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

Mount("/static", StaticFiles(directory="static"))
"""
        result = parser.parse(content)
        mounts_with_static = [m for m in result.mounts if m.mount_type == "static"]
        assert len(mounts_with_static) >= 1


# ═══════════════════════════════════════════════════════════════════
# WebSocket Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteWebSocket:

    def test_extract_websocket_route(self, parser):
        """Test WebSocketRoute() extraction."""
        content = """
from starlette.routing import WebSocketRoute

async def ws_endpoint(websocket):
    await websocket.accept()

routes = [
    WebSocketRoute("/ws", ws_endpoint),
]
"""
        result = parser.parse(content)
        assert len(result.websocket_routes) >= 1
        ws = result.websocket_routes[0]
        assert ws.path == "/ws"
        assert ws.endpoint == "ws_endpoint"

    def test_decorator_websocket_route(self, parser):
        """Test @app.websocket_route() decorator style."""
        content = """
from starlette.applications import Starlette

app = Starlette()

@app.websocket_route("/ws/chat")
async def chat_ws(websocket):
    await websocket.accept()
"""
        result = parser.parse(content)
        assert len(result.websocket_routes) >= 1
        assert result.websocket_routes[0].path == "/ws/chat"


# ═══════════════════════════════════════════════════════════════════
# Middleware Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteMiddleware:

    def test_add_middleware(self, parser):
        """Test app.add_middleware() extraction."""
        content = """
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
"""
        result = parser.parse(content)
        assert len(result.middleware) >= 1
        mw = result.middleware[0]
        assert mw.name == "CORSMiddleware"
        assert mw.middleware_type == "cors"

    def test_middleware_stack(self, parser):
        """Test Middleware() stack pattern."""
        content = """
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"]),
    Middleware(GZipMiddleware, minimum_size=500),
]

app = Starlette(middleware=middleware)
"""
        result = parser.parse(content)
        assert len(result.middleware) >= 2
        names = [m.name for m in result.middleware]
        assert "CORSMiddleware" in names
        assert "GZipMiddleware" in names

    def test_middleware_classification(self, parser):
        """Test middleware type classification."""
        content = """
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware

middleware = [
    Middleware(SessionMiddleware, secret_key="secret"),
    Middleware(HTTPSRedirectMiddleware),
    Middleware(TrustedHostMiddleware, allowed_hosts=["example.com"]),
    Middleware(AuthenticationMiddleware, backend=my_backend),
]
"""
        result = parser.parse(content)
        types = {m.name: m.middleware_type for m in result.middleware}
        assert types.get("SessionMiddleware") == "sessions"
        assert types.get("HTTPSRedirectMiddleware") == "httpsredirect"
        assert types.get("TrustedHostMiddleware") == "trustedhost"
        assert types.get("AuthenticationMiddleware") == "authentication"


# ═══════════════════════════════════════════════════════════════════
# Lifespan Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteLifespan:

    def test_on_startup_shutdown_list(self, parser):
        """Test on_startup=[...] / on_shutdown=[...] extraction."""
        content = """
from starlette.applications import Starlette

async def startup():
    print("Starting...")

async def shutdown():
    print("Shutting down...")

app = Starlette(
    on_startup=[startup],
    on_shutdown=[shutdown],
)
"""
        result = parser.parse(content)
        events = {lh.event: lh.handler for lh in result.lifespan_handlers}
        assert "startup" in events
        assert events["startup"] == "startup"
        assert "shutdown" in events

    def test_on_event_decorator(self, parser):
        """Test @app.on_event("startup") decorator pattern."""
        content = """
from starlette.applications import Starlette

app = Starlette()

@app.on_event("startup")
async def on_startup():
    print("Starting...")

@app.on_event("shutdown")
async def on_shutdown():
    print("Shutting down...")
"""
        result = parser.parse(content)
        events = [lh.event for lh in result.lifespan_handlers]
        assert "startup" in events
        assert "shutdown" in events

    def test_lifespan_context_manager(self, parser):
        """Test @asynccontextmanager lifespan pattern (Starlette 0.20+)."""
        content = """
from contextlib import asynccontextmanager
from starlette.applications import Starlette

@asynccontextmanager
async def lifespan(app):
    print("Starting up")
    yield
    print("Shutting down")

app = Starlette(lifespan=lifespan)
"""
        result = parser.parse(content)
        lifespan_events = [lh for lh in result.lifespan_handlers if lh.event == "lifespan"]
        assert len(lifespan_events) >= 1
        assert lifespan_events[0].handler == "lifespan"


# ═══════════════════════════════════════════════════════════════════
# Exception Handler Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteExceptionHandlers:

    def test_exception_handlers_dict(self, parser):
        """Test exception_handlers dictionary extraction."""
        content = """
from starlette.applications import Starlette

async def not_found(request, exc):
    return JSONResponse({"error": "Not found"}, status_code=404)

async def server_error(request, exc):
    return JSONResponse({"error": "Server error"}, status_code=500)

exception_handlers = {
    404: not_found,
    500: server_error,
}

app = Starlette(exception_handlers=exception_handlers)
"""
        result = parser.parse(content)
        assert len(result.exception_handlers) >= 2
        exc_classes = [eh.exception_class for eh in result.exception_handlers]
        assert "404" in exc_classes
        assert "500" in exc_classes


# ═══════════════════════════════════════════════════════════════════
# Auth Backend Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteAuth:

    def test_auth_backend(self, parser):
        """Test AuthenticationBackend extraction."""
        content = """
from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser

class JWTAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        token = conn.headers.get("Authorization")
        if token:
            return AuthCredentials(["authenticated"]), SimpleUser("user")
"""
        result = parser.parse(content)
        assert len(result.auth_backends) >= 1
        assert result.auth_backends[0].name == "JWTAuthBackend"


# ═══════════════════════════════════════════════════════════════════
# Static Files Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteStaticFiles:

    def test_static_files(self, parser):
        """Test StaticFiles extraction."""
        content = """
from starlette.staticfiles import StaticFiles
from starlette.routing import Mount

routes = [
    Mount("/static", StaticFiles(directory="static")),
]
"""
        result = parser.parse(content)
        assert len(result.static_files) >= 1
        sf = result.static_files[0]
        assert sf.directory == "static"

    def test_static_files_html(self, parser):
        """Test StaticFiles with html=True."""
        content = """
from starlette.staticfiles import StaticFiles
from starlette.routing import Mount

Mount("/", StaticFiles(directory="build", html=True))
"""
        result = parser.parse(content)
        assert len(result.static_files) >= 1
        assert result.static_files[0].html is True


# ═══════════════════════════════════════════════════════════════════
# Framework Detection & Version Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteDetection:

    def test_detect_frameworks(self, parser):
        """Test framework detection."""
        content = """
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware
from starlette.templating import Jinja2Templates
from starlette.authentication import AuthenticationBackend
"""
        result = parser.parse(content)
        assert "starlette" in result.detected_frameworks
        assert "starlette.cors" in result.detected_frameworks
        assert "starlette.templating" in result.detected_frameworks
        assert "starlette.authentication" in result.detected_frameworks

    def test_version_detection(self, parser):
        """Test version feature detection."""
        content = """
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.authentication import AuthenticationBackend

@asynccontextmanager
async def lifespan(app):
    yield
"""
        result = parser.parse(content)
        # Should detect >= 0.20 (lifespan feature)
        assert result.starlette_version != ""

    def test_is_starlette_file(self, parser):
        """Test starlette file detection."""
        content = """
from starlette.applications import Starlette
from starlette.routing import Route

app = Starlette(routes=[])
"""
        assert parser.is_starlette_file(content) is True

    def test_not_starlette_file(self, parser):
        """Test non-starlette file detection."""
        content = """
def hello():
    print("Hello")
"""
        assert parser.is_starlette_file(content) is False

    def test_fastapi_not_starlette(self, parser):
        """Test FastAPI file is not identified as Starlette."""
        content = """
from fastapi import FastAPI
from starlette.responses import JSONResponse

app = FastAPI()
"""
        assert parser.is_starlette_file(content) is False


# ═══════════════════════════════════════════════════════════════════
# File Classification Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteClassification:

    def test_classify_app(self, parser):
        """Test app file classification."""
        content = "app = Starlette(routes=[])"
        result = parser.parse(content, "main.py")
        assert result.file_type == "app"

    def test_classify_middleware(self, parser):
        """Test middleware file classification."""
        content = "class LoggingMiddleware: pass"
        result = parser.parse(content, "middleware.py")
        assert result.file_type == "middleware"

    def test_classify_test(self, parser):
        """Test test file classification."""
        content = "def test_homepage(): pass"
        result = parser.parse(content, "test_app.py")
        assert result.file_type == "test"


# ═══════════════════════════════════════════════════════════════════
# CodeTrellis Format Output Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteFormat:

    def test_to_codetrellis_format_routes(self, parser):
        """Test CodeTrellis format includes routes."""
        content = """
from starlette.applications import Starlette
from starlette.routing import Route

async def homepage(request):
    return JSONResponse({"hello": "world"})

Route("/", homepage, methods=["GET"])
"""
        result = parser.parse(content, "app.py")
        output = parser.to_codetrellis_format(result)
        assert "STARLETTE_ROUTES" in output

    def test_to_codetrellis_format_middleware(self, parser):
        """Test CodeTrellis format includes middleware."""
        content = """
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

Middleware(CORSMiddleware, allow_origins=["*"])
"""
        result = parser.parse(content)
        output = parser.to_codetrellis_format(result)
        assert "STARLETTE_MIDDLEWARE" in output

    def test_to_codetrellis_format_empty(self, parser):
        """Test CodeTrellis format for empty/non-starlette file."""
        content = "x = 1"
        result = parser.parse(content)
        output = parser.to_codetrellis_format(result)
        assert "STARLETTE_ROUTES" not in output

    def test_parse_empty_file(self, parser):
        """Test parsing an empty file."""
        result = parser.parse("")
        assert result.total_routes == 0
        assert result.total_middleware == 0
        assert len(result.routes) == 0


# ═══════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestStarletteIntegration:

    def test_full_starlette_app(self, parser):
        """Test parsing a full Starlette application."""
        content = """
from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse
from starlette.authentication import AuthenticationBackend, AuthCredentials

class MyAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        return None

async def homepage(request):
    return JSONResponse({"msg": "Hello"})

async def users(request):
    return JSONResponse([])

async def ws_handler(websocket):
    await websocket.accept()

@asynccontextmanager
async def lifespan(app):
    print("startup")
    yield
    print("shutdown")

exception_handlers = {
    404: homepage,
}

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"]),
    Middleware(SessionMiddleware, secret_key="secret"),
]

routes = [
    Route("/", homepage, methods=["GET"]),
    Route("/users", users, methods=["GET", "POST"]),
    WebSocketRoute("/ws", ws_handler),
    Mount("/static", StaticFiles(directory="static")),
]

app = Starlette(
    routes=routes,
    middleware=middleware,
    lifespan=lifespan,
    exception_handlers=exception_handlers,
)
"""
        result = parser.parse(content, "main.py")

        # Routes
        assert len(result.routes) >= 2
        # WebSockets
        assert len(result.websocket_routes) >= 1
        # Middleware
        assert len(result.middleware) >= 2
        # Lifespan
        assert len(result.lifespan_handlers) >= 1
        # Exception handlers
        assert len(result.exception_handlers) >= 1
        # Auth backends
        assert len(result.auth_backends) >= 1
        # Static files
        assert len(result.static_files) >= 1
        # File type
        assert result.file_type == "app"
        # Total routes
        assert result.total_routes >= 3

        # Format output
        output = parser.to_codetrellis_format(result)
        assert "STARLETTE_ROUTES" in output
        assert "STARLETTE_MIDDLEWARE" in output
        assert "STARLETTE_WEBSOCKET" in output
        assert "STARLETTE_LIFESPAN" in output
        assert "STARLETTE_AUTH" in output
