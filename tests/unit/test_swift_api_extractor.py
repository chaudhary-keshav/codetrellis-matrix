"""
Tests for SwiftAPIExtractor — routes (Vapor), SwiftUI views, Combine publishers, gRPC.

Part of CodeTrellis v4.22 Swift Language Support.
"""

import pytest
from codetrellis.extractors.swift.api_extractor import SwiftAPIExtractor


@pytest.fixture
def extractor():
    return SwiftAPIExtractor()


# ===== VAPOR ROUTE EXTRACTION =====

class TestVaporRouteExtraction:
    """Tests for Vapor server-side route extraction."""

    def test_basic_get_route(self, extractor):
        code = '''
app.get("users") { req -> [User] in
    return try await User.query(on: req.db).all()
}
'''
        result = extractor.extract(code, "routes.swift")
        assert len(result["routes"]) >= 1
        r = result["routes"][0]
        assert r.method.upper() == "GET"
        assert "users" in r.path

    def test_post_route(self, extractor):
        code = '''
app.post("users") { req -> User in
    let user = try req.content.decode(User.self)
    try await user.save(on: req.db)
    return user
}
'''
        result = extractor.extract(code, "routes.swift")
        assert len(result["routes"]) >= 1
        r = result["routes"][0]
        assert r.method.upper() == "POST"

    def test_multiple_routes(self, extractor):
        code = '''
app.get("api", "v1", "users") { req -> [User] in
    return try await User.query(on: req.db).all()
}

app.post("api", "v1", "users") { req -> User in
    let user = try req.content.decode(User.self)
    return user
}

app.delete("api", "v1", "users", ":id") { req -> HTTPStatus in
    let user = try await User.find(req.parameters.get("id"), on: req.db)
    try await user?.delete(on: req.db)
    return .noContent
}
'''
        result = extractor.extract(code, "routes.swift")
        assert len(result["routes"]) >= 3

    def test_route_group(self, extractor):
        code = '''
let api = app.grouped("api", "v1")
app.get("health") { req -> String in
    return "OK"
}
'''
        result = extractor.extract(code, "routes.swift")
        assert len(result["routes"]) >= 1


# ===== SWIFTUI VIEW EXTRACTION =====

class TestSwiftUIViewExtraction:
    """Tests for SwiftUI view extraction."""

    def test_simple_view(self, extractor):
        code = '''
struct ContentView: View {
    var body: some View {
        Text("Hello, World!")
    }
}
'''
        result = extractor.extract(code, "ContentView.swift")
        assert len(result["views"]) >= 1
        v = result["views"][0]
        assert v.name == "ContentView"

    def test_view_with_state(self, extractor):
        code = '''
struct CounterView: View {
    @State private var count = 0

    var body: some View {
        VStack {
            Text("Count: \\(count)")
            Button("Increment") {
                count += 1
            }
        }
    }
}
'''
        result = extractor.extract(code, "CounterView.swift")
        assert len(result["views"]) >= 1
        v = result["views"][0]
        assert v.name == "CounterView"

    def test_multiple_views(self, extractor):
        code = '''
struct HomeView: View {
    var body: some View {
        NavigationStack {
            Text("Home")
        }
    }
}

struct DetailView: View {
    let item: Item

    var body: some View {
        Text(item.title)
    }
}

struct SettingsView: View {
    var body: some View {
        Form {
            Text("Settings")
        }
    }
}
'''
        result = extractor.extract(code, "Views.swift")
        assert len(result["views"]) >= 3


# ===== COMBINE PUBLISHER EXTRACTION =====

class TestCombinePublisherExtraction:
    """Tests for Combine publisher/subscriber extraction."""

    def test_published_property(self, extractor):
        code = '''
class UserViewModel: ObservableObject {
    @Published var users: [User] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
}
'''
        result = extractor.extract(code, "UserViewModel.swift")
        assert len(result["publishers"]) >= 1

    def test_combine_pipeline(self, extractor):
        code = '''
class NetworkManager {
    let subject = CurrentValueSubject<[User], Never>([])
    var publisher: AnyPublisher<[User], Error> {
        return subject.eraseToAnyPublisher()
    }
}
'''
        result = extractor.extract(code, "ViewModel.swift")
        assert len(result["publishers"]) >= 1


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases and robustness."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.swift")
        assert result["routes"] == []
        assert result["views"] == []
        assert result["publishers"] == []
        assert result["grpc_services"] == []

    def test_non_api_code(self, extractor):
        code = '''
struct Point {
    var x: Double
    var y: Double
}

func add(_ a: Int, _ b: Int) -> Int {
    return a + b
}
'''
        result = extractor.extract(code, "Utils.swift")
        assert result["routes"] == []
        assert result["views"] == []
        assert result["publishers"] == []
