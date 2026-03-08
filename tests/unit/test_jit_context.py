"""
Tests for JITContextProvider — JIT context discovery (A5.3).

Validates file extension mapping, path pattern matching, relevance scoring,
token budget enforcement, and context assembly.
"""

import pytest
import re
from codetrellis.jit_context import (
    JITContextProvider,
    JITContextResult,
    EXTENSION_TO_SECTIONS,
    PATH_PATTERN_SECTIONS,
    UNIVERSAL_SECTIONS,
)


# ===== FIXTURES =====

def _parse_sections(raw: str):
    """Parse raw matrix prompt into {name: content} dict."""
    sections = {}
    current = None
    current_lines = []
    for line in raw.split("\n"):
        m = re.match(r'^\[([A-Z][A-Z0-9_]*)\]', line)
        if m:
            if current:
                sections[current] = "\n".join(current_lines)
            current = m.group(1)
            current_lines = [line]
        elif current:
            current_lines.append(line)
    if current:
        sections[current] = "\n".join(current_lines)
    return sections


SAMPLE_MATRIX_RAW = """[AI_INSTRUCTION]
# CodeTrellis v4.9.0

[PROJECT]
# name: testapp
# lang: Python, TypeScript
# framework: FastAPI, React

[RUNBOOK]
# How to develop on testapp
1. Install deps: pip install -r requirements.txt
2. Run server: uvicorn main:app

[BEST_PRACTICES]
# Python: Use type hints everywhere
# React: Prefer functional components

[SCHEMAS]
User|id:int,name:str,email:str|models/user.py
Post|id:int,title:str|models/post.py

[SERVICES]
UserService|getUser(id:int):User|services/user_service.py

[COMPONENTS]
UserList|props:{users:User[]}|components/UserList.tsx
PostCard|props:{post:Post}|components/PostCard.tsx

[TYPES]
UserRole|admin,editor,viewer|types/enums.ts

[INTERFACES]
IUserService|getUser(id:int):User|interfaces/user.ts

[CONTROLLERS]
UserController|GET /users,POST /users|controllers/user_controller.py

[STORES]
useUserStore|state:{users,loading},actions:{fetchUsers}|stores/userStore.ts

[ROUTES]
/users|UserList|pages/users.tsx
/posts|PostList|pages/posts.tsx

[PYTHON_TYPES]
UserModel|BaseModel|id:int,name:str|models.py

[PYTHON_FUNCTIONS]
get_user|user_service.py|def get_user(id: int) -> User

[TODOS]
TODO|user_service.py:42|Add validation
TODO|PostCard.tsx:15|Add loading state

[IMPLEMENTATION_LOGIC]
## user_service.py
  get_user: db.query → validate → return
"""

SAMPLE_SECTIONS = _parse_sections(SAMPLE_MATRIX_RAW)


@pytest.fixture
def provider():
    return JITContextProvider(SAMPLE_SECTIONS, max_tokens=30000)


@pytest.fixture
def small_provider():
    return JITContextProvider(SAMPLE_SECTIONS, max_tokens=500)


# ===== EXTENSION TO SECTIONS MAPPING =====

class TestExtensionMapping:
    """Tests for EXTENSION_TO_SECTIONS mapping."""

    def test_python_extension(self):
        assert ".py" in EXTENSION_TO_SECTIONS
        sections = EXTENSION_TO_SECTIONS[".py"]
        assert "PYTHON_TYPES" in sections

    def test_typescript_extension(self):
        assert ".ts" in EXTENSION_TO_SECTIONS
        sections = EXTENSION_TO_SECTIONS[".ts"]
        assert any("TYPE" in s or "INTERFACE" in s for s in sections)

    def test_tsx_extension(self):
        assert ".tsx" in EXTENSION_TO_SECTIONS
        sections = EXTENSION_TO_SECTIONS[".tsx"]
        assert "REACT_COMPONENTS" in sections

    def test_unknown_extension_not_mapped(self):
        assert ".xyz123" not in EXTENSION_TO_SECTIONS


