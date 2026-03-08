# CodeTrellis Python Language Support Plan

**Document Version:** 2.0.0
**Created:** 2 February 2026
**Updated:** 2 February 2026
**Author:** AI Assistant + Keshav Chaudhary

---

## 📋 Executive Summary

This document outlines the plan to extend CodeTrellis (Project Self-Awareness System) to provide **comprehensive Python support** that captures the entire Python ecosystem - from web services to AI/ML pipelines, data engineering, and MLOps.

### Vision: Python as a Complete Ecosystem

Python is NOT just a scripting language. In modern systems, Python serves as:

1. **AI/ML Platform** - PyTorch, TensorFlow, JAX, Hugging Face, LangChain
2. **Data Engineering** - Pandas, Spark, Polars, Dask, data pipelines
3. **Database Integration** - MongoDB, Redis, Elasticsearch, PostgreSQL, vector DBs
4. **Workflow Orchestration** - Airflow, Prefect, Dagster, Kubeflow
5. **MLOps & Experiment Tracking** - MLflow, W&B, DVC, Hydra
6. **API Services** - FastAPI, Flask, gRPC, message queues
7. **Distributed Systems** - Celery, Ray, Kafka consumers

### Current State

CodeTrellis v2.0 has support for:

- ✅ Angular components, services, stores, routes
- ✅ TypeScript interfaces, types, generics
- ✅ NestJS schemas, DTOs, controllers, guards
- ✅ Basic Python (dataclasses, Pydantic, FastAPI, Flask)
- ⚠️ No AI/ML pipeline awareness
- ⚠️ No data engineering patterns
- ⚠️ No MLOps/experiment tracking

### Goal

Capture the **complete Python AI/ML lifecycle**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PYTHON AI/ML LIFECYCLE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │   Data   │ → │ Feature  │ → │  Model   │ → │ Training │     │
│  │ Ingestion│   │Engineering│   │ Define  │   │ Pipeline │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│       ↓              ↓              ↓              ↓            │
│  MongoDB,      Pandas,        PyTorch,       Hydra,            │
│  Kafka,        Polars,        TensorFlow,    MLflow,           │
│  S3, APIs      Spark          HuggingFace    W&B               │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │Evaluation│ → │Deployment│ → │ Serving  │ → │Monitoring│     │
│  │& Metrics │   │ & Export │   │  & API   │   │& Logging │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│       ↓              ↓              ↓              ↓            │
│  Metrics,      ONNX,          FastAPI,       Prometheus,       │
│  Benchmarks    TorchServe     Triton         Grafana           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Expanded Python Ecosystem Coverage

### Complete Concept Mapping

| Domain         | Concept          | Python Implementation                | CodeTrellis Section     |
| -------------- | ---------------- | ------------------------------------ | ----------------------- |
| **Types**      | Interface        | `Protocol`, `TypedDict`, type hints  | `[PROTOCOLS]`           |
| **Types**      | Type alias       | `TypeAlias`, `Union`, `Literal`      | `[TYPE_ALIASES]`        |
| **Types**      | Data class       | `@dataclass`, `NamedTuple`           | `[DATACLASSES]`         |
| **Types**      | Enum             | `Enum`, `StrEnum`, `IntEnum`, `Flag` | `[ENUMS]`               |
| **Validation** | Schema/DTO       | Pydantic `BaseModel`                 | `[PYDANTIC_MODELS]`     |
| **API**        | Routes           | FastAPI, Flask, Django REST          | `[ROUTES]`              |
| **API**        | WebSocket        | FastAPI WebSocket, Socket.IO         | `[WEBSOCKET]`           |
| **API**        | gRPC             | gRPC servicers                       | `[GRPC_SERVICES]`       |
| **Database**   | ORM Models       | SQLAlchemy, SQLModel                 | `[ORM_MODELS]`          |
| **Database**   | MongoDB          | PyMongo, Motor, Beanie               | `[MONGODB_MODELS]`      |
| **Database**   | Redis            | redis-py, aioredis                   | `[REDIS_OPERATIONS]`    |
| **Database**   | Vector DB        | Pinecone, Weaviate, ChromaDB, FAISS  | `[VECTOR_STORES]`       |
| **ML/AI**      | Model Definition | PyTorch `nn.Module`, TensorFlow      | `[ML_MODELS]`           |
| **ML/AI**      | Dataset          | PyTorch Dataset, TF Dataset          | `[DATASETS]`            |
| **ML/AI**      | Training Loop    | PyTorch Lightning, Keras fit         | `[TRAINING_PIPELINES]`  |
| **ML/AI**      | Hugging Face     | Transformers, Tokenizers             | `[HF_MODELS]`           |
| **ML/AI**      | LangChain        | Chains, Agents, Tools                | `[LANGCHAIN]`           |
| **Data**       | DataFrame ops    | Pandas, Polars, Dask                 | `[DATA_TRANSFORMS]`     |
| **Data**       | Streaming        | Kafka, RabbitMQ consumers            | `[MESSAGE_CONSUMERS]`   |
| **Pipeline**   | Orchestration    | Airflow DAGs, Prefect flows          | `[WORKFLOW_DAGS]`       |
| **Pipeline**   | Feature Store    | Feast features                       | `[FEATURE_DEFINITIONS]` |
| **MLOps**      | Experiment       | MLflow, W&B runs                     | `[EXPERIMENTS]`         |
| **MLOps**      | Config           | Hydra, OmegaConf                     | `[CONFIG_SCHEMAS]`      |
| **MLOps**      | Model Registry   | MLflow, BentoML                      | `[MODEL_ARTIFACTS]`     |
| **Async**      | Tasks            | Celery, RQ, Dramatiq                 | `[ASYNC_TASKS]`         |
| **Async**      | Distributed      | Ray, Dask distributed                | `[DISTRIBUTED_COMPUTE]` |
| **Testing**    | Test suites      | pytest fixtures, test classes        | `[TEST_FIXTURES]`       |
| **CLI**        | Commands         | Click, Typer, argparse               | `[CLI_COMMANDS]`        |

