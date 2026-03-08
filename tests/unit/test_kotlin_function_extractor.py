"""
Tests for KotlinFunctionExtractor — suspend, extension, inline, infix, operator functions.

Part of CodeTrellis v4.12 Kotlin Language Support.
"""

import pytest
from codetrellis.extractors.kotlin.function_extractor import KotlinFunctionExtractor


@pytest.fixture
def extractor():
    return KotlinFunctionExtractor()


# ===== REGULAR FUNCTION =====

class TestRegularFunctions:
    """Tests for regular Kotlin function extraction."""

    def test_simple_function(self, extractor):
        code = '''
        fun greet(name: String): String {
            return "Hello, $name"
        }
        '''
        result = extractor.extract(code, "Utils.kt")
        assert len(result["functions"]) == 1
        fn = result["functions"][0]
        assert fn.name == "greet"
        assert fn.return_type == "String"
        assert len(fn.parameters) == 1
        assert fn.parameters[0].name == "name"
        assert fn.parameters[0].type == "String"

    def test_function_no_return_type(self, extractor):
        code = '''
        fun doSomething() {
            println("done")
        }
        '''
        result = extractor.extract(code, "Utils.kt")
        assert len(result["functions"]) == 1
        fn = result["functions"][0]
        assert fn.name == "doSomething"
        assert fn.return_type == ""

    def test_function_multiple_params(self, extractor):
        code = '''
        fun add(a: Int, b: Int): Int = a + b
        '''
        result = extractor.extract(code, "Math.kt")
        assert len(result["functions"]) == 1
        fn = result["functions"][0]
        assert fn.name == "add"
        assert len(fn.parameters) == 2

    def test_private_function(self, extractor):
        code = '''
        private fun helper(): Unit {
        }
        '''
        result = extractor.extract(code, "Internal.kt")
        assert len(result["functions"]) == 1
        fn = result["functions"][0]
        assert fn.is_private is True
        assert fn.is_exported is False

    def test_internal_function(self, extractor):
        code = '''
        internal fun moduleHelper(): String = "ok"
        '''
        result = extractor.extract(code, "Internal.kt")
        assert len(result["functions"]) == 1
        fn = result["functions"][0]
        assert fn.is_internal is True
        assert fn.is_exported is True  # internal is still exported within module


# ===== SUSPEND FUNCTIONS =====

class TestSuspendFunctions:
    """Tests for Kotlin coroutine suspend functions."""

    def test_suspend_function(self, extractor):
        code = '''
        suspend fun fetchData(): List<String> {
            return emptyList()
        }
        '''
        result = extractor.extract(code, "DataSource.kt")
        assert len(result["functions"]) == 1
        fn = result["functions"][0]
        assert fn.name == "fetchData"
        assert fn.is_suspend is True

    def test_suspend_with_params(self, extractor):
        code = '''
        suspend fun loadUser(id: Long): User? {
            return null
        }
        '''
        result = extractor.extract(code, "UserRepo.kt")
        fn = result["functions"][0]
        assert fn.is_suspend is True
        assert fn.name == "loadUser"
        assert len(fn.parameters) == 1


# ===== EXTENSION FUNCTIONS =====

class TestExtensionFunctions:
    """Tests for Kotlin extension functions."""

    def test_extension_function(self, extractor):
        code = '''
        fun String.toSlug(): String {
            return this.lowercase().replace(" ", "-")
        }
        '''
        result = extractor.extract(code, "StringExt.kt")
        assert len(result["functions"]) == 1
        fn = result["functions"][0]
        assert fn.name == "toSlug"
        assert fn.is_extension is True
        assert fn.receiver_type is not None
        assert "String" in fn.receiver_type

    def test_extension_with_generics(self, extractor):
        code = '''
        fun <T> List<T>.secondOrNull(): T? {
            return if (size >= 2) this[1] else null
        }
        '''
        result = extractor.extract(code, "ListExt.kt")
        assert len(result["functions"]) == 1
        fn = result["functions"][0]
        assert fn.name == "secondOrNull"
        assert fn.is_extension is True
        assert len(fn.generic_params) >= 1


# ===== INLINE, INFIX, OPERATOR =====

class TestSpecialModifiers:
    """Tests for inline, infix, operator, tailrec functions."""

    def test_inline_function(self, extractor):
        code = '''
        inline fun <T> measure(block: T): T {
            return block
        }
        '''
        result = extractor.extract(code, "Profiling.kt")
        assert len(result["functions"]) == 1
        fn = result["functions"][0]
        assert fn.name == "measure"
        assert fn.is_inline is True

    def test_infix_function(self, extractor):
        code = '''
        infix fun Int.pow(exponent: Int): Int {
            return Math.pow(this.toDouble(), exponent.toDouble()).toInt()
        }
        '''
        result = extractor.extract(code, "MathExt.kt")
        assert len(result["functions"]) == 1
        fn = result["functions"][0]
        assert fn.name == "pow"
        assert fn.is_infix is True
        assert fn.is_extension is True

    def test_operator_function(self, extractor):
        code = '''
        operator fun Point.plus(other: Point): Point {
            return Point(x + other.x, y + other.y)
        }
        '''
        result = extractor.extract(code, "PointOps.kt")
        assert len(result["functions"]) == 1
        fn = result["functions"][0]
        assert fn.name == "plus"
        assert fn.is_operator is True


# ===== OVERRIDE FUNCTIONS =====

class TestOverrideFunctions:
    """Tests for override modifier detection."""

    def test_override_function(self, extractor):
        code = '''
        class MyService : Service {
            override fun execute(): Result {
                return Result()
            }
        }
        '''
        result = extractor.extract(code, "MyService.kt")
        fns = [f for f in result["functions"] if f.name == "execute"]
        assert len(fns) >= 1
        assert fns[0].is_override is True


# ===== LAMBDA COUNT =====

class TestLambdaCount:
    """Tests for lambda expression counting."""

    def test_lambda_count(self, extractor):
        code = '''
        fun process() {
            val filter = { x: Int -> x > 0 }
            val mapper = { x: Int -> x * 2 }
            list.forEach { item -> println(item) }
        }
        '''
        result = extractor.extract(code, "Lambdas.kt")
        assert result["lambda_count"] >= 3

    def test_no_lambdas(self, extractor):
        code = '''
        fun add(a: Int, b: Int): Int = a + b
        '''
        result = extractor.extract(code, "NoLambdas.kt")
        assert result["lambda_count"] == 0


# ===== EMPTY INPUT =====

class TestEmptyInput:
    """Tests for empty/whitespace input."""

    def test_empty_string(self, extractor):
        result = extractor.extract("", "Empty.kt")
        assert result["functions"] == []
        assert result["lambda_count"] == 0

    def test_whitespace_only(self, extractor):
        result = extractor.extract("   \n\n  ", "Empty.kt")
        assert result["functions"] == []