# ===== UNIVERSAL SECTIONS =====

class TestUniversalSections:
    """Tests for universal sections always included."""

    def test_universal_sections_defined(self):
        assert "PROJECT" in UNIVERSAL_SECTIONS
        assert "BEST_PRACTICES" in UNIVERSAL_SECTIONS
        assert "RUNBOOK" in UNIVERSAL_SECTIONS

    def test_universal_sections_always_included(self, provider):
        result = provider.resolve_context("random_file.xyz")
        for section in UNIVERSAL_SECTIONS:
            if section in SAMPLE_SECTIONS:
                assert section in result.sections_included, \
                    f"Universal section {section} should always be included"


# ===== FILE CONTEXT RESOLUTION =====

class TestFileContextResolution:
    """Tests for get_context_for_file() and resolve_context()."""

    def test_python_file_gets_python_sections(self, provider):
        result = provider.resolve_context("services/user_service.py")
        has_python = any("PYTHON" in s or "SCHEMA" in s or "SERVICE" in s
                        for s in result.sections_included)
        assert has_python, "Python file should get Python-related sections"

    def test_tsx_file_gets_react_sections(self, provider):
        result = provider.resolve_context("components/UserList.tsx")
        has_react = any("REACT" in s or "COMPONENT" in s or s == "TS_TYPES"
                       for s in result.sections_included)
        assert has_react, "TSX file should get React/component sections"

    def test_file_mention_boosts_relevance(self, provider):
        result = provider.resolve_context("services/user_service.py")
        # File is mentioned in SERVICES, PYTHON_FUNCTIONS, TODOS, IMPLEMENTATION_LOGIC
        assert len(result.sections_included) > 0

    def test_result_type(self, provider):
        result = provider.resolve_context("test.py")
        assert isinstance(result, JITContextResult)

    def test_result_has_sections(self, provider):
        result = provider.resolve_context("test.py")
        assert isinstance(result.sections_included, list)

    def test_result_has_relevance_scores(self, provider):
        result = provider.resolve_context("test.py")
        assert isinstance(result.relevance_scores, dict)

    def test_result_has_context(self, provider):
        result = provider.resolve_context("test.py")
        assert isinstance(result.context, str)
        assert len(result.context) > 0

    def test_result_has_token_estimate(self, provider):
        result = provider.resolve_context("test.py")
        assert isinstance(result.token_estimate, int)
        assert result.token_estimate >= 0

    def test_get_context_returns_string(self, provider):
        context = provider.get_context_for_file("test.py")
        assert isinstance(context, str)
        assert len(context) > 0

    def test_different_files_different_context(self, provider):
        py_result = provider.resolve_context("models/user.py")
        tsx_result = provider.resolve_context("components/UserList.tsx")
        py_only = set(py_result.sections_included) - set(tsx_result.sections_included)
        tsx_only = set(tsx_result.sections_included) - set(py_result.sections_included)
        assert len(py_only) > 0 or len(tsx_only) > 0, \
            "Different file types should get different section sets"


# ===== PATH PATTERN MATCHING =====

class TestPathPatterns:
    """Tests for PATH_PATTERN_SECTIONS regex matching."""

    def test_path_patterns_defined(self):
        assert len(PATH_PATTERN_SECTIONS) > 0

    def test_controller_path_pattern(self, provider):
        result = provider.resolve_context("controllers/user_controller.py")
        assert "CONTROLLERS" in result.sections_included

    def test_model_path_pattern(self, provider):
        result = provider.resolve_context("models/user.py")
        has_schema = "SCHEMAS" in result.sections_included or "PYTHON_TYPES" in result.sections_included
        assert has_schema, "Model path should include schema/type sections"

    def test_store_path_pattern(self, provider):
        result = provider.resolve_context("stores/userStore.ts")
        assert "STORES" in result.sections_included


