"""
Tests for C++ type extractor — classes, structs, unions, enums, concepts,
type aliases, namespaces, forward declarations.

Part of CodeTrellis v4.20 C++ Language Support.
"""

import pytest
from codetrellis.extractors.cpp.type_extractor import (
    CppTypeExtractor, CppClassInfo, CppUnionInfo, CppEnumInfo,
    CppTypeAliasInfo, CppConceptInfo, CppForwardDeclInfo, CppNamespaceInfo,
)


@pytest.fixture
def extractor():
    return CppTypeExtractor()


class TestCppClassExtraction:
    """Tests for C++ class/struct extraction."""

    def test_basic_class(self, extractor):
        code = '''
class Widget {
public:
    int width;
    int height;
    void draw();
};
'''
        result = extractor.extract(code)
        assert len(result['classes']) >= 1
        cls = result['classes'][0]
        assert cls.name == 'Widget'
        assert cls.kind == 'class'

    def test_struct_with_fields(self, extractor):
        code = '''
struct Point {
    double x;
    double y;
    double z;
};
'''
        result = extractor.extract(code)
        assert len(result['classes']) >= 1
        s = result['classes'][0]
        assert s.name == 'Point'
        assert s.kind == 'struct'

    def test_class_with_inheritance(self, extractor):
        code = '''
class Shape {
public:
    virtual double area() const = 0;
    virtual ~Shape() = default;
};

class Circle : public Shape {
    double radius_;
public:
    double area() const override;
};
'''
        result = extractor.extract(code)
        classes = result['classes']
        assert len(classes) >= 2
        shape = next((c for c in classes if c.name == 'Shape'), None)
        circle = next((c for c in classes if c.name == 'Circle'), None)
        assert shape is not None
        assert circle is not None
        assert circle.is_abstract is False

    def test_template_class(self, extractor):
        code = '''
template<typename T, typename Allocator = std::allocator<T>>
class Vector {
    T* data_;
    size_t size_;
    size_t capacity_;
public:
    void push_back(const T& value);
    void push_back(T&& value);
};
'''
        result = extractor.extract(code)
        classes = result['classes']
        assert len(classes) >= 1
        vec = classes[0]
        assert vec.name == 'Vector'
        assert vec.is_template is True

    def test_final_class(self, extractor):
        code = '''
class Singleton final {
    static Singleton& instance();
    Singleton() = default;
};
'''
        result = extractor.extract(code)
        classes = result['classes']
        assert len(classes) >= 1
        assert classes[0].is_final is True

    def test_crtp_pattern(self, extractor):
        code = '''
template<typename Derived>
class Base {
    void interface() {
        static_cast<Derived*>(this)->implementation();
    }
};

class Impl : public Base<Impl> {
    void implementation();
};
'''
        result = extractor.extract(code)
        classes = result['classes']
        assert len(classes) >= 2

    def test_multiple_inheritance(self, extractor):
        code = '''
class Drawable {
public:
    virtual void draw() = 0;
};

class Serializable {
public:
    virtual std::string serialize() = 0;
};

class Entity : public Drawable, public Serializable {
    void draw() override;
    std::string serialize() override;
};
'''
        result = extractor.extract(code)
        classes = result['classes']
        assert len(classes) >= 3


class TestCppUnionExtraction:
    """Tests for C++ union extraction."""

    def test_basic_union(self, extractor):
        code = '''
union Value {
    int i;
    float f;
    double d;
    char* s;
};
'''
        result = extractor.extract(code)
        assert len(result['unions']) >= 1
        u = result['unions'][0]
        assert u.name == 'Value'

    def test_anonymous_union(self, extractor):
        code = '''
struct Variant {
    int type;
    union {
        int int_val;
        float float_val;
    };
};
'''
        result = extractor.extract(code)
        # Should detect either union or struct
        assert len(result['unions']) + len(result['classes']) >= 1


