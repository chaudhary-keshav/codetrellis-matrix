"""
Bootstrap Plugin/JavaScript Extractor for CodeTrellis

Extracts Bootstrap JavaScript plugin usage and initialization from source code.
Covers Bootstrap v3.x through v5.x JavaScript features:

Bootstrap 3/4 jQuery Plugins:
- $(element).modal(), .tooltip(), .popover(), .carousel()
- $(element).on('show.bs.modal'), .on('hidden.bs.modal')
- $.fn.tooltip.Constructor.Default

Bootstrap 5 Vanilla JS:
- new bootstrap.Modal(element, options)
- bootstrap.Modal.getInstance(element)
- bootstrap.Modal.getOrCreateInstance(element)
- element.addEventListener('show.bs.modal')

Data Attributes:
- data-bs-toggle, data-bs-target, data-bs-dismiss
- data-bs-ride, data-bs-slide, data-bs-theme

Events:
- show.bs.*, shown.bs.*, hide.bs.*, hidden.bs.*
- slide.bs.*, slid.bs.*, change.bs.*

CDN / Package Detection:
- npm: bootstrap, react-bootstrap, reactstrap, @ng-bootstrap/ng-bootstrap
- CDN: cdn.jsdelivr.net/npm/bootstrap, unpkg.com/bootstrap
- File: bootstrap.min.js, bootstrap.bundle.min.js

Part of CodeTrellis v4.40 - Bootstrap Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BootstrapPluginInfo:
    """Information about a Bootstrap JavaScript plugin usage."""
    plugin_name: str = ""
    file: str = ""
    line_number: int = 0
    init_method: str = ""        # constructor, jquery, data-attribute, getInstance
    options: List[str] = field(default_factory=list)
    events_bound: List[str] = field(default_factory=list)


@dataclass
class BootstrapEventInfo:
    """Information about a Bootstrap event listener."""
    event_name: str = ""
    file: str = ""
    line_number: int = 0
    component: str = ""          # modal, tooltip, etc.
    event_type: str = ""         # show, shown, hide, hidden, etc.
    method: str = ""             # addEventListener, on, jquery


@dataclass
class BootstrapCDNInfo:
    """Information about Bootstrap CDN/package inclusion."""
    source: str = ""             # cdn, npm, local
    file: str = ""
    line_number: int = 0
    version: str = ""
    package_name: str = ""       # bootstrap, react-bootstrap, etc.
    includes_js: bool = False
    includes_css: bool = False
    is_bundle: bool = False      # bootstrap.bundle includes Popper


class BootstrapPluginExtractor:
    """
    Extracts Bootstrap JavaScript plugin usage from source code.

    Detects:
    - Bootstrap 5 vanilla JS constructors
    - Bootstrap 3/4 jQuery plugins
    - Data attribute initialization
    - Event listeners for Bootstrap events
    - CDN/npm package inclusion
    """

    PLUGINS = [
        'Alert', 'Button', 'Carousel', 'Collapse', 'Dropdown',
        'Modal', 'Offcanvas', 'Popover', 'ScrollSpy', 'Tab',
        'Toast', 'Tooltip',
    ]

    EVENTS = {
        'modal': ['show', 'shown', 'hide', 'hidden', 'hidePrevented'],
        'toast': ['show', 'shown', 'hide', 'hidden'],
        'alert': ['close', 'closed'],
        'carousel': ['slide', 'slid'],
        'collapse': ['show', 'shown', 'hide', 'hidden'],
        'dropdown': ['show', 'shown', 'hide', 'hidden'],
        'offcanvas': ['show', 'shown', 'hide', 'hidden', 'hidePrevented'],
        'tab': ['show', 'shown', 'hide', 'hidden'],
        'tooltip': ['show', 'shown', 'hide', 'hidden', 'inserted'],
        'popover': ['show', 'shown', 'hide', 'hidden', 'inserted'],
        'scrollspy': ['activate'],
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Bootstrap plugin/JS usage from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'plugins', 'events', 'cdn_includes' keys
        """
        plugins: List[BootstrapPluginInfo] = []
        events: List[BootstrapEventInfo] = []
        cdn_includes: List[BootstrapCDNInfo] = []

        if not content or not content.strip():
            return {
                'plugins': plugins,
                'events': events,
                'cdn_includes': cdn_includes,
            }

        self._extract_v5_constructors(content, file_path, plugins)
        self._extract_jquery_plugins(content, file_path, plugins)
        self._extract_data_attributes(content, file_path, plugins)
        self._extract_events(content, file_path, events)
        self._extract_cdn_includes(content, file_path, cdn_includes)
        self._extract_npm_packages(content, file_path, cdn_includes)

        return {
            'plugins': plugins,
            'events': events,
            'cdn_includes': cdn_includes,
        }

    def _extract_v5_constructors(
        self, content: str, file_path: str,
        plugins: List[BootstrapPluginInfo]
    ):
        """Extract Bootstrap 5 vanilla JS constructor usage."""
        # new bootstrap.PluginName(element, options)
        v5_pattern = re.compile(
            r'new\s+bootstrap\.(Alert|Button|Carousel|Collapse|Dropdown|'
            r'Modal|Offcanvas|Popover|ScrollSpy|Tab|Toast|Tooltip)\s*\(',
            re.MULTILINE
        )
        for m in v5_pattern.finditer(content):
            plugin = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Try to extract options from constructor call
            options = []
            after = content[m.end():m.end() + 500]
            opt_match = re.search(r'\{([^}]*)\}', after)
            if opt_match:
                opt_keys = re.findall(r'(\w+)\s*:', opt_match.group(1))
                options = opt_keys[:10]

            plugins.append(BootstrapPluginInfo(
                plugin_name=plugin.lower(),
                file=file_path,
                line_number=line_num,
                init_method='constructor',
                options=options,
            ))

        # Static methods: bootstrap.Modal.getInstance(), .getOrCreateInstance()
        static_pattern = re.compile(
            r'bootstrap\.(Alert|Button|Carousel|Collapse|Dropdown|'
            r'Modal|Offcanvas|Popover|ScrollSpy|Tab|Toast|Tooltip)'
            r'\.(getInstance|getOrCreateInstance)\s*\(',
            re.MULTILINE
        )
        for m in static_pattern.finditer(content):
            plugin = m.group(1)
            method = m.group(2)
            line_num = content[:m.start()].count('\n') + 1
            plugins.append(BootstrapPluginInfo(
                plugin_name=plugin.lower(),
                file=file_path,
                line_number=line_num,
                init_method=method,
            ))

    def _extract_jquery_plugins(
        self, content: str, file_path: str,
        plugins: List[BootstrapPluginInfo]
    ):
        """Extract Bootstrap jQuery plugin usage (v3/v4 style)."""
        # $(selector).modal('show'), .tooltip({...}), etc.
        jquery_pattern = re.compile(
            r'\$\([^)]+\)\.'
            r'(modal|tooltip|popover|toast|carousel|'
            r'collapse|dropdown|offcanvas|tab|scrollspy|'
            r'alert|button)\s*\(',
            re.MULTILINE
        )
        for m in jquery_pattern.finditer(content):
            plugin = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            plugins.append(BootstrapPluginInfo(
                plugin_name=plugin,
                file=file_path,
                line_number=line_num,
                init_method='jquery',
            ))

    def _extract_data_attributes(
        self, content: str, file_path: str,
        plugins: List[BootstrapPluginInfo]
    ):
        """Extract Bootstrap data-attribute plugin initialization."""
        # data-bs-toggle="modal", data-toggle="tooltip", etc.
        data_toggle_pattern = re.compile(
            r'data-(?:bs-)?toggle\s*=\s*["\'](\w+)["\']',
            re.IGNORECASE
        )
        seen = set()
        for m in data_toggle_pattern.finditer(content):
            plugin = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            key = (plugin, line_num)
            if key in seen:
                continue
            seen.add(key)

            plugins.append(BootstrapPluginInfo(
                plugin_name=plugin,
                file=file_path,
                line_number=line_num,
                init_method='data-attribute',
            ))

    def _extract_events(
        self, content: str, file_path: str,
        events: List[BootstrapEventInfo]
    ):
        """Extract Bootstrap event listeners."""
        # addEventListener('show.bs.modal', ...)
        bs_event_pattern = re.compile(
            r"(?:addEventListener|on)\s*\(\s*['\"](\w+)\.bs\.(\w+)['\"]",
            re.MULTILINE
        )
        for m in bs_event_pattern.finditer(content):
            event_type = m.group(1)
            component = m.group(2)
            line_num = content[:m.start()].count('\n') + 1
            events.append(BootstrapEventInfo(
                event_name=f'{event_type}.bs.{component}',
                file=file_path,
                line_number=line_num,
                component=component,
                event_type=event_type,
                method='addEventListener',
            ))

        # jQuery: .on('show.bs.modal', ...)
        jquery_event_pattern = re.compile(
            r"\.on\s*\(\s*['\"](\w+)\.bs\.(\w+)['\"]",
            re.MULTILINE
        )
        for m in jquery_event_pattern.finditer(content):
            event_type = m.group(1)
            component = m.group(2)
            line_num = content[:m.start()].count('\n') + 1
            events.append(BootstrapEventInfo(
                event_name=f'{event_type}.bs.{component}',
                file=file_path,
                line_number=line_num,
                component=component,
                event_type=event_type,
                method='jquery',
            ))

    def _extract_cdn_includes(
        self, content: str, file_path: str,
        cdn_includes: List[BootstrapCDNInfo]
    ):
        """Extract Bootstrap CDN/local file includes."""
        # CDN patterns
        cdn_pattern = re.compile(
            r'(?:href|src)\s*=\s*["\']([^"\']*'
            r'(?:cdn\.jsdelivr\.net|cdnjs\.cloudflare\.com|'
            r'unpkg\.com|stackpath\.bootstrapcdn\.com|'
            r'maxcdn\.bootstrapcdn\.com)'
            r'[^"\']*bootstrap[^"\']*)["\']',
            re.IGNORECASE
        )
        for m in cdn_pattern.finditer(content):
            url = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Extract version
            ver_match = re.search(r'bootstrap[@/]v?(\d+\.\d+(?:\.\d+)?)', url)
            version = ver_match.group(1) if ver_match else ""

            includes_css = '.css' in url
            includes_js = '.js' in url
            is_bundle = 'bundle' in url

            cdn_includes.append(BootstrapCDNInfo(
                source='cdn',
                file=file_path,
                line_number=line_num,
                version=version,
                package_name='bootstrap',
                includes_js=includes_js,
                includes_css=includes_css,
                is_bundle=is_bundle,
            ))

        # Local file includes
        local_pattern = re.compile(
            r'(?:href|src)\s*=\s*["\']([^"\']*bootstrap[^"\']*'
            r'(?:\.min)?\.(?:css|js))["\']',
            re.IGNORECASE
        )
        for m in local_pattern.finditer(content):
            path = m.group(1)
            # Skip CDN URLs (already captured)
            if any(cdn in path for cdn in ['cdn.', 'cdnjs.', 'unpkg.', 'stackpath.', 'maxcdn.']):
                continue
            line_num = content[:m.start()].count('\n') + 1
            cdn_includes.append(BootstrapCDNInfo(
                source='local',
                file=file_path,
                line_number=line_num,
                package_name='bootstrap',
                includes_css='.css' in path,
                includes_js='.js' in path,
                is_bundle='bundle' in path,
            ))

    def _extract_npm_packages(
        self, content: str, file_path: str,
        cdn_includes: List[BootstrapCDNInfo]
    ):
        """Extract Bootstrap npm package imports."""
        # ES module imports
        npm_import_pattern = re.compile(
            r"(?:import|from)\s+['\"]"
            r"(bootstrap(?:/[^'\"]+)?|"
            r"react-bootstrap(?:/[^'\"]+)?|"
            r"reactstrap(?:/[^'\"]+)?|"
            r"@ng-bootstrap/ng-bootstrap(?:/[^'\"]+)?|"
            r"ng-bootstrap(?:/[^'\"]+)?|"
            r"bootstrap-vue(?:/[^'\"]+)?|"
            r"@popperjs/core(?:/[^'\"]+)?|"
            r"@ng-bootstrap/ng-bootstrap(?:/[^'\"]+)?)"
            r"['\"]",
            re.MULTILINE
        )
        seen_packages = set()
        for m in npm_import_pattern.finditer(content):
            pkg = m.group(1).split('/')[0]
            if pkg.startswith('@'):
                pkg = '/'.join(m.group(1).split('/')[:2])
            if pkg in seen_packages:
                continue
            seen_packages.add(pkg)

            line_num = content[:m.start()].count('\n') + 1

            includes_css = 'css' in m.group(1).lower() or 'dist/css' in m.group(1)
            includes_js = not includes_css

            cdn_includes.append(BootstrapCDNInfo(
                source='npm',
                file=file_path,
                line_number=line_num,
                package_name=pkg,
                includes_js=includes_js,
                includes_css=includes_css,
            ))

        # require() calls
        require_pattern = re.compile(
            r"require\s*\(\s*['\"]"
            r"(bootstrap(?:/[^'\"]+)?|"
            r"react-bootstrap(?:/[^'\"]+)?|"
            r"reactstrap(?:/[^'\"]+)?)"
            r"['\"]\s*\)",
            re.MULTILINE
        )
        for m in require_pattern.finditer(content):
            pkg = m.group(1).split('/')[0]
            if pkg in seen_packages:
                continue
            seen_packages.add(pkg)

            line_num = content[:m.start()].count('\n') + 1
            cdn_includes.append(BootstrapCDNInfo(
                source='npm',
                file=file_path,
                line_number=line_num,
                package_name=pkg,
                includes_js=True,
            ))
