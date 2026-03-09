#!/usr/bin/env python3
"""
CodeTrellis CLI - Command Line Interface for Project Self-Awareness System
=====================================================================

Usage:
    codetrellis scan [path]        # Scan project and create matrix
    codetrellis scan [path] --tier prompt   # Scan with specific output tier
    codetrellis scan [path] --tier logic    # Include implementation logic (NEW in v4.1)
    codetrellis scan [path] --deep  # Use LSP for accurate type extraction (requires Node.js)
    codetrellis scan [path] --cache-optimize  # Post-process for LLM prompt caching (A5.1)
    codetrellis sync               # Sync only changed files
    codetrellis show               # Show compressed matrix
    codetrellis watch              # Watch for changes
    codetrellis prompt             # Print prompt-ready matrix
    codetrellis prompt --tier full # Print with full detail (no truncation)
    codetrellis prompt --tier logic # Include function bodies and code logic (NEW)
    codetrellis init               # Initialize CodeTrellis in current directory
    codetrellis init --ai          # + generate AI integration files (Copilot, Claude, Cursor)
    codetrellis init --ai --force  # Overwrite existing AI integration files
    codetrellis init --update-ai   # Regenerate AI files from existing matrix (no re-scan)
    codetrellis cache-optimize     # Optimize matrix for prompt caching (A5.1)
    codetrellis mcp                # Start MCP server (A5.2)
    codetrellis context <file>     # Get JIT context for a file (A5.3)
    codetrellis skills             # List AI-ready skills (A5.5)

Output Tiers:
    compact  - Maximum compression, truncation allowed (~800-2000 tokens)
    prompt   - Balanced, NO truncation on important items (DEFAULT)
    full     - Complete extraction, NO truncation anywhere
    logic    - Includes implementation details: function bodies, control flow, API calls (NEW in v4.1)
               Addresses: "AI can't see specific code logic" limitation
    json     - Machine-readable full export

Deep Analysis (--deep):
    Uses TypeScript Language Server Protocol for 99% accurate type extraction.
    Requires Node.js 18+ to be installed. Falls back to regex if unavailable.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional


def _get_build_timestamp() -> str:
    """Get build timestamp, respecting CODETRELLIS_BUILD_TIMESTAMP env var for determinism.
    
    Per B4 Phase 0 and C3: When CODETRELLIS_BUILD_TIMESTAMP is set, use it
    to ensure deterministic, reproducible builds across runs.
    """
    return os.environ.get("CODETRELLIS_BUILD_TIMESTAMP", datetime.now().isoformat())

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from codetrellis import __version__ as VERSION
from codetrellis.scanner import ProjectScanner, ProjectMatrix
from codetrellis.compressor import MatrixCompressor
from codetrellis.interfaces import OutputTier
from codetrellis.build_contract import (
    ExitCode,
    BuildContractError,
    InputValidator,
    OutputSchemaValidator,
    DeterminismEnforcer,
    ErrorBudget,
    BuildContractVerifier,
    get_versioned_cache_dir,
)


def _parse_tier(tier_str: str) -> OutputTier:
    """Parse tier string to OutputTier enum"""
    tier_map = {
        "compact": OutputTier.COMPACT,
        "prompt": OutputTier.PROMPT,
        "full": OutputTier.FULL,
        "json": OutputTier.JSON,
        "logic": OutputTier.LOGIC,  # v4.1: Implementation logic tier
    }
    return tier_map.get(tier_str.lower(), OutputTier.PROMPT)


def _generate_progress_section(project_root: Path, matrix) -> str:
    """Generate a progress detail section with TODOs/FIXMEs for inclusion in the matrix.

    Phase A fix: Renamed from [ACTIONABLE_ITEMS] to [PROGRESS_DETAIL] to avoid
    overwriting the compressor's [ACTIONABLE_ITEMS] section (G-10).
    This section provides additional per-file progress breakdown.
    Enhanced: Now includes placeholder details and incomplete areas.
    """
    lines = []

    # Get progress data from matrix
    progress = getattr(matrix, 'progress', None)
    if not progress:
        return ""

    summary = progress.get('summary', {})
    completion = progress.get('completion', 0)
    files = progress.get('files', [])
    high_priority = progress.get('high_priority', [])
    placeholders = progress.get('placeholders', [])

    # Only output if there's meaningful data
    if not files and not high_priority and not placeholders:
        return ""

    lines.append("\n[PROGRESS_DETAIL]")
    placeholder_count = summary.get('placeholders', len(placeholders))
    lines.append(
        f"# Completion: {completion}% | TODOs: {summary.get('todos', 0)} "
        f"| FIXMEs: {summary.get('fixmes', 0)} | Placeholders: {placeholder_count}"
    )

    # Show high priority items first
    if high_priority:
        lines.append("# High-priority items:")
        for item in high_priority[:10]:
            file_path = item.get('file_path', item.get('file', 'unknown'))
            line_num = item.get('line_number', item.get('line', 0))
            text = item.get('text', '')[:100]
            marker_type = item.get('marker_type', 'TODO')
            lines.append(f"  {marker_type}|{Path(file_path).name}:{line_num}|{text}")

    # Show placeholder details — what's incomplete and where
    if placeholders:
        lines.append("# Placeholder/stub locations (incomplete areas):")
        for ph in placeholders[:20]:
            file_path = ph.get('file_path', ph.get('file', 'unknown'))
            line_num = ph.get('line_number', ph.get('line', 0))
            text = ph.get('text', ph.get('content', ''))[:80]
            ph_type = ph.get('type', ph.get('marker_type', 'PLACEHOLDER'))
            lines.append(f"  {ph_type}|{Path(file_path).name}:{line_num}|{text}")
        if len(placeholders) > 20:
            lines.append(f"  # ... +{len(placeholders) - 20} more placeholders")
    elif placeholder_count > 0:
        # Placeholders exist in summary but no detail — look in files
        lines.append(f"# {placeholder_count} placeholders detected across files:")
        placeholder_files = [
            f for f in files
            if f.get('placeholders', 0) > 0 or f.get('stubs', 0) > 0
        ]
        for pf in placeholder_files[:15]:
            fname = Path(pf.get('file', 'unknown')).name
            ph_count = pf.get('placeholders', 0) + pf.get('stubs', 0)
            lines.append(f"  {fname}|placeholders:{ph_count}")

    # Show per-file progress summary
    if files:
        lines.append("# Per-file progress:")
        for f in files[:15]:
            fname = Path(f.get('file', 'unknown')).name
            fcomp = f.get('completion', 0)
            ftodos = f.get('todos', 0)
            ffixmes = f.get('fixmes', 0)
            if ftodos > 0 or ffixmes > 0:
                lines.append(f"  {fname}|{fcomp}%|todos:{ftodos}|fixmes:{ffixmes}")

    # Show incomplete areas summary
    incomplete_areas = progress.get('incomplete_areas', [])
    if incomplete_areas:
        lines.append("# Incomplete areas:")
        for area in incomplete_areas[:10]:
            if isinstance(area, dict):
                lines.append(f"  {area.get('area', '')}|{area.get('reason', '')}")
            elif isinstance(area, str):
                lines.append(f"  {area}")

    return "\n".join(lines) if len(lines) > 2 else ""


def _generate_overview_section(project_root: Path, matrix) -> str:
    """Generate a project structure overview for inclusion in the matrix.

    This helps AI understand the project architecture quickly.
    """
    lines = []
    lines.append("\n[PROJECT_STRUCTURE]")
    lines.append("# Directory structure with file counts and purposes")

    # Get overview data from matrix
    overview = getattr(matrix, 'overview', None)
    if overview:
        # Phase A fix: dict keys are 'type' and 'techStack' (from to_dict()),
        # not 'project_type' and 'tech_stack'
        project_type = overview.get('type', overview.get('project_type', 'Unknown'))
        tech_stack = overview.get('techStack', overview.get('tech_stack', []))
        patterns = overview.get('patterns', [])

        lines.append(f"# Type: {project_type}")
        if tech_stack:
            lines.append(f"# Stack: {', '.join(tech_stack[:5])}")
        if patterns:
            lines.append(f"# Patterns: {', '.join(patterns[:5])}")

    # Add directory info
    dirs = getattr(matrix, 'directory_summary', {})
    if dirs:
        lines.append("# Key directories:")
        # Sort by file count descending for importance
        sorted_dirs = sorted(dirs.items(), key=lambda x: x[1].get('files', 0), reverse=True)
        for dir_name, info in sorted_dirs[:20]:  # Limit to 20
            file_count = info.get('files', 0)
            purpose = info.get('purpose', '')[:50]
            languages = info.get('languages', [])
            lang_str = ','.join(languages[:2]) if languages else ''
            parts = [f"{dir_name}/", f"files:{file_count}"]
            if lang_str:
                parts.append(lang_str)
            if purpose:
                parts.append(purpose)
            lines.append(f"  {'|'.join(parts)}")

    return "\n".join(lines) if len(lines) > 2 else ""


def _generate_practices_section(
    project_root: Path,
    matrix,
    level: Optional[str] = None,
    categories: Optional[list] = None,
    practices_format: str = "standard",
    max_practice_tokens: Optional[int] = None,
) -> str:
    """Generate a best practices section for inclusion in the matrix.

    This provides AI with context-aware coding best practices relevant
    to the detected tech stack and project structure.

    Args:
        project_root: Path to the project root
        matrix: ProjectMatrix with detected project info
        level: Optional minimum practice level filter (beginner, intermediate, advanced, expert)
        categories: Optional list of categories to include (general, style, performance, etc.)
        practices_format: Output verbosity level:
            - "minimal": IDs and titles only (~50% token reduction)
            - "standard": Brief descriptions + truncated examples (default)
            - "comprehensive": Full descriptions, all examples, references

    Returns:
        Formatted string for inclusion in compressed output
    """
    try:
        from codetrellis.bpl import PracticeSelector, PracticeLevel, PracticeCategory
        from codetrellis.bpl.selector import SelectionCriteria, ProjectContext
    except ImportError:
        return ""  # BPL not available

    lines = []
    lines.append("\n[BEST_PRACTICES]")
    lines.append(f"# Context-aware coding best practices for this project (BPL v1.0) [{practices_format.upper()}]")

    try:
        # Build context from matrix and select practices
        selector = PracticeSelector()

        # Adjust max practices based on format (comprehensive needs fewer for token budget)
        max_practices_by_format = {
            "minimal": 25,      # Can include more since output is compact
            "standard": 15,     # Default balanced limit
            "comprehensive": 8  # Fewer practices but with full detail
        }
        max_practices = max_practices_by_format.get(practices_format.lower(), 15)

        # Build criteria from filters
        criteria = SelectionCriteria(
            max_practices=max_practices,
            max_tokens=max_practice_tokens,
        )

        # Filter by level if specified
        if level:
            try:
                min_level = PracticeLevel[level.upper()]
                criteria.levels = [lvl for lvl in PracticeLevel if lvl.value >= min_level.value]
            except (KeyError, AttributeError):
                pass  # Invalid level, skip filtering

        # Filter by categories if specified
        if categories:
            try:
                criteria.categories = [PracticeCategory[c.upper()] for c in categories]
            except (KeyError, AttributeError):
                pass  # Invalid categories, skip filtering

        # Select practices based on project context
        bpl_output = selector.select_for_project(matrix, criteria)

        if not bpl_output.practices:
            return ""

        selected = bpl_output.practices

        # Group by category for organization
        by_category = {}
        for practice in selected:
            cat_name = practice.category.value
            if cat_name not in by_category:
                by_category[cat_name] = []
            by_category[cat_name].append(practice)

        # Add context summary
        if bpl_output.context_summary:
            lines.append(f"# Context: {bpl_output.context_summary}")

        lines.append(f"# Practices: {len(selected)} selected (from {bpl_output.total_available} available)")

        # Per-category limits based on format
        per_category_limits = {
            "minimal": 8,       # More practices allowed
            "standard": 5,      # Default
            "comprehensive": 3  # Fewer but detailed
        }
        per_category_limit = per_category_limits.get(practices_format.lower(), 5)

        # Output practices by category with format-specific rendering
        for category, practices in by_category.items():
            lines.append(f"## {category.upper()}")
            for practice in practices[:per_category_limit]:
                lines.extend(_format_practice(practice, practices_format))

        return "\n".join(lines)

    except Exception as e:
        # Log error but don't fail the scan
        lines.append(f"# BPL Error: {str(e)[:100]}")
        return "\n".join(lines)


def _format_practice(practice, format_level: str) -> list:
    """Format a single practice based on the output format level.

    Args:
        practice: Practice object to format
        format_level: "minimal", "standard", or "comprehensive"

    Returns:
        List of formatted lines for this practice
    """
    lines = []
    format_level = format_level.lower()

    # MINIMAL: Just ID, level, and title
    if format_level == "minimal":
        lines.append(f"  {practice.id}|{practice.level.value}|{practice.title}")
        return lines

    # STANDARD: ID + title + brief description + truncated example
    if format_level == "standard":
        lines.append(f"  {practice.id}|{practice.level.value}|{practice.title}")

        # Brief description (first 150 chars)
        if practice.content and practice.content.description:
            brief = practice.content.description[:150].replace('\n', ' ')
            if len(practice.content.description) > 150:
                brief += "..."
            lines.append(f"    {brief}")

        # Truncated code example (first 3 lines, max 80 chars each)
        if practice.content and practice.content.good_examples:
            first_example = practice.content.good_examples[0]
            example_lines = first_example.split('\n')[:3]
            for ex_line in example_lines:
                lines.append(f"    > {ex_line[:80]}")
        return lines

    # COMPREHENSIVE: Full detail - complete description, all examples, anti-patterns, references
    if format_level == "comprehensive":
        lines.append(f"  {practice.id}|{practice.level.value}|{practice.title}")

        # Full description
        if practice.content and practice.content.description:
            # Split into readable lines
            desc = practice.content.description
            lines.append("    Description:")
            for desc_line in desc.split('\n'):
                lines.append(f"      {desc_line}")

        # All good examples
        if practice.content and practice.content.good_examples:
            lines.append(f"    Good Examples ({len(practice.content.good_examples)}):")
            for i, example in enumerate(practice.content.good_examples, 1):
                lines.append(f"      Example {i}:")
                for ex_line in example.split('\n'):
                    lines.append(f"        > {ex_line}")

        # Bad examples (anti-patterns) if available
        if practice.content and practice.content.bad_examples:
            lines.append(f"    Anti-patterns ({len(practice.content.bad_examples)}):")
            for i, bad in enumerate(practice.content.bad_examples, 1):
                lines.append(f"      Avoid {i}:")
                for bad_line in bad.split('\n'):
                    lines.append(f"        X {bad_line}")

        # References if available (inside content)
        if practice.content and practice.content.references:
            lines.append("    References:")
            for ref in practice.content.references:
                lines.append(f"      - {ref}")

        # Tags for searchability (inside content)
        if practice.content and practice.content.tags:
            lines.append(f"    Tags: {', '.join(practice.content.tags)}")

        return lines

    # Default to standard
    return _format_practice(practice, "standard")


def get_codetrellis_dir(project_root: Path) -> Path:
    """Get the .codetrellis directory path"""
    return project_root / ".codetrellis"


def get_cache_dir(project_root: Path) -> Path:
    """Get the cache directory path"""
    ct_dir = get_codetrellis_dir(project_root)
    project_name = project_root.name
    return ct_dir / "cache" / VERSION / project_name


def init_codetrellis(project_root: Path):
    """Initialize CodeTrellis directory structure"""
    ct_dir = get_codetrellis_dir(project_root)
    cache_dir = get_cache_dir(project_root)
    files_dir = cache_dir / "files"

    # Create directories
    files_dir.mkdir(parents=True, exist_ok=True)

    # Create config file
    config = {
        "version": VERSION,
        "project": project_root.name,
        "created": datetime.now().isoformat(),
        "ignore": [
            "node_modules",
            "dist",
            "build",
            ".git",
            ".angular",
            "__pycache__",
            ".pytest_cache",
            ".venv",
            "venv",
            "coverage",
            "*.spec.ts",
            "*.test.ts",
            "*.spec.py",
            "*.test.py"
        ],
        "parsers": {
            "typescript": True,
            "python": True,
            "proto": True,
            "angular": True
        },
        "maxTokens": 2000,
        "compression": "high"
    }

    config_file = ct_dir / "config.json"
    config_file.write_text(json.dumps(config, indent=2, sort_keys=True))

    print(f"[CodeTrellis] Initialized in {ct_dir}")
    return ct_dir


def scan_project(path: str, output_format: str = "prompt", tier: OutputTier = OutputTier.PROMPT,
                 deep: bool = False, parallel: bool = False, max_workers: Optional[int] = None,
                 include_progress: bool = False, include_overview: bool = False,
                 include_practices: bool = False, practices_level: Optional[str] = None,
                 practices_categories: Optional[list] = None, practices_format: str = "standard",
                 max_practice_tokens: Optional[int] = None, cache_optimize: bool = False) -> int:
    """Scan project and create matrix.

    Per C4 Error Contract, returns standardized exit codes:
    - 0: Success — all outputs written
    - 1: Partial failure — some extractors failed
    - 2: Configuration error
    - 3: Fatal error — no outputs written

    Args:
        path: Project path to scan
        output_format: Output format (prompt, json)
        tier: Output tier (compact, prompt, full, logic)
        deep: Use LSP for accurate type extraction
        parallel: Enable parallel processing
        max_workers: Number of workers for parallel processing
        include_progress: Include TODO/FIXME progress section
        include_overview: Include project structure overview
        include_practices: Include context-aware best practices from BPL
        practices_level: Minimum practice level filter (beginner, intermediate, advanced, expert)
        practices_categories: List of categories to include
        practices_format: Output format for practices (minimal, standard, comprehensive)
        max_practice_tokens: Maximum token budget for the [BEST_PRACTICES] section
        cache_optimize: Post-process for LLM prompt caching (A5.1)

    Returns:
        Exit code per C4 Error Contract (0, 1, 2, or 3).
    """
    project_root = Path(path).resolve()
    error_budget = ErrorBudget()

    # C1: Input validation
    input_validator = InputValidator(str(project_root))
    input_errors = input_validator.validate()
    if input_errors:
        for err in input_errors:
            print(f"[CodeTrellis] CONFIG ERROR: {err}", file=sys.stderr)
        return int(ExitCode.CONFIGURATION_ERROR)

    print(f"[CodeTrellis] Scanning project: {project_root.name}")
    print(f"[CodeTrellis] Path: {project_root}")
    print(f"[CodeTrellis] Output tier: {tier.value}")
    if deep:
        print("[CodeTrellis] Deep mode: ENABLED (LSP type extraction)")
    if parallel:
        workers = max_workers or "auto"
        print(f"[CodeTrellis] Parallel mode: ENABLED ({workers} workers)")
    if include_progress:
        print("[CodeTrellis] Progress section: ENABLED")
    if include_overview:
        print("[CodeTrellis] Overview section: ENABLED")
    if include_practices:
        print("[CodeTrellis] Best Practices (BPL): ENABLED")
        print(f"[CodeTrellis]   Format: {practices_format}")
        if practices_level:
            print(f"[CodeTrellis]   Level filter: {practices_level}+")
        if practices_categories:
            print(f"[CodeTrellis]   Categories: {', '.join(practices_categories)}")
    if cache_optimize:
        print("[CodeTrellis] Cache optimization: ENABLED (A5.1)")
    print()

    # Initialize if needed
    ct_dir = get_codetrellis_dir(project_root)
    if not ct_dir.exists():
        init_codetrellis(project_root)

    cache_dir = get_cache_dir(project_root)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Scan (with optional parallel processing)
    scanner = ProjectScanner(parallel=parallel, max_workers=max_workers)
    matrix = scanner.scan(str(project_root))

    # LSP deep extraction if requested
    lsp_output = ""
    lsp_stats = None
    if deep:
        from codetrellis.extractors.lsp_extractor import LSPExtractor
        lsp_extractor = LSPExtractor(project_root)

        if lsp_extractor.is_available():
            print("[CodeTrellis] Running LSP extraction...")
            if lsp_extractor.extract():
                lsp_stats = lsp_extractor.stats
                lsp_output = lsp_extractor.get_compact_output()
                print(f"[CodeTrellis] LSP: {lsp_stats.interfaces_found} interfaces, "
                      f"{lsp_stats.types_found} types, {lsp_stats.classes_found} classes, "
                      f"{lsp_stats.components_found} components, {lsp_stats.services_found} services, "
                      f"{lsp_stats.stores_found} stores in {lsp_stats.processing_time_ms}ms")
            else:
                print(f"[CodeTrellis] LSP extraction failed: {lsp_extractor.stats.fallback_reason}")
                print("[CodeTrellis] Falling back to regex extraction")
        else:
            print("[CodeTrellis] LSP not available (requires Node.js and tsconfig.json)")
            print("[CodeTrellis] Using regex extraction")

    # Compress with selected tier
    compressor = MatrixCompressor(tier=tier)
    compressed = compressor.compress(matrix)

    # Append LSP output if available
    if lsp_output:
        compressed = compressed + "\n" + lsp_output

    # Append progress section if requested
    if include_progress:
        progress_output = _generate_progress_section(project_root, matrix)
        if progress_output:
            compressed = compressed + "\n" + progress_output

    # Append overview section if requested
    if include_overview:
        overview_output = _generate_overview_section(project_root, matrix)
        if overview_output:
            compressed = compressed + "\n" + overview_output

    # Append best practices section if requested (BPL)
    # When BPL is enabled, replace the compressor's basic [BEST_PRACTICES] section
    # with the richer BPL-generated section to avoid duplicate headers.
    if include_practices:
        practices_output = _generate_practices_section(
            project_root, matrix,
            level=practices_level,
            categories=practices_categories,
            practices_format=practices_format,
            max_practice_tokens=max_practice_tokens,
        )
        if practices_output:
            # Remove the compressor's basic [BEST_PRACTICES] section before appending BPL output.
            # The compressor section starts with "[BEST_PRACTICES]" and continues until
            # the next section header "[..." or end of string.
            import re
            compressed = re.sub(
                r'\[BEST_PRACTICES\]\n?(?:(?!\[)[^\n]*\n?)*',
                '',
                compressed,
                count=1,
            )
            compressed = compressed.rstrip() + "\n" + practices_output

    # Apply cache optimization if requested (A5.1)
    cache_result = None
    if cache_optimize:
        from codetrellis.cache_optimizer import optimize_matrix_prompt
        print("[CodeTrellis] Applying prompt cache optimization...")
        cache_result = optimize_matrix_prompt(compressed, insert_cache_breaks=True)
        compressed = cache_result.optimized_prompt
        print(f"[CodeTrellis] Cache optimization: {cache_result.sections_reordered} sections reordered")
        print(f"[CodeTrellis]   Static sections: {cache_result.static_token_estimate} tokens (cached)")
        print(f"[CodeTrellis]   Volatile sections: {cache_result.volatile_token_estimate} tokens (refreshed)")
        if cache_result.estimated_cache_hit_ratio > 0:
            print(f"[CodeTrellis]   Estimated cache hit ratio: {cache_result.estimated_cache_hit_ratio:.0%}")
            print(f"[CodeTrellis]   Estimated cost savings: {cache_result.estimated_cost_savings_pct:.0%}")

    # Save files
    # 1. Save metadata JSON
    metadata_file = cache_dir / "_metadata.json"
    metadata = {
        "version": VERSION,
        "project": project_root.name,
        "generated": _get_build_timestamp(),
        "deep_mode": deep,
        "lsp_stats": {
            "used": lsp_stats.lsp_used if lsp_stats else False,
            "interfaces": lsp_stats.interfaces_found if lsp_stats else 0,
            "types": lsp_stats.types_found if lsp_stats else 0,
            "classes": lsp_stats.classes_found if lsp_stats else 0,
            "components": lsp_stats.components_found if lsp_stats else 0,
            "services": lsp_stats.services_found if lsp_stats else 0,
            "stores": lsp_stats.stores_found if lsp_stats else 0,
            "processing_time_ms": lsp_stats.processing_time_ms if lsp_stats else 0,
        } if deep else None,
        "stats": {
            "totalFiles": matrix.total_files,
            "schemas": len(matrix.schemas),
            "dtos": len(matrix.dtos),
            "controllers": len(matrix.controllers),
            "components": len(matrix.components),
            "services": len(matrix.services),
            "grpcServices": len(matrix.grpc_services),
            "enums": len(matrix.enums),
            "interfaces": len(matrix.interfaces),        # v2.0
            "types": len(matrix.types),                  # v2.0
            "angularServices": len(matrix.angular_services), # v2.0
            "stores": len(matrix.stores),                # v2.0
        },
        "dependencies": matrix.dependencies,
        "cache_optimization": {
            "enabled": cache_optimize,
            "sections_reordered": cache_result.sections_reordered if cache_result else 0,
            "static_tokens": cache_result.static_token_estimate if cache_result else 0,
            "volatile_tokens": cache_result.volatile_token_estimate if cache_result else 0,
            "cache_hit_ratio": cache_result.estimated_cache_hit_ratio if cache_result else 0,
            "cost_savings_pct": cache_result.estimated_cost_savings_pct if cache_result else 0,
        } if cache_optimize else None,
    }
    metadata_file.write_text(json.dumps(metadata, indent=2, sort_keys=True, default=str))

    # 2. Save compressed prompt
    prompt_file = cache_dir / "matrix.prompt"
    prompt_file.write_text(compressed)

    # 3. Save full JSON matrix
    json_file = cache_dir / "matrix.json"
    json_file.write_text(json.dumps(matrix.to_dict(), indent=2, sort_keys=True, default=str))

    # Calculate stats
    estimated_tokens = len(compressed) // 4

    print()
    print("="*60)
    print("SCAN COMPLETE")
    print("="*60)
    print(f"Files scanned:  {matrix.total_files}")
    print(f"Schemas:        {len(matrix.schemas)}")
    print(f"DTOs:           {len(matrix.dtos)}")
    print(f"Controllers:    {len(matrix.controllers)}")
    print(f"Components:     {len(matrix.components)}")
    print(f"Services:       {len(matrix.services)}")
    print(f"gRPC Services:  {len(matrix.grpc_services)}")
    print(f"Enums:          {len(matrix.enums)}")
    print(f"Interfaces:     {len(matrix.interfaces)}")       # v2.0
    print(f"Types:          {len(matrix.types)}")            # v2.0
    print(f"AngularServices:{len(matrix.angular_services)}") # v2.0
    print(f"Stores:         {len(matrix.stores)}")           # v2.0
    print()
    print(f"Estimated tokens: ~{estimated_tokens}")
    print()
    print("Output files:")
    print(f"  Prompt:   {prompt_file}")
    print(f"  JSON:     {json_file}")
    print(f"  Metadata: {metadata_file}")
    print()

    if output_format == "prompt":
        print("="*60)
        print("COMPRESSED MATRIX (copy this to inject into prompts):")
        print("="*60)
        print(compressed)

    # C4: Return proper exit code
    return int(error_budget.exit_code)


def show_matrix(path: str, section: str = None):
    """Show the compressed matrix"""
    project_root = Path(path).resolve()
    cache_dir = get_cache_dir(project_root)
    prompt_file = cache_dir / "matrix.prompt"

    if not prompt_file.exists():
        print("[CodeTrellis] No matrix found. Run 'codetrellis scan' first.")
        return

    content = prompt_file.read_text()

    if section:
        # Filter to specific section
        lines = content.split("\n")
        in_section = False
        section_lines = []

        for line in lines:
            if line.startswith(f"[{section.upper()}"):
                in_section = True
            elif line.startswith("[") and in_section:
                break

            if in_section:
                section_lines.append(line)

        if section_lines:
            print("\n".join(section_lines))
        else:
            print(f"[CodeTrellis] Section '{section}' not found")
    else:
        print(content)


def print_prompt(path: str, include_header: bool = True, tier: OutputTier = OutputTier.PROMPT):
    """Print prompt-ready matrix for injection"""
    project_root = Path(path).resolve()
    cache_dir = get_cache_dir(project_root)

    # If non-default tier requested, regenerate from JSON
    if tier != OutputTier.PROMPT:
        json_file = cache_dir / "matrix.json"
        if not json_file.exists():
            print("[CodeTrellis] No matrix found. Run 'codetrellis scan' first.", file=sys.stderr)
            return

        # Load matrix JSON and recompress with requested tier
        import json as json_mod
        matrix_data = json_mod.loads(json_file.read_text())

        # Create a simple namespace object for compressor
        class MatrixObj:
            pass

        matrix = MatrixObj()
        for key, value in matrix_data.items():
            setattr(matrix, key, value)

        compressor = MatrixCompressor(tier=tier)
        content = compressor.compress(matrix)
    else:
        prompt_file = cache_dir / "matrix.prompt"
        if not prompt_file.exists():
            print("[CodeTrellis] No matrix found. Run 'codetrellis scan' first.", file=sys.stderr)
            return
        content = prompt_file.read_text()

    if include_header:
        tier_label = f" tier={tier.value}" if tier != OutputTier.PROMPT else ""
        print(f"[CodeTrellis:PROJECT_CONTEXT{tier_label}]")
        print(content)
        print("[/CodeTrellis:PROJECT_CONTEXT]")
    else:
        print(content)


def watch_project(path: str):
    """Watch for file changes and auto-sync"""
    try:
        from codetrellis.watcher import FileWatcher
    except ImportError:
        print("[CodeTrellis] Error: watchdog not installed")
        print("[CodeTrellis] Install with: pip install watchdog")
        return

    project_root = Path(path).resolve()

    # Initialize if needed
    ct_dir = get_codetrellis_dir(project_root)
    if not ct_dir.exists():
        init_codetrellis(project_root)

    def on_change(file_paths):
        """Handle file changes — receives None (full resync) or List[Path] batch."""
        if file_paths is None:
            # Full resync
            scan_project(str(project_root), output_format=None)
        else:
            # True incremental build — pass changed file paths to builder
            # so it can skip re-scanning unchanged files (Angular SourceFileCache pattern)
            try:
                from codetrellis.builder import MatrixBuilder, BuildConfig
                builder = MatrixBuilder(str(project_root))
                changed_abs = [str(p) for p in file_paths]
                result = builder.build(config=BuildConfig(
                    incremental=True,
                    changed_files=changed_abs,
                ))
                if result.success:
                    files_label = f"{result.extractors_run}/{result.total_files} files"
                    print(f"[CodeTrellis] Incremental rebuild: {result.duration_ms:.0f}ms ({files_label})")
                else:
                    print("[CodeTrellis] Incremental failed, falling back to full scan")
                    scan_project(str(project_root), output_format=None)
            except Exception as exc:
                names = ", ".join(str(p.name) if hasattr(p, 'name') else str(p)
                                 for p in file_paths[:5])
                if len(file_paths) > 5:
                    names += f" (+{len(file_paths) - 5} more)"
                print(f"[CodeTrellis] Changed: {names} — full scan (error: {exc})")
                scan_project(str(project_root), output_format=None)

    watcher = FileWatcher(str(project_root), on_change)
    watcher.run_forever()


def sync_project(path: str, file_path: str = None):
    """Sync matrix (full or incremental) using MatrixBuilder."""
    project_root = Path(path).resolve()

    try:
        from codetrellis.builder import MatrixBuilder, BuildConfig
        builder = MatrixBuilder(str(project_root))
        result = builder.build(config=BuildConfig(incremental=True))
        if result.success:
            print(f"[CodeTrellis] Sync complete ({result.duration_ms:.0f}ms)")
        else:
            print("[CodeTrellis] Incremental sync failed, running full scan")
            scan_project(str(project_root), output_format=None)
            print("[CodeTrellis] Sync complete")
    except Exception:
        scan_project(str(project_root), output_format=None)
        print("[CodeTrellis] Sync complete")


def clean_project(path: str, version: Optional[str] = None) -> int:
    """Remove the .codetrellis/cache directory (or a specific version).

    Per B6 Command Matrix and C5 Cache Contract:
    - ``codetrellis clean`` removes entire cache
    - ``codetrellis clean --version X.Y.Z`` removes specific version

    Args:
        path: Project root path
        version: Optional specific version to clean (e.g. '4.16.0')

    Returns:
        Exit code: 0 on success, 2 on configuration/path error
    """
    import shutil

    project_root = Path(path).resolve()
    ct_dir = get_codetrellis_dir(project_root)

    if not ct_dir.exists():
        print(f"[CodeTrellis] No .codetrellis directory found in {project_root}")
        return 2

    cache_base = ct_dir / "cache"
    if not cache_base.exists():
        print("[CodeTrellis] No cache directory found — nothing to clean")
        return 0

    if version:
        target = cache_base / version
        if not target.exists():
            print(f"[CodeTrellis] Cache version {version} not found")
            return 2
        shutil.rmtree(target)
        print(f"[CodeTrellis] Cleaned cache for version {version}")
    else:
        shutil.rmtree(cache_base)
        print("[CodeTrellis] Cleaned all cache data")

    return 0


def export_section(path: str, sections: list, output_file: str = None):
    """Export specific sections of the matrix"""
    project_root = Path(path).resolve()
    cache_dir = get_cache_dir(project_root)
    prompt_file = cache_dir / "matrix.prompt"

    if not prompt_file.exists():
        print("[CodeTrellis] No matrix found. Run 'codetrellis scan' first.", file=sys.stderr)
        return

    content = prompt_file.read_text()
    lines = content.split("\n")

    exported_lines = []
    current_section = None
    in_target_section = False

    for line in lines:
        # Check if this is a section header
        if line.startswith("[") and "]" in line:
            section_name = line.split("]")[0][1:].split(":")[0]  # Handle [SECTION:subsection]
            current_section = section_name
            in_target_section = section_name.upper() in [s.upper() for s in sections]

        if in_target_section:
            exported_lines.append(line)

    result = "\n".join(exported_lines)

    if output_file:
        output_path = Path(output_file)
        output_path.write_text(result)
        print(f"[CodeTrellis] Exported {len(sections)} section(s) to {output_path}")
    else:
        print(result)


def validate_project(path: str, verbose: bool = False):
    """Validate extraction completeness and report issues"""
    project_root = Path(path).resolve()
    cache_dir = get_cache_dir(project_root)
    metadata_file = cache_dir / "_metadata.json"
    json_file = cache_dir / "matrix.json"

    if not metadata_file.exists() or not json_file.exists():
        print("[CodeTrellis] No matrix found. Run 'codetrellis scan' first.", file=sys.stderr)
        return

    # Load metadata and matrix
    metadata = json.loads(metadata_file.read_text())
    matrix_data = json.loads(json_file.read_text())

    issues = []
    warnings = []

    # Check for empty sections
    stats = metadata.get('stats', {})
    for key, count in stats.items():
        if count == 0 and key not in ['grpcServices', 'enums']:  # Some may legitimately be 0
            warnings.append(f"Section '{key}' is empty")

    # Check for Angular projects - should have components
    if matrix_data.get('components') == [] and matrix_data.get('angular_services') == []:
        package_json = project_root / 'package.json'
        if package_json.exists():
            pkg = json.loads(package_json.read_text())
            deps = pkg.get('dependencies', {})
            if '@angular/core' in deps:
                issues.append("Angular project detected but no components/services extracted")

    # Check for NestJS projects - should have controllers/schemas
    if matrix_data.get('controllers') == [] and matrix_data.get('schemas') == []:
        package_json = project_root / 'package.json'
        if package_json.exists():
            pkg = json.loads(package_json.read_text())
            deps = pkg.get('dependencies', {})
            if '@nestjs/core' in deps:
                issues.append("NestJS project detected but no controllers/schemas extracted")

    # Check for missing interfaces in components
    components = matrix_data.get('components', [])
    interfaces = matrix_data.get('interfaces', [])
    interface_names = {i.get('name') for i in interfaces if isinstance(i, dict)}

    for comp in components:
        if isinstance(comp, dict):
            used_interfaces = comp.get('interfaces', [])
            for iface in used_interfaces:
                if isinstance(iface, str) and iface not in interface_names:
                    warnings.append(f"Component uses undefined interface: {iface}")

    # Print results
    print("="*60)
    print("CodeTrellis VALIDATION REPORT")
    print("="*60)
    print(f"Project: {project_root.name}")
    print(f"Version: {metadata.get('version', 'unknown')}")
    print(f"Generated: {metadata.get('generated', 'unknown')}")
    print()

    if issues:
        print(f"❌ ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
        print()

    if warnings:
        print(f"⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings[:10]:  # Limit to 10
            print(f"  - {warning}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more")
        print()

    if not issues and not warnings:
        print("✅ All validations passed!")
    elif not issues:
        print("✅ No critical issues found")

    print()
    print("Stats:")
    for key, count in stats.items():
        status = "✅" if count > 0 else "⚪"
        print(f"  {status} {key}: {count}")


def coverage_report(path: str, detailed: bool = False):
    """Report extraction coverage statistics"""
    project_root = Path(path).resolve()
    cache_dir = get_cache_dir(project_root)
    metadata_file = cache_dir / "_metadata.json"

    if not metadata_file.exists():
        print("[CodeTrellis] No matrix found. Run 'codetrellis scan' first.", file=sys.stderr)
        return

    metadata = json.loads(metadata_file.read_text())
    stats = metadata.get('stats', {})

    # Count actual files in project
    file_counts = {
        'components': len(list(project_root.rglob('*.component.ts'))),
        'services': len(list(project_root.rglob('*.service.ts'))),
        'stores': len(list(project_root.rglob('*.store.ts'))),
        'controllers': len(list(project_root.rglob('*.controller.ts'))),
        'schemas': len(list(project_root.rglob('*.schema.ts'))),
        'dtos': len(list(project_root.rglob('*.dto.ts'))),
    }

    # Filter out node_modules
    for key in file_counts:
        pattern = f'*.{key.rstrip("s")}.ts' if not key.endswith('es') else f'*.{key[:-2]}.ts'
        actual_files = [
            f for f in project_root.rglob(pattern)
            if 'node_modules' not in str(f) and 'dist' not in str(f)
        ]
        file_counts[key] = len(actual_files)

    print("="*60)
    print("CodeTrellis COVERAGE REPORT")
    print("="*60)
    print(f"Project: {project_root.name}")
    print()

    print("Extraction Coverage:")
    print("-"*40)

    total_files = 0
    total_extracted = 0

    # Map stats keys to file counts keys
    mapping = {
        'components': 'components',
        'angularServices': 'services',
        'stores': 'stores',
        'controllers': 'controllers',
        'schemas': 'schemas',
        'dtos': 'dtos',
    }

    for stat_key, file_key in mapping.items():
        extracted = stats.get(stat_key, 0)
        available = file_counts.get(file_key, 0)

        if available > 0:
            percentage = (extracted / available) * 100
            status = "✅" if percentage >= 90 else "⚠️" if percentage >= 50 else "❌"
            print(f"  {status} {stat_key}: {extracted}/{available} ({percentage:.0f}%)")
        else:
            print(f"  ⚪ {stat_key}: {extracted}/0 (N/A)")

        total_files += available
        total_extracted += extracted

    print("-"*40)

    if total_files > 0:
        overall = (total_extracted / total_files) * 100
        print(f"  Overall: {total_extracted}/{total_files} ({overall:.0f}%)")

    print()
    print("Additional Extractions:")
    for key in ['interfaces', 'types', 'enums', 'grpcServices']:
        count = stats.get(key, 0)
        if count > 0:
            print(f"  ✅ {key}: {count}")

    # LSP stats if available
    lsp_stats = metadata.get('lsp_stats')
    if lsp_stats and lsp_stats.get('used'):
        print()
        print("LSP Extraction (Deep Mode):")
        print(f"  Interfaces: {lsp_stats.get('interfaces', 0)}")
        print(f"  Types: {lsp_stats.get('types', 0)}")
        print(f"  Classes: {lsp_stats.get('classes', 0)}")
        print(f"  Processing time: {lsp_stats.get('processing_time_ms', 0)}ms")


def show_progress(path: str, detailed: bool = False, by_module: bool = False, as_json: bool = False):
    """Show project progress - TODOs, completion, blockers"""
    project_root = Path(path).resolve()
    cache_dir = get_cache_dir(project_root)
    json_file = cache_dir / "matrix.json"

    if not json_file.exists():
        # Scan first
        print("[CodeTrellis] No matrix found. Scanning project first...")
        scan_project(str(project_root), output_format=None)

    # Reload after potential scan
    json_file = cache_dir / "matrix.json"
    if not json_file.exists():
        print("[CodeTrellis] Error: Could not create matrix.", file=sys.stderr)
        return

    matrix_data = json.loads(json_file.read_text())
    progress = matrix_data.get('progress', {})

    if as_json:
        print(json.dumps(progress, indent=2))
        return

    print("="*60)
    print("📊 PROJECT PROGRESS REPORT")
    print("="*60)
    print(f"Project: {project_root.name}")
    print()

    # Overall completion
    completion = progress.get('completion', 100)
    completion_bar = "█" * (completion // 5) + "░" * (20 - completion // 5)
    print(f"Completion: [{completion_bar}] {completion}%")
    print()

    # Summary
    summary = progress.get('summary', {})
    print("Summary:")
    print(f"  📝 TODOs:       {summary.get('todos', 0)}")
    print(f"  🔧 FIXMEs:      {summary.get('fixmes', 0)}")
    print(f"  ⚠️  Deprecated:  {summary.get('deprecated', 0)}")
    print(f"  🚧 Placeholders: {summary.get('placeholders', 0)}")
    print()

    # Per-language breakdown
    _LANG_MAP = {
        '.py': 'Python', '.ts': 'TypeScript', '.tsx': 'TypeScript',
        '.js': 'JavaScript', '.jsx': 'JavaScript', '.mjs': 'JavaScript',
        '.java': 'Java', '.kt': 'Kotlin', '.cs': 'C#',
        '.go': 'Go', '.rs': 'Rust', '.rb': 'Ruby', '.php': 'PHP',
        '.swift': 'Swift', '.dart': 'Dart', '.lua': 'Lua',
        '.c': 'C', '.cpp': 'C++', '.h': 'C/C++',
        '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS',
        '.sql': 'SQL', '.sh': 'Shell', '.bash': 'Shell',
        '.r': 'R', '.scala': 'Scala', '.vue': 'Vue',
    }
    files = progress.get('files', [])
    if files:
        lang_stats = {}
        for f in files:
            fp = f.get('file', '')
            ext = '.' + fp.rsplit('.', 1)[-1] if '.' in fp else ''
            lang = _LANG_MAP.get(ext.lower(), 'Other')
            if lang not in lang_stats:
                lang_stats[lang] = {'files': 0, 'todos': 0, 'fixmes': 0, 'placeholders': 0}
            lang_stats[lang]['files'] += 1
            lang_stats[lang]['todos'] += f.get('todos', 0)
            lang_stats[lang]['fixmes'] += f.get('fixmes', 0)
            lang_stats[lang]['placeholders'] += f.get('placeholders', 0)

        # Show only languages with issues or multiple files
        active_langs = {k: v for k, v in lang_stats.items()
                        if v['todos'] + v['fixmes'] + v['placeholders'] > 0 or v['files'] >= 3}
        if active_langs:
            print("🌐 BY LANGUAGE:")
            for lang, stats in sorted(active_langs.items(), key=lambda x: x[1]['files'], reverse=True):
                issues = stats['todos'] + stats['fixmes'] + stats['placeholders']
                issue_str = f" ({stats['todos']}T/{stats['fixmes']}F/{stats['placeholders']}P)" if issues else ""
                print(f"  • {lang}: {stats['files']} files{issue_str}")
            print()

    # Blockers
    blockers = progress.get('blockers', [])
    if blockers:
        print("🚫 BLOCKERS:")
        for blocker in blockers:
            file_name = blocker.get('file', 'unknown').split('/')[-1]
            msg = blocker.get('message', '')[:50]
            print(f"  • {file_name}: {msg}")
        print()

    # High priority items
    high_priority = progress.get('high_priority', [])
    if high_priority:
        print("⚡ HIGH PRIORITY:")
        for item in high_priority[:5]:
            marker_type = item.get('type', 'TODO').upper()
            file_name = item.get('file', 'unknown').split('/')[-1]
            msg = item.get('message', '')[:40]
            line = item.get('line', 0)
            print(f"  • [{marker_type}] {file_name}:{line} - {msg}")
        if len(high_priority) > 5:
            print(f"  ... and {len(high_priority) - 5} more")
        print()

    # Detailed mode: show all files
    if detailed:
        files = progress.get('files', [])
        if files:
            print("📁 FILES WITH ISSUES:")
            for f in files[:20]:
                file_name = f.get('file', 'unknown').split('/')[-1]
                status = f.get('status', 'complete')
                file_completion = f.get('completion', 100)
                todos = f.get('todos', 0)
                fixmes = f.get('fixmes', 0)

                status_icon = "✅" if status == 'complete' else "🔄" if status == 'in-progress' else "⏸️"
                print(f"  {status_icon} {file_name} ({file_completion}%) - {todos} TODOs, {fixmes} FIXMEs")

            if len(files) > 20:
                print(f"  ... and {len(files) - 20} more files")

    # By module mode
    if by_module:
        files = progress.get('files', [])
        if files:
            modules = {}
            for f in files:
                file_path = f.get('file', '')
                # Extract module from path (first directory after src/)
                parts = file_path.split('/')
                if 'src' in parts:
                    idx = parts.index('src')
                    module = parts[idx + 1] if idx + 1 < len(parts) else 'root'
                else:
                    module = parts[0] if parts else 'root'

                if module not in modules:
                    modules[module] = {'todos': 0, 'fixmes': 0, 'files': 0}
                modules[module]['todos'] += f.get('todos', 0)
                modules[module]['fixmes'] += f.get('fixmes', 0)
                modules[module]['files'] += 1

            print("\n📦 BY MODULE:")
            for module, stats in sorted(modules.items(), key=lambda x: x[1]['todos'], reverse=True):
                print(f"  • {module}/: {stats['files']} files, {stats['todos']} TODOs, {stats['fixmes']} FIXMEs")


def show_overview(path: str, as_json: bool = False, as_markdown: bool = False):
    """Show project overview for onboarding"""
    project_root = Path(path).resolve()
    cache_dir = get_cache_dir(project_root)
    json_file = cache_dir / "matrix.json"

    if not json_file.exists():
        # Scan first
        print("[CodeTrellis] No matrix found. Scanning project first...")
        scan_project(str(project_root), output_format=None)

    # Reload after potential scan
    json_file = cache_dir / "matrix.json"
    if not json_file.exists():
        print("[CodeTrellis] Error: Could not create matrix.", file=sys.stderr)
        return

    matrix_data = json.loads(json_file.read_text())
    overview = matrix_data.get('overview', {})

    if as_json:
        print(json.dumps(overview, indent=2))
        return

    if as_markdown:
        _print_overview_markdown(overview, project_root)
        return

    print("="*60)
    print("📚 PROJECT OVERVIEW")
    print("="*60)

    name = overview.get('name', project_root.name)
    proj_type = overview.get('type', 'Unknown')
    version = overview.get('version', '')
    description = overview.get('description', '')

    print(f"Name: {name}")
    print(f"Type: {proj_type}")
    if version:
        print(f"Version: {version}")
    if description:
        print(f"Description: {description}")
    print()

    # Tech stack
    tech_stack = overview.get('techStack', [])
    if tech_stack:
        print("🔧 TECH STACK:")
        for tech in tech_stack:
            print(f"  • {tech}")
        print()

    # Entry points
    entry_points = overview.get('entryPoints', [])
    if entry_points:
        print("🚀 ENTRY POINTS:")
        for entry in entry_points:
            file_path = entry.get('file', '')
            kind = entry.get('kind', 'entry')
            desc = entry.get('description', '')
            print(f"  • {file_path} ({kind}){' - ' + desc if desc else ''}")
        print()

    # Directories
    directories = overview.get('directories', [])
    if directories:
        print("📁 KEY DIRECTORIES:")
        sorted_dirs = sorted(directories, key=lambda x: x.get('fileCount', 0), reverse=True)
        for d in sorted_dirs[:10]:
            name = d.get('name', '')
            count = d.get('fileCount', 0)
            purpose = d.get('purpose', '')
            print(f"  • {name}/ ({count} files){' - ' + purpose if purpose else ''}")
        print()

    # Patterns
    patterns = overview.get('patterns', [])
    if patterns:
        print("🏗️ ARCHITECTURE PATTERNS:")
        for pattern in patterns:
            print(f"  • {pattern}")
        print()

    # Key dependencies
    deps = overview.get('dependencies', [])
    core_deps = [d for d in deps if d.get('category') == 'core']
    if core_deps:
        print("📦 KEY DEPENDENCIES:")
        for dep in core_deps[:8]:
            name = dep.get('name', '')
            version = dep.get('version', '')
            print(f"  • {name} {version}")
        print()

    # API connections
    apis = overview.get('apiConnections', [])
    if apis:
        print("🔌 API CONNECTIONS:")
        for api in apis:
            name = api.get('name', '')
            protocol = api.get('protocol', 'http')
            base_url = api.get('baseUrl', '')
            print(f"  • {name} ({protocol}): {base_url}")
        print()

    # Available scripts
    scripts = overview.get('scripts', {})
    if scripts:
        print("📜 AVAILABLE SCRIPTS:")
        for name, cmd in list(scripts.items())[:8]:
            cmd_preview = cmd[:50] + '...' if len(cmd) > 50 else cmd
            print(f"  • npm run {name}: {cmd_preview}")


def _print_overview_markdown(overview: dict, project_root: Path):
    """Print overview in markdown format"""
    name = overview.get('name', project_root.name)
    proj_type = overview.get('type', 'Unknown')
    version = overview.get('version', '')
    description = overview.get('description', '')

    print(f"# {name}")
    print()
    if description:
        print(f"> {description}")
        print()

    print(f"**Type:** {proj_type}")
    if version:
        print(f"**Version:** {version}")
    print()

    # Tech stack
    tech_stack = overview.get('techStack', [])
    if tech_stack:
        print("## Tech Stack")
        print()
        for tech in tech_stack:
            print(f"- {tech}")
        print()

    # Entry points
    entry_points = overview.get('entryPoints', [])
    if entry_points:
        print("## Entry Points")
        print()
        print("| File | Type | Description |")
        print("|------|------|-------------|")
        for entry in entry_points:
            file_path = entry.get('file', '')
            kind = entry.get('kind', 'entry')
            desc = entry.get('description', '-')
            print(f"| `{file_path}` | {kind} | {desc} |")
        print()

    # Directories
    directories = overview.get('directories', [])
    if directories:
        print("## Project Structure")
        print()
        print("| Directory | Files | Purpose |")
        print("|-----------|-------|---------|")
        sorted_dirs = sorted(directories, key=lambda x: x.get('fileCount', 0), reverse=True)
        for d in sorted_dirs[:10]:
            name = d.get('name', '')
            count = d.get('fileCount', 0)
            purpose = d.get('purpose', '-')
            print(f"| `{name}/` | {count} | {purpose} |")
        print()

    # Patterns
    patterns = overview.get('patterns', [])
    if patterns:
        print("## Architecture Patterns")
        print()
        for pattern in patterns:
            print(f"- `{pattern}`")
        print()

    # Getting started
    scripts = overview.get('scripts', {})
    if scripts:
        print("## Getting Started")
        print()
        print("```bash")
        print("# Install dependencies")
        if 'install' in scripts:
            print("npm install")

        # Development
        dev_scripts = ['dev', 'start', 'serve']
        for s in dev_scripts:
            if s in scripts:
                print(f"npm run {s}")
                break
        print("```")


def onboard_project(path: str):
    """Interactive onboarding guide"""
    project_root = Path(path).resolve()

    print("="*60)
    print("🎓 WELCOME TO PROJECT ONBOARDING")
    print("="*60)
    print()
    print(f"Project: {project_root.name}")
    print()
    print("This guide will help you understand the project structure.")
    print()

    # First show overview
    show_overview(path)

    print()
    print("-"*60)
    print()

    # Then show progress
    show_progress(path)

    print()
    print("-"*60)
    print("🎯 NEXT STEPS:")
    print("-"*60)
    print("1. Review the entry points to understand app flow")
    print("2. Check the key directories for code organization")
    print("3. Look at high-priority TODOs for areas needing work")
    print("4. Run 'codetrellis show --section SCHEMAS' to see data models")
    print("5. Run 'codetrellis show --section COMPONENTS' to see UI components")
    print()
    print("💡 Tip: Use 'codetrellis prompt' to get a condensed matrix for AI prompts!")


def plugins_command(action: str, plugin_name: str = None):
    """Manage plugins"""
    from codetrellis.plugins import PluginRegistry, discover_plugins, load_builtin_plugins

    registry = PluginRegistry()

    if action == "list":
        # Load built-in plugins
        builtin = load_builtin_plugins()

        print("="*60)
        print("CodeTrellis PLUGINS")
        print("="*60)

        print("\nBuilt-in Language Plugins:")
        for plugin in builtin['language']:
            meta = plugin.metadata
            print(f"  • {meta.name} v{meta.version} - {meta.description}")

        print("\nBuilt-in Framework Plugins:")
        for plugin in builtin['framework']:
            meta = plugin.metadata
            caps = ", ".join(c.name for c in meta.capabilities[:5])
            print(f"  • {meta.name} v{meta.version} - {meta.description}")
            print(f"    Capabilities: {caps}")

        # Discover installed plugins
        discovered = discover_plugins()

        if discovered['language'] or discovered['framework']:
            print("\nInstalled Plugins:")
            for plugin in discovered['language'] + discovered['framework']:
                meta = plugin.metadata
                print(f"  • {meta.name} v{meta.version} - {meta.description}")

    elif action == "info" and plugin_name:
        from codetrellis.plugins.discovery import get_plugin_info
        from codetrellis.plugins.builtin import BUILTIN_FRAMEWORK_PLUGINS, BUILTIN_LANGUAGE_PLUGINS

        # Find plugin
        all_plugins = [p() for p in BUILTIN_LANGUAGE_PLUGINS + BUILTIN_FRAMEWORK_PLUGINS]
        plugin = None
        for p in all_plugins:
            if p.metadata.name == plugin_name:
                plugin = p
                break

        if plugin:
            info = get_plugin_info(plugin)
            print(f"\nPlugin: {info['name']} v{info['version']}")
            print(f"Description: {info['description']}")
            print(f"Author: {info['author']}")
            print(f"Type: {info['type']}")
            print(f"Capabilities: {', '.join(info.get('capabilities', []))}")
            print(f"File extensions: {', '.join(info.get('file_extensions', []))}")
            print(f"Config files: {', '.join(info.get('config_files', []))}")
        else:
            print(f"Plugin '{plugin_name}' not found")

    elif action == "detect":
        path = plugin_name or "."
        project_root = Path(path).resolve()

        builtin = load_builtin_plugins()
        for plugin in builtin['language']:
            registry.register_language_plugin(plugin)
        for plugin in builtin['framework']:
            registry.register_framework_plugin(plugin)

        detected = registry.detect_frameworks(project_root)

        print(f"\nDetected frameworks in {project_root.name}:")
        if detected:
            for plugin in detected:
                print(f"  ✅ {plugin.metadata.name}")
        else:
            print("  No frameworks detected")

    else:
        print("Usage:")
        print("  codetrellis plugins list           # List all plugins")
        print("  codetrellis plugins info <name>    # Show plugin details")
        print("  codetrellis plugins detect [path]  # Detect frameworks in project")


def validate_repos_command(args):
    """Run public repository validation framework (Phase D — WS-8).

    Supports three modes:
    1. Full run: clone repos, scan, score, and analyze
    2. Score only: score existing results
    3. Analyze only: generate Gap Analysis Round 2
    """
    import subprocess
    import time as _time

    ct_root = Path(__file__).parent.parent
    scripts_dir = ct_root / "scripts" / "validation"

    # Resolve paths
    repos_file = Path(args.repos_file) if args.repos_file else scripts_dir / "repos.txt"
    results_dir = Path(args.results_dir) if args.results_dir else scripts_dir / "validation-results"
    repos_dir = Path(args.repos_dir)

    if not repos_file.exists():
        print(f"[CodeTrellis] ❌ repos.txt not found: {repos_file}")
        print(f"[CodeTrellis]    Expected at: {scripts_dir / 'repos.txt'}")
        return

    verbose = getattr(args, "verbose", False)

    # Score-only mode
    if getattr(args, "score_only", False):
        print("[CodeTrellis] Phase D — Quality Scoring Mode")
        scorer_path = scripts_dir / "quality_scorer.py"
        if not scorer_path.exists():
            print(f"[CodeTrellis] ❌ quality_scorer.py not found: {scorer_path}")
            return
        cmd = [sys.executable, str(scorer_path), "--results-dir", str(results_dir)]
        if verbose:
            cmd.append("--verbose")
        cmd.extend(["--output", str(results_dir / "quality_report.json")])
        subprocess.run(cmd)
        return

    # Analyze-only mode
    if getattr(args, "analyze_only", False):
        print("[CodeTrellis] Phase D — Gap Analysis Round 2 Generation")
        analyzer_path = scripts_dir / "analyze_results.py"
        if not analyzer_path.exists():
            print(f"[CodeTrellis] ❌ analyze_results.py not found: {analyzer_path}")
            return
        output_path = ct_root / "docs" / "gap_analysis" / "CODETRELLIS_GAP_ANALYSIS_ROUND2.md"
        cmd = [sys.executable, str(analyzer_path),
               "--results-dir", str(results_dir),
               "--output", str(output_path)]
        subprocess.run(cmd)
        return

    # Full validation run
    print("[CodeTrellis] Phase D — Full Public Repository Validation")
    print(f"[CodeTrellis] Repos file:   {repos_file}")
    print(f"[CodeTrellis] Repos dir:    {repos_dir}")
    print(f"[CodeTrellis] Results dir:  {results_dir}")
    print()

    # Create results directory
    results_dir.mkdir(parents=True, exist_ok=True)

    # Read repos
    repos = []
    with open(repos_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            repos.append(line)

    max_repos = getattr(args, "max", 0)
    if max_repos > 0:
        repos = repos[:max_repos]

    timeout = getattr(args, "timeout", 300)
    total = len(repos)
    passed = 0
    failed = 0

    # Initialize CSV
    csv_path = results_dir / "summary.csv"
    with open(csv_path, "w") as f:
        f.write("repo,repo_name,exit_code,duration_s,output_lines,file_count,has_traceback\n")

    for i, repo in enumerate(repos, 1):
        repo_name = repo.replace("/", "_")
        repo_dir = repos_dir / repo_name
        prompt_file = results_dir / f"{repo_name}.prompt"
        log_file = results_dir / f"{repo_name}.log"

        print(f"[{i}/{total}] {repo}")

        # Clone (shallow)
        if not repo_dir.exists():
            print("  📥 Cloning...")
            try:
                clone_result = subprocess.run(
                    ["git", "clone", "--depth", "1", "--single-branch",
                     f"https://github.com/{repo}.git", str(repo_dir)],
                    capture_output=True, text=True, timeout=120
                )
                if clone_result.returncode != 0:
                    print("  ❌ Clone failed")
                    with open(log_file, "w") as f:
                        f.write(clone_result.stderr)
                    failed += 1
                    with open(csv_path, "a") as f:
                        f.write(f"{repo},{repo_name},-1,0,0,0,false\n")
                    print()
                    continue
            except subprocess.TimeoutExpired:
                print("  ❌ Clone timed out")
                failed += 1
                with open(csv_path, "a") as f:
                    f.write(f"{repo},{repo_name},-2,120,0,0,false\n")
                print()
                continue
        else:
            print("  📁 Using cached clone")

        # Count files
        file_count = sum(1 for p in repo_dir.rglob("*") if p.is_file())
        print(f"  📊 Files: {file_count}")

        # Scan
        print("  🔍 Scanning...")
        start = _time.time()
        has_traceback = False

        try:
            scan_result = subprocess.run(
                [sys.executable, "-m", "codetrellis.cli", "scan", str(repo_dir), "--optimal"],
                capture_output=True, text=True,
                timeout=timeout,
                cwd=str(ct_root),
                env={**os.environ, "PYTHONPATH": str(ct_root)}
            )
            exit_code = scan_result.returncode
            duration = int(_time.time() - start)

            # Save output
            with open(prompt_file, "w") as f:
                f.write(scan_result.stdout)
            with open(log_file, "w") as f:
                f.write(scan_result.stderr)
                f.write(f"\nTIMING: {duration}s (exit={exit_code})\n")

            if "Traceback" in scan_result.stderr:
                has_traceback = True

        except subprocess.TimeoutExpired:
            exit_code = 124
            duration = timeout
            with open(prompt_file, "w") as f:
                f.write("")
            with open(log_file, "w") as f:
                f.write(f"TIMEOUT after {timeout}s\n")
            print(f"  ⏰ TIMEOUT after {timeout}s")

        except Exception as e:
            exit_code = 1
            duration = int(_time.time() - start)
            with open(log_file, "w") as f:
                f.write(f"ERROR: {e}\nTIMING: {duration}s (exit=1)\n")
            print(f"  ❌ ERROR: {e}")

        # Count output lines
        line_count = 0
        if prompt_file.exists() and prompt_file.stat().st_size > 0:
            line_count = len(prompt_file.read_text().split("\n"))

        # Report
        if exit_code == 0 and line_count > 10:
            print(f"  ✅ OK ({line_count} lines, {duration}s)")
            passed += 1
        elif exit_code == 124:
            failed += 1
        else:
            print(f"  ❌ FAILED (exit={exit_code}, {line_count} lines, {duration}s)")
            failed += 1

        # Append CSV
        with open(csv_path, "a") as f:
            f.write(f"{repo},{repo_name},{exit_code},{duration},{line_count},{file_count},{has_traceback}\n")

        if verbose:
            print(f"  Log: {log_file}")

        print()

    # Summary
    pass_rate = (passed / total * 100) if total else 0
    print("=" * 60)
    print(f"  VALIDATION COMPLETE: {passed}/{total} passed ({pass_rate:.1f}%)")
    print(f"  Target: >70%  {'🎉 MET' if pass_rate >= 70 else '⚠️  NOT MET'}")
    print(f"  CSV: {csv_path}")
    print("=" * 60)
    print()
    print("[CodeTrellis] Next steps:")
    print("  codetrellis validate-repos --score-only    # Run quality scoring")
    print("  codetrellis validate-repos --analyze-only   # Generate Gap Analysis Round 2")


def cache_optimize_command(args):
    """Optimize existing matrix.prompt for LLM prompt caching (A5.1).

    Reorders sections: static/structural first, volatile last.
    Inserts cache_control breakpoints for Anthropic/Google APIs.
    """
    from codetrellis.cache_optimizer import optimize_matrix_prompt, get_anthropic_cache_messages

    project_root = Path(args.path).resolve()
    cache_dir = get_cache_dir(project_root)
    prompt_file = cache_dir / "matrix.prompt"

    if not prompt_file.exists():
        print("[CodeTrellis] No matrix.prompt found. Run 'codetrellis scan' first.")
        return

    raw_prompt = prompt_file.read_text()
    insert_breaks = not getattr(args, "no_cache_breaks", False)

    result = optimize_matrix_prompt(raw_prompt, insert_cache_breaks=insert_breaks)

    # Anthropic messages format
    if getattr(args, "anthropic_messages", False):
        messages = get_anthropic_cache_messages(result.optimized_prompt)
        print(json.dumps(messages, indent=2))
        return

    # Stats-only mode
    if getattr(args, "stats", False):
        print("=" * 60)
        print("CACHE OPTIMIZATION ANALYSIS")
        print("=" * 60)
        print(f"Total sections:           {result.total_sections}")
        print(f"Sections reordered:       {result.sections_reordered}")
        print(f"Cache breaks inserted:    {result.cache_breaks_inserted}")
        print()
        print(f"Static tokens (cached):   ~{result.static_token_estimate}")
        print(f"Volatile tokens (fresh):  ~{result.volatile_token_estimate}")
        print(f"Total tokens:             ~{result.static_token_estimate + result.volatile_token_estimate}")
        print()
        print(f"Estimated cache hit ratio: {result.estimated_cache_hit_ratio:.0%}")
        print(f"Estimated cost savings:    {result.estimated_cost_savings_pct:.0%}")
        print()
        print("Section order (stability → priority):")
        for i, name in enumerate(result.section_order, 1):
            stability = result.stability_map.get(name, "unknown")
            print(f"  {i:2d}. [{name}] ({stability})")
        return

    # Write optimized prompt
    output_path = getattr(args, "output", None)
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.optimized_prompt)
        print(f"[CodeTrellis] Optimized matrix written to: {output_path}")
    else:
        prompt_file.write_text(result.optimized_prompt)
        print(f"[CodeTrellis] matrix.prompt optimized in place: {prompt_file}")

    print(f"[CodeTrellis] {result.sections_reordered} sections reordered, "
          f"{result.cache_breaks_inserted} cache breaks inserted")
    print(f"[CodeTrellis] Estimated cache hit ratio: {result.estimated_cache_hit_ratio:.0%}, "
          f"cost savings: {result.estimated_cost_savings_pct:.0%}")


def mcp_command(args):
    """Start MCP server for matrix access (A5.2).

    Exposes matrix sections as MCP resources and search/context as tools.
    Default transport: stdio (for Claude Desktop, Cursor, etc.)
    """
    from codetrellis.mcp_server import MatrixMCPServer

    project_root = Path(args.path).resolve()
    matrix_path = getattr(args, "matrix_path", None)

    server = MatrixMCPServer(str(project_root), matrix_path=matrix_path)

    if not server.load_matrix():
        print("[CodeTrellis] Failed to load matrix. Run 'codetrellis scan' first.",
              file=sys.stderr)
        sys.exit(1)

    sections = len(server._sections) if server._sections else 0
    print(f"[CodeTrellis] MCP Server starting for: {project_root.name}", file=sys.stderr)
    print(f"[CodeTrellis] Matrix loaded: {sections} sections", file=sys.stderr)
    print(f"[CodeTrellis] Resources: {len(server.list_resources())}", file=sys.stderr)
    print(f"[CodeTrellis] Tools: {len(server.list_tools())}", file=sys.stderr)
    print("[CodeTrellis] Transport: stdio (JSON-RPC 2.0)", file=sys.stderr)
    print("[CodeTrellis] Ready. Waiting for requests...", file=sys.stderr)

    server.run_stdio()


def context_command(args):
    """Get JIT context for a specific file (A5.3).

    Auto-discovers which matrix sections are relevant to a given file
    based on file extension, path patterns, and content mentions.
    """
    from codetrellis.jit_context import JITContextProvider

    project_root = Path(getattr(args, "project", ".")).resolve()
    file_path = args.file
    max_tokens = getattr(args, "max_tokens", 30000)
    as_json = getattr(args, "json", False)
    sections_only = getattr(args, "sections_only", False)

    # Load matrix
    cache_dir = get_cache_dir(project_root)
    prompt_file = cache_dir / "matrix.prompt"

    if not prompt_file.exists():
        print("[CodeTrellis] No matrix.prompt found. Run 'codetrellis scan' first.")
        return

    raw_prompt = prompt_file.read_text()

    # Parse raw prompt into sections dict (JITContextProvider expects Dict[str, str])
    import re as _re
    sections = {}
    current_section = None
    current_lines = []
    for line in raw_prompt.split("\n"):
        header_match = _re.match(r'^\[([A-Z][A-Z0-9_]*)\]', line)
        if header_match:
            if current_section:
                sections[current_section] = "\n".join(current_lines)
            current_section = header_match.group(1)
            current_lines = [line]
        elif current_section:
            current_lines.append(line)
    if current_section:
        sections[current_section] = "\n".join(current_lines)

    provider = JITContextProvider(sections, max_tokens=max_tokens)
    result = provider.resolve_context(file_path)

    if as_json:
        output = {
            "file": file_path,
            "sections_included": result.sections_included,
            "relevance_scores": result.relevance_scores,
            "token_estimate": result.token_estimate,
        }
        if not sections_only:
            output["context"] = result.context
        print(json.dumps(output, indent=2))
    elif sections_only:
        print(f"[CodeTrellis] JIT Context for: {file_path}")
        print(f"[CodeTrellis] Sections ({len(result.sections_included)}):")
        for section in result.sections_included:
            score = result.relevance_scores.get(section, 0)
            print(f"  [{section}] (relevance: {score:.1f})")
        print(f"\n[CodeTrellis] Token estimate: ~{result.token_estimate}")
    else:
        print(result.context)


def skills_command(args):
    """Generate and list AI-ready skills from the matrix (A5.5).

    Skills are auto-detected based on which matrix sections are present.
    Each skill includes instructions, required context, and validation steps.
    """
    from codetrellis.skills_generator import SkillsGenerator

    project_root = Path(args.path).resolve()
    as_json = getattr(args, "json", False)
    claude_format = getattr(args, "claude_format", False)
    skill_name = getattr(args, "skill", None)
    context_skill = getattr(args, "context", None)

    # Load matrix and parse into sections
    cache_dir = get_cache_dir(project_root)
    prompt_file = cache_dir / "matrix.prompt"

    if not prompt_file.exists():
        print("[CodeTrellis] No matrix.prompt found. Run 'codetrellis scan' first.")
        return

    raw_prompt = prompt_file.read_text()

    # Parse into sections (reuse the MCP server's parser logic)
    import re as _re
    sections = {}
    current_section = None
    current_lines = []
    for line in raw_prompt.split("\n"):
        header_match = _re.match(r'^\[([A-Z][A-Z0-9_]*)\]', line)
        if header_match:
            if current_section:
                sections[current_section] = "\n".join(current_lines)
            current_section = header_match.group(1)
            current_lines = [line]
        elif current_section:
            current_lines.append(line)
    if current_section:
        sections[current_section] = "\n".join(current_lines)

    generator = SkillsGenerator(sections)
    skills = generator.generate()

    # Get context for a specific skill
    if context_skill:
        ctx = generator.get_skill_context(context_skill)
        if ctx:
            print(ctx)
        else:
            print(f"[CodeTrellis] Skill '{context_skill}' not found.")
            print(f"[CodeTrellis] Available: {', '.join(generator.list_skill_names())}")
        return

    # Show details for a specific skill
    if skill_name:
        skill = generator.get_skill_by_name(skill_name)
        if skill:
            if as_json:
                print(json.dumps(skill.to_dict(), indent=2))
            else:
                print(f"Skill: {skill.name}")
                print(f"Description: {skill.description}")
                print(f"Category: {skill.category}")
                print(f"Priority: {skill.priority}")
                print(f"Trigger: {skill.trigger}")
                print(f"Context sections: {', '.join(skill.context_sections)}")
                print(f"\nInstructions:\n{skill.instructions}")
        else:
            print(f"[CodeTrellis] Skill '{skill_name}' not found.")
            print(f"[CodeTrellis] Available: {', '.join(generator.list_skill_names())}")
        return

    # Claude Skills format
    if claude_format:
        print(json.dumps(generator.to_claude_skills_format(), indent=2))
        return

    # List all skills
    if as_json:
        print(json.dumps([s.to_dict() for s in skills], indent=2))
    else:
        print("=" * 60)
        print(f"AI-READY SKILLS ({len(skills)} available)")
        print("=" * 60)
        for skill in skills:
            print(f"\n  📋 {skill.name}")
            print(f"     {skill.description}")
            print(f"     Sections: {', '.join(skill.context_sections[:3])}"
                  + (f" +{len(skill.context_sections)-3}" if len(skill.context_sections) > 3 else ""))
        print()
        print("[CodeTrellis] Use --skill <name> for details, --context <name> for context")
        print("[CodeTrellis] Use --claude-format for Claude Skills export")


# ---------------------------------------------------------------------------
# export-context command (E6 — Multi-AI CLI context export)
# ---------------------------------------------------------------------------

# AI-tool format specifications
_AI_TOOL_FORMATS: dict[str, dict[str, str]] = {
    "claude": {
        "file": ".claude/instructions.md",
        "wrapper": "markdown",
        "header": "# Project Context — Auto-generated by CodeTrellis\n\n"
                  "This file provides the AI with deep project awareness.\n\n",
    },
    "cursor": {
        "file": ".cursorrules",
        "wrapper": "markdown",
        "header": "# Cursor Rules — Auto-generated by CodeTrellis\n\n",
    },
    "copilot": {
        "file": ".github/copilot-instructions.md",
        "wrapper": "markdown",
        "header": "# Copilot Instructions — Auto-generated by CodeTrellis\n\n",
    },
    "windsurf": {
        "file": ".windsurfrules",
        "wrapper": "markdown",
        "header": "# Windsurf Rules — Auto-generated by CodeTrellis\n\n",
    },
    "aider": {
        "file": ".aider.conf.yml",
        "wrapper": "yaml",
        "header": "# Aider configuration — Auto-generated by CodeTrellis\n",
    },
    "gemini": {
        "file": "GEMINI.md",
        "wrapper": "xml",
        "header": "",
    },
}


def _parse_matrix_sections(raw: str) -> dict[str, str]:
    """Parse a matrix.prompt file into section-name → content mapping."""
    import re as _re
    sections: dict[str, str] = {}
    current: str | None = None
    lines: list[str] = []
    for line in raw.split("\n"):
        m = _re.match(r'^\[([A-Z][A-Z0-9_]*)\]', line)
        if m:
            if current:
                sections[current] = "\n".join(lines)
            current = m.group(1)
            lines = [line]
        elif current:
            lines.append(line)
    if current:
        sections[current] = "\n".join(lines)
    return sections


def _format_for_tool(sections: dict[str, str], fmt: str, compact: bool) -> str:
    """Render sections into the requested output format."""
    body_parts: list[str] = []

    for name, content in sections.items():
        if compact:
            # Strip excessive blank lines
            import re as _re
            content = _re.sub(r'\n{3,}', '\n\n', content).strip()
        body_parts.append(content)

    body = "\n\n".join(body_parts)

    if fmt in _AI_TOOL_FORMATS:
        spec = _AI_TOOL_FORMATS[fmt]
        wrapper = spec["wrapper"]
        header = spec["header"]
        if wrapper == "xml":
            return (
                "<project_context>\n"
                f"{header}"
                f"{body}\n"
                "</project_context>"
            )
        if wrapper == "yaml":
            # Aider expects read: key with a list of context files
            # We export the content as a comment block + instructions
            import textwrap
            wrapped = textwrap.indent(body, "# ")
            return (
                f"{header}"
                "# Project matrix context (paste relevant parts into .aider.conf.yml)\n"
                f"{wrapped}\n"
            )
        # markdown (default)
        return f"{header}{body}\n"

    # raw / json / markdown / xml
    if fmt == "json":
        return json.dumps(
            {"sections": {k: v for k, v in sections.items()},
             "meta": {"tool": "codetrellis", "version": VERSION}},
            indent=2,
        )
    if fmt == "xml":
        parts = ['<codetrellis_context version="' + VERSION + '">']
        for name, content in sections.items():
            parts.append(f'  <section name="{name}">')
            parts.append(f'    {content}')
            parts.append('  </section>')
        parts.append('</codetrellis_context>')
        return "\n".join(parts)
    if fmt == "markdown":
        md: list[str] = [f"# CodeTrellis Context Export (v{VERSION})\n"]
        for name, content in sections.items():
            md.append(f"## {name}\n")
            md.append(content)
            md.append("")
        return "\n".join(md)
    # raw
    return body


def export_context_command(args) -> None:
    """Export matrix context formatted for a specific AI tool (E6).

    Supports output for Claude Code, Cursor, Aider, Gemini CLI,
    Copilot, Windsurf, and generic raw/json/markdown/xml formats.
    """
    project_root = Path(args.path).resolve()
    cache_dir = get_cache_dir(project_root)
    prompt_file = cache_dir / "matrix.prompt"

    if not prompt_file.exists():
        print("[CodeTrellis] No matrix.prompt found. Run 'codetrellis scan' first.")
        return

    raw = prompt_file.read_text()
    sections = _parse_matrix_sections(raw)

    # Filter to requested sections
    requested = getattr(args, "sections", None)
    if requested:
        normalised = {s.upper().replace("-", "_") for s in requested}
        sections = {k: v for k, v in sections.items() if k in normalised}
        if not sections:
            print(f"[CodeTrellis] No matching sections. Available: "
                  f"{', '.join(_parse_matrix_sections(raw).keys())}")
            return

    # Token budget (rough estimate: 1 token ≈ 4 chars)
    max_tokens = getattr(args, "max_tokens", 0) or 0
    if max_tokens > 0:
        budget_chars = max_tokens * 4
        trimmed: dict[str, str] = {}
        used = 0
        for k, v in sections.items():
            if used + len(v) > budget_chars:
                remaining = budget_chars - used
                if remaining > 200:
                    trimmed[k] = v[:remaining] + "\n[... truncated for token budget ...]"
                break
            trimmed[k] = v
            used += len(v)
        sections = trimmed

    fmt = getattr(args, "format", "raw") or "raw"
    compact = getattr(args, "compact", False)
    output = _format_for_tool(sections, fmt, compact)

    # Determine output destination
    out_path = getattr(args, "output", None)
    if out_path is None and fmt in _AI_TOOL_FORMATS:
        # Use the canonical file path for the AI tool
        out_path = str(project_root / _AI_TOOL_FORMATS[fmt]["file"])

    if out_path:
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(output)
        print(f"[CodeTrellis] Exported {len(sections)} sections "
              f"({len(output):,} chars) → {out_file}")
    else:
        print(output)

    # Clipboard
    if getattr(args, "clipboard", False):
        try:
            import subprocess as _sp
            proc = _sp.Popen(["pbcopy"], stdin=_sp.PIPE)
            proc.communicate(output.encode())
            print("[CodeTrellis] Copied to clipboard ✓")
        except Exception:
            print("[CodeTrellis] Could not copy to clipboard (pbcopy not available)")


def main():
    parser = argparse.ArgumentParser(
        prog="codetrellis",
        description="Project Self-Awareness System - AI context injection tool"
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"CodeTrellis {VERSION}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan project and create matrix")
    scan_parser.add_argument("path", nargs="?", default=".", help="Project path")
    scan_parser.add_argument("--json", action="store_true", help="Output as JSON")
    scan_parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    scan_parser.add_argument(
        "--tier", "-t",
        choices=["compact", "prompt", "full", "json", "logic"],
        default="prompt",
        help="Output tier: compact (truncated), prompt (default), full (detailed), logic (includes function bodies and code flow), json"
    )
    scan_parser.add_argument(
        "--deep", "-d",
        action="store_true",
        help="Use LSP for 99%% accurate type extraction (requires Node.js 18+)"
    )
    scan_parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Enable parallel processing for faster scanning (v4.1.1)"
    )
    scan_parser.add_argument(
        "--workers", "-w",
        type=int,
        default=None,
        help="Number of workers for parallel processing (default: auto)"
    )
    scan_parser.add_argument(
        "--optimal", "-o",
        action="store_true",
        help="Maximum quality: combines --tier logic --deep --parallel + progress + overview (v4.1.2)"
    )
    scan_parser.add_argument(
        "--include-progress",
        action="store_true",
        help="Include TODO/FIXME progress section in output"
    )
    scan_parser.add_argument(
        "--include-overview",
        action="store_true",
        help="Include project structure overview in output"
    )
    scan_parser.add_argument(
        "--include-practices",
        action="store_true",
        help="Include context-aware best practices from BPL (Best Practices Library)"
    )
    scan_parser.add_argument(
        "--practices-level",
        choices=["beginner", "intermediate", "advanced", "expert"],
        default=None,
        help="Minimum practice level to include (default: all levels)"
    )
    scan_parser.add_argument(
        "--practices-categories",
        nargs="+",
        default=None,
        help="Filter practices by categories (e.g., --practices-categories style performance security)"
    )
    scan_parser.add_argument(
        "--practices-format",
        choices=["minimal", "standard", "comprehensive"],
        default="standard",
        help="Practices output format: minimal (IDs only), standard (brief), comprehensive (full detail)"
    )
    scan_parser.add_argument(
        "--max-practice-tokens",
        type=int,
        default=None,
        help="Maximum token budget for the [BEST_PRACTICES] section (~4 chars/token)"
    )
    scan_parser.add_argument(
        "--cache-optimize",
        action="store_true",
        help="Post-process output for LLM prompt caching (stable-first, volatile-last, cache breaks)"
    )
    scan_parser.add_argument(
        "--incremental",
        action="store_true",
        help="Incremental build: only re-extract changed files using cached results (B4 Phase 2)"
    )
    scan_parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Force deterministic output: sorted keys, fixed timestamps (B4 Phase 3)"
    )
    scan_parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: deterministic + parallel, suitable for CI/CD pipelines (B4 Phase 3)"
    )

    # distribute command (NEW!)
    dist_parser = subparsers.add_parser("distribute", help="Generate .codetrellis files in each component folder")
    dist_parser.add_argument("path", nargs="?", default=".", help="Project path")
    dist_parser.add_argument("--clean", action="store_true", help="Remove existing .codetrellis files first")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize CodeTrellis in directory")
    init_parser.add_argument("path", nargs="?", default=".", help="Project path")
    init_parser.add_argument("--ai", action="store_true",
                             help="Generate AI integration files (Copilot, Claude, Cursor, VS Code tasks)")
    init_parser.add_argument("--update-ai", action="store_true",
                             help="Regenerate AI integration files using existing matrix (no re-scan)")
    init_parser.add_argument("--force", action="store_true",
                             help="Overwrite existing AI integration files")

    # clean command (B4 Phase 0 — cache cleanup)
    clean_parser = subparsers.add_parser("clean", help="Remove .codetrellis/cache directory")
    clean_parser.add_argument("path", nargs="?", default=".", help="Project path")
    clean_parser.add_argument("--version", help="Remove only a specific version cache (e.g. 4.16.0)")

    # show command
    show_parser = subparsers.add_parser("show", help="Show compressed matrix")
    show_parser.add_argument("path", nargs="?", default=".", help="Project path")
    show_parser.add_argument("--section", "-s", help="Show specific section")
    show_parser.add_argument("--schemas", action="store_true", help="Show schemas only")
    show_parser.add_argument("--dtos", action="store_true", help="Show DTOs only")
    show_parser.add_argument("--services", action="store_true", help="Show services only")

    # prompt command
    prompt_parser = subparsers.add_parser("prompt", help="Print prompt-ready matrix")
    prompt_parser.add_argument("path", nargs="?", default=".", help="Project path")
    prompt_parser.add_argument("--no-header", action="store_true", help="Skip header/footer")
    prompt_parser.add_argument("--tokens", action="store_true", help="Show token count")
    prompt_parser.add_argument(
        "--tier", "-t",
        choices=["compact", "prompt", "full", "json", "logic"],
        default="prompt",
        help="Output tier: compact (truncated), prompt (default), full (detailed), logic (includes function bodies and code flow), json"
    )

    # watch command
    watch_parser = subparsers.add_parser("watch", help="Watch for changes")
    watch_parser.add_argument("path", nargs="?", default=".", help="Project path")

    # sync command
    sync_parser = subparsers.add_parser("sync", help="Sync matrix")
    sync_parser.add_argument("path", nargs="?", default=".", help="Project path")
    sync_parser.add_argument("--file", "-f", help="Sync specific file")

    # export command (NEW!)
    export_parser = subparsers.add_parser("export", help="Export specific sections")
    export_parser.add_argument("path", nargs="?", default=".", help="Project path")
    export_parser.add_argument(
        "--section", "-s",
        action="append",
        dest="sections",
        required=True,
        help="Section(s) to export (can be used multiple times)"
    )
    export_parser.add_argument("--output", "-o", help="Output file path")

    # validate command (NEW!)
    validate_parser = subparsers.add_parser("validate", help="Validate extraction completeness")
    validate_parser.add_argument("path", nargs="?", default=".", help="Project path")
    validate_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # coverage command (NEW!)
    coverage_parser = subparsers.add_parser("coverage", help="Show extraction coverage")
    coverage_parser.add_argument("path", nargs="?", default=".", help="Project path")
    coverage_parser.add_argument("--detailed", "-d", action="store_true", help="Detailed output")

    # progress command (NEW v2.1!)
    progress_parser = subparsers.add_parser("progress", help="Show project progress (TODOs, completion, blockers)")
    progress_parser.add_argument("path", nargs="?", default=".", help="Project path")
    progress_parser.add_argument("--detailed", "-d", action="store_true", help="Show all TODOs/FIXMEs")
    progress_parser.add_argument("--by-module", "-m", action="store_true", help="Group by module/directory")
    progress_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    # overview command (NEW v2.1!)
    overview_parser = subparsers.add_parser("overview", help="Show project overview for onboarding")
    overview_parser.add_argument("path", nargs="?", default=".", help="Project path")
    overview_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    overview_parser.add_argument("--markdown", "-md", action="store_true", help="Output as markdown")

    # onboard command (alias for overview with extra context)
    onboard_parser = subparsers.add_parser("onboard", help="Interactive onboarding guide")
    onboard_parser.add_argument("path", nargs="?", default=".", help="Project path")

    # verify command (B4 Phase 3 — quality gate verification)
    verify_parser = subparsers.add_parser("verify", help="Run build quality gate verification (D1)")
    verify_parser.add_argument("path", nargs="?", default=".", help="Project path")
    verify_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    # plugins command (NEW!)
    plugins_parser = subparsers.add_parser("plugins", help="Manage plugins")
    plugins_parser.add_argument(
        "action",
        choices=["list", "info", "detect"],
        help="Plugin action: list, info <name>, detect [path]"
    )
    plugins_parser.add_argument("plugin_name", nargs="?", help="Plugin name or path")

    # cache-optimize command (A5.1)
    cache_parser = subparsers.add_parser("cache-optimize",
        help="Optimize matrix.prompt for LLM prompt caching (A5.1)")
    cache_parser.add_argument("path", nargs="?", default=".", help="Project path")
    cache_parser.add_argument("--no-cache-breaks", action="store_true",
        help="Don't insert <!-- CACHE_BREAK --> markers")
    cache_parser.add_argument("--output", "-o", help="Output file path (default: overwrite matrix.prompt)")
    cache_parser.add_argument("--stats", action="store_true",
        help="Print optimization statistics only (don't write)")
    cache_parser.add_argument("--anthropic-messages", action="store_true",
        help="Output Anthropic API cache_control message format as JSON")

    # mcp command (A5.2)
    mcp_parser = subparsers.add_parser("mcp",
        help="Start MCP (Model Context Protocol) server for matrix (A5.2)")
    mcp_parser.add_argument("path", nargs="?", default=".", help="Project path")
    mcp_parser.add_argument("--matrix-path", default=None,
        help="Explicit path to matrix.prompt file")
    mcp_parser.add_argument("--port", type=int, default=None,
        help="HTTP port (default: stdio transport)")

    # context command (A5.3)
    context_parser = subparsers.add_parser("context",
        help="Get JIT context for a specific file (A5.3)")
    context_parser.add_argument("file", help="File path to get context for")
    context_parser.add_argument("--project", "-p", default=".", help="Project path")
    context_parser.add_argument("--max-tokens", type=int, default=30000,
        help="Maximum token budget (default: 30000)")
    context_parser.add_argument("--json", "-j", action="store_true",
        help="Output as JSON")
    context_parser.add_argument("--sections-only", action="store_true",
        help="Only list section names without content")

    # skills command (A5.5)
    skills_parser = subparsers.add_parser("skills",
        help="Generate and list AI-ready skills from matrix (A5.5)")
    skills_parser.add_argument("path", nargs="?", default=".", help="Project path")
    skills_parser.add_argument("--skill", "-s", help="Show details for a specific skill")
    skills_parser.add_argument("--json", "-j", action="store_true",
        help="Output as JSON")
    skills_parser.add_argument("--claude-format", action="store_true",
        help="Output in Claude Skills format")
    skills_parser.add_argument("--context", "-c", help="Get context for a specific skill")

    # export-context command (E6 — Multi-AI CLI context export)
    export_ctx_parser = subparsers.add_parser("export-context",
        help="Export matrix context formatted for specific AI tools (E6)")
    export_ctx_parser.add_argument("path", nargs="?", default=".", help="Project path")
    export_ctx_parser.add_argument(
        "--format", "-f",
        choices=["claude", "cursor", "aider", "gemini", "copilot", "windsurf",
                 "raw", "json", "markdown", "xml"],
        default="raw",
        help="Output format for the target AI tool"
    )
    export_ctx_parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    export_ctx_parser.add_argument(
        "--sections", "-s",
        nargs="*",
        help="Specific sections to include (default: all)"
    )
    export_ctx_parser.add_argument("--max-tokens", type=int, default=0,
        help="Maximum token budget (0 = unlimited)")
    export_ctx_parser.add_argument("--compact", action="store_true",
        help="Use compact output (fewer tokens)")
    export_ctx_parser.add_argument("--clipboard", "-c", action="store_true",
        help="Copy output to clipboard")

    # validate-repos command (Phase D — WS-8)
    vr_parser = subparsers.add_parser("validate-repos",
        help="Run public repo validation framework (Phase D)")
    vr_parser.add_argument("--repos-file", default=None,
        help="Path to repos.txt file (default: scripts/validation/repos.txt)")
    vr_parser.add_argument("--repos-dir", default="/tmp/codetrellis-validation",
        help="Directory to clone repos into (default: /tmp/codetrellis-validation)")
    vr_parser.add_argument("--results-dir", default=None,
        help="Directory for results (default: scripts/validation/validation-results)")
    vr_parser.add_argument("--max", type=int, default=0,
        help="Maximum repos to scan (0 = all)")
    vr_parser.add_argument("--timeout", type=int, default=300,
        help="Timeout per repo in seconds (default: 300)")
    vr_parser.add_argument("--score-only", action="store_true",
        help="Only run quality scoring on existing results")
    vr_parser.add_argument("--analyze-only", action="store_true",
        help="Only generate Gap Analysis Round 2 report")
    vr_parser.add_argument("--verbose", "-v", action="store_true",
        help="Verbose output")

    args = parser.parse_args()

    if args.command == "scan":
        output = "json" if getattr(args, "json", False) else "prompt"
        if getattr(args, "quiet", False):
            output = None

        # Check for --optimal flag (combines best options)
        optimal = getattr(args, "optimal", False)
        if optimal:
            tier = OutputTier.LOGIC  # Best tier for AI understanding
            deep = True
            parallel = True
            include_progress = True
            include_overview = True
            include_practices = True  # BPL enabled in optimal mode
            print("[CodeTrellis] OPTIMAL MODE: Using --tier logic --deep --parallel --include-progress --include-overview --include-practices")
        else:
            tier = _parse_tier(getattr(args, "tier", "prompt"))
            deep = getattr(args, "deep", False)
            parallel = getattr(args, "parallel", False)
            include_progress = getattr(args, "include_progress", False)
            include_overview = getattr(args, "include_overview", False)
            include_practices = getattr(args, "include_practices", False)

        # BPL practice filters
        practices_level = getattr(args, "practices_level", None)
        practices_categories = getattr(args, "practices_categories", None)
        practices_format = getattr(args, "practices_format", "standard")
        max_practice_tokens = getattr(args, "max_practice_tokens", None)

        workers = getattr(args, "workers", None)
        cache_optimize = getattr(args, "cache_optimize", False)
        incremental = getattr(args, "incremental", False)
        deterministic = getattr(args, "deterministic", False)
        ci_mode = getattr(args, "ci", False)

        # C1.3: CODETRELLIS_CI env var enables CI mode
        if os.environ.get("CODETRELLIS_CI"):
            ci_mode = True

        # Use MatrixBuilder for incremental/deterministic/ci builds
        if incremental or deterministic or ci_mode:
            from codetrellis.builder import MatrixBuilder, BuildConfig
            builder = MatrixBuilder(args.path)
            build_config = BuildConfig(
                tier=tier,
                deep=deep,
                parallel=parallel,
                max_workers=workers,
                include_progress=include_progress,
                include_overview=include_overview,
                include_practices=include_practices,
                practices_level=practices_level,
                practices_categories=practices_categories,
                practices_format=practices_format,
                max_practice_tokens=max_practice_tokens,
                cache_optimize=cache_optimize,
                incremental=incremental,
                deterministic=deterministic,
                ci=ci_mode,
            )
            result = builder.build(config=build_config)
            if result.success:
                print()
                print("=" * 60)
                print("BUILD COMPLETE (MatrixBuilder)")
                print("=" * 60)
                print(f"Files scanned:    {result.total_files}")
                print(f"Extractors run:   {result.extractors_run}")
                print(f"Cache hits:       {result.cache_hits}")
                print(f"Cache misses:     {result.cache_misses}")
                print(f"Duration:         {result.duration_ms:.0f}ms")
                if result.warnings:
                    print(f"Warnings:         {len(result.warnings)}")
                print(f"Output:           {result.matrix_prompt_path}")
            else:
                print(f"[CodeTrellis] Build FAILED (exit code {result.exit_code})")
                for err in result.errors:
                    print(f"  ERROR: {err}")
            sys.exit(result.exit_code)
        else:
            exit_code = scan_project(
                args.path,
                output,
                tier=tier,
                deep=deep,
                parallel=parallel,
                max_workers=workers,
                include_progress=include_progress,
                include_overview=include_overview,
                include_practices=include_practices,
                practices_level=practices_level,
                practices_categories=practices_categories,
                practices_format=practices_format,
                max_practice_tokens=max_practice_tokens,
                cache_optimize=cache_optimize,
            )
            sys.exit(exit_code)

    elif args.command == "distribute":
        from codetrellis.distributed_generator import DistributedCodeTrellisGenerator
        project_root = Path(args.path).resolve()

        if getattr(args, "clean", False):
            # Remove existing .codetrellis files
            import subprocess
            subprocess.run(
                ["find", str(project_root / "src"), "-name", ".codetrellis", "-delete"],
                capture_output=True
            )
            print("[CodeTrellis] Cleaned existing .codetrellis files")

        generator = DistributedCodeTrellisGenerator()
        stats = generator.generate(str(project_root))

        print(f"\nStats: components={stats['components']}, services={stats['services']}, total={stats['total_files']}")

    elif args.command == "init":
        project_root = Path(args.path).resolve()

        # --update-ai: quick regeneration of AI files using existing matrix (no scan)
        if getattr(args, "update_ai", False):
            from codetrellis.init_integrations import generate_ai_integrations, detect_project

            print("[CodeTrellis] Updating AI integration files from existing matrix...")
            info = detect_project(project_root)
            print(f"[CodeTrellis] Detected: {info.project_type}")
            if info.detected_languages:
                print(f"[CodeTrellis] Languages: {', '.join(info.detected_languages)}")
            if info.detected_frameworks:
                print(f"[CodeTrellis] Frameworks: {', '.join(info.detected_frameworks)}")
            print()

            generated = generate_ai_integrations(project_root, force=True)

            print()
            print(f"[CodeTrellis] ✅ {len(generated)} file(s) updated.")
            if generated:
                print("[CodeTrellis]    Updated files:")
                for gf in generated:
                    print(f"[CodeTrellis]      • {gf.path.relative_to(project_root)}")

        else:
            init_codetrellis(project_root)

            # Generate AI integration files if --ai flag is passed
            if getattr(args, "ai", False):
                from codetrellis.init_integrations import generate_ai_integrations, detect_project

                # Step 1: Run optimal scan FIRST so the matrix is ready
                print()
                print("[CodeTrellis] Running optimal scan...")
                print("=" * 60)
                exit_code = scan_project(
                    str(project_root),
                    tier=OutputTier.LOGIC,
                    parallel=True,
                    include_progress=True,
                    include_overview=True,
                )
                print("=" * 60)

                if exit_code != 0:
                    print()
                    print(f"[CodeTrellis] ⚠️  Scan completed with exit code {exit_code}.")
                    print("[CodeTrellis]    Generating basic AI integration files (no matrix data).")

                # Step 2: Generate AI files AFTER scan — they read the matrix for rich content
                print()
                print("[CodeTrellis] Generating AI integration files (enriched with matrix data)...")
                info = detect_project(project_root)
                print(f"[CodeTrellis] Detected: {info.project_type}")
                if info.detected_languages:
                    print(f"[CodeTrellis] Languages: {', '.join(info.detected_languages)}")
                if info.detected_frameworks:
                    print(f"[CodeTrellis] Frameworks: {', '.join(info.detected_frameworks)}")
                print()

                force = getattr(args, "force", False)
                generated = generate_ai_integrations(project_root, force=force)

                print()
                print(f"[CodeTrellis] {len(generated)} file(s) generated.")

                if exit_code == 0:
                    print()
                    print("[CodeTrellis] ✅ Setup complete! Open VS Code — everything is automatic.")
                    print("[CodeTrellis]    • Copilot reads .github/copilot-instructions.md")
                    print("[CodeTrellis]    • MCP server registered in .vscode/mcp.json")
                    print("[CodeTrellis]    • Watch task auto-starts on folder open")
                    print("[CodeTrellis]    • Claude Code reads CLAUDE.md")
                    print("[CodeTrellis]    • Cursor reads .cursorrules")
                else:
                    print()
                    print(f"[CodeTrellis] ⚠️  Scan completed with exit code {exit_code}.")
                    print("[CodeTrellis]    AI integration files are ready, but review scan output above.")

    elif args.command == "clean":
        version = getattr(args, "version", None)
        exit_code = clean_project(args.path, version=version)
        sys.exit(exit_code)

    elif args.command == "show":
        section = None
        if getattr(args, "schemas", False):
            section = "SCHEMAS"
        elif getattr(args, "dtos", False):
            section = "DTOS"
        elif getattr(args, "services", False):
            section = "SERVICES"
        elif getattr(args, "section", None):
            section = args.section
        show_matrix(args.path, section)

    elif args.command == "prompt":
        tier = _parse_tier(getattr(args, "tier", "prompt"))
        if getattr(args, "tokens", False):
            project_root = Path(args.path).resolve()
            cache_dir = get_cache_dir(project_root)
            prompt_file = cache_dir / "matrix.prompt"
            if prompt_file.exists():
                content = prompt_file.read_text()
                tokens = len(content) // 4
                print(f"Estimated tokens: ~{tokens}")
        else:
            print_prompt(args.path, not getattr(args, "no_header", False), tier=tier)

    elif args.command == "watch":
        watch_project(args.path)

    elif args.command == "sync":
        sync_project(args.path, getattr(args, "file", None))

    elif args.command == "export":
        sections = getattr(args, "sections", [])
        output_file = getattr(args, "output", None)
        export_section(args.path, sections, output_file)

    elif args.command == "validate":
        verbose = getattr(args, "verbose", False)
        validate_project(args.path, verbose)

    elif args.command == "coverage":
        detailed = getattr(args, "detailed", False)
        coverage_report(args.path, detailed)

    elif args.command == "progress":
        detailed = getattr(args, "detailed", False)
        by_module = getattr(args, "by_module", False)
        as_json = getattr(args, "json", False)
        show_progress(args.path, detailed=detailed, by_module=by_module, as_json=as_json)

    elif args.command == "overview":
        as_json = getattr(args, "json", False)
        as_markdown = getattr(args, "markdown", False)
        show_overview(args.path, as_json=as_json, as_markdown=as_markdown)

    elif args.command == "onboard":
        onboard_project(args.path)

    elif args.command == "verify":
        # Use BuildContractVerifier for comprehensive C1-C6 verification
        verifier = BuildContractVerifier(args.path)
        gate_result = verifier.verify()
        if getattr(args, "json", False):
            print(json.dumps(gate_result, indent=2, sort_keys=True))
        else:
            status = "✅ PASS" if gate_result["passed"] else "❌ FAIL"
            print(f"[CodeTrellis] Build Contract Gate: {status}")
            if gate_result.get("warnings"):
                for warn in gate_result["warnings"]:
                    print(f"  WARNING: {warn}")
            if gate_result["errors"]:
                for err in gate_result["errors"]:
                    print(f"  ERROR: {err}")
            print(f"  Checks: {', '.join(gate_result.get('checks_run', []))}")
        sys.exit(gate_result.get("exit_code", 0 if gate_result["passed"] else 1))

    elif args.command == "plugins":
        action = getattr(args, "action", "list")
        plugin_name = getattr(args, "plugin_name", None)
        plugins_command(action, plugin_name)

    elif args.command == "validate-repos":
        validate_repos_command(args)

    elif args.command == "cache-optimize":
        cache_optimize_command(args)

    elif args.command == "mcp":
        mcp_command(args)

    elif args.command == "context":
        context_command(args)

    elif args.command == "skills":
        skills_command(args)

    elif args.command == "export-context":
        export_context_command(args)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
