"""
CodeTrellis MatrixBuilder — Incremental Build Pipeline Orchestrator
=================================================================

Per PART B (B3-B4) of the Master Plan:
- MatrixBuilder replaces the monolithic scanner.scan() → compressor.compress() flow
- Manages targets: SCAN, COMPILE, VERIFY, PACKAGE
- Wires CacheManager + LockfileManager for incremental builds
- Produces identical output to the legacy pipeline (parity requirement)

Architecture (B3.2):
    CLI → MatrixBuilder → DAG Scheduler → Extractors → CacheManager
                        → Compressor → Output files

Author: Keshav Chaudhary
Created: 20 February 2026
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from codetrellis import __version__ as VERSION
from codetrellis.cache import (
    CacheManager,
    DiffEngine,
    DiffResult,
    InputHashCalculator,
    Lockfile,
    FileManifestEntry,
    LockfileManager,
)
from codetrellis.interfaces import (
    BuildEvent,
    BuildResult,
    OutputTier,
)
from codetrellis.build_contract import (
    ExitCode,
    InputValidator,
    OutputSchemaValidator,
    DeterminismEnforcer,
    ErrorBudget,
    EnvironmentFingerprint,
    CacheInvalidator,
    get_config_hash,
    get_versioned_cache_dir,
)


__all__ = ["MatrixBuilder", "BuildConfig"]


# =============================================================================
# BuildConfig — Captures all build parameters
# =============================================================================

@dataclass
class BuildConfig:
    """Configuration for a single build invocation.

    Captures all CLI flags and settings so they can be hashed
    for cache invalidation (C5 Invalidation Rule 4).
    """
    tier: OutputTier = OutputTier.PROMPT
    deep: bool = False
    parallel: bool = False
    max_workers: Optional[int] = None
    include_progress: bool = False
    include_overview: bool = False
    include_practices: bool = False
    practices_level: Optional[str] = None
    practices_categories: Optional[List[str]] = None
    practices_format: str = "standard"
    max_practice_tokens: Optional[int] = None
    cache_optimize: bool = False
    incremental: bool = False
    deterministic: bool = False
    ci: bool = False
    # Watcher-supplied list of changed file paths (absolute) — enables
    # true incremental builds that only re-extract these files instead of
    # doing a full project scan.  Inspired by Angular's SourceFileCache.
    changed_files: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for hashing."""
        return {
            "tier": self.tier.value,
            "deep": self.deep,
            "parallel": self.parallel,
            "max_workers": self.max_workers,
            "include_progress": self.include_progress,
            "include_overview": self.include_overview,
            "include_practices": self.include_practices,
            "practices_level": self.practices_level,
            "practices_categories": sorted(self.practices_categories) if self.practices_categories else None,
            "practices_format": self.practices_format,
            "max_practice_tokens": self.max_practice_tokens,
            "cache_optimize": self.cache_optimize,
        }

    def flags_hash(self) -> str:
        """Compute a hash of all build-relevant flags."""
        return InputHashCalculator.hash_config(self.to_dict())


# =============================================================================
# Build Logger — Structured JSONL logging
# =============================================================================

