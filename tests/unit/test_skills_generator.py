"""
Tests for SkillsGenerator — Auto-generated AI skills (A5.5).

Validates skill generation, detection logic, instruction enrichment,
Claude Skills format export, and context retrieval.
"""

import pytest
from codetrellis.skills_generator import (
    SkillsGenerator,
    Skill,
    SKILL_TEMPLATES,
)


# ===== FIXTURES =====

FULL_SECTIONS = {
    "PROJECT": "# name: testapp\n# lang: Python, TypeScript\n# framework: FastAPI, React",
    "SCHEMAS": "User|id:int,name:str,email:str|models/user.py\nPost|id:int,title:str|models/post.py",
    "SERVICES": "UserService|getUser(id:int):User|services/user_service.py",
    "CONTROLLERS": "UserController|GET /users,POST /users|controllers/user.py",
    "HTTP_API": "GET /api/users → UserController.list",
    "ROUTES": "/users|UserList|pages/users.tsx",
    "COMPONENTS": "UserList|props:{users:User[]}|components/UserList.tsx",
    "TYPES": "UserRole|admin,editor,viewer|types/enums.ts",
    "INTERFACES": "IUserService|getUser(id:int):User|interfaces/user.ts",
    "STORES": "useUserStore|state:{users},actions:{fetchUsers}|stores/userStore.ts",
    "INFRASTRUCTURE": "Docker, Kubernetes, AWS",
    "DATABASE": "PostgreSQL, Redis",
    "SECURITY": "JWT auth, CORS enabled",
    "BEST_PRACTICES": "# Use type hints everywhere",
    "TODOS": "TODO|user_service.py:42|Add validation",
    "GRAPHQL": "type Query { users: [User!]! }",
    "OPENAPI": "/api/users: GET list, POST create",
    "MIDDLEWARE": "auth, logging, cors",
}

MINIMAL_SECTIONS = {
    "PROJECT": "# name: tiny\n# lang: Python",
    "SCHEMAS": "Item|id:int|item.py",
}

EMPTY_SECTIONS = {}


@pytest.fixture
def full_generator():
    return SkillsGenerator(FULL_SECTIONS)


@pytest.fixture
def minimal_generator():
    return SkillsGenerator(MINIMAL_SECTIONS)


@pytest.fixture
def empty_generator():
    return SkillsGenerator(EMPTY_SECTIONS)


# ===== SKILL GENERATION =====

class TestSkillGeneration:
    """Tests for generate() method."""

    def test_generates_skills(self, full_generator):
        skills = full_generator.generate()
        assert isinstance(skills, list)
        assert len(skills) > 0

    def test_skills_are_skill_instances(self, full_generator):
        skills = full_generator.generate()
        for skill in skills:
            assert isinstance(skill, Skill)

    def test_skill_has_required_fields(self, full_generator):
        skills = full_generator.generate()
        for skill in skills:
            assert skill.name is not None and len(skill.name) > 0
            assert skill.description is not None and len(skill.description) > 0
            assert skill.instructions is not None and len(skill.instructions) > 0
            assert isinstance(skill.context_sections, list)
            assert len(skill.context_sections) > 0
            assert skill.trigger is not None

    def test_minimal_sections_fewer_skills(self, full_generator, minimal_generator):
        full_skills = full_generator.generate()
        minimal_skills = minimal_generator.generate()
        assert len(full_skills) > len(minimal_skills), \
            "More sections should enable more skills"

    def test_empty_sections_minimal_skills(self, empty_generator):
        skills = empty_generator.generate()
        assert len(skills) <= 2

    def test_no_duplicate_skill_names(self, full_generator):
        skills = full_generator.generate()
        names = [s.name for s in skills]
        assert len(names) == len(set(names)), "Skill names should be unique"


# ===== SKILL DETECTION LOGIC =====

class TestSkillDetection:
    """Tests that skills are only generated when required sections exist."""

    def test_add_endpoint_requires_api_sections(self, full_generator):
        skills = full_generator.generate()
        names = [s.name for s in skills]
        assert "add-endpoint" in names

    def test_add_component_requires_components(self, full_generator):
        skills = full_generator.generate()
        names = [s.name for s in skills]
        assert "add-component" in names

    def test_no_component_skill_without_components(self):
        sections = {"PROJECT": "# name: api-only", "SERVICES": "SomeService|..."}
        gen = SkillsGenerator(sections)
        skills = gen.generate()
        names = [s.name for s in skills]
        assert "add-component" not in names

    def test_add_model_requires_schemas(self, full_generator):
        skills = full_generator.generate()
        names = [s.name for s in skills]
        assert "add-model" in names

    def test_no_store_skill_without_stores(self):
        sections = {"PROJECT": "# name: test", "SCHEMAS": "User|id:int"}
        gen = SkillsGenerator(sections)
        skills = gen.generate()
        names = [s.name for s in skills]
        assert "add-store" not in names

    def test_fix_issue_requires_todos(self, full_generator):
        skills = full_generator.generate()
        names = [s.name for s in skills]
        assert "fix-issue" in names

    def test_security_review_requires_security(self, full_generator):
        skills = full_generator.generate()
        names = [s.name for s in skills]
        assert "security-review" in names


