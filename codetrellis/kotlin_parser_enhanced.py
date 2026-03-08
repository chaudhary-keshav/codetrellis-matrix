"""
EnhancedKotlinParser v2.0 - Comprehensive Kotlin parser with full AST + LSP support.

Supports Kotlin 1.0 through 2.1+, K2 compiler detection, tree-sitter-kotlin AST,
Kotlin Language Server LSP, and 45+ framework detection patterns.

Part of CodeTrellis v4.21 - Kotlin Language Support Upgrade
"""

import re
import os
import json
import subprocess
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Tuple
from pathlib import Path

from .extractors.kotlin import (
    KotlinTypeExtractor, KotlinClassInfo, KotlinObjectInfo,
    KotlinInterfaceInfo, KotlinEnumInfo, KotlinPropertyInfo,
    KotlinFunctionExtractor, KotlinFunctionInfo, KotlinParameterInfo,
    KotlinAPIExtractor, KotlinEndpointInfo, KotlinWebSocketInfo,
    KotlinGRPCServiceInfo, KotlinGraphQLInfo,
    KotlinModelExtractor, KotlinEntityInfo, KotlinRepositoryInfo,
    KotlinExposedTableInfo, KotlinSerializableInfo, KotlinDTOInfo,
    KotlinAttributeExtractor, KotlinAnnotationDefInfo,
    KotlinAnnotationUsageInfo, KotlinDelegationInfo,
    KotlinDIBindingInfo, KotlinMultiplatformDeclInfo,
    KotlinContextReceiverInfo, KotlinContractInfo,
)

from .extractors.java import (
    JavaAPIExtractor, JavaModelExtractor, JavaAnnotationExtractor,
)

logger = logging.getLogger(__name__)

_TREE_SITTER_KOTLIN_AVAILABLE = False
try:
    import tree_sitter
    import tree_sitter_kotlin
    _TREE_SITTER_KOTLIN_AVAILABLE = True
    logger.debug("tree-sitter-kotlin available for Kotlin AST parsing")
except ImportError:
    logger.debug("tree-sitter-kotlin not available, using regex-based parsing")


@dataclass
class KotlinParseResult:
    """Complete parse result for a Kotlin file."""
    file_path: str
    file_type: str = "kotlin"
    package_name: str = ""
    imports: List[str] = field(default_factory=list)
    classes: List[KotlinClassInfo] = field(default_factory=list)
    objects: List[KotlinObjectInfo] = field(default_factory=list)
    interfaces: List[KotlinInterfaceInfo] = field(default_factory=list)
    enums: List[KotlinEnumInfo] = field(default_factory=list)
    type_aliases: List[Dict[str, str]] = field(default_factory=list)
    functions: List[KotlinFunctionInfo] = field(default_factory=list)
    lambda_count: int = 0
    endpoints: List[Any] = field(default_factory=list)
    websockets: List[KotlinWebSocketInfo] = field(default_factory=list)
    grpc_services: List[KotlinGRPCServiceInfo] = field(default_factory=list)
    graphql: List[KotlinGraphQLInfo] = field(default_factory=list)
    entities: List[Any] = field(default_factory=list)
    repositories: List[Any] = field(default_factory=list)
    exposed_tables: List[KotlinExposedTableInfo] = field(default_factory=list)
    serializables: List[KotlinSerializableInfo] = field(default_factory=list)
    dtos: List[KotlinDTOInfo] = field(default_factory=list)
    annotation_defs: List[KotlinAnnotationDefInfo] = field(default_factory=list)
    annotation_usages: List[KotlinAnnotationUsageInfo] = field(default_factory=list)
    delegations: List[KotlinDelegationInfo] = field(default_factory=list)
    di_bindings: List[KotlinDIBindingInfo] = field(default_factory=list)
    dsl_markers: List[Dict[str, Any]] = field(default_factory=list)
    multiplatform_decls: List[KotlinMultiplatformDeclInfo] = field(default_factory=list)
    context_receivers: List[KotlinContextReceiverInfo] = field(default_factory=list)
    contracts: List[KotlinContractInfo] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)
    kotlin_features: List[str] = field(default_factory=list)
    kotlin_version: str = ""
    uses_coroutines: bool = False
    uses_compose: bool = False
    uses_multiplatform: bool = False
    uses_k2_compiler: bool = False
    ast_available: bool = False
    ast_node_count: int = 0


