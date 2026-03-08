"""
Micronaut Feature Extractor v1.0 - Feature detection, health, security, scheduled tasks.
Part of CodeTrellis v4.94 - Micronaut Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class MicronautFeatureInfo:
    """A detected Micronaut feature."""
    name: str
    group_id: str = ""
    artifact_id: str = ""
    category: str = ""  # core, web, data, messaging, security, observability, integration
    file: str = ""


@dataclass
class MicronautHealthInfo:
    """A health indicator."""
    name: str
    health_type: str = ""  # liveness, readiness, custom
    file: str = ""
    line_number: int = 0


@dataclass
class MicronautSecurityInfo:
    """A security configuration."""
    name: str
    security_type: str = ""  # authentication, authorization, oauth2, jwt, basic
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class MicronautFeatureExtractor:
    """Extracts Micronaut feature, health, security, and scheduling patterns."""

    FEATURE_MAP = {
        'micronaut-http-server-netty': ('web', 'HTTP Server Netty'),
        'micronaut-http-client': ('web', 'HTTP Client'),
        'micronaut-data-hibernate-jpa': ('data', 'Data Hibernate JPA'),
        'micronaut-data-jdbc': ('data', 'Data JDBC'),
        'micronaut-data-r2dbc': ('data', 'Data R2DBC'),
        'micronaut-data-mongodb': ('data', 'Data MongoDB'),
        'micronaut-jdbc-hikari': ('data', 'JDBC HikariCP'),
        'micronaut-flyway': ('data', 'Flyway Migrations'),
        'micronaut-liquibase': ('data', 'Liquibase Migrations'),
        'micronaut-kafka': ('messaging', 'Kafka'),
        'micronaut-rabbitmq': ('messaging', 'RabbitMQ'),
        'micronaut-nats': ('messaging', 'NATS'),
        'micronaut-jms': ('messaging', 'JMS'),
        'micronaut-security': ('security', 'Security'),
        'micronaut-security-jwt': ('security', 'Security JWT'),
        'micronaut-security-oauth2': ('security', 'Security OAuth2'),
        'micronaut-management': ('observability', 'Management'),
        'micronaut-micrometer-core': ('observability', 'Micrometer'),
        'micronaut-tracing': ('observability', 'Distributed Tracing'),
        'micronaut-openapi': ('observability', 'OpenAPI'),
        'micronaut-grpc': ('integration', 'gRPC'),
        'micronaut-graphql': ('integration', 'GraphQL'),
        'micronaut-cache': ('core', 'Cache'),
        'micronaut-reactor': ('core', 'Project Reactor'),
        'micronaut-rxjava3': ('core', 'RxJava 3'),
        'micronaut-views': ('web', 'Server-Side Views'),
        'micronaut-websocket': ('web', 'WebSocket'),
        'micronaut-discovery-client': ('integration', 'Service Discovery'),
        'micronaut-test': ('core', 'Testing'),
    }

    HEALTH_INDICATOR_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+HealthIndicator',
        re.MULTILINE
    )

    LIVENESS_PATTERN = re.compile(
        r'@Liveness\s*\n(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    READINESS_PATTERN = re.compile(
        r'@Readiness\s*\n(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    SECURED_PATTERN = re.compile(
        r'@Secured\(\s*(?:SecurityRule\.)?"?([^")]+)"?\s*\)',
        re.MULTILINE
    )

    SECURITY_RULE_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+(?:SecurityRule|AuthenticationProvider|TokenValidator)',
        re.MULTILINE
    )

    LOGIN_HANDLER_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+(?:LoginHandler|LogoutHandler|AuthenticationFetcher)',
        re.MULTILINE
    )

    SCHEDULED_PATTERN = re.compile(
        r'@Scheduled\(\s*(?:fixedRate|fixedDelay|cron|initialDelay)\s*=\s*"([^"]*)"',
        re.MULTILINE
    )

    EVENT_LISTENER_PATTERN = re.compile(
        r'@EventListener\s*\n\s*(?:public\s+)?void\s+(\w+)',
        re.MULTILINE
    )

    DEPENDENCY_PATTERN = re.compile(
        r'<artifactId>(micronaut-[\w-]+)</artifactId>',
        re.MULTILINE
    )

    GRADLE_DEPENDENCY_PATTERN = re.compile(
        r'(?:implementation|annotationProcessor|runtimeOnly|testImplementation)\s*\(?\s*["\']io\.micronaut(?:\.\w+)*:(micronaut-[\w-]+)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {
            'features': [], 'health_indicators': [],
            'security': [], 'scheduled_tasks': [], 'event_listeners': [],
        }
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract features from build files
        if file_path.endswith(('pom.xml', 'build.gradle', 'build.gradle.kts')):
            dep_pattern = self.DEPENDENCY_PATTERN if 'pom.xml' in file_path else self.GRADLE_DEPENDENCY_PATTERN
            for match in dep_pattern.finditer(content):
                artifact_id = match.group(1)
                feature_info = self.FEATURE_MAP.get(artifact_id)
                if feature_info:
                    category, display_name = feature_info
                    result['features'].append(MicronautFeatureInfo(
                        name=display_name,
                        group_id='io.micronaut',
                        artifact_id=artifact_id,
                        category=category,
                        file=file_path,
                    ))

        # Health indicators
        for match in self.HEALTH_INDICATOR_PATTERN.finditer(content):
            result['health_indicators'].append(MicronautHealthInfo(
                name=match.group(1), health_type='custom',
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.LIVENESS_PATTERN.finditer(content):
            result['health_indicators'].append(MicronautHealthInfo(
                name=match.group(1), health_type='liveness',
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.READINESS_PATTERN.finditer(content):
            result['health_indicators'].append(MicronautHealthInfo(
                name=match.group(1), health_type='readiness',
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Security
        for match in self.SECURED_PATTERN.finditer(content):
            result['security'].append(MicronautSecurityInfo(
                name=match.group(1).strip(), security_type='secured',
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.SECURITY_RULE_PATTERN.finditer(content):
            result['security'].append(MicronautSecurityInfo(
                name=match.group(1), security_type='authorization',
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.LOGIN_HANDLER_PATTERN.finditer(content):
            result['security'].append(MicronautSecurityInfo(
                name=match.group(1), security_type='authentication',
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Scheduled tasks
        for match in self.SCHEDULED_PATTERN.finditer(content):
            result['scheduled_tasks'].append({
                'schedule': match.group(1),
                'file': file_path,
                'line_number': content[:match.start()].count('\n') + 1,
            })

        # Event listeners
        for match in self.EVENT_LISTENER_PATTERN.finditer(content):
            result['event_listeners'].append({
                'method': match.group(1),
                'file': file_path,
                'line_number': content[:match.start()].count('\n') + 1,
            })

        return result
