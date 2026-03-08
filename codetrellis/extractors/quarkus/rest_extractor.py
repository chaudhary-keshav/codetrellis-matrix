"""
Quarkus REST Extractor v1.0 - RESTEasy Reactive endpoints, JAX-RS resources, filters.
Part of CodeTrellis v4.94 - Quarkus Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class QuarkusEndpointInfo:
    """A REST endpoint in Quarkus."""
    path: str
    method: str  # GET, POST, PUT, DELETE, PATCH, etc.
    function_name: str = ""
    consumes: str = ""
    produces: str = ""
    params: List[str] = field(default_factory=list)
    return_type: str = ""
    is_reactive: bool = False  # Uni<T>, Multi<T>
    is_blocking: bool = False  # @Blocking
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class QuarkusResourceInfo:
    """A JAX-RS resource class."""
    name: str
    base_path: str = ""
    endpoints: List[Dict] = field(default_factory=list)
    is_reactive: bool = False
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class QuarkusFilterInfo:
    """A REST filter or interceptor."""
    name: str
    filter_type: str = ""  # request, response, exception_mapper, reader_interceptor, writer_interceptor
    priority: int = 0
    file: str = ""
    line_number: int = 0


class QuarkusRESTExtractor:
    """Extracts Quarkus REST/JAX-RS patterns."""

    CLASS_PATH_PATTERN = re.compile(
        r'@Path\(\s*"([^"]+)"\s*\)\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    ENDPOINT_PATTERN = re.compile(
        r'@(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\n'
        r'(?:@Path\(\s*"([^"]*)"\s*\)\s*\n)?'
        r'(?:@Produces\(\s*"?([^")]+)"?\s*\)\s*\n)?'
        r'(?:@Consumes\(\s*"?([^")]+)"?\s*\)\s*\n)?'
        r'(?:@Blocking\s*\n)?'
        r'(?:public\s+)?([\w<>,?\[\]]+)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    PARAM_PATTERN = re.compile(
        r'@(PathParam|QueryParam|HeaderParam|FormParam|BeanParam|CookieParam|MatrixParam)\(\s*"?([^")]*)"?\s*\)\s+'
        r'(?:[\w<>,?\[\]]+)\s+(\w+)',
        re.MULTILINE
    )

    FILTER_PATTERNS = {
        'request': re.compile(r'class\s+(\w+)\s+implements\s+(?:ContainerRequestFilter|ServerRequestFilter)', re.MULTILINE),
        'response': re.compile(r'class\s+(\w+)\s+implements\s+(?:ContainerResponseFilter|ServerResponseFilter)', re.MULTILINE),
        'exception_mapper': re.compile(r'@Provider\s*\n(?:public\s+)?class\s+(\w+)\s+implements\s+ExceptionMapper', re.MULTILINE),
        'reader_interceptor': re.compile(r'class\s+(\w+)\s+implements\s+ReaderInterceptor', re.MULTILINE),
        'writer_interceptor': re.compile(r'class\s+(\w+)\s+implements\s+WriterInterceptor', re.MULTILINE),
    }

    REACTIVE_TYPES = {'Uni', 'Multi', 'CompletionStage', 'CompletableFuture', 'Publisher'}

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'endpoints': [], 'resources': [], 'filters': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract resource classes
        base_path = ""
        for match in self.CLASS_PATH_PATTERN.finditer(content):
            base_path = match.group(1)
            result['resources'].append(QuarkusResourceInfo(
                name=match.group(2), base_path=base_path,
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
            is_reactive = any(rt in return_type for rt in self.REACTIVE_TYPES)
            is_blocking = bool(re.search(r'@Blocking', content[max(0, match.start()-100):match.start()]))

            # Extract params for this method
            method_start = match.start()
            method_end = content.find('\n\n', match.end())
            if method_end == -1:
                method_end = len(content)
            method_text = content[method_start:method_end]
            params = [f"@{m.group(1)}({m.group(2)}) {m.group(3)}"
                      for m in self.PARAM_PATTERN.finditer(method_text)]

            result['endpoints'].append(QuarkusEndpointInfo(
                path=full_path, method=http_method,
                function_name=function_name,
                consumes=consumes, produces=produces,
                params=params, return_type=return_type,
                is_reactive=is_reactive, is_blocking=is_blocking,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Update resource endpoint counts
        for resource in result['resources']:
            resource.endpoints = [
                {'method': ep.method, 'path': ep.path, 'function': ep.function_name}
                for ep in result['endpoints']
            ]
            resource.is_reactive = any(ep.is_reactive for ep in result['endpoints'])

        # Extract filters
        for filter_type, pattern in self.FILTER_PATTERNS.items():
            for match in pattern.finditer(content):
                result['filters'].append(QuarkusFilterInfo(
                    name=match.group(1), filter_type=filter_type,
                    file=file_path, line_number=content[:match.start()].count('\n') + 1,
                ))

        return result
