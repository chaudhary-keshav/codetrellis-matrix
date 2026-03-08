"""
Tests for ScalaTypeExtractor — classes, traits, objects, enums, type aliases, givens.

Part of CodeTrellis v4.25 Scala Language Support.
"""

import pytest
from codetrellis.extractors.scala.type_extractor import ScalaTypeExtractor


@pytest.fixture
def extractor():
    return ScalaTypeExtractor()


# ===== CLASS EXTRACTION =====

class TestClassExtraction:
    """Tests for Scala class extraction."""

    def test_simple_class(self, extractor):
        code = '''
class User(val name: String, val email: String) {
  def greet: String = s"Hello, $name"
}
'''
        result = extractor.extract(code, "User.scala")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "User"

    def test_case_class(self, extractor):
        code = '''
case class Point(x: Double, y: Double)
'''
        result = extractor.extract(code, "Point.scala")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Point"
        assert cls.is_case is True

    def test_abstract_class(self, extractor):
        code = '''
abstract class Shape {
  def area: Double
  def perimeter: Double
}
'''
        result = extractor.extract(code, "Shape.scala")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Shape"
        assert cls.is_abstract is True

    def test_sealed_abstract_class(self, extractor):
        code = '''
sealed abstract class Tree[+A]
case class Leaf[A](value: A) extends Tree[A]
case class Branch[A](left: Tree[A], right: Tree[A]) extends Tree[A]
'''
        result = extractor.extract(code, "Tree.scala")
        classes = result["classes"]
        sealed_classes = [c for c in classes if c.name == "Tree"]
        assert len(sealed_classes) >= 1
        assert sealed_classes[0].is_sealed is True

    def test_class_with_extends(self, extractor):
        code = '''
class Admin(name: String, val role: String) extends User(name, role + "@admin") with Serializable
'''
        result = extractor.extract(code, "Admin.scala")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Admin"

    def test_implicit_class(self, extractor):
        code = '''
implicit class RichString(val s: String) extends AnyVal {
  def toSlug: String = s.toLowerCase.replaceAll("\\\\s+", "-")
}
'''
        result = extractor.extract(code, "RichString.scala")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "RichString"

    def test_value_class(self, extractor):
        code = '''
class UserId(val value: Long) extends AnyVal
'''
        result = extractor.extract(code, "UserId.scala")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "UserId"

    def test_class_with_annotations(self, extractor):
        code = '''
@Singleton
@Inject
class UserService(db: Database) {
  def findAll: List[User] = ???
}
'''
        result = extractor.extract(code, "UserService.scala")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "UserService"


# ===== TRAIT EXTRACTION =====

class TestTraitExtraction:
    """Tests for Scala trait extraction."""

    def test_simple_trait(self, extractor):
        code = '''
trait Printable {
  def print(): Unit
  def prettyPrint(): Unit = println(toString)
}
'''
        result = extractor.extract(code, "Printable.scala")
        assert len(result["traits"]) >= 1
        t = result["traits"][0]
        assert t.name == "Printable"

    def test_sealed_trait(self, extractor):
        code = '''
sealed trait Shape
case class Circle(radius: Double) extends Shape
case class Rectangle(width: Double, height: Double) extends Shape
'''
        result = extractor.extract(code, "Shape.scala")
        traits = result["traits"]
        sealed_traits = [t for t in traits if t.name == "Shape"]
        assert len(sealed_traits) >= 1
        assert sealed_traits[0].is_sealed is True

    def test_trait_with_generic(self, extractor):
        code = '''
trait Repository[F[_], A] {
  def findById(id: Long): F[Option[A]]
  def findAll: F[List[A]]
  def save(entity: A): F[A]
}
'''
        result = extractor.extract(code, "Repository.scala")
        assert len(result["traits"]) >= 1
        t = result["traits"][0]
        assert t.name == "Repository"

    def test_trait_with_self_type(self, extractor):
        code = '''
trait Logging { self: Actor =>
  def log(msg: String): Unit = println(msg)
}
'''
        result = extractor.extract(code, "Logging.scala")
        assert len(result["traits"]) >= 1
        t = result["traits"][0]
        assert t.name == "Logging"


# ===== OBJECT EXTRACTION =====

