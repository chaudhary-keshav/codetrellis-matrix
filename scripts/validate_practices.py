#!/usr/bin/env python3
"""YAML Practice Validator for BPL.

Validates all YAML practice files against the expected schema,
checks for duplicate IDs, validates enum values, and reports statistics.

Usage:
    python validate_practices.py
    python validate_practices.py --verbose
    python validate_practices.py --practices-dir /path/to/practices

Exit Codes:
    0: All validations passed
    1: One or more validations failed
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import yaml

# ── Valid enum values (must match codetrellis/bpl/models.py) ──────────────────────

VALID_CATEGORIES = {
    "type_safety", "error_handling", "code_style", "documentation",
    "testing", "performance", "security", "maintainability",
    "debugging", "best_practices", "design_patterns", "solid_principles",
    "api_design", "data_modeling", "architecture", "state_management",
    "patterns", "fastapi", "django", "flask", "pytorch", "pandas",
    "sqlalchemy", "pydantic", "celery", "component_design",
    "signal_patterns", "service_patterns", "lifecycle", "routing",
    "forms", "networking", "async_patterns", "concurrency", "database",
    "caching", "logging", "configuration", "creational", "structural",
    "behavioral", "enterprise",
    # NestJS-Specific Categories
    "validation", "monitoring", "reliability",
    # React-Specific Categories
    "accessibility", "user_experience",
    # DevOps Categories
    "automation", "containers", "deployment", "infrastructure",
    # Go Categories
    "ownership", "lifetimes", "memory_safety", "trait_design", "cargo",
    # Rust Categories
    "ownership", "lifetimes", "memory_safety", "trait_design", "cargo",
    # SQL Categories
    "query_optimization", "schema_design", "stored_procedures",
    "data_integrity", "indexing", "migration_patterns",
    "sql_security", "sql_anti_patterns",
    # HTML Categories
    "semantic_html", "html_forms", "seo", "web_components",
    "template_engines", "html_performance", "responsive_design", "html_security",
    # CSS Categories (v4.17)
    "css_layout", "css_variables", "css_animations", "css_preprocessor",
    "css_architecture", "css_naming", "css_performance", "css_responsive",
    # Chakra UI Categories (v4.38)
    "chakra_components", "chakra_theme", "chakra_styling", "chakra_hooks",
    "chakra_performance", "chakra_accessibility", "chakra_forms",
    "chakra_overlay", "chakra_navigation", "chakra_migration",
}

VALID_LEVELS = {"beginner", "intermediate", "advanced", "expert"}

VALID_PRIORITIES = {"critical", "high", "medium", "low", "optional"}

VALID_SOLID = {
    "single_responsibility", "open_closed", "liskov_substitution",
    "interface_segregation", "dependency_inversion",
}

# ── Required fields for a practice ─────────────────────────────────────────

REQUIRED_FIELDS = {"id", "title", "category"}
OPTIONAL_FIELDS = {
    "level", "priority", "content", "python_version", "applicability",
    "solid_principles", "design_patterns", "deprecated", "superseded_by",
}


class ValidationError:
    """A single validation error."""

    def __init__(self, file: str, practice_id: str, field: str, message: str) -> None:
        self.file = file
        self.practice_id = practice_id
        self.field = field
        self.message = message

    def __str__(self) -> str:
        return f"  [{self.file}] {self.practice_id}.{self.field}: {self.message}"


class ValidationResult:
    """Aggregate validation result."""

    def __init__(self) -> None:
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.files_checked: int = 0
        self.practices_checked: int = 0
        self.all_ids: List[str] = []
        self.by_file: Dict[str, int] = {}
        self.by_category: Counter = Counter()
        self.by_level: Counter = Counter()
        self.by_priority: Counter = Counter()

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, file: str, pid: str, field: str, msg: str) -> None:
        self.errors.append(ValidationError(file, pid, field, msg))

    def add_warning(self, file: str, pid: str, field: str, msg: str) -> None:
        self.warnings.append(ValidationError(file, pid, field, msg))


def validate_practice(
    data: Dict[str, Any], filename: str, result: ValidationResult
) -> None:
    """Validate a single practice definition."""
    pid = data.get("id", "<missing-id>")
    result.practices_checked += 1
    result.all_ids.append(pid)

    # ── Check required fields ──────────────────────────────────────────
    for field in REQUIRED_FIELDS:
        if field not in data or data[field] is None:
            result.add_error(filename, pid, field, f"Required field '{field}' is missing")

    if "id" not in data:
        return  # Can't validate further without ID

    # ── Check ID format ────────────────────────────────────────────────
    if not isinstance(pid, str) or len(pid) < 2:
        result.add_error(filename, pid, "id", f"ID must be a non-empty string, got: {pid!r}")

    # ── Check title ────────────────────────────────────────────────────
    title = data.get("title", "")
    if not isinstance(title, str) or len(title) < 3:
        result.add_error(filename, pid, "title", f"Title must be >= 3 chars, got: {title!r}")

    # ── Check category ─────────────────────────────────────────────────
    category = data.get("category", "")
    if category and category not in VALID_CATEGORIES:
        result.add_error(
            filename, pid, "category",
            f"Invalid category '{category}'. Valid: {sorted(VALID_CATEGORIES)}"
        )
    if category:
        result.by_category[category] += 1

    # ── Check level ────────────────────────────────────────────────────
    level = data.get("level", "intermediate")
    if level not in VALID_LEVELS:
        result.add_error(
            filename, pid, "level",
            f"Invalid level '{level}'. Valid: {sorted(VALID_LEVELS)}"
        )
    result.by_level[level] += 1

    # ── Check priority ─────────────────────────────────────────────────
    priority = data.get("priority", "medium")
    if priority not in VALID_PRIORITIES:
        result.add_error(
            filename, pid, "priority",
            f"Invalid priority '{priority}'. Valid: {sorted(VALID_PRIORITIES)}"
        )
    result.by_priority[priority] += 1

    # ── Check content ──────────────────────────────────────────────────
    content = data.get("content", {})
    if content:
        if not isinstance(content, dict):
            result.add_error(filename, pid, "content", "Content must be a dict")
        else:
            desc = content.get("description", "")
            if not desc or len(str(desc).strip()) < 5:
                result.add_warning(
                    filename, pid, "content.description",
                    "Description is empty or very short"
                )

    # ── Check python_version ───────────────────────────────────────────
    version = data.get("python_version", {})
    if version and isinstance(version, dict):
        for key in version:
            if key not in {"min_version", "max_version", "excluded_versions"}:
                result.add_warning(
                    filename, pid, f"python_version.{key}",
                    f"Unexpected version field: '{key}'"
                )

    # ── Check applicability ────────────────────────────────────────────
    app = data.get("applicability", {})
    if app and isinstance(app, dict):
        valid_app_keys = {
            "frameworks", "patterns", "file_patterns",
            "has_dependencies", "project_types", "excluded_patterns",
            "min_python", "contexts",
        }
        for key in app:
            if key not in valid_app_keys:
                result.add_warning(
                    filename, pid, f"applicability.{key}",
                    f"Unexpected applicability field: '{key}'"
                )

    # ── Check SOLID principles ─────────────────────────────────────────
    solid = data.get("solid_principles", [])
    if solid:
        if not isinstance(solid, list):
            result.add_error(filename, pid, "solid_principles", "Must be a list")
        else:
            for s in solid:
                if s not in VALID_SOLID:
                    result.add_error(
                        filename, pid, "solid_principles",
                        f"Invalid SOLID principle: '{s}'. Valid: {sorted(VALID_SOLID)}"
                    )


def validate_file(filepath: Path, result: ValidationResult) -> None:
    """Validate a single YAML file."""
    filename = filepath.name
    result.files_checked += 1

    try:
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result.add_error(filename, "FILE", "yaml", f"YAML parse error: {e}")
        return
    except OSError as e:
        result.add_error(filename, "FILE", "io", f"File read error: {e}")
        return

    if not data:
        result.add_warning(filename, "FILE", "empty", "File is empty")
        return

    if not isinstance(data, dict):
        result.add_error(filename, "FILE", "structure", "Root must be a dict")
        return

    practices = data.get("practices", [])
    if not practices:
        result.add_warning(filename, "FILE", "practices", "No practices found in file")
        return

    if not isinstance(practices, list):
        result.add_error(filename, "FILE", "practices", "practices must be a list")
        return

    count = 0
    for practice_data in practices:
        if not isinstance(practice_data, dict):
            result.add_error(filename, "?", "practice", "Practice entry must be a dict")
            continue
        validate_practice(practice_data, filename, result)
        count += 1

    result.by_file[filename] = count


def check_duplicates(result: ValidationResult) -> None:
    """Check for duplicate practice IDs across all files."""
    id_counts = Counter(result.all_ids)
    for pid, count in id_counts.items():
        if count > 1:
            result.add_error(
                "GLOBAL", pid, "id",
                f"Duplicate practice ID found {count} times"
            )


def main() -> int:
    """Run validation and print report."""
    parser = argparse.ArgumentParser(description="Validate BPL practice YAML files")
    parser.add_argument(
        "--practices-dir",
        type=Path,
        default=Path(__file__).parent.parent / "codetrellis" / "bpl" / "practices",
        help="Path to practices directory",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show warnings too")
    args = parser.parse_args()

    practices_dir = args.practices_dir
    if not practices_dir.exists():
        print(f"ERROR: Practices directory not found: {practices_dir}")
        return 1

    result = ValidationResult()

    # Validate all YAML files
    yaml_files = sorted(practices_dir.glob("*.yaml")) + sorted(practices_dir.glob("*.yml"))
    if not yaml_files:
        print(f"ERROR: No YAML files found in {practices_dir}")
        return 1

    for filepath in yaml_files:
        validate_file(filepath, result)

    # Check for duplicates
    check_duplicates(result)

    # ── Print Report ───────────────────────────────────────────────────
    print("=" * 70)
    print("  BPL Practice Validation Report")
    print("=" * 70)
    print()

    # File summary
    print(f"  Files checked:      {result.files_checked}")
    print(f"  Practices checked:  {result.practices_checked}")
    print(f"  Errors:             {len(result.errors)}")
    print(f"  Warnings:           {len(result.warnings)}")
    print()

    # Per-file counts
    print("  Per-file practice counts:")
    for filename, count in sorted(result.by_file.items()):
        print(f"    {filename:<35} {count:>4}")
    print(f"    {'TOTAL':<35} {result.practices_checked:>4}")
    print()

    # By category
    print("  By category:")
    for cat, count in result.by_category.most_common():
        print(f"    {cat:<30} {count:>4}")
    print()

    # By level
    print("  By level:")
    for level, count in result.by_level.most_common():
        print(f"    {level:<20} {count:>4}")
    print()

    # By priority
    print("  By priority:")
    for pri, count in result.by_priority.most_common():
        print(f"    {pri:<20} {count:>4}")
    print()

    # Errors
    if result.errors:
        print("  ERRORS:")
        for err in result.errors:
            print(f"    ❌ {err}")
        print()

    # Warnings
    if args.verbose and result.warnings:
        print("  WARNINGS:")
        for warn in result.warnings:
            print(f"    ⚠️  {warn}")
        print()

    # Final verdict
    print("-" * 70)
    if result.passed:
        print("  ✅ VALIDATION PASSED - All practices are valid")
    else:
        print(f"  ❌ VALIDATION FAILED - {len(result.errors)} error(s) found")
    print("-" * 70)

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