class EnhancedKotlinParser:
    """Enhanced Kotlin parser v2.0 with full AST and LSP support."""

    FRAMEWORK_PATTERNS = {
        'spring_boot': re.compile(r'import\s+org\.springframework\.boot\b'),
        'spring_mvc': re.compile(r'import\s+org\.springframework\.web\b'),
        'spring_webflux': re.compile(r'import\s+org\.springframework\.web\.reactive\b'),
        'spring_data': re.compile(r'import\s+org\.springframework\.data\b'),
        'spring_security': re.compile(r'import\s+org\.springframework\.security\b'),
        'spring_cloud': re.compile(r'import\s+org\.springframework\.cloud\b'),
        'ktor_server': re.compile(r'import\s+io\.ktor\.server\b'),
        'ktor_client': re.compile(r'import\s+io\.ktor\.client\b'),
        'ktor': re.compile(r'import\s+io\.ktor\b'),
        'quarkus': re.compile(r'import\s+io\.quarkus\b'),
        'micronaut': re.compile(r'import\s+io\.micronaut\b'),
        'jpa': re.compile(r'import\s+(?:jakarta|javax)\.persistence\b'),
        'hibernate': re.compile(r'import\s+org\.hibernate\b'),
        'exposed': re.compile(r'import\s+org\.jetbrains\.exposed\b'),
        'room': re.compile(r'import\s+androidx\.room\b'),
        'kotlinx_serialization': re.compile(r'import\s+kotlinx\.serialization\b'),
        'kotlinx_coroutines': re.compile(r'import\s+kotlinx\.coroutines\b'),
        'kotlinx_datetime': re.compile(r'import\s+kotlinx\.datetime\b'),
        'arrow': re.compile(r'import\s+arrow\b'),
        'koin': re.compile(r'import\s+org\.koin\b'),
        'dagger': re.compile(r'import\s+dagger\b'),
        'hilt': re.compile(r'import\s+dagger\.hilt\b'),
        'compose': re.compile(r'import\s+androidx\.compose\b'),
        'compose_multiplatform': re.compile(r'import\s+org\.jetbrains\.compose\b'),
        'jetpack_navigation': re.compile(r'import\s+androidx\.navigation\b'),
        'jetpack_lifecycle': re.compile(r'import\s+androidx\.lifecycle\b'),
        'jetpack_viewmodel': re.compile(r'import\s+androidx\.lifecycle\.ViewModel\b'),
        'retrofit': re.compile(r'import\s+retrofit2\b'),
        'okhttp': re.compile(r'import\s+okhttp3\b'),
        'jackson': re.compile(r'import\s+com\.fasterxml\.jackson\b'),
        'grpc': re.compile(r'import\s+io\.grpc\b'),
        'graphql_kotlin': re.compile(r'import\s+com\.expediagroup\.graphql\b'),
        'dgs': re.compile(r'import\s+com\.netflix\.graphql\.dgs\b'),
        'kgraphql': re.compile(r'import\s+com\.apurebase\.kgraphql\b'),
        'kotest': re.compile(r'import\s+io\.kotest\b'),
        'mockk': re.compile(r'import\s+io\.mockk\b'),
        'junit5': re.compile(r'import\s+org\.junit\.jupiter\b'),
        'testcontainers': re.compile(r'import\s+org\.testcontainers\b'),
        'kodein': re.compile(r'import\s+org\.kodein\b'),
        'realm': re.compile(r'import\s+io\.realm\b'),
        'sqldelight': re.compile(r'import\s+com\.squareup\.sqldelight\b'),
        'ktor_auth': re.compile(r'import\s+io\.ktor\.server\.auth\b'),
        'kmongo': re.compile(r'import\s+org\.litote\.kmongo\b'),
        'ktorm': re.compile(r'import\s+org\.ktorm\b'),
        'moshi': re.compile(r'import\s+com\.squareup\.moshi\b'),
        'kotlin_result': re.compile(r'import\s+com\.github\.michaelbull\.result\b'),
        'kotlinx_html': re.compile(r'import\s+kotlinx\.html\b'),
    }

    PACKAGE_PATTERN = re.compile(r'^package\s+([\w.]+)', re.MULTILINE)
    IMPORT_PATTERN = re.compile(r'^import\s+([\w.*]+)', re.MULTILINE)

    FEATURE_PATTERNS = {
        'coroutines': re.compile(r'\bsuspend\s+fun\b|\bCoroutineScope\b|\blaunch\b|\basync\b|\bwithContext\b'),
        'flow': re.compile(r'\bFlow<|\bflow\s*\{|\bcollect\b|\bStateFlow\b|\bSharedFlow\b|\bMutableStateFlow\b'),
        'channels': re.compile(r'\bChannel<|\bBroadcastChannel\b|\bSendChannel\b|\bReceiveChannel\b'),
        'data_classes': re.compile(r'\bdata\s+class\b'),
        'sealed_classes': re.compile(r'\bsealed\s+(?:class|interface)\b'),
        'value_classes': re.compile(r'\b(?:value|inline)\s+class\b'),
        'delegation': re.compile(r'\bby\s+\w+'),
        'dsl': re.compile(r'@DslMarker|@\w+Dsl'),
        'multiplatform': re.compile(r'\bexpect\s+(?:fun|class|interface)\b|\bactual\s+(?:fun|class|interface)\b'),
        'contracts': re.compile(r'\bcontract\s*\{'),
        'type_aliases': re.compile(r'\btypealias\s+\w+'),
        'context_receivers': re.compile(r'\bcontext\s*\('),
        'compose': re.compile(r'@Composable'),
        'destructuring': re.compile(r'\bcomponent[1-9]\b|\bval\s*\([^)]+\)\s*='),
        'reified': re.compile(r'\breified\s+\w+'),
        'sam_conversions': re.compile(r'\bfun\s+interface\b'),
        'scope_functions': re.compile(r'\b(?:let|run|with|apply|also)\s*\{'),
        'sequences': re.compile(r'\bsequence\s*\{|\basSequence\b|\bgenerateSequence\b'),
        'delegation_properties': re.compile(r'\bby\s+(?:lazy|Delegates|observable|vetoable|map)\b'),
        'operator_overloading': re.compile(r'\boperator\s+fun\b'),
        'extension_functions': re.compile(r'\bfun\s+\w+\.\w+'),
        'companion_objects': re.compile(r'\bcompanion\s+object\b'),
        'object_declarations': re.compile(r'(?<!\bcompanion\s)\bobject\s+\w+'),
    }

    KOTLIN_VERSION_FEATURES = {
        '2.1': [re.compile(r'\bwhen\s+guard\b')],
        '2.0': [re.compile(r'\b@SubclassOptInRequired\b'), re.compile(r'\bdata\s+object\b')],
        '1.9': [re.compile(r'\bdata\s+object\b'), re.compile(r'\benum\s+entries\b')],
        '1.8': [re.compile(r'\b@JvmDefaultWithCompatibility\b')],
        '1.7': [re.compile(r'\bcontext\s*\('), re.compile(r'\bOptIn\b')],
        '1.6': [re.compile(r'\bvalue\s+class\b')],
        '1.5': [re.compile(r'\bsealed\s+interface\b')],
        '1.4': [re.compile(r'\bfun\s+interface\b')],
        '1.3': [re.compile(r'\binline\s+class\b'), re.compile(r'\bUInt\b|\bULong\b')],
        '1.2': [re.compile(r'\blateinit\b.*::isInitialized')],
        '1.1': [re.compile(r'\btypealias\b')],
        '1.0': [re.compile(r'\bdata\s+class\b'), re.compile(r'\bcompanion\s+object\b')],
    }

    K2_INDICATORS = [
        re.compile(r'languageVersion\s*=\s*["\']?2\.\d'),
        re.compile(r'kotlin\.experimental\.tryK2\s*=\s*true'),
        re.compile(r'compilerOptions\s*\{[^}]*languageVersion\.set\s*\(\s*KotlinVersion\.KOTLIN_2'),
    ]

    def __init__(self):
        """Initialize the enhanced Kotlin parser with all extractors."""
        self.type_extractor = KotlinTypeExtractor()
        self.function_extractor = KotlinFunctionExtractor()
        self.api_extractor = KotlinAPIExtractor()
        self.model_extractor = KotlinModelExtractor()
        self.attribute_extractor = KotlinAttributeExtractor()
        self.java_api_extractor = JavaAPIExtractor()
        self.java_model_extractor = JavaModelExtractor()
        self.java_annotation_extractor = JavaAnnotationExtractor()

        self._ts_parser = None
        self._ts_language = None
        if _TREE_SITTER_KOTLIN_AVAILABLE:
            try:
                self._ts_language = tree_sitter_kotlin.language()
                self._ts_parser = tree_sitter.Parser(self._ts_language)
                logger.debug("tree-sitter-kotlin parser initialized")
            except Exception as e:
                logger.debug(f"Failed to init tree-sitter-kotlin: {e}")

    def parse(self, content, file_path=""):
        """Parse Kotlin source code and extract all information."""
        result = KotlinParseResult(file_path=file_path)
        if not content or not content.strip():
            return result

        # Package name
        pkg_match = self.PACKAGE_PATTERN.search(content)
        if pkg_match:
            result.package_name = pkg_match.group(1)

        # Imports
        result.imports = [m.group(1) for m in self.IMPORT_PATTERN.finditer(content)]

        # Detect frameworks, features, version
        result.detected_frameworks = self._detect_frameworks(content)
        result.kotlin_features = self._detect_features(content)
        result.uses_coroutines = 'coroutines' in result.kotlin_features
        result.uses_compose = 'compose' in result.kotlin_features
        result.uses_multiplatform = 'multiplatform' in result.kotlin_features
        result.kotlin_version = self._detect_kotlin_version(content)
        result.uses_k2_compiler = self._detect_k2_compiler(content)

        # AST-assisted extraction if available
        if self._ts_parser:
            self._ast_extract(content, result)

        # Type extraction (classes, objects, interfaces, enums, type aliases)
        type_result = self.type_extractor.extract(content, file_path)
        result.classes = type_result.get('classes', [])
        result.objects = type_result.get('objects', [])
        result.interfaces = type_result.get('interfaces', [])
        result.enums = type_result.get('enums', [])
        result.type_aliases = type_result.get('type_aliases', [])

        # Function extraction
        class_names = [c.name for c in result.classes]
        class_names.extend([o.name for o in result.objects])
        func_result = self.function_extractor.extract(content, file_path, class_names=class_names)
        result.functions = func_result.get('functions', [])
        result.lambda_count = func_result.get('lambda_count', 0)

        # API extraction (Ktor, GraphQL, gRPC, WebSocket)
        api_result = self.api_extractor.extract(content, file_path)
        result.endpoints = api_result.get('endpoints', [])
        result.websockets = api_result.get('websockets', [])
        result.grpc_services = api_result.get('grpc_services', [])
        result.graphql = api_result.get('graphql', [])

        # JVM framework elements via Java extractors
        self._extract_jvm_framework_elements(content, file_path, result)

        # Model extraction (JPA, Exposed, Room, serialization, DTOs)
        model_result = self.model_extractor.extract(content, file_path)
        existing_entity_names = set()
        for e in result.entities:
            if hasattr(e, 'name'):
                existing_entity_names.add(e.name)
            elif isinstance(e, dict):
                existing_entity_names.add(e.get('name', ''))
        for entity in model_result.get('entities', []):
            if entity.name not in existing_entity_names:
                result.entities.append(entity)
        existing_repo_names = set()
        for r in result.repositories:
            if hasattr(r, 'name'):
                existing_repo_names.add(r.name)
            elif isinstance(r, dict):
                existing_repo_names.add(r.get('name', ''))
        for repo in model_result.get('repositories', []):
            if repo.name not in existing_repo_names:
                result.repositories.append(repo)
        result.exposed_tables = model_result.get('exposed_tables', [])
        result.serializables = model_result.get('serializables', [])
        result.dtos = model_result.get('dtos', [])

        # Attribute extraction (annotations, DI, delegation, multiplatform, etc.)
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.annotation_defs = attr_result.get('annotation_defs', [])
        result.annotation_usages = attr_result.get('annotation_usages', [])
        result.delegations = attr_result.get('delegations', [])
        result.di_bindings = attr_result.get('di_bindings', [])
        result.multiplatform_decls = attr_result.get('multiplatform_decls', [])
        result.context_receivers = attr_result.get('context_receivers', [])
        result.contracts = attr_result.get('contracts', [])
        result.dsl_markers = attr_result.get('dsl_markers', [])

        return result

    def _extract_jvm_framework_elements(self, content, file_path, result):
        """Extract JVM framework elements using Java extractors as fallback."""
        try:
            java_api_result = self.java_api_extractor.extract(content, file_path)
            java_endpoints = java_api_result.get('endpoints', [])
            existing_paths = set()
            for ep in result.endpoints:
                if hasattr(ep, 'path'):
                    existing_paths.add(ep.path)
                elif isinstance(ep, dict):
                    existing_paths.add(ep.get('path', ''))
            for ep in java_endpoints:
                ep_path = ep.path if hasattr(ep, 'path') else ep.get('path', '')
                if ep_path not in existing_paths:
                    result.endpoints.append(ep)
        except Exception:
            pass

        try:
            java_model_result = self.java_model_extractor.extract(content, file_path)
            java_entities = java_model_result.get('entities', [])
            existing_entity_names = set()
            for e in result.entities:
                if hasattr(e, 'name'):
                    existing_entity_names.add(e.name)
                elif isinstance(e, dict):
                    existing_entity_names.add(e.get('name', ''))
            for entity in java_entities:
                name = entity.name if hasattr(entity, 'name') else entity.get('name', '')
                if name not in existing_entity_names:
                    result.entities.append(entity)
            java_repos = java_model_result.get('repositories', [])
            existing_repo_names = set()
            for r in result.repositories:
                if hasattr(r, 'name'):
                    existing_repo_names.add(r.name)
                elif isinstance(r, dict):
                    existing_repo_names.add(r.get('name', ''))
            for repo in java_repos:
                name = repo.name if hasattr(repo, 'name') else repo.get('name', '')
                if name not in existing_repo_names:
                    result.repositories.append(repo)
        except Exception:
            pass

    def _detect_frameworks(self, content):
        """Detect which frameworks are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_features(self, content):
        """Detect Kotlin-specific features used in the file."""
        features = []
        for feature, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                features.append(feature)
        return features

    def _detect_kotlin_version(self, content):
        """Detect minimum Kotlin version based on language features."""
        for version in ('2.1', '2.0', '1.9', '1.8', '1.7', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0'):
            patterns = self.KOTLIN_VERSION_FEATURES.get(version, [])
            for pattern in patterns:
                if pattern.search(content):
                    return version
        return ""

    def _detect_k2_compiler(self, content):
        """Detect if the project uses the K2 compiler."""
        for pattern in self.K2_INDICATORS:
            if pattern.search(content):
                return True
        return False

    # ============================================
    # AST Support (tree-sitter-kotlin)
    # ============================================

    def _ast_extract(self, content, result):
        """Use tree-sitter AST for precise extraction."""
        try:
            tree = self._ts_parser.parse(bytes(content, 'utf-8'))
            root = tree.root_node
            result.ast_available = True
            result.ast_node_count = self._count_nodes(root)
            self._ast_extract_classes(root, content, result)
            self._ast_extract_functions(root, content, result)
            logger.debug("AST: %d nodes", result.ast_node_count)
        except Exception as e:
            logger.debug("AST extraction failed: %s", e)

    def _ast_extract_classes(self, root, content, result):
        """Extract class definitions from AST nodes."""
        for node in self._find_nodes(root, 'class_declaration'):
            try:
                name_node = node.child_by_field_name('name')
                if not name_node:
                    for child in node.children:
                        if child.type in ('type_identifier', 'simple_identifier'):
                            name_node = child
                            break
                if not name_node:
                    continue
                name = content[name_node.start_byte:name_node.end_byte]
                modifiers = self._get_modifiers(node, content)
                kind = 'class'
                if 'data' in modifiers:
                    kind = 'data_class'
                elif 'sealed' in modifiers:
                    kind = 'sealed_class'
                elif 'abstract' in modifiers:
                    kind = 'abstract_class'
                elif 'annotation' in modifiers:
                    kind = 'annotation_class'
                elif 'value' in modifiers or 'inline' in modifiers:
                    kind = 'value_class'
                elif 'inner' in modifiers:
                    kind = 'inner_class'
                elif 'enum' in modifiers:
                    continue
                visibility = 'public'
                for mod in ('private', 'protected', 'internal'):
                    if mod in modifiers:
                        visibility = mod
                        break
                line = node.start_point[0] + 1
                existing = any(c.name == name and c.line_number == line for c in result.classes)
                if existing:
                    continue
                result.classes.append(KotlinClassInfo(
                    name=name, kind=kind, file=result.file_path, line_number=line,
                    is_exported=visibility in ('public', 'internal'),
                    is_sealed='sealed' in modifiers, is_data='data' in modifiers,
                    is_abstract='abstract' in modifiers, is_open='open' in modifiers,
                    is_inner='inner' in modifiers, visibility=visibility,
                ))
            except Exception:
                continue

    def _ast_extract_functions(self, root, content, result):
        """Extract function definitions from AST nodes."""
        for node in self._find_nodes(root, 'function_declaration'):
            try:
                name_node = node.child_by_field_name('name')
                if not name_node:
                    for child in node.children:
                        if child.type == 'simple_identifier':
                            name_node = child
                            break
                if not name_node:
                    continue
                name = content[name_node.start_byte:name_node.end_byte]
                line = node.start_point[0] + 1
                existing = any(f.name == name and f.line_number == line for f in result.functions)
                if existing:
                    continue
                modifiers = self._get_modifiers(node, content)
                visibility = 'public'
                for mod in ('private', 'protected', 'internal'):
                    if mod in modifiers:
                        visibility = mod
                        break
                result.functions.append(KotlinFunctionInfo(
                    name=name, is_suspend='suspend' in modifiers,
                    is_inline='inline' in modifiers, is_infix='infix' in modifiers,
                    is_operator='operator' in modifiers, is_tailrec='tailrec' in modifiers,
                    is_override='override' in modifiers,
                    is_private=visibility == 'private', is_internal=visibility == 'internal',
                    file=result.file_path, line_number=line,
                    is_exported=visibility in ('public', 'internal'),
                ))
            except Exception:
                continue

    def _find_nodes(self, node, node_type):
        """Recursively find all nodes of a given type."""
        results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            results.extend(self._find_nodes(child, node_type))
        return results

    def _get_modifiers(self, node, content):
        """Extract modifier keywords for a declaration node."""
        modifiers = []
        for child in node.children:
            if child.type in ('modifiers', 'modifier', 'visibility_modifier',
                             'class_modifier', 'member_modifier', 'function_modifier',
                             'property_modifier', 'inheritance_modifier',
                             'parameter_modifier', 'type_parameter_modifier'):
                mod_text = content[child.start_byte:child.end_byte]
                for mod in mod_text.split():
                    mod_clean = mod.strip()
                    if mod_clean and not mod_clean.startswith('@'):
                        modifiers.append(mod_clean)
        return modifiers

    def _count_nodes(self, node):
        """Count total AST nodes."""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count

    # ============================================
    # LSP Support (Kotlin Language Server)
    # ============================================

    def lsp_enhance(self, result, project_root):
        """Enhance parse result with Kotlin LSP data."""
        kls_path = self._find_kotlin_ls(project_root)
        if not kls_path:
            logger.debug("Kotlin Language Server not found")
            return result
        try:
            symbols = self._lsp_document_symbols(kls_path, result.file_path, project_root)
            if symbols:
                self._merge_lsp_symbols(result, symbols)
        except Exception as e:
            logger.debug("LSP enhancement failed: %s", e)
        return result

    def _find_kotlin_ls(self, project_root):
        """Find the Kotlin Language Server binary."""
        import shutil
        path_binary = shutil.which("kotlin-language-server")
        if path_binary:
            return path_binary
        candidates = [
            os.path.expanduser("~/.sdkman/candidates/kotlin-language-server/current/bin/kotlin-language-server"),
            "/usr/local/bin/kotlin-language-server",
            os.path.join(project_root, ".kotlin-language-server", "bin", "kotlin-language-server"),
            "/opt/homebrew/bin/kotlin-language-server",
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
        return None

    def _lsp_document_symbols(self, kls_path, file_path, project_root):
        """Get document symbols from Kotlin Language Server."""
        proc = None
        try:
            init_request = json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {
                    "processId": os.getpid(),
                    "rootUri": "file://" + project_root,
                    "capabilities": {
                        "textDocument": {"documentSymbol": {"hierarchicalDocumentSymbolSupport": True}}
                    }
                }
            })
            symbols_request = json.dumps({
                "jsonrpc": "2.0", "id": 2, "method": "textDocument/documentSymbol",
                "params": {"textDocument": {"uri": "file://" + file_path}}
            })
            proc = subprocess.Popen(
                [kls_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=project_root,
            )
            for req in [init_request, symbols_request]:
                header = "Content-Length: " + str(len(req)) + "\r\n\r\n"
                proc.stdin.write(header.encode() + req.encode())
                proc.stdin.flush()
            proc.stdin.close()
            output, _ = proc.communicate(timeout=10)
            responses = self._parse_lsp_responses(output.decode())
            for resp in responses:
                if resp.get('id') == 2:
                    return resp.get('result', [])
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.debug("LSP document symbols failed: %s", e)
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
        return None

    def _parse_lsp_responses(self, output):
        """Parse JSON-RPC responses from LSP output."""
        responses = []
        i = 0
        while i < len(output):
            header_end = output.find('\r\n\r\n', i)
            if header_end < 0:
                break
            header = output[i:header_end]
            length_match = re.search(r'Content-Length:\s*(\d+)', header)
            if not length_match:
                break
            content_length = int(length_match.group(1))
            body_start = header_end + 4
            body_end = body_start + content_length
            if body_end <= len(output):
                try:
                    response = json.loads(output[body_start:body_end])
                    responses.append(response)
                except json.JSONDecodeError:
                    pass
            i = body_end
        return responses

    def _merge_lsp_symbols(self, result, symbols):
        """Merge LSP document symbols into parse result."""
        for symbol in symbols:
            kind = symbol.get('kind', 0)
            name = symbol.get('name', '')
            if kind == 5:  # Class
                if not any(c.name == name for c in result.classes):
                    line = symbol.get('range', {}).get('start', {}).get('line', 0) + 1
                    result.classes.append(KotlinClassInfo(
                        name=name, file=result.file_path, line_number=line, is_exported=True,
                    ))
            elif kind == 11:  # Interface
                if not any(i.name == name for i in result.interfaces):
                    line = symbol.get('range', {}).get('start', {}).get('line', 0) + 1
                    result.interfaces.append(KotlinInterfaceInfo(
                        name=name, file=result.file_path, line_number=line, is_exported=True,
                    ))
            elif kind == 12:  # Function
                if not any(f.name == name for f in result.functions):
                    line = symbol.get('range', {}).get('start', {}).get('line', 0) + 1
                    result.functions.append(KotlinFunctionInfo(
                        name=name, file=result.file_path, line_number=line, is_exported=True,
                    ))
            children = symbol.get('children', [])
            if children:
                self._merge_lsp_symbols(result, children)
