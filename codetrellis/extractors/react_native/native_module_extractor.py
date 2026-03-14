"""
React Native Native Module Extractor for CodeTrellis

Extracts native module and bridge patterns from React Native source code:
- NativeModules usage (NativeModules.ModuleName)
- TurboModules / New Architecture specs (TurboModuleRegistrySpec)
- Fabric components (codegenNativeComponent, HostComponent)
- Native event emitters (NativeEventEmitter, DeviceEventEmitter)
- Bridge calls and native method invocations
- Codegen specifications (Native*.js interface files)
- JSI bindings and direct native access

Supports React Native 0.59+ (Bridge) through 0.76+ (Bridgeless/New Architecture).

Part of CodeTrellis v5.6 - React Native Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class RNNativeModuleInfo:
    """Information about a NativeModule usage."""
    name: str
    file: str = ""
    line_number: int = 0
    module_name: str = ""  # The native module name accessed
    methods_called: List[str] = field(default_factory=list)
    is_event_emitter: bool = False
    architecture: str = "bridge"  # bridge, turbo_module, jsi


@dataclass
class RNTurboModuleInfo:
    """Information about a TurboModule specification (New Architecture)."""
    name: str
    file: str = ""
    line_number: int = 0
    spec_name: str = ""  # Spec interface name (e.g., NativeCalculatorSpec)
    methods: List[str] = field(default_factory=list)
    is_sync: bool = False
    constants: List[str] = field(default_factory=list)


@dataclass
class RNFabricComponentInfo:
    """Information about a Fabric component (New Architecture)."""
    name: str
    file: str = ""
    line_number: int = 0
    component_name: str = ""
    props_type: str = ""
    events: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    is_codegen: bool = False


class ReactNativeNativeModuleExtractor:
    """
    Extracts native module patterns from React Native source code.

    Detects:
    - NativeModules.X access patterns
    - TurboModule specifications (New Architecture)
    - Fabric component specs (codegenNativeComponent)
    - NativeEventEmitter / DeviceEventEmitter usage
    - JSI direct bindings (global.__jsi)
    - Codegen interface files (Native*.js/ts)
    """

    # NativeModules access
    NATIVE_MODULES_ACCESS = re.compile(
        r"NativeModules\.(\w+)",
        re.MULTILINE
    )

    # NativeModules destructuring
    NATIVE_MODULES_DESTRUCTURE = re.compile(
        r"(?:const|let|var)\s+\{([^}]+)\}\s*=\s*NativeModules",
        re.MULTILINE
    )

    # requireNativeComponent (legacy)
    REQUIRE_NATIVE_COMPONENT = re.compile(
        r"requireNativeComponent\s*[<(]\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # TurboModuleRegistry
    TURBO_MODULE = re.compile(
        r"TurboModuleRegistry\.(?:get|getEnforcing)\s*[<(]\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # TurboModule spec interface
    TURBO_MODULE_SPEC = re.compile(
        r"(?:export\s+)?interface\s+(Native\w*Spec)\s+extends\s+TurboModule",
        re.MULTILINE
    )

    # Fabric codegenNativeComponent
    FABRIC_CODEGEN = re.compile(
        r"codegenNativeComponent\s*<\s*(\w+)\s*>\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # codegenNativeCommands
    FABRIC_COMMANDS = re.compile(
        r"codegenNativeCommands\s*<\s*(\w+)\s*>",
        re.MULTILINE
    )

    # NativeEventEmitter
    NATIVE_EVENT_EMITTER = re.compile(
        r"new\s+NativeEventEmitter\s*\(\s*(?:NativeModules\.)?(\w+)",
        re.MULTILINE
    )

    # DeviceEventEmitter
    DEVICE_EVENT_EMITTER = re.compile(
        r"DeviceEventEmitter\.addListener\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # JSI bindings
    JSI_BINDING = re.compile(
        r"global\.__\w+|jsi::\w+|installJSI|nativeCallSyncHook",
        re.MULTILINE
    )

    # method calls on native modules
    NATIVE_METHOD_CALL = re.compile(
        r"(?:NativeModules\.\w+|self\.\w+Module)\.(\w+)\s*\(",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract native module information from source code.

        Returns:
            Dict with keys: native_modules, turbo_modules, fabric_components
        """
        native_modules = []
        turbo_modules = []
        fabric_components = []

        # NativeModules direct access
        accessed_modules = set()
        for match in self.NATIVE_MODULES_ACCESS.finditer(content):
            module_name = match.group(1)
            if module_name not in accessed_modules:
                accessed_modules.add(module_name)
                line_num = content[:match.start()].count('\n') + 1

                methods = []
                for mm in re.finditer(rf'NativeModules\.{re.escape(module_name)}\.(\w+)\s*\(', content):
                    method = mm.group(1)
                    if method not in methods:
                        methods.append(method)

                is_emitter = bool(re.search(
                    rf'NativeEventEmitter\s*\(\s*(?:NativeModules\.)?{re.escape(module_name)}',
                    content
                ))

                native_modules.append(RNNativeModuleInfo(
                    name=module_name,
                    file=file_path,
                    line_number=line_num,
                    module_name=module_name,
                    methods_called=methods[:15],
                    is_event_emitter=is_emitter,
                    architecture="bridge",
                ))

        # NativeModules destructuring
        for match in self.NATIVE_MODULES_DESTRUCTURE.finditer(content):
            names = [n.strip().split(' as ')[0].strip() for n in match.group(1).split(',')]
            line_num = content[:match.start()].count('\n') + 1
            for name in names:
                if name and name not in accessed_modules:
                    accessed_modules.add(name)
                    native_modules.append(RNNativeModuleInfo(
                        name=name,
                        file=file_path,
                        line_number=line_num,
                        module_name=name,
                        architecture="bridge",
                    ))

        # TurboModule registry access
        for match in self.TURBO_MODULE.finditer(content):
            module_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            native_modules.append(RNNativeModuleInfo(
                name=module_name,
                file=file_path,
                line_number=line_num,
                module_name=module_name,
                architecture="turbo_module",
            ))

        # TurboModule spec interfaces
        for match in self.TURBO_MODULE_SPEC.finditer(content):
            spec_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Extract methods from the spec
            spec_section = content[match.start():match.start() + 2000]
            methods = []
            constants = []
            for mm in re.finditer(r'(\w+)\s*\([^)]*\)\s*:', spec_section):
                method = mm.group(1)
                if method != 'getConstants':
                    methods.append(method)
                else:
                    constants.append(method)
            is_sync = 'Sync' in spec_name or bool(re.search(r'\bsync\b', spec_section, re.IGNORECASE))

            turbo_modules.append(RNTurboModuleInfo(
                name=spec_name,
                file=file_path,
                line_number=line_num,
                spec_name=spec_name,
                methods=methods[:15],
                is_sync=is_sync,
                constants=constants[:10],
            ))

        # Fabric codegenNativeComponent
        for match in self.FABRIC_CODEGEN.finditer(content):
            props_type = match.group(1)
            component_name = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Extract events
            events = []
            for em in re.finditer(r"BubblingEventHandler<[^>]*>|DirectEventHandler<[^>]*>", content):
                event_match = re.search(r'on(\w+)', content[max(0, em.start()-50):em.start()])
                if event_match:
                    events.append(event_match.group(0))

            # Extract commands
            commands = []
            cmd_match = self.FABRIC_COMMANDS.search(content)
            if cmd_match:
                cmd_section = content[cmd_match.start():cmd_match.start() + 500]
                for cm in re.finditer(r"(\w+)\s*\(", cmd_section):
                    name = cm.group(1)
                    if name not in ('codegenNativeCommands', 'supportedCommands'):
                        commands.append(name)

            fabric_components.append(RNFabricComponentInfo(
                name=component_name,
                file=file_path,
                line_number=line_num,
                component_name=component_name,
                props_type=props_type,
                events=events[:10],
                commands=commands[:10],
                is_codegen=True,
            ))

        # DeviceEventEmitter listeners (standalone events)
        for match in self.DEVICE_EVENT_EMITTER.finditer(content):
            event_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            native_modules.append(RNNativeModuleInfo(
                name=f"DeviceEvent:{event_name}",
                file=file_path,
                line_number=line_num,
                module_name="DeviceEventEmitter",
                is_event_emitter=True,
                architecture="bridge",
            ))

        # JSI bindings detection
        if self.JSI_BINDING.search(content):
            m = self.JSI_BINDING.search(content)
            native_modules.append(RNNativeModuleInfo(
                name="JSI",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                module_name="JSI",
                architecture="jsi",
            ))

        return {
            'native_modules': native_modules,
            'turbo_modules': turbo_modules,
            'fabric_components': fabric_components,
        }
