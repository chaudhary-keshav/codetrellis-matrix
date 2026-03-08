# CodeTrellis v4.16.0 — Supported Repository Types

> **Generated:** 12 February 2026
> **Scanner Version:** 4.16.0
> **Purpose:** Comprehensive catalog of repository types, languages, frameworks, and architectural patterns that CodeTrellis can scan and extract context from.

---

## 1. Supported Programming Languages

| Language                        | Parser                       | AST Support                                    | Depth of Extraction                                                                                                                                                                   |
| ------------------------------- | ---------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **TypeScript / TSX**            | Regex + Tree-sitter + LSP    | ✅ Full                                        | Deep — interfaces, types, classes, generics, decorators                                                                                                                               |
| **JavaScript / JSX**            | Regex + Tree-sitter          | ✅ Full                                        | Moderate — functions, classes, imports                                                                                                                                                |
| **Python**                      | Enhanced regex + Tree-sitter | ✅ Full                                        | Deep — dataclasses, Pydantic, protocols, TypedDicts, enums, decorators                                                                                                                |
| **Go**                          | Enhanced regex parser        | ❌ Regex-only                                  | Deep — structs, interfaces, methods, routes, gRPC, const blocks                                                                                                                       |
| **Protocol Buffers (.proto)**   | Dedicated proto parser       | ❌ Regex-only                                  | Full — services, messages, enums                                                                                                                                                      |
| **YAML / JSON / TOML**          | Config extractors            | N/A                                            | Configuration, environment, Docker, CI/CD                                                                                                                                             |
| **Markdown**                    | README extractor             | N/A                                            | Documentation context, features, installation                                                                                                                                         |
| **GraphQL (.graphql, .gql)**    | Schema extractor             | ❌ Regex-only                                  | Types, operations, directives, federation detection                                                                                                                                   |
| **SQL**                         | Indirect via ORM extractors  | N/A                                            | Models, migrations, schema definitions (via ORM)                                                                                                                                      |
| **SQL (Dedicated)**             | EnhancedSQLParser            | ❌ Regex-only                                  | Tables, views, functions, procedures, triggers, indexes, RLS, migrations — 6 dialects                                                                                                 |
| **Java**                        | EnhancedJavaParser + AST     | ✅ tree-sitter                                 | Classes, interfaces, records, enums, JPA entities, Spring/Quarkus/Micronaut endpoints                                                                                                 |
| **Kotlin**                      | EnhancedKotlinParser v2.0    | ✅ tree-sitter-kotlin + kotlin-language-server | Classes, objects, data/sealed/value classes, suspend functions, Ktor/Spring/Compose endpoints, DI (Koin/Hilt), multiplatform, contracts, 45+ frameworks, Kotlin 1.0-2.1+, K2 compiler |
| **C#**                          | EnhancedCSharpParser         | ❌ Regex-only                                  | Classes, structs, records, delegates, ASP.NET Core/EF Core/Blazor/SignalR                                                                                                             |
| **Rust**                        | EnhancedRustParser           | ❌ Regex-only                                  | Structs, enums, traits, impls, actix-web/Rocket/Axum/Diesel/SeaORM                                                                                                                    |
| **HTML**                        | EnhancedHTMLParser           | ✅ html.parser                                 | Documents, forms, meta/OG/JSON-LD, ARIA/WCAG, Web Components, 10 template engines                                                                                                     |
| **CSS / SCSS / Less / Stylus**  | EnhancedCSSParser            | ❌ Regex-only                                  | Selectors, variables, layout (flex/grid), media/container, animations, preprocessor                                                                                                   |
| **Bash / Shell**                | EnhancedBashParser           | ✅ tree-sitter                                 | Functions, variables, pipelines, traps, signals, HTTP calls, Docker/K8s/cloud CLIs                                                                                                    |
| **C (C89–C23)**                 | EnhancedCParser              | ✅ tree-sitter                                 | Structs, unions, enums, typedefs, functions, sockets, signals, IPC, 25+ frameworks                                                                                                    |
| **Terraform (.tf)**             | Dedicated extractor          | ❌ Regex-only                                  | Resources, variables, outputs, modules, providers                                                                                                                                     |
| **Dockerfile / docker-compose** | Docker extractor             | N/A                                            | Stages, base images, ports, volumes, commands                                                                                                                                         |

---

## 2. Supported Frameworks & Libraries

### 2.1 Frontend Frameworks

| Framework          | Detection                               | What's Extracted                                                                                                           |
| ------------------ | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Angular (v14+)** | `angular.json`, `@angular/core` imports | Components, services, modules, directives, pipes, inputs/outputs, signals, routes, stores (SignalStore/NgRx), lazy loading |
| **React**          | `react` dependency, JSX/TSX files       | Components, hooks (partial), routes (react-router)                                                                         |
| **Vue**            | `vue` dependency                        | Components (via generic extractor)                                                                                         |
| **Next.js**        | `next` dependency                       | Pages, API routes, SSR/SSG configuration                                                                                   |
| **Nuxt**           | `nuxt` dependency                       | Pages, plugins, modules                                                                                                    |

### 2.2 Backend Frameworks — TypeScript/JavaScript

| Framework   | Detection              | What's Extracted                                                                                                       |
| ----------- | ---------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **NestJS**  | `@nestjs/core` imports | Modules, controllers, services, guards, interceptors, pipes, middleware, WebSocket gateways, dependency injection tree |
| **Express** | `express` dependency   | Routes, middleware, error handlers                                                                                     |
| **Fastify** | `fastify` dependency   | Routes, plugins (via semantic extractor)                                                                               |

### 2.3 Backend Frameworks — Python

| Framework   | Detection         | What's Extracted                                                                                                        |
| ----------- | ----------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **FastAPI** | `fastapi` imports | Routes (GET/POST/PUT/DELETE/PATCH), routers, dependencies, response models, path/query/body parameters, async detection |
| **Flask**   | `flask` imports   | Routes, blueprints, URL variables, static/template folders                                                              |
| **Django**  | `django` imports  | Models (via SQLAlchemy/ORM extractor), views, URL patterns, settings                                                    |
| **Celery**  | `celery` imports  | Tasks (bind, retries, rate limits, time limits), beat schedules, queues                                                 |

### 2.4 Backend Frameworks — Go

| Framework      | Detection                | What's Extracted                                 |
| -------------- | ------------------------ | ------------------------------------------------ |
| **Gin**        | `gin-gonic/gin` imports  | Routes, handlers, middleware, route groups       |
| **Echo**       | `labstack/echo` imports  | Routes, handlers, middleware                     |
| **Chi**        | `go-chi/chi` imports     | Routes, handlers, middleware                     |
| **net/http**   | Standard library         | HTTP handlers, route registration                |
| **gRPC**       | `google.golang.org/grpc` | Service interfaces, server registration, methods |
| **Cobra**      | `spf13/cobra`            | CLI commands, subcommands                        |
| **PocketBase** | PocketBase hooks         | Hooks, lifecycle events                          |

---

## 3. AI/ML & Data Science Ecosystem

### 3.1 Deep Learning

| Library                      | What's Extracted                                                                                                    |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **PyTorch**                  | Model classes (nn.Module), layers, forward signatures, DataLoaders, training configs, optimizers, Lightning modules |
| **HuggingFace Transformers** | Models, tokenizers, TrainingArguments, Trainers, pipelines, datasets, LoRA configs                                  |

### 3.2 LLM / Agent Frameworks

| Library       | What's Extracted                                                                                |
| ------------- | ----------------------------------------------------------------------------------------------- |
| **LangChain** | LLMs, PromptTemplates, Chains (including LCEL), Agents, Tools, VectorStores, Retrievers, Memory |

### 3.3 Experiment Tracking & MLOps

| Library               | What's Extracted                                                       |
| --------------------- | ---------------------------------------------------------------------- |
| **MLflow**            | Experiments, runs, parameters, metrics, model logging, autolog configs |
| **Hydra**             | Config paths, structured configs, overrides                            |
| **Pydantic Settings** | Settings classes, env prefixes, env files                              |

### 3.4 Data Processing

| Library    | What's Extracted                                                                                                        |
| ---------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Pandas** | DataFrame creation, operations (filter/transform/aggregate/merge), GroupBy, I/O (read/write CSV/Parquet/JSON/Excel/SQL) |

