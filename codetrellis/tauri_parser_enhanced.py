"""
EnhancedTauriParser v1.0 - Comprehensive Tauri desktop framework parser.

Extracts Tauri-specific patterns from Rust source files:
- Commands (#[tauri::command], invoke handlers)
- State management (tauri::State, manage())
- Events (emit, listen, on_event)
- Plugin system (tauri::plugin::Builder)
- Window management (WindowBuilder, create_window)
- Menu system (CustomMenuItem, Menu, Submenu)
- System tray (SystemTray, SystemTrayMenu)
- IPC (invoke, command argument types)
- Configuration (tauri.conf.json patterns, Builder)
- File system and path APIs
- Updater patterns
- Multi-window support

Supports Tauri 1.x through 2.x.

Part of CodeTrellis - Rust Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TauriCommandInfo:
    name: str
    args: List[str] = field(default_factory=list)
    return_type: str = ""
    async_cmd: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class TauriStateInfo:
    type_name: str
    managed: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class TauriEventInfo:
    name: str
    kind: str = ""  # emit, listen, on_event, emit_all, once
    payload_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class TauriPluginInfo:
    name: str
    has_commands: bool = False
    has_state: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class TauriWindowInfo:
    label: str = ""
    kind: str = ""  # create_window, WindowBuilder, current_window, get_window
    file: str = ""
    line_number: int = 0


@dataclass
class TauriMenuInfo:
    kind: str  # CustomMenuItem, Menu, Submenu, SystemTray, SystemTrayMenu
    name: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class TauriConfigInfo:
    kind: str  # Builder, setup, invoke_handler, plugin, manage, on_*
    setting: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class TauriParseResult:
    file_path: str
    file_type: str = "rust"

    commands: List[TauriCommandInfo] = field(default_factory=list)
    state: List[TauriStateInfo] = field(default_factory=list)
    events: List[TauriEventInfo] = field(default_factory=list)
    plugins: List[TauriPluginInfo] = field(default_factory=list)
    windows: List[TauriWindowInfo] = field(default_factory=list)
    menus: List[TauriMenuInfo] = field(default_factory=list)
    configs: List[TauriConfigInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    tauri_version: str = ""


class EnhancedTauriParser:
    """
    Enhanced Tauri desktop framework parser for comprehensive analysis.

    Supports Tauri 1.x through 2.x:
    - v1.x: Original API with tauri::command, Builder pattern
    - v2.0: New plugin system, capability-based permissions, improved IPC
    """

    TAURI_DETECT = re.compile(
        r'(?:use\s+tauri|tauri::|#\[tauri::command\]|tauri::Builder)',
        re.MULTILINE
    )

    FRAMEWORK_PATTERNS = {
        'tauri': re.compile(r'\btauri\b'),
        'tauri-plugin-store': re.compile(r'tauri_plugin_store|tauri-plugin-store'),
        'tauri-plugin-sql': re.compile(r'tauri_plugin_sql|tauri-plugin-sql'),
        'tauri-plugin-http': re.compile(r'tauri_plugin_http|tauri-plugin-http'),
        'tauri-plugin-fs': re.compile(r'tauri_plugin_fs|tauri-plugin-fs'),
        'tauri-plugin-dialog': re.compile(r'tauri_plugin_dialog|tauri-plugin-dialog'),
        'tauri-plugin-shell': re.compile(r'tauri_plugin_shell|tauri-plugin-shell'),
        'tauri-plugin-notification': re.compile(r'tauri_plugin_notification|tauri-plugin-notification'),
        'tauri-plugin-updater': re.compile(r'tauri_plugin_updater|tauri-plugin-updater'),
        'tauri-plugin-log': re.compile(r'tauri_plugin_log|tauri-plugin-log'),
        'tauri-plugin-clipboard': re.compile(r'tauri_plugin_clipboard|tauri-plugin-clipboard'),
    }

    # #[tauri::command] / #[command]
    COMMAND_ATTR = re.compile(
        r'#\[tauri::command\]\s*(?:pub\s+)?(?P<async>async\s+)?fn\s+(?P<name>\w+)\s*\((?P<args>[^)]*)\)(?:\s*->\s*(?P<ret>[^{]+))?\s*\{',
        re.MULTILINE
    )

    # tauri::State<'_, AppState>
    STATE_TYPE = re.compile(
        r'(?:tauri::)?State\s*<[^,>]*,?\s*(?P<type>\w+)\s*>',
        re.MULTILINE
    )

    # .manage(state)
    MANAGE_CALL = re.compile(
        r'\.manage\s*\(\s*(?P<state>[^)]+)\)',
        re.MULTILINE
    )

    # Event emit: .emit("event", payload) / .emit_all("event", payload)
    EVENT_EMIT = re.compile(
        r'\.(?P<kind>emit|emit_all|emit_to)\s*\(\s*"(?P<event>[^"]+)"',
        re.MULTILINE
    )

    # Event listen: .listen("event", handler) / .once
    EVENT_LISTEN = re.compile(
        r'\.(?P<kind>listen|listen_global|once|once_global)\s*\(\s*"(?P<event>[^"]+)"',
        re.MULTILINE
    )

    # on_event: .on_window_event / .on_menu_event / .on_system_tray_event
    ON_EVENT = re.compile(
        r'\.(?P<kind>on_window_event|on_menu_event|on_system_tray_event)\s*\(',
        re.MULTILINE
    )

    # Plugin: tauri::plugin::Builder::new("name") / .plugin(...)
    PLUGIN_BUILDER = re.compile(
        r'(?:tauri::)?plugin::Builder::new\s*\(\s*"(?P<name>[^"]+)"',
        re.MULTILINE
    )

    PLUGIN_USE = re.compile(
        r'\.plugin\s*\(\s*(?P<plugin>[^)]+)\)',
        re.MULTILINE
    )

    # Window management
    WINDOW_CREATE = re.compile(
        r'(?:WindowBuilder::new|create_window|get_window|current_window)\s*\(\s*(?:[^,)]*,\s*)?"?(?P<label>[^",)]*)"?',
        re.MULTILINE
    )

    WINDOW_BUILDER = re.compile(
        r'WindowBuilder\s*::new\s*\(',
        re.MULTILINE
    )

    # Menu items
    MENU_ITEM = re.compile(
        r'(?P<kind>CustomMenuItem|MenuItemAttributes|MenuItem|Submenu|Menu|SystemTray|SystemTrayMenu)::(?:new|custom)\s*\(',
        re.MULTILINE
    )

    # Tauri Builder configuration
    BUILDER_PATTERN = re.compile(
        r'(?:tauri::)?Builder::default\s*\(\s*\)',
        re.MULTILINE
    )

    BUILDER_METHOD = re.compile(
        r'\.(?P<method>setup|invoke_handler|plugin|manage|on_window_event|on_menu_event|system_tray|menu|run)\s*\(',
        re.MULTILINE
    )

    # invoke_handler!(commands)
    INVOKE_HANDLER = re.compile(
        r'(?:tauri::)?generate_handler!\s*\[(?P<commands>[^\]]*)\]',
        re.MULTILINE
    )

    VERSION_FEATURES = {
        '2.x': [r'tauri\s*=\s*"2', r'tauri::Emitter', r'tauri::Listener', r'tauri_plugin_'],
        '1.x': [r'tauri\s*=\s*"1', r'generate_handler!', r'tauri::command'],
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> TauriParseResult:
        result = TauriParseResult(file_path=file_path)
        if not self.TAURI_DETECT.search(content):
            return result

        result.detected_frameworks = self._detect_frameworks(content)
        result.tauri_version = self._detect_version(content)
        result.commands = self._extract_commands(content, file_path)
        result.state = self._extract_state(content, file_path)
        result.events = self._extract_events(content, file_path)
        result.plugins = self._extract_plugins(content, file_path)
        result.windows = self._extract_windows(content, file_path)
        result.menus = self._extract_menus(content, file_path)
        result.configs = self._extract_configs(content, file_path)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        return [n for n, p in self.FRAMEWORK_PATTERNS.items() if p.search(content)]

    def _detect_version(self, content: str) -> str:
        for ver, patterns in self.VERSION_FEATURES.items():
            for p in patterns:
                if re.search(p, content):
                    return ver
        return ""

    def _extract_commands(self, content: str, file_path: str) -> List[TauriCommandInfo]:
        commands = []
        for m in self.COMMAND_ATTR.finditer(content):
            name = m.group('name')
            args_str = m.group('args') or ''
            ret = (m.group('ret') or '').strip()
            is_async = bool(m.group('async'))
            line_num = content[:m.start()].count('\n') + 1

            # Parse argument names (skip self, state, window, app_handle)
            args = []
            for arg in args_str.split(','):
                arg = arg.strip()
                if not arg or any(skip in arg for skip in ['self', 'State<', 'Window', 'AppHandle']):
                    continue
                arg_name = arg.split(':')[0].strip()
                if arg_name:
                    args.append(arg_name)

            commands.append(TauriCommandInfo(
                name=name, args=args, return_type=ret,
                async_cmd=is_async, file=file_path, line_number=line_num,
            ))

        # Also extract from generate_handler!
        for m in self.INVOKE_HANDLER.finditer(content):
            cmds_str = m.group('commands')
            for cmd_name in cmds_str.split(','):
                cmd_name = cmd_name.strip()
                if cmd_name and not any(c.name == cmd_name for c in commands):
                    line_num = content[:m.start()].count('\n') + 1
                    commands.append(TauriCommandInfo(
                        name=cmd_name, file=file_path, line_number=line_num,
                    ))

        return commands

    def _extract_state(self, content: str, file_path: str) -> List[TauriStateInfo]:
        state = []
        seen = set()

        for m in self.STATE_TYPE.finditer(content):
            type_name = m.group('type')
            if type_name not in seen:
                seen.add(type_name)
                line_num = content[:m.start()].count('\n') + 1
                state.append(TauriStateInfo(
                    type_name=type_name, file=file_path, line_number=line_num,
                ))

        for m in self.MANAGE_CALL.finditer(content):
            setting = m.group('state').strip()
            line_num = content[:m.start()].count('\n') + 1
            # Check if any state already found matches
            for s in state:
                if s.type_name.lower() in setting.lower():
                    s.managed = True

        return state

    def _extract_events(self, content: str, file_path: str) -> List[TauriEventInfo]:
        events = []

        for m in self.EVENT_EMIT.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            events.append(TauriEventInfo(
                name=m.group('event'), kind=m.group('kind'),
                file=file_path, line_number=line_num,
            ))

        for m in self.EVENT_LISTEN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            events.append(TauriEventInfo(
                name=m.group('event'), kind=m.group('kind'),
                file=file_path, line_number=line_num,
            ))

        for m in self.ON_EVENT.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            events.append(TauriEventInfo(
                name=m.group('kind'), kind='on_event',
                file=file_path, line_number=line_num,
            ))

        return events

    def _extract_plugins(self, content: str, file_path: str) -> List[TauriPluginInfo]:
        plugins = []

        for m in self.PLUGIN_BUILDER.finditer(content):
            name = m.group('name')
            line_num = content[:m.start()].count('\n') + 1
            # Look for .invoke_handler and .manage in the builder chain
            search_area = content[m.start():m.start() + 1000]
            has_commands = bool(re.search(r'\.invoke_handler', search_area))
            has_state = bool(re.search(r'\.manage', search_area))
            plugins.append(TauriPluginInfo(
                name=name, has_commands=has_commands, has_state=has_state,
                file=file_path, line_number=line_num,
            ))

        for m in self.PLUGIN_USE.finditer(content):
            plugin = m.group('plugin').strip()
            line_num = content[:m.start()].count('\n') + 1
            # Extract plugin name from common patterns:
            # tauri_plugin_store::init() or tauri_plugin_store::Builder::default().build()
            name_m = re.search(r'(tauri_plugin_\w+|[\w]+)::(?:init|Builder)', plugin)
            if not name_m:
                name_m = re.search(r'(\w+)::init', plugin)
            if name_m:
                name = name_m.group(1)
                if not any(p.name == name for p in plugins):
                    plugins.append(TauriPluginInfo(
                        name=name, file=file_path, line_number=line_num,
                    ))

        return plugins

    def _extract_windows(self, content: str, file_path: str) -> List[TauriWindowInfo]:
        windows = []
        for m in self.WINDOW_CREATE.finditer(content):
            label = m.group('label').strip() if m.group('label') else ''
            kind_str = content[m.start():m.start() + 30]
            kind = 'create_window'
            if 'WindowBuilder' in kind_str:
                kind = 'WindowBuilder'
            elif 'get_window' in kind_str:
                kind = 'get_window'
            elif 'current_window' in kind_str:
                kind = 'current_window'
            line_num = content[:m.start()].count('\n') + 1
            windows.append(TauriWindowInfo(
                label=label, kind=kind,
                file=file_path, line_number=line_num,
            ))
        return windows

    def _extract_menus(self, content: str, file_path: str) -> List[TauriMenuInfo]:
        menus = []
        for m in self.MENU_ITEM.finditer(content):
            kind = m.group('kind')
            line_num = content[:m.start()].count('\n') + 1
            menus.append(TauriMenuInfo(
                kind=kind, file=file_path, line_number=line_num,
            ))
        return menus

    def _extract_configs(self, content: str, file_path: str) -> List[TauriConfigInfo]:
        configs = []

        for m in self.BUILDER_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            configs.append(TauriConfigInfo(
                kind='Builder', file=file_path, line_number=line_num,
            ))

        for m in self.BUILDER_METHOD.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            configs.append(TauriConfigInfo(
                kind=m.group('method'), file=file_path, line_number=line_num,
            ))

        return configs
