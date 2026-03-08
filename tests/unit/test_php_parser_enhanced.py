"""
Tests for EnhancedPhpParser — full parser integration, framework detection, composer.json parsing.

Part of CodeTrellis v4.24 PHP Language Support.
"""

import pytest
from codetrellis.php_parser_enhanced import EnhancedPhpParser, PhpParseResult


@pytest.fixture
def parser():
    return EnhancedPhpParser()


# ===== BASIC PARSING =====

class TestBasicParsing:
    """Tests for basic PHP file parsing."""

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.php")
        assert isinstance(result, PhpParseResult)
        assert result.file_path == "empty.php"
        assert result.classes == []
        assert result.functions == []
        assert result.methods == []

    def test_parse_simple_class(self, parser):
        code = '''<?php
declare(strict_types=1);

namespace App\\Models;

class User
{
    private string $name;
    private string $email;

    public function __construct(string $name, string $email)
    {
        $this->name = $name;
        $this->email = $email;
    }

    public function getName(): string
    {
        return $this->name;
    }
}
'''
        result = parser.parse(code, "User.php")
        assert len(result.classes) >= 1
        assert result.classes[0].name == "User"
        assert len(result.methods) >= 1

    def test_parse_interface(self, parser):
        code = '''<?php
namespace App\\Contracts;

interface UserRepositoryInterface
{
    public function findById(int $id): ?User;
    public function save(User $user): void;
}
'''
        result = parser.parse(code, "UserRepositoryInterface.php")
        assert len(result.interfaces) >= 1
        assert result.interfaces[0].name == "UserRepositoryInterface"

    def test_parse_trait(self, parser):
        code = '''<?php
namespace App\\Traits;

trait HasUuids
{
    public function initializeHasUuids(): void
    {
        $this->usesUniqueIds = true;
    }

    public function uniqueIds(): array
    {
        return [$this->getKeyName()];
    }
}
'''
        result = parser.parse(code, "HasUuids.php")
        assert len(result.traits) >= 1
        assert result.traits[0].name == "HasUuids"

    def test_parse_enum(self, parser):
        code = '''<?php
namespace App\\Enums;

enum Status: string
{
    case Active = 'active';
    case Inactive = 'inactive';
    case Pending = 'pending';
}
'''
        result = parser.parse(code, "Status.php")
        assert len(result.enums) >= 1
        assert result.enums[0].name == "Status"

    def test_parse_functions(self, parser):
        code = '''<?php
function add(int $a, int $b): int
{
    return $a + $b;
}

function subtract(int $a, int $b): int
{
    return $a - $b;
}
'''
        result = parser.parse(code, "math.php")
        assert len(result.functions) >= 2


# ===== FRAMEWORK DETECTION =====