### 3.5 Pipeline Orchestration

| Library     | What's Extracted                                               |
| ----------- | -------------------------------------------------------------- |
| **Airflow** | DAGs, tasks (operators), dependencies, schedules, default args |
| **Prefect** | Flows, tasks, retries, cache configs                           |
| **Dagster** | Assets, dependencies, groups, I/O managers                     |

---

## 4. Data Infrastructure

### 4.1 Databases & ORMs

| Technology           | What's Extracted                                                       |
| -------------------- | ---------------------------------------------------------------------- |
| **SQLAlchemy**       | Models, columns (types, PKs, FKs, indexes), relationships, table names |
| **Tortoise ORM**     | Model detection                                                        |
| **Prisma**           | Schema detection (via config files)                                    |
| **TypeORM**          | Entity detection (via NestJS extractor)                                |
| **Active Record**    | Model detection                                                        |
| **Django ORM**       | Model detection                                                        |
| **Beanie (MongoDB)** | Documents, fields, indexes, validators, links                          |
| **Motor / PyMongo**  | Collections, operations, aggregations, connections                     |

### 4.2 Message Queues & Event Streaming

| Technology            | What's Extracted                                                    |
| --------------------- | ------------------------------------------------------------------- |
| **Kafka**             | Producers, consumers, topics, schemas (Avro/JSON/Protobuf), streams |
| **RabbitMQ**          | Detection via compose/config                                        |
| **NATS**              | Detection via imports                                               |
| **Celery**            | Tasks, schedules, queues, routing                                   |
| **AWS SQS**           | Detection via imports                                               |
| **Google Pub/Sub**    | Detection via imports                                               |
| **Azure Service Bus** | Detection via imports                                               |
| **Pulsar / ZeroMQ**   | Detection via imports                                               |

### 4.3 Caching & Key-Value Stores

| Technology | What's Extracted                                                                                                            |
| ---------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Redis**  | Clients, cache patterns (key patterns, TTLs), pub/sub channels, data structures (lists, sets, sorted sets, hashes, streams) |

### 4.4 Vector Databases

| Technology   | What's Extracted                                   |
| ------------ | -------------------------------------------------- |
| **Pinecone** | Collections, indexes, queries, dimensions, metrics |
| **ChromaDB** | Collections, queries                               |
| **Qdrant**   | Collections, queries                               |
| **Weaviate** | Collections, queries                               |
| **FAISS**    | Index configurations                               |
| **Milvus**   | Collections, queries                               |

---

## 5. Infrastructure & DevOps

### 5.1 Containerization

| Technology         | What's Extracted                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------------------- |
| **Dockerfile**     | Multi-stage builds, base images, exposed ports, environment variables, workdirs, CMD/ENTRYPOINT, healthchecks |
| **docker-compose** | Services, images, build contexts, ports, dependencies, networks, volumes                                      |

### 5.2 Infrastructure as Code

| Technology    | What's Extracted                                                                             |
| ------------- | -------------------------------------------------------------------------------------------- |
| **Terraform** | Providers, required versions, backends, resources, data sources, variables, outputs, modules |

### 5.3 CI/CD Pipelines

| Platform                | What's Extracted                                                                  |
| ----------------------- | --------------------------------------------------------------------------------- |
| **GitHub Actions**      | Workflows, triggers, jobs, steps, needs, services, environment variables, secrets |
| **GitLab CI**           | Stages, jobs, scripts, artifacts                                                  |
| **Jenkins**             | Pipeline stages (Jenkinsfile)                                                     |
| **CircleCI**            | Jobs, workflows                                                                   |
| **Bitbucket Pipelines** | Steps, pipelines                                                                  |

### 5.4 Configuration

| Source                  | What's Extracted                                               |
| ----------------------- | -------------------------------------------------------------- |
| **package.json**        | Name, version, scripts, dependencies, devDependencies, engines |
| **tsconfig.json**       | Compiler options, paths, strict mode                           |
| **angular.json**        | Project config, prefix, styles, assets                         |
| **pyproject.toml**      | Name, version, dependencies, scripts, Python version           |
| **requirements.txt**    | Dependencies with version specs                                |
| **go.mod**              | Module name, dependencies                                      |
| **.env / .env.example** | Environment variables, defaults                                |
| **Makefile**            | Targets and commands                                           |

