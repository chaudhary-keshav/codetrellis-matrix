"""
CodeTrellis Build Contract — Formal I/O Contract for Matrix Generation
=====================================================================

Implements PART C (C1-C6) of the Master Research & Implementation Plan.

C1: Input validation (source files, config, env vars, CLI flags)
C2: Output schema enforcement (matrix.prompt, matrix.json, _metadata.json, _lockfile.json, _build_log.jsonl)
C3: Determinism guarantees (sorted keys, sorted traversal, timestamp control)
C4: Error contract (exit codes 0/1/2/3/124, error budgets, structured reporting)
C5: Cache contract (invalidation rules, hash generation, env fingerprint)
C6: Compatibility (additive fields, SemVer, section header stability)

Author: Keshav Chaudhary
Created: 20 February 2026
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from codetrellis import __version__ as VERSION


__all__ = [
    "ExitCode",
    "BuildContractError",
    "InputValidator",
    "OutputSchemaValidator",
    "DeterminismEnforcer",
    "ErrorBudget",
    "EnvironmentFingerprint",
    "CacheInvalidator",
    "BuildContractVerifier",
    "SUPPORTED_EXTENSIONS",
    "REQUIRED_METADATA_FIELDS",
    "REQUIRED_PROMPT_SECTIONS",
]


# =============================================================================
# C4: Exit Codes
# =============================================================================

class ExitCode(IntEnum):
    """Standardized exit codes per C4 Error Contract.

    | Code | Meaning                                         |
    |------|-------------------------------------------------|
    | 0    | Success — all outputs written                    |
    | 1    | Partial failure — some extractors failed         |
    | 2    | Configuration error                             |
    | 3    | Fatal error — no outputs written                |
    | 41   | JSON-LD validation failed (H1)                  |
    | 42   | Embedding generation failed (H2)                |
    | 43   | JSON Patch integrity mismatch (H3)              |
    | 44   | Compression critical AST node loss (H4)         |
    | 45   | Cross-language orphaned nodes (H5)              |
    | 46   | Navigator query parsing failed (H6)             |
    | 47   | MatrixBench variance exceeded threshold (H7)    |
    | 124  | Timeout                                         |
    """
    SUCCESS = 0
    PARTIAL_FAILURE = 1
    CONFIGURATION_ERROR = 2
    FATAL_ERROR = 3
    # Advanced Research Module exit codes (PART H)
    JSONLD_VALIDATION_FAILED = 41
    EMBEDDING_GENERATION_FAILED = 42
    JSON_PATCH_INTEGRITY_MISMATCH = 43
    COMPRESSION_AST_NODE_LOSS = 44
    CROSS_LANGUAGE_ORPHANED_NODES = 45
    NAVIGATOR_QUERY_PARSE_FAILED = 46
    MATRIXBENCH_VARIANCE_EXCEEDED = 47
    TIMEOUT = 124


# =============================================================================
# C1: Supported Extensions
# =============================================================================

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    # Core languages
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".java", ".kt", ".cs", ".go", ".rs",
    ".rb", ".php", ".scala", ".r",
    ".dart", ".lua", ".ps1",
    ".sh", ".bash",
    ".sql",
    ".swift",
    ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
    # Web
    ".html", ".css", ".scss", ".sass", ".less",
    ".vue", ".svelte", ".astro",
    # Config / data
    ".json", ".yaml", ".yml", ".toml",
    ".proto", ".graphql", ".gql",
})

# =============================================================================
# C1.3: Environment Variables
# =============================================================================

ENV_VARS: Dict[str, Dict[str, str]] = {
    "CODETRELLIS_BUILD_TIMESTAMP": {
        "purpose": "Override generated_at timestamp for deterministic builds",
        "default": "datetime.now().isoformat()",
    },
    "CODETRELLIS_CI": {
        "purpose": "Enable CI mode (deterministic + parallel)",
        "default": "unset",
    },
    "CODETRELLIS_CACHE_DIR": {
        "purpose": "Override cache location",
        "default": ".codetrellis/cache/",
    },
    "JAVA_HOME": {
        "purpose": "Java SDK path for Java/Kotlin parsing",
        "default": "System default",
    },
    "JDT_LS_PATH": {
        "purpose": "Eclipse JDT Language Server path",
        "default": "None",
    },
    "NODE_ENV": {
        "purpose": "Node.js environment",
        "default": "None",
    },
}


# =============================================================================
# C2: Required Output Fields
# =============================================================================

REQUIRED_METADATA_FIELDS: frozenset[str] = frozenset({
    "version", "project", "generated", "stats",
})

REQUIRED_STATS_FIELDS: frozenset[str] = frozenset({
    "totalFiles",
})

REQUIRED_PROMPT_SECTIONS: frozenset[str] = frozenset({
    "PROJECT",
})


# =============================================================================
# C4: Error Contract
# =============================================================================

class BuildContractError(Exception):
    """Raised when a build contract violation is detected.

    Attributes:
        exit_code: The C4 exit code for this error type.
        violations: List of human-readable violation descriptions.
    """

    def __init__(
        self,
        message: str,
        exit_code: ExitCode = ExitCode.FATAL_ERROR,
        violations: Optional[List[str]] = None,
    ) -> None:
        self.exit_code = exit_code
        self.violations = violations or []
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for structured error reporting."""
        return {
            "error": str(self),
            "exit_code": int(self.exit_code),
            "exit_code_name": self.exit_code.name,
            "violations": self.violations,
            "timestamp": datetime.now().isoformat(),
        }


