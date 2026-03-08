"""
CAPIExtractor - Extracts C API patterns: sockets, signal handlers, IPC, callbacks.

This extractor parses C source code and extracts:
- Socket API usage (socket, bind, listen, connect, accept, send, recv)
- Signal handlers (signal(), sigaction())
- IPC mechanisms (pipe, mmap, shmget, semget, msgget)
- HTTP/RPC server patterns (libevent, libmicrohttpd, gRPC C)
- Callback registrations (function pointers passed to APIs)
- System call wrappers (ioctl, fcntl, epoll, select, poll)

Part of CodeTrellis v4.19 - C Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSocketAPIInfo:
    """Information about a C socket API usage."""
    function: str  # socket, bind, listen, connect, accept, send, recv, etc.
    family: str = ""  # AF_INET, AF_INET6, AF_UNIX
    socket_type: str = ""  # SOCK_STREAM, SOCK_DGRAM
    protocol: str = ""  # IPPROTO_TCP, IPPROTO_UDP
    file: str = ""
    line_number: int = 0


@dataclass
class CSignalHandlerInfo:
    """Information about a C signal handler."""
    signal_name: str  # SIGINT, SIGTERM, SIGUSR1, etc.
    handler_name: str
    is_sigaction: bool = False  # Uses sigaction() vs signal()
    file: str = ""
    line_number: int = 0


@dataclass
class CIPCInfo:
    """Information about C IPC mechanism usage."""
    mechanism: str  # pipe, mmap, shmget, semget, msgget, socketpair
    file: str = ""
    line_number: int = 0
    details: Optional[str] = None


@dataclass
class CCallbackInfo:
    """Information about a callback registration in C."""
    function: str  # The API function receiving the callback
    callback_name: str  # The callback function name
    callback_param_pos: int = 0  # Position of callback parameter
    file: str = ""
    line_number: int = 0


class CAPIExtractor:
    """
    Extracts C API patterns from source code.

    Detects:
    - BSD socket API (socket, bind, listen, connect, accept)
    - Async I/O (select, poll, epoll, kqueue, io_uring)
    - Signal handling (signal, sigaction, kill, raise)
    - IPC (pipe, mmap, shmget, semaphores, message queues)
    - HTTP server libraries (libevent, libmicrohttpd, libcurl)
    - Threading (pthread_create, mutex, rwlock, condition)
    - Callback patterns
    """

    # Socket API functions
    SOCKET_PATTERN = re.compile(
        r'\b(socket|bind|listen|connect|accept|send|recv|'
        r'sendto|recvfrom|sendmsg|recvmsg|'
        r'setsockopt|getsockopt|'
        r'getaddrinfo|freeaddrinfo|'
        r'select|poll|epoll_create|epoll_ctl|epoll_wait|'
        r'kqueue|kevent|io_uring_queue_init|io_uring_submit)\s*\(',
        re.MULTILINE
    )

    # Address family patterns
    AF_PATTERN = re.compile(r'\b(AF_INET6?|AF_UNIX|AF_LOCAL|AF_UNSPEC)\b')

    # Socket type patterns
    SOCK_TYPE_PATTERN = re.compile(r'\b(SOCK_STREAM|SOCK_DGRAM|SOCK_RAW|SOCK_SEQPACKET)\b')

    # Signal handler patterns — signal(SIG..., handler)
    SIGNAL_PATTERN = re.compile(
        r'\bsignal\s*\(\s*(?P<sig>SIG\w+)\s*,\s*(?P<handler>\w+)',
        re.MULTILINE
    )

    # sigaction call — may pass a struct pointer (&sa), not handler directly
    SIGACTION_CALL_PATTERN = re.compile(
        r'\bsigaction\s*\(\s*(?P<sig>SIG\w+)\s*,',
        re.MULTILINE
    )

    # Struct field assignment for sigaction handler
    SIGACTION_HANDLER_PATTERN = re.compile(
        r'\.sa_handler\s*=\s*(?P<handler>\w+)|'
        r'\.sa_sigaction\s*=\s*(?P<sa_handler>\w+)',
        re.MULTILINE
    )

    # IPC patterns
    IPC_PATTERN = re.compile(
        r'\b(pipe|pipe2|mkfifo|mmap|munmap|shm_open|shm_unlink|'
        r'shmget|shmat|shmdt|shmctl|'
        r'semget|semop|semctl|'
        r'sem_open|sem_close|sem_unlink|sem_wait|sem_timedwait|sem_trywait|sem_post|sem_init|sem_destroy|'
        r'msgget|msgsnd|msgrcv|msgctl|'
        r'socketpair)\s*\(',
        re.MULTILINE
    )

    # Threading patterns
    THREAD_PATTERN = re.compile(
        r'\b(pthread_create|pthread_join|pthread_mutex_init|pthread_mutex_lock|'
        r'pthread_mutex_unlock|pthread_rwlock_init|pthread_cond_init|'
        r'pthread_cond_wait|pthread_cond_signal|'
        r'thrd_create|mtx_init|mtx_lock|mtx_unlock|'
        r'cnd_init|cnd_wait|cnd_signal|'
        r'_Atomic|atomic_load|atomic_store|atomic_fetch_add)\b',
        re.MULTILINE
    )

    # HTTP library patterns
    HTTP_PATTERN = re.compile(
        r'\b(curl_easy_init|curl_easy_perform|curl_easy_cleanup|'
        r'MHD_start_daemon|MHD_stop_daemon|'
        r'evhttp_new|evhttp_bind_socket|evhttp_set_cb|'
        r'mg_http_listen|mg_mgr_init)\s*\(',
        re.MULTILINE
    )

    # Common callback patterns
    CALLBACK_PATTERN = re.compile(
        r'\b(?P<api>\w+)\s*\([^)]*(?P<cb>\w+_cb|on_\w+|handler|callback)\s*[,)]',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the C API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all C API patterns from source code.

        Args:
            content: C source code content
            file_path: Path to source file

        Returns:
            Dict with 'socket_apis', 'signal_handlers', 'ipc', 'callbacks',
                  'threading', 'http_apis' keys
        """
        # Remove comments
        clean = re.sub(r'//[^\n]*', '', content)
        clean = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), clean, flags=re.DOTALL)

        socket_apis = self._extract_socket_apis(clean, file_path, content)
        signal_handlers = self._extract_signal_handlers(clean, file_path, content)
        ipc = self._extract_ipc(clean, file_path, content)
        callbacks = self._extract_callbacks(clean, file_path, content)
        threading = self._extract_threading(clean, file_path)
        http_apis = self._extract_http_apis(clean, file_path)

        return {
            'socket_apis': socket_apis,
            'signal_handlers': signal_handlers,
            'ipc': ipc,
            'callbacks': callbacks,
            'threading': threading,
            'http_apis': http_apis,
        }

    def _get_line_number(self, content: str, pos: int) -> int:
        return content[:pos].count('\n') + 1

    def _extract_socket_apis(self, clean: str, file_path: str, original: str) -> List[CSocketAPIInfo]:
        """Extract socket API usage."""
        apis = []
        for match in self.SOCKET_PATTERN.finditer(clean):
            func = match.group(1)
            line_num = self._get_line_number(original, match.start())

            # Try to detect address family near this call
            context = clean[max(0, match.start()-200):match.end()+200]
            family = ''
            af_match = self.AF_PATTERN.search(context)
            if af_match:
                family = af_match.group(1)

            sock_type = ''
            st_match = self.SOCK_TYPE_PATTERN.search(context)
            if st_match:
                sock_type = st_match.group(1)

            apis.append(CSocketAPIInfo(
                function=func,
                family=family,
                socket_type=sock_type,
                file=file_path,
                line_number=line_num,
            ))
        return apis

    def _extract_signal_handlers(self, clean: str, file_path: str, original: str) -> List[CSignalHandlerInfo]:
        """Extract signal handler registrations."""
        handlers = []

        # Direct signal() calls: signal(SIGINT, handler)
        for match in self.SIGNAL_PATTERN.finditer(clean):
            sig = match.group('sig')
            handler = match.group('handler')
            line_num = self._get_line_number(original, match.start())
            handlers.append(CSignalHandlerInfo(
                signal_name=sig,
                handler_name=handler,
                is_sigaction=False,
                file=file_path,
                line_number=line_num,
            ))

        # sigaction() calls: extract signal from sigaction(SIG..., ...)
        # and handler from .sa_handler = ... or .sa_sigaction = ...
        sigaction_signals = []
        for match in self.SIGACTION_CALL_PATTERN.finditer(clean):
            sig = match.group('sig')
            line_num = self._get_line_number(original, match.start())
            sigaction_signals.append((sig, line_num))

        # Extract handler names from .sa_handler / .sa_sigaction assignments
        sigaction_handler_name = None
        for match in self.SIGACTION_HANDLER_PATTERN.finditer(clean):
            h = match.group('handler') or match.group('sa_handler')
            if h and h != 'SIG_DFL' and h != 'SIG_IGN':
                sigaction_handler_name = h

        # Pair sigaction calls with handler name
        for sig, line_num in sigaction_signals:
            handler_name = sigaction_handler_name or 'unknown'
            handlers.append(CSignalHandlerInfo(
                signal_name=sig,
                handler_name=handler_name,
                is_sigaction=True,
                file=file_path,
                line_number=line_num,
            ))

        return handlers

    def _extract_ipc(self, clean: str, file_path: str, original: str) -> List[CIPCInfo]:
        """Extract IPC mechanism usage."""
        ipcs = []
        for match in self.IPC_PATTERN.finditer(clean):
            mechanism = match.group(1)
            line_num = self._get_line_number(original, match.start())
            ipcs.append(CIPCInfo(
                mechanism=mechanism,
                file=file_path,
                line_number=line_num,
            ))
        return ipcs

    def _extract_callbacks(self, clean: str, file_path: str, original: str) -> List[CCallbackInfo]:
        """Extract callback registrations."""
        callbacks = []
        seen = set()
        for match in self.CALLBACK_PATTERN.finditer(clean):
            api = match.group('api')
            cb = match.group('cb')
            key = f"{api}_{cb}"
            if key in seen:
                continue
            seen.add(key)
            line_num = self._get_line_number(original, match.start())
            callbacks.append(CCallbackInfo(
                function=api,
                callback_name=cb,
                file=file_path,
                line_number=line_num,
            ))
        return callbacks

    def _extract_threading(self, clean: str, file_path: str) -> List[str]:
        """Extract threading pattern usage (returns list of function names)."""
        found = set()
        for match in self.THREAD_PATTERN.finditer(clean):
            found.add(match.group(1))
        return sorted(found)

    def _extract_http_apis(self, clean: str, file_path: str) -> List[str]:
        """Extract HTTP library usage (returns list of function names)."""
        found = set()
        for match in self.HTTP_PATTERN.finditer(clean):
            found.add(match.group(1))
        return sorted(found)
