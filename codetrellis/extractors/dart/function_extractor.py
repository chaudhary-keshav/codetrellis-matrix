"""
Dart Function Extractor for CodeTrellis

Extracts function and method definitions from Dart source code:
- Top-level functions
- Instance methods
- Static methods
- Constructors (named, factory, const, redirecting)
- Getters and setters
- Operator overloads
- Extension methods
- Async/generator functions (async, async*, sync*)

Supports Dart 2.0 through Dart 3.x+ features including:
- Null safety parameters (required keyword, ? nullable)
- Named parameters with defaults
- Records as return types (Dart 3.0+)
- Patterns in function signatures (Dart 3.0+)

Part of CodeTrellis v4.27 - Dart Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DartParameterInfo:
    """Information about a function/method parameter."""
    name: str
    type: str = ""
    is_required: bool = False
    is_named: bool = False
    is_positional: bool = True
    is_nullable: bool = False
    default_value: str = ""
    line_number: int = 0


@dataclass
class DartFunctionInfo:
    """Information about a top-level function."""
    name: str
    file: str = ""
    return_type: str = ""
    parameters: List[DartParameterInfo] = field(default_factory=list)
    is_async: bool = False
    is_async_star: bool = False
    is_sync_star: bool = False
    is_generator: bool = False
    is_external: bool = False
    annotations: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class DartMethodInfo:
    """Information about a class/mixin method."""
    name: str
    class_name: str = ""
    file: str = ""
    return_type: str = ""
    parameters: List[DartParameterInfo] = field(default_factory=list)
    is_static: bool = False
    is_abstract: bool = False
    is_async: bool = False
    is_async_star: bool = False
    is_sync_star: bool = False
    is_override: bool = False
    is_external: bool = False
    is_getter: bool = False
    is_setter: bool = False
    is_operator: bool = False
    annotations: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class DartConstructorInfo:
    """Information about a constructor."""
    class_name: str
    name: str = ""  # Named constructor name (empty for default)
    file: str = ""
    parameters: List[DartParameterInfo] = field(default_factory=list)
    is_const: bool = False
    is_factory: bool = False
    is_external: bool = False
    is_named: bool = False
    redirects_to: str = ""
    annotations: List[str] = field(default_factory=list)
    line_number: int = 0


class DartFunctionExtractor:
    """
    Extracts Dart function and method definitions using regex-based parsing.

    Supports:
    - Top-level functions (async, async*, sync*)
    - Instance methods with return types
    - Static methods
    - Constructors (default, named, factory, const, redirecting)
    - Getters and setters
    - Operator overloads
    - External functions/methods
    """

    # Top-level function pattern
    FUNCTION_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<external>external)\s+)?'
        r'(?:(?P<return_type>(?:Future|Stream|FutureOr|Iterable|List|Map|Set|void|int|double|String|bool|dynamic|num|Never|Object|Record)\w*(?:<[^>]+>)?(?:\?)?)\s+)?'
        r'(?P<name>\w+)\s*'
        r'(?:<(?P<generics>[^>]+)>\s*)?'
        r'\((?P<params>[^)]*)\)\s*'
        r'(?:(?P<async>async\*?|sync\*)\s*)?'
        r'[{=;]',
        re.MULTILINE
    )

    # Method pattern (inside class/mixin body — context-free regex)
    METHOD_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<static>static)\s+)?'
        r'(?:(?P<external>external)\s+)?'
        r'(?:(?P<return_type>(?:\w+(?:<[^>]+>)?(?:\?)?\s+)))?'
        r'(?P<name>\w+)\s*'
        r'(?:<(?P<generics>[^>]+)>\s*)?'
        r'\((?P<params>[^)]*)\)\s*'
        r'(?:(?P<async>async\*?|sync\*)\s*)?'
        r'[{=;]',
        re.MULTILINE
    )

    # Getter pattern
    GETTER_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<static>static)\s+)?'
        r'(?:(?P<external>external)\s+)?'
        r'(?:(?P<return_type>\w+(?:<[^>]+>)?(?:\?)?)\s+)?'
        r'get\s+(?P<name>\w+)\s*'
        r'(?:[{=;])',
        re.MULTILINE
    )

    # Setter pattern
    SETTER_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<static>static)\s+)?'
        r'(?:(?P<external>external)\s+)?'
        r'set\s+(?P<name>\w+)\s*'
        r'\((?P<params>[^)]+)\)\s*[{=;]',
        re.MULTILINE
    )

    # Constructor pattern
    CONSTRUCTOR_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<annotations>(?:@\w+(?:\([^)]*\))?\s+)*))?'
        r'(?:(?P<external>external)\s+)?'
        r'(?:(?P<const>const)\s+)?'
        r'(?:(?P<factory>factory)\s+)?'
        r'(?P<class_name>\w+)'
        r'(?:\.(?P<named>\w+))?'
        r'\s*\((?P<params>[^)]*)\)',
        re.MULTILINE
    )

    # Operator overload pattern
    OPERATOR_PATTERN = re.compile(
        r'^\s*'
        r'(?:(?P<return_type>\w+(?:<[^>]+>)?(?:\?)?)\s+)?'
        r'operator\s*(?P<op>[\+\-\*\/\%\~\&\|\^\<\>\=\[\]]+)\s*'
        r'\((?P<params>[^)]*)\)\s*[{=;]',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all function/method definitions from Dart source code.

        Returns:
            Dict with 'functions', 'methods', 'constructors',
            'getters', 'setters' lists.
        """
        result: Dict[str, Any] = {
            'functions': [],
            'methods': [],
            'constructors': [],
            'getters': [],
            'setters': [],
        }

        # Determine class context for constructor detection
        class_names = set()
        class_pattern = re.compile(r'\bclass\s+(\w+)', re.MULTILINE)
        for m in class_pattern.finditer(content):
            class_names.add(m.group(1))

        # Extract top-level functions (not inside class bodies)
        result['functions'] = self._extract_functions(content, file_path, class_names)

        # Extract constructors
        result['constructors'] = self._extract_constructors(content, file_path, class_names)

        # Extract getters
        result['getters'] = self._extract_getters(content, file_path)

        # Extract setters
        result['setters'] = self._extract_setters(content, file_path)

        return result

    def _parse_parameters(self, params_str: str) -> List[DartParameterInfo]:
        """Parse parameter string into structured parameter info."""
        params = []
        if not params_str or not params_str.strip():
            return params

        # Handle named parameters {required Type name, ...}
        # Handle positional optional parameters [Type name = default, ...]
        current_section = "positional"
        param_text = params_str.strip()

        # Split respecting generics and braces
        parts = self._split_params(param_text)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if part == '{':
                current_section = "named"
                continue
            if part == '}':
                current_section = "positional"
                continue
            if part == '[':
                current_section = "optional_positional"
                continue
            if part == ']':
                current_section = "positional"
                continue

            # Parse individual parameter
            p = self._parse_single_param(part, current_section)
            if p:
                params.append(p)

        return params[:15]

    def _parse_single_param(self, param: str, section: str) -> Optional[DartParameterInfo]:
        """Parse a single parameter."""
        param = param.strip()
        if not param:
            return None

        is_required = False
        is_named = section == "named"
        is_positional = section != "named"

        # Check for 'required' keyword
        if param.startswith('required '):
            is_required = True
            param = param[9:].strip()

        # Check for annotations
        while param.startswith('@'):
            # Skip annotation
            space_idx = param.find(' ')
            if space_idx > 0:
                param = param[space_idx:].strip()
            else:
                break

        # Handle 'this.name' and 'super.name' shorthand
        if param.startswith('this.') or param.startswith('super.'):
            parts = param.split('=', 1)
            name = parts[0].strip().split('.')[-1]
            default = parts[1].strip() if len(parts) > 1 else ""
            return DartParameterInfo(
                name=name,
                type="",
                is_required=is_required or section == "positional",
                is_named=is_named,
                is_positional=is_positional,
                default_value=default,
            )

        # Split on '=' for default value
        parts = param.split('=', 1)
        param_decl = parts[0].strip()
        default_value = parts[1].strip() if len(parts) > 1 else ""

        # Parse 'Type name' or 'Type? name' or just 'name'
        tokens = param_decl.rsplit(None, 1)
        if len(tokens) == 2:
            ptype = tokens[0].strip()
            pname = tokens[1].strip()
        elif len(tokens) == 1:
            ptype = ""
            pname = tokens[0].strip()
        else:
            return None

        is_nullable = ptype.endswith('?') if ptype else False

        return DartParameterInfo(
            name=pname,
            type=ptype,
            is_required=is_required or (section == "positional" and not default_value),
            is_named=is_named,
            is_positional=is_positional,
            is_nullable=is_nullable,
            default_value=default_value,
        )

    def _split_params(self, text: str) -> List[str]:
        """Split parameter text respecting generics, braces, and brackets."""
        parts = []
        current = []
        depth = 0
        i = 0
        while i < len(text):
            ch = text[i]
            if ch in '<({[':
                if ch in '{[' and depth == 0:
                    if current:
                        parts.append(''.join(current).strip())
                        current = []
                    parts.append(ch)
                    i += 1
                    continue
                depth += 1
                current.append(ch)
            elif ch in '>)}]':
                if ch in '}]' and depth == 0:
                    if current:
                        parts.append(''.join(current).strip())
                        current = []
                    parts.append(ch)
                    i += 1
                    continue
                depth -= 1
                current.append(ch)
            elif ch == ',' and depth == 0:
                if current:
                    parts.append(''.join(current).strip())
                    current = []
            else:
                current.append(ch)
            i += 1

        if current:
            parts.append(''.join(current).strip())

        return parts

    def _extract_functions(self, content: str, file_path: str,
                          class_names: set) -> List[DartFunctionInfo]:
        """Extract top-level function declarations."""
        functions = []

        for match in self.FUNCTION_PATTERN.finditer(content):
            name = match.group('name')

            # Skip if name is a known class (constructor)
            if name in class_names:
                continue
            # Skip keywords
            if name in ('if', 'else', 'for', 'while', 'switch', 'return', 'try',
                       'catch', 'finally', 'throw', 'new', 'const', 'var', 'final',
                       'class', 'enum', 'mixin', 'extension', 'import', 'export',
                       'part', 'library', 'typedef', 'abstract', 'get', 'set'):
                continue

            return_type = match.group('return_type') or ""
            return_type = return_type.strip()

            params = self._parse_parameters(match.group('params'))

            annotations = []
            if match.group('annotations'):
                annotations = re.findall(r'@(\w+)', match.group('annotations'))

            generics = []
            if match.group('generics'):
                generics = [g.strip() for g in match.group('generics').split(',')]

            async_str = match.group('async') or ""
            is_async = async_str == 'async'
            is_async_star = async_str == 'async*'
            is_sync_star = async_str == 'sync*'

            func = DartFunctionInfo(
                name=name,
                file=file_path,
                return_type=return_type,
                parameters=params,
                is_async=is_async,
                is_async_star=is_async_star,
                is_sync_star=is_sync_star,
                is_external=bool(match.group('external')),
                annotations=annotations,
                generic_params=generics,
                line_number=content[:match.start()].count('\n') + 1,
            )
            functions.append(func)

        return functions

    def _extract_constructors(self, content: str, file_path: str,
                              class_names: set) -> List[DartConstructorInfo]:
        """Extract constructor declarations."""
        constructors = []

        for match in self.CONSTRUCTOR_PATTERN.finditer(content):
            class_name = match.group('class_name')
            if class_name not in class_names:
                continue

            named = match.group('named') or ""
            params = self._parse_parameters(match.group('params'))

            annotations = []
            if match.group('annotations'):
                annotations = re.findall(r'@(\w+)', match.group('annotations'))

            ctor = DartConstructorInfo(
                class_name=class_name,
                name=named,
                file=file_path,
                parameters=params,
                is_const=bool(match.group('const')),
                is_factory=bool(match.group('factory')),
                is_external=bool(match.group('external')),
                is_named=bool(named),
                annotations=annotations,
                line_number=content[:match.start()].count('\n') + 1,
            )
            constructors.append(ctor)

        return constructors

    def _extract_getters(self, content: str, file_path: str) -> List[DartMethodInfo]:
        """Extract getter declarations."""
        getters = []

        for match in self.GETTER_PATTERN.finditer(content):
            name = match.group('name')
            return_type = match.group('return_type') or ""

            annotations = []
            if match.group('annotations'):
                annotations = re.findall(r'@(\w+)', match.group('annotations'))

            is_override = 'override' in annotations

            getter = DartMethodInfo(
                name=name,
                file=file_path,
                return_type=return_type.strip(),
                is_static=bool(match.group('static')),
                is_getter=True,
                is_override=is_override,
                is_external=bool(match.group('external')),
                annotations=annotations,
                line_number=content[:match.start()].count('\n') + 1,
            )
            getters.append(getter)

        return getters

    def _extract_setters(self, content: str, file_path: str) -> List[DartMethodInfo]:
        """Extract setter declarations."""
        setters = []

        for match in self.SETTER_PATTERN.finditer(content):
            name = match.group('name')
            params = self._parse_parameters(match.group('params'))

            annotations = []
            if match.group('annotations'):
                annotations = re.findall(r'@(\w+)', match.group('annotations'))

            setter = DartMethodInfo(
                name=name,
                file=file_path,
                parameters=params,
                is_static=bool(match.group('static')),
                is_setter=True,
                is_external=bool(match.group('external')),
                annotations=annotations,
                line_number=content[:match.start()].count('\n') + 1,
            )
            setters.append(setter)

        return setters
