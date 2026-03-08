"""
HTML Asset Extractor for CodeTrellis

Extracts script tags, style tags, inline JS/CSS, external resources,
preload/prefetch hints, module scripts, and resource integrity information.

Part of CodeTrellis v4.16 - HTML Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from html.parser import HTMLParser


@dataclass
class HTMLScriptInfo:
    """Information about a script element."""
    src: str = ""                # External source
    script_type: str = ""        # text/javascript, module, application/json, etc.
    is_module: bool = False
    is_async: bool = False
    is_defer: bool = False
    is_inline: bool = False
    is_nomodule: bool = False
    crossorigin: str = ""
    integrity: str = ""
    nonce: str = ""
    inline_size: int = 0         # Size of inline script in chars
    inline_preview: str = ""     # First 100 chars of inline script
    line_number: int = 0


@dataclass
class HTMLStyleInfo:
    """Information about a style element or CSS link."""
    href: str = ""               # External stylesheet href
    media: str = ""
    is_inline: bool = False
    inline_size: int = 0
    scoped: bool = False         # HTML5 scoped attribute (deprecated but detectable)
    nonce: str = ""
    crossorigin: str = ""
    integrity: str = ""
    css_variables: List[str] = field(default_factory=list)
    css_imports: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class HTMLPreloadInfo:
    """Information about resource hints (preload, prefetch, preconnect)."""
    hint_type: str = ""          # preload, prefetch, preconnect, dns-prefetch, modulepreload
    href: str = ""
    as_type: str = ""            # script, style, font, image, etc.
    crossorigin: str = ""
    media: str = ""
    line_number: int = 0


class _AssetHTMLParser(HTMLParser):
    """Internal parser for script/style/resource extraction."""

    def __init__(self):
        super().__init__()
        self.scripts: List[HTMLScriptInfo] = []
        self.styles: List[HTMLStyleInfo] = []
        self.preloads: List[HTMLPreloadInfo] = []
        self._in_script = False
        self._in_style = False
        self._current_script: Optional[HTMLScriptInfo] = None
        self._current_style: Optional[HTMLStyleInfo] = None
        self._text_buffer = ""

    def handle_starttag(self, tag: str, attrs: list):
        tag_lower = tag.lower()
        attrs_dict = dict(attrs)
        line = self.getpos()[0]

        if tag_lower == 'script':
            script = HTMLScriptInfo(
                src=attrs_dict.get('src', ''),
                script_type=attrs_dict.get('type', ''),
                is_module=attrs_dict.get('type', '').lower() == 'module',
                is_async='async' in attrs_dict or any(a[0] == 'async' for a in attrs),
                is_defer='defer' in attrs_dict or any(a[0] == 'defer' for a in attrs),
                is_nomodule='nomodule' in attrs_dict or any(a[0] == 'nomodule' for a in attrs),
                crossorigin=attrs_dict.get('crossorigin', ''),
                integrity=attrs_dict.get('integrity', ''),
                nonce=attrs_dict.get('nonce', ''),
                is_inline=not attrs_dict.get('src', ''),
                line_number=line,
            )
            self._current_script = script
            if script.is_inline:
                self._in_script = True
                self._text_buffer = ""
            self.scripts.append(script)

        elif tag_lower == 'style':
            style = HTMLStyleInfo(
                media=attrs_dict.get('media', ''),
                is_inline=True,
                scoped='scoped' in attrs_dict or any(a[0] == 'scoped' for a in attrs),
                nonce=attrs_dict.get('nonce', ''),
                line_number=line,
            )
            self._current_style = style
            self._in_style = True
            self._text_buffer = ""
            self.styles.append(style)

        elif tag_lower == 'link':
            rel = attrs_dict.get('rel', '').lower()
            href = attrs_dict.get('href', '')

            # Stylesheet
            if 'stylesheet' in rel:
                self.styles.append(HTMLStyleInfo(
                    href=href,
                    media=attrs_dict.get('media', ''),
                    is_inline=False,
                    crossorigin=attrs_dict.get('crossorigin', ''),
                    integrity=attrs_dict.get('integrity', ''),
                    line_number=line,
                ))

            # Resource hints
            if rel in ('preload', 'prefetch', 'preconnect', 'dns-prefetch', 'modulepreload'):
                self.preloads.append(HTMLPreloadInfo(
                    hint_type=rel,
                    href=href,
                    as_type=attrs_dict.get('as', ''),
                    crossorigin=attrs_dict.get('crossorigin', ''),
                    media=attrs_dict.get('media', ''),
                    line_number=line,
                ))

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower == 'script' and self._in_script:
            self._in_script = False
            if self._current_script:
                self._current_script.inline_size = len(self._text_buffer)
                self._current_script.inline_preview = self._text_buffer.strip()[:100]
            self._current_script = None
        elif tag_lower == 'style' and self._in_style:
            self._in_style = False
            if self._current_style:
                self._current_style.inline_size = len(self._text_buffer)
                # Extract CSS custom properties (variables)
                css_vars = re.findall(r'--[\w-]+', self._text_buffer)
                self._current_style.css_variables = list(set(css_vars))
                # Extract @import URLs
                imports = re.findall(r'@import\s+(?:url\()?\s*["\']?([^"\';\s)]+)', self._text_buffer)
                self._current_style.css_imports = imports
            self._current_style = None

    def handle_data(self, data: str):
        if self._in_script or self._in_style:
            self._text_buffer += data


class HTMLAssetExtractor:
    """Extracts script, style, and resource hint information from HTML."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract asset information from HTML content.

        Args:
            content: HTML source code string.
            file_path: Optional file path for context.

        Returns:
            Dict with 'scripts', 'styles', 'preloads' lists.
        """
        parser = _AssetHTMLParser()
        try:
            parser.feed(content)
        except Exception:
            pass

        return {
            'scripts': parser.scripts,
            'styles': parser.styles,
            'preloads': parser.preloads,
        }
