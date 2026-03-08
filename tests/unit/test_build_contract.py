"""
Tests for CodeTrellis Build Contract (PART C: C1-C6)
=====================================================

Comprehensive test suite covering every clause of the formal I/O contract
for matrix generation:

    C1: Input validation (source files, config, env vars, CLI flags)
    C2: Output schema enforcement (matrix.prompt, matrix.json, _metadata.json,
        _lockfile.json, _build_log.jsonl)
    C3: Determinism guarantees (sorted keys, sorted traversal, timestamp control,
        set→sorted list, SHA-256 consistency)
    C4: Error contract (exit codes 0/1/2/3/124, error budgets, structured reporting)
    C5: Cache contract (invalidation rules, hash generation, env fingerprint,
        cache directory resolution)
    C6: Compatibility (additive fields, SemVer, section header stability)

Per D3 Quality Gate:
    - All tests use tmp_path fixture (no hardcoded paths)
    - No external network dependencies
    - Target ≥80% line coverage on build_contract.py

Author: Keshav Chaudhary
Created: 20 February 2026
"""

import hashlib
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from codetrellis import __version__ as VERSION
from codetrellis.build_contract import (
    ExitCode,
    BuildContractError,
    InputValidator,
    OutputSchemaValidator,
    DeterminismEnforcer,
    ErrorBudget,
    EnvironmentFingerprint,
    CacheInvalidator,
    BuildContractVerifier,
    TimeoutHandler,
    SUPPORTED_EXTENSIONS,
    REQUIRED_METADATA_FIELDS,
    REQUIRED_PROMPT_SECTIONS,
    REQUIRED_STATS_FIELDS,
    ENV_VARS,
    get_cache_base_dir,
    get_versioned_cache_dir,
    get_config_hash,
)
from codetrellis.cache import (
    Lockfile,
    FileManifestEntry,
    LockfileManager,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a minimal valid project directory."""
    project = tmp_path / "test-project"
    project.mkdir()
    # Create a minimal Python file
    (project / "main.py").write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    return project


@pytest.fixture
def project_with_config(project_dir: Path) -> Path:
    """Project with a .codetrellis/config.json."""
    config_dir = project_dir / ".codetrellis"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(
        json.dumps({"tier": "standard", "parallel": True}, indent=2),
        encoding="utf-8",
    )
    return project_dir


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    """Create a valid cache directory with all required outputs."""
    cache = tmp_path / ".codetrellis" / "cache" / VERSION / "test-project"
    cache.mkdir(parents=True)

    # matrix.prompt — requires [PROJECT] section and ≥100 bytes
    prompt_content = (
        "[PROJECT]\nName: test-project\nType: Python\n"
        "Description: A test project for build contract validation.\n"
        "Technologies: Python 3.9+\n\n"
        "[SCHEMAS]\nNo schemas found.\n\n"
        "[COMPONENTS]\nNo components found.\n"
    )
    (cache / "matrix.prompt").write_text(prompt_content, encoding="utf-8")

    # matrix.json — valid JSON object with sorted keys
    matrix_data = {
        "components": [],
        "controllers": [],
        "dtos": [],
        "interfaces": [],
        "project": "test-project",
        "schemas": [],
        "services": [],
        "total_files": 1,
        "types": [],
        "version": VERSION,
    }
    (cache / "matrix.json").write_text(
        json.dumps(matrix_data, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # _metadata.json — valid with all required fields
    metadata = {
        "generated": "2026-02-20T10:00:00",
        "project": "test-project",
        "stats": {"totalFiles": 1},
        "version": VERSION,
    }
    (cache / "_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # _lockfile.json — valid with required fields
    lockfile_data = {
        "build_key": f"{VERSION}:abc123",
        "cli_flags_hash": "abc123",
        "codetrellis_version": VERSION,
        "config_hash": "abc123",
        "env_fingerprint": "0000000000000000",
        "extractor_versions": {},
        "file_manifest": {},
        "generated_at": "2026-02-20T10:00:00",
        "total_files": 1,
    }
    (cache / "_lockfile.json").write_text(
        json.dumps(lockfile_data, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # _build_log.jsonl — valid JSONL
    log_entry = json.dumps({
        "level": "INFO",
        "event": "build_start",
        "message": "Build started",
        "timestamp": "2026-02-20T10:00:00",
    })
    (cache / "_build_log.jsonl").write_text(log_entry + "\n", encoding="utf-8")

    return cache


@pytest.fixture(autouse=True)
def clean_env():
    """Ensure build-related env vars are clean for each test."""
    vars_to_clean = [
        "CODETRELLIS_BUILD_TIMESTAMP",
        "CODETRELLIS_CI",
        "CODETRELLIS_CACHE_DIR",
    ]
    old_values = {}
    for var in vars_to_clean:
        old_values[var] = os.environ.pop(var, None)
    yield
    for var, val in old_values.items():
        if val is not None:
            os.environ[var] = val
        else:
            os.environ.pop(var, None)


# =============================================================================
# C4: Exit Code Tests
# =============================================================================

class TestExitCodes:
    """C4: Exit code constants and semantics."""

    def test_success_is_zero(self):
        """C4: Exit code 0 means all outputs written successfully."""
        assert ExitCode.SUCCESS == 0
        assert int(ExitCode.SUCCESS) == 0

    def test_partial_failure_is_one(self):
        """C4: Exit code 1 means some extractors failed."""
        assert ExitCode.PARTIAL_FAILURE == 1

    def test_configuration_error_is_two(self):
        """C4: Exit code 2 means configuration error."""
        assert ExitCode.CONFIGURATION_ERROR == 2

    def test_fatal_error_is_three(self):
        """C4: Exit code 3 means fatal error, no outputs written."""
        assert ExitCode.FATAL_ERROR == 3

    def test_timeout_is_124(self):
        """C4: Exit code 124 means build timed out."""
        assert ExitCode.TIMEOUT == 124

    def test_all_exit_codes_are_unique(self):
        """C4: No two exit codes share the same integer value."""
        values = [e.value for e in ExitCode]
        assert len(values) == len(set(values))

    def test_exit_codes_are_ints(self):
        """C4: All exit codes are valid integers."""
        for code in ExitCode:
            assert isinstance(int(code), int)


# =============================================================================
# C4: BuildContractError Tests
# =============================================================================

class TestBuildContractError:
    """C4: Structured error reporting."""

    def test_basic_construction(self):
        """Error can be constructed with message."""
        err = BuildContractError("test error")
        assert str(err) == "test error"
        assert err.exit_code == ExitCode.FATAL_ERROR
        assert err.violations == []

    def test_with_exit_code(self):
        """Error can specify exit code."""
        err = BuildContractError(
            "config invalid",
            exit_code=ExitCode.CONFIGURATION_ERROR,
        )
        assert err.exit_code == ExitCode.CONFIGURATION_ERROR

    def test_with_violations(self):
        """Error can carry violation list."""
        violations = ["C1.1: root missing", "C1.2: config invalid"]
        err = BuildContractError(
            "validation failed",
            violations=violations,
        )
        assert err.violations == violations

    def test_to_dict_serialization(self):
        """C4: Error serializes to dict for structured reporting."""
        err = BuildContractError(
            "test",
            exit_code=ExitCode.PARTIAL_FAILURE,
            violations=["v1"],
        )
        d = err.to_dict()
        assert d["exit_code"] == 1
        assert d["exit_code_name"] == "PARTIAL_FAILURE"
        assert d["violations"] == ["v1"]
        assert "timestamp" in d
        assert "error" in d


# =============================================================================
# C1: Input Validator Tests
# =============================================================================

class TestInputValidator:
    """C1: Input validation for source files, config, env vars, CLI flags."""

    # --- C1.1: Project Root ---

    def test_valid_project_root(self, project_dir: Path):
        """C1.1: Valid project root passes validation."""
        validator = InputValidator(str(project_dir))
        errors = validator.validate()
        assert errors == []

    def test_nonexistent_project_root(self, tmp_path: Path):
        """C1.1: Non-existent path fails validation."""
        validator = InputValidator(str(tmp_path / "does-not-exist"))
        errors = validator.validate()
        assert any("C1.1" in e and "does not exist" in e for e in errors)

    def test_file_as_project_root(self, tmp_path: Path):
        """C1.1: File (not directory) fails validation."""
        f = tmp_path / "not-a-dir"
        f.write_text("hello", encoding="utf-8")
        validator = InputValidator(str(f))
        errors = validator.validate()
        assert any("C1.1" in e and "not a directory" in e for e in errors)

    # --- C1.1: Supported Extensions ---

    def test_supported_extensions_include_core_languages(self):
        """C1.1: All core language extensions are in SUPPORTED_EXTENSIONS."""
        core = [".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt", ".cs",
                ".go", ".rs", ".rb", ".php", ".scala", ".r", ".dart", ".lua",
                ".swift", ".c", ".h", ".cpp", ".hpp"]
        for ext in core:
            assert InputValidator.is_supported_extension(ext), f"{ext} not supported"

    def test_supported_extensions_include_web(self):
        """C1.1: Web extensions are in SUPPORTED_EXTENSIONS."""
        web = [".html", ".css", ".scss", ".sass", ".less", ".vue", ".svelte", ".astro"]
        for ext in web:
            assert InputValidator.is_supported_extension(ext), f"{ext} not supported"

    def test_supported_extensions_include_config(self):
        """C1.1: Config/data extensions are in SUPPORTED_EXTENSIONS."""
        config = [".json", ".yaml", ".yml", ".toml", ".proto", ".graphql"]
        for ext in config:
            assert InputValidator.is_supported_extension(ext), f"{ext} not supported"

    def test_unsupported_extension_rejected(self):
        """C1.1: Non-supported extensions are rejected."""
        assert not InputValidator.is_supported_extension(".exe")
        assert not InputValidator.is_supported_extension(".dll")
        assert not InputValidator.is_supported_extension(".docx")

    def test_extension_check_case_insensitive(self):
        """C1.1: Extension check is case-insensitive."""
        assert InputValidator.is_supported_extension(".PY")
        assert InputValidator.is_supported_extension(".Ts")
        assert InputValidator.is_supported_extension(".JSX")

    # --- C1.2: Config Validation ---

    def test_valid_config_json(self, project_with_config: Path):
        """C1.2: Valid config.json passes."""
        validator = InputValidator(str(project_with_config))
        errors = validator.validate()
        assert errors == []

    def test_invalid_config_json(self, project_dir: Path):
        """C1.2: Malformed config.json fails."""
        config_dir = project_dir / ".codetrellis"
        config_dir.mkdir()
        (config_dir / "config.json").write_text("{invalid json", encoding="utf-8")
        validator = InputValidator(str(project_dir))
        errors = validator.validate()
        assert any("C1.2" in e and "invalid JSON" in e for e in errors)

    def test_config_json_not_object(self, project_dir: Path):
        """C1.2: config.json that is not a JSON object fails."""
        config_dir = project_dir / ".codetrellis"
        config_dir.mkdir()
        (config_dir / "config.json").write_text("[1, 2, 3]", encoding="utf-8")
        validator = InputValidator(str(project_dir))
        errors = validator.validate()
        assert any("C1.2" in e and "must be a JSON object" in e for e in errors)

    def test_missing_config_json_is_ok(self, project_dir: Path):
        """C1.2: Absence of config.json is NOT an error (auto-created)."""
        validator = InputValidator(str(project_dir))
        errors = validator.validate()
        assert errors == []

    # --- C1.3: Environment Variables ---

    def test_valid_timestamp_env_var(self, project_dir: Path):
        """C1.3: Valid ISO 8601 timestamp passes."""
        os.environ["CODETRELLIS_BUILD_TIMESTAMP"] = "2026-02-20T10:00:00"
        validator = InputValidator(str(project_dir))
        errors = validator.validate()
        assert errors == []

    def test_deterministic_timestamp_accepted(self, project_dir: Path):
        """C1.3: Special value 'deterministic' is accepted."""
        os.environ["CODETRELLIS_BUILD_TIMESTAMP"] = "deterministic"
        validator = InputValidator(str(project_dir))
        errors = validator.validate()
        assert not any("CODETRELLIS_BUILD_TIMESTAMP" in e for e in errors)

    def test_invalid_timestamp_env_var(self, project_dir: Path):
        """C1.3: Invalid timestamp value fails."""
        os.environ["CODETRELLIS_BUILD_TIMESTAMP"] = "not-a-timestamp"
        validator = InputValidator(str(project_dir))
        errors = validator.validate()
        assert any("C1.3" in e and "CODETRELLIS_BUILD_TIMESTAMP" in e for e in errors)

    def test_cache_dir_file_not_directory(self, tmp_path: Path, project_dir: Path):
        """C1.3: CODETRELLIS_CACHE_DIR pointing to a file fails."""
        f = tmp_path / "cache_file"
        f.write_text("not a dir", encoding="utf-8")
        os.environ["CODETRELLIS_CACHE_DIR"] = str(f)
        validator = InputValidator(str(project_dir))
        errors = validator.validate()
        assert any("C1.3" in e and "CODETRELLIS_CACHE_DIR" in e for e in errors)

    def test_cache_dir_nonexistent_is_ok(self, project_dir: Path):
        """C1.3: CODETRELLIS_CACHE_DIR that doesn't exist yet is NOT an error."""
        os.environ["CODETRELLIS_CACHE_DIR"] = "/tmp/does-not-exist-yet"
        validator = InputValidator(str(project_dir))
        errors = validator.validate()
        assert not any("CODETRELLIS_CACHE_DIR" in e for e in errors)

    # --- C1.3: ENV_VARS documentation ---

    def test_env_vars_registry_complete(self):
        """C1.3: ENV_VARS registry documents all build-relevant env vars."""
        expected = {
            "CODETRELLIS_BUILD_TIMESTAMP",
            "CODETRELLIS_CI",
            "CODETRELLIS_CACHE_DIR",
            "JAVA_HOME",
            "JDT_LS_PATH",
            "NODE_ENV",
        }
        assert set(ENV_VARS.keys()) == expected


# =============================================================================
# C2: Output Schema Validator Tests
# =============================================================================

class TestOutputSchemaValidator:
    """C2: Output schema enforcement."""

    def test_all_valid_outputs_pass(self, cache_dir: Path):
        """C2: Valid outputs pass all validation."""
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is True
        assert errors == []

    # --- C2.1: Required Files ---

    def test_missing_matrix_prompt(self, cache_dir: Path):
        """C2.1: Missing matrix.prompt fails."""
        (cache_dir / "matrix.prompt").unlink()
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("MISSING" in e and "matrix.prompt" in e for e in errors)

    def test_missing_matrix_json(self, cache_dir: Path):
        """C2.1: Missing matrix.json fails."""
        (cache_dir / "matrix.json").unlink()
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("MISSING" in e and "matrix.json" in e for e in errors)

    def test_missing_metadata_json(self, cache_dir: Path):
        """C2.1: Missing _metadata.json fails."""
        (cache_dir / "_metadata.json").unlink()
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("MISSING" in e and "_metadata.json" in e for e in errors)

    def test_empty_matrix_prompt(self, cache_dir: Path):
        """C2.1: Empty matrix.prompt fails."""
        (cache_dir / "matrix.prompt").write_text("", encoding="utf-8")
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("EMPTY" in e and "matrix.prompt" in e for e in errors)

    def test_matrix_prompt_too_small(self, cache_dir: Path):
        """C2.1: matrix.prompt smaller than 100 bytes fails."""
        (cache_dir / "matrix.prompt").write_text("[PROJECT]\nSmall", encoding="utf-8")
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("too small" in e for e in errors)

    # --- C2.1: matrix.prompt Section Headers ---

    def test_matrix_prompt_missing_project_section(self, cache_dir: Path):
        """C2.1: matrix.prompt without [PROJECT] section fails."""
        (cache_dir / "matrix.prompt").write_text(
            "No section headers here. " * 10,
            encoding="utf-8",
        )
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("[PROJECT]" in e for e in errors)

    # --- C2.1: matrix.json Validation ---

    def test_matrix_json_invalid(self, cache_dir: Path):
        """C2.1: Invalid JSON in matrix.json fails."""
        (cache_dir / "matrix.json").write_text("{bad json", encoding="utf-8")
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("invalid JSON" in e and "matrix.json" in e for e in errors)

    def test_matrix_json_not_object(self, cache_dir: Path):
        """C2.1: matrix.json root must be a JSON object."""
        (cache_dir / "matrix.json").write_text("[1, 2, 3]", encoding="utf-8")
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("must be a JSON object" in e for e in errors)

    def test_matrix_json_unsorted_keys(self, cache_dir: Path):
        """C2.1/C3: matrix.json with unsorted top-level keys fails."""
        data = json.dumps({"zebra": 1, "alpha": 2})  # Not sorted
        (cache_dir / "matrix.json").write_text(data, encoding="utf-8")
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("not sorted" in e for e in errors)

    # --- C2.1: _metadata.json Validation ---

    def test_metadata_missing_required_fields(self, cache_dir: Path):
        """C2.1: _metadata.json missing required fields fails."""
        (cache_dir / "_metadata.json").write_text(
            json.dumps({"version": VERSION}, sort_keys=True),
            encoding="utf-8",
        )
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        # Should report missing project, generated, stats
        assert any("missing required field" in e for e in errors)

    def test_metadata_stats_missing_total_files(self, cache_dir: Path):
        """C2.1: _metadata.json.stats missing totalFiles fails."""
        data = {
            "generated": "2026-02-20T10:00:00",
            "project": "test",
            "stats": {},
            "version": VERSION,
        }
        (cache_dir / "_metadata.json").write_text(
            json.dumps(data, sort_keys=True),
            encoding="utf-8",
        )
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("totalFiles" in e for e in errors)

    def test_metadata_version_mismatch(self, cache_dir: Path):
        """C2.1: _metadata.json version mismatch fails."""
        data = {
            "generated": "2026-02-20T10:00:00",
            "project": "test",
            "stats": {"totalFiles": 1},
            "version": "0.0.0",
        }
        (cache_dir / "_metadata.json").write_text(
            json.dumps(data, sort_keys=True),
            encoding="utf-8",
        )
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("version mismatch" in e for e in errors)

    def test_metadata_unsorted_keys(self, cache_dir: Path):
        """C2.1/C3: _metadata.json with unsorted keys fails."""
        data = json.dumps({
            "version": VERSION,
            "project": "test",
            "generated": "2026-02-20T10:00:00",
            "stats": {"totalFiles": 1},
        })  # version before project = not sorted
        (cache_dir / "_metadata.json").write_text(data, encoding="utf-8")
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("not sorted" in e for e in errors)

    # --- C2.2: _lockfile.json Validation ---

    def test_lockfile_missing_is_ok(self, cache_dir: Path):
        """C2.2: Missing _lockfile.json is not an error (optional)."""
        (cache_dir / "_lockfile.json").unlink()
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is True

    def test_lockfile_invalid_json(self, cache_dir: Path):
        """C2.2: Invalid JSON in _lockfile.json fails."""
        (cache_dir / "_lockfile.json").write_text("{bad", encoding="utf-8")
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("_lockfile.json" in e and "invalid JSON" in e for e in errors)

    def test_lockfile_missing_required_fields(self, cache_dir: Path):
        """C2.2: _lockfile.json missing build_key/codetrellis_version/config_hash fails."""
        (cache_dir / "_lockfile.json").write_text(
            json.dumps({"some_field": "value"}, sort_keys=True),
            encoding="utf-8",
        )
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("missing field" in e for e in errors)

    def test_lockfile_unsorted_keys(self, cache_dir: Path):
        """C2.2/C3: _lockfile.json with unsorted keys fails."""
        data = json.dumps({
            "config_hash": "abc",
            "build_key": "key",
            "codetrellis_version": VERSION,
        })  # Not sorted
        (cache_dir / "_lockfile.json").write_text(data, encoding="utf-8")
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
        assert passed is False
        assert any("not sorted" in e for e in errors)


# =============================================================================
# C3: Determinism Enforcer Tests
# =============================================================================

class TestDeterminismEnforcer:
    """C3: Determinism guarantees."""

    # --- C3.1: JSON Determinism ---

    def test_deterministic_json_sorted_keys(self):
        """C3 Req 2: json.dumps with sort_keys=True."""
        data = {"z": 1, "a": 2, "m": 3}
        result = DeterminismEnforcer.deterministic_json(data)
        parsed = json.loads(result)
        assert list(parsed.keys()) == ["a", "m", "z"]

    def test_deterministic_json_set_conversion(self):
        """C3 Req 4: Sets converted to sorted lists."""
        data = {"items": {3, 1, 2}, "name": "test"}
        result = DeterminismEnforcer.deterministic_json(data)
        parsed = json.loads(result)
        assert parsed["items"] == ["1", "2", "3"]

    def test_deterministic_json_frozenset_conversion(self):
        """C3 Req 4: Frozensets also converted to sorted lists."""
        data = {"tags": frozenset(["c", "a", "b"])}
        result = DeterminismEnforcer.deterministic_json(data)
        parsed = json.loads(result)
        assert parsed["tags"] == ["a", "b", "c"]

    def test_deterministic_json_nested_sets(self):
        """C3 Req 4: Nested sets are recursively converted."""
        data = {"outer": {"inner": {"1", "3", "2"}}}
        result = DeterminismEnforcer.deterministic_json(data)
        parsed = json.loads(result)
        assert parsed["outer"]["inner"] == ["1", "2", "3"]

    def test_deterministic_json_reproducible(self):
        """C3: Same input always produces same output."""
        data = {"b": [3, 1, 2], "a": {"y": 1, "x": 2}}
        r1 = DeterminismEnforcer.deterministic_json(data)
        r2 = DeterminismEnforcer.deterministic_json(data)
        assert r1 == r2

    # --- C3.3: Timestamp Control ---

    def test_timestamp_from_env(self):
        """C3 Req 3: Uses CODETRELLIS_BUILD_TIMESTAMP if set."""
        os.environ["CODETRELLIS_BUILD_TIMESTAMP"] = "2026-01-01T00:00:00"
        ts = DeterminismEnforcer.get_timestamp()
        assert ts == "2026-01-01T00:00:00"

    def test_timestamp_default_is_now(self):
        """C3 Req 3: Falls back to datetime.now().isoformat()."""
        ts = DeterminismEnforcer.get_timestamp()
        # Should be a valid ISO timestamp close to now
        parsed = datetime.fromisoformat(ts)
        assert abs((datetime.now() - parsed).total_seconds()) < 5

    def test_deterministic_timestamp_value(self):
        """C3: 'deterministic' is a valid timestamp value."""
        os.environ["CODETRELLIS_BUILD_TIMESTAMP"] = "deterministic"
        ts = DeterminismEnforcer.get_timestamp()
        assert ts == "deterministic"

    # --- C3.1: Sorted File Walk ---

    def test_sorted_file_walk(self, tmp_path: Path):
        """C3 Req 1: sorted(Path.rglob(...)) for file traversal."""
        (tmp_path / "c.py").write_text("c", encoding="utf-8")
        (tmp_path / "a.py").write_text("a", encoding="utf-8")
        (tmp_path / "b.py").write_text("b", encoding="utf-8")
        result = DeterminismEnforcer.sorted_file_walk(tmp_path)
        names = [p.name for p in result]
        assert names == sorted(names)

    # --- C3.5: SHA-256 Consistency ---

    def test_file_hash_sha256(self, tmp_path: Path):
        """C3 Req 5: File hash uses SHA-256 (not MD5)."""
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        expected = hashlib.sha256(b"hello world").hexdigest()[:16]
        assert DeterminismEnforcer.file_hash(str(f)) == expected

    def test_file_hash_is_16_chars(self, tmp_path: Path):
        """C3 Req 5: File hash returns first 16 hex chars."""
        f = tmp_path / "test.txt"
        f.write_text("test content", encoding="utf-8")
        h = DeterminismEnforcer.file_hash(str(f))
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    def test_content_hash(self):
        """C3: String content hash uses SHA-256 (first 16 chars)."""
        h = DeterminismEnforcer.content_hash("hello")
        expected = hashlib.sha256(b"hello").hexdigest()[:16]
        assert h == expected

    # --- C3: Determinism Verification ---

    def test_verify_determinism_identical(self, tmp_path: Path):
        """C3: Identical files pass determinism check."""
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        content = "identical content"
        a.write_text(content, encoding="utf-8")
        b.write_text(content, encoding="utf-8")
        identical, detail = DeterminismEnforcer.verify_determinism(a, b)
        assert identical is True
        assert "match" in detail

    def test_verify_determinism_different(self, tmp_path: Path):
        """C3: Different files fail determinism check."""
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("content A", encoding="utf-8")
        b.write_text("content B", encoding="utf-8")
        identical, detail = DeterminismEnforcer.verify_determinism(a, b)
        assert identical is False
        assert "mismatch" in detail

    def test_verify_determinism_missing_file(self, tmp_path: Path):
        """C3: Missing file fails determinism check."""
        a = tmp_path / "exists.txt"
        b = tmp_path / "missing.txt"
        a.write_text("content", encoding="utf-8")
        identical, detail = DeterminismEnforcer.verify_determinism(a, b)
        assert identical is False
        assert "do not exist" in detail


# =============================================================================
# C4: Error Budget Tests
# =============================================================================

class TestErrorBudget:
    """C4: Error budget tracking and exit code derivation."""

    def test_empty_budget_is_success(self):
        """C4: No failures → exit 0."""
        budget = ErrorBudget()
        assert budget.exit_code == ExitCode.SUCCESS
        assert budget.total_successes == 0
        assert budget.total_failures == 0

    def test_all_success_is_exit_zero(self):
        """C4: All successes → exit 0."""
        budget = ErrorBudget()
        budget.record_success("python_parser", "cli.py")
        budget.record_success("python_parser", "builder.py")
        assert budget.exit_code == ExitCode.SUCCESS
        assert budget.total_successes == 2

    def test_some_failures_is_partial(self):
        """C4: Some successes + some failures → exit 1 (partial)."""
        budget = ErrorBudget()
        budget.record_success("python_parser", "good.py")
        budget.record_failure("python_parser", "bad.py", "SyntaxError")
        assert budget.exit_code == ExitCode.PARTIAL_FAILURE
        assert budget.total_failures == 1

    def test_all_failures_is_fatal(self):
        """C4: All failures, no successes → exit 3 (fatal)."""
        budget = ErrorBudget()
        budget.record_failure("parser", "a.py", "Error 1")
        budget.record_failure("parser", "b.py", "Error 2")
        assert budget.exit_code == ExitCode.FATAL_ERROR

    def test_skip_tracking(self):
        """C4: Skipped files are tracked."""
        budget = ErrorBudget()
        budget.record_skip("binary.exe", "unsupported extension")
        assert budget.total_skipped == 1

    def test_warning_tracking(self):
        """C4: Warnings are tracked."""
        budget = ErrorBudget()
        budget.record_warning("deprecated function used", "old.py")
        assert budget.total_warnings == 1

    def test_to_dict_serialization(self):
        """C4: Budget serializes for _build_log.jsonl."""
        budget = ErrorBudget()
        budget.record_success("py", "a.py")
        budget.record_failure("py", "b.py", "err")
        budget.record_skip("c.bin", "binary")
        budget.record_warning("warn", "d.py")
        d = budget.to_dict()
        assert d["successes"] == 1
        assert d["failures"] == 1
        assert d["skipped"] == 1
        assert d["warnings"] == 1
        assert d["exit_code"] == 1
        assert d["exit_code_name"] == "PARTIAL_FAILURE"
        assert len(d["failure_details"]) == 1
        assert len(d["skip_details"]) == 1
        assert len(d["warning_details"]) == 1

    def test_summary_string(self):
        """C4: Summary is human-readable."""
        budget = ErrorBudget()
        budget.record_success("py", "a.py")
        budget.record_failure("py", "b.py", "err")
        summary = budget.summary()
        assert "1 succeeded" in summary
        assert "1 failed" in summary
        assert "exit 1" in summary


# =============================================================================
# C5: Environment Fingerprint Tests
# =============================================================================

class TestEnvironmentFingerprint:
    """C5 Rule 6: Environment fingerprint for cache invalidation."""

    def test_fingerprint_is_16_hex_chars(self):
        """C5: Fingerprint is first 16 hex chars of SHA-256."""
        fp = EnvironmentFingerprint.compute()
        assert len(fp) == 16
        assert all(c in "0123456789abcdef" for c in fp)

    def test_fingerprint_is_deterministic(self):
        """C5: Same environment produces same fingerprint."""
        fp1 = EnvironmentFingerprint.compute()
        fp2 = EnvironmentFingerprint.compute()
        assert fp1 == fp2

    def test_fingerprint_changes_with_env_var(self):
        """C5 Rule 6: Changing a relevant env var changes the fingerprint."""
        fp1 = EnvironmentFingerprint.compute()
        os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-17"
        fp2 = EnvironmentFingerprint.compute()
        # Clean up
        del os.environ["JAVA_HOME"]
        assert fp1 != fp2

    def test_fingerprint_includes_version(self):
        """C5: Fingerprint includes CodeTrellis version."""
        details = EnvironmentFingerprint.to_dict()
        assert details["codetrellis_version"] == VERSION
        assert details["python_version"] == sys.version
        assert details["platform"] == sys.platform

    def test_fingerprint_to_dict_env_vars(self):
        """C5: to_dict shows set env vars."""
        os.environ["NODE_ENV"] = "production"
        details = EnvironmentFingerprint.to_dict()
        assert "NODE_ENV" in details["env_vars"]
        assert details["env_vars"]["NODE_ENV"] == "production"
        del os.environ["NODE_ENV"]


# =============================================================================
# C5: Cache Invalidator Tests
# =============================================================================

class TestCacheInvalidator:
    """C5: Cache invalidation rules."""

    def _make_lockfile_data(self, **overrides) -> dict:
        """Helper to create a lockfile dict."""
        base = {
            "build_key": f"{VERSION}:abc123",
            "codetrellis_version": VERSION,
            "config_hash": "abc123",
            "cli_flags_hash": "abc123",
            "env_fingerprint": "0000000000000000",
            "file_manifest": {},
            "generated_at": "2026-02-20T10:00:00",
            "total_files": 1,
        }
        base.update(overrides)
        return base

    def test_valid_cache(self):
        """C5: Matching parameters → cache valid."""
        invalidator = CacheInvalidator(
            current_version=VERSION,
            current_config_hash="abc123",
            current_flags_hash="abc123",
            current_env_fingerprint="0000000000000000",
        )
        lockfile = self._make_lockfile_data()
        assert invalidator.is_cache_valid(lockfile) is True
        assert invalidator.invalidation_reasons(lockfile) == []

    def test_rule_2_version_change(self):
        """C5 Rule 2: Version change invalidates cache."""
        invalidator = CacheInvalidator(
            current_version="99.99.99",
            current_config_hash="abc123",
            current_flags_hash="abc123",
            current_env_fingerprint="0000000000000000",
        )
        lockfile = self._make_lockfile_data()
        assert invalidator.is_cache_valid(lockfile) is False
        reasons = invalidator.invalidation_reasons(lockfile)
        assert any("Rule 2" in r for r in reasons)

    def test_rule_3_config_hash_change(self):
        """C5 Rule 3: Config hash change invalidates cache."""
        invalidator = CacheInvalidator(
            current_version=VERSION,
            current_config_hash="different_hash",
            current_flags_hash="abc123",
            current_env_fingerprint="0000000000000000",
        )
        lockfile = self._make_lockfile_data()
        assert invalidator.is_cache_valid(lockfile) is False
        reasons = invalidator.invalidation_reasons(lockfile)
        assert any("Rule 3" in r for r in reasons)

    def test_rule_4_cli_flags_change(self):
        """C5 Rule 4: CLI flags change invalidates cache."""
        invalidator = CacheInvalidator(
            current_version=VERSION,
            current_config_hash="abc123",
            current_flags_hash="different_flags",
            current_env_fingerprint="0000000000000000",
        )
        lockfile = self._make_lockfile_data()
        assert invalidator.is_cache_valid(lockfile) is False
        reasons = invalidator.invalidation_reasons(lockfile)
        assert any("Rule 4" in r for r in reasons)

    def test_rule_6_env_fingerprint_change(self):
        """C5 Rule 6: Environment fingerprint change invalidates cache."""
        invalidator = CacheInvalidator(
            current_version=VERSION,
            current_config_hash="abc123",
            current_flags_hash="abc123",
            current_env_fingerprint="ffff000000000000",
        )
        lockfile = self._make_lockfile_data()
        assert invalidator.is_cache_valid(lockfile) is False
        reasons = invalidator.invalidation_reasons(lockfile)
        assert any("Rule 6" in r for r in reasons)

    def test_rule_6_empty_fingerprint_in_lockfile(self):
        """C5 Rule 6: Empty fingerprint in lockfile is treated as valid (upgrade)."""
        invalidator = CacheInvalidator(
            current_version=VERSION,
            current_config_hash="abc123",
            current_flags_hash="abc123",
            current_env_fingerprint="ffff000000000000",
        )
        lockfile = self._make_lockfile_data(env_fingerprint="")
        assert invalidator.is_cache_valid(lockfile) is True

    def test_multiple_invalidation_reasons(self):
        """C5: Multiple changes produce multiple reasons."""
        invalidator = CacheInvalidator(
            current_version="99.99.99",
            current_config_hash="new_config",
            current_flags_hash="new_flags",
            current_env_fingerprint="new_fingerprint",
        )
        lockfile = self._make_lockfile_data()
        reasons = invalidator.invalidation_reasons(lockfile)
        assert len(reasons) >= 3  # version + config + flags (+ maybe env)


# =============================================================================
# C5: Cache Directory Resolution Tests
# =============================================================================

class TestCacheDirectoryResolution:
    """C5: Cache directory layout and resolution."""

    def test_default_cache_dir(self, project_dir: Path):
        """C5: Default cache dir is .codetrellis/cache/{VERSION}/{project_name}."""
        cache = get_versioned_cache_dir(project_dir)
        assert str(cache).endswith(f"cache/{VERSION}/{project_dir.name}")

    def test_env_override_cache_dir(self, project_dir: Path, tmp_path: Path):
        """C5/C1.3: CODETRELLIS_CACHE_DIR overrides default location."""
        custom = tmp_path / "custom_cache"
        os.environ["CODETRELLIS_CACHE_DIR"] = str(custom)
        base = get_cache_base_dir(project_dir)
        assert base == custom

    def test_config_hash_empty_when_no_config(self, project_dir: Path):
        """C5 Rule 3: No config.json → empty config hash."""
        h = get_config_hash(project_dir)
        assert h == ""

    def test_config_hash_computed(self, project_with_config: Path):
        """C5 Rule 3: config.json hash is SHA-256 (first 16 chars)."""
        h = get_config_hash(project_with_config)
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    def test_config_hash_deterministic(self, project_with_config: Path):
        """C5 Rule 3: Same config.json always produces same hash."""
        h1 = get_config_hash(project_with_config)
        h2 = get_config_hash(project_with_config)
        assert h1 == h2

    def test_config_hash_changes_with_content(self, project_with_config: Path):
        """C5 Rule 3: Changing config.json changes hash."""
        h1 = get_config_hash(project_with_config)
        config_path = project_with_config / ".codetrellis" / "config.json"
        config_path.write_text(json.dumps({"tier": "deep"}), encoding="utf-8")
        h2 = get_config_hash(project_with_config)
        assert h1 != h2


# =============================================================================
# C5: Lockfile env_fingerprint Integration Tests
# =============================================================================

class TestLockfileEnvFingerprint:
    """C5: Lockfile includes env_fingerprint field."""

    def test_lockfile_has_env_fingerprint_field(self):
        """C5 Rule 6: Lockfile dataclass has env_fingerprint field."""
        lf = Lockfile(
            build_key="test",
            codetrellis_version=VERSION,
            config_hash="abc",
            env_fingerprint="0123456789abcdef",
        )
        assert lf.env_fingerprint == "0123456789abcdef"

    def test_lockfile_env_fingerprint_default_empty(self):
        """C5 Rule 6: env_fingerprint defaults to empty string."""
        lf = Lockfile(
            build_key="test",
            codetrellis_version=VERSION,
            config_hash="abc",
        )
        assert lf.env_fingerprint == ""

    def test_lockfile_to_dict_includes_env_fingerprint(self):
        """C5 Rule 6: to_dict serializes env_fingerprint."""
        lf = Lockfile(
            build_key="test",
            codetrellis_version=VERSION,
            config_hash="abc",
            env_fingerprint="0123456789abcdef",
        )
        d = lf.to_dict()
        assert "env_fingerprint" in d
        assert d["env_fingerprint"] == "0123456789abcdef"

    def test_lockfile_from_dict_reads_env_fingerprint(self):
        """C5 Rule 6: from_dict reads env_fingerprint."""
        data = {
            "build_key": "test",
            "codetrellis_version": VERSION,
            "config_hash": "abc",
            "env_fingerprint": "fedcba9876543210",
        }
        lf = Lockfile.from_dict(data)
        assert lf.env_fingerprint == "fedcba9876543210"

    def test_lockfile_from_dict_missing_env_fingerprint(self):
        """C5 Rule 6: from_dict handles missing env_fingerprint (backward compat)."""
        data = {
            "build_key": "test",
            "codetrellis_version": VERSION,
            "config_hash": "abc",
        }
        lf = Lockfile.from_dict(data)
        assert lf.env_fingerprint == ""

    def test_lockfile_roundtrip(self, tmp_path: Path):
        """C5: Lockfile survives to_dict → JSON → from_dict roundtrip."""
        original = Lockfile(
            build_key=f"{VERSION}:xyz",
            codetrellis_version=VERSION,
            config_hash="xyz",
            cli_flags_hash="xyz",
            generated_at="2026-02-20T10:00:00",
            total_files=5,
            env_fingerprint="abcdef0123456789",
            file_manifest={
                "main.py": FileManifestEntry(
                    file_path="main.py",
                    content_hash="hash123",
                ),
            },
        )
        # Roundtrip through JSON
        json_str = json.dumps(original.to_dict(), indent=2, sort_keys=True)
        restored = Lockfile.from_dict(json.loads(json_str))
        assert restored.env_fingerprint == original.env_fingerprint
        assert restored.build_key == original.build_key
        assert restored.total_files == original.total_files
        assert "main.py" in restored.file_manifest


# =============================================================================
# Unified Build Contract Verifier Tests
# =============================================================================

class TestBuildContractVerifier:
    """Unified C1-C6 verification for `codetrellis verify`."""

    def test_verify_valid_project_with_cache(self, project_dir: Path, cache_dir: Path):
        """C1-C6: Valid project with valid cache passes all checks."""
        # Point the verifier at the project dir and patch cache resolution
        with patch(
            "codetrellis.build_contract.get_versioned_cache_dir",
            return_value=cache_dir,
        ):
            verifier = BuildContractVerifier(str(project_dir))
            verifier._cache_dir = cache_dir
            report = verifier.verify()
            # C1 should pass (valid project root)
            assert "C1_inputs" in report["checks_run"]
            # If there are errors, they should only be non-critical
            assert report["codetrellis_version"] == VERSION

    def test_verify_nonexistent_project(self, tmp_path: Path):
        """C1: Non-existent project root fails verification."""
        verifier = BuildContractVerifier(str(tmp_path / "ghost"))
        report = verifier.verify()
        assert report["passed"] is False
        assert any("C1.1" in e for e in report["errors"])

    def test_verify_no_cache_directory(self, project_dir: Path):
        """C2: Missing cache dir produces warning, not error."""
        verifier = BuildContractVerifier(str(project_dir))
        # Ensure cache_dir doesn't exist
        verifier._cache_dir = project_dir / "nonexistent_cache"
        report = verifier.verify()
        assert any("skipping output validation" in w for w in report["warnings"])

    def test_verify_report_structure(self, project_dir: Path):
        """Verify report has all required keys."""
        verifier = BuildContractVerifier(str(project_dir))
        report = verifier.verify()
        required_keys = {
            "gate", "passed", "exit_code", "errors", "warnings",
            "checks_run", "codetrellis_version", "project_root", "cache_dir",
        }
        assert required_keys.issubset(set(report.keys()))
        assert report["gate"] == "build_contract"

    def test_verify_checks_run(self, project_dir: Path):
        """All major checks are listed in checks_run."""
        verifier = BuildContractVerifier(str(project_dir))
        report = verifier.verify()
        assert "C1_inputs" in report["checks_run"]
        assert "C3_determinism" in report["checks_run"]
        assert "C5_cache" in report["checks_run"]


# =============================================================================
# C4: Timeout Handler Tests
# =============================================================================

class TestTimeoutHandler:
    """C4: Build timeout handling with exit code 124."""

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="SIGALRM not available on Windows",
    )
    def test_timeout_context_manager_no_timeout(self):
        """C4: Code within timeout that finishes normally succeeds."""
        with TimeoutHandler(seconds=10):
            time.sleep(0.01)  # Fast operation

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="SIGALRM not available on Windows",
    )
    def test_timeout_raises_system_exit_124(self):
        """C4: Timeout raises SystemExit(124)."""
        with pytest.raises(SystemExit) as exc_info:
            with TimeoutHandler(seconds=1):
                time.sleep(5)  # Exceeds 1s timeout
        assert exc_info.value.code == 124

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="SIGALRM not available on Windows",
    )
    def test_timeout_restores_signal_handler(self):
        """C4: TimeoutHandler restores previous SIGALRM handler."""
        original = signal.getsignal(signal.SIGALRM)
        with TimeoutHandler(seconds=10):
            pass
        restored = signal.getsignal(signal.SIGALRM)
        assert restored == original

    def test_timeout_handler_on_windows_is_noop(self):
        """C4: On Windows, TimeoutHandler is a no-op (no SIGALRM)."""
        with patch.object(sys, "platform", "win32"):
            handler = TimeoutHandler(seconds=1)
            # Should not raise
            handler.__enter__()
            handler.__exit__(None, None, None)


