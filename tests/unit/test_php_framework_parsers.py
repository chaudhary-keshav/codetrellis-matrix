"""
Tests for PHP framework enhanced parsers — Laravel, Symfony, CodeIgniter, Slim, WordPress.

Part of CodeTrellis v5.3 PHP Framework Support.
"""

import pytest
from codetrellis.laravel_parser_enhanced import EnhancedLaravelParser, LaravelParseResult
from codetrellis.symfony_parser_enhanced import EnhancedSymfonyParser, SymfonyParseResult
from codetrellis.codeigniter_parser_enhanced import EnhancedCodeIgniterParser, CodeIgniterParseResult
from codetrellis.slim_parser_enhanced import EnhancedSlimParser, SlimParseResult
from codetrellis.wordpress_parser_enhanced import EnhancedWordPressParser, WordPressParseResult


# ===== FIXTURES =====

@pytest.fixture
def laravel_parser():
    return EnhancedLaravelParser()


@pytest.fixture
def symfony_parser():
    return EnhancedSymfonyParser()


@pytest.fixture
def codeigniter_parser():
    return EnhancedCodeIgniterParser()


@pytest.fixture
def slim_parser():
    return EnhancedSlimParser()


@pytest.fixture
def wordpress_parser():
    return EnhancedWordPressParser()


# ===== LARAVEL TESTS =====

class TestLaravelParser:
    """Tests for EnhancedLaravelParser."""

    def test_parse_empty_file(self, laravel_parser):
        result = laravel_parser.parse("", "empty.php")
        assert isinstance(result, LaravelParseResult)
        assert result.routes == []
        assert result.controllers == []

    def test_parse_non_laravel_file(self, laravel_parser):
        code = "<?php\nclass Foo { public function bar() {} }"
        result = laravel_parser.parse(code, "foo.php")
        assert result.detected_frameworks == []

    def test_parse_routes(self, laravel_parser):
        code = '''<?php
use Illuminate\\Support\\Facades\\Route;
use App\\Http\\Controllers\\UserController;

Route::get('/users', [UserController::class, 'index'])->name('users.index');
Route::post('/users', [UserController::class, 'store'])->middleware('auth');
Route::get('/about', function () { return view('about'); });
Route::resource('articles', ArticleController::class);
Route::apiResource('posts', PostController::class);

Route::middleware(['auth'])->group(function () {
    Route::get('/dashboard', [DashboardController::class, 'index']);
});
'''
        result = laravel_parser.parse(code, "routes/web.php")
        assert len(result.routes) >= 3
        assert any(r.method == "GET" for r in result.routes)
        assert any(r.path == "/users" for r in result.routes)
        assert 'laravel' in result.detected_frameworks

    def test_parse_controller(self, laravel_parser):
        code = '''<?php
namespace App\\Http\\Controllers;

use App\\Models\\User;
use Illuminate\\Http\\Request;

class UserController extends Controller
{
    public function index()
    {
        $users = User::all();
        return view('users.index', compact('users'));
    }

    public function store(Request $request)
    {
        $user = User::create($request->validated());
        return redirect()->route('users.show', $user);
    }

    public function show(User $user)
    {
        return view('users.show', compact('user'));
    }
}
'''
        result = laravel_parser.parse(code, "app/Http/Controllers/UserController.php")
        assert len(result.controllers) >= 1
        assert result.controllers[0].name == "UserController"

    def test_parse_model(self, laravel_parser):
        code = '''<?php
namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Model;
use Illuminate\\Database\\Eloquent\\Factories\\HasFactory;

class Post extends Model
{
    use HasFactory;

    protected $fillable = ['title', 'body', 'user_id'];
    protected $table = 'posts';

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
        result = laravel_parser.parse(code, "app/Models/Post.php")
        assert len(result.models) >= 1
        assert result.models[0].name == "Post"
        assert 'title' in result.models[0].fillable

    def test_parse_migration(self, laravel_parser):
        code = '''<?php
use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Database\\Schema\\Blueprint;
use Illuminate\\Support\\Facades\\Schema;

class CreatePostsTable extends Migration
{
    public function up()
    {
        Schema::create('posts', function (Blueprint $table) {
            $table->id();
            $table->string('title');
            $table->text('body');
            $table->foreignId('user_id')->constrained();
            $table->timestamps();
        });
    }
}
'''
        result = laravel_parser.parse(code, "database/migrations/2024_01_01_create_posts_table.php")
        assert len(result.migrations) >= 1
        assert "posts" in result.migrations[0].tables_created

    def test_parse_middleware(self, laravel_parser):
        code = '''<?php
namespace App\\Http\\Middleware;

use Closure;
use Illuminate\\Http\\Request;

class EnsureTokenIsValid
{
    public function handle(Request $request, Closure $next)
    {
        if ($request->input('token') !== 'valid-token') {
            return redirect('home');
        }
        return $next($request);
    }
}
'''
        result = laravel_parser.parse(code, "app/Http/Middleware/EnsureTokenIsValid.php")
        assert len(result.middleware) >= 1
        assert result.middleware[0].name == "EnsureTokenIsValid"

    def test_parse_job(self, laravel_parser):
        code = '''<?php
namespace App\\Jobs;

use Illuminate\\Bus\\Queueable;
use Illuminate\\Contracts\\Queue\\ShouldQueue;
use Illuminate\\Foundation\\Bus\\Dispatchable;
use Illuminate\\Queue\\InteractsWithQueue;
use Illuminate\\Queue\\SerializesModels;

class ProcessPodcast implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public function handle()
    {
        // Process the podcast...
    }
}
'''
        result = laravel_parser.parse(code, "app/Jobs/ProcessPodcast.php")
        assert len(result.jobs) >= 1
        assert result.jobs[0].name == "ProcessPodcast"

    def test_parse_event(self, laravel_parser):
        code = '''<?php
namespace App\\Events;

use Illuminate\\Broadcasting\\InteractsWithSockets;
use Illuminate\\Foundation\\Events\\Dispatchable;
use Illuminate\\Queue\\SerializesModels;

class OrderShippedEvent
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    public $order;

    public function __construct($order)
    {
        $this->order = $order;
    }
}
'''
        result = laravel_parser.parse(code, "app/Events/OrderShippedEvent.php")
        assert len(result.events) >= 1
        assert result.events[0].name == "OrderShippedEvent"

    def test_parse_service_provider(self, laravel_parser):
        code = '''<?php
namespace App\\Providers;

use Illuminate\\Support\\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register()
    {
        $this->app->singleton(Service::class, function ($app) {
            return new Service();
        });
    }

    public function boot()
    {
        //
    }
}
'''
        result = laravel_parser.parse(code, "app/Providers/AppServiceProvider.php")
        assert len(result.service_providers) >= 1
        assert result.service_providers[0].name == "AppServiceProvider"

    def test_parse_command(self, laravel_parser):
        code = '''<?php
namespace App\\Console\\Commands;

use Illuminate\\Console\\Command;

class SendEmails extends Command
{
    protected $signature = 'emails:send {user}';
    protected $description = 'Send emails to a user';

    public function handle()
    {
        // Send emails
    }
}
'''
        result = laravel_parser.parse(code, "app/Console/Commands/SendEmails.php")
        assert len(result.commands) >= 1
        assert 'emails:send' in result.commands[0].signature

    def test_detect_ecosystem(self, laravel_parser):
        code = '''<?php
namespace App\\Http\\Livewire;

use Illuminate\\Support\\Facades\\Auth;
use Livewire\\Component;
use Inertia\\Inertia;

class Dashboard extends Component
{
    public function render()
    {
        return Inertia::render('Dashboard');
    }
}
'''
        result = laravel_parser.parse(code, "app/Http/Livewire/Dashboard.php")
        detected = result.detected_frameworks
        assert 'laravel' in detected
        # Should detect livewire or inertia ecosystem
        assert any(fw in detected for fw in ['livewire', 'inertia'])

    def test_version_detection(self, laravel_parser):
        code = '''<?php
use Illuminate\\Support\\Facades\\Route;

