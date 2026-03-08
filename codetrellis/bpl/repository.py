"""Best Practices Repository for loading and managing practices.

This module provides the BestPracticesRepository class for loading,
caching, and querying best practices from YAML files.

The repository supports:
- Loading practices from YAML files
- Caching for performance
- Filtering by category, level, and priority
- Version-aware practice selection

Example:
    >>> from codetrellis.bpl.repository import BestPracticesRepository
    >>> repo = BestPracticesRepository()
    >>> repo.load_all()
    >>> practices = repo.get_by_category(PracticeCategory.TYPE_SAFETY)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set

import yaml

from .models import (
    ApplicabilityRule,
    BestPractice,
    PracticeCategory,
    PracticeContent,
    PracticeLevel,
    PracticePriority,
    PracticeSet,
    SOLIDPrinciple,
    VersionConstraint,
)

logger = logging.getLogger(__name__)


class PracticeLoadError(Exception):
    """Raised when a practice file cannot be loaded."""

    def __init__(self, file_path: Path, message: str) -> None:
        self.file_path = file_path
        self.message = message
        super().__init__(f"Failed to load {file_path}: {message}")


class PracticeValidationError(Exception):
    """Raised when a practice definition is invalid."""

    def __init__(self, practice_id: str, message: str) -> None:
        self.practice_id = practice_id
        self.message = message
        super().__init__(f"Invalid practice {practice_id}: {message}")


class BestPracticesRepository:
    """Repository for loading and managing best practices.

    The repository loads practices from YAML files in the practices directory,
    validates them, and provides various query methods for retrieving practices
    based on different criteria.

    Attributes:
        practices_dir: Path to the practices directory.
        practices: Dictionary of loaded practices keyed by ID.
        practice_sets: Dictionary of practice sets keyed by name.

    Example:
        >>> repo = BestPracticesRepository()
        >>> repo.load_all()
        >>> len(repo.practices)
        25
        >>> repo.get("PY001").title
        'Use Type Hints for All Function Signatures'
    """

    # Default practices directory relative to this module
    DEFAULT_PRACTICES_DIR = Path(__file__).parent / "practices"

    def __init__(
        self,
        practices_dir: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
        use_cache: bool = True,
    ) -> None:
        """Initialize the repository.

        Args:
            practices_dir: Path to the practices directory. Defaults to
                the built-in practices directory.
            cache_dir: Path for caching parsed practices. If None, no caching.
            use_cache: Whether to use caching for loaded practices.
        """
        self.practices_dir = practices_dir or self.DEFAULT_PRACTICES_DIR
        self.cache_dir = cache_dir
        self.use_cache = use_cache and cache_dir is not None

        self._practices: Dict[str, BestPractice] = {}
        self._practice_sets: Dict[str, PracticeSet] = {}
        self._by_category: Dict[PracticeCategory, List[str]] = {}
        self._by_level: Dict[PracticeLevel, List[str]] = {}
        self._by_framework: Dict[str, List[str]] = {}
        self._loaded = False
        self._load_errors: List[str] = []

    @property
    def practices(self) -> Dict[str, BestPractice]:
        """Get all loaded practices."""
        return self._practices.copy()

    @property
    def practice_sets(self) -> Dict[str, PracticeSet]:
        """Get all loaded practice sets."""
        return self._practice_sets.copy()

    @property
    def is_loaded(self) -> bool:
        """Check if practices have been loaded."""
        return self._loaded

    @property
    def load_errors(self) -> List[str]:
        """Get any errors that occurred during loading."""
        return self._load_errors.copy()

    def load_all(self, force_reload: bool = False) -> int:
        """Load all practices from the practices directory.

        Args:
            force_reload: If True, reload even if already loaded.

        Returns:
            Number of practices loaded.

        Raises:
            FileNotFoundError: If the practices directory doesn't exist.
        """
        if self._loaded and not force_reload:
            return len(self._practices)

        t_start = time.perf_counter()

        if not self.practices_dir.exists():
            raise FileNotFoundError(f"Practices directory not found: {self.practices_dir}")

        # Reset state
        self._practices.clear()
        self._practice_sets.clear()
        self._by_category.clear()
        self._by_level.clear()
        self._by_framework.clear()
        self._load_errors.clear()

        # Try cache first
        if self.use_cache and self._load_from_cache():
            self._loaded = True
            return len(self._practices)

        # Load from YAML files
        yaml_files = list(self.practices_dir.glob("*.yaml")) + list(
            self.practices_dir.glob("*.yml")
        )

        for yaml_file in yaml_files:
            try:
                self._load_file(yaml_file)
            except PracticeLoadError as e:
                self._load_errors.append(str(e))
                logger.warning(str(e))

        # Build indexes
        self._build_indexes()

        # Save to cache
        if self.use_cache:
            self._save_to_cache()

        self._loaded = True
        t_elapsed = time.perf_counter() - t_start
        logger.info(
            f"Loaded {len(self._practices)} practices from {len(yaml_files)} files "
            f"in {t_elapsed:.3f}s (errors={len(self._load_errors)})"
        )

        return len(self._practices)

    def _load_file(self, file_path: Path) -> None:
        """Load practices from a single YAML file.

        Args:
            file_path: Path to the YAML file.

        Raises:
            PracticeLoadError: If the file cannot be loaded or parsed.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PracticeLoadError(file_path, f"YAML parse error: {e}")
        except OSError as e:
            raise PracticeLoadError(file_path, f"File read error: {e}")

        if not data:
            return

        # Load practices
        practices_data = data.get("practices", [])
        for practice_data in practices_data:
            try:
                practice = self._parse_practice(practice_data)
                if practice.id in self._practices:
                    logger.warning(f"Duplicate practice ID: {practice.id}")
                self._practices[practice.id] = practice
            except (KeyError, ValueError) as e:
                practice_id = practice_data.get("id", "unknown")
                self._load_errors.append(f"Invalid practice {practice_id}: {e}")
                logger.warning(f"Failed to parse practice: {e}")

        # Load practice sets
        sets_data = data.get("practice_sets", [])
        for set_data in sets_data:
            try:
                practice_set = self._parse_practice_set(set_data)
                self._practice_sets[practice_set.name] = practice_set
            except (KeyError, ValueError) as e:
                set_name = set_data.get("name", "unknown")
                self._load_errors.append(f"Invalid practice set {set_name}: {e}")

    def _parse_practice(self, data: Dict[str, Any]) -> BestPractice:
        """Parse a practice from dictionary data.

        Args:
            data: Dictionary containing practice definition.

        Returns:
            Parsed BestPractice object.

        Raises:
            KeyError: If required fields are missing.
            ValueError: If field values are invalid.
        """
        # Parse category
        category_str = data["category"]
        try:
            category = PracticeCategory(category_str)
        except ValueError:
            raise ValueError(f"Invalid category: {category_str}")

        # Parse level
        level_str = data.get("level", "intermediate")
        try:
            level = PracticeLevel(level_str)
        except ValueError:
            raise ValueError(f"Invalid level: {level_str}")

        # Parse priority
        priority_str = data.get("priority", "medium")
        try:
            priority = PracticePriority(priority_str)
        except ValueError:
            raise ValueError(f"Invalid priority: {priority_str}")

        # Parse content
        content_data = data.get("content", {})
        # v4.77: Support flat-format YAML where description/tags/references
        # are at top level instead of nested under 'content'
        content = PracticeContent(
            description=content_data.get("description", "") or data.get("description", ""),
            rationale=content_data.get("rationale", "") or data.get("rationale", ""),
            good_examples=content_data.get("good_examples", []) or data.get("good_examples", []),
            bad_examples=content_data.get("bad_examples", []) or data.get("bad_examples", []),
            references=content_data.get("references", []) or data.get("references", []),
            related_practices=content_data.get("related_practices", []) or data.get("related_practices", []),
            tags=content_data.get("tags", []) or data.get("tags", []),
        )

        # Parse version constraint
        version_data = data.get("python_version", {})
        python_version = VersionConstraint(
            min_version=version_data.get("min_version"),
            max_version=version_data.get("max_version"),
            excluded_versions=tuple(version_data.get("excluded_versions", [])),
        )

        # Parse applicability
        app_data = data.get("applicability", {})
        # v4.77: Also support top-level 'frameworks' key as shorthand
        # (used by gsap_core.yaml, rxjs_core.yaml, framer_motion_core.yaml)
        app_frameworks = app_data.get("frameworks", [])
        if not app_frameworks and "frameworks" in data:
            app_frameworks = data["frameworks"]
        applicability = ApplicabilityRule(
            frameworks=tuple(app_frameworks),
            patterns=tuple(app_data.get("patterns", [])),
            file_patterns=tuple(app_data.get("file_patterns", [])),
            has_dependencies=tuple(app_data.get("has_dependencies", [])),
            project_types=tuple(app_data.get("project_types", [])),
            excluded_patterns=tuple(app_data.get("excluded_patterns", [])),
            min_python=app_data.get("min_python"),
            contexts=tuple(app_data.get("contexts", [])),
        )

        # Parse SOLID principles
        solid_data = data.get("solid_principles", [])
        solid_principles = []
        for principle_str in solid_data:
            try:
                solid_principles.append(SOLIDPrinciple(principle_str))
            except ValueError:
                logger.warning(f"Invalid SOLID principle: {principle_str}")

        # Parse complexity_score (optional, 1-10 scale)
        complexity_score = data.get("complexity_score")
        if complexity_score is not None:
            complexity_score = int(complexity_score)
            if not 1 <= complexity_score <= 10:
                logger.warning(
                    f"complexity_score {complexity_score} out of range (1-10), "
                    f"clamping to valid range"
                )
                complexity_score = max(1, min(10, complexity_score))

        return BestPractice(
            id=data["id"],
            title=data["title"],
            category=category,
            level=level,
            priority=priority,
            content=content,
            python_version=python_version,
            applicability=applicability,
            solid_principles=solid_principles,
            design_patterns=data.get("design_patterns", []),
            complexity_score=complexity_score,
            anti_pattern_id=data.get("anti_pattern_id"),
            deprecated=data.get("deprecated", False),
            superseded_by=data.get("superseded_by"),
        )

    def _parse_practice_set(self, data: Dict[str, Any]) -> PracticeSet:
        """Parse a practice set from dictionary data.

        Args:
            data: Dictionary containing practice set definition.

        Returns:
            Parsed PracticeSet object.
        """
        return PracticeSet(
            name=data["name"],
            description=data.get("description", ""),
            practices=data.get("practices", []),
            order=data.get("order", []),
            prerequisites=data.get("prerequisites", []),
        )

    def _build_indexes(self) -> None:
        """Build indexes for efficient querying."""
        for practice_id, practice in self._practices.items():
            # Index by category
            if practice.category not in self._by_category:
                self._by_category[practice.category] = []
            self._by_category[practice.category].append(practice_id)

            # Index by level
            if practice.level not in self._by_level:
                self._by_level[practice.level] = []
            self._by_level[practice.level].append(practice_id)

            # Index by framework (from applicability)
            for framework in practice.applicability.frameworks:
                if framework not in self._by_framework:
                    self._by_framework[framework] = []
                self._by_framework[framework].append(practice_id)

    def _get_cache_path(self) -> Path:
        """Get the cache file path."""
        if not self.cache_dir:
            raise ValueError("Cache directory not set")

        # Create hash of practices directory for cache invalidation
        dir_hash = hashlib.md5(str(self.practices_dir).encode()).hexdigest()[:8]
        return self.cache_dir / f"bpl_cache_{dir_hash}.json"

    def _load_from_cache(self) -> bool:
        """Try to load practices from cache.

        Returns:
            True if cache was loaded successfully.
        """
        if not self.cache_dir:
            return False

        cache_path = self._get_cache_path()
        if not cache_path.exists():
            return False

        try:
            # Check if cache is newer than all YAML files
            cache_mtime = cache_path.stat().st_mtime
            yaml_files = list(self.practices_dir.glob("*.yaml")) + list(
                self.practices_dir.glob("*.yml")
            )

            for yaml_file in yaml_files:
                if yaml_file.stat().st_mtime > cache_mtime:
                    logger.info("Cache is stale, will reload from YAML")
                    return False

            # Load from cache
            with open(cache_path, encoding="utf-8") as f:
                cache_data = json.load(f)

            for practice_data in cache_data.get("practices", []):
                practice = self._parse_practice(practice_data)
                self._practices[practice.id] = practice

            for set_data in cache_data.get("practice_sets", []):
                practice_set = self._parse_practice_set(set_data)
                self._practice_sets[practice_set.name] = practice_set

            self._build_indexes()
            logger.info(f"Loaded {len(self._practices)} practices from cache")
            return True

        except (json.JSONDecodeError, OSError, KeyError) as e:
            logger.warning(f"Failed to load cache: {e}")
            return False

    def _save_to_cache(self) -> None:
        """Save practices to cache."""
        if not self.cache_dir:
            return

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path = self._get_cache_path()

            cache_data = {
                "practices": [p.to_dict() for p in self._practices.values()],
                "practice_sets": [s.to_dict() for s in self._practice_sets.values()],
                "cached_at": datetime.now().isoformat(),
            }

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f)

            logger.info(f"Saved {len(self._practices)} practices to cache")

        except OSError as e:
            logger.warning(f"Failed to save cache: {e}")

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get(self, practice_id: str) -> Optional[BestPractice]:
        """Get a practice by its ID.

        Args:
            practice_id: The unique practice identifier.

        Returns:
            The practice if found, None otherwise.
        """
        return self._practices.get(practice_id)

    def get_all(self) -> List[BestPractice]:
        """Get all loaded practices.

        Returns:
            List of all practices.
        """
        return list(self._practices.values())

    def get_by_category(self, category: PracticeCategory) -> List[BestPractice]:
        """Get practices by category.

        Args:
            category: The category to filter by.

        Returns:
            List of practices in the category.
        """
        practice_ids = self._by_category.get(category, [])
        return [self._practices[pid] for pid in practice_ids]

    def get_by_level(self, level: PracticeLevel) -> List[BestPractice]:
        """Get practices by expertise level.

        Args:
            level: The level to filter by.

        Returns:
            List of practices at that level.
        """
        practice_ids = self._by_level.get(level, [])
        return [self._practices[pid] for pid in practice_ids]

    def get_by_framework(self, framework: str) -> List[BestPractice]:
        """Get practices applicable to a framework.

        Args:
            framework: The framework name (e.g., "fastapi", "django").

        Returns:
            List of practices for that framework.
        """
        practice_ids = self._by_framework.get(framework.lower(), [])
        return [self._practices[pid] for pid in practice_ids]

    def get_by_priority(
        self,
        min_priority: PracticePriority = PracticePriority.OPTIONAL,
    ) -> List[BestPractice]:
        """Get practices at or above a priority level.

        Args:
            min_priority: Minimum priority level.

        Returns:
            List of practices at or above that priority.
        """
        priority_order = list(PracticePriority)
        min_index = priority_order.index(min_priority)

        return [
            p
            for p in self._practices.values()
            if priority_order.index(p.priority) <= min_index
        ]

    def search(
        self,
        query: str,
        fields: Optional[List[str]] = None,
    ) -> List[BestPractice]:
        """Search practices by text query.

        Args:
            query: Search query string.
            fields: Fields to search in. Defaults to title, description, tags.

        Returns:
            List of matching practices.
        """
        if fields is None:
            fields = ["title", "description", "tags"]

        query_lower = query.lower()
        results = []

        for practice in self._practices.values():
            matched = False

            if "title" in fields and query_lower in practice.title.lower():
                matched = True
            elif "description" in fields and query_lower in practice.content.description.lower():
                matched = True
            elif "tags" in fields and any(
                query_lower in tag.lower() for tag in practice.content.tags
            ):
                matched = True
            elif "id" in fields and query_lower in practice.id.lower():
                matched = True

            if matched:
                results.append(practice)

        return results

    def get_applicable(
        self,
        context: Dict[str, Any],
        python_version: Optional[str] = None,
    ) -> List[BestPractice]:
        """Get practices applicable to a project context.

        Args:
            context: Project context dictionary with keys:
                - frameworks: Set of detected framework names
                - patterns: Set of detected architecture patterns
                - dependencies: Set of package names
                - project_type: String of project type
            python_version: Python version to check compatibility.

        Returns:
            List of applicable practices.
        """
        return [
            p
            for p in self._practices.values()
            if p.is_applicable(context, python_version)
        ]

    def get_practice_set(self, name: str) -> Optional[PracticeSet]:
        """Get a practice set by name.

        Args:
            name: The practice set name.

        Returns:
            The practice set if found, None otherwise.
        """
        return self._practice_sets.get(name)

    def iter_practices(self) -> Iterator[BestPractice]:
        """Iterate over all practices.

        Yields:
            BestPractice objects.
        """
        yield from self._practices.values()

    def get_categories(self) -> Set[PracticeCategory]:
        """Get all categories that have practices.

        Returns:
            Set of categories with at least one practice.
        """
        return set(self._by_category.keys())

    def get_frameworks(self) -> Set[str]:
        """Get all frameworks that have specific practices.

        Returns:
            Set of framework names.
        """
        return set(self._by_framework.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded practices.

        Returns:
            Dictionary with statistics.
        """
        return {
            "total_practices": len(self._practices),
            "total_sets": len(self._practice_sets),
            "by_category": {
                cat.value: len(ids) for cat, ids in self._by_category.items()
            },
            "by_level": {
                level.value: len(ids) for level, ids in self._by_level.items()
            },
            "by_framework": {
                fw: len(ids) for fw, ids in self._by_framework.items()
            },
            "load_errors": len(self._load_errors),
        }


# Module-level repository instance for convenience
_default_repository: Optional[BestPracticesRepository] = None


def get_repository() -> BestPracticesRepository:
    """Get the default repository instance.

    Creates and loads the repository on first call.

    Returns:
        The default BestPracticesRepository instance.
    """
    global _default_repository

    if _default_repository is None:
        _default_repository = BestPracticesRepository()
        _default_repository.load_all()

    return _default_repository


def reload_repository() -> BestPracticesRepository:
    """Reload the default repository.

    Returns:
        The reloaded BestPracticesRepository instance.
    """
    global _default_repository

    _default_repository = BestPracticesRepository()
    _default_repository.load_all()

    return _default_repository
