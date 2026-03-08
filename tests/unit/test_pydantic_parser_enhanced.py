"""
Tests for Enhanced Pydantic Parser.

Part of CodeTrellis v4.93 Pydantic Framework Support.
Tests cover:
- Model extraction (BaseModel, RootModel, GenericModel)
- Settings extraction (BaseSettings, env vars, secrets)
- Validator extraction (field_validator, model_validator, validator, root_validator, validate_call)
- Serializer extraction (field_serializer, model_serializer)
- TypeAdapter extraction
- Custom type extraction (Annotated with BeforeValidator, AfterValidator, etc.)
- Discriminated union extraction
- Pydantic dataclass extraction
- Plugin extraction
- Framework detection (v1, v2, settings, types, etc.)
- Version detection
- is_pydantic_file detection
- to_codetrellis_format output
"""

import pytest
from codetrellis.pydantic_parser_enhanced import (
    EnhancedPydanticParser,
    PydanticEnhancedParseResult,
    PydanticEnhancedModelInfo,
    PydanticSettingsInfo,
    PydanticValidatorDetailInfo,
    PydanticSerializerInfo,
    PydanticTypeAdapterInfo,
    PydanticCustomTypeInfo,
    PydanticDiscriminatedUnionInfo,
    PydanticDataclassInfo,
    PydanticPluginInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedPydanticParser()


# ═══════════════════════════════════════════════════════════════════
# Model Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticModels:

    def test_extract_basic_model(self, parser):
        source = '''
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
    age: int
'''
        result = parser.parse(source, "models.py")
        assert len(result.models) >= 1
        model = result.models[0]
        assert model.name == "User"
        assert model.model_type == "BaseModel"
        assert model.field_count >= 3

    def test_extract_model_with_config(self, parser):
        source = '''
from pydantic import BaseModel, ConfigDict

class StrictUser(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    name: str
    age: int
'''
        result = parser.parse(source, "models.py")
        assert len(result.models) >= 1
        assert result.models[0].has_config is True

    def test_extract_model_with_validators(self, parser):
        source = '''
from pydantic import BaseModel, field_validator

class User(BaseModel):
    name: str
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return v
'''
        result = parser.parse(source, "models.py")
        assert len(result.models) >= 1
        assert result.models[0].validator_count >= 1

    def test_extract_root_model(self, parser):
        source = '''
from pydantic import RootModel

class IntList(RootModel[list[int]]):
    pass
'''
        result = parser.parse(source, "models.py")
        assert len(result.models) >= 1
        model = result.models[0]
        assert model.name == "IntList"
        assert model.model_type == "RootModel"

    def test_extract_generic_model(self, parser):
        source = '''
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    data: T
    status: int
'''
        result = parser.parse(source, "models.py")
        # BaseModel with Generic mixin - should detect is_generic
        assert len(result.models) >= 1

    def test_extract_multiple_models(self, parser):
        source = '''
from pydantic import BaseModel

class User(BaseModel):
    name: str

class Item(BaseModel):
    title: str
    price: float

class Order(BaseModel):
    user_id: int
    items: list
'''
        result = parser.parse(source, "models.py")
        assert len(result.models) >= 3

    def test_extract_model_with_computed_field(self, parser):
        source = '''
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height
'''
        result = parser.parse(source, "models.py")
        assert len(result.models) >= 1
        assert result.models[0].has_computed_fields is True


# ═══════════════════════════════════════════════════════════════════
# Settings Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticSettings:

    def test_extract_basic_settings(self, parser):
        source = '''
from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    database_url: str
'''
        result = parser.parse(source, "settings.py")
        assert len(result.settings) >= 1
        settings = result.settings[0]
        assert settings.name == "AppSettings"
        assert settings.field_count >= 3

    def test_extract_settings_with_env_prefix(self, parser):
        source = '''
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    host: str
    port: int
    name: str

    model_config = ConfigDict(env_prefix="DB_")
'''
        result = parser.parse(source, "settings.py")
        assert len(result.settings) >= 1

    def test_extract_settings_with_env_file(self, parser):
        source = '''
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    api_key: str

    class Config:
        env_file = ".env"
'''
        result = parser.parse(source, "config.py")
        assert len(result.settings) >= 1

    def test_extract_settings_with_secrets(self, parser):
        source = '''
from pydantic_settings import BaseSettings

class SecretConfig(BaseSettings):
    db_password: str
    api_secret: str

    class Config:
        secrets_dir = "/run/secrets"
'''
        result = parser.parse(source, "config.py")
        assert len(result.settings) >= 1


# ═══════════════════════════════════════════════════════════════════
# Validator Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticValidators:

    def test_extract_field_validator(self, parser):
        source = '''
from pydantic import BaseModel, field_validator

class User(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email")
        return v
'''
        result = parser.parse(source, "models.py")
        assert len(result.validators) >= 1
        v = result.validators[0]
        assert v.name == "validate_email"
        assert v.validator_type == "field_validator"
        assert "email" in v.fields

    def test_extract_model_validator(self, parser):
        source = '''
from pydantic import BaseModel, model_validator

class DateRange(BaseModel):
    start: str
    end: str

    @model_validator(mode="after")
    def validate_range(self):
        return self
'''
        result = parser.parse(source, "models.py")
        assert len(result.validators) >= 1
        v = result.validators[0]
        assert v.validator_type == "model_validator"
        assert v.mode == "after"

    def test_extract_model_validator_before(self, parser):
        source = '''
from pydantic import BaseModel, model_validator

class MyModel(BaseModel):
    value: int

    @model_validator(mode="before")
    @classmethod
    def pre_validate(cls, data):
        return data
'''
        result = parser.parse(source, "models.py")
        assert len(result.validators) >= 1
        v = result.validators[0]
        assert v.mode == "before"

    def test_extract_v1_validator(self, parser):
        source = '''
from pydantic import BaseModel, validator

class LegacyModel(BaseModel):
    name: str

    @validator("name")
    @classmethod
    def clean_name(cls, v):
        return v.strip()
'''
        result = parser.parse(source, "models.py")
        assert len(result.validators) >= 1
        v = result.validators[0]
        assert v.validator_type == "validator"
        assert "name" in v.fields

    def test_extract_v1_root_validator(self, parser):
        source = '''
from pydantic import BaseModel, root_validator

class LegacyModel(BaseModel):
    a: int
    b: int

    @root_validator
    @classmethod
    def check_sum(cls, values):
        return values
'''
        result = parser.parse(source, "models.py")
        assert len(result.validators) >= 1
        v = result.validators[0]
        assert v.validator_type == "root_validator"

    def test_extract_validate_call(self, parser):
        source = '''
from pydantic import validate_call

@validate_call
def process_data(x: int, y: str) -> str:
    return f"{x}: {y}"
'''
        result = parser.parse(source, "utils.py")
        assert len(result.validators) >= 1
        v = result.validators[0]
        assert v.validator_type == "validate_call"
        assert v.name == "process_data"

    def test_extract_multiple_field_validators(self, parser):
        source = '''
from pydantic import BaseModel, field_validator

class User(BaseModel):
    name: str
    email: str

    @field_validator("name", "email")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip()
'''
        result = parser.parse(source, "models.py")
        assert len(result.validators) >= 1
        v = result.validators[0]
        assert len(v.fields) >= 2


# ═══════════════════════════════════════════════════════════════════
# Serializer Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticSerializers:

    def test_extract_field_serializer(self, parser):
        source = '''
from pydantic import BaseModel, field_serializer

class Event(BaseModel):
    timestamp: datetime

    @field_serializer("timestamp")
    def serialize_timestamp(self, v):
        return v.isoformat()
'''
        result = parser.parse(source, "models.py")
        assert len(result.serializers) >= 1
        s = result.serializers[0]
        assert s.name == "serialize_timestamp"
        assert s.serializer_type == "field_serializer"
        assert "timestamp" in s.fields

    def test_extract_model_serializer(self, parser):
        source = '''
from pydantic import BaseModel, model_serializer

class CustomModel(BaseModel):
    data: dict

    @model_serializer
    def serialize_model(self):
        return {"wrapped": self.data}
'''
        result = parser.parse(source, "models.py")
        assert len(result.serializers) >= 1
        s = result.serializers[0]
        assert s.serializer_type == "model_serializer"

    def test_extract_model_serializer_with_mode(self, parser):
        source = '''
from pydantic import BaseModel, model_serializer

class WrapModel(BaseModel):
    value: int

    @model_serializer(mode="wrap")
    def custom_serialize(self, handler):
        return handler(self)
'''
        result = parser.parse(source, "models.py")
        assert len(result.serializers) >= 1
        assert result.serializers[0].mode == "wrap"


# ═══════════════════════════════════════════════════════════════════
# TypeAdapter Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticTypeAdapters:

    def test_extract_type_adapter(self, parser):
        source = '''
from pydantic import TypeAdapter

int_list_adapter = TypeAdapter(list[int])
'''
        result = parser.parse(source, "adapters.py")
        assert len(result.type_adapters) >= 1
        ta = result.type_adapters[0]
        assert ta.variable_name == "int_list_adapter"
        assert "list[int]" in ta.adapted_type

    def test_extract_multiple_type_adapters(self, parser):
        source = '''
from pydantic import TypeAdapter

str_adapter = TypeAdapter(str)
user_adapter = TypeAdapter(User)
list_adapter = TypeAdapter(list[dict])
'''
        result = parser.parse(source, "adapters.py")
        assert len(result.type_adapters) >= 3


# ═══════════════════════════════════════════════════════════════════
# Custom Type Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticCustomTypes:

    def test_extract_annotated_before_validator(self, parser):
        source = '''
from typing import Annotated
from pydantic import BeforeValidator

UpperStr = Annotated[str, BeforeValidator(lambda v: v.upper())]
'''
        result = parser.parse(source, "types.py")
        assert len(result.custom_types) >= 1
        ct = result.custom_types[0]
        assert ct.name == "UpperStr"
        assert ct.type_kind == "BeforeValidator"
        assert ct.base_type == "str"

    def test_extract_annotated_after_validator(self, parser):
        source = '''
from typing import Annotated
from pydantic import AfterValidator

PositiveInt = Annotated[int, AfterValidator(lambda v: max(0, v))]
'''
        result = parser.parse(source, "types.py")
        assert len(result.custom_types) >= 1
        assert result.custom_types[0].type_kind == "AfterValidator"


# ═══════════════════════════════════════════════════════════════════
# Discriminated Union Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticDiscriminatedUnions:

    def test_extract_discriminated_union(self, parser):
        source = '''
from typing import Annotated, Union
from pydantic import Discriminator

Animal = Annotated[Union[Cat, Dog], Discriminator("pet_type")]
'''
        result = parser.parse(source, "types.py")
        assert len(result.discriminated_unions) >= 1
        du = result.discriminated_unions[0]
        assert du.name == "Animal"
        assert du.discriminator == "pet_type"
        assert "Cat" in du.variants
        assert "Dog" in du.variants


# ═══════════════════════════════════════════════════════════════════
# Pydantic Dataclass Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticDataclasses:

    def test_extract_pydantic_dataclass(self, parser):
        source = '''
from pydantic.dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float
'''
        result = parser.parse(source, "models.py")
        assert len(result.pydantic_dataclasses) >= 1
        dc = result.pydantic_dataclasses[0]
        assert dc.name == "Point"

    def test_extract_pydantic_dot_dataclass(self, parser):
        source = '''
import pydantic

@pydantic.dataclass
class Config:
    name: str
    value: int
'''
        result = parser.parse(source, "models.py")
        assert len(result.pydantic_dataclasses) >= 1


# ═══════════════════════════════════════════════════════════════════
# Plugin Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticPlugins:

    def test_extract_pydantic_plugin(self, parser):
        source = '''
from pydantic.plugin import PydanticPlugin

class MyPlugin(PydanticPlugin):
    def on_validate_python(self, schema, *args, **kwargs):
        pass
'''
        result = parser.parse(source, "plugins.py")
        assert len(result.plugins) >= 1
        assert result.plugins[0].name == "MyPlugin"


# ═══════════════════════════════════════════════════════════════════
# Framework Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticFrameworkDetection:

    def test_detect_pydantic_core(self, parser):
        source = '''
from pydantic import BaseModel
'''
        result = parser.parse(source, "models.py")
        assert 'pydantic-core' in result.detected_frameworks

    def test_detect_pydantic_settings(self, parser):
        source = '''
from pydantic_settings import BaseSettings
'''
        result = parser.parse(source, "settings.py")
        assert 'pydantic-settings' in result.detected_frameworks

    def test_detect_pydantic_v2_features(self, parser):
        source = '''
from pydantic import BaseModel, ConfigDict, field_validator, TypeAdapter, RootModel
'''
        result = parser.parse(source, "models.py")
        assert 'pydantic-v2' in result.detected_frameworks

    def test_detect_pydantic_v1_features(self, parser):
        source = '''
from pydantic import BaseModel, validator

class MyModel(BaseModel):
    class Config:
        orm_mode = True
'''
        result = parser.parse(source, "models.py")
        assert 'pydantic-v1' in result.detected_frameworks

    def test_detect_pydantic_annotated(self, parser):
        source = '''
from pydantic import BeforeValidator, AfterValidator
'''
        result = parser.parse(source, "types.py")
        assert 'pydantic-annotated' in result.detected_frameworks

    def test_detect_pydantic_functional(self, parser):
        source = '''
from pydantic import validate_call

@validate_call
def func(x: int) -> int:
    return x
'''
        result = parser.parse(source, "utils.py")
        assert 'pydantic-functional' in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Version Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticVersionDetection:

    def test_detect_v1(self, parser):
        source = '''
from pydantic import BaseModel, validator

class User(BaseModel):
    name: str

    @validator("name")
    @classmethod
    def clean(cls, v):
        return v

    class Config:
        orm_mode = True
'''
        result = parser.parse(source, "models.py")
        assert result.pydantic_version == '1.0'

    def test_detect_v2(self, parser):
        source = '''
from pydantic import BaseModel, ConfigDict, field_validator

class User(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str

    @field_validator("name")
    @classmethod
    def clean(cls, v):
        return v
'''
        result = parser.parse(source, "models.py")
        assert result.pydantic_version == '2.0'

    def test_detect_v2_4_plugin(self, parser):
        source = '''
from pydantic.plugin import PydanticPlugin

class MyPlugin(PydanticPlugin):
    pass
'''
        result = parser.parse(source, "plugins.py")
        assert result.pydantic_version == '2.4'


# ═══════════════════════════════════════════════════════════════════
# is_pydantic_file Tests
# ═══════════════════════════════════════════════════════════════════

class TestIsPydanticFile:

    def test_detects_pydantic_import(self, parser):
        source = '''
from pydantic import BaseModel
'''
        assert parser.is_pydantic_file(source) is True

    def test_detects_pydantic_settings_import(self, parser):
        source = '''
from pydantic_settings import BaseSettings
'''
        assert parser.is_pydantic_file(source) is True

    def test_detects_pydantic_submodule(self, parser):
        source = '''
from pydantic.fields import FieldInfo
'''
        assert parser.is_pydantic_file(source) is True

    def test_detects_basemodel_subclass(self, parser):
        source = '''
class MyModel(BaseModel):
    name: str
'''
        assert parser.is_pydantic_file(source) is True

    def test_no_detection_for_non_pydantic(self, parser):
        source = '''
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float
'''
        assert parser.is_pydantic_file(source) is False


# ═══════════════════════════════════════════════════════════════════
# to_codetrellis_format Tests
# ═══════════════════════════════════════════════════════════════════

class TestToCodetrelisFormat:

    def test_format_output_with_models(self, parser):
        source = '''
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
'''
        result = parser.parse(source, "models.py")
        output = parser.to_codetrellis_format(result)
        assert "PYDANTIC_MODELS" in output
        assert "User" in output

    def test_format_output_with_validators(self, parser):
        source = '''
from pydantic import BaseModel, field_validator

class User(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return v
'''
        result = parser.parse(source, "models.py")
        output = parser.to_codetrellis_format(result)
        assert "PYDANTIC_VALIDATORS" in output

    def test_format_empty_result(self, parser):
        source = '''
x = 1
'''
        result = parser.parse(source, "empty.py")
        output = parser.to_codetrellis_format(result)
        assert "PYDANTIC_MODELS" not in output


# ═══════════════════════════════════════════════════════════════════
# File Classification Tests
# ═══════════════════════════════════════════════════════════════════

class TestFileClassification:

    def test_classify_model_file(self, parser):
        source = 'from pydantic import BaseModel'
        result = parser.parse(source, "models.py")
        assert result.file_type == "model"

    def test_classify_settings_file(self, parser):
        source = 'from pydantic_settings import BaseSettings'
        result = parser.parse(source, "settings.py")
        assert result.file_type == "settings"

    def test_classify_test_file(self, parser):
        source = 'import pytest'
        result = parser.parse(source, "test_models.py")
        assert result.file_type == "test"


# ═══════════════════════════════════════════════════════════════════
# Complex Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestPydanticIntegration:

    def test_full_v2_app_parsing(self, parser):
        source = '''
from pydantic import BaseModel, ConfigDict, field_validator, model_validator, field_serializer, computed_field, TypeAdapter, RootModel, validate_call
from pydantic_settings import BaseSettings
from typing import Annotated, Union
from pydantic import BeforeValidator, Discriminator

# Settings
class AppConfig(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    db_url: str

# Models
class User(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str
    email: str
    age: int

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return v

    @model_validator(mode="after")
    def check_age(self):
        return self

    @field_serializer("email")
    def mask_email(self, v):
        return v[:3] + "***"

    @computed_field
    @property
    def display_name(self) -> str:
        return self.name

class UserList(RootModel[list[User]]):
    pass

# TypeAdapter
user_adapter = TypeAdapter(User)

# Custom type
UpperStr = Annotated[str, BeforeValidator(lambda v: v.upper())]

# Discriminated union
Pet = Annotated[Union[Cat, Dog], Discriminator("type")]

# Validate call
@validate_call
def process(x: int) -> str:
    return str(x)
'''
        result = parser.parse(source, "app.py")
        assert len(result.models) >= 2  # User, UserList
        assert len(result.settings) >= 1  # AppConfig
        assert len(result.validators) >= 3  # validate_email, check_age, process
        assert len(result.serializers) >= 1  # mask_email
        assert len(result.type_adapters) >= 1  # user_adapter
        assert len(result.custom_types) >= 1  # UpperStr
        assert len(result.discriminated_unions) >= 1  # Pet
        assert result.pydantic_version >= '2.0'
        assert result.total_models >= 2
        assert result.total_validators >= 3

    def test_v1_compatibility(self, parser):
        source = '''
from pydantic import BaseModel, validator, root_validator

class LegacyModel(BaseModel):
    name: str
    value: int

    @validator("name")
    @classmethod
    def clean_name(cls, v):
        return v.strip()

    @root_validator
    @classmethod
    def validate_all(cls, values):
        return values

    class Config:
        orm_mode = True
'''
        result = parser.parse(source, "legacy.py")
        assert len(result.models) >= 1
        assert len(result.validators) >= 2
        validator_types = [v.validator_type for v in result.validators]
        assert "validator" in validator_types
        assert "root_validator" in validator_types
        assert 'pydantic-v1' in result.detected_frameworks
