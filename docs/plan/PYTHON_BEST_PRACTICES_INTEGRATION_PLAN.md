# CodeTrellis Multi-Language Best Practices Integration Plan

> **Version:** 2.0.0
> **Created:** 3 February 2026
> **Updated:** 3 February 2026
> **Author:** CodeTrellis Enhancement Team
> **Related:** CodeTrellis v4.1.2, PYTHON_BEST_PRACTICES.md

---

## Executive Summary

This document outlines the plan to integrate **multi-language best practices detection and compression** into CodeTrellis (Project Self-Awareness System). The system supports:

- **Languages:** Python, TypeScript, JavaScript
- **Frameworks:** Angular, NestJS, Node.js/Express, FastAPI, Flask, Django, React, Vue, Next.js

### Goals

1. **Detect language/framework usage** in any scanned project (primary, secondary, or minimal)
2. **Append compressed best practices** for detected languages/frameworks to generated prompts
3. **Create a new CLI flag** (`--best-practices` or `--bp`) to enable this feature
4. **Compress extensive documentation** into ~200-500 token-efficient reference material per language
5. **Support framework-specific practices** that augment base language practices

---

## Part 1: Current State Analysis

### 1.1 What CodeTrellis Already Does

From analyzing the matrix prompt and codebase:

| Feature                | Current Status   | Location                                                                |
| ---------------------- | ---------------- | ----------------------------------------------------------------------- |
| Project Type Detection | ✅ Exists        | `architecture_extractor.py` - `ProjectType` enum                        |
| Language Detection     | ✅ Partial       | Detects Python via files (.py), frameworks (FastAPI, Flask, Django)     |
| Python Parsing         | ✅ Comprehensive | 20+ Python extractors (pydantic, fastapi, flask, celery, pytorch, etc.) |
| Compression System     | ✅ Mature        | `compressor.py` - `MatrixCompressor` class                              |
| Output Tiers           | ✅ Exists        | compact, prompt, full, logic, json                                      |
| Plugin System          | ✅ Exists        | `plugins/` directory with language/framework plugins                    |

### 1.2 Current Python Detection Points

```
architecture_extractor.py:
├── ProjectType.FASTAPI
├── ProjectType.FLASK
├── ProjectType.DJANGO
├── ProjectType.PYTHON_LIBRARY
└── Detection via: requirements.txt, pyproject.toml, *.py files

parsers/:
├── python_parser.py       → Basic Python parsing
└── python_parser_enhanced.py → Framework-aware parsing

extractors/:
├── pydantic_extractor.py
├── fastapi_extractor.py
├── flask_extractor.py
├── sqlalchemy_extractor.py
├── celery_extractor.py
├── pytorch_extractor.py
├── huggingface_extractor.py
├── langchain_extractor.py
├── pandas_extractor.py
├── dataclass_extractor.py
├── typeddict_extractor.py
├── protocol_extractor.py
├── enum_extractor.py
├── function_extractor.py
├── dependency_extractor.py
├── mongodb_extractor.py
├── redis_extractor.py
├── kafka_extractor.py
├── vectordb_extractor.py
├── mlflow_extractor.py
└── pipeline_extractor.py
```

### 1.3 Gap Analysis

| What's Missing                        | Priority | Effort |
| ------------------------------------- | -------- | ------ |
| Language usage percentage calculation | High     | Medium |
| Best practices compression system     | High     | Medium |
| CLI flag for best practices           | High     | Low    |
| Best practices storage/caching        | Medium   | Low    |
| Multi-language best practices support | High     | High   |
| Framework-specific practice selection | High     | Medium |
| Context-aware practice selection      | Low      | High   |

---

## Part 2: Supported Languages & Frameworks

### 2.0 Language & Framework Matrix

| Language       | Frameworks                                                  | Priority | Status     |
| -------------- | ----------------------------------------------------------- | -------- | ---------- |
| **Python**     | FastAPI, Flask, Django, PyTorch, Pandas, Celery, SQLAlchemy | High     | 🟢 Planned |
| **TypeScript** | Angular, NestJS, React, Vue, Next.js                        | High     | 🟢 Planned |
| **JavaScript** | Node.js/Express, React, Vue                                 | High     | 🟢 Planned |
| Go             | Gin, Echo, Fiber                                            | Medium   | 🟡 Future  |
| Rust           | Actix, Axum, Rocket                                         | Medium   | 🟡 Future  |
| Java           | Spring Boot                                                 | Low      | ⚪ Backlog |
| C#             | .NET Core                                                   | Low      | ⚪ Backlog |

---

## Part 2A: TypeScript Best Practices

### 2A.1 Compressed TypeScript Best Practices Template

```
[TYPESCRIPT_BEST_PRACTICES]
# TypeScript 5.x | Strict Mode | ESLint Compliant

## NAMING
variable|function|method=camelCase|Class|Interface|Type=PascalCase|CONSTANT=UPPER_SNAKE|_private|#private(ES2022)

## TYPES
prefer_interface_over_type(extendable)|avoid_any→unknown|use_strict_mode|no_implicit_any|strict_null_checks

## TYPE_DEFINITIONS
primitives:string,number,boolean,null,undefined,symbol,bigint|Array<T>|T[]|Record<K,V>|Map<K,V>|Set<T>

## UNIONS_INTERSECTIONS
union:A|B|C|discriminated:{type:'a'}|{type:'b'}|intersection:A&B|type_guards:is,in,typeof,instanceof

## GENERICS
function fn<T>(x:T):T|constraints:<T extends Base>|defaults:<T=string>|infer:infer R

## UTILITY_TYPES
Partial<T>|Required<T>|Readonly<T>|Pick<T,K>|Omit<T,K>|Record<K,V>|ReturnType<F>|Parameters<F>|Awaited<P>

## FUNCTIONS
typed_params|explicit_return|overloads|arrow_preferred|async/await>promises|void_vs_undefined

## CLASSES
readonly_props|private_#|abstract|implements_interface|constructor_injection|no_public_keyword_redundant

## MODULES
named_exports_preferred|barrel_files(index.ts)|path_aliases(@/)|avoid_default_exports(libs)|tree_shaking

## ENUMS
const_enum(inlined)|string_enum_preferred|as_const_alternative|exhaustive_switch

## ERROR_HANDLING
custom_errors(extends Error)|type_safe_catch|Result<T,E>_pattern|never_for_exhaustive

## ASYNC
Promise<T>|async/await|Promise.all/allSettled/race|AbortController|AsyncIterator

## CONFIG
strict:true|noUncheckedIndexedAccess|exactOptionalPropertyTypes|noImplicitReturns|esModuleInterop

## TOOLS
eslint(@typescript-eslint)|prettier|tsc --noEmit(check)|ts-node|tsx|vitest/jest
```

### 2A.2 TypeScript Framework Extensions

#### Angular-Specific Practices

```
[ANGULAR_BEST_PRACTICES]
# Angular 17+ | Standalone | Signals

## ARCHITECTURE
standalone_components(default)|lazy_loading|feature_modules|smart/dumb_components|barrel_exports

## COMPONENTS
@Component({standalone:true,imports:[]})|OnPush_change_detection|signals()|input()|output()|viewChild()

## SIGNALS
signal<T>()|computed()|effect()|input.required<T>()|model<T>()|toSignal()|toObservable()

## TEMPLATES
@if/@else/@switch(new)|@for(track)|@defer/@loading/@error|ng-container|ng-template

## SERVICES
@Injectable({providedIn:'root'})|inject()|functional_guards|functional_resolvers|HttpClient

## STATE
NgRx_SignalStore|withState()|withComputed()|withMethods()|patchState()|rxMethod()

## ROUTING
Routes[]|loadComponent()|loadChildren()|canActivate/canMatch(functional)|resolve

## FORMS
ReactiveFormsModule|FormControl<T>|FormGroup|FormArray|Validators|async_validators

## HTTP
HttpClient|interceptors(functional)|withFetch()|typed_responses|error_handling(catchError)

## TESTING
TestBed.configureTestingModule|ComponentFixture|fakeAsync/tick|HttpTestingController|jest/vitest

## PERFORMANCE
OnPush|trackBy→track|*ngFor→@for|lazy_routes|preloadingStrategy|defer_views

## STYLE
component.scss(encapsulated)|:host|::ng-deep(avoid)|CSS_variables|Tailwind_compatible
```

#### NestJS-Specific Practices

```
[NESTJS_BEST_PRACTICES]
# NestJS 10+ | TypeScript | Decorators

## ARCHITECTURE
modules(@Module)|controllers(@Controller)|providers(@Injectable)|domain-driven|clean_architecture

## MODULES
@Module({imports,controllers,providers,exports})|forRoot()/forRootAsync()|dynamic_modules|global_modules

## CONTROLLERS
@Controller('prefix')|@Get/@Post/@Put/@Delete/@Patch|@Param/@Query/@Body/@Headers|@Res(passthrough)

## PROVIDERS
@Injectable()|constructor_injection|custom_providers(useClass,useValue,useFactory)|scope(DEFAULT,REQUEST,TRANSIENT)

## DTOs
class-validator(@IsString,@IsNumber,@IsOptional)|class-transformer(@Transform,@Exclude)|ValidationPipe(global)

## PIPES
@UsePipes()|ValidationPipe|ParseIntPipe|ParseUUIDPipe|custom_pipes(@Injectable)

## GUARDS
@UseGuards()|CanActivate|ExecutionContext|@SetMetadata()|Reflector|JwtAuthGuard

## INTERCEPTORS
@UseInterceptors()|NestInterceptor|CallHandler|map()|catchError()|timeout()

## EXCEPTION_FILTERS
@Catch()|ExceptionFilter|HttpException|custom_exceptions|global_filters

## MIDDLEWARE
implements NestMiddleware|@Module({}).configure()|MiddlewareConsumer|apply().forRoutes()

## DATABASE
TypeORM(@Entity,@Column,@Repository)|Prisma(PrismaService)|Mongoose(@Schema,@Prop)|transactions

## AUTH
Passport(@UseGuards(AuthGuard))|JWT|@nestjs/jwt|strategies|decorators(@CurrentUser)

## VALIDATION
class-validator|whitelist:true|forbidNonWhitelisted:true|transform:true|groups

## TESTING
@nestjs/testing|Test.createTestingModule|overrideProvider|mock_repositories|e2e(supertest)

## CONFIG
@nestjs/config|ConfigModule.forRoot()|ConfigService|env_validation(joi/zod)|typed_config

## SWAGGER
@nestjs/swagger|@ApiTags|@ApiOperation|@ApiResponse|@ApiProperty|DocumentBuilder
```

#### Node.js/Express-Specific Practices

