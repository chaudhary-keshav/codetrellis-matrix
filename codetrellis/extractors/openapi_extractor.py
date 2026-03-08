"""
CodeTrellis OpenAPI Extractor — Phase 3 of v5.0 Universal Scanner
==================================================================

Parses OpenAPI 2.0 (Swagger) and 3.0 specification files to extract:
- All API endpoints with methods, paths, parameters, responses
- Security schemes (bearer, API key, OAuth2, OIDC)
- Data models / schema definitions
- Tags and server base URLs

This gives 100% API coverage from a single structured file,
without needing to parse any source code.

Part of CodeTrellis v5.0 — Universal Scanner
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class OpenAPIEndpoint:
    """A single API endpoint from the spec."""
    method: str              # GET, POST, PUT, DELETE, PATCH
    path: str                # /api/v1/users/{id}
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[str] = None
    responses: Dict[str, str] = field(default_factory=dict)
    security: List[str] = field(default_factory=list)
    operation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "path": self.path,
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "parameters": self.parameters,
            "request_body": self.request_body,
            "responses": self.responses,
            "security": self.security,
            "operation_id": self.operation_id,
        }


@dataclass
class OpenAPISecurityScheme:
    """A security scheme from the spec."""
    name: str                # "bearerAuth", "apiKey"
    scheme_type: str         # "http", "apiKey", "oauth2", "openIdConnect"
    scheme: Optional[str] = None       # "bearer"
    bearer_format: Optional[str] = None  # "JWT"
    location: Optional[str] = None     # "header", "query", "cookie"
    header_name: Optional[str] = None  # "X-Gotify-Key"

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "scheme_type": self.scheme_type,
        }
        if self.scheme:
            result["scheme"] = self.scheme
        if self.bearer_format:
            result["bearer_format"] = self.bearer_format
        if self.location:
            result["location"] = self.location
        if self.header_name:
            result["header_name"] = self.header_name
        return result


@dataclass
class OpenAPIModel:
    """A data model/schema definition from the spec."""
    name: str
    properties: List[Dict[str, Any]] = field(default_factory=list)
    description: Optional[str] = None
    required_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "properties": self.properties,
            "description": self.description,
            "required_fields": self.required_fields,
        }


@dataclass
class OpenAPIInfo:
    """Complete parsed OpenAPI specification."""
    file_path: str
    spec_version: str        # "2.0" or "3.0.x"
    title: str = ""
    description: Optional[str] = None
    version: str = ""
    endpoints: List[OpenAPIEndpoint] = field(default_factory=list)
    models: List[OpenAPIModel] = field(default_factory=list)
    security_schemes: List[OpenAPISecurityScheme] = field(default_factory=list)
    tags: List[Dict[str, str]] = field(default_factory=list)
    servers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "spec_version": self.spec_version,
            "title": self.title,
            "description": self.description,
            "version": self.version,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "models": [m.to_dict() for m in self.models],
            "security_schemes": [s.to_dict() for s in self.security_schemes],
            "tags": self.tags,
            "servers": self.servers,
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format."""
        lines = []
        lines.append(f"# OpenAPI {self.spec_version}: {self.title} v{self.version}")
        if self.description:
            desc = self.description[:150]
            lines.append(f"# {desc}")

        # Security schemes
        if self.security_schemes:
            schemes = [f"{s.name}({s.scheme_type})" for s in self.security_schemes]
            lines.append(f"security:{','.join(schemes)}")

        # Endpoints grouped by tag
        tag_endpoints: Dict[str, List[OpenAPIEndpoint]] = {}
        for ep in self.endpoints:
            tag = ep.tags[0] if ep.tags else "default"
            if tag not in tag_endpoints:
                tag_endpoints[tag] = []
            tag_endpoints[tag].append(ep)

        for tag, eps in tag_endpoints.items():
            lines.append(f"# {tag}")
            for ep in eps:
                summary = f" # {ep.summary}" if ep.summary else ""
                security_str = f" [{','.join(ep.security)}]" if ep.security else ""
                lines.append(f"  {ep.method} {ep.path}{security_str}{summary}")

        # Models (compact)
        if self.models:
            lines.append(f"# Models ({len(self.models)})")
            for model in self.models:
                props = [
                    f"{p['name']}{'!' if p.get('required') else ''}:{p.get('type', '?')}"
                    for p in model.properties[:10]
                ]
                more = f",+{len(model.properties) - 10}more" if len(model.properties) > 10 else ""
                lines.append(f"  {model.name}:{','.join(props)}{more}")

        return '\n'.join(lines)


# =============================================================================
# OpenAPI Extractor
# =============================================================================

