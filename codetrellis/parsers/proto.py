"""
Proto Parser - Extracts structure from .proto files
=====================================================
"""

import re
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class ParsedService:
    """Parsed gRPC service"""
    name: str
    port: str = None
    methods: List[Dict] = field(default_factory=list)


@dataclass
class ParsedMessage:
    """Parsed protobuf message"""
    name: str
    fields: List[Dict] = field(default_factory=list)


@dataclass
class ParsedEnum:
    """Parsed protobuf enum"""
    name: str
    values: List[str] = field(default_factory=list)


class ProtoParser:
    """
    Parser for Protocol Buffer (.proto) files
    """

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse a proto file"""
        content = file_path.read_text()

        result = {
            "path": str(file_path),
            "type": "proto",
            "package": self._parse_package(content),
            "imports": self._parse_imports(content),
            "services": self._parse_services(content),
            "messages": self._parse_messages(content),
            "enums": self._parse_enums(content),
            "metadata": self._parse_metadata(content),
        }

        return result

    def _parse_package(self, content: str) -> str:
        """Parse package declaration"""
        match = re.search(r"package\s+([\w.]+);", content)
        return match.group(1) if match else ""

    def _parse_imports(self, content: str) -> List[str]:
        """Parse import statements"""
        imports = []
        pattern = r'import\s+"([^"]+)";'

        for match in re.finditer(pattern, content):
            imports.append(match.group(1))

        return imports

    def _parse_metadata(self, content: str) -> Dict[str, str]:
        """Parse metadata from comments (port, version, etc.)"""
        metadata = {}

        # Port
        port_match = re.search(r"Port:\s*(\d+)", content)
        if port_match:
            metadata["port"] = port_match.group(1)

        # Version
        version_match = re.search(r"Version:\s*([\d.]+)", content)
        if version_match:
            metadata["version"] = version_match.group(1)

        # Service name
        service_match = re.search(r"Service:\s*(\w+)", content)
        if service_match:
            metadata["service_name"] = service_match.group(1)

        return metadata

    def _parse_services(self, content: str) -> List[ParsedService]:
        """Parse gRPC service definitions"""
        services = []

        # Pattern for service definition
        service_pattern = r"service\s+(\w+)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}"

        for match in re.finditer(service_pattern, content, re.DOTALL):
            service_name = match.group(1)
            service_body = match.group(2)

            service = ParsedService(name=service_name)

            # Try to find port from comments above the service
            preceding_content = content[:match.start()]
            port_match = re.search(r"Port:\s*(\d+)", preceding_content[-500:] if len(preceding_content) > 500 else preceding_content)
            if port_match:
                service.port = port_match.group(1)

            # Parse RPC methods
            rpc_pattern = r"rpc\s+(\w+)\s*\(\s*(\w+)\s*\)\s*returns\s*\(\s*(stream\s+)?(\w+)\s*\)"

            for rpc_match in re.finditer(rpc_pattern, service_body):
                method_name = rpc_match.group(1)
                request_type = rpc_match.group(2)
                is_streaming = rpc_match.group(3) is not None
                response_type = rpc_match.group(4)

                service.methods.append({
                    "name": method_name,
                    "request": request_type,
                    "response": response_type,
                    "streaming": is_streaming
                })

            services.append(service)

        return services

    def _parse_messages(self, content: str) -> List[ParsedMessage]:
        """Parse message definitions"""
        messages = []

        # Pattern for message definition
        message_pattern = r"message\s+(\w+)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}"

        for match in re.finditer(message_pattern, content, re.DOTALL):
            message_name = match.group(1)
            message_body = match.group(2)

            message = ParsedMessage(name=message_name)

            # Parse fields
            field_pattern = r"(?:(repeated|optional)\s+)?(\w+)\s+(\w+)\s*=\s*(\d+)"

            for field_match in re.finditer(field_pattern, message_body):
                modifier = field_match.group(1)
                field_type = field_match.group(2)
                field_name = field_match.group(3)
                field_number = field_match.group(4)

                message.fields.append({
                    "name": field_name,
                    "type": field_type,
                    "number": int(field_number),
                    "repeated": modifier == "repeated",
                    "optional": modifier == "optional"
                })

            # Parse map fields
            map_pattern = r"map<(\w+),\s*(\w+)>\s+(\w+)\s*=\s*(\d+)"

            for map_match in re.finditer(map_pattern, message_body):
                key_type = map_match.group(1)
                value_type = map_match.group(2)
                field_name = map_match.group(3)
                field_number = map_match.group(4)

                message.fields.append({
                    "name": field_name,
                    "type": f"map<{key_type},{value_type}>",
                    "number": int(field_number),
                    "is_map": True
                })

            messages.append(message)

        return messages

    def _parse_enums(self, content: str) -> List[ParsedEnum]:
        """Parse enum definitions"""
        enums = []

        enum_pattern = r"enum\s+(\w+)\s*\{([^}]+)\}"

        for match in re.finditer(enum_pattern, content):
            enum_name = match.group(1)
            enum_body = match.group(2)

            parsed_enum = ParsedEnum(name=enum_name)

            # Parse enum values
            value_pattern = r"(\w+)\s*=\s*(\d+)"

            for value_match in re.finditer(value_pattern, enum_body):
                parsed_enum.values.append(value_match.group(1))

            enums.append(parsed_enum)

        return enums


# Convenience function
def parse_proto(file_path: str) -> Dict:
    """Parse a proto file"""
    parser = ProtoParser()
    return parser.parse(Path(file_path))
