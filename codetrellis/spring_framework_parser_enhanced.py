"""
EnhancedSpringFrameworkParser v1.0 - Spring Framework core patterns parser.

Extracts Spring Framework-specific patterns that go beyond what the base Java parser
and Spring Boot parser capture: DI wiring, AOP aspects, event system, MVC infrastructure.

Supports:
- Spring Framework 4.x (Java config, @Conditional, SpEL improvements)
- Spring Framework 5.x (WebFlux, Kotlin extensions, functional bean registration)
- Spring Framework 6.x (Jakarta EE 9+, native images, HTTP interfaces, virtual threads)

Part of CodeTrellis v4.94 - Spring Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

from .extractors.spring_framework import (
    SpringDIExtractor, SpringDIInfo, SpringBeanDefinitionInfo, SpringQualifierInfo,
    SpringAOPExtractor, SpringAspectInfo, SpringAdviceInfo, SpringPointcutInfo,
    SpringEventExtractor, SpringEventInfo, SpringEventListenerInfo, SpringEventPublisherInfo,
    SpringMVCExtractor, SpringInterceptorInfo, SpringConverterInfo, SpringResolverInfo,
)


@dataclass
class SpringFrameworkParseResult:
    """Complete parse result for Spring Framework patterns."""
    file_path: str
    file_type: str = "spring_framework"

    # DI
    injections: List[SpringDIInfo] = field(default_factory=list)
    bean_definitions: List[SpringBeanDefinitionInfo] = field(default_factory=list)
    qualifiers: List[SpringQualifierInfo] = field(default_factory=list)

    # AOP
    aspects: List[SpringAspectInfo] = field(default_factory=list)
    advices: List[SpringAdviceInfo] = field(default_factory=list)
    pointcuts: List[SpringPointcutInfo] = field(default_factory=list)

    # Events
    events: List[SpringEventInfo] = field(default_factory=list)
    event_listeners: List[SpringEventListenerInfo] = field(default_factory=list)
    event_publishers: List[SpringEventPublisherInfo] = field(default_factory=list)

    # MVC Infrastructure
    interceptors: List[SpringInterceptorInfo] = field(default_factory=list)
    converters: List[SpringConverterInfo] = field(default_factory=list)
    resolvers: List[SpringResolverInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    spring_version: str = ""
    total_injections: int = 0
    total_aspects: int = 0
    total_events: int = 0


class EnhancedSpringFrameworkParser:
    """Enhanced Spring Framework parser for core patterns."""

    FRAMEWORK_PATTERNS = {
        'spring_core': re.compile(
            r'import\s+org\.springframework\.context\b|'
            r'import\s+org\.springframework\.beans\b|'
            r'ApplicationContext|BeanFactory',
            re.MULTILINE
        ),
        'spring_aop': re.compile(
            r'import\s+org\.springframework\.aop\b|'
            r'import\s+org\.aspectj\b|@Aspect|@Pointcut',
            re.MULTILINE
        ),
        'spring_tx': re.compile(
            r'import\s+org\.springframework\.transaction\b|'
            r'@Transactional|PlatformTransactionManager',
            re.MULTILINE
        ),
        'spring_events': re.compile(
            r'ApplicationEvent|@EventListener|ApplicationEventPublisher',
            re.MULTILINE
        ),
        'spring_spel': re.compile(
            r'SpelExpressionParser|ExpressionParser|#\{[^}]+\}',
            re.MULTILINE
        ),
        'spring_mvc': re.compile(
            r'import\s+org\.springframework\.web\.servlet\b|'
            r'WebMvcConfigurer|HandlerInterceptor|ViewResolver',
            re.MULTILINE
        ),
        'spring_webflux': re.compile(
            r'import\s+org\.springframework\.web\.reactive\b|'
            r'WebFluxConfigurer|RouterFunction',
            re.MULTILINE
        ),
        'spring_test': re.compile(
            r'@SpringBootTest|@ContextConfiguration|@RunWith\(SpringRunner',
            re.MULTILINE
        ),
    }

    VERSION_INDICATORS = {
        '6.x': re.compile(r'import\s+jakarta\.\b|HttpServiceProxyFactory'),
        '5.x': re.compile(r'import\s+javax\.\b|RouterFunction|WebFluxConfigurer'),
        '4.x': re.compile(r'@Conditional\b|@PropertySource'),
    }

    def __init__(self):
        self.di_extractor = SpringDIExtractor()
        self.aop_extractor = SpringAOPExtractor()
        self.event_extractor = SpringEventExtractor()
        self.mvc_extractor = SpringMVCExtractor()

    def is_spring_framework_file(self, content: str, file_path: str = "") -> bool:
        """Check if file contains Spring Framework core patterns."""
        if not content:
            return False

        # XML spring config
        if file_path.endswith('.xml') and ('springframework' in content or '<beans' in content):
            return True

        patterns = [
            r'import\s+org\.springframework\.',
            r'@Autowired|@Inject|@Resource\b',
            r'@Aspect|@Pointcut',
            r'@EventListener|ApplicationEventPublisher',
            r'HandlerInterceptor|WebMvcConfigurer',
        ]
        for p in patterns:
            if re.search(p, content):
                return True
        return False

    def parse(self, content: str, file_path: str = "") -> SpringFrameworkParseResult:
        """Parse Spring Framework patterns."""
        result = SpringFrameworkParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        result.detected_frameworks = self._detect_frameworks(content)
        result.spring_version = self._detect_version(content)

        # DI
        di_result = self.di_extractor.extract(content, file_path)
        result.injections = di_result.get('injections', [])
        result.bean_definitions = di_result.get('bean_definitions', [])
        result.qualifiers = di_result.get('qualifiers', [])

        # AOP
        aop_result = self.aop_extractor.extract(content, file_path)
        result.aspects = aop_result.get('aspects', [])
        result.advices = aop_result.get('advices', [])
        result.pointcuts = aop_result.get('pointcuts', [])

        # Events
        event_result = self.event_extractor.extract(content, file_path)
        result.events = event_result.get('events', [])
        result.event_listeners = event_result.get('listeners', [])
        result.event_publishers = event_result.get('publishers', [])

        # MVC
        mvc_result = self.mvc_extractor.extract(content, file_path)
        result.interceptors = mvc_result.get('interceptors', [])
        result.converters = mvc_result.get('converters', [])
        result.resolvers = mvc_result.get('resolvers', [])

        # Totals
        result.total_injections = len(result.injections)
        result.total_aspects = len(result.aspects)
        result.total_events = len(result.events) + len(result.event_listeners)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_version(self, content: str) -> str:
        for version, pattern in self.VERSION_INDICATORS.items():
            if pattern.search(content):
                return version
        return ""
