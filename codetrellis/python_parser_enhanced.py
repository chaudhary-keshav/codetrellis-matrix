"""
EnhancedPythonParser v2.0 - Comprehensive Python parser using all extractors.

This parser integrates all Python extractors to provide complete
parsing of Python source files similar to how the TypeScript parser
handles Angular/NestJS projects.

Supports:
- Core Python types (dataclass, TypedDict, Protocol, Enum)
- Web frameworks (FastAPI, Flask, SQLAlchemy, Celery)
- ML/AI frameworks (PyTorch, HuggingFace, LangChain)
- Databases (MongoDB, Vector DBs, Redis, Kafka)
- Data processing (Pandas, Airflow/Prefect/Dagster)
- MLOps (MLflow, Hydra/OmegaConf config)

Part of CodeTrellis v2.0 - Python AI/ML Lifecycle Support
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all core extractors
from .extractors.python import (
    DataclassExtractor, DataclassInfo,
    PydanticExtractor, PydanticModelInfo,
    TypedDictExtractor, TypedDictInfo,
    ProtocolExtractor, ProtocolInfo,
    PythonTypeAliasExtractor, PythonTypeAliasInfo,
    PythonEnumExtractor, PythonEnumInfo,
    FastAPIExtractor, FastAPIRouteInfo,
    FlaskExtractor, FlaskBlueprintInfo, FlaskRouteInfo,
    SQLAlchemyExtractor, SQLAlchemyModelInfo,
    CeleryExtractor, CeleryTaskInfo,
    DependencyExtractor, ImportInfo, DependencyInfo,
    PythonFunctionExtractor, FunctionInfo, ClassInfo,
    # ML/AI extractors
    PyTorchExtractor,
    HuggingFaceExtractor,
    LangChainExtractor,
    # Database extractors
    MongoDBExtractor,
    VectorDBExtractor,
    RedisExtractor,
    KafkaExtractor,
    # Data processing extractors
    PandasExtractor,
    DataPipelineExtractor,
    # MLOps extractors
    MLflowExtractor,
    ConfigExtractor,
)


@dataclass
class PythonParseResult:
    """Complete parse result for a Python file."""
    file_path: str
    file_type: str = "python"

    # Type definitions
    dataclasses: List[DataclassInfo] = field(default_factory=list)
    pydantic_models: List[PydanticModelInfo] = field(default_factory=list)
    typeddicts: List[TypedDictInfo] = field(default_factory=list)
    protocols: List[ProtocolInfo] = field(default_factory=list)
    type_aliases: List[PythonTypeAliasInfo] = field(default_factory=list)
    enums: List[PythonEnumInfo] = field(default_factory=list)

    # Framework elements
    fastapi_routes: List[FastAPIRouteInfo] = field(default_factory=list)
    fastapi_routers: List[Any] = field(default_factory=list)
    flask_routes: List[FlaskRouteInfo] = field(default_factory=list)
    flask_blueprints: List[FlaskBlueprintInfo] = field(default_factory=list)
    sqlalchemy_models: List[SQLAlchemyModelInfo] = field(default_factory=list)
    celery_tasks: List[CeleryTaskInfo] = field(default_factory=list)
    celery_schedules: List[Any] = field(default_factory=list)

    # Code structure
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)

    # Dependencies
    imports: List[ImportInfo] = field(default_factory=list)

    # ML/AI results
    pytorch: Dict[str, Any] = field(default_factory=dict)
    huggingface: Dict[str, Any] = field(default_factory=dict)
    langchain: Dict[str, Any] = field(default_factory=dict)

    # Database results
    mongodb: Dict[str, Any] = field(default_factory=dict)
    vectordb: Dict[str, Any] = field(default_factory=dict)
    redis: Dict[str, Any] = field(default_factory=dict)
    kafka: Dict[str, Any] = field(default_factory=dict)

    # Data processing results
    pandas: Dict[str, Any] = field(default_factory=dict)
    pipeline: Dict[str, Any] = field(default_factory=dict)

    # MLOps results
    mlflow: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    docstring: Optional[str] = None
    detected_frameworks: List[str] = field(default_factory=list)


class EnhancedPythonParser:
    """
    Enhanced Python parser v2.0 that uses all extractors for comprehensive parsing.

    Automatically detects and extracts:
    - Core Python: dataclasses, Pydantic, TypedDict, Protocol, Enum
    - Web Frameworks: FastAPI, Flask, SQLAlchemy, Celery
    - ML/AI: PyTorch, HuggingFace Transformers, LangChain
    - Databases: MongoDB, Vector DBs, Redis, Kafka
    - Data: Pandas, Airflow/Prefect/Dagster pipelines
    - MLOps: MLflow, Hydra/OmegaConf configuration
    """

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'fastapi': re.compile(r'from\s+fastapi[\s.]|import\s+fastapi\b|from\s+starlette[\s.]'),
        'flask': re.compile(r'from\s+flask[\s.]|import\s+flask\b|from\s+flask_\w+'),
        'sanic': re.compile(r'from\s+sanic[\s.]|import\s+sanic\b|from\s+sanic_\w+'),
        'sqlalchemy': re.compile(r'from\s+sqlalchemy[\s.]|import\s+sqlalchemy\b'),
        'celery': re.compile(r'from\s+celery[\s.]|import\s+celery\b|@.*\.task'),
        'pydantic': re.compile(r'from\s+pydantic[\s.]|import\s+pydantic\b'),
        'django': re.compile(r'from\s+django[\s.]|import\s+django\b|from\s+rest_framework[\s.]|import\s+rest_framework\b'),
        'pytest': re.compile(r'import\s+pytest\b|from\s+pytest[\s.]'),
        # ML/AI frameworks
        'pytorch': re.compile(r'import\s+torch|from\s+torch\s+import'),
        'tensorflow': re.compile(r'import\s+tensorflow|from\s+tensorflow'),
        'huggingface': re.compile(r'from\s+transformers\s+import|import\s+transformers'),
        'langchain': re.compile(r'from\s+langchain|import\s+langchain'),
        # Databases
        'mongodb': re.compile(r'from\s+(?:pymongo|motor|beanie)|import\s+(?:pymongo|motor)'),
        'redis': re.compile(r'import\s+redis|from\s+redis|import\s+aioredis'),
        'kafka': re.compile(r'from\s+kafka|import\s+kafka|from\s+confluent_kafka'),
        # Vector DBs
        'pinecone': re.compile(r'import\s+pinecone|from\s+pinecone'),
        'chromadb': re.compile(r'import\s+chromadb|from\s+chromadb'),
        'qdrant': re.compile(r'from\s+qdrant_client|import\s+qdrant'),
        # Data processing
        'pandas': re.compile(r'import\s+pandas|from\s+pandas'),
        'airflow': re.compile(r'from\s+airflow|import\s+airflow'),
        'prefect': re.compile(r'from\s+prefect|import\s+prefect'),
        'dagster': re.compile(r'from\s+dagster|import\s+dagster'),
        # MLOps
        'mlflow': re.compile(r'import\s+mlflow|from\s+mlflow'),
        'hydra': re.compile(r'import\s+hydra|from\s+hydra'),
        'omegaconf': re.compile(r'from\s+omegaconf|import\s+omegaconf'),
    }

    def __init__(self):
        """Initialize the enhanced Python parser with all extractors."""
        # Core extractors
        self.dataclass_extractor = DataclassExtractor()
        self.pydantic_extractor = PydanticExtractor()
        self.typeddict_extractor = TypedDictExtractor()
        self.protocol_extractor = ProtocolExtractor()
        self.type_alias_extractor = PythonTypeAliasExtractor()
        self.enum_extractor = PythonEnumExtractor()

        # Web framework extractors
        self.fastapi_extractor = FastAPIExtractor()
        self.flask_extractor = FlaskExtractor()
        self.sqlalchemy_extractor = SQLAlchemyExtractor()
        self.celery_extractor = CeleryExtractor()
        self.dependency_extractor = DependencyExtractor()
        self.function_extractor = PythonFunctionExtractor()

        # ML/AI extractors
        self.pytorch_extractor = PyTorchExtractor()
        self.huggingface_extractor = HuggingFaceExtractor()
        self.langchain_extractor = LangChainExtractor()

        # Database extractors
        self.mongodb_extractor = MongoDBExtractor()
        self.vectordb_extractor = VectorDBExtractor()
        self.redis_extractor = RedisExtractor()
        self.kafka_extractor = KafkaExtractor()

        # Data processing extractors
        self.pandas_extractor = PandasExtractor()
        self.pipeline_extractor = DataPipelineExtractor()

        # MLOps extractors
        self.mlflow_extractor = MLflowExtractor()
        self.config_extractor = ConfigExtractor()
        self.fastapi_extractor = FastAPIExtractor()
        self.flask_extractor = FlaskExtractor()
        self.sqlalchemy_extractor = SQLAlchemyExtractor()
        self.celery_extractor = CeleryExtractor()
        self.dependency_extractor = DependencyExtractor()
        self.function_extractor = PythonFunctionExtractor()

    def parse(self, content: str, file_path: str = "") -> PythonParseResult:
        """
        Parse Python source code and extract all information.

        Args:
            content: Python source code
            file_path: Path to the source file

        Returns:
            PythonParseResult with all extracted information
        """
        result = PythonParseResult(file_path=file_path)

        # Detect frameworks first to optimize extraction
        result.detected_frameworks = self._detect_frameworks(content)

        # Extract module docstring
        result.docstring = self._extract_module_docstring(content)

        # Always extract core types
        result.dataclasses = self.dataclass_extractor.extract(content)
        result.type_aliases = self.type_alias_extractor.extract(content)
        result.enums = self.enum_extractor.extract(content)
        result.typeddicts = self.typeddict_extractor.extract(content)
        result.protocols = self.protocol_extractor.extract(content)

        # Extract based on detected frameworks
        if 'pydantic' in result.detected_frameworks or self._has_pydantic_patterns(content):
            result.pydantic_models = self.pydantic_extractor.extract(content)

        # Web frameworks
        if 'fastapi' in result.detected_frameworks:
            fastapi_result = self.fastapi_extractor.extract(content)
            result.fastapi_routes = fastapi_result.get('routes', [])
            result.fastapi_routers = fastapi_result.get('routers', [])

        if 'flask' in result.detected_frameworks:
            flask_result = self.flask_extractor.extract(content)
            result.flask_routes = flask_result.get('routes', [])
            result.flask_blueprints = flask_result.get('blueprints', [])

        if 'sqlalchemy' in result.detected_frameworks or self._has_sqlalchemy_patterns(content):
            result.sqlalchemy_models = self.sqlalchemy_extractor.extract(content)

        if 'celery' in result.detected_frameworks:
            celery_result = self.celery_extractor.extract(content)
            result.celery_tasks = celery_result.get('tasks', [])
            result.celery_schedules = celery_result.get('schedules', [])

        # ML/AI frameworks
        if 'pytorch' in result.detected_frameworks:
            result.pytorch = self.pytorch_extractor.extract(content)

        if 'huggingface' in result.detected_frameworks:
            result.huggingface = self.huggingface_extractor.extract(content)

        if 'langchain' in result.detected_frameworks:
            result.langchain = self.langchain_extractor.extract(content)

        # Databases
        if 'mongodb' in result.detected_frameworks:
            result.mongodb = self.mongodb_extractor.extract(content)

        if any(f in result.detected_frameworks for f in ['pinecone', 'chromadb', 'qdrant']):
            result.vectordb = self.vectordb_extractor.extract(content)

        if 'redis' in result.detected_frameworks:
            result.redis = self.redis_extractor.extract(content)

        if 'kafka' in result.detected_frameworks:
            result.kafka = self.kafka_extractor.extract(content)

        # Data processing
        if 'pandas' in result.detected_frameworks:
            result.pandas = self.pandas_extractor.extract(content)

        if any(f in result.detected_frameworks for f in ['airflow', 'prefect', 'dagster']):
            result.pipeline = self.pipeline_extractor.extract(content)

        # MLOps
        if 'mlflow' in result.detected_frameworks:
            result.mlflow = self.mlflow_extractor.extract(content)

        if any(f in result.detected_frameworks for f in ['hydra', 'omegaconf']):
            result.config = self.config_extractor.extract(content)

        # Extract imports
        result.imports = self.dependency_extractor.extract_imports(content)

        # Extract functions and classes
        func_result = self.function_extractor.extract(content)
        result.functions = func_result.get('functions', [])
        result.classes = func_result.get('classes', [])

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which frameworks are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _has_pydantic_patterns(self, content: str) -> bool:
        """Check for Pydantic patterns even without explicit import."""
        return bool(re.search(r'class\s+\w+\s*\(\s*BaseModel\s*\)', content))

    def _has_sqlalchemy_patterns(self, content: str) -> bool:
        """Check for SQLAlchemy patterns even without explicit import."""
        return bool(re.search(r'class\s+\w+\s*\(\s*(?:Base|DeclarativeBase)\s*\)', content))

    def _extract_module_docstring(self, content: str) -> Optional[str]:
        """Extract the module-level docstring."""
        match = re.match(r'^\s*(?:"""(.*?)"""|\'\'\'(.*?)\'\'\')', content, re.DOTALL)
        if match:
            return (match.group(1) or match.group(2)).strip()
        return None

    def to_codetrellis_format(self, result: PythonParseResult) -> str:
        """
        Convert parse result to CodeTrellis compressed format.

        Args:
            result: PythonParseResult from parsing

        Returns:
            CodeTrellis formatted string
        """
        lines = []

        # File header
        if result.file_path:
            lines.append(f"[FILE:{Path(result.file_path).name}]")

        # Frameworks detected
        if result.detected_frameworks:
            lines.append(f"[FRAMEWORKS:{','.join(result.detected_frameworks)}]")

        lines.append("")

        # Type definitions section
        type_sections = []

        # Dataclasses
        if result.dataclasses:
            type_sections.append(self.dataclass_extractor.to_codetrellis_format(result.dataclasses))

        # Pydantic
        if result.pydantic_models:
            type_sections.append(self.pydantic_extractor.to_codetrellis_format(result.pydantic_models))

        # TypedDicts
        if result.typeddicts:
            type_sections.append(self.typeddict_extractor.to_codetrellis_format(result.typeddicts))

        # Protocols
        if result.protocols:
            type_sections.append(self.protocol_extractor.to_codetrellis_format(result.protocols))

        # Type aliases
        if result.type_aliases:
            type_sections.append(self.type_alias_extractor.to_codetrellis_format(result.type_aliases))

        # Enums
        if result.enums:
            type_sections.append(self.enum_extractor.to_codetrellis_format(result.enums))

        if type_sections:
            lines.append("=== TYPES ===")
            lines.extend(type_sections)
            lines.append("")

        # Framework sections
        framework_sections = []

        # FastAPI
        if result.fastapi_routes or result.fastapi_routers:
            framework_sections.append(self.fastapi_extractor.to_codetrellis_format({
                'routes': result.fastapi_routes,
                'routers': result.fastapi_routers
            }))

        # Flask
        if result.flask_routes or result.flask_blueprints:
            framework_sections.append(self.flask_extractor.to_codetrellis_format({
                'routes': result.flask_routes,
                'blueprints': result.flask_blueprints
            }))

        # SQLAlchemy
        if result.sqlalchemy_models:
            framework_sections.append(self.sqlalchemy_extractor.to_codetrellis_format(result.sqlalchemy_models))

        # Celery
        if result.celery_tasks or result.celery_schedules:
            framework_sections.append(self.celery_extractor.to_codetrellis_format({
                'tasks': result.celery_tasks,
                'schedules': result.celery_schedules
            }))

        if framework_sections:
            lines.append("=== FRAMEWORK ===")
            lines.extend(framework_sections)
            lines.append("")

        # ML/AI sections
        ml_sections = []

        # PyTorch
        if result.pytorch:
            ml_sections.append(self.pytorch_extractor.to_codetrellis_format(result.pytorch))

        # HuggingFace
        if result.huggingface:
            ml_sections.append(self.huggingface_extractor.to_codetrellis_format(result.huggingface))

        # LangChain
        if result.langchain:
            ml_sections.append(self.langchain_extractor.to_codetrellis_format(result.langchain))

        if ml_sections:
            lines.append("=== ML/AI ===")
            lines.extend(ml_sections)
            lines.append("")

        # Database sections
        db_sections = []

        # MongoDB
        if result.mongodb:
            db_sections.append(self.mongodb_extractor.to_codetrellis_format(result.mongodb))

        # Vector DBs
        if result.vectordb:
            db_sections.append(self.vectordb_extractor.to_codetrellis_format(result.vectordb))

        # Redis
        if result.redis:
            db_sections.append(self.redis_extractor.to_codetrellis_format(result.redis))

        # Kafka
        if result.kafka:
            db_sections.append(self.kafka_extractor.to_codetrellis_format(result.kafka))

        if db_sections:
            lines.append("=== DATABASE ===")
            lines.extend(db_sections)
            lines.append("")

        # Data processing sections
        data_sections = []

        # Pandas
        if result.pandas:
            data_sections.append(self.pandas_extractor.to_codetrellis_format(result.pandas))

        # Data pipelines
        if result.pipeline:
            data_sections.append(self.pipeline_extractor.to_codetrellis_format(result.pipeline))

        if data_sections:
            lines.append("=== DATA ===")
            lines.extend(data_sections)
            lines.append("")

        # MLOps sections
        mlops_sections = []

        # MLflow
        if result.mlflow:
            mlops_sections.append(self.mlflow_extractor.to_codetrellis_format(result.mlflow))

        # Config
        if result.config:
            mlops_sections.append(self.config_extractor.to_codetrellis_format(result.config))

        if mlops_sections:
            lines.append("=== MLOPS ===")
            lines.extend(mlops_sections)
            lines.append("")

        # Functions and Classes
        if result.functions or result.classes:
            lines.append("=== CODE ===")
            lines.append(self.function_extractor.to_codetrellis_format({
                'functions': result.functions,
                'classes': result.classes
            }))
            lines.append("")

        # Imports summary
        if result.imports:
            lines.append("=== DEPS ===")
            lines.append(self.dependency_extractor.to_codetrellis_format(result.imports))

        return "\n".join(lines)


class PythonProjectParser:
    """
    Parses an entire Python project directory.

    Similar to how CodeTrellis Scanner works for TypeScript projects,
    this parser recursively scans Python projects and extracts
    all relevant information.
    """

    def __init__(self, exclude_patterns: List[str] = None):
        """
        Initialize the project parser.

        Args:
            exclude_patterns: Glob patterns for files/dirs to exclude
        """
        self.parser = EnhancedPythonParser()
        self.dependency_extractor = DependencyExtractor()

        self.exclude_patterns = exclude_patterns or [
            '__pycache__',
            '.git',
            '.venv',
            'venv',
            'env',
            '.env',
            'node_modules',
            '.mypy_cache',
            '.pytest_cache',
            '*.pyc',
            '.tox',
            'dist',
            'build',
            '*.egg-info',
        ]

    def parse_project(self, project_path: str) -> Dict[str, Any]:
        """
        Parse an entire Python project.

        Args:
            project_path: Root path of the project

        Returns:
            Dict containing all parsed information
        """
        project_path = Path(project_path)

        result = {
            'project_root': str(project_path),
            'files': [],
            'dependencies': [],
            'summary': {
                'total_files': 0,
                'dataclasses': 0,
                'pydantic_models': 0,
                'fastapi_routes': 0,
                'flask_routes': 0,
                'sqlalchemy_models': 0,
                'celery_tasks': 0,
                'functions': 0,
                'classes': 0,
            }
        }

        # Parse requirements.txt if exists
        requirements_path = project_path / 'requirements.txt'
        if requirements_path.exists():
            with open(requirements_path, 'r') as f:
                result['dependencies'] = self.dependency_extractor.extract_requirements(f.read())

        # Parse pyproject.toml if exists
        pyproject_path = project_path / 'pyproject.toml'
        if pyproject_path.exists():
            with open(pyproject_path, 'r') as f:
                toml_deps = self.dependency_extractor.extract_pyproject_dependencies(f.read())
                result['dependencies'].extend(toml_deps)

        # Parse all Python files
        for py_file in self._find_python_files(project_path):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_result = self.parser.parse(content, str(py_file))
                result['files'].append(file_result)

                # Update summary
                result['summary']['total_files'] += 1
                result['summary']['dataclasses'] += len(file_result.dataclasses)
                result['summary']['pydantic_models'] += len(file_result.pydantic_models)
                result['summary']['fastapi_routes'] += len(file_result.fastapi_routes)
                result['summary']['flask_routes'] += len(file_result.flask_routes)
                result['summary']['sqlalchemy_models'] += len(file_result.sqlalchemy_models)
                result['summary']['celery_tasks'] += len(file_result.celery_tasks)
                result['summary']['functions'] += len(file_result.functions)
                result['summary']['classes'] += len(file_result.classes)

            except Exception as e:
                # Log error but continue
                print(f"Error parsing {py_file}: {e}")

        return result

    def _find_python_files(self, root_path: Path) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []

        for path in root_path.rglob('*.py'):
            # Check exclusions
            relative_path = str(path.relative_to(root_path))
            if self._should_exclude(relative_path):
                continue

            python_files.append(path)

        return python_files

    def _should_exclude(self, path: str) -> bool:
        """Check if path should be excluded."""
        for pattern in self.exclude_patterns:
            if pattern in path:
                return True
        return False

    def to_codetrellis_format(self, project_result: Dict[str, Any]) -> str:
        """
        Convert entire project result to CodeTrellis format.

        Args:
            project_result: Result from parse_project()

        Returns:
            CodeTrellis formatted string for entire project
        """
        lines = []

        # Project header
        lines.append("=" * 60)
        lines.append(f"PROJECT: {project_result['project_root']}")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        summary = project_result['summary']
        lines.append("[PROJECT_SUMMARY]")
        lines.append(f"files:{summary['total_files']}")
        lines.append(f"dataclasses:{summary['dataclasses']}")
        lines.append(f"pydantic:{summary['pydantic_models']}")
        lines.append(f"fastapi_routes:{summary['fastapi_routes']}")
        lines.append(f"flask_routes:{summary['flask_routes']}")
        lines.append(f"sqlalchemy:{summary['sqlalchemy_models']}")
        lines.append(f"celery_tasks:{summary['celery_tasks']}")
        lines.append(f"functions:{summary['functions']}")
        lines.append(f"classes:{summary['classes']}")
        lines.append("")

        # Dependencies
        if project_result['dependencies']:
            lines.append("[PROJECT_DEPENDENCIES]")
            for dep in project_result['dependencies']:
                version = f"{dep.version_spec}" if dep.version_spec else ""
                lines.append(f"{dep.name}{version}")
            lines.append("")

        # Individual files
        for file_result in project_result['files']:
            lines.append("-" * 40)
            lines.append(self.parser.to_codetrellis_format(file_result))

        return "\n".join(lines)


# Convenience functions
def parse_python_file(file_path: str) -> PythonParseResult:
    """Parse a single Python file."""
    parser = EnhancedPythonParser()
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return parser.parse(content, file_path)


def parse_python_content(content: str) -> PythonParseResult:
    """Parse Python source code content."""
    parser = EnhancedPythonParser()
    return parser.parse(content)


def parse_python_project(project_path: str) -> Dict[str, Any]:
    """Parse an entire Python project."""
    parser = PythonProjectParser()
    return parser.parse_project(project_path)
