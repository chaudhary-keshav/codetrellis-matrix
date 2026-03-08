"""
Tests for CodeTrellis Auto-Compilation Pipeline (PART B)
======================================================

Tests cover:
- Phase 0: Stabilization (version sync, deterministic traversal, timestamps, clean)
- Phase 1: Compiler Core (CacheManager, LockfileManager, InputHashCalculator)
- Phase 2: Incremental/Watch (DiffEngine, incremental builds)
- Phase 3-4: CI/CD & Hardening (deterministic builds, quality gates, verify)

Per D3 Quality Gate:
- All tests use tmp_path fixture (no hardcoded paths)
- No external network dependencies
- Target ≥80% line coverage on new modules

Author: Keshav Chaudhary
Created: 20 February 2026
"""

import json
import os
import sys
import hashlib
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from codetrellis.cache import (
    InputHashCalculator,
    FileManifestEntry,
    Lockfile,
    LockfileManager,
    CacheManager,
    CacheHitResult,
    DiffEngine,
    DiffResult,
)
from codetrellis.builder import (
    MatrixBuilder,
    BuildConfig,
    BuildLogger,
)
from codetrellis.interfaces import (
    ExtractorManifest,
    BuildEvent,
    BuildResult,
    OutputTier,
    IExtractor,
)


# =============================================================================
# Phase 0: Stabilization Tests
# =============================================================================

class TestVersionSync:
    """Verify __init__.py and pyproject.toml have the same version."""

    def test_version_matches_pyproject(self):
        """B4 Phase 0: Version mismatch fix."""
        from codetrellis import __version__

        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            for line in content.split("\n"):
                if line.strip().startswith("version") and "=" in line:
                    pyproject_version = line.split("=")[1].strip().strip('"')
                    assert __version__ == pyproject_version, (
                        f"Version mismatch: __init__.py={__version__}, "
                        f"pyproject.toml={pyproject_version}"
                    )
                    break


class TestBuildTimestamp:
    """Verify CODETRELLIS_BUILD_TIMESTAMP support."""

    def test_env_var_override(self):
        """B4 Phase 0: CODETRELLIS_BUILD_TIMESTAMP env var."""
        from codetrellis.scanner import _get_build_datetime

        with patch.dict(os.environ, {"CODETRELLIS_BUILD_TIMESTAMP": "2026-01-01T00:00:00"}):
            dt = _get_build_datetime()
            assert dt.year == 2026
            assert dt.month == 1
            assert dt.day == 1

    def test_default_when_no_env(self):
        """Falls back to datetime.now() when env var is unset."""
        from codetrellis.scanner import _get_build_datetime

        with patch.dict(os.environ, {}, clear=True):
            # Remove the var if set
            os.environ.pop("CODETRELLIS_BUILD_TIMESTAMP", None)
            dt = _get_build_datetime()
            assert dt.year >= 2026

    def test_cli_get_build_timestamp(self):
        """CLI helper respects the env var."""
        from codetrellis.cli import _get_build_timestamp

        with patch.dict(os.environ, {"CODETRELLIS_BUILD_TIMESTAMP": "2026-02-19T12:00:00"}):
            ts = _get_build_timestamp()
            assert ts == "2026-02-19T12:00:00"