---

## 🏗️ Architecture: Expanded Python Extractors

Following the existing CodeTrellis architecture (SOLID principles), we organize extractors by domain:

```
codetrellis/extractors/python/
│
├── core/                          # Core Python constructs
│   ├── dataclass_extractor.py     # @dataclass, @dataclass_transform
│   ├── pydantic_extractor.py      # Pydantic BaseModel, BaseSettings
│   ├── typeddict_extractor.py     # TypedDict definitions
│   ├── protocol_extractor.py      # Protocol classes (structural typing)
│   ├── type_alias_extractor.py    # TypeAlias, Union, Literal, Optional
│   ├── enum_extractor.py          # Enum, StrEnum, IntEnum, Flag
│   └── function_extractor.py      # Functions, classes, decorators
│
├── api/                           # API & Web frameworks
│   ├── fastapi_extractor.py       # FastAPI routes, dependencies
│   ├── flask_extractor.py         # Flask routes, blueprints
│   ├── django_extractor.py        # Django views, URLs, DRF
│   ├── grpc_extractor.py          # gRPC servicer classes
│   └── websocket_extractor.py     # WebSocket handlers
│
├── database/                      # Database integrations
│   ├── sqlalchemy_extractor.py    # SQLAlchemy models
│   ├── mongodb_extractor.py       # PyMongo, Motor, Beanie ODM
│   ├── redis_extractor.py         # Redis operations, caching
│   ├── elasticsearch_extractor.py # ES indices, queries
│   └── vector_db_extractor.py     # Pinecone, Weaviate, ChromaDB, FAISS
│
├── ml/                            # Machine Learning
│   ├── pytorch_extractor.py       # nn.Module, DataLoader, training
│   ├── tensorflow_extractor.py    # tf.keras models, layers
│   ├── sklearn_extractor.py       # Scikit-learn pipelines
│   ├── huggingface_extractor.py   # Transformers, Tokenizers, Trainers
│   ├── langchain_extractor.py     # Chains, Agents, Tools, RAG
│   └── dataset_extractor.py       # Dataset definitions, loaders
│
├── data/                          # Data Engineering
│   ├── pandas_extractor.py        # DataFrame operations, transforms
│   ├── spark_extractor.py         # PySpark jobs, transformations
│   ├── polars_extractor.py        # Polars lazy/eager operations
│   └── kafka_extractor.py         # Kafka consumers, producers
│
├── pipeline/                      # Workflow & MLOps
│   ├── airflow_extractor.py       # Airflow DAGs, operators, sensors
│   ├── prefect_extractor.py       # Prefect flows, tasks
│   ├── mlflow_extractor.py        # MLflow experiments, runs, models
│   ├── wandb_extractor.py         # W&B logging, sweeps
│   ├── hydra_extractor.py         # Hydra configs, structured configs
│   └── dvc_extractor.py           # DVC pipelines, params
│
├── async/                         # Async & Distributed
│   ├── celery_extractor.py        # Celery tasks, beat schedules
│   ├── ray_extractor.py           # Ray remote functions, actors
│   └── asyncio_extractor.py       # Asyncio patterns, coroutines
│
└── testing/                       # Testing patterns
    ├── pytest_extractor.py        # pytest fixtures, marks, parametrize
    └── mock_extractor.py          # Mock patterns, patch decorators
```

