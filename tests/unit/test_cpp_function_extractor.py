"""
Tests for C++ function extractor — methods, free functions, constructors,
destructors, operators, lambdas, coroutines, templates.

Part of CodeTrellis v4.20 C++ Language Support.
"""

import pytest
from codetrellis.extractors.cpp.function_extractor import (
    CppFunctionExtractor, CppMethodInfo, CppLambdaInfo, CppParameterInfo,
)


@pytest.fixture
def extractor():
    return CppFunctionExtractor()


class TestCppMethodExtraction:
    """Tests for C++ method/function extraction."""

    def test_free_function(self, extractor):
        code = '''
int add(int a, int b) {
    return a + b;
}
'''
        result = extractor.extract(code)
        assert len(result['methods']) >= 1
        fn = result['methods'][0]
        assert fn.name == 'add'
        assert fn.return_type == 'int'

    def test_method_with_qualifiers(self, extractor):
        code = '''
class Widget {
public:
    virtual void draw() const noexcept override;
    static Widget create(int w, int h);
};
'''
        result = extractor.extract(code)
        methods = result['methods']
        assert len(methods) >= 1

    def test_constructor_destructor(self, extractor):
        code = '''
class Resource {
public:
    Resource(const std::string& path);
    Resource(Resource&& other) noexcept;
    ~Resource();
};
'''
        result = extractor.extract(code)
        methods = result['methods']
        constructors = [m for m in methods if m.is_constructor]
        destructors = [m for m in methods if m.is_destructor]
        assert len(constructors) + len(destructors) >= 1

    def test_operator_overload(self, extractor):
        code = '''
class Vector3 {
public:
    Vector3 operator+(const Vector3& rhs) const {
        return Vector3(x + rhs.x, y + rhs.y, z + rhs.z);
    }
    bool operator==(const Vector3& rhs) const = default;
};
'''
        result = extractor.extract(code)
        methods = result['methods']
        operators = [m for m in methods if m.is_operator]
        assert len(operators) >= 1

    def test_template_function(self, extractor):
        code = '''
template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}
'''
        result = extractor.extract(code)
        methods = result['methods']
        assert len(methods) >= 1
        assert methods[0].is_template is True

    def test_constexpr_function(self, extractor):
        code = '''
constexpr int factorial(int n) {
    return (n <= 1) ? 1 : n * factorial(n - 1);
}
'''
        result = extractor.extract(code)
        methods = result['methods']
        assert len(methods) >= 1
        assert methods[0].is_constexpr is True

    def test_coroutine_function(self, extractor):
        code = '''
Task<int> fetch_data(const std::string& url) {
    auto response = co_await http::get(url);
    co_return response.status_code();
}
'''
        result = extractor.extract(code)
        methods = result['methods']
        assert len(methods) >= 1
        assert methods[0].is_coroutine is True

    def test_deleted_defaulted(self, extractor):
        code = '''
class NonCopyable {
public:
    NonCopyable() = default;
    NonCopyable(const NonCopyable&) = delete;
    NonCopyable& operator=(const NonCopyable&) = delete;
    NonCopyable(NonCopyable&&) = default;
};
'''
        result = extractor.extract(code)
        methods = result['methods']
        deleted = [m for m in methods if m.is_deleted]
        defaulted = [m for m in methods if m.is_defaulted]
        assert len(deleted) + len(defaulted) >= 1

    def test_static_member_function(self, extractor):
        code = '''
class Factory {
public:
    static std::unique_ptr<Widget> create(int type) {
        switch (type) {
            case 1: return std::make_unique<Button>();
            default: return nullptr;
        }
    }
};
'''
        result = extractor.extract(code)
        methods = result['methods']
        static_fns = [m for m in methods if m.is_static]
        assert len(static_fns) >= 1

    def test_complexity_estimation(self, extractor):
        code = '''
int process(int x) {
    if (x > 0) {
        for (int i = 0; i < x; i++) {
            if (i % 2 == 0) {
                continue;
            } else {
                break;
            }
        }
    } else if (x < -10) {
        while (x++ < 0) {
            x *= 2;
        }
    }
    return x;
}
'''
        result = extractor.extract(code)
        methods = result['methods']
        assert len(methods) >= 1
        # Should have complexity > 1 due to branches
        assert methods[0].complexity >= 2


class TestCppLambdaExtraction:
    """Tests for C++ lambda extraction."""

    def test_basic_lambda(self, extractor):
        code = '''
auto greet = [](const std::string& name) {
    std::cout << "Hello, " << name << std::endl;
};
'''
        result = extractor.extract(code)
        assert len(result['lambdas']) >= 1

    def test_capture_lambda(self, extractor):
        code = '''
int x = 42;
auto add_x = [x](int y) -> int {
    return x + y;
};
'''
        result = extractor.extract(code)
        lambdas = result['lambdas']
        assert len(lambdas) >= 1

    def test_generic_lambda(self, extractor):
        code = '''
auto multiply = [](auto a, auto b) {
    return a * b;
};
'''
        result = extractor.extract(code)
        lambdas = result['lambdas']
        assert len(lambdas) >= 1
        assert lambdas[0].is_generic is True

    def test_mutable_lambda(self, extractor):
        code = '''
int counter = 0;
auto inc = [counter]() mutable {
    return ++counter;
};
'''
        result = extractor.extract(code)
        lambdas = result['lambdas']
        assert len(lambdas) >= 1
        assert lambdas[0].is_mutable is True
