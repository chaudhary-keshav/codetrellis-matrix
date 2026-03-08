"""
CodeTrellis Python Extractors Module v2.0

Provides comprehensive extractors for Python AI/ML ecosystem:

Core Type Extractors:
- DataclassExtractor: @dataclass decorated classes
- PydanticExtractor: Pydantic BaseModel classes
- TypedDictExtractor: TypedDict definitions
- ProtocolExtractor: Protocol classes
- TypeAliasExtractor: Type aliases, Union, Literal
- EnumExtractor: Enum, StrEnum, IntEnum, Flag

Web Framework Extractors:
- FastAPIExtractor: FastAPI routes and dependencies
- FlaskExtractor: Flask routes and blueprints
- SQLAlchemyExtractor: SQLAlchemy models
- CeleryExtractor: Celery task definitions
- DependencyExtractor: Imports and project dependencies
- FunctionExtractor: Functions and classes

ML/AI Extractors (ml submodule):
- PyTorchExtractor: nn.Module, training loops, layers
- HuggingFaceExtractor: Models, tokenizers, trainers
- LangChainExtractor: Chains, agents, tools, prompts

Database Extractors (database submodule):
- MongoDBExtractor: PyMongo, Motor, Beanie ODM
- VectorDBExtractor: Pinecone, ChromaDB, Qdrant, FAISS
- RedisExtractor: Caching, Pub/Sub, Streams
- KafkaExtractor: Producers, Consumers, Streams

Data Processing Extractors (data submodule):
- PandasExtractor: DataFrame operations
- DataPipelineExtractor: Airflow, Prefect, Dagster

MLOps Extractors (mlops submodule):
- MLflowExtractor: Experiments, runs, model registry
- ConfigExtractor: Hydra, OmegaConf, Pydantic Settings
"""

# Core type extractors
from .dataclass_extractor import DataclassExtractor, DataclassInfo, DataclassFieldInfo
from .pydantic_extractor import PydanticExtractor, PydanticModelInfo, PydanticFieldInfo
from .typeddict_extractor import TypedDictExtractor, TypedDictInfo
from .protocol_extractor import ProtocolExtractor, ProtocolInfo
from .type_alias_extractor import PythonTypeAliasExtractor, PythonTypeAliasInfo
from .enum_extractor import PythonEnumExtractor, PythonEnumInfo

# Web framework extractors
from .fastapi_extractor import FastAPIExtractor, FastAPIRouteInfo
from .flask_extractor import FlaskExtractor, FlaskBlueprintInfo, FlaskRouteInfo
from .sqlalchemy_extractor import SQLAlchemyExtractor, SQLAlchemyModelInfo, SQLAlchemyColumnInfo
from .celery_extractor import CeleryExtractor, CeleryTaskInfo, CeleryBeatScheduleInfo
from .dependency_extractor import DependencyExtractor, ImportInfo, DependencyInfo
from .function_extractor import PythonFunctionExtractor, FunctionInfo, ClassInfo

# ML/AI extractors
from .ml import (
    PyTorchExtractor,
    HuggingFaceExtractor,
    LangChainExtractor,
    extract_pytorch,
    extract_huggingface,
    extract_langchain,
)

# Database extractors
from .database import (
    MongoDBExtractor,
    VectorDBExtractor,
    RedisExtractor,
    KafkaExtractor,
    extract_mongodb,
    extract_vectordb,
    extract_redis,
    extract_kafka,
)

# Data processing extractors
from .data import (
    PandasExtractor,
    DataPipelineExtractor,
    extract_pandas,
    extract_data_pipeline,
)

# MLOps extractors
from .mlops import (
    MLflowExtractor,
    ConfigExtractor,
    extract_mlflow,
    extract_config,
)

__all__ = [
    # === Core Type Extractors ===
    # Dataclass
    "DataclassExtractor",
    "DataclassInfo",
    "DataclassFieldInfo",
    # Pydantic
    "PydanticExtractor",
    "PydanticModelInfo",
    "PydanticFieldInfo",
    # TypedDict
    "TypedDictExtractor",
    "TypedDictInfo",
    # Protocol
    "ProtocolExtractor",
    "ProtocolInfo",
    # Type Aliases
    "PythonTypeAliasExtractor",
    "PythonTypeAliasInfo",
    # Enums
    "PythonEnumExtractor",
    "PythonEnumInfo",

    # === Web Framework Extractors ===
    # FastAPI
    "FastAPIExtractor",
    "FastAPIRouteInfo",
    # Flask
    "FlaskExtractor",
    "FlaskBlueprintInfo",
    "FlaskRouteInfo",
    # SQLAlchemy
    "SQLAlchemyExtractor",
    "SQLAlchemyModelInfo",
    "SQLAlchemyColumnInfo",
    # Celery
    "CeleryExtractor",
    "CeleryTaskInfo",
    "CeleryBeatScheduleInfo",
    # Dependencies
    "DependencyExtractor",
    "ImportInfo",
    "DependencyInfo",
    # Functions/Classes
    "PythonFunctionExtractor",
    "FunctionInfo",
    "ClassInfo",

    # === ML/AI Extractors ===
    "PyTorchExtractor",
    "HuggingFaceExtractor",
    "LangChainExtractor",
    "extract_pytorch",
    "extract_huggingface",
    "extract_langchain",

    # === Database Extractors ===
    "MongoDBExtractor",
    "VectorDBExtractor",
    "RedisExtractor",
    "KafkaExtractor",
    "extract_mongodb",
    "extract_vectordb",
    "extract_redis",
    "extract_kafka",

    # === Data Processing Extractors ===
    "PandasExtractor",
    "DataPipelineExtractor",
    "extract_pandas",
    "extract_data_pipeline",

    # === MLOps Extractors ===
    "MLflowExtractor",
    "ConfigExtractor",
    "extract_mlflow",
    "extract_config",
]