├── python/ # NEW: Python-specific extractors
│ ├── **init**.py
│ ├── dataclass_extractor.py # @dataclass, @dataclass_transform
│ ├── pydantic_extractor.py # Pydantic BaseModel, BaseSettings
│ ├── typeddict_extractor.py # TypedDict definitions
│ ├── protocol_extractor.py # Protocol classes (structural typing)
│ ├── type_alias_extractor.py # TypeAlias, Union, Literal, Optional
│ ├── enum_extractor.py # Enum, StrEnum, IntEnum, Flag
│ ├── fastapi_extractor.py # FastAPI routes, dependencies
│ ├── flask_extractor.py # Flask routes, blueprints
│ ├── sqlalchemy_extractor.py # SQLAlchemy models
│ ├── celery_extractor.py # Celery tasks
│ ├── grpc_extractor.py # gRPC servicer classes
│ └── dependency_extractor.py # Dependency injection patterns

````

---

## 📐 Phase 1: Core Python Type Extractors (Priority: P0)

### 1.1 DataclassExtractor

**Purpose:** Extract Python `@dataclass` definitions with fields, types, and defaults.

**Patterns to detect:**
```python
from dataclasses import dataclass, field

@dataclass
class User:
    id: int
    name: str
    email: str = ""
    tags: list[str] = field(default_factory=list)

@dataclass(frozen=True, slots=True)
class ImmutableConfig:
    api_key: str
    timeout: int = 30
````

**DataclassInfo:**

```python
@dataclass
class DataclassFieldInfo:
    name: str
    type: str
    default: Optional[str] = None
    default_factory: Optional[str] = None
    required: bool = True

@dataclass
class DataclassInfo:
    name: str
    fields: List[DataclassFieldInfo]
    decorators: List[str]  # frozen, slots, kw_only, etc.
    bases: List[str]
    is_exported: bool = True  # Python doesn't have export, always True
```

**CodeTrellis Output Format:**

```
[DATACLASSES]
User|fields:[id:int!,name:str!,email:str='',tags:list[str]=factory]|options:[]
ImmutableConfig|fields:[api_key:str!,timeout:int=30]|options:[frozen,slots]
```

---

### 1.2 PydanticExtractor

**Purpose:** Extract Pydantic `BaseModel`, `BaseSettings`, validators, and computed fields.

**Patterns to detect:**

```python
from pydantic import BaseModel, Field, field_validator, computed_field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: SecretStr
    age: int | None = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        return v.lower()

    @computed_field
    @property
    def display_name(self) -> str:
        return self.username.title()

    model_config = ConfigDict(from_attributes=True)
```

**PydanticInfo:**

```python
@dataclass
class PydanticFieldInfo:
    name: str
    type: str
    required: bool = True
    default: Optional[str] = None
    field_info: Optional[Dict[str, Any]] = None  # min_length, max_length, etc.

@dataclass
class PydanticValidatorInfo:
    name: str
    fields: List[str]  # Which fields it validates
    mode: str = "after"  # before, after, wrap

@dataclass
class PydanticModelInfo:
    name: str
    fields: List[PydanticFieldInfo]
    validators: List[PydanticValidatorInfo]
    computed_fields: List[str]
    config: Dict[str, Any]
    bases: List[str]  # BaseModel, BaseSettings, etc.
```

**CodeTrellis Output Format:**

```
[PYDANTIC_MODELS]
UserCreate|extends:BaseModel|fields:[username:str!,email:EmailStr!,password:SecretStr!,age:int?]
  validators:[validate_username→username]
  computed:[display_name:str]
  config:[from_attributes=True]
```

---

### 1.3 TypedDictExtractor

**Purpose:** Extract `TypedDict` definitions.

**Patterns to detect:**

```python
from typing import TypedDict, Required, NotRequired

class MovieDict(TypedDict):
    title: str
    year: int
    director: NotRequired[str]

class DetailedMovieDict(MovieDict, total=False):
    rating: float
    genres: list[str]

# Alternative syntax
Point = TypedDict('Point', {'x': int, 'y': int})
```

**CodeTrellis Output Format:**

```
[TYPED_DICTS]
MovieDict|fields:[title:str!,year:int!,director:str?]|total:True
DetailedMovieDict|extends:MovieDict|fields:[rating:float?,genres:list[str]?]|total:False
Point|fields:[x:int!,y:int!]|total:True
```

---

### 1.4 ProtocolExtractor

**Purpose:** Extract Python `Protocol` classes (structural typing).

**Patterns to detect:**

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Comparable(Protocol):
    def __lt__(self, other: Self) -> bool: ...
    def __eq__(self, other: object) -> bool: ...

class Repository(Protocol[T]):
    def get(self, id: int) -> T | None: ...
    def create(self, item: T) -> T: ...
    def update(self, id: int, item: T) -> T: ...
    def delete(self, id: int) -> bool: ...
```

