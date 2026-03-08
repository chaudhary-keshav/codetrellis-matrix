"""
Express.js API Pattern Extractor - Extracts REST API and response patterns.

Supports:
- RESTful resource patterns (CRUD on /resource/:id)
- API versioning (v1, v2 prefixes)
- Response helpers: res.json(), res.send(), res.render(), res.redirect()
- Content negotiation (res.format())
- res.status() chaining
- API documentation patterns (swagger/openapi decorators)
- Request validation patterns
- Authentication/authorization guards
- Rate limiting per-route
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class ExpressResourceInfo:
    """A RESTful resource identified from route patterns."""
    name: str
    base_path: str = ""
    file: str = ""
    operations: List[str] = field(default_factory=list)  # GET, POST, PUT, DELETE, PATCH
    has_list: bool = False
    has_detail: bool = False
    has_create: bool = False
    has_update: bool = False
    has_delete: bool = False
    has_nested: bool = False
    param_name: str = ""


@dataclass
class ExpressResponsePatternInfo:
    """A response pattern usage."""
    file: str = ""
    line_number: int = 0
    response_type: str = ""  # json, send, render, redirect, download, sendFile
    status_code: int = 0
    has_data: bool = False


@dataclass
class ExpressApiVersionInfo:
    """API versioning information."""
    version: str = ""
    prefix: str = ""
    file: str = ""
    line_number: int = 0
    route_count: int = 0


@dataclass
class ExpressApiSummary:
    """Summary of Express API patterns."""
    total_resources: int = 0
    total_endpoints: int = 0
    api_versions: List[str] = field(default_factory=list)
    response_formats: List[str] = field(default_factory=list)
    has_versioning: bool = False
    has_swagger: bool = False
    has_openapi: bool = False
    has_validation: bool = False
    has_pagination: bool = False
    has_filtering: bool = False
    has_sorting: bool = False
    rest_style: str = ""  # restful, rpc, mixed


class ExpressApiExtractor:
    """Extracts Express.js API pattern information from source code."""

    # Route patterns for CRUD detection
    HTTP_METHODS = {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}

    ROUTE_PATTERN = re.compile(
        r'(?:\w+)\s*\.\s*(get|post|put|patch|delete|head|options)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
    )

    # API version prefix (works on raw path strings)
    VERSION_PATTERN = re.compile(
        r'(?:/(?:api/)?)(v\d+)'
    )

    # Response patterns
    RESPONSE_PATTERNS = {
        'json': re.compile(r'(?:res|response)\s*\.\s*(?:status\s*\(\s*\d+\s*\)\s*\.)?\s*json\s*\('),
        'send': re.compile(r'(?:res|response)\s*\.\s*(?:status\s*\(\s*\d+\s*\)\s*\.)?\s*send\s*\('),
        'render': re.compile(r'(?:res|response)\s*\.\s*render\s*\('),
        'redirect': re.compile(r'(?:res|response)\s*\.\s*redirect\s*\('),
        'download': re.compile(r'(?:res|response)\s*\.\s*download\s*\('),
        'sendFile': re.compile(r'(?:res|response)\s*\.\s*sendFile\s*\('),
        'format': re.compile(r'(?:res|response)\s*\.\s*format\s*\('),
    }

    STATUS_CODE_PATTERN = re.compile(r'\.status\s*\(\s*(\d{3})\s*\)')

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract API pattern information from Express.js source code."""
        resources: Dict[str, ExpressResourceInfo] = {}
        response_patterns: List[ExpressResponsePatternInfo] = []
        api_versions: Dict[str, ExpressApiVersionInfo] = {}
        lines = content.split('\n')
        endpoint_count = 0
        response_formats: Set[str] = set()

        has_swagger = 'swagger' in content.lower() or 'openapi' in content.lower()
        has_validation = any(
            v in content for v in [
                'express-validator', 'joi', 'yup', 'zod', 'celebrate',
                'body(', 'param(', 'query(', 'check(', '.validate(',
            ]
        )
        has_pagination = any(
            p in content for p in ['page', 'limit', 'offset', 'skip', 'per_page', 'perPage']
        )
        has_filtering = 'filter' in content.lower() or 'where' in content.lower()
        has_sorting = 'sort' in content.lower() or 'order' in content.lower()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Detect routes
            route_match = self.ROUTE_PATTERN.search(stripped)
            if route_match:
                method = route_match.group(1).upper()
                path = route_match.group(2)
                endpoint_count += 1

                # Detect API version
                ver_match = self.VERSION_PATTERN.search(path)
                if ver_match:
                    ver = ver_match.group(1)
                    if ver not in api_versions:
                        api_versions[ver] = ExpressApiVersionInfo(
                            version=ver,
                            prefix=ver,
                            file=file_path,
                            line_number=i,
                        )
                    api_versions[ver].route_count += 1

                # Group into resources
                resource_name = self._extract_resource_name(path)
                if resource_name:
                    if resource_name not in resources:
                        resources[resource_name] = ExpressResourceInfo(
                            name=resource_name,
                            base_path=self._extract_base_path(path, resource_name),
                            file=file_path,
                        )
                    res = resources[resource_name]
                    if method not in res.operations:
                        res.operations.append(method)

                    has_param = ':' in path or path.endswith('/:id')
                    if method == 'GET' and not has_param:
                        res.has_list = True
                    elif method == 'GET' and has_param:
                        res.has_detail = True
                    elif method == 'POST':
                        res.has_create = True
                    elif method in ('PUT', 'PATCH'):
                        res.has_update = True
                    elif method == 'DELETE':
                        res.has_delete = True

                    # Check for nested resources
                    parts = [p for p in path.split('/') if p and not p.startswith(':')]
                    if len(parts) > 2:
                        res.has_nested = True

                    # Extract param name
                    param_match = re.search(r':(\w+)', path)
                    if param_match and not res.param_name:
                        res.param_name = param_match.group(1)

            # Detect response patterns
            for resp_type, pattern in self.RESPONSE_PATTERNS.items():
                if pattern.search(stripped):
                    status_match = self.STATUS_CODE_PATTERN.search(stripped)
                    status_code = int(status_match.group(1)) if status_match else 0
                    response_formats.add(resp_type)
                    response_patterns.append(ExpressResponsePatternInfo(
                        file=file_path,
                        line_number=i,
                        response_type=resp_type,
                        status_code=status_code,
                        has_data='(' in stripped and ')' in stripped,
                    ))

        # Build summary
        summary = ExpressApiSummary(
            total_resources=len(resources),
            total_endpoints=endpoint_count,
            api_versions=list(api_versions.keys()),
            response_formats=sorted(response_formats),
            has_versioning=len(api_versions) > 0,
            has_swagger=has_swagger,
            has_openapi=has_swagger,
            has_validation=has_validation,
            has_pagination=has_pagination,
            has_filtering=has_filtering,
            has_sorting=has_sorting,
            rest_style=self._determine_rest_style(resources),
        )

        return {
            "resources": list(resources.values()),
            "response_patterns": response_patterns,
            "api_versions": list(api_versions.values()),
            "summary": summary,
        }

    def _extract_resource_name(self, path: str) -> str:
        """Extract resource name from a route path."""
        parts = path.strip('/').split('/')
        # Skip version prefixes
        for part in parts:
            if part.startswith(':') or part.startswith('v') and part[1:].isdigit():
                continue
            if part in ('api', 'auth', 'health', 'status'):
                continue
            return part
        return ''

    def _extract_base_path(self, path: str, resource_name: str) -> str:
        """Extract base path up to resource name."""
        idx = path.find(resource_name)
        if idx >= 0:
            return path[:idx + len(resource_name)]
        return path

    def _determine_rest_style(self, resources: Dict[str, ExpressResourceInfo]) -> str:
        """Determine REST API style."""
        if not resources:
            return ''
        restful_count = 0
        for res in resources.values():
            crud_ops = sum([res.has_list, res.has_detail, res.has_create, res.has_update, res.has_delete])
            if crud_ops >= 3:
                restful_count += 1
        if restful_count > len(resources) * 0.5:
            return 'restful'
        elif restful_count > 0:
            return 'mixed'
        return 'rpc'
