"""
Enhanced Symfony Framework Parser for CodeTrellis.

v5.3: Full Symfony framework support (3.x through 7.x).
Extracts bundles, services, Doctrine entities, console commands,
event subscribers, Twig templates, security voters, form types,
serializer configs, controllers, routes (attributes/annotations),
message handlers, middleware, validators, data transformers.

Runs AFTER the base PHP parser when Symfony framework is detected.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ===== DATACLASSES =====

@dataclass
class SymfonyRouteInfo:
    """Information about a Symfony route."""
    method: str  # GET, POST, PUT, DELETE, ANY
    path: str
    controller: str = ""
    action: str = ""
    name: str = ""
    requirements: List[str] = field(default_factory=list)
    defaults: Dict[str, str] = field(default_factory=dict)
    is_attribute: bool = False  # PHP 8 attribute vs annotation
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyControllerInfo:
    """Information about a Symfony controller."""
    name: str
    parent_class: str = ""
    actions: List[str] = field(default_factory=list)
    is_abstract: bool = False
    template_engine: str = ""  # twig, php
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyEntityInfo:
    """Information about a Doctrine entity."""
    name: str
    table_name: str = ""
    repository_class: str = ""
    columns: List[Dict[str, str]] = field(default_factory=list)
    relationships: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    lifecycle_callbacks: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    is_mapped_superclass: bool = False
    is_embeddable: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyServiceInfo:
    """Information about a Symfony service."""
    name: str
    class_name: str = ""
    tags: List[str] = field(default_factory=list)
    arguments: List[str] = field(default_factory=list)
    is_autowired: bool = False
    is_autoconfigured: bool = False
    is_lazy: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyCommandInfo:
    """Information about a Symfony console command."""
    name: str
    command_name: str = ""
    description: str = ""
    arguments: List[str] = field(default_factory=list)
    options: List[str] = field(default_factory=list)
    is_hidden: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyEventSubscriberInfo:
    """Information about a Symfony event subscriber."""
    name: str
    events: List[str] = field(default_factory=list)
    priority: int = 0
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyFormTypeInfo:
    """Information about a Symfony form type."""
    name: str
    parent_type: str = ""
    fields: List[Dict[str, str]] = field(default_factory=list)
    data_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyVoterInfo:
    """Information about a Symfony security voter."""
    name: str
    attributes: List[str] = field(default_factory=list)
    subject_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyMessageHandlerInfo:
    """Information about a Symfony Messenger handler."""
    name: str
    message_class: str = ""
    bus: str = ""
    is_async: bool = False
    transport: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyValidatorInfo:
    """Information about a Symfony validator constraint."""
    name: str
    target: str = ""  # property, class, method
    constraint_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyTwigExtensionInfo:
    """Information about a Twig extension."""
    name: str
    functions: List[str] = field(default_factory=list)
    filters: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyBundleInfo:
    """Information about a Symfony bundle."""
    name: str
    namespace: str = ""
    parent_bundle: str = ""
    extension_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyConfigInfo:
    """Information about Symfony configuration."""
    key: str
    value: str = ""
    section: str = ""  # framework, security, doctrine, etc.
    file: str = ""
    line_number: int = 0


@dataclass
class SymfonyParseResult:
    """Complete parse result for a Symfony file."""
    file_path: str
    file_type: str = "php"

    # Routes
    routes: List[SymfonyRouteInfo] = field(default_factory=list)

    # Controllers
    controllers: List[SymfonyControllerInfo] = field(default_factory=list)

    # Doctrine Entities
    entities: List[SymfonyEntityInfo] = field(default_factory=list)

    # Services
    services: List[SymfonyServiceInfo] = field(default_factory=list)

    # Commands
    commands: List[SymfonyCommandInfo] = field(default_factory=list)

    # Event Subscribers
    event_subscribers: List[SymfonyEventSubscriberInfo] = field(default_factory=list)

    # Form Types
    form_types: List[SymfonyFormTypeInfo] = field(default_factory=list)

    # Security Voters
    voters: List[SymfonyVoterInfo] = field(default_factory=list)

    # Messenger Handlers
    message_handlers: List[SymfonyMessageHandlerInfo] = field(default_factory=list)

    # Validators
    validators: List[SymfonyValidatorInfo] = field(default_factory=list)

    # Twig Extensions
    twig_extensions: List[SymfonyTwigExtensionInfo] = field(default_factory=list)

    # Bundles
    bundles: List[SymfonyBundleInfo] = field(default_factory=list)

    # Configuration
    configs: List[SymfonyConfigInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    symfony_version: str = ""
    has_doctrine: bool = False
    has_twig: bool = False
    has_messenger: bool = False
    has_security: bool = False
    has_api_platform: bool = False
    has_mercure: bool = False
    has_webpack_encore: bool = False


# ===== PARSER =====

class EnhancedSymfonyParser:
    """
    Enhanced parser for Symfony framework (3.x through 7.x).
    Extracts routes, controllers, entities, services, commands,
    event subscribers, form types, voters, message handlers,
    validators, Twig extensions, bundles, configurations.
    """

    # Detection pattern
    SYMFONY_DETECT = re.compile(
        r"(?:Symfony\\|AbstractController|AbstractBundle|"
        r"KernelInterface|ContainerInterface|EventSubscriberInterface|"
        r"#\[Route\(|#\[ORM\\|@Route\(|@ORM\\|"
        r"namespace\s+App\\|use\s+Symfony\\)",
        re.MULTILINE,
    )

    # Framework ecosystem patterns
    FRAMEWORK_PATTERNS = {
        'symfony': re.compile(r'(?:Symfony\\Component|Symfony\\Bundle)'),
        'doctrine': re.compile(r'(?:Doctrine\\ORM|Doctrine\\DBAL|#\[ORM\\|@ORM\\)'),
        'twig': re.compile(r'(?:Twig\\|\.html\.twig|AbstractExtension|TwigFunction)'),
        'messenger': re.compile(r'(?:Symfony\\.*Messenger|MessageHandlerInterface|#\[AsMessageHandler\])'),
        'security': re.compile(r'(?:Symfony\\.*Security|VoterInterface|IsGranted|#\[Security\])'),
        'api_platform': re.compile(r'(?:ApiPlatform\\|#\[ApiResource\]|#\[ApiFilter\])'),
        'mercure': re.compile(r'(?:Symfony\\.*Mercure|MercureBundle)'),
        'webpack_encore': re.compile(r'(?:webpack_encore|encore_entry)'),
        'easyadmin': re.compile(r'(?:EasyCorp\\Bundle\\EasyAdminBundle|AbstractCrudController)'),
        'maker_bundle': re.compile(r'(?:Symfony\\.*MakerBundle)'),
        'flex': re.compile(r'(?:symfony/flex)'),
        'ux': re.compile(r'(?:Symfony\\UX|stimulus_controller)'),
        'panther': re.compile(r'(?:Symfony\\.*Panther|PantherTestCase)'),
        'monolog': re.compile(r'(?:Monolog\\|LoggerInterface)'),
    }

    # Route patterns (PHP 8 attributes)
    ROUTE_ATTRIBUTE = re.compile(
        r"#\[Route\s*\(\s*['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*name\s*:\s*['\"]([^'\"]+)['\"])?"
        r"(?:\s*,\s*methods\s*:\s*\[([^\]]*)\])?",
        re.MULTILINE,
    )
    # Route annotation (legacy)
    ROUTE_ANNOTATION = re.compile(
        r"@Route\s*\(\s*['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*name\s*=\s*['\"]([^'\"]+)['\"])?"
        r"(?:\s*,\s*methods\s*=\s*\{([^}]*)\})?",
        re.MULTILINE,
    )

    # Controller pattern
    CONTROLLER_PATTERN = re.compile(
        r"class\s+(\w+Controller)\s+extends\s+(\w+)",
        re.MULTILINE,
    )
    CONTROLLER_ACTION = re.compile(
        r"public\s+function\s+(\w+)\s*\(",
    )

    # Entity patterns (PHP 8 attributes)
    ENTITY_ATTRIBUTE = re.compile(
        r"#\[ORM\\Entity\s*(?:\(([^)]*)\))?\]",
        re.MULTILINE,
    )
    ENTITY_ANNOTATION = re.compile(
        r"@ORM\\Entity\s*(?:\(([^)]*)\))?",
        re.MULTILINE,
    )
    ENTITY_CLASS = re.compile(
        r"class\s+(\w+)\s*\{",
        re.MULTILINE,
    )
    TABLE_ATTRIBUTE = re.compile(
        r"#\[ORM\\Table\s*\(\s*name\s*:\s*['\"](\w+)['\"]",
    )
    TABLE_ANNOTATION = re.compile(
        r"@ORM\\Table\s*\(\s*name\s*=\s*['\"](\w+)['\"]",
    )
    COLUMN_ATTRIBUTE = re.compile(
        r"#\[ORM\\Column\s*\(([^)]*)\)\]",
    )
    COLUMN_ANNOTATION = re.compile(
        r"@ORM\\Column\s*\(([^)]*)\)",
    )
    RELATIONSHIP_ATTRIBUTE = re.compile(
        r"#\[ORM\\(OneToOne|OneToMany|ManyToOne|ManyToMany)\s*\(\s*"
        r"(?:targetEntity\s*:\s*)?(?:(\w+)::class|['\"]([^'\"]+)['\"])",
    )
    RELATIONSHIP_ANNOTATION = re.compile(
        r"@ORM\\(OneToOne|OneToMany|ManyToOne|ManyToMany)\s*\(\s*"
        r"targetEntity\s*=\s*['\"]([^'\"]+)['\"]",
    )

    # Service patterns
    SERVICE_ATTRIBUTE = re.compile(
        r"#\[(?:AsTaggedItem|Autoconfigure|AutoconfigureTag|AsAlias)\s*\(",
    )
    SERVICE_TAG = re.compile(
        r"#\[AsTaggedItem\s*\(\s*['\"]([^'\"]+)['\"]",
    )

    # Command patterns
    COMMAND_ATTRIBUTE = re.compile(
        r"#\[AsCommand\s*\(\s*(?:name\s*:\s*)?['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*(?:description\s*:\s*)?['\"]([^'\"]+)['\"])?",
    )
    COMMAND_CLASS = re.compile(
        r"class\s+(\w+Command)\s+extends\s+Command",
        re.MULTILINE,
    )
    COMMAND_NAME_PROP = re.compile(
        r"(?:protected\s+static\s+\$defaultName|static\s+\$defaultName)\s*=\s*['\"]([^'\"]+)['\"]",
    )

    # Event subscriber pattern
    EVENT_SUBSCRIBER_CLASS = re.compile(
        r"class\s+(\w+(?:Subscriber|Listener)?)\s+implements\s+EventSubscriberInterface",
        re.MULTILINE,
    )
    SUBSCRIBED_EVENTS = re.compile(
        r"getSubscribedEvents\s*\([^)]*\).*?return\s+\[([^\]]*(?:\[[^\]]*\][^\]]*)*)\]",
        re.DOTALL,
    )

    # Form type pattern
    FORM_TYPE_CLASS = re.compile(
        r"class\s+(\w+Type)\s+extends\s+AbstractType",
        re.MULTILINE,
    )
    FORM_FIELD = re.compile(
        r"\$(?:builder|form)->add\s*\(\s*['\"](\w+)['\"]"
        r"(?:\s*,\s*(\w+Type)::class)?",
    )

    # Voter pattern
    VOTER_CLASS = re.compile(
        r"class\s+(\w+Voter)\s+extends\s+Voter",
        re.MULTILINE,
    )
    VOTER_ATTRIBUTE = re.compile(
        r"(?:const|case)\s+(\w+)\s*=\s*['\"](\w+)['\"]",
    )

    # Message handler patterns
    MESSAGE_HANDLER_ATTRIBUTE = re.compile(
        r"#\[AsMessageHandler\s*(?:\(([^)]*)\))?\]",
    )
    MESSAGE_HANDLER_CLASS = re.compile(
        r"class\s+(\w+Handler)\s+",
        re.MULTILINE,
    )
    MESSAGE_HANDLER_INVOKE = re.compile(
        r"public\s+function\s+__invoke\s*\(\s*(\w+)\s+\$",
    )

    # Twig extension patterns
    TWIG_EXTENSION_CLASS = re.compile(
        r"class\s+(\w+Extension)\s+extends\s+AbstractExtension",
        re.MULTILINE,
    )
    TWIG_FUNCTION = re.compile(
        r"new\s+TwigFunction\s*\(\s*['\"](\w+)['\"]",
    )
    TWIG_FILTER = re.compile(
        r"new\s+TwigFilter\s*\(\s*['\"](\w+)['\"]",
    )

    # Bundle patterns
    BUNDLE_CLASS = re.compile(
        r"class\s+(\w+Bundle)\s+extends\s+(?:Abstract)?Bundle",
        re.MULTILINE,
    )

    # Validator patterns
    CONSTRAINT_ATTRIBUTE = re.compile(
        r"#\[Assert\\(\w+)\s*(?:\(([^)]*)\))?\]",
    )
    CONSTRAINT_ANNOTATION = re.compile(
        r"@Assert\\(\w+)\s*(?:\(([^)]*)\))?",
    )

    # Version detection
    VERSION_PATTERNS = [
        (r'#\[AsCommand\b|#\[AsMessageHandler\b|#\[AsTaggedItem\b', '6.x'),
        (r'#\[Route\b|#\[ORM\\', '5.x+'),  # PHP 8 attributes (Symfony 5.2+)
        (r'Symfony\\Component\\Uid|AbstractUid', '5.x'),
        (r'Symfony\\Component\\Mailer|Mailer\\MailerInterface', '4.x'),
        (r'Symfony\\Component\\Messenger', '4.x'),
        (r'@Route\(|@ORM\\Entity', '3.x+'),
    ]

    def parse(self, content: str, file_path: str = "") -> SymfonyParseResult:
        """Parse PHP source code for Symfony-specific patterns."""
        result = SymfonyParseResult(file_path=file_path)

        if not content.strip():
            return result

        # Check if this file uses Symfony
        if not self.SYMFONY_DETECT.search(content):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version
        result.symfony_version = self._detect_version(content)

        # Ecosystem detection
        result.has_doctrine = bool(self.FRAMEWORK_PATTERNS['doctrine'].search(content))
        result.has_twig = bool(self.FRAMEWORK_PATTERNS['twig'].search(content))
        result.has_messenger = bool(self.FRAMEWORK_PATTERNS['messenger'].search(content))
        result.has_security = bool(self.FRAMEWORK_PATTERNS['security'].search(content))
        result.has_api_platform = bool(self.FRAMEWORK_PATTERNS['api_platform'].search(content))
        result.has_mercure = bool(self.FRAMEWORK_PATTERNS['mercure'].search(content))
        result.has_webpack_encore = bool(self.FRAMEWORK_PATTERNS['webpack_encore'].search(content))

        # Extract all entities
        self._extract_routes(content, file_path, result)
        self._extract_controllers(content, file_path, result)
        self._extract_entities(content, file_path, result)
        self._extract_commands(content, file_path, result)
        self._extract_event_subscribers(content, file_path, result)
        self._extract_form_types(content, file_path, result)
        self._extract_voters(content, file_path, result)
        self._extract_message_handlers(content, file_path, result)
        self._extract_twig_extensions(content, file_path, result)
        self._extract_bundles(content, file_path, result)
        self._extract_validators(content, file_path, result)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Symfony ecosystem frameworks used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """Detect Symfony version from code features."""
        for pattern, version in self.VERSION_PATTERNS:
            if re.search(pattern, content):
                return version
        return ""

    def _get_line(self, content: str, pos: int) -> int:
        """Get 1-based line number for a position."""
        return content[:pos].count('\n') + 1

    def _extract_routes(self, content: str, file_path: str, result: SymfonyParseResult):
        """Extract Symfony route definitions (attributes and annotations)."""
        # PHP 8 attributes
        for m in self.ROUTE_ATTRIBUTE.finditer(content):
            path = m.group(1)
            name = m.group(2) or ""
            methods_str = m.group(3) or ""
            methods = [s.strip().strip("'\"") for s in methods_str.split(',') if s.strip()] if methods_str else ["ANY"]
            line = self._get_line(content, m.start())
            for method in methods:
                route = SymfonyRouteInfo(
                    method=method.upper() if method != "ANY" else "ANY",
                    path=path,
                    name=name,
                    is_attribute=True,
                    file=file_path,
                    line_number=line,
                )
                result.routes.append(route)

        # Legacy annotations
        for m in self.ROUTE_ANNOTATION.finditer(content):
            path = m.group(1)
            name = m.group(2) or ""
            methods_str = m.group(3) or ""
            methods = [s.strip().strip("'\"") for s in methods_str.split(',') if s.strip()] if methods_str else ["ANY"]
            line = self._get_line(content, m.start())
            for method in methods:
                route = SymfonyRouteInfo(
                    method=method.upper() if method != "ANY" else "ANY",
                    path=path,
                    name=name,
                    is_attribute=False,
                    file=file_path,
                    line_number=line,
                )
                result.routes.append(route)

    def _extract_controllers(self, content: str, file_path: str, result: SymfonyParseResult):
        """Extract Symfony controller definitions."""
        for m in self.CONTROLLER_PATTERN.finditer(content):
            name = m.group(1)
            parent = m.group(2)
            line = self._get_line(content, m.start())
            actions = [am.group(1) for am in self.CONTROLLER_ACTION.finditer(content)
                       if am.group(1) not in ('__construct', '__invoke')]
            is_abstract = bool(re.search(r'abstract\s+class', content[:m.start() + 100]))
            ctrl = SymfonyControllerInfo(
                name=name,
                parent_class=parent,
                actions=actions[:30],
                is_abstract=is_abstract,
                file=file_path,
                line_number=line,
            )
            result.controllers.append(ctrl)

    def _extract_entities(self, content: str, file_path: str, result: SymfonyParseResult):
        """Extract Doctrine entity definitions."""
        # Check for entity attribute or annotation
        entity_m = self.ENTITY_ATTRIBUTE.search(content) or self.ENTITY_ANNOTATION.search(content)
        if not entity_m:
            return

        # Get class name
        class_m = self.ENTITY_CLASS.search(content)
        if not class_m:
            return

        name = class_m.group(1)
        line = self._get_line(content, class_m.start())

        # Table name
        table = ""
        table_m = self.TABLE_ATTRIBUTE.search(content) or self.TABLE_ANNOTATION.search(content)
        if table_m:
            table = table_m.group(1)

        # Repository class
        repo = ""
        repo_m = re.search(r"repositoryClass\s*[:=]\s*(?:(\w+)::class|['\"]([^'\"]+)['\"])", content)
        if repo_m:
            repo = (repo_m.group(1) or repo_m.group(2) or "").split('\\')[-1]

        # Columns
        columns = []
        for col_m in self.COLUMN_ATTRIBUTE.finditer(content):
            args = col_m.group(1)
            col_type = ""
            type_m = re.search(r"type\s*:\s*['\"](\w+)['\"]", args)
            if type_m:
                col_type = type_m.group(1)
            # Get the property name from next line
            next_content = content[col_m.end():col_m.end() + 200]
            prop_m = re.search(r'(?:private|protected|public)\s+(?:\?\s*)?(\w+)\s+\$(\w+)', next_content)
            if prop_m:
                columns.append({"name": prop_m.group(2), "type": col_type or prop_m.group(1)})

        # Relationships
        relationships = []
        for rel_m in self.RELATIONSHIP_ATTRIBUTE.finditer(content):
            rel_type = rel_m.group(1)
            related = (rel_m.group(2) or rel_m.group(3) or "").split('\\')[-1]
            relationships.append({"type": rel_type, "related": related})
        for rel_m in self.RELATIONSHIP_ANNOTATION.finditer(content):
            rel_type = rel_m.group(1)
            related = rel_m.group(2).split('\\')[-1]
            relationships.append({"type": rel_type, "related": related})

        # Lifecycle callbacks
        callbacks = []
        for cb_m in re.finditer(r"#\[ORM\\(?:PrePersist|PostPersist|PreUpdate|PostUpdate|PreRemove|PostRemove|PostLoad)\]", content):
            cb_type = re.search(r'ORM\\(\w+)', cb_m.group()).group(1)
            callbacks.append(cb_type)

        is_mapped = bool(re.search(r'#\[ORM\\MappedSuperclass\]|@ORM\\MappedSuperclass', content))
        is_embeddable = bool(re.search(r'#\[ORM\\Embeddable\]|@ORM\\Embeddable', content))

        entity = SymfonyEntityInfo(
            name=name,
            table_name=table,
            repository_class=repo,
            columns=columns[:30],
            relationships=relationships[:20],
            lifecycle_callbacks=callbacks[:10],
            is_mapped_superclass=is_mapped,
            is_embeddable=is_embeddable,
            file=file_path,
            line_number=line,
        )
        result.entities.append(entity)

    def _extract_commands(self, content: str, file_path: str, result: SymfonyParseResult):
        """Extract Symfony console command definitions."""
        # PHP 8 attribute style
        for m in self.COMMAND_ATTRIBUTE.finditer(content):
            cmd_name = m.group(1)
            desc = m.group(2) or ""
            line = self._get_line(content, m.start())
            # Get class name
            class_m = self.COMMAND_CLASS.search(content)
            name = class_m.group(1) if class_m else cmd_name
            cmd = SymfonyCommandInfo(
                name=name,
                command_name=cmd_name,
                description=desc,
                file=file_path,
                line_number=line,
            )
            result.commands.append(cmd)
            return  # Only one command per file

        # Legacy style
        for m in self.COMMAND_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            cmd_name = ""
            name_m = self.COMMAND_NAME_PROP.search(content)
            if name_m:
                cmd_name = name_m.group(1)
            cmd = SymfonyCommandInfo(
                name=name,
                command_name=cmd_name,
                file=file_path,
                line_number=line,
            )
            result.commands.append(cmd)

    def _extract_event_subscribers(self, content: str, file_path: str, result: SymfonyParseResult):
        """Extract Symfony event subscriber definitions."""
        for m in self.EVENT_SUBSCRIBER_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            events = []
            ev_m = self.SUBSCRIBED_EVENTS.search(content)
            if ev_m:
                for evt in re.finditer(r"(\w+)::(?:\w+)|['\"](\w+[\.\w]*)['\"]", ev_m.group(1)):
                    events.append(evt.group(1) or evt.group(2))
            sub = SymfonyEventSubscriberInfo(
                name=name,
                events=events[:15],
                file=file_path,
                line_number=line,
            )
            result.event_subscribers.append(sub)

    def _extract_form_types(self, content: str, file_path: str, result: SymfonyParseResult):
        """Extract Symfony form type definitions."""
        for m in self.FORM_TYPE_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            fields = []
            for field_m in self.FORM_FIELD.finditer(content):
                field_name = field_m.group(1)
                field_type = field_m.group(2) or ""
                fields.append({"name": field_name, "type": field_type})
            data_class = ""
            dc_m = re.search(r"'data_class'\s*=>\s*(\w+)::class|data_class\s*:\s*(\w+)::class", content)
            if dc_m:
                data_class = (dc_m.group(1) or dc_m.group(2) or "")
            ft = SymfonyFormTypeInfo(
                name=name,
                fields=fields[:20],
                data_class=data_class,
                file=file_path,
                line_number=line,
            )
            result.form_types.append(ft)

    def _extract_voters(self, content: str, file_path: str, result: SymfonyParseResult):
        """Extract Symfony security voter definitions."""
        for m in self.VOTER_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            attributes = [va.group(2) for va in self.VOTER_ATTRIBUTE.finditer(content)]
            subject = ""
            sub_m = re.search(r"function\s+supports\s*\([^,]+,\s*\$subject\).*?instanceof\s+(\w+)", content, re.DOTALL)
            if sub_m:
                subject = sub_m.group(1)
            voter = SymfonyVoterInfo(
                name=name,
                attributes=attributes[:10],
                subject_class=subject,
                file=file_path,
                line_number=line,
            )
            result.voters.append(voter)

    def _extract_message_handlers(self, content: str, file_path: str, result: SymfonyParseResult):
        """Extract Symfony Messenger handler definitions."""
        # Attribute-based
        for m in self.MESSAGE_HANDLER_ATTRIBUTE.finditer(content):
            line = self._get_line(content, m.start())
            class_m = self.MESSAGE_HANDLER_CLASS.search(content)
            name = class_m.group(1) if class_m else "Handler"
            msg_class = ""
            invoke_m = self.MESSAGE_HANDLER_INVOKE.search(content)
            if invoke_m:
                msg_class = invoke_m.group(1)
            handler = SymfonyMessageHandlerInfo(
                name=name,
                message_class=msg_class,
                file=file_path,
                line_number=line,
            )
            result.message_handlers.append(handler)
            return

        # Interface-based
        if re.search(r'MessageHandlerInterface', content):
            class_m = self.MESSAGE_HANDLER_CLASS.search(content)
            if class_m:
                name = class_m.group(1)
                line = self._get_line(content, class_m.start())
                msg_class = ""
                invoke_m = self.MESSAGE_HANDLER_INVOKE.search(content)
                if invoke_m:
                    msg_class = invoke_m.group(1)
                handler = SymfonyMessageHandlerInfo(
                    name=name,
                    message_class=msg_class,
                    file=file_path,
                    line_number=line,
                )
                result.message_handlers.append(handler)

    def _extract_twig_extensions(self, content: str, file_path: str, result: SymfonyParseResult):
        """Extract Twig extension definitions."""
        for m in self.TWIG_EXTENSION_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            functions = [f.group(1) for f in self.TWIG_FUNCTION.finditer(content)]
            filters = [f.group(1) for f in self.TWIG_FILTER.finditer(content)]
            ext = SymfonyTwigExtensionInfo(
                name=name,
                functions=functions[:10],
                filters=filters[:10],
                file=file_path,
                line_number=line,
            )
            result.twig_extensions.append(ext)

    def _extract_bundles(self, content: str, file_path: str, result: SymfonyParseResult):
        """Extract Symfony bundle definitions."""
        for m in self.BUNDLE_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            ns = ""
            ns_m = re.search(r"namespace\s+([\w\\]+)", content)
            if ns_m:
                ns = ns_m.group(1)
            bundle = SymfonyBundleInfo(
                name=name,
                namespace=ns,
                file=file_path,
                line_number=line,
            )
            result.bundles.append(bundle)

    def _extract_validators(self, content: str, file_path: str, result: SymfonyParseResult):
        """Extract Symfony validator constraint usage."""
        for m in self.CONSTRAINT_ATTRIBUTE.finditer(content):
            constraint = m.group(1)
            line = self._get_line(content, m.start())
            validator = SymfonyValidatorInfo(
                name=constraint,
                constraint_class=f"Assert\\{constraint}",
                file=file_path,
                line_number=line,
            )
            result.validators.append(validator)
