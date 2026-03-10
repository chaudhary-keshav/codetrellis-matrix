"""
EnhancedFiberParser v1.0 - Comprehensive Fiber web framework parser.

Supports:
- Fiber v1.x (basic routing, based on Fasthttp)
- Fiber v2.x (improved middleware, prefork, route groups, app.Config)
- Fiber v3.x (client package, hooks, bind struct, Ctx generic type)

Fiber-specific extraction:
- Routes: Get/Post/Put/Delete/Patch/Head/Options/All, route groups
- Middleware: Use(), global/group/route-level middleware
- Binding: BodyParser, QueryParser, ParamsParser, Bind()
- Rendering: JSON/XML/SendString/SendFile/Download/Render
- App config: fiber.Config{}, Prefork, Views, ErrorHandler
- Static files: Static(), embedded FS

Part of CodeTrellis v5.2.0 - Go Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class FiberRouteInfo:
    method: str
    path: str
    handler: str
    group_prefix: str = ""
    full_path: str = ""
    middleware: List[str] = field(default_factory=list)
    name: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class FiberMiddlewareInfo:
    name: str
    scope: str = "global"
    group_path: str = ""
    is_builtin: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class FiberRouteGroupInfo:
    prefix: str
    variable_name: str = ""
    middleware: List[str] = field(default_factory=list)
    parent_group: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class FiberBindingInfo:
    bind_type: str
    target_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class FiberConfigInfo:
    setting: str
    value: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class FiberParseResult:
    file_path: str
    file_type: str = "go"

    routes: List[FiberRouteInfo] = field(default_factory=list)
    route_groups: List[FiberRouteGroupInfo] = field(default_factory=list)
    middleware: List[FiberMiddlewareInfo] = field(default_factory=list)
    bindings: List[FiberBindingInfo] = field(default_factory=list)
    configs: List[FiberConfigInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    fiber_version: str = ""
    has_fiber_app: bool = False
    total_routes: int = 0
    total_middleware: int = 0


class EnhancedFiberParser:
    """Enhanced Fiber parser for comprehensive Fiber web framework extraction."""

    FIBER_IMPORT = re.compile(r'"github\.com/gofiber/fiber(?:/v\d+)?"')

    # Fiber app creation: app := fiber.New(fiber.Config{...})
    APP_PATTERN = re.compile(r'(\w+)\s*:?=\s*fiber\.New\s*\(')

    # Route: app.Get("/path", handler)
    ROUTE_PATTERN = re.compile(
        r'(\w+)\.(Get|Post|Put|Delete|Patch|Head|Options|All|Trace|Connect)\s*\(\s*"([^"]*)"\s*(?:,\s*([^)]+))?\)',
    )

    # Group: api := app.Group("/api")
    GROUP_PATTERN = re.compile(
        r'(\w+)\s*:?=\s*(\w+)\.Group\s*\(\s*"([^"]*)"\s*(?:,\s*([^)]+))?\)',
    )

    # Middleware: app.Use(middleware)
    USE_PATTERN = re.compile(r'(\w+)\.Use\s*\(\s*([^)]+)\s*\)')

    # Binding: c.BodyParser(&obj), c.QueryParser(&obj), c.ParamsParser(&obj)
    BIND_PATTERN = re.compile(
        r'(\w+)\.(BodyParser|QueryParser|ParamsParser|ReqHeaderParser|'
        r'CookieParser|Bind)\s*\(\s*[&]?(\w+)',
    )

    # Render: c.JSON(obj), c.SendString("text"), c.Render("view", fiber.Map{})
    RENDER_PATTERN = re.compile(
        r'(\w+)\.(JSON|XML|JSONP|SendString|SendFile|Download|Render|'
        r'SendStatus|Status|Redirect|Type|Format|Attachment)\s*\(',
    )

    # Config via fiber.Config{...}
    CONFIG_FIELD_PATTERN = re.compile(
        r'fiber\.Config\s*\{([^}]*)\}', re.DOTALL
    )

    # Static: app.Static("/", "./public")
    STATIC_PATTERN = re.compile(
        r'(\w+)\.Static\s*\(\s*"([^"]*)"\s*,\s*"?([^",)]+)',
    )

    # Route naming: app.Get("/", handler).Name("home")
    ROUTE_NAME_PATTERN = re.compile(r'\.Name\s*\(\s*"([^"]*)"\s*\)')

    # Fiber middleware imports (github.com/gofiber/fiber/v2/middleware/*)
    FIBER_MW_IMPORT = re.compile(r'"github\.com/gofiber/fiber(?:/v\d+)?/middleware/(\w+)"')

    FRAMEWORK_PATTERNS = {
        'fiber': re.compile(r'"github\.com/gofiber/fiber(?:/v\d+)?"'),
        'fiber-jwt': re.compile(r'"github\.com/gofiber/jwt(?:/v\d+)?"'),
        'fiber-websocket': re.compile(r'"github\.com/gofiber/websocket(?:/v\d+)?"'),
        'fiber-template': re.compile(r'"github\.com/gofiber/template"'),
        'fiber-storage': re.compile(r'"github\.com/gofiber/storage"'),
        'fiber-helmet': re.compile(r'"github\.com/gofiber/helmet(?:/v\d+)?"'),
        'fiber-contrib': re.compile(r'"github\.com/gofiber/contrib"'),
        'fiber-swagger': re.compile(r'"github\.com/gofiber/swagger"'),
        'fiber-casbin': re.compile(r'"github\.com/gofiber/contrib/casbin"'),
        'fiber-otelfiber': re.compile(r'"github\.com/gofiber/contrib/otelfiber"'),
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> FiberParseResult:
        result = FiberParseResult(file_path=file_path)

        if not self.FIBER_IMPORT.search(content):
            return result

        for m in self.APP_PATTERN.finditer(content):
            result.has_fiber_app = True

        result.detected_frameworks = self._detect_frameworks(content)
        result.fiber_version = self._detect_version(content)

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
            result.route_groups.append(FiberRouteGroupInfo(
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
            handler = handlers[-1] if handlers else ""

            group_prefix = group_map.get(var_name, "")
            full_path = group_prefix + path

            result.routes.append(FiberRouteInfo(
                method=method.upper(), path=path, handler=handler,
                group_prefix=group_prefix, full_path=full_path,
                middleware=handlers[:-1] if len(handlers) > 1 else [],
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract middleware
        for m in self.USE_PATTERN.finditer(content):
            var_name = m.group(1)
            mw_str = m.group(2)

            for mw in mw_str.split(','):
                mw = mw.strip()
                if not mw:
                    continue
                scope = "group" if var_name in group_map else "global"
                result.middleware.append(FiberMiddlewareInfo(
                    name=mw, scope=scope,
                    group_path=group_map.get(var_name, ""),
                    is_builtin=any(x in mw for x in ['logger.', 'recover.', 'cors.', 'csrf.']),
                    file=file_path, line_number=content[:m.start()].count('\n') + 1,
                ))

        # Extract built-in middleware from imports
        for m in self.FIBER_MW_IMPORT.finditer(content):
            mw_name = m.group(1)
            result.middleware.append(FiberMiddlewareInfo(
                name=f"fiber/middleware/{mw_name}",
                scope="import", is_builtin=True,
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract bindings
        for m in self.BIND_PATTERN.finditer(content):
            result.bindings.append(FiberBindingInfo(
                bind_type=m.group(2), target_type=m.group(3),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract config
        for m in self.CONFIG_FIELD_PATTERN.finditer(content):
            config_block = m.group(1)
            for line in config_block.split('\n'):
                line = line.strip().rstrip(',')
                if ':' in line:
                    parts = line.split(':', 1)
                    result.configs.append(FiberConfigInfo(
                        setting=parts[0].strip(), value=parts[1].strip(),
                        file=file_path, line_number=content[:m.start()].count('\n') + 1,
                    ))

        # Static routes
        for m in self.STATIC_PATTERN.finditer(content):
            result.routes.append(FiberRouteInfo(
                method="STATIC", path=m.group(2), handler=m.group(3).strip(),
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
        if re.search(r'fiber/v3', content):
            return "v3.x"
        if re.search(r'fiber/v2', content):
            return "v2.x"
        if self.FIBER_IMPORT.search(content):
            return "v1.x+"
        return ""
