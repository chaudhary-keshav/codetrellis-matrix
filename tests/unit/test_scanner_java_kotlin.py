"""
Tests for ProjectMatrix Java & Kotlin field population via parser integration.

Tests that EnhancedJavaParser and EnhancedKotlinParser results are correctly
converted to dict format for the ProjectMatrix dataclass fields.

Part of CodeTrellis v4.12 Java & Kotlin Language Support.
"""

import pytest
from dataclasses import asdict
from codetrellis.java_parser_enhanced import EnhancedJavaParser
from codetrellis.kotlin_parser_enhanced import EnhancedKotlinParser


@pytest.fixture
def java_parser():
    return EnhancedJavaParser()


@pytest.fixture
def kotlin_parser():
    return EnhancedKotlinParser()


# ===== JAVA PARSER -> DICT CONVERSION =====

class TestJavaParserToDict:
    """Tests that parser results can be serialized to dict for ProjectMatrix."""

    def test_class_to_dict(self, java_parser):
        code = '''
        package com.example;

        @Service
        public class UserService {
            private String name;
            public void process() {}
        }
        '''
        result = java_parser.parse(code, "UserService.java")
        assert len(result.classes) >= 1

        # Convert to dict (simulating what scanner does)
        cls = result.classes[0]
        cls_dict = {
            'name': cls.name,
            'kind': cls.kind,
            'is_exported': cls.is_exported,
            'fields': [asdict(f) for f in cls.fields] if cls.fields else [],
            'extends': cls.extends,
            'implements': cls.implements,
            'annotations': cls.annotations,
            'file': cls.file,
        }
        assert cls_dict['name'] == 'UserService'
        assert isinstance(cls_dict['fields'], list)
        assert isinstance(cls_dict['annotations'], list)

    def test_endpoint_to_dict(self, java_parser):
        code = (
            "import org.springframework.web.bind.annotation.*;\n"
            "\n"
            "@RestController\n"
            "@RequestMapping(\"/api/users\")\n"
            "public class UserController {\n"
            "    @GetMapping(\"/{id}\")\n"
            "    public String getUser(@PathVariable Long id) { return \"\"; }\n"
            "}\n"
        )
        result = java_parser.parse(code, "UserController.java")
        assert len(result.endpoints) >= 1

        ep = result.endpoints[0]
        ep_dict = {
            'method': ep.method,
            'path': ep.path,
            'handler': ep.handler_method,
            'framework': ep.framework,
            'file': ep.file,
        }
        assert ep_dict['method'] in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH')
        assert '/' in ep_dict['path']

    def test_entity_to_dict(self, java_parser):
        code = '''
        import jakarta.persistence.*;

        @Entity
        @Table(name = "products")
        public class Product {
            @Id
            private Long id;
            @Column(nullable = false)
            private String name;
        }
        '''
        result = java_parser.parse(code, "Product.java")
        assert len(result.entities) >= 1

        entity = result.entities[0]
        entity_dict = {
            'name': entity.name,
            'table_name': entity.table_name,
            'columns': [asdict(c) for c in entity.columns],
            'relationships': [asdict(r) for r in entity.relationships],
        }
        assert entity_dict['name'] == 'Product'
        assert entity_dict['table_name'] == 'products'
        assert len(entity_dict['columns']) >= 1

    def test_repository_to_dict(self, java_parser):
        code = '''
        import org.springframework.data.jpa.repository.JpaRepository;

        public interface ProductRepository extends JpaRepository<Product, Long> {
            Product findByName(String name);
        }
        '''
        result = java_parser.parse(code, "ProductRepository.java")
        assert len(result.repositories) >= 1

        repo = result.repositories[0]
        repo_dict = {
            'name': repo.name,
            'entity_type': repo.entity_type,
            'base_interface': repo.base_interface,
            'custom_methods': repo.custom_methods,
        }
        assert repo_dict['name'] == 'ProductRepository'
        assert repo_dict['entity_type'] == 'Product'

    def test_enum_to_dict(self, java_parser):
        code = '''
        public enum Priority {
            LOW, MEDIUM, HIGH;

            public int level() { return ordinal(); }
        }
        '''
        result = java_parser.parse(code, "Priority.java")
        assert len(result.enums) >= 1

        enum = result.enums[0]
        enum_dict = {
            'name': enum.name,
            'is_exported': enum.is_exported,
            'constants': [asdict(c) for c in enum.constants],
            'methods': enum.methods,
        }
        assert enum_dict['name'] == 'Priority'
        assert len(enum_dict['constants']) == 3


# ===== KOTLIN PARSER -> DICT CONVERSION =====