class TestCleanCommand:
    """Test codetrellis clean functionality."""

    def test_clean_removes_cache(self, tmp_path):
        """B6: codetrellis clean removes cache directory."""
        from codetrellis.cli import clean_project

        # Create fake cache structure under tmp_path/.codetrellis
        ct_dir = tmp_path / ".codetrellis"
        cache_dir = ct_dir / "cache" / "4.16.0" / "test_project"
        cache_dir.mkdir(parents=True)
        (cache_dir / "matrix.prompt").write_text("test")
        (cache_dir / "matrix.json").write_text("{}")

        # clean_project calls get_codetrellis_dir(Path(path).resolve())
        # which returns project_root / ".codetrellis" — tmp_path already works
        exit_code = clean_project(str(tmp_path))

        assert exit_code == 0
        assert not (ct_dir / "cache").exists()

    def test_clean_specific_version(self, tmp_path):
        """C5: codetrellis clean --version removes specific version."""
        from codetrellis.cli import clean_project

        ct_dir = tmp_path / ".codetrellis"
        v1_dir = ct_dir / "cache" / "4.15.0" / "test_project"
        v2_dir = ct_dir / "cache" / "4.16.0" / "test_project"
        v1_dir.mkdir(parents=True)
        v2_dir.mkdir(parents=True)
        (v1_dir / "matrix.prompt").write_text("old")
        (v2_dir / "matrix.prompt").write_text("new")

        exit_code = clean_project(str(tmp_path), version="4.15.0")

        assert exit_code == 0
        assert not (ct_dir / "cache" / "4.15.0").exists()
        assert (ct_dir / "cache" / "4.16.0").exists()

    def test_clean_no_cache_returns_0(self, tmp_path):
        """Clean with no cache dir returns exit code 0."""
        from codetrellis.cli import clean_project

        ct_dir = tmp_path / ".codetrellis"
        ct_dir.mkdir()

        exit_code = clean_project(str(tmp_path))

        assert exit_code == 0

    def test_clean_no_codetrellis_returns_2(self, tmp_path):
        """Clean with no .codetrellis dir returns exit code 2."""
        from codetrellis.cli import clean_project

        # tmp_path has no .codetrellis directory
        exit_code = clean_project(str(tmp_path))

        assert exit_code == 2

    def test_clean_specific_version_not_found(self, tmp_path):
        """Clean specific version that doesn't exist returns exit code 2."""
        from codetrellis.cli import clean_project

        ct_dir = tmp_path / ".codetrellis"
        cache_dir = ct_dir / "cache" / "4.16.0" / "test_project"
        cache_dir.mkdir(parents=True)

        exit_code = clean_project(str(tmp_path), version="9.9.9")

        assert exit_code == 2


# =============================================================================
# Phase 1: InputHashCalculator Tests
# =============================================================================

class TestInputHashCalculator:
    """Test SHA-256 content hashing."""

    def test_hash_file(self, tmp_path):
        """C1.1: SHA-256, first 16 hex chars."""
        test_file = tmp_path / "test.py"
        test_file.write_text("hello world")

        result = InputHashCalculator.hash_file(str(test_file))

        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_file_deterministic(self, tmp_path):
        """C3: Same content → same hash."""
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text("same content")
        f2.write_text("same content")

        assert InputHashCalculator.hash_file(str(f1)) == InputHashCalculator.hash_file(str(f2))

    def test_hash_file_different_content(self, tmp_path):
        """Different content → different hash."""
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text("content A")
        f2.write_text("content B")

        assert InputHashCalculator.hash_file(str(f1)) != InputHashCalculator.hash_file(str(f2))

    def test_hash_string(self):
        """Hash a string deterministically."""
        h1 = InputHashCalculator.hash_string("hello")
        h2 = InputHashCalculator.hash_string("hello")
        h3 = InputHashCalculator.hash_string("world")

        assert h1 == h2
        assert h1 != h3
        assert len(h1) == 16

    def test_hash_config(self):
        """Hash a config dict deterministically with sorted keys."""
        config_a = {"tier": "logic", "deep": True, "parallel": False}
        config_b = {"parallel": False, "deep": True, "tier": "logic"}  # Same keys, different order

        assert InputHashCalculator.hash_config(config_a) == InputHashCalculator.hash_config(config_b)

    def test_hash_bytes(self):
        """Hash raw bytes."""
        h = InputHashCalculator.hash_bytes(b"binary data")
        assert len(h) == 16

    def test_hash_file_not_found(self, tmp_path):
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            InputHashCalculator.hash_file(str(tmp_path / "nonexistent.py"))


# =============================================================================
# Phase 1: LockfileManager Tests
# =============================================================================

