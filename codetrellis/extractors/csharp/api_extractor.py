"""
CSharpAPIExtractor - Extracts ASP.NET Core endpoints, gRPC services, SignalR hubs.

Extracts:
- ASP.NET Core MVC/API controllers ([ApiController], [Route], [HttpGet], etc.)
- Minimal API endpoints (app.MapGet, app.MapPost, etc.)
- gRPC service implementations (override methods from generated base)
- SignalR hub methods
- Razor Pages handlers (OnGet, OnPost, etc.)
- Controller action filters and route constraints
- API versioning ([ApiVersion])
- Response types ([ProducesResponseType])

Part of CodeTrellis v4.13 - C# Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSharpEndpointInfo:
    """Information about a C# API endpoint."""
    method: str              # GET, POST, PUT, DELETE, PATCH
    path: str                # Route path
    handler_method: str      # Method name
    controller: str = ""     # Controller name
    return_type: str = ""    # Return type (IActionResult, Task<T>, etc.)
    parameters: List[Dict[str, str]] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    response_types: List[str] = field(default_factory=list)  # [ProducesResponseType]
    is_authorized: bool = False
    authorize_policy: Optional[str] = None
    api_version: Optional[str] = None
    framework: str = "aspnet"  # aspnet, minimal_api, razor_pages
    file: str = ""
    line_number: int = 0


@dataclass
class CSharpGRPCServiceInfo:
    """Information about a C# gRPC service."""
    name: str
    base_class: str = ""
    methods: List[Dict[str, str]] = field(default_factory=list)  # name, request_type, response_type
    file: str = ""
    line_number: int = 0


@dataclass
class CSharpSignalRHubInfo:
    """Information about a C# SignalR hub."""
    name: str
    base_class: str = ""
    methods: List[Dict[str, str]] = field(default_factory=list)  # name, return_type
    file: str = ""
    line_number: int = 0


class CSharpAPIExtractor:
    """
    Extracts C# API endpoint definitions from source code.

    Handles:
    - ASP.NET Core MVC controllers with [HttpGet], [HttpPost], etc.
    - Controller base route from [Route] attribute
    - [ApiController] detection
    - Minimal API (app.MapGet, app.MapPost, etc.)
    - gRPC service implementations
    - SignalR Hub classes
    - Razor Pages handlers
    - [Authorize] attribute detection
    - [ProducesResponseType] for response documentation
    - [ApiVersion] for API versioning
    """

    # Controller-level route
    CONTROLLER_ROUTE = re.compile(
        r'\[Route\s*\(\s*["\']([^"\']+)["\']\s*\)\]',
    )

    # API Controller attribute
    API_CONTROLLER = re.compile(r'\[ApiController\]')

    # HTTP method attributes
    HTTP_METHOD_PATTERN = re.compile(
        r'\[(Http(?:Get|Post|Put|Delete|Patch|Head|Options))'  # HTTP method attribute
        r'(?:\s*\(\s*["\']([^"\']*)["\'])?'                   # Optional route template
        r'[^]]*\]'                                             # Rest of attribute
        r'.*?'                                                 # Stuff between
        r'(?:public|private|protected|internal)\s+'            # Access modifier
        r'(?:async\s+)?'                                       # Optional async
        r'([\w<>\[\]?,.\s]+?)\s+'                              # Return type
        r'(\w+)\s*\(',                                         # Method name
        re.MULTILINE | re.DOTALL
    )

    # Minimal API patterns — capture handler (method reference or lambda)
    MINIMAL_API_PATTERN = re.compile(
        r'\w+\s*\.\s*'
        r'Map(Get|Post|Put|Delete|Patch)\s*\(\s*'
        r'["\']([^"\']+)["\']\s*,\s*'
        r'(\w+|\([^)]*\)\s*=>)',               # Handler: method reference or lambda
        re.MULTILINE
    )

    # Authorize attribute
    AUTHORIZE_PATTERN = re.compile(
        r'\[Authorize(?:\s*\(\s*(?:Policy\s*=\s*["\']([^"\']+)["\']|Roles\s*=\s*["\']([^"\']+)["\']\s*)?\s*\))?\]'
    )

    # ProducesResponseType
    PRODUCES_PATTERN = re.compile(
        r'\[ProducesResponseType\s*\(\s*(?:typeof\s*\(\s*(\w+)\s*\)\s*,\s*)?(\d+)\s*\)\]'
    )

    # API Version
    API_VERSION_PATTERN = re.compile(
        r'\[ApiVersion\s*\(\s*["\']([^"\']+)["\']\s*\)\]'
    )

    # SignalR Hub
    SIGNALR_HUB_PATTERN = re.compile(
        r'(?:public|internal)\s+class\s+(\w+)\s*:\s*Hub(?:<(\w+)>)?\s*\{',
        re.MULTILINE
    )

    # gRPC service
    GRPC_SERVICE_PATTERN = re.compile(
        r'(?:public|internal)\s+class\s+(\w+)\s*:\s*(\w+)\.(\w+Base)\s*\{',
        re.MULTILINE
    )

    # Razor Pages handler pattern
    RAZOR_HANDLER_PATTERN = re.compile(
        r'public\s+(?:async\s+)?(?:[\w<>]+\s+)?(On(?:Get|Post|Put|Delete)(?:Async)?)\s*\(',
        re.MULTILINE
    )

    # Controller class detection
    CONTROLLER_CLASS_PATTERN = re.compile(
        r'(?:public|internal)\s+class\s+(\w+)\s*:\s*(?:Controller(?:Base)?|ControllerBase)\s*',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all API endpoints from C# source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with keys: endpoints, grpc_services, signalr_hubs
        """
        result = {
            "endpoints": [],
            "grpc_services": [],
            "signalr_hubs": [],
        }

        # Extract controller-based endpoints
        controller_endpoints = self._extract_controller_endpoints(content, file_path)
        result["endpoints"].extend(controller_endpoints)

        # Extract minimal API endpoints
        minimal_endpoints = self._extract_minimal_api(content, file_path)
        result["endpoints"].extend(minimal_endpoints)

        # Extract Razor Pages handlers
        razor_endpoints = self._extract_razor_handlers(content, file_path)
        result["endpoints"].extend(razor_endpoints)

        # Extract gRPC services
        result["grpc_services"] = self._extract_grpc_services(content, file_path)

        # Extract SignalR hubs
        result["signalr_hubs"] = self._extract_signalr_hubs(content, file_path)

        return result

    def _extract_controller_endpoints(self, content: str, file_path: str) -> List[CSharpEndpointInfo]:
        """Extract endpoints from ASP.NET Core controllers."""
        endpoints = []

        # Detect controller base route
        base_route = ""
        route_match = self.CONTROLLER_ROUTE.search(content)
        if route_match:
            base_route = route_match.group(1)

        # Detect API version
        api_version = None
        ver_match = self.API_VERSION_PATTERN.search(content)
        if ver_match:
            api_version = ver_match.group(1)

        # Detect controller name
        controller_name = ""
        ctrl_match = self.CONTROLLER_CLASS_PATTERN.search(content)
        if ctrl_match:
            controller_name = ctrl_match.group(1)

        # Extract HTTP endpoints
        for match in self.HTTP_METHOD_PATTERN.finditer(content):
            http_attr = match.group(1)  # HttpGet, HttpPost, etc.
            route_template = match.group(2) or ""
            return_type = match.group(3).strip()
            method_name = match.group(4)

            # Build full route
            method = http_attr.replace("Http", "").upper()
            path = base_route
            if route_template:
                if path and not path.endswith('/'):
                    path += '/'
                path += route_template
            elif not path:
                path = f"/{controller_name.replace('Controller', '').lower()}/{method_name.lower()}"

            # Check for authorization
            # Search backward from match for [Authorize]
            preceding = content[:match.start()]
            is_authorized = bool(self.AUTHORIZE_PATTERN.search(preceding[-500:] if len(preceding) > 500 else preceding))
            authorize_policy = None
            auth_match = self.AUTHORIZE_PATTERN.search(preceding[-500:] if len(preceding) > 500 else preceding)
            if auth_match:
                authorize_policy = auth_match.group(1) or auth_match.group(2)

            # Response types
            response_types = []
            for prod in self.PRODUCES_PATTERN.finditer(preceding[-500:] if len(preceding) > 500 else preceding):
                type_name = prod.group(1) or ""
                status = prod.group(2)
                response_types.append(f"{status}:{type_name}" if type_name else status)

            line_number = content[:match.start()].count('\n') + 1

            endpoints.append(CSharpEndpointInfo(
                method=method,
                path=path,
                handler_method=method_name,
                controller=controller_name,
                return_type=return_type,
                is_authorized=is_authorized,
                authorize_policy=authorize_policy,
                api_version=api_version,
                response_types=response_types,
                framework="aspnet",
                file=file_path,
                line_number=line_number,
            ))

        return endpoints

    def _extract_minimal_api(self, content: str, file_path: str) -> List[CSharpEndpointInfo]:
        """Extract Minimal API endpoints."""
        endpoints = []
        for match in self.MINIMAL_API_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            handler = match.group(3)
            line_number = content[:match.start()].count('\n') + 1

            # Use captured handler name if it's a valid identifier, else synthesize
            handler_name = handler if handler and handler[0].isupper() else f"Map{method}_{path.replace('/', '_').strip('_')}"

            endpoints.append(CSharpEndpointInfo(
                method=method,
                path=path,
                handler_method=handler_name,
                framework="minimal_api",
                file=file_path,
                line_number=line_number,
            ))

        return endpoints

    def _extract_razor_handlers(self, content: str, file_path: str) -> List[CSharpEndpointInfo]:
        """Extract Razor Pages handlers."""
        endpoints = []
        for match in self.RAZOR_HANDLER_PATTERN.finditer(content):
            handler = match.group(1)
            method = "GET"
            if "Post" in handler:
                method = "POST"
            elif "Put" in handler:
                method = "PUT"
            elif "Delete" in handler:
                method = "DELETE"

            line_number = content[:match.start()].count('\n') + 1
            endpoints.append(CSharpEndpointInfo(
                method=method,
                path="",  # Path determined by file location in Razor Pages
                handler_method=handler,
                framework="razor_pages",
                file=file_path,
                line_number=line_number,
            ))

        return endpoints

    def _extract_grpc_services(self, content: str, file_path: str) -> List[CSharpGRPCServiceInfo]:
        """Extract gRPC service implementations."""
        services = []
        for match in self.GRPC_SERVICE_PATTERN.finditer(content):
            name = match.group(1)
            proto_service = match.group(2)
            base_class = f"{proto_service}.{match.group(3)}"

            # Extract override methods
            methods = []
            method_re = re.compile(
                r'public\s+override\s+(?:async\s+)?'
                r'([\w<>\[\]?,.\s]+?)\s+'
                r'(\w+)\s*\(',
                re.MULTILINE
            )
            for m in method_re.finditer(content[match.start():]):
                return_type = m.group(1).strip()
                method_name = m.group(2)
                methods.append({
                    "name": method_name,
                    "return_type": return_type,
                })

            line_number = content[:match.start()].count('\n') + 1
            services.append(CSharpGRPCServiceInfo(
                name=name,
                base_class=base_class,
                methods=methods[:20],
                file=file_path,
                line_number=line_number,
            ))

        return services

    def _extract_signalr_hubs(self, content: str, file_path: str) -> List[CSharpSignalRHubInfo]:
        """Extract SignalR hub classes."""
        hubs = []
        for match in self.SIGNALR_HUB_PATTERN.finditer(content):
            name = match.group(1)
            client_interface = match.group(2) or ""

            # Extract public methods (hub methods callable from clients)
            methods = []
            body_start = match.end()
            method_re = re.compile(
                r'public\s+(?:async\s+)?'
                r'([\w<>\[\]?,.\s]+?)\s+'
                r'(\w+)\s*\(',
                re.MULTILINE
            )
            for m in method_re.finditer(content[body_start:body_start + 3000]):
                return_type = m.group(1).strip()
                method_name = m.group(2)
                if method_name not in ('Dispose', 'ToString', 'Equals', 'GetHashCode'):
                    methods.append({
                        "name": method_name,
                        "return_type": return_type,
                    })

            line_number = content[:match.start()].count('\n') + 1
            hubs.append(CSharpSignalRHubInfo(
                name=name,
                base_class=f"Hub<{client_interface}>" if client_interface else "Hub",
                methods=methods[:20],
                file=file_path,
                line_number=line_number,
            ))

        return hubs