# =============================================================================
# C1: Input Validator
# =============================================================================

class InputValidator:
    """Validates all inputs per C1 (Source Files, Config, Env Vars, CLI Flags).

    Usage:
        validator = InputValidator(project_root="/path/to/project")
        errors = validator.validate()
        if errors:
            raise BuildContractError("Input validation failed", ExitCode.CONFIGURATION_ERROR, errors)
    """

    def __init__(self, project_root: str) -> None:
        self._root = Path(project_root).resolve()

    def validate(self) -> List[str]:
        """Run all input validations.

        Returns:
            List of validation error messages (empty = valid).
        """
        errors: List[str] = []
        errors.extend(self._validate_project_root())
        errors.extend(self._validate_config())
        errors.extend(self._validate_env_vars())
        return errors

    def _validate_project_root(self) -> List[str]:
        """C1.1: Validate the project root directory exists and is readable."""
        errors: List[str] = []
        if not self._root.exists():
            errors.append(f"C1.1: Project root does not exist: {self._root}")
        elif not self._root.is_dir():
            errors.append(f"C1.1: Project root is not a directory: {self._root}")
        elif not os.access(str(self._root), os.R_OK):
            errors.append(f"C1.1: Project root is not readable: {self._root}")
        return errors

    def _validate_config(self) -> List[str]:
        """C1.2: Validate .codetrellis/config.json if it exists."""
        errors: List[str] = []
        config_path = self._root / ".codetrellis" / "config.json"
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    errors.append("C1.2: config.json must be a JSON object")
            except json.JSONDecodeError as exc:
                errors.append(f"C1.2: config.json is invalid JSON: {exc}")
            except (PermissionError, OSError) as exc:
                errors.append(f"C1.2: Cannot read config.json: {exc}")
        # config.json is auto-created if missing, so absence is NOT an error
        return errors

    def _validate_env_vars(self) -> List[str]:
        """C1.3: Validate environment variable values (where applicable)."""
        errors: List[str] = []
        ts = os.environ.get("CODETRELLIS_BUILD_TIMESTAMP")
        if ts and ts != "deterministic":
            try:
                datetime.fromisoformat(ts)
            except (ValueError, TypeError):
                errors.append(
                    f"C1.3: CODETRELLIS_BUILD_TIMESTAMP is not a valid ISO 8601 timestamp: {ts!r}"
                )

        cache_dir = os.environ.get("CODETRELLIS_CACHE_DIR")
        if cache_dir:
            cache_path = Path(cache_dir)
            if cache_path.exists() and not cache_path.is_dir():
                errors.append(
                    f"C1.3: CODETRELLIS_CACHE_DIR exists but is not a directory: {cache_dir}"
                )

        return errors

    @staticmethod
    def is_supported_extension(ext: str) -> bool:
        """C1.1: Check if a file extension is in the supported set."""
        return ext.lower() in SUPPORTED_EXTENSIONS


# =============================================================================
# C2: Output Schema Validator
# =============================================================================

