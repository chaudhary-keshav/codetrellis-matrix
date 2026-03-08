"""
Tests for DartTypeExtractor — classes, mixins, enums, extensions, extension types, typedefs.

Part of CodeTrellis v4.27 Dart Language Support.
"""

import pytest
from codetrellis.extractors.dart.type_extractor import DartTypeExtractor


@pytest.fixture
def extractor():
    return DartTypeExtractor()


# ===== CLASS EXTRACTION =====

class TestClassExtraction:
    """Tests for Dart class extraction."""

    def test_simple_class(self, extractor):
        code = '''
class User {
  final String id;
  final String name;
  User(this.id, this.name);
}
'''
        result = extractor.extract(code, "user.dart")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "User"

    def test_abstract_class(self, extractor):
        code = '''
abstract class Repository<T> {
  Future<T> findById(String id);
  Future<List<T>> findAll();
  Future<void> save(T entity);
}
'''
        result = extractor.extract(code, "repository.dart")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "Repository"
        assert c.is_abstract is True

    def test_sealed_class(self, extractor):
        code = '''
sealed class Shape {}
class Circle extends Shape {
  final double radius;
  Circle(this.radius);
}
class Square extends Shape {
  final double side;
  Square(this.side);
}
'''
        result = extractor.extract(code, "shape.dart")
        classes = result["classes"]
        sealed = [c for c in classes if c.name == "Shape"]
        assert len(sealed) >= 1
        assert sealed[0].is_sealed is True

    def test_base_class(self, extractor):
        code = '''
base class Animal {
  final String name;
  Animal(this.name);
}
'''
        result = extractor.extract(code, "animal.dart")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "Animal"
        assert c.is_base is True

    def test_interface_class(self, extractor):
        code = '''
interface class Describable {
  String describe();
}
'''
        result = extractor.extract(code, "describable.dart")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "Describable"
        assert c.is_interface is True

    def test_final_class(self, extractor):
        code = '''
final class Config {
  final String key;
  final String value;
  Config(this.key, this.value);
}
'''
        result = extractor.extract(code, "config.dart")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "Config"
        assert c.is_final is True

    def test_mixin_class(self, extractor):
        code = '''
mixin class LoggerMixin {
  void log(String msg) => print(msg);
}
'''
        result = extractor.extract(code, "logger.dart")
        # mixin class can appear as class with is_mixin_class=True
        classes = result.get("classes", [])
        if classes:
            assert any(c.name == "LoggerMixin" for c in classes)

    def test_class_with_mixins(self, extractor):
        code = '''
class MyWidget extends StatelessWidget with LogMixin, CacheMixin {
  @override
  Widget build(BuildContext context) => Container();
}
'''
        result = extractor.extract(code, "widget.dart")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "MyWidget"
        assert "StatelessWidget" in (c.superclass or "")

    def test_class_with_implements(self, extractor):
        code = '''
class UserService implements AuthService, NotificationService {
  void authenticate() {}
  void notify() {}
}
'''
        result = extractor.extract(code, "service.dart")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "UserService"

    def test_class_fields(self, extractor):
        code = '''
class Product {
  final String id;
  late String? description;
  static int count = 0;
  final double price;
}
'''
        result = extractor.extract(code, "product.dart")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "Product"
        fields = c.fields
        assert len(fields) >= 2


# ===== MIXIN EXTRACTION =====

class TestMixinExtraction:
    """Tests for Dart mixin extraction."""

    def test_simple_mixin(self, extractor):
        code = '''
mixin Serializable {
  Map<String, dynamic> toMap();
  factory Serializable.fromMap(Map<String, dynamic> map);
}
'''
        result = extractor.extract(code, "serializable.dart")
        assert len(result["mixins"]) >= 1
        m = result["mixins"][0]
        assert m.name == "Serializable"

    def test_mixin_with_on(self, extractor):
        code = '''
mixin LogMixin on Service {
  void log(String message) {
    print('[${runtimeType}] $message');
  }
}
'''
        result = extractor.extract(code, "log_mixin.dart")
        assert len(result["mixins"]) >= 1
        m = result["mixins"][0]
        assert m.name == "LogMixin"
        assert "Service" in m.on_types

    def test_mixin_with_implements(self, extractor):
        code = '''
mixin CacheMixin on Repository implements Disposable {
  void dispose() {}
  void clearCache() {}
}
'''
        result = extractor.extract(code, "cache_mixin.dart")
        assert len(result["mixins"]) >= 1
        m = result["mixins"][0]
        assert m.name == "CacheMixin"


