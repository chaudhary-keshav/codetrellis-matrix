"""
Tests for EnhancedChiParser.

Part of CodeTrellis v5.2 Go Framework Support.
Tests cover:
- Route extraction (Get, Post, Put, Delete, Patch)
- Route group extraction via r.Route()
- Mount extraction (sub-router mounting)
- Middleware extraction (Use, With, built-in middleware)
- Framework version detection (chi v1.x → v5.x)
"""

import pytest
from codetrellis.chi_parser_enhanced import (
    EnhancedChiParser,
    ChiParseResult,
)


@pytest.fixture
def parser():
    return EnhancedChiParser()


SAMPLE_CHI_APP = '''
package main

import (
    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
    "net/http"
)

func main() {
    r := chi.NewRouter()

    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(middleware.RequestID)
    r.Use(middleware.RealIP)
    r.Use(middleware.Timeout(60 * time.Second))

    r.Get("/health", healthCheck)
    r.Post("/login", loginHandler)

    r.Route("/api/v1", func(r chi.Router) {
        r.Use(authMiddleware)
        r.Get("/users", listUsers)
        r.Post("/users", createUser)
        r.Put("/users/{id}", updateUser)
        r.Delete("/users/{id}", deleteUser)

        r.Route("/articles/{articleID}", func(r chi.Router) {
            r.Use(ArticleCtx)
            r.Get("/", getArticle)
            r.Put("/", updateArticle)
            r.Delete("/", deleteArticle)
        })
    })

    r.Mount("/admin", adminRouter())
    r.Mount("/debug", middleware.Profiler())

    r.With(rateLimiter).Get("/public", publicHandler)

    http.ListenAndServe(":8080", r)
}

func adminRouter() http.Handler {
    r := chi.NewRouter()
    r.Use(adminAuth)
    r.Get("/stats", getStats)
    return r
}

func healthCheck(w http.ResponseWriter, r *http.Request) {
    userID := chi.URLParam(r, "userID")
    w.Write([]byte("ok"))
}
'''


class TestChiParser:

    def test_parse_returns_result(self, parser):
        result = parser.parse(SAMPLE_CHI_APP, "main.go")
        assert isinstance(result, ChiParseResult)

    def test_detect_chi_framework(self, parser):
        result = parser.parse(SAMPLE_CHI_APP, "main.go")
        assert len(result.detected_frameworks) > 0
        assert "chi" in result.detected_frameworks

    def test_extract_routes(self, parser):
        result = parser.parse(SAMPLE_CHI_APP, "main.go")
        assert len(result.routes) >= 5
        methods = [r.method for r in result.routes]
        assert "GET" in methods or "Get" in methods
        assert "POST" in methods or "Post" in methods

    def test_extract_route_groups(self, parser):
        result = parser.parse(SAMPLE_CHI_APP, "main.go")
        assert len(result.route_groups) >= 1

    def test_extract_mounts(self, parser):
        result = parser.parse(SAMPLE_CHI_APP, "main.go")
        assert len(result.mounts) >= 1
        patterns = [m.path for m in result.mounts]
        assert any("/admin" in p for p in patterns)

    def test_extract_middleware(self, parser):
        result = parser.parse(SAMPLE_CHI_APP, "main.go")
        assert len(result.middleware) >= 3
        names = [m.name for m in result.middleware]
        assert any("Logger" in n for n in names)

    def test_non_chi_file(self, parser):
        result = parser.parse("package main\n\nfunc main() {}", "main.go")
        assert len(result.routes) == 0
        assert len(result.detected_frameworks) == 0

    def test_chi_detection(self, parser):
        result = parser.parse(SAMPLE_CHI_APP, "main.go")
        assert len(result.detected_frameworks) > 0
        result2 = parser.parse("package main\nfunc main() {}", "main.go")
        assert len(result2.detected_frameworks) == 0
