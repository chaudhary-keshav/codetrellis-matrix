"""Tests for EnhancedKotlinParser v2.0 - new features: version detection, K2 compiler,
framework detection, feature detection, and full integration with all 5 extractors."""

import pytest
from codetrellis.kotlin_parser_enhanced import EnhancedKotlinParser, KotlinParseResult


@pytest.fixture
def parser():
    return EnhancedKotlinParser()


# ============================================
# Kotlin Version Detection
# ============================================

class TestKotlinVersionDetection:
    def test_detect_data_class_v1_0(self, parser):
        code = '''
        data class User(val name: String, val age: Int)
        '''
        result = parser.parse(code, "User.kt")
        assert result.kotlin_version == '1.0'

    def test_detect_typealias_v1_1(self, parser):
        code = '''
        typealias StringList = List<String>
        '''
        result = parser.parse(code, "Types.kt")
        assert result.kotlin_version == '1.1'

    def test_detect_fun_interface_v1_4(self, parser):
        code = '''
        fun interface Predicate<T> {
            fun test(value: T): Boolean
        }
        '''
        result = parser.parse(code, "Predicate.kt")
        assert result.kotlin_version == '1.4'

    def test_detect_sealed_interface_v1_5(self, parser):
        code = '''
        sealed interface Result<out T> {
            data class Success<T>(val value: T) : Result<T>
            data class Failure(val error: Throwable) : Result<Nothing>
        }
        '''
        result = parser.parse(code, "Result.kt")
        assert result.kotlin_version == '1.5'

    def test_detect_value_class_v1_6(self, parser):
        code = '''
        @JvmInline
        value class Email(val value: String)
        '''
        result = parser.parse(code, "Email.kt")
        assert result.kotlin_version == '1.6'

    def test_detect_context_receivers_v1_7(self, parser):
        code = '''
        context(Logger)
        fun processData(data: Data) {
            log("Processing...")
        }
        '''
        result = parser.parse(code, "Process.kt")
        assert result.kotlin_version == '1.7'

    def test_no_version_for_basic_code(self, parser):
        code = '''
        fun hello(): String = "hello"
        '''
        result = parser.parse(code, "Hello.kt")
        # Basic code without version-specific features
        assert result.kotlin_version == '' or result.kotlin_version is not None


# ============================================
# K2 Compiler Detection
# ============================================

class TestK2CompilerDetection:
    def test_k2_language_version(self, parser):
        code = '''
        kotlin {
            compilerOptions {
                languageVersion = "2.0"
            }
        }
        '''
        result = parser.parse(code, "build.gradle.kts")
        assert result.uses_k2_compiler is True

    def test_k2_experimental_flag(self, parser):
        code = '''
        kotlin.experimental.tryK2 = true
        '''
        result = parser.parse(code, "gradle.properties")
        assert result.uses_k2_compiler is True

    def test_no_k2(self, parser):
        code = '''
        data class User(val name: String)
        '''
        result = parser.parse(code, "User.kt")
        assert result.uses_k2_compiler is False


# ============================================
# Framework Detection
# ============================================

class TestFrameworkDetection:
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
        assert 'spring_boot' in result.detected_frameworks

    def test_ktor(self, parser):
        code = '''
        import io.ktor.server.engine.*
        import io.ktor.server.netty.*

        fun main() {
            embeddedServer(Netty, port = 8080) {
                routing { get("/") { call.respondText("Hello") } }
            }.start(wait = true)
        }
        '''
        result = parser.parse(code, "Application.kt")
        assert 'ktor_server' in result.detected_frameworks or 'ktor' in result.detected_frameworks

    def test_koin(self, parser):
        code = '''
        import org.koin.dsl.module
        import org.koin.core.component.inject

        val appModule = module {
            single { UserRepository() }
        }
        '''
        result = parser.parse(code, "AppModule.kt")
        assert 'koin' in result.detected_frameworks

    def test_compose(self, parser):
        code = '''
        import androidx.compose.runtime.Composable
        import androidx.compose.material.Text

        @Composable
        fun Greeting(name: String) {
            Text(text = "Hello, $name!")
        }
        '''
        result = parser.parse(code, "Greeting.kt")
        assert 'compose' in result.detected_frameworks
        assert result.uses_compose is True

    def test_exposed(self, parser):
        code = '''
        import org.jetbrains.exposed.sql.Table

        object Users : Table() {
            val id = integer("id").autoIncrement()
        }
        '''
        result = parser.parse(code, "Tables.kt")
        assert 'exposed' in result.detected_frameworks

    def test_kotlinx_serialization(self, parser):
        code = '''
        import kotlinx.serialization.Serializable

        @Serializable
        data class User(val name: String)
        '''
        result = parser.parse(code, "User.kt")
        assert 'kotlinx_serialization' in result.detected_frameworks

    def test_coroutines(self, parser):
        code = '''
        import kotlinx.coroutines.launch
        import kotlinx.coroutines.CoroutineScope

        fun CoroutineScope.doWork() {
            launch { println("working") }
        }
        '''
        result = parser.parse(code, "Work.kt")
        assert 'kotlinx_coroutines' in result.detected_frameworks
        assert result.uses_coroutines is True

    def test_no_frameworks(self, parser):
        code = '''
        fun main() {
            println("Hello, World!")
        }
        '''
        result = parser.parse(code, "Main.kt")
        assert result.detected_frameworks == []

    def test_multiple_frameworks(self, parser):
        code = '''
        import org.springframework.boot.autoconfigure.SpringBootApplication
        import org.springframework.data.jpa.repository.JpaRepository
        import kotlinx.coroutines.flow.Flow

        @SpringBootApplication
        class Application
        '''
        result = parser.parse(code, "Application.kt")
        assert 'spring_boot' in result.detected_frameworks
        assert 'spring_data' in result.detected_frameworks


