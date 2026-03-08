"""
Tests for TypeScriptFunctionExtractor — typed functions, overloads, type guards.

Part of CodeTrellis v4.31 TypeScript Language Support.
"""

import pytest
from codetrellis.extractors.typescript.function_extractor import (
    TypeScriptFunctionExtractor,
    TSFunctionInfo,
    TSParameterInfo,
    TSOverloadInfo,
)


@pytest.fixture
def extractor():
    return TypeScriptFunctionExtractor()


class TestFunctionExtraction:
    """Tests for typed function extraction."""

    def test_simple_typed_function(self, extractor):
        code = '''
export function add(a: number, b: number): number {
    return a + b;
}
'''
        result = extractor.extract(code, "math.ts")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        func = functions[0]
        assert func.name == "add"
        assert func.return_type == "number"
        assert len(func.parameters) >= 2

    def test_async_function(self, extractor):
        code = '''
export async function fetchUser(id: string): Promise<User> {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
}
'''
        result = extractor.extract(code, "api.ts")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        func = functions[0]
        assert func.name == "fetchUser"
        assert func.is_async is True

    def test_generic_function(self, extractor):
        code = '''
export function identity<T>(value: T): T {
    return value;
}
'''
        result = extractor.extract(code, "utils.ts")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        func = functions[0]
        assert func.name == "identity"
        assert len(func.generics) >= 1

    def test_arrow_function(self, extractor):
        code = '''
export const greet = (name: string): string => {
    return `Hello, ${name}!`;
};
'''
        result = extractor.extract(code, "utils.ts")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        func = functions[0]
        assert func.name == "greet"

    def test_optional_parameters(self, extractor):
        code = '''
export function createUser(name: string, age?: number, role: string = 'user'): User {
    return { name, age, role };
}
'''
        result = extractor.extract(code, "users.ts")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        func = functions[0]
        assert func.name == "createUser"
        assert len(func.parameters) >= 2

    def test_rest_parameters(self, extractor):
        code = '''
export function merge<T>(...items: T[]): T[] {
    return items.flat();
}
'''
        result = extractor.extract(code, "utils.ts")
        functions = result.get('functions', [])
        assert len(functions) >= 1


class TestTypeGuardExtraction:
    """Tests for type guard and assertion function extraction."""

    def test_type_guard(self, extractor):
        code = '''
export function isString(value: unknown): value is string {
    return typeof value === 'string';
}
'''
        result = extractor.extract(code, "guards.ts")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        func = functions[0]
        assert func.name == "isString"
        assert func.is_type_guard is True

    def test_assertion_function(self, extractor):
        code = '''
export function assertDefined<T>(value: T | undefined): asserts value is T {
    if (value === undefined) throw new Error('Expected defined');
}
'''
        result = extractor.extract(code, "assertions.ts")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        func = functions[0]
        assert func.name == "assertDefined"
        assert func.is_assertion is True


class TestOverloadExtraction:
    """Tests for function overload extraction."""

    def test_function_overloads(self, extractor):
        code = '''
export function createElement(tag: 'div'): HTMLDivElement;
export function createElement(tag: 'span'): HTMLSpanElement;
export function createElement(tag: string): HTMLElement;
export function createElement(tag: string): HTMLElement {
    return document.createElement(tag);
}
'''
        result = extractor.extract(code, "dom.ts")
        overloads = result.get('overloads', [])
        # Overloads are individual signatures with same name
        create_overloads = [o for o in overloads if o.name == "createElement"]
        assert len(create_overloads) >= 2


class TestGeneratorFunction:
    """Tests for generator function extraction."""

    def test_generator_function(self, extractor):
        code = '''
export function* range(start: number, end: number): Generator<number> {
    for (let i = start; i < end; i++) {
        yield i;
    }
}
'''
        result = extractor.extract(code, "generators.ts")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        func = functions[0]
        assert func.name == "range"
        assert func.is_generator is True
