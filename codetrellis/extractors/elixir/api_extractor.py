"""
Elixir API Extractor for CodeTrellis

Extracts API/web-related constructs from Elixir source code:
- Plug pipelines (plug :authenticate, plug MyPlug)
- Plug.Router routes (get/post/put/delete/match/forward)
- Endpoint configuration (socket, plug pipeline)
- HTTP client calls (HTTPoison, Tesla, Finch, Req, Mint)

Part of CodeTrellis - Elixir Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ElixirPlugInfo:
    """Information about a Plug usage."""
    name: str
    file: str = ""
    line_number: int = 0
    plug_type: str = "function"  # function, module, inline
    options: str = ""
    pipeline: str = ""


@dataclass
class ElixirPipelineInfo:
    """Information about a Plug pipeline."""
    name: str
    file: str = ""
    line_number: int = 0
    plugs: List[str] = field(default_factory=list)


@dataclass
class ElixirEndpointInfo:
    """Information about an Endpoint configuration."""
    name: str
    file: str = ""
    line_number: int = 0
    endpoint_type: str = "http"  # http, socket, plug
    config: str = ""


class ElixirAPIExtractor:
    """Extracts API/web constructs from Elixir source code."""

    # Plug patterns
    _PLUG_RE = re.compile(
        r'^\s*plug\s+:?(\w[\w.]*)\s*(,\s*(.+))?$',
        re.MULTILINE
    )

    # Pipeline patterns (Phoenix router)
    _PIPELINE_RE = re.compile(
        r'^\s*pipeline\s+:(\w+)\s+do\b',
        re.MULTILINE
    )

    # Plug.Router route patterns
    _PLUG_ROUTE_RE = re.compile(
        r'^\s*(get|post|put|patch|delete|options|head|match|forward)\s+"([^"]+)"',
        re.MULTILINE
    )

    # Endpoint socket configuration
    _SOCKET_RE = re.compile(
        r'^\s*socket\s+"([^"]+)"\s*,\s*([\w.]+)',
        re.MULTILINE
    )

    # HTTP client patterns
    _HTTP_CLIENT_RE = re.compile(
        r'(?:HTTPoison|Tesla|Finch|Req|Mint)\.(get|post|put|patch|delete|request|head|options)[\s!]*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all API/web constructs."""
        plugs = self._extract_plugs(content, file_path)
        pipelines = self._extract_pipelines(content, file_path)
        endpoints = self._extract_endpoints(content, file_path)

        return {
            "plugs": plugs,
            "pipelines": pipelines,
            "endpoints": endpoints,
        }

    def _extract_plugs(self, content: str, file_path: str) -> List[ElixirPlugInfo]:
        plugs = []
        for m in self._PLUG_RE.finditer(content):
            name = m.group(1)
            options = (m.group(3) or "").strip()
            line = content[:m.start()].count('\n') + 1

            # Determine plug type
            plug_type = "function" if name[0].islower() or name.startswith(':') else "module"

            plugs.append(ElixirPlugInfo(
                name=name,
                file=file_path,
                line_number=line,
                plug_type=plug_type,
                options=options[:100],
            ))
        return plugs

    def _extract_pipelines(self, content: str, file_path: str) -> List[ElixirPipelineInfo]:
        pipelines = []
        for m in self._PIPELINE_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Find plugs within this pipeline block
            # Simple approach: find plugs between this 'do' and next 'end'
            start = m.end()
            depth = 1
            pos = start
            block_content = ""
            while pos < len(content) and depth > 0:
                if content[pos:pos+3] == 'end' and (pos + 3 >= len(content) or not content[pos+3].isalnum()):
                    depth -= 1
                    if depth == 0:
                        block_content = content[start:pos]
                        break
                elif content[pos:pos+2] == 'do' and (pos == 0 or not content[pos-1].isalnum()):
                    depth += 1
                pos += 1

            pipeline_plugs = re.findall(r'plug\s+:?(\w[\w.]*)', block_content)

            pipelines.append(ElixirPipelineInfo(
                name=name,
                file=file_path,
                line_number=line,
                plugs=pipeline_plugs[:20],
            ))
        return pipelines

    def _extract_endpoints(self, content: str, file_path: str) -> List[ElixirEndpointInfo]:
        endpoints = []

        # Socket endpoints
        for m in self._SOCKET_RE.finditer(content):
            path = m.group(1)
            handler = m.group(2)
            line = content[:m.start()].count('\n') + 1
            endpoints.append(ElixirEndpointInfo(
                name=handler,
                file=file_path,
                line_number=line,
                endpoint_type="socket",
                config=path,
            ))

        return endpoints
