"""
EnhancedLitestarParser - Deep extraction for Litestar framework projects.

Extracts:
- Routes (@get, @post, @put, @patch, @delete, @head, @options, route())
- Controllers (class-based route handlers inheriting from Controller)
- Guards (authentication/authorisation guards, guard decorators)
- Dependencies (Provide(), Dependency injection)
- Middleware (AbstractMiddleware, MiddlewareProtocol, DefineMiddleware)
- Listeners (on_startup, on_shutdown, on_app_init)
- WebSocket routes (@websocket, @websocket_listener)
- Exception handlers (ExceptionHandler mapping)
- DTOs (DataTransferObject, DTOConfig, AbstractDTO)
- Plugins (PluginProtocol, InitPluginProtocol)
- OpenAPI configuration (OpenAPIConfig)
- Response types (Response, File, Stream, Redirect, Template)
- Stores (StoreRegistry, MemoryStore, FileStore, RedisStore)
- Channels (ChannelPlugin)
- Template engines (JinjaTemplateEngine, MakoTemplateEngine)
- Testing helpers (create_test_client, TestClient)
- Security (SessionAuth, JWTAuth, JWTCookieAuth)

Supports:
- Starlite 1.x (pre-rename era, import from starlite)
- Litestar 2.x+ (current, import from litestar)

Part of CodeTrellis v4.93 - Python Framework Support.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any


# ═══════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════

@dataclass
class LitestarRouteInfo:
    """Information about a Litestar route."""
    path: str
    handler: str
    methods: List[str] = field(default_factory=list)
    name: Optional[str] = None
    is_async: bool = True
    controller: Optional[str] = None
    guards: List[str] = field(default_factory=list)
    opt: Optional[Dict[str, str]] = None
    media_type: Optional[str] = None
    status_code: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    sync_to_thread: bool = False
    line_number: int = 0


@dataclass
class LitestarControllerInfo:
    """Information about a Litestar Controller."""
    name: str
    path: Optional[str] = None
    guards: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class LitestarGuardInfo:
    """Information about a Litestar guard."""
    name: str
    guard_type: str = "function"  # function, class, AbstractGuard
    is_async: bool = False
    line_number: int = 0


@dataclass
class LitestarDependencyInfo:
    """Information about a Litestar dependency injection."""
    name: str
    provide_type: str = "Provide"  # Provide, Dependency
    is_async: bool = False
    use_cache: bool = False
    sync_to_thread: bool = False
    line_number: int = 0


@dataclass
class LitestarMiddlewareInfo:
    """Information about Litestar middleware."""
    name: str
    middleware_type: str = "class"  # class, DefineMiddleware, function
    line_number: int = 0


@dataclass
class LitestarListenerInfo:
    """Information about a Litestar listener (lifecycle event)."""
    event: str  # on_startup, on_shutdown, on_app_init, before_send, after_exception
    handler: str
    is_async: bool = True
    line_number: int = 0


@dataclass
class LitestarWebSocketInfo:
    """Information about a Litestar WebSocket endpoint."""
    path: str
    handler: str
    is_async: bool = True
    controller: Optional[str] = None
    line_number: int = 0


@dataclass
class LitestarExceptionHandlerInfo:
    """Information about a Litestar exception handler."""
    exception_class: str
    handler: str
    is_async: bool = False
    line_number: int = 0


@dataclass
class LitestarDTOInfo:
    """Information about a Litestar DTO (Data Transfer Object)."""
    name: str
    dto_type: str = "DTOConfig"  # DTOConfig, AbstractDTO, DataclassDTO, MsgspecDTO, PydanticDTO
    model_class: Optional[str] = None
    exclude: List[str] = field(default_factory=list)
    rename_fields: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0


@dataclass
class LitestarPluginInfo:
    """Information about a Litestar plugin."""
    name: str
    plugin_type: str = "class"  # class, InitPluginProtocol, PluginProtocol, SerializationPluginProtocol
    line_number: int = 0


@dataclass
class LitestarStoreInfo:
    """Information about a Litestar store."""
    name: str
    store_type: str = "MemoryStore"  # MemoryStore, FileStore, RedisStore, ValKeyStore
    variable_name: str = ""
    line_number: int = 0


@dataclass
class LitestarSecurityInfo:
    """Information about a Litestar security configuration."""
    name: str
    auth_type: str = "SessionAuth"  # SessionAuth, JWTAuth, JWTCookieAuth, AbstractSecurityConfig
    line_number: int = 0


@dataclass
class LitestarParseResult:
    """Result of parsing Litestar source code."""
    file_path: str = ""
    file_type: str = "module"

    routes: List[LitestarRouteInfo] = field(default_factory=list)
    controllers: List[LitestarControllerInfo] = field(default_factory=list)
    guards: List[LitestarGuardInfo] = field(default_factory=list)
    dependencies: List[LitestarDependencyInfo] = field(default_factory=list)
    middleware: List[LitestarMiddlewareInfo] = field(default_factory=list)
    listeners: List[LitestarListenerInfo] = field(default_factory=list)
    websocket_routes: List[LitestarWebSocketInfo] = field(default_factory=list)
    exception_handlers: List[LitestarExceptionHandlerInfo] = field(default_factory=list)
    dtos: List[LitestarDTOInfo] = field(default_factory=list)
    plugins: List[LitestarPluginInfo] = field(default_factory=list)
    stores: List[LitestarStoreInfo] = field(default_factory=list)
    security: List[LitestarSecurityInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    litestar_version: str = ""

    # Aggregates
    total_routes: int = 0
    total_controllers: int = 0
    total_middleware: int = 0
    total_guards: int = 0


# ═══════════════════════════════════════════════════════════════════
# Parser
# ═══════════════════════════════════════════════════════════════════

class EnhancedLitestarParser:
    """
    Comprehensive Litestar framework parser.

    Extracts routes, controllers, guards, dependencies, middleware,
    listeners, WebSocket routes, DTOs, plugins, stores, security
    and more from Litestar (and legacy Starlite) source code.
    """

    # ── Framework detection patterns ──────────────────────────────
    FRAMEWORK_PATTERNS = {
        'litestar-core': re.compile(r'from\s+litestar\s+import|import\s+litestar\b', re.MULTILINE),
        'starlite-legacy': re.compile(r'from\s+starlite\s+import|import\s+starlite\b', re.MULTILINE),
        'litestar-controller': re.compile(r'from\s+litestar(?:\.controller)?\s+import\s+.*\bController\b', re.MULTILINE),
        'litestar-dto': re.compile(r'from\s+litestar\.dto\s+import|DTOConfig|AbstractDTO|DataclassDTO|MsgspecDTO|PydanticDTO', re.MULTILINE),
        'litestar-openapi': re.compile(r'from\s+litestar\.openapi\s+import|OpenAPIConfig', re.MULTILINE),
        'litestar-testing': re.compile(r'from\s+litestar\.testing\s+import|create_test_client|TestClient', re.MULTILINE),
        'litestar-stores': re.compile(r'from\s+litestar\.stores\s+import|StoreRegistry|MemoryStore|FileStore|RedisStore', re.MULTILINE),
        'litestar-channels': re.compile(r'from\s+litestar\.channels\s+import|ChannelPlugin', re.MULTILINE),
        'litestar-security': re.compile(r'from\s+litestar\.security\s+import|SessionAuth|JWTAuth|JWTCookieAuth', re.MULTILINE),
        'litestar-middleware': re.compile(r'from\s+litestar\.middleware\s+import|AbstractMiddleware|MiddlewareProtocol|DefineMiddleware', re.MULTILINE),
        'litestar-template': re.compile(r'from\s+litestar\.contrib\.(?:jinja2|mako)\s+import|JinjaTemplateEngine|MakoTemplateEngine', re.MULTILINE),
        'litestar-di': re.compile(r'from\s+litestar\.di\s+import|Provide\s*\(', re.MULTILINE),
        'litestar-plugins': re.compile(r'from\s+litestar\.plugins\s+import|PluginProtocol|InitPluginProtocol|SerializationPluginProtocol', re.MULTILINE),
        'litestar-guards': re.compile(r'from\s+litestar\s+import\s+.*\bGuard\b|AbstractGuard', re.MULTILINE),
        'litestar-response': re.compile(r'from\s+litestar\.response\s+import|Response\s*\(|File\s*\(|Stream\s*\(|Redirect\s*\(|Template\s*\(', re.MULTILINE),
        'sqlalchemy-plugin': re.compile(r'from\s+(?:litestar\.contrib\.sqlalchemy|advanced_alchemy)\s+import|SQLAlchemyPlugin|SQLAlchemyInitPlugin', re.MULTILINE),
        'tortoise-plugin': re.compile(r'from\s+litestar\.contrib\.tortoise_orm\s+import|TortoiseORMPlugin', re.MULTILINE),
        'piccolo-plugin': re.compile(r'from\s+litestar\.contrib\.piccolo\s+import|PiccoloORMPlugin', re.MULTILINE),
    }

    # ── Route decorator patterns ──────────────────────────────────

    # @get("/path"), @post("/path"), etc. (standalone decorators)
    HTTP_METHOD_DECORATOR_PATTERN = re.compile(
        r'@(get|post|put|patch|delete|head|options)\s*\(\s*'
        r'(?:["\']([^"\']*)["\'])?'                    # optional path
        r'[^)]*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # @route("/path", http_method=[...])
    ROUTE_DECORATOR_PATTERN = re.compile(
        r'@route\s*\(\s*'
        r'(?:["\']([^"\']*)["\'])?'                    # optional path
        r'[^)]*?http_method\s*=\s*\[([^\]]+)\]'       # http_method=[...]
        r'[^)]*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # @route("/path") without explicit http_method (defaults)
    ROUTE_DECORATOR_SIMPLE_PATTERN = re.compile(
        r'@route\s*\(\s*'
        r'["\']([^"\']*)["\']'                         # path
        r'\s*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # ── Controller patterns ───────────────────────────────────────

    # class MyController(Controller):
    CONTROLLER_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*Controller\s*\)\s*:',
        re.MULTILINE,
    )

    # path = "/api" inside controller
    CONTROLLER_PATH_PATTERN = re.compile(
        r'\s+path\s*=\s*["\']([^"\']+)["\']',
    )

    # guards = [...] inside controller
    CONTROLLER_GUARDS_PATTERN = re.compile(
        r'\s+guards\s*=\s*\[([^\]]+)\]',
    )

    # tags = [...] inside controller
    CONTROLLER_TAGS_PATTERN = re.compile(
        r'\s+tags\s*=\s*\[([^\]]+)\]',
    )

    # dependencies = {...} inside controller
    CONTROLLER_DEPS_PATTERN = re.compile(
        r'\s+dependencies\s*=\s*\{([^}]+)\}',
    )

    # middleware = [...] inside controller
    CONTROLLER_MIDDLEWARE_PATTERN = re.compile(
        r'\s+middleware\s*=\s*\[([^\]]+)\]',
    )

    # ── Guard patterns ────────────────────────────────────────────

    # async def my_guard(connection, _) -> None:
    # def my_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    GUARD_FUNCTION_PATTERN = re.compile(
        r'(async\s+)?def\s+(\w+)\s*\(\s*'
        r'(?:connection|conn)\s*(?::\s*[\w\[\], ]+)?\s*,'
        r'\s*(?:_|handler)\s*(?::\s*[\w\[\], ]+)?\s*\)'
        r'\s*->\s*None\s*:',
        re.MULTILINE,
    )

    # class MyGuard(AbstractGuard):
    GUARD_CLASS_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*AbstractGuard\s*\)\s*:',
        re.MULTILINE,
    )

    # ── Dependency patterns ───────────────────────────────────────

    # Provide(my_dep), Provide(my_dep, use_cache=True), Provide(my_dep, sync_to_thread=True)
    PROVIDE_PATTERN = re.compile(
        r'["\'](\w+)["\']\s*:\s*Provide\s*\(\s*(\w+)'
        r'(?:\s*,\s*use_cache\s*=\s*(True|False))?'
        r'(?:\s*,\s*sync_to_thread\s*=\s*(True|False))?'
        r'\s*\)',
        re.MULTILINE,
    )

    # Dependency() parameter annotation
    DEPENDENCY_ANNOTATION_PATTERN = re.compile(
        r'(\w+)\s*:\s*[\w\[\], ]+\s*=\s*Dependency\s*\(',
        re.MULTILINE,
    )

    # ── Middleware patterns ────────────────────────────────────────

    # class MyMiddleware(AbstractMiddleware):
    MIDDLEWARE_CLASS_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*(AbstractMiddleware|MiddlewareProtocol)\s*\)\s*:',
        re.MULTILINE,
    )

    # DefineMiddleware(MyMiddleware, ...)
    DEFINE_MIDDLEWARE_PATTERN = re.compile(
        r'DefineMiddleware\s*\(\s*(\w+)',
        re.MULTILINE,
    )

    # ── Listener patterns ─────────────────────────────────────────

    # on_startup=[...], on_shutdown=[...], on_app_init=[...],
    # before_send=[...], after_exception=[...]
    LIFECYCLE_PATTERN = re.compile(
        r'(on_startup|on_shutdown|on_app_init|before_send|after_exception)\s*=\s*\[([^\]]+)\]',
        re.MULTILINE,
    )

    # @app.on_startup  / after_exception decorators (Litestar 2.x)
    LISTENER_DECORATOR_PATTERN = re.compile(
        r'@\w+\.(on_startup|on_shutdown|before_send|after_exception)\s*(?:\([^)]*\))?\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # ── WebSocket patterns ────────────────────────────────────────

    # @websocket("/ws") or @websocket_listener("/ws")
    WEBSOCKET_DECORATOR_PATTERN = re.compile(
        r'@(websocket|websocket_listener)\s*\(\s*["\']([^"\']+)["\']\s*[^)]*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # ── Exception handler patterns ────────────────────────────────

    # exception_handlers={ValidationException: validation_handler, ...}
    EXCEPTION_HANDLER_PATTERN = re.compile(
        r'(\w+)\s*:\s*(\w+)',
    )

    # Exception handler block: exception_handlers={...}
    EXCEPTION_HANDLERS_BLOCK_PATTERN = re.compile(
        r'exception_handlers\s*=\s*\{([^}]+)\}',
        re.MULTILINE,
    )

    # ── DTO patterns ──────────────────────────────────────────────

    # class MyDTO(DataclassDTO[MyModel]): or class MyDTO(PydanticDTO[MyModel]):
    DTO_CLASS_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*(DataclassDTO|PydanticDTO|MsgspecDTO|AbstractDTO)\s*'
        r'(?:\[\s*(\w+)\s*\])?\s*\)\s*:',
        re.MULTILINE,
    )

    # dto = DTOConfig(...)
    DTO_CONFIG_PATTERN = re.compile(
        r'(\w+)\s*=\s*DTOConfig\s*\(',
        re.MULTILINE,
    )

    # ── Plugin patterns ───────────────────────────────────────────

    # class MyPlugin(PluginProtocol): or (InitPluginProtocol): or (SerializationPluginProtocol):
    PLUGIN_CLASS_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*(PluginProtocol|InitPluginProtocol|SerializationPluginProtocol'
        r'|CLIPlugin|OpenAPISchemaPlugin)\s*\)\s*:',
        re.MULTILINE,
    )

    # Known plugin instantiations: SQLAlchemyPlugin(...), StructlogPlugin(...), etc.
    PLUGIN_INSTANCE_PATTERN = re.compile(
        r'(\w+(?:Plugin|PluginConfig))\s*\(',
        re.MULTILINE,
    )

    # ── Store patterns ────────────────────────────────────────────

    # MemoryStore(), FileStore(path=...), RedisStore.with_client(...)
    STORE_PATTERN = re.compile(
        r'(\w+)\s*=\s*(MemoryStore|FileStore|RedisStore|ValKeyStore)\s*[\.(]',
        re.MULTILINE,
    )

    # StoreRegistry(default_factory=...)
    STORE_REGISTRY_PATTERN = re.compile(
        r'StoreRegistry\s*\(',
        re.MULTILINE,
    )

    # ── Security patterns ─────────────────────────────────────────

    # SessionAuth[User, ...], JWTAuth[User], JWTCookieAuth[User]
    SECURITY_PATTERN = re.compile(
        r'(\w+)\s*=\s*(SessionAuth|JWTAuth|JWTCookieAuth|AbstractSecurityConfig)\s*'
        r'(?:\[\s*[\w,\s]+\s*\])?\s*\(',
        re.MULTILINE,
    )

    # ── Litestar app instantiation ────────────────────────────────
    LITESTAR_APP_PATTERN = re.compile(
        r'(\w+)\s*=\s*(?:Litestar|Starlite)\s*\(',
        re.MULTILINE,
    )

    # ── Version feature detection ─────────────────────────────────
    LITESTAR_VERSION_FEATURES = {
        # Starlite 1.x era
        'from starlite import': '1.0',
        'import starlite': '1.0',
        'Starlite(': '1.0',
        'StarletteMiddleware': '1.0',
        # Litestar 2.0 transition
        'from litestar import': '2.0',
        'import litestar': '2.0',
        'Litestar(': '2.0',
        'Controller': '1.0',
        '@get(': '1.0',
        '@post(': '1.0',
        '@put(': '1.0',
        '@patch(': '1.0',
        '@delete(': '1.0',
        '@route(': '1.0',
        '@websocket(': '1.0',
        '@websocket_listener(': '2.0',
        'Provide(': '1.0',
        'Dependency(': '2.0',
        'DTOConfig': '2.0',
        'DataclassDTO': '2.0',
        'MsgspecDTO': '2.0',
        'PydanticDTO': '2.0',
        'AbstractDTO': '2.0',
        'DefineMiddleware': '2.0',
        'AbstractMiddleware': '1.0',
        'MiddlewareProtocol': '1.0',
        'AbstractGuard': '1.0',
        'OpenAPIConfig': '1.0',
        'StoreRegistry': '2.0',
        'ChannelPlugin': '2.0',
        'SessionAuth': '1.0',
        'JWTAuth': '1.0',
        'JWTCookieAuth': '1.0',
        'before_send': '2.0',
        'after_exception': '2.0',
        'on_app_init': '2.0',
        'sync_to_thread': '2.0',
        'opt=': '2.0',
        'InitPluginProtocol': '2.0',
        'CLIPlugin': '2.0',
        'Template(': '1.0',
        'JinjaTemplateEngine': '1.0',
        'MakoTemplateEngine': '1.0',
        'SQLAlchemyPlugin': '2.0',
        'SQLAlchemyInitPlugin': '2.0',
        'create_test_client': '1.0',
        'TestClient': '1.0',
        'advanced_alchemy': '2.0',
    }

    def __init__(self):
        """Initialize the enhanced Litestar parser."""
        pass

    def parse(self, content: str, file_path: str = "") -> LitestarParseResult:
        """
        Parse Litestar source code and extract all Litestar-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            LitestarParseResult with all extracted information
        """
        result = LitestarParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Routes ───────────────────────────────────────────────
        self._extract_http_method_routes(content, result)
        self._extract_route_decorator_routes(content, result)

        # ── Controllers ──────────────────────────────────────────
        self._extract_controllers(content, result)

        # ── Guards ───────────────────────────────────────────────
        self._extract_guards(content, result)

        # ── Dependencies ─────────────────────────────────────────
        self._extract_dependencies(content, result)

        # ── Middleware ───────────────────────────────────────────
        self._extract_middleware(content, result)

        # ── Listeners ────────────────────────────────────────────
        self._extract_listeners(content, result)

        # ── WebSocket routes ─────────────────────────────────────
        self._extract_websocket_routes(content, result)

        # ── Exception handlers ───────────────────────────────────
        self._extract_exception_handlers(content, result)

        # ── DTOs ─────────────────────────────────────────────────
        self._extract_dtos(content, result)

        # ── Plugins ──────────────────────────────────────────────
        self._extract_plugins(content, result)

        # ── Stores ───────────────────────────────────────────────
        self._extract_stores(content, result)

        # ── Security ─────────────────────────────────────────────
        self._extract_security(content, result)

        # Aggregates
        result.total_routes = len(result.routes) + len(result.websocket_routes)
        result.total_controllers = len(result.controllers)
        result.total_middleware = len(result.middleware)
        result.total_guards = len(result.guards)
        result.litestar_version = self._detect_litestar_version(content)

        return result

    # ─── Extraction methods ───────────────────────────────────────

    def _extract_http_method_routes(self, content: str, result: LitestarParseResult):
        """Extract @get(), @post(), @put(), @patch(), @delete(), @head(), @options() routes."""
        for match in self.HTTP_METHOD_DECORATOR_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2) or "/"
            is_async = match.group(3) is not None
            handler = match.group(4)

            result.routes.append(LitestarRouteInfo(
                path=path,
                handler=handler,
                methods=[method],
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_route_decorator_routes(self, content: str, result: LitestarParseResult):
        """Extract @route() decorator routes with explicit http_method."""
        # @route("/path", http_method=[...])
        for match in self.ROUTE_DECORATOR_PATTERN.finditer(content):
            path = match.group(1) or "/"
            methods_str = match.group(2) or ""
            is_async = match.group(3) is not None
            handler = match.group(4)

            methods = [m.strip().strip('"\'') for m in methods_str.split(',') if m.strip()]

            result.routes.append(LitestarRouteInfo(
                path=path,
                handler=handler,
                methods=[m.upper() for m in methods] if methods else ['GET'],
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @route("/path") without explicit http_method
        for match in self.ROUTE_DECORATOR_SIMPLE_PATTERN.finditer(content):
            path = match.group(1) or "/"
            is_async = match.group(2) is not None
            handler = match.group(3)

            # Avoid duplicates if already matched by the explicit pattern
            already = any(
                r.handler == handler and r.path == path
                for r in result.routes
            )
            if not already:
                result.routes.append(LitestarRouteInfo(
                    path=path,
                    handler=handler,
                    methods=['GET'],
                    is_async=is_async,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

    def _extract_controllers(self, content: str, result: LitestarParseResult):
        """Extract Controller classes and their metadata."""
        for match in self.CONTROLLER_PATTERN.finditer(content):
            name = match.group(1)
            class_start = match.start()

            # Find class body (until next class or end of file)
            next_class = re.search(r'\nclass\s+', content[class_start + 1:])
            class_end = class_start + 1 + next_class.start() if next_class else len(content)
            class_body = content[class_start:class_end]

            # Extract path
            path = None
            path_match = self.CONTROLLER_PATH_PATTERN.search(class_body)
            if path_match:
                path = path_match.group(1)

            # Extract guards
            guards = []
            guards_match = self.CONTROLLER_GUARDS_PATTERN.search(class_body)
            if guards_match:
                guards = [g.strip().strip('"\'') for g in guards_match.group(1).split(',') if g.strip()]

            # Extract tags
            tags = []
            tags_match = self.CONTROLLER_TAGS_PATTERN.search(class_body)
            if tags_match:
                tags = [t.strip().strip('"\'') for t in tags_match.group(1).split(',') if t.strip()]

            # Extract dependencies
            deps = []
            deps_match = self.CONTROLLER_DEPS_PATTERN.search(class_body)
            if deps_match:
                for dep_m in re.finditer(r'["\'](\w+)["\']', deps_match.group(1)):
                    deps.append(dep_m.group(1))

            # Extract middleware
            middleware = []
            mw_match = self.CONTROLLER_MIDDLEWARE_PATTERN.search(class_body)
            if mw_match:
                middleware = [m.strip() for m in mw_match.group(1).split(',') if m.strip()]

            # Extract methods (route handlers in the class)
            methods = []
            for method_match in self.HTTP_METHOD_DECORATOR_PATTERN.finditer(class_body):
                methods.append(method_match.group(1).upper())

            result.controllers.append(LitestarControllerInfo(
                name=name,
                path=path,
                guards=guards,
                tags=tags,
                dependencies=deps,
                middleware=middleware,
                methods=methods,
                line_number=content[:class_start].count('\n') + 1,
            ))

    def _extract_guards(self, content: str, result: LitestarParseResult):
        """Extract guard functions and classes."""
        # Guard functions: def my_guard(connection, _) -> None:
        for match in self.GUARD_FUNCTION_PATTERN.finditer(content):
            is_async = match.group(1) is not None
            name = match.group(2)

            result.guards.append(LitestarGuardInfo(
                name=name,
                guard_type="async_function" if is_async else "function",
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Guard classes: class MyGuard(AbstractGuard):
        for match in self.GUARD_CLASS_PATTERN.finditer(content):
            name = match.group(1)

            result.guards.append(LitestarGuardInfo(
                name=name,
                guard_type="AbstractGuard",
                is_async=False,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_dependencies(self, content: str, result: LitestarParseResult):
        """Extract Provide() and Dependency() patterns."""
        # Provide(my_dep) in dependencies={...}
        for match in self.PROVIDE_PATTERN.finditer(content):
            dep_key = match.group(1)
            dep_func = match.group(2)
            use_cache = match.group(3) == 'True' if match.group(3) else False
            sync_to_thread = match.group(4) == 'True' if match.group(4) else False

            result.dependencies.append(LitestarDependencyInfo(
                name=dep_key,
                provide_type="Provide",
                use_cache=use_cache,
                sync_to_thread=sync_to_thread,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Dependency() annotations
        for match in self.DEPENDENCY_ANNOTATION_PATTERN.finditer(content):
            name = match.group(1)

            result.dependencies.append(LitestarDependencyInfo(
                name=name,
                provide_type="Dependency",
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_middleware(self, content: str, result: LitestarParseResult):
        """Extract middleware classes and DefineMiddleware usage."""
        # class MyMiddleware(AbstractMiddleware):
        for match in self.MIDDLEWARE_CLASS_PATTERN.finditer(content):
            name = match.group(1)
            base = match.group(2)

            result.middleware.append(LitestarMiddlewareInfo(
                name=name,
                middleware_type=base,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # DefineMiddleware(MyMiddleware, ...)
        for match in self.DEFINE_MIDDLEWARE_PATTERN.finditer(content):
            name = match.group(1)

            # Avoid duplicates (already captured as class)
            already = any(m.name == name for m in result.middleware)
            if not already:
                result.middleware.append(LitestarMiddlewareInfo(
                    name=name,
                    middleware_type="DefineMiddleware",
                    line_number=content[:match.start()].count('\n') + 1,
                ))

    def _extract_listeners(self, content: str, result: LitestarParseResult):
        """Extract lifecycle event listeners."""
        # on_startup=[func1, func2], on_shutdown=[...], etc. in Litestar(...)
        for match in self.LIFECYCLE_PATTERN.finditer(content):
            event = match.group(1)
            handlers_str = match.group(2)

            for handler_match in re.finditer(r'(\w+)', handlers_str):
                handler = handler_match.group(1)

                result.listeners.append(LitestarListenerInfo(
                    event=event,
                    handler=handler,
                    is_async=True,  # Assumed async in Litestar
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        # @app.on_startup, @app.on_shutdown decorator form
        for match in self.LISTENER_DECORATOR_PATTERN.finditer(content):
            event = match.group(1)
            is_async = match.group(2) is not None
            handler = match.group(3)

            # Avoid duplicates
            already = any(
                l.handler == handler and l.event == event
                for l in result.listeners
            )
            if not already:
                result.listeners.append(LitestarListenerInfo(
                    event=event,
                    handler=handler,
                    is_async=is_async,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

    def _extract_websocket_routes(self, content: str, result: LitestarParseResult):
        """Extract WebSocket routes."""
        for match in self.WEBSOCKET_DECORATOR_PATTERN.finditer(content):
            decorator_type = match.group(1)  # websocket or websocket_listener
            path = match.group(2)
            is_async = match.group(3) is not None
            handler = match.group(4)

            result.websocket_routes.append(LitestarWebSocketInfo(
                path=path,
                handler=handler,
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_exception_handlers(self, content: str, result: LitestarParseResult):
        """Extract exception handler mappings."""
        # exception_handlers={ExceptionClass: handler_func, ...}
        for block_match in self.EXCEPTION_HANDLERS_BLOCK_PATTERN.finditer(content):
            block_content = block_match.group(1)

            for match in self.EXCEPTION_HANDLER_PATTERN.finditer(block_content):
                exc_class = match.group(1)
                handler = match.group(2)

                # Skip common false positives (Python keywords, etc.)
                if exc_class in ('True', 'False', 'None', 'self', 'cls', 'type'):
                    continue

                result.exception_handlers.append(LitestarExceptionHandlerInfo(
                    exception_class=exc_class,
                    handler=handler,
                    line_number=content[:block_match.start()].count('\n') + 1,
                ))

    def _extract_dtos(self, content: str, result: LitestarParseResult):
        """Extract DTO classes and DTOConfig instances."""
        # class MyDTO(DataclassDTO[MyModel]):
        for match in self.DTO_CLASS_PATTERN.finditer(content):
            name = match.group(1)
            dto_type = match.group(2)
            model_class = match.group(3)

            result.dtos.append(LitestarDTOInfo(
                name=name,
                dto_type=dto_type,
                model_class=model_class,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # my_config = DTOConfig(...)
        for match in self.DTO_CONFIG_PATTERN.finditer(content):
            name = match.group(1)

            result.dtos.append(LitestarDTOInfo(
                name=name,
                dto_type="DTOConfig",
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_plugins(self, content: str, result: LitestarParseResult):
        """Extract plugin classes."""
        # class MyPlugin(PluginProtocol):
        for match in self.PLUGIN_CLASS_PATTERN.finditer(content):
            name = match.group(1)
            plugin_type = match.group(2)

            result.plugins.append(LitestarPluginInfo(
                name=name,
                plugin_type=plugin_type,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_stores(self, content: str, result: LitestarParseResult):
        """Extract store instances."""
        for match in self.STORE_PATTERN.finditer(content):
            var_name = match.group(1)
            store_type = match.group(2)

            result.stores.append(LitestarStoreInfo(
                name=var_name,
                store_type=store_type,
                variable_name=var_name,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_security(self, content: str, result: LitestarParseResult):
        """Extract security configurations."""
        for match in self.SECURITY_PATTERN.finditer(content):
            var_name = match.group(1)
            auth_type = match.group(2)

            result.security.append(LitestarSecurityInfo(
                name=var_name,
                auth_type=auth_type,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    # ─── Helper methods ───────────────────────────────────────────

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a Litestar file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        if basename in ('main.py', 'app.py', 'application.py', 'server.py', '__init__.py'):
            if re.search(r'Litestar\s*\(|Starlite\s*\(', content):
                return 'app'
        if 'controller' in basename:
            return 'controller'
        if 'middleware' in basename:
            return 'middleware'
        if 'guard' in basename:
            return 'guard'
        if 'route' in basename or 'endpoint' in basename or 'view' in basename:
            return 'route'
        if 'model' in basename or 'schema' in basename:
            return 'model'
        if 'dto' in basename:
            return 'dto'
        if 'plugin' in basename:
            return 'plugin'
        if 'test' in basename:
            return 'test'
        if 'config' in basename or 'settings' in basename:
            return 'config'
        if 'depend' in basename or 'di' in basename:
            return 'dependency'

        if '/controllers/' in normalized:
            return 'controller'
        if '/middleware/' in normalized:
            return 'middleware'
        if '/guards/' in normalized:
            return 'guard'
        if '/routes/' in normalized or '/endpoints/' in normalized or '/views/' in normalized:
            return 'route'
        if '/models/' in normalized or '/schemas/' in normalized:
            return 'model'
        if '/dtos/' in normalized:
            return 'dto'
        if '/plugins/' in normalized:
            return 'plugin'

        return 'module'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Litestar ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_litestar_version(self, content: str) -> str:
        """Detect minimum Litestar version required based on features used."""
        max_version = '0.0'
        for feature, version in self.LITESTAR_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version
        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_litestar_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a Litestar-specific file.
        Returns True if the file uses Litestar directly.
        """
        # Direct litestar imports
        if re.search(r'from\s+litestar\s+import|import\s+litestar\b|from\s+litestar\.\w+\s+import', content):
            return True
        # Legacy starlite imports
        if re.search(r'from\s+starlite\s+import|import\s+starlite\b|from\s+starlite\.\w+\s+import', content):
            return True
        # Litestar app instantiation
        if re.search(r'(?:Litestar|Starlite)\s*\(', content):
            return True
        # Controller subclass
        if re.search(r'class\s+\w+\s*\(\s*Controller\s*\)', content):
            # Only if litestar/starlite is imported
            if re.search(r'(?:litestar|starlite)', content, re.IGNORECASE):
                return True
        return False

    def to_codetrellis_format(self, result: LitestarParseResult) -> str:
        """Convert parse result to CodeTrellis compressed format."""
        lines = []

        if result.file_path:
            lines.append(f"[FILE:{Path(result.file_path).name}|type:{result.file_type}]")
        if result.detected_frameworks:
            lines.append(f"[LITESTAR_ECOSYSTEM:{','.join(result.detected_frameworks)}]")
        if result.litestar_version:
            lines.append(f"[LITESTAR_VERSION:>={result.litestar_version}]")
        lines.append("")

        # Routes
        if result.routes:
            lines.append("=== LITESTAR_ROUTES ===")
            for r in result.routes:
                methods_str = ",".join(r.methods) if r.methods else "GET"
                async_str = "|async" if r.is_async else "|sync"
                ctrl_str = f"|ctrl:{r.controller}" if r.controller else ""
                lines.append(f"  {methods_str} {r.path} → {r.handler}{async_str}{ctrl_str}")
            lines.append("")

        # Controllers
        if result.controllers:
            lines.append("=== LITESTAR_CONTROLLERS ===")
            for c in result.controllers:
                path_str = f"|path:{c.path}" if c.path else ""
                methods_str = f"|methods:{','.join(c.methods)}" if c.methods else ""
                guards_str = f"|guards:{','.join(c.guards)}" if c.guards else ""
                lines.append(f"  {c.name}{path_str}{methods_str}{guards_str}")
            lines.append("")

        # Guards
        if result.guards:
            lines.append("=== LITESTAR_GUARDS ===")
            for g in result.guards:
                lines.append(f"  {g.name}[{g.guard_type}]")
            lines.append("")

        # Dependencies
        if result.dependencies:
            lines.append("=== LITESTAR_DEPENDENCIES ===")
            for d in result.dependencies:
                cache_str = "|cached" if d.use_cache else ""
                sync_str = "|sync_to_thread" if d.sync_to_thread else ""
                lines.append(f"  {d.name}[{d.provide_type}]{cache_str}{sync_str}")
            lines.append("")

        # Middleware
        if result.middleware:
            lines.append("=== LITESTAR_MIDDLEWARE ===")
            for mw in result.middleware:
                lines.append(f"  {mw.name}[{mw.middleware_type}]")
            lines.append("")

        # WebSocket routes
        if result.websocket_routes:
            lines.append("=== LITESTAR_WEBSOCKET ===")
            for ws in result.websocket_routes:
                lines.append(f"  WS {ws.path} → {ws.handler}")
            lines.append("")

        # Listeners
        if result.listeners:
            lines.append("=== LITESTAR_LISTENERS ===")
            for lh in result.listeners:
                lines.append(f"  @{lh.event} → {lh.handler}")
            lines.append("")

        # Exception handlers
        if result.exception_handlers:
            lines.append("=== LITESTAR_EXCEPTIONS ===")
            for ex in result.exception_handlers:
                lines.append(f"  {ex.exception_class} → {ex.handler}")
            lines.append("")

        # DTOs
        if result.dtos:
            lines.append("=== LITESTAR_DTOS ===")
            for dto in result.dtos:
                model_str = f"|model:{dto.model_class}" if dto.model_class else ""
                lines.append(f"  {dto.name}[{dto.dto_type}]{model_str}")
            lines.append("")

        # Plugins
        if result.plugins:
            lines.append("=== LITESTAR_PLUGINS ===")
            for p in result.plugins:
                lines.append(f"  {p.name}[{p.plugin_type}]")
            lines.append("")

        # Stores
        if result.stores:
            lines.append("=== LITESTAR_STORES ===")
            for s in result.stores:
                lines.append(f"  {s.variable_name}[{s.store_type}]")
            lines.append("")

        # Security
        if result.security:
            lines.append("=== LITESTAR_SECURITY ===")
            for sec in result.security:
                lines.append(f"  {sec.name}[{sec.auth_type}]")
            lines.append("")

        return '\n'.join(lines)
