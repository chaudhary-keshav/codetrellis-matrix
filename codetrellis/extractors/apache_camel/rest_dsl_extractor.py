"""
Apache Camel REST DSL Extractor - Extracts REST DSL definitions.

Extracts:
- rest() definitions with path and description
- HTTP verb operations (get, post, put, delete, patch, head)
- Request/response types (consumes, produces)
- Parameter bindings
- OpenAPI/Swagger integration
- REST configuration (component, host, port, contextPath)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class CamelRestOperationInfo:
    """Information about a REST operation."""
    http_method: str = ""  # get, post, put, delete, patch, head
    path: str = ""
    description: str = ""
    consumes: str = ""
    produces: str = ""
    type_class: str = ""
    out_type_class: str = ""
    to_endpoint: str = ""
    route_id: str = ""
    param_bindings: List[Dict[str, str]] = field(default_factory=list)
    line_number: int = 0


@dataclass
class CamelRestInfo:
    """Information about a REST definition."""
    base_path: str = ""
    description: str = ""
    tag: str = ""
    consumes: str = ""
    produces: str = ""
    operations: List[CamelRestOperationInfo] = field(default_factory=list)
    binding_mode: str = ""  # auto, json, xml, off
    skip_binding_on_error: bool = False
    line_number: int = 0


class CamelRestDSLExtractor:
    """Extracts REST DSL definitions."""

    # rest() definition
    REST_DEFINITION_PATTERN = re.compile(
        r'rest\s*\(\s*["\']([^"\']*)["\']',
        re.MULTILINE
    )

    # REST description
    REST_DESCRIPTION_PATTERN = re.compile(
        r'\.description\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # REST tag
    REST_TAG_PATTERN = re.compile(
        r'\.tag\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # HTTP verb patterns
    GET_PATTERN = re.compile(
        r'\.get\s*\(\s*(?:["\']([^"\']*)["\'])?\s*\)',
        re.MULTILINE
    )
    POST_PATTERN = re.compile(
        r'\.post\s*\(\s*(?:["\']([^"\']*)["\'])?\s*\)',
        re.MULTILINE
    )
    PUT_PATTERN = re.compile(
        r'\.put\s*\(\s*(?:["\']([^"\']*)["\'])?\s*\)',
        re.MULTILINE
    )
    DELETE_PATTERN = re.compile(
        r'\.delete\s*\(\s*(?:["\']([^"\']*)["\'])?\s*\)',
        re.MULTILINE
    )
    PATCH_PATTERN = re.compile(
        r'\.patch\s*\(\s*(?:["\']([^"\']*)["\'])?\s*\)',
        re.MULTILINE
    )
    HEAD_PATTERN = re.compile(
        r'\.head\s*\(\s*(?:["\']([^"\']*)["\'])?\s*\)',
        re.MULTILINE
    )

    # Consumes/produces
    CONSUMES_PATTERN = re.compile(
        r'\.consumes\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    PRODUCES_PATTERN = re.compile(
        r'\.produces\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Type bindings
    TYPE_PATTERN = re.compile(
        r'\.type\s*\(\s*(\w+)\.class\s*\)',
        re.MULTILINE
    )
    OUT_TYPE_PATTERN = re.compile(
        r'\.outType\s*\(\s*(\w+)\.class\s*\)',
        re.MULTILINE
    )

    # To endpoint
    REST_TO_PATTERN = re.compile(
        r'\.to\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Route ID
    REST_ROUTE_ID_PATTERN = re.compile(
        r'\.routeId\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Binding mode
    BINDING_MODE_PATTERN = re.compile(
        r'\.bindingMode\s*\(\s*RestBindingMode\.(\w+)',
        re.MULTILINE
    )

    # REST configuration
    REST_CONFIGURATION_PATTERN = re.compile(
        r'restConfiguration\s*\(\s*\)',
        re.MULTILINE
    )

    REST_CONFIG_COMPONENT_PATTERN = re.compile(
        r'\.component\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    REST_CONFIG_HOST_PATTERN = re.compile(
        r'\.host\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    REST_CONFIG_PORT_PATTERN = re.compile(
        r'\.port\s*\(\s*(\d+|["\'][^"\']+["\'])',
        re.MULTILINE
    )

    REST_CONFIG_CONTEXT_PATTERN = re.compile(
        r'\.contextPath\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # OpenAPI / Swagger
    OPENAPI_PATTERN = re.compile(
        r'apiContextPath|apiProperty|restConfiguration.*\.apiComponent|'
        r'import\s+org\.apache\.camel\.openapi\b|'
        r'import\s+org\.apache\.camel\.swagger\b',
        re.MULTILINE
    )

    # Param annotations
    PARAM_PATTERN = re.compile(
        r'\.param\s*\(\s*\)\s*\.name\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract REST DSL definitions."""
        rest_definitions: List[CamelRestInfo] = []
        rest_operations: List[CamelRestOperationInfo] = []
        has_openapi = False
        rest_config: Dict[str, str] = {}

        if not content or not content.strip():
            return {
                'rest_definitions': rest_definitions,
                'rest_operations': rest_operations,
                'has_openapi': has_openapi,
                'rest_config': rest_config,
            }

        # REST definitions
        for match in self.REST_DEFINITION_PATTERN.finditer(content):
            rest = CamelRestInfo(
                base_path=match.group(1),
                line_number=content[:match.start()].count('\n') + 1,
            )

            following = content[match.end():match.end() + 300]
            desc = self.REST_DESCRIPTION_PATTERN.search(following)
            if desc:
                rest.description = desc.group(1)

            tag = self.REST_TAG_PATTERN.search(following)
            if tag:
                rest.tag = tag.group(1)

            bm = self.BINDING_MODE_PATTERN.search(following)
            if bm:
                rest.binding_mode = bm.group(1)

            rest_definitions.append(rest)

        # HTTP verb operations
        verb_patterns = [
            ('get', self.GET_PATTERN),
            ('post', self.POST_PATTERN),
            ('put', self.PUT_PATTERN),
            ('delete', self.DELETE_PATTERN),
            ('patch', self.PATCH_PATTERN),
            ('head', self.HEAD_PATTERN),
        ]

        for method, pattern in verb_patterns:
            for match in pattern.finditer(content):
                op = CamelRestOperationInfo(
                    http_method=method,
                    path=match.group(1) or "",
                    line_number=content[:match.start()].count('\n') + 1,
                )

                # Look for configuration after the verb
                following = content[match.end():match.end() + 500]

                cons = self.CONSUMES_PATTERN.search(following)
                if cons:
                    op.consumes = cons.group(1)

                prod = self.PRODUCES_PATTERN.search(following)
                if prod:
                    op.produces = prod.group(1)

                typ = self.TYPE_PATTERN.search(following)
                if typ:
                    op.type_class = typ.group(1)

                out = self.OUT_TYPE_PATTERN.search(following)
                if out:
                    op.out_type_class = out.group(1)

                to = self.REST_TO_PATTERN.search(following)
                if to:
                    op.to_endpoint = to.group(1)

                rid = self.REST_ROUTE_ID_PATTERN.search(following)
                if rid:
                    op.route_id = rid.group(1)

                rest_operations.append(op)

                # Add to most recent rest definition
                if rest_definitions:
                    rest_definitions[-1].operations.append(op)

        # OpenAPI detection
        has_openapi = bool(self.OPENAPI_PATTERN.search(content))

        # REST configuration
        if self.REST_CONFIGURATION_PATTERN.search(content):
            comp = self.REST_CONFIG_COMPONENT_PATTERN.search(content)
            if comp:
                rest_config['component'] = comp.group(1)
            host = self.REST_CONFIG_HOST_PATTERN.search(content)
            if host:
                rest_config['host'] = host.group(1)
            port = self.REST_CONFIG_PORT_PATTERN.search(content)
            if port:
                rest_config['port'] = port.group(1)
            ctx = self.REST_CONFIG_CONTEXT_PATTERN.search(content)
            if ctx:
                rest_config['contextPath'] = ctx.group(1)

        return {
            'rest_definitions': rest_definitions,
            'rest_operations': rest_operations,
            'has_openapi': has_openapi,
            'rest_config': rest_config,
        }
