"""
EnhancedPydanticParser - Deep extraction for Pydantic framework projects.

This is a framework-level enhanced parser that goes beyond the basic
PydanticExtractor (which extracts BaseModel definitions). This parser
extracts the full Pydantic ecosystem:

- Models (BaseModel subclasses, RootModel, GenericModel)
- Settings (BaseSettings, env vars, secrets)
- Validators (field_validator, model_validator, @validate_call)
- Serializers (model_serializer, field_serializer, PlainSerializer)
- TypeAdapter usage
- Custom types (Annotated types, BeforeValidator, AfterValidator, PlainValidator)
- Discriminated unions (Discriminator, Tag, Union[...])
- JSON Schema customization (model_json_schema, json_schema_extra)
- Config patterns (model_config = ConfigDict(...), Config class)
- Pydantic plugins (PydanticPlugin)
- Dataclass integration (@pydantic.dataclass)
- Computed fields (@computed_field)
- Field metadata (Field(), FieldInfo)

Supports:
- Pydantic v1.x (BaseModel, Config class, @validator, @root_validator)
- Pydantic v2.x (ConfigDict, @field_validator, @model_validator, TypeAdapter, RootModel)

Part of CodeTrellis v4.93 - Python Framework Support.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any


# ═══════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PydanticEnhancedModelInfo:
    """Information about a Pydantic model (framework-level)."""
    name: str
    model_type: str = "BaseModel"  # BaseModel, RootModel, GenericModel, BaseSettings
    bases: List[str] = field(default_factory=list)
    field_count: int = 0
    validator_count: int = 0
    has_config: bool = False
    has_computed_fields: bool = False
    has_custom_init: bool = False
    is_generic: bool = False
    is_abstract: bool = False
    line_number: int = 0


@dataclass
class PydanticSettingsInfo:
    """Information about a Pydantic BaseSettings class."""
    name: str
    env_prefix: Optional[str] = None
    env_file: Optional[str] = None
    env_nested_delimiter: Optional[str] = None
    secrets_dir: Optional[str] = None
    case_sensitive: bool = False
    field_count: int = 0
    line_number: int = 0


@dataclass
class PydanticValidatorDetailInfo:
    """Detailed information about a Pydantic validator."""
    name: str
    validator_type: str = "field_validator"  # field_validator, model_validator, validator, root_validator, validate_call
    fields: List[str] = field(default_factory=list)
    mode: str = "after"  # before, after, wrap, plain
    is_classmethod: bool = True
    line_number: int = 0


@dataclass
class PydanticSerializerInfo:
    """Information about a Pydantic serializer."""
    name: str
    serializer_type: str = "field_serializer"  # field_serializer, model_serializer, PlainSerializer
    fields: List[str] = field(default_factory=list)
    mode: str = "plain"  # plain, wrap
    return_type: Optional[str] = None
    line_number: int = 0


@dataclass
class PydanticTypeAdapterInfo:
    """Information about a TypeAdapter instance."""
    variable_name: str
    adapted_type: str
    line_number: int = 0


@dataclass
class PydanticCustomTypeInfo:
    """Information about a custom Pydantic type (Annotated validators)."""
    name: str
    type_kind: str = "Annotated"  # Annotated, BeforeValidator, AfterValidator, PlainValidator, WrapValidator
    base_type: Optional[str] = None
    line_number: int = 0


@dataclass
class PydanticDiscriminatedUnionInfo:
    """Information about a discriminated union."""
    name: str
    discriminator: Optional[str] = None
    variants: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class PydanticDataclassInfo:
    """Information about a @pydantic.dataclass."""
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    field_count: int = 0
    line_number: int = 0


@dataclass
class PydanticPluginInfo:
    """Information about a Pydantic plugin."""
    name: str
    plugin_type: str = "PydanticPlugin"
    line_number: int = 0


@dataclass
class PydanticEnhancedParseResult:
    """Result of parsing Pydantic source code at framework level."""
    file_path: str = ""
    file_type: str = "module"

    models: List[PydanticEnhancedModelInfo] = field(default_factory=list)
    settings: List[PydanticSettingsInfo] = field(default_factory=list)
    validators: List[PydanticValidatorDetailInfo] = field(default_factory=list)
    serializers: List[PydanticSerializerInfo] = field(default_factory=list)
    type_adapters: List[PydanticTypeAdapterInfo] = field(default_factory=list)
    custom_types: List[PydanticCustomTypeInfo] = field(default_factory=list)
    discriminated_unions: List[PydanticDiscriminatedUnionInfo] = field(default_factory=list)
    pydantic_dataclasses: List[PydanticDataclassInfo] = field(default_factory=list)
    plugins: List[PydanticPluginInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    pydantic_version: str = ""

    # Aggregates
    total_models: int = 0
    total_settings: int = 0
    total_validators: int = 0
    total_serializers: int = 0


# ═══════════════════════════════════════════════════════════════════
# Parser
# ═══════════════════════════════════════════════════════════════════

class EnhancedPydanticParser:
    """
    Comprehensive Pydantic framework parser.

    Extracts models, settings, validators, serializers, TypeAdapters,
    custom types, discriminated unions, dataclasses, and plugins from
    Pydantic v1.x and v2.x source code.

    This is a framework-level parser that complements the existing
    PydanticExtractor (which provides field-level extraction for the
    python_pydantic_models matrix field). This parser provides broader
    ecosystem-level information.
    """

    # ── Framework detection patterns ──────────────────────────────
    FRAMEWORK_PATTERNS = {
        'pydantic-core': re.compile(r'from\s+pydantic\s+import|import\s+pydantic\b', re.MULTILINE),
        'pydantic-settings': re.compile(r'from\s+pydantic_settings\s+import|from\s+pydantic\s+import\s+.*BaseSettings', re.MULTILINE),
        'pydantic-v2': re.compile(r'ConfigDict|@field_validator|@model_validator|TypeAdapter|RootModel|@computed_field|@field_serializer|@model_serializer', re.MULTILINE),
        'pydantic-v1': re.compile(r'class\s+Config\s*:|@validator\s*\(|@root_validator', re.MULTILINE),
        'pydantic-dataclass': re.compile(r'@pydantic\.dataclass|from\s+pydantic\.dataclasses\s+import', re.MULTILINE),
        'pydantic-types': re.compile(r'from\s+pydantic\s+import\s+.*(?:conint|constr|confloat|conlist|conbytes|PositiveInt|NegativeInt|StrictStr|StrictInt|StrictFloat|StrictBool|EmailStr|AnyUrl|HttpUrl|AnyHttpUrl|IPvAnyAddress)', re.MULTILINE),
        'pydantic-annotated': re.compile(r'BeforeValidator|AfterValidator|PlainValidator|WrapValidator|PlainSerializer|WrapSerializer', re.MULTILINE),
        'pydantic-json-schema': re.compile(r'model_json_schema|json_schema_extra|WithJsonSchema|JsonSchemaValue', re.MULTILINE),
        'pydantic-generics': re.compile(r'GenericModel|Generic\s*\[.*\].*BaseModel', re.MULTILINE),
        'pydantic-plugin': re.compile(r'PydanticPlugin|from\s+pydantic\.plugin\s+import', re.MULTILINE),
        'pydantic-functional': re.compile(r'@validate_call|validate_call\s*\(', re.MULTILINE),
        'pydantic-discriminator': re.compile(r'Discriminator|discriminator\s*=', re.MULTILINE),
    }

    # ── Model patterns ────────────────────────────────────────────

    # class MyModel(BaseModel): or class MyModel(BaseModel, SomeMixin):
    BASE_MODEL_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(([^)]*(?:BaseModel|GenericModel)[^)]*)\)\s*:',
        re.MULTILINE,
    )

    # class MyModel(RootModel[int]): or RootModel[list[str]]
    ROOT_MODEL_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*RootModel\s*(?:\[\s*(.+?)\s*\]\s*)?\)\s*:',
        re.MULTILINE,
    )

    # ── Settings patterns ─────────────────────────────────────────

    # class MySettings(BaseSettings):
    SETTINGS_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(([^)]*BaseSettings[^)]*)\)\s*:',
        re.MULTILINE,
    )

    # env_prefix = "MY_APP_"
    ENV_PREFIX_PATTERN = re.compile(
        r'env_prefix\s*=\s*["\']([^"\']+)["\']',
    )

    # env_file = ".env"
    ENV_FILE_PATTERN = re.compile(
        r'env_file\s*=\s*["\']([^"\']+)["\']',
    )

    # env_nested_delimiter = "__"
    ENV_NESTED_DELIMITER_PATTERN = re.compile(
        r'env_nested_delimiter\s*=\s*["\']([^"\']+)["\']',
    )

    # secrets_dir = "/run/secrets"
    SECRETS_DIR_PATTERN = re.compile(
        r'secrets_dir\s*=\s*["\']([^"\']+)["\']',
    )

    # case_sensitive = True
    CASE_SENSITIVE_PATTERN = re.compile(
        r'case_sensitive\s*=\s*(True|False)',
    )

    # ── Validator patterns ────────────────────────────────────────

    # @field_validator("field1", "field2", mode="before")
    FIELD_VALIDATOR_PATTERN = re.compile(
        r'@field_validator\s*\(\s*([^)]+)\s*\)\s*\n'
        r'\s*(?:@classmethod\s+)?'
        r'def\s+(\w+)',
        re.MULTILINE,
    )

    # @model_validator(mode="before")
    MODEL_VALIDATOR_PATTERN = re.compile(
        r'@model_validator\s*\(\s*mode\s*=\s*["\'](\w+)["\']\s*\)\s*\n'
        r'\s*(?:@classmethod\s+)?'
        r'def\s+(\w+)',
        re.MULTILINE,
    )

    # @validator("field1", "field2", pre=True)  (v1 syntax)
    V1_VALIDATOR_PATTERN = re.compile(
        r'@validator\s*\(\s*([^)]+)\s*\)\s*\n'
        r'\s*(?:@classmethod\s+)?'
        r'def\s+(\w+)',
        re.MULTILINE,
    )

    # @root_validator  or @root_validator(pre=True)  (v1 syntax)
    V1_ROOT_VALIDATOR_PATTERN = re.compile(
        r'@root_validator\s*(?:\(\s*(?:pre\s*=\s*(True|False))?\s*\))?\s*\n'
        r'\s*(?:@classmethod\s+)?'
        r'def\s+(\w+)',
        re.MULTILINE,
    )

    # @validate_call
    VALIDATE_CALL_PATTERN = re.compile(
        r'@validate_call\s*(?:\([^)]*\))?\s*\n'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # ── Serializer patterns ───────────────────────────────────────

    # @field_serializer("field1", "field2", mode="plain")
    FIELD_SERIALIZER_PATTERN = re.compile(
        r'@field_serializer\s*\(\s*([^)]+)\s*\)\s*\n'
        r'\s*(?:@classmethod\s+)?'
        r'def\s+(\w+)',
        re.MULTILINE,
    )

    # @model_serializer(mode="wrap")
    MODEL_SERIALIZER_PATTERN = re.compile(
        r'@model_serializer\s*(?:\(\s*mode\s*=\s*["\'](\w+)["\']\s*\))?\s*\n'
        r'\s*def\s+(\w+)',
        re.MULTILINE,
    )

    # ── TypeAdapter patterns ──────────────────────────────────────

    # my_adapter = TypeAdapter(List[int])
    TYPE_ADAPTER_PATTERN = re.compile(
        r'(\w+)\s*=\s*TypeAdapter\s*\(\s*([^)]+)\s*\)',
        re.MULTILINE,
    )

    # ── Custom type patterns ──────────────────────────────────────

    # MyType = Annotated[str, BeforeValidator(func)]
    ANNOTATED_TYPE_PATTERN = re.compile(
        r'(\w+)\s*=\s*Annotated\s*\[\s*(\w[\w\[\], ]*?)\s*,\s*'
        r'(BeforeValidator|AfterValidator|PlainValidator|WrapValidator|PlainSerializer|WrapSerializer)',
        re.MULTILINE,
    )

    # ── Discriminated union patterns ──────────────────────────────

    # MyUnion = Annotated[Union[Cat, Dog], Discriminator("pet_type")]
    DISCRIMINATED_UNION_PATTERN = re.compile(
        r'(\w+)\s*=\s*Annotated\s*\[\s*Union\s*\[([^\]]+)\]\s*,\s*Discriminator\s*\(\s*["\'](\w+)["\']\s*\)',
        re.MULTILINE,
    )

    # field: Union[Cat, Dog] = Field(discriminator="pet_type")
    FIELD_DISCRIMINATOR_PATTERN = re.compile(
        r'(\w+)\s*:\s*(?:Union\s*\[([^\]]+)\]|Annotated\[.*?\])\s*=\s*Field\s*\([^)]*discriminator\s*=\s*["\'](\w+)["\']',
        re.MULTILINE,
    )

    # ── Pydantic dataclass patterns ───────────────────────────────

    # @pydantic.dataclass or @dataclass (from pydantic.dataclasses)
    PYDANTIC_DATACLASS_PATTERN = re.compile(
        r'@(?:pydantic\.)?dataclass\s*(?:\([^)]*\))?\s*\n'
        r'class\s+(\w+)',
        re.MULTILINE,
    )

    # ── Config patterns ───────────────────────────────────────────

    # model_config = ConfigDict(...)
    CONFIG_DICT_PATTERN = re.compile(
        r'model_config\s*=\s*ConfigDict\s*\(\s*([^)]+)\s*\)',
        re.MULTILINE,
    )

    # class Config: (v1 pattern)
    CONFIG_CLASS_PATTERN = re.compile(
        r'class\s+Config\s*:',
        re.MULTILINE,
    )

    # ── Computed field patterns ───────────────────────────────────

    # @computed_field
    COMPUTED_FIELD_PATTERN = re.compile(
        r'@computed_field(?:\s*\([^)]*\))?\s*\n'
        r'\s*@property\s*\n'
        r'\s*def\s+(\w+)',
        re.MULTILINE,
    )

    # ── Plugin patterns ───────────────────────────────────────────

    # class MyPlugin(PydanticPlugin):
    PLUGIN_CLASS_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*PydanticPlugin\s*\)\s*:',
        re.MULTILINE,
    )

    # ── Field counting pattern ────────────────────────────────────
    FIELD_LINE_PATTERN = re.compile(
        r'^\s{4}(\w+)\s*:\s*\S',
        re.MULTILINE,
    )

    # ── Version feature detection ─────────────────────────────────
    PYDANTIC_VERSION_FEATURES = {
        # v1.x features
        'BaseModel': '1.0',
        'BaseSettings': '1.0',
        '@validator(': '1.0',
        '@root_validator': '1.0',
        'class Config:': '1.0',
        'Field(': '1.0',
        'GenericModel': '1.0',
        'conint': '1.0',
        'constr': '1.0',
        'confloat': '1.0',
        # v1.x late features
        'orm_mode': '1.0',
        'schema_extra': '1.0',
        # v2.0 features
        'ConfigDict': '2.0',
        '@field_validator': '2.0',
        '@model_validator': '2.0',
        'TypeAdapter': '2.0',
        'RootModel': '2.0',
        '@computed_field': '2.0',
        '@field_serializer': '2.0',
        '@model_serializer': '2.0',
        'model_config': '2.0',
        'model_json_schema': '2.0',
        '@validate_call': '2.0',
        'BeforeValidator': '2.0',
        'AfterValidator': '2.0',
        'PlainValidator': '2.0',
        'WrapValidator': '2.0',
        'PlainSerializer': '2.0',
        'WrapSerializer': '2.0',
        'Discriminator': '2.0',
        'WithJsonSchema': '2.0',
        'model_dump': '2.0',
        'model_validate': '2.0',
        'model_validate_json': '2.0',
        'model_dump_json': '2.0',
        'model_fields': '2.0',
        'model_computed_fields': '2.0',
        'model_rebuild': '2.0',
        # v2.x late features
        'PydanticPlugin': '2.4',
        'from pydantic_settings': '2.0',
        'SettingsConfigDict': '2.0',
    }

    def __init__(self):
        """Initialize the enhanced Pydantic parser."""
        pass

    def parse(self, content: str, file_path: str = "") -> PydanticEnhancedParseResult:
        """
        Parse Pydantic source code and extract all Pydantic-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            PydanticEnhancedParseResult with all extracted information
        """
        result = PydanticEnhancedParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Models ───────────────────────────────────────────────
        self._extract_models(content, result)
        self._extract_root_models(content, result)

        # ── Settings ─────────────────────────────────────────────
        self._extract_settings(content, result)

        # ── Validators ───────────────────────────────────────────
        self._extract_validators(content, result)

        # ── Serializers ──────────────────────────────────────────
        self._extract_serializers(content, result)

        # ── TypeAdapters ─────────────────────────────────────────
        self._extract_type_adapters(content, result)

        # ── Custom types ─────────────────────────────────────────
        self._extract_custom_types(content, result)

        # ── Discriminated unions ─────────────────────────────────
        self._extract_discriminated_unions(content, result)

        # ── Pydantic dataclasses ─────────────────────────────────
        self._extract_pydantic_dataclasses(content, result)

        # ── Plugins ──────────────────────────────────────────────
        self._extract_plugins(content, result)

        # Aggregates
        result.total_models = len(result.models)
        result.total_settings = len(result.settings)
        result.total_validators = len(result.validators)
        result.total_serializers = len(result.serializers)
        result.pydantic_version = self._detect_pydantic_version(content)

        return result

    # ─── Extraction methods ───────────────────────────────────────

    def _extract_models(self, content: str, result: PydanticEnhancedParseResult):
        """Extract BaseModel and GenericModel subclasses."""
        for match in self.BASE_MODEL_PATTERN.finditer(content):
            name = match.group(1)
            bases_str = match.group(2)
            bases = [b.strip() for b in bases_str.split(',') if b.strip()]

            # Determine model type
            model_type = "BaseModel"
            is_generic = False
            if any('GenericModel' in b for b in bases):
                model_type = "GenericModel"
                is_generic = True
            if any('Generic[' in b or 'Generic [' in b for b in bases):
                is_generic = True

            # Get class body for counting
            class_start = match.end()
            class_body = self._extract_class_body(content, class_start)

            # Count fields and check features
            field_count = len(self.FIELD_LINE_PATTERN.findall(class_body)) if class_body else 0
            validator_count = len(self.FIELD_VALIDATOR_PATTERN.findall(class_body or "")) + \
                              len(self.V1_VALIDATOR_PATTERN.findall(class_body or ""))
            has_config = bool(self.CONFIG_DICT_PATTERN.search(class_body or "")) or \
                         bool(self.CONFIG_CLASS_PATTERN.search(class_body or ""))
            has_computed = bool(self.COMPUTED_FIELD_PATTERN.search(class_body or ""))
            has_init = bool(re.search(r'def\s+__init__\s*\(', class_body or ""))

            # Check if abstract (no fields, or ABC mixin)
            is_abstract = any('ABC' in b for b in bases) or (field_count == 0 and not has_init)

            result.models.append(PydanticEnhancedModelInfo(
                name=name,
                model_type=model_type,
                bases=bases,
                field_count=field_count,
                validator_count=validator_count,
                has_config=has_config,
                has_computed_fields=has_computed,
                has_custom_init=has_init,
                is_generic=is_generic,
                is_abstract=is_abstract,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_root_models(self, content: str, result: PydanticEnhancedParseResult):
        """Extract RootModel subclasses."""
        for match in self.ROOT_MODEL_PATTERN.finditer(content):
            name = match.group(1)
            root_type = match.group(2) or "Any"

            result.models.append(PydanticEnhancedModelInfo(
                name=name,
                model_type="RootModel",
                bases=[f"RootModel[{root_type}]"],
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_settings(self, content: str, result: PydanticEnhancedParseResult):
        """Extract BaseSettings subclasses."""
        for match in self.SETTINGS_PATTERN.finditer(content):
            name = match.group(1)

            # Get class body
            class_start = match.end()
            class_body = self._extract_class_body(content, class_start) or ""

            # Extract settings-specific config
            env_prefix = None
            env_file = None
            env_nested_delimiter = None
            secrets_dir = None
            case_sensitive = False

            prefix_match = self.ENV_PREFIX_PATTERN.search(class_body)
            if prefix_match:
                env_prefix = prefix_match.group(1)

            file_match = self.ENV_FILE_PATTERN.search(class_body)
            if file_match:
                env_file = file_match.group(1)

            delim_match = self.ENV_NESTED_DELIMITER_PATTERN.search(class_body)
            if delim_match:
                env_nested_delimiter = delim_match.group(1)

            secrets_match = self.SECRETS_DIR_PATTERN.search(class_body)
            if secrets_match:
                secrets_dir = secrets_match.group(1)

            case_match = self.CASE_SENSITIVE_PATTERN.search(class_body)
            if case_match:
                case_sensitive = case_match.group(1) == 'True'

            field_count = len(self.FIELD_LINE_PATTERN.findall(class_body))

            result.settings.append(PydanticSettingsInfo(
                name=name,
                env_prefix=env_prefix,
                env_file=env_file,
                env_nested_delimiter=env_nested_delimiter,
                secrets_dir=secrets_dir,
                case_sensitive=case_sensitive,
                field_count=field_count,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_validators(self, content: str, result: PydanticEnhancedParseResult):
        """Extract all validator types."""
        # @field_validator (v2)
        for match in self.FIELD_VALIDATOR_PATTERN.finditer(content):
            args_str = match.group(1)
            handler = match.group(2)

            fields = []
            mode = "after"

            # Parse field names and mode
            for part in args_str.split(','):
                part = part.strip().strip('"\'')
                if part.startswith('mode=') or part.startswith('mode ='):
                    mode = part.split('=')[1].strip().strip('"\'')
                elif part and not part.startswith('*'):
                    fields.append(part)

            result.validators.append(PydanticValidatorDetailInfo(
                name=handler,
                validator_type="field_validator",
                fields=fields,
                mode=mode,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @model_validator (v2)
        for match in self.MODEL_VALIDATOR_PATTERN.finditer(content):
            mode = match.group(1)
            handler = match.group(2)

            result.validators.append(PydanticValidatorDetailInfo(
                name=handler,
                validator_type="model_validator",
                mode=mode,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @validator (v1)
        for match in self.V1_VALIDATOR_PATTERN.finditer(content):
            args_str = match.group(1)
            handler = match.group(2)

            fields = []
            mode = "after"

            for part in args_str.split(','):
                part = part.strip().strip('"\'')
                if part.startswith('pre=') or part.startswith('pre ='):
                    if 'True' in part:
                        mode = "before"
                elif part and not part.startswith('always') and not part.startswith('each_item'):
                    fields.append(part)

            result.validators.append(PydanticValidatorDetailInfo(
                name=handler,
                validator_type="validator",
                fields=fields,
                mode=mode,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @root_validator (v1)
        for match in self.V1_ROOT_VALIDATOR_PATTERN.finditer(content):
            pre = match.group(1)
            handler = match.group(2)

            mode = "before" if pre == 'True' else "after"

            result.validators.append(PydanticValidatorDetailInfo(
                name=handler,
                validator_type="root_validator",
                mode=mode,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @validate_call (v2)
        for match in self.VALIDATE_CALL_PATTERN.finditer(content):
            handler = match.group(2)

            result.validators.append(PydanticValidatorDetailInfo(
                name=handler,
                validator_type="validate_call",
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_serializers(self, content: str, result: PydanticEnhancedParseResult):
        """Extract serializer decorators."""
        # @field_serializer
        for match in self.FIELD_SERIALIZER_PATTERN.finditer(content):
            args_str = match.group(1)
            handler = match.group(2)

            fields = []
            mode = "plain"

            for part in args_str.split(','):
                part = part.strip().strip('"\'')
                if part.startswith('mode=') or part.startswith('mode ='):
                    mode = part.split('=')[1].strip().strip('"\'')
                elif part and not part.startswith('when_used'):
                    fields.append(part)

            result.serializers.append(PydanticSerializerInfo(
                name=handler,
                serializer_type="field_serializer",
                fields=fields,
                mode=mode,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @model_serializer
        for match in self.MODEL_SERIALIZER_PATTERN.finditer(content):
            mode = match.group(1) or "plain"
            handler = match.group(2)

            result.serializers.append(PydanticSerializerInfo(
                name=handler,
                serializer_type="model_serializer",
                mode=mode,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_type_adapters(self, content: str, result: PydanticEnhancedParseResult):
        """Extract TypeAdapter instances."""
        for match in self.TYPE_ADAPTER_PATTERN.finditer(content):
            var_name = match.group(1)
            adapted_type = match.group(2).strip()

            result.type_adapters.append(PydanticTypeAdapterInfo(
                variable_name=var_name,
                adapted_type=adapted_type,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_custom_types(self, content: str, result: PydanticEnhancedParseResult):
        """Extract custom Annotated types with Pydantic validators/serializers."""
        for match in self.ANNOTATED_TYPE_PATTERN.finditer(content):
            name = match.group(1)
            base_type = match.group(2)
            type_kind = match.group(3)

            result.custom_types.append(PydanticCustomTypeInfo(
                name=name,
                type_kind=type_kind,
                base_type=base_type,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_discriminated_unions(self, content: str, result: PydanticEnhancedParseResult):
        """Extract discriminated union patterns."""
        # Annotated[Union[...], Discriminator(...)]
        for match in self.DISCRIMINATED_UNION_PATTERN.finditer(content):
            name = match.group(1)
            variants_str = match.group(2)
            discriminator = match.group(3)

            variants = [v.strip() for v in variants_str.split(',') if v.strip()]

            result.discriminated_unions.append(PydanticDiscriminatedUnionInfo(
                name=name,
                discriminator=discriminator,
                variants=variants,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Field(discriminator="...")
        for match in self.FIELD_DISCRIMINATOR_PATTERN.finditer(content):
            name = match.group(1)
            variants_str = match.group(2) or ""
            discriminator = match.group(3)

            variants = [v.strip() for v in variants_str.split(',') if v.strip()] if variants_str else []

            # Avoid duplicates
            already = any(d.name == name for d in result.discriminated_unions)
            if not already:
                result.discriminated_unions.append(PydanticDiscriminatedUnionInfo(
                    name=name,
                    discriminator=discriminator,
                    variants=variants,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

    def _extract_pydantic_dataclasses(self, content: str, result: PydanticEnhancedParseResult):
        """Extract @pydantic.dataclass decorated classes."""
        # We need to check that pydantic dataclasses is actually imported
        if not re.search(r'pydantic\.dataclass|from\s+pydantic\.dataclasses\s+import|from\s+pydantic\s+import\s+.*\bdataclass\b', content):
            return

        for match in self.PYDANTIC_DATACLASS_PATTERN.finditer(content):
            name = match.group(1)

            # Get class body to count fields
            class_start = match.end()
            remaining = content[class_start:]
            # Find the "class ClassName" part end (after the decorator match)
            class_def_match = re.match(r'[^:]*:', remaining)
            if class_def_match:
                body_start = class_start + class_def_match.end()
            else:
                body_start = class_start

            class_body = self._extract_class_body(content, body_start) or ""
            field_count = len(self.FIELD_LINE_PATTERN.findall(class_body))

            result.pydantic_dataclasses.append(PydanticDataclassInfo(
                name=name,
                field_count=field_count,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_plugins(self, content: str, result: PydanticEnhancedParseResult):
        """Extract Pydantic plugins."""
        for match in self.PLUGIN_CLASS_PATTERN.finditer(content):
            name = match.group(1)

            result.plugins.append(PydanticPluginInfo(
                name=name,
                plugin_type="PydanticPlugin",
                line_number=content[:match.start()].count('\n') + 1,
            ))

    # ─── Helper methods ───────────────────────────────────────────

    def _extract_class_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract the body of a class from start_pos (after the colon)."""
        lines = content[start_pos:].split('\n')

        if not lines:
            return None

        body_lines = []
        base_indent = None

        for line in lines:
            if not line.strip():
                if base_indent is not None:
                    body_lines.append('')
                continue

            # Calculate indentation
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            if base_indent is None:
                if stripped:
                    base_indent = indent
                    body_lines.append(line)
            else:
                if indent >= base_indent:
                    body_lines.append(line)
                else:
                    # End of class body
                    break

        return '\n'.join(body_lines)

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a Pydantic file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        # Test files checked first (test_models.py should be 'test' not 'model')
        if basename.startswith('test_') or basename.endswith('_test.py') or 'conftest' in basename:
            return 'test'
        if 'model' in basename or 'schema' in basename:
            return 'model'
        if 'settings' in basename or 'config' in basename:
            return 'settings'
        if 'validator' in basename:
            return 'validator'
        if 'serializer' in basename:
            return 'serializer'
        if 'type' in basename and 'test' not in basename:
            return 'types'

        if '/models/' in normalized or '/schemas/' in normalized:
            return 'model'
        if '/settings/' in normalized or '/config/' in normalized:
            return 'settings'

        return 'module'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Pydantic ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_pydantic_version(self, content: str) -> str:
        """Detect minimum Pydantic version required based on features used."""
        max_version = '0.0'
        for feature, version in self.PYDANTIC_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version
        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_pydantic_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a Pydantic-heavy file.
        Returns True if the file uses Pydantic extensively (beyond basic model usage).
        """
        # Direct pydantic imports
        if re.search(r'from\s+pydantic\s+import|import\s+pydantic\b|from\s+pydantic\.\w+\s+import', content):
            return True
        # Pydantic settings imports
        if re.search(r'from\s+pydantic_settings\s+import', content):
            return True
        # BaseModel/BaseSettings subclass
        if re.search(r'class\s+\w+\s*\([^)]*(?:BaseModel|BaseSettings|RootModel|GenericModel)[^)]*\)', content):
            return True
        return False

    def to_codetrellis_format(self, result: PydanticEnhancedParseResult) -> str:
        """Convert parse result to CodeTrellis compressed format."""
        lines = []

        if result.file_path:
            lines.append(f"[FILE:{Path(result.file_path).name}|type:{result.file_type}]")
        if result.detected_frameworks:
            lines.append(f"[PYDANTIC_ECOSYSTEM:{','.join(result.detected_frameworks)}]")
        if result.pydantic_version:
            lines.append(f"[PYDANTIC_VERSION:>={result.pydantic_version}]")
        lines.append("")

        # Models
        if result.models:
            lines.append("=== PYDANTIC_MODELS ===")
            for m in result.models:
                generic_str = "|generic" if m.is_generic else ""
                config_str = "|config" if m.has_config else ""
                computed_str = "|computed" if m.has_computed_fields else ""
                lines.append(f"  {m.name}[{m.model_type}]|fields:{m.field_count}|validators:{m.validator_count}{generic_str}{config_str}{computed_str}")
            lines.append("")

        # Settings
        if result.settings:
            lines.append("=== PYDANTIC_SETTINGS ===")
            for s in result.settings:
                prefix_str = f"|env_prefix:{s.env_prefix}" if s.env_prefix else ""
                file_str = f"|env_file:{s.env_file}" if s.env_file else ""
                lines.append(f"  {s.name}|fields:{s.field_count}{prefix_str}{file_str}")
            lines.append("")

        # Validators
        if result.validators:
            lines.append("=== PYDANTIC_VALIDATORS ===")
            for v in result.validators:
                fields_str = f"|fields:{','.join(v.fields)}" if v.fields else ""
                lines.append(f"  {v.name}[{v.validator_type}]|mode:{v.mode}{fields_str}")
            lines.append("")

        # Serializers
        if result.serializers:
            lines.append("=== PYDANTIC_SERIALIZERS ===")
            for s in result.serializers:
                fields_str = f"|fields:{','.join(s.fields)}" if s.fields else ""
                lines.append(f"  {s.name}[{s.serializer_type}]|mode:{s.mode}{fields_str}")
            lines.append("")

        # TypeAdapters
        if result.type_adapters:
            lines.append("=== PYDANTIC_TYPE_ADAPTERS ===")
            for ta in result.type_adapters:
                lines.append(f"  {ta.variable_name}=TypeAdapter({ta.adapted_type})")
            lines.append("")

        # Custom types
        if result.custom_types:
            lines.append("=== PYDANTIC_CUSTOM_TYPES ===")
            for ct in result.custom_types:
                lines.append(f"  {ct.name}=Annotated[{ct.base_type}, {ct.type_kind}]")
            lines.append("")

        # Discriminated unions
        if result.discriminated_unions:
            lines.append("=== PYDANTIC_DISCRIMINATED_UNIONS ===")
            for du in result.discriminated_unions:
                variants_str = ",".join(du.variants)
                lines.append(f"  {du.name}|discriminator:{du.discriminator}|variants:[{variants_str}]")
            lines.append("")

        # Pydantic dataclasses
        if result.pydantic_dataclasses:
            lines.append("=== PYDANTIC_DATACLASSES ===")
            for dc in result.pydantic_dataclasses:
                lines.append(f"  {dc.name}|fields:{dc.field_count}")
            lines.append("")

        # Plugins
        if result.plugins:
            lines.append("=== PYDANTIC_PLUGINS ===")
            for p in result.plugins:
                lines.append(f"  {p.name}[{p.plugin_type}]")
            lines.append("")

        return '\n'.join(lines)
