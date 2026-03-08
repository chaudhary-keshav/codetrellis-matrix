"""
CppAttributeExtractor - Extracts C++ preprocessor, attributes, modules, and includes.

This extractor parses C++ source code and extracts:
- Include directives (#include <...> and #include "...")
- Preprocessor macros (#define, function-like macros)
- Conditional compilation (#ifdef, #if, #elif, #else, #endif)
- Pragmas (#pragma once, #pragma pack, etc.)
- C++ attributes ([[nodiscard]], [[deprecated]], [[likely]], etc.)
- Static assertions (static_assert)
- Module declarations (C++20: import, export, module)
- Feature test macros (__has_include, __has_cpp_attribute)
- Compiler-specific extensions (__declspec, __attribute__)

Supports all C++ standards: C++98 through C++26.

Part of CodeTrellis v4.20 - C++ Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CppIncludeInfo:
    """Information about a C++ #include directive."""
    path: str
    is_system: bool = False  # <...> vs "..."
    file: str = ""
    line_number: int = 0


@dataclass
class CppMacroDefInfo:
    """Information about a C++ #define macro."""
    name: str
    body: Optional[str] = None
    is_function_like: bool = False
    params: List[str] = field(default_factory=list)
    is_multiline: bool = False
    is_variadic: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class CppConditionalBlockInfo:
    """Information about a preprocessor conditional block."""
    directive: str = ""  # ifdef, ifndef, if, elif, else, endif
    condition: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CppPragmaInfo:
    """Information about a #pragma directive."""
    directive: str = ""  # once, pack, comment, warning, etc.
    arguments: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CppAttributeInfo:
    """Information about a C++ attribute."""
    name: str = ""  # nodiscard, deprecated, likely, unlikely, etc.
    arguments: Optional[str] = None
    is_standard: bool = True  # [[...]] vs __attribute__ vs __declspec
    kind: str = "standard"  # standard, gcc, msvc
    file: str = ""
    line_number: int = 0


@dataclass
class CppStaticAssertInfo:
    """Information about a static_assert."""
    condition: str = ""
    message: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CppModuleInfo:
    """Information about a C++20 module declaration."""
    name: str = ""
    kind: str = "import"  # import, export, module
    is_partition: bool = False
    file: str = ""
    line_number: int = 0


