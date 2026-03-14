# CodeTrellis — Complete Feature List

> Full feature reference for CodeTrellis 1.0.0

| Feature                     | Description                                                                   |
| --------------------------- | ----------------------------------------------------------------------------- |
| **Output Tiers**            | COMPACT, PROMPT, FULL, JSON, LOGIC - control usage                            |
| **No Truncation**           | PROMPT/FULL tiers have ZERO truncation                                        |
| **Plugin Architecture**     | Extensible language & framework plugins                                       |
| **Go Support**              | Structs, interfaces, methods, routes (Gin/Echo/Chi)                           |
| **Python Enhanced Parsing** | Dataclasses, Pydantic, Protocols, TypedDicts, Enums                           |
| **AI/ML Extractors**        | PyTorch, HuggingFace, LangChain, MLflow support                               |
| **Data Infrastructure**     | MongoDB, Redis, Kafka, Vector DB extraction                                   |
| **Pipeline Orchestration**  | Airflow, Prefect, Dagster DAG/flow/asset extraction                           |
| **JSDoc Extraction**        | Captures @param, @returns, @example                                           |
| **README Parsing**          | Extracts project documentation                                                |
| **Config Extraction**       | package.json, tsconfig, angular.json, pyproject.toml                          |
| **LSP Deep Mode**           | 99% accurate TypeScript types (--deep flag)                                   |
| **Business Domain**         | Auto-detects domain (Trading, E-commerce, etc.)                               |
| **Data Flow Analysis**      | Maps data flows through WebSocket/HTTP                                        |
| **Arch Decisions**          | Infers architectural decisions with rationale                                 |
| **Domain Vocabulary**       | Extracts domain-specific terms and definitions                                |
| **Logic Extraction**        | Captures function bodies and control flow                                     |
| **Error Boundaries**        | Resilient extraction with proper error isolation                              |
| **Parallel Processing**     | Multi-threaded scanning with `--parallel` flag                                |
| **Streaming**               | Memory-efficient extraction for large projects                                |
| **Optimal Mode**            | Maximum quality with `--optimal` flag                                         |
| **Tree-sitter AST**         | AST-based parsing for Python/TypeScript                                       |
| **Docker/Compose**          | Dockerfile & docker-compose.yml extraction                                    |
| **Terraform**               | Resources, variables, outputs, modules                                        |
| **CI/CD Pipelines**         | GitHub Actions, GitLab CI, Jenkins, CircleCI                                  |
| **NestJS Support**          | Modules, guards, interceptors, pipes, gateways                                |
| **Distributed Generation**  | Generate .codetrellis files in each component folder                          |
| **Best Practices Library**  | 4,500+ coding practices across languages                                      |
| **Context-Aware Selection** | Auto-selects practices based on detected stack                                |
| **Multi-Level Compression** | Minimal/Standard/Comprehensive formats                                        |
| **Cache Optimization**      | LLM KV-cache-aware section reordering (A5.1)                                  |
| **MCP Server**              | JSON-RPC 2.0 Model Context Protocol server (A5.2)                             |
| **JIT Context**             | File-aware context injection (A5.3)                                           |
| **AI Skills Generation**    | Auto-generated AI-executable skills (A5.5)                                    |
| **Incremental Builds**      | Only re-extract changed files (`--incremental`)                               |
| **Deterministic Output**    | Byte-identical outputs across runs (`--deterministic`)                        |
| **CI/CD Mode**              | Deterministic + parallel for pipelines (`--ci`)                               |
| **Build Verification**      | Quality gate verification (`codetrellis verify`)                              |
| **Cache Management**        | Content-addressed SHA-256 caching with `codetrellis clean`                    |
| **AI Integration Init**     | Auto-generates enriched Copilot, Claude, Cursor configs (`init --ai`)         |
| **AI Config Update**        | Regenerate AI files from existing matrix without re-scan (`init --update-ai`) |
| **JSON-LD Export**          | Schema.org/CodeAction structured data                                         |
| **Semantic Embeddings**     | TF-IDF vector embeddings for code search                                      |
| **Matrix Diff**             | JSON Patch diffs between matrix versions                                      |
| **Cross-Language Types**    | Unified type graph across 53+ languages                                       |
| **Matrix Navigator**        | Structural query engine (`fn:*`, `dep:*`)                                     |
| **MatrixBench Scorer**      | Automated quality benchmarking suite                                          |
| **Quality Gates (G1–G7)**   | 7 formal quality gates for advanced modules                                   |
| **Build Contracts (H1–H7)** | Formal I/O contracts with exit codes 41–47                                    |
| **IMPLEMENTATION_LOGIC**    | Function bodies & control flow in default PROMPT tier                         |
| **Best Practices 15+ Lang** | Auto-detected for 15 languages + 20+ frameworks                               |
| **Thread-Safe Watcher**     | threading.Lock, 2s debounce, batch callbacks                                  |
| **Git Context Section**     | Recent commits, working diff, file change frequency in matrix                 |
| **Change-Freq Sorting**     | IMPLEMENTATION_LOGIC sorted by git change frequency — hot files last          |
| **JIT Graph Boosting**      | Dependency-graph co-occurrence boosting in JIT context                        |
| **Remote Repo Scan**        | `--remote URL` clones and scans any public git repo                           |