class OutputSchemaValidator:
    """Validates output artifacts per C2 (Required Outputs + Schema).

    Usage:
        validator = OutputSchemaValidator(cache_dir)
        passed, errors = validator.validate_all()
    """

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir

    def validate_all(self) -> Tuple[bool, List[str]]:
        """Validate all required outputs.

        Returns:
            (passed: bool, errors: list[str])
        """
        errors: List[str] = []
        errors.extend(self._validate_required_files())
        errors.extend(self._validate_matrix_prompt())
        errors.extend(self._validate_matrix_json())
        errors.extend(self._validate_metadata_json())
        errors.extend(self._validate_lockfile())
        return (len(errors) == 0, errors)

    def _validate_required_files(self) -> List[str]:
        """C2.1: Required output files exist and are non-empty."""
        errors: List[str] = []
        for fname in ["matrix.prompt", "matrix.json", "_metadata.json"]:
            fpath = self._cache_dir / fname
            if not fpath.exists():
                errors.append(f"C2.1: MISSING required output: {fname}")
            elif fpath.stat().st_size == 0:
                errors.append(f"C2.1: EMPTY required output: {fname}")
            elif fname == "matrix.prompt" and fpath.stat().st_size < 100:
                errors.append("C2.1: matrix.prompt too small (<100 bytes)")
        return errors

    def _validate_matrix_prompt(self) -> List[str]:
        """C2.1: matrix.prompt is UTF-8, has required section headers."""
        errors: List[str] = []
        fpath = self._cache_dir / "matrix.prompt"
        if not fpath.exists():
            return errors  # Already reported by _validate_required_files

        try:
            content = fpath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append("C2.1: matrix.prompt is not valid UTF-8")
            return errors

        for section in REQUIRED_PROMPT_SECTIONS:
            if f"[{section}]" not in content:
                errors.append(f"C2.1: matrix.prompt missing required section: [{section}]")

        return errors

    def _validate_matrix_json(self) -> List[str]:
        """C2.1: matrix.json is valid JSON with sorted keys."""
        errors: List[str] = []
        fpath = self._cache_dir / "matrix.json"
        if not fpath.exists():
            return errors

        try:
            content = fpath.read_text(encoding="utf-8")
            data = json.loads(content)
            if not isinstance(data, dict):
                errors.append("C2.1: matrix.json root must be a JSON object")
            else:
                # C3: Verify sorted keys at top level
                keys = list(data.keys())
                if keys != sorted(keys):
                    errors.append("C2.1/C3: matrix.json top-level keys are not sorted")
        except json.JSONDecodeError as exc:
            errors.append(f"C2.1: matrix.json is invalid JSON: {exc}")

        return errors

    def _validate_metadata_json(self) -> List[str]:
        """C2.1: _metadata.json has required fields, valid structure."""
        errors: List[str] = []
        fpath = self._cache_dir / "_metadata.json"
        if not fpath.exists():
            return errors

        try:
            content = fpath.read_text(encoding="utf-8")
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            errors.append(f"C2.1: _metadata.json is invalid JSON: {exc}")
            return errors

        if not isinstance(data, dict):
            errors.append("C2.1: _metadata.json root must be a JSON object")
            return errors

        # Check required fields
        for req in REQUIRED_METADATA_FIELDS:
            if req not in data:
                errors.append(f"C2.1: _metadata.json missing required field: {req}")

        # Check stats sub-fields
        stats = data.get("stats", {})
        if isinstance(stats, dict):
            for req in REQUIRED_STATS_FIELDS:
                if req not in stats:
                    errors.append(f"C2.1: _metadata.json.stats missing required field: {req}")
            if stats.get("totalFiles", 0) == 0:
                errors.append("C2.1: _metadata.json.stats.totalFiles is 0 (no files scanned)")

        # Version must match running version
        meta_version = data.get("version")
        if meta_version and meta_version != VERSION:
            errors.append(
                f"C2.1: _metadata.json version mismatch: "
                f"metadata={meta_version}, running={VERSION}"
            )

        # Sorted keys
        keys = list(data.keys())
        if keys != sorted(keys):
            errors.append("C2.1/C3: _metadata.json top-level keys are not sorted")

        return errors

    def _validate_lockfile(self) -> List[str]:
        """C2.2: _lockfile.json (optional) is valid if present."""
        errors: List[str] = []
        fpath = self._cache_dir / "_lockfile.json"
        if not fpath.exists():
            return errors  # Optional in Phase 1+

        try:
            content = fpath.read_text(encoding="utf-8")
            data = json.loads(content)
            if not isinstance(data, dict):
                errors.append("C2.2: _lockfile.json root must be a JSON object")
            else:
                for req in ["build_key", "codetrellis_version", "config_hash"]:
                    if req not in data:
                        errors.append(f"C2.2: _lockfile.json missing field: {req}")
                # Sorted keys
                keys = list(data.keys())
                if keys != sorted(keys):
                    errors.append("C2.2/C3: _lockfile.json top-level keys are not sorted")
        except json.JSONDecodeError as exc:
            errors.append(f"C2.2: _lockfile.json is invalid JSON: {exc}")

        return errors


