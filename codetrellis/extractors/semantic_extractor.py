"""
Semantic Extractor for CodeTrellis
=============================
Language-agnostic extraction of behavioral/semantic patterns that syntax-based
extractors miss. This addresses the fundamental limitation where CodeTrellis captures
signatures but misses HOW code behaves.

Detects:
- Hook/Event systems (On*, Bind, Subscribe patterns)
- Middleware chains (Use, Wrap, Handler patterns)
- Custom route registrations (any .GET/.POST/.PUT/.DELETE calls)
- Plugin/Extension registration patterns
- Lifecycle methods (Init, Start, Stop, Close, Cleanup)
- Observer/Subscriber patterns

This extractor works by scanning raw text for semantic patterns rather than
parsing AST, making it inherently language-agnostic.

Part of CodeTrellis v4.6 - Generic Semantic Extraction
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from pathlib import Path


@dataclass
class HookInfo:
    """A detected hook/event registration."""
    name: str               # Hook name (e.g., "OnBeforeServe", "OnRecordCreate")
    hook_type: str           # 'lifecycle', 'event', 'observer', 'callback'
    file: str
    line: int
    pattern: str             # The matched pattern (e.g., "app.OnBeforeServe.Add()")
    return_type: str = ""    # For Go: *hook.Hook, for JS: EventEmitter, etc.


@dataclass
class MiddlewareInfo:
    """A detected middleware registration."""
    name: str               # Middleware name or description
    file: str
    line: int
    pattern: str            # e.g., "router.Use(authMiddleware)"
    middleware_type: str = "generic"  # 'auth', 'logging', 'cors', 'rate-limit', 'generic'


@dataclass
class GenericRouteInfo:
    """A detected route registration from any framework/custom router."""
    method: str             # GET, POST, PUT, DELETE, PATCH, etc.
    path: str               # The URL path
    handler: str            # Handler function/method name
    file: str
    line: int
    receiver: str = ""      # The object the route is called on (e.g., "router", "api", "group")


@dataclass
class PluginInfo:
    """A detected plugin/extension registration."""
    name: str
    file: str
    line: int
    pattern: str
    plugin_type: str = "generic"  # 'plugin', 'extension', 'addon', 'module'


@dataclass
class LifecycleInfo:
    """A detected lifecycle method."""
    name: str               # e.g., "Init", "Start", "Close"
    phase: str              # 'init', 'start', 'run', 'stop', 'cleanup'
    file: str
    line: int
    owner: str = ""         # Class/struct/receiver that owns this method


@dataclass
class CLICommandInfo:
    """A detected CLI command (cobra, click, argparse, etc.)."""
    name: str               # Command name (e.g., "serve", "superuser")
    description: str        # Short description from Short/help fields
    file: str
    line: int
    parent: str = ""        # Parent command if subcommand
    cli_framework: str = "generic"  # 'cobra', 'click', 'argparse', 'commander'


@dataclass
class SemanticResult:
    """Complete semantic extraction result for a project."""
    hooks: List[HookInfo] = field(default_factory=list)
    middleware: List[MiddlewareInfo] = field(default_factory=list)
    generic_routes: List[GenericRouteInfo] = field(default_factory=list)
    plugins: List[PluginInfo] = field(default_factory=list)
    lifecycle: List[LifecycleInfo] = field(default_factory=list)
    cli_commands: List[CLICommandInfo] = field(default_factory=list)


class SemanticExtractor:
    """
    Language-agnostic semantic pattern extractor.

    Strategy:
    1. Scan file text for known behavioral patterns (hooks, middleware, routes, etc.)
    2. Use heuristics to identify patterns regardless of language
    3. Produce structured data that the compressor can emit as sections

    This is intentionally regex/heuristic-based rather than AST-based so it works
    across Go, Python, TypeScript, Rust, Java, and any new language without
    language-specific parsers.
    """

    # --- Hook/Event Patterns ---
    # Matches: On<Event>, Hook<Event>, .Add(), .Bind(), .BindFunc(), .Subscribe(), .On()
    HOOK_PATTERNS = [
        # Go PocketBase-style: app.OnBeforeServe().Add(func(e *core.ServeEvent) error { ... })
        (r'(\w+)\.(On\w+)\s*\(\s*\)\.(?:Add|PreAdd|BindFunc)\s*\(', 'event'),
        # Go hook field declarations: OnBeforeServe *hook.Hook[*ServeEvent]
        (r'(On\w+)\s+\*?hook\.Hook\[', 'lifecycle'),
        # Generic .On("event", handler) — Node.js EventEmitter, Socket.IO, etc.
        (r'(\w+)\.On\s*\(\s*["\'](\w+)["\']', 'event'),
        # .Subscribe("event", handler) — NATS, Redis PubSub, etc.
        (r'(\w+)\.Subscribe\s*\(\s*["\']([^"\']+)["\']', 'observer'),
        # .AddListener("event", handler)
        (r'(\w+)\.AddListener\s*\(\s*["\'](\w+)["\']', 'observer'),
        # @EventHandler, @OnEvent decorators (NestJS, Spring)
        (r'@(?:EventHandler|OnEvent|Listener)\s*\(\s*["\']?(\w+)', 'event'),
        # .Emit("event") — tracks what events are emitted
        (r'(\w+)\.Emit\s*\(\s*["\'](\w+)["\']', 'event'),
        # Python signals: signal.connect(handler)
        (r'(\w+)\.connect\s*\(', 'observer'),
        # Go lifecycle hooks: OnModelBeforeCreate, OnModelAfterCreate, etc.
        (r'(\w+)\.(On(?:Model|Record|Collection|Admin|Mail|Settings)(?:Before|After)\w+)', 'lifecycle'),
    ]

    # --- Middleware Patterns ---
    MIDDLEWARE_PATTERNS = [
        # .Use(middleware) — Express, Gin, Echo, Chi, Fiber, Koa
        (r'(\w+)\.Use\s*\(([^)]+)\)', 'generic'),
        # .Middleware(func) — custom middleware registration
        (r'(\w+)\.Middleware\s*\(([^)]+)\)', 'generic'),
        # app.middleware("path", handler) — various frameworks
        (r'(\w+)\.middleware\s*\(', 'generic'),
        # Go: func(next http.Handler) http.Handler pattern (middleware signature)
        (r'func\s+(\w+)\s*\([^)]*http\.Handler[^)]*\)\s*http\.Handler', 'generic'),
        # Go: func(next http.HandlerFunc) http.HandlerFunc
        (r'func\s+(\w+)\s*\([^)]*http\.HandlerFunc[^)]*\)\s*http\.HandlerFunc', 'generic'),
        # Go: exported func returning *hook.Handler (PocketBase-style middleware factories)
        (r'func\s+(Require\w+|Skip\w+|BodyLimit|CORS|Gzip|GzipWithConfig|RateLimit|LoadAuth\w*|WrapStd\w*)\s*\([^)]*\)\s*\*?(?:hook\.Handler|Hook)', 'auth'),
        # Go: .Bind(middleware) — PocketBase/custom framework middleware binding
        (r'\.Bind\s*\(\s*(Require\w+|Skip\w+|BodyLimit|CORS|Gzip|RateLimit)\s*\(', 'generic'),
        # Python: @middleware decorator
        (r'@middleware', 'generic'),
        # Python ASGI/WSGI middleware
        (r'class\s+(\w+Middleware)\s*[\(:]', 'generic'),
        # NestJS: @UseGuards, @UseInterceptors, @UsePipes
        (r'@Use(?:Guards|Interceptors|Pipes|Filters)\s*\(([^)]+)\)', 'generic'),
        # Middleware ID constants (e.g., DefaultRateLimitMiddlewareId)
        (r'(\w+MiddlewareId)\s*=\s*["\']([^"\']+)["\']', 'generic'),
    ]

    # --- Generic Route Patterns ---
    # These catch routes from ANY framework, not just known ones
    # v4.9: Changed [^"']+ to [^"']* to match empty-path routes like .GET("", handler)
    ROUTE_PATTERNS = [
        # .GET("/path", handler), .POST("/path", handler), etc.
        (r'(\w+)\.(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\(\s*["\']([^"\']*)["\'\)]\s*,\s*(\w+(?:\.\w+)?)', None),
        # .Get("/path", handler), .Post("/path", handler)  (case variants)
        (r'(\w+)\.(Get|Post|Put|Delete|Patch|Head|Options)\s*\(\s*["\']([^"\']*)["\'\)]\s*,\s*(\w+(?:\.\w+)?)', None),
        # .Handle("METHOD", "/path", handler)
        (r'(\w+)\.Handle\s*\(\s*["\']?(GET|POST|PUT|DELETE|PATCH)["\']?\s*,\s*["\']([^"\']*)["\'\)]\s*,\s*(\w+(?:\.\w+)?)', None),
        # .HandleFunc("/path", handler).Methods("GET")
        (r'(\w+)\.HandleFunc\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+(?:\.\w+)?)\s*\)\.Methods\s*\(\s*["\'](\w+)["\']', None),
        # http.HandleFunc("/path", handler) — Go stdlib
        (r'(http)\.HandleFunc\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)', None),
        # router.add_api_route("/path", handler, methods=["GET"])
        (r'(\w+)\.add_api_route\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)', None),
        # @app.get("/path"), @app.post("/path") — FastAPI/Flask
        (r'@(\w+)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', None),
        # router.route("/path").get(handler).post(handler) — Express
        (r'(\w+)\.route\s*\(\s*["\']([^"\']+)["\']\s*\)\.(get|post|put|delete|patch)\s*\((\w+)', None),
    ]

    # --- Plugin/Extension Patterns ---
    PLUGIN_PATTERNS = [
        # .Register(plugin), .RegisterPlugin(plugin), .AddPlugin(plugin)
        (r'(\w+)\.(?:Register|RegisterPlugin|AddPlugin|InstallPlugin)\s*\(([^)]+)\)', 'plugin'),
        # .Use(plugin) — when used with plugin-like objects
        (r'app\.Use\s*\(\s*(\w+Plugin)', 'plugin'),
        # Go: plugin.Register("name", impl)
        (r'(\w+)\.Register\s*\(\s*["\']([^"\']+)["\']', 'plugin'),
        # Go: MustRegister(name, impl) — Prometheus, telemetry, etc.
        (r'(?:Must)?Register\s*\(\s*["\']?(\w+)["\']?\s*,', 'plugin'),
        # Go: interface-based plugin — type X interface { ... }Plugin suffix
        (r'type\s+(\w+Plugin)\s+interface\s*\{', 'plugin'),
        # Python: app.register_blueprint, app.include_router
        (r'(\w+)\.(?:register_blueprint|include_router)\s*\(([^)]+)\)', 'extension'),
        # Go/Generic: .Mount("/prefix", subApp) — mounting sub-applications
        (r'(\w+)\.Mount\s*\(\s*["\']([^"\']+)["\']', 'extension'),
    ]

    # --- Lifecycle Patterns ---
    LIFECYCLE_PATTERNS = {
        'init': [r'func\s+(?:\([^)]+\)\s+)?(?:Init|Initialize|Setup|Configure)\s*\(',
                 r'def\s+(?:__init__|initialize|setup|configure)\s*\(',
                 r'(?:onInit|ngOnInit|componentDidMount|onCreate)\s*\('],
        'start': [r'func\s+(?:\([^)]+\)\s+)?(?:Start|Run|Serve|Listen|Boot|Launch)\s*\(',
                  r'def\s+(?:start|run|serve|boot|launch)\s*\(',
                  r'(?:onStart|main)\s*\('],
        'stop': [r'func\s+(?:\([^)]+\)\s+)?(?:Stop|Shutdown|Close|Terminate|Cleanup)\s*\(',
                 r'def\s+(?:stop|shutdown|close|cleanup|teardown|__del__)\s*\(',
                 r'(?:onDestroy|componentWillUnmount|ngOnDestroy)\s*\('],
    }

    # --- CLI Command Patterns ---
    CLI_COMMAND_PATTERNS = [
        # Go cobra: &cobra.Command{Use: "serve", Short: "..."}
        (r'cobra\.Command\s*\{[^}]*Use:\s*"([^"]+)"[^}]*?(?:Short:\s*"([^"]+)")?', 'cobra'),
        # Go cobra: .AddCommand(cmd)
        (r'(\w+)\.AddCommand\s*\(\s*(\w+)', 'cobra'),
        # Python click: @click.command(name="serve")
        (r'@click\.command\s*\(\s*(?:name\s*=\s*)?["\'](\w+)["\']', 'click'),
        # Python click: @click.group()
        (r'@click\.group\s*\(', 'click'),
        # Python argparse: parser.add_subparsers / subparser.add_parser("name")
        (r'\.add_parser\s*\(\s*["\'](\w+)["\'](?:\s*,\s*help\s*=\s*["\']([^"\']+)["\'])?', 'argparse'),
        # Node.js commander: .command("serve")
        (r'\.command\s*\(\s*["\'](\w+)["\'](?:\s*,\s*["\']([^"\']+)["\'])?', 'commander'),
    ]

    def __init__(self):
        """Initialize SemanticExtractor with compiled patterns."""
        pass

    def extract(self, content: str, file_path: str) -> SemanticResult:
        """Extract all semantic patterns from a source file."""
        result = SemanticResult()

        lines = content.split('\n')

        # Extract hooks
        result.hooks = self._extract_hooks(content, file_path, lines)

        # Extract middleware
        result.middleware = self._extract_middleware(content, file_path, lines)

        # Extract generic routes
        result.generic_routes = self._extract_routes(content, file_path, lines)

        # Extract plugins
        result.plugins = self._extract_plugins(content, file_path, lines)

        # Extract lifecycle methods
        result.lifecycle = self._extract_lifecycle(content, file_path, lines)

        # Extract CLI commands
        result.cli_commands = self._extract_cli_commands(content, file_path)

        return result

    def _get_line_number(self, content: str, pos: int) -> int:
        """Get 1-based line number for a position in content."""
        return content[:pos].count('\n') + 1

    def _extract_hooks(self, content: str, file_path: str, lines: List[str]) -> List[HookInfo]:
        """Extract hook/event registrations."""
        hooks = []
        seen = set()

        for pattern, hook_type in self.HOOK_PATTERNS:
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_num = self._get_line_number(content, match.start())
                groups = match.groups()

                # Determine hook name based on pattern groups
                if len(groups) >= 2:
                    receiver = groups[0]
                    hook_name = groups[1]
                    pattern_str = match.group(0).strip()[:80]
                else:
                    hook_name = groups[0]
                    receiver = ""
                    pattern_str = match.group(0).strip()[:80]

                # Deduplicate
                key = f"{hook_name}:{file_path}:{line_num}"
                if key in seen:
                    continue
                seen.add(key)

                hooks.append(HookInfo(
                    name=hook_name,
                    hook_type=hook_type,
                    file=file_path,
                    line=line_num,
                    pattern=pattern_str,
                ))

        return hooks

    def _extract_middleware(self, content: str, file_path: str, lines: List[str]) -> List[MiddlewareInfo]:
        """Extract middleware registrations."""
        middleware = []
        seen = set()

        for pattern, mw_type in self.MIDDLEWARE_PATTERNS:
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_num = self._get_line_number(content, match.start())
                groups = match.groups()
                pattern_str = match.group(0).strip()[:80]

                # Extract middleware name
                if len(groups) >= 2:
                    name = groups[1].strip().split(',')[0].strip().strip('"\'')
                elif len(groups) >= 1:
                    name = groups[0].strip()
                else:
                    name = "unknown"

                # Classify middleware type
                name_lower = name.lower()
                if any(k in name_lower for k in ['auth', 'jwt', 'token', 'guard', 'permission']):
                    mw_type = 'auth'
                elif any(k in name_lower for k in ['log', 'logger', 'logging']):
                    mw_type = 'logging'
                elif any(k in name_lower for k in ['cors']):
                    mw_type = 'cors'
                elif any(k in name_lower for k in ['rate', 'limit', 'throttle']):
                    mw_type = 'rate-limit'

                key = f"{name}:{line_num}"
                if key in seen:
                    continue
                seen.add(key)

                middleware.append(MiddlewareInfo(
                    name=name,
                    file=file_path,
                    line=line_num,
                    pattern=pattern_str,
                    middleware_type=mw_type,
                ))

        return middleware

    def _extract_routes(self, content: str, file_path: str, lines: List[str]) -> List[GenericRouteInfo]:
        """Extract route registrations from any framework."""
        routes = []
        seen = set()

        for pattern, _ in self.ROUTE_PATTERNS:
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_num = self._get_line_number(content, match.start())
                groups = match.groups()

                # Different patterns have different group orderings
                # Most: (receiver, method, path, handler) or variants
                receiver = ""
                method = ""
                path = ""
                handler = ""

                if len(groups) == 4:
                    receiver, method, path, handler = groups
                elif len(groups) == 3:
                    # Could be (receiver, path, handler) or (receiver, method, path)
                    if groups[1].startswith('/') or groups[1].startswith(':'):
                        receiver, path, handler = groups
                        method = "GET"  # Default
                    else:
                        receiver, method, path = groups
                        handler = "anonymous"
                elif len(groups) == 2:
                    receiver, path = groups
                    method = "GET"
                    handler = "anonymous"

                method = method.upper()

                # Filter: path must look like a URL path (starts with / or : or {)
                # This avoids matching r.Get("Content-Type") as a route
                if path and not (path.startswith('/') or path.startswith(':') or path.startswith('{')):
                    continue

                key = f"{method}:{path}:{line_num}"
                if key in seen:
                    continue
                seen.add(key)

                routes.append(GenericRouteInfo(
                    method=method,
                    path=path,
                    handler=handler,
                    file=file_path,
                    line=line_num,
                    receiver=receiver,
                ))

        return routes

    def _extract_plugins(self, content: str, file_path: str, lines: List[str]) -> List[PluginInfo]:
        """Extract plugin/extension registrations."""
        plugins = []
        seen = set()

        for pattern, plugin_type in self.PLUGIN_PATTERNS:
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_num = self._get_line_number(content, match.start())
                groups = match.groups()
                pattern_str = match.group(0).strip()[:80]

                if len(groups) >= 2:
                    name = groups[1].strip().split(',')[0].strip().strip('"\'')
                else:
                    name = groups[0].strip() if groups else "unknown"

                key = f"{name}:{line_num}"
                if key in seen:
                    continue
                seen.add(key)

                plugins.append(PluginInfo(
                    name=name,
                    file=file_path,
                    line=line_num,
                    pattern=pattern_str,
                    plugin_type=plugin_type,
                ))

        return plugins

    def _extract_lifecycle(self, content: str, file_path: str, lines: List[str]) -> List[LifecycleInfo]:
        """Extract lifecycle method definitions."""
        lifecycle = []
        seen = set()

        for phase, patterns in self.LIFECYCLE_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    line_num = self._get_line_number(content, match.start())
                    matched_text = match.group(0).strip()

                    # Try to extract method name
                    name_match = re.search(r'(?:func\s+(?:\([^)]+\)\s+)?|def\s+)(\w+)', matched_text)
                    if name_match:
                        name = name_match.group(1)
                    else:
                        name = matched_text[:30]

                    # Try to extract owner (receiver for Go, class for Python/TS)
                    owner = ""
                    receiver_match = re.search(r'\(\s*\w+\s+\*?(\w+)\s*\)', matched_text)
                    if receiver_match:
                        owner = receiver_match.group(1)

                    key = f"{name}:{file_path}:{line_num}"
                    if key in seen:
                        continue
                    seen.add(key)

                    lifecycle.append(LifecycleInfo(
                        name=name,
                        phase=phase,
                        file=file_path,
                        line=line_num,
                        owner=owner,
                    ))

        return lifecycle

    def _extract_cli_commands(self, content: str, file_path: str) -> List[CLICommandInfo]:
        """Extract CLI command definitions (cobra, click, argparse, commander)."""
        commands = []
        seen = set()

        for pattern, framework in self.CLI_COMMAND_PATTERNS:
            for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                line_num = self._get_line_number(content, match.start())
                groups = match.groups()

                name = ""
                description = ""

                if framework == 'cobra' and 'AddCommand' not in pattern:
                    # cobra.Command{Use: "serve", Short: "..."}
                    name = groups[0] if len(groups) >= 1 else ""
                    description = groups[1] if len(groups) >= 2 and groups[1] else ""
                    # Clean Use field (may have args like "serve [domain(s)]")
                    name = name.split()[0] if name else ""
                elif framework == 'cobra' and 'AddCommand' in pattern:
                    # .AddCommand(cmd) — skip these, the commands themselves are captured
                    continue
                elif len(groups) >= 2 and groups[1]:
                    name = groups[0]
                    description = groups[1]
                elif len(groups) >= 1:
                    name = groups[0]

                if not name:
                    continue

                key = f"{name}:{file_path}"
                if key in seen:
                    continue
                seen.add(key)

                commands.append(CLICommandInfo(
                    name=name,
                    description=description or "",
                    file=file_path,
                    line=line_num,
                    cli_framework=framework,
                ))

        return commands
