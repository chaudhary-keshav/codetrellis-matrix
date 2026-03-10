"""
EnhancedChiParser v1.0 - Comprehensive Chi router parser.

Supports:
- Chi v1.x-v4.x (basic routing, middleware stack)
- Chi v5.x (improved route patterns, middleware, chi.URLParam)

Chi-specific extraction:
- Routes: Get/Post/Put/Delete/Patch/Head/Options/Connect/Trace
- Route patterns: Route(), Mount(), Handle(), Method()
- Middleware: Use(), With(), inline middleware chain
- Sub-routers: Mount(), subrouter patterns
- URL parameters: URLParam(), URLParamFromCtx()
- Route groups: Group(), Route(), Mount()

Part of CodeTrellis v5.2.0 - Go Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChiRouteInfo:
    method: str
    path: str
    handler: str
    group_prefix: str = ""
    full_path: str = ""
    middleware: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class ChiMiddlewareInfo:
    name: str
    scope: str = "global"  # global, group, route, inline
    group_path: str = ""
    is_builtin: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class ChiMountInfo:
    path: str
    handler: str
    is_subrouter: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class ChiRouteGroupInfo:
    prefix: str
    variable_name: str = ""
    middleware: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class ChiParseResult:
    file_path: str
    file_type: str = "go"

    routes: List[ChiRouteInfo] = field(default_factory=list)
    route_groups: List[ChiRouteGroupInfo] = field(default_factory=list)
    mounts: List[ChiMountInfo] = field(default_factory=list)
    middleware: List[ChiMiddlewareInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    chi_version: str = ""
    has_chi_router: bool = False
    total_routes: int = 0
    total_middleware: int = 0


class EnhancedChiParser:
    """Enhanced Chi parser for comprehensive Chi router extraction."""

    CHI_IMPORT = re.compile(r'"github\.com/go-chi/chi(?:/v\d+)?"')

    # Chi router creation: r := chi.NewRouter()
    ROUTER_PATTERN = re.compile(r'(\w+)\s*:?=\s*chi\.NewRouter\s*\(\s*\)')

    # Standard route: r.Get("/path", handler)
    ROUTE_PATTERN = re.compile(
        r'(\w+)\.(Get|Post|Put|Delete|Patch|Head|Options|Connect|Trace)\s*\(\s*"([^"]*)"\s*,\s*([^)]+)\)',
    )

    # Route with method string: r.Method("GET", "/path", handler)
    METHOD_PATTERN = re.compile(
        r'(\w+)\.Method\s*\(\s*"([^"]+)"\s*,\s*"([^"]*)"\s*,\s*([^)]+)\)',
    )

    # Handle pattern: r.Handle("/path", handler)
    HANDLE_PATTERN = re.compile(
        r'(\w+)\.Handle\s*\(\s*"([^"]*)"\s*,\s*([^)]+)\)',
    )

    # HandleFunc pattern: r.HandleFunc("/path", handler)
    HANDLEFUNC_PATTERN = re.compile(
        r'(\w+)\.HandleFunc\s*\(\s*"([^"]*)"\s*,\s*([^)]+)\)',
    )

    # Group/Route: r.Group(func(r chi.Router) { ... })
    GROUP_FUNC_PATTERN = re.compile(
        r'(\w+)\.Group\s*\(\s*func\s*\(\s*(\w+)\s+chi\.Router\s*\)',
    )

    # Route pattern: r.Route("/path", func(r chi.Router) { ... })
    ROUTE_FUNC_PATTERN = re.compile(
        r'(\w+)\.Route\s*\(\s*"([^"]*)"\s*,\s*func\s*\(\s*(\w+)\s+chi\.Router\s*\)',
    )

    # Mount: r.Mount("/path", handler)
    MOUNT_PATTERN = re.compile(
        r'(\w+)\.Mount\s*\(\s*"([^"]*)"\s*,\s*([^)]+)\)',
    )

    # Middleware: r.Use(middleware)
    USE_PATTERN = re.compile(r'(\w+)\.Use\s*\(\s*([^)]+)\s*\)')

    # With (inline middleware): r.With(middleware).Get("/path", handler)
    WITH_PATTERN = re.compile(
        r'(\w+)\.With\s*\(\s*([^)]+)\s*\)\.(Get|Post|Put|Delete|Patch|Head|Options)\s*\(\s*"([^"]*)"\s*,\s*([^)]+)\)',
    )

    # Chi middleware imports
    CHI_MW_IMPORT = re.compile(r'"github\.com/go-chi/chi(?:/v\d+)?/middleware"')

    # Chi built-in middleware usage
    CHI_BUILTIN_MW = re.compile(
        r'middleware\.(Logger|Recoverer|RequestID|RealIP|Compress|Heartbeat|'
        r'Throttle|Timeout|AllowContentType|CleanPath|StripSlashes|'
        r'RedirectSlashes|URLFormat|NoCache|SetHeader|GetHead|'
        r'ContentCharset|RouteHeaders|BasicAuth)\b',
    )

    # URLParam usage
    URL_PARAM_PATTERN = re.compile(
        r'chi\.URLParam\s*\(\s*\w+\s*,\s*"([^"]+)"\s*\)',
    )

    FRAMEWORK_PATTERNS = {
        'chi': re.compile(r'"github\.com/go-chi/chi(?:/v\d+)?"'),
        'chi-middleware': re.compile(r'"github\.com/go-chi/chi(?:/v\d+)?/middleware"'),
        'chi-render': re.compile(r'"github\.com/go-chi/render"'),
        'chi-cors': re.compile(r'"github\.com/go-chi/cors"'),
        'chi-jwtauth': re.compile(r'"github\.com/go-chi/jwtauth(?:/v\d+)?"'),
        'chi-docgen': re.compile(r'"github\.com/go-chi/docgen"'),
        'chi-httprate': re.compile(r'"github\.com/go-chi/httprate"'),
        'chi-httplog': re.compile(r'"github\.com/go-chi/httplog"'),
        'chi-stampede': re.compile(r'"github\.com/go-chi/stampede"'),
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> ChiParseResult:
        result = ChiParseResult(file_path=file_path)

        if not self.CHI_IMPORT.search(content):
            return result

        for m in self.ROUTER_PATTERN.finditer(content):
            result.has_chi_router = True

        result.detected_frameworks = self._detect_frameworks(content)
        result.chi_version = self._detect_version(content)

        # Build group/route prefix map from Route() calls
        route_groups = {}  # inner_var -> prefix
        for m in self.ROUTE_FUNC_PATTERN.finditer(content):
            parent_var = m.group(1)
            prefix = m.group(2)
            inner_var = m.group(3)
            route_groups[inner_var] = prefix
            result.route_groups.append(ChiRouteGroupInfo(
                prefix=prefix, variable_name=inner_var,
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Standard routes
        for m in self.ROUTE_PATTERN.finditer(content):
            var_name = m.group(1)
            method = m.group(2)
            path = m.group(3)
            handler = m.group(4).strip()

            group_prefix = route_groups.get(var_name, "")
            full_path = group_prefix + path

            result.routes.append(ChiRouteInfo(
                method=method.upper(), path=path, handler=handler,
                group_prefix=group_prefix, full_path=full_path,
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Method() routes
        for m in self.METHOD_PATTERN.finditer(content):
            result.routes.append(ChiRouteInfo(
                method=m.group(2).upper(), path=m.group(3),
                handler=m.group(4).strip(),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Handle/HandleFunc routes
        for pattern in [self.HANDLE_PATTERN, self.HANDLEFUNC_PATTERN]:
            for m in pattern.finditer(content):
                var_name = m.group(1)
                path = m.group(2)
                handler = m.group(3).strip()
                group_prefix = route_groups.get(var_name, "")

                result.routes.append(ChiRouteInfo(
                    method="ANY", path=path, handler=handler,
                    group_prefix=group_prefix,
                    full_path=group_prefix + path,
                    file=file_path, line_number=content[:m.start()].count('\n') + 1,
                ))

        # With (inline middleware) routes
        for m in self.WITH_PATTERN.finditer(content):
            mw_str = m.group(2)
            method = m.group(3)
            path = m.group(4)
            handler = m.group(5).strip()

            mw_list = [x.strip() for x in mw_str.split(',') if x.strip()]
            result.routes.append(ChiRouteInfo(
                method=method.upper(), path=path, handler=handler,
                middleware=mw_list,
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Mount points
        for m in self.MOUNT_PATTERN.finditer(content):
            result.mounts.append(ChiMountInfo(
                path=m.group(2), handler=m.group(3).strip(),
                is_subrouter='Router' in m.group(3) or 'router' in m.group(3).lower(),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Middleware
        for m in self.USE_PATTERN.finditer(content):
            var_name = m.group(1)
            mw_str = m.group(2)

            for mw in mw_str.split(','):
                mw = mw.strip()
                if not mw:
                    continue
                scope = "group" if var_name in route_groups else "global"
                result.middleware.append(ChiMiddlewareInfo(
                    name=mw, scope=scope,
                    group_path=route_groups.get(var_name, ""),
                    is_builtin='middleware.' in mw,
                    file=file_path, line_number=content[:m.start()].count('\n') + 1,
                ))

        # Built-in middleware
        for m in self.CHI_BUILTIN_MW.finditer(content):
            result.middleware.append(ChiMiddlewareInfo(
                name=f"middleware.{m.group(1)}",
                scope="builtin", is_builtin=True,
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
        if re.search(r'chi/v5', content):
            return "v5.x"
        if re.search(r'chi/v4', content):
            return "v4.x"
        if re.search(r'chi/v3', content):
            return "v3.x"
        if self.CHI_IMPORT.search(content):
            return "v1.x+"
        return ""
