"""
Astro Component Extractor v1.0

Extracts component-level information from .astro files:
- Component name (derived from filename)
- Props interface (Astro.props, Props type/interface)
- Slots (default, named via <slot name="...">)
- Template expressions ({expression})
- Component imports and usage
- Directives (set:html, set:text, class:list, define:vars)
- Fragment usage
- is:inline, is:global, is:raw directives
- Scoped styles (<style> in .astro files)

Part of CodeTrellis v4.60 - Astro Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class AstroSlotInfo:
    """Information about a slot in an Astro component."""
    name: str = "default"  # default or named slot
    line_number: int = 0
    has_fallback: bool = False
    is_named: bool = False


@dataclass
class AstroExpressionInfo:
    """Information about a template expression in an Astro component."""
    expression: str = ""
    line_number: int = 0
    expression_type: str = ""  # variable, function_call, conditional, map, spread


@dataclass
class AstroComponentInfo:
    """Information about an Astro component."""
    name: str = ""
    file_path: str = ""
    line_number: int = 0

    # Props
    has_props: bool = False
    props_type: str = ""  # TypeScript type name for Props
    prop_names: List[str] = field(default_factory=list)
    has_rest_props: bool = False

    # Slots
    slots: List[AstroSlotInfo] = field(default_factory=list)
    has_default_slot: bool = False
    has_named_slots: bool = False

    # Template
    expressions: List[AstroExpressionInfo] = field(default_factory=list)
    component_imports: List[str] = field(default_factory=list)
    used_components: List[str] = field(default_factory=list)

    # Directives
    has_set_html: bool = False
    has_set_text: bool = False
    has_class_list: bool = False
    has_define_vars: bool = False
    has_is_inline: bool = False
    has_is_global: bool = False
    has_is_raw: bool = False

    # Scoped styles
    has_scoped_style: bool = False
    has_global_style: bool = False
    style_lang: str = ""  # css, scss, less, stylus, postcss

    # Fragment
    has_fragment: bool = False

    # Head / SEO
    has_head_content: bool = False
    has_view_transitions: bool = False

    # Misc
    is_layout: bool = False
    is_page: bool = False
    is_exported: bool = True  # Astro components are always exported


class AstroComponentExtractor:
    """Extracts component information from Astro files."""

    # Pattern to match Props interface or type
    PROPS_INTERFACE_PATTERN = re.compile(
        r'(?:interface|type)\s+Props\s*(?:extends\s+[^{]+)?\s*[{=]',
        re.MULTILINE
    )

    # Pattern for Astro.props destructuring
    ASTRO_PROPS_PATTERN = re.compile(
        r'(?:const|let)\s+\{([^}]+)\}\s*(?::\s*Props)?\s*=\s*Astro\.props',
        re.MULTILINE
    )

    # Pattern for Astro.props direct access
    ASTRO_PROPS_DIRECT = re.compile(
        r'Astro\.props(?:\.\w+|\[)',
        re.MULTILINE
    )

    # Slot patterns
    SLOT_DEFAULT = re.compile(r'<slot\s*/?\s*>', re.MULTILINE)
    SLOT_NAMED = re.compile(
        r'<slot\s+name\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    SLOT_FALLBACK = re.compile(
        r'<slot[^>]*>(?!\s*</slot>).+?</slot>',
        re.DOTALL
    )

    # Template expression patterns
    EXPRESSION_PATTERN = re.compile(
        r'\{([^}]+)\}',
        re.MULTILINE
    )

    # Component import pattern (in frontmatter)
    COMPONENT_IMPORT = re.compile(
        r"import\s+(\w+)\s+from\s+['\"]([^'\"]+\.astro)['\"]",
        re.MULTILINE
    )

    # JSX/TSX component import
    FRAMEWORK_COMPONENT_IMPORT = re.compile(
        r"import\s+(\w+)\s+from\s+['\"]([^'\"]+(?:\.(?:jsx|tsx|svelte|vue|solid))?)['\"]",
        re.MULTILINE
    )

    # Directive patterns
    SET_HTML = re.compile(r'set:html\s*=', re.MULTILINE)
    SET_TEXT = re.compile(r'set:text\s*=', re.MULTILINE)
    CLASS_LIST = re.compile(r'class:list\s*=', re.MULTILINE)
    DEFINE_VARS = re.compile(r'define:vars\s*=', re.MULTILINE)
    IS_INLINE = re.compile(r'is:inline\b', re.MULTILINE)
    IS_GLOBAL = re.compile(r'is:global\b', re.MULTILINE)
    IS_RAW = re.compile(r'is:raw\b', re.MULTILINE)

    # Style tag patterns
    STYLE_TAG = re.compile(
        r'<style(?:\s+[^>]*)?>',
        re.MULTILINE
    )
    STYLE_LANG = re.compile(
        r'<style\s+[^>]*lang\s*=\s*["\'](\w+)["\']',
        re.MULTILINE
    )
    STYLE_GLOBAL = re.compile(
        r'<style\s+[^>]*is:global\b',
        re.MULTILINE
    )

    # Fragment pattern
    FRAGMENT_PATTERN = re.compile(r'<Fragment\b|<>', re.MULTILINE)

    # View transitions
    VIEW_TRANSITIONS = re.compile(
        r'<ViewTransitions\b|transition:(?:name|animate|persist)',
        re.MULTILINE
    )

    # Used component detection (PascalCase tags in template)
    USED_COMPONENT = re.compile(
        r'<([A-Z][a-zA-Z0-9]*)\b',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract component information from an Astro file.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with component information
        """
        # Split into frontmatter and template
        frontmatter, template = self._split_frontmatter(content)

        comp = AstroComponentInfo()
        comp.file_path = file_path

        # Component name from filename
        if file_path:
            import os
            name = os.path.basename(file_path).replace('.astro', '')
            comp.name = name
            # Detect layout/page
            comp.is_layout = 'layout' in file_path.lower() or 'Layout' in name
            comp.is_page = '/pages/' in file_path

        # Line offset for template (after frontmatter)
        frontmatter_lines = frontmatter.count('\n') + 2 if frontmatter else 0

        # Props extraction
        self._extract_props(frontmatter, comp)

        # Slots
        self._extract_slots(template, comp, frontmatter_lines)

        # Directives
        comp.has_set_html = bool(self.SET_HTML.search(template))
        comp.has_set_text = bool(self.SET_TEXT.search(template))
        comp.has_class_list = bool(self.CLASS_LIST.search(template))
        comp.has_define_vars = bool(self.DEFINE_VARS.search(content))
        comp.has_is_inline = bool(self.IS_INLINE.search(content))
        comp.has_is_global = bool(self.IS_GLOBAL.search(content))
        comp.has_is_raw = bool(self.IS_RAW.search(template))

        # Styles
        if self.STYLE_TAG.search(content):
            comp.has_scoped_style = True
            lang_match = self.STYLE_LANG.search(content)
            if lang_match:
                comp.style_lang = lang_match.group(1)
            if self.STYLE_GLOBAL.search(content):
                comp.has_global_style = True

        # Fragment
        comp.has_fragment = bool(self.FRAGMENT_PATTERN.search(template))

        # View transitions
        comp.has_view_transitions = bool(self.VIEW_TRANSITIONS.search(content))

        # Head content
        comp.has_head_content = '<head' in template.lower() or '<title' in template.lower() or '<meta' in template.lower()

        # Component imports
        for m in self.COMPONENT_IMPORT.finditer(frontmatter):
            comp.component_imports.append(m.group(1))

        # Used components in template
        for m in self.USED_COMPONENT.finditer(template):
            tag = m.group(1)
            if tag not in ('Fragment', 'Script', 'Style') and tag not in comp.used_components:
                comp.used_components.append(tag)

        # Template expressions (simplified — skip HTML attribute values)
        self._extract_expressions(template, comp, frontmatter_lines)

        return {"components": [comp]}

    def _split_frontmatter(self, content: str) -> tuple:
        """Split an Astro file into frontmatter and template sections."""
        # Astro frontmatter is delimited by --- at the top
        fm_pattern = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
        match = fm_pattern.search(content)
        if match:
            frontmatter = match.group(1)
            template = content[match.end():]
            return frontmatter, template
        return "", content

    def _extract_props(self, frontmatter: str, comp: AstroComponentInfo) -> None:
        """Extract props from frontmatter."""
        if not frontmatter:
            return

        # Check for Props interface/type
        if self.PROPS_INTERFACE_PATTERN.search(frontmatter):
            comp.has_props = True
            comp.props_type = "Props"

        # Check for Astro.props destructuring
        match = self.ASTRO_PROPS_PATTERN.search(frontmatter)
        if match:
            comp.has_props = True
            props_str = match.group(1)
            # Extract prop names
            for prop in props_str.split(','):
                prop = prop.strip()
                if prop:
                    # Handle destructuring with defaults: name = "default"
                    prop_name = prop.split('=')[0].split(':')[0].strip()
                    if prop_name.startswith('...'):
                        comp.has_rest_props = True
                        prop_name = prop_name[3:]
                    if prop_name:
                        comp.prop_names.append(prop_name)

        # Check for direct Astro.props access
        if self.ASTRO_PROPS_DIRECT.search(frontmatter):
            comp.has_props = True

    def _extract_slots(self, template: str, comp: AstroComponentInfo, line_offset: int) -> None:
        """Extract slot information from template."""
        # Default slots
        for m in self.SLOT_DEFAULT.finditer(template):
            line = template[:m.start()].count('\n') + line_offset + 1
            comp.slots.append(AstroSlotInfo(
                name="default",
                line_number=line,
                is_named=False,
            ))
            comp.has_default_slot = True

        # Named slots
        for m in self.SLOT_NAMED.finditer(template):
            line = template[:m.start()].count('\n') + line_offset + 1
            name = m.group(1)
            comp.slots.append(AstroSlotInfo(
                name=name,
                line_number=line,
                is_named=True,
            ))
            comp.has_named_slots = True

        # Check for fallback content
        for m in self.SLOT_FALLBACK.finditer(template):
            for slot in comp.slots:
                # Mark slots that have fallback
                slot.has_fallback = True
                break

    def _extract_expressions(self, template: str, comp: AstroComponentInfo,
                             line_offset: int) -> None:
        """Extract template expressions (simplified)."""
        # Only extract top-level expressions, not HTML attributes
        for m in self.EXPRESSION_PATTERN.finditer(template):
            expr = m.group(1).strip()
            if not expr or len(expr) > 200:
                continue
            # Skip style/class attribute values and empty objects
            if expr.startswith('{') or expr.startswith("'") or expr.startswith('"'):
                continue

            line = template[:m.start()].count('\n') + line_offset + 1

            # Determine expression type
            expr_type = "variable"
            if '(' in expr:
                expr_type = "function_call"
            if '.map(' in expr or '.filter(' in expr or '.reduce(' in expr:
                expr_type = "map"
            if '?' in expr and ':' in expr:
                expr_type = "conditional"
            if expr.startswith('...'):
                expr_type = "spread"

            comp.expressions.append(AstroExpressionInfo(
                expression=expr[:100],
                line_number=line,
                expression_type=expr_type,
            ))
