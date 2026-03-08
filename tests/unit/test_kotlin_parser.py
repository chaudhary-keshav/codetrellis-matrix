"""
Tests for EnhancedKotlinParser — full integration, framework detection, Ktor routes, features.

Part of CodeTrellis v4.12 Kotlin Language Support.
"""

import pytest
from codetrellis.kotlin_parser_enhanced import EnhancedKotlinParser, KotlinParseResult


@pytest.fixture
def parser():
    return EnhancedKotlinParser()


# ===== BASIC PARSE =====

class TestBasicParse:
    """Tests for basic parse functionality."""

    def test_empty_content(self, parser):
        result = parser.parse("", "Empty.kt")
        assert isinstance(result, KotlinParseResult)
        assert result.file_type == "kotlin"
        assert result.classes == []

    def test_package_extraction(self, parser):
        code = (
            "package com.example.demo\n"
            "\n"
            "class App\n"
        )
        result = parser.parse(code, "App.kt")
        assert result.package_name == "com.example.demo"

    def test_import_extraction(self, parser):
        code = (
            "package com.example\n"
            "import java.util.List\n"
            "import kotlinx.coroutines.launch\n"
            "\n"
            "class App\n"
        )
        result = parser.parse(code, "App.kt")
        assert "java.util.List" in result.imports
        assert "kotlinx.coroutines.launch" in result.imports


# ===== TYPE EXTRACTION VIA PARSER =====

class TestTypeExtraction:
    """Tests for type extraction through the full Kotlin parser."""

    def test_data_class(self, parser):
        code = '''
        package com.example
        data class User(val name: String, val email: String)
        '''
        result = parser.parse(code, "User.kt")
        assert len(result.classes) >= 1
        cls = result.classes[0]
        assert cls.name == "User"
        assert cls.is_data is True

    def test_object_declaration(self, parser):
        code = '''
        package com.example
        object AppConfig {
            val version: String = "1.0"
        }
        '''
        result = parser.parse(code, "AppConfig.kt")
        assert len(result.objects) >= 1
        assert result.objects[0].name == "AppConfig"

    def test_interface(self, parser):
        code = '''
        package com.example
        interface UserService {
            fun findAll(): List<User>
        }
        '''
        result = parser.parse(code, "UserService.kt")
        assert len(result.interfaces) >= 1
        assert result.interfaces[0].name == "UserService"

    def test_enum_class(self, parser):
        code = '''
        package com.example
        enum class Status {
            ACTIVE,
            INACTIVE
        }
        '''
        result = parser.parse(code, "Status.kt")
        assert len(result.enums) >= 1
        assert result.enums[0].name == "Status"


# ===== FUNCTION EXTRACTION =====

class TestFunctionExtraction:
    """Tests for function extraction through the full parser."""

    def test_suspend_function(self, parser):
        code = '''
        package com.example
        class DataSource {
            suspend fun fetchData(): List<String> = emptyList()
        }
        '''
        result = parser.parse(code, "DataSource.kt")
        suspend_fns = [f for f in result.functions if f.is_suspend]
        assert len(suspend_fns) >= 1

    def test_extension_function(self, parser):
        code = '''
        package com.example
        fun String.toSlug(): String = this.lowercase().replace(" ", "-")
        '''
        result = parser.parse(code, "Extensions.kt")
        ext_fns = [f for f in result.functions if f.is_extension]
        assert len(ext_fns) >= 1


# ===== FRAMEWORK DETECTION =====

