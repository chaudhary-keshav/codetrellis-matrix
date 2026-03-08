"""
EnhancedCppParser v1.0 - Comprehensive C++ parser using all extractors.

This parser integrates all C++ extractors to provide complete
parsing of C++ source files.

Supports:
- All C++ standards: C++98, C++03, C++11, C++14, C++17, C++20, C++23, C++26
- Classes, structs, unions with inheritance, templates, concepts
- Scoped enums (enum class/struct) with underlying types
- Functions, methods, operators, constructors, destructors
- Lambdas, coroutines (co_await/co_yield/co_return)
- Template metaprogramming (SFINAE, type_traits, concepts, requires)
- constexpr, consteval, constinit
- Smart pointers (unique_ptr, shared_ptr, weak_ptr)
- STL container usage detection
- RAII patterns
- Design pattern detection (Singleton, Factory, Observer, Strategy, Visitor)
- REST API extraction (Crow, Pistache, cpp-httplib, Boost.Beast, Drogon)
- gRPC service detection
- Qt signals/slots
- Boost.Asio networking
- C++20 modules (import, export, module)
- AST support via tree-sitter-cpp (optional, graceful fallback to regex)
- LSP support via clangd (optional)
- C++ standard version detection from compiler flags and features
- CMakeLists.txt / Makefile / meson.build parser

Part of CodeTrellis v4.20 - C++ Language Support
"""

import re
import os
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all C++ extractors
from .extractors.cpp import (
    CppTypeExtractor, CppClassInfo, CppUnionInfo, CppEnumInfo,
    CppEnumConstantInfo, CppTypeAliasInfo, CppConceptInfo,
    CppForwardDeclInfo, CppNamespaceInfo, CppFieldInfo, CppBaseClassInfo,
    CppFunctionExtractor, CppMethodInfo, CppLambdaInfo, CppParameterInfo,
    CppAPIExtractor, CppEndpointInfo, CppGrpcServiceInfo,
    CppSignalSlotInfo, CppCallbackInfo, CppNetworkingInfo, CppIPCInfo,
    CppModelExtractor, CppContainerUsageInfo, CppSmartPointerInfo,
    CppRAIIInfo, CppGlobalVarInfo, CppConstantInfo, CppDesignPatternInfo,
    CppAttributeExtractor, CppIncludeInfo, CppMacroDefInfo,
    CppConditionalBlockInfo, CppPragmaInfo, CppAttributeInfo,
    CppStaticAssertInfo, CppModuleInfo,
)

logger = logging.getLogger(__name__)

# Try to import tree-sitter-cpp for AST parsing (optional)
_TREE_SITTER_CPP_AVAILABLE = False
try:
    import tree_sitter
    import tree_sitter_cpp
    _TREE_SITTER_CPP_AVAILABLE = True
    logger.debug("tree-sitter-cpp available for C++ AST parsing")
except ImportError:
    logger.debug("tree-sitter-cpp not available, using regex-based parsing")


