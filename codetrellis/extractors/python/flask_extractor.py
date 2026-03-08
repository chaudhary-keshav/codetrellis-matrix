"""
FlaskExtractor - Extracts Flask route definitions from Python source code.

This extractor parses Flask routes and extracts:
- Route decorators (@app.route, @blueprint.route)
- HTTP methods
- URL rules and variables
- View functions
- Blueprints
- URL converters

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class FlaskRouteInfo:
    """Information about a Flask route."""
    path: str
    methods: List[str] = field(default_factory=list)
    handler: str = ""
    url_variables: List[str] = field(default_factory=list)
    endpoint: Optional[str] = None
    is_static: bool = False
    blueprint: Optional[str] = None
    line_number: int = 0


@dataclass
class FlaskBlueprintInfo:
    """Information about a Flask Blueprint."""
    name: str
    variable_name: str
    url_prefix: str = ""
    static_folder: Optional[str] = None
    template_folder: Optional[str] = None
    routes: List[FlaskRouteInfo] = field(default_factory=list)


class FlaskExtractor:
    """
    Extracts Flask route definitions from source code.

    Handles:
    - @app.route() decorators
    - @blueprint.route() decorators
    - @app.get(), @app.post(), etc. (Flask 2.0+)
    - Blueprint definitions
    - URL variables with converters (<int:id>, <string:name>)
    - Multiple methods per route
    """

    # HTTP methods
    HTTP_METHODS = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']

    # Route decorator pattern
    ROUTE_DECORATOR_PATTERN = re.compile(
        r'@(\w+)\.route\s*\(\s*[\'"]([^"\']+)[\'"](?:\s*,\s*([^)]+))?\s*\)',
        re.MULTILINE
    )

    # Method-specific decorator pattern (Flask 2.0+)
    METHOD_DECORATOR_PATTERN = re.compile(
        r'@(\w+)\.(' + '|'.join(HTTP_METHODS) + r')\s*\(\s*[\'"]([^"\']+)[\'"](?:\s*,\s*([^)]+))?\s*\)',
        re.MULTILINE | re.IGNORECASE
    )

    # Function definition pattern
    FUNCTION_PATTERN = re.compile(
        r'(async\s+)?def\s+(\w+)\s*\(\s*([^)]*)\s*\)(?:\s*->\s*([^:]+))?\s*:',
        re.MULTILINE
    )

    # Blueprint definition pattern
    BLUEPRINT_PATTERN = re.compile(
        r'(\w+)\s*=\s*Blueprint\s*\(\s*[\'"](\w+)[\'"](?:\s*,\s*([^)]+))?\s*\)',
        re.MULTILINE
    )

    # URL variable pattern
    URL_VARIABLE_PATTERN = re.compile(r'<(?:(\w+):)?(\w+)>')

    def __init__(self):
        """Initialize the Flask extractor."""
        self._blueprints: Dict[str, FlaskBlueprintInfo] = {}

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all Flask routes and blueprints from Python content.

        Args:
            content: Python source code

        Returns:
            Dict containing 'routes' and 'blueprints'
        """
        # Extract blueprints first
        blueprints = self._extract_blueprints(content)
        self._blueprints = {bp.variable_name: bp for bp in blueprints}

        # Extract routes
        routes = self._extract_routes(content)

        return {
            'routes': routes,
            'blueprints': blueprints
        }

    def _extract_blueprints(self, content: str) -> List[FlaskBlueprintInfo]:
        """Extract Blueprint definitions."""
        blueprints = []

        for match in self.BLUEPRINT_PATTERN.finditer(content):
            var_name = match.group(1)
            bp_name = match.group(2)
            bp_args = match.group(3) or ""

            # Extract url_prefix
            prefix_match = re.search(r'url_prefix\s*=\s*[\'"]([^"\']*)[\'"]', bp_args)
            url_prefix = prefix_match.group(1) if prefix_match else ""

            # Extract static_folder
            static_match = re.search(r'static_folder\s*=\s*[\'"]([^"\']+)[\'"]', bp_args)
            static_folder = static_match.group(1) if static_match else None

            # Extract template_folder
            template_match = re.search(r'template_folder\s*=\s*[\'"]([^"\']+)[\'"]', bp_args)
            template_folder = template_match.group(1) if template_match else None

            blueprints.append(FlaskBlueprintInfo(
                name=bp_name,
                variable_name=var_name,
                url_prefix=url_prefix,
                static_folder=static_folder,
                template_folder=template_folder
            ))

        return blueprints

    def _extract_routes(self, content: str) -> List[FlaskRouteInfo]:
        """Extract route definitions."""
        routes = []

        # Extract @app.route or @blueprint.route
        for match in self.ROUTE_DECORATOR_PATTERN.finditer(content):
            route = self._parse_route_decorator(content, match, None)
            if route:
                routes.append(route)

        # Extract @app.get, @app.post, etc. (Flask 2.0+)
        for match in self.METHOD_DECORATOR_PATTERN.finditer(content):
            route = self._parse_method_decorator(content, match)
            if route:
                routes.append(route)

        return routes

    def _parse_route_decorator(self, content: str, match: re.Match, forced_method: Optional[str]) -> Optional[FlaskRouteInfo]:
        """Parse a @route() decorator."""
        app_or_bp = match.group(1)
        path = match.group(2)
        route_args = match.group(3) or ""

        # Extract methods
        methods = ['GET']  # Default
        methods_match = re.search(r'methods\s*=\s*\[([^\]]+)\]', route_args)
        if methods_match:
            methods = re.findall(r'[\'"](\w+)[\'"]', methods_match.group(1))
            methods = [m.upper() for m in methods]

        if forced_method:
            methods = [forced_method.upper()]

        # Extract endpoint
        endpoint_match = re.search(r'endpoint\s*=\s*[\'"](\w+)[\'"]', route_args)
        endpoint = endpoint_match.group(1) if endpoint_match else None

        # Find the function definition after the decorator
        remaining_content = content[match.end():]
        func_match = self.FUNCTION_PATTERN.search(remaining_content)

        if not func_match:
            return None

        handler = func_match.group(2)

        # Extract URL variables
        url_variables = self._extract_url_variables(path)

        # Calculate line number
        line_number = content[:match.start()].count('\n') + 1

        # Check if it's a blueprint route
        blueprint = None
        if app_or_bp in self._blueprints:
            blueprint = app_or_bp

        return FlaskRouteInfo(
            path=path,
            methods=methods,
            handler=handler,
            url_variables=url_variables,
            endpoint=endpoint,
            blueprint=blueprint,
            line_number=line_number
        )

    def _parse_method_decorator(self, content: str, match: re.Match) -> Optional[FlaskRouteInfo]:
        """Parse a @app.get(), @app.post() decorator."""
        app_or_bp = match.group(1)
        method = match.group(2).upper()
        path = match.group(3)
        route_args = match.group(4) or ""

        # Extract endpoint
        endpoint_match = re.search(r'endpoint\s*=\s*[\'"](\w+)[\'"]', route_args)
        endpoint = endpoint_match.group(1) if endpoint_match else None

        # Find the function definition after the decorator
        remaining_content = content[match.end():]
        func_match = self.FUNCTION_PATTERN.search(remaining_content)

        if not func_match:
            return None

        handler = func_match.group(2)

        # Extract URL variables
        url_variables = self._extract_url_variables(path)

        # Calculate line number
        line_number = content[:match.start()].count('\n') + 1

        # Check if it's a blueprint route
        blueprint = None
        if app_or_bp in self._blueprints:
            blueprint = app_or_bp

        return FlaskRouteInfo(
            path=path,
            methods=[method],
            handler=handler,
            url_variables=url_variables,
            endpoint=endpoint,
            blueprint=blueprint,
            line_number=line_number
        )

    def _extract_url_variables(self, path: str) -> List[str]:
        """Extract URL variables from a path."""
        variables = []
        for match in self.URL_VARIABLE_PATTERN.finditer(path):
            converter = match.group(1) or 'string'
            name = match.group(2)
            variables.append(f"{name}:{converter}")
        return variables

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """
        Convert extracted Flask data to CodeTrellis format.

        Args:
            result: Dict with 'routes' and 'blueprints'

        Returns:
            CodeTrellis formatted string
        """
        lines = []

        # Add blueprints
        blueprints = result.get('blueprints', [])
        if blueprints:
            lines.append("[FLASK_BLUEPRINTS]")
            for bp in blueprints:
                parts = [f"{bp.variable_name}|name:{bp.name}"]
                if bp.url_prefix:
                    parts.append(f"prefix:{bp.url_prefix}")
                lines.append("|".join(parts))
            lines.append("")

        # Add routes
        routes = result.get('routes', [])
        if routes:
            lines.append("[FLASK_ROUTES]")

            for route in routes:
                methods_str = ','.join(route.methods)
                parts = [f"{methods_str} {route.path} → {route.handler}"]

                if route.url_variables:
                    parts.append(f"vars:[{','.join(route.url_variables)}]")

                if route.blueprint:
                    parts.append(f"bp:{route.blueprint}")

                if route.endpoint:
                    parts.append(f"ep:{route.endpoint}")

                lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_flask_routes(content: str) -> Dict[str, Any]:
    """Extract Flask routes and blueprints from Python content."""
    extractor = FlaskExtractor()
    return extractor.extract(content)
