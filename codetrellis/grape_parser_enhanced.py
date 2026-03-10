"""
EnhancedGrapeParser v1.0 - Comprehensive Grape API framework parser.

Runs as a supplementary layer on top of the Ruby parser, extracting
Grape-specific semantics.

Supports:
- Grape 0.x (original API DSL)
- Grape 1.x (entity exposure, validators, error handling)
- Grape 2.x (enhanced params, Swagger/OpenAPI integration)

Grape-specific extraction:
- Endpoints: RESTful route definitions (get, post, etc.)
- Resources: resource/namespace/group blocks
- Params: DSL param declarations (requires, optional, coercion)
- Entities: Grape::Entity representers with field exposure
- Helpers: Shared helper modules, authentication helpers
- Validators: Custom param validators
- Error handling: rescue_from, error responses
- Versioning: path, header, param, accept_version_header
- Middleware: Grape::Middleware, insert_before/after
- Mounting: mount points for modular APIs

Framework detection (15+ Grape ecosystem patterns):
- Core: grape, grape-entity, grape-swagger
- Serialization: grape-entity, grape-roar, grape-jsonapi
- Auth: grape-doorkeeper, grape-token_auth
- Docs: grape-swagger, grape-swagger-entity
- Validation: grape-validators, grape-extra_validators
- Caching: grape-cache_control
- Versioning: grape-versioning

Part of CodeTrellis v5.2.0 - Ruby Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class GrapeEndpointInfo:
    """Information about a Grape API endpoint."""
    method: str
    path: str
    desc: str = ""
    resource: str = ""
    version: str = ""
    params: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class GrapeResourceInfo:
    """Information about a Grape resource/namespace."""
    name: str
    endpoints: List[str] = field(default_factory=list)
    nested: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class GrapeParamInfo:
    """Information about Grape parameter declarations."""
    name: str
    type: str = ""
    required: bool = False
    desc: str = ""
    endpoint: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GrapeEntityInfo:
    """Information about a Grape::Entity."""
    name: str
    root: str = ""
    exposures: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class GrapeHelperInfo:
    """Information about Grape helpers."""
    name: str
    methods: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class GrapeValidatorInfo:
    """Information about a custom Grape validator."""
    name: str
    param_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GrapeErrorHandlerInfo:
    """Information about Grape error handling."""
    exception: str
    handler: str = ""
    status: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GrapeMountInfo:
    """Information about Grape API mount points."""
    mounted_class: str
    path: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GrapeMiddlewareInfo:
    """Information about Grape middleware."""
    name: str
    position: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GrapeParseResult:
    """Complete parse result for a Grape file."""
    file_path: str
    file_type: str = "ruby"

    # Endpoints
    endpoints: List[GrapeEndpointInfo] = field(default_factory=list)

    # Resources
    resources: List[GrapeResourceInfo] = field(default_factory=list)

    # Params
    params: List[GrapeParamInfo] = field(default_factory=list)

    # Entities
    entities: List[GrapeEntityInfo] = field(default_factory=list)

    # Helpers
    helpers: List[GrapeHelperInfo] = field(default_factory=list)

    # Validators
    validators: List[GrapeValidatorInfo] = field(default_factory=list)

    # Error handlers
    error_handlers: List[GrapeErrorHandlerInfo] = field(default_factory=list)

    # Mounts
    mounts: List[GrapeMountInfo] = field(default_factory=list)

    # Middleware
    middleware: List[GrapeMiddlewareInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    grape_version: str = ""
    versioning_strategy: str = ""
    total_endpoints: int = 0
    total_resources: int = 0


class EnhancedGrapeParser:
    """
    Enhanced Grape parser for REST API framework extraction.

    Runs AFTER the Ruby parser when Grape framework is detected.
    """

    # Grape detection
    GRAPE_REQUIRE = re.compile(
        r"require\s+['\"]grape['\"]|"
        r"Grape::API|"
        r"class\s+\w+\s*<\s*Grape::|"
        r"include\s+Grape::"
    )

    # Endpoint patterns
    ENDPOINT_DEF = re.compile(
        r"^\s*(get|post|put|patch|delete|head|options)\s+"
        r"(?:['\"]([^'\"]*)['\"]|:(\w+))",
        re.MULTILINE,
    )
    # Endpoints without explicit path (e.g. `get do` inside resource block)
    ENDPOINT_BARE = re.compile(
        r"^\s*(get|post|put|patch|delete|head|options)\s+do\b",
        re.MULTILINE,
    )
    DESC_DEF = re.compile(
        r"^\s*desc\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Resource/namespace patterns
    RESOURCE_DEF = re.compile(
        r"^\s*(?:resource|resources)\s+:(\w+)",
        re.MULTILINE,
    )
    NAMESPACE_DEF = re.compile(
        r"^\s*(?:namespace|group|segment)\s+['\"]?:?(\w+)['\"]?",
        re.MULTILINE,
    )
    ROUTE_PARAM = re.compile(
        r"^\s*route_param\s+:(\w+)",
        re.MULTILINE,
    )

    # Parameter patterns
    PARAM_REQUIRES = re.compile(
        r"^\s*requires\s+:(\w+)"
        r"(?:\s*,\s*type:\s*(\w+))?",
        re.MULTILINE,
    )
    PARAM_OPTIONAL = re.compile(
        r"^\s*optional\s+:(\w+)"
        r"(?:\s*,\s*type:\s*(\w+))?",
        re.MULTILINE,
    )
    PARAMS_BLOCK = re.compile(
        r"^\s*params\s+do\b",
        re.MULTILINE,
    )

    # Entity patterns
    ENTITY_CLASS = re.compile(
        r"class\s+(\w+)\s*<\s*Grape::Entity",
    )
    ENTITY_EXPOSE = re.compile(
        r"^\s*expose\s+:(\w+)",
        re.MULTILINE,
    )
    ENTITY_ROOT = re.compile(
        r"^\s*root\s+['\"](\w+)['\"]",
        re.MULTILINE,
    )

    # Helper patterns
    HELPERS_BLOCK = re.compile(
        r"^\s*helpers\s+(?:do|(\w+))",
        re.MULTILINE,
    )
    HELPERS_MODULE = re.compile(
        r"^\s*helpers\s+(\w+(?:::\w+)*)",
        re.MULTILINE,
    )

    # Validator patterns
    VALIDATOR_CLASS = re.compile(
        r"class\s+(\w+)\s*<\s*Grape::Validations::(?:Base|Validators::Base)",
    )

    # Error handling
    RESCUE_FROM = re.compile(
        r"^\s*rescue_from\s+([A-Z][\w:]+)",
        re.MULTILINE,
    )

    # Mount patterns
    MOUNT_DEF = re.compile(
        r"^\s*mount\s+([A-Z][\w:]+)",
        re.MULTILINE,
    )

    # Versioning patterns
    VERSION_DEF = re.compile(
        r"^\s*version\s+['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*using:\s*:(\w+))?",
        re.MULTILINE,
    )

    # Middleware patterns
    MIDDLEWARE_USE = re.compile(
        r"^\s*(?:use|insert_before|insert_after)\s+([A-Z][\w:]+)",
        re.MULTILINE,
    )

    # Present / format
    PRESENT_CALL = re.compile(
        r"^\s*present\s+.+,\s*with:\s*([A-Z][\w:]+)",
        re.MULTILINE,
    )
    FORMAT_DEF = re.compile(
        r"^\s*(?:format|default_format|content_type)\s+:(\w+)",
        re.MULTILINE,
    )

    # Framework detection
    FRAMEWORK_PATTERNS = {
        'grape': re.compile(r"require\s+['\"]grape|Grape::API"),
        'grape-entity': re.compile(r"grape-entity|Grape::Entity"),
        'grape-swagger': re.compile(r"grape-swagger|GrapeSwagger"),
        'grape-swagger-entity': re.compile(r"grape-swagger-entity"),
        'grape-roar': re.compile(r"grape-roar|Roar::"),
        'grape-jsonapi': re.compile(r"grape-jsonapi|JSONAPI::"),
        'grape-doorkeeper': re.compile(r"grape-doorkeeper|Doorkeeper"),
        'grape-cache_control': re.compile(r"grape-cache_control|cache_control"),
        'grape-kaminari': re.compile(r"grape-kaminari|Kaminari"),
        'grape-extra_validators': re.compile(r"grape-extra_validators"),
        'grape-batch': re.compile(r"grape-batch"),
        'grape-cancan': re.compile(r"grape-cancan|authorize!"),
        'rack-cors': re.compile(r"rack-cors|Rack::Cors"),
        'hashie-mash': re.compile(r"Hashie::Mash|hashie"),
    }

    def __init__(self):
        """Initialize the Grape parser."""
        pass

    def parse(self, content: str, file_path: str = "") -> GrapeParseResult:
        """Parse Ruby source code for Grape-specific patterns."""
        result = GrapeParseResult(file_path=file_path)

        # Check if this file uses Grape
        if not self.GRAPE_REQUIRE.search(content):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version
        result.grape_version = self._detect_version(content)

        # Detect versioning strategy
        v_match = self.VERSION_DEF.search(content)
        if v_match:
            result.versioning_strategy = v_match.group(2) or "path"

        # Extract all components
        self._extract_endpoints(content, file_path, result)
        self._extract_resources(content, file_path, result)
        self._extract_params(content, file_path, result)
        self._extract_entities(content, file_path, result)
        self._extract_helpers(content, file_path, result)
        self._extract_validators(content, file_path, result)
        self._extract_error_handlers(content, file_path, result)
        self._extract_mounts(content, file_path, result)
        self._extract_middleware(content, file_path, result)

        # Totals
        result.total_endpoints = len(result.endpoints)
        result.total_resources = len(result.resources)

        return result

    def _extract_endpoints(self, content: str, file_path: str, result: GrapeParseResult):
        """Extract Grape API endpoint definitions."""
        matched_positions = set()
        for m in self.ENDPOINT_DEF.finditer(content):
            path = m.group(2) or m.group(3) or ""
            result.endpoints.append(GrapeEndpointInfo(
                method=m.group(1).upper(),
                path=path,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))
            matched_positions.add(m.start())
        # Bare endpoints (e.g. `get do` inside resource blocks)
        for m in self.ENDPOINT_BARE.finditer(content):
            if m.start() not in matched_positions:
                result.endpoints.append(GrapeEndpointInfo(
                    method=m.group(1).upper(),
                    path="",
                    file=file_path,
                    line_number=content[:m.start()].count('\n') + 1,
                ))

    def _extract_resources(self, content: str, file_path: str, result: GrapeParseResult):
        """Extract Grape resource/namespace definitions."""
        for m in self.RESOURCE_DEF.finditer(content):
            result.resources.append(GrapeResourceInfo(
                name=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))
        for m in self.NAMESPACE_DEF.finditer(content):
            result.resources.append(GrapeResourceInfo(
                name=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_params(self, content: str, file_path: str, result: GrapeParseResult):
        """Extract Grape parameter declarations."""
        for m in self.PARAM_REQUIRES.finditer(content):
            result.params.append(GrapeParamInfo(
                name=m.group(1),
                type=m.group(2) or "",
                required=True,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))
        for m in self.PARAM_OPTIONAL.finditer(content):
            result.params.append(GrapeParamInfo(
                name=m.group(1),
                type=m.group(2) or "",
                required=False,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_entities(self, content: str, file_path: str, result: GrapeParseResult):
        """Extract Grape::Entity definitions."""
        for m in self.ENTITY_CLASS.finditer(content):
            entity = GrapeEntityInfo(
                name=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            for em in self.ENTITY_EXPOSE.finditer(content):
                entity.exposures.append(em.group(1))
            root = self.ENTITY_ROOT.search(content)
            if root:
                entity.root = root.group(1)
            result.entities.append(entity)

    def _extract_helpers(self, content: str, file_path: str, result: GrapeParseResult):
        """Extract Grape helper definitions."""
        for m in self.HELPERS_MODULE.finditer(content):
            if m.group(1) and m.group(1) != "do":
                result.helpers.append(GrapeHelperInfo(
                    name=m.group(1),
                    file=file_path,
                    line_number=content[:m.start()].count('\n') + 1,
                ))

    def _extract_validators(self, content: str, file_path: str, result: GrapeParseResult):
        """Extract custom Grape validators."""
        for m in self.VALIDATOR_CLASS.finditer(content):
            result.validators.append(GrapeValidatorInfo(
                name=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_error_handlers(self, content: str, file_path: str, result: GrapeParseResult):
        """Extract Grape error handlers."""
        for m in self.RESCUE_FROM.finditer(content):
            result.error_handlers.append(GrapeErrorHandlerInfo(
                exception=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_mounts(self, content: str, file_path: str, result: GrapeParseResult):
        """Extract Grape mount points."""
        for m in self.MOUNT_DEF.finditer(content):
            result.mounts.append(GrapeMountInfo(
                mounted_class=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_middleware(self, content: str, file_path: str, result: GrapeParseResult):
        """Extract Grape middleware."""
        for m in self.MIDDLEWARE_USE.finditer(content):
            result.middleware.append(GrapeMiddlewareInfo(
                name=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Grape ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect Grape version from usage patterns."""
        # Grape 2.x indicators
        if re.search(r"Grape::API::Instance|grape.*2\.", content):
            return "2.x"
        # Grape 1.x indicators
        if re.search(r"Grape::API|grape-entity|grape-swagger", content):
            return "1.x+"
        # Grape 0.x indicators
        if re.search(r"Grape::Endpoint|grape.*0\.", content):
            return "0.x"
        return ""
