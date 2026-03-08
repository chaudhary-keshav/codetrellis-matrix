"""Tests for Kotlin model extractor - JPA entities, repositories, Exposed, serialization, DTOs."""

import pytest
from codetrellis.extractors.kotlin.model_extractor import (
    KotlinModelExtractor, KotlinEntityInfo, KotlinRepositoryInfo,
    KotlinExposedTableInfo, KotlinSerializableInfo, KotlinDTOInfo,
)


@pytest.fixture
def extractor():
    return KotlinModelExtractor()


# ============================================
# JPA Entity Extraction
# ============================================

class TestJPAEntities:
    def test_simple_entity(self, extractor):
        code = '''
        import javax.persistence.*

        @Entity
        @Table(name = "users")
        data class User(
            @Id @GeneratedValue
            val id: Long = 0,
            @Column(nullable = false)
            val name: String,
            val email: String
        )
        '''
        result = extractor.extract(code, "User.kt")
        entities = result.get('entities', [])
        assert len(entities) >= 1
        entity = entities[0]
        assert entity.name == 'User'
        assert entity.table_name == 'users'

    def test_entity_with_jakarta(self, extractor):
        code = '''
        import jakarta.persistence.*

        @Entity
        data class Product(
            @Id @GeneratedValue(strategy = GenerationType.UUID)
            val id: String = "",
            val name: String,
            val price: Double
        )
        '''
        result = extractor.extract(code, "Product.kt")
        entities = result.get('entities', [])
        assert len(entities) >= 1
        assert entities[0].name == 'Product'

    def test_entity_relationships(self, extractor):
        code = '''
        @Entity
        data class Order(
            @Id val id: Long = 0,
            @ManyToOne
            val customer: Customer,
            @OneToMany(mappedBy = "order")
            val items: List<OrderItem> = emptyList()
        )
        '''
        result = extractor.extract(code, "Order.kt")
        entities = result.get('entities', [])
        assert len(entities) >= 1


# ============================================
# Repository Extraction
# ============================================

class TestRepositories:
    def test_spring_data_repository(self, extractor):
        code = '''
        import org.springframework.data.jpa.repository.JpaRepository

        interface UserRepository : JpaRepository<User, Long> {
            fun findByEmail(email: String): User?
            fun findByNameContaining(name: String): List<User>
        }
        '''
        result = extractor.extract(code, "UserRepository.kt")
        repos = result.get('repositories', [])
        assert len(repos) >= 1
        repo = repos[0]
        assert repo.name == 'UserRepository'

    def test_crud_repository(self, extractor):
        code = '''
        interface ProductRepository : CrudRepository<Product, Long> {
            fun findByCategory(category: String): List<Product>
        }
        '''
        result = extractor.extract(code, "ProductRepository.kt")
        repos = result.get('repositories', [])
        assert len(repos) >= 1


# ============================================
# Exposed Table Extraction
# ============================================

class TestExposedTables:
    def test_table_object(self, extractor):
        code = '''
        import org.jetbrains.exposed.sql.Table

        object Users : Table("users") {
            val id = integer("id").autoIncrement()
            val name = varchar("name", 50)
            val email = varchar("email", 255)
            override val primaryKey = PrimaryKey(id)
        }
        '''
        result = extractor.extract(code, "Tables.kt")
        tables = result.get('exposed_tables', [])
        assert len(tables) >= 1
        table = tables[0]
        assert table.name == 'Users'
        assert table.table_name == 'users'

    def test_id_table(self, extractor):
        code = '''
        import org.jetbrains.exposed.dao.id.IntIdTable

        object Products : IntIdTable("products") {
            val name = varchar("name", 100)
            val price = decimal("price", 10, 2)
            val categoryId = reference("category_id", Categories)
        }
        '''
        result = extractor.extract(code, "Tables.kt")
        tables = result.get('exposed_tables', [])
        assert len(tables) >= 1


# ============================================
# kotlinx.serialization Extraction
# ============================================

class TestSerializables:
    def test_serializable_class(self, extractor):
        code = '''
        import kotlinx.serialization.Serializable

        @Serializable
        data class UserResponse(
            val id: Long,
            val name: String,
            val email: String
        )
        '''
        result = extractor.extract(code, "UserResponse.kt")
        serializables = result.get('serializables', [])
        assert len(serializables) >= 1
        ser = serializables[0]
        assert ser.name == 'UserResponse'

    def test_serializable_with_custom_serializer(self, extractor):
        code = '''
        @Serializable(with = DateSerializer::class)
        data class Event(
            val name: String,
            val date: LocalDate
        )
        '''
        result = extractor.extract(code, "Event.kt")
        serializables = result.get('serializables', [])
        assert len(serializables) >= 1


# ============================================
# DTO Extraction
# ============================================

class TestDTOs:
    def test_dto_by_name(self, extractor):
        code = '''
        data class CreateUserDTO(
            val name: String,
            val email: String,
            val password: String
        )
        '''
        result = extractor.extract(code, "CreateUserDTO.kt")
        dtos = result.get('dtos', [])
        assert len(dtos) >= 1
        assert dtos[0].name == 'CreateUserDTO'

    def test_request_class(self, extractor):
        code = '''
        data class CreateOrderRequest(
            val items: List<OrderItemRequest>,
            val shippingAddress: Address
        )
        '''
        result = extractor.extract(code, "CreateOrderRequest.kt")
        dtos = result.get('dtos', [])
        assert len(dtos) >= 1

    def test_response_class(self, extractor):
        code = '''
        data class UserResponse(
            val id: Long,
            val name: String,
            val email: String
        )
        '''
        result = extractor.extract(code, "UserResponse.kt")
        # May appear in both serializables and DTOs depending on annotations
        dtos = result.get('dtos', [])
        assert isinstance(dtos, list)


# ============================================
# Edge Cases
# ============================================

class TestEdgeCases:
    def test_empty_content(self, extractor):
        result = extractor.extract("", "empty.kt")
        assert result.get('entities', []) == []
        assert result.get('repositories', []) == []
        assert result.get('exposed_tables', []) == []
        assert result.get('serializables', []) == []
        assert result.get('dtos', []) == []

    def test_no_models(self, extractor):
        code = '''
        fun main() {
            println("Hello, World!")
        }
        '''
        result = extractor.extract(code, "Main.kt")
        assert result.get('entities', []) == []
        assert result.get('repositories', []) == []

    def test_whitespace_only(self, extractor):
        result = extractor.extract("   \n\n  ", "blank.kt")
        assert result.get('entities', []) == []
