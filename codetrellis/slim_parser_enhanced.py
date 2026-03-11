"""
Enhanced Slim Framework Parser for CodeTrellis.

v5.3: Full Slim framework support (3.x through 4.x).
Extracts routes, middleware, DI container bindings, PSR-7 request/response,
controllers, error handlers, route groups, CORS configurations,
Twig view rendering, route strategies.

Runs AFTER the base PHP parser when Slim framework is detected.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ===== DATACLASSES =====

@dataclass
class SlimRouteInfo:
    """Information about a Slim route."""
    method: str  # GET, POST, PUT, PATCH, DELETE, OPTIONS, ANY, map
    path: str
    handler: str = ""
    name: str = ""
    middleware: List[str] = field(default_factory=list)
    group: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SlimMiddlewareInfo:
    """Information about Slim middleware."""
    name: str
    class_name: str = ""
    is_global: bool = False
    is_route_level: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class SlimControllerInfo:
    """Information about a Slim controller/action class."""
    name: str
    methods: List[str] = field(default_factory=list)
    is_invokable: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class SlimDIBindingInfo:
    """Information about a DI container binding."""
    name: str
    class_name: str = ""
    is_factory: bool = False
    is_shared: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class SlimErrorHandlerInfo:
    """Information about a Slim error handler."""
    name: str
    exception_type: str = ""
    status_code: int = 0
    file: str = ""
    line_number: int = 0


@dataclass
class SlimRouteGroupInfo:
    """Information about a Slim route group."""
    prefix: str
    middleware: List[str] = field(default_factory=list)
    route_count: int = 0
    file: str = ""
    line_number: int = 0


@dataclass
class SlimConfigInfo:
    """Information about Slim configuration."""
    key: str
    value: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SlimParseResult:
    """Complete parse result for a Slim file."""
    file_path: str
    file_type: str = "php"

    # Routes
    routes: List[SlimRouteInfo] = field(default_factory=list)

    # Middleware
    middleware: List[SlimMiddlewareInfo] = field(default_factory=list)

    # Controllers
    controllers: List[SlimControllerInfo] = field(default_factory=list)

    # DI Container
    di_bindings: List[SlimDIBindingInfo] = field(default_factory=list)

    # Error Handlers
    error_handlers: List[SlimErrorHandlerInfo] = field(default_factory=list)

    # Route Groups
    route_groups: List[SlimRouteGroupInfo] = field(default_factory=list)

    # Configuration
    configs: List[SlimConfigInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    slim_version: str = ""
    has_twig: bool = False
    has_php_di: bool = False
    has_monolog: bool = False
    uses_psr7: bool = False
    uses_psr15: bool = False


# ===== PARSER =====

class EnhancedSlimParser:
    """
    Enhanced parser for Slim framework (3.x through 4.x).
    Extracts routes, middleware, DI containers, controllers,
    error handlers, route groups, configurations.
    """

    # Detection pattern
    SLIM_DETECT = re.compile(
        r"(?:Slim\\App|Slim\\Factory|Slim\\Routing|"
        r"use\s+Slim\\|AppFactory::create|"
        r"\$app->(?:get|post|put|patch|delete|options|any|map|group|add)\s*\(|"
        r"Slim\\Middleware|Slim\\Psr7)",
        re.MULTILINE,
    )

    # Framework ecosystem patterns
    FRAMEWORK_PATTERNS = {
        'slim': re.compile(r'(?:Slim\\App|Slim\\Factory|AppFactory)'),
        'slim4': re.compile(r'(?:Slim\\Factory\\AppFactory|ResponseEmitter|Slim\\Middleware\\ErrorMiddleware)'),
        'slim3': re.compile(r'(?:new\s+\\?Slim\\App|Slim\\Container|\$app\s*=\s*new\s+App)'),
        'php_di': re.compile(r'(?:DI\\ContainerBuilder|PHP-DI)'),
        'twig': re.compile(r'(?:Twig\\|SlimTwig|TwigMiddleware)'),
        'monolog': re.compile(r'(?:Monolog\\|LoggerInterface)'),
        'eloquent': re.compile(r'(?:Illuminate\\Database|Eloquent)'),
        'doctrine': re.compile(r'(?:Doctrine\\ORM|EntityManager)'),
    }

    # Route patterns - Slim 4 / Slim 3
    ROUTE_PATTERN = re.compile(
        r"\$app->(get|post|put|patch|delete|options|any|map)\s*\(\s*"
        r"['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*(?:\[([^\]]*)\]|['\"]?([^'\")\s,;]+)['\"]?(?:::class)?))?",
        re.MULTILINE,
    )
    ROUTE_NAME = re.compile(r"->setName\s*\(\s*['\"]([^'\"]+)['\"]")
    ROUTE_ADD_MIDDLEWARE = re.compile(r"->add\s*\(\s*(?:new\s+)?(\w+)")

    # Route group
    ROUTE_GROUP_PATTERN = re.compile(
        r"\$app->group\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Middleware patterns
    MIDDLEWARE_ADD = re.compile(
        r"\$app->add\s*\(\s*(?:new\s+)?(\w+(?:\\\w+)*)",
    )
    MIDDLEWARE_CLASS = re.compile(
        r"class\s+(\w+(?:Middleware)?)\s+(?:implements\s+MiddlewareInterface|extends\s+\w*Middleware)",
        re.MULTILINE,
    )
    MIDDLEWARE_PROCESS = re.compile(
        r"public\s+function\s+process\s*\(\s*",
    )

    # Controller/Action patterns
    CONTROLLER_CLASS = re.compile(
        r"class\s+(\w+(?:Controller|Action))\s+",
        re.MULTILINE,
    )
    CONTROLLER_INVOKE = re.compile(
        r"public\s+function\s+__invoke\s*\(",
    )
    CONTROLLER_ACTION = re.compile(
        r"public\s+function\s+(\w+)\s*\(",
    )

    # DI Container patterns
    DI_SET = re.compile(
        r"(?:\$container|container)->\s*(?:set|add)\s*\(\s*"
        r"(?:(\w+(?:\\\w+)*)::class|['\"]([^'\"]+)['\"])",
    )
    DI_DEFINITION = re.compile(
        r"['\"]([^'\"]+)['\"]\s*=>\s*(?:function|DI\\factory|DI\\create|DI\\autowire|\\DI\\)",
    )
    CONTAINER_BUILDER = re.compile(
        r"ContainerBuilder|Container\(\[",
    )

    # Error handler patterns
    ERROR_HANDLER = re.compile(
        r"(?:\$errorMiddleware|errorMiddleware)->setErrorHandler\s*\(\s*"
        r"(?:(\w+)::class|['\"]([^'\"]+)['\"]|(\d+))",
    )
    CUSTOM_ERROR = re.compile(
        r"\$app->addErrorMiddleware\s*\(",
    )

    # Settings/Config patterns
    SETTINGS = re.compile(
        r"['\"]([^'\"]+)['\"]\s*=>\s*(?:env\s*\(\s*)?['\"]([^'\"]*)['\"]",
    )

    # Version detection
    VERSION_PATTERNS = [
        (r'Slim\\Factory\\AppFactory|ResponseEmitter|ErrorMiddleware', '4.x'),
        (r'Slim\\App\(|new\s+App\(|\\Slim\\Container', '3.x'),
    ]

    def parse(self, content: str, file_path: str = "") -> SlimParseResult:
        """Parse PHP source code for Slim-specific patterns."""
        result = SlimParseResult(file_path=file_path)

        if not content.strip():
            return result

        # Check if this file uses Slim
        if not self.SLIM_DETECT.search(content):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version
        result.slim_version = self._detect_version(content)

        # Ecosystem detection
        result.has_twig = bool(self.FRAMEWORK_PATTERNS['twig'].search(content))
        result.has_php_di = bool(self.FRAMEWORK_PATTERNS['php_di'].search(content))
        result.has_monolog = bool(self.FRAMEWORK_PATTERNS['monolog'].search(content))
        result.uses_psr7 = bool(re.search(r'Psr\\Http\\Message|ServerRequestInterface|ResponseInterface', content))
        result.uses_psr15 = bool(re.search(r'Psr\\Http\\Server\\MiddlewareInterface|RequestHandlerInterface', content))

        # Extract all entities
        self._extract_routes(content, file_path, result)
        self._extract_middleware(content, file_path, result)
        self._extract_controllers(content, file_path, result)
        self._extract_di_bindings(content, file_path, result)
        self._extract_error_handlers(content, file_path, result)
        self._extract_route_groups(content, file_path, result)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Slim ecosystem frameworks used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """Detect Slim version from code features."""
        for pattern, version in self.VERSION_PATTERNS:
            if re.search(pattern, content):
                return version
        return ""

    def _get_line(self, content: str, pos: int) -> int:
        """Get 1-based line number for a position."""
        return content[:pos].count('\n') + 1

    def _extract_routes(self, content: str, file_path: str, result: SlimParseResult):
        """Extract Slim route definitions."""
        for m in self.ROUTE_PATTERN.finditer(content):
            method = m.group(1).upper()
            path = m.group(2)
            handler = m.group(3) or m.group(4) or ""
            line = self._get_line(content, m.start())

            # Check for route name
            name = ""
            rest = content[m.end():m.end() + 200]
            name_m = self.ROUTE_NAME.search(rest)
            if name_m:
                name = name_m.group(1)

            # Check for route middleware
            middleware = []
            add_m = self.ROUTE_ADD_MIDDLEWARE.search(rest)
            if add_m:
                middleware.append(add_m.group(1).split('\\')[-1])

            route = SlimRouteInfo(
                method=method,
                path=path,
                handler=handler.strip(),
                name=name,
                middleware=middleware,
                file=file_path,
                line_number=line,
            )
            result.routes.append(route)

    def _extract_middleware(self, content: str, file_path: str, result: SlimParseResult):
        """Extract Slim middleware definitions and usage."""
        # Global middleware (added to $app)
        for m in self.MIDDLEWARE_ADD.finditer(content):
            name = m.group(1).split('\\')[-1]
            line = self._get_line(content, m.start())
            mw = SlimMiddlewareInfo(
                name=name,
                class_name=m.group(1),
                is_global=True,
                file=file_path,
                line_number=line,
            )
            result.middleware.append(mw)

        # Middleware class definitions
        if self.MIDDLEWARE_PROCESS.search(content):
            for m in self.MIDDLEWARE_CLASS.finditer(content):
                name = m.group(1)
                line = self._get_line(content, m.start())
                mw = SlimMiddlewareInfo(
                    name=name,
                    class_name=name,
                    file=file_path,
                    line_number=line,
                )
                result.middleware.append(mw)

    def _extract_controllers(self, content: str, file_path: str, result: SlimParseResult):
        """Extract Slim controller/action definitions."""
        for m in self.CONTROLLER_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            is_invokable = bool(self.CONTROLLER_INVOKE.search(content))
            methods = [am.group(1) for am in self.CONTROLLER_ACTION.finditer(content)
                       if am.group(1) != '__construct']

            ctrl = SlimControllerInfo(
                name=name,
                methods=methods[:20],
                is_invokable=is_invokable,
                file=file_path,
                line_number=line,
            )
            result.controllers.append(ctrl)

    def _extract_di_bindings(self, content: str, file_path: str, result: SlimParseResult):
        """Extract DI container bindings."""
        # Container set/add
        for m in self.DI_SET.finditer(content):
            name = (m.group(1) or m.group(2) or "").split('\\')[-1]
            line = self._get_line(content, m.start())
            binding = SlimDIBindingInfo(
                name=name,
                class_name=m.group(1) or m.group(2) or "",
                file=file_path,
                line_number=line,
            )
            result.di_bindings.append(binding)

        # Array-style definitions
        for m in self.DI_DEFINITION.finditer(content):
            name = m.group(1).split('\\')[-1]
            line = self._get_line(content, m.start())
            is_factory = 'factory' in content[m.start():m.end() + 50].lower()
            binding = SlimDIBindingInfo(
                name=name,
                class_name=m.group(1),
                is_factory=is_factory,
                file=file_path,
                line_number=line,
            )
            result.di_bindings.append(binding)

    def _extract_error_handlers(self, content: str, file_path: str, result: SlimParseResult):
        """Extract Slim error handler definitions."""
        for m in self.ERROR_HANDLER.finditer(content):
            exc_type = m.group(1) or m.group(2) or ""
            status = int(m.group(3)) if m.group(3) else 0
            line = self._get_line(content, m.start())
            eh = SlimErrorHandlerInfo(
                name=exc_type or f"HttpStatus{status}",
                exception_type=exc_type,
                status_code=status,
                file=file_path,
                line_number=line,
            )
            result.error_handlers.append(eh)

    def _extract_route_groups(self, content: str, file_path: str, result: SlimParseResult):
        """Extract Slim route group definitions."""
        for m in self.ROUTE_GROUP_PATTERN.finditer(content):
            prefix = m.group(1)
            line = self._get_line(content, m.start())

            # Count routes within potential scope
            group_text = content[m.start():m.start() + 2000]
            route_count = len(re.findall(r'\$(?:group|app)->\s*(?:get|post|put|patch|delete|any)', group_text))

            grp = SlimRouteGroupInfo(
                prefix=prefix,
                route_count=route_count,
                file=file_path,
                line_number=line,
            )
            result.route_groups.append(grp)