**CodeTrellis Output Format:**

```
[PROTOCOLS]
Comparable|runtime_checkable|methods:[__lt__(other:Self)→bool,__eq__(other:object)→bool]
Repository<T>|methods:[get(id:int)→T|None,create(item:T)→T,update(id:int,item:T)→T,delete(id:int)→bool]
```

---

### 1.5 TypeAliasExtractor

**Purpose:** Extract Python type aliases, Union types, Literal types.

**Patterns to detect:**

```python
from typing import TypeAlias, Union, Literal, Optional

# PEP 613 style
UserId: TypeAlias = int
UserIds: TypeAlias = list[int]

# Union types
Result = str | int | None
MaybeUser = User | None

# Literal types
Status = Literal["pending", "active", "inactive"]
HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]

# Generic type aliases
from typing import TypeVar
T = TypeVar("T")
Response = dict[str, T]
```

**CodeTrellis Output Format:**

```
[TYPE_ALIASES]
UserId=int
UserIds=list[int]
Result=str|int|None|kind:union
MaybeUser=User|None|kind:optional
Status='pending'|'active'|'inactive'|kind:literal
HttpMethod='GET'|'POST'|'PUT'|'DELETE'|kind:literal
T=TypeVar|bound:None
Response<T>=dict[str,T]|kind:generic
```

---

### 1.6 EnumExtractor (Enhanced)

**Purpose:** Extract Python enums with values.

**Patterns to detect:**

```python
from enum import Enum, IntEnum, StrEnum, Flag, auto

class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class Permission(Flag):
    READ = auto()
    WRITE = auto()
    DELETE = auto()
    ADMIN = READ | WRITE | DELETE

class HttpStatus(IntEnum):
    OK = 200
    NOT_FOUND = 404
    INTERNAL_ERROR = 500
```

**CodeTrellis Output Format:**

```
[ENUMS]
UserRole|type:StrEnum|values:[ADMIN='admin',USER='user',GUEST='guest']
Permission|type:Flag|values:[READ=auto,WRITE=auto,DELETE=auto,ADMIN=READ|WRITE|DELETE]
HttpStatus|type:IntEnum|values:[OK=200,NOT_FOUND=404,INTERNAL_ERROR=500]
```

---

## 📐 Phase 2: Framework Extractors (Priority: P1)

### 2.1 FastAPIExtractor

**Purpose:** Extract FastAPI routes, dependencies, request/response models.

**Patterns to detect:**

```python
from fastapi import FastAPI, Depends, HTTPException, Query, Path, Body
from fastapi.security import OAuth2PasswordBearer

app = FastAPI(title="My API", version="1.0.0")
router = APIRouter(prefix="/users", tags=["users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    ...

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int = Path(..., gt=0),
    include_posts: bool = Query(False),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    ...

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate = Body(...),
    db: Session = Depends(get_db)
) -> UserResponse:
    ...
```

**FastAPIInfo:**

```python
@dataclass
class FastAPIParameter:
    name: str
    type: str
    source: str  # path, query, body, header, cookie, depends
    required: bool = True
    default: Optional[str] = None

@dataclass
class FastAPIRoute:
    method: str  # GET, POST, PUT, DELETE, PATCH
    path: str
    handler: str
    parameters: List[FastAPIParameter]
    response_model: Optional[str] = None
    status_code: int = 200
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

@dataclass
class FastAPIRouterInfo:
    prefix: str
    tags: List[str]
    routes: List[FastAPIRoute]
```

**CodeTrellis Output Format:**

```
[FASTAPI_ROUTES]
# /users (tags: users)
GET /users/{user_id} → get_user
  params:[user_id:int@path!,include_posts:bool@query=False]
  deps:[get_current_user]
  response:UserResponse

POST /users/ → create_user (201)
  body:UserCreate
  deps:[get_db]
  response:UserResponse
```

---

### 2.2 FlaskExtractor

**Purpose:** Extract Flask routes, blueprints, request parsers.

**Patterns to detect:**

```python
from flask import Flask, Blueprint, request, jsonify
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id: int):
    ...

@users_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()
    ...

class UserResource(Resource):
    def get(self, user_id: int):
        ...

    def put(self, user_id: int):
        ...

api.add_resource(UserResource, '/api/users/<int:user_id>')
```

