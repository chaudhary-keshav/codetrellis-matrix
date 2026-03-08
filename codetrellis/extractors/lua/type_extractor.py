"""
Lua Type Extractor for CodeTrellis

Extracts type definitions from Lua source code:
- Class definitions (via OOP patterns: middleclass, classic, 30log, LOOP, hump)
- Module tables (M = {}, module("name"))
- Metatables and metatable patterns (__index, setmetatable)
- Prototype-based inheritance patterns
- Table constructors as data types

Supports Lua 5.1 through 5.4+ and LuaJIT 2.x features.

Part of CodeTrellis v4.28 - Lua Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class LuaFieldInfo:
    """Information about a table/class field."""
    name: str
    value_type: str = ""  # inferred from assignment
    is_static: bool = False
    is_method: bool = False
    default_value: str = ""
    line_number: int = 0


@dataclass
class LuaClassInfo:
    """Information about a Lua class (OOP pattern)."""
    name: str
    file: str = ""
    parent_class: str = ""
    oop_library: str = ""  # middleclass, classic, 30log, hump, LOOP, manual
    fields: List[LuaFieldInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    static_methods: List[str] = field(default_factory=list)
    metamethods: List[str] = field(default_factory=list)
    mixins: List[str] = field(default_factory=list)
    is_singleton: bool = False
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class LuaModuleInfo:
    """Information about a Lua module."""
    name: str
    file: str = ""
    module_type: str = ""  # return-table, module(), setfenv, M pattern
    exports: List[str] = field(default_factory=list)
    local_functions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class LuaMetatableInfo:
    """Information about a metatable definition."""
    name: str
    file: str = ""
    target_table: str = ""
    metamethods: List[str] = field(default_factory=list)
    has_index: bool = False
    has_newindex: bool = False
    has_call: bool = False
    has_tostring: bool = False
    line_number: int = 0


class LuaTypeExtractor:
    """
    Extracts Lua type definitions using regex-based parsing.

    Supports:
    - OOP class patterns (middleclass, classic, 30log, LOOP, hump.class, manual setmetatable)
    - Module table patterns (local M = {}, return M)
    - Metatable-based inheritance
    - Prototype chains
    """

    # OOP library class patterns
    # middleclass: Class = class('Class') or Class = class('Class', Parent)
    MIDDLECLASS_PATTERN = re.compile(
        r"^\s*(?:local\s+)?(?P<name>\w+)\s*=\s*(?:class|Class)\s*\(\s*['\"](?P<classname>[^'\"]+)['\"]"
        r"(?:\s*,\s*(?P<parent>\w+))?\s*\)",
        re.MULTILINE
    )

    # classic: Class = Object:extend()
    CLASSIC_EXTEND_PATTERN = re.compile(
        r"^\s*(?:local\s+)?(?P<name>\w+)\s*=\s*(?P<parent>\w+)\s*:\s*extend\s*\(\s*\)",
        re.MULTILINE
    )

    # Manual OOP: setmetatable(Class, {__index = Parent})
    MANUAL_OOP_PATTERN = re.compile(
        r"^\s*(?:local\s+)?(?P<name>\w+)\s*=\s*(?:setmetatable\s*\(\s*\{\s*\}\s*,\s*\{?\s*__index\s*=\s*(?P<parent>\w+))",
        re.MULTILINE
    )

    # Self-referencing class pattern: Class = {}; Class.__index = Class
    SELF_INDEX_PATTERN = re.compile(
        r"^\s*(?:local\s+)?(?P<name>\w+)\s*=\s*\{\s*\}.*\n\s*\1\.__index\s*=\s*\1",
        re.MULTILINE
    )

    # Module definitions
    # local M = {} ... return M
    MODULE_TABLE_PATTERN = re.compile(
        r"^\s*local\s+(?P<name>\w+)\s*=\s*\{\s*\}",
        re.MULTILINE
    )

    # Lua 5.1 module() call
    MODULE_CALL_PATTERN = re.compile(
        r"^\s*module\s*\(\s*['\"](?P<name>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # Metatable assignment: setmetatable(tbl, mt)
    SETMETATABLE_PATTERN = re.compile(
        r"setmetatable\s*\(\s*(?P<target>\w+)\s*,\s*(?P<metatable>\{[^}]*\}|\w+)\s*\)",
        re.MULTILINE
    )

    # Method definition on table: Class.method = function(...) or Class:method(...)
    TABLE_METHOD_PATTERN = re.compile(
        r"^\s*(?:function\s+)?(?P<table>\w+)(?P<sep>[.:])(?P<method>\w+)\s*(?:=\s*function)?\s*\(",
        re.MULTILINE
    )

    # Field assignment: Class.field = value
    TABLE_FIELD_PATTERN = re.compile(
        r"^\s*(?P<table>\w+)\.(?P<field>\w+)\s*=\s*(?!function)(?P<value>[^\n]+)",
        re.MULTILINE
    )

    # Metamethods
    METAMETHODS = {
        '__index', '__newindex', '__call', '__tostring', '__len',
        '__add', '__sub', '__mul', '__div', '__mod', '__pow',
        '__unm', '__eq', '__lt', '__le', '__concat', '__gc',
        '__metatable', '__pairs', '__ipairs', '__name',
        # Lua 5.3+
        '__idiv', '__band', '__bor', '__bxor', '__bnot', '__shl', '__shr',
        # Lua 5.4+
        '__close',
    }

    def __init__(self):
        """Initialize the type extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all type definitions from Lua source code.

        Args:
            content: Lua source code
            file_path: Path to source file

        Returns:
            Dict with 'classes', 'modules', 'metatables' lists
        """
        classes = []
        modules = []
        metatables = []
        lines = content.split('\n')

        # Extract classes from OOP libraries
        classes.extend(self._extract_middleclass(content, file_path, lines))
        classes.extend(self._extract_classic(content, file_path, lines))
        classes.extend(self._extract_manual_oop(content, file_path, lines))
        classes.extend(self._extract_self_index(content, file_path, lines))

        # Extract modules
        modules.extend(self._extract_modules(content, file_path, lines))

        # Extract metatables
        metatables.extend(self._extract_metatables(content, file_path))

        # Enrich classes with methods and fields
        for cls in classes:
            cls.methods = self._find_methods(content, cls.name, ':')
            cls.static_methods = self._find_methods(content, cls.name, '.')
            cls.fields = self._find_fields(content, cls.name)
            cls.metamethods = self._find_metamethods(content, cls.name)

        return {
            'classes': classes,
            'modules': modules,
            'metatables': metatables,
        }

    def _extract_middleclass(self, content: str, file_path: str, lines: List[str]) -> List[LuaClassInfo]:
        """Extract middleclass/hump.class-style classes."""
        results = []
        for match in self.MIDDLECLASS_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            doc = self._get_preceding_comment(lines, line_num - 1)
            results.append(LuaClassInfo(
                name=match.group('name'),
                file=file_path,
                parent_class=match.group('parent') or "",
                oop_library="middleclass",
                doc_comment=doc,
                line_number=line_num,
            ))
        return results

    def _extract_classic(self, content: str, file_path: str, lines: List[str]) -> List[LuaClassInfo]:
        """Extract classic/Object:extend() style classes."""
        results = []
        for match in self.CLASSIC_EXTEND_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            doc = self._get_preceding_comment(lines, line_num - 1)
            results.append(LuaClassInfo(
                name=match.group('name'),
                file=file_path,
                parent_class=match.group('parent') or "",
                oop_library="classic",
                doc_comment=doc,
                line_number=line_num,
            ))
        return results

    def _extract_manual_oop(self, content: str, file_path: str, lines: List[str]) -> List[LuaClassInfo]:
        """Extract manually-defined OOP classes using setmetatable."""
        results = []
        for match in self.MANUAL_OOP_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            doc = self._get_preceding_comment(lines, line_num - 1)
            results.append(LuaClassInfo(
                name=match.group('name'),
                file=file_path,
                parent_class=match.group('parent') or "",
                oop_library="manual",
                doc_comment=doc,
                line_number=line_num,
            ))
        return results

    def _extract_self_index(self, content: str, file_path: str, lines: List[str]) -> List[LuaClassInfo]:
        """Extract Class = {}; Class.__index = Class pattern."""
        results = []
        for match in self.SELF_INDEX_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            doc = self._get_preceding_comment(lines, line_num - 1)
            name = match.group('name')
            # Check if it also has setmetatable with parent
            parent = ""
            parent_pattern = re.compile(
                rf'setmetatable\s*\(\s*{re.escape(name)}\s*,\s*\{{\s*__index\s*=\s*(\w+)\s*\}}\s*\)'
            )
            parent_match = parent_pattern.search(content)
            if parent_match and parent_match.group(1) != name:
                parent = parent_match.group(1)
            results.append(LuaClassInfo(
                name=name,
                file=file_path,
                parent_class=parent,
                oop_library="manual",
                doc_comment=doc,
                line_number=line_num,
            ))
        return results

    def _extract_modules(self, content: str, file_path: str, lines: List[str]) -> List[LuaModuleInfo]:
        """Extract module definitions."""
        results = []
        seen = set()

        # Check for module() call (Lua 5.1)
        for match in self.MODULE_CALL_PATTERN.finditer(content):
            name = match.group('name')
            if name not in seen:
                seen.add(name)
                line_num = content[:match.start()].count('\n') + 1
                results.append(LuaModuleInfo(
                    name=name,
                    file=file_path,
                    module_type="module()",
                    line_number=line_num,
                ))

        # Check for local M = {} pattern
        for match in self.MODULE_TABLE_PATTERN.finditer(content):
            name = match.group('name')
            # Must have a corresponding 'return <name>' at end
            return_pattern = re.compile(rf'^\s*return\s+{re.escape(name)}\s*$', re.MULTILINE)
            if return_pattern.search(content) and name not in seen:
                seen.add(name)
                line_num = content[:match.start()].count('\n') + 1
                doc = self._get_preceding_comment(lines, line_num - 1)
                exports = self._find_methods(content, name, '.') + self._find_methods(content, name, ':')
                results.append(LuaModuleInfo(
                    name=name,
                    file=file_path,
                    module_type="return-table",
                    exports=exports,
                    doc_comment=doc,
                    line_number=line_num,
                ))

        return results

    def _extract_metatables(self, content: str, file_path: str) -> List[LuaMetatableInfo]:
        """Extract metatable definitions."""
        results = []
        for match in self.SETMETATABLE_PATTERN.finditer(content):
            target = match.group('target')
            metatable_str = match.group('metatable')
            line_num = content[:match.start()].count('\n') + 1
            metamethods = []
            for mm in self.METAMETHODS:
                if mm in metatable_str:
                    metamethods.append(mm)
            results.append(LuaMetatableInfo(
                name=target,
                file=file_path,
                target_table=target,
                metamethods=metamethods,
                has_index='__index' in metatable_str,
                has_newindex='__newindex' in metatable_str,
                has_call='__call' in metatable_str,
                has_tostring='__tostring' in metatable_str,
                line_number=line_num,
            ))
        return results

    def _find_methods(self, content: str, table_name: str, sep: str) -> List[str]:
        """Find methods defined on a table."""
        methods = []
        escaped = re.escape(table_name)
        escaped_sep = re.escape(sep)
        # function Table.method(...) or function Table:method(...)
        pattern1 = re.compile(rf'function\s+{escaped}{escaped_sep}(\w+)\s*\(', re.MULTILINE)
        for m in pattern1.finditer(content):
            name = m.group(1)
            if not name.startswith('_') or name.startswith('__'):
                methods.append(name)
            else:
                methods.append(name)
        # Table.method = function(...)
        pattern2 = re.compile(rf'{escaped}{escaped_sep}(\w+)\s*=\s*function\s*\(', re.MULTILINE)
        for m in pattern2.finditer(content):
            name = m.group(1)
            if name not in methods:
                methods.append(name)
        return methods

    def _find_fields(self, content: str, table_name: str) -> List[LuaFieldInfo]:
        """Find fields assigned to a table."""
        fields = []
        seen = set()
        for match in self.TABLE_FIELD_PATTERN.finditer(content):
            if match.group('table') == table_name:
                fname = match.group('field')
                if fname not in seen and not fname.startswith('__'):
                    seen.add(fname)
                    val = match.group('value').strip()
                    vtype = self._infer_type(val)
                    line_num = content[:match.start()].count('\n') + 1
                    fields.append(LuaFieldInfo(
                        name=fname,
                        value_type=vtype,
                        default_value=val[:80],
                        line_number=line_num,
                    ))
        return fields

    def _find_metamethods(self, content: str, table_name: str) -> List[str]:
        """Find metamethods defined for a table/class."""
        mms = []
        for mm in self.METAMETHODS:
            # Check: Table.__mm = function or function Table:__mm
            pattern = re.compile(
                rf'(?:{re.escape(table_name)}\.{re.escape(mm)}\s*=\s*function|'
                rf'function\s+{re.escape(table_name)}[.:]{re.escape(mm)}\s*\()'
            )
            if pattern.search(content):
                mms.append(mm)
        return mms

    def _infer_type(self, value: str) -> str:
        """Infer the type from a Lua value literal."""
        v = value.strip().rstrip(';').strip()
        if v in ('true', 'false'):
            return 'boolean'
        if v == 'nil':
            return 'nil'
        if v.startswith('"') or v.startswith("'") or v.startswith('[['):
            return 'string'
        if v.startswith('{'):
            return 'table'
        if re.match(r'^-?\d+$', v):
            return 'integer'
        if re.match(r'^-?\d+\.\d*$', v):
            return 'number'
        if v.startswith('function'):
            return 'function'
        if 'require' in v:
            return 'module'
        return ''

    def _get_preceding_comment(self, lines: List[str], line_idx: int) -> str:
        """Get doc-comment (--- or -- style) above a line."""
        comments = []
        idx = line_idx - 1
        while idx >= 0:
            stripped = lines[idx].strip()
            if stripped.startswith('---') or stripped.startswith('--'):
                text = stripped.lstrip('-').strip()
                comments.insert(0, text)
                idx -= 1
            else:
                break
        return ' '.join(comments)[:300] if comments else ""
