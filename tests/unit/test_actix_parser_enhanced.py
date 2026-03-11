"""
Tests for EnhancedActixParser — Actix Web framework analysis.

Part of CodeTrellis v5.4 Rust Framework Support.
Tests: route extraction, middleware, extractors, state, error handling,
WebSocket, config, version detection, self-selection.
"""

import pytest
from codetrellis.actix_parser_enhanced import EnhancedActixParser, ActixParseResult


@pytest.fixture
def parser():
    return EnhancedActixParser()


# ═══════════════════════════════════════════════════════════════════
# Self-Selection Tests
# ═══════════════════════════════════════════════════════════════════

class TestActixSelfSelection:

    def test_returns_empty_for_non_actix_file(self, parser):
        code = '''
use std::collections::HashMap;

fn main() {
    let map = HashMap::new();
}
'''
        result = parser.parse(code, "main.rs")
        assert result.routes == []
        assert result.middleware == []
        assert result.detected_frameworks == []

    def test_detects_actix_use_import(self, parser):
        code = '''
use actix_web::{get, web, App, HttpServer, Responder};
'''
        result = parser.parse(code, "main.rs")
        assert len(result.detected_frameworks) > 0
        assert "actix-web" in result.detected_frameworks

    def test_detects_actix_attribute(self, parser):
        code = '''
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| App::new()).bind("127.0.0.1:8080")?.run().await
}
'''
        result = parser.parse(code, "main.rs")
        assert len(result.detected_frameworks) > 0


# ═══════════════════════════════════════════════════════════════════
# Route Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestActixRouteExtraction:

    def test_extract_attribute_routes(self, parser):
        code = '''
use actix_web::{get, post, web, HttpResponse, Responder};

#[get("/api/users")]
async fn list_users() -> impl Responder {
    HttpResponse::Ok().json(vec!["user1"])
}

#[post("/api/users")]
async fn create_user(body: web::Json<CreateUser>) -> impl Responder {
    HttpResponse::Created().finish()
}
'''
        result = parser.parse(code, "handlers.rs")
        assert len(result.routes) >= 2
        methods = [r.method for r in result.routes]
        assert "GET" in methods
        assert "POST" in methods
        paths = [r.path for r in result.routes]
        assert "/api/users" in paths

    def test_extract_all_http_methods(self, parser):
        code = '''
use actix_web::{get, post, put, delete, patch, head, options, web};

#[get("/test")]
async fn get_handler() -> &'static str { "ok" }

#[post("/test")]
async fn post_handler() -> &'static str { "ok" }

#[put("/test")]
async fn put_handler() -> &'static str { "ok" }

#[delete("/test")]
async fn delete_handler() -> &'static str { "ok" }

#[patch("/test")]
async fn patch_handler() -> &'static str { "ok" }
'''
        result = parser.parse(code, "routes.rs")
        methods = {r.method for r in result.routes}
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods
        assert "PATCH" in methods

    def test_extract_resource_routes(self, parser):
        code = '''
use actix_web::{web, App};

fn config(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::resource("/items")
            .route(web::get().to(list_items))
            .route(web::post().to(create_item))
    );
}
'''
        result = parser.parse(code, "config.rs")
        assert len(result.routes) >= 2

    def test_handler_name_extraction(self, parser):
        code = '''
use actix_web::{get, Responder};

#[get("/hello")]
async fn hello_world() -> impl Responder {
    "Hello!"
}
'''
        result = parser.parse(code, "handlers.rs")
        handlers = [r.handler for r in result.routes]
        assert "hello_world" in handlers


# ═══════════════════════════════════════════════════════════════════
# Scope/Resource Tests
# ═══════════════════════════════════════════════════════════════════

class TestActixScopes:

    def test_extract_scopes(self, parser):
        code = '''
use actix_web::{web, App};

App::new()
    .service(
        web::scope("/api/v1")
            .service(users_scope())
    );
'''
        result = parser.parse(code, "app.rs")
        assert len(result.scopes) >= 1
        assert any(s.path == "/api/v1" for s in result.scopes)

    def test_extract_resource(self, parser):
        code = '''
use actix_web::{web, App};

App::new()
    .service(
        web::resource("/items/{id}")
            .route(web::get().to(get_item))
    );
'''
        result = parser.parse(code, "app.rs")
        # web::resource is also caught by RESOURCE_SCOPE
        assert len(result.scopes) >= 1


# ═══════════════════════════════════════════════════════════════════
# Middleware Tests
# ═══════════════════════════════════════════════════════════════════

class TestActixMiddleware:

    def test_extract_wrap_middleware(self, parser):
        code = '''
use actix_web::{App, middleware};

App::new()
    .wrap(middleware::Logger::default())
    .wrap(middleware::Compress::default());
'''
        result = parser.parse(code, "app.rs")
        assert len(result.middleware) >= 2

    def test_extract_from_fn_middleware(self, parser):
        code = '''
use actix_web::{middleware, App};

async fn auth_check(req: ServiceRequest, next: Next<impl MessageBody>) -> Result<ServiceResponse<impl MessageBody>, Error> {
    next.call(req).await
}

App::new()
    .wrap(middleware::from_fn(auth_check));
'''
        result = parser.parse(code, "app.rs")
        assert any(m.name == "auth_check" for m in result.middleware)


