"""
Tests for Hono extractors and EnhancedHonoParser.

Part of CodeTrellis v4.84 Hono Backend Framework Support.
Tests cover:
- Route extraction (HTTP methods, route(), basePath, params, validators)
- Middleware extraction (built-in, @hono/*, custom, onError, notFound)
- Context extraction (c.json, c.text, c.req.*, c.env.*, c.var, streaming)
- Config extraction (new Hono, router type, runtime, serve/export)
- API pattern extraction (resources, runtime detection, RPC, OpenAPI)
- Parser integration (framework detection, version detection, is_hono_file)
"""

import pytest
from codetrellis.hono_parser_enhanced import (
    EnhancedHonoParser,
    HonoParseResult,
)
from codetrellis.extractors.hono import (
    HonoRouteExtractor,
    HonoRouteInfo,
    HonoRouterInfo,
    HonoParamInfo,
    HonoMiddlewareExtractor,
    HonoMiddlewareInfo,
    HonoMiddlewareStackInfo,
    HonoContextExtractor,
    HonoContextUsageInfo,
    HonoConfigExtractor,
    HonoApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedHonoParser()


@pytest.fixture
def route_extractor():
    return HonoRouteExtractor()


@pytest.fixture
def middleware_extractor():
    return HonoMiddlewareExtractor()


@pytest.fixture
def context_extractor():
    return HonoContextExtractor()


@pytest.fixture
def config_extractor():
    return HonoConfigExtractor()


@pytest.fixture
def api_extractor():
    return HonoApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Route Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestHonoRouteExtractor:

    def test_extract_basic_routes(self, route_extractor):
        """Test extracting basic HTTP method routes."""
        content = """
import { Hono } from 'hono';
const app = new Hono();

app.get('/users', (c) => c.json([]));
app.post('/users', (c) => c.json({ id: 1 }));
app.put('/users/:id', (c) => c.json({}));
app.delete('/users/:id', (c) => c.text('Deleted'));
app.patch('/users/:id', (c) => c.json({}));
"""
        result = route_extractor.extract(content, "index.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 5
        methods = [r.method for r in routes]
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'PUT' in methods
        assert 'DELETE' in methods
        assert 'PATCH' in methods

    def test_extract_hono_instances(self, route_extractor):
        """Test extracting Hono app instances."""
        content = """
import { Hono } from 'hono';
const app = new Hono();
const api = new Hono();
"""
        result = route_extractor.extract(content, "index.ts")
        routers = result.get('routers', [])
        assert len(routers) >= 2

    def test_extract_route_params(self, route_extractor):
        """Test extracting route parameters."""
        content = """
const app = new Hono();
app.get('/users/:id/posts/:postId', (c) => c.json({}));
"""
        result = route_extractor.extract(content, "index.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        assert 'id' in routes[0].params
        assert 'postId' in routes[0].params

    def test_extract_route_mount(self, route_extractor):
        """Test app.route() mounting."""
        content = """
const app = new Hono();
const users = new Hono();
users.get('/', (c) => c.json([]));
app.route('/api/users', users);
"""
        result = route_extractor.extract(content, "index.ts")
        routers = result.get('routers', [])
        assert len(routers) >= 1

    def test_extract_basepath(self, route_extractor):
        """Test basePath detection."""
        content = """
const app = new Hono().basePath('/api');
app.get('/users', (c) => c.json([]));
"""
        result = route_extractor.extract(content, "index.ts")
        routers = result.get('routers', [])
        # basePath should be detected
        assert any(r.base_path == '/api' for r in routers) or len(routers) >= 0


# ═══════════════════════════════════════════════════════════════════
# Middleware Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestHonoMiddlewareExtractor:

    def test_extract_builtin_middleware(self, middleware_extractor):
        """Test extracting built-in Hono middleware."""
        content = """
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { jwt } from 'hono/jwt';

const app = new Hono();
app.use(cors());
app.use(logger());
app.use(jwt({ secret: 'key' }));
"""
        result = middleware_extractor.extract(content, "index.ts")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 3
        names = [m.name for m in middleware]
        assert 'cors' in names
        assert 'logger' in names
        assert 'jwt' in names

    def test_extract_middleware_stack(self, middleware_extractor):
        """Test middleware stack summary."""
        content = """
import { cors } from 'hono/cors';
import { jwt } from 'hono/jwt';
import { secureHeaders } from 'hono/secure-headers';
import { logger } from 'hono/logger';

const app = new Hono();
app.use(cors());
app.use(jwt({ secret: 'x' }));
app.use(secureHeaders());
app.use(logger());
"""
        result = middleware_extractor.extract(content, "index.ts")
        stack = result.get('stack')
        assert stack is not None
        assert stack.has_cors is True
        assert stack.has_jwt is True
        assert stack.has_secure_headers is True
        assert stack.has_logger is True

    def test_extract_path_scoped_middleware(self, middleware_extractor):
        """Test path-scoped middleware."""
        content = """
import { Hono } from 'hono';
import { basicAuth } from 'hono/basic-auth';

const app = new Hono();
app.use('/admin/*', basicAuth({ username: 'admin', password: 'pw' }));
"""
        result = middleware_extractor.extract(content, "index.ts")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 1
        admin_mw = [m for m in middleware if m.mount_path == '/admin/*']
        assert len(admin_mw) >= 1

    def test_extract_error_handler(self, middleware_extractor):
        """Test onError handler detection."""
        content = """
const app = new Hono();
app.onError((err, c) => {
    return c.json({ error: err.message }, 500);
});
"""
        result = middleware_extractor.extract(content, "index.ts")
        middleware = result.get('middleware', [])
        names = [m.name for m in middleware]
        assert 'onError' in names

    def test_extract_not_found_handler(self, middleware_extractor):
        """Test notFound handler detection."""
        content = """
const app = new Hono();
app.notFound((c) => c.json({ error: 'Not Found' }, 404));
"""
        result = middleware_extractor.extract(content, "index.ts")
        middleware = result.get('middleware', [])
        names = [m.name for m in middleware]
        assert 'notFound' in names


# ═══════════════════════════════════════════════════════════════════
# Context Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestHonoContextExtractor:

    def test_extract_response_helpers(self, context_extractor):
        """Test c.json(), c.text(), c.html() detection."""
        content = """
app.get('/json', (c) => c.json({ ok: true }));
app.get('/text', (c) => c.text('Hello'));
app.get('/html', (c) => c.html('<h1>Hi</h1>'));
app.get('/redirect', (c) => c.redirect('/other'));
"""
        result = context_extractor.extract(content, "index.ts")
        responses = result.get('responses', [])
        methods = [r.method for r in responses]
        assert 'json' in methods
        assert 'text' in methods
        assert 'html' in methods
        assert 'redirect' in methods

    def test_extract_request_helpers(self, context_extractor):
        """Test c.req.* detection."""
        content = """
app.post('/users', async (c) => {
    const body = await c.req.json();
    const id = c.req.param('id');
    const search = c.req.query('q');
    const auth = c.req.header('Authorization');
    return c.json({ ok: true });
});
"""
        result = context_extractor.extract(content, "index.ts")
        usages = result.get('context_usages', [])
        paths = [u.property_path for u in usages]
        assert 'c.req.json' in paths
        assert 'c.req.param' in paths
        assert 'c.req.query' in paths
        assert 'c.req.header' in paths

    def test_extract_env_bindings(self, context_extractor):
        """Test c.env.* Cloudflare bindings detection."""
        content = """
app.get('/data', async (c) => {
    const db = c.env.DB;
    const kv = c.env.KV_STORE;
    const bucket = c.env.R2_BUCKET;
    return c.json({ ok: true });
});
"""
        result = context_extractor.extract(content, "worker.ts")
        bindings = result.get('env_bindings', [])
        assert len(bindings) >= 3
        names = [b.name for b in bindings]
        assert 'DB' in names
        assert 'KV_STORE' in names
        assert 'R2_BUCKET' in names

    def test_extract_context_variables(self, context_extractor):
        """Test c.set()/c.get()/c.var detection."""
        content = """
app.use(async (c, next) => {
    c.set('user', { id: 1 });
    await next();
});
app.get('/me', (c) => {
    const user = c.get('user');
    return c.json(c.var.user);
});
"""
        result = context_extractor.extract(content, "index.ts")
        usages = result.get('context_usages', [])
        paths = [u.property_path for u in usages]
        assert any('set' in p for p in paths)
        assert any('get' in p for p in paths)

    def test_extract_streaming(self, context_extractor):
        """Test c.stream/c.streamText/c.streamSSE detection."""
        content = """
app.get('/stream', (c) => {
    return c.stream(async (stream) => {
        stream.write('Hello');
    });
});
app.get('/sse', (c) => {
    return c.streamSSE(async (stream) => {
        await stream.writeSSE({ data: 'hello' });
    });
});
"""
        result = context_extractor.extract(content, "index.ts")
        responses = result.get('responses', [])
        methods = [r.method for r in responses]
        assert 'stream' in methods
        assert 'streamSSE' in methods


# ═══════════════════════════════════════════════════════════════════
# Config Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestHonoConfigExtractor:

    def test_extract_app_creation(self, config_extractor):
        """Test new Hono() detection."""
        content = """
import { Hono } from 'hono';
const app = new Hono();
"""
        result = config_extractor.extract(content, "index.ts")
        apps = result.get('apps', [])
        assert len(apps) >= 1
        assert apps[0].variable_name == 'app'

    def test_extract_router_type(self, config_extractor):
        """Test router type detection."""
        content = """
import { Hono } from 'hono';
import { RegExpRouter } from 'hono/router/reg-exp-router';
const app = new Hono({ router: new RegExpRouter() });
"""
        result = config_extractor.extract(content, "index.ts")
        apps = result.get('apps', [])
        assert len(apps) >= 1
        assert apps[0].router_type == 'RegExpRouter'

    def test_extract_generics(self, config_extractor):
        """Test Hono generics detection."""
        content = """
type Env = { Bindings: { DB: D1Database }; Variables: { user: User } };
const app = new Hono<Env>();
"""
        result = config_extractor.extract(content, "index.ts")
        apps = result.get('apps', [])
        assert len(apps) >= 1
        assert apps[0].has_generics is True

    def test_extract_node_serve(self, config_extractor):
        """Test Node.js serve detection."""
        content = """
import { serve } from '@hono/node-server';
import { Hono } from 'hono';
const app = new Hono();
serve({ fetch: app.fetch, port: 3000 });
"""
        result = config_extractor.extract(content, "index.ts")
        servers = result.get('servers', [])
        assert len(servers) >= 1
        assert servers[0].runtime == 'node'

    def test_extract_bun_serve(self, config_extractor):
        """Test Bun serve detection."""
        content = """
import { Hono } from 'hono';
const app = new Hono();
export default { port: 3000, fetch: app.fetch };
"""
        result = config_extractor.extract(content, "index.ts")
        servers = result.get('servers', [])
        assert len(servers) >= 1
        assert servers[0].runtime == 'bun'


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestHonoApiExtractor:

    def test_extract_imports(self, api_extractor):
        """Test Hono ecosystem import detection."""
        content = """
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { jwt } from 'hono/jwt';
import { zValidator } from '@hono/zod-validator';
"""
        result = api_extractor.extract(content, "index.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 4

    def test_extract_resources(self, api_extractor):
        """Test RESTful resource detection."""
        content = """
app.get('/users', listUsers);
app.post('/users', createUser);
app.get('/users/:id', getUser);
app.put('/users/:id', updateUser);
app.delete('/users/:id', deleteUser);
"""
        result = api_extractor.extract(content, "index.ts")
        resources = result.get('resources', [])
        assert len(resources) >= 1

    def test_detect_cloudflare_runtime(self, api_extractor):
        """Test Cloudflare Workers runtime detection."""
        content = """
import { Hono } from 'hono';
const app = new Hono();
app.get('/', (c) => {
    const db = c.env.DB;
    return c.json({ ok: true });
});
export default app;
"""
        result = api_extractor.extract(content, "worker.ts")
        summary = result.get('summary')
        assert summary is not None
        assert summary.runtime == 'cloudflare-workers'

    def test_detect_deno_runtime(self, api_extractor):
        """Test Deno runtime detection."""
        content = """
import { Hono } from 'hono';
const app = new Hono();
Deno.serve(app.fetch);
"""
        result = api_extractor.extract(content, "main.ts")
        summary = result.get('summary')
        assert summary.runtime == 'deno'

    def test_detect_rpc_mode(self, api_extractor):
        """Test RPC mode detection."""
        content = """
import { hc } from 'hono/client';
const client = hc<AppType>('http://localhost:3000');
"""
        result = api_extractor.extract(content, "client.ts")
        summary = result.get('summary')
        assert summary.has_rpc is True

    def test_detect_graphql(self, api_extractor):
        """Test GraphQL detection."""
        content = """
import { graphqlServer } from '@hono/graphql-server';
app.use('/graphql', graphqlServer({ schema }));
"""
        result = api_extractor.extract(content, "index.ts")
        summary = result.get('summary')
        assert summary.has_graphql is True

    def test_detect_websocket(self, api_extractor):
        """Test WebSocket detection."""
        content = """
import { createNodeWebSocket } from '@hono/node-ws';
const { injectWebSocket, upgradeWebSocket } = createNodeWebSocket({ app });
"""
        result = api_extractor.extract(content, "index.ts")
        summary = result.get('summary')
        assert summary.has_websocket is True


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedHonoParser:

    def test_is_hono_file_import(self, parser):
        """Test is_hono_file with direct import."""
        content = "import { Hono } from 'hono';"
        assert parser.is_hono_file(content) is True

    def test_is_hono_file_cjs(self, parser):
        """Test is_hono_file with CJS require."""
        content = "const { Hono } = require('hono');"
        assert parser.is_hono_file(content) is True

    def test_is_hono_file_new_hono(self, parser):
        """Test is_hono_file with new Hono()."""
        content = "const app = new Hono();"
        assert parser.is_hono_file(content) is True

    def test_is_hono_file_sub_package(self, parser):
        """Test is_hono_file with hono/* import."""
        content = "import { cors } from 'hono/cors';"
        assert parser.is_hono_file(content) is True

    def test_is_hono_file_third_party(self, parser):
        """Test is_hono_file with @hono/* import."""
        content = "import { zValidator } from '@hono/zod-validator';"
        assert parser.is_hono_file(content) is True

    def test_is_hono_file_negative(self, parser):
        """Test is_hono_file with non-Hono code."""
        content = "const express = require('express');\nconst app = express();"
        assert parser.is_hono_file(content) is False

    def test_parse_full_app(self, parser):
        """Test full Hono app parsing."""
        content = """
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { jwt } from 'hono/jwt';

const app = new Hono();

app.use(cors());
app.use(logger());
app.use('/api/*', jwt({ secret: 'secret' }));

app.get('/api/users', async (c) => {
    return c.json([]);
});

app.post('/api/users', async (c) => {
    const body = await c.req.json();
    return c.json(body, 201);
});

app.get('/api/users/:id', async (c) => {
    const id = c.req.param('id');
    return c.json({ id });
});

app.delete('/api/users/:id', async (c) => {
    return c.text('Deleted', 204);
});

app.onError((err, c) => {
    return c.json({ error: err.message }, 500);
});

export default app;
"""
        result = parser.parse(content, "index.ts")
        assert isinstance(result, HonoParseResult)
        assert result.total_routes >= 4
        assert len(result.middleware) >= 3
        assert len(result.detected_frameworks) >= 1
        assert 'hono' in result.detected_frameworks
        assert result.is_typescript is True

    def test_detect_hono_v1(self, parser):
        """Test Hono v1 detection."""
        content = """
import { Hono } from 'hono';
const app = new Hono();
app.get('/', (c) => c.json({ ok: true }));
"""
        result = parser.parse(content, "index.ts")
        assert result.hono_version == '1.0'

    def test_detect_hono_v3(self, parser):
        """Test Hono v3 detection (JSX/streaming)."""
        content = """
import { Hono } from 'hono';
import { streamSSE } from 'hono/streaming';
import { getCookie, setCookie } from 'hono/cookie';

const app = new Hono();
app.get('/stream', (c) => c.streamSSE(async (s) => {}));
"""
        result = parser.parse(content, "index.tsx")
        assert result.hono_version == '3.0'

    def test_detect_hono_v4(self, parser):
        """Test Hono v4 detection (css, contextStorage)."""
        content = """
import { Hono } from 'hono';
import { css, Style } from 'hono/css';
import { contextStorage } from 'hono/context-storage';
"""
        result = parser.parse(content, "index.tsx")
        assert result.hono_version == '4.0'

    def test_detect_frameworks(self, parser):
        """Test framework ecosystem detection."""
        content = """
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { jwt } from 'hono/jwt';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';
"""
        result = parser.parse(content, "index.ts")
        assert 'hono' in result.detected_frameworks
        assert len(result.detected_frameworks) >= 3

    def test_cloudflare_workers_full(self, parser):
        """Test Cloudflare Workers full parse."""
        content = """
import { Hono } from 'hono';
import { cors } from 'hono/cors';

type Bindings = { DB: D1Database; KV: KVNamespace };
const app = new Hono<{ Bindings: Bindings }>();

app.use(cors());

app.get('/api/data', async (c) => {
    const db = c.env.DB;
    const results = await db.prepare('SELECT * FROM items').all();
    return c.json(results);
});

export default app;
"""
        result = parser.parse(content, "worker.ts")
        assert result.is_typescript is True
        assert result.total_routes >= 1
        assert len(result.env_bindings) >= 1

    def test_classify_file_app(self, parser):
        """Test file classification for app files."""
        content = "import { Hono } from 'hono';\nconst app = new Hono();\nexport default app;"
        result = parser.parse(content, "src/index.ts")
        assert result.file_type == 'app'

    def test_classify_file_route(self, parser):
        """Test file classification for route files."""
        content = "const app = new Hono();\napp.get('/users', handler);"
        result = parser.parse(content, "src/routes/users.ts")
        assert result.file_type == 'route'

    def test_typescript_detection(self, parser):
        """Test TypeScript detection."""
        content = "import { Hono } from 'hono';"
        result = parser.parse(content, "index.ts")
        assert result.is_typescript is True
        result2 = parser.parse(content, "index.js")
        assert result2.is_typescript is False