```
[NODEJS_BEST_PRACTICES]
# Node.js 20+ | ES Modules | Express/Fastify

## ARCHITECTURE
layered(controllers→services→repositories)|clean_architecture|DI_container|error_handling_middleware

## MODULES
ES_modules(import/export)|package.json:type="module"|.mjs/.cjs|dynamic_import()|top-level_await

## EXPRESS
app.use(middleware)|router.get/post/put/delete|req.params/query/body|res.json/status/send|next(err)

## MIDDLEWARE
(req,res,next)=>{}|error_middleware(err,req,res,next)|async_wrapper|helmet|cors|compression|morgan

## ERROR_HANDLING
custom_errors(extends Error)|async_wrapper|global_error_handler|operational_vs_programmer|process.on('uncaughtException')

## VALIDATION
joi/zod/yup|validate_early|sanitize_input|express-validator|ajv(JSON_Schema)

## DATABASE
connection_pooling|migrations|transactions|query_builders(knex)|ORMs(prisma,typeorm,sequelize)

## AUTH
passport.js|JWT(jsonwebtoken)|bcrypt|session(express-session)|OAuth2|refresh_tokens

## SECURITY
helmet|rate_limiting|CORS|input_validation|SQL_injection_prevention|XSS_protection|CSRF

## ASYNC
async/await|Promise.all|worker_threads|cluster|stream_processing|AbortController

## LOGGING
winston/pino|structured_logging|log_levels|request_id|correlation_id|no_console.log_in_prod

## ENV
dotenv|env_validation|secrets_management|config_per_environment|never_commit_.env

## TESTING
jest/vitest/mocha|supertest(e2e)|sinon(mocks)|nyc/c8(coverage)|test_containers

## PERFORMANCE
clustering|caching(redis)|compression|connection_pooling|lazy_loading|memory_leaks

## PM2/PROCESS
pm2|cluster_mode|graceful_shutdown|health_checks|process.env.NODE_ENV
```

---

## Part 2B: React & Vue Best Practices

### React-Specific Practices

```
[REACT_BEST_PRACTICES]
# React 18+ | Hooks | TypeScript

## COMPONENTS
functional_components|props:interface|children:ReactNode|forwardRef|memo()|displayName

## HOOKS
useState<T>()|useEffect(deps)|useCallback(deps)|useMemo(deps)|useRef<T>()|useReducer|useContext

## CUSTOM_HOOKS
use*_naming|return_tuple/object|handle_cleanup|deps_array|extract_reusable_logic

## STATE
local(useState)|lifted(props)|context(createContext)|global(zustand,redux,jotai)|server(tanstack-query)

## EFFECTS
cleanup_return|deps_exhaustive|avoid_object_deps|useLayoutEffect(DOM)|StrictMode_double_invoke

## PATTERNS
compound_components|render_props|HOCs(sparingly)|controlled_vs_uncontrolled|composition>inheritance

## PERFORMANCE
memo()|useMemo()|useCallback()|lazy()+Suspense|virtualization|code_splitting|React.Profiler

## FORMS
controlled_inputs|react-hook-form|zod/yup_validation|FormProvider|useFormContext

## ROUTING
react-router-dom|createBrowserRouter|loader/action|Outlet|useParams/useSearchParams|lazy_routes

## DATA_FETCHING
tanstack-query(useQuery,useMutation)|SWR|suspense_for_data|error_boundaries|loading_states

## TESTING
@testing-library/react|render()|screen.getBy*/findBy*/queryBy*|userEvent|act()|jest/vitest

## STYLING
CSS_Modules|Tailwind|styled-components|className_conditional(clsx)|CSS-in-JS

## FILE_STRUCTURE
feature-based|components/|hooks/|utils/|types/|index.ts_barrels|*.test.tsx_colocated
```

### Vue-Specific Practices

```
[VUE_BEST_PRACTICES]
# Vue 3 | Composition API | TypeScript

## COMPONENTS
<script setup lang="ts">|defineProps<T>()|defineEmits<T>()|defineExpose()|SFC(.vue)

## COMPOSITION_API
ref<T>()|reactive<T>()|computed()|watch()|watchEffect()|provide/inject|composables

## REACTIVITY
ref(primitives)|reactive(objects)|toRef()|toRefs()|shallowRef()|readonly()|unref()

## LIFECYCLE
onMounted()|onUnmounted()|onUpdated()|onBeforeMount()|onBeforeUnmount()|onErrorCaptured()

## COMPOSABLES
use*_naming|return_refs|handle_cleanup|accept_refs_or_getters|VueUse_library

## TEMPLATES
v-if/v-else/v-else-if|v-for(:key)|v-model|v-bind(:)|v-on(@)|v-slot(#)|<template>

## STATE
Pinia(defineStore)|state()|getters|actions|$patch()|storeToRefs()|persist_plugin

## ROUTING
vue-router|createRouter()|<RouterView>|<RouterLink>|useRoute()|useRouter()|navigation_guards

## PROPS_EMITS
withDefaults(defineProps)|defineEmits(['event'])|v-model:prop|.sync_modifier(v2)

## PERFORMANCE
v-once|v-memo|shallowRef|<KeepAlive>|<Suspense>|defineAsyncComponent|code_splitting

## TESTING
@vue/test-utils|mount()/shallowMount()|wrapper.find()|trigger()|vitest|@testing-library/vue

## STYLING
scoped_styles|CSS_modules|v-bind_in_css|Tailwind|UnoCSS
```

### Next.js-Specific Practices

```
[NEXTJS_BEST_PRACTICES]
# Next.js 14+ | App Router | TypeScript

## APP_ROUTER
app/|page.tsx|layout.tsx|loading.tsx|error.tsx|not-found.tsx|route.tsx(API)

## SERVER_COMPONENTS
default_server|'use client'(client)|async_components|fetch_in_components|no_useState_server

## DATA_FETCHING
fetch(cache/revalidate)|generateStaticParams()|generateMetadata()|cookies()|headers()

## ROUTING
folder-based|[param]|[...catch]|[[...optional]]|(groups)|@parallel|intercepting(.)

## CACHING
fetch_cache:{cache:'force-cache'|'no-store'}|revalidate:seconds|revalidatePath()|revalidateTag()

## SERVER_ACTIONS
'use server'|form_actions|useFormState()|useFormStatus()|validation(zod)|error_handling

## METADATA
generateMetadata()|metadata_object|opengraph|twitter|icons|sitemap.xml|robots.txt

## API_ROUTES
app/api/route.tsx|GET/POST/PUT/DELETE|NextRequest/NextResponse|middleware.ts

## OPTIMIZATION
next/image|next/font|next/script|lazy_loading|static_generation|ISR|streaming

## ENV
.env.local|NEXT_PUBLIC_*|server_only_env|env_validation

## DEPLOYMENT
vercel|edge_runtime|serverless_functions|static_export|docker
```

---

## Part 2: Architecture Design

### 2.1 Language Detection Enhancement

Create a new `LanguageAnalyzer` class to calculate language distribution:

```python
# Proposed:.codetrellis/analyzers/language_analyzer.py

class Language(Enum):
    """Supported languages for best practices"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    UNKNOWN = "unknown"


class Framework(Enum):
    """Detected frameworks"""
    # Python
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO = "django"
    PYTORCH = "pytorch"
    PANDAS = "pandas"
    CELERY = "celery"
    SQLALCHEMY = "sqlalchemy"
    # TypeScript/JavaScript
    ANGULAR = "angular"
    NESTJS = "nestjs"
    REACT = "react"
    VUE = "vue"
    NEXTJS = "nextjs"
    EXPRESS = "express"
    # Others
    UNKNOWN = "unknown"


@dataclass
class LanguageStats:
    """Statistics about language usage in the project"""
    language: Language
    file_count: int
    line_count: int
    percentage: float  # 0-100
    frameworks: List[Framework]
    is_primary: bool  # > 50%
    is_significant: bool  # > 10%

@dataclass
class LanguageAnalysis:
    """Complete language analysis result"""
    primary_language: Language
    languages: Dict[Language, LanguageStats]
    total_files: int
    total_lines: int
    detected_frameworks: List[Framework]
    project_type: str  # "fullstack", "frontend", "backend", "library", "monorepo"
```

**Detection Logic:**

```
1. Count files by extension:
   - .py → Python
   - .ts, .tsx → TypeScript
   - .js, .jsx → JavaScript
   - .go → Go
   - .rs → Rust
   - etc.

2. Calculate line counts (weighted importance)

3. Detect frameworks:
   Python: FastAPI, Flask, Django, PyTorch, etc.
   TypeScript: Angular, React, NestJS, Vue, Next.js
   JavaScript: Express, React, Vue

4. Determine:
   - PRIMARY: > 50% of codebase
   - SIGNIFICANT: 10-50% of codebase
   - MINIMAL: < 10% of codebase

5. Project Type Classification:
   - Frontend: Angular/React/Vue without backend
   - Backend: NestJS/FastAPI/Flask/Express
   - Fullstack: Frontend + Backend frameworks
   - Library: No framework, publishable package
   - Monorepo: Multiple packages/apps
```

### 2.2 Multi-Language Best Practices System

Create a dedicated module for compressing and storing best practices:

```python
# Proposed:.codetrellis/best_practices/

best_practices/
├── __init__.py
├── base.py                    # Abstract base class
├── compressor.py              # Generic compression logic
├── registry.py                # Language/Framework registry
├── languages/
│   ├── __init__.py
│   ├── python_practices.py    # Python best practices
│   ├── typescript_practices.py # TypeScript best practices
│   └── javascript_practices.py # JavaScript best practices
├── frameworks/
│   ├── __init__.py
│   ├── angular_practices.py   # Angular-specific
│   ├── nestjs_practices.py    # NestJS-specific
│   ├── react_practices.py     # React-specific
│   ├── vue_practices.py       # Vue-specific
│   ├── nextjs_practices.py    # Next.js-specific
│   ├── express_practices.py   # Express-specific
│   ├── fastapi_practices.py   # FastAPI-specific
│   ├── flask_practices.py     # Flask-specific
│   └── django_practices.py    # Django-specific
└── templates/
    ├── python_compressed.txt
    ├── typescript_compressed.txt
    ├── angular_compressed.txt
    ├── nestjs_compressed.txt
    └── ... (more templates)
```

### 2.3 Compression Strategy for Python Best Practices

**Source:** `docs/PYTHON_BEST_PRACTICES.md` (1384 lines, ~20KB)
**Target:** ~200-400 tokens (~800-1600 characters)

**Compression Approach:**

```
Level 1: MINIMAL (~100 tokens)
- Only Zen of Python principles (abbreviated)
- Core PEP 8 rules (one-liners)

Level 2: STANDARD (~250 tokens) [DEFAULT]
- Key naming conventions table
- Essential idioms (comprehensions, context managers)
- Type hints basics
- Error handling rules

Level 3: COMPREHENSIVE (~400 tokens)
- All Level 2 content
- Framework-specific guidelines
- Security basics
- Testing patterns
```