// Laravel 11+ Folio
Route::get('/users', function () {
    return view('users');
});
'''
        result = laravel_parser.parse(code, "routes/web.php")
        assert 'laravel' in result.detected_frameworks


# ===== SYMFONY TESTS =====

class TestSymfonyParser:
    """Tests for EnhancedSymfonyParser."""

    def test_parse_empty_file(self, symfony_parser):
        result = symfony_parser.parse("", "empty.php")
        assert isinstance(result, SymfonyParseResult)
        assert result.routes == []
        assert result.controllers == []

    def test_parse_non_symfony_file(self, symfony_parser):
        code = "<?php\nclass Foo { public function bar() {} }"
        result = symfony_parser.parse(code, "foo.php")
        assert result.detected_frameworks == []

    def test_parse_routes_attributes(self, symfony_parser):
        code = '''<?php
namespace App\\Controller;

use Symfony\\Bundle\\FrameworkBundle\\Controller\\AbstractController;
use Symfony\\Component\\Routing\\Attribute\\Route;
use Symfony\\Component\\HttpFoundation\\Response;

class UserController extends AbstractController
{
    #[Route('/users', name: 'user_list', methods: ['GET'])]
    public function list(): Response
    {
        return $this->render('user/list.html.twig');
    }

    #[Route('/users/{id}', name: 'user_show', methods: ['GET'])]
    public function show(int $id): Response
    {
        return $this->render('user/show.html.twig');
    }

    #[Route('/users', name: 'user_create', methods: ['POST'])]
    public function create(): Response
    {
        return new Response('Created', 201);
    }
}
'''
        result = symfony_parser.parse(code, "src/Controller/UserController.php")
        assert len(result.routes) >= 2
        assert any(r.path == "/users" for r in result.routes)
        assert 'symfony' in result.detected_frameworks

    def test_parse_controller(self, symfony_parser):
        code = '''<?php
namespace App\\Controller;

use Symfony\\Bundle\\FrameworkBundle\\Controller\\AbstractController;
use Symfony\\Component\\Routing\\Attribute\\Route;

class ProductController extends AbstractController
{
    #[Route('/products', name: 'product_index')]
    public function index(): Response
    {
        return $this->render('product/index.html.twig');
    }
}
'''
        result = symfony_parser.parse(code, "src/Controller/ProductController.php")
        assert len(result.controllers) >= 1
        assert result.controllers[0].name == "ProductController"

    def test_parse_entity(self, symfony_parser):
        code = '''<?php
namespace App\\Entity;

use Doctrine\\ORM\\Mapping as ORM;

#[ORM\\Entity(repositoryClass: UserRepository::class)]
#[ORM\\Table(name: 'users')]
class User
{
    #[ORM\\Id]
    #[ORM\\GeneratedValue]
    #[ORM\\Column]
    private ?int $id = null;

    #[ORM\\Column(length: 255)]
    private ?string $name = null;

    #[ORM\\Column(length: 180, unique: true)]
    private ?string $email = null;

    #[ORM\\OneToMany(targetEntity: Post::class, mappedBy: 'author')]
    private Collection $posts;
}
'''
        result = symfony_parser.parse(code, "src/Entity/User.php")
        assert len(result.entities) >= 1
        assert result.entities[0].name == "User"
        assert result.entities[0].table_name == "users"

    def test_parse_service(self, symfony_parser):
        code = '''<?php
namespace App\\Service;

use Symfony\\Component\\DependencyInjection\\Attribute\\Autoconfigure;
use Symfony\\Component\\DependencyInjection\\Attribute\\AsAlias;

#[Autoconfigure(tags: ['app.service'])]
class UserService
{
    public function __construct(
        private UserRepository $userRepository
    ) {}

    public function findActive(): array
    {
        return $this->userRepository->findActive();
    }
}
'''
        result = symfony_parser.parse(code, "src/Service/UserService.php")
        # Should detect symfony from DI attributes
        assert 'symfony' in result.detected_frameworks

    def test_parse_command(self, symfony_parser):
        code = '''<?php
namespace App\\Command;

use Symfony\\Component\\Console\\Attribute\\AsCommand;
use Symfony\\Component\\Console\\Command\\Command;

#[AsCommand(
    name: 'app:create-user',
    description: 'Creates a new user.',
)]
class CreateUserCommand extends Command
{
    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        return Command::SUCCESS;
    }
}
'''
        result = symfony_parser.parse(code, "src/Command/CreateUserCommand.php")
        assert len(result.commands) >= 1
        assert result.commands[0].command_name == "app:create-user"

    def test_parse_event_subscriber(self, symfony_parser):
        code = '''<?php
