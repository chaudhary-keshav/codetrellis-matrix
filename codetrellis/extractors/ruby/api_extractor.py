"""
RubyAPIExtractor - Extracts Ruby API endpoints, routes, and controllers.

This extractor parses Ruby source code and extracts:
- Rails routes (config/routes.rb DSL: get, post, resources, namespace, scope)
- Sinatra DSL (get, post, put, delete, patch)
- Grape API endpoints (desc, params, get, post, etc.)
- Hanami routes and actions
- Rails controllers (actions, filters, concerns)
- gRPC services (grpc gem)
- GraphQL types/mutations/queries (graphql-ruby)
- ActionCable channels (WebSocket)
- Rack middleware
- Roda routes

Supports Rails 4.x through Rails 8.x, Sinatra, Grape, Hanami, Roda.

Part of CodeTrellis v4.23 - Ruby Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RubyRouteInfo:
    """Information about a Ruby HTTP route."""
    method: str  # GET, POST, PUT, DELETE, PATCH, ANY
    path: str
    handler: str = ""  # controller#action or block
    framework: str = "rails"  # rails, sinatra, grape, hanami, roda
    file: str = ""
    line_number: int = 0
    namespace: Optional[str] = None
    constraints: Optional[str] = None
    is_api: bool = False
    middleware: List[str] = field(default_factory=list)


@dataclass
class RubyControllerInfo:
    """Information about a Rails/Hanami controller."""
    name: str
    actions: List[str] = field(default_factory=list)
    before_actions: List[str] = field(default_factory=list)
    after_actions: List[str] = field(default_factory=list)
    around_actions: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    parent_class: Optional[str] = None
    file: str = ""
    line_number: int = 0
    is_api: bool = False  # ApplicationController vs ApiController


@dataclass
class RubyGRPCServiceInfo:
    """Information about a Ruby gRPC service."""
    name: str
    methods: List[str] = field(default_factory=list)
    proto_file: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class RubyGraphQLInfo:
    """Information about a Ruby GraphQL type/mutation/query."""
    name: str
    kind: str = "type"  # type, mutation, query, input, enum, interface, union, subscription
    fields: List[str] = field(default_factory=list)
    arguments: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class RubyAPIExtractor:
    """
    Extracts Ruby API definitions from source code.

    Handles:
    - Rails routes DSL (resources, member, collection, namespace, scope)
    - Rails controller actions and filters
    - Sinatra DSL routes
    - Grape API endpoints with versioning
    - Hanami routes and actions
    - Roda routes
    - gRPC service definitions
    - GraphQL type definitions (graphql-ruby gem)
    - ActionCable channels
    - Rack middleware
    """

    # Rails routes DSL patterns
    RAILS_ROUTE_PATTERN = re.compile(
        r'^\s*(?P<method>get|post|put|patch|delete|match)\s+[\'"](?P<path>[^\'"]+)[\'"](?:.*?to:\s*[\'"](?P<handler>[^\'"]+)[\'"])?',
        re.MULTILINE
    )

    # Rails resources/resource
    RAILS_RESOURCES_PATTERN = re.compile(
        r'^\s*(?P<kind>resources|resource)\s+:(?P<name>\w+)',
        re.MULTILINE
    )

    # Rails namespace/scope
    RAILS_NAMESPACE_PATTERN = re.compile(
        r'^\s*(?P<kind>namespace|scope)\s+[:\'](?P<name>\w+)',
        re.MULTILINE
    )

    # Rails root route
    RAILS_ROOT_PATTERN = re.compile(
        r'^\s*root\s+(?:to:\s*)?[\'"](?P<handler>[^\'"]+)[\'"]',
        re.MULTILINE
    )

    # Sinatra DSL routes
    SINATRA_ROUTE_PATTERN = re.compile(
        r'^\s*(?P<method>get|post|put|patch|delete|options|head)\s+[\'"](?P<path>[^\'"]+)[\'"]\s*(?:do)?',
        re.MULTILINE
    )

    # Grape API DSL: matches both `get :path` and `get do` (block form)
    GRAPE_ROUTE_PATTERN = re.compile(
        r'^\s*(?P<method>get|post|put|patch|delete)\s+(?:[:\'](?P<path>\w+)|do\b)',
        re.MULTILINE
    )

    # Grape resource/namespace
    GRAPE_RESOURCE_PATTERN = re.compile(
        r'^\s*(?:resource|namespace)\s+:(?P<name>\w+)',
        re.MULTILINE
    )

    # Rails controller pattern
    CONTROLLER_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>(?:\w+::)*\w+Controller)\s*<\s*(?P<parent>[\w:]+)',
        re.MULTILINE
    )

    # Controller actions (def index, def show, etc.)
    CONTROLLER_ACTION_PATTERN = re.compile(
        r'^\s*def\s+(?P<action>index|show|new|create|edit|update|destroy|search|custom\w*)\b',
        re.MULTILINE
    )

    # Before/after/around filters
    FILTER_PATTERN = re.compile(
        r'^\s*(?P<kind>before_action|after_action|around_action|before_filter|after_filter|skip_before_action)\s+:(?P<name>\w+)',
        re.MULTILINE
    )

    # gRPC service definition
    GRPC_SERVICE_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>\w+)\s*<\s*(?P<base>\w+::Service)',
        re.MULTILINE
    )

    # gRPC rpc method
    GRPC_RPC_PATTERN = re.compile(
        r'^\s*rpc\s+:(?P<name>\w+)',
        re.MULTILINE
    )

    # GraphQL type/mutation/query/input
    GRAPHQL_TYPE_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>\w+)\s*<\s*(?:GraphQL::Schema::(?P<kind>Object|Mutation|InputObject|Enum|Interface|Union|Subscription)|Types::Base(?P<kind2>Object|InputObject|Enum|Interface|Union))',
        re.MULTILINE
    )

    # GraphQL field definition
    GRAPHQL_FIELD_PATTERN = re.compile(
        r'^\s*field\s+:(?P<name>\w+)',
        re.MULTILINE
    )

    # GraphQL argument
    GRAPHQL_ARG_PATTERN = re.compile(
        r'^\s*argument\s+:(?P<name>\w+)',
        re.MULTILINE
    )

    # ActionCable channel
    ACTIONCABLE_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>\w+Channel)\s*<\s*(?:ApplicationCable::Channel|ActionCable::Channel::Base)',
        re.MULTILINE
    )

    # Rack middleware
    RACK_MIDDLEWARE_PATTERN = re.compile(
        r'^\s*(?:use|config\.middleware\.(?:use|insert_before|insert_after))\s+(?P<name>\w+(?:::\w+)*)',
        re.MULTILINE
    )

    # Roda routes
    RODA_ROUTE_PATTERN = re.compile(
        r'r\.(?P<method>get|post|put|patch|delete|is|on)\s+[\'"]?(?P<path>[^\'")\s,]+)?',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all API definitions from Ruby source code.

        Args:
            content: Ruby source code content
            file_path: Path to source file

        Returns:
            Dict with 'routes', 'controllers', 'grpc_services', 'graphql', 'channels', 'middleware'
        """
        # Detect framework context from content
        framework = self._detect_framework(content, file_path)

        routes = self._extract_routes(content, file_path, framework)
        controllers = self._extract_controllers(content, file_path)
        grpc_services = self._extract_grpc(content, file_path)
        graphql = self._extract_graphql(content, file_path)
        channels = self._extract_channels(content, file_path)
        middleware = self._extract_middleware(content, file_path)

        return {
            'routes': routes,
            'controllers': controllers,
            'grpc_services': grpc_services,
            'graphql': graphql,
            'channels': channels,
            'middleware': middleware,
        }

    def _detect_framework(self, content: str, file_path: str) -> str:
        """Detect which web framework is being used."""
        if 'Sinatra::Base' in content or 'Sinatra::Application' in content:
            return 'sinatra'
        if 'Grape::API' in content:
            return 'grape'
        if 'Hanami::Action' in content or 'Hanami::Router' in content:
            return 'hanami'
        if 'Roda' in content:
            return 'roda'
        if 'routes.rb' in file_path or 'Controller' in content:
            return 'rails'
        return 'rails'

    def _extract_routes(self, content: str, file_path: str, framework: str) -> List[RubyRouteInfo]:
        """Extract HTTP route definitions."""
        routes = []

        if framework == 'sinatra':
            for match in self.SINATRA_ROUTE_PATTERN.finditer(content):
                routes.append(RubyRouteInfo(
                    method=match.group('method').upper(),
                    path=match.group('path'),
                    handler='block',
                    framework='sinatra',
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))
        elif framework == 'grape':
            # Extract resource context for path prefixes
            resources = [m.group('name') for m in self.GRAPE_RESOURCE_PATTERN.finditer(content)]
            resource_prefix = f"/{resources[0]}" if resources else "/"
            for match in self.GRAPE_ROUTE_PATTERN.finditer(content):
                path = match.group('path') or resource_prefix
                routes.append(RubyRouteInfo(
                    method=match.group('method').upper(),
                    path=path if path.startswith('/') else f"/{path}",
                    framework='grape',
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))
        elif framework == 'roda':
            for match in self.RODA_ROUTE_PATTERN.finditer(content):
                method = match.group('method').upper()
                path = match.group('path') or '/'
                if method in ('IS', 'ON'):
                    method = 'ANY'
                routes.append(RubyRouteInfo(
                    method=method,
                    path=path,
                    framework='roda',
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))
        else:
            # Rails routes
            for match in self.RAILS_ROUTE_PATTERN.finditer(content):
                routes.append(RubyRouteInfo(
                    method=match.group('method').upper(),
                    path=match.group('path'),
                    handler=match.group('handler') or '',
                    framework='rails',
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

            # Rails root route
            for match in self.RAILS_ROOT_PATTERN.finditer(content):
                routes.append(RubyRouteInfo(
                    method='GET',
                    path='/',
                    handler=match.group('handler'),
                    framework='rails',
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

            # Rails resources (expand to standard CRUD routes)
            for match in self.RAILS_RESOURCES_PATTERN.finditer(content):
                name = match.group('name')
                kind = match.group('kind')
                line = content[:match.start()].count('\n') + 1

                if kind == 'resources':
                    for method, action, path in [
                        ('GET', 'index', f'/{name}'),
                        ('GET', 'show', f'/{name}/:id'),
                        ('GET', 'new', f'/{name}/new'),
                        ('POST', 'create', f'/{name}'),
                        ('GET', 'edit', f'/{name}/:id/edit'),
                        ('PATCH', 'update', f'/{name}/:id'),
                        ('DELETE', 'destroy', f'/{name}/:id'),
                    ]:
                        routes.append(RubyRouteInfo(
                            method=method,
                            path=path,
                            handler=f'{name}#{action}',
                            framework='rails',
                            file=file_path,
                            line_number=line,
                        ))
                else:  # resource (singular)
                    for method, action, path in [
                        ('GET', 'show', f'/{name}'),
                        ('GET', 'new', f'/{name}/new'),
                        ('POST', 'create', f'/{name}'),
                        ('GET', 'edit', f'/{name}/edit'),
                        ('PATCH', 'update', f'/{name}'),
                        ('DELETE', 'destroy', f'/{name}'),
                    ]:
                        routes.append(RubyRouteInfo(
                            method=method,
                            path=path,
                            handler=f'{name}#{action}',
                            framework='rails',
                            file=file_path,
                            line_number=line,
                        ))

        return routes

    def _extract_controllers(self, content: str, file_path: str) -> List[RubyControllerInfo]:
        """Extract Rails controller definitions."""
        controllers = []

        for match in self.CONTROLLER_PATTERN.finditer(content):
            name = match.group('name')
            parent = match.group('parent')
            line = content[:match.start()].count('\n') + 1

            # Extract actions
            actions = []
            for am in re.finditer(r'^\s*def\s+(\w+)', content[match.start():], re.MULTILINE):
                action_name = am.group(1)
                if not action_name.startswith('_'):
                    actions.append(action_name)
                if len(actions) >= 30:
                    break

            # Extract filters
            before_actions = [m.group('name') for m in self.FILTER_PATTERN.finditer(content)
                            if m.group('kind') in ('before_action', 'before_filter')]
            after_actions = [m.group('name') for m in self.FILTER_PATTERN.finditer(content)
                          if m.group('kind') in ('after_action', 'after_filter')]
            around_actions = [m.group('name') for m in self.FILTER_PATTERN.finditer(content)
                            if m.group('kind') == 'around_action']

            is_api = 'Api' in parent or 'API' in name or '::Api::' in name

            controllers.append(RubyControllerInfo(
                name=name,
                actions=actions,
                before_actions=before_actions,
                after_actions=after_actions,
                around_actions=around_actions,
                parent_class=parent,
                file=file_path,
                line_number=line,
                is_api=is_api,
            ))

        return controllers

    def _extract_grpc(self, content: str, file_path: str) -> List[RubyGRPCServiceInfo]:
        """Extract gRPC service definitions."""
        services = []

        for match in self.GRPC_SERVICE_PATTERN.finditer(content):
            name = match.group('name')
            line = content[:match.start()].count('\n') + 1
            methods = [m.group('name') for m in self.GRPC_RPC_PATTERN.finditer(content)]

            services.append(RubyGRPCServiceInfo(
                name=name,
                methods=methods,
                file=file_path,
                line_number=line,
            ))

        return services

    def _extract_graphql(self, content: str, file_path: str) -> List[RubyGraphQLInfo]:
        """Extract GraphQL type definitions (graphql-ruby gem)."""
        types = []

        for match in self.GRAPHQL_TYPE_PATTERN.finditer(content):
            name = match.group('name')
            kind = (match.group('kind') or match.group('kind2') or 'Object').lower()
            if kind == 'object':
                kind = 'type'
            elif kind == 'inputobject':
                kind = 'input'
            line = content[:match.start()].count('\n') + 1

            # Extract fields
            fields = [m.group('name') for m in self.GRAPHQL_FIELD_PATTERN.finditer(content)]
            args = [m.group('name') for m in self.GRAPHQL_ARG_PATTERN.finditer(content)]

            types.append(RubyGraphQLInfo(
                name=name,
                kind=kind,
                fields=fields[:20],
                arguments=args[:10],
                file=file_path,
                line_number=line,
            ))

        return types

    def _extract_channels(self, content: str, file_path: str) -> List[Dict]:
        """Extract ActionCable channel definitions."""
        channels = []

        for match in self.ACTIONCABLE_PATTERN.finditer(content):
            name = match.group('name')
            line = content[:match.start()].count('\n') + 1

            # Extract subscribed/unsubscribed/receive and other methods
            actions = []
            for am in re.finditer(r'^\s*def\s+(\w+)', content[match.start():], re.MULTILINE):
                actions.append(am.group(1))
                if len(actions) >= 10:
                    break

            channels.append({
                'name': name,
                'actions': actions,
                'file': file_path,
                'line': line,
            })

        return channels

    def _extract_middleware(self, content: str, file_path: str) -> List[str]:
        """Extract Rack middleware usage."""
        middleware = []
        for match in self.RACK_MIDDLEWARE_PATTERN.finditer(content):
            mw_name = match.group('name')
            if mw_name not in middleware:
                middleware.append(mw_name)
        return middleware
