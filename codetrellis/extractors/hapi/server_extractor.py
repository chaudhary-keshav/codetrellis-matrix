"""
Hapi server extractor - Extract server config, caching, server methods, ext points.

Extracts:
- Server creation (Hapi.server({ port, host, routes }))
- Server options (tls, compression, routes defaults, debug)
- Cache configuration (catbox, catbox-redis, catbox-memcached, server.cache)
- Server methods (server.method())
- Extension points (server.ext('onPreAuth', ...))
- Server decorations (server.decorate())
- Server bindings (server.bind())
- Connection keep-alive, payload limits

Supports @hapi/hapi v17-v21+ server configuration.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class HapiExtPointInfo:
    """Server extension point (lifecycle hook)."""
    event: str = ""             # onPreAuth, onPostAuth, onPreHandler, onPostHandler, etc.
    handler: str = ""           # handler function name
    is_async: bool = False
    bind: str = ""              # bind context
    file: str = ""
    line_number: int = 0


@dataclass
class HapiServerMethodInfo:
    """Server method registration."""
    name: str = ""              # 'users.list', 'math.add'
    handler: str = ""           # handler function name
    cache_config: Dict[str, Any] = field(default_factory=dict)
    bind: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class HapiCacheInfo:
    """Cache configuration (catbox)."""
    name: str = ""              # cache partition name
    provider: str = ""          # catbox-redis, catbox-memcached, catbox-memory
    engine: str = ""            # engine class name
    expires_in: int = 0         # milliseconds
    generate_timeout: int = 0
    segment: str = ""
    shared: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class HapiServerConfigInfo:
    """Server configuration details."""
    port: str = ""
    host: str = ""
    has_tls: bool = False
    has_compression: bool = False
    debug_mode: Dict[str, Any] = field(default_factory=dict)
    routes_defaults: Dict[str, Any] = field(default_factory=dict)
    payload_max_bytes: int = 0
    cors_enabled: bool = False
    decorations: List[str] = field(default_factory=list)
    bindings: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class HapiServerExtractor:
    """Extract Hapi server configuration, caching, methods, and ext points."""

    # Hapi.server() or new Hapi.Server()
    SERVER_CREATE_PATTERN = re.compile(
        r'(?:Hapi\.server|new\s+Hapi\.Server)\s*\(\s*\{',
        re.MULTILINE,
    )

    # Port and host
    PORT_PATTERN = re.compile(
        r'port\s*:\s*(?:(\d+)|process\.env\.(\w+)|[\'"](\d+)[\'"])',
        re.MULTILINE,
    )
    HOST_PATTERN = re.compile(
        r'host\s*:\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE,
    )

    # TLS
    TLS_PATTERN = re.compile(
        r'tls\s*:\s*\{',
        re.MULTILINE,
    )

    # Compression
    COMPRESSION_PATTERN = re.compile(
        r'compression\s*:\s*(?:true|\{)',
        re.MULTILINE,
    )

    # Debug
    DEBUG_PATTERN = re.compile(
        r'debug\s*:\s*\{([^}]+)\}',
        re.MULTILINE,
    )

    # Routes defaults
    ROUTES_DEFAULTS_PATTERN = re.compile(
        r'routes\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
        re.DOTALL,
    )

    # CORS in routes defaults
    CORS_PATTERN = re.compile(
        r'cors\s*:\s*(true|\{)',
        re.MULTILINE,
    )

    # Payload max bytes
    PAYLOAD_PATTERN = re.compile(
        r'maxBytes\s*:\s*(\d+)',
        re.MULTILINE,
    )

    # server.cache()
    CACHE_PATTERN = re.compile(
        r'server\.cache\s*\(\s*\{',
        re.MULTILINE,
    )

    # Cache provider patterns
    CACHE_PROVIDER_PATTERN = re.compile(
        r'(?:provider|engine)\s*:\s*(?:require\([\'"]([^\'"]+)[\'"]\)|(\w+))',
        re.MULTILINE,
    )

    CACHE_NAME_PATTERN = re.compile(
        r'name\s*:\s*[\'"](\w+)[\'"]',
        re.MULTILINE,
    )

    CACHE_SEGMENT_PATTERN = re.compile(
        r'segment\s*:\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE,
    )

    CACHE_EXPIRES_PATTERN = re.compile(
        r'expiresIn\s*:\s*(\d+)',
        re.MULTILINE,
    )

    CACHE_TIMEOUT_PATTERN = re.compile(
        r'generateTimeout\s*:\s*(\d+)',
        re.MULTILINE,
    )

    # Known cache providers
    CACHE_PROVIDERS: Set[str] = {
        '@hapi/catbox', '@hapi/catbox-memory', '@hapi/catbox-redis',
        '@hapi/catbox-memcached', 'catbox-redis', 'catbox-memcached',
        'catbox-memory', 'catbox-mongodb',
    }

    # server.method(name, method, options)
    SERVER_METHOD_PATTERN = re.compile(
        r'server\.method\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(async\s+)?(?:function\s+)?(?:(\w+)|\()',
        re.MULTILINE,
    )

    # server.ext(event, handler)
    EXT_PATTERN = re.compile(
        r'server\.ext\s*\(\s*[\'"](\w+)[\'"]\s*,\s*(?:async\s+)?(?:function\s+)?(\w+)?',
        re.MULTILINE,
    )

    # server.ext([{ type, method }])
    EXT_ARRAY_PATTERN = re.compile(
        r'type\s*:\s*[\'"](\w+)[\'"]\s*,\s*method\s*:\s*(?:async\s+)?(?:function\s+)?(\w+)?',
        re.MULTILINE,
    )

    # Valid ext events
    EXT_EVENTS: Set[str] = {
        'onPreStart', 'onPostStart', 'onPreStop', 'onPostStop',
        'onRequest', 'onPreAuth', 'onCredentials', 'onPostAuth',
        'onPreHandler', 'onPostHandler', 'onPreResponse',
    }

    # server.decorate(type, property, method)
    DECORATE_PATTERN = re.compile(
        r'server\.decorate\s*\(\s*[\'"](\w+)[\'"]\s*,\s*[\'"](\w+)[\'"]',
        re.MULTILINE,
    )

    # server.bind(context)
    BIND_PATTERN = re.compile(
        r'server\.bind\s*\(\s*(\w+)',
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Hapi server configuration from source code.

        Returns:
            Dict with 'config' (HapiServerConfigInfo),
                       'caches' (List[HapiCacheInfo]),
                       'methods' (List[HapiServerMethodInfo]),
                       'ext_points' (List[HapiExtPointInfo])
        """
        config = self._extract_server_config(content, file_path)
        caches = self._extract_caches(content, file_path)
        methods = self._extract_methods(content, file_path)
        ext_points = self._extract_ext_points(content, file_path)

        return {
            'config': config,
            'caches': caches,
            'methods': methods,
            'ext_points': ext_points,
        }

    def _extract_server_config(self, content: str, file_path: str) -> Optional[HapiServerConfigInfo]:
        """Extract server creation configuration."""
        match = self.SERVER_CREATE_PATTERN.search(content)
        if not match:
            return None

        line_number = content[:match.start()].count('\n') + 1
        block_start = match.start()
        block_end = min(block_start + 2000, len(content))
        block = content[block_start:block_end]

        config = HapiServerConfigInfo(
            file=file_path,
            line_number=line_number,
        )

        # Port
        port_match = self.PORT_PATTERN.search(block)
        if port_match:
            config.port = port_match.group(1) or port_match.group(2) or port_match.group(3) or ''

        # Host
        host_match = self.HOST_PATTERN.search(block)
        if host_match:
            config.host = host_match.group(1)

        # TLS
        config.has_tls = bool(self.TLS_PATTERN.search(block))

        # Compression
        config.has_compression = bool(self.COMPRESSION_PATTERN.search(block))

        # Debug
        debug_match = self.DEBUG_PATTERN.search(block)
        if debug_match:
            config.debug_mode = {'raw': debug_match.group(1).strip()}

        # CORS
        config.cors_enabled = bool(self.CORS_PATTERN.search(block))

        # Payload max bytes
        payload_match = self.PAYLOAD_PATTERN.search(block)
        if payload_match:
            config.payload_max_bytes = int(payload_match.group(1))

        # Decorations
        for dec_match in self.DECORATE_PATTERN.finditer(content):
            dec_type = dec_match.group(1)
            dec_prop = dec_match.group(2)
            config.decorations.append(f"{dec_type}.{dec_prop}")

        # Bindings
        for bind_match in self.BIND_PATTERN.finditer(content):
            config.bindings.append(bind_match.group(1))

        return config

    def _extract_caches(self, content: str, file_path: str) -> List[HapiCacheInfo]:
        """Extract cache configurations."""
        caches: List[HapiCacheInfo] = []

        # server.cache() calls
        for match in self.CACHE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            block_start = match.start()
            block_end = min(block_start + 1000, len(content))
            block = content[block_start:block_end]

            cache = HapiCacheInfo(
                file=file_path,
                line_number=line_number,
            )

            # Provider
            provider_match = self.CACHE_PROVIDER_PATTERN.search(block)
            if provider_match:
                cache.provider = provider_match.group(1) or provider_match.group(2) or ''
                cache.engine = cache.provider.split('/')[-1] if cache.provider else ''

            # Name
            name_match = self.CACHE_NAME_PATTERN.search(block)
            if name_match:
                cache.name = name_match.group(1)

            # Segment
            segment_match = self.CACHE_SEGMENT_PATTERN.search(block)
            if segment_match:
                cache.segment = segment_match.group(1)

            # Expires
            expires_match = self.CACHE_EXPIRES_PATTERN.search(block)
            if expires_match:
                cache.expires_in = int(expires_match.group(1))

            # Generate timeout
            timeout_match = self.CACHE_TIMEOUT_PATTERN.search(block)
            if timeout_match:
                cache.generate_timeout = int(timeout_match.group(1))

            # Shared
            if re.search(r'shared\s*:\s*true', block):
                cache.shared = True

            caches.append(cache)

        # Also detect cache providers from imports
        for provider in self.CACHE_PROVIDERS:
            if re.search(re.escape(provider), content):
                # Check if we already captured this provider
                found = any(c.provider == provider for c in caches)
                if not found:
                    caches.append(HapiCacheInfo(
                        provider=provider,
                        engine=provider.split('/')[-1],
                        file=file_path,
                    ))

        return caches

    def _extract_methods(self, content: str, file_path: str) -> List[HapiServerMethodInfo]:
        """Extract server method registrations."""
        methods: List[HapiServerMethodInfo] = []

        for match in self.SERVER_METHOD_PATTERN.finditer(content):
            name = match.group(1)
            is_async = bool(match.group(2))
            named_handler = match.group(3) or ''
            handler = ('async ' if is_async else '') + (named_handler or '<anonymous>')
            line_number = content[:match.start()].count('\n') + 1

            method = HapiServerMethodInfo(
                name=name,
                handler=handler,
                file=file_path,
                line_number=line_number,
            )

            # Check for cache in method options
            block_start = match.start()
            block_end = min(block_start + 500, len(content))
            block = content[block_start:block_end]

            cache_match = re.search(r'cache\s*:\s*\{([^}]+)\}', block)
            if cache_match:
                cache_str = cache_match.group(1)
                expires_match = self.CACHE_EXPIRES_PATTERN.search(cache_str)
                if expires_match:
                    method.cache_config['expiresIn'] = int(expires_match.group(1))
                timeout_match = self.CACHE_TIMEOUT_PATTERN.search(cache_str)
                if timeout_match:
                    method.cache_config['generateTimeout'] = int(timeout_match.group(1))

            methods.append(method)

        return methods

    def _extract_ext_points(self, content: str, file_path: str) -> List[HapiExtPointInfo]:
        """Extract server extension points."""
        ext_points: List[HapiExtPointInfo] = []
        seen: Set[str] = set()

        # server.ext('event', handler)
        for match in self.EXT_PATTERN.finditer(content):
            event = match.group(1)
            handler = match.group(2) or '(anonymous)'
            line_number = content[:match.start()].count('\n') + 1

            key = f"{event}:{line_number}"
            if key in seen:
                continue
            seen.add(key)

            if event in self.EXT_EVENTS:
                ext = HapiExtPointInfo(
                    event=event,
                    handler=handler,
                    file=file_path,
                    line_number=line_number,
                )

                # Check if async
                block_start = max(0, match.start() - 20)
                block_end = match.end() + 50
                block = content[block_start:block_end]
                ext.is_async = 'async' in block

                ext_points.append(ext)

        # server.ext([{ type, method }])
        for match in self.EXT_ARRAY_PATTERN.finditer(content):
            event = match.group(1)
            handler = match.group(2) or '(anonymous)'
            line_number = content[:match.start()].count('\n') + 1

            key = f"{event}:{line_number}"
            if key in seen:
                continue
            seen.add(key)

            if event in self.EXT_EVENTS:
                ext_points.append(HapiExtPointInfo(
                    event=event,
                    handler=handler,
                    file=file_path,
                    line_number=line_number,
                ))

        return ext_points
