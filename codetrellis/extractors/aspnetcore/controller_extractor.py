"""
ASP.NET Core Controller & Endpoint Extractor.

Extracts MVC controllers, API controllers, Minimal API endpoints,
action filters, and route information from ASP.NET Core source files.

Supports:
- [ApiController] attribute controllers
- [Controller] base class controllers  
- Minimal API (app.MapGet/MapPost/MapPut/MapDelete)
- Route attributes ([Route], [HttpGet], [HttpPost], etc.)
- Action filters ([ServiceFilter], [TypeFilter], [ActionFilter])
- API versioning ([ApiVersion])
- Authorization attributes ([Authorize], [AllowAnonymous])
- Content negotiation ([Produces], [Consumes])
- Model binding ([FromBody], [FromQuery], [FromRoute], [FromHeader], [FromServices])

Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AspNetEndpointInfo:
    """Information about an ASP.NET Core endpoint."""
    method: str = ""                   # GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
    path: str = ""                     # Route template
    handler_method: str = ""           # Method name
    controller: str = ""               # Controller class name
    return_type: str = ""              # Return type (IActionResult, ActionResult<T>, etc.)
    parameters: List[Dict[str, str]] = field(default_factory=list)  # [{name, type, source}]
    is_authorized: bool = False        # Has [Authorize]
    is_anonymous: bool = False         # Has [AllowAnonymous]
    produces: List[str] = field(default_factory=list)  # [Produces] types
    consumes: List[str] = field(default_factory=list)  # [Consumes] types
    api_version: str = ""              # [ApiVersion] value
    filters: List[str] = field(default_factory=list)   # Applied filters
    response_types: List[Dict[str, str]] = field(default_factory=list)  # [ProducesResponseType]
    file: str = ""
    line_number: int = 0


@dataclass
class AspNetControllerInfo:
    """Information about an ASP.NET Core controller."""
    name: str = ""
    base_class: str = ""               # ControllerBase, Controller, etc.
    route_prefix: str = ""             # [Route("api/[controller]")]
    is_api_controller: bool = False    # [ApiController]
    api_version: str = ""              # [ApiVersion]
    area: str = ""                     # [Area]
    authorization: str = ""            # [Authorize(Policy="...")]
    endpoints: List[AspNetEndpointInfo] = field(default_factory=list)
    filters: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class AspNetMinimalApiInfo:
    """Information about a Minimal API endpoint."""
    method: str = ""                   # GET, POST, etc.
    path: str = ""                     # Route pattern
    handler: str = ""                  # Lambda or method group
    group: str = ""                    # MapGroup name
    is_authorized: bool = False
    produces: List[str] = field(default_factory=list)
    with_metadata: List[str] = field(default_factory=list)  # WithName, WithTags, etc.
    file: str = ""
    line_number: int = 0


@dataclass
class AspNetFilterInfo:
    """Information about an ASP.NET Core filter."""
    name: str = ""
    kind: str = ""  # action, result, exception, authorization, resource
    implements: List[str] = field(default_factory=list)
    is_global: bool = False
    file: str = ""
    line_number: int = 0


class AspNetCoreControllerExtractor:
    """Extracts ASP.NET Core controllers, endpoints, and Minimal API definitions."""

    # MVC Controller patterns
    CONTROLLER_PATTERN = re.compile(
        r'(?:\[(?:ApiController|Route\(["\']([^"\']*)["\'])\)\]\s*)*'
        r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)\s*:\s*(Controller(?:Base)?|ControllerBase)',
        re.MULTILINE
    )

    # Route attribute on controller
    ROUTE_ATTR_PATTERN = re.compile(
        r'\[Route\(["\']([^"\']+)["\']\)\]',
        re.MULTILINE
    )

    # API Controller attribute
    API_CONTROLLER_PATTERN = re.compile(
        r'\[ApiController\]',
        re.MULTILINE
    )

    # HTTP method attributes
    HTTP_METHOD_PATTERNS = {
        'GET': re.compile(r'\[HttpGet(?:\(["\']([^"\']*)["\'])?\)\]', re.MULTILINE),
        'POST': re.compile(r'\[HttpPost(?:\(["\']([^"\']*)["\'])?\)\]', re.MULTILINE),
        'PUT': re.compile(r'\[HttpPut(?:\(["\']([^"\']*)["\'])?\)\]', re.MULTILINE),
        'DELETE': re.compile(r'\[HttpDelete(?:\(["\']([^"\']*)["\'])?\)\]', re.MULTILINE),
        'PATCH': re.compile(r'\[HttpPatch(?:\(["\']([^"\']*)["\'])?\)\]', re.MULTILINE),
        'HEAD': re.compile(r'\[HttpHead(?:\(["\']([^"\']*)["\'])?\)\]', re.MULTILINE),
        'OPTIONS': re.compile(r'\[HttpOptions(?:\(["\']([^"\']*)["\'])?\)\]', re.MULTILINE),
    }

    # Authorize attribute
    AUTHORIZE_PATTERN = re.compile(
        r'\[Authorize(?:\((?:Policy\s*=\s*["\']([^"\']+)["\']|Roles\s*=\s*["\']([^"\']+)["\']|'
        r'AuthenticationSchemes\s*=\s*["\']([^"\']+)["\'])?\))?\]',
        re.MULTILINE
    )

    # AllowAnonymous
    ALLOW_ANONYMOUS_PATTERN = re.compile(r'\[AllowAnonymous\]', re.MULTILINE)

    # ApiVersion
    API_VERSION_PATTERN = re.compile(
        r'\[ApiVersion\(["\']([^"\']+)["\']\)\]',
        re.MULTILINE
    )

    # ProducesResponseType
    PRODUCES_RESPONSE_PATTERN = re.compile(
        r'\[ProducesResponseType\((?:typeof\((\w+)\),\s*)?(?:StatusCodes\.)?(\d+|Status\w+)\)\]',
        re.MULTILINE
    )

    # Action method pattern (public method in controller)
    ACTION_METHOD_PATTERN = re.compile(
        r'(?:(?:\[(?:HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch|HttpHead|HttpOptions)'
        r'(?:\([^\)]*\))?\]\s*)+)'
        r'(?:\[(?:Authorize|AllowAnonymous|ProducesResponseType|Produces|Consumes)'
        r'(?:\([^\)]*\))?\]\s*)*'
        r'public\s+(?:async\s+)?(\w+(?:<\w+>)?)\s+(\w+)\s*\(([^)]*)\)',
        re.MULTILINE | re.DOTALL
    )

    # Minimal API patterns
    MINIMAL_API_PATTERN = re.compile(
        r'(?:app|group|endpoints?)\s*\.\s*Map(Get|Post|Put|Delete|Patch)\s*\(\s*["\']([^"\']+)["\']\s*,',
        re.MULTILINE
    )

    # MapGroup
    MAP_GROUP_PATTERN = re.compile(
        r'\.MapGroup\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    # Produces/Consumes
    PRODUCES_PATTERN = re.compile(
        r'\[Produces\(["\']([^"\']+)["\']\)\]',
        re.MULTILINE
    )
    CONSUMES_PATTERN = re.compile(
        r'\[Consumes\(["\']([^"\']+)["\']\)\]',
        re.MULTILINE
    )

    # Parameter binding
    PARAM_BINDING_PATTERN = re.compile(
        r'\[From(Body|Query|Route|Header|Services|Form)\]\s*(\w+(?:<[^>]+>)?)\s+(\w+)',
        re.MULTILINE
    )

    # Filter patterns  
    FILTER_PATTERNS = {
        'action': re.compile(r'class\s+(\w+)\s*:\s*(?:I?ActionFilter(?:Attribute)?|ActionFilterAttribute)', re.MULTILINE),
        'result': re.compile(r'class\s+(\w+)\s*:\s*(?:I?ResultFilter(?:Attribute)?|ResultFilterAttribute)', re.MULTILINE),
        'exception': re.compile(r'class\s+(\w+)\s*:\s*(?:I?ExceptionFilter(?:Attribute)?|ExceptionFilterAttribute)', re.MULTILINE),
        'authorization': re.compile(r'class\s+(\w+)\s*:\s*(?:I?AuthorizationFilter|AuthorizationFilterAttribute)', re.MULTILINE),
        'resource': re.compile(r'class\s+(\w+)\s*:\s*(?:I?ResourceFilter|ResourceFilterAttribute)', re.MULTILINE),
    }

    # Area attribute
    AREA_PATTERN = re.compile(r'\[Area\(["\'](\w+)["\']\)\]', re.MULTILINE)

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract ASP.NET Core controllers, endpoints, and Minimal APIs."""
        result = {
            'controllers': [],
            'minimal_apis': [],
            'filters': [],
        }

        if not content or not content.strip():
            return result

        # Extract MVC Controllers
        result['controllers'] = self._extract_controllers(content, file_path)

        # Extract Minimal API endpoints
        result['minimal_apis'] = self._extract_minimal_apis(content, file_path)

        # Extract filters
        result['filters'] = self._extract_filters(content, file_path)

        return result

    def _extract_controllers(self, content: str, file_path: str) -> List[AspNetControllerInfo]:
        """Extract MVC controller definitions and their action methods."""
        controllers = []

        # Find controller classes
        # More permissive pattern for controller detection
        ctrl_pattern = re.compile(
            r'(?:(?:\[[^\]]+\]\s*)*)'
            r'public\s+(?:abstract\s+)?(?:partial\s+)?class\s+(\w+Controller)\s*:\s*(\w+)',
            re.MULTILINE
        )

        for match in ctrl_pattern.finditer(content):
            ctrl_name = match.group(1)
            base_class = match.group(2)

            # Check if it's a legitimate controller base
            if base_class not in ('Controller', 'ControllerBase', 'ApiController',
                                   'ODataController', 'HubController'):
                # Check if base class ends with Controller
                if not base_class.endswith('Controller') and not base_class.endswith('ControllerBase'):
                    continue

            ctrl_start = match.start()
            line_num = content[:ctrl_start].count('\n') + 1

            # Look for attributes before the class
            pre_class = content[max(0, ctrl_start - 500):ctrl_start]

            # Route prefix
            route_match = self.ROUTE_ATTR_PATTERN.search(pre_class)
            route_prefix = route_match.group(1) if route_match else ""

            # API Controller
            is_api = bool(self.API_CONTROLLER_PATTERN.search(pre_class))

            # API Version
            ver_match = self.API_VERSION_PATTERN.search(pre_class)
            api_version = ver_match.group(1) if ver_match else ""

            # Area
            area_match = self.AREA_PATTERN.search(pre_class)
            area = area_match.group(1) if area_match else ""

            # Authorization
            auth_match = self.AUTHORIZE_PATTERN.search(pre_class)
            authorization = ""
            if auth_match:
                authorization = auth_match.group(1) or auth_match.group(2) or "default"

            # Extract controller body (find matching braces)
            body_start = content.find('{', match.end())
            if body_start == -1:
                continue
            body = self._extract_body(content, body_start)

            # Extract endpoints from controller body
            endpoints = self._extract_endpoints(body, ctrl_name, route_prefix, file_path, line_num)

            controllers.append(AspNetControllerInfo(
                name=ctrl_name,
                base_class=base_class,
                route_prefix=route_prefix,
                is_api_controller=is_api,
                api_version=api_version,
                area=area,
                authorization=authorization,
                endpoints=endpoints,
                file=file_path,
                line_number=line_num,
            ))

        return controllers

    def _extract_endpoints(self, body: str, ctrl_name: str, route_prefix: str,
                           file_path: str, base_line: int) -> List[AspNetEndpointInfo]:
        """Extract action method endpoints from controller body."""
        endpoints = []

        for http_method, pattern in self.HTTP_METHOD_PATTERNS.items():
            for match in pattern.finditer(body):
                route = match.group(1) if match.group(1) else ""
                attr_pos = match.start()

                # Look ahead for method declaration
                after_attr = body[match.end():]
                method_match = re.search(
                    r'(?:\[[^\]]+\]\s*)*public\s+(?:async\s+)?'
                    r'([\w<>,\s]+?)\s+(\w+)\s*\(([^)]*)\)',
                    after_attr[:500]
                )

                if method_match:
                    return_type = method_match.group(1).strip()
                    method_name = method_match.group(2)
                    params_str = method_match.group(3)

                    # Parse parameters
                    parameters = self._parse_parameters(params_str)

                    # Check auth
                    pre_method = body[max(0, attr_pos - 200):attr_pos]
                    is_authorized = bool(self.AUTHORIZE_PATTERN.search(pre_method))
                    is_anonymous = bool(self.ALLOW_ANONYMOUS_PATTERN.search(pre_method))

                    # Full path
                    full_path = route_prefix
                    if route:
                        if full_path and not full_path.endswith('/'):
                            full_path += '/'
                        full_path += route

                    line = base_line + body[:attr_pos].count('\n')

                    endpoints.append(AspNetEndpointInfo(
                        method=http_method,
                        path=full_path or route_prefix,
                        handler_method=method_name,
                        controller=ctrl_name,
                        return_type=return_type,
                        parameters=parameters,
                        is_authorized=is_authorized,
                        is_anonymous=is_anonymous,
                        file=file_path,
                        line_number=line,
                    ))

        return endpoints

    def _extract_minimal_apis(self, content: str, file_path: str) -> List[AspNetMinimalApiInfo]:
        """Extract Minimal API endpoint definitions."""
        apis = []

        # Extract MapGroup definitions
        groups = {}
        for match in self.MAP_GROUP_PATTERN.finditer(content):
            groups[match.start()] = match.group(1)

        for match in self.MINIMAL_API_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line = content[:match.start()].count('\n') + 1

            # Check for chained metadata
            after = content[match.end():match.end() + 500]
            with_metadata = []
            for meta_match in re.finditer(r'\.(WithName|WithTags|WithDescription|RequireAuthorization|'
                                          r'AllowAnonymous|WithOpenApi|Produces|ProducesProblem|'
                                          r'AddEndpointFilter)\s*\(', after):
                with_metadata.append(meta_match.group(1))

            is_authorized = 'RequireAuthorization' in with_metadata

            apis.append(AspNetMinimalApiInfo(
                method=method,
                path=path,
                handler="lambda" if '=>' in content[match.end():match.end() + 200] else "method_group",
                is_authorized=is_authorized,
                with_metadata=with_metadata,
                file=file_path,
                line_number=line,
            ))

        return apis

    def _extract_filters(self, content: str, file_path: str) -> List[AspNetFilterInfo]:
        """Extract ASP.NET Core filter definitions."""
        filters = []
        for kind, pattern in self.FILTER_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content[:match.start()].count('\n') + 1
                filters.append(AspNetFilterInfo(
                    name=match.group(1),
                    kind=kind,
                    file=file_path,
                    line_number=line,
                ))
        return filters

    def _parse_parameters(self, params_str: str) -> List[Dict[str, str]]:
        """Parse method parameters including binding attributes."""
        params = []
        if not params_str.strip():
            return params

        # Split by comma (handling generics)
        depth = 0
        current = ""
        for ch in params_str:
            if ch in ('<', '('):
                depth += 1
            elif ch in ('>', ')'):
                depth -= 1
            elif ch == ',' and depth == 0:
                if current.strip():
                    params.append(self._parse_single_param(current.strip()))
                current = ""
                continue
            current += ch

        if current.strip():
            params.append(self._parse_single_param(current.strip()))

        return params

    def _parse_single_param(self, param_str: str) -> Dict[str, str]:
        """Parse a single parameter with optional binding attribute."""
        source = ""
        binding_match = re.match(
            r'\[From(Body|Query|Route|Header|Services|Form)\]\s*(.+)',
            param_str
        )
        if binding_match:
            source = binding_match.group(1).lower()
            param_str = binding_match.group(2)

        parts = param_str.strip().split()
        if len(parts) >= 2:
            return {"name": parts[-1], "type": ' '.join(parts[:-1]), "source": source}
        elif len(parts) == 1:
            return {"name": parts[0], "type": "", "source": source}
        return {"name": "", "type": "", "source": source}

    def _extract_body(self, content: str, start: int) -> str:
        """Extract content between matching braces."""
        depth = 0
        i = start
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[start + 1:i]
            i += 1
        return content[start + 1:]
