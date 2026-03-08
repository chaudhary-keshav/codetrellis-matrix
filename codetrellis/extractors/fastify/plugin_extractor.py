"""
Fastify Plugin Extractor - Extracts plugin registrations, decorators, and encapsulation.

Supports:
- fastify.register() plugin registration
- fastify-plugin (fp) wrapping for encapsulation skip
- Decorators: fastify.decorate(), decorateRequest(), decorateReply()
- Plugin prefixing
- Plugin options
- @fastify/autoload for directory-based loading
- Fastify 3.x through 5.x plugin patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class FastifyPluginInfo:
    """A Fastify plugin definition (export default or module.exports)."""
    name: str
    file: str = ""
    line_number: int = 0
    is_async: bool = False
    uses_fp: bool = False  # Wrapped with fastify-plugin
    has_options: bool = False
    encapsulation: str = "encapsulated"  # encapsulated, skip


@dataclass
class FastifyPluginRegistrationInfo:
    """A fastify.register() call."""
    plugin_name: str
    file: str = ""
    line_number: int = 0
    prefix: str = ""
    has_options: bool = False
    is_autoload: bool = False
    source_package: str = ""


@dataclass
class FastifyDecoratorInfo:
    """A fastify.decorate/decorateRequest/decorateReply call."""
    name: str
    file: str = ""
    line_number: int = 0
    target: str = ""  # server, request, reply
    value_type: str = ""  # function, object, primitive


class FastifyPluginExtractor:
    """Extracts Fastify plugin information from source code."""

    # fastify.register()
    REGISTER_PATTERN = re.compile(
        r'(\w+)\s*\.\s*register\s*\(\s*(\w+)',
    )

    # Register with prefix: fastify.register(plugin, { prefix: '/api' })
    REGISTER_PREFIX_PATTERN = re.compile(
        r"register\s*\([^,]+,\s*\{[^}]*prefix\s*:\s*['\"`]([^'\"`]+)['\"`]",
        re.DOTALL
    )

    # fastify-plugin wrapping: fp(plugin) or fastifyPlugin(plugin)
    FP_PATTERN = re.compile(
        r'(?:fp|fastifyPlugin)\s*\(\s*(?:async\s+)?(?:function\s+)?(\w+)?'
    )

    # Plugin export
    PLUGIN_EXPORT_PATTERN = re.compile(
        r'(?:module\.exports\s*=|export\s+default)\s*(?:fp\s*\(\s*)?(?:async\s+)?(?:function\s+)?(\w+)?',
    )

    # Decorator patterns
    DECORATE_PATTERN = re.compile(
        r"(\w+)\s*\.\s*(decorate|decorateRequest|decorateReply)\s*\(\s*['\"`](\w+)['\"`]"
    )

    # @fastify/autoload
    AUTOLOAD_PATTERN = re.compile(
        r"(?:fastifyAutoload|autoLoad|@fastify/autoload)"
    )

    # Known Fastify plugins from packages
    KNOWN_PLUGINS = {
        'cors': '@fastify/cors',
        'helmet': '@fastify/helmet',
        'rateLimit': '@fastify/rate-limit',
        'jwt': '@fastify/jwt',
        'cookie': '@fastify/cookie',
        'session': '@fastify/session',
        'multipart': '@fastify/multipart',
        'formbody': '@fastify/formbody',
        'swagger': '@fastify/swagger',
        'swaggerUi': '@fastify/swagger-ui',
        'websocket': '@fastify/websocket',
        'static': '@fastify/static',
        'compress': '@fastify/compress',
        'sensible': '@fastify/sensible',
        'auth': '@fastify/auth',
        'bearer': '@fastify/bearer-auth',
        'view': '@fastify/view',
        'etag': '@fastify/etag',
        'caching': '@fastify/caching',
        'circuitBreaker': '@fastify/circuit-breaker',
        'mongo': '@fastify/mongodb',
        'postgres': '@fastify/postgres',
        'redis': '@fastify/redis',
        'mysql': '@fastify/mysql',
    }

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract plugin information from Fastify source code."""
        plugins: List[FastifyPluginInfo] = []
        registrations: List[FastifyPluginRegistrationInfo] = []
        decorators: List[FastifyDecoratorInfo] = []
        lines = content.split('\n')

        # Build import map
        import_map = self._build_import_map(content)
        uses_fp = bool(self.FP_PATTERN.search(content))
        has_autoload = bool(self.AUTOLOAD_PATTERN.search(content))

        # Detect plugin definitions (exports)
        for match in self.PLUGIN_EXPORT_PATTERN.finditer(content):
            name = match.group(1) or 'default'
            line_num = content[:match.start()].count('\n') + 1
            plugins.append(FastifyPluginInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_async='async' in content[match.start():match.start()+50],
                uses_fp='fp(' in content[match.start():match.start()+100] or 'fastifyPlugin(' in content[match.start():match.start()+100],
                encapsulation='skip' if uses_fp else 'encapsulated',
            ))

        # Detect registrations
        for match in self.REGISTER_PATTERN.finditer(content):
            receiver = match.group(1)
            plugin_ref = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Check prefix
            prefix = ''
            prefix_match = self.REGISTER_PREFIX_PATTERN.search(
                content[match.start():match.start()+300]
            )
            if prefix_match:
                prefix = prefix_match.group(1)

            # Determine source package
            source = import_map.get(plugin_ref, '')
            for known_name, pkg in self.KNOWN_PLUGINS.items():
                if known_name in plugin_ref.lower() or pkg in source:
                    source = pkg
                    break

            registrations.append(FastifyPluginRegistrationInfo(
                plugin_name=plugin_ref,
                file=file_path,
                line_number=line_num,
                prefix=prefix,
                has_options=',' in content[match.start():match.start()+200],
                is_autoload='autoload' in plugin_ref.lower() or 'autoLoad' in plugin_ref,
                source_package=source,
            ))

        # Detect decorators
        for match in self.DECORATE_PATTERN.finditer(content):
            target_map = {
                'decorate': 'server',
                'decorateRequest': 'request',
                'decorateReply': 'reply',
            }
            line_num = content[:match.start()].count('\n') + 1
            decorators.append(FastifyDecoratorInfo(
                name=match.group(3),
                file=file_path,
                line_number=line_num,
                target=target_map.get(match.group(2), 'server'),
            ))

        return {
            "plugins": plugins,
            "registrations": registrations,
            "decorators": decorators,
        }

    def _build_import_map(self, content: str) -> Dict[str, str]:
        """Map variable names to imported package names."""
        import_map: Dict[str, str] = {}
        for match in re.finditer(r'import\s+(\w+)\s+from\s+[\'"`]([^\'"`]+)[\'"`]', content):
            import_map[match.group(1)] = match.group(2)
        for match in re.finditer(r'(?:const|let|var)\s+(\w+)\s*=\s*require\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)', content):
            import_map[match.group(1)] = match.group(2)
        return import_map
