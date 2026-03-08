"""
EnhancedJavaParser v1.0 - Comprehensive Java parser using all extractors.

This parser integrates all Java extractors to provide complete
parsing of Java source files.

Supports:
- Core types: classes, interfaces, enums, records, annotations (Java 8-21+)
- Methods: instance, static, abstract, default, constructors
- Frameworks: Spring Boot, Spring MVC/WebFlux, JAX-RS, Quarkus, Micronaut
- JPA/Hibernate: @Entity, relationships, repositories
- Messaging: Kafka, RabbitMQ, JMS listeners
- gRPC: Service implementations
- Build systems: Maven (pom.xml), Gradle (build.gradle, build.gradle.kts)
- Annotations: Spring DI, validation, security, test, Lombok
- AST support via tree-sitter-java (optional, graceful fallback to regex)
- LSP support via Eclipse JDT Language Server (optional)

Part of CodeTrellis v4.12 - Java Language Support
"""

import re
import os
import json
import subprocess
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Tuple
from pathlib import Path

# Import all Java extractors
from .extractors.java import (
    JavaTypeExtractor, JavaClassInfo, JavaInterfaceInfo, JavaRecordInfo,
    JavaFieldInfo, JavaAnnotationDef, JavaGenericParam,
    JavaFunctionExtractor, JavaMethodInfo, JavaConstructorInfo, JavaParameterInfo,
    JavaEnumExtractor, JavaEnumInfo, JavaEnumConstant,
    JavaAPIExtractor, JavaEndpointInfo, JavaGRPCServiceInfo, JavaMessageListenerInfo,
    JavaAnnotationExtractor, JavaAnnotationUsage,
    JavaModelExtractor, JavaEntityInfo, JavaRepositoryInfo,
    JavaColumnInfo, JavaRelationshipInfo,
)

logger = logging.getLogger(__name__)

# Try to import tree-sitter-java for AST parsing (optional)
_TREE_SITTER_JAVA_AVAILABLE = False
try:
    import tree_sitter
    import tree_sitter_java
    _TREE_SITTER_JAVA_AVAILABLE = True
    logger.debug("tree-sitter-java available for Java AST parsing")
except ImportError:
    logger.debug("tree-sitter-java not available, using regex-based parsing")


@dataclass
class JavaParseResult:
    """Complete parse result for a Java file."""
    file_path: str
    file_type: str = "java"

    # Package and imports
    package_name: str = ""
    imports: List[str] = field(default_factory=list)

    # Core type definitions
    classes: List[JavaClassInfo] = field(default_factory=list)
    interfaces: List[JavaInterfaceInfo] = field(default_factory=list)
    records: List[JavaRecordInfo] = field(default_factory=list)
    enums: List[JavaEnumInfo] = field(default_factory=list)
    annotation_defs: List[JavaAnnotationDef] = field(default_factory=list)

    # Methods and constructors
    methods: List[JavaMethodInfo] = field(default_factory=list)
    constructors: List[JavaConstructorInfo] = field(default_factory=list)

    # Framework elements
    endpoints: List[JavaEndpointInfo] = field(default_factory=list)
    grpc_services: List[JavaGRPCServiceInfo] = field(default_factory=list)
    message_listeners: List[JavaMessageListenerInfo] = field(default_factory=list)

    # JPA/Hibernate
    entities: List[JavaEntityInfo] = field(default_factory=list)
    repositories: List[JavaRepositoryInfo] = field(default_factory=list)

    # Annotations
    annotation_usages: List[JavaAnnotationUsage] = field(default_factory=list)
    annotation_summary: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    java_version_features: List[str] = field(default_factory=list)  # records, sealed, etc.
    lambda_count: int = 0
    method_ref_count: int = 0
    javadoc: Optional[str] = None


@dataclass
class JavaDependency:
    """Represents a Java project dependency."""
    group_id: str
    artifact_id: str
    version: Optional[str] = None
    scope: Optional[str] = None  # compile, test, runtime, provided
    build_system: str = "maven"  # maven or gradle


