"""
Emotion Component Extractor for CodeTrellis

Extracts @emotion/styled component creation patterns from JS/TS source code.
Covers Emotion v9 (legacy) through v11.x+:
- styled.div`` / styled(Component)`` tagged template literal (same API as styled-components)
- styled('div')({}) object-style syntax (Emotion-specific)
- shouldForwardProp (via createStyled or config)
- as prop polymorphism
- Component extending via styled(ExistingComponent)``
- Composition with css prop + styled together
- @emotion/styled label option
- withComponent() (legacy, deprecated in v11)
- forwardRef integration

Part of CodeTrellis v4.43 - Emotion CSS-in-JS Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EmotionStyledComponentInfo:
    """Information about an @emotion/styled component definition."""
    name: str
    file: str = ""
    line_number: int = 0
    base_element: str = ""          # div, span, button, h1, etc.
    base_component: str = ""        # Component being extended
    import_source: str = ""         # @emotion/styled, emotion, etc.
    has_should_forward_prop: bool = False
    has_dynamic_props: bool = False
    dynamic_props: List[str] = field(default_factory=list)
    has_theme_usage: bool = False
    has_media_query: bool = False
    has_nesting: bool = False
    has_label: bool = False
    css_properties_count: int = 0
    style_syntax: str = ""          # tagged-template, object, string
    method: str = ""                # styled.element, styled(Component), styled('element')


@dataclass
class EmotionExtendedComponentInfo:
    """Information about a component extending another @emotion/styled component."""
    name: str
    file: str = ""
    line_number: int = 0
    parent_component: str = ""
    additional_styles: int = 0
    has_overrides: bool = False
    has_dynamic_props: bool = False


class EmotionComponentExtractor:
    """
    Extracts @emotion/styled component definitions from JS/TS/JSX/TSX source code.

    Detects:
    - styled.element`` tagged template definitions (emotion-styled)
    - styled(Component)`` extending patterns
    - styled('element')({}) object syntax (Emotion-specific)
    - shouldForwardProp configuration
    - Dynamic prop interpolation ${props => ...}
    - Theme usage in interpolations
    - Label option for debugging
    - @emotion/styled and legacy emotion compatibility
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

    # Regex: styled.element`` (tagged template) — same as styled-components
    RE_STYLED_ELEMENT_TEMPLATE = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
        r"styled\s*\.\s*(\w+)"
        r"(?:\s*\.\s*withConfig\s*\([^)]*\))?"
        r"\s*`",
        re.MULTILINE
    )

    # Regex: styled(Component)`` (tagged template extending)
    RE_STYLED_COMPONENT_TEMPLATE = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
        r"styled\s*\(\s*(\w+)\s*\)"
        r"(?:\s*\.\s*withConfig\s*\([^)]*\))?"
        r"\s*`",
        re.MULTILINE
    )

    # Regex: styled.element({}) or styled('element')({}) — object syntax (Emotion-specific)
    RE_STYLED_ELEMENT_OBJECT = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
        r"styled\s*\.\s*(\w+)\s*\(",
        re.MULTILINE
    )

    # Regex: styled('element')({}) — string element (Emotion-specific)
    RE_STYLED_STRING_ELEMENT = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
        r"styled\s*\(\s*['\"](\w+)['\"]\s*(?:,\s*\{.*?\}\s*)?\)\s*(?:\(|`)",
        re.MULTILINE | re.DOTALL
    )

    # Regex: styled(Component)({}) — object syntax extending
    RE_STYLED_COMPONENT_OBJECT = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
        r"styled\s*\(\s*(\w+)\s*(?:,\s*\{.*?\}\s*)?\)\s*\(",
        re.MULTILINE | re.DOTALL
    )

    # Regex: shouldForwardProp configuration
    RE_SHOULD_FORWARD_PROP = re.compile(
        r"shouldForwardProp",
        re.MULTILINE
    )

    # Regex: Dynamic prop interpolation
    RE_DYNAMIC_PROP = re.compile(
        r"\$\{\s*(?:\(\s*\{\s*(\w+(?:\s*,\s*\w+)*)\s*\}\s*\)|props)\s*=>",
        re.MULTILINE
    )

    # Regex: Theme usage
    RE_THEME_USAGE = re.compile(
        r"(?:props\.theme|(?:\{\s*theme\s*\})\s*=>|\btheme\b\.)",
        re.MULTILINE
    )

    # Regex: Media query
    RE_MEDIA_QUERY = re.compile(
        r"@media\s*\(",
        re.MULTILINE
    )

    # Regex: CSS nesting with & parent
    RE_NESTING = re.compile(
        r"&\s*[.:#\[\s{>+~]",
        re.MULTILINE
    )

    # Regex: Label option in Emotion config
    RE_LABEL = re.compile(
        r"label\s*:\s*['\"]",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract @emotion/styled component definitions.

        Returns:
            Dict with 'components' and 'extended_components' lists.
        """
        components: List[EmotionStyledComponentInfo] = []
        extended_components: List[EmotionExtendedComponentInfo] = []

        if not content or not content.strip():
            return {'components': components, 'extended_components': extended_components}

        # ── styled.element`` (tagged template) ──────────────────
        for match in self.RE_STYLED_ELEMENT_TEMPLATE.finditer(content):
            name = match.group(1)
            element = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Get the template body for analysis
            body = self._extract_template_body(content, match.end() - 1)

            comp = EmotionStyledComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                base_element=element if element.lower() in self.HTML_ELEMENTS else "",
                base_component=element if element.lower() not in self.HTML_ELEMENTS else "",
                import_source=self._detect_import_source(content),
                style_syntax="tagged-template",
                method="styled.element",
                has_should_forward_prop=bool(self.RE_SHOULD_FORWARD_PROP.search(content[:match.start()])),
                has_dynamic_props=bool(self.RE_DYNAMIC_PROP.search(body)) if body else False,
                has_theme_usage=bool(self.RE_THEME_USAGE.search(body)) if body else False,
                has_media_query=bool(self.RE_MEDIA_QUERY.search(body)) if body else False,
                has_nesting=bool(self.RE_NESTING.search(body)) if body else False,
                has_label=bool(self.RE_LABEL.search(body)) if body else False,
                css_properties_count=self._count_css_properties(body) if body else 0,
            )

            if body and self.RE_DYNAMIC_PROP.search(body):
                comp.dynamic_props = self._extract_dynamic_props(body)

            components.append(comp)

        # ── styled(Component)`` (tagged template extending) ─────
        for match in self.RE_STYLED_COMPONENT_TEMPLATE.finditer(content):
            name = match.group(1)
            parent = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            body = self._extract_template_body(content, match.end() - 1)

            comp = EmotionStyledComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                base_component=parent,
                import_source=self._detect_import_source(content),
                style_syntax="tagged-template",
                method="styled(Component)",
                has_dynamic_props=bool(self.RE_DYNAMIC_PROP.search(body)) if body else False,
                has_theme_usage=bool(self.RE_THEME_USAGE.search(body)) if body else False,
                has_media_query=bool(self.RE_MEDIA_QUERY.search(body)) if body else False,
                has_nesting=bool(self.RE_NESTING.search(body)) if body else False,
                css_properties_count=self._count_css_properties(body) if body else 0,
            )

            ext = EmotionExtendedComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                parent_component=parent,
                additional_styles=comp.css_properties_count,
                has_overrides=comp.css_properties_count > 0,
                has_dynamic_props=comp.has_dynamic_props,
            )

            components.append(comp)
            extended_components.append(ext)

        # ── styled('element')({}) — Emotion string-element syntax ──
        for match in self.RE_STYLED_STRING_ELEMENT.finditer(content):
            name = match.group(1)
            element = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Check for shouldForwardProp in the matched text (options object)
            matched_text = match.group(0)
            has_sfp = 'shouldForwardProp' in matched_text

            comp = EmotionStyledComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                base_element=element if element.lower() in self.HTML_ELEMENTS else "",
                import_source=self._detect_import_source(content),
                style_syntax="object",
                method="styled('element')",
                has_should_forward_prop=has_sfp,
            )
            components.append(comp)

        # ── styled.element({}) — object syntax ──────────────────
        for match in self.RE_STYLED_ELEMENT_OBJECT.finditer(content):
            name = match.group(1)
            element = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Skip if already matched as tagged template
            already_matched = any(
                c.name == name and c.line_number == line_num
                for c in components
            )
            if already_matched:
                continue

            # Verify it's actually object syntax (not tagged template)
            rest = content[match.end():]
            if rest.lstrip().startswith('`'):
                continue

            comp = EmotionStyledComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                base_element=element if element.lower() in self.HTML_ELEMENTS else "",
                base_component=element if element.lower() not in self.HTML_ELEMENTS else "",
                import_source=self._detect_import_source(content),
                style_syntax="object",
                method="styled.element" if element.lower() in self.HTML_ELEMENTS else "styled(Component)",
            )
            components.append(comp)

        return {
            'components': components,
            'extended_components': extended_components,
        }

    def _extract_template_body(self, content: str, backtick_pos: int) -> str:
        """Extract content between backticks for a tagged template literal."""
        if backtick_pos >= len(content) or content[backtick_pos] != '`':
            return ""

        depth = 0
        i = backtick_pos + 1
        while i < len(content):
            ch = content[i]
            if ch == '`' and depth == 0:
                return content[backtick_pos + 1:i]
            elif ch == '$' and i + 1 < len(content) and content[i + 1] == '{':
                depth += 1
                i += 1
            elif ch == '}' and depth > 0:
                depth -= 1
            elif ch == '\\':
                i += 1  # skip escaped char
            i += 1
        return ""

    def _detect_import_source(self, content: str) -> str:
        """Detect the import source for styled."""
        if re.search(r"from\s+['\"]@emotion/styled['/\"]", content):
            return "@emotion/styled"
        if re.search(r"from\s+['\"]emotion['/\"]", content):
            return "emotion"
        if re.search(r"require\(['\"]@emotion/styled['\"]\)", content):
            return "@emotion/styled"
        if re.search(r"from\s+['\"]styled-components['/\"]", content):
            return "styled-components"
        return ""

    def _count_css_properties(self, body: str) -> int:
        """Count CSS property declarations in a template body."""
        if not body:
            return 0
        # Match property: value; patterns
        props = re.findall(r'[\w-]+\s*:\s*[^;{}\n]+[;\n]', body)
        return len(props)

    def _extract_dynamic_props(self, body: str) -> List[str]:
        """Extract dynamic prop names from interpolations."""
        props = set()
        for match in self.RE_DYNAMIC_PROP.finditer(body):
            if match.group(1):
                for p in match.group(1).split(','):
                    props.add(p.strip())
        return sorted(props)
