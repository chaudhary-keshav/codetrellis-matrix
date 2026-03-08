"""
CodeTrellis Plugin System - Base Interfaces
====================================

Defines the core interfaces and protocols for the plugin system.

Following SOLID principles:
- Single Responsibility: Each interface has one purpose
- Open/Closed: Extensible through plugins without modifying core
- Liskov Substitution: All plugins can be used interchangeably
- Interface Segregation: Small, focused interfaces
- Dependency Inversion: Depend on abstractions, not concretions
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, Type


# =============================================================================
# Enums
# =============================================================================

class PluginCapability(Enum):
    """Capabilities that a plugin can provide"""
    # Code Structure
    INTERFACES = auto()          # TypeScript/Java interfaces
    TYPES = auto()               # Type aliases
    CLASSES = auto()             # Class definitions
    FUNCTIONS = auto()           # Function definitions
    ENUMS = auto()               # Enum definitions

    # Framework Specific
    COMPONENTS = auto()          # UI components (Angular, React, Vue)
    SERVICES = auto()            # Injectable services
    STORES = auto()              # State management (NgRx, Redux, Pinia)
    ROUTES = auto()              # Routing configuration
    MODULES = auto()             # Module definitions

    # API & Communication
    HTTP_API = auto()            # HTTP client calls
    WEBSOCKET = auto()           # WebSocket events
    GRPC = auto()                # gRPC services
    GRAPHQL = auto()             # GraphQL queries/mutations

    # Documentation & Meta
    JSDOC = auto()               # JSDoc comments
    DOCSTRINGS = auto()          # Python docstrings
    README = auto()              # README extraction
    CONFIG = auto()              # Config file parsing

    # Code Quality
    ERRORS = auto()              # Error handling patterns
    TODOS = auto()               # TODO/FIXME comments
    TESTS = auto()               # Test file analysis


class PluginType(Enum):
    """Type of plugin"""
    LANGUAGE = "language"        # Language support (TypeScript, Python, etc.)
    FRAMEWORK = "framework"      # Framework support (Angular, NestJS, etc.)
    EXTRACTOR = "extractor"      # Specialized extractor
    FORMATTER = "formatter"      # Output formatter


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PluginMetadata:
    """Metadata about a plugin"""
    name: str
    version: str
    description: str
    author: str = "CodeTrellis Team"
    homepage: str = ""
    plugin_type: PluginType = PluginType.FRAMEWORK
    capabilities: List[PluginCapability] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Other plugins required
    file_extensions: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)  # Files that indicate this framework

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'homepage': self.homepage,
            'type': self.plugin_type.value,
            'capabilities': [c.name for c in self.capabilities],
            'dependencies': self.dependencies,
            'file_extensions': self.file_extensions,
            'config_files': self.config_files,
        }


@dataclass
class ExtractorResult:
    """Result from an extractor"""
    extractor_name: str
    file_path: str
    success: bool = True
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_codetrellis_format(self) -> str:
        """Convert to CodeTrellis output format"""
        if not self.success:
            return f"# {self.extractor_name} - FAILED: {', '.join(self.errors)}"

        lines = []
        for key, value in self.data.items():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, 'to_codetrellis_format'):
                        lines.append(item.to_codetrellis_format())
                    else:
                        lines.append(str(item))
            elif hasattr(value, 'to_codetrellis_format'):
                lines.append(value.to_codetrellis_format())
            else:
                lines.append(f"{key}: {value}")

        return "\n".join(lines)


@dataclass
class PluginConfig:
    """Configuration for a plugin"""
    enabled: bool = True
    options: Dict[str, Any] = field(default_factory=dict)
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)


# =============================================================================
# Protocols (Interfaces)
# =============================================================================

@runtime_checkable
class IExtractor(Protocol):
    """
    Protocol for extractors.

    An extractor is responsible for extracting specific information
    from source code files.
    """

    @property
    def name(self) -> str:
        """Unique name of the extractor"""
        ...

    @property
    def capabilities(self) -> List[PluginCapability]:
        """What this extractor can extract"""
        ...

    def can_extract(self, file_path: Path, content: str) -> bool:
        """Check if this extractor can handle the file"""
        ...

    def extract(self, file_path: Path, content: str) -> ExtractorResult:
        """Extract information from the file"""
        ...


@runtime_checkable
class ILanguagePlugin(Protocol):
    """
    Protocol for language plugins.

    A language plugin provides basic language support (parsing, AST, etc.)
    that framework plugins can build upon.
    """

    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata"""
        ...

    @property
    def file_extensions(self) -> List[str]:
        """File extensions this plugin handles"""
        ...

    def can_parse(self, file_path: Path) -> bool:
        """Check if this plugin can parse the file"""
        ...

    def parse(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Parse file and return AST or parsed data"""
        ...

    def get_extractors(self) -> List[Type[IExtractor]]:
        """Get extractors provided by this plugin"""
        ...


@runtime_checkable
class IFrameworkPlugin(Protocol):
    """
    Protocol for framework plugins.

    A framework plugin provides support for a specific framework
    (Angular, React, NestJS, FastAPI, etc.)
    """

    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata"""
        ...

    @property
    def language_plugin(self) -> str:
        """Name of the required language plugin"""
        ...

    def detect_project(self, project_path: Path) -> bool:
        """Check if a project uses this framework"""
        ...

    def get_file_patterns(self) -> List[str]:
        """Get glob patterns for files this plugin handles"""
        ...

    def get_extractors(self) -> List[Type[IExtractor]]:
        """Get extractors provided by this plugin"""
        ...

    def get_output_sections(self) -> List[str]:
        """Get output section names this plugin produces"""
        ...


# =============================================================================
# Abstract Base Classes
# =============================================================================

class BaseExtractor(ABC):
    """
    Abstract base class for extractors.

    Provides common functionality for all extractors.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the extractor"""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[PluginCapability]:
        """What this extractor can extract"""
        pass

    @abstractmethod
    def can_extract(self, file_path: Path, content: str) -> bool:
        """Check if this extractor can handle the file"""
        pass

    @abstractmethod
    def extract(self, file_path: Path, content: str) -> ExtractorResult:
        """Extract information from the file"""
        pass

    def _create_result(
        self,
        file_path: Path,
        success: bool = True,
        data: Dict[str, Any] = None,
        errors: List[str] = None,
        warnings: List[str] = None
    ) -> ExtractorResult:
        """Helper to create ExtractorResult"""
        return ExtractorResult(
            extractor_name=self.name,
            file_path=str(file_path),
            success=success,
            data=data or {},
            errors=errors or [],
            warnings=warnings or []
        )


class BaseLanguagePlugin(ABC):
    """
    Abstract base class for language plugins.
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata"""
        pass

    @property
    @abstractmethod
    def file_extensions(self) -> List[str]:
        """File extensions this plugin handles"""
        pass

    def can_parse(self, file_path: Path) -> bool:
        """Check if this plugin can parse the file"""
        return file_path.suffix in self.file_extensions

    @abstractmethod
    def parse(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Parse file and return AST or parsed data"""
        pass

    @abstractmethod
    def get_extractors(self) -> List[Type[IExtractor]]:
        """Get extractors provided by this plugin"""
        pass


class BaseFrameworkPlugin(ABC):
    """
    Abstract base class for framework plugins.
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata"""
        pass

    @property
    @abstractmethod
    def language_plugin(self) -> str:
        """Name of the required language plugin"""
        pass

    @abstractmethod
    def detect_project(self, project_path: Path) -> bool:
        """Check if a project uses this framework"""
        pass

    @abstractmethod
    def get_file_patterns(self) -> List[str]:
        """Get glob patterns for files this plugin handles"""
        pass

    @abstractmethod
    def get_extractors(self) -> List[Type[IExtractor]]:
        """Get extractors provided by this plugin"""
        pass

    @abstractmethod
    def get_output_sections(self) -> List[str]:
        """Get output section names this plugin produces"""
        pass

    def _check_config_file(self, project_path: Path, config_file: str) -> bool:
        """Helper to check if a config file exists"""
        return (project_path / config_file).exists()

    def _check_package_json_dependency(
        self,
        project_path: Path,
        package_name: str
    ) -> bool:
        """Helper to check if a package is in package.json dependencies"""
        import json

        package_json = project_path / 'package.json'
        if not package_json.exists():
            return False

        try:
            data = json.loads(package_json.read_text())
            deps = data.get('dependencies', {})
            dev_deps = data.get('devDependencies', {})
            return package_name in deps or package_name in dev_deps
        except (json.JSONDecodeError, IOError):
            return False
