"""
HTML Semantic Extractor for CodeTrellis

Extracts semantic HTML5 elements and microdata/structured data from HTML.
Detects article, nav, aside, header, footer, main, figure, figcaption,
details, summary, dialog, time, mark, progress, meter, and microdata.

Part of CodeTrellis v4.16 - HTML Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from html.parser import HTMLParser


@dataclass
class HTMLSemanticElementInfo:
    """Information about a semantic HTML element."""
    tag: str = ""
    role: str = ""
    purpose: str = ""          # auto-classified purpose
    text_preview: str = ""     # first 80 chars of inner text
    id: str = ""
    classes: List[str] = field(default_factory=list)
    attributes: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0


@dataclass
class HTMLMicrodataInfo:
    """Microdata / structured data information."""
    schema_type: str = ""      # itemtype URL
    properties: List[str] = field(default_factory=list)  # itemprop values
    scope_tag: str = ""        # tag with itemscope
    line_number: int = 0


class _SemanticHTMLParser(HTMLParser):
    """Internal parser for semantic element extraction."""

    SEMANTIC_TAGS = {
        'article': 'content',
        'section': 'grouping',
        'nav': 'navigation',
        'aside': 'complementary',
        'header': 'banner',
        'footer': 'contentinfo',
        'main': 'main_content',
        'figure': 'figure',
        'figcaption': 'caption',
        'details': 'disclosure',
        'summary': 'disclosure_trigger',
        'dialog': 'dialog',
        'time': 'temporal',
        'mark': 'highlight',
        'progress': 'progress',
        'meter': 'measurement',
        'address': 'contact',
        'blockquote': 'quotation',
        'cite': 'citation',
        'abbr': 'abbreviation',
        'data': 'data_value',
        'output': 'computation_result',
        'picture': 'responsive_image',
        'source': 'media_source',
        'template': 'template',
        'slot': 'slot',
    }

    def __init__(self):
        super().__init__()
        self.semantic_elements: List[HTMLSemanticElementInfo] = []
        self.microdata: List[HTMLMicrodataInfo] = []
        self._text_buffer = ""
        self._current_semantic = None

    def handle_starttag(self, tag: str, attrs: list):
        tag_lower = tag.lower()
        attrs_dict = dict(attrs)
        line = self.getpos()[0]

        # Semantic elements
        if tag_lower in self.SEMANTIC_TAGS:
            elem = HTMLSemanticElementInfo(
                tag=tag_lower,
                role=attrs_dict.get('role', ''),
                purpose=self.SEMANTIC_TAGS[tag_lower],
                id=attrs_dict.get('id', ''),
                classes=attrs_dict.get('class', '').split() if attrs_dict.get('class') else [],
                line_number=line,
            )
            # Capture useful attributes
            for key in ('datetime', 'value', 'min', 'max', 'open', 'cite', 'title'):
                if key in attrs_dict:
                    elem.attributes[key] = attrs_dict[key]
            self.semantic_elements.append(elem)
            self._current_semantic = elem
            self._text_buffer = ""

        # Microdata
        if 'itemscope' in attrs_dict or any(a[0] == 'itemscope' for a in attrs):
            item_type = attrs_dict.get('itemtype', '')
            self.microdata.append(HTMLMicrodataInfo(
                schema_type=item_type,
                scope_tag=tag_lower,
                line_number=line,
            ))

        if 'itemprop' in attrs_dict and self.microdata:
            self.microdata[-1].properties.append(attrs_dict['itemprop'])

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if self._current_semantic and self._current_semantic.tag == tag_lower:
            text = self._text_buffer.strip()
            self._current_semantic.text_preview = text[:80] if text else ""
            self._current_semantic = None
            self._text_buffer = ""

    def handle_data(self, data: str):
        if self._current_semantic:
            self._text_buffer += data


class HTMLSemanticExtractor:
    """Extracts semantic HTML5 elements and microdata from HTML content."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract semantic elements and microdata.

        Args:
            content: HTML source code string.
            file_path: Optional file path for context.

        Returns:
            Dict with 'semantic_elements' and 'microdata' lists.
        """
        parser = _SemanticHTMLParser()
        try:
            parser.feed(content)
        except Exception:
            pass

        return {
            'semantic_elements': parser.semantic_elements,
            'microdata': parser.microdata,
        }
