"""
Lit Property Extractor for CodeTrellis

Extracts Lit reactive property and internal state declarations:
- @property() decorator with options (type, attribute, reflect, converter, hasChanged)
- @state() decorator for internal reactive state
- static properties = { ... } block (lit-element 2.x / lit 2.x-3.x)
- static get properties() { return { ... } } (Polymer / lit-element legacy)
- PropertyDeclaration interface support
- Attribute reflection and custom converters
- Property accessors (getter/setter overrides)

Supports:
- Polymer 1.x-3.x (properties: { prop: { type: String, value: '', observer: '_propChanged' } })
- lit-element 2.x (@property(), static get properties())
- lit 2.x-3.x (@property(), @state(), static properties = {})
- @lit/reactive-element (ReactiveElement property system)
- Type coercion (String, Number, Boolean, Array, Object)

Part of CodeTrellis v4.65 - Lit / Web Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class LitPropertyInfo:
    """Information about a Lit reactive property."""
    name: str
    file: str = ""
    line_number: int = 0
    prop_type: str = ""  # String, Number, Boolean, Array, Object, custom
    attribute: str = ""  # attribute name (or False for no attribute)
    has_reflect: bool = False
    has_converter: bool = False
    has_has_changed: bool = False
    has_no_accessor: bool = False
    default_value: str = ""
    is_decorator: bool = False  # True if @property(), False if static properties
    is_readonly: bool = False
    type_annotation: str = ""  # TypeScript type annotation
    component_name: str = ""  # Which component this belongs to


@dataclass
class LitStateInfo:
    """Information about a Lit internal state property (@state())."""
    name: str
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""
    default_value: str = ""
    is_decorator: bool = True
    component_name: str = ""


class LitPropertyExtractor:
    """
    Extracts reactive property and state declarations from Lit source code.

    Detects:
    - @property({ type: String, reflect: true }) name = 'default'
    - @state() private _count = 0
    - static properties = { name: { type: String } }
    - static get properties() { return { name: { type: String } } }
    - Polymer-style properties with observers and computed
    """

    # @property() decorator
    PROPERTY_DECORATOR = re.compile(
        r'@property\s*\(\s*(\{[^}]*\})?\s*\)\s*'
        r'(?:(?:declare|readonly|private|protected|public|accessor)\s+)*'
        r'(\w+)\s*(?:[:?!]?\s*([^=;]+))?\s*(?:=\s*([^;]+))?',
        re.MULTILINE
    )

    # @state() decorator
    STATE_DECORATOR = re.compile(
        r'@state\s*\(\s*\)\s*'
        r'(?:(?:declare|private|protected|public|accessor)\s+)*'
        r'(\w+)\s*(?:[:?!]?\s*([^=;]+))?\s*(?:=\s*([^;]+))?',
        re.MULTILINE
    )

    # static properties = { ... }
    STATIC_PROPERTIES_BLOCK = re.compile(
        r'static\s+(?:override\s+)?properties\s*[=:]\s*\{',
        re.MULTILINE
    )

    # static get properties() { return { ... } }
    STATIC_GET_PROPERTIES = re.compile(
        r'static\s+get\s+properties\s*\(\s*\)\s*\{[^}]*return\s*\{',
        re.MULTILINE | re.DOTALL
    )

    # Individual property in static block: name: { type: String, reflect: true }
    STATIC_PROP_ENTRY = re.compile(
        r'(\w+)\s*:\s*\{\s*([^}]*)\}',
        re.MULTILINE
    )

    # Simple property in static block: name: String
    STATIC_PROP_SIMPLE = re.compile(
        r'(\w+)\s*:\s*(String|Number|Boolean|Array|Object)\b',
        re.MULTILINE
    )

    # Property option patterns
    TYPE_OPTION = re.compile(r'type\s*:\s*(String|Number|Boolean|Array|Object|\w+)')
    REFLECT_OPTION = re.compile(r'reflect\s*:\s*true')
    ATTRIBUTE_OPTION = re.compile(r'attribute\s*:\s*(?:[\'"]([^"\']+)[\'"]|false)')
    CONVERTER_OPTION = re.compile(r'converter\s*:')
    HAS_CHANGED_OPTION = re.compile(r'hasChanged\s*:')
    NO_ACCESSOR_OPTION = re.compile(r'noAccessor\s*:\s*true')

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract Lit property and state information from source code.

        Returns dict with keys: properties, states
        """
        properties: List[LitPropertyInfo] = []
        states: List[LitStateInfo] = []

        # ── @property() decorators ────────────────────────────────
        for m in self.PROPERTY_DECORATOR.finditer(content):
            options_str = m.group(1) or ""
            name = m.group(2)
            type_annotation = (m.group(3) or "").strip()
            default_value = (m.group(4) or "").strip().rstrip(';')
            line_num = content[:m.start()].count('\n') + 1

            prop = LitPropertyInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_decorator=True,
                type_annotation=type_annotation,
                default_value=default_value,
            )

            # Parse options
            if options_str:
                type_m = self.TYPE_OPTION.search(options_str)
                if type_m:
                    prop.prop_type = type_m.group(1)
                prop.has_reflect = bool(self.REFLECT_OPTION.search(options_str))
                attr_m = self.ATTRIBUTE_OPTION.search(options_str)
                if attr_m:
                    prop.attribute = attr_m.group(1) or "false"
                prop.has_converter = bool(self.CONVERTER_OPTION.search(options_str))
                prop.has_has_changed = bool(self.HAS_CHANGED_OPTION.search(options_str))
                prop.has_no_accessor = bool(self.NO_ACCESSOR_OPTION.search(options_str))

            properties.append(prop)

        # ── @state() decorators ───────────────────────────────────
        for m in self.STATE_DECORATOR.finditer(content):
            name = m.group(1)
            type_annotation = (m.group(2) or "").strip()
            default_value = (m.group(3) or "").strip().rstrip(';')
            line_num = content[:m.start()].count('\n') + 1

            state = LitStateInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                type_annotation=type_annotation,
                default_value=default_value,
            )
            states.append(state)

        # ── static properties = { ... } ──────────────────────────
        for m in self.STATIC_PROPERTIES_BLOCK.finditer(content):
            block_start = m.end() - 1  # Position of opening {
            block_content = self._extract_brace_block(content, block_start)
            if block_content:
                self._parse_static_properties(block_content, content[:m.start()].count('\n') + 1,
                                               file_path, properties)

        # ── static get properties() { return { ... } } ───────────
        for m in self.STATIC_GET_PROPERTIES.finditer(content):
            # Find the inner object (after 'return {')
            return_pos = content.find('return', m.start())
            if return_pos != -1:
                brace_pos = content.find('{', return_pos)
                if brace_pos != -1:
                    block_content = self._extract_brace_block(content, brace_pos)
                    if block_content:
                        self._parse_static_properties(block_content, content[:m.start()].count('\n') + 1,
                                                       file_path, properties)

        return {
            'properties': properties,
            'states': states,
        }

    def _extract_brace_block(self, content: str, start: int) -> str:
        """Extract content within balanced braces starting at position start."""
        if start >= len(content) or content[start] != '{':
            return ""
        depth = 1
        pos = start + 1
        while pos < len(content) and depth > 0:
            ch = content[pos]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            elif ch in ('"', "'", '`'):
                # Skip string literals
                end_char = ch
                pos += 1
                while pos < len(content) and content[pos] != end_char:
                    if content[pos] == '\\':
                        pos += 1
                    pos += 1
            pos += 1
        return content[start + 1:pos - 1]

    def _parse_static_properties(self, block: str, base_line: int,
                                   file_path: str, properties: List[LitPropertyInfo]):
        """Parse individual properties from a static properties block."""
        # Match complex properties: name: { type: String, reflect: true }
        for m in self.STATIC_PROP_ENTRY.finditer(block):
            name = m.group(1)
            options_str = m.group(2)
            line_offset = block[:m.start()].count('\n')

            prop = LitPropertyInfo(
                name=name,
                file=file_path,
                line_number=base_line + line_offset,
                is_decorator=False,
            )

            type_m = self.TYPE_OPTION.search(options_str)
            if type_m:
                prop.prop_type = type_m.group(1)
            prop.has_reflect = bool(self.REFLECT_OPTION.search(options_str))
            attr_m = self.ATTRIBUTE_OPTION.search(options_str)
            if attr_m:
                prop.attribute = attr_m.group(1) or "false"
            prop.has_converter = bool(self.CONVERTER_OPTION.search(options_str))
            prop.has_has_changed = bool(self.HAS_CHANGED_OPTION.search(options_str))

            # Avoid duplicates with decorator properties
            if not any(p.name == name and p.is_decorator for p in properties):
                properties.append(prop)

        # Match simple properties: name: String
        for m in self.STATIC_PROP_SIMPLE.finditer(block):
            name = m.group(1)
            type_str = m.group(2)
            # Skip if already captured by complex pattern
            if any(p.name == name for p in properties):
                continue
            line_offset = block[:m.start()].count('\n')

            prop = LitPropertyInfo(
                name=name,
                file=file_path,
                line_number=base_line + line_offset,
                prop_type=type_str,
                is_decorator=False,
            )
            properties.append(prop)