## Supported Languages & Frameworks

| Type             | Extension            | Parser                                                    |
| ---------------- | -------------------- | --------------------------------------------------------- |
| TypeScript       | `.ts`                | Schemas, DTOs, Controllers, Services, Guards              |
| Python           | `.py`                | Classes, Functions, Flask/FastAPI routes                  |
| Go               | `.go`                | Structs, Interfaces, Methods, Routes (Gin/Echo/Chi), gRPC |
| Protocol Buffers | `.proto`             | Services, Messages, RPCs                                  |
| Angular          | `.component.ts`      | Components, Inputs, Outputs, Signals                      |
| NestJS           | `.ts`                | Modules, Guards, Interceptors, Pipes, Gateways            |
| JSON             | `.json`              | package.json, tsconfig.json                               |
| TOML             | `.toml`              | pyproject.toml                                            |
| Dockerfile       | `Dockerfile`         | Stages, ports, env vars, healthchecks                     |
| Docker Compose   | `docker-compose.yml` | Services, networks, volumes                               |
| Terraform        | `.tf`                | Resources, variables, outputs, modules                    |
| CI/CD            | `.yml`               | GitHub Actions, GitLab CI, Jenkins, CircleCI              |
| YAML             | `.yaml`              | Hydra configs, structured configs                         |

## Best Practices Library — Coverage

| Category             | Count | Description                                  |
| -------------------- | ----- | -------------------------------------------- |
| **Python Core**      | 55+   | Type hints, error handling, async, security  |
| **Python 3.10-3.12** | 36    | Version-specific features (match, @override) |
| **TypeScript**       | 42    | Type safety, generics, utility types         |
| **Angular**          | 45    | Signals, standalone components, OnPush       |
| **Design Patterns**  | 30    | Creational, structural, behavioral patterns  |
| **FastAPI**          | 10+   | Authentication, CORS, async DB operations    |
| **Django**           | 10+   | ORM, middleware, views                       |
| **Flask**            | 10+   | Blueprints, extensions, error handling       |
| **PyTorch**          | 10+   | Model architecture, training, data loading   |
| **Pandas**           | 10+   | DataFrames, groupby, merge, I/O              |
| **SQLAlchemy**       | 10+   | Models, relationships, queries               |
| **Pydantic**         | 10+   | Validation, settings, computed fields        |
| **Celery**           | 10+   | Tasks, beat scheduling, retries              |
| **DevOps**           | 15+   | Monitoring, logging, containers, deployment  |
| **Security**         | 15+   | Auth, sanitization, secrets management       |

## Output Tiers

| Tier      | Truncation | Tokens      | Use Case                                    |
| --------- | ---------- | ----------- | ------------------------------------------- |
| `compact` | Yes        | ~800-2000   | Quick overview                              |
| `prompt`  | **NO**     | ~8000-15000 | Default AI injection (includes code logic!) |
| `full`    | **NO**     | ~15000+     | Detailed analysis                           |
| `logic`   | **NO**     | ~30000+     | Full code context                           |
| `json`    | **NO**     | Variable    | Machine processing                          |
