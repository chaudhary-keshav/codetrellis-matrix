"""
Tests for GitContextExtractor — Git metadata extraction (v5.1).

Validates git repo detection, branch extraction, recent commit retrieval,
diff stat extraction, file change frequency counting, and non-git-repo fallback.
"""

import os
import subprocess
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from codetrellis.git_context import GitContextExtractor, GitContext


# ===== FIXTURES =====

@pytest.fixture
def extractor():
    return GitContextExtractor(max_commits=5, max_frequency_commits=50)


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repo with some commits."""
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(tmp_path), capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(tmp_path), capture_output=True,
    )
    # Create initial commit
    f1 = tmp_path / "main.py"
    f1.write_text("# main")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=str(tmp_path), capture_output=True,
    )
    # Second commit touching main.py
    f1.write_text("# main\nprint('hello')")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add print"],
        cwd=str(tmp_path), capture_output=True,
    )
    # Third commit adding a new file
    f2 = tmp_path / "utils.py"
    f2.write_text("# utils")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add utils"],
        cwd=str(tmp_path), capture_output=True,
    )
    return tmp_path


# ===== GITCONTEXT DATACLASS =====

class TestGitContextDataclass:
    """Tests for GitContext dataclass defaults."""

    def test_default_values(self):
        ctx = GitContext()
        assert ctx.recent_commits == []
        assert ctx.diff_stat == ""
        assert ctx.file_change_counts == {}
        assert ctx.active_branch == ""
        assert ctx.is_git_repo is False

    def test_custom_values(self):
        ctx = GitContext(
            is_git_repo=True,
            active_branch="main",
            recent_commits=[{"hash": "abc", "subject": "test"}],
        )
        assert ctx.is_git_repo is True
        assert ctx.active_branch == "main"
        assert len(ctx.recent_commits) == 1


# ===== NON-GIT REPO FALLBACK =====

class TestNonGitRepo:
    """Tests for non-git directories."""

    def test_non_git_dir_returns_empty_context(self, extractor, tmp_path):
        ctx = extractor.extract(str(tmp_path))
        assert ctx.is_git_repo is False
        assert ctx.active_branch == ""
        assert ctx.recent_commits == []
        assert ctx.file_change_counts == {}

    def test_nonexistent_dir(self, extractor):
        ctx = extractor.extract("/nonexistent/path/aabbcc")
        assert ctx.is_git_repo is False


# ===== GIT REPO EXTRACTION =====

class TestGitRepoExtraction:
    """Tests for extracting context from a real git repo."""

    def test_is_git_repo(self, extractor, git_repo):
        ctx = extractor.extract(str(git_repo))
        assert ctx.is_git_repo is True

    def test_active_branch(self, extractor, git_repo):
        ctx = extractor.extract(str(git_repo))
        # Branch should be master or main depending on git config
        assert ctx.active_branch in ("master", "main")

    def test_recent_commits(self, extractor, git_repo):
        ctx = extractor.extract(str(git_repo))
        assert len(ctx.recent_commits) == 3
        # Most recent commit first
        assert ctx.recent_commits[0]["subject"] == "Add utils"
        assert ctx.recent_commits[1]["subject"] == "Add print"
        assert ctx.recent_commits[2]["subject"] == "Initial commit"

    def test_commit_has_required_fields(self, extractor, git_repo):
        ctx = extractor.extract(str(git_repo))
        for commit in ctx.recent_commits:
            assert "hash" in commit
            assert "author" in commit
            assert "date" in commit
            assert "subject" in commit
            assert len(commit["hash"]) == 8  # abbreviated

    def test_file_change_frequency(self, extractor, git_repo):
        ctx = extractor.extract(str(git_repo))
        assert "main.py" in ctx.file_change_counts
        assert ctx.file_change_counts["main.py"] == 2  # touched in 2 commits
        assert "utils.py" in ctx.file_change_counts
        assert ctx.file_change_counts["utils.py"] == 1  # touched in 1 commit

    def test_diff_stat_empty_for_clean_repo(self, extractor, git_repo):
        ctx = extractor.extract(str(git_repo))
        # No uncommitted changes, diff stat should be empty
        assert ctx.diff_stat == ""

    def test_diff_stat_with_uncommitted_changes(self, extractor, git_repo):
        # Make an uncommitted change
        (git_repo / "main.py").write_text("# modified\nimport os\n")
        ctx = extractor.extract(str(git_repo))
        assert "main.py" in ctx.diff_stat

    def test_max_commits_respected(self, git_repo):
        ext = GitContextExtractor(max_commits=2)
        ctx = ext.extract(str(git_repo))
        assert len(ctx.recent_commits) == 2


# ===== TIMEOUT / ERROR HANDLING =====

class TestErrorHandling:
    """Tests for error handling in git commands."""

    def test_git_not_installed(self, extractor, tmp_path):
        with patch("codetrellis.git_context.subprocess.run", side_effect=FileNotFoundError):
            ctx = extractor.extract(str(tmp_path))
            assert ctx.is_git_repo is False

    def test_git_timeout(self, extractor, tmp_path):
        with patch(
            "codetrellis.git_context.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="git", timeout=30),
        ):
            ctx = extractor.extract(str(tmp_path))
            assert ctx.is_git_repo is False


# ===== SCANNER INTEGRATION =====

class TestScannerIntegration:
    """Tests for git extraction integrated into ProjectMatrix via scanner."""

    def test_project_matrix_has_git_fields(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name="test", root_path="/tmp")
        assert hasattr(matrix, "git_context")
        assert hasattr(matrix, "git_file_changes")
        assert matrix.git_context is None
        assert matrix.git_file_changes == {}

    def test_project_matrix_git_context_assignable(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name="test", root_path="/tmp")
        matrix.git_context = {
            "branch": "main",
            "recent_commits": [{"hash": "abc12345", "subject": "test"}],
            "diff_stat": "",
        }
        matrix.git_file_changes = {"main.py": 5, "utils.py": 2}
        assert matrix.git_context["branch"] == "main"
        assert matrix.git_file_changes["main.py"] == 5