# =============================================================================
# C3: Determinism Enforcer
# =============================================================================

class DeterminismEnforcer:
    """Enforces determinism guarantees per C3.

    Provides utilities for ensuring byte-identical output across runs.

    Usage:
        enforcer = DeterminismEnforcer()
        json_str = enforcer.deterministic_json(data)
        timestamp = enforcer.get_timestamp()
    """

    @staticmethod
    def deterministic_json(data: Any, indent: int = 2) -> str:
        """Serialize to JSON with sorted keys and str default.

        C3 requirement 2: json.dumps(..., sort_keys=True, default=str)
        C3 requirement 4: Convert sets to sorted lists.

        Args:
            data: Data to serialize.
            indent: JSON indentation level.

        Returns:
            Deterministic JSON string.
        """
        prepared = DeterminismEnforcer._prepare_for_json(data)
        return json.dumps(prepared, indent=indent, sort_keys=True, default=str)

    @staticmethod
    def _prepare_for_json(obj: Any) -> Any:
        """C3 requirement 4: Convert sets/frozensets to sorted lists recursively."""
        if isinstance(obj, (set, frozenset)):
            return sorted(str(item) for item in obj)
        elif isinstance(obj, dict):
            return {
                k: DeterminismEnforcer._prepare_for_json(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, (list, tuple)):
            return [DeterminismEnforcer._prepare_for_json(item) for item in obj]
        return obj

    @staticmethod
    def get_timestamp() -> str:
        """Get deterministic timestamp per C3 requirement 3.

        Returns CODETRELLIS_BUILD_TIMESTAMP if set, else datetime.now().isoformat().
        """
        return os.environ.get(
            "CODETRELLIS_BUILD_TIMESTAMP",
            datetime.now().isoformat(),
        )

    @staticmethod
    def sorted_file_walk(root: Path) -> List[Path]:
        """C3 requirement 1: sorted(Path.rglob(...)) for file traversal.

        Returns:
            Sorted list of file paths.
        """
        return sorted(root.rglob("*"))

    @staticmethod
    def file_hash(file_path: str) -> str:
        """C3 requirement 5: SHA-256 consistently (not MD5).

        Returns:
            First 16 hex chars of SHA-256 digest.
        """
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()[:16]

    @staticmethod
    def content_hash(content: str) -> str:
        """SHA-256 of string content (first 16 hex chars)."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def verify_determinism(file_a: Path, file_b: Path) -> Tuple[bool, str]:
        """Verify two files are byte-identical.

        Args:
            file_a: First file path.
            file_b: Second file path.

        Returns:
            (identical: bool, detail: str)
        """
        if not file_a.exists() or not file_b.exists():
            return False, "One or both files do not exist"

        hash_a = hashlib.sha256(file_a.read_bytes()).hexdigest()
        hash_b = hashlib.sha256(file_b.read_bytes()).hexdigest()

        if hash_a == hash_b:
            return True, f"SHA-256 match: {hash_a}"
        else:
            return False, f"SHA-256 mismatch: {hash_a} != {hash_b}"


# =============================================================================
# C4: Error Budget
# =============================================================================

@dataclass
class ErrorBudget:
    """Tracks extractor failures to determine exit code per C4.

    Per C4 Retry Policy:
    - File read error → skip file, log warning
    - Extractor exception → catch, log, continue with others
    - If ALL extractors succeed → exit 0
    - If SOME fail → exit 1 (partial failure)
    - If config is invalid → exit 2
    - If fatal error → exit 3

    Usage:
        budget = ErrorBudget()
        budget.record_success("python_parser", "cli.py")
        budget.record_failure("python_parser", "broken.py", "SyntaxError")
        exit_code = budget.exit_code
    """
    _successes: List[Dict[str, str]] = field(default_factory=list)
    _failures: List[Dict[str, str]] = field(default_factory=list)
    _skipped: List[Dict[str, str]] = field(default_factory=list)
    _warnings: List[Dict[str, str]] = field(default_factory=list)

    def record_success(self, extractor: str, file_path: str) -> None:
        """Record a successful extraction."""
        self._successes.append({"extractor": extractor, "file": file_path})

    def record_failure(
        self, extractor: str, file_path: str, error: str
    ) -> None:
        """Record an extractor failure."""
        self._failures.append({
            "extractor": extractor,
            "file": file_path,
            "error": error,
        })

    def record_skip(self, file_path: str, reason: str) -> None:
        """Record a skipped file (e.g., read error)."""
        self._skipped.append({"file": file_path, "reason": reason})

    def record_warning(self, message: str, file_path: str = "") -> None:
        """Record a warning."""
        self._warnings.append({"message": message, "file": file_path})

    @property
    def exit_code(self) -> ExitCode:
        """Compute the C4 exit code based on recorded results.

        Returns:
            ExitCode.SUCCESS if no failures,
            ExitCode.PARTIAL_FAILURE if some extractors failed,
            ExitCode.FATAL_ERROR if all extractors failed with no successes.
        """
        if not self._failures:
            return ExitCode.SUCCESS
        if self._successes:
            return ExitCode.PARTIAL_FAILURE
        return ExitCode.FATAL_ERROR

    @property
    def total_successes(self) -> int:
        """Number of successful extractions."""
        return len(self._successes)

    @property
    def total_failures(self) -> int:
        """Number of failed extractions."""
        return len(self._failures)

    @property
    def total_skipped(self) -> int:
        """Number of skipped files."""
        return len(self._skipped)

    @property
    def total_warnings(self) -> int:
        """Number of warnings."""
        return len(self._warnings)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for structured error reporting and _build_log.jsonl."""
        return {
            "successes": self.total_successes,
            "failures": self.total_failures,
            "skipped": self.total_skipped,
            "warnings": self.total_warnings,
            "exit_code": int(self.exit_code),
            "exit_code_name": self.exit_code.name,
            "failure_details": self._failures,
            "skip_details": self._skipped,
            "warning_details": self._warnings,
        }

    def summary(self) -> str:
        """Human-readable summary."""
        parts = [
            f"✓ {self.total_successes} succeeded",
            f"✗ {self.total_failures} failed",
        ]
        if self.total_skipped:
            parts.append(f"⊘ {self.total_skipped} skipped")
        if self.total_warnings:
            parts.append(f"⚠ {self.total_warnings} warnings")
        parts.append(f"→ exit {int(self.exit_code)}")
        return ", ".join(parts)


# =============================================================================
# C5: Environment Fingerprint
# =============================================================================

class EnvironmentFingerprint:
    """Computes an environment fingerprint for cache invalidation per C5.

    C5 Invalidation Rule 6: Environment fingerprint changes invalidate cache.
    Captures: Python version, OS, CodeTrellis version, relevant env vars.
    """

    @staticmethod
    def compute() -> str:
        """Compute a deterministic fingerprint of the current environment.

        Returns:
            First 16 hex chars of the SHA-256 digest of the fingerprint.
        """
        parts = [
            f"python={sys.version}",
            f"platform={sys.platform}",
            f"codetrellis={VERSION}",
        ]
        # Include relevant env vars that affect output
        for var in sorted(ENV_VARS.keys()):
            val = os.environ.get(var, "")
            if val:
                parts.append(f"{var}={val}")

        fingerprint = "|".join(parts)
        return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def to_dict() -> Dict[str, Any]:
        """Return the fingerprint components for debugging/logging."""
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "codetrellis_version": VERSION,
            "env_vars": {
                var: os.environ.get(var, "")
                for var in sorted(ENV_VARS.keys())
                if os.environ.get(var)
            },
        }


