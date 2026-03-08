"""
Tests for LuaModelExtractor — models, queries, schemas.

Part of CodeTrellis v4.28 Lua Language Support.
"""

import pytest
from codetrellis.extractors.lua.model_extractor import LuaModelExtractor


@pytest.fixture
def extractor():
    return LuaModelExtractor()


# ===== LAPIS MODELS =====

class TestLapisModels:
    """Tests for Lapis Model:extend() extraction."""

    def test_lapis_model(self, extractor):
        code = '''
local Model = require("lapis.db.model").Model

local Users = Model:extend("users", {
    timestamp = true,
    relations = {
        {"posts", has_many = "Posts"},
        {"profile", has_one = "Profiles"},
    }
})
'''
        result = extractor.extract(code, "models/users.lua")
        models = result["models"]
        assert len(models) >= 1
        m = models[0]
        assert m.name == "Users"
        assert m.table_name == "users"
        assert m.orm == "lapis"

    def test_lapis_model_with_relations(self, extractor):
        code = '''
local Model = require("lapis.db.model").Model

local Posts = Model:extend("posts", {
    relations = {
        {"user", belongs_to = "Users"},
    }
})
'''
        result = extractor.extract(code, "models/posts.lua")
        models = result["models"]
        assert len(models) >= 1


# ===== SQL QUERIES =====

class TestSQLQueries:
    """Tests for SQL query extraction."""

    def test_pgmoon_query(self, extractor):
        code = '''
local pgmoon = require("pgmoon")
local pg = pgmoon.new({host = "localhost", database = "mydb"})

local res = pg:query("SELECT * FROM users WHERE id = $1", user_id)
'''
        result = extractor.extract(code, "db.lua")
        queries = result["queries"]
        assert len(queries) >= 1
        q = queries[0]
        assert q.query_type == "SELECT"
        assert q.table == "users"

    def test_insert_query(self, extractor):
        code = '''
db:query("INSERT INTO posts (title, body, user_id) VALUES ($1, $2, $3)", title, body, uid)
'''
        result = extractor.extract(code, "posts.lua")
        queries = result["queries"]
        assert len(queries) >= 1
        q = queries[0]
        assert q.query_type == "INSERT"


# ===== TARANTOOL =====

class TestTarantoolSchemas:
    """Tests for Tarantool space/index extraction."""

    def test_tarantool_space(self, extractor):
        code = '''
box.cfg{listen = 3301}

box.schema.space.create("users", {if_not_exists = true})
box.space.users:create_index("primary", {
    type = "hash",
    parts = {1, "unsigned"},
    if_not_exists = true,
})
'''
        result = extractor.extract(code, "init.lua")
        schemas = result["schemas"]
        assert len(schemas) >= 1
        s = schemas[0]
        assert s.name == "users"
        assert s.framework == "tarantool"


# ===== LAPIS MIGRATIONS =====

class TestLapisMigrations:
    """Tests for Lapis migration extraction."""

    def test_create_table(self, extractor):
        code = '''
local schema = require("lapis.db.schema")

schema.create_table("users", {
    {"id", schema.types.serial},
    {"username", schema.types.varchar},
    {"email", schema.types.varchar},
    {"created_at", schema.types.time},
})
'''
        result = extractor.extract(code, "migrations.lua")
        schemas = result["schemas"]
        assert len(schemas) >= 1
        s = schemas[0]
        assert s.name == "users"
        assert s.operation == "create_table"
        assert s.framework == "lapis"