class TestKotlinParserToDict:
    """Tests that Kotlin parser results can be serialized to dict for ProjectMatrix."""

    def test_data_class_to_dict(self, kotlin_parser):
        code = '''
        package com.example
        data class User(val name: String, val email: String)
        '''
        result = kotlin_parser.parse(code, "User.kt")
        assert len(result.classes) >= 1

        cls = result.classes[0]
        cls_dict = {
            'name': cls.name,
            'kind': cls.kind,
            'is_exported': cls.is_exported,
            'is_data': cls.is_data,
            'primary_constructor': cls.primary_constructor_params,
            'extends': cls.extends,
            'implements': cls.implements,
            'annotations': cls.annotations,
            'file': cls.file,
        }
        assert cls_dict['name'] == 'User'
        assert cls_dict['kind'] == 'data_class'
        assert cls_dict['is_data'] is True

    def test_suspend_function_to_dict(self, kotlin_parser):
        code = '''
        package com.example
        suspend fun fetchData(): List<String> = emptyList()
        '''
        result = kotlin_parser.parse(code, "DataSource.kt")
        suspend_fns = [f for f in result.functions if f.is_suspend]
        assert len(suspend_fns) >= 1

        fn = suspend_fns[0]
        fn_dict = {
            'name': fn.name,
            'is_suspend': fn.is_suspend,
            'is_extension': fn.is_extension,
            'return_type': fn.return_type,
            'is_exported': fn.is_exported,
            'file': fn.file,
        }
        assert fn_dict['is_suspend'] is True
        assert fn_dict['name'] == 'fetchData'

    def test_object_to_dict(self, kotlin_parser):
        code = '''
        package com.example
        object Registry {
            val items: MutableList<String> = mutableListOf()
            fun register(item: String) { items.add(item) }
        }
        '''
        result = kotlin_parser.parse(code, "Registry.kt")
        assert len(result.objects) >= 1

        obj = result.objects[0]
        obj_dict = {
            'name': obj.name,
            'kind': obj.kind,
            'methods': obj.methods,
            'is_exported': obj.is_exported,
            'file': obj.file,
        }
        assert obj_dict['name'] == 'Registry'
        assert obj_dict['kind'] == 'object'

    def test_enum_to_dict(self, kotlin_parser):
        code = '''
        package com.example
        enum class Status {
            ACTIVE,
            INACTIVE
        }
        '''
        result = kotlin_parser.parse(code, "Status.kt")
        assert len(result.enums) >= 1

        enum = result.enums[0]
        enum_dict = {
            'name': enum.name,
            'entries': enum.entries,
            'is_exported': enum.is_exported,
            'file': enum.file,
        }
        assert enum_dict['name'] == 'Status'
        assert len(enum_dict['entries']) == 2


# ===== FULL PARSE ROUND-TRIP =====

class TestFullParseRoundTrip:
    """Tests that a full parse produces all expected field categories."""

    def test_java_full_parse_fields(self, java_parser):
        """Parse a Spring Boot controller and verify all result fields are populated."""
        code = (
            "package com.example.demo;\n"
            "\n"
            "import org.springframework.boot.SpringApplication;\n"
            "import org.springframework.boot.autoconfigure.SpringBootApplication;\n"
            "import org.springframework.web.bind.annotation.*;\n"
            "import jakarta.persistence.*;\n"
            "\n"
            "@SpringBootApplication\n"
            "public class DemoApplication {\n"
            "    public static void main(String[] args) {\n"
            "        SpringApplication.run(DemoApplication.class, args);\n"
            "    }\n"
            "}\n"
        )
        result = java_parser.parse(code, "DemoApplication.java")
        assert result.package_name == "com.example.demo"
        assert len(result.imports) >= 3
        assert "spring_boot" in result.detected_frameworks
        assert len(result.classes) >= 1

    def test_kotlin_full_parse_fields(self, kotlin_parser):
        """Parse a Kotlin file with multiple elements and verify completeness."""
        code = (
            "package com.example\n"
            "\n"
            "import kotlinx.coroutines.flow.*\n"
            "\n"
            "data class User(val name: String, val age: Int)\n"
            "\n"
            "sealed interface UiState {\n"
            "    object Loading : UiState\n"
            "    data class Success(val users: List<User>) : UiState\n"
            "}\n"
            "\n"
            "enum class Status {\n"
            "    ACTIVE, INACTIVE\n"
            "}\n"
            "\n"
            "object UserCache {\n"
            "    val cache: MutableMap<String, User> = mutableMapOf()\n"
            "}\n"
            "\n"
            "suspend fun fetchUsers(): Flow<User> = flow { }\n"
            "\n"
            "typealias UserList = List<User>\n"
        )
        result = kotlin_parser.parse(code, "Models.kt")
        assert result.package_name == "com.example"
        assert len(result.classes) >= 1  # User, Success
        assert len(result.interfaces) >= 1  # UiState
        assert len(result.enums) >= 1  # Status
        assert len(result.objects) >= 1  # UserCache (Loading is inner companion)
        assert result.uses_coroutines is True or "coroutines" in result.kotlin_features
        assert "flow" in result.kotlin_features
        assert len(result.type_aliases) >= 1
