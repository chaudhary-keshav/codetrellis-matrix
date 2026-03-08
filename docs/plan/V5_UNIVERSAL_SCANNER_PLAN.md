# CodeTrellis v5.0 — Universal Scanner Implementation Plan

> **Created:** 10 February 2026
> **Author:** Architecture Review Session
> **Status:** PLAN — Ready for implementation
> **Baseline:** v4.9.0 (76% completion, 47% gotify score, ~35% photoprism score)
> **Target:** 80%+ scan accuracy on ANY public repository

---

## Table of Contents

1. [Current State Audit](#1-current-state-audit)
2. [Root Cause Analysis](#2-root-cause-analysis)
3. [Architecture Changes](#3-architecture-changes)
4. [Implementation Phases](#4-implementation-phases)
5. [Phase 1: Project Discovery Layer](#5-phase-1-project-discovery-layer)
6. [Phase 2: Multi-Identity Project Profile](#6-phase-2-multi-identity-project-profile)
7. [Phase 3: Spec-File Gold Mines](#7-phase-3-spec-file-gold-mines)
8. [Phase 4: Convention & Config Inference](#8-phase-4-convention--config-inference)
9. [Phase 5: Security & DB Architecture Facets](#9-phase-5-security--db-architecture-facets)
10. [Phase 6: Cross-Reference & Sub-Project Scanning](#10-phase-6-cross-reference--sub-project-scanning)
11. [Phase 7: Graceful Degradation](#11-phase-7-graceful-degradation)
12. [Files Changed Per Phase](#12-files-changed-per-phase)
13. [Testing Strategy](#13-testing-strategy)
14. [Risk Assessment](#14-risk-assessment)

---

## 1. Current State Audit

### What Exists Today (from matrix.prompt)

**Languages supported (with dedicated analyzers):**
| Language | Parser | Extractors | Depth |
|----------|--------|------------|-------|
| TypeScript/JS | `ast_parser.py` (TypeScriptASTParser), `typescript.py`, `angular.py` | Interface, Type, Service, Store, Route, Component, JSDoc, WebSocket, HttpApi, Error, Logic | DEEP |
| Python | `python_parser_enhanced.py`, `ast_parser.py` (PythonASTParser) | Pydantic, Dataclass, TypedDict, Protocol, Enum, FastAPI, Flask, SQLAlchemy, Celery, PyTorch, HuggingFace, LangChain, MongoDB, Redis, Kafka, Vector, Pandas, Airflow, Prefect, Dagster, MLflow, Hydra, PydanticSettings | DEEP |
| Go | `go_parser_enhanced.py` | Struct, Interface, TypeAlias, Function, Method, Const, API (Gin/Echo/Chi), gRPC | MEDIUM |
| Proto | `proto.py` (ParsedService, ParsedMessage, ParsedEnum) | gRPC service/message extraction | BASIC |

**Framework-specific extractors:**
| Framework | Extractor | What it extracts |
|-----------|-----------|-----------------|
| Angular | `angular.py` | Components, services, modules, directives, pipes |
| NestJS | `nestjs_extractor.py` | Modules, guards, interceptors, pipes, middleware, gateways |
| FastAPI | `fastapi_extractor.py` | Routes, routers, parameters, dependencies |
| Flask | `flask_extractor.py` | Routes, blueprints |
| Gin/Echo/Chi | `api_extractor.py` (GoAPIExtractor) | HTTP routes, gRPC services |
| Django | ❌ NOT IMPLEMENTED | — |
| React | ❌ NOT IMPLEMENTED | — |
| Vue | ❌ NOT IMPLEMENTED | — |
| Spring Boot | ❌ NOT IMPLEMENTED | — |

**Cross-cutting extractors (language-agnostic):**
| Extractor | File | What |
|-----------|------|------|
| Architecture | `architecture_extractor.py` | Project type, deps, entry points, dirs, patterns, tech stack |
| Business Domain | `business_domain_extractor.py` | Domain category, entities, vocabulary, data flows |
| Readme | `readme_extractor.py` | Title, description, features, sections |
| Config | `config_extractor.py` | package.json, tsconfig, angular.json, environments, Hydra, PydanticSettings |
| Runbook | `runbook_extractor.py` | Commands, CI/CD, env vars, Docker, compose |
| CI/CD | `cicd_extractor.py` | GitHub Actions, GitLab CI, Jenkins, CircleCI, Bitbucket |
| Docker | `docker_extractor.py` | Dockerfiles, compose files |
| Terraform | `terraform_extractor.py` | Providers, resources, variables, outputs, modules |
| Logic | `logic_extractor.py` | Function bodies, control flow, API calls, data transforms |
| Semantic | `semantic_extractor.py` | Hooks, middleware, routes, plugins, lifecycle, CLI commands |
| Error | `error_extractor.py` | Try/catch, error classes, error boundaries |
| Todo | `todo_extractor.py` | TODO, FIXME, HACK, NOTE |
| Progress | `progress_extractor.py` | Completion %, placeholders, blockers |
| Service Map | In `scanner.py` | Inter-service connections |

**Plugin system:**
| Interface | File | Purpose |
|-----------|------|---------|
| `IExtractor` | `plugins/base.py` | `name`, `capabilities`, `can_extract(path, content)`, `extract(path, content)` |
| `ILanguagePlugin` | `plugins/base.py` | `metadata`, `file_extensions`, `can_parse`, `parse`, `get_extractors` |
| `IFrameworkPlugin` | `plugins/base.py` | `metadata`, `language_plugin`, `detect_project`, `get_file_patterns`, `get_extractors`, `get_output_sections` |
| `BaseExtractor` | `plugins/base.py` | ABC with `_create_result()` helper |
| `BaseLanguagePlugin` | `plugins/base.py` | ABC with `can_parse()` default |
| `BaseFrameworkPlugin` | `plugins/base.py` | ABC with `_check_config_file()`, `_check_package_json_dependency()` |

**Key enums:**

- `ProjectType`: ANGULAR, REACT, VUE, NESTJS, EXPRESS, FASTAPI, FLASK, DJANGO, NEXTJS, NUXT, PYTHON_LIBRARY, NODE_LIBRARY, MONOREPO, GO_CLI, GO_LIBRARY, GO_WEB_SERVICE, GO_FRAMEWORK, UNKNOWN
- `DomainCategory`: TRADING, ECOMMERCE, CRM, HEALTHCARE, EDUCATION, SOCIAL, PRODUCTIVITY, IOT, LOGISTICS, ANALYTICS, CONTENT, GAMING, COMMUNICATION, AI_ML, DEVTOOLS, INFRASTRUCTURE, MEDIA_PHOTO, WEB_SERVER, UNKNOWN
- `PluginCapability`: 21 values (INTERFACES through TESTS)
- `ArchPattern`: 16 values (STANDALONE_COMPONENTS through WEBSOCKET)

**Key data structures:**

- `ProjectMatrix` in `scanner.py`: 74+ fields, the central data store
- `ProjectOverview` in `architecture_extractor.py`: name, type, version, description, tech_stack, patterns, entry_points, directories, dependencies
- `RunbookContext` in `runbook_extractor.py`: commands, pipelines, env_variables, docker, compose
- `BusinessDomainContext` in `business_domain_extractor.py`: domain_category, entities, vocabulary, data_flows

**Scanner execution order (`scanner.py` → `scan()`):**

1. Walk files → `_process_file()` → `_parse_file()` (per-file, type-based dispatch)
2. `_extract_dependencies()` (package.json)
3. `_detect_services()` (NestJS modules)
4. `_extract_context()` (readme, config, jsdoc)
5. `_extract_errors_and_todos()`
6. `_extract_progress_and_overview()`
7. `_extract_logic()`
8. `_extract_runbook()`
9. `_tag_source_services()` + `_build_service_map()`
10. `_extract_infrastructure()` (Docker, Terraform, CI/CD)
11. `_extract_nestjs()`
12. `_extract_semantics()`
13. `_resolve_cross_file_route_prefixes()`
14. `_build_directory_summary()`

---

## 2. Root Cause Analysis

### Why gotify scored 47% and photoprism ~35%

**ROOT CAUSE 1: Single ProjectType classification**

- `_detect_project_type()` returns ONE enum value
- gotify = "Go Web Service" (ignores React/TS frontend entirely)
- photoprism = "Go Web Service" (ignores Vue, TensorFlow, OIDC, 217 env vars)
- CodeTrellis itself = "Python Library" (ignores LSP/TypeScript, Angular test fixtures)
- **Location:** `architecture_extractor.py:488-608`

**ROOT CAUSE 2: `_build_tech_stack()` only knows JS dependencies**

- `key_deps` dict only contains `@ngrx/*`, `rxjs`, `tailwindcss`, `socket.io-client`, `mongoose`, etc.
- Zero Go framework names (gin, gorm, gorilla/websocket)
- Zero Python ML names (tensorflow, pytorch, transformers)
- Stack output = just the ProjectType value ("Go Web Service")
- **Location:** `architecture_extractor.py:896-940`

**ROOT CAUSE 3: `_extract_from_package_json()` only reads ROOT package.json**

- gotify has `ui/package.json` with React — never read
- photoprism has `frontend/package.json` with Vue — never read
- **Location:** `architecture_extractor.py:408-445`

**ROOT CAUSE 4: No spec file parsing**

- gotify has `docs/spec.json` (Swagger 2.0, 44 endpoints) — never parsed
- photoprism has Swagger annotations in Go source — never structured
- **Location:** No extractor exists

**ROOT CAUSE 5: Business domain extractor doesn't read README content**

- `_detect_domain_category()` uses keyword-frequency heuristics on struct/function names
- photoprism's `frontend/package.json` says `"description": "AI-Powered Photos App"` — never read
- CodeTrellis has test fixtures with trading terms → classified as "Trading/Finance"
- **Location:** `business_domain_extractor.py`

**ROOT CAUSE 6: Config detection misses Go/Python config library conventions**

- configor with `ENVPrefix: "GOTIFY"` → 0 env vars detected (should be 30+)
- urfave/cli with `EnvVars: EnvVars("X")` → 0 env vars detected (should be 217+)
- pydantic BaseSettings with `env_prefix` → exists in `config_extractor.py` but only for Python
- **Location:** `config_extractor.py` (Python-only), `runbook_extractor.py` (basic env grep)

**ROOT CAUSE 7: Go route extraction gaps**

- `g.Match()`, `g.StaticFS()`, `g.Static()` not recognized
- Same-file `.Group("/prefix")` doesn't propagate prefix to child routes
- `router.Any()` not recognized (health endpoints)
- `router.Handle(MethodPropfind, ...)` not recognized (WebDAV)
- **Location:** `extractors/go/api_extractor.py`

**ROOT CAUSE 8: Middleware detection only looks for `.Use()`**

- `router.Group(path, middleware)` syntax (middleware as Group argument) not detected
- **Location:** `semantic_extractor.py`

---

## 3. Architecture Changes

### No Pipeline Refactor Needed

After re-reading the codebase, the current `scanner.py` → `scan()` method already IS a sequential pipeline. We do NOT need to build a new pipeline framework. Instead, we:

1. **Add a discovery pre-pass** before the file walk (cheap, glob-based)
2. **Replace `ProjectType` enum with `ProjectProfile` dataclass** (additive, not exclusive)
3. **Add new extractors** following the existing `IExtractor`/`BaseExtractor` pattern
4. **Fix existing extractors** (Go routes, business domain, tech stack)
5. **Enhance `_extract_context()`** to find sub-project package.json files

### Design Principles

1. **Every new extractor follows `BaseExtractor` pattern** from `plugins/base.py`
2. **Every new dataclass follows existing conventions** — `to_dict()`, `to_codetrellis_format()`
3. **No breaking changes to `ProjectMatrix`** — only add fields
4. **No breaking changes to `compressor.py`** — only add new `_compress_*` methods
5. **Tests use existing `conftest.py` patterns**

---

## 4. Implementation Phases

| Phase     | Name                                   | Files New       | Files Modified   | Est. Effort  | Impact  |
| --------- | -------------------------------------- | --------------- | ---------------- | ------------ | ------- |
| 1         | Project Discovery Layer                | 1               | 2                | 2 days       | HIGH    |
| 2         | Multi-Identity Project Profile         | 0               | 3                | 2 days       | HIGH    |
| 3         | Spec-File Gold Mines                   | 2               | 3                | 3 days       | HIGHEST |
| 4         | Convention & Config Inference          | 2               | 2                | 3 days       | HIGH    |
| 5         | Security & DB Architecture Facets      | 2               | 2                | 3 days       | MEDIUM  |
| 6         | Cross-Reference & Sub-Project Scanning | 1               | 3                | 2 days       | HIGH    |
| 7         | Graceful Degradation                   | 1               | 2                | 2 days       | MEDIUM  |
| **Total** |                                        | **9 new files** | **~10 modified** | **~17 days** |         |

---

## 5. Phase 1: Project Discovery Layer

### Goal

Before any file parsing, run a lightweight discovery pass that finds everything of interest: sub-projects, spec files, config templates, manifest files.

### New File: `codetrellis/extractors/discovery_extractor.py`

```python
# New dataclasses needed:

@dataclass
class SubProjectInfo:
    """An embedded sub-project discovered inside the main project."""
    path: str                    # Relative path (e.g., "ui/", "frontend/")
    manifest_file: str           # e.g., "package.json", "go.mod", "Cargo.toml"
    languages: List[str]         # Detected languages in this sub-project
    name: Optional[str]          # From manifest (e.g., package.json "name")
    description: Optional[str]   # From manifest
    framework_hints: List[str]   # e.g., ["react", "mobx"] from deps

@dataclass
class SpecFileInfo:
    """A structured specification file found in the project."""
    path: str                    # Relative path
    spec_type: str               # "openapi-2.0", "openapi-3.0", "graphql-schema",
                                 # "protobuf", "avro", "thrift", "json-schema"
    format: str                  # "json", "yaml", "proto", "graphql"

@dataclass
class ConfigTemplateInfo:
    """A configuration template file found in the project."""
    path: str                    # Relative path
    template_type: str           # "env-example", "yaml-example", "toml-example",
                                 # "ini-example", "json-example"
    format: str                  # "env", "yaml", "toml", "ini", "json"

@dataclass
class LanguageBreakdown:
    """Language presence detected in the project."""
    name: str                    # "go", "python", "typescript", "java", "rust"
    file_count: int              # Number of files with this language's extensions
    percentage: float            # % of total code files
    root_dirs: List[str]         # Which directories contain this language
    manifest: Optional[str]      # "go.mod", "pyproject.toml", "Cargo.toml"

@dataclass
class ProjectDiscoveryResult:
    """Result of the discovery pre-pass."""
    # Language breakdown (plural — NOT one ProjectType)
    languages: List[LanguageBreakdown]
    primary_language: str        # The dominant language

    # Sub-projects found
    sub_projects: List[SubProjectInfo]

    # Spec files found (gold mines)
    spec_files: List[SpecFileInfo]

    # Config templates found
    config_templates: List[ConfigTemplateInfo]

    # Manifest files found (already partially done by architecture_extractor)
    manifest_files: List[str]    # ["go.mod", "package.json", "pyproject.toml"]

    # README info (first 500 chars for domain classification)
    readme_summary: Optional[str]
    readme_description: Optional[str]  # Extracted description/subtitle

    # Package description from manifest
    package_description: Optional[str]

    def to_dict(self) -> Dict[str, Any]: ...
```

### Class: `DiscoveryExtractor`

**What it does (all cheap glob/stat operations, no file parsing):**

```python
class DiscoveryExtractor:
    """Lightweight pre-pass discovery — runs BEFORE all other extractors."""

    # Extension → language mapping
    LANGUAGE_MAP = {
        '.go': 'go', '.py': 'python', '.ts': 'typescript', '.tsx': 'typescript',
        '.js': 'javascript', '.jsx': 'javascript', '.rs': 'rust',
        '.java': 'java', '.kt': 'kotlin', '.scala': 'scala',
        '.rb': 'ruby', '.ex': 'elixir', '.exs': 'elixir',
        '.swift': 'swift', '.dart': 'dart', '.cs': 'csharp',
        '.lua': 'lua', '.zig': 'zig', '.nim': 'nim',
        '.php': 'php', '.r': 'r', '.R': 'r',
        '.cpp': 'cpp', '.c': 'c', '.h': 'c',
    }

    # Manifest files that indicate a sub-project
    MANIFEST_FILES = [
        'package.json', 'go.mod', 'Cargo.toml', 'pyproject.toml',
        'setup.py', 'pom.xml', 'build.gradle', 'build.gradle.kts',
        'Gemfile', 'mix.exs', 'Package.swift', 'pubspec.yaml',
        'composer.json', '*.csproj', '*.sln',
    ]

    # Spec file patterns
    SPEC_PATTERNS = {
        'openapi': ['swagger.json', 'swagger.yaml', 'swagger.yml',
                     'openapi.json', 'openapi.yaml', 'openapi.yml',
                     'spec.json', 'spec.yaml', 'api-spec.*'],
        'graphql-schema': ['schema.graphql', 'schema.gql', '*.graphqls'],
        'protobuf': ['*.proto'],
        'avro': ['*.avsc'],
        'thrift': ['*.thrift'],
        'json-schema': ['*schema*.json'],  # heuristic, filtered later
    }

    # Config template patterns
    CONFIG_TEMPLATE_PATTERNS = [
        '.env.example', '.env.sample', '.env.template', '.env.dist',
        'config.example.*', 'config.sample.*',
        '*.example.yml', '*.example.yaml', '*.example.toml',
        '*.sample.yml', '*.sample.yaml',
        'application.yml.example', 'application.yaml.example',
    ]

    def discover(self, root_path: Path) -> ProjectDiscoveryResult:
        """Run discovery pre-pass. Must be fast (<1 second for most repos)."""
        ...

    def _count_languages(self, root: Path) -> List[LanguageBreakdown]: ...
    def _find_sub_projects(self, root: Path) -> List[SubProjectInfo]: ...
    def _find_spec_files(self, root: Path) -> List[SpecFileInfo]: ...
    def _find_config_templates(self, root: Path) -> List[ConfigTemplateInfo]: ...
    def _extract_readme_summary(self, root: Path) -> Tuple[Optional[str], Optional[str]]: ...
    def _extract_package_description(self, root: Path, sub_projects: List[SubProjectInfo]) -> Optional[str]: ...
```

### Changes to Existing Files

**`scanner.py`** — Add discovery call at the start of `scan()`:

```python
def scan(self, root_path: str) -> ProjectMatrix:
    root = Path(root_path).resolve()

    # NEW: Phase 1 — Discovery pre-pass
    from codetrellis.extractors.discovery_extractor import DiscoveryExtractor
    discovery = DiscoveryExtractor()
    discovery_result = discovery.discover(root)

    # Store discovery in matrix for use by other extractors
    matrix.discovery = discovery_result.to_dict()  # New field on ProjectMatrix

    # ... rest of existing scan logic ...
```

**`scanner.py` (ProjectMatrix)** — Add field:

```python
# v5.0: Discovery pre-pass results
discovery: Optional[Dict] = field(default_factory=dict)
```

### Step-by-Step Implementation

| Step | Task                                       | Details                                                                                                               |
| ---- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| 1.1  | Create `discovery_extractor.py`            | All dataclasses + `DiscoveryExtractor` class                                                                          |
| 1.2  | Implement `_count_languages()`             | Walk dirs, count extensions, skip ignored dirs. Use same `_should_ignore()` logic                                     |
| 1.3  | Implement `_find_sub_projects()`           | Glob for manifest files in subdirs (not root). Read name/description from each. Extract dep names for framework hints |
| 1.4  | Implement `_find_spec_files()`             | Glob for spec patterns. For JSON files, peek at first 200 bytes to verify `"swagger"` or `"openapi"` key exists       |
| 1.5  | Implement `_find_config_templates()`       | Glob for `.example`, `.sample`, `.template` patterns                                                                  |
| 1.6  | Implement `_extract_readme_summary()`      | Read `README.md` first 500 chars. Extract first paragraph after `# Title`                                             |
| 1.7  | Implement `_extract_package_description()` | Read `description` field from root + sub-project manifests                                                            |
| 1.8  | Wire into `scanner.py` `scan()`            | Call discovery before file walk. Store result in matrix                                                               |
| 1.9  | Add `discovery` field to `ProjectMatrix`   | New optional Dict field                                                                                               |
| 1.10 | Write unit tests                           | Test discovery on CodeTrellis repo itself + mock repos                                                                |

---

## 6. Phase 2: Multi-Identity Project Profile

### Goal

Replace the single `ProjectType` enum classification with a multi-dimensional `ProjectProfile` that captures ALL languages, frameworks, and facets.

### Changes to `architecture_extractor.py`

**New dataclass (add to existing file):**

```python
@dataclass
class ProjectProfile:
    """Multi-dimensional project identity — replaces single ProjectType."""
    # Primary classification (backward compatible)
    primary_type: ProjectType

    # All languages detected (from discovery)
    languages: List[Dict[str, Any]]  # [{name, percentage, file_count}]

    # All frameworks per language (from discovery + dep analysis)
    frameworks: Dict[str, List[str]]  # {"go": ["gin", "gorm"], "typescript": ["react"]}

    # Facets/concerns present
    facets: List[str]  # ["rest-api", "websocket", "database", "auth", "docker", "ml"]

    # Sub-projects
    sub_projects: List[Dict[str, Any]]  # From discovery

    # Rich stack summary (human-readable)
    stack_summary: str  # "Go + React/TS + Gin + GORM + WebSocket + Multi-DB"

    def to_dict(self) -> Dict[str, Any]: ...
```

### Changes to `_build_tech_stack()`

**Before:** Only knew JS deps. Returned `["Go Web Service"]`.

**After:** Uses discovery result to build rich stack. Add Go, Python, Rust, Java dep maps:

```python
GO_FRAMEWORK_NAMES = {
    'gin-gonic/gin': 'Gin', 'labstack/echo': 'Echo', 'go-chi/chi': 'Chi',
    'gorilla/mux': 'Gorilla Mux', 'gofiber/fiber': 'Fiber',
    'gorm.io/gorm': 'GORM', 'jinzhu/gorm': 'GORM',
    'gorilla/websocket': 'WebSocket', 'go-redis': 'Redis',
    'jinzhu/configor': 'Configor', 'spf13/viper': 'Viper',
    'urfave/cli': 'CLI', 'spf13/cobra': 'Cobra',
    'golang-jwt/jwt': 'JWT',
    'tensorflow/tensorflow': 'TensorFlow',
}

PYTHON_FRAMEWORK_NAMES = {
    'fastapi': 'FastAPI', 'flask': 'Flask', 'django': 'Django',
    'pytorch': 'PyTorch', 'torch': 'PyTorch', 'tensorflow': 'TensorFlow',
    'transformers': 'HuggingFace', 'langchain': 'LangChain',
    'celery': 'Celery', 'sqlalchemy': 'SQLAlchemy',
    'pydantic': 'Pydantic', 'pandas': 'Pandas',
}
```

### Changes to `_detect_project_type()`

Keep existing logic for backward compatibility, but also build `ProjectProfile`:

```python
def _build_project_profile(self, overview, discovery_result) -> ProjectProfile:
    """Build multi-dimensional project profile from overview + discovery."""
    ...
```

### Changes to `ProjectOverview.to_codetrellis_format()`

**Before output:** `name:gotify-server|type:Go Web Service|stack:Go Web Service`
**After output:** `name:gotify-server|type:Go Web Service|stack:Go + React/TS + Gin + GORM + WebSocket + Configor|languages:Go(66%),TypeScript(32%)|facets:rest-api,websocket,database,auth,docker,ci-cd,plugin-system`

### Step-by-Step Implementation

| Step | Task                                                          | Details                                                                                                                                                                                   |
| ---- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1  | Add `ProjectProfile` dataclass to `architecture_extractor.py` | With `to_dict()` and `to_codetrellis_format()`                                                                                                                                            |
| 2.2  | Add `GO_FRAMEWORK_NAMES`, `PYTHON_FRAMEWORK_NAMES` dicts      | To `architecture_extractor.py` class                                                                                                                                                      |
| 2.3  | Implement `_build_project_profile()`                          | Uses discovery languages + dep analysis                                                                                                                                                   |
| 2.4  | Enhance `_build_tech_stack()`                                 | Use Go deps from `go.mod`, Python deps from `requirements.txt`/`pyproject.toml`, sub-project deps from discovered `package.json` files                                                    |
| 2.5  | Detect facets                                                 | Based on: has API routes = "rest-api", has Docker = "docker", has CI = "ci-cd", has WebSocket dep = "websocket", has DB dep = "database", has auth middleware = "auth", has ML dep = "ml" |
| 2.6  | Update `ProjectOverview.to_codetrellis_format()`              | Include languages, frameworks, facets in output                                                                                                                                           |
| 2.7  | Add `profile` field to `ProjectMatrix`                        | `project_profile: Optional[Dict]`                                                                                                                                                         |
| 2.8  | Update `compressor.py` `_compress_overview()`                 | Include new profile data in `[OVERVIEW]` section                                                                                                                                          |
| 2.9  | Write tests                                                   | Verify gotify-like project gets "Go + React/TS + Gin + GORM"                                                                                                                              |

---

## 7. Phase 3: Spec-File Gold Mines

### Goal

Parse OpenAPI/Swagger specs and other structured API definitions to get 100% API coverage without any code parsing.

### New File: `codetrellis/extractors/openapi_extractor.py`

```python
@dataclass
class OpenAPIEndpoint:
    method: str          # GET, POST, PUT, DELETE, PATCH
    path: str            # /api/v1/users/{id}
    summary: Optional[str]
    description: Optional[str]
    tags: List[str]
    parameters: List[Dict[str, Any]]  # [{name, in, type, required}]
    request_body: Optional[str]       # Schema reference
    responses: Dict[str, str]         # {"200": "UserResponse", "404": "Error"}
    security: List[str]               # ["bearerAuth", "apiKey"]
    operation_id: Optional[str]

@dataclass
class OpenAPISecurityScheme:
    name: str            # "bearerAuth", "apiKey"
    scheme_type: str     # "http", "apiKey", "oauth2", "openIdConnect"
    scheme: Optional[str]  # "bearer"
    bearer_format: Optional[str]  # "JWT"
    location: Optional[str]  # "header", "query", "cookie"
    header_name: Optional[str]  # "X-Gotify-Key"

@dataclass
class OpenAPIModel:
    name: str
    properties: List[Dict[str, Any]]  # [{name, type, required}]
    description: Optional[str]

@dataclass
class OpenAPIInfo:
    file_path: str
    spec_version: str    # "2.0" or "3.0.x"
    title: str
    description: Optional[str]
    version: str
    endpoints: List[OpenAPIEndpoint]
    models: List[OpenAPIModel]
    security_schemes: List[OpenAPISecurityScheme]
    tags: List[Dict[str, str]]  # [{name, description}]
    servers: List[str]   # Base URLs

    def to_dict(self) -> Dict[str, Any]: ...
    def to_codetrellis_format(self) -> str: ...

class OpenAPIExtractor:
    """Parse OpenAPI 2.0 (Swagger) and 3.0 specification files."""

    def can_extract(self, file_path: Path) -> bool:
        """Check if file is an OpenAPI spec."""
        ...

    def extract(self, file_path: Path) -> Optional[OpenAPIInfo]:
        """Parse an OpenAPI spec file (JSON or YAML)."""
        ...

    def _parse_swagger_2(self, data: dict, file_path: str) -> OpenAPIInfo: ...
    def _parse_openapi_3(self, data: dict, file_path: str) -> OpenAPIInfo: ...
    def _extract_endpoints(self, paths: dict, spec_version: str) -> List[OpenAPIEndpoint]: ...
    def _extract_models(self, definitions: dict) -> List[OpenAPIModel]: ...
    def _extract_security_schemes(self, data: dict, spec_version: str) -> List[OpenAPISecurityScheme]: ...
```

### New File: `codetrellis/extractors/graphql_schema_extractor.py`

```python
@dataclass
class GraphQLType:
    name: str
    kind: str  # "type", "input", "enum", "interface", "union", "scalar"
    fields: List[Dict[str, Any]]
    description: Optional[str]

@dataclass
class GraphQLQuery:
    name: str
    arguments: List[Dict[str, str]]
    return_type: str
    description: Optional[str]

@dataclass
class GraphQLSchemaInfo:
    file_path: str
    types: List[GraphQLType]
    queries: List[GraphQLQuery]
    mutations: List[GraphQLQuery]
    subscriptions: List[GraphQLQuery]

    def to_dict(self) -> Dict[str, Any]: ...
    def to_codetrellis_format(self) -> str: ...

class GraphQLSchemaExtractor:
    """Parse .graphql/.gql schema files."""
    ...
```

### Changes to Existing Files

**`scanner.py`** — Add spec extraction step:

```python
# After discovery, before file walk:
# Phase 3: Extract from spec files found by discovery
self._extract_spec_files(root, matrix, discovery_result)
```

**`scanner.py` (ProjectMatrix)** — Add fields:

```python
# v5.0: Spec file extractions
openapi_specs: List[Dict] = field(default_factory=list)
graphql_schemas: List[Dict] = field(default_factory=list)
```

**`compressor.py`** — Add new output sections:

```python
# New section: [OPENAPI]
def _compress_openapi(self, specs: List[Dict]) -> str: ...

# New section: [GRAPHQL_SCHEMA]
def _compress_graphql_schema(self, schemas: List[Dict]) -> str: ...
```

### Step-by-Step Implementation

| Step | Task                                                      | Details                                                                        |
| ---- | --------------------------------------------------------- | ------------------------------------------------------------------------------ |
| 3.1  | Create `openapi_extractor.py`                             | All dataclasses + `OpenAPIExtractor` class                                     |
| 3.2  | Implement Swagger 2.0 parser                              | Parse `paths`, `definitions`, `securityDefinitions`. JSON only first           |
| 3.3  | Implement OpenAPI 3.0 parser                              | Parse `paths`, `components/schemas`, `components/securitySchemes`. JSON + YAML |
| 3.4  | Add YAML support                                          | Use `pyyaml` (already in requirements.txt) for `.yaml`/`.yml` specs            |
| 3.5  | Create `graphql_schema_extractor.py`                      | Parse `.graphql` schema files (type, input, enum, query, mutation)             |
| 3.6  | Wire into `scanner.py`                                    | Use discovery `spec_files` to find and parse specs                             |
| 3.7  | Add `openapi_specs`, `graphql_schemas` to `ProjectMatrix` | New list fields                                                                |
| 3.8  | Add `_compress_openapi()` to `compressor.py`              | Output as `[OPENAPI]` section                                                  |
| 3.9  | Add `_compress_graphql_schema()` to `compressor.py`       | Output as `[GRAPHQL_SCHEMA]` section                                           |
| 3.10 | Write tests                                               | Test with gotify's `docs/spec.json`, test with sample OpenAPI 3.0              |

### Expected Impact

- gotify Swagger/OpenAPI: 5% → **95%**
- gotify Routes: 55% → **85%** (spec gives complete API surface)
- gotify Auth: 40% → **65%** (spec documents security schemes)

---

## 8. Phase 4: Convention & Config Inference

### Goal

Parse config template files (`.env.example`, `config.example.yml`) and understand config library conventions (configor ENVPrefix, viper, pydantic-settings).

### New File: `codetrellis/extractors/config_template_extractor.py`

```python
@dataclass
class ConfigField:
    name: str                    # Field name or env var name
    default: Optional[str]       # Default value
    comment: Optional[str]       # Inline comment/description
    section: Optional[str]       # Section/group name
    field_type: Optional[str]    # Inferred type (string, int, bool, url)
    required: bool = False       # Whether it has no default

@dataclass
class ConfigTemplateResult:
    file_path: str
    format: str                  # "env", "yaml", "toml", "ini"
    fields: List[ConfigField]
    sections: List[str]          # Top-level sections
    total_fields: int

    def to_dict(self) -> Dict[str, Any]: ...
    def to_codetrellis_format(self) -> str: ...

class ConfigTemplateExtractor:
    """Parse .env.example, config.example.yml, etc."""

    def extract(self, file_path: Path) -> Optional[ConfigTemplateResult]: ...
    def _parse_env_file(self, content: str, file_path: str) -> ConfigTemplateResult: ...
    def _parse_yaml_config(self, content: str, file_path: str) -> ConfigTemplateResult: ...
    def _parse_toml_config(self, content: str, file_path: str) -> ConfigTemplateResult: ...
```

### New File: `codetrellis/extractors/env_inference_extractor.py`

```python
@dataclass
class InferredEnvVar:
    name: str                    # e.g., "GOTIFY_SERVER_PORT"
    source: str                  # "configor-prefix", "viper", "pydantic-settings", "cli-flag", "source-code"
    config_field: Optional[str]  # Original field name (e.g., "Server.Port")
    default: Optional[str]       # Default value if detected
    field_type: Optional[str]    # Inferred type

@dataclass
class EnvInferenceResult:
    env_vars: List[InferredEnvVar]
    env_prefix: Optional[str]    # e.g., "GOTIFY", "PHOTOPRISM"
    config_library: Optional[str]  # e.g., "configor", "viper", "pydantic-settings"
    config_struct: Optional[str]   # e.g., "Configuration" (the Go struct name)

    def to_dict(self) -> Dict[str, Any]: ...
    def to_codetrellis_format(self) -> str: ...

class EnvInferenceExtractor:
    """Infer environment variables from config library conventions."""

    def extract_from_go(self, root: Path, go_structs: List[Dict]) -> Optional[EnvInferenceResult]:
        """Detect configor/viper patterns in Go code and infer env vars from struct fields."""
        # 1. Search for configor.New(&configor.Config{ENVPrefix: "X"}) pattern
        # 2. Find the struct type passed to configor.Load()
        # 3. Walk struct fields recursively, building ENVPREFIX_SECTION_FIELD names
        ...

    def extract_from_python(self, root: Path) -> Optional[EnvInferenceResult]:
        """Detect pydantic BaseSettings env_prefix."""
        # Already partially done in config_extractor.py — enhance
        ...

    def extract_from_cli_flags(self, root: Path) -> Optional[EnvInferenceResult]:
        """Detect urfave/cli flag EnvVars patterns."""
        # Search for cli.StringFlag{Name: "x", EnvVars: EnvVars("Y")} patterns
        ...

    def _walk_go_struct_fields(self, struct_name: str, structs: Dict, prefix: str) -> List[InferredEnvVar]:
        """Recursively walk Go struct fields to build env var names."""
        ...
```

### Changes to Existing Files

**`scanner.py`** — Add config extraction step:

```python
# After extract_infrastructure:
self._extract_config_templates(root, matrix, discovery_result)
self._extract_inferred_env_vars(root, matrix)
```

**`scanner.py` (ProjectMatrix)** — Add fields:

```python
# v5.0: Configuration inference
config_templates: List[Dict] = field(default_factory=list)
inferred_env_vars: Optional[Dict] = None
```

### Step-by-Step Implementation

| Step | Task                                    | Details                                                                                    |
| ---- | --------------------------------------- | ------------------------------------------------------------------------------------------ |
| 4.1  | Create `config_template_extractor.py`   | Dataclasses + parser                                                                       |
| 4.2  | Implement `.env` parser                 | Parse `KEY=value # comment` lines. Handle sections via `# --- Section ---` comments        |
| 4.3  | Implement YAML config parser            | Parse YAML, flatten to dotted keys, extract comments (use pyyaml)                          |
| 4.4  | Implement TOML config parser            | Parse TOML structure (regex-based, like existing `_extract_from_pyproject`)                |
| 4.5  | Create `env_inference_extractor.py`     | Dataclasses + extractor                                                                    |
| 4.6  | Implement Go configor pattern detection | Regex for `configor.New(&configor.Config{ENVPrefix:` → extract prefix → walk struct fields |
| 4.7  | Implement Go viper pattern detection    | Regex for `viper.SetEnvPrefix("X")`                                                        |
| 4.8  | Implement urfave/cli flag detection     | Regex for `cli.StringFlag{...EnvVars:` patterns                                            |
| 4.9  | Wire into `scanner.py`                  | Call after infrastructure extraction                                                       |
| 4.10 | Add output sections to `compressor.py`  | `[CONFIG_SCHEMA]`, enhanced `[RUNBOOK]` env vars                                           |
| 4.11 | Write tests                             | Test with gotify-like configor pattern, test with .env.example                             |

### Expected Impact

- gotify Configuration: 35% → **85%**
- gotify Env Vars: 30% → **80%**
- photoprism Env Vars: 10% → **70%** (urfave/cli pattern)

---

## 9. Phase 5: Security & DB Architecture Facets

### Goal

Add cross-cutting extractors that detect authentication patterns and database architecture regardless of language.

### New File: `codetrellis/extractors/security_extractor.py`

```python
@dataclass
class AuthScheme:
    name: str                    # "bearer-token", "api-key", "basic-auth", "oauth2", "oidc"
    source: str                  # Where detected: "middleware", "openapi-spec", "code-pattern"
    details: Dict[str, Any]      # {header: "X-Gotify-Key"}, {endpoints: ["/oauth/token"]}

@dataclass
class RBACRole:
    name: str                    # "admin", "user", "viewer"
    source_file: str
    permissions: List[str]       # If detectable

@dataclass
class SecurityModel:
    auth_schemes: List[AuthScheme]
    roles: List[RBACRole]
    password_hashing: Optional[str]   # "bcrypt", "argon2", "scrypt"
    session_management: Optional[str]  # "server-side", "jwt", "cookie"
    cors_configured: bool
    rate_limiting: bool

    def to_dict(self) -> Dict[str, Any]: ...
    def to_codetrellis_format(self) -> str: ...

class SecurityExtractor:
    """Detect security/auth patterns across languages."""

    def extract(self, root: Path, matrix_data: Dict) -> Optional[SecurityModel]:
        """
        Analyze project for security patterns.
        Uses: openapi specs (if available), middleware detection, code patterns.
        """
        ...

    # Detection patterns (regex-based, language-aware):
    def _detect_token_extraction(self, content: str, lang: str) -> List[AuthScheme]: ...
    def _detect_password_hashing(self, content: str) -> Optional[str]: ...
    def _detect_rbac_patterns(self, content: str, lang: str) -> List[RBACRole]: ...
    def _detect_oauth_oidc(self, content: str) -> List[AuthScheme]: ...
    def _from_openapi_security(self, openapi_specs: List[Dict]) -> List[AuthScheme]: ...
```

### New File: `codetrellis/extractors/database_architecture_extractor.py`

```python
@dataclass
class DatabaseDialect:
    name: str                    # "sqlite", "mysql", "postgresql", "mongodb"
    driver: Optional[str]        # "gorm.io/driver/sqlite", "psycopg2"
    detection_source: str        # "go.mod", "requirements.txt", "code-pattern"

@dataclass
class MigrationStrategy:
    tool: str                    # "gorm-automigrate", "alembic", "flyway", "django-migrations"
    models: List[str]            # Model names passed to AutoMigrate or declared
    source_file: str

@dataclass
class ConnectionPoolConfig:
    max_open: Optional[int]
    max_idle: Optional[int]
    max_lifetime: Optional[str]
    source_file: str

@dataclass
class DatabaseArchitecture:
    dialects: List[DatabaseDialect]
    migration_strategy: Optional[MigrationStrategy]
    connection_pool: Optional[ConnectionPoolConfig]
    orm: Optional[str]           # "gorm", "sqlalchemy", "typeorm", "prisma"
    models: List[str]            # List of model/entity names
    transactions: bool           # Whether transaction patterns detected

    def to_dict(self) -> Dict[str, Any]: ...
    def to_codetrellis_format(self) -> str: ...

class DatabaseArchitectureExtractor:
    """Detect database architecture patterns across languages."""
    ...
```

### Step-by-Step Implementation

| Step | Task                                        | Details                                                                               |
| ---- | ------------------------------------------- | ------------------------------------------------------------------------------------- |
| 5.1  | Create `security_extractor.py`              | Dataclasses + extractor                                                               |
| 5.2  | Implement auth scheme detection             | Regex for `Authorization`, `Bearer`, `X-*-Key`, `apiKey` patterns across Go/Python/TS |
| 5.3  | Implement RBAC detection                    | Look for role enums, permission constants, ACL structs                                |
| 5.4  | Implement OpenAPI security integration      | If `openapi_specs` available, extract `securitySchemes`                               |
| 5.5  | Create `database_architecture_extractor.py` | Dataclasses + extractor                                                               |
| 5.6  | Implement dialect detection                 | Check go.mod for `gorm.io/driver/*`, requirements.txt for `psycopg2`/`mysqlclient`    |
| 5.7  | Implement migration detection               | Regex for `AutoMigrate`, `alembic`, `db.Migrate()` patterns                           |
| 5.8  | Implement connection pool detection         | Regex for `SetMaxOpenConns`, `pool_size=`, `max_connections=`                         |
| 5.9  | Wire into `scanner.py`                      | Add `security_model`, `database_architecture` to ProjectMatrix                        |
| 5.10 | Add output sections to `compressor.py`      | `[SECURITY_MODEL]`, `[DATABASE]` sections                                             |
| 5.11 | Write tests                                 | Test with gotify patterns (bcrypt, RequireAdmin, multi-DB)                            |

### Expected Impact

- gotify Auth/Security: 40% → **75%**
- gotify Database/ORM: 45% → **80%**

---

## 10. Phase 6: Cross-Reference & Sub-Project Scanning

### Goal

Scan embedded sub-projects (ui/, frontend/) with appropriate language analyzers. Cross-reference frontend→backend API calls.

### New File: `codetrellis/extractors/sub_project_extractor.py`

```python
@dataclass
class SubProjectScanResult:
    path: str                    # Relative path
    name: str
    framework: str               # "react", "vue", "angular", "svelte"
    version: Optional[str]
    key_dependencies: List[str]  # Top deps: ["react@19", "mobx@6", "material-ui@5"]
    scripts: Dict[str, str]      # From package.json scripts
    components_count: int        # Rough count of component files
    pages_count: int             # For file-based routing

    def to_dict(self) -> Dict[str, Any]: ...
    def to_codetrellis_format(self) -> str: ...

class SubProjectExtractor:
    """Extract key information from embedded sub-projects."""

    def extract(self, sub_project: SubProjectInfo) -> SubProjectScanResult:
        """Analyze a sub-project discovered by DiscoveryExtractor."""
        ...

    def _analyze_package_json(self, pkg_path: Path) -> Dict: ...
    def _detect_frontend_framework(self, deps: Dict) -> str: ...
    def _count_components(self, root: Path, framework: str) -> int: ...
```

### Changes to Existing Files

**`scanner.py`** — Add sub-project scanning:

```python
# After discovery:
self._scan_sub_projects(root, matrix, discovery_result)
```

**`business_domain_extractor.py`** — Fix domain classification:

```python
def _detect_domain_category(self, ...):
    # NEW: Check readme_summary and package_description FIRST
    # (From discovery result, passed in via matrix.discovery)
    readme_desc = matrix_discovery.get('readme_summary', '')
    pkg_desc = matrix_discovery.get('package_description', '')
    combined_desc = f"{readme_desc} {pkg_desc}".lower()

    # Weight description-based detection 10x over heuristics
    if 'photo' in combined_desc or 'image' in combined_desc:
        return DomainCategory.MEDIA_PHOTO
    if 'notification' in combined_desc or 'push' in combined_desc:
        return DomainCategory.COMMUNICATION
    # ... etc
```

**Go API extractor fixes** (`extractors/go/api_extractor.py`):

```python
# Fix GAP-1: Same-file group prefix resolution
# Fix GAP-2: Add g.Match(), g.StaticFS(), g.Static(), router.Any(), router.Handle()
# These are targeted regex additions to existing _extract_gin_routes()
```

### Step-by-Step Implementation

| Step | Task                                                   | Details                                                                                       |
| ---- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------- | ----------------------- |
| 6.1  | Create `sub_project_extractor.py`                      | Dataclasses + extractor                                                                       |
| 6.2  | Implement `_analyze_package_json()`                    | Read name, version, description, key deps, scripts                                            |
| 6.3  | Implement `_detect_frontend_framework()`               | Check for react, vue, angular, svelte, next, nuxt in deps                                     |
| 6.4  | Wire into `scanner.py`                                 | Iterate `discovery.sub_projects`, call extractor on each                                      |
| 6.5  | Fix `business_domain_extractor.py`                     | Use `discovery.readme_summary` + `discovery.package_description` as primary signal            |
| 6.6  | Fix `api_extractor.py` — `g.Match()`                   | Add regex pattern for `\.Match\(\[.*?\],\s*"([^"]+)"`                                         |
| 6.7  | Fix `api_extractor.py` — `g.StaticFS()`                | Add regex pattern for `\.StaticFS\(\s*"([^"]+)"`                                              |
| 6.8  | Fix `api_extractor.py` — `router.Any()`                | Add regex pattern for `\.(Any                                                                 | Handle)\(\s\*"([^"]+)"` |
| 6.9  | Fix `api_extractor.py` — same-file group prefix        | When processing `.Group("/prefix")`, track prefix and apply to subsequent route registrations |
| 6.10 | Fix `semantic_extractor.py` — middleware in Group args | Detect `router.Group(path, middleware)` pattern                                               |
| 6.11 | Add `sub_project_results` to `ProjectMatrix`           | New list field                                                                                |
| 6.12 | Add output to `compressor.py`                          | Include sub-project info in `[OVERVIEW]` or new `[FRONTEND]` section                          |
| 6.13 | Write tests                                            | Test domain fix (should NOT classify CodeTrellis as Trading/Finance)                          |

### Expected Impact

- gotify Frontend: 25% → **70%**
- gotify Business Domain: 20% → **85%**
- photoprism Business Domain: 15% → **85%**
- CodeTrellis own scan: "Trading/Finance" → **"Developer Tools"** ✓

---

## 11. Phase 7: Graceful Degradation

### Goal

For languages WITHOUT dedicated analyzers (Ruby, Rust, Java, Elixir, etc.), produce useful output via generic text analysis.

### New File: `codetrellis/extractors/generic_language_extractor.py`

```python
@dataclass
class GenericCodeInfo:
    """Basic extraction for any language — the fallback tier."""
    file_path: str
    language: str
    imports: List[str]           # Lines matching import/require/use patterns
    class_names: List[str]       # Lines matching class/struct/trait patterns
    function_names: List[str]    # Lines matching func/def/fn patterns
    constants: List[str]         # Lines matching UPPER_CASE = patterns
    comments: List[str]          # Lines matching //,  #, /* patterns (for TODOs etc)
    line_count: int

@dataclass
class GenericLanguageResult:
    language: str
    total_files: int
    total_lines: int
    classes: List[str]           # Unique class/struct names
    functions: List[str]         # Unique function names (top 50)
    imports: List[str]           # Unique import sources

    def to_dict(self) -> Dict[str, Any]: ...
    def to_codetrellis_format(self) -> str: ...

class GenericLanguageExtractor:
    """Tier 2/3 fallback extractor for unsupported languages."""

    # Generic patterns that work across most languages
    IMPORT_PATTERNS = [
        r'^\s*import\s+(.+)',           # Python, Go, Java, Kotlin, Dart, Scala
        r'^\s*from\s+(\S+)\s+import',   # Python
        r"^\s*require\s*\(?['\"](.+)['\"]", # Ruby, Node
        r'^\s*use\s+(\S+)',             # Rust, Elixir, PHP
        r'^\s*#include\s+[<"](.+)[>"]', # C/C++
        r'^\s*using\s+(\S+)',           # C#
    ]

    CLASS_PATTERNS = [
        r'^\s*(?:export\s+)?(?:public\s+)?(?:abstract\s+)?class\s+(\w+)',
        r'^\s*(?:pub\s+)?struct\s+(\w+)',    # Rust, Go
        r'^\s*(?:pub\s+)?trait\s+(\w+)',     # Rust
        r'^\s*(?:pub\s+)?enum\s+(\w+)',      # Rust, Java
        r'^\s*defmodule\s+(\S+)',            # Elixir
        r'^\s*module\s+(\w+)',               # Ruby
        r'^\s*interface\s+(\w+)',            # Java, Go, TS
    ]

    FUNCTION_PATTERNS = [
        r'^\s*(?:export\s+)?(?:pub\s+)?(?:async\s+)?(?:fn|func|def|function)\s+(\w+)',
        r'^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:async\s+)?\w+\s+(\w+)\s*\(',  # Java methods
    ]

    def extract(self, file_path: Path, language: str) -> GenericCodeInfo: ...
    def aggregate(self, results: List[GenericCodeInfo]) -> GenericLanguageResult: ...
```

### Changes to `scanner.py`

```python
def _parse_file(self, file_path, file_info, matrix):
    # ... existing type-based dispatch ...

    # NEW: Fallback for unsupported languages
    elif file_info.file_type == "unknown" and file_path.suffix in KNOWN_CODE_EXTENSIONS:
        self._parse_generic(file_path, matrix)
```

### Step-by-Step Implementation

| Step | Task                                       | Details                                             |
| ---- | ------------------------------------------ | --------------------------------------------------- |
| 7.1  | Create `generic_language_extractor.py`     | Dataclasses + extractor                             |
| 7.2  | Implement import detection                 | Multi-language regex patterns                       |
| 7.3  | Implement class/function name detection    | Multi-language regex patterns                       |
| 7.4  | Implement aggregation                      | Deduplicate, sort by frequency, limit to top 50     |
| 7.5  | Wire into `scanner.py` `_parse_file()`     | Fallback for unknown file types                     |
| 7.6  | Add `generic_languages` to `ProjectMatrix` | New dict field: `{language: GenericLanguageResult}` |
| 7.7  | Add output to `compressor.py`              | `[GENERIC_TYPES]` section for non-primary languages |
| 7.8  | Write tests                                | Test with a Rust file, Ruby file, Java file         |

---

## 12. Files Changed Per Phase

### New Files (9 total)

| Phase | File                                 | Location                  |
| ----- | ------------------------------------ | ------------------------- |
| 1     | `discovery_extractor.py`             | `codetrellis/extractors/` |
| 3     | `openapi_extractor.py`               | `codetrellis/extractors/` |
| 3     | `graphql_schema_extractor.py`        | `codetrellis/extractors/` |
| 4     | `config_template_extractor.py`       | `codetrellis/extractors/` |
| 4     | `env_inference_extractor.py`         | `codetrellis/extractors/` |
| 5     | `security_extractor.py`              | `codetrellis/extractors/` |
| 5     | `database_architecture_extractor.py` | `codetrellis/extractors/` |
| 6     | `sub_project_extractor.py`           | `codetrellis/extractors/` |
| 7     | `generic_language_extractor.py`      | `codetrellis/extractors/` |

### Modified Files

| File                             | Phases      | Changes                                                                                    |
| -------------------------------- | ----------- | ------------------------------------------------------------------------------------------ |
| `scanner.py`                     | 1,3,4,5,6,7 | Add discovery call, new fields on ProjectMatrix, new extraction steps                      |
| `compressor.py`                  | 2,3,4,5,6,7 | New `_compress_*` methods, new output sections                                             |
| `architecture_extractor.py`      | 2           | `ProjectProfile` dataclass, enhanced `_build_tech_stack()`, Go/Python framework name dicts |
| `business_domain_extractor.py`   | 6           | Fix `_detect_domain_category()` — use README + package description                         |
| `extractors/go/api_extractor.py` | 6           | Fix `g.Match()`, `g.StaticFS()`, `router.Any()`, same-file group prefix                    |
| `semantic_extractor.py`          | 6           | Fix middleware detection for `Group(path, middleware)`                                     |
| `extractors/__init__.py`         | 1,3,4,5,6,7 | Export new extractors                                                                      |
| `interfaces.py`                  | 2           | Add new enum values to `ProjectType` if needed                                             |

---

## 13. Testing Strategy

### Test Structure

```
tests/
  unit/
    test_discovery_extractor.py      # Phase 1
    test_openapi_extractor.py        # Phase 3
    test_graphql_schema_extractor.py  # Phase 3
    test_config_template_extractor.py # Phase 4
    test_env_inference_extractor.py   # Phase 4
    test_security_extractor.py       # Phase 5
    test_database_architecture.py    # Phase 5
    test_sub_project_extractor.py    # Phase 6
    test_generic_language.py         # Phase 7
    test_project_profile.py          # Phase 2
    test_domain_fix.py               # Phase 6
    test_go_route_fixes.py           # Phase 6
  fixtures/
    openapi/
      swagger_2_gotify.json          # Real gotify spec (trimmed)
      openapi_3_sample.yaml          # Sample OpenAPI 3.0
    config/
      env_example.txt                # Sample .env.example
      config_example.yml             # Sample config.example.yml
    go/
      configor_pattern.go            # Go code with configor ENVPrefix
      gin_routes_complex.go          # Go with g.Match, g.StaticFS, Groups
    sub_projects/
      package.json                   # React sub-project
    graphql/
      schema.graphql                 # Sample GraphQL schema
```

### Validation After Each Phase

After each phase, run `codetrellis scan` on the CodeTrellis repo itself and verify:

1. No regressions (existing sections still present)
2. New sections appear where expected
3. Domain is NOT "Trading/Finance" (after Phase 6)

---

## 14. Risk Assessment

| Risk                                                 | Probability | Impact | Mitigation                                                              |
| ---------------------------------------------------- | ----------- | ------ | ----------------------------------------------------------------------- |
| Discovery pass is too slow on large repos            | LOW         | HIGH   | Only glob, no file reading. Skip `node_modules`, `vendor`               |
| OpenAPI parser breaks on edge-case specs             | MEDIUM      | LOW    | Wrap in try/except, fall back gracefully                                |
| Env inference produces false positives               | MEDIUM      | MEDIUM | Only infer when we find explicit ENVPrefix/SetEnvPrefix pattern         |
| ProjectProfile increases token count significantly   | MEDIUM      | MEDIUM | Keep it to one line in `[OVERVIEW]`. Token budget managed by compressor |
| Phase 6 Go route fixes break existing correct routes | LOW         | HIGH   | Test extensively with existing Go test fixtures before merging          |
| `pyyaml` not installed in some environments          | LOW         | LOW    | Already in requirements.txt. Make YAML parsing optional with try/except |

---

## Summary: Execution Order

```
Phase 1 (2d) → Discovery Layer         → unlocks all other phases
Phase 2 (2d) → Project Profile          → fixes Overview/Stack output
Phase 3 (3d) → OpenAPI + GraphQL        → highest single ROI
Phase 6 (2d) → Sub-Project + Domain Fix → fixes Frontend + Domain
Phase 4 (3d) → Config Inference          → fixes Env Vars + Config
Phase 5 (3d) → Security + DB            → fixes Auth + Database
Phase 7 (2d) → Graceful Degradation     → enables new languages
```

**Phase 1 MUST be first** — everything else reads from discovery results.
**Phase 3 before Phase 4** — OpenAPI spec gives security schemes that Phase 5 can use.
**Phase 6 before Phase 5** — Sub-project scanning gives frontend context for facet detection.

---

**Total estimated effort: ~17 working days**
**Expected gotify score improvement: 47% → ~82%**
**Expected photoprism score improvement: ~35% → ~70%**
**Expected new-language coverage: 0% → ~50% (via Tier 2/3 fallback)**
