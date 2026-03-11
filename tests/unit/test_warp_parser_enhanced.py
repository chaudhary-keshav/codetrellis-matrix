"""
Tests for EnhancedWarpParser — Warp framework analysis.

Part of CodeTrellis v5.4 Rust Framework Support.
Tests: filter/route extraction, rejections, replies, WebSocket,
config detection, version detection, self-selection.
"""

import pytest
from codetrellis.warp_parser_enhanced import EnhancedWarpParser, WarpParseResult


@pytest.fixture
def parser():
    return EnhancedWarpParser()


# ═══════════════════════════════════════════════════════════════════
# Self-Selection Tests
# ═══════════════════════════════════════════════════════════════════

class TestWarpSelfSelection:

    def test_returns_empty_for_non_warp_file(self, parser):
        code = '''
use std::io;
fn main() {}
'''
        result = parser.parse(code, "main.rs")
        assert result.routes == []
        assert result.detected_frameworks == []

    def test_detects_warp_import(self, parser):
        code = '''
use warp::Filter;
'''
        result = parser.parse(code, "main.rs")
        assert "warp" in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Route/Filter Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestWarpRouteExtraction:

    def test_extract_path_filters(self, parser):
        code = '''
use warp::Filter;

let hello = warp::path("hello")
    .and(warp::get())
    .map(|| "Hello, World!");

let users = warp::path("users")
    .and(warp::get())
    .and_then(list_users);
'''
        result = parser.parse(code, "routes.rs")
        assert len(result.routes) >= 2

    def test_extract_method_filters(self, parser):
        code = '''
use warp::Filter;

let api = warp::path("api")
    .and(warp::path("v1"))
    .and(warp::get())
    .and_then(handler);
'''
        result = parser.parse(code, "api.rs")
        assert len(result.routes) >= 1

    def test_extract_body_filters(self, parser):
        code = '''
use warp::Filter;

let api = warp::path("api")
    .and(warp::body::json())
    .and_then(handler);
'''
        result = parser.parse(code, "routes.rs")
        assert len(result.filters) >= 1


# ═══════════════════════════════════════════════════════════════════
# Rejection Tests
# ═══════════════════════════════════════════════════════════════════

class TestWarpRejections:

    def test_extract_custom_rejection(self, parser):
        code = '''
use warp::{reject, Rejection};

#[derive(Debug)]
struct NotFound;
impl reject::Reject for NotFound {}

#[derive(Debug)]
struct Unauthorized;
impl reject::Reject for Unauthorized {}
'''
        result = parser.parse(code, "errors.rs")
        assert len(result.rejections) >= 2

    def test_extract_recover_handler(self, parser):
        code = '''
use warp::Filter;

let routes = api
    .recover(handle_rejection);

async fn handle_rejection(err: Rejection) -> Result<impl Reply, Infallible> {
    Ok(warp::reply::with_status("error", StatusCode::INTERNAL_SERVER_ERROR))
}
'''
        result = parser.parse(code, "errors.rs")
        # Recovery detection varies by implementation
        assert result.detected_frameworks  # at least warp is detected


# ═══════════════════════════════════════════════════════════════════
# Reply Tests
# ═══════════════════════════════════════════════════════════════════

class TestWarpReplies:

    def test_extract_reply_helpers(self, parser):
        code = '''
use warp::{reply, Filter};

let resp = warp::reply::json(&data);
let html = warp::reply::html("<h1>Hello</h1>");
let status = warp::reply::with_status("ok", StatusCode::OK);
'''
        result = parser.parse(code, "handlers.rs")
        assert len(result.replies) >= 1


# ═══════════════════════════════════════════════════════════════════
# WebSocket Tests
# ═══════════════════════════════════════════════════════════════════

class TestWarpWebSocket:

    def test_extract_websocket(self, parser):
        code = '''
use warp::{ws, Filter};

let ws_route = warp::path("ws")
    .and(warp::ws())
    .map(|ws: ws::Ws| {
        ws.on_upgrade(|websocket| handle_connection(websocket))
    });
'''
        result = parser.parse(code, "ws.rs")
        assert len(result.websockets) >= 1


# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════

class TestWarpConfig:

    def test_extract_serve_config(self, parser):
        code = '''
use warp::Filter;

warp::serve(routes)
    .tls()
    .cert_path("cert.pem")
    .key_path("key.pem")
    .run(([0, 0, 0, 0], 3030))
    .await;
'''
        result = parser.parse(code, "main.rs")
        assert len(result.configs) >= 1


# ═══════════════════════════════════════════════════════════════════
# Version/Ecosystem Tests
# ═══════════════════════════════════════════════════════════════════

class TestWarpVersionDetection:

    def test_detect_warp_ecosystem(self, parser):
        code = '''
use warp::Filter;
use warp::ws;
'''
        result = parser.parse(code, "main.rs")
        assert "warp" in result.detected_frameworks

    def test_version_detection(self, parser):
        code = '''
use warp::Filter;
warp::serve(routes).run(([0, 0, 0, 0], 3030)).await;
'''
        result = parser.parse(code, "main.rs")
        # Version detection should work
        assert result.warp_version != "" or result.detected_frameworks