class TestFileManifestEntry:
    """Test file manifest entry serialization."""

    def test_roundtrip(self):
        """Serialize and deserialize a FileManifestEntry."""
        entry = FileManifestEntry(
            file_path="codetrellis/cli.py",
            content_hash="abc123def456gh78",
            size_bytes=1024,
            last_modified="2026-02-20T10:00:00",
            extractors_run=["python_parser", "todo_extractor"],
        )

        d = entry.to_dict()
        restored = FileManifestEntry.from_dict(d)

        assert restored.file_path == entry.file_path
        assert restored.content_hash == entry.content_hash
        assert restored.size_bytes == entry.size_bytes
        assert restored.extractors_run == sorted(entry.extractors_run)


class TestLockfile:
    """Test lockfile serialization."""

    def test_roundtrip(self):
        """Serialize and deserialize a Lockfile."""
        lockfile = Lockfile(
            build_key="4.16.0:abc123",
            codetrellis_version="4.16.0",
            config_hash="abc123",
            cli_flags_hash="def456",
            generated_at="2026-02-20T10:00:00",
            total_files=42,
            file_manifest={
                "cli.py": FileManifestEntry("cli.py", "hash1"),
                "scanner.py": FileManifestEntry("scanner.py", "hash2"),
            },
            extractor_versions={"python_parser": "1.0"},
        )

        d = lockfile.to_dict()
        restored = Lockfile.from_dict(d)

        assert restored.build_key == lockfile.build_key
        assert restored.codetrellis_version == lockfile.codetrellis_version
        assert restored.total_files == 42
        assert len(restored.file_manifest) == 2

    def test_sorted_output(self):
        """JSON output has sorted keys for determinism."""
        lockfile = Lockfile(
            build_key="test",
            codetrellis_version="4.16.0",
            config_hash="cfg",
            file_manifest={
                "z_file.py": FileManifestEntry("z_file.py", "z_hash"),
                "a_file.py": FileManifestEntry("a_file.py", "a_hash"),
            },
        )

        d = lockfile.to_dict()
        keys = list(d["file_manifest"].keys())
        assert keys == sorted(keys), "File manifest keys must be sorted"


class TestLockfileManager:
    """Test lockfile read/write operations."""

    def test_write_and_read(self, tmp_path):
        """Write a lockfile and read it back."""
        mgr = LockfileManager(tmp_path)

        lockfile = Lockfile(
            build_key="4.16.0:abc",
            codetrellis_version="4.16.0",
            config_hash="abc",
            total_files=10,
        )

        mgr.write(lockfile)
        assert mgr.exists()

        restored = mgr.read()
        assert restored is not None
        assert restored.build_key == "4.16.0:abc"
        assert restored.total_files == 10

    def test_read_nonexistent(self, tmp_path):
        """Read returns None when lockfile doesn't exist."""
        mgr = LockfileManager(tmp_path)
        assert mgr.read() is None
        assert not mgr.exists()

    def test_read_corrupted(self, tmp_path):
        """Read returns None for corrupted lockfile."""
        mgr = LockfileManager(tmp_path)
        (tmp_path / "_lockfile.json").write_text("not valid json {{{")

        assert mgr.read() is None

    def test_delete(self, tmp_path):
        """Delete removes the lockfile."""
        mgr = LockfileManager(tmp_path)
        lockfile = Lockfile(build_key="x", codetrellis_version="4.16.0", config_hash="y")
        mgr.write(lockfile)
        assert mgr.exists()

        mgr.delete()
        assert not mgr.exists()

    def test_lockfile_json_sorted_keys(self, tmp_path):
        """C3: Lockfile JSON has sorted keys."""
        mgr = LockfileManager(tmp_path)
        lockfile = Lockfile(
            build_key="test",
            codetrellis_version="4.16.0",
            config_hash="abc",
        )
        mgr.write(lockfile)

        content = (tmp_path / "_lockfile.json").read_text()
        data = json.loads(content)
        keys = list(data.keys())
        assert keys == sorted(keys)


# =============================================================================
# Phase 1: CacheManager Tests
# =============================================================================

