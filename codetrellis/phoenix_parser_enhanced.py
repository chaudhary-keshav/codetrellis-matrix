"""
Enhanced Phoenix Parser for CodeTrellis

Self-contained framework parser for the Phoenix web framework (Elixir).
Detects and extracts:
- Router routes (get/post/put/patch/delete/live/resources/pipe_through)
- Controllers (actions, plugs, renders)
- LiveView modules (mount, handle_event, handle_info, render, assigns)
- LiveComponent modules
- Channels (join, handle_in, handle_out, broadcast)
- Sockets
- Components (function components, HEEx, slots)
- Verified routes (~p sigil)
- Endpoint configuration

Phoenix versions: 1.0–1.7+ (detects based on features)

Reference pattern: Rails parser (self-contained framework file)

Part of CodeTrellis - Phoenix Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class PhoenixRouteInfo:
    """Information about a Phoenix route."""
    method: str  # get, post, put, patch, delete, live, resources, forward, pipe_through
    path: str = ""
    controller: str = ""
    action: str = ""
    live_module: str = ""
    pipe_through: List[str] = field(default_factory=list)
    scope: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class PhoenixControllerInfo:
    """Information about a Phoenix controller."""
    name: str
    actions: List[str] = field(default_factory=list)
    plugs: List[str] = field(default_factory=list)
    renders: List[str] = field(default_factory=list)
    is_api: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class PhoenixLiveViewInfo:
    """Information about a Phoenix LiveView module."""
    name: str
    mount: bool = False
    handle_events: List[str] = field(default_factory=list)
    handle_infos: List[str] = field(default_factory=list)
    handle_params: bool = False
    assigns: List[str] = field(default_factory=list)
    has_render: bool = False
    live_components: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class PhoenixLiveComponentInfo:
    """Information about a Phoenix LiveComponent."""
    name: str
    has_update: bool = False
    has_render: bool = False
    has_mount: bool = False
    has_handle_event: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class PhoenixChannelInfo:
    """Information about a Phoenix Channel."""
    name: str
    topic: str = ""
    join: bool = False
    handle_in_events: List[str] = field(default_factory=list)
    handle_out_events: List[str] = field(default_factory=list)
    broadcasts: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class PhoenixComponentInfo:
    """Information about a Phoenix function component."""
    name: str
    attrs: List[str] = field(default_factory=list)
    slots: List[str] = field(default_factory=list)
    is_heex: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class PhoenixSocketInfo:
    """Information about a Phoenix Socket."""
    name: str
    channels: List[str] = field(default_factory=list)
    live_transports: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class PhoenixParseResult:
    """Complete parse result for a Phoenix file."""
    file_path: str
    file_type: str = "elixir"

    # Routes
    routes: List[PhoenixRouteInfo] = field(default_factory=list)

    # Controllers
    controllers: List[PhoenixControllerInfo] = field(default_factory=list)

    # LiveView
    live_views: List[PhoenixLiveViewInfo] = field(default_factory=list)
    live_components: List[PhoenixLiveComponentInfo] = field(default_factory=list)

    # Channels / Sockets
    channels: List[PhoenixChannelInfo] = field(default_factory=list)
    sockets: List[PhoenixSocketInfo] = field(default_factory=list)

    # Components
    components: List[PhoenixComponentInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    phoenix_version: str = ""
    has_live_view: bool = False
    has_verified_routes: bool = False
    has_heex: bool = False
    total_routes: int = 0
    total_controllers: int = 0
    total_live_views: int = 0


# ── Parser ───────────────────────────────────────────────────────────────────

class EnhancedPhoenixParser:
    """
    Enhanced Phoenix framework parser for CodeTrellis.

    Self-contained parser that extracts Phoenix-specific patterns from Elixir files.
    Only populates results if Phoenix framework is detected in the file content.
    """

    # Phoenix framework detection
    PHOENIX_REQUIRE = re.compile(
        r'use\s+(?:Phoenix\.\w+|'
        r'\w+Web(?:,|\s)|'
        r'\w+Web\.\w+)|'
        r'Phoenix\.Router|Phoenix\.Controller|'
        r'Phoenix\.LiveView|Phoenix\.Channel',
        re.MULTILINE,
    )

    # ── Route patterns ────────────────────────────────────────────────────

    ROUTE_HTTP = re.compile(
        r'^\s*(get|post|put|patch|delete|options|head)\s+"([^"]+)"\s*,\s*([\w.]+)\s*,\s*:(\w+)',
        re.MULTILINE,
    )

    ROUTE_LIVE = re.compile(
        r'^\s*live\s+"([^"]+)"\s*,\s*([\w.]+)(?:\s*,\s*:(\w+))?',
        re.MULTILINE,
    )

    ROUTE_RESOURCES = re.compile(
        r'^\s*resources\s+"([^"]+)"\s*,\s*([\w.]+)',
        re.MULTILINE,
    )

    ROUTE_FORWARD = re.compile(
        r'^\s*forward\s+"([^"]+)"\s*,\s*([\w.]+)',
        re.MULTILINE,
    )

    ROUTE_PIPE_THROUGH = re.compile(
        r'^\s*pipe_through\s+(?::(\w+)|\[([^\]]+)\])',
        re.MULTILINE,
    )

    ROUTE_SCOPE = re.compile(
        r'^\s*scope\s+"([^"]+)"(?:\s*,\s*([\w.]+))?\s+do',
        re.MULTILINE,
    )

    # ── Controller patterns ───────────────────────────────────────────────

    CONTROLLER_RE = re.compile(
        r'defmodule\s+([\w.]+Controller)\s+do',
        re.MULTILINE,
    )

    CONTROLLER_ACTION_RE = re.compile(
        r'^\s*def\s+(index|show|new|create|edit|update|delete|action_fallback)\s*\(',
        re.MULTILINE,
    )

    CONTROLLER_RENDER_RE = re.compile(
        r'render\(conn\s*,\s*"([^"]+)"',
        re.MULTILINE,
    )

    CONTROLLER_PLUG_RE = re.compile(
        r'^\s*plug\s+:?(\w[\w.]*)',
        re.MULTILINE,
    )

    # ── LiveView patterns ─────────────────────────────────────────────────

    LIVEVIEW_RE = re.compile(
        r'use\s+(?:Phoenix\.LiveView|\w+Web\s*,\s*:live_view)',
        re.MULTILINE,
    )

    LIVEVIEW_MODULE_RE = re.compile(
        r'defmodule\s+([\w.]+Live(?:\.\w+)?)\s+do',
        re.MULTILINE,
    )

    HANDLE_EVENT_RE = re.compile(
        r'def\s+handle_event\(\s*"([^"]+)"',
        re.MULTILINE,
    )

    HANDLE_INFO_RE = re.compile(
        r'def\s+handle_info\(\s*(?:\{:(\w+)|:(\w+))',
        re.MULTILINE,
    )

    HANDLE_PARAMS_RE = re.compile(
        r'def\s+handle_params\(',
        re.MULTILINE,
    )

    ASSIGN_RE = re.compile(
        r'(?:assign|assign_new)\(\s*(?:socket\s*,\s*)?:(\w+)',
        re.MULTILINE,
    )

    # ── LiveComponent patterns ────────────────────────────────────────────

    LIVE_COMPONENT_RE = re.compile(
        r'use\s+(?:Phoenix\.LiveComponent|\w+Web\s*,\s*:live_component)',
        re.MULTILINE,
    )

    LIVE_COMPONENT_MODULE_RE = re.compile(
        r'defmodule\s+([\w.]+)\s+do',
        re.MULTILINE,
    )

    # ── Channel patterns ──────────────────────────────────────────────────

    CHANNEL_RE = re.compile(
        r'use\s+(?:Phoenix\.Channel|\w+Web\s*,\s*:channel)',
        re.MULTILINE,
    )

    CHANNEL_MODULE_RE = re.compile(
        r'defmodule\s+([\w.]+Channel)\s+do',
        re.MULTILINE,
    )

    CHANNEL_JOIN_RE = re.compile(
        r'def\s+join\(\s*"([^"]+)"',
        re.MULTILINE,
    )

    HANDLE_IN_RE = re.compile(
        r'def\s+handle_in\(\s*"([^"]+)"',
        re.MULTILINE,
    )

    HANDLE_OUT_RE = re.compile(
        r'def\s+handle_out\(\s*"([^"]+)"',
        re.MULTILINE,
    )

    BROADCAST_RE = re.compile(
        r'broadcast(?:!|_from)?\(\s*(?:\w+\s*,\s*)?"([^"]+)"',
        re.MULTILINE,
    )

    # ── Socket patterns ───────────────────────────────────────────────────

    SOCKET_MODULE_RE = re.compile(
        r'defmodule\s+([\w.]+Socket)\s+do',
        re.MULTILINE,
    )

    SOCKET_CHANNEL_RE = re.compile(
        r'channel\s+"([^"]+)"\s*,\s*([\w.]+)',
        re.MULTILINE,
    )

    # ── Component patterns (Phoenix 1.7+) ────────────────────────────────

    FUNC_COMPONENT_RE = re.compile(
        r'^\s*(?:def|defp)\s+(\w+)\(assigns\)',
        re.MULTILINE,
    )

    ATTR_RE = re.compile(
        r'^\s*attr\s+:(\w+)\s*,\s*:?(\w+)',
        re.MULTILINE,
    )

    SLOT_RE = re.compile(
        r'^\s*slot\s+:(\w+)',
        re.MULTILINE,
    )

    VERIFIED_ROUTE_RE = re.compile(r'~p"', re.MULTILINE)

    # ── Version detection ─────────────────────────────────────────────────

    VERSION_FEATURES = [
        ('1.8', re.compile(r'Phoenix\.Swoosh|Bandit|DNS\.cluster|Phoenix\.Presence\.track\b', re.MULTILINE)),
        ('1.7', re.compile(r'attr\s+:\w+|slot\s+:\w+|~p"|verified_routes|CoreComponents', re.MULTILINE)),
        ('1.6', re.compile(r'Phoenix\.LiveView|live\s+"/|live_render', re.MULTILINE)),
        ('1.5', re.compile(r'Phoenix\.LiveDashboard|Phoenix\.PubSub', re.MULTILINE)),
        ('1.4', re.compile(r'Phoenix\.Presence|Phoenix\.Token', re.MULTILINE)),
        ('1.3', re.compile(r'Phoenix\.Controller|action_fallback|FallbackController', re.MULTILINE)),
        ('1.2', re.compile(r'Phoenix\.Channel|Phoenix\.Socket', re.MULTILINE)),
        ('1.0', re.compile(r'Phoenix\.Router|Phoenix\.Endpoint', re.MULTILINE)),
    ]

    def parse(self, content: str, file_path: str = "") -> PhoenixParseResult:
        """Parse Elixir source code for Phoenix-specific patterns."""
        result = PhoenixParseResult(file_path=file_path)

        # Check if this file uses Phoenix
        if not self.PHOENIX_REQUIRE.search(content):
            return result

        # Detect version
        result.phoenix_version = self._detect_version(content)

        # Feature flags
        result.has_live_view = bool(self.LIVEVIEW_RE.search(content))
        result.has_verified_routes = bool(self.VERIFIED_ROUTE_RE.search(content))
        result.has_heex = bool(re.search(r'~H"""', content))

        # Extract routes
        self._extract_routes(content, file_path, result)

        # Extract controllers
        self._extract_controllers(content, file_path, result)

        # Extract LiveViews
        self._extract_live_views(content, file_path, result)

        # Extract LiveComponents
        self._extract_live_components(content, file_path, result)

        # Extract channels
        self._extract_channels(content, file_path, result)

        # Extract sockets
        self._extract_sockets(content, file_path, result)

        # Extract function components
        self._extract_components(content, file_path, result)

        # Update totals
        result.total_routes = len(result.routes)
        result.total_controllers = len(result.controllers)
        result.total_live_views = len(result.live_views)

        return result

    def _detect_version(self, content: str) -> str:
        """Detect Phoenix version based on features used."""
        for version, pattern in self.VERSION_FEATURES:
            if pattern.search(content):
                return version
        return ""

    def _extract_routes(self, content: str, file_path: str, result: PhoenixParseResult):
        """Extract Phoenix route definitions."""
        # HTTP method routes
        for m in self.ROUTE_HTTP.finditer(content):
            result.routes.append(PhoenixRouteInfo(
                method=m.group(1).upper(),
                path=m.group(2),
                controller=m.group(3),
                action=m.group(4),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Live routes
        for m in self.ROUTE_LIVE.finditer(content):
            result.routes.append(PhoenixRouteInfo(
                method="live",
                path=m.group(1),
                live_module=m.group(2),
                action=m.group(3) or "",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Resource routes
        for m in self.ROUTE_RESOURCES.finditer(content):
            result.routes.append(PhoenixRouteInfo(
                method="resources",
                path=m.group(1),
                controller=m.group(2),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Forward routes
        for m in self.ROUTE_FORWARD.finditer(content):
            result.routes.append(PhoenixRouteInfo(
                method="forward",
                path=m.group(1),
                controller=m.group(2),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_controllers(self, content: str, file_path: str, result: PhoenixParseResult):
        """Extract Phoenix controller definitions."""
        for m in self.CONTROLLER_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Find all actions, plugs, renders in the module
            actions = [a.group(1) for a in self.CONTROLLER_ACTION_RE.finditer(content)]
            plugs = [p.group(1) for p in self.CONTROLLER_PLUG_RE.finditer(content)]
            renders = [r.group(1) for r in self.CONTROLLER_RENDER_RE.finditer(content)]

            is_api = 'ActionController::API' in content or ':api' in content or 'json(' in content

            result.controllers.append(PhoenixControllerInfo(
                name=name,
                actions=actions[:20],
                plugs=plugs[:20],
                renders=renders[:20],
                is_api=is_api,
                file=file_path,
                line_number=line,
            ))

    def _extract_live_views(self, content: str, file_path: str, result: PhoenixParseResult):
        """Extract Phoenix LiveView modules."""
        if not self.LIVEVIEW_RE.search(content):
            return

        for m in self.LIVEVIEW_MODULE_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            handle_events = [e.group(1) for e in self.HANDLE_EVENT_RE.finditer(content)]
            handle_infos = [(i.group(1) or i.group(2)) for i in self.HANDLE_INFO_RE.finditer(content)]
            assigns = list(set(a.group(1) for a in self.ASSIGN_RE.finditer(content)))
            has_mount = bool(re.search(r'def\s+mount\(', content))
            has_render = bool(re.search(r'def\s+render\(', content))
            has_handle_params = bool(self.HANDLE_PARAMS_RE.search(content))

            # Detect LiveComponent usage
            live_comps = re.findall(r'live_component\(\s*([\w.]+)', content)

            result.live_views.append(PhoenixLiveViewInfo(
                name=name,
                mount=has_mount,
                handle_events=handle_events[:20],
                handle_infos=handle_infos[:20],
                handle_params=has_handle_params,
                assigns=assigns[:30],
                has_render=has_render,
                live_components=live_comps[:20],
                file=file_path,
                line_number=line,
            ))

    def _extract_live_components(self, content: str, file_path: str, result: PhoenixParseResult):
        """Extract Phoenix LiveComponent modules."""
        if not self.LIVE_COMPONENT_RE.search(content):
            return

        for m in self.LIVE_COMPONENT_MODULE_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            result.live_components.append(PhoenixLiveComponentInfo(
                name=name,
                has_update=bool(re.search(r'def\s+update\(', content)),
                has_render=bool(re.search(r'def\s+render\(', content)),
                has_mount=bool(re.search(r'def\s+mount\(', content)),
                has_handle_event=bool(re.search(r'def\s+handle_event\(', content)),
                file=file_path,
                line_number=line,
            ))

    def _extract_channels(self, content: str, file_path: str, result: PhoenixParseResult):
        """Extract Phoenix Channel definitions."""
        if not self.CHANNEL_RE.search(content):
            return

        for m in self.CHANNEL_MODULE_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            topic = ""
            join_m = self.CHANNEL_JOIN_RE.search(content)
            if join_m:
                topic = join_m.group(1)

            handle_in_events = [e.group(1) for e in self.HANDLE_IN_RE.finditer(content)]
            handle_out_events = [e.group(1) for e in self.HANDLE_OUT_RE.finditer(content)]
            broadcasts = [b.group(1) for b in self.BROADCAST_RE.finditer(content)]

            result.channels.append(PhoenixChannelInfo(
                name=name,
                topic=topic,
                join=join_m is not None,
                handle_in_events=handle_in_events[:20],
                handle_out_events=handle_out_events[:20],
                broadcasts=broadcasts[:20],
                file=file_path,
                line_number=line,
            ))

    def _extract_sockets(self, content: str, file_path: str, result: PhoenixParseResult):
        """Extract Phoenix Socket definitions."""
        for m in self.SOCKET_MODULE_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            channels = [c.group(2) for c in self.SOCKET_CHANNEL_RE.finditer(content)]

            result.sockets.append(PhoenixSocketInfo(
                name=name,
                channels=channels[:20],
                file=file_path,
                line_number=line,
            ))

    def _extract_components(self, content: str, file_path: str, result: PhoenixParseResult):
        """Extract Phoenix function components (1.7+)."""
        # Only if file has attr/slot declarations
        attrs_in_file = [a.group(1) for a in self.ATTR_RE.finditer(content)]
        slots_in_file = [s.group(1) for s in self.SLOT_RE.finditer(content)]

        if not attrs_in_file and not slots_in_file:
            return

        for m in self.FUNC_COMPONENT_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Find attr/slot declarations preceding this function
            # (simplified: uses all attrs/slots in the file for each component)
            result.components.append(PhoenixComponentInfo(
                name=name,
                attrs=attrs_in_file[:20],
                slots=slots_in_file[:10],
                is_heex=bool(re.search(r'~H"""', content)),
                file=file_path,
                line_number=line,
            ))
