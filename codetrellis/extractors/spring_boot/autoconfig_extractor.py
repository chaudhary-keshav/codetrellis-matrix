"""
Spring Boot Auto-Configuration Extractor v1.0

Extracts Spring Boot auto-configuration, starters, and customizer patterns.

Extracts:
- @EnableAutoConfiguration and exclusions
- @SpringBootApplication (combined annotation)
- Auto-configuration classes (META-INF/spring.factories pattern)
- @ConditionalOn* conditions at class level
- Starter detection from dependencies
- Customizer beans (WebServerFactoryCustomizer, Jackson, etc.)
- @Enable* annotations (EnableCaching, EnableScheduling, EnableAsync, etc.)

Part of CodeTrellis v4.94 - Spring Boot Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class SpringBootAutoConfigInfo:
    """Auto-configuration class or @SpringBootApplication."""
    name: str
    config_type: str = ""  # spring_boot_app, auto_configuration, enable_annotation
    excludes: List[str] = field(default_factory=list)  # Excluded auto-configs
    scan_packages: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    enables: List[str] = field(default_factory=list)  # @Enable* annotations
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootStarterInfo:
    """Detected Spring Boot starter dependency."""
    starter_name: str  # spring-boot-starter-web, etc.
    category: str = ""  # web, data, security, messaging, cloud, test, etc.
    version: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootCustomizerInfo:
    """Spring Boot customizer bean (WebServerFactory, Jackson, etc.)."""
    name: str
    customizer_type: str = ""  # web_server, jackson, error_page, etc.
    target_class: str = ""
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class SpringBootAutoConfigExtractor:
    """Extracts Spring Boot auto-configuration and starter patterns."""

    # @SpringBootApplication
    SPRING_BOOT_APP_PATTERN = re.compile(
        r'@SpringBootApplication'
        r'(?:\(\s*'
        r'(?:exclude\s*=\s*(?:\{([^}]*)\}|(\w+\.class)))?'
        r'(?:\s*,\s*scanBasePackages\s*=\s*(?:\{([^}]*)\}|"([^"]*)"))?'
        r'\s*\))?\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    # @EnableAutoConfiguration
    ENABLE_AUTOCONFIG_PATTERN = re.compile(
        r'@EnableAutoConfiguration'
        r'(?:\(\s*exclude\s*=\s*(?:\{([^}]*)\}|(\w+\.class))\s*\))?\s*',
        re.MULTILINE
    )

    # @Enable* annotations
    ENABLE_PATTERN = re.compile(
        r'@Enable(\w+)(?:\([^)]*\))?',
        re.MULTILINE
    )

    # Common @Enable annotations
    KNOWN_ENABLES = {
        'EnableCaching', 'EnableScheduling', 'EnableAsync',
        'EnableTransactionManagement', 'EnableJpaRepositories',
        'EnableJpaAuditing', 'EnableWebSecurity', 'EnableWebMvc',
        'EnableWebFlux', 'EnableMethodSecurity', 'EnableGlobalMethodSecurity',
        'EnableConfigurationProperties', 'EnableFeignClients',
        'EnableCircuitBreaker', 'EnableEurekaClient', 'EnableDiscoveryClient',
        'EnableKafka', 'EnableRabbit', 'EnableJms',
        'EnableBatchProcessing', 'EnableIntegration', 'EnableRetry',
        'EnableWebSocketMessageBroker', 'EnableAspectJAutoProxy',
        'EnableSwagger2', 'EnableOpenApi',
    }

    # Customizer patterns
    CUSTOMIZER_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+'
        r'(WebServerFactoryCustomizer|WebMvcConfigurer|WebFluxConfigurer|'
        r'Jackson2ObjectMapperBuilderCustomizer|ErrorPageRegistrar|'
        r'RestTemplateCustomizer|WebClientCustomizer|'
        r'HealthContributor|InfoContributor)',
        re.MULTILINE
    )

    # Spring Boot starter pattern in build files
    STARTER_PATTERN = re.compile(
        r'spring-boot-starter(?:-(\w[\w-]*))?',
        re.MULTILINE
    )

    STARTER_CATEGORIES = {
        'web': 'web', 'webflux': 'web', 'websocket': 'web',
        'data-jpa': 'data', 'data-mongodb': 'data', 'data-redis': 'data',
        'data-cassandra': 'data', 'data-elasticsearch': 'data',
        'data-r2dbc': 'data', 'jdbc': 'data',
        'security': 'security', 'oauth2-client': 'security',
        'oauth2-resource-server': 'security',
        'amqp': 'messaging', 'kafka': 'messaging',
        'mail': 'messaging',
        'test': 'test', 'actuator': 'ops',
        'validation': 'validation', 'cache': 'cache',
        'batch': 'batch', 'integration': 'integration',
        'cloud-starter': 'cloud',
        'aop': 'aop', 'logging': 'logging',
        'thymeleaf': 'template', 'freemarker': 'template',
        'mustache': 'template',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract auto-configuration patterns from Java source code."""
        result: Dict[str, Any] = {
            'auto_configs': [],
            'starters': [],
            'customizers': [],
        }

        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # @SpringBootApplication
        for match in self.SPRING_BOOT_APP_PATTERN.finditer(content):
            excludes_str = match.group(1) or match.group(2) or ""
            excludes = [e.strip().replace('.class', '') for e in excludes_str.split(',') if e.strip()] if excludes_str else []
            scan_str = match.group(3) or match.group(4) or ""
            scans = [s.strip().strip('"') for s in scan_str.split(',') if s.strip()] if scan_str else []
            class_name = match.group(5)

            # Collect @Enable* annotations
            context_start = max(0, match.start() - 1000)
            context = content[context_start:match.end()]
            enables = self._extract_enables(context)

            result['auto_configs'].append(SpringBootAutoConfigInfo(
                name=class_name,
                config_type='spring_boot_app',
                excludes=excludes,
                scan_packages=scans,
                enables=enables,
                annotations=['SpringBootApplication'],
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @EnableAutoConfiguration (standalone)
        for match in self.ENABLE_AUTOCONFIG_PATTERN.finditer(content):
            excludes_str = match.group(1) or match.group(2) or ""
            excludes = [e.strip().replace('.class', '') for e in excludes_str.split(',') if e.strip()] if excludes_str else []

            result['auto_configs'].append(SpringBootAutoConfigInfo(
                name='',
                config_type='auto_configuration',
                excludes=excludes,
                annotations=['EnableAutoConfiguration'],
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Customizers
        for match in self.CUSTOMIZER_PATTERN.finditer(content):
            class_name = match.group(1)
            iface = match.group(2)

            type_map = {
                'WebServerFactoryCustomizer': 'web_server',
                'WebMvcConfigurer': 'web_mvc',
                'WebFluxConfigurer': 'web_flux',
                'Jackson2ObjectMapperBuilderCustomizer': 'jackson',
                'ErrorPageRegistrar': 'error_page',
                'RestTemplateCustomizer': 'rest_template',
                'WebClientCustomizer': 'web_client',
                'HealthContributor': 'health',
                'InfoContributor': 'info',
            }

            result['customizers'].append(SpringBootCustomizerInfo(
                name=class_name,
                customizer_type=type_map.get(iface, 'other'),
                target_class=iface,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Starters (from build files content)
        for match in self.STARTER_PATTERN.finditer(content):
            suffix = match.group(1) or ''
            starter_name = f"spring-boot-starter-{suffix}" if suffix else "spring-boot-starter"
            category = self.STARTER_CATEGORIES.get(suffix, 'core')

            result['starters'].append(SpringBootStarterInfo(
                starter_name=starter_name,
                category=category,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return result

    def _extract_enables(self, text: str) -> List[str]:
        enables = []
        for m in self.ENABLE_PATTERN.finditer(text):
            name = f"Enable{m.group(1)}"
            if name in self.KNOWN_ENABLES:
                enables.append(name)
        return enables
