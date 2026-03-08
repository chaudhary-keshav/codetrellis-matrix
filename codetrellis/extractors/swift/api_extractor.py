"""
Swift API Extractor for CodeTrellis

Extracts API and framework-specific patterns from Swift source code:
- Vapor routes (GET, POST, PUT, DELETE, PATCH, WebSocket)
- SwiftUI views (body, ViewBuilder, previews)
- Combine publishers and subscribers
- URLSession / Alamofire HTTP calls
- gRPC services (GRPC Swift / SwiftProtobuf)
- SwiftNIO channel handlers
- GraphQL (Graphiti)
- WebSocket endpoints
- Server-side Swift (Kitura, Perfect, Hummingbird)

Part of CodeTrellis v4.22 - Swift Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SwiftRouteInfo:
    """Information about an HTTP route/endpoint."""
    method: str = ""  # GET, POST, PUT, DELETE, PATCH, etc.
    path: str = ""
    handler: str = ""
    middleware: List[str] = field(default_factory=list)
    framework: str = ""  # vapor, kitura, perfect, hummingbird
    is_async: bool = False
    is_throws: bool = False
    is_grouped: bool = False
    group_path: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SwiftViewInfo:
    """Information about a SwiftUI View."""
    name: str
    file: str = ""
    state_properties: List[str] = field(default_factory=list)
    binding_properties: List[str] = field(default_factory=list)
    environment_properties: List[str] = field(default_factory=list)
    observed_objects: List[str] = field(default_factory=list)
    child_views: List[str] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    uses_navigation: bool = False
    uses_list: bool = False
    uses_form: bool = False
    is_preview_provider: bool = False
    line_number: int = 0


@dataclass
class SwiftPublisherInfo:
    """Information about a Combine publisher/subscriber."""
    name: str
    file: str = ""
    publisher_type: str = ""  # CurrentValueSubject, PassthroughSubject, @Published, etc.
    output_type: str = ""
    failure_type: str = ""
    operators: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SwiftGRPCServiceInfo:
    """Information about a gRPC service."""
    name: str
    file: str = ""
    methods: List[str] = field(default_factory=list)
    is_client: bool = False
    is_server: bool = False
    line_number: int = 0


class SwiftAPIExtractor:
    """
    Extracts API patterns from Swift source code.

    Supports:
    - Vapor (routes, middleware, groups)
    - Kitura, Perfect, Hummingbird routes
    - SwiftUI views and view hierarchy
    - Combine reactive patterns
    - gRPC services
    - URLSession calls
    """

    # Vapor route patterns
    VAPOR_ROUTE_PATTERN = re.compile(
        r'(?:app|routes|router|grouped)\s*\.\s*'
        r'(?P<method>get|post|put|delete|patch|head|options|webSocket)\s*\('
        r'(?P<path>[^)]*)\)',
        re.IGNORECASE
    )

    # Vapor route group pattern
    VAPOR_GROUP_PATTERN = re.compile(
        r'(?:app|routes|router)\s*\.\s*grouped\s*\(\s*'
        r'(?:"(?P<path>[^"]*)")?'
        r'(?:,\s*(?P<middleware>[^)]+))?'
        r'\)',
        re.MULTILINE
    )

    # Hummingbird route pattern
    HUMMINGBIRD_ROUTE_PATTERN = re.compile(
        r'(?:app|router)\s*\.\s*(?:on|'
        r'(?P<method>get|post|put|delete|patch))\s*\('
        r'(?:"(?P<path>[^"]*)")',
        re.IGNORECASE
    )

    # SwiftUI View conformance
    SWIFTUI_VIEW_PATTERN = re.compile(
        r'struct\s+(?P<name>\w+)\s*:\s*[^{]*\bView\b[^{]*\{',
        re.MULTILINE
    )

    # SwiftUI state properties
    SWIFTUI_STATE_PATTERN = re.compile(
        r'@(?P<wrapper>State|Binding|Published|ObservedObject|StateObject|'
        r'EnvironmentObject|Environment|AppStorage|SceneStorage|'
        r'FetchRequest|Query|Bindable|Observable)\s+'
        r'(?:(?:private|public|internal|fileprivate)\s+)?'
        r'var\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Combine publisher patterns
    COMBINE_PUBLISHER_PATTERN = re.compile(
        r'(?:let|var)\s+(?P<name>\w+)\s*(?::\s*(?P<type>[^=]+))?\s*=\s*'
        r'(?P<publisher>CurrentValueSubject|PassthroughSubject|'
        r'AnyPublisher|Published\.Publisher|Just|Future|Deferred)\s*'
        r'(?:<(?P<generics>[^>]+)>)?',
        re.MULTILINE
    )

    # @Published property
    PUBLISHED_PATTERN = re.compile(
        r'@Published\s+(?:(?:private|public|internal|fileprivate)\s+)?'
        r'var\s+(?P<name>\w+)\s*(?::\s*(?P<type>[^=\n{]+))?',
        re.MULTILINE
    )

    # gRPC provider/client patterns
    GRPC_PROVIDER_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s*:\s*[^{]*'
        r'(?P<kind>Provider|AsyncProvider|Client|AsyncClient)\b',
        re.MULTILINE
    )

    # URLSession patterns
    URLSESSION_PATTERN = re.compile(
        r'URLSession\s*\.\s*shared\s*\.\s*'
        r'(?P<method>data|upload|download|dataTask|uploadTask|downloadTask)'
        r'\s*\(',
        re.MULTILINE
    )

    # Alamofire patterns
    ALAMOFIRE_PATTERN = re.compile(
        r'AF\s*\.\s*request\s*\(\s*(?P<url>[^,)]+)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract API patterns from Swift source code.

        Args:
            content: Swift source code
            file_path: Path to source file

        Returns:
            Dict with keys: routes, views, publishers, grpc_services
        """
        return {
            'routes': self._extract_routes(content, file_path),
            'views': self._extract_views(content, file_path),
            'publishers': self._extract_publishers(content, file_path),
            'grpc_services': self._extract_grpc(content, file_path),
        }

    def _extract_routes(self, content: str, file_path: str) -> List[SwiftRouteInfo]:
        """Extract HTTP route definitions."""
        routes = []

        # Vapor routes
        for match in self.VAPOR_ROUTE_PATTERN.finditer(content):
            method = match.group('method').upper()
            if method == 'WEBSOCKET':
                method = 'WS'
            path_str = match.group('path').strip()
            # Extract path strings
            paths = re.findall(r'"([^"]*)"', path_str)
            path = '/' + '/'.join(paths) if paths else path_str

            # Look for handler name
            handler = ''
            handler_match = re.search(r'use:\s*(\w+)', path_str)
            if handler_match:
                handler = handler_match.group(1)

            line_number = content[:match.start()].count('\n') + 1

            routes.append(SwiftRouteInfo(
                method=method,
                path=path,
                handler=handler,
                framework='vapor',
                file=file_path,
                line_number=line_number,
            ))

        # Hummingbird routes
        for match in self.HUMMINGBIRD_ROUTE_PATTERN.finditer(content):
            method = (match.group('method') or 'GET').upper()
            path = match.group('path') or ''

            line_number = content[:match.start()].count('\n') + 1

            routes.append(SwiftRouteInfo(
                method=method,
                path='/' + path if path and not path.startswith('/') else path,
                framework='hummingbird',
                file=file_path,
                line_number=line_number,
            ))

        return routes

    def _extract_views(self, content: str, file_path: str) -> List[SwiftViewInfo]:
        """Extract SwiftUI views."""
        views = []
        for match in self.SWIFTUI_VIEW_PATTERN.finditer(content):
            name = match.group('name')

            # Extract view body
            body_start = content.find('{', match.start())
            body = self._extract_brace_body(content, body_start) if body_start >= 0 else ''

            # Extract state properties
            state_props = []
            binding_props = []
            env_props = []
            observed = []

            for prop_match in self.SWIFTUI_STATE_PATTERN.finditer(content[match.start():match.start() + len(body) + 100]):
                wrapper = prop_match.group('wrapper')
                prop_name = prop_match.group('name')
                if wrapper == 'State':
                    state_props.append(prop_name)
                elif wrapper == 'Binding':
                    binding_props.append(prop_name)
                elif wrapper in ('Environment', 'EnvironmentObject'):
                    env_props.append(prop_name)
                elif wrapper in ('ObservedObject', 'StateObject'):
                    observed.append(prop_name)

            uses_nav = bool(re.search(r'NavigationView|NavigationStack|NavigationLink|NavigationSplitView', body))
            uses_list = bool(re.search(r'\bList\b|\bForEach\b|\bLazyVStack\b|\bLazyHStack\b', body))
            uses_form = bool(re.search(r'\bForm\b|\bSection\b|\bTextField\b|\bToggle\b|\bPicker\b', body))

            line_number = content[:match.start()].count('\n') + 1

            views.append(SwiftViewInfo(
                name=name,
                file=file_path,
                state_properties=state_props,
                binding_properties=binding_props,
                environment_properties=env_props,
                observed_objects=observed,
                uses_navigation=uses_nav,
                uses_list=uses_list,
                uses_form=uses_form,
                line_number=line_number,
            ))
        return views

    def _extract_publishers(self, content: str, file_path: str) -> List[SwiftPublisherInfo]:
        """Extract Combine publishers."""
        publishers = []

        # Direct publisher declarations
        for match in self.COMBINE_PUBLISHER_PATTERN.finditer(content):
            name = match.group('name')
            publisher_type = match.group('publisher')
            generics = match.group('generics') or ''

            output_type = ''
            failure_type = ''
            if generics:
                parts = [p.strip() for p in generics.split(',')]
                if len(parts) >= 1:
                    output_type = parts[0]
                if len(parts) >= 2:
                    failure_type = parts[1]

            line_number = content[:match.start()].count('\n') + 1

            publishers.append(SwiftPublisherInfo(
                name=name,
                file=file_path,
                publisher_type=publisher_type,
                output_type=output_type,
                failure_type=failure_type,
                line_number=line_number,
            ))

        # @Published properties
        for match in self.PUBLISHED_PATTERN.finditer(content):
            name = match.group('name')
            type_str = (match.group('type') or '').strip()

            line_number = content[:match.start()].count('\n') + 1

            publishers.append(SwiftPublisherInfo(
                name=name,
                file=file_path,
                publisher_type='@Published',
                output_type=type_str,
                line_number=line_number,
            ))

        return publishers

    def _extract_grpc(self, content: str, file_path: str) -> List[SwiftGRPCServiceInfo]:
        """Extract gRPC service implementations."""
        services = []
        for match in self.GRPC_PROVIDER_PATTERN.finditer(content):
            name = match.group('name')
            kind = match.group('kind')
            is_client = 'Client' in kind
            is_server = 'Provider' in kind

            # Extract method names from body
            body_start = content.find('{', match.start())
            body = self._extract_brace_body(content, body_start) if body_start >= 0 else ''
            methods = re.findall(r'func\s+(\w+)', body)

            line_number = content[:match.start()].count('\n') + 1

            services.append(SwiftGRPCServiceInfo(
                name=name,
                file=file_path,
                methods=methods,
                is_client=is_client,
                is_server=is_server,
                line_number=line_number,
            ))
        return services

    def _extract_brace_body(self, content: str, open_pos: int) -> str:
        """Extract body between matching braces."""
        if open_pos >= len(content) or content[open_pos] != '{':
            return ""
        depth = 0
        i = open_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[open_pos + 1:i]
            i += 1
        return content[open_pos + 1:]
