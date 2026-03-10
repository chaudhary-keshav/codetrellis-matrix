"""
EnhancedEchoParser v1.0 - Comprehensive Echo web framework parser.

Supports:
- Echo v3.x (basic routing, context interface)
- Echo v4.x (improved middleware, binder, renderer, route grouping)
- Echo v4.9+ (enhanced routing, JWT middleware updates)

Echo-specific extraction:
- Routes: GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS/Any, route groups
- Middleware: Use(), Pre(), global/group/route-level, built-in middleware
- Binding: Bind(), QueryParam(), PathParam(), FormValue()
- Rendering: JSON/XML/HTML/String/Blob/Stream/File/Attachment
- Validators: custom validators, binding tags
- WebSocket: echo.WebSocket support

Part of CodeTrellis v5.2.0 - Go Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EchoRouteInfo:
    """Information about an Echo route."""
    method: str
    path: str
    handler: str
    group_prefix: str = ""
    full_path: str = ""
    middleware: List[str] = field(default_factory=list)
    name: str = ""  # Named route
    file: str = ""
    line_number: int = 0


@dataclass
class EchoMiddlewareInfo:
    """Information about Echo middleware."""
    name: str
    scope: str = "global"  # global, group, route, pre
    group_path: str = ""
    is_builtin: bool = False
    is_pre: bool = False  # Pre() middleware runs before routing
    file: str = ""
    line_number: int = 0


@dataclass
class EchoRouteGroupInfo:
    """Information about an Echo route group."""
    prefix: str
    variable_name: str = ""
    middleware: List[str] = field(default_factory=list)
    parent_group: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class EchoBindingInfo:
    """Information about request binding."""
    bind_type: str  # Bind, QueryParam, PathParam, FormValue, etc.
    target_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class EchoRenderInfo:
    """Information about response rendering."""
    render_type: str  # JSON, XML, HTML, String, Blob, Stream, File
    status_code: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class EchoParseResult:
    """Complete parse result for an Echo file."""
    file_path: str
    file_type: str = "go"

    routes: List[EchoRouteInfo] = field(default_factory=list)
    route_groups: List[EchoRouteGroupInfo] = field(default_factory=list)
    middleware: List[EchoMiddlewareInfo] = field(default_factory=list)
    bindings: List[EchoBindingInfo] = field(default_factory=list)
    renders: List[EchoRenderInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    echo_version: str = ""
    has_echo_instance: bool = False
    total_routes: int = 0
    total_middleware: int = 0


class EnhancedEchoParser:
    """Enhanced Echo parser for comprehensive Echo web framework extraction."""

    ECHO_IMPORT = re.compile(r'"github\.com/labstack/echo(?:/v\d+)?"')

    # Echo instance: e := echo.New()
    INSTANCE_PATTERN = re.compile(r'(\w+)\s*:?=\s*echo\.New\s*\(\s*\)')

    # Route: e.GET("/path", handler)
    ROUTE_PATTERN = re.compile(
        r'(\w+)\.(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|Any|CONNECT|TRACE|'
        r'Add|Match|RouteNotFound)\s*\(\s*"([^"]*)"\s*(?:,\s*([^)]+))?\)',
    )

    # Group: g := e.Group("/api")
    GROUP_PATTERN = re.compile(
        r'(\w+)\s*:?=\s*(\w+)\.Group\s*\(\s*"([^"]*)"\s*(?:,\s*([^)]+))?\)',
    )

    # Middleware: e.Use(middleware), e.Pre(middleware)
    USE_PATTERN = re.compile(r'(\w+)\.(Use|Pre)\s*\(\s*([^)]+)\s*\)')

    # Binding: c.Bind(&obj)
    BIND_PATTERN = re.compile(
        r'(\w+)\.(Bind|QueryParam|QueryParams|PathParam|PathParamNames|'
        r'FormValue|FormFile|FormParams|MultipartForm|RealIP)\s*\(\s*([^)]*)\)',
    )

    # Render: c.JSON(200, obj)
    RENDER_PATTERN = re.compile(
        r'(\w+)\.(JSON|JSONPretty|JSONBlob|XML|XMLPretty|XMLBlob|HTML|HTMLBlob|'
        r'String|Blob|Stream|File|Attachment|Inline|NoContent|Redirect|Render)\s*\(\s*([^,)]+)',
    )

    # Static files
    STATIC_PATTERN = re.compile(
        r'(\w+)\.(Static|File)\s*\(\s*"([^"]*)"\s*,\s*"([^"]*)"',
    )

    # Echo built-in middleware imports
    ECHO_MW_IMPORT = re.compile(r'"github\.com/labstack/echo(?:/v\d+)?/middleware"')

    # Middleware usage from echo middleware package
    ECHO_BUILTIN_MW = re.compile(
        r'middleware\.(Logger|Recover|CORS|Gzip|Secure|BodyLimit|RateLimiter|'
        r'BasicAuth|JWTWithConfig|JWT|KeyAuth|Static|Proxy|Rewrite|'
        r'RequestID|Timeout|CSRF|BodyDump|Decompress)\s*\(',
    )

    # Named routes: e.GET(...).Name = "name"
    NAMED_ROUTE = re.compile(r'\.Name\s*=\s*"([^"]*)"')

    # Framework ecosystem detection
    FRAMEWORK_PATTERNS = {
        'echo': re.compile(r'"github\.com/labstack/echo(?:/v\d+)?"'),
        'echo-middleware': re.compile(r'"github\.com/labstack/echo(?:/v\d+)?/middleware"'),
        'echo-jwt': re.compile(r'"github\.com/labstack/echo-jwt(?:/v\d+)?"'),
        'echo-swagger': re.compile(r'"github\.com/swaggo/echo-swagger"'),
        'echo-prometheus': re.compile(r'"github\.com/labstack/echo-contrib/prometheus"'),
        'echo-casbin': re.compile(r'"github\.com/labstack/echo-contrib/casbin"'),
        'echo-jaeger': re.compile(r'"github\.com/labstack/echo-contrib/jaegertracing"'),
        'echo-session': re.compile(r'"github\.com/gorilla/sessions|github\.com/labstack/echo-contrib/session"'),
        'echo-validator': re.compile(r'"github\.com/go-playground/validator"'),
        'echo-pprof': re.compile(r'"github\.com/labstack/echo-contrib/pprof"'),
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> EchoParseResult:
        """Parse Go source code for Echo-specific patterns."""
        result = EchoParseResult(file_path=file_path)

        if not self.ECHO_IMPORT.search(content):
            return result

        # Detect Echo instance
        for m in self.INSTANCE_PATTERN.finditer(content):
            result.has_echo_instance = True

        result.detected_frameworks = self._detect_frameworks(content)
        result.echo_version = self._detect_version(content)

        # Build group map
        group_map = {}
        for m in self.GROUP_PATTERN.finditer(content):
            var_name = m.group(1)
            parent_var = m.group(2)
            prefix = m.group(3)
            mw_str = m.group(4) or ""

            parent_prefix = group_map.get(parent_var, "")
            full_prefix = parent_prefix + prefix
            group_map[var_name] = full_prefix

            mw_list = [x.strip() for x in mw_str.split(',') if x.strip()] if mw_str else []
            result.route_groups.append(EchoRouteGroupInfo(
                prefix=prefix, variable_name=var_name,
                middleware=mw_list, parent_group=parent_var,
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract routes
        for m in self.ROUTE_PATTERN.finditer(content):
            var_name = m.group(1)
            method = m.group(2)
            path = m.group(3)
            handler_str = m.group(4) or ""

            handlers = [h.strip() for h in handler_str.split(',') if h.strip()]
            handler = handlers[0] if handlers else ""

            group_prefix = group_map.get(var_name, "")
            full_path = group_prefix + path

            result.routes.append(EchoRouteInfo(
                method=method.upper(),
                path=path, handler=handler,
                group_prefix=group_prefix, full_path=full_path,
                middleware=handlers[1:] if len(handlers) > 1 else [],
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract middleware
        for m in self.USE_PATTERN.finditer(content):
            var_name = m.group(1)
            is_pre = m.group(2) == "Pre"
            mw_str = m.group(3)

            for mw in mw_str.split(','):
                mw = mw.strip()
                if not mw:
                    continue
                scope = "pre" if is_pre else ("group" if var_name in group_map else "global")
                result.middleware.append(EchoMiddlewareInfo(
                    name=mw, scope=scope,
                    group_path=group_map.get(var_name, ""),
                    is_builtin='middleware.' in mw,
                    is_pre=is_pre, file=file_path,
                    line_number=content[:m.start()].count('\n') + 1,
                ))

        # Extract built-in middleware
        for m in self.ECHO_BUILTIN_MW.finditer(content):
            result.middleware.append(EchoMiddlewareInfo(
                name=f"middleware.{m.group(1)}()",
                scope="builtin", is_builtin=True,
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract bindings
        for m in self.BIND_PATTERN.finditer(content):
            result.bindings.append(EchoBindingInfo(
                bind_type=m.group(2), target_type=m.group(3).strip(),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract renders
        for m in self.RENDER_PATTERN.finditer(content):
            result.renders.append(EchoRenderInfo(
                render_type=m.group(2), status_code=m.group(3).strip(),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        result.total_routes = len(result.routes)
        result.total_middleware = len(result.middleware)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_version(self, content: str) -> str:
        if re.search(r'echo/v4', content):
            return "v4.x"
        if re.search(r'echo/v3', content):
            return "v3.x"
        if self.ECHO_IMPORT.search(content):
            return "v3.x+"
        return ""
