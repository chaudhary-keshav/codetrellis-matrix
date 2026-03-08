"""
Lua API Extractor for CodeTrellis

Extracts API/framework patterns from Lua source code:
- LÖVE2D callbacks (love.load, love.update, love.draw, etc.)
- OpenResty directives (content_by_lua, access_by_lua, ngx.*)
- Lapis routes (match, get, post, before_filter)
- Turbo.lua handlers (RequestHandler)
- Sailor routes
- Redis commands (via redis-lua, resty.redis)
- Nginx directives and phases
- Game loops and lifecycle callbacks
- Event handler patterns
- CLI command patterns (argparse, lua-cliargs)

Part of CodeTrellis v4.28 - Lua Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class LuaRouteInfo:
    """Information about an HTTP route/endpoint."""
    method: str  # GET, POST, PUT, DELETE, etc.
    path: str
    handler: str
    framework: str  # lapis, openresty, turbo, sailor, pegasus, lor
    middleware: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class LuaCallbackInfo:
    """Information about a framework callback (e.g., LÖVE2D, Corona)."""
    name: str
    framework: str  # love2d, corona, defold, gideros
    callback_type: str = ""  # lifecycle, input, graphics, audio, physics
    parameters: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class LuaEventHandlerInfo:
    """Information about an event handler."""
    event_name: str
    handler_name: str
    framework: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class LuaCommandInfo:
    """Information about a CLI command definition."""
    name: str
    description: str = ""
    framework: str = ""  # argparse, cliargs, lapp
    file: str = ""
    line_number: int = 0


class LuaAPIExtractor:
    """
    Extracts Lua API/framework patterns using regex-based parsing.

    Supports:
    - LÖVE2D: love.load, love.update, love.draw, love.keypressed, etc.
    - OpenResty/nginx-lua: ngx.req, ngx.say, ngx.exit, content_by_lua
    - Lapis: match(), get(), post(), before_filter
    - Turbo.lua: RequestHandler, route patterns
    - Sailor: routes table
    - Pegasus: server routes
    - lor: route definitions
    - Redis: redis:command patterns
    - Tarantool: box.space, fiber, net.box
    """

    # LÖVE2D callbacks
    LOVE_CALLBACKS = {
        'load': 'lifecycle', 'update': 'lifecycle', 'draw': 'graphics',
        'quit': 'lifecycle', 'run': 'lifecycle', 'errorhandler': 'lifecycle',
        'keypressed': 'input', 'keyreleased': 'input',
        'mousepressed': 'input', 'mousereleased': 'input', 'mousemoved': 'input',
        'wheelmoved': 'input', 'touchpressed': 'input', 'touchreleased': 'input',
        'touchmoved': 'input', 'joystickpressed': 'input',
        'textinput': 'input', 'textedited': 'input',
        'resize': 'graphics', 'focus': 'lifecycle', 'visible': 'lifecycle',
        'gamepadpressed': 'input', 'gamepadreleased': 'input', 'gamepadaxis': 'input',
        'filedropped': 'input', 'directorydropped': 'input',
        'lowmemory': 'lifecycle', 'threaderror': 'lifecycle',
        'displayrotated': 'graphics',
    }

    LOVE_CALLBACK_PATTERN = re.compile(
        r"^\s*function\s+love\.(?P<callback>\w+)\s*\((?P<params>[^)]*)\)",
        re.MULTILINE
    )
    LOVE_CALLBACK_ASSIGN_PATTERN = re.compile(
        r"^\s*love\.(?P<callback>\w+)\s*=\s*function\s*\((?P<params>[^)]*)\)",
        re.MULTILINE
    )

    # Lapis routes
    LAPIS_ROUTE_PATTERN = re.compile(
        r"^\s*\[\s*(?P<method>match|get|post|put|delete|patch|head|options)\s*\]\s*"
        r"['\"](?P<path>[^'\"]+)['\"]",
        re.MULTILINE
    )
    LAPIS_APP_ROUTE_PATTERN = re.compile(
        r"app\s*:\s*(?P<method>match|get|post|put|delete|patch)\s*\(\s*['\"](?P<path>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # OpenResty/ngx patterns
    NGX_PATTERN = re.compile(
        r"ngx\.(?P<module>\w+)(?:\.(?P<method>\w+))?\s*\(",
        re.MULTILINE
    )
    CONTENT_BY_LUA_PATTERN = re.compile(
        r"(?P<directive>content_by_lua|access_by_lua|rewrite_by_lua|"
        r"init_by_lua|init_worker_by_lua|log_by_lua|"
        r"header_filter_by_lua|body_filter_by_lua|"
        r"ssl_certificate_by_lua|ssl_session_fetch_by_lua|"
        r"balancer_by_lua|set_by_lua)(?:_block|_file)?\s+",
        re.MULTILINE
    )

    # lor framework routes
    LOR_ROUTE_PATTERN = re.compile(
        r"(?:app|router)\s*:\s*(?P<method>get|post|put|delete|patch|head|options|use)\s*\(\s*['\"](?P<path>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # Turbo.lua
    TURBO_HANDLER_PATTERN = re.compile(
        r"(?P<name>\w+)\s*=\s*class\s*\(\s*['\"](?P<classname>[^'\"]+)['\"]"
        r"\s*,\s*turbo\.web\.RequestHandler\s*\)",
        re.MULTILINE
    )

    # Redis command patterns
    REDIS_COMMAND_PATTERN = re.compile(
        r"(?:redis|red|resty\.redis)\s*:\s*(?P<command>\w+)\s*\(",
        re.MULTILINE
    )

    # Tarantool patterns
    TARANTOOL_SPACE_PATTERN = re.compile(
        r"box\.space\.(?P<space>\w+)\s*:\s*(?P<operation>\w+)\s*\(",
        re.MULTILINE
    )

    # CLI command patterns
    ARGPARSE_PATTERN = re.compile(
        r"(?:parser|argparse)\s*(?::command|:argument|:option)\s*\(\s*['\"](?P<name>[^'\"]+)['\"]",
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all API/framework patterns from Lua source code.

        Args:
            content: Lua source code
            file_path: Path to source file

        Returns:
            Dict with 'routes', 'callbacks', 'event_handlers', 'commands' lists
        """
        routes = []
        callbacks = []
        event_handlers = []
        commands = []

        # LÖVE2D callbacks
        callbacks.extend(self._extract_love_callbacks(content, file_path))

        # Lapis routes
        routes.extend(self._extract_lapis_routes(content, file_path))

        # lor routes
        routes.extend(self._extract_lor_routes(content, file_path))

        # OpenResty directives
        callbacks.extend(self._extract_openresty(content, file_path))

        # CLI commands
        commands.extend(self._extract_cli_commands(content, file_path))

        return {
            'routes': routes,
            'callbacks': callbacks,
            'event_handlers': event_handlers,
            'commands': commands,
        }

    def _extract_love_callbacks(self, content: str, file_path: str) -> List[LuaCallbackInfo]:
        """Extract LÖVE2D callbacks."""
        results = []
        seen = set()

        for pattern in [self.LOVE_CALLBACK_PATTERN, self.LOVE_CALLBACK_ASSIGN_PATTERN]:
            for match in pattern.finditer(content):
                cb = match.group('callback')
                if cb not in seen and cb in self.LOVE_CALLBACKS:
                    seen.add(cb)
                    params = [p.strip() for p in match.group('params').split(',') if p.strip()]
                    line_num = content[:match.start()].count('\n') + 1
                    results.append(LuaCallbackInfo(
                        name=f"love.{cb}",
                        framework="love2d",
                        callback_type=self.LOVE_CALLBACKS[cb],
                        parameters=params,
                        file=file_path,
                        line_number=line_num,
                    ))

        return results

    def _extract_lapis_routes(self, content: str, file_path: str) -> List[LuaRouteInfo]:
        """Extract Lapis web framework routes."""
        results = []
        for pattern in [self.LAPIS_ROUTE_PATTERN, self.LAPIS_APP_ROUTE_PATTERN]:
            for match in pattern.finditer(content):
                method = match.group('method').upper()
                if method == 'MATCH':
                    method = 'ANY'
                path = match.group('path')
                line_num = content[:match.start()].count('\n') + 1
                results.append(LuaRouteInfo(
                    method=method,
                    path=path,
                    handler="",
                    framework="lapis",
                    file=file_path,
                    line_number=line_num,
                ))
        return results

    def _extract_lor_routes(self, content: str, file_path: str) -> List[LuaRouteInfo]:
        """Extract lor framework routes."""
        results = []
        for match in self.LOR_ROUTE_PATTERN.finditer(content):
            method = match.group('method').upper()
            if method == 'USE':
                method = 'MIDDLEWARE'
            path = match.group('path')
            line_num = content[:match.start()].count('\n') + 1
            results.append(LuaRouteInfo(
                method=method,
                path=path,
                handler="",
                framework="lor",
                file=file_path,
                line_number=line_num,
            ))
        return results

    def _extract_openresty(self, content: str, file_path: str) -> List[LuaCallbackInfo]:
        """Extract OpenResty/nginx-lua directives."""
        results = []
        seen = set()
        for match in self.CONTENT_BY_LUA_PATTERN.finditer(content):
            directive = match.group('directive')
            if directive not in seen:
                seen.add(directive)
                line_num = content[:match.start()].count('\n') + 1
                results.append(LuaCallbackInfo(
                    name=directive,
                    framework="openresty",
                    callback_type="nginx_phase",
                    file=file_path,
                    line_number=line_num,
                ))
        return results

    def _extract_cli_commands(self, content: str, file_path: str) -> List[LuaCommandInfo]:
        """Extract CLI command definitions."""
        results = []
        for match in self.ARGPARSE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            results.append(LuaCommandInfo(
                name=match.group('name'),
                framework="argparse",
                file=file_path,
                line_number=line_num,
            ))
        return results