namespace App\\EventSubscriber;

use Symfony\\Component\\EventDispatcher\\EventSubscriberInterface;
use Symfony\\Component\\HttpKernel\\Event\\RequestEvent;

class RequestSubscriber implements EventSubscriberInterface
{
    public static function getSubscribedEvents(): array
    {
        return [
            RequestEvent::class => 'onRequest',
        ];
    }

    public function onRequest(RequestEvent $event): void
    {
        // handle request
    }
}
'''
        result = symfony_parser.parse(code, "src/EventSubscriber/RequestSubscriber.php")
        assert len(result.event_subscribers) >= 1
        assert result.event_subscribers[0].name == "RequestSubscriber"

    def test_parse_form_type(self, symfony_parser):
        code = '''<?php
namespace App\\Form;

use Symfony\\Component\\Form\\AbstractType;
use Symfony\\Component\\Form\\FormBuilderInterface;

class UserType extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options): void
    {
        $builder
            ->add('name')
            ->add('email');
    }
}
'''
        result = symfony_parser.parse(code, "src/Form/UserType.php")
        assert len(result.form_types) >= 1
        assert result.form_types[0].name == "UserType"

    def test_parse_voter(self, symfony_parser):
        code = '''<?php
namespace App\\Security;

use Symfony\\Component\\Security\\Core\\Authorization\\Voter\\Voter;

class PostVoter extends Voter
{
    protected function supports(string $attribute, mixed $subject): bool
    {
        return $subject instanceof Post;
    }

    protected function voteOnAttribute(string $attribute, mixed $subject, TokenInterface $token): bool
    {
        return true;
    }
}
'''
        result = symfony_parser.parse(code, "src/Security/PostVoter.php")
        assert len(result.voters) >= 1
        assert result.voters[0].name == "PostVoter"

    def test_parse_annotations(self, symfony_parser):
        code = '''<?php
namespace App\\Controller;

use Symfony\\Bundle\\FrameworkBundle\\Controller\\AbstractController;

class LegacyController extends AbstractController
{
    /**
     * @Route("/legacy", name="legacy_index", methods={"GET"})
     */
    public function index(): Response
    {
        return $this->render('legacy/index.html.twig');
    }

    /**
     * @Route("/legacy/{id}", name="legacy_show")
     */
    public function show(int $id): Response
    {
        return $this->render('legacy/show.html.twig');
    }
}
'''
        result = symfony_parser.parse(code, "src/Controller/LegacyController.php")
        assert len(result.routes) >= 1
        assert any(r.path == "/legacy" for r in result.routes)


# ===== CODEIGNITER TESTS =====

class TestCodeIgniterParser:
    """Tests for EnhancedCodeIgniterParser."""

    def test_parse_empty_file(self, codeigniter_parser):
        result = codeigniter_parser.parse("", "empty.php")
        assert isinstance(result, CodeIgniterParseResult)
        assert result.routes == []
        assert result.controllers == []

    def test_parse_non_ci_file(self, codeigniter_parser):
        code = "<?php\nclass Foo { public function bar() {} }"
        result = codeigniter_parser.parse(code, "foo.php")
        assert result.detected_frameworks == []

    def test_parse_ci4_controller(self, codeigniter_parser):
        code = '''<?php
namespace App\\Controllers;

use CodeIgniter\\Controller;

class UserController extends BaseController
{
    public function index()
    {
        $users = $this->userModel->findAll();
        return view('users/index', ['users' => $users]);
    }

    public function show($id)
    {
        $user = $this->userModel->find($id);
        return view('users/show', ['user' => $user]);
    }

    public function create()
    {
        $this->userModel->save($this->request->getPost());
        return redirect()->to('/users');
    }
}
'''
        result = codeigniter_parser.parse(code, "app/Controllers/UserController.php")
        assert len(result.controllers) >= 1
        assert result.controllers[0].name == "UserController"
        assert 'codeigniter' in result.detected_frameworks

    def test_parse_ci4_model(self, codeigniter_parser):
        code = '''<?php
namespace App\\Models;

use CodeIgniter\\Model;

class UserModel extends Model
{
    protected $table = 'users';
    protected $primaryKey = 'id';
    protected $allowedFields = ['name', 'email', 'password'];
    protected $validationRules = [
        'name'  => 'required|min_length[3]',
        'email' => 'required|valid_email',
    ];
    protected $returnType = 'App\\Entities\\User';
}
'''
        result = codeigniter_parser.parse(code, "app/Models/UserModel.php")
        assert len(result.models) >= 1
        assert result.models[0].name == "UserModel"
        assert result.models[0].table == "users"

    def test_parse_ci4_routes(self, codeigniter_parser):
        code = '''<?php
namespace App\\Controllers;

use CodeIgniter\\Router\\RouteCollection;

$routes->get('/', 'Home::index');
$routes->get('users', 'UserController::index');
$routes->post('users/create', 'UserController::create');
$routes->put('users/(:num)', 'UserController::update/$1');
$routes->delete('users/(:num)', 'UserController::delete/$1');
$routes->resource('articles');
'''
        result = codeigniter_parser.parse(code, "app/Config/Routes.php")
        assert len(result.routes) >= 3
        assert any(r.path == "users" for r in result.routes)

    def test_parse_ci4_migration(self, codeigniter_parser):
        code = '''<?php
namespace App\\Database\\Migrations;

use CodeIgniter\\Database\\Migration;

class CreateUsersTable extends Migration
{
    public function up()
    {
        $this->forge->addField([
            'id'    => ['type' => 'INT', 'auto_increment' => true],
            'name'  => ['type' => 'VARCHAR', 'constraint' => '100'],
            'email' => ['type' => 'VARCHAR', 'constraint' => '255'],
        ]);
        $this->forge->addKey('id', true);
        $this->forge->createTable('users');
    }

    public function down()
    {
        $this->forge->dropTable('users');
    }
}
'''
        result = codeigniter_parser.parse(code, "app/Database/Migrations/2024-01-01-CreateUsersTable.php")
        assert len(result.migrations) >= 1
        assert result.migrations[0].name == "CreateUsersTable"

    def test_parse_ci4_filter(self, codeigniter_parser):
        code = '''<?php
namespace App\\Filters;

use CodeIgniter\\Filters\\FilterInterface;
use CodeIgniter\\HTTP\\RequestInterface;
use CodeIgniter\\HTTP\\ResponseInterface;

class AuthFilter implements FilterInterface
{
    public function before(RequestInterface $request, $arguments = null)
    {
        if (!session()->get('logged_in')) {
            return redirect()->to('/login');
        }
    }

    public function after(RequestInterface $request, ResponseInterface $response, $arguments = null)
    {
    }
}
'''
        result = codeigniter_parser.parse(code, "app/Filters/AuthFilter.php")
        assert len(result.filters) >= 1
        assert result.filters[0].name == "AuthFilter"

    def test_parse_ci3_controller(self, codeigniter_parser):
        code = '''<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Welcome extends CI_Controller
{
    public function __construct()
    {
        parent::__construct();
        $this->load->model('user_model');
    }

    public function index()
    {
        $this->load->view('welcome_message');
    }
}
'''
        result = codeigniter_parser.parse(code, "application/controllers/Welcome.php")
        assert len(result.controllers) >= 1
        assert result.controllers[0].name == "Welcome"

    def test_parse_ci4_entity(self, codeigniter_parser):
        code = '''<?php
namespace App\\Entities;

use CodeIgniter\\Entity\\Entity;

class User extends Entity
{
    protected $attributes = [
        'id'    => null,
        'name'  => null,
        'email' => null,
    ];
}
'''
        result = codeigniter_parser.parse(code, "app/Entities/User.php")
        assert len(result.entities) >= 1
        assert result.entities[0].name == "User"


# ===== SLIM TESTS =====

class TestSlimParser:
    """Tests for EnhancedSlimParser."""

    def test_parse_empty_file(self, slim_parser):
        result = slim_parser.parse("", "empty.php")
        assert isinstance(result, SlimParseResult)
        assert result.routes == []
        assert result.middleware == []

    def test_parse_non_slim_file(self, slim_parser):
        code = "<?php\nclass Foo { public function bar() {} }"
        result = slim_parser.parse(code, "foo.php")
        assert result.detected_frameworks == []

    def test_parse_routes(self, slim_parser):
        code = '''<?php