# ===== TOKEN BUDGET ENFORCEMENT =====

class TestTokenBudget:
    """Tests for token budget enforcement."""

    def test_respects_token_budget(self, small_provider):
        result = small_provider.resolve_context("test.py")
        assert result.token_estimate <= 500

    def test_large_budget_includes_more(self, provider, small_provider):
        large_result = provider.resolve_context("test.py")
        small_result = small_provider.resolve_context("test.py")
        assert len(large_result.sections_included) >= len(small_result.sections_included)

    def test_max_tokens_configurable(self):
        p = JITContextProvider(SAMPLE_SECTIONS, max_tokens=100)
        result = p.resolve_context("test.py")
        assert result.token_estimate <= 100


# ===== RELEVANCE SCORING =====

class TestRelevanceScoring:
    """Tests for relevance scoring logic."""

    def test_scores_are_positive(self, provider):
        result = provider.resolve_context("test.py")
        for section, score in result.relevance_scores.items():
            assert score > 0, f"Score for {section} should be positive"

    def test_sections_sorted_by_relevance(self, provider):
        result = provider.resolve_context("services/user_service.py")
        scores = [result.relevance_scores.get(s, 0) for s in result.sections_included]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], \
                "Sections should be ordered by relevance (highest first)"


# ===== HELPER METHODS =====

class TestHelperMethods:
    """Tests for get_sections_for_extension() and get_available_sections()."""

    def test_get_sections_for_extension(self, provider):
        sections = provider.get_sections_for_extension(".py")
        assert isinstance(sections, list)
        assert "PYTHON_TYPES" in sections

    def test_get_sections_for_unknown_extension(self, provider):
        sections = provider.get_sections_for_extension(".xyz999")
        assert isinstance(sections, list)
        assert len(sections) == 0

    def test_get_available_sections(self, provider):
        available = provider.get_available_sections()
        assert isinstance(available, list)
        assert "PROJECT" in available
        assert "SCHEMAS" in available
        assert len(available) > 0


# ===== EDGE CASES =====

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_sections(self):
        provider = JITContextProvider({})
        result = provider.resolve_context("test.py")
        assert isinstance(result, JITContextResult)
        assert len(result.sections_included) == 0

    def test_no_extension_file(self, provider):
        result = provider.resolve_context("Makefile")
        assert isinstance(result, JITContextResult)
        # Should still include universal sections
        for section in UNIVERSAL_SECTIONS:
            if section in SAMPLE_SECTIONS:
                assert section in result.sections_included

    def test_deeply_nested_path(self, provider):
        result = provider.resolve_context("src/modules/auth/services/auth.service.ts")
        assert isinstance(result, JITContextResult)

    def test_relative_vs_absolute_path(self, provider):
        result1 = provider.resolve_context("services/user_service.py")
        result2 = provider.resolve_context("/app/services/user_service.py")
        # Both should get service-related context
        assert "SERVICES" in result1.sections_included or "SERVICES" in result2.sections_included


# ===== FRAMEWORK COVERAGE TESTS =====

