"""
Tests for Vert.x extractors and EnhancedVertxParser.

Part of CodeTrellis v4.95 Vert.x Framework Support.
Tests cover:
- Verticle extraction (AbstractVerticle, deployVerticle, DeploymentOptions)
- Route extraction (router.get/post/put/delete, handlers)
- Event bus extraction (consumer, publish, send, request)
- Data extraction (PgPool, MongoClient, Redis)
- API extraction (WebSocket, auth, cluster managers)
- Parser integration (framework detection, version detection, is_vertx_file)
"""

import pytest
from codetrellis.vertx_parser_enhanced import EnhancedVertxParser, VertxParseResult
from codetrellis.extractors.vertx import (
    VertxVerticleExtractor,
    VertxRouteExtractor,
    VertxEventBusExtractor,
    VertxDataExtractor,
    VertxApiExtractor,
)


@pytest.fixture
def parser():
    return EnhancedVertxParser()


@pytest.fixture
def verticle_extractor():
    return VertxVerticleExtractor()


@pytest.fixture
def route_extractor():
    return VertxRouteExtractor()


@pytest.fixture
def eventbus_extractor():
    return VertxEventBusExtractor()


@pytest.fixture
def data_extractor():
    return VertxDataExtractor()


@pytest.fixture
def api_extractor():
    return VertxApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Verticle Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestVertxVerticleExtractor:

    def test_extract_abstract_verticle(self, verticle_extractor):
        content = """
package com.example;

import io.vertx.core.AbstractVerticle;

public class MainVerticle extends AbstractVerticle {
    @Override
    public void start() {
        vertx.createHttpServer()
            .requestHandler(req -> req.response().end("Hello"))
            .listen(8080);
    }
}
"""
        result = verticle_extractor.extract(content)
        assert len(result['verticles']) > 0
        assert result['verticles'][0].name == 'MainVerticle'

    def test_extract_deploy_verticle(self, verticle_extractor):
        content = """
vertx.deployVerticle(new MyVerticle(), new DeploymentOptions().setInstances(4));
vertx.deployVerticle("com.example.WorkerVerticle", new DeploymentOptions().setWorker(true));
"""
        result = verticle_extractor.extract(content)
        assert len(result['deployments']) > 0

    def test_empty_content(self, verticle_extractor):
        result = verticle_extractor.extract("")
        assert result['verticles'] == []
        assert result['deployments'] == []


# ═══════════════════════════════════════════════════════════════════
# Route Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestVertxRouteExtractor:

    def test_extract_routes(self, route_extractor):
        content = """
Router router = Router.router(vertx);
router.get("/api/users").handler(this::getUsers);
router.post("/api/users").handler(this::createUser);
router.put("/api/users/:id").handler(this::updateUser);
router.delete("/api/users/:id").handler(this::deleteUser);
"""
        result = route_extractor.extract(content)
        assert len(result['routes']) >= 4

    def test_extract_mount_subrouter(self, route_extractor):
        content = """
router.mountSubRouter("/api/v2", apiRouter);
"""
        result = route_extractor.extract(content)
        assert len(result['sub_routers']) > 0


# ═══════════════════════════════════════════════════════════════════
# Event Bus Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestVertxEventBusExtractor:

    def test_extract_consumers(self, eventbus_extractor):
        content = """
vertx.eventBus().consumer("user.created", message -> {
    JsonObject user = (JsonObject) message.body();
    System.out.println("New user: " + user.getString("name"));
});
vertx.eventBus().localConsumer("local.event", handler);
"""
        result = eventbus_extractor.extract(content)
        assert len(result['consumers']) >= 2

    def test_extract_publishers(self, eventbus_extractor):
        content = """
vertx.eventBus().publish("news.update", new JsonObject().put("title", "Breaking"));
vertx.eventBus().send("process.order", orderJson);
vertx.eventBus().request("math.add", data, reply -> {});
"""
        result = eventbus_extractor.extract(content)
        assert len(result['publishers']) >= 3


# ═══════════════════════════════════════════════════════════════════
# Data Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestVertxDataExtractor:

    def test_extract_pg_pool(self, data_extractor):
        content = """
import io.vertx.pgclient.PgPool;

PgPool pool = PgPool.pool(vertx, connectOptions, poolOptions);
pool.query("SELECT * FROM users").execute(ar -> {});
"""
        result = data_extractor.extract(content)
        assert len(result['sql_clients']) > 0

    def test_extract_mongo_client(self, data_extractor):
        content = """
import io.vertx.ext.mongo.MongoClient;

MongoClient client = MongoClient.createShared(vertx, config);
client.find("users", query, res -> {});
"""
        result = data_extractor.extract(content)
        assert len(result['mongo_clients']) > 0


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestVertxApiExtractor:

    def test_extract_websocket(self, api_extractor):
        content = """
vertx.createHttpServer().webSocketHandler(ws -> {
    ws.handler(buffer -> {
        ws.writeTextMessage("Echo: " + buffer.toString());
    });
}).listen(8080);
"""
        result = api_extractor.extract(content)
        assert result['websockets']

    def test_extract_auth(self, api_extractor):
        content = """
JWTAuth jwtAuth = JWTAuth.create(vertx, new JWTAuthOptions());
OAuth2Auth oauth2 = OAuth2Auth.create(vertx, options);
"""
        result = api_extractor.extract(content)
        assert len(result['auth_providers']) >= 2


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedVertxParser:

    def test_is_vertx_file(self, parser):
        content = """
import io.vertx.core.AbstractVerticle;
public class Main extends AbstractVerticle {}
"""
        assert parser.is_vertx_file(content) is True

    def test_is_not_vertx_file(self, parser):
        content = """
import java.util.List;
public class Main {}
"""
        assert parser.is_vertx_file(content) is False

    def test_detect_frameworks(self, parser):
        content = """
import io.vertx.core.Vertx;
import io.vertx.ext.web.Router;
import io.vertx.pgclient.PgPool;
import io.vertx.ext.auth.jwt.JWTAuth;
"""
        frameworks = parser._detect_frameworks(content)
        assert 'vertx_core' in frameworks
        assert 'vertx_web' in frameworks

    def test_detect_version_4x(self, parser):
        content = """
import io.vertx.pgclient.PgPool;
Future.succeededFuture(result);
"""
        version = parser._detect_version(content)
        assert '4.x' in version

    def test_parse_full(self, parser):
        content = """
import io.vertx.core.AbstractVerticle;
import io.vertx.ext.web.Router;

public class MainVerticle extends AbstractVerticle {
    @Override
    public void start() {
        Router router = Router.router(vertx);
        router.get("/api/hello").handler(ctx -> {
            ctx.response().end("Hello World");
        });
        vertx.eventBus().consumer("greetings", msg -> {});
        vertx.createHttpServer()
            .requestHandler(router)
            .listen(8080);
    }
}
"""
        result = parser.parse(content)
        assert isinstance(result, VertxParseResult)
        assert len(result.verticles) > 0
        assert len(result.routes) > 0

    def test_parse_empty(self, parser):
        result = parser.parse("")
        assert isinstance(result, VertxParseResult)
        assert result.verticles == []
        assert result.routes == []

    def test_parse_returns_dataclass_items(self, parser):
        content = """
import io.vertx.core.AbstractVerticle;
public class TestVerticle extends AbstractVerticle {
    public void start() {}
}
"""
        result = parser.parse(content)
        for v in result.verticles:
            assert hasattr(v, 'name')
