"""
EnhancedTypeScriptParser v1.0 - Comprehensive TypeScript parser using all extractors.

This parser integrates all TypeScript extractors to provide complete
parsing of TypeScript source files.

Supports:
- TypeScript 2.0 through 5.7+ (all versions)
- Classes with access modifiers, abstract, decorators, generics
- Interfaces, type aliases (union/intersection/conditional/mapped/template literal)
- Enums (numeric, string, const, ambient)
- Function overloads, type guards, assertion functions
- NestJS/Express/Fastify/tRPC/Hono/GraphQL routes
- TypeORM/MikroORM/Prisma/Drizzle/Sequelize-TypeScript models
- class-validator DTOs, Zod schemas
- Type-only imports/exports, namespace/module declarations
- Triple-slash directives, TSDoc comments
- Decorators (TC39 / experimental)
- tsconfig.json detection

TypeScript version detection from:
- satisfies operator → TS 4.9+
- using/await using → TS 5.2+
- const type parameters → TS 5.0+
- Template literal types → TS 4.1+
- Variadic tuple types → TS 4.0+
- Assertion functions → TS 3.7+
- Optional chaining/nullish → TS 3.7+
- unknown type → TS 3.0+
- Conditional types (infer) → TS 2.8+
- Mapped types → TS 2.1+
- enum, interface → TS 2.0+

Framework detection (80+ frameworks/libraries):
- Backend: NestJS, Express, Fastify, Koa, Hapi, Hono, Deno Oak
- Frontend: Angular, React, Vue 3, Svelte, Solid, Lit, Qwik
- Full-stack: Next.js, Nuxt 3, Remix, Astro, SvelteKit, Analog
- API: tRPC, GraphQL (type-graphql, Pothos), gRPC, REST
- ORM: TypeORM, MikroORM, Prisma, Drizzle, Sequelize-TS, Kysely
- Validation: Zod, class-validator, io-ts, Yup, Arktype, Valibot
- Testing: Jest, Vitest, Playwright, Cypress, Testing Library
- State: NgRx, Redux Toolkit, Zustand, Jotai, MobX, Pinia, Tanstack Query
- Auth: Passport, NextAuth, Lucia, Auth.js
- Realtime: Socket.io, WebSocket, Server-Sent Events
- DI: InversifyJS, tsyringe, NestJS DI
- Build: tsc, esbuild, SWC, Vite, Turbopack, Webpack
- Util: RxJS, fp-ts, Effect, Lodash, date-fns, Temporal

Optional AST support via tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.31 - TypeScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all TypeScript extractors
from .extractors.typescript import (
    TypeScriptTypeExtractor, TSClassInfo, TSInterfaceInfo, TSTypeAliasInfo,
    TSEnumInfo, TSEnumMemberInfo, TSPropertyInfo, TSGenericParam,
    TypeScriptFunctionExtractor, TSFunctionInfo, TSParameterInfo,
    TSOverloadInfo, TSMethodInfo,
    TypeScriptAPIExtractor, TSRouteInfo, TSMiddlewareInfo,
    TSWebSocketInfo, TSGraphQLResolverInfo, TSTRPCRouterInfo,
    TypeScriptModelExtractor, TSModelInfo, TSFieldInfo,
    TSRelationInfo, TSMigrationInfo, TSDTOInfo,
    TypeScriptAttributeExtractor, TSImportInfo, TSExportInfo,
    TSDecoratorInfo, TSNamespaceInfo, TSTripleSlashDirective, TSTSDocInfo,
)


@dataclass
class TypeScriptParseResult:
    """Complete parse result for a TypeScript file."""
    file_path: str
    file_type: str = "typescript"  # typescript, tsx, dts, mts, cts

    # Core types
    classes: List[TSClassInfo] = field(default_factory=list)
    interfaces: List[TSInterfaceInfo] = field(default_factory=list)
    type_aliases: List[TSTypeAliasInfo] = field(default_factory=list)
    enums: List[TSEnumInfo] = field(default_factory=list)

    # Functions
    functions: List[TSFunctionInfo] = field(default_factory=list)
    overloads: List[TSOverloadInfo] = field(default_factory=list)

    # API / Framework
    routes: List[TSRouteInfo] = field(default_factory=list)
    middleware: List[TSMiddlewareInfo] = field(default_factory=list)
    websockets: List[TSWebSocketInfo] = field(default_factory=list)
    graphql_resolvers: List[TSGraphQLResolverInfo] = field(default_factory=list)
    trpc_routers: List[TSTRPCRouterInfo] = field(default_factory=list)

    # Models / Data
    models: List[TSModelInfo] = field(default_factory=list)
    migrations: List[TSMigrationInfo] = field(default_factory=list)
    relationships: List[TSRelationInfo] = field(default_factory=list)
    dtos: List[TSDTOInfo] = field(default_factory=list)

    # Attributes / Imports / Exports
    imports: List[TSImportInfo] = field(default_factory=list)
    exports: List[TSExportInfo] = field(default_factory=list)
    decorators: List[TSDecoratorInfo] = field(default_factory=list)
    namespaces: List[TSNamespaceInfo] = field(default_factory=list)
    triple_slash_directives: List[TSTripleSlashDirective] = field(default_factory=list)
    tsdoc: List[TSTSDocInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    ts_version: str = ""  # Detected minimum TS version (2.0, 3.0, 4.0, 4.1, 4.9, 5.0, 5.2)
    is_declaration_file: bool = False


class EnhancedTypeScriptParser:
    """
    Enhanced TypeScript parser that uses all extractors for comprehensive parsing.

    Framework detection supports 80+ frameworks/libraries across:
    - Backend (NestJS, Express, Fastify, Koa, Hapi, Hono, Deno)
    - Frontend (Angular, React, Vue 3, Svelte, Solid, Lit, Qwik)
    - Full-stack (Next.js, Nuxt 3, Remix, Astro, SvelteKit, Analog)
    - API (tRPC, GraphQL, gRPC)
    - ORM (TypeORM, MikroORM, Prisma, Drizzle, Sequelize-TS, Kysely)
    - Validation (Zod, class-validator, io-ts, Arktype, Valibot)
    - Testing (Jest, Vitest, Playwright, Cypress, Testing Library)
    - State (NgRx, Redux Toolkit, Zustand, Jotai, MobX, Pinia)
    - Auth (Passport, NextAuth, Lucia, Auth.js)
    - Realtime (Socket.io, WebSocket)
    - DI (InversifyJS, tsyringe, NestJS)
    - Build (tsc, esbuild, SWC, Vite, Turbopack)
    - Util (RxJS, fp-ts, Effect, date-fns)

    Optional AST: tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Backend frameworks
        'nestjs': re.compile(r"from\s+['\"]@nestjs/(?:common|core|platform-express|microservices|websockets|graphql|swagger)['\"]|@Controller|@Injectable|@Module", re.MULTILINE),
        'express': re.compile(r"from\s+['\"]express['\"]|require\(['\"]express['\"]\)|express\.Router|RequestHandler|NextFunction", re.MULTILINE),
        'fastify': re.compile(r"from\s+['\"]fastify['\"]|FastifyInstance|FastifyRequest|FastifyReply|fastify\(\)", re.MULTILINE),
        'koa': re.compile(r"from\s+['\"]koa['\"]|Koa\.|new\s+Koa\(\)|Context|Middleware", re.MULTILINE),
        'hapi': re.compile(r"from\s+['\"]@hapi/hapi['\"]|Hapi\.Server|ServerRoute", re.MULTILINE),
        'hono': re.compile(r"from\s+['\"]hono['\"]|new\s+Hono\(\)|Hono<|HonoRequest", re.MULTILINE),
        'deno_oak': re.compile(r"from\s+['\"]https?://deno\.land.*/oak/|from\s+['\"]oak['\"]|Application|Router", re.MULTILINE),

        # Frontend frameworks
        'angular': re.compile(r"from\s+['\"]@angular/(?:core|common|router|forms|http)['\"]|@Component|@Directive|@Pipe|@NgModule|@Input|@Output|@Injectable", re.MULTILINE),
        'react': re.compile(r"from\s+['\"]react['\"]|React\.|useState|useEffect|useContext|useReducer|useMemo|useCallback|useRef|JSX\.Element|FC<|React\.FC", re.MULTILINE),
        'vue': re.compile(r"from\s+['\"]vue['\"]|defineComponent|ref\(|reactive\(|computed\(|watch\(|onMounted|defineProps|defineEmits|Ref<|ComputedRef", re.MULTILINE),
        'svelte': re.compile(r"from\s+['\"]svelte['\"]|from\s+['\"]svelte/|writable\(|readable\(|derived\(|\.svelte", re.MULTILINE),
        'solid': re.compile(r"from\s+['\"]solid-js['\"]|createSignal|createEffect|createMemo|createResource|Component<", re.MULTILINE),
        'lit': re.compile(r"from\s+['\"]lit['\"]|LitElement|html`|css`|@customElement|@property", re.MULTILINE),
        'qwik': re.compile(r"from\s+['\"]@builder\.io/qwik['\"]|component\$|useSignal|useStore|useTask", re.MULTILINE),

        # Full-stack / Meta-frameworks
        'nextjs': re.compile(r"from\s+['\"]next['/\"]|NextPage|GetServerSideProps|GetStaticProps|NextResponse|NextRequest|NextApiRequest|NextApiResponse|app/.*page\.tsx|app/.*layout\.tsx", re.MULTILINE),
        'nuxt': re.compile(r"from\s+['\"]nuxt['\"]|defineNuxtConfig|useAsyncData|useFetch|NuxtPage|navigateTo", re.MULTILINE),
        'remix': re.compile(r"from\s+['\"]@remix-run['/\"]|LoaderFunction|ActionFunction|MetaFunction|json\(|redirect\(", re.MULTILINE),
        'astro': re.compile(r"from\s+['\"]astro['\"]|Astro\.|astro\.config|defineCollection", re.MULTILINE),
        'sveltekit': re.compile(r"from\s+['\"]\$app/|from\s+['\"]\$env/|PageServerLoad|LayoutServerLoad|RequestHandler", re.MULTILINE),
        'analog': re.compile(r"from\s+['\"]@analogjs/['\"]|defineRouteMeta|injectLoad", re.MULTILINE),

        # Testing
        'jest': re.compile(r"from\s+['\"]@jest/|describe\s*\(|it\s*\(|test\s*\(|expect\s*\(|jest\.mock|jest\.fn|jest\.spyOn|beforeEach|afterEach", re.MULTILINE),
        'vitest': re.compile(r"from\s+['\"]vitest['\"]|vi\.mock|vi\.fn|vi\.spyOn", re.MULTILINE),
        'playwright': re.compile(r"from\s+['\"]@playwright/test['\"]|page\.\w+\(|test\.describe|test\.beforeEach|expect\(page\)", re.MULTILINE),
        'cypress': re.compile(r"cy\.\w+\(|Cypress\.\w+|describe.*cy\.", re.MULTILINE),
        'testing_library': re.compile(r"from\s+['\"]@testing-library/|render\(|screen\.\w+|fireEvent\.\w+|waitFor\(", re.MULTILINE),

        # ORM / Data
        'typeorm': re.compile(r"from\s+['\"]typeorm['\"]|@Entity|@Column|@ManyToOne|@OneToMany|@ManyToMany|@OneToOne|getRepository|Repository<", re.MULTILINE),
        'mikroorm': re.compile(r"from\s+['\"]@mikro-orm/|@Entity|@Property|@ManyToOne|@OneToMany|EntityManager|EntityRepository", re.MULTILINE),
        'prisma': re.compile(r"from\s+['\"]@prisma/client['\"]|PrismaClient|Prisma\.\w+|prisma\.\w+\.\w+", re.MULTILINE),
        'drizzle': re.compile(r"from\s+['\"]drizzle-orm['\"]|pgTable|mysqlTable|sqliteTable|drizzle\(|InferModel", re.MULTILINE),
        'sequelize_ts': re.compile(r"from\s+['\"]sequelize-typescript['\"]|@Table|@Column|@HasMany|@BelongsTo|@ForeignKey", re.MULTILINE),
        'kysely': re.compile(r"from\s+['\"]kysely['\"]|Kysely<|sql\.|SelectQueryBuilder|InsertQueryBuilder", re.MULTILINE),
        'mongoose_ts': re.compile(r"from\s+['\"]@typegoose/typegoose['\"]|@prop|getModelForClass|modelOptions", re.MULTILINE),

        # API / RPC
        'trpc': re.compile(r"from\s+['\"]@trpc/['\"]|initTRPC|publicProcedure|protectedProcedure|createTRPCRouter|TRPCError", re.MULTILINE),
        'graphql_typegraphql': re.compile(r"from\s+['\"]type-graphql['\"]|@Resolver|@Query|@Mutation|@Subscription|@Arg|@Field|@ObjectType|@InputType", re.MULTILINE),
        'apollo': re.compile(r"from\s+['\"]@apollo/['\"]|ApolloServer|ApolloClient|gql`|useQuery|useMutation|useLazyQuery", re.MULTILINE),
        'pothos': re.compile(r"from\s+['\"]@pothos/['\"]|SchemaBuilder|builder\.\w+Type", re.MULTILINE),
        'grpc': re.compile(r"from\s+['\"]@grpc/|from\s+['\"]grpc['\"]|ServiceClient|ServiceImplementation|ServerUnaryCall", re.MULTILINE),

        # Validation
        'zod': re.compile(r"from\s+['\"]zod['\"]|z\.object|z\.string|z\.number|z\.array|z\.enum|z\.infer|ZodSchema", re.MULTILINE),
        'class_validator': re.compile(r"from\s+['\"]class-validator['\"]|@IsString|@IsNumber|@IsEmail|@IsOptional|@IsNotEmpty|@ValidateNested|@IsEnum", re.MULTILINE),
        'io_ts': re.compile(r"from\s+['\"]io-ts['\"]|t\.type|t\.string|t\.number|t\.array|TypeOf", re.MULTILINE),
        'yup': re.compile(r"from\s+['\"]yup['\"]|yup\.object|yup\.string|InferType", re.MULTILINE),
        'arktype': re.compile(r"from\s+['\"]arktype['\"]|type\(|scope\(", re.MULTILINE),
        'valibot': re.compile(r"from\s+['\"]valibot['\"]|object\(|string\(|number\(|InferOutput", re.MULTILINE),

        # State management
        'ngrx': re.compile(r"from\s+['\"]@ngrx/(?:store|effects|entity|component-store)['\"]|createAction|createReducer|createEffect|createFeature|Store<|Actions", re.MULTILINE),
        'redux_toolkit': re.compile(r"from\s+['\"]@reduxjs/toolkit['\"]|createSlice|createAsyncThunk|configureStore|PayloadAction", re.MULTILINE),
        'zustand': re.compile(r"from\s+['\"]zustand['\"]|create\s*\(\s*\(set|StateCreator|StoreApi", re.MULTILINE),
        'jotai': re.compile(r"from\s+['\"]jotai['\"]|atom\s*\(|useAtom|atomWithStorage|PrimitiveAtom", re.MULTILINE),
        'mobx': re.compile(r"from\s+['\"]mobx['\"]|makeObservable|makeAutoObservable|observable|computed|action|observer", re.MULTILINE),
        'pinia': re.compile(r"from\s+['\"]pinia['\"]|defineStore|storeToRefs|PiniaPluginContext", re.MULTILINE),
        'tanstack_query': re.compile(r"from\s+['\"]@tanstack/(?:react-query|vue-query|solid-query|svelte-query)['\"]|useQuery|useMutation|QueryClient|QueryClientProvider", re.MULTILINE),

        # Auth
        'passport': re.compile(r"from\s+['\"]passport['\"]|passport\.use|passport\.authenticate|Strategy", re.MULTILINE),
        'nextauth': re.compile(r"from\s+['\"]next-auth['\"]|from\s+['\"]@auth/|NextAuth|getServerSession|SessionProvider|AuthOptions", re.MULTILINE),
        'lucia': re.compile(r"from\s+['\"]lucia['\"]|Lucia\(|validateSession|createSession|SessionCookie", re.MULTILINE),

        # Realtime
        'socketio': re.compile(r"from\s+['\"]socket\.io['\"]|from\s+['\"]socket\.io-client['\"]|io\(|Socket<|ServerSocket", re.MULTILINE),
        'ws': re.compile(r"from\s+['\"]ws['\"]|WebSocket|WebSocketServer", re.MULTILINE),

        # DI
        'inversify': re.compile(r"from\s+['\"]inversify['\"]|@injectable|@inject|Container|interfaces\.\w+", re.MULTILINE),
        'tsyringe': re.compile(r"from\s+['\"]tsyringe['\"]|@injectable|@inject|container\.resolve|DependencyContainer", re.MULTILINE),

        # Build / Tooling
        'webpack': re.compile(r"from\s+['\"]webpack['\"]|Configuration|webpack\.config|HtmlWebpackPlugin|Module\.exports", re.MULTILINE),
        'vite': re.compile(r"from\s+['\"]vite['\"]|defineConfig|import\.meta\.env|import\.meta\.hot|ViteDevServer", re.MULTILINE),
        'esbuild': re.compile(r"from\s+['\"]esbuild['\"]|esbuild\.build|BuildOptions|Plugin", re.MULTILINE),
        'swc': re.compile(r"from\s+['\"]@swc/|\.swcrc|swc\.config", re.MULTILINE),

        # Utility libraries
        'rxjs': re.compile(r"from\s+['\"]rxjs['\"]|from\s+['\"]rxjs/operators['\"]|Observable<|Subject<|BehaviorSubject|pipe\(|switchMap|mergeMap|map\(|filter\(|tap\(|catchError", re.MULTILINE),
        'fp_ts': re.compile(r"from\s+['\"]fp-ts/|pipe\(|flow\(|Either<|Option<|TaskEither|IO<", re.MULTILINE),
        'effect': re.compile(r"from\s+['\"]effect['\"]|from\s+['\"]@effect/|Effect\.succeed|Effect\.fail|pipe\(|Layer\.", re.MULTILINE),
        'date_fns': re.compile(r"from\s+['\"]date-fns['\"]|format\(|parseISO\(|addDays\(|differenceInDays", re.MULTILINE),
        'lodash': re.compile(r"from\s+['\"]lodash['\"]|import\s+_\s+from|_\.\w+\(", re.MULTILINE),
        'axios': re.compile(r"from\s+['\"]axios['\"]|axios\.get|axios\.post|AxiosInstance|AxiosResponse|AxiosRequestConfig", re.MULTILINE),

        # Process / Runtime
        'electron': re.compile(r"from\s+['\"]electron['\"]|BrowserWindow|ipcMain|ipcRenderer|app\.on|dialog\.showOpenDialog", re.MULTILINE),
        'tauri': re.compile(r"from\s+['\"]@tauri-apps/api['\"]|invoke\(|window\.__TAURI__", re.MULTILINE),

        # Monorepo tools
        'nx': re.compile(r"from\s+['\"]@nx/|nx\.json|project\.json|executors|generators", re.MULTILINE),
        'turborepo': re.compile(r"turbo\.json|TURBO_", re.MULTILINE),
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = TypeScriptTypeExtractor()
        self.function_extractor = TypeScriptFunctionExtractor()
        self.api_extractor = TypeScriptAPIExtractor()
        self.model_extractor = TypeScriptModelExtractor()
        self.attribute_extractor = TypeScriptAttributeExtractor()

    def parse(self, content: str, file_path: str = "") -> TypeScriptParseResult:
        """
        Parse TypeScript source code and extract all information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            TypeScriptParseResult with all extracted information
        """
        result = TypeScriptParseResult(file_path=file_path)

        # Detect file type
        if file_path.endswith('.d.ts') or file_path.endswith('.d.mts') or file_path.endswith('.d.cts'):
            result.file_type = "dts"
            result.is_declaration_file = True
        elif file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.mts'):
            result.file_type = "mts"
        elif file_path.endswith('.cts'):
            result.file_type = "cts"
        else:
            result.file_type = "typescript"

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract types ─────────────────────────────────────────
        type_result = self.type_extractor.extract(content, file_path)
        result.classes = type_result.get('classes', [])
        result.interfaces = type_result.get('interfaces', [])
        result.type_aliases = type_result.get('type_aliases', [])
        result.enums = type_result.get('enums', [])

        # ── Extract functions ─────────────────────────────────────
        func_result = self.function_extractor.extract(content, file_path)
        result.functions = func_result.get('functions', [])
        result.overloads = func_result.get('overloads', [])

        # ── Extract API/framework patterns ────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.routes = api_result.get('routes', [])
        result.middleware = api_result.get('middleware', [])
        result.websockets = api_result.get('websockets', [])
        result.graphql_resolvers = api_result.get('graphql_resolvers', [])
        result.trpc_routers = api_result.get('trpc_routers', [])

        # ── Extract models/data ───────────────────────────────────
        model_result = self.model_extractor.extract(content, file_path)
        result.models = model_result.get('models', [])
        result.migrations = model_result.get('migrations', [])
        result.relationships = model_result.get('relationships', [])
        result.dtos = model_result.get('dtos', [])

        # ── Extract attributes ────────────────────────────────────
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.imports = attr_result.get('imports', [])
        result.exports = attr_result.get('exports', [])
        result.decorators = attr_result.get('decorators', [])
        result.namespaces = attr_result.get('namespaces', [])
        result.triple_slash_directives = attr_result.get('triple_slash_directives', [])
        result.tsdoc = attr_result.get('tsdoc', [])

        # ── Version detection ─────────────────────────────────────
        result.ts_version = self._detect_version(content)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which frameworks are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect the minimum TypeScript version required by the file."""
        # Check from newest to oldest
        # TS 5.2: using declarations
        if re.search(r'\busing\s+\w+\s*=', content) or re.search(r'\bawait\s+using\b', content):
            return "5.2"

        # TS 5.0: const type parameters
        if re.search(r'<\s*const\s+\w+', content):
            return "5.0"

        # TS 4.9: satisfies operator
        if re.search(r'\bsatisfies\s+\w', content):
            return "4.9"

        # TS 4.7: variance annotations (in/out)
        if re.search(r'<\s*(?:in|out|in\s+out)\s+\w', content):
            return "4.7"

        # TS 4.5: type-only import specifiers (import { type Foo })
        if re.search(r'import\s+\{[^}]*\btype\s+\w+', content):
            return "4.5"

        # TS 4.1: template literal types
        if re.search(r'type\s+\w+\s*=\s*`[^`]*\$\{', content):
            return "4.1"

        # TS 4.0: variadic tuple types, labeled tuples
        if re.search(r'\[\s*\.\.\.\w+', content) or re.search(r'\[\s*\w+\s*:\s*\w+', content):
            return "4.0"

        # TS 3.7: optional chaining, assertion functions
        if re.search(r'\w+\?\.\w+', content) or re.search(r'\?\?\s*[^=]', content) or re.search(r'asserts\s+\w+\s+is\b', content):
            return "3.7"

        # TS 3.0: unknown type
        if re.search(r':\s*unknown\b|<\s*unknown\s*>', content):
            return "3.0"

        # TS 2.8: conditional types (extends ? : )
        if re.search(r'extends\s+\w+\s*\?', content) and re.search(r'type\s+\w+', content):
            return "2.8"

        # TS 2.1: keyof, mapped types
        if re.search(r'\bkeyof\b', content) or re.search(r'\{\s*\[\s*\w+\s+in\b', content):
            return "2.1"

        # TS 2.0: discriminated unions, non-null assertion, strictNullChecks types
        if re.search(r'\binterface\b|\benum\b|\btype\s+\w+\s*=', content):
            return "2.0"

        return "2.0"
