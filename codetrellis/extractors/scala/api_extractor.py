"""
ScalaAPIExtractor - Extracts Scala API endpoints, routes, and controllers.

This extractor parses Scala source code and extracts:
- Play Framework routes (conf/routes, @routes annotation, Router DSL)
- Akka HTTP directives (path, get, post, complete, entity)
- http4s routes (HttpRoutes, HttpApp, DSL)
- Tapir endpoints (endpoint.get.in.out)
- Finch endpoints (get, post, body, path)
- Scalatra routes (get, post, put, delete)
- ZIO HTTP routes (Routes, Method, handler)
- Cask routes (@cask.get, @cask.post)
- gRPC services (ScalaPB, fs2-grpc)
- GraphQL types (Caliban, Sangria)
- Controller patterns (Play controllers, Akka HTTP)

Supports Play 2.6+, Akka HTTP, http4s 0.21+, Tapir, ZIO HTTP 3.x.

Part of CodeTrellis v4.25 - Scala Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ScalaRouteInfo:
    """Information about a Scala HTTP route/endpoint."""
    method: str  # GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, WS, ANY
    path: str
    handler: str = ""
    framework: str = "play"  # play, akka_http, http4s, tapir, finch, scalatra, zio_http, cask
    file: str = ""
    line_number: int = 0
    controller: Optional[str] = None
    content_type: Optional[str] = None
    auth_required: bool = False
    middleware: List[str] = field(default_factory=list)
    query_params: List[str] = field(default_factory=list)
    path_params: List[str] = field(default_factory=list)


@dataclass
class ScalaControllerInfo:
    """Information about a Scala controller."""
    name: str
    actions: List[str] = field(default_factory=list)
    framework: str = "play"  # play, akka_http, http4s, tapir
    parent_class: Optional[str] = None
    injected_services: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_abstract: bool = False


@dataclass
class ScalaGRPCServiceInfo:
    """Information about a Scala gRPC service."""
    name: str
    methods: List[str] = field(default_factory=list)
    proto_file: Optional[str] = None
    framework: str = "scalapb"  # scalapb, fs2_grpc, zio_grpc, akka_grpc
    file: str = ""
    line_number: int = 0


@dataclass
class ScalaGraphQLInfo:
    """Information about a Scala GraphQL type/mutation/query."""
    name: str
    kind: str = "type"  # type, mutation, query, subscription, input, enum, interface
    fields: List[str] = field(default_factory=list)
    framework: str = "caliban"  # caliban, sangria
    file: str = ""
    line_number: int = 0


class ScalaAPIExtractor:
    """
    Extracts Scala API definitions from source code.

    Handles:
    - Play Framework routes file and controller actions
    - Akka HTTP route directives (path, get, post, complete, concat)
    - http4s routes DSL (HttpRoutes.of, dsl.io)
    - Tapir endpoint definitions
    - Finch endpoint definitions
    - Scalatra route handlers
    - ZIO HTTP routes
    - Cask annotated routes
    - ScalaPB / fs2-grpc / zio-grpc / akka-grpc services
    - Caliban / Sangria GraphQL schemas
    """

    # ── Play Framework ──────────────────────────────────────────
    # Play routes file: GET /path controllers.HomeController.index()
    PLAY_ROUTE_PATTERN = re.compile(
        r'^\s*(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+'
        r'(?P<path>/[^\s]*)\s+'
        r'(?P<handler>[^\s(]+(?:\([^)]*\))?)',
        re.MULTILINE
    )

    # Play controller action
    PLAY_ACTION_PATTERN = re.compile(
        r'def\s+(?P<name>\w+)(?:\s*\([^)]*\))?\s*=\s*(?P<action>Action(?:\.async)?|TODO)',
        re.MULTILINE
    )

    # Play controller class
    PLAY_CONTROLLER_PATTERN = re.compile(
        r'class\s+(?P<name>\w+Controller)\s*(?:@Inject\(\)\s*)?\('
        r'(?P<deps>[^)]*)\)\s+extends\s+(?P<parent>\w+)',
        re.MULTILINE
    )

    # ── Akka HTTP ───────────────────────────────────────────────
    AKKA_DIRECTIVE_PATTERN = re.compile(
        r'(?P<method>get|post|put|patch|delete|head|options)\s*\{',
        re.MULTILINE
    )

    AKKA_PATH_PATTERN = re.compile(
        r'path(?:Prefix)?\s*\(\s*["\'](?P<path>[^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    # ── http4s ──────────────────────────────────────────────────
    HTTP4S_ROUTE_PATTERN = re.compile(
        r'case\s+(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s*->\s*'
        r'Root\s*(?:/\s*(?P<path>[^\s=]+))?',
        re.MULTILINE
    )

    HTTP4S_HTTPROUTES_PATTERN = re.compile(
        r'HttpRoutes\.of\[',
        re.MULTILINE
    )

    # ── Tapir ───────────────────────────────────────────────────
    TAPIR_ENDPOINT_PATTERN = re.compile(
        r'(?:val|def)\s+(?P<name>\w+)\s*[=:][^=]*?endpoint\s*\.'
        r'(?P<method>get|post|put|patch|delete|head|options)?',
        re.MULTILINE | re.DOTALL
    )

    TAPIR_IN_PATTERN = re.compile(
        r'\.in\(\s*["\'](?P<path>[^"\']+)["\']\s*\)',
    )

    # ── Finch ───────────────────────────────────────────────────
    FINCH_ENDPOINT_PATTERN = re.compile(
        r'(?P<method>get|post|put|patch|delete)\s*\(\s*(?P<path>[^)]+)\)',
        re.MULTILINE
    )

    # ── Scalatra ────────────────────────────────────────────────
    SCALATRA_ROUTE_PATTERN = re.compile(
        r'(?P<method>get|post|put|patch|delete)\s*\(\s*["\'](?P<path>[^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    # ── ZIO HTTP ────────────────────────────────────────────────
    ZIO_ROUTE_PATTERN = re.compile(
        r'Method\.(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s*/\s*'
        r'(?P<path>[^\s\->]+)',
        re.MULTILINE
    )

    # ── Cask ────────────────────────────────────────────────────
    CASK_ROUTE_PATTERN = re.compile(
        r'@cask\.(?P<method>get|post|put|delete|patch|websocket)\s*'
        r'(?:\(\s*["\'](?P<path>[^"\']+)["\']\s*\))?',
        re.MULTILINE
    )

    # ── gRPC ────────────────────────────────────────────────────
    GRPC_SERVICE_PATTERN = re.compile(
        r'(?:trait|abstract\s+class|class)\s+(?P<name>\w+(?:Grpc|Service|Fs2Grpc|ZioGrpc))',
        re.MULTILINE
    )

    GRPC_METHOD_PATTERN = re.compile(
        r'(?:override\s+)?def\s+(?P<name>\w+)\s*\([^)]*\)\s*:\s*'
        r'(?:Future|IO|Task|ZIO|Stream|F)\[',
        re.MULTILINE
    )

    # ── GraphQL ─────────────────────────────────────────────────
    # Caliban
    CALIBAN_TYPE_PATTERN = re.compile(
        r'case\s+class\s+(?P<name>(?:Queries|Mutations|Subscriptions)\w*)',
        re.MULTILINE
    )

    # Sangria
    SANGRIA_TYPE_PATTERN = re.compile(
        r'(?:ObjectType|InputObjectType|EnumType|InterfaceType|UnionType)\s*\(\s*["\'](?P<name>[^"\']+)["\']',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Scala API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all API definitions from Scala source code.

        Args:
            content: Scala source code
            file_path: Path to the source file

        Returns:
            Dictionary with keys: routes, controllers, grpc_services, graphql_types
        """
        result = {
            'routes': [],
            'controllers': [],
            'grpc_services': [],
            'graphql_types': [],
        }

        # Detect framework
        is_routes_file = file_path.endswith('/routes') or file_path.endswith('routes.conf')

        if is_routes_file:
            result['routes'].extend(self._extract_play_routes_file(content, file_path))
        else:
            result['routes'].extend(self._extract_play_controller_routes(content, file_path))
            result['routes'].extend(self._extract_akka_routes(content, file_path))
            result['routes'].extend(self._extract_http4s_routes(content, file_path))
            result['routes'].extend(self._extract_tapir_endpoints(content, file_path))
            result['routes'].extend(self._extract_finch_endpoints(content, file_path))
            result['routes'].extend(self._extract_scalatra_routes(content, file_path))
            result['routes'].extend(self._extract_zio_routes(content, file_path))
            result['routes'].extend(self._extract_cask_routes(content, file_path))

        result['controllers'] = self._extract_controllers(content, file_path)
        result['grpc_services'] = self._extract_grpc_services(content, file_path)
        result['graphql_types'] = self._extract_graphql_types(content, file_path)

        return result

    def _extract_play_routes_file(self, content: str, file_path: str) -> List[ScalaRouteInfo]:
        """Extract routes from Play Framework routes file."""
        routes = []
        for match in self.PLAY_ROUTE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            path = match.group('path')
            handler = match.group('handler')

            # Extract path params
            path_params = re.findall(r':(\w+)|\$(\w+)', path)
            path_params = [p[0] or p[1] for p in path_params]

            route = ScalaRouteInfo(
                method=match.group('method'),
                path=path,
                handler=handler,
                framework='play',
                file=file_path,
                line_number=line_number,
                path_params=path_params,
            )
            routes.append(route)
        return routes

    def _extract_play_controller_routes(self, content: str, file_path: str) -> List[ScalaRouteInfo]:
        """Extract action methods from Play controllers."""
        routes = []
        for match in self.PLAY_ACTION_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            action_type = match.group('action')

            route = ScalaRouteInfo(
                method='ANY',
                path=f'/{name}',
                handler=name,
                framework='play',
                file=file_path,
                line_number=line_number,
            )
            routes.append(route)
        return routes

    def _extract_akka_routes(self, content: str, file_path: str) -> List[ScalaRouteInfo]:
        """Extract Akka HTTP route directives."""
        routes = []
        if 'akka.http' not in content and 'AkkaHttp' not in content and 'akkaHttp' not in content:
            return routes

        # Gather path contexts
        paths = {}
        for pm in self.AKKA_PATH_PATTERN.finditer(content):
            line = content[:pm.start()].count('\n') + 1
            paths[line] = pm.group('path')

        for match in self.AKKA_DIRECTIVE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            method = match.group('method').upper()

            # Find nearest path above this line
            nearest_path = '/'
            for pline, ppath in sorted(paths.items()):
                if pline <= line_number:
                    nearest_path = f'/{ppath}'
                else:
                    break

            route = ScalaRouteInfo(
                method=method,
                path=nearest_path,
                framework='akka_http',
                file=file_path,
                line_number=line_number,
            )
            routes.append(route)
        return routes

    def _extract_http4s_routes(self, content: str, file_path: str) -> List[ScalaRouteInfo]:
        """Extract http4s routes."""
        routes = []
        if 'http4s' not in content and 'HttpRoutes' not in content and 'dsl.io' not in content:
            return routes

        for match in self.HTTP4S_ROUTE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            method = match.group('method')
            path_parts = match.group('path') or ''

            # Build path from segments
            path = '/' + path_parts.replace(' / ', '/').strip() if path_parts else '/'
            path_params = re.findall(r'(\w+Var)', path)

            route = ScalaRouteInfo(
                method=method,
                path=path,
                framework='http4s',
                file=file_path,
                line_number=line_number,
                path_params=path_params,
            )
            routes.append(route)
        return routes

    def _extract_tapir_endpoints(self, content: str, file_path: str) -> List[ScalaRouteInfo]:
        """Extract Tapir endpoint definitions."""
        routes = []
        if 'tapir' not in content and 'endpoint' not in content:
            return routes

        for match in self.TAPIR_ENDPOINT_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            method = (match.group('method') or 'GET').upper()

            # Try to find .in("path")
            path = '/'
            context = content[match.start():match.start() + 500]
            in_match = self.TAPIR_IN_PATTERN.search(context)
            if in_match:
                path = '/' + in_match.group('path')

            route = ScalaRouteInfo(
                method=method,
                path=path,
                handler=name,
                framework='tapir',
                file=file_path,
                line_number=line_number,
            )
            routes.append(route)
        return routes

    def _extract_finch_endpoints(self, content: str, file_path: str) -> List[ScalaRouteInfo]:
        """Extract Finch endpoint definitions."""
        routes = []
        if 'finch' not in content and 'Endpoint' not in content:
            return routes

        for match in self.FINCH_ENDPOINT_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            route = ScalaRouteInfo(
                method=match.group('method').upper(),
                path=match.group('path').strip().strip('"\''),
                framework='finch',
                file=file_path,
                line_number=line_number,
            )
            routes.append(route)
        return routes

    def _extract_scalatra_routes(self, content: str, file_path: str) -> List[ScalaRouteInfo]:
        """Extract Scalatra route definitions."""
        routes = []
        if 'Scalatra' not in content and 'ScalatraServlet' not in content:
            return routes

        for match in self.SCALATRA_ROUTE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            path = match.group('path')
            path_params = re.findall(r':(\w+)', path)

            route = ScalaRouteInfo(
                method=match.group('method').upper(),
                path=path,
                framework='scalatra',
                file=file_path,
                line_number=line_number,
                path_params=path_params,
            )
            routes.append(route)
        return routes

    def _extract_zio_routes(self, content: str, file_path: str) -> List[ScalaRouteInfo]:
        """Extract ZIO HTTP route definitions."""
        routes = []
        if 'zio' not in content.lower() and 'Routes' not in content:
            return routes

        for match in self.ZIO_ROUTE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            path_raw = match.group('path').strip()
            path = '/' + path_raw.replace(' / ', '/').lstrip('/')

            route = ScalaRouteInfo(
                method=match.group('method'),
                path=path,
                framework='zio_http',
                file=file_path,
                line_number=line_number,
            )
            routes.append(route)
        return routes

    def _extract_cask_routes(self, content: str, file_path: str) -> List[ScalaRouteInfo]:
        """Extract Cask annotated routes."""
        routes = []
        for match in self.CASK_ROUTE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            method = match.group('method').upper()
            if method == 'WEBSOCKET':
                method = 'WS'
            path = match.group('path') or '/'

            route = ScalaRouteInfo(
                method=method,
                path=path,
                framework='cask',
                file=file_path,
                line_number=line_number,
            )
            routes.append(route)
        return routes

    def _extract_controllers(self, content: str, file_path: str) -> List[ScalaControllerInfo]:
        """Extract controller class definitions."""
        controllers = []

        for match in self.PLAY_CONTROLLER_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            parent = match.group('parent')
            deps_raw = match.group('deps') or ''

            # Parse injected dependencies
            injected = []
            for dep in deps_raw.split(','):
                dep = dep.strip()
                if ':' in dep:
                    dep_name = dep.split(':')[0].strip()
                    dep_name = re.sub(r'\b(val|var|implicit|private)\b\s*', '', dep_name).strip()
                    if dep_name:
                        injected.append(dep_name)

            # Find actions in the controller body
            actions = []
            for action_match in self.PLAY_ACTION_PATTERN.finditer(content[match.start():]):
                actions.append(action_match.group('name'))

            controller = ScalaControllerInfo(
                name=name,
                actions=actions[:20],  # Limit
                framework='play',
                parent_class=parent,
                injected_services=injected,
                file=file_path,
                line_number=line_number,
            )
            controllers.append(controller)

        # Generic controller pattern (Akka HTTP, http4s)
        controller_pattern = re.compile(
            r'(?:class|object)\s+(?P<name>\w+(?:Routes?|Controller|Endpoint|Api))\s*'
            r'(?:extends\s+(?P<parent>\w+))?',
            re.MULTILINE
        )
        for match in controller_pattern.finditer(content):
            name = match.group('name')
            # Skip if already found as Play controller
            if any(c.name == name for c in controllers):
                continue

            line_number = content[:match.start()].count('\n') + 1
            parent = match.group('parent')

            # Detect framework
            fw = 'play'
            if 'akka' in content.lower():
                fw = 'akka_http'
            elif 'http4s' in content.lower() or 'HttpRoutes' in content:
                fw = 'http4s'
            elif 'tapir' in content.lower():
                fw = 'tapir'

            controller = ScalaControllerInfo(
                name=name,
                framework=fw,
                parent_class=parent,
                file=file_path,
                line_number=line_number,
            )
            controllers.append(controller)

        return controllers

    def _extract_grpc_services(self, content: str, file_path: str) -> List[ScalaGRPCServiceInfo]:
        """Extract gRPC service definitions."""
        services = []
        for match in self.GRPC_SERVICE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')

            # Detect framework
            fw = 'scalapb'
            if 'fs2' in content.lower():
                fw = 'fs2_grpc'
            elif 'zio' in content.lower():
                fw = 'zio_grpc'
            elif 'akka' in content.lower():
                fw = 'akka_grpc'

            # Find methods
            methods = []
            body = content[match.end():match.end() + 2000]
            for m in self.GRPC_METHOD_PATTERN.finditer(body):
                methods.append(m.group('name'))

            service = ScalaGRPCServiceInfo(
                name=name,
                methods=methods[:20],
                framework=fw,
                file=file_path,
                line_number=line_number,
            )
            services.append(service)
        return services

    def _extract_graphql_types(self, content: str, file_path: str) -> List[ScalaGraphQLInfo]:
        """Extract GraphQL type definitions."""
        types = []

        # Caliban
        for match in self.CALIBAN_TYPE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            kind = 'query'
            if 'Mutation' in name:
                kind = 'mutation'
            elif 'Subscription' in name:
                kind = 'subscription'

            gql = ScalaGraphQLInfo(
                name=name,
                kind=kind,
                framework='caliban',
                file=file_path,
                line_number=line_number,
            )
            types.append(gql)

        # Sangria
        for match in self.SANGRIA_TYPE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')

            # Detect kind from the type constructor
            context = content[max(0, match.start() - 20):match.start()]
            kind = 'type'
            if 'InputObject' in context:
                kind = 'input'
            elif 'EnumType' in context:
                kind = 'enum'
            elif 'InterfaceType' in context:
                kind = 'interface'
            elif 'UnionType' in context:
                kind = 'union'

            gql = ScalaGraphQLInfo(
                name=name,
                kind=kind,
                framework='sangria',
                file=file_path,
                line_number=line_number,
            )
            types.append(gql)

        return types
