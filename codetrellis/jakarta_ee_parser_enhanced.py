"""
Enhanced Jakarta EE Parser v1.0
Part of CodeTrellis v4.94 - Jakarta EE Framework Support

Extracts Jakarta EE patterns:
- CDI 4.0+ beans, producers, decorators, events
- Servlets, filters, listeners
- JPA entities, relationships, named queries
- JAX-RS resources, endpoints, providers
- EJB session beans, message-driven beans, timers
- Version detection (Java EE 5 → Jakarta EE 10+)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any

from codetrellis.extractors.jakarta_ee import (
    JakartaCDIExtractor,
    JakartaCDIBeanInfo,
    JakartaProducerInfo,
    JakartaDecoratorInfo,
    JakartaServletExtractor,
    JakartaServletInfo,
    JakartaServletFilterInfo,
    JakartaListenerInfo,
    JakartaJPAExtractor,
    JakartaEntityInfo,
    JakartaNamedQueryInfo,
    JakartaRelationshipInfo,
    JakartaJAXRSExtractor,
    JakartaResourceInfo,
    JakartaJAXRSEndpointInfo,
    JakartaProviderInfo,
    JakartaEJBExtractor,
    JakartaSessionBeanInfo,
    JakartaMessageDrivenBeanInfo,
    JakartaTimerInfo,
)


@dataclass
class JakartaEEParseResult:
    """Aggregated Jakarta EE parse result."""
    # CDI
    cdi_beans: List[Dict] = field(default_factory=list)
    producers: List[Dict] = field(default_factory=list)
    decorators: List[Dict] = field(default_factory=list)
    event_observers: List[Dict] = field(default_factory=list)
    # Servlet
    servlets: List[Dict] = field(default_factory=list)
    servlet_filters: List[Dict] = field(default_factory=list)
    listeners: List[Dict] = field(default_factory=list)
    # JPA
    jpa_entities: List[Dict] = field(default_factory=list)
    named_queries: List[Dict] = field(default_factory=list)
    relationships: List[Dict] = field(default_factory=list)
    # JAX-RS
    jaxrs_resources: List[Dict] = field(default_factory=list)
    jaxrs_endpoints: List[Dict] = field(default_factory=list)
    jaxrs_providers: List[Dict] = field(default_factory=list)
    jaxrs_applications: List[Dict] = field(default_factory=list)
    # EJB
    session_beans: List[Dict] = field(default_factory=list)
    message_driven_beans: List[Dict] = field(default_factory=list)
    timers: List[Dict] = field(default_factory=list)
    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    jakarta_version: str = ""
    namespace: str = ""  # jakarta or javax
    file_path: str = ""
    errors: List[str] = field(default_factory=list)


class EnhancedJakartaEEParser:
    """Parses Jakarta EE / Java EE patterns from source files and config files."""

    FRAMEWORK_PATTERNS: Dict[str, str] = {
        # CDI
        'jakarta_cdi': r'(?:jakarta|javax)\.enterprise\.(?:context|inject|event)\.',
        'jakarta_cdi_interceptor': r'(?:jakarta|javax)\.interceptor\.',
        # Servlet
        'jakarta_servlet': r'(?:jakarta|javax)\.servlet\.',
        'jakarta_websocket': r'(?:jakarta|javax)\.websocket\.',
        # JPA / Persistence
        'jakarta_jpa': r'(?:jakarta|javax)\.persistence\.',
        'jakarta_validation': r'(?:jakarta|javax)\.validation\.',
        # JAX-RS
        'jakarta_jaxrs': r'(?:jakarta|javax)\.ws\.rs\.',
        # EJB
        'jakarta_ejb': r'(?:jakarta|javax)\.ejb\.',
        # JMS
        'jakarta_jms': r'(?:jakarta|javax)\.jms\.',
        # Transactions
        'jakarta_transaction': r'(?:jakarta|javax)\.transaction\.',
        # JSON
        'jakarta_jsonp': r'(?:jakarta|javax)\.json\.',
        'jakarta_jsonb': r'(?:jakarta|javax)\.json\.bind\.',
        # Security
        'jakarta_security': r'(?:jakarta|javax)\.security\.enterprise\.',
        # Concurrency
        'jakarta_concurrency': r'(?:jakarta|javax)\.enterprise\.concurrent\.',
        # Batch
        'jakarta_batch': r'(?:jakarta|javax)\.batch\.',
        # Mail
        'jakarta_mail': r'(?:jakarta|javax)\.mail\.',
        # Faces
        'jakarta_faces': r'(?:jakarta|javax)\.faces\.',
        # Expression Language
        'jakarta_el': r'(?:jakarta|javax)\.el\.',
    }

    VERSION_INDICATORS: Dict[str, List[str]] = {
        'Jakarta EE 10': [
            'jakarta.enterprise',
            'jakarta.persistence',
            'jakarta.ws.rs',
        ],
        'Jakarta EE 9/9.1': [
            'jakarta.enterprise',
            'jakarta.servlet',
        ],
        'Java EE 8': [
            'javax.enterprise',
            'javax.persistence',
            'javax.ws.rs',
        ],
        'Java EE 7': [
            'javax.enterprise',
            'javax.ejb',
        ],
        'Java EE 6': [
            'javax.ejb',
            'javax.servlet',
        ],
        'Java EE 5': [
            'javax.ejb',
        ],
    }

    def __init__(self) -> None:
        self.cdi_extractor = JakartaCDIExtractor()
        self.servlet_extractor = JakartaServletExtractor()
        self.jpa_extractor = JakartaJPAExtractor()
        self.jaxrs_extractor = JakartaJAXRSExtractor()
        self.ejb_extractor = JakartaEJBExtractor()
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            try:
                self._compiled_patterns[name] = re.compile(pattern)
            except re.error:
                pass

    def is_jakarta_ee_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file uses Jakarta EE / Java EE APIs."""
        if not content:
            return False
        # Descriptor files
        if file_path.endswith(('web.xml', 'beans.xml', 'ejb-jar.xml', 'persistence.xml',
                                'application.xml', 'faces-config.xml')):
            return True
        # Source files
        jakarta_indicators = [
            r'import\s+(?:jakarta|javax)\.enterprise\.',
            r'import\s+(?:jakarta|javax)\.ejb\.',
            r'import\s+(?:jakarta|javax)\.servlet\.',
            r'import\s+(?:jakarta|javax)\.persistence\.',
            r'import\s+(?:jakarta|javax)\.ws\.rs\.',
            r'import\s+(?:jakarta|javax)\.inject\.',
            r'import\s+(?:jakarta|javax)\.faces\.',
            r'import\s+(?:jakarta|javax)\.jms\.',
            r'@Stateless', r'@Stateful', r'@MessageDriven',
            r'@WebServlet', r'@WebFilter', r'@WebListener',
            r'@Entity\b', r'@MappedSuperclass',
        ]
        return any(re.search(p, content) for p in jakarta_indicators)

    def parse(self, content: str, file_path: str = "") -> JakartaEEParseResult:
        """Parse a file for Jakarta EE patterns."""
        result = JakartaEEParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        try:
            result.detected_frameworks = self._detect_frameworks(content)
            result.jakarta_version = self._detect_version(content)
            result.namespace = 'jakarta' if re.search(r'import\s+jakarta\.', content) else (
                'javax' if re.search(r'import\s+javax\.', content) else ''
            )

            # CDI extraction
            cdi_result = self.cdi_extractor.extract(content, file_path)
            result.cdi_beans = [vars(b) if hasattr(b, '__dict__') else b for b in cdi_result.get('beans', [])]
            result.producers = [vars(p) if hasattr(p, '__dict__') else p for p in cdi_result.get('producers', [])]
            result.decorators = [vars(d) if hasattr(d, '__dict__') else d for d in cdi_result.get('decorators', [])]
            result.event_observers = cdi_result.get('event_observers', [])

            # Servlet extraction
            servlet_result = self.servlet_extractor.extract(content, file_path)
            result.servlets = [vars(s) if hasattr(s, '__dict__') else s for s in servlet_result.get('servlets', [])]
            result.servlet_filters = [vars(f) if hasattr(f, '__dict__') else f for f in servlet_result.get('filters', [])]
            result.listeners = [vars(l) if hasattr(l, '__dict__') else l for l in servlet_result.get('listeners', [])]

            # JPA extraction
            jpa_result = self.jpa_extractor.extract(content, file_path)
            result.jpa_entities = [vars(e) if hasattr(e, '__dict__') else e for e in jpa_result.get('entities', [])]
            result.named_queries = [vars(q) if hasattr(q, '__dict__') else q for q in jpa_result.get('named_queries', [])]
            result.relationships = [r if isinstance(r, dict) else vars(r) for r in jpa_result.get('relationships', [])]

            # JAX-RS extraction
            jaxrs_result = self.jaxrs_extractor.extract(content, file_path)
            result.jaxrs_resources = [vars(r) if hasattr(r, '__dict__') else r for r in jaxrs_result.get('resources', [])]
            result.jaxrs_endpoints = [vars(e) if hasattr(e, '__dict__') else e for e in jaxrs_result.get('endpoints', [])]
            result.jaxrs_providers = [vars(p) if hasattr(p, '__dict__') else p for p in jaxrs_result.get('providers', [])]
            result.jaxrs_applications = jaxrs_result.get('applications', [])

            # EJB extraction
            ejb_result = self.ejb_extractor.extract(content, file_path)
            result.session_beans = [vars(b) if hasattr(b, '__dict__') else b for b in ejb_result.get('session_beans', [])]
            result.message_driven_beans = [vars(b) if hasattr(b, '__dict__') else b for b in ejb_result.get('message_driven_beans', [])]
            result.timers = [vars(t) if hasattr(t, '__dict__') else t for t in ejb_result.get('timers', [])]

        except Exception as e:
            result.errors.append(f"Parse error: {e}")

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Jakarta EE specs are used."""
        detected = []
        for name, pattern in self._compiled_patterns.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """Detect Jakarta EE / Java EE version."""
        has_jakarta = bool(re.search(r'import\s+jakarta\.', content))
        has_javax = bool(re.search(r'import\s+javax\.(?:enterprise|ejb|servlet|persistence|ws\.rs)', content))

        if has_jakarta:
            # Jakarta EE 10+ uses jakarta.* across all specs
            if re.search(r'import\s+jakarta\.enterprise\.concurrent', content):
                return 'Jakarta EE 10+'
            return 'Jakarta EE 9+'

        if has_javax:
            # Differentiate Java EE versions
            if re.search(r'import\s+javax\.json\.bind', content):
                return 'Java EE 8'
            if re.search(r'import\s+javax\.enterprise\.concurrent', content):
                return 'Java EE 7'
            if re.search(r'import\s+javax\.enterprise\.context', content):
                return 'Java EE 6+'
            return 'Java EE 5'

        return ''