class TestCppEnumExtraction:
    """Tests for C++ enum extraction."""

    def test_scoped_enum(self, extractor):
        code = '''
enum class Color : uint8_t {
    Red = 0,
    Green = 1,
    Blue = 2
};
'''
        result = extractor.extract(code)
        assert len(result['enums']) >= 1
        e = result['enums'][0]
        assert e.name == 'Color'
        assert e.is_scoped is True

    def test_unscoped_enum(self, extractor):
        code = '''
enum Direction {
    North,
    South,
    East,
    West
};
'''
        result = extractor.extract(code)
        assert len(result['enums']) >= 1
        e = result['enums'][0]
        assert e.name == 'Direction'
        assert e.is_scoped is False

    def test_enum_struct(self, extractor):
        code = '''
enum struct LogLevel {
    Debug,
    Info,
    Warning,
    Error,
    Fatal
};
'''
        result = extractor.extract(code)
        assert len(result['enums']) >= 1
        e = result['enums'][0]
        assert e.is_scoped is True


class TestCppTypeAliasExtraction:
    """Tests for C++ type alias extraction."""

    def test_using_alias(self, extractor):
        code = '''
using StringVec = std::vector<std::string>;
using Callback = std::function<void(int)>;
'''
        result = extractor.extract(code)
        assert len(result['type_aliases']) >= 2

    def test_template_alias(self, extractor):
        code = '''
template<typename T>
using Vec = std::vector<T, CustomAllocator<T>>;
'''
        result = extractor.extract(code)
        aliases = result['type_aliases']
        assert len(aliases) >= 1
        assert aliases[0].is_template is True

    def test_typedef(self, extractor):
        code = '''
typedef unsigned long ulong;
typedef void (*SignalHandler)(int);
'''
        result = extractor.extract(code)
        assert len(result['type_aliases']) >= 1


class TestCppConceptExtraction:
    """Tests for C++20 concept extraction."""

    def test_basic_concept(self, extractor):
        code = '''
template<typename T>
concept Hashable = requires(T a) {
    { std::hash<T>{}(a) } -> std::convertible_to<std::size_t>;
};
'''
        result = extractor.extract(code)
        assert len(result['concepts']) >= 1
        c = result['concepts'][0]
        assert c.name == 'Hashable'

    def test_compound_concept(self, extractor):
        code = '''
template<typename T>
concept Sortable = std::random_access_iterator<T> && std::totally_ordered<T>;
'''
        result = extractor.extract(code)
        assert len(result['concepts']) >= 1


class TestCppNamespaceExtraction:
    """Tests for C++ namespace extraction."""

    def test_basic_namespace(self, extractor):
        code = '''
namespace mylib {
    class Widget {};
}
'''
        result = extractor.extract(code)
        assert len(result['namespaces']) >= 1
        ns = result['namespaces'][0]
        assert ns.name == 'mylib'

    def test_nested_namespace_cpp17(self, extractor):
        code = '''
namespace mylib::detail::internal {
    void helper();
}
'''
        result = extractor.extract(code)
        assert len(result['namespaces']) >= 1

    def test_inline_namespace(self, extractor):
        code = '''
inline namespace v2 {
    class API {};
}
'''
        result = extractor.extract(code)
        assert len(result['namespaces']) >= 1
        ns = result['namespaces'][0]
        assert ns.is_inline is True

    def test_anonymous_namespace(self, extractor):
        code = '''
namespace {
    int internal_counter = 0;
}
'''
        result = extractor.extract(code)
        assert len(result['namespaces']) >= 1
        ns = result['namespaces'][0]
        assert ns.is_anonymous is True


class TestCppForwardDeclarations:
    """Tests for C++ forward declaration extraction."""

    def test_class_forward_decl(self, extractor):
        code = '''
class Widget;
struct Point;
'''
        result = extractor.extract(code)
        assert len(result['forward_decls']) >= 2
