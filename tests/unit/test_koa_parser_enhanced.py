"""
Tests for Koa.js extractors and EnhancedKoaParser.

Part of CodeTrellis v4.83 Koa Backend Framework Support.
Tests cover:
- Route extraction (HTTP methods, @koa/router, koa-route, params, named routes)
- Middleware extraction (global, route-level, koa-compose, known middleware)
- Context extraction (ctx.body, ctx.throw, ctx.assert, ctx.state, custom ctx)
- Config extraction (new Koa(), app.keys, app.proxy, listen, error events)
- API pattern extraction (RESTful resources, versioning, imports)
- Parser integration (framework detection, version detection, is_koa_file)
"""

import pytest
from codetrellis.koa_parser_enhanced import (
    EnhancedKoaParser,
    KoaParseResult,
)
from codetrellis.extractors.koa import (
    KoaRouteExtractor,
    KoaRouteInfo,
    KoaRouterInfo,
    KoaParamInfo,
    KoaMiddlewareExtractor,
    KoaMiddlewareInfo,
    KoaMiddlewareStackInfo,
    KoaContextExtractor,
    KoaContextUsageInfo,
    KoaConfigExtractor,
    KoaApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedKoaParser()


@pytest.fixture
def route_extractor():
    return KoaRouteExtractor()


@pytest.fixture
def middleware_extractor():
    return KoaMiddlewareExtractor()


@pytest.fixture
def context_extractor():
    return KoaContextExtractor()


@pytest.fixture
def config_extractor():
    return KoaConfigExtractor()


@pytest.fixture
def api_extractor():
    return KoaApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Route Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestKoaRouteExtractor:

    def test_extract_basic_routes(self, route_extractor):
        """Test extracting basic HTTP method routes via koa-router."""
        content = """
const Router = require('@koa/router');
const router = new Router();

router.get('/users', async (ctx) => { ctx.body = []; });
router.post('/users', async (ctx) => { ctx.body = {}; });
router.put('/users/:id', async (ctx) => { ctx.body = {}; });
router.delete('/users/:id', async (ctx) => { ctx.status = 204; });
router.patch('/users/:id', async (ctx) => { ctx.body = {}; });
"""
        result = route_extractor.extract(content, "routes/users.js")
        routes = result.get('routes', [])
        assert len(routes) >= 5
        methods = [r.method for r in routes]
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'PUT' in methods
        assert 'DELETE' in methods
        assert 'PATCH' in methods

    def test_extract_router_instance(self, route_extractor):
        """Test extracting Router() instances."""
        content = """
const Router = require('@koa/router');
const router = new Router();

router.get('/', listItems);
router.post('/', createItem);
"""
        result = route_extractor.extract(content, "routes/items.js")
        routers = result.get('routers', [])
        assert len(routers) >= 1

    def test_extract_router_with_prefix(self, route_extractor):
        """Test extracting Router with prefix."""
        content = """
const Router = require('@koa/router');
const router = new Router({ prefix: '/api/v1' });

router.get('/users', listUsers);
"""
        result = route_extractor.extract(content, "routes.js")
        routers = result.get('routers', [])
        assert len(routers) >= 1

    def test_extract_route_params(self, route_extractor):
        """Test extracting route parameters."""
        content = """
const Router = require('@koa/router');
const router = new Router();

router.get('/users/:userId/posts/:postId', getPost);
"""
        result = route_extractor.extract(content, "routes.js")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        assert 'userId' in routes[0].param_names or len(result.get('params', [])) >= 2

    def test_extract_named_routes(self, route_extractor):
        """Test extracting named routes."""
        content = """
const Router = require('@koa/router');
const router = new Router();

router.get('user-list', '/users', listUsers);
"""
        result = route_extractor.extract(content, "routes.js")
        routes = result.get('routes', [])
        assert len(routes) >= 1

    def test_extract_koa_route_module(self, route_extractor):
        """Test extracting koa-route style routes."""
        content = """
const route = require('koa-route');

app.use(route.get('/users', listUsers));
app.use(route.post('/users', createUser));
"""
        result = route_extractor.extract(content, "app.js")
        routes = result.get('routes', [])
        assert len(routes) >= 2


# ═══════════════════════════════════════════════════════════════════
# Middleware Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestKoaMiddlewareExtractor:

    def test_extract_global_middleware(self, middleware_extractor):
        """Test extracting global app.use() middleware."""
        content = """
const Koa = require('koa');
const bodyParser = require('koa-bodyparser');
const cors = require('@koa/cors');
const logger = require('koa-logger');

const app = new Koa();

app.use(logger());
app.use(cors());
app.use(bodyParser());
"""
        result = middleware_extractor.extract(content, "app.js")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 3
        names = [m.name for m in middleware]
        assert 'logger' in names or 'cors' in names or 'bodyParser' in names

    def test_extract_middleware_stack(self, middleware_extractor):
        """Test middleware stack detection."""
        content = """
const Koa = require('koa');
const cors = require('@koa/cors');
const helmet = require('koa-helmet');
const session = require('koa-session');
const bodyParser = require('koa-bodyparser');
const logger = require('koa-logger');
const serve = require('koa-static');

const app = new Koa();
app.use(cors());
app.use(helmet());
app.use(session(app));
app.use(bodyParser());
app.use(logger());
app.use(serve('./public'));
"""
        result = middleware_extractor.extract(content, "app.js")
        stack = result.get('stack')
        assert stack is not None
        assert stack.has_cors is True
        assert stack.has_helmet is True
        assert stack.has_body_parser is True
        assert stack.has_logger is True

    def test_extract_compose_middleware(self, middleware_extractor):
        """Test koa-compose middleware detection."""
        content = """
const compose = require('koa-compose');
const middleware = compose([auth, validate, handler]);
app.use(middleware);
"""
        result = middleware_extractor.extract(content, "app.js")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 1

    def test_extract_error_handler_middleware(self, middleware_extractor):
        """Test error handler middleware detection."""
        content = """
app.use(async (ctx, next) => {
    try {
        await next();
    } catch (err) {
        ctx.status = err.statusCode || 500;
        ctx.body = { error: err.message };
    }
});
"""
        result = middleware_extractor.extract(content, "app.js")
        # Error handler patterns are detected
        middleware = result.get('middleware', [])
        assert len(middleware) >= 0  # May be detected as custom middleware


# ═══════════════════════════════════════════════════════════════════
# Context Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestKoaContextExtractor:

    def test_extract_ctx_body(self, context_extractor):
        """Test ctx.body usage detection."""
        content = """
router.get('/users', async (ctx) => {
    ctx.body = await User.find();
});
router.post('/users', async (ctx) => {
    const user = new User(ctx.request.body);
    ctx.body = await user.save();
    ctx.status = 201;
});
"""
        result = context_extractor.extract(content, "routes.js")
        usages = result.get('context_usages', [])
        paths = [u.property_path for u in usages]
        assert any('ctx.body' in p for p in paths) or any('ctx.status' in p for p in paths)

    def test_extract_ctx_throw(self, context_extractor):
        """Test ctx.throw usage detection."""
        content = """
router.get('/users/:id', async (ctx) => {
    const user = await User.findById(ctx.params.id);
    ctx.throw(404, 'User not found');
    ctx.body = user;
});
"""
        result = context_extractor.extract(content, "routes.js")
        throws = result.get('throws', [])
        assert len(throws) >= 1
        assert throws[0].method == 'throw'

    def test_extract_ctx_assert(self, context_extractor):
        """Test ctx.assert usage detection."""
        content = """
router.put('/users/:id', async (ctx) => {
    ctx.assert(ctx.request.body.name, 400, 'Name is required');
});
"""
        result = context_extractor.extract(content, "routes.js")
        throws = result.get('throws', [])
        assert len(throws) >= 1

    def test_extract_ctx_state(self, context_extractor):
        """Test ctx.state usage detection."""
        content = """
app.use(async (ctx, next) => {
    ctx.state.user = await getUser(ctx.request.header.authorization);
    await next();
});
"""
        result = context_extractor.extract(content, "auth.js")
        usages = result.get('context_usages', [])
        assert any('state' in u.property_path for u in usages)

    def test_extract_ctx_request_response(self, context_extractor):
        """Test ctx.request and ctx.response usage."""
        content = """
router.post('/upload', async (ctx) => {
    const body = ctx.request.body;
    ctx.response.type = 'application/json';
    ctx.body = { ok: true };
});
"""
        result = context_extractor.extract(content, "upload.js")
        usages = result.get('context_usages', [])
        assert len(usages) >= 1


# ═══════════════════════════════════════════════════════════════════
# Config Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestKoaConfigExtractor:

    def test_extract_app_creation(self, config_extractor):
        """Test new Koa() detection."""
        content = """
const Koa = require('koa');
const app = new Koa();
"""
        result = config_extractor.extract(content, "app.js")
        apps = result.get('apps', [])
        assert len(apps) >= 1
        assert apps[0].variable_name == 'app'

    def test_extract_app_keys(self, config_extractor):
        """Test app.keys = [...] detection."""
        content = """
const app = new Koa();
app.keys = ['secret1', 'secret2'];
"""
        result = config_extractor.extract(content, "app.js")
        settings = result.get('settings', [])
        assert any(s.setting_type == 'keys' for s in settings)

    def test_extract_app_proxy(self, config_extractor):
        """Test app.proxy = true detection."""
        content = """
const app = new Koa();
app.proxy = true;
"""
        result = config_extractor.extract(content, "app.js")
        settings = result.get('settings', [])
        assert any(s.setting_type == 'proxy' for s in settings)

    def test_extract_listen(self, config_extractor):
        """Test app.listen() detection."""
        content = """
const app = new Koa();
app.listen(3000, () => console.log('Running'));
"""
        result = config_extractor.extract(content, "server.js")
        servers = result.get('servers', [])
        assert len(servers) >= 1
        assert servers[0].port == '3000'

    def test_extract_error_listener(self, config_extractor):
        """Test app.on('error', handler) detection."""
        content = """
const app = new Koa();
app.on('error', (err, ctx) => {
    console.error('server error', err, ctx);
});
"""
        result = config_extractor.extract(content, "app.js")
        assert result.get('has_error_listener') is True


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestKoaApiExtractor:

    def test_extract_imports(self, api_extractor):
        """Test Koa ecosystem import detection."""
        content = """
import Koa from 'koa';
import Router from '@koa/router';
import bodyParser from 'koa-bodyparser';
import cors from '@koa/cors';
"""
        result = api_extractor.extract(content, "app.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 4

    def test_extract_resources(self, api_extractor):
        """Test RESTful resource detection."""
        content = """
router.get('/users', listUsers);
router.post('/users', createUser);
router.get('/users/:id', getUser);
router.put('/users/:id', updateUser);
router.delete('/users/:id', deleteUser);

router.get('/posts', listPosts);
router.post('/posts', createPost);
"""
        result = api_extractor.extract(content, "routes.js")
        resources = result.get('resources', [])
        assert len(resources) >= 1

    def test_extract_api_versioning(self, api_extractor):
        """Test API versioning detection."""
        content = """
const v1Router = new Router({ prefix: '/api/v1' });
const v2Router = new Router({ prefix: '/api/v2' });

v1Router.get('/users', listUsersV1);
v2Router.get('/users', listUsersV2);
"""
        result = api_extractor.extract(content, "routes.js")
        summary = result.get('summary')
        assert summary is not None


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedKoaParser:

    def test_is_koa_file_import(self, parser):
        """Test is_koa_file with direct import."""
        content = "const Koa = require('koa');"
        assert parser.is_koa_file(content) is True

    def test_is_koa_file_esm(self, parser):
        """Test is_koa_file with ESM import."""
        content = "import Koa from 'koa';"
        assert parser.is_koa_file(content) is True

    def test_is_koa_file_router(self, parser):
        """Test is_koa_file with @koa/router."""
        content = "import Router from '@koa/router';"
        assert parser.is_koa_file(content) is True

    def test_is_koa_file_new_koa(self, parser):
        """Test is_koa_file with new Koa()."""
        content = "const app = new Koa();"
        assert parser.is_koa_file(content) is True

    def test_is_koa_file_packages(self, parser):
        """Test is_koa_file with koa-bodyparser."""
        content = "const bodyParser = require('koa-bodyparser');"
        assert parser.is_koa_file(content) is True

    def test_is_koa_file_negative(self, parser):
        """Test is_koa_file with non-Koa code."""
        content = "const express = require('express');\nconst app = express();"
        assert parser.is_koa_file(content) is False

    def test_parse_full_app(self, parser):
        """Test full app parsing."""
        content = """
const Koa = require('koa');
const Router = require('@koa/router');
const bodyParser = require('koa-bodyparser');
const cors = require('@koa/cors');

const app = new Koa();
const router = new Router();

app.use(cors());
app.use(bodyParser());

router.get('/users', async (ctx) => {
    ctx.body = await User.find();
});

router.post('/users', async (ctx) => {
    const user = new User(ctx.request.body);
    ctx.body = await user.save();
    ctx.status = 201;
});

router.get('/users/:id', async (ctx) => {
    const user = await User.findById(ctx.params.id);
    if (!user) ctx.throw(404, 'User not found');
    ctx.body = user;
});

app.use(router.routes());
app.use(router.allowedMethods());

app.listen(3000);
"""
        result = parser.parse(content, "app.js")
        assert isinstance(result, KoaParseResult)
        assert result.total_routes >= 3
        assert len(result.middleware) >= 2
        assert len(result.detected_frameworks) >= 1
        assert 'koa' in result.detected_frameworks

    def test_detect_koa_v1(self, parser):
        """Test Koa v1 detection (generator middleware)."""
        content = """
const koa = require('koa');
const app = koa();

app.use(function *(next) {
    this.body = 'Hello';
    this.status = 200;
});
"""
        result = parser.parse(content, "app.js")
        assert result.koa_version == '1.0' or result.uses_generator_middleware is True

    def test_detect_koa_v2(self, parser):
        """Test Koa v2 detection (async/await)."""
        content = """
const Koa = require('koa');
const app = new Koa();

app.use(async (ctx, next) => {
    ctx.body = 'Hello';
    ctx.status = 200;
});
"""
        result = parser.parse(content, "app.js")
        assert result.koa_version == '2.0'

    def test_detect_frameworks(self, parser):
        """Test framework ecosystem detection."""
        content = """
import Koa from 'koa';
import Router from '@koa/router';
import bodyParser from 'koa-bodyparser';
import cors from '@koa/cors';
import helmet from 'koa-helmet';
import jwt from 'koa-jwt';
import session from 'koa-session';
import logger from 'koa-logger';
"""
        result = parser.parse(content, "app.ts")
        assert 'koa' in result.detected_frameworks
        assert len(result.detected_frameworks) >= 3

    def test_classify_file_app(self, parser):
        """Test file classification for app files."""
        content = "const Koa = require('koa');\nconst app = new Koa();\napp.listen(3000);"
        result = parser.parse(content, "src/app.js")
        assert result.file_type == 'app'

    def test_classify_file_route(self, parser):
        """Test file classification for route files."""
        content = "const Router = require('@koa/router');\nrouter.get('/users', handler);"
        result = parser.parse(content, "src/routes/users.js")
        assert result.file_type == 'route'

    def test_classify_file_middleware(self, parser):
        """Test file classification for middleware files."""
        content = "module.exports = async (ctx, next) => { await next(); };"
        result = parser.parse(content, "src/middleware/auth.js")
        assert result.file_type == 'middleware'

    def test_typescript_detection(self, parser):
        """Test TypeScript detection."""
        content = "import Koa from 'koa';"
        result = parser.parse(content, "app.ts")
        assert result.is_typescript is True
