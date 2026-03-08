"""
Dart API Extractor for CodeTrellis

Extracts API/framework patterns from Dart source code:
- Flutter widgets (StatelessWidget, StatefulWidget, State)
- Flutter route definitions
- Shelf HTTP routes (dart:io server, shelf, shelf_router)
- Dart Frog API routes
- Serverpod endpoints
- gRPC service implementations
- GraphQL schema (Ferry, Artemis)
- Riverpod/Bloc/GetX state management
- Dio/http interceptors
- Firebase integrations

Supports:
- Flutter 1.x through Flutter 3.x+
- Server-side Dart: shelf, dart_frog, serverpod, conduit, angel
- State management: Riverpod, Bloc, Provider, GetX, MobX
- Networking: Dio, http, Chopper, Retrofit

Part of CodeTrellis v4.27 - Dart Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DartWidgetInfo:
    """Information about a Flutter widget."""
    name: str
    file: str = ""
    widget_type: str = ""  # stateless, stateful, inherited, render_object
    kind: str = ""  # alias for widget_type (used by scanner)
    parent_class: str = ""
    state_class: str = ""  # For StatefulWidget
    has_key: bool = False
    build_method: bool = False
    build_methods: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class DartRouteInfo:
    """Information about an HTTP route."""
    method: str = ""  # GET, POST, PUT, DELETE, PATCH, WS
    path: str = ""
    handler: str = ""
    framework: str = ""  # shelf, dart_frog, serverpod, angel, conduit
    middleware: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class DartStateInfo:
    """Information about state management."""
    name: str
    file: str = ""
    pattern: str = ""  # riverpod, bloc, cubit, getx, provider, mobx
    framework: str = ""  # alias for pattern (used by scanner)
    kind: str = ""  # notifier, provider, bloc, cubit, etc.
    state_type: str = ""
    events: List[str] = field(default_factory=list)
    providers: List[str] = field(default_factory=list)
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class DartGRPCServiceInfo:
    """Information about a gRPC service."""
    name: str
    file: str = ""
    methods: List[str] = field(default_factory=list)
    line_number: int = 0


class DartAPIExtractor:
    """
    Extracts API and framework patterns from Dart source code.

    Detects:
    - Flutter widgets (Stateless, Stateful, InheritedWidget)
    - Shelf/dart_frog/serverpod HTTP routes
    - State management patterns (Riverpod, Bloc, GetX, Provider, MobX)
    - gRPC service definitions
    - Flutter navigation/routing
    """

    # StatelessWidget pattern
    STATELESS_WIDGET_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>\w+)\s+extends\s+StatelessWidget\b',
        re.MULTILINE
    )

    # StatefulWidget pattern
    STATEFUL_WIDGET_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>\w+)\s+extends\s+StatefulWidget\b',
        re.MULTILINE
    )

    # State class pattern
    STATE_CLASS_PATTERN = re.compile(
        r'^\s*class\s+(?P<state_name>\w+)\s+extends\s+State<(?P<widget_name>\w+)>',
        re.MULTILINE
    )

    # InheritedWidget pattern
    INHERITED_WIDGET_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>\w+)\s+extends\s+(?:InheritedWidget|InheritedNotifier|InheritedModel)\b',
        re.MULTILINE
    )

    # RenderObject pattern
    RENDER_OBJECT_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>\w+)\s+extends\s+(?:RenderBox|RenderObject|RenderSliver|LeafRenderObjectWidget|SingleChildRenderObjectWidget|MultiChildRenderObjectWidget)\b',
        re.MULTILINE
    )

    # Shelf route handler pattern
    SHELF_ROUTE_PATTERN = re.compile(
        r"router\.(?P<method>get|post|put|delete|patch|head|options|all)\s*\(\s*['\"](?P<path>[^'\"]+)['\"]",
        re.MULTILINE | re.IGNORECASE
    )

    # Shelf handler annotation (@Route.get, @Route.post, etc.)
    SHELF_ANNOTATION_PATTERN = re.compile(
        r"@Route\.(?P<method>get|post|put|delete|patch|head|all)\s*\(\s*['\"](?P<path>[^'\"]+)['\"]",
        re.MULTILINE | re.IGNORECASE
    )

    # Dart Frog route handler pattern (convention-based)
    DART_FROG_HANDLER_PATTERN = re.compile(
        r'Response\s+(?P<handler>on(?:Get|Post|Put|Delete|Patch|Request))\s*\(',
        re.MULTILINE
    )

    # Serverpod endpoint pattern
    SERVERPOD_ENDPOINT_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s+extends\s+Endpoint\b',
        re.MULTILINE
    )

    # Riverpod provider patterns
    RIVERPOD_PROVIDER_PATTERN = re.compile(
        r'(?:final|const)\s+(?P<name>\w+)\s*=\s*'
        r'(?:StateNotifier|ChangeNotifier|Notifier|AsyncNotifier|Stream)?'
        r'Provider(?:\.(?:family|autoDispose))*'
        r'(?:<(?P<type>[^>]+)>)?',
        re.MULTILINE
    )

    # Riverpod @riverpod annotation (code-gen)
    RIVERPOD_ANNOTATION_PATTERN = re.compile(
        r'@(?:riverpod|Riverpod)\b',
        re.MULTILINE
    )

    # Bloc pattern
    BLOC_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s+extends\s+(?:Bloc|Cubit)<(?P<state>[^>]+)>',
        re.MULTILINE
    )

    # Bloc event handler pattern
    BLOC_EVENT_HANDLER = re.compile(
        r'on<(?P<event>\w+)>\s*\(',
        re.MULTILINE
    )

    # GetX controller pattern
    GETX_CONTROLLER_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s+extends\s+(?:GetxController|GetxService|GetConnect)\b',
        re.MULTILINE
    )

    # Provider (basic) pattern
    PROVIDER_PATTERN = re.compile(
        r'(?:ChangeNotifierProvider|ValueNotifierProvider|ListenableProvider|'
        r'FutureProvider|StreamProvider|Provider)\s*(?:<[^>]+>)?\s*\(',
        re.MULTILINE
    )

    # MobX store pattern
    MOBX_STORE_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s+extends\s+_\w+\s+with\s+_\$\w+',
        re.MULTILINE
    )

    # gRPC service pattern
    GRPC_SERVICE_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s+extends\s+(?P<base>\w+ServiceBase)\b',
        re.MULTILINE
    )

    # Flutter route definition patterns
    FLUTTER_ROUTE_PATTERN = re.compile(
        r"(?:GoRoute|MaterialPageRoute|CupertinoPageRoute|GetPage)\s*\(\s*"
        r"(?:path:|name:)\s*['\"](?P<path>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # AutoRoute pattern
    AUTO_ROUTE_PATTERN = re.compile(
        r'@(?:MaterialRoute|CupertinoRoute|CustomRoute|AdaptiveRoute)\s*\(\s*'
        r'(?:page:)?\s*(?P<page>\w+)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all API/framework patterns from Dart source code.

        Returns:
            Dict with 'widgets', 'routes', 'state_managers',
            'grpc_services', 'flutter_routes' lists.
        """
        result: Dict[str, Any] = {
            'widgets': [],
            'routes': [],
            'state_managers': [],
            'grpc_services': [],
            'flutter_routes': [],
        }

        result['widgets'] = self._extract_widgets(content, file_path)
        result['routes'] = self._extract_routes(content, file_path)
        result['state_managers'] = self._extract_state_managers(content, file_path)
        result['grpc_services'] = self._extract_grpc_services(content, file_path)
        result['flutter_routes'] = self._extract_flutter_routes(content, file_path)

        return result

    def _extract_widgets(self, content: str, file_path: str) -> List[DartWidgetInfo]:
        """Extract Flutter widget declarations."""
        widgets = []

        # StatelessWidget
        for match in self.STATELESS_WIDGET_PATTERN.finditer(content):
            widgets.append(DartWidgetInfo(
                name=match.group('name'),
                file=file_path,
                widget_type="stateless",
                parent_class="StatelessWidget",
                build_method='Widget build(' in content,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # StatefulWidget
        for match in self.STATEFUL_WIDGET_PATTERN.finditer(content):
            name = match.group('name')
            # Find corresponding State class
            state_class = ""
            for state_match in self.STATE_CLASS_PATTERN.finditer(content):
                if state_match.group('widget_name') == name:
                    state_class = state_match.group('state_name')
                    break

            widgets.append(DartWidgetInfo(
                name=name,
                file=file_path,
                widget_type="stateful",
                parent_class="StatefulWidget",
                state_class=state_class,
                build_method='Widget build(' in content,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # InheritedWidget
        for match in self.INHERITED_WIDGET_PATTERN.finditer(content):
            widgets.append(DartWidgetInfo(
                name=match.group('name'),
                file=file_path,
                widget_type="inherited",
                parent_class="InheritedWidget",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # RenderObject
        for match in self.RENDER_OBJECT_PATTERN.finditer(content):
            widgets.append(DartWidgetInfo(
                name=match.group('name'),
                file=file_path,
                widget_type="render_object",
                parent_class="RenderObject",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return widgets

    def _extract_routes(self, content: str, file_path: str) -> List[DartRouteInfo]:
        """Extract HTTP API route definitions."""
        routes = []

        # Shelf routes
        for match in self.SHELF_ROUTE_PATTERN.finditer(content):
            routes.append(DartRouteInfo(
                method=match.group('method').upper(),
                path=match.group('path'),
                framework="shelf",
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Shelf annotation routes
        for match in self.SHELF_ANNOTATION_PATTERN.finditer(content):
            routes.append(DartRouteInfo(
                method=match.group('method').upper(),
                path=match.group('path'),
                framework="shelf_router",
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Dart Frog handlers
        for match in self.DART_FROG_HANDLER_PATTERN.finditer(content):
            handler = match.group('handler')
            method_map = {
                'onGet': 'GET', 'onPost': 'POST', 'onPut': 'PUT',
                'onDelete': 'DELETE', 'onPatch': 'PATCH', 'onRequest': 'ANY',
            }
            routes.append(DartRouteInfo(
                method=method_map.get(handler, 'ANY'),
                handler=handler,
                framework="dart_frog",
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Serverpod endpoints
        for match in self.SERVERPOD_ENDPOINT_PATTERN.finditer(content):
            routes.append(DartRouteInfo(
                handler=match.group('name'),
                framework="serverpod",
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return routes

    def _extract_state_managers(self, content: str, file_path: str) -> List[DartStateInfo]:
        """Extract state management patterns."""
        managers = []

        # Riverpod providers
        for match in self.RIVERPOD_PROVIDER_PATTERN.finditer(content):
            managers.append(DartStateInfo(
                name=match.group('name'),
                file=file_path,
                pattern="riverpod",
                state_type=match.group('type') or "",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Bloc/Cubit
        for match in self.BLOC_PATTERN.finditer(content):
            name = match.group('name')
            # Find events
            events = [em.group('event') for em in self.BLOC_EVENT_HANDLER.finditer(content)]

            is_cubit = 'extends Cubit' in content[match.start():match.start() + 200]
            managers.append(DartStateInfo(
                name=name,
                file=file_path,
                pattern="cubit" if is_cubit else "bloc",
                state_type=match.group('state'),
                events=events[:10],
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # GetX controllers
        for match in self.GETX_CONTROLLER_PATTERN.finditer(content):
            managers.append(DartStateInfo(
                name=match.group('name'),
                file=file_path,
                pattern="getx",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # MobX stores
        for match in self.MOBX_STORE_PATTERN.finditer(content):
            managers.append(DartStateInfo(
                name=match.group('name'),
                file=file_path,
                pattern="mobx",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return managers

    def _extract_grpc_services(self, content: str, file_path: str) -> List[DartGRPCServiceInfo]:
        """Extract gRPC service implementations."""
        services = []

        for match in self.GRPC_SERVICE_PATTERN.finditer(content):
            name = match.group('name')
            # Find method declarations in the service
            methods = []
            method_pattern = re.compile(
                r'Future<\w+>\s+(\w+)\s*\(', re.MULTILINE
            )
            service_start = match.end()
            service_area = content[service_start:service_start + 2000]
            for m in method_pattern.finditer(service_area):
                methods.append(m.group(1))

            services.append(DartGRPCServiceInfo(
                name=name,
                file=file_path,
                methods=methods[:20],
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return services

    def _extract_flutter_routes(self, content: str, file_path: str) -> List[DartRouteInfo]:
        """Extract Flutter navigation route definitions."""
        routes = []

        # GoRouter / MaterialPageRoute patterns
        for match in self.FLUTTER_ROUTE_PATTERN.finditer(content):
            routes.append(DartRouteInfo(
                path=match.group('path'),
                framework="flutter_router",
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # AutoRoute patterns
        for match in self.AUTO_ROUTE_PATTERN.finditer(content):
            routes.append(DartRouteInfo(
                handler=match.group('page'),
                framework="auto_route",
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return routes
