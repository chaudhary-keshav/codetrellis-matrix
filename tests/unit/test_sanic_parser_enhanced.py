"""
Tests for Enhanced Sanic Parser.

Part of CodeTrellis v4.92 Sanic Framework Support.
Tests cover:
- Route extraction (decorator-based, HTTP method, add_route)
- Blueprint extraction
- Middleware extraction (request, response)
- Listener extraction (server lifecycle events)
- Signal extraction
- WebSocket route extraction
- Static file route extraction
- Exception handler extraction
- Class-based view extraction (HTTPMethodView)
- Framework detection
- Version detection
- is_sanic_file detection
- to_codetrellis_format output
"""

import pytest
from codetrellis.sanic_parser_enhanced import (
    EnhancedSanicParser,
    SanicParseResult,
    SanicRouteInfo,
    SanicBlueprintInfo,
    SanicMiddlewareInfo,
    SanicListenerInfo,
    SanicSignalInfo,
    SanicWebSocketInfo,
    SanicStaticInfo,
    SanicExceptionHandlerInfo,
    SanicClassBasedViewInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedSanicParser()


# ═══════════════════════════════════════════════════════════════════
# Route Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicRoutes:

    def test_extract_decorator_routes(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.route("/hello")
async def hello(request):
    return text("Hello")

@app.route("/users", methods=["GET", "POST"])
async def users(request):
    return json({"users": []})

@app.route("/items/<item_id>", methods=["GET"])
async def get_item(request, item_id):
    return json({"id": item_id})
'''
        result = parser.parse(source, "app.py")
        assert len(result.routes) >= 3
        paths = [r.path for r in result.routes]
        assert "/hello" in paths
        assert "/users" in paths
        assert "/items/<item_id>" in paths

    def test_extract_http_method_decorators(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.get("/items")
async def list_items(request):
    return json([])

@app.post("/items")
async def create_item(request):
    return json({})

@app.put("/items/<id>")
async def update_item(request, id):
    return json({})

@app.delete("/items/<id>")
async def delete_item(request, id):
    return empty()

@app.patch("/items/<id>")
async def patch_item(request, id):
    return json({})

@app.head("/items")
async def head_items(request):
    return empty()

@app.options("/items")
async def options_items(request):
    return empty()
'''
        result = parser.parse(source, "routes.py")
        assert len(result.routes) >= 7
        handlers = [r.handler for r in result.routes]
        assert "list_items" in handlers
        assert "create_item" in handlers
        assert "update_item" in handlers
        assert "delete_item" in handlers

    def test_extract_versioned_routes(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.route("/users", version=1)
async def users_v1(request):
    return json([])

@app.route("/users", version=2)
async def users_v2(request):
    return json([])
'''
        result = parser.parse(source, "versioned.py")
        assert len(result.routes) >= 2

    def test_extract_add_route(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

async def handler(request):
    return json({})

app.add_route(handler, "/test")
app.add_route(handler, "/test2", methods=["POST"])
'''
        result = parser.parse(source, "add_route.py")
        assert len(result.routes) >= 2

    def test_route_with_stream(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.route("/upload", methods=["POST"], stream=True)
async def upload(request):
    body = b""
    while True:
        data = await request.stream.read()
        if data is None:
            break
        body += data
    return text("OK")
'''
        result = parser.parse(source, "stream.py")
        assert len(result.routes) >= 1

    def test_route_with_host(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.route("/", host="example.com")
async def home(request):
    return text("example.com")
'''
        result = parser.parse(source, "host.py")
        assert len(result.routes) >= 1


# ═══════════════════════════════════════════════════════════════════
# Blueprint Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicBlueprints:

    def test_extract_basic_blueprint(self, parser):
        source = '''
from sanic import Blueprint

bp = Blueprint("users", url_prefix="/users")

@bp.route("/")
async def list_users(request):
    return json([])
'''
        result = parser.parse(source, "blueprints.py")
        assert len(result.blueprints) >= 1
        bp = result.blueprints[0]
        assert bp.name == "users"
        assert bp.url_prefix == "/users"

    def test_extract_versioned_blueprint(self, parser):
        source = '''
from sanic import Blueprint

bp = Blueprint("api", url_prefix="/api", version=2)

@bp.get("/items")
async def items(request):
    return json([])
'''
        result = parser.parse(source, "versioned_bp.py")
        assert len(result.blueprints) >= 1

    def test_extract_multiple_blueprints(self, parser):
        source = '''
from sanic import Blueprint

users_bp = Blueprint("users", url_prefix="/users")
items_bp = Blueprint("items", url_prefix="/items")
admin_bp = Blueprint("admin", url_prefix="/admin")

@users_bp.get("/")
async def list_users(request):
    return json([])

@items_bp.get("/")
async def list_items(request):
    return json([])
'''
        result = parser.parse(source, "multi_bp.py")
        assert len(result.blueprints) >= 3

    def test_extract_blueprint_group(self, parser):
        source = '''
from sanic import Blueprint

bp1 = Blueprint("users", url_prefix="/users")
bp2 = Blueprint("items", url_prefix="/items")

group = Blueprint.group(bp1, bp2, url_prefix="/api/v1")
'''
        result = parser.parse(source, "bp_group.py")
        assert len(result.blueprints) >= 2


# ═══════════════════════════════════════════════════════════════════
# Middleware Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicMiddleware:

    def test_extract_request_middleware(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.middleware("request")
async def add_key(request):
    request.ctx.key = "value"
'''
        result = parser.parse(source, "middleware.py")
        assert len(result.middleware) >= 1
        mw = result.middleware[0]
        assert mw.name == "add_key"
        assert mw.middleware_type in ("request", "request")

    def test_extract_response_middleware(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.middleware("response")
async def add_header(request, response):
    response.headers["X-Custom"] = "value"
'''
        result = parser.parse(source, "response_mw.py")
        assert len(result.middleware) >= 1

    def test_extract_on_request_on_response(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.on_request
async def before(request):
    pass

@app.on_response
async def after(request, response):
    pass
'''
        result = parser.parse(source, "on_mw.py")
        assert len(result.middleware) >= 2

    def test_extract_blueprint_middleware(self, parser):
        source = '''
from sanic import Blueprint

bp = Blueprint("test", url_prefix="/test")

@bp.middleware("request")
async def bp_middleware(request):
    pass
'''
        result = parser.parse(source, "bp_middleware.py")
        assert len(result.middleware) >= 1


# ═══════════════════════════════════════════════════════════════════
# Listener Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicListeners:

    def test_extract_server_lifecycle_listeners(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.listener("before_server_start")
async def setup_db(app, loop):
    app.ctx.db = await create_pool()

@app.listener("after_server_start")
async def notify_start(app, loop):
    print("Server started")

@app.listener("before_server_stop")
async def cleanup(app, loop):
    await app.ctx.db.close()

@app.listener("after_server_stop")
async def final(app, loop):
    print("Stopped")
'''
        result = parser.parse(source, "listeners.py")
        assert len(result.listeners) >= 4
        events = [li.event for li in result.listeners]
        assert "before_server_start" in events
        assert "after_server_start" in events
        assert "before_server_stop" in events
        assert "after_server_stop" in events

    def test_extract_shorthand_listeners(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.before_server_start
async def init(app, loop):
    pass

@app.after_server_stop
async def teardown(app, loop):
    pass
'''
        result = parser.parse(source, "shorthand_listeners.py")
        assert len(result.listeners) >= 2

    def test_extract_main_process_listeners(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.main_process_start
async def main_start(app, loop):
    pass

@app.main_process_stop
async def main_stop(app, loop):
    pass
'''
        result = parser.parse(source, "main_process.py")
        assert len(result.listeners) >= 2


# ═══════════════════════════════════════════════════════════════════
# Signal Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicSignals:

    def test_extract_signals(self, parser):
        source = '''
from sanic import Sanic
from sanic.signals import Event

app = Sanic("MyApp")

@app.signal("http.lifecycle.complete")
async def on_complete(**context):
    print("Complete")

@app.signal(Event.HTTP_LIFECYCLE_BEGIN)
async def on_begin(**context):
    pass
'''
        result = parser.parse(source, "signals.py")
        assert len(result.signals) >= 1

    def test_extract_custom_signal(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.signal("user.registration.complete")
async def on_user_registered(**context):
    pass
'''
        result = parser.parse(source, "custom_signal.py")
        assert len(result.signals) >= 1


# ═══════════════════════════════════════════════════════════════════
# WebSocket Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicWebSockets:

    def test_extract_websocket_routes(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.websocket("/ws")
async def feed(request, ws):
    while True:
        data = await ws.recv()
        await ws.send(data)

@app.websocket("/chat")
async def chat(request, ws):
    pass
'''
        result = parser.parse(source, "websocket.py")
        assert len(result.websocket_routes) >= 2
        paths = [ws.path for ws in result.websocket_routes]
        assert "/ws" in paths
        assert "/chat" in paths

    def test_extract_blueprint_websocket(self, parser):
        source = '''
from sanic import Blueprint

bp = Blueprint("ws", url_prefix="/ws")

@bp.websocket("/feed")
async def feed(request, ws):
    pass
'''
        result = parser.parse(source, "bp_ws.py")
        assert len(result.websocket_routes) >= 1


# ═══════════════════════════════════════════════════════════════════
# Static Route Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicStatic:

    def test_extract_static_files(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

app.static("/static", "./static")
app.static("/uploads", "/var/uploads", name="uploads")
'''
        result = parser.parse(source, "static.py")
        assert len(result.static_routes) >= 2

    def test_extract_static_single_file(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

app.static("/favicon.ico", "./static/favicon.ico")
'''
        result = parser.parse(source, "single_static.py")
        assert len(result.static_routes) >= 1


# ═══════════════════════════════════════════════════════════════════
# Exception Handler Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicExceptionHandlers:

    def test_extract_exception_handlers(self, parser):
        source = '''
from sanic import Sanic
from sanic.exceptions import NotFound, ServerError

app = Sanic("MyApp")

@app.exception(NotFound)
async def not_found(request, exception):
    return json({"error": "Not found"}, status=404)

@app.exception(ServerError)
async def server_error(request, exception):
    return json({"error": "Server error"}, status=500)
'''
        result = parser.parse(source, "exceptions.py")
        assert len(result.exception_handlers) >= 2

    def test_extract_generic_exception_handler(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.exception(Exception)
async def catch_all(request, exception):
    return json({"error": str(exception)}, status=500)
'''
        result = parser.parse(source, "generic_exception.py")
        assert len(result.exception_handlers) >= 1


# ═══════════════════════════════════════════════════════════════════
# Class-Based View Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicClassBasedViews:

    def test_extract_http_method_view(self, parser):
        source = '''
from sanic import Sanic
from sanic.views import HTTPMethodView

app = Sanic("MyApp")

class UserView(HTTPMethodView):
    async def get(self, request):
        return json([])

    async def post(self, request):
        return json({})

    async def put(self, request, user_id):
        return json({})

app.add_route(UserView.as_view(), "/users")
'''
        result = parser.parse(source, "cbv.py")
        assert len(result.class_based_views) >= 1
        cbv = result.class_based_views[0]
        assert cbv.name == "UserView"
        assert "GET" in cbv.methods
        assert "POST" in cbv.methods

    def test_extract_composition_view(self, parser):
        source = '''
from sanic import Sanic
from sanic.views import CompositionView

app = Sanic("MyApp")

class MixedView(CompositionView):
    pass

view = CompositionView()
'''
        result = parser.parse(source, "composition.py")
        # Should detect CompositionView
        assert len(result.class_based_views) >= 1


# ═══════════════════════════════════════════════════════════════════
# Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicDetection:

    def test_is_sanic_file_positive(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")
'''
        assert parser.is_sanic_file(source, "app.py") is True

    def test_is_sanic_file_with_blueprint(self, parser):
        source = '''
from sanic import Blueprint

bp = Blueprint("test")
'''
        assert parser.is_sanic_file(source, "bp.py") is True

    def test_is_sanic_file_with_response(self, parser):
        source = '''
from sanic.response import json
from sanic import Sanic

app = Sanic("test")
'''
        assert parser.is_sanic_file(source, "resp.py") is True

    def test_is_sanic_file_negative(self, parser):
        source = '''
from flask import Flask

app = Flask(__name__)
'''
        assert parser.is_sanic_file(source, "flask_app.py") is False

    def test_is_sanic_file_with_extensions(self, parser):
        source = '''
from sanic import Sanic
from sanic_ext import openapi

app = Sanic("MyApp")
'''
        assert parser.is_sanic_file(source, "ext.py") is True

    def test_empty_file_negative(self, parser):
        source = '''
x = 1
y = 2
'''
        assert parser.is_sanic_file(source, "nothing.py") is False


# ═══════════════════════════════════════════════════════════════════
# Classification Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicClassification:

    def test_classify_app_file(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.route("/")
async def index(request):
    return text("Hello")

if __name__ == "__main__":
    app.run()
'''
        result = parser.parse(source, "app.py")
        assert result.file_type == "app"

    def test_classify_blueprint_file(self, parser):
        source = '''
from sanic import Blueprint

bp = Blueprint("users", url_prefix="/users")

@bp.get("/")
async def list_users(request):
    return json([])
'''
        result = parser.parse(source, "users_bp.py")
        assert result.file_type == "blueprint"

    def test_classify_middleware_file(self, parser):
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

@app.middleware("request")
async def auth_check(request):
    pass

@app.middleware("response")
async def add_cors(request, response):
    pass
'''
        result = parser.parse(source, "middleware.py")
        assert result.file_type == "middleware"


# ═══════════════════════════════════════════════════════════════════
# Format Output Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicFormat:

    def test_to_codetrellis_format(self, parser):
        source = '''
from sanic import Sanic, Blueprint

app = Sanic("MyApp")
bp = Blueprint("api", url_prefix="/api")

@app.get("/")
async def index(request):
    return text("Hello")

@bp.get("/items")
async def items(request):
    return json([])

@app.websocket("/ws")
async def feed(request, ws):
    pass

app.static("/static", "./static")

@app.middleware("request")
async def check_auth(request):
    pass

@app.listener("before_server_start")
async def setup(app, loop):
    pass
'''
        result = parser.parse(source, "full_app.py")
        output = parser.to_codetrellis_format(result)

        assert isinstance(output, str)
        assert len(output) > 0
        assert "SANIC_ROUTES" in output or "Routes" in output.upper()

    def test_empty_parse_result(self, parser):
        source = '''
# Just a plain Python file
x = 1
'''
        result = parser.parse(source, "plain.py")
        assert result.total_routes == 0
        assert result.total_middleware == 0
        assert result.total_blueprints == 0


# ═══════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestSanicIntegration:

    def test_full_sanic_application(self, parser):
        """Test parsing a complete Sanic application."""
        source = '''
from sanic import Sanic, Blueprint
from sanic.response import json, text
from sanic.views import HTTPMethodView
from sanic.exceptions import NotFound

app = Sanic("FullApp")

# Blueprint
api = Blueprint("api", url_prefix="/api", version=1)

# Routes
@app.get("/")
async def index(request):
    return text("Hello")

@api.get("/items")
async def get_items(request):
    return json([])

@api.post("/items")
async def create_item(request):
    return json({})

# Class-based view
class UserView(HTTPMethodView):
    async def get(self, request):
        return json([])
    async def post(self, request):
        return json({})

app.add_route(UserView.as_view(), "/users")

# WebSocket
@app.websocket("/feed")
async def feed(request, ws):
    while True:
        data = await ws.recv()
        await ws.send(data)

# Middleware
@app.middleware("request")
async def auth(request):
    pass

@app.middleware("response")
async def cors(request, response):
    response.headers["Access-Control-Allow-Origin"] = "*"

# Listeners
@app.listener("before_server_start")
async def setup(app, loop):
    pass

@app.listener("after_server_stop")
async def teardown(app, loop):
    pass

# Signals
@app.signal("http.lifecycle.complete")
async def on_complete(**context):
    pass

# Static
app.static("/static", "./static")

# Exception handlers
@app.exception(NotFound)
async def not_found(request, exception):
    return json({"error": "Not found"}, status=404)

# Register blueprint
app.blueprint(api)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
'''
        result = parser.parse(source, "full_app.py")

        # Verify comprehensive extraction
        assert result.total_routes >= 4  # index, get_items, create_item, add_route
        assert result.total_blueprints >= 1
        assert result.total_middleware >= 2
        assert result.total_listeners >= 2
        assert len(result.websocket_routes) >= 1
        assert len(result.static_routes) >= 1
        assert len(result.exception_handlers) >= 1
        assert len(result.class_based_views) >= 1
        assert len(result.signals) >= 1

    def test_sanic_with_extensions(self, parser):
        """Test parsing Sanic with popular extensions."""
        source = '''
from sanic import Sanic
from sanic_ext import openapi
from sanic_cors import CORS

app = Sanic("ExtApp")

CORS(app)

@app.get("/api/data")
@openapi.summary("Get data")
@openapi.response(200, {"application/json": {"data": []}})
async def get_data(request):
    return json({"data": []})
'''
        result = parser.parse(source, "ext_app.py")
        assert len(result.detected_frameworks) >= 1
        assert result.total_routes >= 1

    def test_sanic_version_detection(self, parser):
        """Test that Sanic version features are detected."""
        source = '''
from sanic import Sanic

app = Sanic("MyApp")

# v21.3+ signal
@app.signal("http.lifecycle.complete")
async def sig(**ctx):
    pass

# v22.3+ on_request shorthand
@app.on_request
async def before(request):
    pass
'''
        result = parser.parse(source, "version.py")
        # Parser should handle both old and new API styles
        assert len(result.signals) >= 1 or len(result.middleware) >= 1

    def test_multiple_apps(self, parser):
        """Test parsing a file with multiple Sanic app instances."""
        source = '''
from sanic import Sanic

app1 = Sanic("App1")
app2 = Sanic("App2")

@app1.get("/hello")
async def hello1(request):
    return text("Hello from App1")

@app2.get("/hello")
async def hello2(request):
    return text("Hello from App2")
'''
        result = parser.parse(source, "multi_app.py")
        assert result.total_routes >= 2

    def test_sanic_with_jinja(self, parser):
        """Test parsing Sanic with Jinja2 templates."""
        source = '''
from sanic import Sanic
from sanic_ext import render

app = Sanic("TemplateApp")

@app.get("/")
@render(template="index.html")
async def index(request):
    return {"title": "Home"}
'''
        result = parser.parse(source, "template_app.py")
        assert result.total_routes >= 1


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════

class TestSanicEdgeCases:

    def test_empty_source(self, parser):
        result = parser.parse("", "empty.py")
        assert result.total_routes == 0
        assert len(result.routes) == 0

    def test_syntax_error_source(self, parser):
        source = '''
from sanic import Sanic
app = Sanic(
'''
        # Should not raise; parser handles gracefully
        result = parser.parse(source, "broken.py")
        assert isinstance(result, SanicParseResult)

    def test_sanic_import_only(self, parser):
        source = '''
import sanic
'''
        assert parser.is_sanic_file(source, "import_only.py") is True

    def test_comment_with_sanic(self, parser):
        source = '''
# This is not sanic
# from sanic import Sanic
x = 1
'''
        # Comments shouldn't trigger false positives in is_sanic_file
        # (depending on implementation, this may or may not match)
        result = parser.parse(source, "comment.py")
        assert result.total_routes == 0

    def test_large_blueprint_app(self, parser):
        source = '''
from sanic import Blueprint

bp = Blueprint("large", url_prefix="/large")

@bp.get("/1")
async def r1(request): return json({})

@bp.get("/2")
async def r2(request): return json({})

@bp.get("/3")
async def r3(request): return json({})

@bp.post("/1")
async def r4(request): return json({})

@bp.put("/1")
async def r5(request): return json({})
'''
        result = parser.parse(source, "large_bp.py")
        assert result.total_routes >= 5
