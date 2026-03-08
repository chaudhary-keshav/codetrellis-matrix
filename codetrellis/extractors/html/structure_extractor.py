"""
HTML Structure Extractor for CodeTrellis

Extracts document structure, sections, headings, and landmarks from HTML source code.
Supports HTML 1.0 through HTML Living Standard (HTML5+).

Part of CodeTrellis v4.16 - HTML Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from html.parser import HTMLParser


@dataclass
class HTMLHeadingInfo:
    """Information about an HTML heading element."""
    level: int = 0           # 1-6
    text: str = ""
    id: str = ""
    classes: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class HTMLLandmarkInfo:
    """Information about an HTML5 landmark/sectioning element."""
    tag: str = ""            # header, footer, nav, main, aside, section, article
    role: str = ""           # ARIA role override
    label: str = ""          # aria-label or aria-labelledby
    id: str = ""
    classes: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class HTMLSectionInfo:
    """Information about a structural section in the document."""
    tag: str = ""
    id: str = ""
    classes: List[str] = field(default_factory=list)
    parent_tag: str = ""
    depth: int = 0
    line_number: int = 0


@dataclass
class HTMLDocumentInfo:
    """Complete document structure information."""
    doctype: str = ""                          # HTML version doctype
    html_version: str = ""                     # Detected HTML version
    lang: str = ""                             # Document language
    charset: str = ""                          # Character encoding
    title: str = ""                            # Page title
    headings: List[HTMLHeadingInfo] = field(default_factory=list)
    landmarks: List[HTMLLandmarkInfo] = field(default_factory=list)
    sections: List[HTMLSectionInfo] = field(default_factory=list)
    has_html5_doctype: bool = False
    has_viewport_meta: bool = False
    total_elements: int = 0
    line_count: int = 0


class _StructureHTMLParser(HTMLParser):
    """Internal HTML parser for structure extraction."""

    # HTML5 sectioning/landmark elements
    LANDMARK_TAGS = {'header', 'footer', 'nav', 'main', 'aside', 'section', 'article'}
    SECTION_TAGS = {'div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main', 'form', 'fieldset'}
    HEADING_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}

    def __init__(self):
        super().__init__()
        self.doc = HTMLDocumentInfo()
        self._current_heading = None
        self._heading_text = ""
        self._title_text = ""
        self._in_title = False
        self._tag_stack: List[str] = []
        self._element_count = 0
        self._current_line = 1

    def handle_decl(self, decl: str):
        decl_upper = decl.upper().strip()
        self.doc.doctype = decl
        if decl_upper == 'DOCTYPE HTML':
            self.doc.has_html5_doctype = True
            self.doc.html_version = "HTML5"
        elif 'XHTML 1.0' in decl_upper:
            self.doc.html_version = "XHTML 1.0"
        elif 'XHTML 1.1' in decl_upper:
            self.doc.html_version = "XHTML 1.1"
        elif 'HTML 4.01' in decl_upper:
            if 'STRICT' in decl_upper:
                self.doc.html_version = "HTML 4.01 Strict"
            elif 'FRAMESET' in decl_upper:
                self.doc.html_version = "HTML 4.01 Frameset"
            else:
                self.doc.html_version = "HTML 4.01 Transitional"
        elif 'HTML 3.2' in decl_upper:
            self.doc.html_version = "HTML 3.2"
        elif 'HTML 2.0' in decl_upper:
            self.doc.html_version = "HTML 2.0"
        else:
            self.doc.html_version = "HTML5"  # Modern default

    def handle_starttag(self, tag: str, attrs: list):
        tag_lower = tag.lower()
        self._element_count += 1
        attrs_dict = dict(attrs)
        line = self.getpos()[0]

        self._tag_stack.append(tag_lower)

        # HTML root element
        if tag_lower == 'html':
            self.doc.lang = attrs_dict.get('lang', attrs_dict.get('xml:lang', ''))
            if not self.doc.html_version:
                self.doc.html_version = "HTML5"

        # Meta charset
        elif tag_lower == 'meta':
            charset = attrs_dict.get('charset', '')
            if charset:
                self.doc.charset = charset
            content = attrs_dict.get('content', '')
            http_equiv = attrs_dict.get('http-equiv', '').lower()
            if http_equiv == 'content-type' and 'charset=' in content.lower():
                self.doc.charset = content.split('charset=')[-1].strip().rstrip(';')
            name = attrs_dict.get('name', '').lower()
            if name == 'viewport':
                self.doc.has_viewport_meta = True

        # Title
        elif tag_lower == 'title':
            self._in_title = True
            self._title_text = ""

        # Headings
        elif tag_lower in self.HEADING_TAGS:
            level = int(tag_lower[1])
            self._current_heading = HTMLHeadingInfo(
                level=level,
                id=attrs_dict.get('id', ''),
                classes=attrs_dict.get('class', '').split() if attrs_dict.get('class') else [],
                line_number=line,
            )
            self._heading_text = ""

        # Landmarks
        if tag_lower in self.LANDMARK_TAGS:
            self.doc.landmarks.append(HTMLLandmarkInfo(
                tag=tag_lower,
                role=attrs_dict.get('role', ''),
                label=attrs_dict.get('aria-label', attrs_dict.get('aria-labelledby', '')),
                id=attrs_dict.get('id', ''),
                classes=attrs_dict.get('class', '').split() if attrs_dict.get('class') else [],
                line_number=line,
            ))

        # Sections
        if tag_lower in self.SECTION_TAGS:
            parent = self._tag_stack[-2] if len(self._tag_stack) >= 2 else ''
            self.doc.sections.append(HTMLSectionInfo(
                tag=tag_lower,
                id=attrs_dict.get('id', ''),
                classes=attrs_dict.get('class', '').split() if attrs_dict.get('class') else [],
                parent_tag=parent,
                depth=len(self._tag_stack),
                line_number=line,
            ))

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()

        if tag_lower == 'title':
            self._in_title = False
            self.doc.title = self._title_text.strip()

        if tag_lower in self.HEADING_TAGS and self._current_heading:
            self._current_heading.text = self._heading_text.strip()
            self.doc.headings.append(self._current_heading)
            self._current_heading = None

        if self._tag_stack and self._tag_stack[-1] == tag_lower:
            self._tag_stack.pop()

    def handle_data(self, data: str):
        if self._in_title:
            self._title_text += data
        if self._current_heading is not None:
            self._heading_text += data

    def get_result(self) -> HTMLDocumentInfo:
        self.doc.total_elements = self._element_count
        return self.doc


class HTMLStructureExtractor:
    """Extracts HTML document structure, headings, and landmarks."""

    # DOCTYPE patterns for version detection
    DOCTYPE_PATTERNS = {
        'html5': re.compile(r'<!DOCTYPE\s+html\s*>', re.IGNORECASE),
        'html4_strict': re.compile(r'<!DOCTYPE\s+HTML\s+PUBLIC\s+"-//W3C//DTD\s+HTML\s+4\.01//EN"', re.IGNORECASE),
        'html4_transitional': re.compile(r'<!DOCTYPE\s+HTML\s+PUBLIC\s+"-//W3C//DTD\s+HTML\s+4\.01\s+Transitional', re.IGNORECASE),
        'xhtml_strict': re.compile(r'<!DOCTYPE\s+html\s+PUBLIC\s+"-//W3C//DTD\s+XHTML\s+1\.0\s+Strict', re.IGNORECASE),
        'xhtml_transitional': re.compile(r'<!DOCTYPE\s+html\s+PUBLIC\s+"-//W3C//DTD\s+XHTML\s+1\.0\s+Transitional', re.IGNORECASE),
        'xhtml11': re.compile(r'<!DOCTYPE\s+html\s+PUBLIC\s+"-//W3C//DTD\s+XHTML\s+1\.1', re.IGNORECASE),
    }

    def extract(self, content: str, file_path: str = "") -> HTMLDocumentInfo:
        """Extract document structure from HTML content.

        Args:
            content: HTML source code string.
            file_path: Optional file path for context.

        Returns:
            HTMLDocumentInfo with extracted structure.
        """
        parser = _StructureHTMLParser()
        try:
            parser.feed(content)
        except Exception:
            pass  # Best effort parsing for malformed HTML

        result = parser.get_result()
        result.line_count = content.count('\n') + 1
        return result
