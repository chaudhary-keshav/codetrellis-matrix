"""
Jakarta EE JAX-RS Extractor v1.0 - JAX-RS resources, endpoints, providers.
Part of CodeTrellis v4.94 - Jakarta EE Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class JakartaResourceInfo:
    """A JAX-RS resource class."""
    name: str
    base_path: str = ""
    endpoints: List[Dict] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    namespace: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class JakartaJAXRSEndpointInfo:
    """A JAX-RS endpoint."""
    path: str
    method: str
    function_name: str = ""
    consumes: str = ""
    produces: str = ""
    return_type: str = ""
    params: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class JakartaProviderInfo:
    """A JAX-RS provider."""
    name: str
    provider_type: str = ""  # exception_mapper, message_body_reader, message_body_writer, container_filter, interceptor
    file: str = ""
    line_number: int = 0


class JakartaJAXRSExtractor:
    """Extracts Jakarta JAX-RS patterns."""

    CLASS_PATH_PATTERN = re.compile(
        r'@Path\(\s*"([^"]+)"\s*\)\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    ENDPOINT_PATTERN = re.compile(
        r'@(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\n'
        r'(?:@Path\(\s*"([^"]*)"\s*\)\s*\n)?'
        r'(?:@Produces\(\s*(?:MediaType\.)?("?[^")]+)"?\s*\)\s*\n)?'
        r'(?:@Consumes\(\s*(?:MediaType\.)?("?[^")]+)"?\s*\)\s*\n)?'
        r'(?:public\s+)?([\w<>,?\[\]]+)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    PARAM_PATTERN = re.compile(
        r'@(PathParam|QueryParam|HeaderParam|FormParam|BeanParam|CookieParam|MatrixParam|DefaultValue)\s*'
        r'(?:\(\s*"?([^")]*)"?\s*\))?\s+'
        r'([\w<>,?\[\]]+)\s+(\w+)',
        re.MULTILINE
    )

    PROVIDER_PATTERNS = {
        'exception_mapper': re.compile(r'@Provider\s*\n(?:public\s+)?class\s+(\w+)\s+implements\s+ExceptionMapper', re.MULTILINE),
        'message_body_reader': re.compile(r'@Provider\s*\n(?:public\s+)?class\s+(\w+)\s+implements\s+MessageBodyReader', re.MULTILINE),
        'message_body_writer': re.compile(r'@Provider\s*\n(?:public\s+)?class\s+(\w+)\s+implements\s+MessageBodyWriter', re.MULTILINE),
        'container_request_filter': re.compile(r'@Provider\s*\n(?:public\s+)?class\s+(\w+)\s+implements\s+ContainerRequestFilter', re.MULTILINE),
        'container_response_filter': re.compile(r'@Provider\s*\n(?:public\s+)?class\s+(\w+)\s+implements\s+ContainerResponseFilter', re.MULTILINE),
        'reader_interceptor': re.compile(r'@Provider\s*\n(?:public\s+)?class\s+(\w+)\s+implements\s+ReaderInterceptor', re.MULTILINE),
        'writer_interceptor': re.compile(r'@Provider\s*\n(?:public\s+)?class\s+(\w+)\s+implements\s+WriterInterceptor', re.MULTILINE),
    }

    APPLICATION_PATTERN = re.compile(
        r'@ApplicationPath\(\s*"([^"]+)"\s*\)\s*\n'
        r'(?:public\s+)?class\s+(\w+)\s+extends\s+Application',
        re.MULTILINE
    )

    NAMESPACE_PATTERN = re.compile(r'import\s+(jakarta|javax)\.ws\.rs\.')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'resources': [], 'endpoints': [], 'providers': [], 'applications': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        ns_match = self.NAMESPACE_PATTERN.search(content)
        namespace = ns_match.group(1) if ns_match else ""

        # Extract JAX-RS Application
        for match in self.APPLICATION_PATTERN.finditer(content):
            result['applications'].append({
                'name': match.group(2),
                'path': match.group(1),
                'file': file_path,
                'line_number': content[:match.start()].count('\n') + 1,
            })

        # Extract resource classes
        base_path = ""
        for match in self.CLASS_PATH_PATTERN.finditer(content):
            base_path = match.group(1)
            result['resources'].append(JakartaResourceInfo(
                name=match.group(2), base_path=base_path,
                namespace=namespace,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract endpoints
        for match in self.ENDPOINT_PATTERN.finditer(content):
            http_method = match.group(1)
            path = match.group(2) or ""
            produces = match.group(3) or ""
            consumes = match.group(4) or ""
            return_type = match.group(5)
            function_name = match.group(6)

            full_path = base_path.rstrip('/') + '/' + path.lstrip('/') if path else base_path

            # Extract params
            method_start = match.start()
            method_end = content.find('\n\n', match.end())
            if method_end == -1:
                method_end = min(match.end() + 500, len(content))
            method_text = content[method_start:method_end]
            params = [f"@{m.group(1)}({m.group(2)}) {m.group(3)} {m.group(4)}"
                      for m in self.PARAM_PATTERN.finditer(method_text)]

            result['endpoints'].append(JakartaJAXRSEndpointInfo(
                path=full_path, method=http_method,
                function_name=function_name,
                consumes=consumes.strip('"'), produces=produces.strip('"'),
                return_type=return_type, params=params,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Update resource endpoint counts
        for resource in result['resources']:
            resource.endpoints = [
                {'method': ep.method, 'path': ep.path, 'function': ep.function_name}
                for ep in result['endpoints']
            ]

        # Extract providers
        for provider_type, pattern in self.PROVIDER_PATTERNS.items():
            for match in pattern.finditer(content):
                result['providers'].append(JakartaProviderInfo(
                    name=match.group(1), provider_type=provider_type,
                    file=file_path, line_number=content[:match.start()].count('\n') + 1,
                ))

        return result
