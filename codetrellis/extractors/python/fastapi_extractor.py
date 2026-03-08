"""
FastAPIExtractor - Extracts FastAPI route definitions from Python source code.

This extractor parses FastAPI route decorators and extracts:
- Route paths and HTTP methods
- Path parameters, query parameters, body parameters
- Dependencies (Depends)
- Response models
- Status codes and tags
- APIRouter definitions

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class FastAPIParameterInfo:
    """Information about a FastAPI parameter."""
    name: str
    type: str
    source: str  # path, query, body, header, cookie, depends
    required: bool = True
    default: Optional[str] = None
    description: Optional[str] = None


@dataclass
class FastAPIDependencyInfo:
    """Information about a FastAPI dependency."""
    name: str
    dependency_func: str
    parameter_name: Optional[str] = None


@dataclass
class FastAPIRouteInfo:
    """Complete information about a FastAPI route."""
    method: str  # GET, POST, PUT, DELETE, PATCH
    path: str
    handler: str
    parameters: List[FastAPIParameterInfo] = field(default_factory=list)
    dependencies: List[FastAPIDependencyInfo] = field(default_factory=list)
    response_model: Optional[str] = None
    status_code: int = 200
    tags: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    is_async: bool = False
    line_number: int = 0


@dataclass
class FastAPIRouterInfo:
    """Information about an APIRouter."""
    name: str
    prefix: str = ""
    tags: List[str] = field(default_factory=list)
    routes: List[FastAPIRouteInfo] = field(default_factory=list)


class FastAPIExtractor:
    """
    Extracts FastAPI route definitions from source code.

    Handles:
    - @app.get, @app.post, @app.put, @app.delete, @app.patch decorators
    - @router.get, etc. for APIRouter
    - Path, Query, Body, Header, Cookie parameters
    - Depends() for dependency injection
    - response_model, status_code, tags
    - Async route handlers
    """

    # HTTP methods
    HTTP_METHODS = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']

    # Pattern for route decorators
    ROUTE_DECORATOR_PATTERN = re.compile(
        r'@(\w+)\.(' + '|'.join(HTTP_METHODS) + r')\s*\(\s*([^)]*)\s*\)',
        re.MULTILINE | re.IGNORECASE
    )

    # Pattern for function definition following decorator
    FUNCTION_PATTERN = re.compile(
        r'(async\s+)?def\s+(\w+)\s*\(\s*([^)]*)\s*\)(?:\s*->\s*([^:]+))?\s*:',
        re.MULTILINE
    )

    # Pattern for APIRouter definition
    ROUTER_PATTERN = re.compile(
        r'(\w+)\s*=\s*APIRouter\s*\(\s*([^)]*)\s*\)',
        re.MULTILINE
    )

    # Pattern for Depends
    DEPENDS_PATTERN = re.compile(
        r'Depends\s*\(\s*(\w+)\s*\)'
    )

    # Pattern for typed parameters
    TYPED_PARAM_PATTERN = re.compile(
        r'(\w+)\s*:\s*([^=,]+?)(?:\s*=\s*(.+?))?(?:,|$)'
    )

    def __init__(self):
        """Initialize the FastAPI extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all FastAPI routes and routers from Python content.

        Args:
            content: Python source code

        Returns:
            Dict containing 'routes' and 'routers'
        """
        # Extract routers first
        routers = self._extract_routers(content)

        # Extract routes
        routes = self._extract_routes(content)

        return {
            'routes': routes,
            'routers': routers
        }

    def _extract_routers(self, content: str) -> List[FastAPIRouterInfo]:
        """Extract APIRouter definitions."""
        routers = []

        for match in self.ROUTER_PATTERN.finditer(content):
            router_name = match.group(1)
            router_args = match.group(2)

            prefix = ""
            tags = []

            # Extract prefix
            prefix_match = re.search(r'prefix\s*=\s*[\'"]([^"\']+)[\'"]', router_args)
            if prefix_match:
                prefix = prefix_match.group(1)

            # Extract tags
            tags_match = re.search(r'tags\s*=\s*\[([^\]]+)\]', router_args)
            if tags_match:
                tags = re.findall(r'[\'"](\w+)[\'"]', tags_match.group(1))

            routers.append(FastAPIRouterInfo(
                name=router_name,
                prefix=prefix,
                tags=tags
            ))

        return routers

    def _extract_routes(self, content: str) -> List[FastAPIRouteInfo]:
        """Extract route definitions."""
        routes = []

        # Find all route decorators
        for decorator_match in self.ROUTE_DECORATOR_PATTERN.finditer(content):
            app_or_router = decorator_match.group(1)
            http_method = decorator_match.group(2).upper()
            decorator_args = decorator_match.group(3)

            # Parse decorator arguments
            path = self._extract_path(decorator_args)
            response_model = self._extract_response_model(decorator_args)
            status_code = self._extract_status_code(decorator_args)
            tags = self._extract_tags(decorator_args)
            summary = self._extract_summary(decorator_args)

            # Find the function definition after the decorator
            remaining_content = content[decorator_match.end():]
            func_match = self.FUNCTION_PATTERN.search(remaining_content)

            if not func_match:
                continue

            is_async = func_match.group(1) is not None
            handler_name = func_match.group(2)
            params_str = func_match.group(3)
            return_type = func_match.group(4)

            # Parse parameters
            parameters, dependencies = self._parse_parameters(params_str)

            # Calculate line number
            line_number = content[:decorator_match.start()].count('\n') + 1

            route = FastAPIRouteInfo(
                method=http_method,
                path=path,
                handler=handler_name,
                parameters=parameters,
                dependencies=dependencies,
                response_model=response_model or return_type,
                status_code=status_code,
                tags=tags,
                summary=summary,
                is_async=is_async,
                line_number=line_number
            )

            routes.append(route)

        return routes

    def _extract_path(self, decorator_args: str) -> str:
        """Extract path from decorator arguments."""
        # First argument should be the path
        path_match = re.search(r'^[\'"]([^"\']+)[\'"]', decorator_args.strip())
        if path_match:
            return path_match.group(1)

        # Or it might be named
        path_match = re.search(r'path\s*=\s*[\'"]([^"\']+)[\'"]', decorator_args)
        if path_match:
            return path_match.group(1)

        return "/"

    def _extract_response_model(self, decorator_args: str) -> Optional[str]:
        """Extract response_model from decorator arguments."""
        match = re.search(r'response_model\s*=\s*(\w+)', decorator_args)
        if match:
            return match.group(1)
        return None

    def _extract_status_code(self, decorator_args: str) -> int:
        """Extract status_code from decorator arguments."""
        match = re.search(r'status_code\s*=\s*(\d+)', decorator_args)
        if match:
            return int(match.group(1))

        # Check for status.HTTP_XXX constants
        match = re.search(r'status_code\s*=\s*status\.HTTP_(\d+)', decorator_args)
        if match:
            return int(match.group(1))

        return 200

    def _extract_tags(self, decorator_args: str) -> List[str]:
        """Extract tags from decorator arguments."""
        match = re.search(r'tags\s*=\s*\[([^\]]+)\]', decorator_args)
        if match:
            return re.findall(r'[\'"](\w+)[\'"]', match.group(1))
        return []

    def _extract_summary(self, decorator_args: str) -> Optional[str]:
        """Extract summary from decorator arguments."""
        match = re.search(r'summary\s*=\s*[\'"]([^"\']+)[\'"]', decorator_args)
        if match:
            return match.group(1)
        return None

    def _parse_parameters(self, params_str: str) -> tuple[List[FastAPIParameterInfo], List[FastAPIDependencyInfo]]:
        """Parse function parameters into FastAPI parameters and dependencies."""
        parameters = []
        dependencies = []

        if not params_str.strip():
            return parameters, dependencies

        # Split parameters (handling nested brackets)
        param_parts = self._split_params(params_str)

        for param in param_parts:
            param = param.strip()
            if not param:
                continue

            # Parse the parameter
            param_info = self._parse_single_parameter(param)
            if param_info:
                if isinstance(param_info, FastAPIDependencyInfo):
                    dependencies.append(param_info)
                else:
                    parameters.append(param_info)

        return parameters, dependencies

    def _parse_single_parameter(self, param: str) -> Optional[FastAPIParameterInfo | FastAPIDependencyInfo]:
        """Parse a single parameter string."""
        # Skip self
        if param.strip() == 'self':
            return None

        # Check for type annotation
        if ':' not in param:
            return None

        name_part, type_part = param.split(':', 1)
        name = name_part.strip()

        # Check for default value
        default = None
        if '=' in type_part:
            type_str, default_part = type_part.split('=', 1)
            type_str = type_str.strip()
            default_part = default_part.strip()

            # Check for Depends
            depends_match = self.DEPENDS_PATTERN.search(default_part)
            if depends_match:
                dep_func = depends_match.group(1)
                return FastAPIDependencyInfo(
                    name=name,
                    dependency_func=dep_func,
                    parameter_name=name
                )

            # Check for Path, Query, Body, etc.
            source = self._determine_source(default_part)
            default = self._extract_default(default_part)
            required = '...' in default_part or default is None

            return FastAPIParameterInfo(
                name=name,
                type=type_str,
                source=source,
                required=required,
                default=default
            )
        else:
            type_str = type_part.strip()

            # Determine source from type or position
            # Path parameters are usually just annotated without default
            source = 'path' if '{' in param else 'query'

            return FastAPIParameterInfo(
                name=name,
                type=type_str,
                source=source,
                required=True
            )

    def _determine_source(self, default_part: str) -> str:
        """Determine the source of a parameter (path, query, body, etc.)."""
        sources = ['Path', 'Query', 'Body', 'Header', 'Cookie', 'File', 'Form']
        for source in sources:
            if source + '(' in default_part:
                return source.lower()
        return 'query'

    def _extract_default(self, default_part: str) -> Optional[str]:
        """Extract the default value from a parameter default."""
        # If it's a Path(), Query(), etc., extract the default
        match = re.search(r'\(\s*([^,)]+)', default_part)
        if match:
            default = match.group(1).strip()
            if default == '...':
                return None
            if default.startswith('"') or default.startswith("'"):
                return default[1:-1]
            if default not in ('None', 'True', 'False') and not default.isdigit():
                return None
            return default
        return None

    def _split_params(self, params_str: str) -> List[str]:
        """Split parameters handling nested brackets."""
        params = []
        current = ""
        depth = 0

        for char in params_str:
            if char in '([{':
                depth += 1
            elif char in ')]}':
                depth -= 1
            elif char == ',' and depth == 0:
                params.append(current)
                current = ""
                continue
            current += char

        if current.strip():
            params.append(current)

        return params

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """
        Convert extracted FastAPI data to CodeTrellis format.

        Args:
            result: Dict with 'routes' and 'routers'

        Returns:
            CodeTrellis formatted string
        """
        lines = []

        # Add routers
        routers = result.get('routers', [])
        if routers:
            lines.append("[FASTAPI_ROUTERS]")
            for router in routers:
                tags_str = f"tags:[{','.join(router.tags)}]" if router.tags else ""
                lines.append(f"{router.name}|prefix:{router.prefix}|{tags_str}")
            lines.append("")

        # Add routes
        routes = result.get('routes', [])
        if routes:
            lines.append("[FASTAPI_ROUTES]")
            for route in routes:
                parts = [f"{route.method} {route.path} → {route.handler}"]

                # Add parameters
                if route.parameters:
                    param_strs = []
                    for p in route.parameters:
                        req = "!" if p.required else ""
                        default_str = f"={p.default}" if p.default else ""
                        param_strs.append(f"{p.name}:{p.type}@{p.source}{req}{default_str}")
                    parts.append(f"params:[{','.join(param_strs)}]")

                # Add dependencies
                if route.dependencies:
                    dep_strs = [d.dependency_func for d in route.dependencies]
                    parts.append(f"deps:[{','.join(dep_strs)}]")

                # Add response model
                if route.response_model:
                    parts.append(f"response:{route.response_model}")

                # Add status code if not 200
                if route.status_code != 200:
                    parts.append(f"status:{route.status_code}")

                lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_fastapi_routes(content: str) -> Dict[str, Any]:
    """Extract FastAPI routes and routers from Python content."""
    extractor = FastAPIExtractor()
    return extractor.extract(content)
