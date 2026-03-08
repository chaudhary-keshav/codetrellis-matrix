"""
CodeTrellis Interfaces Module
======================

This module defines all abstract base classes and protocols following
SOLID principles (specifically DIP and LSP).

All parsers, formatters, and validators must implement these interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# =============================================================================
# Enums
# =============================================================================

class FileType(Enum):
    """Type of file being parsed"""
    COMPONENT = "component"
    SERVICE = "service"
    STORE = "store"
    MODULE = "module"
    ROUTES = "routes"
    SCHEMA = "schema"
    DTO = "dto"
    CONTROLLER = "controller"
    PROTO = "proto"
    PYTHON = "python"
    GO = "go"
    JAVA = "java"
    KOTLIN = "kotlin"
    CSHARP = "csharp"
    RUST = "rust"
    SQL = "sql"
    HTML = "html"
    CSS = "css"  # v4.17: CSS/SCSS/Less/Stylus language support
    SASS = "sass"  # v4.44: Sass/SCSS language support (Dart Sass, LibSass, Ruby Sass)
    LESS = "less"  # v4.45: Less CSS language support (Less 1.x-4.x+)
    UNKNOWN = "unknown"


class CodeTrellisVersion(Enum):
    """CodeTrellis format version"""
    V1_0 = "1.0"
    V2_0 = "2.0"


class OutputTier(Enum):
    """
    Output compression tier - controls how much truncation is applied.

    COMPACT: Maximum compression, truncation allowed (legacy behavior)
             - Limits: 5 props, 8 methods, +Nmore suffix
             - Use case: Quick overview, minimal tokens

    PROMPT:  Balanced compression, NO truncation on important items
             - Full properties, methods, types
             - Use case: AI prompts requiring complete context

    FULL:    Complete extraction, NO truncation anywhere
             - Everything included with full detail
             - Use case: Documentation, complete reference

    JSON:    Machine-readable full export
             - Structured JSON output
             - Use case: Tooling integration, IDE plugins

    LOGIC:   Implementation details tier (NEW in v4.1)
             - Includes function bodies and logic summaries
             - Captures control flow, API calls, data transforms
             - Use case: AI needs to understand WHAT code does, not just signatures
             - Addresses: "AI can't see specific code logic" limitation
    """
    COMPACT = "compact"
    PROMPT = "prompt"
    FULL = "full"
    JSON = "json"
    LOGIC = "logic"


class PracticesFormat(Enum):
    """
    Output format for Best Practices Library (BPL) content.

    Controls verbosity level when including practices in CodeTrellis output.
    Enables token-efficient practice delivery based on context needs.

    MINIMAL:    Maximum compression - IDs and titles only
                - Format: practice_id|level|title
                - ~50% token reduction vs standard
                - Use case: Quick reference, token-constrained prompts
                - Ideal for: Large projects, iterative development

    STANDARD:   Balanced output - brief descriptions + truncated examples
                - Format: ID + title + first 150 chars + 3-line example
                - Default format for most use cases
                - Use case: Regular AI assistance, code generation
                - Ideal for: Most development workflows

    COMPREHENSIVE: Full detail - complete descriptions, all examples, references
                - Format: Everything - full descriptions, multiple examples
                - Complete practice content, anti-patterns, references
                - Use case: Learning, onboarding, documentation
                - Ideal for: New team members, best practice enforcement
    """
    MINIMAL = "minimal"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PropertyInfo:
    """Information about a property/field"""
    name: str
    type: str
    required: bool = True
    readonly: bool = False
    default: Optional[str] = None

    def to_string(self) -> str:
        """Convert to string representation"""
        result = f"{self.name}:{self.type}"
        if not self.required:
            result = f"{self.name}?:{self.type}"
        if self.readonly:
            result += "|readonly"
        if self.default is not None:
            result += f"={self.default}"
        return result


@dataclass
class InterfaceInfo:
    """Parsed interface information"""
    name: str
    properties: List[PropertyInfo] = field(default_factory=list)
    extends: Optional[str] = None
    generic_params: List[str] = field(default_factory=list)

    def to_string(self) -> str:
        """Convert to string representation"""
        props = ",".join(p.to_string() for p in self.properties)
        result = f"{self.name}"
        if self.generic_params:
            result += f"<{','.join(self.generic_params)}>"
        if self.extends:
            result += f" extends {self.extends}"
        result += f"{{{props}}}"
        return result


@dataclass
class TypeAliasInfo:
    """Parsed type alias information"""
    name: str
    definition: str
    generic_params: List[str] = field(default_factory=list)

    def to_string(self) -> str:
        """Convert to string representation"""
        if self.generic_params:
            return f"{self.name}<{','.join(self.generic_params)}>={self.definition}"
        return f"{self.name}={self.definition}"


@dataclass
class SignalInfo:
    """Parsed signal information"""
    name: str
    type: str
    initial_value: Optional[str] = None
    is_computed: bool = False
    dependencies: List[str] = field(default_factory=list)

    def to_string(self) -> str:
        """Convert to string representation"""
        if self.is_computed:
            deps = ",".join(self.dependencies) if self.dependencies else "..."
            return f"{self.name}=computed({deps})"
        result = f"{self.name}:{self.type}"
        if self.initial_value is not None:
            result += f"={self.initial_value}"
        return result


@dataclass
class MethodInfo:
    """Parsed method information"""
    name: str
    params: List[PropertyInfo] = field(default_factory=list)
    return_type: str = "void"
    is_async: bool = False

    def to_string(self) -> str:
        """Convert to string representation"""
        params = ",".join(f"{p.name}:{p.type}" for p in self.params)
        prefix = "async " if self.is_async else ""
        return f"{prefix}{self.name}({params}):{self.return_type}"


@dataclass
class InputInfo:
    """Parsed input binding information"""
    name: str
    type: str
    required: bool = False
    default: Optional[str] = None
    transform: Optional[str] = None

    def to_string(self) -> str:
        """Convert to string representation"""
        result = f"{self.name}:{self.type}"
        if self.required:
            result += "=required"
        elif self.default is not None:
            result += f"={self.default}"
        if self.transform:
            result += f"|transform:{self.transform}"
        return result


@dataclass
class OutputInfo:
    """Parsed output event information"""
    name: str
    event_type: str

    def to_string(self) -> str:
        """Convert to string representation"""
        return f"{self.name}:{self.event_type}"


@dataclass
class RouteInfo:
    """Parsed route information"""
    path: str
    component: Optional[str] = None
    redirect: Optional[str] = None
    params: List[str] = field(default_factory=list)
    guards: List[str] = field(default_factory=list)
    children: List['RouteInfo'] = field(default_factory=list)
    lazy_path: Optional[str] = None

    def to_string(self, indent: int = 0) -> str:
        """Convert to string representation"""
        prefix = "  " * indent

        if self.redirect:
            return f"{prefix}/{self.path}→redirect:{self.redirect}"

        result = f"{prefix}/{self.path}→"

        if self.lazy_path:
            result += f"lazy:{self.lazy_path}"
        elif self.component:
            result += self.component

        if self.params:
            result += f"|params:{','.join(self.params)}"
        if self.guards:
            result += f"|guards:{','.join(self.guards)}"
        if self.children:
            result += "|children"
            for child in self.children:
                result += "\n" + child.to_string(indent + 1)

        return result


@dataclass
class WebSocketEventInfo:
    """Parsed WebSocket event information"""
    name: str
    direction: str  # 'IN' or 'OUT'
    payload_type: Optional[str] = None
    handler: Optional[str] = None

    def to_string(self) -> str:
        """Convert to string representation"""
        result = self.name
        if self.payload_type:
            result += f":{self.payload_type}"
        if self.handler:
            result += f"→{self.handler}"
        return result


@dataclass
class APIEndpointInfo:
    """Parsed HTTP API endpoint information"""
    method: str  # GET, POST, PUT, DELETE
    url: str
    response_type: Optional[str] = None
    handler: Optional[str] = None

    def to_string(self) -> str:
        """Convert to string representation"""
        result = f"{self.method}:{self.url}"
        if self.response_type:
            result += f"→{self.response_type}"
        return result


@dataclass
class ParseResult:
    """
    Result of parsing a single file.
    Contains all extracted information.
    """
    file_path: str
    file_type: FileType
    name: str  # Component/Service/Store name
    version: CodeTrellisVersion = CodeTrellisVersion.V2_0

    # Features/flags
    features: List[str] = field(default_factory=list)  # ['standalone', 'OnPush', 'signals']

    # Angular component specific
    selector: Optional[str] = None
    inputs: List[InputInfo] = field(default_factory=list)
    outputs: List[OutputInfo] = field(default_factory=list)

    # Signals (Angular 17+)
    signals: List[SignalInfo] = field(default_factory=list)
    computed: List[SignalInfo] = field(default_factory=list)

    # SignalStore specific
    state_properties: List[PropertyInfo] = field(default_factory=list)
    store_computed: List[SignalInfo] = field(default_factory=list)
    store_methods: List[MethodInfo] = field(default_factory=list)

    # Common
    interfaces: List[InterfaceInfo] = field(default_factory=list)
    type_aliases: List[TypeAliasInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    # Routes (only for routes files)
    routes: List[RouteInfo] = field(default_factory=list)

    # WebSocket events
    ws_events_in: List[WebSocketEventInfo] = field(default_factory=list)
    ws_events_out: List[WebSocketEventInfo] = field(default_factory=list)

    # HTTP API endpoints
    api_endpoints: List[APIEndpointInfo] = field(default_factory=list)

    # NestJS specific
    controller_prefix: Optional[str] = None
    schema_collection: Optional[str] = None

    # Metadata
    raw_content_hash: Optional[str] = None

    def has_content(self) -> bool:
        """Check if parse result has any meaningful content"""
        return any([
            self.inputs, self.outputs, self.signals, self.computed,
            self.state_properties, self.store_computed, self.store_methods,
            self.interfaces, self.type_aliases, self.methods, self.dependencies,
            self.routes, self.ws_events_in, self.ws_events_out, self.api_endpoints
        ])


@dataclass
class ValidationResult:
    """Result of validating a .codetrellis file"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str):
        """Add an error message"""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)


