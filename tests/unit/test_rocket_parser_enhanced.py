"""
Tests for EnhancedRocketParser — Rocket framework analysis.

Part of CodeTrellis v5.4 Rust Framework Support.
Tests: route extraction, catchers, fairings, guards, state,
responders, mount detection, version detection, self-selection.
"""

import pytest
from codetrellis.rocket_parser_enhanced import EnhancedRocketParser, RocketParseResult


@pytest.fixture
def parser():
    return EnhancedRocketParser()


# ═══════════════════════════════════════════════════════════════════
# Self-Selection Tests
# ═══════════════════════════════════════════════════════════════════

class TestRocketSelfSelection:

    def test_returns_empty_for_non_rocket_file(self, parser):
        code = '''
use std::collections::HashMap;
fn main() { }
'''
        result = parser.parse(code, "main.rs")
        assert result.routes == []
        assert result.detected_frameworks == []

    def test_detects_rocket_import(self, parser):
        code = '''
use rocket::{get, routes, launch};
'''
        result = parser.parse(code, "main.rs")
        assert "rocket" in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Route Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestRocketRouteExtraction:

    def test_extract_attribute_routes(self, parser):
        code = '''
use rocket::{get, post};

#[get("/hello")]
fn hello() -> &'static str {
    "Hello, world!"
}

#[post("/users", data = "<user>")]
fn create_user(user: Json<User>) -> Json<User> {
    user
}
'''
        result = parser.parse(code, "routes.rs")
        assert len(result.routes) >= 2
        methods = [r.method for r in result.routes]
        assert "GET" in methods
        assert "POST" in methods
        paths = [r.path for r in result.routes]
        assert "/hello" in paths
        assert "/users" in paths

    def test_extract_all_methods(self, parser):
        code = '''
use rocket::{get, post, put, delete, patch};

#[get("/test")]
fn test_get() -> &'static str { "ok" }

#[put("/test")]
fn test_put() -> &'static str { "ok" }

#[delete("/test")]
fn test_delete() -> &'static str { "ok" }
'''
        result = parser.parse(code, "routes.rs")
        methods = {r.method for r in result.routes}
        assert "GET" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    def test_handler_name_extraction(self, parser):
        code = '''
use rocket::get;

#[get("/items")]
fn list_items() -> Json<Vec<Item>> {
    Json(vec![])
}
'''
        result = parser.parse(code, "items.rs")
        assert any(r.handler == "list_items" for r in result.routes)


# ═══════════════════════════════════════════════════════════════════
# Catcher Tests
# ═══════════════════════════════════════════════════════════════════

class TestRocketCatchers:

    def test_extract_catchers(self, parser):
        code = '''
use rocket::{catch, catchers, Request};
use rocket::serde::json::Json;

#[catch(404)]
fn not_found(req: &Request) -> Json<ErrorResponse> {
    Json(ErrorResponse { message: "Not Found".into() })
}

#[catch(500)]
fn internal_error() -> &'static str {
    "Internal Server Error"
}
'''
        result = parser.parse(code, "catchers.rs")
        assert len(result.catchers) >= 2
        codes = [c.status_code for c in result.catchers]
        assert 404 in codes
        assert 500 in codes


# ═══════════════════════════════════════════════════════════════════
# Fairing Tests
# ═══════════════════════════════════════════════════════════════════

class TestRocketFairings:

    def test_extract_fairing_impl(self, parser):
        code = '''
use rocket::{fairing::{Fairing, Info, Kind}, Request, Response, Data};

pub struct Counter;

#[rocket::async_trait]
impl Fairing for Counter {
    fn info(&self) -> Info {
        Info { name: "Request Counter", kind: Kind::Request }
    }

    async fn on_request(&self, req: &mut Request<'_>, _data: &mut Data<'_>) {
        // count request
    }
}
'''
        result = parser.parse(code, "fairings.rs")
        assert len(result.fairings) >= 1
        assert any(f.name == "Counter" for f in result.fairings)


# ═══════════════════════════════════════════════════════════════════
# Guard Tests
# ═══════════════════════════════════════════════════════════════════

class TestRocketGuards:

    def test_extract_request_guard(self, parser):
        code = '''
use rocket::request::{self, FromRequest, Request, Outcome};

pub struct ApiKey(String);

#[rocket::async_trait]
impl<'r> FromRequest<'r> for ApiKey {
    type Error = ApiKeyError;

    async fn from_request(req: &'r Request<'_>) -> request::Outcome<Self, Self::Error> {
        match req.headers().get_one("X-API-Key") {
            Some(key) => Outcome::Success(ApiKey(key.to_string())),
            None => Outcome::Error((Status::Unauthorized, ApiKeyError::Missing)),
        }
    }
}
'''
        result = parser.parse(code, "guards.rs")
        assert len(result.guards) >= 1
        assert any(g.name == "ApiKey" for g in result.guards)


# ═══════════════════════════════════════════════════════════════════
# State Tests
# ═══════════════════════════════════════════════════════════════════

class TestRocketState:

    def test_extract_managed_state(self, parser):
        code = '''
use rocket::{State, launch, routes};

struct DbPool(Pool);

#[launch]
fn rocket() -> _ {
    rocket::build()
        .manage(DbPool(create_pool()))
        .mount("/", routes![index])
}
'''
        result = parser.parse(code, "main.rs")
        assert len(result.state) >= 1


# ═══════════════════════════════════════════════════════════════════
# Mount Tests
# ═══════════════════════════════════════════════════════════════════

class TestRocketMounts:

    def test_extract_mounts(self, parser):
        code = '''
use rocket::{launch, routes};

#[launch]
fn rocket() -> _ {
    rocket::build()
        .mount("/api", routes![list_users, create_user])
        .mount("/admin", routes![dashboard])
}
'''
        result = parser.parse(code, "main.rs")
        assert len(result.mounts) >= 2
        paths = [m.base for m in result.mounts]
        assert "/api" in paths
        assert "/admin" in paths


# ═══════════════════════════════════════════════════════════════════
# Version Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestRocketVersionDetection:

    def test_detect_v5_features(self, parser):
        code = '''
#[launch]
fn rocket() -> _ {
    rocket::build()
        .mount("/", routes![index])
}
'''
        result = parser.parse(code, "main.rs")
        assert result.rocket_version in ("0.5", "0.4")

    def test_detect_ecosystem(self, parser):
        code = '''
use rocket::serde::json::Json;
use rocket_db_pools::Database;
use rocket_dyn_templates::Template;
'''
        result = parser.parse(code, "main.rs")
        assert "rocket" in result.detected_frameworks
