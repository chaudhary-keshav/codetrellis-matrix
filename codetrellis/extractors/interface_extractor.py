"""
InterfaceExtractor - Extracts TypeScript interfaces from source code.

This extractor parses TypeScript interface declarations and extracts:
- Interface names and export status
- Properties with types, optional/readonly modifiers
- Method signatures
- Generic type parameters
- Extended interfaces
- Index signatures
- JSDoc documentation
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


@dataclass
class PropertyInfo:
    """Represents a property in an interface."""
    name: str
    type: str
    optional: bool = False
    readonly: bool = False
    description: str = ""


@dataclass
class MethodSignatureInfo:
    """Represents a method signature in an interface."""
    name: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_type: str = "void"
    optional: bool = False
    description: str = ""


@dataclass
class IndexSignatureInfo:
    """Represents an index signature in an interface."""
    key_name: str
    key_type: str
    value_type: str


@dataclass
class InterfaceInfo:
    """Complete information about a TypeScript interface."""
    name: str
    properties: List[PropertyInfo] = field(default_factory=list)
    methods: List[MethodSignatureInfo] = field(default_factory=list)
    generics: List[str] = field(default_factory=list)
    extends: List[str] = field(default_factory=list)
    is_exported: bool = False
    index_signature: Optional[IndexSignatureInfo] = None
    description: str = ""
    line_number: int = 0


class InterfaceExtractor:
    """
    Extracts TypeScript interface definitions from source code.

    Handles:
    - Simple interfaces with properties
    - Interfaces with optional/readonly properties
    - Generic interfaces
    - Extended interfaces
    - Interfaces with methods
    - Index signatures
    - JSDoc comments
    """

    # Regex patterns
    INTERFACE_PATTERN = re.compile(
        r'(?P<jsdoc>/\*\*[\s\S]*?\*/\s*)?'  # Optional JSDoc
        r'(?P<export>export\s+)?'            # Optional export
        r'interface\s+'                       # interface keyword
        r'(?P<name>\w+)'                      # Interface name
        r'(?:<(?P<generics>[^>]+)>)?'         # Optional generics
        r'(?:\s+extends\s+(?P<extends>[^{]+))?' # Optional extends
        r'\s*\{',                              # Opening brace
        re.MULTILINE
    )

    PROPERTY_PATTERN = re.compile(
        r'(?P<jsdoc>/\*\*[\s\S]*?\*/\s*)?'  # Optional JSDoc
        r'(?P<readonly>readonly\s+)?'        # Optional readonly
        r'(?P<name>\w+)'                      # Property name
        r'(?P<optional>\?)?'                  # Optional marker
        r'\s*:\s*'                            # Colon
        r'(?P<type>[^;}\n]+)'                 # Type (everything until ; or } or newline)
        r'\s*[;,]?',                          # Optional semicolon/comma
        re.MULTILINE
    )

    METHOD_PATTERN = re.compile(
        r'(?P<jsdoc>/\*\*[\s\S]*?\*/\s*)?'  # Optional JSDoc
        r'(?P<name>\w+)'                      # Method name
        r'(?P<optional>\?)?'                  # Optional marker
        r'\s*\('                              # Opening paren
        r'(?P<params>[^)]*)'                  # Parameters
        r'\)\s*:\s*'                          # Closing paren and colon
        r'(?P<return_type>[^;}\n]+)'          # Return type
        r'\s*[;,]?',                          # Optional semicolon
        re.MULTILINE
    )

    INDEX_SIGNATURE_PATTERN = re.compile(
        r'\[\s*(?P<key_name>\w+)\s*:\s*(?P<key_type>\w+)\s*\]'
        r'\s*:\s*(?P<value_type>[^;}\n]+)'
        r'\s*[;,]?',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the interface extractor."""
        self._comment_ranges: List[tuple] = []

    def extract(self, content: str) -> List[InterfaceInfo]:
        """
        Extract all interfaces from TypeScript content.

        Args:
            content: TypeScript source code

        Returns:
            List of InterfaceInfo objects
        """
        # First, identify comment ranges to skip
        self._find_comment_ranges(content)

        interfaces = []

        for match in self.INTERFACE_PATTERN.finditer(content):
            # Skip if inside a comment
            if self._is_in_comment(match.start()):
                continue

            interface = self._parse_interface(content, match)
            if interface:
                interfaces.append(interface)

        return interfaces

    def _find_comment_ranges(self, content: str) -> None:
        """Find all comment ranges to skip during parsing."""
        self._comment_ranges = []

        # Single line comments
        for match in re.finditer(r'//[^\n]*', content):
            self._comment_ranges.append((match.start(), match.end()))

        # Multi-line comments (but not JSDoc which starts with /**)
        for match in re.finditer(r'/\*(?!\*)[\s\S]*?\*/', content):
            self._comment_ranges.append((match.start(), match.end()))

    def _is_in_comment(self, position: int) -> bool:
        """Check if a position is inside a comment."""
        for start, end in self._comment_ranges:
            if start <= position < end:
                return True
        return False

    def _parse_interface(self, content: str, match: re.Match) -> Optional[InterfaceInfo]:
        """Parse a single interface from its match."""
        name = match.group('name')
        is_exported = match.group('export') is not None
        jsdoc = match.group('jsdoc') or ""
        description = self._parse_jsdoc_description(jsdoc)

        # Parse generics
        generics = []
        if match.group('generics'):
            generics = [g.strip() for g in match.group('generics').split(',')]

        # Parse extends
        extends = []
        if match.group('extends'):
            extends = [e.strip() for e in match.group('extends').split(',')]

        # Find the interface body
        body_start = match.end()
        body = self._extract_brace_content(content, body_start - 1)

        if body is None:
            return None

        # Calculate line number
        line_number = content[:match.start()].count('\n') + 1

        # Parse properties and methods from body
        properties, methods, index_signature = self._parse_body(body)

        return InterfaceInfo(
            name=name,
            properties=properties,
            methods=methods,
            generics=generics,
            extends=extends,
            is_exported=is_exported,
            index_signature=index_signature,
            description=description,
            line_number=line_number
        )

    def _extract_brace_content(self, content: str, start: int) -> Optional[str]:
        """Extract content between matching braces."""
        if start >= len(content) or content[start] != '{':
            return None

        depth = 0
        end = start

        for i in range(start, len(content)):
            char = content[i]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break

        if depth != 0:
            return None

        return content[start + 1:end]

    def _parse_body(self, body: str) -> tuple:
        """
        Parse interface body to extract properties, methods, and index signatures.

        Returns:
            Tuple of (properties, methods, index_signature)
        """
        properties = []
        methods = []
        index_signature = None

        # Remove nested object types temporarily to avoid confusion
        cleaned_body = self._mask_nested_objects(body)

        # Extract index signature first
        idx_match = self.INDEX_SIGNATURE_PATTERN.search(cleaned_body)
        if idx_match:
            index_signature = IndexSignatureInfo(
                key_name=idx_match.group('key_name'),
                key_type=idx_match.group('key_type'),
                value_type=idx_match.group('value_type').strip()
            )

        # Parse line by line for better accuracy
        lines = body.split('\n')
        current_jsdoc = ""

        for line in lines:
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('//'):
                continue

            # Capture JSDoc
            if stripped.startswith('/**') or stripped.startswith('*'):
                if stripped.startswith('/**'):
                    current_jsdoc = stripped
                elif stripped.startswith('*/'):
                    current_jsdoc += '\n' + stripped
                else:
                    current_jsdoc += '\n' + stripped
                continue

            # Skip index signatures (already handled)
            if '[' in stripped and ']:' in stripped:
                current_jsdoc = ""
                continue

            # Check if it's a method (has parentheses before colon)
            if self._is_method_signature(stripped):
                method = self._parse_method_line(stripped, current_jsdoc)
                if method:
                    methods.append(method)
            else:
                # It's a property
                prop = self._parse_property_line(stripped, current_jsdoc)
                if prop:
                    properties.append(prop)

            current_jsdoc = ""

        return properties, methods, index_signature

    def _mask_nested_objects(self, body: str) -> str:
        """Temporarily mask nested object types to simplify parsing."""
        result = []
        depth = 0

        for char in body:
            if char == '{':
                depth += 1
                if depth > 0:
                    result.append('〈')  # Use special char as placeholder
                else:
                    result.append(char)
            elif char == '}':
                if depth > 0:
                    result.append('〉')
                else:
                    result.append(char)
                depth -= 1
            else:
                result.append(char)

        return ''.join(result)

    def _is_method_signature(self, line: str) -> bool:
        """Check if a line represents a method signature."""
        # Method has name followed by ( before :
        # Property might have function type like: onClick: (event: Event) => void

        # Remove function type annotations to check
        # If the line starts with name( then it's a method
        match = re.match(r'^\w+\??\s*\(', line)
        return match is not None

    def _parse_property_line(self, line: str, jsdoc: str) -> Optional[PropertyInfo]:
        """Parse a single property line."""
        # Pattern: readonly? name?: type;
        match = re.match(
            r'(?P<readonly>readonly\s+)?'
            r'(?P<name>\w+)'
            r'(?P<optional>\?)?'
            r'\s*:\s*'
            r'(?P<type>.+?)'
            r'\s*[;,]?\s*$',
            line
        )

        if not match:
            return None

        type_str = match.group('type').strip()
        # Restore masked nested objects
        type_str = type_str.replace('〈', '{').replace('〉', '}')

        return PropertyInfo(
            name=match.group('name'),
            type=type_str,
            optional=match.group('optional') is not None,
            readonly=match.group('readonly') is not None,
            description=self._parse_jsdoc_description(jsdoc)
        )

    def _parse_method_line(self, line: str, jsdoc: str) -> Optional[MethodSignatureInfo]:
        """Parse a single method signature line."""
        # Pattern: name?(params): returnType;
        match = re.match(
            r'(?P<name>\w+)'
            r'(?P<optional>\?)?'
            r'\s*\('
            r'(?P<params>[^)]*)'
            r'\)\s*:\s*'
            r'(?P<return_type>.+?)'
            r'\s*[;,]?\s*$',
            line
        )

        if not match:
            return None

        # Parse parameters
        params_str = match.group('params')
        parameters = self._parse_parameters(params_str)

        return_type = match.group('return_type').strip()
        # Restore masked nested objects
        return_type = return_type.replace('〈', '{').replace('〉', '}')

        return MethodSignatureInfo(
            name=match.group('name'),
            parameters=parameters,
            return_type=return_type,
            optional=match.group('optional') is not None,
            description=self._parse_jsdoc_description(jsdoc)
        )

    def _parse_parameters(self, params_str: str) -> List[Dict[str, str]]:
        """Parse method parameters."""
        params = []

        if not params_str.strip():
            return params

        # Split by comma, but be careful of generic types
        depth = 0
        current_param = ""

        for char in params_str:
            if char in '<({':
                depth += 1
                current_param += char
            elif char in '>)}':
                depth -= 1
                current_param += char
            elif char == ',' and depth == 0:
                param = self._parse_single_param(current_param.strip())
                if param:
                    params.append(param)
                current_param = ""
            else:
                current_param += char

        # Don't forget the last parameter
        if current_param.strip():
            param = self._parse_single_param(current_param.strip())
            if param:
                params.append(param)

        return params

    def _parse_single_param(self, param_str: str) -> Optional[Dict[str, str]]:
        """Parse a single parameter like 'name: type' or 'name?: type'."""
        match = re.match(
            r'(?P<name>\w+)'
            r'(?P<optional>\?)?'
            r'\s*:\s*'
            r'(?P<type>.+)',
            param_str
        )

        if not match:
            return None

        return {
            'name': match.group('name'),
            'type': match.group('type').strip(),
            'optional': match.group('optional') is not None
        }

    def _parse_jsdoc_description(self, jsdoc: str) -> str:
        """Extract description from JSDoc comment."""
        if not jsdoc:
            return ""

        # Remove /** and */
        content = jsdoc.replace('/**', '').replace('*/', '')

        # Remove leading * from each line
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('*'):
                line = line[1:].strip()
            # Skip @property, @param, etc.
            if line.startswith('@'):
                continue
            if line:
                lines.append(line)

        return ' '.join(lines)

    def to_codetrellis_format(self, interfaces: List[InterfaceInfo]) -> str:
        """
        Convert extracted interfaces to CodeTrellis format.

        Args:
            interfaces: List of extracted interfaces

        Returns:
            CodeTrellis formatted string
        """
        if not interfaces:
            return ""

        lines = ["[INTERFACES]"]

        for iface in interfaces:
            # Interface header
            export_marker = "export " if iface.is_exported else ""
            generics = f"<{', '.join(iface.generics)}>" if iface.generics else ""
            extends = f" extends {', '.join(iface.extends)}" if iface.extends else ""

            lines.append(f"  {export_marker}interface {iface.name}{generics}{extends}:")

            # Properties
            for prop in iface.properties:
                readonly = "readonly " if prop.readonly else ""
                optional = "?" if prop.optional else ""
                lines.append(f"    {readonly}{prop.name}{optional}: {prop.type}")

            # Methods
            for method in iface.methods:
                optional = "?" if method.optional else ""
                params = ", ".join([f"{p['name']}: {p['type']}" for p in method.parameters])
                lines.append(f"    {method.name}{optional}({params}): {method.return_type}")

            # Index signature
            if iface.index_signature:
                idx = iface.index_signature
                lines.append(f"    [{idx.key_name}: {idx.key_type}]: {idx.value_type}")

            lines.append("")  # Empty line between interfaces

        return '\n'.join(lines)


# Convenience function
def extract_interfaces(content: str) -> List[InterfaceInfo]:
    """
    Convenience function to extract interfaces from content.

    Args:
        content: TypeScript source code

    Returns:
        List of InterfaceInfo objects
    """
    extractor = InterfaceExtractor()
    return extractor.extract(content)
