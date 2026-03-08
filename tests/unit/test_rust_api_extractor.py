"""
Tests for RustAPIExtractor — actix-web, Rocket, Axum, Warp, Tide, Tonic, GraphQL.

Part of CodeTrellis v4.14 Rust Language Support.
"""

import pytest
from codetrellis.extractors.rust.api_extractor import RustAPIExtractor


@pytest.fixture
def extractor():
    return RustAPIExtractor()


# ===== ACTIX-WEB =====

class TestActixWebExtraction:
    """Tests for actix-web route extraction."""

    def test_actix_get_route(self, extractor):
        code = '''
use actix_web::{get, web, HttpResponse, Responder};

#[get("/api/users")]
async fn get_users(db: web::Data<Pool>) -> impl Responder {
    HttpResponse::Ok().json(users)
}
'''
        result = extractor.extract(code, "handlers.rs")
        assert len(result["routes"]) >= 1
        route = result["routes"][0]
        assert route.method == "GET"
        assert route.path == "/api/users"
        assert route.handler == "get_users"
        assert route.framework == "actix-web"

    def test_actix_post_route(self, extractor):
        code = '''
#[post("/api/users")]
async fn create_user(body: web::Json<CreateUser>) -> impl Responder {
    HttpResponse::Created().json(user)
}
'''
        result = extractor.extract(code, "handlers.rs")
        assert len(result["routes"]) >= 1
        route = result["routes"][0]
        assert route.method == "POST"
        assert route.path == "/api/users"

    def test_actix_multiple_routes(self, extractor):
        code = '''
#[get("/health")]
async fn health() -> impl Responder {
    HttpResponse::Ok()
}

#[delete("/api/users/{id}")]
async fn delete_user(path: web::Path<u64>) -> impl Responder {
    HttpResponse::NoContent()
}
'''
        result = extractor.extract(code, "handlers.rs")
        assert len(result["routes"]) >= 2


# ===== ROCKET =====

class TestRocketExtraction:
    """Tests for Rocket route extraction."""

    def test_rocket_get_route(self, extractor):
        code = '''
use rocket::get;
use rocket::serde::json::Json;

#[get("/api/items/<id>")]
fn get_item(id: u64) -> Json<Item> {
    Json(Item::find(id))
}
'''
        result = extractor.extract(code, "routes.rs")
        assert len(result["routes"]) >= 1
        route = result["routes"][0]
        assert route.method == "GET"
        assert route.path == "/api/items/<id>"
        assert route.framework == "rocket"


# ===== AXUM =====

class TestAxumExtraction:
    """Tests for Axum route extraction."""

    def test_axum_router(self, extractor):
        code = '''
let app = Router::new()
    .route("/api/users", get(list_users).post(create_user))
    .route("/api/users/:id", get(get_user).put(update_user).delete(delete_user));
'''
        result = extractor.extract(code, "main.rs")
        routes = result["routes"]
        assert len(routes) >= 2
        # Should detect multiple methods per path
        frameworks = [r.framework for r in routes]
        assert any(f == "axum" for f in frameworks)


# ===== TONIC gRPC =====

class TestTonicGRPCExtraction:
    """Tests for Tonic gRPC service extraction."""

    def test_tonic_service(self, extractor):
        code = '''
#[tonic::async_trait]
impl Greeter for MyGreeter {
    async fn say_hello(&self, request: Request<HelloRequest>) -> Result<Response<HelloReply>, Status> {
        let reply = HelloReply { message: format!("Hello {}", request.into_inner().name) };
        Ok(Response::new(reply))
    }
}
'''
        result = extractor.extract(code, "grpc.rs")
        assert len(result["grpc_services"]) >= 1
        svc = result["grpc_services"][0]
        assert svc.name == "Greeter"


# ===== GRAPHQL =====

class TestGraphQLExtraction:
    """Tests for async-graphql extraction."""

    def test_graphql_object(self, extractor):
        code = '''
#[Object]
impl QueryRoot {
    async fn users(&self, ctx: &Context<'_>) -> Vec<User> {
        ctx.data::<Database>().unwrap().get_users().await
    }
}
'''
        result = extractor.extract(code, "query.rs")
        assert len(result["graphql"]) >= 1
        gql = result["graphql"][0]
        assert gql.name == "QueryRoot"
        assert gql.query_type == "Query"
