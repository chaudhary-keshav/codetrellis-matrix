"""
JavaScript Type Extractor for CodeTrellis

Extracts type definitions from JavaScript source code:
- ES6+ classes (class declarations, class expressions)
- Prototype-based constructors / pseudo-classes
- Symbol definitions
- Top-level constants (const enumerations, frozen objects)
- Property descriptors (Object.defineProperty / defineProperties)

Supports ES5 through ES2024+ (ES15):
- ES6 (2015): class, extends, Symbol, const/let
- ES2020: class fields, private fields (#), static fields
- ES2022: static blocks, #private methods
- ES2024+: decorators (Stage 3), explicit resource management

Part of CodeTrellis v4.30 - JavaScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JSPropertyInfo:
    """Information about a JavaScript class property or object key."""
    name: str
    type: str = ""  # inferred or JSDoc type
    default_value: Optional[str] = None
    is_static: bool = False
    is_private: bool = False
    is_readonly: bool = False
    is_computed: bool = False
    line_number: int = 0


@dataclass
class JSClassInfo:
    """Information about a JavaScript class definition."""
    name: str
    file: str = ""
    line_number: int = 0
    superclass: Optional[str] = None
    mixins: List[str] = field(default_factory=list)
    properties: List[JSPropertyInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    static_methods: List[str] = field(default_factory=list)
    private_methods: List[str] = field(default_factory=list)
    getters: List[str] = field(default_factory=list)
    setters: List[str] = field(default_factory=list)
    is_exported: bool = False
    is_default_export: bool = False
    is_abstract: bool = False  # via JSDoc @abstract
    decorators: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)  # via JSDoc @implements


@dataclass
class JSPrototypeInfo:
    """Information about a prototype-based constructor function / pseudo-class."""
    name: str
    file: str = ""
    line_number: int = 0
    prototype_methods: List[str] = field(default_factory=list)
    prototype_properties: List[str] = field(default_factory=list)
    is_exported: bool = False


@dataclass
class JSConstantInfo:
    """Information about a top-level constant or frozen object."""
    name: str
    file: str = ""
    line_number: int = 0
    kind: str = "const"  # const, Object.freeze, enum-like, scalar
    values: List[str] = field(default_factory=list)  # keys for enum-like objects
    value_type: str = ""  # number, string, boolean, null, unknown (for scalars)
    is_exported: bool = False
    is_frozen: bool = False


@dataclass
class JSSymbolInfo:
    """Information about a Symbol definition."""
    name: str
    file: str = ""
    line_number: int = 0
    description: str = ""
    is_exported: bool = False
    is_global: bool = False


class JavaScriptTypeExtractor:
    """
    Extracts type definitions from JavaScript source code.

    Detects:
    - ES6+ class declarations and expressions
    - Prototype-based constructor functions
    - Object.freeze / const enum-like patterns
    - Symbol definitions
    - Private fields (#) and static class features
    - Decorator patterns (Stage 3)
    """

    # ES6 class declaration / expression
    CLASS_DECL_PATTERN = re.compile(
        r'^[ \t]*(?:(?:export\s+(?:default\s+)?)?)'
        r'class\s+(\w+)'
        r'(?:\s+extends\s+([\w.]+))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Class expression assigned to variable
    CLASS_EXPR_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+(\w+)\s*=\s*class(?:\s+\w+)?\s*'
        r'(?:extends\s+([\w.]+)\s*)?\{',
        re.MULTILINE
    )

    # Prototype-based constructor function
    CONSTRUCTOR_FUNC_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+)?function\s+([A-Z]\w+)\s*\([^)]*\)\s*\{',
        re.MULTILINE
    )

    # Prototype method assignment
    PROTOTYPE_METHOD_PATTERN = re.compile(
        r'^[ \t]*(\w+)\.prototype\.(\w+)\s*=\s*function',
        re.MULTILINE
    )

    # Class method (inside class body)
    CLASS_METHOD_PATTERN = re.compile(
        r'^[ \t]*(?:(static|async|get|set)\s+)*'
        r'(?:(#)?(\w+|\[Symbol\.\w+\]))'
        r'\s*\([^)]*\)\s*\{',
        re.MULTILINE
    )

    # Class field (public or private)
    CLASS_FIELD_PATTERN = re.compile(
        r'^[ \t]*(static\s+)?'
        r'(#)?(\w+)\s*=\s*(.+?);\s*$',
        re.MULTILINE
    )

    # const enum-like: const FOO = Object.freeze({...}) or const FOO = {...}
    CONST_ENUM_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+)?const\s+([A-Z][A-Z_0-9]+)\s*=\s*'
        r'(?:Object\.freeze\(\s*)?'
        r'\{([^}]+)\}',
        re.MULTILINE
    )

    # Scalar UPPER_CASE constant: const MAX_RETRIES = 3;
    CONST_SCALAR_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+)?const\s+([A-Z][A-Z_0-9]{1,})\s*=\s*([^;{}\n]+)',
        re.MULTILINE
    )

    # Symbol definition
    SYMBOL_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*Symbol(?:\.for)?\s*\(\s*[\'"]([^"\']*)[\'"]',
        re.MULTILINE
    )

    # Export detection
    EXPORT_PATTERN = re.compile(r'^[ \t]*export\s+', re.MULTILINE)
    DEFAULT_EXPORT_PATTERN = re.compile(r'^[ \t]*export\s+default\s+', re.MULTILINE)

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all type definitions from JavaScript source code.

        Returns dict with keys: classes, prototypes, constants, symbols
        """
        classes = self._extract_classes(content, file_path)
        prototypes = self._extract_prototypes(content, file_path)
        constants = self._extract_constants(content, file_path)
        symbols = self._extract_symbols(content, file_path)

        return {
            'classes': classes,
            'prototypes': prototypes,
            'constants': constants,
            'symbols': symbols,
        }

    def _extract_classes(self, content: str, file_path: str) -> List[JSClassInfo]:
        """Extract ES6+ class definitions."""
        classes = []
        seen_names = set()

        # Class declarations
        for match in self.CLASS_DECL_PATTERN.finditer(content):
            name = match.group(1)
            superclass = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen_names:
                continue
            seen_names.add(name)

            # Determine export status
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))
            is_default = bool(re.search(r'\bexport\s+default\b', line_text))

            # Extract class body
            class_body = self._extract_brace_block(content, match.end() - 1)
            methods, static_methods, private_methods = [], [], []
            getters, setters = [], []
            properties = []

            if class_body:
                methods, static_methods, private_methods, getters, setters, properties = \
                    self._parse_class_body(class_body)

            classes.append(JSClassInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                superclass=superclass,
                properties=properties,
                methods=methods,
                static_methods=static_methods,
                private_methods=private_methods,
                getters=getters,
                setters=setters,
                is_exported=is_exported,
                is_default_export=is_default,
            ))

        # Class expressions
        for match in self.CLASS_EXPR_PATTERN.finditer(content):
            name = match.group(1)
            superclass = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen_names:
                continue
            seen_names.add(name)

            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))

            classes.append(JSClassInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                superclass=superclass,
                is_exported=is_exported,
            ))

        return classes

    def _parse_class_body(self, body: str):
        """Parse a class body to extract methods, properties, etc."""
        methods = []
        static_methods = []
        private_methods = []
        getters = []
        setters = []
        properties = []

        for line in body.split('\n'):
            stripped = line.strip()
            if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
                continue

            # Static method
            m = re.match(r'static\s+(?:async\s+)?(?:#)?(\w+)\s*\(', stripped)
            if m:
                name = m.group(1)
                if name != 'get' and name != 'set':
                    static_methods.append(name)
                continue

            # Getter
            m = re.match(r'(?:static\s+)?get\s+(?:#)?(\w+)\s*\(', stripped)
            if m:
                getters.append(m.group(1))
                continue

            # Setter
            m = re.match(r'(?:static\s+)?set\s+(?:#)?(\w+)\s*\(', stripped)
            if m:
                setters.append(m.group(1))
                continue

            # Private method
            m = re.match(r'(?:async\s+)?#(\w+)\s*\(', stripped)
            if m:
                private_methods.append('#' + m.group(1))
                continue

            # Regular method
            m = re.match(r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{', stripped)
            if m:
                name = m.group(1)
                if name not in ('if', 'for', 'while', 'switch', 'catch', 'constructor'):
                    methods.append(name)
                elif name == 'constructor':
                    methods.insert(0, 'constructor')
                continue

            # Class field
            m = re.match(r'(static\s+)?(#)?(\w+)\s*=\s*(.+?);\s*$', stripped)
            if m:
                is_static = bool(m.group(1))
                is_private = bool(m.group(2))
                prop_name = ('#' + m.group(3)) if is_private else m.group(3)
                properties.append(JSPropertyInfo(
                    name=prop_name,
                    default_value=m.group(4).strip(),
                    is_static=is_static,
                    is_private=is_private,
                ))
                continue

        return methods, static_methods, private_methods, getters, setters, properties

    def _extract_prototypes(self, content: str, file_path: str) -> List[JSPrototypeInfo]:
        """Extract prototype-based constructor functions."""
        prototypes = {}

        # Find constructor functions (capitalized function declarations)
        for match in self.CONSTRUCTOR_FUNC_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))

            if name not in prototypes:
                prototypes[name] = JSPrototypeInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    is_exported=is_exported,
                )

        # Collect prototype methods
        for match in self.PROTOTYPE_METHOD_PATTERN.finditer(content):
            ctor_name = match.group(1)
            method_name = match.group(2)
            if ctor_name in prototypes:
                prototypes[ctor_name].prototype_methods.append(method_name)
            else:
                prototypes[ctor_name] = JSPrototypeInfo(
                    name=ctor_name,
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                )
                prototypes[ctor_name].prototype_methods.append(method_name)

        return list(prototypes.values())

    def _extract_constants(self, content: str, file_path: str) -> List[JSConstantInfo]:
        """Extract enum-like constants (frozen objects, UPPER_CASE const objects)."""
        constants = []
        seen = set()

        for match in self.CONST_ENUM_PATTERN.finditer(content):
            name = match.group(1)
            body = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            # Extract keys from the object
            keys = re.findall(r'(\w+)\s*:', body)

            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))
            is_frozen = 'Object.freeze' in content[match.start():match.end() + 50]

            constants.append(JSConstantInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                kind='frozen_object' if is_frozen else 'const_object',
                values=keys,
                is_exported=is_exported,
                is_frozen=is_frozen,
            ))

        # Scalar UPPER_CASE constants (const MAX_RETRIES = 3)
        for match in self.CONST_SCALAR_PATTERN.finditer(content):
            name = match.group(1)
            value = match.group(2).strip().rstrip(';')
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            # Skip if already captured as object const
            # Determine value type
            value_type = "unknown"
            if re.match(r'^[\d.]+$', value):
                value_type = "number"
            elif re.match(r'^[\'"]', value):
                value_type = "string"
            elif value in ('true', 'false'):
                value_type = "boolean"
            elif value == 'null':
                value_type = "null"

            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))

            constants.append(JSConstantInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                kind='scalar',
                values=[],
                value_type=value_type,
                is_exported=is_exported,
                is_frozen=False,
            ))

        return constants

    def _extract_symbols(self, content: str, file_path: str) -> List[JSSymbolInfo]:
        """Extract Symbol definitions."""
        symbols = []

        for match in self.SYMBOL_PATTERN.finditer(content):
            name = match.group(1)
            desc = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_exported = bool(re.search(r'\bexport\b', line_text))

            # Detect Symbol.for (global symbols)
            match_text = content[match.start():match.end()]
            is_global = 'Symbol.for' in match_text

            symbols.append(JSSymbolInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                description=desc,
                is_exported=is_exported,
                is_global=is_global,
            ))

        return symbols

    def _extract_brace_block(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content between balanced braces starting at start_pos."""
        if start_pos >= len(content) or content[start_pos] != '{':
            return None

        depth = 0
        i = start_pos
        while i < len(content):
            ch = content[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[start_pos + 1:i]
            elif ch in ('"', "'", '`'):
                # Skip string literals
                quote = ch
                i += 1
                while i < len(content) and content[i] != quote:
                    if content[i] == '\\':
                        i += 1
                    i += 1
            elif ch == '/' and i + 1 < len(content):
                if content[i + 1] == '/':
                    # Line comment
                    while i < len(content) and content[i] != '\n':
                        i += 1
                elif content[i + 1] == '*':
                    # Block comment
                    i += 2
                    while i < len(content) - 1 and not (content[i] == '*' and content[i + 1] == '/'):
                        i += 1
                    i += 1
            i += 1

        return None
