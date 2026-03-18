"""
Tests for CodeTrellis AI Integration File Generation
=====================================================

Comprehensive test suite covering the init_integrations module:

    T1: MatrixContext extraction from real matrix data
    T2: Language-aware convention filtering
    T3: Quality gates — language-specific linter detection
    T4: Version & release — detection from pyproject.toml / package.json / Cargo.toml
    T5: Lifecycle guidance — correct test/lint commands per language
    T6: Template generators — copilot-instructions, CLAUDE.md, .cursorrules consistency
    T7: Agent file generation — 4 agent files with correct project context
    T8: No cross-language contamination (Python linters don't appear in Go projects)
    T9: Full integration — scan → init --ai → validate output

Per D3 Quality Gate:
    - All tests use tmp_path fixture (no hardcoded paths)
    - No external network dependencies
    - Tests should pass with pytest tests/unit/test_init_integrations.py -x -q
"""

import json
import sys
from pathlib import Path
from typing import List

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from codetrellis.init_integrations import (
    ProjectInfo,
    MatrixContext,
    detect_project,
    extract_matrix_context,
    generate_copilot_instructions,
    generate_claude_md,
    generate_cursorrules,
    generate_agent_files,
    generate_ai_integrations,
    _parse_best_practices,
    _build_conventions_block,
    _build_quality_gates_block,
    _build_version_block,
    _build_lifecycle_block,
    _build_known_pitfalls_block,
    _build_architecture_block,
    _build_mcp_tools_block,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def python_info() -> ProjectInfo:
    """A Python library project."""
    return ProjectInfo(
        name="mylib",
        root=Path("/fake"),
        project_type="Python Library",
        detected_languages=["Python"],
        detected_frameworks=["FastAPI"],
        has_pyproject=True,
        test_command="pytest tests/ -x -q",
    )


@pytest.fixture
def go_info() -> ProjectInfo:
    """A Go web service project."""
    return ProjectInfo(
        name="myservice",
        root=Path("/fake"),
        project_type="Go Web Service",
        detected_languages=["Go"],
        detected_frameworks=["Gin"],
        has_go_mod=True,
        test_command="go test ./...",
    )


@pytest.fixture
def ts_info() -> ProjectInfo:
    """A TypeScript/Node project."""
    return ProjectInfo(
        name="myapp",
        root=Path("/fake"),
        project_type="Node Web App",
        detected_languages=["TypeScript"],
        detected_frameworks=["Next.js"],
        has_package_json=True,
        test_command="npm test",
    )


@pytest.fixture
def rust_info() -> ProjectInfo:
    """A Rust project."""
    return ProjectInfo(
        name="mycrate",
        root=Path("/fake"),
        project_type="Unknown",
        detected_languages=["Rust"],
        detected_frameworks=[],
        has_cargo_toml=True,
        test_command="cargo test",
    )


@pytest.fixture
def java_info() -> ProjectInfo:
    """A Java Spring project."""
    return ProjectInfo(
        name="myspring",
        root=Path("/fake"),
        project_type="Spring Boot Application",
        detected_languages=["Java"],
        detected_frameworks=["Spring Boot"],
        test_command="./mvnw test",
    )


@pytest.fixture
def python_ctx() -> MatrixContext:
    """Rich matrix context for a Python project."""
    return MatrixContext(
        project_name="mylib",
        project_type="Python Library",
        business_domain="Developer Tools",
        business_purpose="A code analysis library.",
        overview="Full overview text",
        runbook="pytest tests/ -x -q\nruff check mylib/",
        cli_commands="scan - Scan project\ninit - Initialize",
        project_structure="mylib(50),scripts(5),tests(20),docs(3)",
        best_practices="python:library|use:type-hints,docstrings,pytest,ruff,mypy|avoid:print,global-state\nbash:|use:set-euo-pipefail,shellcheck|avoid:eval",
        best_practices_parsed=[
            {"lang": "python", "category": "library",
             "use": ["type-hints", "docstrings", "pytest", "ruff", "mypy"],
             "avoid": ["print", "global-state"]},
            {"lang": "bash", "category": "",
             "use": ["set-euo-pipefail", "shellcheck"],
             "avoid": ["eval"]},
        ],
        primary_language="Python",
        primary_type_section="PYTHON_TYPES",
        python_version=">=3.9",
        version_source="pyproject.toml (version = \"1.0.0\")",
        ci_jobs=["lint", "test", "build", "publish"],
        ci_triggers="push",
        contributing_steps=[
            "Import: `from mylib.parser import MyParser`",
            "Add dispatch in scanner.py",
            "Add tests",
        ],
        data_flow_pattern="Request-Response",
        type_count=150,
        total_files=500,
        sections=["OVERVIEW", "PROJECT", "PYTHON_TYPES", "RUNBOOK",
                   "BUSINESS_DOMAIN", "CLI_COMMANDS", "BEST_PRACTICES",
                   "IMPLEMENTATION_LOGIC"],
        section_count=28,
    )


@pytest.fixture
def go_ctx() -> MatrixContext:
    """Rich matrix context for a Go project."""
    return MatrixContext(
        project_name="myservice",
        project_type="Go Web Service",
        business_domain="Web Framework/Library",
        business_purpose="HTTP router library.",
        best_practices_parsed=[
            {"lang": "go", "category": "",
             "use": ["error-wrapping", "context", "interfaces", "golangci-lint"],
             "avoid": ["panic", "naked-returns"]},
            {"lang": "python", "category": "library",
             "use": ["type-hints", "ruff", "mypy"],
             "avoid": ["print"]},
            {"lang": "bash", "category": "",
             "use": ["shellcheck"],
             "avoid": ["eval"]},
        ],
        primary_language="Go",
        primary_type_section="GO_TYPES",
        sections=["OVERVIEW", "GO_TYPES", "RUNBOOK", "BEST_PRACTICES"],
        section_count=20,
        type_count=71,
        total_files=130,
    )


@pytest.fixture
def rust_ctx() -> MatrixContext:
    """Rich matrix context for a Rust project."""
    return MatrixContext(
        project_name="mycrate",
        project_type="Unknown",
        best_practices_parsed=[
            {"lang": "rust", "category": "",
             "use": ["Result<T, E>", "Option", "iterators", "clippy"],
             "avoid": ["unwrap", "clone-abuse"]},
            {"lang": "python", "category": "library",
             "use": ["ruff", "mypy"],
             "avoid": ["print"]},
        ],
        primary_language="Rust",
        primary_type_section="RUST_TYPES",
        version_source="Cargo.toml (version = \"0.5.0\")",
        sections=["OVERVIEW", "RUST_TYPES", "RUNBOOK", "BEST_PRACTICES"],
        section_count=22,
        type_count=100,
        total_files=80,
    )


# ---------------------------------------------------------------------------
# T1: _parse_best_practices
# ---------------------------------------------------------------------------

class TestParseBestPractices:
    """Test parsing of best practices from matrix format."""

    def test_single_entry(self) -> None:
        raw = "python:library|use:type-hints,docstrings|avoid:print"
        result = _parse_best_practices(raw)
        assert len(result) == 1
        assert result[0]["lang"] == "python"
        assert result[0]["category"] == "library"
        assert "type-hints" in result[0]["use"]
        assert "print" in result[0]["avoid"]

    def test_multiple_entries(self) -> None:
        raw = "python:library|use:ruff,mypy|avoid:print\ngo:|use:golangci-lint|avoid:panic"
        result = _parse_best_practices(raw)
        assert len(result) == 2
        assert result[0]["lang"] == "python"
        assert result[1]["lang"] == "go"

    def test_empty_input(self) -> None:
        assert _parse_best_practices("") == []
        assert _parse_best_practices("   ") == []

    def test_no_avoid(self) -> None:
        raw = "rust:|use:clippy,cargo-fmt"
        result = _parse_best_practices(raw)
        assert len(result) == 1
        assert result[0]["use"] == ["clippy", "cargo-fmt"]
        assert result[0].get("avoid", []) == []

    def test_entry_without_category(self) -> None:
        raw = "bash:|use:shellcheck|avoid:eval"
        result = _parse_best_practices(raw)
        assert result[0]["lang"] == "bash"
        assert result[0]["category"] == ""


# ---------------------------------------------------------------------------
# T2: Language-aware convention filtering
# ---------------------------------------------------------------------------

class TestConventionsBlock:
    """Test that conventions are language-filtered."""

    def test_python_project_includes_python(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_conventions_block(python_info, python_ctx)
        assert "python" in block.lower()
        assert "type-hints" in block

    def test_python_project_includes_bash(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        """Bash is always included."""
        block = _build_conventions_block(python_info, python_ctx)
        assert "bash" in block.lower()

    def test_go_project_excludes_python(
        self, go_info: ProjectInfo, go_ctx: MatrixContext,
    ) -> None:
        """Python conventions should NOT appear in a Go project."""
        block = _build_conventions_block(go_info, go_ctx)
        assert "ruff" not in block
        assert "mypy" not in block
        # Go conventions should be present
        assert "error-wrapping" in block or "go" in block.lower()

    def test_rust_project_excludes_python(
        self, rust_info: ProjectInfo, rust_ctx: MatrixContext,
    ) -> None:
        block = _build_conventions_block(rust_info, rust_ctx)
        assert "ruff" not in block
        assert "mypy" not in block
        assert "rust" in block.lower()

    def test_no_ctx_fallback(self, go_info: ProjectInfo) -> None:
        """Without ctx, should fall back to generic conventions."""
        block = _build_conventions_block(go_info, None)
        assert "Go" in block  # language name
        assert "Follow existing patterns" in block

    def test_contributing_steps_included(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_conventions_block(python_info, python_ctx)
        assert "Contributing" in block
        assert "from mylib.parser" in block


# ---------------------------------------------------------------------------
# T3: Quality gates — language-specific linters
# ---------------------------------------------------------------------------

class TestQualityGatesBlock:
    """Test that quality gates only include relevant linters."""

    def test_python_includes_ruff(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_quality_gates_block(python_info, python_ctx)
        assert "ruff" in block

    def test_python_includes_mypy_as_advisory(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_quality_gates_block(python_info, python_ctx)
        assert "mypy" in block
        assert "advisory" in block

    def test_go_excludes_ruff(
        self, go_info: ProjectInfo, go_ctx: MatrixContext,
    ) -> None:
        block = _build_quality_gates_block(go_info, go_ctx)
        assert "ruff" not in block
        assert "mypy" not in block

    def test_go_includes_golangci_lint(
        self, go_info: ProjectInfo, go_ctx: MatrixContext,
    ) -> None:
        block = _build_quality_gates_block(go_info, go_ctx)
        assert "golangci-lint" in block

    def test_rust_includes_clippy(
        self, rust_info: ProjectInfo, rust_ctx: MatrixContext,
    ) -> None:
        block = _build_quality_gates_block(rust_info, rust_ctx)
        assert "clippy" in block

    def test_rust_excludes_ruff(
        self, rust_info: ProjectInfo, rust_ctx: MatrixContext,
    ) -> None:
        block = _build_quality_gates_block(rust_info, rust_ctx)
        assert "ruff" not in block

    def test_empty_without_ctx(self, python_info: ProjectInfo) -> None:
        block = _build_quality_gates_block(python_info, None)
        assert block == ""


# ---------------------------------------------------------------------------
# T4: Version & release
# ---------------------------------------------------------------------------

class TestVersionBlock:
    """Test version detection per language."""

    def test_pyproject_toml(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_version_block(python_info, python_ctx)
        assert "pyproject.toml" in block
        assert "importlib.metadata" in block

    def test_cargo_toml(
        self, rust_info: ProjectInfo, rust_ctx: MatrixContext,
    ) -> None:
        block = _build_version_block(rust_info, rust_ctx)
        assert "Cargo.toml" in block

    def test_package_json(self, ts_info: ProjectInfo) -> None:
        ctx = MatrixContext(
            project_name="myapp",
            version_source='package.json (version = "2.0.0")',
        )
        block = _build_version_block(ts_info, ctx)
        assert "package.json" in block
        assert "npm version" in block

    def test_empty_without_version_source(
        self, python_info: ProjectInfo,
    ) -> None:
        ctx = MatrixContext(project_name="test")
        block = _build_version_block(python_info, ctx)
        assert block == ""


# ---------------------------------------------------------------------------
# T5: Lifecycle guidance
# ---------------------------------------------------------------------------

class TestLifecycleBlock:
    """Test lifecycle guidance correctness."""

    def test_python_lifecycle_uses_pytest(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_lifecycle_block(python_info, python_ctx)
        assert "pytest" in block
        assert "ruff check" in block

    def test_go_lifecycle_uses_go_test(
        self, go_info: ProjectInfo, go_ctx: MatrixContext,
    ) -> None:
        block = _build_lifecycle_block(go_info, go_ctx)
        assert "go test" in block
        # Should NOT recommend ruff for Go
        assert "ruff" not in block

    def test_rust_lifecycle(
        self, rust_info: ProjectInfo, rust_ctx: MatrixContext,
    ) -> None:
        block = _build_lifecycle_block(rust_info, rust_ctx)
        assert "cargo test" in block
        assert "ruff" not in block

    def test_contributing_steps_used(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_lifecycle_block(python_info, python_ctx)
        assert "New feature" in block
        # Should reference contributing steps
        assert "mylib" in block or "parser" in block.lower()


# ---------------------------------------------------------------------------
# T6: Template generators — consistency
# ---------------------------------------------------------------------------

class TestTemplateGenerators:
    """Test that all 3 template generators produce consistent output."""

    def test_copilot_has_all_sections(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        output = generate_copilot_instructions(python_info, python_ctx)
        assert "# GitHub Copilot" in output
        assert "CodeTrellis Matrix" in output
        assert "MCP Server Tools" in output
        assert "Key Conventions" in output
        assert "Quality Gates" in output
        assert "Version & Release" in output
        assert "Lifecycle Guidance" in output
        assert "Known Pitfalls" in output

    def test_claude_has_all_sections(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        output = generate_claude_md(python_info, python_ctx)
        assert "CLAUDE.md" in output
        assert "Read the Matrix FIRST" in output
        assert "Quick Commands" in output
        assert "Quality Gates" in output
        assert "Key Conventions" in output
        assert "Lifecycle Guidance" in output
        assert "Known Pitfalls" in output

    def test_cursorrules_has_all_sections(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        output = generate_cursorrules(python_info, python_ctx)
        assert "Cursor Rules" in output
        assert "CodeTrellis Matrix" in output
        assert "MCP Server Tools" in output
        assert "Key Conventions" in output
        assert "Quality Gates" in output
        assert "Lifecycle Guidance" in output

    def test_copilot_uses_correct_type_section(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        output = generate_copilot_instructions(python_info, python_ctx)
        assert "PYTHON_TYPES" in output

    def test_claude_uses_correct_type_section(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        """CLAUDE.md should reference PYTHON_TYPES, not TS_TYPES."""
        output = generate_claude_md(python_info, python_ctx)
        assert "PYTHON_TYPES" in output
        assert "TS_TYPES" not in output
        # Should not have hardcoded src/path/to/file.ts
        assert "src/path/to/file.ts" not in output

    def test_claude_uses_ts_types_for_ts_project(self, ts_info: ProjectInfo) -> None:
        ctx = MatrixContext(
            project_name="myapp",
            primary_language="TypeScript",
            primary_type_section="TS_TYPES",
            sections=["OVERVIEW", "TS_TYPES"],
            section_count=15,
        )
        output = generate_claude_md(ts_info, ctx)
        assert "TS_TYPES" in output

    def test_go_output_has_no_python_references(
        self, go_info: ProjectInfo, go_ctx: MatrixContext,
    ) -> None:
        for gen_fn in [generate_copilot_instructions, generate_claude_md, generate_cursorrules]:
            output = gen_fn(go_info, go_ctx)
            # Should not reference Python tools
            assert "ruff" not in output.lower()
            assert "mypy" not in output.lower()
            assert "pyproject.toml" not in output

    def test_basic_mode_without_ctx(self, python_info: ProjectInfo) -> None:
        """All generators should work without MatrixContext."""
        for gen_fn in [generate_copilot_instructions, generate_claude_md, generate_cursorrules]:
            output = gen_fn(python_info, None)
            assert python_info.name in output
            assert "Python" in output


# ---------------------------------------------------------------------------
# T7: Agent file generation
# ---------------------------------------------------------------------------

class TestAgentFiles:
    """Test agent file generation."""

    def test_generates_four_agents(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        agents = generate_agent_files(python_info, python_ctx)
        assert len(agents) == 4
        names = [a[0] for a in agents]
        assert ".github/agents/ct-research.agent.md" in names
        assert ".github/agents/ct-implement.agent.md" in names
        assert ".github/agents/ct-verify.agent.md" in names
        assert ".github/agents/ct-orchestrator.agent.md" in names

    def test_agent_has_yaml_frontmatter(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        agents = generate_agent_files(python_info, python_ctx)
        for _, content, _ in agents:
            assert content.startswith("---\n")
            assert "name:" in content
            assert "description:" in content

    def test_agents_reference_project_name(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        agents = generate_agent_files(python_info, python_ctx)
        for _, content, _ in agents:
            assert python_info.name in content

    def test_agents_have_quality_checks(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        agents = generate_agent_files(python_info, python_ctx)
        # ct-implement and ct-verify should have quality checks
        agent_dict = {a[0]: a[1] for a in agents}
        implement = agent_dict[".github/agents/ct-implement.agent.md"]
        verify = agent_dict[".github/agents/ct-verify.agent.md"]
        assert "Quality Checks" in implement or "pytest" in implement
        assert "Quality Checks" in verify or "pytest" in verify

    def test_orchestrator_references_matrix(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        agents = generate_agent_files(python_info, python_ctx)
        agent_dict = {a[0]: a[1] for a in agents}
        orch = agent_dict[".github/agents/ct-orchestrator.agent.md"]
        assert "matrix.prompt" in orch
        assert python_ctx.project_name in orch


# ---------------------------------------------------------------------------
# T8: Cross-language contamination checks
# ---------------------------------------------------------------------------

class TestNoContamination:
    """Ensure language-specific tools don't leak into wrong projects."""

    def test_go_project_no_python_linters(
        self, go_info: ProjectInfo, go_ctx: MatrixContext,
    ) -> None:
        conventions = _build_conventions_block(go_info, go_ctx)
        gates = _build_quality_gates_block(go_info, go_ctx)
        lifecycle = _build_lifecycle_block(go_info, go_ctx)

        for section in [conventions, gates, lifecycle]:
            assert "ruff" not in section, f"ruff leaked into Go section: {section[:100]}"
            assert "mypy" not in section, f"mypy leaked into Go section: {section[:100]}"

    def test_rust_project_no_python_linters(
        self, rust_info: ProjectInfo, rust_ctx: MatrixContext,
    ) -> None:
        conventions = _build_conventions_block(rust_info, rust_ctx)
        gates = _build_quality_gates_block(rust_info, rust_ctx)
        lifecycle = _build_lifecycle_block(rust_info, rust_ctx)

        for section in [conventions, gates, lifecycle]:
            assert "ruff" not in section, f"ruff leaked into Rust: {section[:100]}"
            assert "mypy" not in section, f"mypy leaked into Rust: {section[:100]}"

    def test_java_no_python_tools(self, java_info: ProjectInfo) -> None:
        ctx = MatrixContext(
            project_name="myspring",
            best_practices_parsed=[
                {"lang": "java", "category": "",
                 "use": ["records", "sealed-classes"],
                 "avoid": ["raw-types"]},
                {"lang": "python", "category": "quality",
                 "use": ["ruff", "mypy", "black"],
                 "avoid": ["any-type"]},
            ],
        )
        conventions = _build_conventions_block(java_info, ctx)
        gates = _build_quality_gates_block(java_info, ctx)

        assert "ruff" not in conventions
        assert "ruff" not in gates
        assert "java" in conventions.lower()


# ---------------------------------------------------------------------------
# T9: Full integration — generate_ai_integrations with tmp_path
# ---------------------------------------------------------------------------

class TestIntegration:
    """Full integration test using tmp_path."""

    def _setup_project(self, tmp_path: Path, lang: str = "python") -> Path:
        """Create a minimal project structure for testing."""
        if lang == "python":
            (tmp_path / "pyproject.toml").write_text(
                '[project]\nname = "testproj"\nversion = "0.1.0"\n'
                'requires-python = ">=3.9"\n'
            )
            (tmp_path / "testproj").mkdir()
            (tmp_path / "testproj" / "__init__.py").write_text("")
            (tmp_path / "testproj" / "main.py").write_text("def hello(): pass\n")
        elif lang == "node":
            (tmp_path / "package.json").write_text(json.dumps({
                "name": "testproj",
                "version": "1.0.0",
                "scripts": {"test": "jest"},
            }))
            (tmp_path / "src").mkdir()
            (tmp_path / "src" / "index.ts").write_text("export const x = 1;\n")
        elif lang == "go":
            (tmp_path / "go.mod").write_text("module testproj\n\ngo 1.21\n")
            (tmp_path / "main.go").write_text("package main\n\nfunc main() {}\n")
        return tmp_path

    def test_generate_all_files_python(self, tmp_path: Path) -> None:
        """Test that generate_ai_integrations creates all expected files."""
        project = self._setup_project(tmp_path, "python")
        results = generate_ai_integrations(project, force=True)

        # Should create at least 5 core files + 4 agent files
        assert len(results) >= 5
        created_paths = {str(r.path.relative_to(project)) for r in results}
        assert ".github/copilot-instructions.md" in created_paths
        assert "CLAUDE.md" in created_paths
        assert ".cursorrules" in created_paths
        assert ".vscode/mcp.json" in created_paths
        assert ".vscode/tasks.json" in created_paths

    def test_generate_agent_files_created(self, tmp_path: Path) -> None:
        """Test that agent files are physically created."""
        project = self._setup_project(tmp_path, "python")
        generate_ai_integrations(project, force=True)

        assert (project / ".github" / "agents" / "ct-research.agent.md").exists()
        assert (project / ".github" / "agents" / "ct-implement.agent.md").exists()
        assert (project / ".github" / "agents" / "ct-verify.agent.md").exists()
        assert (project / ".github" / "agents" / "ct-orchestrator.agent.md").exists()

    def test_no_overwrite_without_force(self, tmp_path: Path) -> None:
        """Test that existing files are not overwritten without --force."""
        project = self._setup_project(tmp_path, "python")
        # Create a file first
        (project / "CLAUDE.md").write_text("original content")
        (project / ".github").mkdir(parents=True, exist_ok=True)
        (project / ".github" / "copilot-instructions.md").write_text("original")

        results = generate_ai_integrations(project, force=False)
        created_names = {r.path.name for r in results}
        # CLAUDE.md and copilot-instructions.md should NOT be in results
        assert "CLAUDE.md" not in created_names
        assert "copilot-instructions.md" not in created_names
        # Original content should remain
        assert (project / "CLAUDE.md").read_text() == "original content"

    def test_overwrite_with_force(self, tmp_path: Path) -> None:
        """Test that files ARE overwritten with --force."""
        project = self._setup_project(tmp_path, "python")
        (project / "CLAUDE.md").write_text("original content")

        results = generate_ai_integrations(project, force=True)
        assert any(r.path.name == "CLAUDE.md" for r in results)
        assert (project / "CLAUDE.md").read_text() != "original content"

    def test_python_project_detection(self, tmp_path: Path) -> None:
        project = self._setup_project(tmp_path, "python")
        info = detect_project(project)
        assert "Python" in info.detected_languages
        assert info.test_command is not None

    def test_node_project_detection(self, tmp_path: Path) -> None:
        project = self._setup_project(tmp_path, "node")
        info = detect_project(project)
        assert any(lang in info.detected_languages
                   for lang in ["TypeScript", "JavaScript"])

    def test_go_project_detection(self, tmp_path: Path) -> None:
        project = self._setup_project(tmp_path, "go")
        info = detect_project(project)
        assert "Go" in info.detected_languages


# ---------------------------------------------------------------------------
# T10: MCP tools block
# ---------------------------------------------------------------------------

class TestMCPToolsBlock:
    """Test MCP tools reference block."""

    def test_includes_all_tools(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_mcp_tools_block(python_info, python_ctx)
        assert "search_matrix" in block
        assert "get_section" in block
        assert "get_context_for_file" in block
        assert "get_skills" in block
        assert "get_cache_stats" in block

    def test_section_count_in_output(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_mcp_tools_block(python_info, python_ctx)
        assert str(python_ctx.section_count) in block

    def test_correct_cache_path(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_mcp_tools_block(python_info, python_ctx)
        assert f".codetrellis/cache/{python_ctx.project_name}" in block

    def test_uses_actual_sections(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_mcp_tools_block(python_info, python_ctx)
        assert "PYTHON_TYPES" in block


# ---------------------------------------------------------------------------
# T11: Architecture block
# ---------------------------------------------------------------------------

class TestArchitectureBlock:
    """Test architecture / project structure block."""

    def test_parses_dir_format(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_architecture_block(python_info, python_ctx)
        assert "mylib/" in block
        assert "50 files" in block
        assert "scripts/" in block

    def test_includes_data_flow_pattern(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_architecture_block(python_info, python_ctx)
        assert "Request-Response" in block

    def test_empty_without_ctx(self, python_info: ProjectInfo) -> None:
        block = _build_architecture_block(python_info, None)
        assert block == ""


# ---------------------------------------------------------------------------
# T12: Known pitfalls
# ---------------------------------------------------------------------------

class TestKnownPitfalls:
    """Test known pitfalls block."""

    def test_cache_path_pitfall(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_known_pitfalls_block(python_info, python_ctx)
        assert ".codetrellis/cache/" in block

    def test_python_init_pitfall(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        """Python projects with pyproject.toml should warn about __init__.py."""
        block = _build_known_pitfalls_block(python_info, python_ctx)
        assert "__init__.py" in block

    def test_contributing_steps_pitfall(
        self, python_info: ProjectInfo, python_ctx: MatrixContext,
    ) -> None:
        block = _build_known_pitfalls_block(python_info, python_ctx)
        assert "coordinated" in block

    def test_no_python_pitfalls_for_go(
        self, go_info: ProjectInfo, go_ctx: MatrixContext,
    ) -> None:
        block = _build_known_pitfalls_block(go_info, go_ctx)
        assert "__init__.py" not in block