class TestCacheManager:
    """Test per-extractor result caching."""

    def test_miss_then_hit(self, tmp_path):
        """Cache miss, then store, then hit."""
        cache = CacheManager(tmp_path, "4.16.0")

        # Miss
        result = cache.get("python_parser", "abc123")
        assert not result.is_hit
        assert cache.misses == 1
        assert cache.hits == 0

        # Store
        cache.put("python_parser", "abc123", {"classes": ["Foo"]})

        # Hit
        result = cache.get("python_parser", "abc123")
        assert result.is_hit
        assert result.cached_data == {"classes": ["Foo"]}
        assert cache.hits == 1

    def test_version_mismatch_invalidates(self, tmp_path):
        """C5: Version change invalidates cache."""
        cache_v1 = CacheManager(tmp_path, "4.15.0")
        cache_v1.put("parser", "hash1", {"data": "old"})

        cache_v2 = CacheManager(tmp_path, "4.16.0")
        result = cache_v2.get("parser", "hash1")
        assert not result.is_hit  # Version mismatch

    def test_different_extractors_independent(self, tmp_path):
        """Different extractors have independent caches."""
        cache = CacheManager(tmp_path, "4.16.0")

        cache.put("parser_a", "hash1", {"a": 1})
        cache.put("parser_b", "hash1", {"b": 2})

        result_a = cache.get("parser_a", "hash1")
        result_b = cache.get("parser_b", "hash1")

        assert result_a.cached_data == {"a": 1}
        assert result_b.cached_data == {"b": 2}

    def test_invalidate_all(self, tmp_path):
        """Invalidate all caches."""
        cache = CacheManager(tmp_path, "4.16.0")
        cache.put("parser_a", "hash1", {"a": 1})
        cache.put("parser_b", "hash2", {"b": 2})

        count = cache.invalidate()
        assert count == 2

        assert not cache.get("parser_a", "hash1").is_hit
        assert not cache.get("parser_b", "hash2").is_hit

    def test_invalidate_specific(self, tmp_path):
        """Invalidate only one extractor's cache."""
        cache = CacheManager(tmp_path, "4.16.0")
        cache.put("parser_a", "hash1", {"a": 1})
        cache.put("parser_b", "hash2", {"b": 2})

        count = cache.invalidate("parser_a")
        assert count == 1

        assert not cache.get("parser_a", "hash1").is_hit
        assert cache.get("parser_b", "hash2").is_hit

    def test_get_stats(self, tmp_path):
        """Cache stats report hits, misses, and on-disk count."""
        cache = CacheManager(tmp_path, "4.16.0")
        cache.put("parser", "hash1", {"x": 1})
        cache.get("parser", "hash1")  # hit
        cache.get("parser", "hash2")  # miss

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["on_disk_entries"] == 1
        assert 0 < stats["hit_rate"] < 1

    def test_hit_rate_no_requests(self, tmp_path):
        """Hit rate is 0.0 with no requests."""
        cache = CacheManager(tmp_path, "4.16.0")
        assert cache.hit_rate == 0.0


# =============================================================================
# Phase 2: DiffEngine Tests
# =============================================================================

