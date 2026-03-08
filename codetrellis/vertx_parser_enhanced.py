"""
EnhancedVertxParser v1.0 - Comprehensive Vert.x parser using all extractors.

This parser integrates all Vert.x extractors to provide complete parsing of
Vert.x application files. It runs as a supplementary layer on top of the
Java parser, extracting Vert.x-specific semantics.

Supports:
- Vert.x 2.x (legacy platform, module system)
- Vert.x 3.x (core rewrite, Router, clustered event bus, service discovery)
- Vert.x 4.x (Future-based API, reactive SQL clients, Mutiny bindings, virtual threads)

Vert.x-specific extraction:
- Verticles: AbstractVerticle, worker verticles, deployment options
- Routing: Router, sub-routers, HTTP handlers, middleware chain
- Event Bus: consumers, publishers, request-reply, message codecs
- Data: reactive SQL clients (Pg/MySQL/MSSQL/Oracle/DB2/JDBC), Mongo, Redis
- WebSocket: server handlers, SockJS bridges
- Auth: JWT, OAuth2, basic, LDAP, SQL/Mongo auth providers
- Clustering: Hazelcast, Infinispan, Ignite, Zookeeper managers
- Service Proxy: @ProxyGen, ServiceBinder

Framework detection (40+ Vert.x ecosystem patterns):
- Core: vertx-core, vertx-web, vertx-web-client
- Data: vertx-pg-client, vertx-mysql-client, vertx-mongo-client, vertx-redis-client
- Auth: vertx-auth-jwt, vertx-auth-oauth2, vertx-auth-common
- Cluster: vertx-hazelcast, vertx-infinispan, vertx-ignite, vertx-zookeeper
- Messaging: vertx-kafka-client, vertx-amqp-client, vertx-rabbitmq-client
- gRPC: vertx-grpc, vertx-grpc-server, vertx-grpc-client
- Testing: vertx-junit5, vertx-unit
- Reactive: smallrye-mutiny-vertx-core, vertx-rx-java3
- Micro: vertx-circuit-breaker, vertx-service-discovery, vertx-config
- OpenAPI: vertx-web-api-contract, vertx-web-openapi

Part of CodeTrellis v4.95 - Vert.x Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

# Import all Vert.x extractors
from .extractors.vertx import (
    VertxVerticleExtractor, VertxVerticleInfo, VertxDeploymentInfo,
    VertxRouteExtractor, VertxRouteInfo, VertxHandlerInfo, VertxSubRouterInfo,
    VertxEventBusExtractor, VertxEventBusConsumerInfo, VertxEventBusPublisherInfo, VertxCodecInfo,
    VertxDataExtractor, VertxSQLClientInfo, VertxMongoClientInfo, VertxRedisClientInfo,
    VertxApiExtractor, VertxWebSocketInfo, VertxAuthProviderInfo, VertxClusterInfo, VertxServiceProxyInfo,
)


@dataclass
class VertxParseResult:
    """Complete parse result for a Vert.x file."""
    file_path: str
    file_type: str = "vertx"

    # Verticles
    verticles: List[VertxVerticleInfo] = field(default_factory=list)
    deployments: List[VertxDeploymentInfo] = field(default_factory=list)

    # Routes
    routes: List[VertxRouteInfo] = field(default_factory=list)
    handlers: List[VertxHandlerInfo] = field(default_factory=list)
    sub_routers: List[VertxSubRouterInfo] = field(default_factory=list)

    # Event Bus
    event_bus_consumers: List[VertxEventBusConsumerInfo] = field(default_factory=list)
    event_bus_publishers: List[VertxEventBusPublisherInfo] = field(default_factory=list)
    codecs: List[VertxCodecInfo] = field(default_factory=list)

    # Data Access
    sql_clients: List[VertxSQLClientInfo] = field(default_factory=list)
    mongo_clients: List[VertxMongoClientInfo] = field(default_factory=list)
    redis_clients: List[VertxRedisClientInfo] = field(default_factory=list)

    # API / Infrastructure
    websockets: List[VertxWebSocketInfo] = field(default_factory=list)
    auth_providers: List[VertxAuthProviderInfo] = field(default_factory=list)
    clusters: List[VertxClusterInfo] = field(default_factory=list)
    service_proxies: List[VertxServiceProxyInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    vertx_version: str = ""
    is_reactive: bool = False
    total_verticles: int = 0
    total_routes: int = 0
    total_event_bus: int = 0


class EnhancedVertxParser:
    """
    Enhanced Vert.x parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the Java parser when Vert.x
    framework is detected. It extracts Vert.x-specific semantics
    that the base Java parser cannot capture in full detail.

    Supports Vert.x 2.x through 4.x.
    """

    # Vert.x ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'vertx_core': re.compile(
            r'import\s+io\.vertx\.core\b|'
            r'AbstractVerticle|Vertx\.vertx\(\)|'
            r'io\.vertx\.core\.Vertx',
            re.MULTILINE
        ),
        'vertx_web': re.compile(
            r'import\s+io\.vertx\.ext\.web\b|'
            r'Router\.router\(|RoutingContext|'
            r'BodyHandler|CorsHandler|SessionHandler',
            re.MULTILINE
        ),
        'vertx_web_client': re.compile(
            r'import\s+io\.vertx\.ext\.web\.client\b|'
            r'WebClient\.create\(',
            re.MULTILINE
        ),

        # ── Data ──────────────────────────────────────────────────
        'vertx_pg_client': re.compile(
            r'import\s+io\.vertx\.pgclient\b|PgPool|PgConnectOptions',
            re.MULTILINE
        ),
        'vertx_mysql_client': re.compile(
            r'import\s+io\.vertx\.mysqlclient\b|MySQLPool|MySQLConnectOptions',
            re.MULTILINE
        ),
        'vertx_mssql_client': re.compile(
            r'import\s+io\.vertx\.mssqlclient\b|MSSQLPool',
            re.MULTILINE
        ),
        'vertx_oracle_client': re.compile(
            r'import\s+io\.vertx\.oracleclient\b|OraclePool',
            re.MULTILINE
        ),
        'vertx_mongo_client': re.compile(
            r'import\s+io\.vertx\.ext\.mongo\b|MongoClient\.create',
            re.MULTILINE
        ),
        'vertx_redis_client': re.compile(
            r'import\s+io\.vertx\.redis\b|Redis\.createClient',
            re.MULTILINE
        ),
        'vertx_jdbc_client': re.compile(
            r'import\s+io\.vertx\.ext\.jdbc\b|JDBCPool|JDBCClient',
            re.MULTILINE
        ),
        'vertx_sql_common': re.compile(
            r'import\s+io\.vertx\.sqlclient\b|SqlClient|Row|RowSet|Tuple',
            re.MULTILINE
        ),

        # ── Auth ──────────────────────────────────────────────────
        'vertx_auth_jwt': re.compile(
            r'import\s+io\.vertx\.ext\.auth\.jwt\b|JWTAuth\.\w+',
            re.MULTILINE
        ),
        'vertx_auth_oauth2': re.compile(
            r'import\s+io\.vertx\.ext\.auth\.oauth2\b|OAuth2Auth\.\w+',
            re.MULTILINE
        ),
        'vertx_auth_common': re.compile(
            r'import\s+io\.vertx\.ext\.auth\b|AuthenticationProvider|AuthorizationProvider',
            re.MULTILINE
        ),
        'vertx_auth_htdigest': re.compile(
            r'import\s+io\.vertx\.ext\.auth\.htdigest\b|HtdigestAuth',
            re.MULTILINE
        ),

        # ── Cluster ───────────────────────────────────────────────
        'vertx_hazelcast': re.compile(
            r'import\s+io\.vertx\.spi\.cluster\.hazelcast\b|HazelcastClusterManager',
            re.MULTILINE
        ),
        'vertx_infinispan': re.compile(
            r'import\s+io\.vertx\.ext\.cluster\.infinispan\b|InfinispanClusterManager',
            re.MULTILINE
        ),
        'vertx_ignite': re.compile(
            r'import\s+io\.vertx\.spi\.cluster\.ignite\b|IgniteClusterManager',
            re.MULTILINE
        ),
        'vertx_zookeeper': re.compile(
            r'import\s+io\.vertx\.spi\.cluster\.zookeeper\b|ZookeeperClusterManager',
            re.MULTILINE
        ),

        # ── Messaging ─────────────────────────────────────────────
        'vertx_kafka_client': re.compile(
            r'import\s+io\.vertx\.kafka\b|KafkaConsumer|KafkaProducer',
            re.MULTILINE
        ),
        'vertx_amqp_client': re.compile(
            r'import\s+io\.vertx\.amqp\b|AmqpClient',
            re.MULTILINE
        ),
        'vertx_rabbitmq_client': re.compile(
            r'import\s+io\.vertx\.rabbitmq\b|RabbitMQClient',
            re.MULTILINE
        ),
        'vertx_mqtt': re.compile(
            r'import\s+io\.vertx\.mqtt\b|MqttServer|MqttClient',
            re.MULTILINE
        ),
        'vertx_stomp': re.compile(
            r'import\s+io\.vertx\.ext\.stomp\b|StompServer|StompClient',
            re.MULTILINE
        ),

        # ── gRPC ──────────────────────────────────────────────────
        'vertx_grpc': re.compile(
            r'import\s+io\.vertx\.grpc\b|GrpcServer|VertxServer',
            re.MULTILINE
        ),

        # ── Testing ───────────────────────────────────────────────
        'vertx_junit5': re.compile(
            r'import\s+io\.vertx\.junit5\b|VertxExtension|VertxTestContext',
            re.MULTILINE
        ),
        'vertx_unit': re.compile(
            r'import\s+io\.vertx\.ext\.unit\b|TestContext|TestSuite',
            re.MULTILINE
        ),

        # ── Reactive bindings ─────────────────────────────────────
        'vertx_mutiny': re.compile(
            r'import\s+io\.smallrye\.mutiny\.vertx\b|'
            r'import\s+io\.vertx\.mutiny\b|Uni<|Multi<',
            re.MULTILINE
        ),
        'vertx_rxjava': re.compile(
            r'import\s+io\.vertx\.rxjava3?\b|import\s+io\.vertx\.reactivex\b',
            re.MULTILINE
        ),

        # ── Microservices ─────────────────────────────────────────
        'vertx_circuit_breaker': re.compile(
            r'import\s+io\.vertx\.circuitbreaker\b|CircuitBreaker\.create',
            re.MULTILINE
        ),
        'vertx_service_discovery': re.compile(
            r'import\s+io\.vertx\.servicediscovery\b|ServiceDiscovery\.create',
            re.MULTILINE
        ),
        'vertx_config': re.compile(
            r'import\s+io\.vertx\.config\b|ConfigRetriever\.create',
            re.MULTILINE
        ),
        'vertx_health_check': re.compile(
            r'import\s+io\.vertx\.ext\.healthchecks\b|HealthChecks\.create',
            re.MULTILINE
        ),

        # ── OpenAPI ───────────────────────────────────────────────
        'vertx_web_openapi': re.compile(
            r'import\s+io\.vertx\.ext\.web\.openapi\b|'
            r'RouterBuilder\.create|OpenAPI3RouterFactory',
            re.MULTILINE
        ),
        'vertx_web_api_contract': re.compile(
            r'import\s+io\.vertx\.ext\.web\.api\b|'
            r'OpenAPI3RouterFactory|ValidationHandler',
            re.MULTILINE
        ),

        # ── Service Proxy ─────────────────────────────────────────
        'vertx_service_proxy': re.compile(
            r'import\s+io\.vertx\.serviceproxy\b|@ProxyGen|ServiceBinder',
            re.MULTILINE
        ),

        # ── Template engines ──────────────────────────────────────
        'vertx_web_templ': re.compile(
            r'import\s+io\.vertx\.ext\.web\.templ\b|'
            r'ThymeleafTemplateEngine|HandlebarsTemplateEngine|JadeTemplateEngine|'
            r'FreemarkerTemplateEngine|PebbleTemplateEngine',
            re.MULTILINE
        ),

        # ── Micrometer / Metrics ──────────────────────────────────
        'vertx_micrometer': re.compile(
            r'import\s+io\.vertx\.micrometer\b|MicrometerMetricsOptions',
            re.MULTILINE
        ),
    }

    # Vert.x version detection from import patterns
    VERSION_INDICATORS = {
        '4.x': re.compile(
            r'import\s+io\.vertx\.(?:sqlclient|pgclient|mysqlclient|mssqlclient)\b|'
            r'Future\.succeededFuture|Future\.failedFuture|'
            r'Promise<Void>|\.compose\(|\.onSuccess\(|\.onFailure\('
        ),
        '3.x': re.compile(
            r'import\s+io\.vertx\.ext\.web\.Router\b|'
            r'import\s+io\.vertx\.ext\.asyncsql\b|'
            r'Handler<AsyncResult'
        ),
        '2.x': re.compile(
            r'import\s+org\.vertx\.java\b|'
            r'vertx\.createHttpServer\(\)\.requestHandler'
        ),
    }

    def __init__(self):
        """Initialize the enhanced Vert.x parser with all extractors."""
        self.verticle_extractor = VertxVerticleExtractor()
        self.route_extractor = VertxRouteExtractor()
        self.eventbus_extractor = VertxEventBusExtractor()
        self.data_extractor = VertxDataExtractor()
        self.api_extractor = VertxApiExtractor()

    def is_vertx_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file contains Vert.x code."""
        if not content:
            return False

        vertx_patterns = [
            r'import\s+io\.vertx\.',
            r'AbstractVerticle',
            r'Vertx\.vertx\(\)',
            r'Router\.router\(',
            r'vertx\.eventBus\(\)',
            r'vertx\.createHttpServer\(',
            r'RoutingContext',
            r'io\.vertx\.core',
        ]
        for pattern in vertx_patterns:
            if re.search(pattern, content):
                return True
        return False

    def parse(self, content: str, file_path: str = "") -> VertxParseResult:
        """
        Parse Vert.x source code and extract all Vert.x-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            VertxParseResult with all extracted information
        """
        result = VertxParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version
        result.vertx_version = self._detect_version(content)

        # Check if reactive
        result.is_reactive = any(
            fw in result.detected_frameworks
            for fw in ['vertx_mutiny', 'vertx_rxjava']
        )

        # Run all extractors
        # Verticles
        verticle_result = self.verticle_extractor.extract(content, file_path)
        result.verticles = verticle_result.get('verticles', [])
        result.deployments = verticle_result.get('deployments', [])

        # Routes
        route_result = self.route_extractor.extract(content, file_path)
        result.routes = route_result.get('routes', [])
        result.handlers = route_result.get('handlers', [])
        result.sub_routers = route_result.get('sub_routers', [])

        # Event Bus
        eventbus_result = self.eventbus_extractor.extract(content, file_path)
        result.event_bus_consumers = eventbus_result.get('consumers', [])
        result.event_bus_publishers = eventbus_result.get('publishers', [])
        result.codecs = eventbus_result.get('codecs', [])

        # Data
        data_result = self.data_extractor.extract(content, file_path)
        result.sql_clients = data_result.get('sql_clients', [])
        result.mongo_clients = data_result.get('mongo_clients', [])
        result.redis_clients = data_result.get('redis_clients', [])

        # API
        api_result = self.api_extractor.extract(content, file_path)
        result.websockets = api_result.get('websockets', [])
        result.auth_providers = api_result.get('auth_providers', [])
        result.clusters = api_result.get('clusters', [])
        result.service_proxies = api_result.get('service_proxies', [])

        # Compute totals
        result.total_verticles = len(result.verticles)
        result.total_routes = len(result.routes)
        result.total_event_bus = len(result.event_bus_consumers) + len(result.event_bus_publishers)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Vert.x ecosystem frameworks are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect Vert.x version from code patterns."""
        for version, pattern in self.VERSION_INDICATORS.items():
            if pattern.search(content):
                return version
        return ""