# ===== SKILL RETRIEVAL =====

class TestSkillRetrieval:
    """Tests for get_skill_by_name() and get_skill_context()."""

    def test_get_skill_by_name(self, full_generator):
        full_generator.generate()
        skill = full_generator.get_skill_by_name("add-endpoint")
        assert skill is not None
        assert skill.name == "add-endpoint"

    def test_get_nonexistent_skill(self, full_generator):
        full_generator.generate()
        skill = full_generator.get_skill_by_name("nonexistent-skill-xyz")
        assert skill is None

    def test_get_skill_context(self, full_generator):
        full_generator.generate()
        context = full_generator.get_skill_context("add-endpoint")
        assert context is not None
        assert isinstance(context, str)
        assert len(context) > 0

    def test_get_context_nonexistent_skill(self, full_generator):
        full_generator.generate()
        context = full_generator.get_skill_context("nonexistent-skill-xyz")
        assert context is None

    def test_list_skill_names(self, full_generator):
        full_generator.generate()
        names = full_generator.list_skill_names()
        assert isinstance(names, list)
        assert len(names) > 0
        for name in names:
            assert isinstance(name, str)


# ===== SKILL DATA STRUCTURES =====

class TestSkillDataclass:
    """Tests for Skill dataclass methods."""

    def test_skill_to_dict(self, full_generator):
        skills = full_generator.generate()
        for skill in skills:
            d = skill.to_dict()
            assert "name" in d
            assert "description" in d
            assert "instructions" in d
            assert "context_sections" in d
            assert isinstance(d["context_sections"], list)

    def test_skill_get_context(self, full_generator):
        skills = full_generator.generate()
        for skill in skills:
            context = skill.get_context(FULL_SECTIONS)
            assert isinstance(context, str)

    def test_skill_has_category(self, full_generator):
        skills = full_generator.generate()
        for skill in skills:
            assert isinstance(skill.category, str)
            assert len(skill.category) > 0


# ===== CLAUDE SKILLS FORMAT =====

class TestClaudeSkillsFormat:
    """Tests for to_claude_skills_format() export."""

    def test_claude_format_structure(self, full_generator):
        full_generator.generate()
        claude_skills = full_generator.to_claude_skills_format()
        assert isinstance(claude_skills, list)
        assert len(claude_skills) > 0

    def test_claude_format_fields(self, full_generator):
        full_generator.generate()
        claude_skills = full_generator.to_claude_skills_format()
        for skill in claude_skills:
            assert isinstance(skill, dict)

    def test_claude_format_serializable(self, full_generator):
        """Claude skills format should be JSON-serializable."""
        import json
        full_generator.generate()
        claude_skills = full_generator.to_claude_skills_format()
        json_str = json.dumps(claude_skills)
        assert len(json_str) > 0


# ===== INSTRUCTION ENRICHMENT =====

class TestInstructionEnrichment:
    """Tests for _enrich_instructions() — project-specific context injection."""

    def test_enriched_instructions_substantial(self, full_generator):
        skills = full_generator.generate()
        for skill in skills:
            assert len(skill.instructions) > 10, \
                f"Skill {skill.name} should have substantial instructions"

    def test_enriched_instructions_vary_by_skill(self, full_generator):
        skills = full_generator.generate()
        if len(skills) >= 2:
            assert skills[0].instructions != skills[1].instructions, \
                "Different skills should have different instructions"


# ===== SKILL TEMPLATES =====

class TestSkillTemplates:
    """Tests for SKILL_TEMPLATES constant."""

    def test_templates_exist(self):
        assert isinstance(SKILL_TEMPLATES, list)
        assert len(SKILL_TEMPLATES) > 0

    def test_template_structure(self):
        for template in SKILL_TEMPLATES:
            assert "name" in template
            assert "description" in template
            assert "context_sections" in template
            assert "detect_sections" in template
            assert isinstance(template["context_sections"], list)
            assert isinstance(template["detect_sections"], list)

    def test_template_names_unique(self):
        names = [t["name"] for t in SKILL_TEMPLATES]
        assert len(names) == len(set(names))

    def test_expected_templates_exist(self):
        names = [t["name"] for t in SKILL_TEMPLATES]
        expected = ["add-endpoint", "add-model", "add-component",
                     "fix-issue", "security-review",
                     "add-style", "add-route", "add-data-fetch"]
        for name in expected:
            assert name in names, f"Expected template: {name}"


