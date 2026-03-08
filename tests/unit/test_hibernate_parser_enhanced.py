"""
Tests for Hibernate extractors and EnhancedHibernateParser.

Part of CodeTrellis v4.95 Hibernate Framework Support.
Tests cover:
- Entity extraction (@Entity, @Table, @Column, relationships)
- Session extraction (SessionFactory, EntityManager, @Transactional)
- Query extraction (HQL/JPQL, Criteria API, @NamedQuery, native SQL)
- Cache extraction (@Cacheable, L2 cache providers)
- Listener extraction (@PrePersist, @PostLoad, Envers)
- Parser integration (framework detection, version detection, is_hibernate_file)
"""

import pytest
from codetrellis.hibernate_parser_enhanced import EnhancedHibernateParser, HibernateParseResult
from codetrellis.extractors.hibernate import (
    HibernateEntityExtractor,
    HibernateSessionExtractor,
    HibernateQueryExtractor,
    HibernateCacheExtractor,
    HibernateListenerExtractor,
)


@pytest.fixture
def parser():
    return EnhancedHibernateParser()


@pytest.fixture
def entity_extractor():
    return HibernateEntityExtractor()


@pytest.fixture
def session_extractor():
    return HibernateSessionExtractor()


@pytest.fixture
def query_extractor():
    return HibernateQueryExtractor()


@pytest.fixture
def cache_extractor():
    return HibernateCacheExtractor()


@pytest.fixture
def listener_extractor():
    return HibernateListenerExtractor()


class TestHibernateEntityExtractor:

    def test_extract_entity(self, entity_extractor):
        content = """
import javax.persistence.*;

@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "username", nullable = false, unique = true)
    private String username;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL)
    private List<Order> orders;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "department_id")
    private Department department;
}
"""
        result = entity_extractor.extract(content)
        assert len(result['entities']) > 0
        ent = result['entities'][0]
        assert ent.class_name == 'User'
        assert ent.table_name == 'users'

    def test_extract_relationships(self, entity_extractor):
        content = """
@Entity
public class Order {
    @ManyToOne
    private User user;

    @OneToMany
    private List<OrderItem> items;

    @ManyToMany
    private Set<Tag> tags;

    @OneToOne
    private Invoice invoice;
}
"""
        result = entity_extractor.extract(content)
        rels = result['relationships']
        assert len(rels) >= 4

    def test_extract_inheritance(self, entity_extractor):
        content = """
@Entity
@Inheritance(strategy = InheritanceType.SINGLE_TABLE)
@DiscriminatorColumn(name = "type")
public abstract class Vehicle {
    @Id
    private Long id;
}
"""
        result = entity_extractor.extract(content)
        assert len(result['entities']) > 0

    def test_empty_content(self, entity_extractor):
        result = entity_extractor.extract("")
        assert result['entities'] == []


class TestHibernateSessionExtractor:

    def test_extract_session_factory(self, session_extractor):
        content = """
SessionFactory sessionFactory = new Configuration().configure().buildSessionFactory();
Session session = sessionFactory.openSession();
Transaction tx = session.beginTransaction();
"""
        result = session_extractor.extract(content)
        assert len(result['session_factories']) > 0

    def test_extract_entity_manager(self, session_extractor):
        content = """
@PersistenceContext
private EntityManager entityManager;

EntityManagerFactory emf = Persistence.createEntityManagerFactory("myPU");
"""
        result = session_extractor.extract(content)
        assert len(result['session_factories']) > 0

    def test_extract_transactional(self, session_extractor):
        content = """
@Transactional
public void saveUser(User user) {
    entityManager.persist(user);
}

@Transactional(readOnly = true)
public User findUser(Long id) {
    return entityManager.find(User.class, id);
}
"""
        result = session_extractor.extract(content)
        assert len(result['transactions']) > 0


