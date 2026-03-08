"""
CppModelExtractor - Extracts C++ data patterns, RAII resources, smart pointers, containers.

This extractor parses C++ source code and extracts:
- STL container usage (vector, map, set, unordered_map, etc.)
- Smart pointer usage (unique_ptr, shared_ptr, weak_ptr)
- RAII resource wrappers
- Global/static variables
- Constants (const, constexpr, constinit)
- Design pattern indicators (Singleton, Factory, Observer, etc.)
- Template metaprogramming patterns (SFINAE, type_traits, concepts)

Supports all C++ standards: C++98 through C++26.

Part of CodeTrellis v4.20 - C++ Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CppContainerUsageInfo:
    """Information about STL container usage."""
    container_type: str = ""  # vector, map, set, deque, etc.
    element_type: Optional[str] = None
    variable_name: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CppSmartPointerInfo:
    """Information about smart pointer usage."""
    kind: str = ""  # unique_ptr, shared_ptr, weak_ptr
    pointee_type: Optional[str] = None
    variable_name: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CppRAIIInfo:
    """Information about a RAII wrapper class."""
    class_name: str = ""
    resource_type: str = ""  # file, lock, connection, memory, handle
    has_destructor: bool = False
    has_move: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class CppGlobalVarInfo:
    """Information about a C++ global/static variable."""
    name: str = ""
    type: str = ""
    is_static: bool = False
    is_extern: bool = False
    is_const: bool = False
    is_constexpr: bool = False
    is_constinit: bool = False  # C++20
    is_inline: bool = False  # C++17
    is_thread_local: bool = False
    namespace: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CppConstantInfo:
    """Information about a C++ constant."""
    name: str = ""
    value: Optional[str] = None
    type: Optional[str] = None
    kind: str = "constexpr"  # constexpr, const, constinit, define, enum
    is_template: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class CppDesignPatternInfo:
    """Information about a detected design pattern."""
    pattern: str = ""  # singleton, factory, observer, strategy, visitor, etc.
    class_name: str = ""
    confidence: str = "medium"  # low, medium, high
    file: str = ""
    line_number: int = 0


class CppModelExtractor:
    """
    Extracts C++ data model patterns from source code.

    Handles:
    - STL container usage (vector, map, set, list, deque, array, etc.)
    - Smart pointer patterns (unique_ptr, shared_ptr, weak_ptr)
    - RAII resource wrappers
    - Global/static/extern variables
    - Constants (const, constexpr, constinit)
    - Design pattern detection (Singleton, Factory, Observer, Strategy, Visitor)
    - Template metaprogramming patterns
    """

    # STL container patterns
    CONTAINER_PATTERN = re.compile(
        r'(?:std::)?(?P<type>vector|map|unordered_map|set|unordered_set|'
        r'multimap|multiset|deque|list|forward_list|array|'
        r'stack|queue|priority_queue|span|mdspan|flat_map|flat_set)'
        r'\s*<\s*(?P<elem>[^>]+(?:<[^>]*>[^>]*)?)>'
        r'(?:\s+(?P<name>\w+))?',
        re.MULTILINE
    )

    # Smart pointer patterns
    SMART_PTR_PATTERN = re.compile(
        r'(?:std::)?(?P<kind>unique_ptr|shared_ptr|weak_ptr|auto_ptr)'
        r'\s*<\s*(?P<type>[^>]+)>'
        r'(?:\s+(?P<name>\w+))?',
        re.MULTILINE
    )

    # make_unique / make_shared
    MAKE_PTR_PATTERN = re.compile(
        r'(?:std::)?(?P<kind>make_unique|make_shared)\s*<\s*(?P<type>[^>]+)>',
        re.MULTILINE
    )

    # RAII patterns (class with destructor managing resources)
    RAII_KEYWORDS = re.compile(
        r'(?:std::)?(?:lock_guard|unique_lock|shared_lock|scoped_lock|'
        r'fstream|ifstream|ofstream|stringstream|'
        r'mutex|recursive_mutex|'
        r'condition_variable|'
        r'jthread|thread)',
        re.MULTILINE
    )

    # Global/static variable pattern
    GLOBAL_VAR_PATTERN = re.compile(
        r'^(?P<qualifiers>(?:(?:static|extern|inline|thread_local|constexpr|constinit|const|volatile)\s+)*)'
        r'(?P<type>(?:(?:unsigned|signed|long|short|struct|class|enum|typename|auto)\s+)*[\w:]+(?:<[^>]*>)?[\s*&]*)'
        r'\s+(?P<name>\w+)'
        r'(?:\s*=\s*(?P<value>[^;]+))?'
        r'\s*;',
        re.MULTILINE
    )

    # Constexpr variable pattern
    CONSTEXPR_PATTERN = re.compile(
        r'(?:inline\s+)?constexpr\s+(?P<type>[\w:]+(?:<[^>]*>)?)\s+(?P<name>\w+)\s*=\s*(?P<value>[^;]+);',
        re.MULTILINE
    )

    # Singleton pattern detection
    SINGLETON_PATTERN = re.compile(
        r'static\s+\w+[&*]?\s+(?:getInstance|instance|get_instance)\s*\(',
        re.MULTILINE
    )

    # Factory pattern detection
    FACTORY_PATTERN = re.compile(
        r'(?:virtual\s+)?(?:std::)?(?:unique_ptr|shared_ptr|[\w:]+\s*\*)\s+'
        r'(?:create|make|build|construct)\w*\s*\(',
        re.MULTILINE
    )

    # Observer/event pattern detection
    OBSERVER_PATTERN = re.compile(
        r'(?:add|remove|notify|register|subscribe|unsubscribe)(?:Observer|Listener|Handler|Callback)\s*\(',
        re.MULTILINE
    )

    # Strategy pattern detection
    STRATEGY_PATTERN = re.compile(
        r'(?:set|change|switch)(?:Strategy|Policy|Algorithm)\s*\(',
        re.MULTILINE
    )

    # Visitor pattern detection
    VISITOR_PATTERN = re.compile(
        r'(?:virtual\s+)?void\s+(?:accept|visit)\s*\(\s*(?:const\s+)?\w*(?:Visitor|Element)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the C++ model extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all model/data patterns from C++ source code.

        Args:
            content: C++ source code content
            file_path: Path to source file

        Returns:
            Dict with 'containers', 'smart_pointers', 'raii', 'global_vars',
            'constants', 'design_patterns' lists
        """
        result = {
            'containers': [],
            'smart_pointers': [],
            'raii': [],
            'global_vars': [],
            'constants': [],
            'design_patterns': [],
        }

        result['containers'] = self._extract_containers(content, file_path)
        result['smart_pointers'] = self._extract_smart_pointers(content, file_path)
        result['raii'] = self._extract_raii(content, file_path)
        result['global_vars'] = self._extract_globals(content, file_path)
        result['constants'] = self._extract_constants(content, file_path)
        result['design_patterns'] = self._extract_design_patterns(content, file_path)

        return result

    def _extract_containers(self, content: str, file_path: str) -> List[CppContainerUsageInfo]:
        """Extract STL container usage."""
        containers = []
        seen = set()
        for match in self.CONTAINER_PATTERN.finditer(content):
            ctype = match.group('type')
            elem = match.group('elem').strip()
            name = match.group('name')
            line_num = content[:match.start()].count('\n') + 1
            key = f"{ctype}:{elem}:{name}"
            if key not in seen:
                seen.add(key)
                containers.append(CppContainerUsageInfo(
                    container_type=ctype,
                    element_type=elem,
                    variable_name=name,
                    file=file_path,
                    line_number=line_num,
                ))
        return containers

    def _extract_smart_pointers(self, content: str, file_path: str) -> List[CppSmartPointerInfo]:
        """Extract smart pointer usage."""
        ptrs = []
        seen = set()

        # Direct declarations
        for match in self.SMART_PTR_PATTERN.finditer(content):
            kind = match.group('kind')
            ptype = match.group('type').strip()
            name = match.group('name')
            line_num = content[:match.start()].count('\n') + 1
            key = f"{kind}:{ptype}:{name}"
            if key not in seen:
                seen.add(key)
                ptrs.append(CppSmartPointerInfo(
                    kind=kind,
                    pointee_type=ptype,
                    variable_name=name,
                    file=file_path,
                    line_number=line_num,
                ))

        # make_unique / make_shared
        for match in self.MAKE_PTR_PATTERN.finditer(content):
            kind = match.group('kind').replace('make_', '') + '_ptr'
            ptype = match.group('type').strip()
            line_num = content[:match.start()].count('\n') + 1
            key = f"make:{kind}:{ptype}"
            if key not in seen:
                seen.add(key)
                ptrs.append(CppSmartPointerInfo(
                    kind=kind,
                    pointee_type=ptype,
                    file=file_path,
                    line_number=line_num,
                ))

        return ptrs

    def _extract_raii(self, content: str, file_path: str) -> List[CppRAIIInfo]:
        """Extract RAII resource wrapper patterns."""
        raii = []
        seen = set()
        for match in self.RAII_KEYWORDS.finditer(content):
            keyword = match.group(0)
            line_num = content[:match.start()].count('\n') + 1
            key = f"{keyword}:{line_num}"
            if key not in seen:
                seen.add(key)
                # Classify resource type
                if 'lock' in keyword or 'mutex' in keyword:
                    rtype = 'lock'
                elif 'stream' in keyword or 'fstream' in keyword:
                    rtype = 'file'
                elif 'thread' in keyword:
                    rtype = 'thread'
                elif 'condition' in keyword:
                    rtype = 'synchronization'
                else:
                    rtype = 'resource'

                raii.append(CppRAIIInfo(
                    class_name=keyword,
                    resource_type=rtype,
                    file=file_path,
                    line_number=line_num,
                ))
        return raii

    def _extract_globals(self, content: str, file_path: str) -> List[CppGlobalVarInfo]:
        """Extract global/static variable declarations."""
        globals_list = []
        # Only match at top level (rough heuristic: not indented)
        for match in self.GLOBAL_VAR_PATTERN.finditer(content):
            qualifiers = match.group('qualifiers') or ''
            vtype = match.group('type').strip()
            name = match.group('name')
            line_num = content[:match.start()].count('\n') + 1

            # Skip function declarations and common false positives
            if name in ('main', 'return', 'if', 'for', 'while', 'switch', 'case', 'class', 'struct'):
                continue
            if '(' in match.group(0):  # likely a function
                continue

            # Only include if it has storage qualifiers or is clearly global
            has_qualifier = any(q in qualifiers for q in ('static', 'extern', 'constexpr', 'constinit', 'inline', 'thread_local', 'const'))
            if not has_qualifier:
                continue

            globals_list.append(CppGlobalVarInfo(
                name=name,
                type=vtype,
                is_static='static' in qualifiers,
                is_extern='extern' in qualifiers,
                is_const='const' in qualifiers and 'constexpr' not in qualifiers,
                is_constexpr='constexpr' in qualifiers,
                is_constinit='constinit' in qualifiers,
                is_inline='inline' in qualifiers,
                is_thread_local='thread_local' in qualifiers,
                file=file_path,
                line_number=line_num,
            ))
        return globals_list

    def _extract_constants(self, content: str, file_path: str) -> List[CppConstantInfo]:
        """Extract constant definitions."""
        constants = []
        seen = set()

        # constexpr constants
        for match in self.CONSTEXPR_PATTERN.finditer(content):
            name = match.group('name')
            value = match.group('value').strip()
            ctype = match.group('type')
            line_num = content[:match.start()].count('\n') + 1
            key = f"constexpr:{name}"
            if key not in seen:
                seen.add(key)
                constants.append(CppConstantInfo(
                    name=name,
                    value=value[:100],
                    type=ctype,
                    kind='constexpr',
                    file=file_path,
                    line_number=line_num,
                ))

        # #define constants (but not macros)
        for match in re.finditer(r'^#\s*define\s+(\w+)\s+([^\n\\]+)', content, re.MULTILINE):
            name = match.group(1)
            value = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1
            # Skip function-like macros and include guards
            if '(' in name or name.endswith('_H') or name.endswith('_HPP') or name.startswith('_'):
                continue
            key = f"define:{name}"
            if key not in seen:
                seen.add(key)
                constants.append(CppConstantInfo(
                    name=name,
                    value=value[:100],
                    kind='define',
                    file=file_path,
                    line_number=line_num,
                ))

        return constants

    def _extract_design_patterns(self, content: str, file_path: str) -> List[CppDesignPatternInfo]:
        """Detect common design patterns."""
        patterns = []

        # Singleton
        for match in self.SINGLETON_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Find enclosing class
            class_match = re.search(r'class\s+(\w+)', content[:match.start()])
            class_name = class_match.group(1) if class_match else 'Unknown'
            patterns.append(CppDesignPatternInfo(
                pattern='singleton',
                class_name=class_name,
                confidence='high',
                file=file_path,
                line_number=line_num,
            ))

        # Factory
        for match in self.FACTORY_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            class_match = re.search(r'class\s+(\w+)', content[:match.start()])
            class_name = class_match.group(1) if class_match else 'Unknown'
            patterns.append(CppDesignPatternInfo(
                pattern='factory',
                class_name=class_name,
                confidence='medium',
                file=file_path,
                line_number=line_num,
            ))

        # Observer
        for match in self.OBSERVER_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            class_match = re.search(r'class\s+(\w+)', content[:match.start()])
            class_name = class_match.group(1) if class_match else 'Unknown'
            patterns.append(CppDesignPatternInfo(
                pattern='observer',
                class_name=class_name,
                confidence='medium',
                file=file_path,
                line_number=line_num,
            ))

        # Strategy
        for match in self.STRATEGY_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            class_match = re.search(r'class\s+(\w+)', content[:match.start()])
            class_name = class_match.group(1) if class_match else 'Unknown'
            patterns.append(CppDesignPatternInfo(
                pattern='strategy',
                class_name=class_name,
                confidence='medium',
                file=file_path,
                line_number=line_num,
            ))

        # Visitor
        for match in self.VISITOR_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            class_match = re.search(r'class\s+(\w+)', content[:match.start()])
            class_name = class_match.group(1) if class_match else 'Unknown'
            patterns.append(CppDesignPatternInfo(
                pattern='visitor',
                class_name=class_name,
                confidence='high',
                file=file_path,
                line_number=line_num,
            ))

        return patterns
