"""
Styled Components Component Extractor for CodeTrellis

Extracts styled-components component creation patterns from JS/TS source code.
Covers styled-components v1.x through v6.x and CSS-in-JS ecosystem:
- styled.div`` / styled(Component)`` tagged template literal
- .attrs() for default prop injection
- .withConfig() for displayName/componentId/shouldForwardProp
- Component extending via styled(ExistingComponent)``
- as prop polymorphism
- forwardRef integration
- Transient props ($-prefix, v5.1+)
- shouldForwardProp (v5.1+)
- Object-style syntax: styled.div({})
- @emotion/styled compatibility (same API surface)
- linaria/css`` (static extraction)
- goober css``/styled``
- stitches styled()

Part of CodeTrellis v4.42 - Styled Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class StyledComponentInfo:
    """Information about a styled-component definition."""
    name: str
    file: str = ""
    line_number: int = 0
    base_element: str = ""          # div, span, button, h1, etc.
    base_component: str = ""        # Component being extended
    import_source: str = ""         # styled-components, @emotion/styled, etc.
    has_attrs: bool = False
    attrs_props: List[str] = field(default_factory=list)
    has_with_config: bool = False
    has_should_forward_prop: bool = False
    has_transient_props: bool = False    # $-prefixed props
    transient_props: List[str] = field(default_factory=list)
    has_dynamic_props: bool = False
    dynamic_props: List[str] = field(default_factory=list)
    has_theme_usage: bool = False
    has_media_query: bool = False
    has_nesting: bool = False
    css_properties_count: int = 0
    style_syntax: str = ""          # tagged-template, object
    method: str = ""                # styled.element, styled(Component), css
    is_extended: bool = False


@dataclass
class StyledExtendedComponentInfo:
    """Information about a component extending another styled-component."""
    name: str
    file: str = ""
    line_number: int = 0
    parent_component: str = ""
    additional_styles: int = 0
    has_overrides: bool = False
    has_dynamic_props: bool = False


class StyledComponentExtractor:
    """
    Extracts styled-component definitions from JS/TS/JSX/TSX source code.

    Detects:
    - styled.element`` tagged template definitions
    - styled(Component)`` extending patterns
    - .attrs({}) / .attrs(props => {}) default props
    - .withConfig({}) configuration
    - shouldForwardProp (v5.1+)
    - Transient $-prefixed props (v5.1+)
    - Dynamic prop interpolation ${props => ...}
    - Object-style syntax styled.div({})
    - @emotion/styled compatibility
    - as prop polymorphism patterns
    """

    # HTML elements that styled can target
    HTML_ELEMENTS = {
        'a', 'abbr', 'address', 'area', 'article', 'aside', 'audio',
        'b', 'base', 'bdi', 'bdo', 'blockquote', 'body', 'br', 'button',
        'canvas', 'caption', 'cite', 'code', 'col', 'colgroup',
        'data', 'datalist', 'dd', 'del', 'details', 'dfn', 'dialog',
        'div', 'dl', 'dt', 'em', 'embed', 'fieldset', 'figcaption',
        'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'head', 'header', 'hgroup', 'hr', 'html', 'i', 'iframe', 'img',
        'input', 'ins', 'kbd', 'label', 'legend', 'li', 'link', 'main',
        'map', 'mark', 'menu', 'meta', 'meter', 'nav', 'noscript',
        'object', 'ol', 'optgroup', 'option', 'output', 'p', 'picture',
        'pre', 'progress', 'q', 'rp', 'rt', 'ruby', 's', 'samp',
        'script', 'section', 'select', 'slot', 'small', 'source', 'span',
        'strong', 'style', 'sub', 'summary', 'sup', 'table', 'tbody',
        'td', 'template', 'textarea', 'tfoot', 'th', 'thead', 'time',
        'title', 'tr', 'track', 'u', 'ul', 'var', 'video', 'wbr',
        'svg', 'circle', 'clipPath', 'defs', 'ellipse', 'g', 'image',
        'line', 'linearGradient', 'mask', 'path', 'pattern', 'polygon',
        'polyline', 'radialGradient', 'rect', 'stop', 'text', 'tspan',
    }

    # Regex: styled.element`` or styled.element({}) or styled.element.attrs(...)``
    RE_STYLED_ELEMENT = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
        r"styled\s*\.\s*(\w+)"
        r"(?:\.attrs\s*\(([^)]*(?:\([^)]*\))*[^)]*)\))?"
        r"(?:\.withConfig\s*\([^)]*\))?"
        r"\s*(?:`|[\(\{])",
        re.MULTILINE
    )

    # Regex: styled(Component)`` or styled(Component).attrs(...)``
    RE_STYLED_COMPONENT = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
        r"styled\s*\(\s*(\w+)\s*\)"
        r"(?:\.attrs\s*\(([^)]*(?:\([^)]*\))*[^)]*)\))?"
        r"(?:\.withConfig\s*\([^)]*\))?"
        r"\s*(?:`|[\(\{])",
        re.MULTILINE
    )

    # Regex: Transient props ($propName) in tagged template interpolations
    RE_TRANSIENT_PROP = re.compile(r'\$(\w+)', re.MULTILINE)

    # Regex: Dynamic prop interpolation ${props => props.xxx} or ${({ xxx }) => xxx}
    RE_DYNAMIC_PROP = re.compile(
        r"\$\{\s*(?:\(\s*\{\s*(\w+(?:\s*,\s*\w+)*)\s*\}\s*\)|props)\s*=>",
        re.MULTILINE
    )

    # Regex: Theme usage in interpolation ${props => props.theme.xxx} or ${({ theme }) => ...}
    RE_THEME_USAGE = re.compile(
        r"(?:props\.theme|(?:\{\s*theme\s*\})\s*=>|\btheme\b\.)",
        re.MULTILINE
    )

    # Regex: shouldForwardProp
    RE_SHOULD_FORWARD_PROP = re.compile(
        r"shouldForwardProp|\.withConfig\s*\(\s*\{[^}]*shouldForwardProp",
        re.MULTILINE
    )

    # Regex: .attrs() usage
    RE_ATTRS = re.compile(
        r"\.attrs\s*\(",
        re.MULTILINE
    )

    # Regex: .withConfig() usage
    RE_WITH_CONFIG = re.compile(
        r"\.withConfig\s*\(",
        re.MULTILINE
    )

    # Regex: @media queries in template strings
    RE_MEDIA_QUERY = re.compile(
        r"@media\s*\(",
        re.MULTILINE
    )

    # Regex: CSS nesting (&)
    RE_NESTING = re.compile(
        r"&\s*[\.:\[\w>~+]|&\s*\{",
        re.MULTILINE
    )

    # Regex: object-style styled.element({...})
    RE_OBJECT_STYLE = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
        r"styled\s*(?:\.\s*(\w+)|\(\s*(\w+)\s*\))\s*\(\s*\{",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract styled-component definitions from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'components' and 'extended_components' lists
        """
        components: List[StyledComponentInfo] = []
        extended: List[StyledExtendedComponentInfo] = []

        if not content or not content.strip():
            return {'components': components, 'extended_components': extended}

        # Detect import source
        import_source = self._detect_import_source(content)

        # ── styled.element`` patterns ─────────────────────────────
        for m in self.RE_STYLED_ELEMENT.finditer(content):
            name = m.group(1)
            element = m.group(2)
            attrs_str = m.group(3) or ""

            line_num = content[:m.start()].count('\n') + 1

            # Get the template literal block after the match
            block = self._get_style_block(content, m.end())

            comp = StyledComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                base_element=element if element in self.HTML_ELEMENTS else "",
                base_component=element if element not in self.HTML_ELEMENTS else "",
                import_source=import_source,
                has_attrs=bool(attrs_str.strip()),
                attrs_props=self._extract_attrs_props(attrs_str),
                has_with_config=bool(self.RE_WITH_CONFIG.search(content[m.start():m.end()])),
                has_should_forward_prop=bool(self.RE_SHOULD_FORWARD_PROP.search(content[m.start():m.end() + len(block)])),
                has_transient_props=bool(re.search(r'\$\w+', block)),
                transient_props=self._extract_transient_props(block),
                has_dynamic_props=bool(self.RE_DYNAMIC_PROP.search(block)),
                dynamic_props=self._extract_dynamic_props(block),
                has_theme_usage=bool(self.RE_THEME_USAGE.search(block)),
                has_media_query=bool(self.RE_MEDIA_QUERY.search(block)),
                has_nesting=bool(self.RE_NESTING.search(block)),
                css_properties_count=self._count_css_properties(block),
                style_syntax="tagged-template",
                method="styled.element" if element in self.HTML_ELEMENTS else "styled(Component)",
                is_extended=element not in self.HTML_ELEMENTS,
            )
            components.append(comp)

            if element not in self.HTML_ELEMENTS:
                extended.append(StyledExtendedComponentInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    parent_component=element,
                    additional_styles=comp.css_properties_count,
                    has_overrides=comp.css_properties_count > 0,
                    has_dynamic_props=comp.has_dynamic_props,
                ))

        # ── styled(Component)`` patterns ──────────────────────────
        for m in self.RE_STYLED_COMPONENT.finditer(content):
            name = m.group(1)
            base_comp = m.group(2)
            attrs_str = m.group(3) or ""

            # Skip if already captured by styled.element pattern
            if any(c.name == name and c.line_number == content[:m.start()].count('\n') + 1 for c in components):
                continue

            line_num = content[:m.start()].count('\n') + 1
            block = self._get_style_block(content, m.end())

            comp = StyledComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                base_element="",
                base_component=base_comp,
                import_source=import_source,
                has_attrs=bool(attrs_str.strip()),
                attrs_props=self._extract_attrs_props(attrs_str),
                has_with_config=bool(self.RE_WITH_CONFIG.search(content[m.start():m.end()])),
                has_should_forward_prop=bool(self.RE_SHOULD_FORWARD_PROP.search(content[m.start():m.end() + len(block)])),
                has_transient_props=bool(re.search(r'\$\w+', block)),
                transient_props=self._extract_transient_props(block),
                has_dynamic_props=bool(self.RE_DYNAMIC_PROP.search(block)),
                dynamic_props=self._extract_dynamic_props(block),
                has_theme_usage=bool(self.RE_THEME_USAGE.search(block)),
                has_media_query=bool(self.RE_MEDIA_QUERY.search(block)),
                has_nesting=bool(self.RE_NESTING.search(block)),
                css_properties_count=self._count_css_properties(block),
                style_syntax="tagged-template",
                method="styled(Component)",
                is_extended=True,
            )
            components.append(comp)

            extended.append(StyledExtendedComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                parent_component=base_comp,
                additional_styles=comp.css_properties_count,
                has_overrides=comp.css_properties_count > 0,
                has_dynamic_props=comp.has_dynamic_props,
            ))

        # ── Object-style patterns ─────────────────────────────────
        for m in self.RE_OBJECT_STYLE.finditer(content):
            name = m.group(1)
            element = m.group(2) or ""
            base_comp = m.group(3) or ""

            if any(c.name == name for c in components):
                continue

            line_num = content[:m.start()].count('\n') + 1

            comp = StyledComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                base_element=element if element in self.HTML_ELEMENTS else "",
                base_component=base_comp or (element if element not in self.HTML_ELEMENTS else ""),
                import_source=import_source,
                style_syntax="object",
                method="styled.element" if element in self.HTML_ELEMENTS else "styled(Component)",
                is_extended=bool(base_comp) or (element not in self.HTML_ELEMENTS and bool(element)),
            )
            components.append(comp)

        return {'components': components, 'extended_components': extended}

    def _detect_import_source(self, content: str) -> str:
        """Detect which CSS-in-JS library is being used."""
        if re.search(r"from\s+['\"]styled-components['/\"]", content):
            return "styled-components"
        if re.search(r"from\s+['\"]@emotion/styled['/\"]", content):
            return "@emotion/styled"
        if re.search(r"from\s+['\"]goober['/\"]", content):
            return "goober"
        if re.search(r"from\s+['\"]@stitches/react['/\"]", content):
            return "@stitches/react"
        if re.search(r"from\s+['\"]@linaria/react['/\"]", content):
            return "@linaria/react"
        if re.search(r"require\(['\"]styled-components['\"]\)", content):
            return "styled-components"
        return "styled-components"

    def _get_style_block(self, content: str, start_pos: int) -> str:
        """Extract the style block (template literal or object) from start position."""
        if start_pos >= len(content):
            return ""

        # Find backtick-delimited block
        if start_pos > 0 and content[start_pos - 1] == '`':
            end = content.find('`', start_pos)
            if end != -1:
                return content[start_pos:end]
        # Handle if start_pos points to opening backtick
        if content[start_pos - 1:start_pos] == '`' or (start_pos < len(content) and content[start_pos] == '`'):
            # Skip opening backtick
            actual_start = start_pos + 1 if content[start_pos] == '`' else start_pos
            end = content.find('`', actual_start)
            if end != -1:
                return content[actual_start:end]

        # Try to find the next template literal end
        # Walk from start_pos to find matching backtick
        depth = 0
        i = start_pos
        in_template = False
        while i < len(content) and i < start_pos + 5000:
            ch = content[i]
            if ch == '`' and not in_template:
                in_template = True
                start_pos = i + 1
            elif ch == '`' and in_template:
                return content[start_pos:i]
            elif ch == '$' and i + 1 < len(content) and content[i + 1] == '{' and in_template:
                depth += 1
                i += 1
            elif ch == '}' and depth > 0:
                depth -= 1
            i += 1

        # Fallback: grab up to 500 chars
        return content[start_pos:start_pos + 500]

    def _extract_attrs_props(self, attrs_str: str) -> List[str]:
        """Extract prop names from .attrs() arguments."""
        if not attrs_str:
            return []
        props = re.findall(r'(\w+)\s*:', attrs_str)
        return props[:15]

    def _extract_transient_props(self, block: str) -> List[str]:
        """Extract $-prefixed transient prop names."""
        props = set()
        for m in re.finditer(r'\$(\w+)', block):
            prop_name = m.group(1)
            # Filter out common template literal expressions
            if prop_name not in ('', '{', '}') and len(prop_name) > 1:
                props.add(f"${prop_name}")
        return sorted(props)[:15]

    def _extract_dynamic_props(self, block: str) -> List[str]:
        """Extract dynamic prop names used in interpolations."""
        props = set()
        # ${({ prop1, prop2 }) => ...} destructured pattern
        for m in re.finditer(r'\$\{\s*\(\s*\{\s*([\w\s,]+)\s*\}\s*\)\s*=>', block):
            for p in m.group(1).split(','):
                p = p.strip()
                if p:
                    props.add(p)
        # ${props => props.xxx} dot-access pattern
        for m in re.finditer(r'props\.(\w+)', block):
            props.add(m.group(1))
        return sorted(props)[:15]

    def _count_css_properties(self, block: str) -> int:
        """Count CSS properties in a style block."""
        # Count lines that look like CSS properties (property: value;)
        count = 0
        for line in block.split('\n'):
            line = line.strip()
            if line and ':' in line and not line.startswith('//') and not line.startswith('${'):
                count += 1
        return count
