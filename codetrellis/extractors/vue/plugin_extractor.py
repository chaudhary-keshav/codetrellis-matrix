"""
Vue.js Plugin Extractor for CodeTrellis

Extracts plugin definitions from Vue.js source code:
- Plugin objects with install function
- Plugin functions (simple install)
- app.use() registrations
- Global component/directive registrations via plugins
- app.config.globalProperties additions
- app.provide() for global provide/inject

Supports Vue 2.x (Vue.use) through Vue 3.5+ (app.use, createApp).

Part of CodeTrellis v4.34 - Vue.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VuePluginInfo:
    """Information about a Vue plugin definition."""
    name: str
    file: str = ""
    line_number: int = 0
    has_install: bool = False
    is_exported: bool = False
    options_type: str = ""
    global_components: List[str] = field(default_factory=list)
    global_directives: List[str] = field(default_factory=list)
    global_provides: List[str] = field(default_factory=list)
    global_properties: List[str] = field(default_factory=list)


@dataclass
class VueGlobalRegistrationInfo:
    """Information about a global registration (component, directive, etc.)."""
    name: str
    kind: str = ""  # component, directive, mixin, provide, property
    file: str = ""
    line_number: int = 0


class VuePluginExtractor:
    """
    Extracts Vue.js plugin definitions from source code.

    Detects:
    - Plugin objects ({ install(app, options) { ... } })
    - Plugin functions (function install(app) { ... })
    - app.use() calls
    - app.component() global registrations
    - app.directive() global registrations
    - app.mixin() registrations
    - app.provide() global provide
    - app.config.globalProperties additions
    """

    # Plugin object with install
    PLUGIN_OBJECT_PATTERN = re.compile(
        r'(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+(\w+)\s*(?::\s*Plugin\s*)?=\s*\{\s*'
        r'(?:[^}]*\n)*?\s*install\s*[:(]',
        re.MULTILINE
    )

    # Plugin install function
    PLUGIN_FUNCTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:function|const)\s+(\w+)\s*(?:=\s*)?(?:\([^)]*app[^)]*\)|:\s*Plugin)',
        re.MULTILINE
    )

    # export default { install() { ... } }
    EXPORT_DEFAULT_INSTALL_PATTERN = re.compile(
        r'export\s+default\s*\{\s*(?:[^}]*\n)*?\s*install\s*[:(]',
        re.MULTILINE
    )

    # app.use(plugin)
    APP_USE_PATTERN = re.compile(
        r'(?:app|Vue)\s*\.\s*use\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # app.component('name', Component)
    GLOBAL_COMPONENT_PATTERN = re.compile(
        r'(?:app|Vue)\s*\.\s*component\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(\w+)',
        re.MULTILINE
    )

    # app.directive('name', directive)
    GLOBAL_DIRECTIVE_PATTERN = re.compile(
        r'(?:app|Vue)\s*\.\s*directive\s*\(\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )

    # app.mixin(mixin)
    GLOBAL_MIXIN_PATTERN = re.compile(
        r'(?:app|Vue)\s*\.\s*mixin\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # app.provide(key, value)
    GLOBAL_PROVIDE_PATTERN = re.compile(
        r'(?:app|Vue)\s*\.\s*provide\s*\(\s*(?:[\'"]([^\'"]+)[\'"]|(\w+))',
        re.MULTILINE
    )

    # app.config.globalProperties.$name
    GLOBAL_PROPERTY_PATTERN = re.compile(
        r'(?:app|Vue)\s*\.\s*(?:config\s*\.\s*)?(?:globalProperties|prototype)\s*\.\s*\$?(\w+)\s*=',
        re.MULTILINE
    )

    # createApp
    CREATE_APP_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*createApp\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Vue plugin definitions from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'plugins', 'global_registrations', 'app_uses'
        """
        result: Dict[str, Any] = {
            'plugins': [],
            'global_registrations': [],
            'app_uses': [],
        }

        # Plugin objects
        for m in self.PLUGIN_OBJECT_PATTERN.finditer(content):
            name = m.group(1)
            plugin = VuePluginInfo(
                name=name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                has_install=True,
                is_exported='export' in content[max(0, m.start() - 10):m.start() + 10],
            )
            self._analyze_plugin_body(content[m.start():], plugin)
            result['plugins'].append(plugin)

        # Export default with install
        for m in self.EXPORT_DEFAULT_INSTALL_PATTERN.finditer(content):
            import os
            name = os.path.splitext(os.path.basename(file_path))[0] if file_path else "Plugin"
            plugin = VuePluginInfo(
                name=name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                has_install=True,
                is_exported=True,
            )
            self._analyze_plugin_body(content[m.start():], plugin)
            # Avoid duplicate if already found
            existing_names = {p.name for p in result['plugins']}
            if name not in existing_names:
                result['plugins'].append(plugin)

        # Global component registrations
        for m in self.GLOBAL_COMPONENT_PATTERN.finditer(content):
            result['global_registrations'].append(VueGlobalRegistrationInfo(
                name=m.group(1),
                kind="component",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Global directive registrations
        for m in self.GLOBAL_DIRECTIVE_PATTERN.finditer(content):
            result['global_registrations'].append(VueGlobalRegistrationInfo(
                name=m.group(1),
                kind="directive",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Global mixin registrations
        for m in self.GLOBAL_MIXIN_PATTERN.finditer(content):
            result['global_registrations'].append(VueGlobalRegistrationInfo(
                name=m.group(1),
                kind="mixin",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Global provides
        for m in self.GLOBAL_PROVIDE_PATTERN.finditer(content):
            name = m.group(1) or m.group(2) or ""
            result['global_registrations'].append(VueGlobalRegistrationInfo(
                name=name,
                kind="provide",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Global properties
        for m in self.GLOBAL_PROPERTY_PATTERN.finditer(content):
            result['global_registrations'].append(VueGlobalRegistrationInfo(
                name=m.group(1),
                kind="property",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # app.use() calls
        for m in self.APP_USE_PATTERN.finditer(content):
            result['app_uses'].append(m.group(1))

        return result

    def _analyze_plugin_body(self, body_text: str, plugin: VuePluginInfo) -> None:
        """Analyze plugin body for registrations."""
        # Limit analysis to ~2000 chars
        body = body_text[:2000]

        plugin.global_components = re.findall(
            r'app\.component\s*\(\s*[\'"]([^\'"]+)[\'"]', body
        )
        plugin.global_directives = re.findall(
            r'app\.directive\s*\(\s*[\'"]([^\'"]+)[\'"]', body
        )
        plugin.global_provides = re.findall(
            r'app\.provide\s*\(\s*[\'"]([^\'"]+)[\'"]', body
        )
        plugin.global_properties = re.findall(
            r'app\.config\.globalProperties\.\$?(\w+)', body
        )
