"""
Tests for JavaModelExtractor — JPA entities, columns, relationships, repositories, Panache.

Part of CodeTrellis v4.12 Java Language Support.
"""

import pytest
from codetrellis.extractors.java.model_extractor import JavaModelExtractor


@pytest.fixture
def extractor():
    return JavaModelExtractor()


# ===== JPA ENTITY EXTRACTION =====

class TestEntityExtraction:
    """Tests for JPA entity extraction."""

    def test_simple_entity(self, extractor):
        code = '''
        @Entity
        public class User {
            @Id
            private Long id;

            private String name;
        }
        '''
        result = extractor.extract(code, "User.java")
        assert len(result["entities"]) == 1
        entity = result["entities"][0]
        assert entity.name == "User"

    def test_entity_with_table_name(self, extractor):
        code = '''
        @Entity
        @Table(name = "users")
        public class User {
            @Id
            private Long id;
        }
        '''
        result = extractor.extract(code, "User.java")
        entity = result["entities"][0]
        assert entity.table_name == "users"

    def test_entity_columns(self, extractor):
        code = '''
        @Entity
        @Table(name = "users")
        public class User {
            @Id
            @GeneratedValue(strategy = GenerationType.IDENTITY)
            private Long id;

            @Column(nullable = false, unique = true)
            private String username;

            @Column(nullable = false)
            private String email;

            private String optionalField;
        }
        '''
        result = extractor.extract(code, "User.java")
        entity = result["entities"][0]
        assert len(entity.columns) >= 3

        # Check column properties
        col_by_name = {c.name: c for c in entity.columns}
        if "username" in col_by_name:
            assert col_by_name["username"].is_nullable is False
            assert col_by_name["username"].is_unique is True
        if "email" in col_by_name:
            assert col_by_name["email"].is_nullable is False

    def test_entity_relationships(self, extractor):
        code = '''
        @Entity
        public class Order {
            @Id
            private Long id;

            @ManyToOne
            private Customer customer;

            @OneToMany(mappedBy = "order")
            private List<OrderItem> items;
        }
        '''
        result = extractor.extract(code, "Order.java")
        entity = result["entities"][0]
        assert len(entity.relationships) >= 1

    def test_entity_annotations(self, extractor):
        code = '''
        @Entity
        @Table(name = "products")
        public class Product {
            @Id
            private Long id;
            private String name;
        }
        '''
        result = extractor.extract(code, "Product.java")
        entity = result["entities"][0]
        assert "Entity" in entity.annotations


# ===== PANACHE ENTITY DETECTION =====

class TestPanacheEntityExtraction:
    """Tests for Quarkus Panache entity detection."""

    def test_panache_entity(self, extractor):
        code = '''
        @Entity
        public class Fruit extends PanacheEntity {
            public String name;
            public String color;
        }
        '''
        result = extractor.extract(code, "Fruit.java")
        assert len(result["entities"]) >= 1
        # Panache entities should be detected
        entity_names = [e.name for e in result["entities"]]
        assert "Fruit" in entity_names

    def test_panache_entity_base(self, extractor):
        code = '''
        @Entity
        public class Person extends PanacheEntityBase {
            @Id
            public Long id;
            public String name;
        }
        '''
        result = extractor.extract(code, "Person.java")
        entity_names = [e.name for e in result["entities"]]
        assert "Person" in entity_names


# ===== REPOSITORY EXTRACTION =====

class TestRepositoryExtraction:
    """Tests for Spring Data repository extraction."""

    def test_simple_repository(self, extractor):
        code = '''
        public interface UserRepository extends JpaRepository<User, Long> {
            Optional<User> findByEmail(String email);
            List<User> findByNameContaining(String name);
        }
        '''
        result = extractor.extract(code, "UserRepository.java")
        assert len(result["repositories"]) == 1
        repo = result["repositories"][0]
        assert repo.name == "UserRepository"
        assert repo.entity_type == "User"
        assert repo.base_interface == "JpaRepository"

    def test_crud_repository(self, extractor):
        code = '''
        public interface ItemRepository extends CrudRepository<Item, Integer> {
        }
        '''
        result = extractor.extract(code, "ItemRepository.java")
        assert len(result["repositories"]) == 1
        repo = result["repositories"][0]
        assert repo.entity_type == "Item"
        assert repo.base_interface == "CrudRepository"

    def test_repository_custom_methods(self, extractor):
        code = '''
        public interface OrderRepository extends JpaRepository<Order, Long> {
            List<Order> findByStatus(String status);
            @Query("SELECT o FROM Order o WHERE o.total > :amount")
            List<Order> findExpensiveOrders(@Param("amount") Double amount);
        }
        '''
        result = extractor.extract(code, "OrderRepository.java")
        repo = result["repositories"][0]
        assert len(repo.custom_methods) >= 1


# ===== NO MODELS =====

class TestNoModels:
    """Tests for files that should NOT produce entities/repositories."""

    def test_plain_class_no_entity(self, extractor):
        code = '''
        public class UserService {
            public User findById(Long id) { return null; }
        }
        '''
        result = extractor.extract(code, "UserService.java")
        assert len(result["entities"]) == 0
        assert len(result["repositories"]) == 0

    def test_interface_no_repository(self, extractor):
        """Interface without JpaRepository/CrudRepository should not be a repository."""
        code = '''
        public interface UserService {
            User findById(Long id);
        }
        '''
        result = extractor.extract(code, "UserService.java")
        assert len(result["repositories"]) == 0