# ===== ENUM EXTRACTION =====

class TestEnumExtraction:
    """Tests for Dart enum extraction."""

    def test_simple_enum(self, extractor):
        code = '''
enum Color {
  red,
  green,
  blue,
}
'''
        result = extractor.extract(code, "color.dart")
        assert len(result["enums"]) >= 1
        e = result["enums"][0]
        assert e.name == "Color"

    def test_enhanced_enum(self, extractor):
        code = '''
enum Planet {
  mercury(3.303e+23, 2.4397e6),
  venus(4.869e+24, 6.0518e6),
  earth(5.976e+24, 6.37814e6);

  const Planet(this.mass, this.radius);
  final double mass;
  final double radius;

  double get surfaceGravity => 6.67430e-11 * mass / (radius * radius);
}
'''
        result = extractor.extract(code, "planet.dart")
        assert len(result["enums"]) >= 1
        e = result["enums"][0]
        assert e.name == "Planet"
        assert e.has_members is True

    def test_enum_with_mixin(self, extractor):
        code = '''
enum Status with Comparable<Status> {
  active,
  inactive,
  deleted;

  @override
  int compareTo(Status other) => index - other.index;
}
'''
        result = extractor.extract(code, "status.dart")
        assert len(result["enums"]) >= 1
        e = result["enums"][0]
        assert e.name == "Status"


# ===== EXTENSION EXTRACTION =====

class TestExtensionExtraction:
    """Tests for Dart extension extraction."""

    def test_named_extension(self, extractor):
        code = '''
extension StringUtils on String {
  bool get isEmail => contains('@');
  String capitalize() => '${this[0].toUpperCase()}${substring(1)}';
}
'''
        result = extractor.extract(code, "string_utils.dart")
        assert len(result["extensions"]) >= 1
        e = result["extensions"][0]
        assert e.name == "StringUtils"
        assert e.on_type == "String"

    def test_generic_extension(self, extractor):
        code = '''
extension ListUtils on List {
  dynamic firstOrNull() => isEmpty ? null : first;
}
'''
        result = extractor.extract(code, "list_utils.dart")
        assert len(result["extensions"]) >= 1
        e = result["extensions"][0]
        assert e.name == "ListUtils"


# ===== EXTENSION TYPE EXTRACTION =====

class TestExtensionTypeExtraction:
    """Tests for Dart 3.3+ extension type extraction."""

    def test_extension_type(self, extractor):
        code = '''
extension type UserId(int value) {
  UserId.parse(String s) : value = int.parse(s);
  bool get isValid => value > 0;
}
'''
        result = extractor.extract(code, "user_id.dart")
        assert len(result["extension_types"]) >= 1
        et = result["extension_types"][0]
        assert et.name == "UserId"
        assert et.is_extension_type is True


# ===== TYPEDEF EXTRACTION =====

class TestTypedefExtraction:
    """Tests for Dart typedef extraction."""

    def test_function_typedef(self, extractor):
        code = '''
typedef Callback = void Function(String message);
typedef Predicate<T> = bool Function(T value);
'''
        result = extractor.extract(code, "types.dart")
        assert len(result["typedefs"]) >= 1

    def test_type_alias_typedef(self, extractor):
        code = '''
typedef JsonMap = Map<String, dynamic>;
typedef UserList = List<User>;
'''
        result = extractor.extract(code, "aliases.dart")
        assert len(result["typedefs"]) >= 1
        td = result["typedefs"][0]
        assert td.name == "JsonMap"
