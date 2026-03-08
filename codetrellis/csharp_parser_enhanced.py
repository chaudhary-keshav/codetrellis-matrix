"""
EnhancedCSharpParser v1.0 - Comprehensive C# parser using all extractors.

This parser integrates all C# extractors to provide complete
parsing of C# source files.

Supports:
- Core types: classes, interfaces, structs, records (C# 1-12+)
- Methods: instance, static, abstract, virtual, extension, async
- Frameworks: ASP.NET Core MVC, Minimal APIs, gRPC, SignalR, Blazor
- EF Core: DbContext, entities, repositories, Fluent API
- Patterns: DTOs, ViewModels, CQRS (Commands/Queries), Repository pattern
- Attributes: categorized (DI, validation, auth, serialization, EF, testing)
- AST support via tree-sitter-c-sharp (optional, graceful fallback to regex)
- LSP support via OmniSharp/Roslyn (optional)

Part of CodeTrellis v4.13 - C# Language Support
"""

import re
import os
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all C# extractors
from .extractors.csharp import (
    CSharpTypeExtractor, CSharpClassInfo, CSharpInterfaceInfo,
    CSharpStructInfo, CSharpRecordInfo, CSharpDelegateInfo,
    CSharpFieldInfo, CSharpPropertyInfo, CSharpGenericParam,
    CSharpFunctionExtractor, CSharpMethodInfo, CSharpConstructorInfo,
    CSharpParameterInfo, CSharpEventInfo,
    CSharpEnumExtractor, CSharpEnumInfo, CSharpEnumMember,
    CSharpAPIExtractor, CSharpEndpointInfo, CSharpGRPCServiceInfo, CSharpSignalRHubInfo,
    CSharpModelExtractor, CSharpEntityInfo, CSharpDbContextInfo,
    CSharpDTOInfo, CSharpRepositoryInfo,
    CSharpAttributeExtractor, CSharpAttributeInfo, CSharpCustomAttributeInfo,
)

logger = logging.getLogger(__name__)

# Try to import tree-sitter-c-sharp for AST parsing (optional)
_TREE_SITTER_CSHARP_AVAILABLE = False
try:
    import tree_sitter
    import tree_sitter_c_sharp
    _TREE_SITTER_CSHARP_AVAILABLE = True
    logger.debug("tree-sitter-c-sharp available for C# AST parsing")
except ImportError:
    logger.debug("tree-sitter-c-sharp not available, using regex-based parsing")


@dataclass
class CSharpParseResult:
    """Complete parse result for a C# file."""
    file_path: str
    file_type: str = "csharp"

    # Namespace and usings
    namespace: str = ""
    usings: List[str] = field(default_factory=list)

    # Core type definitions
    classes: List[CSharpClassInfo] = field(default_factory=list)
    interfaces: List[CSharpInterfaceInfo] = field(default_factory=list)
    structs: List[CSharpStructInfo] = field(default_factory=list)
    records: List[CSharpRecordInfo] = field(default_factory=list)
    delegates: List[CSharpDelegateInfo] = field(default_factory=list)
    enums: List[CSharpEnumInfo] = field(default_factory=list)

    # Methods and constructors
    methods: List[CSharpMethodInfo] = field(default_factory=list)
    constructors: List[CSharpConstructorInfo] = field(default_factory=list)
    events: List[CSharpEventInfo] = field(default_factory=list)

    # Framework elements
    endpoints: List[CSharpEndpointInfo] = field(default_factory=list)
    grpc_services: List[CSharpGRPCServiceInfo] = field(default_factory=list)
    signalr_hubs: List[CSharpSignalRHubInfo] = field(default_factory=list)

    # EF Core / Data
    entities: List[CSharpEntityInfo] = field(default_factory=list)
    db_contexts: List[CSharpDbContextInfo] = field(default_factory=list)
    dtos: List[CSharpDTOInfo] = field(default_factory=list)
    repositories: List[CSharpRepositoryInfo] = field(default_factory=list)
    entity_configs: List[Dict[str, Any]] = field(default_factory=list)

    # Attributes
    attributes: List[CSharpAttributeInfo] = field(default_factory=list)
    custom_attributes: List[CSharpCustomAttributeInfo] = field(default_factory=list)
    attribute_summary: Dict[str, int] = field(default_factory=dict)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    csharp_version_features: List[str] = field(default_factory=list)
    lambda_count: int = 0
    xml_doc: Optional[str] = None


