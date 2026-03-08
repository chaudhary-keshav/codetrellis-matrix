"""
Alpine.js Component Extractor for CodeTrellis

Extracts Alpine.js component definitions from HTML and JavaScript/TypeScript source:
- Inline x-data components (x-data="{ count: 0, increment() { this.count++ } }")
- Alpine.data() registered components (Alpine.data('dropdown', () => ({ ... })))
- Component state fields (properties in x-data objects)
- Component methods
- Computed getters (get property)
- init() lifecycle hook
- destroy() lifecycle hook
- $refs, $el, $root, $data, $watch, $dispatch, $nextTick usage
- Nested x-data scopes

Supports:
- Alpine.js v2.x (inline x-data only)
- Alpine.js v3.x (Alpine.data(), init/destroy, $watch, $dispatch)

Part of CodeTrellis v4.66 - Alpine.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class AlpineComponentInfo:
    """Information about an Alpine.js component definition."""
    name: str  # Component name (from Alpine.data() or derived from x-data)
    file: str = ""
    line_number: int = 0
    component_type: str = ""  # inline, registered (Alpine.data), function
    state_fields: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    computed_getters: List[str] = field(default_factory=list)
    has_init: bool = False
    has_destroy: bool = False
    magics_used: List[str] = field(default_factory=list)  # $refs, $el, $dispatch, etc.
    is_exported: bool = False
    has_typescript: bool = False


@dataclass
class AlpineMethodInfo:
    """Information about a method in an Alpine.js component."""
    name: str
    file: str = ""
    line_number: int = 0
    is_async: bool = False
    is_getter: bool = False
    component_name: str = ""


class AlpineComponentExtractor:
    """
    Extracts Alpine.js component definitions and their internals.

    Detects:
    - Alpine.data('name', () => ({ ... })) registered components
    - Alpine.data('name', function() { return { ... } }) registered components
    - Inline x-data="{ ... }" component definitions
    - x-data="componentName" (referencing Alpine.data registered components)
    - x-data="componentName()" (function call patterns)
    - State fields, methods, getters, init/destroy lifecycle
    - Magic property usage ($refs, $el, $dispatch, $watch, $nextTick, etc.)
    """

    # Alpine.data('name', () => ({ ... })) or Alpine.data('name', function() { ... })
    ALPINE_DATA_PATTERN = re.compile(
        r"""Alpine\.data\(\s*['"](\w+)['"]\s*,\s*"""
        r"""(?:\(?[^)]*\)?\s*=>\s*\(?|function\s*\([^)]*\)\s*\{?\s*(?:return\s*)?\(?)""",
        re.MULTILINE
    )

    # Inline x-data="{ ... }" — capture the component name reference or inline object
    XDATA_INLINE_PATTERN = re.compile(
        r"""x-data\s*=\s*"(\{[^"]*\})"\s*""",
        re.MULTILINE
    )

    # x-data="componentName" or x-data="componentName()"
    XDATA_REF_PATTERN = re.compile(
        r"""x-data\s*=\s*"([a-zA-Z_]\w*(?:\(\))?)"(?:\s|>)""",
        re.MULTILINE
    )

    # Method patterns inside x-data or Alpine.data objects
    METHOD_PATTERN = re.compile(
        r"""(?:^|\s+)(async\s+)?(\w+)\s*\([^)]*\)\s*\{""",
        re.MULTILINE
    )

    # Getter patterns
    GETTER_PATTERN = re.compile(
        r"""get\s+(\w+)\s*\(\s*\)\s*\{""",
        re.MULTILINE
    )

    # State field patterns (key: value in object literal)
    STATE_FIELD_PATTERN = re.compile(
        r"""(\w+)\s*:\s*(?!function)(?!.*=>)([^,}\n]+)""",
        re.MULTILINE
    )

    # Magic property usage
    MAGIC_PATTERN = re.compile(
        r"""\$(\w+)""",
        re.MULTILINE
    )

    KNOWN_MAGICS = {
        'el', 'refs', 'store', 'watch', 'dispatch', 'nextTick',
        'root', 'data', 'id', 'persist',
    }

    def extract(self, content: str, file_path: str = "") -> tuple:
        """Extract Alpine.js component definitions.

        Args:
            content: Source code content (HTML or JS/TS).
            file_path: Path to the source file.

        Returns:
            Tuple of (List[AlpineComponentInfo], List[AlpineMethodInfo]).
        """
        components: List[AlpineComponentInfo] = []
        methods: List[AlpineMethodInfo] = []

        is_ts = file_path.endswith(('.ts', '.tsx'))

        # Extract Alpine.data() registered components
        for match in self.ALPINE_DATA_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Try to extract the component body
            body = self._extract_body(content, match.end())
            comp_methods = self._extract_methods(body, file_path, name)
            comp_getters = self._extract_getters(body)
            state_fields = self._extract_state_fields(body)
            magics = self._extract_magics(body)

            components.append(AlpineComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                component_type="registered",
                state_fields=state_fields,
                methods=[m.name for m in comp_methods],
                computed_getters=comp_getters,
                has_init='init' in [m.name for m in comp_methods],
                has_destroy='destroy' in [m.name for m in comp_methods],
                magics_used=magics,
                is_exported=self._is_exported(content, match.start()),
                has_typescript=is_ts,
            ))
            methods.extend(comp_methods)

        # Extract inline x-data components
        for match in self.XDATA_INLINE_PATTERN.finditer(content):
            body = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            state_fields = self._extract_state_fields_inline(body)
            inline_methods = self._extract_method_names_inline(body)
            magics = self._extract_magics(body)

            comp_name = f"inline_{line_num}"

            components.append(AlpineComponentInfo(
                name=comp_name,
                file=file_path,
                line_number=line_num,
                component_type="inline",
                state_fields=state_fields,
                methods=inline_methods,
                computed_getters=[],
                has_init='init' in inline_methods,
                has_destroy=False,
                magics_used=magics,
                is_exported=False,
                has_typescript=False,
            ))

        # Extract x-data="componentName" references
        for match in self.XDATA_REF_PATTERN.finditer(content):
            ref_name = match.group(1).rstrip('()')
            line_num = content[:match.start()].count('\n') + 1

            # Only add if not already in components (it's a reference, not definition)
            if not any(c.name == ref_name for c in components):
                components.append(AlpineComponentInfo(
                    name=ref_name,
                    file=file_path,
                    line_number=line_num,
                    component_type="reference",
                    state_fields=[],
                    methods=[],
                    computed_getters=[],
                    has_init=False,
                    has_destroy=False,
                    magics_used=[],
                    is_exported=False,
                    has_typescript=False,
                ))

        return components, methods

    def _extract_body(self, content: str, start: int) -> str:
        """Extract balanced braces body from content starting at position.

        Args:
            content: Full source code.
            start: Start position after opening pattern.

        Returns:
            Body string (may be truncated if unbalanced).
        """
        depth = 0
        body_start = -1
        for i in range(start, min(start + 5000, len(content))):
            ch = content[i]
            if ch == '{':
                if depth == 0:
                    body_start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and body_start >= 0:
                    return content[body_start:i + 1]
        if body_start >= 0:
            return content[body_start:min(start + 5000, len(content))]
        return ""

    def _extract_methods(self, body: str, file_path: str, comp_name: str) -> List[AlpineMethodInfo]:
        """Extract methods from a component body.

        Args:
            body: Component body text.
            file_path: Source file path.
            comp_name: Component name.

        Returns:
            List of AlpineMethodInfo.
        """
        result: List[AlpineMethodInfo] = []
        for match in self.METHOD_PATTERN.finditer(body):
            is_async = bool(match.group(1))
            name = match.group(2)
            # Skip common false positives
            if name in ('if', 'for', 'while', 'switch', 'catch', 'function', 'class', 'return'):
                continue
            line_num = body[:match.start()].count('\n') + 1
            result.append(AlpineMethodInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_async=is_async,
                is_getter=False,
                component_name=comp_name,
            ))

        # Add getters
        for match in self.GETTER_PATTERN.finditer(body):
            name = match.group(1)
            line_num = body[:match.start()].count('\n') + 1
            result.append(AlpineMethodInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_async=False,
                is_getter=True,
                component_name=comp_name,
            ))

        return result

    def _extract_getters(self, body: str) -> List[str]:
        """Extract getter names from component body.

        Args:
            body: Component body text.

        Returns:
            List of getter names.
        """
        return [m.group(1) for m in self.GETTER_PATTERN.finditer(body)]

    def _extract_state_fields(self, body: str) -> List[str]:
        """Extract state field names from component body.

        Args:
            body: Component body text.

        Returns:
            List of state field names.
        """
        fields: List[str] = []
        for match in self.STATE_FIELD_PATTERN.finditer(body):
            name = match.group(1)
            # Skip methods and keywords
            if name in ('get', 'set', 'async', 'function', 'class', 'return', 'if', 'for'):
                continue
            if name not in fields:
                fields.append(name)
        return fields[:20]  # Limit

    def _extract_state_fields_inline(self, body: str) -> List[str]:
        """Extract state fields from inline x-data object.

        Args:
            body: Inline object body (e.g., "{ count: 0, name: '' }").

        Returns:
            List of state field names.
        """
        fields: List[str] = []
        # Simple key: value extraction
        for match in re.finditer(r'(\w+)\s*:', body):
            name = match.group(1)
            if name not in ('get', 'set', 'function'):
                fields.append(name)
        return fields[:20]

    def _extract_method_names_inline(self, body: str) -> List[str]:
        """Extract method names from inline x-data object.

        Args:
            body: Inline object body.

        Returns:
            List of method names.
        """
        methods: List[str] = []
        for match in re.finditer(r'(\w+)\s*\([^)]*\)\s*\{', body):
            name = match.group(1)
            if name not in ('if', 'for', 'while', 'switch', 'catch', 'function'):
                methods.append(name)
        return methods

    def _extract_magics(self, body: str) -> List[str]:
        """Extract Alpine magic property usages from body.

        Args:
            body: Component body text.

        Returns:
            List of magic names used (e.g., ['refs', 'dispatch', 'watch']).
        """
        magics: List[str] = []
        for match in self.MAGIC_PATTERN.finditer(body):
            name = match.group(1)
            if name in self.KNOWN_MAGICS and name not in magics:
                magics.append(name)
        return magics

    def _is_exported(self, content: str, pos: int) -> bool:
        """Check if the Alpine.data() call is in an export context.

        Args:
            content: Full source code.
            pos: Position of the Alpine.data() match.

        Returns:
            True if the component is exported.
        """
        # Check the line before the match
        line_start = content.rfind('\n', 0, pos)
        if line_start < 0:
            line_start = 0
        prefix = content[line_start:pos].strip()
        return 'export' in prefix
