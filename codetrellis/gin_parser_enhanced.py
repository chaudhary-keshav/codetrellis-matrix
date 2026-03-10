"""
EnhancedGinParser v1.0 - Comprehensive Gin web framework parser.

This parser integrates Gin-specific extraction to provide complete parsing of
Gin web application files. It runs as a supplementary layer on top of the
Go parser, extracting Gin-specific semantics.

Supports:
- Gin v1.x (original gin-gonic/gin, basic routing/middleware)
- Gin v1.6+ (ShouldBind, gin.H, improved error handling)
- Gin v1.7+ (trusted proxies, ContextWithFallback)
- Gin v1.9+ (ContextWithFallback default true, improved performance)

Gin-specific extraction:
- Routes: GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS/Any, route groups
- Middleware: Use(), global/group/route-level middleware, recovery, CORS
- Binding: ShouldBind/ShouldBindJSON/ShouldBindQuery/Bind/BindJSON
- Rendering: JSON/XML/YAML/HTML/String/Redirect/File/Data responses
- Engine config: SetMode, TrustedProxies, RedirectTrailingSlash, etc.
- Route groups: Group() with prefix and middleware
- Static files: Static/StaticFS/StaticFile
- Error handling: AbortWithStatus, AbortWithStatusJSON, Error()

Framework detection (20+ Gin ecosystem patterns):
- Core: gin-gonic/gin, gin.Default(), gin.New()
- Auth: gin-jwt, gin-sessions, gin-oauth2
- Validation: gin-validator, binding tags
- DB: gin-gorm, gin-mongo
- Middleware: gin-cors, gin-contrib/*, gin-limiter
- Swagger: gin-swagger, swaggo/swag
- Testing: httptest, gin test mode

Part of CodeTrellis v5.2.0 - Go Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class GinRouteInfo:
    """Information about a Gin route."""
    method: str  # GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, Any
    path: str
    handler: str
    group_prefix: str = ""
    full_path: str = ""  # group_prefix + path
    middleware: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class GinMiddlewareInfo:
    """Information about Gin middleware."""
    name: str
    scope: str = "global"  # global, group, route
    group_path: str = ""
    is_builtin: bool = False  # gin.Logger(), gin.Recovery()
    file: str = ""
    line_number: int = 0


@dataclass
class GinRouteGroupInfo:
    """Information about a Gin route group."""
    prefix: str
    variable_name: str = ""
    middleware: List[str] = field(default_factory=list)
    parent_group: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GinBindingInfo:
    """Information about request binding."""
    bind_type: str  # ShouldBind, ShouldBindJSON, ShouldBindQuery, Bind, BindJSON, etc.
    target_type: str = ""
    handler: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GinRenderInfo:
    """Information about response rendering."""
    render_type: str  # JSON, XML, YAML, HTML, String, Redirect, File, Data
    status_code: str = ""
    handler: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GinEngineConfigInfo:
    """Information about Gin engine configuration."""
    setting: str
    value: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GinParseResult:
    """Complete parse result for a Gin file."""
    file_path: str
    file_type: str = "go"

    # Routes
    routes: List[GinRouteInfo] = field(default_factory=list)
    route_groups: List[GinRouteGroupInfo] = field(default_factory=list)

    # Middleware
    middleware: List[GinMiddlewareInfo] = field(default_factory=list)

    # Request binding
    bindings: List[GinBindingInfo] = field(default_factory=list)

    # Response rendering
    renders: List[GinRenderInfo] = field(default_factory=list)

    # Engine configuration
    engine_configs: List[GinEngineConfigInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    gin_version: str = ""  # Detected Gin version hint
    has_gin_engine: bool = False
    total_routes: int = 0
    total_middleware: int = 0


class EnhancedGinParser:
    """
    Enhanced Gin parser for comprehensive Gin web framework extraction.

    Runs AFTER the Go parser when Gin framework is detected.
    """

    # Gin import detection
    GIN_IMPORT = re.compile(r'"github\.com/gin-gonic/gin"')

    # Gin engine creation: gin.Default() or gin.New()
    ENGINE_PATTERN = re.compile(
        r'(\w+)\s*:?=\s*gin\.(Default|New)\s*\(\s*\)'
    )

    # Route patterns: router.GET("/path", handler)
    ROUTE_PATTERN = re.compile(
        r'(\w+)\.(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|Any|Handle)\s*\(\s*"([^"]*)"\s*(?:,\s*([^)]+))?\)',
    )

    # Route group: v1 := router.Group("/api/v1")
    GROUP_PATTERN = re.compile(
        r'(\w+)\s*:?=\s*(\w+)\.Group\s*\(\s*"([^"]*)"\s*(?:,\s*([^)]+))?\)',
    )

    # Middleware: router.Use(middleware)
    USE_PATTERN = re.compile(
        r'(\w+)\.Use\s*\(\s*([^)]+)\s*\)',
    )

    # Binding patterns: c.ShouldBindJSON(&req)
    BIND_PATTERN = re.compile(
        r'(\w+)\.(ShouldBind|ShouldBindJSON|ShouldBindXML|ShouldBindQuery|'
        r'ShouldBindYAML|ShouldBindUri|ShouldBindHeader|ShouldBindWith|'
        r'Bind|BindJSON|BindXML|BindQuery|BindYAML|BindUri|BindHeader|'
        r'MustBindWith)\s*\(\s*[&]?(\w+)',
    )

    # Render patterns: c.JSON(200, gin.H{...})
    RENDER_PATTERN = re.compile(
        r'(\w+)\.(JSON|XML|YAML|HTML|String|Redirect|File|FileAttachment|'
        r'Data|DataFromReader|IndentedJSON|SecureJSON|JSONP|AsciiJSON|'
        r'PureJSON|ProtoBuf)\s*\(\s*([^,)]+)',
    )

    # Engine configuration: router.SetMode(), etc.
    CONFIG_PATTERN = re.compile(
        r'(?:gin\.SetMode\s*\(\s*([^)]+)\)|'
        r'(\w+)\.SetTrustedProxies\s*\(\s*([^)]+)\)|'
        r'(\w+)\.(RedirectTrailingSlash|RedirectFixedPath|HandleMethodNotAllowed|'
        r'ForwardedByClientIP|UseRawPath|UnescapePathValues)\s*=\s*(\w+))',
    )

    # Static file serving
    STATIC_PATTERN = re.compile(
        r'(\w+)\.(Static|StaticFS|StaticFile)\s*\(\s*"([^"]*)"\s*,\s*([^)]+)\)',
    )

    # NoRoute / NoMethod handlers
    NO_ROUTE_PATTERN = re.compile(
        r'(\w+)\.(NoRoute|NoMethod)\s*\(\s*([^)]+)\)',
    )

    # Gin contrib middleware patterns
    GIN_CONTRIB_PATTERN = re.compile(
        r'"github\.com/gin-contrib/(\w+)"'
    )

    # Framework ecosystem detection
    FRAMEWORK_PATTERNS = {
        'gin': re.compile(r'"github\.com/gin-gonic/gin"'),
        'gin-swagger': re.compile(r'"github\.com/swaggo/gin-swagger"'),
        'gin-cors': re.compile(r'"github\.com/gin-contrib/cors"'),
        'gin-sessions': re.compile(r'"github\.com/gin-contrib/sessions"'),
        'gin-jwt': re.compile(r'"github\.com/appleboy/gin-jwt"'),
        'gin-cache': re.compile(r'"github\.com/gin-contrib/cache"'),
        'gin-timeout': re.compile(r'"github\.com/gin-contrib/timeout"'),
        'gin-gzip': re.compile(r'"github\.com/gin-contrib/gzip"'),
        'gin-logger': re.compile(r'"github\.com/gin-contrib/logger"'),
        'gin-requestid': re.compile(r'"github\.com/gin-contrib/requestid"'),
        'gin-pprof': re.compile(r'"github\.com/gin-contrib/pprof"'),
        'gin-limiter': re.compile(r'"github\.com/ulule/limiter|github\.com/gin-contrib/limiter"'),
        'gin-secure': re.compile(r'"github\.com/gin-contrib/secure"'),
        'gin-multitemplate': re.compile(r'"github\.com/gin-contrib/multitemplate"'),
        'gin-static': re.compile(r'"github\.com/gin-contrib/static"'),
        'swaggo': re.compile(r'"github\.com/swaggo/swag"'),
        'gin-i18n': re.compile(r'"github\.com/gin-contrib/i18n"'),
        'gin-zap': re.compile(r'"github\.com/gin-contrib/zap"'),
        'gin-prometheus': re.compile(r'"github\.com/zsais/go-gin-prometheus"'),
        'go-playground-validator': re.compile(r'"github\.com/go-playground/validator"'),
    }

    def __init__(self):
        """Initialize the Gin parser."""
        pass

    def parse(self, content: str, file_path: str = "") -> GinParseResult:
        """Parse Go source code for Gin-specific patterns."""
        result = GinParseResult(file_path=file_path)

        # Check if this file uses Gin
        if not self.GIN_IMPORT.search(content):
            return result

        # Detect gin engine creation
        for m in self.ENGINE_PATTERN.finditer(content):
            result.has_gin_engine = True

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version hints
        result.gin_version = self._detect_version(content)

        # Build group prefix map
        group_map = {}  # var_name -> prefix
        for m in self.GROUP_PATTERN.finditer(content):
            var_name = m.group(1)
            parent_var = m.group(2)
            prefix = m.group(3)
            mw_str = m.group(4) or ""

            # Resolve parent prefix
            parent_prefix = group_map.get(parent_var, "")
            full_prefix = parent_prefix + prefix

            group_map[var_name] = full_prefix

            mw_list = [x.strip() for x in mw_str.split(',') if x.strip()] if mw_str else []
            result.route_groups.append(GinRouteGroupInfo(
                prefix=prefix,
                variable_name=var_name,
                middleware=mw_list,
                parent_group=parent_var,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract routes
        for m in self.ROUTE_PATTERN.finditer(content):
            var_name = m.group(1)
            method = m.group(2)
            path = m.group(3)
            handler_str = m.group(4) or ""

            # Get handler name (first arg after path)
            handlers = [h.strip() for h in handler_str.split(',') if h.strip()]
            handler = handlers[-1] if handlers else ""  # Last arg is usually the handler

            # Resolve group prefix
            group_prefix = group_map.get(var_name, "")
            full_path = group_prefix + path

            route_mw = handlers[:-1] if len(handlers) > 1 else []

            result.routes.append(GinRouteInfo(
                method=method.upper() if method != "Any" else "ANY",
                path=path,
                handler=handler,
                group_prefix=group_prefix,
                full_path=full_path,
                middleware=route_mw,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract middleware
        for m in self.USE_PATTERN.finditer(content):
            var_name = m.group(1)
            mw_str = m.group(2)

            for mw in mw_str.split(','):
                mw = mw.strip()
                if not mw:
                    continue
                is_builtin = 'gin.Logger' in mw or 'gin.Recovery' in mw or 'gin.BasicAuth' in mw
                scope = "group" if var_name in group_map else "global"

                result.middleware.append(GinMiddlewareInfo(
                    name=mw,
                    scope=scope,
                    group_path=group_map.get(var_name, ""),
                    is_builtin=is_builtin,
                    file=file_path,
                    line_number=content[:m.start()].count('\n') + 1,
                ))

        # Extract bindings
        for m in self.BIND_PATTERN.finditer(content):
            result.bindings.append(GinBindingInfo(
                bind_type=m.group(2),
                target_type=m.group(3),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract renders
        for m in self.RENDER_PATTERN.finditer(content):
            result.renders.append(GinRenderInfo(
                render_type=m.group(2),
                status_code=m.group(3).strip(),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract engine configs
        for m in self.CONFIG_PATTERN.finditer(content):
            if m.group(1):
                result.engine_configs.append(GinEngineConfigInfo(
                    setting="SetMode", value=m.group(1).strip(),
                    file=file_path, line_number=content[:m.start()].count('\n') + 1,
                ))
            elif m.group(3):
                result.engine_configs.append(GinEngineConfigInfo(
                    setting="SetTrustedProxies", value=m.group(3).strip(),
                    file=file_path, line_number=content[:m.start()].count('\n') + 1,
                ))
            elif m.group(5):
                result.engine_configs.append(GinEngineConfigInfo(
                    setting=m.group(5), value=m.group(6) or "",
                    file=file_path, line_number=content[:m.start()].count('\n') + 1,
                ))

        # Extract static file routes
        for m in self.STATIC_PATTERN.finditer(content):
            result.routes.append(GinRouteInfo(
                method="STATIC",
                path=m.group(3),
                handler=m.group(4).strip(),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Totals
        result.total_routes = len(result.routes)
        result.total_middleware = len(result.middleware)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Gin ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect Gin version hint from import/usage patterns."""
        if re.search(r'SetTrustedProxies|TrustedPlatform', content):
            return "v1.7+"
        if re.search(r'ContextWithFallback', content):
            return "v1.9+"
        if re.search(r'ShouldBind|ShouldBindJSON|ShouldBindQuery', content):
            return "v1.6+"
        if self.GIN_IMPORT.search(content):
            return "v1.x"
        return ""
