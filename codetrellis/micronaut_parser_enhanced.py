"""
Enhanced Micronaut Parser v1.0
Part of CodeTrellis v4.94 - Micronaut Framework Support

Extracts Micronaut-specific patterns:
- Compile-time DI (beans, factories, qualifiers, @Requires)
- HTTP controllers, endpoints, filters, declarative clients
- Micronaut Data repositories and entities
- @ConfigurationProperties, @EachProperty
- Feature detection, health indicators, security, scheduled tasks
- Version detection (1.x → 4.x)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any

from codetrellis.extractors.micronaut import (
    MicronautDIExtractor,
    MicronautBeanInfo,
    MicronautFactoryInfo,
    MicronautHTTPExtractor,
    MicronautControllerInfo,
    MicronautEndpointInfo,
    MicronautFilterInfo,
    MicronautClientInfo,
    MicronautDataExtractor,
    MicronautRepositoryInfo,
    MicronautEntityInfo,
    MicronautConfigExtractor,
    MicronautConfigPropsInfo,
    MicronautEachPropertyInfo,
    MicronautFeatureExtractor,
    MicronautFeatureInfo,
    MicronautHealthInfo,
    MicronautSecurityInfo,
)


@dataclass
class MicronautParseResult:
    """Aggregated Micronaut parse result."""
    # DI
    beans: List[Dict] = field(default_factory=list)
    factories: List[Dict] = field(default_factory=list)
    # HTTP
    controllers: List[Dict] = field(default_factory=list)
    endpoints: List[Dict] = field(default_factory=list)
    filters: List[Dict] = field(default_factory=list)
    clients: List[Dict] = field(default_factory=list)
    # Data
    repositories: List[Dict] = field(default_factory=list)
    entities: List[Dict] = field(default_factory=list)
    # Config
    config_properties: List[Dict] = field(default_factory=list)
    each_properties: List[Dict] = field(default_factory=list)
    value_injections: List[Dict] = field(default_factory=list)
    # Features & operational
    features: List[Dict] = field(default_factory=list)
    health_indicators: List[Dict] = field(default_factory=list)
    security: List[Dict] = field(default_factory=list)
    scheduled_tasks: List[Dict] = field(default_factory=list)
    event_listeners: List[Dict] = field(default_factory=list)
    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    micronaut_version: str = ""
    is_reactive: bool = False
    file_path: str = ""
    errors: List[str] = field(default_factory=list)


class EnhancedMicronautParser:
    """Parses Micronaut framework-specific patterns from Java/Kotlin/Groovy source files."""

    FRAMEWORK_PATTERNS: Dict[str, str] = {
        # Core
        'micronaut_core': r'io\.micronaut\.',
        'micronaut_inject': r'io\.micronaut\.context\.|jakarta\.inject\.|javax\.inject\.',
        # HTTP
        'micronaut_http_server': r'io\.micronaut\.http\.(?:annotation|server)\.',
        'micronaut_http_client': r'io\.micronaut\.http\.client\.',
        'micronaut_websocket': r'io\.micronaut\.websocket\.',
        # Data
        'micronaut_data': r'io\.micronaut\.data\.',
        'micronaut_data_jpa': r'io\.micronaut\.data\.(?:jpa|hibernate)\.',
        'micronaut_data_jdbc': r'io\.micronaut\.data\.jdbc\.',
        'micronaut_data_r2dbc': r'io\.micronaut\.data\.r2dbc\.',
        'micronaut_data_mongo': r'io\.micronaut\.data\.mongodb\.',
        # Messaging
        'micronaut_kafka': r'io\.micronaut\.configuration\.kafka\.|io\.micronaut\.kafka\.',
        'micronaut_rabbitmq': r'io\.micronaut\.(?:configuration\.)?rabbitmq\.',
        'micronaut_nats': r'io\.micronaut\.nats\.',
        # Security
        'micronaut_security': r'io\.micronaut\.security\.',
        'micronaut_security_jwt': r'io\.micronaut\.security\.token\.jwt\.',
        'micronaut_security_oauth2': r'io\.micronaut\.security\.oauth2\.',
        # Observability
        'micronaut_management': r'io\.micronaut\.management\.',
        'micronaut_micrometer': r'io\.micronaut\.configuration\.metrics\.|io\.micrometer\.',
        'micronaut_tracing': r'io\.micronaut\.tracing\.',
        # Integration
        'micronaut_grpc': r'io\.micronaut\.grpc\.',
        'micronaut_graphql': r'io\.micronaut\.configuration\.graphql\.',
        'micronaut_cache': r'io\.micronaut\.cache\.',
        # Reactive
        'micronaut_reactor': r'io\.micronaut\.reactor\.|reactor\.core\.',
        'micronaut_rxjava': r'io\.micronaut\.rxjava\d?\.|io\.reactivex\.',
        # Testing
        'micronaut_test': r'io\.micronaut\.test\.|@MicronautTest',
    }

    VERSION_INDICATORS: Dict[str, List[str]] = {
        '4.x': [
            'io.micronaut.serde',
            'io.micronaut.http.annotation',
            'jakarta.inject',
        ],
        '3.x': [
            'io.micronaut.http.annotation',
            'jakarta.inject',
            'io.micronaut.core.annotation',
        ],
        '2.x': [
            'io.micronaut.http.annotation',
            'javax.inject',
        ],
        '1.x': [
            'io.micronaut.http.annotation',
            'javax.inject',
        ],
    }

    def __init__(self) -> None:
        self.di_extractor = MicronautDIExtractor()
        self.http_extractor = MicronautHTTPExtractor()
        self.data_extractor = MicronautDataExtractor()
        self.config_extractor = MicronautConfigExtractor()
        self.feature_extractor = MicronautFeatureExtractor()
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            try:
                self._compiled_patterns[name] = re.compile(pattern)
            except re.error:
                pass

    def is_micronaut_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file is Micronaut-related."""
        if not content:
            return False
        # Build files
        if file_path.endswith(('pom.xml', 'build.gradle', 'build.gradle.kts')):
            return bool(re.search(r'io\.micronaut|micronaut-', content))
        # application.yml / application.properties
        if file_path.endswith(('application.yml', 'application.yaml', 'application.properties')):
            return bool(re.search(r'micronaut\.', content))
        # Source files
        micronaut_indicators = [
            r'import\s+io\.micronaut\.',
            r'@MicronautTest',
            r'@Controller\(',
            r'@Singleton\b',
            r'@Client\(',
            r'@ConfigurationProperties\(',
            r'@EachProperty\(',
            r'HttpServerFilter',
            r'CrudRepository',
        ]
        return any(re.search(p, content) for p in micronaut_indicators)

    def parse(self, content: str, file_path: str = "") -> MicronautParseResult:
        """Parse a file for Micronaut-specific patterns."""
        result = MicronautParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        try:
            result.detected_frameworks = self._detect_frameworks(content)
            result.micronaut_version = self._detect_version(content)
            result.is_reactive = self._detect_reactive(content)

            # DI extraction
            di_result = self.di_extractor.extract(content, file_path)
            result.beans = [vars(b) if hasattr(b, '__dict__') else b for b in di_result.get('beans', [])]
            result.factories = [vars(f) if hasattr(f, '__dict__') else f for f in di_result.get('factories', [])]

            # HTTP extraction
            http_result = self.http_extractor.extract(content, file_path)
            result.controllers = [vars(c) if hasattr(c, '__dict__') else c for c in http_result.get('controllers', [])]
            result.endpoints = [vars(e) if hasattr(e, '__dict__') else e for e in http_result.get('endpoints', [])]
            result.filters = [vars(f) if hasattr(f, '__dict__') else f for f in http_result.get('filters', [])]
            result.clients = [vars(c) if hasattr(c, '__dict__') else c for c in http_result.get('clients', [])]

            # Data extraction
            data_result = self.data_extractor.extract(content, file_path)
            result.repositories = [vars(r) if hasattr(r, '__dict__') else r for r in data_result.get('repositories', [])]
            result.entities = [vars(e) if hasattr(e, '__dict__') else e for e in data_result.get('entities', [])]

            # Config extraction
            config_result = self.config_extractor.extract(content, file_path)
            result.config_properties = [vars(c) if hasattr(c, '__dict__') else c for c in config_result.get('config_properties', [])]
            result.each_properties = [vars(e) if hasattr(e, '__dict__') else e for e in config_result.get('each_properties', [])]
            result.value_injections = config_result.get('value_injections', [])

            # Feature extraction
            feat_result = self.feature_extractor.extract(content, file_path)
            result.features = [vars(f) if hasattr(f, '__dict__') else f for f in feat_result.get('features', [])]
            result.health_indicators = [vars(h) if hasattr(h, '__dict__') else h for h in feat_result.get('health_indicators', [])]
            result.security = [vars(s) if hasattr(s, '__dict__') else s for s in feat_result.get('security', [])]
            result.scheduled_tasks = feat_result.get('scheduled_tasks', [])
            result.event_listeners = feat_result.get('event_listeners', [])

        except Exception as e:
            result.errors.append(f"Parse error: {e}")

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Micronaut-related frameworks are used."""
        detected = []
        for name, pattern in self._compiled_patterns.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """Detect Micronaut version."""
        # Explicit version in build files
        version_match = re.search(
            r'<micronaut\.version>([\d.]+)</micronaut\.version>',
            content
        )
        if version_match:
            return version_match.group(1)

        version_match = re.search(
            r'micronautVersion\s*=\s*["\']?([\d.]+)',
            content
        )
        if version_match:
            return version_match.group(1)

        # Infer from patterns
        if re.search(r'io\.micronaut\.serde\.', content):
            return '4.x'
        if re.search(r'import\s+jakarta\.inject\.', content):
            return '3.x+'
        if re.search(r'import\s+javax\.inject\.', content):
            return '2.x'
        return ''

    def _detect_reactive(self, content: str) -> bool:
        """Detect if the file uses reactive patterns."""
        reactive_indicators = [
            r'\bMono<', r'\bFlux<',
            r'\bPublisher<', r'\bMaybe<', r'\bSingle<',
            r'\bFlowable<', r'\bObservable<',
            r'io\.micronaut\.reactor',
            r'io\.reactivex',
            r'reactor\.core',
        ]
        return any(re.search(p, content) for p in reactive_indicators)