### 2.4 Compressed Python Best Practices Template

Here's the proposed compressed format for `python_compressed.txt`:

```
[PYTHON_BEST_PRACTICES]
# PEP8|PEP20|PEP484|PEP257 Compliant

## NAMING
var|func|method=snake_case|Class=PascalCase|CONST=UPPER_SNAKE|_protected|__private|__dunder__

## STYLE
indent=4spaces|max_line=79|imports:stdlib→3rdparty→local|quotes=consistent|blank_lines:2(top-level),1(methods)

## TYPE_HINTS
basic:str,int,float,bool,None|collections:List[T],Dict[K,V],Set[T],Tuple[T,...]|Optional[T]=T|None|Union[A,B]→A|B(3.10+)

## IDIOMS
comprehensions>map/filter|f-strings>format|enumerate>range(len)|context_managers(with)|unpacking(a,b=b,a)|truthiness(if x:)

## ERROR_HANDLING
specific_exceptions|raise_from|custom_errors(Exception)|context_managers|no_bare_except|no_pass_silently

## DOCSTRINGS
"""One-line."""|"""Multi-line.\n\nArgs:\n    param: Description.\n\nReturns:\n    Description.\n"""

## PROJECT_STRUCTURE
src/pkg/|tests/|pyproject.toml|requirements.txt|.venv/|docs/

## TESTING
pytest|fixtures|parametrize|mocks|assert|coverage

## SECURITY
input_validation(pydantic)|env_vars(pydantic-settings)|hash_passwords(passlib)|jwt(jose)|no_secrets_in_code

## FRAMEWORKS
fastapi:BaseModel,Depends,HTTPException,status|flask:Blueprint,request,jsonify|django:models,views,urls

## ASYNC
asyncio|async/await|aiohttp|gather|TaskGroup(3.11+)

## TOOLS
black(format)|ruff(lint)|mypy(types)|pytest(test)|pre-commit
```

---

## Part 3: Implementation Plan

### Phase 1: Language Detection Enhancement (Week 1)

#### Task 1.1: Create Language Analyzer

**File:** .codetrellis/analyzers/language_analyzer.py`

```python
"""
Language Analyzer for CodeTrellis
==========================

Analyzes language distribution in a project to determine:
- Primary language
- Language percentages
- Framework detection per language
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple
from enum import Enum


class Language(Enum):
    """Supported languages for best practices"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    UNKNOWN = "unknown"


LANGUAGE_EXTENSIONS = {
    Language.PYTHON: {".py", ".pyi", ".pyx", ".pxd"},
    Language.TYPESCRIPT: {".ts", ".tsx", ".mts", ".cts"},
    Language.JAVASCRIPT: {".js", ".jsx", ".mjs", ".cjs"},
    Language.GO: {".go"},
    Language.RUST: {".rs"},
    Language.JAVA: {".java"},
}


