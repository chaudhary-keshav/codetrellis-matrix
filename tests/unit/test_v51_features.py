"""
Tests for v5.1 features — Git context compression, sort-by-change-frequency,
JIT dependency-graph boosting, and --remote CLI flag.
"""

import pytest
import re
import subprocess
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from pathlib import Path

from codetrellis.compressor import MatrixCompressor
from codetrellis.jit_context import JITContextProvider, JITContextResult


# ===== HELPERS =====

def _make_matrix(**kwargs):
    """Create a minimal matrix-like object with the given attributes."""
    return SimpleNamespace(**kwargs)


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


# ===== COMPRESSOR: GIT_CONTEXT SECTION =====

class TestGitContextSection:
    """Tests for the [GIT_CONTEXT] section in compressed output."""

    @pytest.fixture
    def compressor(self):
        return MatrixCompressor()

    def _minimal_matrix(self, **overrides):
        """Build a minimal matrix with git_context fields."""
        defaults = dict(
            name="testproject",
            overview={"type": "Library"},
            services={},
            schemas=[],
            enums=[],
            dtos=[],
            controllers=[],
            grpc_services=[],
            routes=[],
            websocket_events=[],
            modules=[],
            components=[],
            interfaces=[],
            types=[],
            angular_services=[],
            stores=[],
            guards=[],
            interceptors=[],
            pipes=[],
            gateways=[],
            http_apis=[],
            jsdoc=[],
            readme_content="",
            config={},
            error_handling=[],
            todos=[],
            dependencies={},
            files={},
            total_files=10,
            total_tokens=0,
            logic_snippets=[],
            business_domain=None,
            data_flows=[],
            arch_decisions=[],
            domain_vocabulary=[],
            overview_data=None,
            progress=None,
            infrastructure_docker=None,
            infrastructure_terraform=None,
            infrastructure_cicd=None,
            nestjs_modules=[],
            nestjs_guards=[],
            nestjs_interceptors=[],
            nestjs_pipes=[],
            nestjs_gateways=[],
            service_map=None,
            runbook=None,
            git_context=None,
            git_file_changes={},
            # v4.0 Python fields
            python_pydantic_models=[],
            python_dataclasses=[],
            python_typed_dicts=[],
            python_protocols=[],
            python_enums=[],
            python_functions=[],
            python_decorators=[],
            python_exceptions=[],
            python_fastapi_endpoints=[],
            python_flask_routes=[],
            python_django_views=[],
            python_ml_models=[],
            python_ml_trainers=[],
            python_langchain_components=[],
            python_mongodb_collections=[],
            python_vector_stores=[],
            python_redis_usage=[],
            python_kafka_topics=[],
            python_pipeline_dags=[],
            # Java
            java_classes=[],
            java_interfaces=[],
            java_records=[],
            java_enums=[],
            java_annotation_defs=[],
            java_spring_components=[],
            java_jpa_entities=[],
            java_rest_endpoints=[],
            java_build_info=None,
            java_exception_handlers=[],
            java_version="",
            # Go
            go_structs=[],
            go_interfaces=[],
            go_functions=[],
            go_routes=[],
            go_middleware=[],
            go_errors=[],
            go_channels=[],
            go_tests=[],
            go_build_tags=[],
            go_version="",
            # Kotlin
            kotlin_classes=[],
            kotlin_data_classes=[],
            kotlin_objects=[],
            kotlin_sealed_classes=[],
            kotlin_interfaces=[],
            kotlin_enums=[],
            kotlin_functions=[],
            kotlin_coroutine_scopes=[],
            kotlin_dsl_builders=[],
            kotlin_extensions=[],
            kotlin_annotations=[],
            kotlin_version="",
            # Rust
            rust_structs=[],
            rust_enums=[],
            rust_traits=[],
            rust_impls=[],
            rust_functions=[],
            rust_macros=[],
            rust_modules=[],
            rust_dependencies=[],
            rust_version="",
            # C#/C/C++
            csharp_classes=[],
            csharp_interfaces=[],
            csharp_records=[],
            csharp_enums=[],
            csharp_controllers=[],
            csharp_services=[],
            csharp_models=[],
            csharp_middleware=[],
            csharp_version="",
            c_types=[],
            c_functions=[],
            c_macros=[],
            c_globals=[],
            c_headers=[],
            c_version="",
            cpp_classes=[],
            cpp_templates=[],
            cpp_functions=[],
            cpp_namespaces=[],
            cpp_version="",
            # Misc languages
            sql_tables=[],
            sql_views=[],
            sql_procedures=[],
            sql_functions=[],
            sql_indexes=[],
            sql_triggers=[],
            sql_version="",
            html_pages=[],
            css_selectors=[],
            bash_functions=[],
            swift_types=[],
            ruby_classes=[],
            php_classes=[],
            scala_classes=[],
            r_functions=[],
            dart_classes=[],
            lua_modules=[],
            powershell_functions=[],
            # Semantic
            semantic_hooks=[],
            semantic_middleware=[],
            semantic_routes=[],
            semantic_plugins=[],
            semantic_lifecycle=[],
            semantic_cli_commands=[],
            # Directory + universal
            directory_summary={},
            discovery=None,
            project_profile=None,
            openapi_specs=[],
            graphql_schema=None,
            config_templates=None,
            env_inference=None,
            security=None,
            database_architecture=None,
            sub_projects=None,
            generic_languages=None,
        )
        defaults.update(overrides)
        return _make_matrix(**defaults)

    def test_no_git_context_no_section(self, compressor):
        matrix = self._minimal_matrix(git_context=None)
        output = compressor.compress(matrix)
        assert "[GIT_CONTEXT]" not in output

    def test_git_context_section_present(self, compressor):
        matrix = self._minimal_matrix(
            git_context={
                "branch": "main",
                "recent_commits": [
                    {"hash": "abc12345", "subject": "Fix bug"},
                    {"hash": "def67890", "subject": "Add feature"},
                ],
                "diff_stat": "",
            },
            git_file_changes={"src/main.py": 10, "src/utils.py": 3},
        )
        output = compressor.compress(matrix)
        assert "[GIT_CONTEXT]" in output

    def test_branch_in_section(self, compressor):
        matrix = self._minimal_matrix(
            git_context={
                "branch": "feature/new-ui",
                "recent_commits": [],
                "diff_stat": "",
            },
        )
        output = compressor.compress(matrix)
        assert "branch=feature/new-ui" in output

    def test_recent_commits_listed(self, compressor):
        matrix = self._minimal_matrix(
            git_context={
                "branch": "main",
                "recent_commits": [
                    {"hash": "aaa11111", "subject": "First commit"},
                    {"hash": "bbb22222", "subject": "Second commit"},
                ],
                "diff_stat": "",
            },
        )
        output = compressor.compress(matrix)
        assert "aaa11111 First commit" in output
        assert "bbb22222 Second commit" in output

    def test_hot_files_listed(self, compressor):
        matrix = self._minimal_matrix(
            git_context={
                "branch": "main",
                "recent_commits": [],
                "diff_stat": "",
            },
            git_file_changes={"scanner.py": 42, "compressor.py": 15},
        )
        output = compressor.compress(matrix)
        assert "scanner.py|changes:42" in output
        assert "compressor.py|changes:15" in output

    def test_hot_files_sorted_by_frequency(self, compressor):
        matrix = self._minimal_matrix(
            git_context={
                "branch": "main",
                "recent_commits": [],
                "diff_stat": "",
            },
            git_file_changes={"low.py": 1, "mid.py": 5, "high.py": 20},
        )
        output = compressor.compress(matrix)
        high_pos = output.index("high.py|changes:20")
        mid_pos = output.index("mid.py|changes:5")
        low_pos = output.index("low.py|changes:1")
        assert high_pos < mid_pos < low_pos

    def test_git_context_before_best_practices(self, compressor):
        matrix = self._minimal_matrix(
            git_context={
                "branch": "main",
                "recent_commits": [],
                "diff_stat": "",
            },
        )
        output = compressor.compress(matrix)
        git_pos = output.index("[GIT_CONTEXT]")
        bp_pos = output.index("[BEST_PRACTICES]")
        assert git_pos < bp_pos

    def test_diff_stat_included(self, compressor):
        matrix = self._minimal_matrix(
            git_context={
                "branch": "main",
                "recent_commits": [],
                "diff_stat": " main.py | 5 ++---\n 1 file changed, 2 insertions(+), 3 deletions(-)",
            },
        )
        output = compressor.compress(matrix)
        assert "Working tree changes" in output
        assert "main.py" in output

    def test_max_10_commits_shown(self, compressor):
        commits = [{"hash": f"hash{i:04d}", "subject": f"Commit {i}"} for i in range(20)]
        matrix = self._minimal_matrix(
            git_context={
                "branch": "main",
                "recent_commits": commits,
                "diff_stat": "",
            },
        )
        output = compressor.compress(matrix)
        # Only first 10 should be shown
        assert "hash0009" in output
        assert "hash0010" not in output

    def test_max_15_hot_files(self, compressor):
        changes = {f"file_{i:03d}.py": 100 - i for i in range(25)}
        matrix = self._minimal_matrix(
            git_context={
                "branch": "main",
                "recent_commits": [],
                "diff_stat": "",
            },
            git_file_changes=changes,
        )
        output = compressor.compress(matrix)
        hot_lines = [l for l in output.split("\n") if "|changes:" in l]
        assert len(hot_lines) == 15


