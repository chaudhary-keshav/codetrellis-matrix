"""
EnhancedGoParser v1.0 - Comprehensive Go parser using all extractors.

This parser integrates all Go extractors to provide complete
parsing of Go source files.

Supports:
- Core Go types (structs, interfaces, type aliases)
- Functions and methods with receivers
- Const blocks / iota enums
- Web frameworks (Gin, Echo, Chi, net/http)
- gRPC service implementations
- Package and import detection

Part of CodeTrellis v4.5 - Go Language Support (G-17)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Go extractors
from .extractors.go import (
    GoTypeExtractor, GoStructInfo, GoInterfaceInfo, GoTypeAliasInfo,
    GoFunctionExtractor, GoFunctionInfo, GoMethodInfo,
    GoEnumExtractor, GoConstBlockInfo,
    GoAPIExtractor, GoRouteInfo, GoGRPCServiceInfo,
)


@dataclass
class GoParseResult:
    """Complete parse result for a Go file."""
    file_path: str
    file_type: str = "go"

    # Package info
    package_name: str = ""

    # Core types
    structs: List[GoStructInfo] = field(default_factory=list)
    interfaces: List[GoInterfaceInfo] = field(default_factory=list)
    type_aliases: List[GoTypeAliasInfo] = field(default_factory=list)

    # Functions and methods
    functions: List[GoFunctionInfo] = field(default_factory=list)
    methods: List[GoMethodInfo] = field(default_factory=list)

    # Const blocks (Go enum equivalents)
    const_blocks: List[GoConstBlockInfo] = field(default_factory=list)

    # API/Framework elements
    routes: List[GoRouteInfo] = field(default_factory=list)
    grpc_services: List[GoGRPCServiceInfo] = field(default_factory=list)

    # Metadata
    imports: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)


class EnhancedGoParser:
    """
    Enhanced Go parser that uses all extractors for comprehensive parsing.

    Framework detection supports:
    - Gin (github.com/gin-gonic/gin)
    - Echo (github.com/labstack/echo)
    - Chi (github.com/go-chi/chi)
    - Gorilla Mux (github.com/gorilla/mux)
    - gRPC (google.golang.org/grpc)
    - GORM (gorm.io/gorm)
    - Cobra (github.com/spf13/cobra)
    - Viper (github.com/spf13/viper)
    """

    # Package declaration
    PACKAGE_PATTERN = re.compile(r'^package\s+(\w+)', re.MULTILINE)

    # Import block: import ( ... ) or import "path"
    IMPORT_BLOCK_PATTERN = re.compile(
        r'import\s*\(\s*((?:.*?\n)*?)\s*\)',
        re.MULTILINE
    )
    IMPORT_SINGLE_PATTERN = re.compile(
        r'^import\s+"([^"]+)"',
        re.MULTILINE
    )

    # Framework detection patterns (import paths)
    FRAMEWORK_PATTERNS = {
        'gin': re.compile(r'"github\.com/gin-gonic/gin"'),
        'echo': re.compile(r'"github\.com/labstack/echo'),
        'chi': re.compile(r'"github\.com/go-chi/chi'),
        'gorilla': re.compile(r'"github\.com/gorilla/mux"'),
        'grpc': re.compile(r'"google\.golang\.org/grpc"'),
        'gorm': re.compile(r'"gorm\.io/gorm"'),
        'cobra': re.compile(r'"github\.com/spf13/cobra"'),
        'viper': re.compile(r'"github\.com/spf13/viper"'),
        'fiber': re.compile(r'"github\.com/gofiber/fiber'),
        'protobuf': re.compile(r'"google\.golang\.org/protobuf'),
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = GoTypeExtractor()
        self.function_extractor = GoFunctionExtractor()
        self.enum_extractor = GoEnumExtractor()
        self.api_extractor = GoAPIExtractor()

    def parse(self, content: str, file_path: str = "") -> GoParseResult:
        """
        Parse Go source code and extract all information.

        Args:
            content: Go source code content
            file_path: Path to source file

        Returns:
            GoParseResult with all extracted information
        """
        result = GoParseResult(file_path=file_path)

        # Extract package name
        pkg_match = self.PACKAGE_PATTERN.search(content)
        if pkg_match:
            result.package_name = pkg_match.group(1)

        # Extract imports
        result.imports = self._extract_imports(content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Extract types (structs, interfaces, aliases)
        type_result = self.type_extractor.extract(content, file_path)
        result.structs = type_result.get('structs', [])
        result.interfaces = type_result.get('interfaces', [])
        result.type_aliases = type_result.get('type_aliases', [])

        # Extract functions and methods
        func_result = self.function_extractor.extract(content, file_path)
        result.functions = func_result.get('functions', [])
        result.methods = func_result.get('methods', [])

        # Extract const blocks (enums)
        result.const_blocks = self.enum_extractor.extract(content, file_path)

        # Extract API patterns
        api_result = self.api_extractor.extract(content, file_path)
        result.routes = api_result.get('routes', [])
        result.grpc_services = api_result.get('grpc_services', [])

        return result

    def _extract_imports(self, content: str) -> List[str]:
        """Extract import paths from Go file."""
        imports = []

        # Multi-import block
        for match in self.IMPORT_BLOCK_PATTERN.finditer(content):
            block = match.group(1)
            for line in block.split('\n'):
                line = line.strip()
                # Extract import path from: "path" or alias "path"
                import_match = re.search(r'"([^"]+)"', line)
                if import_match:
                    imports.append(import_match.group(1))

        # Single imports
        for match in self.IMPORT_SINGLE_PATTERN.finditer(content):
            imports.append(match.group(1))

        return imports

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Go frameworks are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks
