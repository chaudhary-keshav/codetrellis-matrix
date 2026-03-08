"""
Akka HTTP Extractor - Extracts Akka HTTP route and server definitions.

Extracts:
- Route directives (path, get, post, put, delete, etc.)
- Path matchers and parameters
- Request/Response marshalling
- Rejection handlers
- Exception handlers
- Server bindings
- WebSocket support
- CORS and security directives
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AkkaHttpRouteInfo:
    """Information about an Akka HTTP route."""
    method: str = ""  # GET, POST, PUT, DELETE, etc.
    path: str = ""
    directives: List[str] = field(default_factory=list)
    has_entity: bool = False
    produces: str = ""
    consumes: str = ""
    line_number: int = 0


@dataclass
class AkkaHttpDirectiveInfo:
    """Information about custom or notable directives."""
    directive_name: str = ""
    directive_type: str = ""  # routing, security, marshalling, custom
    parameters: List[str] = field(default_factory=list)
    line_number: int = 0


class AkkaHttpExtractor:
    """Extracts Akka HTTP route and directive information."""

    # HTTP method directives
    METHOD_PATTERN = re.compile(
        r'\b(get|post|put|delete|patch|head|options)\s*\(',
        re.MULTILINE
    )

    # Path directives
    PATH_PATTERN = re.compile(
        r'(?:path|pathPrefix|pathEnd|pathSingleSlash|rawPathPrefix|'
        r'rawPathPrefixTest|pathSuffix|pathSuffixTest)\s*\(\s*["\']([^"\']*)["\']',
        re.MULTILINE
    )

    PATH_MATCHER_PATTERN = re.compile(
        r'(?:path|pathPrefix)\s*\(\s*'
        r'(?:(?:IntNumber|LongNumber|HexIntNumber|DoubleNumber|'
        r'JavaUUID|Segment|Remaining|Segments|Slash|PathEnd)\b'
        r'|["\']([^"\']*)["\'])',
        re.MULTILINE
    )

    # Parameter extraction
    PARAMETER_PATTERN = re.compile(
        r'(?:parameter|parameters|parameterMap|parameterMultiMap|'
        r'parameterSeq)\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # Entity / Marshalling
    ENTITY_PATTERN = re.compile(
        r'(?:entity\s*\(\s*as\s*\[\s*(\w+)|'
        r'as\s*\(\s*Jackson\.\w+\s*\(\s*classOf\s*\[\s*(\w+)|'
        r'entity\s*\(\s*Jackson\.unmarshaller)',
        re.MULTILINE
    )

    COMPLETE_PATTERN = re.compile(
        r'complete\s*\(\s*(?:StatusCodes\.(\w+)|(\d{3}))?',
        re.MULTILINE
    )

    MARSHAL_PATTERN = re.compile(
        r'(?:Jackson\.\s*(?:marshaller|unmarshaller)|'
        r'SprayJsonSupport|'
        r'akka\.http\.scaladsl\.marshallers\.sprayjson|'
        r'akka\.http\.javadsl\.marshallers\.jackson|'
        r'Marshaller\.\s*(?:opaque|stringMarshaller)|'
        r'Unmarshaller\.\s*\w+)',
        re.MULTILINE
    )

    # Rejection handling
    REJECTION_HANDLER_PATTERN = re.compile(
        r'RejectionHandler\s*\.\s*(?:newBuilder|default)|'
        r'handleRejections\s*\(|'
        r'\.handle\s*\(\s*classOf\s*\[\s*(\w+Rejection)',
        re.MULTILINE
    )

    # Exception handling
    EXCEPTION_HANDLER_PATTERN = re.compile(
        r'ExceptionHandler\s*\{|'
        r'handleExceptions\s*\(|'
        r'ExceptionHandler\s*\.\s*newBuilder',
        re.MULTILINE
    )

    # Server binding
    SERVER_BIND_PATTERN = re.compile(
        r'Http\s*\(\s*\)\s*\.(?:newServerAt|bindAndHandle|bind)\s*\(',
        re.MULTILINE
    )

    HOST_PORT_PATTERN = re.compile(
        r'\.(?:newServerAt|bindAndHandle|bind)\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\d+)',
        re.MULTILINE
    )

    # WebSocket
    WEBSOCKET_PATTERN = re.compile(
        r'handleWebSocketMessages\s*\(|'
        r'handleWebSocketMessagesForProtocol\s*\(|'
        r'WebSocket\.\s*(?:handleMessages|createServer)|'
        r'TextMessage|BinaryMessage|UpgradeToWebSocket',
        re.MULTILINE
    )

    # Security directives
    SECURITY_PATTERN = re.compile(
        r'(?:authenticateBasic|authenticateOAuth2|'
        r'authenticateBasicAsync|authenticateOAuth2Async|'
        r'authorize|authorizeAsync|'
        r'optionalHeaderValueByName|headerValueByName)\s*\(',
        re.MULTILINE
    )

    # CORS
    CORS_PATTERN = re.compile(
        r'cors\s*\(|respondWithHeaders?\s*\(\s*.*?Access-Control|'
        r'CorsSettings|ch\.megard\.akka\.http\.cors',
        re.MULTILINE
    )

    # Concat routes
    CONCAT_PATTERN = re.compile(
        r'concat\s*\(|~\s*(?:path|get|post|put|delete)',
        re.MULTILINE
    )

    # Custom directives
    CUSTOM_DIRECTIVE_PATTERN = re.compile(
        r'(?:def|val|private\s+def)\s+(\w+)\s*(?::\s*(?:Route|Directive\w*)\s*=|'
        r'=\s*(?:extract|provide|mapResponse|mapRequest|textract))',
        re.MULTILINE
    )

    # File upload / multipart
    FILE_UPLOAD_PATTERN = re.compile(
        r'(?:fileUpload|storeUploadedFile|storeUploadedFiles|'
        r'formField|formFields|formFieldMap|'
        r'toStrictEntity|withSizeLimit)\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Akka HTTP information."""
        routes: List[AkkaHttpRouteInfo] = []
        directives: List[AkkaHttpDirectiveInfo] = []
        metadata: Dict[str, Any] = {
            'has_websocket': False,
            'has_rejection_handler': False,
            'has_exception_handler': False,
            'has_cors': False,
            'has_file_upload': False,
            'server_bindings': [],
            'security_mechanisms': [],
            'marshal_formats': [],
        }

        if not content or not content.strip():
            return {'routes': routes, 'directives': directives, 'metadata': metadata}

        # Routes (methods + paths)
        for match in self.METHOD_PATTERN.finditer(content):
            route = AkkaHttpRouteInfo(
                method=match.group(1).upper(),
                line_number=content[:match.start()].count('\n') + 1,
            )
            routes.append(route)

        # Path directives
        for match in self.PATH_PATTERN.finditer(content):
            directives.append(AkkaHttpDirectiveInfo(
                directive_name=match.group(0).split('(')[0].strip(),
                directive_type="routing",
                parameters=[match.group(1)] if match.group(1) else [],
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Security
        for match in self.SECURITY_PATTERN.finditer(content):
            name = match.group(0).split('(')[0].strip()
            metadata['security_mechanisms'].append(name)
            directives.append(AkkaHttpDirectiveInfo(
                directive_name=name,
                directive_type="security",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Marshalling
        for match in self.MARSHAL_PATTERN.finditer(content):
            metadata['marshal_formats'].append(match.group(0).strip())

        # WebSocket
        if self.WEBSOCKET_PATTERN.search(content):
            metadata['has_websocket'] = True

        # Rejection handler
        if self.REJECTION_HANDLER_PATTERN.search(content):
            metadata['has_rejection_handler'] = True

        # Exception handler
        if self.EXCEPTION_HANDLER_PATTERN.search(content):
            metadata['has_exception_handler'] = True

        # CORS
        if self.CORS_PATTERN.search(content):
            metadata['has_cors'] = True

        # File upload
        if self.FILE_UPLOAD_PATTERN.search(content):
            metadata['has_file_upload'] = True

        # Server bindings
        for match in self.HOST_PORT_PATTERN.finditer(content):
            metadata['server_bindings'].append({
                'host': match.group(1),
                'port': int(match.group(2)),
            })

        # Custom directives
        for match in self.CUSTOM_DIRECTIVE_PATTERN.finditer(content):
            directives.append(AkkaHttpDirectiveInfo(
                directive_name=match.group(1),
                directive_type="custom",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return {'routes': routes, 'directives': directives, 'metadata': metadata}