**CodeTrellis Output Format:**

```
[FLASK_ROUTES]
# Blueprint: users (prefix: /users)
GET /users/<int:user_id> → get_user
POST /users/ → create_user

# Resource: UserResource
GET /api/users/<int:user_id> → UserResource.get
PUT /api/users/<int:user_id> → UserResource.put
```

---

### 2.3 SQLAlchemyExtractor

**Purpose:** Extract SQLAlchemy model definitions.

**Patterns to detect:**

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# SQLAlchemy 2.0 style
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    posts: Mapped[list["Post"]] = relationship(back_populates="author")

# Legacy style
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))

    author = relationship("User", back_populates="posts")
```

**CodeTrellis Output Format:**

```
[SQLALCHEMY_MODELS]
User|table:users|columns:[id:int!pk,name:str(100)!,email:str(255)!unique+idx,created_at:datetime=utcnow]
  relationships:[posts→Post(back_populates:author)]

Post|table:posts|columns:[id:int!pk,title:str(200)!,author_id:int→users.id]
  relationships:[author→User(back_populates:posts)]
```

---

### 2.4 SQLModelExtractor

**Purpose:** Extract SQLModel definitions (Pydantic + SQLAlchemy).

**Patterns to detect:**

```python
from sqlmodel import SQLModel, Field, Relationship

class UserBase(SQLModel):
    name: str
    email: str = Field(unique=True, index=True)

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    posts: list["Post"] = Relationship(back_populates="author")

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
```

**CodeTrellis Output Format:**

```
[SQLMODEL_MODELS]
UserBase|fields:[name:str!,email:str!unique+idx]
User|extends:UserBase|table:True|fields:[id:int?pk]|relationships:[posts→Post]
UserCreate|extends:UserBase|fields:[password:str!]
UserResponse|extends:UserBase|fields:[id:int!]
```

---

### 2.5 CeleryExtractor

**Purpose:** Extract Celery task definitions.

**Patterns to detect:**

```python
from celery import Celery, shared_task

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3)
def send_email(self, to: str, subject: str, body: str) -> bool:
    ...

@shared_task(name="process_order")
def process_order(order_id: int) -> dict:
    ...

@app.task(queue="high_priority", rate_limit="10/m")
def critical_task(data: dict) -> None:
    ...
```

**CodeTrellis Output Format:**

```
[CELERY_TASKS]
send_email(to:str,subject:str,body:str)→bool|bind:True|max_retries:3
process_order(order_id:int)→dict|name:process_order
critical_task(data:dict)→None|queue:high_priority|rate_limit:10/m
```

---

### 2.6 DependencyExtractor

**Purpose:** Extract dependency injection patterns.

**Patterns to detect:**

```python
# FastAPI Depends
async def get_db() -> AsyncGenerator[Session, None]:
    ...

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    ...

# Class-based dependency injection
class UserService:
    def __init__(
        self,
        repository: UserRepository,
        cache: CacheService,
        logger: Logger = None
    ):
        self.repository = repository
        self.cache = cache
        self.logger = logger or get_logger()

# dependency-injector library
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    db = providers.Singleton(Database, url=config.db_url)
    user_repository = providers.Factory(UserRepository, db=db)
```

**CodeTrellis Output Format:**

```
[DEPENDENCIES]
get_db()→AsyncGenerator[Session,None]|type:factory
get_current_user(db:Session@Depends,token:str@Depends)→User|deps:[get_db,oauth2_scheme]

UserService|deps:[repository:UserRepository!,cache:CacheService!,logger:Logger?]

Container|di_framework:dependency-injector
  providers:[config:Configuration,db:Singleton→Database,user_repository:Factory→UserRepository]
```

---

## 📐 Phase 3: WebSocket & gRPC (Priority: P2)

### 3.1 Python WebSocket Patterns

**Patterns to detect:**

```python
# FastAPI WebSocket
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    user: User = Depends(get_current_user)
):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        await websocket.send_json({"message": "received"})

# Socket.IO (python-socketio)
import socketio
sio = socketio.AsyncServer()

@sio.event
async def connect(sid, environ):
    ...

@sio.on("chat_message")
async def handle_message(sid, data):
    await sio.emit("new_message", data, room=data["room"])
```

**CodeTrellis Output Format:**

```
[WEBSOCKET_EVENTS]
# FastAPI WebSocket
/ws/{room_id}|params:[room_id:str]|deps:[get_current_user]

