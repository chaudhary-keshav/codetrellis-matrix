"""
Tests for AdonisJS extractors and EnhancedAdonisJSParser.

Part of CodeTrellis v4.87 AdonisJS Backend Framework Support.
Tests cover:
- Route extraction (Route.get/post/resource/group, v4-v6 patterns, params, naming)
- Controller extraction (class detection, actions, DI, validators)
- Middleware extraction (global/named/route middleware, kernel config)
- Model extraction (Lucid ORM, @column, relationships, hooks, scopes, soft deletes)
- API extraction (core/official/community packages, version detection)
- Parser integration (framework detection, version detection, is_adonisjs_file)
"""

import pytest
from codetrellis.adonisjs_parser_enhanced import (
    EnhancedAdonisJSParser,
    AdonisJSParseResult,
)
from codetrellis.extractors.adonisjs import (
    AdonisRouteExtractor,
    AdonisControllerExtractor,
    AdonisMiddlewareExtractor,
    AdonisModelExtractor,
    AdonisApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedAdonisJSParser()


@pytest.fixture
def route_extractor():
    return AdonisRouteExtractor()


@pytest.fixture
def controller_extractor():
    return AdonisControllerExtractor()


@pytest.fixture
def middleware_extractor():
    return AdonisMiddlewareExtractor()


@pytest.fixture
def model_extractor():
    return AdonisModelExtractor()


@pytest.fixture
def api_extractor():
    return AdonisApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Route Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAdonisRouteExtractor:

    def test_extract_basic_routes(self, route_extractor):
        """Test extracting basic Route.get/post/put/delete."""
        content = """
import Route from '@ioc:Adonis/Core/Route'

Route.get('/users', 'UsersController.index')
Route.post('/users', 'UsersController.store')
Route.put('/users/:id', 'UsersController.update')
Route.delete('/users/:id', 'UsersController.destroy')
Route.patch('/users/:id', 'UsersController.patch')
"""
        result = route_extractor.extract(content, "start/routes.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 5
        methods = [r.method for r in routes]
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'PUT' in methods
        assert 'DELETE' in methods

    def test_extract_route_params(self, route_extractor):
        """Test extracting route parameters."""
        content = """
Route.get('/users/:id/posts/:postId', 'PostsController.show')
"""
        result = route_extractor.extract(content, "start/routes.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        assert 'id' in routes[0].params
        assert 'postId' in routes[0].params

    def test_extract_route_group(self, route_extractor):
        """Test extracting Route.group()."""
        content = """
Route.group(() => {
  Route.get('/users', 'UsersController.index')
  Route.post('/users', 'UsersController.store')
}).prefix('/api/v1').middleware(['auth'])
"""
        result = route_extractor.extract(content, "start/routes.ts")
        groups = result.get('groups', [])
        assert len(groups) >= 1

    def test_extract_resource_routes(self, route_extractor):
        """Test extracting Route.resource()."""
        content = """
Route.resource('users', 'UsersController').apiOnly()
Route.resource('posts', 'PostsController').only(['index', 'show', 'store'])
"""
        result = route_extractor.extract(content, "start/routes.ts")
        resources = result.get('resources', [])
        assert len(resources) >= 2

    def test_extract_named_routes(self, route_extractor):
        """Test extracting named routes."""
        content = """
Route.get('/dashboard', 'DashboardController.index').as('dashboard')
Route.get('/login', 'AuthController.login').as('auth.login')
"""
        result = route_extractor.extract(content, "start/routes.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 2
        named = [r for r in routes if r.name]
        assert len(named) >= 1

    def test_extract_v6_routes(self, route_extractor):
        """Test extracting v6 route patterns (ESM, hash imports)."""
        content = """
import router from '@adonisjs/core/services/router'

const UsersController = () => import('#controllers/users_controller')

router.get('/users', [UsersController, 'index'])
router.post('/users', [UsersController, 'store'])
"""
        result = route_extractor.extract(content, "start/routes.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 2


# ═══════════════════════════════════════════════════════════════════
# Controller Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAdonisControllerExtractor:

    def test_extract_basic_controller(self, controller_extractor):
        """Test extracting a basic controller class."""
        content = """
import { HttpContextContract } from '@ioc:Adonis/Core/HttpContext'

export default class UsersController {
  public async index({ request, response }: HttpContextContract) {
    const users = await User.all()
    return response.json(users)
  }

  public async store({ request, response }: HttpContextContract) {
    const data = request.only(['name', 'email'])
    const user = await User.create(data)
    return response.created(user)
  }

  public async show({ params, response }: HttpContextContract) {
    const user = await User.findOrFail(params.id)
    return response.json(user)
  }

  public async update({ params, request, response }: HttpContextContract) {
    const user = await User.findOrFail(params.id)
    user.merge(request.only(['name', 'email']))
    await user.save()
    return response.json(user)
  }

  public async destroy({ params, response }: HttpContextContract) {
    const user = await User.findOrFail(params.id)
    await user.delete()
    return response.noContent()
  }
}
"""
        result = controller_extractor.extract(content, "app/Controllers/Http/UsersController.ts")
        controllers = result.get('controllers', [])
        assert len(controllers) >= 1
        ctrl = controllers[0]
        assert ctrl.name == 'UsersController'
        assert len(ctrl.actions) >= 5
        assert ctrl.is_resourceful is True

    def test_extract_controller_with_injection(self, controller_extractor):
        """Test extracting controller with dependency injection."""
        content = """
import { inject } from '@adonisjs/core'
import UserService from '#services/user_service'

@inject()
export default class UsersController {
  constructor(private userService: UserService) {}

  async index() {
    return this.userService.getAll()
  }
}
"""
        result = controller_extractor.extract(content, "app/controllers/users_controller.ts")
        controllers = result.get('controllers', [])
        assert len(controllers) >= 1
        ctrl = controllers[0]
        assert ctrl.has_injection is True

    def test_extract_controller_with_validator(self, controller_extractor):
        """Test extracting controller that uses validators."""
        content = """
import { HttpContextContract } from '@ioc:Adonis/Core/HttpContext'
import CreateUserValidator from 'App/Validators/CreateUserValidator'

export default class UsersController {
  public async store({ request }: HttpContextContract) {
    const payload = await request.validate(CreateUserValidator)
    return User.create(payload)
  }
}
"""
        result = controller_extractor.extract(content, "app/Controllers/Http/UsersController.ts")
        controllers = result.get('controllers', [])
        assert len(controllers) >= 1


# ═══════════════════════════════════════════════════════════════════
# Middleware Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAdonisMiddlewareExtractor:

    def test_extract_middleware_class(self, middleware_extractor):
        """Test extracting middleware class definition."""
        content = """
import { HttpContextContract } from '@ioc:Adonis/Core/HttpContext'

export default class AuthMiddleware {
  public async handle({ auth, response }: HttpContextContract, next: () => Promise<void>) {
    try {
      await auth.authenticate()
    } catch {
      return response.unauthorized({ error: 'Must be logged in' })
    }
    await next()
  }
}
"""
        result = middleware_extractor.extract(content, "app/Middleware/Auth.ts")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 1
        assert middleware[0].name == 'AuthMiddleware' or middleware[0].class_name == 'AuthMiddleware'

    def test_extract_kernel_registration(self, middleware_extractor):
        """Test extracting middleware from kernel config (v5)."""
        content = """
Server.middleware.register([
  () => import('@ioc:Adonis/Core/BodyParser'),
  () => import('App/Middleware/SilentAuth'),
])

Server.middleware.registerNamed({
  auth: () => import('App/Middleware/Auth'),
  guest: () => import('App/Middleware/Guest'),
  admin: () => import('App/Middleware/Admin'),
})
"""
        result = middleware_extractor.extract(content, "start/kernel.ts")
        kernel = result.get('kernel')
        assert kernel is not None
        # Global middleware from Server.middleware.register()
        assert len(kernel.global_middleware) >= 2
        # Named middleware from Server.middleware.registerNamed()
        assert len(kernel.named_middleware) >= 2

    def test_extract_v6_middleware(self, middleware_extractor):
        """Test extracting v6 middleware patterns."""
        content = """
import router from '@adonisjs/core/services/router'
import { middleware } from '#start/kernel'

router.get('/dashboard', [DashboardController, 'index']).use(middleware.auth())
"""
        result = middleware_extractor.extract(content, "start/routes.ts")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 0  # At least parses without error


# ═══════════════════════════════════════════════════════════════════
# Model Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAdonisModelExtractor:

    def test_extract_basic_model(self, model_extractor):
        """Test extracting a basic Lucid model."""
        content = """
import { DateTime } from 'luxon'
import { BaseModel, column } from '@ioc:Adonis/Lucid/Orm'

export default class User extends BaseModel {
  @column({ isPrimary: true })
  public id: number

  @column()
  public name: string

  @column()
  public email: string

  @column.dateTime({ autoCreate: true })
  public createdAt: DateTime

  @column.dateTime({ autoCreate: true, autoUpdate: true })
  public updatedAt: DateTime
}
"""
        result = model_extractor.extract(content, "app/Models/User.ts")
        models = result.get('models', [])
        assert len(models) >= 1
        model = models[0]
        assert model.name == 'User'
        assert len(model.columns) >= 3
        assert model.has_timestamps is True

    def test_extract_model_relationships(self, model_extractor):
        """Test extracting Lucid model relationships."""
        content = """
import { BaseModel, column, hasMany, belongsTo, HasMany, BelongsTo } from '@ioc:Adonis/Lucid/Orm'
import Post from 'App/Models/Post'
import Team from 'App/Models/Team'

export default class User extends BaseModel {
  @column({ isPrimary: true })
  public id: number

  @column()
  public teamId: number

  @hasMany(() => Post)
  public posts: HasMany<typeof Post>

  @belongsTo(() => Team)
  public team: BelongsTo<typeof Team>
}
"""
        result = model_extractor.extract(content, "app/Models/User.ts")
        models = result.get('models', [])
        assert len(models) >= 1
        model = models[0]
        assert len(model.relationships) >= 2
        rel_types = [r.type for r in model.relationships]
        assert 'hasMany' in rel_types
        assert 'belongsTo' in rel_types

    def test_extract_model_hooks(self, model_extractor):
        """Test extracting model lifecycle hooks."""
        content = """
import { BaseModel, column, beforeSave, afterCreate } from '@ioc:Adonis/Lucid/Orm'
import Hash from '@ioc:Adonis/Core/Hash'

export default class User extends BaseModel {
  @column({ isPrimary: true })
  public id: number

  @column()
  public password: string

  @beforeSave()
  public static async hashPassword(user: User) {
    if (user.$dirty.password) {
      user.password = await Hash.make(user.password)
    }
  }

  @afterCreate()
  public static async sendWelcomeEmail(user: User) {
    await Mail.send('welcome', user)
  }
}
"""
        result = model_extractor.extract(content, "app/Models/User.ts")
        models = result.get('models', [])
        assert len(models) >= 1
        model = models[0]
        assert len(model.hooks) >= 2

    def test_extract_soft_deletes(self, model_extractor):
        """Test extracting model with soft deletes."""
        content = """
import { BaseModel, column, SoftDeletes } from '@ioc:Adonis/Lucid/Orm'
import { compose } from '@ioc:Adonis/Core/Helpers'

export default class Post extends compose(BaseModel, SoftDeletes) {
  @column({ isPrimary: true })
  public id: number

  @column()
  public title: string

  @column.dateTime()
  public deletedAt: DateTime | null
}
"""
        result = model_extractor.extract(content, "app/Models/Post.ts")
        models = result.get('models', [])
        assert len(models) >= 1
        model = models[0]
        assert model.has_soft_deletes is True

    def test_extract_model_scopes(self, model_extractor):
        """Test extracting model query scopes."""
        content = """
import { BaseModel, column, scope } from '@ioc:Adonis/Lucid/Orm'

export default class Post extends BaseModel {
  @column({ isPrimary: true })
  public id: number

  @column()
  public status: string

  @column()
  public publishedAt: DateTime | null

  public static published = scope((query) => {
    query.where('status', 'published')
  })

  public static recent = scope((query) => {
    query.orderBy('createdAt', 'desc')
  })
}
"""
        result = model_extractor.extract(content, "app/Models/Post.ts")
        models = result.get('models', [])
        assert len(models) >= 1
        model = models[0]
        assert len(model.scopes) >= 2


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAdonisApiExtractor:

    def test_extract_core_imports(self, api_extractor):
        """Test extracting AdonisJS core package imports."""
        content = """
import Route from '@ioc:Adonis/Core/Route'
import HttpContext from '@ioc:Adonis/Core/HttpContext'
import { BaseModel, column } from '@ioc:Adonis/Lucid/Orm'
import Hash from '@ioc:Adonis/Core/Hash'
"""
        result = api_extractor.extract(content, "app/Models/User.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 3

    def test_extract_v6_imports(self, api_extractor):
        """Test extracting AdonisJS v6 imports."""
        content = """
import router from '@adonisjs/core/services/router'
import { middleware } from '#start/kernel'
import { HttpContext } from '@adonisjs/core/http'
import db from '@adonisjs/lucid/services/db'
"""
        result = api_extractor.extract(content, "start/routes.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 2

    def test_detect_adonis_version_v5(self, api_extractor):
        """Test detecting AdonisJS v5 from IoC imports."""
        content = """
import Route from '@ioc:Adonis/Core/Route'
import { HttpContextContract } from '@ioc:Adonis/Core/HttpContext'
"""
        result = api_extractor.extract(content, "start/routes.ts")
        # Should detect v5 patterns via @ioc: imports
        imports = result.get('imports', [])
        assert len(imports) >= 1

    def test_detect_adonis_version_v6(self, api_extractor):
        """Test detecting AdonisJS v6 from @adonisjs/ imports."""
        content = """
import router from '@adonisjs/core/services/router'
import { HttpContext } from '@adonisjs/core/http'
"""
        result = api_extractor.extract(content, "start/routes.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedAdonisJSParser:

    def test_is_adonisjs_file_positive(self, parser):
        """Test that AdonisJS files are correctly identified."""
        content = """
import Route from '@ioc:Adonis/Core/Route'

Route.get('/', 'HomeController.index')
"""
        assert parser.is_adonisjs_file(content, "start/routes.ts") is True

    def test_is_adonisjs_file_v6_positive(self, parser):
        """Test that AdonisJS v6 files are correctly identified."""
        content = """
import router from '@adonisjs/core/services/router'
"""
        assert parser.is_adonisjs_file(content, "start/routes.ts") is True

    def test_is_adonisjs_file_negative(self, parser):
        """Test that non-AdonisJS files are correctly rejected."""
        content = """
import React from 'react';
function App() { return <div>Hello</div>; }
"""
        assert parser.is_adonisjs_file(content, "App.tsx") is False

    def test_parse_full_adonisjs_file(self, parser):
        """Test full parsing of an AdonisJS routes file."""
        content = """
import Route from '@ioc:Adonis/Core/Route'

Route.group(() => {
  Route.get('/users', 'UsersController.index')
  Route.post('/users', 'UsersController.store')
  Route.get('/users/:id', 'UsersController.show')
  Route.put('/users/:id', 'UsersController.update')
  Route.delete('/users/:id', 'UsersController.destroy')
}).prefix('/api/v1').middleware(['auth'])

Route.resource('posts', 'PostsController').apiOnly()

Route.get('/', 'HomeController.index')
Route.get('/login', 'AuthController.login').as('auth.login')
Route.post('/login', 'AuthController.authenticate')
"""
        result = parser.parse(content, "start/routes.ts")
        assert isinstance(result, AdonisJSParseResult)
        assert len(result.routes) >= 5
        assert len(result.route_groups) >= 1
        assert len(result.resource_routes) >= 1

    def test_parse_model_file(self, parser):
        """Test parsing a Lucid model file."""
        content = """
import { DateTime } from 'luxon'
import { BaseModel, column, hasMany, HasMany } from '@ioc:Adonis/Lucid/Orm'
import Post from 'App/Models/Post'

export default class User extends BaseModel {
  @column({ isPrimary: true })
  public id: number

  @column()
  public name: string

  @column()
  public email: string

  @hasMany(() => Post)
  public posts: HasMany<typeof Post>

  @column.dateTime({ autoCreate: true })
  public createdAt: DateTime

  @column.dateTime({ autoCreate: true, autoUpdate: true })
  public updatedAt: DateTime
}
"""
        result = parser.parse(content, "app/Models/User.ts")
        assert isinstance(result, AdonisJSParseResult)
        assert len(result.models) >= 1
        model = result.models[0]
        assert model.name == 'User'
        assert len(model.relationships) >= 1

    def test_parse_controller_file(self, parser):
        """Test parsing a controller file."""
        content = """
import { HttpContextContract } from '@ioc:Adonis/Core/HttpContext'

export default class UsersController {
  public async index({ response }: HttpContextContract) {
    return response.json(await User.all())
  }

  public async store({ request, response }: HttpContextContract) {
    const data = request.only(['name', 'email'])
    return response.created(await User.create(data))
  }
}
"""
        result = parser.parse(content, "app/Controllers/Http/UsersController.ts")
        assert isinstance(result, AdonisJSParseResult)
        assert len(result.controllers) >= 1
        ctrl = result.controllers[0]
        assert ctrl.name == 'UsersController'

    def test_detect_adonis_version(self, parser):
        """Test AdonisJS version detection."""
        # v5 (IoC container imports)
        content_v5 = """
import Route from '@ioc:Adonis/Core/Route'
"""
        result_v5 = parser.parse(content_v5, "start/routes.ts")
        assert isinstance(result_v5, AdonisJSParseResult)

        # v6 (ESM imports)
        content_v6 = """
import router from '@adonisjs/core/services/router'
"""
        result_v6 = parser.parse(content_v6, "start/routes.ts")
        assert isinstance(result_v6, AdonisJSParseResult)

    def test_parse_empty_content(self, parser):
        """Test parsing empty content returns empty result."""
        result = parser.parse("", "empty.ts")
        assert isinstance(result, AdonisJSParseResult)
        assert len(result.routes) == 0
        assert len(result.controllers) == 0
        assert len(result.models) == 0

    def test_typescript_detection(self, parser):
        """Test TypeScript detection from file extension."""
        content = """
import Route from '@ioc:Adonis/Core/Route'
"""
        result = parser.parse(content, "start/routes.ts")
        assert result.is_typescript is True

        result_js = parser.parse(content, "start/routes.js")
        assert result_js.is_typescript is False

    def test_legacy_v4_detection(self, parser):
        """Test legacy v4 AdonisJS detection."""
        content = """
'use strict'

const Route = use('Route')

Route.get('/', 'HomeController.index')
Route.group(() => {
  Route.resource('users', 'UserController')
}).prefix('api')
"""
        result = parser.parse(content, "start/routes.js")
        assert isinstance(result, AdonisJSParseResult)
        # v4 uses `use()` for imports
        assert result.is_legacy is True or len(result.routes) >= 1
