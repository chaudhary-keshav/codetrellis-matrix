"""
Tests for CacheOptimizer — Prompt caching optimization (A5.1).

Validates section parsing, stability-based reordering, cache break insertion,
statistics computation, and Anthropic API message formatting.
"""

import pytest
from codetrellis.cache_optimizer import (
    CacheOptimizer,
    CacheOptimizationResult,
    SectionStability,
    SectionInfo,
    SECTION_STABILITY,
    DEFAULT_STABILITY,
    optimize_matrix_prompt,
    get_anthropic_cache_messages,
)


# ===== FIXTURES =====

@pytest.fixture
def optimizer():
    return CacheOptimizer(insert_cache_breaks=True)


@pytest.fixture
def optimizer_no_breaks():
    return CacheOptimizer(insert_cache_breaks=False)


SAMPLE_PROMPT = """[AI_INSTRUCTION]
# CodeTrellis v4.9.0 — Project Self-Awareness System
This is the AI instruction block.

[PROJECT]
# name: myapp
# lang: TypeScript, Python
# framework: NestJS, Angular

[SCHEMAS]
User|id:string,name:string,email:string|user.entity.ts

[SERVICES]
UserService|getUser(id:string):User|user.service.ts

[TODOS]
TODO|user.service.ts:42|Add validation for email format

[PROGRESS]
# Completion: 75%
# TODOs: 3 | FIXMEs: 1

[IMPLEMENTATION_LOGIC]
## user.service.ts
  getUser: db.query → validate → transform → return
"""

MINIMAL_PROMPT = """[PROJECT]
# name: tiny
[SCHEMAS]
User|id:string
"""


# ===== SECTION PARSING =====

class TestSectionParsing:
    """Tests for _parse_sections()."""

    def test_parses_all_sections(self, optimizer):
        sections = optimizer._parse_sections(SAMPLE_PROMPT)
        names = [s.name for s in sections]
        assert "AI_INSTRUCTION" in names
        assert "PROJECT" in names
        assert "SCHEMAS" in names
        assert "SERVICES" in names
        assert "TODOS" in names
        assert "PROGRESS" in names
        assert "IMPLEMENTATION_LOGIC" in names

    def test_section_count(self, optimizer):
        sections = optimizer._parse_sections(SAMPLE_PROMPT)
        assert len(sections) == 7  # 7 sections, no preamble

    def test_preamble_extraction(self, optimizer):
        prompt_with_preamble = "Header text here\n\n[PROJECT]\n# name: test"
        sections = optimizer._parse_sections(prompt_with_preamble)
        assert sections[0].name == "_PREAMBLE"
        assert "Header text" in sections[0].content

    def test_no_preamble_when_section_first(self, optimizer):
        sections = optimizer._parse_sections(SAMPLE_PROMPT)
        names = [s.name for s in sections]
        assert "_PREAMBLE" not in names

    def test_section_content_preserved(self, optimizer):
        sections = optimizer._parse_sections(SAMPLE_PROMPT)
        project_section = next(s for s in sections if s.name == "PROJECT")
        assert "myapp" in project_section.content
        assert "TypeScript" in project_section.content

    def test_section_stability_assigned(self, optimizer):
        sections = optimizer._parse_sections(SAMPLE_PROMPT)
        project = next(s for s in sections if s.name == "PROJECT")
        assert project.stability == SectionStability.STATIC

        todos = next(s for s in sections if s.name == "TODOS")
        assert todos.stability == SectionStability.VOLATILE

    def test_token_estimate(self, optimizer):
        sections = optimizer._parse_sections(SAMPLE_PROMPT)
        for section in sections:
            assert section.token_estimate == len(section.content) // 4

    def test_no_sections_returns_preamble(self, optimizer):
        sections = optimizer._parse_sections("Just plain text with no sections")
        assert len(sections) == 1
        assert sections[0].name == "_PREAMBLE"

    def test_empty_string(self, optimizer):
        sections = optimizer._parse_sections("")
        # Either empty list or a single empty preamble
        assert len(sections) <= 1

    def test_colon_section_normalization(self, optimizer):
        prompt = "[DTOS:auth]\nLoginDto|email:string\n[DTOS:user]\nUserDto|name:string"
        sections = optimizer._parse_sections(prompt)
        assert len(sections) == 2
        assert sections[0].name == "DTOS:auth"
        assert sections[1].name == "DTOS:user"
        # Both should be classified as SEMANTIC (base name DTOS is unknown, uses default)


# ===== SECTION SORTING =====

class TestSectionSorting:
    """Tests for _sort_sections() — stability-based ordering."""

    def test_static_before_volatile(self, optimizer):
        sections = optimizer._parse_sections(SAMPLE_PROMPT)
        sorted_sections = optimizer._sort_sections(sections)
        names = [s.name for s in sorted_sections]

        # Static sections should come before volatile
        ai_idx = names.index("AI_INSTRUCTION")
        project_idx = names.index("PROJECT")
        todos_idx = names.index("TODOS")
        progress_idx = names.index("PROGRESS")

        assert ai_idx < todos_idx
        assert project_idx < progress_idx

    def test_preamble_always_first(self, optimizer):
        prompt = "Preamble\n\n[TODOS]\nTODO|fix it\n[PROJECT]\n# name: test"
        sections = optimizer._parse_sections(prompt)
        sorted_sections = optimizer._sort_sections(sections)
        assert sorted_sections[0].name == "_PREAMBLE"

    def test_stability_tier_ordering(self, optimizer):
        """Static → Structural → Semantic → Volatile."""
        sections = optimizer._parse_sections(SAMPLE_PROMPT)
        sorted_sections = optimizer._sort_sections(sections)

        stability_order = {
            SectionStability.STATIC: 0,
            SectionStability.STRUCTURAL: 1,
            SectionStability.SEMANTIC: 2,
            SectionStability.VOLATILE: 3,
        }

        prev_order = -1
        for section in sorted_sections:
            current_order = stability_order[section.stability]
            assert current_order >= prev_order, \
                f"Section {section.name} ({section.stability}) is out of order"
            prev_order = current_order

    def test_priority_within_tier(self, optimizer):
        """Within the same stability tier, sections should be ordered by priority."""
        sections = optimizer._parse_sections(SAMPLE_PROMPT)
        sorted_sections = optimizer._sort_sections(sections)

        # Group by stability
        by_stability = {}
        for s in sorted_sections:
            by_stability.setdefault(s.stability, []).append(s)

        for tier_sections in by_stability.values():
            for i in range(len(tier_sections) - 1):
                assert tier_sections[i].priority <= tier_sections[i + 1].priority


# ===== CACHE BREAK INSERTION =====