# Socket.IO
connect|type:event|direction:in
chat_message|type:on|direction:in|handler:handle_message
new_message|type:emit|direction:out
```

---

### 3.2 Python gRPC Patterns

**Patterns to detect:**

```python
import grpc
from generated import user_pb2, user_pb2_grpc

class UserServicer(user_pb2_grpc.UserServiceServicer):
    async def GetUser(
        self,
        request: user_pb2.GetUserRequest,
        context: grpc.aio.ServicerContext
    ) -> user_pb2.User:
        ...

    async def ListUsers(
        self,
        request: user_pb2.ListUsersRequest,
        context: grpc.aio.ServicerContext
    ) -> user_pb2.ListUsersResponse:
        ...

# Registration
server = grpc.aio.server()
user_pb2_grpc.add_UserServiceServicer_to_server(UserServicer(), server)
```

**CodeTrellis Output Format:**

```
[GRPC_SERVICES]
UserServicer|extends:UserServiceServicer
  rpcs:[GetUser(GetUserRequest)→User,ListUsers(ListUsersRequest)→ListUsersResponse]
```

---

## 🎯 Implementation Order

### Sprint 1 (Week 1-2): Core Type Extractors

1. ✅ DataclassExtractor - IMPLEMENTED
2. ✅ PydanticExtractor - IMPLEMENTED
3. ✅ TypedDictExtractor - IMPLEMENTED
4. ✅ ProtocolExtractor - IMPLEMENTED
5. ✅ TypeAliasExtractor - IMPLEMENTED
6. ✅ EnumExtractor (enhanced) - IMPLEMENTED

### Sprint 2 (Week 3-4): Framework Extractors

7. ✅ FastAPIExtractor - IMPLEMENTED
8. ✅ FlaskExtractor - IMPLEMENTED
9. ✅ SQLAlchemyExtractor - IMPLEMENTED
10. ⏳ SQLModelExtractor - Pending (can use SQLAlchemy + Pydantic extractors)

### Sprint 3 (Week 5): Advanced Extractors

11. ✅ CeleryExtractor - IMPLEMENTED
12. ✅ DependencyExtractor - IMPLEMENTED (imports + requirements parsing)
13. ✅ PythonFunctionExtractor - IMPLEMENTED (functions + classes)
14. ⏳ gRPC patterns - Pending

### Sprint 4 (Week 6): Integration & Testing

15. ✅ EnhancedPythonParser - IMPLEMENTED (integrates all extractors)
16. ✅ PythonProjectParser - IMPLEMENTED (project-level scanning)
17. ✅ Unit tests skeleton - IMPLEMENTED
18. ⏳ Integration tests - Pending
19. ⏳ Documentation - In Progress

---

## 📁 Implemented Files

All Python extractors are located in `/tools.codetrellis.codetrellis/extractors/python/`:

| File                      | Description               | Status |
| ------------------------- | ------------------------- | ------ |
| `__init__.py`             | Module exports            | ✅     |
| `dataclass_extractor.py`  | @dataclass parsing        | ✅     |
| `pydantic_extractor.py`   | Pydantic models           | ✅     |
| `typeddict_extractor.py`  | TypedDict definitions     | ✅     |
| `protocol_extractor.py`   | Protocol classes          | ✅     |
| `type_alias_extractor.py` | TypeAlias, Union, Literal | ✅     |
| `enum_extractor.py`       | Enum/StrEnum/IntEnum/Flag | ✅     |
| `fastapi_extractor.py`    | FastAPI routes            | ✅     |
| `flask_extractor.py`      | Flask routes/blueprints   | ✅     |
| `sqlalchemy_extractor.py` | SQLAlchemy models         | ✅     |
| `celery_extractor.py`     | Celery tasks              | ✅     |
| `dependency_extractor.py` | Imports & requirements    | ✅     |
| `function_extractor.py`   | Functions & classes       | ✅     |

Additional files:

- `/tools.codetrellis.codetrellis/python_parser_enhanced.py` - Main parser integrating all extractors
- `/tools.codetrellis/tests/test_python_extractors.py` - Unit test suite

---

## 📦 File Type Detection

Update `ProjectScanner.FILE_TYPES`:

```python
FILE_TYPES = {
    # Existing TypeScript
    ".schema.ts": "schema",
    ".dto.ts": "dto",
    ".controller.ts": "controller",
    ".service.ts": "service",
    # ...existing...

    # NEW: Python patterns
    "models.py": "python_models",
    "schemas.py": "python_schemas",
    "routes.py": "python_routes",
    "api.py": "python_routes",
    "views.py": "python_routes",
    "tasks.py": "celery_tasks",
    "services.py": "python_services",
    "repositories.py": "python_repositories",
    "dependencies.py": "python_dependencies",
    "config.py": "python_config",
    "settings.py": "python_settings",
    "_pb2.py": "grpc_generated",
    "_pb2_grpc.py": "grpc_generated",
}
```

---

## 🔧 Configuration

Add Python-specific configuration to `.codetrellis/config.json`:

```json
{
  "version": "2.0.0",
  "project": "my-python-project",
  "parsers": {
    "typescript": false,
    "python": true,
    "proto": true
  },
  "python": {
    "frameworks": ["fastapi", "sqlalchemy", "pydantic", "celery"],
    "extractDataclasses": true,
    "extractPydantic": true,
    "extractTypedDict": true,
    "extractProtocol": true,
    "extractSQLAlchemy": true,
    "extractFastAPI": true,
    "extractFlask": false,
    "extractCelery": true
  },
  "ignore": [
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "migrations",
    "*_test.py",
    "test_*.py",
    "conftest.py"
  ]
}
```

---

## 📄 Example CodeTrellis Output for Python Project

```
# CodeTrellis Matrix v4.9.0 | my-fastapi-project | 2026-02-02

