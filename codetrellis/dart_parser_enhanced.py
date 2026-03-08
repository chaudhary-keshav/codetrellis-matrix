"""
EnhancedDartParser v1.0 - Comprehensive Dart parser using all extractors.

This parser integrates all Dart extractors to provide complete
parsing of Dart source files.

Supports:
- Core Dart types (classes, mixins, enums, extensions, extension types, typedefs)
- Functions, methods, constructors, getters/setters
- Flutter widgets (Stateless, Stateful, Inherited, RenderObject)
- Server-side frameworks (Shelf, Dart Frog, Serverpod, Conduit, Angel)
- State management (Riverpod, Bloc, Cubit, GetX, Provider, MobX)
- Database/ORM (Drift, Floor, Isar, Hive, ObjectBox)
- Data classes (Freezed, JsonSerializable, Built Value, Equatable)
- gRPC service implementations
- Platform channels (MethodChannel, EventChannel)
- Isolate/compute concurrency
- Code generation annotations
- Null safety analysis
- Dart 3.0+ features (sealed, records, patterns, class modifiers, extension types)

Dart version detection from pubspec.yaml:
- sdk constraint (e.g., '>=3.0.0 <4.0.0')
- Flutter SDK constraint
- Environment declarations

Framework detection (70+ frameworks):
- Flutter: Material, Cupertino, widgets, animation, gestures
- State: Riverpod, Bloc, GetX, Provider, MobX, Redux
- Networking: Dio, http, Chopper, Retrofit, GraphQL
- Database: Drift/Moor, Floor, Isar, Hive, ObjectBox, Firebase
- Serialization: Freezed, JsonSerializable, Built Value
- DI: GetIt, Injectable, Riverpod
- Navigation: GoRouter, AutoRoute, Fluro, Beamer
- Testing: flutter_test, mockito, bloc_test
- Server: shelf, dart_frog, serverpod, conduit, angel

Optional AST support via tree-sitter (when available).
Optional LSP support via Dart Analysis Server (when available).

Part of CodeTrellis v4.27 - Dart Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Dart extractors
from .extractors.dart import (
    DartTypeExtractor, DartClassInfo, DartMixinInfo, DartEnumInfo,
    DartEnumCaseInfo, DartExtensionInfo, DartTypedefInfo, DartFieldInfo,
    DartFunctionExtractor, DartFunctionInfo, DartMethodInfo,
    DartConstructorInfo, DartParameterInfo,
    DartAPIExtractor, DartWidgetInfo, DartRouteInfo, DartStateInfo,
    DartGRPCServiceInfo,
    DartModelExtractor, DartModelInfo, DartDataClassInfo, DartMigrationInfo,
    DartAttributeExtractor, DartAnnotationInfo, DartImportInfo,
    DartPartInfo, DartIsolateInfo, DartPlatformChannelInfo,
)


@dataclass
class DartParseResult:
    """Complete parse result for a Dart file."""
    file_path: str
    file_type: str = "dart"

    # Library/package info
    library_name: str = ""
    package_name: str = ""

    # Core types
    classes: List[DartClassInfo] = field(default_factory=list)
    mixins: List[DartMixinInfo] = field(default_factory=list)
    enums: List[DartEnumInfo] = field(default_factory=list)
    extensions: List[DartExtensionInfo] = field(default_factory=list)
    extension_types: List[DartExtensionInfo] = field(default_factory=list)
    typedefs: List[DartTypedefInfo] = field(default_factory=list)

    # Functions and methods
    functions: List[DartFunctionInfo] = field(default_factory=list)
    constructors: List[DartConstructorInfo] = field(default_factory=list)
    getters: List[DartMethodInfo] = field(default_factory=list)
    setters: List[DartMethodInfo] = field(default_factory=list)

    # API/Framework elements
    widgets: List[DartWidgetInfo] = field(default_factory=list)
    routes: List[DartRouteInfo] = field(default_factory=list)
    state_managers: List[DartStateInfo] = field(default_factory=list)
    grpc_services: List[DartGRPCServiceInfo] = field(default_factory=list)
    flutter_routes: List[DartRouteInfo] = field(default_factory=list)

    # Database models
    models: List[DartModelInfo] = field(default_factory=list)
    data_classes: List[DartDataClassInfo] = field(default_factory=list)
    migrations: List[DartMigrationInfo] = field(default_factory=list)

    # Attributes / meta
    annotations: List[DartAnnotationInfo] = field(default_factory=list)
    imports: List[DartImportInfo] = field(default_factory=list)
    exports: List[DartImportInfo] = field(default_factory=list)
    parts: List[DartPartInfo] = field(default_factory=list)
    isolates: List[DartIsolateInfo] = field(default_factory=list)
    platform_channels: List[DartPlatformChannelInfo] = field(default_factory=list)
    null_safety: Dict[str, int] = field(default_factory=dict)
    dart3_features: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    import_uris: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)
    dart_version: str = ""
    flutter_version: str = ""
    is_flutter: bool = False


class EnhancedDartParser:
    """
    Enhanced Dart parser that uses all extractors for comprehensive parsing.

    Framework detection supports 70+ frameworks across:
    - Flutter UI frameworks (Material, Cupertino, widgets)
    - State management (Riverpod, Bloc, GetX, Provider, MobX, Redux)
    - Networking (Dio, http, Chopper, Retrofit)
    - Database/ORM (Drift, Floor, Isar, Hive, ObjectBox, Firebase)
    - Serialization (Freezed, JsonSerializable, Built Value)
    - DI (GetIt, Injectable)
    - Navigation (GoRouter, AutoRoute, Fluro, Beamer)
    - Testing (flutter_test, mockito, bloc_test, patrol)
    - Server-side (shelf, dart_frog, serverpod, conduit, angel)
    - Build tools (build_runner, dart_code_metrics)

    Optional AST: tree-sitter (pip install tree-sitter)
    Optional LSP: Dart Analysis Server (dart language-server)
    """

    # Import pattern
    IMPORT_PATTERN = re.compile(
        r"^\s*import\s+['\"](?P<uri>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Flutter Core
        'flutter': re.compile(r"import\s+['\"]package:flutter/"),
        'flutter_material': re.compile(r"import\s+['\"]package:flutter/material\.dart['\"]"),
        'flutter_cupertino': re.compile(r"import\s+['\"]package:flutter/cupertino\.dart['\"]"),
        'flutter_widgets': re.compile(r"import\s+['\"]package:flutter/widgets\.dart['\"]"),
        # State Management
        'riverpod': re.compile(r"import\s+['\"]package:(?:flutter_)?riverpod/|@riverpod\b|@Riverpod\b"),
        'bloc': re.compile(r"import\s+['\"]package:(?:flutter_)?bloc/|extends\s+(?:Bloc|Cubit)<"),
        'getx': re.compile(r"import\s+['\"]package:get/|extends\s+GetxController\b"),
        'provider': re.compile(r"import\s+['\"]package:provider/"),
        'mobx': re.compile(r"import\s+['\"]package:(?:flutter_)?mobx/|_\$\w+"),
        'redux': re.compile(r"import\s+['\"]package:(?:flutter_)?redux/"),
        'signals': re.compile(r"import\s+['\"]package:signals/"),
        # Networking
        'dio': re.compile(r"import\s+['\"]package:dio/"),
        'http': re.compile(r"import\s+['\"]package:http/"),
        'chopper': re.compile(r"import\s+['\"]package:chopper/"),
        'retrofit': re.compile(r"import\s+['\"]package:retrofit/"),
        'graphql': re.compile(r"import\s+['\"]package:graphql(?:_flutter)?/"),
        'ferry': re.compile(r"import\s+['\"]package:ferry/"),
        'websocket': re.compile(r"import\s+['\"]package:web_socket_channel/|WebSocket\b"),
        # Database/Storage
        'drift': re.compile(r"import\s+['\"]package:drift/|extends\s+Table\b"),
        'floor': re.compile(r"import\s+['\"]package:floor/|@Entity\b.*@dao\b"),
        'isar': re.compile(r"import\s+['\"]package:isar/|@collection\b"),
        'hive': re.compile(r"import\s+['\"]package:hive(?:_flutter)?/|@HiveType\b"),
        'objectbox': re.compile(r"import\s+['\"]package:objectbox/"),
        'sqflite': re.compile(r"import\s+['\"]package:sqflite/"),
        'shared_preferences': re.compile(r"import\s+['\"]package:shared_preferences/"),
        'firebase_core': re.compile(r"import\s+['\"]package:firebase_core/"),
        'cloud_firestore': re.compile(r"import\s+['\"]package:cloud_firestore/"),
        'firebase_auth': re.compile(r"import\s+['\"]package:firebase_auth/"),
        'firebase_storage': re.compile(r"import\s+['\"]package:firebase_storage/"),
        'firebase_messaging': re.compile(r"import\s+['\"]package:firebase_messaging/"),
        'firebase_analytics': re.compile(r"import\s+['\"]package:firebase_analytics/"),
        'supabase': re.compile(r"import\s+['\"]package:supabase(?:_flutter)?/"),
        'appwrite': re.compile(r"import\s+['\"]package:appwrite/"),
        # Serialization / Code Gen
        'freezed': re.compile(r"import\s+['\"]package:freezed_annotation/|@freezed\b|@Freezed\b"),
        'json_serializable': re.compile(r"import\s+['\"]package:json_annotation/|@JsonSerializable\b"),
        'built_value': re.compile(r"import\s+['\"]package:built_value/"),
        'json_annotation': re.compile(r"import\s+['\"]package:json_annotation/"),
        'equatable': re.compile(r"import\s+['\"]package:equatable/|extends\s+Equatable\b"),
        'copy_with': re.compile(r"import\s+['\"]package:copy_with_extension/"),
        # DI
        'get_it': re.compile(r"import\s+['\"]package:get_it/"),
        'injectable': re.compile(r"import\s+['\"]package:injectable/|@injectable\b|@Injectable\b"),
        # Navigation
        'go_router': re.compile(r"import\s+['\"]package:go_router/|GoRoute\b|GoRouter\b"),
        'auto_route': re.compile(r"import\s+['\"]package:auto_route/|@RoutePage\b|@MaterialRoute\b"),
        'fluro': re.compile(r"import\s+['\"]package:fluro/"),
        'beamer': re.compile(r"import\s+['\"]package:beamer/"),
        # Testing
        'flutter_test': re.compile(r"import\s+['\"]package:flutter_test/"),
        'test': re.compile(r"import\s+['\"]package:test/"),
        'mockito': re.compile(r"import\s+['\"]package:mockito/|@GenerateMocks\b"),
        'mocktail': re.compile(r"import\s+['\"]package:mocktail/"),
        'bloc_test': re.compile(r"import\s+['\"]package:bloc_test/"),
        'patrol': re.compile(r"import\s+['\"]package:patrol/"),
        'integration_test': re.compile(r"import\s+['\"]package:integration_test/"),
        'golden_toolkit': re.compile(r"import\s+['\"]package:golden_toolkit/"),
        # Server-side
        'shelf': re.compile(r"import\s+['\"]package:shelf/"),
        'shelf_router': re.compile(r"import\s+['\"]package:shelf_router/"),
        'dart_frog': re.compile(r"import\s+['\"]package:dart_frog/"),
        'serverpod': re.compile(r"import\s+['\"]package:serverpod/"),
        'conduit': re.compile(r"import\s+['\"]package:conduit(?:_core)?/"),
        'angel': re.compile(r"import\s+['\"]package:angel(?:3)?_framework/"),
        # gRPC
        'grpc': re.compile(r"import\s+['\"]package:grpc/|extends\s+\w+ServiceBase\b"),
        'protobuf': re.compile(r"import\s+['\"]package:protobuf/|GeneratedMessage\b"),
        # Build Tools
        'build_runner': re.compile(r"import\s+['\"]package:build_runner/"),
        'source_gen': re.compile(r"import\s+['\"]package:source_gen/"),
        # Utilities
        'intl': re.compile(r"import\s+['\"]package:intl/"),
        'path': re.compile(r"import\s+['\"]package:path/"),
        'collection': re.compile(r"import\s+['\"]package:collection/"),
        'rxdart': re.compile(r"import\s+['\"]package:rxdart/"),
        'dartz': re.compile(r"import\s+['\"]package:dartz/"),
        'fpdart': re.compile(r"import\s+['\"]package:fpdart/"),
        # Platform
        'camera': re.compile(r"import\s+['\"]package:camera/"),
        'geolocator': re.compile(r"import\s+['\"]package:geolocator/"),
        'permission_handler': re.compile(r"import\s+['\"]package:permission_handler/"),
        'url_launcher': re.compile(r"import\s+['\"]package:url_launcher/"),
        'flutter_local_notifications': re.compile(r"import\s+['\"]package:flutter_local_notifications/"),
        'in_app_purchase': re.compile(r"import\s+['\"]package:in_app_purchase/"),
    }

    # Pubspec.yaml SDK constraint pattern
    SDK_CONSTRAINT_PATTERN = re.compile(
        r"sdk:\s*['\"]?(?:>=?\s*)?(?P<min>\d+\.\d+\.\d+)",
    )

    # Flutter SDK constraint
    FLUTTER_CONSTRAINT_PATTERN = re.compile(
        r"flutter:\s*['\"]?(?:>=?\s*)?(?P<min>\d+\.\d+\.\d+)",
    )

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = DartTypeExtractor()
        self.function_extractor = DartFunctionExtractor()
        self.api_extractor = DartAPIExtractor()
        self.model_extractor = DartModelExtractor()
        self.attribute_extractor = DartAttributeExtractor()

        # Optional AST support via tree-sitter
        self._tree_sitter_available = False
        try:
            from tree_sitter import Language, Parser as TSParser
            # Try to load dart grammar if available
            try:
                import tree_sitter_dart
                self._dart_language = Language(tree_sitter_dart.language())
                self._ts_parser = TSParser(self._dart_language)
                self._tree_sitter_available = True
            except (ImportError, Exception):
                pass
        except (ImportError, Exception):
            pass

        # Optional LSP support via Dart Analysis Server
        self._lsp_available = False
        try:
            from .lsp_client import LSPClient
            self._lsp_client_class = LSPClient
            self._lsp_available = True
        except (ImportError, Exception):
            pass

    def parse(self, content: str, file_path: str = "") -> DartParseResult:
        """
        Parse Dart source code and extract all information.

        Args:
            content: Dart source code content
            file_path: Path to source file

        Returns:
            DartParseResult with all extracted information
        """
        result = DartParseResult(file_path=file_path)

        # Extract package/library name
        result.library_name = self._detect_library_name(content)
        result.package_name = self._detect_package_name(file_path)

        # Extract import URIs
        result.import_uris = self._extract_import_uris(content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect if Flutter project
        result.is_flutter = any(
            fw.startswith('flutter') for fw in result.detected_frameworks
        ) or any('package:flutter/' in uri for uri in result.import_uris)

        # If tree-sitter is available, use AST for enhanced extraction
        if self._tree_sitter_available:
            self._enhance_with_ast(content, result)

        # Extract types (classes, mixins, enums, extensions, typedefs)
        type_result = self.type_extractor.extract(content, file_path)
        result.classes = type_result.get('classes', [])
        result.mixins = type_result.get('mixins', [])
        result.enums = type_result.get('enums', [])
        result.extensions = type_result.get('extensions', [])
        result.extension_types = type_result.get('extension_types', [])
        result.typedefs = type_result.get('typedefs', [])

        # Extract functions, constructors, getters, setters
        func_result = self.function_extractor.extract(content, file_path)
        result.functions = func_result.get('functions', [])
        result.constructors = func_result.get('constructors', [])
        result.getters = func_result.get('getters', [])
        result.setters = func_result.get('setters', [])

        # Extract API patterns (widgets, routes, state managers, gRPC)
        api_result = self.api_extractor.extract(content, file_path)
        result.widgets = api_result.get('widgets', [])
        result.routes = api_result.get('routes', [])
        result.state_managers = api_result.get('state_managers', [])
        result.grpc_services = api_result.get('grpc_services', [])
        result.flutter_routes = api_result.get('flutter_routes', [])

        # Extract models (ORM models, data classes, migrations)
        model_result = self.model_extractor.extract(content, file_path)
        result.models = model_result.get('models', [])
        result.data_classes = model_result.get('data_classes', [])
        result.migrations = model_result.get('migrations', [])

        # Extract attributes (annotations, imports, exports, parts, isolates, channels)
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.annotations = attr_result.get('annotations', [])
        result.imports = attr_result.get('imports', [])
        result.exports = attr_result.get('exports', [])
        result.parts = attr_result.get('parts', [])
        result.isolates = attr_result.get('isolates', [])
        result.platform_channels = attr_result.get('platform_channels', [])
        result.null_safety = attr_result.get('null_safety', {})
        result.dart3_features = attr_result.get('dart3_features', {})

        return result

    def _detect_library_name(self, content: str) -> str:
        """Detect library name from library directive."""
        match = re.search(r'^\s*library\s+(\w+(?:\.\w+)*)\s*;', content, re.MULTILINE)
        if match:
            return match.group(1)
        return ""

    def _detect_package_name(self, file_path: str) -> str:
        """Detect package name from file path."""
        if not file_path:
            return ""
        path = Path(file_path)
        # Check for lib/ directory (Dart convention)
        parts = path.parts
        for i, part in enumerate(parts):
            if part == 'lib' and i > 0:
                return parts[i - 1]
        return path.stem

    def _extract_import_uris(self, content: str) -> List[str]:
        """Extract import URIs from the file."""
        uris = []
        for match in self.IMPORT_PATTERN.finditer(content):
            uri = match.group('uri')
            if uri not in uris:
                uris.append(uri)
        return uris

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Dart/Flutter frameworks are used in the file."""
        frameworks = []
        for fw_name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(fw_name)
        return frameworks

    def _enhance_with_ast(self, content: str, result: DartParseResult):
        """Use tree-sitter AST for enhanced extraction if available."""
        if not self._tree_sitter_available:
            return
        try:
            tree = self._ts_parser.parse(bytes(content, 'utf-8'))
            root = tree.root_node

            # AST-enhanced: Extract class declarations with precise positions
            self._ast_extract_classes(root, content, result)
            # AST-enhanced: Extract function signatures with precise params
            self._ast_extract_functions(root, content, result)
            # AST-enhanced: Extract enum cases with associated values
            self._ast_extract_enums(root, content, result)
        except Exception:
            pass  # Fallback to regex extraction

    def _ast_extract_classes(self, root_node, content: str, result: DartParseResult):
        """AST-enhanced class extraction."""
        for node in self._find_nodes(root_node, 'class_definition'):
            name_node = self._find_child(node, 'identifier')
            if name_node:
                name = content[name_node.start_byte:name_node.end_byte]
                for cls in result.classes:
                    if cls.name == name:
                        cls.line_number = node.start_point[0] + 1
                        break

    def _ast_extract_functions(self, root_node, content: str, result: DartParseResult):
        """AST-enhanced function extraction."""
        for node in self._find_nodes(root_node, 'function_signature'):
            name_node = self._find_child(node, 'identifier')
            if name_node:
                name = content[name_node.start_byte:name_node.end_byte]
                for func in result.functions:
                    if func.name == name:
                        func.line_number = node.start_point[0] + 1
                        break

    def _ast_extract_enums(self, root_node, content: str, result: DartParseResult):
        """AST-enhanced enum extraction."""
        for node in self._find_nodes(root_node, 'enum_declaration'):
            name_node = self._find_child(node, 'identifier')
            if name_node:
                name = content[name_node.start_byte:name_node.end_byte]
                for enum in result.enums:
                    if enum.name == name:
                        enum.line_number = node.start_point[0] + 1
                        break

    def _find_nodes(self, root, node_type: str):
        """Recursively find all nodes of a given type."""
        results = []
        if root.type == node_type:
            results.append(root)
        for child in root.children:
            results.extend(self._find_nodes(child, node_type))
        return results

    def _find_child(self, node, child_type: str):
        """Find first child of a given type."""
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    @staticmethod
    def parse_pubspec(content: str) -> Dict[str, Any]:
        """
        Parse pubspec.yaml to extract dependency and configuration information.

        Args:
            content: pubspec.yaml file content

        Returns:
            Dict with 'name', 'dart_sdk', 'flutter_sdk', 'dependencies',
            'dev_dependencies', 'is_flutter'
        """
        result: Dict[str, Any] = {
            'name': '',
            'description': '',
            'version': '',
            'dart_sdk': '',
            'flutter_sdk': '',
            'dependencies': [],
            'dev_dependencies': [],
            'is_flutter': False,
        }

        # Extract name
        name_match = re.search(r'^name:\s*(\S+)', content, re.MULTILINE)
        if name_match:
            result['name'] = name_match.group(1).strip().strip("'\"")

        # Extract version
        version_match = re.search(r'^version:\s*(\S+)', content, re.MULTILINE)
        if version_match:
            result['version'] = version_match.group(1).strip().strip("'\"")

        # Extract description
        desc_match = re.search(r'^description:\s*(.+)', content, re.MULTILINE)
        if desc_match:
            result['description'] = desc_match.group(1).strip().strip("'\"")

        # Extract SDK constraint
        sdk_match = re.search(
            r'sdk:\s*["\']?(?:>=?\s*)?(\d+\.\d+\.\d+)',
            content
        )
        if sdk_match:
            result['dart_sdk'] = sdk_match.group(1)

        # Extract Flutter SDK constraint
        flutter_sdk_match = re.search(
            r'flutter:\s*["\']?(?:>=?\s*)?(\d+\.\d+\.\d+)',
            content
        )
        if flutter_sdk_match:
            result['flutter_sdk'] = flutter_sdk_match.group(1)

        # Check if Flutter project
        result['is_flutter'] = bool(re.search(
            r'^\s*flutter:\s*$|dependencies:\s*\n(?:.*\n)*?\s+flutter:',
            content, re.MULTILINE
        ))

        # Extract dependencies section
        dep_section = re.search(
            r'^dependencies:\s*\n((?:\s+[^\n]+\n)*)',
            content, re.MULTILINE
        )
        if dep_section:
            for dep_match in re.finditer(
                r'^\s+(\w[\w_]*)\s*:', dep_section.group(1), re.MULTILINE
            ):
                dep_name = dep_match.group(1)
                if dep_name not in ('sdk', 'flutter', 'path', 'git', 'hosted'):
                    result['dependencies'].append(dep_name)

        # Extract dev_dependencies section
        dev_dep_section = re.search(
            r'^dev_dependencies:\s*\n((?:\s+[^\n]+\n)*)',
            content, re.MULTILINE
        )
        if dev_dep_section:
            for dep_match in re.finditer(
                r'^\s+(\w[\w_]*)\s*:', dev_dep_section.group(1), re.MULTILINE
            ):
                dep_name = dep_match.group(1)
                if dep_name not in ('sdk', 'flutter', 'path', 'git', 'hosted'):
                    result['dev_dependencies'].append(dep_name)

        return result
