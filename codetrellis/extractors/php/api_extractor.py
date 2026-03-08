"""
PhpAPIExtractor - Extracts PHP API routes, controllers, middleware, gRPC, and GraphQL.

This extractor parses PHP source code and extracts:
- Laravel routes (Route::get, Route::post, resource routes, API routes)
- Symfony routes (#[Route] attribute, annotations, YAML-style)
- Slim Framework routes ($app->get, $app->post)
- Lumen routes ($router->get, $router->post)
- CakePHP routes ($routes->connect)
- CodeIgniter routes ($routes->get)
- Laminas/Zend routes
- Laravel controllers with methods
- Middleware definitions and usage
- gRPC service definitions
- GraphQL type/query/mutation definitions (Lighthouse, webonyx/graphql-php)
- RESTful resource controllers

Supports PHP 5.x through PHP 8.3+ features (attributes, named arguments).

Part of CodeTrellis v4.24 - PHP Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PhpRouteInfo:
    """Information about a PHP route definition."""
    method: str  # GET, POST, PUT, DELETE, PATCH, ANY, etc.
    path: str
    handler: str  # Controller@method or closure
    name: Optional[str] = None
    middleware: List[str] = field(default_factory=list)
    prefix: Optional[str] = None
    framework: str = "laravel"
    file: str = ""
    line_number: int = 0


@dataclass
class PhpControllerInfo:
    """Information about a PHP controller."""
    name: str
    parent_class: Optional[str] = None
    actions: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    prefix: Optional[str] = None
    is_resource: bool = False
    is_api: bool = False
    framework: str = "laravel"
    file: str = ""
    line_number: int = 0


@dataclass
class PhpMiddlewareInfo:
    """Information about PHP middleware."""
    name: str
    kind: str = "middleware"  # middleware, guard, filter
    handler: Optional[str] = None
    framework: str = "laravel"
    file: str = ""
    line_number: int = 0


@dataclass
class PhpGRPCServiceInfo:
    """Information about a PHP gRPC service."""
    name: str
    methods: List[str] = field(default_factory=list)
    proto_file: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class PhpGraphQLInfo:
    """Information about a PHP GraphQL type/query/mutation."""
    name: str
    kind: str = "type"  # type, query, mutation, subscription, input, enum
    fields: List[str] = field(default_factory=list)
    framework: str = "lighthouse"  # lighthouse, webonyx, graphql-php
    file: str = ""
    line_number: int = 0


class PhpAPIExtractor:
    """
    Extracts PHP API routes, controllers, middleware, gRPC, and GraphQL definitions.

    Supports:
    - Laravel: Route::get/post/put/delete/patch/any/match/resource/apiResource
    - Symfony: #[Route] attributes, @Route annotations
    - Slim: $app->get/post/put/delete/patch/any/map/group
    - Lumen: $router->get/post/put/delete/patch
    - CakePHP: $routes->connect, $routes->scope
    - CodeIgniter: $routes->get/post/put/delete
    - Laravel controllers extending Controller
    - Middleware class detection and usage
    - gRPC service stubs
    - GraphQL: Lighthouse directives, webonyx type definitions

    v4.24: Comprehensive PHP API extraction.
    """

    # Laravel route patterns
    LARAVEL_ROUTE_PATTERN = re.compile(
        r'''Route::(?P<method>get|post|put|patch|delete|any|match|options)\s*\(\s*'''
        r'''['"](?P<path>[^'"]+)['"]\s*,\s*'''
        r'''(?:'''
        r'''(?:\[(?P<controller>[A-Za-z_\\]+)::class\s*,\s*'(?P<action>\w+)'\])|'''
        r'''(?:['"](?P<handler>[^'"]+)['"]))''',
        re.MULTILINE
    )

    # Laravel resource/apiResource routes
    LARAVEL_RESOURCE_PATTERN = re.compile(
        r'''Route::(?P<type>resource|apiResource)\s*\(\s*['"](?P<path>[^'"]+)['"]\s*,\s*'''
        r'''(?:(?P<controller>[A-Za-z_\\]+)::class|['"](?P<handler>[^'"]+)['"])''',
        re.MULTILINE
    )

    # Laravel route group
    LARAVEL_GROUP_PATTERN = re.compile(
        r'''Route::(?:prefix|group)\s*\(\s*['"](?P<prefix>[^'"]+)['"]''',
        re.MULTILINE
    )

    # Laravel middleware usage
    LARAVEL_MIDDLEWARE_PATTERN = re.compile(
        r'''->middleware\s*\(\s*(?:\[(?P<list>[^\]]+)\]|['"](?P<single>[^'"]+)['"])''',
        re.MULTILINE
    )

    # Laravel named routes
    LARAVEL_NAME_PATTERN = re.compile(
        r'''->name\s*\(\s*['"](?P<name>[^'"]+)['"]''',
        re.MULTILINE
    )

    # Symfony #[Route] attribute (PHP 8.0+)
    SYMFONY_ROUTE_ATTR_PATTERN = re.compile(
        r'''#\[Route\s*\(\s*['"](?P<path>[^'"]+)['"]'''
        r'''(?:\s*,\s*(?:name:\s*)?['"](?P<name>[^'"]+)['"])?'''
        r'''(?:\s*,\s*methods?:\s*(?:\[(?P<methods>[^\]]+)\]|['"](?P<method>[^'"]+)['"]))?''',
        re.MULTILINE
    )

    # Symfony @Route annotation
    SYMFONY_ROUTE_ANNOT_PATTERN = re.compile(
        r'''@Route\s*\(\s*['"](?P<path>[^'"]+)['"]'''
        r'''(?:\s*,\s*name\s*=\s*['"](?P<name>[^'"]+)['"])?'''
        r'''(?:\s*,\s*methods?\s*=\s*(?:\{(?P<methods>[^}]+)\}|['"](?P<method>[^'"]+)['"]))?''',
        re.MULTILINE
    )

    # Slim Framework routes
    SLIM_ROUTE_PATTERN = re.compile(
        r'''\$(?:app|group)\s*->\s*(?P<method>get|post|put|patch|delete|any|map|options)\s*\(\s*'''
        r'''['"](?P<path>[^'"]+)['"]''',
        re.MULTILINE
    )

    # Lumen routes
    LUMEN_ROUTE_PATTERN = re.compile(
        r'''\$(?:router|app)\s*->\s*(?P<method>get|post|put|patch|delete)\s*\(\s*'''
        r'''['"](?P<path>[^'"]+)['"]\s*,\s*'''
        r'''(?:'''
        r'''(?:\[(?:['"]uses['"]\s*=>\s*)?['"](?P<handler>[^'"]+)['"])|'''
        r'''['"](?P<handler2>[^'"]+)['"])''',
        re.MULTILINE
    )

    # CakePHP routes
    CAKEPHP_ROUTE_PATTERN = re.compile(
        r'''\$routes\s*->\s*connect\s*\(\s*['"](?P<path>[^'"]+)['"]''',
        re.MULTILINE
    )

    # CodeIgniter routes
    CODEIGNITER_ROUTE_PATTERN = re.compile(
        r'''\$routes\s*->\s*(?P<method>get|post|put|patch|delete|cli)\s*\(\s*'''
        r'''['"](?P<path>[^'"]+)['"]\s*,\s*['"](?P<handler>[^'"]+)['"]''',
        re.MULTILINE
    )

    # Controller class pattern (extends Controller, BaseController, etc.)
    CONTROLLER_PATTERN = re.compile(
        r'class\s+(?P<name>\w+Controller)\s+extends\s+(?P<parent>[A-Za-z_\\]+)',
        re.MULTILINE
    )

    # Middleware class pattern
    MIDDLEWARE_CLASS_PATTERN = re.compile(
        r'class\s+(?P<name>\w+(?:Middleware|Guard|Filter))\s',
        re.MULTILINE
    )

    # Middleware handle method
    MIDDLEWARE_HANDLE_PATTERN = re.compile(
        r'function\s+handle\s*\(',
        re.MULTILINE
    )

    # gRPC service class (extends generated stub)
    GRPC_SERVICE_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s+extends\s+(?P<parent>\w+(?:ServiceClient|Grpc|GrpcClient))',
        re.MULTILINE
    )

    # GraphQL type (Lighthouse)
    GRAPHQL_LIGHTHOUSE_PATTERN = re.compile(
        r'''#\[(?:GraphQLType|GraphQLQuery|GraphQLMutation|GraphQLSubscription)\s*'''
        r'''(?:\(\s*name:\s*['"](?P<name>[^'"]+)['"]\s*\))?''',
        re.MULTILINE
    )

    # GraphQL webonyx patterns
    GRAPHQL_WEBONYX_PATTERN = re.compile(
        r'new\s+ObjectType\s*\(\s*\[.*?[\'"]name[\'"]\s*=>\s*[\'"](?P<name>[^\'"]*)[\'"]\s*',
        re.DOTALL
    )

    def __init__(self):
        """Initialize the API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all PHP API patterns from source code.

        Args:
            content: PHP source code content
            file_path: Path to source file

        Returns:
            Dict with 'routes', 'controllers', 'middleware', 'grpc_services', 'graphql' keys
        """
        routes = []
        controllers = []
        middleware = []
        grpc_services = []
        graphql = []

        # Laravel routes
        routes.extend(self._extract_laravel_routes(content, file_path))

        # Symfony routes
        routes.extend(self._extract_symfony_routes(content, file_path))

        # Slim routes
        routes.extend(self._extract_slim_routes(content, file_path))

        # Lumen routes
        routes.extend(self._extract_lumen_routes(content, file_path))

        # CakePHP routes
        routes.extend(self._extract_cakephp_routes(content, file_path))

        # CodeIgniter routes
        routes.extend(self._extract_codeigniter_routes(content, file_path))

        # Controllers
        controllers.extend(self._extract_controllers(content, file_path))

        # Middleware
        middleware.extend(self._extract_middleware(content, file_path))

        # gRPC
        grpc_services.extend(self._extract_grpc(content, file_path))

        # GraphQL
        graphql.extend(self._extract_graphql(content, file_path))

        return {
            'routes': routes,
            'controllers': controllers,
            'middleware': middleware,
            'grpc_services': grpc_services,
            'graphql': graphql,
        }

    def _extract_laravel_routes(self, content: str, file_path: str) -> List[PhpRouteInfo]:
        """Extract Laravel route definitions."""
        routes = []

        # Standard routes
        for match in self.LARAVEL_ROUTE_PATTERN.finditer(content):
            method = match.group('method').upper()
            path = match.group('path')
            controller = match.group('controller')
            action = match.group('action')
            handler_str = match.group('handler')

            if controller and action:
                handler = f"{controller}@{action}"
            elif handler_str:
                handler = handler_str
            else:
                handler = "closure"

            line_number = content[:match.start()].count('\n') + 1

            route = PhpRouteInfo(
                method=method,
                path=path,
                handler=handler,
                framework="laravel",
                file=file_path,
                line_number=line_number,
            )

            # Check for middleware on same line or nearby
            line_end = content.find('\n', match.end())
            if line_end == -1:
                line_end = len(content)
            line_context = content[match.start():min(line_end + 200, len(content))]
            mw_match = self.LARAVEL_MIDDLEWARE_PATTERN.search(line_context)
            if mw_match:
                mw_list = mw_match.group('list') or mw_match.group('single') or ''
                route.middleware = [m.strip().strip("'\"") for m in mw_list.split(',') if m.strip()]

            name_match = self.LARAVEL_NAME_PATTERN.search(line_context)
            if name_match:
                route.name = name_match.group('name')

            routes.append(route)

        # Resource routes
        for match in self.LARAVEL_RESOURCE_PATTERN.finditer(content):
            path = match.group('path')
            controller = match.group('controller') or match.group('handler')
            route_type = match.group('type')
            line_number = content[:match.start()].count('\n') + 1

            resource_methods = ['index', 'create', 'store', 'show', 'edit', 'update', 'destroy']
            if route_type == 'apiResource':
                resource_methods = ['index', 'store', 'show', 'update', 'destroy']

            for method_name in resource_methods:
                http_method = {
                    'index': 'GET', 'create': 'GET', 'store': 'POST',
                    'show': 'GET', 'edit': 'GET', 'update': 'PUT',
                    'destroy': 'DELETE',
                }[method_name]

                routes.append(PhpRouteInfo(
                    method=http_method,
                    path=f"{path}/{method_name}" if method_name not in ('index', 'store') else path,
                    handler=f"{controller}@{method_name}",
                    framework="laravel",
                    file=file_path,
                    line_number=line_number,
                ))

        return routes

    def _extract_symfony_routes(self, content: str, file_path: str) -> List[PhpRouteInfo]:
        """Extract Symfony route definitions."""
        routes = []

        # PHP 8 attributes
        for match in self.SYMFONY_ROUTE_ATTR_PATTERN.finditer(content):
            path = match.group('path')
            name = match.group('name')
            methods_str = match.group('methods') or match.group('method')
            line_number = content[:match.start()].count('\n') + 1

            methods = ['GET']
            if methods_str:
                methods = [m.strip().strip("'\"") for m in methods_str.split(',') if m.strip()]

            # Find the method name that follows this attribute
            method_match = re.search(
                r'(?:public|protected)\s+function\s+(\w+)',
                content[match.end():match.end() + 200]
            )
            handler = method_match.group(1) if method_match else ''

            for method in methods:
                routes.append(PhpRouteInfo(
                    method=method.upper(),
                    path=path,
                    handler=handler,
                    name=name,
                    framework="symfony",
                    file=file_path,
                    line_number=line_number,
                ))

        # Annotations
        for match in self.SYMFONY_ROUTE_ANNOT_PATTERN.finditer(content):
            path = match.group('path')
            name = match.group('name')
            methods_str = match.group('methods') or match.group('method')
            line_number = content[:match.start()].count('\n') + 1

            methods = ['GET']
            if methods_str:
                methods = [m.strip().strip("'\"") for m in methods_str.split(',') if m.strip()]

            method_match = re.search(
                r'(?:public|protected)\s+function\s+(\w+)',
                content[match.end():match.end() + 200]
            )
            handler = method_match.group(1) if method_match else ''

            for method in methods:
                routes.append(PhpRouteInfo(
                    method=method.upper(),
                    path=path,
                    handler=handler,
                    name=name,
                    framework="symfony",
                    file=file_path,
                    line_number=line_number,
                ))

        return routes

    def _extract_slim_routes(self, content: str, file_path: str) -> List[PhpRouteInfo]:
        """Extract Slim Framework route definitions."""
        routes = []
        for match in self.SLIM_ROUTE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            routes.append(PhpRouteInfo(
                method=match.group('method').upper(),
                path=match.group('path'),
                handler="closure",
                framework="slim",
                file=file_path,
                line_number=line_number,
            ))
        return routes

    def _extract_lumen_routes(self, content: str, file_path: str) -> List[PhpRouteInfo]:
        """Extract Lumen route definitions."""
        routes = []
        for match in self.LUMEN_ROUTE_PATTERN.finditer(content):
            handler = match.group('handler') or match.group('handler2') or 'closure'
            line_number = content[:match.start()].count('\n') + 1
            routes.append(PhpRouteInfo(
                method=match.group('method').upper(),
                path=match.group('path'),
                handler=handler,
                framework="lumen",
                file=file_path,
                line_number=line_number,
            ))
        return routes

    def _extract_cakephp_routes(self, content: str, file_path: str) -> List[PhpRouteInfo]:
        """Extract CakePHP route definitions."""
        routes = []
        for match in self.CAKEPHP_ROUTE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            routes.append(PhpRouteInfo(
                method="GET",
                path=match.group('path'),
                handler="",
                framework="cakephp",
                file=file_path,
                line_number=line_number,
            ))
        return routes

    def _extract_codeigniter_routes(self, content: str, file_path: str) -> List[PhpRouteInfo]:
        """Extract CodeIgniter route definitions."""
        routes = []
        for match in self.CODEIGNITER_ROUTE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            routes.append(PhpRouteInfo(
                method=match.group('method').upper(),
                path=match.group('path'),
                handler=match.group('handler'),
                framework="codeigniter",
                file=file_path,
                line_number=line_number,
            ))
        return routes

    def _extract_controllers(self, content: str, file_path: str) -> List[PhpControllerInfo]:
        """Extract controller class definitions."""
        controllers = []

        for match in self.CONTROLLER_PATTERN.finditer(content):
            name = match.group('name')
            parent = match.group('parent')
            line_number = content[:match.start()].count('\n') + 1

            # Detect framework
            framework = "laravel"
            if 'Symfony' in parent or 'AbstractController' in parent:
                framework = "symfony"
            elif 'BaseController' in parent and 'CodeIgniter' in content:
                framework = "codeigniter"
            elif 'AppController' in parent and 'Cake' in content:
                framework = "cakephp"

            # Extract actions (public methods)
            actions = []
            body_start = content.find('{', match.end())
            if body_start != -1:
                method_pattern = re.compile(
                    r'public\s+function\s+(?P<name>\w+)\s*\(',
                    re.MULTILINE
                )
                body_content = content[body_start:]
                for method_match in method_pattern.finditer(body_content):
                    method_name = method_match.group('name')
                    if not method_name.startswith('__'):
                        actions.append(method_name)

            # Extract middleware from constructor
            middleware = []
            ctor_match = re.search(
                r'function\s+__construct.*?middleware\s*\(\s*[\'"](\w+)[\'"]\s*\)',
                content[match.start():match.start() + 2000],
                re.DOTALL
            )
            if ctor_match:
                middleware.append(ctor_match.group(1))

            controllers.append(PhpControllerInfo(
                name=name,
                parent_class=parent,
                actions=actions[:30],
                middleware=middleware,
                framework=framework,
                file=file_path,
                line_number=line_number,
            ))

        return controllers

    def _extract_middleware(self, content: str, file_path: str) -> List[PhpMiddlewareInfo]:
        """Extract middleware class definitions."""
        middleware = []

        for match in self.MIDDLEWARE_CLASS_PATTERN.finditer(content):
            name = match.group('name')
            line_number = content[:match.start()].count('\n') + 1

            # Verify it has a handle method
            if self.MIDDLEWARE_HANDLE_PATTERN.search(content[match.end():match.end() + 2000]):
                middleware.append(PhpMiddlewareInfo(
                    name=name,
                    kind="middleware",
                    framework="laravel",
                    file=file_path,
                    line_number=line_number,
                ))

        return middleware

    def _extract_grpc(self, content: str, file_path: str) -> List[PhpGRPCServiceInfo]:
        """Extract gRPC service definitions."""
        services = []

        for match in self.GRPC_SERVICE_PATTERN.finditer(content):
            name = match.group('name')
            line_number = content[:match.start()].count('\n') + 1

            # Extract methods
            methods = []
            body_start = content.find('{', match.end())
            if body_start != -1:
                method_pattern = re.compile(r'public\s+function\s+(\w+)\s*\(')
                for method_match in method_pattern.finditer(content[body_start:body_start + 5000]):
                    methods.append(method_match.group(1))

            services.append(PhpGRPCServiceInfo(
                name=name,
                methods=methods[:20],
                file=file_path,
                line_number=line_number,
            ))

        return services

    def _extract_graphql(self, content: str, file_path: str) -> List[PhpGraphQLInfo]:
        """Extract GraphQL type definitions."""
        graphql = []

        # Lighthouse attributes
        for match in self.GRAPHQL_LIGHTHOUSE_PATTERN.finditer(content):
            name = match.group('name') or ''
            line_number = content[:match.start()].count('\n') + 1

            # Determine kind from attribute name
            attr_text = content[match.start():match.end()]
            if 'Query' in attr_text:
                kind = 'query'
            elif 'Mutation' in attr_text:
                kind = 'mutation'
            elif 'Subscription' in attr_text:
                kind = 'subscription'
            else:
                kind = 'type'

            graphql.append(PhpGraphQLInfo(
                name=name,
                kind=kind,
                framework="lighthouse",
                file=file_path,
                line_number=line_number,
            ))

        # webonyx/graphql-php
        for match in self.GRAPHQL_WEBONYX_PATTERN.finditer(content):
            name = match.group('name')
            line_number = content[:match.start()].count('\n') + 1

            graphql.append(PhpGraphQLInfo(
                name=name,
                kind='type',
                framework="webonyx",
                file=file_path,
                line_number=line_number,
            ))

        return graphql
