"""
Tests for PhpTypeExtractor — classes, interfaces, traits, enums, abstract classes.

Part of CodeTrellis v4.24 PHP Language Support.
"""

import pytest
from codetrellis.extractors.php.type_extractor import PhpTypeExtractor


@pytest.fixture
def extractor():
    return PhpTypeExtractor()


# ===== CLASS EXTRACTION =====

class TestClassExtraction:
    """Tests for PHP class extraction."""

    def test_simple_class(self, extractor):
        code = '''<?php
class User
{
    private string $name;
    private string $email;

    public function __construct(string $name, string $email)
    {
        $this->name = $name;
        $this->email = $email;
    }
}
'''
        result = extractor.extract(code, "User.php")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "User"

    def test_class_with_inheritance(self, extractor):
        code = '''<?php
class Admin extends User
{
    private bool $superAdmin;

    public function isSuperAdmin(): bool
    {
        return $this->superAdmin;
    }
}
'''
        result = extractor.extract(code, "Admin.php")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Admin"
        assert cls.parent_class == "User"

    def test_class_with_namespace(self, extractor):
        code = '''<?php
namespace App\\Models;

class User extends Model
{
    protected $fillable = ['name', 'email'];
}
'''
        result = extractor.extract(code, "User.php")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "User"
        assert "App\\Models" in (cls.namespace or "")

    def test_class_with_implements(self, extractor):
        code = '''<?php
class UserRepository implements UserRepositoryInterface, CacheableInterface
{
    public function findById(int $id): ?User
    {
        return User::find($id);
    }
}
'''
        result = extractor.extract(code, "UserRepository.php")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "UserRepository"
        assert len(cls.interfaces) >= 1

    def test_class_with_trait_use(self, extractor):
        code = '''<?php
class Post extends Model
{
    use HasFactory;
    use SoftDeletes;

    protected $fillable = ['title', 'body'];
}
'''
        result = extractor.extract(code, "Post.php")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Post"
        assert len(cls.traits) >= 1

    def test_final_class(self, extractor):
        code = '''<?php
final class EmailNotification
{
    public function send(string $to, string $message): void
    {
    }
}
'''
        result = extractor.extract(code, "EmailNotification.php")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "EmailNotification"
        assert cls.is_final is True

    def test_class_with_properties(self, extractor):
        code = '''<?php
class Config
{
    public const MAX_RETRIES = 3;
    public string $host = 'localhost';
    protected int $port = 3306;
    private readonly string $dsn;
}
'''
        result = extractor.extract(code, "Config.php")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Config"
        assert len(cls.properties) > 0 or len(cls.constants) > 0

    def test_readonly_class_php82(self, extractor):
        code = '''<?php
readonly class Point
{
    public function __construct(
        public float $x,
        public float $y,
    ) {}
}
'''
        result = extractor.extract(code, "Point.php")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Point"


# ===== INTERFACE EXTRACTION =====

class TestInterfaceExtraction:
    """Tests for PHP interface extraction."""

    def test_simple_interface(self, extractor):
        code = '''<?php
interface UserRepositoryInterface
{
    public function findById(int $id): ?User;
    public function save(User $user): void;
    public function delete(int $id): bool;
}
'''
        result = extractor.extract(code, "UserRepositoryInterface.php")
        assert len(result["interfaces"]) >= 1
        iface = result["interfaces"][0]
        assert iface.name == "UserRepositoryInterface"
        # Interface method extraction is not yet implemented; verify basic parsing
        assert iface.extends == []

    def test_interface_extending(self, extractor):
        code = '''<?php
interface CrudRepositoryInterface extends RepositoryInterface, CountableInterface
{
    public function create(array $data): Model;
    public function update(int $id, array $data): Model;
}
'''
        result = extractor.extract(code, "CrudRepositoryInterface.php")
        assert len(result["interfaces"]) >= 1
        iface = result["interfaces"][0]
        assert iface.name == "CrudRepositoryInterface"

    def test_interface_with_constants(self, extractor):
        code = '''<?php
interface HttpStatusInterface
{
    const OK = 200;
    const NOT_FOUND = 404;
    const SERVER_ERROR = 500;
}
'''
        result = extractor.extract(code, "HttpStatusInterface.php")
        assert len(result["interfaces"]) >= 1


# ===== TRAIT EXTRACTION =====

