"""
Tests for EnhancedLuaParser — integration test across all extractors.

Part of CodeTrellis v4.28 Lua Language Support.
"""

import pytest
from codetrellis.lua_parser_enhanced import EnhancedLuaParser, LuaParseResult


@pytest.fixture
def parser():
    return EnhancedLuaParser()


class TestFrameworkDetection:
    """Tests for Lua framework detection."""

    def test_love2d_detection(self, parser):
        code = '''
function love.load()
    player = {x = 100, y = 100}
end

function love.update(dt)
    player.x = player.x + 100 * dt
end

function love.draw()
    love.graphics.circle("fill", player.x, player.y, 20)
end
'''
        result = parser.parse(code, "main.lua")
        assert "love2d" in result.detected_frameworks

    def test_openresty_detection(self, parser):
        code = '''
local cjson = require("cjson")
ngx.req.read_body()
local body = ngx.req.get_body_data()
ngx.say(cjson.encode({status = "ok"}))
'''
        result = parser.parse(code, "handler.lua")
        assert "openresty" in result.detected_frameworks

    def test_lapis_detection(self, parser):
        code = '''
local lapis = require("lapis")
local app = lapis.Application()
'''
        result = parser.parse(code, "app.lua")
        assert "lapis" in result.detected_frameworks

    def test_busted_detection(self, parser):
        code = '''
describe("Calculator", function()
    it("adds numbers", function()
        assert.are.equal(4, 2 + 2)
    end)
end)
'''
        result = parser.parse(code, "calculator_spec.lua")
        assert "busted" in result.detected_frameworks

    def test_luajit_detection(self, parser):
        code = '''
local ffi = require("ffi")
ffi.cdef[[
    int printf(const char *fmt, ...);
]]
'''
        result = parser.parse(code, "ffi_test.lua")
        assert result.is_luajit is True
        assert "luajit_ffi" in result.detected_frameworks

    def test_tarantool_detection(self, parser):
        code = '''
box.cfg{listen = 3301}
box.schema.space.create("users", {if_not_exists = true})
'''
        result = parser.parse(code, "init.lua")
        assert "tarantool" in result.detected_frameworks

    def test_middleclass_detection(self, parser):
        code = '''
local class = require("middleclass")
local Animal = class("Animal")
'''
        result = parser.parse(code, "animal.lua")
        assert "middleclass" in result.detected_frameworks

    def test_multiple_frameworks(self, parser):
        code = '''
local class = require("middleclass")
local cjson = require("cjson")

function love.load()
    player = class("Player")
end
'''
        result = parser.parse(code, "main.lua")
        assert "love2d" in result.detected_frameworks
        assert "middleclass" in result.detected_frameworks
        assert "cjson" in result.detected_frameworks


class TestFullParse:
    """Tests for full parse integration."""

    def test_parse_result_type(self, parser):
        code = '''
local M = {}
function M.hello() return "world" end
return M
'''
        result = parser.parse(code, "test.lua")
        assert isinstance(result, LuaParseResult)
        assert result.file_path == "test.lua"
        assert result.file_type == "lua"

    def test_love2d_game(self, parser):
        code = '''
local class = require("middleclass")

local Entity = class("Entity")

function Entity:initialize(x, y)
    self.x = x
    self.y = y
    self.speed = 100
end

function Entity:update(dt)
    self.x = self.x + self.speed * dt
end

function Entity:draw()
    love.graphics.rectangle("fill", self.x, self.y, 32, 32)
end

local player

function love.load()
    player = Entity:new(100, 100)
end

function love.update(dt)
    player:update(dt)
end

function love.draw()
    player:draw()
end

function love.keypressed(key)
    if key == "escape" then
        love.event.quit()
    end
end
'''
        result = parser.parse(code, "main.lua")
        assert "love2d" in result.detected_frameworks
        assert "middleclass" in result.detected_frameworks
        assert len(result.classes) >= 1
        assert len(result.callbacks) >= 4  # load, update, draw, keypressed

    def test_openresty_handler(self, parser):
        code = '''
local cjson = require("cjson")
local redis = require("resty.redis")

local red = redis:new()
red:connect("127.0.0.1", 6379)

ngx.req.read_body()
local body = ngx.req.get_body_data()
local data = cjson.decode(body)

local ok, err = red:set("key", data.value)
if not ok then
    ngx.status = 500
    ngx.say(cjson.encode({error = err}))
    return
end

ngx.say(cjson.encode({status = "ok"}))
'''
        result = parser.parse(code, "handler.lua")
        assert "openresty" in result.detected_frameworks
        assert "cjson" in result.detected_frameworks
        assert len(result.imports) >= 2


class TestRockspecParsing:
    """Tests for .rockspec file parsing."""

    def test_parse_rockspec(self, parser):
        content = '''
package = "luasocket"
version = "3.1.0-1"
source = {
    url = "https://github.com/lunarmodules/luasocket/archive/v3.1.0.tar.gz",
}
dependencies = {
    "lua >= 5.1",
    "luasec >= 1.0",
}
build = {
    type = "builtin",
}
'''
        result = parser.parse_rockspec(content)
        assert result['package'] == 'luasocket'
        assert result['version'] == '3.1.0-1'
        assert result['lua_version'] == '5.1'
        assert 'luasec' in result['dependencies']
        assert result['build_type'] == 'builtin'


class TestLuacheckrcParsing:
    """Tests for .luacheckrc file parsing."""

    def test_parse_luacheckrc(self, parser):
        content = '''
std = "lua51"
globals = {"love", "ngx"}
read_globals = {"jit", "bit"}
'''
        result = parser.parse_luacheckrc(content)
        assert result['std'] == 'lua51'
        assert result['lua_version'] == '5.1'
        assert 'love' in result['globals']
        assert 'jit' in result['read_globals']

    def test_luajit_detection(self, parser):
        content = '''
std = "luajit"
'''
        result = parser.parse_luacheckrc(content)
        assert result['lua_version'] == 'jit'
