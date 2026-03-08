"""
Hapi plugin extractor - Extract server.register() calls, plugin lifecycle, and dependencies.

Extracts:
- server.register() calls (single plugin, array of plugins, with options)
- Plugin definition objects (name, version, register function, dependencies)
- Plugin dependencies (server.dependency(), once flag)
- Built-in Hapi plugins (inert, vision, hapi-swagger, hapi-auth-jwt2, etc.)
- Plugin lifecycle (register, deregister, onPreStart, onPostStart, onPreStop)
- Plugin prefix/route options

Supports @hapi/hapi v17-v21+ plugin system.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class HapiPluginDependencyInfo:
    """Plugin dependency declaration."""
    plugin_name: str = ""
    required_by: str = ""
    line_number: int = 0


@dataclass
class HapiPluginInfo:
    """Information about a Hapi plugin registration or definition."""
    name: str = ""
    version: str = ""
    package_name: str = ""          # npm package (e.g. '@hapi/inert')
    is_builtin: bool = False        # @hapi/* official plugin
    is_custom: bool = False         # user-defined plugin
    options: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    routes_prefix: str = ""         # route prefix when registered
    has_register: bool = False
    lifecycle_hooks: List[str] = field(default_factory=list)  # onPreStart, etc.
    file: str = ""
    line_number: int = 0
    once: bool = False


class HapiPluginExtractor:
    """Extract Hapi plugin registrations and definitions."""

    # server.register(plugin) or server.register([plugin1, plugin2])
    REGISTER_PATTERN = re.compile(
        r'(?:await\s+)?server\.register\s*\(\s*',
        re.MULTILINE,
    )

    # Plugin object: { plugin: require('@hapi/inert'), options: {} }
    PLUGIN_REF_PATTERN = re.compile(
        r'plugin\s*:\s*(?:require\([\'"]([^\'"]+)[\'"]\)|(\w+))',
        re.MULTILINE,
    )

    # Direct plugin reference in register: server.register(Inert)
    DIRECT_PLUGIN_PATTERN = re.compile(
        r'server\.register\s*\(\s*(\w+)\s*[,)]',
        re.MULTILINE,
    )

    # Plugin definition: exports.plugin = { name, version, register }
    PLUGIN_DEF_PATTERN = re.compile(
        r'(?:exports\.plugin|module\.exports)\s*=\s*\{|'
        r'export\s+(?:default|const\s+\w+)\s*[:=]\s*\{[^}]*name\s*:',
        re.MULTILINE,
    )

    # Plugin name/version
    PLUGIN_NAME_PATTERN = re.compile(
        r'name\s*:\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE,
    )

    PLUGIN_VERSION_PATTERN = re.compile(
        r'version\s*:\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE,
    )

    # Plugin register function
    REGISTER_FUNC_PATTERN = re.compile(
        r'register\s*:\s*(?:async\s+)?(?:function\s+)?(?:\w+\s*)?\(',
        re.MULTILINE,
    )

    # server.dependency()
    DEPENDENCY_PATTERN = re.compile(
        r'server\.dependency\s*\(\s*(?:\[([^\]]+)\]|[\'"](\w+)[\'"])',
        re.MULTILINE,
    )

    # Route prefix: { routes: { prefix: '/api/v1' } }
    PREFIX_PATTERN = re.compile(
        r'routes\s*:\s*\{\s*prefix\s*:\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE,
    )

    # Plugin lifecycle hooks
    LIFECYCLE_PATTERN = re.compile(
        r'server\.ext\s*\(\s*[\'"](\w+)[\'"]',
        re.MULTILINE,
    )

    # once flag
    ONCE_PATTERN = re.compile(
        r'once\s*:\s*true',
        re.MULTILINE,
    )

    # Known @hapi/* official plugins
    HAPI_OFFICIAL_PLUGINS: Set[str] = {
        '@hapi/inert', '@hapi/vision', '@hapi/cookie', '@hapi/bell',
        '@hapi/basic', '@hapi/jwt', '@hapi/crumb', '@hapi/yar',
        '@hapi/good', '@hapi/nes', '@hapi/scooter', '@hapi/blankie',
        '@hapi/h2o2', '@hapi/accept', '@hapi/boom',
    }

    # Known community plugins
    COMMUNITY_PLUGINS: Set[str] = {
        'hapi-swagger', 'hapi-auth-jwt2', 'hapi-auth-bearer-token',
        'hapi-rate-limit', 'hapi-pino', 'hapi-boom-decorators',
        'hapi-auth-cookie', 'laabr', 'blipp', 'hapi-dev-errors',
        'hapi-alive', 'hapi-pagination', 'schmervice',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Hapi plugin information from source code.

        Returns:
            Dict with 'plugins' (List[HapiPluginInfo]),
                       'dependencies' (List[HapiPluginDependencyInfo])
        """
        plugins: List[HapiPluginInfo] = []
        dependencies: List[HapiPluginDependencyInfo] = []

        # ── Extract plugin registrations ─────────────────────────
        for match in self.REGISTER_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            block_start = match.start()
            block_end = min(block_start + 1500, len(content))
            block = content[block_start:block_end]

            # Find plugin references in register call
            for plugin_match in self.PLUGIN_REF_PATTERN.finditer(block):
                pkg = plugin_match.group(1) or ''
                var = plugin_match.group(2) or ''

                plugin = HapiPluginInfo(
                    name=var or pkg.split('/')[-1],
                    package_name=pkg,
                    file=file_path,
                    line_number=line_number,
                )

                if pkg in self.HAPI_OFFICIAL_PLUGINS:
                    plugin.is_builtin = True
                elif pkg in self.COMMUNITY_PLUGINS:
                    plugin.is_builtin = False

                # Check for route prefix
                prefix_match = self.PREFIX_PATTERN.search(block)
                if prefix_match:
                    plugin.routes_prefix = prefix_match.group(1)

                plugins.append(plugin)

            # Direct register: server.register(Inert)
            direct_match = self.DIRECT_PLUGIN_PATTERN.match(block)
            if direct_match and not plugins:
                var_name = direct_match.group(1)
                if var_name[0].isupper():  # Likely a plugin variable
                    plugin = HapiPluginInfo(
                        name=var_name,
                        file=file_path,
                        line_number=line_number,
                    )
                    plugins.append(plugin)

        # ── Extract plugin definitions ───────────────────────────
        for match in self.PLUGIN_DEF_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            block_start = match.start()
            block_end = min(block_start + 2000, len(content))
            block = content[block_start:block_end]

            plugin = HapiPluginInfo(
                is_custom=True,
                file=file_path,
                line_number=line_number,
            )

            # Name
            name_match = self.PLUGIN_NAME_PATTERN.search(block)
            if name_match:
                plugin.name = name_match.group(1)

            # Version
            ver_match = self.PLUGIN_VERSION_PATTERN.search(block)
            if ver_match:
                plugin.version = ver_match.group(1)

            # Register function
            if self.REGISTER_FUNC_PATTERN.search(block):
                plugin.has_register = True

            # Once
            if self.ONCE_PATTERN.search(block):
                plugin.once = True

            # Lifecycle hooks
            for hook_match in self.LIFECYCLE_PATTERN.finditer(block):
                plugin.lifecycle_hooks.append(hook_match.group(1))

            if plugin.name:
                plugins.append(plugin)

        # ── Extract dependencies ─────────────────────────────────
        for match in self.DEPENDENCY_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            deps_array = match.group(1) or match.group(2)
            if deps_array:
                dep_names = [d.strip().strip("'\"") for d in deps_array.split(',')]
                for dep_name in dep_names:
                    if dep_name:
                        dependencies.append(HapiPluginDependencyInfo(
                            plugin_name=dep_name,
                            line_number=line_number,
                        ))

        return {
            'plugins': plugins,
            'dependencies': dependencies,
        }
