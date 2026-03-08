"""
Tests for EnhancedSwiftParser — full integration of all Swift extractors.

Part of CodeTrellis v4.22 Swift Language Support.
"""

import pytest
from codetrellis.swift_parser_enhanced import EnhancedSwiftParser


@pytest.fixture
def parser():
    return EnhancedSwiftParser()


class TestSwiftParserBasic:
    """Tests for basic Swift parsing capabilities."""

    def test_parse_simple_swift_file(self, parser):
        code = '''
import Foundation

struct User: Codable {
    let id: Int
    let name: String
    let email: String
}

func fetchUsers() async throws -> [User] {
    let url = URL(string: "https://api.example.com/users")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode([User].self, from: data)
}
'''
        result = parser.parse(code, "User.swift")
        assert result.file_type == "swift"
        assert len(result.structs) >= 1
        assert result.structs[0].name == "User"
        assert len(result.functions) >= 1
        assert len(result.imports) >= 1

    def test_parse_result_fields(self, parser):
        code = '''
import Foundation

class UserService {
    func getUser(id: Int) async throws -> User {
        return User(id: id, name: "Test", email: "test@test.com")
    }
}
'''
        result = parser.parse(code, "UserService.swift")
        assert result.file_type == "swift"
        assert hasattr(result, 'classes')
        assert hasattr(result, 'functions')
        assert hasattr(result, 'imports')
        assert hasattr(result, 'detected_frameworks')


class TestFrameworkDetection:
    """Tests for Swift framework detection."""

    def test_detect_swiftui(self, parser):
        code = '''
import SwiftUI

struct ContentView: View {
    var body: some View {
        Text("Hello!")
    }
}
'''
        result = parser.parse(code, "ContentView.swift")
        assert "swiftui" in [f.lower() for f in result.detected_frameworks]

    def test_detect_combine(self, parser):
        code = '''
import Combine

class ViewModel: ObservableObject {
    @Published var items: [String] = []
    private var cancellables = Set<AnyCancellable>()
}
'''
        result = parser.parse(code, "ViewModel.swift")
        assert "combine" in [f.lower() for f in result.detected_frameworks]

    def test_detect_vapor(self, parser):
        code = '''
import Vapor

func routes(_ app: Application) throws {
    app.get("hello") { req -> String in
        return "Hello, world!"
    }
}
'''
        result = parser.parse(code, "routes.swift")
        assert "vapor" in [f.lower() for f in result.detected_frameworks]

    def test_detect_foundation(self, parser):
        code = '''
import Foundation

let url = URL(string: "https://api.example.com")!
let session = URLSession.shared
'''
        result = parser.parse(code, "main.swift")
        # Foundation is a base framework; detector picks up URLSession usage
        assert "urlsession" in [f.lower() for f in result.detected_frameworks]

    def test_detect_multiple_frameworks(self, parser):
        code = '''
import SwiftUI
import Combine
import CoreData

struct AppView: View {
    @StateObject var viewModel = AppViewModel()
    var body: some View {
        Text("App")
    }
}
'''
        result = parser.parse(code, "App.swift")
        frameworks_lower = [f.lower() for f in result.detected_frameworks]
        assert "swiftui" in frameworks_lower
        assert "combine" in frameworks_lower

    def test_detect_uikit(self, parser):
        code = '''
import UIKit

class ViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
    }
}
'''
        result = parser.parse(code, "ViewController.swift")
        assert "uikit" in [f.lower() for f in result.detected_frameworks]


class TestImportExtraction:
    """Tests for Swift import extraction."""

    def test_basic_imports(self, parser):
        code = '''
import Foundation
import UIKit
import SwiftUI
'''
        result = parser.parse(code, "main.swift")
        assert len(result.imports) >= 3

    def test_submodule_import(self, parser):
        code = '''
import Foundation
import struct Foundation.URL
import class UIKit.UIViewController
'''
        result = parser.parse(code, "main.swift")
        assert len(result.imports) >= 1

    def test_no_imports(self, parser):
        code = '''
func add(_ a: Int, _ b: Int) -> Int {
    return a + b
}
'''
        result = parser.parse(code, "math.swift")
        assert len(result.imports) == 0


class TestSwiftConcurrency:
    """Tests for Swift concurrency features."""

    def test_actor_parsing(self, parser):
        code = '''
import Foundation

actor ImageCache {
    private var cache: [String: Data] = [:]

    func image(for key: String) -> Data? {
        return cache[key]
    }

    func store(_ data: Data, for key: String) {
        cache[key] = data
    }
}
'''
        result = parser.parse(code, "ImageCache.swift")
        assert len(result.actors) >= 1
        assert result.actors[0].name == "ImageCache"

    def test_async_await_functions(self, parser):
        code = '''
func fetchData() async throws -> Data {
    let url = URL(string: "https://api.example.com")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return data
}

func processData() async {
    do {
        let data = try await fetchData()
        print(data)
    } catch {
        print(error)
    }
}
'''
        result = parser.parse(code, "DataService.swift")
        assert len(result.functions) >= 2
        async_funcs = [f for f in result.functions if f.is_async]
        assert len(async_funcs) >= 1


class TestProtocolOrientedDesign:
    """Tests for protocol extraction and extensions."""

    def test_protocol_with_extensions(self, parser):
        code = '''
protocol Validatable {
    func validate() -> Bool
}

extension Validatable {
    func validate() -> Bool {
        return true
    }
}

struct Email: Validatable {
    let address: String

    func validate() -> Bool {
        return address.contains("@")
    }
}
'''
        result = parser.parse(code, "Validation.swift")
        assert len(result.protocols) >= 1
        assert result.protocols[0].name == "Validatable"
        assert len(result.extensions) >= 1
        assert len(result.structs) >= 1


