"""
LSP Client for TypeScript Type Extraction

This module provides a Python interface to the TypeScript LSP bridge.
It spawns the Node.js extraction script and parses the results.
"""

import subprocess
import json
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


@dataclass
class LSPProperty:
    """Property extracted via LSP"""
    name: str
    type: str
    optional: bool = False
    readonly: bool = False
    documentation: Optional[str] = None


@dataclass
class LSPMethod:
    """Method extracted via LSP"""
    name: str
    parameters: list[dict]  # [{name, type, optional}]
    return_type: str
    documentation: Optional[str] = None


@dataclass
class LSPInterface:
    """Interface extracted via LSP"""
    name: str
    file_path: str
    exported: bool
    properties: list[LSPProperty] = field(default_factory=list)
    methods: list[LSPMethod] = field(default_factory=list)
    extends: list[str] = field(default_factory=list)
    generics: list[str] = field(default_factory=list)
    documentation: Optional[str] = None


@dataclass
class LSPTypeAlias:
    """Type alias extracted via LSP"""
    name: str
    file_path: str
    exported: bool
    definition: str
    kind: str  # union, intersection, object, function, primitive, generic
    documentation: Optional[str] = None


@dataclass
class LSPInputSignal:
    """Angular input signal extracted via LSP"""
    name: str
    type: str
    required: bool = False
    alias: Optional[str] = None


@dataclass
class LSPOutputSignal:
    """Angular output signal extracted via LSP"""
    name: str
    type: str
    alias: Optional[str] = None


@dataclass
class LSPClass:
    """Class extracted via LSP"""
    name: str
    file_path: str
    exported: bool
    properties: list[LSPProperty] = field(default_factory=list)
    methods: list[LSPMethod] = field(default_factory=list)
    extends: Optional[str] = None
    implements: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    documentation: Optional[str] = None
    # Angular-specific fields
    is_component: bool = False
    is_service: bool = False
    is_directive: bool = False
    is_pipe: bool = False
    selector: Optional[str] = None
    inputs: list[LSPInputSignal] = field(default_factory=list)
    outputs: list[LSPOutputSignal] = field(default_factory=list)
    injectables: list[str] = field(default_factory=list)


@dataclass
class LSPSignalStore:
    """NgRx SignalStore extracted via LSP"""
    name: str
    file_path: str
    features: list[str] = field(default_factory=list)
    state: list[dict] = field(default_factory=list)  # [{name, type}]
    computed: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)


@dataclass
class LSPExtractionResult:
    """Complete LSP extraction result"""
    project_path: str
    interfaces: list[LSPInterface] = field(default_factory=list)
    types: list[LSPTypeAlias] = field(default_factory=list)
    classes: list[LSPClass] = field(default_factory=list)
    stores: list[LSPSignalStore] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    files_processed: int = 0
    components_found: int = 0
    services_found: int = 0
    stores_found: int = 0
    processing_time_ms: int = 0
    success: bool = False
    fallback_reason: Optional[str] = None


