"""
Apache Camel Route Extractor - Extracts route definitions and endpoints.

Extracts:
- RouteBuilder / EndpointRouteBuilder classes
- from() / to() / toD() endpoint URIs
- Route IDs, descriptions, auto-startup settings
- Direct, SEDA, timer, and other internal endpoints
- Endpoint properties and options
- Route groups and policies
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class CamelEndpointInfo:
    """Information about a Camel endpoint."""
    uri: str = ""
    component: str = ""  # extracted from URI scheme
    direction: str = ""  # from, to, toD, wireTap
    options: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0


@dataclass
class CamelRouteInfo:
    """Information about a Camel route."""
    route_id: str = ""
    description: str = ""
    from_endpoint: str = ""
    from_component: str = ""
    to_endpoints: List[CamelEndpointInfo] = field(default_factory=list)
    route_builder_class: str = ""
    auto_startup: bool = True
    is_rest_route: bool = False
    route_policy: str = ""
    log_name: str = ""
    line_number: int = 0


class CamelRouteExtractor:
    """Extracts Apache Camel route definitions and endpoints."""

    # RouteBuilder class
    ROUTE_BUILDER_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+extends\s+'
        r'(?:RouteBuilder|EndpointRouteBuilder|'
        r'AdviceWithRouteBuilder|SpringRouteBuilder)',
        re.MULTILINE
    )

    # from() endpoint
    FROM_PATTERN = re.compile(
        r'from\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # to() / toD() / toF() endpoints
    TO_PATTERN = re.compile(
        r'\.to\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    TO_D_PATTERN = re.compile(
        r'\.toD\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    TO_F_PATTERN = re.compile(
        r'\.toF\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    WIRE_TAP_PATTERN = re.compile(
        r'\.wireTap\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Route ID
    ROUTE_ID_PATTERN = re.compile(
        r'\.routeId\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Route description
    ROUTE_DESCRIPTION_PATTERN = re.compile(
        r'\.description\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Auto startup
    AUTO_STARTUP_PATTERN = re.compile(
        r'\.autoStartup\s*\(\s*(true|false|["\'][^"\']+["\'])',
        re.MULTILINE
    )

    # Route policy
    ROUTE_POLICY_PATTERN = re.compile(
        r'\.routePolicy\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # Log name
    LOG_NAME_PATTERN = re.compile(
        r'\.log\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Configure method
    CONFIGURE_METHOD_PATTERN = re.compile(
        r'(?:@Override\s*)?(?:public\s+)?void\s+configure\s*\(\s*\)',
        re.MULTILINE
    )

    # Lambda route builder (Camel 3.x+)
    LAMBDA_ROUTE_PATTERN = re.compile(
        r'(?:addRouteBuilder|addRoutesToCamelContext)\s*\(',
        re.MULTILINE
    )

    @staticmethod
    def _extract_component(uri: str) -> str:
        """Extract component name from endpoint URI."""
        if ':' in uri:
            return uri.split(':')[0].strip()
        return uri.strip()

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract route definitions and endpoints."""
        routes: List[CamelRouteInfo] = []
        endpoints: List[CamelEndpointInfo] = []
        route_builder_classes: List[str] = []

        if not content or not content.strip():
            return {
                'routes': routes,
                'endpoints': endpoints,
                'route_builder_classes': route_builder_classes,
            }

        # Route builder classes
        for match in self.ROUTE_BUILDER_PATTERN.finditer(content):
            route_builder_classes.append(match.group(1))

        # From endpoints (each from() starts a new route)
        for match in self.FROM_PATTERN.finditer(content):
            uri = match.group(1)
            route = CamelRouteInfo(
                from_endpoint=uri,
                from_component=self._extract_component(uri),
                line_number=content[:match.start()].count('\n') + 1,
            )

            if route_builder_classes:
                route.route_builder_class = route_builder_classes[-1]

            # Look for route ID after from()
            following = content[match.end():match.end() + 500]
            rid = self.ROUTE_ID_PATTERN.search(following)
            if rid:
                route.route_id = rid.group(1)

            desc = self.ROUTE_DESCRIPTION_PATTERN.search(following)
            if desc:
                route.description = desc.group(1)

            auto = self.AUTO_STARTUP_PATTERN.search(following)
            if auto:
                route.auto_startup = auto.group(1) != 'false'

            routes.append(route)

            endpoints.append(CamelEndpointInfo(
                uri=uri,
                component=self._extract_component(uri),
                direction="from",
                line_number=route.line_number,
            ))

        # To endpoints
        for match in self.TO_PATTERN.finditer(content):
            uri = match.group(1)
            ep = CamelEndpointInfo(
                uri=uri,
                component=self._extract_component(uri),
                direction="to",
                line_number=content[:match.start()].count('\n') + 1,
            )
            endpoints.append(ep)
            # Assign to most recent route
            if routes:
                routes[-1].to_endpoints.append(ep)

        for match in self.TO_D_PATTERN.finditer(content):
            uri = match.group(1)
            ep = CamelEndpointInfo(
                uri=uri,
                component=self._extract_component(uri),
                direction="toD",
                line_number=content[:match.start()].count('\n') + 1,
            )
            endpoints.append(ep)
            if routes:
                routes[-1].to_endpoints.append(ep)

        for match in self.WIRE_TAP_PATTERN.finditer(content):
            uri = match.group(1)
            ep = CamelEndpointInfo(
                uri=uri,
                component=self._extract_component(uri),
                direction="wireTap",
                line_number=content[:match.start()].count('\n') + 1,
            )
            endpoints.append(ep)

        return {
            'routes': routes,
            'endpoints': endpoints,
            'route_builder_classes': route_builder_classes,
        }