# =============================================================================
# Protocols (Interfaces)
# =============================================================================

@runtime_checkable
class IParser(Protocol):
    """
    Interface for all file parsers.

    Parsers are responsible for extracting structured information
    from source files. Each parser handles specific file types.

    Following ISP: This is the minimal interface all parsers must implement.
    """

    def can_parse(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file.

        Args:
            file_path: Path to the file

        Returns:
            True if this parser can parse the file
        """
        ...

    def parse(self, file_path: Path, content: str) -> ParseResult:
        """
        Parse the file content and extract structured information.

        Args:
            file_path: Path to the file
            content: File content as string

        Returns:
            ParseResult with all extracted information
        """
        ...


@runtime_checkable
class IExtractor(Protocol):
    """
    Interface for specialized extractors.

    Extractors are responsible for extracting specific types of
    information (interfaces, types, signals, etc.) from content.

    Extractors are used by parsers to delegate specific extraction tasks.
    """

    def extract(self, content: str) -> List[Any]:
        """
        Extract specific information from content.

        Args:
            content: Source code content

        Returns:
            List of extracted items
        """
        ...


@runtime_checkable
class IFormatter(Protocol):
    """
    Interface for output formatters.

    Formatters convert ParseResult objects into string output
    in a specific format (V1.0, V2.0, JSON, etc.)
    """

    @property
    def version(self) -> CodeTrellisVersion:
        """Get the format version this formatter produces"""
        ...

    def format(self, result: ParseResult) -> str:
        """
        Format a parse result into string output.

        Args:
            result: ParseResult to format

        Returns:
            Formatted string
        """
        ...

    def format_multiple(self, results: List[ParseResult]) -> str:
        """
        Format multiple parse results into single output.

        Args:
            results: List of ParseResult objects

        Returns:
            Formatted string
        """
        ...


@runtime_checkable
class IValidator(Protocol):
    """
    Interface for validators.

    Validators check .codetrellis files for correctness and completeness.
    """

    def validate(self, content: str) -> ValidationResult:
        """
        Validate .codetrellis content.

        Args:
            content: Content of .codetrellis file

        Returns:
            ValidationResult with any errors/warnings
        """
        ...

    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate a .codetrellis file.

        Args:
            file_path: Path to .codetrellis file

        Returns:
            ValidationResult with any errors/warnings
        """
        ...


@runtime_checkable
class IParserRegistry(Protocol):
    """
    Interface for parser registry.

    The registry manages parser registration and selection.
    Following OCP: New parsers can be added without modifying existing code.
    """

    def register(self, parser: IParser) -> None:
        """
        Register a parser.

        Args:
            parser: Parser instance to register
        """
        ...

    def get_parser(self, file_path: Path) -> Optional[IParser]:
        """
        Get appropriate parser for a file.

        Args:
            file_path: Path to the file

        Returns:
            Parser that can handle the file, or None
        """
        ...

    def get_all_parsers(self) -> List[IParser]:
        """
        Get all registered parsers.

        Returns:
            List of all registered parsers
        """
        ...


# =============================================================================
# Abstract Base Classes
# =============================================================================

class BaseParser(ABC):
    """
    Abstract base class for parsers.

    Provides common functionality for all parsers.
    Subclasses must implement can_parse() and parse().
    """

    def __init__(self):
        self._extractors: Dict[str, IExtractor] = {}

    def register_extractor(self, name: str, extractor: IExtractor) -> None:
        """Register an extractor for use by this parser"""
        self._extractors[name] = extractor

    def get_extractor(self, name: str) -> Optional[IExtractor]:
        """Get a registered extractor by name"""
        return self._extractors.get(name)

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the file"""
        pass

    @abstractmethod
    def parse(self, file_path: Path, content: str) -> ParseResult:
        """Parse file content"""
        pass

    def _create_empty_result(self, file_path: Path, file_type: FileType) -> ParseResult:
        """Create an empty parse result"""
        return ParseResult(
            file_path=str(file_path),
            file_type=file_type,
            name=file_path.stem
        )


class BaseExtractor(ABC):
    """
    Abstract base class for extractors.

    Provides common regex-based extraction utilities.
    """

    @abstractmethod
    def extract(self, content: str) -> List[Any]:
        """Extract information from content"""
        pass

    def _extract_class_body(self, content: str, class_name: str) -> Optional[str]:
        """
        Extract the body of a class by matching braces.

        Args:
            content: Full file content
            class_name: Name of the class to extract

        Returns:
            Class body content or None if not found
        """
        import re

        # Find class declaration
        pattern = rf'class\s+{re.escape(class_name)}\s*(?:extends\s+\w+)?\s*(?:implements\s+[\w,\s]+)?\s*\{{'
        match = re.search(pattern, content)

        if not match:
            return None

        # Find matching closing brace
        start = match.end() - 1  # Position of opening brace
        brace_count = 1
        pos = start + 1

        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1

        if brace_count == 0:
            return content[start + 1:pos - 1]

        return None


class BaseFormatter(ABC):
    """
    Abstract base class for formatters.

    Provides common formatting utilities.
    """

    @property
    @abstractmethod
    def version(self) -> CodeTrellisVersion:
        """Get the format version"""
        pass

    @abstractmethod
    def format(self, result: ParseResult) -> str:
        """Format a single parse result"""
        pass

    def format_multiple(self, results: List[ParseResult]) -> str:
        """Format multiple parse results"""
        return "\n\n".join(self.format(r) for r in results if r.has_content())

    def _format_section(self, title: str, items: List[str]) -> str:
        """Format a section with title and items"""
        if not items:
            return ""
        return f"[{title}]\n" + "\n".join(items)


# =============================================================================
# Registry Implementation
# =============================================================================

class ParserRegistry:
    """
    Registry for managing parsers.

    Implements IParserRegistry following the plugin pattern.
    New parsers can be registered at runtime.
    """

    def __init__(self):
        self._parsers: List[IParser] = []

    def register(self, parser: IParser) -> None:
        """Register a parser"""
        if parser not in self._parsers:
            self._parsers.append(parser)

    def get_parser(self, file_path: Path) -> Optional[IParser]:
        """Get the first parser that can handle the file"""
        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser
        return None

    def get_all_parsers(self) -> List[IParser]:
        """Get all registered parsers"""
        return list(self._parsers)

    def clear(self) -> None:
        """Clear all registered parsers"""
        self._parsers.clear()


# =============================================================================
# Build Pipeline Interfaces (B3 — Auto-Compilation Architecture)
# =============================================================================

@dataclass
class ExtractorManifest:
    """Declares an extractor's identity and dependencies for the DAG scheduler.

    Per B3.2: Each extractor declares its name, version, the file patterns
    it operates on, and what other extractors it depends on.
    """
    name: str
    version: str
    input_patterns: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    output_sections: List[str] = field(default_factory=list)


@runtime_checkable
class IExtractor(Protocol):
    """Protocol for all extractors in the build pipeline.

    Per B3.2 and B4 Phase 1: Every extractor must implement this interface
    so the MatrixBuilder can schedule, cache, and incrementally re-run them.

    Methods:
        manifest: Returns extractor identity and dependency info
        cache_key: Returns a stable hash key for the given file
        extract: Runs extraction on a single file, returning a dict of results
    """

    @property
    def manifest(self) -> ExtractorManifest:
        """Return the extractor's manifest (name, version, patterns, deps)."""
        ...

    def cache_key(self, file_path: str, file_content_hash: str) -> str:
        """Compute a deterministic cache key for a file.

        Args:
            file_path: Absolute path to the file
            file_content_hash: SHA-256 hex digest (first 16 chars) of file content

        Returns:
            A string key unique to this extractor + file + content
        """
        ...

    def extract(self, file_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from a single file.

        Args:
            file_path: Absolute path to the file
            context: Shared context dict (project root, config, prior results)

        Returns:
            Dict with extracted data, keyed by output section names
        """
        ...


@dataclass
class BuildEvent:
    """Structured build log event for _build_log.jsonl.

    Per C2.2: Each line in the build log captures timing, level, and extractor info.
    """
    timestamp: str
    level: str  # "info", "warn", "error", "debug"
    event: str  # "start", "complete", "cache_hit", "cache_miss", "error", "skip"
    extractor: str = ""
    file: str = ""
    duration_ms: float = 0.0
    message: str = ""

    def to_json(self) -> str:
        """Serialize to a single JSON line."""
        import json
        return json.dumps({
            "timestamp": self.timestamp,
            "level": self.level,
            "event": self.event,
            "extractor": self.extractor,
            "file": self.file,
            "duration_ms": round(self.duration_ms, 2),
            "message": self.message,
        }, sort_keys=True)


@dataclass
class BuildResult:
    """Result of a MatrixBuilder build operation.

    Per C2.1-C2.2 and D1: Captures all outputs and gate results.
    """
    success: bool
    exit_code: int  # 0=success, 1=partial, 2=config error, 3=fatal
    matrix_json_path: Optional[str] = None
    matrix_prompt_path: Optional[str] = None
    metadata_path: Optional[str] = None
    lockfile_path: Optional[str] = None
    build_log_path: Optional[str] = None
    total_files: int = 0
    extractors_run: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