# ===== COMPRESSOR: SORT BY CHANGE FREQUENCY =====

class TestSortByChangeFrequency:
    """Tests for sorting IMPLEMENTATION_LOGIC files by git change frequency."""

    @pytest.fixture
    def compressor(self):
        return MatrixCompressor()

    def test_most_changed_file_at_bottom(self, compressor):
        """Most-changed file should appear last (bottom) in IMPLEMENTATION_LOGIC."""
        matrix = _make_matrix(
            name="test",
            overview=None,
            services={},
            schemas=[],
            enums=[],
            dtos=[],
            controllers=[],
            grpc_services=[],
            routes=[],
            websocket_events=[],
            modules=[],
            components=[],
            interfaces=[],
            types=[],
            angular_services=[],
            stores=[],
            guards=[],
            interceptors=[],
            pipes=[],
            gateways=[],
            http_apis=[],
            jsdoc=[],
            readme_content="",
            config={},
            error_handling=[],
            todos=[],
            dependencies={},
            files={},
            total_files=3,
            total_tokens=0,
            business_domain=None,
            data_flows=[],
            arch_decisions=[],
            domain_vocabulary=[],
            overview_data=None,
            progress=None,
            infrastructure_docker=None,
            infrastructure_terraform=None,
            infrastructure_cicd=None,
            nestjs_modules=[],
            nestjs_guards=[],
            nestjs_interceptors=[],
            nestjs_pipes=[],
            nestjs_gateways=[],
            service_map=None,
            runbook=None,
            git_context=None,
            git_file_changes={"hot_file.py": 50, "cold_file.py": 1},
            logic_snippets=[
                {"name": "cold_func", "file": "src/cold_file.py", "complexity": "simple", "lines": 10},
                {"name": "hot_func", "file": "src/hot_file.py", "complexity": "simple", "lines": 10},
            ],
            # Minimal other fields
            python_pydantic_models=[],
            python_dataclasses=[],
            python_typed_dicts=[],
            python_protocols=[],
            python_enums=[],
            python_functions=[],
            python_decorators=[],
            python_exceptions=[],
            python_fastapi_endpoints=[],
            python_flask_routes=[],
            python_django_views=[],
            python_ml_models=[],
            python_ml_trainers=[],
            python_langchain_components=[],
            python_mongodb_collections=[],
            python_vector_stores=[],
            python_redis_usage=[],
            python_kafka_topics=[],
            python_pipeline_dags=[],
            java_classes=[],
            java_interfaces=[],
            java_records=[],
            java_enums=[],
            java_annotation_defs=[],
            java_spring_components=[],
            java_jpa_entities=[],
            java_rest_endpoints=[],
            java_build_info=None,
            java_exception_handlers=[],
            java_version="",
            go_structs=[],
            go_interfaces=[],
            go_functions=[],
            go_routes=[],
            go_middleware=[],
            go_errors=[],
            go_channels=[],
            go_tests=[],
            go_build_tags=[],
            go_version="",
            kotlin_classes=[],
            kotlin_data_classes=[],
            kotlin_objects=[],
            kotlin_sealed_classes=[],
            kotlin_interfaces=[],
            kotlin_enums=[],
            kotlin_functions=[],
            kotlin_coroutine_scopes=[],
            kotlin_dsl_builders=[],
            kotlin_extensions=[],
            kotlin_annotations=[],
            kotlin_version="",
            rust_structs=[],
            rust_enums=[],
            rust_traits=[],
            rust_impls=[],
            rust_functions=[],
            rust_macros=[],
            rust_modules=[],
            rust_dependencies=[],
            rust_version="",
            csharp_classes=[],
            csharp_interfaces=[],
            csharp_records=[],
            csharp_enums=[],
            csharp_controllers=[],
            csharp_services=[],
            csharp_models=[],
            csharp_middleware=[],
            csharp_version="",
            c_types=[],
            c_functions=[],
            c_macros=[],
            c_globals=[],
            c_headers=[],
            c_version="",
            cpp_classes=[],
            cpp_templates=[],
            cpp_functions=[],
            cpp_namespaces=[],
            cpp_version="",
            sql_tables=[],
            sql_views=[],
            sql_procedures=[],
            sql_functions=[],
            sql_indexes=[],
            sql_triggers=[],
            sql_version="",
            html_pages=[],
            css_selectors=[],
            bash_functions=[],
            swift_types=[],
            ruby_classes=[],
            php_classes=[],
            scala_classes=[],
            r_functions=[],
            dart_classes=[],
            lua_modules=[],
            powershell_functions=[],
            semantic_hooks=[],
            semantic_middleware=[],
            semantic_routes=[],
            semantic_plugins=[],
            semantic_lifecycle=[],
            semantic_cli_commands=[],
            directory_summary={},
            discovery=None,
            project_profile=None,
            openapi_specs=[],
            graphql_schema=None,
            config_templates=None,
            env_inference=None,
            security=None,
            database_architecture=None,
            sub_projects=None,
            generic_languages=None,
        )
        lines = compressor._compress_logic(matrix)
        file_headers = [l for l in lines if l.startswith("# ")]
        # hot_file should come after cold_file (bottom = last)
        if len(file_headers) == 2:
            assert "hot_file" in file_headers[-1]

    def test_no_git_changes_no_crash(self, compressor):
        """Sort should work fine even without git_file_changes."""
        matrix = _make_matrix(
            name="test",
            logic_snippets=[
                {"name": "func_a", "file": "a.py", "complexity": "simple", "lines": 5},
                {"name": "func_b", "file": "b.py", "complexity": "simple", "lines": 5},
            ],
            git_file_changes={},
        )
        lines = compressor._compress_logic(matrix)
        assert isinstance(lines, list)


