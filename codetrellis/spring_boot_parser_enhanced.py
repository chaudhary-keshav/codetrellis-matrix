"""
EnhancedSpringBootParser v1.0 - Comprehensive Spring Boot parser using all extractors.

This parser integrates all Spring Boot extractors to provide complete parsing of
Spring Boot application files. It runs as a supplementary layer on top of the
Java parser, extracting Spring Boot-specific semantics.

Supports:
- Spring Boot 1.x (basic auto-configuration, embedded containers, externalized config)
- Spring Boot 2.x (WebFlux, Spring Security 5, actuator 2.x, Micrometer, Config Server)
- Spring Boot 3.x (Jakarta EE 9+ namespace, Spring Security 6, native images, virtual threads,
                    HTTP interfaces, observability, Problem Details RFC 7807)

Spring Boot-specific extraction:
- Beans: @Component, @Service, @Repository, @Controller, @Configuration, @Bean
- Auto-Config: @SpringBootApplication, @EnableAutoConfiguration, @ConditionalOn*
- Endpoints: REST controllers, WebFlux handlers, Actuator custom endpoints
- Properties: application.properties/yml, @ConfigurationProperties, @Value, profiles
- Security: SecurityFilterChain, OAuth2, JWT, method security, CORS/CSRF
- Data: Spring Data repositories, @Query, @Cacheable, @Transactional

Framework detection (50+ Spring Boot ecosystem patterns):
- Core: spring-boot, spring-boot-autoconfigure, spring-boot-actuator
- Web: spring-webmvc, spring-webflux, spring-websocket
- Data: spring-data-jpa, spring-data-mongodb, spring-data-redis, spring-data-r2dbc
- Security: spring-security, spring-security-oauth2, spring-security-jwt
- Cloud: spring-cloud-config, eureka, zuul, gateway, feign, ribbon, hystrix
- Messaging: spring-kafka, spring-amqp, spring-jms
- Testing: spring-boot-test, spring-security-test, testcontainers

Part of CodeTrellis v4.94 - Spring Boot Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Spring Boot extractors
from .extractors.spring_boot import (
    SpringBootBeanExtractor, SpringBootBeanInfo, SpringBootConfigurationInfo,
    SpringBootBeanMethodInfo, SpringBootProfileInfo, SpringBootConditionInfo,
    SpringBootAutoConfigExtractor, SpringBootAutoConfigInfo,
    SpringBootStarterInfo, SpringBootCustomizerInfo,
    SpringBootEndpointExtractor, SpringBootControllerInfo,
    SpringBootEndpointInfo, SpringBootActuatorInfo, SpringBootWebFluxHandlerInfo,
    SpringBootPropertyExtractor, SpringBootPropertyInfo,
    SpringBootConfigPropsInfo, SpringBootProfileConfigInfo,
    SpringBootSecurityExtractor, SpringBootSecurityConfigInfo,
    SpringBootAuthInfo, SpringBootMethodSecurityInfo,
    SpringBootDataExtractor, SpringBootRepoInfo,
    SpringBootQueryMethodInfo, SpringBootCacheInfo, SpringBootTransactionInfo,
)


@dataclass
class SpringBootParseResult:
    """Complete parse result for a Spring Boot file."""
    file_path: str
    file_type: str = "spring_boot"

    # Beans
    beans: List[SpringBootBeanInfo] = field(default_factory=list)
    configurations: List[SpringBootConfigurationInfo] = field(default_factory=list)
    bean_methods: List[SpringBootBeanMethodInfo] = field(default_factory=list)
    profiles: List[SpringBootProfileInfo] = field(default_factory=list)
    conditions: List[SpringBootConditionInfo] = field(default_factory=list)

    # Auto-Configuration
    auto_configs: List[SpringBootAutoConfigInfo] = field(default_factory=list)
    starters: List[SpringBootStarterInfo] = field(default_factory=list)
    customizers: List[SpringBootCustomizerInfo] = field(default_factory=list)

    # Endpoints
    controllers: List[SpringBootControllerInfo] = field(default_factory=list)
    endpoints: List[SpringBootEndpointInfo] = field(default_factory=list)
    actuators: List[SpringBootActuatorInfo] = field(default_factory=list)
    webflux_handlers: List[SpringBootWebFluxHandlerInfo] = field(default_factory=list)

    # Properties
    properties: List[SpringBootPropertyInfo] = field(default_factory=list)
    config_props_classes: List[SpringBootConfigPropsInfo] = field(default_factory=list)
    profile_configs: List[SpringBootProfileConfigInfo] = field(default_factory=list)

    # Security
    security_configs: List[SpringBootSecurityConfigInfo] = field(default_factory=list)
    auth_infos: List[SpringBootAuthInfo] = field(default_factory=list)
    method_security: List[SpringBootMethodSecurityInfo] = field(default_factory=list)

    # Data
    repositories: List[SpringBootRepoInfo] = field(default_factory=list)
    query_methods: List[SpringBootQueryMethodInfo] = field(default_factory=list)
    caches: List[SpringBootCacheInfo] = field(default_factory=list)
    transactions: List[SpringBootTransactionInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    spring_boot_version: str = ""
    is_reactive: bool = False
    total_beans: int = 0
    total_endpoints: int = 0
    total_configs: int = 0


class EnhancedSpringBootParser:
    """
    Enhanced Spring Boot parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the Java parser when Spring Boot
    framework is detected. It extracts Spring Boot-specific semantics
    that the base Java parser cannot capture in full detail.

    Supports Spring Boot 1.x through 3.x.
    """

    # Spring Boot ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core Spring Boot ─────────────────────────────────────
        'spring_boot': re.compile(
            r'import\s+org\.springframework\.boot\b|'
            r'@SpringBootApplication|@EnableAutoConfiguration|'
            r'SpringApplication\.run',
            re.MULTILINE
        ),
        'spring_boot_autoconfigure': re.compile(
            r'import\s+org\.springframework\.boot\.autoconfigure\b|'
            r'@ConditionalOn\w+',
            re.MULTILINE
        ),
        'spring_boot_actuator': re.compile(
            r'import\s+org\.springframework\.boot\.actuate\b|'
            r'@Endpoint\(|management\.endpoints',
            re.MULTILINE
        ),
        'spring_boot_devtools': re.compile(
            r'spring-boot-devtools|org\.springframework\.boot\.devtools',
            re.MULTILINE
        ),

        # ── Web ──────────────────────────────────────────────────
        'spring_webmvc': re.compile(
            r'import\s+org\.springframework\.web\.servlet\b|'
            r'@RestController|@Controller(?!Advice)\b|'
            r'@RequestMapping|@GetMapping|@PostMapping',
            re.MULTILINE
        ),
        'spring_webflux': re.compile(
            r'import\s+org\.springframework\.web\.reactive\b|'
            r'RouterFunction|HandlerFunction|ServerResponse|'
            r'@EnableWebFlux|WebFluxConfigurer',
            re.MULTILINE
        ),
        'spring_websocket': re.compile(
            r'import\s+org\.springframework\.web\.socket\b|'
            r'@EnableWebSocket|WebSocketHandler|SockJS',
            re.MULTILINE
        ),

        # ── Data ─────────────────────────────────────────────────
        'spring_data_jpa': re.compile(
            r'import\s+org\.springframework\.data\.jpa\b|'
            r'JpaRepository|@EnableJpaRepositories|@EnableJpaAuditing',
            re.MULTILINE
        ),
        'spring_data_mongodb': re.compile(
            r'import\s+org\.springframework\.data\.mongodb\b|'
            r'MongoRepository|@EnableMongoRepositories',
            re.MULTILINE
        ),
        'spring_data_redis': re.compile(
            r'import\s+org\.springframework\.data\.redis\b|'
            r'RedisTemplate|StringRedisTemplate|@EnableRedisRepositories',
            re.MULTILINE
        ),
        'spring_data_r2dbc': re.compile(
            r'import\s+org\.springframework\.data\.r2dbc\b|'
            r'R2dbcRepository|@EnableR2dbcRepositories',
            re.MULTILINE
        ),
        'spring_data_elasticsearch': re.compile(
            r'import\s+org\.springframework\.data\.elasticsearch\b|'
            r'ElasticsearchRepository|@EnableElasticsearchRepositories',
            re.MULTILINE
        ),

        # ── Security ─────────────────────────────────────────────
        'spring_security': re.compile(
            r'import\s+org\.springframework\.security\b|'
            r'@EnableWebSecurity|SecurityFilterChain|'
            r'WebSecurityConfigurerAdapter',
            re.MULTILINE
        ),
        'spring_security_oauth2': re.compile(
            r'import\s+org\.springframework\.security\.oauth2\b|'
            r'@EnableOAuth2Client|@EnableResourceServer|'
            r'\.oauth2Login\(|\.oauth2ResourceServer\(',
            re.MULTILINE
        ),
        'spring_security_jwt': re.compile(
            r'JwtDecoder|JwtAuthenticationConverter|JwtGrantedAuthoritiesConverter|'
            r'NimbusJwtDecoder',
            re.MULTILINE
        ),

        # ── Cloud ────────────────────────────────────────────────
        'spring_cloud_config': re.compile(
            r'@EnableConfigServer|@RefreshScope|spring\.cloud\.config',
            re.MULTILINE
        ),
        'spring_cloud_eureka': re.compile(
            r'@EnableEurekaClient|@EnableEurekaServer|@EnableDiscoveryClient',
            re.MULTILINE
        ),
        'spring_cloud_gateway': re.compile(
            r'import\s+org\.springframework\.cloud\.gateway\b|'
            r'RouteLocator|@EnableGateway',
            re.MULTILINE
        ),
        'spring_cloud_feign': re.compile(
            r'@EnableFeignClients|@FeignClient',
            re.MULTILINE
        ),
        'spring_cloud_circuit_breaker': re.compile(
            r'@CircuitBreaker|@Retry|@Bulkhead|Resilience4j|'
            r'CircuitBreakerFactory',
            re.MULTILINE
        ),
        'spring_cloud_stream': re.compile(
            r'import\s+org\.springframework\.cloud\.stream\b|'
            r'@EnableBinding|StreamBridge',
            re.MULTILINE
        ),

        # ── Messaging ────────────────────────────────────────────
        'spring_kafka': re.compile(
            r'import\s+org\.springframework\.kafka\b|'
            r'@KafkaListener|KafkaTemplate|@EnableKafka',
            re.MULTILINE
        ),
        'spring_amqp': re.compile(
            r'import\s+org\.springframework\.amqp\b|'
            r'@RabbitListener|RabbitTemplate|@EnableRabbit',
            re.MULTILINE
        ),
        'spring_jms': re.compile(
            r'import\s+org\.springframework\.jms\b|'
            r'@JmsListener|JmsTemplate|@EnableJms',
            re.MULTILINE
        ),

        # ── Batch & Integration ──────────────────────────────────
        'spring_batch': re.compile(
            r'import\s+org\.springframework\.batch\b|'
            r'@EnableBatchProcessing|Job\b|Step\b',
            re.MULTILINE
        ),
        'spring_integration': re.compile(
            r'import\s+org\.springframework\.integration\b|'
            r'@EnableIntegration|IntegrationFlow',
            re.MULTILINE
        ),

        # ── Testing ──────────────────────────────────────────────
        'spring_boot_test': re.compile(
            r'@SpringBootTest|@WebMvcTest|@DataJpaTest|'
            r'@WebFluxTest|@MockBean|@SpyBean|TestRestTemplate',
            re.MULTILINE
        ),
        'spring_security_test': re.compile(
            r'@WithMockUser|@WithAnonymousUser|'
            r'SecurityMockMvcRequestPostProcessors',
            re.MULTILINE
        ),

        # ── Observability ────────────────────────────────────────
        'micrometer': re.compile(
            r'import\s+io\.micrometer\b|MeterRegistry|@Timed|@Counted',
            re.MULTILINE
        ),
        'spring_boot_actuator_metrics': re.compile(
            r'management\.metrics|management\.endpoint\.metrics',
            re.MULTILINE
        ),

        # ── Utilities ────────────────────────────────────────────
        'spring_validation': re.compile(
            r'import\s+org\.springframework\.validation\b|'
            r'@Valid(?:ated)?|BindingResult',
            re.MULTILINE
        ),
        'spring_hateoas': re.compile(
            r'import\s+org\.springframework\.hateoas\b|'
            r'EntityModel|CollectionModel|RepresentationModel|'
            r'WebMvcLinkBuilder',
            re.MULTILINE
        ),
        'spring_cache': re.compile(
            r'@EnableCaching|@Cacheable|@CacheEvict|@CachePut',
            re.MULTILINE
        ),
        'spring_scheduling': re.compile(
            r'@EnableScheduling|@Scheduled|TaskScheduler',
            re.MULTILINE
        ),
        'spring_async': re.compile(
            r'@EnableAsync|@Async\b|CompletableFuture',
            re.MULTILINE
        ),
        'spring_retry': re.compile(
            r'@EnableRetry|@Retryable|@Recover',
            re.MULTILINE
        ),

        # ── Third-party commonly with Spring Boot ────────────────
        'swagger_springdoc': re.compile(
            r'import\s+io\.swagger\b|import\s+org\.springdoc\b|'
            r'@ApiOperation|@Operation|@Tag',
            re.MULTILINE
        ),
        'mapstruct': re.compile(
            r'import\s+org\.mapstruct\b|@Mapper\b',
            re.MULTILINE
        ),
        'lombok': re.compile(
            r'import\s+lombok\b|@Data\b|@Builder\b|@AllArgsConstructor|@NoArgsConstructor',
            re.MULTILINE
        ),
        'flyway': re.compile(
            r'spring\.flyway|import\s+org\.flywaydb\b',
            re.MULTILINE
        ),
        'liquibase': re.compile(
            r'spring\.liquibase|import\s+liquibase\b',
            re.MULTILINE
        ),
        'testcontainers': re.compile(
            r'@Testcontainers|@Container|GenericContainer|'
            r'import\s+org\.testcontainers\b',
            re.MULTILINE
        ),
    }

    # Spring Boot version detection from imports / patterns
    VERSION_INDICATORS = {
        '3.x': re.compile(
            r'import\s+jakarta\.\b|ProblemDetail|HttpServiceProxyFactory|'
            r'\.oauth2ResourceServer\(\s*oauth2\s*->|'
            r'@EnableMethodSecurity\b'
        ),
        '2.x': re.compile(
            r'import\s+javax\.\b.*(?!jakarta)|WebSecurityConfigurerAdapter|'
            r'@EnableGlobalMethodSecurity\b'
        ),
        '1.x': re.compile(
            r'@EnableAutoConfigurationReport|spring\.profiles\.active'
        ),
    }

    def __init__(self):
        """Initialize the enhanced Spring Boot parser with all extractors."""
        self.bean_extractor = SpringBootBeanExtractor()
        self.autoconfig_extractor = SpringBootAutoConfigExtractor()
        self.endpoint_extractor = SpringBootEndpointExtractor()
        self.property_extractor = SpringBootPropertyExtractor()
        self.security_extractor = SpringBootSecurityExtractor()
        self.data_extractor = SpringBootDataExtractor()

    def is_spring_boot_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file contains Spring Boot code."""
        if not content:
            return False

        # Properties/YAML files in src/main/resources
        if file_path.endswith(('.properties', '.yml', '.yaml')):
            if 'application' in file_path.split('/')[-1]:
                return True
            if 'spring.' in content or 'server.' in content or 'management.' in content:
                return True

        # Java files with Spring Boot imports
        spring_patterns = [
            r'import\s+org\.springframework\.boot\b',
            r'import\s+org\.springframework\.web\b',
            r'import\s+org\.springframework\.data\b',
            r'import\s+org\.springframework\.security\b',
            r'import\s+org\.springframework\.cloud\b',
            r'import\s+org\.springframework\.kafka\b',
            r'import\s+org\.springframework\.amqp\b',
            r'@SpringBootApplication',
            r'@RestController',
            r'@Configuration\b',
            r'@ConfigurationProperties',
            r'@EnableAutoConfiguration',
            r'@Component\b',
            r'@Service\b',
            r'@Repository\b',
        ]
        for pattern in spring_patterns:
            if re.search(pattern, content):
                return True

        return False

    def parse(self, content: str, file_path: str = "") -> SpringBootParseResult:
        """
        Parse Spring Boot source code and extract all Spring Boot-specific information.

        Args:
            content: Source code content (Java, properties, or YAML)
            file_path: Path to source file

        Returns:
            SpringBootParseResult with all extracted information
        """
        result = SpringBootParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect Spring Boot version
        result.spring_boot_version = self._detect_version(content)

        # Check if reactive
        result.is_reactive = any(
            fw in result.detected_frameworks
            for fw in ['spring_webflux', 'spring_data_r2dbc']
        )

        # Run all extractors
        # Beans
        bean_result = self.bean_extractor.extract(content, file_path)
        result.beans = bean_result.get('beans', [])
        result.configurations = bean_result.get('configurations', [])
        result.bean_methods = bean_result.get('bean_methods', [])
        result.profiles = bean_result.get('profiles', [])
        result.conditions = bean_result.get('conditions', [])

        # Auto-configuration
        autoconfig_result = self.autoconfig_extractor.extract(content, file_path)
        result.auto_configs = autoconfig_result.get('auto_configs', [])
        result.starters = autoconfig_result.get('starters', [])
        result.customizers = autoconfig_result.get('customizers', [])

        # Endpoints
        endpoint_result = self.endpoint_extractor.extract(content, file_path)
        result.controllers = endpoint_result.get('controllers', [])
        result.endpoints = endpoint_result.get('endpoints', [])
        result.actuators = endpoint_result.get('actuators', [])
        result.webflux_handlers = endpoint_result.get('webflux_handlers', [])

        # Properties
        property_result = self.property_extractor.extract(content, file_path)
        result.properties = property_result.get('properties', [])
        result.config_props_classes = property_result.get('config_props_classes', [])
        result.profile_configs = property_result.get('profile_configs', [])

        # Security
        security_result = self.security_extractor.extract(content, file_path)
        result.security_configs = security_result.get('security_configs', [])
        result.auth_infos = security_result.get('auth_infos', [])
        result.method_security = security_result.get('method_security', [])

        # Data
        data_result = self.data_extractor.extract(content, file_path)
        result.repositories = data_result.get('repositories', [])
        result.query_methods = data_result.get('query_methods', [])
        result.caches = data_result.get('caches', [])
        result.transactions = data_result.get('transactions', [])

        # Compute totals
        result.total_beans = len(result.beans) + len(result.bean_methods)
        result.total_endpoints = len(result.endpoints) + len(result.webflux_handlers)
        result.total_configs = len(result.configurations) + len(result.auto_configs)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Spring Boot ecosystem frameworks are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect Spring Boot version from code patterns."""
        for version, pattern in self.VERSION_INDICATORS.items():
            if pattern.search(content):
                return version
        return ""
