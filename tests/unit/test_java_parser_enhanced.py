"""
Tests for EnhancedJavaParser — full integration parse, framework detection, AST, version features.

Part of CodeTrellis v4.12 Java Language Support.
"""

import pytest
from codetrellis.java_parser_enhanced import EnhancedJavaParser, JavaParseResult


@pytest.fixture
def parser():
    return EnhancedJavaParser()


# ===== BASIC PARSE =====

class TestBasicParse:
    """Tests for basic parse functionality."""

    def test_empty_content(self, parser):
        result = parser.parse("", "Empty.java")
        assert isinstance(result, JavaParseResult)
        assert result.file_type == "java"
        assert result.classes == []

    def test_package_extraction(self, parser):
        code = (
            "package com.example.demo;\n"
            "\n"
            "public class App {}\n"
        )
        result = parser.parse(code, "App.java")
        assert result.package_name == "com.example.demo"

    def test_import_extraction(self, parser):
        code = (
            "package com.example;\n"
            "import java.util.List;\n"
            "import java.util.Map;\n"
            "import static java.lang.Math.PI;\n"
            "\n"
            "public class App {}\n"
        )
        result = parser.parse(code, "App.java")
        assert "java.util.List" in result.imports
        assert "java.util.Map" in result.imports
        # static imports
        assert any("Math.PI" in i for i in result.imports)


# ===== TYPE EXTRACTION VIA PARSER =====

class TestTypeExtraction:
    """Tests for type extraction through the full parser."""

    def test_class_extraction(self, parser):
        code = '''
        package com.example;

        public class UserService {
            private String name;
            public void process() {}
        }
        '''
        result = parser.parse(code, "UserService.java")
        assert len(result.classes) >= 1
        assert result.classes[0].name == "UserService"

    def test_interface_extraction(self, parser):
        code = '''
        package com.example;

        public interface UserRepository {
            void save();
            void findById();
        }
        '''
        result = parser.parse(code, "UserRepository.java")
        assert len(result.interfaces) >= 1
        assert result.interfaces[0].name == "UserRepository"

    def test_enum_extraction(self, parser):
        code = '''
        package com.example;

        public enum Status {
            ACTIVE, INACTIVE, PENDING;
        }
        '''
        result = parser.parse(code, "Status.java")
        assert len(result.enums) >= 1
        assert result.enums[0].name == "Status"
        assert len(result.enums[0].constants) == 3

    def test_record_extraction(self, parser):
        code = '''
        package com.example;

        public record Point(int x, int y) {}
        '''
        result = parser.parse(code, "Point.java")
        assert len(result.records) >= 1
        assert result.records[0].name == "Point"

    def test_annotation_def_extraction(self, parser):
        code = '''
        package com.example;

        import java.lang.annotation.*;

        @Retention(RetentionPolicy.RUNTIME)
        @Target(ElementType.TYPE)
        public @interface MyAnnotation {
            String value() default "";
        }
        '''
        result = parser.parse(code, "MyAnnotation.java")
        assert len(result.annotation_defs) >= 1
        assert result.annotation_defs[0].name == "MyAnnotation"


# ===== FRAMEWORK DETECTION =====

class TestFrameworkDetection:
    """Tests for framework detection via imports."""

    def test_spring_boot(self, parser):
        code = '''
        package com.example;
        import org.springframework.boot.SpringApplication;
        import org.springframework.boot.autoconfigure.SpringBootApplication;

        @SpringBootApplication
        public class Application {
            public static void main(String[] args) {
                SpringApplication.run(Application.class, args);
            }
        }
        '''
        result = parser.parse(code, "Application.java")
        assert "spring_boot" in result.detected_frameworks

    def test_quarkus(self, parser):
        code = '''
        import io.quarkus.runtime.Quarkus;

        public class QuarkusApp {}
        '''
        result = parser.parse(code, "QuarkusApp.java")
        assert "quarkus" in result.detected_frameworks

    def test_micronaut(self, parser):
        code = '''
        import io.micronaut.runtime.Micronaut;

        public class MicronautApp {}
        '''
        result = parser.parse(code, "MicronautApp.java")
        assert "micronaut" in result.detected_frameworks

    def test_jpa(self, parser):
        code = '''
        import jakarta.persistence.Entity;
        import jakarta.persistence.Id;

        @Entity
        public class User {
            @Id
            private Long id;
        }
        '''
        result = parser.parse(code, "User.java")
        assert "jpa" in result.detected_frameworks or "jakarta" in result.detected_frameworks

    def test_junit5(self, parser):
        code = '''
        import org.junit.jupiter.api.Test;

        class AppTest {
            @Test
            void testSomething() {}
        }
        '''
        result = parser.parse(code, "AppTest.java")
        assert "junit5" in result.detected_frameworks

    def test_lombok(self, parser):
        code = '''
        import lombok.Data;
        import lombok.Builder;

        @Data
        @Builder
        public class UserDTO {}
        '''
        result = parser.parse(code, "UserDTO.java")
        assert "lombok" in result.detected_frameworks

    def test_multiple_frameworks(self, parser):
        code = '''
        import org.springframework.boot.SpringApplication;
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.data.jpa.repository.JpaRepository;
        import lombok.Data;

        @Data
        public class App {}
        '''
        result = parser.parse(code, "App.java")
        assert "spring_boot" in result.detected_frameworks
        assert "spring_mvc" in result.detected_frameworks
        assert "spring_data" in result.detected_frameworks
        assert "lombok" in result.detected_frameworks

    def test_no_frameworks(self, parser):
        code = '''
        import java.util.List;

        public class PlainApp {}
        '''
        result = parser.parse(code, "PlainApp.java")
        # Should have no major framework detected
        assert "spring_boot" not in result.detected_frameworks
        assert "quarkus" not in result.detected_frameworks


