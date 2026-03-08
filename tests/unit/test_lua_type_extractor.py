"""
Tests for LuaTypeExtractor — classes, modules, metatables.

Part of CodeTrellis v4.28 Lua Language Support.
"""

import pytest
from codetrellis.extractors.lua.type_extractor import LuaTypeExtractor


@pytest.fixture
def extractor():
    return LuaTypeExtractor()


# ===== CLASS EXTRACTION =====

class TestClassExtraction:
    """Tests for Lua OOP class extraction."""

    def test_middleclass_class(self, extractor):
        code = '''
local class = require("middleclass")
local Animal = class("Animal")

function Animal:initialize(name)
    self.name = name
end

function Animal:speak()
    return "..."
end
'''
        result = extractor.extract(code, "animal.lua")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "Animal"
        assert c.oop_library == "middleclass"

    def test_middleclass_inheritance(self, extractor):
        code = '''
local class = require("middleclass")
local Animal = class("Animal")
local Dog = class("Dog", Animal)

function Dog:speak()
    return "Woof!"
end
'''
        result = extractor.extract(code, "dog.lua")
        classes = result["classes"]
        dog = [c for c in classes if c.name == "Dog"]
        assert len(dog) >= 1
        assert dog[0].parent_class == "Animal"

    def test_classic_extend(self, extractor):
        code = '''
local Object = require("classic")
local Player = Object:extend()

function Player:new(x, y)
    self.x = x
    self.y = y
end
'''
        result = extractor.extract(code, "player.lua")
        assert len(result["classes"]) >= 1
        c = result["classes"][0]
        assert c.name == "Player"

    def test_manual_oop(self, extractor):
        code = '''
local MyClass = {}
MyClass.__index = MyClass

function MyClass.new(name)
    local self = setmetatable({}, MyClass)
    self.name = name
    return self
end

function MyClass:greet()
    return "Hello, " .. self.name
end
'''
        result = extractor.extract(code, "myclass.lua")
        classes = result["classes"]
        assert len(classes) >= 1


# ===== MODULE EXTRACTION =====

class TestModuleExtraction:
    """Tests for Lua module extraction."""

    def test_return_table_module(self, extractor):
        code = '''
local M = {}

function M.hello()
    return "world"
end

return M
'''
        result = extractor.extract(code, "mymodule.lua")
        modules = result["modules"]
        assert len(modules) >= 1

    def test_module_function_call(self, extractor):
        code = '''
module("mypackage.mymodule", package.seeall)

function greet(name)
    return "Hello, " .. name
end
'''
        result = extractor.extract(code, "mymodule.lua")
        modules = result["modules"]
        assert len(modules) >= 1
        assert modules[0].name == "mypackage.mymodule"


# ===== METATABLE EXTRACTION =====

class TestMetatableExtraction:
    """Tests for Lua metatable extraction."""

    def test_setmetatable(self, extractor):
        code = '''
local vec2 = {}
vec2.__index = vec2

function vec2.new(x, y)
    return setmetatable({x = x, y = y}, vec2)
end

function vec2.__add(a, b)
    return vec2.new(a.x + b.x, a.y + b.y)
end

function vec2.__tostring(v)
    return string.format("(%g, %g)", v.x, v.y)
end
'''
        result = extractor.extract(code, "vec2.lua")
        # Should detect classes or metatables
        assert len(result["classes"]) >= 1 or len(result["metatables"]) >= 1
