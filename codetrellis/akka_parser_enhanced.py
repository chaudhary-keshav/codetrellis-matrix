"""
Enhanced Akka Parser for CodeTrellis.

Provides comprehensive parsing of Akka toolkit files including:
- Akka Classic actors (AbstractActor, UntypedAbstractActor)
- Akka Typed actors (AbstractBehavior, Behavior factories)
- Akka Streams (Source, Flow, Sink, Graph DSL)
- Akka HTTP (routes, directives, marshalling)
- Akka Cluster (sharding, singleton, pub/sub, CRDTs)
- Akka Persistence (EventSourcedBehavior, DurableStateBehavior, projections)
- Version detection: Classic (2.x), Typed (2.6+), Pekko (1.x)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set

from .extractors.akka import (
    AkkaActorExtractor,
    AkkaStreamExtractor,
    AkkaHttpExtractor,
    AkkaClusterExtractor,
    AkkaPersistenceExtractor,
)


@dataclass
class AkkaParseResult:
    """Result of parsing an Akka file."""
    # Actors
    actors: List[Dict[str, Any]] = field(default_factory=list)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    supervision: List[Dict[str, Any]] = field(default_factory=list)

    # Streams
    stream_stages: List[Dict[str, Any]] = field(default_factory=list)
    stream_graphs: List[Dict[str, Any]] = field(default_factory=list)
    stream_operators: List[str] = field(default_factory=list)

    # HTTP
    http_routes: List[Dict[str, Any]] = field(default_factory=list)
    http_directives: List[Dict[str, Any]] = field(default_factory=list)

    # Cluster
    cluster_sharding: List[Dict[str, Any]] = field(default_factory=list)
    cluster_singletons: List[Dict[str, Any]] = field(default_factory=list)
    cluster_pubsub: List[Dict[str, Any]] = field(default_factory=list)

    # Persistence
    persistence_actors: List[Dict[str, Any]] = field(default_factory=list)
    snapshots: List[Dict[str, Any]] = field(default_factory=list)
    projections: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    frameworks: List[str] = field(default_factory=list)
    version: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedAkkaParser:
    """Enhanced parser for Akka toolkit files."""

    # ── Framework detection patterns ──
    FRAMEWORK_PATTERNS = {
        # Akka Core
        'akka-actor': re.compile(r'import\s+akka\.actor\b'),
        'akka-actor-typed': re.compile(r'import\s+akka\.actor\.typed\b'),

        # Akka Streams
        'akka-stream': re.compile(r'import\s+akka\.stream\b'),
        'akka-stream-typed': re.compile(r'import\s+akka\.stream\.typed\b'),

        # Akka HTTP
        'akka-http': re.compile(r'import\s+akka\.http\b'),
        'akka-http-spray-json': re.compile(r'import\s+akka\.http\.scaladsl\.marshallers\.sprayjson\b'),
        'akka-http-jackson': re.compile(r'import\s+akka\.http\.javadsl\.marshallers\.jackson\b'),
        'akka-http-xml': re.compile(r'import\s+akka\.http\.scaladsl\.marshallers\.xml\b'),

        # Akka Cluster
        'akka-cluster': re.compile(r'import\s+akka\.cluster\b'),
        'akka-cluster-typed': re.compile(r'import\s+akka\.cluster\.typed\b'),
        'akka-cluster-sharding': re.compile(r'import\s+akka\.cluster\.sharding\b'),
        'akka-cluster-singleton': re.compile(r'import\s+akka\.cluster\.singleton\b'),
        'akka-cluster-tools': re.compile(r'import\s+akka\.cluster\.(?:pubsub|client)\b'),
        'akka-distributed-data': re.compile(r'import\s+akka\.cluster\.ddata\b'),

        # Akka Persistence
        'akka-persistence': re.compile(r'import\s+akka\.persistence\b'),
        'akka-persistence-typed': re.compile(r'import\s+akka\.persistence\.typed\b'),
        'akka-persistence-query': re.compile(r'import\s+akka\.persistence\.query\b'),
        'akka-persistence-cassandra': re.compile(r'akka-persistence-cassandra|CassandraReadJournal'),
        'akka-persistence-jdbc': re.compile(r'akka-persistence-jdbc|JdbcReadJournal'),
        'akka-persistence-r2dbc': re.compile(r'akka-persistence-r2dbc|R2dbcReadJournal'),

        # Akka Projections
        'akka-projection': re.compile(r'import\s+akka\.projection\b'),
        'akka-projection-r2dbc': re.compile(r'R2dbcProjection\b'),
        'akka-projection-jdbc': re.compile(r'JdbcProjection\b'),
        'akka-projection-cassandra': re.compile(r'CassandraProjection\b'),
        'akka-projection-kafka': re.compile(r'KafkaProjection\b'),
        'akka-projection-slick': re.compile(r'SlickProjection\b'),

        # Akka gRPC
        'akka-grpc': re.compile(r'import\s+akka\.grpc\b|AkkaGrpcPlugin'),

        # Akka Management
        'akka-management': re.compile(r'import\s+akka\.management\b|AkkaManagement'),
        'akka-discovery': re.compile(r'import\s+akka\.discovery\b|ServiceDiscovery'),

        # Akka Remote
        'akka-remote': re.compile(r'import\s+akka\.remote\b|akka\.remote\.artery'),

        # Akka Coordination (Lease)
        'akka-coordination': re.compile(r'import\s+akka\.coordination\b|Lease\b'),

        # Alpakka (Akka Streams connectors)
        'alpakka': re.compile(r'import\s+akka\.stream\.alpakka\b'),
        'alpakka-kafka': re.compile(r'import\s+akka\.kafka\b|ConsumerSettings|ProducerSettings'),
        'alpakka-cassandra': re.compile(r'CassandraSource|CassandraFlow|CassandraSession'),
        'alpakka-s3': re.compile(r'S3\.\s*(?:download|upload|multipartUpload)'),
        'alpakka-slick': re.compile(r'Slick\.\s*(?:source|flow|sink)'),

        # Testing
        'akka-testkit': re.compile(r'import\s+akka\.testkit\b|TestKit|TestProbe'),
        'akka-testkit-typed': re.compile(r'import\s+akka\.actor\.testkit\.typed\b|BehaviorTestKit|ActorTestKit'),
        'akka-stream-testkit': re.compile(r'import\s+akka\.stream\.testkit\b|TestSource|TestSink'),
        'akka-http-testkit': re.compile(r'import\s+akka\.http\.scaladsl\.testkit\b|RouteTest|ScalatestRouteTest'),
        'akka-persistence-testkit': re.compile(r'PersistenceTestKit|EventSourcedBehaviorTestKit'),
        'akka-multi-node-testkit': re.compile(r'MultiNodeSpec|MultiNodeConfig'),

        # Akka Serialization
        'akka-serialization-jackson': re.compile(r'akka-serialization-jackson|JacksonJsonSerializer|JacksonCborSerializer'),

        # Apache Pekko (Akka fork)
        'pekko': re.compile(r'import\s+org\.apache\.pekko\b'),
        'pekko-actor': re.compile(r'import\s+org\.apache\.pekko\.actor\b'),
        'pekko-stream': re.compile(r'import\s+org\.apache\.pekko\.stream\b'),
        'pekko-http': re.compile(r'import\s+org\.apache\.pekko\.http\b'),
        'pekko-cluster': re.compile(r'import\s+org\.apache\.pekko\.cluster\b'),
        'pekko-persistence': re.compile(r'import\s+org\.apache\.pekko\.persistence\b'),
    }

    # ── Version indicators ──
    VERSION_INDICATORS = {
        # Pekko (fork of Akka, Apache project)
        '1.x (Pekko)': [
            re.compile(r'org\.apache\.pekko'),
        ],
        # Akka 2.9+ (licensed BSL)
        '2.9.x': [
            re.compile(r'akka[-.](?:actor|stream|http).*2\.9\.\d+'),
            re.compile(r'"com\.typesafe\.akka"\s*%+\s*"akka-.*"\s*%\s*"2\.9'),
        ],
        # Akka 2.8.x
        '2.8.x': [
            re.compile(r'akka[-.](?:actor|stream|http).*2\.8\.\d+'),
            re.compile(r'"com\.typesafe\.akka"\s*%+\s*"akka-.*"\s*%\s*"2\.8'),
        ],
        # Akka 2.7.x
        '2.7.x': [
            re.compile(r'akka[-.](?:actor|stream|http).*2\.7\.\d+'),
            re.compile(r'"com\.typesafe\.akka"\s*%+\s*"akka-.*"\s*%\s*"2\.7'),
        ],
        # Akka 2.6.x (Typed stable)
        '2.6.x': [
            re.compile(r'akka[-.](?:actor|stream|http).*2\.6\.\d+'),
            re.compile(r'"com\.typesafe\.akka"\s*%+\s*"akka-.*"\s*%\s*"2\.6'),
        ],
        # Akka 2.5.x
        '2.5.x': [
            re.compile(r'akka[-.](?:actor|stream|http).*2\.5\.\d+'),
            re.compile(r'"com\.typesafe\.akka"\s*%+\s*"akka-.*"\s*%\s*"2\.5'),
        ],
        # Akka 2.4.x
        '2.4.x': [
            re.compile(r'akka[-.](?:actor|stream|http).*2\.4\.\d+'),
            re.compile(r'"com\.typesafe\.akka"\s*%+\s*"akka-.*"\s*%\s*"2\.4'),
        ],
    }

    def __init__(self):
        """Initialize extractors."""
        self.actor_extractor = AkkaActorExtractor()
        self.stream_extractor = AkkaStreamExtractor()
        self.http_extractor = AkkaHttpExtractor()
        self.cluster_extractor = AkkaClusterExtractor()
        self.persistence_extractor = AkkaPersistenceExtractor()

    def is_akka_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file is an Akka file."""
        if not content:
            return False

        # Check for Akka / Pekko imports
        akka_import = re.search(
            r'import\s+(?:akka|org\.apache\.pekko)\.',
            content,
        )
        if akka_import:
            return True

        # Check for Akka class usage
        akka_usage = re.search(
            r'(?:ActorSystem|ActorRef|Behavior|Props|'
            r'Source|Flow|Sink|Route|'
            r'ClusterSharding|EventSourcedBehavior|'
            r'AbstractActor|AbstractBehavior)\b',
            content,
        )
        if akka_usage:
            return True

        # Check build files for Akka dependencies
        if file_path and ('build.sbt' in file_path or 'build.gradle' in file_path or 'pom.xml' in file_path):
            return bool(re.search(r'akka[-.]|pekko[-.]', content))

        return False

    def parse(self, content: str, file_path: str = "") -> AkkaParseResult:
        """Parse an Akka file and return structured results."""
        result = AkkaParseResult()

        if not content or not content.strip():
            return result

        # Detect frameworks and version
        result.frameworks = self._detect_frameworks(content)
        result.version = self._detect_version(content)

        # Run all extractors
        try:
            actor_data = self.actor_extractor.extract(content, file_path)
            result.actors = [vars(a) if hasattr(a, '__dict__') else a for a in actor_data.get('actors', [])]
            result.messages = [vars(m) if hasattr(m, '__dict__') else m for m in actor_data.get('messages', [])]
            result.supervision = [vars(s) if hasattr(s, '__dict__') else s for s in actor_data.get('supervision', [])]
        except Exception:
            pass

        try:
            stream_data = self.stream_extractor.extract(content, file_path)
            result.stream_stages = [vars(s) if hasattr(s, '__dict__') else s for s in stream_data.get('stages', [])]
            result.stream_graphs = [vars(g) if hasattr(g, '__dict__') else g for g in stream_data.get('graphs', [])]
            result.stream_operators = stream_data.get('operators', [])
        except Exception:
            pass

        try:
            http_data = self.http_extractor.extract(content, file_path)
            result.http_routes = [vars(r) if hasattr(r, '__dict__') else r for r in http_data.get('routes', [])]
            result.http_directives = [vars(d) if hasattr(d, '__dict__') else d for d in http_data.get('directives', [])]
            result.metadata['http'] = http_data.get('metadata', {})
        except Exception:
            pass

        try:
            cluster_data = self.cluster_extractor.extract(content, file_path)
            result.cluster_sharding = [vars(s) if hasattr(s, '__dict__') else s for s in cluster_data.get('sharding', [])]
            result.cluster_singletons = [vars(s) if hasattr(s, '__dict__') else s for s in cluster_data.get('singletons', [])]
            result.cluster_pubsub = [vars(p) if hasattr(p, '__dict__') else p for p in cluster_data.get('pubsub', [])]
            result.metadata['cluster'] = cluster_data.get('metadata', {})
        except Exception:
            pass

        try:
            persistence_data = self.persistence_extractor.extract(content, file_path)
            result.persistence_actors = [vars(a) if hasattr(a, '__dict__') else a for a in persistence_data.get('actors', [])]
            result.snapshots = [vars(s) if hasattr(s, '__dict__') else s for s in persistence_data.get('snapshots', [])]
            result.projections = [vars(p) if hasattr(p, '__dict__') else p for p in persistence_data.get('projections', [])]
            result.metadata['persistence'] = persistence_data.get('metadata', {})
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Akka frameworks/modules are used."""
        detected: List[str] = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return sorted(detected)

    def _detect_version(self, content: str) -> str:
        """Detect Akka version from content (newest to oldest)."""
        for version, patterns in self.VERSION_INDICATORS.items():
            for pattern in patterns:
                if pattern.search(content):
                    return version
        return ""
