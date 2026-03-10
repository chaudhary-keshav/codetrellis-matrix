"""
EnhancedSinatraParser v1.0 - Comprehensive Sinatra framework parser.

Runs as a supplementary layer on top of the Ruby parser, extracting
Sinatra-specific semantics.

Supports:
- Sinatra 1.x (classic DSL, basic routing, ERB/Haml templates)
- Sinatra 2.x (Rack 2 support, mustermann routing, streaming)
- Sinatra 3.x (Rack 3 support, pattern matching routes)
- Sinatra 4.x (Ruby 3.0+ only, enhanced streaming, modern Rack)

Sinatra-specific extraction:
- Routes: GET/POST/PUT/PATCH/DELETE/OPTIONS/HEAD, named params, splat, regex
- Filters: before/after filters with optional route patterns
- Helpers: helper methods, extensions, registered hooks
- Templates: ERB, Haml, Slim, Liquid, Markdown, inline templates
- Settings: set/enable/disable, configuration blocks, environments
- Middleware: use declarations
- Error handlers: error/not_found/halt
- Streaming: stream/EventSource
- Extensions: register/helpers

Framework detection (20+ Sinatra ecosystem patterns):
- Core: sinatra, sinatra/base, sinatra/namespace
- Extensions: sinatra-contrib, sinatra-flash, sinatra-param
- Auth: sinatra-auth, warden, rack-protection
- Templates: sinatra-partial, sinatra-assetpack
- API: sinatra-cross_origin, sinatra-respond_to
- Testing: rack-test

Part of CodeTrellis v5.2.0 - Ruby Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SinatraRouteInfo:
    """Information about a Sinatra route."""
    method: str
    path: str
    has_named_params: bool = False
    has_splat: bool = False
    has_regex: bool = False
    conditions: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SinatraFilterInfo:
    """Information about a Sinatra filter."""
    filter_type: str  # before, after
    route_pattern: str = ""  # Optional route-specific filter
    file: str = ""
    line_number: int = 0


@dataclass
class SinatraHelperInfo:
    """Information about a Sinatra helper."""
    name: str
    module_name: str = ""
    is_extension: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class SinatraTemplateInfo:
    """Information about template usage."""
    engine: str  # erb, haml, slim, liquid, markdown
    name: str = ""
    is_inline: bool = False
    layout: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SinatraSettingInfo:
    """Information about Sinatra settings."""
    name: str
    value: str = ""
    setting_type: str = "set"  # set, enable, disable, configure
    environment: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SinatraMiddlewareInfo:
    """Information about Sinatra middleware."""
    name: str
    args: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SinatraErrorHandlerInfo:
    """Information about error handlers."""
    error_type: str  # error, not_found, halt
    status_code: str = ""
    exception_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SinatraParseResult:
    """Complete parse result for a Sinatra file."""
    file_path: str
    file_type: str = "ruby"

    # Routes
    routes: List[SinatraRouteInfo] = field(default_factory=list)

    # Filters
    filters: List[SinatraFilterInfo] = field(default_factory=list)

    # Helpers
    helpers: List[SinatraHelperInfo] = field(default_factory=list)

    # Templates
    templates: List[SinatraTemplateInfo] = field(default_factory=list)

    # Settings
    settings: List[SinatraSettingInfo] = field(default_factory=list)

    # Middleware
    middleware: List[SinatraMiddlewareInfo] = field(default_factory=list)

    # Error handlers
    error_handlers: List[SinatraErrorHandlerInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    sinatra_version: str = ""
    is_modular: bool = False  # Classic vs modular (< Sinatra::Base)
    is_classic: bool = False
    has_namespace: bool = False
    total_routes: int = 0
    total_filters: int = 0


class EnhancedSinatraParser:
    """
    Enhanced Sinatra parser for comprehensive Sinatra web framework extraction.

    Runs AFTER the Ruby parser when Sinatra framework is detected.
    """

    # Sinatra detection
    SINATRA_REQUIRE = re.compile(
        r"require\s+['\"]sinatra(?:/base)?['\"]|"
        r"class\s+\w+\s*<\s*Sinatra::(?:Base|Application)"
    )

    # Route patterns
    ROUTE_PATTERN = re.compile(
        r"^\s*(get|post|put|patch|delete|options|head|link|unlink)\s+"
        r"(?:['\"]([^'\"]+)['\"]|(/[^\s]+))",
        re.MULTILINE,
    )

    # Filter patterns
    FILTER_PATTERN = re.compile(
        r"^\s*(before|after)\s*(?:['\"]([^'\"]+)['\"])?",
        re.MULTILINE,
    )

    # Helper patterns
    HELPERS_BLOCK = re.compile(
        r"^\s*helpers\s+(?:(\w[\w:]*)|do)",
        re.MULTILINE,
    )
    HELPER_METHOD = re.compile(
        r"^\s*def\s+(\w+)",
        re.MULTILINE,
    )

    # Template patterns
    TEMPLATE_RENDER = re.compile(
        r"\b(erb|haml|slim|liquid|markdown|rdoc|builder|nokogiri|"
        r"coffee|sass|scss|less)\s+:(\w+)(?:\s*,\s*(.+))?",
    )
    INLINE_TEMPLATE = re.compile(
        r"^__END__$",
        re.MULTILINE,
    )

    # Settings patterns
    SET_PATTERN = re.compile(
        r"^\s*set\s+:(\w+)\s*,\s*(.+)",
        re.MULTILINE,
    )
    ENABLE_PATTERN = re.compile(
        r"^\s*enable\s+:(.+)",
        re.MULTILINE,
    )
    DISABLE_PATTERN = re.compile(
        r"^\s*disable\s+:(.+)",
        re.MULTILINE,
    )
    CONFIGURE_PATTERN = re.compile(
        r"^\s*configure\s+(?::(\w+)\s*)?do",
        re.MULTILINE,
    )

    # Middleware patterns
    USE_PATTERN = re.compile(
        r"^\s*use\s+(\w[\w:]+)(?:\s*,\s*(.+))?$",
        re.MULTILINE,
    )

    # Error handler patterns
    ERROR_PATTERN = re.compile(
        r"^\s*error\s+(?:(\d+)|(\w[\w:]+))\s+do",
        re.MULTILINE,
    )
    NOT_FOUND_PATTERN = re.compile(
        r"^\s*not_found\s+do",
        re.MULTILINE,
    )

    # Extension patterns
    REGISTER_PATTERN = re.compile(
        r"^\s*register\s+(\w[\w:]+)",
        re.MULTILINE,
    )

    # Namespace patterns (sinatra-contrib)
    NAMESPACE_PATTERN = re.compile(
        r"^\s*namespace\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Modular app detection
    MODULAR_CLASS = re.compile(
        r"class\s+(\w+)\s*<\s*Sinatra::Base",
    )

    # Framework detection
    FRAMEWORK_PATTERNS = {
        'sinatra': re.compile(r"require\s+['\"]sinatra|Sinatra::"),
        'sinatra-contrib': re.compile(r"require\s+['\"]sinatra/contrib|sinatra-contrib"),
        'sinatra-namespace': re.compile(r"register\s+Sinatra::Namespace|sinatra/namespace"),
        'sinatra-flash': re.compile(r"sinatra-flash|sinatra/flash"),
        'sinatra-param': re.compile(r"sinatra-param"),
        'sinatra-cross_origin': re.compile(r"sinatra-cross_origin|cross_origin"),
        'sinatra-respond_to': re.compile(r"sinatra-respond_to|respond_to"),
        'sinatra-partial': re.compile(r"sinatra-partial|partial\b"),
        'sinatra-streaming': re.compile(r"sinatra/streaming|stream\s+do"),
        'rack-protection': re.compile(r"rack-protection|Rack::Protection"),
        'rack-test': re.compile(r"rack/test|Rack::Test"),
        'warden': re.compile(r"gem\s+['\"]warden|Warden"),
        'tilt': re.compile(r"gem\s+['\"]tilt|Tilt"),
        'puma': re.compile(r"gem\s+['\"]puma"),
        'thin': re.compile(r"gem\s+['\"]thin"),
        'shotgun': re.compile(r"gem\s+['\"]shotgun"),
        'rerun': re.compile(r"gem\s+['\"]rerun"),
        'sequel': re.compile(r"gem\s+['\"]sequel|Sequel\."),
        'activerecord': re.compile(r"sinatra-activerecord|ActiveRecord"),
        'mongoid': re.compile(r"gem\s+['\"]mongoid|Mongoid"),
    }

    def __init__(self):
        """Initialize the Sinatra parser."""
        pass

    def parse(self, content: str, file_path: str = "") -> SinatraParseResult:
        """Parse Ruby source code for Sinatra-specific patterns."""
        result = SinatraParseResult(file_path=file_path)

        # Check if this file uses Sinatra
        if not self.SINATRA_REQUIRE.search(content):
            return result

        # Detect classic vs modular
        modular = self.MODULAR_CLASS.search(content)
        result.is_modular = bool(modular)
        result.is_classic = not result.is_modular

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version
        result.sinatra_version = self._detect_version(content)

        # Namespace detection
        result.has_namespace = bool(self.NAMESPACE_PATTERN.search(content))

        # Extract routes
        self._extract_routes(content, file_path, result)

        # Extract filters
        self._extract_filters(content, file_path, result)

        # Extract helpers
        self._extract_helpers(content, file_path, result)

        # Extract templates
        self._extract_templates(content, file_path, result)

        # Extract settings
        self._extract_settings(content, file_path, result)

        # Extract middleware
        self._extract_middleware(content, file_path, result)

        # Extract error handlers
        self._extract_error_handlers(content, file_path, result)

        # Totals
        result.total_routes = len(result.routes)
        result.total_filters = len(result.filters)

        return result

    def _extract_routes(self, content: str, file_path: str, result: SinatraParseResult):
        """Extract Sinatra route definitions."""
        for m in self.ROUTE_PATTERN.finditer(content):
            method = m.group(1).upper()
            path = m.group(2) or m.group(3) or ""
            result.routes.append(SinatraRouteInfo(
                method=method,
                path=path,
                has_named_params=bool(re.search(r":\w+", path)),
                has_splat="*" in path,
                has_regex=path.startswith("/") and "(" in path,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_filters(self, content: str, file_path: str, result: SinatraParseResult):
        """Extract Sinatra before/after filters."""
        for m in self.FILTER_PATTERN.finditer(content):
            result.filters.append(SinatraFilterInfo(
                filter_type=m.group(1),
                route_pattern=m.group(2) or "",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_helpers(self, content: str, file_path: str, result: SinatraParseResult):
        """Extract Sinatra helper definitions."""
        for m in self.HELPERS_BLOCK.finditer(content):
            module_name = m.group(1) or ""
            result.helpers.append(SinatraHelperInfo(
                name=module_name or "anonymous_helpers",
                module_name=module_name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extensions via register
        for m in self.REGISTER_PATTERN.finditer(content):
            result.helpers.append(SinatraHelperInfo(
                name=m.group(1),
                is_extension=True,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_templates(self, content: str, file_path: str, result: SinatraParseResult):
        """Extract template rendering calls."""
        for m in self.TEMPLATE_RENDER.finditer(content):
            engine = m.group(1)
            name = m.group(2)
            opts = m.group(3) or ""
            layout = ""
            layout_match = re.search(r"layout:\s*:?(\w+)", opts)
            if layout_match:
                layout = layout_match.group(1)

            result.templates.append(SinatraTemplateInfo(
                engine=engine,
                name=name,
                layout=layout,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Inline templates
        if self.INLINE_TEMPLATE.search(content):
            result.templates.append(SinatraTemplateInfo(
                engine="inline",
                name="__END__",
                is_inline=True,
                file=file_path,
            ))

    def _extract_settings(self, content: str, file_path: str, result: SinatraParseResult):
        """Extract Sinatra settings."""
        for m in self.SET_PATTERN.finditer(content):
            result.settings.append(SinatraSettingInfo(
                name=m.group(1),
                value=m.group(2).strip()[:100],
                setting_type="set",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.ENABLE_PATTERN.finditer(content):
            for name in m.group(1).split(','):
                name = name.strip().lstrip(':')
                if name:
                    result.settings.append(SinatraSettingInfo(
                        name=name,
                        value="true",
                        setting_type="enable",
                        file=file_path,
                        line_number=content[:m.start()].count('\n') + 1,
                    ))

        for m in self.DISABLE_PATTERN.finditer(content):
            for name in m.group(1).split(','):
                name = name.strip().lstrip(':')
                if name:
                    result.settings.append(SinatraSettingInfo(
                        name=name,
                        value="false",
                        setting_type="disable",
                        file=file_path,
                        line_number=content[:m.start()].count('\n') + 1,
                    ))

        for m in self.CONFIGURE_PATTERN.finditer(content):
            result.settings.append(SinatraSettingInfo(
                name="configure",
                environment=m.group(1) or "all",
                setting_type="configure",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_middleware(self, content: str, file_path: str, result: SinatraParseResult):
        """Extract Sinatra middleware declarations."""
        for m in self.USE_PATTERN.finditer(content):
            result.middleware.append(SinatraMiddlewareInfo(
                name=m.group(1),
                args=m.group(2) or "",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_error_handlers(self, content: str, file_path: str, result: SinatraParseResult):
        """Extract error handlers."""
        for m in self.ERROR_PATTERN.finditer(content):
            result.error_handlers.append(SinatraErrorHandlerInfo(
                error_type="error",
                status_code=m.group(1) or "",
                exception_class=m.group(2) or "",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.NOT_FOUND_PATTERN.finditer(content):
            result.error_handlers.append(SinatraErrorHandlerInfo(
                error_type="not_found",
                status_code="404",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Sinatra ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect Sinatra version from usage patterns."""
        if re.search(r"sinatra.*['\"]~>\s*4|rack\s*3", content):
            return "4.x"
        if re.search(r"sinatra.*['\"]~>\s*3", content):
            return "3.x"
        if re.search(r"Sinatra::IndifferentHash|mustermann", content):
            return "2.x"
        if re.search(r"require\s+['\"]sinatra|Sinatra::", content):
            return "1.x+"
        return ""