PYTHON_FRAMEWORKS = {
    "fastapi": ["fastapi", "starlette"],
    "flask": ["flask"],
    "django": ["django"],
    "pytorch": ["torch", "pytorch"],
    "tensorflow": ["tensorflow", "keras"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["sklearn"],
    "celery": ["celery"],
    "sqlalchemy": ["sqlalchemy"],
    "pydantic": ["pydantic"],
    "langchain": ["langchain"],
    "huggingface": ["transformers", "datasets"],
}


@dataclass
class LanguageStats:
    """Statistics about a single language in the project"""
    language: Language
    file_count: int = 0
    line_count: int = 0
    percentage: float = 0.0
    frameworks: List[str] = field(default_factory=list)

    @property
    def is_primary(self) -> bool:
        """Language is primary if > 50% of codebase"""
        return self.percentage > 50

    @property
    def is_significant(self) -> bool:
        """Language is significant if > 10% of codebase"""
        return self.percentage > 10

    @property
    def is_minimal(self) -> bool:
        """Language is minimal if < 10% of codebase"""
        return self.percentage < 10 and self.file_count > 0


@dataclass
class LanguageAnalysis:
    """Complete language analysis of a project"""
    project_path: str
    primary_language: Language = Language.UNKNOWN
    languages: Dict[Language, LanguageStats] = field(default_factory=dict)
    total_files: int = 0
    total_lines: int = 0

    def get_language_stats(self, language: Language) -> LanguageStats:
        """Get stats for a specific language"""
        return self.languages.get(language, LanguageStats(language=language))

    def has_language(self, language: Language, min_percentage: float = 1.0) -> bool:
        """Check if project uses a language above threshold"""
        stats = self.get_language_stats(language)
        return stats.percentage >= min_percentage

    def get_significant_languages(self) -> List[LanguageStats]:
        """Get all languages with > 10% usage"""
        return [s for s in self.languages.values() if s.is_significant]


class LanguageAnalyzer:
    """Analyzes language distribution in a project"""

    def __init__(self, ignore_patterns: List[str] = None):
        self.ignore_patterns = ignore_patterns or [
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            "dist", "build", ".angular", "coverage"
        ]

    def analyze(self, project_path: Path) -> LanguageAnalysis:
        """Analyze language distribution in project"""
        result = LanguageAnalysis(project_path=str(project_path))

        # Count files by language
        file_counts: Dict[Language, int] = {}
        line_counts: Dict[Language, int] = {}

        for file_path in self._walk_files(project_path):
            lang = self._detect_language(file_path)
            if lang != Language.UNKNOWN:
                file_counts[lang] = file_counts.get(lang, 0) + 1
                line_counts[lang] = line_counts.get(lang, 0) + self._count_lines(file_path)

        # Calculate totals
        result.total_files = sum(file_counts.values())
        result.total_lines = sum(line_counts.values())

        if result.total_files == 0:
            return result

        # Calculate percentages and create stats
        for lang in file_counts:
            percentage = (file_counts[lang] / result.total_files) * 100
            frameworks = self._detect_frameworks(project_path, lang) if lang == Language.PYTHON else []

            result.languages[lang] = LanguageStats(
                language=lang,
                file_count=file_counts[lang],
                line_count=line_counts.get(lang, 0),
                percentage=round(percentage, 1),
                frameworks=frameworks
            )

        # Determine primary language
        if result.languages:
            primary = max(result.languages.values(), key=lambda x: x.percentage)
            result.primary_language = primary.language

        return result

    def _walk_files(self, root: Path):
        """Walk through files, respecting ignore patterns"""
        for item in root.rglob("*"):
            if item.is_file() and not self._should_ignore(item):
                yield item

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        path_str = str(path)
        return any(pattern in path_str for pattern in self.ignore_patterns)

    def _detect_language(self, file_path: Path) -> Language:
        """Detect language from file extension"""
        suffix = file_path.suffix.lower()
        for lang, extensions in LANGUAGE_EXTENSIONS.items():
            if suffix in extensions:
                return lang
        return Language.UNKNOWN

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in file"""
        try:
            return sum(1 for _ in open(file_path, 'r', encoding='utf-8', errors='ignore'))
        except:
            return 0

    def _detect_frameworks(self, project_path: Path, language: Language) -> List[str]:
        """Detect frameworks used for a language"""
        if language == Language.PYTHON:
            return self._detect_python_frameworks(project_path)
        return []

    def _detect_python_frameworks(self, project_path: Path) -> List[str]:
        """Detect Python frameworks from requirements/imports"""
        frameworks = []

        # Check requirements.txt
        req_file = project_path / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text().lower()
            for framework, patterns in PYTHON_FRAMEWORKS.items():
                if any(p in content for p in patterns):
                    frameworks.append(framework)

        # Check pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text().lower()
            for framework, patterns in PYTHON_FRAMEWORKS.items():
                if any(p in content for p in patterns):
                    if framework not in frameworks:
                        frameworks.append(framework)

        return frameworks
```

#### Task 1.2: Integrate with Scanner

**File:** .codetrellis/scanner.py` - Add language analysis

```python
# In ProjectScanner.scan() method, add:

from.codetrellis.analyzers.language_analyzer import LanguageAnalyzer, LanguageAnalysis

# After existing scanning logic:
language_analyzer = LanguageAnalyzer()
matrix.language_analysis = language_analyzer.analyze(root)
```

### Phase 2: Best Practices Compression System (Week 1-2)

#### Task 2.1: Create Best Practices Base

**File:** .codetrellis/best_practices/__init__.py`

```python
"""
CodeTrellis Best Practices Module
==========================

Provides language-specific best practices that can be compressed
and injected into generated prompts.
"""

from .base import BestPracticesProvider, CompressionLevel
from .python_practices import PythonBestPractices

__all__ = [
    "BestPracticesProvider",
    "CompressionLevel",
    "PythonBestPractices",
]
```

**File:** .codetrellis/best_practices/base.py`

```python
"""
Base classes for best practices providers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class CompressionLevel(Enum):
    """Compression level for best practices"""
    MINIMAL = "minimal"      # ~100 tokens
    STANDARD = "standard"    # ~250 tokens (default)
    COMPREHENSIVE = "comprehensive"  # ~400 tokens


@dataclass
class BestPracticesSection:
    """A section of best practices"""
    name: str
    content: str
    priority: int  # 1-10, higher = more important
    tokens_estimate: int
    frameworks: List[str] = None  # If framework-specific


class BestPracticesProvider(ABC):
    """Abstract base class for language best practices"""

    @property
    @abstractmethod
    def language(self) -> str:
        """Return the language name"""
        pass

    @property
    @abstractmethod
    def sections(self) -> List[BestPracticesSection]:
        """Return all available sections"""
        pass

    @abstractmethod
    def compress(
        self,
        level: CompressionLevel = CompressionLevel.STANDARD,
        frameworks: List[str] = None,
        max_tokens: int = None
    ) -> str:
        """
        Compress best practices to target level.

        Args:
            level: Compression level
            frameworks: Include framework-specific practices
            max_tokens: Override default token limit

        Returns:
            Compressed best practices string
        """
        pass

    def get_framework_practices(self, framework: str) -> Optional[str]:
        """Get practices specific to a framework"""
        for section in self.sections:
            if section.frameworks and framework in section.frameworks:
                return section.content
        return None
```

#### Task 2.2: Create Python Best Practices Provider

**File:** .codetrellis/best_practices/python_practices.py`

```python
"""
Python Best Practices Provider
==============================

Compresses Python best practices from various PEPs and guidelines
into token-efficient formats for prompt injection.
"""

from typing import List, Optional
from .base import BestPracticesProvider, BestPracticesSection, CompressionLevel


class PythonBestPractices(BestPracticesProvider):
    """Provides compressed Python best practices"""

    @property
    def language(self) -> str:
        return "python"

    @property
    def sections(self) -> List[BestPracticesSection]:
        return [
            BestPracticesSection(
                name="naming",
                content=self._naming_section(),
                priority=10,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="style",
                content=self._style_section(),
                priority=9,
                tokens_estimate=35
            ),
            BestPracticesSection(
                name="type_hints",
                content=self._type_hints_section(),
                priority=8,
                tokens_estimate=40
            ),
            BestPracticesSection(
                name="idioms",
                content=self._idioms_section(),
                priority=9,
                tokens_estimate=40
            ),
            BestPracticesSection(
                name="error_handling",
                content=self._error_handling_section(),
                priority=8,
                tokens_estimate=35
            ),
            BestPracticesSection(
                name="docstrings",
                content=self._docstrings_section(),
                priority=7,
                tokens_estimate=40
            ),
            BestPracticesSection(
                name="project_structure",
                content=self._project_structure_section(),
                priority=6,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="testing",
                content=self._testing_section(),
                priority=6,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="security",
                content=self._security_section(),
                priority=7,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="async",
                content=self._async_section(),
                priority=5,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="tools",
                content=self._tools_section(),
                priority=5,
                tokens_estimate=15
            ),
            # Framework-specific sections
            BestPracticesSection(
                name="fastapi",
                content=self._fastapi_section(),
                priority=8,
                tokens_estimate=40,
                frameworks=["fastapi"]
            ),
            BestPracticesSection(
                name="flask",
                content=self._flask_section(),
                priority=8,
                tokens_estimate=35,
                frameworks=["flask"]
            ),
            BestPracticesSection(
                name="django",
                content=self._django_section(),
                priority=8,
                tokens_estimate=35,
                frameworks=["django"]
            ),
            BestPracticesSection(
                name="pytorch",
                content=self._pytorch_section(),
                priority=7,
                tokens_estimate=40,
                frameworks=["pytorch"]
            ),
            BestPracticesSection(
                name="pandas",
                content=self._pandas_section(),
                priority=6,
                tokens_estimate=30,
                frameworks=["pandas"]
            ),
        ]

    def compress(
        self,
        level: CompressionLevel = CompressionLevel.STANDARD,
        frameworks: List[str] = None,
        max_tokens: int = None
    ) -> str:
        """Compress Python best practices"""

        # Token budgets by level
        token_limits = {
            CompressionLevel.MINIMAL: 100,
            CompressionLevel.STANDARD: 250,
            CompressionLevel.COMPREHENSIVE: 400,
        }

        budget = max_tokens or token_limits.get(level, 250)

        # Sort sections by priority
        sections = sorted(self.sections, key=lambda x: x.priority, reverse=True)

        # Filter framework-specific sections
        if frameworks:
            sections = [
                s for s in sections
                if not s.frameworks or any(f in (s.frameworks or []) for f in frameworks)
            ]
        else:
            # Exclude framework-specific sections if no frameworks specified
            sections = [s for s in sections if not s.frameworks]

        # Build output within budget
        lines = ["[PYTHON_BEST_PRACTICES]"]
        lines.append("# PEP8|PEP20|PEP484|PEP257 Compliant")
        lines.append("")

        current_tokens = 15  # Header estimate

        for section in sections:
            if current_tokens + section.tokens_estimate <= budget:
                lines.append(f"## {section.name.upper()}")
                lines.append(section.content)
                lines.append("")
                current_tokens += section.tokens_estimate

        return "\n".join(lines).strip()

    # ============ Section Definitions ============

    def _naming_section(self) -> str:
        return "var|func|method=snake_case|Class=PascalCase|CONST=UPPER_SNAKE|_protected|__private|__dunder__"

    def _style_section(self) -> str:
        return "indent=4spaces|max_line=79|imports:stdlib→3rdparty→local|quotes=consistent|blank:2(top),1(method)"

    def _type_hints_section(self) -> str:
        return "basic:str,int,float,bool,None|List[T],Dict[K,V],Set[T],Tuple[T,...]|Optional[T]=T|None|Union→|(3.10+)"

    def _idioms_section(self) -> str:
        return "comprehensions>map/filter|f-strings>format|enumerate>range(len)|with(context)|unpacking|truthiness(if x:)"

    def _error_handling_section(self) -> str:
        return "specific_except|raise_from|custom_errors(Exception)|with(cleanup)|no_bare_except|no_pass_silently"

    def _docstrings_section(self) -> str:
        return '"""One-line."""|"""Multi.\\n\\nArgs:\\n    p:Desc.\\n\\nReturns:\\n    Desc.\\nRaises:\\n    Err:When."""'

    def _project_structure_section(self) -> str:
        return "src/pkg/|tests/|pyproject.toml|requirements.txt|.venv/|docs/"

    def _testing_section(self) -> str:
        return "pytest|@fixture|@parametrize|mock.patch|assert|coverage>80%"

    def _security_section(self) -> str:
        return "pydantic(validate)|env_vars(settings)|passlib(hash)|jose(jwt)|no_secrets_in_code"

    def _async_section(self) -> str:
        return "asyncio|async/await|aiohttp|gather(*tasks)|TaskGroup(3.11+)"

    def _tools_section(self) -> str:
        return "black(fmt)|ruff(lint)|mypy(types)|pytest(test)|pre-commit"

    # ============ Framework Sections ============

    def _fastapi_section(self) -> str:
        return """fastapi:
  routes:@app.get/post|async def|->Response
  models:BaseModel|Field()|validator
  deps:Depends()|get_db|auth
  errors:HTTPException(status,detail)
  docs:summary,description,tags"""

    def _flask_section(self) -> str:
        return """flask:
  routes:@app.route()|@bp.route()
  factory:create_app()|init_extensions
  req:request.json|request.args
  resp:jsonify()|make_response()
  blueprints:modular structure"""

    def _django_section(self) -> str:
        return """django:
  models:Model|fields|Meta|managers
  views:CBV(View)|FBV|@api_view
  urls:path()|include()
  forms:Form|ModelForm|clean_*
  admin:ModelAdmin|register"""

    def _pytorch_section(self) -> str:
        return """pytorch:
  models:nn.Module|forward()|to(device)
  train:zero_grad→forward→loss→backward→step
  data:Dataset|DataLoader|transforms
  device:cuda.is_available()|.to(device)
  save:state_dict()|load_state_dict()"""

    def _pandas_section(self) -> str:
        return """pandas:
  read:pd.read_csv/parquet/sql
  transform:df[col]|.apply()|.map()
  filter:df[df.col>x]|.query()
  group:groupby().agg()
  merge:pd.merge()|.join()"""


# Convenience function
def get_python_practices(
    level: CompressionLevel = CompressionLevel.STANDARD,
    frameworks: List[str] = None
) -> str:
    """Get compressed Python best practices"""
    provider = PythonBestPractices()
    return provider.compress(level=level, frameworks=frameworks)
```

#### Task 2.3: Create TypeScript Best Practices Provider

**File:** .codetrellis/best_practices/languages/typescript_practices.py`

```python
"""
TypeScript Best Practices Provider
==================================

Compresses TypeScript best practices into token-efficient formats.
"""

from typing import List, Optional
from ..base import BestPracticesProvider, BestPracticesSection, CompressionLevel


class TypeScriptBestPractices(BestPracticesProvider):
    """Provides compressed TypeScript best practices"""

    @property
    def language(self) -> str:
        return "typescript"

    @property
    def sections(self) -> List[BestPracticesSection]:
        return [
            BestPracticesSection(
                name="naming",
                content="variable|function|method=camelCase|Class|Interface|Type=PascalCase|CONSTANT=UPPER_SNAKE|_private|#private(ES2022)",
                priority=10,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="types",
                content="prefer_interface(extendable)|avoid_any→unknown|strict_mode|no_implicit_any|strict_null_checks",
                priority=10,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="type_definitions",
                content="primitives:string,number,boolean,null,undefined,symbol,bigint|Array<T>|T[]|Record<K,V>|Map<K,V>|Set<T>",
                priority=9,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="unions_guards",
                content="union:A|B|discriminated:{type:'a'}|{type:'b'}|intersection:A&B|guards:is,in,typeof,instanceof",
                priority=8,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="generics",
                content="<T>(x:T):T|constraints:<T extends Base>|defaults:<T=string>|infer:infer R",
                priority=8,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="utility_types",
                content="Partial<T>|Required<T>|Readonly<T>|Pick<T,K>|Omit<T,K>|Record<K,V>|ReturnType<F>|Parameters<F>|Awaited<P>",
                priority=7,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="functions",
                content="typed_params|explicit_return|overloads|arrow_preferred|async/await>promises",
                priority=8,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="modules",
                content="named_exports_preferred|barrel_files(index.ts)|path_aliases(@/)|tree_shaking",
                priority=6,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="async",
                content="Promise<T>|async/await|Promise.all/allSettled/race|AbortController",
                priority=7,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="config",
                content="strict:true|noUncheckedIndexedAccess|exactOptionalPropertyTypes|esModuleInterop",
                priority=6,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="tools",
                content="eslint(@typescript-eslint)|prettier|tsc --noEmit|vitest/jest",
                priority=5,
                tokens_estimate=15
            ),
        ]

    def compress(
        self,
        level: CompressionLevel = CompressionLevel.STANDARD,
        frameworks: List[str] = None,
        max_tokens: int = None
    ) -> str:
        """Compress TypeScript best practices"""
        token_limits = {
            CompressionLevel.MINIMAL: 100,
            CompressionLevel.STANDARD: 250,
            CompressionLevel.COMPREHENSIVE: 400,
        }

        budget = max_tokens or token_limits.get(level, 250)
        sections = sorted(self.sections, key=lambda x: x.priority, reverse=True)

        lines = ["[TYPESCRIPT_BEST_PRACTICES]"]
        lines.append("# TypeScript 5.x | Strict Mode | ESLint Compliant")
        lines.append("")

        current_tokens = 15

        for section in sections:
            if current_tokens + section.tokens_estimate <= budget:
                lines.append(f"## {section.name.upper()}")
                lines.append(section.content)
                lines.append("")
                current_tokens += section.tokens_estimate

        return "\n".join(lines).strip()
```

#### Task 2.4: Create Angular Best Practices Provider

**File:** .codetrellis/best_practices/frameworks/angular_practices.py`

```python
"""
Angular Best Practices Provider
===============================

Angular 17+ with Standalone Components and Signals.
"""

from typing import List, Optional
from ..base import BestPracticesProvider, BestPracticesSection, CompressionLevel


class AngularBestPractices(BestPracticesProvider):
    """Provides compressed Angular best practices"""

    @property
    def language(self) -> str:
        return "angular"

    @property
    def sections(self) -> List[BestPracticesSection]:
        return [
            BestPracticesSection(
                name="architecture",
                content="standalone_components(default)|lazy_loading|feature_modules|smart/dumb_components|barrel_exports",
                priority=10,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="components",
                content="@Component({standalone:true,imports:[]})|OnPush_CD|signals()|input()|output()|viewChild()",
                priority=10,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="signals",
                content="signal<T>()|computed()|effect()|input.required<T>()|model<T>()|toSignal()|toObservable()",
                priority=9,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="templates",
                content="@if/@else/@switch(new)|@for(track)|@defer/@loading/@error|ng-container|ng-template",
                priority=9,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="services",
                content="@Injectable({providedIn:'root'})|inject()|functional_guards|functional_resolvers|HttpClient",
                priority=8,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="state",
                content="NgRx_SignalStore|withState()|withComputed()|withMethods()|patchState()|rxMethod()",
                priority=8,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="routing",
                content="Routes[]|loadComponent()|loadChildren()|canActivate/canMatch(functional)|resolve",
                priority=7,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="forms",
                content="ReactiveFormsModule|FormControl<T>|FormGroup|FormArray|Validators|async_validators",
                priority=7,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="http",
                content="HttpClient|interceptors(functional)|withFetch()|typed_responses|catchError",
                priority=7,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="testing",
                content="TestBed|ComponentFixture|fakeAsync/tick|HttpTestingController|jest/vitest",
                priority=6,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="performance",
                content="OnPush|trackBy→track|@for>*ngFor|lazy_routes|defer_views",
                priority=7,
                tokens_estimate=20
            ),
        ]

    def compress(
        self,
        level: CompressionLevel = CompressionLevel.STANDARD,
        frameworks: List[str] = None,
        max_tokens: int = None
    ) -> str:
        """Compress Angular best practices"""
        token_limits = {
            CompressionLevel.MINIMAL: 120,
            CompressionLevel.STANDARD: 280,
            CompressionLevel.COMPREHENSIVE: 450,
        }

        budget = max_tokens or token_limits.get(level, 280)
        sections = sorted(self.sections, key=lambda x: x.priority, reverse=True)

        lines = ["[ANGULAR_BEST_PRACTICES]"]
        lines.append("# Angular 17+ | Standalone | Signals | OnPush")
        lines.append("")

        current_tokens = 15

        for section in sections:
            if current_tokens + section.tokens_estimate <= budget:
                lines.append(f"## {section.name.upper()}")
                lines.append(section.content)
                lines.append("")
                current_tokens += section.tokens_estimate

        return "\n".join(lines).strip()
```

#### Task 2.5: Create NestJS Best Practices Provider

**File:** .codetrellis/best_practices/frameworks/nestjs_practices.py`

```python
"""
NestJS Best Practices Provider
==============================

NestJS 10+ with TypeScript decorators.
"""

from typing import List, Optional
from ..base import BestPracticesProvider, BestPracticesSection, CompressionLevel


class NestJSBestPractices(BestPracticesProvider):
    """Provides compressed NestJS best practices"""

    @property
    def language(self) -> str:
        return "nestjs"

    @property
    def sections(self) -> List[BestPracticesSection]:
        return [
            BestPracticesSection(
                name="architecture",
                content="modules(@Module)|controllers(@Controller)|providers(@Injectable)|domain-driven|clean_architecture",
                priority=10,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="modules",
                content="@Module({imports,controllers,providers,exports})|forRoot()/forRootAsync()|dynamic_modules|global_modules",
                priority=9,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="controllers",
                content="@Controller('prefix')|@Get/@Post/@Put/@Delete/@Patch|@Param/@Query/@Body/@Headers|@Res(passthrough)",
                priority=9,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="providers",
                content="@Injectable()|constructor_injection|custom_providers(useClass,useValue,useFactory)|scope(REQUEST,TRANSIENT)",
                priority=8,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="dtos",
                content="class-validator(@IsString,@IsNumber,@IsOptional)|class-transformer(@Transform)|ValidationPipe(global)",
                priority=9,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="guards",
                content="@UseGuards()|CanActivate|ExecutionContext|@SetMetadata()|Reflector|JwtAuthGuard",
                priority=8,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="interceptors",
                content="@UseInterceptors()|NestInterceptor|CallHandler|map()|catchError()|timeout()",
                priority=7,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="exception_filters",
                content="@Catch()|ExceptionFilter|HttpException|custom_exceptions|global_filters",
                priority=8,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="database",
                content="TypeORM(@Entity,@Column,@Repository)|Prisma(PrismaService)|Mongoose(@Schema)|transactions",
                priority=7,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="auth",
                content="Passport(@UseGuards(AuthGuard))|JWT|@nestjs/jwt|strategies|@CurrentUser",
                priority=8,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="config",
                content="@nestjs/config|ConfigModule.forRoot()|ConfigService|env_validation(joi/zod)|typed_config",
                priority=6,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="swagger",
                content="@nestjs/swagger|@ApiTags|@ApiOperation|@ApiResponse|@ApiProperty|DocumentBuilder",
                priority=6,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="testing",
                content="@nestjs/testing|Test.createTestingModule|overrideProvider|mock_repos|e2e(supertest)",
                priority=6,
                tokens_estimate=25
            ),
        ]

    def compress(
        self,
        level: CompressionLevel = CompressionLevel.STANDARD,
        frameworks: List[str] = None,
        max_tokens: int = None
    ) -> str:
        """Compress NestJS best practices"""
        token_limits = {
            CompressionLevel.MINIMAL: 120,
            CompressionLevel.STANDARD: 300,
            CompressionLevel.COMPREHENSIVE: 500,
        }

        budget = max_tokens or token_limits.get(level, 300)
        sections = sorted(self.sections, key=lambda x: x.priority, reverse=True)

        lines = ["[NESTJS_BEST_PRACTICES]"]
        lines.append("# NestJS 10+ | TypeScript | Decorators | DI")
        lines.append("")

        current_tokens = 15

        for section in sections:
            if current_tokens + section.tokens_estimate <= budget:
                lines.append(f"## {section.name.upper()}")
                lines.append(section.content)
                lines.append("")
                current_tokens += section.tokens_estimate

        return "\n".join(lines).strip()
```

#### Task 2.6: Create Node.js/Express Best Practices Provider

**File:** .codetrellis/best_practices/frameworks/nodejs_practices.py`

```python
"""
Node.js/Express Best Practices Provider
=======================================

Node.js 20+ with ES Modules and Express/Fastify.
"""

from typing import List, Optional
from ..base import BestPracticesProvider, BestPracticesSection, CompressionLevel


class NodeJSBestPractices(BestPracticesProvider):
    """Provides compressed Node.js best practices"""

    @property
    def language(self) -> str:
        return "nodejs"

    @property
    def sections(self) -> List[BestPracticesSection]:
        return [
            BestPracticesSection(
                name="architecture",
                content="layered(controllers→services→repos)|clean_architecture|DI_container|error_middleware",
                priority=10,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="modules",
                content="ES_modules(import/export)|package.json:type=\"module\"|.mjs/.cjs|top-level_await",
                priority=9,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="express",
                content="app.use(middleware)|router.get/post/put/delete|req.params/query/body|res.json/status|next(err)",
                priority=9,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="middleware",
                content="(req,res,next)=>{}|error(err,req,res,next)|async_wrapper|helmet|cors|compression|morgan",
                priority=8,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="error_handling",
                content="custom_errors(extends Error)|async_wrapper|global_handler|operational_vs_programmer|process.on('uncaughtException')",
                priority=9,
                tokens_estimate=30
            ),
            BestPracticesSection(
                name="validation",
                content="joi/zod/yup|validate_early|sanitize_input|express-validator|ajv(JSON_Schema)",
                priority=8,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="database",
                content="connection_pooling|migrations|transactions|query_builders(knex)|ORMs(prisma,typeorm)",
                priority=7,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="auth",
                content="passport.js|JWT(jsonwebtoken)|bcrypt|sessions|OAuth2|refresh_tokens",
                priority=8,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="security",
                content="helmet|rate_limiting|CORS|input_validation|SQL_injection_prevention|XSS_protection",
                priority=8,
                tokens_estimate=25
            ),
            BestPracticesSection(
                name="async",
                content="async/await|Promise.all|worker_threads|cluster|streams|AbortController",
                priority=7,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="logging",
                content="winston/pino|structured_logging|log_levels|request_id|no_console.log_prod",
                priority=6,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="env",
                content="dotenv|env_validation|secrets_management|config_per_env|never_commit_.env",
                priority=7,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="testing",
                content="jest/vitest/mocha|supertest(e2e)|sinon(mocks)|nyc/c8(coverage)",
                priority=6,
                tokens_estimate=20
            ),
            BestPracticesSection(
                name="pm2",
                content="pm2|cluster_mode|graceful_shutdown|health_checks|NODE_ENV",
                priority=5,
                tokens_estimate=20
            ),
        ]

    def compress(
        self,
        level: CompressionLevel = CompressionLevel.STANDARD,
        frameworks: List[str] = None,
        max_tokens: int = None
    ) -> str:
        """Compress Node.js best practices"""
        token_limits = {
            CompressionLevel.MINIMAL: 100,
            CompressionLevel.STANDARD: 280,
            CompressionLevel.COMPREHENSIVE: 450,
        }

        budget = max_tokens or token_limits.get(level, 280)
        sections = sorted(self.sections, key=lambda x: x.priority, reverse=True)

        lines = ["[NODEJS_BEST_PRACTICES]"]
        lines.append("# Node.js 20+ | ES Modules | Express/Fastify")
        lines.append("")

        current_tokens = 15

        for section in sections:
            if current_tokens + section.tokens_estimate <= budget:
                lines.append(f"## {section.name.upper()}")
                lines.append(section.content)
                lines.append("")
                current_tokens += section.tokens_estimate

        return "\n".join(lines).strip()
```

#### Task 2.7: Create Best Practices Registry

**File:** .codetrellis/best_practices/registry.py`

```python
"""
Best Practices Registry
=======================

Central registry for all language and framework best practices providers.
"""

from typing import Dict, List, Optional, Type
from .base import BestPracticesProvider, CompressionLevel
from .languages.python_practices import PythonBestPractices
from .languages.typescript_practices import TypeScriptBestPractices
from .frameworks.angular_practices import AngularBestPractices
from .frameworks.nestjs_practices import NestJSBestPractices
from .frameworks.nodejs_practices import NodeJSBestPractices


class BestPracticesRegistry:
    """
    Registry for managing best practices providers.

    Supports:
    - Language-level practices (Python, TypeScript, JavaScript)
    - Framework-level practices (Angular, NestJS, React, etc.)
    - Automatic selection based on detected languages/frameworks
    """

    # Language providers
    LANGUAGE_PROVIDERS: Dict[str, Type[BestPracticesProvider]] = {
        "python": PythonBestPractices,
        "typescript": TypeScriptBestPractices,
        "javascript": TypeScriptBestPractices,  # JS uses TS practices (subset)
    }

    # Framework providers (augment language practices)
    FRAMEWORK_PROVIDERS: Dict[str, Type[BestPracticesProvider]] = {
        "angular": AngularBestPractices,
        "nestjs": NestJSBestPractices,
        "express": NodeJSBestPractices,
        "nodejs": NodeJSBestPractices,
        "fastapi": None,  # Uses Python practices with fastapi section
        "flask": None,    # Uses Python practices with flask section
        "django": None,   # Uses Python practices with django section
        "react": None,    # Future: ReactBestPractices
        "vue": None,      # Future: VueBestPractices
        "nextjs": None,   # Future: NextJSBestPractices
    }

    @classmethod
    def get_language_provider(cls, language: str) -> Optional[BestPracticesProvider]:
        """Get provider for a language"""
        provider_cls = cls.LANGUAGE_PROVIDERS.get(language.lower())
        return provider_cls() if provider_cls else None

    @classmethod
    def get_framework_provider(cls, framework: str) -> Optional[BestPracticesProvider]:
        """Get provider for a framework"""
        provider_cls = cls.FRAMEWORK_PROVIDERS.get(framework.lower())
        return provider_cls() if provider_cls else None

    @classmethod
    def get_practices_for_project(
        cls,
        languages: List[str],
        frameworks: List[str],
        level: CompressionLevel = CompressionLevel.STANDARD,
        max_total_tokens: int = 800
    ) -> str:
        """
        Get combined best practices for a project based on detected languages/frameworks.

        Args:
            languages: List of detected languages (e.g., ["python", "typescript"])
            frameworks: List of detected frameworks (e.g., ["angular", "fastapi"])
            level: Compression level
            max_total_tokens: Maximum total tokens across all practices

        Returns:
            Combined best practices string
        """
        practices_parts = []
        tokens_used = 0
        tokens_per_section = max_total_tokens // max(len(languages) + len(frameworks), 1)

        # Add language practices
        for lang in languages:
            provider = cls.get_language_provider(lang)
            if provider:
                # Adjust tokens based on frameworks for this language
                lang_frameworks = [f for f in frameworks if cls._framework_uses_language(f, lang)]
                practices = provider.compress(
                    level=level,
                    frameworks=lang_frameworks,
                    max_tokens=tokens_per_section
                )
                practices_parts.append(practices)
                tokens_used += tokens_per_section

        # Add framework-specific practices (if they have their own provider)
        for framework in frameworks:
            provider = cls.get_framework_provider(framework)
            if provider:
                remaining_tokens = max_total_tokens - tokens_used
                if remaining_tokens > 100:
                    practices = provider.compress(
                        level=level,
                        max_tokens=min(tokens_per_section, remaining_tokens)
                    )
                    practices_parts.append(practices)
                    tokens_used += tokens_per_section

        return "\n\n".join(practices_parts)

    @classmethod
    def _framework_uses_language(cls, framework: str, language: str) -> bool:
        """Check if a framework uses a specific language"""
        framework_languages = {
            "angular": "typescript",
            "nestjs": "typescript",
            "react": "typescript",  # Can be JS too, but TS preferred
            "vue": "typescript",
            "nextjs": "typescript",
            "express": "javascript",
            "nodejs": "javascript",
            "fastapi": "python",
            "flask": "python",
            "django": "python",
            "pytorch": "python",
            "pandas": "python",
        }
        return framework_languages.get(framework.lower()) == language.lower()


def get_best_practices(
    languages: List[str],
    frameworks: List[str] = None,
    level: CompressionLevel = CompressionLevel.STANDARD,
    max_tokens: int = 800
) -> str:
    """
    Convenience function to get best practices for a project.

    Example:
        practices = get_best_practices(
            languages=["typescript", "python"],
            frameworks=["angular", "fastapi"],
            level=CompressionLevel.STANDARD
        )
    """
    return BestPracticesRegistry.get_practices_for_project(
        languages=languages,
        frameworks=frameworks or [],
        level=level,
        max_total_tokens=max_tokens
    )
```

### Phase 3: CLI Integration (Week 2)

#### Task 3.1: Add CLI Flags

**File:** .codetrellis/cli.py` - Add new arguments

```python
# In main() function, add to argparse:

# Best practices flags
scan_parser.add_argument(
    "--best-practices", "--bp",
    action="store_true",
    help="Include language-specific best practices in output"
)

scan_parser.add_argument(
    "--bp-level",
    choices=["minimal", "standard", "comprehensive"],
    default="standard",
    help="Best practices compression level (default: standard)"
)

prompt_parser.add_argument(
    "--best-practices", "--bp",
    action="store_true",
    help="Include language-specific best practices in output"
)

prompt_parser.add_argument(
    "--bp-level",
    choices=["minimal", "standard", "comprehensive"],
    default="standard",
    help="Best practices compression level (default: standard)"
)
```

#### Task 3.2: Integrate into Output Generation

**File:** .codetrellis/cli.py` - Modify output functions

```python
def _append_best_practices(
    content: str,
    language_analysis: LanguageAnalysis,
    level: CompressionLevel = CompressionLevel.STANDARD
) -> str:
    """Append language-specific best practices to output"""
    from.codetrellis.best_practices.registry import BestPracticesRegistry, get_best_practices

    # Collect significant languages
    significant_languages = [
        lang.value for lang, stats in language_analysis.languages.items()
        if stats.is_significant or stats.is_primary
    ]

    # Collect detected frameworks
    frameworks = []
    for lang, stats in language_analysis.languages.items():
        frameworks.extend(stats.frameworks)

    if significant_languages:
        practices = get_best_practices(
            languages=significant_languages,
            frameworks=frameworks,
            level=level,
            max_tokens=800  # Total budget for all practices
        )

        if practices:
            content += "\n\n" + practices

    return content
```

### Phase 4: Testing & Documentation (Week 2-3)

#### Task 4.1: Unit Tests

**File:** `tests/test_language_analyzer.py`

```python
"""Tests for language analyzer"""

import pytest
from pathlib import Path
from.codetrellis.analyzers.language_analyzer import LanguageAnalyzer, Language, Framework


class TestLanguageAnalyzer:

    @pytest.fixture
    def analyzer(self):
        return LanguageAnalyzer()

    def test_python_detection(self, analyzer, tmp_path):
        """Test Python file detection"""
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def func(): pass")

        result = analyzer.analyze(tmp_path)

        assert result.primary_language == Language.PYTHON
        assert result.languages[Language.PYTHON].file_count == 2
        assert result.languages[Language.PYTHON].percentage == 100.0

    def test_typescript_detection(self, analyzer, tmp_path):
        """Test TypeScript file detection"""
        (tmp_path / "app.component.ts").write_text("export class AppComponent {}")
        (tmp_path / "main.ts").write_text("import { bootstrap } from '@angular/core';")

        result = analyzer.analyze(tmp_path)

        assert result.primary_language == Language.TYPESCRIPT
        assert Language.TYPESCRIPT in result.languages

    def test_mixed_languages(self, analyzer, tmp_path):
        """Test mixed language detection"""
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "app.ts").write_text("const x = 1;")
        (tmp_path / "server.js").write_text("console.log('hi');")

        result = analyzer.analyze(tmp_path)

        assert Language.PYTHON in result.languages
        assert Language.TYPESCRIPT in result.languages
        assert Language.JAVASCRIPT in result.languages

    def test_angular_framework_detection(self, analyzer, tmp_path):
        """Test Angular framework detection"""
        (tmp_path / "package.json").write_text('{"dependencies": {"@angular/core": "^17.0.0"}}')
        (tmp_path / "angular.json").write_text('{}')
        (tmp_path / "app.component.ts").write_text("@Component({})")

        result = analyzer.analyze(tmp_path)

        ts_stats = result.languages[Language.TYPESCRIPT]
        assert Framework.ANGULAR in ts_stats.frameworks

    def test_nestjs_framework_detection(self, analyzer, tmp_path):
        """Test NestJS framework detection"""
        (tmp_path / "package.json").write_text('{"dependencies": {"@nestjs/core": "^10.0.0"}}')
        (tmp_path / "app.module.ts").write_text("@Module({})")

        result = analyzer.analyze(tmp_path)

        ts_stats = result.languages[Language.TYPESCRIPT]
        assert Framework.NESTJS in ts_stats.frameworks

    def test_fastapi_framework_detection(self, analyzer, tmp_path):
        """Test FastAPI framework detection"""
        (tmp_path / "requirements.txt").write_text("fastapi==0.100.0\npydantic==2.0")
        (tmp_path / "main.py").write_text("from fastapi import FastAPI")

        result = analyzer.analyze(tmp_path)

        python_stats = result.languages[Language.PYTHON]
        assert Framework.FASTAPI in python_stats.frameworks

    def test_fullstack_project_detection(self, analyzer, tmp_path):
        """Test fullstack project with multiple frameworks"""
        # Backend (NestJS)
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "package.json").write_text('{"dependencies": {"@nestjs/core": "^10.0.0"}}')
        (backend / "app.module.ts").write_text("@Module({})")

        # Frontend (Angular)
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text('{"dependencies": {"@angular/core": "^17.0.0"}}')
        (frontend / "app.component.ts").write_text("@Component({})")

        result = analyzer.analyze(tmp_path)

        assert result.project_type == "fullstack"
        assert Framework.ANGULAR in result.detected_frameworks
        assert Framework.NESTJS in result.detected_frameworks