class BuildLogger:
    """Writes structured build events to _build_log.jsonl.

    Per C2.2: Each line is a JSON object with timestamp, level, event,
    extractor, duration_ms, and message.
    """

    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        self._events: List[BuildEvent] = []

    def log(self, event: BuildEvent) -> None:
        """Append a build event."""
        self._events.append(event)

    def info(self, event_type: str, message: str = "", **kwargs: Any) -> None:
        """Log an info-level event."""
        self.log(BuildEvent(
            timestamp=datetime.now().isoformat(),
            level="info",
            event=event_type,
            message=message,
            **kwargs,
        ))

    def warn(self, event_type: str, message: str = "", **kwargs: Any) -> None:
        """Log a warning-level event."""
        self.log(BuildEvent(
            timestamp=datetime.now().isoformat(),
            level="warn",
            event=event_type,
            message=message,
            **kwargs,
        ))

    def error(self, event_type: str, message: str = "", **kwargs: Any) -> None:
        """Log an error-level event."""
        self.log(BuildEvent(
            timestamp=datetime.now().isoformat(),
            level="error",
            event=event_type,
            message=message,
            **kwargs,
        ))

    def flush(self) -> None:
        """Write all buffered events to disk."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._log_path, "a", encoding="utf-8") as f:
            for evt in self._events:
                f.write(evt.to_json() + "\n")
        self._events.clear()

    @property
    def events(self) -> List[BuildEvent]:
        """Return all buffered events."""
        return list(self._events)


# =============================================================================
# MatrixBuilder — The orchestrator
# =============================================================================

class MatrixBuilder:
    """Orchestrates the full matrix build pipeline.

    Per B3.2: Acts as the "Builder/Executor" (Angular concept mapping).
    Replaces the direct cli.py → scanner.scan() → compressor.compress() flow
    with a structured pipeline that supports caching, incremental builds,
    and structured logging.

    Lifecycle:
        1. SCAN — Walk files, compute hashes, diff against lockfile
        2. EXTRACT — Run extractors (only on changed files if incremental)
        3. COMPILE — Compress matrix into prompt format
        4. PACKAGE — Write outputs (matrix.prompt, matrix.json, _metadata.json, _lockfile.json)

    Usage:
        builder = MatrixBuilder(project_root="/path/to/project")
        result = builder.build(config=BuildConfig(tier=OutputTier.LOGIC, incremental=True))
        print(result.exit_code)
    """

    def __init__(self, project_root: str) -> None:
        """Initialize the builder.

        Args:
            project_root: Absolute path to the project root
        """
        self._project_root = Path(project_root).resolve()
        self._project_name = self._project_root.name
        self._hasher = InputHashCalculator()
        self._diff_engine = DiffEngine(self._hasher)

    def _get_cache_dir(self) -> Path:
        """Get the versioned cache directory."""
        return (
            self._project_root / ".codetrellis" / "cache" / self._project_name
        )

    def _get_build_timestamp(self) -> str:
        """Get the build timestamp, respecting CODETRELLIS_BUILD_TIMESTAMP."""
        return os.environ.get(
            "CODETRELLIS_BUILD_TIMESTAMP", datetime.now().isoformat()
        )

    def build(self, config: Optional[BuildConfig] = None) -> BuildResult:
        """Execute the full build pipeline.

        Per C4 Error Contract, returns standardized exit codes:
        - 0: Success — all outputs written
        - 1: Partial failure — some extractors failed
        - 2: Configuration error
        - 3: Fatal error — no outputs written

        Args:
            config: Build configuration (defaults to BuildConfig())

        Returns:
            BuildResult with all outputs and metrics
        """
        config = config or BuildConfig()
        start_time = time.time()
        error_budget = ErrorBudget()

        # Handle CI mode: force deterministic + parallel
        if config.ci:
            config.deterministic = True
            config.parallel = True

        # Handle deterministic mode: force timestamp
        if config.deterministic and not os.environ.get("CODETRELLIS_BUILD_TIMESTAMP"):
            os.environ["CODETRELLIS_BUILD_TIMESTAMP"] = "deterministic"

        # C1: Input validation
        input_validator = InputValidator(str(self._project_root))
        input_errors = input_validator.validate()
        if input_errors:
            duration = (time.time() - start_time) * 1000
            return BuildResult(
                success=False,
                exit_code=int(ExitCode.CONFIGURATION_ERROR),
                duration_ms=duration,
                errors=input_errors,
            )

        cache_dir = self._get_cache_dir()
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize subsystems
        cache_mgr = CacheManager(cache_dir, VERSION)
        lockfile_mgr = LockfileManager(cache_dir)
        logger = BuildLogger(cache_dir / "_build_log.jsonl")

        logger.info("build_start", f"Building {self._project_name} v{VERSION}")

        errors: List[str] = []
        warnings: List[str] = []

        # C5 Rule 6: Compute environment fingerprint
        env_fingerprint = EnvironmentFingerprint.compute()

        try:
            # ─── Phase 1: SCAN — Walk files and compute hashes ───
            logger.info("scan_start", "Walking project files")
            current_files = self._scan_files()
            logger.info("scan_complete", f"Found {len(current_files)} files")

            # ─── Phase 2: DIFF — Compare against lockfile ───
            prev_lockfile = lockfile_mgr.read() if config.incremental else None
            diff = self._diff_engine.diff(current_files, prev_lockfile)

            if config.incremental and prev_lockfile:
                logger.info("diff_complete", diff.summary())
                if not diff.has_changes:
                    logger.info("no_changes", "No changes detected — skipping extraction")
                    # Return cached result
                    duration = (time.time() - start_time) * 1000
                    logger.info("build_complete", f"No changes. Duration: {duration:.0f}ms")
                    logger.flush()
                    return BuildResult(
                        success=True,
                        exit_code=0,
                        matrix_json_path=str(cache_dir / "matrix.json"),
                        matrix_prompt_path=str(cache_dir / "matrix.prompt"),
                        metadata_path=str(cache_dir / "_metadata.json"),
                        lockfile_path=str(lockfile_mgr.lockfile_path),
                        build_log_path=str(cache_dir / "_build_log.jsonl"),
                        total_files=diff.total_files,
                        extractors_run=0,
                        cache_hits=len(diff.unchanged_files),
                        cache_misses=0,
                        duration_ms=duration,
                    )

            # ─── Phase 3: EXTRACT — Run extraction pipeline ───
            logger.info("extract_start", "Running extraction pipeline")

            from codetrellis.scanner import ProjectScanner
            from codetrellis.compressor import MatrixCompressor

            # Always run the full scanner pipeline.  The scanner has its own
            # per-file content-hash cache (see _parse_file_cached) so unchanged
            # files are skipped automatically — giving us incremental speed
            # without the risk of losing data in a JSON → ProjectMatrix
            # round-trip.  The watcher already batches changes (2s debounce)
            # so we only rebuild once per batch.
            scanner = ProjectScanner(
                parallel=config.parallel,
                max_workers=config.max_workers,
            )

            # Pass changed_files hint to scanner for per-file cache bypass
            if config.incremental and config.changed_files:
                scanner._changed_files_hint = {
                    str(Path(f).resolve()) for f in config.changed_files
                }

            matrix = scanner.scan(str(self._project_root))
            extractors_run = len(current_files)

            # C4: Track extraction results in error budget
            if hasattr(matrix, 'errors') and matrix.errors:
                for err in matrix.errors:
                    error_budget.record_failure("scanner", "", str(err))
                    errors.append(str(err))
            # Record successes for all processed files
            for _ in range(extractors_run):
                error_budget.record_success("scanner", "")

            # ─── Phase 4: COMPILE — Compress to prompt format ───
            logger.info("compile_start", "Compressing matrix")
            compressor = MatrixCompressor(tier=config.tier)
            compressed = compressor.compress(matrix)

            # Apply post-processing (deep, progress, overview, practices, cache-optimize)
            compressed = self._apply_post_processing(compressed, matrix, config)

            # ─── Phase 5: PACKAGE — Write all outputs ───
            logger.info("package_start", "Writing outputs")

            build_ts = self._get_build_timestamp()

            # Write matrix.prompt
            prompt_path = cache_dir / "matrix.prompt"
            prompt_path.write_text(compressed, encoding="utf-8")

            # Write matrix.json
            json_path = cache_dir / "matrix.json"
            json_path.write_text(
                json.dumps(matrix.to_dict(), indent=2, sort_keys=True, default=str),
                encoding="utf-8",
            )

            # Write _metadata.json
            meta_path = cache_dir / "_metadata.json"
            metadata = {
                "version": VERSION,
                "project": self._project_name,
                "generated": build_ts,
                "build_config": config.to_dict(),
                "stats": {
                    "totalFiles": matrix.total_files,
                    "schemas": len(matrix.schemas),
                    "dtos": len(matrix.dtos),
                    "controllers": len(matrix.controllers),
                    "components": len(matrix.components),
                    "services": len(matrix.services),
                    "interfaces": len(matrix.interfaces),
                    "types": len(matrix.types),
                },
                "cache_stats": cache_mgr.get_stats(),
            }
            meta_path.write_text(
                json.dumps(metadata, indent=2, sort_keys=True, default=str),
                encoding="utf-8",
            )

            # Write _lockfile.json
            new_lockfile = Lockfile(
                build_key=f"{VERSION}:{config.flags_hash()}",
                codetrellis_version=VERSION,
                config_hash=config.flags_hash(),
                cli_flags_hash=config.flags_hash(),
                generated_at=build_ts,
                total_files=len(current_files),
                env_fingerprint=env_fingerprint,
                file_manifest={
                    rel_path: FileManifestEntry(
                        file_path=rel_path,
                        content_hash=content_hash,
                    )
                    for rel_path, content_hash in current_files.items()
                },
            )
            lockfile_mgr.write(new_lockfile)

            duration = (time.time() - start_time) * 1000
            logger.info("build_complete", f"Build complete. Duration: {duration:.0f}ms")
            logger.flush()

            # C4: Derive exit code from error budget
            exit_code = int(error_budget.exit_code)

            return BuildResult(
                success=exit_code == 0,
                exit_code=exit_code,
                matrix_json_path=str(json_path),
                matrix_prompt_path=str(prompt_path),
                metadata_path=str(meta_path),
                lockfile_path=str(lockfile_mgr.lockfile_path),
                build_log_path=str(cache_dir / "_build_log.jsonl"),
                total_files=matrix.total_files,
                extractors_run=extractors_run,
                cache_hits=cache_mgr.hits,
                cache_misses=cache_mgr.misses,
                duration_ms=duration,
                errors=errors,
                warnings=warnings,
            )

        except Exception as exc:
            logger.error("build_fatal", str(exc))
            logger.flush()
            duration = (time.time() - start_time) * 1000
            return BuildResult(
                success=False,
                exit_code=int(ExitCode.FATAL_ERROR),
                duration_ms=duration,
                errors=[str(exc)],
            )

    def _scan_files(self) -> Dict[str, str]:
        """Walk the project and compute content hashes for all source files.

        Returns:
            Dict mapping relative_path → content_hash (sorted)
        """
        from codetrellis.scanner import ProjectScanner

        scanner = ProjectScanner()
        root = self._project_root
        result: Dict[str, str] = {}

        for file_path in scanner._walk_files(root):
            try:
                rel_path = str(file_path.relative_to(root))
                content_hash = self._hasher.hash_file(str(file_path))
                result[rel_path] = content_hash
            except (PermissionError, OSError):
                continue

        return dict(sorted(result.items()))

    def _apply_post_processing(
        self,
        compressed: str,
        matrix: Any,
        config: BuildConfig,
    ) -> str:
        """Apply all post-processing steps to the compressed output.

        This mirrors the logic in cli.py scan_project() for parity.
        """
        import re

        # Deep LSP extraction
        if config.deep:
            try:
                from codetrellis.extractors.lsp_extractor import LSPExtractor
                lsp = LSPExtractor(self._project_root)
                if lsp.is_available() and lsp.extract():
                    compressed = compressed + "\n" + lsp.get_compact_output()
            except Exception:
                pass

        # Progress section
        if config.include_progress:
            try:
                from codetrellis.cli import _generate_progress_section
                progress = _generate_progress_section(self._project_root, matrix)
                if progress:
                    compressed = compressed + "\n" + progress
            except Exception:
                pass

        # Overview section
        if config.include_overview:
            try:
                from codetrellis.cli import _generate_overview_section
                overview = _generate_overview_section(self._project_root, matrix)
                if overview:
                    compressed = compressed + "\n" + overview
            except Exception:
                pass

        # Best practices
        if config.include_practices:
            try:
                from codetrellis.cli import _generate_practices_section
                practices = _generate_practices_section(
                    self._project_root, matrix,
                    level=config.practices_level,
                    categories=config.practices_categories,
                    practices_format=config.practices_format,
                    max_practice_tokens=config.max_practice_tokens,
                )
                if practices:
                    compressed = re.sub(
                        r'\[BEST_PRACTICES\]\n?(?:(?!\[)[^\n]*\n?)*',
                        '', compressed, count=1,
                    )
                    compressed = compressed.rstrip() + "\n" + practices
            except Exception:
                pass

        # Cache optimization
        if config.cache_optimize:
            try:
                from codetrellis.cache_optimizer import optimize_matrix_prompt
                result = optimize_matrix_prompt(compressed, insert_cache_breaks=True)
                compressed = result.optimized_prompt
            except Exception:
                pass

        return compressed

    def verify(self) -> Dict[str, Any]:
        """Run quality gate verification on existing outputs.

        Per D1 Gate 1 — Build verification.

        Returns:
            Dict with gate results (pass/fail + errors)
        """
        cache_dir = self._get_cache_dir()
        errors: List[str] = []

        # Check required files exist and are non-empty
        for fname in ["matrix.prompt", "matrix.json", "_metadata.json"]:
            fpath = cache_dir / fname
            if not fpath.exists():
                errors.append(f"MISSING: {fname}")
            elif fpath.stat().st_size == 0:
                errors.append(f"EMPTY: {fname}")

        # Validate JSON files
        for fname in ["matrix.json", "_metadata.json"]:
            fpath = cache_dir / fname
            if fpath.exists():
                try:
                    json.loads(fpath.read_text(encoding="utf-8"))
                except json.JSONDecodeError as e:
                    errors.append(f"INVALID_JSON: {fname}: {e}")

        # Validate metadata fields
        meta_path = cache_dir / "_metadata.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                for req_field in ["version", "project", "generated", "stats"]:
                    if req_field not in meta:
                        errors.append(f"MISSING_FIELD: _metadata.json.{req_field}")
                if meta.get("stats", {}).get("totalFiles", 0) == 0:
                    errors.append("ZERO_FILES: No files scanned")
                if meta.get("version") != VERSION:
                    errors.append(
                        f"VERSION_MISMATCH: metadata={meta.get('version')} vs code={VERSION}"
                    )
            except json.JSONDecodeError:
                pass  # Already reported above

        # Validate matrix.prompt contains [PROJECT]
        prompt_path = cache_dir / "matrix.prompt"
        if prompt_path.exists():
            content = prompt_path.read_text(encoding="utf-8")
            if "[PROJECT]" not in content:
                errors.append("MISSING_SECTION: [PROJECT] not found in matrix.prompt")

        passed = len(errors) == 0
        return {
            "gate": "build",
            "passed": passed,
            "errors": errors,
            "files_checked": [
                str(cache_dir / f)
                for f in ["matrix.prompt", "matrix.json", "_metadata.json"]
            ],
        }
