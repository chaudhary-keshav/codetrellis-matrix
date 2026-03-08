"""
KotlinAttributeExtractor - Extracts Kotlin annotation and metadata definitions.

Extracts:
- Custom annotation definitions
- Annotation usage patterns (Spring DI, validation, lifecycle)
- Kotlin DSL markers
- Delegation patterns (by lazy, by inject, by viewModels)
- Dependency injection (Koin, Dagger/Hilt, Spring)
- Kotlin compiler plugins metadata (serialization, compose, allopen)
- Build script metadata (Gradle Kotlin DSL)
- Multiplatform expect/actual declarations
- Context receivers (Kotlin 1.6.20+)
- Contracts (kotlin.contracts)

Part of CodeTrellis v4.21 - Kotlin Language Support Upgrade
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KotlinAnnotationDefInfo:
    """Information about a custom Kotlin annotation definition."""
    name: str
    targets: List[str] = field(default_factory=list)  # @Target values
    retention: str = ""  # RUNTIME, BINARY, SOURCE
    parameters: List[Dict[str, str]] = field(default_factory=list)
    is_repeatable: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinAnnotationUsageInfo:
    """Information about annotation usage in Kotlin code."""
    annotation: str
    category: str = ""  # di, validation, lifecycle, spring, test, serialization
    target_name: str = ""
    target_kind: str = ""  # class, function, property, parameter
    arguments: Dict[str, str] = field(default_factory=dict)
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinDelegationInfo:
    """Information about a Kotlin delegation pattern."""
    property_name: str
    delegate_type: str = ""  # lazy, inject, viewModels, map, observable, vetoable
    delegate_expression: str = ""
    is_lazy: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinDIBindingInfo:
    """Information about a dependency injection binding."""
    framework: str = ""  # koin, dagger, hilt, spring
    kind: str = ""  # module, component, singleton, factory, bind, provide
    type_bound: str = ""
    scope: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinMultiplatformDeclInfo:
    """Information about a Kotlin multiplatform expect/actual declaration."""
    name: str
    kind: str = ""  # class, fun, val, interface, object
    is_expect: bool = True
    platform: str = ""  # common, jvm, js, native, ios, android
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinContextReceiverInfo:
    """Information about a context receiver declaration (Kotlin 1.6.20+)."""
    function_name: str = ""
    context_types: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinContractInfo:
    """Information about a Kotlin contract declaration."""
    function_name: str = ""
    effects: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class KotlinAttributeExtractor:
    """
    Extracts Kotlin annotations, metadata, and advanced language features.

    Handles:
    - Custom annotation definitions
    - DI annotations (Spring, Koin, Dagger/Hilt)
    - Delegation patterns
    - Kotlin multiplatform declarations
    - Context receivers
    - Contracts
    - DSL markers
    - Compiler plugin metadata
    """

    # Custom annotation definition
    ANNOTATION_DEF_PATTERN = re.compile(
        r'(?:@Target\s*\(([^)]*)\)\s*)?'
        r'(?:@Retention\s*\(\s*AnnotationRetention\.(\w+)\s*\)\s*)?'
        r'(?:@Repeatable\s*)?'
        r'(?:@MustBeDocumented\s*)?'
        r'annotation\s+class\s+(\w+)\s*(?:\(([^)]*)\))?',
        re.MULTILINE
    )

    # Delegation patterns
    DELEGATION_PATTERN = re.compile(
        r'(?:val|var)\s+(\w+)\s*(?::\s*[\w<>,.\s?*]+)?\s*by\s+'
        r'(lazy|inject|viewModels|activityViewModels|viewModel|'
        r'observable|vetoable|map|Delegates\.\w+|remember|mutableStateOf)\b'
        r'(?:\s*\([^)]*\))?',
        re.MULTILINE
    )

    # Koin module DSL
    KOIN_MODULE_PATTERN = re.compile(
        r'val\s+(\w+)\s*=\s*module\s*\{',
        re.MULTILINE
    )

    # Koin bindings inside module
    KOIN_BINDING_PATTERN = re.compile(
        r'(single|factory|scoped|viewModel|worker)\s*(?:<\s*(\w+)\s*>)?\s*\{',
        re.MULTILINE
    )

    # Dagger/Hilt module
    DAGGER_MODULE_PATTERN = re.compile(
        r'@Module\s*(?:\([^)]*\))?\s*'
        r'(?:@InstallIn\s*\((\w+)(?:::class)?\s*\)\s*)?'
        r'(?:abstract\s+)?(?:class|object)\s+(\w+)',
        re.MULTILINE
    )

    # Dagger/Hilt provides/binds
    DAGGER_PROVIDES_PATTERN = re.compile(
        r'@(Provides|Binds)\s*'
        r'(?:@(\w+)\s*)?'  # Scope annotation
        r'(?:abstract\s+)?fun\s+(\w+)\s*\([^)]*\)\s*:\s*([\w<>,.\s?*]+)',
        re.MULTILINE
    )

    # Spring component annotations
    SPRING_DI_PATTERN = re.compile(
        r'@(Component|Service|Repository|Configuration|Bean|Autowired|Inject|Value|Qualifier)\s*'
        r'(?:\(\s*(?:"([^"]*)")?\s*\))?',
        re.MULTILINE
    )

    # Context receivers (Kotlin 1.6.20+)
    CONTEXT_RECEIVER_PATTERN = re.compile(
        r'context\s*\(([^)]+)\)\s*'
        r'(?:(?:suspend|inline|infix|operator)\s+)*'
        r'fun\s+(?:<[^>]+>\s*)?'
        r'(?:\w+\.)?(\w+)',
        re.MULTILINE
    )

    # Contracts
    CONTRACT_PATTERN = re.compile(
        r'fun\s+(\w+)\s*\([^)]*\)\s*(?::\s*[\w<>,.\s?*]+)?\s*\{[^}]*'
        r'contract\s*\{([^}]*)\}',
        re.DOTALL
    )

    # Expect/actual declarations
    EXPECT_ACTUAL_PATTERN = re.compile(
        r'(expect|actual)\s+'
        r'(?:(suspend|inline)\s+)?'
        r'(class|fun|val|var|interface|object|enum\s+class)\s+'
        r'(\w+)',
        re.MULTILINE
    )

    # DSL marker
    DSL_MARKER_PATTERN = re.compile(
        r'@DslMarker\s*'
        r'annotation\s+class\s+(\w+)',
        re.MULTILINE
    )

    # Validation annotations
    VALIDATION_ANNOTATIONS = {
        'NotNull', 'NotBlank', 'NotEmpty', 'Size', 'Min', 'Max',
        'Email', 'Pattern', 'Positive', 'PositiveOrZero',
        'Negative', 'NegativeOrZero', 'Past', 'Future',
        'Valid', 'AssertTrue', 'AssertFalse', 'Digits',
    }

    # Lifecycle annotations
    LIFECYCLE_ANNOTATIONS = {
        'PostConstruct', 'PreDestroy', 'EventListener',
        'Scheduled', 'Async', 'Transactional',
    }

    # Test annotations
    TEST_ANNOTATIONS = {
        'Test', 'BeforeEach', 'AfterEach', 'BeforeAll', 'AfterAll',
        'Nested', 'DisplayName', 'ParameterizedTest', 'RepeatedTest',
        'ExtendWith', 'SpringBootTest', 'MockkTest', 'MockK', 'InjectMockKs',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all annotation and metadata definitions from Kotlin source code.

        Returns dict with keys: annotation_defs, annotation_usages, delegations,
                                di_bindings, multiplatform_decls, context_receivers,
                                contracts, dsl_markers
        """
        result = {
            'annotation_defs': [],
            'annotation_usages': [],
            'delegations': [],
            'di_bindings': [],
            'multiplatform_decls': [],
            'context_receivers': [],
            'contracts': [],
            'dsl_markers': [],
        }

        if not content or not content.strip():
            return result

        # Extract custom annotation definitions
        self._extract_annotation_defs(content, file_path, result)

        # Extract delegation patterns
        self._extract_delegations(content, file_path, result)

        # Extract DI bindings (Koin, Dagger/Hilt, Spring)
        self._extract_di_bindings(content, file_path, result)

        # Extract annotation usages
        self._extract_annotation_usages(content, file_path, result)

        # Extract multiplatform declarations
        self._extract_multiplatform(content, file_path, result)

        # Extract context receivers
        self._extract_context_receivers(content, file_path, result)

        # Extract contracts
        self._extract_contracts(content, file_path, result)

        # Extract DSL markers
        self._extract_dsl_markers(content, file_path, result)

        return result

    def _extract_annotation_defs(self, content: str, file_path: str,
                                  result: Dict[str, Any]):
        """Extract custom annotation class definitions."""
        for match in self.ANNOTATION_DEF_PATTERN.finditer(content):
            targets_str = match.group(1) or ""
            retention = match.group(2) or ""
            name = match.group(3)
            params_str = match.group(4) or ""
            line = content[:match.start()].count('\n') + 1

            # Parse targets
            targets = []
            if targets_str:
                for t in re.finditer(r'AnnotationTarget\.(\w+)', targets_str):
                    targets.append(t.group(1))

            # Parse parameters
            parameters = []
            if params_str:
                for p in re.finditer(r'(?:val|var)\s+(\w+)\s*:\s*([\w<>,.\s?*]+)', params_str):
                    parameters.append({
                        'name': p.group(1),
                        'type': p.group(2).strip(),
                    })

            is_repeatable = '@Repeatable' in content[max(0, match.start() - 50):match.start()]

            result['annotation_defs'].append(KotlinAnnotationDefInfo(
                name=name,
                targets=targets,
                retention=retention,
                parameters=parameters,
                is_repeatable=is_repeatable,
                file=file_path,
                line_number=line,
            ))

    def _extract_delegations(self, content: str, file_path: str,
                              result: Dict[str, Any]):
        """Extract delegation patterns."""
        for match in self.DELEGATION_PATTERN.finditer(content):
            prop_name = match.group(1)
            delegate_type = match.group(2)
            line = content[:match.start()].count('\n') + 1

            result['delegations'].append(KotlinDelegationInfo(
                property_name=prop_name,
                delegate_type=delegate_type,
                is_lazy=delegate_type == 'lazy',
                file=file_path,
                line_number=line,
            ))

    def _extract_di_bindings(self, content: str, file_path: str,
                              result: Dict[str, Any]):
        """Extract dependency injection bindings."""
        # Koin modules
        for match in self.KOIN_MODULE_PATTERN.finditer(content):
            module_name = match.group(1)
            line = content[:match.start()].count('\n') + 1

            # Find module body
            brace_pos = content.find('{', match.end() - 1)
            body = self._extract_body(content, brace_pos) if brace_pos >= 0 else ""

            # Extract bindings
            for binding in self.KOIN_BINDING_PATTERN.finditer(body):
                kind = binding.group(1)
                type_bound = binding.group(2) or ""
                result['di_bindings'].append(KotlinDIBindingInfo(
                    framework='koin',
                    kind=kind,
                    type_bound=type_bound,
                    scope=module_name,
                    file=file_path,
                    line_number=line,
                ))

        # Dagger/Hilt modules
        for match in self.DAGGER_MODULE_PATTERN.finditer(content):
            component = match.group(1) or ""
            module_name = match.group(2)
            line = content[:match.start()].count('\n') + 1

            brace_pos = content.find('{', match.end())
            body = self._extract_body(content, brace_pos) if brace_pos >= 0 else ""

            for provides in self.DAGGER_PROVIDES_PATTERN.finditer(body):
                kind = provides.group(1).lower()
                scope = provides.group(2) or ""
                func_name = provides.group(3)
                type_bound = provides.group(4).strip()
                result['di_bindings'].append(KotlinDIBindingInfo(
                    framework='dagger',
                    kind=kind,
                    type_bound=type_bound,
                    scope=scope or component,
                    file=file_path,
                    line_number=line,
                ))

        # Spring DI annotations
        for match in self.SPRING_DI_PATTERN.finditer(content):
            annotation = match.group(1)
            value = match.group(2) or ""
            line = content[:match.start()].count('\n') + 1

            if annotation in ('Component', 'Service', 'Repository', 'Configuration'):
                # Find the class/object name
                rest = content[match.end():match.end() + 200]
                class_match = re.search(r'(?:class|object)\s+(\w+)', rest)
                type_bound = class_match.group(1) if class_match else ""
                result['di_bindings'].append(KotlinDIBindingInfo(
                    framework='spring',
                    kind=annotation.lower(),
                    type_bound=type_bound,
                    file=file_path,
                    line_number=line,
                ))
            elif annotation == 'Bean':
                rest = content[match.end():match.end() + 200]
                func_match = re.search(r'fun\s+(\w+)', rest)
                type_bound = func_match.group(1) if func_match else ""
                result['di_bindings'].append(KotlinDIBindingInfo(
                    framework='spring',
                    kind='bean',
                    type_bound=type_bound,
                    file=file_path,
                    line_number=line,
                ))

    def _extract_annotation_usages(self, content: str, file_path: str,
                                    result: Dict[str, Any]):
        """Extract categorized annotation usage patterns."""
        for match in re.finditer(r'@(\w+)\s*(?:\(([^)]*)\))?\s*\n?\s*'
                                  r'(?:(?:data|sealed|abstract|open|inner|annotation|value|inline)\s+)*'
                                  r'(?:(class|fun|val|var|object|interface)\s+(\w+))?',
                                  content):
            annotation = match.group(1)
            args_str = match.group(2) or ""
            target_kind = match.group(3) or ""
            target_name = match.group(4) or ""
            line = content[:match.start()].count('\n') + 1

            # Categorize
            category = self._categorize_annotation(annotation)
            if not category:
                continue

            # Parse arguments
            arguments = {}
            if args_str:
                for arg in re.finditer(r'(\w+)\s*=\s*("[^"]*"|\w+|[^,]+)', args_str):
                    arguments[arg.group(1)] = arg.group(2).strip('"')

            result['annotation_usages'].append(KotlinAnnotationUsageInfo(
                annotation=annotation,
                category=category,
                target_name=target_name,
                target_kind=target_kind,
                arguments=arguments,
                file=file_path,
                line_number=line,
            ))

    def _extract_multiplatform(self, content: str, file_path: str,
                                result: Dict[str, Any]):
        """Extract Kotlin multiplatform expect/actual declarations."""
        for match in self.EXPECT_ACTUAL_PATTERN.finditer(content):
            modifier = match.group(1)
            kind = match.group(3)
            name = match.group(4)
            line = content[:match.start()].count('\n') + 1

            # Determine platform from file path
            platform = 'common'
            fp_lower = file_path.lower()
            if 'jvmmain' in fp_lower or 'jvm' in fp_lower:
                platform = 'jvm'
            elif 'jsmain' in fp_lower or 'js' in fp_lower:
                platform = 'js'
            elif 'nativemain' in fp_lower or 'native' in fp_lower:
                platform = 'native'
            elif 'iosmain' in fp_lower or 'ios' in fp_lower:
                platform = 'ios'
            elif 'androidmain' in fp_lower or 'android' in fp_lower:
                platform = 'android'

            result['multiplatform_decls'].append(KotlinMultiplatformDeclInfo(
                name=name,
                kind=kind,
                is_expect=modifier == 'expect',
                platform=platform,
                file=file_path,
                line_number=line,
            ))

    def _extract_context_receivers(self, content: str, file_path: str,
                                    result: Dict[str, Any]):
        """Extract context receiver declarations."""
        for match in self.CONTEXT_RECEIVER_PATTERN.finditer(content):
            contexts_str = match.group(1)
            func_name = match.group(2)
            line = content[:match.start()].count('\n') + 1

            context_types = [c.strip() for c in contexts_str.split(',')]

            result['context_receivers'].append(KotlinContextReceiverInfo(
                function_name=func_name,
                context_types=context_types,
                file=file_path,
                line_number=line,
            ))

    def _extract_contracts(self, content: str, file_path: str,
                            result: Dict[str, Any]):
        """Extract Kotlin contract declarations."""
        for match in self.CONTRACT_PATTERN.finditer(content):
            func_name = match.group(1)
            contract_body = match.group(2)
            line = content[:match.start()].count('\n') + 1

            effects = []
            for effect in re.finditer(r'(returns|callsInPlace|returnsNotNull)\s*\([^)]*\)', contract_body):
                effects.append(effect.group(0).strip())

            result['contracts'].append(KotlinContractInfo(
                function_name=func_name,
                effects=effects,
                file=file_path,
                line_number=line,
            ))

    def _extract_dsl_markers(self, content: str, file_path: str,
                              result: Dict[str, Any]):
        """Extract DSL marker annotation definitions."""
        for match in self.DSL_MARKER_PATTERN.finditer(content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            result['dsl_markers'].append({
                'name': name,
                'file': file_path,
                'line': line,
            })

    def _categorize_annotation(self, annotation: str) -> str:
        """Categorize an annotation by its purpose."""
        if annotation in self.VALIDATION_ANNOTATIONS:
            return 'validation'
        if annotation in self.LIFECYCLE_ANNOTATIONS:
            return 'lifecycle'
        if annotation in self.TEST_ANNOTATIONS:
            return 'test'
        if annotation in ('Component', 'Service', 'Repository', 'Configuration',
                          'Bean', 'Autowired', 'Inject', 'Value', 'Qualifier',
                          'Primary', 'Scope', 'Lazy'):
            return 'di'
        if annotation in ('Serializable', 'SerialName', 'Transient', 'Contextual'):
            return 'serialization'
        if annotation in ('Composable', 'Preview', 'Stable', 'Immutable'):
            return 'compose'
        if annotation in ('GetMapping', 'PostMapping', 'PutMapping', 'DeleteMapping',
                          'PatchMapping', 'RequestMapping', 'PathVariable',
                          'RequestBody', 'RequestParam', 'ResponseStatus',
                          'RestController', 'Controller'):
            return 'web'
        if annotation in ('Entity', 'Table', 'Column', 'Id', 'GeneratedValue',
                          'OneToMany', 'ManyToOne', 'OneToOne', 'ManyToMany',
                          'JoinColumn', 'MappedSuperclass', 'Embeddable'):
            return 'persistence'
        return ""

    def _extract_body(self, content: str, brace_pos: int) -> str:
        """Extract body from opening brace to matching closing brace."""
        if brace_pos < 0 or brace_pos >= len(content) or content[brace_pos] != '{':
            return ""
        depth = 0
        i = brace_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[brace_pos + 1:i]
            elif content[i] == '"':
                i += 1
                while i < len(content) and content[i] != '"':
                    if content[i] == '\\':
                        i += 1
                    i += 1
            i += 1
        return content[brace_pos + 1:]