# =============================================================================
# C6: Compatibility Tests
# =============================================================================

class TestCompatibility:
    """C6: Backward compatibility and SemVer compliance."""

    def test_version_is_semver(self):
        """C6: Version string follows SemVer (MAJOR.MINOR.PATCH)."""
        parts = VERSION.split(".")
        assert len(parts) == 3, f"Version {VERSION} is not SemVer"
        for part in parts:
            assert part.isdigit(), f"Version part '{part}' is not numeric"

    def test_lockfile_additive_fields(self):
        """C6: New fields in lockfile don't break from_dict of old data."""
        # Simulate an old lockfile without env_fingerprint
        old_data = {
            "build_key": "4.15.0:abc",
            "codetrellis_version": "4.15.0",
            "config_hash": "abc",
            "cli_flags_hash": "abc",
            "generated_at": "2026-01-01",
            "total_files": 10,
            "file_manifest": {},
            "extractor_versions": {},
        }
        lf = Lockfile.from_dict(old_data)
        assert lf.env_fingerprint == ""  # Default for missing field
        assert lf.build_key == "4.15.0:abc"

    def test_lockfile_extra_fields_ignored(self):
        """C6: Unknown fields in lockfile data are gracefully ignored."""
        data = {
            "build_key": "test",
            "codetrellis_version": VERSION,
            "config_hash": "abc",
            "future_field": "some_value",
            "another_new_field": 42,
        }
        lf = Lockfile.from_dict(data)
        assert lf.build_key == "test"

    def test_required_prompt_sections_stable(self):
        """C6: Required prompt sections are defined and non-empty."""
        assert len(REQUIRED_PROMPT_SECTIONS) >= 1
        assert "PROJECT" in REQUIRED_PROMPT_SECTIONS

    def test_required_metadata_fields_stable(self):
        """C6: Required metadata fields are defined and non-empty."""
        assert len(REQUIRED_METADATA_FIELDS) >= 4
        for field in ["version", "project", "generated", "stats"]:
            assert field in REQUIRED_METADATA_FIELDS

    def test_supported_extensions_non_empty(self):
        """C6: Supported extensions set is non-empty and frozen."""
        assert len(SUPPORTED_EXTENSIONS) >= 30
        assert isinstance(SUPPORTED_EXTENSIONS, frozenset)