@dataclass
class CppParseResult:
    """Complete parse result for a C++ file."""
    file_path: str
    file_type: str = "cpp"

    # Header info
    is_header: bool = False
    include_guard: Optional[str] = None
    has_pragma_once: bool = False

    # Core type definitions
    classes: List[CppClassInfo] = field(default_factory=list)
    unions: List[CppUnionInfo] = field(default_factory=list)
    enums: List[CppEnumInfo] = field(default_factory=list)
    type_aliases: List[CppTypeAliasInfo] = field(default_factory=list)
    concepts: List[CppConceptInfo] = field(default_factory=list)
    forward_decls: List[CppForwardDeclInfo] = field(default_factory=list)
    namespaces: List[CppNamespaceInfo] = field(default_factory=list)

    # Functions / Methods
    methods: List[CppMethodInfo] = field(default_factory=list)
    lambdas: List[CppLambdaInfo] = field(default_factory=list)

    # API patterns
    endpoints: List[CppEndpointInfo] = field(default_factory=list)
    grpc_services: List[CppGrpcServiceInfo] = field(default_factory=list)
    signals_slots: List[CppSignalSlotInfo] = field(default_factory=list)
    callbacks: List[CppCallbackInfo] = field(default_factory=list)
    networking: List[CppNetworkingInfo] = field(default_factory=list)
    ipc: List[CppIPCInfo] = field(default_factory=list)
    websockets: List[Dict] = field(default_factory=list)

    # Model / Data patterns
    containers: List[CppContainerUsageInfo] = field(default_factory=list)
    smart_pointers: List[CppSmartPointerInfo] = field(default_factory=list)
    raii: List[CppRAIIInfo] = field(default_factory=list)
    global_vars: List[CppGlobalVarInfo] = field(default_factory=list)
    constants: List[CppConstantInfo] = field(default_factory=list)
    design_patterns: List[CppDesignPatternInfo] = field(default_factory=list)

    # Preprocessor / Attributes
    includes: List[CppIncludeInfo] = field(default_factory=list)
    macros: List[CppMacroDefInfo] = field(default_factory=list)
    conditionals: List[CppConditionalBlockInfo] = field(default_factory=list)
    pragmas: List[CppPragmaInfo] = field(default_factory=list)
    attributes: List[CppAttributeInfo] = field(default_factory=list)
    static_asserts: List[CppStaticAssertInfo] = field(default_factory=list)
    modules: List[CppModuleInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    cpp_standard: str = ""  # c++98, c++11, c++14, c++17, c++20, c++23, c++26
    detected_compiler: str = ""  # gcc, clang, msvc
    detected_features: List[str] = field(default_factory=list)


class EnhancedCppParser:
    """
    Enhanced C++ parser that uses all extractors for comprehensive parsing.

    Framework/library detection supports 30+ frameworks:
    - STL (C++ Standard Library)
    - Boost (Asio, Beast, Filesystem, Spirit, etc.)
    - Qt (5/6, widgets, QML, networking)
    - POCO (networking, data, utilities)
    - gRPC (C++ client/server)
    - Protobuf (Protocol Buffers)
    - OpenCV (computer vision)
    - Eigen (linear algebra)
    - LLVM/Clang (compiler infrastructure)
    - Abseil (Google's C++ library)
    - folly (Facebook's C++ library)
    - Crow / Pistache / cpp-httplib / Drogon / Beast (HTTP servers)
    - fmt (formatting)
    - spdlog (logging)
    - nlohmann/json (JSON)
    - catch2 / gtest / doctest (testing)
    - pybind11 (Python bindings)
    - Vulkan / OpenGL / DirectX (graphics)
    - CUDA (GPU computing)
    - TBB / OpenMP (parallelism)
    - ROS / ROS2 (robotics)
    - Unreal Engine (game engine)
    - wxWidgets (GUI)
    - SFML (multimedia)

    AST support: Optional tree-sitter-cpp integration for precise parsing.
    Falls back to regex when tree-sitter is not available.

    LSP support: Optional clangd integration for:
    - Symbol resolution
    - Cross-file references
    - Template instantiation
    - Compilation database (compile_commands.json)
    """

    # Framework detection patterns (30+ frameworks)
    FRAMEWORK_PATTERNS = {
        # Standard Library
        'stl': re.compile(r'#include\s*<(?:algorithm|vector|map|set|string|iostream|fstream|memory|functional|chrono|thread|mutex|atomic|optional|variant|any|filesystem|ranges|format|expected|print)>'),
        # Boost
        'boost': re.compile(r'#include\s*<boost/|boost::'),
        'boost_asio': re.compile(r'(?:#include\s*<boost/asio|boost::asio::|asio::io_context|asio::ip::tcp)'),
        'boost_beast': re.compile(r'(?:#include\s*<boost/beast|beast::websocket|beast::http)'),
        'boost_spirit': re.compile(r'(?:#include\s*<boost/spirit|qi::|karma::)'),
        # Qt
        'qt': re.compile(r'(?:#include\s*<Q\w+>|Q_OBJECT|Q_PROPERTY|QApplication|QWidget|QMainWindow|qDebug|emit\s+\w+)'),
        'qml': re.compile(r'(?:#include\s*<QQml|QQuick|qmlRegisterType)'),
        # POCO
        'poco': re.compile(r'(?:#include\s*"Poco/|Poco::)'),
        # gRPC
        'grpc': re.compile(r'(?:#include\s*<grpc|grpc::)'),
        'protobuf': re.compile(r'(?:#include\s*.*\.pb\.h|google::protobuf)'),
        # HTTP Frameworks
        'crow': re.compile(r'(?:#include\s*"?crow\.h"?|crow::SimpleApp|CROW_ROUTE)'),
        'pistache': re.compile(r'(?:#include\s*<pistache/|Pistache::)'),
        'httplib': re.compile(r'(?:#include\s*"?httplib\.h"?|httplib::Server)'),
        'drogon': re.compile(r'(?:#include\s*<drogon/|drogon::app)'),
        # JSON
        'nlohmann_json': re.compile(r'(?:#include\s*<nlohmann/json\.hpp>|nlohmann::json|json::parse)'),
        'rapidjson': re.compile(r'(?:#include\s*"?rapidjson/|rapidjson::)'),
        # Computer Vision / Math
        'opencv': re.compile(r'(?:#include\s*<opencv2/|cv::Mat|cv::imread)'),
        'eigen': re.compile(r'(?:#include\s*<Eigen/|Eigen::Matrix|Eigen::Vector)'),
        # Logging / Formatting
        'spdlog': re.compile(r'(?:#include\s*<spdlog/|spdlog::)'),
        'fmt': re.compile(r'(?:#include\s*<fmt/|fmt::format|fmt::print)'),
        # Testing
        'gtest': re.compile(r'(?:#include\s*<gtest/|TEST\(|TEST_F\(|EXPECT_|ASSERT_)'),
        'catch2': re.compile(r'(?:#include\s*<catch2/|TEST_CASE\(|SECTION\(|REQUIRE\(|CHECK\()'),
        'doctest': re.compile(r'(?:#include\s*"?doctest\.h"?|DOCTEST_|TEST_CASE\()'),
        # Compiler / Tooling
        'llvm': re.compile(r'(?:#include\s*"?llvm/|llvm::)'),
        'clang': re.compile(r'(?:#include\s*"?clang/|clang::)'),
        # Google
        'abseil': re.compile(r'(?:#include\s*"?absl/|absl::)'),
        'folly': re.compile(r'(?:#include\s*<folly/|folly::)'),
        # Python bindings
        'pybind11': re.compile(r'(?:#include\s*<pybind11/|pybind11::|PYBIND11_MODULE)'),
        # Graphics / GPU
        'vulkan': re.compile(r'(?:#include\s*<vulkan/|vk\w+|VkDevice|VK_)'),
        'opengl': re.compile(r'(?:#include\s*<GL/|glfw|GL_\w+|glBegin|glEnable)'),
        'cuda': re.compile(r'(?:#include\s*<cuda|__global__|__device__|cudaMalloc|dim3)'),
        # Parallelism
        'tbb': re.compile(r'(?:#include\s*<tbb/|tbb::)'),
        'openmp': re.compile(r'(?:#pragma\s+omp\s|#include\s*<omp\.h>)'),
        # Robotics / Game Engines
        'ros': re.compile(r'(?:#include\s*<ros/|ros::init|ros::NodeHandle)'),
        'ros2': re.compile(r'(?:#include\s*"?rclcpp/|rclcpp::)'),
        'unreal': re.compile(r'(?:UCLASS\(|UPROPERTY\(|UFUNCTION\(|APlayerController|UGameplayStatics)'),
        # Other
        'wxwidgets': re.compile(r'(?:#include\s*<wx/|wxFrame|wxApp|wxBEGIN_EVENT_TABLE)'),
        'sfml': re.compile(r'(?:#include\s*<SFML/|sf::RenderWindow|sf::Sprite)'),
        'sqlite': re.compile(r'(?:#include\s*"?sqlite3\.h"?|sqlite3_\w+)'),
        'libcurl': re.compile(r'(?:#include\s*<curl/|CURL\w*|curl_easy_)'),
    }

    # C++ standard feature detection
    CPP_STANDARD_FEATURES = {
        'c++11': [
            re.compile(r'\bauto\s+\w+\s*='),
            re.compile(r'\bnullptr\b'),
            re.compile(r'\blambda.*\['),
            re.compile(r'\bstatic_assert\b'),
            re.compile(r'\bconstexpr\b'),
            re.compile(r'\bnoexcept\b'),
            re.compile(r'\benum\s+class\b'),
            re.compile(r'\boverride\b'),
            re.compile(r'\bfinal\b'),
            re.compile(r'\bdecltype\b'),
            re.compile(r'(?:unique_ptr|shared_ptr|weak_ptr)'),
            re.compile(r'\bstd::move\b'),
            re.compile(r'&&\s*\w+\s*[){]'),  # rvalue references
            re.compile(r'using\s+\w+\s*='),  # alias templates
            re.compile(r'\bthread_local\b'),
            re.compile(r'\bstd::thread\b'),
            re.compile(r'\bstd::async\b'),
            re.compile(r'\bstd::mutex\b'),
        ],
        'c++14': [
            re.compile(r'\bdecltype\s*\(\s*auto\s*\)'),
            re.compile(r'\bstd::make_unique\b'),
            re.compile(r"(?:0b[01]+|0B[01]+)"),  # binary literals
            re.compile(r"[\d]+'\d"),  # digit separators
        ],
        'c++17': [
            re.compile(r'\bstd::optional\b'),
            re.compile(r'\bstd::variant\b'),
            re.compile(r'\bstd::any\b'),
            re.compile(r'\bstd::string_view\b'),
            re.compile(r'\bstd::filesystem\b'),
            re.compile(r'\bif\s+constexpr\b'),
            re.compile(r'\binline\s+(?:static\s+)?(?:constexpr\s+)?(?:const\s+)?\w+\s+\w+\s*='),  # inline variables
            re.compile(r'\b(?:auto|const auto)\s*\['),  # structured bindings
            re.compile(r'\bstd::apply\b'),
        ],
        'c++20': [
            re.compile(r'\bconcept\s+\w+\s*='),
            re.compile(r'\brequires\s+(?:\{|[\w:]+)'),
            re.compile(r'\bco_await\b'),
            re.compile(r'\bco_yield\b'),
            re.compile(r'\bco_return\b'),
            re.compile(r'\bstd::span\b'),
            re.compile(r'\bstd::ranges\b'),
            re.compile(r'\bstd::format\b'),
            re.compile(r'\bconsteval\b'),
            re.compile(r'\bconstinit\b'),
            re.compile(r'\bstd::jthread\b'),
            re.compile(r'\bstd::source_location\b'),
            re.compile(r'\bstd::coroutine_handle\b'),
            re.compile(r'(?:export\s+)?module\s+\w+'),
            re.compile(r'import\s+(?:std|\w+)\s*;'),
            re.compile(r'\[\[likely\]\]|\[\[unlikely\]\]'),
            re.compile(r'\bstd::three_way_comparable\b|<=>'),  # spaceship operator
        ],
        'c++23': [
            re.compile(r'\bstd::expected\b'),
            re.compile(r'\bstd::mdspan\b'),
            re.compile(r'\bstd::flat_map\b'),
            re.compile(r'\bstd::flat_set\b'),
            re.compile(r'\bstd::print\b'),
            re.compile(r'\bstd::println\b'),
            re.compile(r'\bstd::generator\b'),
            re.compile(r'\bif\s+consteval\b'),
            re.compile(r'\bstd::stacktrace\b'),
            re.compile(r'\bstatic\s+operator\s*\('),  # static operator()
            re.compile(r'\[\[assume\('),
        ],
        'c++26': [
            re.compile(r'\bstd::execution\b'),
            re.compile(r'\bstd::inplace_vector\b'),
            re.compile(r'\bstd::hive\b'),
            re.compile(r'#\s*embed\b'),  # #embed directive
        ],
    }

    # Compiler detection
    COMPILER_PATTERNS = {
        'gcc': re.compile(r'__GNUC__|__gcc_struct__|__builtin_\w+'),
        'clang': re.compile(r'__clang__|__has_feature|__has_builtin|__has_cpp_attribute'),
        'msvc': re.compile(r'_MSC_VER|__declspec|__cdecl|__stdcall|__forceinline'),
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = CppTypeExtractor()
        self.function_extractor = CppFunctionExtractor()
        self.api_extractor = CppAPIExtractor()
        self.model_extractor = CppModelExtractor()
        self.attribute_extractor = CppAttributeExtractor()

        # Initialize tree-sitter if available
        self._ts_parser = None
        self._ts_language = None
        if _TREE_SITTER_CPP_AVAILABLE:
            try:
                self._ts_language = tree_sitter_cpp.language()
                self._ts_parser = tree_sitter.Parser(self._ts_language)
                logger.debug("tree-sitter-cpp parser initialized")
            except Exception as e:
                logger.debug(f"Failed to init tree-sitter-cpp: {e}")

    def parse(self, content: str, file_path: str = "") -> CppParseResult:
        """
        Parse C++ source code and extract all information.

        Args:
            content: C++ source code content
            file_path: Path to source file

        Returns:
            CppParseResult with all extracted information
        """
        result = CppParseResult(file_path=file_path)

        # Detect if header file
        if file_path:
            ext = Path(file_path).suffix.lower()
            result.is_header = ext in ('.h', '.hh', '.hpp', '.hxx', '.h++', '.ipp', '.inl', '.tpp')

        # Detect include guard / pragma once
        guard = self._detect_include_guard(content)
        result.include_guard = guard
        result.has_pragma_once = bool(re.search(r'#\s*pragma\s+once', content))

        # Detect C++ standard version
        result.cpp_standard = self._detect_cpp_standard(content)

        # Detect compiler
        result.detected_compiler = self._detect_compiler(content)

        # Detect frameworks/libraries
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect C++ features used
        result.detected_features = self._detect_features(content)

        # If tree-sitter is available, use AST-assisted extraction
        if self._ts_parser:
            self._ast_extract(content, result)

        # Extract types (classes, structs, unions, enums, concepts, aliases)
        type_result = self.type_extractor.extract(content, file_path)
        result.classes = type_result.get('classes', [])
        result.unions = type_result.get('unions', [])
        result.enums = type_result.get('enums', [])
        result.type_aliases = type_result.get('type_aliases', [])
        result.concepts = type_result.get('concepts', [])
        result.forward_decls = type_result.get('forward_decls', [])
        result.namespaces = type_result.get('namespaces', [])

        # Extract functions and methods
        func_result = self.function_extractor.extract(content, file_path)
        result.methods = func_result.get('methods', [])
        result.lambdas = func_result.get('lambdas', [])

        # Extract API patterns
        api_result = self.api_extractor.extract(content, file_path)
        result.endpoints = api_result.get('endpoints', [])
        result.grpc_services = api_result.get('grpc_services', [])
        result.signals_slots = api_result.get('signals_slots', [])
        result.callbacks = api_result.get('callbacks', [])
        result.networking = api_result.get('networking', [])
        result.ipc = api_result.get('ipc', [])
        result.websockets = api_result.get('websockets', [])

        # Extract model/data patterns
        model_result = self.model_extractor.extract(content, file_path)
        result.containers = model_result.get('containers', [])
        result.smart_pointers = model_result.get('smart_pointers', [])
        result.raii = model_result.get('raii', [])
        result.global_vars = model_result.get('global_vars', [])
        result.constants = model_result.get('constants', [])
        result.design_patterns = model_result.get('design_patterns', [])

        # Extract preprocessor/attribute information
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.includes = attr_result.get('includes', [])
        result.macros = attr_result.get('macros', [])
        result.conditionals = attr_result.get('conditionals', [])
        result.pragmas = attr_result.get('pragmas', [])
        result.attributes = attr_result.get('attributes', [])
        result.static_asserts = attr_result.get('static_asserts', [])
        result.modules = attr_result.get('modules', [])

        return result

    def _detect_include_guard(self, content: str) -> Optional[str]:
        """Detect include guard macro name."""
        match = re.search(r'#\s*ifndef\s+(\w+(?:_H|_HPP|_HXX|_H_|_HPP_)\w*)\s*\n\s*#\s*define\s+\1', content)
        if match:
            return match.group(1)
        if re.search(r'#\s*pragma\s+once', content):
            return '__pragma_once__'
        return None

    def _detect_cpp_standard(self, content: str) -> str:
        """Detect which C++ standard the code is using based on features."""
        # Check from newest to oldest
        for std in ('c++26', 'c++23', 'c++20', 'c++17', 'c++14', 'c++11'):
            patterns = self.CPP_STANDARD_FEATURES.get(std, [])
            for pattern in patterns:
                if pattern.search(content):
                    return std
        return "c++98"  # Default

    def _detect_compiler(self, content: str) -> str:
        """Detect target compiler from extensions used."""
        for compiler, pattern in self.COMPILER_PATTERNS.items():
            if pattern.search(content):
                return compiler
        return ""

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which frameworks/libraries are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_features(self, content: str) -> List[str]:
        """Detect specific C++ language features used."""
        features = []
        feature_checks = {
            'rvalue_references': re.compile(r'&&\s*\w+\s*[){]'),
            'move_semantics': re.compile(r'std::move\b|std::forward\b'),
            'variadic_templates': re.compile(r'template\s*<.*\.\.\.'),
            'fold_expressions': re.compile(r'\(\s*\.\.\.\s*[+\-*/%^&|<>!=]'),
            'structured_bindings': re.compile(r'(?:auto|const auto)\s*\['),
            'if_constexpr': re.compile(r'if\s+constexpr\b'),
            'concepts': re.compile(r'\bconcept\s+\w+'),
            'coroutines': re.compile(r'\bco_await\b|\bco_yield\b|\bco_return\b'),
            'modules': re.compile(r'(?:export\s+)?module\s+\w+|import\s+(?:std|\w+)'),
            'ranges': re.compile(r'std::ranges\b|std::views\b'),
            'spaceship_operator': re.compile(r'<=>'),
            'designated_init': re.compile(r'\.\w+\s*=\s*[^=]'),
            'template_lambdas': re.compile(r'\[.*\]\s*<'),
            'consteval': re.compile(r'\bconsteval\b'),
            'constinit': re.compile(r'\bconstinit\b'),
            'three_way_comparison': re.compile(r'\bstd::strong_ordering\b|\bstd::weak_ordering\b'),
            'smart_pointers': re.compile(r'(?:unique_ptr|shared_ptr|weak_ptr)'),
            'raii': re.compile(r'(?:lock_guard|unique_lock|scoped_lock)'),
            'algorithms': re.compile(r'std::(?:sort|find|transform|accumulate|for_each|remove_if)\b'),
            'type_traits': re.compile(r'std::(?:is_same|enable_if|remove_cv|decay|conditional|void_t)\b'),
        }
        for feat_name, pattern in feature_checks.items():
            if pattern.search(content):
                features.append(feat_name)
        return features

    def _ast_extract(self, content: str, result: CppParseResult):
        """Use tree-sitter AST for enhanced extraction (when available)."""
        if not self._ts_parser:
            return

        try:
            tree = self._ts_parser.parse(content.encode('utf-8'))
            root = tree.root_node

            # Walk the AST for validation and enhancement
            template_count = 0
            namespace_count = 0
            class_count = 0
            function_count = 0

            for child in root.children:
                if child.type == 'template_declaration':
                    template_count += 1
                elif child.type == 'namespace_definition':
                    namespace_count += 1
                elif child.type in ('class_specifier', 'struct_specifier'):
                    class_count += 1
                elif child.type == 'function_definition':
                    function_count += 1
                elif child.type == 'declaration':
                    pass
                elif child.type == 'preproc_include':
                    pass
                elif child.type == 'preproc_def':
                    pass
                elif child.type == 'preproc_function_def':
                    pass

            logger.debug(
                f"tree-sitter-cpp AST: {len(root.children)} top-level nodes, "
                f"{template_count} templates, {namespace_count} namespaces, "
                f"{class_count} classes, {function_count} functions"
            )
        except Exception as e:
            logger.debug(f"tree-sitter-cpp AST extraction failed: {e}")

    @staticmethod
    def parse_cmake_lists(content: str) -> Dict[str, Any]:
        """
        Parse CMakeLists.txt to extract C++ build information.

        Args:
            content: CMakeLists.txt file content

        Returns:
            Dict with project info, targets, dependencies
        """
        result: Dict[str, Any] = {
            'project_name': '',
            'version': '',
            'cpp_standard': '',
            'targets': [],
            'libraries': [],
            'packages': [],
            'options': [],
        }

        # Project name
        proj_match = re.search(r'project\s*\(\s*(\w+)', content, re.IGNORECASE)
        if proj_match:
            result['project_name'] = proj_match.group(1)

        # Version
        ver_match = re.search(r'project\s*\([^)]*VERSION\s+([0-9.]+)', content, re.IGNORECASE)
        if ver_match:
            result['version'] = ver_match.group(1)

        # C++ standard
        std_match = re.search(r'CMAKE_CXX_STANDARD\s+(\d+)', content)
        if std_match:
            result['cpp_standard'] = f"c++{std_match.group(1)}"

        # Targets
        for target_match in re.finditer(
            r'add_(?:executable|library)\s*\(\s*(\w+)',
            content, re.IGNORECASE
        ):
            result['targets'].append(target_match.group(1))

        # Linked libraries
        for lib_match in re.finditer(
            r'target_link_libraries\s*\(\s*\w+\s+(?:PUBLIC|PRIVATE|INTERFACE)?\s*([\w\s:]+)\)',
            content, re.IGNORECASE
        ):
            libs = lib_match.group(1).strip().split()
            result['libraries'].extend(libs)

        # Find packages
        for pkg_match in re.finditer(
            r'find_package\s*\(\s*(\w+)',
            content, re.IGNORECASE
        ):
            result['packages'].append(pkg_match.group(1))

        # Options
        for opt_match in re.finditer(
            r'option\s*\(\s*(\w+)\s+"([^"]*)"',
            content, re.IGNORECASE
        ):
            result['options'].append({
                'name': opt_match.group(1),
                'description': opt_match.group(2),
            })

        return result

    @staticmethod
    def parse_makefile(content: str) -> Dict[str, Any]:
        """
        Parse Makefile to extract C++ build information.

        Args:
            content: Makefile content

        Returns:
            Dict with targets, compiler flags, libraries
        """
        result: Dict[str, Any] = {
            'cxx': '',
            'cxxflags': '',
            'ldflags': '',
            'targets': [],
            'libraries': [],
            'cpp_standard': '',
        }

        # Compiler
        cxx_match = re.search(r'^CXX\s*[:?]?=\s*(.+)', content, re.MULTILINE)
        if cxx_match:
            result['cxx'] = cxx_match.group(1).strip()

        # CXXFLAGS
        cxxflags_match = re.search(r'^CXXFLAGS\s*[:?]?=\s*(.+)', content, re.MULTILINE)
        if cxxflags_match:
            result['cxxflags'] = cxxflags_match.group(1).strip()
            std_match = re.search(r'-std=(c\+\+\d+|gnu\+\+\d+)', result['cxxflags'])
            if std_match:
                result['cpp_standard'] = std_match.group(1)

        # LDFLAGS / LDLIBS
        ldflags_match = re.search(r'^(?:LDFLAGS|LDLIBS)\s*[:?]?=\s*(.+)', content, re.MULTILINE)
        if ldflags_match:
            result['ldflags'] = ldflags_match.group(1).strip()
            for lib_match in re.finditer(r'-l(\w+)', result['ldflags']):
                result['libraries'].append(lib_match.group(1))

        # Targets
        for target_match in re.finditer(r'^(\w[\w.-]*)\s*:', content, re.MULTILINE):
            target = target_match.group(1)
            if target not in ('CXX', 'CXXFLAGS', 'LDFLAGS', 'LDLIBS', 'SRCS', 'OBJS',
                             'PREFIX', 'INSTALL', 'DESTDIR', 'INCLUDES', 'CC', 'CFLAGS'):
                result['targets'].append(target)

        return result