# ===== EDGE CASES =====

class TestEdgeCases:
    """Edge case tests."""

    def test_generate_idempotent(self, full_generator):
        skills1 = full_generator.generate()
        skills2 = full_generator.generate()
        names1 = [s.name for s in skills1]
        names2 = [s.name for s in skills2]
        assert names1 == names2

    def test_sections_with_empty_content(self):
        sections = {"PROJECT": "", "SCHEMAS": "", "SERVICES": ""}
        gen = SkillsGenerator(sections)
        skills = gen.generate()
        assert isinstance(skills, list)

    def test_large_section_content(self):
        sections = {
            "PROJECT": "# name: bigapp\n# lang: Python",
            "SCHEMAS": "Schema|" + ",".join(f"field{i}:str" for i in range(100)) + "|big.py",
        }
        gen = SkillsGenerator(sections)
        skills = gen.generate()
        assert isinstance(skills, list)


# ===== FRAMEWORK COVERAGE TESTS =====

class TestFrameworkCoverage:
    """Verify skills detect all integrated frameworks."""

    def test_add_component_detects_all_frameworks(self):
        """add-component should detect SolidJS, Qwik, Preact, Alpine, HTMX, Bootstrap."""
        template = next(t for t in SKILL_TEMPLATES if t["name"] == "add-component")
        detect = template["detect_sections"]
        assert "SOLIDJS_COMPONENTS" in detect
        assert "QWIK_COMPONENTS" in detect
        assert "PREACT_COMPONENTS" in detect
        assert "ALPINE_COMPONENTS" in detect
        assert "HTMX_ATTRIBUTES" in detect
        assert "BOOTSTRAP_COMPONENTS" in detect
        assert "MUI_COMPONENTS" in detect
        assert "ANTD_COMPONENTS" in detect
        assert "CHAKRA_COMPONENTS" in detect
        assert "SHADCN_COMPONENTS" in detect
        assert "RADIX_COMPONENTS" in detect
        assert "SC_COMPONENTS" in detect
        assert "EM_COMPONENTS" in detect

    def test_add_store_detects_all_state_managers(self):
        """add-store should detect Valtio, XState, Svelte stores, SolidJS, etc."""
        template = next(t for t in SKILL_TEMPLATES if t["name"] == "add-store")
        detect = template["detect_sections"]
        assert "VALTIO_PROXIES" in detect
        assert "XSTATE_MACHINES" in detect
        assert "SVELTE_STORES" in detect
        assert "SOLIDJS_STORES" in detect
        assert "SOLIDJS_SIGNALS" in detect
        assert "QWIK_SIGNALS" in detect
        assert "PREACT_SIGNALS" in detect
        assert "ALPINE_STORES" in detect
        assert "ZUSTAND_SELECTORS" in detect
        assert "JOTAI_SELECTORS" in detect
        assert "RECOIL_SELECTORS" in detect
        assert "NGRX_EFFECTS" in detect
        assert "NGRX_SELECTORS" in detect

    def test_add_endpoint_detects_all_api_sections(self):
        """add-endpoint should detect all language API sections."""
        template = next(t for t in SKILL_TEMPLATES if t["name"] == "add-endpoint")
        detect = template["detect_sections"]
        assert "DART_API" in detect
        assert "LUA_API" in detect
        assert "C_API" in detect
        assert "CPP_API" in detect
        assert "POWERSHELL_API" in detect
        assert "BASH_API" in detect
        assert "R_API" in detect
        assert "NEXT_SERVER_ACTIONS" in detect
        assert "REMIX_ACTIONS" in detect
        assert "ASTRO_API" in detect
        assert "SOLIDJS_API" in detect
        assert "QWIK_API" in detect
        assert "PREACT_API" in detect
        assert "LIT_API" in detect
        assert "ALPINE_API" in detect
        assert "HTMX_API" in detect

    def test_add_model_detects_all_model_sections(self):
        """add-model should detect all language model sections."""
        template = next(t for t in SKILL_TEMPLATES if t["name"] == "add-model")
        detect = template["detect_sections"]
        assert "DART_MODELS" in detect
        assert "LUA_MODELS" in detect
        assert "SWIFT_MODELS" in detect
        assert "SCALA_MODELS" in detect
        assert "GO_TYPES" in detect
        assert "C_TYPES" in detect
        assert "CPP_TYPES" in detect
        assert "POWERSHELL_MODELS" in detect
        assert "R_MODELS" in detect

    def test_add_hook_detects_all_hooks(self):
        """add-hook should detect Preact, MUI, SWR hooks."""
        template = next(t for t in SKILL_TEMPLATES if t["name"] == "add-hook")
        detect = template["detect_sections"]
        assert "PREACT_HOOKS" in detect
        assert "SOLIDJS_SIGNALS" in detect
        assert "MUI_HOOKS" in detect
        assert "ANTD_HOOKS" in detect
        assert "CHAKRA_HOOKS" in detect
        assert "SHADCN_HOOKS" in detect
        assert "SWR_HOOKS" in detect

    def test_add_style_template(self):
        """add-style skill should detect CSS, Sass, Tailwind, styled-components, etc."""
        template = next(t for t in SKILL_TEMPLATES if t["name"] == "add-style")
        detect = template["detect_sections"]
        assert "CSS_SELECTORS" in detect
        assert "SASS_VARIABLES" in detect
        assert "TAILWIND_CONFIG" in detect
        assert "SC_COMPONENTS" in detect
        assert "EM_COMPONENTS" in detect
        assert "MUI_THEME" in detect
        assert "BOOTSTRAP_THEME" in detect
        assert "POSTCSS_PLUGINS" in detect

    def test_add_route_template(self):
        """add-route skill should detect Next.js, Remix, Vue, Svelte, Astro routing."""
        template = next(t for t in SKILL_TEMPLATES if t["name"] == "add-route")
        detect = template["detect_sections"]
        assert "NEXT_PAGES" in detect
        assert "NEXT_ROUTES" in detect
        assert "REMIX_ROUTES" in detect
        assert "VUE_ROUTING" in detect
        assert "SVELTEKIT_ROUTING" in detect
        assert "ASTRO_ROUTING" in detect
        assert "QWIK_ROUTES" in detect

    def test_add_data_fetch_template(self):
        """add-data-fetch skill should detect TanStack, SWR, Apollo."""
        template = next(t for t in SKILL_TEMPLATES if t["name"] == "add-data-fetch")
        detect = template["detect_sections"]
        assert "TANSTACK_QUERIES" in detect
        assert "SWR_HOOKS" in detect
        assert "APOLLO_QUERIES" in detect
        assert "NEXT_DATA_FETCHING" in detect
        assert "REMIX_LOADERS" in detect
        assert "SOLIDJS_RESOURCES" in detect
        assert "QWIK_TASKS" in detect

    def test_solidjs_store_activates_add_store(self):
        """SolidJS signals should activate the add-store skill."""
        sections = {"SOLIDJS_SIGNALS": "count|number|app.tsx", "PROJECT": "# solid"}
        gen = SkillsGenerator(sections)
        skill_names = gen.list_skill_names()
        assert "add-store" in skill_names

    def test_valtio_activates_add_store(self):
        """Valtio proxies should activate the add-store skill."""
        sections = {"VALTIO_PROXIES": "state|{count:0}|state.ts", "PROJECT": "# v"}
        gen = SkillsGenerator(sections)
        skill_names = gen.list_skill_names()
        assert "add-store" in skill_names

    def test_tailwind_activates_add_style(self):
        """Tailwind config should activate the add-style skill."""
        sections = {"TAILWIND_CONFIG": "theme: {...}", "PROJECT": "# app"}
        gen = SkillsGenerator(sections)
        skill_names = gen.list_skill_names()
        assert "add-style" in skill_names

    def test_next_routes_activates_add_route(self):
        """Next.js routes should activate the add-route skill."""
        sections = {"NEXT_ROUTES": "/api/users|handler|route.ts", "PROJECT": "# n"}
        gen = SkillsGenerator(sections)
        skill_names = gen.list_skill_names()
        assert "add-route" in skill_names

    def test_tanstack_activates_add_data_fetch(self):
        """TanStack queries should activate the add-data-fetch skill."""
        sections = {"TANSTACK_QUERIES": "useUsers|['users']|hooks.ts", "PROJECT": "# t"}
        gen = SkillsGenerator(sections)
        skill_names = gen.list_skill_names()
        assert "add-data-fetch" in skill_names

    def test_total_skill_templates_count(self):
        """Verify total skill template count after expansion."""
        assert len(SKILL_TEMPLATES) == 18  # 14 original + 3 new + 1 storybook
