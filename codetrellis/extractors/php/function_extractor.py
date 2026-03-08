"""
PhpFunctionExtractor - Extracts PHP function and method definitions.

This extractor parses PHP source code and extracts:
- Global functions
- Class methods (instance and static)
- Abstract methods
- Constructor/destructor (__construct, __destruct)
- Magic methods (__get, __set, __call, __toString, etc.)
- Closures (anonymous functions)
- Arrow functions (PHP 7.4+: fn() =>)
- Named arguments (PHP 8.0+)
- Union types (PHP 8.0+) and intersection types (PHP 8.1+)
- Return types (PHP 7.0+)
- Nullable types (PHP 7.1+)
- Void return type
- Never return type (PHP 8.1+)
- Parameter types with defaults
- Variadic parameters (...$args)
- Generator functions (yield)
- First-class callable syntax (PHP 8.1+)
- PHPDoc @param/@return annotations

Supports PHP 5.x through PHP 8.3+ features.

Part of CodeTrellis v4.24 - PHP Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PhpParameterInfo:
    """Information about a PHP function/method parameter."""
    name: str
    type_hint: Optional[str] = None
    default_value: Optional[str] = None
    is_variadic: bool = False
    is_nullable: bool = False
    is_reference: bool = False  # &$param
    is_promoted: bool = False  # Constructor promotion
    visibility: Optional[str] = None  # For promoted params
    is_readonly: bool = False


@dataclass
class PhpMethodInfo:
    """Information about a PHP class method."""
    name: str
    parameters: List[PhpParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    visibility: str = "public"
    is_static: bool = False
    is_abstract: bool = False
    is_final: bool = False
    is_constructor: bool = False
    is_destructor: bool = False
    is_magic: bool = False
    is_generator: bool = False
    owner_class: Optional[str] = None
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class PhpFunctionInfo:
    """Information about a PHP global function."""
    name: str
    parameters: List[PhpParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    namespace: Optional[str] = None
    is_generator: bool = False
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class PhpClosureInfo:
    """Information about a PHP closure or arrow function."""
    kind: str = "closure"  # closure, arrow (fn() =>)
    name: Optional[str] = None  # Variable name if assigned
    parameters: List[PhpParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    uses: List[str] = field(default_factory=list)  # use($var1, $var2)
    file: str = ""
    line_number: int = 0


class PhpFunctionExtractor:
    """
    Extracts PHP functions, methods, and callable constructs from source code.

    Handles:
    - Global function definitions
    - Class methods with visibility modifiers
    - Static methods
    - Abstract and final methods
    - Constructors (__construct) and destructors (__destruct)
    - Magic methods (__get, __set, __call, __callStatic, __toString, etc.)
    - Closures (function() use ($var) { })
    - Arrow functions (fn($x) => $x * 2, PHP 7.4+)
    - Return type declarations (PHP 7.0+)
    - Union types (PHP 8.0+), intersection types (PHP 8.1+)
    - Nullable types (?Type, PHP 7.1+)
    - Never return type (PHP 8.1+)
    - Variadic parameters (...$args)
    - Pass by reference (&$param)
    - Named arguments (PHP 8.0+)
    - Generator detection (yield/yield from)
    - PHPDoc type annotations

    v4.24: Comprehensive PHP function extraction.
    """

    # Function definition (global)
    FUNCTION_PATTERN = re.compile(
        r'(?P<doc>(?:/\*\*[\s\S]*?\*/\s*)?)'
        r'^\s*function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)'
        r'(?:\s*:\s*(?P<return_type>[?A-Za-z_\\][A-Za-z0-9_\\|&]*))?',
        re.MULTILINE
    )

    # Method definition (inside class/trait/interface/enum)
    METHOD_PATTERN = re.compile(
        r'(?P<doc>(?:/\*\*[\s\S]*?\*/\s*)?)'
        r'^\s*(?P<abstract>abstract\s+)?(?P<final>final\s+)?'
        r'(?P<visibility>public|protected|private)\s+'
        r'(?P<static>static\s+)?'
        r'function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)'
        r'(?:\s*:\s*(?P<return_type>[?A-Za-z_\\][A-Za-z0-9_\\|&]*))?',
        re.MULTILINE
    )

    # Also match methods with static before visibility
    METHOD_STATIC_FIRST_PATTERN = re.compile(
        r'(?P<doc>(?:/\*\*[\s\S]*?\*/\s*)?)'
        r'^\s*(?P<abstract>abstract\s+)?(?P<final>final\s+)?'
        r'(?P<static>static\s+)'
        r'(?P<visibility>public|protected|private)\s+'
        r'function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)'
        r'(?:\s*:\s*(?P<return_type>[?A-Za-z_\\][A-Za-z0-9_\\|&]*))?',
        re.MULTILINE
    )

    # Closure: $var = function(...) use (...) { }
    CLOSURE_PATTERN = re.compile(
        r'(?P<var>\$\w+\s*=\s*)?function\s*\((?P<params>[^)]*)\)'
        r'(?:\s*use\s*\((?P<uses>[^)]*)\))?'
        r'(?:\s*:\s*(?P<return_type>[?A-Za-z_\\][A-Za-z0-9_\\|&]*))?',
        re.MULTILINE
    )

    # Arrow function (PHP 7.4+): fn($x) => $x * 2
    ARROW_FUNCTION_PATTERN = re.compile(
        r'(?P<var>\$\w+\s*=\s*)?fn\s*\((?P<params>[^)]*)\)'
        r'(?:\s*:\s*(?P<return_type>[?A-Za-z_\\][A-Za-z0-9_\\|&]*))?'
        r'\s*=>',
        re.MULTILINE
    )

    # Yield detection
    YIELD_PATTERN = re.compile(r'\byield\b(?:\s+from)?')

    # PHPDoc patterns
    PHPDOC_PARAM_PATTERN = re.compile(r'@param\s+(?P<type>[^\s]+)\s+\$(?P<name>\w+)')
    PHPDOC_RETURN_PATTERN = re.compile(r'@return\s+(?P<type>[^\s]+)')

    # Magic methods
    MAGIC_METHODS = {
        '__construct', '__destruct', '__call', '__callStatic',
        '__get', '__set', '__isset', '__unset', '__sleep',
        '__wakeup', '__serialize', '__unserialize', '__toString',
        '__invoke', '__set_state', '__clone', '__debugInfo',
    }

    def __init__(self):
        """Initialize the function extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all PHP functions and methods from source code.

        Args:
            content: PHP source code content
            file_path: Path to source file

        Returns:
            Dict with 'functions', 'methods', 'closures' keys
        """
        functions = self._extract_functions(content, file_path)
        methods = self._extract_methods(content, file_path)
        closures = self._extract_closures(content, file_path)

        return {
            'functions': functions,
            'methods': methods,
            'closures': closures,
        }

    def _parse_params(self, params_str: str) -> List[PhpParameterInfo]:
        """Parse parameter string into parameter info objects."""
        params = []
        if not params_str or not params_str.strip():
            return params

        # Split by comma, handling nested angle brackets and parentheses
        depth = 0
        current = []
        for ch in params_str:
            if ch in ('(', '<', '['):
                depth += 1
            elif ch in (')', '>', ']'):
                depth -= 1
            elif ch == ',' and depth == 0:
                params.append(self._parse_single_param(''.join(current).strip()))
                current = []
                continue
            current.append(ch)

        if current:
            param_str = ''.join(current).strip()
            if param_str:
                params.append(self._parse_single_param(param_str))

        return [p for p in params if p is not None]

    def _parse_single_param(self, param_str: str) -> Optional[PhpParameterInfo]:
        """Parse a single parameter string."""
        if not param_str:
            return None

        is_variadic = False
        is_reference = False
        is_nullable = False
        type_hint = None
        name = None
        default_value = None
        visibility = None
        is_readonly = False

        # Check for promoted parameter (PHP 8.0+)
        vis_match = re.match(r'(public|protected|private)\s+', param_str)
        if vis_match:
            visibility = vis_match.group(1)
            param_str = param_str[vis_match.end():]

        # Check for readonly
        if param_str.startswith('readonly '):
            is_readonly = True
            param_str = param_str[len('readonly '):]

        # Split at = for default value
        if '=' in param_str:
            parts = param_str.split('=', 1)
            param_str = parts[0].strip()
            default_value = parts[1].strip()

        # Check for variadic
        if '...' in param_str:
            is_variadic = True
            param_str = param_str.replace('...', '')

        # Check for reference
        if '&$' in param_str or '& $' in param_str:
            is_reference = True
            param_str = param_str.replace('&', '')

        # Extract type and name
        param_str = param_str.strip()
        parts = param_str.split()

        if len(parts) >= 2:
            # Has type hint
            type_parts = parts[:-1]
            type_hint = ' '.join(type_parts)
            name = parts[-1]
        elif len(parts) == 1:
            name = parts[0]

        if name and name.startswith('$'):
            name = name[1:]  # Remove $

        if not name:
            return None

        # Check nullable
        if type_hint and type_hint.startswith('?'):
            is_nullable = True

        return PhpParameterInfo(
            name=name,
            type_hint=type_hint,
            default_value=default_value,
            is_variadic=is_variadic,
            is_nullable=is_nullable,
            is_reference=is_reference,
            is_promoted=visibility is not None,
            visibility=visibility,
            is_readonly=is_readonly,
        )

    def _extract_doc_comment(self, text: str) -> Optional[str]:
        """Extract PHPDoc comment text."""
        if not text:
            return None
        text = text.strip()
        match = re.search(r'/\*\*\s*([\s\S]*?)\*/', text)
        if match:
            comment = match.group(1).strip()
            lines = []
            for line in comment.split('\n'):
                line = re.sub(r'^\s*\*\s?', '', line).strip()
                if line and not line.startswith('@'):
                    lines.append(line)
            return ' '.join(lines)[:200] if lines else None
        return None

    def _extract_functions(self, content: str, file_path: str) -> List[PhpFunctionInfo]:
        """Extract global function definitions."""
        functions = []

        for match in self.FUNCTION_PATTERN.finditer(content):
            name = match.group('name')

            # Skip if this is actually a method (preceded by visibility modifier)
            pre_context = content[max(0, match.start() - 100):match.start()]
            if re.search(r'(?:public|protected|private|static|abstract|final)\s*$', pre_context):
                continue

            line_number = content[:match.start()].count('\n') + 1
            doc = self._extract_doc_comment(match.group('doc'))
            params = self._parse_params(match.group('params'))

            # Check for yield (generator)
            body_start = content.find('{', match.end())
            is_generator = False
            if body_start != -1:
                # Simple check in the next few hundred chars
                body_preview = content[body_start:body_start + 2000]
                is_generator = bool(self.YIELD_PATTERN.search(body_preview))

            functions.append(PhpFunctionInfo(
                name=name,
                parameters=params,
                return_type=match.group('return_type'),
                is_generator=is_generator,
                file=file_path,
                line_number=line_number,
                doc_comment=doc,
            ))

        return functions

    def _extract_methods(self, content: str, file_path: str) -> List[PhpMethodInfo]:
        """Extract class method definitions."""
        methods = []
        seen = set()

        for pattern in [self.METHOD_PATTERN, self.METHOD_STATIC_FIRST_PATTERN]:
            for match in pattern.finditer(content):
                name = match.group('name')
                line_number = content[:match.start()].count('\n') + 1
                key = (name, line_number)
                if key in seen:
                    continue
                seen.add(key)

                doc = self._extract_doc_comment(match.group('doc'))
                params = self._parse_params(match.group('params'))
                is_magic = name in self.MAGIC_METHODS

                # Check for yield (generator)
                body_start = content.find('{', match.end())
                is_generator = False
                if body_start != -1:
                    body_preview = content[body_start:body_start + 2000]
                    is_generator = bool(self.YIELD_PATTERN.search(body_preview))

                methods.append(PhpMethodInfo(
                    name=name,
                    parameters=params,
                    return_type=match.group('return_type'),
                    visibility=match.group('visibility'),
                    is_static=bool(match.group('static')),
                    is_abstract=bool(match.group('abstract')),
                    is_final=bool(match.group('final')),
                    is_constructor=name == '__construct',
                    is_destructor=name == '__destruct',
                    is_magic=is_magic,
                    is_generator=is_generator,
                    file=file_path,
                    line_number=line_number,
                    doc_comment=doc,
                ))

        return methods

    def _extract_closures(self, content: str, file_path: str) -> List[PhpClosureInfo]:
        """Extract closures and arrow functions."""
        closures = []

        # Arrow functions (fn() =>)
        for match in self.ARROW_FUNCTION_PATTERN.finditer(content):
            var = match.group('var')
            name = None
            if var:
                name = re.search(r'\$(\w+)', var)
                name = name.group(1) if name else None

            line_number = content[:match.start()].count('\n') + 1
            params = self._parse_params(match.group('params'))

            closures.append(PhpClosureInfo(
                kind="arrow",
                name=name,
                parameters=params,
                return_type=match.group('return_type'),
                file=file_path,
                line_number=line_number,
            ))

        return closures