class TestFrameworkExtensionCoverage:
    """Verify all framework-specific extensions map to correct sections."""

    def test_vue_extension_correct_sections(self):
        """Vue must map to VUE_COMPOSABLES (not VUE_REACTIVITY) and VUE_ROUTING (not VUE_ROUTER)."""
        sections = EXTENSION_TO_SECTIONS[".vue"]
        assert "VUE_COMPONENTS" in sections
        assert "VUE_COMPOSABLES" in sections
        assert "VUE_DIRECTIVES" in sections
        assert "VUE_PLUGINS" in sections
        assert "VUE_ROUTING" in sections
        assert "PINIA_STORES" in sections
        # These are wrong names that should NOT exist
        assert "VUE_REACTIVITY" not in sections
        assert "VUE_ROUTER" not in sections
        assert "VUE_API" not in sections

    def test_svelte_extension_correct_sections(self):
        """Svelte must map to SVELTEKIT_ROUTING (not SVELTE_LIFECYCLE)."""
        sections = EXTENSION_TO_SECTIONS[".svelte"]
        assert "SVELTE_COMPONENTS" in sections
        assert "SVELTE_STORES" in sections
        assert "SVELTE_ACTIONS" in sections
        assert "SVELTEKIT_ROUTING" in sections
        assert "SVELTE_RUNES" in sections
        assert "SVELTE_LIFECYCLE" not in sections

    def test_astro_extension_correct_sections(self):
        """Astro must map to ASTRO_ISLANDS/ROUTING/CONTENT (not ASTRO_PAGES/LAYOUTS)."""
        sections = EXTENSION_TO_SECTIONS[".astro"]
        assert "ASTRO_COMPONENTS" in sections
        assert "ASTRO_ISLANDS" in sections
        assert "ASTRO_ROUTING" in sections
        assert "ASTRO_CONTENT" in sections
        assert "ASTRO_API" in sections
        assert "ASTRO_PAGES" not in sections
        assert "ASTRO_LAYOUTS" not in sections

    def test_tsx_includes_framework_sections(self):
        """TSX files should include state management and UI library sections."""
        sections = EXTENSION_TO_SECTIONS[".tsx"]
        assert "REACT_COMPONENTS" in sections
        assert "REACT_HOOKS" in sections
        assert "REDUX_STORES" in sections
        assert "ZUSTAND_STORES" in sections
        assert "MUI_COMPONENTS" in sections
        assert "TANSTACK_QUERIES" in sections
        assert "APOLLO_QUERIES" in sections

    def test_jsx_includes_framework_sections(self):
        """JSX files should include state management and UI library sections."""
        sections = EXTENSION_TO_SECTIONS[".jsx"]
        assert "REACT_COMPONENTS" in sections
        assert "REDUX_STORES" in sections
        assert "ZUSTAND_STORES" in sections
        assert "MUI_COMPONENTS" in sections

    def test_postcss_extension(self):
        """PostCSS extension .pcss should be mapped."""
        assert ".pcss" in EXTENSION_TO_SECTIONS
        sections = EXTENSION_TO_SECTIONS[".pcss"]
        assert "POSTCSS_PLUGINS" in sections
        assert "POSTCSS_CONFIG" in sections

    def test_mdx_extension(self):
        """MDX extension should be mapped."""
        assert ".mdx" in EXTENSION_TO_SECTIONS
        sections = EXTENSION_TO_SECTIONS[".mdx"]
        assert "REACT_COMPONENTS" in sections

    def test_html_includes_htmx_and_alpine(self):
        """HTML should include HTMX and Alpine.js sections."""
        sections = EXTENSION_TO_SECTIONS[".html"]
        assert "HTMX_ATTRIBUTES" in sections
        assert "ALPINE_DIRECTIVES" in sections
        assert "BOOTSTRAP_COMPONENTS" in sections

    def test_css_includes_tailwind(self):
        """CSS should include Tailwind sections."""
        sections = EXTENSION_TO_SECTIONS[".css"]
        assert "TAILWIND_CONFIG" in sections
        assert "TAILWIND_UTILITIES" in sections

    def test_kotlin_includes_advanced_sections(self):
        """Kotlin should include coroutines and extensions."""
        sections = EXTENSION_TO_SECTIONS[".kt"]
        assert "KOTLIN_EXTENSIONS" in sections
        assert "KOTLIN_COROUTINES" in sections

    def test_env_extension(self):
        """Env files should map to config sections."""
        assert ".env" in EXTENSION_TO_SECTIONS
        sections = EXTENSION_TO_SECTIONS[".env"]
        assert "CONFIG_VARIABLES" in sections
        assert "ENV_GAPS" in sections

    def test_all_core_languages_mapped(self):
        """Every core language must have an extension mapping."""
        required_extensions = [
            ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java",
            ".kt", ".cs", ".rs", ".swift", ".rb", ".php", ".scala",
            ".r", ".dart", ".lua", ".c", ".cpp", ".sh", ".sql",
            ".html", ".css", ".scss", ".less", ".vue", ".svelte", ".astro",
            ".ps1",
        ]
        for ext in required_extensions:
            assert ext in EXTENSION_TO_SECTIONS, f"Missing extension: {ext}"
            assert len(EXTENSION_TO_SECTIONS[ext]) > 0, f"Empty mapping: {ext}"


