"""
CodeTrellis Git Context Extractor
==================================

Extracts git metadata for the scanned project:
  - Recent commit log (last N commits, configurable)
  - Working-tree diff stats (staged + unstaged)
  - Per-file change frequency from git log

This data feeds into:
  1. A new [GIT_CONTEXT] section in the compressed matrix
  2. Sort-by-change-frequency ordering in IMPLEMENTATION_LOGIC
  3. Dependency-graph JIT boosting (files that change together)

Version: 1.0.0
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class GitContext:
    """Aggregated git metadata for a project."""
    recent_commits: List[Dict[str, str]] = field(default_factory=list)
    diff_stat: str = ""
    file_change_counts: Dict[str, int] = field(default_factory=dict)
    active_branch: str = ""
    is_git_repo: bool = False


class GitContextExtractor:
    """Extracts git metadata from a project root."""

    def __init__(self, max_commits: int = 15, max_frequency_commits: int = 200):
        self._max_commits = max_commits
        self._max_freq_commits = max_frequency_commits

    def extract(self, root_path: str) -> GitContext:
        """
        Extract git context from the project at *root_path*.

        Returns a GitContext even when the directory is not a git repo
        (all fields will be empty / default).
        """
        root = Path(root_path).resolve()
        ctx = GitContext()

        if not self._is_git_repo(root):
            return ctx

        ctx.is_git_repo = True
        ctx.active_branch = self._get_branch(root)
        ctx.recent_commits = self._get_recent_commits(root)
        ctx.diff_stat = self._get_diff_stat(root)
        ctx.file_change_counts = self._get_file_change_frequency(root)
        return ctx

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run(self, args: List[str], cwd: Path) -> Optional[str]:
        """Run a git command, return stdout or None on failure."""
        try:
            result = subprocess.run(
                args,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def _is_git_repo(self, root: Path) -> bool:
        return self._run(["git", "rev-parse", "--is-inside-work-tree"], root) == "true"

    def _get_branch(self, root: Path) -> str:
        return self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root) or ""

    def _get_recent_commits(self, root: Path) -> List[Dict[str, str]]:
        """Return list of {hash, author, date, subject}."""
        fmt = "%H%x00%an%x00%aI%x00%s"
        out = self._run(
            ["git", "log", f"-{self._max_commits}", f"--pretty=format:{fmt}"],
            root,
        )
        if not out:
            return []
        commits = []
        for line in out.splitlines():
            parts = line.split("\x00")
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0][:8],
                    "author": parts[1],
                    "date": parts[2],
                    "subject": parts[3],
                })
        return commits

    def _get_diff_stat(self, root: Path) -> str:
        """Return combined staged + unstaged diff stat."""
        out = self._run(["git", "diff", "--stat", "HEAD"], root)
        return out or ""

    def _get_file_change_frequency(self, root: Path) -> Dict[str, int]:
        """Count how often each file appears in the last N commits."""
        out = self._run(
            ["git", "log", f"-{self._max_freq_commits}", "--pretty=format:", "--name-only"],
            root,
        )
        if not out:
            return {}
        counts: Dict[str, int] = {}
        for line in out.splitlines():
            line = line.strip()
            if line:
                counts[line] = counts.get(line, 0) + 1
        return counts
