"""
Lua Attribute Extractor for CodeTrellis

Extracts module-level attributes and metadata from Lua source code:
- require() imports and module resolution
- module() definitions
- LuaJIT FFI declarations (ffi.cdef, ffi.new, ffi.typeof)
- LuaRocks dependency parsing (rockspec files)
- Metamethods (__index, __newindex, __tostring, __add, etc.)
- Global variable declarations

Part of CodeTrellis v4.28 - Lua Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class LuaImportInfo:
    """Information about a require() import."""
    module: str
    alias: str = ""
    is_local: bool = True
    is_destructured: bool = False
    destructured_names: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class LuaModuleDefInfo:
    """Information about a module definition."""
    name: str
    module_type: str = ""  # module(), return-table, M-pattern
    exports: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class LuaFFIInfo:
    """Information about a LuaJIT FFI declaration."""
    declaration_type: str = ""  # cdef, new, typeof, cast, load
    c_type: str = ""
    name: str = ""
    library: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class LuaDependencyInfo:
    """Information about a LuaRocks dependency."""
    name: str
    version: str = ""
    constraint: str = ""  # >=, ==, ~>
    source: str = ""  # rockspec, config
    file: str = ""
    line_number: int = 0


@dataclass
class LuaMetaMethodInfo:
    """Information about a metamethod definition."""
    name: str  # __index, __newindex, __tostring, etc.
    target: str = ""  # table or class name
    implementation_type: str = ""  # function, table, redirect
    file: str = ""
    line_number: int = 0


# All Lua metamethods
METAMETHOD_NAMES = frozenset({
    "__index", "__newindex", "__call", "__tostring", "__len",
    "__unm", "__add", "__sub", "__mul", "__div", "__mod", "__pow",
    "__concat", "__eq", "__lt", "__le", "__gc", "__metatable",
    "__mode", "__pairs", "__ipairs",
    # Lua 5.3+
    "__idiv", "__band", "__bor", "__bxor", "__bnot", "__shl", "__shr",
    # Lua 5.4
    "__close",
})


class LuaAttributeExtractor:
    """
    Extracts Lua module attributes, imports, FFI, dependencies, and metamethods.

    Supports:
    - require() pattern: local x = require("module")
    - Destructured require: local x, y = require("module").x, require("module").y
    - Module field require: local x = require("module").field
    - module() definition (Lua 5.1)
    - Return-table module pattern
    - M-pattern modules (local M = {}; ... return M)
    - LuaJIT ffi.cdef, ffi.new, ffi.typeof, ffi.load
    - LuaRocks rockspec dependency parsing
    - All metamethods (Lua 5.1 through 5.4)
    """

    # require patterns
    REQUIRE_PATTERN = re.compile(
        r"(?P<local>local\s+)?(?P<alias>\w+)\s*=\s*require\s*\(?['\"](?P<module>[^'\"]+)['\"]\)?",
        re.MULTILINE
    )

    # Destructured require: local insert = table.insert  (after require)
    REQUIRE_FIELD_PATTERN = re.compile(
        r"(?:local\s+)?(?P<alias>\w+)\s*=\s*require\s*\(?['\"](?P<module>[^'\"]+)['\"]\)?\s*\.\s*(?P<field>\w+)",
        re.MULTILINE
    )

    # module() definition (Lua 5.1 style)
    MODULE_DEF_PATTERN = re.compile(
        r"module\s*\(\s*['\"](?P<name>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # M-pattern: local M = {}
    M_PATTERN = re.compile(
        r"local\s+(?P<name>[A-Z_]\w*)\s*=\s*\{\s*\}",
        re.MULTILINE
    )

    # Return-table: return { ... }
    RETURN_TABLE_PATTERN = re.compile(
        r"^return\s*\{",
        re.MULTILINE
    )

    # FFI cdef
    FFI_CDEF_PATTERN = re.compile(
        r"ffi\.cdef\s*\[\[(?P<content>.*?)\]\]",
        re.DOTALL
    )

    # FFI new/typeof/cast
    FFI_NEW_PATTERN = re.compile(
        r"ffi\.(?P<func>new|typeof|cast|sizeof|alignof|istype)\s*\(\s*['\"](?P<type>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # FFI load (C library)
    FFI_LOAD_PATTERN = re.compile(
        r"(?:local\s+)?(?P<name>\w+)\s*=\s*ffi\.load\s*\(\s*['\"](?P<lib>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # Rockspec dependencies
    ROCKSPEC_DEP_PATTERN = re.compile(
        r"['\"](?P<name>[\w\-\.]+)\s*(?P<constraint>>=|==|~>|<=|>|<)?\s*(?P<version>[\d\.\-\w]*)['\"]",
        re.MULTILINE
    )

    # Metamethod assignment
    METAMETHOD_PATTERN = re.compile(
        r"(?P<target>\w+)\s*\.\s*(?P<meta>__\w+)\s*=\s*(?P<value>function|{|\w+)",
        re.MULTILINE
    )

    # Metamethod in table constructor
    METAMETHOD_TABLE_PATTERN = re.compile(
        r"(?P<meta>__\w+)\s*=\s*(?P<value>function|{|\w+)",
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the attribute extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all attributes from Lua source code.

        Args:
            content: Lua source code
            file_path: Path to source file

        Returns:
            Dict with 'imports', 'module_defs', 'ffi_declarations', 'dependencies', 'metamethods'
        """
        imports = self._extract_imports(content, file_path)
        module_defs = self._extract_module_defs(content, file_path)
        ffi = self._extract_ffi(content, file_path)
        deps = self._extract_dependencies(content, file_path)
        metamethods = self._extract_metamethods(content, file_path)

        return {
            'imports': imports,
            'module_defs': module_defs,
            'ffi_declarations': ffi,
            'dependencies': deps,
            'metamethods': metamethods,
        }

    def _extract_imports(self, content: str, file_path: str) -> List[LuaImportInfo]:
        """Extract require() statements."""
        results = []
        seen = set()

        # Field-level requires first (more specific)
        for match in self.REQUIRE_FIELD_PATTERN.finditer(content):
            alias = match.group('alias')
            module = match.group('module')
            fld = match.group('field')
            line_num = content[:match.start()].count('\n') + 1
            key = (alias, module, line_num)
            if key not in seen:
                seen.add(key)
                results.append(LuaImportInfo(
                    module=module,
                    alias=alias,
                    is_local=True,
                    is_destructured=True,
                    destructured_names=[fld],
                    file=file_path,
                    line_number=line_num,
                ))

        # Standard requires
        for match in self.REQUIRE_PATTERN.finditer(content):
            alias = match.group('alias')
            module = match.group('module')
            is_local = match.group('local') is not None
            line_num = content[:match.start()].count('\n') + 1
            key = (alias, module, line_num)
            if key not in seen:
                seen.add(key)
                results.append(LuaImportInfo(
                    module=module,
                    alias=alias,
                    is_local=is_local,
                    file=file_path,
                    line_number=line_num,
                ))

        return results

    def _extract_module_defs(self, content: str, file_path: str) -> List[LuaModuleDefInfo]:
        """Extract module definitions."""
        results = []

        # Lua 5.1 module() call
        for match in self.MODULE_DEF_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            results.append(LuaModuleDefInfo(
                name=match.group('name'),
                module_type="module()",
                file=file_path,
                line_number=line_num,
            ))

        # M-pattern
        for match in self.M_PATTERN.finditer(content):
            name = match.group('name')
            # Check if there's a corresponding return at end
            if re.search(rf'return\s+{re.escape(name)}\s*$', content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                # Collect exports: M.func_name = function or function M.func_name
                exports = re.findall(
                    rf'{re.escape(name)}\.(\w+)\s*=\s*function|function\s+{re.escape(name)}\.(\w+)',
                    content
                )
                export_names = [e[0] or e[1] for e in exports]
                results.append(LuaModuleDefInfo(
                    name=name,
                    module_type="M-pattern",
                    exports=export_names,
                    file=file_path,
                    line_number=line_num,
                ))

        # Return-table pattern
        for match in self.RETURN_TABLE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Only count if it's the last return in file
            after = content[match.start():]
            if after.count('return') <= 1:
                results.append(LuaModuleDefInfo(
                    name="(anonymous)",
                    module_type="return-table",
                    file=file_path,
                    line_number=line_num,
                ))

        return results

    def _extract_ffi(self, content: str, file_path: str) -> List[LuaFFIInfo]:
        """Extract LuaJIT FFI declarations."""
        results = []

        # Check if FFI is used at all
        if 'ffi' not in content:
            return results

        # ffi.cdef blocks
        for match in self.FFI_CDEF_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            c_content = match.group('content').strip()
            # Extract individual type declarations
            type_defs = re.findall(
                r'typedef\s+(?:struct|union|enum)?\s*\w+\s+(\w+)|struct\s+(\w+)',
                c_content
            )
            for td in type_defs:
                name = td[0] or td[1]
                results.append(LuaFFIInfo(
                    declaration_type="cdef",
                    c_type="struct" if td[1] else "typedef",
                    name=name,
                    file=file_path,
                    line_number=line_num,
                ))

            # If no specific types, register the cdef block itself
            if not type_defs:
                results.append(LuaFFIInfo(
                    declaration_type="cdef",
                    c_type="block",
                    name="cdef_block",
                    file=file_path,
                    line_number=line_num,
                ))

        # ffi.new / ffi.typeof / ffi.cast
        for match in self.FFI_NEW_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            results.append(LuaFFIInfo(
                declaration_type=match.group('func'),
                c_type=match.group('type'),
                file=file_path,
                line_number=line_num,
            ))

        # ffi.load
        for match in self.FFI_LOAD_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            results.append(LuaFFIInfo(
                declaration_type="load",
                library=match.group('lib'),
                name=match.group('name'),
                file=file_path,
                line_number=line_num,
            ))

        return results

    def _extract_dependencies(self, content: str, file_path: str) -> List[LuaDependencyInfo]:
        """Extract LuaRocks dependencies from rockspec files."""
        results = []

        # Only parse rockspec files
        if not file_path.endswith('.rockspec') and 'dependencies' not in content:
            return results

        # Find dependencies block
        dep_match = re.search(
            r'dependencies\s*=\s*\{(.*?)\}',
            content,
            re.DOTALL
        )
        if dep_match:
            dep_block = dep_match.group(1)
            for match in self.ROCKSPEC_DEP_PATTERN.finditer(dep_block):
                name = match.group('name')
                constraint = match.group('constraint') or ""
                version = match.group('version') or ""
                line_num = content[:match.start() + dep_match.start()].count('\n') + 1

                results.append(LuaDependencyInfo(
                    name=name,
                    version=version,
                    constraint=constraint,
                    source="rockspec",
                    file=file_path,
                    line_number=line_num,
                ))

        return results

    def _extract_metamethods(self, content: str, file_path: str) -> List[LuaMetaMethodInfo]:
        """Extract metamethod definitions."""
        results = []
        seen = set()

        # Direct assignment: MyClass.__tostring = function(self) ...
        for match in self.METAMETHOD_PATTERN.finditer(content):
            meta = match.group('meta')
            if meta in METAMETHOD_NAMES:
                target = match.group('target')
                value = match.group('value')
                line_num = content[:match.start()].count('\n') + 1
                key = (target, meta, line_num)
                if key not in seen:
                    seen.add(key)
                    impl_type = "function" if value == "function" else (
                        "table" if value == "{" else "redirect"
                    )
                    results.append(LuaMetaMethodInfo(
                        name=meta,
                        target=target,
                        implementation_type=impl_type,
                        file=file_path,
                        line_number=line_num,
                    ))

        return results
