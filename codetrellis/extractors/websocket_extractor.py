"""
WebSocket Event Extractor for Angular/TypeScript

Extracts WebSocket event definitions from Angular services and components.
Supports:
- Socket.IO patterns (socket.on, socket.emit)
- Native WebSocket patterns
- Event payload types
- Connection handlers (connect, disconnect, error)

Part of CodeTrellis v2.0 - Phase 3 Implementation
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class WebSocketEventInfo:
    """Information about a single WebSocket event"""
    event_name: str
    event_type: str  # 'on' (incoming) or 'emit' (outgoing)
    payload_type: Optional[str] = None
    handler_name: Optional[str] = None
    description: Optional[str] = None
    line_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'eventName': self.event_name,
            'type': self.event_type,
        }
        if self.payload_type:
            result['payloadType'] = self.payload_type
        if self.handler_name:
            result['handler'] = self.handler_name
        if self.description:
            result['description'] = self.description
        return result

    def to_codetrellis_format(self) -> str:
        """Convert to CodeTrellis output format"""
        direction = '←' if self.event_type == 'on' else '→'
        parts = [f"{direction} '{self.event_name}'"]

        if self.payload_type:
            # Truncate long payload types
            payload = self.payload_type
            if len(payload) > 50:
                payload = payload[:47] + '...'
            parts.append(f"payload: {payload}")

        if self.handler_name:
            parts.append(f"handler: {self.handler_name}")

        return ' | '.join(parts)


@dataclass
class WebSocketConnectionInfo:
    """Information about a WebSocket connection"""
    socket_name: str
    url: Optional[str] = None
    url_variable: Optional[str] = None
    events: List[WebSocketEventInfo] = field(default_factory=list)
    connection_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'socketName': self.socket_name,
            'events': [e.to_dict() for e in self.events],
        }
        if self.url:
            result['url'] = self.url
        if self.url_variable:
            result['urlVariable'] = self.url_variable
        if self.connection_config:
            result['config'] = self.connection_config
        return result


@dataclass
class WebSocketFileInfo:
    """Information about WebSocket usage in a file"""
    file_path: str
    connections: List[WebSocketConnectionInfo] = field(default_factory=list)
    total_events: int = 0
    incoming_events: int = 0  # .on() events
    outgoing_events: int = 0  # .emit() events

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'filePath': self.file_path,
            'connections': [c.to_dict() for c in self.connections],
            'stats': {
                'totalEvents': self.total_events,
                'incomingEvents': self.incoming_events,
                'outgoingEvents': self.outgoing_events,
            }
        }


class WebSocketExtractor:
    """
    Extracts WebSocket event definitions from TypeScript/Angular files.

    Supports Socket.IO and native WebSocket patterns.
    """

    # Pattern to detect Socket.IO import
    SOCKET_IO_IMPORT_PATTERN = re.compile(
        r"import\s*\{[^}]*Socket[^}]*\}\s*from\s*['\"]socket\.io-client['\"]",
        re.MULTILINE
    )

    # Pattern to detect native WebSocket
    WEBSOCKET_PATTERN = re.compile(
        r'new\s+WebSocket\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        re.MULTILINE
    )

    # Pattern to detect socket.io connection
    SOCKET_IO_CONNECTION_PATTERN = re.compile(
        r'(\w+)\s*=\s*io\s*\(\s*([^,)]+)',
        re.MULTILINE
    )

    # Pattern for socket.on events with typed payload
    SOCKET_ON_TYPED_PATTERN = re.compile(
        r'(\w+)\.on\s*\(\s*[\'"](\w+)[\'"]\s*,\s*\(([^)]*)\)\s*(?::\s*([^=]+))?\s*=>\s*\{',
        re.MULTILINE
    )

    # Pattern for socket.on events with inline arrow function
    SOCKET_ON_INLINE_PATTERN = re.compile(
        r'(\w+)\.on\s*[<]?([^>]*)[>]?\s*\(\s*[\'"](\w+)[\'"]\s*,\s*(?:\([^)]*\)\s*=>\s*|function)',
        re.MULTILINE
    )

    # Pattern for socket.on with typed data parameter
    SOCKET_ON_DATA_PATTERN = re.compile(
        r'(\w+)\.on\s*\(\s*[\'"](\w+)[\'"]\s*,\s*\(\s*(\w+)\s*:\s*([^)]+)\)',
        re.MULTILINE
    )

    # Pattern for socket.emit events
    SOCKET_EMIT_PATTERN = re.compile(
        r'(\w+)\.emit\s*\(\s*[\'"](\w+)[\'"]\s*(?:,\s*([^)]+))?\)',
        re.MULTILINE
    )

    # Pattern to detect private socket declarations
    SOCKET_DECLARATION_PATTERN = re.compile(
        r'private\s+(?:readonly\s+)?(\w+)\s*:\s*Socket',
        re.MULTILINE
    )

    # Common connection events
    CONNECTION_EVENTS = {'connect', 'disconnect', 'connect_error', 'reconnect', 'reconnect_error'}

    def __init__(self):
        self.files_info: List[WebSocketFileInfo] = []

    def can_extract(self, file_path: str, content: str) -> bool:
        """Check if this file contains WebSocket patterns"""
        # Check for Socket.IO import
        if self.SOCKET_IO_IMPORT_PATTERN.search(content):
            return True

        # Check for native WebSocket
        if 'new WebSocket' in content:
            return True

        # Check for socket.on or socket.emit patterns
        if '.on(' in content and ('socket' in content.lower() or 'Socket' in content):
            return True

        return False

    def extract(self, file_path: str, content: str) -> Optional[WebSocketFileInfo]:
        """Extract WebSocket events from a file"""
        if not self.can_extract(file_path, content):
            return None

        file_info = WebSocketFileInfo(file_path=file_path)

        # Find socket declarations
        socket_names = self._find_socket_declarations(content)

        # Find io() connections
        connections = self._find_io_connections(content)

        # Extract events for each socket
        all_events = []

        # Process declared sockets
        for socket_name in socket_names:
            conn_info = WebSocketConnectionInfo(socket_name=socket_name)
            events = self._extract_socket_events(content, socket_name)
            conn_info.events = events
            all_events.extend(events)

            if events:
                file_info.connections.append(conn_info)

        # Process io() connections
        for var_name, url in connections:
            # Check if already processed
            existing = next((c for c in file_info.connections if c.socket_name == var_name), None)
            if existing:
                existing.url = url if url.startswith(('http', 'ws', '/')) else None
                existing.url_variable = url if not url.startswith(('http', 'ws', '/')) else None
            else:
                conn_info = WebSocketConnectionInfo(
                    socket_name=var_name,
                    url=url if url.startswith(('http', 'ws', '/')) else None,
                    url_variable=url if not url.startswith(('http', 'ws', '/')) else None
                )
                events = self._extract_socket_events(content, var_name)
                conn_info.events = events
                all_events.extend(events)

                if events:
                    file_info.connections.append(conn_info)

        # Calculate stats
        file_info.total_events = len(all_events)
        file_info.incoming_events = sum(1 for e in all_events if e.event_type == 'on')
        file_info.outgoing_events = sum(1 for e in all_events if e.event_type == 'emit')

        if file_info.total_events > 0:
            self.files_info.append(file_info)
            return file_info

        return None

    def _find_socket_declarations(self, content: str) -> List[str]:
        """Find socket variable declarations"""
        names = []

        # Pattern: private signalSocket: Socket
        matches = self.SOCKET_DECLARATION_PATTERN.findall(content)
        names.extend(matches)

        # Also look for: this.socket, this.signalSocket, etc.
        this_pattern = re.findall(r'this\.(\w*[sS]ocket\w*)', content)
        for name in this_pattern:
            if name not in names:
                names.append(name)

        return names

    def _find_io_connections(self, content: str) -> List[tuple]:
        """Find io() connection calls"""
        connections = []

        # Pattern: socket = io(url)
        matches = self.SOCKET_IO_CONNECTION_PATTERN.findall(content)
        for var_name, url in matches:
            url = url.strip().strip('"\'')
            connections.append((var_name, url))

        # Pattern: this.socket = io(...)
        this_pattern = re.findall(
            r'this\.(\w+)\s*=\s*io\s*\(\s*([^,)]+)',
            content
        )
        for var_name, url in this_pattern:
            url = url.strip().strip('"\'')
            connections.append((var_name, url))

        return connections

    def _extract_socket_events(self, content: str, socket_name: str) -> List[WebSocketEventInfo]:
        """Extract all events for a specific socket"""
        events = []
        seen_events = set()

        # Escape socket_name for regex
        escaped_name = re.escape(socket_name)

        # Pattern for .on() with typed data
        on_pattern = re.compile(
            rf'(?:this\.)?{escaped_name}\.on\s*\(\s*[\'"](\w+)[\'"]\s*,\s*\(\s*(\w+)?\s*(?::\s*([^)]+))?\)',
            re.MULTILINE
        )

        for match in on_pattern.finditer(content):
            event_name = match.group(1)
            param_name = match.group(2)
            payload_type = match.group(3)

            if event_name not in seen_events:
                seen_events.add(event_name)
                events.append(WebSocketEventInfo(
                    event_name=event_name,
                    event_type='on',
                    payload_type=payload_type.strip() if payload_type else None,
                    line_number=content[:match.start()].count('\n') + 1
                ))

        # Pattern for .on() with generic type <T>
        on_generic_pattern = re.compile(
            rf'(?:this\.)?{escaped_name}\.on\s*<([^>]+)>\s*\(\s*[\'"](\w+)[\'"]',
            re.MULTILINE
        )

        for match in on_generic_pattern.finditer(content):
            payload_type = match.group(1)
            event_name = match.group(2)

            if event_name not in seen_events:
                seen_events.add(event_name)
                events.append(WebSocketEventInfo(
                    event_name=event_name,
                    event_type='on',
                    payload_type=payload_type.strip() if payload_type else None,
                    line_number=content[:match.start()].count('\n') + 1
                ))

        # Simple .on() pattern
        simple_on_pattern = re.compile(
            rf'(?:this\.)?{escaped_name}\.on\s*\(\s*[\'"](\w+)[\'"]',
            re.MULTILINE
        )

        for match in simple_on_pattern.finditer(content):
            event_name = match.group(1)

            if event_name not in seen_events:
                seen_events.add(event_name)
                events.append(WebSocketEventInfo(
                    event_name=event_name,
                    event_type='on',
                    payload_type=None,
                    line_number=content[:match.start()].count('\n') + 1
                ))

        # Pattern for .emit()
        emit_pattern = re.compile(
            rf'(?:this\.)?{escaped_name}\.emit\s*\(\s*[\'"](\w+)[\'"]\s*(?:,\s*([^)]+))?\)',
            re.MULTILINE
        )

        for match in emit_pattern.finditer(content):
            event_name = match.group(1)
            payload = match.group(2)

            event_key = f"emit_{event_name}"
            if event_key not in seen_events:
                seen_events.add(event_key)
                events.append(WebSocketEventInfo(
                    event_name=event_name,
                    event_type='emit',
                    payload_type=self._infer_payload_type(payload) if payload else None,
                    line_number=content[:match.start()].count('\n') + 1
                ))

        return events

    def _infer_payload_type(self, payload: str) -> Optional[str]:
        """Try to infer the type of emitted payload"""
        if not payload:
            return None

        payload = payload.strip()

        # Object literal
        if payload.startswith('{'):
            return 'object'

        # Array literal
        if payload.startswith('['):
            return 'array'

        # String literal
        if payload.startswith(('"', "'", '`')):
            return 'string'

        # Number literal
        if payload.isdigit() or (payload[0] == '-' and payload[1:].isdigit()):
            return 'number'

        # Boolean
        if payload in ('true', 'false'):
            return 'boolean'

        # Variable reference
        return payload.split(',')[0].strip()  # Return first argument variable name

    def get_all_events(self) -> List[WebSocketFileInfo]:
        """Get all extracted WebSocket info"""
        return self.files_info

    def get_event_summary(self) -> Dict[str, int]:
        """Get summary of all events across files"""
        incoming = {}
        outgoing = {}

        for file_info in self.files_info:
            for conn in file_info.connections:
                for event in conn.events:
                    if event.event_type == 'on':
                        incoming[event.event_name] = incoming.get(event.event_name, 0) + 1
                    else:
                        outgoing[event.event_name] = outgoing.get(event.event_name, 0) + 1

        return {
            'incoming': incoming,
            'outgoing': outgoing,
            'total_incoming': sum(incoming.values()),
            'total_outgoing': sum(outgoing.values()),
        }

    def clear(self):
        """Clear all extracted events"""
        self.files_info = []