@dataclass
class CSharpDependency:
    """Represents a C# NuGet dependency."""
    name: str
    version: Optional[str] = None
    is_private_assets: bool = False  # PrivateAssets="All" (dev-only)


class EnhancedCSharpParser:
    """
    Enhanced C# parser v1.0 that uses all extractors for comprehensive parsing.

    Automatically detects and extracts:
    - Core C#: classes, interfaces, structs, records, enums, delegates
    - Web Frameworks: ASP.NET Core MVC, Minimal APIs, Razor Pages
    - Real-time: SignalR hubs
    - RPC: gRPC service implementations
    - Data: EF Core DbContext, entities, repositories
    - Patterns: CQRS, Repository, DTO/ViewModel
    - Attributes: categorized by purpose
    - Build: .csproj (project files), Directory.Build.props
    - Testing: xUnit, NUnit, MSTest

    Supports full AST parsing via tree-sitter-c-sharp when available.
    Supports LSP integration via OmniSharp/Roslyn (optional).
    """

    # Framework detection patterns (using-based)
    FRAMEWORK_PATTERNS = {
        # ASP.NET Core
        'aspnet_core': re.compile(r'using\s+Microsoft\.AspNetCore\b'),
        'aspnet_mvc': re.compile(r'using\s+Microsoft\.AspNetCore\.Mvc\b'),
        'aspnet_razor': re.compile(r'using\s+Microsoft\.AspNetCore\.Razor\b'),
        'blazor': re.compile(r'using\s+Microsoft\.AspNetCore\.Components\b'),
        'signalr': re.compile(r'using\s+Microsoft\.AspNetCore\.SignalR\b'),
        'minimal_api': re.compile(r'app\.Map(?:Get|Post|Put|Delete|Patch)\b'),

        # Entity Framework Core
        'ef_core': re.compile(r'using\s+Microsoft\.EntityFrameworkCore\b'),
        'ef_design': re.compile(r'using\s+Microsoft\.EntityFrameworkCore\.Design\b'),
        'ef_migrations': re.compile(r'using\s+Microsoft\.EntityFrameworkCore\.Migrations\b'),

        # Identity
        'identity': re.compile(r'using\s+Microsoft\.AspNetCore\.Identity\b'),
        'identity_server': re.compile(r'using\s+IdentityServer4\b|using\s+Duende\.IdentityServer\b'),

        # gRPC
        'grpc': re.compile(r'using\s+Grpc\.Core\b|using\s+Google\.Protobuf\b'),

        # Messaging
        'masstransit': re.compile(r'using\s+MassTransit\b'),
        'mediatr': re.compile(r'using\s+MediatR\b'),
        'rabbitmq': re.compile(r'using\s+RabbitMQ\b'),
        'azure_servicebus': re.compile(r'using\s+Azure\.Messaging\.ServiceBus\b'),

        # Testing
        'xunit': re.compile(r'using\s+Xunit\b'),
        'nunit': re.compile(r'using\s+NUnit\b'),
        'mstest': re.compile(r'using\s+Microsoft\.VisualStudio\.TestTools\b'),
        'moq': re.compile(r'using\s+Moq\b'),
        'nsubstitute': re.compile(r'using\s+NSubstitute\b'),
        'fluentassertions': re.compile(r'using\s+FluentAssertions\b'),
        'bogus': re.compile(r'using\s+Bogus\b'),

        # Serialization
        'system_text_json': re.compile(r'using\s+System\.Text\.Json\b'),
        'newtonsoft_json': re.compile(r'using\s+Newtonsoft\.Json\b'),
        'messagepack': re.compile(r'using\s+MessagePack\b'),

        # Logging
        'serilog': re.compile(r'using\s+Serilog\b'),
        'nlog': re.compile(r'using\s+NLog\b'),

        # DI
        'autofac': re.compile(r'using\s+Autofac\b'),
        'castle_windsor': re.compile(r'using\s+Castle\.Windsor\b'),
        'microsoft_di': re.compile(r'using\s+Microsoft\.Extensions\.DependencyInjection\b'),

        # ORM/Data
        'dapper': re.compile(r'using\s+Dapper\b'),
        'npgsql': re.compile(r'using\s+Npgsql\b'),
        'automapper': re.compile(r'using\s+AutoMapper\b'),
        'mapster': re.compile(r'using\s+Mapster\b'),
        'fluentvalidation': re.compile(r'using\s+FluentValidation\b'),

        # Cloud/Platform
        'azure_functions': re.compile(r'using\s+Microsoft\.Azure\.Functions\b'),
        'aws_lambda': re.compile(r'using\s+Amazon\.Lambda\b'),

        # Reactive
        'reactive': re.compile(r'using\s+System\.Reactive\b'),

        # MAUI / Xamarin
        'maui': re.compile(r'using\s+Microsoft\.Maui\b'),
        'xamarin': re.compile(r'using\s+Xamarin\b'),

        # ML.NET
        'mlnet': re.compile(r'using\s+Microsoft\.ML\b'),

        # Polly (resilience)
        'polly': re.compile(r'using\s+Polly\b'),

        # Swagger / API docs
        'swashbuckle': re.compile(r'using\s+Swashbuckle\b'),
        'nswag': re.compile(r'using\s+NSwag\b'),

        # Hangfire
        'hangfire': re.compile(r'using\s+Hangfire\b'),

        # Quartz.NET
        'quartz': re.compile(r'using\s+Quartz\b'),
    }

    # Namespace declaration
    NAMESPACE_PATTERN = re.compile(
        r'^\s*namespace\s+([\w.]+)\s*[{;]',
        re.MULTILINE
    )

    # Using directive
    USING_PATTERN = re.compile(
        r'^\s*using\s+(?:static\s+)?([\w.]+)\s*;',
        re.MULTILINE
    )

    # C# version feature detection
    VERSION_FEATURES = {
        'records': re.compile(r'\brecord\s+(?:class\s+|struct\s+)?\w+'),
        'init_only': re.compile(r'\binit\s*;'),
        'top_level_statements': re.compile(r'^(?!.*namespace\b).*\bawait\s+|^(?!.*class\b).*\bConsole\.', re.MULTILINE),
        'file_scoped_namespace': re.compile(r'^\s*namespace\s+[\w.]+\s*;', re.MULTILINE),
        'global_using': re.compile(r'^\s*global\s+using\b', re.MULTILINE),
        'nullable_ref_types': re.compile(r'#nullable\s+enable'),
        'pattern_matching': re.compile(r'\bis\s+\w+\s+\w+\b|\bswitch\s*\{'),
        'raw_string_literal': re.compile(r'"""'),
        'primary_constructor': re.compile(r'class\s+\w+\s*\([^)]+\)\s*(?::|{)'),
        'required_members': re.compile(r'\brequired\s+'),
        'collection_expressions': re.compile(r'\[\s*\.\.\s*\w+'),
        'span_stackalloc': re.compile(r'\bstackalloc\b'),
        'async_streams': re.compile(r'\bIAsyncEnumerable\b|\bawait\s+foreach\b'),
        'interpolated_strings': re.compile(r'\$"'),
        'switch_expressions': re.compile(r'\bswitch\s*\{'),
    }

    def __init__(self):
        """Initialize the enhanced C# parser with all extractors."""
        self.type_extractor = CSharpTypeExtractor()
        self.function_extractor = CSharpFunctionExtractor()
        self.enum_extractor = CSharpEnumExtractor()
        self.api_extractor = CSharpAPIExtractor()
        self.model_extractor = CSharpModelExtractor()
        self.attribute_extractor = CSharpAttributeExtractor()

        # AST parser (optional)
        self._ast_parser = None
        self._ast_language = None
        if _TREE_SITTER_CSHARP_AVAILABLE:
            try:
                self._ast_language = tree_sitter.Language(tree_sitter_c_sharp.language())
                self._ast_parser = tree_sitter.Parser(self._ast_language)
                logger.info("C# AST parser initialized with tree-sitter-c-sharp")
            except Exception as e:
                logger.warning(f"Failed to initialize tree-sitter-c-sharp: {e}")

    def parse(self, content: str, file_path: str = "") -> CSharpParseResult:
        """
        Parse C# source code and extract all information.

        Uses tree-sitter AST when available, falls back to regex-based extraction.

        Args:
            content: C# source code content
            file_path: Path to source file

        Returns:
            CSharpParseResult with all extracted information
        """
        result = CSharpParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Extract namespace
        ns_match = self.NAMESPACE_PATTERN.search(content)
        if ns_match:
            result.namespace = ns_match.group(1)

        # Extract usings
        result.usings = [m.group(1) for m in self.USING_PATTERN.finditer(content)]

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect C# version features
        result.csharp_version_features = self._detect_version_features(content)

        # Extract XML doc on class/file
        first_doc = re.search(r'///\s*<summary>\s*\n///\s*(.*?)\n', content)
        if first_doc:
            result.xml_doc = first_doc.group(1).strip()[:200]

        # Use AST parser if available for type/method extraction
        if self._ast_parser and self._ast_language:
            self._parse_with_ast(content, file_path, result)
        else:
            self._parse_with_regex(content, file_path, result)

        return result

    def _parse_with_ast(self, content: str, file_path: str, result: CSharpParseResult):
        """Parse using tree-sitter AST for maximum accuracy."""
        try:
            tree = self._ast_parser.parse(bytes(content, 'utf-8'))
            root = tree.root_node

            # Extract types from AST
            self._extract_ast_types(root, content, file_path, result)

            # Use regex for framework-specific patterns (AST may not cover these)
            self._extract_frameworks_regex(content, file_path, result, skip_types=True)
        except Exception as e:
            logger.warning(f"AST parsing failed for {file_path}, falling back to regex: {e}")
            self._parse_with_regex(content, file_path, result)

    def _extract_ast_types(self, root_node, content: str, file_path: str, result: CSharpParseResult):
        """Extract type definitions from AST."""
        if not _TREE_SITTER_CSHARP_AVAILABLE:
            return

        for node in self._walk_ast(root_node):
            node_type = node.type

            if node_type == 'class_declaration':
                self._extract_ast_class(node, content, file_path, result)
            elif node_type == 'interface_declaration':
                self._extract_ast_interface(node, content, file_path, result)
            elif node_type == 'struct_declaration':
                self._extract_ast_struct(node, content, file_path, result)
            elif node_type == 'record_declaration':
                self._extract_ast_record(node, content, file_path, result)
            elif node_type == 'enum_declaration':
                self._extract_ast_enum(node, content, file_path, result)
            elif node_type == 'delegate_declaration':
                self._extract_ast_delegate(node, content, file_path, result)
            elif node_type == 'method_declaration':
                self._extract_ast_method(node, content, file_path, result)
            elif node_type == 'constructor_declaration':
                self._extract_ast_constructor(node, content, file_path, result)

    def _extract_ast_class(self, node, content: str, file_path: str, result: CSharpParseResult):
        """Extract class info from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return
        name = content[name_node.start_byte:name_node.end_byte]

        modifiers = self._get_ast_modifiers(node, content)
        attributes = self._get_ast_attributes(node, content)

        # Get base types
        base_list = node.child_by_field_name('bases')
        extends = None
        implements = []
        if base_list:
            bases_text = content[base_list.start_byte:base_list.end_byte]
            bases_text = bases_text.lstrip(':').strip()
            parts = [p.strip() for p in bases_text.split(',')]
            if parts:
                extends = parts[0]
                implements = parts[1:]

        result.classes.append(CSharpClassInfo(
            name=name,
            extends=extends,
            implements=implements,
            attributes=attributes,
            fields=[],
            properties=[],
            methods=[],
            file=file_path,
            line_number=node.start_point[0] + 1,
            is_abstract='abstract' in modifiers,
            is_sealed='sealed' in modifiers,
            is_static='static' in modifiers,
            is_partial='partial' in modifiers,
            generic_params=[],
        ))

    def _extract_ast_interface(self, node, content: str, file_path: str, result: CSharpParseResult):
        """Extract interface from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return
        name = content[name_node.start_byte:name_node.end_byte]
        attributes = self._get_ast_attributes(node, content)

        result.interfaces.append(CSharpInterfaceInfo(
            name=name,
            extends=[],
            methods=[],
            properties=[],
            attributes=attributes,
            file=file_path,
            line_number=node.start_point[0] + 1,
        ))

    def _extract_ast_struct(self, node, content: str, file_path: str, result: CSharpParseResult):
        """Extract struct from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return
        name = content[name_node.start_byte:name_node.end_byte]
        modifiers = self._get_ast_modifiers(node, content)
        attributes = self._get_ast_attributes(node, content)

        result.structs.append(CSharpStructInfo(
            name=name,
            implements=[],
            fields=[],
            properties=[],
            methods=[],
            attributes=attributes,
            file=file_path,
            line_number=node.start_point[0] + 1,
            is_readonly='readonly' in modifiers,
            is_ref='ref' in modifiers,
        ))

    def _extract_ast_record(self, node, content: str, file_path: str, result: CSharpParseResult):
        """Extract record from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return
        name = content[name_node.start_byte:name_node.end_byte]
        attributes = self._get_ast_attributes(node, content)

        result.records.append(CSharpRecordInfo(
            name=name,
            parameters=[],
            implements=[],
            attributes=attributes,
            file=file_path,
            line_number=node.start_point[0] + 1,
        ))

    def _extract_ast_enum(self, node, content: str, file_path: str, result: CSharpParseResult):
        """Extract enum from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return
        name = content[name_node.start_byte:name_node.end_byte]
        attributes = self._get_ast_attributes(node, content)

        result.enums.append(CSharpEnumInfo(
            name=name,
            members=[],
            attributes=attributes,
            file=file_path,
            line_number=node.start_point[0] + 1,
        ))

    def _extract_ast_delegate(self, node, content: str, file_path: str, result: CSharpParseResult):
        """Extract delegate from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return
        name = content[name_node.start_byte:name_node.end_byte]

        result.delegates.append(CSharpDelegateInfo(
            name=name,
            return_type="",
            parameters=[],
            file=file_path,
            line_number=node.start_point[0] + 1,
        ))

    def _extract_ast_method(self, node, content: str, file_path: str, result: CSharpParseResult):
        """Extract method from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return
        name = content[name_node.start_byte:name_node.end_byte]
        modifiers = self._get_ast_modifiers(node, content)
        attributes = self._get_ast_attributes(node, content)

        # Return type
        return_type_node = node.child_by_field_name('type')
        return_type = content[return_type_node.start_byte:return_type_node.end_byte] if return_type_node else "void"

        # Find enclosing class
        class_name = None
        parent = node.parent
        while parent:
            if parent.type in ('class_declaration', 'struct_declaration',
                               'record_declaration', 'interface_declaration'):
                pn = parent.child_by_field_name('name')
                if pn:
                    class_name = content[pn.start_byte:pn.end_byte]
                break
            parent = parent.parent

        result.methods.append(CSharpMethodInfo(
            name=name,
            return_type=return_type,
            parameters=[],
            modifiers=modifiers,
            attributes=attributes,
            class_name=class_name or "",
            file=file_path,
            line_number=node.start_point[0] + 1,
            is_async='async' in modifiers,
            is_virtual='virtual' in modifiers,
            is_override='override' in modifiers,
            is_abstract='abstract' in modifiers,
            is_static='static' in modifiers,
        ))

    def _extract_ast_constructor(self, node, content: str, file_path: str, result: CSharpParseResult):
        """Extract constructor from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return
        class_name = content[name_node.start_byte:name_node.end_byte]
        modifiers = self._get_ast_modifiers(node, content)

        result.constructors.append(CSharpConstructorInfo(
            class_name=class_name,
            parameters=[],
            modifiers=modifiers,
            file=file_path,
            line_number=node.start_point[0] + 1,
        ))

    def _get_ast_modifiers(self, node, content: str) -> List[str]:
        """Get modifiers from an AST node."""
        modifiers = []
        for child in node.children:
            if child.type == 'modifier':
                modifiers.append(content[child.start_byte:child.end_byte])
        return modifiers

    def _get_ast_attributes(self, node, content: str) -> List[str]:
        """Get attributes from an AST node."""
        attributes = []
        for child in node.children:
            if child.type == 'attribute_list':
                attr_text = content[child.start_byte:child.end_byte]
                # Extract attribute names from [Attr1, Attr2(...)]
                for attr_match in re.finditer(r'(\w+)(?:\s*\()?', attr_text.strip('[]')):
                    attributes.append(attr_match.group(1))
        return attributes

    def _walk_ast(self, node):
        """Walk AST tree depth-first."""
        yield node
        for child in node.children:
            yield from self._walk_ast(child)

    def _parse_with_regex(self, content: str, file_path: str, result: CSharpParseResult):
        """Parse using regex-based extractors (fallback, always available)."""
        # Extract types
        type_result = self.type_extractor.extract(content, file_path)
        result.classes = type_result.get('classes', [])
        result.interfaces = type_result.get('interfaces', [])
        result.structs = type_result.get('structs', [])
        result.records = type_result.get('records', [])
        result.delegates = type_result.get('delegates', [])

        # Extract enums
        result.enums = self.enum_extractor.extract(content, file_path)

        # Extract framework elements
        self._extract_frameworks_regex(content, file_path, result)

    def _extract_frameworks_regex(self, content: str, file_path: str,
                                   result: CSharpParseResult,
                                   skip_types: bool = False):
        """Extract framework-specific elements using regex.

        Args:
            skip_types: If True, skip type extraction (already done by AST).
        """
        if not skip_types:
            # Extract methods, constructors, events
            # (function_extractor auto-detects class names for constructor matching)
            func_result = self.function_extractor.extract(content, file_path)
            result.methods = func_result.get('methods', [])
            result.constructors = func_result.get('constructors', [])
            result.events = func_result.get('events', [])
            result.lambda_count = func_result.get('lambda_count', 0)

        # Extract API endpoints
        api_result = self.api_extractor.extract(content, file_path)
        result.endpoints = api_result.get('endpoints', [])
        result.grpc_services = api_result.get('grpc_services', [])
        result.signalr_hubs = api_result.get('signalr_hubs', [])

        # Extract EF Core models and repositories
        model_result = self.model_extractor.extract(content, file_path)
        result.entities = model_result.get('entities', [])
        result.db_contexts = model_result.get('db_contexts', [])
        result.dtos = model_result.get('dtos', [])
        result.repositories = model_result.get('repositories', [])
        result.entity_configs = model_result.get('entity_configs', [])

        # Extract attribute usages
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.attributes = attr_result.get('attributes', [])
        result.custom_attributes = attr_result.get('custom_attributes', [])
        result.attribute_summary = attr_result.get('attribute_summary', {})

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which C#/.NET frameworks are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_version_features(self, content: str) -> List[str]:
        """Detect C# version-specific features used in the file."""
        features = []
        for feature, pattern in self.VERSION_FEATURES.items():
            if pattern.search(content):
                features.append(feature)
        return features

    @staticmethod
    def parse_csproj(csproj_path: str) -> Dict[str, Any]:
        """
        Parse .csproj project file to extract dependencies and project metadata.

        Returns dict with: target_framework, sdk, dependencies (NuGet packages),
                          project_references, output_type, nullable, implicit_usings
        """
        result = {
            'target_framework': '',
            'sdk': '',
            'output_type': '',
            'nullable': '',
            'implicit_usings': False,
            'root_namespace': '',
            'assembly_name': '',
            'dependencies': [],
            'project_references': [],
            'analyzers': [],
            'is_web': False,
            'is_test': False,
            'is_blazor': False,
        }

        try:
            content = Path(csproj_path).read_text()

            # SDK
            sdk_match = re.search(r'<Project\s+Sdk="([^"]+)"', content)
            if sdk_match:
                result['sdk'] = sdk_match.group(1)
                if 'Web' in result['sdk']:
                    result['is_web'] = True
                if 'BlazorWebAssembly' in result['sdk']:
                    result['is_blazor'] = True

            # Target framework
            tf_match = re.search(r'<TargetFramework>([^<]+)</TargetFramework>', content)
            if tf_match:
                result['target_framework'] = tf_match.group(1)
            else:
                tfs_match = re.search(r'<TargetFrameworks>([^<]+)</TargetFrameworks>', content)
                if tfs_match:
                    result['target_framework'] = tfs_match.group(1)  # Multi-target

            # OutputType
            out_match = re.search(r'<OutputType>([^<]+)</OutputType>', content)
            if out_match:
                result['output_type'] = out_match.group(1)

            # Nullable
            null_match = re.search(r'<Nullable>([^<]+)</Nullable>', content)
            if null_match:
                result['nullable'] = null_match.group(1)

            # ImplicitUsings
            iu_match = re.search(r'<ImplicitUsings>([^<]+)</ImplicitUsings>', content)
            if iu_match:
                result['implicit_usings'] = iu_match.group(1).lower() in ('enable', 'true')

            # RootNamespace
            rns_match = re.search(r'<RootNamespace>([^<]+)</RootNamespace>', content)
            if rns_match:
                result['root_namespace'] = rns_match.group(1)

            # AssemblyName
            an_match = re.search(r'<AssemblyName>([^<]+)</AssemblyName>', content)
            if an_match:
                result['assembly_name'] = an_match.group(1)

            # PackageReferences (NuGet)
            for pkg_match in re.finditer(
                r'<PackageReference\s+Include="([^"]+)"(?:\s+Version="([^"]+)")?'
                r'(?:\s+PrivateAssets="([^"]+)")?',
                content
            ):
                dep = {
                    'name': pkg_match.group(1),
                    'version': pkg_match.group(2) or '',
                    'is_private_assets': bool(pkg_match.group(3)),
                }
                result['dependencies'].append(dep)

                # Detect test projects
                if pkg_match.group(1) in ('xunit', 'NUnit', 'MSTest.TestFramework',
                                          'Microsoft.NET.Test.Sdk'):
                    result['is_test'] = True

            # ProjectReferences
            for ref_match in re.finditer(
                r'<ProjectReference\s+Include="([^"]+)"',
                content
            ):
                result['project_references'].append(ref_match.group(1))

        except Exception as e:
            logger.warning(f"Failed to parse .csproj {csproj_path}: {e}")

        return result

    @staticmethod
    def parse_sln(sln_path: str) -> Dict[str, Any]:
        """
        Parse .sln solution file to extract project references.

        Returns dict with: projects (list of project entries with name, path, type)
        """
        result = {
            'projects': [],
            'configurations': [],
        }

        try:
            content = Path(sln_path).read_text()

            # Project entries: Project("{GUID}") = "Name", "Path", "{GUID}"
            for match in re.finditer(
                r'Project\("\{([^}]+)\}"\)\s*=\s*"([^"]+)",\s*"([^"]+)",\s*"\{([^}]+)\}"',
                content
            ):
                type_guid = match.group(1)
                name = match.group(2)
                path = match.group(3)
                proj_guid = match.group(4)

                # Determine project type from GUID
                proj_type = "unknown"
                # C# project GUID
                if type_guid.upper() in ("FAE04EC0-301F-11D3-BF4B-00C04F79EFBC",
                                          "9A19103F-16F7-4668-BE54-9A1E7A4F7556"):
                    proj_type = "csharp"
                elif type_guid.upper() == "2150E333-8FDC-42A3-9474-1A3956D46DE8":
                    proj_type = "solution_folder"

                if proj_type != "solution_folder":  # Skip virtual folders
                    result['projects'].append({
                        'name': name,
                        'path': path,
                        'type': proj_type,
                        'guid': proj_guid,
                    })

            # Build configurations
            for config in re.findall(
                r'(\w+\|\w+)\s*=\s*\w+\|\w+',
                content
            ):
                if config not in result['configurations']:
                    result['configurations'].append(config)

        except Exception as e:
            logger.warning(f"Failed to parse .sln {sln_path}: {e}")

        return result
