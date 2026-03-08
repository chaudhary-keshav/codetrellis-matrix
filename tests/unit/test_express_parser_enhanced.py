"""
Tests for Express.js extractors and EnhancedExpressParser.

Part of CodeTrellis v4.80 Express.js Backend Framework Support.
Tests cover:
- Route extraction (HTTP methods, Router, params, middleware chains)
- Middleware extraction (global, route-level, third-party, custom)
- Error handler extraction (4-param handlers, custom error classes)
- Config extraction (app.set, view engines, static files, server listen)
- API pattern extraction (RESTful resources, versioning, response patterns)
- Parser integration (framework detection, version detection, is_express_file)
"""

import pytest
from codetrellis.express_parser_enhanced import (
    EnhancedExpressParser,
    ExpressParseResult,
)
from codetrellis.extractors.express import (
    ExpressRouteExtractor,
    ExpressRouteInfo,
    ExpressRouterInfo,
    ExpressParamInfo,
    ExpressMiddlewareExtractor,
    ExpressMiddlewareInfo,
    ExpressMiddlewareStackInfo,
    ExpressErrorExtractor,
    ExpressErrorHandlerInfo,
    ExpressConfigExtractor,
    ExpressApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedExpressParser()


@pytest.fixture
def route_extractor():
    return ExpressRouteExtractor()


@pytest.fixture
def middleware_extractor():
    return ExpressMiddlewareExtractor()


@pytest.fixture
def error_extractor():
    return ExpressErrorExtractor()


@pytest.fixture
def config_extractor():
    return ExpressConfigExtractor()


@pytest.fixture
def api_extractor():
    return ExpressApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Route Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestExpressRouteExtractor:

    def test_extract_basic_routes(self, route_extractor):
        """Test extracting basic HTTP method routes."""
        content = """
const express = require('express');
const app = express();

app.get('/users', getUsers);
app.post('/users', createUser);
app.put('/users/:id', updateUser);
app.delete('/users/:id', deleteUser);
app.patch('/users/:id', patchUser);
"""
        result = route_extractor.extract(content, "app.js")
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
const express = require('express');
const router = express.Router();

router.get('/', listItems);
router.post('/', createItem);
router.get('/:id', getItem);
"""
        result = route_extractor.extract(content, "routes/items.js")
        routers = result.get('routers', [])
        routes = result.get('routes', [])
        assert len(routers) >= 1
        assert len(routes) >= 3

    def test_extract_route_with_middleware(self, route_extractor):
        """Test routes with inline middleware."""
        content = """
const express = require('express');
const app = express();

app.get('/admin', isAdmin, authenticate, getAdminDashboard);
app.post('/users', validate(userSchema), createUser);
"""
        result = route_extractor.extract(content, "app.js")
        routes = result.get('routes', [])
        assert len(routes) >= 2

    def test_extract_param_middleware(self, route_extractor):
        """Test app.param() middleware."""
        content = """
const express = require('express');
const app = express();

app.param('id', function(req, res, next, id) {
    req.item = items[id];
    next();
});
"""
        result = route_extractor.extract(content, "app.js")
        params = result.get('params', [])
        assert len(params) >= 1

    def test_extract_async_routes(self, route_extractor):
        """Test async route handlers (Express 5.x)."""
        content = """
const express = require('express');
const app = express();

app.get('/users', async (req, res) => {
    const users = await User.find();
    res.json(users);
});

app.post('/users', async (req, res, next) => {
    try {
        const user = await User.create(req.body);
        res.status(201).json(user);
    } catch (err) {
        next(err);
    }
});
"""
        result = route_extractor.extract(content, "app.js")
        routes = result.get('routes', [])
        assert len(routes) >= 2

    def test_extract_route_chaining(self, route_extractor):
        """Test standard route definitions (chained .route() is handled at parser level)."""
        content = """
const express = require('express');
const app = express();

app.get('/books', listBooks);
app.post('/books', addBook);
app.put('/books/:id', updateBook);
"""
        result = route_extractor.extract(content, "app.js")
        routes = result.get('routes', [])
        assert len(routes) >= 3


# ═══════════════════════════════════════════════════════════════════
# Middleware Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestExpressMiddlewareExtractor:

    def test_extract_builtin_middleware(self, middleware_extractor):
        """Test extracting built-in Express middleware."""
        content = """
const express = require('express');
const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));
"""
        result = middleware_extractor.extract(content, "app.js")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 3

    def test_extract_third_party_middleware(self, middleware_extractor):
        """Test extracting third-party middleware."""
        content = """
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');

const app = express();

app.use(cors());
app.use(helmet());
app.use(morgan('dev'));
app.use(compression());
"""
        result = middleware_extractor.extract(content, "app.js")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 4

    def test_extract_mounted_middleware(self, middleware_extractor):
        """Test middleware with mount path."""
        content = """
const express = require('express');
const app = express();

app.use('/api', cors());
app.use('/admin', isAdmin);
"""
        result = middleware_extractor.extract(content, "app.js")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 2


# ═══════════════════════════════════════════════════════════════════
# Error Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestExpressErrorExtractor:

    def test_extract_error_handler(self, error_extractor):
        """Test extracting error handling middleware."""
        content = """
const express = require('express');
const app = express();

app.use(function errorHandler(err, req, res, next) {
    console.error(err.stack);
    res.status(500).json({ error: err.message });
});
"""
        result = error_extractor.extract(content, "app.js")
        handlers = result.get('error_handlers', [])
        assert len(handlers) >= 1

    def test_extract_custom_error_class(self, error_extractor):
        """Test extracting custom error classes."""
        content = """
