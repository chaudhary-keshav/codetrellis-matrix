"""
ProtocolExtractor - Extracts Protocol class definitions from Python source code.

This extractor parses Protocol declarations (structural typing) and extracts:
- Protocol names and generic parameters
- Method signatures
- Properties
- @runtime_checkable decorator
- Inherited protocols

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ProtocolMethodInfo:
    """Information about a method in a Protocol."""
    name: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_type: str = "None"
    is_async: bool = False
    is_property: bool = False


@dataclass
class ProtocolInfo:
    """Complete information about a Protocol."""
    name: str
    methods: List[ProtocolMethodInfo] = field(default_factory=list)
    generics: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    runtime_checkable: bool = False
    line_number: int = 0


class ProtocolExtractor:
    """
    Extracts Protocol class definitions from Python source code.

    Handles:
    - Simple protocols with methods
    - Generic protocols (Protocol[T])
    - @runtime_checkable decorator
    - Protocol inheritance
    - Abstract method stubs (...)
    - Properties in protocols
    """

    # Pattern to detect @runtime_checkable decorator
    RUNTIME_CHECKABLE_PATTERN = re.compile(
        r'@runtime_checkable\s*\n',
        re.MULTILINE
    )

    # Pattern for Protocol class definition
    PROTOCOL_CLASS_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(([^)]*Protocol[^)]*)\):',
        re.MULTILINE
    )

    # Pattern for method definitions
    METHOD_PATTERN = re.compile(
        r'(?:@property\s+)?(async\s+)?def\s+(\w+)\s*\(\s*([^)]*)\s*\)\s*(?:->\s*([^:]+))?\s*:',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Protocol extractor."""
        pass

    def extract(self, content: str) -> List[ProtocolInfo]:
        """
        Extract all Protocols from Python content.

        Args:
            content: Python source code

        Returns:
            List of ProtocolInfo objects
        """
        protocols = []

        for match in self.PROTOCOL_CLASS_PATTERN.finditer(content):
            protocol_name = match.group(1)
            bases_str = match.group(2)

            # Parse bases and generics
            bases, generics = self._parse_bases_and_generics(bases_str)

            # Check for @runtime_checkable decorator
            # Look backwards from the class definition
            before_class = content[:match.start()]
            # Check the last 100 chars for the decorator
            check_range = before_class[-100:] if len(before_class) > 100 else before_class
            runtime_checkable = '@runtime_checkable' in check_range

            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            # Extract class body
            class_body_start = match.end()
            class_body = self._extract_class_body(content, class_body_start)

            if class_body is None:
                continue

            # Parse methods
            methods = self._parse_methods(class_body)

            protocol_info = ProtocolInfo(
                name=protocol_name,
                methods=methods,
                generics=generics,
                bases=bases,
                runtime_checkable=runtime_checkable,
                line_number=line_number
            )

            protocols.append(protocol_info)

        return protocols

    def _parse_bases_and_generics(self, bases_str: str) -> tuple[List[str], List[str]]:
        """Parse base classes and generic parameters."""
        bases = []
        generics = []

        # Check for Protocol[T, U, ...] syntax
        generic_match = re.search(r'Protocol\[([^\]]+)\]', bases_str)
        if generic_match:
            generics = [g.strip() for g in generic_match.group(1).split(',')]
            # Remove the generic part from bases_str for further processing
            bases_str = re.sub(r'Protocol\[[^\]]+\]', 'Protocol', bases_str)

        # Parse remaining bases
        for base in bases_str.split(','):
            base = base.strip()
            if base and base != 'Protocol':
                bases.append(base)

        return bases, generics

    def _extract_class_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract the body of a class by indentation."""
        lines = content[start_pos:].split('\n')

        if not lines:
            return None

        body_lines = []
        base_indent = None

        for line in lines:
            if not line.strip():
                if base_indent is not None:
                    body_lines.append('')
                continue

            current_indent = len(line) - len(line.lstrip())

            if base_indent is None:
                base_indent = current_indent
                body_lines.append(line)
                continue

            if current_indent < base_indent and line.strip():
                break

            body_lines.append(line)

        return '\n'.join(body_lines)

    def _parse_methods(self, class_body: str) -> List[ProtocolMethodInfo]:
        """Parse method signatures from class body."""
        methods = []

        # Track if we're looking at a property
        lines = class_body.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for @property decorator
            is_property = '@property' in line
            if is_property:
                i += 1
                if i >= len(lines):
                    break
                line = lines[i]

            # Look for method definition
            method_match = re.match(
                r'\s*(async\s+)?def\s+(\w+)\s*\(\s*([^)]*)\s*\)\s*(?:->\s*([^:]+))?\s*:',
                line
            )

            if method_match:
                is_async = method_match.group(1) is not None
                method_name = method_match.group(2)
                params_str = method_match.group(3)
                return_type = method_match.group(4)

                # Parse parameters
                parameters = self._parse_parameters(params_str)

                # Clean return type
                if return_type:
                    return_type = return_type.strip()
                else:
                    return_type = "None"

                methods.append(ProtocolMethodInfo(
                    name=method_name,
                    parameters=parameters,
                    return_type=return_type,
                    is_async=is_async,
                    is_property=is_property
                ))

            i += 1

        return methods

    def _parse_parameters(self, params_str: str) -> List[Dict[str, str]]:
        """Parse method parameters."""
        parameters = []

        if not params_str.strip():
            return parameters

        # Split by comma, but be careful about nested generics
        param_parts = self._split_params(params_str)

        for param in param_parts:
            param = param.strip()
            if not param or param == 'self' or param == 'cls':
                continue

            # Parse name: type = default
            if ':' in param:
                name_part, type_part = param.split(':', 1)
                name = name_part.strip()

                # Handle default value
                if '=' in type_part:
                    type_str, _ = type_part.split('=', 1)
                else:
                    type_str = type_part

                parameters.append({
                    'name': name,
                    'type': type_str.strip()
                })
            else:
                # No type annotation
                name = param.split('=')[0].strip()
                parameters.append({
                    'name': name,
                    'type': 'Any'
                })

        return parameters

    def _split_params(self, params_str: str) -> List[str]:
        """Split parameters handling nested brackets."""
        params = []
        current = ""
        depth = 0

        for char in params_str:
            if char in '([{':
                depth += 1
            elif char in ')]}':
                depth -= 1
            elif char == ',' and depth == 0:
                params.append(current)
                current = ""
                continue
            current += char

        if current.strip():
            params.append(current)

        return params

    def to_codetrellis_format(self, protocols: List[ProtocolInfo]) -> str:
        """
        Convert extracted Protocols to CodeTrellis format.

        Args:
            protocols: List of ProtocolInfo objects

        Returns:
            CodeTrellis formatted string
        """
        if not protocols:
            return ""

        lines = ["[PROTOCOLS]"]

        for proto in protocols:
            parts = [proto.name]

            # Add generics
            if proto.generics:
                parts[0] = f"{proto.name}<{','.join(proto.generics)}>"

            # Add runtime_checkable flag
            if proto.runtime_checkable:
                parts.append("runtime_checkable")

            # Add bases
            if proto.bases:
                parts.append(f"extends:{','.join(proto.bases)}")

            # Add methods
            method_strs = []
            for m in proto.methods:
                param_str = ','.join(f"{p['name']}:{p['type']}" for p in m.parameters)
                prefix = "async " if m.is_async else ""
                prop_prefix = "@property " if m.is_property else ""
                method_strs.append(f"{prop_prefix}{prefix}{m.name}({param_str})→{m.return_type}")

            if method_strs:
                parts.append(f"methods:[{';'.join(method_strs)}]")

            lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_protocols(content: str) -> List[ProtocolInfo]:
    """Extract Protocols from Python content."""
    extractor = ProtocolExtractor()
    return extractor.extract(content)