[PROJECT]
name=my-fastapi-project
type=python-api
stack=fastapi:0.109.0,sqlalchemy:2.0,pydantic:2.6

[PYDANTIC_MODELS]
UserBase|fields:[name:str!,email:EmailStr!]
UserCreate|extends:UserBase|fields:[password:SecretStr!]
UserResponse|extends:UserBase|fields:[id:int!,created_at:datetime!]
UserUpdate|fields:[name:str?,email:EmailStr?]

[SQLALCHEMY_MODELS]
User|table:users|columns:[id:int!pk,name:str(100)!,email:str(255)!unique+idx,hashed_password:str!,created_at:datetime=now]
  relationships:[posts→Post,comments→Comment]

Post|table:posts|columns:[id:int!pk,title:str(200)!,content:text!,author_id:int→users.id]

[ENUMS]
UserRole|type:StrEnum|values:[ADMIN='admin',USER='user',GUEST='guest']
PostStatus|type:Enum|values:[DRAFT,PUBLISHED,ARCHIVED]

[TYPE_ALIASES]
UserId=int
UserIds=list[int]
MaybeUser=User|None|kind:optional

[PROTOCOLS]
Repository<T>|methods:[get(id:int)→T|None,create(item:T)→T,list()→list[T]]

[FASTAPI_ROUTES]
# /users (tags: users)
GET /users/ → list_users|response:list[UserResponse]
GET /users/{user_id} → get_user|params:[user_id:int@path!]|response:UserResponse
POST /users/ → create_user|body:UserCreate|response:UserResponse|status:201
PUT /users/{user_id} → update_user|body:UserUpdate|response:UserResponse
DELETE /users/{user_id} → delete_user|status:204

# /posts (tags: posts)
GET /posts/ → list_posts|query:[skip:int=0,limit:int=10]|response:list[PostResponse]

[DEPENDENCIES]
get_db()→AsyncGenerator[Session]|type:factory
get_current_user|deps:[get_db,oauth2_scheme]→User
get_admin_user|deps:[get_current_user]→User|raises:HTTPException

[CELERY_TASKS]
send_welcome_email(user_id:int)→bool|queue:emails|retry:3
process_upload(file_id:int,options:dict)→dict|queue:processing