use Slim\\Factory\\AppFactory;

$app = AppFactory::create();

$app->get('/', function ($request, $response) {
    $response->getBody()->write('Hello');
    return $response;
});

$app->get('/users', function ($request, $response) {
    return $response->withJson($users);
});

$app->post('/users', function ($request, $response) {
    $data = $request->getParsedBody();
    return $response->withStatus(201);
});

$app->put('/users/{id}', function ($request, $response, $args) {
    return $response;
});

$app->delete('/users/{id}', function ($request, $response, $args) {
    return $response->withStatus(204);
});

$app->run();
'''
        result = slim_parser.parse(code, "public/index.php")
        assert len(result.routes) >= 4
        assert any(r.method == "GET" for r in result.routes)
        assert any(r.path == "/users" for r in result.routes)
        assert 'slim' in result.detected_frameworks

    def test_parse_middleware(self, slim_parser):
        code = '''<?php
use Slim\\Factory\\AppFactory;
use Psr\\Http\\Server\\MiddlewareInterface;

$app = AppFactory::create();

$app->add(new JsonBodyParsingMiddleware());
$app->add(new CorsMiddleware());
$app->addErrorMiddleware(true, true, true);
'''
        result = slim_parser.parse(code, "public/index.php")
        assert len(result.middleware) >= 1

    def test_parse_route_groups(self, slim_parser):
        code = '''<?php
use Slim\\Factory\\AppFactory;

$app = AppFactory::create();

$app->group('/api/v1', function ($group) {
    $group->get('/users', 'UserController:list');
    $group->post('/users', 'UserController:create');
});

$app->group('/admin', function ($group) {
    $group->get('/dashboard', 'AdminController:dashboard');
});
'''
        result = slim_parser.parse(code, "public/index.php")
        assert len(result.route_groups) >= 1

    def test_parse_di_bindings(self, slim_parser):
        code = '''<?php
use DI\\ContainerBuilder;
use Slim\\Factory\\AppFactory;

$containerBuilder = new ContainerBuilder();

$containerBuilder->addDefinitions([
    'db' => function ($container) {
        return new PDO('mysql:host=localhost;dbname=test', 'root', 'pass');
    },
    UserRepository::class => function ($container) {
        return new UserRepository($container->get('db'));
    },
]);

$container = $containerBuilder->build();
AppFactory::setContainer($container);
$app = AppFactory::create();
'''
        result = slim_parser.parse(code, "public/index.php")
        # Should detect slim + php_di
        assert 'slim' in result.detected_frameworks

    def test_parse_controller_class(self, slim_parser):
        code = '''<?php
namespace App\\Controllers;

use Slim\\Http\\Response;
use Slim\\Http\\ServerRequest as Request;

class UserController
{
    public function __invoke(Request $request, Response $response): Response
    {
        $response->getBody()->write('User List');
        return $response;
    }
}
'''
        result = slim_parser.parse(code, "src/Controllers/UserController.php")
        assert len(result.controllers) >= 1
        assert result.controllers[0].name == "UserController"


# ===== WORDPRESS TESTS =====

class TestWordPressParser:
    """Tests for EnhancedWordPressParser."""

    def test_parse_empty_file(self, wordpress_parser):
        result = wordpress_parser.parse("", "empty.php")
        assert isinstance(result, WordPressParseResult)
        assert result.hooks == []
        assert result.post_types == []

    def test_parse_non_wp_file(self, wordpress_parser):
        code = "<?php\nclass Foo { public function bar() {} }"
        result = wordpress_parser.parse(code, "foo.php")
        assert result.detected_frameworks == []

    def test_parse_hooks(self, wordpress_parser):
        code = '''<?php
/**
 * Plugin Name: Test Plugin
 */

add_action('init', 'my_plugin_init');
add_action('admin_menu', [$this, 'add_admin_menu'], 20);
add_action('wp_enqueue_scripts', 'my_enqueue_assets');