class CppAttributeExtractor:
    """
    Extracts C++ preprocessor directives, attributes, and module declarations.

    Handles:
    - System and local #include directives
    - Object-like and function-like macros
    - Variadic macros
    - Conditional compilation blocks
    - #pragma directives
    - Standard C++ attributes ([[...]])
    - GCC __attribute__ and MSVC __declspec
    - static_assert
    - C++20 modules (import, export, module)
    - Feature test macros (__has_include, __has_cpp_attribute)
    """

    # Include pattern
    INCLUDE_PATTERN = re.compile(
        r'#\s*include\s+(?:(?P<system><[^>]+>)|(?P<local>"[^"]+"))',
        re.MULTILINE
    )

    # Macro definition
    MACRO_DEF_PATTERN = re.compile(
        r'#\s*define\s+(?P<name>\w+)'
        r'(?:\((?P<params>[^)]*)\))?\s*'
        r'(?P<body>(?:\\\n|[^\n])*)',
        re.MULTILINE
    )

    # Conditional compilation
    CONDITIONAL_PATTERN = re.compile(
        r'#\s*(?P<directive>ifdef|ifndef|if|elif|elifdef|elifndef|else|endif)\s*(?P<condition>[^\n]*)',
        re.MULTILINE
    )

    # Pragma
    PRAGMA_PATTERN = re.compile(
        r'#\s*pragma\s+(?P<directive>\w+)\s*(?P<args>[^\n]*)',
        re.MULTILINE
    )

    # Standard C++ attributes [[...]]
    STANDARD_ATTR_PATTERN = re.compile(
        r'\[\[\s*(?P<ns>\w+::)?(?P<name>[\w]+)(?:\s*\((?P<args>[^)]*)\))?\s*\]\]',
        re.MULTILINE
    )

    # GCC __attribute__
    GCC_ATTR_PATTERN = re.compile(
        r'__attribute__\s*\(\(\s*(?P<name>[\w]+)(?:\s*\((?P<args>[^)]*)\))?\s*\)\)',
        re.MULTILINE
    )

    # MSVC __declspec
    MSVC_ATTR_PATTERN = re.compile(
        r'__declspec\s*\(\s*(?P<name>[\w]+)(?:\s*\((?P<args>[^)]*)\))?\s*\)',
        re.MULTILINE
    )

    # static_assert
    STATIC_ASSERT_PATTERN = re.compile(
        r'static_assert\s*\(\s*(?P<condition>[^,)]+)(?:\s*,\s*(?P<message>[^)]+))?\s*\)\s*;',
        re.MULTILINE
    )

    # C++20 module declarations
    MODULE_PATTERN = re.compile(
        r'^(?P<export>export\s+)?(?P<kind>module|import)\s+(?P<name>[\w.:]+)\s*;',
        re.MULTILINE
    )

    # Feature test macros
    FEATURE_TEST_PATTERN = re.compile(
        r'(?:__has_include|__has_cpp_attribute|__cpp_\w+)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the C++ attribute extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all preprocessor and attribute information from C++ source code.

        Args:
            content: C++ source code content
            file_path: Path to source file

        Returns:
            Dict with 'includes', 'macros', 'conditionals', 'pragmas',
            'attributes', 'static_asserts', 'modules' lists
        """
        result = {
            'includes': [],
            'macros': [],
            'conditionals': [],
            'pragmas': [],
            'attributes': [],
            'static_asserts': [],
            'modules': [],
        }

        result['includes'] = self._extract_includes(content, file_path)
        result['macros'] = self._extract_macros(content, file_path)
        result['conditionals'] = self._extract_conditionals(content, file_path)
        result['pragmas'] = self._extract_pragmas(content, file_path)
        result['attributes'] = self._extract_attributes(content, file_path)
        result['static_asserts'] = self._extract_static_asserts(content, file_path)
        result['modules'] = self._extract_modules(content, file_path)

        return result

    def _extract_includes(self, content: str, file_path: str) -> List[CppIncludeInfo]:
        """Extract #include directives."""
        includes = []
        for match in self.INCLUDE_PATTERN.finditer(content):
            is_system = match.group('system') is not None
            path = (match.group('system') or match.group('local')).strip('<>"')
            line_num = content[:match.start()].count('\n') + 1
            includes.append(CppIncludeInfo(
                path=path,
                is_system=is_system,
                file=file_path,
                line_number=line_num,
            ))
        return includes

    def _extract_macros(self, content: str, file_path: str) -> List[CppMacroDefInfo]:
        """Extract #define macro definitions."""
        macros = []
        for match in self.MACRO_DEF_PATTERN.finditer(content):
            name = match.group('name')
            params_str = match.group('params')
            body = match.group('body').strip()
            line_num = content[:match.start()].count('\n') + 1

            is_function_like = params_str is not None
            params = []
            is_variadic = False
            if params_str:
                params = [p.strip() for p in params_str.split(',') if p.strip()]
                is_variadic = '...' in params_str

            is_multiline = '\\' in match.group(0)

            macros.append(CppMacroDefInfo(
                name=name,
                body=body[:200] if body else None,
                is_function_like=is_function_like,
                params=params,
                is_multiline=is_multiline,
                is_variadic=is_variadic,
                file=file_path,
                line_number=line_num,
            ))
        return macros

    def _extract_conditionals(self, content: str, file_path: str) -> List[CppConditionalBlockInfo]:
        """Extract conditional compilation blocks."""
        conditionals = []
        for match in self.CONDITIONAL_PATTERN.finditer(content):
            directive = match.group('directive')
            condition = match.group('condition').strip() or None
            line_num = content[:match.start()].count('\n') + 1
            conditionals.append(CppConditionalBlockInfo(
                directive=directive,
                condition=condition,
                file=file_path,
                line_number=line_num,
            ))
        return conditionals

    def _extract_pragmas(self, content: str, file_path: str) -> List[CppPragmaInfo]:
        """Extract #pragma directives."""
        pragmas = []
        for match in self.PRAGMA_PATTERN.finditer(content):
            directive = match.group('directive')
            args = match.group('args').strip() or None
            line_num = content[:match.start()].count('\n') + 1
            pragmas.append(CppPragmaInfo(
                directive=directive,
                arguments=args,
                file=file_path,
                line_number=line_num,
            ))
        return pragmas

    def _extract_attributes(self, content: str, file_path: str) -> List[CppAttributeInfo]:
        """Extract C++ attributes (standard, GCC, MSVC)."""
        attributes = []

        # Standard [[...]] attributes
        for match in self.STANDARD_ATTR_PATTERN.finditer(content):
            ns = match.group('ns')
            name = match.group('name')
            args = match.group('args')
            line_num = content[:match.start()].count('\n') + 1
            full_name = f"{ns}{name}" if ns else name
            attributes.append(CppAttributeInfo(
                name=full_name,
                arguments=args,
                is_standard=True,
                kind='standard',
                file=file_path,
                line_number=line_num,
            ))

        # GCC __attribute__
        for match in self.GCC_ATTR_PATTERN.finditer(content):
            name = match.group('name')
            args = match.group('args')
            line_num = content[:match.start()].count('\n') + 1
            attributes.append(CppAttributeInfo(
                name=name,
                arguments=args,
                is_standard=False,
                kind='gcc',
                file=file_path,
                line_number=line_num,
            ))

        # MSVC __declspec
        for match in self.MSVC_ATTR_PATTERN.finditer(content):
            name = match.group('name')
            args = match.group('args')
            line_num = content[:match.start()].count('\n') + 1
            attributes.append(CppAttributeInfo(
                name=name,
                arguments=args,
                is_standard=False,
                kind='msvc',
                file=file_path,
                line_number=line_num,
            ))

        return attributes

    def _extract_static_asserts(self, content: str, file_path: str) -> List[CppStaticAssertInfo]:
        """Extract static_assert declarations."""
        asserts = []
        for match in self.STATIC_ASSERT_PATTERN.finditer(content):
            condition = match.group('condition').strip()
            message = match.group('message')
            line_num = content[:match.start()].count('\n') + 1
            asserts.append(CppStaticAssertInfo(
                condition=condition,
                message=message.strip().strip('"') if message else None,
                file=file_path,
                line_number=line_num,
            ))
        return asserts

    def _extract_modules(self, content: str, file_path: str) -> List[CppModuleInfo]:
        """Extract C++20 module declarations."""
        modules = []
        for match in self.MODULE_PATTERN.finditer(content):
            kind = match.group('kind')
            name = match.group('name')
            is_export = match.group('export') is not None
            line_num = content[:match.start()].count('\n') + 1

            if is_export and kind == 'module':
                actual_kind = 'export_module'
            elif is_export:
                actual_kind = 'export_import'
            else:
                actual_kind = kind

            is_partition = ':' in name

            modules.append(CppModuleInfo(
                name=name,
                kind=actual_kind,
                is_partition=is_partition,
                file=file_path,
                line_number=line_num,
            ))
        return modules
