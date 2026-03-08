"""
EnhancedRustParser v1.0 - Comprehensive Rust parser using all extractors.

This parser integrates all Rust extractors to provide complete
parsing of Rust source files.

Supports:
- Core Rust types (structs, enums, traits, type aliases, impl blocks)
- Functions and methods with async/unsafe/const qualifiers
- Web frameworks (actix-web, Rocket, Axum, Warp, Tide)
- gRPC (Tonic) and GraphQL (async-graphql)
- Database models (Diesel, SeaORM, SQLx)
- Derive macros, proc macros, cfg attributes, feature flags
- Module and use declarations
- Crate dependency detection from Cargo.toml

Part of CodeTrellis v4.14 - Rust Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Rust extractors
from .extractors.rust import (
    RustTypeExtractor, RustStructInfo, RustEnumInfo, RustTraitInfo,
    RustTypeAliasInfo, RustImplInfo,
    RustFunctionExtractor, RustFunctionInfo, RustMethodInfo,
    RustAPIExtractor, RustRouteInfo, RustGRPCServiceInfo, RustGraphQLInfo,
    RustModelExtractor, RustModelInfo, RustSchemaInfo,
    RustAttributeExtractor, RustDeriveInfo, RustFeatureFlagInfo,
    RustMacroUsageInfo, RustCrateAttributeInfo,
)


@dataclass
class RustParseResult:
    """Complete parse result for a Rust file."""
    file_path: str
    file_type: str = "rust"

    # Module info
    module_name: str = ""
    crate_name: str = ""

    # Core types
    structs: List[RustStructInfo] = field(default_factory=list)
    enums: List[RustEnumInfo] = field(default_factory=list)
    traits: List[RustTraitInfo] = field(default_factory=list)
    type_aliases: List[RustTypeAliasInfo] = field(default_factory=list)
    impls: List[RustImplInfo] = field(default_factory=list)

    # Functions and methods
    functions: List[RustFunctionInfo] = field(default_factory=list)
    methods: List[RustMethodInfo] = field(default_factory=list)

    # API/Framework elements
    routes: List[RustRouteInfo] = field(default_factory=list)
    grpc_services: List[RustGRPCServiceInfo] = field(default_factory=list)
    graphql_types: List[RustGraphQLInfo] = field(default_factory=list)

    # Database models
    models: List[RustModelInfo] = field(default_factory=list)
    schemas: List[RustSchemaInfo] = field(default_factory=list)

    # Attributes / macros
    derives: List[RustDeriveInfo] = field(default_factory=list)
    features: List[RustFeatureFlagInfo] = field(default_factory=list)
    proc_macros: List[RustMacroUsageInfo] = field(default_factory=list)
    crate_attrs: List[RustCrateAttributeInfo] = field(default_factory=list)

    # Metadata
    imports: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)
    extern_crates: List[str] = field(default_factory=list)
    macros_defined: List[str] = field(default_factory=list)


class EnhancedRustParser:
    """
    Enhanced Rust parser that uses all extractors for comprehensive parsing.

    Framework detection supports:
    - actix-web (HTTP framework)
    - Rocket (HTTP framework)
    - Axum (HTTP framework built on tower/hyper)
    - Warp (HTTP framework)
    - Tide (async HTTP framework)
    - Tokio (async runtime)
    - Tonic (gRPC)
    - Diesel (ORM)
    - SeaORM (ORM)
    - SQLx (async SQL toolkit)
    - Serde (serialization)
    - Clap (CLI argument parser)
    - Tracing (instrumentation)
    - async-graphql
    - Tower (middleware/service)
    """

    # Module detection
    MODULE_PATTERN = re.compile(
        r'^\s*(?:pub\s+)?mod\s+(\w+)\s*[{;]',
        re.MULTILINE
    )

    # use declarations
    USE_PATTERN = re.compile(
        r'^\s*(?:pub\s+)?use\s+([^;]+);',
        re.MULTILINE
    )

    # extern crate
    EXTERN_CRATE_PATTERN = re.compile(
        r'^\s*extern\s+crate\s+(\w+)',
        re.MULTILINE
    )

    # macro_rules! definition
    MACRO_RULES_PATTERN = re.compile(
        r'^\s*(?:#\[[^\]]*\]\s*)*macro_rules!\s+(\w+)',
        re.MULTILINE
    )

    # Framework detection patterns (use paths and Cargo.toml deps)
    FRAMEWORK_PATTERNS = {
        'actix-web': re.compile(r'(?:actix_web|actix_rt)\b'),
        'rocket': re.compile(r'\brocket\b'),
        'axum': re.compile(r'\baxum\b'),
        'warp': re.compile(r'\bwarp\b'),
        'tide': re.compile(r'\btide\b'),
        'tokio': re.compile(r'\btokio\b'),
        'tonic': re.compile(r'\btonic\b'),
        'diesel': re.compile(r'\bdiesel\b'),
        'sea-orm': re.compile(r'\bsea_orm\b'),
        'sqlx': re.compile(r'\bsqlx\b'),
        'serde': re.compile(r'\bserde\b'),
        'clap': re.compile(r'\bclap\b'),
        'tracing': re.compile(r'\btracing\b'),
        'async-graphql': re.compile(r'\basync_graphql\b'),
        'tower': re.compile(r'\btower\b'),
        'hyper': re.compile(r'\bhyper\b'),
        'reqwest': re.compile(r'\breqwest\b'),
        'prost': re.compile(r'\bprost\b'),
        'anyhow': re.compile(r'\banyhow\b'),
        'thiserror': re.compile(r'\bthiserror\b'),
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = RustTypeExtractor()
        self.function_extractor = RustFunctionExtractor()
        self.api_extractor = RustAPIExtractor()
        self.model_extractor = RustModelExtractor()
        self.attribute_extractor = RustAttributeExtractor()

    def parse(self, content: str, file_path: str = "") -> RustParseResult:
        """
        Parse Rust source code and extract all information.

        Args:
            content: Rust source code content
            file_path: Path to source file

        Returns:
            RustParseResult with all extracted information
        """
        result = RustParseResult(file_path=file_path)

        # Extract module info
        result.module_name = self._detect_module_name(file_path)

        # Extract imports (use declarations)
        result.imports = self._extract_imports(content)

        # Extract extern crates
        result.extern_crates = self._extract_extern_crates(content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Extract macro definitions
        result.macros_defined = self._extract_macro_definitions(content)

        # Extract types (structs, enums, traits, aliases, impls)
        type_result = self.type_extractor.extract(content, file_path)
        result.structs = type_result.get('structs', [])
        result.enums = type_result.get('enums', [])
        result.traits = type_result.get('traits', [])
        result.type_aliases = type_result.get('type_aliases', [])
        result.impls = type_result.get('impls', [])

        # Extract functions and methods
        func_result = self.function_extractor.extract(content, file_path)
        result.functions = func_result.get('functions', [])
        result.methods = func_result.get('methods', [])

        # Extract API patterns
        api_result = self.api_extractor.extract(content, file_path)
        result.routes = api_result.get('routes', [])
        result.grpc_services = api_result.get('grpc_services', [])
        result.graphql_types = api_result.get('graphql', [])

        # Extract database models
        model_result = self.model_extractor.extract(content, file_path)
        result.models = model_result.get('models', [])
        result.schemas = model_result.get('schemas', [])

        # Extract attributes
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.derives = attr_result.get('derives', [])
        result.features = attr_result.get('features', [])
        result.proc_macros = attr_result.get('proc_macros', [])
        result.crate_attrs = attr_result.get('crate_attrs', [])

        return result

    def _detect_module_name(self, file_path: str) -> str:
        """Detect module name from file path."""
        if not file_path:
            return ""
        path = Path(file_path)
        name = path.stem
        if name == "mod" or name == "lib" or name == "main":
            return path.parent.name
        return name

    def _extract_imports(self, content: str) -> List[str]:
        """Extract use declarations from Rust file."""
        imports = []
        for match in self.USE_PATTERN.finditer(content):
            use_path = match.group(1).strip()
            imports.append(use_path)
        return imports

    def _extract_extern_crates(self, content: str) -> List[str]:
        """Extract extern crate declarations."""
        crates = []
        for match in self.EXTERN_CRATE_PATTERN.finditer(content):
            crates.append(match.group(1))
        return crates

    def _extract_macro_definitions(self, content: str) -> List[str]:
        """Extract macro_rules! definitions."""
        macros = []
        for match in self.MACRO_RULES_PATTERN.finditer(content):
            macros.append(match.group(1))
        return macros

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Rust frameworks/libraries are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    @staticmethod
    def parse_cargo_toml(content: str) -> Dict[str, Any]:
        """
        Parse Cargo.toml to extract dependency information.

        Args:
            content: Cargo.toml file content

        Returns:
            Dict with 'name', 'version', 'edition', 'dependencies',
            'dev_dependencies', 'features', 'workspace_members'
        """
        result: Dict[str, Any] = {
            'name': '',
            'version': '',
            'edition': '',
            'dependencies': [],
            'dev_dependencies': [],
            'features': {},
            'workspace_members': [],
        }

        # Extract package info
        name_match = re.search(r'^\s*name\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if name_match:
            result['name'] = name_match.group(1)

        version_match = re.search(r'^\s*version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if version_match:
            result['version'] = version_match.group(1)

        edition_match = re.search(r'^\s*edition\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if edition_match:
            result['edition'] = edition_match.group(1)

        # Extract sections
        current_section = ''
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Section header
            section_match = re.match(r'^\[([^\]]+)\]', line)
            if section_match:
                current_section = section_match.group(1)
                continue

            # Dependencies
            if current_section in ('dependencies', 'dev-dependencies'):
                dep_match = re.match(r'^(\w[\w-]*)\s*=', line)
                if dep_match:
                    dep_name = dep_match.group(1)
                    # Extract version
                    version = ''
                    ver_match = re.search(r'"([^"]+)"', line)
                    if ver_match:
                        version = ver_match.group(1)
                    dep_info = {'name': dep_name, 'version': version}

                    if current_section == 'dependencies':
                        result['dependencies'].append(dep_info)
                    else:
                        result['dev_dependencies'].append(dep_info)

            # Features
            elif current_section == 'features':
                feat_match = re.match(r'^(\w+)\s*=\s*\[([^\]]*)\]', line)
                if feat_match:
                    feat_name = feat_match.group(1)
                    feat_deps = [d.strip().strip('"') for d in feat_match.group(2).split(',') if d.strip()]
                    result['features'][feat_name] = feat_deps

            # Workspace members
            elif current_section == 'workspace':
                member_match = re.search(r'"([^"]+)"', line)
                if member_match:
                    result['workspace_members'].append(member_match.group(1))

        return result