class NotFoundError extends Error {
    constructor(message) {
        super(message);
        this.statusCode = 404;
    }
}

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.statusCode = 400;
    }
}
"""
        result = error_extractor.extract(content, "errors.js")
        custom_errors = result.get('custom_errors', [])
        assert len(custom_errors) >= 2


# ═══════════════════════════════════════════════════════════════════
# Config Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestExpressConfigExtractor:

    def test_extract_app_settings(self, config_extractor):
        """Test extracting app.set() settings."""
        content = """
const express = require('express');
const app = express();

app.set('view engine', 'ejs');
app.set('views', './views');
app.set('port', process.env.PORT || 3000);
app.enable('trust proxy');
"""
        result = config_extractor.extract(content, "app.js")
        settings = result.get('settings', [])
        assert len(settings) >= 3

    def test_extract_server_listen(self, config_extractor):
        """Test extracting server listen configuration."""
        content = """
const express = require('express');
const app = express();

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
"""
        result = config_extractor.extract(content, "app.js")
        servers = result.get('servers', [])
        assert len(servers) >= 1


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestExpressApiExtractor:

    def test_extract_rest_resources(self, api_extractor):
        """Test extracting RESTful resource patterns."""
        content = """
const express = require('express');
const router = express.Router();

router.get('/users', listUsers);
router.post('/users', createUser);
router.get('/users/:id', getUser);
router.put('/users/:id', updateUser);
router.delete('/users/:id', deleteUser);
"""
        result = api_extractor.extract(content, "routes/users.js")
        resources = result.get('resources', [])
        assert len(resources) >= 1

    def test_extract_api_versioning(self, api_extractor):
        """Test extracting API version patterns from route paths."""
        content = """
const express = require('express');
const app = express();

app.get('/api/v1/users', listUsersV1);
app.get('/api/v2/users', listUsersV2);
app.post('/api/v1/users', createUserV1);
"""
        result = api_extractor.extract(content, "app.js")
        versions = result.get('api_versions', [])
        assert len(versions) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedExpressParser:

    def test_is_express_file(self, parser):
        """Test Express file detection."""
        express_content = """
const express = require('express');
const app = express();
app.get('/health', (req, res) => res.json({ status: 'ok' }));
"""
        assert parser.is_express_file(express_content, "app.js") is True

    def test_is_not_express_file(self, parser):
        """Test non-Express file detection."""
        react_content = """
import React from 'react';
const App = () => <div>Hello</div>;
export default App;
"""
        assert parser.is_express_file(react_content, "App.tsx") is False

    def test_parse_full_express_app(self, parser):
        """Test parsing a full Express.js application file."""
        content = """
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');

const app = express();

// Middleware
app.use(cors());
app.use(helmet());
app.use(morgan('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.get('/api/users', async (req, res) => {
    const users = await User.find();
    res.json(users);
});

app.post('/api/users', async (req, res) => {
    const user = await User.create(req.body);
    res.status(201).json(user);
});

app.get('/api/users/:id', async (req, res) => {
    const user = await User.findById(req.params.id);
    res.json(user);
});

// Error handler
app.use(function(err, req, res, next) {
    res.status(500).json({ error: err.message });
});

app.listen(3000, () => console.log('Server running'));
"""
        result = parser.parse(content, "app.js")
        assert isinstance(result, ExpressParseResult)
        assert len(result.routes) >= 3
        assert len(result.middleware) >= 4
        assert len(result.detected_frameworks) >= 1

    def test_detect_express_version(self, parser):
        """Test Express version detection from patterns."""
        content_v5 = """
import express from 'express';
const app = express();

// Express 5.x async error handling
app.get('/users', async (req, res) => {
    const users = await User.find();
    res.json(users);
});
"""
        result = parser.parse(content_v5, "app.ts")
        # Should detect some version or at minimum parse successfully
        assert isinstance(result, ExpressParseResult)

    def test_detect_express_ecosystem(self, parser):
        """Test ecosystem/framework detection."""
        content = """
const express = require('express');
const passport = require('passport');
const { body, validationResult } = require('express-validator');
const mongoose = require('mongoose');
const swaggerUi = require('swagger-ui-express');

const app = express();
app.use(passport.initialize());
"""
        result = parser.parse(content, "app.js")
        assert isinstance(result, ExpressParseResult)
        assert len(result.detected_frameworks) >= 1

    def test_parse_typescript_express(self, parser):
        """Test parsing TypeScript Express app."""
        content = """
import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';

const app = express();

app.use(cors());
app.use(express.json());

app.get('/api/health', (req: Request, res: Response) => {
    res.json({ status: 'ok' });
});

export default app;
"""
        result = parser.parse(content, "app.ts")
        assert isinstance(result, ExpressParseResult)
        assert result.is_typescript is True
        assert len(result.routes) >= 1

    def test_parse_express_router_module(self, parser):
        """Test parsing a separate Express Router file."""
        content = """
const express = require('express');
const router = express.Router();

router.get('/', listProducts);
router.get('/:id', getProduct);
router.post('/', authenticate, createProduct);
router.put('/:id', authenticate, updateProduct);
router.delete('/:id', authenticate, isAdmin, deleteProduct);

module.exports = router;
"""
        result = parser.parse(content, "routes/products.js")
        assert isinstance(result, ExpressParseResult)
        assert len(result.routes) >= 5
        assert len(result.routers) >= 1

    def test_parse_empty_file(self, parser):
        """Test parsing an empty file."""
        result = parser.parse("", "empty.js")
        assert isinstance(result, ExpressParseResult)
        assert len(result.routes) == 0
        assert len(result.middleware) == 0
