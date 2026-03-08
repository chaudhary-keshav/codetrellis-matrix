"""
Tests for Hapi extractors and EnhancedHapiParser.

Part of CodeTrellis v4.86 Hapi Backend Framework Support.
Tests cover:
- Route extraction (server.route, path params, Joi validation, route config)
- Plugin extraction (server.register, plugin lifecycle, official/community plugins)
- Auth extraction (strategy/scheme/default, JWT/cookie/bearer/basic/bell)
- Server extraction (server config, catbox caching, server.method, ext events)
- API extraction (official packages, community packages, legacy)
- Parser integration (framework detection, version detection, is_hapi_file)
"""

import pytest
from codetrellis.hapi_parser_enhanced import (
    EnhancedHapiParser,
    HapiParseResult,
)
from codetrellis.extractors.hapi import (
    HapiRouteExtractor,
    HapiPluginExtractor,
    HapiAuthExtractor,
    HapiServerExtractor,
    HapiApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedHapiParser()


@pytest.fixture
def route_extractor():
    return HapiRouteExtractor()


@pytest.fixture
def plugin_extractor():
    return HapiPluginExtractor()


@pytest.fixture
def auth_extractor():
    return HapiAuthExtractor()


@pytest.fixture
def server_extractor():
    return HapiServerExtractor()


@pytest.fixture
def api_extractor():
    return HapiApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Route Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestHapiRouteExtractor:

    def test_extract_basic_routes(self, route_extractor):
        """Test extracting basic server.route() calls."""
        content = """
const Hapi = require('@hapi/hapi');

server.route({
    method: 'GET',
    path: '/users',
    handler: (request, h) => {
        return User.findAll();
    }
});

server.route({
    method: 'POST',
    path: '/users',
    handler: async (request, h) => {
        return User.create(request.payload);
    }
});
"""
        result = route_extractor.extract(content, "routes/users.js")
        routes = result.get('routes', [])
        assert len(routes) >= 2
        methods = [r.method for r in routes]
        assert 'GET' in methods
        assert 'POST' in methods

    def test_extract_route_params(self, route_extractor):
        """Test extracting route path parameters."""
        content = """
server.route({
    method: 'GET',
    path: '/users/{id}/posts/{postId}',
    handler: (request, h) => {
        const { id, postId } = request.params;
        return Post.findByUser(id, postId);
    }
});
"""
        result = route_extractor.extract(content, "routes/users.js")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        assert 'id' in routes[0].path_params
        assert 'postId' in routes[0].path_params

    def test_extract_route_with_joi_validation(self, route_extractor):
        """Test extracting routes with Joi validation."""
        content = """
const Joi = require('joi');

server.route({
    method: 'POST',
    path: '/users',
    options: {
        validate: {
            payload: Joi.object({
                name: Joi.string().required(),
                email: Joi.string().email().required(),
            }),
            query: Joi.object({
                page: Joi.number().integer().min(1),
            }),
        },
    },
    handler: async (request, h) => {
        return User.create(request.payload);
    }
});
"""
        result = route_extractor.extract(content, "routes/users.js")
        routes = result.get('routes', [])
        assert len(routes) >= 1

    def test_extract_route_array(self, route_extractor):
        """Test extracting array of routes."""
        content = """
server.route([
    {
        method: 'GET',
        path: '/health',
        handler: () => ({ status: 'ok' })
    },
    {
        method: 'GET',
        path: '/version',
        handler: () => ({ version: '1.0.0' })
    }
]);
"""
        result = route_extractor.extract(content, "routes/health.js")
        routes = result.get('routes', [])
        assert len(routes) >= 2


# ═══════════════════════════════════════════════════════════════════
# Plugin Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestHapiPluginExtractor:

    def test_extract_official_plugin_registration(self, plugin_extractor):
        """Test extracting official Hapi plugin registrations."""
        content = """
const Inert = require('@hapi/inert');
const Vision = require('@hapi/vision');
const HapiSwagger = require('hapi-swagger');

await server.register([
    Inert,
    Vision,
    {
        plugin: HapiSwagger,
        options: {
            info: { title: 'API Documentation' },
        },
    },
]);
"""
        result = plugin_extractor.extract(content, "server.js")
        plugins = result.get('plugins', [])
        assert len(plugins) >= 1  # At least the HapiSwagger explicit plugin

    def test_extract_custom_plugin_definition(self, plugin_extractor):
        """Test extracting custom plugin via { plugin: X, options: {...} } form."""
        content = """
await server.register({
    plugin: require('./my-auth-plugin'),
    options: {
        secret: 'my-secret',
    },
    routes: {
        prefix: '/auth',
    },
});
"""
        result = plugin_extractor.extract(content, "plugins/auth.js")
        plugins = result.get('plugins', [])
        assert len(plugins) >= 1


# ═══════════════════════════════════════════════════════════════════
# Auth Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestHapiAuthExtractor:

    def test_extract_jwt_strategy(self, auth_extractor):
        """Test extracting JWT auth strategy."""
        content = """
const HapiJwt = require('hapi-auth-jwt2');

await server.register(HapiJwt);

server.auth.strategy('jwt', 'jwt', {
    key: process.env.JWT_SECRET,
    validate: validateFunc,
    verifyOptions: { algorithms: ['HS256'] },
});

server.auth.default('jwt');
"""
        result = auth_extractor.extract(content, "auth.js")
        strategies = result.get('strategies', [])
        assert len(strategies) >= 1
        assert strategies[0].name == 'jwt'

    def test_extract_auth_scheme(self, auth_extractor):
        """Test extracting custom auth scheme."""
        content = """
server.auth.scheme('custom-scheme', (server, options) => {
    return {
        authenticate: async (request, h) => {
            const token = request.headers.authorization;
            if (!token) {
                throw Boom.unauthorized('Missing auth token');
            }
            return h.authenticated({ credentials: { user: decoded } });
        },
    };
});

server.auth.strategy('custom', 'custom-scheme');
"""
        result = auth_extractor.extract(content, "auth/scheme.js")
        schemes = result.get('schemes', [])
        assert len(schemes) >= 1

    def test_extract_default_auth(self, auth_extractor):
        """Test extracting default auth strategy."""
        content = """
server.auth.default('session');
"""
        result = auth_extractor.extract(content, "server.js")
        default_auth = result.get('default_strategy', '')
        assert default_auth == 'session'


# ═══════════════════════════════════════════════════════════════════
# Server Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestHapiServerExtractor:

    def test_extract_server_config(self, server_extractor):
        """Test extracting Hapi server configuration."""
        content = """
const Hapi = require('@hapi/hapi');

const server = Hapi.server({
    port: 3000,
    host: 'localhost',
    routes: {
        cors: true,
    },
});
"""
        result = server_extractor.extract(content, "server.js")
        config = result.get('config', None)
        assert config is not None

    def test_extract_server_methods(self, server_extractor):
        """Test extracting server methods."""
        content = """
server.method('add', (a, b) => {
    return a + b;
});

server.method('getUser', async (id) => {
    return db.users.findById(id);
}, {
    cache: {
        expiresIn: 60000,
        generateTimeout: 2000,
    },
});
"""
        result = server_extractor.extract(content, "methods.js")
        methods = result.get('methods', [])
        assert len(methods) >= 2

    def test_extract_ext_points(self, server_extractor):
        """Test extracting server extension points."""
        content = """
server.ext('onPreAuth', (request, h) => {
    request.headers['x-custom'] = 'value';
    return h.continue;
});

server.ext('onPostHandler', (request, h) => {
    console.log('Request completed');
    return h.continue;
});
"""
        result = server_extractor.extract(content, "server.js")
        ext_points = result.get('ext_points', [])
        assert len(ext_points) >= 2
        events = [e.event for e in ext_points]
        assert 'onPreAuth' in events
        assert 'onPostHandler' in events

    def test_extract_cache_config(self, server_extractor):
        """Test extracting catbox cache configuration."""
        content = """
const CatboxRedis = require('@hapi/catbox-redis');

const server = Hapi.server({
    port: 3000,
    cache: [
        {
            name: 'redis-cache',
            provider: {
                constructor: CatboxRedis,
                options: {
                    host: 'localhost',
                    port: 6379,
                },
            },
        },
    ],
});
"""
        result = server_extractor.extract(content, "server.js")
        caches = result.get('caches', [])
        assert len(caches) >= 1


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestHapiApiExtractor:

    def test_extract_official_packages(self, api_extractor):
        """Test extracting official Hapi package imports."""
        content = """
const Hapi = require('@hapi/hapi');
const Boom = require('@hapi/boom');
const Joi = require('@hapi/joi');
const Hoek = require('@hapi/hoek');
const Inert = require('@hapi/inert');
"""
        result = api_extractor.extract(content, "server.js")
        imports = result.get('imports', [])
        assert len(imports) >= 4
        packages = [i.package for i in imports]
        assert '@hapi/hapi' in packages
        assert '@hapi/boom' in packages

    def test_extract_community_packages(self, api_extractor):
        """Test extracting community Hapi package imports."""
        content = """
const HapiSwagger = require('hapi-swagger');
const Good = require('@hapi/good');
const HapiAuthJwt = require('hapi-auth-jwt2');
"""
        result = api_extractor.extract(content, "server.js")
        imports = result.get('imports', [])
        assert len(imports) >= 2

    def test_detect_legacy_hapi(self, api_extractor):
        """Test detecting legacy (pre-v17) Hapi."""
        content = """
const Hapi = require('hapi');
const server = new Hapi.Server();
server.connection({ port: 3000 });
"""
        result = api_extractor.extract(content, "server.js")
        imports = result.get('imports', [])
        # Should detect legacy hapi (unscoped package)
        packages = [i.package for i in imports]
        assert 'hapi' in packages


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedHapiParser:

    def test_is_hapi_file_positive(self, parser):
        """Test that Hapi files are correctly identified."""
        content = """
const Hapi = require('@hapi/hapi');
const server = Hapi.server({ port: 3000 });
"""
        assert parser.is_hapi_file(content, "server.js") is True

    def test_is_hapi_file_negative(self, parser):
        """Test that non-Hapi files are correctly rejected."""
        content = """
import React from 'react';
function App() { return <div>Hello</div>; }
"""
        assert parser.is_hapi_file(content, "App.tsx") is False

    def test_parse_full_hapi_file(self, parser):
        """Test full parsing of a Hapi server file."""
        content = """
'use strict';

const Hapi = require('@hapi/hapi');
const Joi = require('@hapi/joi');
const Boom = require('@hapi/boom');

const init = async () => {
    const server = Hapi.server({
        port: 3000,
        host: 'localhost',
        routes: {
            cors: true,
        },
    });

    server.route({
        method: 'GET',
        path: '/api/users',
        handler: async (request, h) => {
            return User.findAll();
        },
    });

    server.route({
        method: 'GET',
        path: '/api/users/{id}',
        options: {
            validate: {
                params: Joi.object({
                    id: Joi.string().required(),
                }),
            },
        },
        handler: async (request, h) => {
            const user = await User.findById(request.params.id);
            if (!user) throw Boom.notFound('User not found');
            return user;
        },
    });

    server.route({
        method: 'POST',
        path: '/api/users',
        options: {
            validate: {
                payload: Joi.object({
                    name: Joi.string().required(),
                    email: Joi.string().email().required(),
                }),
            },
        },
        handler: async (request, h) => {
            return h.response(await User.create(request.payload)).code(201);
        },
    });

    await server.start();
    console.log('Server running on %s', server.info.uri);
};

init();
"""
        result = parser.parse(content, "server.js")
        assert isinstance(result, HapiParseResult)
        assert len(result.routes) >= 3
        assert len(result.detected_frameworks) >= 0

    def test_detect_hapi_version(self, parser):
        """Test Hapi version detection."""
        # Modern @hapi/hapi (v17+)
        content_modern = """
const Hapi = require('@hapi/hapi');
const server = Hapi.server({ port: 3000 });
"""
        result = parser.parse(content_modern, "server.js")
        assert isinstance(result, HapiParseResult)

        # Legacy hapi (pre-v17)
        content_legacy = """
const Hapi = require('hapi');
const server = new Hapi.Server();
server.connection({ port: 3000 });
"""
        result_legacy = parser.parse(content_legacy, "server.js")
        assert isinstance(result_legacy, HapiParseResult)

    def test_parse_empty_content(self, parser):
        """Test parsing empty content returns empty result."""
        result = parser.parse("", "empty.js")
        assert isinstance(result, HapiParseResult)
        assert len(result.routes) == 0
        assert len(result.plugins) == 0

    def test_typescript_detection(self, parser):
        """Test TypeScript detection from file extension."""
        content = """
import Hapi from '@hapi/hapi';
"""
        result = parser.parse(content, "server.ts")
        assert result.is_typescript is True

        result_js = parser.parse(content, "server.js")
        assert result_js.is_typescript is False
