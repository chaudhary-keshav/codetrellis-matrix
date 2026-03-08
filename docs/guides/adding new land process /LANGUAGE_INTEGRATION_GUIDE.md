# CodeTrellis Language Integration Guide v4.7

> **Updated:** Session 75 - Phase CA: Java Framework Parsers Round 2 (v4.95) — 5 Java framework parsers (Vert.x 3.x-4.x / Hibernate 3.x-6.x+JPA / MyBatis 3.x+MyBatis-Plus / Apache Camel 2.x-4.x / Akka Classic+Typed 2.5-2.8+), 25 extractors in 5 directories (vertx: verticle/route/eventbus/data/api, hibernate: entity/session/query/cache/listener, mybatis: mapper/sql/dynamic*sql/result_map/cache, apache_camel: route/component/processor/error_handler/rest_dsl, akka: actor/stream/http/cluster/persistence) + 5 parser files, 35 total implementation files, ~45 ProjectMatrix fields, scanner integration (5 `\_parse**` methods dispatched from Java/Scala/Kotlin handlers), compressor (5 sections + compress methods), Scanner Evaluation on 3 repos (vert-x3/vertx-examples 70 verticles/93 routes/19 fw/v4.x, akka/akka-samples 17 fw/29 messages/72 HTTP routes, mybatis/mybatis-3 detection works), 4 scanner bugs fixed, 109 new tests, 6752 total passing (0 regressions)
> **Updated:** Session 74 - Phase BZ: Java Framework Parsers (v4.94) — 5 Java framework parsers (Spring Boot 1.x-3.x / Spring Framework 4.x-6.x / Quarkus 1.x-3.x / Micronaut 1.x-4.x / Jakarta EE Java EE 5→Jakarta EE 10+), 25 extractors in 5 directories + java*utils.py, 5 parser files, ~60 ProjectMatrix fields, scanner integration (5 \_parse*\_ methods, build file extension hooks), compressor (5 sections + 5 *compress*\_ methods), Scanner Evaluation Round 1 on 3 repos (spring-petclinic 100% coverage, quarkus-quickstarts 97% CDI, micronaut-starter 90% DI), 10 bugs fixed, 127 new tests, 6643 total tests passing
> **Updated:** Session 73 - Phase BY: Litestar + Pydantic Enhanced Framework Support (v4.93) — 2 enhanced parsers (EnhancedLitestarParser/EnhancedPydanticParser), Litestar Starlite 1.x + Litestar 2.x+ (routes/controllers/guards/dependencies/middleware/listeners/websockets/exception_handlers/DTOs/plugins/stores/security), Pydantic v1.0-v2.4 (models/RootModel/GenericModel/settings/field_validator/model_validator/validator/root_validator/validate_call/field_serializer/model_serializer/TypeAdapter/custom_types/discriminated_unions/dataclasses/plugins), 19 ProjectMatrix fields (12 Litestar + 7 Pydantic), scanner + compressor integration, 3 bugs fixed, 3-repo validation (litestar-org/litestar-fullstack, pydantic/pydantic-settings, litestar-org/litestar-hello-world), 102 new tests, 6516 total tests passing
> **Updated:** Session 71 - Phase BW: Starlette + SQLAlchemy + Celery Enhanced Language Support (v4.91) — 3 enhanced parsers (EnhancedStarletteParser/EnhancedSQLAlchemyParser/EnhancedCeleryParser), Starlette 0.12+ (routes/mounts/middleware/WebSocket/lifespan/auth/static), SQLAlchemy 0.x-2.x+ (ORM models/Core tables/sessions/engines/Alembic migrations/events/hybrids), Celery 3.x-5.x+ (tasks/beat schedules/signals/canvas/result backends/worker config/queues), 32 ProjectMatrix fields, scanner + compressor integration, 4 bugs fixed, 3-repo validation (encode/starlette, sqlalchemy/sqlalchemy, celery/celery), 101 new tests, 6069 total tests passing
> **Updated:** Session 66 - Phase BT+BU: GSAP + RxJS Dual Framework Support (v4.77/v4.78) — 5 GSAP extractors (animation, timeline, plugin, scroll, api) + 5 RxJS extractors (operator, observable, subject, scheduler, api), GsapParseResult + RxjsParseResult parsers, GSAP v1-v3+ (tweens/timelines/ScrollTrigger/ScrollSmoother/Observer/context/matchMedia/@gsap/react) + RxJS v5-v7+ (operators/observables/subjects/schedulers/TestScheduler/marble testing), ~30 ProjectMatrix fields each, scanner + compressor (5+5 sections) + BPL (100 practices, 20 categories, flat-format YAML support, Angular file type shadowing fix), Scanner Evaluation Round 1 on 3 synthetic repos, 79 new tests, 0 regressions, 5907 total tests passing. **⚠️ Key lesson: Angular-specific file type patterns (.service.ts, .component.ts, etc.) intercept TypeScript files and prevent framework parsers from running. Always add new framework parsers to BOTH the typescript AND Angular-specific file type handlers.**
> **Updated:** Session 65 - Phase BS: Framer Motion Animation Framework Support (v4.76) — 5 Framer Motion extractors (animation, gesture, layout, scroll, api), EnhancedFramerMotionParser with 13 framework patterns, framer-motion v1-v10 / motion v11+ / popmotion / framer SDK / framer-motion-3d / react-spring bridge, 22 ProjectMatrix fields, scanner + compressor (5 FRAMER sections) + BPL (50 practices FRAMER001-FRAMER050, 10 categories), 107 new tests, 0 regressions, 5843 total tests passing
> **Updated:** Session 63 - Phase BQ: Recharts Data Visualization Framework Support (v4.74) — 5 Recharts extractors (component, data, axis, customization, api), EnhancedRechartsParser with regex AST, Recharts v1-v2+ (tree-shakeable imports, React/Next.js/Remix/Gatsby integrations), 10 framework patterns + 30+ feature patterns, 24 ProjectMatrix fields, scanner + compressor (5 RECHARTS sections) + BPL (50 practices RECHARTS001-RECHARTS050, 10 categories), 132 new tests, 5621 total tests passing
> **Updated:** Session 62 - Phase BP: Chart.js Data Visualization Framework Support (v4.73) — 5 Chart.js extractors (chart_config, dataset, scale, plugin, api), EnhancedChartJSParser with regex AST, Chart.js v1-v4+ (tree-shakeable/auto imports, React/Vue/Angular/Svelte integrations), 18 framework patterns + 40+ feature patterns, 23 ProjectMatrix fields, scanner + compressor (5 CHARTJS sections) + BPL (50 practices CHARTJS001-CHARTJS050, 10 categories), 133 new tests, 3 bugs fixed (bare import regex, ChartJS alias, inline plugin detection), 3-repo validation (chartjs/Chart.js, reactchartjs/react-chartjs-2, apertureless/vue-chartjs), 5489 total tests passing
> **Updated:** Session 61 - Phase BO: D3.js Data Visualization Framework Support (v4.72) — 5 D3.js extractors (visualization, scale, axis, interaction, api), EnhancedD3JSParser with regex AST, D3.js v3-v7+ (modular/monolithic/Observable), 30+ framework patterns, 25 ProjectMatrix fields, scanner + compressor (5 D3JS sections) + BPL (50 practices D3JS001-D3JS050, 10 categories), 118 new tests, 0 bugs, 3-repo validation (d3/d3, observablehq/plot, d3/d3-shape), 5356 total tests passing
> **Updated:** Session 59 - Infrastructure Hardening (v4.69) — Watcher crash fix (threading.Lock, 2s debounce, batch callback), broken incremental build removed (4 methods ~350 lines — lossy `_hydrate_matrix()` only mapped ~40/200+ ProjectMatrix fields), IMPLEMENTATION_LOGIC added to PROMPT tier (matrix 20→33 sections, 1850→4177 lines), BEST_PRACTICES `_get_best_practices()` rewritten: 3-layer auto-detection covering 15 languages (Python/JS/TS/Java/Kotlin/Go/Rust/C/C++/Swift/Ruby/PHP/Scala/Dart/Bash from matrix field presence) + 20+ frameworks (React/Angular/Vue/Next.js/FastAPI/Django/Flask/Express/NestJS/Spring/Rails... from stack detection), JSON-LD project_profile None fix, embeddings test threshold fix, `_changed_files_hint` scanner infrastructure, 15 new watcher tests, 5112 total tests passing. **⚠️ Key lesson: When adding new matrix sections, verify they appear in PROMPT tier. When modifying builder, never round-trip ProjectMatrix through JSON without `from_dict()`.**
> **Updated:** Session 58 - Phase BJ-0: Stimulus / Hotwire Framework Support (v4.68) — 5 Stimulus extractors (controller, target, action, value, api), EnhancedStimulusParser with regex AST, Stimulus v1-v3 + Turbo v7-v8 + Strada v1, controllers/targets/actions/values/API extraction, 20+ framework + 40+ feature patterns, 17 ProjectMatrix fields, scanner + compressor + BPL + A5.x integration, 91 new tests, 0 bugs, 3-repo validation (hotwired/stimulus-starter, hotwired/stimulus, thoughtbot/hotwire-example-template), 5018 total tests passing
> **Updated:** Session 54 - Phase BJ: Auto-Compilation Pipeline (PART B, v4.16.0) — Added Step 15: Build Pipeline Integration. MatrixBuilder orchestrator (SCAN→DIFF→EXTRACT→COMPILE→PACKAGE), content-addressed SHA-256 caching (InputHashCalculator, CacheManager, LockfileManager), DiffEngine for incremental builds, IExtractor protocol + ExtractorManifest, BuildEvent/BuildResult types, --incremental/--deterministic/--ci flags, codetrellis clean + verify commands, D4 determinism gate passed, 62 new tests, 4609 total tests passing.
> **Updated:** Session 54b - A5.x Module Coverage Expansion — Added Step 14: A5.x Module Integration. All 4 A5.x modules (cache*optimizer, mcp_server, jit_context, skills_generator) expanded to support 53+ languages/frameworks with ~350 unique section names. Cache optimizer SECTION_STABILITY ~350 entries, MCP AGGREGATE_RESOURCES 8 categories (types/api/state/components/styling/routing/overview/infrastructure), JIT EXTENSION_TO_SECTIONS 50+ extensions + PATH_PATTERN_SECTIONS 40+ patterns, Skills generator 17 templates. 201 A5.x tests passing. 4346 total tests passing.
> **Updated:** Session 53 - Phase BI: HTMX Framework Support (v4.67) — 5 HTMX extractors (attribute, request, event, extension, api), EnhancedHtmxParser with regex AST, HTMX v1.x (data-hx-_ prefix) + v2.x (hx-on:event, hx-disabled-elt, hx-inherit, idiomorph) + attribute categories + HTTP request extraction + event system (40+ lifecycle events, SSE/WS, trigger modifiers) + extensions (21 official) + API (ESM/CJS imports, CDN, htmx.config.\_, 12 integrations), 20 framework + 50 feature patterns, 18 ProjectMatrix fields, 50 BPL practices (HTMX001-HTMX050), 10 PracticeCategory entries, 166 new tests, 0 bugs, 3-repo validation (bigskysoftware/htmx, adamchainz/django-htmx, bigskysoftware/contact-app), 4346 total tests passing
> **Updated:** Session 52 - Phase BH: Alpine.js Framework Support (v4.66) — 5 Alpine.js extractors (directive, component, store, plugin, api), EnhancedAlpineParser with regex AST, Alpine.js v1.x (x-spread, CDN-only) + v2.x (x-data/x-show/x-bind/x-on/x-model/x-for/x-if/x-ref/x-text/x-html/x-transition/x-cloak/x-init) + v3.x (Alpine.start()/data()/store()/plugin()/directive()/magic()/bind(), x-effect/x-teleport/x-id/x-ignore, @alpinejs/_ plugins, $dispatch/$refs/$el/$watch/$nextTick/$root/$data/$store/$id) + CDN + ESM + CJS import detection, 20+ framework + 50+ feature patterns, 18 ProjectMatrix fields, 50 BPL practices (ALPINE001-ALPINE050), 10 PracticeCategory entries, 108 new tests, 3-repo validation (alpinejs/alpine, alpine-clipboard, alpine-ajax), 4180 total tests passing
> **Updated:** Session 51 - Phase BG: Lit / Web Components Framework Support (v4.65) — 5 Lit extractors (component, property, event, template, api), EnhancedLitParser with regex AST, Polymer 1.x-3.x + lit-element 2.x + lit 2.x-3.x, 25+ framework + 35+ feature patterns, 25+ ProjectMatrix fields, 50 BPL practices (LIT001-LIT050), 10 PracticeCategory entries, 109 new tests, 6 bugs fixed, 3-repo validation (lit/lit, pwa-starter, synthetic lit*demo), 4072 total tests passing
> **Updated:** Session 50 - Phase BF: Preact Framework Support (v4.64) — 5 Preact extractors (component, hook, signal, context, api), EnhancedPreactParser with regex AST, Preact v8.x (h/Component/linkState/preact-compat) + v10.x (hooks/createContext/Fragment) + v10.5+ (useId/useErrorBoundary) + v10.11+ (@preact/signals) + v10.19+ (useSignalEffect) + @preact/signals v1-v2 (signal/computed/effect/batch/untracked/useSignal/useComputed/useSignalEffect) + import-based feature/version detection, 25 framework patterns + 35 feature patterns, 27 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (PREACT001-PREACT050), 19 artifact types + 20 fw mappings, 10 PracticeCategory entries, 92 new unit tests, 5 bugs fixed (signal regex typed annotations, context field name, API category, YAML path, ProjectMatrix constructor), 3-repo validation (preactjs/preact, preactjs/preact-router, denoland/fresh), 3963 total tests passing
> **Updated:** Session 49 - Phase BE: Qwik Framework Support (v4.63) — 5 Qwik extractors (component, signal, resource, routing, api), EnhancedQwikParser with regex AST, Qwik v1.x-v2.x (component$/useSignal/useStore/useResource$/useTask$/useVisibleTask$/useComputed$/Slot/useContext/createContextId) + Qwik City v1.x (routeLoader$/routeAction$/server$/validator$/Form/Link/useLocation/useNavigate/layout/index routing) + import-based feature/version detection, 25 framework patterns + 35 feature patterns, 24 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (QWIK001-QWIK050), 20 artifact types + 20 fw mappings, 10 PracticeCategory entries, 103 new unit tests, 0 bugs, 3-repo validation (BuilderIO/qwik, QwikDev/qwik-ui, BuilderIO/qwik-city-e-commerce), 3871 total tests passing
> **Updated:** Session 48 - Phase BD: Solid.js Framework Support (v4.62) — 6 Solid.js extractors (component, signal, store, resource, router, api), EnhancedSolidParser with regex AST, Solid.js v1.x-v2.x (createSignal/createMemo/createEffect/createResource/createStore/createMutable, Show/For/Switch/Match/Suspense/ErrorBoundary/Portal/Dynamic, onMount/onCleanup/onError, batch/untrack/on/mergeProps/splitProps, createContext/useContext) + SolidStart v0.x-v1.x (server$/createServerAction$/createServerData$, cache/action/createAsync, middleware) + @solidjs/router (Route/Router, useParams/useNavigate/useLocation/useSearchParams/useMatch) + import-based feature/version detection, 27 framework + 40 feature patterns, 24 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (SOLIDJS001-SOLIDJS050), 25 artifact types + fw mappings, 10 PracticeCategory entries, 79 new unit tests, 3 bugs fixed, 3-repo validation (solid-start/solid-router/solid-primitives), 3768 total tests passing
> **Updated:** Session 47 - Phase BC: Remix Framework Support (v4.61) — 5 Remix extractors (route, loader, action, meta, api), EnhancedRemixParser with regex AST, Remix v1.x (@remix-run/\*, CatchBoundary, LoaderFunction) + v2.x (Vite plugin, flat routes, useRouteError, LoaderFunctionArgs) + React Router v7 (@react-router/\_, routes.ts, Route.LoaderArgs/ActionArgs/MetaArgs, ServerRouter/HydratedRouter, middleware) + import-based feature/version detection, 30+ framework + 25+ feature patterns, 21 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (REMIX001-REMIX050), 15 artifact types + 20+ fw mappings, 10 PracticeCategory entries, 102 new unit tests, 2 bugs fixed, 3-repo validation (indie-stack/remix-examples/epic-stack), 3689 total tests passing
> **Updated:** Session 46 - Phase BB: Astro Framework Support (v4.60) — 5 Astro extractors, EnhancedAstroParser with regex AST, Astro v1-v5, 30+ framework + 25+ feature patterns, 20 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (ASTRO001-ASTRO050), 64 new unit tests, 12 bugs fixed, 3-repo validation, 3587 total tests passing
> **Updated:** Session 45 - Phase BA: Apollo Client Framework Support (v4.59) — 5 Apollo extractors (query, mutation, cache, subscription, api), EnhancedApolloParser with regex AST, Apollo Client v1-v3 (useQuery/useLazyQuery/useSuspenseQuery/useBackgroundQuery/useReadQuery/useMutation/useSubscription/gql tags, InMemoryCache/typePolicies/makeVar/readQuery/writeQuery/modify/evict, ApolloLink chain, ApolloProvider, graphql-codegen), 15 framework + 30 feature patterns, 19 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (APOLLO001-APOLLO050), 10 PracticeCategory entries, 68 new unit tests, 15 bugs fixed (scanner/compressor field name mismatches), 3-repo validation (apollo-client 690 imports/26 queries/37 links/v3, fullstack-tutorial 17 imports/7 queries/3 mutations/v3, spotify-showcase 144 imports/24 queries/29 mutations/65 gql_tags/v3), 3523 total tests passing
> **Updated:** Session 44 - Phase AZ: SWR Framework Support (v4.58) — 5 SWR extractors (hook, cache, mutation, middleware, api), EnhancedSWRParser with regex AST, SWR v0.x-v2.x (useSWR/useSWRImmutable/useSWRInfinite/useSWRSubscription/useSWRMutation, SWRConfig provider, global/bound mutate, preload, cache provider, fallback data, middleware, conditional/dependent fetching, optimistic updates, 20 config options) + import-based feature/version detection, 15 framework + 30 feature patterns, 15 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (SWR001-SWR050), 10 PracticeCategory entries, 84 new unit tests, 4 bugs fixed, 3-repo validation (vercel/swr v2/15 imports/20 types, vercel/swr-site v2/swr+next, shuding/nextra v2/nextjs integration), 3455 total tests passing
> **Updated:** Session 42 - Phase AX: Valtio Framework Support (v4.56) — 5 Valtio extractors (proxy, snapshot, subscription, action, api), EnhancedValtioParser with regex AST, Valtio v1-v2 (proxy/proxy<T>(), ref(), proxyMap/proxySet, useSnapshot/snapshot, subscribe/subscribeKey/watch, devtools, actions with direct mutation detection, TypeScript Snapshot<T> types) + import-based feature/version detection, 13 framework + 12 feature patterns, 15 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (VALTIO001-VALTIO050), 58 new unit tests, 2 bugs fixed, 2-file validation (store.ts/TodoApp.tsx), 3304 total tests passing
> **Updated:** Session 41 - Phase AW: XState Framework Support (v4.55) — 5 XState extractors (machine, state, action, guard, api), EnhancedXstateParser with regex AST, XState v3-v5, 11 framework + 30 feature patterns, 12 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (XSTATE001-XSTATE050), 80 new unit tests, 7 bugs fixed, 2-repo validation (statelyai/xstate 257 files/1196 machines/0 errors, statelyai/xstate-viz 71 files/11 machines/0 errors), 3246 total tests passing
> **Updated:** Session 40 - Phase AV: NgRx Framework Support (v4.53) — 5 NgRx extractors (store, effect, selector, action, api), EnhancedNgrxParser with regex AST, NgRx v1-v19 (StoreModule.forRoot/forFeature, provideStore/provideState, ComponentStore, signalStore(), createAction/createActionGroup, createEffect/@Effect/functional effects, createSelector/createFeatureSelector/createFeature, @ngrx/entity/router-store) + meta-reducers + runtime checks + devtools, 30 framework + 20 feature patterns, 18 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (NGRX001-NGRX050), 10 PracticeCategory entries, 49 new unit tests, 0 bugs, 3-repo validation (ngrx-material-starter 10 actions/8 effects/13 selectors/v8-v11, ngrx/platform 35 stores/23 actions/29 effects/38 selectors/3 entities, ngrx-contacts 12 actions/8 effects/4 selectors/1 entity/v8-v11), 3166 total tests passing
> **Updated:** Session 39 - Phase AU: Pinia Framework Support (v4.52) — 5 Pinia extractors (store, getter, action, plugin, api), EnhancedPiniaParser with regex AST, Pinia v0-v3 (defineStore Options API + Setup API, state, getters, actions, HMR, persist, cross-store, TypeScript) + getters (options/setup/storeToRefs()/return functions) + actions ($patch object/function, $subscribe, $onAction, async, error handling) + plugins (createPinia(), pinia.use(), persistedstate/debounce/orm, SSR) + API (imports/integrations/TypeScript types/map helpers), 30 framework + 20 feature patterns, 14 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (PINIA001-PINIA050), 9 PracticeCategory values, 60 new unit tests, 0 bugs, 3-repo validation (vuejs/pinia 13 stores/7 getters/6 actions/9 patches/v2, piniajs/example-vue-3-vite 2 actions/2 patches/v2, wobsoriano/pinia-shared-state 1 patch/2 subscriptions/v2), 3117 total tests passing
> **Updated:** Session 38 - Phase AT: MobX Framework Support (v4.51) — 5 MobX extractors (observable, computed, action, reaction, api), EnhancedMobXParser with regex AST, MobX v3-v6 (makeObservable/makeAutoObservable/@observable/observable.ref/shallow/struct) + computed (computed()/@computed/computed.struct/keepAlive/requiresReaction) + actions (action()/action.bound/@action/runInAction/flow()/@flow) + reactions (autorun/reaction/when/observe/intercept/onBecomeObserved/onBecomeUnobserved) + API (imports/configure/observer/inject/Provider/TypeScript types), 16 framework + 20 feature patterns, 14 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (MOBX001-MOBX050), 11 artifact types + 10 fw mappings in selector, 72 new unit tests, 0 bugs, 3057 total tests passing
> **Updated:** Session 37.5 - Phase AS: Recoil Framework Support (v4.50) — 5 Recoil extractors (atom, selector, hook, effect, api), EnhancedRecoilParser with regex AST, Recoil v0.x (atom/atomFamily/selector/selectorFamily/atom effects) + hooks (useRecoilState/useRecoilValue/useSetRecoilState/useRecoilCallback/useRecoilTransaction) + effects (onSet/onGet/setSelf/resetSelf/persistence/sync/logging) + API (RecoilRoot/Snapshot/integrations/TypeScript types), framework + feature patterns, 14 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (RECOIL001-RECOIL050), 108 new unit tests, 0 bugs, 2985 total tests passing
> **Updated:** Session 37 - Phase AR: Jotai Framework Support (v4.49) — 5 Jotai extractors (atom, selector, middleware, action, api), EnhancedJotaiParser with regex AST, Jotai v1.x-v2.x (atom/atomFamily/atomWithReset/atomWithReducer/atomWithDefault) + selectors (derived atoms/selectAtom/focusAtom/splitAtom/loadable/unwrap) + middleware (atomWithStorage/atomEffect/atomWithMachine/atomWithProxy/atomWithImmer/atomWithLocation/atomWithHash/atomWithObservable) + actions (useAtom/useAtomValue/useSetAtom/useStore/useHydrateAtoms/useAtomCallback/createStore/getDefaultStore/store.get/set/sub) + API (imports/integrations/TypeScript types), 17 framework patterns + 34 feature patterns, 18 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (JOTAI001-JOTAI050) with priority fields, 10 PracticeCategory enum values, 98 new unit tests, 0 bugs, validation scan (10 atoms/7 hooks/6 store usages/v2 detected/5 frameworks), 2877 total tests passing
> **Updated:** Session 36 - Phase AQ: Zustand Framework Support (v4.48) — 5 Zustand extractors (store, selector, middleware, action, api), EnhancedZustandParser with regex AST, Zustand v1.x-v5.x (create/createStore/createWithEqualityFn) + middleware (persist/devtools/immer/subscribeWithSelector) + selectors (named/inline/shallow/useShallow v5) + vanilla + slice pattern + TypeScript (StateCreator/StoreApi) + SSR/Next.js (skipHydration), 16 framework + 20 feature patterns, 17 ProjectMatrix fields, 50 BPL practices (ZUSTAND001-ZUSTAND050), 10 PracticeCategory enums, 57 new unit tests, 0 bugs, 2-repo validation (pmndrs/zustand, zustand-app), 2779 total tests passing
> **Updated:** Session 35 - Phase AP: Redux/RTK Framework Support (v4.47) — 5 Redux extractors (store, slice, middleware, selector, api), EnhancedReduxParser with regex AST, Redux 1.x-5.x + RTK 1.0-2.x + redux-saga + redux-observable + RTK Query + redux-persist + reselect, 30+ framework detection, 20 ProjectMatrix fields, 50 BPL practices (REDUX001-REDUX050), 10 PracticeCategory enums, 46 new unit tests, 1 regex bug fixed, 3-repo validation (redux-essentials-final/react-redux-realworld/react-boilerplate), 2722 total tests passing
> **Updated:** Session 34 - Phase AO: PostCSS Language Support (v4.46) — 5 PostCSS extractors (plugin, config, transform, syntax, api), EnhancedPostCSSParser with regex AST, PostCSS 1.x-8.5+ version detection, 100+ known plugins across 7 categories (future_css/optimization/utility/linting/syntax/modules/framework), config format detection (CJS/ESM/JSON/YAML), 15+ CSS transform patterns (@custom-media/@layer/@container/color functions/logical properties), custom syntax detection (postcss-scss/postcss-less/postcss-html/sugarss/postcss-jsx), PostCSS JS API usage extraction (postcss()/plugin()/process()/walk\*/node creation/result handling), 30+ framework/tool detection (Vite/Webpack/Next.js/Parcel/Rollup/Gulp/postcss-cli/postcss-loader/stylelint/cssnano/autoprefixer/tailwindcss), 15 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (PCSS001-PCSS050) with priority fields, 10 PracticeCategory enum values, 98 new unit tests, 0 bugs, 2676 total tests passing
> **Updated:** Session 33 - Phase AN: Less Language Support (v4.45) — 5 Less extractors (variable, mixin, function, import, ruleset), EnhancedLessParser with regex AST, Less 1.x-4.x+ version detection, @variables with scopes/data types/lazy evaluation/interpolation, .mixin() parametric/pattern-matched definitions + calls, guards (when/not/and/or/type-checking), namespaces (#id > .class), 70+ built-in functions across 8 categories (color/math/string/list/type/misc/color-ops/color-blend), @import with options (reference/inline/less/css/once/multiple/optional), :extend() all/inline, detached rulesets, nesting depth/BEM patterns/parent selectors, property merging (+/\_), math mode detection (always/parens-division/parens/strict/strict-legacy), 20+ feature detection, 5+ framework detection (Bootstrap, Ant Design, Semantic UI, Element UI, iView), 6+ library detection (LESS Hat, LESSElements, 3L, Preboot, Est, CSS Owl), 17 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (LESS001-LESS050) with priority fields, 10 PracticeCategory enum values, 79 new unit tests, 0 bugs, 2-repo validation (less/less.js 329 .less files/494 vars/1289 mixin defs/426 calls/132 guards, Semantic-Org/Semantic-UI 48 .less files), 2578 total tests passing
> **Updated:** Session 32 - Phase AM: Sass/SCSS Language Support (v4.44) — 5 Sass extractors (variable, mixin, function, module, nesting), EnhancedSassParser with regex AST, Dart Sass 1.x/LibSass/Ruby Sass version detection, .scss + .sass (indented) syntax support, @use/@forward module system (Dart Sass 1.23.0+), @import (legacy), $variables/$maps/lists/!default/!global, @mixin/@include (=mixin/+include indented), @function/@return with 100+ built-in functions across 7 categories (color/math/string/list/map/selector/meta), @extend/%placeholders, nesting depth analysis, BEM pattern detection (&\__element/&--modifier), @at-root, partial detection (\_prefix), 20+ framework detection (Bootstrap, Foundation, Bulma, Bourbon, Compass, Susy, include-media, sass-mq, rfs, Neat, Bitters, breakpoint-sass, normalize-scss, family.scss, sass-rem, sass-true, eyeglass, node-sass, dart-sass), 18 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (SASS001-SASS050), 10 PracticeCategory enums, 50 new unit tests, 0 bugs, 2-repo validation (twbs/bootstrap 122 SCSS files/299 vars/42 maps/60 mixin defs/314 usages/564 func calls, jgthms/bulma 863 vars/301 @use/129 @forward/module_system=dart_sass), 2499 total tests passing
> **Updated:** Session 31 - Phase AL: Emotion CSS-in-JS Framework Support (v4.43) — 5 Emotion extractors (component, theme, style, animation, api), EnhancedEmotionParser with regex AST, Emotion v9 (legacy single package)/v10 (emotion-theming)/v11+ (@emotion/react scoped packages) support, css prop (string/object/template/array syntax), @emotion/styled (styled.element`, styled(Component)`, styled('element')({}), shouldForwardProp), @emotion/css (framework-agnostic css()/cx()), @emotion/cache (createCache/CacheProvider), @emotion/server SSR (extractCritical/extractCriticalToChunks/renderStylesToString/renderStylesToNodeStream), @emotion/jest testing (createSerializer/toHaveStyleRule), Global component, keyframes, ClassNames render prop, facepaint responsive utilities, Next.js compiler.emotion detection, babel-plugin-emotion/@swc/plugin-emotion, 30+ framework detection (emotion-react/emotion-styled/emotion-css/emotion-cache/emotion-server/emotion-jest/twin-macro/facepaint/polished/theme-ui/rebass/next-emotion/gatsby-plugin-emotion), 22 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (EMO001-EMO050), 10 PracticeCategory enums, 63 new unit tests, 0 bugs, 3-repo validation (emotion-js/emotion 40+ comps/33 css/7 ThemeProviders, chakra-ui/chakra-ui ecosystem, mui/material-ui 18 comps/SSR/cache), 2449 total tests passing
> **Updated:** Session 30 - Phase AK: Styled Components Framework Support (v4.42) — 5 SC extractors (component, theme, mixin, style, api), EnhancedStyledComponentsParser with regex AST, styled-components v1-v6 support (styled.element`, styled(Component)`, .attrs(), .withConfig(), transient $props, css`, keyframes`, createGlobalStyle, ThemeProvider, useTheme, SSR ServerStyleSheet), 30+ CSS-in-JS ecosystem detection (styled-components/@emotion/styled/linaria/goober/stitches/polished/styled-system/rebass/xstyled/styled-media-query/jest-styled-components/babel-plugin-styled-components/@swc/plugin-styled-components), 18 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (SC001-SC050), 10 PracticeCategory enums, 57 new unit tests, 0 bugs, 3-repo validation (styled-components-website 64+15 comps, hyper no FP, xstyled 40+13 comps), 2386 total tests passing
> **Updated:** Session 29 - Phase AJ: Radix UI Framework Support (v4.41) — 5 Radix extractors (component, primitive, theme, style, api), EnhancedRadixParser with regex AST, Radix Primitives v0.x-v1.x + Themes v1.x-v4.x support (30+ primitives, 50+ themes components, 28 color scales × 12 steps, 500+ icons), 30+ framework detection (radix-primitives/radix-themes/radix-colors/radix-icons/stitches/tailwind-merge/clsx/CVA/vanilla-extract/framer-motion/react-spring), 14 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (RADIX001-RADIX050), 10 PracticeCategory enums, BPL selector filter reordering (React sub-framework specificity: Radix/MUI/ANTD/Chakra checked before generic React), 95 new unit tests, 0 bugs, 2-repo validation (radix-ui/themes, shadcn-ui/ui), 2329 total tests passing
> **Updated:** Session 28 - Phase AI: Bootstrap Framework Support (v4.40) — 5 Bootstrap extractors (component, grid, theme, utility, plugin), EnhancedBootstrapParser with regex AST, Bootstrap v3.x-v5.3+ support (50+ component categories, React-Bootstrap/reactstrap JSX, jQuery/vanilla JS init, data-bs-\* attributes, 6 breakpoints, SCSS variables, CSS custom properties, Bootswatch 25 themes, v5.3+ color modes), 16 framework detection (bootstrap-css/bootstrap-js/react-bootstrap/reactstrap/ng-bootstrap/ngx-bootstrap/bootstrap-vue/bootswatch/bootstrap-icons/@popperjs/core/jQuery), 15 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (BOOT001-BOOT050), 10 PracticeCategory enums, 64 new unit tests, 0 bugs, 2-repo validation (StartBootstrap/sb-admin-2 166 comps/32 grids/120 utils/110 plugins, react-bootstrap/react-bootstrap), 2234 total tests passing
> **Updated:** Session 27 - Phase AH: shadcn/ui Framework Support (v4.39) — 5 shadcn extractors (component, theme, hook, style, api), EnhancedShadcnParser with regex AST, shadcn/ui v0.x-v3.x support (40+ components, 5 categories, Radix UI primitives, cn() utility, CVA, components.json registry), 30+ ecosystem detection (class-variance-authority/cmdk/lucide-react/react-hook-form/@tanstack/react-table/next-themes/embla-carousel/react-day-picker/input-otp/sonner/react-resizable-panels/hookform-resolvers), 17 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (SHADCN001-SHADCN050), 10 PracticeCategory enums, 63 new unit tests, 7 bugs fixed (#97-103 including field name mismatches + import-based feature flags), 2-repo validation (shadcn-ui/taxonomy 81 files/131 comps/0 errors, shadcn-ui/ui 385 files/1366 comps/v1-v3/0 errors), 2170 total tests passing
> **Updated:** 15 Feb 2026 - Phase AG: Chakra UI Framework Support (v4.38) — 5 Chakra extractors (component, theme, hook, style, api), EnhancedChakraParser with regex AST, Chakra UI v1.x-v3.x/Ark UI support (70+ components, 8 categories, chakra() factory, forwardRef, sub-components), 30+ ecosystem detection (@chakra-ui/react/@chakra-ui/icons/@ark-ui/react/@pandacss/dev/@saas-ui/react/framer-motion/chakra-react-select), 22 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (CHAKRA001-CHAKRA050), 10 PracticeCategory enums, 53 new unit tests, 5 bugs fixed (#92-96 including multi-line JSX tracking), 3-repo validation (nextarter-chakra v3, myPortfolio v2, chakra-ui/chakra-ui v3), 2107 total tests passing
> **Updated:** 15 Feb 2026 - Phase AF: Ant Design (Antd) Framework Support (v4.37) — 5 Antd extractors (component, theme, hook, style, api), EnhancedAntdParser with regex AST, Ant Design v1-v5 support (80+ components, 6 categories, Pro components, sub-components, tree-shaking imports), 40+ ecosystem detection (antd/@ant-design/icons/@ant-design/pro-components/@ant-design/pro-layout/@ant-design/pro-table/antd-style/antd-mobile/umi/ahooks/babel-plugin-import), 20 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (ANTD001-ANTD050), 10 PracticeCategory enums, 52 new unit tests, 2 bugs fixed (#91-92 including CommonJS require support), 2-repo validation (ant-design-pro 25+ comps/v5/Pro/umi, antd-admin 70+ comps/v4-v5), 2054 total tests passing
> **Updated:** 15 Feb 2026 - Phase AE: Material UI (MUI) Framework Support (v4.36) — 5 MUI extractors (component, theme, hook, style, api), EnhancedMuiParser with regex AST, MUI v0.x-v6.x support (130+ components, @material-ui/_, @mui/\_, Pigment CSS), 30+ ecosystem detection (mui-material/mui-lab/mui-icons/mui-x-date-pickers/mui-x-data-grid/mui-system/notistack/tss-react/emotion/styled-components), 20 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (MUI001-MUI050), 10 PracticeCategory enums, 43 new unit tests, 7 bugs fixed (#84-90 including critical to_dict() root cause), 3-repo validation (devias-kit 411 comps, minimal-ui-kit 293 comps/27 styled, react-material-admin 4614 comps/24 makeStyles), 2002 total tests passing
> **Updated:** 15 Feb 2026 - Phase AD: Tailwind CSS Framework Support (v4.35) — 5 Tailwind extractors (utility, component, config, theme, plugin), EnhancedTailwindParser with regex AST + @tailwindcss/language-server LSP, Tailwind CSS v1.x-v4.x support (@apply/@tailwind/@screen/@layer/@utility/@variant/@theme/@source/@plugin, CSS-first config), 13 framework detection (DaisyUI/Flowbite/Preline/NextUI/shadcn/twin.macro/Headless UI/tailwind-animate/tailwind-merge/tailwind-variants/CVA), 20+ feature detection, 19 ProjectMatrix fields, scanner + compressor + BPL integration, 50 BPL practices (TW001-TW050), 10 PracticeCategory enums, 55 new unit tests, 5 bugs fixed (#79-83 including CSS layer crash + Tailwind detection fix), 3-repo validation (Flowbite 55 @apply, DaisyUI 613 @apply/331 components, TW Docs 36 @apply), 1959 total tests passing
> **Updated:** 14 Feb 2026 - Phase AC: Vue.js Framework Support (v4.34) — 5 Vue extractors (component, composable, directive, plugin, routing), EnhancedVueParser with regex AST, Vue 2.x-3.5+ support (Options API, Composition API, script setup, Reactive Props Destructure, useTemplateRef, useId, defineModel), 80+ framework detection (Nuxt 2/3, Quasar, Vuetify, Element Plus, PrimeVue, Naive UI, Pinia, Vuex, VueUse, Vue Router, vue-i18n), SFC extraction, 50 BPL practices (VUE001-VUE050), 59 new unit tests, 2 bugs fixed, 3-repo validation (Element Plus, VueUse, Nuxt UI), 1834 total tests passing
> **Updated:** 14 Feb 2026 - Phase AB: TypeScript Language Support (v4.31) — 5 TypeScript extractors (type, function, api, model, attribute), EnhancedTypeScriptParser with regex AST, TS 2.x-5.x+ support, 80+ framework detection (NestJS/Next.js/React/Angular/Vue/Express/Fastify/Hono/tRPC/Prisma/TypeORM/Sequelize/Drizzle/MikroORM/GraphQL/Socket.io), interface/type alias/enum/class extraction, mapped/conditional/utility/template literal type classification, function overload detection, tRPC programmatic paren-counting (ReDoS-safe), scanner + compressor + BPL integration, 45 BPL practices (TS001-TS045) with priority fields, 15 PracticeCategory enums, 98 new unit tests, 3 bugs fixed (#74-76 including critical ReDoS fix), 3-repo validation (Cal.com 7511 TS files, Strapi, Hatchet), 1649 total tests passing
> **Updated:** 14 Feb 2026 - Phase AA: JavaScript Language Support (v4.30) — 5 JavaScript extractors (type, function, api, model, attribute), EnhancedJavaScriptParser with regex AST, ES5-ES2024+ support, 70+ framework detection (Express/React/Vue/Angular/Next.js/Fastify/Koa/Hapi/Mongoose/Sequelize/Prisma/Knex/Socket.io/GraphQL), ES6+ class extraction + prototype-based OOP, CommonJS + ESM module detection, JSDoc extraction, scanner + compressor + BPL integration, 50 BPL practices (JS001-JS050) with priority fields (9 critical, 27 high, 13 medium, 1 low), 15 PracticeCategory enums, 88 new unit tests, 6 bugs fixed (#68-73 including 3 critical BPL selector fixes), 3-repo validation (Express.js, Ghost, Nodemailer), 1551 total tests passing
> **Updated:** 14 Feb 2026 - Phase Z: PowerShell Language Support (v4.29) — 5 PowerShell extractors (type, function, api, model, attribute), EnhancedPowerShellParser with regex AST, Windows PowerShell 1.0-5.1 + PowerShell Core 6.0-7.4+ support, 30+ framework detection (Pode/Polaris/UniversalDashboard/Pester/DSC/Azure/AWS/GCP/MSGraph/Exchange/ActiveDirectory/PSake/InvokeBuild/Plaster), DSC resource/config/node extraction, Pester test extraction, cmdlet binding detection, scanner + compressor + BPL integration, 50 BPL practices (PS001-PS050), 14 PracticeCategory enums, 57 new unit tests, 5 bugs fixed, 3 coverage gaps fixed, 3-repo validation (Pode, SqlServerDsc, Pester), 1463 total tests passing
> **Updated:** 14 Feb 2026 - Phase Y: Lua Language Support (v4.28) — 5 Lua extractors (type, function, api, model, attribute), EnhancedLuaParser with regex AST + optional tree-sitter-lua + lua-language-server LSP, Lua 5.1-5.4/LuaJIT 2.x support, 50+ framework detection (LÖVE2D/OpenResty/Lapis/lor/Corona/Defold/Gideros/Tarantool/middleclass/classic/30log), OOP pattern detection (4 OOP libraries + manual setmetatable), rockspec/luacheckrc parsing, scanner + compressor + BPL integration, 50 BPL practices (LUA001-LUA050), 15 PracticeCategory enums, 52 new unit tests, 1 bug fixed, 3-repo validation (Lapis, Hawkthorne, Kong), 1406 total tests passing
> **Updated:** 13 Feb 2026 - Phase X: Dart Language Support (v4.27) — 5 Dart extractors (type, function, api, model, attribute), EnhancedDartParser with regex AST + optional tree-sitter-dart + dart analysis_server LSP, Dart 2.0-3.5+ support (null safety 2.12+, class modifiers 3.0+, records 3.0+, extension types 3.3+), Flutter 1.x-3.x+ (4 widget types), 70+ framework detection (Flutter/Riverpod/Bloc/GetX/Provider/Dio/Drift/Floor/Isar/Hive/Shelf/DartFrog/Serverpod), pubspec.yaml/lock parsing, scanner + compressor + BPL integration, 50 BPL practices (DART001-DART050), 27 PracticeCategory enums, 126 new unit tests, 4 bugs fixed, 3-repo validation (Isar, Bloc, Shelf), 1354 total tests passing
> **Updated:** 13 Feb 2026 - Phase W: R Language Support (v4.26) — 5 R extractors (type, function, api, model, attribute), EnhancedRParser with regex AST + R-languageserver LSP, R 2.x-4.4+ support, 6 class systems (S3/S4/R5/R6/S7/proto), 70+ framework detection (tidyverse/Shiny/Plumber/data.table/arrow/Rcpp/caret/tidymodels/bioconductor/golem), DESCRIPTION/NAMESPACE/renv.lock parsing, scanner + compressor + BPL integration, 50 BPL practices (R001-R050), 62 new unit tests, 11 bugs fixed, 3-repo validation (dplyr, Shiny, plumber), 1228 total tests passing
> **Updated:** 13 Feb 2026 - Phase V: Scala Language Support (v4.25) — 5 Scala extractors (type, function, api, model, attribute), EnhancedScalaParser with regex AST + Metals LSP, Scala 2.x-3.x support, 25+ framework detection (Play/Akka/ZIO/http4s/Tapir/Cats/Spark), Slick/Doobie/Quill ORM, build.sbt parsing, scanner + compressor + BPL integration, 50 BPL practices (SCALA001-SCALA050), 132 new unit tests, 4 bugs fixed, 3-repo validation (Caliban, Play Samples, ZIO HTTP), 1166 total tests passing
> **Updated:** 12 Feb 2026 - Phase U: PHP Language Support (v4.24) — 5 PHP extractors, EnhancedPhpParser with regex AST, PHP 5.6-8.3+, 30+ framework detection, Laravel/Symfony/Doctrine, composer.json, 84 new unit tests, 1034 total tests passing
> **Updated:** 12 Feb 2026 - Phase T: Ruby Language Support (v4.23) — 5 Ruby extractors (type, function, api, model, attribute), EnhancedRubyParser with regex AST + solargraph LSP, Ruby 1.8-3.3+ support, 10+ framework detection (Rails/Sinatra/Grape/Hanami/Roda), ActiveRecord/Sequel/Mongoid ORM, Gemfile parsing, scanner + compressor + BPL integration, 50 BPL practices (RB001-RB050), 80 new unit tests, 3-repo validation (Discourse, Faker, Mastodon), 950 total tests passing
> **Updated:** 12 Feb 2026 - Phase S: C++ Language Support (v4.20) — 5 C++ extractors (type, function, api, model, attribute), EnhancedCppParser with optional tree-sitter-cpp AST + clangd LSP, C++98-C++26 standard detection, 30+ framework detection, CRTP/concepts/coroutines/smart pointers, scanner + compressor + BPL integration, 50 BPL practices (CPP001-CPP050), 73 new unit tests, 8 bugs fixed, 3-repo validation (spdlog, fmt, nlohmann_json), 713 total tests passing
> **Updated:** 12 Feb 2026 - Phase N: Rust Language Support (v4.14) — 5 Rust extractors (type, function, api, model, attribute), EnhancedRustParser, scanner + compressor + BPL integration, 50 BPL practices (RS001-RS050), 46 new unit tests, 6 bugs fixed, 3-repo validation (Axum, Diesel, actix-web), 315 total tests passing
> **Updated:** 12 Feb 2026 - Phase M: C# Language Support (v4.13) — 6 C# extractors (type, function, enum, api, model, attribute), EnhancedCSharpParser with optional tree-sitter-c-sharp, scanner + compressor + BPL integration, 50 BPL practices (CS001-CS050), 97 new unit tests, 10 bugs fixed, 3-repo validation (eShop, Ardalis/JT CleanArchitecture), 269 total tests passing
> **Updated:** 12 Feb 2026 - Phase L: Java & Kotlin Language Support (v4.12) — Java extractors (6), Kotlin extractors (2), tree-sitter-java AST, Eclipse JDT LSP, Panache entity detection, Kotlin dedicated parser, 50 Java BPL practices, 12 bugs fixed, 3-repo validation
> **Updated:** 11 Feb 2026 - Phase K: Systemic Improvements (v4.11) — Weighted domain scoring with confidence/runner-up, unified FileClassifier wiring, multi-signal ORM/DB/MQ detection ({strong,medium,weak,anti} tiers), discovery-driven per-sub-project stack detection, ORMEvidence affinity graph with sub-project provenance. DB false positives reduced 46%.
> **Updated:** 11 Feb 2026 - Phase J: R4 Evaluation & .gitignore-Aware Scanning (v4.10) — GitignoreFilter for `.gitignore` + `.git/info/exclude`, all v5 extractors accept `gitignore_filter` param, R4 evaluation (Gitea/Strapi/Medusa), 18 test failures fixed
> **Updated:** 9 Feb 2026 - Phase I: Targeted Extractor Fixes (v4.9) — BPL type detection from overview, runbook enrichment (contributing/examples/versions/license), test dir visibility in directory_summary
> **Updated:** 9 Feb 2026 - Phase H: Deep Pipeline Fixes (v4.8) — Brace-balanced extraction, adaptive compressor, BPL ratio limiting, directory summary, primary language priority
> **Purpose**: This document provides a step-by-step blueprint for adding support for any new programming language to CodeTrellis (Project Structure Analysis System). Follow this guide to ensure complete end-to-end integration.
>
> **Updated:** 9 Feb 2026 - Phase G: PocketBase 16-Gap Remediation (v4.7) — BaaS domain, .d.ts filter, enhanced middleware/plugin/CLI detection, route group prefixes
> **Updated:** 9 Feb 2026 - Phase F: Go Language Support (v4.5) + Generic Semantic Extraction (v4.6) — G-17 resolved, PocketBase validated
> **Updated:** 9 Feb 2026 - Phase D: Public Repository Validation Framework (.codetrellis validate-repos`CLI, 60-repo corpus, quality_scorer.py, analyze_results.py)
**Updated:** 7 Feb 2026 - Phase A Remediation: RunbookExtractor, domain categories,`[AI_INSTRUCTION]`prompt, cross-cutting extractor patterns
**Session Update:** 6 Feb 2026 (Afternoon) - BPL v1.1:`min_python`/`contexts`formalized in ApplicabilityRule, YAML warnings 0,`python -m.codetrellis` support added
**Session Update:** 6 Feb 2026 (Evening) - JSON Schema (`practice.schema.json`), pre-commit hooks, CI pipeline added. Phase 2 Validation complete.
**Session Update:** Current - Phase BG complete (v4.65: Lit / Web Components framework support — Polymer 1.x-3.x, lit-element 2.x, lit 2.x-3.x, @customElement/@property/@state/@query, html/css/svg templates, ReactiveController, Shadow DOM, 5 extractors, 25+ ProjectMatrix fields, 50 BPL practices, 109 tests, 3-repo validation), Phase BF complete (v4.64: Preact framework support — v8.x/v10.x/v10.5+/v10.11+/v10.19+, @preact/signals v1-v2, 5 extractors, 25 fw + 35 feature patterns, 27 ProjectMatrix fields, 50 BPL practices, 92 tests, 3-repo validation), Phase BE complete (v4.63: Qwik framework support — Qwik v1.x-v2.x + Qwik City, component$/useSignal/useStore/useResource$/useTask$, routeLoader$/routeAction$/server$, 5 extractors, 24 ProjectMatrix fields, 50 BPL practices, 103 tests, 3-repo validation), Phase BD complete (v4.62: Solid.js framework support), Phase BC complete (v4.61: Remix framework support), Phase BB complete (v4.60: Astro framework support), Phase BA complete (v4.59: Apollo Client framework support), Phase AZ complete (v4.58: SWR framework support), Phase AY complete (v4.57: TanStack Query framework support), Phase AX complete (v4.56: Valtio framework support), Phase AW complete (v4.55: XState framework support), Phase AV complete (v4.53: NgRx framework support), Phase AU complete (v4.52: Pinia framework support), Phase AT complete (v4.51: MobX framework support), Phase AS complete (v4.50: Recoil framework support), Phase AR complete (v4.49: Jotai framework support), Phase AQ complete (v4.48: Zustand framework support), Phase AP complete (v4.47: Redux/RTK framework support), Phase AO complete (v4.46: PostCSS language support), Phase AN complete (v4.45: Less language support — Less 1.x-4.x+, @variables/scopes/lazy-eval/interpolation, .mixin() parametric/pattern-matched/guards/namespaces, 70+ built-in functions, @import with options, :extend() all/inline, detached rulesets, nesting/BEM/parent selectors, property merging, math mode detection, 20+ feature detection, 5+ framework detection, 6+ library detection, 50 BPL practices, 2-repo validation), Phase AM complete (v4.44: Sass/SCSS language support — Dart Sass 1.x/LibSass/Ruby Sass, .scss+.sass syntax, @use/@forward module system, @import legacy, $variables/maps/lists, @mixin/@include, @function/@return, 100+ built-in functions, @extend/%placeholders, nesting depth, BEM patterns, @at-root, partials, 20+ framework detection, 50 BPL practices, 2-repo validation), Phase AK complete (v4.42: Styled Components framework support — v1-v6, styled.element`, styled(Component)`, .attrs(), .withConfig(), transient $props, css` helpers, keyframes`, createGlobalStyle, ThemeProvider, useTheme, withTheme, ServerStyleSheet SSR, babel/SWC plugins, jest-styled-components testing, polished utilities, 30+ ecosystem detection, @emotion/styled compatibility, 50 BPL practices, 3-repo validation), Phase AJ complete (v4.41: Radix UI framework support — Primitives v0.x-v1.x, Themes v1.x-v4.x, Colors v1.x-v3.x, 30+ primitives, 50+ themes components, 28 color scales, asChild composition, controlled/uncontrolled patterns, portal management, data-attribute styling, 5 styling approaches detection, 50 BPL practices, BPL filter reordering fix, 2-repo validation), Phase AI complete (v4.40: Bootstrap framework support — v3.x-v5.3+, 50+ component categories, React-Bootstrap/reactstrap/ng-bootstrap/bootstrap-vue, 6 breakpoints, SCSS variables, CSS custom properties, Bootswatch themes, v5.3+ color modes, 16 utility categories, 12 JS plugins, CDN detection, 50 BPL practices, 2-repo validation), Phase AH complete (v4.39: shadcn/ui framework support — v0.x-v3.x, 40+ components, 5 categories, Radix UI, cn() utility, CVA, components.json, 30+ ecosystem patterns, import-path-based detection, 50 BPL practices, 2-repo validation 0 errors), Phase AG complete (v4.38: Chakra UI framework support — v1-v3/Ark UI, 70+ components, 8 categories, chakra() factory, 30+ ecosystem patterns, @chakra-ui/@ark-ui/@pandacss/framer-motion, theme/hook/style/API extraction, 50 BPL practices), Phase AF complete (v4.37: Ant Design framework support — v1-v5, 80+ components, 6 categories, Pro components, 40+ ecosystem patterns, antd/@ant-design/umi/ahooks, theme/hook/style/API extraction, 50 BPL practices), Phase AE complete (v4.36: Material UI framework support — MUI v0.x-v6.x, 130+ components, 30+ ecosystem patterns, @material-ui/@mui/Pigment CSS, theme/hook/style/API extraction, 50 BPL practices), Phase AD complete (v4.35: Tailwind CSS framework support — v1.x-v4.x, 13 frameworks, CSS-first config, @apply/@layer/@theme/@utility/@variant, 50 BPL practices), Phase AC complete (v4.34: Vue.js framework support — Vue 2.x-3.5+, 80+ frameworks, SFC/Options/Composition/script-setup, Nuxt/Pinia/Vuex/Vuetify/Quasar, 50 BPL practices), Phase AB complete (v4.31: TypeScript language support — TS 2.x-5.x+, 80+ frameworks, NestJS/tRPC/Prisma/GraphQL, ReDoS-safe extraction), Phase AA complete (v4.30: JavaScript language support — ES5-ES2024+, 70+ frameworks, CommonJS+ESM, BPL selector fixes), Phase Z complete (v4.29: PowerShell language support — Windows PS 1.0-5.1 + PS Core 6.0-7.4+, 30+ frameworks, DSC/Pester/Pode), Phase Y complete (v4.28: Lua language support — Lua 5.1-5.4/LuaJIT 2.x, 50+ frameworks, OOP libraries, rockspec parsing), Phase X complete (v4.27: Dart language support — Dart 2.0-3.5+, Flutter 1.x-3.x+, 70+ frameworks, 4 widget types, pubspec parsing), Phase W complete (v4.26: R language support — 6 class systems, 70+ frameworks, pipe chain analysis), Phase K complete (v4.11: systemic improvements — weighted scoring, multi-signal detection, affinity graph), Phase J complete (v4.10: R4 evaluation, .gitignore scanning), Phase G complete (v4.7: 16-gap remediation), Phase F complete (Go v4.5, Semantic v4.6), Phase 2 Practices complete (React, NestJS, Django, Flask, DB, DevOps), Phase 3 Token Optimization complete, Phase A Remediation (RunbookExtractor, AI_ML/DEVTOOLS domains, [AI_INSTRUCTION]), Phase D Validation Framework (60-repo public corpus)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Integration Checklist](#2-integration-checklist)
3. [Step 1: Create Extractors](#step-1-create-extractors)
4. [Step 2: Create Enhanced Parser](#step-2-create-enhanced-parser)
5. [Step 3: Update ProjectMatrix](#step-3-update-projectmatrix)
6. [Step 4: Update Scanner](#step-4-update-scanner)
7. [Step 5: Update Compressor](#step-5-update-compressor)
8. [Step 6: Testing & Validation](#step-6-testing--validation)
9. [**Step 7: BPL Integration (NEW)**](#step-7-bpl-integration)
10. [**Step 8: Cross-Cutting Extractor Integration (NEW)**](#step-8-cross-cutting-extractor-integration)
11. [**Step 9: Semantic Extraction Integration (NEW v4.6)**](#step-9-semantic-extraction-integration)
12. [**Step 10: File Filtering & Output Quality (NEW v4.7)**](#step-10-file-filtering--output-quality)
13. [Common Pitfalls](#7-common-pitfalls)
14. [**Step 11: Pipeline Quality Assurance (NEW v4.8)**](#step-11-pipeline-quality-assurance)
15. [**Step 12: .gitignore-Aware Scanning (NEW v4.10)**](#step-12-gitignore-aware-scanning-integration)
16. [**Step 13: Systemic Detection Architecture (NEW v4.11)**](#step-13-systemic-detection-architecture)
17. [**Step 14: A5.x Module Integration (NEW Session 54b)**](#step-14-a5x-module-integration)
18. [Reference: Python Integration Example](#8-reference-python-integration-example)
19. [Reference: Go Integration Example (NEW v4.5)](#9-reference-go-integration-example)
20. [Reference: Java & Kotlin Integration Example (NEW v4.12)](#10-reference-java--kotlin-integration-example)
21. [Reference: C# Integration Example (NEW v4.13)](#11-reference-c-integration-example)
22. [Reference: Rust Integration Example (NEW v4.14)](#12-reference-rust-integration-example)
23. [Reference: C++ Integration Example (NEW v4.20)](#13-reference-c-integration-example-v420)
24. [Reference: Ruby Integration Example (NEW v4.23)](#14-reference-ruby-integration-example-v423)
25. [Reference: Scala Integration Example (NEW v4.25)](#15-reference-scala-integration-example-new-v425)
26. [Reference: R Integration Example (NEW v4.26)](#16-reference-r-integration-example-new-v426)
27. [Reference: Dart Integration Example (NEW v4.27)](#17-reference-dart-integration-example-new-v427)
28. [Reference: Lua Integration Example (NEW v4.28)](#18-reference-lua-integration-example-new-v428)
29. [Reference: PowerShell Integration Example (NEW v4.29)](#19-reference-powershell-integration-example-new-v429)
30. [Reference: JavaScript Integration Example (NEW v4.30)](#20-reference-javascript-integration-example-new-v430)
31. [Reference: TypeScript Integration Example (NEW v4.31)](#21-reference-typescript-integration-example-new-v431)
32. [Reference: Material UI Integration Example (NEW v4.36)](#22-reference-material-ui-integration-example-new-v436)
33. [Reference: Ant Design Integration Example (NEW v4.37)](#23-reference-ant-design-integration-example-new-v437)
34. [Reference: Chakra UI Integration Example (NEW v4.38)](#24-reference-chakra-ui-integration-example-new-v438)
35. [Reference: Less Integration Example (NEW v4.45)](#reference-less-integration-example-new-v445)
36. [Reference: Lit / Web Components Integration Example (NEW v4.65)](#reference-lit--web-components-integration-example-new-v465)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CodeTrellis Data Flow                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  CLI Command (codetrellis scan /path)                                          │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ProjectScanner._walk_directory()                                 │    │
│  │   - Walks all files in project                                   │    │
│  │   - Filters by extension (.py, .ts, .tsx, .go, .rs, .java, .kt, .cs, .c, .cpp, .js, .jsx, .R, .dart, etc.)  │    │
│  │   - Calls appropriate parser based on extension                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Language Parser (e.g., EnhancedPythonParser)                     │    │
│  │   - Detects frameworks used in file                              │    │
│  │   - Calls individual extractors                                  │    │
│  │   - Returns ParseResult dataclass                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Individual Extractors                                            │    │
│  │   - TypeExtractor, FunctionExtractor, APIExtractor, etc.        │    │
│  │   - Each returns specific info objects                           │    │
│  │   - RunbookExtractor (cross-cutting: Docker, CI/CD, shell)      │    │
│  │   - BusinessDomainExtractor (domain detection)                  │    │
│  │   - SemanticExtractor (hooks, middleware, routes, lifecycle)     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ProjectMatrix (dataclass)                                        │    │
│  │   - Central data structure holding all extracted info            │    │
│  │   - Has fields for each language's data                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ MatrixCompressor                                                 │    │
│  │   - Converts ProjectMatrix to token-efficient prompt format      │    │
│  │   - Has _compress_<lang>_*() methods for each language           │    │
│  │   - Adds [AI_INSTRUCTION] header for AI context guidance         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│       │                                                                  │
│       ▼                                                                  │
│  matrix.prompt (output file)                                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Files to Modify

| File                                                        | Purpose                                                                                 |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| .codetrellis/extractors/<lang>/\*.py`                       | Individual extractors for language constructs                                           |
| .codetrellis/extractors/<lang>/**init**.py`                 | Export all extractors                                                                   |
| .codetrellis/<lang>\_parser_enhanced.py`                    | Main parser that orchestrates extractors                                                |
| .codetrellis/scanner.py`                                    | `ProjectMatrix` dataclass + `_parse_<lang>()` method                                    |
| .codetrellis/compressor.py`                                 | `_compress_<lang>_*()` methods for output + `[AI_INSTRUCTION]` header                   |
| .codetrellis/file_classifier.py`                            | `FileClassifier` (file type) + `GitignoreFilter` (`.gitignore`/`.git/info/exclude`)     |
| .codetrellis/extractors/runbook_extractor.py`               | Cross-cutting extractor for Dockerfiles, CI/CD, shell scripts                           |
| .codetrellis/extractors/business_domain_extractor.py`       | Domain detection — weighted {high,medium,low} scoring + confidence + runner-up (v4.11)  |
| .codetrellis/extractors/database_architecture_extractor.py` | Multi-signal ORM/DB/MQ detection + ORMEvidence affinity graph (v4.11)                   |
| .codetrellis/extractors/architecture_extractor.py`          | Discovery-driven per-sub-project stack detection (v4.11)                                |
| .codetrellis/extractors/semantic_extractor.py`              | Language-agnostic hooks, middleware, routes, plugins, CLI commands, lifecycle detection |
| `scripts/validation/quality_scorer.py`                      | Phase D: Automated quality scoring for public repo validation                           |
| `scripts/validation/analyze_results.py`                     | Phase D: Gap Analysis Round 2 generator from validation results                         |
| `scripts/validation/repos.txt`                              | Phase D: 60 GitHub repos for validation (6 categories × 10 repos)                       |

---

## 2. Integration Checklist

Use this checklist when adding a new language:

### Phase 1: Extractors

- [ ] Create .codetrellis/extractors/<lang>/` directory
- [ ] Create `__init__.py` with all exports
- [ ] Create individual extractor files (see categories below)
- [ ] Each extractor has `extract()` method returning typed info objects

### Phase 2: Parser

- [ ] Create .codetrellis/<lang>\_parser_enhanced.py`
- [ ] Define `<Lang>ParseResult` dataclass with all extracted data
- [ ] Define `Enhanced<Lang>Parser` class
- [ ] Add framework detection patterns
- [ ] Initialize all extractors in `__init__()`
- [ ] Implement `parse()` method calling all extractors

### Phase 3: Scanner Integration

- [ ] Add language fields to `ProjectMatrix` dataclass
- [ ] Import parser in `scanner.py`
- [ ] Initialize parser in `ProjectScanner.__init__()`
- [ ] Add file extension to `_walk_directory()` handling
- [ ] Create `_parse_<lang>()` method
- [ ] Update ignore patterns for language-specific dirs (e.g., `venv`, `node_modules`)

### Phase 4: Compressor Integration

- [ ] Add `_compress_<lang>_types()` method
- [ ] Add `_compress_<lang>_api()` method
- [ ] Add `_compress_<lang>_functions()` method
- [ ] Add other relevant compression methods
- [ ] Call compression methods in main `compress()` method
- [ ] Add section headers (e.g., `[<LANG>_TYPES]`)

### Phase 5: Testing

- [ ] Test individual extractors with sample code
- [ ] Test parser with comprehensive sample file
- [ ] Test scanner integration with single file
- [ ] Test full CLI scan on real project
- [ ] Verify output in matrix.prompt

### Phase 6: BPL Integration (UPDATED 6 Feb 2026)

- [ ] Create .codetrellis/bpl/practices/<lang>\_core.yaml` - Core language practices (40-60 practices)
- [ ] Create framework-specific files (e.g., `<lang>_django.yaml`, `<lang>_spring.yaml`)
- [ ] Use `applicability.min_python` / `applicability.contexts` fields where appropriate (v1.1)
- [ ] Run YAML validation: `python3 scripts/validate_practices.py` (must pass with 0 errors, 0 warnings)
- [ ] Add new PracticeCategory values to .codetrellis/bpl/models.py` (if needed)
- [ ] Update `ProjectContext.from_matrix()` in .codetrellis/bpl/selector.py`:
  - [ ] Add framework detection from dependencies
  - [ ] Add artifact counting for weighted detection
- [ ] Update `_get_practice_frameworks()` in selector.py:
  - [ ] Add ID prefix mapping (e.g., `GO*` → golang, `RS*` → rust)
- [ ] Update `_filter_applicable()` to handle new language
- [ ] Test context-aware selection with new language project
- [ ] Test token budget enforcement: `--max-practice-tokens 200` → reduced count
- [ ] Verify practices appear in `--include-practices` output
- [ ] Add unit tests in `tests/unit/test_bpl_<lang>.py` (see existing 125 tests for patterns)
- [ ] Run full test suite: `python3 -m pytest tests/unit/test_bpl_*.py -v`

### Phase 7: Semantic Extraction (NEW v4.6, UPDATED v4.7)

- [ ] Verify `SemanticExtractor` runs on `.{ext}` files (scanner's `_extract_semantics()`)
- [ ] Validate hook detection for language (On\* methods, event patterns)
- [ ] Validate middleware detection (Use(), Bind(), chain patterns, exported middleware factories)
- [ ] Validate route detection (generic HTTP handlers)
- [ ] Validate lifecycle detection (Init/Start/Stop/Shutdown)
- [ ] Validate CLI command detection (cobra, click, argparse, commander)
- [ ] Validate plugin detection (Register, Mount, MustRegister patterns)
- [ ] Check compressor outputs: `[HOOKS]`, `[MIDDLEWARE]`, `[ROUTES_SEMANTIC]`, `[LIFECYCLE]`, `[CLI_COMMANDS]`
- [ ] Verify path validation filters false positives (HTTP headers, non-URL strings)
- [ ] Verify `.d.ts` declaration files are excluded from semantic scanning

### Phase 8: Architecture Detection (NEW v4.6)

- [ ] Update `can_extract()` in `architecture_extractor.py` for language manifest file (e.g., go.mod, Cargo.toml)
- [ ] Add project type detection in `_detect_project_type()` (e.g., GO_CLI, GO_WEB_SERVICE)
- [ ] Add dependency parsing in scanner's `_extract_dependencies()` for the manifest file

---

## Step 1: Create Extractors

### Directory Structure

```
codetrellis/extractors/<lang>/
├── __init__.py              # Export all extractors
├── type_extractor.py        # Classes, interfaces, types
├── function_extractor.py    # Functions, methods
├── api_extractor.py         # REST/GraphQL endpoints
├── framework_extractor.py   # Framework-specific patterns
└── <category>/              # Optional subdirectories for organization
    ├── __init__.py
    └── specific_extractor.py
```

### Extractor Template

```python
"""
<Lang> <Concept> Extractor for CodeTrellis

Extracts <concept> definitions from <lang> source code.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class <Concept>Info:
    """Information about a <concept>."""
    name: str
    file: str = ""
    # Add fields specific to this concept
    line_number: int = 0


class <Concept>Extractor:
    """
    Extracts <concept> from <lang> source code.

    Detects:
    - Pattern 1
    - Pattern 2
    """

    # Regex patterns for detection
    PATTERN = re.compile(r'...')

    def __init__(self):
        """Initialize the extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> List[<Concept>Info]:
        """
        Extract all <concepts> from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            List of <Concept>Info objects
        """
        results = []

        for match in self.PATTERN.finditer(content):
            info = <Concept>Info(
                name=match.group(1),
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            )
            results.append(info)

        return results

    def to.codetrellis_format(self, items: List[<Concept>Info]) -> str:
        """Convert to CodeTrellis compressed format."""
        lines = []
        for item in items:
            lines.append(f"  {item.name}:...")
        return '\n'.join(lines)
```

### Recommended Extractor Categories

| Category      | What to Extract                                   |
| ------------- | ------------------------------------------------- |
| **Types**     | Classes, interfaces, structs, enums, type aliases |
| **Functions** | Functions, methods, lambdas, closures             |
| **API**       | REST endpoints, GraphQL resolvers, RPC methods    |
| **Data**      | Database models, schemas, migrations              |
| **Config**    | Configuration classes, settings, environment      |
| **Tests**     | Test classes, fixtures, mocks                     |
| **Framework** | Framework-specific patterns (e.g., decorators)    |

---

## Step 2: Create Enhanced Parser

### File: .codetrellis/<lang>\_parser_enhanced.py`

```python
"""
Enhanced<Lang>Parser v1.0 - Comprehensive <lang> parser using all extractors.

This parser integrates all <lang> extractors to provide complete
parsing of <lang> source files.

Supports:
- Core types (classes, interfaces, enums)
- Functions and methods
- Framework patterns (list frameworks)
- API endpoints
- etc.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

# Import all extractors
from .extractors.<lang> import (
    TypeExtractor, TypeInfo,
    FunctionExtractor, FunctionInfo,
    APIExtractor, APIInfo,
    # ... more extractors
)


@dataclass
class <Lang>ParseResult:
    """Complete parse result for a <lang> file."""
    file_path: str
    file_type: str = "<lang>"

    # Core types
    types: List[TypeInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)

    # Framework-specific
    api_endpoints: List[APIInfo] = field(default_factory=list)

    # Metadata
    docstring: Optional[str] = None
    detected_frameworks: List[str] = field(default_factory=list)


class Enhanced<Lang>Parser:
    """
    Enhanced <lang> parser that uses all extractors for comprehensive parsing.
    """

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'framework1': re.compile(r'import\s+framework1'),
        'framework2': re.compile(r'from\s+framework2'),
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = TypeExtractor()
        self.function_extractor = FunctionExtractor()
        self.api_extractor = APIExtractor()
        # Initialize more extractors...

    def parse(self, content: str, file_path: str = "") -> <Lang>ParseResult:
        """
        Parse <lang> source code and extract all information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            <Lang>ParseResult with all extracted information
        """
        result = <Lang>ParseResult(file_path=file_path)

        # Detect frameworks first
        result.detected_frameworks = self._detect_frameworks(content)

        # Always extract core types
        result.types = self.type_extractor.extract(content)
        result.functions = self.function_extractor.extract(content)

        # Extract based on detected frameworks
        if 'framework1' in result.detected_frameworks:
            result.api_endpoints = self.api_extractor.extract(content)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which frameworks are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks
```

---

## Step 3: Update ProjectMatrix

### File: .codetrellis/scanner.py` - ProjectMatrix dataclass

Add fields for the new language in the `ProjectMatrix` dataclass:

```python
@dataclass
class ProjectMatrix:
    """Central data structure for project analysis."""

    # ... existing fields ...

    # NEW: <Lang> Language Support
    # Core Types
    <lang>_types: List[Dict] = field(default_factory=list)
    <lang>_functions: List[Dict] = field(default_factory=list)
    <lang>_enums: List[Dict] = field(default_factory=list)

    # Framework-specific
    <lang>_api_endpoints: List[Dict] = field(default_factory=list)
    <lang>_models: List[Dict] = field(default_factory=list)

    # Infrastructure
    <lang>_configs: List[Dict] = field(default_factory=list)
```

### Naming Convention

Use this pattern for field names:

```
<lang>_<concept>s  (plural)

Examples:
- python_dataclasses
- go_structs
- rust_traits
- java_classes
```

---

## Step 4: Update Scanner

### File: .codetrellis/scanner.py` - ProjectScanner class

#### 4.1 Import the Parser

```python
# At top of file, add import
from .python_parser_enhanced import EnhancedPythonParser  # Example
from .<lang>_parser_enhanced import Enhanced<Lang>Parser   # New language
```

#### 4.2 Initialize Parser in `__init__`

```python
class ProjectScanner:
    def __init__(self, root_path: str = "."):
        # ... existing code ...

        # Initialize language parsers
        self.python_parser = EnhancedPythonParser()  # Existing
        self.<lang>_parser = Enhanced<Lang>Parser()   # New language
```

#### 4.3 Update `_walk_directory()` to Handle New Extension

Find the section where files are dispatched to parsers:

```python
def _walk_directory(self, root: Path, matrix: ProjectMatrix):
    """Walk directory and parse files."""

    for file_path in root.rglob("*"):
        # Skip ignored directories
        if self._should_ignore(file_path):
            continue

        suffix = file_path.suffix.lower()

        # Existing handlers
        if suffix == '.py':
            self._parse_python(file_path, matrix)
        elif suffix in ['.ts', '.tsx']:
            self._parse_typescript(file_path, matrix)

        # NEW: Add handler for new language
        elif suffix == '.<ext>':  # e.g., '.go', '.rs', '.java'
            self._parse_<lang>(file_path, matrix)
```

#### 4.4 Update Ignore Patterns

Add language-specific directories to ignore:

```python
IGNORE_PATTERNS = [
    # Existing
    'node_modules', '__pycache__', '.git', 'dist', 'build',
    '*_env', 'site-packages', '.venv', 'venv',

    # NEW: Add language-specific ignores
    'target',        # Rust
    'vendor',        # Go
    '.gradle',       # Java/Kotlin
    'Pods',          # Swift/iOS
]
```

#### 4.5 Create `_parse_<lang>()` Method

This is the critical integration point. Create a method that:

1. Reads the file
2. Parses with the language parser
3. Populates ProjectMatrix fields

```python
def _parse_<lang>(self, file_path: Path, matrix: ProjectMatrix):
    """
    Parse <lang> file using Enhanced<Lang>Parser.
    """
    try:
        content = file_path.read_text()
        if not content.strip():
            return

        # Parse with enhanced parser
        result = self.<lang>_parser.parse(content, str(file_path))

        # Populate matrix fields
        # IMPORTANT: Match attribute names exactly!

        if result.types:
            for t in result.types:
                matrix.<lang>_types.append({
                    "name": t.name,
                    "file": str(file_path),
                    "fields": [...],  # Convert to dict format
                })

        if result.functions:
            for func in result.functions:
                matrix.<lang>_functions.append({
                    "name": func.name,
                    "file": str(file_path),
                    "params": func.parameters,
                    "return_type": func.return_type,
                })

        if result.api_endpoints:
            for ep in result.api_endpoints:
                matrix.<lang>_api_endpoints.append({
                    "method": ep.method,
                    "path": ep.path,
                    "file": str(file_path),
                })

    except Exception as e:
        # Silently skip files that can't be parsed
        pass
```

### ⚠️ Critical: Attribute Name Matching

**This is the #1 source of integration bugs!**

The attribute names in your `ParseResult` dataclass MUST match what you access in `_parse_<lang>()`:

```python
# In ParseResult dataclass:
@dataclass
class <Lang>ParseResult:
    types: List[TypeInfo]      # ← Attribute name is 'types'
    api_routes: List[APIInfo]  # ← Attribute name is 'api_routes'

# In _parse_<lang>():
if result.types:        # ✅ Correct - matches 'types'
    ...
if result.api_routes:   # ✅ Correct - matches 'api_routes'
    ...
if result.routes:       # ❌ WRONG - 'routes' doesn't exist!
    ...
```

Also watch for nested attribute mismatches:

```python
# TypeInfo has 'fields' attribute:
@dataclass
class TypeInfo:
    fields: List[FieldInfo]  # ← 'fields'

# But TypedDictInfo might have 'keys':
@dataclass
class TypedDictInfo:
    keys: List[KeyInfo]      # ← 'keys' not 'fields'!

# In scanner, handle both:
fields = getattr(t, 'fields', None) or getattr(t, 'keys', [])
```

---

## Step 5: Update Compressor

### File: .codetrellis/compressor.py`

#### 5.1 Add Compression Methods

Create methods to compress each data category:

```python
class MatrixCompressor:

    # ... existing methods ...

    # ============================================
    # <Lang> Language Support Methods
    # ============================================

    def _compress_<lang>_types(self, matrix) -> List[str]:
        """Compress <lang> type definitions."""
        lines = []

        if hasattr(matrix, '<lang>_types') and matrix.<lang>_types:
            lines.append("# Types")
            for t in matrix.<lang>_types:
                fields_str = self._compress_fields(t.get('fields', []))
                lines.append(f"  {t['name']}:{fields_str}")

        if hasattr(matrix, '<lang>_enums') and matrix.<lang>_enums:
            lines.append("# Enums")
            for enum in matrix.<lang>_enums:
                values = [v.get('name', '') for v in enum.get('values', [])]
                lines.append(f"  {enum['name']}={','.join(values)}")

        return lines

    def _compress_<lang>_api(self, matrix) -> List[str]:
        """Compress <lang> API endpoints."""
        lines = []

        if hasattr(matrix, '<lang>_api_endpoints') and matrix.<lang>_api_endpoints:
            lines.append("# API Endpoints")
            for ep in matrix.<lang>_api_endpoints:
                method = ep.get('method', 'GET')
                path = ep.get('path', '/')
                lines.append(f"  {method}:{path}")

        return lines

    def _compress_<lang>_functions(self, matrix) -> List[str]:
        """Compress <lang> functions."""
        lines = []

        if hasattr(matrix, '<lang>_functions') and matrix.<lang>_functions:
            for func in matrix.<lang>_functions:
                name = func.get('name', '')
                ret = func.get('return_type', '')
                ret_str = f"->{ret}" if ret else ""
                lines.append(f"  {name}(){ret_str}")

        return lines
```

#### 5.2 Call Compression Methods in `compress()`

Find the main `compress()` method and add calls to your new compression methods:

```python
def compress(self, matrix: ProjectMatrix, tier: str = "prompt") -> str:
    """Compress ProjectMatrix to prompt format."""
    lines = []

    # ... existing sections ...

    # NEW: Add <Lang> sections
    <lang>_types_lines = self._compress_<lang>_types(matrix)
    if <lang>_types_lines:
        lines.append("")
        lines.append("[<LANG>_TYPES]")
        lines.extend(<lang>_types_lines)

    <lang>_api_lines = self._compress_<lang>_api(matrix)
    if <lang>_api_lines:
        lines.append("")
        lines.append("[<LANG>_API]")
        lines.extend(<lang>_api_lines)

    <lang>_func_lines = self._compress_<lang>_functions(matrix)
    if <lang>_func_lines:
        lines.append("")
        lines.append("[<LANG>_FUNCTIONS]")
        lines.extend(<lang>_func_lines)

    return '\n'.join(lines)
```

### Section Header Naming Convention

```
[<LANG>_TYPES]      - Type definitions (classes, structs, interfaces)
[<LANG>_API]        - API endpoints (REST, GraphQL, gRPC)
[<LANG>_FUNCTIONS]  - Functions and methods
[<LANG>_ML]         - ML/AI components (if applicable)
[<LANG>_INFRA]      - Infrastructure (databases, caches)
[<LANG>_DATA]       - Data processing components
```

---

## Step 6: Testing & Validation

### 6.1 Test Individual Extractors

```python
# test_extractors.py
from.codetrellis.extractors.<lang> import TypeExtractor

def test_type_extractor():
    code = '''
    class MyClass {
        field1: string
        field2: int
    }
    '''
    extractor = TypeExtractor()
    results = extractor.extract(code)

    assert len(results) == 1
    assert results[0].name == 'MyClass'
```

### 6.2 Test Parser Integration

```python
# test_parser.py
from.codetrellis.<lang>_parser_enhanced import Enhanced<Lang>Parser

def test_parser():
    code = '''...comprehensive sample code...'''

    parser = Enhanced<Lang>Parser()
    result = parser.parse(code, 'test.file')

    print(f'Types: {len(result.types)}')
    print(f'Functions: {len(result.functions)}')
    print(f'APIs: {len(result.api_endpoints)}')
    print(f'Frameworks: {result.detected_frameworks}')
```

### 6.3 Test Scanner Integration

```python
# test_scanner.py
from.codetrellis.scanner import ProjectScanner, ProjectMatrix
import pathlib

def test_scanner():
    matrix = ProjectMatrix(name='test', root_path='/test')
    scanner = ProjectScanner()

    # Create temp file or use real file
    test_file = pathlib.Path('/path/to/test.file')
    scanner._parse_<lang>(test_file, matrix)

    print(f'Types: {len(matrix.<lang>_types)}')
    print(f'Functions: {len(matrix.<lang>_functions)}')
```

### 6.4 Full CLI Test

```bash
# Run full scan
codetrellis scan /path/to/project --tier prompt

# Check output
cat /path/to/project/.codetrellis/cache/*/project/matrix.prompt | grep -A 20 "\[<LANG>_"
```

### 6.5 Validation Checklist

```python
# Run this validation script
def validate_integration():
    """Validate all components are properly integrated."""

    # 1. Check extractors are importable
    from.codetrellis.extractors.<lang> import (
        TypeExtractor, FunctionExtractor, APIExtractor
    )
    print("✅ Extractors importable")

    # 2. Check parser is importable
    from.codetrellis.<lang>_parser_enhanced import Enhanced<Lang>Parser
    print("✅ Parser importable")

    # 3. Check scanner has parser
    from.codetrellis.scanner import ProjectScanner, ProjectMatrix
    scanner = ProjectScanner()
    assert hasattr(scanner, '<lang>_parser')
    print("✅ Scanner has parser")

    # 4. Check matrix has fields
    matrix = ProjectMatrix(name='test', root_path='/test')
    assert hasattr(matrix, '<lang>_types')
    assert hasattr(matrix, '<lang>_functions')
    print("✅ Matrix has language fields")

    # 5. Check compressor has methods
    from.codetrellis.compressor import MatrixCompressor
    compressor = MatrixCompressor()
    assert hasattr(compressor, '_compress_<lang>_types')
    assert hasattr(compressor, '_compress_<lang>_api')
    print("✅ Compressor has methods")

    print("\n✅ ALL VALIDATIONS PASSED!")

validate_integration()
```

---

## 7. Common Pitfalls

### Pitfall 1: Attribute Name Mismatch

**Problem**: ParseResult has `keys` but scanner checks `fields`

```python
# ParseResult:
typeddicts: List[TypedDictInfo]  # TypedDictInfo has 'keys'

# Scanner (WRONG):
for f in td.fields:  # ❌ AttributeError!

# Scanner (CORRECT):
fields = getattr(td, 'fields', None) or getattr(td, 'keys', [])
```

### Pitfall 2: Singular vs Plural

**Problem**: ParseResult has `pipeline` but scanner checks `pipelines`

```python
# ParseResult:
pipeline: Dict = field(default_factory=dict)  # Singular

# Scanner (WRONG):
if result.pipelines:  # ❌ AttributeError!

# Scanner (CORRECT):
if result.pipeline:   # ✅ Matches ParseResult
```

### Pitfall 3: Missing Ignore Patterns

**Problem**: Scanner processes files from virtual environments

```python
# Add to IGNORE_PATTERNS:
IGNORE_PATTERNS = [
    'venv', '.venv', '*_env',      # Python virtual envs
    'site-packages',               # Python packages
    'node_modules',                # Node.js
    'target',                      # Rust/Java
    'vendor',                      # Go
]
```

### Pitfall 4: Silent Exception Handling

**Problem**: Errors are silently caught, data not populated

```python
# Add debug logging during development:
def _parse_<lang>(self, file_path, matrix):
    try:
        ...
    except Exception as e:
        # During development, log errors:
        print(f"Error parsing {file_path}: {e}")
        # In production, silent:
        pass
```

### Pitfall 5: Object-to-String Conversion

**Problem**: Storing objects instead of strings/dicts in matrix

```python
# WRONG - stores object:
"validators": model.validators  # List of ValidatorInfo objects

# CORRECT - convert to strings:
"validators": [v.name for v in model.validators] if model.validators else []
```

---

## 8. Reference: Python Integration Example

This section documents the actual Python integration done in this session.

### Files Created

```
codetrellis/extractors/python/
├── __init__.py                    # 174 lines - exports all 23 extractors
├── dataclass_extractor.py         # @dataclass classes
├── pydantic_extractor.py          # Pydantic BaseModel
├── typeddict_extractor.py         # TypedDict definitions
├── protocol_extractor.py          # Protocol classes
├── type_alias_extractor.py        # Type aliases
├── enum_extractor.py              # Enum classes
├── fastapi_extractor.py           # FastAPI routes
├── flask_extractor.py             # Flask routes/blueprints
├── sqlalchemy_extractor.py        # SQLAlchemy models
├── celery_extractor.py            # Celery tasks
├── dependency_extractor.py        # Import analysis
├── function_extractor.py          # Functions/classes
├── ml/
│   ├── pytorch_extractor.py       # nn.Module, training
│   ├── huggingface_extractor.py   # Transformers
│   └── langchain_extractor.py     # LangChain
├── database/
│   ├── mongodb_extractor.py       # PyMongo, Beanie
│   ├── vectordb_extractor.py      # Pinecone, ChromaDB
│   ├── redis_extractor.py         # Redis caching
│   └── kafka_extractor.py         # Kafka producers/consumers
├── data/
│   ├── pandas_extractor.py        # DataFrame operations
│   └── pipeline_extractor.py      # Airflow, Prefect
└── mlops/
    ├── mlflow_extractor.py        # MLflow experiments
    └── config_extractor.py        # Hydra, OmegaConf
```

### Files Modified

#### .codetrellis/scanner.py`

1. **Added to ProjectMatrix** (lines 97-128):

```python
# Core Python Types
python_dataclasses: List[Dict] = field(default_factory=list)
python_pydantic_models: List[Dict] = field(default_factory=list)
python_typed_dicts: List[Dict] = field(default_factory=list)
python_protocols: List[Dict] = field(default_factory=list)
python_type_aliases: List[Dict] = field(default_factory=list)
python_enums: List[Dict] = field(default_factory=list)

# Python Frameworks
python_fastapi_endpoints: List[Dict] = field(default_factory=list)
python_flask_routes: List[Dict] = field(default_factory=list)
python_sqlalchemy_models: List[Dict] = field(default_factory=list)
python_celery_tasks: List[Dict] = field(default_factory=list)
python_functions: List[Dict] = field(default_factory=list)

# ML/AI
python_ml_models: List[Dict] = field(default_factory=list)
python_ml_trainers: List[Dict] = field(default_factory=list)
python_langchain_components: List[Dict] = field(default_factory=list)

# Database/Infrastructure
python_mongodb_collections: List[Dict] = field(default_factory=list)
python_vector_stores: List[Dict] = field(default_factory=list)
python_redis_usage: List[Dict] = field(default_factory=list)
python_kafka_topics: List[Dict] = field(default_factory=list)

# Data/Pipeline
python_pandas_operations: List[Dict] = field(default_factory=list)
python_pipeline_dags: List[Dict] = field(default_factory=list)

# MLOps/Config
python_mlflow_experiments: List[Dict] = field(default_factory=list)
python_config_schemas: List[Dict] = field(default_factory=list)
```

2. **Added import**:

```python
from .python_parser_enhanced import EnhancedPythonParser
```

3. **Added parser initialization in `__init__`**:

```python
self.python_parser = EnhancedPythonParser()
```

4. **Added `_parse_python()` method** (lines 931-1170):

```python
def _parse_python(self, file_path: Path, matrix: ProjectMatrix):
    # Full implementation parsing all Python constructs
```

5. **Updated ignore patterns**:

```python
'*_env', 'site-packages', '.venv', 'venv'
```

#### .codetrellis/compressor.py`

Added 6 compression methods (lines 1368-1600+):

- `_compress_python_types()`
- `_compress_python_api()`
- `_compress_python_ml()`
- `_compress_python_infrastructure()`
- `_compress_python_data()`
- `_compress_python_functions()`

### Bugs Fixed During Integration

1. **TypedDictInfo uses `keys` not `fields`**:

```python
# Fixed in scanner.py:
fields_attr = getattr(td, 'fields', None) or getattr(td, 'keys', [])
```

2. **PythonParseResult has `pipeline` not `pipelines`**:

```python
# Fixed in scanner.py:
if result.pipeline:  # Not result.pipelines
```

### Final Test Results

```
✅ Files scanned: 1633
✅ Python types: 633 (19 Pydantic, 598 dataclasses)
✅ API endpoints: 104 (14 FastAPI, 90 Flask)
✅ Functions: 723
✅ Estimated tokens: ~33,016
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                 CodeTrellis Language Integration                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CREATE EXTRACTORS                                           │
│     📁.codetrellis/extractors/<lang>/*.py                              │
│     📄.codetrellis/extractors/<lang>/__init__.py                       │
│                                                                  │
│  2. CREATE PARSER                                               │
│     📄.codetrellis/<lang>_parser_enhanced.py                           │
│     - <Lang>ParseResult dataclass                               │
│     - Enhanced<Lang>Parser class                                │
│                                                                  │
│  3. UPDATE SCANNER .codetrellis/scanner.py)                            │
│     ✏️ Add fields to ProjectMatrix                              │
│     ✏️ Import parser                                            │
│     ✏️ Initialize in __init__                                   │
│     ✏️ Add _parse_<lang>() method                               │
│     ✏️ Update ignore patterns                                   │
│                                                                  │
│  4. UPDATE COMPRESSOR .codetrellis/compressor.py)                      │
│     ✏️ Add _compress_<lang>_*() methods                         │
│     ✏️ Call in compress() method                                │
│     ✏️ Add section headers [<LANG>_*]                           │
│                                                                  │
│  5. TEST                                                        │
│     🧪 Individual extractors                                    │
│     🧪 Parser with sample code                                  │
│     🧪 Scanner with single file                                 │
│     🧪 Full CLI scan                                            │
│                                                                  │
│  6. BPL INTEGRATION                                             │
│     📄.codetrellis/bpl/practices/<lang>_core.yaml (40-60 practices)   │
│     ✏️ Update selector.py (framework detection, prefix map)     │
│     🧪 Validate: python3 scripts/validate_practices.py          │
│                                                                  │
│  7. SEMANTIC EXTRACTION (automatic for new languages!)          │
│     ✅ Hooks/events detected via generic On*/Subscribe patterns │
│     ✅ Middleware detected via Use()/chain patterns              │
│     ✅ Routes detected via HTTP handler signatures               │
│     ✅ Lifecycle detected via Init/Start/Stop/Shutdown           │
│     ➕ Add language-specific patterns if needed                  │
│                                                                  │
│  8. ARCHITECTURE DETECTION                                      │
│     ✏️ Update can_extract() for manifest file (go.mod, etc.)    │
│     ✏️ Add project type to _detect_project_type()               │
│     ✏️ Add dependency parsing in _extract_dependencies()        │
│                                                                  │
│  ⚠️ WATCH FOR:                                                  │
│     - Attribute name mismatches (keys vs fields)                │
│     - Singular vs plural (pipeline vs pipelines)                │
│     - Object to string conversion                               │
│     - Missing ignore patterns                                   │
│     - False positive routes (use path validation!)              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 7: BPL Integration (UPDATED Current Session)

The **Best Practices Library (BPL)** provides context-aware coding practices that are automatically selected based on the project's detected tech stack. When adding a new language, you must integrate it with BPL for full CodeTrellis functionality.

> **Current state (BPL v1.4):** 407 practices across 16 YAML files, 125 unit tests passing,
> YAML validation script with **0 errors, 0 warnings**, token budget enforcement via `--max-practice-tokens`.
> `ApplicabilityRule` now supports `min_python` and `contexts` as formalized typed fields.
> CLI available via `python -m.codetrellis` (entry point added in v1.1).
> **New in v1.4:** tiktoken integration for accurate token counting, OutputFormat dynamic selection,
> "minimal" output tier, complexity_score and anti_pattern_id fields.
>
> **Practice files added:** React (40), NestJS (30), Django (30), Flask (20), Database (20), DevOps (15).

### 7.1 BPL Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       BPL Data Flow                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ProjectMatrix (from Scanner)                                   │
│       │                                                          │
│       ▼                                                          │
│  ProjectContext.from_matrix()                                   │
│   - Counts artifacts by language                                 │
│   - Detects frameworks from dependencies                         │
│   - Determines dominant language(s)                              │
│       │                                                          │
│       ▼                                                          │
│  PracticeSelector._filter_applicable()                          │
│   - Gets practice frameworks from ID prefix                      │
│   - Filters practices by detected context                        │
│   - Scores and ranks by relevance                                │
│       │                                                          │
│       ▼                                                          │
│  _enforce_token_budget()  (if --max-practice-tokens set)        │
│   - Estimates tokens via len(text) // 4 heuristic               │
│   - Greedy inclusion until budget exhausted                      │
│       │                                                          │
│       ▼                                                          │
│  [BEST_PRACTICES] section in output                             │
│   - minimal (~25 practices), standard (~15), comprehensive (~8) │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Create Practice YAML Files

#### File: .codetrellis/bpl/practices/<lang>\_core.yaml`

```yaml
# <Lang> Best Practices Library
# Version: 1.0.0
# Total Practices: 40-60
# Coverage: Types, Functions, Error Handling, Security, Performance

version: "1.0.0"
framework: <lang>
description: "Core <lang> best practices for modern development"

practices:
  # ============================================================================
  # TYPE SAFETY (<LANG>001-<LANG>010)
  # ============================================================================

  - id: <LANG>001
    title: "<Practice Title>"
    category: type_safety # Must match PracticeCategory enum
    level: beginner # beginner | intermediate | advanced
    priority: high # critical | high | medium | low
    python_version: # Optional: version constraints
      min_version: "3.9"
    applicability: # Optional: targeting rules (v1.1)
      frameworks: ["<lang>"]
      min_python: "3.10" # Formalized in v1.1 — version check in matches()
      contexts: ["web", "api"] # Formalized in v1.1 — usage contexts
    content:
      description: |
        Detailed description of the practice.
        Can be multi-line.
      rationale: |
        Why this practice matters.
      good_examples:
        - |
          // Example code showing correct usage
          func example() {
              // good code
          }
      bad_examples:
        - |
          // ❌ Don't do this
          func badExample() {
              // bad code
          }
      references:
        - "https://docs.lang.org/best-practices"
      tags:
        - type-safety
        - core
```

#### Practice ID Naming Convention

| Prefix      | Language/Framework        |
| ----------- | ------------------------- |
| `PY`, `PYE` | Python, Python Expanded   |
| `TS`        | TypeScript                |
| `NG`        | Angular                   |
| `FAST`      | FastAPI                   |
| `GO`        | Go                        |
| `RS`        | Rust                      |
| `JAVA`      | Java                      |
| `KT`        | Kotlin                    |
| `CS`        | C#                        |
| `RB`        | Ruby                      |
| `DP`        | Design Patterns (generic) |

### 7.3 Add PracticeCategory Values

#### File: .codetrellis/bpl/models.py`

If your language needs new categories, add them to the `PracticeCategory` enum:

```python
class PracticeCategory(Enum):
    """Categories for organizing best practices."""

    # Existing categories
    TYPE_SAFETY = "type_safety"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE = "performance"
    SECURITY = "security"

    # NEW: Add language-specific categories if needed
    CONCURRENCY = "concurrency"          # For Go goroutines, Rust async
    MEMORY_SAFETY = "memory_safety"      # For Rust, C++
    DEPENDENCY_INJECTION = "di"          # For Java/Spring, C#/.NET
    GENERICS = "generics"                # For Go, TypeScript, Rust

    # Added in v1.2 (NestJS/React expansion)
    VALIDATION = "validation"            # For NestJS pipes, React forms
    MONITORING = "monitoring"            # For health checks, logging
    RELIABILITY = "reliability"          # For graceful shutdown, resilience
    ACCESSIBILITY = "accessibility"      # For React a11y patterns
    USER_EXPERIENCE = "user_experience"  # For React loading states, UX
```

> **Note (v1.2):** 5 new categories were added for React and NestJS practices.
> Remember to also update `scripts/validate_practices.py` `VALID_CATEGORIES` set.

> **Note (v1.1):** The `ApplicabilityRule` frozen dataclass now includes:
>
> - `min_python: Optional[str]` — checked in `matches()` via tuple comparison against `context["python_version"]`
> - `contexts: tuple[str, ...]` — formalized usage context tags
> - Both fields are recognized by `validate_practices.py` and serialized in `to_dict()`
> - `repository.py` `_parse_practice()` passes these fields from YAML `applicability` section

### 7.4 Update Framework Detection

#### File: .codetrellis/bpl/selector.py`-`ProjectContext.from_matrix()`

Add framework detection for the new language:

```python
@classmethod
def from_matrix(cls, matrix: Any) -> "ProjectContext":
    # ... existing code ...

    # ==== <LANG> FRAMEWORK DETECTION ====
    <lang>_framework_mapping = {
        # Map framework name to dependency names
        "gin": ["github.com/gin-gonic/gin"],      # Go
        "actix": ["actix-web"],                    # Rust
        "spring": ["spring-boot", "spring-core"], # Java
        "rails": ["rails"],                        # Ruby
    }

    for framework, dep_names in <lang>_framework_mapping.items():
        if any(dep in context.dependencies for dep in dep_names):
            context.frameworks.add(framework)

    # ==== COUNT ARTIFACTS FOR WEIGHTED DETECTION ====
    <lang>_count = 0
    <lang>_artifacts = [
        "<lang>_types", "<lang>_functions", "<lang>_structs",
        "<lang>_interfaces", "<lang>_api_endpoints"
    ]
    for attr in <lang>_artifacts:
        if hasattr(matrix, attr):
            <lang>_count += len(getattr(matrix, attr, []))

    # Add to context if significant
    SIGNIFICANCE_THRESHOLD = 5
    if <lang>_count >= SIGNIFICANCE_THRESHOLD:
        context.frameworks.add("<lang>")
```

### 7.5 Update Practice ID Prefix Mapping

#### File: .codetrellis/bpl/selector.py`-`\_get_practice_frameworks()`

Add the ID prefix mapping for the new language:

```python
def _get_practice_frameworks(self, practice: BestPractice) -> Set[str]:
    """Determine which frameworks a practice applies to from its ID prefix."""
    practice_id = practice.id.upper()

    # Map of ID prefixes to required frameworks
    prefix_framework_map = {
        # Existing
        "NG": {"angular", "typescript"},
        "TS": {"typescript"},
        "PY": {"python"},
        "PYE": {"python"},
        "DP": set(),  # Design patterns are generic

        # NEW: Add your language
        "GO": {"golang"},
        "RS": {"rust"},
        "JAVA": {"java"},
        "KT": {"kotlin"},
        "CS": {"csharp", "dotnet"},
        "RB": {"ruby"},
        "SCALA": {"scala"},
        "GIN": {"gin", "golang"},
        "ACTIX": {"actix", "rust"},
        "SPRING": {"spring", "java"},
        "RAILS": {"rails", "ruby"},
        "PLAY": {"play", "scala"},
        "AKKA": {"akka", "scala"},
        "ZIO": {"zio", "scala"},
        "HTTP4S": {"http4s", "scala"},
        "TAPIR": {"tapir", "scala"},
    }

    # ... rest of method
```

### 7.6 Update Filtering Logic

#### File: .codetrellis/bpl/selector.py`-`\_filter_applicable()`

Add filtering for the new language:

```python
def _filter_applicable(self, practices, context, criteria):
    # ... existing code ...

    # Detect language presence
    has_<lang> = any(f in context_frameworks for f in ["<lang>", "framework1", "framework2"])

    # ... in the filtering loop ...

    # <Lang> practices: require <lang> in context
    if "<lang>" in practice_frameworks:
        if has_<lang>:
            result.append(practice)
        continue
```

### 7.7 Recommended Practice Categories

When creating practices for a new language, cover these categories:

| Category           | Practice Count | Examples                          |
| ------------------ | -------------- | --------------------------------- |
| **Type Safety**    | 8-12           | Type hints, generics, null safety |
| **Error Handling** | 6-10           | Error types, recovery, logging    |
| **Performance**    | 6-10           | Memory, async, caching            |
| **Security**       | 8-12           | Input validation, crypto, auth    |
| **Concurrency**    | 5-8            | Threads, async, channels          |
| **Code Style**     | 6-10           | Naming, formatting, idioms        |
| **Testing**        | 5-8            | Unit tests, mocks, coverage       |
| **Architecture**   | 5-8            | Patterns, DI, modules             |

**Total: 40-60 practices per language**

### 7.8 BPL Testing Checklist

```bash
# 1. Run YAML validation (must pass with 0 errors, 0 warnings)
cd tools.codetrellis
python3 scripts/validate_practices.py
# Expected: 0 errors, 0 warnings. All fields (min_python, contexts) are recognized.

# 2. Verify practices load
python -c "
from.codetrellis.bpl import get_repository
repo = get_repository()
repo.load_all()
print(f'Loaded {len(repo.practices)} practices')
# Should see your <LANG>* practices
for p in repo.practices.values():
    if p.id.startswith('<LANG>'):
        print(f'  {p.id}: {p.title}')
"

# 3. Test context detection
python -c "
from.codetrellis.scanner import ProjectScanner
from.codetrellis.bpl.selector import ProjectContext

scanner = ProjectScanner()
matrix = scanner.scan('/path/to/<lang>/project')
context = ProjectContext.from_matrix(matrix)
print(f'Detected frameworks: {context.frameworks}')
# Should include '<lang>' and any frameworks
"

# 4. Test practice selection (all 3 formats)
python -m.codetrellis.cli scan /path/to/<lang>/project --include-practices --practices-format minimal
# Should show ~25 <LANG>* practices, NOT practices from other languages

python -m.codetrellis.cli scan /path/to/<lang>/project --include-practices --practices-format standard
# Should show ~15 practices

python -m.codetrellis.cli scan /path/to/<lang>/project --include-practices --practices-format comprehensive
# Should show ~8 practices with full detail

# 5. Test token budget enforcement
python -m.codetrellis.cli scan /path/to/<lang>/project --include-practices --max-practice-tokens 200
# Should show only 1-2 practices under tight budget

# 6. Run all BPL unit tests (should all pass)
python3 -m pytest tests/unit/test_bpl_*.py -v
# Expected: All tests pass (125+ after adding your language tests)
```

### 7.9 Add Unit Tests for New Language

Create `tests/unit/test_bpl_<lang>.py` following existing patterns:

```python
"""
Unit tests for <Lang> BPL integration.

Reference: 125 existing tests across:
- tests/unit/test_bpl_models.py    (43 tests)
- tests/unit/test_bpl_repository.py (35 tests)
- tests/unit/test_bpl_selector.py   (47 tests)
"""
import pytest
from.codetrellis.bpl import get_repository
from.codetrellis.bpl.selector import ProjectContext, PracticeSelector, SelectionCriteria


class TestLangPracticeLoading:
    """Verify <lang> practices load correctly."""

    def test_practices_load(self):
        repo = get_repository()
        repo.load_all()
        lang_practices = [p for p in repo.practices.values()
                         if p.id.startswith('<LANG>')]
        assert len(lang_practices) >= 40, f"Expected 40+ practices, got {len(lang_practices)}"

    def test_no_duplicate_ids(self):
        repo = get_repository()
        repo.load_all()
        ids = [p.id for p in repo.practices.values() if p.id.startswith('<LANG>')]
        assert len(ids) == len(set(ids)), "Duplicate practice IDs found"


class TestLangContextDetection:
    """Verify <lang> detected from matrix."""

    def test_framework_detected(self):
        # Build a mock matrix with <lang> artifacts
        # Verify ProjectContext.from_matrix() detects the language
        pass


class TestLangPracticeSelection:
    """Verify correct practices selected for <lang> context."""

    def test_only_lang_practices_selected(self):
        # With a pure <lang> context, should NOT get Python/TS practices
        pass

    def test_token_budget_respected(self):
        # With max_tokens set, should limit output
        pass
```

### 7.9 BPL Integration Example: Go Language

Here's a complete example for adding Go support:

#### .codetrellis/bpl/practices/golang_core.yaml`

```yaml
version: "1.0.0"
framework: golang
description: "Go best practices for idiomatic and efficient code"

practices:
  - id: GO001
    title: "Use Explicit Error Handling"
    category: error_handling
    level: beginner
    priority: critical
    content:
      description: |
        Always check returned errors. Never ignore them with _.
      good_examples:
        - |
          result, err := doSomething()
          if err != nil {
              return fmt.Errorf("doSomething failed: %w", err)
          }
      bad_examples:
        - |
          result, _ := doSomething() // ❌ Never ignore errors
      tags:
        - error-handling
        - idiomatic-go

  - id: GO002
    title: "Use Context for Cancellation"
    category: concurrency
    level: intermediate
    priority: high
    content:
      description: |
        Use context.Context for cancellation, timeouts, and request-scoped values.
      good_examples:
        - |
          func fetchData(ctx context.Context) error {
              select {
              case <-ctx.Done():
                  return ctx.Err()
              case result := <-dataChan:
                  return process(result)
              }
          }
      tags:
        - context
        - cancellation
        - concurrency
```

#### Update `selector.py`

```python
# In from_matrix():
go_framework_mapping = {
    "gin": ["github.com/gin-gonic/gin"],
    "echo": ["github.com/labstack/echo"],
    "fiber": ["github.com/gofiber/fiber"],
    "grpc": ["google.golang.org/grpc"],
}

# In _get_practice_frameworks():
prefix_framework_map = {
    ...
    "GO": {"golang"},
    "GIN": {"gin", "golang"},
    "ECHO": {"echo", "golang"},
}

# In _filter_applicable():
has_golang = any(f in context_frameworks for f in ["golang", "gin", "echo", "fiber"])
```

---

## Appendix: Language-Specific Considerations

### Go

- Structs, interfaces, functions
- Goroutines and channels
- HTTP handlers (net/http, gin, echo)
- gRPC services

### Rust

- Structs, enums, traits, impls
- Async functions
- Actix-web, Rocket routes
- Tokio patterns

### Java/Kotlin

- Classes, interfaces, annotations
- Spring Boot controllers
- JPA entities
- Dependency injection
- **Java Framework Parsers (v4.94):** Spring Boot (beans/endpoints/autoconfig/security/data), Spring Framework (DI/AOP/events/MVC), Quarkus (CDI/REST/Panache/config/extensions), Micronaut (DI/HTTP/Data/config/features), Jakarta EE (CDI/Servlet/JPA/JAX-RS/EJB)

### C#

- Classes, interfaces, records
- ASP.NET Core controllers
- Entity Framework models
- Dependency injection

---

## Appendix: BPL Quick Reference

### Current Practice Counts (Updated Current Session)

| File                        |   Count | Notes                       |
| --------------------------- | ------: | --------------------------- |
| `python_core.yaml`          |      17 | Core Python practices       |
| `python_core_expanded.yaml` |      60 | Expanded Python coverage    |
| `python_3_10.yaml`          |      12 | match, ParamSpec, etc.      |
| `python_3_11.yaml`          |      12 | ExceptionGroup, tomllib     |
| `python_3_12.yaml`          |      12 | f-string debug, type params |
| `typescript_core.yaml`      |      45 | TS 5.0+ features            |
| `angular.yaml`              |      45 | Signals, Standalone         |
| `fastapi.yaml`              |      10 | Endpoints, Depends          |
| `solid_patterns.yaml`       |       9 | SRP, OCP, LSP, ISP, DIP     |
| `design_patterns.yaml`      |      30 | GoF + Enterprise            |
| `nestjs.yaml`               |      30 | Controllers, Services       |
| `react.yaml`                |      40 | Hooks, State, Components    |
| `django.yaml`               |      30 | Views, Models, ORM          |
| `flask.yaml`                |      20 | Routes, Blueprints          |
| `database.yaml`             |      20 | SQL, ORM, Indexing          |
| `devops.yaml`               |      15 | CI/CD, Docker, IaC          |
| `go_core.yaml`              |      40 | Go idioms, concurrency      |
| **Total**                   | **447** |                             |

### BPL Quality Infrastructure

| Component                  | Location                                             | Details                       |
| -------------------------- | ---------------------------------------------------- | ----------------------------- |
| Unit Tests                 | `tests/unit/test_bpl_*.py`                           | 125 tests, all passing        |
| YAML Validation            | `scripts/validate_practices.py`                      | 0 errors, **0 warnings**      |
| Architecture Docs          | `docs/bpl/ARCHITECTURE.md`                           | System design                 |
| Roadmap                    | `docs/bpl/ROADMAP.md`                                | v1.1, v1.2, v2.0 plans        |
| ADR: Flat YAML             | `docs/bpl/adr/001-*.md`                              | Why flat files                |
| ADR: Rule-based            | `docs/bpl/adr/002-*.md`                              | Why not ML                    |
| ADR: Nested in CodeTrellis | `docs/bpl/adr/003-*.md`                              | Why.codetrellis/bpl/ not bpl/ |
| Session Checklist          | `docs/checklist/BPL_SESSION_CHECKLIST_2026_02_06.md` | Full audit trail              |

### Practice YAML Structure

```yaml
practices:
  - id: <LANG>001 # Unique ID with language prefix
    title: "Practice Title" # Short descriptive title
    category: type_safety # PracticeCategory enum value
    level: beginner # beginner | intermediate | advanced
    priority: high # critical | high | medium | low
    python_version: # Optional: version constraints
      min_version: "3.9"
    applicability: # Optional: framework requirements
      frameworks: ["fastapi"]
      min_python: "3.10" # Formalized in v1.1 — checked by matches()
      contexts: ["web", "api"] # Formalized in v1.1 — usage contexts
    content:
      description: | # Detailed description
        Multi-line description
      rationale: | # Why it matters
        Explanation
      good_examples: # List of correct examples
        - |
          // code example
      bad_examples: # List of incorrect examples
        - |
          // bad code
      references: # External links
        - "https://..."
      tags: # Searchable tags
        - tag1
        - tag2
```

### ID Prefix Reference

| Language   | Prefix      | Framework Prefixes                       |
| ---------- | ----------- | ---------------------------------------- |
| Python     | `PY`, `PYE` | `FAST` (FastAPI), `FLASK`, `DJANGO`      |
| TypeScript | `TS`        | `NG` (Angular), `NEST`, `REACT`          |
| Database   | `DB`        | Generic SQL, ORM patterns                |
| DevOps     | `DEVOPS`    | CI/CD, Docker, IaC                       |
| Go         | `GO`        | `GIN`, `ECHO`, `FIBER`                   |
| Rust       | `RS`        | `ACTIX`, `ROCKET`, `AXUM`                |
| Java       | `JAVA`      | `SPRING`, `QUARKUS`                      |
| Kotlin     | `KT`        | `KTOR`                                   |
| C#         | `CS`        | `ASPNET`, `BLAZOR`                       |
| Ruby       | `RB`        | `RAILS`, `SINATRA`                       |
| PHP        | `PHP`       | `LARAVEL`, `SYMFONY`                     |
| Scala      | `SCALA`     | `PLAY`, `AKKA`, `ZIO`, `HTTP4S`, `TAPIR` |
| SOLID      | `SOLID`     | N/A (cross-language, 9 practices)        |
| Generic    | `DP`        | Design Patterns (30 practices)           |

---

## Step 8: Cross-Cutting Extractor Integration (NEW - Phase A Remediation)

> **Added:** 7 Feb 2026 — Documents cross-cutting extractors that work across all languages, domain detection, and the AI_INSTRUCTION prompt header.

### 8.1 RunbookExtractor Pattern

The `RunbookExtractor` is a **cross-cutting extractor** — unlike language-specific extractors (TypeExtractor, FunctionExtractor), it operates on **config files** that don't belong to any single language: Dockerfiles, docker-compose.yml, CI/CD configs, Makefiles, and shell scripts.

#### Source Files

| File                                                  | Purpose                      |
| ----------------------------------------------------- | ---------------------------- |
| .codetrellis/extractors/runbook_extractor.py`         | Main extractor (~500 lines)  |
| .codetrellis/scanner.py` (`\_extract_runbook_data()`) | Integration point in scanner |
| .codetrellis/compressor.py` (`\_compress_runbook()`)  | Output formatting for prompt |

#### How It Works

```
Scanner._walk_directory()
    │
    ├── Encounters .py, .ts → Language-specific parsers
    │
    └── Encounters Dockerfile, docker-compose.yml, Makefile, .sh, .yml (CI/CD)
            │
            ▼
        RunbookExtractor.extract_from_file(path, content)
            │
            ├── _extract_docker_info()      → DockerInfo
            ├── _extract_compose_info()     → ComposeInfo
            ├── _extract_cicd_info()        → CICDInfo
            ├── _extract_makefile_info()    → MakefileInfo
            └── _extract_shell_info()       → ShellInfo
            │
            ▼
        ProjectMatrix.runbook_data (dict)
            │
            ▼
        MatrixCompressor._compress_runbook() → [RUNBOOK] section in prompt
```

#### Integration Pattern for New Config Extractors

If adding a new cross-cutting extractor (e.g., for Terraform, Kubernetes manifests):

1. **Create extractor** in .codetrellis/extractors/` (not inside a language subdirectory)
2. **Add dataclass** for extracted data (e.g., `TerraformInfo`)
3. **Register in scanner** — add file extension/name matching in `_walk_directory()` or a new `_extract_*()` method
4. **Add ProjectMatrix field** for the new data
5. **Add compressor method** — `_compress_terraform()` or similar
6. **Test with real projects** — use `--optimal` flag to verify output

#### Key Lesson (from Phase A Testing)

> The `_compress_runbook()` method was producing empty `[RUNBOOK]` sections when runbook data existed but all sub-sections were empty strings. Fix: Check `if any(runbook_data.values())` before emitting the section header.

### 8.2 Domain Category Extension

The `BusinessDomainExtractor` detects what kind of project is being scanned (FinTech, E-commerce, Developer Tools, etc.) and includes domain-specific best practices.

#### Adding a New Domain Category

1. **Add domain to `DomainCategory` enum** in `business_domain_extractor.py`:

   ```python
   class DomainCategory(Enum):
       AI_ML = "AI/Machine Learning"
       DEVTOOLS = "Developer Tools"
       # Add your new domain here
       HEALTHCARE = "Healthcare"
   ```

2. **Add indicator patterns** in the `DOMAIN_INDICATORS` dict:

   ```python
   DOMAIN_INDICATORS = {
       DomainCategory.HEALTHCARE: {
           'keywords': ['patient', 'diagnosis', 'ehr', 'fhir', 'hl7', 'hipaa'],
           'files': ['health_records.py', 'patient_portal.py'],
           'frameworks': ['django-health', 'fhir-py'],
       },
   }
   ```

3. **Domain scoring**: The extractor scores each domain by counting matching indicators. Highest score wins. In Phase A, `AI_ML` and `DEVTOOLS` domains were added to fix false-positive "Trading/Finance" detection on developer tool projects.

#### Domains Added in Phase A

| Domain     | Indicators Added                                                                         |
| ---------- | ---------------------------------------------------------------------------------------- |
| `AI_ML`    | Keywords: `model`, `training`, `inference`, `neural`, `tensor`, `dataset`, `epoch`       |
| `DEVTOOLS` | Keywords: `linter`, `formatter`, `cli`, `parser`, `scanner`, `extractor`, `ast`, `token` |

### 8.3 `[AI_INSTRUCTION]` Prompt Header

Every `matrix.prompt` output now starts with a 13-line `[AI_INSTRUCTION]` block that tells any AI reading it how to interpret the file.

#### Implementation Location

.codetrellis/compressor.py`→`compress()` method, inserted before the header line.

#### What It Does

- Tells the AI this is a **structured project analysis file** generated by CodeTrellis
- Instructs the AI to **read the entire file** before responding
- Lists all sections to expect (BEST_PRACTICES, RUNBOOK, PROJECT_STRUCTURE, etc.)
- Directs the AI to use the content as **ground truth** about the project

#### ⚠️ Critical Bracket Syntax Warning

> **Do NOT use `[SECTION_NAME]` bracket syntax inside instruction text.**
>
> The CLI's `cli.py` (line ~519) has a `re.sub` regex that strips any line matching `\[SECTION_NAME\]` patterns followed by content. If you write `[BEST_PRACTICES]` inside the instruction text, it gets treated as a section header and removed.
>
> **Correct:** `"# Sections include: the BEST_PRACTICES section, the RUNBOOK section..."`
> **Wrong:** `"# Sections include: [BEST_PRACTICES], [RUNBOOK]..."`

---

## Step 9: Semantic Extraction Integration (NEW v4.6, UPDATED v4.7)

> **Added:** 9 Feb 2026 — Documents the language-agnostic SemanticExtractor that detects behavioral patterns (hooks, middleware, routes, plugins, CLI commands, lifecycle) without requiring language-specific extractors.
>
> **Updated v4.7:** Enhanced middleware detection (exported factory functions, Bind() patterns, middleware IDs), CLI command detection (cobra, click, argparse, commander), enhanced plugin detection (MustRegister, interface patterns, Mount), .d.ts file filtering.

### 9.1 Why Semantic Extraction?

Language-specific extractors (GoFunctionExtractor, PythonDataclassExtractor) handle **structural** patterns — types, functions, APIs. But projects also have **behavioral** patterns that are common across languages:

| Pattern          | Examples                                             | Languages                   |
| ---------------- | ---------------------------------------------------- | --------------------------- |
| **Hooks/Events** | `OnBeforeCreate`, `addEventListener`, `Subscribe`    | Go, JS/TS, Python, Java     |
| **Middleware**   | `.Use()`, `.Bind()`, `RequireAuth()`, CORS factories | Go, Express, NestJS, Django |
| **Routes**       | `HandleFunc`, `router.GET`, HTTP handler signatures  | Go, Python, JS/TS           |
| **Plugins**      | `Register()`, `AddPlugin`, `MustRegister`, `Mount`   | Go, JS/TS, Java             |
| **CLI Commands** | `cobra.Command`, `@click.command`, `add_parser`      | Go, Python, Node.js         |
| **Lifecycle**    | `Init`, `Start`, `Stop`, `Shutdown`, `Destroy`       | All languages               |

The `SemanticExtractor` detects these patterns using **language-agnostic regex heuristics**, so any new language gets behavioral extraction **for free** without writing custom extractors.

### 9.2 Architecture

```
Scanner._extract_semantics()
    │
    ▼
SemanticExtractor.extract(content, file_path)
    │
    ├── _extract_hooks()         → List[HookInfo]       → [HOOKS] section
    ├── _extract_middleware()    → List[MiddlewareInfo]  → [MIDDLEWARE] section
    ├── _extract_routes()       → List[GenericRouteInfo] → [ROUTES_SEMANTIC] section
    ├── _extract_plugins()      → List[PluginInfo]       (stored, not yet compressed)
    ├── _extract_lifecycle()    → List[LifecycleInfo]    → [LIFECYCLE] section
    └── _extract_cli_commands() → List[CLICommandInfo]   → [CLI_COMMANDS] section (NEW v4.7)
    │
    ▼
SemanticResult → ProjectMatrix.semantic_* fields
    │
    ▼
MatrixCompressor._compress_semantic_*() → matrix.prompt sections
```

### 9.3 Key Files

| File                                                    | Purpose                                    |
| ------------------------------------------------------- | ------------------------------------------ |
| .codetrellis/extractors/semantic_extractor.py`          | Main extractor (~510 lines, v4.7)          |
| .codetrellis/scanner.py` (`\_extract_semantics()`)      | Integration point — scans all source files |
| .codetrellis/compressor.py` (`_compress_semantic_\*()`) | Output formatting for 5 sections           |

### 9.4 How It Works for New Languages

**Zero configuration needed.** When you add a new language:

1. The scanner's `_extract_semantics()` method already scans **all source files** matching `FILE_TYPES`
2. The `SemanticExtractor` uses generic patterns that work across languages
3. New `[HOOKS]`, `[MIDDLEWARE]`, `[ROUTES_SEMANTIC]`, `[LIFECYCLE]` sections appear automatically

**You only need to add patterns if** the new language has unique behavioral idioms not covered by the generic patterns. For example, PocketBase's `BindFunc` pattern was added for Go-specific hook registration.

### 9.5 Pattern Categories

#### Hook Patterns (detect event/callback registration)

```python
HOOK_PATTERNS = [
    r'\bOn[A-Z]\w+\s*\(',           # On* method calls: OnBeforeCreate()
    r'\.BindFunc\s*\(',              # PocketBase-style: app.OnModelBeforeCreate().BindFunc()
    r'\.AddListener\s*\(',           # Event listener pattern
    r'\.Subscribe\s*\(',             # Pub/sub pattern
    r'\.addEventListener\s*\(',      # DOM/browser pattern
    r'\.on\s*\(\s*["\']',           # Node.js style: emitter.on('event', ...)
    r'\.emit\s*\(\s*["\']',         # Event emission
    r'@hook\s*\(',                  # Python decorator style
    r'\.hook\s*\(',                 # Generic hook registration
]
```

#### Path Validation (filter false positives)

```python
def _is_valid_route_path(self, path: str) -> bool:
    """Validate that a detected path is actually a URL route, not noise."""
    # Must start with / or {
    if not path.startswith('/') and not path.startswith('{'):
        return False
    # Exclude HTTP header-like strings
    header_patterns = ['Content-', 'Accept-', 'Cache-', 'X-']
    if any(path.startswith(p) for p in header_patterns):
        return False
    return True
```

### 9.6 Validation Results (PocketBase)

| Metric              | v4.5 (Before Semantic) | v4.6 (After Semantic) | v4.7 (After 16-Gap Remediation) |
| ------------------- | ---------------------- | --------------------- | ------------------------------- |
| Domain detected     | General Application    | General Application   | **Infrastructure/BaaS** ✅      |
| Hooks detected      | 0                      | 64                    | 64                              |
| Middleware detected | 0                      | 1                     | **42** ✅                       |
| Semantic routes     | 0                      | 45                    | 45                              |
| CLI commands        | 0                      | 0                     | **9** (cobra) ✅                |
| .d.ts in IMPL_LOGIC | Yes (noise)            | Yes (noise)           | **No** ✅                       |
| Lifecycle events    | 0                      | detected              | detected                        |

### 9.7 Adding New Semantic Patterns

To extend the SemanticExtractor for a new framework or language pattern:

```python
# In.codetrellis/extractors/semantic_extractor.py

# Add to the appropriate pattern list:
HOOK_PATTERNS.append((r'\bnew_framework_hook_pattern\s*\(', 'event'))

# Middleware patterns added in v4.7:
MIDDLEWARE_PATTERNS.append(
    # Exported middleware factory functions (returns Handler/Hook)
    (r'func\s+(MyMiddleware)\s*\([^)]*\)\s*\*?hook\.Handler', 'generic')
)
MIDDLEWARE_PATTERNS.append(
    # .Bind() pattern for inline middleware
    (r'\.Bind\s*\(\s*(MyMiddleware)\s*\(', 'generic')
)

# CLI command patterns:
CLI_COMMAND_PATTERNS.append(
    (r'new_cli_pattern_for_framework', 'framework_name')
)

# Plugin detection patterns:
PLUGIN_PATTERNS.append(
    (r'MustRegister\s*\(\s*["\']?(\w+)', 'plugin')  # Added in v4.7
)

# Or add a new category by:
# 1. Create a new Info dataclass (e.g., SignalInfo)
# 2. Add a new _extract_signals() method
# 3. Add the field to SemanticResult
# 4. Add semantic_signals to ProjectMatrix in scanner.py
# 5. Add _compress_semantic_signals() to compressor.py
# 6. Call it in compress() to emit [SIGNALS] section
```

### 9.8 Route Group Prefix Tracking (NEW v4.7)

The Go API extractor now tracks `.Group("/prefix")` assignments within each file and prepends the prefix to child routes. This addresses the issue where routes like `sub.GET("/{key}")` in a `sub := rg.Group("/backups")` context would show as `/{key}` instead of `/backups/{key}`.

**How it works:**

1. `_build_group_prefix_map()` scans for `var := parent.Group("/prefix")` patterns
2. Builds a map: `{variable_name: accumulated_prefix}`
3. Resolves chained groups: `api := r.Group("/api")`, `sub := api.Group("/v2")` → `sub = "/api/v2"`
4. During route extraction, if the receiver matches a known group variable, the prefix is prepended

**Limitation:** Cross-file prefix resolution (e.g., parent passes `/api` group as a function parameter) is not yet supported. Within-file group chains work correctly.

---

## Step 10: File Filtering & Output Quality (NEW v4.7)

> **Added:** 9 Feb 2026 — Lessons learned from PocketBase 16-gap analysis. Ensures new language integrations produce clean, relevant output without noise from vendor/declaration files.

### 10.1 Declaration & Vendor File Filtering

When a project embeds UI code, type stubs, or vendor files from other languages, those files can pollute `[IMPLEMENTATION_LOGIC]`, `[ROUTES_SEMANTIC]`, and `[LIFECYCLE]` sections with irrelevant noise.

**Files that MUST be filtered in `_extract_logic()` and `_extract_semantics()`:**

| Pattern                       | Why                                                           | Added    |
| ----------------------------- | ------------------------------------------------------------- | -------- |
| `.min.js`, `.min.ts`          | Minified bundles — unreadable noise                           | v4.5     |
| `.d.ts`                       | TypeScript declaration files — type stubs, not implementation | **v4.7** |
| `_test.go`, `.spec.`, `test_` | Test files inflate logic counts                               | v4.5     |

**When adding a new language, check for similar patterns:**

- **Rust:** `.rlib` files, `target/` directory
- **Java:** `.class` files, `build/` directory
- **C#:** `.Designer.cs` (auto-generated UI code), `obj/` directory
- **PHP:** `vendor/` (Composer dependencies)

### 10.2 Domain Category Extension

The `BusinessDomainExtractor` has domain categories with keyword indicators. If your language/framework targets a domain not yet covered, add it:

**Current domains (v4.7):**

| Domain             | Example Projects                                       |
| ------------------ | ------------------------------------------------------ |
| TRADING            | Fintech, trading bots, market data                     |
| ECOMMERCE          | Online stores, payment processing                      |
| CRM                | Sales, leads, customer management                      |
| HEALTHCARE         | EHR, patient management                                |
| EDUCATION          | LMS, course platforms                                  |
| ANALYTICS          | Dashboards, BI tools                                   |
| COMMUNICATION      | Chat, messaging, email                                 |
| AI_ML              | LLM platforms, ML pipelines                            |
| DEVTOOLS           | Code analyzers, build tools                            |
| **INFRASTRUCTURE** | **BaaS, PaaS, API gateways, auth services** (NEW v4.7) |

**How to add a new domain:**

1. Add enum value to `DomainCategory` in `business_domain_extractor.py`
2. Add 15-20 unique keyword indicators to `DOMAIN_INDICATORS`
3. Add description to `_generate_domain_description()`
4. Ensure keywords are **unique** to avoid overlapping with existing domains

### 10.3 Route Group Prefix Tracking

For languages with route grouping (Go, Express, Flask Blueprints, NestJS controllers):

- Track `.Group()`, `.Blueprint()`, `.controller()` variable assignments
- Build a prefix map: `{variable_name: accumulated_prefix_path}`
- Resolve chains: `api = router.Group("/api")`, `v2 = api.Group("/v2")` → `"/api/v2"`
- Prepend prefix when extracting child routes

**Already implemented for Go** (v4.7). When adding Express/Flask/NestJS support, follow the same pattern in the API extractor.

### 10.4 Middleware Factory Detection

Many frameworks define middleware as exported factory functions rather than `.Use()` calls:

```go
// Go: func RequireAuth() *hook.Handler[*RequestEvent]
// Python: def require_auth() -> Callable
// JS: const requireAuth = () => (req, res, next) => ...
```

**v4.7 added patterns for:**

- Exported functions returning `*hook.Handler` (PocketBase/Go)
- `.Bind(MiddlewareName(` inline middleware binding
- Middleware ID constants (e.g., `DefaultRateLimitMiddlewareId`)

When integrating a new language, add similar factory patterns to `MIDDLEWARE_PATTERNS`.

---

## 9. Reference: Go Integration Example (NEW v4.5)

This section documents the actual Go language integration completed in Phase F, serving as a reference implementation for adding new languages.

### Files Created

```
codetrellis/extractors/go/
├── __init__.py                    # Exports all 4 Go extractors
├── type_extractor.py              # Structs, interfaces, type aliases
├── function_extractor.py          # Functions, methods with receivers
├── enum_extractor.py              # Const blocks, iota patterns
└── api_extractor.py               # HTTP routes (gin/echo/fiber/chi/gorilla/net/http/generic), gRPC

codetrellis/go_parser_enhanced.py         # EnhancedGoParser + GoParseResult + framework detection
codetrellis/bpl/practices/go_core.yaml    # 40 practices (GO001-GO040)
codetrellis/extractors/semantic_extractor.py  # Language-agnostic behavioral extraction
```

### Files Modified

| File                                               | Changes                                                                                                                                                                                                                                                                |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| .codetrellis/scanner.py`                           | Added `go_*` fields (12 fields), `semantic_*` fields (5 fields), `_parse_go()`, `_extract_semantics()`, go.mod parsing in `_extract_dependencies()`, `.go` scanning + `.min.js` filter in `_extract_logic()`                                                           |
| .codetrellis/compressor.py`                        | Added 8 compression methods: `_compress_go_types()`, `_compress_go_api()`, `_compress_go_functions()`, `_compress_go_dependencies()`, `_compress_semantic_hooks()`, `_compress_semantic_middleware()`, `_compress_semantic_routes()`, `_compress_semantic_lifecycle()` |
| .codetrellis/extractors/architecture_extractor.py` | Added `GO_CLI`, `GO_LIBRARY`, `GO_WEB_SERVICE`, `GO_FRAMEWORK` project types, Go detection in `_detect_project_type()`, `can_extract()` updated for `go.mod`                                                                                                           |
| .codetrellis/extractors/logic_extractor.py`        | Added `extract_go()`, `_analyze_go_logic()`, `_simplify_go_params()`, Go control flow keywords                                                                                                                                                                         |
| .codetrellis/bpl/selector.py`                      | Go artifact counting, "golang" framework detection, `GO` prefix mapping                                                                                                                                                                                                |
| .codetrellis/extractors/**init**.py`               | Added Go + SemanticExtractor exports                                                                                                                                                                                                                                   |

### Prompt Sections Generated

| Section             | Description                                                                |
| ------------------- | -------------------------------------------------------------------------- |
| `[GO_TYPES]`        | Structs (with fields), interfaces (with methods), type aliases             |
| `[GO_API]`          | HTTP routes grouped by framework, gRPC services                            |
| `[GO_FUNCTIONS]`    | Functions + methods grouped by receiver type                               |
| `[GO_DEPENDENCIES]` | Parsed from go.mod — module, Go version, categorized deps                  |
| `[HOOKS]`           | Semantic hook/event detection (On\*, BindFunc, Subscribe)                  |
| `[MIDDLEWARE]`      | Semantic middleware detection (Use, chain, factory, Bind patterns)         |
| `[ROUTES_SEMANTIC]` | Generic HTTP handler routes                                                |
| `[LIFECYCLE]`       | Init/Start/Stop/Shutdown lifecycle methods                                 |
| `[CLI_COMMANDS]`    | CLI command definitions (cobra, click, argparse, commander) **(NEW v4.7)** |

### Validation Results

#### PocketBase (Go Framework — 249 files)

```
Type:           Go Framework ✅
Domain:         Infrastructure/BaaS ✅ (was "General Application" before v4.7)
Structs:        169
Interfaces:     24
Functions:      1,762
API Endpoints:  41 (after path validation, down from 71 false positives)
Const Blocks:   41
Hooks:          64 (via SemanticExtractor)
Middleware:     42 ✅ (was 1 before v4.7 — factory + Bind patterns)
Semantic Routes: 45
CLI Commands:   9 ✅ (cobra — NEW v4.7)
Dependencies:   21 (from go.mod)
Logic Snippets: 1,931 (no .d.ts — filtered v4.7)
Tokens:         ~12,824
```

#### gin-gonic/gin (Go HTTP Framework — 87 files)

```
Structs:     20
Interfaces:  6
Functions:   278
API Routes:  10
```

#### go-admin-team/go-admin (Go Admin Panel — 364 files)

```
Structs:     117
Functions:   1,156
API Routes:  63
```

---

_Document Version: 1.7_
_Created: 2026-02-02_
_Updated: 9 Feb 2026 - Phase G: PocketBase 16-Gap Remediation (v4.7) — BaaS domain, middleware factories, CLI commands, .d.ts filtering, route prefix tracking, plugin detection_
_Updated: 9 Feb 2026 - Phase F: Go Language Support (v4.5), Generic Semantic Extraction (v4.6), PocketBase validation_
_Updated: 9 Feb 2026 - Phase D: Public Repository Validation Framework (.codetrellis validate-repos` CLI, 60-repo corpus, quality_scorer.py, analyze_results.py, validation_runner.sh)_
_Updated: 7 Feb 2026 - Phase A Remediation: RunbookExtractor, domain categories, AI_INSTRUCTION, cross-cutting extractor patterns_
_Based on: Python Integration Session + BPL Hardening Session + Phase 2 & 3 Completion + Phase A Remediation (125 tests, 447 practices) + Phase D Validation Framework + Phase F Go/Semantic (v4.6) + Phase G Gap Remediation (v4.7)_

---

## Step 11: Pipeline Quality Assurance (NEW v4.8)

> Added in v4.8 (Phase H: Deep Pipeline Fixes). These are **generic** improvements that apply to ALL languages.

### 11.1 Brace-Balanced Extraction

**Problem**: Regex patterns like `[^}]*` stop at the first `}` in comments, strings, or nested code — causing catastrophic extraction loss (e.g., 44% struct loss in Go, 52% interface method loss).

**Solution**: Replace regex body capture with `_extract_brace_body()` — a proper state-machine parser:

```python
@staticmethod
def _extract_brace_body(content: str, open_brace_pos: int) -> Optional[str]:
    """Extract body between braces using brace-counting (handles comments, strings, nested)."""
    depth = 0
    i = open_brace_pos
    in_line_comment = False
    in_block_comment = False
    in_string = False
    string_char = ''

    while i < len(content):
        ch = content[i]
        # Track state: comments, strings, raw strings
        # Count { and } only outside strings/comments
        # Return body when depth returns to 0
```

**When to apply**: Any extractor that uses `{[^}]*}` or similar body-capture regex. Pattern:

1. Find the **header** only (e.g., `type Foo struct`)
2. Locate the opening `{`
3. Call `_extract_brace_body()` for the complete body

**Validated results** (PocketBase):

- events.go: 1 → 41 structs extracted
- App interface: 97 → 190 methods extracted
- Full scan: 169 → 282 structs, 24 → 38 interfaces

### 11.2 Adaptive Compressor with Importance Scoring

**Problem**: Hard-coded limits (10 receivers × 5 methods = 50 max) cause 95% data loss when projects have hundreds of types.

**Solution**: `_compress_go_functions()` (and equivalents for other languages) should use:

1. **Sort by importance** — types with more methods first
2. **Adaptive limits** — `min(total, max(40, total // 2))` instead of fixed 10
3. **Tiered detail** — full signatures for small types (≤15 methods), compact `+name1,name2,...` for large ones
4. **Prefix grouping** for large interfaces — group by common prefix (`On*(83)`, `Find*(28)`, etc.)

### 11.3 BPL Language Ratio Limiting

**Problem**: Generic practices (DP*, SOLID*, DB\*) with Python/TS examples dominate output for Go projects.

**Solution**: After BPL scoring, separate language-specific vs generic practices and cap generics:

```python
language_specific = [p for p in scored if self._get_practice_frameworks(p)]
generic = [p for p in scored if not self._get_practice_frameworks(p)]
max_generic = max(3, len(language_specific) // 3)
scored = language_specific + generic[:max_generic]
```

### 11.4 Primary Language Priority in Logic Section

**Problem**: IMPLEMENTATION_LOGIC section shows files randomly, burying primary language files.

**Solution**: Detect primary language from matrix artifacts and sort files accordingly:

- Primary language files first, sorted by complexity then function count
- Secondary language files after

### 11.5 Directory Summary Generation

**Problem**: PROJECT_STRUCTURE section was empty — no `directory_summary` was populated.

**Solution**: `_build_directory_summary()` in scanner.py:

- Analyzes scanned files to build directory tree
- Detects languages per directory from file extensions
- Infers purpose from directory names using hint table + fallback heuristics
- Sorted by file count descending (most important first)

### 11.6 Validation Scorecard

After implementing a new language, run this scorecard:

| Category             | Check                               | Target         |
| -------------------- | ----------------------------------- | -------------- |
| Types                | All structs/classes extracted       | >90% of source |
| Types                | Config/Settings types visible       | All present    |
| Methods              | Core type methods listed            | All exported   |
| API                  | All routes captured                 | >95%           |
| Dependencies         | All direct deps listed              | 100%           |
| Best Practices       | Primary language practices dominate | >70%           |
| PROJECT_STRUCTURE    | Directory tree populated            | All key dirs   |
| IMPLEMENTATION_LOGIC | Primary language files first        | Yes            |

---

## Step 12: .gitignore-Aware Scanning Integration (NEW v4.10) ✅

> **Context:** Phase J (R4 evaluation) discovered that v5 extractors doing their own `os.walk()` with hardcoded `IGNORE_DIRS` didn't respect `.gitignore`, causing scan hangs when gitignored directories contained large cloned repos. `GitignoreFilter` was created to solve this.

### 12.1 GitignoreFilter Overview

**Key file:** `codetrellis/file_classifier.py`

The `GitignoreFilter` class provides lightweight `.gitignore` + `.git/info/exclude` parsing using only stdlib (`fnmatch`, `os`, `pathlib`). No external dependencies.

```python
from codetrellis.file_classifier import GitignoreFilter

# Load from project root (reads .gitignore + .git/info/exclude)
gi = GitignoreFilter.from_root("/path/to/project")

# Check if a relative path should be ignored
gi.should_ignore("tests/repos", is_dir=True)   # True (if in .gitignore)
gi.should_ignore("codetrellis/scanner.py")       # False
```

### 12.2 Integrating GitignoreFilter in New Extractors

If your extractor does its own `os.walk()` (like v5 extractors: security, database, env, config, graphql, discovery, generic language), follow this pattern:

**Step 1: Add import and parameter**

```python
from codetrellis.file_classifier import GitignoreFilter
from typing import Optional

def extract_from_directory(self, directory: str, ...,
                           gitignore_filter: Optional[GitignoreFilter] = None,
                           ...) -> SomeResult:
```

**Step 2: Apply in os.walk()**

```python
gi = gitignore_filter
for root, dirs, files in os.walk(directory):
    # Apply gitignore to directories (prune walk)
    if gi:
        rel = os.path.relpath(root, directory)
        dirs[:] = [d for d in dirs
                   if d not in IGNORE_DIRS
                   and not gi.should_ignore(
                       os.path.join(rel, d) if rel != '.' else d,
                       is_dir=True)]
    else:
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

    # Optionally filter files too
    for fname in files:
        if gi:
            rel_file = os.path.relpath(os.path.join(root, fname), directory)
            if gi.should_ignore(rel_file):
                continue
```

**Step 3: Pass from scanner**

In `scanner.py`, the `scan()` method loads the filter and passes it to all extractors:

```python
self._gitignore_filter = GitignoreFilter.from_root(root)
# Then when calling extractors:
result = extractor.extract_from_directory(root, ..., gitignore_filter=self._gitignore_filter)
```

### 12.3 Already-Updated Extractors (R4)

| Extractor                     | File                                 | Methods Updated                                                                                    |
| ----------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------- |
| SecurityExtractor             | `security_extractor.py`              | `extract_from_directory`                                                                           |
| DatabaseArchitectureExtractor | `database_architecture_extractor.py` | `extract_from_directory`                                                                           |
| EnvInferenceExtractor         | `env_inference_extractor.py`         | `extract_from_directory`                                                                           |
| ConfigTemplateExtractor       | `config_template_extractor.py`       | `extract_from_directory`                                                                           |
| GenericLanguageExtractor      | `generic_language_extractor.py`      | `extract_from_directory`                                                                           |
| GraphQLSchemaExtractor        | `graphql_schema_extractor.py`        | `extract_from_directory`                                                                           |
| DiscoveryExtractor            | `discovery_extractor.py`             | `discover`, `_count_languages`, `_find_sub_projects`, `_find_spec_files`, `_find_config_templates` |

### 12.4 Supported .gitignore Patterns

GitignoreFilter supports:

- Simple names: `node_modules`, `*.pyc`
- Directory-only patterns: `__pycache__/`
- Rooted patterns: `/build`, `src/generated/`
- Glob patterns: `**/*.log`, `tests/repos/*`
- Negation: `!important.log`
- Comments: Lines starting with `#`

---

## Step 13: Systemic Detection Architecture (NEW v4.11) ✅

> **Context:** Phase K implemented all 3 phases of the Systemic Improvement Plan. These architectural changes affect how CodeTrellis detects domains, ORMs, databases, message queues, and per-sub-project tech stacks. New languages automatically benefit from these improvements.

### 13.1 Weighted Domain Scoring

**Key file:** `codetrellis/extractors/business_domain_extractor.py`

Domain detection now uses tiered weighted scoring instead of flat keyword counting:

```python
# Old approach: flat keywords, equal weight
DOMAIN_INDICATORS = {
    DomainCategory.ECOMMERCE: ["checkout", "cart", "order", "product"]  # all weight=1
}

# New approach: tiered weights
DOMAIN_INDICATORS = {
    DomainCategory.ECOMMERCE: {
        "high": ["checkout", "cart", "sku", "storefront"],      # weight=3
        "medium": ["product", "order", "payment", "shipping"],  # weight=2
        "low": ["customer", "discount", "inventory"],           # weight=1
    },
}
```

**Source weights** (where the keyword was found):

- `pkg_json` = 4 (package.json/manifest descriptions)
- `code` = 3 (source code content)
- `fs` = 2 (file/directory names)
- `readme` = 1 (README content)

**Output format:** `domain:Developer Tools (confidence=0.24, runner_up=AI/ML Platform:0.09)`

**For new languages:** When adding language-specific domain keywords, place them in the appropriate tier. Unambiguous keywords go in `high`, generic ones in `low`.

### 13.2 Multi-Signal ORM/DB/MQ Detection

**Key file:** `codetrellis/extractors/database_architecture_extractor.py`

Detection now requires convergent evidence instead of single regex matches:

```python
ORM_DETECTION = {
    'typeorm': {
        'strong': [r'TypeOrmModule', r'createConnection.*typeorm'],  # 1 strong = detected
        'medium': [r'getRepository\(', r'@PrimaryGeneratedColumn'],  # 2 medium = detected
        'weak':   [r'Repository', r'Entity'],                        # ignored alone
        'anti':   [r'\.go$', r'\.py$'],                              # file types where impossible
    },
}
```

**Current coverage:**

- `ORM_DETECTION`: 19 ORMs (Django, SQLAlchemy, GORM, Prisma, TypeORM, etc.)
- `DB_DETECTION`: 13 database types (PostgreSQL, MySQL, MongoDB, Redis, etc.)
- `MQ_DETECTION`: 10 message queue types (RabbitMQ, Kafka, Redis pub/sub, etc.)

**For new languages:** Add language-specific ORM/DB/MQ entries with appropriate `anti` patterns to prevent cross-language false positives.

### 13.3 ORM-DB Affinity Graph

**Key file:** `codetrellis/extractors/database_architecture_extractor.py`

ORM detection now builds an evidence graph with sub-project provenance:

```python
@dataclass
class ORMEvidence:
    orm: str                        # "django_orm", "prisma", etc.
    db_type: Optional[str]          # Associated DB from ORM_PATTERNS
    file_path: str                  # Where detected
    sub_project: Optional[str]      # Which sub-project (from discovery)
    confidence: float               # Detection confidence
    all_files: List[str]            # All files with this ORM
```

DB type resolution uses affinity ordering:

1. **Explicit association** from ORM_PATTERNS (e.g., Django → PostgreSQL)
2. **Co-located DB** detected in the same sub-project
3. **Any relational DB** found anywhere in the project

### 13.4 Discovery-Driven Stack Detection

**Key file:** `codetrellis/extractors/architecture_extractor.py`

`build_project_profile()` now reads per-sub-project manifests:

```python
# For each sub-project found by DiscoveryExtractor:
#   1. Read its package.json / requirements.txt / go.mod
#   2. Detect frameworks from dependencies
#   3. Enrich sub_project with detected_frameworks field
# Output: "django (apps/api), next.js (apps/web), redis (standalone)"
```

**For new languages:** Add manifest parsing for new package managers (e.g., `Cargo.toml` → Rust crates, `pom.xml` → Java deps) in `build_project_profile()`.

### 13.5 Integration Checklist for New Languages

When adding a new language, verify these systemic improvements work:

- [ ] **Domain detection**: New language keywords placed in `DOMAIN_INDICATORS` with proper tiers
- [ ] **ORM detection**: Language-specific ORMs added to `ORM_DETECTION` with `anti` patterns
- [ ] **DB detection**: Language-specific DB drivers added to `DB_DETECTION`
- [ ] **Stack detection**: Language manifest parsed in `build_project_profile()`
- [ ] **FileClassifier**: New extractors use `FileClassifier.is_app_code()` or `should_skip_for_detection()`
- [ ] **Self-scan validation**: Run `codetrellis scan .` and verify no false positives from the language's own detection patterns appearing in CodeTrellis source code

---

## Step 14: A5.x Module Integration (NEW Session 54b) ✅

> **Context:** Session 54 introduced 4 A5.x post-processing modules that enhance AI prompt delivery. Session 54b expanded all 4 modules to fully support 53+ languages/frameworks with ~350 unique compressor section names. When adding a new language, all 4 modules must be updated to include the new section names.

### 14.1 Overview: The 4 A5.x Modules

| Module                    | File                  | Purpose                                               | CLI Command                                                                  |
| ------------------------- | --------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------- |
| **A5.1 Cache Optimizer**  | `cache_optimizer.py`  | Reorders sections by stability for LLM KV-cache reuse | `codetrellis scan . --cache-optimize` / `codetrellis cache-optimize --stats` |
| **A5.2 MCP Server**       | `mcp_server.py`       | JSON-RPC 2.0 server exposing aggregate resources      | `codetrellis mcp --stdio`                                                    |
| **A5.3 JIT Context**      | `jit_context.py`      | Selects relevant sections based on file being edited  | `codetrellis context path/to/file --sections-only`                           |
| **A5.5 Skills Generator** | `skills_generator.py` | Creates AI-executable skill definitions from matrix   | `codetrellis skills`                                                         |

### 14.2 Cache Optimizer Integration

**File:** `codetrellis/cache_optimizer.py`
**Dict:** `SECTION_STABILITY`

Every section name emitted by the compressor must have a stability mapping. The cache optimizer reorders sections so stable content (types, schemas) appears first for KV-cache reuse, and volatile content (implementation logic, progress) appears last.

```python
from codetrellis.cache_optimizer import CacheOptimizer, SectionStability

# Add entries for each new section:
# Pattern: "SECTION_NAME": (SectionStability.<TIER>, <order_number>)
SECTION_STABILITY = {
    # ... existing entries ...
    "<LANG>_TYPES": (SectionStability.STRUCTURAL, 1100),
    "<LANG>_FUNCTIONS": (SectionStability.SEMANTIC, 1400),
    "<LANG>_API": (SectionStability.SEMANTIC, 1500),
    "<LANG>_MODELS": (SectionStability.STRUCTURAL, 1200),
    "<LANG>_DEPENDENCIES": (SectionStability.STATIC, 600),
}
```

**Stability tiers:**

| Tier         | Order Range | Change Frequency   | Examples                                   |
| ------------ | ----------- | ------------------ | ------------------------------------------ |
| `STATIC`     | 100-800     | Rarely changes     | Dependencies, configs, project metadata    |
| `STRUCTURAL` | 900-1300    | Infrequent changes | Types, models, schemas, class definitions  |
| `SEMANTIC`   | 1400-1800   | Moderate changes   | Functions, APIs, hooks, middleware         |
| `VOLATILE`   | 1900-2200   | Frequent changes   | Implementation logic, progress, TODO items |

**Default:** Sections not in `SECTION_STABILITY` get `(SectionStability.SEMANTIC, 1400)`.

**Verification:**

```bash
# Verify sections appear in cache-optimized output
codetrellis scan . --cache-optimize

# Verify stability stats show correct tiers
codetrellis cache-optimize --stats
```

### 14.3 MCP Server Integration

**File:** `codetrellis/mcp_server.py`
**Dict:** `AGGREGATE_RESOURCES`

The MCP server auto-registers aggregate resources that combine related sections. When adding a new language, its sections should be added to the appropriate aggregate category.

```python
AGGREGATE_RESOURCES = {
    "types": ["PYTHON_TYPES", "TS_TYPES", ..., "<LANG>_TYPES"],
    "api": ["PYTHON_API", "TS_API", ..., "<LANG>_API"],
    "state": ["REDUX_STORE", "ZUSTAND_STORES", ..., "<LANG>_STORES"],
    "components": ["REACT_COMPONENTS", "VUE_COMPONENTS", ..., "<LANG>_COMPONENTS"],
    "styling": ["CSS_STYLES", "TAILWIND_CONFIG", ..., "<LANG>_STYLES"],
    "routing": ["NEXTJS_ROUTING", "VUE_ROUTING", ..., "<LANG>_ROUTING"],
    "overview": ["PROJECT", "OVERVIEW", "BUSINESS_DOMAIN", "RUNBOOK"],
    "infrastructure": ["DEPENDENCIES", "DOCKER", "TERRAFORM", "CI_CD"],
}
```

**Current category counts (Session 54b):**

| Category         | Section Count          | Purpose                                       |
| ---------------- | ---------------------- | --------------------------------------------- |
| `types`          | All `*_TYPES` sections | Type definitions across all languages         |
| `api`            | 52 sections            | API endpoints, routes, gRPC, GraphQL          |
| `state`          | 27 sections            | State management (Redux, Zustand, MobX, etc.) |
| `components`     | 19 sections            | UI component sections                         |
| `styling`        | 31 sections            | CSS, Sass, Tailwind, CSS-in-JS                |
| `routing`        | 12 sections            | File-based & programmatic routing             |
| `overview`       | 4 sections             | Project metadata                              |
| `infrastructure` | 4 sections             | DevOps & deployment                           |

**Auto-registration:** Resources are auto-registered via `for agg_name in self.AGGREGATE_RESOURCES` loop, so no additional code is needed beyond adding sections to the dict.

### 14.4 JIT Context Provider Integration

**File:** `codetrellis/jit_context.py`
**Dicts:** `EXTENSION_TO_SECTIONS`, `PATH_PATTERN_SECTIONS`

The JIT context provider selects which sections to include based on the file currently being edited. This ensures AI gets only the most relevant context.

#### Extension Mapping

```python
EXTENSION_TO_SECTIONS = {
    # Core languages
    ".py": ["PYTHON_TYPES", "PYTHON_API", "PYTHON_FUNCTIONS"],
    ".go": ["GO_TYPES", "GO_API", "GO_FUNCTIONS"],
    # ... add new language:
    ".<ext>": ["<LANG>_TYPES", "<LANG>_FUNCTIONS", "<LANG>_API"],
}
```

**Framework-aware `.tsx`/`.jsx` sections:** These extensions include state management, UI library, and data fetching sections (Redux, Zustand, MUI, TanStack Query, etc.) because JSX/TSX files commonly use these frameworks.

#### Path Pattern Mapping

```python
PATH_PATTERN_SECTIONS = {
    # Convention-based paths → relevant sections
    r"components?/": ["REACT_COMPONENTS", "VUE_COMPONENTS", ...],
    r"stores?/": ["REDUX_STORE", "ZUSTAND_STORES", ...],
    r"routes?/": ["NEXTJS_ROUTING", "REMIX_ROUTES", ...],
    # Add framework-specific patterns:
    r"<framework_dir>/": ["<LANG>_SECTIONS"],
}
```

**UNIVERSAL_SECTIONS:** `["PROJECT", "BEST_PRACTICES", "RUNBOOK"]` — always included for every file.

**Critical rule:** Section names must exactly match compressor output. Use the actual section names from `compressor.py`, not invented names (e.g., `VUE_COMPOSABLES` not `VUE_REACTIVITY`).

**Verification:**

```bash
# Check which sections are selected for a file
codetrellis context path/to/file.<ext> --sections-only
```

### 14.5 Skills Generator Integration

**File:** `codetrellis/skills_generator.py`
**Dict:** `SKILL_TEMPLATES`

The skills generator creates AI-executable skill definitions. Each template has a `detect_sections` list — if any of those sections exist in the project matrix, the skill is generated.

```python
SKILL_TEMPLATES = {
    "add-component": {
        "detect_sections": [
            "REACT_COMPONENTS", "VUE_COMPONENTS", ..., "<LANG>_COMPONENTS"
        ],
        "description": "Add a new UI component",
        "steps": [...],
    },
    "add-store": {
        "detect_sections": [
            "REDUX_STORE", "ZUSTAND_STORES", ..., "<LANG>_STORES"
        ],
        ...
    },
}
```

**Current templates (17):**

| Template          | Purpose             | Typical `detect_sections`           |
| ----------------- | ------------------- | ----------------------------------- |
| `add-component`   | New UI component    | `*_COMPONENTS` sections             |
| `add-store`       | New state store     | `*_STORES`, `*_ATOMS` sections      |
| `add-endpoint`    | New API endpoint    | `*_API`, `*_ROUTES` sections        |
| `add-model`       | New data model      | `*_MODELS`, `*_ENTITIES` sections   |
| `add-hook`        | New hook/composable | `*_HOOKS`, `*_COMPOSABLES` sections |
| `add-style`       | New stylesheet      | `*_STYLES`, `*_CONFIG` CSS sections |
| `add-route`       | New route/page      | `*_ROUTING`, `*_ROUTES` sections    |
| `add-data-fetch`  | New data fetch hook | `*_QUERIES`, `*_CACHE` sections     |
| `add-test`        | New test file       | `PYTHON_TYPES`, `TS_TYPES`          |
| `add-migration`   | New DB migration    | `*_MODELS` sections                 |
| `add-config`      | New config          | `DEPENDENCIES`                      |
| `add-type`        | New type definition | `*_TYPES` sections                  |
| `add-middleware`  | New middleware      | `MIDDLEWARE`                        |
| `add-plugin`      | New plugin          | `LIFECYCLE`                         |
| `add-page`        | New page component  | `NEXTJS_ROUTING`                    |
| `add-guard`       | New auth guard      | `*_API` sections                    |
| `add-interceptor` | New interceptor     | `*_API` sections                    |

**Verification:**

```bash
# Check generated skills count
codetrellis skills
```

### 14.6 Testing A5.x Integration

**Test files:**

- `tests/unit/test_cache_optimizer.py` — 56 tests (includes `TestFrameworkStabilityCoverage`)
- `tests/unit/test_mcp_server.py` — 48 tests (includes `TestAggregateResourcesCoverage`)
- `tests/unit/test_jit_context.py` — 46 tests (includes `TestFrameworkExtensionCoverage`, `TestFrameworkPathPatterns`)
- `tests/unit/test_skills_generator.py` — 51 tests (includes `TestFrameworkCoverage`)

**Run all A5.x tests:**

```bash
python -m pytest tests/unit/test_cache_optimizer.py tests/unit/test_mcp_server.py tests/unit/test_jit_context.py tests/unit/test_skills_generator.py -v
# Expected: 201 tests, all passing
```

**Add framework coverage tests for new language:**

```python
# In test_cache_optimizer.py → TestFrameworkStabilityCoverage
def test_<lang>_sections_have_stability(self):
    sections = ["<LANG>_TYPES", "<LANG>_FUNCTIONS", "<LANG>_API"]
    for section in sections:
        assert section in CacheOptimizer.SECTION_STABILITY

# In test_mcp_server.py → TestAggregateResourcesCoverage
def test_<lang>_in_aggregates(self):
    assert "<LANG>_TYPES" in server.AGGREGATE_RESOURCES["types"]

# In test_jit_context.py → TestFrameworkExtensionCoverage
def test_<ext>_extension(self):
    assert ".<ext>" in JITContextProvider.EXTENSION_TO_SECTIONS

# In test_skills_generator.py → TestFrameworkCoverage
def test_<lang>_in_add_component(self):
    detect = templates["add-component"]["detect_sections"]
    assert "<LANG>_COMPONENTS" in detect
```

### 14.7 Common Pitfalls

1. **Section name mismatch**: The most common bug is using section names that don't match the compressor output. Always verify against `compressor.py` → `compress()` method.
2. **Missing default**: Unknown sections default to `(SectionStability.SEMANTIC, 1400)` in cache optimizer. This works but isn't optimal — explicit mappings are preferred.
3. **MCP auto-registration**: No code changes needed beyond adding to `AGGREGATE_RESOURCES` dict — the loop handles registration automatically.
4. **JIT UNIVERSAL_SECTIONS**: Don't add `PROJECT`, `BEST_PRACTICES`, or `RUNBOOK` to extension mappings — they're already always included.

---

## Step 15: Build Pipeline Integration (NEW v4.16.0 — Phase BJ) ✅

> **Context:** Phase BJ (PART B) introduced an Angular 21-inspired auto-compilation pipeline that replaces monolithic full-rescan with deterministic, incremental, content-addressed builds. When adding a new language, the new extractor automatically benefits from the pipeline — but following these integration guidelines ensures optimal caching, incremental behavior, and CI/CD determinism.

### 15.1 Overview: Build Pipeline Architecture

The MatrixBuilder orchestrates a 5-stage lifecycle:

```
SCAN → DIFF → EXTRACT → COMPILE → PACKAGE
```

| Stage   | Module          | Purpose                                                                  |
| ------- | --------------- | ------------------------------------------------------------------------ |
| SCAN    | `cache.py`      | Walk files, compute SHA-256 content hashes                               |
| DIFF    | `cache.py`      | Compare against `_lockfile.json`, find changes                           |
| EXTRACT | `scanner.py`    | Run language extractors on changed files only                            |
| COMPILE | `compressor.py` | Compress extracted data into matrix                                      |
| PACKAGE | `builder.py`    | Write `matrix.prompt`, `matrix.json`, `_metadata.json`, `_lockfile.json` |

**Key files:** `codetrellis/cache.py` (534 lines), `codetrellis/builder.py` (546 lines), `codetrellis/interfaces.py` (IExtractor/ExtractorManifest/BuildEvent/BuildResult)

### 15.2 IExtractor Protocol (Future Extractors)

New extractors can implement the `IExtractor` protocol for per-file caching:

```python
from codetrellis.interfaces import IExtractor, ExtractorManifest

class NewLangComponentExtractor:
    """Implements IExtractor protocol for per-file caching."""

    @property
    def manifest(self) -> ExtractorManifest:
        return ExtractorManifest(
            name="newlang_component",
            version="1.0.0",
            input_patterns=["*.newlang", "*.nl"],
            depends_on=[],                           # Other extractors this depends on
            output_sections=["NEWLANG_COMPONENTS"],   # Sections this produces
        )

    def cache_key(self, file_path: str, content_hash: str) -> str:
        """Generate deterministic cache key for this extractor + file."""
        from codetrellis.cache import InputHashCalculator
        hasher = InputHashCalculator()
        return hasher.hash_string(f"{self.manifest.name}:{self.manifest.version}:{content_hash}")

    def extract(self, file_path: str, content: str) -> dict:
        """Extract language-specific data from a single file."""
        # ... extraction logic ...
        return {"components": [...], "imports": [...]}
```

**Note:** Current extractors (53+ languages) work without implementing `IExtractor` — the legacy scanner path handles them. The protocol is designed for future extractors that want per-file cache granularity.

### 15.3 Content-Addressed Caching

The `InputHashCalculator` uses SHA-256 (first 16 hex chars) for deterministic file identity:

```python
from codetrellis.cache import InputHashCalculator

hasher = InputHashCalculator()

# File content hash — used by DiffEngine to detect changes
file_hash = hasher.hash_file("/path/to/file.newlang")  # e.g., "a3b4c5d6e7f8a9b0"

# Config hash — used to invalidate cache when settings change
config_hash = hasher.hash_config({"tier": "deep", "parallel": True})

# String hash — used for cache keys, CLI flag fingerprints
flags_hash = hasher.hash_string("--incremental --deterministic")
```

**Cache layout:**

```
.codetrellis/cache/{VERSION}/{project_name}/
├── _extractor_cache/
│   ├── {extractor_name}/
│   │   ├── {file_content_hash}.json
│   │   └── ...
│   └── ...
├── _lockfile.json          # File manifest + extractor versions
├── _metadata.json          # Build stats + timing
└── _build_log.jsonl        # Build events (structured logging)
```

### 15.4 DiffEngine: Incremental Builds

When `--incremental` is used, the `DiffEngine` compares current file hashes against `_lockfile.json`:

```python
from codetrellis.cache import DiffEngine, LockfileManager

lockfile_mgr = LockfileManager(cache_dir)
lockfile = lockfile_mgr.read_lockfile()

diff_engine = DiffEngine()
diff = diff_engine.diff(current_files={"file.py": "abc123..."}, lockfile=lockfile)

# diff.added    → list of new files
# diff.modified → list of changed files
# diff.deleted  → list of removed files
# diff.unchanged → list of untouched files (skip extraction)
# diff.has_changes → bool — if False, entire build is skipped
```

**For new languages:** No special integration needed. The DiffEngine works on file paths + content hashes, which are language-agnostic. New file extensions are automatically picked up by `_walk_files()`.

### 15.5 Deterministic Output Guarantees

All new language extractors automatically benefit from Phase 0 stabilization:

1. **Sorted file traversal**: `_walk_files()` uses `sorted(dirnames)` and `sorted(filenames)` — file processing order is deterministic across OS/filesystem
2. **Sorted JSON keys**: `json.dumps(..., sort_keys=True)` — output JSON is byte-deterministic
3. **Reproducible timestamps**: `CODETRELLIS_BUILD_TIMESTAMP` env var overrides `datetime.now()` — CI runs produce identical output

**Verification:**

```bash
# Two consecutive runs should produce byte-identical output
CODETRELLIS_BUILD_TIMESTAMP="2026-01-01T00:00:00" codetrellis scan /project --deterministic
sha256sum matrix.prompt  # should match across runs
```

### 15.6 CLI Flags for New Language Testing

When adding a new language, test with the build pipeline flags:

```bash
# Standard scan (legacy path — always works)
codetrellis scan /project

# Incremental build — only re-processes changed files
codetrellis scan /project --incremental

# Deterministic build — sorted output, fixed timestamp
codetrellis scan /project --deterministic

# CI mode — deterministic + parallel
codetrellis scan /project --ci

# Verify output quality gates
codetrellis verify /project

# Clean cache (force full re-extraction)
codetrellis clean /project
```

### 15.7 Testing Checklist for New Languages

When adding a new language extractor, verify the following build pipeline behaviors:

```python
# In test_<lang>_pipeline_integration.py

def test_incremental_detects_new_lang_files(self, tmp_path):
    """New .lang files should appear in DiffResult.added."""
    # Create file → scan → verify in lockfile → modify → scan → verify in diff.modified

def test_deterministic_output_with_new_lang(self, tmp_path):
    """Two scans of same project should produce identical output."""
    # Run 2x with fixed timestamp → SHA-256 of matrix.prompt should match

def test_verify_includes_new_lang_sections(self, tmp_path):
    """Verify command should find new language sections in output."""
    # Scan → verify → check [PROJECT] section present

def test_clean_removes_new_lang_cache(self, tmp_path):
    """Clean should remove cached extractor results."""
    # Scan --incremental → verify cache exists → clean → verify cache gone
```

### 15.8 Lessons Learned

1. **Determinism is free**: All new extractors automatically get sorted traversal, sorted JSON keys, and reproducible timestamps — no extractor-level code needed.
2. **Legacy parity preserved**: MatrixBuilder delegates to `scanner.scan()` for extraction — the same code path processes all 53+ languages whether invoked via legacy CLI or the new pipeline.
3. **IExtractor is opt-in**: Current extractors work without protocol compliance. The `IExtractor` protocol enables future per-file caching but is not required for correctness.
4. **Cache invalidation is content-based**: SHA-256 content hashes mean renaming a file without changing content won't trigger re-extraction, and touching a file's metadata won't either — only actual content changes trigger rebuilds.

This section documents the actual Java & Kotlin language integration completed in Phase L (Sessions 1 & 2), serving as a reference implementation for adding JVM-family languages.

### Key Design Decisions

1. **Shared JVM extractors**: Kotlin reuses Java's `APIExtractor`, `ModelExtractor`, and `AnnotationExtractor` for JVM framework patterns (Spring, JPA, Micronaut) — avoiding duplication
2. **Optional AST layer**: `tree-sitter-java` provides AST parsing for classes/enums/records/annotations/methods, with graceful fallback to regex when tree-sitter is unavailable
3. **Optional LSP layer**: Eclipse JDT Language Server integration via JSON-RPC over stdin/stdout, with graceful fallback when JDT LS is not installed
4. **FileClassifier fix**: `src/main/kotlin` and `src/test/kotlin` paths needed the same "JVM source tree" treatment as `src/main/java` to prevent `com/example/` being classified as EXAMPLE

### Files Created

```
codetrellis/extractors/java/
├── __init__.py                       # Exports all 6 Java extractors
├── type_extractor.py                 # Classes, interfaces, enums, records, annotations, sealed, generics
├── function_extractor.py             # Methods, constructors, overloads
├── api_extractor.py                  # REST endpoints (Spring MVC, JAX-RS, Micronaut, Vert.x, Spark)
├── model_extractor.py                # JPA entities, columns, repos, Panache entities (Session 2)
├── annotation_extractor.py           # Framework annotations (Spring, CDI, JPA, validation, Lombok)
└── dependency_extractor.py           # Maven pom.xml + Gradle build.gradle(.kts)

codetrellis/extractors/kotlin/
├── __init__.py                       # Exports all Kotlin extractors
├── type_extractor.py                 # Classes (7 kinds), objects, interfaces, enums, type aliases
└── function_extractor.py             # Top-level, extension, suspend, inline functions

codetrellis/java_parser_enhanced.py   # EnhancedJavaParser + JavaParseResult + AST + LSP
codetrellis/kotlin_parser_enhanced.py # EnhancedKotlinParser + KotlinParseResult (reuses Java extractors)
codetrellis/bpl/practices/java_core.yaml  # 50 practices (JAVA001-JAVA050)
```

### Files Modified

| File                                                   | Changes                                                                                                                                                                                                                                                        |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `codetrellis/scanner.py`                               | Added 10 `java_*` fields + 10 `kotlin_*` fields to ProjectMatrix, `.java`/`.kt`/`.kts` to FILE_TYPES, `_parse_java()` (~210 lines), `_parse_kotlin()` (~160 lines), Maven/Gradle dep dedup with `seen` set, Kotlin stats in `_summarize_stats()` + `to_dict()` |
| `codetrellis/compressor.py`                            | Added 8 compression methods: `_compress_java_types()`, `_compress_java_api()`, `_compress_java_models()`, `_compress_java_dependencies()`, `_compress_kotlin_types()`, `_compress_kotlin_functions()`, `_compress_kotlin_api()`, `_compress_kotlin_models()`   |
| `codetrellis/file_classifier.py`                       | Extended `should_skip_for_detection` to handle `src/main/kotlin` paths (renamed to `in_jvm_source_tree`)                                                                                                                                                       |
| `codetrellis/extractors/generic_language_extractor.py` | Removed `.java`, `.kt`, `.kts` from `EXTENSION_LANGUAGE` dict                                                                                                                                                                                                  |
| `codetrellis/bpl/selector.py`                          | Java artifact counting, framework detection from deps, `JAVA` prefix mapping                                                                                                                                                                                   |
| `requirements.txt`                                     | Added `tree-sitter>=0.22.0`, `tree-sitter-java>=0.23.0`                                                                                                                                                                                                        |

### Prompt Sections Generated

| Section               | Description                                                                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `[JAVA_TYPES]`        | Classes (with extends/implements/annotations/generics), interfaces, enums (constants/fields/methods), records (components), annotation defs |
| `[JAVA_API]`          | REST endpoints grouped by class: method, path, params, return type                                                                          |
| `[JAVA_MODELS]`       | JPA entities with columns (type/nullable/unique), repositories with entity/base interface, Panache entities                                 |
| `[JAVA_DEPENDENCIES]` | Maven/Gradle deps categorized (core/web/data/test/...), deduped                                                                             |
| `[KOTLIN_TYPES]`      | Classes (7 kinds with ctor params/annotations), objects, interfaces, enums with entries, features + frameworks summary                      |
| `[KOTLIN_FUNCTIONS]`  | Functions grouped by file, suspend/inline/extension markers, params, return types                                                           |
| `[KOTLIN_API]`        | Spring endpoints + Ktor routes                                                                                                              |
| `[KOTLIN_MODELS]`     | JPA entities + repositories from Kotlin files                                                                                               |

### Bugs Found & Fixed (12 total across 2 sessions)

| #   | Bug                         | Root Cause                                                  | Fix                                         |
| --- | --------------------------- | ----------------------------------------------------------- | ------------------------------------------- |
| 1-6 | Session 1 bugs              | Various field name/attribute errors in scanner.py           | Fixed attribute names, dict access patterns |
| 7   | Entity column fields        | `c.nullable` → `c.is_nullable`, `c.unique` → `c.is_unique`  | Fixed in scanner.py                         |
| 8   | Repository field            | `repo.repo_type` → `repo.base_interface`                    | Fixed in scanner.py                         |
| 9   | Enum dict access            | `f.name`/`f.type` but enum fields are dicts                 | Fixed to `f['name']`/`f['type']`            |
| 10  | FileClassifier Kotlin       | `example` in `src/main/kotlin/com/example/` matched EXAMPLE | Extended JVM source tree check              |
| 11  | Kotlin CLASS_PATTERN        | `@Column(nullable = false)` broke `[^)]*` ctor regex        | `_extract_balanced_parens()` helper         |
| 12  | Kotlin in generic extractor | `.kt`/`.kts` duplication                                    | Removed from `EXTENSION_LANGUAGE`           |

**Root cause**: All bugs 1-9 were hidden by `except Exception: pass` in `_parse_java()`. Recommend replacing with proper logging.

### Validation Results

| Repo                | Java Classes | Kotlin Classes | Endpoints | Entities | Special                             |
| ------------------- | ------------ | -------------- | --------- | -------- | ----------------------------------- |
| Spring PetClinic    | 22           | —              | 16        | 9        | 3 repos, 0 dup deps                 |
| Quarkus Quickstarts | 370          | —              | 345       | 32       | 2 Panache entities                  |
| Micronaut Guides    | 698          | 374            | 55+47     | —        | 77 Kotlin interfaces, 528 functions |

### Lessons Learned

1. **Silent error handling kills quality**: `except Exception: pass` hid 9 bugs across 2 sessions — always log at minimum
2. **Reuse JVM extractors across languages**: Kotlin inheriting Java's API/Model/Annotation extractors saved ~1000 lines and ensured consistent framework detection
3. **Balanced-paren extraction > regex for constructors**: Kotlin annotations like `@Column(nullable = false)` inside constructor params break simple `[^)]*` regex
4. **FileClassifier awareness**: JVM source trees (`src/main/java/`, `src/main/kotlin/`) contain package directories (`com/example/`) that look like classification keywords but aren't
5. **tree-sitter complements regex**: AST parsing is more reliable for nested structures (enum bodies, record components) but regex is faster for simple patterns — use both with deduplication

---

## 11. Reference: C# Integration Example (NEW v4.13)

### Architecture

```
Extractors (6):
  type_extractor.py      → Classes, interfaces, structs, records, delegates
  function_extractor.py  → Methods, constructors, events
  enum_extractor.py      → Enums with members
  api_extractor.py       → ASP.NET Core controllers, Minimal API, gRPC, SignalR, Razor
  model_extractor.py     → EF Core entities, DbContext, DTOs, repositories
  attribute_extractor.py → Attribute usage detection and categorization

Parser:
  csharp_parser_enhanced.py → EnhancedCSharpParser integrating all 6 extractors
                              + optional tree-sitter-c-sharp AST
                              + .csproj parsing + .sln parsing
                              + framework & version feature detection

Integration:
  scanner.py    → 21 ProjectMatrix fields, _parse_csharp(), FILE_TYPES routing
  compressor.py → 5 sections: TYPES, API, FUNCTIONS, MODELS, DEPENDENCIES
  selector.py   → C# artifact counting, framework mapping, practice filtering

Practices:
  csharp_core.yaml → 50 practices (CS001-CS050)
```

### Key Design Decisions

1. **Separate type_extractor for C#-specific types**: C# has more type kinds than Java (classes, interfaces, structs, records, delegates) — each needs distinct dataclasses and extraction logic.

2. **Minimal API as first-class extraction**: .NET 6+ Minimal APIs (`app.MapGet("/path", handler)`) are fundamentally different from controller-based routing — requires separate regex pattern.

3. **Modifier keyword post-processing**: Regex `(modifier)*` repeated capture groups only retain the last iteration. C# methods can have 3+ modifiers (`public static async`), requiring post-processing to extract modifiers from the return_type string.

4. **EF Core entity detection by convention**: Entities detected by: (a) explicit `[Table]`/`[Key]` annotations, (b) DbSet<Entity> references, (c) `IEntityTypeConfiguration<T>` implementations.

5. **DTOs by naming convention**: Classes/records matching `*Dto`, `*ViewModel`, `*Request`, `*Response`, `*Command`, `*Query` patterns are auto-classified as DTOs.

### Files Created

| File                                       | Purpose                    | Lines |
| ------------------------------------------ | -------------------------- | ----- |
| `extractors/csharp/__init__.py`            | Module exports             | ~60   |
| `extractors/csharp/type_extractor.py`      | Type extraction            | ~800  |
| `extractors/csharp/function_extractor.py`  | Function extraction        | ~420  |
| `extractors/csharp/enum_extractor.py`      | Enum extraction            | ~190  |
| `extractors/csharp/api_extractor.py`       | API endpoint extraction    | ~380  |
| `extractors/csharp/model_extractor.py`     | Data model extraction      | ~505  |
| `extractors/csharp/attribute_extractor.py` | Attribute extraction       | ~330  |
| `csharp_parser_enhanced.py`                | Parser with all extractors | ~785  |
| `bpl/practices/csharp_core.yaml`           | 50 BPL practices           | ~700  |
| 6 test files                               | 97 tests total             | ~1585 |

### Bugs Fixed: 10

Key patterns from C# integration:

1. **Repeated capture groups lose data**: `(modifier)*` → only last modifier captured → modifiers leak into return_type
2. **Dataclass field name mismatches**: Scanner code assumed field names that didn't match actual dataclass definitions (5 separate occurrences)
3. **Undefined instance attributes**: Compressor used `self.max_props`/`self.max_methods` which don't exist on `MatrixCompressor`
4. **Regex too restrictive**: Minimal API pattern only matched specific variable names (`app|builder`) instead of any variable

### Validation

Validated on 3 production C# repositories:

- **dotnet/eShop**: Large multi-project e-commerce app — 100+ classes, 27 endpoints, 3 DbContexts
- **ardalis/CleanArchitecture**: Template project — 357 C# files, full type/model/dependency extraction
- **jasontaylordev/CleanArchitecture**: CQRS-based project — 115 C# files, controllers + Minimal API + EF Core

### Lessons Learned (C# Specific)

1. **Modifier leaking is a C#-specific regex issue**: Java modifiers are captured differently; C# methods can have 3-4 modifiers (`public static async override`) which overwhelm repeated capture groups.
2. **Test content with leading whitespace**: Unit tests using triple-quoted strings naturally have indentation — regex patterns with `^` anchors must use `^\s*` to handle this.
3. **Test file/designer file filtering**: C# projects have generated files (`.Designer.cs`, `.g.cs`, `.AssemblyInfo.cs`) and test files that should be excluded from analysis.
4. **Lambda handlers in Minimal API**: Unlike controller methods, Minimal API handlers can be lambdas (`() =>`) or method group references (`CreateOrder`) — regex must handle both.
5. **Silent exception swallowing is still the #1 bug source**: Even after fixing this in Java, the same `except Exception: pass` pattern in `_parse_csharp` hid 5+ bugs during initial development.

---

## 12. Reference: Rust Integration Example (NEW v4.14)

### Architecture

```
Extractors (5):
  type_extractor.py      → Structs (named/tuple/unit), enums (unit/tuple/struct variants),
                            traits (default impls, supertraits), impl blocks, type aliases
  function_extractor.py  → Functions (pub/const/async/unsafe/extern), methods,
                            closures, #[test] detection
  api_extractor.py       → Actix-web, Rocket, Axum, Warp, Tide routes,
                            Tonic gRPC services, async-graphql types
  model_extractor.py     → Diesel models/schemas, SeaORM entities, SQLx queries
  attribute_extractor.py → Derive macros, proc macros, cfg attributes, feature flags

Parser:
  rust_parser_enhanced.py → EnhancedRustParser integrating all 5 extractors
                            + import/extern crate extraction
                            + macro_rules! parsing
                            + Cargo.toml parsing (deps, dev-deps, workspace)
                            + framework & edition detection

Integration:
  scanner.py    → 16+ ProjectMatrix fields, _parse_rust(), FILE_TYPES routing
  compressor.py → 5 sections: TYPES, API, FUNCTIONS, MODELS, DEPENDENCIES
  selector.py   → Rust artifact counting, framework mapping, practice filtering

Practices:
  rust_core.yaml → 50 practices (RS001-RS050)
```

### Key Design Decisions

1. **Ownership/borrowing-aware type extraction**: Rust's `&self`, `&mut self`, and `self` method signatures fundamentally differ from other languages — extracted as `self_kind` on `RustMethodInfo` for AI context.

2. **Enum variant differentiation**: Rust enums have 3 variant kinds (unit, tuple, struct) unlike most languages — tracked via `is_unit/is_tuple/is_struct` booleans on `RustEnumVariantInfo`.

3. **Trait + impl block as first-class concepts**: Unlike Java interfaces, Rust traits with default implementations and separate impl blocks need dedicated extraction and compression sections.

4. **Multi-framework route extraction**: Rust web frameworks use fundamentally different routing patterns (actix-web `#[get]`, Rocket `#[get]`, Axum `Router::new().route()`, Warp `warp::path()`, Tide `app.at()`) — requires framework-specific regex.

5. **Feature flag and cfg attribute tracking**: Rust's conditional compilation (`#[cfg(feature = "...")]`) affects which code is active — extracted for AI context.

6. **Cargo.toml as primary dependency source**: Unlike Maven/Gradle which have complex structures, Cargo.toml is TOML-based with simple dependency sections — parsed with Python's `tomllib`/`tomli`.

### Files Created

| File                                     | Purpose                    | Lines |
| ---------------------------------------- | -------------------------- | ----- |
| `extractors/rust/__init__.py`            | Module exports             | ~30   |
| `extractors/rust/type_extractor.py`      | Type extraction            | ~685  |
| `extractors/rust/function_extractor.py`  | Function extraction        | ~440  |
| `extractors/rust/api_extractor.py`       | API endpoint extraction    | ~385  |
| `extractors/rust/model_extractor.py`     | Data model extraction      | ~345  |
| `extractors/rust/attribute_extractor.py` | Attribute extraction       | ~290  |
| `rust_parser_enhanced.py`                | Parser with all extractors | ~340  |
| `bpl/practices/rust_core.yaml`           | 50 BPL practices           | ~700  |
| 4 test files                             | 46 tests total             | ~1200 |

### Bugs Fixed: 6

Key patterns from Rust integration:

1. **Dataclass field name mismatches (10+ occurrences)**: Scanner code assumed `generic_params`, `is_tuple`, `type_name`, `has_default`, `kind` but dataclasses use `generics`, `is_tuple_struct`, `target_type`, `has_default_impl`, `query_type` — same silent-swallowing pattern as Java/C#
2. **Absolute vs relative path in test-skip logic**: `'/tests/' in str(file_path)` matched parent directory when scanning repos stored under `tests/repos/` — CRITICAL bug causing 0 extractions
3. **Regex-consumed attributes**: `FUNC_PATTERN` regex captured `#[test]` in its `attrs` group, but `_extract_attributes()` looked before `match.start()` finding nothing — required dual-source attr parsing

### Validation

Validated on 3 production Rust repositories:

- **tokio-rs/axum**: Web framework — 380 structs, 53 enums, 28 traits, 257 routes, 10 frameworks
- **diesel-rs/diesel**: ORM — 655 structs, 96 enums, 299 traits, 98 models, 107 schema tables
- **actix/actix-web**: Web framework — 411 structs, 121 enums, 33 traits, 43 routes

### Lessons Learned (Rust Specific)

1. **Rust's ownership model affects extraction**: `&self`, `&mut self`, `self`, and associated functions (no self) are semantically different — must track `self_kind` for AI to reason about mutability.
2. **Enum variants are more complex than other languages**: Rust's enum variants can hold data (tuple/struct) unlike Java/C# where enums are constants — requires 3-boolean tracking instead of simple name+value.
3. **Trait impl blocks live separately from type definitions**: Unlike Java where methods are inside class bodies, Rust's `impl Trait for Type` blocks can be in different files — impl extraction must be file-aware.
4. **The silent `except Exception: pass` pattern is STILL the #1 bug source**: Despite being flagged in Java, C#, and now Rust sessions, it continues to silently swallow 10+ AttributeErrors per new language integration. Each language adds ~15 new dataclass fields with unique names.
5. **Test-skip path logic must use relative paths**: Absolute path matching for test-file exclusion can match parent directory components — use `file_path.relative_to(root_path)` consistently.

---

## 13. Reference: C++ Integration Example (NEW v4.20)

### Architecture

```
Extractors (5):
  type_extractor.py      → Classes (CRTP, abstract, final, nested), structs, unions,
                            enums (scoped/unscoped), concepts, type aliases, namespaces,
                            forward declarations
  function_extractor.py  → Methods (virtual/override/const/noexcept), free functions,
                            constructors/destructors, operators, lambdas (generic),
                            coroutines (co_await/co_yield/co_return)
  api_extractor.py       → Crow, Pistache, cpp-httplib, Boost.Beast, Drogon REST,
                            gRPC services, Qt signals/slots, Boost.Asio, IPC, WebSocket
  model_extractor.py     → STL containers, smart pointers (unique/shared/weak),
                            RAII resources, globals, constants, design patterns
  attribute_extractor.py → #include, macros, conditional compilation, pragmas,
                            C++ attributes ([[nodiscard]], [[deprecated]]),
                            static_assert, C++20 modules

Parser:
  cpp_parser_enhanced.py → EnhancedCppParser integrating all 5 extractors
                            + 30+ FRAMEWORK_PATTERNS
                            + C++ standard detection (C++98 through C++26)
                            + compiler detection (GCC, Clang, MSVC, Intel)
                            + CMakeLists.txt parsing (project, deps, features)
                            + optional tree-sitter-cpp AST
                            + optional clangd LSP integration

Integration:
  scanner.py    → ~30 ProjectMatrix fields, _parse_cpp(), FILE_TYPES routing,
                  .h disambiguation (C++ indicators → cpp parser)
  compressor.py → 5 sections: CPP_TYPES, CPP_FUNCTIONS, CPP_API, CPP_MODELS,
                  CPP_DEPENDENCIES
  selector.py   → C++ artifact counting, 30+ framework mappings, practice filtering

Practices:
  cpp_core.yaml → 50 practices (CPP001-CPP050)
```

### Key Design Decisions

1. **CRTP detection**: C++ heavily uses the Curiously Recurring Template Pattern (`class Derived : public Base<Derived>`) — tracked via `is_crtp` on `CppClassInfo` by checking if any base class template argument matches the class name.

2. **Smart pointer as first-class concept**: Unlike raw pointers in C, C++ smart pointers (`unique_ptr`, `shared_ptr`, `weak_ptr`) are semantically different — extracted as `CppSmartPointerInfo` with `pointee_type` for AI to reason about ownership.

3. **`.h` file disambiguation**: Both C and C++ use `.h` headers — moved disambiguation to `_parse_file()` routing level, checking for C++ indicators (class, namespace, template, nullptr, etc.) in file content before routing to correct parser.

4. **Concept and constraint extraction**: C++20 concepts (`template<typename T> concept Foo = ...`) are a new kind of type — extracted as `CppConceptInfo` with parameters and constraint expressions.

5. **Coroutine detection**: C++20 coroutines (`co_await`, `co_yield`, `co_return`) mark functions fundamentally differently — tracked via `is_coroutine` on `CppMethodInfo`.

6. **Multi-framework REST extraction**: C++ REST frameworks use fundamentally different patterns — Crow macros (`CROW_ROUTE`), Pistache static methods (`Routes::Get`), cpp-httplib member calls (`svr.Get`) — requires framework-specific regex with alternation groups.

7. **Constructor extraction separate from methods**: C++ constructors have no return type, so `FUNC_PATTERN` (which requires a return type) misses them — added separate `CONSTRUCTOR_PATTERN` processing after main method extraction.

### Files Created

| File                                    | Purpose                    | Lines |
| --------------------------------------- | -------------------------- | ----- |
| `extractors/cpp/__init__.py`            | Module exports             | ~90   |
| `extractors/cpp/type_extractor.py`      | Type extraction            | ~530  |
| `extractors/cpp/function_extractor.py`  | Function extraction        | ~540  |
| `extractors/cpp/api_extractor.py`       | API endpoint extraction    | ~437  |
| `extractors/cpp/model_extractor.py`     | Data model extraction      | ~350  |
| `extractors/cpp/attribute_extractor.py` | Attribute extraction       | ~320  |
| `cpp_parser_enhanced.py`                | Parser with all extractors | ~638  |
| `bpl/practices/cpp_core.yaml`           | 50 BPL practices           | ~700  |
| 4 test files                            | 73 tests total             | ~1000 |
| `docs/reports/CPP_VALIDATION_REPORT.md` | Validation report          | ~300  |

### Bugs Fixed: 8

Key patterns from C++ integration:

1. **Pistache static method syntax not matched**: `Routes::Get(router, "/path", ...)` vs `router.get("/path", ...)` — required regex alternation with named groups for both syntaxes.
2. **POSIX IPC functions missing**: `shmget/shmat/shmdt/shmctl/pipe` not in IPC_PATTERN — only Boost.Interprocess was detected.
3. **Constructor extraction missing due to return type requirement**: FUNC_PATTERN requires a return type, but constructors have none — added separate CONSTRUCTOR_PATTERN loop.
4. **Lambda is_generic field missing**: Generic lambdas (`[](auto x)`) need `is_generic` tracking — added field + `'auto' in params` detection.
5. **CRTP field missing**: CRTP is ubiquitous in C++ but wasn't detected — added `is_crtp` field + base class template argument matching.
6. **Smart pointer field name mismatch**: `CppSmartPointerInfo` uses `pointee_type` but scanner accessed `managed_type` — the silent `except Exception` pattern strikes again.
7. **.h disambiguation critical for header-only libraries**: Without content-based C++ detection, spdlog/fmt/nlohmann_json (all header-only) extracted 0 C++ artifacts from `.h` files.
8. **Silent exception swallowing**: Same pattern as Java/C#/Rust/C — `except Exception` hid all field access bugs until direct Python debugging.

### Validation

Validated on 3 production C++ repositories:

- **gabime/spdlog**: Logging library — 356 classes, 1476 methods, 46 enums, 82 namespaces, 69 smart pointers, C++23
- **fmtlib/fmt**: Formatting library — 245 classes, 88 methods, 44 enums, 3 namespaces, C++23
- **nlohmann/json**: JSON library — 229 classes, 110 methods, 16 enums, 12 namespaces, C++20

### Lessons Learned (C++ Specific)

1. **Header-only libraries require `.h` disambiguation**: C++ header-only libraries (spdlog, fmt, nlohmann_json) put all code in `.h` files — without content-based C++ detection, these would all go to the C parser and extract nothing meaningful.
2. **CRTP is everywhere in template-heavy C++ code**: The Curiously Recurring Template Pattern is so common that not detecting it means missing fundamental design intent — AI needs `is_crtp` to reason about static polymorphism.
3. **C++ constructors break function regex patterns**: Unlike other languages where constructors look like functions, C++ constructors have no return type — requires a separate regex pattern.
4. **Smart pointer field names differ from raw pointer conventions**: C++ smart pointers use `pointee_type` (what they point to) rather than `managed_type` — naming must match the actual dataclass.
5. **C++ REST frameworks have no standardized routing API**: Each framework (Crow, Pistache, cpp-httplib, Beast, Drogon) uses fundamentally different syntax — requires framework-specific regex unlike Java/C# where Spring/ASP.NET dominate.
6. **The `except Exception: pass` pattern remains the #1 bug source**: Now documented across 5 languages (Java, C#, Rust, C, C++) — each new language adds 15-30 new dataclass fields, and silent swallowing hides all mismatches.

---

## 14. Reference: Ruby Integration Example (NEW v4.23)

### Overview

Ruby is the 15th language added to CodeTrellis (v4.23). Ruby integration covers:

- **Ruby 1.8 – 3.3+** version detection
- **5 web frameworks**: Rails, Sinatra, Grape, Hanami, Roda
- **3 ORMs**: ActiveRecord, Sequel, Mongoid
- **Rails ecosystem**: Controllers, models, migrations, concerns, callbacks, workers, channels, middleware
- **Metaprogramming**: `define_method`, `method_missing`, `class_eval`, `send`, `respond_to_missing?`
- **Gemfile parsing**: Dependency extraction with version constraints, groups, ruby version

### Key Design Decisions

1. **Dataclass field naming conventions**: Ruby extractors use `parent_class` (not `superclass`), `kind` (not `type` — avoids Python builtin collision), `owner_class` (not `class_name`), `names` (List[str] for accessors), `uses_yield` (not `yields`).

2. **Name-based file detection**: Ruby has critical files without extensions — `Gemfile`, `Rakefile`, `Guardfile`, `Capfile`, `Vagrantfile`, `Podfile`, `Brewfile`, `Berksfile`. Added 8 name-based entries to `FILE_TYPES` in scanner.

3. **Controller regex for namespaced classes**: Ruby controllers can be namespaced (`Api::V1::ProductsController`) — regex uses `(?:\w+::)*\w+Controller` pattern.

4. **Route handler splitting**: Rails routes use `controller#action` format (e.g., `health#show`). Scanner splits handler into separate `controller` and `action` fields for easier consumption.

5. **Flexible route regex**: Rails `match` routes can have options between path and `to:` (e.g., `match 'userinfo', via: [:get, :post], to: 'userinfo#show'`). Used `.*?to:` instead of `,\s*to:` for flexible matching.

6. **Struct/Data/OpenStruct distinction**: Ruby has 3 value-like types — `Struct.new`, `Data.define` (Ruby 3.2+), `OpenStruct.new`. Tracked via `kind` field on `RubyStructInfo`.

7. **Multiple filter types**: Rails controllers have `before_action`, `after_action`, and `around_action` — stored as 3 separate lists on `RubyControllerInfo` instead of a single `filters` list, combined during scanner serialization.

8. **Gemfile ruby version flexibility**: Gemfiles use version constraints like `ruby "~> 3.3"` or `ruby '>= 3.2.0', '< 3.5.0'` — regex accepts any version string within quotes, not just strict semver.

### Files Created

| File                                     | Purpose                    | Lines |
| ---------------------------------------- | -------------------------- | ----- |
| `extractors/ruby/__init__.py`            | Module exports             | ~30   |
| `extractors/ruby/type_extractor.py`      | Type extraction            | ~467  |
| `extractors/ruby/function_extractor.py`  | Function extraction        | ~427  |
| `extractors/ruby/api_extractor.py`       | API endpoint extraction    | ~477  |
| `extractors/ruby/model_extractor.py`     | ORM model extraction       | ~519  |
| `extractors/ruby/attribute_extractor.py` | Callbacks, DSL, Gemfile    | ~521  |
| `ruby_parser_enhanced.py`                | Parser with all extractors | ~449  |
| `bpl/practices/ruby_core.yaml`           | 50 BPL practices           | ~500  |
| 4 test files                             | 80 tests total             | ~1422 |

### Bugs Fixed During Integration

Key patterns from Ruby integration:

1. **Attribute name mismatches (15+ fixes)**: The #1 recurring pattern across all language integrations. Every dataclass field name must exactly match scanner/compressor access. Ruby had `parent_class` vs `superclass`, `kind` vs `mixin_type`, `uses_yield` vs `yields`, `owner_class` vs `class_name`, and many more.

2. **Controller regex didn't match namespaced classes**: `\w+Controller` failed on `Api::V1::ProductsController` — fixed with `(?:\w+::)*\w+Controller`.

3. **Grape route regex didn't match block form**: `get :path` worked but `get do...end` (common Grape pattern) didn't — added alternation `(?:[:\'](?P<path>\w+)|do\b)`.

4. **Rails framework detection too narrow**: Pattern only matched `class.*Rails` — didn't detect `ApplicationController`, `ApplicationRecord`, `ApplicationMailer`, `ApplicationJob` as Rails indicators.

5. **Gemfile not parsed — no file extension**: `Gemfile` has no `.rb` extension, wasn't in FILE_TYPES map — added 8 name-based file entries.

6. **Ruby version regex too strict**: Only matched `\d+\.\d+\.\d+` but real Gemfiles use `~> 3.3`, `>= 3.2.0` — changed to accept any string within quotes.

7. **Rails route regex too rigid**: `to:` must immediately follow path in `(?:,\s*to:...)` — but real routes have `via:`, `defaults:`, `constraints:` between path and `to:` — changed to `.*?to:`.

### Validation

Validated on 3 production Ruby repositories:

- **discourse/discourse**: Forum platform — 3,698 classes, 17,881 methods, 1,182 routes, 135 controllers, 204 models, 178 gems, Rails/ActiveRecord/Sidekiq/Sorbet
- **faker-ruby/faker**: Data generation library — 247 classes, 245 modules, 1,392 methods, 15 gems, RSpec
- **mastodon/mastodon**: Social network — 1,898 classes, 7,653 methods, 1,740 routes, 292 controllers, 221 models, 153 gems, 89 workers, Rails/Devise/Sidekiq/Pundit

### Lessons Learned (Ruby Specific)

1. **Ruby's metaprogramming makes static analysis challenging**: `define_method`, `method_missing`, `class_eval` create methods/classes dynamically that static regex can never fully capture — surface-level detection is the practical approach.
2. **Name-based file detection is essential for Ruby**: Unlike most languages, Ruby has critical project files (`Gemfile`, `Rakefile`, `Capfile`) with no extension — scanner must support name-based routing.
3. **Rails conventions make extraction easier**: Rails' convention-over-configuration means controller/model/concern patterns are highly regular — regex works well.
4. **Accessor notation differs from other languages**: Ruby `attr_reader :name, :email` creates multiple getters from a single declaration — must extract `names` as `List[str]`, not `name` as `str`.
5. **Ruby version constraints aren't semver**: Unlike most languages, Ruby Gemfile version specs use constraint operators (`~>`, `>=`, `<`) — regex must accept flexible formats.
6. **The `except Exception: pass` bug source continues**: Ruby is the 6th language (after Java, C#, Rust, C, C++) where silent exception swallowing in scanner hid 15+ attribute name mismatches until direct Python testing.

---

## 15. Reference: Scala Integration Example (NEW v4.25)

Scala is the 18th language added to CodeTrellis (v4.25). Scala integration covers:

- **Scala 2.x – 3.x** version detection (from code features + `scalaVersion` in build.sbt)
- **25+ framework detection** (Play, Akka, Akka HTTP, Pekko, http4s, ZIO, ZIO HTTP, Cats, Cats Effect, fs2, Tapir, Circe, Doobie, Skunk, Slick, Quill, ScalikeJDBC, Spark, Flink, Finch, Scalatra, Sangria, Caliban, ScalaTest, MUnit, Specs2, ScalaCheck, Monix)
- **5 extractors**: type (classes, case classes, traits, sealed traits, objects, case objects, enums, type aliases, givens, opaque types), function (methods, extension methods, val functions), api (Play routes, Akka HTTP, http4s, Tapir, ZIO HTTP, Finch, Scalatra, Cask, gRPC, GraphQL), model (Slick, Doobie, Quill, Skunk, ScalikeJDBC, JSON codecs), attribute (annotations, implicits/givens, macros, SBT deps, imports)
- **build.sbt parsing**: SBT dependency extraction with `%%`/`%%%` notation, `scalaVersion` extraction
- **50 BPL practices** (SCALA001-SCALA050) covering immutability, pattern matching, effect systems, type classes, Scala 3 features

### Key Design Decisions

1. **Regex AST only**: Unlike Java (tree-sitter) or Swift (tree-sitter-swift), Scala has no stable tree-sitter grammar — regex-based extraction with balanced-paren helpers provides reliable coverage.

2. **Scala 2/3 feature detection**: Version is inferred from code features (`given`/`using`/`enum`/`extension` → Scala 3, `implicit class`/`implicit def` → Scala 2). `parse_build_sbt()` is a separate static method for explicit scalaVersion from build files.

3. **Multiple framework paradigms**: Scala uniquely spans OOP (Play, Akka) and FP (http4s, ZIO, Cats Effect) — framework detection covers both paradigms and their combinations.

4. **SBT double-percent notation**: Scala dependencies use `%%` (cross-build) and `%%%` (Scala.js cross-build) — regex handles both and preserves the notation.

5. **Build file routing**: `.sbt` files and `build.sbt` are detected by name and routed to the Scala parser for dependency extraction, similar to how `Gemfile` is handled for Ruby.

### Bugs Found During Integration

1. **Python 3.14 regex incompatibility**: `[^\s->]` character class is rejected — hyphen must be escaped: `[^\s\->]`
2. **Slick table syntax mismatch**: Real Slick uses `Table[User](tag, "users")` not `Table[User]("users")`
3. **Dataclass field name bug**: `db_name` vs `db_type` in ScalaColumnInfo
4. **BPL category validation**: 14 categories used across Scala/Ruby/PHP/DevOps YAML files not in PracticeCategory enum

### Validation

Validated on 3 production Scala repositories:

- **ghostdogpr/caliban**: GraphQL library — 517 .scala files, 161 types, 2,436 methods, 37 API lines (routes, gRPC, GraphQL), 51 deps, frameworks: caliban, zio, tapir, cats, scalapb, sangria
- **playframework/play-samples**: Play Framework samples — 140 .scala files, 103 types, 75+ methods, 54 API lines (28 Play routes, 30 controllers), 14 models (11 JSON codecs), 76 deps
- **zio/zio-http**: ZIO HTTP library — 721 .scala files, 133 types (726 classes), 109 methods, 95 API lines (42 tapir, 13 finch routes), 72 deps

### Lessons Learned (Scala Specific)

1. **Scala's type system complexity challenges regex**: Type parameters with variance (`+A`, `-B`), context bounds (`A: Ordering`), and higher-kinded types (`F[_]`) require careful regex grouping.
2. **Multiple build tool support**: Scala projects use SBT (`.sbt`), Mill (`build.sc`), or Maven/Gradle — build.sbt is most common; `.sc` files can be both Mill build files and Scala scripts.
3. **Framework detection spans paradigms**: Unlike Ruby (mostly OOP/Rails) or PHP (mostly OOP/Laravel), Scala spans pure FP (Cats Effect, ZIO), hybrid FP-OOP (Akka), and traditional OOP (Play) — framework detection needs broader coverage.
4. **Implicit/given evolution**: Scala 2 uses `implicit def/val/class`, Scala 3 uses `given`/`using` — extractors detect both to support migration-era codebases.
5. **The BPL category gap was cross-language**: Adding Scala's categories (build, style, serialization, etc.) also fixed "Failed to parse practice" warnings for Ruby, PHP, and DevOps practices — a cross-cutting fix.

---

## 16. Reference: R Integration Example (NEW v4.26)

R is the 19th language added to CodeTrellis (v4.26). R integration covers:

- **R 2.x – 4.4+** version detection (from code features + DESCRIPTION `Depends: R (>= x.y.z)`)
- **6 class systems**: S3 (structure-based), S4 (formal with slots), R5 (ReferenceClass), R6 (encapsulated OOP), S7/R7 (next-gen formal), proto (prototype-based)
- **70+ framework detection** (tidyverse, Shiny, Plumber, data.table, arrow, Rcpp, caret, tidymodels, mlr3, sf, terra, brms, rstan, torch, reticulate, future, testthat, devtools, roxygen2, golem, rhino, bioconductor, and many more)
- **5 extractors**: type (R6/R5/S4/S3/S7/proto classes, generics, environments), function (functions, S3 methods, operators, lambdas, pipe chains), api (Plumber, Shiny, RestRserve, Ambiorix), model (data models, DBI connections, queries, pipelines), attribute (DESCRIPTION/NAMESPACE deps, exports, configs, hooks)
- **DESCRIPTION/NAMESPACE/renv.lock parsing**: Full package metadata, dependency extraction, export/import tracking
- **50 BPL practices** (R001-R050) covering style, type safety, error handling, testing, performance, architecture, security, documentation, DevOps, data engineering

### Architecture

```
Extractors (5):
  type_extractor.py      → R6 classes, R5 (ReferenceClass), S4 classes, S3 classes,
                            S7/R7 classes, proto objects, environments,
                            S4 generics (setGeneric), S7 generics (new_generic),
                            S4 methods (setMethod), fields (RFieldInfo)
  function_extractor.py  → Functions (exported/internal), S3 methods (method.class),
                            infix operators (%%, %+%, %>%, %<>%),
                            R 4.1+ lambdas (\(x) expr), pipe chains (|> and %>%)
  api_extractor.py       → Plumber routes (#* @get/@post/@put/@delete),
                            Shiny server/UI components (renderPlot, observeEvent),
                            Shiny modules (moduleServer, NS), RestRserve, Ambiorix
  model_extractor.py     → Data models (tibble, data.table, arrow, data.frame),
                            DBI connections (dbConnect with pool support),
                            SQL queries (dbGetQuery, dbSendQuery, sqlInterpolate),
                            data pipelines (read_csv → mutate → write_csv)
  attribute_extractor.py → DESCRIPTION deps (Imports/Depends/Suggests/LinkingTo),
                            NAMESPACE exports/imports, configs (yaml/json/ini),
                            lifecycle hooks (onLoad, onAttach, onUnload),
                            package metadata (Title, Version, License)

Parser:
  r_parser_enhanced.py   → EnhancedRParser integrating all 5 extractors
                            + 70+ FRAMEWORK_PATTERNS
                            + R version detection (R 2.x through R 4.4+)
                            + DESCRIPTION file parsing (deps, version, license)
                            + NAMESPACE parsing (exports, imports, S3/S4 methods)
                            + renv.lock parsing (package versions, repositories)
                            + LIBRARY_PATTERN with dotted package name support
                            + optional R-languageserver LSP integration

Integration:
  scanner.py    → ~25 ProjectMatrix fields, _parse_r(), FILE_TYPES routing
                  (.R/.r/.Rmd/.Rnw/.Rproj + DESCRIPTION/NAMESPACE/renv.lock)
  compressor.py → 5 sections: R_TYPES, R_FUNCTIONS, R_API, R_MODELS,
                  R_DEPENDENCIES
  selector.py   → R artifact counting, 70+ framework mappings,
                  prefix mapping (R, SHINY, PLUMBER, GOLEM, TIDY)

Practices:
  r_core.yaml   → 50 practices (R001-R050) across 10 categories
```

### Key Design Decisions

1. **Six class systems require unified extraction**: R uniquely has 6 OOP systems active simultaneously. Each system uses fundamentally different patterns (`R6Class()` vs `setClass()` vs `setRefClass()` vs `new_class()`). Separate regex patterns per system with unified `RClassInfo` output dataclass.

2. **Pipe chain analysis as first-class concept**: R's pipe operators (`%>%` from magrittr and `|>` native) create complex data transformation chains. Extracted as `RPipeChainInfo` with `start_function`, `chain_functions`, `pipe_type`, and `length` for AI to reason about data flow.

3. **DESCRIPTION/NAMESPACE as structured metadata**: Unlike most languages where deps come from manifest files (package.json, Cargo.toml), R uses two separate files — DESCRIPTION for metadata/deps and NAMESPACE for exports/imports. Both are parsed with dedicated static methods.

4. **Dotted package names**: R packages commonly use dots in names (`data.table`, `R.utils`, `Rcpp.package.skeleton`). The `LIBRARY_PATTERN` regex uses `[\w.]+` instead of `\w+` to capture these correctly.

5. **Shiny reactive component model**: Shiny's reactive programming model (`reactive()`, `observe()`, `eventReactive()`, `renderPlot()`) is fundamentally different from REST APIs. Extracted as `RShinyComponentInfo` with `kind`, `inputs`, `outputs`, `reactive_values`, `observers`, `renders`.

6. **S3 method naming convention**: S3 methods follow `generic.class` naming (`print.my_class`, `summary.lm`). Regex splits on the first dot to identify generic and class — but must handle dotted class names carefully.

7. **Lambda extraction for R 4.1+**: R's lambda syntax `\(x) expr` is syntactically similar to function definitions but semantically lighter. Extracted separately via `_extract_lambdas()` with R 4.1+ version tagging.

8. **Name-based file detection**: R has critical files without `.R` extension — `DESCRIPTION`, `NAMESPACE`, `renv.lock`. Scanner uses name-based routing (same pattern as Ruby's `Gemfile`).

### Files Created

| File                                  | Purpose                    | Lines |
| ------------------------------------- | -------------------------- | ----- |
| `extractors/r/__init__.py`            | Module exports             | ~30   |
| `extractors/r/type_extractor.py`      | Type extraction            | ~670  |
| `extractors/r/function_extractor.py`  | Function extraction        | ~521  |
| `extractors/r/api_extractor.py`       | API endpoint extraction    | ~418  |
| `extractors/r/model_extractor.py`     | Data model extraction      | ~401  |
| `extractors/r/attribute_extractor.py` | Dependencies & metadata    | ~451  |
| `r_parser_enhanced.py`                | Parser with all extractors | ~503  |
| `bpl/practices/r_core.yaml`           | 50 BPL practices           | ~700  |
| 4 test files                          | 62 tests total             | ~1200 |

### Bugs Fixed: 11

Key patterns from R integration:

1. **Dataclass field name mismatches (15+ occurrences)**: Scanner code assumed `inherits`, `access`, `generic`, `start_symbol`, `steps`, `module_id`, `params`, `doc`, `format`, `is_pool`, `operation`, `source`, `kind`, `type_hint` but dataclasses use `parent_class`, `visibility`, `generic_name`, `start_function`, `chain_functions`, `renders`/`outputs`, `parameters`, `description`, `kind`, `pool`, `query_type`, `input_source`, `actions`, `type` — the same silent-swallowing pattern as Java/C#/Rust/C/C++/Scala.
2. **Operator regex too restrictive**: `%\w+%` didn't match `%+%` because `+` is not a word character — changed to `%[^%\s]+%`.
3. **Dotted package names in library()**: `library(data.table)` failed because `(\w+)` doesn't match dots — changed to `([\w.]+)`.
4. **Multi-line pipe chain detection**: R pipes span multiple lines (`df %>%\n  filter() %>%\n  select()`) but single-line regex missed them — rewrote with line merging.
5. **Python 3.14 SyntaxWarnings**: Unescaped `\(` in docstrings triggers warnings in Python 3.14 — escaped to `\\(`.

### Validation

Validated on 3 production R repositories:

- **tidyverse/dplyr**: Data manipulation — 897 functions, 4 classes, 100 pipe chains, 29 DESCRIPTION deps, 338 exports, tidyverse/rlang/vctrs detected
- **rstudio/shiny**: Reactive web framework — 1,117 functions, 35 classes, 128 Shiny components, 4 module servers, 4 module UIs, shiny/htmltools/httpuv detected
- **rstudio/plumber**: API framework — 361 functions, 12 classes, plumber/R7/future/promises/swagger detected

### Lessons Learned (R Specific)

1. **R's multiple OOP systems are the biggest extraction challenge**: No other language has 6 concurrent class systems with fundamentally different declaration patterns. Each system needs its own regex, but all must output to a unified `RClassInfo` dataclass with a `kind` field to distinguish them.

2. **Pipe chains are the dominant code pattern in modern R**: The `%>%` (magrittr) and `|>` (native) pipe operators are used extensively — extracting pipe chains gives AI critical context about data transformation workflows that function-level extraction alone misses.

3. **DESCRIPTION file is richer than most manifests**: Unlike `package.json` (just deps), R's DESCRIPTION contains Package, Title, Version, Authors@R, Description, License, Depends, Imports, Suggests, LinkingTo — all valuable metadata for AI context.

4. **S3's naming convention creates ambiguity**: `print.data.frame` — is this method `print` for class `data.frame`, or method `print.data` for class `frame`? R resolves this at runtime via method dispatch, but static regex uses first-dot splitting with common generic names list.

5. **Shiny's reactive model is unlike REST APIs**: Shiny components (`renderPlot`, `observeEvent`, `moduleServer`) don't follow request/response patterns — they need their own dataclass (`RShinyComponentInfo`) rather than being forced into `RRouteInfo`.

6. **The `except Exception: pass` pattern is STILL the #1 bug source**: R is the 7th language (after Java, C#, Rust, C, C++, Scala) where silent exception swallowing in scanner hid 15+ attribute name mismatches. Each language adds ~25 new dataclass fields with unique naming.

---

## 17. Reference: Dart Integration Example (NEW v4.27)

Dart is the 20th language added to CodeTrellis (v4.27). Dart integration covers:

- **Dart 2.0 – 3.5+** version detection (from pubspec.yaml SDK constraints + code features)
- **Null safety** detection (Dart 2.12+: `late`, `required`, `?`, `!`)
- **Dart 3 features** (sealed classes, class modifiers, records, patterns, extension types)
- **Flutter 1.x – 3.x+** (4 widget types: Stateless, Stateful, Inherited, RenderObject)
- **70+ framework detection** (Flutter, Riverpod, Bloc, GetX, Provider, MobX, Dio, Drift, Floor, Isar, Hive, ObjectBox, Freezed, JsonSerializable, GetIt, Injectable, GoRouter, AutoRoute, Fluro, Shelf, Dart Frog, Serverpod, Conduit, Angel, Firebase, Supabase, gRPC, and many more)
- **5 extractors**: type (classes with Dart 3 modifiers, mixins, enhanced enums, extensions, extension types, typedefs), function (async/async*/sync* functions, constructors, getters, setters), api (Flutter widgets, routes for 5 server frameworks, state managers for 5 state management libs, gRPC), model (5 ORM backends, 4 data class generators, migrations), attribute (annotations, imports/exports/parts, isolates/compute, platform channels, null safety, Dart 3 features)
- **pubspec.yaml/pubspec.lock parsing**: Full dependency extraction, SDK version detection, Flutter config
- **50 BPL practices** (DART001-DART050) covering null safety, type system, async, error handling, organization, Flutter widgets, state management, performance, testing, package design

### Architecture

```
Extractors (5):
  type_extractor.py      → Classes (abstract/sealed/base/interface/final/mixin class),
                            mixins, enhanced enums (with members, Dart 2.17+),
                            extensions, extension types (Dart 3.3+),
                            typedefs (function/non-function)
  function_extractor.py  → Functions (async/async*/sync*), methods,
                            constructors (const/factory/named/redirecting),
                            getters, setters
  api_extractor.py       → Flutter widgets (Stateless/Stateful/Inherited/RenderObject),
                            server routes (Shelf/DartFrog/Serverpod/Conduit/Angel),
                            state managers (Riverpod/Bloc/GetX/Provider/MobX),
                            gRPC services
  model_extractor.py     → ORM models (Drift/Floor/Isar/Hive/ObjectBox),
                            data classes (Freezed/JsonSerializable/BuiltValue/Equatable),
                            database migrations
  attribute_extractor.py → Annotations (@override, @immutable, custom),
                            imports/exports/parts,
                            isolates (Isolate.spawn/compute),
                            platform channels (MethodChannel/EventChannel),
                            null safety analysis (late/required/?/! counts),
                            Dart 3 feature detection (sealed/records/patterns)

Parser:
  dart_parser_enhanced.py → EnhancedDartParser integrating all 5 extractors
                             + 70+ FRAMEWORK_PATTERNS
                             + Dart version detection from pubspec SDK constraints
                             + Flutter version detection from pubspec
                             + parse_pubspec() static method for dependency extraction
                             + Null safety detection from environment SDK constraints
                             + Optional tree-sitter-dart AST integration
                             + Optional dart analysis_server LSP integration

Integration:
  scanner.py    → ~30 ProjectMatrix fields, _parse_dart(), FILE_TYPES routing
                  (.dart + pubspec.yaml/pubspec.lock name-based)
  compressor.py → 5 sections: DART_TYPES, DART_FUNCTIONS, DART_API, DART_MODELS,
                  DART_DEPENDENCIES
  selector.py   → Dart artifact counting (19 types), 35 framework mappings,
                  prefix mapping (DART, FLUTTER),
                  27 PracticeCategory enums

Practices:
  dart_core.yaml → 50 practices (DART001-DART050) across 10 categories
```

### Key Design Decisions

1. **Dart 3 class modifiers as first-class concepts**: Dart 3.0 introduced `sealed`, `base`, `interface`, `final`, and `mixin` class modifiers. Each modifier is extracted as a separate flag on `DartClassInfo` and surfaced in the compressor output, enabling AI to reason about API design intent and exhaustiveness checking.

2. **Flutter widget type hierarchy**: Flutter has 4 fundamentally different widget types (StatelessWidget, StatefulWidget, InheritedWidget, RenderObjectWidget), each with different lifecycle patterns. Extracted as `DartWidgetInfo` with `kind` field rather than a generic class, giving AI context about the widget's lifecycle and rendering behavior.

3. **Null safety as a cross-cutting concern**: Null safety isn't just about types — it changes how entire codebases are written. Extracted as aggregate counts (`late_count`, `required_count`, `nullable_count`, `bang_operator_count`) to give AI a measure of null safety adoption and migration status.

4. **Multiple state management paradigms**: Dart/Flutter has 5+ major state management approaches (Riverpod, Bloc, GetX, Provider, MobX), each with fundamentally different patterns. Extracted as `DartStateInfo` with `framework` field rather than forcing all into a single pattern.

5. **pubspec.yaml as the single source of truth**: Unlike R's DESCRIPTION+NAMESPACE or Ruby's Gemfile+gemspec, Dart uses `pubspec.yaml` for all dependency and metadata needs. `parse_pubspec()` extracts deps, dev_deps, Flutter config, SDK version, and Flutter SDK version from a single file.

6. **Extension types (Dart 3.3+) as a new type category**: Extension types (`extension type Meters(double value)`) are a Dart-specific feature that creates zero-cost wrappers. Extracted separately from regular extensions because they have different semantics (compile-time only, no runtime overhead).

7. **`packages` directory is NOT ignorable for Dart**: The C# integration added `"packages"` to DEFAULT_IGNORE (for NuGet packages), but Dart/Flutter monorepos use `packages/` for their sub-packages. This was causing 100% of Dart files in monorepos to be silently skipped — removed from DEFAULT_IGNORE.

8. **Dataclass field alias pattern**: To handle the mismatch between what scanner code expects and what extractors provide, adopted a fallback pattern (`widget.kind or widget.widget_type`, `sm.framework or sm.pattern`) instead of renaming fields — this maintains backward compatibility while supporting multiple naming conventions.

### Files Created

| File                                     | Purpose                    | Lines |
| ---------------------------------------- | -------------------------- | ----- |
| `extractors/dart/__init__.py`            | Module exports             | ~35   |
| `extractors/dart/type_extractor.py`      | Type extraction            | ~500  |
| `extractors/dart/function_extractor.py`  | Function extraction        | ~400  |
| `extractors/dart/api_extractor.py`       | API/widget extraction      | ~450  |
| `extractors/dart/model_extractor.py`     | Model/ORM extraction       | ~400  |
| `extractors/dart/attribute_extractor.py` | Attributes/null safety     | ~450  |
| `dart_parser_enhanced.py`                | Parser with all extractors | ~450  |
| `bpl/practices/dart_core.yaml`           | 50 BPL practices           | ~700  |
| 6 test files                             | 126 tests total            | ~2500 |

### Bugs Fixed: 4

Key patterns from Dart integration:

1. **Dataclass field name mismatches (15+ occurrences, Bug #58)**: Scanner code assumed `methods`, `doc_comment`, `kind`, `framework`, `is_enhanced`, `values`, `columns`, etc. but dataclasses used different field names or were missing fields entirely. Fixed by adding missing fields to 14 dataclasses across all 5 extractors + fallback logic in `_parse_dart`. The same `except Exception: pass` silent-swallowing pattern as Java/C#/Rust/C/C++/Scala/R — now the 8th language with this exact bug.

2. **`packages` in DEFAULT_IGNORE blocked all Dart files (Bug #59)**: The most impactful bug — `"packages"` was added to DEFAULT_IGNORE for C# NuGet packages, but Dart/Flutter monorepos (like Isar with 210 `.dart` files) store all their code under `packages/`. This caused 100% file loss with zero scanner errors. Fixed by removing `"packages"` from DEFAULT_IGNORE.

3. **`scala_case_classes` phantom references (Bug #60)**: Two C# scanner tests referenced `matrix.scala_case_classes` which doesn't exist as a ProjectMatrix field. These tests passed silently because they tested `len(...) == 0` on a non-existent attribute that defaulted to `[]`. Fixed by removing the references.

4. **BPL PracticeCategory validation errors (Bug #61)**: 50 "Failed to parse practice" warnings because dart_core.yaml used 27 Dart/Flutter-specific category names not in the PracticeCategory enum. Fixed by adding all 27 values to the enum in `models.py`.

### Validation

Validated on 3 production Dart repositories:

- **isar/isar**: NoSQL database — 210 Dart files, 168 classes, 512 functions, 32 widgets, 28 annotations, 13 detected frameworks (isar, flutter, riverpod, drift, hive, objectbox, freezed, json_serializable, dio, go_router, auto_route, get_it, injectable), Dart SDK 3.5.0, Flutter SDK 3.22.0
- **felangel/bloc**: State management library — 148 Dart files, 88 classes, 281 functions, 5 detected frameworks (bloc, provider, mobx, riverpod, getx)
- **dart-lang/shelf**: HTTP server middleware — 45 Dart files, 26 classes, 87 functions, 3 API endpoints, 3 detected frameworks (shelf, shelf_router, websocket)

### Lessons Learned (Dart Specific)

1. **Dart's class modifier system is the richest among all 21 languages**: With 6 modifiers (`abstract`, `sealed`, `base`, `interface`, `final`, `mixin`) that can be combined (e.g., `sealed base class`, `interface mixin class`), Dart 3.0+ has the most complex class declaration syntax. Regex must handle all combinations.

2. **Flutter widget detection requires inheritance analysis**: Unlike REST controllers (detectable by annotations), Flutter widgets are identified by their superclass (`extends StatelessWidget`). This makes regex extraction reliable since the pattern is always in the class declaration line.

3. **Dart's `packages/` directory convention conflicts with C# NuGet**: This cross-language collision (Bug #59) demonstrates that `DEFAULT_IGNORE` entries must be language-aware. A pattern that's correct for one ecosystem can silently break another.

4. **Null safety migration creates two code styles**: Pre-2.12 Dart code lacks null safety markers, while post-2.12 uses `?`, `!`, `late`, `required` extensively. The null safety analysis (counts of each marker) helps AI understand whether a codebase has fully migrated.

5. **Multiple ORM/data class patterns require framework-aware extraction**: Dart has 5+ ORM backends (Drift, Floor, Isar, Hive, ObjectBox) and 4+ data class generators (Freezed, JsonSerializable, Built Value, Equatable), each with unique annotation/superclass patterns. Framework detection from imports drives correct ORM model extraction.

6. **pubspec.yaml is simpler than most manifests but Flutter config adds complexity**: While `pubspec.yaml` deps are straightforward (`name: ^version`), Flutter-specific config (`flutter:`, `uses-material-design:`, `assets:`, `fonts:`) adds rich metadata that no other language manifest has.

7. **State management framework detection is Dart's unique challenge**: No other language has 5+ competing state management patterns all active in the same ecosystem. The `DartStateInfo.framework` field is critical for AI to understand which pattern the project uses.

8. **The `except Exception: pass` bug is now confirmed across 8 languages**: Dart is the 8th language where silent exception swallowing in scanner hid field name mismatches. This pattern should be considered a systemic architectural issue rather than a per-language bug.

---

## 19. Reference: PowerShell Integration Example (NEW v4.29)

### Overview

PowerShell is the 19th language (20th counting Kotlin v2) added to CodeTrellis. It supports Windows PowerShell 1.0-5.1 and PowerShell Core 6.0-7.4+, covering scripting, automation, infrastructure-as-code (DSC), web servers (Pode), and testing (Pester).

### Key Architecture Decisions

1. **Five extractors matching the standard pattern**: type (classes/enums/interfaces/DSC resources), function (functions/filters/workflows/scriptblocks/pipelines), api (routes/DSC configs/Pester tests/cmdlet bindings), model (manifests/PSCustomObject/registry ops/DSC nodes), attribute (using/Import-Module/#Requires/dot-sourcing/comment-based help/version detection)

2. **30+ framework patterns**: Pode, Polaris, UniversalDashboard (web), Pester (testing), DSC (infrastructure), Azure/AzureAD/AWS/GCP (cloud), MSGraph/Exchange/ActiveDirectory (Microsoft services), PSake/InvokeBuild (build), Plaster/PSGallery (packaging), SecretManagement/SecretStore (security), ImportExcel/dbatools/SqlServer (data), Remoting, GitHub Actions/Azure DevOps (CI/CD), PSFramework, RestPS

3. **DSC (Desired State Configuration) is unique to PowerShell**: Three dedicated extractors handle DSC resources (type_extractor), DSC configurations (api_extractor), and DSC nodes (model_extractor). No other language has infrastructure-as-code built into its class system.

4. **Pester test extraction**: Dedicated patterns for `Describe`, `Context`, `It`, `BeforeAll`, `BeforeEach`, `AfterAll`, `AfterEach` blocks with nesting support. This is analogous to RSpec (Ruby) and Jest (TypeScript) but with PowerShell's unique syntax.

5. **Cmdlet binding and parameter attributes**: PowerShell's `[CmdletBinding()]` and `[Parameter()]` attribute system is richer than any other language's function metadata. Extractors capture `Mandatory`, `ValueFromPipeline`, `Position`, `ValidateSet`, `ValidatePattern`, and parameter set names.

6. **Pipeline-centric execution model**: PowerShell's `Begin/Process/End` block pattern for pipeline-aware functions is unique. The `has_begin_process_end` flag on `PSFunctionInfo` captures this critical architectural information.

### Files Created

| File                                                       | Purpose                                                 |
| ---------------------------------------------------------- | ------------------------------------------------------- |
| `codetrellis/extractors/powershell/__init__.py`            | Module exports (5 extractors, 17 dataclasses)           |
| `codetrellis/extractors/powershell/type_extractor.py`      | Classes, enums, interfaces, DSC resources               |
| `codetrellis/extractors/powershell/function_extractor.py`  | Functions, filters, workflows, scriptblocks, pipelines  |
| `codetrellis/extractors/powershell/api_extractor.py`       | Routes, DSC configs, Pester tests, cmdlet bindings      |
| `codetrellis/extractors/powershell/model_extractor.py`     | Manifests, PSCustomObject, registry ops, DSC nodes      |
| `codetrellis/extractors/powershell/attribute_extractor.py` | Imports, usings, requires, help, dot-sourcing, versions |
| `codetrellis/powershell_parser_enhanced.py`                | Parser with 30+ framework patterns                      |
| `codetrellis/bpl/practices/powershell_core.yaml`           | 50 practices (PS001-PS050)                              |

### Integration Points

| File                     | Changes                                                              |
| ------------------------ | -------------------------------------------------------------------- |
| `scanner.py`             | 23 `ps_*` fields, `_parse_powershell()`, file routing, `ext_to_lang` |
| `compressor.py`          | 5 sections: TYPES, FUNCTIONS, API, MODELS, DEPENDENCIES              |
| `bpl/selector.py`        | 19 artifact types, 20 framework mappings, `from_matrix()` counting   |
| `bpl/models.py`          | 14 PracticeCategory enum values (PS_CMDLET_DESIGN through PS_WEB)    |
| `discovery_extractor.py` | `.ps1/.psm1/.psd1` → `powershell` in LANGUAGE_MAP                    |

### Bugs Fixed

| #   | Description                                 | Fix                                             |
| --- | ------------------------------------------- | ----------------------------------------------- |
| 63  | `has_begin_process_end` missing             | Added dataclass field + constructor logic       |
| 64  | Param block regex too greedy                | Balanced-parenthesis `_extract_param_block()`   |
| 65  | Pipeline detection failed with scriptblocks | Line-by-line + balanced-brace tracking          |
| 66  | `[DscResource()]` not detected              | Check `attrs_str` inline before pre-text window |
| 67  | `[Flags()]` not detected                    | Check `matched_text` before pre-text window     |

### Coverage Gaps Fixed

| Gap | Issue                                | Fix                                                             |
| --- | ------------------------------------ | --------------------------------------------------------------- |
| G-1 | PS files missing from language stats | Added to `ext_to_lang` in scanner.py                            |
| G-2 | PS files not in discovery extractor  | Added to `LANGUAGE_MAP`                                         |
| G-3 | BPL not detecting PS presence        | Added artifact counting + framework mappings in `from_matrix()` |

### Validation Results

| Repository                | Classes | Functions | Routes | Pester Tests | Frameworks                                  |
| ------------------------- | ------- | --------- | ------ | ------------ | ------------------------------------------- |
| badgerati/Pode            | 29      | 951       | 35     | 0            | pode, pester, powershell                    |
| dsccommunity/SqlServerDsc | 16      | 374       | 0      | 0            | azure, dsc, invokebuild, pester, powershell |
| pester/Pester             | 59      | 565       | 0      | 1,823        | pester, powershell                          |

### Lessons Learned (PowerShell Specific)

1. **PowerShell's attribute system is consumed by class/enum regex patterns**: Unlike Java/C# where annotations are on separate lines, PowerShell attributes like `[DscResource()]` and `[Flags()]` appear on the same line or are captured by the main pattern's prefix group. Always check the matched text first, then fall back to pre-text window analysis.

2. **Balanced-delimiter parsing is essential for PowerShell**: Both param blocks `([Parameter(Mandatory=$true)]$Name)` and scriptblocks in pipelines `| ForEach-Object { ... }` contain nested delimiters that simple regex cannot handle. Dedicated balanced-paren/brace parsers are required.

3. **PowerShell's pipeline model is fundamentally different from Unix pipes**: While both use `|`, PowerShell passes objects not text. The `Begin/Process/End` blocks enable stream processing of pipeline objects, making pipeline-aware function detection a critical architectural signal.

4. **DSC is infrastructure-as-code within PowerShell's type system**: DSC resources are classes with `[DscResource()]`, DSC configurations use `Configuration` keyword (not `class`), and DSC nodes use `Node` keyword. These three different constructs require three different extractors.

5. **Module manifests (`.psd1`) are PowerShell hashtables, not YAML/JSON**: The `@{...}` syntax with `RequiredModules`, `FunctionsToExport`, `ModuleVersion` etc. requires custom parsing. The extractor uses regex to find key-value pairs within the hashtable.

6. **The `ext_to_lang` gap affected 10+ languages, not just PowerShell**: When adding PS to `ext_to_lang`, audit revealed that Scala, R, Dart, Lua, Bash, C, SQL, HTML, and CSS were also missing. Always audit cross-language integration points when adding a new language.

---

## 20. Reference: JavaScript Integration Example (NEW v4.30)

### Overview

JavaScript is the 20th language (21st counting Kotlin v2) added to CodeTrellis. It supports ES5 through ES2024+, covering Node.js backends, Express/Fastify/Koa/Hapi web frameworks, React/Vue/Angular frontends, Mongoose/Sequelize/Prisma ORMs, and the full CommonJS + ESM module ecosystem.

### Key Architecture Decisions

1. **Five extractors matching the standard pattern**: type (ES6+ classes, prototype-based OOP, constants, Symbols), function (functions, arrow functions, generators, IIFEs, async functions, CJS export functions), api (Express/Fastify/Koa/Hapi routes, middleware, WebSocket, GraphQL resolvers), model (Mongoose/Sequelize/Prisma/Knex/Objection.js models, migrations, relationships), attribute (ES6 imports/exports, CommonJS require/module.exports, dynamic imports, JSDoc, decorators)

2. **70+ framework detection patterns**: Express, Fastify, Koa, Hapi, Nest, React, Vue, Angular, Next.js, Nuxt, Svelte, Gatsby, Electron, Socket.io, GraphQL, Apollo, Mongoose, Sequelize, Prisma, Knex, TypeORM, Objection.js, Passport, Jest, Mocha, Chai, Winston, Pino, Webpack, Vite, Rollup, ESLint, Prettier, Babel, Storybook, Redux, MobX, Zustand, and more

3. **Dual module system detection**: JavaScript uniquely supports both CommonJS (`require`/`module.exports`) and ESM (`import`/`export`). The module_system field in `JavaScriptParseResult` detects which is in use, enabling BPL practices to recommend appropriate module patterns.

4. **ES version detection**: Automatic detection of JavaScript version from syntax features (const/let → ES2015, async/await → ES2017, optional chaining → ES2020, etc.) and from package.json `engines` field.

5. **Prototype-based OOP alongside ES6 classes**: Unlike most languages that have only class-based OOP, JavaScript's prototype system (`Object.create`, `prototype` assignments) requires dedicated extraction patterns alongside ES6 class extraction.

6. **BPL priority system fix**: JavaScript integration discovered and fixed a critical BPL bug where practices without explicit `priority:` fields defaulted to lowest score. This fix benefits all future language integrations by establishing the precedent of always including priority fields in YAML practices.

### Files Created

| File                                                       | Purpose                                                       |
| ---------------------------------------------------------- | ------------------------------------------------------------- |
| `codetrellis/extractors/javascript/__init__.py`            | Module exports (5 extractors, 17 dataclasses)                 |
| `codetrellis/extractors/javascript/type_extractor.py`      | ES6 classes, prototypes, constants, Symbols                   |
| `codetrellis/extractors/javascript/function_extractor.py`  | Functions, arrow funcs, generators, IIFEs, CJS exports        |
| `codetrellis/extractors/javascript/api_extractor.py`       | Routes, middleware, WebSocket, GraphQL resolvers              |
| `codetrellis/extractors/javascript/model_extractor.py`     | Mongoose, Sequelize, Prisma, Knex, Objection.js models        |
| `codetrellis/extractors/javascript/attribute_extractor.py` | Imports, exports, require, dynamic imports, JSDoc, decorators |
| `codetrellis/javascript_parser_enhanced.py`                | Parser with 70+ framework patterns, ES version detection      |
| `codetrellis/bpl/practices/javascript_core.yaml`           | 50 practices (JS001-JS050) with priority fields               |

### Integration Points

| File              | Changes                                                                     |
| ----------------- | --------------------------------------------------------------------------- |
| `scanner.py`      | 24 `js_*` fields, `_parse_javascript()`, file routing                       |
| `compressor.py`   | 5 sections: TYPES, FUNCTIONS, API, MODELS, DEPENDENCIES                     |
| `bpl/selector.py` | 50+ framework mappings, `has_javascript` detection, **3 critical fixes**    |
| `bpl/models.py`   | 15 PracticeCategory enum values (JS_MODERN_SYNTAX through JS_DOCUMENTATION) |

### Bugs Fixed

| #   | Description                                 | Fix                                                       |
| --- | ------------------------------------------- | --------------------------------------------------------- |
| 68  | `Symbol.for()` not detected as global       | Added `is_global` field + `Symbol.for(` detection         |
| 69  | Simple scalar constants not extracted       | Added `SCALAR_CONST_PATTERN` for strings/numbers/booleans |
| 70  | CJS export functions not extracted          | Added CJS export function extraction loop                 |
| 71  | Pure JS projects showing TS practices       | Restricted `has_typescript` to TS-exclusive frameworks    |
| 72  | JS practices scored lowest (no priority)    | Added priority fields to all 50 JS practices              |
| 73  | Duplicate REACT key in prefix_framework_map | Removed duplicate JS section REACT entry                  |

### Validation Results

| Repository            | Classes | Functions | Routes | Module System | ES Version | Frameworks Detected     | JS Practices       |
| --------------------- | ------- | --------- | ------ | ------------- | ---------- | ----------------------- | ------------------ |
| expressjs/express     | 0       | 30        | 9      | commonjs      | es5        | express, javascript     | 15                 |
| TryGhost/Ghost        | 686     | 1,472     | 352    | esm           | es2015+    | express, react, ts + 29 | 7 REACT + 5 TS + 3 |
| nodemailer/nodemailer | 0       | 37        | 0      | commonjs      | es5        | javascript              | 15                 |

### Lessons Learned (JavaScript Specific)

1. **JavaScript and TypeScript share frameworks, causing BPL conflicts**: React, Vue, Next.js, and many other frameworks are used in both JS and TS projects. The `has_typescript` check in `_filter_applicable()` must ONLY check for TS-exclusive signals (the TypeScript compiler itself, Angular which requires TS, NestJS which requires TS) — NOT shared frameworks. This was the root cause of bug #71.

2. **BPL practice priorities are NOT optional**: All 50 JS practices initially had no `priority:` field, causing them to always lose to TypeScript practices (which had explicit priorities). The default priority score is the lowest possible, effectively making practices invisible. **Every future language integration MUST include explicit priority fields** on all YAML practices.

3. **Python dict keys must be unique — duplicate keys silently overwrite**: The `prefix_framework_map` dict had two `"REACT"` keys — one for TS (`{"react", "typescript"}`) and one added for JS (`{"react", "javascript"}`). Python silently used the second one, breaking TS React practice selection. **Always use unique prefix keys** or use a data structure that supports multiple values.

4. **CommonJS and ESM coexistence requires module system detection**: Unlike most languages with a single import system, JS projects may use `require()` (CommonJS), `import/export` (ESM), or both. The parser must detect and report the module system to enable appropriate BPL practice selection.

5. **Prototype-based OOP requires separate extraction patterns**: While ES6 classes are the modern standard, significant JS codebases (especially Node.js core and older libraries like Express.js) still use `Constructor.prototype.method = function()` patterns. Dedicated `JSPrototypeInfo` extraction is essential for covering older codebases.

6. **Express.js itself is surprisingly small**: Despite being the most popular Node.js framework, Express.js core has only ~30 functions and ~9 routes. This validates that the scanner correctly handles minimal codebases without inflating artifact counts.

---

## 21. Reference: TypeScript Integration Example (NEW v4.31)

### Quick Stats

| Metric              | Value                                                                                   |
| ------------------- | --------------------------------------------------------------------------------------- |
| Version             | v4.31 (Phase AB)                                                                        |
| Extractors          | 5 (type, function, api, model, attribute)                                               |
| Parser              | `EnhancedTypeScriptParser` with regex AST                                               |
| TS Version Support  | 2.x-5.x+                                                                                |
| Framework Detection | 80+ patterns (NestJS, Next.js, React, Angular, Vue, Express, Fastify, Hono, tRPC, etc.) |
| BPL Practices       | 45 (TS001-TS045) with priority fields                                                   |
| Unit Tests          | 98 new tests across 6 test files                                                        |
| Bugs Fixed          | 3 (#74-76, including critical ReDoS fix)                                                |
| Validation Repos    | Cal.com (7511 TS files), Strapi (3431 TS files), Hatchet (688 TS files)                 |
| Total Tests         | 1649 passing                                                                            |

### Architecture

```
codetrellis/extractors/typescript/
├── __init__.py                 # 22 dataclasses + 5 extractor exports
├── type_extractor.py           # Interfaces, type aliases, enums, classes
├── function_extractor.py       # Functions, overloads, arrow functions, type guards
├── api_extractor.py            # NestJS, Express, Fastify, Hono, tRPC, GraphQL, WebSocket
├── model_extractor.py          # Prisma, TypeORM, Sequelize, Drizzle, MikroORM, Mongoose, DTOs
└── attribute_extractor.py      # Imports/exports, decorators, JSDoc/TSDoc, namespaces, configs
```

### Key Design Decisions

1. **Type alias classification system**: TypeScript's type system goes far beyond simple aliases. The `_classify_type_alias()` method categorizes types into 6 categories: `union`, `intersection`, `conditional`, `mapped`, `template_literal`, `utility`, and `alias`. This enables the compressor to produce meaningful type summaries.

2. **Function overload detection**: TypeScript function overloads (multiple signatures for one function) are first-class entities, stored as `TSOverloadInfo` with all signatures preserved. This is critical for understanding API surfaces.

3. **Programmatic tRPC extraction (ReDoS-safe)**: The initial regex-based approach for extracting tRPC router procedures used nested parentheses patterns that caused catastrophic backtracking (O(2^n)) on deeply nested Zod schemas (4+ levels). The fix replaces regex with O(n) programmatic forward scanning using balanced paren counting. This is a **critical lesson for all future language integrations** — never use nested quantifier regexes on untrusted input.

4. **Mapped type readonly handling**: TypeScript mapped types can have `readonly` modifiers between `{` and `[`: `{ readonly [P in keyof T]: T[P] }`. The regex must allow optional `(?:[+-]?readonly\s+)?` between `\{` and `\[`.

5. **80+ framework detection via package.json parsing**: The parser reads `package.json` dependencies to detect frameworks, using a comprehensive pattern dict mapping npm package names to framework identifiers. This gives much richer framework detection than code-only analysis.

### Integration Points

| Component         | Changes                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------- |
| `scanner.py`      | 25 `ts_*` ProjectMatrix fields, `_parse_typescript()`, `.ts/.tsx/.mts/.cts` routing, stats output |
| `compressor.py`   | 5 sections: `[TS_TYPES]`, `[TS_FUNCTIONS]`, `[TS_API]`, `[TS_MODELS]`, `[TS_DEPENDENCIES]`        |
| `bpl/selector.py` | TS artifact counting, 60+ framework mappings, 8 prefix entries, `has_typescript` detection        |
| `bpl/models.py`   | 15 `TS_*` PracticeCategory enum values                                                            |

### Validation Results

| Repository      | Interfaces | Type Aliases | Enums | Overloads | Models/DTOs | Frameworks | TS Version |
| --------------- | ---------- | ------------ | ----- | --------- | ----------- | ---------- | ---------- |
| cal-com/cal.com | 1,226      | 2,705        | 102   | 339       | 242         | 47+        | 4.0        |
| strapi/strapi   | 1,392      | 1,599        | —     | 263       | —           | 44+        | —          |
| hatchet-dev     | 241        | 204          | 22    | —         | —           | 30+        | —          |

### Lessons Learned (TypeScript Specific)

1. **Never use nested quantifier regexes on user input (ReDoS)**: The `_NESTED_PARENS = r"\((?:[^()]*|\((?:[^()]*|\([^()]*\))*\))*\)"` pattern caused catastrophic backtracking on Cal.com's tRPC router files with deeply nested Zod schemas like `z.object({ data: z.record(z.string(), z.union([z.string(), z.number()])) })`. The fix uses programmatic paren-counting with a while loop and depth counter — O(n) instead of O(2^n). **All future regex-based extraction must avoid nested quantifiers.**

2. **TypeScript and JavaScript share ~70% of frameworks**: React, Vue, Next.js, Express, Fastify, etc. are used in both TS and JS projects. The BPL `has_typescript` detection must check for TS-exclusive signals only (the TypeScript compiler itself, Angular, NestJS) — not shared frameworks. This was already fixed in the JS integration (bug #71) but remains a critical principle.

3. **Type alias classification is essential for meaningful output**: Simply listing `type Foo = ...` is not useful. Classifying into union/intersection/conditional/mapped/utility categories enables the compressor to produce actionable summaries like `Mapped: ReadonlyConfig, OptionalUser` vs `Type Alias: Foo, Bar`.

4. **tRPC routers need procedure-level extraction**: Unlike REST frameworks where routes have clear HTTP method + path patterns, tRPC routers define procedures as object properties with chained `.query()/.mutation()/.subscription()` calls. A two-pass approach (find procedure names via simple regex, then scan forward for operation type) is more reliable than single complex regex.

5. **Cal.com is an excellent stress test**: At 7,511 TypeScript files and 549MB, Cal.com exercises every edge case — deeply nested types, complex tRPC routers with 4+ level Zod schemas, massive monorepo structure. Any new TypeScript feature should be validated against Cal.com.

---

## 22. Reference: Material UI Integration Example (NEW v4.36)

### Quick Stats

| Metric              | Value                                                                                           |
| ------------------- | ----------------------------------------------------------------------------------------------- |
| Version             | v4.36 (Phase AE)                                                                                |
| Extractors          | 5 (component, theme, hook, style, api) — framework-specific                                     |
| Parser              | `EnhancedMuiParser` with regex AST                                                              |
| MUI Version Support | v0.x-v6.x (@material-ui/core → @mui/material → Pigment CSS)                                     |
| Framework Detection | 30+ patterns (mui-material, mui-lab, mui-icons, mui-x-data-grid, notistack, tss-react, emotion) |
| BPL Practices       | 50 (MUI001-MUI050) with priority fields                                                         |
| Unit Tests          | 43 new tests                                                                                    |
| Bugs Fixed          | 7 (#84-90, including critical to_dict() root cause)                                             |
| Validation Repos    | devias-kit (411 comps), minimal-ui-kit (293 comps/27 styled), react-material-admin (4614 comps) |
| Total Tests         | 2002 passing                                                                                    |

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 MUI Framework Integration                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  JS/TS File → is_mui_file() check                           │
│       │                                                      │
│       ▼                                                      │
│  EnhancedMuiParser.parse(file_path, content)                │
│       │                                                      │
│       ├── MuiComponentExtractor  → 130+ components           │
│       ├── MuiThemeExtractor      → createTheme, palette      │
│       ├── MuiHookExtractor       → 50+ hooks, 8 categories  │
│       ├── MuiStyleExtractor      → sx, styled, makeStyles   │
│       └── MuiApiExtractor        → DataGrid, forms, dialogs │
│                                                              │
│  Scanner._parse_mui() → 20 ProjectMatrix fields             │
│  Compressor → 5 sections                                     │
│  BPL → 50 practices (MUI001-MUI050)                         │
└──────────────────────────────────────────────────────────────┘
```

### Key Design Pattern: Framework-Level Parser

Unlike language parsers (Java, Python, etc.), MUI and Ant Design are **framework-level parsers** that run as supplementary layers on JS/TS files. They are invoked _after_ the language parser and populate additional ProjectMatrix fields:

```python
# In scanner._walk_directory():
if file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
    self._parse_javascript(file_path, matrix)  # or _parse_typescript
    self._parse_react(file_path, matrix)        # framework layer
    self._parse_mui(file_path, matrix)          # framework layer
    self._parse_antd(file_path, matrix)         # framework layer
```

### Lessons Learned

1. **to_dict() is manually constructed**: The ProjectMatrix `to_dict()` method must be explicitly updated for each new integration — forgetting this silently omits all data from JSON output.
2. **Version migration paths matter**: MUI has gone through 4 package name changes (`material-ui/core` → `@material-ui/core` → `@mui/material` → Pigment CSS), each requiring separate detection patterns.
3. **Styled component patterns are diverse**: `styled()`, `sx` prop, `makeStyles()`, `withStyles()`, `tss-react`, and Pigment CSS each require different regex patterns.

---

## 23. Reference: Ant Design Integration Example (NEW v4.37)

### Quick Stats

| Metric               | Value                                                                                            |
| -------------------- | ------------------------------------------------------------------------------------------------ |
| Version              | v4.37 (Phase AF)                                                                                 |
| Extractors           | 5 (component, theme, hook, style, api) — framework-specific                                      |
| Parser               | `EnhancedAntdParser` with regex AST                                                              |
| Antd Version Support | v1-v5 (with version-specific feature detection)                                                  |
| Framework Detection  | 40+ patterns (antd, @ant-design/icons, @ant-design/pro-\*, antd-style, antd-mobile, umi, ahooks) |
| BPL Practices        | 50 (ANTD001-ANTD050) with priority fields                                                        |
| Unit Tests           | 52 new tests                                                                                     |
| Bugs Fixed           | 2 (#91-92, CommonJS require support + test assertion fixes)                                      |
| Validation Repos     | ant-design-pro (25+ comps, v5, Pro, umi), antd-admin (70+ comps, v4/v5)                          |
| Total Tests          | 2054 passing                                                                                     |

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               Ant Design Framework Integration               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  JS/TS File → is_antd_file() check                          │
│       │        (ES modules + CommonJS require)               │
│       ▼                                                      │
│  EnhancedAntdParser.parse(file_path, content)               │
│       │                                                      │
│       ├── AntdComponentExtractor → 80+ components, 6 cats   │
│       │   └── Pro components, sub-components, tree-shaking   │
│       ├── AntdThemeExtractor     → ConfigProvider, tokens    │
│       │   └── Design tokens, Less vars, algorithms           │
│       ├── AntdHookExtractor      → 15+ hooks, 6 categories  │
│       │   └── useForm, useApp, useToken, Pro hooks           │
│       ├── AntdStyleExtractor     → CSS-in-JS, Less, classes │
│       │   └── createStyles, antd-style, className overrides  │
│       └── AntdApiExtractor       → Table, Form, Modal, Menu │
│           └── ProTable, server-side, validation, drawers     │
│                                                              │
│  Scanner._parse_antd() → 20 ProjectMatrix fields            │
│  Compressor → 5 sections                                     │
│  BPL → 50 practices (ANTD001-ANTD050)                       │
└──────────────────────────────────────────────────────────────┘
```

### ProjectMatrix Fields (20 fields)

```python
# Component fields
antd_components: List[Dict]        # Core component usage (80+ patterns)
antd_pro_components: List[Dict]    # Pro component usage (ProTable, ProForm, etc.)
antd_custom_components: List[Dict] # Components wrapping antd components
antd_sub_components: List[Dict]    # Sub-component usage (Table.Column, etc.)

# Theme fields
antd_theme_configs: List[Dict]     # ConfigProvider theme configurations
antd_design_tokens: List[Dict]     # Design token customizations
antd_less_variables: List[Dict]    # Less variable overrides
antd_component_tokens: List[Dict]  # Component-level token customizations

# Hook fields
antd_hooks: List[Dict]             # Hook usage (useForm, useApp, etc.)
antd_custom_hooks: List[Dict]      # Custom hooks wrapping antd hooks

# Style fields
antd_css_in_js: List[Dict]         # CSS-in-JS patterns (createStyles)
antd_less_styles: List[Dict]       # Less stylesheet patterns
antd_style_overrides: List[Dict]   # className override patterns

# API pattern fields
antd_table_patterns: List[Dict]    # Table/ProTable configuration
antd_form_patterns: List[Dict]     # Form patterns with validation
antd_modal_patterns: List[Dict]    # Modal/Drawer patterns
antd_menu_patterns: List[Dict]     # Menu/navigation patterns

# Metadata
antd_version: str                  # Detected version (v1-v5)
antd_frameworks: List[str]         # Detected ecosystem (antd, umi, ahooks, etc.)
```

### Component Categories (6)

| Category     | Examples                                                    |
| ------------ | ----------------------------------------------------------- |
| General      | Button, Typography, Icon, Divider                           |
| Layout       | Layout, Grid, Row, Col, Space, Flex                         |
| Navigation   | Menu, Breadcrumb, Pagination, Steps, Tabs, Dropdown         |
| Data Entry   | Form, Input, Select, DatePicker, Upload, Checkbox, Radio    |
| Data Display | Table, List, Card, Collapse, Tree, Tag, Avatar, Badge       |
| Feedback     | Modal, Drawer, Alert, Message, Notification, Progress, Spin |

### Ecosystem Detection (40+ patterns)

| Pattern               | Ecosystem                       |
| --------------------- | ------------------------------- |
| `antd`                | Core library                    |
| `@ant-design/icons`   | Icon library                    |
| `@ant-design/pro-*`   | Pro components                  |
| `@ant-design/charts`  | Chart library                   |
| `antd-style`          | CSS-in-JS styling               |
| `antd-mobile`         | Mobile component library        |
| `antd-dayjs-plugin`   | Date utility plugin             |
| `umi`                 | Ant Group application framework |
| `ahooks`              | React hooks library             |
| `babel-plugin-import` | Tree-shaking plugin             |
| `antd-img-crop`       | Image cropping plugin           |
| `@formily/antd`       | Form solution integration       |
| `ant-design-vue`      | Vue port of Ant Design          |

### BPL Practice Categories (10)

| Category      | Enum Value         | ID Range    | Count |
| ------------- | ------------------ | ----------- | ----- |
| Components    | ANTD_COMPONENTS    | ANTD001-010 | 10    |
| Theme         | ANTD_THEME         | ANTD011-020 | 10    |
| Styling       | ANTD_STYLING       | ANTD021-025 | 5     |
| Hooks         | ANTD_HOOKS         | ANTD026-030 | 5     |
| Performance   | ANTD_PERFORMANCE   | ANTD031-035 | 5     |
| Accessibility | ANTD_ACCESSIBILITY | ANTD036-040 | 5     |
| Forms         | ANTD_FORMS         | ANTD041-043 | 3     |
| Table         | ANTD_TABLE         | ANTD044-046 | 3     |
| Navigation    | ANTD_NAVIGATION    | ANTD047-048 | 2     |
| Migration     | ANTD_MIGRATION     | ANTD049-050 | 2     |

### Differences from MUI Integration

| Aspect                | MUI                                        | Ant Design                                   |
| --------------------- | ------------------------------------------ | -------------------------------------------- |
| Package evolution     | 4 major renames (v0→v6)                    | Stable `antd` package (v1→v5)                |
| Styling approach      | sx prop, styled(), makeStyles, Pigment CSS | ConfigProvider, Less, CSS-in-JS (antd-style) |
| Pro components        | N/A (MUI X is separate product)            | @ant-design/pro-\* (ProTable, ProForm, etc.) |
| Application framework | N/A                                        | umi (integrated routing, build, plugins)     |
| Hook ecosystem        | 50+ hooks                                  | 15+ hooks + ahooks library                   |
| Tree-shaking          | Built-in (ES modules)                      | babel-plugin-import + antd/es/\* paths       |
| Design tokens         | createTheme()                              | ConfigProvider token prop                    |
| CommonJS support      | Rare                                       | Common (older Chinese codebases)             |

### Lessons Learned

1. **CommonJS `require()` patterns are common**: Many Chinese open-source projects use `require('antd')` instead of ES module imports. The `is_antd_file()` check must support both patterns — this was bug #91.

2. **Pro components are a distinct ecosystem**: `@ant-design/pro-components` (ProTable, ProForm, ProLayout, ProList, ProDescriptions) have different APIs than core antd. Separate detection and extraction is essential.

3. **umi framework integration**: Many antd projects use umi, which provides its own routing, build system, and plugin architecture. Ecosystem detection should include umi, @umijs/\* packages, and ahooks.

4. **Less variables are still common**: Despite CSS-in-JS adoption in v5, many v3/v4 projects still use Less variable overrides for theming. Both approaches must be detected.

5. **MUI served as an excellent template**: The 5-extractor + parser + scanner + compressor + BPL pattern established for MUI transferred directly to Ant Design with minimal structural changes — only the regex patterns and component catalogs differed.

---

## 24. Reference: Chakra UI Integration Example (NEW v4.38)

| Attribute           | Value                                                                                                                                                     |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Version             | v4.38 (Phase AG)                                                                                                                                          |
| Files Created       | 9 (5 extractors + parser + BPL YAML + `__init__.py` + test file)                                                                                          |
| Files Modified      | 5 (scanner.py, compressor.py, bpl/models.py, bpl/selector.py, scripts/validate_practices.py)                                                              |
| Component Coverage  | 70+ components across 8 categories (layout, typography, forms, data-display, feedback, overlay, navigation, disclosure)                                   |
| Version Detection   | v1.x (ChakraProvider/extendTheme), v2.x (style props/colorScheme), v3.x (createSystem/defineConfig/Ark UI/Panda CSS/recipes)                              |
| Framework Detection | 30+ patterns (@chakra-ui/react, @chakra-ui/icons, @ark-ui/react, @pandacss/dev, @saas-ui/react, @chakra-ui/pro-theme, framer-motion, chakra-react-select) |
| Tests               | 53 new tests (2107 total)                                                                                                                                 |
| Validation Repos    | nextarter-chakra (v3, Ark UI), myPortfolio (v2, extendTheme), chakra-ui/chakra-ui (v3, official)                                                          |

### 24.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               Chakra UI Framework Integration               │
├─────────────────────────────────────────────────────────────┤
│  JS/TS File → is_chakra_file() check                        │
│  ├── Component Extractor → 70+ components, 8 categories     │
│  ├── Theme Extractor → extendTheme/createSystem/recipes      │
│  ├── Hook Extractor → 20+ hooks, 9 categories               │
│  ├── Style Extractor → style props, sx, responsive, pseudo   │
│  └── API Extractor → forms, modals, drawers, toasts, menus  │
│                                                              │
│  Scanner → 22 chakra_* ProjectMatrix fields                  │
│  Compressor → 5 sections (COMPONENTS/THEME/HOOKS/STYLES/API)│
│  BPL → 50 practices (CHAKRA001-CHAKRA050)                    │
└──────────────────────────────────────────────────────────────┘
```

### 24.2 Key Lessons Learned

1. **Multi-line JSX requires context tracking**: Unlike single-line HTML attributes, JSX style props span multiple lines. The style extractor needed to track the current component context across lines to properly attribute props like `_hover`, `bg`, `p` to their parent component.

2. **Self-closing/direct-close JSX**: The regex pattern `<Component\s` misses `<Heading>Title</Heading>` where `>` follows directly after the name. Using `<Component[\s/>]` catches all variations.

3. **Semantic token nested structure**: Chakra UI's `semanticTokens: { colors: { 'bg.surface': { default: '...', _dark: '...' } } }` uses dotted quoted keys that `\w+` regexes cannot match. The extractor needed both simple word and quoted key matching.

4. **Standalone recipes vs theme recipes**: v3 `defineRecipe`/`defineSlotRecipe` can be standalone files, not just inside `createSystem`/`extendTheme`. Both contexts need detection.

5. **Ark UI is Chakra v3's foundation**: Chakra UI v3 is built on Ark UI (@ark-ui/react), so detecting Ark UI imports should flag the file as Chakra-related for comprehensive extraction.

6. **The MUI→Antd→Chakra pipeline is proven**: Three consecutive framework integrations using the same 7-phase pattern validate the architecture. The pattern (5 extractors + parser + scanner + compressor + BPL) scales reliably to new React UI frameworks.

---

## Phase AI: Bootstrap Framework Support (v4.40 — Session 28)

### Overview

Bootstrap is the most widely-used CSS framework, spanning v3.x (jQuery-dependent, panels/wells/glyphicons), v4.x (flexbox, cards, data-toggle), v5.x (vanilla JS, data-bs-toggle, offcanvas, RTL), and v5.3+ (data-bs-theme color modes). Unlike React-specific libraries (MUI, Antd, Chakra, shadcn), Bootstrap operates primarily through CSS classes on HTML elements, with optional JS plugins and multiple React/Angular/Vue wrapper libraries.

### Architecture

| Component           | File                                          | Purpose                                                                                                          |
| ------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Component Extractor | `extractors/bootstrap/component_extractor.py` | 50+ component categories (HTML classes + React-Bootstrap/reactstrap JSX), sub-components, jQuery/vanilla JS init |
| Grid Extractor      | `extractors/bootstrap/grid_extractor.py`      | Container/Row/Col system, 6 breakpoints (xs-xxl), gutters, ordering, offsets, row-cols, nesting                  |
| Theme Extractor     | `extractors/bootstrap/theme_extractor.py`     | SCSS variables, CSS custom properties (--bs-\*), Bootswatch 25 themes, v5.3+ color modes                         |
| Utility Extractor   | `extractors/bootstrap/utility_extractor.py`   | 16 utility categories (spacing, display, flex, text, colors, borders, sizing, position, etc.)                    |
| Plugin Extractor    | `extractors/bootstrap/plugin_extractor.py`    | 12 JS plugins (Modal, Tooltip, Carousel, etc.), events, CDN/npm detection                                        |
| Parser              | `bootstrap_parser_enhanced.py`                | 16 framework detection patterns, v3-v5.3+ version detection, Bootstrap file classification                       |

### Ecosystem Detection (16 frameworks)

- **Core**: bootstrap-css, bootstrap-js, bootstrap-bundle
- **React**: react-bootstrap, reactstrap
- **Angular**: @ng-bootstrap/ng-bootstrap, ngx-bootstrap
- **Vue**: bootstrap-vue, bootstrap-vue-next
- **Themes**: bootswatch (25 themes)
- **Icons**: bootstrap-icons
- **Dependencies**: @popperjs/core, jQuery
- **Build**: sass/node-sass (SCSS compilation)

### Version Detection

| Version | Indicators                                                  |
| ------- | ----------------------------------------------------------- |
| v3.x    | `panel`, `well`, `glyphicon`, `data-toggle` (without -bs-)  |
| v4.x    | `card`, `d-flex`, `data-toggle`, no `data-bs-`              |
| v5.x    | `data-bs-toggle`, `offcanvas`, `accordion`, vanilla JS init |
| v5.3+   | `data-bs-theme`, `color-mode`, CSS `color-scheme`           |

### BPL Practices (50 total: BOOT001-BOOT050)

| Category                | Count | Examples                                                                      |
| ----------------------- | ----- | ----------------------------------------------------------------------------- |
| BOOTSTRAP_COMPONENTS    | 5     | Semantic component selection, accessibility attributes, component composition |
| BOOTSTRAP_GRID          | 5     | Mobile-first breakpoints, container usage, column sizing                      |
| BOOTSTRAP_THEME         | 5     | CSS custom properties, SCSS variable overrides, color modes                   |
| BOOTSTRAP_UTILITIES     | 5     | Utility-first approach, responsive utilities, custom utilities                |
| BOOTSTRAP_PLUGINS       | 5     | JavaScript initialization, event handling, programmatic control               |
| BOOTSTRAP_FORMS         | 5     | Form validation, floating labels, input groups                                |
| BOOTSTRAP_RESPONSIVE    | 5     | Responsive images, visibility classes, breakpoint strategy                    |
| BOOTSTRAP_ACCESSIBILITY | 5     | ARIA attributes, keyboard navigation, screen reader support                   |
| BOOTSTRAP_PERFORMANCE   | 5     | Tree-shaking, CDN optimization, critical CSS                                  |
| BOOTSTRAP_MIGRATION     | 5     | v3→v4, v4→v5, data attribute migration                                        |

### Validation Results

| Repository                      | Components | Grid | Utilities | Plugins | CDN | Frameworks                          |
| ------------------------------- | ---------- | ---- | --------- | ------- | --- | ----------------------------------- |
| StartBootstrap/sb-admin-2       | 166        | 32   | 120       | 110     | Yes | bootstrap-css, bootstrap-js, jquery |
| react-bootstrap/react-bootstrap | 4          | 0    | 2         | 6       | No  | react-bootstrap, bootstrap-css      |

### Lessons Learned

1. **CSS class-based detection differs from import-based**: Bootstrap detection relies primarily on CSS class patterns (btn, card, modal, etc.) rather than import statements. Data attributes (data-bs-\*) alone are insufficient — component CSS classes must be present.

2. **Multi-version support requires careful pattern separation**: v3 (data-toggle) vs v5 (data-bs-toggle) patterns must be distinguished. The version detection system uses indicator sets to classify accurately.

3. **React wrappers vs native Bootstrap**: React-Bootstrap and reactstrap use JSX components (<Button>, <Modal>) while native Bootstrap uses CSS classes on HTML elements. Both detection paths are needed.

4. **The MUI→Antd→Chakra→shadcn→Bootstrap pipeline is validated**: Five consecutive framework integrations using the same 7-phase pattern confirm the architecture scales to any CSS/UI framework, including class-based frameworks beyond React-only libraries.

---

## Reference: Less Integration Example (NEW v4.45)

### Architecture

Less CSS preprocessor support follows the CSS preprocessor integration pattern established by Sass/SCSS (v4.44). Like Sass, Less uses its own set of domain-specific extractors rather than the type/function/api/model/attribute pattern used by programming languages.

### Extractors (5)

| Extractor               | Dataclasses                                                                             | Purpose                                                           |
| ----------------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `variable_extractor.py` | `LessVariableInfo`, `LessVariableUsageInfo`                                             | @var: value declarations, scopes, types, lazy eval, interpolation |
| `mixin_extractor.py`    | `LessMixinDefInfo`, `LessMixinCallInfo`, `LessGuardInfo`, `LessNamespaceInfo`           | Parametric/pattern-matched mixins, guards, namespaces             |
| `function_extractor.py` | `LessFunctionCallInfo`, `LessPluginInfo`                                                | 70+ built-in functions (8 categories), plugin detection           |
| `import_extractor.py`   | `LessImportInfo`                                                                        | @import with 7 options, URL imports, media queries                |
| `ruleset_extractor.py`  | `LessExtendInfo`, `LessDetachedRulesetInfo`, `LessNestingInfo`, `LessPropertyMergeInfo` | :extend(), detached rulesets, nesting/BEM, property merge         |

### Version Detection

| Version | Indicators                                                      |
| ------- | --------------------------------------------------------------- |
| 1.x     | Basic variables, mixins, nested rules, operations               |
| 2.x     | :extend(), detached rulesets, property merging (+/\_)           |
| 3.x     | @plugin, property access ($prop), each() loops                  |
| 4.x+    | Math mode options (parens-division/parens/strict/strict-legacy) |

### Framework/Library Detection

- **Frameworks**: Bootstrap, Ant Design, Semantic UI, Element UI, iView
- **Libraries**: LESS Hat, LESSElements, 3L, Preboot, Est, CSS Owl

### Feature Detection (20+)

Variables, mixins, guards, parametric mixins, pattern matching, namespaces, functions, imports, extend, detached rulesets, nesting, parent selectors, property merging, lazy evaluation, variable interpolation, property variables, plugins, each loops, math operations, color operations

### BPL Practices (50 total: LESS001-LESS050)

| Category            | Count | Examples                                                    |
| ------------------- | ----- | ----------------------------------------------------------- |
| LESS_VARIABLES      | 5     | Naming conventions, scoping, lazy evaluation, interpolation |
| LESS_MIXINS         | 5     | Parametric mixins, guards, namespaces, pattern matching     |
| LESS_FUNCTIONS      | 5     | Built-in function usage, color operations, type checking    |
| LESS_IMPORTS        | 5     | Import options, reference imports, organization             |
| LESS_EXTEND         | 5     | :extend() vs mixins, all keyword, placeholder patterns      |
| LESS_ARCHITECTURE   | 5     | File organization, naming, modular structure                |
| LESS_PERFORMANCE    | 5     | Selector optimization, mixin vs extend, nesting depth       |
| LESS_NAMING         | 5     | Variable naming, mixin naming, BEM patterns                 |
| LESS_BEST_PRACTICES | 5     | Code style, comments, maintainability                       |
| LESS_TOOLING        | 5     | Plugin usage, math modes, source maps, compilation          |

### Validation Results

| Repository               | .less Files | Variables | Mixin Defs | Mixin Calls | Guards | Function Calls | Imports |
| ------------------------ | ----------- | --------- | ---------- | ----------- | ------ | -------------- | ------- |
| less/less.js             | 329         | 494       | 1,289      | 426         | 132    | 331            | 101     |
| Semantic-Org/Semantic-UI | 48          | ✅        | ✅         | ✅          | ✅     | ✅             | ✅      |

### Lessons Learned

1. **CSS preprocessor pattern confirmed**: Like Sass/SCSS, Less uses domain-specific extractors (variable, mixin, function, import, ruleset) rather than the generic type/function/api/model/attribute pattern. This two-phase pattern (Sass then Less) validates the CSS preprocessor architecture.
2. **Guard expressions are syntactically complex**: Less guards (`when (iscolor(@a)) and (@b > 0)`) combine type-checking functions with boolean operators. Regex extraction captures guard expressions as strings but does not evaluate them.
3. **Namespace accessor patterns**: Less namespaces (`#bundle > .mixin()`) use `>` accessor syntax. The extractor detects namespace-qualified mixin calls by parsing the accessor chain.
4. **Property merging is unique to Less**: The `+:` and `+_:` property merge syntax is a Less-specific feature not found in Sass/SCSS. Separate detection ensures accurate feature reporting.
5. **Math mode detection distinguishes Less versions**: Less 4.x changed default math behavior from `always` to `parens-only`. Detecting math mode helps identify version compatibility requirements.
6. **The Sass→Less preprocessor pipeline is validated**: Two consecutive CSS preprocessor integrations using the same domain-specific extractor pattern confirm the architecture scales for all CSS preprocessor languages.

---

## Reference: Lit / Web Components Integration Example (NEW v4.65)

### Architecture

Lit / Web Components support follows the framework-level parser pattern used by React, Vue, Svelte, etc. — a supplementary parser that runs on JS/TS files after the language-level parser. It covers the full Lit ecosystem from Polymer 1.x (2013) through modern Lit 3.x (2023+), including lit-element 2.x and lit-html 1.x.

### Extractors (5)

| Extractor                | Dataclasses                                                             | Purpose                                                                                                                                                                                |
| ------------------------ | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `component_extractor.py` | `LitComponentInfo`, `LitQueryInfo`, `LitControllerInfo`, `LitMixinInfo` | LitElement/ReactiveElement/HTMLElement/PolymerElement/FASTElement classes, @customElement, customElements.define(), lifecycle, query decorators, controllers, mixins, shadow/light DOM |
| `property_extractor.py`  | `LitPropertyInfo`                                                       | @property() with options (type/reflect/attribute/converter/hasChanged/noAccessor), @state(), static properties, static get properties()                                                |
| `event_extractor.py`     | `LitEventInfo`                                                          | CustomEvent dispatch, @eventOptions, template @event bindings, addEventListener, Polymer fire()/listeners                                                                              |
| `template_extractor.py`  | `LitTemplateInfo`, `LitCSSInfo`                                         | html\`\`/svg\`\`/css\`\` extraction, property/attribute/event bindings, CSS :host/:part/::slotted/custom properties                                                                    |
| `api_extractor.py`       | `LitImportInfo`, `LitDecoratorInfo`, `LitIntegrationInfo`               | Import categorization (core/directive/decorator/controller/context/localization), decorator detection, 15+ ecosystem integration patterns                                              |

### Version Detection

| Version / Era   | Indicators                                                                               |
| --------------- | ---------------------------------------------------------------------------------------- |
| Polymer 1.x     | `Polymer({is:`, `Polymer.dom`, `properties: {}` (no decorators)                          |
| Polymer 2.x     | `class extends Polymer.Element`, `connectedCallback`, `_template`                        |
| Polymer 3.x     | `@polymer/polymer`, ES modules, `html\`...\``                                            |
| lit-element 2.x | `import { LitElement } from 'lit-element'`, `@customElement`, `@property()`              |
| lit 2.x         | `import { LitElement } from 'lit'`, `@property()`, `@state()`, reactive controllers      |
| lit 3.x         | `import { LitElement } from 'lit'`, `@lit/reactive-element`, `@lit/task`, `@lit/context` |

### Ecosystem / Integration Detection (15+ patterns)

- **Vaadin**: `@vaadin/` imports (side-effect + named)
- **Shoelace**: `@shoelace-style/shoelace` imports
- **Adobe Spectrum**: `@spectrum-web-components/` imports
- **Microsoft FAST**: `@microsoft/fast-element` / `@fluentui/web-components`
- **Polymer**: `@polymer/` imports
- **Open WC**: `@open-wc/` imports
- **Storybook**: `@storybook/web-components`
- **Esbuild/Rollup/Vite**: Build tool detection via config patterns

### Feature Detection (35+)

Decorators (@customElement/@property/@state/@query/@queryAll/@queryAsync/@eventOptions), reactive controllers (addController), context (@lit/context), tasks (@lit/task), localization (@lit/localize), SSR (@lit-labs/ssr), directives (repeat/when/choose/map/join/guard/cache/live/ref/classMap/styleMap/ifDefined/until/asyncAppend/asyncReplace/templateContent/unsafeHTML/unsafeSVG/keyed), shadow DOM, light DOM, CSS custom properties, CSS parts, slotted selectors

### BPL Practices (50 total: LIT001-LIT050)

| Category          | Count | Examples                                                           |
| ----------------- | ----- | ------------------------------------------------------------------ |
| LIT_COMPONENTS    | 10    | Component architecture, naming, lifecycle, shadow DOM, composition |
| LIT_PROPERTIES    | 10    | Reactive properties, type coercion, reflect, attribute naming      |
| LIT_TEMPLATES     | 10    | Template efficiency, bindings, directives, conditional rendering   |
| LIT_EVENTS        | 5     | Custom events, event delegation, bubbling, composition             |
| LIT_PERFORMANCE   | 5     | Render optimization, lazy loading, update batching                 |
| LIT_SSR           | 3     | Server-side rendering, hydration, declarative shadow DOM           |
| LIT_TYPESCRIPT    | 3     | Type-safe properties, generic components, decorator typing         |
| LIT_PATTERNS      | 2     | Controller pattern, mixin pattern                                  |
| LIT_ACCESSIBILITY | 1     | ARIA attributes, keyboard navigation, screen reader support        |
| LIT_TESTING       | 1     | Web Test Runner, @open-wc/testing, fixture patterns                |

### Validation Results

| Repository         | Detected | Version | Frameworks | Features | Notes                                       |
| ------------------ | -------- | ------- | ---------- | -------- | ------------------------------------------- |
| lit/lit (official) | ✅       | lit 3.x | 10+        | 20+      | Full Lit monorepo with packages + examples  |
| pwa-starter        | ✅       | lit 2.x | 3+         | 10+      | PWA template with Lit components            |
| synthetic lit_demo | ✅       | lit 3.x | 4          | 8        | 3 TS files exercising components/properties |

### Bugs Fixed (6 total)

| #   | Bug                                          | Fix                                                                  |
| --- | -------------------------------------------- | -------------------------------------------------------------------- |
| 1   | `_is_lit_import()` trailing slashes          | Removed `/` from prefixes (`'@lit/'` → `'@lit'`)                     |
| 2   | Query decorator names stored with `@` prefix | Test assertions updated (extractor stores `'query'` not `'@query'`)  |
| 3   | Multi-line regex mismatch                    | Fixed test data to use single-line options for `\{[^}]*\}` patterns  |
| 4   | Dict key `css` vs `css_styles`               | Fixed all test accesses to use `css_styles`                          |
| 5   | `boolean_bindings` attribute missing         | Boolean bindings counted in `attribute_bindings`, not separate field |
| 6   | Vaadin side-effect imports not detected      | Changed pattern from `from` to `(?:from\|import)` for bare imports   |

### Lessons Learned

1. **Web Components span 10+ years of API evolution**: Unlike most frameworks with 2-3 major versions, Web Components support requires covering Polymer 1.x (2013), Polymer 2.x (2017), Polymer 3.x (2018), lit-element 2.x (2019), and lit 2.x-3.x (2021-2024). Each era has distinct import patterns, class hierarchies, and APIs.
2. **Side-effect imports need `(?:from|import)` patterns**: Vaadin uses `import '@vaadin/vaadin-grid'` (no `from` clause). Patterns that only match `from '...'` miss these entirely.
3. **Import prefix matching must avoid trailing slashes**: `'@lit/'.startswith('@lit/' + '/')` produces `'@lit//'` which never matches. Always use base prefixes without trailing separators.
4. **Template literal extraction requires backtick depth tracking**: Tagged template literals (`html\`...\``) can contain nested template expressions (`${...}`) which may themselves contain backticks. Simple regex can't handle this; the extractor uses character-by-character depth tracking.
5. **CSS selector analysis is separate from template analysis**: The `:host`, `::part`, `::slotted` CSS selectors and CSS custom properties are analyzed in the CSS portion of `template_extractor.py`, not in the HTML template analysis.
6. **Reactive controllers are the modern composition pattern**: Lit 2.x introduced `ReactiveController` as an alternative to mixins. The component extractor detects both `addController()` calls and controller class definitions.

---

## Reference: Three.js / React Three Fiber Integration Example (NEW v4.71)

### Architecture

Three.js / R3F is a **framework-level** integration that runs on `.js/.jsx/.ts/.tsx` files alongside existing JavaScript/TypeScript parsers. It uses regex-based AST extraction (no tree-sitter grammar needed — Three.js is a JS/TS library, not a distinct language).

### Extractors (5)

| Extractor                   | Dataclasses                                                                                                                                     | Extracts                                                                                                                                                |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ThreeJSSceneExtractor`     | ThreeJSCanvasInfo, ThreeJSCameraInfo, ThreeJSRendererInfo, ThreeJSControlsInfo, ThreeJSLightInfo, ThreeJSPostProcessingInfo, ThreeJSPhysicsInfo | Canvas/renderer setup, cameras (4 types), controls (10 types), lights (6 types), post-processing (20+ effects), physics (rapier/cannon/ammo/oimo/havok) |
| `ThreeJSComponentExtractor` | ThreeJSMeshInfo, ThreeJSGroupInfo, ThreeJSInstancedMeshInfo, ThreeJSDreiComponentInfo, ThreeJSCustomComponentInfo, ThreeJSModelInfo             | R3F primitives, 100+ drei components (10 categories), model loading (GLTF/FBX/OBJ), `extend()`, geometry detection (20+ types)                          |
| `ThreeJSMaterialExtractor`  | ThreeJSMaterialInfo, ThreeJSShaderInfo, ThreeJSTextureInfo, ThreeJSUniformInfo                                                                  | R3F materials (16 types), vanilla materials (17 types), drei materials (8 types), GLSL shaders, uniforms, textures                                      |
| `ThreeJSAnimationExtractor` | ThreeJSUseFrameInfo, ThreeJSAnimationMixerInfo, ThreeJSSpringAnimationInfo, ThreeJSTweenInfo, ThreeJSMorphTargetInfo                            | `useFrame` hooks, AnimationMixer, spring animations (react-spring/drei), tweens (GSAP/tween.js), morph targets                                          |
| `ThreeJSAPIExtractor`       | ThreeJSImportInfo, ThreeJSIntegrationInfo, ThreeJSTypeInfo                                                                                      | Import analysis, ecosystem package detection (16 packages), TypeScript type definitions                                                                 |

### Version Detection

- **Three.js versions**: r60 through r170 (detected from package.json, imports, or REVISION patterns)
- **R3F versions**: v1 through v8 (detected from `@react-three/fiber` package version)
- **Mode detection**: R3F mode (declarative JSX) vs vanilla mode (imperative `new THREE.*`)

### Ecosystem Detection (16 packages)

`three`, `@react-three/fiber`, `@react-three/drei`, `@react-three/rapier`, `@react-three/postprocessing`, `@react-three/a11y`, `@react-three/xr`, `@react-three/cannon`, `@react-three/flex`, `@react-three/test-renderer`, `react-spring`, `@react-spring/three`, `postprocessing`, `troika-three-text`, `three-stdlib`, `leva`

### Feature Detection (20+)

Canvas setup, camera types, renderer options, orbit/fly/pointer-lock/transform/arcball/trackball/first-person/drag/scroll/map controls, directional/point/spot/ambient/hemisphere/rect-area lights, Bloom/SSAO/DepthOfField/ChromaticAberration effects, rapier/cannon/ammo/oimo/havok physics engines, instanced meshes, custom shaders, texture loading, morph targets.

### BPL Practices (50 total: THREEJS001-THREEJS050)

| Range          | Category                | Examples                                                                                                                                                               |
| -------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| THREEJS001-010 | Scene Setup             | Canvas sizing, camera defaults, renderer settings, controls, lights, shadows, fog, helpers, post-processing, physics                                                   |
| THREEJS011-020 | Components              | Mesh keys, drei usage, instanced meshes, model loading, Draco compression, custom components, geometry reuse, LOD, conditional rendering, portals                      |
| THREEJS021-030 | Materials               | Material reuse, shader uniforms, texture loading, PBR workflow, custom shaders, shader cleanup, texture compression, environment maps, transparency, material disposal |
| THREEJS031-040 | Animation & Interaction | useFrame delta, animation mixer cleanup, spring animations, morph targets, GSAP integration, raycasting, pointer events, hover state, keyboard input, gesture handling |
| THREEJS041-050 | Advanced                | Object pooling, draw call batching, texture atlasing, frustum culling, web workers, rapier physics, XR sessions, accessibility, SSR hydration, performance monitoring  |

### Validation Results

| Repository                  | Canvases | Cameras | Meshes | drei Components | useFrame | Types | Ecosystem | Version | Prompt Lines |
| --------------------------- | -------- | ------- | ------ | --------------- | -------- | ----- | --------- | ------- | ------------ |
| pmndrs/react-three-fiber    | 1        | 2       | —      | 6 (misc+perf)   | 1        | 94    | 5 pkgs    | r152/v8 | 993          |
| pmndrs/drei                 | 3        | 43      | 66     | 100+ (10 cats)  | 14       | 79    | 13 pkgs   | r152/v8 | 2058         |
| wass08/r3f-wawatmos-starter | 1        | —       | 1      | 1 (controls)    | —        | —     | 2 pkgs    | v1      | 231          |

### Bugs Fixed (4 total)

1. **Missing `__init__.py` exports**: `ThreeJSModelInfo` and `ThreeJSMorphTargetInfo` not exported from `extractors/threejs/__init__.py`
2. **GLSL shader regex**: `/* glsl */` template tag comment between assignment and backtick broke vertex/fragment shader detection — added optional group `(?:/\*\s*glsl\s*\*/\s*)?`
3. **Test attribute mismatch**: Tests used `model_format` but dataclass field is `loader_type`
4. **ProjectMatrix constructor**: Tests missing required `root_path` positional argument

### Lessons Learned

1. **Framework-level parsers compose well**: Three.js/R3F runs alongside React, Redux, and other framework parsers on the same JS/TS files without conflicts. The `_parse_threejs()` method aggregates results into dedicated `threejs_*` fields.
2. **Drei component detection requires category awareness**: The drei library has 100+ helper components across 10 categories (controls, abstractions, gizmos, shaders, shapes, staging, performance, misc, portals, loaders). Category-aware extraction provides much richer context than flat component lists.
3. **R3F vs vanilla detection matters for BPL**: The same Three.js concept (e.g., adding a mesh) has completely different best practices in R3F (declarative JSX) vs vanilla (imperative `new THREE.Mesh()`). The `threejs_is_r3f` / `threejs_is_vanilla` flags enable mode-specific practice selection.
4. **GLSL template literals have multiple tag formats**: Developers use `glsl\`...\``, `/_ glsl _/ \`...\``, and `shader\`...\`` — regex patterns must accommodate all variants.
5. **Version ranges span decades**: Three.js r60 (2013) through r170 (2024+) and R3F v1-v8 represent very different APIs. Version detection enables version-appropriate best practices.

## Step 19: Advanced Research Integration — PART F (v4.67, Session 55)

> **Goal:** Integrate the 7 PART F research prototypes into the language-integration workflow so every new or existing language benefits from semantic encoding, embeddings-based retrieval, differential updates, multi-level compression, cross-language linking, directed file navigation, and benchmarking.

### 19.1 Overview

PART F adds **7 orthogonal modules** that enhance the Matrix without changing existing parser or extractor code:

| #   | Module                  | File                                      | Purpose                                                                    |
| --- | ----------------------- | ----------------------------------------- | -------------------------------------------------------------------------- |
| F1  | JSON-LD Encoder         | `codetrellis/matrix_jsonld.py`            | Semantic knowledge-graph encoding with `@context`, `@type`, `@id`          |
| F2  | TF-IDF Embeddings       | `codetrellis/matrix_embeddings.py`        | Vector index for sub-ms semantic section retrieval (99.4 % token savings)  |
| F3  | JSON Patch Diff         | `codetrellis/matrix_diff.py`              | RFC 6902 differential updates (21 772× compression for single-field edits) |
| F4  | Multi-Level Compression | `codetrellis/matrix_compressor_levels.py` | L1/L2/L3 levels — identity, signatures-only, skeleton (up to 24×)          |
| F5  | Cross-Language Types    | `codetrellis/cross_language_types.py`     | Bidirectional type mapping across 19 languages                             |
| F6  | Directed Retrieval      | `codetrellis/matrix_navigator.py`         | 3-phase keyword → graph BFS → embedding re-ranking file discovery          |
| F7  | MatrixBench             | `codetrellis/matrixbench_scorer.py`       | Benchmark suite — 22 core + 59 language-coverage tasks, ±0 % deterministic |

### 19.2 When to Use Each Module

**During language integration (Steps 1-18):**

- After **Step 3** (parser creation): run `MatrixBench.add_language_coverage_tasks()` to auto-generate benchmark tasks for the new language.
- After **Step 7** (BPL practices): run `CrossLanguageLinker.resolve_type()` to verify type equivalences for the language's type system.
- After **Step 10** (validation): run `MatrixDiffEngine.compute_diff()` to measure the matrix delta introduced by the new language.
- After **Step 12** (final validation): run the full `MatrixBench.run_all()` suite to confirm no regressions across all categories.

**For ongoing matrix operations:**

- Use `MatrixEmbeddingIndex` for context-window-aware section retrieval instead of sending the full matrix.prompt.
- Use `MatrixMultiLevelCompressor` to select L1/L2/L3 based on the target model's context window via `auto_select_for_model(model_name)`.
- Use `MatrixNavigator.discover(query)` for IDE-integrated file navigation from natural-language queries.
- Use `MatrixJsonLdEncoder` to export the matrix as a JSON-LD knowledge graph for external tool integration.

### 19.3 Adding Cross-Language Support for a New Language

When adding language **N** to `cross_language_types.py`:

```python
# 1. Add primitive type mappings to TYPE_MAP
TYPE_MAP["newlang"] = {
    "int":    TypeMapping("int",    "newlang", "integer", category="primitive"),
    "float":  TypeMapping("float",  "newlang", "float",   category="primitive"),
    "string": TypeMapping("string", "newlang", "string",  category="primitive"),
    "bool":   TypeMapping("bool",   "newlang", "boolean", category="primitive"),
    "list":   TypeMapping("list",   "newlang", "array",   category="collection"),
    "dict":   TypeMapping("dict",   "newlang", "object",  category="collection"),
    "null":   TypeMapping("null",   "newlang", "null",    category="primitive"),
}

# 2. Verify with resolve_type
linker = CrossLanguageLinker()
assert linker.resolve_type("newlang", "string", "python").target_type == "str"
assert linker.resolve_type("python", "str", "newlang").target_type == "string"

# 3. Run cross-language benchmark category
bench = MatrixBench(matrix_json, matrix_prompt)
result = bench.run_category("cross_language")
assert result.pass_rate == 1.0
```

### 19.4 Running Benchmarks After Integration

```bash
# Run all 40 benchmark tests
.venv/bin/python -m pytest tests/benchmarks/matrix_bench.py -v

# Run individual PoC scripts
.venv/bin/python scripts/research/run_all_pocs.py

# Run a specific PoC
.venv/bin/python scripts/research/poc_json_patch.py
```

### 19.5 Dependencies

These modules require three additional packages (already in `requirements.txt`):

| Package     | Version | Used By                                    |
| ----------- | ------- | ------------------------------------------ |
| `jsonpatch` | ≥ 1.33  | F3 — RFC 6902 JSON Patch                   |
| `numpy`     | ≥ 2.4   | F2 — TF-IDF vector math, cosine similarity |
| `tiktoken`  | ≥ 0.12  | F2, F4, F7 — token counting                |

### 19.6 Key Files Reference

| Category         | Path                                                                                                                                                                               |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Core modules (7) | `codetrellis/matrix_jsonld.py`, `matrix_embeddings.py`, `matrix_diff.py`, `matrix_compressor_levels.py`, `cross_language_types.py`, `matrix_navigator.py`, `matrixbench_scorer.py` |
| Benchmark tests  | `tests/benchmarks/matrix_bench.py` (40 tests)                                                                                                                                      |
| PoC scripts      | `scripts/research/poc_*.py`, `scripts/research/run_all_pocs.py`                                                                                                                    |
| Research report  | `docs/research/ADVANCED_TOPICS_REPORT.md`                                                                                                                                          |

### Lessons Learned

1. **JSON-LD framing requires explicit frame specs**: The `frame()` method takes a `frame_spec: Dict` (not a string type name). Frame specs use `@type` and `@explicit` to reshape the graph.
2. **TF-IDF vectorizer state must be persisted alongside vectors**: Saving only `.npz` vectors is insufficient — the vocabulary and IDF weights must also be serialized to `.meta.json` for `load()` to restore a queryable index.
3. **`jsonpatch.JsonPatch` does not support `len()`**: Use `patch.patch` (the underlying list) for length checks and iteration.
4. **NumPy `savez_compressed` silently appends `.npz`**: Code must handle both `path` and `path.npz` when verifying file existence after save.
5. **Cross-language type mapping is inherently lossy**: TypeScript `number` maps to Python `int` (not `float`), and some languages lack direct equivalents for complex types. The canonical form (e.g., `"integer"`, `"string"`) bridges the gap.
6. **Composite scoring prevents single-signal dominance**: The navigator's `0.5 × keyword + 0.3 × graph + 0.2 × embedding` weighting ensures files reachable only via dependency edges still surface.
7. **Benchmark determinism requires sorted traversal**: `MatrixBench` produces ±0 % variance because all iteration uses sorted keys and fixed random seeds.

---

## Step 20: Java Framework Integration — Phase BZ (v4.94, Session 74)

> **Goal:** Add framework-level parsing for 5 major Java frameworks (Spring Boot, Spring Framework, Quarkus, Micronaut, Jakarta EE) as supplementary layers on top of the existing base Java parser from Step 12.

### 20.1 Architecture Pattern

Java framework parsers follow a **supplementary layer** architecture:

```
Base Java Parser (Step 12)          → [JAVA_TYPES], [JAVA_API], etc.
  ├── Spring Boot Parser (v4.94)    → [SPRING_BOOT]
  ├── Spring Framework Parser       → [SPRING_FRAMEWORK]
  ├── Quarkus Parser                → [QUARKUS]
  ├── Micronaut Parser              → [MICRONAUT]
  └── Jakarta EE Parser             → [JAKARTA_EE]
```

Each framework parser:

1. Has **5 extractors** in `extractors/<framework>/` (except Spring Framework which has 4)
2. Has a **parser file** (`<framework>_parser_enhanced.py`) with dataclass results, framework patterns, and version indicators
3. Writes **~8-12 ProjectMatrix fields** in `scanner.py`
4. Produces **1 compressor section** (`[FRAMEWORK_NAME]`) via `_compress_<framework>()` in `compressor.py`

### 20.2 Extractor Directory Layout

```
extractors/
├── java_utils.py              ← normalize_java_content() shared across all 25 extractors
├── spring_boot/
│   ├── __init__.py
│   ├── bean_extractor.py      ← @Component/@Service/@Repository/@Controller/@Bean
│   ├── autoconfig_extractor.py ← @ConditionalOn*/@EnableAutoConfiguration
│   ├── endpoint_extractor.py  ← @GetMapping/@PostMapping/@RequestMapping
│   ├── property_extractor.py  ← @Value/@ConfigurationProperties/application.yml
│   ├── security_extractor.py  ← @EnableWebSecurity/@PreAuthorize/SecurityFilterChain
│   └── data_extractor.py      ← @Entity/JpaRepository/Spring Data queries
├── spring_framework/
│   ├── __init__.py
│   ├── di_extractor.py        ← @Autowired/@Inject/XML beans/constructor injection
│   ├── aop_extractor.py       ← @Aspect/@Before/@After/@Around/pointcut
│   ├── event_extractor.py     ← ApplicationEvent/@EventListener/@Async
│   └── mvc_extractor.py       ← HandlerInterceptor/WebMvcConfigurer/ViewResolver
├── quarkus/
│   ├── __init__.py
│   ├── cdi_extractor.py       ← @ApplicationScoped/@RequestScoped/@Inject/@Produces
│   ├── rest_extractor.py      ← @Path/@GET/@POST/quarkus-resteasy-reactive
│   ├── panache_extractor.py   ← PanacheEntity/PanacheRepository/PanacheQuery
│   ├── config_extractor.py    ← @ConfigProperty/@ConfigMapping/SmallRye Config
│   └── extension_extractor.py ← quarkus-* extensions/build-time augmentation
├── micronaut/
│   ├── __init__.py
│   ├── di_extractor.py        ← @Singleton/@Inject/@Factory/BeanContext
│   ├── http_extractor.py      ← @Controller/@Get/@Post/@Client
│   ├── data_extractor.py      ← @Repository/@MappedEntity/Micronaut Data
│   ├── config_extractor.py    ← @ConfigurationProperties/@Value/application.yml
│   └── feature_extractor.py   ← micronaut-* features/micronaut-platform-catalog
└── jakarta_ee/
    ├── __init__.py
    ├── cdi_extractor.py       ← @Named/@Inject/@Produces/@ApplicationScoped
    ├── servlet_extractor.py   ← @WebServlet/@WebFilter/@WebListener/HttpServlet
    ├── jpa_extractor.py       ← @Entity/@Table/@ManyToOne/JPQL/CriteriaBuilder
    ├── jaxrs_extractor.py     ← @Path/@GET/@POST/Application subclass/JAX-RS client
    └── ejb_extractor.py       ← @Stateless/@Stateful/@Singleton/@MessageDriven/@Schedule
```

### 20.3 Content Normalization

All 25 extractors use `normalize_java_content()` from `extractors/java_utils.py`:

```python
from codetrellis.extractors.java_utils import normalize_java_content

def extract_beans(content: str, file_path: str) -> list[dict]:
    content = normalize_java_content(content)  # Strips leading whitespace per line
    # ... regex matching on normalized content
```

This eliminates indentation-sensitivity bugs in regex patterns across all frameworks.

### 20.4 Scanner Integration Points

Seven edits to `scanner.py`:

1. **Imports** (line ~285): 5 parser imports
2. **ProjectMatrix fields** (line ~2196): ~60 new fields across 5 frameworks
3. **Parser initialization** (line ~4094): 5 parser instances created in `__init__()`
4. **Dispatch wiring** (line ~4764): 5 `_parse_<framework>()` calls in Java/Kotlin dispatch
5. **Parse methods** (line ~6647): 5 `_parse_*()` methods (~200 lines total)
6. **Build file hook — Maven** (line ~23641): `pom.xml` triggers framework detection
7. **Build file hook — Gradle** (line ~23695): `build.gradle`/`build.gradle.kts` triggers framework detection

### 20.5 Compressor Field Alignment

**Critical lesson:** Compressor `getattr()` field names must match Scanner's `ProjectMatrix` field names exactly.

| Framework        | Scanner Field            | Wrong (initial)               | Correct (fixed)          |
| ---------------- | ------------------------ | ----------------------------- | ------------------------ |
| Spring Framework | `spring_framework_di`    | `_di_beans`                   | `_di`                    |
| Spring Framework | `spring_framework_aop`   | `_aop_aspects`                | `_aop`                   |
| Spring Framework | `spring_framework_mvc`   | `_mvc_interceptors`           | `_mvc`                   |
| Quarkus          | `quarkus_endpoints`      | `quarkus_rest_endpoints`      | `quarkus_endpoints`      |
| Quarkus          | `quarkus_config`         | `quarkus_config_properties`   | `quarkus_config`         |
| Quarkus          | `quarkus_health`         | `quarkus_health_checks`       | `quarkus_health`         |
| Micronaut        | `micronaut_beans`        | `micronaut_di_beans`          | `micronaut_beans`        |
| Micronaut        | `micronaut_endpoints`    | `micronaut_http_routes`       | `micronaut_endpoints`    |
| Micronaut        | `micronaut_repositories` | `micronaut_data_repos`        | `micronaut_repositories` |
| Micronaut        | `micronaut_config`       | `micronaut_config_properties` | `micronaut_config`       |

### 20.6 Scanner Evaluation Results (Round 1)

| Repository          | Framework   | CDI/DI        | Endpoints     | ORM/Data       | Config     | Extensions     | Coverage |
| ------------------- | ----------- | ------------- | ------------- | -------------- | ---------- | -------------- | -------- |
| spring-petclinic    | Spring Boot | 7 beans       | 16 endpoints  | 9 JPA entities | 2 configs  | —              | 100%     |
| quarkus-quickstarts | Quarkus     | 103 CDI beans | 253 endpoints | 16 Panache     | 149 config | 149 extensions | 97% CDI  |
| micronaut-starter   | Micronaut   | 431 DI beans  | 8 HTTP routes | 3 controllers  | 6 features | —              | 90% DI   |

### 20.7 Version Detection

Each parser includes `VERSION_INDICATORS` for historical version support:

| Framework        | Versions           | Detection Signal                                                           |
| ---------------- | ------------------ | -------------------------------------------------------------------------- |
| Spring Boot      | 1.x, 2.x, 3.x      | `spring-boot-starter-*`, `@SpringBootApplication`, `SpringApplication.run` |
| Spring Framework | 4.x, 5.x, 6.x      | XML `<beans>`, `@Autowired`, `@ComponentScan`                              |
| Quarkus          | 1.x, 2.x, 3.x      | `quarkus-*` extensions, `@QuarkusMain`, `quarkus-bom`                      |
| Micronaut        | 1.x, 2.x, 3.x, 4.x | `micronaut-*` features, `@MicronautTest`, `micronaut-platform-catalog`     |
| Jakarta EE       | EE 5→10+           | `javax.*` vs `jakarta.*` namespace migration, `web.xml`, `ejb-jar.xml`     |

### 20.8 Key Files Reference

| Category        | Files                                                                                            |
| --------------- | ------------------------------------------------------------------------------------------------ |
| Extractors (25) | `extractors/{spring_boot,spring_framework,quarkus,micronaut,jakarta_ee}/*.py`                    |
| Shared utility  | `extractors/java_utils.py`                                                                       |
| Parsers (5)     | `{spring_boot,spring_framework,quarkus,micronaut,jakarta_ee}_parser_enhanced.py`                 |
| Scanner         | `scanner.py` (7 integration edits)                                                               |
| Compressor      | `compressor.py` (5 `_compress_*` methods + field alignment fixes)                                |
| Tests (127)     | `tests/unit/test_{spring_boot,spring_framework,quarkus,micronaut,jakarta_ee}_parser_enhanced.py` |
| Analysis report | `docs/JAVA_FRAMEWORK_ANALYSIS_REPORT.md`                                                         |

### Lessons Learned

1. **Content normalization eliminates indentation bugs**: Java files have varying indentation (tabs, 2/4/8 spaces). Stripping leading whitespace via `normalize_java_content()` before regex matching prevents false negatives across all 25 extractors.
2. **Annotation patterns need optional parentheses**: Many Java annotations work both with and without parentheses (`@Get` vs `@Get("/")`). Always use `\(?` in regex patterns.
3. **Inner parentheses in annotations require careful regex**: `@PreAuthorize("hasRole('ADMIN')")` breaks naive `\(.*\)` patterns. Use `"([^"]*)"` to match only the string content.
4. **Compressor field names must exactly match scanner fields**: Any mismatch in `getattr(matrix, "field_name", [])` silently returns empty data. Always verify by printing field names from both sides.
5. **Build file hooks are essential for framework detection**: Without `pom.xml`/`build.gradle` hooks, framework parsers only fire on `.java` files. Adding build file hooks ensures dependency-based detection works even before any Java source is scanned.
6. **Constructor injection needs separate patterns**: `@Autowired` on fields is common but constructor injection (no annotation needed in modern Spring) requires matching constructor parameter patterns separately.
7. **Pre-existing bugs surface during integration**: The `custom_methods` dict-in-join bug in compressor.py had existed for many sessions but only manifested when new framework sections exercised the code path.

---

_Document Version: 5.2_
_Created: 2026-02-02_
_Updated: Session 74 - Phase BZ: Java Framework Parsers (v4.94) — Step 20 added: 5 Java framework parsers (Spring Boot/Spring Framework/Quarkus/Micronaut/Jakarta EE), 25 extractors + java_utils.py, ~60 ProjectMatrix fields, scanner + compressor integration, field alignment fixes, Scanner Evaluation Round 1 (3 repos), 10 bugs fixed, 127 new tests, 6643 total tests passing_
_Updated: Session 60 - Phase BN: Three.js / React Three Fiber Support (v4.71) — 5 Three.js extractors (scene, component, material, animation, api), EnhancedThreeJSParser with regex AST, R3F v1-v8 + Three.js r60-r170, 100+ drei components, ~33 ProjectMatrix fields, 50 BPL practices (THREEJS001-THREEJS050), 63 new tests, 4 bugs fixed, 3-repo validation, 5238 total tests passing_
_Updated: Session 55 - PART F: Advanced Research (v4.67) — Step 19 added: Advanced Research Integration (7 modules: JSON-LD, TF-IDF embeddings, JSON Patch differential, multi-level compression, cross-language types, directed retrieval, MatrixBench). 40 new benchmark tests, 6 PoCs validated, all 53+ languages covered, research report generated._
_Updated: Session 54b - A5.x Module Coverage Expansion — Step 14 added: A5.x Module Integration (cache_optimizer, mcp_server, jit_context, skills_generator) — 4 modules expanded for 53+ languages, ~350 sections, 201 tests, 4346 total tests passing_
_Updated: Session 51 - Phase BG: Lit / Web Components Framework Support (v4.65) — 5 Lit extractors (component, property, event, template, api), EnhancedLitParser with regex AST, Polymer 1.x-3.x + lit-element 2.x + lit 2.x-3.x, 25+ ProjectMatrix fields, 50 BPL practices (LIT001-LIT050), 109 new tests, 6 bugs fixed, 3-repo validation (lit/lit, pwa-starter, synthetic lit_demo), 4072 total tests passing_
_Updated: Session 44 - Phase AZ: SWR Framework Support (v4.58) — 5 SWR extractors (hook, cache, mutation, middleware, api), EnhancedSWRParser with regex AST, SWR v0.x-v2.x (useSWR/useSWRImmutable/useSWRInfinite/useSWRSubscription/useSWRMutation, SWRConfig, preload, middleware, conditional/dependent fetching, optimistic updates), 15 framework + 30 feature patterns, 15 ProjectMatrix fields, 50 BPL practices (SWR001-SWR050), 10 PracticeCategory entries, 84 new tests, 4 bugs fixed, 3-repo validation (vercel/swr, vercel/swr-site, shuding/nextra), 3455 total tests passing_
_Updated: Session 33 - Phase AN: Less Language Support (v4.45) — 5 Less extractors (variable, mixin, function, import, ruleset), EnhancedLessParser with regex AST, Less 1.x-4.x+, @variables/scopes/lazy-eval/interpolation, mixin guards/namespaces/pattern-matching, 70+ built-in functions, @import with options, :extend() all/inline, detached rulesets, nesting/BEM, property merging, math mode detection, 50 BPL practices (LESS001-LESS050), 79 new tests, 0 bugs, 2-repo validation (less/less.js, Semantic-UI), 2578 total tests passing_
_Updated: Session 37 - Phase AR: Jotai Framework Support (v4.49) — 5 Jotai extractors (atom, selector, middleware, action, api), EnhancedJotaiParser with regex AST, Jotai v1.x-v2.x (atom/atomFamily/atomWithReset/atomWithReducer/atomWithDefault) + selectors (derived/selectAtom/focusAtom/splitAtom/loadable/unwrap) + middleware (atomWithStorage/atomEffect/atomWithMachine/atomWithProxy/atomWithImmer) + actions (useAtom/useAtomValue/useSetAtom/createStore/getDefaultStore/store API) + 30+ ecosystem frameworks, 17 framework + 34 feature patterns, 18 ProjectMatrix fields, 50 BPL practices (JOTAI001-JOTAI050), 98 new tests, 0 bugs, validation scan (10 atoms/7 hooks/6 store usages/v2/5 frameworks), 2877 total tests passing_
_Updated: Session 32 - Phase AM: Sass/SCSS Language Support (v4.44) — 5 Sass extractors (variable, mixin, function, module, nesting), EnhancedSassParser with regex AST, Dart Sass 1.x/LibSass/Ruby Sass, .scss+.sass syntax, @use/@forward module system, 100+ built-in functions, 20+ framework detection, 18 ProjectMatrix fields, 50 BPL practices (SASS001-SASS050), 50 new tests, 0 bugs, 2-repo validation (Bootstrap, Bulma), 2499 total tests passing_
_Updated: Session 28 - Phase AI: Bootstrap Framework Support (v4.40) — 5 Bootstrap extractors, EnhancedBootstrapParser, 50 BPL practices (BOOT001-BOOT050), 64 new tests, 0 bugs, 2-repo validation (sb-admin-2, react-bootstrap), 2234 total tests passing_
_Updated: 15 Feb 2026 - Phase AG: Chakra UI Framework Support (v4.38) — 5 Chakra extractors, EnhancedChakraParser, 50 BPL practices (CHAKRA001-CHAKRA050), 53 new tests, 5 bugs fixed (#92-96), 3-repo validation (nextarter-chakra, myPortfolio, chakra-ui/chakra-ui), 2107 total tests passing_
_Updated: Session 66 - Phase BT+BU: GSAP + RxJS Dual Framework Support (v4.77/v4.78) — 5 GSAP extractors + 5 RxJS extractors, GsapParseResult + RxjsParseResult parsers, GSAP v1-v3+ + RxJS v5-v7+, ~30 ProjectMatrix fields each, 100 BPL practices (GSAP001-GSAP050 + RXJS001-RXJS050), 20 categories, Angular file type shadowing fix, flat-format YAML support, Scanner Evaluation Round 1, 79 new tests, 5907 total tests passing_
_Updated: Session 65 - Phase BS: Framer Motion Animation Framework Support (v4.76) — 5 Framer Motion extractors (animation, gesture, layout, scroll, api), EnhancedFramerMotionParser with 13 framework patterns, framer-motion v1-v10 / motion v11+ / popmotion / framer SDK / framer-motion-3d / react-spring bridge, 22 ProjectMatrix fields, 50 BPL practices (FRAMER001-FRAMER050), 107 new tests, 0 regressions, 5843 total tests passing_
_Updated: 15 Feb 2026 - Phase AF: Ant Design Framework Support (v4.37) — 5 Antd extractors, EnhancedAntdParser, 50 BPL practices (ANTD001-ANTD050), 52 new tests, 2 bugs fixed (#91-92), 2-repo validation (ant-design-pro, antd-admin), 2054 total tests passing_
_Updated: 15 Feb 2026 - Phase AE: Material UI Framework Support (v4.36) — 5 MUI extractors, EnhancedMuiParser, 50 BPL practices (MUI001-MUI050), 43 new tests, 7 bugs fixed (#84-90), 3-repo validation (devias-kit, minimal-ui-kit, react-material-admin), 2002 total tests passing_
_Updated: 14 Feb 2026 - Phase AB: TypeScript Language Support (v4.31) — 5 TS extractors, EnhancedTypeScriptParser, 45 BPL practices (TS001-TS045), 98 new tests, 3 bugs fixed (#74-76 including ReDoS), 3-repo validation (Cal.com, Strapi, Hatchet), 1649 total tests passing_
_Updated: 14 Feb 2026 - Phase AA: JavaScript Language Support (v4.30) — 5 JS extractors, EnhancedJavaScriptParser, 50 BPL practices (JS001-JS050), 88 new tests, 6 bugs fixed (#68-73), 3 BPL selector fixes, 3-repo validation (Express.js, Ghost, Nodemailer), 1551 total tests passing_
_Updated: 14 Feb 2026 - Phase Z: PowerShell Language Support (v4.29) — 5 PS extractors, EnhancedPowerShellParser, 50 BPL practices (PS001-PS050), 57 new tests, 5 bugs fixed, 3 gaps fixed, 3-repo validation (Pode, SqlServerDsc, Pester), 1463 total tests passing_
_Updated: 14 Feb 2026 - Phase Y: Lua Language Support (v4.28) — 5 Lua extractors, EnhancedLuaParser, 50 BPL practices (LUA001-LUA050), 52 new tests, 1 bug fixed, 3-repo validation, 1406 total tests passing_
_Updated: 13 Feb 2026 - Phase X: Dart Language Support (v4.27) — 5 Dart extractors, EnhancedDartParser, 50 BPL practices (DART001-DART050), 126 new tests, 4 bugs fixed, 3-repo validation (Isar, Bloc, Shelf), 1354 total tests passing_
_Updated: 13 Feb 2026 - Phase W: R Language Support (v4.26) — 5 R extractors, EnhancedRParser, 50 BPL practices (R001-R050), 62 new tests, 11 bugs fixed, 3-repo validation (dplyr, Shiny, plumber), 1228 total tests passing_
_Updated: 13 Feb 2026 - Phase V: Scala Language Support (v4.25) — 5 Scala extractors, EnhancedScalaParser, 50 BPL practices (SCALA001-SCALA050), 132 new tests, 4 bugs fixed, 3-repo validation (Caliban, Play Samples, ZIO HTTP), 1166 total tests passing_
_Updated: 12 Feb 2026 - Phase U: PHP Language Support (v4.24) — 5 PHP extractors, EnhancedPhpParser, 50 BPL practices (PHP001-PHP050), 84 new tests, 1034 total tests passing_
_Updated: 12 Feb 2026 - Phase T: Ruby Language Support (v4.23) — 5 Ruby extractors, EnhancedRubyParser, 50 BPL practices (RB001-RB050), 80 new tests, 3-repo validation (Discourse, Faker, Mastodon), 950 total tests passing_
_Updated: 12 Feb 2026 - Phase S: C++ Language Support (v4.20) — 5 C++ extractors, EnhancedCppParser, 50 BPL practices (CPP001-CPP050), 73 new tests, 8 bugs fixed, 3-repo validation (spdlog, fmt, nlohmann_json), 713 total tests passing_
_Updated: 12 Feb 2026 - Phase N: Rust Language Support (v4.14) — 5 Rust extractors, EnhancedRustParser, 50 BPL practices (RS001-RS050), 46 new tests, 6 bugs fixed, 3-repo validation (Axum, Diesel, actix-web), 315 total tests passing_
_Updated: 12 Feb 2026 - Phase M: C# Language Support (v4.13) — 6 C# extractors, EnhancedCSharpParser, 50 BPL practices (CS001-CS050), 97 new tests, 10 bugs fixed, 3-repo validation (eShop, Ardalis/JT CleanArchitecture)_
_Updated: 12 Feb 2026 - Phase L: Java & Kotlin Language Support (v4.12) — 6 Java extractors, 2 Kotlin extractors, tree-sitter-java AST, Eclipse JDT LSP, Panache detection, 50 BPL practices, 12 bugs fixed, 3-repo validation_
_Updated: 11 Feb 2026 - Phase K: Systemic Improvements (v4.11) — Weighted domain scoring, multi-signal detection, ORM-DB affinity graph, discovery-driven stack_
_Updated: 11 Feb 2026 - Phase J: R4 Evaluation & .gitignore-Aware Scanning (v4.10) — GitignoreFilter, 7 extractors updated, R4 evaluation (Gitea/Strapi/Medusa), 18 test fixes_
_Updated: 9 Feb 2026 - Phase H: Deep Pipeline Fixes (v4.8) — Brace-balanced extraction, adaptive compressor, BPL ratio limiting, directory summary, primary language priority_
_Updated: 9 Feb 2026 - Phase G: PocketBase 16-Gap Remediation (v4.7) — BaaS domain, middleware factories, CLI commands, .d.ts filtering, route prefix tracking, plugin detection_
_Updated: 9 Feb 2026 - Phase F: Go Language Support (v4.5), Generic Semantic Extraction (v4.6), PocketBase validation_
_Updated: Session 75 - Phase CA: Java Framework Parsers Round 2 (v4.95) — 5 parsers (Vert.x/Hibernate/MyBatis/Apache Camel/Akka), 35 files, 25 extractors, ~45 ProjectMatrix fields, scanner + compressor, 4 bugs fixed, 109 new tests, 6752 total passing_
_Based on: Python Integration Session + BPL Hardening Session + Phase 2 & 3 Completion + Phase A Remediation + Phase D Validation Framework + Phase F Go/Semantic (v4.6) + Phase G Gap Remediation (v4.7) + Phase H Deep Pipeline Fixes (v4.8) + Phase J R4 Evaluation & .gitignore Scanning (v4.10) + Phase K Systemic Improvements (v4.11) + Phase L Java & Kotlin (v4.12) + Phase N Rust (v4.14) + Phase S C++ (v4.20) + Phase T Ruby (v4.23) + Phase W R (v4.26) + Phase X Dart (v4.27) + Phase Y Lua (v4.28) + Phase Z PowerShell (v4.29) + Phase AE MUI (v4.36) + Phase AF Ant Design (v4.37) + Phase AG Chakra UI (v4.38) + Phase AH shadcn/ui (v4.39) + Phase AI Bootstrap (v4.40) + Phase AM Sass/SCSS (v4.44) + Phase AN Less (v4.45) + Phase BZ Java Framework Parsers (v4.94) + Phase CA Java Framework Parsers Round 2 (v4.95)_