[BEST_PRACTICES]
python:3.12|use:typing,Pydantic-v2,async/await,dataclasses|avoid:Any,bare-except
fastapi:0.109|use:Depends,BackgroundTasks,HTTPException|avoid:sync-endpoints
sqlalchemy:2.0|use:Mapped,mapped_column,async-session|avoid:legacy-Query
```

---

## ✅ Implementation Progress

### Phase 1: Core Type Extractors - ✅ COMPLETE

| Extractor          | Status  | File                                        |
| ------------------ | ------- | ------------------------------------------- |
| DataclassExtractor | ✅ Done | `extractors/python/dataclass_extractor.py`  |
| PydanticExtractor  | ✅ Done | `extractors/python/pydantic_extractor.py`   |
| TypedDictExtractor | ✅ Done | `extractors/python/typeddict_extractor.py`  |
| ProtocolExtractor  | ✅ Done | `extractors/python/protocol_extractor.py`   |
| TypeAliasExtractor | ✅ Done | `extractors/python/type_alias_extractor.py` |
| EnumExtractor      | ✅ Done | `extractors/python/enum_extractor.py`       |

### Phase 2: Web Framework Extractors - ✅ COMPLETE

| Extractor           | Status  | File                                        |
| ------------------- | ------- | ------------------------------------------- |
| FastAPIExtractor    | ✅ Done | `extractors/python/fastapi_extractor.py`    |
| FlaskExtractor      | ✅ Done | `extractors/python/flask_extractor.py`      |
| SQLAlchemyExtractor | ✅ Done | `extractors/python/sqlalchemy_extractor.py` |
| CeleryExtractor     | ✅ Done | `extractors/python/celery_extractor.py`     |
| DependencyExtractor | ✅ Done | `extractors/python/dependency_extractor.py` |
| FunctionExtractor   | ✅ Done | `extractors/python/function_extractor.py`   |

### Phase 3: ML/AI Extractors - ✅ COMPLETE

| Extractor            | Status  | File                                            |
| -------------------- | ------- | ----------------------------------------------- |
| PyTorchExtractor     | ✅ Done | `extractors/python/ml/pytorch_extractor.py`     |
| HuggingFaceExtractor | ✅ Done | `extractors/python/ml/huggingface_extractor.py` |
| LangChainExtractor   | ✅ Done | `extractors/python/ml/langchain_extractor.py`   |

### Phase 4: Database Extractors - ✅ COMPLETE

| Extractor         | Status  | File                                               |
| ----------------- | ------- | -------------------------------------------------- |
| MongoDBExtractor  | ✅ Done | `extractors/python/database/mongodb_extractor.py`  |
| VectorDBExtractor | ✅ Done | `extractors/python/database/vectordb_extractor.py` |
| RedisExtractor    | ✅ Done | `extractors/python/database/redis_extractor.py`    |
| KafkaExtractor    | ✅ Done | `extractors/python/database/kafka_extractor.py`    |

### Phase 5: Data Processing Extractors - ✅ COMPLETE

| Extractor             | Status  | File                                           |
| --------------------- | ------- | ---------------------------------------------- |
| PandasExtractor       | ✅ Done | `extractors/python/data/pandas_extractor.py`   |
| DataPipelineExtractor | ✅ Done | `extractors/python/data/pipeline_extractor.py` |

### Phase 6: MLOps Extractors - ✅ COMPLETE

| Extractor       | Status  | File                                          |
| --------------- | ------- | --------------------------------------------- |
| MLflowExtractor | ✅ Done | `extractors/python/mlops/mlflow_extractor.py` |
| ConfigExtractor | ✅ Done | `extractors/python/mlops/config_extractor.py` |

### Integration - ✅ COMPLETE

| Component                 | Status  | File                                     |
| ------------------------- | ------- | ---------------------------------------- |
| EnhancedPythonParser v2.0 | ✅ Done | `python_parser_enhanced.py`              |
| Module `__init__.py`      | ✅ Done | `extractors/python/__init__.py`          |
| ML Module Init            | ✅ Done | `extractors/python/ml/__init__.py`       |
| Database Module Init      | ✅ Done | `extractors/python/database/__init__.py` |
| Data Module Init          | ✅ Done | `extractors/python/data/__init__.py`     |
| MLOps Module Init         | ✅ Done | `extractors/python/mlops/__init__.py`    |

### Summary

**Total Extractors Implemented: 18**

The CodeTrellis Python support now covers the complete AI/ML lifecycle:

- ✅ Core Python types (dataclass, Pydantic, Protocol, Enum, TypedDict, TypeAlias)
- ✅ Web frameworks (FastAPI, Flask, SQLAlchemy, Celery)
- ✅ ML/AI frameworks (PyTorch, HuggingFace, LangChain)
- ✅ Databases (MongoDB, Vector DBs, Redis, Kafka)
- ✅ Data processing (Pandas, Airflow/Prefect/Dagster pipelines)
- ✅ MLOps (MLflow, Hydra/OmegaConf configuration)

---

## ✅ Success Criteria

- [ ] All Python type constructs extracted with full type information
- [ ] FastAPI routes with parameters, dependencies, response models
- [ ] SQLAlchemy/SQLModel schemas with relationships
- [ ] Pydantic models with validators and computed fields
- [ ] Celery tasks with queue and retry configuration
- [ ] Dependency injection patterns mapped
- [ ] 100% test coverage for Python extractors
- [ ] Documentation complete
- [ ] Backward compatible with existing TypeScript/Angular support

---

## 🔗 Related Documents

- [CodeTrellis_V2_IMPLEMENTATION_PLAN.md](./CodeTrellis_V2_IMPLEMENTATION_PLAN.md) - Original v2.0 plan
- [IMPLEMENTATION_PROGRESS.md](./IMPLEMENTATION_PROGRESS.md) - Current progress tracking
