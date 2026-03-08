"""
Tests for SwiftFunctionExtractor — functions, methods, initializers, subscripts.

Part of CodeTrellis v4.22 Swift Language Support.
"""

import pytest
from codetrellis.extractors.swift.function_extractor import SwiftFunctionExtractor


@pytest.fixture
def extractor():
    return SwiftFunctionExtractor()


# ===== FUNCTION EXTRACTION =====

class TestFunctionExtraction:
    """Tests for Swift function extraction."""

    def test_simple_function(self, extractor):
        code = '''
func greet(name: String) -> String {
    return "Hello, \\(name)!"
}
'''
        result = extractor.extract(code, "Utils.swift")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "greet"

    def test_void_function(self, extractor):
        code = '''
func printMessage() {
    print("Hello")
}
'''
        result = extractor.extract(code, "Utils.swift")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "printMessage"

    def test_function_with_return_type(self, extractor):
        code = '''
func calculateArea(width: Double, height: Double) -> Double {
    return width * height
}
'''
        result = extractor.extract(code, "Math.swift")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "calculateArea"
        assert f.return_type == "Double"

    def test_async_function(self, extractor):
        code = '''
func fetchUser(id: String) async throws -> User {
    let data = try await api.get("/users/\\(id)")
    return try JSONDecoder().decode(User.self, from: data)
}
'''
        result = extractor.extract(code, "UserService.swift")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "fetchUser"
        assert f.is_async is True
        assert f.is_throws is True

    def test_throwing_function(self, extractor):
        code = '''
func parseJSON(data: Data) throws -> [String: Any] {
    guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
        throw ParseError.invalidFormat
    }
    return json
}
'''
        result = extractor.extract(code, "Parser.swift")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "parseJSON"
        assert f.is_throws is True

    def test_generic_function(self, extractor):
        code = '''
func decode<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
    return try JSONDecoder().decode(type, from: data)
}
'''
        result = extractor.extract(code, "Decoder.swift")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "decode"

    def test_public_function(self, extractor):
        code = '''
public func configure(app: Application) throws {
    app.databases.use(.postgres)
}
'''
        result = extractor.extract(code, "configure.swift")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "configure"

    def test_static_function(self, extractor):
        code = '''
static func create(from data: Data) -> User? {
    return try? JSONDecoder().decode(User.self, from: data)
}
'''
        result = extractor.extract(code, "User.swift")
        assert len(result["functions"]) >= 1

    def test_mutating_function(self, extractor):
        code = '''
mutating func moveBy(dx: Double, dy: Double) {
    x += dx
    y += dy
}
'''
        result = extractor.extract(code, "Point.swift")
        assert len(result["functions"]) >= 1

    def test_multiple_functions(self, extractor):
        code = '''
func add(_ a: Int, _ b: Int) -> Int {
    return a + b
}

func subtract(_ a: Int, _ b: Int) -> Int {
    return a - b
}

func multiply(_ a: Int, _ b: Int) -> Int {
    return a * b
}
'''
        result = extractor.extract(code, "Math.swift")
        assert len(result["functions"]) >= 3


# ===== INITIALIZER EXTRACTION =====

class TestInitExtraction:
    """Tests for Swift initializer extraction."""

    def test_simple_init(self, extractor):
        code = '''
init(name: String, age: Int) {
    self.name = name
    self.age = age
}
'''
        result = extractor.extract(code, "Person.swift")
        assert len(result["inits"]) >= 1

    def test_failable_init(self, extractor):
        code = '''
init?(rawValue: String) {
    guard !rawValue.isEmpty else { return nil }
    self.value = rawValue
}
'''
        result = extractor.extract(code, "Wrapper.swift")
        assert len(result["inits"]) >= 1

    def test_required_init(self, extractor):
        code = '''
required init(coder: NSCoder) {
    fatalError("init(coder:) has not been implemented")
}
'''
        result = extractor.extract(code, "View.swift")
        assert len(result["inits"]) >= 1

    def test_convenience_init(self, extractor):
        code = '''
convenience init(name: String) {
    self.init(name: name, age: 0)
}
'''
        result = extractor.extract(code, "Person.swift")
        assert len(result["inits"]) >= 1

    def test_deinit(self, extractor):
        code = '''
deinit {
    NotificationCenter.default.removeObserver(self)
}
'''
        # deinit is parsed but may not appear in inits list
        # (it's a different construct from init)
        result = extractor.extract(code, "Observer.swift")
        # No error should be raised
        assert isinstance(result, dict)


# ===== SUBSCRIPT EXTRACTION =====

class TestSubscriptExtraction:
    """Tests for Swift subscript extraction."""

    def test_simple_subscript(self, extractor):
        code = '''
subscript(index: Int) -> Element {
    get { return storage[index] }
    set { storage[index] = newValue }
}
'''
        result = extractor.extract(code, "Collection.swift")
        assert len(result["subscripts"]) >= 1

    def test_subscript_with_key(self, extractor):
        code = '''
subscript(key: String) -> Value? {
    get { return dictionary[key] }
    set { dictionary[key] = newValue }
}
'''
        result = extractor.extract(code, "Store.swift")
        assert len(result["subscripts"]) >= 1


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases and robustness."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.swift")
        assert result["functions"] == []
        assert result["inits"] == []
        assert result["subscripts"] == []

    def test_function_with_complex_closure_param(self, extractor):
        code = '''
func performRequest(completion: @escaping (Result<Data, Error>) -> Void) {
    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            completion(.failure(error))
        } else if let data = data {
            completion(.success(data))
        }
    }.resume()
}
'''
        result = extractor.extract(code, "Network.swift")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "performRequest"

    def test_function_with_default_parameters(self, extractor):
        code = '''
func fetchItems(page: Int = 1, limit: Int = 20, sortBy: String = "date") -> [Item] {
    return []
}
'''
        result = extractor.extract(code, "ItemService.swift")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "fetchItems"