class EnhancedJavaParser:
    """
    Enhanced Java parser v1.0 that uses all extractors for comprehensive parsing.

    Automatically detects and extracts:
    - Core Java: classes, interfaces, enums, records, sealed classes, annotations
    - Web Frameworks: Spring MVC, Spring WebFlux, JAX-RS, Quarkus, Micronaut
    - Data: JPA/Hibernate entities, Spring Data repositories
    - Messaging: Kafka, RabbitMQ, JMS
    - gRPC: Service implementations
    - Build tools: Maven, Gradle
    - Testing: JUnit 5, Mockito, Spring Boot Test
    - Utilities: Lombok, MapStruct

    Supports full AST parsing via tree-sitter-java when available.
    Supports LSP integration via Eclipse JDT Language Server.
    """

    # Framework detection patterns (import-based)
    FRAMEWORK_PATTERNS = {
        # Spring ecosystem
        'spring_boot': re.compile(r'import\s+org\.springframework\.boot\b'),
        'spring_mvc': re.compile(r'import\s+org\.springframework\.web\b'),
        'spring_webflux': re.compile(r'import\s+org\.springframework\.web\.reactive\b|import\s+reactor\.core\b'),
        'spring_data': re.compile(r'import\s+org\.springframework\.data\b'),
        'spring_security': re.compile(r'import\s+org\.springframework\.security\b'),
        'spring_cloud': re.compile(r'import\s+org\.springframework\.cloud\b'),
        'spring_batch': re.compile(r'import\s+org\.springframework\.batch\b'),
        'spring_kafka': re.compile(r'import\s+org\.springframework\.kafka\b'),
        'spring_amqp': re.compile(r'import\s+org\.springframework\.amqp\b'),

        # Jakarta EE / Java EE
        'jakarta': re.compile(r'import\s+jakarta\.\b'),
        'javax': re.compile(r'import\s+javax\.\b'),

        # Alternative frameworks
        'quarkus': re.compile(r'import\s+io\.quarkus\b'),
        'micronaut': re.compile(r'import\s+io\.micronaut\b'),
        'vertx': re.compile(r'import\s+io\.vertx\b'),
        'dropwizard': re.compile(r'import\s+io\.dropwizard\b'),

        # Persistence
        'jpa': re.compile(r'import\s+(?:jakarta|javax)\.persistence\b'),
        'hibernate': re.compile(r'import\s+org\.hibernate\b'),
        'mybatis': re.compile(r'import\s+org\.apache\.ibatis\b|import\s+org\.mybatis\b'),
        'jooq': re.compile(r'import\s+org\.jooq\b'),

        # Testing
        'junit5': re.compile(r'import\s+org\.junit\.jupiter\b'),
        'junit4': re.compile(r'import\s+org\.junit\.(Test|Before|After|Rule)\b'),
        'mockito': re.compile(r'import\s+org\.mockito\b'),
        'assertj': re.compile(r'import\s+org\.assertj\b'),

        # Build/DI
        'lombok': re.compile(r'import\s+lombok\b'),
        'mapstruct': re.compile(r'import\s+org\.mapstruct\b'),
        'dagger': re.compile(r'import\s+dagger\b'),
        'guice': re.compile(r'import\s+com\.google\.inject\b'),

        # Messaging
        'kafka': re.compile(r'import\s+org\.apache\.kafka\b'),
        'rabbitmq': re.compile(r'import\s+com\.rabbitmq\b'),

        # gRPC
        'grpc': re.compile(r'import\s+io\.grpc\b'),
        'protobuf': re.compile(r'import\s+com\.google\.protobuf\b'),

        # Reactive
        'reactor': re.compile(r'import\s+reactor\b'),
        'rxjava': re.compile(r'import\s+io\.reactivex\b'),

        # Logging
        'slf4j': re.compile(r'import\s+org\.slf4j\b'),
        'log4j': re.compile(r'import\s+org\.apache\.logging\b|import\s+org\.apache\.log4j\b'),

        # Serialization
        'jackson': re.compile(r'import\s+com\.fasterxml\.jackson\b'),
        'gson': re.compile(r'import\s+com\.google\.gson\b'),

        # Utilities
        'guava': re.compile(r'import\s+com\.google\.common\b'),
        'apache_commons': re.compile(r'import\s+org\.apache\.commons\b'),
    }

    # Package declaration
    PACKAGE_PATTERN = re.compile(r'^package\s+([\w.]+)\s*;', re.MULTILINE)

    # Import pattern
    IMPORT_PATTERN = re.compile(r'^import\s+(?:static\s+)?([\w.*]+)\s*;', re.MULTILINE)

    # Java version feature detection
    VERSION_FEATURES = {
        'records': re.compile(r'\brecord\s+\w+'),
        'sealed_classes': re.compile(r'\bsealed\s+(?:class|interface)\b'),
        'text_blocks': re.compile(r'"""'),
        'pattern_matching': re.compile(r'\binstanceof\s+\w+\s+\w+\b'),
        'switch_expressions': re.compile(r'\bcase\s+\w+\s*->'),
        'var_keyword': re.compile(r'\bvar\s+\w+\s*='),
        'modules': re.compile(r'^module\s+[\w.]+\s*\{', re.MULTILINE),
    }

    def __init__(self):
        """Initialize the enhanced Java parser with all extractors."""
        self.type_extractor = JavaTypeExtractor()
        self.function_extractor = JavaFunctionExtractor()
        self.enum_extractor = JavaEnumExtractor()
        self.api_extractor = JavaAPIExtractor()
        self.annotation_extractor = JavaAnnotationExtractor()
        self.model_extractor = JavaModelExtractor()

        # AST parser (optional)
        self._ast_parser = None
        self._ast_language = None
        if _TREE_SITTER_JAVA_AVAILABLE:
            try:
                self._ast_language = tree_sitter.Language(tree_sitter_java.language())
                self._ast_parser = tree_sitter.Parser(self._ast_language)
                logger.info("Java AST parser initialized with tree-sitter-java")
            except Exception as e:
                logger.warning(f"Failed to initialize tree-sitter-java: {e}")

    def parse(self, content: str, file_path: str = "") -> JavaParseResult:
        """
        Parse Java source code and extract all information.

        Uses tree-sitter AST when available, falls back to regex-based extraction.

        Args:
            content: Java source code content
            file_path: Path to source file

        Returns:
            JavaParseResult with all extracted information
        """
        result = JavaParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Extract package name
        pkg_match = self.PACKAGE_PATTERN.search(content)
        if pkg_match:
            result.package_name = pkg_match.group(1)

        # Extract imports
        result.imports = [m.group(1) for m in self.IMPORT_PATTERN.finditer(content)]

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect Java version features
        result.java_version_features = self._detect_version_features(content)

        # Extract file-level javadoc
        first_javadoc = re.match(r'\s*/\*\*(.*?)\*/', content, re.DOTALL)
        if first_javadoc:
            cleaned = re.sub(r'\*', '', first_javadoc.group(1)).strip()
            lines = [l.strip() for l in cleaned.split('\n') if l.strip() and not l.strip().startswith('@')]
            if lines:
                result.javadoc = lines[0][:200]

        # === Use AST parser if available ===
        if self._ast_parser and self._ast_language:
            self._parse_with_ast(content, file_path, result)
        else:
            self._parse_with_regex(content, file_path, result)

        return result

    def _parse_with_ast(self, content: str, file_path: str, result: JavaParseResult):
        """Parse using tree-sitter AST for maximum accuracy."""
        try:
            tree = self._ast_parser.parse(bytes(content, 'utf-8'))
            root = tree.root_node

            # Extract types and methods using AST nodes
            self._extract_ast_types(root, content, file_path, result)
            self._extract_ast_methods(root, content, file_path, result)

            # Use regex for framework-specific patterns that AST doesn't cover:
            # API endpoints, JPA entities, gRPC services, annotation usages.
            # Methods/constructors are already extracted by AST — skip them.
            self._extract_frameworks_regex(content, file_path, result, skip_methods=True)
        except Exception as e:
            logger.warning(f"AST parsing failed for {file_path}, falling back to regex: {e}")
            self._parse_with_regex(content, file_path, result)

    def _extract_ast_types(self, root_node, content: str, file_path: str, result: JavaParseResult):
        """Extract type definitions from AST."""
        if not _TREE_SITTER_JAVA_AVAILABLE:
            return

        for node in self._walk_ast(root_node):
            node_type = node.type

            if node_type == 'class_declaration':
                self._extract_ast_class(node, content, file_path, result)
            elif node_type == 'interface_declaration':
                self._extract_ast_interface(node, content, file_path, result)
            elif node_type == 'enum_declaration':
                self._extract_ast_enum(node, content, file_path, result)
            elif node_type == 'record_declaration':
                self._extract_ast_record(node, content, file_path, result)
            elif node_type == 'annotation_type_declaration':
                self._extract_ast_annotation_def(node, content, file_path, result)

    def _extract_ast_class(self, node, content: str, file_path: str, result: JavaParseResult):
        """Extract class info from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return

        name = content[name_node.start_byte:name_node.end_byte]

        # Get modifiers
        modifiers = []
        annotations = []
        for child in node.children:
            if child.type == 'modifiers':
                for mod_child in child.children:
                    if mod_child.type == 'marker_annotation' or mod_child.type == 'annotation':
                        ann_text = content[mod_child.start_byte:mod_child.end_byte]
                        annotations.append(ann_text.lstrip('@').split('(')[0])
                    else:
                        modifiers.append(content[mod_child.start_byte:mod_child.end_byte])

        # Get superclass
        extends = None
        extends_node = node.child_by_field_name('superclass')
        if extends_node:
            extends = content[extends_node.start_byte:extends_node.end_byte].replace('extends ', '').strip()

        # Get interfaces
        implements = []
        interfaces_node = node.child_by_field_name('interfaces')
        if interfaces_node:
            impl_text = content[interfaces_node.start_byte:interfaces_node.end_byte]
            impl_text = impl_text.replace('implements ', '').strip()
            implements = [i.strip() for i in impl_text.split(',')]

        # Get body and extract fields/methods
        body_node = node.child_by_field_name('body')
        body_text = content[body_node.start_byte + 1:body_node.end_byte - 1] if body_node else ""
        fields = self.type_extractor._extract_fields(body_text) if body_text else []
        method_names = self.type_extractor._extract_methods_from_body(body_text) if body_text else []

        is_abstract = 'abstract' in modifiers
        is_sealed = 'sealed' in modifiers
        kind = "class"
        if is_abstract:
            kind = "abstract_class"
        elif is_sealed:
            kind = "sealed_class"

        result.classes.append(JavaClassInfo(
            name=name,
            kind=kind,
            fields=fields,
            methods=method_names,
            extends=extends,
            implements=implements,
            annotations=annotations,
            file=file_path,
            line_number=node.start_point[0] + 1,
            is_exported='public' in modifiers,
            is_abstract=is_abstract,
            is_sealed=is_sealed,
            modifiers=modifiers,
        ))

    def _extract_ast_interface(self, node, content: str, file_path: str, result: JavaParseResult):
        """Extract interface from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return

        name = content[name_node.start_byte:name_node.end_byte]
        modifiers = []
        annotations = []
        for child in node.children:
            if child.type == 'modifiers':
                for mod_child in child.children:
                    if mod_child.type in ('marker_annotation', 'annotation'):
                        ann_text = content[mod_child.start_byte:mod_child.end_byte]
                        annotations.append(ann_text.lstrip('@').split('(')[0])
                    else:
                        modifiers.append(content[mod_child.start_byte:mod_child.end_byte])

        result.interfaces.append(JavaInterfaceInfo(
            name=name,
            annotations=annotations,
            file=file_path,
            line_number=node.start_point[0] + 1,
            is_exported='public' in modifiers,
            is_functional='FunctionalInterface' in annotations,
        ))

    def _extract_ast_enum(self, node, content: str, file_path: str, result: JavaParseResult):
        """Extract enum from AST node with full constant, field, and method detail."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return

        name = content[name_node.start_byte:name_node.end_byte]

        # Modifiers and annotations
        modifiers = []
        annotations = []
        for child in node.children:
            if child.type == 'modifiers':
                for mod_child in child.children:
                    if mod_child.type in ('marker_annotation', 'annotation'):
                        ann_text = content[mod_child.start_byte:mod_child.end_byte]
                        annotations.append(ann_text.lstrip('@').split('(')[0])
                    else:
                        modifiers.append(content[mod_child.start_byte:mod_child.end_byte])

        # Implements
        implements = []
        for child in node.children:
            if child.type == 'super_interfaces':
                for sub in child.children:
                    if sub.type == 'type_list':
                        for t in sub.children:
                            if t.type in ('type_identifier', 'generic_type'):
                                implements.append(content[t.start_byte:t.end_byte])

        # Parse enum body
        constants = []
        fields = []
        methods = []
        body_node = node.child_by_field_name('body')
        if body_node:
            for child in body_node.children:
                if child.type == 'enum_constant':
                    const_name = ''
                    const_args = []
                    const_annotations = []
                    for cc in child.children:
                        if cc.type == 'identifier':
                            const_name = content[cc.start_byte:cc.end_byte]
                        elif cc.type == 'argument_list':
                            for arg in cc.children:
                                if arg.type not in ('(', ')', ','):
                                    const_args.append(content[arg.start_byte:arg.end_byte])
                        elif cc.type in ('marker_annotation', 'annotation'):
                            ann_text = content[cc.start_byte:cc.end_byte]
                            const_annotations.append(ann_text.lstrip('@').split('(')[0])
                    if const_name:
                        constants.append(JavaEnumConstant(
                            name=const_name,
                            arguments=const_args,
                            annotations=const_annotations,
                        ))
                elif child.type == 'enum_body_declarations':
                    for decl in child.children:
                        if decl.type == 'field_declaration':
                            # Extract field type and name
                            f_type = ''
                            f_name = ''
                            for fc in decl.children:
                                if fc.type in ('type_identifier', 'integral_type',
                                               'floating_point_type', 'boolean_type',
                                               'generic_type', 'array_type', 'void_type'):
                                    f_type = content[fc.start_byte:fc.end_byte]
                                elif fc.type == 'variable_declarator':
                                    id_node = fc.child_by_field_name('name')
                                    if id_node:
                                        f_name = content[id_node.start_byte:id_node.end_byte]
                            if f_name:
                                fields.append({'name': f_name, 'type': f_type})
                        elif decl.type == 'method_declaration':
                            m_name_node = decl.child_by_field_name('name')
                            if m_name_node:
                                methods.append(content[m_name_node.start_byte:m_name_node.end_byte])

        result.enums.append(JavaEnumInfo(
            name=name,
            constants=constants,
            implements=implements,
            annotations=annotations,
            fields=fields,
            methods=methods,
            file=file_path,
            line_number=node.start_point[0] + 1,
            is_exported='public' in modifiers,
        ))

    def _extract_ast_record(self, node, content: str, file_path: str, result: JavaParseResult):
        """Extract record from AST node with components, generics, and methods."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return

        name = content[name_node.start_byte:name_node.end_byte]

        # Modifiers and annotations
        modifiers = []
        annotations = []
        for child in node.children:
            if child.type == 'modifiers':
                for mod_child in child.children:
                    if mod_child.type in ('marker_annotation', 'annotation'):
                        ann_text = content[mod_child.start_byte:mod_child.end_byte]
                        annotations.append(ann_text.lstrip('@').split('(')[0])
                    else:
                        modifiers.append(content[mod_child.start_byte:mod_child.end_byte])

        # Components from formal_parameters
        components = []
        for child in node.children:
            if child.type == 'formal_parameters':
                for param in child.children:
                    if param.type == 'formal_parameter':
                        p_type = ''
                        p_name = ''
                        for pc in param.children:
                            if pc.type in ('type_identifier', 'integral_type',
                                           'floating_point_type', 'boolean_type',
                                           'generic_type', 'array_type', 'void_type'):
                                p_type = content[pc.start_byte:pc.end_byte]
                            elif pc.type == 'identifier':
                                p_name = content[pc.start_byte:pc.end_byte]
                        if p_name:
                            components.append({'type': p_type, 'name': p_name})

        # Generic type parameters
        generic_params = []
        for child in node.children:
            if child.type == 'type_parameters':
                tp_text = content[child.start_byte:child.end_byte]
                # Parse <T extends Foo, U> into JavaGenericParam list
                inner = tp_text.strip('<>').strip()
                for part in self._split_generic_params(inner):
                    part = part.strip()
                    if ' extends ' in part:
                        gp_name, bounds_str = part.split(' extends ', 1)
                        bounds = [b.strip() for b in bounds_str.split('&')]
                        generic_params.append(JavaGenericParam(name=gp_name.strip(), bounds=bounds))
                    elif ' super ' in part:
                        gp_name, bounds_str = part.split(' super ', 1)
                        generic_params.append(JavaGenericParam(name=gp_name.strip(), bounds=[f'super {bounds_str.strip()}']))
                    else:
                        generic_params.append(JavaGenericParam(name=part, bounds=[]))

        # Implements
        implements = []
        for child in node.children:
            if child.type == 'super_interfaces':
                for sub in child.children:
                    if sub.type == 'type_list':
                        for t in sub.children:
                            if t.type in ('type_identifier', 'generic_type'):
                                implements.append(content[t.start_byte:t.end_byte])

        # Methods from body
        methods = []
        body_node = node.child_by_field_name('body')
        if body_node:
            for child in body_node.children:
                if child.type == 'method_declaration':
                    m_name_node = child.child_by_field_name('name')
                    if m_name_node:
                        methods.append(content[m_name_node.start_byte:m_name_node.end_byte])

        result.records.append(JavaRecordInfo(
            name=name,
            components=components,
            implements=implements,
            annotations=annotations,
            generic_params=generic_params,
            methods=methods,
            file=file_path,
            line_number=node.start_point[0] + 1,
            is_exported='public' in modifiers,
        ))

    def _extract_ast_annotation_def(self, node, content: str, file_path: str, result: JavaParseResult):
        """Extract annotation definition from AST node with elements and meta-annotations."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return

        name = content[name_node.start_byte:name_node.end_byte]

        # Modifiers and meta-annotations (e.g., @Retention, @Target)
        modifiers = []
        annotations = []
        retention = None
        target = []
        for child in node.children:
            if child.type == 'modifiers':
                for mod_child in child.children:
                    if mod_child.type in ('marker_annotation', 'annotation'):
                        ann_text = content[mod_child.start_byte:mod_child.end_byte]
                        ann_name = ann_text.lstrip('@').split('(')[0]
                        annotations.append(ann_name)
                        # Extract retention policy
                        if ann_name == 'Retention':
                            ret_match = re.search(r'RetentionPolicy\.(\w+)', ann_text)
                            if ret_match:
                                retention = ret_match.group(1)
                        # Extract targets
                        elif ann_name == 'Target':
                            for tgt in re.findall(r'ElementType\.(\w+)', ann_text):
                                target.append(tgt)
                    else:
                        modifiers.append(content[mod_child.start_byte:mod_child.end_byte])

        # Annotation elements from body
        elements = []
        body_node = node.child_by_field_name('body')
        if body_node:
            for child in body_node.children:
                if child.type == 'annotation_type_element_declaration':
                    elem_type = ''
                    elem_name = ''
                    elem_default = None
                    reading_default = False
                    for ec in child.children:
                        if ec.type in ('type_identifier', 'integral_type',
                                       'floating_point_type', 'boolean_type',
                                       'generic_type', 'array_type', 'void_type'):
                            elem_type = content[ec.start_byte:ec.end_byte]
                        elif ec.type == 'identifier':
                            elem_name = content[ec.start_byte:ec.end_byte]
                        elif ec.type == 'default':
                            reading_default = True
                        elif reading_default and ec.type not in (';',):
                            elem_default = content[ec.start_byte:ec.end_byte]
                            reading_default = False
                    if elem_name:
                        elem_info: Dict[str, Any] = {'name': elem_name, 'type': elem_type}
                        if elem_default is not None:
                            elem_info['default'] = elem_default
                        elements.append(elem_info)

        result.annotation_defs.append(JavaAnnotationDef(
            name=name,
            elements=elements,
            retention=retention,
            target=target,
            annotations=annotations,
            file=file_path,
            line_number=node.start_point[0] + 1,
            is_exported='public' in modifiers,
        ))

    def _extract_ast_methods(self, root_node, content: str, file_path: str, result: JavaParseResult):
        """Extract methods and constructors from AST with full signature detail.

        Only extracts from class/interface bodies — enum and record body methods
        are already captured by their respective extractors as method name lists,
        so we skip them here to avoid duplication.
        """
        for node in self._walk_ast(root_node):
            if node.type in ('method_declaration', 'constructor_declaration'):
                # Walk up to determine the enclosing type declaration
                parent = node.parent
                grandparent = parent.parent if parent else None
                # Enum methods live inside enum_body_declarations (parent)
                # whose parent is enum_body (grandparent).
                # Record methods live inside class_body whose grandparent
                # is record_declaration.
                # We only want class_declaration or interface_declaration bodies.
                enclosing_decl = grandparent if grandparent else parent
                if enclosing_decl and enclosing_decl.type in ('enum_declaration', 'enum_body',
                                                               'record_declaration',
                                                               'annotation_type_declaration'):
                    continue
                if node.type == 'method_declaration':
                    self._extract_ast_method(node, content, file_path, result)
                else:
                    self._extract_ast_constructor(node, content, file_path, result)

        # Lambda and method reference counts still use regex (AST walk would be overkill)
        result.lambda_count = len(re.findall(r'->', content))
        result.method_ref_count = len(re.findall(r'::', content))

    def _extract_ast_method(self, node, content: str, file_path: str, result: JavaParseResult):
        """Extract a single method from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return

        name = content[name_node.start_byte:name_node.end_byte]

        # Find enclosing class name
        class_name = None
        parent = node.parent
        while parent:
            if parent.type in ('class_declaration', 'enum_declaration', 'interface_declaration'):
                pn = parent.child_by_field_name('name')
                if pn:
                    class_name = content[pn.start_byte:pn.end_byte]
                break
            parent = parent.parent

        # Modifiers and annotations
        modifiers = []
        annotations = []
        for child in node.children:
            if child.type == 'modifiers':
                for mod_child in child.children:
                    if mod_child.type in ('marker_annotation', 'annotation'):
                        ann_text = content[mod_child.start_byte:mod_child.end_byte]
                        annotations.append(ann_text.lstrip('@').split('(')[0])
                    else:
                        modifiers.append(content[mod_child.start_byte:mod_child.end_byte])

        # Return type
        return_type = 'void'
        type_node = node.child_by_field_name('type')
        if type_node:
            return_type = content[type_node.start_byte:type_node.end_byte]
        else:
            # Fallback: look for type nodes before the name
            for child in node.children:
                if child.type in ('type_identifier', 'integral_type', 'void_type',
                                  'floating_point_type', 'boolean_type',
                                  'generic_type', 'array_type'):
                    return_type = content[child.start_byte:child.end_byte]
                    break

        # Parameters
        parameters = self._extract_ast_params(node, content)

        # Throws
        throws = []
        for child in node.children:
            if child.type == 'throws':
                for tc in child.children:
                    if tc.type in ('type_identifier', 'generic_type'):
                        throws.append(content[tc.start_byte:tc.end_byte])

        # Generic type parameters
        generic_params = []
        for child in node.children:
            if child.type == 'type_parameters':
                tp_text = content[child.start_byte:child.end_byte].strip('<>').strip()
                generic_params = [p.strip().split()[0] for p in self._split_generic_params(tp_text)]

        result.methods.append(JavaMethodInfo(
            name=name,
            return_type=return_type,
            parameters=parameters,
            modifiers=modifiers,
            annotations=annotations,
            throws=throws,
            generic_params=generic_params,
            file=file_path,
            line_number=node.start_point[0] + 1,
            is_exported='public' in modifiers,
            is_static='static' in modifiers,
            is_abstract='abstract' in modifiers,
            is_synchronized='synchronized' in modifiers,
            is_default='default' in modifiers,
            is_override='Override' in annotations,
            class_name=class_name,
        ))

    def _extract_ast_constructor(self, node, content: str, file_path: str, result: JavaParseResult):
        """Extract a constructor from AST node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return

        class_name = content[name_node.start_byte:name_node.end_byte]

        # Modifiers and annotations
        modifiers = []
        annotations = []
        for child in node.children:
            if child.type == 'modifiers':
                for mod_child in child.children:
                    if mod_child.type in ('marker_annotation', 'annotation'):
                        ann_text = content[mod_child.start_byte:mod_child.end_byte]
                        annotations.append(ann_text.lstrip('@').split('(')[0])
                    else:
                        modifiers.append(content[mod_child.start_byte:mod_child.end_byte])

        # Parameters
        parameters = self._extract_ast_params(node, content)

        # Throws
        throws = []
        for child in node.children:
            if child.type == 'throws':
                for tc in child.children:
                    if tc.type in ('type_identifier', 'generic_type'):
                        throws.append(content[tc.start_byte:tc.end_byte])

        result.constructors.append(JavaConstructorInfo(
            class_name=class_name,
            parameters=parameters,
            modifiers=modifiers,
            annotations=annotations,
            throws=throws,
            file=file_path,
            line_number=node.start_point[0] + 1,
            is_exported='public' in modifiers,
        ))

    def _extract_ast_params(self, node, content: str) -> List[JavaParameterInfo]:
        """Extract parameters from a method/constructor AST node."""
        params = []
        for child in node.children:
            if child.type == 'formal_parameters':
                for param in child.children:
                    if param.type in ('formal_parameter', 'spread_parameter'):
                        p_type = ''
                        p_name = ''
                        p_annotations = []
                        is_varargs = param.type == 'spread_parameter'
                        is_final = False
                        for pc in param.children:
                            if pc.type in ('type_identifier', 'integral_type',
                                           'floating_point_type', 'boolean_type',
                                           'generic_type', 'array_type', 'void_type'):
                                p_type = content[pc.start_byte:pc.end_byte]
                            elif pc.type == 'identifier':
                                p_name = content[pc.start_byte:pc.end_byte]
                            elif pc.type in ('marker_annotation', 'annotation'):
                                ann_text = content[pc.start_byte:pc.end_byte]
                                p_annotations.append(ann_text.lstrip('@').split('(')[0])
                            elif pc.type == 'modifiers':
                                for mc in pc.children:
                                    if mc.type in ('marker_annotation', 'annotation'):
                                        ann_text = content[mc.start_byte:mc.end_byte]
                                        p_annotations.append(ann_text.lstrip('@').split('(')[0])
                                    elif content[mc.start_byte:mc.end_byte] == 'final':
                                        is_final = True
                            elif pc.type == '...':
                                is_varargs = True
                        if p_name:
                            params.append(JavaParameterInfo(
                                name=p_name,
                                type=p_type,
                                annotations=p_annotations,
                                is_varargs=is_varargs,
                                is_final=is_final,
                            ))
        return params

    def _split_generic_params(self, text: str) -> List[str]:
        """Split generic type parameters respecting nested angle brackets."""
        parts = []
        depth = 0
        current = []
        for ch in text:
            if ch == '<':
                depth += 1
                current.append(ch)
            elif ch == '>':
                depth -= 1
                current.append(ch)
            elif ch == ',' and depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                current.append(ch)
        if current:
            parts.append(''.join(current))
        return parts

    def _walk_ast(self, node):
        """Walk AST tree depth-first."""
        yield node
        for child in node.children:
            yield from self._walk_ast(child)

    def _parse_with_regex(self, content: str, file_path: str, result: JavaParseResult):
        """Parse using regex-based extractors (fallback, always available)."""
        # Extract types
        type_result = self.type_extractor.extract(content, file_path)
        result.classes = type_result.get('classes', [])
        result.interfaces = type_result.get('interfaces', [])
        result.records = type_result.get('records', [])
        result.annotation_defs = type_result.get('annotation_defs', [])

        # Extract enums
        result.enums = self.enum_extractor.extract(content, file_path)

        # Extract framework elements
        self._extract_frameworks_regex(content, file_path, result)

    def _extract_frameworks_regex(self, content: str, file_path: str, result: JavaParseResult,
                                skip_methods: bool = False):
        """Extract framework-specific elements using regex.

        Args:
            skip_methods: If True, skip method/constructor extraction (already done by AST).
        """
        if not skip_methods:
            # Get class names for constructor detection
            class_names = [c.name for c in result.classes]
            class_names.extend([e.name for e in result.enums])

            # Extract methods and constructors
            func_result = self.function_extractor.extract(content, file_path, class_names=class_names)
            result.methods = func_result.get('methods', [])
            result.constructors = func_result.get('constructors', [])
            result.lambda_count = func_result.get('lambda_count', 0)
            result.method_ref_count = func_result.get('method_ref_count', 0)

        # Extract API endpoints
        api_result = self.api_extractor.extract(content, file_path)
        result.endpoints = api_result.get('endpoints', [])
        result.grpc_services = api_result.get('grpc_services', [])
        result.message_listeners = api_result.get('message_listeners', [])

        # Extract JPA entities and repositories
        model_result = self.model_extractor.extract(content, file_path)
        result.entities = model_result.get('entities', [])
        result.repositories = model_result.get('repositories', [])

        # Extract annotation usages
        result.annotation_usages = self.annotation_extractor.extract(content, file_path)
        result.annotation_summary = self.annotation_extractor.summarize(result.annotation_usages)

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Java frameworks are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_version_features(self, content: str) -> List[str]:
        """Detect Java version-specific features used in the file."""
        features = []
        for feature, pattern in self.VERSION_FEATURES.items():
            if pattern.search(content):
                features.append(feature)
        return features

    @staticmethod
    def parse_pom_xml(pom_path: str) -> Dict[str, Any]:
        """
        Parse Maven pom.xml to extract dependencies and project metadata.

        Returns dict with: group_id, artifact_id, version, packaging,
                          java_version, dependencies, plugins
        """
        result = {
            'group_id': '',
            'artifact_id': '',
            'version': '',
            'packaging': 'jar',
            'java_version': '',
            'parent': None,
            'dependencies': [],
            'plugins': [],
            'modules': [],
        }

        try:
            content = Path(pom_path).read_text()

            # Remove XML namespace for simpler parsing
            content_clean = re.sub(r'\sxmlns[^"]*"[^"]*"', '', content)

            # Project coordinates
            # Be careful to get project-level, not dependency-level
            project_match = re.search(r'<project[^>]*>(.*?)</project>', content_clean, re.DOTALL)
            if not project_match:
                return result

            project_content = project_match.group(1)

            # Extract direct children only (not nested in dependencies)
            def _extract_direct(tag, text):
                # Find tag NOT inside <dependencies> or <dependency> blocks
                pattern = rf'<{tag}>([^<]+)</{tag}>'
                matches = list(re.finditer(pattern, text))
                if matches:
                    return matches[0].group(1)
                return ''

            result['group_id'] = _extract_direct('groupId', project_content)
            result['artifact_id'] = _extract_direct('artifactId', project_content)
            result['version'] = _extract_direct('version', project_content)
            result['packaging'] = _extract_direct('packaging', project_content) or 'jar'

            # Parent
            parent_match = re.search(r'<parent>(.*?)</parent>', project_content, re.DOTALL)
            if parent_match:
                parent_content = parent_match.group(1)
                result['parent'] = {
                    'group_id': _extract_direct('groupId', parent_content),
                    'artifact_id': _extract_direct('artifactId', parent_content),
                    'version': _extract_direct('version', parent_content),
                }

            # Java version
            java_ver = re.search(r'<(?:java\.version|maven\.compiler\.source|source)>([^<]+)</', project_content)
            if java_ver:
                result['java_version'] = java_ver.group(1)

            # Dependencies
            deps_section = re.search(r'<dependencies>(.*?)</dependencies>', project_content, re.DOTALL)
            if deps_section:
                for dep_match in re.finditer(r'<dependency>(.*?)</dependency>', deps_section.group(1), re.DOTALL):
                    dep_text = dep_match.group(1)
                    dep = JavaDependency(
                        group_id=_extract_direct('groupId', dep_text),
                        artifact_id=_extract_direct('artifactId', dep_text),
                        version=_extract_direct('version', dep_text) or None,
                        scope=_extract_direct('scope', dep_text) or None,
                        build_system='maven',
                    )
                    result['dependencies'].append({
                        'group_id': dep.group_id,
                        'artifact_id': dep.artifact_id,
                        'version': dep.version,
                        'scope': dep.scope,
                    })

            # Modules (multi-module project)
            modules_match = re.search(r'<modules>(.*?)</modules>', project_content, re.DOTALL)
            if modules_match:
                result['modules'] = re.findall(r'<module>([^<]+)</module>', modules_match.group(1))

            # Plugins
            plugins_section = re.search(r'<plugins>(.*?)</plugins>', project_content, re.DOTALL)
            if plugins_section:
                for plugin_match in re.finditer(r'<plugin>(.*?)</plugin>', plugins_section.group(1), re.DOTALL):
                    plugin_text = plugin_match.group(1)
                    result['plugins'].append({
                        'group_id': _extract_direct('groupId', plugin_text),
                        'artifact_id': _extract_direct('artifactId', plugin_text),
                    })

        except Exception as e:
            logger.warning(f"Failed to parse pom.xml {pom_path}: {e}")

        return result

    @staticmethod
    def parse_build_gradle(gradle_path: str) -> Dict[str, Any]:
        """
        Parse Gradle build file (build.gradle or build.gradle.kts) for dependencies.

        Returns dict with: dependencies, plugins, java_version
        """
        result = {
            'dependencies': [],
            'plugins': [],
            'java_version': '',
            'group_id': '',
            'artifact_id': '',
            'version': '',
        }

        try:
            content = Path(gradle_path).read_text()

            # Java version
            java_ver = re.search(
                r'(?:sourceCompatibility|java\.sourceCompatibility|jvmTarget)\s*[=:]\s*["\']?(\d+)["\']?',
                content
            )
            if java_ver:
                result['java_version'] = java_ver.group(1)

            # Group and version
            group_match = re.search(r'group\s*[=:]\s*["\']([^"\']+)["\']', content)
            if group_match:
                result['group_id'] = group_match.group(1)
            version_match = re.search(r'version\s*[=:]\s*["\']([^"\']+)["\']', content)
            if version_match:
                result['version'] = version_match.group(1)

            # Dependencies (Groovy and Kotlin DSL)
            dep_patterns = [
                # Groovy: implementation 'group:artifact:version'
                re.compile(r"(implementation|api|compileOnly|runtimeOnly|testImplementation|testRuntimeOnly)"
                          r"\s+['\"]([^'\"]+)['\"]"),
                # Kotlin: implementation("group:artifact:version")
                re.compile(r"(implementation|api|compileOnly|runtimeOnly|testImplementation|testRuntimeOnly)"
                          r"\s*\(\s*['\"]([^'\"]+)['\"]"),
            ]

            for pattern in dep_patterns:
                for match in pattern.finditer(content):
                    scope = match.group(1)
                    dep_str = match.group(2)
                    parts = dep_str.split(':')
                    if len(parts) >= 2:
                        result['dependencies'].append({
                            'group_id': parts[0],
                            'artifact_id': parts[1],
                            'version': parts[2] if len(parts) > 2 else None,
                            'scope': scope,
                        })

            # Plugins
            plugin_patterns = [
                re.compile(r"id\s+['\"]([^'\"]+)['\"]"),
                re.compile(r'id\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            ]
            for pattern in plugin_patterns:
                for match in pattern.finditer(content):
                    result['plugins'].append(match.group(1))

        except Exception as e:
            logger.warning(f"Failed to parse build.gradle {gradle_path}: {e}")

        return result

    def try_lsp_extraction(self, project_root: str) -> Optional[Dict[str, Any]]:
        """
        Attempt LSP-based extraction using Eclipse JDT Language Server.

        This provides more accurate type resolution, cross-file references,
        and complete type hierarchies compared to regex-based extraction.

        Requires: Eclipse JDT LS installed and available in PATH or configured.
        The JDT LS launcher JAR must be found under the configured path.

        Environment variables:
            JDT_LS_PATH: Path to JDT LS installation directory
            JAVA_HOME: Path to Java 17+ installation (required to run JDT LS)

        Returns:
            Dict with LSP-extracted data (document symbols, type hierarchy),
            or None if LSP is not available or fails.
        """
        import json
        import glob
        import tempfile

        # 1. Locate JDT Language Server
        jdt_ls_path = os.environ.get('JDT_LS_PATH', '')
        if not jdt_ls_path:
            # Try common installation locations
            common_paths = [
                os.path.expanduser('~/.local/share/jdt-ls'),
                '/usr/local/share/jdt-ls',
                os.path.expanduser('~/.eclipse/jdt-ls'),
                os.path.expanduser('~/jdt-ls'),
                # macOS Homebrew
                '/opt/homebrew/opt/jdtls',
                '/usr/local/opt/jdtls',
                # VS Code extensions (Red Hat Java)
                *glob.glob(os.path.expanduser(
                    '~/.vscode/extensions/redhat.java-*/server'
                )),
                *glob.glob(os.path.expanduser(
                    '~/.vscode-server/extensions/redhat.java-*/server'
                )),
            ]
            for path in common_paths:
                if os.path.exists(path):
                    jdt_ls_path = path
                    break

        if not jdt_ls_path:
            logger.debug(
                "JDT Language Server not found. "
                "Set JDT_LS_PATH or install Eclipse JDT LS. "
                "Falling back to regex + tree-sitter parsing."
            )
            return None

        # 2. Find the launcher JAR
        launcher_jars = glob.glob(
            os.path.join(jdt_ls_path, 'plugins', 'org.eclipse.equinox.launcher_*.jar')
        )
        if not launcher_jars:
            logger.debug(f"JDT LS found at {jdt_ls_path} but no launcher JAR in plugins/")
            return None
        launcher_jar = launcher_jars[0]

        # 3. Determine Java executable
        java_home = os.environ.get('JAVA_HOME', '')
        if java_home:
            java_bin = os.path.join(java_home, 'bin', 'java')
        else:
            java_bin = 'java'

        # Verify Java is available
        try:
            java_ver = subprocess.run(
                [java_bin, '-version'],
                capture_output=True, text=True, timeout=5
            )
            if java_ver.returncode != 0:
                logger.debug("Java not available or too old for JDT LS")
                return None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.debug("Java executable not found")
            return None

        # 4. Determine platform config
        import platform
        system = platform.system().lower()
        if system == 'darwin':
            config_dir = 'config_mac'
        elif system == 'linux':
            config_dir = 'config_linux'
        else:
            config_dir = 'config_win'

        config_path = os.path.join(jdt_ls_path, config_dir)
        if not os.path.exists(config_path):
            # Try generic config
            config_path = os.path.join(jdt_ls_path, 'config')
            if not os.path.exists(config_path):
                logger.debug(f"JDT LS config directory not found: {config_dir}")
                return None

        # 5. Create workspace directory for JDT LS
        workspace_dir = tempfile.mkdtemp(prefix='jdt-ws-')

        # 6. Build JDT LS command
        cmd = [
            java_bin,
            '-Declipse.application=org.eclipse.jdt.ls.core.id1',
            '-Dosgi.bundles.defaultStartLevel=4',
            '-Declipse.product=org.eclipse.jdt.ls.core.product',
            '-Dlog.level=WARNING',
            '-Xmx512m',
            '--add-modules=ALL-SYSTEM',
            '--add-opens', 'java.base/java.util=ALL-UNNAMED',
            '--add-opens', 'java.base/java.lang=ALL-UNNAMED',
            '-jar', launcher_jar,
            '-configuration', config_path,
            '-data', workspace_dir,
        ]

        logger.info(f"Starting JDT LS for project: {project_root}")

        try:
            # 7. Start JDT LS process
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # 8. Send LSP initialize request
            project_uri = f"file://{os.path.abspath(project_root)}"
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "processId": os.getpid(),
                    "rootUri": project_uri,
                    "capabilities": {
                        "textDocument": {
                            "documentSymbol": {
                                "hierarchicalDocumentSymbolSupport": True,
                            },
                        },
                    },
                    "workspaceFolders": [
                        {"uri": project_uri, "name": os.path.basename(project_root)}
                    ],
                },
            }

            # Send request using LSP content-length protocol
            self._lsp_send(process, init_request)

            # Read response (with timeout)
            init_response = self._lsp_recv(process, timeout=30)
            if not init_response or init_response.get('id') != 1:
                logger.debug("JDT LS initialization failed or timed out")
                process.terminate()
                return None

            # 9. Send initialized notification
            self._lsp_send(process, {
                "jsonrpc": "2.0",
                "method": "initialized",
                "params": {},
            })

            # 10. Collect document symbols for all Java files
            result = {
                'lsp_available': True,
                'symbols': [],
                'type_hierarchy': [],
            }

            java_files = []
            for root_dir, _, files in os.walk(project_root):
                for f in files:
                    if f.endswith('.java') and not any(
                        skip in root_dir for skip in ['/test/', '/tests/', '/build/', '/target/']
                    ):
                        java_files.append(os.path.join(root_dir, f))

            # Request document symbols for each file (limit to avoid timeout)
            for i, java_file in enumerate(java_files[:50]):
                file_uri = f"file://{os.path.abspath(java_file)}"
                self._lsp_send(process, {
                    "jsonrpc": "2.0",
                    "id": 100 + i,
                    "method": "textDocument/documentSymbol",
                    "params": {
                        "textDocument": {"uri": file_uri},
                    },
                })

                response = self._lsp_recv(process, timeout=10)
                if response and 'result' in response:
                    symbols = response['result']
                    if symbols:
                        result['symbols'].append({
                            'file': java_file,
                            'symbols': symbols,
                        })

            # 11. Shutdown
            self._lsp_send(process, {
                "jsonrpc": "2.0",
                "id": 9999,
                "method": "shutdown",
                "params": None,
            })
            self._lsp_recv(process, timeout=5)
            self._lsp_send(process, {
                "jsonrpc": "2.0",
                "method": "exit",
                "params": None,
            })
            process.wait(timeout=5)

            logger.info(
                f"JDT LS extraction complete: "
                f"{len(result['symbols'])} files with symbols"
            )
            return result if result['symbols'] else None

        except (subprocess.TimeoutExpired, OSError, Exception) as e:
            logger.debug(f"JDT LS extraction failed: {e}")
            try:
                process.terminate()
            except Exception:
                pass
            return None
        finally:
            # Cleanup workspace
            import shutil
            try:
                shutil.rmtree(workspace_dir, ignore_errors=True)
            except Exception:
                pass

    def _lsp_send(self, process, message: Dict) -> None:
        """Send an LSP JSON-RPC message to the process stdin."""
        body = json.dumps(message)
        header = f"Content-Length: {len(body)}\r\n\r\n"
        try:
            process.stdin.write(header.encode('utf-8'))
            process.stdin.write(body.encode('utf-8'))
            process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    def _lsp_recv(self, process, timeout: int = 10) -> Optional[Dict]:
        """
        Read an LSP JSON-RPC response from the process stdout.
        Handles Content-Length header protocol and skips notification messages.
        """
        import select
        import time

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            # Check if data is available
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break

            try:
                ready, _, _ = select.select([process.stdout], [], [], min(remaining, 1.0))
                if not ready:
                    continue

                # Read header
                header_data = b''
                while True:
                    byte = process.stdout.read(1)
                    if not byte:
                        return None
                    header_data += byte
                    if header_data.endswith(b'\r\n\r\n'):
                        break

                # Parse content length
                header_str = header_data.decode('utf-8')
                content_length = 0
                for line in header_str.split('\r\n'):
                    if line.lower().startswith('content-length:'):
                        content_length = int(line.split(':')[1].strip())
                        break

                if content_length == 0:
                    continue

                # Read body
                body = process.stdout.read(content_length)
                if not body:
                    return None

                message = json.loads(body.decode('utf-8'))

                # Skip notifications (no 'id' field) — wait for actual response
                if 'id' in message:
                    return message
                # Notifications are logged but ignored
                logger.debug(f"LSP notification: {message.get('method', '?')}")

            except (ValueError, json.JSONDecodeError, OSError) as e:
                logger.debug(f"LSP recv error: {e}")
                return None

        return None