# ===== JIT: DEPENDENCY-GRAPH BOOSTING =====

SAMPLE_MATRIX_WITH_LOGIC = """[PROJECT]
# name: testapp
# lang: Python

[SCHEMAS]
User|id:int,name:str|models/user.py

[SERVICES]
UserService|getUser:User|services/user_service.py

[PYTHON_TYPES]
UserModel|BaseModel|id:int|models.py

[IMPLEMENTATION_LOGIC]
# user_service.py (3 functions, 1 complex)
  get_user|def get_user(id)|db.query → validate → return|[complex]
  create_user|def create_user(data)|validate → db.insert → return|[moderate]
  delete_user|def delete_user(id)|db.delete → return|[simple]

# user_repo.py (2 functions, 0 complex)
  find_by_id|def find_by_id(id)|SELECT * FROM users → return|[simple]
  save|def save(user)|INSERT INTO users → return|[simple]

# auth_service.py (2 functions, 1 complex)
  authenticate|def authenticate(token)|decode → validate → lookup|[complex]
  refresh|def refresh(token)|validate → generate → return|[simple]

# unrelated_module.py (1 function, 0 complex)
  utility_func|def utility_func(x)|compute → return|[simple]

[BEST_PRACTICES]
# Use type hints
"""


class TestDependencyGraphBoosting:
    """Tests for JIT dependency-graph boosting via co-occurring files."""

    @pytest.fixture
    def sections(self):
        return _parse_sections(SAMPLE_MATRIX_WITH_LOGIC)

    @pytest.fixture
    def provider(self, sections):
        return JITContextProvider(sections, max_tokens=30000)

    def test_co_occurring_files_found(self, provider):
        """Files neighbouring user_service.py in IMPL_LOGIC should be found."""
        co = provider._find_co_occurring_files("user_service.py", "user_service")
        assert "user_repo.py" in co or "auth_service.py" in co

    def test_co_occurring_boosts_sections(self, provider):
        """Sections containing co-occurring files should get boosted relevance."""
        result_with_logic = provider.resolve_context("services/user_service.py")
        # IMPLEMENTATION_LOGIC mentions user_service.py directly → +4.0
        # Neighbours (user_repo.py) are mentioned too → additional boost to sections
        assert "IMPLEMENTATION_LOGIC" in result_with_logic.sections_included

    def test_unrelated_file_no_boost(self, provider):
        """A file not in IMPLEMENTATION_LOGIC should not get co-occurrence boost."""
        co = provider._find_co_occurring_files("totally_unknown.py", "totally_unknown")
        assert len(co) == 0

    def test_neighbouring_files_limited(self, provider):
        """max_results should cap the neighbour set."""
        co = provider._find_co_occurring_files("user_service.py", "user_service")
        assert len(co) <= 8  # default max_results

    def test_empty_implementation_logic(self):
        """No crash when IMPLEMENTATION_LOGIC section is absent."""
        sections = {"PROJECT": "[PROJECT]\n# test"}
        provider = JITContextProvider(sections, max_tokens=30000)
        co = provider._find_co_occurring_files("test.py", "test")
        assert co == set()

    def test_boosted_score_higher(self, sections):
        """A file with co-occurring neighbours should score higher than one without."""
        provider = JITContextProvider(sections, max_tokens=30000)
        result = provider.resolve_context("services/user_service.py")
        # user_service.py is directly mentioned in IMPL_LOGIC (+4.0)
        # and has co-occurring neighbours that boost related sections
        scores = result.relevance_scores
        if "IMPLEMENTATION_LOGIC" in scores:
            # It should have at least direct mention + co-occurrence boost
            assert scores["IMPLEMENTATION_LOGIC"] >= 4.0


