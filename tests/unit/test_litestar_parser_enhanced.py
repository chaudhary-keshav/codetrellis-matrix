"""
Tests for Enhanced Litestar Parser.

Part of CodeTrellis v4.93 Litestar Framework Support.
Tests cover:
- Route extraction (@get, @post, @put, @delete, @patch, @head, @options, @route)
- Controller extraction (class-based handlers)
- Guard extraction (function guards, AbstractGuard)
- Dependency extraction (Provide, Dependency)
- Middleware extraction (AbstractMiddleware, DefineMiddleware)
- Listener extraction (on_startup, on_shutdown, on_app_init)
- WebSocket route extraction (@websocket, @websocket_listener)
- Exception handler extraction
- DTO extraction (DataclassDTO, PydanticDTO, DTOConfig)
- Plugin extraction
- Store extraction (MemoryStore, FileStore, RedisStore)
- Security extraction (SessionAuth, JWTAuth, JWTCookieAuth)
- Framework detection (litestar-core, starlite-legacy, etc.)
- Version detection
- is_litestar_file detection
- to_codetrellis_format output
"""

import pytest
from codetrellis.litestar_parser_enhanced import (
    EnhancedLitestarParser,
    LitestarParseResult,
    LitestarRouteInfo,
    LitestarControllerInfo,
    LitestarGuardInfo,
    LitestarDependencyInfo,
    LitestarMiddlewareInfo,
    LitestarListenerInfo,
    LitestarWebSocketInfo,
    LitestarExceptionHandlerInfo,
    LitestarDTOInfo,
    LitestarPluginInfo,
    LitestarStoreInfo,
    LitestarSecurityInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedLitestarParser()


# ═══════════════════════════════════════════════════════════════════
# Route Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarRoutes:

    def test_extract_get_route(self, parser):
        source = '''
from litestar import get

@get("/items")
async def list_items() -> list[dict]:
    return []
'''
        result = parser.parse(source, "routes.py")
        assert len(result.routes) >= 1
        route = result.routes[0]
        assert route.path == "/items"
        assert route.handler == "list_items"
        assert "GET" in route.methods
        assert route.is_async is True

    def test_extract_post_route(self, parser):
        source = '''
from litestar import post

@post("/items")
async def create_item(data: dict) -> dict:
    return data
'''
        result = parser.parse(source, "routes.py")
        assert len(result.routes) >= 1
        assert result.routes[0].path == "/items"
        assert "POST" in result.routes[0].methods

    def test_extract_all_http_methods(self, parser):
        source = '''
from litestar import get, post, put, patch, delete, head, options

@get("/items")
async def list_items() -> list:
    return []

@post("/items")
async def create_item() -> dict:
    return {}

@put("/items/{item_id:int}")
async def update_item(item_id: int) -> dict:
    return {}

@patch("/items/{item_id:int}")
async def patch_item(item_id: int) -> dict:
    return {}

@delete("/items/{item_id:int}")
async def delete_item(item_id: int) -> None:
    pass

@head("/items")
async def head_items() -> None:
    pass

@options("/items")
async def options_items() -> None:
    pass
'''
        result = parser.parse(source, "routes.py")
        assert len(result.routes) >= 7
        methods = [r.methods[0] for r in result.routes]
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "PATCH" in methods
        assert "DELETE" in methods
        assert "HEAD" in methods
        assert "OPTIONS" in methods

    def test_extract_sync_route(self, parser):
        source = '''
from litestar import get

@get("/sync")
def sync_handler() -> str:
    return "hello"
'''
        result = parser.parse(source, "routes.py")
        assert len(result.routes) >= 1
        assert result.routes[0].is_async is False

    def test_extract_route_decorator(self, parser):
        source = '''
from litestar import route

@route("/items", http_method=["GET", "POST"])
async def items_handler() -> None:
    pass
'''
        result = parser.parse(source, "routes.py")
        assert len(result.routes) >= 1
        r = result.routes[0]
        assert r.path == "/items"
        assert "GET" in r.methods
        assert "POST" in r.methods

    def test_extract_route_without_path(self, parser):
        source = '''
from litestar import get

@get()
async def root_handler() -> str:
    return "root"
'''
        result = parser.parse(source, "routes.py")
        assert len(result.routes) >= 1
        assert result.routes[0].path == "/"


# ═══════════════════════════════════════════════════════════════════
# Controller Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarControllers:

    def test_extract_basic_controller(self, parser):
        source = '''
from litestar import Controller, get, post

class UserController(Controller):
    path = "/users"

    @get()
    async def list_users(self) -> list:
        return []

    @post()
    async def create_user(self) -> dict:
        return {}
'''
        result = parser.parse(source, "controllers.py")
        assert len(result.controllers) >= 1
        ctrl = result.controllers[0]
        assert ctrl.name == "UserController"
        assert ctrl.path == "/users"
        assert len(ctrl.methods) >= 2

    def test_extract_controller_with_guards(self, parser):
        source = '''
from litestar import Controller, get

class AdminController(Controller):
    path = "/admin"
    guards = [admin_guard, rate_limit_guard]

    @get()
    async def admin_dashboard(self) -> dict:
        return {}
'''
        result = parser.parse(source, "controllers.py")
        assert len(result.controllers) >= 1
        ctrl = result.controllers[0]
        assert len(ctrl.guards) >= 2

    def test_extract_controller_with_tags(self, parser):
        source = '''
from litestar import Controller, get

class ItemController(Controller):
    path = "/items"
    tags = ["items", "catalog"]

    @get()
    async def list_items(self) -> list:
        return []
'''
        result = parser.parse(source, "controllers.py")
        assert len(result.controllers) >= 1


# ═══════════════════════════════════════════════════════════════════
# Guard Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarGuards:

    def test_extract_guard_function(self, parser):
        source = '''
from litestar.connection import ASGIConnection
from litestar.handlers import BaseRouteHandler

async def admin_guard(connection: ASGIConnection, handler: BaseRouteHandler) -> None:
    if not connection.user.is_admin:
        raise NotAuthorizedException()
'''
        result = parser.parse(source, "guards.py")
        assert len(result.guards) >= 1
        guard = result.guards[0]
        assert guard.name == "admin_guard"
        assert guard.is_async is True

    def test_extract_guard_class(self, parser):
        source = '''
from litestar.security import AbstractGuard

class RateLimitGuard(AbstractGuard):
    async def __call__(self, connection, handler):
        pass
'''
        result = parser.parse(source, "guards.py")
        assert len(result.guards) >= 1
        assert result.guards[0].name == "RateLimitGuard"
        assert result.guards[0].guard_type == "AbstractGuard"


# ═══════════════════════════════════════════════════════════════════
# Dependency Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarDependencies:

    def test_extract_provide_dependency(self, parser):
        source = '''
from litestar import Litestar
from litestar.di import Provide

async def provide_db():
    return Database()

app = Litestar(
    dependencies={"db": Provide(provide_db)}
)
'''
        result = parser.parse(source, "app.py")
        assert len(result.dependencies) >= 1
        dep = result.dependencies[0]
        assert dep.name == "db"
        assert dep.provide_type == "Provide"

    def test_extract_provide_with_cache(self, parser):
        source = '''
from litestar.di import Provide

dependencies = {
    "config": Provide(get_config, use_cache=True)
}
'''
        result = parser.parse(source, "deps.py")
        assert len(result.dependencies) >= 1
        assert result.dependencies[0].use_cache is True

    def test_extract_provide_sync_to_thread(self, parser):
        source = '''
from litestar.di import Provide

dependencies = {
    "heavy_compute": Provide(compute_func, sync_to_thread=True)
}
'''
        result = parser.parse(source, "deps.py")
        assert len(result.dependencies) >= 1
        assert result.dependencies[0].sync_to_thread is True


# ═══════════════════════════════════════════════════════════════════
# Middleware Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarMiddleware:

    def test_extract_abstract_middleware(self, parser):
        source = '''
from litestar.middleware import AbstractMiddleware

class LoggingMiddleware(AbstractMiddleware):
    async def __call__(self, scope, receive, send):
        pass
'''
        result = parser.parse(source, "middleware.py")
        assert len(result.middleware) >= 1
        mw = result.middleware[0]
        assert mw.name == "LoggingMiddleware"
        assert mw.middleware_type == "AbstractMiddleware"

    def test_extract_middleware_protocol(self, parser):
        source = '''
from litestar.middleware import MiddlewareProtocol

class CORSMiddleware(MiddlewareProtocol):
    async def __call__(self, scope, receive, send):
        pass
'''
        result = parser.parse(source, "middleware.py")
        assert len(result.middleware) >= 1
        assert result.middleware[0].middleware_type == "MiddlewareProtocol"

    def test_extract_define_middleware(self, parser):
        source = '''
from litestar.middleware import DefineMiddleware

auth_middleware = DefineMiddleware(AuthMiddleware, exclude=["login"])
'''
        result = parser.parse(source, "middleware.py")
        assert len(result.middleware) >= 1
        mw = [m for m in result.middleware if m.name == "AuthMiddleware"]
        assert len(mw) >= 1


# ═══════════════════════════════════════════════════════════════════
# Listener Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarListeners:

    def test_extract_lifecycle_listeners(self, parser):
        source = '''
from litestar import Litestar

async def startup_handler():
    print("Starting up")

async def shutdown_handler():
    print("Shutting down")

app = Litestar(
    on_startup=[startup_handler],
    on_shutdown=[shutdown_handler],
)
'''
        result = parser.parse(source, "app.py")
        assert len(result.listeners) >= 2
        events = [l.event for l in result.listeners]
        assert "on_startup" in events
        assert "on_shutdown" in events

    def test_extract_before_send_listener(self, parser):
        source = '''
from litestar import Litestar

async def before_send_hook(message, scope):
    pass

app = Litestar(
    before_send=[before_send_hook],
)
'''
        result = parser.parse(source, "app.py")
        assert len(result.listeners) >= 1
        assert result.listeners[0].event == "before_send"


# ═══════════════════════════════════════════════════════════════════
# WebSocket Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarWebSockets:

    def test_extract_websocket_route(self, parser):
        source = '''
from litestar import websocket

@websocket("/ws")
async def ws_handler(socket) -> None:
    data = await socket.receive_data()
    await socket.send_data(data)
'''
        result = parser.parse(source, "ws.py")
        assert len(result.websocket_routes) >= 1
        ws = result.websocket_routes[0]
        assert ws.path == "/ws"
        assert ws.handler == "ws_handler"

    def test_extract_websocket_listener(self, parser):
        source = '''
from litestar import websocket_listener

@websocket_listener("/ws/chat")
async def chat_handler(data: str) -> str:
    return f"Echo: {data}"
'''
        result = parser.parse(source, "ws.py")
        assert len(result.websocket_routes) >= 1
        ws = result.websocket_routes[0]
        assert ws.path == "/ws/chat"


# ═══════════════════════════════════════════════════════════════════
# Exception Handler Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarExceptionHandlers:

    def test_extract_exception_handlers(self, parser):
        source = '''
from litestar import Litestar

def validation_exception_handler(request, exc):
    return Response({"error": str(exc)}, status_code=400)

def not_found_handler(request, exc):
    return Response({"error": "Not Found"}, status_code=404)

app = Litestar(
    exception_handlers={ValidationException: validation_exception_handler, NotFoundException: not_found_handler}
)
'''
        result = parser.parse(source, "app.py")
        assert len(result.exception_handlers) >= 2
        exc_classes = [eh.exception_class for eh in result.exception_handlers]
        assert "ValidationException" in exc_classes
        assert "NotFoundException" in exc_classes


# ═══════════════════════════════════════════════════════════════════
# DTO Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarDTOs:

    def test_extract_dataclass_dto(self, parser):
        source = '''
from litestar.dto import DataclassDTO

class UserDTO(DataclassDTO[User]):
    config = DTOConfig(exclude={"password"})
'''
        result = parser.parse(source, "dtos.py")
        assert len(result.dtos) >= 1
        dto = result.dtos[0]
        assert dto.name == "UserDTO"
        assert dto.dto_type == "DataclassDTO"
        assert dto.model_class == "User"

    def test_extract_pydantic_dto(self, parser):
        source = '''
from litestar.contrib.pydantic import PydanticDTO

class ItemDTO(PydanticDTO[Item]):
    pass
'''
        result = parser.parse(source, "dtos.py")
        assert len(result.dtos) >= 1
        assert result.dtos[0].dto_type == "PydanticDTO"

    def test_extract_dto_config(self, parser):
        source = '''
from litestar.dto import DTOConfig

write_config = DTOConfig(exclude={"id", "created_at"})
'''
        result = parser.parse(source, "dtos.py")
        configs = [d for d in result.dtos if d.dto_type == "DTOConfig"]
        assert len(configs) >= 1
        assert configs[0].name == "write_config"


# ═══════════════════════════════════════════════════════════════════
# Plugin Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarPlugins:

    def test_extract_plugin_class(self, parser):
        source = '''
from litestar.plugins import InitPluginProtocol

class MyCustomPlugin(InitPluginProtocol):
    def on_app_init(self, app_config):
        pass
'''
        result = parser.parse(source, "plugins.py")
        assert len(result.plugins) >= 1
        assert result.plugins[0].name == "MyCustomPlugin"
        assert result.plugins[0].plugin_type == "InitPluginProtocol"


# ═══════════════════════════════════════════════════════════════════
# Store Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarStores:

    def test_extract_memory_store(self, parser):
        source = '''
from litestar.stores.memory import MemoryStore

cache = MemoryStore()
'''
        result = parser.parse(source, "stores.py")
        assert len(result.stores) >= 1
        assert result.stores[0].store_type == "MemoryStore"

    def test_extract_redis_store(self, parser):
        source = '''
from litestar.stores.redis import RedisStore

session_store = RedisStore.with_client(url="redis://localhost")
'''
        result = parser.parse(source, "stores.py")
        assert len(result.stores) >= 1
        assert result.stores[0].store_type == "RedisStore"


# ═══════════════════════════════════════════════════════════════════
# Security Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarSecurity:

    def test_extract_jwt_auth(self, parser):
        source = '''
from litestar.security.jwt import JWTAuth

jwt_auth = JWTAuth[User](
    token_secret="secret",
    retrieve_user_handler=retrieve_user,
)
'''
        result = parser.parse(source, "security.py")
        assert len(result.security) >= 1
        sec = result.security[0]
        assert sec.name == "jwt_auth"
        assert sec.auth_type == "JWTAuth"

    def test_extract_session_auth(self, parser):
        source = '''
from litestar.security.session_auth import SessionAuth

session_auth = SessionAuth[User, ServerSideSessionBackend](
    retrieve_user_handler=get_user,
    session_backend_config=session_config,
)
'''
        result = parser.parse(source, "security.py")
        assert len(result.security) >= 1
        assert result.security[0].auth_type == "SessionAuth"


# ═══════════════════════════════════════════════════════════════════
# Framework Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarFrameworkDetection:

    def test_detect_litestar_core(self, parser):
        source = '''
from litestar import Litestar, get
'''
        result = parser.parse(source, "app.py")
        assert 'litestar-core' in result.detected_frameworks

    def test_detect_starlite_legacy(self, parser):
        source = '''
from starlite import Starlite, get
'''
        result = parser.parse(source, "app.py")
        assert 'starlite-legacy' in result.detected_frameworks

    def test_detect_litestar_dto(self, parser):
        source = '''
from litestar.dto import DataclassDTO, DTOConfig
'''
        result = parser.parse(source, "dtos.py")
        assert 'litestar-dto' in result.detected_frameworks

    def test_detect_litestar_security(self, parser):
        source = '''
from litestar.security.jwt import JWTAuth
'''
        result = parser.parse(source, "security.py")
        assert 'litestar-security' in result.detected_frameworks

    def test_detect_sqlalchemy_plugin(self, parser):
        source = '''
from advanced_alchemy import SQLAlchemyPlugin
'''
        result = parser.parse(source, "plugins.py")
        assert 'sqlalchemy-plugin' in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Version Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarVersionDetection:

    def test_detect_v1_starlite(self, parser):
        source = '''
from starlite import Starlite, get

@get("/")
async def index() -> str:
    return "Hello"

app = Starlite(route_handlers=[index])
'''
        result = parser.parse(source, "app.py")
        assert result.litestar_version == '1.0'

    def test_detect_v2_features(self, parser):
        source = '''
from litestar import Litestar, get
from litestar.dto import DTOConfig

@get("/")
async def index() -> str:
    return "Hello"

app = Litestar(route_handlers=[index])
'''
        result = parser.parse(source, "app.py")
        assert result.litestar_version == '2.0'


# ═══════════════════════════════════════════════════════════════════
# is_litestar_file Tests
# ═══════════════════════════════════════════════════════════════════

class TestIsLitestarFile:

    def test_detects_litestar_import(self, parser):
        source = '''
from litestar import Litestar, get
'''
        assert parser.is_litestar_file(source) is True

    def test_detects_starlite_import(self, parser):
        source = '''
from starlite import Starlite, get
'''
        assert parser.is_litestar_file(source) is True

    def test_detects_litestar_submodule_import(self, parser):
        source = '''
from litestar.dto import DataclassDTO
'''
        assert parser.is_litestar_file(source) is True

    def test_no_detection_for_non_litestar(self, parser):
        source = '''
from flask import Flask

app = Flask(__name__)
'''
        assert parser.is_litestar_file(source) is False

    def test_detects_litestar_app_instantiation(self, parser):
        source = '''
app = Litestar(route_handlers=[index])
'''
        assert parser.is_litestar_file(source) is True


# ═══════════════════════════════════════════════════════════════════
# to_codetrellis_format Tests
# ═══════════════════════════════════════════════════════════════════

class TestToCodetrelisFormat:

    def test_format_output(self, parser):
        source = '''
from litestar import Litestar, get, Controller

class ItemController(Controller):
    path = "/items"

    @get()
    async def list_items(self) -> list:
        return []

@get("/health")
async def health() -> dict:
    return {"status": "ok"}

app = Litestar(route_handlers=[ItemController, health])
'''
        result = parser.parse(source, "app.py")
        output = parser.to_codetrellis_format(result)
        assert "LITESTAR_ROUTES" in output
        assert "LITESTAR_CONTROLLERS" in output
        assert "ItemController" in output

    def test_format_empty_result(self, parser):
        source = '''
# Empty Python file
x = 1
'''
        result = parser.parse(source, "empty.py")
        output = parser.to_codetrellis_format(result)
        assert "LITESTAR_ROUTES" not in output


# ═══════════════════════════════════════════════════════════════════
# File Classification Tests
# ═══════════════════════════════════════════════════════════════════

class TestFileClassification:

    def test_classify_app_file(self, parser):
        source = '''
from litestar import Litestar
app = Litestar(route_handlers=[])
'''
        result = parser.parse(source, "app.py")
        assert result.file_type == "app"

    def test_classify_controller_file(self, parser):
        source = '''
from litestar import Controller
'''
        result = parser.parse(source, "user_controller.py")
        assert result.file_type == "controller"

    def test_classify_middleware_file(self, parser):
        source = '''
from litestar.middleware import AbstractMiddleware
'''
        result = parser.parse(source, "middleware.py")
        assert result.file_type == "middleware"

    def test_classify_guard_file(self, parser):
        source = '''
guard = True
'''
        result = parser.parse(source, "guard.py")
        assert result.file_type == "guard"

    def test_classify_dto_file(self, parser):
        source = '''
dto_config = True
'''
        result = parser.parse(source, "dto.py")
        assert result.file_type == "dto"


# ═══════════════════════════════════════════════════════════════════
# Aggregation Tests
# ═══════════════════════════════════════════════════════════════════

class TestAggregations:

    def test_total_routes_includes_websockets(self, parser):
        source = '''
from litestar import get, websocket

@get("/items")
async def list_items() -> list:
    return []

@websocket("/ws")
async def ws_handler(socket) -> None:
    pass
'''
        result = parser.parse(source, "app.py")
        assert result.total_routes == len(result.routes) + len(result.websocket_routes)
        assert result.total_routes >= 2


# ═══════════════════════════════════════════════════════════════════
# Complex Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitestarIntegration:

    def test_full_app_parsing(self, parser):
        source = '''
from litestar import Litestar, get, post, Controller, websocket
from litestar.di import Provide
from litestar.middleware import AbstractMiddleware
from litestar.security.jwt import JWTAuth
from litestar.stores.memory import MemoryStore
from litestar.dto import DataclassDTO, DTOConfig

cache_store = MemoryStore()

jwt_auth = JWTAuth[dict](
    token_secret="secret",
    retrieve_user_handler=lambda: None,
)

class LogMiddleware(AbstractMiddleware):
    async def __call__(self, scope, receive, send):
        pass

async def provide_db():
    return None

class UserDTO(DataclassDTO[dict]):
    config = DTOConfig(exclude={"password"})

class UserController(Controller):
    path = "/users"

    @get()
    async def list_users(self) -> list:
        return []

    @post()
    async def create_user(self) -> dict:
        return {}

@get("/health")
async def health() -> dict:
    return {"status": "ok"}

@websocket("/ws")
async def ws_handler(socket) -> None:
    pass

async def on_start():
    print("starting")

app = Litestar(
    route_handlers=[UserController, health, ws_handler],
    dependencies={"db": Provide(provide_db)},
    on_startup=[on_start],
    exception_handlers={ValueError: lambda r, e: None}
)
'''
        result = parser.parse(source, "app.py")
        assert len(result.routes) >= 3  # list_users, create_user, health
        assert len(result.controllers) >= 1
        assert len(result.middleware) >= 1
        assert len(result.dependencies) >= 1
        assert len(result.websocket_routes) >= 1
        assert len(result.dtos) >= 1
        assert len(result.stores) >= 1
        assert len(result.security) >= 1
        assert len(result.listeners) >= 1
        assert result.litestar_version >= '2.0'
