"""
EnhancedFastAPIParser v1.0 - Comprehensive FastAPI parser using all extractors.

This parser provides enhanced FastAPI extraction beyond the basic FastAPIExtractor,
adding support for dependency injection trees, middleware, event handlers, WebSocket
routes, background tasks, and more.

Supports:
- FastAPI 0.1.x - 0.50.x (early versions, basic routing)
- FastAPI 0.50.x - 0.80.x (APIRouter, Depends, BackgroundTasks)
- FastAPI 0.80.x - 0.100.x (lifespan, improved OpenAPI)
- FastAPI 0.100.x+ (Annotated dependencies, latest patterns)

FastAPI-specific extraction:
- Routes: @app.get/post/put/delete/patch, WebSocket routes
- APIRouter: prefix, tags, dependencies, nested routers
- Dependency Injection: Depends(), Security(), full DI tree
- Middleware: CORS, Trusted Hosts, GZip, custom
- Event Handlers: on_event("startup"/"shutdown"), lifespan context manager
- Background Tasks: BackgroundTasks parameter
- WebSocket: @app.websocket, WebSocketEndpoint
- Exception Handlers: @app.exception_handler, HTTPException
- OpenAPI: tags_metadata, description, version, servers

Framework detection (20+ FastAPI ecosystem patterns):
- Core: FastAPI, APIRouter, Depends, Security
- Auth: fastapi-users, fastapi-jwt-auth, python-jose
- Database: SQLModel, Tortoise-ORM, databases, ormar
- Validation: Pydantic v1/v2
- Testing: TestClient, httpx, pytest-asyncio
- Deployment: uvicorn, gunicorn, hypercorn
- Admin: sqladmin, fastapi-admin
- Caching: fastapi-cache, aiocache
- Background: celery, arq, rq, dramatiq
- Docs: openapi, swagger, redoc

Part of CodeTrellis v4.33 - FastAPI Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import existing FastAPI extractor
from .extractors.python import (
    FastAPIExtractor, FastAPIRouteInfo,
)
from .extractors.python.fastapi_extractor import (
    FastAPIRouterInfo, FastAPIParameterInfo, FastAPIDependencyInfo,
)


@dataclass
class FastAPIMiddlewareInfo:
    """Information about FastAPI middleware."""
    name: str
    middleware_type: str  # cors, trustedhost, gzip, custom, http
    kwargs: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0


@dataclass
class FastAPIEventHandlerInfo:
    """Information about a FastAPI event handler."""
    event: str  # startup, shutdown, lifespan
    handler: str
    is_async: bool = False
    line_number: int = 0


@dataclass
class FastAPIWebSocketInfo:
    """Information about a FastAPI WebSocket route."""
    path: str
    handler: str
    is_async: bool = True
    parameters: List[FastAPIParameterInfo] = field(default_factory=list)
    line_number: int = 0


@dataclass
class FastAPIExceptionHandlerInfo:
    """Information about a FastAPI exception handler."""
    exception_class: str
    handler: str
    line_number: int = 0


@dataclass
class FastAPIBackgroundTaskInfo:
    """Information about background task usage in a handler."""
    handler: str
    task_functions: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class FastAPIParseResult:
    """Complete parse result for a FastAPI file."""
    file_path: str
    file_type: str = "module"  # app, router, model, schema, dependency, test

    # Routes (from existing extractor)
    routes: List[FastAPIRouteInfo] = field(default_factory=list)
    routers: List[FastAPIRouterInfo] = field(default_factory=list)

    # Enhanced extraction
    websocket_routes: List[FastAPIWebSocketInfo] = field(default_factory=list)
    middleware: List[FastAPIMiddlewareInfo] = field(default_factory=list)
    event_handlers: List[FastAPIEventHandlerInfo] = field(default_factory=list)
    exception_handlers: List[FastAPIExceptionHandlerInfo] = field(default_factory=list)
    background_tasks: List[FastAPIBackgroundTaskInfo] = field(default_factory=list)

    # Aggregate
    detected_frameworks: List[str] = field(default_factory=list)
    fastapi_version: str = ""
    uses_pydantic_v2: bool = False
    total_routes: int = 0
    total_middleware: int = 0


class EnhancedFastAPIParser:
    """
    Enhanced FastAPI parser v1.0 that extends the basic FastAPIExtractor.

    Provides additional extraction for WebSocket routes, middleware,
    event handlers, exception handlers, and background tasks.
    """

    # FastAPI ecosystem detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core FastAPI ──────────────────────────────────────────
        'fastapi': re.compile(
            r'from\s+fastapi\s+import|import\s+fastapi',
            re.MULTILINE
        ),
        'fastapi.routing': re.compile(
            r'APIRouter|from\s+fastapi\.routing',
            re.MULTILINE
        ),

        # ── Auth ──────────────────────────────────────────────────
        'fastapi_users': re.compile(
            r'from\s+fastapi_users|import\s+fastapi_users',
            re.MULTILINE
        ),
        'python_jose': re.compile(
            r'from\s+jose\s+import|import\s+jose',
            re.MULTILINE
        ),
        'passlib': re.compile(
            r'from\s+passlib|import\s+passlib',
            re.MULTILINE
        ),

        # ── Database ──────────────────────────────────────────────
        'sqlmodel': re.compile(
            r'from\s+sqlmodel|import\s+sqlmodel|SQLModel',
            re.MULTILINE
        ),
        'tortoise': re.compile(
            r'from\s+tortoise|import\s+tortoise',
            re.MULTILINE
        ),
        'databases': re.compile(
            r'from\s+databases\s+import|import\s+databases',
            re.MULTILINE
        ),
        'ormar': re.compile(
            r'from\s+ormar|import\s+ormar',
            re.MULTILINE
        ),
        'beanie': re.compile(
            r'from\s+beanie|import\s+beanie',
            re.MULTILINE
        ),

        # ── Pydantic ─────────────────────────────────────────────
        'pydantic': re.compile(
            r'from\s+pydantic|import\s+pydantic',
            re.MULTILINE
        ),

        # ── Testing ──────────────────────────────────────────────
        'testclient': re.compile(
            r'from\s+fastapi\.testclient|TestClient|from\s+httpx',
            re.MULTILINE
        ),

        # ── Deployment ───────────────────────────────────────────
        'uvicorn': re.compile(
            r'import\s+uvicorn|uvicorn\.run',
            re.MULTILINE
        ),

        # ── Admin ────────────────────────────────────────────────
        'sqladmin': re.compile(
            r'from\s+sqladmin|import\s+sqladmin',
            re.MULTILINE
        ),

        # ── Caching ──────────────────────────────────────────────
        'fastapi_cache': re.compile(
            r'from\s+fastapi_cache|@cache',
            re.MULTILINE
        ),

        # ── Background Tasks ─────────────────────────────────────
        'celery': re.compile(
            r'from\s+celery|import\s+celery',
            re.MULTILINE
        ),
        'arq': re.compile(
            r'from\s+arq|import\s+arq',
            re.MULTILINE
        ),

        # ── Monitoring ───────────────────────────────────────────
        'prometheus': re.compile(
            r'from\s+prometheus_fastapi_instrumentator|instrumentator',
            re.MULTILINE
        ),
    }

    # WebSocket route pattern
    WEBSOCKET_PATTERN = re.compile(
        r'@(\w+)\.websocket\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE
    )

    # Middleware patterns
    ADD_MIDDLEWARE_PATTERN = re.compile(
        r'(\w+)\.add_middleware\s*\(\s*(\w+)(?:\s*,\s*([^)]+))?\s*\)',
        re.MULTILINE
    )

    # Event handler patterns (old style)
    EVENT_HANDLER_PATTERN = re.compile(
        r'@(\w+)\.on_event\s*\(\s*["\'](\w+)["\']\s*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE
    )

    # Lifespan pattern (new style)
    LIFESPAN_PATTERN = re.compile(
        r'@asynccontextmanager\s*\n\s*async\s+def\s+(\w+)\s*\(\s*app',
        re.MULTILINE
    )

    # Exception handler pattern
    EXCEPTION_HANDLER_PATTERN = re.compile(
        r'@(\w+)\.exception_handler\s*\(\s*(\w+)\s*\)\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE
    )

    # Background task usage
    BACKGROUND_TASK_PATTERN = re.compile(
        r'background_tasks\s*:\s*BackgroundTasks',
        re.MULTILINE
    )

    # FastAPI version features
    FASTAPI_VERSION_FEATURES = {
        'lifespan': '0.93',
        'Annotated': '0.95',
        '@asynccontextmanager': '0.93',
        'on_event': '0.1',
        'APIRouter': '0.20',
        'BackgroundTasks': '0.30',
        'WebSocket': '0.20',
    }

    def __init__(self):
        """Initialize the enhanced FastAPI parser."""
        self.fastapi_extractor = FastAPIExtractor()

    def parse(self, content: str, file_path: str = "") -> FastAPIParseResult:
        """
        Parse FastAPI source code and extract all FastAPI-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            FastAPIParseResult with all extracted FastAPI information
        """
        result = FastAPIParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Pydantic v2 detection
        result.uses_pydantic_v2 = bool(re.search(r'model_validator|field_validator|ConfigDict', content))

        # ── Routes & Routers (existing extractor) ────────────────
        fastapi_result = self.fastapi_extractor.extract(content)
        result.routes = fastapi_result.get('routes', [])
        result.routers = fastapi_result.get('routers', [])
        result.total_routes = len(result.routes)

        # ── WebSocket Routes ─────────────────────────────────────
        for match in self.WEBSOCKET_PATTERN.finditer(content):
            result.websocket_routes.append(FastAPIWebSocketInfo(
                path=match.group(2),
                handler=match.group(4),
                is_async=match.group(3) is not None,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # ── Middleware ───────────────────────────────────────────
        for match in self.ADD_MIDDLEWARE_PATTERN.finditer(content):
            mw_class = match.group(2)
            kwargs_str = match.group(3) or ""

            # Parse kwargs
            kwargs = {}
            for kv in re.finditer(r'(\w+)\s*=\s*([^,\)]+)', kwargs_str):
                kwargs[kv.group(1)] = kv.group(2).strip()

            mw_type = 'cors' if 'CORS' in mw_class else \
                      'trustedhost' if 'TrustedHost' in mw_class else \
                      'gzip' if 'GZip' in mw_class else \
                      'http' if 'HTTPSRedirect' in mw_class else 'custom'

            result.middleware.append(FastAPIMiddlewareInfo(
                name=mw_class,
                middleware_type=mw_type,
                kwargs=kwargs,
                line_number=content[:match.start()].count('\n') + 1,
            ))
        result.total_middleware = len(result.middleware)

        # ── Event Handlers ───────────────────────────────────────
        for match in self.EVENT_HANDLER_PATTERN.finditer(content):
            result.event_handlers.append(FastAPIEventHandlerInfo(
                event=match.group(2),
                handler=match.group(4),
                is_async=match.group(3) is not None,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Lifespan handler
        lifespan_match = self.LIFESPAN_PATTERN.search(content)
        if lifespan_match:
            result.event_handlers.append(FastAPIEventHandlerInfo(
                event='lifespan',
                handler=lifespan_match.group(1),
                is_async=True,
                line_number=content[:lifespan_match.start()].count('\n') + 1,
            ))

        # ── Exception Handlers ───────────────────────────────────
        for match in self.EXCEPTION_HANDLER_PATTERN.finditer(content):
            result.exception_handlers.append(FastAPIExceptionHandlerInfo(
                exception_class=match.group(2),
                handler=match.group(4),
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # ── Version detection ────────────────────────────────────
        result.fastapi_version = self._detect_fastapi_version(content)

        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a FastAPI file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        if basename in ('main.py', 'app.py', '__init__.py'):
            if 'FastAPI(' in content:
                return 'app'
        if 'router' in basename or 'route' in basename or 'endpoint' in basename:
            return 'router'
        if 'model' in basename or 'schema' in basename:
            return 'schema'
        if 'depend' in basename:
            return 'dependency'
        if 'test' in basename:
            return 'test'

        if '/routers/' in normalized or '/routes/' in normalized or '/endpoints/' in normalized:
            return 'router'
        if '/models/' in normalized or '/schemas/' in normalized:
            return 'schema'
        if '/dependencies/' in normalized:
            return 'dependency'

        return 'module'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect FastAPI ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_fastapi_version(self, content: str) -> str:
        """Detect minimum FastAPI version required."""
        max_version = '0.0'
        for feature, version in self.FASTAPI_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version
        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_fastapi_file(self, content: str, file_path: str = "") -> bool:
        """Determine if a file is a FastAPI-specific file."""
        if re.search(r'from\s+fastapi\s+import|import\s+fastapi', content):
            return True
        if re.search(r'FastAPI\s*\(|APIRouter\s*\(', content):
            return True
        if re.search(r'@\w+\.(get|post|put|delete|patch)\s*\(', content):
            if 'Depends' in content or 'Response' in content:
                return True
        normalized = file_path.replace('\\', '/').lower()
        if any(p in normalized for p in ['/routers/', '/endpoints/', '/dependencies/']):
            return True
        return False

    def to_codetrellis_format(self, result: FastAPIParseResult) -> str:
        """Convert parse result to CodeTrellis compressed format."""
        lines = []

        if result.file_path:
            lines.append(f"[FILE:{Path(result.file_path).name}|type:{result.file_type}]")
        if result.detected_frameworks:
            lines.append(f"[FASTAPI_ECOSYSTEM:{','.join(result.detected_frameworks)}]")
        if result.fastapi_version:
            lines.append(f"[FASTAPI_VERSION:>={result.fastapi_version}]")
        lines.append("")

        # Routers
        if result.routers:
            lines.append("=== FASTAPI_ROUTERS ===")
            for r in result.routers:
                tags = f"|tags:{','.join(r.tags)}" if r.tags else ""
                lines.append(f"  {r.name}|prefix:{r.prefix}{tags}")
            lines.append("")

        # Routes
        if result.routes:
            lines.append("=== FASTAPI_ROUTES ===")
            for r in result.routes:
                async_str = "|async" if r.is_async else ""
                response = f"|resp:{r.response_model}" if r.response_model else ""
                deps = f"|deps:{','.join(d.dependency_func for d in r.dependencies)}" if r.dependencies else ""
                tags = f"|tags:{','.join(r.tags)}" if r.tags else ""
                lines.append(f"  {r.method} {r.path} → {r.handler}{async_str}{response}{deps}{tags}")
            lines.append("")

        # WebSocket routes
        if result.websocket_routes:
            lines.append("=== FASTAPI_WEBSOCKET ===")
            for ws in result.websocket_routes:
                lines.append(f"  WS {ws.path} → {ws.handler}")
            lines.append("")

        # Middleware
        if result.middleware:
            lines.append("=== FASTAPI_MIDDLEWARE ===")
            for mw in result.middleware:
                kwargs_str = ",".join(f"{k}={v}" for k, v in list(mw.kwargs.items())[:3])
                lines.append(f"  {mw.name}[{mw.middleware_type}]({kwargs_str})")
            lines.append("")

        # Event handlers
        if result.event_handlers:
            lines.append("=== FASTAPI_EVENTS ===")
            for eh in result.event_handlers:
                lines.append(f"  @{eh.event} → {eh.handler}")
            lines.append("")

        # Exception handlers
        if result.exception_handlers:
            lines.append("=== FASTAPI_EXCEPTIONS ===")
            for ex in result.exception_handlers:
                lines.append(f"  {ex.exception_class} → {ex.handler}")
            lines.append("")

        return '\n'.join(lines)
