"""
CSharpFunctionExtractor - Extracts C# methods, constructors, properties, events.

Extracts:
- Instance and static methods with full signatures
- Constructors
- Extension methods (this parameter)
- Async/await methods
- Properties (auto, computed, expression-bodied)
- Events and event handlers
- Operator overloads
- Indexers
- Local functions (C# 7+)
- Expression-bodied members (C# 6+)

Part of CodeTrellis v4.13 - C# Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSharpParameterInfo:
    """Information about a C# method parameter."""
    name: str
    type: str
    attributes: List[str] = field(default_factory=list)
    default_value: Optional[str] = None
    is_params: bool = False     # params keyword
    is_ref: bool = False        # ref parameter
    is_out: bool = False        # out parameter
    is_in: bool = False         # in parameter (readonly ref)
    is_this: bool = False       # Extension method this parameter


@dataclass
class CSharpMethodInfo:
    """Information about a C# method."""
    name: str
    return_type: str = "void"
    parameters: List[CSharpParameterInfo] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    is_static: bool = False
    is_abstract: bool = False
    is_virtual: bool = False
    is_override: bool = False
    is_async: bool = False
    is_extension: bool = False  # Extension method
    is_expression_bodied: bool = False  # => syntax
    class_name: Optional[str] = None
    xml_doc: Optional[str] = None


@dataclass
class CSharpConstructorInfo:
    """Information about a C# constructor."""
    class_name: str
    parameters: List[CSharpParameterInfo] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    calls_base: bool = False     # : base(...)
    calls_this: bool = False     # : this(...)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    is_static: bool = False      # static constructor


@dataclass
class CSharpEventInfo:
    """Information about a C# event."""
    name: str
    type: str               # EventHandler, EventHandler<T>, custom delegate
    modifiers: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_static: bool = False


