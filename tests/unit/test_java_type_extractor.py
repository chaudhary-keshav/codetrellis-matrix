"""
Tests for JavaTypeExtractor — classes, interfaces, records, enums, annotation defs.

Part of CodeTrellis v4.12 Java Language Support.
"""

import pytest
from codetrellis.extractors.java.type_extractor import JavaTypeExtractor


@pytest.fixture
def extractor():
    return JavaTypeExtractor()


# ===== CLASS EXTRACTION =====

class TestClassExtraction:
    """Tests for Java class extraction."""

    def test_simple_public_class(self, extractor):
        code = '''
        package com.example;

        public class HelloWorld {
            private String name;
            public String getName() { return name; }
        }
        '''
        result = extractor.extract(code, "HelloWorld.java")
        assert len(result["classes"]) == 1
        cls = result["classes"][0]
        assert cls.name == "HelloWorld"
        assert cls.kind == "class"
        assert cls.is_exported is True

    def test_abstract_class(self, extractor):
        code = '''
        public abstract class BaseService {
            public abstract void execute();
        }
        '''
        result = extractor.extract(code, "BaseService.java")
        assert len(result["classes"]) == 1
        cls = result["classes"][0]
        assert cls.name == "BaseService"
        assert cls.kind == "abstract_class"
        assert cls.is_abstract is True

    def test_class_with_extends_and_implements(self, extractor):
        code = '''
        public class UserService extends BaseService implements Serializable, Comparable<UserService> {
            private String name;
        }
        '''
        result = extractor.extract(code, "UserService.java")
        cls = result["classes"][0]
        assert cls.extends is not None
        assert "BaseService" in cls.extends
        assert "Serializable" in cls.implements
        assert len(cls.implements) == 2

    def test_class_with_annotations(self, extractor):
        code = '''
        @Entity
        @Table(name = "users")
        public class User {
            @Id
            @GeneratedValue(strategy = GenerationType.IDENTITY)
            private Long id;

            @Column(nullable = false)
            private String name;
        }
        '''
        result = extractor.extract(code, "User.java")
        cls = result["classes"][0]
        assert "Entity" in cls.annotations
        assert any("Table" in a for a in cls.annotations)
        assert len(cls.fields) == 2

    def test_class_fields_with_annotations(self, extractor):
        code = '''
        public class User {
            @Id
            @GeneratedValue(strategy = GenerationType.IDENTITY)
            private Long id;

            @Column(nullable = false, unique = true)
            private String username;

            @Column(nullable = false)
            private String email;
        }
        '''
        result = extractor.extract(code, "User.java")
        cls = result["classes"][0]
        assert len(cls.fields) == 3
        # Check field names
        field_names = [f.name for f in cls.fields]
        assert "id" in field_names
        assert "username" in field_names
        assert "email" in field_names

    def test_class_with_generics(self, extractor):
        code = '''
        public class Repository<T extends Entity, ID extends Serializable> {
            private Map<ID, T> store;
        }
        '''
        result = extractor.extract(code, "Repository.java")
        cls = result["classes"][0]
        assert cls.generic_params is not None
        assert len(cls.generic_params) >= 1

    def test_sealed_class(self, extractor):
        code = '''
        public sealed class Shape permits Circle, Rectangle, Triangle {
            protected double area;
        }
        '''
        result = extractor.extract(code, "Shape.java")
        cls = result["classes"][0]
        assert cls.kind == "sealed_class"
        assert cls.is_sealed is True
        assert len(cls.permits) > 0

    def test_private_class_not_exported(self, extractor):
        code = '''
        class InternalHelper {
            void doWork() {}
        }
        '''
        result = extractor.extract(code, "InternalHelper.java")
        if result["classes"]:
            cls = result["classes"][0]
            assert cls.is_exported is False

    def test_spring_boot_application_class(self, extractor):
        code = '''
        @SpringBootApplication
        public class Application {
            public static void main(String[] args) {
                SpringApplication.run(Application.class, args);
            }
        }
        '''
        result = extractor.extract(code, "Application.java")
        cls = result["classes"][0]
        assert cls.name == "Application"
        assert "SpringBootApplication" in cls.annotations
        assert len(cls.fields) == 0  # No fields in Application class

    def test_class_methods_extracted(self, extractor):
        code = '''
        public class Calculator {
            public int add(int a, int b) { return a + b; }
            public int subtract(int a, int b) { return a - b; }
            private void reset() {}
        }
        '''
        result = extractor.extract(code, "Calculator.java")
        cls = result["classes"][0]
        assert "add" in cls.methods
        assert "subtract" in cls.methods

    def test_data_class_pattern(self, extractor):
        """Test a typical data class with fields, getters and setters."""
        code = '''
        public class User {
            private Long id;
            private String username;
            private String email;

            public Long getId() { return id; }
            public String getUsername() { return username; }
            public String getEmail() { return email; }
            public void setId(Long id) { this.id = id; }
            public void setUsername(String username) { this.username = username; }
            public void setEmail(String email) { this.email = email; }
        }
        '''
        result = extractor.extract(code, "User.java")
        cls = result["classes"][0]
        assert cls.name == "User"
        assert len(cls.fields) == 3
        assert len(cls.methods) >= 6

    def test_package_extraction(self, extractor):
        code = (
            "package com.example.demo.model;\n"
            "\n"
            "public class User {}\n"
        )
        result = extractor.extract(code, "User.java")
        assert result["package"] == "com.example.demo.model"

    def test_import_extraction(self, extractor):
        code = (
            "package com.example;\n"
            "\n"
            "import java.util.List;\n"
            "import java.util.Map;\n"
            "import org.springframework.stereotype.Service;\n"
            "\n"
            "public class MyService {}\n"
        )
        result = extractor.extract(code, "MyService.java")
        assert len(result["imports"]) == 3
        assert "java.util.List" in result["imports"]


