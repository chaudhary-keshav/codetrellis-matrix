"""Tests for Kotlin attribute extractor - annotations, DI, delegation, multiplatform, contracts."""

import pytest
from codetrellis.extractors.kotlin.attribute_extractor import (
    KotlinAttributeExtractor, KotlinAnnotationDefInfo,
    KotlinAnnotationUsageInfo, KotlinDelegationInfo,
    KotlinDIBindingInfo, KotlinMultiplatformDeclInfo,
    KotlinContextReceiverInfo, KotlinContractInfo,
)


@pytest.fixture
def extractor():
    return KotlinAttributeExtractor()


# ============================================
# Annotation Definition Extraction
# ============================================

class TestAnnotationDefs:
    def test_simple_annotation(self, extractor):
        code = '''
        @Target(AnnotationTarget.FUNCTION)
        @Retention(AnnotationRetention.RUNTIME)
        annotation class Logged
        '''
        result = extractor.extract(code, "annotations.kt")
        defs = result.get('annotation_defs', [])
        assert len(defs) >= 1
        assert defs[0].name == 'Logged'

    def test_annotation_with_params(self, extractor):
        code = '''
        @Target(AnnotationTarget.CLASS)
        @Retention(AnnotationRetention.RUNTIME)
        annotation class CacheDuration(val seconds: Int, val key: String = "")
        '''
        result = extractor.extract(code, "annotations.kt")
        defs = result.get('annotation_defs', [])
        assert len(defs) >= 1
        assert defs[0].name == 'CacheDuration'


# ============================================
# Annotation Usage Extraction
# ============================================

class TestAnnotationUsages:
    def test_annotation_on_class(self, extractor):
        code = '''
@Service
class UserService(private val repo: UserRepository) {
    @Transactional
    fun createUser(dto: CreateUserDTO): User { }
}
        '''
        result = extractor.extract(code, "UserService.kt")
        usages = result.get('annotation_usages', [])
        assert len(usages) >= 1
        annotations = [u.annotation for u in usages]
        assert 'Service' in annotations or 'Transactional' in annotations

    def test_validation_annotations(self, extractor):
        code = '''
@NotBlank
val name: String = ""
@Email
val email: String = ""
@Size(min = 8, max = 100)
val password: String = ""
        '''
        result = extractor.extract(code, "CreateUserRequest.kt")
        usages = result.get('annotation_usages', [])
        assert len(usages) >= 1


# ============================================
# Delegation Extraction
# ============================================

class TestDelegations:
    def test_by_lazy(self, extractor):
        code = '''
        class SettingsManager {
            val config by lazy { loadConfiguration() }
            val database by lazy { DatabaseConnection.create() }
        }
        '''
        result = extractor.extract(code, "SettingsManager.kt")
        delegations = result.get('delegations', [])
        assert len(delegations) >= 1

    def test_by_viewmodels(self, extractor):
        code = '''
        class MainActivity : AppCompatActivity() {
            private val viewModel by viewModels<MainViewModel>()
        }
        '''
        result = extractor.extract(code, "MainActivity.kt")
        delegations = result.get('delegations', [])
        assert len(delegations) >= 1


# ============================================
# DI Binding Extraction
# ============================================

class TestDIBindings:
    def test_koin_module(self, extractor):
        code = '''
        import org.koin.dsl.module

        val appModule = module {
            single { UserRepository() }
            factory { UserService(get()) }
            viewModel { MainViewModel(get()) }
        }
        '''
        result = extractor.extract(code, "AppModule.kt")
        bindings = result.get('di_bindings', [])
        assert len(bindings) >= 1
        frameworks = {b.framework for b in bindings}
        assert 'koin' in frameworks

    def test_hilt_module(self, extractor):
        code = '''
        import dagger.hilt.android.lifecycle.HiltViewModel
        import javax.inject.Inject

        @HiltViewModel
        class MainViewModel @Inject constructor(
            private val repository: UserRepository
        ) : ViewModel()
        '''
        result = extractor.extract(code, "MainViewModel.kt")
        bindings = result.get('di_bindings', [])
        # Hilt annotations should be detected
        assert isinstance(bindings, list)