# ═══════════════════════════════════════════════════════════════════
# Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestActixExtractors:

    def test_extract_typed_extractors(self, parser):
        code = '''
use actix_web::{get, web, HttpResponse};

#[get("/users/{id}")]
async fn get_user(
    path: web::Path<u64>,
    query: web::Query<FilterParams>,
    data: web::Data<AppState>,
) -> HttpResponse {
    HttpResponse::Ok().finish()
}
'''
        result = parser.parse(code, "handlers.rs")
        types = {e.extractor_type for e in result.extractors}
        assert "Path" in types
        assert "Query" in types
        assert "Data" in types

    def test_extract_json_body(self, parser):
        code = '''
use actix_web::{post, web, HttpResponse};

#[post("/users")]
async fn create_user(body: web::Json<CreateUser>) -> HttpResponse {
    HttpResponse::Created().json(body.into_inner())
}
'''
        result = parser.parse(code, "handlers.rs")
        assert any(e.extractor_type == "Json" for e in result.extractors)


# ═══════════════════════════════════════════════════════════════════
# State Tests
# ═══════════════════════════════════════════════════════════════════

class TestActixState:

    def test_extract_app_data(self, parser):
        code = '''
use actix_web::{web, App};

struct AppState {
    db: Pool,
}

App::new()
    .app_data(web::Data::new(AppState { db: pool }));
'''
        result = parser.parse(code, "main.rs")
        assert len(result.app_state) >= 1


# ═══════════════════════════════════════════════════════════════════
# Error Handling Tests
# ═══════════════════════════════════════════════════════════════════

class TestActixErrorHandling:

    def test_extract_response_error_impl(self, parser):
        code = '''
use actix_web::{HttpResponse, ResponseError};
use std::fmt;

#[derive(Debug)]
struct MyError;

impl fmt::Display for MyError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "My error")
    }
}

impl ResponseError for MyError {
    fn error_response(&self) -> HttpResponse {
        HttpResponse::InternalServerError().finish()
    }
}
'''
        result = parser.parse(code, "errors.rs")
        assert len(result.error_handlers) >= 1
        assert any(e.name == "MyError" for e in result.error_handlers)


# ═══════════════════════════════════════════════════════════════════
# Version Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestActixVersionDetection:

    def test_detect_v4_features(self, parser):
        code = '''
use actix_web::{middleware, App};
use actix_web::middleware::from_fn;
'''
        result = parser.parse(code, "main.rs")
        assert result.actix_version == "4.0"

    def test_detect_v3_features(self, parser):
        code = '''
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| App::new()).bind("127.0.0.1:8080")?.run().await
}
'''
        result = parser.parse(code, "main.rs")
        assert result.actix_version == "3.0"

    def test_detect_v2_features(self, parser):
        code = '''
use actix_web::{web, HttpServer};

HttpServer::new(|| {
    App::new().route("/", web::get().to(index))
})
'''
        result = parser.parse(code, "main.rs")
        assert result.actix_version in ("2.0", "3.0")


# ═══════════════════════════════════════════════════════════════════
# Ecosystem Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestActixEcosystem:

    def test_detect_cors(self, parser):
        code = '''
use actix_web::App;
use actix_cors::Cors;

App::new().wrap(Cors::permissive());
'''
        result = parser.parse(code, "app.rs")
        assert "actix-cors" in result.detected_frameworks

    def test_detect_session(self, parser):
        code = '''
use actix_web::App;
use actix_session::SessionMiddleware;
'''
        result = parser.parse(code, "app.rs")
        assert "actix-session" in result.detected_frameworks

    def test_detect_multiple_ecosystem(self, parser):
        code = '''
use actix_web::{App, HttpServer};
use actix_cors::Cors;
use actix_identity::IdentityMiddleware;
use actix_files;
'''
        result = parser.parse(code, "app.rs")
        assert "actix-web" in result.detected_frameworks
        assert "actix-cors" in result.detected_frameworks
        assert "actix-identity" in result.detected_frameworks
        assert "actix-files" in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════

class TestActixConfig:

    def test_extract_server_config(self, parser):
        code = '''
use actix_web::HttpServer;

HttpServer::new(|| App::new())
    .workers(4)
    .bind("0.0.0.0:8080")?
    .run()
    .await
'''
        result = parser.parse(code, "main.rs")
        assert len(result.configs) >= 1

    def test_extract_configure_fn(self, parser):
        code = '''
use actix_web::{web, App};

fn api_config(cfg: &mut web::ServiceConfig) {
    cfg.service(web::resource("/users").to(list_users));
}

App::new().configure(api_config);
'''
        result = parser.parse(code, "main.rs")
        assert len(result.configs) >= 1


# ═══════════════════════════════════════════════════════════════════
# Test Utilities Tests
# ═══════════════════════════════════════════════════════════════════

class TestActixTestUtils:

    def test_extract_test_utilities(self, parser):
        code = '''
use actix_web::{test, App};

#[actix_web::test]
async fn test_hello() {
    let app = test::init_service(App::new().service(hello)).await;
    let req = test::TestRequest::get().uri("/hello").to_request();
    let resp = test::call_service(&app, req).await;
    assert!(resp.status().is_success());
}
'''
        result = parser.parse(code, "tests.rs")
        assert len(result.tests) >= 2
