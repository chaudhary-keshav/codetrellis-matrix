"""
EnhancedLuaParser v1.0 - Comprehensive Lua parser using all extractors.

This parser integrates all Lua extractors to provide complete
parsing of Lua source files.

Supports:
- Lua classes (middleclass, classic, 30log, LOOP, hump.class, manual OOP)
- Modules (return-table, M-pattern, module())
- Metatables and metamethods
- Functions (global, local, table, method, coroutines)
- LÖVE2D framework (30+ callbacks, state management)
- OpenResty/nginx-lua directives (content_by_lua, access_by_lua, etc.)
- Lapis web framework (routes, models, migrations)
- lor micro-framework routes
- Redis scripting patterns
- Tarantool database integration
- LuaJIT FFI declarations
- LuaRocks dependency management

Lua version detection from:
- .luacheckrc configuration
- rockspec files (lua >= "5.1")
- require("ffi") for LuaJIT detection

Framework detection (40+ frameworks):
- Game: LÖVE2D, Corona/Solar2D, Defold, Gideros, MOAI
- Web: OpenResty, Lapis, Sailor, lor, Pegasus
- Database: Tarantool, Redis scripting
- Networking: Turbo.lua
- Testing: busted, luaunit, telescope, lust
- OOP: middleclass, classic, 30log, LOOP, hump
- Build: LuaRocks, Teal (typed Lua)

Optional AST support via tree-sitter (when available).
Optional LSP support via lua-language-server / sumneko (when available).

Part of CodeTrellis v4.28 - Lua Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Lua extractors
from .extractors.lua import (
    LuaTypeExtractor, LuaClassInfo, LuaModuleInfo, LuaFieldInfo, LuaMetatableInfo,
    LuaFunctionExtractor, LuaFunctionInfo, LuaMethodInfo, LuaParameterInfo,
    LuaCoroutineInfo,
    LuaAPIExtractor, LuaRouteInfo, LuaCallbackInfo, LuaEventHandlerInfo,
    LuaCommandInfo,
    LuaModelExtractor, LuaModelInfo, LuaQueryInfo, LuaSchemaInfo,
    LuaAttributeExtractor, LuaImportInfo, LuaModuleDefInfo, LuaFFIInfo,
    LuaDependencyInfo, LuaMetaMethodInfo,
)


@dataclass
class LuaParseResult:
    """Complete parse result for a Lua file."""
    file_path: str
    file_type: str = "lua"

    # Core types
    classes: List[LuaClassInfo] = field(default_factory=list)
    modules: List[LuaModuleInfo] = field(default_factory=list)
    metatables: List[LuaMetatableInfo] = field(default_factory=list)

    # Functions and methods
    functions: List[LuaFunctionInfo] = field(default_factory=list)
    methods: List[LuaMethodInfo] = field(default_factory=list)
    coroutines: List[LuaCoroutineInfo] = field(default_factory=list)

    # API/Framework elements
    routes: List[LuaRouteInfo] = field(default_factory=list)
    callbacks: List[LuaCallbackInfo] = field(default_factory=list)
    event_handlers: List[LuaEventHandlerInfo] = field(default_factory=list)
    commands: List[LuaCommandInfo] = field(default_factory=list)

    # Database models
    models: List[LuaModelInfo] = field(default_factory=list)
    queries: List[LuaQueryInfo] = field(default_factory=list)
    schemas: List[LuaSchemaInfo] = field(default_factory=list)

    # Attributes / meta
    imports: List[LuaImportInfo] = field(default_factory=list)
    module_defs: List[LuaModuleDefInfo] = field(default_factory=list)
    ffi_declarations: List[LuaFFIInfo] = field(default_factory=list)
    dependencies: List[LuaDependencyInfo] = field(default_factory=list)
    metamethods: List[LuaMetaMethodInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    lua_version: str = ""
    is_luajit: bool = False


class EnhancedLuaParser:
    """
    Enhanced Lua parser that uses all extractors for comprehensive parsing.

    Framework detection supports 40+ frameworks across:
    - Game engines (LÖVE2D, Corona/Solar2D, Defold, Gideros, MOAI)
    - Web/API (OpenResty, Lapis, Sailor, lor, Pegasus, Turbo.lua)
    - Database (Tarantool, Redis scripting, pgmoon, luasql)
    - Testing (busted, luaunit, telescope, lust, gambiarra)
    - OOP (middleclass, classic, 30log, LOOP, hump.class)
    - Build/Tools (LuaRocks, Teal, MoonScript, Fennel)
    - Utility (Penlight, luaposix, LuaSocket, luasec)

    Optional AST: tree-sitter (pip install tree-sitter tree-sitter-lua)
    Optional LSP: lua-language-server (sumneko_lua)
    """

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Game engines
        'love2d': re.compile(r"function\s+love\.\w+|require\s*\(?['\"]love\.|love\.graphics|love\.audio", re.MULTILINE),
        'corona': re.compile(r"require\s*\(?['\"]composer['\"]|display\.new|system\.getInfo|transition\.to", re.MULTILINE),
        'solar2d': re.compile(r"require\s*\(?['\"]solar2d|solar2d\.composer", re.MULTILINE),
        'defold': re.compile(r"function\s+init\s*\(self\)|function\s+update\s*\(self|msg\.url\(|go\.property\(", re.MULTILINE),
        'gideros': re.compile(r"require\s*\(?['\"]gideros|Sprite\.new|Stage\.new", re.MULTILINE),
        'moai': re.compile(r"MOAISim\.|MOAIGfxDevice|MOAILayer2D", re.MULTILINE),

        # Web / API
        'openresty': re.compile(r"ngx\.\w+|content_by_lua|access_by_lua|resty\.\w+|ngx\.say|ngx\.req", re.MULTILINE),
        'lapis': re.compile(r"require\s*\(?['\"]lapis|class\s+extends\s+lapis|lapis\.Application|@route", re.MULTILINE),
        'sailor': re.compile(r"require\s*\(?['\"]sailor|sailor\.model|sailor\.page", re.MULTILINE),
        'lor': re.compile(r"require\s*\(?['\"]lor\.index|lor\(\)|lor:Router|app:get\(|app:post\(", re.MULTILINE),
        'pegasus': re.compile(r"require\s*\(?['\"]pegasus|Pegasus:new", re.MULTILINE),
        'turbo': re.compile(r"require\s*\(?['\"]turbo|turbo\.web\.Application|turbo\.httpserver", re.MULTILINE),
        'xavante': re.compile(r"require\s*\(?['\"]xavante|xavante\.httpd", re.MULTILINE),

        # Database
        'tarantool': re.compile(r"box\.schema|box\.space|box\.cfg|require\s*\(?['\"]box", re.MULTILINE),
        'redis': re.compile(r"redis\.call|redis\.pcall|KEYS\[|ARGV\[|redis\.status_reply", re.MULTILINE),
        'pgmoon': re.compile(r"require\s*\(?['\"]pgmoon|Postgres:new|pg:query", re.MULTILINE),
        'luasql': re.compile(r"require\s*\(?['\"]luasql\.|luasql\.mysql|luasql\.postgres|luasql\.sqlite3", re.MULTILINE),

        # Testing
        'busted': re.compile(r"describe\s*\(|it\s*\(|assert\.are\.equal|assert\.is_true|pending\s*\(", re.MULTILINE),
        'luaunit': re.compile(r"require\s*\(?['\"]luaunit|TestCase|lu\.assert", re.MULTILINE),
        'telescope': re.compile(r"require\s*\(?['\"]telescope|context\s*\(|test\s*\(", re.MULTILINE),
        'lust': re.compile(r"require\s*\(?['\"]lust|lust\.describe|lust\.it", re.MULTILINE),
        'gambiarra': re.compile(r"require\s*\(?['\"]gambiarra", re.MULTILINE),

        # OOP libraries
        'middleclass': re.compile(r"require\s*\(?['\"]middleclass|class\(['\"]|:subclass\(", re.MULTILINE),
        'classic': re.compile(r"require\s*\(?['\"]classic|Object:extend\(", re.MULTILINE),
        '30log': re.compile(r"require\s*\(?['\"]30log|class\(\)|:extend\(\)", re.MULTILINE),
        'loop': re.compile(r"require\s*\(?['\"]loop\.\w+|loop\.class|loop\.base", re.MULTILINE),
        'hump_class': re.compile(r"require\s*\(?['\"]hump\.class|Class\{|Class:new", re.MULTILINE),

        # Build / Transpilers
        'luarocks': re.compile(r"rockspec_format|package\s*=|dependencies\s*=\s*\{", re.MULTILINE),
        'teal': re.compile(r"require\s*\(?['\"]tl|\.tl$", re.MULTILINE),
        'moonscript': re.compile(r"require\s*\(?['\"]moonscript|moon\.p\(", re.MULTILINE),

        # Utility libraries
        'penlight': re.compile(r"require\s*\(?['\"]pl\.\w+|require\s*\(?['\"]penlight", re.MULTILINE),
        'luasocket': re.compile(r"require\s*\(?['\"]socket|socket\.tcp\(\)|socket\.http", re.MULTILINE),
        'luasec': re.compile(r"require\s*\(?['\"]ssl|ssl\.newcontext", re.MULTILINE),
        'luaposix': re.compile(r"require\s*\(?['\"]posix|posix\.unistd|posix\.signal", re.MULTILINE),
        'lpeg': re.compile(r"require\s*\(?['\"]lpeg|lpeg\.P\(|lpeg\.R\(|lpeg\.S\(", re.MULTILINE),
        'cjson': re.compile(r"require\s*\(?['\"]cjson|cjson\.encode|cjson\.decode", re.MULTILINE),
        'luafilesystem': re.compile(r"require\s*\(?['\"]lfs|lfs\.dir|lfs\.attributes", re.MULTILINE),

        # LuaJIT
        'luajit_ffi': re.compile(r"require\s*\(?['\"]ffi['\"]|ffi\.cdef|ffi\.new|ffi\.typeof", re.MULTILINE),
    }

    # Lua version from .luacheckrc
    LUACHECKRC_VERSION_PATTERN = re.compile(
        r"std\s*=\s*['\"](?:lua)?(?P<version>5[0-4]|jit)['\"]",
        re.MULTILINE
    )

    # Rockspec lua version constraint
    ROCKSPEC_LUA_PATTERN = re.compile(
        r"['\"]lua\s*>=?\s*(?P<version>[\d\.]+)['\"]",
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = LuaTypeExtractor()
        self.function_extractor = LuaFunctionExtractor()
        self.api_extractor = LuaAPIExtractor()
        self.model_extractor = LuaModelExtractor()
        self.attribute_extractor = LuaAttributeExtractor()

        # Optional AST support via tree-sitter
        self._tree_sitter_available = False
        try:
            from tree_sitter import Language, Parser as TSParser
            try:
                import tree_sitter_lua
                self._lua_language = Language(tree_sitter_lua.language())
                self._ts_parser = TSParser(self._lua_language)
                self._tree_sitter_available = True
            except (ImportError, Exception):
                pass
        except (ImportError, Exception):
            pass

        # Optional LSP support via lua-language-server
        self._lsp_available = False
        try:
            from .lsp_client import LSPClient
            self._lsp_client_class = LSPClient
            self._lsp_available = True
        except (ImportError, Exception):
            pass

    def parse(self, content: str, file_path: str = "") -> LuaParseResult:
        """
        Parse Lua source code and extract all information.

        Args:
            content: Lua source code content
            file_path: Path to source file

        Returns:
            LuaParseResult with all extracted information
        """
        result = LuaParseResult(file_path=file_path)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect if LuaJIT
        result.is_luajit = 'luajit_ffi' in result.detected_frameworks or \
            bool(re.search(r"require\s*\(?['\"]ffi['\"]", content))

        # If tree-sitter is available, use AST for enhanced extraction
        if self._tree_sitter_available:
            self._enhance_with_ast(content, result)

        # Extract types (classes, modules, metatables)
        type_result = self.type_extractor.extract(content, file_path)
        result.classes = type_result.get('classes', [])
        result.modules = type_result.get('modules', [])
        result.metatables = type_result.get('metatables', [])

        # Extract functions, methods, coroutines
        func_result = self.function_extractor.extract(content, file_path)
        result.functions = func_result.get('functions', [])
        result.methods = func_result.get('methods', [])
        result.coroutines = func_result.get('coroutines', [])

        # Extract API patterns (routes, callbacks, events, commands)
        api_result = self.api_extractor.extract(content, file_path)
        result.routes = api_result.get('routes', [])
        result.callbacks = api_result.get('callbacks', [])
        result.event_handlers = api_result.get('event_handlers', [])
        result.commands = api_result.get('commands', [])

        # Extract models (ORM models, queries, schemas)
        model_result = self.model_extractor.extract(content, file_path)
        result.models = model_result.get('models', [])
        result.queries = model_result.get('queries', [])
        result.schemas = model_result.get('schemas', [])

        # Extract attributes (imports, module defs, FFI, deps, metamethods)
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.imports = attr_result.get('imports', [])
        result.module_defs = attr_result.get('module_defs', [])
        result.ffi_declarations = attr_result.get('ffi_declarations', [])
        result.dependencies = attr_result.get('dependencies', [])
        result.metamethods = attr_result.get('metamethods', [])

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Lua frameworks are used in the file."""
        frameworks = []
        for fw_name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(fw_name)
        return frameworks

    def _enhance_with_ast(self, content: str, result: LuaParseResult):
        """Use tree-sitter AST for enhanced extraction if available."""
        if not self._tree_sitter_available:
            return
        try:
            tree = self._ts_parser.parse(bytes(content, 'utf-8'))
            root = tree.root_node

            # AST-enhanced: Extract function declarations with precise positions
            self._ast_extract_functions(root, content, result)
        except Exception:
            pass  # Fallback to regex extraction

    def _ast_extract_functions(self, root_node, content: str, result: LuaParseResult):
        """AST-enhanced function extraction."""
        for node in self._find_nodes(root_node, 'function_declaration'):
            name_node = self._find_child(node, 'identifier')
            if name_node:
                name = content[name_node.start_byte:name_node.end_byte]
                for func in result.functions:
                    if func.name == name:
                        func.line_number = node.start_point[0] + 1
                        break

    def _find_nodes(self, root, node_type: str):
        """Recursively find all nodes of a given type."""
        results = []
        if root.type == node_type:
            results.append(root)
        for child in root.children:
            results.extend(self._find_nodes(child, node_type))
        return results

    def _find_child(self, node, child_type: str):
        """Find first child of a given type."""
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    @staticmethod
    def parse_rockspec(content: str) -> Dict[str, Any]:
        """
        Parse a .rockspec file to extract dependency and configuration info.

        Args:
            content: rockspec file content

        Returns:
            Dict with 'package', 'version', 'lua_version', 'dependencies',
            'build_type', 'source_url'
        """
        result: Dict[str, Any] = {
            'package': '',
            'version': '',
            'lua_version': '',
            'dependencies': [],
            'build_type': '',
            'source_url': '',
        }

        # Extract package name
        pkg_match = re.search(r"package\s*=\s*['\"]([^'\"]+)['\"]", content)
        if pkg_match:
            result['package'] = pkg_match.group(1)

        # Extract version
        ver_match = re.search(r"version\s*=\s*['\"]([^'\"]+)['\"]", content)
        if ver_match:
            result['version'] = ver_match.group(1)

        # Extract Lua version constraint
        lua_ver_match = re.search(
            r"['\"]lua\s*>=?\s*([\d\.]+)['\"]",
            content
        )
        if lua_ver_match:
            result['lua_version'] = lua_ver_match.group(1)

        # Extract build type
        build_match = re.search(r"type\s*=\s*['\"](\w+)['\"]", content)
        if build_match:
            result['build_type'] = build_match.group(1)

        # Extract source URL
        url_match = re.search(r"url\s*=\s*['\"]([^'\"]+)['\"]", content)
        if url_match:
            result['source_url'] = url_match.group(1)

        # Extract dependencies
        dep_match = re.search(r"dependencies\s*=\s*\{(.*?)\}", content, re.DOTALL)
        if dep_match:
            dep_block = dep_match.group(1)
            for dep in re.finditer(r"['\"]([^'\"]+)['\"]", dep_block):
                dep_str = dep.group(1)
                parts = dep_str.split()
                dep_name = parts[0] if parts else dep_str
                if dep_name != 'lua':
                    result['dependencies'].append(dep_name)

        return result

    @staticmethod
    def parse_luacheckrc(content: str) -> Dict[str, Any]:
        """
        Parse a .luacheckrc file for version and config info.

        Args:
            content: .luacheckrc file content

        Returns:
            Dict with 'std', 'lua_version', 'globals', 'read_globals'
        """
        result: Dict[str, Any] = {
            'std': '',
            'lua_version': '',
            'globals': [],
            'read_globals': [],
        }

        # Extract std
        std_match = re.search(r"std\s*=\s*['\"]([^'\"]+)['\"]", content)
        if std_match:
            std_val = std_match.group(1)
            result['std'] = std_val
            # Map std to version
            version_map = {
                'lua51': '5.1', 'lua52': '5.2', 'lua53': '5.3',
                'lua54': '5.4', 'luajit': 'jit',
                'max': '5.4', 'min': '5.1',
            }
            result['lua_version'] = version_map.get(std_val, std_val)

        # Extract globals
        globals_match = re.search(r"globals\s*=\s*\{([^}]+)\}", content)
        if globals_match:
            result['globals'] = re.findall(r"['\"](\w+)['\"]", globals_match.group(1))

        # Extract read_globals
        rg_match = re.search(r"read_globals\s*=\s*\{([^}]+)\}", content)
        if rg_match:
            result['read_globals'] = re.findall(r"['\"](\w+)['\"]", rg_match.group(1))

        return result
