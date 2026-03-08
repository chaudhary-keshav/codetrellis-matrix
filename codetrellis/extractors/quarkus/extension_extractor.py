"""
Quarkus Extension Extractor v1.0 - Extension detection, native build hints, health, metrics.
Part of CodeTrellis v4.94 - Quarkus Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class QuarkusExtensionInfo:
    """A detected Quarkus extension."""
    name: str
    group_id: str = ""
    artifact_id: str = ""
    category: str = ""  # core, web, data, messaging, security, observability, integration
    file: str = ""


@dataclass
class QuarkusNativeHintInfo:
    """A native image build hint."""
    name: str
    hint_type: str = ""  # register_for_reflection, register_for_proxy, native_image_resource
    classes: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class QuarkusHealthInfo:
    """A health check endpoint."""
    name: str
    health_type: str = ""  # liveness, readiness, startup
    file: str = ""
    line_number: int = 0


class QuarkusExtensionExtractor:
    """Extracts Quarkus extension, native, health, and metric patterns."""

    EXTENSION_MAP = {
        'quarkus-resteasy-reactive': ('web', 'RESTEasy Reactive'),
        'quarkus-resteasy': ('web', 'RESTEasy Classic'),
        'quarkus-rest': ('web', 'Quarkus REST'),
        'quarkus-hibernate-orm-panache': ('data', 'Hibernate ORM Panache'),
        'quarkus-hibernate-reactive-panache': ('data', 'Hibernate Reactive Panache'),
        'quarkus-mongodb-panache': ('data', 'MongoDB Panache'),
        'quarkus-hibernate-orm': ('data', 'Hibernate ORM'),
        'quarkus-agroal': ('data', 'Agroal DataSource'),
        'quarkus-jdbc-postgresql': ('data', 'PostgreSQL JDBC'),
        'quarkus-jdbc-mysql': ('data', 'MySQL JDBC'),
        'quarkus-jdbc-h2': ('data', 'H2 JDBC'),
        'quarkus-reactive-pg-client': ('data', 'Reactive PostgreSQL'),
        'quarkus-reactive-mysql-client': ('data', 'Reactive MySQL'),
        'quarkus-kafka': ('messaging', 'Kafka'),
        'quarkus-smallrye-reactive-messaging-kafka': ('messaging', 'SmallRye Reactive Messaging Kafka'),
        'quarkus-smallrye-reactive-messaging-amqp': ('messaging', 'SmallRye AMQP'),
        'quarkus-artemis-jms': ('messaging', 'Artemis JMS'),
        'quarkus-security': ('security', 'Security'),
        'quarkus-oidc': ('security', 'OIDC'),
        'quarkus-keycloak-authorization': ('security', 'Keycloak Authorization'),
        'quarkus-smallrye-jwt': ('security', 'SmallRye JWT'),
        'quarkus-smallrye-health': ('observability', 'SmallRye Health'),
        'quarkus-micrometer': ('observability', 'Micrometer'),
        'quarkus-opentelemetry': ('observability', 'OpenTelemetry'),
        'quarkus-smallrye-openapi': ('observability', 'SmallRye OpenAPI'),
        'quarkus-smallrye-fault-tolerance': ('core', 'SmallRye Fault Tolerance'),
        'quarkus-rest-client-reactive': ('integration', 'REST Client Reactive'),
        'quarkus-grpc': ('integration', 'gRPC'),
        'quarkus-scheduler': ('core', 'Scheduler'),
        'quarkus-cache': ('core', 'Cache'),
        'quarkus-qute': ('web', 'Qute Templating'),
        'quarkus-arc': ('core', 'ArC CDI'),
        'quarkus-vertx': ('core', 'Vert.x'),
    }

    REFLECTION_PATTERN = re.compile(
        r'@RegisterForReflection(?:\(\s*(?:targets\s*=\s*\{([^}]+)\})?\s*\))?\s*\n'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    PROXY_PATTERN = re.compile(
        r'@RegisterForProxy\s*\n(?:public\s+)?(?:interface|class)\s+(\w+)',
        re.MULTILINE
    )

    NATIVE_RESOURCE_PATTERN = re.compile(
        r'@NativeImageResource\("([^"]+)"\)',
        re.MULTILINE
    )

    HEALTH_PATTERNS = {
        'liveness': re.compile(r'@Liveness\s*\n(?:public\s+)?class\s+(\w+)', re.MULTILINE),
        'readiness': re.compile(r'@Readiness\s*\n(?:public\s+)?class\s+(\w+)', re.MULTILINE),
        'startup': re.compile(r'@Startup\s*\n.*?@Health\s*\n(?:public\s+)?class\s+(\w+)', re.MULTILINE | re.DOTALL),
    }

    HEALTH_CHECK_IMPL = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+HealthCheck',
        re.MULTILINE
    )

    METRIC_PATTERNS = {
        'timed': re.compile(r'@Timed\(\s*(?:value\s*=\s*)?"([^"]*)"', re.MULTILINE),
        'counted': re.compile(r'@Counted\(\s*(?:value\s*=\s*)?"([^"]*)"', re.MULTILINE),
        'gauge': re.compile(r'@Gauge\(\s*(?:value\s*=\s*)?"([^"]*)"', re.MULTILINE),
    }

    DEPENDENCY_PATTERN = re.compile(
        r'<artifactId>(quarkus-[\w-]+)</artifactId>',
        re.MULTILINE
    )

    GRADLE_DEPENDENCY_PATTERN = re.compile(
        r"implementation\s*['\"]io\.quarkus:(quarkus-[\w-]+)",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {
            'extensions': [], 'native_hints': [],
            'health_checks': [], 'metrics': [],
        }
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract extensions from build files
        if file_path.endswith('pom.xml') or file_path.endswith('build.gradle') or file_path.endswith('build.gradle.kts'):
            dep_pattern = self.DEPENDENCY_PATTERN if 'pom.xml' in file_path else self.GRADLE_DEPENDENCY_PATTERN
            for match in dep_pattern.finditer(content):
                artifact_id = match.group(1)
                ext_info = self.EXTENSION_MAP.get(artifact_id)
                if ext_info:
                    category, display_name = ext_info
                    result['extensions'].append(QuarkusExtensionInfo(
                        name=display_name,
                        group_id='io.quarkus',
                        artifact_id=artifact_id,
                        category=category,
                        file=file_path,
                    ))

        # Extract native image hints
        for match in self.REFLECTION_PATTERN.finditer(content):
            targets = []
            if match.group(1):
                targets = [t.strip().rstrip('.class') for t in match.group(1).split(',')]
            class_name = match.group(2)
            result['native_hints'].append(QuarkusNativeHintInfo(
                name=class_name, hint_type='register_for_reflection',
                classes=targets or [class_name],
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.PROXY_PATTERN.finditer(content):
            result['native_hints'].append(QuarkusNativeHintInfo(
                name=match.group(1), hint_type='register_for_proxy',
                classes=[match.group(1)],
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.NATIVE_RESOURCE_PATTERN.finditer(content):
            result['native_hints'].append(QuarkusNativeHintInfo(
                name=match.group(1), hint_type='native_image_resource',
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract health checks
        for health_type, pattern in self.HEALTH_PATTERNS.items():
            for match in pattern.finditer(content):
                result['health_checks'].append(QuarkusHealthInfo(
                    name=match.group(1), health_type=health_type,
                    file=file_path, line_number=content[:match.start()].count('\n') + 1,
                ))

        for match in self.HEALTH_CHECK_IMPL.finditer(content):
            # Check if it already has a specific health type annotation
            pre_class = content[max(0, match.start()-200):match.start()]
            if not re.search(r'@(Liveness|Readiness)', pre_class):
                result['health_checks'].append(QuarkusHealthInfo(
                    name=match.group(1), health_type='unknown',
                    file=file_path, line_number=content[:match.start()].count('\n') + 1,
                ))

        # Extract metrics annotations
        for metric_type, pattern in self.METRIC_PATTERNS.items():
            for match in pattern.finditer(content):
                result['metrics'].append({
                    'type': metric_type,
                    'name': match.group(1),
                    'file': file_path,
                    'line_number': content[:match.start()].count('\n') + 1,
                })

        return result
