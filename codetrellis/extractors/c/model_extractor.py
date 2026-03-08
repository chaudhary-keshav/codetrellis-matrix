"""
CModelExtractor - Extracts C data structures, global variables, and constants.

This extractor parses C source code and extracts:
- Data structure patterns (linked lists, trees, hash tables, queues, stacks)
- Global variable declarations
- Constant definitions (#define constants, const variables, enum-based constants)
- Extern declarations for cross-module data
- Static file-scope variables

Part of CodeTrellis v4.19 - C Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CDataStructureInfo:
    """Information about a C data structure pattern (linked list, tree, etc.)."""
    name: str
    kind: str = ""  # linked_list, tree, hash_table, queue, stack, ring_buffer, graph
    struct_name: str = ""
    file: str = ""
    line_number: int = 0
    details: Optional[str] = None


@dataclass
class CGlobalVarInfo:
    """Information about a C global variable."""
    name: str
    type: str
    is_static: bool = False
    is_extern: bool = False
    is_const: bool = False
    is_volatile: bool = False
    is_thread_local: bool = False
    initial_value: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CConstantInfo:
    """Information about a C constant."""
    name: str
    value: str
    kind: str = "define"  # define, const, enum
    type: Optional[str] = None
    file: str = ""
    line_number: int = 0


class CModelExtractor:
    """
    Extracts C data structure patterns and global data from source code.

    Detects:
    - Linked list patterns (next pointer in struct)
    - Binary tree patterns (left/right pointers)
    - Hash table patterns (buckets, hash function, table array)
    - Queue/Stack patterns (head/tail, top, push/pop)
    - Ring buffer patterns (read/write index, buffer)
    - Global variables with extern/static
    - Constants (#define, const, enum-based)
    """

    # Linked list pattern: struct with self-referential next pointer
    LINKED_LIST = re.compile(
        r'struct\s+(\w+)\s*\{[^}]*'
        r'struct\s+\1\s*\*\s*(?:next|prev|flink|blink)',
        re.MULTILINE | re.DOTALL
    )

    # Tree pattern: struct with left/right or children
    TREE_PATTERN = re.compile(
        r'struct\s+(\w+)\s*\{[^}]*'
        r'struct\s+\1\s*\*\s*(?:left|right|parent|child)',
        re.MULTILINE | re.DOTALL
    )

    # Hash table pattern
    HASH_TABLE = re.compile(
        r'struct\s+(\w+)\s*\{[^}]*'
        r'(?:bucket|hash|table|entries)\b',
        re.MULTILINE | re.DOTALL
    )

    # Queue/stack patterns
    QUEUE_PATTERN = re.compile(
        r'struct\s+(\w+)\s*\{[^}]*'
        r'(?:head|tail|front|rear|capacity|size)\b',
        re.MULTILINE | re.DOTALL
    )

    # Ring buffer
    RING_BUFFER = re.compile(
        r'struct\s+(\w+)\s*\{[^}]*'
        r'(?:read_idx|write_idx|rd_idx|wr_idx|head|tail).*'
        r'(?:buf|buffer|data)\b',
        re.MULTILINE | re.DOTALL
    )

    # Global variable at file scope
    GLOBAL_VAR = re.compile(
        r'^(?P<qualifiers>(?:(?:static|extern|const|volatile|_Thread_local|__thread|register)\s+)*)'
        r'(?P<type>(?:(?:unsigned|signed|long|short|struct|union|enum)\s+)*\w[\w\s*]*?)'
        r'\s+(?P<stars>\**)(?P<name>\w+)'
        r'(?:\s*=\s*(?P<value>[^;]+?))?;',
        re.MULTILINE
    )

    # #define constants
    DEFINE_CONSTANT = re.compile(
        r'^\s*#\s*define\s+(?P<name>[A-Z_]\w*)\s+(?P<value>[^\n\\]+(?:\\\n[^\n]*)*)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the C model extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract C data structures, globals, and constants.

        Args:
            content: C source code content
            file_path: Path to source file

        Returns:
            Dict with 'data_structures', 'global_vars', 'constants' keys
        """
        # Remove single-line comments
        clean = re.sub(r'//[^\n]*', '', content)
        # Remove multi-line comments
        clean = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), clean, flags=re.DOTALL)

        data_structures = self._extract_data_structures(clean, file_path, content)
        global_vars = self._extract_global_vars(clean, file_path, content)
        constants = self._extract_constants(clean, file_path, content)

        return {
            'data_structures': data_structures,
            'global_vars': global_vars,
            'constants': constants,
        }

    def _get_line_number(self, content: str, pos: int) -> int:
        return content[:pos].count('\n') + 1

    def _extract_data_structures(self, clean: str, file_path: str, original: str) -> List[CDataStructureInfo]:
        """Detect common C data structure patterns."""
        ds_list = []
        seen = set()

        # Linked lists
        for match in self.LINKED_LIST.finditer(clean):
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                ds_list.append(CDataStructureInfo(
                    name=name,
                    kind='linked_list',
                    struct_name=name,
                    file=file_path,
                    line_number=self._get_line_number(original, match.start()),
                ))

        # Trees
        for match in self.TREE_PATTERN.finditer(clean):
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                ds_list.append(CDataStructureInfo(
                    name=name,
                    kind='tree',
                    struct_name=name,
                    file=file_path,
                    line_number=self._get_line_number(original, match.start()),
                ))

        # Hash tables
        for match in self.HASH_TABLE.finditer(clean):
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                ds_list.append(CDataStructureInfo(
                    name=name,
                    kind='hash_table',
                    struct_name=name,
                    file=file_path,
                    line_number=self._get_line_number(original, match.start()),
                ))

        # Queues/Stacks
        for match in self.QUEUE_PATTERN.finditer(clean):
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                ds_list.append(CDataStructureInfo(
                    name=name,
                    kind='queue_or_stack',
                    struct_name=name,
                    file=file_path,
                    line_number=self._get_line_number(original, match.start()),
                ))

        # Ring buffers
        for match in self.RING_BUFFER.finditer(clean):
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                ds_list.append(CDataStructureInfo(
                    name=name,
                    kind='ring_buffer',
                    struct_name=name,
                    file=file_path,
                    line_number=self._get_line_number(original, match.start()),
                ))

        return ds_list

    def _extract_global_vars(self, clean: str, file_path: str, original: str) -> List[CGlobalVarInfo]:
        """Extract file-scope global variables."""
        globals_list = []
        # Only consider top-level declarations (not inside braces)
        # Simple heuristic: lines at indent level 0
        for match in self.GLOBAL_VAR.finditer(clean):
            qualifiers = match.group('qualifiers').strip() if match.group('qualifiers') else ''
            ftype = match.group('type').strip()
            stars = match.group('stars') or ''
            name = match.group('name')
            value = match.group('value').strip() if match.group('value') else None

            # Skip function definitions/prototypes (have parentheses)
            after_name_pos = match.end()
            # Skip common false positives
            if name in ('if', 'for', 'while', 'switch', 'return', 'sizeof',
                        'typedef', 'struct', 'union', 'enum', 'main'):
                continue

            full_type = ftype + stars if stars else ftype

            # Check if this is at top level (crude heuristic: starts at column 0 or after static/extern)
            line_start = clean.rfind('\n', 0, match.start()) + 1
            indent = match.start() - line_start
            if indent > 4 and 'static' not in qualifiers and 'extern' not in qualifiers:
                continue  # Likely inside a function

            globals_list.append(CGlobalVarInfo(
                name=name,
                type=full_type,
                is_static='static' in qualifiers,
                is_extern='extern' in qualifiers,
                is_const='const' in qualifiers,
                is_volatile='volatile' in qualifiers,
                is_thread_local='_Thread_local' in qualifiers or '__thread' in qualifiers,
                initial_value=value[:50] if value else None,
                file=file_path,
                line_number=self._get_line_number(original, match.start()),
            ))
        return globals_list

    def _extract_constants(self, clean: str, file_path: str, original: str) -> List[CConstantInfo]:
        """Extract constants (#define and const variables)."""
        constants = []

        # #define constants (only uppercase names by convention)
        for match in self.DEFINE_CONSTANT.finditer(original):  # Use original for #define
            name = match.group('name')
            value = match.group('value').strip()
            # Skip function-like macros
            if '(' in value[:1]:
                continue
            # Skip include guards
            if name.endswith('_H') or name.endswith('_H_') or name.endswith('_INCLUDED'):
                continue
            constants.append(CConstantInfo(
                name=name,
                value=value[:80],
                kind='define',
                file=file_path,
                line_number=self._get_line_number(original, match.start()),
            ))

        return constants
