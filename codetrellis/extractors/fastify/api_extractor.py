"""
Fastify API Pattern Extractor - Extracts REST patterns, serialization, and API summaries.

Supports:
- RESTful resource patterns from routes
- Response serialization via reply.serialize()
- Content type serialization (serializerCompiler)
- API versioning via constraints
- Fastify 3.x through 5.x patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class FastifyResourceInfo:
    """A RESTful resource identified from route patterns."""
    name: str
    base_path: str = ""
    file: str = ""
    operations: List[str] = field(default_factory=list)
    has_list: bool = False
    has_detail: bool = False
    has_create: bool = False
    has_update: bool = False
    has_delete: bool = False
    param_name: str = ""


@dataclass
class FastifySerializerInfo:
    """Serialization configuration."""
    file: str = ""
    line_number: int = 0
    serializer_type: str = ""  # schema-based, custom, compiler
    content_type: str = ""


@dataclass
class FastifyApiSummary:
    """Summary of Fastify API patterns."""
    total_routes: int = 0
    total_resources: int = 0
    total_plugins: int = 0
    total_hooks: int = 0
    total_schemas: int = 0
    has_swagger: bool = False
    has_versioning: bool = False
    has_validation: bool = False
    has_serialization: bool = False
    has_websockets: bool = False
    has_graphql: bool = False
    type_provider: str = ""
    response_formats: List[str] = field(default_factory=list)


class FastifyApiExtractor:
    """Extracts Fastify API pattern information from source code."""

    HTTP_METHODS = {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}

    ROUTE_PATTERN = re.compile(
        r'(?:\w+)\s*\.\s*(get|post|put|patch|delete|head|options)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        re.IGNORECASE
    )

    # reply.send(), reply.code(), reply.type()
    REPLY_PATTERN = re.compile(
        r'(?:reply|res)\s*\.\s*(send|code|type|serialize|header)\s*\('
    )

    # Serializer compiler
    SERIALIZER_COMPILER_PATTERN = re.compile(
        r'(?:setSerializerCompiler|serializerCompiler)\s*'
    )

    # Content type parser
    CONTENT_TYPE_PARSER_PATTERN = re.compile(
        r"addContentTypeParser\s*\(\s*['\"`]([^'\"`]+)['\"`]"
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract API pattern information from Fastify source code."""
        resources: Dict[str, FastifyResourceInfo] = {}
        serializers: List[FastifySerializerInfo] = []
        response_formats: Set[str] = set()

        has_swagger = any(
            p in content for p in ['@fastify/swagger', 'fastify-swagger', 'SwaggerModule']
        )
        has_versioning = 'constraints' in content and 'version' in content
        has_websockets = any(
            p in content for p in ['@fastify/websocket', 'fastify-websocket', 'ws']
        )
        has_graphql = any(
            p in content for p in ['@fastify/mercurius', 'mercurius', 'graphql']
        )

        # Extract routes and group into resources
        endpoint_count = 0
        for match in self.ROUTE_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            endpoint_count += 1

            resource_name = self._extract_resource_name(path)
            if resource_name:
                if resource_name not in resources:
                    resources[resource_name] = FastifyResourceInfo(
                        name=resource_name,
                        base_path=self._extract_base_path(path, resource_name),
                        file=file_path,
                    )
                res = resources[resource_name]
                if method not in res.operations:
                    res.operations.append(method)

                has_param = ':' in path
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

                param_match = re.search(r':(\w+)', path)
                if param_match and not res.param_name:
                    res.param_name = param_match.group(1)

        # Detect reply patterns for response format
        for match in self.REPLY_PATTERN.finditer(content):
            method = match.group(1)
            if method == 'send':
                response_formats.add('json')
            elif method == 'type':
                # Look for content type
                after = content[match.end():match.end() + 50]
                if 'html' in after:
                    response_formats.add('html')
                elif 'json' in after:
                    response_formats.add('json')
                elif 'text' in after:
                    response_formats.add('text')

        # Detect serializer compilers
        if self.SERIALIZER_COMPILER_PATTERN.search(content):
            serializers.append(FastifySerializerInfo(
                file=file_path,
                serializer_type='compiler',
            ))

        # Detect custom content type parsers
        for match in self.CONTENT_TYPE_PARSER_PATTERN.finditer(content):
            content_type = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            serializers.append(FastifySerializerInfo(
                file=file_path,
                line_number=line_num,
                serializer_type='parser',
                content_type=content_type,
            ))

        # Detect type provider
        type_provider = ''
        if '@sinclair/typebox' in content or 'TypeBox' in content:
            type_provider = 'typebox'
        elif 'zod' in content and ('ZodTypeProvider' in content or 'z.' in content):
            type_provider = 'zod'
        elif 'json-schema-to-ts' in content:
            type_provider = 'json-schema-to-ts'

        # Build summary
        summary = FastifyApiSummary(
            total_routes=endpoint_count,
            total_resources=len(resources),
            has_swagger=has_swagger,
            has_versioning=has_versioning,
            has_validation='schema' in content,
            has_serialization=bool(serializers),
            has_websockets=has_websockets,
            has_graphql=has_graphql,
            type_provider=type_provider,
            response_formats=sorted(response_formats),
        )

        return {
            "resources": list(resources.values()),
            "serializers": serializers,
            "summary": summary,
        }

    def _extract_resource_name(self, path: str) -> str:
        """Extract resource name from a route path."""
        parts = path.strip('/').split('/')
        for part in parts:
            if part.startswith(':'):
                continue
            if part in ('api', 'v1', 'v2', 'v3'):
                continue
            return part
        return ''

    def _extract_base_path(self, path: str, resource_name: str) -> str:
        """Extract base path up to resource name."""
        idx = path.find(resource_name)
        if idx >= 0:
            return path[:idx + len(resource_name)]
        return path