class TestDiffEngine:
    """Test file diff detection."""

    def test_first_build_all_added(self):
        """First build (no lockfile): all files are 'added'."""
        engine = DiffEngine()
        current = {"a.py": "hash_a", "b.py": "hash_b"}

        result = engine.diff(current, None)

        assert result.added_files == ["a.py", "b.py"]
        assert result.modified_files == []
        assert result.deleted_files == []
        assert result.unchanged_files == []
        assert result.has_changes

    def test_no_changes(self):
        """No changes detected → unchanged list populated."""
        engine = DiffEngine()
        lockfile = Lockfile(
            build_key="test",
            codetrellis_version="4.16.0",
            config_hash="cfg",
            file_manifest={
                "a.py": FileManifestEntry("a.py", "hash_a"),
                "b.py": FileManifestEntry("b.py", "hash_b"),
            },
        )
        current = {"a.py": "hash_a", "b.py": "hash_b"}

        result = engine.diff(current, lockfile)

        assert result.added_files == []
        assert result.modified_files == []
        assert result.deleted_files == []
        assert result.unchanged_files == ["a.py", "b.py"]
        assert not result.has_changes

    def test_file_modified(self):
        """Detect modified file."""
        engine = DiffEngine()
        lockfile = Lockfile(
            build_key="test",
            codetrellis_version="4.16.0",
            config_hash="cfg",
            file_manifest={
                "a.py": FileManifestEntry("a.py", "hash_a"),
            },
        )
        current = {"a.py": "hash_a_CHANGED"}

        result = engine.diff(current, lockfile)

        assert result.modified_files == ["a.py"]
        assert result.has_changes

    def test_file_added(self):
        """Detect added file."""
        engine = DiffEngine()
        lockfile = Lockfile(
            build_key="test",
            codetrellis_version="4.16.0",
            config_hash="cfg",
            file_manifest={
                "a.py": FileManifestEntry("a.py", "hash_a"),
            },
        )
        current = {"a.py": "hash_a", "b.py": "hash_b"}

        result = engine.diff(current, lockfile)

        assert result.added_files == ["b.py"]
        assert result.unchanged_files == ["a.py"]

    def test_file_deleted(self):
        """Detect deleted file."""
        engine = DiffEngine()
        lockfile = Lockfile(
            build_key="test",
            codetrellis_version="4.16.0",
            config_hash="cfg",
            file_manifest={
                "a.py": FileManifestEntry("a.py", "hash_a"),
                "b.py": FileManifestEntry("b.py", "hash_b"),
            },
        )
        current = {"a.py": "hash_a"}

        result = engine.diff(current, lockfile)

        assert result.deleted_files == ["b.py"]
        assert result.unchanged_files == ["a.py"]

    def test_mixed_changes(self):
        """Added + modified + deleted + unchanged in one diff."""
        engine = DiffEngine()
        lockfile = Lockfile(
            build_key="test",
            codetrellis_version="4.16.0",
            config_hash="cfg",
            file_manifest={
                "keep.py": FileManifestEntry("keep.py", "keep_hash"),
                "modify.py": FileManifestEntry("modify.py", "old_hash"),
                "delete.py": FileManifestEntry("delete.py", "del_hash"),
            },
        )
        current = {
            "keep.py": "keep_hash",
            "modify.py": "new_hash",
            "add.py": "add_hash",
        }

        result = engine.diff(current, lockfile)

        assert result.added_files == ["add.py"]
        assert result.modified_files == ["modify.py"]
        assert result.deleted_files == ["delete.py"]
        assert result.unchanged_files == ["keep.py"]
        assert result.has_changes
        assert result.total_files == 3  # added + modified + unchanged

    def test_summary(self):
        """Human-readable summary string."""
        result = DiffResult(
            added_files=["a.py"],
            modified_files=["b.py", "c.py"],
            deleted_files=["d.py"],
            unchanged_files=["e.py"],
        )
        summary = result.summary()
        assert "+1 added" in summary
        assert "~2 modified" in summary
        assert "-1 deleted" in summary
        assert "=1 unchanged" in summary

    def test_changed_files(self):
        """changed_files = added + modified."""
        result = DiffResult(
            added_files=["a.py"],
            modified_files=["b.py"],
        )
        assert set(result.changed_files) == {"a.py", "b.py"}


# =============================================================================
# Phase 1: BuildConfig Tests
# =============================================================================

