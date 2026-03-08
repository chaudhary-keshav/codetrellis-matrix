"""
HTMX Attribute Extractor for CodeTrellis

Extracts HTMX attribute usage from HTML source code:
- Core request attributes: hx-get, hx-post, hx-put, hx-patch, hx-delete
- Swap attributes: hx-swap, hx-target, hx-select, hx-select-oob, hx-swap-oob
- Navigation: hx-boost, hx-push-url, hx-replace-url, hx-history, hx-history-elt
- Request modifiers: hx-vals, hx-headers, hx-include, hx-params, hx-encoding
- UX attributes: hx-indicator, hx-confirm, hx-prompt, hx-disable, hx-disabled-elt
- Inheritance: hx-disinherit, hx-inherit
- Other: hx-preserve, hx-sync, hx-validate, hx-on, hx-ext
- data-hx-* prefix (HTMX v1.x compatibility)

Supports:
- HTMX v1.x (data-hx-* prefix, older attribute names)
- HTMX v2.x (hx-on:* syntax, hx-disabled-elt, hx-inherit)

Part of CodeTrellis v4.67 - HTMX Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HtmxAttributeInfo:
    """Information about an HTMX attribute usage."""
    attribute_name: str  # hx-get, hx-post, hx-swap, etc.
    file: str = ""
    line_number: int = 0
    attribute_value: str = ""  # The value of the attribute
    attribute_category: str = ""  # request, swap, navigation, modifier, ux, inheritance, extension
    is_data_prefix: bool = False  # data-hx-* prefix (v1 compat)
    version_hint: str = ""  # v1, v2


# Attribute categories for classification
ATTRIBUTE_CATEGORIES = {
    # Core request methods
    'hx-get': 'request',
    'hx-post': 'request',
    'hx-put': 'request',
    'hx-patch': 'request',
    'hx-delete': 'request',
    # Swap / targeting
    'hx-swap': 'swap',
    'hx-target': 'swap',
    'hx-select': 'swap',
    'hx-select-oob': 'swap',
    'hx-swap-oob': 'swap',
    # Navigation
    'hx-boost': 'navigation',
    'hx-push-url': 'navigation',
    'hx-replace-url': 'navigation',
    'hx-history': 'navigation',
    'hx-history-elt': 'navigation',
    # Request modifiers
    'hx-vals': 'modifier',
    'hx-headers': 'modifier',
    'hx-include': 'modifier',
    'hx-params': 'modifier',
    'hx-encoding': 'modifier',
    # UX
    'hx-indicator': 'ux',
    'hx-confirm': 'ux',
    'hx-prompt': 'ux',
    'hx-disable': 'ux',
    'hx-disabled-elt': 'ux',
    # Trigger
    'hx-trigger': 'trigger',
    # Inheritance
    'hx-disinherit': 'inheritance',
    'hx-inherit': 'inheritance',
    # Preservation
    'hx-preserve': 'other',
    'hx-sync': 'other',
    'hx-validate': 'other',
    # Extension
    'hx-ext': 'extension',
    # Event handler (v2)
    'hx-on': 'event',
}

# Attributes introduced or changed in v2
V2_ATTRIBUTES = {'hx-disabled-elt', 'hx-inherit'}


class HtmxAttributeExtractor:
    """
    Extracts HTMX attribute usages from HTML source code.

    Detects all hx-* and data-hx-* attributes in HTML elements,
    classifies them by category, and detects version hints.
    """

    # Pattern for hx-* attributes in HTML
    # Matches: hx-get="/api/data" hx-swap="innerHTML" etc.
    HX_ATTR_PATTERN = re.compile(
        r"""(?:^|\s)"""
        r"""((?:data-)?hx-(?:[a-zA-Z][a-zA-Z0-9\-]*))"""
        r"""(?:\s*=\s*(?:"([^"]*)"|'([^']*)'))?""",
        re.MULTILINE
    )

    # Pattern for hx-on:event="handler" (v2 syntax)
    HX_ON_EVENT_PATTERN = re.compile(
        r"""(?:^|\s)"""
        r"""((?:data-)?hx-on:([a-zA-Z][a-zA-Z0-9:.\-]*))"""
        r"""(?:\s*=\s*(?:"([^"]*)"|'([^']*)'))?""",
        re.MULTILINE
    )

    # Pattern for hx-on::event="handler" (htmx: prefixed events via hx-on)
    HX_ON_HTMX_EVENT_PATTERN = re.compile(
        r"""(?:^|\s)"""
        r"""((?:data-)?hx-on::([a-zA-Z][a-zA-Z0-9:.\-]*))"""
        r"""(?:\s*=\s*(?:"([^"]*)"|'([^']*)'))?""",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> List[HtmxAttributeInfo]:
        """Extract all HTMX attribute usages from source code.

        Args:
            content: Source code content (HTML).
            file_path: Path to the source file.

        Returns:
            List of HtmxAttributeInfo objects.
        """
        if not content or not content.strip():
            return []

        results: List[HtmxAttributeInfo] = []
        lines = content.split('\n')

        # Track line numbers for attributes
        for line_idx, line in enumerate(lines, start=1):
            # Standard hx-* attributes
            for match in self.HX_ATTR_PATTERN.finditer(line):
                attr_name = match.group(1)
                attr_value = match.group(2) if match.group(2) is not None else (match.group(3) or "")

                is_data_prefix = attr_name.startswith('data-')
                canonical = attr_name.replace('data-', '', 1) if is_data_prefix else attr_name

                # Skip hx-on: pattern (handled below)
                if canonical.startswith('hx-on:'):
                    continue

                category = ATTRIBUTE_CATEGORIES.get(canonical, 'other')
                version_hint = ""
                if is_data_prefix:
                    version_hint = "v1"
                elif canonical in V2_ATTRIBUTES:
                    version_hint = "v2"

                results.append(HtmxAttributeInfo(
                    attribute_name=canonical,
                    file=file_path,
                    line_number=line_idx,
                    attribute_value=attr_value,
                    attribute_category=category,
                    is_data_prefix=is_data_prefix,
                    version_hint=version_hint,
                ))

            # hx-on:event="handler" (v2 inline event syntax)
            for match in self.HX_ON_EVENT_PATTERN.finditer(line):
                full_attr = match.group(1)
                event_name = match.group(2)
                handler = match.group(3) if match.group(3) is not None else (match.group(4) or "")

                is_data_prefix = full_attr.startswith('data-')

                results.append(HtmxAttributeInfo(
                    attribute_name=f"hx-on:{event_name}",
                    file=file_path,
                    line_number=line_idx,
                    attribute_value=handler,
                    attribute_category='event',
                    is_data_prefix=is_data_prefix,
                    version_hint='v2',
                ))

            # hx-on::htmx-event="handler" (htmx: namespaced events)
            for match in self.HX_ON_HTMX_EVENT_PATTERN.finditer(line):
                full_attr = match.group(1)
                event_name = match.group(2)
                handler = match.group(3) if match.group(3) is not None else (match.group(4) or "")

                is_data_prefix = full_attr.startswith('data-')

                results.append(HtmxAttributeInfo(
                    attribute_name=f"hx-on::{event_name}",
                    file=file_path,
                    line_number=line_idx,
                    attribute_value=handler,
                    attribute_category='event',
                    is_data_prefix=is_data_prefix,
                    version_hint='v2',
                ))

        return results
