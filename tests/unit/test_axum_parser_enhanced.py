"""
Tests for EnhancedAxumParser — Axum framework analysis.

Part of CodeTrellis v5.4 Rust Framework Support.
Tests: route extraction, layers/middleware, extractors, state,
error handling, nesting, version detection, self-selection.
"""

import pytest
from codetrellis.axum_parser_enhanced import EnhancedAxumParser, AxumParseResult


@pytest.fixture
def parser():
    return EnhancedAxumParser()


# ═══════════════════════════════════════════════════════════════════
# Self-Selection Tests
# ═══════════════════════════════════════════════════════════════════

class TestAxumSelfSelection:

    def test_returns_empty_for_non_axum_file(self, parser):
        code = '''
use std::io;

fn main() {
    println!("hello");
}
'''
        result = parser.parse(code, "main.rs")
        assert result.routes == []
        assert result.detected_frameworks == []

    def test_detects_axum_import(self, parser):
        code = '''
use axum::{Router, routing::get};
'''
        result = parser.parse(code, "main.rs")
        assert len(result.detected_frameworks) > 0
        assert "axum" in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Route Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestAxumRouteExtraction:

    def test_extract_basic_routes(self, parser):
        code = '''
use axum::{Router, routing::{get, post}};

let app = Router::new()
    .route("/users", get(list_users).post(create_user))
    .route("/users/:id", get(get_user));
'''
        result = parser.parse(code, "main.rs")
        assert len(result.routes) >= 2
        paths = [r.path for r in result.routes]
        assert "/users" in paths
        assert "/users/:id" in paths

    def test_extract_method_routing(self, parser):
        code = '''
use axum::{Router, routing::{get, post, put, delete}};

Router::new()
    .route("/items", get(list).post(create))
    .route("/items/:id", get(show).put(update).delete(destroy));
'''
        result = parser.parse(code, "routes.rs")
        assert len(result.routes) >= 2

    def test_extract_handler_names(self, parser):
        code = '''
use axum::{Router, routing::get};

Router::new()
    .route("/hello", get(hello_handler));
'''
        result = parser.parse(code, "main.rs")
        assert len(result.routes) >= 1


# ═══════════════════════════════════════════════════════════════════
# Layer/Middleware Tests
# ═══════════════════════════════════════════════════════════════════

class TestAxumLayers:

    def test_extract_tower_layers(self, parser):
        code = '''
use axum::Router;
use tower_http::trace::TraceLayer;
use tower_http::cors::CorsLayer;

Router::new()
    .layer(TraceLayer::new_for_http())
    .layer(CorsLayer::permissive());
'''
        result = parser.parse(code, "app.rs")
        assert len(result.layers) >= 2

    def test_extract_service_builder_layers(self, parser):
        code = '''
use axum::Router;
use tower::ServiceBuilder;
use tower_http::trace::TraceLayer;

Router::new()
    .layer(
        ServiceBuilder::new()
            .layer(TraceLayer::new_for_http())
    );
'''
        result = parser.parse(code, "app.rs")
        assert len(result.layers) >= 1


# ═══════════════════════════════════════════════════════════════════
# Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAxumExtractors:

    def test_extract_typed_extractors(self, parser):
        code = '''
use axum::{extract::{Path, Query, State, Json}, Router};

async fn get_user(
    Path(id): Path<u64>,
    Query(params): Query<FilterParams>,
    State(state): State<AppState>,
) -> Json<User> {
    Json(User { id, name: "test".into() })
}
'''
        result = parser.parse(code, "handlers.rs")
        types = {e.extractor_type for e in result.extractors}
        assert "Path" in types
        assert "Query" in types
        assert "State" in types

    def test_extract_json_body(self, parser):
        code = '''
use axum::{Json, Router};

async fn create_user(Json(body): Json<CreateUser>) -> Json<User> {
    Json(User::from(body))
}
'''
        result = parser.parse(code, "handlers.rs")
        assert any(e.extractor_type == "Json" for e in result.extractors)


# ═══════════════════════════════════════════════════════════════════
# State Tests
# ═══════════════════════════════════════════════════════════════════

class TestAxumState:

    def test_extract_with_state(self, parser):
        code = '''
use axum::{Router, routing::get, extract::State};
use std::sync::Arc;

struct AppState { db: Pool }

let state = Arc::new(AppState { db: pool });
let app = Router::new()
    .route("/", get(handler))
    .with_state(state);
'''
        result = parser.parse(code, "main.rs")
        assert len(result.state) >= 1


# ═══════════════════════════════════════════════════════════════════
# Nest Tests
# ═══════════════════════════════════════════════════════════════════

class TestAxumNesting:

    def test_extract_nested_routers(self, parser):
        code = '''
use axum::Router;

let api = Router::new()
    .nest("/users", user_routes())
    .nest("/items", item_routes());
'''
        result = parser.parse(code, "main.rs")
        assert len(result.nests) >= 2
        paths = [n.path for n in result.nests]
        assert "/users" in paths
        assert "/items" in paths


# ═══════════════════════════════════════════════════════════════════
# Error Handling Tests
# ═══════════════════════════════════════════════════════════════════

class TestAxumErrorHandling:

    def test_extract_into_response_impl(self, parser):
        code = '''
use axum::{response::IntoResponse, http::StatusCode, Json};

struct AppError(anyhow::Error);

impl IntoResponse for AppError {
    fn into_response(self) -> axum::response::Response {
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": self.0.to_string()}))).into_response()
    }
}
'''
        result = parser.parse(code, "errors.rs")
        assert len(result.errors) >= 1
        assert any(e.name == "AppError" for e in result.errors)


# ═══════════════════════════════════════════════════════════════════
# Version Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestAxumVersionDetection:

    def test_detect_axum_ecosystem(self, parser):
        code = '''
use axum::{Router, routing::get};
use axum_extra::TypedHeader;
use tower_http::cors::CorsLayer;
'''
        result = parser.parse(code, "main.rs")
        assert "axum" in result.detected_frameworks

    def test_version_detection(self, parser):
        code = '''
use axum::{Router, routing::get, extract::State};

let app = Router::new()
    .route("/", get(handler))
    .with_state(state);
'''
        result = parser.parse(code, "main.rs")
        # .with_state() is 0.6+
        assert result.axum_version == "0.6"


# ═══════════════════════════════════════════════════════════════════
# WebSocket Tests
# ═══════════════════════════════════════════════════════════════════

class TestAxumWebSocket:

    def test_extract_websocket(self, parser):
        code = '''
use axum::{extract::ws::{WebSocket, WebSocketUpgrade}, Router, routing::get};

async fn ws_handler(ws: WebSocketUpgrade) -> impl IntoResponse {
    ws.on_upgrade(handle_socket)
}

async fn handle_socket(mut socket: WebSocket) {
    while let Some(msg) = socket.recv().await {
        // handle
    }
}
'''
        result = parser.parse(code, "ws.rs")
        assert len(result.websockets) >= 1
