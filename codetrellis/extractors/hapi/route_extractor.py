"""
Hapi route extractor - Extract server.route() definitions, route configs, and validation.

Extracts:
- server.route() calls (single and array)
- Route config objects ({ method, path, handler, options })
- Path parameters (/users/{id})
- Joi/Zod validation on params, query, payload, headers
- Route tags, notes, description (Swagger/OpenAPI annotations)
- Route-level auth configuration
- Pre-handler hooks (pre: [])
- Route caching configuration (cache: { expiresIn, ... })

Supports @hapi/hapi v17-v21+ route configuration format.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class HapiValidationInfo:
    """Information about route validation (Joi or other)."""
    target: str = ""        # params, query, payload, headers, state
    schema_type: str = ""   # joi, zod, yup, custom
    fields: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class HapiRouteConfigInfo:
    """Detailed route configuration."""
    auth: str = ""              # auth strategy name or False
    tags: List[str] = field(default_factory=list)     # ['api', 'users']
    description: str = ""       # route description
    notes: List[str] = field(default_factory=list)    # route notes
    pre_handlers: List[str] = field(default_factory=list)  # pre-handler method names
    cache_config: Dict[str, Any] = field(default_factory=dict)
    cors: bool = False
    payload_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HapiRouteInfo:
    """Information about a single Hapi route."""
    method: str = ""            # GET, POST, PUT, DELETE, PATCH, *
    path: str = ""              # /users/{id}
    handler: str = ""           # handler function/method name
    file: str = ""
    line_number: int = 0
    path_params: List[str] = field(default_factory=list)     # ['id']
    validation: List[HapiValidationInfo] = field(default_factory=list)
    config: Optional[HapiRouteConfigInfo] = None
    is_async: bool = False


class HapiRouteExtractor:
    """Extract Hapi route definitions and their configurations."""

    # server.route({ method, path, handler }) or server.route([{...}, {...}])
    ROUTE_PATTERN = re.compile(
        r'server\.route\s*\(\s*(\{|\[)',
        re.MULTILINE,
    )

    # Individual route config object: { method: 'GET', path: '/users', ... }
    ROUTE_CONFIG_PATTERN = re.compile(
        r'\{\s*method\s*:\s*[\'"]([A-Z*,\s]+)[\'"]\s*,\s*path\s*:\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE,
    )

    # Handler reference: handler: functionName or handler: { ... }
    HANDLER_PATTERN = re.compile(
        r'handler\s*:\s*(?:async\s+)?(?:function\s+)?(\w+)|'
        r'handler\s*:\s*(?:async\s+)?\(\s*(?:request|req|h)',
        re.MULTILINE,
    )

    # Path parameters: /users/{id}, /posts/{postId}/comments/{commentId}
    PATH_PARAM_PATTERN = re.compile(r'\{(\w+)\}')

    # Validation patterns: validate: { params: Joi.object({...}), query: ..., payload: ... }
    VALIDATE_BLOCK_PATTERN = re.compile(
        r'validate\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
        re.DOTALL,
    )

    VALIDATE_TARGET_PATTERN = re.compile(
        r'(params|query|payload|headers|state)\s*:\s*(\w+)',
        re.MULTILINE,
    )

    # Route options: options: { auth, tags, description, notes, pre, cache, cors }
    AUTH_PATTERN = re.compile(
        r'auth\s*:\s*(?:[\'"](\w+)[\'"]|false|(\{[^}]+\}))',
        re.MULTILINE,
    )

    TAGS_PATTERN = re.compile(
        r'tags\s*:\s*\[([^\]]*)\]',
        re.MULTILINE,
    )

    DESCRIPTION_PATTERN = re.compile(
        r'description\s*:\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE,
    )

    NOTES_PATTERN = re.compile(
        r'notes\s*:\s*\[([^\]]*)\]',
        re.MULTILINE,
    )

    PRE_PATTERN = re.compile(
        r'pre\s*:\s*\[([^\]]*)\]',
        re.DOTALL,
    )

    CACHE_PATTERN = re.compile(
        r'cache\s*:\s*\{([^}]+)\}',
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Hapi route information from source code.

        Returns:
            Dict with 'routes' (List[HapiRouteInfo])
        """
        routes: List[HapiRouteInfo] = []

        # Find all route config objects
        for match in self.ROUTE_CONFIG_PATTERN.finditer(content):
            methods_str = match.group(1).strip()
            path = match.group(2).strip()
            line_number = content[:match.start()].count('\n') + 1

            # Handle multiple methods: ['GET', 'POST']
            methods = [m.strip() for m in methods_str.split(',') if m.strip()]
            if not methods:
                methods = [methods_str]

            for method in methods:
                route = HapiRouteInfo(
                    method=method.upper().strip("'\""),
                    path=path,
                    file=file_path,
                    line_number=line_number,
                )

                # Extract path parameters
                route.path_params = self.PATH_PARAM_PATTERN.findall(path)

                # Try to find handler in the surrounding block
                block_start = match.start()
                block_end = min(block_start + 1000, len(content))
                block = content[block_start:block_end]

                handler_match = self.HANDLER_PATTERN.search(block)
                if handler_match:
                    route.handler = handler_match.group(1) or '(anonymous)'
                    route.is_async = 'async' in block[:handler_match.start() + 20]

                # Extract route config (auth, tags, description, etc.)
                route.config = self._extract_route_config(block)

                # Extract validation
                route.validation = self._extract_validation(block, line_number)

                routes.append(route)

        return {'routes': routes}

    def _extract_route_config(self, block: str) -> HapiRouteConfigInfo:
        """Extract route configuration from a route block."""
        config = HapiRouteConfigInfo()

        # Auth
        auth_match = self.AUTH_PATTERN.search(block)
        if auth_match:
            config.auth = auth_match.group(1) or auth_match.group(2) or 'false'

        # Tags
        tags_match = self.TAGS_PATTERN.search(block)
        if tags_match:
            tags_str = tags_match.group(1)
            config.tags = [t.strip().strip("'\"") for t in tags_str.split(',') if t.strip()]

        # Description
        desc_match = self.DESCRIPTION_PATTERN.search(block)
        if desc_match:
            config.description = desc_match.group(1)

        # Notes
        notes_match = self.NOTES_PATTERN.search(block)
        if notes_match:
            notes_str = notes_match.group(1)
            config.notes = [n.strip().strip("'\"") for n in notes_str.split(',') if n.strip()]

        # Pre handlers
        pre_match = self.PRE_PATTERN.search(block)
        if pre_match:
            pre_str = pre_match.group(1)
            # Find method references in pre array
            method_refs = re.findall(r'method\s*:\s*(\w+)|[\'"](\w+)[\'"]', pre_str)
            config.pre_handlers = [m[0] or m[1] for m in method_refs if m[0] or m[1]]

        # Cache
        cache_match = self.CACHE_PATTERN.search(block)
        if cache_match:
            cache_str = cache_match.group(1)
            config.cache_config = self._parse_key_value(cache_str)

        # CORS
        if re.search(r'cors\s*:\s*true', block):
            config.cors = True

        return config

    def _extract_validation(self, block: str, base_line: int) -> List[HapiValidationInfo]:
        """Extract validation configuration from a route block."""
        validations: List[HapiValidationInfo] = []

        validate_match = self.VALIDATE_BLOCK_PATTERN.search(block)
        if not validate_match:
            return validations

        validate_block = validate_match.group(1)

        for target_match in self.VALIDATE_TARGET_PATTERN.finditer(validate_block):
            target = target_match.group(1)
            schema_ref = target_match.group(2)

            # Detect schema type
            schema_type = 'custom'
            if 'Joi' in schema_ref or 'joi' in validate_block:
                schema_type = 'joi'
            elif 'Zod' in schema_ref or 'z.' in validate_block:
                schema_type = 'zod'
            elif 'yup' in schema_ref.lower():
                schema_type = 'yup'

            validations.append(HapiValidationInfo(
                target=target,
                schema_type=schema_type,
                line_number=base_line,
            ))

        return validations

    @staticmethod
    def _parse_key_value(text: str) -> Dict[str, Any]:
        """Parse simple key: value pairs from a block of text."""
        result = {}
        for match in re.finditer(r'(\w+)\s*:\s*([^\s,]+)', text):
            key = match.group(1)
            value = match.group(2).strip("'\"")
            result[key] = value
        return result