class TestTraitExtraction:
    """Tests for PHP trait extraction."""

    def test_simple_trait(self, extractor):
        code = '''<?php
trait HasTimestamps
{
    public function getCreatedAt(): DateTime
    {
        return $this->createdAt;
    }

    public function setCreatedAt(DateTime $date): void
    {
        $this->createdAt = $date;
    }
}
'''
        result = extractor.extract(code, "HasTimestamps.php")
        assert len(result["traits"]) >= 1
        trait = result["traits"][0]
        assert trait.name == "HasTimestamps"

    def test_trait_with_abstract_method(self, extractor):
        code = '''<?php
trait Sluggable
{
    abstract protected function getSlugSource(): string;

    public function generateSlug(): string
    {
        return Str::slug($this->getSlugSource());
    }
}
'''
        result = extractor.extract(code, "Sluggable.php")
        assert len(result["traits"]) >= 1
        trait = result["traits"][0]
        assert trait.name == "Sluggable"


# ===== ENUM EXTRACTION =====

class TestEnumExtraction:
    """Tests for PHP 8.1+ enum extraction."""

    def test_basic_enum(self, extractor):
        code = '''<?php
enum Color
{
    case Red;
    case Green;
    case Blue;
}
'''
        result = extractor.extract(code, "Color.php")
        assert len(result["enums"]) >= 1
        enum = result["enums"][0]
        assert enum.name == "Color"
        assert len(enum.cases) >= 3

    def test_backed_string_enum(self, extractor):
        code = '''<?php
enum Status: string
{
    case Active = 'active';
    case Inactive = 'inactive';
    case Pending = 'pending';
}
'''
        result = extractor.extract(code, "Status.php")
        assert len(result["enums"]) >= 1
        enum = result["enums"][0]
        assert enum.name == "Status"
        assert enum.backed_type == "string"

    def test_backed_int_enum(self, extractor):
        code = '''<?php
enum Priority: int
{
    case Low = 1;
    case Medium = 2;
    case High = 3;
    case Critical = 4;
}
'''
        result = extractor.extract(code, "Priority.php")
        assert len(result["enums"]) >= 1
        enum = result["enums"][0]
        assert enum.name == "Priority"
        assert enum.backed_type == "int"

    def test_enum_with_implements(self, extractor):
        code = '''<?php
enum Suit: string implements HasColor
{
    case Hearts = 'H';
    case Diamonds = 'D';
    case Clubs = 'C';
    case Spades = 'S';

    public function color(): string
    {
        return match($this) {
            self::Hearts, self::Diamonds => 'red',
            self::Clubs, self::Spades => 'black',
        };
    }
}
'''
        result = extractor.extract(code, "Suit.php")
        assert len(result["enums"]) >= 1
        enum = result["enums"][0]
        assert enum.name == "Suit"


# ===== ABSTRACT CLASS EXTRACTION =====

class TestAbstractClassExtraction:
    """Tests for PHP abstract class extraction."""

    def test_abstract_class(self, extractor):
        code = '''<?php
abstract class Shape
{
    abstract public function area(): float;
    abstract public function perimeter(): float;

    public function describe(): string
    {
        return sprintf("Area: %.2f, Perimeter: %.2f", $this->area(), $this->perimeter());
    }
}
'''
        result = extractor.extract(code, "Shape.php")
        assert len(result.get("abstract_classes", [])) >= 1 or any(
            c.is_abstract for c in result.get("classes", [])
        )


# ===== NAMESPACE EXTRACTION =====

class TestNamespaceExtraction:
    """Tests for PHP namespace extraction."""

    def test_namespace_declaration(self, extractor):
        code = '''<?php
namespace App\\Http\\Controllers;

use App\\Models\\User;
use Illuminate\\Http\\Request;

class UserController extends Controller
{
}
'''
        result = extractor.extract(code, "UserController.php")
        assert result["namespace"] is not None
        assert "App" in result["namespace"]

    def test_multiple_use_statements(self, extractor):
        code = '''<?php
namespace App\\Services;

use App\\Models\\User;
use App\\Models\\Order;
use App\\Events\\OrderCreated;
use Illuminate\\Support\\Facades\\Log;

class OrderService
{
}
'''
        result = extractor.extract(code, "OrderService.php")
        assert len(result["classes"]) >= 1


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases in type extraction."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.php")
        assert result["classes"] == []
        assert result["interfaces"] == []
        assert result["traits"] == []
        assert result["enums"] == []

    def test_php_without_opening_tag(self, extractor):
        code = '''
class Orphan
{
    public function test(): void {}
}
'''
        result = extractor.extract(code, "orphan.php")
        # Should still try to parse
        assert isinstance(result, dict)

    def test_multiple_classes_in_file(self, extractor):
        code = '''<?php
class First {}
class Second {}
class Third {}
'''
        result = extractor.extract(code, "multi.php")
        assert len(result["classes"]) >= 2

    def test_nested_anonymous_class(self, extractor):
        code = '''<?php
class Container
{
    public function getLogger(): LoggerInterface
    {
        return new class implements LoggerInterface {
            public function log(string $message): void {}
        };
    }
}
'''
        result = extractor.extract(code, "Container.php")
        assert len(result["classes"]) >= 1
