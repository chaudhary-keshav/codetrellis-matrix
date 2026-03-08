"""
Tests for JavaScriptTypeExtractor — class, prototype, constant, symbol extraction.

Part of CodeTrellis v4.30 JavaScript Language Support.
"""

import pytest
from codetrellis.extractors.javascript.type_extractor import (
    JavaScriptTypeExtractor,
    JSClassInfo,
    JSPrototypeInfo,
    JSConstantInfo,
    JSSymbolInfo,
    JSPropertyInfo,
)


@pytest.fixture
def extractor():
    return JavaScriptTypeExtractor()


class TestClassExtraction:
    """Tests for ES6+ class extraction."""

    def test_simple_class(self, extractor):
        code = '''
class Person {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }

    greet() {
        return `Hello, I'm ${this.name}`;
    }
}
'''
        result = extractor.extract(code, "person.js")
        classes = result.get('classes', [])
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "Person"

    def test_class_with_extends(self, extractor):
        code = '''
class Animal {
    constructor(name) {
        this.name = name;
    }
}

class Dog extends Animal {
    bark() {
        return 'Woof!';
    }
}
'''
        result = extractor.extract(code, "animals.js")
        classes = result.get('classes', [])
        dog_classes = [c for c in classes if c.name == "Dog"]
        assert len(dog_classes) >= 1
        assert dog_classes[0].superclass == "Animal"

    def test_exported_class(self, extractor):
        code = '''
export class UserService {
    constructor(db) {
        this.db = db;
    }

    async findById(id) {
        return this.db.find(id);
    }
}
'''
        result = extractor.extract(code, "service.js")
        classes = result.get('classes', [])
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "UserService"
        assert cls.is_exported is True

    def test_default_exported_class(self, extractor):
        code = '''
export default class App {
    start() {}
}
'''
        result = extractor.extract(code, "app.js")
        classes = result.get('classes', [])
        assert len(classes) >= 1
        assert classes[0].is_default_export is True

    def test_class_with_static_methods(self, extractor):
        code = '''
class MathUtils {
    static add(a, b) {
        return a + b;
    }

    static multiply(a, b) {
        return a * b;
    }
}
'''
        result = extractor.extract(code, "math.js")
        classes = result.get('classes', [])
        assert len(classes) >= 1
        cls = classes[0]
        assert "add" in cls.static_methods or len(cls.static_methods) >= 1

    def test_class_with_getters_setters(self, extractor):
        code = '''
class Temperature {
    constructor(celsius) {
        this._celsius = celsius;
    }

    get fahrenheit() {
        return this._celsius * 9/5 + 32;
    }

    set fahrenheit(f) {
        this._celsius = (f - 32) * 5/9;
    }
}
'''
        result = extractor.extract(code, "temp.js")
        classes = result.get('classes', [])
        assert len(classes) >= 1

    def test_class_expression(self, extractor):
        code = '''
const MyClass = class {
    constructor() {}
    doSomething() {}
};
'''
        result = extractor.extract(code, "expr.js")
        classes = result.get('classes', [])
        assert len(classes) >= 1


class TestPrototypeExtraction:
    """Tests for prototype-based type extraction."""

    def test_constructor_function(self, extractor):
        code = '''
function Vehicle(make, model) {
    this.make = make;
    this.model = model;
}

Vehicle.prototype.start = function() {
    console.log('Starting...');
};

Vehicle.prototype.stop = function() {
    console.log('Stopping...');
};
'''
        result = extractor.extract(code, "vehicle.js")
        prototypes = result.get('prototypes', [])
        assert len(prototypes) >= 1
        assert prototypes[0].name == "Vehicle"

    def test_prototype_methods(self, extractor):
        code = '''
function Queue() {
    this.items = [];
}

Queue.prototype.enqueue = function(item) {
    this.items.push(item);
};

Queue.prototype.dequeue = function() {
    return this.items.shift();
};
'''
        result = extractor.extract(code, "queue.js")
        prototypes = result.get('prototypes', [])
        assert len(prototypes) >= 1


class TestConstantExtraction:
    """Tests for constant and frozen object extraction."""

    def test_frozen_object(self, extractor):
        code = '''
const STATUS = Object.freeze({
    ACTIVE: 'active',
    INACTIVE: 'inactive',
    PENDING: 'pending',
});
'''
        result = extractor.extract(code, "constants.js")
        constants = result.get('constants', [])
        assert len(constants) >= 1
        assert constants[0].name == "STATUS"
        assert constants[0].is_frozen is True

    def test_uppercase_const(self, extractor):
        code = '''
const MAX_RETRIES = 3;
const API_BASE_URL = 'https://api.example.com';
const DEFAULT_TIMEOUT = 5000;
'''
        result = extractor.extract(code, "config.js")
        constants = result.get('constants', [])
        assert len(constants) >= 1

    def test_exported_frozen_object(self, extractor):
        code = '''
export const COLORS = Object.freeze({
    RED: '#ff0000',
    GREEN: '#00ff00',
    BLUE: '#0000ff',
});
'''
        result = extractor.extract(code, "colors.js")
        constants = result.get('constants', [])
        assert len(constants) >= 1
        assert constants[0].is_exported is True


class TestSymbolExtraction:
    """Tests for Symbol extraction."""

    def test_symbol_creation(self, extractor):
        code = '''
const mySymbol = Symbol('mySymbol');
const ITERATOR = Symbol('iterator');
'''
        result = extractor.extract(code, "symbols.js")
        symbols = result.get('symbols', [])
        assert len(symbols) >= 1

    def test_global_symbol(self, extractor):
        code = '''
const sharedSymbol = Symbol.for('app.shared');
'''
        result = extractor.extract(code, "global_sym.js")
        symbols = result.get('symbols', [])
        assert len(symbols) >= 1
        assert symbols[0].is_global is True