class LSPClient:
    """
    Client for extracting TypeScript types using the LSP bridge.

    Falls back gracefully if Node.js is not available.
    """

    def __init__(self):
        self._lsp_dir = Path(__file__).parent.parent / 'lsp'
        self._extract_script = self._lsp_dir / 'extract-types.ts'
        self._node_available: Optional[bool] = None
        self._npm_installed: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if LSP extraction is available (Node.js installed)"""
        if self._node_available is None:
            self._node_available = shutil.which('node') is not None
        return self._node_available

    def _ensure_dependencies(self) -> bool:
        """Ensure npm dependencies are installed"""
        if self._npm_installed:
            return True

        node_modules = self._lsp_dir / 'node_modules'
        if node_modules.exists():
            self._npm_installed = True
            return True

        logger.info("Installing LSP bridge dependencies...")
        try:
            result = subprocess.run(
                ['npm', 'install'],
                cwd=self._lsp_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                self._npm_installed = True
                logger.info("LSP dependencies installed successfully")
                return True
            else:
                logger.warning(f"npm install failed: {result.stderr}")
                return False
        except Exception as e:
            logger.warning(f"Failed to install LSP dependencies: {e}")
            return False

    def extract(self, project_path: Union[str, Path], timeout: int = 120) -> LSPExtractionResult:
        """
        Extract types from a TypeScript project using the LSP bridge.

        Args:
            project_path: Path to the TypeScript project (must have tsconfig.json)
            timeout: Maximum seconds to wait for extraction

        Returns:
            LSPExtractionResult with all extracted types
        """
        project_path = Path(project_path).resolve()
        result = LSPExtractionResult(project_path=str(project_path))

        # Check if Node.js is available
        if not self.is_available():
            result.fallback_reason = "Node.js is not installed"
            logger.warning("LSP extraction unavailable: Node.js not found")
            return result

        # Check if tsconfig.json exists
        tsconfig = project_path / 'tsconfig.json'
        if not tsconfig.exists():
            result.fallback_reason = f"No tsconfig.json found at {project_path}"
            logger.warning(f"LSP extraction unavailable: {result.fallback_reason}")
            return result

        # Ensure dependencies
        if not self._ensure_dependencies():
            result.fallback_reason = "Failed to install LSP dependencies"
            return result

        # Run the extraction script
        try:
            logger.info(f"Running LSP extraction on {project_path}")

            proc_result = subprocess.run(
                ['npx', 'ts-node', str(self._extract_script), str(project_path)],
                cwd=self._lsp_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if proc_result.returncode != 0:
                result.fallback_reason = f"Extraction script failed: {proc_result.stderr[:500]}"
                result.errors.append(proc_result.stderr)
                logger.error(f"LSP extraction failed: {proc_result.stderr[:200]}")
                return result

            # Parse JSON output
            data = json.loads(proc_result.stdout)
            return self._parse_result(data)

        except subprocess.TimeoutExpired:
            result.fallback_reason = f"Extraction timed out after {timeout}s"
            logger.error("LSP extraction timed out")
            return result
        except json.JSONDecodeError as e:
            result.fallback_reason = f"Failed to parse extraction output: {e}"
            logger.error(f"LSP output parse error: {e}")
            return result
        except Exception as e:
            result.fallback_reason = f"Extraction error: {e}"
            logger.error(f"LSP extraction error: {e}")
            return result

    def _parse_result(self, data: dict) -> LSPExtractionResult:
        """Parse JSON extraction result into dataclasses"""
        stats = data.get('stats', {})
        result = LSPExtractionResult(
            project_path=data.get('projectPath', ''),
            errors=data.get('errors', []),
            files_processed=stats.get('filesProcessed', 0),
            components_found=stats.get('componentsFound', 0),
            services_found=stats.get('servicesFound', 0),
            stores_found=stats.get('storesFound', 0),
            processing_time_ms=stats.get('processingTimeMs', 0),
            success=True
        )

        # Parse interfaces
        for iface_data in data.get('interfaces', []):
            iface = LSPInterface(
                name=iface_data['name'],
                file_path=iface_data['filePath'],
                exported=iface_data['exported'],
                extends=iface_data.get('extends', []),
                generics=iface_data.get('generics', []),
                documentation=iface_data.get('documentation'),
            )

            for prop_data in iface_data.get('properties', []):
                iface.properties.append(LSPProperty(
                    name=prop_data['name'],
                    type=prop_data['type'],
                    optional=prop_data.get('optional', False),
                    readonly=prop_data.get('readonly', False),
                ))

            for method_data in iface_data.get('methods', []):
                iface.methods.append(LSPMethod(
                    name=method_data['name'],
                    parameters=method_data.get('parameters', []),
                    return_type=method_data.get('returnType', 'void'),
                ))

            result.interfaces.append(iface)

        # Parse type aliases
        for type_data in data.get('types', []):
            result.types.append(LSPTypeAlias(
                name=type_data['name'],
                file_path=type_data['filePath'],
                exported=type_data['exported'],
                definition=type_data['definition'],
                kind=type_data['kind'],
                documentation=type_data.get('documentation'),
            ))

        # Parse classes
        for class_data in data.get('classes', []):
            cls = LSPClass(
                name=class_data['name'],
                file_path=class_data['filePath'],
                exported=class_data['exported'],
                extends=class_data.get('extends'),
                implements=class_data.get('implements', []),
                decorators=class_data.get('decorators', []),
                documentation=class_data.get('documentation'),
                # Angular-specific fields
                is_component=class_data.get('isComponent', False),
                is_service=class_data.get('isService', False),
                is_directive=class_data.get('isDirective', False),
                is_pipe=class_data.get('isPipe', False),
                selector=class_data.get('selector'),
                injectables=class_data.get('injectables', []),
            )

            # Parse properties
            for prop_data in class_data.get('properties', []):
                cls.properties.append(LSPProperty(
                    name=prop_data['name'],
                    type=prop_data['type'],
                    optional=prop_data.get('optional', False),
                    readonly=prop_data.get('readonly', False),
                ))

            # Parse methods
            for method_data in class_data.get('methods', []):
                cls.methods.append(LSPMethod(
                    name=method_data['name'],
                    parameters=method_data.get('parameters', []),
                    return_type=method_data.get('returnType', 'void'),
                ))

            # Parse Angular inputs
            for input_data in class_data.get('inputs', []):
                cls.inputs.append(LSPInputSignal(
                    name=input_data['name'],
                    type=input_data['type'],
                    required=input_data.get('required', False),
                    alias=input_data.get('alias'),
                ))

            # Parse Angular outputs
            for output_data in class_data.get('outputs', []):
                cls.outputs.append(LSPOutputSignal(
                    name=output_data['name'],
                    type=output_data['type'],
                    alias=output_data.get('alias'),
                ))

            result.classes.append(cls)

        # Parse SignalStores
        for store_data in data.get('stores', []):
            store = LSPSignalStore(
                name=store_data['name'],
                file_path=store_data['filePath'],
                features=store_data.get('features', []),
                state=store_data.get('state', []),
                computed=store_data.get('computed', []),
                methods=store_data.get('methods', []),
            )
            result.stores.append(store)

        return result


# Singleton instance
_client: Optional[LSPClient] = None


def get_lsp_client() -> LSPClient:
    """Get or create the LSP client singleton"""
    global _client
    if _client is None:
        _client = LSPClient()
    return _client


def extract_types(project_path: Union[str, Path]) -> LSPExtractionResult:
    """Convenience function to extract types from a project"""
    return get_lsp_client().extract(project_path)


def is_lsp_available() -> bool:
    """Check if LSP extraction is available"""
    return get_lsp_client().is_available()