# ===== JAVA VERSION FEATURES =====

class TestVersionFeatures:
    """Tests for Java version feature detection."""

    def test_record_feature(self, parser):
        code = '''
        public record Point(int x, int y) {}
        '''
        result = parser.parse(code, "Point.java")
        assert "records" in result.java_version_features

    def test_sealed_class_feature(self, parser):
        code = '''
        public sealed class Shape permits Circle, Rectangle {}
        '''
        result = parser.parse(code, "Shape.java")
        assert "sealed_classes" in result.java_version_features

    def test_text_blocks(self, parser):
        code = '''
        public class App {
            String sql = \"""
                SELECT * FROM users
                WHERE active = true
            \""";
        }
        '''
        result = parser.parse(code, "App.java")
        assert "text_blocks" in result.java_version_features

    def test_var_keyword(self, parser):
        code = '''
        public class App {
            void test() {
                var list = new ArrayList<>();
            }
        }
        '''
        result = parser.parse(code, "App.java")
        assert "var_keyword" in result.java_version_features


# ===== ENDPOINT EXTRACTION VIA PARSER =====

class TestEndpointExtraction:
    """Tests for endpoint extraction through the full parser."""

    def test_spring_endpoints(self, parser):
        code = '''
        package com.example;
        import org.springframework.web.bind.annotation.*;

        @RestController
        @RequestMapping("/api/users")
        public class UserController {
            @GetMapping("/{id}")
            public User getUser(@PathVariable Long id) { return null; }

            @PostMapping
            public User createUser(@RequestBody User user) { return null; }
        }
        '''
        result = parser.parse(code, "UserController.java")
        assert len(result.endpoints) >= 2


# ===== ENTITY EXTRACTION VIA PARSER =====

class TestEntityExtraction:
    """Tests for JPA entity extraction through the full parser."""

    def test_jpa_entity(self, parser):
        code = '''
        package com.example;
        import jakarta.persistence.*;

        @Entity
        @Table(name = "users")
        public class User {
            @Id
            @GeneratedValue(strategy = GenerationType.IDENTITY)
            private Long id;
            private String name;
        }
        '''
        result = parser.parse(code, "User.java")
        assert len(result.entities) >= 1
        assert result.entities[0].name == "User"

    def test_repository(self, parser):
        code = '''
        package com.example;
        import org.springframework.data.jpa.repository.JpaRepository;

        public interface UserRepository extends JpaRepository<User, Long> {
            User findByEmail(String email);
        }
        '''
        result = parser.parse(code, "UserRepository.java")
        assert len(result.repositories) >= 1
        assert result.repositories[0].name == "UserRepository"


# ===== JAVADOC =====

class TestJavadoc:
    """Tests for file-level javadoc extraction."""

    def test_file_javadoc(self, parser):
        code = '''/**
 * Main application entry point for the demo service.
 */
package com.example;

public class App {}
'''
        result = parser.parse(code, "App.java")
        assert result.javadoc is not None
        assert "Main application" in result.javadoc

    def test_no_javadoc(self, parser):
        code = '''
        package com.example;
        public class App {}
        '''
        result = parser.parse(code, "App.java")
        # javadoc may be None
        # just ensure no crash
