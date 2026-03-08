"""
CAttributeExtractor - Extracts C preprocessor directives, macros, and attributes.

This extractor parses C source code and extracts:
- #define macros (object-like and function-like)
- #include directives (system and local)
- Conditional compilation (#ifdef, #ifndef, #if, #elif, #else, #endif)
- #pragma directives (once, pack, warning, message)
- GCC __attribute__ usage (packed, aligned, deprecated, visibility, etc.)
- C23 [[attributes]] (nodiscard, deprecated, maybe_unused, fallthrough)
- _Static_assert / static_assert (C11/C23)
- _Generic selections (C11)

Supports all C standards: C89/C90, C99, C11, C17, C23.

Part of CodeTrellis v4.19 - C Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CMacroDefInfo:
    """Information about a C #define macro."""
    name: str
    value: Optional[str] = None
    is_function_like: bool = False
    parameters: List[str] = field(default_factory=list)
    is_variadic: bool = False  # Uses __VA_ARGS__
    is_include_guard: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class CIncludeInfo:
    """Information about a C #include directive."""
    path: str
    is_system: bool = False  # <...> vs "..."
    file: str = ""
    line_number: int = 0


@dataclass
class CConditionalBlockInfo:
    """Information about a conditional compilation block."""
    directive: str  # ifdef, ifndef, if, elif
    condition: str
    file: str = ""
    line_number: int = 0


@dataclass
class CPragmaInfo:
    """Information about a #pragma directive."""
    directive: str  # once, pack, warning, message, GCC, clang
    value: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CAttributeInfo:
    """Information about a C attribute (GCC __attribute__ or C23 [[...]])."""
    name: str
    args: Optional[str] = None
    kind: str = "gcc"  # gcc, c23, msvc
    target: Optional[str] = None  # What it's applied to (function name, struct name)
    file: str = ""
    line_number: int = 0


@dataclass
class CStaticAssertInfo:
    """Information about a _Static_assert / static_assert."""
    condition: str
    message: Optional[str] = None
    file: str = ""
    line_number: int = 0


