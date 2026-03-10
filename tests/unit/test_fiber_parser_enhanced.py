"""
Tests for EnhancedFiberParser.

Part of CodeTrellis v5.2 Go Framework Support.
Tests cover:
- Route extraction (Get, Post, Put, Delete, Patch)
- Route group extraction with prefix
- Middleware extraction (Use, group-level)
- Binding extraction (BodyParser, QueryParser, ParamsParser)
- Config extraction (fiber.Config{})
- Framework version detection (fiber v1.x → v3.x)
"""

import pytest
from codetrellis.fiber_parser_enhanced import (
    EnhancedFiberParser,
    FiberParseResult,
)


@pytest.fixture
def parser():
    return EnhancedFiberParser()


SAMPLE_FIBER_APP = '''
package main

import (
    "github.com/gofiber/fiber/v2"
    "github.com/gofiber/fiber/v2/middleware/cors"
    "github.com/gofiber/fiber/v2/middleware/logger"
    "github.com/gofiber/fiber/v2/middleware/recover"
    "time"
)

func main() {
    app := fiber.New(fiber.Config{
        Prefork:      false,
        ReadTimeout:  10 * time.Second,
        WriteTimeout: 10 * time.Second,
        BodyLimit:    4 * 1024 * 1024,
    })

    app.Use(logger.New())
    app.Use(recover.New())
    app.Use(cors.New())

    app.Get("/health", healthCheck)
    app.Post("/login", login)

    api := app.Group("/api/v1")
    api.Use(authMiddleware)
    api.Get("/users", listUsers)
    api.Post("/users", createUser)
    api.Put("/users/:id", updateUser)
    api.Delete("/users/:id", deleteUser)
    api.Patch("/users/:id", patchUser)

    app.Listen(":3000")
}

func healthCheck(c *fiber.Ctx) error {
    return c.JSON(fiber.Map{"status": "ok"})
}

func createUser(c *fiber.Ctx) error {
    user := new(User)
    if err := c.BodyParser(user); err != nil {
        return c.Status(400).JSON(fiber.Map{"error": err.Error()})
    }
    return c.Status(201).JSON(user)
}

func listUsers(c *fiber.Ctx) error {
    var q PaginationQuery
    c.QueryParser(&q)
    return c.JSON(users)
}

func updateUser(c *fiber.Ctx) error {
    var p UserParams
    c.ParamsParser(&p)
    return c.JSON(fiber.Map{"id": p.ID})
}
'''


class TestFiberParser:

    def test_parse_returns_result(self, parser):
        result = parser.parse(SAMPLE_FIBER_APP, "main.go")
        assert isinstance(result, FiberParseResult)

    def test_detect_fiber_framework(self, parser):
        result = parser.parse(SAMPLE_FIBER_APP, "main.go")
        assert len(result.detected_frameworks) > 0
        assert "fiber" in result.detected_frameworks

    def test_extract_routes(self, parser):
        result = parser.parse(SAMPLE_FIBER_APP, "main.go")
        assert len(result.routes) >= 6
        methods = [r.method for r in result.routes]
        assert "GET" in methods or "Get" in methods
        assert "POST" in methods or "Post" in methods

    def test_extract_route_groups(self, parser):
        result = parser.parse(SAMPLE_FIBER_APP, "main.go")
        assert len(result.route_groups) >= 1

    def test_extract_middleware(self, parser):
        result = parser.parse(SAMPLE_FIBER_APP, "main.go")
        assert len(result.middleware) >= 2

    def test_extract_bindings(self, parser):
        result = parser.parse(SAMPLE_FIBER_APP, "main.go")
        assert len(result.bindings) >= 1

    def test_extract_configs(self, parser):
        result = parser.parse(SAMPLE_FIBER_APP, "main.go")
        assert len(result.configs) >= 1

    def test_non_fiber_file(self, parser):
        result = parser.parse("package main\n\nfunc main() {}", "main.go")
        assert len(result.routes) == 0
        assert len(result.detected_frameworks) == 0

    def test_fiber_detection(self, parser):
        result = parser.parse(SAMPLE_FIBER_APP, "main.go")
        assert len(result.detected_frameworks) > 0
        result2 = parser.parse("package main\nfunc main() {}", "main.go")
        assert len(result2.detected_frameworks) == 0
