"""Tests for incremental build support in MatrixBuilder.

Verifies:
- BuildConfig.changed_files wiring
- ProjectScanner.scan_files_only processes only given files
- Full scan fallback works when cache is missing
- _changed_files_hint is passed from builder to scanner
"""

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from codetrellis.builder import MatrixBuilder, BuildConfig


# ─── Helpers ───

def _make_project(tmp_path: Path, files: dict) -> Path:
    """Create a minimal project with the given files.

    Args:
        tmp_path: pytest tmp_path fixture
        files: Dict of relative_path → content

    Returns:
        project root Path
    """
    root = tmp_path / "test_project"
    root.mkdir()
    for rel_path, content in files.items():
        fp = root / rel_path
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
    return root


# ─── Tests ───

class TestBuildConfigChangedFiles:
    """Test that BuildConfig.changed_files is properly wired."""

    def test_changed_files_default_none(self):
        config = BuildConfig()
        assert config.changed_files is None

    def test_changed_files_set(self):
        config = BuildConfig(
            incremental=True,
            changed_files=["/path/to/a.ts", "/path/to/b.ts"],
        )
        assert config.changed_files == ["/path/to/a.ts", "/path/to/b.ts"]
        assert config.incremental is True


class TestScanFilesOnly:
    """Test ProjectScanner.scan_files_only processes only given files."""

    def test_scan_single_typescript_file(self, tmp_path):
        root = _make_project(tmp_path, {
            "src/user.controller.ts": """
import { Controller, Get } from '@nestjs/common';

@Controller('users')
export class UserController {
    @Get()
    findAll() { return []; }
}
""",
            "src/other.ts": "export class Other {}",
        })

        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        result = scanner.scan_files_only(str(root), [root / "src/user.controller.ts"])

        # Should have scanned exactly 1 file
        assert result.total_files == 1
        # The other file should NOT appear
        assert "src/other.ts" not in result.files

    def test_scan_missing_file_skipped(self, tmp_path):
        root = _make_project(tmp_path, {"a.ts": "export class A {}"})

        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        result = scanner.scan_files_only(str(root), [
            root / "a.ts",
            root / "does_not_exist.ts",
        ])

        assert result.total_files == 1

    def test_scan_python_file(self, tmp_path):
        root = _make_project(tmp_path, {
            "models.py": """
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
""",
        })

        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        result = scanner.scan_files_only(str(root), [root / "models.py"])

        assert result.total_files == 1


class TestIncrementalBuildIntegration:
    """Integration test: full build → modify file → incremental build.

    Since we always run a full scanner.scan() (to avoid lossy JSON→ProjectMatrix
    hydration), the 'incremental' flag now just sets _changed_files_hint on the
    scanner — a future per-file cache optimisation hook.  These tests verify the
    build still succeeds and produces correct output.
    """

    def test_incremental_build_succeeds(self, tmp_path):
        """Verify incremental build with changed_files still produces full output."""
        root = _make_project(tmp_path, {
            "src/a.ts": "export class A { value = 1; }",
            "src/b.ts": "export class B { value = 2; }",
        })

        builder = MatrixBuilder(str(root))

        # First: full build to create cache
        result1 = builder.build(config=BuildConfig(incremental=False))
        assert result1.success

        # Verify matrix.json was written
        from codetrellis import __version__ as VERSION
        cache_dir = root / ".codetrellis" / "cache" / VERSION / root.name
        assert (cache_dir / "matrix.json").exists()
        assert (cache_dir / "matrix.prompt").exists()

        # Now modify file a.ts
        (root / "src/a.ts").write_text("export class A { value = 42; modified = true; }")

        # Second: incremental build with changed_files
        result2 = builder.build(config=BuildConfig(
            incremental=True,
            changed_files=[str(root / "src/a.ts")],
        ))

        assert result2.success
        # matrix.prompt should still exist and not be empty
        prompt = (cache_dir / "matrix.prompt").read_text()
        assert len(prompt) > 100  # Not a tiny/empty prompt

    def test_incremental_build_after_file_deletion(self, tmp_path):
        """Verify build succeeds even when files are deleted between runs."""
        root = _make_project(tmp_path, {
            "src/a.ts": "export class A {}",
            "src/b.ts": "export class B {}",
        })

        builder = MatrixBuilder(str(root))

        # First build
        result1 = builder.build(config=BuildConfig(incremental=False))
        assert result1.success

        # Delete a file
        (root / "src/b.ts").unlink()

        # Incremental build — full scan will naturally exclude the deleted file
        result2 = builder.build(config=BuildConfig(
            incremental=True,
            changed_files=[str(root / "src/a.ts")],
        ))

        assert result2.success

    def test_no_cache_falls_back_to_full(self, tmp_path):
        """Verify incremental falls back when no cached matrix exists."""
        root = _make_project(tmp_path, {
            "src/a.ts": "export class A {}",
        })

        builder = MatrixBuilder(str(root))

        # No prior build — no cache
        result = builder.build(config=BuildConfig(
            incremental=True,
            changed_files=[str(root / "src/a.ts")],
        ))

        # Should still succeed (full scan fallback)
        assert result.success


class TestChangedFilesHint:
    """Test that _changed_files_hint is correctly passed to the scanner."""

    def test_hint_set_when_incremental(self, tmp_path):
        """Builder should set scanner._changed_files_hint for incremental builds."""
        root = _make_project(tmp_path, {
            "src/a.ts": "export class A {}",
        })

        captured_hints = []

        from codetrellis.scanner import ProjectScanner
        original_scan = ProjectScanner.scan

        def spy_scan(self_scanner, root_path):
            captured_hints.append(getattr(self_scanner, '_changed_files_hint', None))
            return original_scan(self_scanner, root_path)

        with patch.object(ProjectScanner, 'scan', spy_scan):
            builder = MatrixBuilder(str(root))
            builder.build(config=BuildConfig(
                incremental=True,
                changed_files=[str(root / "src/a.ts")],
            ))

        assert len(captured_hints) == 1
        hint = captured_hints[0]
        assert hint is not None
        assert str(Path(root / "src/a.ts").resolve()) in hint

    def test_hint_none_when_not_incremental(self, tmp_path):
        """Builder should NOT set _changed_files_hint for full builds."""
        root = _make_project(tmp_path, {
            "src/a.ts": "export class A {}",
        })

        captured_hints = []

        from codetrellis.scanner import ProjectScanner
        original_scan = ProjectScanner.scan

        def spy_scan(self_scanner, root_path):
            captured_hints.append(getattr(self_scanner, '_changed_files_hint', None))
            return original_scan(self_scanner, root_path)

        with patch.object(ProjectScanner, 'scan', spy_scan):
            builder = MatrixBuilder(str(root))
            builder.build(config=BuildConfig(incremental=False))

        assert len(captured_hints) == 1
        hint = captured_hints[0]
        # Should be None (default) since incremental is False
        assert hint is None
