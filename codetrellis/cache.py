"""
CodeTrellis Cache Manager — Content-Addressed Caching for Incremental Builds
=========================================================================

Per PART B (B3-B5) of the Master Plan:
- InputHashCalculator: SHA-256 content hashing for files
- LockfileManager: Manages _lockfile.json with input manifests
- CacheManager: Orchestrates per-file, per-extractor result caching

Cache Structure (C5):
    .codetrellis/
    └── cache/
        └── {VERSION}/
            └── {project_name}/
                ├── matrix.prompt
                ├── matrix.json
                ├── _metadata.json
                ├── _lockfile.json
                ├── _build_log.jsonl
                └── _extractor_cache/
                    └── {extractor_name}/
                        └── {file_content_hash}.json

Invalidation Rules (C5):
    A cached result is INVALID when:
    1. File content hash differs from lockfile
    2. CodeTrellis version changes
    3. Config hash changes
    4. CLI flags change
    5. Extractor version changes

Author: Keshav Chaudhary
Created: 20 February 2026
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


__all__ = [
    "InputHashCalculator",
    "LockfileManager",
    "CacheManager",
    "FileManifestEntry",
    "Lockfile",
]


# =============================================================================
# InputHashCalculator
# =============================================================================

class InputHashCalculator:
    """Computes deterministic SHA-256 hashes for files and configurations.

    Per C1.1: Uses SHA-256, first 16 hex chars for file content hashing.
    Per C3: Deterministic — same content always produces same hash.
    """

    @staticmethod
    def hash_file(file_path: str) -> str:
        """Compute SHA-256 hash of a file's content (first 16 hex chars).

        Args:
            file_path: Absolute path to the file

        Returns:
            First 16 hex characters of the SHA-256 digest

        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be read
        """
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()[:16]

    @staticmethod
    def hash_string(content: str) -> str:
        """Compute SHA-256 hash of a string (first 16 hex chars).

        Args:
            content: String to hash

        Returns:
            First 16 hex characters of the SHA-256 digest
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def hash_config(config: Dict[str, Any]) -> str:
        """Compute a deterministic hash of a configuration dict.

        Args:
            config: Configuration dictionary

        Returns:
            First 16 hex characters of the SHA-256 digest
        """
        serialized = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """Compute SHA-256 hash of raw bytes (first 16 hex chars).

        Args:
            data: Raw bytes to hash

        Returns:
            First 16 hex characters of the SHA-256 digest
        """
        return hashlib.sha256(data).hexdigest()[:16]


# =============================================================================
# Lockfile Data Structures
# =============================================================================