class TestBuildConfig:
    """Test build configuration."""

    def test_default_config(self):
        """Default config has sane defaults."""
        config = BuildConfig()
        assert config.tier == OutputTier.PROMPT
        assert not config.deep
        assert not config.parallel
        assert not config.incremental
        assert not config.deterministic
        assert not config.ci

    def test_flags_hash_deterministic(self):
        """Same flags → same hash."""
        c1 = BuildConfig(tier=OutputTier.LOGIC, deep=True)
        c2 = BuildConfig(tier=OutputTier.LOGIC, deep=True)
        assert c1.flags_hash() == c2.flags_hash()

    def test_flags_hash_different(self):
        """Different flags → different hash."""
        c1 = BuildConfig(tier=OutputTier.LOGIC, deep=True)
        c2 = BuildConfig(tier=OutputTier.PROMPT, deep=False)
        assert c1.flags_hash() != c2.flags_hash()

    def test_to_dict(self):
        """Config serializes to dict."""
        config = BuildConfig(tier=OutputTier.LOGIC, deep=True, parallel=True)
        d = config.to_dict()
        assert d["tier"] == "logic"
        assert d["deep"] is True
        assert d["parallel"] is True


# =============================================================================
# Phase 1: BuildLogger Tests
# =============================================================================

class TestBuildLogger:
    """Test structured build logging."""

    def test_log_and_flush(self, tmp_path):
        """Log events and flush to JSONL file."""
        log_path = tmp_path / "_build_log.jsonl"
        logger = BuildLogger(log_path)

        logger.info("build_start", "Starting build")
        logger.warn("deprecation", "Old API used", extractor="python_parser")
        logger.error("extraction_failed", "File not found", file="missing.py")
        logger.flush()

        assert log_path.exists()
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 3

        event1 = json.loads(lines[0])
        assert event1["level"] == "info"
        assert event1["event"] == "build_start"

        event2 = json.loads(lines[1])
        assert event2["level"] == "warn"
        assert event2["extractor"] == "python_parser"

        event3 = json.loads(lines[2])
        assert event3["level"] == "error"
        assert event3["file"] == "missing.py"

    def test_events_property(self, tmp_path):
        """Buffered events accessible before flush."""
        logger = BuildLogger(tmp_path / "_build_log.jsonl")
        logger.info("test_event")
        assert len(logger.events) == 1

    def test_flush_clears_buffer(self, tmp_path):
        """Flush clears the event buffer."""
        logger = BuildLogger(tmp_path / "_build_log.jsonl")
        logger.info("test_event")
        logger.flush()
        assert len(logger.events) == 0


# =============================================================================
# Phase 3: BuildResult & BuildEvent Tests
# =============================================================================

class TestBuildEvent:
    """Test build event serialization."""

    def test_to_json(self):
        """Event serializes to valid JSON with sorted keys."""
        event = BuildEvent(
            timestamp="2026-02-20T10:00:00",
            level="info",
            event="build_start",
            extractor="scanner",
            duration_ms=123.456,
            message="test",
        )
        json_str = event.to_json()
        data = json.loads(json_str)

        assert data["level"] == "info"
        assert data["event"] == "build_start"
        assert data["duration_ms"] == 123.46  # Rounded to 2 decimal places
        keys = list(data.keys())
        assert keys == sorted(keys)  # Sorted keys


class TestBuildResult:
    """Test build result dataclass."""

    def test_success_result(self):
        """Successful build result."""
        result = BuildResult(
            success=True,
            exit_code=0,
            total_files=100,
            extractors_run=50,
            duration_ms=1234.5,
        )
        assert result.success
        assert result.exit_code == 0
        assert result.errors == []

    def test_failure_result(self):
        """Failed build result."""
        result = BuildResult(
            success=False,
            exit_code=3,
            errors=["Fatal error"],
        )
        assert not result.success
        assert result.exit_code == 3
        assert len(result.errors) == 1


# =============================================================================
# Phase 1: IExtractor Protocol Tests
# =============================================================================

class TestIExtractorProtocol:
    """Test the IExtractor protocol."""

    def test_protocol_compliance(self):
        """A class implementing all methods satisfies the protocol."""

        class MyExtractor:
            @property
            def manifest(self) -> ExtractorManifest:
                return ExtractorManifest(
                    name="my_extractor",
                    version="1.0",
                    input_patterns=["*.py"],
                    output_sections=["PYTHON_TYPES"],
                )

            def cache_key(self, file_path: str, file_content_hash: str) -> str:
                return f"my_extractor:{file_content_hash}"

            def extract(self, file_path: str, context: dict) -> dict:
                return {"classes": []}

        extractor = MyExtractor()
        assert isinstance(extractor, IExtractor)

    def test_non_compliant(self):
        """A class missing methods does NOT satisfy the protocol."""

        class NotAnExtractor:
            pass

        assert not isinstance(NotAnExtractor(), IExtractor)


