"""
Tests for SwiftTypeExtractor — classes, structs, enums, protocols, actors, extensions, type aliases.

Part of CodeTrellis v4.22 Swift Language Support.
"""

import pytest
from codetrellis.extractors.swift.type_extractor import SwiftTypeExtractor


@pytest.fixture
def extractor():
    return SwiftTypeExtractor()


# ===== CLASS EXTRACTION =====

class TestClassExtraction:
    """Tests for Swift class extraction."""

    def test_simple_class(self, extractor):
        code = '''
class User {
    var id: Int
    var name: String

    init(id: Int, name: String) {
        self.id = id
        self.name = name
    }
}
'''
        result = extractor.extract(code, "User.swift")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "User"

    def test_class_with_inheritance(self, extractor):
        code = '''
class ViewController: UIViewController, UITableViewDelegate {
    var tableView: UITableView!
}
'''
        result = extractor.extract(code, "ViewController.swift")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "ViewController"
        assert "UIViewController" in c.superclass or "UIViewController" in str(c.superclass)

    def test_final_class(self, extractor):
        code = '''
final class APIClient {
    static let shared = APIClient()
    private init() {}
}
'''
        result = extractor.extract(code, "APIClient.swift")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "APIClient"

    def test_generic_class(self, extractor):
        code = '''
class Cache<Key: Hashable, Value> {
    private var storage: [Key: Value] = [:]
}
'''
        result = extractor.extract(code, "Cache.swift")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "Cache"

    def test_public_class(self, extractor):
        code = '''
public class NetworkManager {
    public var baseURL: URL?
}
'''
        result = extractor.extract(code, "NetworkManager.swift")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "NetworkManager"

    def test_open_class(self, extractor):
        code = '''
open class BaseRouter {
    open func route(to path: String) {}
}
'''
        result = extractor.extract(code, "BaseRouter.swift")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "BaseRouter"


# ===== STRUCT EXTRACTION =====

class TestStructExtraction:
    """Tests for Swift struct extraction."""

    def test_simple_struct(self, extractor):
        code = '''
struct Point {
    var x: Double
    var y: Double
}
'''
        result = extractor.extract(code, "Point.swift")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "Point"

    def test_struct_with_conformance(self, extractor):
        code = '''
struct User: Codable, Equatable {
    let id: Int
    let name: String
    let email: String
}
'''
        result = extractor.extract(code, "User.swift")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "User"

    def test_public_struct(self, extractor):
        code = '''
public struct APIResponse<T: Codable>: Codable {
    public let data: T
    public let status: Int
}
'''
        result = extractor.extract(code, "APIResponse.swift")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "APIResponse"


# ===== ENUM EXTRACTION =====

class TestEnumExtraction:
    """Tests for Swift enum extraction."""

    def test_simple_enum(self, extractor):
        code = '''
enum Direction {
    case north
    case south
    case east
    case west
}
'''
        result = extractor.extract(code, "Direction.swift")
        assert len(result["enums"]) >= 1
        e = result["enums"][0]
        assert e.name == "Direction"

    def test_enum_with_raw_value(self, extractor):
        code = '''
enum HTTPMethod: String {
    case get = "GET"
    case post = "POST"
    case put = "PUT"
    case delete = "DELETE"
}
'''
        result = extractor.extract(code, "HTTPMethod.swift")
        assert len(result["enums"]) >= 1
        e = result["enums"][0]
        assert e.name == "HTTPMethod"

    def test_enum_with_associated_values(self, extractor):
        code = '''
enum NetworkResult {
    case success(Data)
    case failure(Error)
    case loading(progress: Double)
}
'''
        result = extractor.extract(code, "NetworkResult.swift")
        assert len(result["enums"]) >= 1
        e = result["enums"][0]
        assert e.name == "NetworkResult"

    def test_indirect_enum(self, extractor):
        code = '''
indirect enum Expression {
    case number(Int)
    case addition(Expression, Expression)
    case multiplication(Expression, Expression)
}
'''
        result = extractor.extract(code, "Expression.swift")
        assert len(result["enums"]) >= 1


# ===== PROTOCOL EXTRACTION =====