add_filter('the_content', 'my_content_filter');
add_filter('wp_title', 'my_title_filter', 10, 2);
'''
        result = wordpress_parser.parse(code, "my-plugin/my-plugin.php")
        assert len(result.hooks) >= 4
        actions = [h for h in result.hooks if h.kind == 'action']
        filters = [h for h in result.hooks if h.kind == 'filter']
        assert len(actions) >= 3
        assert len(filters) >= 2
        assert any(h.name == 'init' for h in actions)
        assert any(h.name == 'the_content' for h in filters)
        assert 'wordpress' in result.detected_frameworks
        assert result.is_plugin

    def test_parse_custom_post_types(self, wordpress_parser):
        code = '''<?php
add_action('init', 'register_book_cpt');

function register_book_cpt() {
    register_post_type('book', [
        'label' => 'Books',
        'public' => true,
        'has_archive' => true,
        'show_in_rest' => true,
        'supports' => ['title', 'editor', 'thumbnail'],
    ]);
}
'''
        result = wordpress_parser.parse(code, "my-plugin/cpt.php")
        assert len(result.post_types) >= 1
        assert result.post_types[0].name == "book"
        assert result.post_types[0].show_in_rest

    def test_parse_taxonomies(self, wordpress_parser):
        code = '''<?php
add_action('init', 'register_genre_taxonomy');

function register_genre_taxonomy() {
    register_taxonomy('genre', ['book'], [
        'hierarchical' => true,
        'show_in_rest' => true,
    ]);
    register_taxonomy('author_tag', 'book', [
        'hierarchical' => false,
    ]);
}
'''
        result = wordpress_parser.parse(code, "my-plugin/taxonomies.php")
        assert len(result.taxonomies) >= 1
        assert result.taxonomies[0].name == "genre"

    def test_parse_shortcodes(self, wordpress_parser):
        code = '''<?php
add_shortcode('gallery', 'render_gallery_shortcode');
add_shortcode('contact_form', [$this, 'render_contact_form']);
'''
        result = wordpress_parser.parse(code, "my-plugin/shortcodes.php")
        assert len(result.shortcodes) >= 2
        assert any(sc.tag == 'gallery' for sc in result.shortcodes)

    def test_parse_rest_routes(self, wordpress_parser):
        code = '''<?php
add_action('rest_api_init', function () {
    register_rest_route('myplugin/v1', '/items', [
        'methods'  => 'GET',
        'callback' => 'get_items',
        'permission_callback' => '__return_true',
    ]);
    register_rest_route('myplugin/v1', '/items/(?P<id>\\\\d+)', [
        'methods'  => WP_REST_Server::READABLE,
        'callback' => 'get_single_item',
        'permission_callback' => 'check_permissions',
    ]);
});
'''
        result = wordpress_parser.parse(code, "my-plugin/rest-api.php")
        assert len(result.rest_routes) >= 2
        assert result.rest_routes[0].namespace == "myplugin/v1"

    def test_parse_blocks(self, wordpress_parser):
        code = '''<?php
add_action('init', function () {
    register_block_type('myplugin/hero', [
        'render_callback' => 'render_hero_block',
    ]);
    register_block_type('myplugin/testimonial', [
        'render_callback' => [$this, 'render_testimonial'],
    ]);
});
'''
        result = wordpress_parser.parse(code, "my-plugin/blocks.php")
        assert len(result.blocks) >= 2
        assert any(b.name == 'myplugin/hero' for b in result.blocks)
        assert result.blocks[0].is_dynamic

    def test_parse_widgets(self, wordpress_parser):
        code = '''<?php
class My_Featured_Widget extends WP_Widget
{
    public function __construct()
    {
        parent::__construct('my_featured', 'Featured Posts');
    }

    public function widget($args, $instance)
    {
        echo $args['before_widget'];
        echo '<h3>' . esc_html($instance['title']) . '</h3>';
        echo $args['after_widget'];
    }

    public function form($instance) {}
    public function update($new_instance, $old_instance) {}
}
'''
        result = wordpress_parser.parse(code, "my-plugin/widgets.php")
        assert len(result.widgets) >= 1
        assert result.widgets[0].name == "My_Featured_Widget"

    def test_parse_admin_pages(self, wordpress_parser):
        code = '''<?php