class TestComplexSwiftFile:
    """Tests for parsing complex multi-feature Swift files."""

    def test_vapor_controller(self, parser):
        code = '''
import Vapor
import Fluent

struct UserController: RouteCollection {
    func boot(routes: RoutesBuilder) throws {
        let users = routes.grouped("users")
        users.get(use: index)
        users.post(use: create)
        users.group(":userID") { user in
            user.get(use: show)
            user.put(use: update)
            user.delete(use: delete)
        }
    }

    func index(req: Request) async throws -> [User] {
        try await User.query(on: req.db).all()
    }

    func create(req: Request) async throws -> User {
        let user = try req.content.decode(User.self)
        try await user.save(on: req.db)
        return user
    }

    func show(req: Request) async throws -> User {
        guard let user = try await User.find(req.parameters.get("userID"), on: req.db) else {
            throw Abort(.notFound)
        }
        return user
    }

    func update(req: Request) async throws -> User {
        guard let user = try await User.find(req.parameters.get("userID"), on: req.db) else {
            throw Abort(.notFound)
        }
        let updatedUser = try req.content.decode(User.self)
        user.name = updatedUser.name
        try await user.save(on: req.db)
        return user
    }

    func delete(req: Request) async throws -> HTTPStatus {
        guard let user = try await User.find(req.parameters.get("userID"), on: req.db) else {
            throw Abort(.notFound)
        }
        try await user.delete(on: req.db)
        return .noContent
    }
}
'''
        result = parser.parse(code, "UserController.swift")
        frameworks_lower = [f.lower() for f in result.detected_frameworks]
        assert "vapor" in frameworks_lower
        assert len(result.structs) >= 1
        assert len(result.functions) >= 5

    def test_swiftui_app(self, parser):
        code = '''
import SwiftUI

@main
struct MyApp: App {
    @StateObject private var store = AppStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(store)
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var store: AppStore
    @State private var searchText = ""

    var body: some View {
        NavigationStack {
            List(store.items.filter { item in
                searchText.isEmpty || item.title.contains(searchText)
            }) { item in
                NavigationLink(item.title) {
                    DetailView(item: item)
                }
            }
            .searchable(text: $searchText)
            .navigationTitle("Items")
        }
    }
}

struct DetailView: View {
    let item: Item

    var body: some View {
        VStack {
            Text(item.title)
                .font(.headline)
            Text(item.description)
                .font(.body)
        }
        .padding()
    }
}
'''
        result = parser.parse(code, "App.swift")
        frameworks_lower = [f.lower() for f in result.detected_frameworks]
        assert "swiftui" in frameworks_lower
        assert len(result.structs) >= 3
        assert len(result.views) >= 2


class TestSwiftVersionFeatures:
    """Tests for Swift version-specific features."""

    def test_swift_55_async_await(self, parser):
        """Swift 5.5: async/await, actors"""
        code = '''
actor Counter {
    private var count = 0

    func increment() {
        count += 1
    }

    func getCount() -> Int {
        return count
    }
}

func performCounting() async {
    let counter = Counter()
    await counter.increment()
    let value = await counter.getCount()
    print(value)
}
'''
        result = parser.parse(code, "Counter.swift")
        assert len(result.actors) >= 1
        async_funcs = [f for f in result.functions if f.is_async]
        assert len(async_funcs) >= 1

    def test_swift_59_macros(self, parser):
        """Swift 5.9: Macros"""
        code = '''
import Foundation
import SwiftUI

@Observable
class UserStore {
    var users: [User] = []
    var isLoading = false
}

#Preview {
    ContentView()
}
'''
        result = parser.parse(code, "UserStore.swift")
        assert len(result.classes) >= 1


class TestPackageSwift:
    """Tests for Package.swift parsing."""

    def test_parse_package_swift(self, parser):
        code = '''
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MyApp",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    dependencies: [
        .package(url: "https://github.com/vapor/vapor.git", from: "4.83.1"),
        .package(url: "https://github.com/vapor/fluent.git", from: "4.8.0"),
    ],
    targets: [
        .executableTarget(
            name: "App",
            dependencies: [
                .product(name: "Vapor", package: "vapor"),
                .product(name: "Fluent", package: "fluent"),
            ]
        ),
        .testTarget(
            name: "AppTests",
            dependencies: ["App"]
        ),
    ]
)
'''
        result = EnhancedSwiftParser.parse_package_swift(code)
        assert result is not None
        assert result["name"] == "MyApp"
        assert len(result["dependencies"]) >= 2
        assert any("vapor" in d.get("name", "").lower() for d in result["dependencies"])


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_file(self, parser):
        result = parser.parse("", "empty.swift")
        assert result.file_type == "swift"
        assert result.classes == []
        assert result.structs == []
        assert result.functions == []
        assert result.imports == []

    def test_comments_only(self, parser):
        code = '''
// MARK: - Utilities
// TODO: Implement this
/* Multi-line
   comment */
'''
        result = parser.parse(code, "comments.swift")
        assert result.classes == []
        assert result.structs == []

    def test_file_type_always_swift(self, parser):
        result = parser.parse("let x = 1", "test.swift")
        assert result.file_type == "swift"
