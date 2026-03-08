"""
HTML Form Extractor for CodeTrellis

Extracts form elements, inputs, validation attributes, and fieldsets
from HTML source code. Covers HTML4 forms through HTML5 advanced
input types and validation.

Part of CodeTrellis v4.16 - HTML Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from html.parser import HTMLParser


@dataclass
class HTMLInputInfo:
    """Information about an HTML input/control element."""
    input_type: str = "text"     # text, email, password, number, date, file, etc.
    name: str = ""
    id: str = ""
    required: bool = False
    pattern: str = ""            # HTML5 pattern attribute
    placeholder: str = ""
    min_val: str = ""
    max_val: str = ""
    step: str = ""
    autocomplete: str = ""
    disabled: bool = False
    readonly: bool = False
    aria_label: str = ""
    data_attributes: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0


@dataclass
class HTMLFieldsetInfo:
    """Information about a fieldset grouping."""
    legend: str = ""
    id: str = ""
    name: str = ""
    disabled: bool = False
    input_count: int = 0
    line_number: int = 0


@dataclass
class HTMLFormInfo:
    """Information about an HTML form."""
    action: str = ""
    method: str = "GET"
    enctype: str = ""
    name: str = ""
    id: str = ""
    classes: List[str] = field(default_factory=list)
    inputs: List[HTMLInputInfo] = field(default_factory=list)
    fieldsets: List[HTMLFieldsetInfo] = field(default_factory=list)
    has_csrf_token: bool = False
    has_file_upload: bool = False
    novalidate: bool = False
    autocomplete: str = ""
    target: str = ""
    line_number: int = 0


class _FormHTMLParser(HTMLParser):
    """Internal parser for form extraction."""

    INPUT_TAGS = {'input', 'select', 'textarea', 'button', 'output', 'datalist'}

    def __init__(self):
        super().__init__()
        self.forms: List[HTMLFormInfo] = []
        self._current_form: Optional[HTMLFormInfo] = None
        self._current_fieldset: Optional[HTMLFieldsetInfo] = None
        self._in_legend = False
        self._legend_text = ""

    def handle_starttag(self, tag: str, attrs: list):
        tag_lower = tag.lower()
        attrs_dict = dict(attrs)
        line = self.getpos()[0]

        if tag_lower == 'form':
            form = HTMLFormInfo(
                action=attrs_dict.get('action', ''),
                method=attrs_dict.get('method', 'GET').upper(),
                enctype=attrs_dict.get('enctype', ''),
                name=attrs_dict.get('name', ''),
                id=attrs_dict.get('id', ''),
                classes=attrs_dict.get('class', '').split() if attrs_dict.get('class') else [],
                novalidate='novalidate' in attrs_dict or any(a[0] == 'novalidate' for a in attrs),
                autocomplete=attrs_dict.get('autocomplete', ''),
                target=attrs_dict.get('target', ''),
                line_number=line,
            )
            self._current_form = form
            self.forms.append(form)

        elif tag_lower == 'fieldset' and self._current_form:
            fs = HTMLFieldsetInfo(
                id=attrs_dict.get('id', ''),
                name=attrs_dict.get('name', ''),
                disabled='disabled' in attrs_dict or any(a[0] == 'disabled' for a in attrs),
                line_number=line,
            )
            self._current_fieldset = fs
            self._current_form.fieldsets.append(fs)

        elif tag_lower == 'legend':
            self._in_legend = True
            self._legend_text = ""

        elif tag_lower in self.INPUT_TAGS and self._current_form:
            input_type = attrs_dict.get('type', 'text').lower() if tag_lower == 'input' else tag_lower
            inp = HTMLInputInfo(
                input_type=input_type,
                name=attrs_dict.get('name', ''),
                id=attrs_dict.get('id', ''),
                required='required' in attrs_dict or any(a[0] == 'required' for a in attrs),
                pattern=attrs_dict.get('pattern', ''),
                placeholder=attrs_dict.get('placeholder', ''),
                min_val=attrs_dict.get('min', ''),
                max_val=attrs_dict.get('max', ''),
                step=attrs_dict.get('step', ''),
                autocomplete=attrs_dict.get('autocomplete', ''),
                disabled='disabled' in attrs_dict or any(a[0] == 'disabled' for a in attrs),
                readonly='readonly' in attrs_dict or any(a[0] == 'readonly' for a in attrs),
                aria_label=attrs_dict.get('aria-label', ''),
                line_number=line,
            )
            # Collect data-* attributes
            for key, val in attrs:
                if key and key.startswith('data-'):
                    inp.data_attributes[key] = val or ''

            self._current_form.inputs.append(inp)

            if self._current_fieldset:
                self._current_fieldset.input_count += 1

            # Track special form features
            if input_type == 'file':
                self._current_form.has_file_upload = True
            if input_type == 'hidden' and ('csrf' in (attrs_dict.get('name', '')).lower() or
                                            '_token' in (attrs_dict.get('name', '')).lower()):
                self._current_form.has_csrf_token = True

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower == 'form':
            self._current_form = None
        elif tag_lower == 'fieldset':
            self._current_fieldset = None
        elif tag_lower == 'legend':
            self._in_legend = False
            if self._current_fieldset:
                self._current_fieldset.legend = self._legend_text.strip()

    def handle_data(self, data: str):
        if self._in_legend:
            self._legend_text += data


class HTMLFormExtractor:
    """Extracts form elements, inputs, and validation from HTML content."""

    def extract(self, content: str, file_path: str = "") -> List[HTMLFormInfo]:
        """Extract all forms from HTML content.

        Args:
            content: HTML source code string.
            file_path: Optional file path for context.

        Returns:
            List of HTMLFormInfo objects.
        """
        parser = _FormHTMLParser()
        try:
            parser.feed(content)
        except Exception:
            pass

        return parser.forms
