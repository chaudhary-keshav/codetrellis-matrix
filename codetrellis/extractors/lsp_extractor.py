"""
LSP Type Extractor for CodeTrellis

Uses TypeScript compiler API for accurate type extraction with full resolution.
Falls back to regex-based extraction if LSP is unavailable.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Union
import logging

from ..lsp_client import (
    get_lsp_client,
    LSPExtractionResult,
    LSPInterface,
    LSPTypeAlias,
    LSPClass,
    LSPSignalStore,
    LSPInputSignal,
    LSPOutputSignal,
)
from ..interfaces import InterfaceInfo, PropertyInfo, MethodInfo

logger = logging.getLogger(__name__)


@dataclass
class LSPExtractionStats:
    """Statistics from LSP extraction"""
    files_processed: int = 0
    interfaces_found: int = 0
    types_found: int = 0
    classes_found: int = 0
    components_found: int = 0
    services_found: int = 0
    stores_found: int = 0
    processing_time_ms: int = 0
    lsp_used: bool = False
    fallback_reason: Optional[str] = None
    classes_found: int = 0
    processing_time_ms: int = 0
    lsp_used: bool = False
    fallback_reason: Optional[str] = None


@dataclass
class EnhancedInterfaceInfo(InterfaceInfo):
    """Interface info with LSP-enhanced type information"""
    lsp_resolved: bool = False
    generics: list[str] = field(default_factory=list)
    extends: list[str] = field(default_factory=list)
    documentation: Optional[str] = None


class LSPExtractor:
    """
    Extracts types using TypeScript LSP for accurate resolution.

    This extractor provides:
    - Fully resolved generic types
    - Cross-file type references
    - Inferred return types
    - Complete union/intersection types
    - Accurate class hierarchy information
    """

    def __init__(self, project_path: Union[str, Path]):
        self.project_path = Path(project_path).resolve()
        self._client = get_lsp_client()
        self._result: Optional[LSPExtractionResult] = None
        self._stats = LSPExtractionStats()

    @property
    def stats(self) -> LSPExtractionStats:
        """Get extraction statistics"""
        return self._stats

    def is_available(self) -> bool:
        """Check if LSP extraction is available for this project"""
        if not self._client.is_available():
            return False

        # Check for tsconfig.json
        tsconfig = self.project_path / 'tsconfig.json'
        return tsconfig.exists()

    def extract(self, timeout: int = 120) -> bool:
        """
        Run LSP extraction on the project.

        Returns:
            True if extraction was successful, False if fallback needed
        """
        if not self.is_available():
            self._stats.lsp_used = False
            self._stats.fallback_reason = "LSP not available (Node.js or tsconfig.json missing)"
            logger.info("LSP extraction not available, will use regex fallback")
            return False

        logger.info(f"Starting LSP extraction for {self.project_path}")
        self._result = self._client.extract(self.project_path, timeout)

        if not self._result.success:
            self._stats.lsp_used = False
            self._stats.fallback_reason = self._result.fallback_reason
            logger.warning(f"LSP extraction failed: {self._result.fallback_reason}")
            return False

        self._stats.lsp_used = True
        self._stats.files_processed = self._result.files_processed
        self._stats.interfaces_found = len(self._result.interfaces)
        self._stats.types_found = len(self._result.types)
        self._stats.classes_found = len(self._result.classes)
        self._stats.components_found = self._result.components_found
        self._stats.services_found = self._result.services_found
        self._stats.stores_found = self._result.stores_found
        self._stats.processing_time_ms = self._result.processing_time_ms

        logger.info(
            f"LSP extraction complete: {self._stats.interfaces_found} interfaces, "
            f"{self._stats.types_found} types, {self._stats.classes_found} classes, "
            f"{self._stats.components_found} components, {self._stats.services_found} services, "
            f"{self._stats.stores_found} stores in {self._stats.processing_time_ms}ms"
        )

        return True

    def get_interfaces(self) -> list[EnhancedInterfaceInfo]:
        """Get extracted interfaces as EnhancedInterfaceInfo objects"""
        if not self._result or not self._result.success:
            return []

        interfaces = []
        for lsp_iface in self._result.interfaces:
            iface = self._convert_interface(lsp_iface)
            interfaces.append(iface)

        return interfaces

    def get_types_as_interfaces(self) -> list[EnhancedInterfaceInfo]:
        """
        Get type aliases as InterfaceInfo objects for compatibility.

        This allows type aliases to be included in the same output format.
        """
        if not self._result or not self._result.success:
            return []

        types = []
        for lsp_type in self._result.types:
            # Convert type alias to pseudo-interface for output
            iface = EnhancedInterfaceInfo(
                name=lsp_type.name,
                file_path=lsp_type.file_path,
                exported=lsp_type.exported,
                properties=[],
                methods=[],
                lsp_resolved=True,
                documentation=lsp_type.documentation,
            )

            # Add the type definition as a special property
            iface.properties.append(PropertyInfo(
                name='__type__',
                type=lsp_type.definition,
                optional=False,
                readonly=True,
            ))

            types.append(iface)

        return types

    def get_classes_as_interfaces(self) -> list[EnhancedInterfaceInfo]:
        """Get extracted classes as EnhancedInterfaceInfo for compatibility"""
        if not self._result or not self._result.success:
            return []

        classes = []
        for lsp_class in self._result.classes:
            iface = self._convert_class(lsp_class)
            classes.append(iface)

        return classes

    def get_all_types(self) -> list[EnhancedInterfaceInfo]:
        """Get all extracted types (interfaces, type aliases, classes)"""
        all_types = []
        all_types.extend(self.get_interfaces())
        all_types.extend(self.get_types_as_interfaces())
        all_types.extend(self.get_classes_as_interfaces())
        return all_types

    def get_components(self) -> list[LSPClass]:
        """Get Angular components extracted by LSP"""
        if not self._result or not self._result.success:
            return []
        return [c for c in self._result.classes if c.is_component]

    def get_services(self) -> list[LSPClass]:
        """Get Angular services extracted by LSP"""
        if not self._result or not self._result.success:
            return []
        return [c for c in self._result.classes if c.is_service]

    def get_directives(self) -> list[LSPClass]:
        """Get Angular directives extracted by LSP"""
        if not self._result or not self._result.success:
            return []
        return [c for c in self._result.classes if c.is_directive]

    def get_pipes(self) -> list[LSPClass]:
        """Get Angular pipes extracted by LSP"""
        if not self._result or not self._result.success:
            return []
        return [c for c in self._result.classes if c.is_pipe]

    def get_stores(self) -> list[LSPSignalStore]:
        """Get NgRx SignalStores extracted by LSP"""
        if not self._result or not self._result.success:
            return []
        return self._result.stores

    def _convert_interface(self, lsp_iface: LSPInterface) -> EnhancedInterfaceInfo:
        """Convert LSP interface to EnhancedInterfaceInfo"""
        properties = [
            PropertyInfo(
                name=p.name,
                type=p.type,
                optional=p.optional,
                readonly=p.readonly,
            )
            for p in lsp_iface.properties
        ]

        methods = [
            MethodInfo(
                name=m.name,
                params=self._format_params(m.parameters),
                return_type=m.return_type,
            )
            for m in lsp_iface.methods
        ]

        return EnhancedInterfaceInfo(
            name=lsp_iface.name,
            file_path=lsp_iface.file_path,
            exported=lsp_iface.exported,
            properties=properties,
            methods=methods,
            lsp_resolved=True,
            generics=lsp_iface.generics,
            extends=lsp_iface.extends,
            documentation=lsp_iface.documentation,
        )

    def _convert_class(self, lsp_class: LSPClass) -> EnhancedInterfaceInfo:
        """Convert LSP class to EnhancedInterfaceInfo"""
        properties = [
            PropertyInfo(
                name=p.name,
                type=p.type,
                optional=p.optional,
                readonly=p.readonly,
            )
            for p in lsp_class.properties
        ]

        methods = [
            MethodInfo(
                name=m.name,
                params=self._format_params(m.parameters),
                return_type=m.return_type,
            )
            for m in lsp_class.methods
        ]

        # Create extends list
        extends = []
        if lsp_class.extends:
            extends.append(lsp_class.extends)
        extends.extend(lsp_class.implements or [])

        # Prefix decorators to name for Angular components
        name = lsp_class.name
        if lsp_class.decorators:
            decorator_str = ','.join(f"@{d}" for d in lsp_class.decorators)
            name = f"{decorator_str}|{name}"

        return EnhancedInterfaceInfo(
            name=name,
            file_path=lsp_class.file_path,
            exported=lsp_class.exported,
            properties=properties,
            methods=methods,
            lsp_resolved=True,
            generics=[],
            extends=extends,
            documentation=lsp_class.documentation,
        )

    def _format_params(self, params: list[dict]) -> str:
        """Format parameter list for MethodInfo"""
        parts = []
        for p in params:
            if p.get('optional'):
                parts.append(f"{p['name']}?:{p['type']}")
            else:
                parts.append(f"{p['name']}:{p['type']}")
        return ','.join(parts)

    def get_compact_output(self) -> str:
        """
        Generate compact CodeTrellis-format output from LSP extraction.

        Returns output compatible with existing CodeTrellis format but with
        LSP-accurate types, including Angular-specific sections.
        """
        if not self._result or not self._result.success:
            return ""

        lines = []
        lines.append(f"# LSP Types: {self._stats.interfaces_found} interfaces, "
                     f"{self._stats.types_found} types, {self._stats.classes_found} classes, "
                     f"{self._stats.components_found} components, {self._stats.services_found} services, "
                     f"{self._stats.stores_found} stores")
        lines.append("")

        # Angular Components (separate from generic classes)
        components = [c for c in self._result.classes if c.is_component]
        if components:
            lines.append("[COMPONENTS:LSP]")
            for comp in components:
                line = self._format_component_line(comp)
                lines.append(line)
            lines.append("")

        # Angular Services (separate from generic classes)
        services = [c for c in self._result.classes if c.is_service]
        if services:
            lines.append("[ANGULAR_SERVICES:LSP]")
            for svc in services:
                line = self._format_service_line(svc)
                lines.append(line)
            lines.append("")

        # NgRx SignalStores
        if self._result.stores:
            lines.append("[STORES:LSP]")
            for store in self._result.stores:
                line = self._format_store_line(store)
                lines.append(line)
            lines.append("")

        # Interfaces
        if self._result.interfaces:
            lines.append("[INTERFACES:LSP]")
            for iface in self._result.interfaces:
                line = self._format_interface_line(iface)
                lines.append(line)
            lines.append("")

        # Type aliases
        if self._result.types:
            lines.append("[TYPES:LSP]")
            for type_alias in self._result.types:
                line = self._format_type_line(type_alias)
                lines.append(line)
            lines.append("")

        # Non-Angular Classes (directives, pipes, other classes)
        other_classes = [c for c in self._result.classes
                        if not c.is_component and not c.is_service]
        if other_classes:
            lines.append("[CLASSES:LSP]")
            for cls in other_classes:
                line = self._format_class_line(cls)
                lines.append(line)
            lines.append("")

        return '\n'.join(lines)

    def _format_component_line(self, comp: LSPClass) -> str:
        """Format an Angular component for compact output"""
        parts = [comp.name]

        if comp.selector:
            parts.append(f"selector:{comp.selector}")

        # Inputs
        if comp.inputs:
            inputs = [i.name for i in comp.inputs]
            parts.append(f"@in:{','.join(inputs)}")

        # Outputs
        if comp.outputs:
            outputs = [o.name for o in comp.outputs]
            parts.append(f"@out:{','.join(outputs)}")

        # Injected dependencies
        if comp.injectables:
            parts.append(f"inject:[{','.join(comp.injectables)}]")

        return '|'.join(parts)

    def _format_service_line(self, svc: LSPClass) -> str:
        """Format an Angular service for compact output"""
        parts = [f"@Injectable class {svc.name}"]

        # Injected dependencies
        if svc.injectables:
            parts.append(f"inject:[{','.join(svc.injectables)}]")

        # Methods
        if svc.methods:
            methods = [m.name for m in svc.methods[:15]]
            if len(svc.methods) > 15:
                methods.append(f"+{len(svc.methods) - 15}more")
            parts.append(f"methods:[{','.join(methods)}]")

        return '|'.join(parts)

    def _format_store_line(self, store: LSPSignalStore) -> str:
        """Format an NgRx SignalStore for compact output"""
        parts = [f"signalStore {store.name}"]

        if store.features:
            parts.append(f"features:[{','.join(store.features)}]")

        if store.state:
            state_names = [s['name'] for s in store.state]
            parts.append(f"state:[{','.join(state_names)}]")

        if store.computed:
            computed = store.computed[:10]
            if len(store.computed) > 10:
                computed.append(f"+{len(store.computed) - 10}more")
            parts.append(f"computed:[{','.join(computed)}]")

        if store.methods:
            methods = store.methods[:10]
            if len(store.methods) > 10:
                methods.append(f"+{len(store.methods) - 10}more")
            parts.append(f"methods:[{','.join(methods)}]")

        return '|'.join(parts)

    def _format_interface_line(self, iface: LSPInterface) -> str:
        """Format a single interface for compact output"""
        parts = []

        if iface.exported:
            parts.append("export")

        name = f"interface {iface.name}"
        if iface.generics:
            name += f"<{','.join(iface.generics)}>"
        parts.append(name)

        if iface.extends:
            parts.append(f"extends:{','.join(iface.extends)}")

        # Format properties compactly
        if iface.properties:
            props = []
            for p in iface.properties[:15]:  # Limit for readability
                prop = f"{p.name}{'?' if p.optional else ''}:{p.type}"
                props.append(prop)
            if len(iface.properties) > 15:
                props.append(f"+{len(iface.properties) - 15}more")
            parts.append(f"props:[{','.join(props)}]")

        # Format methods compactly
        if iface.methods:
            methods = []
            for m in iface.methods[:10]:
                params = ','.join(f"{p['name']}:{p['type']}" for p in m.parameters)
                methods.append(f"{m.name}({params})=>{m.return_type}")
            if len(iface.methods) > 10:
                methods.append(f"+{len(iface.methods) - 10}more")
            parts.append(f"methods:[{','.join(methods)}]")

        return '|'.join(parts)

    def _format_type_line(self, type_alias: LSPTypeAlias) -> str:
        """Format a type alias for compact output"""
        parts = []

        if type_alias.exported:
            parts.append("export")

        parts.append(f"type {type_alias.name}")
        parts.append(f"kind:{type_alias.kind}")

        # Truncate very long definitions
        definition = type_alias.definition
        if len(definition) > 200:
            definition = definition[:197] + "..."
        parts.append(f"def:{definition}")

        return '|'.join(parts)

    def _format_class_line(self, cls: LSPClass) -> str:
        """Format a class for compact output"""
        parts = []

        # Decorators first (important for Angular)
        if cls.decorators:
            parts.append(f"@{','.join(cls.decorators)}")

        if cls.exported:
            parts.append("export")

        parts.append(f"class {cls.name}")

        if cls.extends:
            parts.append(f"extends:{cls.extends}")

        if cls.implements:
            parts.append(f"implements:{','.join(cls.implements)}")

        # Key properties
        if cls.properties:
            props = [p.name for p in cls.properties[:10]]
            if len(cls.properties) > 10:
                props.append(f"+{len(cls.properties) - 10}more")
            parts.append(f"props:[{','.join(props)}]")

        # Key methods
        if cls.methods:
            methods = [m.name for m in cls.methods[:10]]
            if len(cls.methods) > 10:
                methods.append(f"+{len(cls.methods) - 10}more")
            parts.append(f"methods:[{','.join(methods)}]")

        return '|'.join(parts)