class TestProtocolExtraction:
    """Tests for Swift protocol extraction."""

    def test_simple_protocol(self, extractor):
        code = '''
protocol Identifiable {
    var id: String { get }
    func display() -> String
}
'''
        result = extractor.extract(code, "Identifiable.swift")
        assert len(result["protocols"]) >= 1
        p = result["protocols"][0]
        assert p.name == "Identifiable"

    def test_protocol_with_associated_type(self, extractor):
        code = '''
protocol Repository {
    associatedtype Entity
    func findById(_ id: String) async throws -> Entity?
    func save(_ entity: Entity) async throws
}
'''
        result = extractor.extract(code, "Repository.swift")
        assert len(result["protocols"]) >= 1
        p = result["protocols"][0]
        assert p.name == "Repository"

    def test_protocol_with_class_constraint(self, extractor):
        code = '''
protocol Delegate: AnyObject {
    func didFinish()
}
'''
        result = extractor.extract(code, "Delegate.swift")
        assert len(result["protocols"]) >= 1
        p = result["protocols"][0]
        assert p.name == "Delegate"


# ===== ACTOR EXTRACTION =====

class TestActorExtraction:
    """Tests for Swift actor extraction (Swift 5.5+)."""

    def test_simple_actor(self, extractor):
        code = '''
actor UserCache {
    private var users: [String: User] = [:]

    func getUser(_ id: String) -> User? {
        return users[id]
    }

    func setUser(_ user: User) {
        users[user.id] = user
    }
}
'''
        result = extractor.extract(code, "UserCache.swift")
        assert len(result["actors"]) >= 1
        a = result["actors"][0]
        assert a.name == "UserCache"

    def test_global_actor(self, extractor):
        code = '''
@globalActor
actor DatabaseActor {
    static let shared = DatabaseActor()
}
'''
        result = extractor.extract(code, "DatabaseActor.swift")
        assert len(result["actors"]) >= 1


# ===== EXTENSION EXTRACTION =====

class TestExtensionExtraction:
    """Tests for Swift extension extraction."""

    def test_simple_extension(self, extractor):
        code = '''
extension String {
    var isEmail: Bool {
        contains("@")
    }
}
'''
        result = extractor.extract(code, "String+Extensions.swift")
        assert len(result["extensions"]) >= 1
        ext = result["extensions"][0]
        assert ext.name == "String"

    def test_extension_with_protocol_conformance(self, extractor):
        code = '''
extension User: CustomStringConvertible {
    var description: String {
        return "User(name: \\(name))"
    }
}
'''
        result = extractor.extract(code, "User+Extensions.swift")
        assert len(result["extensions"]) >= 1

    def test_extension_with_where_clause(self, extractor):
        code = '''
extension Array where Element: Comparable {
    func sorted() -> [Element] {
        return self.sorted(by: <)
    }
}
'''
        result = extractor.extract(code, "Array+Extensions.swift")
        assert len(result["extensions"]) >= 1


# ===== TYPEALIAS EXTRACTION =====

class TestTypeAliasExtraction:
    """Tests for Swift typealias extraction."""

    def test_simple_typealias(self, extractor):
        code = '''
typealias Completion = (Result<Data, Error>) -> Void
typealias UserID = String
'''
        result = extractor.extract(code, "TypeAliases.swift")
        assert len(result["type_aliases"]) >= 1

    def test_generic_typealias(self, extractor):
        code = '''
typealias Handler<T> = (Result<T, Error>) -> Void
'''
        result = extractor.extract(code, "Handlers.swift")
        assert len(result["type_aliases"]) >= 1


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases and robustness."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.swift")
        assert result["classes"] == []
        assert result["structs"] == []
        assert result["enums"] == []
        assert result["protocols"] == []
        assert result["actors"] == []

    def test_comments_only(self, extractor):
        code = '''
// This is a comment
/* This is a
   multi-line comment */
'''
        result = extractor.extract(code, "comments.swift")
        assert result["classes"] == []
        assert result["structs"] == []

    def test_mixed_types(self, extractor):
        code = '''
protocol Drawable {
    func draw()
}

struct Circle: Drawable {
    var radius: Double
    func draw() {}
}

class Canvas {
    var shapes: [Drawable] = []
}

enum Shape {
    case circle(radius: Double)
    case rectangle(width: Double, height: Double)
}
'''
        result = extractor.extract(code, "Drawing.swift")
        assert len(result["protocols"]) >= 1
        assert len(result["structs"]) >= 1
        assert len(result["classes"]) >= 1
        assert len(result["enums"]) >= 1
