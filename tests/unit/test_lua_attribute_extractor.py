"""
Tests for LuaAttributeExtractor — imports, module defs, FFI, deps, metamethods.

Part of CodeTrellis v4.28 Lua Language Support.
"""

import pytest
from codetrellis.extractors.lua.attribute_extractor import LuaAttributeExtractor


@pytest.fixture
def extractor():
    return LuaAttributeExtractor()


# ===== IMPORT EXTRACTION =====

class TestImportExtraction:
    """Tests for require() import extraction."""

    def test_local_require(self, extractor):
        code = '''
local json = require("cjson")
local socket = require("socket")
local lfs = require("lfs")
'''
        result = extractor.extract(code, "app.lua")
        imports = result["imports"]
        assert len(imports) >= 3
        modules = [i.module for i in imports]
        assert "cjson" in modules
        assert "socket" in modules
        assert "lfs" in modules

    def test_field_require(self, extractor):
        code = '''
local insert = require("table").insert
local floor = require("math").floor
'''
        result = extractor.extract(code, "utils.lua")
        imports = result["imports"]
        assert len(imports) >= 2
        # At least one should be destructured
        destructured = [i for i in imports if i.is_destructured]
        assert len(destructured) >= 1

    def test_global_require(self, extractor):
        code = '''
mylib = require("mylib")
'''
        result = extractor.extract(code, "init.lua")
        imports = result["imports"]
        assert len(imports) >= 1
        assert imports[0].is_local is False


# ===== MODULE DEF EXTRACTION =====

class TestModuleDefExtraction:
    """Tests for module definition extraction."""

    def test_module_call(self, extractor):
        code = '''
module("mypackage.mymodule", package.seeall)

function hello()
    return "world"
end
'''
        result = extractor.extract(code, "mymodule.lua")
        module_defs = result["module_defs"]
        assert len(module_defs) >= 1
        assert module_defs[0].name == "mypackage.mymodule"
        assert module_defs[0].module_type == "module()"

    def test_m_pattern(self, extractor):
        code = '''
local M = {}

function M.greet(name)
    return "Hello, " .. name
end

function M.farewell(name)
    return "Goodbye, " .. name
end

return M
'''
        result = extractor.extract(code, "greeting.lua")
        module_defs = result["module_defs"]
        m_patterns = [m for m in module_defs if m.module_type == "M-pattern"]
        assert len(m_patterns) >= 1
        m = m_patterns[0]
        assert "greet" in m.exports
        assert "farewell" in m.exports


# ===== FFI EXTRACTION =====

class TestFFIExtraction:
    """Tests for LuaJIT FFI extraction."""

    def test_ffi_cdef(self, extractor):
        code = '''
local ffi = require("ffi")
ffi.cdef[[
    typedef struct { double x, y; } vec2_t;
    int printf(const char *fmt, ...);
]]
'''
        result = extractor.extract(code, "ffi_types.lua")
        ffi_decls = result["ffi_declarations"]
        assert len(ffi_decls) >= 1

    def test_ffi_new(self, extractor):
        code = '''
local ffi = require("ffi")
local v = ffi.new("vec2_t", {1.0, 2.0})
local arr = ffi.new("int[10]")
'''
        result = extractor.extract(code, "ffi_alloc.lua")
        ffi_decls = result["ffi_declarations"]
        assert len(ffi_decls) >= 2

    def test_ffi_load(self, extractor):
        code = '''
local ffi = require("ffi")
local C = ffi.load("mylib")
'''
        result = extractor.extract(code, "ffi_load.lua")
        ffi_decls = result["ffi_declarations"]
        loads = [f for f in ffi_decls if f.declaration_type == "load"]
        assert len(loads) >= 1
        assert loads[0].library == "mylib"


# ===== DEPENDENCY EXTRACTION =====

class TestDependencyExtraction:
    """Tests for LuaRocks dependency extraction."""

    def test_rockspec_dependencies(self, extractor):
        code = '''
package = "myproject"
version = "1.0-1"

dependencies = {
    "lua >= 5.1",
    "luasocket >= 3.0",
    "cjson >= 2.1.0",
    "lpeg >= 1.0",
}
'''
        result = extractor.extract(code, "myproject-1.0-1.rockspec")
        deps = result["dependencies"]
        assert len(deps) >= 3  # lua is filtered by model, but luasocket/cjson/lpeg should be caught


# ===== METAMETHOD EXTRACTION =====

class TestMetamethodExtraction:
    """Tests for metamethod extraction."""

    def test_metamethod_assignment(self, extractor):
        code = '''
local Vector = {}
Vector.__index = Vector

Vector.__add = function(a, b)
    return Vector.new(a.x + b.x, a.y + b.y)
end

Vector.__tostring = function(v)
    return string.format("(%g, %g)", v.x, v.y)
end
'''
        result = extractor.extract(code, "vector.lua")
        metamethods = result["metamethods"]
        assert len(metamethods) >= 2
        names = [mm.name for mm in metamethods]
        assert "__add" in names
        assert "__tostring" in names
