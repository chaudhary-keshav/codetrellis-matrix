"""
HTML Meta & Head Extractor for CodeTrellis

Extracts meta tags, link tags, Open Graph data, Twitter Cards,
JSON-LD structured data, favicons, and other <head> information.

Part of CodeTrellis v4.16 - HTML Language Support
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from html.parser import HTMLParser


@dataclass
class HTMLMetaInfo:
    """Information about a meta tag."""
    name: str = ""           # meta name
    property: str = ""       # meta property (OG, Twitter)
    content: str = ""
    http_equiv: str = ""
    charset: str = ""
    line_number: int = 0


@dataclass
class HTMLLinkInfo:
    """Information about a link tag."""
    rel: str = ""
    href: str = ""
    link_type: str = ""      # stylesheet, icon, preload, manifest, etc.
    media: str = ""
    sizes: str = ""
    crossorigin: str = ""
    integrity: str = ""
    line_number: int = 0


@dataclass
class HTMLOpenGraphInfo:
    """Open Graph protocol metadata."""
    og_type: str = ""
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_url: str = ""
    og_site_name: str = ""
    og_locale: str = ""
    twitter_card: str = ""
    twitter_site: str = ""
    twitter_creator: str = ""
    other_properties: Dict[str, str] = field(default_factory=dict)


@dataclass
class HTMLJsonLdInfo:
    """JSON-LD structured data."""
    schema_type: str = ""
    schema_context: str = ""
    name: str = ""
    description: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    line_number: int = 0


class _MetaHTMLParser(HTMLParser):
    """Internal parser for meta/head extraction."""

    def __init__(self):
        super().__init__()
        self.metas: List[HTMLMetaInfo] = []
        self.links: List[HTMLLinkInfo] = []
        self.og = HTMLOpenGraphInfo()
        self.json_ld: List[HTMLJsonLdInfo] = []
        self._in_script_ld = False
        self._script_ld_text = ""
        self._script_ld_line = 0

    def handle_starttag(self, tag: str, attrs: list):
        tag_lower = tag.lower()
        attrs_dict = dict(attrs)
        line = self.getpos()[0]

        if tag_lower == 'meta':
            meta = HTMLMetaInfo(
                name=attrs_dict.get('name', ''),
                property=attrs_dict.get('property', ''),
                content=attrs_dict.get('content', ''),
                http_equiv=attrs_dict.get('http-equiv', ''),
                charset=attrs_dict.get('charset', ''),
                line_number=line,
            )
            self.metas.append(meta)

            # Open Graph
            prop = attrs_dict.get('property', '').lower()
            content = attrs_dict.get('content', '')
            if prop == 'og:type':
                self.og.og_type = content
            elif prop == 'og:title':
                self.og.og_title = content
            elif prop == 'og:description':
                self.og.og_description = content
            elif prop == 'og:image':
                self.og.og_image = content
            elif prop == 'og:url':
                self.og.og_url = content
            elif prop == 'og:site_name':
                self.og.og_site_name = content
            elif prop == 'og:locale':
                self.og.og_locale = content
            elif prop.startswith('og:'):
                self.og.other_properties[prop] = content

            # Twitter Cards
            name = attrs_dict.get('name', '').lower()
            if name == 'twitter:card':
                self.og.twitter_card = content
            elif name == 'twitter:site':
                self.og.twitter_site = content
            elif name == 'twitter:creator':
                self.og.twitter_creator = content

        elif tag_lower == 'link':
            rel = attrs_dict.get('rel', '')
            link = HTMLLinkInfo(
                rel=rel,
                href=attrs_dict.get('href', ''),
                link_type=self._classify_link(rel),
                media=attrs_dict.get('media', ''),
                sizes=attrs_dict.get('sizes', ''),
                crossorigin=attrs_dict.get('crossorigin', ''),
                integrity=attrs_dict.get('integrity', ''),
                line_number=line,
            )
            self.links.append(link)

        elif tag_lower == 'script':
            script_type = attrs_dict.get('type', '').lower()
            if script_type == 'application/ld+json':
                self._in_script_ld = True
                self._script_ld_text = ""
                self._script_ld_line = line

    def handle_endtag(self, tag: str):
        if tag.lower() == 'script' and self._in_script_ld:
            self._in_script_ld = False
            try:
                data = json.loads(self._script_ld_text)
                ld = HTMLJsonLdInfo(
                    schema_type=data.get('@type', ''),
                    schema_context=data.get('@context', ''),
                    name=data.get('name', ''),
                    description=data.get('description', ''),
                    raw_data=data,
                    line_number=self._script_ld_line,
                )
                self.json_ld.append(ld)
            except (json.JSONDecodeError, TypeError):
                pass

    def handle_data(self, data: str):
        if self._in_script_ld:
            self._script_ld_text += data

    @staticmethod
    def _classify_link(rel: str) -> str:
        rel_lower = rel.lower()
        if 'stylesheet' in rel_lower:
            return 'stylesheet'
        elif 'icon' in rel_lower:
            return 'icon'
        elif 'preload' in rel_lower:
            return 'preload'
        elif 'prefetch' in rel_lower:
            return 'prefetch'
        elif 'preconnect' in rel_lower:
            return 'preconnect'
        elif 'manifest' in rel_lower:
            return 'manifest'
        elif 'canonical' in rel_lower:
            return 'canonical'
        elif 'alternate' in rel_lower:
            return 'alternate'
        elif 'dns-prefetch' in rel_lower:
            return 'dns-prefetch'
        elif 'modulepreload' in rel_lower:
            return 'modulepreload'
        return rel_lower or 'unknown'


class HTMLMetaExtractor:
    """Extracts meta tags, links, Open Graph, Twitter Cards, and JSON-LD from HTML."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract meta/head information from HTML content.

        Args:
            content: HTML source code string.
            file_path: Optional file path for context.

        Returns:
            Dict with 'metas', 'links', 'open_graph', 'json_ld' keys.
        """
        parser = _MetaHTMLParser()
        try:
            parser.feed(content)
        except Exception:
            pass

        return {
            'metas': parser.metas,
            'links': parser.links,
            'open_graph': parser.og,
            'json_ld': parser.json_ld,
        }