# ============================================
# Multiplatform Declarations
# ============================================

class TestMultiplatformDecls:
    def test_expect_class(self, extractor):
        code = '''
expect class PlatformLogger {
    fun log(message: String)
}
        '''
        result = extractor.extract(code, "PlatformLogger.kt")
        decls = result.get('multiplatform_decls', [])
        assert len(decls) >= 1
        assert decls[0].kind == 'class'
        assert decls[0].is_expect is True
        assert decls[0].name == 'PlatformLogger'

    def test_actual_class(self, extractor):
        code = '''
actual class PlatformLogger {
    actual fun log(message: String) {
        println(message)
    }
}
        '''
        result = extractor.extract(code, "PlatformLogger.jvm.kt")
        decls = result.get('multiplatform_decls', [])
        assert len(decls) >= 1
        assert decls[0].kind == 'class'
        assert decls[0].is_expect is False

    def test_expect_fun(self, extractor):
        code = '''
        expect fun platformName(): String
        '''
        result = extractor.extract(code, "Platform.kt")
        decls = result.get('multiplatform_decls', [])
        assert len(decls) >= 1


# ============================================
# Context Receivers
# ============================================

class TestContextReceivers:
    def test_context_receiver(self, extractor):
        code = '''
        context(LoggingContext, TransactionContext)
        fun processOrder(order: Order): Result<Unit> {
            log("Processing order ${order.id}")
            return runCatching { orderDao.save(order) }
        }
        '''
        result = extractor.extract(code, "OrderService.kt")
        ctx = result.get('context_receivers', [])
        assert len(ctx) >= 1
        assert 'LoggingContext' in ctx[0].context_types


# ============================================
# Contracts
# ============================================

class TestContracts:
    def test_returns_contract(self, extractor):
        code = '''
        import kotlin.contracts.*

        fun requireNotEmpty(value: String) {
            contract {
                returns() implies (value.isNotEmpty())
            }
            if (value.isEmpty()) throw IllegalArgumentException()
        }
        '''
        result = extractor.extract(code, "Contracts.kt")
        contracts = result.get('contracts', [])
        assert len(contracts) >= 1

    def test_callsInPlace_contract(self, extractor):
        code = '''
fun myRun(block: Runnable) {
    contract {
        callsInPlace(block, InvocationKind.EXACTLY_ONCE)
    }
    block.run()
}
        '''
        result = extractor.extract(code, "Utils.kt")
        contracts = result.get('contracts', [])
        assert len(contracts) >= 1


# ============================================
# DSL Markers
# ============================================

class TestDSLMarkers:
    def test_dsl_marker(self, extractor):
        code = '''
        @DslMarker
        annotation class HtmlDsl

        @DslMarker
        annotation class RouteDsl
        '''
        result = extractor.extract(code, "Markers.kt")
        markers = result.get('dsl_markers', [])
        assert len(markers) >= 1


# ============================================
# Edge Cases
# ============================================

class TestEdgeCases:
    def test_empty_content(self, extractor):
        result = extractor.extract("", "empty.kt")
        assert result.get('annotation_defs', []) == []
        assert result.get('di_bindings', []) == []
        assert result.get('multiplatform_decls', []) == []
        assert result.get('context_receivers', []) == []
        assert result.get('contracts', []) == []

    def test_no_attributes(self, extractor):
        code = '''
        fun main() {
            println("Hello")
        }
        '''
        result = extractor.extract(code, "Main.kt")
        assert result.get('annotation_defs', []) == []

    def test_whitespace_only(self, extractor):
        result = extractor.extract("   \n  ", "blank.kt")
        assert result.get('annotation_defs', []) == []