add_action('admin_menu', function () {
    add_menu_page('My Plugin', 'My Plugin', 'manage_options', 'my-plugin');
    add_submenu_page('my-plugin', 'Settings', 'Settings', 'manage_options', 'my-plugin-settings');
});
'''
        result = wordpress_parser.parse(code, "my-plugin/admin.php")
        assert len(result.admin_pages) >= 2
        assert any(p.slug == 'my-plugin' for p in result.admin_pages)

    def test_parse_enqueues(self, wordpress_parser):
        code = '''<?php
add_action('wp_enqueue_scripts', function () {
    wp_enqueue_script('my-plugin-js', plugins_url('js/app.js', __FILE__));
    wp_enqueue_style('my-plugin-css', plugins_url('css/style.css', __FILE__));
});
'''
        result = wordpress_parser.parse(code, "my-plugin/assets.php")
        assert len(result.enqueues) >= 2
        scripts = [e for e in result.enqueues if e.kind == 'script']
        styles = [e for e in result.enqueues if e.kind == 'style']
        assert len(scripts) >= 1
        assert len(styles) >= 1

    def test_parse_cron(self, wordpress_parser):
        code = '''<?php
register_activation_hook(__FILE__, function () {
    if (!wp_next_scheduled('my_daily_event')) {
        wp_schedule_event(time(), 'daily', 'my_daily_event');
    }
});

add_action('my_daily_event', 'do_daily_task');
'''
        result = wordpress_parser.parse(code, "my-plugin/cron.php")
        assert len(result.cron_events) >= 1
        assert result.cron_events[0].recurrence == 'daily'

    def test_parse_ajax(self, wordpress_parser):
        code = '''<?php
add_action('wp_ajax_my_action', 'handle_my_action');
add_action('wp_ajax_nopriv_public_action', 'handle_public_action');
'''
        result = wordpress_parser.parse(code, "my-plugin/ajax.php")
        assert len(result.ajax_handlers) >= 2
        assert any(aj.action == 'my_action' for aj in result.ajax_handlers)
        assert any(aj.is_nopriv for aj in result.ajax_handlers)

    def test_parse_meta_boxes(self, wordpress_parser):
        code = '''<?php
add_action('add_meta_boxes', function () {
    add_meta_box('book_details', 'Book Details', 'render_book_meta_box', 'book');
});
'''
        result = wordpress_parser.parse(code, "my-plugin/meta-boxes.php")
        assert len(result.meta_boxes) >= 1
        assert result.meta_boxes[0].id == "book_details"

    def test_parse_settings(self, wordpress_parser):
        code = '''<?php
add_action('admin_init', function () {
    register_setting('my_plugin_options', 'my_plugin_api_key');
    register_setting('my_plugin_options', 'my_plugin_cache_ttl');
    add_settings_field('api_key_field', 'API Key', 'render_api_key_field', 'my-plugin', 'general');
});
'''
        result = wordpress_parser.parse(code, "my-plugin/settings.php")
        assert len(result.settings) >= 2
        assert any(s.option_name == 'my_plugin_api_key' for s in result.settings)

    def test_theme_detection(self, wordpress_parser):
        code = '''<?php
/**
 * Theme Name: My Custom Theme
 * Theme URI: https://example.com
 * Description: A custom WordPress theme
 * Version: 1.0
 */

add_action('after_setup_theme', function () {
    add_theme_support('post-thumbnails');
    add_theme_support('title-tag');
});
'''
        result = wordpress_parser.parse(code, "wp-content/themes/my-theme/functions.php")
        assert result.is_theme
        assert 'wordpress' in result.detected_frameworks

    def test_woocommerce_detection(self, wordpress_parser):
        code = '''<?php
add_action('woocommerce_before_shop_loop', 'my_custom_banner');
WC()->cart->add_to_cart($product_id);
'''
        result = wordpress_parser.parse(code, "my-plugin/wc-integration.php")
        assert 'woocommerce' in result.detected_frameworks

    def test_acf_detection(self, wordpress_parser):
        code = '''<?php
add_action('init', function() {
    $value = get_field('hero_image');
    the_field('subtitle');
});
'''
        result = wordpress_parser.parse(code, "my-theme/template-parts/hero.php")
        assert 'acf' in result.detected_frameworks
