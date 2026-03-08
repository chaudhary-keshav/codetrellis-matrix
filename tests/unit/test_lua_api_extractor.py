"""
Tests for LuaAPIExtractor — routes, callbacks, events, commands.

Part of CodeTrellis v4.28 Lua Language Support.
"""

import pytest
from codetrellis.extractors.lua.api_extractor import LuaAPIExtractor


@pytest.fixture
def extractor():
    return LuaAPIExtractor()


# ===== LOVE2D CALLBACKS =====

class TestLove2DCallbacks:
    """Tests for LÖVE2D callback extraction."""

    def test_love_load(self, extractor):
        code = '''
function love.load()
    player = {x = 100, y = 100, speed = 200}
    world = love.physics.newWorld(0, 9.81 * 64, true)
end
'''
        result = extractor.extract(code, "main.lua")
        callbacks = result["callbacks"]
        assert len(callbacks) >= 1
        assert callbacks[0].name == "love.load"

    def test_love_update_draw(self, extractor):
        code = '''
function love.update(dt)
    player.x = player.x + player.speed * dt
end

function love.draw()
    love.graphics.circle("fill", player.x, player.y, 20)
end
'''
        result = extractor.extract(code, "main.lua")
        callbacks = result["callbacks"]
        assert len(callbacks) >= 2
        names = [cb.name for cb in callbacks]
        assert "love.update" in names
        assert "love.draw" in names

    def test_love_input_callbacks(self, extractor):
        code = '''
function love.keypressed(key)
    if key == "escape" then
        love.event.quit()
    end
end

function love.mousepressed(x, y, button)
    if button == 1 then
        shoot(x, y)
    end
end
'''
        result = extractor.extract(code, "input.lua")
        callbacks = result["callbacks"]
        assert len(callbacks) >= 2


# ===== LAPIS ROUTES =====

class TestLapisRoutes:
    """Tests for Lapis route extraction."""

    def test_lapis_match_route(self, extractor):
        code = '''
local lapis = require("lapis")
local app = lapis.Application()

app:match("homepage", "/", function(self)
    return "Welcome!"
end)

app:match("user_profile", "/user/:id", function(self)
    return {render = true}
end)
'''
        result = extractor.extract(code, "app.lua")
        routes = result["routes"]
        assert len(routes) >= 2

    def test_lapis_get_post(self, extractor):
        code = '''
app:get("/api/users", function(self)
    return {json = {users = User:select()}}
end)

app:post("/api/users", function(self)
    local user = User:create(self.params)
    return {json = user}
end)
'''
        result = extractor.extract(code, "api.lua")
        routes = result["routes"]
        assert len(routes) >= 2


# ===== OPENRESTY =====

class TestOpenRestyDirectives:
    """Tests for OpenResty directive extraction."""

    def test_openresty_ngx_patterns(self, extractor):
        code = '''
local cjson = require("cjson")

ngx.req.read_body()
local body = ngx.req.get_body_data()
local data = cjson.decode(body)

ngx.say(cjson.encode({status = "ok"}))
'''
        result = extractor.extract(code, "handler.lua")
        # Should detect event_handlers or callbacks for OpenResty patterns
        # The test validates extraction doesn't crash and processes OpenResty code


# ===== LOR ROUTES =====

class TestLorRoutes:
    """Tests for lor micro-framework route extraction."""

    def test_lor_routes(self, extractor):
        code = '''
local lor = require("lor.index")
local app = lor()

app:get("/", function(req, res, next)
    res:send("Hello World!")
end)

app:post("/api/data", function(req, res, next)
    local data = req.body
    res:json({status = "created"})
end)
'''
        result = extractor.extract(code, "app.lua")
        routes = result["routes"]
        assert len(routes) >= 2
