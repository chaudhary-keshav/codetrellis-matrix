"""
Tests for JavaScriptFunctionExtractor — function, arrow, generator extraction.

Part of CodeTrellis v4.30 JavaScript Language Support.
"""

import pytest
from codetrellis.extractors.javascript.function_extractor import (
    JavaScriptFunctionExtractor,
    JSFunctionInfo,
    JSArrowFunctionInfo,
    JSGeneratorInfo,
    JSParameterInfo,
)


@pytest.fixture
def extractor():
    return JavaScriptFunctionExtractor()


class TestFunctionDeclaration:
    """Tests for function declaration extraction."""

    def test_simple_function(self, extractor):
        code = '''
function greet(name) {
    return `Hello, ${name}!`;
}
'''
        result = extractor.extract(code, "greet.js")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        assert functions[0].name == "greet"

    def test_async_function(self, extractor):
        code = '''
async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}
'''
        result = extractor.extract(code, "fetch.js")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        assert functions[0].is_async is True

    def test_exported_function(self, extractor):
        code = '''
export function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}
'''
        result = extractor.extract(code, "calc.js")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        assert functions[0].is_exported is True

    def test_function_with_default_params(self, extractor):
        code = '''
function createUser(name, role = 'user', active = true) {
    return { name, role, active };
}
'''
        result = extractor.extract(code, "users.js")
        functions = result.get('functions', [])
        assert len(functions) >= 1

    def test_function_with_rest_params(self, extractor):
        code = '''
function sum(...numbers) {
    return numbers.reduce((a, b) => a + b, 0);
}
'''
        result = extractor.extract(code, "sum.js")
        functions = result.get('functions', [])
        assert len(functions) >= 1

    def test_commonjs_export_function(self, extractor):
        code = '''
module.exports = function processData(data) {
    return data.filter(item => item.valid);
};
'''
        result = extractor.extract(code, "process.js")
        functions = result.get('functions', [])
        assert len(functions) >= 1

    def test_multiple_functions(self, extractor):
        code = '''
function add(a, b) {
    return a + b;
}

function subtract(a, b) {
    return a - b;
}

function multiply(a, b) {
    return a * b;
}
'''
        result = extractor.extract(code, "math.js")
        functions = result.get('functions', [])
        assert len(functions) >= 3


class TestArrowFunctions:
    """Tests for arrow function extraction."""

    def test_arrow_function(self, extractor):
        code = '''
const double = (x) => x * 2;
const greet = (name) => `Hello, ${name}`;
'''
        result = extractor.extract(code, "arrows.js")
        arrows = result.get('arrow_functions', [])
        assert len(arrows) >= 1

    def test_async_arrow(self, extractor):
        code = '''
const fetchUser = async (id) => {
    const res = await fetch(`/api/users/${id}`);
    return res.json();
};
'''
        result = extractor.extract(code, "async_arrow.js")
        arrows = result.get('arrow_functions', [])
        assert len(arrows) >= 1
        assert arrows[0].is_async is True

    def test_exported_arrow(self, extractor):
        code = '''
export const validate = (input) => {
    if (!input) throw new Error('Invalid');
    return true;
};
'''
        result = extractor.extract(code, "validate.js")
        arrows = result.get('arrow_functions', [])
        assert len(arrows) >= 1
        assert arrows[0].is_exported is True


class TestGenerators:
    """Tests for generator function extraction."""

    def test_generator_function(self, extractor):
        code = '''
function* range(start, end) {
    for (let i = start; i < end; i++) {
        yield i;
    }
}
'''
        result = extractor.extract(code, "gen.js")
        generators = result.get('generators', [])
        assert len(generators) >= 1
        assert generators[0].name == "range"

    def test_async_generator(self, extractor):
        code = '''
async function* fetchPages(url) {
    let page = 1;
    while (true) {
        const data = await fetch(`${url}?page=${page}`);
        const json = await data.json();
        if (!json.length) break;
        yield json;
        page++;
    }
}
'''
        result = extractor.extract(code, "async_gen.js")
        generators = result.get('generators', [])
        assert len(generators) >= 1
        assert generators[0].is_async is True


class TestIIFE:
    """Tests for IIFE extraction."""

    def test_iife(self, extractor):
        code = '''
(function() {
    const secret = 'hidden';
    console.log('IIFE executed');
})();
'''
        result = extractor.extract(code, "iife.js")
        functions = result.get('functions', [])
        iifes = [f for f in functions if f.is_iife]
        assert len(iifes) >= 1