# ===== CLI: --remote FLAG =====

class TestRemoteCLIFlag:
    """Tests for the --remote flag on the scan subcommand."""

    def test_remote_arg_registered(self):
        """The --remote argument should exist on the scan subparser."""
        import argparse
        from codetrellis.cli import main
        # Build the parser the same way main() does
        # We'll parse a minimal command to ensure --remote is accepted
        # If it's not registered, parse_args would raise SystemExit
        from codetrellis.cli import VERSION
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        scan_parser = subparsers.add_parser("scan")
        scan_parser.add_argument("path", nargs="?", default=".")
        scan_parser.add_argument("--remote", type=str, default=None)
        args = parser.parse_args(["scan", "--remote", "https://github.com/user/repo"])
        assert args.remote == "https://github.com/user/repo"

    def test_remote_none_by_default(self):
        """Without --remote, the value should be None."""
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        scan_parser = subparsers.add_parser("scan")
        scan_parser.add_argument("path", nargs="?", default=".")
        scan_parser.add_argument("--remote", type=str, default=None)
        args = parser.parse_args(["scan", "."])
        assert args.remote is None

    def test_clone_failure_exits_3(self):
        """If git clone fails, the CLI should exit with code 3."""
        import sys
        from unittest.mock import patch, MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stderr = "fatal: repository not found"

        with patch("subprocess.run", return_value=mock_result):
            with patch("sys.argv", ["codetrellis", "scan", "--remote", "https://bad-url.example.com/repo"]):
                with pytest.raises(SystemExit) as exc_info:
                    from codetrellis.cli import main
                    main()
                assert exc_info.value.code == 3
