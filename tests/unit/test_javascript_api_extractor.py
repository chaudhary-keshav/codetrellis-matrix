"""
Tests for JavaScriptAPIExtractor — route, middleware, WebSocket, GraphQL extraction.

Part of CodeTrellis v4.30 JavaScript Language Support.
"""

import pytest
from codetrellis.extractors.javascript.api_extractor import (
    JavaScriptAPIExtractor,
    JSRouteInfo,
    JSMiddlewareInfo,
    JSWebSocketInfo,
    JSGraphQLResolverInfo,
)


@pytest.fixture
def extractor():
    return JavaScriptAPIExtractor()


class TestExpressRoutes:
    """Tests for Express.js route extraction."""

    def test_basic_get_route(self, extractor):
        code = '''
const express = require('express');
const app = express();

app.get('/api/users', (req, res) => {
    res.json(users);
});
'''
        result = extractor.extract(code, "app.js")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        route = routes[0]
        assert route.method == "GET"
        assert route.path == "/api/users"

    def test_post_route(self, extractor):
        code = '''
app.post('/api/users', validateBody, (req, res) => {
    const user = createUser(req.body);
    res.status(201).json(user);
});
'''
        result = extractor.extract(code, "routes.js")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        assert routes[0].method == "POST"

    def test_router_routes(self, extractor):
        code = '''
const router = require('express').Router();

router.get('/', getAll);
router.get('/:id', getById);
router.post('/', create);
router.put('/:id', update);
router.delete('/:id', remove);
'''
        result = extractor.extract(code, "router.js")
        routes = result.get('routes', [])
        assert len(routes) >= 4

    def test_all_http_methods(self, extractor):
        code = '''
app.get('/get', handler);
app.post('/post', handler);
app.put('/put', handler);
app.delete('/delete', handler);
app.patch('/patch', handler);
'''
        result = extractor.extract(code, "methods.js")
        routes = result.get('routes', [])
        assert len(routes) >= 5


class TestFastifyRoutes:
    """Tests for Fastify route extraction."""

    def test_fastify_route(self, extractor):
        code = '''
const fastify = require('fastify')();

fastify.get('/api/items', async (request, reply) => {
    return { items: [] };
});
'''
        result = extractor.extract(code, "fastify.js")
        routes = result.get('routes', [])
        assert len(routes) >= 1


class TestMiddleware:
    """Tests for middleware extraction."""

    def test_app_use_middleware(self, extractor):
        code = '''
app.use(express.json());
app.use(cors());
app.use(helmet());
app.use('/api', authMiddleware);
'''
        result = extractor.extract(code, "middleware.js")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 1

    def test_error_middleware(self, extractor):
        code = '''
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Internal Server Error' });
});
'''
        result = extractor.extract(code, "error.js")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 1


class TestWebSocket:
    """Tests for WebSocket handler extraction."""

    def test_socketio_events(self, extractor):
        code = '''
const io = require('socket.io')(server);

io.on('connection', (socket) => {
    socket.on('message', (data) => {
        io.emit('broadcast', data);
    });

    socket.on('disconnect', () => {
        console.log('User disconnected');
    });
});
'''
        result = extractor.extract(code, "socket.js")
        websockets = result.get('websockets', [])
        assert len(websockets) >= 1

    def test_ws_handler(self, extractor):
        code = '''
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
    ws.on('message', (data) => {
        ws.send('received');
    });
});
'''
        result = extractor.extract(code, "ws.js")
        websockets = result.get('websockets', [])
        assert len(websockets) >= 1


class TestGraphQL:
    """Tests for GraphQL resolver extraction."""

    def test_graphql_resolvers(self, extractor):
        code = '''
const resolvers = {
    Query: {
        users: () => User.find(),
        user: (_, { id }) => User.findById(id),
    },
    Mutation: {
        createUser: (_, { input }) => User.create(input),
    },
};
'''
        result = extractor.extract(code, "resolvers.js")
        resolvers = result.get('graphql_resolvers', [])
        assert len(resolvers) >= 1