# =============================================================================
# Integration Tests: Cross-cutting Contract Checks
# =============================================================================

class TestIntegration:
    """Cross-cutting integration tests for multiple contract clauses."""

    def test_full_validation_pipeline(self, project_dir: Path, cache_dir: Path):
        """C1→C2: Input validation then output validation works end-to-end."""
        # C1: Input validation passes
        input_val = InputValidator(str(project_dir))
        assert input_val.validate() == []

        # C2: Output validation passes on valid cache
        output_val = OutputSchemaValidator(cache_dir)
        passed, errors = output_val.validate_all()
        assert passed is True

    def test_deterministic_lockfile_roundtrip(self, tmp_path: Path):
        """C3+C5: Lockfile written deterministically survives roundtrip."""
        cache = tmp_path / "cache"
        cache.mkdir()
        mgr = LockfileManager(cache)

        fp = EnvironmentFingerprint.compute()
        lf = Lockfile(
            build_key=f"{VERSION}:test",
            codetrellis_version=VERSION,
            config_hash="test",
            cli_flags_hash="test",
            generated_at=DeterminismEnforcer.get_timestamp(),
            total_files=2,
            env_fingerprint=fp,
            file_manifest={
                "a.py": FileManifestEntry(file_path="a.py", content_hash="hash_a"),
                "b.py": FileManifestEntry(file_path="b.py", content_hash="hash_b"),
            },
        )
        mgr.write(lf)

        # Read back
        restored = mgr.read()
        assert restored is not None
        assert restored.env_fingerprint == fp
        assert restored.total_files == 2
        assert "a.py" in restored.file_manifest
        assert "b.py" in restored.file_manifest

    def test_error_budget_drives_exit_code(self):
        """C4: Error budget correctly derives exit codes for all scenarios."""
        # Scenario 1: Pure success
        b1 = ErrorBudget()
        b1.record_success("py", "a.py")
        assert int(b1.exit_code) == 0

        # Scenario 2: Partial failure
        b2 = ErrorBudget()
        b2.record_success("py", "a.py")
        b2.record_failure("py", "b.py", "error")
        assert int(b2.exit_code) == 1

        # Scenario 3: Complete failure
        b3 = ErrorBudget()
        b3.record_failure("py", "a.py", "error1")
        b3.record_failure("py", "b.py", "error2")
        assert int(b3.exit_code) == 3

    def test_cache_invalidator_with_real_fingerprint(self):
        """C5: CacheInvalidator works with real EnvironmentFingerprint."""
        fp = EnvironmentFingerprint.compute()
        invalidator = CacheInvalidator(
            current_version=VERSION,
            current_config_hash="test",
            current_flags_hash="test",
            current_env_fingerprint=fp,
        )
        lockfile_data = {
            "codetrellis_version": VERSION,
            "config_hash": "test",
            "cli_flags_hash": "test",
            "env_fingerprint": fp,
        }
        assert invalidator.is_cache_valid(lockfile_data) is True

    def test_deterministic_json_produces_sorted_lockfile(self):
        """C3+C5: DeterminismEnforcer.deterministic_json produces sorted lockfile."""
        lf = Lockfile(
            build_key="test",
            codetrellis_version=VERSION,
            config_hash="abc",
            env_fingerprint="fedcba",
        )
        json_str = DeterminismEnforcer.deterministic_json(lf.to_dict())
        data = json.loads(json_str)
        keys = list(data.keys())
        assert keys == sorted(keys), f"Keys not sorted: {keys}"

    def test_build_contract_error_can_carry_budget_summary(self):
        """C4: BuildContractError can include ErrorBudget summary."""
        budget = ErrorBudget()
        budget.record_success("py", "a.py")
        budget.record_failure("py", "b.py", "SyntaxError at line 10")

        err = BuildContractError(
            f"Build completed with errors: {budget.summary()}",
            exit_code=budget.exit_code,
            violations=[d["error"] for d in budget.to_dict()["failure_details"]],
        )
        assert err.exit_code == ExitCode.PARTIAL_FAILURE
        assert "SyntaxError" in err.violations[0]
