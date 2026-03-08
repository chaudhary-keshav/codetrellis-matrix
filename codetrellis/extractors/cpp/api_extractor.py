"""
CppAPIExtractor - Extracts C++ API patterns: REST, gRPC, WebSocket, IPC, signals.

This extractor parses C++ source code and extracts:
- REST API endpoints (Crow, Pistache, cpp-httplib, Boost.Beast, Drogon)
- gRPC service definitions and method implementations
- WebSocket handlers
- Qt signals/slots mechanism
- Boost.Asio networking patterns
- IPC mechanisms (shared memory, message queues, pipes)
- Callback patterns (std::function, function pointers)
- Event handling patterns

Supports all C++ standards: C++98 through C++26.

Part of CodeTrellis v4.20 - C++ Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CppEndpointInfo:
    """Information about a C++ REST API endpoint."""
    method: str = "GET"  # GET, POST, PUT, DELETE, PATCH
    path: str = ""
    handler_name: Optional[str] = None
    framework: str = ""  # crow, pistache, httplib, beast, drogon
    file: str = ""
    line_number: int = 0


@dataclass
class CppGrpcServiceInfo:
    """Information about a C++ gRPC service."""
    service_name: str = ""
    methods: List[str] = field(default_factory=list)
    is_async: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class CppSignalSlotInfo:
    """Information about a Qt signal or slot."""
    name: str = ""
    kind: str = "signal"  # signal, slot
    parameters: Optional[str] = None
    class_name: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CppCallbackInfo:
    """Information about a C++ callback pattern."""
    name: str = ""
    callback_type: str = ""  # std::function, function_pointer, lambda
    signature: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class CppNetworkingInfo:
    """Information about C++ networking usage."""
    api: str = ""  # boost::asio, socket, curl, etc.
    operation: str = ""  # accept, connect, listen, send, receive
    is_async: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class CppIPCInfo:
    """Information about C++ IPC mechanism."""
    mechanism: str = ""  # shared_memory, message_queue, pipe, named_pipe, socket
    operation: Optional[str] = None
    file: str = ""
    line_number: int = 0


class CppAPIExtractor:
    """
    Extracts C++ API patterns from source code.

    Handles:
    - REST API endpoints (Crow, Pistache, cpp-httplib, Boost.Beast, Drogon)
    - gRPC service implementations
    - Qt signals and slots
    - Boost.Asio networking patterns
    - POSIX socket operations
    - Callback patterns (std::function, function pointers)
    - WebSocket handlers
    - IPC mechanisms
    """

    # REST endpoint patterns by framework
    # Crow: CROW_ROUTE(app, "/path").methods("GET"_method)
    CROW_ROUTE = re.compile(
        r'CROW_ROUTE\s*\(\s*\w+\s*,\s*"(?P<path>[^"]+)"\s*\)'
        r'(?:\s*\.methods\s*\(\s*"?(?P<method>\w+)"?\s*(?:_method)?\s*\))?',
        re.MULTILINE
    )

    # Pistache: router.get("/path", handler) or Routes::Get(router, "/path", handler)
    PISTACHE_ROUTE = re.compile(
        r'(?:'
        r'(?:Routes?|router)\s*\.\s*(?P<method1>get|post|put|del|patch|head|options)\s*\(\s*"(?P<path1>[^"]+)"'
        r'|'
        r'Routes?\s*::\s*(?P<method2>Get|Post|Put|Delete|Patch|Head|Options)\s*\([^,]*,\s*"(?P<path2>[^"]+)"'
        r')',
        re.MULTILINE | re.IGNORECASE
    )

    # cpp-httplib: svr.Get("/path", handler)
    HTTPLIB_ROUTE = re.compile(
        r'(?:svr|server|srv)\s*\.\s*(?P<method>Get|Post|Put|Delete|Patch|Head|Options)\s*\(\s*"(?P<path>[^"]+)"',
        re.MULTILINE
    )

    # Drogon: app().registerHandler("/path", handler, {Get})
    DROGON_ROUTE = re.compile(
        r'(?:app\(\)|HttpAppFramework::instance\(\))\s*\.\s*registerHandler\s*\(\s*"(?P<path>[^"]+)"',
        re.MULTILINE
    )

    # Boost.Beast / generic HTTP handler
    BEAST_HANDLER = re.compile(
        r'(?:handle_request|on_request|http::request)\s*<\s*http::(?P<method>string_body|dynamic_body)',
        re.MULTILINE
    )

    # gRPC service implementation: class MyServiceImpl : public MyService::Service
    GRPC_SERVICE = re.compile(
        r'class\s+(?P<impl>\w+)\s*:\s*(?:public\s+)?(?P<service>[\w:]+)::Service',
        re.MULTILINE
    )

    # gRPC method override: Status MethodName(ServerContext*, const Request*, Response*)
    GRPC_METHOD = re.compile(
        r'(?:grpc::)?Status\s+(?P<name>\w+)\s*\(\s*(?:grpc::)?ServerContext',
        re.MULTILINE
    )

    # Qt signals
    QT_SIGNAL = re.compile(
        r'(?:signals|Q_SIGNALS)\s*:\s*(?P<body>(?:(?!(?:public|protected|private|slots|Q_SLOTS)\s*:)[^\n])*)',
        re.MULTILINE | re.DOTALL
    )

    # Qt slots
    QT_SLOT = re.compile(
        r'(?:(?:public|protected|private)\s+)?(?:slots|Q_SLOTS)\s*:\s*(?P<body>(?:(?!(?:public|protected|private|signals|Q_SIGNALS)\s*:)[^\n])*)',
        re.MULTILINE | re.DOTALL
    )

    # Qt connect
    QT_CONNECT = re.compile(
        r'(?:QObject::)?connect\s*\(\s*(?P<sender>[^,]+),\s*(?:SIGNAL|&\w+::)(?P<signal>[^,)]+)',
        re.MULTILINE
    )

    # Boost.Asio patterns
    ASIO_PATTERN = re.compile(
        r'(?:boost::asio|asio)::'
        r'(?P<op>async_read|async_write|async_connect|async_accept|io_context|'
        r'ip::tcp::acceptor|ip::tcp::socket|ip::udp::socket|'
        r'steady_timer|deadline_timer|strand|post|dispatch|spawn)',
        re.MULTILINE
    )

    # POSIX/BSD sockets
    SOCKET_PATTERN = re.compile(
        r'\b(?P<func>socket|bind|listen|accept|connect|send|recv|'
        r'sendto|recvfrom|setsockopt|getsockopt|select|poll|epoll_\w+|'
        r'getaddrinfo|gethostbyname)\s*\(',
        re.MULTILINE
    )

    # std::function callbacks
    STD_FUNCTION = re.compile(
        r'std::function\s*<\s*(?P<sig>[^>]+)>\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # IPC patterns
    IPC_PATTERN = re.compile(
        r'(?:boost::interprocess::|std::)?'
        r'(?P<mechanism>shared_memory_object|mapped_region|message_queue|'
        r'named_mutex|named_semaphore|named_condition|'
        r'pipe|mkfifo|mmap|shm_open|mq_open|sem_open|'
        r'shmget|shmat|shmdt|shmctl|msgget|msgsnd|msgrcv|msgctl|'
        r'semget|semop|semctl)\b',
        re.MULTILINE
    )

    # WebSocket patterns
    WEBSOCKET_PATTERN = re.compile(
        r'(?:websocket|ws|beast::websocket|websocketpp).*?'
        r'(?P<op>on_open|on_close|on_message|on_error|async_accept|async_read|async_write)',
        re.MULTILINE | re.IGNORECASE
    )

    def __init__(self):
        """Initialize the C++ API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all API patterns from C++ source code.

        Args:
            content: C++ source code content
            file_path: Path to source file

        Returns:
            Dict with 'endpoints', 'grpc_services', 'signals_slots', 'callbacks',
            'networking', 'ipc', 'websockets' lists
        """
        result = {
            'endpoints': [],
            'grpc_services': [],
            'signals_slots': [],
            'callbacks': [],
            'networking': [],
            'ipc': [],
            'websockets': [],
        }

        result['endpoints'] = self._extract_endpoints(content, file_path)
        result['grpc_services'] = self._extract_grpc(content, file_path)
        result['signals_slots'] = self._extract_qt_signals_slots(content, file_path)
        result['callbacks'] = self._extract_callbacks(content, file_path)
        result['networking'] = self._extract_networking(content, file_path)
        result['ipc'] = self._extract_ipc(content, file_path)
        result['websockets'] = self._extract_websockets(content, file_path)

        return result

    def _extract_endpoints(self, content: str, file_path: str) -> List[CppEndpointInfo]:
        """Extract REST API endpoints."""
        endpoints = []

        # Crow routes
        for match in self.CROW_ROUTE.finditer(content):
            path = match.group('path')
            method = match.group('method') or 'GET'
            line_num = content[:match.start()].count('\n') + 1
            endpoints.append(CppEndpointInfo(
                method=method.upper(),
                path=path,
                framework='crow',
                file=file_path,
                line_number=line_num,
            ))

        # Pistache routes
        for match in self.PISTACHE_ROUTE.finditer(content):
            method = (match.group('method1') or match.group('method2')).upper()
            if method == 'DEL':
                method = 'DELETE'
            path = match.group('path1') or match.group('path2')
            line_num = content[:match.start()].count('\n') + 1
            endpoints.append(CppEndpointInfo(
                method=method,
                path=path,
                framework='pistache',
                file=file_path,
                line_number=line_num,
            ))

        # cpp-httplib routes
        for match in self.HTTPLIB_ROUTE.finditer(content):
            method = match.group('method').upper()
            path = match.group('path')
            line_num = content[:match.start()].count('\n') + 1
            endpoints.append(CppEndpointInfo(
                method=method,
                path=path,
                framework='httplib',
                file=file_path,
                line_number=line_num,
            ))

        # Drogon routes
        for match in self.DROGON_ROUTE.finditer(content):
            path = match.group('path')
            line_num = content[:match.start()].count('\n') + 1
            endpoints.append(CppEndpointInfo(
                method='GET',
                path=path,
                framework='drogon',
                file=file_path,
                line_number=line_num,
            ))

        return endpoints

    def _extract_grpc(self, content: str, file_path: str) -> List[CppGrpcServiceInfo]:
        """Extract gRPC service implementations."""
        services = []
        for match in self.GRPC_SERVICE.finditer(content):
            impl_name = match.group('impl')
            service_name = match.group('service')
            line_num = content[:match.start()].count('\n') + 1

            # Find gRPC methods in the class
            methods = []
            for meth_match in self.GRPC_METHOD.finditer(content):
                methods.append(meth_match.group('name'))

            services.append(CppGrpcServiceInfo(
                service_name=service_name,
                methods=methods,
                file=file_path,
                line_number=line_num,
            ))
        return services

    def _extract_qt_signals_slots(self, content: str, file_path: str) -> List[CppSignalSlotInfo]:
        """Extract Qt signals and slots."""
        items = []

        # Check if Qt is used
        if not re.search(r'Q_OBJECT|Q_SIGNALS|Q_SLOTS|signals\s*:|slots\s*:', content):
            return items

        # Extract signals
        for match in self.QT_SIGNAL.finditer(content):
            body = match.group('body')
            line_base = content[:match.start()].count('\n') + 1
            for sig_match in re.finditer(r'void\s+(\w+)\s*\(([^)]*)\)\s*;', body):
                items.append(CppSignalSlotInfo(
                    name=sig_match.group(1),
                    kind='signal',
                    parameters=sig_match.group(2).strip() or None,
                    file=file_path,
                    line_number=line_base + body[:sig_match.start()].count('\n'),
                ))

        # Extract slots
        for match in self.QT_SLOT.finditer(content):
            body = match.group('body')
            line_base = content[:match.start()].count('\n') + 1
            for slot_match in re.finditer(r'(?:void|bool|int|QString)\s+(\w+)\s*\(([^)]*)\)\s*;', body):
                items.append(CppSignalSlotInfo(
                    name=slot_match.group(1),
                    kind='slot',
                    parameters=slot_match.group(2).strip() or None,
                    file=file_path,
                    line_number=line_base + body[:slot_match.start()].count('\n'),
                ))

        return items

    def _extract_callbacks(self, content: str, file_path: str) -> List[CppCallbackInfo]:
        """Extract callback patterns."""
        callbacks = []

        # std::function callbacks
        for match in self.STD_FUNCTION.finditer(content):
            sig = match.group('sig')
            name = match.group('name')
            line_num = content[:match.start()].count('\n') + 1
            callbacks.append(CppCallbackInfo(
                name=name,
                callback_type='std::function',
                signature=sig,
                file=file_path,
                line_number=line_num,
            ))

        return callbacks

    def _extract_networking(self, content: str, file_path: str) -> List[CppNetworkingInfo]:
        """Extract networking patterns."""
        networking = []

        # Boost.Asio
        for match in self.ASIO_PATTERN.finditer(content):
            op = match.group('op')
            line_num = content[:match.start()].count('\n') + 1
            is_async = op.startswith('async_')
            networking.append(CppNetworkingInfo(
                api='boost::asio',
                operation=op,
                is_async=is_async,
                file=file_path,
                line_number=line_num,
            ))

        # POSIX sockets
        for match in self.SOCKET_PATTERN.finditer(content):
            func = match.group('func')
            line_num = content[:match.start()].count('\n') + 1
            networking.append(CppNetworkingInfo(
                api='posix_socket',
                operation=func,
                file=file_path,
                line_number=line_num,
            ))

        return networking

    def _extract_ipc(self, content: str, file_path: str) -> List[CppIPCInfo]:
        """Extract IPC mechanism usage."""
        ipcs = []
        seen = set()
        for match in self.IPC_PATTERN.finditer(content):
            mechanism = match.group('mechanism')
            line_num = content[:match.start()].count('\n') + 1
            key = f"{mechanism}:{line_num}"
            if key not in seen:
                seen.add(key)
                ipcs.append(CppIPCInfo(
                    mechanism=mechanism,
                    file=file_path,
                    line_number=line_num,
                ))
        return ipcs

    def _extract_websockets(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract WebSocket handler patterns."""
        ws_handlers = []
        for match in self.WEBSOCKET_PATTERN.finditer(content):
            op = match.group('op')
            line_num = content[:match.start()].count('\n') + 1
            ws_handlers.append({
                'operation': op,
                'file': file_path,
                'line': line_num,
            })
        return ws_handlers