```

**File:** `tests/test_best_practices.py`

```python
"""Tests for best practices compression"""

import pytest
from.codetrellis.best_practices import CompressionLevel
from.codetrellis.best_practices.languages.python_practices import PythonBestPractices
from.codetrellis.best_practices.languages.typescript_practices import TypeScriptBestPractices
from.codetrellis.best_practices.frameworks.angular_practices import AngularBestPractices
from.codetrellis.best_practices.frameworks.nestjs_practices import NestJSBestPractices
from.codetrellis.best_practices.frameworks.nodejs_practices import NodeJSBestPractices
from.codetrellis.best_practices.registry import get_best_practices


class TestPythonBestPractices:

    @pytest.fixture
    def provider(self):
        return PythonBestPractices()

    def test_minimal_compression(self, provider):
        result = provider.compress(level=CompressionLevel.MINIMAL)
        tokens_estimate = len(result) / 4
        assert tokens_estimate < 150
        assert "[PYTHON_BEST_PRACTICES]" in result

    def test_standard_compression(self, provider):
        result = provider.compress(level=CompressionLevel.STANDARD)
        tokens_estimate = len(result) / 4
        assert 150 < tokens_estimate < 350
        assert "## NAMING" in result

    def test_framework_specific(self, provider):
        result = provider.compress(level=CompressionLevel.STANDARD, frameworks=["fastapi"])
        assert "fastapi:" in result


class TestTypeScriptBestPractices:

    @pytest.fixture
    def provider(self):
        return TypeScriptBestPractices()

    def test_standard_compression(self, provider):
        result = provider.compress(level=CompressionLevel.STANDARD)
        assert "[TYPESCRIPT_BEST_PRACTICES]" in result
        assert "## NAMING" in result
        assert "## TYPES" in result

    def test_utility_types_included(self, provider):
        result = provider.compress(level=CompressionLevel.COMPREHENSIVE)
        assert "Partial<T>" in result
        assert "Record<K,V>" in result


class TestAngularBestPractices:

    @pytest.fixture
    def provider(self):
        return AngularBestPractices()

    def test_standard_compression(self, provider):
        result = provider.compress(level=CompressionLevel.STANDARD)
        assert "[ANGULAR_BEST_PRACTICES]" in result
        assert "standalone" in result.lower()
        assert "signal" in result.lower()

    def test_modern_features_included(self, provider):
        result = provider.compress(level=CompressionLevel.COMPREHENSIVE)
        assert "OnPush" in result
        assert "@if" in result or "@for" in result


class TestNestJSBestPractices:

    @pytest.fixture
    def provider(self):
        return NestJSBestPractices()

    def test_standard_compression(self, provider):
        result = provider.compress(level=CompressionLevel.STANDARD)
        assert "[NESTJS_BEST_PRACTICES]" in result
        assert "@Module" in result or "modules" in result.lower()
        assert "@Controller" in result or "controllers" in result.lower()

    def test_decorators_included(self, provider):
        result = provider.compress(level=CompressionLevel.COMPREHENSIVE)
        assert "@Injectable" in result or "providers" in result.lower()


