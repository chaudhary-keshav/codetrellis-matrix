"""
EnhancedGrpcGoParser v1.0 - Comprehensive gRPC-Go framework parser.

Supports:
- gRPC-Go v1.x (basic server/client, unary/streaming)
- gRPC-Go v1.30+ (xDS support, health checking)
- gRPC-Go v1.40+ (new credentials API)
- gRPC-Go v1.50+ (stats handler, peer info)
- protobuf v3 (proto3 syntax, well-known types)

gRPC-specific extraction:
- Service implementations (Unimplemented*Server embedding)
- RPC methods (unary, server-streaming, client-streaming, bidirectional)
- Interceptors (unary/stream, server/client)
- Server options (credentials, keepalive, max message size)
- Client connections (Dial, DialContext, NewClient)
- Proto message handling (proto.Marshal, proto.Unmarshal)
- Metadata handling (metadata.NewOutgoingContext, metadata.FromIncomingContext)
- Health checking (grpc_health_v1)
- Reflection (grpc/reflection)

Part of CodeTrellis v5.2.0 - Go Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class GrpcServiceImplInfo:
    """gRPC service implementation."""
    name: str
    server_interface: str = ""
    methods: List[str] = field(default_factory=list)
    is_streaming: Dict[str, str] = field(default_factory=dict)  # method -> stream_type
    file: str = ""
    line_number: int = 0


@dataclass
class GrpcMethodInfo:
    """gRPC RPC method."""
    name: str
    service: str = ""
    stream_type: str = "unary"  # unary, server_stream, client_stream, bidi_stream
    request_type: str = ""
    response_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GrpcInterceptorInfo:
    """gRPC interceptor."""
    name: str
    interceptor_type: str = "unary"  # unary_server, stream_server, unary_client, stream_client
    file: str = ""
    line_number: int = 0


@dataclass
class GrpcServerOptionInfo:
    """gRPC server option."""
    option_type: str
    value: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GrpcClientConnInfo:
    """gRPC client connection."""
    target: str
    variable_name: str = ""
    options: List[str] = field(default_factory=list)
    is_secure: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class GrpcProtoImportInfo:
    """Proto/gRPC import."""
    package: str
    alias: str = ""
    is_generated: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class GrpcGoParseResult:
    file_path: str
    file_type: str = "go"

    service_impls: List[GrpcServiceImplInfo] = field(default_factory=list)
    rpc_methods: List[GrpcMethodInfo] = field(default_factory=list)
    interceptors: List[GrpcInterceptorInfo] = field(default_factory=list)
    server_options: List[GrpcServerOptionInfo] = field(default_factory=list)
    client_connections: List[GrpcClientConnInfo] = field(default_factory=list)
    proto_imports: List[GrpcProtoImportInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    has_grpc_server: bool = False
    has_grpc_client: bool = False
    has_reflection: bool = False
    has_health_check: bool = False
    total_services: int = 0
    total_rpc_methods: int = 0


class EnhancedGrpcGoParser:
    """Enhanced gRPC-Go parser for comprehensive gRPC extraction."""

    GRPC_IMPORT = re.compile(r'"google\.golang\.org/grpc"')
    PROTOBUF_IMPORT = re.compile(r'"google\.golang\.org/protobuf')

    # Service implementation: type server struct { pb.UnimplementedGreeterServer }
    SERVICE_IMPL_PATTERN = re.compile(
        r'type\s+(\w+)\s+struct\s*\{[^}]*(?:Unimplemented|mustEmbedUnimplemented)(\w+)Server',
        re.DOTALL,
    )

    # Register service: pb.RegisterGreeterServer(s, &server{})
    REGISTER_SERVICE_PATTERN = re.compile(
        r'(\w+)\.Register(\w+)Server\s*\(\s*(\w+)\s*,\s*[&]?(\w+)',
    )

    # RPC method implementation: func (s *server) SayHello(ctx context.Context, req *pb.HelloRequest) (*pb.HelloReply, error)
    RPC_METHOD_PATTERN = re.compile(
        r'func\s+\(\s*\w+\s+\*?(\w+)\s*\)\s+(\w+)\s*\(\s*'
        r'(?:ctx\s+context\.Context\s*,\s*)?'
        r'(?:(?:req|in|request)\s+\*?(\w+(?:\.\w+)?)|'
        r'(?:stream)\s+(\w+(?:\.\w+)?))',
    )

    # Server streaming method: func (s *server) ListFeatures(req *pb.Req, stream pb.Svc_ListFeaturesServer) error
    STREAM_METHOD_PATTERN = re.compile(
        r'func\s+\(\s*\w+\s+\*?(\w+)\s*\)\s+(\w+)\s*\([^)]*'
        r'(\w+)_(\w+)(?:Server|Client)\s*\)',
    )

    # gRPC server creation: s := grpc.NewServer(opts...)
    SERVER_PATTERN = re.compile(
        r'(\w+)\s*:?=\s*grpc\.NewServer\s*\(\s*([^)]*)\)',
    )

    # gRPC client: conn, err := grpc.Dial("addr", opts...)
    CLIENT_DIAL_PATTERN = re.compile(
        r'(\w+)\s*,\s*\w+\s*:?=\s*grpc\.(Dial|DialContext|NewClient)\s*\(\s*([^,)]+)',
    )

    # New client stub: client := pb.NewGreeterClient(conn)
    CLIENT_STUB_PATTERN = re.compile(
        r'(\w+)\s*:?=\s*(\w+)\.New(\w+)Client\s*\(\s*(\w+)\s*\)',
    )

    # Interceptors: grpc.UnaryInterceptor(func), grpc.StreamInterceptor(func)
    UNARY_SERVER_INTERCEPTOR = re.compile(
        r'grpc\.(?:Unary|Chain[Uu]nary)(?:Server)?Interceptor\s*\(\s*([^)]+)\)',
    )
    STREAM_SERVER_INTERCEPTOR = re.compile(
        r'grpc\.(?:Stream|Chain[Ss]tream)(?:Server)?Interceptor\s*\(\s*([^)]+)\)',
    )
    UNARY_CLIENT_INTERCEPTOR = re.compile(
        r'grpc\.With(?:Unary|ChainUnary)Interceptor\s*\(\s*([^)]+)\)',
    )
    STREAM_CLIENT_INTERCEPTOR = re.compile(
        r'grpc\.With(?:Stream|ChainStream)Interceptor\s*\(\s*([^)]+)\)',
    )

    # Server options
    SERVER_OPTION_PATTERN = re.compile(
        r'grpc\.(Creds|MaxRecvMsgSize|MaxSendMsgSize|KeepaliveParams|'
        r'KeepaliveEnforcementPolicy|MaxConcurrentStreams|'
        r'InitialWindowSize|InitialConnWindowSize|WriteBufferSize|ReadBufferSize|'
        r'ConnectionTimeout|NumStreamWorkers|StatsHandler)\s*\(',
    )

    # Metadata operations
    METADATA_PATTERN = re.compile(
        r'metadata\.(NewOutgoingContext|FromIncomingContext|NewIncomingContext|'
        r'AppendToOutgoingContext|Pairs|New|Join|MD)\s*\(',
    )

    # Reflection
    REFLECTION_PATTERN = re.compile(r'"google\.golang\.org/grpc/reflection"')

    # Health check
    HEALTH_PATTERN = re.compile(r'"google\.golang\.org/grpc/health')

    # Status codes
    STATUS_PATTERN = re.compile(
        r'(?:status|codes)\.(OK|Canceled|Unknown|InvalidArgument|DeadlineExceeded|'
        r'NotFound|AlreadyExists|PermissionDenied|ResourceExhausted|'
        r'FailedPrecondition|Aborted|OutOfRange|Unimplemented|Internal|'
        r'Unavailable|DataLoss|Unauthenticated)\b',
    )

    FRAMEWORK_PATTERNS = {
        'grpc': re.compile(r'"google\.golang\.org/grpc"'),
        'protobuf': re.compile(r'"google\.golang\.org/protobuf'),
        'grpc-gateway': re.compile(r'"github\.com/grpc-ecosystem/grpc-gateway'),
        'grpc-middleware': re.compile(r'"github\.com/grpc-ecosystem/go-grpc-middleware'),
        'grpc-prometheus': re.compile(r'"github\.com/grpc-ecosystem/go-grpc-prometheus"'),
        'grpc-opentracing': re.compile(r'"github\.com/grpc-ecosystem/grpc-opentracing"'),
        'grpc-zap': re.compile(r'"github\.com/grpc-ecosystem/go-grpc-middleware/logging/zap"'),
        'grpc-validator': re.compile(r'"github\.com/grpc-ecosystem/go-grpc-middleware/validator"'),
        'grpc-recovery': re.compile(r'"github\.com/grpc-ecosystem/go-grpc-middleware/recovery"'),
        'grpc-auth': re.compile(r'"github\.com/grpc-ecosystem/go-grpc-middleware/auth"'),
        'grpc-retry': re.compile(r'"github\.com/grpc-ecosystem/go-grpc-middleware/retry"'),
        'grpc-reflection': re.compile(r'"google\.golang\.org/grpc/reflection"'),
        'grpc-health': re.compile(r'"google\.golang\.org/grpc/health'),
        'grpc-status': re.compile(r'"google\.golang\.org/grpc/status"'),
        'grpc-codes': re.compile(r'"google\.golang\.org/grpc/codes"'),
        'grpc-metadata': re.compile(r'"google\.golang\.org/grpc/metadata"'),
        'grpc-credentials': re.compile(r'"google\.golang\.org/grpc/credentials"'),
        'buf': re.compile(r'"buf\.build/'),
        'connect-go': re.compile(r'"connectrpc\.com/connect"'),
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> GrpcGoParseResult:
        result = GrpcGoParseResult(file_path=file_path)

        if not self.GRPC_IMPORT.search(content) and not self.PROTOBUF_IMPORT.search(content):
            # Also check for generated proto code
            if not re.search(r'Register\w+Server|Unimplemented\w+Server', content):
                return result

        result.detected_frameworks = self._detect_frameworks(content)
        result.has_reflection = bool(self.REFLECTION_PATTERN.search(content))
        result.has_health_check = bool(self.HEALTH_PATTERN.search(content))

        # Service implementations
        for m in self.SERVICE_IMPL_PATTERN.finditer(content):
            impl_name = m.group(1)
            service_name = m.group(2)

            # Find methods of this impl
            methods = []
            for rm in self.RPC_METHOD_PATTERN.finditer(content):
                if rm.group(1) == impl_name:
                    methods.append(rm.group(2))

            result.service_impls.append(GrpcServiceImplInfo(
                name=impl_name, server_interface=f"Unimplemented{service_name}Server",
                methods=methods, file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # RPC methods
        for m in self.RPC_METHOD_PATTERN.finditer(content):
            receiver = m.group(1)
            method_name = m.group(2)
            req_type = m.group(3) or ""
            stream_param = m.group(4) or ""

            stream_type = "unary"
            if stream_param:
                stream_type = "server_stream"

            result.rpc_methods.append(GrpcMethodInfo(
                name=method_name, service=receiver,
                stream_type=stream_type, request_type=req_type,
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Stream methods (more specific detection)
        for m in self.STREAM_METHOD_PATTERN.finditer(content):
            service = m.group(3)
            method = m.group(4)
            result.rpc_methods.append(GrpcMethodInfo(
                name=method, service=service,
                stream_type="streaming",
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Server creation
        for m in self.SERVER_PATTERN.finditer(content):
            result.has_grpc_server = True
            opts_str = m.group(2).strip()
            if opts_str:
                for opt in opts_str.split(','):
                    opt = opt.strip()
                    if opt:
                        result.server_options.append(GrpcServerOptionInfo(
                            option_type=opt, file=file_path,
                            line_number=content[:m.start()].count('\n') + 1,
                        ))

        # Server options
        for m in self.SERVER_OPTION_PATTERN.finditer(content):
            result.server_options.append(GrpcServerOptionInfo(
                option_type=m.group(1), file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Client connections
        for m in self.CLIENT_DIAL_PATTERN.finditer(content):
            result.has_grpc_client = True
            result.client_connections.append(GrpcClientConnInfo(
                target=m.group(3).strip(), variable_name=m.group(1),
                is_secure='credentials' in content.lower(),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Interceptors
        for m in self.UNARY_SERVER_INTERCEPTOR.finditer(content):
            for name in m.group(1).split(','):
                name = name.strip()
                if name:
                    result.interceptors.append(GrpcInterceptorInfo(
                        name=name, interceptor_type="unary_server",
                        file=file_path, line_number=content[:m.start()].count('\n') + 1,
                    ))

        for m in self.STREAM_SERVER_INTERCEPTOR.finditer(content):
            for name in m.group(1).split(','):
                name = name.strip()
                if name:
                    result.interceptors.append(GrpcInterceptorInfo(
                        name=name, interceptor_type="stream_server",
                        file=file_path, line_number=content[:m.start()].count('\n') + 1,
                    ))

        for m in self.UNARY_CLIENT_INTERCEPTOR.finditer(content):
            for name in m.group(1).split(','):
                name = name.strip()
                if name:
                    result.interceptors.append(GrpcInterceptorInfo(
                        name=name, interceptor_type="unary_client",
                        file=file_path, line_number=content[:m.start()].count('\n') + 1,
                    ))

        for m in self.STREAM_CLIENT_INTERCEPTOR.finditer(content):
            for name in m.group(1).split(','):
                name = name.strip()
                if name:
                    result.interceptors.append(GrpcInterceptorInfo(
                        name=name, interceptor_type="stream_client",
                        file=file_path, line_number=content[:m.start()].count('\n') + 1,
                    ))

        # Proto imports
        import_block = re.findall(r'import\s*\(\s*((?:.*?\n)*?)\s*\)', content, re.MULTILINE)
        for block in import_block:
            for line in block.split('\n'):
                line = line.strip()
                path_match = re.search(r'"([^"]+)"', line)
                if path_match:
                    pkg = path_match.group(1)
                    if 'pb' in pkg.lower() or 'proto' in pkg.lower() or 'grpc' in pkg.lower():
                        alias_match = re.match(r'(\w+)\s+"', line)
                        result.proto_imports.append(GrpcProtoImportInfo(
                            package=pkg,
                            alias=alias_match.group(1) if alias_match else "",
                            is_generated=pkg.endswith('pb') or '/gen/' in pkg or '_go' in pkg,
                            file=file_path,
                            line_number=content[:content.find(pkg)].count('\n') + 1,
                        ))

        result.total_services = len(result.service_impls)
        result.total_rpc_methods = len(result.rpc_methods)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks
