"""
Pinia Plugin Extractor for CodeTrellis

Extracts Pinia plugin definitions and instance configuration:
- createPinia() instance creation
- pinia.use(plugin) plugin registration
- Built-in plugin patterns (persistedstate, debounce, orm)
- Custom plugin definitions ({ install(context) { ... } })
- PiniaPluginContext usage (store, app, pinia, options)
- Store augmentation via plugins
- SSR context configuration

Supports:
- Pinia v1.x-v2.x plugin API
- pinia-plugin-persistedstate v1-v4
- pinia-plugin-debounce
- pinia-orm
- Custom plugins with context.store augmentation

Part of CodeTrellis v4.52 - Pinia State Management Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PiniaPluginInfo:
    """Information about a Pinia plugin."""
    name: str
    file: str = ""
    line_number: int = 0
    plugin_type: str = ""  # built-in, custom, third-party
    is_persisted_state: bool = False
    is_debounce: bool = False
    is_orm: bool = False
    uses_context_store: bool = False
    uses_context_app: bool = False
    uses_context_pinia: bool = False
    uses_context_options: bool = False
    augments_store: bool = False
    is_exported: bool = False


@dataclass
class PiniaInstanceInfo:
    """Information about a createPinia() instance."""
    name: str = "pinia"
    file: str = ""
    line_number: int = 0
    plugins_registered: List[str] = field(default_factory=list)
    is_exported: bool = False
    has_ssr_context: bool = False


class PiniaPluginExtractor:
    """
    Extracts Pinia plugins and instance configuration.

    Detects:
    - createPinia() instance creation
    - pinia.use(plugin) registration
    - pinia-plugin-persistedstate
    - pinia-plugin-debounce
    - pinia-orm / @pinia/plugin-orm
    - Custom plugin functions: (context) => { context.store.$state... }
    - PiniaPluginContext destructuring: ({ store, app, pinia, options })
    - Store augmentation: store.$state, store.$patch, custom properties
    """

    # createPinia()
    CREATE_PINIA_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*createPinia\s*\(\s*\)',
        re.MULTILINE
    )

    # pinia.use(plugin)
    USE_PLUGIN_PATTERN = re.compile(
        r'(\w+)\.use\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # Plugin function definition
    PLUGIN_FUNCTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|function)\s+(\w+)\s*[:=]?\s*'
        r'(?:\(\s*(?:\{\s*(?:store|app|pinia|options)[^}]*\}|context|\w+)\s*\)|'
        r'\(\s*(?:\{\s*(?:store|app|pinia|options)[^}]*\}|context|\w+)\s*\))\s*(?:=>|:)',
        re.MULTILINE
    )

    # Simplified plugin detection: function with PiniaPluginContext
    PINIA_PLUGIN_CONTEXT_PATTERN = re.compile(
        r'PiniaPluginContext|'
        r'(?:const|function)\s+\w+.*?\(\s*\{\s*store\s*(?:,\s*(?:app|pinia|options))*\s*\}',
        re.MULTILINE
    )

    # pinia-plugin-persistedstate import
    PERSISTED_STATE_IMPORT = re.compile(
        r"from\s+['\"]pinia-plugin-persistedstate['\"]|"
        r"require\(['\"]pinia-plugin-persistedstate['\"]\)|"
        r"from\s+['\"]pinia-plugin-persist['\"]",
        re.MULTILINE
    )

    # pinia-plugin-debounce import
    DEBOUNCE_IMPORT = re.compile(
        r"from\s+['\"]pinia-plugin-debounce['\"]|"
        r"from\s+['\"]@pinia/plugin-debounce['\"]",
        re.MULTILINE
    )

    # pinia-orm import
    ORM_IMPORT = re.compile(
        r"from\s+['\"]pinia-orm['\"]|"
        r"from\s+['\"]@pinia/orm['\"]",
        re.MULTILINE
    )

    # Store augmentation patterns
    STORE_AUGMENT_PATTERN = re.compile(
        r'store\.\$|store\.\w+\s*=|context\.store\.',
        re.MULTILINE
    )

    # SSR context
    SSR_CONTEXT_PATTERN = re.compile(
        r'ssrContext|markRaw|useSSRContext|createPinia.*ssrContext',
        re.MULTILINE
    )

    # app.use(pinia) for Vue app integration
    APP_USE_PINIA_PATTERN = re.compile(
        r'app\.use\s*\(\s*(\w*[Pp]inia\w*)\s*\)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Pinia plugins and instance configuration.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dictionary with 'plugins' and 'instances' lists
        """
        plugins: List[PiniaPluginInfo] = []
        instances: List[PiniaInstanceInfo] = []

        # createPinia() instances
        for match in self.CREATE_PINIA_PATTERN.finditer(content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            instance = PiniaInstanceInfo(
                name=name,
                file=file_path,
                line_number=line,
                is_exported='export' in content[max(0, match.start() - 30):match.start()],
                has_ssr_context=bool(self.SSR_CONTEXT_PATTERN.search(content)),
            )

            # Find plugins registered on this instance
            for use_match in self.USE_PLUGIN_PATTERN.finditer(content):
                if use_match.group(1) == name:
                    plugin_name = use_match.group(2)
                    if plugin_name not in instance.plugins_registered:
                        instance.plugins_registered.append(plugin_name)

            instances.append(instance)

        # Detect third-party plugins by imports
        has_persisted = bool(self.PERSISTED_STATE_IMPORT.search(content))
        has_debounce = bool(self.DEBOUNCE_IMPORT.search(content))
        has_orm = bool(self.ORM_IMPORT.search(content))

        if has_persisted:
            plugins.append(PiniaPluginInfo(
                name="pinia-plugin-persistedstate",
                file=file_path,
                line_number=0,
                plugin_type="third-party",
                is_persisted_state=True,
            ))

        if has_debounce:
            plugins.append(PiniaPluginInfo(
                name="pinia-plugin-debounce",
                file=file_path,
                line_number=0,
                plugin_type="third-party",
                is_debounce=True,
            ))

        if has_orm:
            plugins.append(PiniaPluginInfo(
                name="pinia-orm",
                file=file_path,
                line_number=0,
                plugin_type="third-party",
                is_orm=True,
            ))

        # Custom plugin functions (using PiniaPluginContext pattern)
        if self.PINIA_PLUGIN_CONTEXT_PATTERN.search(content):
            for fn_match in self.PLUGIN_FUNCTION_PATTERN.finditer(content):
                name = fn_match.group(1)
                line = content[:fn_match.start()].count('\n') + 1
                region = content[fn_match.start():fn_match.start() + 1000]

                plugin = PiniaPluginInfo(
                    name=name,
                    file=file_path,
                    line_number=line,
                    plugin_type="custom",
                    uses_context_store='store' in region[:200],
                    uses_context_app='app' in region[:200],
                    uses_context_pinia='pinia' in region[:200],
                    uses_context_options='options' in region[:200],
                    augments_store=bool(self.STORE_AUGMENT_PATTERN.search(region)),
                    is_exported='export' in content[max(0, fn_match.start() - 30):fn_match.start()],
                )
                plugins.append(plugin)

        return {
            'plugins': plugins,
            'instances': instances,
        }
