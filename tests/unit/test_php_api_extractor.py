"""
Tests for PhpAPIExtractor — routes, controllers, middleware, gRPC, GraphQL.

Part of CodeTrellis v4.24 PHP Language Support.
"""

import pytest
from codetrellis.extractors.php.api_extractor import PhpAPIExtractor


@pytest.fixture
def extractor():
    return PhpAPIExtractor()


# ===== LARAVEL ROUTES =====

class TestLaravelRoutes:
    """Tests for Laravel route extraction."""

    def test_basic_get_route(self, extractor):
        code = '''<?php
Route::get('/users', [UserController::class, 'index']);
Route::get('/users/{id}', [UserController::class, 'show']);
'''
        result = extractor.extract(code, "web.php")
        assert len(result["routes"]) >= 2

    def test_post_route(self, extractor):
        code = '''<?php
Route::post('/users', [UserController::class, 'store']);
'''
        result = extractor.extract(code, "api.php")
        assert len(result["routes"]) >= 1
        route = result["routes"][0]
        assert route.method.upper() == "POST"

    def test_resource_route(self, extractor):
        code = '''<?php
Route::resource('photos', PhotoController::class);
Route::apiResource('posts', PostController::class);
'''
        result = extractor.extract(code, "web.php")
        assert len(result["routes"]) >= 1

    def test_route_group(self, extractor):
        code = '''<?php
Route::prefix('api/v1')->middleware('auth:sanctum')->group(function () {
    Route::get('/users', [UserController::class, 'index']);
    Route::post('/users', [UserController::class, 'store']);
});
'''
        result = extractor.extract(code, "api.php")
        assert len(result["routes"]) >= 2

    def test_route_with_middleware(self, extractor):
        code = '''<?php
Route::middleware(['auth', 'verified'])->group(function () {
    Route::get('/dashboard', [DashboardController::class, 'index']);
});
'''
        result = extractor.extract(code, "web.php")
        assert len(result["routes"]) >= 1


# ===== SYMFONY ROUTES =====

class TestSymfonyRoutes:
    """Tests for Symfony route attribute extraction."""

    def test_route_attribute(self, extractor):
        code = '''<?php
class UserController extends AbstractController
{
    #[Route('/users', name: 'user_list', methods: ['GET'])]
    public function list(): Response
    {
        return $this->json($this->userRepository->findAll());
    }
}
'''
        result = extractor.extract(code, "UserController.php")
        assert len(result["routes"]) >= 1

    def test_multiple_route_attributes(self, extractor):
        code = '''<?php
class ProductController extends AbstractController
{
    #[Route('/products', methods: ['GET'])]
    public function index(): Response {}

    #[Route('/products/{id}', methods: ['GET'])]
    public function show(int $id): Response {}

    #[Route('/products', methods: ['POST'])]
    public function create(Request $request): Response {}
}
'''
        result = extractor.extract(code, "ProductController.php")
        assert len(result["routes"]) >= 3


# ===== SLIM ROUTES =====

class TestSlimRoutes:
    """Tests for Slim framework route extraction."""

    def test_slim_routes(self, extractor):
        code = '''<?php
$app->get('/hello/{name}', function (Request $request, Response $response, array $args) {
    $name = $args['name'];
    $response->getBody()->write("Hello, $name");
    return $response;
});

$app->post('/users', function (Request $request, Response $response) {
    return $response;
});
'''
        result = extractor.extract(code, "routes.php")
        assert len(result["routes"]) >= 2


# ===== CONTROLLER EXTRACTION =====

class TestControllerExtraction:
    """Tests for controller extraction."""

    def test_laravel_controller(self, extractor):
        code = '''<?php
namespace App\\Http\\Controllers;

class UserController extends Controller
{
    public function index() {}
    public function show(int $id) {}
    public function store(Request $request) {}
    public function update(Request $request, int $id) {}
    public function destroy(int $id) {}
}
'''
        result = extractor.extract(code, "UserController.php")
        assert len(result["controllers"]) >= 1
        ctrl = result["controllers"][0]
        assert "UserController" in ctrl.name
        assert len(ctrl.actions) >= 3

    def test_symfony_controller(self, extractor):
        code = '''<?php
namespace App\\Controller;

class ArticleController extends AbstractController
{
    #[Route('/articles')]
    public function list(): Response {}

    #[Route('/articles/{id}')]
    public function show(int $id): Response {}
}
'''
        result = extractor.extract(code, "ArticleController.php")
        assert len(result["controllers"]) >= 1


# ===== MIDDLEWARE EXTRACTION =====

class TestMiddlewareExtraction:
    """Tests for middleware extraction."""

    def test_laravel_middleware(self, extractor):
        code = '''<?php
namespace App\\Http\\Middleware;

class EnsureTokenIsValidMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        if ($request->input('token') !== 'valid-token') {
            return redirect('home');
        }
        return $next($request);
    }
}
'''
        result = extractor.extract(code, "EnsureTokenIsValidMiddleware.php")
        assert len(result["middleware"]) >= 1


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.php")
        assert result["routes"] == []
        assert result["controllers"] == []
        assert result["middleware"] == []

    def test_codeigniter_routes(self, extractor):
        code = '''<?php
$routes->get('products', 'ProductController::index');
$routes->get('products/(:num)', 'ProductController::show/$1');
$routes->post('products', 'ProductController::create');
'''
        result = extractor.extract(code, "Routes.php")
        assert len(result["routes"]) >= 1