class TestFrameworkDetection:
    """Tests for framework detection."""

    def test_detect_laravel(self, parser):
        code = '''<?php
namespace App\\Http\\Controllers;

use Illuminate\\Http\\Request;
use Illuminate\\Support\\Facades\\Route;

class UserController extends Controller
{
    public function index(Request $request)
    {
        return User::all();
    }
}
'''
        result = parser.parse(code, "UserController.php")
        assert "laravel" in result.detected_frameworks

    def test_detect_symfony(self, parser):
        code = '''<?php
namespace App\\Controller;

use Symfony\\Bundle\\FrameworkBundle\\Controller\\AbstractController;
use Symfony\\Component\\HttpFoundation\\Response;
use Symfony\\Component\\Routing\\Annotation\\Route;

class ProductController extends AbstractController
{
    #[Route('/products')]
    public function list(): Response
    {
        return $this->json([]);
    }
}
'''
        result = parser.parse(code, "ProductController.php")
        assert "symfony" in result.detected_frameworks

    def test_detect_slim(self, parser):
        code = '''<?php
use Slim\\Factory\\AppFactory;

$app = AppFactory::create();

$app->get('/hello/{name}', function ($request, $response, $args) {
    return $response;
});

$app->run();
'''
        result = parser.parse(code, "index.php")
        assert "slim" in result.detected_frameworks

    def test_detect_codeigniter(self, parser):
        code = '''<?php
namespace App\\Controllers;

use CodeIgniter\\Controller;

class Home extends Controller
{
    public function index()
    {
        return view('welcome_message');
    }
}
'''
        result = parser.parse(code, "Home.php")
        assert "codeigniter" in result.detected_frameworks

    def test_detect_wordpress(self, parser):
        code = '''<?php
/*
Plugin Name: My Plugin
*/

add_action('init', 'my_plugin_init');
add_filter('the_content', 'my_plugin_filter');

function my_plugin_init() {
    register_post_type('book', []);
}
'''
        result = parser.parse(code, "my-plugin.php")
        assert "wordpress" in result.detected_frameworks

    def test_detect_phpunit(self, parser):
        code = '''<?php
use PHPUnit\\Framework\\TestCase;

class CalculatorTest extends TestCase
{
    public function testAdd(): void
    {
        $calc = new Calculator();
        $this->assertEquals(4, $calc->add(2, 2));
    }
}
'''
        result = parser.parse(code, "CalculatorTest.php")
        assert "phpunit" in result.detected_frameworks

    def test_no_framework(self, parser):
        code = '''<?php
function hello(): string
{
    return "Hello World";
}
'''
        result = parser.parse(code, "hello.php")
        assert isinstance(result.detected_frameworks, list)


# ===== IMPORT EXTRACTION =====

class TestImportExtraction:
    """Tests for use statement (import) extraction."""

    def test_basic_imports(self, parser):
        code = '''<?php
use App\\Models\\User;
use App\\Models\\Order;
use Illuminate\\Http\\Request;
'''
        result = parser.parse(code, "test.php")
        assert len(result.use_imports) >= 3

    def test_grouped_imports(self, parser):
        code = '''<?php
use App\\Models\\User;
use App\\Models\\Order;
use App\\Models\\Product;
'''
        result = parser.parse(code, "test.php")
        assert len(result.use_imports) >= 3

    def test_aliased_import(self, parser):
        code = '''<?php
use App\\Models\\User as UserModel;
use Carbon\\Carbon as Date;
'''
        result = parser.parse(code, "test.php")
        assert len(result.use_imports) >= 2


# ===== COMPOSER.JSON PARSING =====

class TestComposerParsing:
    """Tests for composer.json parsing."""

    def test_parse_composer_json(self, parser):
        code = '''{
    "name": "laravel/laravel",
    "type": "project",
    "require": {
        "php": "^8.1",
        "laravel/framework": "^10.0",
        "laravel/sanctum": "^3.3"
    },
    "require-dev": {
        "phpunit/phpunit": "^10.0",
        "laravel/sail": "^1.18"
    }
}
'''
        result = parser.parse_composer_json(code)
        assert "packages" in result
        assert len(result["packages"]) >= 2
        assert "dev_packages" in result
        assert len(result["dev_packages"]) >= 1
        assert result["name"] == "laravel/laravel"

    def test_php_version_from_composer(self, parser):
        code = '''{
    "require": {
        "php": ">=8.2"
    }
}
'''
        result = parser.parse_composer_json(code)
        assert result.get("php_version") == ">=8.2"


# ===== ROUTE EXTRACTION =====

class TestRouteExtraction:
    """Tests for route extraction through the parser."""

    def test_laravel_routes(self, parser):
        code = '''<?php
use Illuminate\\Support\\Facades\\Route;

Route::get('/users', [UserController::class, 'index']);
Route::post('/users', [UserController::class, 'store']);
Route::get('/users/{id}', [UserController::class, 'show']);
Route::put('/users/{id}', [UserController::class, 'update']);
Route::delete('/users/{id}', [UserController::class, 'destroy']);
'''
        result = parser.parse(code, "routes/api.php")
        assert len(result.routes) >= 5


# ===== MODEL EXTRACTION =====

