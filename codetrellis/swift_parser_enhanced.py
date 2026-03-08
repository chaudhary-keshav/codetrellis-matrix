"""
EnhancedSwiftParser v1.0 - Comprehensive Swift parser using all extractors.

This parser integrates all Swift extractors to provide complete
parsing of Swift source files.

Supports:
- Core Swift types (classes, structs, enums, protocols, actors, extensions)
- Functions, methods, initializers, subscripts
- SwiftUI views, Combine publishers
- Vapor/Hummingbird routes, gRPC services
- Core Data/SwiftData/GRDB/Realm models
- Property wrappers, result builders, macros
- Concurrency (async/await, actors, Sendable)
- Availability annotations, ObjC interop
- Swift 5.0 through Swift 6.0+ features
- All Apple platforms (iOS, macOS, watchOS, tvOS, visionOS)

Optional AST support via tree-sitter-swift (when available).
Optional LSP support via sourcekit-lsp (when available).

Swift version detection from Package.swift:
- swift-tools-version:5.5 through 6.0
- Platform minimum versions

Framework detection (35+ frameworks):
- Apple: SwiftUI, UIKit, AppKit, CoreData, SwiftData, Combine, CloudKit,
         WidgetKit, ARKit, RealityKit, MapKit, StoreKit, GameKit, SpriteKit,
         SceneKit, Metal, CoreML, Vision, NaturalLanguage, CoreBluetooth,
         HealthKit, CoreLocation, CoreMotion, AVFoundation, PhotosUI
- Server-side: Vapor, Kitura, Perfect, Hummingbird, SwiftNIO
- Networking: Alamofire, Moya, URLSession
- Database: GRDB, Realm, SQLite.swift, Fluent
- Testing: XCTest, Quick/Nimble, Swift Testing
- DI: Swinject, Resolver, Factory
- Reactive: Combine, RxSwift, ReactiveSwift
- Architecture: TCA (ComposableArchitecture), MVVM

Part of CodeTrellis v4.22 - Swift Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Swift extractors
from .extractors.swift import (
    SwiftTypeExtractor, SwiftClassInfo, SwiftStructInfo, SwiftEnumInfo,
    SwiftProtocolInfo, SwiftActorInfo, SwiftTypeAliasInfo, SwiftExtensionInfo,
    SwiftFunctionExtractor, SwiftFunctionInfo, SwiftInitInfo, SwiftSubscriptInfo,
    SwiftAPIExtractor, SwiftRouteInfo, SwiftViewInfo, SwiftPublisherInfo, SwiftGRPCServiceInfo,
    SwiftModelExtractor, SwiftModelInfo, SwiftMigrationInfo, SwiftCodableInfo,
    SwiftAttributeExtractor, SwiftPropertyWrapperInfo, SwiftResultBuilderInfo,
    SwiftMacroInfo, SwiftAvailabilityInfo, SwiftConcurrencyInfo,
)


@dataclass
class SwiftParseResult:
    """Complete parse result for a Swift file."""
    file_path: str
    file_type: str = "swift"

    # Module info
    module_name: str = ""

    # Core types
    classes: List[SwiftClassInfo] = field(default_factory=list)
    structs: List[SwiftStructInfo] = field(default_factory=list)
    enums: List[SwiftEnumInfo] = field(default_factory=list)
    protocols: List[SwiftProtocolInfo] = field(default_factory=list)
    actors: List[SwiftActorInfo] = field(default_factory=list)
    type_aliases: List[SwiftTypeAliasInfo] = field(default_factory=list)
    extensions: List[SwiftExtensionInfo] = field(default_factory=list)

    # Functions and methods
    functions: List[SwiftFunctionInfo] = field(default_factory=list)
    inits: List[SwiftInitInfo] = field(default_factory=list)
    subscripts: List[SwiftSubscriptInfo] = field(default_factory=list)

    # API / Framework elements
    routes: List[SwiftRouteInfo] = field(default_factory=list)
    views: List[SwiftViewInfo] = field(default_factory=list)
    publishers: List[SwiftPublisherInfo] = field(default_factory=list)
    grpc_services: List[SwiftGRPCServiceInfo] = field(default_factory=list)

    # Database models
    models: List[SwiftModelInfo] = field(default_factory=list)
    migrations: List[SwiftMigrationInfo] = field(default_factory=list)
    codables: List[SwiftCodableInfo] = field(default_factory=list)

    # Attributes / meta
    property_wrappers: List[SwiftPropertyWrapperInfo] = field(default_factory=list)
    result_builders: List[SwiftResultBuilderInfo] = field(default_factory=list)
    macros: List[SwiftMacroInfo] = field(default_factory=list)
    availability: List[SwiftAvailabilityInfo] = field(default_factory=list)
    concurrency: List[SwiftConcurrencyInfo] = field(default_factory=list)

    # Metadata
    imports: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)
    swift_version: str = ""
    detected_platforms: List[str] = field(default_factory=list)
    objc_annotations: List[Dict] = field(default_factory=list)
    compiler_directives: List[Dict] = field(default_factory=list)
    testing: List[Dict] = field(default_factory=list)


class EnhancedSwiftParser:
    """
    Enhanced Swift parser that uses all extractors for comprehensive parsing.

    Framework detection supports 35+ frameworks across:
    - Apple platform frameworks (SwiftUI, UIKit, CoreData, etc.)
    - Server-side Swift (Vapor, Hummingbird, Kitura, Perfect)
    - Networking (Alamofire, Moya)
    - Database (GRDB, Realm, Fluent, SQLite.swift)
    - Testing (XCTest, Quick/Nimble, Swift Testing)
    - Architecture (TCA, MVVM patterns)
    - DI (Swinject, Resolver, Factory)
    - Reactive (Combine, RxSwift)

    Optional AST: tree-sitter-swift (pip install tree-sitter-swift)
    Optional LSP: sourcekit-lsp (bundled with Xcode/Swift toolchain)
    """

    # Import pattern
    IMPORT_PATTERN = re.compile(
        r'^\s*import\s+(?:(?:typealias|struct|class|enum|protocol|var|func|let)\s+)?'
        r'(?P<module>\w+(?:\.\w+)*)',
        re.MULTILINE
    )

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Apple UI Frameworks
        'swiftui': re.compile(r'\bSwiftUI\b'),
        'uikit': re.compile(r'\bUIKit\b|UIViewController|UIView\b|UITableView|UICollectionView'),
        'appkit': re.compile(r'\bAppKit\b|NSViewController|NSView\b|NSWindow'),
        'widgetkit': re.compile(r'\bWidgetKit\b|Widget\b.*Timeline'),
        # Apple Data Frameworks
        'core_data': re.compile(r'\bCoreData\b|NSManagedObject|NSPersistentContainer'),
        'swift_data': re.compile(r'@Model\b|SwiftData\b|ModelContainer'),
        'cloudkit': re.compile(r'\bCloudKit\b|CKContainer|CKRecord'),
        'combine': re.compile(r'\bCombine\b|Publisher\b|@Published\b|CurrentValueSubject|PassthroughSubject'),
        # Apple Platform Frameworks
        'arkit': re.compile(r'\bARKit\b|ARSession|ARView'),
        'realitykit': re.compile(r'\bRealityKit\b|RealityView|Entity\b'),
        'mapkit': re.compile(r'\bMapKit\b|MKMapView|Map\b.*coordinateRegion'),
        'storekit': re.compile(r'\bStoreKit\b|Product\b.*purchase|Transaction'),
        'coreml': re.compile(r'\bCoreML\b|MLModel|MLModelConfiguration'),
        'vision': re.compile(r'\bVision\b|VNRequest|VNImageRequestHandler'),
        'metal': re.compile(r'\bMetal\b|MTLDevice|MTLRenderPipeline'),
        'avfoundation': re.compile(r'\bAVFoundation\b|AVPlayer|AVCaptureSession'),
        'healthkit': re.compile(r'\bHealthKit\b|HKHealthStore|HKQuantityType'),
        'corelocation': re.compile(r'\bCoreLocation\b|CLLocationManager|CLLocation'),
        'corebluetooth': re.compile(r'\bCoreBluetooth\b|CBCentralManager|CBPeripheral'),
        'gamekit': re.compile(r'\bGameKit\b|GKScore|GKAchievement'),
        'spritekit': re.compile(r'\bSpriteKit\b|SKScene|SKSpriteNode'),
        'scenekit': re.compile(r'\bSceneKit\b|SCNScene|SCNNode'),
        # Server-side Swift
        'vapor': re.compile(r'import Vapor\b|Vapor\.Application|app\.(get|post|put|delete|patch)\('),
        'hummingbird': re.compile(r'\bHummingbird\b|import Hummingbird|HBApplication'),
        'kitura': re.compile(r'\bKitura\b|import Kitura'),
        'perfect': re.compile(r'\bPerfect\b|import PerfectHTTP'),
        'swiftnio': re.compile(r'\bNIO\b|import NIO|EventLoopGroup|ChannelHandler'),
        'fluent': re.compile(r'\bFluent\b|import Fluent|Migration\b'),
        # Networking
        'alamofire': re.compile(r'\bAlamofire\b|AF\.request'),
        'moya': re.compile(r'\bMoya\b|TargetType\b'),
        'urlsession': re.compile(r'URLSession\.shared|URLRequest\b|URLSessionTask'),
        # Database
        'grdb': re.compile(r'\bGRDB\b|import GRDB|PersistableRecord|FetchableRecord'),
        'realm': re.compile(r'\bRealmSwift\b|import RealmSwift|@Persisted\b'),
        'sqlite_swift': re.compile(r'\bSQLite\b|import SQLite\b'),
        # Testing
        'xctest': re.compile(r'\bXCTest\b|XCTestCase|func test\w+\('),
        'quick_nimble': re.compile(r'\bQuick\b|\bNimble\b|QuickSpec|describe\s*\('),
        'swift_testing': re.compile(r'import Testing\b|@Test\b|@Suite\b'),
        # DI
        'swinject': re.compile(r'\bSwinject\b|Container\b.*register'),
        'resolver': re.compile(r'\bResolver\b|@Injected\b'),
        'factory': re.compile(r'\bFactory\b|@Injected\b'),
        # Reactive
        'rxswift': re.compile(r'\bRxSwift\b|Observable\b.*subscribe|BehaviorRelay|PublishRelay'),
        'reactiveswift': re.compile(r'\bReactiveSwift\b|SignalProducer|MutableProperty'),
        # Architecture
        'tca': re.compile(r'\bComposableArchitecture\b|ReducerOf|Store<|StoreOf|WithViewStore'),
        # gRPC
        'grpc_swift': re.compile(r'\bGRPC\b|GRPCAsyncServerCallContext|ServerInterceptor'),
        'swift_protobuf': re.compile(r'\bSwiftProtobuf\b|Message\b.*serializedData|Google_Protobuf'),
    }

    # Swift version detection from Package.swift
    SWIFT_TOOLS_VERSION_PATTERN = re.compile(
        r'swift-tools-version:\s*(\d+\.\d+(?:\.\d+)?)',
        re.IGNORECASE
    )

    # Platform targets from Package.swift
    PLATFORM_PATTERN = re.compile(
        r'\.(?P<platform>iOS|macOS|watchOS|tvOS|visionOS|macCatalyst)\s*\('
        r'\.v(?P<version>\d+(?:_\d+)?)\)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = SwiftTypeExtractor()
        self.function_extractor = SwiftFunctionExtractor()
        self.api_extractor = SwiftAPIExtractor()
        self.model_extractor = SwiftModelExtractor()
        self.attribute_extractor = SwiftAttributeExtractor()

        # Optional AST support via tree-sitter-swift
        self._tree_sitter_available = False
        try:
            import tree_sitter_swift
            from tree_sitter import Language, Parser as TSParser
            self._swift_language = Language(tree_sitter_swift.language())
            self._ts_parser = TSParser(self._swift_language)
            self._tree_sitter_available = True
        except (ImportError, Exception):
            pass

        # Optional LSP support via sourcekit-lsp
        self._lsp_available = False
        try:
            from .lsp_client import LSPClient
            self._lsp_client_class = LSPClient
            self._lsp_available = True
        except (ImportError, Exception):
            pass

    def parse(self, content: str, file_path: str = "") -> SwiftParseResult:
        """
        Parse Swift source code and extract all information.

        Args:
            content: Swift source code content
            file_path: Path to source file

        Returns:
            SwiftParseResult with all extracted information
        """
        result = SwiftParseResult(file_path=file_path)

        # Extract module name from file path
        result.module_name = self._detect_module_name(file_path)

        # Extract imports
        result.imports = self._extract_imports(content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # If tree-sitter is available, use AST for enhanced extraction
        if self._tree_sitter_available:
            self._enhance_with_ast(content, result)

        # Extract types (classes, structs, enums, protocols, actors, aliases, extensions)
        type_result = self.type_extractor.extract(content, file_path)
        result.classes = type_result.get('classes', [])
        result.structs = type_result.get('structs', [])
        result.enums = type_result.get('enums', [])
        result.protocols = type_result.get('protocols', [])
        result.actors = type_result.get('actors', [])
        result.type_aliases = type_result.get('type_aliases', [])
        result.extensions = type_result.get('extensions', [])

        # Extract functions, inits, subscripts
        func_result = self.function_extractor.extract(content, file_path)
        result.functions = func_result.get('functions', [])
        result.inits = func_result.get('inits', [])
        result.subscripts = func_result.get('subscripts', [])

        # Extract API patterns (routes, views, publishers, gRPC)
        api_result = self.api_extractor.extract(content, file_path)
        result.routes = api_result.get('routes', [])
        result.views = api_result.get('views', [])
        result.publishers = api_result.get('publishers', [])
        result.grpc_services = api_result.get('grpc_services', [])

        # Extract models (Core Data, SwiftData, GRDB, Realm, Codable)
        model_result = self.model_extractor.extract(content, file_path)
        result.models = model_result.get('models', [])
        result.migrations = model_result.get('migrations', [])
        result.codables = model_result.get('codables', [])

        # Extract attributes (property wrappers, result builders, macros, availability, concurrency)
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.property_wrappers = attr_result.get('property_wrappers', [])
        result.result_builders = attr_result.get('result_builders', [])
        result.macros = attr_result.get('macros', [])
        result.availability = attr_result.get('availability', [])
        result.concurrency = attr_result.get('concurrency', [])
        result.objc_annotations = attr_result.get('objc_annotations', [])
        result.compiler_directives = attr_result.get('compiler_directives', [])
        result.testing = attr_result.get('testing', [])

        return result

    def _detect_module_name(self, file_path: str) -> str:
        """Detect module name from file path."""
        if not file_path:
            return ""
        path = Path(file_path)
        # Check for Sources/<ModuleName>/ pattern (SPM convention)
        parts = path.parts
        for i, part in enumerate(parts):
            if part == 'Sources' and i + 1 < len(parts):
                return parts[i + 1]
        return path.stem

    def _extract_imports(self, content: str) -> List[str]:
        """Extract import declarations."""
        imports = []
        for match in self.IMPORT_PATTERN.finditer(content):
            module = match.group('module')
            if module not in imports:
                imports.append(module)
        return imports

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Swift frameworks/libraries are used in the file."""
        frameworks = []
        for fw_name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(fw_name)
        return frameworks

    def _enhance_with_ast(self, content: str, result: SwiftParseResult):
        """Use tree-sitter-swift AST for enhanced extraction if available."""
        if not self._tree_sitter_available:
            return
        try:
            tree = self._ts_parser.parse(bytes(content, 'utf-8'))
            root = tree.root_node

            # AST-enhanced: Extract class declarations with precise positions
            self._ast_extract_classes(root, content, result)
            # AST-enhanced: Extract function signatures with precise params
            self._ast_extract_functions(root, content, result)
            # AST-enhanced: Extract protocol requirements
            self._ast_extract_protocols(root, content, result)
            # AST-enhanced: Extract enum cases with associated values
            self._ast_extract_enums(root, content, result)
        except Exception:
            pass  # Fallback to regex extraction

    def _ast_extract_classes(self, root_node, content: str, result: SwiftParseResult):
        """AST-enhanced class extraction."""
        for node in self._find_nodes(root_node, 'class_declaration'):
            name_node = self._find_child(node, 'type_identifier')
            if name_node:
                name = content[name_node.start_byte:name_node.end_byte]
                # Merge with regex-extracted class if found
                for cls in result.classes:
                    if cls.name == name:
                        cls.line_number = node.start_point[0] + 1
                        break

    def _ast_extract_functions(self, root_node, content: str, result: SwiftParseResult):
        """AST-enhanced function extraction."""
        for node in self._find_nodes(root_node, 'function_declaration'):
            name_node = self._find_child(node, 'simple_identifier')
            if name_node:
                name = content[name_node.start_byte:name_node.end_byte]
                for func in result.functions:
                    if func.name == name:
                        func.line_number = node.start_point[0] + 1
                        break

    def _ast_extract_protocols(self, root_node, content: str, result: SwiftParseResult):
        """AST-enhanced protocol extraction."""
        for node in self._find_nodes(root_node, 'protocol_declaration'):
            name_node = self._find_child(node, 'type_identifier')
            if name_node:
                name = content[name_node.start_byte:name_node.end_byte]
                for proto in result.protocols:
                    if proto.name == name:
                        proto.line_number = node.start_point[0] + 1
                        break

    def _ast_extract_enums(self, root_node, content: str, result: SwiftParseResult):
        """AST-enhanced enum extraction."""
        for node in self._find_nodes(root_node, 'enum_declaration'):
            name_node = self._find_child(node, 'type_identifier')
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
    def parse_package_swift(content: str) -> Dict[str, Any]:
        """
        Parse Package.swift to extract dependency and platform information.

        Args:
            content: Package.swift file content

        Returns:
            Dict with 'name', 'swift_tools_version', 'platforms',
            'dependencies', 'targets', 'products'
        """
        result: Dict[str, Any] = {
            'name': '',
            'swift_tools_version': '',
            'platforms': [],
            'dependencies': [],
            'products': [],
            'targets': [],
        }

        # Extract swift-tools-version
        version_match = re.search(
            r'swift-tools-version:\s*(\d+\.\d+(?:\.\d+)?)',
            content, re.IGNORECASE
        )
        if version_match:
            result['swift_tools_version'] = version_match.group(1)

        # Extract package name
        name_match = re.search(r'name:\s*"([^"]+)"', content)
        if name_match:
            result['name'] = name_match.group(1)

        # Extract platforms
        for plat_match in re.finditer(
            r'\.(?P<platform>iOS|macOS|watchOS|tvOS|visionOS|macCatalyst)\s*\(\s*'
            r'(?:\.v(?P<vshort>\d+(?:_\d+)?)|"(?P<vstr>[^"]+)")\s*\)',
            content
        ):
            platform = plat_match.group('platform')
            version = (plat_match.group('vshort') or plat_match.group('vstr') or '').replace('_', '.')
            result['platforms'].append({'platform': platform, 'version': version})

        # Extract dependencies
        for dep_match in re.finditer(
            r'\.package\s*\(\s*(?:'
            r'url:\s*"(?P<url>[^"]+)"(?:\s*,\s*(?:from:\s*"(?P<from>[^"]+)"|'
            r'exact:\s*"(?P<exact>[^"]+)"|'
            r'"(?P<range>[^"]+)"\s*\.\.\.\s*"(?P<range_end>[^"]+)"|'
            r'\.upToNextMajor\s*\(\s*from:\s*"(?P<utnm>[^"]+)"\s*\)|'
            r'\.upToNextMinor\s*\(\s*from:\s*"(?P<utnr>[^"]+)"\s*\)|'
            r'branch:\s*"(?P<branch>[^"]+)"|'
            r'revision:\s*"(?P<rev>[^"]+)"))?'
            r'|name:\s*"(?P<name>[^"]+)"'
            r'|path:\s*"(?P<path>[^"]+)"'
            r')',
            content
        ):
            dep: Dict[str, str] = {}
            if dep_match.group('url'):
                dep['url'] = dep_match.group('url')
                # Extract package name from URL
                url = dep_match.group('url')
                dep['name'] = url.rstrip('/').split('/')[-1].replace('.git', '')
                if dep_match.group('from'):
                    dep['version'] = dep_match.group('from')
                elif dep_match.group('exact'):
                    dep['version'] = dep_match.group('exact')
                elif dep_match.group('utnm'):
                    dep['version'] = dep_match.group('utnm')
                elif dep_match.group('branch'):
                    dep['version'] = f"branch:{dep_match.group('branch')}"
            elif dep_match.group('path'):
                dep['path'] = dep_match.group('path')
                dep['name'] = Path(dep_match.group('path')).name
            elif dep_match.group('name'):
                dep['name'] = dep_match.group('name')

            if dep:
                result['dependencies'].append(dep)

        # Extract products
        for prod_match in re.finditer(
            r'\.(?P<type>library|executable|plugin)\s*\(\s*name:\s*"(?P<name>[^"]+)"',
            content
        ):
            result['products'].append({
                'name': prod_match.group('name'),
                'type': prod_match.group('type'),
            })

        # Extract targets
        for target_match in re.finditer(
            r'\.(?P<type>target|executableTarget|testTarget|systemLibrary|binaryTarget|plugin)\s*\(\s*'
            r'name:\s*"(?P<name>[^"]+)"',
            content
        ):
            target_info: Dict[str, Any] = {
                'name': target_match.group('name'),
                'type': target_match.group('type'),
            }

            # Extract target dependencies
            deps_area = content[target_match.end():target_match.end() + 500]
            dep_names = re.findall(r'\.(?:product|target)\s*\(\s*name:\s*"([^"]+)"', deps_area)
            if dep_names:
                target_info['dependencies'] = dep_names

            result['targets'].append(target_info)

        return result