class CAttributeExtractor:
    """
    Extracts C preprocessor directives, macros, and attributes.

    Handles:
    - Object-like and function-like macros (#define)
    - System and local includes (#include)
    - Conditional compilation (#ifdef, #if, etc.)
    - Pragmas (#pragma once, pack, etc.)
    - GCC __attribute__ specifications
    - C23 standard attributes [[...]]
    - MSVC __declspec
    - _Static_assert / static_assert
    """

    # #define patterns
    DEFINE_FUNC = re.compile(
        r'^\s*#\s*define\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*(?P<body>[^\n\\]*(?:\\\n[^\n]*)*)',
        re.MULTILINE
    )

    DEFINE_OBJ = re.compile(
        r'^\s*#\s*define\s+(?P<name>\w+)(?:\s+(?P<value>[^\n\\]+(?:\\\n[^\n]*)*))?',
        re.MULTILINE
    )

    # #include pattern
    INCLUDE_PATTERN = re.compile(
        r'^\s*#\s*include\s+(?:(?P<system><[^>]+>)|(?P<local>"[^"]+"))',
        re.MULTILINE
    )

    # Conditional compilation
    CONDITIONAL_PATTERN = re.compile(
        r'^\s*#\s*(?P<directive>ifdef|ifndef|if|elif|else|endif)\s*(?P<cond>[^\n]*)?',
        re.MULTILINE
    )

    # #pragma
    PRAGMA_PATTERN = re.compile(
        r'^\s*#\s*pragma\s+(?P<body>[^\n]+)',
        re.MULTILINE
    )

    # GCC __attribute__
    GCC_ATTR_PATTERN = re.compile(
        r'__attribute__\s*\(\(\s*(?P<attrs>[^)]+)\s*\)\)',
        re.MULTILINE
    )

    # C23 [[attribute]]
    C23_ATTR_PATTERN = re.compile(
        r'\[\[\s*(?P<attrs>[^\]]+)\s*\]\]',
        re.MULTILINE
    )

    # MSVC __declspec
    DECLSPEC_PATTERN = re.compile(
        r'__declspec\s*\(\s*(?P<spec>[^)]+)\s*\)',
        re.MULTILINE
    )

    # _Static_assert / static_assert
    STATIC_ASSERT_PATTERN = re.compile(
        r'\b(?:_Static_assert|static_assert)\s*\(\s*(?P<cond>[^,]+)\s*(?:,\s*(?P<msg>"[^"]*"))?\s*\)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the C attribute extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all C preprocessor directives, macros, and attributes.

        Args:
            content: C source code content
            file_path: Path to source file

        Returns:
            Dict with 'macros', 'includes', 'conditionals', 'pragmas',
                  'attributes', 'static_asserts' keys
        """
        macros = self._extract_macros(content, file_path)
        includes = self._extract_includes(content, file_path)
        conditionals = self._extract_conditionals(content, file_path)
        pragmas = self._extract_pragmas(content, file_path)
        attributes = self._extract_attributes(content, file_path)
        static_asserts = self._extract_static_asserts(content, file_path)

        return {
            'macros': macros,
            'includes': includes,
            'conditionals': conditionals,
            'pragmas': pragmas,
            'attributes': attributes,
            'static_asserts': static_asserts,
        }

    def _get_line_number(self, content: str, pos: int) -> int:
        return content[:pos].count('\n') + 1

    def _extract_macros(self, content: str, file_path: str) -> List[CMacroDefInfo]:
        """Extract #define macros."""
        macros = []
        seen = set()

        # Function-like macros first
        for match in self.DEFINE_FUNC.finditer(content):
            name = match.group('name')
            if name in seen:
                continue
            seen.add(name)
            params_str = match.group('params').strip()
            params = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []
            body = match.group('body').strip() if match.group('body') else ''
            is_variadic = '...' in params_str or '__VA_ARGS__' in body

            macros.append(CMacroDefInfo(
                name=name,
                value=body[:100] if body else None,
                is_function_like=True,
                parameters=params,
                is_variadic=is_variadic,
                file=file_path,
                line_number=self._get_line_number(content, match.start()),
            ))

        # Object-like macros
        for match in self.DEFINE_OBJ.finditer(content):
            name = match.group('name')
            if name in seen:
                continue
            seen.add(name)
            value = match.group('value').strip() if match.group('value') else None

            is_guard = (name.endswith('_H') or name.endswith('_H_') or
                       name.endswith('_INCLUDED') or name.startswith('_'))

            macros.append(CMacroDefInfo(
                name=name,
                value=value[:100] if value else None,
                is_function_like=False,
                is_include_guard=is_guard,
                file=file_path,
                line_number=self._get_line_number(content, match.start()),
            ))

        return macros

    def _extract_includes(self, content: str, file_path: str) -> List[CIncludeInfo]:
        """Extract #include directives."""
        includes = []
        for match in self.INCLUDE_PATTERN.finditer(content):
            if match.group('system'):
                path = match.group('system').strip('<>')
                is_system = True
            else:
                path = match.group('local').strip('"')
                is_system = False

            includes.append(CIncludeInfo(
                path=path,
                is_system=is_system,
                file=file_path,
                line_number=self._get_line_number(content, match.start()),
            ))
        return includes

    def _extract_conditionals(self, content: str, file_path: str) -> List[CConditionalBlockInfo]:
        """Extract conditional compilation blocks."""
        blocks = []
        for match in self.CONDITIONAL_PATTERN.finditer(content):
            directive = match.group('directive')
            cond = match.group('cond').strip() if match.group('cond') else ''

            # Skip #else and #endif (they don't have conditions, just markers)
            if directive in ('else', 'endif'):
                continue

            blocks.append(CConditionalBlockInfo(
                directive=directive,
                condition=cond,
                file=file_path,
                line_number=self._get_line_number(content, match.start()),
            ))
        return blocks

    def _extract_pragmas(self, content: str, file_path: str) -> List[CPragmaInfo]:
        """Extract #pragma directives."""
        pragmas = []
        for match in self.PRAGMA_PATTERN.finditer(content):
            body = match.group('body').strip()
            directive = body.split()[0] if body.split() else body
            value = ' '.join(body.split()[1:]) if len(body.split()) > 1 else None

            pragmas.append(CPragmaInfo(
                directive=directive,
                value=value,
                file=file_path,
                line_number=self._get_line_number(content, match.start()),
            ))
        return pragmas

    def _extract_attributes(self, content: str, file_path: str) -> List[CAttributeInfo]:
        """Extract GCC __attribute__, C23 [[]], and MSVC __declspec."""
        attributes = []

        # GCC attributes
        for match in self.GCC_ATTR_PATTERN.finditer(content):
            attrs_str = match.group('attrs').strip()
            for attr in re.split(r'\s*,\s*', attrs_str):
                attr = attr.strip()
                if not attr:
                    continue
                attr_match = re.match(r'(\w+)(?:\(([^)]*)\))?', attr)
                if attr_match:
                    attributes.append(CAttributeInfo(
                        name=attr_match.group(1),
                        args=attr_match.group(2) if attr_match.group(2) else None,
                        kind='gcc',
                        file=file_path,
                        line_number=self._get_line_number(content, match.start()),
                    ))

        # C23 attributes
        for match in self.C23_ATTR_PATTERN.finditer(content):
            attrs_str = match.group('attrs').strip()
            for attr in re.split(r'\s*,\s*', attrs_str):
                attr = attr.strip()
                if not attr:
                    continue
                attr_match = re.match(r'(\w+)(?:\(([^)]*)\))?', attr)
                if attr_match:
                    attributes.append(CAttributeInfo(
                        name=attr_match.group(1),
                        args=attr_match.group(2) if attr_match.group(2) else None,
                        kind='c23',
                        file=file_path,
                        line_number=self._get_line_number(content, match.start()),
                    ))

        # MSVC __declspec
        for match in self.DECLSPEC_PATTERN.finditer(content):
            spec = match.group('spec').strip()
            attributes.append(CAttributeInfo(
                name=spec,
                kind='msvc',
                file=file_path,
                line_number=self._get_line_number(content, match.start()),
            ))

        return attributes

    def _extract_static_asserts(self, content: str, file_path: str) -> List[CStaticAssertInfo]:
        """Extract _Static_assert / static_assert."""
        asserts = []
        for match in self.STATIC_ASSERT_PATTERN.finditer(content):
            cond = match.group('cond').strip()
            msg = match.group('msg').strip('"') if match.group('msg') else None
            asserts.append(CStaticAssertInfo(
                condition=cond,
                message=msg,
                file=file_path,
                line_number=self._get_line_number(content, match.start()),
            ))
        return asserts
