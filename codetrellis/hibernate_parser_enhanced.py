"""
EnhancedHibernateParser v1.0 - Comprehensive Hibernate/JPA parser.

Supports:
- Hibernate 3.x (classic XML mapping, Criteria API, HQL)
- Hibernate 4.x (JPA 2.0/2.1, ServiceRegistry, new bootstrap)
- Hibernate 5.x (JPA 2.2, improved Criteria, bytecode enhancement)
- Hibernate 6.x (Jakarta Persistence, HQL improvements, semantic queries)

Hibernate-specific extraction:
- Entities: @Entity, @Table, columns, relationships, inheritance strategies
- Sessions: SessionFactory, EntityManager, transaction management
- Queries: HQL, JPQL, Criteria API, native SQL, named queries
- Cache: L2 cache, query cache, cache regions, providers
- Listeners: Lifecycle callbacks, event listeners, interceptors, Envers

Framework detection (30+ Hibernate ecosystem patterns):
- Core: hibernate-core, hibernate-entitymanager
- Validation: hibernate-validator
- Search: hibernate-search
- Envers: hibernate-envers
- Reactive: hibernate-reactive
- Spatial: hibernate-spatial
- Cache: ehcache, infinispan, hazelcast, caffeine, redisson
- Spring Data JPA integration

Part of CodeTrellis v4.95 - Hibernate Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .extractors.hibernate import (
    HibernateEntityExtractor, HibernateEntityInfo,
    HibernateRelationshipInfo, HibernateEmbeddableInfo,
    HibernateSessionExtractor, HibernateSessionFactoryInfo,
    HibernateTransactionInfo,
    HibernateQueryExtractor, HibernateQueryInfo,
    HibernateCriteriaInfo, HibernateNamedQueryInfo,
    HibernateCacheExtractor, HibernateCacheRegionInfo,
    HibernateCacheConfigInfo,
    HibernateListenerExtractor, HibernateListenerInfo,
    HibernateCallbackInfo, HibernateInterceptorInfo,
)


@dataclass
class HibernateParseResult:
    """Complete parse result for a Hibernate file."""
    file_path: str
    file_type: str = "hibernate"

    # Entities
    entities: List[HibernateEntityInfo] = field(default_factory=list)
    relationships: List[HibernateRelationshipInfo] = field(default_factory=list)
    embeddables: List[HibernateEmbeddableInfo] = field(default_factory=list)

    # Sessions
    session_factories: List[HibernateSessionFactoryInfo] = field(default_factory=list)
    transactions: List[HibernateTransactionInfo] = field(default_factory=list)
    session_operations: List[str] = field(default_factory=list)
    has_stateless_session: bool = False
    flush_modes: List[str] = field(default_factory=list)

    # Queries
    queries: List[HibernateQueryInfo] = field(default_factory=list)
    criteria_queries: List[HibernateCriteriaInfo] = field(default_factory=list)
    named_queries: List[HibernateNamedQueryInfo] = field(default_factory=list)
    fetch_profiles: List[str] = field(default_factory=list)

    # Cache
    cache_regions: List[HibernateCacheRegionInfo] = field(default_factory=list)
    cache_config: Optional[HibernateCacheConfigInfo] = None

    # Listeners
    callbacks: List[HibernateCallbackInfo] = field(default_factory=list)
    listeners: List[HibernateListenerInfo] = field(default_factory=list)
    interceptors: List[HibernateInterceptorInfo] = field(default_factory=list)
    entity_listener_classes: List[str] = field(default_factory=list)
    has_envers: bool = False

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    hibernate_version: str = ""
    total_entities: int = 0
    total_queries: int = 0
    total_relationships: int = 0


class EnhancedHibernateParser:
    """
    Enhanced Hibernate parser using all extractors for comprehensive parsing.

    Runs AFTER the Java parser when Hibernate framework is detected.
    Extracts Hibernate-specific ORM semantics.

    Supports Hibernate 3.x through 6.x.
    """

    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'hibernate_core': re.compile(
            r'import\s+org\.hibernate\b|'
            r'import\s+javax\.persistence\b|'
            r'import\s+jakarta\.persistence\b|'
            r'SessionFactory|Session\s+session',
            re.MULTILINE
        ),
        'hibernate_entitymanager': re.compile(
            r'import\s+org\.hibernate\.jpa\b|'
            r'EntityManagerFactory|EntityManager\s+\w+',
            re.MULTILINE
        ),
        'jpa_annotations': re.compile(
            r'@Entity|@Table|@Column|@Id|@GeneratedValue|'
            r'@OneToMany|@ManyToOne|@ManyToMany|@OneToOne',
            re.MULTILINE
        ),

        # ── Validation ────────────────────────────────────────────
        'hibernate_validator': re.compile(
            r'import\s+org\.hibernate\.validator\b|'
            r'import\s+javax\.validation\b|'
            r'import\s+jakarta\.validation\b|'
            r'@NotNull|@NotBlank|@Size|@Min|@Max|@Email|@Pattern|@Valid',
            re.MULTILINE
        ),

        # ── Envers ────────────────────────────────────────────────
        'hibernate_envers': re.compile(
            r'import\s+org\.hibernate\.envers\b|'
            r'@Audited|@AuditTable|AuditReaderFactory',
            re.MULTILINE
        ),

        # ── Search ────────────────────────────────────────────────
        'hibernate_search': re.compile(
            r'import\s+org\.hibernate\.search\b|'
            r'@Indexed|@FullTextField|@KeywordField|'
            r'SearchSession|SearchResult',
            re.MULTILINE
        ),

        # ── Reactive ──────────────────────────────────────────────
        'hibernate_reactive': re.compile(
            r'import\s+org\.hibernate\.reactive\b|'
            r'Mutiny\.SessionFactory|Mutiny\.Session',
            re.MULTILINE
        ),

        # ── Spatial ───────────────────────────────────────────────
        'hibernate_spatial': re.compile(
            r'import\s+org\.hibernate\.spatial\b|'
            r'@Type\s*\(\s*type\s*=\s*["\']org\.hibernate\.spatial',
            re.MULTILINE
        ),

        # ── Cache providers ───────────────────────────────────────
        'ehcache': re.compile(
            r'import\s+(?:org\.ehcache|net\.sf\.ehcache)\b|'
            r'EhCacheRegionFactory',
            re.MULTILINE
        ),
        'infinispan_cache': re.compile(
            r'import\s+org\.infinispan\b|InfinispanRegionFactory',
            re.MULTILINE
        ),
        'hazelcast_cache': re.compile(
            r'import\s+com\.hazelcast\.hibernate\b|HazelcastCacheRegionFactory',
            re.MULTILINE
        ),
        'caffeine_cache': re.compile(
            r'import\s+com\.github\.benmanes\.caffeine\b',
            re.MULTILINE
        ),
        'redisson_cache': re.compile(
            r'import\s+org\.redisson\.hibernate\b|RedissonRegionFactory',
            re.MULTILINE
        ),

        # ── Spring Data JPA ───────────────────────────────────────
        'spring_data_jpa': re.compile(
            r'import\s+org\.springframework\.data\.jpa\b|'
            r'JpaRepository|CrudRepository|PagingAndSortingRepository|'
            r'@Repository|@Query|@Modifying',
            re.MULTILINE
        ),

        # ── Connection pools ──────────────────────────────────────
        'hikari': re.compile(
            r'import\s+com\.zaxxer\.hikari\b|HikariDataSource|HikariConfig',
            re.MULTILINE
        ),
        'c3p0': re.compile(
            r'import\s+com\.mchange\.v2\.c3p0\b|ComboPooledDataSource|'
            r'hibernate\.c3p0\.',
            re.MULTILINE
        ),

        # ── Flyway / Liquibase ────────────────────────────────────
        'flyway': re.compile(
            r'import\s+org\.flywaydb\b|Flyway\.configure\(',
            re.MULTILINE
        ),
        'liquibase': re.compile(
            r'import\s+liquibase\b|SpringLiquibase',
            re.MULTILINE
        ),

        # ── Jakarta Persistence ───────────────────────────────────
        'jakarta_persistence': re.compile(
            r'import\s+jakarta\.persistence\b',
            re.MULTILINE
        ),
    }

    VERSION_INDICATORS = {
        '6.x': re.compile(
            r'import\s+jakarta\.persistence\b|'
            r'org\.hibernate\.orm\b|'
            r'SemanticException'
        ),
        '5.x': re.compile(
            r'import\s+javax\.persistence\b.*import\s+org\.hibernate\b|'
            r'org\.hibernate\.boot\b|'
            r'MetadataSources|StandardServiceRegistryBuilder',
        ),
        '4.x': re.compile(
            r'ServiceRegistryBuilder|'
            r'org\.hibernate\.service\b|'
            r'hibernate\.cfg\.xml',
        ),
        '3.x': re.compile(
            r'org\.hibernate\.classic\b|'
            r'net\.sf\.hibernate\b|'
            r'HibernateException',
        ),
    }

    def __init__(self):
        """Initialize the enhanced Hibernate parser with all extractors."""
        self.entity_extractor = HibernateEntityExtractor()
        self.session_extractor = HibernateSessionExtractor()
        self.query_extractor = HibernateQueryExtractor()
        self.cache_extractor = HibernateCacheExtractor()
        self.listener_extractor = HibernateListenerExtractor()

    def is_hibernate_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file contains Hibernate/JPA code."""
        if not content:
            return False

        hibernate_patterns = [
            r'import\s+org\.hibernate\.',
            r'import\s+javax\.persistence\.',
            r'import\s+jakarta\.persistence\.',
            r'@Entity',
            r'@Table\s*\(',
            r'SessionFactory',
            r'EntityManager\s+\w+',
            r'@OneToMany|@ManyToOne|@ManyToMany|@OneToOne',
            r'@Cacheable',
            r'@Audited',
            r'CriteriaBuilder',
        ]
        for pattern in hibernate_patterns:
            if re.search(pattern, content):
                return True
        return False

    def parse(self, content: str, file_path: str = "") -> HibernateParseResult:
        """Parse Hibernate source code and extract all ORM information."""
        result = HibernateParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)
        result.hibernate_version = self._detect_version(content)

        # Run all extractors
        # Entities
        entity_result = self.entity_extractor.extract(content, file_path)
        result.entities = entity_result.get('entities', [])
        result.relationships = entity_result.get('relationships', [])
        result.embeddables = entity_result.get('embeddables', [])

        # Sessions
        session_result = self.session_extractor.extract(content, file_path)
        result.session_factories = session_result.get('session_factories', [])
        result.transactions = session_result.get('transactions', [])
        result.session_operations = session_result.get('session_operations', [])
        result.has_stateless_session = session_result.get('has_stateless_session', False)
        result.flush_modes = session_result.get('flush_modes', [])

        # Queries
        query_result = self.query_extractor.extract(content, file_path)
        result.queries = query_result.get('queries', [])
        result.criteria_queries = query_result.get('criteria_queries', [])
        result.named_queries = query_result.get('named_queries', [])
        result.fetch_profiles = query_result.get('fetch_profiles', [])

        # Cache
        cache_result = self.cache_extractor.extract(content, file_path)
        result.cache_regions = cache_result.get('cache_regions', [])
        result.cache_config = cache_result.get('cache_config', None)

        # Listeners
        listener_result = self.listener_extractor.extract(content, file_path)
        result.callbacks = listener_result.get('callbacks', [])
        result.listeners = listener_result.get('listeners', [])
        result.interceptors = listener_result.get('interceptors', [])
        result.entity_listener_classes = listener_result.get('entity_listener_classes', [])
        result.has_envers = listener_result.get('has_envers', False)

        # Compute totals
        result.total_entities = len(result.entities)
        result.total_queries = len(result.queries) + len(result.criteria_queries) + len(result.named_queries)
        result.total_relationships = len(result.relationships)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Hibernate ecosystem frameworks are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect Hibernate version from code patterns."""
        for version, pattern in self.VERSION_INDICATORS.items():
            if pattern.search(content):
                return version
        return ""