class TestExtractorManifest:
    """Test extractor manifest."""

    def test_manifest_fields(self):
        """Manifest has all required fields."""
        m = ExtractorManifest(
            name="python_parser",
            version="2.0",
            input_patterns=["*.py"],
            depends_on=["config_extractor"],
            output_sections=["PYTHON_TYPES", "PYTHON_API"],
        )
        assert m.name == "python_parser"
        assert m.version == "2.0"
        assert "*.py" in m.input_patterns
        assert "config_extractor" in m.depends_on


# =============================================================================
# Phase 3: MatrixBuilder.verify() Tests (Quality Gate D1)
# =============================================================================

class TestMatrixBuilderVerify:
    """Test build quality gate verification."""

    def test_verify_valid_build(self, tmp_path):
        """D1: Verify passes for a valid build output."""
        from codetrellis import __version__

        cache_dir = tmp_path / ".codetrellis" / "cache" / __version__ / tmp_path.name
        cache_dir.mkdir(parents=True)

        # Create valid outputs
        (cache_dir / "matrix.prompt").write_text("[PROJECT]\nname=test")
        (cache_dir / "matrix.json").write_text(json.dumps({"name": "test"}))
        (cache_dir / "_metadata.json").write_text(json.dumps({
            "version": __version__,
            "project": "test",
            "generated": "2026-02-20T10:00:00",
            "stats": {"totalFiles": 10},
        }))

        builder = MatrixBuilder(str(tmp_path))
        result = builder.verify()

        assert result["passed"] is True
        assert result["errors"] == []

    def test_verify_missing_files(self, tmp_path):
        """D1: Verify fails when required files are missing."""
        from codetrellis import __version__

        cache_dir = tmp_path / ".codetrellis" / "cache" / __version__ / tmp_path.name
        cache_dir.mkdir(parents=True)

        builder = MatrixBuilder(str(tmp_path))
        result = builder.verify()

        assert result["passed"] is False
        assert any("MISSING" in e for e in result["errors"])

    def test_verify_empty_files(self, tmp_path):
        """D1: Verify fails for empty files."""
        from codetrellis import __version__

        cache_dir = tmp_path / ".codetrellis" / "cache" / __version__ / tmp_path.name
        cache_dir.mkdir(parents=True)

        (cache_dir / "matrix.prompt").write_text("")
        (cache_dir / "matrix.json").write_text("{}")
        (cache_dir / "_metadata.json").write_text("{}")

        builder = MatrixBuilder(str(tmp_path))
        result = builder.verify()

        assert result["passed"] is False

    def test_verify_invalid_json(self, tmp_path):
        """D1: Verify fails for invalid JSON."""
        from codetrellis import __version__

        cache_dir = tmp_path / ".codetrellis" / "cache" / __version__ / tmp_path.name
        cache_dir.mkdir(parents=True)

        (cache_dir / "matrix.prompt").write_text("[PROJECT]\ntest")
        (cache_dir / "matrix.json").write_text("NOT JSON {{{")
        (cache_dir / "_metadata.json").write_text("{}")

        builder = MatrixBuilder(str(tmp_path))
        result = builder.verify()

        assert result["passed"] is False
        assert any("INVALID_JSON" in e for e in result["errors"])

    def test_verify_version_mismatch(self, tmp_path):
        """D1: Verify warns on version mismatch."""
        from codetrellis import __version__

        cache_dir = tmp_path / ".codetrellis" / "cache" / __version__ / tmp_path.name
        cache_dir.mkdir(parents=True)

        (cache_dir / "matrix.prompt").write_text("[PROJECT]\ntest")
        (cache_dir / "matrix.json").write_text("{}")
        (cache_dir / "_metadata.json").write_text(json.dumps({
            "version": "0.0.0",  # Wrong version
            "project": "test",
            "generated": "2026-02-20",
            "stats": {"totalFiles": 10},
        }))

        builder = MatrixBuilder(str(tmp_path))
        result = builder.verify()

        assert result["passed"] is False
        assert any("VERSION_MISMATCH" in e for e in result["errors"])

    def test_verify_zero_files(self, tmp_path):
        """D1: Verify fails when totalFiles is 0."""
        from codetrellis import __version__

        cache_dir = tmp_path / ".codetrellis" / "cache" / __version__ / tmp_path.name
        cache_dir.mkdir(parents=True)

        (cache_dir / "matrix.prompt").write_text("[PROJECT]\ntest")
        (cache_dir / "matrix.json").write_text("{}")
        (cache_dir / "_metadata.json").write_text(json.dumps({
            "version": __version__,
            "project": "test",
            "generated": "2026-02-20",
            "stats": {"totalFiles": 0},
        }))

        builder = MatrixBuilder(str(tmp_path))
        result = builder.verify()

        assert result["passed"] is False
        assert any("ZERO_FILES" in e for e in result["errors"])

    def test_verify_missing_project_section(self, tmp_path):
        """D1: Verify fails when [PROJECT] is missing from matrix.prompt."""
        from codetrellis import __version__

        cache_dir = tmp_path / ".codetrellis" / "cache" / __version__ / tmp_path.name
        cache_dir.mkdir(parents=True)

        (cache_dir / "matrix.prompt").write_text("just some text without sections")
        (cache_dir / "matrix.json").write_text("{}")
        (cache_dir / "_metadata.json").write_text(json.dumps({
            "version": __version__,
            "project": "test",
            "generated": "2026-02-20",
            "stats": {"totalFiles": 10},
        }))

        builder = MatrixBuilder(str(tmp_path))
        result = builder.verify()

        assert result["passed"] is False
        assert any("MISSING_SECTION" in e for e in result["errors"])