# =============================================================================
# C5: Cache Invalidator
# =============================================================================

class CacheInvalidator:
    """Determines whether cached results are valid per C5 Invalidation Rules.

    A cached result is INVALID when any of these change:
    1. File content hash differs from lockfile
    2. CodeTrellis version changes
    3. .codetrellis/config.json hash changes
    4. CLI flags change
    5. Extractor version changes
    6. Environment fingerprint changes

    Usage:
        invalidator = CacheInvalidator(
            current_version=VERSION,
            current_config_hash="abc123",
            current_flags_hash="def456",
            current_env_fingerprint=EnvironmentFingerprint.compute(),
        )
        is_valid = invalidator.is_cache_valid(lockfile)
        reasons = invalidator.invalidation_reasons(lockfile)
    """

    def __init__(
        self,
        current_version: str,
        current_config_hash: str,
        current_flags_hash: str,
        current_env_fingerprint: str,
    ) -> None:
        self._version = current_version
        self._config_hash = current_config_hash
        self._flags_hash = current_flags_hash
        self._env_fingerprint = current_env_fingerprint

    def is_cache_valid(self, lockfile_data: Dict[str, Any]) -> bool:
        """Check if cached results are still valid.

        Args:
            lockfile_data: Parsed _lockfile.json dict.

        Returns:
            True if cache is valid, False if invalidated.
        """
        return len(self.invalidation_reasons(lockfile_data)) == 0

    def invalidation_reasons(self, lockfile_data: Dict[str, Any]) -> List[str]:
        """List reasons why the cache is invalid.

        Args:
            lockfile_data: Parsed _lockfile.json dict.

        Returns:
            List of invalidation reason strings (empty = valid).
        """
        reasons: List[str] = []

        # Rule 2: Version change
        lf_version = lockfile_data.get("codetrellis_version", "")
        if lf_version != self._version:
            reasons.append(
                f"C5 Rule 2: Version changed ({lf_version} → {self._version})"
            )

        # Rule 3: Config hash change
        lf_config_hash = lockfile_data.get("config_hash", "")
        if lf_config_hash != self._config_hash:
            reasons.append(
                f"C5 Rule 3: Config hash changed ({lf_config_hash} → {self._config_hash})"
            )

        # Rule 4: CLI flags change
        lf_flags_hash = lockfile_data.get("cli_flags_hash", "")
        if lf_flags_hash != self._flags_hash:
            reasons.append(
                f"C5 Rule 4: CLI flags changed ({lf_flags_hash} → {self._flags_hash})"
            )

        # Rule 6: Environment fingerprint change
        lf_env = lockfile_data.get("env_fingerprint", "")
        if lf_env and lf_env != self._env_fingerprint:
            reasons.append(
                f"C5 Rule 6: Environment fingerprint changed ({lf_env} → {self._env_fingerprint})"
            )

        return reasons