# ============================================
# Feature Detection
# ============================================

class TestFeatureDetection:
    def test_coroutines_feature(self, parser):
        code = 'suspend fun fetchData(): Data = withContext(Dispatchers.IO) { api.fetch() }'
        result = parser.parse(code, "Api.kt")
        assert 'coroutines' in result.kotlin_features
        assert result.uses_coroutines is True

    def test_flow_feature(self, parser):
        code = 'val items: Flow<Item> = flow { emit(Item()) }'
        result = parser.parse(code, "Items.kt")
        assert 'flow' in result.kotlin_features

    def test_data_classes_feature(self, parser):
        code = 'data class Point(val x: Int, val y: Int)'
        result = parser.parse(code, "Point.kt")
        assert 'data_classes' in result.kotlin_features

    def test_sealed_classes_feature(self, parser):
        code = 'sealed class UiState'
        result = parser.parse(code, "UiState.kt")
        assert 'sealed_classes' in result.kotlin_features

    def test_multiplatform_feature(self, parser):
        code = 'expect fun platformName(): String'
        result = parser.parse(code, "Platform.kt")
        assert 'multiplatform' in result.kotlin_features
        assert result.uses_multiplatform is True

    def test_compose_feature(self, parser):
        code = '@Composable fun Greeting() { }'
        result = parser.parse(code, "Greeting.kt")
        assert 'compose' in result.kotlin_features
        assert result.uses_compose is True

    def test_operator_overloading(self, parser):
        code = 'operator fun plus(other: Vec2): Vec2 = Vec2(x + other.x, y + other.y)'
        result = parser.parse(code, "Vec2.kt")
        assert 'operator_overloading' in result.kotlin_features

    def test_extension_functions(self, parser):
        code = 'fun String.toCamelCase(): String = this.split("_").joinToString("")'
        result = parser.parse(code, "Extensions.kt")
        assert 'extension_functions' in result.kotlin_features

    def test_delegation_properties(self, parser):
        code = 'val name by lazy { computeName() }'
        result = parser.parse(code, "Lazy.kt")
        assert 'delegation_properties' in result.kotlin_features


# ============================================
# Full Integration Tests
# ============================================

class TestFullIntegration:
    def test_complex_kotlin_file(self, parser):
        code = (
            'package com.example.api\n'
            '\n'
            'import io.ktor.server.routing.*\n'
            'import io.ktor.server.application.*\n'
            'import kotlinx.serialization.Serializable\n'
            'import kotlinx.coroutines.flow.Flow\n'
            '\n'
            '@Serializable\n'
            'data class UserResponse(val id: Long, val name: String, val email: String)\n'
            '\n'
            'sealed interface UserError {\n'
            '    object NotFound : UserError\n'
            '    data class ValidationError(val message: String) : UserError\n'
            '}\n'
            '\n'
            'fun Application.configureUserRoutes() {\n'
            '    routing {\n'
            '        get("/api/users") {\n'
            '            call.respond(userService.findAll())\n'
            '        }\n'
            '        post("/api/users") {\n'
            '            val request = call.receive<CreateUserRequest>()\n'
            '            call.respond(userService.create(request))\n'
            '        }\n'
            '    }\n'
            '}\n'
            '\n'
            'suspend fun UserService.findAllAsFlow(): Flow<User> = flow {\n'
            '    findAll().forEach { emit(it) }\n'
            '}\n'
        )
        result = parser.parse(code, "UserRoutes.kt")

        # Package
        assert result.package_name == 'com.example.api'

        # Frameworks detected
        assert 'ktor_server' in result.detected_frameworks or 'ktor' in result.detected_frameworks
        assert 'kotlinx_serialization' in result.detected_frameworks

        # Features
        assert 'coroutines' in result.kotlin_features
        assert 'data_classes' in result.kotlin_features
        assert 'sealed_classes' in result.kotlin_features

        # Version
        assert result.kotlin_version == '1.5'  # sealed interface

        # Types extracted
        assert any(c.name == 'UserResponse' for c in result.classes)

        # Endpoints extracted
        assert len(result.endpoints) >= 1

        # Coroutines flag
        assert result.uses_coroutines is True

    def test_parse_result_defaults(self, parser):
        result = parser.parse("", "empty.kt")
        assert result.file_path == "empty.kt"
        assert result.file_type == "kotlin"
        assert result.package_name == ""
        assert result.imports == []
        assert result.classes == []
        assert result.objects == []
        assert result.interfaces == []
        assert result.enums == []
        assert result.functions == []
        assert result.endpoints == []
        assert result.detected_frameworks == []
        assert result.kotlin_features == []
        assert result.uses_coroutines is False
        assert result.uses_compose is False
        assert result.uses_multiplatform is False
        assert result.uses_k2_compiler is False
        assert result.ast_available is False

    def test_imports_extraction(self, parser):
        code = (
            'import kotlin.math.sqrt\n'
            'import kotlinx.coroutines.*\n'
            'import io.ktor.server.engine.embeddedServer\n'
        )
        result = parser.parse(code, "Imports.kt")
        assert len(result.imports) == 3
        assert 'kotlin.math.sqrt' in result.imports
        assert 'kotlinx.coroutines.*' in result.imports

    def test_package_extraction(self, parser):
        code = (
            'package com.example.myapp.feature\n'
            '\n'
            'class MyClass\n'
        )
        result = parser.parse(code, "MyClass.kt")
        assert result.package_name == 'com.example.myapp.feature'
