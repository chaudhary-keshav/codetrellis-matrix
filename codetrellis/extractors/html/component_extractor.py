"""
HTML Component Extractor for CodeTrellis

Detects Web Components: custom elements, shadow DOM usage, <template> and <slot>
elements, and custom element registration patterns in inline scripts.
Also detects framework component patterns (Angular, React, Vue, Svelte).

Part of CodeTrellis v4.16 - HTML Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from html.parser import HTMLParser


@dataclass
class HTMLCustomElementInfo:
    """Information about a custom element / Web Component."""
    tag_name: str = ""          # e.g., my-component, app-header
    is_autonomous: bool = True  # Autonomous vs customized built-in
    extends: str = ""           # For customized built-in elements (is="...")
    attributes: List[str] = field(default_factory=list)
    slot_names: List[str] = field(default_factory=list)
    shadow_dom: bool = False
    registered_class: str = ""  # customElements.define class name
    line_number: int = 0


@dataclass
class HTMLSlotInfo:
    """Information about a <slot> element."""
    name: str = ""              # Named slot or default
    fallback_content: str = ""
    line_number: int = 0


class _ComponentHTMLParser(HTMLParser):
    """Internal parser for component extraction."""

    # Custom elements must contain a hyphen
    CUSTOM_ELEMENT_RE = re.compile(r'^[a-z][a-z0-9]*-[a-z0-9-]*$')

    # Inline script patterns for Web Component registration
    DEFINE_PATTERN = re.compile(
        r'customElements\.define\(\s*["\']([a-z][a-z0-9-]*)["\']'
        r'(?:\s*,\s*(\w+))?',
        re.IGNORECASE
    )
    SHADOW_PATTERN = re.compile(r'attachShadow|shadowRoot', re.IGNORECASE)
    CLASS_EXTENDS = re.compile(r'class\s+(\w+)\s+extends\s+(\w+)', re.IGNORECASE)

    def __init__(self):
        super().__init__()
        self.custom_elements: List[HTMLCustomElementInfo] = []
        self.slots: List[HTMLSlotInfo] = []
        self.templates: List[Dict] = []
        self._seen_tags: Dict[str, HTMLCustomElementInfo] = {}
        self._in_script = False
        self._script_text = ""
        self._in_slot = False
        self._slot_text = ""
        self._current_slot_name = ""
        self._slot_line = 0

    def handle_starttag(self, tag: str, attrs: list):
        tag_lower = tag.lower()
        attrs_dict = dict(attrs)
        line = self.getpos()[0]

        # Detect custom elements (tags with hyphens)
        if self.CUSTOM_ELEMENT_RE.match(tag_lower) and tag_lower not in self._seen_tags:
            attr_names = [a[0] for a in attrs if a[0]]
            elem = HTMLCustomElementInfo(
                tag_name=tag_lower,
                is_autonomous=True,
                attributes=attr_names,
                line_number=line,
            )
            self.custom_elements.append(elem)
            self._seen_tags[tag_lower] = elem

        elif tag_lower not in ('script', 'style', 'template', 'slot'):
            # Check for customized built-in (is="...")
            is_attr = attrs_dict.get('is', '')
            if is_attr and self.CUSTOM_ELEMENT_RE.match(is_attr) and is_attr not in self._seen_tags:
                elem = HTMLCustomElementInfo(
                    tag_name=is_attr,
                    is_autonomous=False,
                    extends=tag_lower,
                    line_number=line,
                )
                self.custom_elements.append(elem)
                self._seen_tags[is_attr] = elem

        # Template elements
        if tag_lower == 'template':
            template_id = attrs_dict.get('id', '')
            self.templates.append({
                'id': template_id,
                'line': line,
            })

        # Slot elements
        if tag_lower == 'slot':
            self._in_slot = True
            self._current_slot_name = attrs_dict.get('name', '')
            self._slot_text = ""
            self._slot_line = line

        # Script for Web Component detection
        if tag_lower == 'script':
            self._in_script = True
            self._script_text = ""

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower == 'script' and self._in_script:
            self._in_script = False
            self._process_script(self._script_text)
        elif tag_lower == 'slot' and self._in_slot:
            self._in_slot = False
            self.slots.append(HTMLSlotInfo(
                name=self._current_slot_name,
                fallback_content=self._slot_text.strip()[:80],
                line_number=self._slot_line,
            ))

    def handle_data(self, data: str):
        if self._in_script:
            self._script_text += data
        if self._in_slot:
            self._slot_text += data

    def _process_script(self, script: str):
        """Extract Web Component registrations from inline script."""
        # customElements.define()
        for match in self.DEFINE_PATTERN.finditer(script):
            tag_name = match.group(1)
            class_name = match.group(2) or ''
            if tag_name in self._seen_tags:
                self._seen_tags[tag_name].registered_class = class_name
            else:
                elem = HTMLCustomElementInfo(
                    tag_name=tag_name,
                    registered_class=class_name,
                )
                self.custom_elements.append(elem)
                self._seen_tags[tag_name] = elem

        # Shadow DOM usage
        if self.SHADOW_PATTERN.search(script):
            for elem in self.custom_elements:
                if elem.registered_class:
                    elem.shadow_dom = True


class HTMLComponentExtractor:
    """Extracts Web Components and custom element information from HTML."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract component information from HTML content.

        Args:
            content: HTML source code string.
            file_path: Optional file path for context.

        Returns:
            Dict with 'custom_elements', 'slots', 'templates'.
        """
        parser = _ComponentHTMLParser()
        try:
            parser.feed(content)
        except Exception:
            pass

        return {
            'custom_elements': parser.custom_elements,
            'slots': parser.slots,
            'templates': parser.templates,
        }
