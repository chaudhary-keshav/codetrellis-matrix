"""
Enhanced Quarkus Parser v1.0
Part of CodeTrellis v4.94 - Quarkus Framework Support

Extracts Quarkus-specific patterns:
- CDI beans, producers, interceptors
- RESTEasy Reactive / JAX-RS endpoints
- Panache entities and repositories (active record + repository pattern)
- MicroProfile Config, ConfigMapping
- Extension detection, native image hints, health checks, metrics
- Version detection (1.x → 3.x+)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from codetrellis.extractors.quarkus import (
    QuarkusCDIExtractor,
    QuarkusCDIBeanInfo,
    QuarkusProducerInfo,
    QuarkusInterceptorInfo,
    QuarkusRESTExtractor,
    QuarkusEndpointInfo,
    QuarkusResourceInfo,
    QuarkusFilterInfo,
    QuarkusPanacheExtractor,
    QuarkusPanacheEntityInfo,
    QuarkusPanacheRepoInfo,
    QuarkusConfigExtractor,
    QuarkusConfigPropertyInfo,
    QuarkusConfigMappingInfo,
    QuarkusExtensionExtractor,
    QuarkusExtensionInfo,
    QuarkusNativeHintInfo,
    QuarkusHealthInfo,
)


@dataclass
class QuarkusParseResult:
    """Aggregated Quarkus parse result."""
    # CDI
    cdi_beans: List[Dict] = field(default_factory=list)
    producers: List[Dict] = field(default_factory=list)
    interceptors: List[Dict] = field(default_factory=list)
    # REST
    endpoints: List[Dict] = field(default_factory=list)
    resources: List[Dict] = field(default_factory=list)
    filters: List[Dict] = field(default_factory=list)
    # Panache
    panache_entities: List[Dict] = field(default_factory=list)
    panache_repositories: List[Dict] = field(default_factory=list)
    # Config
    config_properties: List[Dict] = field(default_factory=list)
    config_mappings: List[Dict] = field(default_factory=list)
    app_properties: List[Dict] = field(default_factory=list)
    # Extensions & operational
    extensions: List[Dict] = field(default_factory=list)
    native_hints: List[Dict] = field(default_factory=list)
    health_checks: List[Dict] = field(default_factory=list)
    metrics: List[Dict] = field(default_factory=list)
    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    quarkus_version: str = ""
    is_reactive: bool = False
    is_native: bool = False
    file_path: str = ""
    errors: List[str] = field(default_factory=list)


class EnhancedQuarkusParser:
    """Parses Quarkus framework-specific patterns from Java source files and build files."""

    FRAMEWORK_PATTERNS: Dict[str, str] = {
        # Core
        'quarkus_core': r'io\.quarkus\.',
        'quarkus_arc': r'jakarta\.enterprise\.|javax\.enterprise\.|io\.quarkus\.arc\.',
        # REST
        'quarkus_resteasy_reactive': r'io\.quarkus\.resteasy\.reactive\.|org\.jboss\.resteasy\.reactive\.',
        'quarkus_resteasy_classic': r'org\.jboss\.resteasy\.',
        'quarkus_jaxrs': r'jakarta\.ws\.rs\.|javax\.ws\.rs\.',
        # Data
        'quarkus_hibernate_panache': r'io\.quarkus\.hibernate\.orm\.panache\.',
        'quarkus_hibernate_reactive_panache': r'io\.quarkus\.hibernate\.reactive\.panache\.',
        'quarkus_mongodb_panache': r'io\.quarkus\.mongodb\.panache\.',
        'quarkus_hibernate_orm': r'io\.quarkus\.hibernate\.orm\.',
        'quarkus_agroal': r'io\.quarkus\.agroal\.',
        # Messaging
        'quarkus_kafka': r'io\.quarkus\.kafka\.|org\.eclipse\.microprofile\.reactive\.messaging\.',
        'quarkus_amqp': r'io\.quarkus\..*amqp\.',
        'quarkus_vertx_eventbus': r'io\.vertx\..*EventBus|io\.quarkus\.vertx\.',
        # Security
        'quarkus_security': r'io\.quarkus\.security\.',
        'quarkus_oidc': r'io\.quarkus\.oidc\.',
        'quarkus_jwt': r'org\.eclipse\.microprofile\.jwt\.',
        # Observability
        'quarkus_health': r'org\.eclipse\.microprofile\.health\.',
        'quarkus_metrics': r'org\.eclipse\.microprofile\.metrics\.|io\.micrometer\.',
        'quarkus_opentelemetry': r'io\.opentelemetry\.',
        'quarkus_openapi': r'org\.eclipse\.microprofile\.openapi\.',
        # Integration
        'quarkus_rest_client': r'org\.eclipse\.microprofile\.rest\.client\.|io\.quarkus\.rest\.client\.',
        'quarkus_grpc': r'io\.quarkus\.grpc\.|io\.grpc\.',
        'quarkus_graphql': r'io\.smallrye\.graphql\.|org\.eclipse\.microprofile\.graphql\.',
        # MicroProfile
        'microprofile_config': r'org\.eclipse\.microprofile\.config\.',
        'microprofile_fault_tolerance': r'org\.eclipse\.microprofile\.faulttolerance\.',
        # Quarkus-specific
        'quarkus_scheduler': r'io\.quarkus\.scheduler\.',
        'quarkus_cache': r'io\.quarkus\.cache\.',
        'quarkus_qute': r'io\.quarkus\.qute\.',
        'quarkus_native': r'@RegisterForReflection|@RegisterForProxy|@NativeImageResource',
        # Testing
        'quarkus_test': r'io\.quarkus\.test\.|@QuarkusTest|@QuarkusIntegrationTest',
    }

    VERSION_INDICATORS: Dict[str, List[str]] = {
        '3.x': [
            'jakarta.enterprise',
            'jakarta.ws.rs',
            'jakarta.inject',
            'jakarta.persistence',
            'io.quarkus.resteasy.reactive',
            'io.smallrye.mutiny',
        ],
        '2.x': [
            'javax.enterprise',
            'javax.ws.rs',
            'javax.inject',
            'javax.persistence',
        ],
        '1.x': [
            'javax.enterprise',
            'io.quarkus.runtime.annotations.RegisterForReflection',
        ],
    }

    def __init__(self) -> None:
        self.cdi_extractor = QuarkusCDIExtractor()
        self.rest_extractor = QuarkusRESTExtractor()
        self.panache_extractor = QuarkusPanacheExtractor()
        self.config_extractor = QuarkusConfigExtractor()
        self.extension_extractor = QuarkusExtensionExtractor()
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            try:
                self._compiled_patterns[name] = re.compile(pattern)
            except re.error:
                pass

    def is_quarkus_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file is Quarkus-related."""
        if not content:
            return False
        # Build files
        if file_path.endswith(('pom.xml', 'build.gradle', 'build.gradle.kts')):
            return bool(re.search(r'io\.quarkus|quarkus-', content))
        # application.properties / application.yml
        if file_path.endswith(('application.properties', 'application.yml', 'application.yaml')):
            return bool(re.search(r'quarkus\.', content))
        # Java source files
        quarkus_indicators = [
            r'import\s+io\.quarkus\.',
            r'import\s+jakarta\.enterprise\.',
            r'import\s+org\.eclipse\.microprofile\.',
            r'import\s+org\.jboss\.resteasy\.',
            r'@QuarkusTest',
            r'@ApplicationScoped',
            r'@RequestScoped',
            r'@Path\(',
            r'@RegisterForReflection',
            r'PanacheEntity',
            r'PanacheRepository',
        ]
        return any(re.search(p, content) for p in quarkus_indicators)

    def parse(self, content: str, file_path: str = "") -> QuarkusParseResult:
        """Parse a file for Quarkus-specific patterns."""
        result = QuarkusParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        try:
            # Detect frameworks and version
            result.detected_frameworks = self._detect_frameworks(content)
            result.quarkus_version = self._detect_version(content)
            result.is_reactive = self._detect_reactive(content)
            result.is_native = bool(re.search(r'@RegisterForReflection|@RegisterForProxy|native-image', content))

            # CDI extraction
            cdi_result = self.cdi_extractor.extract(content, file_path)
            result.cdi_beans = [vars(b) if hasattr(b, '__dict__') else b for b in cdi_result.get('beans', [])]
            result.producers = [vars(p) if hasattr(p, '__dict__') else p for p in cdi_result.get('producers', [])]
            result.interceptors = [vars(i) if hasattr(i, '__dict__') else i for i in cdi_result.get('interceptors', [])]

            # REST extraction
            rest_result = self.rest_extractor.extract(content, file_path)
            result.endpoints = [vars(e) if hasattr(e, '__dict__') else e for e in rest_result.get('endpoints', [])]
            result.resources = [vars(r) if hasattr(r, '__dict__') else r for r in rest_result.get('resources', [])]
            result.filters = [vars(f) if hasattr(f, '__dict__') else f for f in rest_result.get('filters', [])]

            # Panache extraction
            panache_result = self.panache_extractor.extract(content, file_path)
            result.panache_entities = [vars(e) if hasattr(e, '__dict__') else e for e in panache_result.get('entities', [])]
            result.panache_repositories = [vars(r) if hasattr(r, '__dict__') else r for r in panache_result.get('repositories', [])]

            # Config extraction
            config_result = self.config_extractor.extract(content, file_path)
            result.config_properties = [vars(c) if hasattr(c, '__dict__') else c for c in config_result.get('config_properties', [])]
            result.config_mappings = [vars(c) if hasattr(c, '__dict__') else c for c in config_result.get('config_mappings', [])]
            result.app_properties = config_result.get('app_properties', [])

            # Extension extraction (mainly build files)
            ext_result = self.extension_extractor.extract(content, file_path)
            result.extensions = [vars(e) if hasattr(e, '__dict__') else e for e in ext_result.get('extensions', [])]
            result.native_hints = [vars(n) if hasattr(n, '__dict__') else n for n in ext_result.get('native_hints', [])]
            result.health_checks = [vars(h) if hasattr(h, '__dict__') else h for h in ext_result.get('health_checks', [])]
            result.metrics = ext_result.get('metrics', [])

        except Exception as e:
            result.errors.append(f"Parse error: {e}")

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Quarkus-related frameworks are used."""
        detected = []
        for name, pattern in self._compiled_patterns.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """Detect Quarkus version from imports and patterns."""
        # Check for explicit version in build files
        version_match = re.search(
            r'<quarkus\.platform\.version>([\d.]+(?:\.Final)?)</quarkus\.platform\.version>',
            content
        )
        if version_match:
            return version_match.group(1)

        version_match = re.search(
            r'quarkusPlatformVersion\s*=\s*["\']?([\d.]+(?:\.Final)?)',
            content
        )
        if version_match:
            return version_match.group(1)

        # Infer from namespace
        if re.search(r'import\s+jakarta\.', content):
            return '3.x'
        if re.search(r'import\s+javax\.enterprise\.|import\s+javax\.ws\.rs\.', content):
            return '2.x'
        return ''

    def _detect_reactive(self, content: str) -> bool:
        """Detect if the file uses reactive patterns."""
        reactive_indicators = [
            r'\bUni<', r'\bMulti<',
            r'io\.smallrye\.mutiny',
            r'ReactivePanache',
            r'io\.quarkus\.hibernate\.reactive',
            r'io\.vertx\.mutiny',
            r'io\.quarkus\.resteasy\.reactive',
        ]
        return any(re.search(p, content) for p in reactive_indicators)