class OpenAPIExtractor:
    """
    Parse OpenAPI 2.0 (Swagger) and 3.0 specification files.

    Extracts complete API surface, security schemes, and data models
    from structured spec files (JSON or YAML).
    """

    HTTP_METHODS = {'get', 'post', 'put', 'delete', 'patch', 'head', 'options'}

    def can_extract(self, file_path: Path) -> bool:
        """Check if file is likely an OpenAPI spec."""
        name = file_path.name.lower()
        return name in (
            'swagger.json', 'swagger.yaml', 'swagger.yml',
            'openapi.json', 'openapi.yaml', 'openapi.yml',
            'spec.json', 'spec.yaml', 'spec.yml',
            'api-spec.json', 'api-spec.yaml', 'api-spec.yml',
        )

    def extract(self, file_path: Path) -> Optional[OpenAPIInfo]:
        """
        Parse an OpenAPI spec file (JSON or YAML).

        Args:
            file_path: Path to the spec file

        Returns:
            OpenAPIInfo or None if parsing fails
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            return None

        data = self._parse_content(content, file_path)
        if data is None:
            return None

        # Determine version
        if 'swagger' in data:
            return self._parse_swagger_2(data, str(file_path))
        elif 'openapi' in data:
            return self._parse_openapi_3(data, str(file_path))
        elif 'paths' in data:
            # Fallback: has paths but no version marker
            return self._parse_swagger_2(data, str(file_path))

        return None

    def _parse_content(self, content: str, file_path: Path) -> Optional[Dict]:
        """Parse JSON or YAML content."""
        name = file_path.name.lower()

        if name.endswith('.json'):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None
        elif name.endswith(('.yaml', '.yml')):
            try:
                import yaml
                return yaml.safe_load(content)
            except ImportError:
                # Fallback: basic YAML-like JSON parsing
                return None
            except Exception:
                return None

        # Try JSON first, then YAML
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                import yaml
                return yaml.safe_load(content)
            except Exception:
                return None

    def _parse_swagger_2(self, data: Dict, file_path: str) -> OpenAPIInfo:
        """Parse Swagger 2.0 specification."""
        info_data = data.get('info', {})

        result = OpenAPIInfo(
            file_path=file_path,
            spec_version='2.0',
            title=info_data.get('title', ''),
            description=info_data.get('description'),
            version=info_data.get('version', ''),
        )

        # Base path
        base_path = data.get('basePath', '')

        # Tags
        result.tags = [
            {"name": t.get("name", ""), "description": t.get("description", "")}
            for t in data.get('tags', [])
        ]

        # Servers (Swagger 2.0: host + basePath + schemes)
        host = data.get('host', '')
        schemes = data.get('schemes', ['https'])
        if host:
            for scheme in schemes:
                result.servers.append(f"{scheme}://{host}{base_path}")

        # Security definitions
        sec_defs = data.get('securityDefinitions', {})
        for name, scheme_data in sec_defs.items():
            result.security_schemes.append(self._parse_security_scheme_v2(name, scheme_data))

        # Global security requirements
        global_security = self._extract_security_names(data.get('security', []))

        # Paths
        for path, path_item in data.get('paths', {}).items():
            full_path = f"{base_path}{path}" if base_path else path
            for method in self.HTTP_METHODS:
                if method in path_item:
                    op = path_item[method]
                    endpoint = self._parse_endpoint(method.upper(), full_path, op, global_security)
                    result.endpoints.append(endpoint)

        # Models (definitions in Swagger 2.0)
        for name, schema in data.get('definitions', {}).items():
            result.models.append(self._parse_model(name, schema))

        return result

    def _parse_openapi_3(self, data: Dict, file_path: str) -> OpenAPIInfo:
        """Parse OpenAPI 3.0+ specification."""
        info_data = data.get('info', {})

        result = OpenAPIInfo(
            file_path=file_path,
            spec_version=str(data.get('openapi', '3.0.0')),
            title=info_data.get('title', ''),
            description=info_data.get('description'),
            version=info_data.get('version', ''),
        )

        # Tags
        result.tags = [
            {"name": t.get("name", ""), "description": t.get("description", "")}
            for t in data.get('tags', [])
        ]

        # Servers
        for server in data.get('servers', []):
            result.servers.append(server.get('url', ''))

        # Security schemes (components/securitySchemes in OpenAPI 3.0)
        components = data.get('components', {})
        sec_schemes = components.get('securitySchemes', {})
        for name, scheme_data in sec_schemes.items():
            result.security_schemes.append(self._parse_security_scheme_v3(name, scheme_data))

        # Global security requirements
        global_security = self._extract_security_names(data.get('security', []))

        # Paths
        for path, path_item in data.get('paths', {}).items():
            for method in self.HTTP_METHODS:
                if method in path_item:
                    op = path_item[method]
                    endpoint = self._parse_endpoint(method.upper(), path, op, global_security)
                    result.endpoints.append(endpoint)

        # Models (components/schemas in OpenAPI 3.0)
        schemas = components.get('schemas', {})
        for name, schema in schemas.items():
            result.models.append(self._parse_model(name, schema))

        return result

    def _parse_endpoint(
        self, method: str, path: str, operation: Dict, global_security: List[str]
    ) -> OpenAPIEndpoint:
        """Parse a single endpoint operation."""
        # Parameters
        params = []
        for param in operation.get('parameters', []):
            params.append({
                "name": param.get('name', ''),
                "in": param.get('in', ''),
                "type": param.get('type', param.get('schema', {}).get('type', '')),
                "required": param.get('required', False),
            })

        # Request body (OpenAPI 3.0)
        request_body = None
        if 'requestBody' in operation:
            rb = operation['requestBody']
            content = rb.get('content', {})
            for content_type, media in content.items():
                schema = media.get('schema', {})
                ref = schema.get('$ref', '')
                if ref:
                    request_body = ref.split('/')[-1]
                    break

        # Responses
        responses = {}
        for status_code, response in operation.get('responses', {}).items():
            ref = ''
            schema = response.get('schema', {})
            if schema:
                ref = schema.get('$ref', '')
            elif 'content' in response:
                for ct, media in response['content'].items():
                    ref = media.get('schema', {}).get('$ref', '')
                    if ref:
                        break
            if ref:
                responses[str(status_code)] = ref.split('/')[-1]
            else:
                desc = response.get('description', '')
                if desc:
                    responses[str(status_code)] = desc[:50]

        # Security (operation-level overrides global)
        op_security = operation.get('security')
        if op_security is not None:
            security = self._extract_security_names(op_security)
        else:
            security = global_security.copy()

        return OpenAPIEndpoint(
            method=method,
            path=path,
            summary=operation.get('summary'),
            description=operation.get('description'),
            tags=operation.get('tags', []),
            parameters=params,
            request_body=request_body,
            responses=responses,
            security=security,
            operation_id=operation.get('operationId'),
        )

    def _parse_model(self, name: str, schema: Dict) -> OpenAPIModel:
        """Parse a model/schema definition."""
        required_fields = schema.get('required', [])
        properties = []

        for prop_name, prop_schema in schema.get('properties', {}).items():
            prop_type = prop_schema.get('type', '')
            ref = prop_schema.get('$ref', '')
            if ref:
                prop_type = ref.split('/')[-1]
            elif prop_type == 'array':
                items = prop_schema.get('items', {})
                items_ref = items.get('$ref', '')
                items_type = items.get('type', '')
                prop_type = f"[{items_ref.split('/')[-1] if items_ref else items_type}]"

            properties.append({
                "name": prop_name,
                "type": prop_type,
                "required": prop_name in required_fields,
                "description": prop_schema.get('description', ''),
            })

        return OpenAPIModel(
            name=name,
            properties=properties,
            description=schema.get('description'),
            required_fields=required_fields,
        )

    def _parse_security_scheme_v2(self, name: str, data: Dict) -> OpenAPISecurityScheme:
        """Parse a Swagger 2.0 security definition."""
        scheme_type = data.get('type', '')
        scheme = OpenAPISecurityScheme(
            name=name,
            scheme_type=scheme_type,
        )

        if scheme_type == 'apiKey':
            scheme.location = data.get('in', '')
            scheme.header_name = data.get('name', '')
        elif scheme_type == 'basic':
            scheme.scheme_type = 'http'
            scheme.scheme = 'basic'
        elif scheme_type == 'oauth2':
            scheme.scheme = data.get('flow', '')

        return scheme

    def _parse_security_scheme_v3(self, name: str, data: Dict) -> OpenAPISecurityScheme:
        """Parse an OpenAPI 3.0 security scheme."""
        scheme_type = data.get('type', '')
        scheme = OpenAPISecurityScheme(
            name=name,
            scheme_type=scheme_type,
        )

        if scheme_type == 'http':
            scheme.scheme = data.get('scheme', '')
            scheme.bearer_format = data.get('bearerFormat')
        elif scheme_type == 'apiKey':
            scheme.location = data.get('in', '')
            scheme.header_name = data.get('name', '')
        elif scheme_type == 'openIdConnect':
            scheme.scheme = 'oidc'

        return scheme

    def _extract_security_names(self, security_list: List) -> List[str]:
        """Extract security scheme names from a security requirement list."""
        names = []
        for item in security_list:
            if isinstance(item, dict):
                names.extend(item.keys())
        return list(dict.fromkeys(names))  # Deduplicate