# =============================================================================
# Integration-level tests
# =============================================================================

class TestDeterministicFileSortOrder:
    """Verify sorted() is applied in _walk_files."""

    def test_walk_files_sorted(self, tmp_path):
        """B4 Phase 0: _walk_files returns files in sorted order."""
        # Create files in reverse alphabetical order
        (tmp_path / "z_file.py").write_text("z")
        (tmp_path / "a_file.py").write_text("a")
        (tmp_path / "m_file.py").write_text("m")

        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        scanner._scan_root = str(tmp_path)
        scanner._gitignore_filter = None

        files = list(scanner._walk_files(tmp_path))
        names = [f.name for f in files]

        assert names == sorted(names), f"Files not sorted: {names}"

    def test_walk_dirs_sorted(self, tmp_path):
        """B4 Phase 0: Directories are traversed in sorted order."""
        # Create directories in reverse order
        (tmp_path / "z_dir").mkdir()
        (tmp_path / "a_dir").mkdir()
        (tmp_path / "z_dir" / "test.py").write_text("z")
        (tmp_path / "a_dir" / "test.py").write_text("a")

        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        scanner._scan_root = str(tmp_path)
        scanner._gitignore_filter = None

        files = list(scanner._walk_files(tmp_path))
        # First file should be from a_dir (alphabetically first)
        assert "a_dir" in str(files[0])


class TestJsonSortKeys:
    """Verify json.dumps uses sort_keys=True in cli.py."""

    def test_metadata_has_sorted_keys(self, tmp_path):
        """C3: _metadata.json has sorted keys."""
        # This is a static analysis test — verify the source code
        cli_path = Path(__file__).parent.parent.parent / "codetrellis" / "cli.py"
        if cli_path.exists():
            content = cli_path.read_text()
            # Check that metadata write uses sort_keys
            assert "sort_keys=True" in content, (
                "cli.py must use sort_keys=True in json.dumps for determinism"
            )