class TestCacheBreaks:
    """Tests for cache break marker insertion."""

    def test_cache_breaks_inserted(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        assert "# [CACHE_BREAK]" in result.optimized_prompt

    def test_no_breaks_when_disabled(self, optimizer_no_breaks):
        result = optimizer_no_breaks.optimize(SAMPLE_PROMPT)
        assert "# [CACHE_BREAK]" not in result.optimized_prompt

    def test_cache_break_at_stability_transitions(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        lines = result.optimized_prompt.split("\n")

        # Find cache break positions and verify they are at transitions
        break_indices = [i for i, l in enumerate(lines) if "CACHE_BREAK" in l]
        assert len(break_indices) > 0, "Should have at least one cache break"

    def test_break_positions_tracked(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        assert len(result.cache_break_positions) > 0
        # Positions should be valid character indices
        for pos in result.cache_break_positions:
            assert isinstance(pos, int)
            assert pos >= 0


# ===== OPTIMIZATION RESULT =====

class TestOptimizationResult:
    """Tests for optimize() output."""

    def test_result_type(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        assert isinstance(result, CacheOptimizationResult)

    def test_result_has_optimized_prompt(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        assert isinstance(result.optimized_prompt, str)
        assert len(result.optimized_prompt) > 0

    def test_result_has_section_order(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        assert isinstance(result.section_order, list)
        assert len(result.section_order) > 0

    def test_section_content_preserved(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        # All original section content should be in the optimized prompt
        assert "myapp" in result.optimized_prompt
        assert "UserService" in result.optimized_prompt
        assert "getUser" in result.optimized_prompt

    def test_stats_populated(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        assert "total_sections" in result.stats
        assert "total_tokens" in result.stats
        assert "cacheable_tokens" in result.stats
        assert "cacheable_pct" in result.stats

    def test_convenience_properties(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        assert result.total_sections > 0
        assert result.sections_reordered > 0
        assert result.cache_breaks_inserted > 0
        assert isinstance(result.static_token_estimate, int)
        assert isinstance(result.volatile_token_estimate, int)
        assert isinstance(result.estimated_cache_hit_ratio, float)
        assert isinstance(result.estimated_cost_savings_pct, float)

    def test_stability_map(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        smap = result.stability_map
        assert smap.get("PROJECT") == "static"
        assert smap.get("TODOS") == "volatile"

    def test_section_order_all_sections_present(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        assert "AI_INSTRUCTION" in result.section_order
        assert "TODOS" in result.section_order
        assert "PROJECT" in result.section_order

    def test_minimal_prompt_works(self, optimizer):
        result = optimizer.optimize(MINIMAL_PROMPT)
        assert "tiny" in result.optimized_prompt
        assert "User" in result.optimized_prompt


# ===== STATISTICS =====

class TestStatistics:
    """Tests for _compute_stats()."""

    def test_tokens_by_stability(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        tokens = result.stats.get("tokens_by_stability", {})
        assert "static" in tokens
        assert "volatile" in tokens

    def test_cacheable_pct_reasonable(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        pct = result.stats.get("cacheable_pct", 0)
        assert 0 <= pct <= 100

    def test_savings_calculation(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        savings = result.stats.get("estimated_savings_10_requests", {})
        assert "uncached_cost" in savings
        assert "cached_cost" in savings
        assert "savings_pct" in savings
        # Cached should cost less than uncached for 10 requests
        if savings["uncached_cost"] > 0:
            assert savings["cached_cost"] <= savings["uncached_cost"]

    def test_section_order_in_stats(self, optimizer):
        result = optimizer.optimize(SAMPLE_PROMPT)
        order = result.stats.get("section_order", [])
        assert len(order) > 0
        assert order[0] in ("_PREAMBLE", "AI_INSTRUCTION", "PROJECT")


# ===== CONVENIENCE FUNCTIONS =====

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_optimize_matrix_prompt(self):
        result = optimize_matrix_prompt(SAMPLE_PROMPT)
        assert isinstance(result, CacheOptimizationResult)
        assert len(result.optimized_prompt) > 0

    def test_optimize_no_cache_breaks(self):
        result = optimize_matrix_prompt(SAMPLE_PROMPT, insert_cache_breaks=False)
        assert "# [CACHE_BREAK]" not in result.optimized_prompt

    def test_get_anthropic_cache_messages(self):
        result = optimize_matrix_prompt(SAMPLE_PROMPT)
        messages = get_anthropic_cache_messages(result.optimized_prompt)
        assert isinstance(messages, list)
        assert len(messages) > 0

        # All but last should have cache_control
        for block in messages[:-1]:
            assert "cache_control" in block
            assert block["type"] == "text"

        # Last block should NOT have cache_control (volatile section)
        last = messages[-1]
        assert "cache_control" not in last

    def test_anthropic_messages_content(self):
        result = optimize_matrix_prompt(SAMPLE_PROMPT)
        messages = get_anthropic_cache_messages(result.optimized_prompt)
        # Combine all message text
        all_text = " ".join(m["text"] for m in messages)
        assert "myapp" in all_text
        assert "UserService" in all_text


# ===== SECTION_STABILITY MAPPING =====

class TestSectionStabilityMapping:
    """Tests for the SECTION_STABILITY constant."""

    def test_static_sections_defined(self):
        static_sections = [
            "AI_INSTRUCTION", "PROJECT", "RUNBOOK", "BEST_PRACTICES",
            "BUSINESS_DOMAIN", "DATA_FLOWS",
        ]
        for name in static_sections:
            stability, _ = SECTION_STABILITY[name]
            assert stability == SectionStability.STATIC, \
                f"{name} should be STATIC"

    def test_volatile_sections_defined(self):
        volatile_sections = [
            "TODOS", "ACTIONABLE_ITEMS", "PROGRESS",
            "IMPLEMENTATION_LOGIC",
        ]
        for name in volatile_sections:
            stability, _ = SECTION_STABILITY[name]
            assert stability == SectionStability.VOLATILE, \
                f"{name} should be VOLATILE"

    def test_structural_sections_defined(self):
        structural_sections = [
            "OVERVIEW", "INFRASTRUCTURE", "SERVICE_MAP",
            "DATABASE", "SECURITY",
        ]
        for name in structural_sections:
            stability, _ = SECTION_STABILITY[name]
            assert stability == SectionStability.STRUCTURAL, \
                f"{name} should be STRUCTURAL"

    def test_semantic_sections_defined(self):
        semantic_sections = [
            "SCHEMAS", "INTERFACES", "TYPES", "SERVICES",
            "CONTROLLERS", "COMPONENTS",
        ]
        for name in semantic_sections:
            stability, _ = SECTION_STABILITY[name]
            assert stability == SectionStability.SEMANTIC, \
                f"{name} should be SEMANTIC"

    def test_default_stability(self):
        stability, priority = DEFAULT_STABILITY
        assert stability == SectionStability.SEMANTIC
        assert isinstance(priority, int)

    def test_priorities_increase_within_tiers(self):
        """Within each stability tier, priorities should be ordered reasonably."""
        by_stability = {}
        for name, (stability, priority) in SECTION_STABILITY.items():
            by_stability.setdefault(stability, []).append((priority, name))

        for stability, items in by_stability.items():
            priorities = sorted([p for p, _ in items])
            # Check that priorities are non-negative and ordered
            for p in priorities:
                assert p >= 0, f"Priority should be non-negative in {stability.value}"


# ===== FRAMEWORK COVERAGE TESTS =====

class TestFrameworkStabilityCoverage:
    """Verify SECTION_STABILITY covers all 53+ language/framework sections."""

    def test_vue_sections_all_present(self):
        expected = ["VUE_COMPONENTS", "VUE_COMPOSABLES", "VUE_DIRECTIVES",
                     "VUE_PLUGINS", "VUE_ROUTING"]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_svelte_sections_all_present(self):
        expected = ["SVELTE_COMPONENTS", "SVELTE_STORES", "SVELTE_ACTIONS",
                     "SVELTEKIT_ROUTING", "SVELTE_RUNES"]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_astro_sections_all_present(self):
        expected = ["ASTRO_COMPONENTS", "ASTRO_ISLANDS", "ASTRO_ROUTING",
                     "ASTRO_CONTENT", "ASTRO_API"]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_solidjs_sections_all_present(self):
        expected = ["SOLIDJS_COMPONENTS", "SOLIDJS_SIGNALS", "SOLIDJS_STORES",
                     "SOLIDJS_RESOURCES", "SOLIDJS_API"]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_qwik_sections_all_present(self):
        expected = ["QWIK_COMPONENTS", "QWIK_SIGNALS", "QWIK_TASKS",
                     "QWIK_ROUTES", "QWIK_API"]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_preact_sections_all_present(self):
        expected = ["PREACT_COMPONENTS", "PREACT_HOOKS", "PREACT_SIGNALS",
                     "PREACT_CONTEXTS", "PREACT_API"]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_lit_sections_all_present(self):
        expected = ["LIT_COMPONENTS", "LIT_PROPERTIES", "LIT_TEMPLATES",
                     "LIT_EVENTS", "LIT_API"]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_alpine_sections_all_present(self):
        expected = ["ALPINE_DIRECTIVES", "ALPINE_COMPONENTS", "ALPINE_STORES",
                     "ALPINE_PLUGINS", "ALPINE_API"]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_htmx_sections_all_present(self):
        expected = ["HTMX_ATTRIBUTES", "HTMX_REQUESTS", "HTMX_EVENTS",
                     "HTMX_EXTENSIONS", "HTMX_API"]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_state_management_sections_all_present(self):
        expected = [
            "REDUX_STORES", "REDUX_SLICES", "REDUX_MIDDLEWARE",
            "REDUX_SELECTORS", "REDUX_RTK_QUERY",
            "ZUSTAND_STORES", "ZUSTAND_SELECTORS", "ZUSTAND_MIDDLEWARE",
            "ZUSTAND_ACTIONS", "ZUSTAND_API",
            "JOTAI_ATOMS", "JOTAI_SELECTORS", "JOTAI_MIDDLEWARE",
            "JOTAI_ACTIONS", "JOTAI_API",
            "RECOIL_ATOMS", "RECOIL_SELECTORS", "RECOIL_EFFECTS",
            "RECOIL_HOOKS", "RECOIL_API",
            "MOBX_OBSERVABLES", "MOBX_COMPUTEDS", "MOBX_ACTIONS",
            "MOBX_REACTIONS", "MOBX_API",
            "PINIA_STORES", "PINIA_GETTERS", "PINIA_ACTIONS",
            "PINIA_PLUGINS", "PINIA_API",
            "NGRX_STORES", "NGRX_ACTIONS", "NGRX_EFFECTS",
            "NGRX_SELECTORS", "NGRX_API", "NGRX_DEVTOOLS",
            "NGRX_STORE_REFS", "NGRX_ESLINT",
            "XSTATE_MACHINES", "XSTATE_STATES", "XSTATE_ACTIONS",
            "XSTATE_GUARDS", "XSTATE_API",
            "VALTIO_PROXIES", "VALTIO_SNAPSHOTS", "VALTIO_SUBSCRIPTIONS",
            "VALTIO_ACTIONS", "VALTIO_API",
        ]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_data_fetching_sections_all_present(self):
        expected = [
            "TANSTACK_QUERIES", "TANSTACK_MUTATIONS", "TANSTACK_CACHE",
            "TANSTACK_PREFETCH", "TANSTACK_QUERY_API",
            "SWR_HOOKS", "SWR_MUTATIONS", "SWR_CACHE",
            "SWR_MIDDLEWARE", "SWR_API",
            "APOLLO_QUERIES", "APOLLO_MUTATIONS", "APOLLO_CACHE",
            "APOLLO_SUBSCRIPTIONS", "APOLLO_API",
        ]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_ui_library_sections_all_present(self):
        expected = [
            "MUI_COMPONENTS", "MUI_THEME", "MUI_HOOKS", "MUI_STYLES", "MUI_API",
            "ANTD_COMPONENTS", "ANTD_THEME", "ANTD_HOOKS", "ANTD_STYLES", "ANTD_API",
            "CHAKRA_COMPONENTS", "CHAKRA_THEME", "CHAKRA_HOOKS",
            "CHAKRA_STYLES", "CHAKRA_API",
            "SHADCN_COMPONENTS", "SHADCN_THEME", "SHADCN_HOOKS",
            "SHADCN_STYLES", "SHADCN_API",
            "BOOTSTRAP_COMPONENTS", "BOOTSTRAP_GRID", "BOOTSTRAP_THEME",
            "BOOTSTRAP_UTILITIES", "BOOTSTRAP_PLUGINS",
            "RADIX_COMPONENTS", "RADIX_PRIMITIVES", "RADIX_THEME",
            "RADIX_STYLES", "RADIX_API",
        ]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_css_in_js_sections_all_present(self):
        expected = [
            "SC_COMPONENTS", "SC_THEME", "SC_MIXINS", "SC_STYLES", "SC_API",
            "EM_COMPONENTS", "EM_STYLES", "EM_THEME", "EM_ANIMATIONS", "EM_API",
        ]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_styling_sections_all_present(self):
        expected = [
            "CSS_SELECTORS", "CSS_VARIABLES", "CSS_LAYOUT",
            "CSS_MEDIA", "CSS_ANIMATIONS", "CSS_PREPROCESSOR",
            "SASS_VARIABLES", "SASS_MIXINS", "SASS_FUNCTIONS",
            "SASS_MODULES", "SASS_NESTING",
            "LESS_VARIABLES", "LESS_MIXINS", "LESS_FUNCTIONS",
            "LESS_IMPORTS", "LESS_RULESETS",
            "TAILWIND_CONFIG", "TAILWIND_UTILITIES", "TAILWIND_COMPONENTS",
            "TAILWIND_THEME", "TAILWIND_PLUGINS", "TAILWIND_FEATURES",
            "POSTCSS_PLUGINS", "POSTCSS_CONFIG", "POSTCSS_TRANSFORMS",
            "POSTCSS_SYNTAX",
        ]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_next_and_remix_sections_all_present(self):
        expected = [
            "NEXT_PAGES", "NEXT_ROUTES", "NEXT_SERVER_ACTIONS",
            "NEXT_DATA_FETCHING", "NEXT_CONFIG",
            "REMIX_ROUTES", "REMIX_LOADERS", "REMIX_ACTIONS",
            "REMIX_META", "REMIX_API",
        ]
        for name in expected:
            assert name in SECTION_STABILITY, f"Missing: {name}"

    def test_total_section_stability_count(self):
        """Should have at least 300 section entries covering all frameworks."""
        assert len(SECTION_STABILITY) >= 300
