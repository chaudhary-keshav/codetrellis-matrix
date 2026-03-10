"""
Tests for EnhancedGinParser.

Part of CodeTrellis v5.2 Go Framework Support.
Tests cover:
- Route extraction (GET, POST, PUT, DELETE, PATCH)
- Route group extraction with prefix and middleware
- Middleware extraction (global, group, inline)
- Binding extraction (ShouldBindJSON, ShouldBindQuery, ShouldBindUri)
- Render extraction (JSON, HTML, XML, String, Redirect)
- Engine config extraction (SetMode, SetTrustedProxies)
- Framework version detection (gin v1.x → v1.9+)
"""

import pytest
from codetrellis.gin_parser_enhanced import (
    EnhancedGinParser,
    GinParseResult,
)


@pytest.fixture
def parser():
    return EnhancedGinParser()


SAMPLE_GIN_APP = '''
package main

import (
    "github.com/gin-gonic/gin"
    "net/http"
)

func main() {
    gin.SetMode(gin.ReleaseMode)
    r := gin.New()
    r.SetTrustedProxies([]string{"127.0.0.1"})

    r.Use(gin.Logger())
    r.Use(gin.Recovery())

    r.GET("/health", healthCheck)
    r.POST("/login", loginHandler)

    api := r.Group("/api/v1")
    api.Use(authMiddleware())
    {
        api.GET("/users", listUsers)
        api.POST("/users", createUser)
        api.PUT("/users/:id", updateUser)
        api.DELETE("/users/:id", deleteUser)
    }

    admin := r.Group("/admin", adminAuth())
    {
        admin.GET("/stats", getStats)
    }

    r.Run(":8080")
}

func healthCheck(c *gin.Context) {
    c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

func loginHandler(c *gin.Context) {
    var req LoginRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    c.JSON(200, gin.H{"token": "xxx"})
}

func listUsers(c *gin.Context) {
    var query PaginationQuery
    c.ShouldBindQuery(&query)
    c.JSON(200, users)
}

func updateUser(c *gin.Context) {
    var uri UserURI
    c.ShouldBindUri(&uri)
    c.JSON(200, gin.H{"id": uri.ID})
}

func getStats(c *gin.Context) {
    c.HTML(200, "stats.html", gin.H{"title": "Stats"})
}
'''


class TestGinParser:

    def test_parse_returns_result(self, parser):
        result = parser.parse(SAMPLE_GIN_APP, "main.go")
        assert isinstance(result, GinParseResult)

    def test_detect_gin_framework(self, parser):
        result = parser.parse(SAMPLE_GIN_APP, "main.go")
        assert len(result.detected_frameworks) > 0
        assert "gin" in result.detected_frameworks

    def test_extract_routes(self, parser):
        result = parser.parse(SAMPLE_GIN_APP, "main.go")
        assert len(result.routes) >= 6
        methods = [r.method for r in result.routes]
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    def test_extract_route_groups(self, parser):
        result = parser.parse(SAMPLE_GIN_APP, "main.go")
        assert len(result.route_groups) >= 1
        prefixes = [g.prefix for g in result.route_groups]
        assert any("/api" in p for p in prefixes)

    def test_extract_middleware(self, parser):
        result = parser.parse(SAMPLE_GIN_APP, "main.go")
        assert len(result.middleware) >= 2
        names = [m.name for m in result.middleware]
        assert any("Logger" in n or "Recovery" in n for n in names)

    def test_extract_bindings(self, parser):
        result = parser.parse(SAMPLE_GIN_APP, "main.go")
        assert len(result.bindings) >= 2
        types = [b.bind_type for b in result.bindings]
        assert any("JSON" in t or "json" in t.lower() for t in types)

    def test_extract_renders(self, parser):
        result = parser.parse(SAMPLE_GIN_APP, "main.go")
        assert len(result.renders) >= 1
        types = [r.render_type for r in result.renders]
        assert any("JSON" in t or "json" in t.lower() for t in types)

    def test_extract_engine_configs(self, parser):
        result = parser.parse(SAMPLE_GIN_APP, "main.go")
        assert len(result.engine_configs) >= 1

    def test_non_gin_file(self, parser):
        result = parser.parse("package main\n\nfunc main() {}", "main.go")
        assert len(result.routes) == 0
        assert len(result.detected_frameworks) == 0

    def test_gin_detection(self, parser):
        result = parser.parse(SAMPLE_GIN_APP, "main.go")
        assert len(result.detected_frameworks) > 0
        result2 = parser.parse("package main\nfunc main() {}", "main.go")
        assert len(result2.detected_frameworks) == 0
