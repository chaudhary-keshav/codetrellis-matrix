"""
HTML Accessibility Extractor for CodeTrellis

Extracts accessibility (a11y) information: ARIA roles, attributes,
alt text, tabindex, lang attributes, and detects common a11y issues.
Supports WAI-ARIA 1.1/1.2 and WCAG 2.0/2.1/2.2 guidelines.

Part of CodeTrellis v4.16 - HTML Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from html.parser import HTMLParser


@dataclass
class HTMLAriaInfo:
    """Information about ARIA attributes on an element."""
    tag: str = ""
    role: str = ""
    aria_attributes: Dict[str, str] = field(default_factory=dict)
    id: str = ""
    line_number: int = 0


@dataclass
class HTMLA11yIssue:
    """Detected accessibility issue."""
    severity: str = "warning"   # error, warning, info
    rule: str = ""              # WCAG rule reference
    message: str = ""
    tag: str = ""
    line_number: int = 0


class _A11yHTMLParser(HTMLParser):
    """Internal parser for accessibility extraction."""

    # Tags that require alt text
    REQUIRES_ALT = {'img', 'area'}
    # Interactive tags that need accessible names
    INTERACTIVE_TAGS = {'button', 'a', 'input', 'select', 'textarea'}
    # Tags that should have explicit lang
    LANDMARK_TAGS = {'header', 'footer', 'nav', 'main', 'aside', 'section', 'article'}

    def __init__(self):
        super().__init__()
        self.aria_elements: List[HTMLAriaInfo] = []
        self.issues: List[HTMLA11yIssue] = []
        self._has_html_lang = False
        self._has_skip_link = False
        self._heading_levels: List[int] = []
        self._img_count = 0
        self._img_with_alt = 0
        self._form_labels: set = set()
        self._form_inputs_needing_label: List[Dict] = []

    def handle_starttag(self, tag: str, attrs: list):
        tag_lower = tag.lower()
        attrs_dict = dict(attrs)
        line = self.getpos()[0]

        # Collect ARIA attributes
        aria_attrs = {}
        for key, val in attrs:
            if key and (key.startswith('aria-') or key == 'role'):
                aria_attrs[key] = val or ''

        if aria_attrs:
            self.aria_elements.append(HTMLAriaInfo(
                tag=tag_lower,
                role=attrs_dict.get('role', ''),
                aria_attributes=aria_attrs,
                id=attrs_dict.get('id', ''),
                line_number=line,
            ))

        # Check html lang attribute
        if tag_lower == 'html':
            if attrs_dict.get('lang') or attrs_dict.get('xml:lang'):
                self._has_html_lang = True
            else:
                self.issues.append(HTMLA11yIssue(
                    severity='error',
                    rule='WCAG-3.1.1',
                    message='Missing lang attribute on <html> element',
                    tag='html',
                    line_number=line,
                ))

        # Check images for alt text
        if tag_lower == 'img':
            self._img_count += 1
            if 'alt' in attrs_dict:
                self._img_with_alt += 1
            else:
                self.issues.append(HTMLA11yIssue(
                    severity='error',
                    rule='WCAG-1.1.1',
                    message=f'Image missing alt attribute (src={attrs_dict.get("src", "?")[:60]})',
                    tag='img',
                    line_number=line,
                ))

        # Check headings for order
        if tag_lower in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            level = int(tag_lower[1])
            if self._heading_levels and level > self._heading_levels[-1] + 1:
                self.issues.append(HTMLA11yIssue(
                    severity='warning',
                    rule='WCAG-1.3.1',
                    message=f'Heading level skip: h{self._heading_levels[-1]} → h{level}',
                    tag=tag_lower,
                    line_number=line,
                ))
            self._heading_levels.append(level)

        # Check form inputs for labels
        if tag_lower == 'label':
            for_attr = attrs_dict.get('for', '')
            if for_attr:
                self._form_labels.add(for_attr)

        if tag_lower in ('input', 'select', 'textarea'):
            input_id = attrs_dict.get('id', '')
            input_type = attrs_dict.get('type', 'text').lower()
            if input_type not in ('hidden', 'submit', 'button', 'reset', 'image'):
                has_label = (
                    input_id in self._form_labels or
                    attrs_dict.get('aria-label') or
                    attrs_dict.get('aria-labelledby') or
                    attrs_dict.get('title')
                )
                if not has_label and input_id:
                    self._form_inputs_needing_label.append({
                        'id': input_id,
                        'type': input_type,
                        'line': line,
                    })

        # Check skip navigation link
        if tag_lower == 'a':
            href = attrs_dict.get('href', '')
            classes = attrs_dict.get('class', '').lower()
            if href.startswith('#') and ('skip' in classes or 'sr-only' in classes):
                self._has_skip_link = True

        # Check tabindex misuse
        tabindex = attrs_dict.get('tabindex', None)
        if tabindex is not None:
            try:
                ti_val = int(tabindex)
                if ti_val > 0:
                    self.issues.append(HTMLA11yIssue(
                        severity='warning',
                        rule='WCAG-2.4.3',
                        message=f'Positive tabindex={ti_val} on <{tag_lower}> disrupts natural tab order',
                        tag=tag_lower,
                        line_number=line,
                    ))
            except (ValueError, TypeError):
                pass

        # Check for autoplaying media
        if tag_lower in ('video', 'audio'):
            if 'autoplay' in attrs_dict or any(a[0] == 'autoplay' for a in attrs):
                self.issues.append(HTMLA11yIssue(
                    severity='warning',
                    rule='WCAG-1.4.2',
                    message=f'Auto-playing <{tag_lower}> may affect users',
                    tag=tag_lower,
                    line_number=line,
                ))

    def finalize(self):
        """Run post-parse checks."""
        # Check unlabeled form inputs
        for inp in self._form_inputs_needing_label:
            if inp['id'] not in self._form_labels:
                self.issues.append(HTMLA11yIssue(
                    severity='error',
                    rule='WCAG-1.3.1',
                    message=f'Input #{inp["id"]} (type={inp["type"]}) has no associated <label>',
                    tag='input',
                    line_number=inp['line'],
                ))


class HTMLAccessibilityExtractor:
    """Extracts accessibility information and detects a11y issues."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract accessibility info from HTML content.

        Args:
            content: HTML source code string.
            file_path: Optional file path for context.

        Returns:
            Dict with 'aria_elements', 'issues', 'stats'.
        """
        parser = _A11yHTMLParser()
        try:
            parser.feed(content)
        except Exception:
            pass
        parser.finalize()

        stats = {
            'total_images': parser._img_count,
            'images_with_alt': parser._img_with_alt,
            'has_html_lang': parser._has_html_lang,
            'has_skip_link': parser._has_skip_link,
            'heading_count': len(parser._heading_levels),
            'aria_elements_count': len(parser.aria_elements),
            'issues_count': len(parser.issues),
            'errors': sum(1 for i in parser.issues if i.severity == 'error'),
            'warnings': sum(1 for i in parser.issues if i.severity == 'warning'),
        }

        return {
            'aria_elements': parser.aria_elements,
            'issues': parser.issues,
            'stats': stats,
        }
