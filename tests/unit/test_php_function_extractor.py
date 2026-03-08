"""
Tests for PhpFunctionExtractor — functions, methods, closures, arrow functions.

Part of CodeTrellis v4.24 PHP Language Support.
"""

import pytest
from codetrellis.extractors.php.function_extractor import PhpFunctionExtractor


@pytest.fixture
def extractor():
    return PhpFunctionExtractor()


# ===== FUNCTION EXTRACTION =====

class TestFunctionExtraction:
    """Tests for PHP function extraction."""

    def test_simple_function(self, extractor):
        code = '''<?php
function greet(string $name): string
{
    return "Hello, {$name}!";
}
'''
        result = extractor.extract(code, "helpers.php")
        assert len(result["functions"]) >= 1
        func = result["functions"][0]
        assert func.name == "greet"
        assert func.return_type == "string"

    def test_function_with_typed_params(self, extractor):
        code = '''<?php
function createUser(string $name, string $email, int $age = 0): User
{
    return new User($name, $email, $age);
}
'''
        result = extractor.extract(code, "factory.php")
        assert len(result["functions"]) >= 1
        func = result["functions"][0]
        assert func.name == "createUser"
        assert len(func.parameters) >= 2

    def test_function_with_nullable_type(self, extractor):
        code = '''<?php
function findUser(int $id): ?User
{
    return User::find($id);
}
'''
        result = extractor.extract(code, "finder.php")
        assert len(result["functions"]) >= 1
        func = result["functions"][0]
        assert func.name == "findUser"

    def test_function_with_union_type(self, extractor):
        code = '''<?php
function parse(string|int $value): string|false
{
    return is_string($value) ? $value : (string) $value;
}
'''
        result = extractor.extract(code, "parser.php")
        assert len(result["functions"]) >= 1
        func = result["functions"][0]
        assert func.name == "parse"

    def test_void_function(self, extractor):
        code = '''<?php
function logMessage(string $message): void
{
    error_log($message);
}
'''
        result = extractor.extract(code, "logger.php")
        assert len(result["functions"]) >= 1
        func = result["functions"][0]
        assert func.name == "logMessage"
        assert func.return_type == "void"

    def test_variadic_function(self, extractor):
        code = '''<?php
function sum(int ...$numbers): int
{
    return array_sum($numbers);
}
'''
        result = extractor.extract(code, "math.php")
        assert len(result["functions"]) >= 1
        func = result["functions"][0]
        assert func.name == "sum"


# ===== METHOD EXTRACTION =====

class TestMethodExtraction:
    """Tests for PHP method extraction."""

    def test_public_method(self, extractor):
        code = '''<?php
class UserService
{
    public function findById(int $id): ?User
    {
        return $this->repository->find($id);
    }
}
'''
        result = extractor.extract(code, "UserService.php")
        assert len(result["methods"]) >= 1
        method = result["methods"][0]
        assert method.name == "findById"
        assert method.visibility == "public"

    def test_private_method(self, extractor):
        code = '''<?php
class PaymentProcessor
{
    private function validateCard(string $number): bool
    {
        return strlen($number) === 16;
    }
}
'''
        result = extractor.extract(code, "PaymentProcessor.php")
        assert len(result["methods"]) >= 1
        method = result["methods"][0]
        assert method.name == "validateCard"
        assert method.visibility == "private"

    def test_protected_method(self, extractor):
        code = '''<?php
class BaseController
{
    protected function authorize(string $ability, $model): void
    {
        if (!Gate::allows($ability, $model)) {
            abort(403);
        }
    }
}
'''
        result = extractor.extract(code, "BaseController.php")
        assert len(result["methods"]) >= 1
        method = result["methods"][0]
        assert method.name == "authorize"
        assert method.visibility == "protected"

    def test_static_method(self, extractor):
        code = '''<?php
class Helper
{
    public static function formatDate(DateTime $date): string
    {
        return $date->format('Y-m-d');
    }
}
'''
        result = extractor.extract(code, "Helper.php")
        assert len(result["methods"]) >= 1
        method = result["methods"][0]
        assert method.name == "formatDate"
        assert method.is_static is True

    def test_abstract_method(self, extractor):
        code = '''<?php
abstract class Shape
{
    abstract public function area(): float;
    abstract protected function validate(): bool;
}
'''
        result = extractor.extract(code, "Shape.php")
        assert len(result["methods"]) >= 1

    def test_constructor_with_promotion(self, extractor):
        code = '''<?php
class Product
{
    public function __construct(
        private readonly string $name,
        private readonly float $price,
        private int $quantity = 0,
    ) {}
}
'''
        result = extractor.extract(code, "Product.php")
        assert len(result["methods"]) >= 1
        ctor = [m for m in result["methods"] if m.name == "__construct"]
        assert len(ctor) >= 1

    def test_multiple_methods(self, extractor):
        code = '''<?php
class Calculator
{
    public function add(float $a, float $b): float { return $a + $b; }
    public function subtract(float $a, float $b): float { return $a - $b; }
    public function multiply(float $a, float $b): float { return $a * $b; }
    private function validate(float $value): void {}
}
'''
        result = extractor.extract(code, "Calculator.php")
        assert len(result["methods"]) >= 3


# ===== CLOSURE EXTRACTION =====

class TestClosureExtraction:
    """Tests for PHP closure and arrow function extraction."""

    def test_closure(self, extractor):
        code = '''<?php
$double = fn(int $x): int => $x * 2;
'''
        result = extractor.extract(code, "closures.php")
        assert len(result["closures"]) >= 1

    def test_closure_with_use(self, extractor):
        code = '''<?php
$multiplier = 3;
$multiply = fn(int $value): int => $value * $multiplier;
'''
        result = extractor.extract(code, "closures.php")
        assert len(result["closures"]) >= 1

    def test_arrow_function(self, extractor):
        code = '''<?php
$double = fn(int $x): int => $x * 2;
$names = array_map(fn(User $u) => $u->name, $users);
'''
        result = extractor.extract(code, "arrows.php")
        assert len(result["closures"]) >= 1


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases in function extraction."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.php")
        assert result["functions"] == []
        assert result["methods"] == []
        assert result["closures"] == []

    def test_function_with_no_return_type(self, extractor):
        code = '''<?php
function oldStyle($name, $email)
{
    return compact('name', 'email');
}
'''
        result = extractor.extract(code, "old.php")
        assert len(result["functions"]) >= 1

    def test_interface_methods(self, extractor):
        code = '''<?php
interface Renderable
{
    public function render(): string;
    public function toHtml(): string;
}
'''
        result = extractor.extract(code, "Renderable.php")
        assert len(result["methods"]) >= 1