# =============================================================================
# C5: Cache Directory Resolution
# =============================================================================

def get_cache_base_dir(project_root: Path) -> Path:
    """Resolve the cache base directory, respecting CODETRELLIS_CACHE_DIR.

    Per C1.3: CODETRELLIS_CACHE_DIR overrides the default location.

    Args:
        project_root: Project root directory.

    Returns:
        Path to the cache base directory.
    """
    env_cache_dir = os.environ.get("CODETRELLIS_CACHE_DIR")
    if env_cache_dir:
        return Path(env_cache_dir)
    return project_root / ".codetrellis" / "cache"


def get_versioned_cache_dir(project_root: Path) -> Path:
    """Get the full versioned cache directory for a project.

    Structure: {cache_base}/{VERSION}/{project_name}/

    Args:
        project_root: Project root directory.

    Returns:
        Path to the versioned project cache directory.
    """
    cache_base = get_cache_base_dir(project_root)
    project_name = project_root.resolve().name
    return cache_base / VERSION / project_name


# =============================================================================
# C5: Cache Eviction
# =============================================================================

def get_config_hash(project_root: Path) -> str:
    """Compute hash of .codetrellis/config.json for C5 Rule 3.

    Args:
        project_root: Project root directory.

    Returns:
        First 16 hex chars of SHA-256, or empty string if no config.
    """
    config_path = project_root / ".codetrellis" / "config.json"
    if config_path.exists():
        try:
            content = config_path.read_text(encoding="utf-8")
            return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        except (PermissionError, OSError):
            return ""
    return ""


# =============================================================================
# Unified Build Contract Verifier
# =============================================================================

