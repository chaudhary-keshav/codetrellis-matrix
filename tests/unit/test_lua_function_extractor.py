"""
Tests for LuaFunctionExtractor — functions, methods, coroutines.

Part of CodeTrellis v4.28 Lua Language Support.
"""

import pytest
from codetrellis.extractors.lua.function_extractor import LuaFunctionExtractor


@pytest.fixture
def extractor():
    return LuaFunctionExtractor()


# ===== FUNCTION EXTRACTION =====

class TestFunctionExtraction:
    """Tests for Lua function extraction."""

    def test_global_function(self, extractor):
        code = '''
function greet(name)
    return "Hello, " .. name
end
'''
        result = extractor.extract(code, "greet.lua")
        funcs = result["functions"]
        assert len(funcs) >= 1
        f = funcs[0]
        assert f.name == "greet"
        assert f.is_local is False

    def test_local_function(self, extractor):
        code = '''
local function calculate(a, b)
    return a + b
end
'''
        result = extractor.extract(code, "calc.lua")
        funcs = result["functions"]
        assert len(funcs) >= 1
        f = funcs[0]
        assert f.name == "calculate"
        assert f.is_local is True

    def test_table_function_dot(self, extractor):
        code = '''
local M = {}

function M.init(config)
    M.config = config
end

function M.process(data)
    return data
end
'''
        result = extractor.extract(code, "module.lua")
        funcs = result["functions"]
        assert len(funcs) >= 2

    def test_method_colon(self, extractor):
        code = '''
function Player:update(dt)
    self.x = self.x + self.speed * dt
end

function Player:draw()
    love.graphics.draw(self.sprite, self.x, self.y)
end
'''
        result = extractor.extract(code, "player.lua")
        methods = result["methods"]
        assert len(methods) >= 2
        assert methods[0].class_name == "Player"

    def test_anonymous_function_assignment(self, extractor):
        code = '''
local process = function(data, options)
    if not data then return nil end
    return transform(data, options)
end
'''
        result = extractor.extract(code, "process.lua")
        funcs = result["functions"]
        assert len(funcs) >= 1

    def test_varargs_function(self, extractor):
        code = '''
function printf(fmt, ...)
    io.write(string.format(fmt, ...))
end
'''
        result = extractor.extract(code, "printf.lua")
        funcs = result["functions"]
        assert len(funcs) >= 1


# ===== COROUTINE EXTRACTION =====

class TestCoroutineExtraction:
    """Tests for Lua coroutine extraction."""

    def test_coroutine_create(self, extractor):
        code = '''
local co = coroutine.create(function()
    for i = 1, 10 do
        coroutine.yield(i)
    end
end)
'''
        result = extractor.extract(code, "co.lua")
        coroutines = result["coroutines"]
        assert len(coroutines) >= 1

    def test_coroutine_wrap(self, extractor):
        code = '''
local counter = coroutine.wrap(function()
    local i = 0
    while true do
        i = i + 1
        coroutine.yield(i)
    end
end)
'''
        result = extractor.extract(code, "counter.lua")
        coroutines = result["coroutines"]
        assert len(coroutines) >= 1