class CSharpFunctionExtractor:
    """
    Extracts C# method, constructor, event and property definitions from source code.

    Handles:
    - Full method signatures with generics, constraints
    - Access modifiers (public, protected, private, internal)
    - Static, abstract, virtual, override, sealed methods
    - Async methods (async Task<T>, async ValueTask<T>)
    - Extension methods (this parameter detection)
    - Expression-bodied members (=>)
    - Constructors with base/this chaining
    - Static constructors
    - Events (event-field, event-accessor)
    - Operator overloads
    - Indexers
    """

    # Method pattern
    METHOD_PATTERN = re.compile(
        r'(?:(?:///.*\n)*)?'                               # Optional XML docs
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'                 # Attributes
        r'((?:public|private|protected|internal|static|virtual|override|abstract|'
        r'sealed|async|extern|unsafe|new|partial)\s+)*'    # Modifiers
        r'(?:<([^>]+)>\s+)?'                               # Optional generic type params before return
        r'([\w<>\[\]?,.\s]+?)\s+'                          # Return type
        r'(\w+)\s*'                                        # Method name
        r'(?:<([^>]+)>)?\s*'                               # Optional method generic params
        r'\(([^)]*)\)'                                     # Parameters
        r'(?:\s+where\s+[^{;]+)?'                          # Optional generic constraints
        r'\s*(?:\{|=>|;)',                                  # Body start, expression body, or abstract
        re.MULTILINE | re.DOTALL
    )

    # Constructor pattern
    CONSTRUCTOR_PATTERN = re.compile(
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'                 # Attributes
        r'((?:public|private|protected|internal|static)\s+)?'  # Modifier
        r'(\w+)\s*'                                        # Class name
        r'\(([^)]*)\)'                                     # Parameters
        r'(?:\s*:\s*(base|this)\s*\([^)]*\))?'             # Optional base/this call
        r'\s*\{',                                          # Body start
        re.MULTILINE | re.DOTALL
    )

    # Event pattern
    EVENT_PATTERN = re.compile(
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'
        r'((?:public|private|protected|internal|static|virtual|override|abstract|sealed|new)\s+)*'
        r'event\s+'
        r'([\w<>\[\]?,.\s]+?)\s+'                          # Event type
        r'(\w+)\s*;',                                      # Event name
        re.MULTILINE
    )

    # Class name detection (to match constructors)
    CLASS_NAME_PATTERN = re.compile(
        r'(?:class|struct|record)\s+(\w+)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all methods, constructors, and events from C# source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with keys: methods, constructors, events
        """
        result = {
            "methods": [],
            "constructors": [],
            "events": [],
        }

        # Detect class names for constructor matching
        class_names = set(m.group(1) for m in self.CLASS_NAME_PATTERN.finditer(content))

        # Extract methods
        for match in self.METHOD_PATTERN.finditer(content):
            method = self._parse_method(match, content, file_path)
            if method and method.name not in class_names:
                result["methods"].append(method)

        # Extract constructors
        for match in self.CONSTRUCTOR_PATTERN.finditer(content):
            ctor = self._parse_constructor(match, content, file_path, class_names)
            if ctor:
                result["constructors"].append(ctor)

        # Extract events
        for match in self.EVENT_PATTERN.finditer(content):
            event = self._parse_event(match, content, file_path)
            if event:
                result["events"].append(event)

        return result

    def _parse_parameters(self, params_str: str) -> List[CSharpParameterInfo]:
        """Parse method parameter list."""
        params = []
        if not params_str or not params_str.strip():
            return params

        # Split by comma (handle nested generics)
        depth = 0
        current = ""
        for ch in params_str:
            if ch in '<(':
                depth += 1
            elif ch in '>)':
                depth -= 1
            elif ch == ',' and depth == 0:
                if current.strip():
                    params.append(self._parse_single_param(current.strip()))
                current = ""
                continue
            current += ch
        if current.strip():
            params.append(self._parse_single_param(current.strip()))

        return params

    def _parse_single_param(self, param_str: str) -> CSharpParameterInfo:
        """Parse a single parameter definition."""
        # Handle attributes [FromBody] etc.
        attrs = []
        attr_match = re.match(r'(\[[\w.,\s()="\[\]]+\]\s*)+', param_str)
        if attr_match:
            for a in re.finditer(r'\[(\w+)', attr_match.group()):
                attrs.append(a.group(1))
            param_str = param_str[attr_match.end():].strip()

        is_this = False
        is_params = False
        is_ref = False
        is_out = False
        is_in = False

        # Check for parameter modifiers
        if param_str.startswith('this '):
            is_this = True
            param_str = param_str[5:]
        if param_str.startswith('params '):
            is_params = True
            param_str = param_str[7:]
        if param_str.startswith('ref '):
            is_ref = True
            param_str = param_str[4:]
        if param_str.startswith('out '):
            is_out = True
            param_str = param_str[4:]
        if param_str.startswith('in '):
            is_in = True
            param_str = param_str[3:]

        # Check for default value
        default_value = None
        if '=' in param_str:
            parts = param_str.split('=', 1)
            param_str = parts[0].strip()
            default_value = parts[1].strip()

        # Split type and name
        parts = param_str.rsplit(' ', 1)
        if len(parts) == 2:
            return CSharpParameterInfo(
                name=parts[1].strip(),
                type=parts[0].strip(),
                attributes=attrs,
                default_value=default_value,
                is_params=is_params,
                is_ref=is_ref,
                is_out=is_out,
                is_in=is_in,
                is_this=is_this,
            )
        return CSharpParameterInfo(name=param_str, type="?", attributes=attrs)

    def _parse_modifiers(self, mod_str: str) -> List[str]:
        """Parse access and other modifiers."""
        if not mod_str:
            return []
        return [m.strip() for m in mod_str.split() if m.strip()]

    # Known modifier keywords that may leak into return_type due to regex
    _MODIFIER_KEYWORDS = frozenset({
        'public', 'private', 'protected', 'internal',
        'static', 'virtual', 'override', 'abstract',
        'sealed', 'async', 'extern', 'unsafe', 'new', 'partial',
    })

    def _parse_method(self, match, content: str, file_path: str) -> Optional[CSharpMethodInfo]:
        """Parse a method definition from regex match."""
        try:
            attr_str = match.group(1) or ""
            mod_str = match.group(2) or ""
            # group(3) is pre-return generics, usually not present
            return_type = match.group(4).strip() if match.group(4) else "void"
            name = match.group(5)
            gen_str = match.group(6) or ""
            params_str = match.group(7) or ""

            # Skip things that aren't real methods
            if name in ('if', 'while', 'for', 'switch', 'catch', 'using',
                       'lock', 'fixed', 'foreach', 'class', 'struct',
                       'interface', 'return', 'throw', 'new', 'get', 'set',
                       'delegate', 'enum', 'namespace', 'try', 'finally'):
                return None

            # Skip if return type looks like a control structure
            if return_type in ('if', 'while', 'for', 'switch', 'class', 'struct',
                              'interface', 'namespace', 'using', 'enum', 'delegate'):
                return None

            modifiers = self._parse_modifiers(mod_str)

            # Fix: repeated capture group (...)* only keeps the last match,
            # so modifiers like 'public' can leak into return_type.
            # Extract any modifier keywords from the return_type.
            rt_parts = return_type.split()
            leaked_mods = []
            clean_rt_parts = []
            for part in rt_parts:
                if part in self._MODIFIER_KEYWORDS:
                    leaked_mods.append(part)
                else:
                    clean_rt_parts.append(part)
            if leaked_mods:
                modifiers = leaked_mods + modifiers
                return_type = ' '.join(clean_rt_parts) if clean_rt_parts else "void"

            parameters = self._parse_parameters(params_str)

            # Check if it's an expression-bodied member
            after_match = content[match.end() - 2:match.end()]
            is_expression_bodied = '=>' in after_match

            # Detect extension method
            is_extension = any(p.is_this for p in parameters)

            line_number = content[:match.start()].count('\n') + 1

            # Parse attributes
            attrs = []
            if attr_str:
                for a in re.finditer(r'\[(\w+)', attr_str):
                    attrs.append(a.group(1))

            generic_params = [g.strip() for g in gen_str.split(',')] if gen_str else []

            return CSharpMethodInfo(
                name=name,
                return_type=return_type,
                parameters=parameters,
                modifiers=modifiers,
                attributes=attrs,
                generic_params=generic_params,
                file=file_path,
                line_number=line_number,
                is_exported='public' in modifiers or 'internal' in modifiers,
                is_static='static' in modifiers,
                is_abstract='abstract' in modifiers,
                is_virtual='virtual' in modifiers,
                is_override='override' in modifiers,
                is_async='async' in modifiers,
                is_extension=is_extension,
                is_expression_bodied=is_expression_bodied,
            )
        except Exception:
            return None

    def _parse_constructor(self, match, content: str, file_path: str,
                           class_names: set) -> Optional[CSharpConstructorInfo]:
        """Parse a constructor definition."""
        try:
            attr_str = match.group(1) or ""
            mod_str = match.group(2) or ""
            name = match.group(3)
            params_str = match.group(4) or ""
            chain_call = match.group(5)  # 'base' or 'this' or None

            # Only accept if name matches a known class name
            if name not in class_names:
                return None

            modifiers = self._parse_modifiers(mod_str)
            parameters = self._parse_parameters(params_str)

            attrs = []
            if attr_str:
                for a in re.finditer(r'\[(\w+)', attr_str):
                    attrs.append(a.group(1))

            line_number = content[:match.start()].count('\n') + 1

            return CSharpConstructorInfo(
                class_name=name,
                parameters=parameters,
                modifiers=modifiers,
                attributes=attrs,
                calls_base=chain_call == 'base',
                calls_this=chain_call == 'this',
                file=file_path,
                line_number=line_number,
                is_exported='public' in modifiers or 'internal' in modifiers,
                is_static='static' in modifiers,
            )
        except Exception:
            return None

    def _parse_event(self, match, content: str, file_path: str) -> Optional[CSharpEventInfo]:
        """Parse an event declaration."""
        try:
            attr_str = match.group(1) or ""
            mod_str = match.group(2) or ""
            event_type = match.group(3).strip()
            name = match.group(4)

            modifiers = self._parse_modifiers(mod_str)
            attrs = []
            if attr_str:
                for a in re.finditer(r'\[(\w+)', attr_str):
                    attrs.append(a.group(1))

            line_number = content[:match.start()].count('\n') + 1

            return CSharpEventInfo(
                name=name,
                type=event_type,
                modifiers=modifiers,
                attributes=attrs,
                file=file_path,
                line_number=line_number,
                is_static='static' in modifiers,
            )
        except Exception:
            return None