class TestHibernateQueryExtractor:

    def test_extract_hql_query(self, query_extractor):
        content = """
Query query = session.createQuery("FROM User u WHERE u.active = true");
session.createQuery("SELECT u FROM User u JOIN FETCH u.orders WHERE u.id = :id");
"""
        result = query_extractor.extract(content)
        assert len(result['queries']) > 0

    def test_extract_named_query(self, query_extractor):
        content = """
@NamedQuery(name = "User.findByEmail", query = "SELECT u FROM User u WHERE u.email = :email")
@NamedQueries({
    @NamedQuery(name = "User.findAll", query = "FROM User"),
    @NamedQuery(name = "User.findActive", query = "FROM User u WHERE u.active = true")
})
public class User {}
"""
        result = query_extractor.extract(content)
        assert len(result['named_queries']) > 0

    def test_extract_native_query(self, query_extractor):
        content = """
session.createNativeQuery("SELECT * FROM users WHERE created_at > :date");
entityManager.createNativeQuery("INSERT INTO audit_log (action) VALUES (?)", AuditLog.class);
"""
        result = query_extractor.extract(content)
        assert len(result['queries']) > 0

    def test_extract_criteria_api(self, query_extractor):
        content = """
CriteriaBuilder cb = entityManager.getCriteriaBuilder();
CriteriaQuery<User> cq = cb.createQuery(User.class);
Root<User> root = cq.from(User.class);
"""
        result = query_extractor.extract(content)
        assert len(result['criteria_queries']) > 0


class TestHibernateCacheExtractor:

    def test_extract_l2_cache(self, cache_extractor):
        content = """
@Entity
@javax.persistence.Cacheable
@org.hibernate.annotations.Cache(usage = CacheConcurrencyStrategy.READ_WRITE, region = "users")
public class User {}
"""
        result = cache_extractor.extract(content)
        assert len(result['cache_regions']) > 0

    def test_extract_cache_provider(self, cache_extractor):
        content = """
hibernate.cache.use_second_level_cache = true
hibernate.cache.region.factory_class = org.hibernate.cache.ehcache.EhCacheRegionFactory
"""
        result = cache_extractor.extract(content)
        assert result['cache_config'].cache_provider == 'ehcache'


class TestHibernateListenerExtractor:

    def test_extract_lifecycle_callbacks(self, listener_extractor):
        content = """
@Entity
public class User {
    @PrePersist
    public void prePersist() { this.createdAt = new Date(); }

    @PostLoad
    public void postLoad() { this.fullName = firstName + " " + lastName; }

    @PreUpdate
    public void preUpdate() { this.updatedAt = new Date(); }
}
"""
        result = listener_extractor.extract(content)
        assert len(result['callbacks']) > 0

    def test_extract_envers(self, listener_extractor):
        content = """
import org.hibernate.envers.Audited;

@Entity
@Audited
public class AuditedEntity {
    @Id
    private Long id;
}
"""
        result = listener_extractor.extract(content)
        assert len(result['callbacks']) > 0 or result.get('has_envers', False)


class TestEnhancedHibernateParser:

    def test_is_hibernate_file(self, parser):
        content = """
import javax.persistence.Entity;

@Entity
public class User {}
"""
        assert parser.is_hibernate_file(content) is True

    def test_is_not_hibernate_file(self, parser):
        content = """
import java.util.List;
public class Main {}
"""
        assert parser.is_hibernate_file(content) is False

    def test_detect_frameworks(self, parser):
        content = """
import javax.persistence.Entity;
import org.hibernate.Session;
import org.hibernate.envers.Audited;
"""
        frameworks = parser._detect_frameworks(content)
        assert 'hibernate_core' in frameworks or 'jpa_annotations' in frameworks

    def test_detect_version_6x(self, parser):
        content = """
implementation 'org.hibernate.orm:hibernate-core:6.4.0.Final'
"""
        version = parser._detect_version(content)
        assert '6.x' in version

    def test_parse_full(self, parser):
        content = """
import javax.persistence.*;
import org.hibernate.annotations.Cache;
import org.hibernate.annotations.CacheConcurrencyStrategy;

@Entity
@Table(name = "products")
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
@NamedQuery(name = "Product.findAll", query = "FROM Product")
public class Product {
    @Id
    @GeneratedValue
    private Long id;

    @Column(nullable = false)
    private String name;

    @ManyToOne
    private Category category;

    @PrePersist
    public void onCreate() { this.createdAt = new Date(); }
}
"""
        result = parser.parse(content)
        assert isinstance(result, HibernateParseResult)
        assert len(result.entities) > 0

    def test_parse_empty(self, parser):
        result = parser.parse("")
        assert isinstance(result, HibernateParseResult)
        assert result.entities == []