class TestModelExtraction:
    """Tests for model extraction through the parser."""

    def test_eloquent_model(self, parser):
        code = '''<?php
namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Model;
use Illuminate\\Database\\Eloquent\\SoftDeletes;

class Post extends Model
{
    use SoftDeletes;

    protected $fillable = ['title', 'body', 'user_id'];
    protected $casts = ['published_at' => 'datetime'];

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function comments()
    {
        return $this->hasMany(Comment::class);
    }

    public function tags()
    {
        return $this->belongsToMany(Tag::class);
    }
}
'''
        result = parser.parse(code, "Post.php")
        assert len(result.models) >= 1
        model = result.models[0]
        assert model.name == "Post"

    def test_doctrine_entity(self, parser):
        code = '''<?php
namespace App\\Entity;

use Doctrine\\ORM\\Mapping as ORM;

#[ORM\\Entity(repositoryClass: ProductRepository::class)]
#[ORM\\Table(name: 'products')]
class Product
{
    #[ORM\\Id]
    #[ORM\\GeneratedValue]
    #[ORM\\Column]
    private ?int $id = null;

    #[ORM\\Column(length: 255)]
    private ?string $name = null;
}
'''
        result = parser.parse(code, "Product.php")
        # Should detect either as model or class
        assert len(result.models) >= 1 or len(result.classes) >= 1


# ===== ATTRIBUTE EXTRACTION =====

class TestAttributeExtraction:
    """Tests for PHP 8.0+ attribute extraction through the parser."""

    def test_route_attributes(self, parser):
        code = '''<?php
use Symfony\\Component\\Routing\\Annotation\\Route;

class ApiController
{
    #[Route('/api/users', methods: ['GET'])]
    public function listUsers(): Response {}

    #[Route('/api/users/{id}', methods: ['GET'])]
    public function getUser(int $id): Response {}
}
'''
        result = parser.parse(code, "ApiController.php")
        assert len(result.attributes) >= 1

    def test_custom_attributes(self, parser):
        code = '''<?php
#[Attribute(Attribute::TARGET_METHOD)]
class RateLimit
{
    public function __construct(
        public readonly int $maxAttempts,
        public readonly int $decayMinutes = 1,
    ) {}
}

class Controller
{
    #[RateLimit(maxAttempts: 60)]
    public function index(): Response {}
}
'''
        result = parser.parse(code, "Controller.php")
        assert len(result.attributes) >= 1


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_content(self, parser):
        result = parser.parse("", "empty.php")
        assert isinstance(result, PhpParseResult)

    def test_only_comments(self, parser):
        code = '''<?php
// This is a comment
/* This is a block comment */
/**
 * This is a docblock
 */
'''
        result = parser.parse(code, "comments.php")
        assert isinstance(result, PhpParseResult)

    def test_blade_template(self, parser):
        code = '''@extends('layouts.app')

@section('content')
<div class="container">
    @foreach($users as $user)
        <p>{{ $user->name }}</p>
    @endforeach
</div>
@endsection
'''
        result = parser.parse(code, "index.blade.php")
        assert isinstance(result, PhpParseResult)

    def test_php_with_html(self, parser):
        code = '''<?php
$title = "Hello";
?>
<html>
<body>
<h1><?= $title ?></h1>
</body>
</html>
'''
        result = parser.parse(code, "page.phtml")
        assert isinstance(result, PhpParseResult)

    def test_multiple_types_in_file(self, parser):
        code = '''<?php
namespace App\\Domain;

interface Identifiable
{
    public function getId(): int;
}

trait HasTimestamps
{
    public DateTime $createdAt;
}

enum Priority: int
{
    case Low = 1;
    case High = 2;
}

class Task implements Identifiable
{
    use HasTimestamps;

    public function __construct(
        private readonly int $id,
        private string $title,
        private Priority $priority = Priority::Low,
    ) {}

    public function getId(): int
    {
        return $this->id;
    }
}
'''
        result = parser.parse(code, "domain.php")
        assert len(result.interfaces) >= 1
        assert len(result.traits) >= 1
        assert len(result.enums) >= 1
        assert len(result.classes) >= 1
