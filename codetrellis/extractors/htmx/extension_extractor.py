"""
HTMX Extension Extractor for CodeTrellis

Extracts HTMX extension usage from HTML and JavaScript source code:
- hx-ext attribute registrations (comma-separated extension names)
- Official extensions: sse, ws, json-enc, class-tools, debug,
  loading-states, head-support, preload, response-targets, multi-swap,
  path-deps, remove-me, restored, alpine-morph, client-side-templates,
  event-header, include-vals, method-override, morphdom-swap,
  disable-element, idiomorph
- Custom extensions: htmx.defineExtension() definitions
- Extension script imports (CDN or npm)
- SSE extension: sse-connect, sse-swap attributes
- WebSocket extension: ws-connect, ws-send attributes

Supports:
- HTMX v1.x extensions (built-in extensions)
- HTMX v2.x extensions (external extensions, htmx-ext/* packages)

Part of CodeTrellis v4.67 - HTMX Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HtmxExtensionInfo:
    """Information about an HTMX extension usage."""
    name: str  # Extension name (e.g., "sse", "json-enc")
    file: str = ""
    line_number: int = 0
    extension_type: str = ""  # official, custom, third_party
    is_official: bool = False
    registration_type: str = ""  # hx-ext, defineExtension, import
    has_sse_connect: bool = False
    has_ws_connect: bool = False
    sse_url: str = ""
    ws_url: str = ""
    config: str = ""  # Extension configuration if detectable


# Official HTMX extensions
OFFICIAL_EXTENSIONS = {
    # Core extensions (ship with htmx)
    'ajax-header', 'class-tools', 'client-side-templates', 'debug',
    'event-header', 'head-support', 'include-vals', 'json-enc',
    'loading-states', 'method-override', 'morphdom-swap', 'multi-swap',
    'path-deps', 'preload', 'remove-me', 'response-targets',
    'restored', 'sse', 'ws',
    # v2 new/moved extensions
    'alpine-morph', 'disable-element', 'idiomorph',
}

# Extension aliases
EXTENSION_ALIASES = {
    'server-sent-events': 'sse',
    'web-sockets': 'ws',
}


class HtmxExtensionExtractor:
    """
    Extracts HTMX extension usages from source code.

    Detects hx-ext attribute registrations, custom extension definitions
    via htmx.defineExtension(), and extension-specific attributes
    like sse-connect, ws-connect.
    """

    # hx-ext attribute pattern
    HX_EXT_PATTERN = re.compile(
        r"""(?:^|\s)(?:data-)?hx-ext\s*=\s*(?:"([^"]*)"|'([^']*)')""",
        re.MULTILINE
    )

    # htmx.defineExtension() pattern
    DEFINE_EXT_PATTERN = re.compile(
        r"""htmx\.defineExtension\(\s*['"]([^'"]+)['"]""",
        re.MULTILINE
    )

    # SSE extension attributes
    SSE_CONNECT_PATTERN = re.compile(
        r"""(?:^|\s)(?:data-)?sse-connect\s*=\s*(?:"([^"]*)"|'([^']*)')""",
        re.MULTILINE
    )

    SSE_SWAP_PATTERN = re.compile(
        r"""(?:^|\s)(?:data-)?sse-swap\s*=\s*(?:"([^"]*)"|'([^']*)')""",
        re.MULTILINE
    )

    # WebSocket extension attributes
    WS_CONNECT_PATTERN = re.compile(
        r"""(?:^|\s)(?:data-)?ws-connect\s*=\s*(?:"([^"]*)"|'([^']*)')""",
        re.MULTILINE
    )

    WS_SEND_PATTERN = re.compile(
        r"""(?:^|\s)(?:data-)?ws-send""",
        re.MULTILINE
    )

    # Extension import patterns
    EXT_IMPORT_PATTERN = re.compile(
        r"""(?:from\s+['"]htmx-ext/([^'"]+)['"]|"""
        r"""<script[^>]*src\s*=\s*["'][^"']*htmx[^"']*ext[^"']*["'][^>]*>)""",
        re.MULTILINE | re.IGNORECASE
    )

    def extract(self, content: str, file_path: str = "") -> List[HtmxExtensionInfo]:
        """Extract all HTMX extension usages from source code.

        Args:
            content: Source code content (HTML or JS/TS).
            file_path: Path to the source file.

        Returns:
            List of HtmxExtensionInfo objects.
        """
        if not content or not content.strip():
            return []

        results: List[HtmxExtensionInfo] = []
        seen_extensions: set = set()
        lines = content.split('\n')

        # Extract hx-ext registrations
        for line_idx, line in enumerate(lines, start=1):
            for match in self.HX_EXT_PATTERN.finditer(line):
                ext_value = match.group(1) if match.group(1) is not None else (match.group(2) or "")
                ext_names = [n.strip() for n in ext_value.split(',') if n.strip()]

                for ext_name in ext_names:
                    # Handle "ignore:" prefix (unregistration)
                    actual_name = ext_name
                    if ext_name.startswith('ignore:'):
                        actual_name = ext_name[7:]

                    canonical = EXTENSION_ALIASES.get(actual_name, actual_name)
                    is_official = canonical in OFFICIAL_EXTENSIONS

                    if canonical not in seen_extensions:
                        seen_extensions.add(canonical)
                        results.append(HtmxExtensionInfo(
                            name=canonical,
                            file=file_path,
                            line_number=line_idx,
                            extension_type='official' if is_official else 'third_party',
                            is_official=is_official,
                            registration_type='hx-ext',
                        ))

        # Extract htmx.defineExtension() definitions
        for line_idx, line in enumerate(lines, start=1):
            for match in self.DEFINE_EXT_PATTERN.finditer(line):
                ext_name = match.group(1)
                canonical = EXTENSION_ALIASES.get(ext_name, ext_name)

                if canonical not in seen_extensions:
                    seen_extensions.add(canonical)
                    results.append(HtmxExtensionInfo(
                        name=canonical,
                        file=file_path,
                        line_number=line_idx,
                        extension_type='custom',
                        is_official=False,
                        registration_type='defineExtension',
                    ))

        # Detect SSE extension usage (sse-connect, sse-swap)
        for line_idx, line in enumerate(lines, start=1):
            for match in self.SSE_CONNECT_PATTERN.finditer(line):
                sse_url = match.group(1) if match.group(1) is not None else (match.group(2) or "")
                if 'sse' not in seen_extensions:
                    seen_extensions.add('sse')
                    results.append(HtmxExtensionInfo(
                        name='sse',
                        file=file_path,
                        line_number=line_idx,
                        extension_type='official',
                        is_official=True,
                        registration_type='attribute',
                        has_sse_connect=True,
                        sse_url=sse_url,
                    ))
                else:
                    # Update existing SSE entry
                    for r in results:
                        if r.name == 'sse':
                            r.has_sse_connect = True
                            r.sse_url = sse_url
                            break

        # Detect WebSocket extension usage (ws-connect, ws-send)
        for line_idx, line in enumerate(lines, start=1):
            for match in self.WS_CONNECT_PATTERN.finditer(line):
                ws_url = match.group(1) if match.group(1) is not None else (match.group(2) or "")
                if 'ws' not in seen_extensions:
                    seen_extensions.add('ws')
                    results.append(HtmxExtensionInfo(
                        name='ws',
                        file=file_path,
                        line_number=line_idx,
                        extension_type='official',
                        is_official=True,
                        registration_type='attribute',
                        has_ws_connect=True,
                        ws_url=ws_url,
                    ))
                else:
                    for r in results:
                        if r.name == 'ws':
                            r.has_ws_connect = True
                            r.ws_url = ws_url
                            break

        return results
