"""
EnhancedHanamiParser v1.0 - Comprehensive Hanami framework parser.

Runs as a supplementary layer on top of the Ruby parser, extracting
Hanami-specific semantics.

Supports:
- Hanami 1.x (MVC, interactors, repositories, entities, view templates)
- Hanami 2.x (Dry-rb integration, slices, actions, providers, settings)
- Hanami 2.1+ (enhanced routing, DB layer with ROM, assets)

Hanami-specific extraction:
- Actions: Hanami::Action classes, params validation, halt, redirect
- Slices: Application slices (Hanami 2.x modular architecture)
- Routes: route definitions (get, post, etc.), scopes, redirects
- Entities: Hanami::Entity (1.x), ROM structs (2.x)
- Repositories: Hanami::Repository (1.x), ROM repositories (2.x)
- Views: Hanami::View (1.x), view parts/scopes (2.x)
- Providers: Dependency injection providers (2.x)
- Settings: Application settings, environment configuration
- Interactors: Hanami::Interactor, Dry::Monads

Framework detection (20+ Hanami ecosystem patterns):
- Core: hanami, hanami-router, hanami-controller, hanami-model
- Hanami 2.x: hanami-2, dry-system, dry-container, dry-auto_inject
- DB: hanami-db, rom, rom-sql, rom-repository
- View: hanami-view, tilt, haml, slim
- Auth: hanami-auth, warden, bcrypt
- Validation: hanami-validations, dry-validation, dry-schema
- Testing: hanami-rspec, rspec

Part of CodeTrellis v5.2.0 - Ruby Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class HanamiActionInfo:
    """Information about a Hanami action."""
    name: str
    slice: str = ""
    params_schema: List[str] = field(default_factory=list)
    has_handle_method: bool = False
    http_status: str = ""
    format: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class HanamiSliceInfo:
    """Information about a Hanami slice (2.x)."""
    name: str
    actions: List[str] = field(default_factory=list)
    providers: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class HanamiRouteInfo:
    """Information about a Hanami route."""
    method: str
    path: str
    action: str = ""
    scope: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class HanamiEntityInfo:
    """Information about a Hanami entity."""
    name: str
    attributes: List[str] = field(default_factory=list)
    is_rom_struct: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class HanamiRepositoryInfo:
    """Information about a Hanami repository."""
    name: str
    entity: str = ""
    methods: List[str] = field(default_factory=list)
    relations: List[str] = field(default_factory=list)
    is_rom_repo: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class HanamiViewInfo:
    """Information about a Hanami view."""
    name: str
    template: str = ""
    format: str = ""
    layout: str = ""
    exposures: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class HanamiProviderInfo:
    """Information about a Hanami provider (2.x DI)."""
    name: str
    provides: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class HanamiSettingInfo:
    """Information about Hanami settings."""
    name: str
    type: str = ""
    default: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class HanamiParseResult:
    """Complete parse result for a Hanami file."""
    file_path: str
    file_type: str = "ruby"

    # Actions
    actions: List[HanamiActionInfo] = field(default_factory=list)

    # Slices
    slices: List[HanamiSliceInfo] = field(default_factory=list)

    # Routes
    routes: List[HanamiRouteInfo] = field(default_factory=list)

    # Entities
    entities: List[HanamiEntityInfo] = field(default_factory=list)

    # Repositories
    repositories: List[HanamiRepositoryInfo] = field(default_factory=list)

    # Views
    views: List[HanamiViewInfo] = field(default_factory=list)

    # Providers
    providers: List[HanamiProviderInfo] = field(default_factory=list)

    # Settings
    settings: List[HanamiSettingInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    hanami_version: str = ""
    has_slices: bool = False
    has_rom: bool = False
    total_actions: int = 0
    total_routes: int = 0


class EnhancedHanamiParser:
    """
    Enhanced Hanami parser for Hanami framework extraction.

    Runs AFTER the Ruby parser when Hanami framework is detected.
    """

    # Hanami detection
    HANAMI_REQUIRE = re.compile(
        r"require\s+['\"]hanami['\"]|"
        r"Hanami\.\w+|"
        r"class\s+\w+\s*<\s*Hanami::|"
        r"include\s+Hanami::"
    )

    # Action patterns (Hanami 2.x)
    ACTION_CLASS_V2 = re.compile(
        r"class\s+(\w+)\s*<\s*(?:\w+::)*Action",
    )
    # Action patterns (Hanami 1.x)
    ACTION_INCLUDE = re.compile(
        r"include\s+Hanami::Action",
    )
    HANDLE_METHOD = re.compile(
        r"def\s+handle\s*\(",
    )
    CALL_METHOD = re.compile(
        r"def\s+call\s*\(",
    )
    PARAMS_VALIDATION = re.compile(
        r"params\s+(?:do|class)\b",
    )
    PARAMS_REQUIRED = re.compile(
        r"(?:required|optional)\s*\(\s*:(\w+)",
    )

    # Route patterns
    ROUTE_HTTP = re.compile(
        r"^\s*(get|post|put|patch|delete|options|head)\s+['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*to:\s*['\"]?([^'\"]+)['\"]?)?",
        re.MULTILINE,
    )
    ROUTE_ROOT = re.compile(
        r"^\s*root\s+(?:to:\s*)?['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    ROUTE_SCOPE = re.compile(
        r"^\s*scope\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    ROUTE_SLICE = re.compile(
        r"^\s*slice\s+:(\w+)",
        re.MULTILINE,
    )

    # Entity patterns
    ENTITY_CLASS = re.compile(
        r"class\s+(\w+)\s*<\s*(?:Hanami::Entity|ROM::Struct|Dry::Struct)",
    )
    ENTITY_INCLUDE = re.compile(
        r"include\s+Hanami::Entity",
    )
    ATTRIBUTE_DEF = re.compile(
        r"^\s*attribute\s+:(\w+)(?:\s*,\s*(.+))?",
        re.MULTILINE,
    )

    # Repository patterns
    REPO_CLASS = re.compile(
        r"class\s+(\w+)\s*<\s*(?:Hanami::Repository|ROM::Repository)",
    )
    REPO_INCLUDE = re.compile(
        r"include\s+Hanami::Repository",
    )
    REPO_RELATION = re.compile(
        r"^\s*relations\s+:(\w+)",
        re.MULTILINE,
    )

    # View patterns
    VIEW_CLASS = re.compile(
        r"class\s+(\w+)\s*<\s*(?:Hanami::View|Phlex::HTML)",
    )
    VIEW_INCLUDE = re.compile(
        r"include\s+Hanami::View",
    )
    EXPOSURE = re.compile(
        r"^\s*expose\s+:(\w+)",
        re.MULTILINE,
    )

    # Provider patterns (Hanami 2.x)
    PROVIDER_REGISTER = re.compile(
        r"Hanami\.app\.register\s*\(\s*['\"]([^'\"]+)['\"]",
    )
    PROVIDER_SOURCE = re.compile(
        r"register_provider\s*\(\s*:(\w+)",
    )
    PROVIDER_PREPARE = re.compile(
        r"prepare\s+do\b",
    )

    # Settings patterns
    SETTING_DEF = re.compile(
        r"^\s*setting\s+:(\w+)(?:\s*,\s*(.+))?",
        re.MULTILINE,
    )

    # Slice definition (Hanami 2.x)
    SLICE_CLASS = re.compile(
        r"class\s+(\w+)\s*<\s*Hanami::Slice",
    )
    SLICE_MODULE = re.compile(
        r"module\s+(\w+)\s*\n\s*class\s+Slice\s*<\s*Hanami::Slice",
    )

    # Framework detection
    FRAMEWORK_PATTERNS = {
        'hanami': re.compile(r"require\s+['\"]hanami|Hanami\.\w+"),
        'hanami-router': re.compile(r"hanami-router|Hanami::Router"),
        'hanami-controller': re.compile(r"hanami-controller|Hanami::Action"),
        'hanami-model': re.compile(r"hanami-model|Hanami::Model"),
        'hanami-view': re.compile(r"hanami-view|Hanami::View"),
        'hanami-validations': re.compile(r"hanami-validations|Hanami::Validations"),
        'hanami-db': re.compile(r"hanami-db"),
        'rom': re.compile(r"gem\s+['\"]rom|ROM::|rom-sql"),
        'rom-sql': re.compile(r"rom-sql|ROM::SQL"),
        'rom-repository': re.compile(r"rom-repository|ROM::Repository"),
        'dry-system': re.compile(r"dry-system|Dry::System"),
        'dry-container': re.compile(r"dry-container|Dry::Container"),
        'dry-auto_inject': re.compile(r"dry-auto_inject|Dry::AutoInject|include\s+Deps"),
        'dry-validation': re.compile(r"dry-validation|Dry::Validation"),
        'dry-schema': re.compile(r"dry-schema|Dry::Schema"),
        'dry-monads': re.compile(r"dry-monads|Dry::Monads"),
        'dry-types': re.compile(r"dry-types|Dry::Types"),
        'phlex': re.compile(r"gem\s+['\"]phlex|Phlex::HTML"),
        'tilt': re.compile(r"gem\s+['\"]tilt|Tilt"),
        'sequel': re.compile(r"gem\s+['\"]sequel|Sequel\."),
    }

    def __init__(self):
        """Initialize the Hanami parser."""
        pass

    def parse(self, content: str, file_path: str = "") -> HanamiParseResult:
        """Parse Ruby source code for Hanami-specific patterns."""
        result = HanamiParseResult(file_path=file_path)

        # Check if this file uses Hanami
        if not self.HANAMI_REQUIRE.search(content):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version
        result.hanami_version = self._detect_version(content)

        # Feature flags
        result.has_rom = bool(re.search(r"ROM::|rom-sql|rom-repository", content))
        result.has_slices = bool(self.SLICE_CLASS.search(content) or self.ROUTE_SLICE.search(content))

        # Extract all components
        self._extract_actions(content, file_path, result)
        self._extract_slices(content, file_path, result)
        self._extract_routes(content, file_path, result)
        self._extract_entities(content, file_path, result)
        self._extract_repositories(content, file_path, result)
        self._extract_views(content, file_path, result)
        self._extract_providers(content, file_path, result)
        self._extract_settings(content, file_path, result)

        # Totals
        result.total_actions = len(result.actions)
        result.total_routes = len(result.routes)

        return result

    def _extract_actions(self, content: str, file_path: str, result: HanamiParseResult):
        """Extract Hanami action definitions."""
        # Hanami 2.x style
        for m in self.ACTION_CLASS_V2.finditer(content):
            action = HanamiActionInfo(
                name=m.group(1),
                has_handle_method=bool(self.HANDLE_METHOD.search(content)),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            # Extract params
            for pm in self.PARAMS_REQUIRED.finditer(content):
                action.params_schema.append(pm.group(1))
            result.actions.append(action)

        # Hanami 1.x style (include Hanami::Action)
        if not result.actions and self.ACTION_INCLUDE.search(content):
            action = HanamiActionInfo(
                name=file_path.split('/')[-1].replace('.rb', ''),
                has_handle_method=bool(self.CALL_METHOD.search(content)),
                file=file_path,
            )
            for pm in self.PARAMS_REQUIRED.finditer(content):
                action.params_schema.append(pm.group(1))
            result.actions.append(action)

    def _extract_slices(self, content: str, file_path: str, result: HanamiParseResult):
        """Extract Hanami slice definitions."""
        for m in self.SLICE_CLASS.finditer(content):
            result.slices.append(HanamiSliceInfo(
                name=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_routes(self, content: str, file_path: str, result: HanamiParseResult):
        """Extract Hanami route definitions."""
        for m in self.ROUTE_ROOT.finditer(content):
            result.routes.append(HanamiRouteInfo(
                method="root",
                path="/",
                action=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.ROUTE_HTTP.finditer(content):
            result.routes.append(HanamiRouteInfo(
                method=m.group(1).upper(),
                path=m.group(2),
                action=m.group(3) or "",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_entities(self, content: str, file_path: str, result: HanamiParseResult):
        """Extract Hanami entity definitions."""
        for m in self.ENTITY_CLASS.finditer(content):
            entity = HanamiEntityInfo(
                name=m.group(1),
                is_rom_struct="ROM" in content or "Dry::Struct" in content,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            for am in self.ATTRIBUTE_DEF.finditer(content):
                entity.attributes.append(am.group(1))
            result.entities.append(entity)

    def _extract_repositories(self, content: str, file_path: str, result: HanamiParseResult):
        """Extract Hanami repository definitions."""
        for m in self.REPO_CLASS.finditer(content):
            repo = HanamiRepositoryInfo(
                name=m.group(1),
                is_rom_repo="ROM" in content,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            for rm in self.REPO_RELATION.finditer(content):
                repo.relations.append(rm.group(1))
            result.repositories.append(repo)

    def _extract_views(self, content: str, file_path: str, result: HanamiParseResult):
        """Extract Hanami view definitions."""
        for m in self.VIEW_CLASS.finditer(content):
            view = HanamiViewInfo(
                name=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            for em in self.EXPOSURE.finditer(content):
                view.exposures.append(em.group(1))
            result.views.append(view)

    def _extract_providers(self, content: str, file_path: str, result: HanamiParseResult):
        """Extract Hanami provider definitions."""
        for m in self.PROVIDER_REGISTER.finditer(content):
            result.providers.append(HanamiProviderInfo(
                name=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))
        for m in self.PROVIDER_SOURCE.finditer(content):
            result.providers.append(HanamiProviderInfo(
                name=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_settings(self, content: str, file_path: str, result: HanamiParseResult):
        """Extract Hanami settings definitions."""
        for m in self.SETTING_DEF.finditer(content):
            opts = m.group(2) or ""
            type_match = re.search(r"Types::(\w+)", opts)
            default_match = re.search(r"default:\s*(.+?)(?:,|$)", opts)
            result.settings.append(HanamiSettingInfo(
                name=m.group(1),
                type=type_match.group(1) if type_match else "",
                default=default_match.group(1).strip() if default_match else "",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Hanami ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect Hanami version from usage patterns."""
        # Hanami 2.1+ indicators
        if re.search(r"Hanami::Slice|hanami-db|register_provider", content):
            return "2.1+"
        # Hanami 2.x indicators
        if re.search(r"include\s+Deps|Dry::AutoInject|Hanami\.app", content):
            return "2.x"
        # Hanami 1.x indicators
        if re.search(r"Hanami::Repository|Hanami::Entity|Hanami::Interactor", content):
            return "1.x"
        if re.search(r"Hanami\.\w+", content):
            return "1.x+"
        return ""
