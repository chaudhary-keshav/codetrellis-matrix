"""
Lit Template Extractor for CodeTrellis

Extracts Lit template patterns from JavaScript/TypeScript source code:
- html`` tagged template literals
- svg`` tagged template literals
- css`` tagged template literals (static styles, shared styles)
- Template directives (repeat, map, classMap, styleMap, ref, cache, guard, etc.)
- Template expressions and bindings (.prop, ?attr, @event)
- nothing / noChange sentinels
- unsafeHTML / unsafeSVG usage
- Shared styles patterns (adoptedStyleSheets, CSSStyleSheet)

Supports:
- lit-html 1.x (html, svg, render, directives)
- lit-html 2.x / lit 2.x (html, svg, css, nothing, noChange)
- lit 3.x (enhanced directives)
- @lit-labs/ssr (server-side rendering templates)
- Polymer html`` usage

Part of CodeTrellis v4.65 - Lit / Web Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class LitTemplateInfo:
    """Information about a lit-html template usage."""
    template_type: str = "html"  # html, svg
    file: str = ""
    line_number: int = 0
    binding_count: int = 0
    property_bindings: int = 0  # .prop=
    attribute_bindings: int = 0  # attr= or ?attr=
    event_bindings: int = 0  # @event=
    has_conditional: bool = False  # ternary or when/choose
    has_loop: bool = False  # map/repeat
    has_slot: bool = False  # <slot> element
    nesting_depth: int = 0  # nested html`` depth
    component_name: str = ""


@dataclass
class LitDirectiveUsageInfo:
    """Information about a Lit template directive usage."""
    directive_name: str  # repeat, classMap, styleMap, ref, etc.
    file: str = ""
    line_number: int = 0
    category: str = ""  # rendering, styling, async, caching, reference, unsafe
    import_source: str = ""  # lit/directives/repeat, etc.
    component_name: str = ""


@dataclass
class LitCSSInfo:
    """Information about a Lit CSS style definition."""
    style_type: str = "static"  # static, shared, adopted, inline
    file: str = ""
    line_number: int = 0
    has_css_custom_properties: bool = False  # Uses --custom-property
    has_host_selector: bool = False  # :host selector
    has_part_selector: bool = False  # ::part() selector
    has_slotted_selector: bool = False  # ::slotted() selector
    has_media_query: bool = False
    variable_count: int = 0  # Number of CSS custom properties defined
    component_name: str = ""
    is_shared: bool = False  # Exported/reused across components


class LitTemplateExtractor:
    """
    Extracts template, directive, and CSS patterns from Lit source code.

    Detects:
    - html`<div .prop=${val} ?hidden=${bool} @click=${handler}>...</div>`
    - svg`<circle r=${radius} />`
    - css`:host { --color: red; } ::slotted(span) { color: blue; }`
    - Directive usage: repeat, classMap, styleMap, ref, cache, guard, etc.
    - nothing, noChange sentinels
    - unsafeHTML, unsafeSVG directives
    - Shared styles and adoptedStyleSheets
    """

    # html`` tagged template
    HTML_TEMPLATE = re.compile(
        r'\bhtml\s*`',
        re.MULTILINE
    )

    # svg`` tagged template
    SVG_TEMPLATE = re.compile(
        r'\bsvg\s*`',
        re.MULTILINE
    )

    # css`` tagged template
    CSS_TEMPLATE = re.compile(
        r'\bcss\s*`',
        re.MULTILINE
    )

    # Property binding: .propName=
    PROPERTY_BINDING = re.compile(r'\.([a-zA-Z]\w*)\s*=\s*\$\{', re.MULTILINE)

    # Boolean attribute binding: ?attr=
    BOOLEAN_BINDING = re.compile(r'\?([a-zA-Z][a-zA-Z0-9-]*)\s*=\s*\$\{', re.MULTILINE)

    # Event binding: @event=
    EVENT_BINDING = re.compile(r'@([a-zA-Z][a-zA-Z0-9-]*)\s*=\s*\$\{', re.MULTILINE)

    # Regular attribute binding: attr=${expr}
    ATTR_BINDING = re.compile(r'(?<![.?@])([a-zA-Z][a-zA-Z0-9-]*)\s*=\s*\$\{', re.MULTILINE)

    # Template expression: ${expr}
    EXPRESSION = re.compile(r'\$\{', re.MULTILINE)

    # <slot> element
    SLOT_ELEMENT = re.compile(r'<slot\b', re.MULTILINE)

    # Directive imports and usages
    KNOWN_DIRECTIVES = {
        'repeat': 'rendering',
        'map': 'rendering',
        'join': 'rendering',
        'range': 'rendering',
        'when': 'rendering',
        'choose': 'rendering',
        'guard': 'caching',
        'cache': 'caching',
        'keyed': 'caching',
        'live': 'caching',
        'ref': 'reference',
        'createRef': 'reference',
        'classMap': 'styling',
        'styleMap': 'styling',
        'ifDefined': 'rendering',
        'until': 'async',
        'asyncAppend': 'async',
        'asyncReplace': 'async',
        'unsafeHTML': 'unsafe',
        'unsafeSVG': 'unsafe',
        'templateContent': 'rendering',
        'nothing': 'sentinel',
        'noChange': 'sentinel',
    }

    DIRECTIVE_USAGE = re.compile(
        r'\b(' + '|'.join(KNOWN_DIRECTIVES.keys()) + r')\s*[\(`]',
        re.MULTILINE
    )

    # Directive imports
    DIRECTIVE_IMPORT = re.compile(
        r"from\s+['\"]lit/directives/(\w+)",
        re.MULTILINE
    )

    # CSS custom properties: --property-name
    CSS_CUSTOM_PROP = re.compile(r'--[a-zA-Z][a-zA-Z0-9-]*', re.MULTILINE)

    # :host selector
    HOST_SELECTOR = re.compile(r':host\b', re.MULTILINE)

    # ::part() selector
    PART_SELECTOR = re.compile(r'::part\s*\(', re.MULTILINE)

    # ::slotted() selector
    SLOTTED_SELECTOR = re.compile(r'::slotted\s*\(', re.MULTILINE)

    # @media query
    MEDIA_QUERY = re.compile(r'@media\b', re.MULTILINE)

    # adoptedStyleSheets
    ADOPTED_STYLESHEETS = re.compile(
        r'adoptedStyleSheets|CSSStyleSheet',
        re.MULTILINE
    )

    # nothing/noChange usage
    NOTHING_SENTINEL = re.compile(r'\bnothing\b', re.MULTILINE)
    NOCHANGE_SENTINEL = re.compile(r'\bnoChange\b', re.MULTILINE)

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract template, directive, and CSS information from source code.

        Returns dict with keys: templates, directives, css_styles
        """
        templates: List[LitTemplateInfo] = []
        directives: List[LitDirectiveUsageInfo] = []
        css_styles: List[LitCSSInfo] = []

        # ── HTML templates ────────────────────────────────────────
        for m in self.HTML_TEMPLATE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            # Extract template content
            template_content = self._extract_template_literal(content, m.end() - 1)

            tpl = LitTemplateInfo(
                template_type="html",
                file=file_path,
                line_number=line_num,
            )

            if template_content:
                tpl.property_bindings = len(self.PROPERTY_BINDING.findall(template_content))
                tpl.attribute_bindings = (len(self.BOOLEAN_BINDING.findall(template_content)) +
                                           len(self.ATTR_BINDING.findall(template_content)))
                tpl.event_bindings = len(self.EVENT_BINDING.findall(template_content))
                tpl.binding_count = len(self.EXPRESSION.findall(template_content))
                tpl.has_slot = bool(self.SLOT_ELEMENT.search(template_content))
                tpl.has_conditional = '?' in template_content and '${' in template_content
                tpl.has_loop = ('repeat(' in template_content or
                                '.map(' in template_content or
                                'map(' in template_content)
                tpl.nesting_depth = template_content.count('html`')

            templates.append(tpl)

        # ── SVG templates ─────────────────────────────────────────
        for m in self.SVG_TEMPLATE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            tpl = LitTemplateInfo(
                template_type="svg",
                file=file_path,
                line_number=line_num,
            )
            templates.append(tpl)

        # ── Directive usages ──────────────────────────────────────
        for m in self.DIRECTIVE_USAGE.finditer(content):
            directive_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            category = self.KNOWN_DIRECTIVES.get(directive_name, "other")

            directive = LitDirectiveUsageInfo(
                directive_name=directive_name,
                file=file_path,
                line_number=line_num,
                category=category,
            )
            directives.append(directive)

        # ── Directive imports (to detect import sources) ──────────
        for m in self.DIRECTIVE_IMPORT.finditer(content):
            directive_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            # Check if already captured
            existing = [d for d in directives if d.directive_name == directive_name]
            if existing:
                for d in existing:
                    d.import_source = f"lit/directives/{directive_name}"
            else:
                category = self.KNOWN_DIRECTIVES.get(directive_name, "other")
                directives.append(LitDirectiveUsageInfo(
                    directive_name=directive_name,
                    file=file_path,
                    line_number=line_num,
                    category=category,
                    import_source=f"lit/directives/{directive_name}",
                ))

        # ── CSS styles (css`` tagged templates) ───────────────────
        for m in self.CSS_TEMPLATE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            css_content = self._extract_template_literal(content, m.end() - 1)

            style = LitCSSInfo(
                style_type="static",
                file=file_path,
                line_number=line_num,
            )

            if css_content:
                style.has_css_custom_properties = bool(self.CSS_CUSTOM_PROP.search(css_content))
                style.has_host_selector = bool(self.HOST_SELECTOR.search(css_content))
                style.has_part_selector = bool(self.PART_SELECTOR.search(css_content))
                style.has_slotted_selector = bool(self.SLOTTED_SELECTOR.search(css_content))
                style.has_media_query = bool(self.MEDIA_QUERY.search(css_content))
                style.variable_count = len(set(self.CSS_CUSTOM_PROP.findall(css_content)))

            # Check if exported (shared style)
            line_content = content.split('\n')[line_num - 1] if line_num <= len(content.split('\n')) else ""
            # Look backwards for export statement
            preceding = content[:m.start()].split('\n')[-1] if m.start() > 0 else ""
            style.is_shared = 'export' in preceding or 'export' in line_content

            css_styles.append(style)

        # Check for adopted stylesheets
        if self.ADOPTED_STYLESHEETS.search(content):
            for m in self.ADOPTED_STYLESHEETS.finditer(content):
                line_num = content[:m.start()].count('\n') + 1
                css_styles.append(LitCSSInfo(
                    style_type="adopted",
                    file=file_path,
                    line_number=line_num,
                ))

        return {
            'templates': templates,
            'directives': directives,
            'css_styles': css_styles,
        }

    def _extract_template_literal(self, content: str, backtick_pos: int) -> str:
        """Extract content from a tagged template literal starting at backtick_pos."""
        if backtick_pos >= len(content) or content[backtick_pos] != '`':
            return ""
        pos = backtick_pos + 1
        depth = 0  # Track ${} nesting
        result = []
        while pos < len(content):
            ch = content[pos]
            if ch == '`' and depth == 0:
                break
            elif ch == '$' and pos + 1 < len(content) and content[pos + 1] == '{':
                depth += 1
                result.append('${')
                pos += 2
                continue
            elif ch == '{' and depth > 0:
                depth += 1
            elif ch == '}' and depth > 0:
                depth -= 1
            elif ch == '\\':
                pos += 2
                continue
            result.append(ch)
            pos += 1
        return ''.join(result)