---

## 6. Architectural Patterns Detected

| Pattern                   | Detection Method                                            |
| ------------------------- | ----------------------------------------------------------- |
| **Monorepo**              | Multiple `package.json` / `go.mod` / `pyproject.toml` files |
| **Microservices**         | Docker compose with multiple services, sub-projects         |
| **MVC**                   | Controller/Service/Model directory structure                |
| **Repository Pattern**    | Repository classes                                          |
| **CQRS**                  | Command/Query separation detection                          |
| **Event-Driven**          | Event handlers, pub/sub, message queues                     |
| **REST**                  | HTTP endpoints, OpenAPI specs                               |
| **GraphQL**               | Schema files, resolvers                                     |
| **gRPC**                  | Proto files, service definitions                            |
| **WebSocket**             | Socket connections, events                                  |
| **Standalone Components** | Angular standalone components                               |
| **Signal Store**          | Angular signal store pattern                                |
| **Lazy Loading**          | Angular/React lazy routes                                   |

---

## 7. Cross-Cutting Extraction Capabilities

| Capability                | Description                                                                                                          |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Business Domain**       | Auto-detects project domain (25 categories: Trading, E-commerce, CRM, Healthcare, etc.) with confidence scoring      |
| **Data Flow Analysis**    | Maps real-time streaming, request-response, event-driven, pub/sub, CQRS, saga patterns                               |
| **Security Analysis**     | JWT, OAuth2, session, API key, RBAC, ABAC, CORS config, rate limiting, input validation, hardcoded secrets detection |
| **API Specification**     | OpenAPI 2.0/3.0 endpoint extraction with parameters, security schemes, models                                        |
| **Environment Variables** | Inference from code, .env files, Docker, CI/CD — with required/optional classification                               |
| **Error Handling**        | Try-catch blocks, custom error classes, HTTP error handlers, error boundaries                                        |
| **TODOs / FIXMEs**        | Extraction with priority, author, date parsing                                                                       |
| **Implementation Logic**  | Function bodies, control flow, API calls, data transformations, complexity indicators                                |
| **Hooks / Middleware**    | Language-agnostic detection of hooks, middleware, lifecycle events, CLI commands                                     |
| **Sub-Project Analysis**  | Cross-project dependency mapping in monorepos                                                                        |

---

## 8. Repository Categories Best Suited for Scanning

Based on the extractor capabilities, CodeTrellis performs best with:

1. **Full-Stack Web Applications** — Angular/React + NestJS/Express/FastAPI backends with database integration
2. **Python ML/AI Projects** — PyTorch, HuggingFace, LangChain with MLflow tracking
3. **Go Microservices** — Gin/Echo/Chi HTTP services with gRPC, Cobra CLIs
4. **Monorepo Projects** — Nx/Turborepo/Lerna workspaces with multiple sub-projects
5. **Enterprise NestJS Applications** — Full module system, guards, interceptors, pipes, gateways
6. **Data Engineering Pipelines** — Airflow/Prefect/Dagster with Kafka/Redis/MongoDB
7. **API-First Projects** — OpenAPI specs, GraphQL schemas, gRPC protobuf definitions
8. **Infrastructure-Heavy Projects** — Docker multi-stage, Terraform, CI/CD pipelines

---

## 9. Known Limitations (Pre-Evaluation)

| Area                 | Limitation                                                        |
| -------------------- | ----------------------------------------------------------------- |
| **Ruby**             | No dedicated parser — generic extraction only                     |
| **PHP**              | No dedicated parser — generic extraction only                     |
| **Elixir**           | No dedicated parser — generic extraction only                     |
| **Scala**            | No dedicated parser — generic extraction only                     |
| **Template engines** | Limited (Jinja2, EJS, Handlebars not deeply parsed)               |
| **Frontend state**   | Redux/MobX/Zustand have limited extraction vs Angular SignalStore |
| **Mono-binary Go**   | Single `main.go` with internal packages may miss structure        |