class TestNodeJSBestPractices:

    @pytest.fixture
    def provider(self):
        return NodeJSBestPractices()

    def test_standard_compression(self, provider):
        result = provider.compress(level=CompressionLevel.STANDARD)
        assert "[NODEJS_BEST_PRACTICES]" in result
        assert "express" in result.lower() or "middleware" in result.lower()


class TestBestPracticesRegistry:

    def test_single_language(self):
        result = get_best_practices(languages=["python"])
        assert "[PYTHON_BEST_PRACTICES]" in result

    def test_typescript_with_angular(self):
        result = get_best_practices(
            languages=["typescript"],
            frameworks=["angular"]
        )
        assert "[TYPESCRIPT_BEST_PRACTICES]" in result
        assert "[ANGULAR_BEST_PRACTICES]" in result

    def test_typescript_with_nestjs(self):
        result = get_best_practices(
            languages=["typescript"],
            frameworks=["nestjs"]
        )
        assert "[TYPESCRIPT_BEST_PRACTICES]" in result
        assert "[NESTJS_BEST_PRACTICES]" in result

    def test_fullstack_project(self):
        result = get_best_practices(
            languages=["typescript", "python"],
            frameworks=["angular", "fastapi"],
            max_tokens=1200
        )
        assert "[TYPESCRIPT_BEST_PRACTICES]" in result
        assert "[PYTHON_BEST_PRACTICES]" in result
        assert "[ANGULAR_BEST_PRACTICES]" in result
        assert "fastapi:" in result

    def test_token_budget_respected(self):
        result = get_best_practices(
            languages=["typescript", "python"],
            frameworks=["angular", "nestjs"],
            max_tokens=400  # Tight budget
        )
        # Should have some content but be limited
        assert len(result) < 2000  # ~500 tokens max
```

#### Task 4.2: Update README

Add to CodeTrellis README:

````markdown
## Best Practices Integration (v4.2+)

CodeTrellis can automatically detect the programming languages used in your project
and append compressed best practices to generated prompts.

### Usage

```bash
# Include best practices in scan output
codetrellis scan /path/to/project --best-practices

# Specify compression level
codetrellis scan /path/to/project --bp --bp-level comprehensive

# In prompt mode
codetrellis prompt --best-practices
```
````

### Compression Levels

| Level         | Tokens | Best For                             |
| ------------- | ------ | ------------------------------------ |
| minimal       | ~100   | Tight token budgets, basic reference |
| standard      | ~250   | General use, balanced coverage       |
| comprehensive | ~400   | Full guidance, complex projects      |

### Supported Languages

- ✅ Python (with framework support: FastAPI, Flask, Django, PyTorch, Pandas)
- 🔜 TypeScript/JavaScript
- 🔜 Go
- 🔜 Rust

````

---

## Part 4: CLI Usage Examples

### 4.1 New CLI Commands

```bash
# Basic scan with Python best practices
codetrellis scan /my/python/project --best-practices

# Short form
codetrellis scan /my/project --bp

# With specific compression level
codetrellis scan /my/project --bp --bp-level minimal
codetrellis scan /my/project --bp --bp-level comprehensive

# Combined with existing flags
codetrellis scan /my/project --tier prompt --bp --bp-level standard
codetrellis scan /my/project --tier logic --bp --deep

# Prompt output with best practices
codetrellis prompt --bp
codetrellis prompt --bp --bp-level comprehensive
````

### 4.2 Example Output

```
# CodeTrellis Matrix v4.2.0 [LOGIC] | my-fastapi-app | 2026-02-03

[PROJECT]
name=my-fastapi-app
type=FastAPI

[LANGUAGE_ANALYSIS]
primary=python|100%
frameworks=fastapi,pydantic,sqlalchemy

[COMPONENTS]
...existing CodeTrellis output...

[PYTHON_BEST_PRACTICES]
# PEP8|PEP20|PEP484|PEP257 Compliant

## NAMING
var|func|method=snake_case|Class=PascalCase|CONST=UPPER_SNAKE|_protected|__private|__dunder__

## STYLE
indent=4spaces|max_line=79|imports:stdlib→3rdparty→local|quotes=consistent|blank:2(top),1(method)

## TYPE_HINTS
basic:str,int,float,bool,None|List[T],Dict[K,V],Set[T],Tuple[T,...]|Optional[T]=T|None|Union→|(3.10+)

## IDIOMS
comprehensions>map/filter|f-strings>format|enumerate>range(len)|with(context)|unpacking|truthiness(if x:)

## FASTAPI
fastapi:
  routes:@app.get/post|async def|->Response
  models:BaseModel|Field()|validator
  deps:Depends()|get_db|auth
  errors:HTTPException(status,detail)
  docs:summary,description,tags
```

---

## Part 5: Future Enhancements

### 5.1 Additional Languages (Phase 2)

| Language              | Priority | Estimated Effort |
| --------------------- | -------- | ---------------- |
| TypeScript/JavaScript | High     | 2 weeks          |
| Go                    | Medium   | 1 week           |
| Rust                  | Medium   | 1 week           |
| Java                  | Low      | 2 weeks          |
| C#                    | Low      | 2 weeks          |

### 5.2 Context-Aware Selection (Phase 3)

- Detect current file type and prioritize relevant sections
- Learn from project patterns to suggest relevant practices
- Integrate with IDE extensions for real-time suggestions

### 5.3 Custom Best Practices (Phase 3)

- Allow projects to define custom `.codetrellis/best-practices.yaml`
- Merge with built-in practices
- Support team-specific guidelines

---

## Part 6: Implementation Timeline

| Week | Tasks                              | Deliverables                             |
| ---- | ---------------------------------- | ---------------------------------------- |
| 1    | Language Analyzer, Basic Structure | `language_analyzer.py`, tests            |
| 1-2  | Best Practices Provider            | `python_practices.py`, compression logic |
| 2    | CLI Integration                    | New flags, output integration            |
| 2-3  | Testing & Documentation            | Test suite, updated README               |
| 3    | Polish & Release                   | CodeTrellis v4.2.0 release                      |

---

## Part 6: Implementation Timeline (Multi-Language)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-LANGUAGE BEST PRACTICES INTEGRATION                     │
│                              Total Duration: 4-5 Weeks                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│ WEEK 1: Foundation                                                               │
│ ├── Day 1-2: Language Analyzer Core                                              │
│ │   ├── Implement LanguageAnalyzer class                                         │
│ │   ├── Add multi-language detection (Python, TypeScript, JavaScript)            │
│ │   └── Add framework enum and basic detection                                   │
│ ├── Day 3-4: Best Practices Architecture                                         │
│ │   ├── Create base classes (Provider, Section, Level)                           │
│ │   ├── Implement BestPracticesRegistry                                          │
│ │   └── Create Python provider                                                   │
│ └── Day 5: Framework Detection Enhancement                                       │
│     ├── Angular detection (angular.json, @angular/core)                          │
│     ├── NestJS detection (@nestjs/core, modules pattern)                         │
│     └── Express/Node.js detection                                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│ WEEK 2: Language Providers                                                       │
│ ├── Day 1-2: TypeScript Provider                                                 │
│ │   ├── Implement TypeScriptBestPractices                                        │
│ │   ├── Add strict mode and type system sections                                 │
│ │   └── Test compression levels                                                  │
│ ├── Day 3-4: Frontend Framework Providers                                        │
│ │   ├── Implement AngularBestPractices                                           │
│ │   ├── Implement ReactBestPractices                                             │
│ │   └── Implement VueBestPractices                                               │
│ └── Day 5: Backend Framework Providers                                           │
│     ├── Implement NestJSBestPractices                                            │
│     └── Implement NodeJSBestPractices                                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│ WEEK 3: CLI Integration                                                          │
│ ├── Day 1-2: CLI Flag Implementation                                             │
│ │   ├── Add --best-practices / --bp flag                                         │
│ │   ├── Add --bp-level [minimal|standard|comprehensive]                          │
│ │   └── Add --bp-only [lang1,lang2] for filtering                                │
│ ├── Day 3-4: Output Integration                                                  │
│ │   ├── Integrate with existing prompt generation                                │
│ │   ├── Add intelligent practice selection based on analysis                     │
│ │   └── Implement token budget management                                        │
│ └── Day 5: Testing                                                               │
│     ├── Unit tests for all providers                                             │
│     └── Integration tests for CLI                                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│ WEEK 4: Polish & Documentation                                                   │
│ ├── Day 1-2: Additional Providers                                                │
│ │   ├── Add Next.js provider                                                     │
│ │   ├── Add Flask/Django-specific sections to Python                             │
│ │   └── Add more AI/ML framework practices                                       │
│ ├── Day 3-4: Documentation                                                       │
│ │   ├── Update CLI help text                                                     │
│ │   ├── Write usage guide                                                        │
│ │   └── Add examples to README                                                   │
│ └── Day 5: Final Testing & Release                                               │
│     ├── End-to-end testing                                                       │
│     └── Version bump to 4.2.0                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ WEEK 5 (Optional): Advanced Features                                             │
│ ├── Custom practice file support (.codetrellis-practices.yaml)                          │
│ ├── Practice caching for faster generation                                       │
│ ├── Interactive mode for practice selection                                      │
│ └── IDE integration (VS Code extension)                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 7: Success Metrics