class BuildContractVerifier:
    """Unified verifier that checks all C1-C6 contract clauses.

    Designed for use by:
    - `codetrellis verify` CLI command (D1 quality gate)
    - CI/CD pipelines
    - Post-build validation in MatrixBuilder

    Usage:
        verifier = BuildContractVerifier(project_root="/path/to/project")
        report = verifier.verify()
        if not report["passed"]:
            for error in report["errors"]:
                print(f"  FAIL: {error}")
            sys.exit(report["exit_code"])
    """

    def __init__(self, project_root: str) -> None:
        self._root = Path(project_root).resolve()
        self._cache_dir = get_versioned_cache_dir(self._root)

    def verify(self) -> Dict[str, Any]:
        """Run all contract verifications.

        Returns:
            Dict with: passed, exit_code, errors, warnings, checks_run,
                       input_validation, output_validation, determinism_checks.
        """
        all_errors: List[str] = []
        all_warnings: List[str] = []
        checks_run: List[str] = []

        # C1: Input validation
        checks_run.append("C1_inputs")
        input_val = InputValidator(str(self._root))
        input_errors = input_val.validate()
        all_errors.extend(input_errors)

        # C2: Output validation (only if cache dir exists)
        if self._cache_dir.exists():
            checks_run.append("C2_outputs")
            output_val = OutputSchemaValidator(self._cache_dir)
            _, output_errors = output_val.validate_all()
            all_errors.extend(output_errors)
        else:
            all_warnings.append("C2: No cache directory found — skipping output validation")

        # C3: Determinism spot-checks
        checks_run.append("C3_determinism")
        determ_errors = self._check_determinism()
        all_errors.extend(determ_errors)

        # C5: Cache contract
        checks_run.append("C5_cache")
        cache_errors = self._check_cache_contract()
        all_errors.extend(cache_errors)

        passed = len(all_errors) == 0
        exit_code = ExitCode.SUCCESS if passed else ExitCode.PARTIAL_FAILURE

        return {
            "gate": "build_contract",
            "passed": passed,
            "exit_code": int(exit_code),
            "errors": all_errors,
            "warnings": all_warnings,
            "checks_run": checks_run,
            "codetrellis_version": VERSION,
            "project_root": str(self._root),
            "cache_dir": str(self._cache_dir),
        }

    def _check_determinism(self) -> List[str]:
        """C3: Spot-check determinism guarantees on existing outputs."""
        errors: List[str] = []
        for fname in ["matrix.json", "_metadata.json", "_lockfile.json"]:
            fpath = self._cache_dir / fname
            if fpath.exists():
                try:
                    content = fpath.read_text(encoding="utf-8")
                    data = json.loads(content)
                    if isinstance(data, dict):
                        keys = list(data.keys())
                        if keys != sorted(keys):
                            errors.append(
                                f"C3: {fname} top-level keys are not sorted"
                            )
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass  # JSON errors reported by C2
        return errors

    def _check_cache_contract(self) -> List[str]:
        """C5: Verify cache structure compliance."""
        errors: List[str] = []
        cache_base = get_cache_base_dir(self._root)
        if cache_base.exists():
            # Check versioned structure
            for version_dir in cache_base.iterdir():
                if version_dir.is_dir():
                    for project_dir in version_dir.iterdir():
                        if project_dir.is_dir():
                            # Verify no unexpected files at top level
                            expected = {
                                "matrix.prompt", "matrix.json", "_metadata.json",
                                "_lockfile.json", "_build_log.jsonl", "_extractor_cache",
                                "files",  # Legacy scanner extractor cache
                            }
                            for item in project_dir.iterdir():
                                if item.name not in expected and not item.name.startswith("."):
                                    errors.append(
                                        f"C5: Unexpected file in cache: {item.name}"
                                    )
        return errors


# =============================================================================
# C4: Timeout Handler
# =============================================================================

class TimeoutHandler:
    """Handles build timeouts per C4 (exit code 124).

    Usage:
        with TimeoutHandler(seconds=300):
            run_build()
        # Raises SystemExit(124) on timeout
    """

    def __init__(self, seconds: int = 300) -> None:
        self._seconds = seconds
        self._old_handler = None

    def __enter__(self) -> "TimeoutHandler":
        if sys.platform != "win32":
            self._old_handler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, self._handle_timeout)
            signal.alarm(self._seconds)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if sys.platform != "win32":
            signal.alarm(0)
            if self._old_handler is not None:
                signal.signal(signal.SIGALRM, self._old_handler)
        return False

    def _handle_timeout(self, signum: int, frame: Any) -> None:
        """Raise SystemExit with C4 timeout exit code."""
        raise SystemExit(int(ExitCode.TIMEOUT))