# ===== INTERFACE EXTRACTION =====

class TestInterfaceExtraction:
    """Tests for Java interface extraction."""

    def test_simple_interface(self, extractor):
        code = '''
        public interface UserService {
            User findById(Long id);
            List<User> findAll();
        }
        '''
        result = extractor.extract(code, "UserService.java")
        assert len(result["interfaces"]) == 1
        iface = result["interfaces"][0]
        assert iface.name == "UserService"
        assert iface.is_exported is True

    def test_interface_with_extends(self, extractor):
        code = '''
        public interface AdminService extends UserService, AuditService {
            void promoteUser(Long userId);
        }
        '''
        result = extractor.extract(code, "AdminService.java")
        iface = result["interfaces"][0]
        assert len(iface.extends) > 0

    def test_functional_interface(self, extractor):
        code = '''
        @FunctionalInterface
        public interface Validator<T> {
            boolean validate(T input);
        }
        '''
        result = extractor.extract(code, "Validator.java")
        iface = result["interfaces"][0]
        assert iface.is_functional is True


# ===== RECORD EXTRACTION =====

class TestRecordExtraction:
    """Tests for Java 14+ record extraction."""

    def test_simple_record(self, extractor):
        code = '''
        public record Point(int x, int y) {}
        '''
        result = extractor.extract(code, "Point.java")
        assert len(result["records"]) == 1
        rec = result["records"][0]
        assert rec.name == "Point"
        assert len(rec.components) == 2
        # Components may be dicts (from AST) or dataclass objects
        comp_names = []
        for c in rec.components:
            if isinstance(c, dict):
                comp_names.append(c['name'])
            else:
                comp_names.append(c.name)
        assert "x" in comp_names
        assert "y" in comp_names

    def test_record_with_generics(self, extractor):
        code = '''
        public record Pair<A, B>(A first, B second) implements Serializable {}
        '''
        result = extractor.extract(code, "Pair.java")
        assert len(result["records"]) == 1
        rec = result["records"][0]
        assert rec.name == "Pair"
        assert len(rec.components) == 2

    def test_record_with_annotations(self, extractor):
        code = '''
        @JsonSerialize
        public record UserDTO(String name, String email) {}
        '''
        result = extractor.extract(code, "UserDTO.java")
        rec = result["records"][0]
        assert "JsonSerialize" in rec.annotations


# ===== ENUM EXTRACTION =====

class TestEnumExtraction:
    """Tests for Java enum extraction."""

    def test_simple_enum(self, extractor):
        code = '''
        public enum Color {
            RED, GREEN, BLUE
        }
        '''
        result = extractor.extract(code, "Color.java")
        assert len(result["classes"]) == 0  # enum should NOT also be a class
        # Enums are extracted via a separate method; check the type_extractor handles them

    def test_enum_with_fields(self, extractor):
        code = '''
        public enum Status {
            ACTIVE("Active"),
            INACTIVE("Inactive"),
            PENDING("Pending");

            private final String label;

            Status(String label) {
                this.label = label;
            }

            public String getLabel() {
                return label;
            }
        }
        '''
        result = extractor.extract(code, "Status.java")
        # Enum extraction is in the extractor
        # Verify it doesn't show up as a regular class
        class_names = [c.name for c in result["classes"]]
        assert "Status" not in class_names  # Should not be double-counted


# ===== ANNOTATION DEF EXTRACTION =====

class TestAnnotationDefExtraction:
    """Tests for Java annotation definition extraction."""

    def test_simple_annotation(self, extractor):
        code = '''
        @Retention(RetentionPolicy.RUNTIME)
        @Target(ElementType.TYPE)
        public @interface MyAnnotation {
            String value() default "";
        }
        '''
        result = extractor.extract(code, "MyAnnotation.java")
        assert len(result["annotation_defs"]) == 1
        ann = result["annotation_defs"][0]
        assert ann.name == "MyAnnotation"


# ===== MULTIPLE TYPES IN ONE FILE =====

class TestMultipleTypes:
    """Tests for files with multiple type definitions."""

    def test_class_and_interface_in_same_file(self, extractor):
        code = '''
        public interface Greeting {
            String greet();
        }

        public class HelloGreeting implements Greeting {
            public String greet() { return "Hello"; }
        }
        '''
        result = extractor.extract(code, "Greeting.java")
        assert len(result["interfaces"]) == 1
        assert len(result["classes"]) == 1

    def test_multiple_classes(self, extractor):
        """Application.java should NOT leak fields to User.java when parsed separately."""
        app_code = '''
        @SpringBootApplication
        public class Application {
            public static void main(String[] args) {
                SpringApplication.run(Application.class, args);
            }
        }
        '''
        user_code = '''
        @Entity
        public class User {
            private Long id;
            private String name;
        }
        '''
        app_result = extractor.extract(app_code, "Application.java")
        user_result = extractor.extract(user_code, "User.java")

        app_cls = app_result["classes"][0]
        user_cls = user_result["classes"][0]

        # Application should have no fields
        assert len(app_cls.fields) == 0
        # User should have its own fields
        assert len(user_cls.fields) == 2
        # No field leaking between classes
        user_field_names = [f.name for f in user_cls.fields]
        assert "id" in user_field_names
        assert "name" in user_field_names
