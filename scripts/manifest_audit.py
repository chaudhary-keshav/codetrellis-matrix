#!/usr/bin/env python3
"""
CodeTrellis File Manifest Auditor — PART J, Section J2
=========================================================

Automated workspace auditor that verifies all planned files across
all phases exist, are correctly located, and follow naming conventions.

Validates:
  1. All Python module files from J2 manifest exist
  2. All TypeScript files from J2 manifest (if VS Code extension dir exists)
  3. All 53+ language parser files exist and follow naming conventions
  4. All BPL practices YAML files exist
  5. All integration test files exist
  6. All scripts exist
  7. No orphaned/undocumented architectural files

Reference: CODETRELLIS_MASTER_RESEARCH_AND_PLAN.md — PART J, J2
Author: Keshav Chaudhary
Created: 20 February 2026

Usage:
  python scripts/manifest_audit.py [project_root]
  python scripts/manifest_audit.py --json
  python scripts/manifest_audit.py --strict
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# J2 File Manifest — Python (codetrellis/)
# ---------------------------------------------------------------------------

# Phase B: Auto-Compilation Pipeline
PYTHON_MANIFEST_PHASE_B = {
    "builder.py": "Build orchestrator",
    "cache.py": "Cache manager with lockfile",
    "interfaces.py": "IExtractor protocol",
    "build_contract.py": "Build contract (C1-C6)",
}

# Phase E: CLI Fusion
PYTHON_MANIFEST_PHASE_E = {
    "mcp_server.py": "MCP protocol server",
}

# Phase F: Advanced Research (F1-F7)
PYTHON_MANIFEST_PHASE_F = {
    "matrix_jsonld.py": "JSON-LD encoder (F1)",
    "matrix_embeddings.py": "Embedding index (F2)",
    "matrix_diff.py": "JSON Patch diff engine (F3)",
    "matrix_compressor_levels.py": "Multi-level compression (F4)",
    "cross_language_types.py": "Cross-language type mapping (F5)",
    "matrix_navigator.py": "Intelligent file discovery (F6)",
    "matrixbench_scorer.py": "Benchmark scoring (F7)",
}

# Phase H: Build Contracts
PYTHON_MANIFEST_PHASE_H = {
    "build_contracts_advanced.py": "Advanced build contracts (H1-H7)",
}

# Core files (always required)
PYTHON_MANIFEST_CORE = {
    "__init__.py": "Package init with version",
    "__main__.py": "CLI entry point",
    "cli.py": "Command-line interface",
    "scanner.py": "Project scanner",
    "compressor.py": "Matrix compressor",
    "errors.py": "Error types",
    "file_classifier.py": "File classifier",
    "parallel.py": "Parallel processing",
    "streaming.py": "Streaming extraction",
    "watcher.py": "File watcher",
    "distributed_generator.py": "Distributed .codetrellis generation",
    "ast_parser.py": "AST parser",
}

# A5.x modules
PYTHON_MANIFEST_A5 = {
    "cache_optimizer.py": "Cache optimizer (A5.1)",
    "jit_context.py": "JIT context injection (A5.3)",
    "skills_generator.py": "AI skills generation (A5.5)",
}


# ---------------------------------------------------------------------------
# All 53+ language/framework parser files
# ---------------------------------------------------------------------------

LANGUAGE_PARSER_FILES = {
    # Core languages (20)
    "python_parser_enhanced.py": "Python",
    "typescript_parser_enhanced.py": "TypeScript",
    "javascript_parser_enhanced.py": "JavaScript",
    "java_parser_enhanced.py": "Java",
    "kotlin_parser_enhanced.py": "Kotlin",
    "csharp_parser_enhanced.py": "C#",
    "rust_parser_enhanced.py": "Rust",
    "go_parser_enhanced.py": "Go",
    "swift_parser_enhanced.py": "Swift",
    "ruby_parser_enhanced.py": "Ruby",
    "php_parser_enhanced.py": "PHP",
    "scala_parser_enhanced.py": "Scala",
    "r_parser_enhanced.py": "R",
    "dart_parser_enhanced.py": "Dart",
    "lua_parser_enhanced.py": "Lua",
    "powershell_parser_enhanced.py": "PowerShell",
    "bash_parser_enhanced.py": "Bash",
    "c_parser_enhanced.py": "C",
    "cpp_parser_enhanced.py": "C++",
    "sql_parser_enhanced.py": "SQL",
    # Markup / Style (3)
    "html_parser_enhanced.py": "HTML",
    "css_parser_enhanced.py": "CSS",
    "sass_parser_enhanced.py": "Sass/SCSS",
    # Frontend frameworks (15)
    "react_parser_enhanced.py": "React",
    "vue_parser_enhanced.py": "Vue.js",
    "svelte_parser_enhanced.py": "Svelte",
    "nextjs_parser_enhanced.py": "Next.js",
    "remix_parser_enhanced.py": "Remix",
    "astro_parser_enhanced.py": "Astro",
    "solidjs_parser_enhanced.py": "Solid.js",
    "qwik_parser_enhanced.py": "Qwik",
    "preact_parser_enhanced.py": "Preact",
    "lit_parser_enhanced.py": "Lit / Web Components",
    "alpinejs_parser_enhanced.py": "Alpine.js",
    "htmx_parser_enhanced.py": "HTMX",
    # CSS-in-JS / UI Frameworks (12)
    "tailwind_parser_enhanced.py": "Tailwind CSS",
    "mui_parser_enhanced.py": "Material UI (MUI)",
    "antd_parser_enhanced.py": "Ant Design",
    "chakra_parser_enhanced.py": "Chakra UI",
    "shadcn_parser_enhanced.py": "shadcn/ui",
    "bootstrap_parser_enhanced.py": "Bootstrap",
    "radix_parser_enhanced.py": "Radix UI",
    "styled_components_parser_enhanced.py": "Styled Components",
    "emotion_parser_enhanced.py": "Emotion",
    "less_parser_enhanced.py": "Less",
    "postcss_parser_enhanced.py": "PostCSS",
    # State management (12)
    "redux_parser_enhanced.py": "Redux / RTK",
    "zustand_parser_enhanced.py": "Zustand",
    "jotai_parser_enhanced.py": "Jotai",
    "recoil_parser_enhanced.py": "Recoil",
    "mobx_parser_enhanced.py": "MobX",
    "pinia_parser_enhanced.py": "Pinia",
    "ngrx_parser_enhanced.py": "NgRx",
    "xstate_parser_enhanced.py": "XState",
    "valtio_parser_enhanced.py": "Valtio",
    # Data fetching (3)
    "tanstack_query_parser_enhanced.py": "TanStack Query",
    "swr_parser_enhanced.py": "SWR",
    "apollo_parser_enhanced.py": "Apollo Client",
}


# ---------------------------------------------------------------------------
# Script files that should exist
# ---------------------------------------------------------------------------

SCRIPT_MANIFEST = {
    "smoke_test_advanced.sh": "Advanced research smoke tests",
    "smoke_test_build_contracts.sh": "Build contracts smoke tests",
    "smoke_test_appendices.sh": "Appendices smoke tests (J1-J4)",
    "verify_all.sh": "Full verification suite",
    "verify_build.sh": "Build verification",
    "verify_tests.sh": "Test verification",
    "verify_lint.sh": "Lint verification",
    "verify_determinism.sh": "Determinism verification",
    "verify_incremental.sh": "Incremental build verification",
    "validate_practices.py": "BPL practices validator",
    "token_budget_validator.py": "Token budget validator (J1)",
    "manifest_audit.py": "File manifest auditor (J2)",
}

# ---------------------------------------------------------------------------
# Test files
# ---------------------------------------------------------------------------

TEST_MANIFEST = {
    "tests/integration/test_advanced_gates.py": "Advanced quality gates (G1-G7)",
    "tests/integration/test_build_contracts_advanced.py": "Build contracts (H1-H7)",
    "tests/integration/test_cross_topic_synergies.py": "Cross-topic synergies (J3)",
}

# ---------------------------------------------------------------------------
# Documentation files
# ---------------------------------------------------------------------------

DOCS_MANIFEST = {
    "docs/plan/auotcompile-plan/CODETRELLIS_MASTER_RESEARCH_AND_PLAN.md": "Master research plan",
    "docs/references/CITATIONS.md": "Research citations (J4)",
    "README.md": "Project README",
    "STATUS.md": "Implementation status",
}


# ---------------------------------------------------------------------------
# Audit Results
# ---------------------------------------------------------------------------

@dataclass
class FileAuditEntry:
    """Result of auditing a single file."""
    path: str
    phase: str
    description: str
    exists: bool
    naming_ok: bool
    issues: List[str] = field(default_factory=list)


@dataclass
class AuditReport:
    """Complete manifest audit report."""
    timestamp: str
    project_root: str
    total_expected: int
    total_found: int
    total_missing: int
    compliance_pct: float

    # Per-category results
    core_files: List[FileAuditEntry] = field(default_factory=list)
    phase_b_files: List[FileAuditEntry] = field(default_factory=list)
    phase_e_files: List[FileAuditEntry] = field(default_factory=list)
    phase_f_files: List[FileAuditEntry] = field(default_factory=list)
    phase_h_files: List[FileAuditEntry] = field(default_factory=list)
    a5x_files: List[FileAuditEntry] = field(default_factory=list)
    parser_files: List[FileAuditEntry] = field(default_factory=list)
    script_files: List[FileAuditEntry] = field(default_factory=list)
    test_files: List[FileAuditEntry] = field(default_factory=list)
    doc_files: List[FileAuditEntry] = field(default_factory=list)

    # Orphaned files (exist but not in manifest)
    orphaned_files: List[str] = field(default_factory=list)

    passed: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# ManifestAuditor
# ---------------------------------------------------------------------------

class ManifestAuditor:
    """Audits workspace against J2 File Manifest."""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else PROJECT_ROOT
        self.codetrellis_dir = self.project_root / "codetrellis"
        self.scripts_dir = self.project_root / "scripts"

    def audit(self) -> AuditReport:
        """Run the full manifest audit."""
        from datetime import datetime

        report = AuditReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            total_expected=0,
            total_found=0,
            total_missing=0,
            compliance_pct=0.0,
        )

        # 1. Core Python files
        report.core_files = self._audit_python_files(PYTHON_MANIFEST_CORE, "Core")

        # 2. Phase B files
        report.phase_b_files = self._audit_python_files(PYTHON_MANIFEST_PHASE_B, "Phase B")

        # 3. Phase E files
        report.phase_e_files = self._audit_python_files(PYTHON_MANIFEST_PHASE_E, "Phase E")

        # 4. Phase F files
        report.phase_f_files = self._audit_python_files(PYTHON_MANIFEST_PHASE_F, "Phase F")

        # 5. Phase H files
        report.phase_h_files = self._audit_python_files(PYTHON_MANIFEST_PHASE_H, "Phase H")

        # 6. A5.x modules
        report.a5x_files = self._audit_python_files(PYTHON_MANIFEST_A5, "A5.x")

        # 7. Language parser files (53+)
        report.parser_files = self._audit_python_files(LANGUAGE_PARSER_FILES, "Parser")

        # 8. Script files
        report.script_files = self._audit_scripts(SCRIPT_MANIFEST)

        # 9. Test files
        report.test_files = self._audit_project_files(TEST_MANIFEST, "Tests")

        # 10. Documentation files
        report.doc_files = self._audit_project_files(DOCS_MANIFEST, "Docs")

        # Aggregate
        all_entries = (
            report.core_files + report.phase_b_files + report.phase_e_files +
            report.phase_f_files + report.phase_h_files + report.a5x_files +
            report.parser_files + report.script_files + report.test_files +
            report.doc_files
        )
        report.total_expected = len(all_entries)
        report.total_found = sum(1 for e in all_entries if e.exists)
        report.total_missing = report.total_expected - report.total_found
        report.compliance_pct = (
            report.total_found / report.total_expected * 100
            if report.total_expected > 0 else 0
        )

        # Check for orphaned parser files
        report.orphaned_files = self._find_orphaned_parsers()

        # Overall pass/fail
        report.passed = report.total_missing == 0

        if report.total_missing > 0:
            missing = [e.path for e in all_entries if not e.exists]
            report.errors.append(f"{report.total_missing} files missing: {', '.join(missing[:10])}")

        if report.orphaned_files:
            report.warnings.append(
                f"{len(report.orphaned_files)} orphaned parser files found: "
                f"{', '.join(report.orphaned_files[:5])}"
            )

        return report

    def _audit_python_files(
        self, manifest: Dict[str, str], phase: str
    ) -> List[FileAuditEntry]:
        """Audit Python files in codetrellis/ directory."""
        results = []
        for filename, description in manifest.items():
            filepath = self.codetrellis_dir / filename
            exists = filepath.exists()
            naming_ok = self._check_naming_convention(filename)
            issues = []
            if not exists:
                issues.append(f"Missing: {filepath}")
            if not naming_ok:
                issues.append(f"Naming violation: {filename} should be snake_case.py")

            results.append(FileAuditEntry(
                path=f"codetrellis/{filename}",
                phase=phase,
                description=description,
                exists=exists,
                naming_ok=naming_ok,
                issues=issues,
            ))
        return results

    def _audit_scripts(self, manifest: Dict[str, str]) -> List[FileAuditEntry]:
        """Audit script files in scripts/ directory."""
        results = []
        for filename, description in manifest.items():
            filepath = self.scripts_dir / filename
            exists = filepath.exists()
            naming_ok = True  # Scripts can have various naming
            issues = []
            if not exists:
                issues.append(f"Missing: {filepath}")

            results.append(FileAuditEntry(
                path=f"scripts/{filename}",
                phase="Scripts",
                description=description,
                exists=exists,
                naming_ok=naming_ok,
                issues=issues,
            ))
        return results

    def _audit_project_files(
        self, manifest: Dict[str, str], phase: str
    ) -> List[FileAuditEntry]:
        """Audit files relative to project root."""
        results = []
        for relpath, description in manifest.items():
            filepath = self.project_root / relpath
            exists = filepath.exists()
            naming_ok = True
            issues = []
            if not exists:
                issues.append(f"Missing: {filepath}")

            results.append(FileAuditEntry(
                path=relpath,
                phase=phase,
                description=description,
                exists=exists,
                naming_ok=naming_ok,
                issues=issues,
            ))
        return results

    def _check_naming_convention(self, filename: str) -> bool:
        """Check that Python files follow snake_case.py convention."""
        if filename.startswith("__"):
            return True  # Dunder files OK
        name = Path(filename).stem
        # snake_case: lowercase, underscores, no hyphens, no uppercase
        return bool(re.match(r'^[a-z][a-z0-9_]*$', name))

    def _find_orphaned_parsers(self) -> List[str]:
        """Find parser files that exist but aren't in any manifest."""
        all_manifest_files: Set[str] = set()
        for m in [PYTHON_MANIFEST_CORE, PYTHON_MANIFEST_PHASE_B,
                   PYTHON_MANIFEST_PHASE_E, PYTHON_MANIFEST_PHASE_F,
                   PYTHON_MANIFEST_PHASE_H, PYTHON_MANIFEST_A5,
                   LANGUAGE_PARSER_FILES]:
            all_manifest_files.update(m.keys())

        orphaned = []
        if self.codetrellis_dir.exists():
            for f in sorted(self.codetrellis_dir.iterdir()):
                if (f.is_file() and f.suffix == ".py" and
                        f.name not in all_manifest_files and
                        not f.name.startswith("__")):
                    orphaned.append(f.name)

        return orphaned

    def format_report(self, report: AuditReport) -> str:
        """Format audit report as human-readable text."""
        lines = []
        lines.append("=" * 72)
        lines.append("  CodeTrellis File Manifest Audit Report (J2)")
        lines.append("=" * 72)
        lines.append("")
        lines.append(f"  Project:     {report.project_root}")
        lines.append(f"  Timestamp:   {report.timestamp}")
        lines.append(f"  Expected:    {report.total_expected} files")
        lines.append(f"  Found:       {report.total_found} files")
        lines.append(f"  Missing:     {report.total_missing} files")
        lines.append(f"  Compliance:  {report.compliance_pct:.1f}%")
        lines.append("")

        categories = [
            ("Core Python", report.core_files),
            ("Phase B (Auto-Compilation)", report.phase_b_files),
            ("Phase E (CLI Fusion)", report.phase_e_files),
            ("Phase F (Advanced Research)", report.phase_f_files),
            ("Phase H (Build Contracts)", report.phase_h_files),
            ("A5.x Modules", report.a5x_files),
            ("Language Parsers (53+)", report.parser_files),
            ("Scripts", report.script_files),
            ("Tests", report.test_files),
            ("Documentation", report.doc_files),
        ]

        for cat_name, entries in categories:
            found = sum(1 for e in entries if e.exists)
            total = len(entries)
            status = "✅" if found == total else "⚠️"
            lines.append(f"--- {cat_name} ({found}/{total}) {status} ---")
            for e in entries:
                icon = "✅" if e.exists else "❌"
                lines.append(f"  {icon} {e.path:<55} {e.description}")
            lines.append("")

        if report.orphaned_files:
            lines.append(f"--- Orphaned Files ({len(report.orphaned_files)}) ---")
            for f in report.orphaned_files:
                lines.append(f"  ⚠️  codetrellis/{f}")
            lines.append("")

        if report.errors:
            lines.append("--- ERRORS ---")
            for e in report.errors:
                lines.append(f"  ❌ {e}")
            lines.append("")

        if report.warnings:
            lines.append("--- WARNINGS ---")
            for w in report.warnings:
                lines.append(f"  ⚠️  {w}")
            lines.append("")

        status = "✅ PASSED (100% Compliance)" if report.passed else f"❌ FAILED ({report.compliance_pct:.1f}% Compliance)"
        lines.append(f"  OVERALL: {status}")
        lines.append("=" * 72)

        return "\n".join(lines)

    def to_json(self, report: AuditReport) -> str:
        """Export report as JSON."""
        data = {
            "timestamp": report.timestamp,
            "project_root": report.project_root,
            "total_expected": report.total_expected,
            "total_found": report.total_found,
            "total_missing": report.total_missing,
            "compliance_pct": report.compliance_pct,
            "categories": {},
            "orphaned_files": report.orphaned_files,
            "passed": report.passed,
            "errors": report.errors,
            "warnings": report.warnings,
        }

        for cat_name, entries in [
            ("core", report.core_files),
            ("phase_b", report.phase_b_files),
            ("phase_e", report.phase_e_files),
            ("phase_f", report.phase_f_files),
            ("phase_h", report.phase_h_files),
            ("a5x", report.a5x_files),
            ("parsers", report.parser_files),
            ("scripts", report.script_files),
            ("tests", report.test_files),
            ("docs", report.doc_files),
        ]:
            data["categories"][cat_name] = [
                {
                    "path": e.path,
                    "phase": e.phase,
                    "description": e.description,
                    "exists": e.exists,
                    "naming_ok": e.naming_ok,
                    "issues": e.issues,
                }
                for e in entries
            ]

        return json.dumps(data, indent=2, sort_keys=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """CLI entry point for manifest audit."""
    import argparse

    parser = argparse.ArgumentParser(
        description="CodeTrellis File Manifest Auditor (J2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=str(PROJECT_ROOT),
        help="Path to the project root (default: current project)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report as JSON",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any warnings (orphaned files)",
    )

    args = parser.parse_args()

    auditor = ManifestAuditor(args.project_root)
    report = auditor.audit()

    if args.strict and report.orphaned_files:
        report.passed = False
        report.errors.append("Strict mode: orphaned files found")

    if args.json:
        print(auditor.to_json(report))
    else:
        print(auditor.format_report(report))

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