class TestFrameworkDetection:
    """Tests for framework detection via imports."""

    def test_spring_boot(self, parser):
        code = '''
        import org.springframework.boot.autoconfigure.SpringBootApplication
        import org.springframework.boot.runApplication

        @SpringBootApplication
        class Application

        fun main(args: Array<String>) {
            runApplication<Application>(*args)
        }
        '''
        result = parser.parse(code, "Application.kt")
        assert "spring_boot" in result.detected_frameworks

    def test_ktor(self, parser):
        code = '''
        import io.ktor.server.application.*
        import io.ktor.server.routing.*

        fun Application.module() {
            routing {
                get("/hello") { call.respondText("Hello") }
            }
        }
        '''
        result = parser.parse(code, "App.kt")
        assert "ktor" in result.detected_frameworks

    def test_coroutines(self, parser):
        code = '''
        import kotlinx.coroutines.launch
        import kotlinx.coroutines.delay

        suspend fun doWork() {
            delay(1000)
        }
        '''
        result = parser.parse(code, "Worker.kt")
        assert "kotlinx_coroutines" in result.detected_frameworks

    def test_no_frameworks(self, parser):
        code = '''
        package com.example
        class Plain
        '''
        result = parser.parse(code, "Plain.kt")
        assert "spring_boot" not in result.detected_frameworks
        assert "ktor" not in result.detected_frameworks


# ===== KOTLIN FEATURE DETECTION =====

class TestFeatureDetection:
    """Tests for Kotlin-specific feature detection."""

    def test_coroutines_feature(self, parser):
        code = '''
        class Worker {
            suspend fun work() {}
        }
        '''
        result = parser.parse(code, "Worker.kt")
        assert "coroutines" in result.kotlin_features
        assert result.uses_coroutines is True

    def test_data_classes_feature(self, parser):
        code = '''
        data class Point(val x: Int, val y: Int)
        '''
        result = parser.parse(code, "Point.kt")
        assert "data_classes" in result.kotlin_features

    def test_sealed_classes_feature(self, parser):
        code = '''
        sealed class Result
        '''
        result = parser.parse(code, "Result.kt")
        assert "sealed_classes" in result.kotlin_features

    def test_flow_feature(self, parser):
        code = '''
        import kotlinx.coroutines.flow.*

        fun getData(): Flow<String> = flow {
            emit("data")
        }
        '''
        result = parser.parse(code, "DataFlow.kt")
        assert "flow" in result.kotlin_features

    def test_type_aliases_feature(self, parser):
        code = '''
        typealias StringMap = Map<String, String>
        '''
        result = parser.parse(code, "Aliases.kt")
        assert "type_aliases" in result.kotlin_features


# ===== KTOR ROUTES =====

class TestKtorRoutes:
    """Tests for Ktor route extraction."""

    def test_ktor_routes(self, parser):
        code = '''
        import io.ktor.server.routing.*

        fun Application.configureRouting() {
            routing {
                get("/api/users") {
                    call.respond(listOf<String>())
                }
                post("/api/users") {
                    call.respond("created")
                }
            }
        }
        '''
        result = parser.parse(code, "Routing.kt")
        assert len(result.endpoints) >= 2
        methods = []
        for ep in result.endpoints:
            if isinstance(ep, dict):
                methods.append(ep.get("method", ""))
            else:
                methods.append(getattr(ep, "method", ""))
        assert "GET" in methods
        assert "POST" in methods


# ===== JPA ENTITIES VIA KOTLIN =====

class TestJPAEntities:
    """Tests for JPA entity extraction from Kotlin code."""

    def test_kotlin_jpa_entity(self, parser):
        code = '''
        import jakarta.persistence.*

        @Entity
        @Table(name = "users")
        class User(
            @Id @GeneratedValue
            var id: Long = 0,
            var name: String = ""
        )
        '''
        result = parser.parse(code, "User.kt")
        assert len(result.entities) >= 1
        assert result.entities[0].name == "User"


# ===== LAMBDA COUNT =====

class TestLambdaCount:
    """Tests for lambda counting through the parser."""

    def test_lambda_count(self, parser):
        code = '''
        fun process(items: List<Int>) {
            items.filter { x -> x > 0 }
                 .map { x -> x * 2 }
                 .forEach { x -> println(x) }
        }
        '''
        result = parser.parse(code, "Processing.kt")
        assert result.lambda_count >= 3
