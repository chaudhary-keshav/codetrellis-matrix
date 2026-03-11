"""
CodeTrellis Cache Optimizer — Prompt Caching Optimization (A5.1)
================================================================

Restructures matrix.prompt output for optimal Anthropic/Google prompt caching.

Strategy:
  - STABLE sections first (rarely change between sessions): PROJECT, OVERVIEW,
    SCHEMAS, TYPES, API, RUNBOOK, BEST_PRACTICES, BUSINESS_DOMAIN
  - VOLATILE sections last (change with every code edit): PROGRESS, TODOS,
    ACTIONABLE_ITEMS, IMPLEMENTATION_LOGIC
  - Insert [CACHE_BREAK] markers at strategic points for cache_control breakpoints

Token Economics (from A3 research):
  Without caching: 94K × $3/MTok = $0.28 per request
  With caching (write): 94K × $3/MTok × 1.25 = $0.35
  With caching (read):  94K × $3/MTok × 0.10 = $0.028
  10-request session: $0.60 (cached) vs $2.82 (uncached) → 79% savings

Version: 1.0.0
Created: 20 February 2026
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class SectionStability(Enum):
    """Classification of matrix section stability for caching."""
    STATIC = "static"          # Never changes unless project config changes
    STRUCTURAL = "structural"  # Changes when files are added/removed
    SEMANTIC = "semantic"      # Changes when code structure changes
    VOLATILE = "volatile"      # Changes with any code edit


@dataclass
class SectionInfo:
    """Metadata about a parsed matrix section."""
    name: str
    content: str
    stability: SectionStability
    priority: int  # Lower = earlier in output (more cacheable)
    token_estimate: int = 0

    @property
    def char_count(self) -> int:
        return len(self.content)


@dataclass
class CacheOptimizationResult:
    """Result of cache optimization."""
    optimized_prompt: str
    section_order: List[str]
    cache_break_positions: List[int]  # Character positions of cache breaks
    stats: Dict[str, any] = field(default_factory=dict)

    @property
    def total_sections(self) -> int:
        return self.stats.get("total_sections", 0)

    @property
    def sections_reordered(self) -> int:
        return self.stats.get("total_sections", 0)

    @property
    def cache_breaks_inserted(self) -> int:
        return len(self.cache_break_positions)

    @property
    def static_token_estimate(self) -> int:
        tokens = self.stats.get("tokens_by_stability", {})
        return tokens.get("static", 0)

    @property
    def volatile_token_estimate(self) -> int:
        tokens = self.stats.get("tokens_by_stability", {})
        return tokens.get("volatile", 0)

    @property
    def estimated_cache_hit_ratio(self) -> float:
        return self.stats.get("cacheable_pct", 0) / 100.0

    @property
    def estimated_cost_savings_pct(self) -> float:
        savings = self.stats.get("estimated_savings_10_requests", {})
        return savings.get("savings_pct", 0) / 100.0

    @property
    def stability_map(self) -> Dict[str, str]:
        """Map section name to its stability classification string."""
        result = {}
        for name in self.section_order:
            base = name.split(":")[0] if ":" in name else name
            stability, _ = SECTION_STABILITY.get(base, DEFAULT_STABILITY)
            result[name] = stability.value
        return result


# Section stability classification — maps section names to their stability level.
# Based on analysis of how frequently each section changes relative to code edits.
SECTION_STABILITY: Dict[str, Tuple[SectionStability, int]] = {
    # === STATIC: Only change when project configuration changes ===
    "AI_INSTRUCTION":       (SectionStability.STATIC, 10),
    "PROJECT":              (SectionStability.STATIC, 20),
    "RUNBOOK":              (SectionStability.STATIC, 30),
    "BEST_PRACTICES":       (SectionStability.STATIC, 40),
    "BUSINESS_DOMAIN":      (SectionStability.STATIC, 50),
    "DATA_FLOWS":           (SectionStability.STATIC, 60),
    "ARCHITECTURAL_DECISIONS": (SectionStability.STATIC, 70),

    # === STRUCTURAL: Change when files/modules are added/removed ===
    "OVERVIEW":             (SectionStability.STRUCTURAL, 100),
    "PROJECT_STRUCTURE":    (SectionStability.STRUCTURAL, 110),
    "PROJECT_PROFILE":      (SectionStability.STRUCTURAL, 120),
    "SUB_PROJECTS":         (SectionStability.STRUCTURAL, 130),
    "SUB_PROJECTS_DETAIL":  (SectionStability.STRUCTURAL, 140),
    "MONOREPO":             (SectionStability.STRUCTURAL, 140),
    "INFRASTRUCTURE":       (SectionStability.STRUCTURAL, 150),
    "SERVICE_MAP":          (SectionStability.STRUCTURAL, 160),
    "DATABASE":             (SectionStability.STRUCTURAL, 170),
    "SECURITY":             (SectionStability.STRUCTURAL, 180),
    "OPENAPI":              (SectionStability.STRUCTURAL, 190),
    "GRAPHQL":              (SectionStability.STRUCTURAL, 200),

    # === SEMANTIC: Change when code structure changes (types, APIs, schemas) ===
    "SCHEMAS":              (SectionStability.SEMANTIC, 300),
    "ENUMS":                (SectionStability.SEMANTIC, 310),
    "INTERFACES":           (SectionStability.SEMANTIC, 320),
    "TYPES":                (SectionStability.SEMANTIC, 330),
    "SERVICES":             (SectionStability.SEMANTIC, 340),
    "CONTROLLERS":          (SectionStability.SEMANTIC, 350),
    "COMPONENTS":           (SectionStability.SEMANTIC, 360),
    "STORES":               (SectionStability.SEMANTIC, 370),
    "ROUTES":               (SectionStability.SEMANTIC, 380),
    "HTTP_API":             (SectionStability.SEMANTIC, 390),
    "WEBSOCKET_EVENTS":     (SectionStability.SEMANTIC, 400),
    "CONTEXT":              (SectionStability.SEMANTIC, 410),

    # Language-specific type/API sections (SEMANTIC)
    "PYTHON_TYPES":         (SectionStability.SEMANTIC, 500),
    "PYTHON_API":           (SectionStability.SEMANTIC, 510),
    "PYTHON_FUNCTIONS":     (SectionStability.SEMANTIC, 520),
    "GO_TYPES":             (SectionStability.SEMANTIC, 530),
    "GO_API":               (SectionStability.SEMANTIC, 540),
    "GO_FUNCTIONS":         (SectionStability.SEMANTIC, 550),
    "JAVA_TYPES":           (SectionStability.SEMANTIC, 560),
    "JAVA_API":             (SectionStability.SEMANTIC, 570),
    "JAVA_FUNCTIONS":       (SectionStability.SEMANTIC, 580),
    "JAVA_MODELS":          (SectionStability.SEMANTIC, 590),
    "KOTLIN_TYPES":         (SectionStability.SEMANTIC, 600),
    "KOTLIN_FUNCTIONS":     (SectionStability.SEMANTIC, 610),
    "KOTLIN_API":           (SectionStability.SEMANTIC, 620),
    "KOTLIN_MODELS":        (SectionStability.SEMANTIC, 630),
    "CSHARP_TYPES":         (SectionStability.SEMANTIC, 640),
    "CSHARP_API":           (SectionStability.SEMANTIC, 650),
    "CSHARP_FUNCTIONS":     (SectionStability.SEMANTIC, 660),
    "CSHARP_MODELS":        (SectionStability.SEMANTIC, 670),
    "RUST_TYPES":           (SectionStability.SEMANTIC, 680),
    "RUST_API":             (SectionStability.SEMANTIC, 690),
    "RUST_FUNCTIONS":       (SectionStability.SEMANTIC, 700),
    "RUST_MODELS":          (SectionStability.SEMANTIC, 710),
    "SWIFT_TYPES":          (SectionStability.SEMANTIC, 720),
    "SWIFT_FUNCTIONS":      (SectionStability.SEMANTIC, 730),
    "SWIFT_API":            (SectionStability.SEMANTIC, 740),
    "SWIFT_MODELS":         (SectionStability.SEMANTIC, 750),
    "RUBY_TYPES":           (SectionStability.SEMANTIC, 760),
    "RUBY_FUNCTIONS":       (SectionStability.SEMANTIC, 770),
    "RUBY_API":             (SectionStability.SEMANTIC, 780),
    "RUBY_MODELS":          (SectionStability.SEMANTIC, 790),
    "PHP_TYPES":            (SectionStability.SEMANTIC, 800),
    "PHP_FUNCTIONS":        (SectionStability.SEMANTIC, 810),
    "PHP_API":              (SectionStability.SEMANTIC, 820),
    "PHP_MODELS":           (SectionStability.SEMANTIC, 830),
    "SCALA_TYPES":          (SectionStability.SEMANTIC, 840),
    "SCALA_FUNCTIONS":      (SectionStability.SEMANTIC, 850),
    "SCALA_API":            (SectionStability.SEMANTIC, 860),
    "SCALA_MODELS":         (SectionStability.SEMANTIC, 870),
    "TS_TYPES":             (SectionStability.SEMANTIC, 880),
    "TS_FUNCTIONS":         (SectionStability.SEMANTIC, 890),
    "TS_API":               (SectionStability.SEMANTIC, 900),
    "TS_MODELS":            (SectionStability.SEMANTIC, 910),
    "JS_TYPES":             (SectionStability.SEMANTIC, 920),
    "JS_FUNCTIONS":         (SectionStability.SEMANTIC, 930),
    "JS_API":               (SectionStability.SEMANTIC, 940),
    "JS_MODELS":            (SectionStability.SEMANTIC, 950),

    # Dependency sections (STRUCTURAL — change when deps change)
    "GO_DEPENDENCIES":      (SectionStability.STRUCTURAL, 1000),
    "JAVA_DEPENDENCIES":    (SectionStability.STRUCTURAL, 1010),
    "RUST_DEPENDENCIES":    (SectionStability.STRUCTURAL, 1020),
    "CSHARP_DEPENDENCIES":  (SectionStability.STRUCTURAL, 1030),
    "SWIFT_DEPENDENCIES":   (SectionStability.STRUCTURAL, 1040),
    "RUBY_DEPENDENCIES":    (SectionStability.STRUCTURAL, 1050),
    "PHP_DEPENDENCIES":     (SectionStability.STRUCTURAL, 1060),
    "SCALA_DEPENDENCIES":   (SectionStability.STRUCTURAL, 1070),
    "TS_DEPENDENCIES":      (SectionStability.STRUCTURAL, 1080),
    "JS_DEPENDENCIES":      (SectionStability.STRUCTURAL, 1090),
    "DART_DEPENDENCIES":    (SectionStability.STRUCTURAL, 1100),
    "R_DEPENDENCIES":       (SectionStability.STRUCTURAL, 1110),
    "LUA_DEPENDENCIES":     (SectionStability.STRUCTURAL, 1120),
    "POWERSHELL_DEPENDENCIES": (SectionStability.STRUCTURAL, 1130),
    "BASH_DEPENDENCIES":    (SectionStability.STRUCTURAL, 1140),
    "C_DEPENDENCIES":       (SectionStability.STRUCTURAL, 1150),
    "CPP_DEPENDENCIES":     (SectionStability.STRUCTURAL, 1160),
    "SQL_DEPENDENCIES":     (SectionStability.STRUCTURAL, 1170),
    "SASS_DEPENDENCIES":    (SectionStability.STRUCTURAL, 1180),
    "LESS_DEPENDENCIES":    (SectionStability.STRUCTURAL, 1190),
    "POSTCSS_DEPENDENCIES": (SectionStability.STRUCTURAL, 1195),

    # === SEMANTIC: Go Framework sections (v5.2) ===
    "GO_GIN":               (SectionStability.SEMANTIC, 1196),
    "GO_ECHO":              (SectionStability.SEMANTIC, 1196),
    "GO_FIBER":             (SectionStability.SEMANTIC, 1196),
    "GO_CHI":               (SectionStability.SEMANTIC, 1196),
    "GO_GRPC":              (SectionStability.SEMANTIC, 1196),
    "GO_GORM":              (SectionStability.SEMANTIC, 1196),
    "GO_SQLX":              (SectionStability.SEMANTIC, 1196),
    "GO_COBRA":             (SectionStability.SEMANTIC, 1196),

    # === SEMANTIC: Rust Framework sections (v5.4) ===
    "ACTIX_WEB":            (SectionStability.SEMANTIC, 1197),
    "AXUM":                 (SectionStability.SEMANTIC, 1197),
    "ROCKET":               (SectionStability.SEMANTIC, 1197),
    "WARP":                 (SectionStability.SEMANTIC, 1197),
    "DIESEL":               (SectionStability.SEMANTIC, 1197),
    "SEAORM":               (SectionStability.SEMANTIC, 1197),
    "TAURI":                (SectionStability.SEMANTIC, 1197),

    # === SEMANTIC: Framework-specific code sections ===

    # React ecosystem
    "REACT_COMPONENTS":     (SectionStability.SEMANTIC, 1200),
    "REACT_HOOKS":          (SectionStability.SEMANTIC, 1201),
    "REACT_CONTEXT":        (SectionStability.SEMANTIC, 1202),
    "REACT_STATE":          (SectionStability.SEMANTIC, 1203),
    "REACT_ROUTING":        (SectionStability.SEMANTIC, 1204),

    # Angular / NestJS
    "NESTJS_MODULES":       (SectionStability.SEMANTIC, 1210),
    "ANGULAR_SERVICES":     (SectionStability.SEMANTIC, 1211),
    "NGRX_STORES":          (SectionStability.SEMANTIC, 1212),
    "NGRX_EFFECTS":         (SectionStability.SEMANTIC, 1213),
    "NGRX_SELECTORS":       (SectionStability.SEMANTIC, 1214),
    "NGRX_ACTIONS":         (SectionStability.SEMANTIC, 1215),
    "NGRX_API":             (SectionStability.SEMANTIC, 1216),
    "NGRX_DEVTOOLS":        (SectionStability.SEMANTIC, 1217),
    "NGRX_ESLINT":          (SectionStability.SEMANTIC, 1218),
    "NGRX_STORE_REFS":      (SectionStability.SEMANTIC, 1219),

    # Vue.js ecosystem
    "VUE_COMPONENTS":       (SectionStability.SEMANTIC, 1220),
    "VUE_COMPOSABLES":      (SectionStability.SEMANTIC, 1221),
    "VUE_DIRECTIVES":       (SectionStability.SEMANTIC, 1222),
    "VUE_PLUGINS":          (SectionStability.SEMANTIC, 1223),
    "VUE_ROUTING":          (SectionStability.SEMANTIC, 1224),
    "PINIA_STORES":         (SectionStability.SEMANTIC, 1225),
    "PINIA_GETTERS":        (SectionStability.SEMANTIC, 1226),
    "PINIA_ACTIONS":        (SectionStability.SEMANTIC, 1227),
    "PINIA_PLUGINS":        (SectionStability.SEMANTIC, 1228),
    "PINIA_API":            (SectionStability.SEMANTIC, 1229),

    # Svelte
    "SVELTE_COMPONENTS":    (SectionStability.SEMANTIC, 1230),
    "SVELTE_STORES":        (SectionStability.SEMANTIC, 1231),
    "SVELTE_ACTIONS":       (SectionStability.SEMANTIC, 1232),
    "SVELTE_RUNES":         (SectionStability.SEMANTIC, 1233),
    "SVELTEKIT_ROUTING":    (SectionStability.SEMANTIC, 1234),

    # Next.js
    "NEXT_PAGES":           (SectionStability.SEMANTIC, 1240),
    "NEXT_ROUTES":          (SectionStability.SEMANTIC, 1241),
    "NEXT_DATA_FETCHING":   (SectionStability.SEMANTIC, 1242),
    "NEXT_SERVER_ACTIONS":  (SectionStability.SEMANTIC, 1243),
    "NEXT_CONFIG":          (SectionStability.STRUCTURAL, 1244),

    # Remix
    "REMIX_ROUTES":         (SectionStability.SEMANTIC, 1250),
    "REMIX_LOADERS":        (SectionStability.SEMANTIC, 1251),
    "REMIX_ACTIONS":        (SectionStability.SEMANTIC, 1252),
    "REMIX_META":           (SectionStability.SEMANTIC, 1253),
    "REMIX_API":            (SectionStability.SEMANTIC, 1254),

    # Astro
    "ASTRO_COMPONENTS":     (SectionStability.SEMANTIC, 1260),
    "ASTRO_CONTENT":        (SectionStability.SEMANTIC, 1261),
    "ASTRO_ISLANDS":        (SectionStability.SEMANTIC, 1262),
    "ASTRO_ROUTING":        (SectionStability.SEMANTIC, 1263),
    "ASTRO_API":            (SectionStability.SEMANTIC, 1264),

    # Solid.js
    "SOLIDJS_COMPONENTS":   (SectionStability.SEMANTIC, 1270),
    "SOLIDJS_SIGNALS":      (SectionStability.SEMANTIC, 1271),
    "SOLIDJS_STORES":       (SectionStability.SEMANTIC, 1272),
    "SOLIDJS_RESOURCES":    (SectionStability.SEMANTIC, 1273),
    "SOLIDJS_API":          (SectionStability.SEMANTIC, 1274),

    # Qwik
    "QWIK_COMPONENTS":      (SectionStability.SEMANTIC, 1280),
    "QWIK_SIGNALS":         (SectionStability.SEMANTIC, 1281),
    "QWIK_ROUTES":          (SectionStability.SEMANTIC, 1282),
    "QWIK_TASKS":           (SectionStability.SEMANTIC, 1283),
    "QWIK_API":             (SectionStability.SEMANTIC, 1284),

    # Preact
    "PREACT_COMPONENTS":    (SectionStability.SEMANTIC, 1290),
    "PREACT_HOOKS":         (SectionStability.SEMANTIC, 1291),
    "PREACT_SIGNALS":       (SectionStability.SEMANTIC, 1292),
    "PREACT_CONTEXTS":      (SectionStability.SEMANTIC, 1293),
    "PREACT_API":           (SectionStability.SEMANTIC, 1294),

    # Lit / Web Components
    "LIT_COMPONENTS":       (SectionStability.SEMANTIC, 1300),
    "LIT_PROPERTIES":       (SectionStability.SEMANTIC, 1301),
    "LIT_EVENTS":           (SectionStability.SEMANTIC, 1302),
    "LIT_TEMPLATES":        (SectionStability.SEMANTIC, 1303),
    "LIT_API":              (SectionStability.SEMANTIC, 1304),

    # Alpine.js
    "ALPINE_DIRECTIVES":    (SectionStability.SEMANTIC, 1310),
    "ALPINE_COMPONENTS":    (SectionStability.SEMANTIC, 1311),
    "ALPINE_STORES":        (SectionStability.SEMANTIC, 1312),
    "ALPINE_PLUGINS":       (SectionStability.SEMANTIC, 1313),
    "ALPINE_API":           (SectionStability.SEMANTIC, 1314),

    # HTMX
    "HTMX_ATTRIBUTES":     (SectionStability.SEMANTIC, 1320),
    "HTMX_REQUESTS":       (SectionStability.SEMANTIC, 1321),
    "HTMX_EVENTS":         (SectionStability.SEMANTIC, 1322),
    "HTMX_EXTENSIONS":     (SectionStability.SEMANTIC, 1323),
    "HTMX_API":            (SectionStability.SEMANTIC, 1324),

    # Stimulus / Hotwire
    "STIMULUS_CONTROLLERS": (SectionStability.SEMANTIC, 1325),
    "STIMULUS_TARGETS":     (SectionStability.SEMANTIC, 1326),
    "STIMULUS_ACTIONS":     (SectionStability.SEMANTIC, 1327),
    "STIMULUS_VALUES":      (SectionStability.SEMANTIC, 1328),
    "STIMULUS_API":         (SectionStability.SEMANTIC, 1329),

    # Storybook
    "STORYBOOK_STORIES":    (SectionStability.SEMANTIC, 1500),
    "STORYBOOK_COMPONENTS": (SectionStability.SEMANTIC, 1501),
    "STORYBOOK_ADDONS":     (SectionStability.SEMANTIC, 1502),
    "STORYBOOK_CONFIG":     (SectionStability.STRUCTURAL, 1503),
    "STORYBOOK_API":        (SectionStability.SEMANTIC, 1504),

    # State management — Redux/RTK
    "REDUX_STORES":         (SectionStability.SEMANTIC, 1330),
    "REDUX_SLICES":         (SectionStability.SEMANTIC, 1331),
    "REDUX_SELECTORS":      (SectionStability.SEMANTIC, 1332),
    "REDUX_MIDDLEWARE":     (SectionStability.SEMANTIC, 1333),
    "REDUX_RTK_QUERY":      (SectionStability.SEMANTIC, 1334),

    # State management — Zustand
    "ZUSTAND_STORES":       (SectionStability.SEMANTIC, 1340),
    "ZUSTAND_SELECTORS":    (SectionStability.SEMANTIC, 1341),
    "ZUSTAND_MIDDLEWARE":   (SectionStability.SEMANTIC, 1342),
    "ZUSTAND_ACTIONS":      (SectionStability.SEMANTIC, 1343),
    "ZUSTAND_API":          (SectionStability.SEMANTIC, 1344),

    # State management — Jotai
    "JOTAI_ATOMS":          (SectionStability.SEMANTIC, 1350),
    "JOTAI_SELECTORS":      (SectionStability.SEMANTIC, 1351),
    "JOTAI_MIDDLEWARE":     (SectionStability.SEMANTIC, 1352),
    "JOTAI_ACTIONS":        (SectionStability.SEMANTIC, 1353),
    "JOTAI_API":            (SectionStability.SEMANTIC, 1354),

    # State management — Recoil
    "RECOIL_ATOMS":         (SectionStability.SEMANTIC, 1360),
    "RECOIL_SELECTORS":     (SectionStability.SEMANTIC, 1361),
    "RECOIL_HOOKS":         (SectionStability.SEMANTIC, 1362),
    "RECOIL_EFFECTS":       (SectionStability.SEMANTIC, 1363),
    "RECOIL_API":           (SectionStability.SEMANTIC, 1364),

    # State management — MobX
    "MOBX_OBSERVABLES":     (SectionStability.SEMANTIC, 1370),
    "MOBX_COMPUTEDS":       (SectionStability.SEMANTIC, 1371),
    "MOBX_ACTIONS":         (SectionStability.SEMANTIC, 1372),
    "MOBX_REACTIONS":       (SectionStability.SEMANTIC, 1373),
    "MOBX_API":             (SectionStability.SEMANTIC, 1374),

    # State management — XState
    "XSTATE_MACHINES":      (SectionStability.SEMANTIC, 1380),
    "XSTATE_STATES":        (SectionStability.SEMANTIC, 1381),
    "XSTATE_ACTIONS":       (SectionStability.SEMANTIC, 1382),
    "XSTATE_GUARDS":        (SectionStability.SEMANTIC, 1383),
    "XSTATE_API":           (SectionStability.SEMANTIC, 1384),

    # State management — Valtio
    "VALTIO_PROXIES":       (SectionStability.SEMANTIC, 1390),
    "VALTIO_SNAPSHOTS":     (SectionStability.SEMANTIC, 1391),
    "VALTIO_SUBSCRIPTIONS": (SectionStability.SEMANTIC, 1392),
    "VALTIO_ACTIONS":       (SectionStability.SEMANTIC, 1393),
    "VALTIO_API":           (SectionStability.SEMANTIC, 1394),

    # Data fetching — TanStack Query
    "TANSTACK_QUERIES":     (SectionStability.SEMANTIC, 1400),
    "TANSTACK_MUTATIONS":   (SectionStability.SEMANTIC, 1401),
    "TANSTACK_CACHE":       (SectionStability.SEMANTIC, 1402),
    "TANSTACK_PREFETCH":    (SectionStability.SEMANTIC, 1403),
    "TANSTACK_QUERY_API":   (SectionStability.SEMANTIC, 1404),

    # Data fetching — SWR
    "SWR_HOOKS":            (SectionStability.SEMANTIC, 1410),
    "SWR_CACHE":            (SectionStability.SEMANTIC, 1411),
    "SWR_MUTATIONS":        (SectionStability.SEMANTIC, 1412),
    "SWR_MIDDLEWARE":       (SectionStability.SEMANTIC, 1413),
    "SWR_API":              (SectionStability.SEMANTIC, 1414),

    # Data fetching — Apollo
    "APOLLO_QUERIES":       (SectionStability.SEMANTIC, 1420),
    "APOLLO_MUTATIONS":     (SectionStability.SEMANTIC, 1421),
    "APOLLO_CACHE":         (SectionStability.SEMANTIC, 1422),
    "APOLLO_SUBSCRIPTIONS": (SectionStability.SEMANTIC, 1423),
    "APOLLO_API":           (SectionStability.SEMANTIC, 1424),

    # CSS-in-JS — Styled Components
    "SC_COMPONENTS":        (SectionStability.SEMANTIC, 1430),
    "SC_STYLES":            (SectionStability.SEMANTIC, 1431),
    "SC_MIXINS":            (SectionStability.SEMANTIC, 1432),
    "SC_THEME":             (SectionStability.STRUCTURAL, 1433),
    "SC_API":               (SectionStability.SEMANTIC, 1434),

    # CSS-in-JS — Emotion
    "EM_COMPONENTS":        (SectionStability.SEMANTIC, 1440),
    "EM_STYLES":            (SectionStability.SEMANTIC, 1441),
    "EM_ANIMATIONS":        (SectionStability.SEMANTIC, 1442),
    "EM_THEME":             (SectionStability.STRUCTURAL, 1443),
    "EM_API":               (SectionStability.SEMANTIC, 1444),

    # UI Libraries — Material UI (MUI)
    "MUI_COMPONENTS":       (SectionStability.SEMANTIC, 1450),
    "MUI_THEME":            (SectionStability.STRUCTURAL, 1451),
    "MUI_STYLES":           (SectionStability.SEMANTIC, 1452),
    "MUI_HOOKS":            (SectionStability.SEMANTIC, 1453),
    "MUI_API":              (SectionStability.SEMANTIC, 1454),

    # UI Libraries — Ant Design
    "ANTD_COMPONENTS":      (SectionStability.SEMANTIC, 1460),
    "ANTD_THEME":           (SectionStability.STRUCTURAL, 1461),
    "ANTD_STYLES":          (SectionStability.SEMANTIC, 1462),
    "ANTD_HOOKS":           (SectionStability.SEMANTIC, 1463),
    "ANTD_API":             (SectionStability.SEMANTIC, 1464),

    # UI Libraries — Chakra UI
    "CHAKRA_COMPONENTS":    (SectionStability.SEMANTIC, 1470),
    "CHAKRA_THEME":         (SectionStability.STRUCTURAL, 1471),
    "CHAKRA_STYLES":        (SectionStability.SEMANTIC, 1472),
    "CHAKRA_HOOKS":         (SectionStability.SEMANTIC, 1473),
    "CHAKRA_API":           (SectionStability.SEMANTIC, 1474),

    # UI Libraries — shadcn/ui
    "SHADCN_COMPONENTS":    (SectionStability.SEMANTIC, 1480),
    "SHADCN_THEME":         (SectionStability.STRUCTURAL, 1481),
    "SHADCN_STYLES":        (SectionStability.SEMANTIC, 1482),
    "SHADCN_HOOKS":         (SectionStability.SEMANTIC, 1483),
    "SHADCN_API":           (SectionStability.SEMANTIC, 1484),

    # UI Libraries — Bootstrap
    "BOOTSTRAP_COMPONENTS": (SectionStability.SEMANTIC, 1490),
    "BOOTSTRAP_GRID":       (SectionStability.SEMANTIC, 1491),
    "BOOTSTRAP_UTILITIES":  (SectionStability.SEMANTIC, 1492),
    "BOOTSTRAP_THEME":      (SectionStability.STRUCTURAL, 1493),
    "BOOTSTRAP_PLUGINS":    (SectionStability.SEMANTIC, 1494),

    # UI Libraries — Radix
    "RADIX_COMPONENTS":     (SectionStability.SEMANTIC, 1500),
    "RADIX_PRIMITIVES":     (SectionStability.SEMANTIC, 1501),
    "RADIX_STYLES":         (SectionStability.SEMANTIC, 1502),
    "RADIX_THEME":          (SectionStability.STRUCTURAL, 1503),
    "RADIX_API":            (SectionStability.SEMANTIC, 1504),

    # CSS — Tailwind
    "TAILWIND_UTILITIES":   (SectionStability.SEMANTIC, 1510),
    "TAILWIND_COMPONENTS":  (SectionStability.SEMANTIC, 1511),
    "TAILWIND_CONFIG":      (SectionStability.STRUCTURAL, 1512),
    "TAILWIND_THEME":       (SectionStability.STRUCTURAL, 1513),
    "TAILWIND_PLUGINS":     (SectionStability.STRUCTURAL, 1514),
    "TAILWIND_FEATURES":    (SectionStability.SEMANTIC, 1515),

    # CSS preprocessors — Sass/SCSS
    "SASS_VARIABLES":       (SectionStability.SEMANTIC, 1520),
    "SASS_MIXINS":          (SectionStability.SEMANTIC, 1521),
    "SASS_FUNCTIONS":       (SectionStability.SEMANTIC, 1522),
    "SASS_MODULES":         (SectionStability.SEMANTIC, 1523),
    "SASS_NESTING":         (SectionStability.SEMANTIC, 1524),

    # CSS preprocessors — Less
    "LESS_VARIABLES":       (SectionStability.SEMANTIC, 1530),
    "LESS_MIXINS":          (SectionStability.SEMANTIC, 1531),
    "LESS_FUNCTIONS":       (SectionStability.SEMANTIC, 1532),
    "LESS_IMPORTS":         (SectionStability.SEMANTIC, 1533),
    "LESS_RULESETS":        (SectionStability.SEMANTIC, 1534),

    # PostCSS
    "POSTCSS_PLUGINS":      (SectionStability.STRUCTURAL, 1540),
    "POSTCSS_CONFIG":       (SectionStability.STRUCTURAL, 1541),
    "POSTCSS_TRANSFORMS":   (SectionStability.SEMANTIC, 1542),
    "POSTCSS_SYNTAX":       (SectionStability.SEMANTIC, 1543),

    # CSS core
    "CSS_SELECTORS":        (SectionStability.SEMANTIC, 1550),
    "CSS_VARIABLES":        (SectionStability.SEMANTIC, 1551),
    "CSS_LAYOUT":           (SectionStability.SEMANTIC, 1552),
    "CSS_MEDIA":            (SectionStability.SEMANTIC, 1553),
    "CSS_ANIMATIONS":       (SectionStability.SEMANTIC, 1554),
    "CSS_PREPROCESSOR":     (SectionStability.SEMANTIC, 1555),

    # HTML
    "HTML_STRUCTURE":       (SectionStability.SEMANTIC, 1560),
    "HTML_FORMS":           (SectionStability.SEMANTIC, 1561),
    "HTML_META":            (SectionStability.STRUCTURAL, 1562),
    "HTML_ACCESSIBILITY":   (SectionStability.SEMANTIC, 1563),
    "HTML_ASSETS":          (SectionStability.SEMANTIC, 1564),
    "HTML_COMPONENTS":      (SectionStability.SEMANTIC, 1565),
    "HTML_TEMPLATES":       (SectionStability.SEMANTIC, 1566),

    # SQL
    "SQL_TABLES":           (SectionStability.STRUCTURAL, 1570),
    "SQL_VIEWS":            (SectionStability.STRUCTURAL, 1571),
    "SQL_FUNCTIONS":        (SectionStability.SEMANTIC, 1572),
    "SQL_INDEXES":          (SectionStability.STRUCTURAL, 1573),
    "SQL_SECURITY":         (SectionStability.STRUCTURAL, 1574),
    "SQL_MIGRATIONS":       (SectionStability.VOLATILE, 1575),

    # Language-specific types/API/functions/models not yet listed
    "C_TYPES":              (SectionStability.SEMANTIC, 960),
    "C_FUNCTIONS":          (SectionStability.SEMANTIC, 961),
    "C_API":                (SectionStability.SEMANTIC, 962),
    "C_MODELS":             (SectionStability.SEMANTIC, 963),
    "CPP_TYPES":            (SectionStability.SEMANTIC, 970),
    "CPP_FUNCTIONS":        (SectionStability.SEMANTIC, 971),
    "CPP_API":              (SectionStability.SEMANTIC, 972),
    "CPP_MODELS":           (SectionStability.SEMANTIC, 973),
    "DART_TYPES":           (SectionStability.SEMANTIC, 980),
    "DART_FUNCTIONS":       (SectionStability.SEMANTIC, 981),
    "DART_API":             (SectionStability.SEMANTIC, 982),
    "DART_MODELS":          (SectionStability.SEMANTIC, 983),
    "LUA_TYPES":            (SectionStability.SEMANTIC, 990),
    "LUA_FUNCTIONS":        (SectionStability.SEMANTIC, 991),
    "LUA_API":              (SectionStability.SEMANTIC, 992),
    "LUA_MODELS":           (SectionStability.SEMANTIC, 993),
    "POWERSHELL_TYPES":     (SectionStability.SEMANTIC, 994),
    "POWERSHELL_FUNCTIONS": (SectionStability.SEMANTIC, 995),
    "POWERSHELL_API":       (SectionStability.SEMANTIC, 996),
    "POWERSHELL_MODELS":    (SectionStability.SEMANTIC, 997),
    "R_TYPES":              (SectionStability.SEMANTIC, 998),
    "R_FUNCTIONS":          (SectionStability.SEMANTIC, 999),
    "R_API":                (SectionStability.SEMANTIC, 1000),
    "R_MODELS":             (SectionStability.SEMANTIC, 1001),

    # Python extra sections
    "PYTHON_DATA":          (SectionStability.SEMANTIC, 525),
    "PYTHON_ML":            (SectionStability.SEMANTIC, 526),
    "PYTHON_INFRA":         (SectionStability.SEMANTIC, 527),

    # Kotlin advanced sections
    "KOTLIN_ADVANCED":      (SectionStability.SEMANTIC, 635),
    "KOTLIN_DI":            (SectionStability.SEMANTIC, 636),
    "KOTLIN_MULTIPLATFORM": (SectionStability.SEMANTIC, 637),
    "KOTLIN_REPOSITORIES":  (SectionStability.SEMANTIC, 638),
    "KOTLIN_SERIALIZATION": (SectionStability.SEMANTIC, 639),

    # Bash extra sections
    "BASH_FUNCTIONS":       (SectionStability.SEMANTIC, 1141),
    "BASH_VARIABLES":       (SectionStability.SEMANTIC, 1142),
    "BASH_COMMANDS":        (SectionStability.SEMANTIC, 1143),
    "BASH_API":             (SectionStability.SEMANTIC, 1144),

    # Semantic/generic sections
    "HOOKS":                (SectionStability.SEMANTIC, 1600),
    "MIDDLEWARE":           (SectionStability.SEMANTIC, 1610),
    "ROUTES_SEMANTIC":      (SectionStability.SEMANTIC, 1620),
    "LIFECYCLE":            (SectionStability.SEMANTIC, 1630),
    "CLI_COMMANDS":         (SectionStability.SEMANTIC, 1640),

    # === VOLATILE: Change with any code edit ===
    "ERROR_HANDLING":       (SectionStability.VOLATILE, 2000),
    "TODOS":                (SectionStability.VOLATILE, 2010),
    "ACTIONABLE_ITEMS":     (SectionStability.VOLATILE, 2020),
    "PROGRESS":             (SectionStability.VOLATILE, 2030),
    "PROGRESS_DETAIL":      (SectionStability.VOLATILE, 2040),
    "IMPLEMENTATION_LOGIC": (SectionStability.VOLATILE, 2050),
    "CONFIG_VARIABLES":     (SectionStability.VOLATILE, 2060),
    "ENV_GAPS":             (SectionStability.VOLATILE, 2070),
    "GENERIC_LANGUAGES":    (SectionStability.VOLATILE, 2080),
}

# Default stability for unknown sections
DEFAULT_STABILITY = (SectionStability.SEMANTIC, 1400)


class CacheOptimizer:
    """
    Optimizes matrix.prompt output for Anthropic/Google prompt caching.

    Reorders sections by stability (stable first, volatile last) and inserts
    cache_control breakpoint markers at strategic positions.

    Usage:
        optimizer = CacheOptimizer()
        result = optimizer.optimize(existing_prompt)
        optimized_text = result.optimized_prompt

    Cache Break Strategy:
        Break 1: After all STATIC sections (~5-10% of tokens, almost never changes)
        Break 2: After STRUCTURAL sections (~15-20%, changes when project structure changes)
        Break 3: After SEMANTIC sections (~60-70%, changes when code structure changes)
        No break before VOLATILE sections — these are always re-read
    """

    # Marker inserted in the optimized prompt to indicate cache break points.
    # AI providers can use these to set cache_control breakpoints.
    CACHE_BREAK_MARKER = "\n# [CACHE_BREAK]\n"

    def __init__(self, insert_cache_breaks: bool = True) -> None:
        self._insert_cache_breaks = insert_cache_breaks

    def optimize(self, raw_prompt: str) -> CacheOptimizationResult:
        """
        Optimize a matrix.prompt for caching.

        Args:
            raw_prompt: The original matrix.prompt content

        Returns:
            CacheOptimizationResult with optimized content and metadata
        """
        sections = self._parse_sections(raw_prompt)
        sorted_sections = self._sort_sections(sections)
        optimized, cache_breaks = self._assemble(sorted_sections)
        stats = self._compute_stats(sections, sorted_sections, raw_prompt, optimized)

        return CacheOptimizationResult(
            optimized_prompt=optimized,
            section_order=[s.name for s in sorted_sections],
            cache_break_positions=cache_breaks,
            stats=stats,
        )

    def _parse_sections(self, raw_prompt: str) -> List[SectionInfo]:
        """
        Parse a matrix.prompt into individual sections.

        Each section starts with [SECTION_NAME] and ends before the next [SECTION_NAME]
        or end of string. Content before the first [SECTION_NAME] is treated as a
        preamble (header) section.
        """
        sections: List[SectionInfo] = []

        # Split by section headers [SECTION_NAME...]
        # Pattern matches [WORD] or [WORD:SUBWORD] at start of line
        pattern = re.compile(r'^(\[([A-Z][A-Z0-9_]*(?::[^\]]+)?)\])', re.MULTILINE)
        matches = list(pattern.finditer(raw_prompt))

        if not matches:
            # No sections found — return the whole thing as a preamble
            sections.append(SectionInfo(
                name="_PREAMBLE",
                content=raw_prompt,
                stability=SectionStability.STATIC,
                priority=0,
                token_estimate=len(raw_prompt) // 4,
            ))
            return sections

        # Extract preamble (content before first section)
        preamble = raw_prompt[:matches[0].start()].strip()
        if preamble:
            sections.append(SectionInfo(
                name="_PREAMBLE",
                content=preamble,
                stability=SectionStability.STATIC,
                priority=0,
                token_estimate=len(preamble) // 4,
            ))

        # Extract each section
        for i, match in enumerate(matches):
            section_name = match.group(2)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_prompt)
            content = raw_prompt[start:end].rstrip()

            # Determine stability and priority
            # For sections like [DTOS:service_name], normalize to base name
            base_name = section_name.split(":")[0] if ":" in section_name else section_name
            stability, priority = SECTION_STABILITY.get(base_name, DEFAULT_STABILITY)

            sections.append(SectionInfo(
                name=section_name,
                content=content,
                stability=stability,
                priority=priority,
                token_estimate=len(content) // 4,
            ))

        return sections

    def _sort_sections(self, sections: List[SectionInfo]) -> List[SectionInfo]:
        """
        Sort sections by stability tier, then by priority within each tier.

        Order:
          1. _PREAMBLE (always first)
          2. STATIC sections (sorted by priority)
          3. [CACHE_BREAK]
          4. STRUCTURAL sections (sorted by priority)
          5. [CACHE_BREAK]
          6. SEMANTIC sections (sorted by priority)
          7. [CACHE_BREAK]
          8. VOLATILE sections (sorted by priority)
        """
        # Separate preamble from the rest
        preamble = [s for s in sections if s.name == "_PREAMBLE"]
        non_preamble = [s for s in sections if s.name != "_PREAMBLE"]

        # Sort by (stability order, priority)
        stability_order = {
            SectionStability.STATIC: 0,
            SectionStability.STRUCTURAL: 1,
            SectionStability.SEMANTIC: 2,
            SectionStability.VOLATILE: 3,
        }

        sorted_sections = sorted(
            non_preamble,
            key=lambda s: (stability_order.get(s.stability, 2), s.priority)
        )

        return preamble + sorted_sections

    def _assemble(self, sorted_sections: List[SectionInfo]) -> Tuple[str, List[int]]:
        """
        Assemble sorted sections into final optimized prompt with cache breaks.

        Returns:
            Tuple of (assembled prompt string, list of cache break positions)
        """
        parts: List[str] = []
        cache_breaks: List[int] = []
        current_pos = 0
        last_stability: Optional[SectionStability] = None

        for section in sorted_sections:
            # Insert cache break when transitioning stability tiers
            if (self._insert_cache_breaks
                    and last_stability is not None
                    and section.stability != last_stability
                    and section.name != "_PREAMBLE"):

                # Only insert break at STATIC→STRUCTURAL and STRUCTURAL→SEMANTIC transitions
                should_break = (
                    (last_stability == SectionStability.STATIC
                     and section.stability != SectionStability.STATIC)
                    or
                    (last_stability == SectionStability.STRUCTURAL
                     and section.stability not in (SectionStability.STATIC, SectionStability.STRUCTURAL))
                    or
                    (last_stability == SectionStability.SEMANTIC
                     and section.stability == SectionStability.VOLATILE)
                )

                if should_break:
                    cache_break_text = self.CACHE_BREAK_MARKER
                    parts.append(cache_break_text)
                    cache_breaks.append(current_pos)
                    current_pos += len(cache_break_text)

            parts.append(section.content)
            current_pos += len(section.content)

            # Add spacing between sections
            parts.append("\n\n")
            current_pos += 2

            last_stability = section.stability

        result = "\n".join(parts).rstrip() if not parts else "".join(parts).rstrip()
        return result, cache_breaks

    def _compute_stats(
        self,
        original_sections: List[SectionInfo],
        sorted_sections: List[SectionInfo],
        original: str,
        optimized: str,
    ) -> Dict[str, any]:
        """Compute optimization statistics."""
        stability_counts: Dict[str, int] = {}
        stability_tokens: Dict[str, int] = {}

        for section in sorted_sections:
            tier_name = section.stability.value
            stability_counts[tier_name] = stability_counts.get(tier_name, 0) + 1
            stability_tokens[tier_name] = stability_tokens.get(tier_name, 0) + section.token_estimate

        total_tokens = len(optimized) // 4
        static_tokens = stability_tokens.get("static", 0)
        structural_tokens = stability_tokens.get("structural", 0)
        cacheable_tokens = static_tokens + structural_tokens

        # Calculate savings for a 10-request session
        # Anthropic pricing: $3/MTok input, cache write 1.25x, cache read 0.10x
        cost_per_mtok = 3.0 / 1_000_000
        uncached_cost_10 = total_tokens * cost_per_mtok * 10
        cached_cost_10 = (
            total_tokens * cost_per_mtok * 1.25  # First request (cache write)
            + cacheable_tokens * cost_per_mtok * 0.10 * 9  # Cached portion (9 reads)
            + (total_tokens - cacheable_tokens) * cost_per_mtok * 9  # Non-cached portion
        )
        savings_pct = (1 - cached_cost_10 / uncached_cost_10) * 100 if uncached_cost_10 > 0 else 0

        return {
            "total_sections": len(sorted_sections),
            "total_tokens": total_tokens,
            "sections_by_stability": stability_counts,
            "tokens_by_stability": stability_tokens,
            "cacheable_tokens": cacheable_tokens,
            "cacheable_pct": round(cacheable_tokens / total_tokens * 100, 1) if total_tokens > 0 else 0,
            "estimated_savings_10_requests": {
                "uncached_cost": round(uncached_cost_10, 4),
                "cached_cost": round(cached_cost_10, 4),
                "savings_pct": round(savings_pct, 1),
            },
            "original_char_count": len(original),
            "optimized_char_count": len(optimized),
            "section_order": [s.name for s in sorted_sections],
        }


def optimize_matrix_prompt(raw_prompt: str, insert_cache_breaks: bool = True) -> CacheOptimizationResult:
    """
    Convenience function to optimize a matrix.prompt for caching.

    Args:
        raw_prompt: The original matrix.prompt content
        insert_cache_breaks: Whether to insert [CACHE_BREAK] markers

    Returns:
        CacheOptimizationResult with optimized content and statistics
    """
    optimizer = CacheOptimizer(insert_cache_breaks=insert_cache_breaks)
    return optimizer.optimize(raw_prompt)


def get_anthropic_cache_messages(optimized_prompt: str) -> List[Dict[str, any]]:
    """
    Convert an optimized matrix.prompt into Anthropic API messages
    with cache_control breakpoints.

    Each [CACHE_BREAK] marker is converted into a separate message part
    with cache_control set, enabling Anthropic's prompt caching.

    Args:
        optimized_prompt: Cache-optimized matrix prompt (output of optimize())

    Returns:
        List of message content blocks for Anthropic's Messages API

    Example:
        result = optimize_matrix_prompt(raw)
        messages = get_anthropic_cache_messages(result.optimized_prompt)
        # Use in Anthropic API: {"role": "user", "content": messages}
    """
    parts = optimized_prompt.split("# [CACHE_BREAK]")
    content_blocks: List[Dict[str, any]] = []

    for i, part in enumerate(parts):
        text = part.strip()
        if not text:
            continue

        block: Dict[str, any] = {
            "type": "text",
            "text": text,
        }

        # Add cache_control to all parts except the last (volatile) section
        if i < len(parts) - 1:
            block["cache_control"] = {"type": "ephemeral"}

        content_blocks.append(block)

    return content_blocks
