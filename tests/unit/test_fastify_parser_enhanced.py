"""
Tests for Fastify extractors and EnhancedFastifyParser.

Part of CodeTrellis v4.81 Fastify Per-File Framework Support.
Tests cover:
- Route extraction (fastify.get/post, full route declarations, shorthand)
- Plugin extraction (fastify-plugin, fp, autoload, register)
- Hook extraction (onRequest, preHandler, onSend, lifecycle hooks)
- Schema extraction (JSON Schema, $ref, fluent-json-schema, type providers)
- API extraction (RESTful resources, serializers)
- Parser integration (framework detection, version detection, is_fastify_file)
"""

import pytest
from codetrellis.fastify_parser_enhanced import (
    EnhancedFastifyParser,
    FastifyParseResult,
)
from codetrellis.extractors.fastify import (
    FastifyRouteExtractor,
    FastifyRouteInfo,
    FastifyRouteOptionsInfo,
    FastifyPluginExtractor,
    FastifyPluginInfo,
    FastifyPluginRegistrationInfo,
    FastifyDecoratorInfo,
    FastifyHookExtractor,
    FastifyHookInfo,
    FastifyHookSummary,
    FastifySchemaExtractor,
    FastifySchemaInfo,
    FastifyTypeProviderInfo,
    FastifyApiExtractor,
    FastifyResourceInfo,
    FastifySerializerInfo,
    FastifyApiSummary,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedFastifyParser()


@pytest.fixture
def route_extractor():
    return FastifyRouteExtractor()


@pytest.fixture
def plugin_extractor():
    return FastifyPluginExtractor()


@pytest.fixture
def hook_extractor():
    return FastifyHookExtractor()


@pytest.fixture
def schema_extractor():
    return FastifySchemaExtractor()


@pytest.fixture
def api_extractor():
    return FastifyApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Route Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestFastifyRouteExtractor:

    def test_extract_shorthand_routes(self, route_extractor):
        """Test extracting shorthand route methods."""
        content = """
import Fastify from 'fastify';

const fastify = Fastify({ logger: true });

fastify.get('/users', async (request, reply) => {
    return { users: [] };
});

fastify.post('/users', async (request, reply) => {
    const user = request.body;
    return { id: 1, ...user };
});

fastify.delete('/users/:id', async (request, reply) => {
    const { id } = request.params;
    return { deleted: id };
});
"""
        result = route_extractor.extract(content, "server.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 3

    def test_extract_full_route_declaration(self, route_extractor):
        """Test extracting full route() declarations."""
        content = """
fastify.route({
    method: 'GET',
    url: '/api/items',
    schema: {
        response: {
            200: { type: 'array' }
        }
    },
    handler: async (request, reply) => {
        return [];
    }
});

fastify.route({
    method: 'POST',
    url: '/api/items',
    preHandler: [authenticate],
    handler: createItem
});
"""
        result = route_extractor.extract(content, "routes.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 2

    def test_extract_parameterized_routes(self, route_extractor):
        """Test routes with parameters."""
        content = """
fastify.get('/users/:userId/posts/:postId', async (request, reply) => {
    const { userId, postId } = request.params;
    return { userId, postId };
});
"""
        result = route_extractor.extract(content, "routes.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 1


# ═══════════════════════════════════════════════════════════════════
# Plugin Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestFastifyPluginExtractor:

    def test_extract_plugin_definition(self, plugin_extractor):
        """Test extracting fastify-plugin wrapped plugins."""
        content = """
import fp from 'fastify-plugin';

async function myPlugin(fastify, options) {
    fastify.decorate('utility', { hello: 'world' });
}

export default fp(myPlugin, {
    name: 'my-plugin',
    fastify: '4.x',
});
"""
        result = plugin_extractor.extract(content, "my-plugin.ts")
        plugins = result.get('plugins', [])
        assert len(plugins) >= 1

    def test_extract_plugin_registration(self, plugin_extractor):
        """Test extracting fastify.register() calls."""
        content = """
import cors from '@fastify/cors';
import swagger from '@fastify/swagger';
import rateLimit from '@fastify/rate-limit';
import autoload from '@fastify/autoload';

fastify.register(cors, { origin: true });
fastify.register(swagger, { routePrefix: '/docs' });
fastify.register(rateLimit, { max: 100, timeWindow: '1 minute' });
fastify.register(autoload, {
    dir: path.join(__dirname, 'plugins'),
    options: { prefix: '/api' }
});
"""
        result = plugin_extractor.extract(content, "app.ts")
        registrations = result.get('registrations', [])
        assert len(registrations) >= 4

    def test_extract_decorators(self, plugin_extractor):
        """Test extracting fastify.decorate()."""
        content = """
fastify.decorate('authenticate', async (request, reply) => {
    const token = request.headers.authorization;
    if (!token) throw new Error('Unauthorized');
});

fastify.decorateRequest('user', null);
fastify.decorateReply('sendSuccess', function(data) {
    return this.send({ success: true, data });
});
"""
        result = plugin_extractor.extract(content, "decorators.ts")
        decorators = result.get('decorators', [])
        assert len(decorators) >= 3


# ═══════════════════════════════════════════════════════════════════
# Hook Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestFastifyHookExtractor:

    def test_extract_lifecycle_hooks(self, hook_extractor):
        """Test extracting lifecycle hooks."""
        content = """
fastify.addHook('onRequest', async (request, reply) => {
    request.startTime = Date.now();
});

fastify.addHook('preHandler', async (request, reply) => {
    if (!request.headers.authorization) {
        reply.code(401).send({ error: 'Unauthorized' });
    }
});

fastify.addHook('onSend', async (request, reply, payload) => {
    const duration = Date.now() - request.startTime;
    reply.header('X-Response-Time', duration);
    return payload;
});

fastify.addHook('onClose', async (instance) => {
    await instance.db.close();
});
"""
        result = hook_extractor.extract(content, "hooks.ts")
        hooks = result.get('hooks', [])
        assert len(hooks) >= 4

    def test_extract_hook_summary(self, hook_extractor):
        """Test hook summary generation."""
        content = """
fastify.addHook('onRequest', authHook);
fastify.addHook('preHandler', validateHook);
fastify.addHook('onError', errorHook);
"""
        result = hook_extractor.extract(content, "hooks.ts")
        hooks = result.get('hooks', [])
        assert len(hooks) >= 3


# ═══════════════════════════════════════════════════════════════════
# Schema Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestFastifySchemaExtractor:

    def test_extract_json_schemas(self, schema_extractor):
        """Test extracting JSON Schema definitions via addSchema()."""
        content = """
fastify.addSchema({
    $id: 'user',
    type: 'object',
    properties: {
        id: { type: 'integer' },
        name: { type: 'string' },
        email: { type: 'string', format: 'email' },
    },
    required: ['name', 'email'],
});

fastify.addSchema({
    $id: 'address',
    type: 'object',
    properties: {
        street: { type: 'string' },
        city: { type: 'string' },
    },
});
"""
        result = schema_extractor.extract(content, "schemas.ts")
        schemas = result.get('schemas', [])
        assert len(schemas) >= 2

    def test_extract_type_provider(self, schema_extractor):
        """Test extracting type provider usage."""
        content = """
import Fastify from 'fastify';
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox';

const app = Fastify().withTypeProvider<TypeBoxTypeProvider>();
"""
        result = schema_extractor.extract(content, "app.ts")
        type_providers = result.get('type_providers', [])
        assert len(type_providers) >= 1


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestFastifyApiExtractor:

    def test_extract_restful_resource(self, api_extractor):
        """Test extracting RESTful resource patterns."""
        content = """
fastify.get('/api/products', listProducts);
fastify.get('/api/products/:id', getProduct);
fastify.post('/api/products', createProduct);
fastify.put('/api/products/:id', updateProduct);
fastify.delete('/api/products/:id', deleteProduct);
"""
        result = api_extractor.extract(content, "products.ts")
        resources = result.get('resources', [])
        assert len(resources) >= 1

    def test_extract_serializers(self, api_extractor):
        """Test extracting serializer patterns."""
        content = """
fastify.setSerializerCompiler(({ schema }) => {
    return data => JSON.stringify(data);
});

fastify.get('/users', {
    schema: {
        response: {
            200: userResponseSchema
        }
    },
    handler: listUsers,
});
"""
        result = api_extractor.extract(content, "api.ts")
        serializers = result.get('serializers', [])
        assert len(serializers) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedFastifyParser:

    def test_is_fastify_file(self, parser):
        """Test Fastify file detection."""
        content = """
import Fastify from 'fastify';

const app = Fastify({ logger: true });

app.get('/', async () => ({ hello: 'world' }));
app.listen({ port: 3000 });
"""
        assert parser.is_fastify_file(content, "server.ts") is True

    def test_is_not_fastify_file(self, parser):
        """Test non-Fastify file detection."""
        content = """
import React from 'react';
const App = () => <div>Hello</div>;
export default App;
"""
        assert parser.is_fastify_file(content, "App.tsx") is False

    def test_parse_full_fastify_app(self, parser):
        """Test parsing a complete Fastify app."""
        content = """
import Fastify from 'fastify';
import cors from '@fastify/cors';
import swagger from '@fastify/swagger';

const fastify = Fastify({ logger: true });

fastify.register(cors, { origin: true });
fastify.register(swagger);

fastify.addHook('onRequest', async (request, reply) => {
    request.startTime = Date.now();
});

fastify.get('/api/users', async (request, reply) => {
    return { users: [] };
});

fastify.post('/api/users', {
    schema: {
        body: {
            type: 'object',
            properties: {
                name: { type: 'string' },
            },
            required: ['name'],
        },
    },
    handler: async (request, reply) => {
        return { id: 1, name: request.body.name };
    },
});

fastify.listen({ port: 3000 });
"""
        result = parser.parse(content, "server.ts")
        assert isinstance(result, FastifyParseResult)
        assert len(result.routes) >= 2
        assert len(result.detected_frameworks) >= 1

    def test_parse_fastify_plugin_file(self, parser):
        """Test parsing a Fastify plugin file."""
        content = """
import fp from 'fastify-plugin';

async function dbPlugin(fastify, options) {
    const db = await connectToDatabase(options.connectionString);
    fastify.decorate('db', db);

    fastify.addHook('onClose', async (instance) => {
        await instance.db.close();
    });
}

export default fp(dbPlugin, {
    name: 'db-plugin',
    fastify: '4.x',
});
"""
        result = parser.parse(content, "db-plugin.ts")
        assert isinstance(result, FastifyParseResult)
        assert len(result.plugins) >= 1

    def test_parse_fastify_route_module(self, parser):
        """Test parsing a Fastify route module."""
        content = """
import { FastifyPluginAsync } from 'fastify';

const userRoutes: FastifyPluginAsync = async (fastify, opts) => {
    fastify.get('/', async (request, reply) => {
        return fastify.db.query('SELECT * FROM users');
    });

    fastify.get('/:id', async (request, reply) => {
        const { id } = request.params as { id: string };
        return fastify.db.query('SELECT * FROM users WHERE id = $1', [id]);
    });

    fastify.post('/', async (request, reply) => {
        const user = request.body;
        return fastify.db.insert('users', user);
    });
};

export default userRoutes;
"""
        result = parser.parse(content, "users.routes.ts")
        assert isinstance(result, FastifyParseResult)
        assert len(result.routes) >= 3

    def test_detect_fastify_ecosystem(self, parser):
        """Test Fastify ecosystem/version detection."""
        content = """
import Fastify from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import rateLimit from '@fastify/rate-limit';
import swagger from '@fastify/swagger';
import swaggerUI from '@fastify/swagger-ui';
import websocket from '@fastify/websocket';

const app = Fastify();
app.register(cors);
app.register(helmet);
app.register(rateLimit);
app.register(swagger);
app.register(swaggerUI);
app.register(websocket);
"""
        result = parser.parse(content, "app.ts")
        assert isinstance(result, FastifyParseResult)
        assert len(result.detected_frameworks) >= 1

    def test_parse_empty_file(self, parser):
        """Test parsing an empty file."""
        result = parser.parse("", "empty.ts")
        assert isinstance(result, FastifyParseResult)
        assert len(result.routes) == 0
        assert len(result.plugins) == 0

    def test_parse_typescript_fastify(self, parser):
        """Test parsing a TypeScript Fastify file with type providers."""
        content = """
import Fastify from 'fastify';
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox';
import { Type, Static } from '@sinclair/typebox';

const app = Fastify().withTypeProvider<TypeBoxTypeProvider>();

const UserSchema = Type.Object({
    name: Type.String(),
    email: Type.String({ format: 'email' }),
});

type UserType = Static<typeof UserSchema>;

app.post<{ Body: UserType }>('/users', {
    schema: { body: UserSchema },
    handler: async (request, reply) => {
        const { name, email } = request.body;
        return { name, email };
    },
});
"""
        result = parser.parse(content, "typed-server.ts")
        assert isinstance(result, FastifyParseResult)
        assert result.is_typescript is True