class TestFrameworkPathPatterns:
    """Verify path patterns include all framework-specific sections."""

    def test_component_path_includes_all_frameworks(self):
        """Component path pattern should match all component frameworks."""
        # Find the component pattern
        component_sections = []
        for pattern, sections in PATH_PATTERN_SECTIONS.items():
            if "component" in pattern.lower():
                component_sections.extend(sections)

        assert "SOLIDJS_COMPONENTS" in component_sections
        assert "QWIK_COMPONENTS" in component_sections
        assert "PREACT_COMPONENTS" in component_sections
        assert "LIT_COMPONENTS" in component_sections
        assert "ALPINE_COMPONENTS" in component_sections
        assert "BOOTSTRAP_COMPONENTS" in component_sections
        assert "MUI_COMPONENTS" in component_sections
        assert "ANTD_COMPONENTS" in component_sections
        assert "CHAKRA_COMPONENTS" in component_sections
        assert "SHADCN_COMPONENTS" in component_sections

    def test_store_path_includes_all_state_managers(self):
        """Store path pattern should match all state management libraries."""
        store_sections = []
        for pattern, sections in PATH_PATTERN_SECTIONS.items():
            if "store" in pattern.lower() or "state" in pattern.lower():
                store_sections.extend(sections)

        assert "XSTATE_MACHINES" in store_sections
        assert "VALTIO_PROXIES" in store_sections
        assert "SVELTE_STORES" in store_sections
        assert "SOLIDJS_STORES" in store_sections
        assert "SOLIDJS_SIGNALS" in store_sections
        assert "QWIK_SIGNALS" in store_sections
        assert "PREACT_SIGNALS" in store_sections

    def test_hook_path_includes_framework_hooks(self):
        """Hook path should include Preact, MUI, etc. hooks."""
        hook_sections = []
        for pattern, sections in PATH_PATTERN_SECTIONS.items():
            if "hook" in pattern.lower():
                hook_sections.extend(sections)

        assert "VUE_COMPOSABLES" in hook_sections
        assert "PREACT_HOOKS" in hook_sections
        assert "MUI_HOOKS" in hook_sections

    def test_routing_path_includes_frameworks(self):
        """Route path should include Next.js, Remix, Svelte, etc."""
        route_sections = []
        for pattern, sections in PATH_PATTERN_SECTIONS.items():
            if "route" in pattern.lower() or "routing" in pattern.lower():
                route_sections.extend(sections)

        assert "NEXT_ROUTES" in route_sections
        assert "REMIX_ROUTES" in route_sections
        assert "VUE_ROUTING" in route_sections
        assert "SVELTEKIT_ROUTING" in route_sections
        assert "ASTRO_ROUTING" in route_sections
        assert "QWIK_ROUTES" in route_sections

    def test_data_fetching_patterns(self):
        """Data fetching patterns should be recognized."""
        all_sections = []
        for pattern, sections in PATH_PATTERN_SECTIONS.items():
            if "tanstack" in pattern.lower() or "react-query" in pattern.lower():
                all_sections.extend(sections)

        assert "TANSTACK_QUERIES" in all_sections
        assert "TANSTACK_MUTATIONS" in all_sections

