"""
EnhancedApacheCamelParser v1.0 - Comprehensive Apache Camel parser.

Supports:
- Camel 2.x (classic Java DSL, Spring XML)
- Camel 3.x (modularized, endpoint DSL, Kamelet, Quarkus integration)
- Camel 4.x (Java 17+, Jakarta namespace, camel-jbang)

Apache Camel-specific extraction:
- Routes: RouteBuilder, from/to endpoints, route IDs
- Components: 300+ components (messaging, file, HTTP, database, cloud)
- Processors: Processor classes, beans, 50+ EIP patterns
- Error handling: Dead letter channel, exception clauses, retry policies
- REST DSL: REST definitions, OpenAPI integration

Framework detection (30+ Camel ecosystem patterns):
- Core: camel-core, camel-spring-boot, camel-quarkus
- Components: camel-kafka, camel-http, camel-jms, camel-file, etc.
- EIP: split, aggregate, filter, multicast, recipientList, saga
- Cloud: camel-aws, camel-azure, camel-google
- Testing: camel-test, camel-test-junit5

Part of CodeTrellis v4.95 - Apache Camel Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .extractors.apache_camel import (
    CamelRouteExtractor, CamelRouteInfo, CamelEndpointInfo,
    CamelComponentExtractor, CamelComponentInfo, CamelDataFormatInfo,
    CamelProcessorExtractor, CamelProcessorInfo, CamelEIPInfo,
    CamelErrorHandlerExtractor, CamelErrorHandlerInfo, CamelExceptionClauseInfo,
    CamelRestDSLExtractor, CamelRestInfo, CamelRestOperationInfo,
)


@dataclass
class ApacheCamelParseResult:
    """Complete parse result for an Apache Camel file."""
    file_path: str
    file_type: str = "apache_camel"

    # Routes
    routes: List[CamelRouteInfo] = field(default_factory=list)
    endpoints: List[CamelEndpointInfo] = field(default_factory=list)
    route_builder_classes: List[str] = field(default_factory=list)

    # Components
    components: List[CamelComponentInfo] = field(default_factory=list)
    data_formats: List[CamelDataFormatInfo] = field(default_factory=list)
    has_type_converters: bool = False

    # Processors / EIP
    processors: List[CamelProcessorInfo] = field(default_factory=list)
    eip_patterns: List[CamelEIPInfo] = field(default_factory=list)

    # Error handling
    error_handlers: List[CamelErrorHandlerInfo] = field(default_factory=list)
    exception_clauses: List[CamelExceptionClauseInfo] = field(default_factory=list)
    has_on_completion: bool = False

    # REST DSL
    rest_definitions: List[CamelRestInfo] = field(default_factory=list)
    rest_operations: List[CamelRestOperationInfo] = field(default_factory=list)
    has_openapi: bool = False
    rest_config: Dict[str, str] = field(default_factory=dict)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    camel_version: str = ""
    total_routes: int = 0
    total_endpoints: int = 0
    total_eip_patterns: int = 0


class EnhancedApacheCamelParser:
    """
    Enhanced Apache Camel parser using all extractors.

    Runs AFTER the Java parser when Camel framework is detected.
    Extracts integration patterns, routes, and EIPs.

    Supports Camel 2.x through 4.x.
    """

    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'camel_core': re.compile(
            r'import\s+org\.apache\.camel\b|'
            r'RouteBuilder|CamelContext|ProducerTemplate|'
            r'Exchange\s+\w+|from\s*\(\s*["\']',
            re.MULTILINE
        ),
        'camel_spring_boot': re.compile(
            r'camel\.springboot\b|@CamelConfiguration|'
            r'CamelSpringBootApplicationRunner',
            re.MULTILINE
        ),
        'camel_quarkus': re.compile(
            r'camel\.quarkus\b|@ApplicationScoped\s+.*RouteBuilder',
            re.MULTILINE
        ),
        'camel_spring_xml': re.compile(
            r'<camelContext|xmlns.*camel\.apache\.org|'
            r'<route\s+id|<from\s+uri',
            re.MULTILINE
        ),

        # ── Messaging ─────────────────────────────────────────────
        'camel_kafka': re.compile(
            r'camel-kafka|from\s*\(\s*["\']kafka:|\.to\s*\(\s*["\']kafka:',
            re.MULTILINE
        ),
        'camel_jms': re.compile(
            r'camel-jms|from\s*\(\s*["\']jms:|\.to\s*\(\s*["\']jms:',
            re.MULTILINE
        ),
        'camel_activemq': re.compile(
            r'camel-activemq|from\s*\(\s*["\']activemq:|\.to\s*\(\s*["\']activemq:',
            re.MULTILINE
        ),
        'camel_rabbitmq': re.compile(
            r'camel-rabbitmq|from\s*\(\s*["\']rabbitmq:',
            re.MULTILINE
        ),
        'camel_amqp': re.compile(
            r'camel-amqp|from\s*\(\s*["\']amqp:',
            re.MULTILINE
        ),

        # ── HTTP ──────────────────────────────────────────────────
        'camel_http': re.compile(
            r'camel-http|\.to\s*\(\s*["\']https?:',
            re.MULTILINE
        ),
        'camel_rest': re.compile(
            r'camel-rest|rest\s*\(\s*["\']|restConfiguration\s*\(\s*\)',
            re.MULTILINE
        ),
        'camel_servlet': re.compile(
            r'camel-servlet|from\s*\(\s*["\']servlet:',
            re.MULTILINE
        ),
        'camel_platform_http': re.compile(
            r'camel-platform-http|from\s*\(\s*["\']platform-http:',
            re.MULTILINE
        ),

        # ── File ──────────────────────────────────────────────────
        'camel_file': re.compile(
            r'from\s*\(\s*["\']file:|\.to\s*\(\s*["\']file:',
            re.MULTILINE
        ),
        'camel_ftp': re.compile(
            r'camel-ftp|from\s*\(\s*["\'](?:s?ftp|ftps):',
            re.MULTILINE
        ),

        # ── Database ──────────────────────────────────────────────
        'camel_jdbc': re.compile(
            r'camel-jdbc|from\s*\(\s*["\']jdbc:|\.to\s*\(\s*["\']jdbc:',
            re.MULTILINE
        ),
        'camel_jpa': re.compile(
            r'camel-jpa|from\s*\(\s*["\']jpa:|\.to\s*\(\s*["\']jpa:',
            re.MULTILINE
        ),
        'camel_sql': re.compile(
            r'camel-sql|from\s*\(\s*["\']sql:|\.to\s*\(\s*["\']sql:',
            re.MULTILINE
        ),
        'camel_mongodb': re.compile(
            r'camel-mongodb|from\s*\(\s*["\']mongodb:',
            re.MULTILINE
        ),

        # ── Cloud ─────────────────────────────────────────────────
        'camel_aws': re.compile(
            r'camel-aws|from\s*\(\s*["\']aws-',
            re.MULTILINE
        ),
        'camel_azure': re.compile(
            r'camel-azure|from\s*\(\s*["\']azure-',
            re.MULTILINE
        ),
        'camel_google': re.compile(
            r'camel-google|from\s*\(\s*["\']google-',
            re.MULTILINE
        ),

        # ── Testing ───────────────────────────────────────────────
        'camel_test': re.compile(
            r'import\s+org\.apache\.camel\.test\b|'
            r'CamelTestSupport|@MockEndpoints|AdviceWith',
            re.MULTILINE
        ),

        # ── Kamelet ───────────────────────────────────────────────
        'camel_kamelet': re.compile(
            r'from\s*\(\s*["\']kamelet:|KameletMain|'
            r'import\s+org\.apache\.camel\.kamelet',
            re.MULTILINE
        ),

        # ── Data formats ──────────────────────────────────────────
        'camel_jackson': re.compile(
            r'camel-jackson|JacksonDataFormat|import\s+org\.apache\.camel\.component\.jackson',
            re.MULTILINE
        ),
        'camel_jaxb': re.compile(
            r'camel-jaxb|JaxbDataFormat',
            re.MULTILINE
        ),

        # ── Integration patterns ──────────────────────────────────
        'camel_saga': re.compile(
            r'\.saga\s*\(|import\s+org\.apache\.camel\.saga',
            re.MULTILINE
        ),
        'camel_resilience4j': re.compile(
            r'camel-resilience4j|\.circuitBreaker\s*\(',
            re.MULTILINE
        ),
    }

    VERSION_INDICATORS = {
        '4.x': re.compile(
            r'import\s+jakarta\b.*camel|camel-jbang|'
            r'org\.apache\.camel\.builder\.endpoint'
        ),
        '3.x': re.compile(
            r'EndpointRouteBuilder|camel-quarkus|'
            r'kamelet:|camel\.main\.'
        ),
        '2.x': re.compile(
            r'import\s+org\.apache\.camel\.spring\b|'
            r'camelContext.*xmlns.*spring'
        ),
    }

    def __init__(self):
        """Initialize the enhanced Apache Camel parser with all extractors."""
        self.route_extractor = CamelRouteExtractor()
        self.component_extractor = CamelComponentExtractor()
        self.processor_extractor = CamelProcessorExtractor()
        self.error_handler_extractor = CamelErrorHandlerExtractor()
        self.rest_dsl_extractor = CamelRestDSLExtractor()

    def is_camel_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file contains Apache Camel code."""
        if not content:
            return False

        camel_patterns = [
            r'import\s+org\.apache\.camel\.',
            r'extends\s+RouteBuilder',
            r'from\s*\(\s*["\'][\w-]+:',
            r'\.to\s*\(\s*["\'][\w-]+:',
            r'CamelContext',
            r'ProducerTemplate',
            r'ConsumerTemplate',
            r'<camelContext',
            r'rest\s*\(\s*["\']/',
        ]
        for pattern in camel_patterns:
            if re.search(pattern, content):
                return True
        return False

    def parse(self, content: str, file_path: str = "") -> ApacheCamelParseResult:
        """Parse Apache Camel source code and extract all integration information."""
        result = ApacheCamelParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        result.detected_frameworks = self._detect_frameworks(content)
        result.camel_version = self._detect_version(content)

        # Routes
        route_result = self.route_extractor.extract(content, file_path)
        result.routes = route_result.get('routes', [])
        result.endpoints = route_result.get('endpoints', [])
        result.route_builder_classes = route_result.get('route_builder_classes', [])

        # Components
        comp_result = self.component_extractor.extract(content, file_path)
        result.components = comp_result.get('components', [])
        result.data_formats = comp_result.get('data_formats', [])
        result.has_type_converters = comp_result.get('has_type_converters', False)

        # Processors / EIP
        proc_result = self.processor_extractor.extract(content, file_path)
        result.processors = proc_result.get('processors', [])
        result.eip_patterns = proc_result.get('eip_patterns', [])

        # Error handling
        err_result = self.error_handler_extractor.extract(content, file_path)
        result.error_handlers = err_result.get('error_handlers', [])
        result.exception_clauses = err_result.get('exception_clauses', [])
        result.has_on_completion = err_result.get('has_on_completion', False)

        # REST DSL
        rest_result = self.rest_dsl_extractor.extract(content, file_path)
        result.rest_definitions = rest_result.get('rest_definitions', [])
        result.rest_operations = rest_result.get('rest_operations', [])
        result.has_openapi = rest_result.get('has_openapi', False)
        result.rest_config = rest_result.get('rest_config', {})

        # Totals
        result.total_routes = len(result.routes)
        result.total_endpoints = len(result.endpoints)
        result.total_eip_patterns = len(result.eip_patterns)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Camel ecosystem frameworks are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect Camel version from code patterns."""
        for version, pattern in self.VERSION_INDICATORS.items():
            if pattern.search(content):
                return version
        return ""
