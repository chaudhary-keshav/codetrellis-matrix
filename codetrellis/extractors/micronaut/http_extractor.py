"""
Micronaut HTTP Extractor v1.0 - Controllers, endpoints, filters, declarative clients.
Part of CodeTrellis v4.94 - Micronaut Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class MicronautControllerInfo:
    """A Micronaut controller."""
    name: str
    base_path: str = ""
    endpoints: List[Dict] = field(default_factory=list)
    is_reactive: bool = False
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class MicronautEndpointInfo:
    """An HTTP endpoint."""
    path: str
    method: str  # GET, POST, PUT, DELETE, PATCH, etc.
    function_name: str = ""
    consumes: str = ""
    produces: str = ""
    return_type: str = ""
    params: List[str] = field(default_factory=list)
    is_reactive: bool = False
    is_blocking: bool = False
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class MicronautFilterInfo:
    """An HTTP filter."""
    name: str
    filter_type: str = ""  # server, client
    pattern: str = ""
    order: int = 0
    file: str = ""
    line_number: int = 0


@dataclass
class MicronautClientInfo:
    """A declarative HTTP client."""
    name: str
    client_id: str = ""
    base_path: str = ""
    endpoints: List[Dict] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class MicronautHTTPExtractor:
    """Extracts Micronaut HTTP patterns."""

    CONTROLLER_PATTERN = re.compile(
        r'@Controller\(\s*"?([^")\s]*)"?\s*\)\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    ENDPOINT_PATTERN = re.compile(
        r'@(Get|Post|Put|Delete|Patch|Head|Options|Trace)'
        r'(?:\(\s*"?([^")\s]*)"?\s*\))?\s*\n'
        r'(?:@(?:Produces|Consumes|Status|Blocking)\([^)]*\)\s*\n)*'
        r'(?:(?:public|protected|private)\s+)?'
        r'(?:static\s+)?(?:final\s+)?'
        r'([\w<>,?\[\]]+)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    PARAM_PATTERN = re.compile(
        r'@(PathVariable|QueryValue|Header|CookieValue|Body|Part|RequestAttribute)\s*'
        r'(?:\(\s*"?([^")]*)"?\s*\))?\s+'
        r'([\w<>,?\[\]]+)\s+(\w+)',
        re.MULTILINE
    )

    CLIENT_PATTERN = re.compile(
        r'@Client\(\s*(?:id\s*=\s*)?"?([^")\s]*)"?\s*'
        r'(?:,\s*path\s*=\s*"([^"]*)")?\s*\)\s*\n'
        r'(?:public\s+)?interface\s+(\w+)',
        re.MULTILINE
    )

    FILTER_PATTERN = re.compile(
        r'@(ServerFilter|ClientFilter|Filter)\(\s*"?([^")\s]*)"?\s*\)\s*\n'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    FILTER_IMPL_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+HttpServerFilter',
        re.MULTILINE
    )

    REACTIVE_TYPES = {'Mono', 'Flux', 'Publisher', 'Maybe', 'Single', 'Flowable', 'Observable', 'CompletableFuture'}

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'controllers': [], 'endpoints': [], 'filters': [], 'clients': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract controllers
        base_path = ""
        for match in self.CONTROLLER_PATTERN.finditer(content):
            base_path = match.group(1) or ""
            result['controllers'].append(MicronautControllerInfo(
                name=match.group(2), base_path=base_path,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract endpoints
        for match in self.ENDPOINT_PATTERN.finditer(content):
            http_method = match.group(1).upper()
            path = match.group(2) or ""
            return_type = match.group(3)
            function_name = match.group(4)

            full_path = base_path.rstrip('/') + '/' + path.lstrip('/') if path else base_path
            is_reactive = any(rt in return_type for rt in self.REACTIVE_TYPES)

            # Look for @Blocking annotation
            pre_text = content[max(0, match.start()-100):match.start()]
            is_blocking = bool(re.search(r'@Blocking', pre_text))

            result['endpoints'].append(MicronautEndpointInfo(
                path=full_path, method=http_method,
                function_name=function_name,
                return_type=return_type,
                is_reactive=is_reactive, is_blocking=is_blocking,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Update controller metadata
        for ctrl in result['controllers']:
            ctrl.endpoints = [
                {'method': ep.method, 'path': ep.path, 'function': ep.function_name}
                for ep in result['endpoints']
            ]
            ctrl.is_reactive = any(ep.is_reactive for ep in result['endpoints'])

        # Extract filters
        for match in self.FILTER_PATTERN.finditer(content):
            filter_type_raw = match.group(1)
            filter_type = 'server' if 'Server' in filter_type_raw else ('client' if 'Client' in filter_type_raw else 'server')
            result['filters'].append(MicronautFilterInfo(
                name=match.group(3), filter_type=filter_type,
                pattern=match.group(2) or "",
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.FILTER_IMPL_PATTERN.finditer(content):
            result['filters'].append(MicronautFilterInfo(
                name=match.group(1), filter_type='server',
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract declarative clients
        for match in self.CLIENT_PATTERN.finditer(content):
            client_id = match.group(1)
            client_path = match.group(2) or ""
            client_name = match.group(3)

            # Find methods in interface
            iface_start = match.end()
            client_endpoints = []
            for em in self.ENDPOINT_PATTERN.finditer(content[iface_start:iface_start+2000]):
                client_endpoints.append({
                    'method': em.group(1).upper(),
                    'path': em.group(2) or "",
                    'function': em.group(4),
                })

            result['clients'].append(MicronautClientInfo(
                name=client_name, client_id=client_id,
                base_path=client_path, endpoints=client_endpoints,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        return result
