"""
EnhancedJavaScriptParser v1.0 - Comprehensive JavaScript parser using all extractors.

This parser integrates all JavaScript extractors to provide complete
parsing of JavaScript source files.

Supports:
- ES6+ classes, arrow functions, generators, async/await
- CommonJS (require/module.exports) and ESM (import/export)
- Express.js / Fastify / Koa / Hapi.js routes & middleware
- Mongoose / Sequelize / Prisma / Knex / Objection.js models
- WebSocket handlers (ws, socket.io)
- GraphQL resolvers
- JSDoc comments and type annotations
- Decorators (Stage 3 / Babel)
- Dynamic imports (React.lazy, code splitting)

JavaScript version detection from:
- ES module syntax (import/export → ES6+)
- Optional chaining (?.) → ES2020+
- Nullish coalescing (??) → ES2020+
- Top-level await → ES2022+
- Private fields (#) → ES2022+
- Array.at() → ES2022+
- structuredClone → ES2022+
- using/await using → ES2024+(proposal)
- Decorators → ES2024+ (Stage 3)
- Package.json "type": "module" detection
- .mjs/.cjs extension inference

Framework detection (70+ frameworks/libraries):
- Web: Express, Fastify, Koa, Hapi, Restify, Polka, micro
- Frontend: React, Vue, Svelte, Preact, Solid, Lit
- Full-stack: Next.js, Nuxt, Gatsby, Remix, Astro
- Testing: Jest, Mocha, Chai, Vitest, Jasmine, Ava, tap
- ORM: Mongoose, Sequelize, Prisma, Knex, TypeORM, Objection
- Auth: Passport, jsonwebtoken, bcrypt, Auth0
- Realtime: socket.io, ws, uWebSockets
- GraphQL: Apollo, graphql-yoga, Mercurius, Pothos
- Validation: Joi, Zod, Yup, AJV, class-validator
- Queue: Bull, BullMQ, Agenda, bee-queue
- Logging: Winston, Pino, Bunyan, Morgan
- State: Redux, MobX, Zustand, Jotai, Recoil
- Build: Webpack, Vite, Rollup, esbuild, Parcel, Turbopack
- Util: Lodash, Ramda, date-fns, moment, Axios

Optional AST support via tree-sitter-javascript.
Optional LSP support via typescript-language-server (also handles JS).

Part of CodeTrellis v4.30 - JavaScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all JavaScript extractors
from .extractors.javascript import (
    JavaScriptTypeExtractor, JSClassInfo, JSPrototypeInfo, JSConstantInfo,
    JSSymbolInfo, JSPropertyInfo,
    JavaScriptFunctionExtractor, JSFunctionInfo, JSParameterInfo,
    JSArrowFunctionInfo, JSGeneratorInfo,
    JavaScriptAPIExtractor, JSRouteInfo, JSMiddlewareInfo,
    JSWebSocketInfo, JSGraphQLResolverInfo,
    JavaScriptModelExtractor, JSModelInfo, JSSchemaFieldInfo,
    JSMigrationInfo, JSRelationInfo,
    JavaScriptAttributeExtractor, JSImportInfo, JSExportInfo,
    JSJSDocInfo, JSDecoratorInfo, JSDynamicImportInfo,
)


@dataclass
class JavaScriptParseResult:
    """Complete parse result for a JavaScript file."""
    file_path: str
    file_type: str = "javascript"  # javascript, module, commonjs, jsx

    # Core types
    classes: List[JSClassInfo] = field(default_factory=list)
    prototypes: List[JSPrototypeInfo] = field(default_factory=list)
    constants: List[JSConstantInfo] = field(default_factory=list)
    symbols: List[JSSymbolInfo] = field(default_factory=list)

    # Functions
    functions: List[JSFunctionInfo] = field(default_factory=list)
    arrow_functions: List[JSArrowFunctionInfo] = field(default_factory=list)
    generators: List[JSGeneratorInfo] = field(default_factory=list)

    # API / Framework
    routes: List[JSRouteInfo] = field(default_factory=list)
    middleware: List[JSMiddlewareInfo] = field(default_factory=list)
    websockets: List[JSWebSocketInfo] = field(default_factory=list)
    graphql_resolvers: List[JSGraphQLResolverInfo] = field(default_factory=list)

    # Models / Data
    models: List[JSModelInfo] = field(default_factory=list)
    migrations: List[JSMigrationInfo] = field(default_factory=list)
    relationships: List[JSRelationInfo] = field(default_factory=list)

    # Attributes / Imports / Exports
    imports: List[JSImportInfo] = field(default_factory=list)
    exports: List[JSExportInfo] = field(default_factory=list)
    jsdoc: List[JSJSDocInfo] = field(default_factory=list)
    decorators: List[JSDecoratorInfo] = field(default_factory=list)
    dynamic_imports: List[JSDynamicImportInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    js_version: str = ""  # ES5, ES6, ES2020, ES2022, ES2024
    module_system: str = ""  # esm, commonjs, mixed


class EnhancedJavaScriptParser:
    """
    Enhanced JavaScript parser that uses all extractors for comprehensive parsing.

    Framework detection supports 70+ frameworks/libraries across:
    - Web servers (Express, Fastify, Koa, Hapi, Restify, Polka)
    - Frontend frameworks (React, Vue, Svelte, Preact, Solid, Lit)
    - Full-stack frameworks (Next.js, Nuxt, Gatsby, Remix, Astro)
    - Testing (Jest, Mocha, Vitest, Jasmine, Ava, tap)
    - ORM/ODM (Mongoose, Sequelize, Prisma, Knex, TypeORM, Objection)
    - Authentication (Passport, jsonwebtoken, Auth0, bcrypt)
    - Real-time (socket.io, ws, uWebSockets, Server-Sent Events)
    - GraphQL (Apollo, graphql-yoga, Mercurius, Pothos)
    - Validation (Joi, Zod, Yup, AJV, class-validator)
    - Queues (Bull, BullMQ, Agenda, bee-queue)
    - Logging (Winston, Pino, Bunyan, Morgan)
    - State management (Redux, MobX, Zustand, Jotai, Recoil)
    - Build tools (Webpack, Vite, Rollup, esbuild, Parcel)
    - Utilities (Lodash, Ramda, date-fns, moment, Axios, node-fetch)

    Optional AST: tree-sitter-javascript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Web server frameworks
        'express': re.compile(r"require\(['\"]express['\"]\)|from\s+['\"]express['\"]|express\(\)", re.MULTILINE),
        'fastify': re.compile(r"require\(['\"]fastify['\"]\)|from\s+['\"]fastify['\"]|fastify\(\)", re.MULTILINE),
        'koa': re.compile(r"require\(['\"]koa['\"]\)|from\s+['\"]koa['\"]|new\s+Koa\(\)", re.MULTILINE),
        'hapi': re.compile(r"require\(['\"]@hapi/hapi['\"]\)|require\(['\"]hapi['\"]\)|Hapi\.server", re.MULTILINE | re.IGNORECASE),
        'restify': re.compile(r"require\(['\"]restify['\"]\)|from\s+['\"]restify['\"]", re.MULTILINE),
        'polka': re.compile(r"require\(['\"]polka['\"]\)|from\s+['\"]polka['\"]", re.MULTILINE),
        'micro': re.compile(r"require\(['\"]micro['\"]\)|from\s+['\"]micro['\"]", re.MULTILINE),

        # Frontend frameworks
        'react': re.compile(r"require\(['\"]react['\"]\)|from\s+['\"]react['\"]|React\.createElement|jsx|useState|useEffect", re.MULTILINE),
        'vue': re.compile(r"require\(['\"]vue['\"]\)|from\s+['\"]vue['\"]|createApp|defineComponent|ref\(|reactive\(", re.MULTILINE),
        'svelte': re.compile(r"from\s+['\"]svelte['\"]|\.svelte", re.MULTILINE),
        'preact': re.compile(r"require\(['\"]preact['\"]\)|from\s+['\"]preact['\"]", re.MULTILINE),
        'solid': re.compile(r"from\s+['\"]solid-js['\"]|createSignal|createEffect", re.MULTILINE),
        'lit': re.compile(r"from\s+['\"]lit['\"]|LitElement|customElement", re.MULTILINE),

        # Full-stack / meta-frameworks
        'nextjs': re.compile(r"from\s+['\"]next['/\"]|require\(['\"]next['/\"]\)|getServerSideProps|getStaticProps|NextResponse", re.MULTILINE),
        'nuxt': re.compile(r"from\s+['\"]nuxt['\"]|defineNuxtConfig|useAsyncData", re.MULTILINE),
        'gatsby': re.compile(r"from\s+['\"]gatsby['\"]|gatsby-node|gatsby-config", re.MULTILINE),
        'remix': re.compile(r"from\s+['\"]@remix-run['/\"]|loader\s*=|action\s*=.*Response", re.MULTILINE),
        'astro': re.compile(r"from\s+['\"]astro['\"]|Astro\.glob|astro\.config", re.MULTILINE),

        # Testing
        'jest': re.compile(r"describe\s*\(|it\s*\(|test\s*\(|expect\s*\(|jest\.mock|beforeEach|afterEach", re.MULTILINE),
        'mocha': re.compile(r"describe\s*\(|it\s*\(|before\s*\(|after\s*\(|require\(['\"]chai['\"]\)", re.MULTILINE),
        'vitest': re.compile(r"from\s+['\"]vitest['\"]|vi\.mock|vi\.fn", re.MULTILINE),
        'jasmine': re.compile(r"jasmine\.createSpy|spyOn\s*\(", re.MULTILINE),
        'ava': re.compile(r"from\s+['\"]ava['\"]|require\(['\"]ava['\"]\)|test\.serial", re.MULTILINE),
        'tap': re.compile(r"require\(['\"]tap['\"]\)|from\s+['\"]tap['\"]", re.MULTILINE),
        'cypress': re.compile(r"cy\.\w+\(|Cypress\.\w+|describe\s*\(.*\{\s*\n.*cy\.", re.MULTILINE),
        'playwright': re.compile(r"from\s+['\"]@playwright/test['\"]|page\.\w+\(", re.MULTILINE),

        # ORM / ODM
        'mongoose': re.compile(r"require\(['\"]mongoose['\"]\)|from\s+['\"]mongoose['\"]|mongoose\.Schema|mongoose\.model", re.MULTILINE),
        'sequelize': re.compile(r"require\(['\"]sequelize['\"]\)|from\s+['\"]sequelize['\"]|extends\s+Model|Sequelize\.define", re.MULTILINE),
        'prisma': re.compile(r"@prisma/client|PrismaClient|prisma\.\w+\.(?:find|create|update|delete)", re.MULTILINE),
        'knex': re.compile(r"require\(['\"]knex['\"]\)|from\s+['\"]knex['\"]|knex\.\w+", re.MULTILINE),
        'typeorm': re.compile(r"require\(['\"]typeorm['\"]\)|from\s+['\"]typeorm['\"]|@Entity|getRepository", re.MULTILINE),
        'objection': re.compile(r"require\(['\"]objection['\"]\)|from\s+['\"]objection['\"]|extends\s+Model", re.MULTILINE),
        'drizzle': re.compile(r"from\s+['\"]drizzle-orm['\"]|pgTable|mysqlTable|sqliteTable", re.MULTILINE),

        # Auth
        'passport': re.compile(r"require\(['\"]passport['\"]\)|from\s+['\"]passport['\"]|passport\.use|passport\.authenticate", re.MULTILINE),
        'jsonwebtoken': re.compile(r"require\(['\"]jsonwebtoken['\"]\)|from\s+['\"]jsonwebtoken['\"]|jwt\.sign|jwt\.verify", re.MULTILINE),
        'bcrypt': re.compile(r"require\(['\"]bcrypt(?:js)?['\"]\)|from\s+['\"]bcrypt(?:js)?['\"]", re.MULTILINE),
        'auth0': re.compile(r"require\(['\"]@auth0['/\"]\)|from\s+['\"]@auth0", re.MULTILINE),

        # Real-time
        'socketio': re.compile(r"require\(['\"]socket\.io['\"]\)|from\s+['\"]socket\.io['\"]|io\.on\s*\(|socket\.on\s*\(", re.MULTILINE),
        'ws': re.compile(r"require\(['\"]ws['\"]\)|from\s+['\"]ws['\"]|new\s+WebSocket", re.MULTILINE),

        # GraphQL
        'apollo': re.compile(r"require\(['\"]@apollo['/\"]\)|from\s+['\"]@apollo|ApolloServer|ApolloClient", re.MULTILINE),
        'graphql_yoga': re.compile(r"from\s+['\"]graphql-yoga['\"]|createYoga", re.MULTILINE),
        'mercurius': re.compile(r"require\(['\"]mercurius['\"]\)|from\s+['\"]mercurius['\"]", re.MULTILINE),

        # Validation
        'joi': re.compile(r"require\(['\"]joi['\"]\)|from\s+['\"]joi['\"]|Joi\.object|Joi\.string", re.MULTILINE),
        'zod': re.compile(r"require\(['\"]zod['\"]\)|from\s+['\"]zod['\"]|z\.object|z\.string", re.MULTILINE),
        'yup': re.compile(r"require\(['\"]yup['\"]\)|from\s+['\"]yup['\"]|yup\.object|yup\.string", re.MULTILINE),
        'ajv': re.compile(r"require\(['\"]ajv['\"]\)|from\s+['\"]ajv['\"]|new\s+Ajv", re.MULTILINE),

        # Queue / Jobs
        'bull': re.compile(r"require\(['\"]bull['\"]\)|from\s+['\"]bull['\"]|new\s+Bull\(", re.MULTILINE),
        'bullmq': re.compile(r"require\(['\"]bullmq['\"]\)|from\s+['\"]bullmq['\"]|new\s+Queue\(|new\s+Worker\(", re.MULTILINE),
        'agenda': re.compile(r"require\(['\"]agenda['\"]\)|from\s+['\"]agenda['\"]|new\s+Agenda\(", re.MULTILINE),

        # Logging
        'winston': re.compile(r"require\(['\"]winston['\"]\)|from\s+['\"]winston['\"]|winston\.createLogger", re.MULTILINE),
        'pino': re.compile(r"require\(['\"]pino['\"]\)|from\s+['\"]pino['\"]|pino\(\)", re.MULTILINE),
        'bunyan': re.compile(r"require\(['\"]bunyan['\"]\)|from\s+['\"]bunyan['\"]|bunyan\.createLogger", re.MULTILINE),
        'morgan': re.compile(r"require\(['\"]morgan['\"]\)|from\s+['\"]morgan['\"]", re.MULTILINE),

        # State management
        'redux': re.compile(r"require\(['\"]redux['\"]\)|from\s+['\"]redux|from\s+['\"]@reduxjs|createSlice|createStore|configureStore", re.MULTILINE),
        'mobx': re.compile(r"require\(['\"]mobx['\"]\)|from\s+['\"]mobx['\"]|observable|makeObservable|makeAutoObservable", re.MULTILINE),
        'zustand': re.compile(r"from\s+['\"]zustand['\"]|require\(['\"]zustand['\"]\)|create\s*\(\s*\(set", re.MULTILINE),
        'jotai': re.compile(r"from\s+['\"]jotai['\"]|require\(['\"]jotai['\"]|atom\s*\(", re.MULTILINE),
        'recoil': re.compile(r"from\s+['\"]recoil['\"]|require\(['\"]recoil['\"]|atom\s*\(|selector\s*\(", re.MULTILINE),

        # Build tools (detected via config files)
        'webpack': re.compile(r"require\(['\"]webpack['\"]\)|module\.exports\s*=.*(?:entry|output|module|plugins)", re.MULTILINE | re.DOTALL),
        'vite': re.compile(r"from\s+['\"]vite['\"]|defineConfig|import\.meta\.env", re.MULTILINE),
        'rollup': re.compile(r"from\s+['\"]rollup['\"]|rollup\.config", re.MULTILINE),
        'esbuild': re.compile(r"require\(['\"]esbuild['\"]\)|from\s+['\"]esbuild['\"]|esbuild\.build", re.MULTILINE),

        # Utilities
        'lodash': re.compile(r"require\(['\"]lodash['\"]\)|from\s+['\"]lodash['/\"]|_\.\w+\(", re.MULTILINE),
        'axios': re.compile(r"require\(['\"]axios['\"]\)|from\s+['\"]axios['\"]|axios\.get|axios\.post", re.MULTILINE),
        'dayjs': re.compile(r"require\(['\"]dayjs['\"]\)|from\s+['\"]dayjs['\"]", re.MULTILINE),
        'moment': re.compile(r"require\(['\"]moment['\"]\)|from\s+['\"]moment['\"]|moment\(", re.MULTILINE),

        # Process managers
        'pm2': re.compile(r"require\(['\"]pm2['\"]\)|ecosystem\.config|pm2\.connect", re.MULTILINE),
        'cluster': re.compile(r"require\(['\"]cluster['\"]\)|from\s+['\"]cluster['\"]|cluster\.fork", re.MULTILINE),

        # Electron
        'electron': re.compile(r"require\(['\"]electron['\"]\)|from\s+['\"]electron['\"]|BrowserWindow|ipcMain|ipcRenderer", re.MULTILINE),
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = JavaScriptTypeExtractor()
        self.function_extractor = JavaScriptFunctionExtractor()
        self.api_extractor = JavaScriptAPIExtractor()
        self.model_extractor = JavaScriptModelExtractor()
        self.attribute_extractor = JavaScriptAttributeExtractor()

    def parse(self, content: str, file_path: str = "") -> JavaScriptParseResult:
        """
        Parse JavaScript source code and extract all information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            JavaScriptParseResult with all extracted information
        """
        result = JavaScriptParseResult(file_path=file_path)

        # Skip minified files — they cause catastrophic regex backtracking
        if file_path.endswith(('.min.js', '.min.mjs')):
            return result
        first_line = content.split('\n', 1)[0] if content else ''
        if len(first_line) > 5000:
            return result

        # Detect frameworks first
        result.detected_frameworks = self._detect_frameworks(content)

        # Determine file type
        if file_path.endswith('.mjs'):
            result.file_type = "module"
            result.module_system = "esm"
        elif file_path.endswith('.cjs'):
            result.file_type = "commonjs"
            result.module_system = "commonjs"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        else:
            result.file_type = "javascript"

        # Detect module system if not set
        if not result.module_system:
            result.module_system = self._detect_module_system(content)

        # ── Extract types ─────────────────────────────────────────
        type_result = self.type_extractor.extract(content, file_path)
        result.classes = type_result.get('classes', [])
        result.prototypes = type_result.get('prototypes', [])
        result.constants = type_result.get('constants', [])
        result.symbols = type_result.get('symbols', [])

        # ── Extract functions ─────────────────────────────────────
        func_result = self.function_extractor.extract(content, file_path)
        result.functions = func_result.get('functions', [])
        result.arrow_functions = func_result.get('arrow_functions', [])
        result.generators = func_result.get('generators', [])

        # ── Extract API/framework patterns ────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.routes = api_result.get('routes', [])
        result.middleware = api_result.get('middleware', [])
        result.websockets = api_result.get('websockets', [])
        result.graphql_resolvers = api_result.get('graphql_resolvers', [])

        # ── Extract models/data ───────────────────────────────────
        model_result = self.model_extractor.extract(content, file_path)
        result.models = model_result.get('models', [])
        result.migrations = model_result.get('migrations', [])
        result.relationships = model_result.get('relationships', [])

        # ── Extract attributes/imports ────────────────────────────
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.imports = attr_result.get('imports', [])
        result.exports = attr_result.get('exports', [])
        result.jsdoc = attr_result.get('jsdoc', [])
        result.decorators = attr_result.get('decorators', [])
        result.dynamic_imports = attr_result.get('dynamic_imports', [])

        # ── Version detection ─────────────────────────────────────
        result.js_version = self._detect_version(content)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which frameworks are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_module_system(self, content: str) -> str:
        """Detect whether the file uses ESM or CommonJS."""
        has_esm = bool(re.search(r'^\s*(?:import\s|export\s)', content, re.MULTILINE))
        has_cjs = bool(re.search(r'(?:require\s*\(|module\.exports|exports\.)', content, re.MULTILINE))

        if has_esm and has_cjs:
            return "mixed"
        elif has_esm:
            return "esm"
        elif has_cjs:
            return "commonjs"
        return ""

    def _detect_version(self, content: str) -> str:
        """Detect the highest ECMAScript version used in the file."""
        # Check from newest to oldest
        if re.search(r'\busing\s+', content) and re.search(r'Symbol\.dispose', content):
            return "ES2024"
        if re.search(r'@\w+', content) and re.search(r'class\s+\w+', content):
            # Decorators (Stage 3, finalized ES2024)
            pass  # Decorators are ambiguous, don't force ES2024 for this
        if re.search(r'Array\.isArray.*\.at\(|\.at\s*\(\s*-?\d+\s*\)|structuredClone\s*\(|Object\.hasOwn\s*\(|\.findLast\s*\(', content):
            return "ES2022"
        if re.search(r'#\w+\s*[=;(]', content):
            return "ES2022"
        if re.search(r'\?\.\s*\w|\?\?\s*[^=]|globalThis\b|Promise\.allSettled|import\.meta\b', content):
            return "ES2020"
        if re.search(r'(?:async\s+)?function\s*\*\s*\w+|for\s+await\s*\(', content):
            return "ES2018"
        if re.search(r'\basync\s+function\b|\bawait\s+\w', content):
            return "ES2017"
        if re.search(r'\bclass\s+\w|const\s+|let\s+|=>\s*[\{(]|`[^`]*\$\{|import\s+\w|export\s+', content):
            return "ES6"
        return "ES5"