class TestObjectExtraction:
    """Tests for Scala object extraction."""

    def test_simple_object(self, extractor):
        code = '''
object MathUtils {
  def square(x: Int): Int = x * x
  def cube(x: Int): Int = x * x * x
}
'''
        result = extractor.extract(code, "MathUtils.scala")
        assert len(result["objects"]) >= 1
        obj = result["objects"][0]
        assert obj.name == "MathUtils"

    def test_case_object(self, extractor):
        code = '''
case object NotFound extends HttpError
'''
        result = extractor.extract(code, "HttpError.scala")
        assert len(result["objects"]) >= 1
        obj = result["objects"][0]
        assert obj.name == "NotFound"
        assert obj.is_case is True

    def test_companion_object(self, extractor):
        code = '''
case class User(name: String, email: String)
object User {
  def apply(name: String): User = User(name, s"$name@example.com")
}
'''
        result = extractor.extract(code, "User.scala")
        assert len(result["objects"]) >= 1
        obj = [o for o in result["objects"] if o.name == "User"]
        assert len(obj) >= 1

    def test_package_object(self, extractor):
        code = '''
package object domain {
  type UserId = Long
  type Email = String
}
'''
        result = extractor.extract(code, "package.scala")
        objects = result["objects"]
        pkg_objects = [o for o in objects if o.is_package_object]
        assert len(pkg_objects) >= 1


# ===== ENUM EXTRACTION =====

class TestEnumExtraction:
    """Tests for Scala enum extraction."""

    def test_scala3_enum(self, extractor):
        code = '''
enum Color:
  case Red, Green, Blue
'''
        result = extractor.extract(code, "Color.scala")
        assert len(result["enums"]) >= 1
        e = result["enums"][0]
        assert e.name == "Color"

    def test_scala3_enum_with_params(self, extractor):
        code = '''
enum Planet(mass: Double, radius: Double):
  case Mercury extends Planet(3.303e+23, 2.4397e6)
  case Venus extends Planet(4.869e+24, 6.0518e6)
  case Earth extends Planet(5.976e+24, 6.37814e6)
'''
        result = extractor.extract(code, "Planet.scala")
        assert len(result["enums"]) >= 1
        e = result["enums"][0]
        assert e.name == "Planet"

    def test_scala2_sealed_trait_enum(self, extractor):
        code = '''
sealed trait Direction
case object North extends Direction
case object South extends Direction
case object East extends Direction
case object West extends Direction
'''
        result = extractor.extract(code, "Direction.scala")
        # Should detect as either enum or sealed trait + case objects
        has_sealed = len([t for t in result["traits"] if t.is_sealed]) >= 1
        has_enum = len(result["enums"]) >= 1
        assert has_sealed or has_enum


# ===== TYPE ALIAS EXTRACTION =====

class TestTypeAliasExtraction:
    """Tests for Scala type alias extraction."""

    def test_simple_type_alias(self, extractor):
        code = '''
type UserId = Long
type Result[A] = Either[Error, A]
'''
        result = extractor.extract(code, "types.scala")
        assert len(result["type_aliases"]) >= 1

    def test_opaque_type(self, extractor):
        code = '''
opaque type Temperature = Double
object Temperature:
  def apply(d: Double): Temperature = d
'''
        result = extractor.extract(code, "Temperature.scala")
        aliases = result["type_aliases"]
        opaque = [a for a in aliases if "Temperature" in a.name]
        assert len(opaque) >= 1


# ===== GIVEN EXTRACTION =====

class TestGivenExtraction:
    """Tests for Scala 3 given extraction."""

    def test_given_instance(self, extractor):
        code = '''
given intOrdering: Ordering[Int] = Ordering.Int
'''
        result = extractor.extract(code, "givens.scala")
        assert len(result["givens"]) >= 1

    def test_given_with_clause(self, extractor):
        code = '''
given Ordering[User] with
  def compare(a: User, b: User): Int = a.name.compare(b.name)
'''
        result = extractor.extract(code, "givens.scala")
        assert len(result["givens"]) >= 1

    def test_anonymous_given(self, extractor):
        code = '''
given Conversion[String, Int] = _.toInt
'''
        result = extractor.extract(code, "givens.scala")
        assert len(result["givens"]) >= 1


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases in type extraction."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.scala")
        assert result["classes"] == []
        assert result["traits"] == []
        assert result["objects"] == []
        assert result["enums"] == []
        assert result["type_aliases"] == []
        assert result["givens"] == []

    def test_comment_only_file(self, extractor):
        code = '''
// This is a comment
/* Block comment */
/** Scaladoc comment */
'''
        result = extractor.extract(code, "comments.scala")
        assert result["classes"] == []

    def test_multiple_classes_in_file(self, extractor):
        code = '''
class Foo
class Bar
class Baz
'''
        result = extractor.extract(code, "multi.scala")
        assert len(result["classes"]) >= 3
