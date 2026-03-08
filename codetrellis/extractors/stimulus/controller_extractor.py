"""
Stimulus Controller Extractor for CodeTrellis

Extracts Stimulus controller definitions from JavaScript/TypeScript source code:
- Controller class declarations (extends Controller / extends ApplicationController)
- Lifecycle callbacks: initialize(), connect(), disconnect()
- Connected/Disconnected callbacks: targetConnected(), targetDisconnected()
- Controller registration: application.register(), Application.start()
- Class inheritance detection
- v3.x: afterLoad static method, outlet callbacks

Supports:
- Stimulus v1.x (legacy `stimulus` package, Controller base class)
- Stimulus v2.x (@hotwired/stimulus, Controller with values/classes API)
- Stimulus v3.x (@hotwired/stimulus, outlets API, afterLoad)

Part of CodeTrellis v4.68 - Stimulus / Hotwire Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StimulusControllerInfo:
    """Information about a Stimulus controller definition."""
    name: str  # Controller class name (e.g., SearchController)
    file: str = ""
    line_number: int = 0
    identifier: str = ""  # kebab-case identifier (e.g., "search")
    extends: str = ""  # Base class (Controller, ApplicationController, etc.)
    has_initialize: bool = False
    has_connect: bool = False
    has_disconnect: bool = False
    has_after_load: bool = False  # v3.x static afterLoad
    has_target_connected: bool = False
    has_target_disconnected: bool = False
    has_outlet_connected: bool = False  # v3.x
    has_outlet_disconnected: bool = False  # v3.x
    static_targets: List[str] = field(default_factory=list)
    static_values: List[str] = field(default_factory=list)
    static_classes: List[str] = field(default_factory=list)
    static_outlets: List[str] = field(default_factory=list)  # v3.x
    methods: List[str] = field(default_factory=list)
    is_exported: bool = False
    is_default_export: bool = False
    is_registered: bool = False  # Registered via application.register()
    registration_name: str = ""  # Name used in register() call
    version_hint: str = ""  # v1, v2, v3


# Regex patterns for controller extraction
# Matches: export default class FooController extends Controller
CONTROLLER_CLASS_PATTERN = re.compile(
    r'^(?P<export>export\s+(?:default\s+)?)?class\s+'
    r'(?P<name>\w+Controller)\s+'
    r'extends\s+(?P<base>\w+)',
    re.MULTILINE
)

# Matches: static targets = ["name", "output"]
STATIC_TARGETS_PATTERN = re.compile(
    r'static\s+targets\s*=\s*\[([^\]]*)\]',
    re.DOTALL
)

# Matches: static values = { name: String, count: { type: Number, default: 0 } }
STATIC_VALUES_PATTERN = re.compile(
    r'static\s+values\s*=\s*\{([^}]*)\}',
    re.DOTALL
)

# Matches: static classes = ["active", "loading"]
STATIC_CLASSES_PATTERN = re.compile(
    r'static\s+classes\s*=\s*\[([^\]]*)\]',
    re.DOTALL
)

# Matches: static outlets = ["search-result", "item"]
STATIC_OUTLETS_PATTERN = re.compile(
    r'static\s+outlets\s*=\s*\[([^\]]*)\]',
    re.DOTALL
)

# Lifecycle methods
LIFECYCLE_METHODS = {
    'initialize', 'connect', 'disconnect',
    'targetConnected', 'targetDisconnected',
    'outletConnected', 'outletDisconnected',
}

# Registration: application.register("controller-name", ControllerClass)
REGISTER_PATTERN = re.compile(
    r'(?:application|app)\s*\.\s*register\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)',
    re.MULTILINE
)

# Method declaration pattern (inside class body)
METHOD_PATTERN = re.compile(
    r'^\s+(?:async\s+)?(?P<name>\w+)\s*\(',
    re.MULTILINE
)

# Static afterLoad method (v3.x)
AFTER_LOAD_PATTERN = re.compile(
    r'static\s+afterLoad\s*\(',
    re.MULTILINE
)


class StimulusControllerExtractor:
    """Extracts Stimulus controller definitions from JavaScript/TypeScript code."""

    def extract(self, content: str, file_path: str = "") -> List[StimulusControllerInfo]:
        """Extract Stimulus controller definitions from source code.

        Args:
            content: File content to parse.
            file_path: Path to the file (for metadata).

        Returns:
            List of StimulusControllerInfo objects.
        """
        if not content or not content.strip():
            return []

        controllers: List[StimulusControllerInfo] = []

        # Find controller class definitions
        for match in CONTROLLER_CLASS_PATTERN.finditer(content):
            export_str = match.group('export') or ''
            name = match.group('name')
            base = match.group('base')
            line_number = content[:match.start()].count('\n') + 1

            # Only process if extends Controller or a known base
            known_bases = {'Controller', 'ApplicationController', 'BridgeComponent'}
            if base not in known_bases and not base.endswith('Controller'):
                continue

            info = StimulusControllerInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                extends=base,
                is_exported='export' in export_str,
                is_default_export='default' in export_str,
            )

            # Derive kebab-case identifier from class name
            # SearchController -> search, ClipboardCopyController -> clipboard-copy
            identifier = name
            if identifier.endswith('Controller'):
                identifier = identifier[:-len('Controller')]
            # CamelCase to kebab-case
            identifier = re.sub(r'(?<!^)(?=[A-Z])', '-', identifier).lower()
            info.identifier = identifier

            # Extract class body (approximate - find matching brace)
            class_start = match.end()
            body = self._extract_class_body(content, class_start)

            if body:
                # Static targets
                targets_match = STATIC_TARGETS_PATTERN.search(body)
                if targets_match:
                    info.static_targets = self._parse_string_array(targets_match.group(1))

                # Static values
                values_match = STATIC_VALUES_PATTERN.search(body)
                if values_match:
                    info.static_values = self._parse_object_keys(values_match.group(1))

                # Static classes
                classes_match = STATIC_CLASSES_PATTERN.search(body)
                if classes_match:
                    info.static_classes = self._parse_string_array(classes_match.group(1))

                # Static outlets (v3.x)
                outlets_match = STATIC_OUTLETS_PATTERN.search(body)
                if outlets_match:
                    info.static_outlets = self._parse_string_array(outlets_match.group(1))
                    info.version_hint = "v3"

                # Lifecycle methods
                info.has_initialize = bool(re.search(r'\binitialize\s*\(', body))
                info.has_connect = bool(re.search(r'\bconnect\s*\(', body))
                info.has_disconnect = bool(re.search(r'\bdisconnect\s*\(', body))
                info.has_target_connected = bool(re.search(r'\b\w+TargetConnected\s*\(', body))
                info.has_target_disconnected = bool(re.search(r'\b\w+TargetDisconnected\s*\(', body))
                info.has_outlet_connected = bool(re.search(r'\b\w+OutletConnected\s*\(', body))
                info.has_outlet_disconnected = bool(re.search(r'\b\w+OutletDisconnected\s*\(', body))

                # afterLoad (v3.x)
                if AFTER_LOAD_PATTERN.search(body):
                    info.has_after_load = True
                    info.version_hint = "v3"

                # Extract method names
                methods = []
                for m in METHOD_PATTERN.finditer(body):
                    method_name = m.group('name')
                    if method_name not in LIFECYCLE_METHODS and method_name != 'constructor':
                        methods.append(method_name)
                info.methods = methods[:30]

            # Version hint from base class
            if base == 'BridgeComponent':
                info.version_hint = "strada"
            elif not info.version_hint:
                info.version_hint = "v2"  # Default to v2+ (@hotwired/stimulus)

            controllers.append(info)

        # Check for registration patterns
        for reg_match in REGISTER_PATTERN.finditer(content):
            reg_name = reg_match.group(1)
            reg_class = reg_match.group(2)
            for ctrl in controllers:
                if ctrl.name == reg_class:
                    ctrl.is_registered = True
                    ctrl.registration_name = reg_name
                    break

        return controllers

    def _extract_class_body(self, content: str, start: int) -> str:
        """Extract class body by brace matching."""
        brace_count = 0
        body_start = -1
        for i in range(start, min(start + 10000, len(content))):
            ch = content[i]
            if ch == '{':
                if brace_count == 0:
                    body_start = i + 1
                brace_count += 1
            elif ch == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[body_start:i]
        return content[body_start:start + 5000] if body_start >= 0 else ""

    def _parse_string_array(self, raw: str) -> List[str]:
        """Parse a JavaScript string array: ["foo", "bar", 'baz']."""
        return re.findall(r'["\'](\w[\w-]*)["\']', raw)

    def _parse_object_keys(self, raw: str) -> List[str]:
        """Parse JavaScript object keys: { name: String, count: Number }."""
        return re.findall(r'(\w+)\s*:', raw)
