"""
HTMX Request Extractor for CodeTrellis

Extracts HTMX request patterns from HTML source code:
- HTTP method endpoints: hx-get="/url", hx-post="/url", hx-put, hx-patch, hx-delete
- Request data: hx-vals (JSON/JS values), hx-headers (custom headers)
- Request inclusion: hx-include (CSS selectors for additional inputs)
- Request params: hx-params (filtering which params to send)
- Request encoding: hx-encoding="multipart/form-data"
- Endpoint analysis: URL patterns, path parameters, API prefixes
- CSRF: meta tags, hx-headers with X-CSRFToken

Supports:
- HTMX v1.x and v2.x request patterns
- JSON and JavaScript expression hx-vals
- Relative and absolute URL endpoints
- Template engine URL patterns (Django {% url %}, Rails, Jinja2, etc.)

Part of CodeTrellis v4.67 - HTMX Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HtmxRequestInfo:
    """Information about an HTMX request pattern."""
    method: str  # GET, POST, PUT, PATCH, DELETE
    endpoint: str = ""
    file: str = ""
    line_number: int = 0
    has_vals: bool = False
    vals_type: str = ""  # json, js (JavaScript expression)
    vals_content: str = ""
    has_headers: bool = False
    headers_content: str = ""
    has_include: bool = False
    include_selector: str = ""
    has_params: bool = False
    params_value: str = ""  # *, none, not <list>, <list>
    has_encoding: bool = False
    encoding_type: str = ""
    has_confirm: bool = False
    confirm_message: str = ""
    swap_strategy: str = ""  # innerHTML, outerHTML, beforebegin, afterbegin, beforeend, afterend, delete, none
    target_selector: str = ""
    trigger_spec: str = ""


class HtmxRequestExtractor:
    """
    Extracts HTMX request patterns from HTML source code.

    Analyzes hx-get/post/put/patch/delete attributes along with their
    associated request modifiers (hx-vals, hx-headers, hx-include, etc.)
    to build a comprehensive picture of each HTMX request.
    """

    # HTTP method attributes
    METHOD_ATTRS = {
        'hx-get': 'GET',
        'hx-post': 'POST',
        'hx-put': 'PUT',
        'hx-patch': 'PATCH',
        'hx-delete': 'DELETE',
    }

    # Pattern to match an HTML element with hx-get/post/put/patch/delete
    # We capture the entire element to find associated attributes
    ELEMENT_PATTERN = re.compile(
        r"""<([a-zA-Z][a-zA-Z0-9]*)\s+([^>]*?(?:data-)?hx-(?:get|post|put|patch|delete)[^>]*)>""",
        re.MULTILINE | re.DOTALL
    )

    # Individual attribute extraction
    ATTR_PATTERN = re.compile(
        r"""((?:data-)?hx-[a-zA-Z\-:]+)\s*=\s*(?:"([^"]*)"|'([^']*)')""",
        re.MULTILINE
    )

    # hx-vals JSON detection
    VALS_JSON_PATTERN = re.compile(
        r"""^\s*\{.*\}\s*$""",
        re.DOTALL
    )

    # hx-vals JS expression detection
    VALS_JS_PATTERN = re.compile(
        r"""^\s*js:""",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> List[HtmxRequestInfo]:
        """Extract all HTMX request patterns from source code.

        Args:
            content: Source code content (HTML).
            file_path: Path to the source file.

        Returns:
            List of HtmxRequestInfo objects.
        """
        if not content or not content.strip():
            return []

        results: List[HtmxRequestInfo] = []
        lines = content.split('\n')

        # Find elements with request attributes
        for match in self.ELEMENT_PATTERN.finditer(content):
            tag_name = match.group(1)
            attrs_str = match.group(2)

            # Calculate line number
            pos = match.start()
            line_number = content[:pos].count('\n') + 1

            # Extract all hx-* attributes from this element
            attrs: dict = {}
            for attr_match in self.ATTR_PATTERN.finditer(attrs_str):
                attr_name = attr_match.group(1)
                attr_value = attr_match.group(2) if attr_match.group(2) is not None else (attr_match.group(3) or "")
                canonical = attr_name.replace('data-', '', 1) if attr_name.startswith('data-') else attr_name
                attrs[canonical] = attr_value

            # Find the HTTP method
            method = ""
            endpoint = ""
            for attr, http_method in self.METHOD_ATTRS.items():
                if attr in attrs:
                    method = http_method
                    endpoint = attrs[attr]
                    break

            if not method:
                continue

            info = HtmxRequestInfo(
                method=method,
                endpoint=endpoint,
                file=file_path,
                line_number=line_number,
            )

            # hx-vals
            if 'hx-vals' in attrs:
                info.has_vals = True
                val = attrs['hx-vals']
                info.vals_content = val[:200]
                if self.VALS_JS_PATTERN.match(val):
                    info.vals_type = 'js'
                elif self.VALS_JSON_PATTERN.match(val):
                    info.vals_type = 'json'
                else:
                    info.vals_type = 'json'

            # hx-headers
            if 'hx-headers' in attrs:
                info.has_headers = True
                info.headers_content = attrs['hx-headers'][:200]

            # hx-include
            if 'hx-include' in attrs:
                info.has_include = True
                info.include_selector = attrs['hx-include']

            # hx-params
            if 'hx-params' in attrs:
                info.has_params = True
                info.params_value = attrs['hx-params']

            # hx-encoding
            if 'hx-encoding' in attrs:
                info.has_encoding = True
                info.encoding_type = attrs['hx-encoding']

            # hx-confirm
            if 'hx-confirm' in attrs:
                info.has_confirm = True
                info.confirm_message = attrs['hx-confirm'][:200]

            # hx-swap
            if 'hx-swap' in attrs:
                info.swap_strategy = attrs['hx-swap'].split()[0] if attrs['hx-swap'] else ""

            # hx-target
            if 'hx-target' in attrs:
                info.target_selector = attrs['hx-target']

            # hx-trigger
            if 'hx-trigger' in attrs:
                info.trigger_spec = attrs['hx-trigger'][:200]

            results.append(info)

        return results