@dataclass
class FileManifestEntry:
    """A single file entry in the lockfile manifest.

    Tracks the content hash and which extractors have been run on this file.
    """
    file_path: str  # Relative to project root
    content_hash: str  # SHA-256 first 16 hex
    size_bytes: int = 0
    last_modified: str = ""
    extractors_run: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON storage."""
        return {
            "file_path": self.file_path,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "last_modified": self.last_modified,
            "extractors_run": sorted(self.extractors_run),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileManifestEntry":
        """Deserialize from dict."""
        return cls(
            file_path=data["file_path"],
            content_hash=data["content_hash"],
            size_bytes=data.get("size_bytes", 0),
            last_modified=data.get("last_modified", ""),
            extractors_run=data.get("extractors_run", []),
        )


@dataclass
class Lockfile:
    """The _lockfile.json structure.

    Per C5: Contains build_key, config_hash, file_manifest, extractor_versions.
    Used to determine what has changed between builds.
    """
    build_key: str  # Composite key: version + config_hash + flags
    codetrellis_version: str
    config_hash: str
    cli_flags_hash: str = ""
    generated_at: str = ""
    file_manifest: Dict[str, FileManifestEntry] = field(default_factory=dict)
    extractor_versions: Dict[str, str] = field(default_factory=dict)
    total_files: int = 0
    env_fingerprint: str = ""  # C5 Rule 6: SHA-256 of environment state

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON storage."""
        return {
            "build_key": self.build_key,
            "codetrellis_version": self.codetrellis_version,
            "config_hash": self.config_hash,
            "cli_flags_hash": self.cli_flags_hash,
            "generated_at": self.generated_at,
            "total_files": self.total_files,
            "env_fingerprint": self.env_fingerprint,
            "extractor_versions": dict(sorted(self.extractor_versions.items())),
            "file_manifest": {
                k: v.to_dict()
                for k, v in sorted(self.file_manifest.items())
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lockfile":
        """Deserialize from dict."""
        manifest = {}
        for k, v in data.get("file_manifest", {}).items():
            manifest[k] = FileManifestEntry.from_dict(v)
        return cls(
            build_key=data.get("build_key", ""),
            codetrellis_version=data.get("codetrellis_version", ""),
            config_hash=data.get("config_hash", ""),
            cli_flags_hash=data.get("cli_flags_hash", ""),
            generated_at=data.get("generated_at", ""),
            file_manifest=manifest,
            extractor_versions=data.get("extractor_versions", {}),
            total_files=data.get("total_files", 0),
            env_fingerprint=data.get("env_fingerprint", ""),
        )


# =============================================================================
# LockfileManager
# =============================================================================

class LockfileManager:
    """Manages reading and writing of _lockfile.json.

    Per C5 Cache Contract: The lockfile captures the complete input manifest
    of a build so the incremental engine can diff against it.
    """

    def __init__(self, cache_dir: Path) -> None:
        """Initialize with the cache directory path.

        Args:
            cache_dir: Path to .codetrellis/cache/{VERSION}/{project_name}/
        """
        self._cache_dir = cache_dir
        self._lockfile_path = cache_dir / "_lockfile.json"

    @property
    def lockfile_path(self) -> Path:
        """Return the path to the lockfile."""
        return self._lockfile_path

    def exists(self) -> bool:
        """Check if a lockfile exists."""
        return self._lockfile_path.exists()

    def read(self) -> Optional[Lockfile]:
        """Read and parse the lockfile.

        Returns:
            Lockfile instance, or None if it doesn't exist or is corrupted
        """
        if not self._lockfile_path.exists():
            return None
        try:
            data = json.loads(self._lockfile_path.read_text(encoding="utf-8"))
            return Lockfile.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def write(self, lockfile: Lockfile) -> None:
        """Write the lockfile to disk.

        Args:
            lockfile: Lockfile instance to persist
        """
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._lockfile_path.write_text(
            json.dumps(lockfile.to_dict(), indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )

    def delete(self) -> None:
        """Remove the lockfile."""
        if self._lockfile_path.exists():
            self._lockfile_path.unlink()


# =============================================================================
# CacheManager
# =============================================================================

@dataclass
class CacheHitResult:
    """Result of checking the extractor cache for a file."""
    is_hit: bool
    cached_data: Optional[Dict[str, Any]] = None
    cache_key: str = ""


class CacheManager:
    """Orchestrates per-file, per-extractor result caching.

    Per B3.2 and C5:
    - Maintains an extractor cache under _extractor_cache/{extractor_name}/
    - Keys: {file_content_hash}.json
    - Validates cache against lockfile, config hash, and extractor version

    Usage:
        cache = CacheManager(cache_dir, version="1.0.0")
        result = cache.get("python_parser", "abc123def456")
        if not result.is_hit:
            data = run_extractor(...)
            cache.put("python_parser", "abc123def456", data)
    """

    def __init__(self, cache_dir: Path, version: str) -> None:
        """Initialize the cache manager.

        Args:
            cache_dir: Path to .codetrellis/cache/{VERSION}/{project_name}/
            version: Current CodeTrellis version string
        """
        self._cache_dir = cache_dir
        self._extractor_cache_dir = cache_dir / "_extractor_cache"
        self._version = version
        self._hits = 0
        self._misses = 0

    @property
    def hits(self) -> int:
        """Number of cache hits in this session."""
        return self._hits

    @property
    def misses(self) -> int:
        """Number of cache misses in this session."""
        return self._misses

    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0.0–1.0)."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def get(self, extractor_name: str, file_content_hash: str) -> CacheHitResult:
        """Look up a cached extractor result.

        Args:
            extractor_name: Name of the extractor (e.g., 'python_parser')
            file_content_hash: SHA-256 first 16 hex chars of the file content

        Returns:
            CacheHitResult indicating hit/miss and optional cached data
        """
        cache_key = f"{extractor_name}/{file_content_hash}"
        cache_file = self._extractor_cache_dir / extractor_name / f"{file_content_hash}.json"

        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                # Validate version match
                if data.get("_cache_version") == self._version:
                    self._hits += 1
                    return CacheHitResult(
                        is_hit=True,
                        cached_data=data.get("result"),
                        cache_key=cache_key,
                    )
            except (json.JSONDecodeError, KeyError):
                pass

        self._misses += 1
        return CacheHitResult(is_hit=False, cache_key=cache_key)

    def put(
        self,
        extractor_name: str,
        file_content_hash: str,
        result: Dict[str, Any],
    ) -> None:
        """Store an extractor result in the cache.

        Args:
            extractor_name: Name of the extractor
            file_content_hash: SHA-256 first 16 hex chars of the file content
            result: Extracted data to cache
        """
        cache_dir = self._extractor_cache_dir / extractor_name
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{file_content_hash}.json"

        wrapper = {
            "_cache_version": self._version,
            "_cached_at": datetime.now().isoformat(),
            "result": result,
        }
        cache_file.write_text(
            json.dumps(wrapper, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )

    def invalidate(self, extractor_name: Optional[str] = None) -> int:
        """Invalidate cached results.

        Args:
            extractor_name: If provided, invalidate only that extractor's cache.
                           If None, invalidate all extractor caches.

        Returns:
            Number of cache entries removed
        """
        import shutil

        count = 0
        if extractor_name:
            target = self._extractor_cache_dir / extractor_name
            if target.exists():
                count = sum(1 for _ in target.glob("*.json"))
                shutil.rmtree(target)
        else:
            if self._extractor_cache_dir.exists():
                for ext_dir in self._extractor_cache_dir.iterdir():
                    if ext_dir.is_dir():
                        count += sum(1 for _ in ext_dir.glob("*.json"))
                shutil.rmtree(self._extractor_cache_dir)
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Return cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, and on-disk entry counts
        """
        on_disk = 0
        if self._extractor_cache_dir.exists():
            for ext_dir in self._extractor_cache_dir.iterdir():
                if ext_dir.is_dir():
                    on_disk += sum(1 for _ in ext_dir.glob("*.json"))

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate, 4),
            "on_disk_entries": on_disk,
        }


# =============================================================================
# DiffEngine — Compare current files against lockfile
# =============================================================================

@dataclass
class DiffResult:
    """Result of diffing current project state against the lockfile.

    Per B4 Phase 2: Identifies which files are new, modified, or deleted
    since the last build, so only affected extractors need to re-run.
    """
    added_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    deleted_files: List[str] = field(default_factory=list)
    unchanged_files: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """True if any files were added, modified, or deleted."""
        return bool(self.added_files or self.modified_files or self.deleted_files)

    @property
    def changed_files(self) -> List[str]:
        """All files that need re-extraction (added + modified)."""
        return self.added_files + self.modified_files

    @property
    def total_files(self) -> int:
        """Total number of files in current scan."""
        return (
            len(self.added_files)
            + len(self.modified_files)
            + len(self.unchanged_files)
        )

    def summary(self) -> str:
        """Human-readable summary of changes."""
        parts = []
        if self.added_files:
            parts.append(f"+{len(self.added_files)} added")
        if self.modified_files:
            parts.append(f"~{len(self.modified_files)} modified")
        if self.deleted_files:
            parts.append(f"-{len(self.deleted_files)} deleted")
        if self.unchanged_files:
            parts.append(f"={len(self.unchanged_files)} unchanged")
        return ", ".join(parts) if parts else "no files"


class DiffEngine:
    """Compares current file hashes against a lockfile to find changes.

    Per B4 Phase 2: The diff engine is the core of incremental builds.
    """

    def __init__(self, hasher: Optional[InputHashCalculator] = None) -> None:
        self._hasher = hasher or InputHashCalculator()

    def diff(
        self,
        current_files: Dict[str, str],
        lockfile: Optional[Lockfile],
    ) -> DiffResult:
        """Diff current file hashes against the lockfile.

        Args:
            current_files: Dict mapping relative_path → content_hash for all current files
            lockfile: Previous lockfile (None if first build)

        Returns:
            DiffResult with added/modified/deleted/unchanged file lists
        """
        result = DiffResult()

        if lockfile is None:
            # No previous build — everything is new
            result.added_files = sorted(current_files.keys())
            return result

        prev_manifest = lockfile.file_manifest
        prev_paths = set(prev_manifest.keys())
        curr_paths = set(current_files.keys())

        # Added files
        result.added_files = sorted(curr_paths - prev_paths)

        # Deleted files
        result.deleted_files = sorted(prev_paths - curr_paths)

        # Modified vs unchanged
        for path in sorted(curr_paths & prev_paths):
            curr_hash = current_files[path]
            prev_hash = prev_manifest[path].content_hash
            if curr_hash != prev_hash:
                result.modified_files.append(path)
            else:
                result.unchanged_files.append(path)

        return result