| Metric                       | Target | Measurement                                                  |
| ---------------------------- | ------ | ------------------------------------------------------------ |
| Language Detection Accuracy  | 99%    | Unit tests covering Python, TS, JS                           |
| Framework Detection Accuracy | 95%    | Unit tests for Angular, NestJS, React, Vue, Express, FastAPI |
| Compression Ratio            | 95%+   | Each MD source → ~250 tokens (standard)                      |
| Token Budget Compliance      | 100%   | All levels within ±10% target                                |
| Multi-Framework Projects     | 100%   | Correctly identifies fullstack projects                      |
| Practice Combination         | 100%   | No duplicates, proper ordering                               |
| User Adoption                | 50%+   | Usage analytics                                              |
| Performance                  | <500ms | Practices appended within scan time                          |

---

## Appendix A: Compressed Best Practices Templates

### A.1: Python (STANDARD ~250 tokens)

```
[PYTHON_BEST_PRACTICES]
# PEP8|PEP20|PEP484|PEP257 Compliant

## NAMING
var|func|method=snake_case|Class=PascalCase|CONST=UPPER_SNAKE|_protected|__private|__dunder__

## STYLE
indent=4spaces|max_line=79|imports:stdlib→3rdparty→local|quotes=consistent|blank:2(top),1(method)

## TYPE_HINTS
basic:str,int,float,bool,None|List[T],Dict[K,V],Set[T],Tuple[T,...]|Optional[T]=T|None|Union→|(3.10+)

## IDIOMS
comprehensions>map/filter|f-strings>format|enumerate>range(len)|with(context)|unpacking|truthiness(if x:)

## ERROR_HANDLING
specific_except|raise_from|custom_errors(Exception)|with(cleanup)|no_bare_except|no_pass_silently

## DOCSTRINGS
"""One-line."""|"""Multi.\n\nArgs:\n    p:Desc.\n\nReturns:\n    Desc.\nRaises:\n    Err:When."""

## PROJECT
src/pkg/|tests/|pyproject.toml|requirements.txt|.venv/

## TESTING
pytest|@fixture|@parametrize|mock.patch|assert|coverage>80%

## SECURITY
pydantic(validate)|env_vars(settings)|passlib(hash)|jose(jwt)|no_secrets_in_code

## ASYNC
asyncio|async/await|aiohttp|gather(*tasks)|TaskGroup(3.11+)

## TOOLS
black(fmt)|ruff(lint)|mypy(types)|pytest(test)|pre-commit
```

### A.2: TypeScript (STANDARD ~250 tokens)

```
[TYPESCRIPT_BEST_PRACTICES]
# TS5.0+|ESNext|strict_mode

## NAMING
var|func=camelCase|Class|Interface|Type=PascalCase|CONST=UPPER_SNAKE|_private|#private(ES2022)

## TYPES
strict:noImplicitAny,strictNullChecks|interface>type(extend)|generics<T extends Base>|as_const|satisfies

## UTILITY_TYPES
Partial<T>|Required<T>|Pick<T,K>|Omit<T,K>|Record<K,V>|ReturnType<F>|Parameters<F>|Awaited<T>

## PATTERNS
discriminated_unions|exhaustive_switch|type_guards(is)|assertion_funcs(asserts)|branded_types

## MODULES
barrel_exports(index.ts)|named>default|import_type{type T}|path_aliases(@/)|ESM>CJS

## ERROR
Result<T,E>_pattern|never_throw_strings|custom_errors(Error)|try/catch(typed)|Error.cause

## ASYNC
Promise<T>|async/await|Promise.all/allSettled|AbortController|for_await_of

## TOOLS
tsc(--strict)|eslint(@typescript-eslint)|prettier|vitest|tsx(run)|tsup(build)
```

### A.3: Angular (STANDARD ~250 tokens)

```
[ANGULAR_BEST_PRACTICES]
# Angular17+|Standalone|Signals

## COMPONENTS
standalone:true(default)|changeDetection:OnPush|signals():input|output|computed|effect

## TEMPLATES
@if/@else|@for(track item.id)|@switch/@case|@defer/@placeholder/@loading|ng-container

## SERVICES
@Injectable({providedIn:'root'})|inject()>constructor|BehaviorSubject|toSignal(obs)

## ROUTING
lazy_load:loadComponent|guards:CanActivateFn|resolvers|RouterLink|withViewTransitions()

## FORMS
reactive>template|FormGroup|FormArray|validators(Validators)|touched|dirty|errors

## STATE
signals>observables|computed()_derived|effect()_sideeffects|toSignal/toObservable

## TESTING
TestBed|ComponentFixture|provideHttpClientTesting|fakeAsync/tick|jest>karma

## STRUCTURE
feature/(components,services)|shared/(ui,utils)|core/guards|environments/

## TOOLS
ng_cli|eslint(angular-eslint)|prettier|husky|strict_mode
```

### A.4: NestJS (STANDARD ~250 tokens)

```
[NESTJS_BEST_PRACTICES]
# NestJS10+|TypeScript|DI

## ARCHITECTURE
@Module(imports,controllers,providers,exports)|single_responsibility|domain_driven

## CONTROLLERS
@Controller('path')|@Get/@Post/@Put/@Delete|@Param/@Query/@Body|@HttpCode|@Header

## SERVICES
@Injectable()|constructor_injection|interface_based|business_logic_only

## DTOs
class-validator|@IsString/@IsEmail/@IsOptional|class-transformer|ValidationPipe(global)

## GUARDS_PIPES_INTERCEPTORS
@UseGuards(AuthGuard)|@UsePipes(ValidationPipe)|@UseInterceptors()|ExecutionContext

## DATABASE
TypeORM/Prisma/@nestjs/mongoose|Repository_pattern|transactions|migrations

## TESTING
@nestjs/testing|Test.createTestingModule|jest.mock|supertest(e2e)|Test containers

## SECURITY
helmet|cors|rate-limit|jwt(@nestjs/jwt)|passport(@nestjs/passport)|bcrypt

## TOOLS
nest_cli|swagger(@nestjs/swagger)|config(@nestjs/config)|class-validator
```

### A.5: Node.js/Express (STANDARD ~250 tokens)

```
[NODEJS_BEST_PRACTICES]
# Node20+|ESM|Express/Fastify

## STRUCTURE
src/(routes,controllers,services,models)|middleware/|config/|tests/|package.json(type:module)

## MIDDLEWARE
error_handler_last|async_wrapper|validation(joi/zod)|auth|cors|helmet|rate-limit

## ERROR_HANDLING
centralized_handler|custom_errors(AppError)|async/await+try/catch|process.on(uncaughtException)

## ASYNC
Promise.all/allSettled|async/await|streams(pipeline)|worker_threads|cluster

## SECURITY
helmet(headers)|cors(whitelist)|rate-limiting|input_validation|env_vars(dotenv)|no_secrets

## LOGGING
pino/winston|structured_json|log_levels|request_id_tracking|no_console.log_prod

## DATABASE
connection_pooling|prepared_statements|ORM(prisma/typeorm)|transactions|migrations

## TESTING
jest/vitest|supertest(http)|mock_dependencies|integration+unit|test_containers

## PERFORMANCE
compression|caching(redis)|lazy_loading|connection_pooling|pm2(cluster)|profiling
```

---

## Appendix B: File Structure After Implementation

```
codetrellis/
├── __init__.py
├── cli.py                           # Updated with --bp flags
├── scanner.py                       # Updated with language analysis
├── compressor.py
├── analyzers/                       # NEW DIRECTORY
│   ├── __init__.py
│   └── language_analyzer.py         # Language & framework detection
├── best_practices/                  # NEW DIRECTORY
│   ├── __init__.py                  # Exports all providers
│   ├── base.py                      # Abstract base classes
│   ├── registry.py                  # Provider registry & get_best_practices()
│   ├── languages/                   # Language-specific providers
│   │   ├── __init__.py
│   │   ├── python_practices.py
│   │   ├── typescript_practices.py
│   │   └── javascript_practices.py
│   ├── frameworks/                  # Framework-specific providers
│   │   ├── __init__.py
│   │   ├── angular_practices.py
│   │   ├── nestjs_practices.py
│   │   ├── nodejs_practices.py
│   │   ├── react_practices.py
│   │   ├── vue_practices.py
│   │   └── nextjs_practices.py
│   └── templates/                   # Pre-compressed text templates
│       ├── python_minimal.txt
│       ├── python_standard.txt
│       ├── python_comprehensive.txt
│       ├── typescript_standard.txt
│       ├── angular_standard.txt
│       └── ... (other templates)
├── extractors/
│   └── ... (existing)
├── parsers/
│   └── ... (existing)
└── plugins/
    └── ... (existing)

tests/
├── test_language_analyzer.py        # NEW: Tests language detection
├── test_best_practices.py           # NEW: Tests all providers
├── test_best_practices_registry.py  # NEW: Tests registry & combinations
└── ... (existing)
```

---

## Appendix C: CLI Usage Examples

### Basic Usage

```bash
# Scan with best practices (auto-detects languages)
codetrellis scan --best-practices

# Short form
codetrellis scan --bp

# With compression level
codetrellis scan --bp --bp-level minimal
codetrellis scan --bp --bp-level comprehensive
```

### Language-Specific

```bash
# Python-only project
codetrellis scan --bp
# Output includes: [PYTHON_BEST_PRACTICES]

# TypeScript/Angular project
codetrellis scan --bp
# Output includes: [TYPESCRIPT_BEST_PRACTICES] + [ANGULAR_BEST_PRACTICES]

# Fullstack (NestJS + Angular)
codetrellis scan --bp
# Output includes: [TYPESCRIPT_BEST_PRACTICES] + [ANGULAR_BEST_PRACTICES] + [NESTJS_BEST_PRACTICES]
```

### Filtering & Control

```bash
# Only include specific languages
codetrellis scan --bp --bp-only python,typescript

# Exclude certain practices
codetrellis scan --bp --bp-exclude angular

# Set total token budget
codetrellis scan --bp --bp-tokens 500
```

### Prompt Generation

```bash
# Generate prompt with practices
codetrellis prompt --best-practices > context.md

# Combine with matrix compression
codetrellis prompt --tier prompt --best-practices > context.md

# For a specific directory
codetrellis prompt ./backend --bp --bp-level standard > backend-context.md
```

---

**Document Status:** Ready for Implementation
**Version:** 2.0.0
**Next Step:** Begin Phase 1 - Week 1 implementation
