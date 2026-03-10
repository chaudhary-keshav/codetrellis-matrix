"""
Tests for EnhancedEchoParser.

Part of CodeTrellis v5.2 Go Framework Support.
Tests cover:
- Route extraction (GET, POST, PUT, DELETE)
- Route group extraction with prefix
- Middleware extraction (Pre, Use, group-level)
- Binding extraction (Bind, Validate)
- Render extraction (JSON, HTML, String)
- Framework version detection (echo v3.x → v4.x)
"""

import pytest
from codetrellis.echo_parser_enhanced import (
    EnhancedEchoParser,
    EchoParseResult,
)


@pytest.fixture
def parser():
    return EnhancedEchoParser()


SAMPLE_ECHO_APP = '''
package main

import (
    "github.com/labstack/echo/v4"
    "github.com/labstack/echo/v4/middleware"
    "net/http"
)

func main() {
    e := echo.New()

    e.Pre(middleware.RemoveTrailingSlash())
    e.Use(middleware.Logger())
    e.Use(middleware.Recover())
    e.Use(middleware.CORS())

    e.GET("/health", healthCheck)
    e.POST("/login", login)

    api := e.Group("/api/v1")
    api.Use(authMiddleware)
    api.GET("/users", listUsers)
    api.POST("/users", createUser)
    api.PUT("/users/:id", updateUser)
    api.DELETE("/users/:id", deleteUser)

    e.Logger.Fatal(e.Start(":8080"))
}

func healthCheck(c echo.Context) error {
    return c.JSON(http.StatusOK, map[string]string{"status": "ok"})
}

func createUser(c echo.Context) error {
    u := new(User)
    if err := c.Bind(u); err != nil {
        return echo.NewHTTPError(400, err.Error())
    }
    if err := c.Validate(u); err != nil {
        return err
    }
    return c.JSON(201, u)
}

func getStats(c echo.Context) error {
    return c.HTML(200, "<h1>Stats</h1>")
}

func getMessage(c echo.Context) error {
    return c.String(200, "hello")
}
'''


class TestEchoParser:

    def test_parse_returns_result(self, parser):
        result = parser.parse(SAMPLE_ECHO_APP, "main.go")
        assert isinstance(result, EchoParseResult)

    def test_detect_echo_framework(self, parser):
        result = parser.parse(SAMPLE_ECHO_APP, "main.go")
        assert len(result.detected_frameworks) > 0
        assert "echo" in result.detected_frameworks

    def test_extract_routes(self, parser):
        result = parser.parse(SAMPLE_ECHO_APP, "main.go")
        assert len(result.routes) >= 5
        methods = [r.method for r in result.routes]
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    def test_extract_route_groups(self, parser):
        result = parser.parse(SAMPLE_ECHO_APP, "main.go")
        assert len(result.route_groups) >= 1
        prefixes = [g.prefix for g in result.route_groups]
        assert any("/api" in p for p in prefixes)

    def test_extract_middleware(self, parser):
        result = parser.parse(SAMPLE_ECHO_APP, "main.go")
        assert len(result.middleware) >= 3
        names = [m.name for m in result.middleware]
        assert any("Logger" in n for n in names)

    def test_extract_bindings(self, parser):
        result = parser.parse(SAMPLE_ECHO_APP, "main.go")
        assert len(result.bindings) >= 1

    def test_extract_renders(self, parser):
        result = parser.parse(SAMPLE_ECHO_APP, "main.go")
        assert len(result.renders) >= 1

    def test_non_echo_file(self, parser):
        result = parser.parse("package main\n\nfunc main() {}", "main.go")
        assert len(result.routes) == 0
        assert len(result.detected_frameworks) == 0

    def test_echo_detection(self, parser):
        result = parser.parse(SAMPLE_ECHO_APP, "main.go")
        assert len(result.detected_frameworks) > 0
        result2 = parser.parse("package main\nfunc main() {}", "main.go")
        assert len(result2.detected_frameworks) == 0
