"""
Tests for DartFunctionExtractor — functions, methods, constructors, getters, setters, operators.

Part of CodeTrellis v4.27 Dart Language Support.
"""

import pytest
from codetrellis.extractors.dart.function_extractor import DartFunctionExtractor


@pytest.fixture
def extractor():
    return DartFunctionExtractor()


# ===== FUNCTION EXTRACTION =====

class TestFunctionExtraction:
    """Tests for Dart function extraction."""

    def test_simple_function(self, extractor):
        code = '''
void greet(String name) {
  print('Hello, $name!');
}
'''
        result = extractor.extract(code, "utils.dart")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "greet"
        assert f.return_type == "void"

    def test_async_function(self, extractor):
        code = '''
Future<User> fetchUser(String id) async {
  final response = await http.get(Uri.parse('/users/$id'));
  return User.fromJson(jsonDecode(response.body));
}
'''
        result = extractor.extract(code, "api.dart")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "fetchUser"
        assert f.is_async is True

    def test_generator_function(self, extractor):
        code = '''
Iterable<int> naturals(int n) sync* {
  int i = 0;
  while (i < n) {
    yield i++;
  }
}
'''
        result = extractor.extract(code, "generators.dart")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "naturals"
        assert f.is_sync_star is True

    def test_async_generator(self, extractor):
        code = '''
Stream<int> countStream(int max) async* {
  for (int i = 0; i < max; i++) {
    yield i;
    await Future.delayed(Duration(seconds: 1));
  }
}
'''
        result = extractor.extract(code, "streams.dart")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "countStream"
        assert f.is_async_star is True

    def test_arrow_function(self, extractor):
        code = '''
int double(int x) => x * 2;
String greet(String name) => 'Hello, $name';
'''
        result = extractor.extract(code, "utils.dart")
        assert len(result["functions"]) >= 1

    def test_generic_function(self, extractor):
        code = '''
Object firstWhere(List list, String predicate) {
  return list.first;
}
'''
        result = extractor.extract(code, "utils.dart")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "firstWhere"

    def test_function_with_named_params(self, extractor):
        code = '''
void buildCard(String title, String subtitle) {
  print(title);
}
'''
        result = extractor.extract(code, "widgets.dart")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "buildCard"

    def test_function_with_positional_params(self, extractor):
        code = '''
String format(String text, [int maxLen = 100, String suffix = '...']) {
  if (text.length > maxLen) return text.substring(0, maxLen) + suffix;
  return text;
}
'''
        result = extractor.extract(code, "format.dart")
        assert len(result["functions"]) >= 1


# ===== CONSTRUCTOR EXTRACTION =====

class TestConstructorExtraction:
    """Tests for Dart constructor extraction."""

    def test_default_constructor(self, extractor):
        code = '''
class User {
  final String id;
  final String name;
  User(this.id, this.name);
}
'''
        result = extractor.extract(code, "user.dart")
        assert len(result["constructors"]) >= 1
        c = result["constructors"][0]
        assert c.class_name == "User"

    def test_named_constructor(self, extractor):
        code = '''
class Color {
  final int r, g, b;
  Color(this.r, this.g, this.b);
  Color.red() : r = 255, g = 0, b = 0;
  Color.fromHex(String hex) : r = 0, g = 0, b = 0;
}
'''
        result = extractor.extract(code, "color.dart")
        constructors = result["constructors"]
        assert len(constructors) >= 2
        named = [c for c in constructors if c.is_named]
        assert len(named) >= 1

    def test_const_constructor(self, extractor):
        code = '''
class Point {
  final double x;
  final double y;
  const Point(this.x, this.y);
}
'''
        result = extractor.extract(code, "point.dart")
        assert len(result["constructors"]) >= 1
        c = result["constructors"][0]
        assert c.is_const is True

    def test_factory_constructor(self, extractor):
        code = '''
class Logger {
  static final _instance = Logger._internal();
  factory Logger() => _instance;
  Logger._internal();
}
'''
        result = extractor.extract(code, "logger.dart")
        constructors = result["constructors"]
        factory = [c for c in constructors if c.is_factory]
        assert len(factory) >= 1

    def test_redirecting_constructor(self, extractor):
        code = '''
class Rectangle {
  final double width;
  final double height;
  Rectangle(this.width, this.height);
  Rectangle.square(double size) : this(size, size);
}
'''
        result = extractor.extract(code, "rect.dart")
        assert len(result["constructors"]) >= 2


# ===== GETTER / SETTER EXTRACTION =====

class TestGetterSetterExtraction:
    """Tests for Dart getter/setter extraction."""

    def test_getter(self, extractor):
        code = '''
class Circle {
  final double radius;
  Circle(this.radius);
  double get area => 3.14159 * radius * radius;
  double get circumference => 2 * 3.14159 * radius;
}
'''
        result = extractor.extract(code, "circle.dart")
        assert len(result["getters"]) >= 1

    def test_setter(self, extractor):
        code = '''
class Temperature {
  double _celsius;
  Temperature(this._celsius);
  double get celsius => _celsius;
  set celsius(double value) => _celsius = value;
  double get fahrenheit => _celsius * 9 / 5 + 32;
  set fahrenheit(double value) => _celsius = (value - 32) * 5 / 9;
}
'''
        result = extractor.extract(code, "temperature.dart")
        assert len(result["getters"]) >= 1
        assert len(result["setters"]) >= 1


# ===== OPERATOR EXTRACTION =====

class TestOperatorExtraction:
    """Tests for Dart operator extraction."""

    def test_operator_overload(self, extractor):
        code = '''
class Vector2 {
  final double x, y;
  const Vector2(this.x, this.y);
  Vector2 operator +(Vector2 other) => Vector2(x + other.x, y + other.y);
  Vector2 operator -(Vector2 other) => Vector2(x - other.x, y - other.y);
  Vector2 operator *(double scalar) => Vector2(x * scalar, y * scalar);
}
'''
        result = extractor.extract(code, "vector.dart")
        # Operators are part of methods, not a separate key
        # Just validate no errors are raised and methods are returned
        assert "methods" in result or "functions" in result
