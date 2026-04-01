# CodeTrellis Language Integration Checklist

> **Updated:** Session 76 - Phase CB: Centralized Language Configuration (v4.96) — Created `codetrellis/language_config.py` as single source of truth for all language-aware mappings (32 `LanguageInfo` frozen dataclass entries with extensions, manifests, version detection, linters, test tools, aliases). Refactored `init_integrations.py` (detect*project, version detection, conventions, quality gates, lifecycle all loop over LANGUAGES), `discovery_extractor.py` (LANGUAGE_MAP → EXT_TO_LANG, MANIFEST_LANGUAGE → MANIFEST_TO_LANG from language_config), `scanner.py` (ext_to_lang → EXT_TO_DISPLAY from language_config). Added Phase 0 to integration checklist/guide. 7337 total tests passing.
> **Updated:** Session 75 - Phase CA: Java Framework Parsers Round 2 (v4.95) — 5 Java framework parsers (Vert.x 3.x-4.x / Hibernate 3.x-6.x+JPA / MyBatis 3.x+MyBatis-Plus / Apache Camel 2.x-4.x / Akka Classic+Typed 2.5-2.8+), 25 extractors in 5 directories (vertx/hibernate/mybatis/apache*camel/akka) + 5 parser files (vertx_parser_enhanced.py/hibernate_parser_enhanced.py/mybatis_parser_enhanced.py/apache_camel_parser_enhanced.py/akka_parser_enhanced.py), 35 implementation files total, ~45 ProjectMatrix fields, scanner integration (5 imports + 5 parser inits + 5 `\_parse**`methods + Java/Scala/Kotlin file handlers), compressor integration (5 sections [VERTX]/[HIBERNATE]/[MYBATIS]/[APACHE_CAMEL]/[AKKA] + 5`_compress__` methods), Scanner Evaluation Round 1 on 3 repos (vert-x3/vertx-examples 70 verticles/93 routes/19 frameworks/v4.x, akka/akka-samples 17 frameworks/29 messages/72 HTTP routes, mybatis/mybatis-3 framework detection works/src/main has no mapper usage), 4 scanner attribute bugs fixed (wrong ParseResult field names in \_parse_vertx/\_parse_hibernate/\_parse_mybatis/\_parse_apache_camel), 109 new tests across 5 test files, 6752 total tests passing (0 regressions from 6643 baseline)
> **Updated:** Session 71 - Phase BW: Starlette + SQLAlchemy + Celery Enhanced Language Support (v4.91) — 3 enhanced parsers (EnhancedStarletteParser/EnhancedSQLAlchemyParser/EnhancedCeleryParser), Starlette 0.12+ (routes/mounts/middleware/WebSocket/lifespan/auth/static files/TestClient/framework ecosystem), SQLAlchemy 0.x-2.x+ (ORM models/Core tables/sessions/engines/Alembic migrations/events/hybrid properties, Mapped[]/mapped*column v2.0 style), Celery 3.x-5.x+ (tasks/@shared_task/@app.task/beat schedules with hyphenated names/signals/canvas primitives chain/group/chord/result backends/worker config/Kombu queues/routing), 32 ProjectMatrix fields, scanner integration (3 imports, 3 parser inits, 3 \_parse_python blocks, to_dict), compressor (3 enhanced sections), 4 bugs fixed (migration path detection, beat schedule hyphenated names, canvas multi-import detection, test file classification order), 3-repo validation (encode/starlette 1 route, sqlalchemy/sqlalchemy 56 core tables/24 engines/19 events/31 models, celery/celery 125 tasks/1496 canvas/54 queues/15 signals/10 configs), 101 new tests, 6069 total tests passing
> **Updated:** Session 67 - Phase BU: Express.js + NestJS + Fastify Backend Framework Support (v4.81) — 15 extractors (5 Express: route/middleware/error/config/api, 5 NestJS Enhanced: module/controller/provider/config/api, 5 Fastify: route/plugin/hook/schema/api), 3 per-file parsers (EnhancedExpressParser/EnhancedNestJSParser/EnhancedFastifyParser), Express 3.x-5.x (app.get/post/put/delete, Router, app.param, error handlers, app.set config, 30+ ecosystem), NestJS 7.x-10.x+ (@Module/@Global/DynamicModule, @Controller/@Get/@Post with guards/interceptors/pipes, @Injectable/constructor DI/@Inject/scopes, ConfigModule/ConfigService/process.env, @ApiTags/@ApiProperty/DTOs/class-validator, 40+ @nestjs/* ecosystem), Fastify 3.x-5.x (shorthand/full route(), fastify-plugin/fp/register/decorate, lifecycle hooks onRequest/preHandler/onSend/onClose, JSON Schema $id/$ref/addSchema/TypeBox/Zod type providers, 30+ @fastify/_ ecosystem), 43 dataclasses, 100+ framework patterns, 53 ProjectMatrix fields, scanner integration (3 \_parse methods ~560L, JS/TS dispatch + Angular-specific handlers for NestJS), compressor (3 sections: EXPRESS_ROUTES/NESTJS_ENHANCED/FASTIFY_ROUTES ~350L), Angular file type constraint solved (NestJS added to schema/dto/controller/model/service handlers), 3 bugs fixed (VERSION_PATTERN regex, \_extract_class_body depth, test alignment), 3-repo validation (expressjs/express 15 routes/3 middleware/36 config, nestjs/nest 81 controllers/99 providers/41 DTOs, fastify/fastify 4 routes/6 plugins/json-schema-to-ts), 62 new unit tests, 5984 total tests passing
> **Updated:** Session 63 - Phase BQ: Recharts Data Visualization Framework Support (v4.74) — 5 Recharts extractors (component, data, axis, customization, api), EnhancedRechartsParser with regex AST, Recharts v1.x (class components, callback refs) + v2.x (hooks, improved TypeScript, ComposedChart, FunnelChart, Sankey), 11 chart types (LineChart/BarChart/AreaChart/PieChart/RadarChart/ScatterChart/ComposedChart/RadialBarChart/Treemap/FunnelChart/Sankey), series components (Line/Bar/Area/Scatter/Pie/Radar/RadialBar with dataKey/stroke/fill/type/dot/activeDot), axes (XAxis/YAxis/ZAxis/CartesianGrid/PolarGrid/PolarAngleAxis/PolarRadiusAxis), customization (Tooltip content/formatter/cursor, Legend content/layout/align, ReferenceLine/ReferenceArea/ReferenceDot, Brush with onChange, events onClick/onMouseEnter/onMouseLeave/onMouseMove, animations isAnimationActive/animationDuration/animationEasing, LabelList), API (ESM named/namespace/default imports, CommonJS require, dynamic imports, tree-shakeable detection, recharts-scale/recharts-to-png/d3-scale/d3-shape/d3-format/d3-time-format ecosystem, TypeScript Props types, React/Next.js/Remix/Gatsby framework detection), ResponsiveContainer width/height/aspect/debounce, syncId synchronized charts, 15 dataclasses, 10 framework patterns + 30+ feature patterns, 24 ProjectMatrix fields, scanner + compressor (5 RECHARTS sections) + BPL integration (10 categories, 50 practices RECHARTS001-RECHARTS050), 132 new unit tests, 5621 total tests passing
> **Updated:** Session 62 - Phase BP: Chart.js Data Visualization Framework Support (v4.73) — 5 Chart.js extractors (chart*config, dataset, scale, plugin, api), EnhancedChartJSParser with regex AST, Chart.js v1.x (Chart.defaults.global) + v2.x (xAxes/yAxes, Chart.plugins.register) + v3.x (tree-shakeable imports, Chart.register, named scales, new plugin system) + v4.x+ (ESM-first, improved TypeScript), auto import (chart.js/auto) + tree-shakeable (chart.js with individual components), React (react-chartjs-2) + Vue (vue-chartjs) + Angular (ng2-charts/angular-chart.js) + Svelte (svelte-chartjs) framework integrations, 9 chart types (bar/line/pie/doughnut/radar/scatter/bubble/polarArea/mixed), datasets (fill/tension/pointStyle/hover/type override), scales (linear/log/time/category/radial, ticks/grid/stacked/beginAtZero), plugins (4 builtin: tooltip/legend/title/decimation, ecosystem: datalabels/zoom/annotation/streaming/gradient, custom inline plugins), date adapters (date-fns/luxon/moment/dayjs), animations (duration/easing/delay), interactions (mode/intersect/axis), CDN detection (jsdelivr/unpkg/cdnjs), 18 framework patterns + 40+ feature patterns, 23 ProjectMatrix fields, scanner + compressor (5 CHARTJS sections) + BPL integration (10 categories, 50 practices CHARTJS001-CHARTJS050), 133 new unit tests, 3 bugs fixed (bare import regex, ChartJS alias in register patterns, inline plugin detection), 3-repo validation (chartjs/Chart.js 303 files/3 sections/registerables/v3, reactchartjs/react-chartjs-2 210 files/5 sections/20 imports/14 builtin plugins/React, apertureless/vue-chartjs 174 files/4 sections/Vue/18 types/tree-shakeable), 5489 total tests passing
> **Updated:** Session 61 - Phase BO: D3.js Data Visualization Framework Support (v4.72) — 5 D3.js extractors (visualization, scale, axis, interaction, api), EnhancedD3JSParser with regex AST, D3.js v3 (monolithic d3.scale.linear/d3.svg.axis/d3.layout.force) + v4 (modular d3.scaleLinear/d3.axisBottom) + v5 (.join()) + v6 (ESM, d3.pointer) + v7+ (TypeScript, d3.bin), modular d3-* packages (d3-selection/d3-scale/d3-axis/d3-shape/d3-force/d3-hierarchy/d3-geo/d3-zoom/d3-brush/d3-drag/d3-transition/d3-array/d3-fetch/d3-format/d3-time-format/d3-scale-chromatic/d3-color/d3-interpolate), monolithic d3 bundle, Observable notebook (FileAttachment/viewof/md\`) + CDN detection, selections (d3.select/d3.selectAll/chained/variable/child), data joins (classic enter-update-exit/join()/datum(), key functions), shapes (arc/line/area/pie/stack/symbol/chord/ribbon/link/contour/density), layouts (force/tree/treemap/pack/partition/chord/sankey/histogram/voronoi/cluster/delaunay), scales (linear/log/pow/sqrt/time/utc/ordinal/band/point/quantize/quantile/threshold/sequential/diverging + v3 equivalents + 9 color scales), axes (axisTop/Right/Bottom/Left, v3 orient(), tick format/values/size/grid), interactions (events/.on()/d3.pointer/d3.mouse, brush/brushX/brushY, zoom with scale/translate extent, drag, transitions with duration/delay/ease), API (ESM/CJS/namespace/require/CDN/Observable imports, React/Angular/Vue/Svelte/D3FC/Vega/NVD3/C3.js/Billboard.js integrations, @types/d3 TypeScript types, data loaders csv/json/tsv/xml/text/image/blob/buffer/svg), 17 dataclasses, 25 ProjectMatrix fields, scanner + compressor (5 D3JS sections) + BPL integration (10 categories, 50 practices D3JS001-D3JS050), 118 new unit tests, 0 bugs, 3-repo validation (d3/d3: d3js-monolithic/namespace import, observablehq/plot: 22 classic joins/40 SVG elements/110 named imports/v5+v7+observable, d3/d3-shape: d3js-modular/d3-path import), 5356 total tests passing
> **Updated:** Session 60 - Phase BN: Three.js / React Three Fiber Framework Support (v4.71) — 5 Three.js extractors (scene, component, material, animation, api), EnhancedThreeJSParser with regex AST, Three.js r73-r162+ (WebGLRenderer/WebGPURenderer, PerspectiveCamera/OrthographicCamera, 20+ geometry types, 17+ materials, ShaderMaterial/RawShaderMaterial, GLSL vertex/fragment shaders, uniforms, textures, AnimationMixer, morph targets) + R3F v1-v8+ (Canvas, useFrame, useThree, useLoader, extend(), declarative mesh/group/instancedMesh, pointer events) + drei 100+ components across 10 categories (abstractions/controls/gizmo/html/loader/misc/performance/shape/staging/text) + @react-three/postprocessing (EffectComposer, Bloom, SSAO, 20+ effects) + @react-three/rapier/cannon/ammo/oimo/havok physics + @react-three/xr + @react-spring/three + GSAP/tween + model loading (useGLTF/useFBX/useOBJ/GLTFLoader, Draco, KTX2, HDR, EXR, preload) + CDN detection + version detection from imports/features, 20+ framework + 40+ feature patterns, ~33 ProjectMatrix fields, scanner + compressor (5 THREEJS sections) + BPL integration (10 categories, 50 practices THREEJS001-THREEJS050), 63 new unit tests, 0 bugs, 3-repo validation (pmndrs/react-three-fiber: Canvas/2 cameras/useFrame/94 types/r152/v8, pmndrs/drei: 3 canvases/43 cameras/66 meshes/14 useFrame/100+ drei components/79 types/13-pkg ecosystem, wass08/r3f-wawatmos-starter: Canvas/mesh/OrbitControls/R3F v1), 5238 total tests passing
> **Updated:** Session 59 - Infrastructure Hardening (v4.69) — Watcher crash fix (threading.Lock, atomic snapshot-and-clear, 2s debounce, batch callback), broken incremental build removed (4 methods ~350 lines: `_incremental_extract`, `_purge_changed_files`, `_merge_delta`, `_hydrate_matrix` — lossy hydration only mapped ~40/200+ ProjectMatrix fields), IMPLEMENTATION*LOGIC section added to PROMPT tier (was LOGIC/FULL only — matrix grew 20→33 sections, 1850→4177 lines), BEST_PRACTICES `_get_best_practices()` rewritten with 3-layer auto-detection: project-type (Python/FastAPI/Django) + language-specific (15 languages from matrix field presence) + framework-specific (20+ frameworks from stack detection), JSON-LD `project_profile` None fix, embeddings test threshold fix, `_changed_files_hint` infrastructure added to scanner, 15 new watcher tests + updated incremental build tests, 5112 total tests passing
> **Updated:** Session 58 - Phase BJ-0: Stimulus / Hotwire Framework Support (v4.68) — 5 Stimulus extractors (controller, target, action, value, api), EnhancedStimulusParser with regex AST, Stimulus v1 (`stimulus` npm) + v2 (`@hotwired/stimulus`) + v3 (outlets, afterLoad, action options) + Turbo v7-v8 (frames, streams, drive, morphing, events) + Strada v1 (BridgeComponent, BridgeElement), controller extraction (class definitions, lifecycle methods, static targets/values/classes/outlets, registration), target extraction (HTML data-*-target v2, data-target v1, JS getters, connected/disconnected callbacks), action extraction (data-action descriptors, event→controller#method, params, keyboard filters, global @window/@document, :prevent/:stop/:self/:once), value extraction (static values, HTML data-\_-\_-value, get/set accessors, valueChanged callbacks), API (ESM/CJS/dynamic/side-effect imports, CDN scripts, Application.start/register/load, Turbo frames/streams/drive/events/morphing, Strada BridgeComponent/BridgeElement, 12+ ecosystem integrations: Rails Importmap/Propshaft, Laravel Vite, Django, Phoenix, webpack/vite helpers, stimulus-use, stimulus-components), 20+ framework + 40+ feature patterns, 17 ProjectMatrix fields, scanner + compressor + BPL + A5.x integration, 91 new unit tests, 0 bugs, 3-repo validation (hotwired/stimulus-starter, hotwired/stimulus 18 controllers/50 actions/70 values/32 targets, thoughtbot/hotwire-example-template), 5018 total tests passing
> **Updated:** Session 54 - Phase BJ: Auto-Compilation Pipeline (PART B) — Incremental build pipeline (`cache.py` 534 lines, `builder.py` 546 lines), MatrixBuilder orchestrator (SCAN→DIFF→EXTRACT→COMPILE→PACKAGE), content-addressed SHA-256 caching (InputHashCalculator/CacheManager/LockfileManager/DiffEngine), IExtractor protocol + ExtractorManifest + BuildEvent + BuildResult interfaces, CLI flags (`--incremental`/`--deterministic`/`--ci`), `codetrellis clean` + `codetrellis verify` commands, Phase 0 stabilization (version sync 4.9.0→4.16.0, sorted traversal, CODETRELLIS*BUILD*TIMESTAMP, sort*keys=True), D4 determinism gate passed (byte-identical across runs), 62 new tests, 4609 total tests passing
> **Updated:** Session 54b - A5.x Module Coverage Expansion — All 4 A5.x modules (cache\*optimizer, mcp_server, jit_context, skills_generator) expanded to support 53+ languages/frameworks with ~350 unique section names. Added Phase 10: A5.x Module Integration checklist with 6 sub-phases (cache stability mapping, MCP aggregates, JIT extensions/path patterns, skills templates, unit tests, CLI verification). 201 A5.x tests passing. 4346 total tests passing.
> **Updated:** Session 53 - Phase BI: HTMX Framework Support (v4.67) — 5 HTMX extractors (attribute, request, event, extension, api), EnhancedHtmxParser with regex AST, HTMX v1.x (data-hx-* prefix, built-in extensions) + v2.x (hx-on:event syntax, hx-disabled-elt, hx-inherit, idiomorph, htmx-ext/\_ packages) + attribute categories (request/swap/navigation/modifier/ux/trigger/inheritance/extension/event) + HTTP request extraction (GET/POST/PUT/PATCH/DELETE endpoints, hx-vals, hx-headers, swap strategies, target selectors, trigger specs) + event system (40+ lifecycle events, SSE/WS events, trigger modifiers, hx-on:\_ inline handlers, htmx.on() JS listeners) + extensions (21 official extensions, custom via htmx.defineExtension()) + API (ESM/CJS imports, CDN scripts, htmx.config.\_, 12 integration patterns: Alpine/Hyperscript/Django/Flask/Rails/Laravel/FastAPI/Go-Templ/ASP.NET/Spring/Phoenix/Tailwind), 20 framework + 50 feature patterns, 18 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (HTMX001-HTMX050), 10 PracticeCategory entries, 166 new unit tests, 0 bugs, 3-repo validation (bigskysoftware/htmx, adamchainz/django-htmx, bigskysoftware/contact-app), 4346 total tests passing
> **Updated:** Session 52 - Phase BH: Alpine.js Framework Support (v4.66) — 5 Alpine.js extractors (directive, component, store, plugin, api), EnhancedAlpineParser with regex AST, Alpine.js v1.x (x-spread, CDN-only) + v2.x (x-data/x-show/x-bind/x-on/x-model/x-for/x-if/x-ref/x-text/x-html/x-transition/x-cloak/x-init) + v3.x (Alpine.start()/Alpine.data()/Alpine.store()/Alpine.plugin()/Alpine.directive()/Alpine.magic()/Alpine.bind(), x-effect/x-teleport/x-id/x-ignore, @alpinejs/\_ plugins: mask/intersect/persist/morph/focus/collapse/anchor/sort/resize, $dispatch/$refs/$el/$watch/$nextTick/$root/$data/$store/$id) + v3.14+ (Alpine.bind()) + CDN + ESM + CJS import detection, 20+ framework patterns + 50+ feature patterns, 18 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (ALPINE001-ALPINE050), 21 artifact types + fw mappings, 10 PracticeCategory entries (ALPINE_DIRECTIVES/ALPINE_COMPONENTS/ALPINE_STORES/ALPINE_PLUGINS/ALPINE_REACTIVITY/ALPINE_EVENTS/ALPINE_TRANSITIONS/ALPINE_PERFORMANCE/ALPINE_PATTERNS/ALPINE_SECURITY), 108 new unit tests, 3-repo validation (alpinejs/alpine, alpine-clipboard, alpine-ajax), 4180 total tests passing
> **Updated:** Session 51 - Phase BG: Lit / Web Components Framework Support (v4.65) — 5 Lit extractors (component, property, event, template, api), EnhancedLitParser with regex AST, Polymer 1.x-3.x (Polymer.Class/Polymer({is:})/PolymerElement) + lit-element 2.x (LitElement/UpdatingElement) + lit-html 1.x + lit 2.x-3.x (LitElement/ReactiveElement/html/css/svg, @customElement/@property/@state/@query/@queryAll/@queryAsync, static properties/static get properties(), render/connectedCallback/disconnectedCallback/firstUpdated/updated/willUpdate/attributeChangedCallback/adoptedCallback/createRenderRoot, ReactiveController/addController, customElements.define(), Shadow DOM/Light DOM, property options type/reflect/attribute/converter/hasChanged/noAccessor) + import-based feature/version detection, 25+ framework patterns + 35+ feature patterns, 25+ ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (LIT001-LIT050), 19 artifact types + 15+ fw mappings, 10 PracticeCategory entries (LIT_COMPONENTS/LIT_PROPERTIES/LIT_TEMPLATES/LIT_EVENTS/LIT_PERFORMANCE/LIT_SSR/LIT_TYPESCRIPT/LIT_PATTERNS/LIT_ACCESSIBILITY/LIT_TESTING), 109 new unit tests, 6 bugs fixed (trailing slash in \_is_lit_import prefixes, query decorator @prefix, multi-line regex, dict key css_styles, boolean_bindings attribute, vaadin side-effect imports), 3-repo validation (lit/lit official, pwa-starter, synthetic lit_demo), 4072 total tests passing
> **Updated:** Session 50 - Phase BF: Preact Framework Support (v4.64) — 5 Preact extractors (component, hook, signal, context, api), EnhancedPreactParser with regex AST, Preact v8.x (h/Component/linkState/preact-compat) + v10.x (hooks/createContext/Fragment) + v10.5+ (useId/useErrorBoundary) + v10.11+ (@preact/signals signal/computed/effect/batch) + v10.19+ (useSignalEffect) + @preact/signals v1-v2 (signal/computed/effect/batch/untracked/useSignal/useComputed/useSignalEffect) + import-based feature/version detection, 25 framework patterns + 35 feature patterns, 27 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (PREACT001-PREACT050), 19 artifact types + 20 fw mappings, 10 PracticeCategory entries, 92 new unit tests, 5 bugs fixed (signal regex typed annotations, context field name, API category, YAML path, ProjectMatrix constructor), 3-repo validation (preactjs/preact, preactjs/preact-router, denoland/fresh), 3963 total tests passing
> **Updated:** Session 49 - Phase BE: Qwik Framework Support (v4.63) — 5 Qwik extractors (component, signal, resource, routing, api), EnhancedQwikParser with regex AST, Qwik v1.x-v2.x (component$/useSignal/useStore/useResource$/useTask$/useVisibleTask$/useComputed$/Slot/useContext/createContextId) + Qwik City v1.x (routeLoader$/routeAction$/server$/validator$/Form/Link/useLocation/useNavigate/layout/index routing) + import-based feature/version detection, 25 framework patterns + 35 feature patterns, 24 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (QWIK001-QWIK050), 20 artifact types + 20 fw mappings, 10 PracticeCategory entries, 103 new unit tests, 0 bugs, 3-repo validation (BuilderIO/qwik, QwikDev/qwik-ui, BuilderIO/qwik-city-e-commerce), 3871 total tests passing
> **Updated:** Session 48 - Phase BD: Solid.js Framework Support (v4.62) — 6 Solid.js extractors (component, signal, store, resource, router, api), EnhancedSolidParser with regex AST, Solid.js v1.x-v2.x (createSignal/createMemo/createEffect/createResource/createStore/createMutable, Show/For/Switch/Match/Suspense/ErrorBoundary/Portal/Dynamic, onMount/onCleanup/onError, batch/untrack/on/mergeProps/splitProps, createContext/useContext) + SolidStart v0.x-v1.x (server$/createServerAction$/createServerData$, cache/action/createAsync, middleware, file-based routing) + @solidjs/router (Route/Router, useParams/useNavigate/useLocation/useSearchParams/useMatch) + import-based feature/version detection, 27 framework patterns + 40 feature patterns, 24 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (SOLIDJS001-SOLIDJS050), 25 artifact types + fw mappings, 10 PracticeCategory entries, 79 new unit tests, 3 bugs fixed (flow*type→name attribute, store*type value mismatch, destructured hook pattern), 3-repo validation (solidjs/solid-start 2 signals/4 fw/18 features/v2, solidjs/solid-router 4 signals/1 store/4 fw/18 features/v2, solidjs-community/solid-primitives 118 signals/6 stores/10 fw/34 features/v2), 3768 total tests passing
> **Updated:** Session 47 - Phase BC: Remix Framework Support (v4.61) — 5 Remix extractors (route, loader, action, meta, api), EnhancedRemixParser with regex AST, Remix v1.x (@remix-run/*, remix.config.js, CatchBoundary, LoaderFunction) + v2.x (Vite plugin, flat routes, v2*routeConvention/v2_meta, useRouteError, LoaderFunctionArgs) + React Router v7 (@react-router/*, routes.ts, Route.LoaderArgs/ActionArgs/MetaArgs, ServerRouter/HydratedRouter, middleware/clientMiddleware) + import-based feature/version detection, 30+ framework patterns + 25+ feature patterns, 21 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (REMIX001-REMIX050), 15 artifact types + 20+ fw mappings, 10 PracticeCategory entries, 102 new unit tests, 2 bugs fixed (intent pattern regex too strict, v1/v2 version substring collision), 3-repo validation (remix-run/indie-stack 2 routes/v2, remix-run/examples 33 routes/mixed, epicweb-dev/epic-stack 7+2 routes/rr7), 3689 total tests passing
> **Updated:** Session 46 - Phase BB: Astro Framework Support (v4.60) — 5 Astro extractors (component, frontmatter, island, routing, api), EnhancedAstroParser with regex AST, Astro v1-v5 (components, islands, content collections, SSR adapters, view transitions, server endpoints) + import-based feature/version detection, 30+ framework patterns + 25+ feature patterns, 20 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (ASTRO001-ASTRO050), 12 artifact types + 27 fw mappings, 10 PracticeCategory entries, 64 new unit tests, 12 bugs fixed (scanner field name mismatches), 3-repo validation (starlight/astro-docs/blog-template), 3587 total tests passing
> **Updated:** Session 45 - Phase BA: Apollo Client Framework Support (v4.59) — 5 Apollo extractors (query, mutation, cache, subscription, api), EnhancedApolloParser with regex AST, Apollo Client v1-v3 (useQuery/useLazyQuery/useSuspenseQuery/useBackgroundQuery/useReadQuery/useMutation/useSubscription/gql tags, InMemoryCache/typePolicies/makeVar/readQuery/writeQuery/modify/evict, ApolloLink chain, ApolloProvider, graphql-codegen, @apollo/client v3.8+ Suspense hooks) + import-based feature/version detection, 15 framework + 30 feature patterns, 19 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (APOLLO001-APOLLO050), 15 artifact types + 10 fw mappings, 10 PracticeCategory entries, 68 new unit tests, 15 bugs fixed (scanner field name mismatches: document→query*name/mutation_name/subscription_name/document_name, hook_type→hook_name, cache_type removed, has_cache_redirects→has_cache_redirect, type_annotation→type_params, target_type→query_name, imported_names→named_imports, pattern→details, name→type_name/link_type, to_dict() missing v4.48-v4.59 serialization), 3-repo validation (apollographql/apollo-client 690 imports/26 queries/37 links/14 cache configs/v3, apollographql/fullstack-tutorial 17 imports/7 queries/3 mutations/v3, apollographql/spotify-showcase 144 imports/24 queries/29 mutations/65 gql_tags/13 cache_ops/10 optimistic/3 reactive_vars/v3), 3523 total tests passing
> **Updated:** Session 44 - Phase AZ: SWR Framework Support (v4.58) — 5 SWR extractors (hook, cache, mutation, middleware, api), EnhancedSWRParser with regex AST, SWR v0.x-v2.x (useSWR/useSWRImmutable/useSWRInfinite/useSWRSubscription/useSWRMutation, SWRConfig provider, global/bound mutate, preload, cache provider, fallback data, middleware, conditional/dependent fetching, optimistic updates, rollback, 20 config options) + import-based feature/version detection, 15 framework + 30 feature patterns, 15 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (SWR001-SWR050), 15 artifact types + 8 fw mappings, 10 PracticeCategory entries, 84 new unit tests, 4 bugs fixed (optimistic update pattern, named imports, integration_type hyphen, TypeScript types), 3-repo validation (vercel/swr 2 InfiniteHooks/3 Preloads/15 Imports/20 Types/v2, vercel/swr-site v2/swr+next, shuding/nextra v2/preload/nextjs integration), 3455 total tests passing
> **Updated:** Session 43 - Phase AY: TanStack Query Framework Support (v4.57) — 5 TanStack Query extractors (query, mutation, cache, prefetch, api), EnhancedTanStackQueryParser with regex AST, TanStack Query v1-v5 (useQuery/useSuspenseQuery/useInfiniteQuery/useMutation/QueryClient/queryOptions/key factories/SSR hydration) + multi-framework (React/Vue/Svelte/Solid), 17 fw patterns + 32 feature patterns, 17 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (TSQUERY001-TSQUERY050), 15 artifact types + 15 fw mappings, 10 PracticeCategory entries, 67 new unit tests, 3-repo validation (E-commerce/Next.js Dashboard/Vue+tRPC, 15/15 checks), 3371 total tests passing
> **Updated:** Session 42 - Phase AX: Valtio Framework Support (v4.56) — 5 Valtio extractors (proxy, snapshot, subscription, action, api), EnhancedValtioParser with regex AST, Valtio v1-v2 (proxy/proxy<T>(), ref(), proxyMap/proxySet, useSnapshot/snapshot, subscribe/subscribeKey/watch, devtools, actions with direct mutation detection, TypeScript Snapshot<T> types) + import-based feature/version detection, 13 framework + 12 feature patterns, 15 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (VALTIO001-VALTIO050), 15 artifact types + 9 fw mappings, 58 new unit tests, 2 bugs fixed (type_name field mismatch, useProxy API correction), 2-file validation (store.ts 1 proxy/2 collections/4 actions/1 devtools/v2, TodoApp.tsx 3 snapshots/react+valtio), 3304 total tests passing
> **Updated:** Session 41 - Phase AW: XState Framework Support (v4.55) — 5 XState extractors (machine, state, action, guard, api), EnhancedXstateParser with regex AST, XState v3-v5 (Machine/createMachine/setup, state nodes atomic/compound/parallel/final/history, transitions event-driven/guarded/delayed/eventless/array, actions assign/send/raise/log/stop/cancel/pure/choose/forwardTo/escalate/respond/enqueueActions/emit, guards cond/guard/not/and/or/stateIn, actors createActor/interpret/fromPromise/fromCallback/fromObservable/fromTransition/spawn, @xstate/react useMachine/useActor/useSelector/useActorRef, @xstate/vue/@xstate/svelte/@xstate/solid, @xstate/inspect/@stately/inspect/@statelyai/inspect, @xstate/test/@xstate/graph/@xstate/store/@xstate/immer, typegen tsTypes) + import-based feature/version detection, 11 framework + 30 feature patterns, 12 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (XSTATE001-XSTATE050), 9 artifact types + 15 fw mappings, 80 new unit tests, 7 bugs fixed (is_exported/array transitions/stateIn object/on: brace balancing/feature import detection/v5 import detection/@stately/inspect), 2-repo validation (statelyai/xstate 257 files/1196 machines/2267 states/891 transitions/0 errors/v3+v4+v5, statelyai/xstate-viz 71 files/11 machines/21 states/14 transitions/0 errors), 3246 total tests passing
> **Updated:** Session 40 - Phase AV: NgRx Framework Support (v4.53) — 5 NgRx extractors (store, effect, selector, action, api), EnhancedNgrxParser with regex AST, NgRx v1-v19 (StoreModule.forRoot/forFeature, provideStore/provideState, ComponentStore, signalStore(), createAction/createActionGroup, createEffect/@Effect/functional effects, createSelector/createFeatureSelector/createFeature, @ngrx/entity/router-store) + meta-reducers + runtime checks + devtools, 30 framework + 20 feature patterns, 18 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (NGRX001-NGRX050), 10 PracticeCategory entries, 49 new unit tests, 0 bugs, 3-repo validation (ngrx-material-starter 10 actions/8 effects/13 selectors/v8-v11, ngrx/platform 23 actions/29 effects/38 selectors/35 stores/3 entities, ngrx-contacts 12 actions/8 effects/4 selectors/1 entity/v8-v11), 3166 total tests passing
> **Updated:** Session 39 - Phase AU: Pinia Framework Support (v4.52) — 5 Pinia extractors (store, getter, action, plugin, api), EnhancedPiniaParser with regex AST, Pinia v0-v3 (defineStore Options API + Setup API, state_fields, getters, actions, HMR, persist, cross-store, TypeScript) + getters (options/setup/storeToRefs()/return functions/cross-store) + actions ($patch object/function, $subscribe detached/flush, $onAction after/onError, async, error handling) + plugins (createPinia(), pinia.use(), persistedstate/debounce/orm/custom context, SSR) + API (imports from pinia/@pinia/nuxt/@pinia/testing/pinia-plugin-*, TypeScript types, map helpers, integrations), 30 framework + 20 feature patterns, 14 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (PINIA001-PINIA050), 60 new unit tests, 0 bugs, 3-repo validation (vuejs/pinia playground 13 stores/7 getters/6 actions/9 patches/v2, piniajs/example-vue-3-vite 2 actions/2 patches/v2, wobsoriano/pinia-shared-state 1 patch/2 subscriptions/v2), 3117 total tests passing
> **Updated:** Session 38 - Phase AT: MobX Framework Support (v4.51) — 5 MobX extractors (observable, computed, action, reaction, api), EnhancedMobXParser with regex AST, MobX v3-v6 (makeObservable/makeAutoObservable/@observable/observable.ref/shallow/struct) + computed (computed()/@computed/computed.struct) + actions (action()/action.bound/@action/runInAction/flow()/@flow) + reactions (autorun/reaction/when/observe/intercept/onBecomeObserved/onBecomeUnobserved) + API (imports/configure/observer/inject/Provider/TypeScript types), 16 framework + 20 feature patterns, 14 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (MOBX001-MOBX050), 72 new unit tests, 0 bugs, 3057 total tests passing
> **Updated:** Session 37.5 - Phase AS: Recoil Framework Support (v4.50) — 5 Recoil extractors (atom, selector, hook, effect, api), EnhancedRecoilParser with regex AST, Recoil v0.x (atom/atomFamily/selector/selectorFamily/atom effects) + hooks (useRecoilState/useRecoilValue/useSetRecoilState/useRecoilCallback/useRecoilTransaction) + effects (onSet/onGet/setSelf/resetSelf) + API (RecoilRoot/Snapshot/integrations/TypeScript types), 14 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (RECOIL001-RECOIL050), 108 new unit tests, 0 bugs, 2985 total tests passing
> **Updated:** Session 37 - Phase AR: Jotai Framework Support (v4.49) — 5 Jotai extractors (atom, selector, middleware, action, api), EnhancedJotaiParser with regex AST, Jotai v1.x-v2.x (atom/atomFamily/atomWithReset/atomWithReducer/atomWithDefault) + selectors (derived atoms/selectAtom/focusAtom/splitAtom/loadable/unwrap) + middleware (atomWithStorage/atomEffect/atomWithMachine/atomWithProxy/atomWithImmer/atomWithLocation/atomWithHash/atomWithObservable) + actions (useAtom/useAtomValue/useSetAtom/useStore/useHydrateAtoms/useAtomCallback/createStore/getDefaultStore/store.get/set/sub) + API (imports/integrations/TypeScript types), 17 framework patterns + 34 feature patterns, 18 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (JOTAI001-JOTAI050) with priority fields, 10 PracticeCategory enum values, 98 new unit tests, 0 bugs, validation scan (10 atoms/7 hooks/6 store usages/v2 detected/5 frameworks), 2877 total tests passing
> **Updated:** Session 36 - Phase AQ: Zustand Framework Support (v4.48) — 5 Zustand extractors (store, selector, middleware, action, api), EnhancedZustandParser with regex AST, Zustand v1.x-v5.x (create/createStore/createWithEqualityFn) + middleware (persist/devtools/immer/subscribeWithSelector) + selectors (named/inline/shallow/useShallow v5) + vanilla stores + slice pattern + context stores + TypeScript (StateCreator/StoreApi/StoreMutatorIdentifier) + SSR/Next.js (skipHydration/createJSONStorage) + imperative API (getState/setState/subscribe/destroy), 16 framework patterns (zustand/zustand-vanilla/zustand-middleware/zustand-persist/zustand-devtools/zustand-immer/zustand-subscribeWithSelector), 20 feature patterns, 17 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (ZUSTAND001-ZUSTAND050) with priority fields, 10 PracticeCategory enum values, 57 new unit tests, 0 bugs, 2-repo validation (pmndrs/zustand v5 detection, zustand-app 3 slices/devtools+persist+immer/useShallow), 2779 total tests passing
> **Updated:** Session 35 - Phase AP: Redux/RTK Framework Support (v4.47) — 5 Redux extractors (store, slice, middleware, selector, api), EnhancedReduxParser with regex AST, Redux 1.x-5.x (createStore/combineReducers/compose) + RTK 1.0-2.x (configureStore/createSlice/createAsyncThunk/createListenerMiddleware/Tuple) + redux-saga 0.x-1.x (generator/effect detection) + redux-observable 1.x-2.x (epic/RxJS operator detection) + RTK Query (createApi/fetchBaseQuery/endpoints/cache tags/lifecycle callbacks/code splitting) + redux-persist v5-v6 + reselect (createSelector/createStructuredSelector), typed hooks (.withTypes<>()), entity adapter selectors, 30+ framework detection (redux, @reduxjs/toolkit, redux-saga, redux-observable, redux-persist, reselect, react-redux, redux-thunk, redux-logger, redux-devtools-extension, immer, normalizr, msw, connected-react-router, typesafe-actions, redux-actions, redux-form, @hookform/resolvers), 20 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (REDUX001-REDUX050) with priority fields, 10 PracticeCategory enum values, 46 new unit tests, 1 regex bug fixed, 3-repo validation (redux-essentials-final 1 store/1 slice/1 API/5 endpoints/rtk-v1, react-redux-realworld 1 store/legacy, react-boilerplate 2 stores/2 sagas/4 selectors), 2722 total tests passing
> **Updated:** Session 34 - Phase AO: PostCSS Language Support (v4.46) — 5 PostCSS extractors (plugin, config, transform, syntax, api), EnhancedPostCSSParser with regex AST, PostCSS 1.x-8.5+ version detection, 100+ known plugins across 7 categories (future_css/optimization/utility/linting/syntax/modules/framework), config format detection (CJS/ESM/JSON/YAML), 15+ CSS transform patterns (@custom-media/@layer/@container/color functions/logical properties), custom syntax detection (postcss-scss/postcss-less/postcss-html/sugarss/postcss-jsx), PostCSS JS API usage extraction (postcss()/plugin()/process()/walk\*/node creation/result handling), 30+ framework/tool detection (Vite/Webpack/Next.js/Parcel/Rollup/Gulp/postcss-cli/postcss-loader/stylelint/cssnano/autoprefixer/tailwindcss), 15 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (PCSS001-PCSS050) with priority fields, 10 PracticeCategory enum values, 98 new unit tests, 0 bugs, 2676 total tests passing
> **Updated:** Session 33 - Phase AN: Less Language Support (v4.45) — 5 Less extractors (variable, mixin, function, import, ruleset), EnhancedLessParser with regex AST, Less 1.x-4.x+ version detection, @variables with scopes/data types/lazy evaluation/interpolation, .mixin() parametric/pattern-matched definitions + calls, guards (when/not/and/or/type-checking), namespaces (#id > .class), 70+ built-in functions across 8 categories (color/math/string/list/type/misc/color-ops/color-blend), @import with options (reference/inline/less/css/once/multiple/optional), :extend() all/inline, detached rulesets, nesting depth/BEM patterns/parent selectors, property merging (+/\_), math mode detection (always/parens-division/parens/strict/strict-legacy), 20+ feature detection, 5+ framework detection (Bootstrap, Ant Design, Semantic UI, Element UI, iView), 6+ library detection (LESS Hat, LESSElements, 3L, Preboot, Est, CSS Owl), 17 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (LESS001-LESS050) with priority fields, 10 PracticeCategory enum values, 79 new unit tests, 0 bugs, 2-repo validation (less/less.js 329 .less files/494 vars/1289 mixin defs/426 calls/132 guards, Semantic-Org/Semantic-UI 48 .less files), 2578 total tests passing
> **Updated:** Session 32 - Phase AM: Sass/SCSS Language Support (v4.44) — 5 Sass extractors (variable, mixin, function, module, nesting), EnhancedSassParser with regex AST, Dart Sass 1.x/LibSass/Ruby Sass version detection, .scss + .sass (indented) syntax support, @use/@forward module system (Dart Sass 1.23.0+), @import (legacy), $variables/$maps/lists/!default/!global, @mixin/@include (=mixin/+include indented), @function/@return with 100+ built-in functions across 7 categories (color/math/string/list/map/selector/meta), @extend/%placeholders, nesting depth analysis, BEM pattern detection (&\__element/&--modifier), @at-root, partial detection (\_prefix), 20+ framework detection (Bootstrap, Foundation, Bulma, Bourbon, Compass, Susy, include-media, sass-mq, rfs, Neat, Bitters, breakpoint-sass, normalize-scss, family.scss, sass-rem, sass-true, eyeglass, node-sass, dart-sass), 18 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (SASS001-SASS050) with priority fields, 10 PracticeCategory enum values, 50 new unit tests, 0 bugs, 2-repo validation (twbs/bootstrap 122 SCSS files, jgthms/bulma 863 vars/301 @use/129 @forward), 2499 total tests passing
> **Updated:** Session 31 - Phase AL: Emotion CSS-in-JS Framework Support (v4.43) — 5 Emotion extractors (component, theme, style, animation, api), EnhancedEmotionParser with regex AST, Emotion v9/v10/v11+ support (@emotion/react css prop, @emotion/styled, @emotion/css, @emotion/cache, @emotion/server SSR, @emotion/jest, Global, keyframes, ClassNames, cx(), shouldForwardProp, facepaint), 30+ framework detection (emotion-react, emotion-styled, emotion-css, emotion-cache, emotion-server, emotion-jest, twin-macro, facepaint, polished, theme-ui, rebass, next-emotion), v9 (legacy emotion pkg)/v10 (emotion-theming)/v11+ (@emotion/react scoped packages) version detection, 22 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (EMO001-EMO050) with priority fields, 10 PracticeCategory enum values, 63 new unit tests, 0 bugs, 3-repo validation (emotion-js/emotion, chakra-ui/chakra-ui, mui/material-ui), 2449 total tests passing
> **Updated:** Session 30 - Phase AK: Styled Components Framework Support (v4.42) — 5 SC extractors (component, theme, mixin, style, api), EnhancedStyledComponentsParser with regex AST, styled-components v1-v6 support (styled.element`, styled(Component)`, .attrs(), .withConfig(), transient $props, css`, keyframes`, createGlobalStyle, ThemeProvider, useTheme, SSR ServerStyleSheet), 30+ framework detection (styled-components, @emotion/styled, linaria, goober, stitches, polished, styled-system, rebass, xstyled, styled-media-query, jest-styled-components, babel-plugin-styled-components, @swc/plugin-styled-components), 18 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (SC001-SC050) with priority fields, 10 PracticeCategory enum values, 57 new unit tests, 0 bugs, 3-repo validation (styled-components-website, hyper, xstyled), 2386 total tests passing
> **Updated:** Session 29 - Phase AJ: Radix UI Framework Support (v4.41) — 5 Radix extractors (component, primitive, theme, style, api), EnhancedRadixParser with regex AST, Radix Primitives v0.x-v1.x + Themes v1.x-v4.x support (30+ primitives, 50+ themes components, 28 color scales), 30+ framework detection (radix-primitives, radix-themes, radix-colors, radix-icons, stitches, tailwind-merge, clsx, CVA, vanilla-extract, framer-motion, react-spring), 14 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (RADIX001-RADIX050) with priority fields, 10 PracticeCategory enum values, BPL selector filter reordering (Radix/MUI/ANTD/Chakra before generic React), 95 new unit tests, 0 bugs, 2-repo validation (radix-ui/themes, shadcn-ui/ui), 2329 total tests passing
> **Updated:** Session 28 - Phase AI: Bootstrap Framework Support (v4.40) — 5 Bootstrap extractors (component, grid, theme, utility, plugin), EnhancedBootstrapParser with regex AST, Bootstrap v3.x-v5.3+ support (50+ component categories, React-Bootstrap/reactstrap JSX, jQuery/vanilla JS init, data-bs-\* attributes), 16 framework detection (bootstrap-css, bootstrap-js, react-bootstrap, reactstrap, ng-bootstrap, ngx-bootstrap, bootstrap-vue, bootswatch, bootstrap-icons, @popperjs/core, jQuery), 15 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (BOOT001-BOOT050) with priority fields, 10 PracticeCategory enum values, 64 new unit tests, 0 bugs, 2-repo validation (StartBootstrap/sb-admin-2, react-bootstrap/react-bootstrap), 2234 total tests passing
> **Updated:** Session 27 - Phase AH: shadcn/ui Framework Support (v4.39) — 5 shadcn extractors (component, theme, hook, style, api), EnhancedShadcnParser with regex AST, shadcn/ui v0.x-v3.x support (40+ components, 5 categories, Radix UI primitives, cn() utility, CVA), 30+ ecosystem detection (class-variance-authority, cmdk, lucide-react, react-hook-form, @tanstack/react-table, next-themes, embla-carousel, react-day-picker, input-otp, sonner), 17 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (SHADCN001-SHADCN050) with priority fields, 10 PracticeCategory enum values, 63 new unit tests, 7 bugs fixed (#97-103 including field name mismatches), 2-repo validation (shadcn-ui/taxonomy 136 files, shadcn-ui/ui 2429 files), 2170 total tests passing
> **Updated:** 15 February 2026 - Phase AF: Ant Design (Antd) Framework Support (v4.37) — 5 Antd extractors (component, theme, hook, style, api), EnhancedAntdParser with regex AST, Ant Design v1-v5 support (80+ components, 6 categories, Pro components, sub-components, tree-shaking imports), 40+ ecosystem detection (antd, @ant-design/icons, @ant-design/pro-components, @ant-design/pro-layout, @ant-design/pro-table, @ant-design/pro-form, @ant-design/charts, antd-style, antd-mobile, umi, ahooks, babel-plugin-import), 20 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (ANTD001-ANTD050) with priority fields, 10 PracticeCategory enum values, 52 new unit tests, 2 bugs fixed (#91-92 including CommonJS require support), 2-repo validation (ant-design-pro 25+ comps/v5/Pro/umi, antd-admin 70+ comps/v4-v5), 2054 total tests passing
> **Updated:** 15 February 2026 - Phase AE: Material UI (MUI) Framework Support (v4.36) — 5 MUI extractors (component, theme, hook, style, api), EnhancedMuiParser with regex AST, MUI v0.x-v6.x support (130+ components, @material-ui/_, @mui/\_, Pigment CSS), 30+ ecosystem detection (mui-material, mui-lab, mui-icons, mui-x-date-pickers, mui-x-data-grid, mui-system, notistack, tss-react, emotion, styled-components), 20 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (MUI001-MUI050) with priority fields, 10 PracticeCategory enum values, 43 new unit tests, 7 bugs fixed (#84-90 including critical to_dict() root cause), 3-repo validation (devias-kit 411 comps, minimal-ui-kit 293 comps/27 styled, react-material-admin 4614 comps/24 makeStyles), 2002 total tests passing
> **Updated:** 15 February 2026 - Phase AD: Tailwind CSS Framework Support (v4.35) — 5 Tailwind extractors (utility, component, config, theme, plugin), EnhancedTailwindParser with regex AST, Tailwind CSS v1.x-v4.x support (@apply, @tailwind, @screen, @layer, @utility, @variant, @theme, @source, @plugin, CSS-first config), 13 framework detection (DaisyUI, Flowbite, Preline, NextUI, shadcn, twin.macro, Headless UI, tailwind-animate, tailwind-merge, tailwind-variants, CVA), 20+ feature detection, 19 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (TW001-TW050) with priority fields, 10 PracticeCategory enum values, 55 new unit tests, 5 bugs fixed (#79-83 including CSS layer crash and Tailwind detection fix), 3-repo validation (Flowbite 55 @apply, DaisyUI 613 @apply/331 components, TW Docs 36 @apply), 1959 total tests passing
> **Updated:** 14 February 2026 - Phase AC: Vue.js Framework Support (v4.34) — 5 Vue extractors (component, composable, directive, plugin, routing), EnhancedVueParser with regex AST, Vue 2.x-3.5+ support (Options API, Composition API, script setup, Reactive Props Destructure, useTemplateRef, useId, defineModel), 80+ framework detection (Nuxt 2/3, Quasar, Vuetify, Element Plus, PrimeVue, Naive UI, Pinia, Vuex, VueUse, VeeValidate, FormKit, Vue Router, vue-i18n, Headless UI Vue, Vue Apollo, Vue Query), SFC template/style/script extraction, props/emits/slots/provide-inject/mixins extraction, 19 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (VUE001-VUE050) with priority fields, 15 PracticeCategory enum values, 59 new unit tests, 2 bugs fixed (#77-78), 3-repo validation (Element Plus, VueUse 217 composables, Nuxt UI 180 components), 1834 total tests passing
> **Updated:** 14 February 2026 - Phase AB: TypeScript Language Support (v4.31) — 5 TypeScript extractors (type, function, api, model, attribute), EnhancedTypeScriptParser with regex AST, TS 2.x-5.x+ support, 80+ framework detection (NestJS/Next.js/React/Angular/Vue/Express/Fastify/Hono/tRPC/Prisma/TypeORM/Sequelize/Drizzle/MikroORM/GraphQL/Socket.io), interface/type alias/enum/class extraction, mapped/conditional/utility/template literal type classification, function overload detection, tRPC programmatic paren-counting (ReDoS-safe), scanner + compressor + BPL integration, 45 BPL practices (TS001-TS045) with priority fields, 15 PracticeCategory enum values, 98 new unit tests, 3 bugs fixed (#74-76 including critical ReDoS fix), 3-repo validation (Cal.com 7511 TS files, Strapi, Hatchet), 1649 total tests passing
> **Updated:** 14 February 2026 - Phase AA: JavaScript Language Support (v4.30) — 5 JavaScript extractors (type, function, api, model, attribute), EnhancedJavaScriptParser with regex AST, ES5-ES2024+ support, 70+ framework detection (Express/React/Vue/Angular/Next.js/Fastify/Koa/Hapi/Nest/Mongoose/Sequelize/Prisma/Knex/Socket.io/GraphQL), ES6+ class extraction + prototype-based OOP, CommonJS + ESM module detection, JSDoc extraction, scanner + compressor + BPL integration, 50 BPL practices (JS001-JS050) with priority fields (9 critical, 27 high, 13 medium, 1 low), 15 PracticeCategory enum values, 88 new unit tests, 6 bugs fixed (#68-73 including 3 critical BPL selector fixes), 3-repo validation (Express.js, Ghost, Nodemailer), 1551 total tests passing
> **Updated:** 14 February 2026 - Phase Z: PowerShell Language Support (v4.29) — 5 PowerShell extractors (type, function, api, model, attribute), EnhancedPowerShellParser with regex AST, Windows PowerShell 1.0-5.1 + PowerShell Core 6.0-7.4+ support, 30+ framework detection (Pode/Polaris/UniversalDashboard/Pester/DSC/Azure/AWS/GCP/MSGraph/Exchange/ActiveDirectory/PSake/InvokeBuild/Plaster), DSC resource/config/node extraction, Pester test extraction, cmdlet binding detection, scanner + compressor + BPL integration, 50 BPL practices (PS001-PS050), 14 PracticeCategory enum values, 57 new unit tests, 5 bugs fixed (#63-67), 3 coverage gaps fixed (G-1 to G-3), 3-repo validation (Pode, SqlServerDsc, Pester), 1463 total tests passing
> **Updated:** 14 February 2026 - Phase Y: Lua Language Support (v4.28) — 5 Lua extractors (type, function, api, model, attribute), EnhancedLuaParser with regex AST + optional tree-sitter-lua + lua-language-server LSP, Lua 5.1-5.4/LuaJIT 2.x support, 50+ framework detection (LÖVE2D/OpenResty/Lapis/lor/Corona/Defold/Gideros/Tarantool/middleclass/classic/30log), OOP pattern detection (4 libraries + manual setmetatable), rockspec/luacheckrc parsing, scanner + compressor + BPL integration, 50 BPL practices (LUA001-LUA050), 15 PracticeCategory enum values, 52 new unit tests, 1 bug fixed (#62), 3-repo validation (Lapis, Hawkthorne, Kong), 1406 total tests passing
> **Updated:** 13 February 2026 - Phase X: Dart Language Support (v4.27) — 5 Dart extractors (type, function, api, model, attribute), EnhancedDartParser with regex AST + optional tree-sitter-dart + dart analysis_server LSP, Dart 2.0-3.5+ support (null safety 2.12+, class modifiers 3.0+, records 3.0+, extension types 3.3+), Flutter 1.x-3.x+ (4 widget types), 70+ framework detection (Flutter/Riverpod/Bloc/GetX/Provider/Dio/Drift/Floor/Isar/Hive/Shelf/DartFrog/Serverpod), pubspec.yaml/pubspec.lock parsing, scanner + compressor + BPL integration, 50 BPL practices (DART001-DART050), 27 PracticeCategory enum values, 126 new unit tests, 4 bugs fixed (#58-61), 3-repo validation (Isar, Bloc, Shelf), 1354 total tests passing
> **Updated:** 13 February 2026 - Phase W: R Language Support (v4.26) — 5 R extractors (type, function, api, model, attribute), EnhancedRParser with regex AST + R-languageserver LSP, R 2.x-4.4+ support, 6 class systems (S3/S4/R5/R6/S7/proto), 70+ framework detection (tidyverse/Shiny/Plumber/data.table/arrow/Rcpp/caret/tidymodels/bioconductor/golem), DESCRIPTION/NAMESPACE/renv.lock parsing, scanner + compressor + BPL integration, 50 BPL practices (R001-R050), 62 new unit tests, 11 bugs fixed, 3-repo validation (dplyr, Shiny, plumber), 1228 total tests passing
> **Updated:** 13 February 2026 - Phase V: Scala Language Support (v4.25) — 5 Scala extractors (type, function, api, model, attribute), EnhancedScalaParser with regex AST + Metals LSP, Scala 2.x-3.x support, 25+ framework detection (Play/Akka/ZIO/http4s/Tapir/Cats/Spark), Slick/Doobie/Quill ORM, build.sbt parsing, scanner + compressor + BPL integration, 50 BPL practices (SCALA001-SCALA050), 132 new unit tests, 4 bugs fixed, 3-repo validation (Caliban, Play Samples, ZIO HTTP), 1166 total tests passing
> **Updated:** 12 February 2026 - Phase U: PHP Language Support (v4.24) — 5 PHP extractors (type, function, api, model, attribute), EnhancedPhpParser with regex AST, PHP 5.6-8.3+ support, 30+ framework detection, Laravel/Symfony/Doctrine ORM, composer.json parsing, scanner + compressor + BPL integration, 50 BPL practices (PHP001-PHP050), 84 new unit tests, 1034 total tests passing
> **Updated:** 12 February 2026 - Phase T: Ruby Language Support (v4.23) — 5 Ruby extractors (type, function, api, model, attribute), EnhancedRubyParser with regex AST + solargraph LSP, Ruby 1.8-3.3+ support, 10+ framework detection (Rails/Sinatra/Grape/Hanami/Roda), ActiveRecord/Sequel/Mongoid ORM, Gemfile parsing, scanner + compressor + BPL integration, 50 BPL practices (RB001-RB050), 80 new unit tests, route controller/action split, Gemfile name-based detection, 3-repo validation (Discourse, Faker, Mastodon), 950 total tests passing
> **Updated:** 12 February 2026 - Phase S: C++ Language Support (v4.20) — 5 C++ extractors (type, function, api, model, attribute), EnhancedCppParser with optional tree-sitter-cpp AST + clangd LSP, C++98-C++26 standard detection, 30+ framework detection, CRTP/concepts/coroutines/smart pointers, scanner + compressor + BPL integration, 50 BPL practices (CPP001-CPP050), 73 new unit tests, 8 bugs fixed (including .h disambiguation + silent exception swallowing), 3-repo validation (spdlog, fmt, nlohmann_json), 713 total tests passing
> **Updated:** 12 February 2026 - Phase R: C Language Support (v4.19) — 5 C extractors (type, function, api, model, attribute), EnhancedCParser with optional tree-sitter-c AST + clangd LSP, C89-C23 standard detection, 25+ framework detection, scanner + compressor + BPL integration, 50 BPL practices (C001-C050), 59 new unit tests, 9 bugs fixed (including critical attribute mismatches), 3-repo validation (jq, Redis, curl), 640 total tests passing
> **Updated:** 12 February 2026 - Phase O: HTML Language Support (v4.16) — 8 HTML extractors (structure, semantic, form, meta, accessibility, template, asset, component), EnhancedHTMLParser with Python html.parser AST, scanner + compressor + BPL integration, 50 BPL practices (HTML001-HTML050), 66 new unit tests, 0 bugs (clean implementation), 3-repo validation (HTML5 Boilerplate, Tabler, Foundation), 441 total tests passing
> **Updated:** 12 February 2026 - Phase N: SQL Language Support (v4.15) — 5 SQL extractors (type, function, index, security, migration), EnhancedSQLParser with 6-dialect detection, scanner + compressor + BPL integration, 50 BPL practices (SQL001-SQL050), 60 new unit tests, 7 bugs fixed, 3-repo validation (jOOQ/sakila, PostgREST, sql-server-samples), 375 total tests passing
> **Updated:** 12 February 2026 - Phase N: Rust Language Support (v4.14) — 5 Rust extractors (type, function, api, model, attribute), EnhancedRustParser, scanner + compressor + BPL integration, 50 BPL practices (RS001-RS050), 46 new unit tests, 6 bugs fixed, 3-repo validation (Axum, Diesel, actix-web), 315 total tests passing
> **Updated:** 12 February 2026 - Phase M: C# Language Support (v4.13) — 6 C# extractors (type, function, enum, api, model, attribute), EnhancedCSharpParser with optional tree-sitter-c-sharp, scanner + compressor + BPL integration, 50 BPL practices (CS001-CS050), 97 new unit tests, 10 bugs fixed, 3-repo validation (eShop, Ardalis CleanArchitecture, JT CleanArchitecture), 269 total tests passing
> **Updated:** 12 February 2026 - Phase L: Java & Kotlin Language Support (v4.12) — 6 Java extractors, 2 Kotlin extractors, tree-sitter-java AST, Eclipse JDT LSP, Panache entity detection, dedicated Kotlin parser, 50 Java BPL practices, 12 bugs fixed, 3-repo validation (Spring PetClinic, Quarkus Quickstarts, Micronaut Guides)
> **Updated:** 11 February 2026 - Phase K: Systemic Improvements (v4.11) — All 3 phases complete: weighted domain scoring with confidence/runner-up, unified FileClassifier wiring, multi-signal ORM/DB/MQ detection, discovery-driven stack detection, ORM-DB affinity graph with ORMEvidence dataclass. DB false positives reduced 46%.
> **Updated:** 11 February 2026 - Phase J: R4 Evaluation & .gitignore-Aware Scanning (v4.10) — GitignoreFilter for `.gitignore` + `.git/info/exclude`, all v5 extractors accept `gitignore_filter` param, R4 evaluation (Gitea/Strapi/Medusa), 18 pre-existing test failures fixed (397 pass)
> **Updated:** 9 February 2026 - Phase I: Targeted Extractor Fixes (v4.9) — BPL type detection from overview, runbook enrichment (contributing/examples/versions/license), test dir visibility in directory_summary
> **Updated:** 9 February 2026 - Phase H: Deep Pipeline Fixes (v4.8) — Brace-balanced extraction, adaptive compressor, BPL ratio limiting, directory summary, primary language priority
> **Use this checklist when adding a new programming language to CodeTrellis**
>
> **Updated:** 9 February 2026 - Phase G: PocketBase 16-Gap Remediation (v4.7) — BaaS domain, middleware factories, CLI commands, .d.ts filtering, route prefix tracking, plugin detection
> **Updated:** 9 February 2026 - Phase F: Go Language Support (v4.5), Generic Semantic Extraction (v4.6), PocketBase validated
> **Updated:** 6 February 2026 - Updated Phase 6 with audited counts, token budget, YAML validation, test patterns
> **Session Update:** 6 Feb 2026 (Afternoon) - BPL v1.1: `min_python`/`contexts` formalized in ApplicabilityRule, YAML warnings 0, `python -m.codetrellis` support added
> **Session Update:** 6 Feb 2026 (Evening) - JSON Schema added (`practice.schema.json`), pre-commit hooks configured, CI pipeline created
> **Session Update:** 6 Feb 2026 (Night) - BPL v1.2: Added React (40 practices) and NestJS (30 practices), 322 total practices, 5 new categories added
> **Session Update:** 7 Feb 2026 - BPL v1.3: Added Django (30), Flask (20), Database (20), DevOps (15) practices, 407 total practices, 4 new categories (automation, containers, deployment, infrastructure), new schema fields (complexity_score, anti_pattern_id)
> **Session Update:** 7 Feb 2026 (Night) - BPL v1.4: tiktoken integration for accurate GPT token counting, dynamic format selection (`OutputFormat.select_format_for_budget()`), 4 output tiers (minimal, compact, prompt, full)
> **Session Update:** 7 Feb 2026 (Late) - Phase A Remediation: RunbookExtractor (shell scripts, CI/CD, env vars), AI_ML/DEVTOOLS domain categories, `[AI_INSTRUCTION]` prompt header in matrix.prompt, 6 testing bugs fixed
> **Session Update:** 9 Feb 2026 - Phase D: Public Repository Validation Framework — .codetrellis validate-repos`CLI command, 60-repo corpus, quality_scorer.py, analyze_results.py, validation_runner.sh — CLI-verified on calcom/cal.com
**Session Update:** 9 Feb 2026 - Phase F: Go language support (v4.5) with 40 BPL practices, SemanticExtractor (v4.6) for hooks/middleware/routes/lifecycle, architecture detection for go.mod — validated on PocketBase, gin, go-admin
**Session Update:** 9 Feb 2026 - Phase G: 16-gap remediation (v4.7) —`DomainCategory.INFRASTRUCTURE`, CLI command detection (cobra/click/argparse/commander), 4 middleware factory patterns, 3 plugin patterns, .d.ts filtering, route group prefix tracking
**Session Update:** 11 Feb 2026 - Phase J: R4 evaluation (Gitea/Strapi/Medusa — 5 gaps fixed, domain accuracy 100%), GitignoreFilter (`.gitignore`+`.git/info/exclude`), 7 v5 extractors updated with `gitignore_filter` param, 18 test failures fixed
> **Session Update:** 11 Feb 2026 - Phase K: Systemic Improvements — Weighted domain scoring ({high,medium,low} tiers, confidence+runner-up), FileClassifier wired into 4 extractors, multi-signal ORM/DB/MQ detection (19 ORMs, 13 DBs, 10 MQs with {strong,medium,weak,anti} tiers), discovery-driven per-sub-project stack detection, ORMEvidence affinity graph with sub-project provenance. DB FPs: 26→14.

## Language: **\*\*\*\***\_**\*\*\*\*** | Date: \***\*\_\*\***

---

## Phase 0: Language Configuration Registry ✅ (Added Session 76)

> **Single source of truth:** `codetrellis/language_config.py`
> All language-aware lookups (file extensions, manifest files, linters, test tools, version detection) are defined here. Adding a new language starts by adding one `LanguageInfo` entry.

### 0.1 Add Entry to `LANGUAGES` Tuple

File: `codetrellis/language_config.py`

- [ ] Add a `LanguageInfo(...)` entry to the `LANGUAGES` tuple:

  ```python
  LanguageInfo(
      key="<lang>",                         # lowercase key (e.g., "rust", "go")
      display_name="<Lang>",                # human-readable (e.g., "Rust", "Go")
      extensions=frozenset({".<ext>"}),      # file extensions (e.g., {".rs"}, {".go"})
      manifest_files=frozenset({"<manifest>"}),  # e.g., {"Cargo.toml"}, {"go.mod"}
      version_file="<manifest>",            # file containing version string
      version_regex=r"<regex>",             # regex to extract version from version_file
      version_bump_hint="...",              # human instruction for version bumping
      aliases=frozenset({"<alias>"}),       # BPL/convention aliases (e.g., {"rust", "cargo"})
      linters=("ruff", "mypy"),             # linter tool names
      type_checkers=("mypy",),              # type checker tool names (can be empty)
      test_command="pytest tests/ -x -q",   # default test invocation
      test_tools=("pytest",),               # test framework names
      project_type_label="library",         # "library", "web-service", "cli", etc.
  )
  ```

### 0.2 Verify Derived Dicts

The following dicts are auto-built at import time from `LANGUAGES`:

| Dict                | Purpose                  | Consumer                 |
| ------------------- | ------------------------ | ------------------------ |
| `BY_KEY`            | key → LanguageInfo       | `init_integrations.py`   |
| `EXT_TO_LANG`       | extension → key          | `discovery_extractor.py` |
| `MANIFEST_TO_LANG`  | manifest file → key      | `discovery_extractor.py` |
| `EXT_TO_DISPLAY`    | extension → display name | `scanner.py`             |
| `ALIAS_MAP`         | alias → LanguageInfo     | `init_integrations.py`   |
| `LINTER_LANG`       | linter name → key        | `init_integrations.py`   |
| `TYPE_CHECKER_LANG` | type checker → key       | `init_integrations.py`   |
| `TEST_TOOL_LANG`    | test tool → key          | `init_integrations.py`   |

- [ ] After adding the entry, verify derived dicts pick it up:
  ```python
  from codetrellis.language_config import BY_KEY, EXT_TO_LANG
  assert "<lang>" in BY_KEY
  assert ".<ext>" in EXT_TO_LANG
  ```

### 0.3 Run Tests

- [ ] `pytest tests/ -x -q` — all existing tests must still pass
- [ ] No changes needed in `init_integrations.py`, `discovery_extractor.py`, or `scanner.py` — they read from `language_config` at import time

---

## Phase 1: Extractors ✅

### Directory Setup

- [ ] Create .codetrellis/extractors/<lang>/` directory
- [ ] Create .codetrellis/extractors/<lang>/**init**.py`

### Core Extractors (Required)

- [ ] `type_extractor.py` - Classes, interfaces, structs
- [ ] `function_extractor.py` - Functions, methods
- [ ] `enum_extractor.py` - Enums, constants

### Framework Extractors (As Needed)

- [ ] `api_extractor.py` - REST/GraphQL endpoints
- [ ] `model_extractor.py` - Database models
- [ ] `config_extractor.py` - Configuration classes

### Verify Exports

- [ ] All extractors exported in `__init__.py`
- [ ] Test: `from.codetrellis.extractors.<lang> import *`

---

## Phase 2: Parser ✅

### File: .codetrellis/<lang>\_parser_enhanced.py`

- [ ] Create `<Lang>ParseResult` dataclass

  ```python
  @dataclass
  class <Lang>ParseResult:
      file_path: str
      types: List[TypeInfo] = field(default_factory=list)
      functions: List[FunctionInfo] = field(default_factory=list)
      # Add more fields...
      detected_frameworks: List[str] = field(default_factory=list)
  ```

- [ ] Create `Enhanced<Lang>Parser` class
  - [ ] Add `FRAMEWORK_PATTERNS` dict for detection
  - [ ] Initialize all extractors in `__init__()`
  - [ ] Implement `parse()` method
  - [ ] Implement `_detect_frameworks()` method

### Verify Parser

- [ ] Test: `parser.parse(sample_code, 'test.ext')` returns valid result

---

## Phase 3: Scanner Integration ✅

### File: .codetrellis/scanner.py`

> **Note (v4.96):** The `ext_to_lang` dict in `scanner.py` is now imported from `codetrellis/language_config.py` as `EXT_TO_DISPLAY`. If you added the language in Phase 0, the extension→display-name mapping is automatic. You only need to add ProjectMatrix fields, the `_parse_<lang>()` method, and the dispatcher entry.

### 3.1 Add ProjectMatrix Fields

Location: `ProjectMatrix` dataclass (around line 90)

- [ ] Add core type fields:

  ```python
  <lang>_types: List[Dict] = field(default_factory=list)
  <lang>_functions: List[Dict] = field(default_factory=list)
  <lang>_enums: List[Dict] = field(default_factory=list)
  ```

- [ ] Add framework-specific fields:
  ```python
  <lang>_api_endpoints: List[Dict] = field(default_factory=list)
  <lang>_models: List[Dict] = field(default_factory=list)
  ```

### 3.2 Import Parser

Location: Top of file with other imports

- [ ] Add import:
  ```python
  from .<lang>_parser_enhanced import Enhanced<Lang>Parser
  ```

### 3.3 Initialize Parser

Location: `ProjectScanner.__init__()` method

- [ ] Add initialization:
  ```python
  self.<lang>_parser = Enhanced<Lang>Parser()
  ```

### 3.4 Update File Handling

Location: `_walk_directory()` method

- [ ] Add file extension handling:
  ```python
  elif suffix == '.<ext>':
      self._parse_<lang>(file_path, matrix)
  ```

### 3.5 Update Ignore Patterns

Location: `IGNORE_PATTERNS` list or `_should_ignore()` method

- [ ] Add language-specific ignores:
  ```python
  'target',     # Rust
  'vendor',     # Go
  '.gradle',    # Java
  ```

### 3.6 Create Parse Method

Location: After other `_parse_*()` methods

- [ ] Create `_parse_<lang>(self, file_path: Path, matrix: ProjectMatrix)`:
  - [ ] Read file content
  - [ ] Call parser
  - [ ] Populate matrix fields for each extracted type

### ⚠️ Attribute Matching Check

- [ ] Verify ParseResult attribute names match scanner access:
  - [ ] `result.types` vs `result.type`
  - [ ] `result.functions` vs `result.function`
  - [ ] `td.fields` vs `td.keys`

---

## Phase 4: Compressor Integration ✅

### File: .codetrellis/compressor.py`

### 4.1 Add Compression Methods

Location: After existing `_compress_*()` methods

- [ ] `_compress_<lang>_types(self, matrix) -> List[str]`
- [ ] `_compress_<lang>_api(self, matrix) -> List[str]`
- [ ] `_compress_<lang>_functions(self, matrix) -> List[str]`

### 4.2 Call in Main Compress Method

Location: `compress()` method

- [ ] Add calls with section headers:
  ```python
  lines.append("[<LANG>_TYPES]")
  lines.extend(self._compress_<lang>_types(matrix))
  ```

---

## Phase 5: Testing ✅

### Unit Tests

- [ ] Test individual extractors with sample code
- [ ] Test parser with comprehensive sample

### Integration Tests

- [ ] Test scanner with single file:
  ```python
  scanner._parse_<lang>(Path('test.ext'), matrix)
  assert len(matrix.<lang>_types) > 0
  ```

### CLI Test

- [ ] Run full scan:

  ```bash
  codetrellis scan /path/to/project --tier prompt
  ```

  Or using module entry point:

  ```bash
  python -m codetrellis scan /path/to/project --tier prompt
  ```

- [ ] Verify output contains `[<LANG>_*]` sections:
  ```bash
  grep "\[<LANG>_" matrix.prompt
  ```

### Validation Script

```python
# Run this to verify integration
from.codetrellis.extractors.<lang> import *
from.codetrellis.<lang>_parser_enhanced import Enhanced<Lang>Parser
from.codetrellis.scanner import ProjectScanner, ProjectMatrix
from.codetrellis.compressor import MatrixCompressor

scanner = ProjectScanner()
assert hasattr(scanner, '<lang>_parser')

matrix = ProjectMatrix(name='test', root_path='/')
assert hasattr(matrix, '<lang>_types')

compressor = MatrixCompressor()
assert hasattr(compressor, '_compress_<lang>_types')

print("✅ All integration checks passed!")
```

---

## Common Issues Checklist

- [ ] **AttributeError on parse result**: Check singular vs plural names
- [ ] **Empty matrix fields**: Check if parse method is being called
- [ ] **Unwanted files processed**: Update ignore patterns
- [ ] **Objects in output**: Convert to strings/dicts before storing

---

## Phase 6: BPL Integration ✅ (UPDATED 6 Feb 2026)

### 6.1 Create Practice YAML File

- [ ] Create .codetrellis/bpl/practices/<lang>\_core.yaml`
- [ ] Add 40-60 practices covering:
  - [ ] Type Safety (8-12 practices)
  - [ ] Error Handling (6-10 practices)
  - [ ] Performance (6-10 practices)
  - [ ] Security (8-12 practices)
  - [ ] Code Style (6-10 practices)
  - [ ] Testing (5-8 practices)
  - [ ] Architecture (5-8 practices)

> **Reference counts (audited 12 Feb 2026, updated):**
> python*core=17, python_core_expanded=60, python_3_10/11/12=12 each,
> typescript_core=45, angular=45, fastapi=10, solid_patterns=9, design_patterns=30,
> react=40, nestjs=30, **django=30** *(NEW)_, **flask=20** _(NEW)_,
> **database=20** _(NEW)_, **devops=15** _(NEW)_, **go_core=40** _(NEW v4.5)_,
> **java_core=50** _(NEW v4.12)\_.
> Total: 497 practices across 18 files.

### 6.2 Practice YAML Structure

```yaml
version: "1.0.0"
framework: <lang>
description: "<Lang> best practices"

practices:
  - id: <LANG>001 # Use language prefix (GO, RS, JAVA, etc.)
    title: "Practice Title"
    category: type_safety # Must exist in PracticeCategory enum
    level: beginner # beginner | intermediate | advanced
    priority: high # critical | high | medium | low
    applicability: # Optional: targeting rules
      frameworks: ["<lang>"] # Required frameworks
      min_python: "3.10" # Optional: min Python version (formalized in v1.1)
      contexts: ["web", "api"] # Optional: usage contexts (formalized in v1.1)
    content:
      description: |
        Multi-line description
      good_examples:
        - |
          // Good code example
      bad_examples:
        - |
          // Bad code example
      tags:
        - tag1
```

### 6.3 Validate YAML Practices

- [ ] Run YAML validation script:
  ```bash
  python3 scripts/validate_practices.py
  # Expected: 0 errors, 0 warnings. All fields (min_python, contexts) are now recognized.
  ```
- [ ] Verify no duplicate IDs across all practice files
- [ ] Verify all `category` values exist in `PracticeCategory` enum

### 6.4 Update Models (if needed)

File: .codetrellis/bpl/models.py`

- [ ] Add new PracticeCategory values if language has unique categories:
  ```python
  class PracticeCategory(Enum):
      CONCURRENCY = "concurrency"      # Go, Rust
      MEMORY_SAFETY = "memory_safety"  # Rust, C++
      # Added in v1.2 (React/NestJS expansion)
      VALIDATION = "validation"
      MONITORING = "monitoring"
      RELIABILITY = "reliability"
      ACCESSIBILITY = "accessibility"
      USER_EXPERIENCE = "user_experience"
  ```
- [ ] Also update `scripts/validate_practices.py` `VALID_CATEGORIES` set to match

> **Note (v1.2):** 5 new categories were added for React and NestJS practices.
> Remember to update both `models.py` and `validate_practices.py`.

> **Note (v1.1):** The `ApplicabilityRule` dataclass now supports `min_python: Optional[str]`
> and `contexts: tuple[str, ...]` as formalized fields. The `matches()` method performs
> Python version checking via tuple comparison. These fields are recognized by the
> YAML validation script — no warnings will be generated.

### 6.5 Update Selector - Framework Detection

File: .codetrellis/bpl/selector.py`-`ProjectContext.from_matrix()`

- [ ] Add framework dependency mapping:

  ```python
  <lang>_framework_mapping = {
      "framework1": ["dep1", "dep2"],
      "framework2": ["dep3"],
  }
  ```

- [ ] Add artifact counting:

  ```python
  <lang>_count = 0
  <lang>_artifacts = ["<lang>_types", "<lang>_functions"]
  for attr in <lang>_artifacts:
      if hasattr(matrix, attr):
          <lang>_count += len(getattr(matrix, attr, []))
  ```

- [ ] Add significance check:
  ```python
  if <lang>_count >= SIGNIFICANCE_THRESHOLD:
      context.frameworks.add("<lang>")
  ```

### 6.6 Update Selector - Practice ID Prefix Mapping (UPDATED v5.0)

File: `codetrellis/bpl/selector.py` — class attribute `_PREFIX_FRAMEWORK_MAP`

> **Note (v5.0):** The prefix→framework map is now a **class-level attribute** on
> `PracticeSelector`, not a local dict inside `_get_practice_frameworks()`. Language
> grouping for proportional allocation and CLI output is **auto-derived** from this
> map via `_derive_prefix_language_map()` — no separate language map needed.

- [ ] Add entries to `PracticeSelector._PREFIX_FRAMEWORK_MAP`:
  ```python
  _PREFIX_FRAMEWORK_MAP: ClassVar[dict[str, set[str]]] = {
      # ... existing entries ...

      # NEW: Add your language (root language — single-element set)
      "<LANG>": {"<lang>"},

      # NEW: Add framework prefixes (multi-element set includes parent language)
      "<FRAMEWORK>": {"<framework>", "<lang>"},
  }
  ```

- [ ] **Root language entries** must use a **single-element set** (e.g., `{"python"}`).
  This tells `_derive_prefix_language_map()` that this is a root language, not a child.

- [ ] **Framework entries** must include the parent language in the set (e.g., `{"flask", "python"}`).
  This creates a child→parent edge so Flask practices are grouped under Python.

- [ ] **What happens automatically** once entries are added:
  | Mechanism | What it does | No manual edit needed |
  |---|---|---|
  | `_derive_prefix_language_map()` | Maps prefix→root language for grouping | Auto-derived from `_PREFIX_FRAMEWORK_MAP` |
  | `_get_practice_language()` | Returns language for any practice by longest-prefix match | Uses cached language map |
  | `_allocate_proportional_slots()` | Distributes practice slots fairly across detected languages | Uses `_get_practice_language()` |
  | CLI `_generate_practices_section()` | Groups practices by language in output (e.g., `## PYTHON (5)`) | Uses `_get_practice_language()` |

### 6.7 Update Selector - Applicability Filter

File: `codetrellis/bpl/selector.py` — `_filter_applicable()`

- [ ] Add language detection:

  ```python
  has_<lang> = any(f in context_frameworks for f in ["<lang>", "framework1"])
  ```

- [ ] Add filtering logic:
  ```python
  if "<lang>" in practice_frameworks:
      if has_<lang>:
          result.append(practice)
      continue
  ```

### 6.8 BPL Testing

- [ ] Verify practices load:

  ```bash
  python -c "
  from.codetrellis.bpl import get_repository
  repo = get_repository()
  repo.load_all()
  print([p.id for p in repo.practices.values() if p.id.startswith('<LANG>')][:5])
  "
  ```

- [ ] Test context detection:

  ```bash
  python -c "
  from.codetrellis.scanner import ProjectScanner
  from.codetrellis.bpl.selector import ProjectContext

  scanner = ProjectScanner()
  matrix = scanner.scan('/path/to/<lang>/project')
  context = ProjectContext.from_matrix(matrix)
  print(f'Frameworks: {context.frameworks}')
  "
  ```

- [ ] Test practice selection:

  ```bash
  codetrellis scan /path/to/<lang>/project --include-practices --practices-format minimal
  # Verify: Shows <LANG>* practices, NOT other language practices
  ```

- [ ] Test token budget enforcement:

  ```bash
  codetrellis scan /path/to/<lang>/project --include-practices --max-practice-tokens 200
  # Verify: Only 1-2 practices returned under tight budget
  ```

- [ ] Test with pure <lang> project - should NOT show Python/TS practices
- [ ] Test with mixed project - should show both language practices

### 6.9 Add Unit Tests

- [ ] Create `tests/unit/test_bpl_<lang>.py` with tests for:
  - [ ] Practice loading and count verification
  - [ ] Context detection from matrix
  - [ ] Practice filtering for the language
  - [ ] Token budget with new practices
  - [ ] Format output (minimal/standard/comprehensive)

> **Reference:** See existing test files for patterns:
>
> - `tests/unit/test_bpl_models.py` (43 tests)
> - `tests/unit/test_bpl_repository.py` (35 tests)
> - `tests/unit/test_bpl_selector.py` (47 tests)

### 6.10 Run Full Validation

- [ ] Run YAML validation: `python3 scripts/validate_practices.py`
- [ ] Run all BPL tests: `python3 -m pytest tests/unit/test_bpl_*.py -v`
- [ ] Run CLI verification for all 3 formats
- [ ] Verify total practice count increased correctly

---

## Phase 7: Cross-Cutting Extractor Integration (Added 7 Feb 2026)

> **Context:** Phase A remediation added cross-cutting extractors that apply to ALL languages, not just a specific language. These are lessons learned for future implementations.
> **Update (v4.96):** `discovery_extractor.py` now imports `EXT_TO_LANG` and `MANIFEST_TO_LANG` from `codetrellis/language_config.py` instead of maintaining its own `LANGUAGE_MAP` and `MANIFEST_LANGUAGE` dicts. Adding a language in Phase 0 automatically makes it discoverable by the discovery extractor — no manual dict edits needed.

### 7.1 RunbookExtractor — Execution Context

The `RunbookExtractor` is a **cross-cutting extractor** that works independently of language-specific parsers. It auto-extracts execution context from project config files.

**Key Files:**

- .codetrellis/extractors/runbook_extractor.py` — Main extractor class (~920 lines)
- .codetrellis/extractors/**init**.py` — Export RunbookExtractor + dataclasses

**What it extracts:**

| Source File                                                      | Data Extracted                            |
| ---------------------------------------------------------------- | ----------------------------------------- |
| `package.json` scripts                                           | Run/build/test/lint/deploy commands       |
| `pyproject.toml` scripts                                         | Python CLI entry points                   |
| `Makefile` targets                                               | Build targets with descriptions           |
| `*.sh` (root level)                                              | Shell scripts with first-line description |
| `Dockerfile`                                                     | Base image, EXPOSE ports, CMD/ENTRYPOINT  |
| `docker-compose.yml`                                             | Services, ports, env vars, depends_on     |
| `.env.example`                                                   | Required environment variables            |
| `.github/workflows/*.yml`                                        | GitHub Actions pipeline steps             |
| `.gitlab-ci.yml`                                                 | GitLab CI pipeline steps                  |
| `Jenkinsfile`, `.circleci/config.yml`, `bitbucket-pipelines.yml` | Other CI/CD                               |
| `README.md`                                                      | Installation/usage sections               |

**Integration pattern for new extractors:**

1. Create extractor with `extract(project_path) -> DataContext` pattern
2. Add dataclass field to `ProjectMatrix` in `scanner.py`
3. Create `_extract_<name>()` method in scanner, call from `scan()`
4. Add `_compress_<name>()` method in `compressor.py`
5. Call compression in `compress()` — emit at ALL tiers for critical context

**Testing lesson:** Always test with `--optimal` on 2+ real projects via CLI. Do NOT rely on unit tests alone — 6 integration bugs were found only through real CLI runs.

### 7.2 Domain Category Extension

When adding new domain categories to `business_domain_extractor.py`:

- [ ] Add enum value to `DomainCategory` (e.g., `AI_ML = "AI/ML Platform"`)
- [ ] Add indicators to `DOMAIN_INDICATORS` dict (minimum 15-20 keywords)
- [ ] Add description to `_generate_domain_description()`
- [ ] Indicators should be **unique** to the domain — avoid generic terms that overlap (e.g., "model" overlaps AI_ML and Trading)
- [ ] Set minimum score threshold (currently 3) to avoid false positives

**Domains added in Phase A:** `AI_ML` (23 indicators), `DEVTOOLS` (18 indicators)
**Domains added in Phase G:** `INFRASTRUCTURE` (~40 indicators — BaaS, PaaS, API gateways, auth services, storage, webhooks)

### 7.3 `[AI_INSTRUCTION]` Prompt Header

Every `matrix.prompt` now starts with an `[AI_INSTRUCTION]` section that instructs any AI consumer to:

- Read the entire file before responding
- Follow best practices from the BEST_PRACTICES section
- Reference RUNBOOK for run/build/test/deploy commands
- Respect architectural patterns from PROJECT_STRUCTURE/OVERVIEW
- Prioritize ACTIONABLE_ITEMS
- Not hallucinate file paths, function names, or APIs

**Implementation:** In `compressor.py` → `compress()` method, before the header line.

**Important:** Do NOT use `[SECTION_NAME]` syntax inside instruction text — the CLI's `re.sub` post-processing strips content that looks like section headers.

---

## Phase 8: Semantic Extraction Integration (Added 9 Feb 2026)

> **Context:** Phase F added the `SemanticExtractor` — a language-agnostic behavioral pattern detector. New languages get hook/middleware/route/lifecycle detection automatically.

### 8.1 Automatic Coverage (No Work Required)

The `SemanticExtractor` runs on ALL source files automatically. For a new language, you get:

- [x] **Hook/event detection**: On\* methods, BindFunc, AddListener, Subscribe, addEventListener, emit
- [x] **Middleware detection**: .Use(), middleware function returns, chain patterns, **exported factory functions** (v4.7), **Bind() inline binding** (v4.7), **middleware ID constants** (v4.7)
- [x] **Route detection**: Generic HTTP method calls, HandleFunc, handler signatures
- [x] **Plugin detection**: Register, Plugin, Extension, AddPlugin, **MustRegister** (v4.7), **interface-based plugins** (v4.7), **Mount/sub-app** (v4.7)
- [x] **Lifecycle detection**: Init, Start, Stop, Shutdown, Close, Serve, Run, Destroy, Cleanup
- [x] **CLI command detection** (NEW v4.7): cobra (`cobra.Command{Use:}`), click (`@click.command`), argparse (`add_parser`), commander (`.command()`)

### 8.2 Verify Semantic Extraction

- [ ] Run scan on new language project and verify `[HOOKS]` section populated
- [ ] Verify `[MIDDLEWARE]` section if applicable — check factory functions are detected, not just `.Use()` calls
- [ ] Verify `[ROUTES_SEMANTIC]` section (check path validation filters false positives)
- [ ] Verify `[LIFECYCLE]` section
- [ ] Verify `[CLI_COMMANDS]` section if project has CLI tools (NEW v4.7)
- [ ] Verify no `.d.ts` or declaration files appear in semantic/logic sections (NEW v4.7)

### 8.3 Add Language-Specific Patterns (Optional)

If the language/framework has unique behavioral patterns not covered by generic heuristics:

- [ ] Add new patterns to `HOOK_PATTERNS` in `semantic_extractor.py`
- [ ] Add new patterns to `MIDDLEWARE_PATTERNS` — especially middleware factory functions unique to the framework
- [ ] Add new patterns to `PLUGIN_PATTERNS` — check for framework-specific registration APIs
- [ ] Add new patterns to `CLI_COMMAND_PATTERNS` if framework has unique CLI tools (NEW v4.7)
- [ ] Add new patterns to `ROUTE_PATTERNS`, etc.
- [ ] Update `_is_valid_route_path()` if route false positives occur

**Example:** PocketBase required adding `\.BindFunc\s*\(` for Go-specific hook registration.
**Example (v4.7):** PocketBase required adding `func\s+(RequireAuth|Skip\w+|BodyLimit|CORS|Gzip)\s*\(` for exported middleware factories.

### 8.4 Route Group Prefix Tracking (NEW v4.7)

For frameworks that use route grouping (Go `Group()`, Express `Router()`, Flask `Blueprint()`, NestJS `@Controller()`):

- [ ] Add Group/Blueprint/Controller prefix assignment pattern to API extractor
- [ ] Build variable→prefix map (resolve chained groups: `api = r.Group("/api")`, `v2 = api.Group("/v2")` → `"/api/v2"`)
- [ ] Apply prefix when extracting child routes from group variables
- [ ] Test: verify `/backups/create` shows as `{prefix}/backups/create` in `[<LANG>_API]`

**Already implemented for Go** (v4.7). Follow same pattern for Express/Flask/NestJS.

### 8.5 File Filtering for Semantic & Logic Extraction (NEW v4.7)

When a project embeds UI or type stubs from other languages:

- [ ] Filter `.d.ts` files in `_extract_logic()` (TypeScript declaration stubs)
- [ ] Filter `.d.ts` files in `_extract_semantics()` (prevents false hooks/routes)
- [ ] Check for similar patterns in your language:
  - Rust: filter `.rlib` files, `target/` directory
  - Java: filter `.class` files, `build/` directory
  - C#: filter `.Designer.cs` (auto-generated UI code)
  - PHP: filter `vendor/` (Composer dependencies)
- [ ] Verify: no auto-generated or declaration files appear in `[IMPLEMENTATION_LOGIC]` or `[LIFECYCLE]`

---

## Phase 9: Architecture Detection (Added 9 Feb 2026)

> **Context:** Phase F revealed that `can_extract()` and `_detect_project_type()` were hardcoded for Python/Node.js projects. New languages need architecture detection updates.

### 9.1 Update `can_extract()`

File: .codetrellis/extractors/architecture_extractor.py`

- [ ] Add language manifest file to `can_extract()`:
  ```python
  # Example: go.mod for Go, Cargo.toml for Rust, pom.xml for Java
  manifest_files = ['package.json', 'requirements.txt', 'pyproject.toml',
                    'go.mod', 'Cargo.toml', 'pom.xml', 'build.gradle']
  ```

### 9.2 Add Project Type Detection

File: .codetrellis/extractors/architecture_extractor.py`-`\_detect_project_type()`

- [ ] Add project type enum values (e.g., `GO_CLI`, `GO_WEB_SERVICE`, `GO_FRAMEWORK`)
- [ ] Add detection logic reading the manifest file
- [ ] Detect project category (CLI tool, library, web service, framework) from file structure

### 9.3 Add Dependency Parsing

File: .codetrellis/scanner.py`-`\_extract_dependencies()`

- [ ] Parse language manifest file for dependencies
- [ ] Categorize deps (web, db, auth, testing, etc.)
- [ ] Add compressed output section (e.g., `[GO_DEPENDENCIES]`)

---

## Sign-off

| Phase                   | Status | Verified By | Date |
| ----------------------- | ------ | ----------- | ---- |
| Language Config (v4.96) | ⬜     |             |      |
| Extractors              | ⬜     |             |      |
| Parser                  | ⬜     |             |      |
| Scanner                 | ⬜     |             |      |
| Compressor              | ⬜     |             |      |
| Testing                 | ⬜     |             |      |
| BPL Integration         | ⬜     |             |      |
| Cross-Cutting           | ⬜     |             |      |
| Semantic Extraction     | ⬜     |             |      |
| Architecture Detection  | ⬜     |             |      |
| A5.x Module Integration | ⬜     |             |      |
| File Filtering (v4.7)   | ⬜     |             |      |

### Completed Language Sign-offs

#### Java (v4.12 — 12 Feb 2026)

| Phase                  | Status | Notes                                                            |
| ---------------------- | ------ | ---------------------------------------------------------------- |
| Extractors             | ✅     | 6 extractors: type, function, api, model, annotation, dependency |
| Parser                 | ✅     | EnhancedJavaParser + tree-sitter-java AST + Eclipse JDT LSP      |
| Scanner                | ✅     | 10 java\_\* fields, `_parse_java()`, Maven/Gradle dep dedup      |
| Compressor             | ✅     | 4 sections: JAVA_TYPES, JAVA_API, JAVA_MODELS, JAVA_DEPENDENCIES |
| Testing                | ✅     | 3-repo validation (PetClinic, Quarkus, Micronaut)                |
| BPL Integration        | ✅     | 50 practices (JAVA001-JAVA050) in java_core.yaml                 |
| Cross-Cutting          | ✅     | RunbookExtractor, domain, architecture detection all work        |
| Semantic Extraction    | ✅     | Hooks, middleware, lifecycle detected automatically              |
| Architecture Detection | ✅     | pom.xml/build.gradle parsed, project type detected               |
| File Filtering (v4.7)  | ✅     | FileClassifier handles `src/main/java` paths                     |

#### Kotlin (v4.12 — 12 Feb 2026)

| Phase                  | Status | Notes                                                                      |
| ---------------------- | ------ | -------------------------------------------------------------------------- |
| Extractors             | ✅     | 2 Kotlin + reuses 3 Java extractors (api, model, annotation)               |
| Parser                 | ✅     | EnhancedKotlinParser with 20+ framework patterns, 11 feature patterns      |
| Scanner                | ✅     | 10 kotlin\_\* fields, `_parse_kotlin()`, `.kt`/`.kts` routing              |
| Compressor             | ✅     | 4 sections: KOTLIN_TYPES, KOTLIN_FUNCTIONS, KOTLIN_API, KOTLIN_MODELS      |
| Testing                | ✅     | Micronaut Guides: 374 classes, 528 functions, 47 endpoints                 |
| BPL Integration        | ⬜     | Not yet created (future: 30-40 practices for coroutines, null safety, DSL) |
| Cross-Cutting          | ✅     | RunbookExtractor, domain detection all work                                |
| Semantic Extraction    | ✅     | Hooks, middleware, lifecycle detected automatically                        |
| Architecture Detection | ✅     | Uses Java's manifest detection (pom.xml/build.gradle)                      |
| File Filtering (v4.7)  | ✅     | FileClassifier handles `src/main/kotlin` paths                             |

#### PowerShell (v4.29 — 14 Feb 2026)

| Phase                  | Status | Notes                                                                             |
| ---------------------- | ------ | --------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: type, function, api, model, attribute (17 dataclasses)              |
| Parser                 | ✅     | EnhancedPowerShellParser with 30+ framework patterns, PS Core detection           |
| Scanner                | ✅     | 23 ps\_\* fields, `_parse_powershell()`, `.ps1/.psm1/.psd1/.ps1xml` routing       |
| Compressor             | ✅     | 5 sections: PS_TYPES, PS_FUNCTIONS, PS_API, PS_MODELS, PS_DEPENDENCIES            |
| Testing                | ✅     | 57 tests, 3-repo validation (Pode, SqlServerDsc, Pester)                          |
| BPL Integration        | ✅     | 50 practices (PS001-PS050) in powershell_core.yaml, 14 PracticeCategory values    |
| Cross-Cutting          | ✅     | discovery_extractor LANGUAGE_MAP, ext_to_lang stats                               |
| Semantic Extraction    | ✅     | Cmdlet bindings, pipelines, DSC configs, Pester tests detected                    |
| Architecture Detection | ✅     | Module manifest parsing, PS version detection, framework detection                |
| File Filtering (v4.7)  | ✅     | `.ps1/.psm1/.psd1/.ps1xml` recognized, PSModuleDevelopment/.psmodulecache ignored |

#### JavaScript (v4.30 — 14 Feb 2026)

| Phase                  | Status | Notes                                                                                |
| ---------------------- | ------ | ------------------------------------------------------------------------------------ |
| Extractors             | ✅     | 5 extractors: type, function, api, model, attribute (17 dataclasses)                 |
| Parser                 | ✅     | EnhancedJavaScriptParser with 70+ framework patterns, ES version detection           |
| Scanner                | ✅     | 24 js\_\* fields, `_parse_javascript()`, `.js/.jsx/.mjs/.cjs` routing                |
| Compressor             | ✅     | 5 sections: JS_TYPES, JS_FUNCTIONS, JS_API, JS_MODELS, JS_DEPENDENCIES               |
| Testing                | ✅     | 88 tests, 3-repo validation (Express.js, Ghost, Nodemailer)                          |
| BPL Integration        | ✅     | 50 practices (JS001-JS050) in javascript_core.yaml, 15 PracticeCategory values       |
| Cross-Cutting          | ✅     | ext_to_lang stats, BPL has_javascript detection, priority-based scoring              |
| Semantic Extraction    | ✅     | ES6 classes, prototypes, arrow functions, IIFEs, generators, JSDoc detected          |
| Architecture Detection | ✅     | package.json framework detection, module system detection (CommonJS/ESM), ES version |
| File Filtering (v4.7)  | ✅     | `.js/.jsx/.mjs/.cjs` recognized, node_modules/dist/build ignored                     |

#### Material UI / MUI (v4.36 — 15 Feb 2026)

| Phase                  | Status | Notes                                                                           |
| ---------------------- | ------ | ------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: component, theme, hook, style, api (15+ dataclasses)              |
| Parser                 | ✅     | EnhancedMuiParser with 30+ ecosystem patterns, MUI v0.x-v6.x detection          |
| Scanner                | ✅     | 20 mui\_\* fields, `_parse_mui()`, JS/TS file routing                           |
| Compressor             | ✅     | 5 sections: MUI_COMPONENTS, MUI_THEMES, MUI_HOOKS, MUI_STYLES, MUI_API_PATTERNS |
| Testing                | ✅     | 43 tests, 3-repo validation (devias-kit, minimal-ui-kit, react-material-admin)  |
| BPL Integration        | ✅     | 50 practices (MUI001-MUI050) in mui_core.yaml, 10 PracticeCategory values       |
| Cross-Cutting          | ✅     | Framework-level parser runs on JS/TS files alongside React                      |
| Semantic Extraction    | ✅     | 130+ components, styled patterns, sx prop, makeStyles, tss-react, Pigment CSS   |
| Architecture Detection | ✅     | package.json MUI ecosystem detection, version detection (v0.x-v6.x)             |
| File Filtering (v4.7)  | ✅     | Runs on `.js/.jsx/.ts/.tsx` files, skips node_modules                           |

#### Ant Design / Antd (v4.37 — 15 Feb 2026)

| Phase                  | Status | Notes                                                                                  |
| ---------------------- | ------ | -------------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: component, theme, hook, style, api (16 dataclasses)                      |
| Parser                 | ✅     | EnhancedAntdParser with 40+ ecosystem patterns, v1-v5 detection, CommonJS support      |
| Scanner                | ✅     | 20 antd\_\* fields, `_parse_antd()`, JS/TS file routing                                |
| Compressor             | ✅     | 5 sections: ANTD_COMPONENTS, ANTD_THEME, ANTD_HOOKS, ANTD_STYLES, ANTD_API             |
| Testing                | ✅     | 52 tests, 2-repo validation (ant-design-pro, antd-admin)                               |
| BPL Integration        | ✅     | 50 practices (ANTD001-ANTD050) in antd_core.yaml, 10 PracticeCategory values           |
| Cross-Cutting          | ✅     | Framework-level parser runs on JS/TS files alongside React                             |
| Semantic Extraction    | ✅     | 80+ components, Pro components, ConfigProvider, design tokens, Less, CSS-in-JS, hooks  |
| Architecture Detection | ✅     | package.json Antd ecosystem detection, version detection (v1-v5), umi/ahooks detection |
| File Filtering (v4.7)  | ✅     | Runs on `.js/.jsx/.ts/.tsx` files, skips node_modules                                  |

#### Chakra UI (v4.38 — 15 Feb 2026)

| Phase                  | Status | Notes                                                                                  |
| ---------------------- | ------ | -------------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: component, theme, hook, style, api (15 dataclasses)                      |
| Parser                 | ✅     | EnhancedChakraParser with 30+ ecosystem patterns, v1-v3/Ark UI detection               |
| Scanner                | ✅     | 22 chakra\_\* fields, `_parse_chakra()`, JS/TS file routing                            |
| Compressor             | ✅     | 5 sections: CHAKRA_COMPONENTS, CHAKRA_THEME, CHAKRA_HOOKS, CHAKRA_STYLES, CHAKRA_API   |
| Testing                | ✅     | 53 tests, 3-repo validation (nextarter-chakra, myPortfolio, chakra-ui/chakra-ui)       |
| BPL Integration        | ✅     | 50 practices (CHAKRA001-CHAKRA050) in chakra_core.yaml, 10 PracticeCategory values     |
| Cross-Cutting          | ✅     | Framework-level parser runs on JS/TS files alongside React                             |
| Semantic Extraction    | ✅     | 70+ components, extendTheme/createSystem/defineConfig, recipes, semantic tokens, hooks |
| Architecture Detection | ✅     | package.json Chakra ecosystem detection, version detection (v1-v3), Ark UI detection   |
| File Filtering (v4.7)  | ✅     | Runs on `.js/.jsx/.ts/.tsx` files, skips node_modules                                  |

#### shadcn/ui (v4.39 — Session 27)

| Phase                  | Status | Notes                                                                                  |
| ---------------------- | ------ | -------------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: component, theme, hook, style, api (16 dataclasses)                      |
| Parser                 | ✅     | EnhancedShadcnParser with 30+ ecosystem patterns, v0-v3 detection, Radix UI            |
| Scanner                | ✅     | 17 shadcn\_\* fields, `_parse_shadcn()`, JS/TS/CSS file routing                        |
| Compressor             | ✅     | 5 sections: SHADCN_COMPONENTS, SHADCN_THEME, SHADCN_HOOKS, SHADCN_STYLES, SHADCN_API   |
| Testing                | ✅     | 63 tests, 2-repo validation (shadcn-ui/taxonomy, shadcn-ui/ui)                         |
| BPL Integration        | ✅     | 50 practices (SHADCN001-SHADCN050) in shadcn_core.yaml, 10 PracticeCategory values     |
| Cross-Cutting          | ✅     | Framework-level parser runs on JS/TS/CSS files alongside React                         |
| Semantic Extraction    | ✅     | 40+ components, cn() utility, CVA, Radix primitives, components.json, CSS variables    |
| Architecture Detection | ✅     | Import-path-based detection (@/components/ui/\*), version detection (v0-v3), ecosystem |
| File Filtering (v4.7)  | ✅     | Runs on `.js/.jsx/.ts/.tsx/.css` files, skips node_modules                             |

#### Bootstrap (v4.40 — Session 28)

| Phase                  | Status | Notes                                                                                                     |
| ---------------------- | ------ | --------------------------------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: component, grid, theme, utility, plugin (12+ dataclasses)                                   |
| Parser                 | ✅     | EnhancedBootstrapParser with 16 framework patterns, v3-v5.3+ detection                                    |
| Scanner                | ✅     | 15 bootstrap\_\* fields, `_parse_bootstrap()`, HTML/CSS/JS/TS file routing                                |
| Compressor             | ✅     | 5 sections: BOOTSTRAP_COMPONENTS, BOOTSTRAP_GRID, BOOTSTRAP_THEME, BOOTSTRAP_UTILITIES, BOOTSTRAP_PLUGINS |
| Testing                | ✅     | 64 tests, 2-repo validation (sb-admin-2, react-bootstrap)                                                 |
| BPL Integration        | ✅     | 50 practices (BOOT001-BOOT050) in bootstrap_core.yaml, 10 PracticeCategory values                         |
| Cross-Cutting          | ✅     | Framework-level parser runs on HTML/CSS/JS/TS files                                                       |
| Semantic Extraction    | ✅     | 50+ components, grid system, SCSS/CSS variables, 16 utility categories, 12 JS plugins                     |
| Architecture Detection | ✅     | CSS class-based detection, data-bs-\* attributes, version detection (v3-v5.3+)                            |
| File Filtering (v4.7)  | ✅     | Runs on `.html/.css/.scss/.js/.jsx/.ts/.tsx` files, skips node_modules                                    |

#### Zustand (v4.48 — Session 36)

| Phase                  | Status | Notes                                                                                           |
| ---------------------- | ------ | ----------------------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: store, selector, middleware, action, api (16 dataclasses)                         |
| Parser                 | ✅     | EnhancedZustandParser with 16 framework + 20 feature patterns, v1-v5 detection                  |
| Scanner                | ✅     | 17 zustand\_\* fields, `_parse_zustand()`, JS/TS file routing                                   |
| Compressor             | ✅     | 5 sections: ZUSTAND_STORES, ZUSTAND_SELECTORS, ZUSTAND_MIDDLEWARE, ZUSTAND_ACTIONS, ZUSTAND_API |
| Testing                | ✅     | 57 tests, 2-repo validation (pmndrs/zustand, zustand-app)                                       |
| BPL Integration        | ✅     | 50 practices (ZUSTAND001-ZUSTAND050) in zustand_core.yaml, 10 PracticeCategory values           |
| Cross-Cutting          | ✅     | Framework-level parser runs on JS/TS/JSX/TSX files                                              |
| Semantic Extraction    | ✅     | Stores, slices, selectors, middleware, actions, subscriptions, imperative API, TypeScript types |
| Architecture Detection | ✅     | Version detection (v1-v5), framework detection (vanilla, middleware, persist, devtools, immer)  |
| File Filtering (v4.7)  | ✅     | Runs on `.js/.jsx/.ts/.tsx` files, skips node_modules                                           |

#### Jotai (v4.49 — Session 37)

| Phase                  | Status | Notes                                                                                        |
| ---------------------- | ------ | -------------------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: atom, selector, middleware, action, api (15 dataclasses)                       |
| Parser                 | ✅     | EnhancedJotaiParser with 17 framework + 34 feature patterns, v1-v2 detection                 |
| Scanner                | ✅     | 18 jotai\_\* fields, `_parse_jotai()`, JS/TS file routing                                    |
| Compressor             | ✅     | 5 sections: JOTAI_ATOMS, JOTAI_SELECTORS, JOTAI_MIDDLEWARE, JOTAI_ACTIONS, JOTAI_API         |
| Testing                | ✅     | 98 tests, validation scan (jotai-test-repo: 10 atoms, 7 hooks, 6 store usages)               |
| BPL Integration        | ✅     | 50 practices (JOTAI001-JOTAI050) in jotai_core.yaml, 10 PracticeCategory values              |
| Cross-Cutting          | ✅     | Framework-level parser runs on JS/TS/JSX/TSX files                                           |
| Semantic Extraction    | ✅     | Atoms, families, derived, selectors, focus, split, storage, effects, hooks, store API, types |
| Architecture Detection | ✅     | Version detection (v1-v2), framework detection (jotai-utils, optics, immer, vanilla, etc.)   |
| File Filtering (v4.7)  | ✅     | Runs on `.js/.jsx/.ts/.tsx` files, skips node_modules                                        |

#### Recoil (v4.50 — Session 37.5)

| Phase                  | Status | Notes                                                                                             |
| ---------------------- | ------ | ------------------------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: atom, selector, hook, effect, api (15 dataclasses)                                  |
| Parser                 | ✅     | EnhancedRecoilParser with regex AST, Recoil v0.x version detection                                |
| Scanner                | ✅     | 14 recoil\_\* fields, `_parse_recoil()`, JS/TS file routing                                       |
| Compressor             | ✅     | 5 sections: RECOIL_ATOMS, RECOIL_SELECTORS, RECOIL_HOOKS, RECOIL_EFFECTS, RECOIL_API              |
| Testing                | ✅     | 108 tests, all passing                                                                            |
| BPL Integration        | ✅     | 50 practices (RECOIL001-RECOIL050) in recoil_core.yaml                                            |
| Cross-Cutting          | ✅     | Framework-level parser runs on JS/TS/JSX/TSX files                                                |
| Semantic Extraction    | ✅     | Atoms, families, selectors, hooks, effects, snapshots, RecoilRoot, integrations, TypeScript types |
| Architecture Detection | ✅     | Version detection (v0.x), framework detection (recoil, recoil-relay, recoil-sync, recoil-nexus)   |
| File Filtering (v4.7)  | ✅     | Runs on `.js/.jsx/.ts/.tsx` files, skips node_modules                                             |

#### MobX (v4.51 — Session 38)

| Phase                  | Status | Notes                                                                                          |
| ---------------------- | ------ | ---------------------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: observable, computed, action, reaction, api (11 dataclasses)                     |
| Parser                 | ✅     | EnhancedMobXParser with 16 framework + 20 feature patterns, v3-v6 detection                    |
| Scanner                | ✅     | 14 mobx\_\* fields, `_parse_mobx()`, JS/TS file routing                                        |
| Compressor             | ✅     | 5 sections: MOBX_OBSERVABLES, MOBX_COMPUTEDS, MOBX_ACTIONS, MOBX_REACTIONS, MOBX_API           |
| Testing                | ✅     | 72 tests, 3-repo validation (mobxjs/mobx, mobx-state-tree, react-mobx-realworld)               |
| BPL Integration        | ✅     | 50 practices (MOBX001-MOBX050) in mobx_core.yaml, 9 PracticeCategory values                    |
| Cross-Cutting          | ✅     | Framework-level parser runs on JS/TS/JSX/TSX files                                             |
| Semantic Extraction    | ✅     | Observables, computeds, actions, flows, reactions, observers, inject, stores, TypeScript types |
| Architecture Detection | ✅     | Version detection (v3-v6), framework detection (mobx-react, mobx-state-tree, mobx-utils)       |
| File Filtering (v4.7)  | ✅     | Runs on `.js/.jsx/.ts/.tsx` files, skips node_modules                                          |

#### Pinia (v4.52 — Session 39)

| Phase                  | Status | Notes                                                                                                       |
| ---------------------- | ------ | ----------------------------------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: store, getter, action, plugin, api (15 dataclasses)                                           |
| Parser                 | ✅     | EnhancedPiniaParser with 30 framework + 20 feature patterns, v0-v3 detection                                |
| Scanner                | ✅     | 14 pinia\_\* fields, `_parse_pinia()`, JS/TS/Vue file routing                                               |
| Compressor             | ✅     | 5 sections: PINIA_STORES, PINIA_GETTERS, PINIA_ACTIONS, PINIA_PLUGINS, PINIA_API                            |
| Testing                | ✅     | 60 tests, 3-repo validation (vuejs/pinia, piniajs/example-vue-3-vite, wobsoriano/pinia-shared-state)        |
| BPL Integration        | ✅     | 50 practices (PINIA001-PINIA050) in pinia_core.yaml, 9 PracticeCategory values                              |
| Cross-Cutting          | ✅     | Framework-level parser runs on JS/TS/Vue files alongside Vue parser                                         |
| Semantic Extraction    | ✅     | Stores (Options/Setup), getters, actions, $patch, $subscribe, $onAction, plugins, storeToRefs, HMR, persist |
| Architecture Detection | ✅     | Version detection (v0-v3), framework detection (pinia, @pinia/nuxt, @pinia/testing, pinia-plugin-\*)        |
| File Filtering (v4.7)  | ✅     | Runs on `.js/.jsx/.ts/.tsx/.vue` files, skips node_modules                                                  |

#### Lit / Web Components (v4.65 — Session 51)

| Phase                  | Status | Notes                                                                                                                  |
| ---------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------- |
| Extractors             | ✅     | 5 extractors: component, property, event, template, api (15 dataclasses)                                               |
| Parser                 | ✅     | EnhancedLitParser with 25+ framework + 35+ feature patterns, Polymer 1.x-3.x / lit-element 2.x / lit 2.x-3.x detection |
| Scanner                | ✅     | 25+ lit\_\* fields, `_parse_lit()`, JS/TS file routing                                                                 |
| Compressor             | ✅     | 5 sections: LIT_COMPONENTS, LIT_PROPERTIES, LIT_EVENTS, LIT_TEMPLATES, LIT_API                                         |
| Testing                | ✅     | 109 tests, 3-repo validation (lit/lit, pwa-starter, synthetic lit_demo)                                                |
| BPL Integration        | ✅     | 50 practices (LIT001-LIT050) in lit_core.yaml, 10 PracticeCategory values                                              |
| Cross-Cutting          | ✅     | Framework-level parser runs on JS/TS files alongside other framework parsers                                           |
| Semantic Extraction    | ✅     | Components, properties, events, templates, CSS, controllers, mixins, lifecycle, Shadow DOM                             |
| Architecture Detection | ✅     | Version detection (Polymer 1-3, lit-element 2, lit 2-3), ecosystem detection (Vaadin/Shoelace/Spectrum/FAST)           |
| File Filtering (v4.7)  | ✅     | Runs on `.js/.jsx/.ts/.tsx` files, skips node_modules                                                                  |

#### Three.js / React Three Fiber (v4.71 — Session 60)

| Phase                  | Status      | Notes                                                                                                                 |
| ---------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------- |
| Extractors             | ✅          | 5 extractors: scene, component, material, animation, api (25 dataclasses)                                             |
| Parser                 | ✅          | EnhancedThreeJSParser with 20+ framework + feature patterns, r60-r170 + v1-v8 R3F version detection                   |
| Scanner                | ✅          | ~33 threejs\_\* fields, `_parse_threejs()`, JS/TS file routing                                                        |
| Compressor             | ✅          | 5 sections: THREEJS_SCENE, THREEJS_COMPONENTS, THREEJS_MATERIALS, THREEJS_ANIMATIONS, THREEJS_API                     |
| Testing                | ✅          | 63 tests, 3-repo validation (react-three-fiber, drei, r3f-wawatmos-starter), 5238 total passing                       |
| BPL Integration        | ✅          | 50 practices (THREEJS001-THREEJS050) in threejs_core.yaml, 10 PracticeCategory values                                 |
| Cross-Cutting          | ✅          | Framework-level parser runs on JS/TS files alongside other framework parsers                                          |
| Semantic Extraction    | ✅          | Canvas, cameras, renderers, controls, lights, meshes, materials, shaders, uniforms, animations, useFrame, drei (100+) |
| Architecture Detection | ✅          | R3F vs vanilla detection, Three.js r60-r170, R3F v1-v8, drei/rapier/cannon/postprocessing ecosystem                   |
| File Filtering (v4.7)  | ✅          | Runs on `.js/.jsx/.ts/.tsx` files, skips node_modules                                                                 |
| ----------             | ----------- | ------------------------------------------------                                                                      |
| Python                 | `PY`, `PYE` | `FAST`, `FLASK`, `DJANGO`                                                                                             |
| TypeScript             | `TS`        | `NG`, `NEST`, `REACT`                                                                                                 |
| JavaScript             | `JS`        | `EXPRESS`, `REACT`, `VUE`, `MONGOOSE`, `FASTIFY`                                                                      |
| Go                     | `GO`        | `GIN`, `ECHO`                                                                                                         |
| Java                   | `JAVA`      | `SPRING`, `QUARKUS`, `MICRONAUT`                                                                                      |
| Kotlin                 | `KT`        | `KTOR`, `KOIN`                                                                                                        |
| Rust                   | `RS`        | `ACTIX`, `ROCKET`                                                                                                     |
| R                      | `R`         | `SHINY`, `PLUMBER`, `GOLEM`, `TIDY`                                                                                   |
| PowerShell             | `PS`        | `PODE`, `DSC`, `PESTER`, `AZURE`                                                                                      |
| MUI                    | `MUI`       | `MUI` (Material UI)                                                                                                   |
| Ant Design             | `ANTD`      | `ANTD` (Ant Design)                                                                                                   |
| Chakra UI              | `CHAKRA`    | `CHAKRA` (Chakra UI)                                                                                                  |
| shadcn/ui              | `SHADCN`    | `SHADCN` (shadcn/ui)                                                                                                  |
| Bootstrap              | `BOOT`      | `BOOT` (Bootstrap)                                                                                                    |
| Redux                  | `REDUX`     | `REDUX` (Redux/RTK)                                                                                                   |
| Zustand                | `ZUSTAND`   | `ZUSTAND` (Zustand)                                                                                                   |
| Jotai                  | `JOTAI`     | `JOTAI` (Jotai)                                                                                                       |
| Recoil                 | `RECOIL`    | `RECOIL` (Recoil)                                                                                                     |
| MobX                   | `MOBX`      | `MOBX` (MobX)                                                                                                         |
| Pinia                  | `PINIA`     | `PINIA` (Pinia)                                                                                                       |
| Lit / Web Components   | `LIT`       | `LIT` (Lit / Polymer / Web Components)                                                                                |
| Three.js / R3F         | `THREEJS`   | `THREEJS` (Three.js / React Three Fiber / drei)                                                                       |
| Generic                | `DP`        | Design Patterns                                                                                                       |
| SOLID                  | `SOLID`     | N/A (cross-language)                                                                                                  |

---

## Quick Reference: Existing Practice Counts (Audited 12 Feb 2026)

| File                        |   Count | Notes                                                                    |
| --------------------------- | ------: | ------------------------------------------------------------------------ |
| `python_core.yaml`          |      17 | Core Python practices                                                    |
| `python_core_expanded.yaml` |      60 | Expanded Python coverage                                                 |
| `python_3_10.yaml`          |      12 | match, ParamSpec, etc.                                                   |
| `python_3_11.yaml`          |      12 | ExceptionGroup, tomllib                                                  |
| `python_3_12.yaml`          |      12 | f-string debug, type params                                              |
| `typescript_core.yaml`      |      45 | TS 5.0+ features                                                         |
| `angular.yaml`              |      45 | Signals, Standalone                                                      |
| `fastapi.yaml`              |      10 | Endpoints, Depends                                                       |
| `solid_patterns.yaml`       |       9 | SRP, OCP, LSP, ISP, DIP                                                  |
| `design_patterns.yaml`      |      30 | GoF + Enterprise                                                         |
| `react.yaml`                |      40 | Hooks, State, Components                                                 |
| `nestjs.yaml`               |      30 | Controllers, Services                                                    |
| `django.yaml`               |      30 | Views, Models, ORM                                                       |
| `flask.yaml`                |      20 | Routes, Blueprints                                                       |
| `database.yaml`             |      20 | SQL, ORM, Indexing                                                       |
| `devops.yaml`               |      15 | CI/CD, Docker, IaC                                                       |
| `go_core.yaml`              |      40 | Go idioms, concurrency                                                   |
| `java_core.yaml`            |      50 | Spring, JPA, Quarkus, Micronaut **(NEW v4.12)**                          |
| `r_core.yaml`               |      50 | R style, tidyverse, Shiny, Plumber, data engineering **(NEW v4.26)**     |
| `powershell_core.yaml`      |      50 | Cmdlets, DSC, Pester, modules, pipelines, remoting **(NEW v4.29)**       |
| `javascript_core.yaml`      |      50 | ES6+, async/await, Express, Node.js, security, testing **(NEW v4.30)**   |
| `mui_core.yaml`             |      50 | MUI components, themes, hooks, styles, API patterns **(NEW v4.36)**      |
| `antd_core.yaml`            |      50 | Antd components, theme, hooks, styles, API patterns **(NEW v4.37)**      |
| `chakra_core.yaml`          |      50 | Chakra components, theme, hooks, styles, API patterns **(NEW v4.38)**    |
| `shadcn_core.yaml`          |      50 | shadcn/ui components, theme, hooks, styles, API patterns **(NEW v4.39)** |
| `bootstrap_core.yaml`       |      50 | Bootstrap components, grid, theme, utilities, plugins **(NEW v4.40)**    |
| `lit_core.yaml`             |      50 | Lit/Web Components, properties, templates, events, SSR **(NEW v4.65)**   |
| **Total**                   | **947** |                                                                          |

---

_Checklist Version: 2.0_
_Updated: Session 28 - Phase AI: Bootstrap Framework Support (v4.40) — 5 Bootstrap extractors, EnhancedBootstrapParser, 50 BPL practices (BOOT001-BOOT050), 64 new tests, 0 bugs, 2-repo validation (sb-admin-2, react-bootstrap), 2234 total tests passing_
_Updated: Session 27 - Phase AH: shadcn/ui Framework Support (v4.39) — 5 shadcn extractors, EnhancedShadcnParser, 50 BPL practices (SHADCN001-SHADCN050), 63 new tests, 7 bugs fixed (#97-103), 2-repo validation (taxonomy, ui), 2170 total tests passing_
_Updated: 2026-02-15 - Phase AG: Chakra UI Framework Support (v4.38) — 5 Chakra extractors, EnhancedChakraParser, 50 BPL practices (CHAKRA001-CHAKRA050), 53 new tests, 5 bugs fixed (#92-96), 3-repo validation, 2107 total tests passing_
_Updated: 2026-02-15 - Phase AF: Ant Design Framework Support (v4.37) — 5 Antd extractors, EnhancedAntdParser, 50 BPL practices (ANTD001-ANTD050), 52 new tests, 2 bugs fixed (#91-92), 2-repo validation (ant-design-pro, antd-admin), 2054 total tests passing_
_Updated: 2026-02-15 - Phase AE: Material UI Framework Support (v4.36) — 5 MUI extractors, EnhancedMuiParser, 50 BPL practices (MUI001-MUI050), 43 new tests, 7 bugs fixed (#84-90), 3-repo validation (devias-kit, minimal-ui-kit, react-material-admin), 2002 total tests passing_
_Updated: 2026-02-14 - Phase AA: JavaScript Language Support (v4.30) — 5 JS extractors, EnhancedJavaScriptParser, 50 BPL practices (JS001-JS050), 88 new tests, 6 bugs fixed (#68-73), 3 BPL selector fixes, 3-repo validation (Express.js, Ghost, Nodemailer), 1551 total tests passing_
_Updated: 2026-02-14 - Phase Z: PowerShell Language Support (v4.29) — 5 PS extractors, EnhancedPowerShellParser, 50 BPL practices (PS001-PS050), 57 new tests, 5 bugs fixed, 3 gaps fixed, 3-repo validation (Pode, SqlServerDsc, Pester), 1463 total tests passing_
_Updated: 2026-02-14 - Phase Y: Lua Language Support (v4.28) — 5 Lua extractors, EnhancedLuaParser, 50 BPL practices (LUA001-LUA050), 52 new tests, 1 bug fixed, 3-repo validation, 1406 total tests passing_
_Updated: 2026-02-09 - Phase D: Public Repository Validation Framework (.codetrellis validate-repos` CLI, quality_scorer.py, analyze_results.py, 60-repo validation corpus)_
_Updated: 2026-02-07 - Phase A Remediation: RunbookExtractor, AI_ML/DEVTOOLS domains, [AI_INSTRUCTION] prompt header, 6 testing bugs fixed_
_BPL v1.4: tiktoken integration, OutputFormat, 447 practices (407+40 Go), min_python/contexts formalized, `python -m.codetrellis` support_

### Phase 10: A5.x Module Integration (Added Session 54b) ✅

> **Purpose**: Ensure the new language/framework is fully supported by the 4 A5.x post-processing modules: cache optimizer, MCP server, JIT context provider, and skills generator. These modules enhance AI prompt delivery by optimizing section ordering, aggregating resources, providing file-aware context, and generating AI skills.

#### 10.1 Cache Optimizer — `cache_optimizer.py`

File: `codetrellis/cache_optimizer.py` → `SECTION_STABILITY` dict

The cache optimizer reorders compressed sections by stability tier for maximum LLM KV-cache reuse. Every compressor section name must have a stability mapping.

- [ ] Add all `[<LANG>_*]` section names to `SECTION_STABILITY`:
  ```python
  # Stability tiers: STATIC (rarely changes), STRUCTURAL (infrequent),
  #                  SEMANTIC (moderate), VOLATILE (frequent changes)
  "<LANG>_TYPES": (SectionStability.STRUCTURAL, 1100),
  "<LANG>_FUNCTIONS": (SectionStability.SEMANTIC, 1400),
  "<LANG>_API": (SectionStability.SEMANTIC, 1500),
  "<LANG>_MODELS": (SectionStability.STRUCTURAL, 1200),
  "<LANG>_DEPENDENCIES": (SectionStability.STATIC, 600),
  ```
- [ ] Verify: `codetrellis scan . --cache-optimize` includes all new sections in output
- [ ] Verify: `codetrellis cache-optimize --stats` lists all new sections with correct stability

> **Stability tier guidelines:**
>
> - `STATIC` (order 100-800): Dependencies, configs, project metadata — rarely change
> - `STRUCTURAL` (order 900-1300): Types, models, schemas — change infrequently
> - `SEMANTIC` (order 1400-1800): Functions, APIs, hooks — moderate change rate
> - `VOLATILE` (order 1900-2200): Implementation logic, progress, actionable items — change often
>
> **Default:** Unknown sections get `(SectionStability.SEMANTIC, 1400)`

#### 10.2 MCP Server — `mcp_server.py`

File: `codetrellis/mcp_server.py` → `AGGREGATE_RESOURCES` dict

The MCP server exposes aggregate resources that combine related sections. New language sections should be added to appropriate aggregate categories.

- [ ] Add `<LANG>_TYPES` to `"types"` aggregate
- [ ] Add `<LANG>_API` to `"api"` aggregate
- [ ] Add `<LANG>_MODELS` to `"state"` aggregate (if ORM/data models)
- [ ] Add `<LANG>_COMPONENTS` to `"components"` aggregate (if UI framework)
- [ ] Add `<LANG>_STYLES` to `"styling"` aggregate (if CSS/styling framework)
- [ ] Add `<LANG>_ROUTING` to `"routing"` aggregate (if routing framework)

> **Current aggregate categories (8):**
> `types` — All type/class/interface sections across languages
> `api` — All API/endpoint/route sections (52 sections)
> `overview` — PROJECT, OVERVIEW, BUSINESS_DOMAIN, RUNBOOK
> `state` — All state management sections (27 sections)
> `infrastructure` — DEPENDENCIES, DOCKER, TERRAFORM, CI_CD
> `components` — All UI component sections (19 sections)
> `styling` — All CSS/styling sections (31 sections)
> `routing` — All routing/navigation sections (12 sections)

#### 10.3 JIT Context Provider — `jit_context.py`

File: `codetrellis/jit_context.py` → `EXTENSION_TO_SECTIONS` and `PATH_PATTERN_SECTIONS`

The JIT context provider selects relevant sections based on the file being edited.

- [ ] Add file extension mapping to `EXTENSION_TO_SECTIONS`:
  ```python
  ".<ext>": ["<LANG>_TYPES", "<LANG>_FUNCTIONS", "<LANG>_API"],
  ```
- [ ] Add path pattern if the framework uses convention-based paths:
  ```python
  # Example: files in /components/ get component sections
  r"components?/": ["<LANG>_COMPONENTS", "REACT_COMPONENTS"],
  # Example: files in /store/ get state sections
  r"stores?/": ["<LANG>_STORES", "REDUX_STORE"],
  ```
- [ ] For framework-specific `.tsx`/`.jsx` files, add to the framework-aware section lists
- [ ] Verify: `codetrellis context path/to/file.<ext> --sections-only` shows correct sections

> **UNIVERSAL_SECTIONS** (`PROJECT`, `BEST_PRACTICES`, `RUNBOOK`) are always included for every file.
>
> **Naming rule:** Section names must match exactly what the compressor emits (e.g., `VUE_COMPOSABLES` not `VUE_REACTIVITY`).

#### 10.4 Skills Generator — `skills_generator.py`

File: `codetrellis/skills_generator.py` → `SKILL_TEMPLATES`

The skills generator creates AI-executable skill definitions. Framework-specific sections should be added to appropriate skill templates' `detect_sections` lists.

- [ ] Add `<LANG>_COMPONENTS` to `add-component` template's `detect_sections`
- [ ] Add `<LANG>_STORES` to `add-store` template's `detect_sections`
- [ ] Add `<LANG>_API` to `add-endpoint` template's `detect_sections`
- [ ] Add `<LANG>_MODELS` to `add-model` template's `detect_sections`
- [ ] Add `<LANG>_HOOKS` to `add-hook` template's `detect_sections` (if applicable)
- [ ] Add `<LANG>_STYLES` to `add-style` template's `detect_sections` (if CSS framework)
- [ ] Add `<LANG>_ROUTING` to `add-route` template's `detect_sections` (if routing)
- [ ] Add `<LANG>_QUERIES` to `add-data-fetch` template's `detect_sections` (if data fetching)
- [ ] Verify: `codetrellis skills` includes the new framework in generated skills

> **Current skill templates (17):**
> `add-component`, `add-store`, `add-endpoint`, `add-model`, `add-hook`,
> `add-test`, `add-migration`, `add-config`, `add-type`, `add-middleware`,
> `add-plugin`, `add-page`, `add-guard`, `add-interceptor`,
> `add-style` _(NEW)_, `add-route` _(NEW)_, `add-data-fetch` _(NEW)_

#### 10.5 A5.x Unit Tests

- [ ] Add test in `test_cache_optimizer.py` → `TestFrameworkStabilityCoverage`:
  ```python
  def test_<lang>_sections_have_stability(self):
      """All <LANG>_* sections should have stability mappings."""
      sections = ["<LANG>_TYPES", "<LANG>_FUNCTIONS", "<LANG>_API"]
      for section in sections:
          assert section in CacheOptimizer.SECTION_STABILITY
  ```
- [ ] Add test in `test_mcp_server.py` → `TestAggregateResourcesCoverage`:
  ```python
  def test_<lang>_sections_in_aggregates(self):
      """<LANG> sections should appear in MCP aggregates."""
      assert "<LANG>_TYPES" in server.AGGREGATE_RESOURCES["types"]
  ```
- [ ] Add test in `test_jit_context.py` → `TestFrameworkExtensionCoverage`:
  ```python
  def test_<ext>_extension_mapped(self):
      """.<ext> extension should map to <LANG> sections."""
      assert ".<ext>" in JITContextProvider.EXTENSION_TO_SECTIONS
  ```
- [ ] Add test in `test_skills_generator.py` → `TestFrameworkCoverage`:
  ```python
  def test_<lang>_in_skill_templates(self):
      """<LANG> sections should appear in relevant skill templates."""
      # Check add-component, add-store, etc.
  ```
- [ ] Run: `python -m pytest tests/unit/test_cache_optimizer.py tests/unit/test_mcp_server.py tests/unit/test_jit_context.py tests/unit/test_skills_generator.py -v`

#### 10.6 A5.x CLI Verification

- [ ] `codetrellis scan . --cache-optimize` — verify new sections appear in cache-optimized output
- [ ] `codetrellis cache-optimize --stats` — verify new sections listed with stability tiers
- [ ] `codetrellis context path/to/file.<ext> --sections-only` — verify correct JIT sections
- [ ] `codetrellis skills` — verify skills count reflects new framework detection

> **Reference:** Session 54b expanded all 4 A5.x modules to support 53+ languages/frameworks with ~350 unique section names.
> **Key files:** `cache_optimizer.py`, `mcp_server.py`, `jit_context.py`, `skills_generator.py`
> **Test files:** `tests/unit/test_cache_optimizer.py` (56 tests), `tests/unit/test_mcp_server.py` (48 tests), `tests/unit/test_jit_context.py` (46 tests), `tests/unit/test_skills_generator.py` (51 tests)
> **Total A5.x tests:** 201, all passing ✅

---

### Phase 11: Pipeline Quality Assurance (v4.8)

> **Purpose**: Verify the extraction → compression pipeline preserves data correctly for the new language.

- [ ] **Brace-balanced extraction**: If the language uses `{}` blocks (Go, Rust, Java, C#, etc.), verify type extractor uses `_extract_brace_body()` instead of `[^}]*` regex
- [ ] **Compressor adaptive limits**: Verify `_compress_{lang}_functions()` uses importance-sorted, adaptive limits (not hard-coded caps)
- [ ] **Prefix grouping**: For interfaces/types with >20 methods, verify compressor groups by method prefix
- [ ] **BPL ratio limiting**: Verify language-specific practices dominate over generic (DP/SOLID) in output
- [ ] **Primary language priority**: Verify IMPLEMENTATION_LOGIC shows primary language files first
- [ ] **Directory summary**: Verify PROJECT_STRUCTURE section shows populated directory tree with file counts, languages, and purposes
- [ ] **Quantitative scorecard**: Run against a representative repo and verify:
  - Types: >90% of source structs/classes extracted
  - Methods: All exported methods visible in compressed output
  - Routes: >95% of API endpoints captured
  - Dependencies: 100% of direct deps listed
  - Best practices: >70% are primary language practices

---

### Phase 12: .gitignore-Aware Scanning (v4.10) ✅

> **Purpose**: Ensure new extractors respect `.gitignore` and `.git/info/exclude` rules, preventing scans from walking into gitignored directories (e.g., cloned evaluation repos, large vendored deps).

- [x] **Accept `gitignore_filter` parameter**: If your extractor does its own `os.walk()`, add `gitignore_filter: Optional[GitignoreFilter] = None` to `extract_from_directory()`
- [x] **Import GitignoreFilter**: `from codetrellis.file_classifier import GitignoreFilter`
- [x] **Apply in directory walk**: Filter dirs in `os.walk()` to skip gitignored paths:
  ```python
  gi = gitignore_filter
  for root, dirs, files in os.walk(directory):
      if gi:
          rel = os.path.relpath(root, directory)
          dirs[:] = [d for d in dirs
                     if d not in IGNORE_DIRS
                     and not gi.should_ignore(os.path.join(rel, d) if rel != '.' else d, is_dir=True)]
  ```
- [x] **Scanner passes filter**: `scanner.py` loads `GitignoreFilter.from_root(root)` at scan start and passes to all v5 extractors
- [x] **Supports both sources**: GitignoreFilter loads `.gitignore` AND `.git/info/exclude`
- [x] **Zero external dependencies**: Uses `fnmatch` from stdlib, no `pathspec` or `gitpython`

**Updated extractors (R4):**
| Extractor | File | Status |
|-----------|------|--------|
| SecurityExtractor | `security_extractor.py` | ✅ |
| DatabaseArchitectureExtractor | `database_architecture_extractor.py` | ✅ |
| EnvInferenceExtractor | `env_inference_extractor.py` | ✅ |
| ConfigTemplateExtractor | `config_template_extractor.py` | ✅ |
| GenericLanguageExtractor | `generic_language_extractor.py` | ✅ |
| GraphQLSchemaExtractor | `graphql_schema_extractor.py` | ✅ |
| DiscoveryExtractor | `discovery_extractor.py` (4 methods) | ✅ |

**Key file:** `codetrellis/file_classifier.py` — `GitignoreFilter` class + `_GitignoreRule` class

---

### Phase 13: Systemic Improvements — Detection Architecture (v4.11) ✅

> **Purpose**: When adding a new language, ensure it benefits from the systemic detection improvements: weighted domain scoring, multi-signal ORM/DB/MQ detection, discovery-driven stack detection, and ORM-DB affinity graph with sub-project provenance.

#### 13.1 Weighted Domain Scoring Integration

- [x] **DOMAIN_INDICATORS structure**: All domains use `{high: [], medium: [], low: []}` tier structure
- [x] **Tier weights**: high=3, medium=2, low=1
- [x] **Source weights**: pkg_json=4, code=3, fs=2, readme=1
- [x] **Confidence scoring**: Normalized against `max_possible` per domain
- [x] **Runner-up reporting**: `BusinessDomainContext.domain_runner_up` + `domain_runner_up_confidence`
- [ ] **For new domains**: Add indicators in tiered format — high-confidence keywords in `high`, ambiguous in `low`

#### 13.2 Multi-Signal Detection

- [x] **ORM_DETECTION**: 19 ORMs with `{strong, medium, weak, anti}` signal tiers
- [x] **DB_DETECTION**: 13 DB types with `{strong, medium, anti}` signal tiers
- [x] **MQ_DETECTION**: 10 MQ types with `{strong, medium, anti}` signal tiers
- [x] **Helper functions**: `detect_orms_multi_signal()`, `detect_dbs_multi_signal()`, `detect_mqs_multi_signal()`
- [ ] **For new ORMs/DBs**: Add to appropriate `*_DETECTION` dict with tiered signal patterns:
  ```python
  ORM_DETECTION['new_orm'] = {
      'strong': [r'unambiguous_import_pattern'],  # 1 strong = detected
      'medium': [r'likely_pattern'],               # 2 medium = detected
      'weak':   [r'generic_term'],                 # ignored alone
      'anti':   [r'\.py$'],                        # file types where impossible
  }
  ```

#### 13.3 Discovery-Driven Stack Detection

- [x] **Per-sub-project manifest reading**: `build_project_profile()` in `architecture_extractor.py`
- [x] **Framework detection from manifests**: package.json deps, requirements.txt, go.mod
- [x] **Sub-projects enriched with `detected_frameworks`**
- [ ] **For new manifests**: Add manifest parsing in `build_project_profile()` (e.g., `Cargo.toml`, `pom.xml`)

#### 13.4 ORM-DB Affinity Graph

- [x] **ORMEvidence dataclass**: orm, db_type, file_path, sub_project, confidence, all_files
- [x] **DatabaseInfo.sub_project field**: Tracks which sub-project owns each DB
- [x] **Evidence consolidation**: By (orm_name, sub_project) pairs
- [x] **DB affinity resolution**: explicit assoc_db → co-located DB → any relational DB
- [ ] **For new ORMs**: Add associated DB type in `ORM_DETECTION` entry's `assoc_db` field

#### 13.5 Unified FileClassifier Integration

- [x] **FileClassifier wired into**: scanner.py, database_architecture_extractor.py, discovery_extractor.py, security_extractor.py
- [x] **`_EXAMPLE_DIRS` aliased**: All modules reference `FileClassifier.EXAMPLE_DIRS`
- [x] **`should_skip_for_detection()`**: Used in `_parse_file()` and `_extract_dependencies()`
- [ ] **For new extractors**: Import `FileClassifier` and use `is_app_code()` or `should_skip_for_detection()`

**Key files modified (Phase K):**
| File | Changes |
|------|---------|
| `business_domain_extractor.py` | Weighted DOMAIN_INDICATORS, confidence scoring, runner-up |
| `database_architecture_extractor.py` | ORM_DETECTION/DB_DETECTION/MQ_DETECTION dicts, ORMEvidence, affinity graph |
| `architecture_extractor.py` | Discovery-driven per-sub-project stack detection |
| `scanner.py` | FileClassifier wiring, pass discovery_result to DB extractor |
| `discovery_extractor.py` | FileClassifier.EXAMPLE_DIRS alias |
| `security_extractor.py` | FileClassifier.EXAMPLE_DIRS alias + should_skip_for_detection |

---

### Phase 14: C# Language Support (v4.13) ✅

> **Purpose**: Full C# support with regex-based extraction (optional tree-sitter-c-sharp AST), covering all C# versions through C# 12+, ASP.NET Core, Entity Framework Core, Blazor, gRPC, SignalR, and MAUI.

#### 14.1 Extractors Created

- [x] `extractors/csharp/__init__.py` — Module exports for all 6 extractors + 22 dataclasses
- [x] `extractors/csharp/type_extractor.py` — Classes (abstract/sealed/static/partial), interfaces, structs (readonly/ref), records (class/struct), delegates
- [x] `extractors/csharp/function_extractor.py` — Methods (async/static/virtual/override/extension), constructors (base/this chaining), events
- [x] `extractors/csharp/enum_extractor.py` — Enums with members, values, and flags detection
- [x] `extractors/csharp/api_extractor.py` — ASP.NET Core controllers, Minimal API (MapGet/MapPost), gRPC services, SignalR hubs, Razor Pages
- [x] `extractors/csharp/model_extractor.py` — EF Core DbContext, entities (annotations + keyless), DTOs/ViewModels/Commands/Queries, repositories
- [x] `extractors/csharp/attribute_extractor.py` — Attribute detection, categorization, custom attribute definitions

#### 14.2 Parser Created

- [x] `csharp_parser_enhanced.py` — `EnhancedCSharpParser` integrating all 6 extractors
- [x] `CSharpParseResult` dataclass with all extracted fields
- [x] `FRAMEWORK_PATTERNS` for 15 .NET ecosystem frameworks
- [x] `VERSION_FEATURES` for C# 7.0-12.0 feature detection
- [x] `parse_csproj()` static method for NuGet package references, SDK type, target framework
- [x] `parse_sln()` static method for solution project listing
- [x] Optional tree-sitter-c-sharp AST (graceful fallback to regex)

#### 14.3 Scanner Integration

- [x] 21 C# fields in `ProjectMatrix` (classes, interfaces, structs, records, delegates, enums, methods, constructors, events, endpoints, grpc_services, signalr_hubs, entities, db_contexts, dtos, repositories, attributes, namespaces, dependencies, detected_frameworks, version_features)
- [x] `FILE_TYPES` mapping: `.cs` → `"csharp"`, `.csx` → `"csharp"`
- [x] `DEFAULT_IGNORE` additions: `bin`, `obj`, `.vs`, `packages`
- [x] `_parse_csharp()` method with full field mapping
- [x] Stats and data sections in `to_dict()`
- [x] Debug logging (replaced `except Exception: pass`)

#### 14.4 Compressor Integration

- [x] `[CSHARP_TYPES]` — Classes, interfaces, structs, records, delegates, enums
- [x] `[CSHARP_API]` — Endpoints, gRPC services, SignalR hubs
- [x] `[CSHARP_FUNCTIONS]` — Methods grouped by file, constructors, events
- [x] `[CSHARP_MODELS]` — DbContexts, entities, DTOs, repositories
- [x] `[CSHARP_DEPENDENCIES]` — Detected frameworks, namespaces, NuGet dependencies

#### 14.5 BPL Integration

- [x] C# artifact counting in `from_matrix()` (`csharp_count` variable)
- [x] Framework detection: `aspnet_core` → `aspnet`, `ef_core` → `efcore`, `blazor`, `signalr`, `maui`
- [x] Prefix mapping: `CS`, `ASPNET`, `EF`, `BLAZOR`
- [x] `has_csharp` detection and C# practice filtering in `_filter_applicable()`
- [x] `bpl/practices/csharp_core.yaml` — 50 practices (CS001-CS050)

#### 14.6 Cross-cutting Updates

- [x] `interfaces.py` — `FileType.CSHARP` enum member
- [x] `architecture_extractor.py` — 6 C# ProjectType enums, `.sln`/`.csproj` detection
- [x] `generic_language_extractor.py` — `.cs`, `.csx` added to exclusion set

#### 14.7 Unit Tests

- [x] `test_csharp_type_extractor.py` (22 tests) — Classes, interfaces, structs, records, delegates
- [x] `test_csharp_function_extractor.py` (11 tests) — Methods, constructors, events
- [x] `test_csharp_api_extractor.py` (13 tests) — Controllers, Minimal API, gRPC, SignalR, Razor
- [x] `test_csharp_model_extractor.py` (11 tests) — DbContext, entities, DTOs, repositories
- [x] `test_csharp_parser_enhanced.py` (18 tests) — Parsing, framework detection, csproj/sln
- [x] `test_csharp_scanner_compressor.py` (22 tests) — Scanner dispatch, compressor, matrix output
- [x] **All 269 tests passing** (97 new + 172 existing)

#### 14.8 Bugs Fixed (10 total)

| #   | Bug                                    | Fix                                         |
| --- | -------------------------------------- | ------------------------------------------- |
| 1   | `class_names=class_names` kwarg crash  | Removed — auto-detects internally           |
| 2   | `cls.extends` field doesn't exist      | Changed to `cls.base_class`                 |
| 3   | `p.accessors` field doesn't exist      | Changed to `has_getter/has_setter/has_init` |
| 4   | Delegate parameters double-wrapped     | Use `dlg.parameters` directly               |
| 5   | `evt.event_type` field doesn't exist   | Changed to `evt.type`                       |
| 6   | `self.max_props/max_methods` undefined | Replaced with inline `8`                    |
| 7   | Minimal API regex too restrictive      | Broadened to `\w+`                          |
| 8   | Lambda handlers not matched            | Extended regex for lambdas                  |
| 9   | Modifiers leaked into return_type      | Post-processing extraction                  |
| 10  | Indented namespace/using not matched   | `^\s*` prefix on patterns                   |

#### 14.9 Validation (3 repos)

| Repo                             | C# Files | Classes | Endpoints | DbContexts | Frameworks |
| -------------------------------- | -------- | ------- | --------- | ---------- | ---------- |
| dotnet/eShop                     | 100+     | 100+    | 27        | 3          | 15         |
| ardalis/CleanArchitecture        | 357      | ✅      | ✅        | ✅         | ✅         |
| jasontaylordev/CleanArchitecture | 115      | ✅      | ✅        | ✅         | ✅         |

---

### Phase 15: Rust Language Support (v4.14) ✅

> **Purpose**: Full Rust support with regex-based extraction (optional tree-sitter-rust AST), covering all Rust editions (2015/2018/2021), Actix-web, Rocket, Axum, Warp, Tide, Diesel, SeaORM, SQLx, Tonic gRPC, async-graphql, and Tokio async runtime.

#### 15.1 Extractors Created

- [x] `extractors/rust/__init__.py` — Module exports for all 5 extractors + dataclasses
- [x] `extractors/rust/type_extractor.py` — Structs (named/tuple/unit), enums (unit/tuple/struct variants), traits (with default impls, supertraits), impl blocks, type aliases
- [x] `extractors/rust/function_extractor.py` — Functions (pub/const/async/unsafe/extern), methods (self/&self/&mut self), closures, `#[test]` detection
- [x] `extractors/rust/api_extractor.py` — Actix-web, Rocket, Axum, Warp, Tide routes, Tonic gRPC services, async-graphql types
- [x] `extractors/rust/model_extractor.py` — Diesel models/schemas, SeaORM entities, SQLx queries
- [x] `extractors/rust/attribute_extractor.py` — Derive macros, proc macros, cfg attributes, feature flags, crate-level attributes

#### 15.2 Parser Created

- [x] `rust_parser_enhanced.py` — `EnhancedRustParser` integrating all 5 extractors
- [x] `RustParseResult` dataclass with all extracted fields
- [x] `FRAMEWORK_PATTERNS` for 15+ Rust ecosystem frameworks
- [x] `parse()` method with import/extern crate extraction
- [x] `_detect_frameworks()` for runtime framework detection
- [x] `_extract_macro_definitions()` for macro_rules! parsing
- [x] `parse_cargo_toml()` static method for dependency extraction (deps, dev-deps, build-deps, workspace)

#### 15.3 Scanner Integration

- [x] 16+ Rust fields in `ProjectMatrix` (structs, enums, traits, type_aliases, impl_blocks, functions, methods, routes, grpc_services, graphql_types, models, schemas, derive_macros, feature_flags, dependencies, detected_frameworks)
- [x] `FILE_TYPES` mapping: `.rs` → `"rust"`
- [x] `DEFAULT_IGNORE` additions: `target` (Rust build output)
- [x] `_parse_rust()` method with full field mapping
- [x] Cargo.toml parsing in `_extract_dependencies()`
- [x] Stats and data sections in `to_dict()`
- [x] Debug logging (replaced `except Exception: pass`)
- [x] Fixed absolute path bug: test-skip uses `file_path.relative_to(matrix.root_path)`

#### 15.4 Compressor Integration

- [x] `[RUST_TYPES]` — Structs, enums, traits, type aliases, impl blocks
- [x] `[RUST_API]` — Routes (5 frameworks), gRPC services, GraphQL types
- [x] `[RUST_FUNCTIONS]` — Functions grouped by file with async/unsafe/const tags
- [x] `[RUST_MODELS]` — Diesel/SeaORM/SQLx models, schemas, migrations
- [x] `[RUST_DEPENDENCIES]` — Cargo.toml dependencies, frameworks, features

#### 15.5 BPL Integration

- [x] Rust artifact counting in `from_matrix()` (`rust_count` variable)
- [x] Framework detection: `actix_web` → `actix`, `rocket`, `axum`, `warp`, `tide`, `tokio`, `serde`, `diesel`
- [x] Prefix mapping: `RS`, `ACTIX`, `ROCKET`, `AXUM`, `WARP`, `TIDE`, `TOKIO`, `SERDE`, `DIESEL`
- [x] `has_rust` detection and Rust practice filtering in `_filter_applicable()`
- [x] `bpl/practices/rust_core.yaml` — 50 practices (RS001-RS050)
- [x] 4 new `PracticeCategory` enums: `MEMORY_SAFETY`, `OWNERSHIP`, `LIFETIME_MANAGEMENT`, `CARGO`

#### 15.6 Cross-cutting Updates

- [x] `interfaces.py` — `FileType.RUST` enum member
- [x] `generic_language_extractor.py` — `.rs` added to exclusion set

#### 15.7 Unit Tests

- [x] `test_rust_type_extractor.py` (16 tests) — Structs, enums, traits, impls, type aliases
- [x] `test_rust_function_extractor.py` (10 tests) — Functions, methods, async, unsafe, closures
- [x] `test_rust_api_extractor.py` (7 tests) — Actix-web, Rocket, Axum, gRPC, GraphQL
- [x] `test_rust_parser_enhanced.py` (13 tests) — Parsing, framework detection, Cargo.toml
- [x] **All 315 tests passing** (46 new + 269 existing)

#### 15.8 Bugs Fixed (6 total)

| #   | Bug                                 | Fix                                                           |
| --- | ----------------------------------- | ------------------------------------------------------------- |
| 13  | Scanner field name mismatches (10+) | Fixed all: `generics`, `is_tuple_struct`, `target_type`, etc. |
| 14  | Test-skip absolute path bug         | Changed to `file_path.relative_to(root_path)`                 |
| 15  | `#[test]` attribute not detected    | Added attrs group parsing from regex match                    |
| 16  | API framework detection `'unknown'` | Check file content for framework imports                      |
| 17  | GraphQL key mismatch                | `api_result.get('graphql', [])` not `'graphql_types'`         |
| 18  | `method.self_param` → `self_kind`   | Changed to `method.self_kind`                                 |

#### 15.9 Validation (3 repos)

| Repo             | Rust Files | Structs | Enums | Traits | Routes | Models | Frameworks |
| ---------------- | ---------- | ------- | ----- | ------ | ------ | ------ | ---------- |
| tokio-rs/axum    | 169        | 380     | 53    | 28     | 257    | —      | 10         |
| diesel-rs/diesel | 400+       | 655     | 96    | 299    | —      | 98     | 8+         |
| actix/actix-web  | 200+       | 411     | 121   | 33     | 43     | —      | 8+         |

---

### Phase 16: R Language Support (v4.26) ✅

> **Purpose**: Full R language support with regex-based extraction (optional R-languageserver LSP), covering all R versions from 2.x through 4.4+, all 6 class systems (S3, S4, R5, R6, S7/R7, proto), 70+ framework patterns, tidyverse pipe chains, Shiny reactive components, Plumber API endpoints, and DESCRIPTION/NAMESPACE/renv.lock dependency extraction.

#### 16.1 Extractors Created

- [x] `extractors/r/__init__.py` — Module exports for all 5 extractors + ~25 dataclasses
- [x] `extractors/r/type_extractor.py` — R6 classes, R5 (ReferenceClass), S4 classes, S3 classes, S7/R7 classes, proto objects, environments, S4 generics, S7 generics
- [x] `extractors/r/function_extractor.py` — Functions (exported/internal), S3 methods, infix operators (%%, %+%, %>%, %<>%), lambdas (R 4.1+), pipe chains (|> and %>%)
- [x] `extractors/r/api_extractor.py` — Plumber routes (#\* @get/@post), Shiny server/UI/modules (renderPlot, observeEvent, moduleServer), RestRserve, Ambiorix
- [x] `extractors/r/model_extractor.py` — Data models (tibble/data.table/arrow), DBI connections (pool support), SQL queries, data pipelines
- [x] `extractors/r/attribute_extractor.py` — DESCRIPTION deps (Imports/Depends/Suggests/LinkingTo), NAMESPACE exports/imports, configs, lifecycle hooks

#### 16.2 Parser Created

- [x] `r_parser_enhanced.py` — `EnhancedRParser` integrating all 5 extractors
- [x] `RParseResult` dataclass with all extracted fields
- [x] 70+ `FRAMEWORK_PATTERNS` covering tidyverse, Shiny, Plumber, data.table, ML/stats, spatial, bioinformatics, etc.
- [x] `R_VERSION_FEATURES` for R 4.0-4.4+ feature detection (native pipe, lambda, S7)
- [x] `parse_description()` static method for DESCRIPTION file parsing (deps, version, license)
- [x] `parse_renv_lock()` static method for renv lockfile dependency extraction
- [x] `parse_namespace()` static method for NAMESPACE export/import extraction
- [x] `LIBRARY_PATTERN` with dotted package name support (`data.table`, `Rcpp`)
- [x] Optional R-languageserver LSP integration (graceful fallback to regex)

#### 16.3 Scanner Integration

- [x] ~25 R fields in `ProjectMatrix` (classes, s4_classes, r6_classes, functions, s3_methods, operators, lambdas, pipe_chains, generics, s4_methods, routes, shiny_components, models, connections, queries, pipelines, dependencies, exports, configs, hooks, package_metadata, detected_frameworks, version_features, fields, environments)
- [x] `FILE_TYPES` mapping: `.R/.r` → `"r"`, `.Rmd/.Rnw/.Rproj` → `"r"`, `DESCRIPTION/NAMESPACE/renv.lock` → `"r"` (name-based)
- [x] `_parse_r()` method with full field mapping (~250 lines)
- [x] DESCRIPTION/NAMESPACE/renv.lock parsing in file dispatch
- [x] Stats and data sections in `to_dict()`

#### 16.4 Compressor Integration

- [x] `[R_TYPES]` — R6, R5, S4, S3, S7 classes, generics, environments
- [x] `[R_FUNCTIONS]` — Functions grouped by file with exported/internal/S3 method/operator markers
- [x] `[R_API]` — Plumber routes, Shiny components (server/UI/modules), RestRserve/Ambiorix
- [x] `[R_MODELS]` — Data models, DBI connections, queries, pipelines
- [x] `[R_DEPENDENCIES]` — DESCRIPTION deps, NAMESPACE exports, detected frameworks, renv packages

#### 16.5 BPL Integration

- [x] R artifact counting in `from_matrix()` (`r_count` variable, ~25 attributes)
- [x] Framework detection mapping (70+ entries)
- [x] Prefix mapping: `R`, `SHINY`, `PLUMBER`, `GOLEM`, `TIDY`
- [x] `has_r` detection and R practice filtering in `_filter_applicable()`
- [x] `bpl/practices/r_core.yaml` — 50 practices (R001-R050) across 10 categories

#### 16.6 Unit Tests

- [x] `test_r_type_extractor.py` (14 tests) — R6, R5, S4, S3, S7, proto, environments, generics
- [x] `test_r_function_extractor.py` (12 tests) — Functions, S3 methods, operators, lambdas, pipe chains
- [x] `test_r_api_extractor.py` (10 tests) — Plumber, Shiny, RestRserve, Ambiorix
- [x] `test_r_parser_enhanced.py` (26 tests) — Parsing, framework detection, DESCRIPTION, NAMESPACE, renv.lock
- [x] **All 1228 tests passing** (62 new + 1166 existing)

#### 16.7 Bugs Fixed (11 total)

| #   | Bug                                          | Fix                                                                             |
| --- | -------------------------------------------- | ------------------------------------------------------------------------------- |
| 47  | Scanner field name mismatches (15+ fields)   | Fixed all: `parent_class`, `visibility`, `generic_name`, `start_function`, etc. |
| 48  | Operator pattern `%\w+%` didn't match `%+%`  | Changed to `%[^%\s]+%`                                                          |
| 49  | Lambda extraction not implemented            | Added `_extract_lambdas()` for R 4.1+ syntax                                    |
| 50  | Multi-line pipe chains not detected          | Rewrote `_extract_pipe_chains()` with line merging                              |
| 51  | `RPipeChainInfo.length` property missing     | Added `@property` method                                                        |
| 52  | LIBRARY_PATTERN didn't match `data.table`    | Changed `(\w+)` to `([\w.]+)`                                                   |
| 53  | Compressor complexity comparison with string | Added `int()` conversion with try/except                                        |
| 54  | Compressor `f.get('access')` mismatch        | Changed to `f.get('visibility')`                                                |
| 55  | SyntaxWarnings from `\(` in docstrings       | Escaped to `\\(` at 3 locations                                                 |
| 56  | S7 generic extraction missing                | Added `S7_NEW_GENERIC` pattern + `_extract_s7_generics()` + `kind` field        |
| 57  | SyntaxWarning in test file                   | Changed to raw string `r"..."`                                                  |

#### 16.8 Validation (3 repos)

| Repo            | Functions | Classes | Pipe Chains | Shiny Components | Deps | Exports | Frameworks               |
| --------------- | --------- | ------- | ----------- | ---------------- | ---- | ------- | ------------------------ |
| tidyverse/dplyr | 897       | 4       | 100         | —                | 29   | 338     | tidyverse, rlang, vctrs  |
| rstudio/shiny   | 1,117     | 35      | —           | 128              | —    | —       | shiny, htmltools, httpuv |
| rstudio/plumber | 361       | 12      | —           | —                | —    | —       | plumber, R7, future      |

---

### Phase 17: Dart Language Support (v4.27) ✅

> **Purpose**: Full Dart language support with regex-based extraction + optional tree-sitter-dart AST + optional dart analysis_server LSP, covering Dart 2.0 through 3.5+ (null safety 2.12+, class modifiers 3.0+, records 3.0+, extension types 3.3+, patterns 3.0+), Flutter 1.x through 3.x+ (4 widget types), 70+ framework patterns, pubspec.yaml/pubspec.lock parsing, null safety analysis, and Dart 3 feature detection.

#### 17.1 Extractors Created

- [x] `extractors/dart/__init__.py` — Module exports for all 5 extractors + ~20 dataclasses
- [x] `extractors/dart/type_extractor.py` — Classes (abstract/sealed/base/interface/final/mixin), mixins, enums (enhanced with members), extensions, extension types (3.3+), typedefs (function/non-function)
- [x] `extractors/dart/function_extractor.py` — Functions (async/async*/sync*), methods, constructors (const/factory/named/redirecting), getters, setters
- [x] `extractors/dart/api_extractor.py` — Flutter widgets (Stateless/Stateful/Inherited/RenderObject), routes (Shelf/DartFrog/Serverpod/Conduit/Angel), state managers (Riverpod/Bloc/GetX/Provider/MobX), gRPC
- [x] `extractors/dart/model_extractor.py` — ORM models (Drift/Floor/Isar/Hive/ObjectBox), data classes (Freezed/JsonSerializable/Built Value/Equatable), migrations
- [x] `extractors/dart/attribute_extractor.py` — Annotations, imports/exports, parts, isolates/compute, platform channels (MethodChannel/EventChannel), null safety analysis, Dart 3 feature detection

#### 17.2 Parser Created

- [x] `dart_parser_enhanced.py` — `EnhancedDartParser` integrating all 5 extractors
- [x] `DartParseResult` dataclass with all extracted fields
- [x] 70+ `FRAMEWORK_PATTERNS` covering Flutter, Riverpod, Bloc, GetX, Provider, MobX, Dio, Drift, Floor, Isar, Hive, ObjectBox, Freezed, JsonSerializable, GetIt, Injectable, GoRouter, AutoRoute, Shelf, Dart Frog, Serverpod, Conduit, Angel, Firebase, Supabase, gRPC, etc.
- [x] `parse()` method with full extraction pipeline
- [x] `parse_pubspec()` static method for pubspec.yaml dependency extraction (deps, dev_deps, flutter config)
- [x] Null safety detection from environment SDK constraints
- [x] Dart version detection from pubspec.yaml SDK constraints
- [x] Optional dart analysis_server LSP integration (graceful fallback to regex)

#### 17.3 Scanner Integration

- [x] ~30 Dart fields in `ProjectMatrix` (classes, mixins, enums, extensions, extension_types, typedefs, functions, constructors, getters, setters, widgets, routes, state_managers, grpc_services, models, data_classes, migrations, annotations, imports, isolates, platform_channels, null_safety, dart3_features, dependencies, dev_dependencies, detected_frameworks, dart_sdk_version, flutter_sdk_version)
- [x] `FILE_TYPES` mapping: `.dart` → `"dart"`, `pubspec.yaml`/`pubspec.lock` → `"dart"` (name-based)
- [x] `_parse_dart()` method with full field mapping (~350 lines)
- [x] pubspec.yaml parsing via `EnhancedDartParser.parse_pubspec()`
- [x] Stats and data sections in `to_dict()`
- [x] Removed `"packages"` from DEFAULT_IGNORE (was blocking Dart/Flutter monorepo `packages/` directories)

#### 17.4 Compressor Integration

- [x] `[DART_TYPES]` — Classes, mixins, enums, extensions, extension types, typedefs
- [x] `[DART_FUNCTIONS]` — Functions grouped by file with async/generator/constructor tags
- [x] `[DART_API]` — Widgets, routes, state managers, gRPC services
- [x] `[DART_MODELS]` — ORM models, data classes, migrations
- [x] `[DART_DEPENDENCIES]` — pubspec deps, frameworks, SDK versions, null safety, Dart 3 features

#### 17.5 BPL Integration

- [x] Dart artifact counting in `from_matrix()` (`dart_count` variable, ~19 attributes)
- [x] Framework detection mapping (35 entries): `flutter` → flutter, `riverpod` → riverpod, `bloc` → bloc, `getx` → getx, `provider` → provider, `mobx` → mobx, `dio` → dio, `drift` → drift, `isar` → isar, etc.
- [x] Prefix mapping: `DART`, `FLUTTER`
- [x] `has_dart` detection and Dart practice filtering in `_filter_applicable()`
- [x] `bpl/practices/dart_core.yaml` — 50 practices (DART001-DART050) across 10 categories
- [x] 27 new `PracticeCategory` enums: `DART_NULL_SAFETY`, `DART_TYPE_SYSTEM`, `DART_ASYNC`, `DART_PATTERNS`, `DART_EXTENSIONS`, `DART_GENERICS`, `DART_ISOLATES`, `DART_STREAMS`, `DART_ERROR_HANDLING`, `DART_COLLECTIONS`, `DART_TESTING`, `DART_CODE_GENERATION`, `DART_DOCUMENTATION`, `DART_PACKAGE_DESIGN`, `DART_PERFORMANCE`, `DART_SECURITY`, `DART_INTEROP`, `DART_WEB`, `DART_CLI`, `FLUTTER_WIDGETS`, `FLUTTER_STATE`, `FLUTTER_NAVIGATION`, `FLUTTER_ANIMATION`, `FLUTTER_TESTING`, `FLUTTER_PERFORMANCE`, `FLUTTER_ARCHITECTURE`, `FLUTTER_PLATFORM`

#### 17.6 Unit Tests

- [x] `test_dart_type_extractor.py` (20 tests) — Classes, mixins, enums, extensions, extension types, typedefs
- [x] `test_dart_function_extractor.py` (22 tests) — Functions, methods, constructors, getters, setters
- [x] `test_dart_api_extractor.py` (18 tests) — Widgets, routes, state managers, gRPC
- [x] `test_dart_model_extractor.py` (16 tests) — ORM models, data classes, migrations
- [x] `test_dart_attribute_extractor.py` (20 tests) — Annotations, imports, isolates, null safety, Dart 3
- [x] `test_dart_parser_enhanced.py` (30 tests) — Framework detection, pubspec parsing, full parse
- [x] **All 1354 tests passing** (126 new + 1228 existing)

#### 17.7 Bugs Fixed (4 total)

| #   | Bug                                             | Fix                                                                                    |
| --- | ----------------------------------------------- | -------------------------------------------------------------------------------------- |
| 58  | `_parse_dart` silently failing (15+ mismatches) | Added missing fields to 14 dataclasses + fallback logic in scanner                     |
| 59  | `packages` in DEFAULT_IGNORE blocked Dart       | Removed `"packages"` from DEFAULT_IGNORE (was for C# NuGet, blocked Flutter monorepos) |
| 60  | `scala_case_classes` references in C# tests     | Removed all references to non-existent field                                           |
| 61  | BPL PracticeCategory validation (50 errors)     | Added 27 Dart/Flutter enum values to PracticeCategory                                  |

#### 17.8 Validation (3 repos)

| Repo            | Dart Files | Classes | Functions | Widgets | Frameworks | SDK Version              |
| --------------- | ---------- | ------- | --------- | ------- | ---------- | ------------------------ |
| isar/isar       | 210        | 168     | 512       | 32      | 13         | Dart 3.5.0, Flutter 3.22 |
| felangel/bloc   | 148        | 88      | 281       | —       | 5          | bloc, provider, mobx     |
| dart-lang/shelf | 45         | 26      | 87        | —       | 3          | shelf, websocket         |

---

### Phase 18: Auto-Compilation Pipeline — Build Pipeline Integration (v4.16.0, Session 54) ✅

> **Purpose**: Ensure new languages/frameworks work correctly with the incremental build pipeline, content-addressed caching, and quality gate verification introduced in PART B.

#### 18.1 Deterministic Output

- [x] `_walk_files()` uses `sorted()` on both dirnames and filenames — all languages benefit automatically
- [x] `json.dumps()` uses `sort_keys=True` — all JSON output is deterministic
- [x] `CODETRELLIS_BUILD_TIMESTAMP` env var — all timestamps are reproducible in CI

#### 18.2 Content-Addressed Caching

- [x] `InputHashCalculator.hash_file()` — SHA-256 first 16 hex chars, works for all file types
- [x] `CacheManager` per-extractor cache — stores and retrieves extractor results by content hash
- [x] `LockfileManager` — writes `_lockfile.json` with full file manifest and extractor versions
- [x] `DiffEngine` — compares current file hashes against lockfile, identifies added/modified/deleted/unchanged

#### 18.3 MatrixBuilder Integration

- [x] `MatrixBuilder.build()` — orchestrates SCAN→DIFF→EXTRACT→COMPILE→PACKAGE lifecycle
- [x] Legacy scanner parity — MatrixBuilder delegates to `scanner.scan()` for extraction, ensuring all 53+ languages produce identical output
- [x] `--incremental` flag — only re-extracts files that changed since last build
- [x] `--deterministic` flag — forces `CODETRELLIS_BUILD_TIMESTAMP` and sorted output
- [x] `--ci` flag — combines deterministic + parallel for CI/CD pipelines

#### 18.4 Quality Gates

- [x] `codetrellis verify` — D1 quality gate: required files exist, valid JSON, [PROJECT] section present, version match, totalFiles > 0
- [x] `codetrellis clean` — purges `_extractor_cache/` and lockfile; `--version` for targeted cleanup

#### 18.5 IExtractor Protocol

- [x] `IExtractor` protocol defined — `manifest`, `cache_key()`, `extract()` methods
- [x] `ExtractorManifest` — name, version, input_patterns, depends_on, output_sections
- [x] **For future extractors**: Implement `IExtractor` protocol to participate in per-file caching

> **Key files:** `codetrellis/cache.py` (534 lines), `codetrellis/builder.py` (546 lines), `codetrellis/interfaces.py` (IExtractor/ExtractorManifest/BuildEvent/BuildResult)
> **Test file:** `tests/unit/test_auto_compilation.py` (62 tests)
> **CLI flags:** `--incremental`, `--deterministic`, `--ci`, `clean`, `verify`

---

### Phase 19: Advanced Research — PART F Prototyping (v4.67, Session 55) ✅

> **Scope:** 7 research prototypes (F1–F7) future-proofing the Matrix architecture.
> **Dependencies added:** `jsonpatch ≥1.33`, `numpy ≥2.4`, `tiktoken ≥0.12`
> **Tests added:** 40 benchmark tests | **PoCs validated:** 6/6 (335 ms)

#### 19.1 JSON-LD Semantic Encoder (F1)

- [x] `MatrixJsonLdEncoder` — converts matrix dict → JSON-LD 1.1 document with `@context`, `@type`, `@id`
- [x] `encode()`, `encode_compact()`, `frame(document, frame_spec)`, `validate()`
- [x] `JsonLdStats` — `total_nodes`, `total_edges`, `sections_encoded`
- [x] Custom `@context` with CodeTrellis vocabulary and schema.org alignment
- [x] **PoC:** 32 sections encoded, 4 469 properties linked, graph validated

#### 19.2 TF-IDF Matrix Embeddings (F2)

- [x] `MatrixEmbeddingIndex` — build, query, save, load vector index per section
- [x] `TFIDFVectorizer` — custom tokenizer, cosine similarity retrieval
- [x] `build_index(sections: Dict[str, str])`, `query(query, top_k)` → `RetrievalResult`
- [x] `save(path)` / `load(path)` — persists vectors + vocabulary + IDF to `.npz` + `.meta.json`
- [x] `get_token_savings(full_tokens, top_k, query)` — **99.4 % token savings** at top-5
- [x] **PoC:** 32 sections indexed, sub-ms retrieval, save/load round-trip verified

#### 19.3 JSON Patch Differential Engine (F3)

- [x] `MatrixDiffEngine` — RFC 6902 compliant via `jsonpatch` library
- [x] `compute_diff(old, new)` → `jsonpatch.JsonPatch`, `apply_patch()`, `verify_patch_integrity()`
- [x] `PatchStats` — `total_operations`, `patch_size_bytes`, `compression_ratio`
- [x] Single-field edit: **62 bytes patch vs 1 349 856 bytes full → 21 772× compression**
- [x] **PoC:** Diff → Apply → Verify round-trip integrity confirmed

#### 19.4 Multi-Level Compression L1/L2/L3 (F4)

- [x] `MatrixMultiLevelCompressor` — `CompressionLevel.L1` (identity), `L2` (signatures), `L3` (skeleton)
- [x] `compress(matrix_text, level)`, `auto_select_level(context_window)`, `auto_select_for_model(model_name)`
- [x] `CompressionResult` — `compression_ratio`, `original_tokens`, `compressed_tokens`, `sections_preserved`
- [x] Benchmarks: L1 = 1.0×, L2 = 1.13× (88.6 % retention), **L3 = 24.10× (4.1 % retention)**
- [x] **PoC:** All 3 levels validated against live matrix.prompt

#### 19.5 Cross-Language Type Mapping (F5)

- [x] `CrossLanguageLinker` — bidirectional type resolution across **19 languages**
- [x] `resolve_type(source_lang, type_name, target_lang)` → `TypeMapping`
- [x] `detect_api_links(matrices: Dict[str, Dict])` → `List[CrossLanguageLink]`
- [x] `merge_matrices()`, `get_available_languages()`
- [x] Covers: Python, TypeScript, JavaScript, Java, Kotlin, C#, Rust, Go, Swift, Ruby, PHP, Scala, R, Dart, Lua, C, C++, SQL, Bash
- [x] **PoC:** 15/15 cross-language type resolutions correct

#### 19.6 Three-Phase Directed Retrieval (F6)

- [x] `MatrixNavigator` — keyword → graph BFS → embedding re-ranking
- [x] `discover(query, max_files, depth)` → `List[FileRelevance]` with `composite_score`
- [x] `get_dependencies(file_path)` → `Set[str]`, `get_reverse_dependencies()`
- [x] Composite: `0.5 × keyword + 0.3 × graph + 0.2 × embedding`
- [x] **PoC:** Multi-hop file discovery with dependency fan-out validated

#### 19.7 MatrixBench Benchmark Suite (F7)

- [x] `MatrixBench` — 5 categories, 22 built-in tasks + 59 language-coverage tasks
- [x] `run_all()`, `run_category()`, `generate_report()`, `export_results()`
- [x] `add_language_coverage_tasks()` — auto-generates tasks for all 53+ languages
- [x] **±0 % deterministic** — results reproducible across runs
- [x] 40 benchmark tests in `tests/benchmarks/matrix_bench.py` — all passing (0.60 s)

> **Key files:**
> `codetrellis/matrix_jsonld.py` (F1), `codetrellis/matrix_embeddings.py` (F2),
> `codetrellis/matrix_diff.py` (F3), `codetrellis/matrix_compressor_levels.py` (F4),
> `codetrellis/cross_language_types.py` (F5), `codetrellis/matrix_navigator.py` (F6),
> `codetrellis/matrixbench_scorer.py` (F7)
> **Test file:** `tests/benchmarks/matrix_bench.py` (40 tests)
> **PoC scripts:** `scripts/research/poc_*.py`, `scripts/research/run_all_pocs.py`
> **Research report:** `docs/research/ADVANCED_TOPICS_REPORT.md`

---

### Step 20: Java Framework Integration (Session 74, v4.94)

Five Java framework-level parsers implemented as supplementary layers on top of base Java parser.

#### 20.1 Spring Boot (v4.94)

- [x] 6 extractors in `extractors/spring_boot/`: bean, autoconfig, endpoint, property, security, data
- [x] `spring_boot_parser_enhanced.py` — SpringBootParseResult, 50+ FRAMEWORK_PATTERNS, VERSION_INDICATORS (1.x-3.x)
- [x] Scanner: ~12 ProjectMatrix fields (`spring_boot_beans`, `spring_boot_endpoints`, `spring_boot_configurations`, etc.)
- [x] Compressor: `[SPRING_BOOT]` section via `_compress_spring_boot()`
- [x] 32 unit tests — all passing

#### 20.2 Spring Framework (v4.94)

- [x] 4 extractors in `extractors/spring_framework/`: di, aop, event, mvc
- [x] `spring_framework_parser_enhanced.py` — SpringFrameworkParseResult, 8 FRAMEWORK_PATTERNS, VERSION_INDICATORS (4.x-6.x)
- [x] Scanner: ~8 ProjectMatrix fields (`spring_framework_di`, `spring_framework_aop`, `spring_framework_events`, `spring_framework_mvc`)
- [x] Compressor: `[SPRING_FRAMEWORK]` section via `_compress_spring_framework()`
- [x] 19 unit tests — all passing

#### 20.3 Quarkus (v4.94)

- [x] 5 extractors in `extractors/quarkus/`: cdi, rest, panache, config, extension
- [x] `quarkus_parser_enhanced.py` — QuarkusParseResult, 30 FRAMEWORK_PATTERNS, version detection (1.x-3.x)
- [x] Scanner: ~12 ProjectMatrix fields (`quarkus_cdi_beans`, `quarkus_endpoints`, `quarkus_panache_entities`, etc.)
- [x] Compressor: `[QUARKUS]` section via `_compress_quarkus()`
- [x] 20 unit tests — all passing

#### 20.4 Micronaut (v4.94)

- [x] 5 extractors in `extractors/micronaut/`: di, http, data, config, feature
- [x] `micronaut_parser_enhanced.py` — MicronautParseResult, 25 FRAMEWORK_PATTERNS, version detection (1.x-4.x)
- [x] Scanner: ~11 ProjectMatrix fields (`micronaut_beans`, `micronaut_endpoints`, `micronaut_controllers`, etc.)
- [x] Compressor: `[MICRONAUT]` section via `_compress_micronaut()`
- [x] 24 unit tests — all passing

#### 20.5 Jakarta EE (v4.94)

- [x] 5 extractors in `extractors/jakarta_ee/`: cdi, servlet, jpa, jaxrs, ejb
- [x] `jakarta_ee_parser_enhanced.py` — JakartaEEParseResult, 18 FRAMEWORK_PATTERNS, version detection (Java EE 5 → Jakarta EE 10+)
- [x] Scanner: ~12 ProjectMatrix fields (`jakarta_ee_cdi_beans`, `jakarta_ee_jpa_entities`, `jakarta_ee_jaxrs_resources`, etc.)
- [x] Compressor: `[JAKARTA_EE]` section via `_compress_jakarta_ee()`
- [x] 32 unit tests — all passing

#### 20.6 Shared Utility

- [x] `extractors/java_utils.py` — `normalize_java_content()` applied in all 25 extractors

#### 20.7 Scanner Evaluation (3 repos)

- [x] spring-petclinic: `[SPRING_BOOT]` 7 beans/16 endpoints/2 configs, `[JAKARTA_EE]` 9 JPA entities — 100% coverage
- [x] quarkus-quickstarts: `[QUARKUS]` 103 CDI beans/253 endpoints/16 Panache/149 extensions — 97% CDI coverage
- [x] micronaut-starter: `[MICRONAUT]` 431 DI beans/8 HTTP routes/3 controllers/6 features — 90% DI coverage

#### 20.8 Bugs Fixed (10 total)

- [x] Regex indentation sensitivity → `normalize_java_content()`
- [x] `@PreAuthorize` inner parens → `"([^"]*)"` pattern
- [x] `@ManyToMany` without args → optional parens
- [x] Bare `@Get`/`@Post` (Micronaut) → optional parens
- [x] WebFlux builder-style routes → `ROUTER_BUILDER_PATTERN`
- [x] Constructor injection → `CONSTRUCTOR_PATTERN`
- [x] `@Secured` pattern unused → added to extract
- [x] Gradle dependency with parens → `\(?\s*` pattern
- [x] Pre-existing `custom_methods` dict-in-join → `str(c)` conversion
- [x] Compressor-Scanner field name mismatches (10+ fields) → aligned all `getattr()` calls

> **Key files:**
> `extractors/spring_boot/*.py` (7 files), `extractors/spring_framework/*.py` (5 files),
> `extractors/quarkus/*.py` (6 files), `extractors/micronaut/*.py` (6 files),
> `extractors/jakarta_ee/*.py` (6 files), `extractors/java_utils.py`,
> `spring_boot_parser_enhanced.py`, `spring_framework_parser_enhanced.py`,
> `quarkus_parser_enhanced.py`, `micronaut_parser_enhanced.py`, `jakarta_ee_parser_enhanced.py`,
> `scanner.py` (7 edits), `compressor.py` (3 edits)
> **Test files:** `tests/unit/test_{spring_boot,spring_framework,quarkus,micronaut,jakarta_ee}_parser_enhanced.py` (127 tests)
> **Analysis report:** `docs/JAVA_FRAMEWORK_ANALYSIS_REPORT.md`

---

_Checklist Version: 5.6_
_Updated: Session 74 - Phase BZ: Java Framework Parsers (v4.94) — 5 Java framework parsers (Spring Boot 1.x-3.x / Spring Framework 4.x-6.x / Quarkus 1.x-3.x / Micronaut 1.x-4.x / Jakarta EE Java EE 5→Jakarta EE 10+), 25 extractors in 5 directories + java_utils.py, 5 parser files, ~60 ProjectMatrix fields, scanner integration (5 \_parse\_* methods, build file extension hooks), compressor (5 sections + 5 \_compress\_* methods), Scanner Evaluation Round 1 on 3 repos (spring-petclinic 100% coverage, quarkus-quickstarts 97% CDI, micronaut-starter 90% DI), 10 bugs fixed (regex indentation, annotation patterns, compressor field alignment), 127 new tests, 6643 total tests passing_
_Updated: Session 73 - Phase BY: Litestar + Pydantic Enhanced Framework Support (v4.93) — EnhancedLitestarParser with 12 dataclasses, 18 framework patterns, 13 extraction methods, Starlite 1.x + Litestar 2.x+ (routes/controllers/guards/dependencies/middleware/listeners/websockets/exception_handlers/DTOs/plugins/stores/security), EnhancedPydanticParser with 11 dataclasses, 12 framework patterns, 10 extraction methods, Pydantic v1.0-v2.4 (models/RootModel/settings/field_validator/model_validator/validator/root_validator/validate_call/field_serializer/model_serializer/TypeAdapter/custom_types/discriminated_unions/dataclasses/plugins), 19 ProjectMatrix fields (12 Litestar + 7 Pydantic), scanner dispatch + compressor 19 sections, Scanner Evaluation Round 1 on 3 repos (litestar-org/litestar-fullstack: routes + controllers + dependencies + models, pydantic/pydantic-settings: models + settings, litestar-org/litestar-hello-world: 2 routes), 3 bugs fixed (middleware regex group, RootModel nested brackets, test file classification), 102 new tests (51 Litestar + 51 Pydantic), 6516 total tests passing_
_Updated: Session 64 - Phase BR: Leaflet / Mapbox Mapping Support (v4.75) — 5 Leaflet extractors (map, layer, control, interaction, api), EnhancedLeafletParser with 19 framework patterns, Leaflet v0.7-v1.9+ / Mapbox GL JS / MapLibre GL JS / react-leaflet / react-map-gl / vue-leaflet / deck.gl / turf.js, 26 ProjectMatrix fields, 50 BPL practices (LEAFLET001-LEAFLET050), 115 new tests, 0 bugs, 3-repo validation (Leaflet/Leaflet, PaulLeCam/react-leaflet, visgl/react-map-gl), 5554 total tests passing_
_Updated: Session 60 - Phase BN: Three.js / React Three Fiber Support (v4.71) — 5 Three.js extractors (scene, component, material, animation, api), EnhancedThreeJSParser with regex AST, R3F v1-v8 + Three.js r60-r170, 100+ drei components across 10 categories, ~33 ProjectMatrix fields, 50 BPL practices (THREEJS001-THREEJS050), 63 new tests, 4 bugs fixed, 3-repo validation (react-three-fiber, drei, r3f-wawatmos-starter), 5238 total tests passing_
_Updated: Session 55 - PART F: Advanced Research (7 Topics) — JSON-LD encoder (F1), TF-IDF embeddings (F2), JSON Patch differential (F3, 21,772× compression), multi-level compression L1/L2/L3 (F4), cross-language type mapping for 19 languages (F5), 3-phase directed retrieval (F6), MatrixBench benchmark suite with 40 tests (F7). All 6 PoCs validated, all 40 benchmark tests passing, research report generated._
_Updated: Session 54 - Phase BJ: Auto-Compilation Pipeline (PART B) — MatrixBuilder orchestrator, content-addressed SHA-256 caching, IExtractor protocol, DiffEngine, --incremental/--deterministic/--ci flags, codetrellis clean + verify, Phase 0 stabilization (version sync, sorted traversal, build timestamp, sort_keys), D4 determinism gate passed, 62 new tests, 4609 total tests passing._
_Updated: Session 54b - A5.x Module Coverage Expansion — Phase 10 added: A5.x Module Integration (cache_optimizer SECTION_STABILITY ~350 entries, mcp_server AGGREGATE_RESOURCES 8 categories/52 APIs/27 state/19 components/31 styling/12 routing, jit_context EXTENSION_TO_SECTIONS 50+ extensions + PATH_PATTERN_SECTIONS 40+ patterns, skills_generator 17 templates with full framework detect_sections). 201 A5.x tests, 4346 total tests passing._
_Updated: Session 51 - Phase BG: Lit / Web Components Framework Support (v4.65) — 5 Lit extractors (component, property, event, template, api), EnhancedLitParser with regex AST, Polymer 1.x-3.x / lit-element 2.x / lit 2.x-3.x, 25+ framework + 35+ feature patterns, 25+ ProjectMatrix fields, 50 BPL practices (LIT001-LIT050), 109 new tests, 6 bugs fixed, 3-repo validation (lit/lit, pwa-starter, synthetic lit_demo), 4072 total tests passing_
_Updated: 2026-02-16 - Phase AM: Sass/SCSS Language Support (v4.44) — 5 Sass extractors (variable, mixin, function, module, nesting), EnhancedSassParser with regex AST, Dart Sass 1.x/LibSass/Ruby Sass version detection, .scss + .sass (indented) syntax, @use/@forward module system, 100+ built-in functions, 20+ framework detection, 18 ProjectMatrix fields, 50 BPL practices (SASS001-SASS050), 50 new tests, 0 bugs, 2-repo validation (Bootstrap, Bulma), 2499 total tests passing_
_Updated: 2026-02-16 - Phase AK: Styled Components Framework Support (v4.42) — 5 SC extractors, EnhancedStyledComponentsParser with regex AST, v1-v6 support, 30+ CSS-in-JS ecosystem detection, 18 ProjectMatrix fields, 50 BPL practices (SC001-SC050), 57 new tests, 0 bugs, 3-repo validation (styled-components-website, hyper, xstyled), 2386 total tests passing_
_Updated: 2026-02-13 - Phase X: Dart Language Support (v4.27) — 5 Dart extractors, EnhancedDartParser with regex AST + tree-sitter-dart + analysis_server LSP, Dart 2.0-3.5+ support, Flutter 1.x-3.x+, 70+ framework detection, pubspec.yaml/lock parsing, 50 BPL practices (DART001-DART050), 126 new tests, 4 bugs fixed, 3-repo validation (Isar, Bloc, Shelf), 1354 total tests passing_
_Updated: 2026-02-13 - Phase W: R Language Support (v4.26) — 5 R extractors, EnhancedRParser with regex AST + R-languageserver LSP, R 2.x-4.4+ support, 6 class systems, 70+ framework detection, DESCRIPTION/NAMESPACE/renv.lock parsing, 50 BPL practices (R001-R050), 62 new tests, 11 bugs fixed, 3-repo validation (dplyr, Shiny, plumber), 1228 total tests passing_
_Updated: 2026-02-12 - Phase R: C Language Support (v4.19) — 5 C extractors, EnhancedCParser with tree-sitter-c AST + clangd LSP, C89-C23 detection, 25+ frameworks, 50 BPL practices (C001-C050), 59 new tests, 9 bugs fixed, 3-repo validation (jq, Redis, curl), 640 total tests passing_
_Updated: 2026-02-12 - Phase N: Rust Language Support (v4.14) — 5 Rust extractors, EnhancedRustParser, 50 BPL practices (RS001-RS050), 46 new tests, 6 bugs fixed, 3-repo validation (Axum, Diesel, actix-web), 315 total tests passing_
_Updated: 2026-02-12 - Phase M: C# Language Support (v4.13) — 6 C# extractors, EnhancedCSharpParser, 50 BPL practices (CS001-CS050), 97 new tests, 10 bugs fixed, 3-repo validation (eShop, Ardalis/JT CleanArchitecture)_
_Updated: 2026-02-12 - Phase L: Java & Kotlin Language Support (v4.12) — 6 Java extractors, 2 Kotlin extractors, tree-sitter-java AST, Eclipse JDT LSP, Panache detection, 50 Java BPL practices, 12 bugs fixed, 3-repo validation_
_Updated: 2026-02-11 - Phase K: Systemic Improvements (v4.11) — Weighted domain scoring, multi-signal detection, discovery-driven stack, ORM-DB affinity graph_
_Updated: 2026-02-11 - Phase J: R4 Evaluation & .gitignore-Aware Scanning (v4.10) — GitignoreFilter, 7 extractors updated, R4 evaluation (Gitea/Strapi/Medusa)_
_Updated: 2026-02-09 - Phase H: Deep Pipeline Fixes (v4.8) — Brace-balanced extraction, adaptive compressor, BPL ratio limiting, directory summary, primary language priority_
_Updated: 2026-02-09 - Phase G: PocketBase 16-gap remediation (v4.7) — BaaS domain, middleware factories, CLI commands, .d.ts filtering, route prefix tracking, plugin detection_
_Updated: 2026-02-09 - Phase F: Go language support (v4.5), SemanticExtractor (v4.6), architecture detection for go.mod, PocketBase validated_
_Updated: 2026-02-09 - Phase D: Public Repository Validation Framework_
_BPL v1.4: tiktoken integration, OutputFormat, 647 practices (497+50 Rust+50 R+50 Lit), min_python/contexts formalized_
_Updated: Session 75 - Phase CA: Java Framework Parsers Round 2 (v4.95) — 5 Java framework parsers (Vert.x/Hibernate/MyBatis/Apache Camel/Akka), 35 files, 25 extractors, 5 parsers, ~45 ProjectMatrix fields, scanner (5 `\_parse_\*` methods) + compressor (5 sections), 4 scanner bugs fixed, 109 new tests, 6752 total tests passing\_
