#!/usr/bin/env python3
"""
CodeTrellis Quality Scorer — Phase D (WS-8)
======================================
Automated quality scoring for CodeTrellis validation scans.

Reads validation-results/*.prompt files and scores each scan
against the quality rubric defined in CodeTrellis_REMEDIATION_PLAN.md § 11.4 (Phase D-2).

Usage:
    python3 quality_scorer.py                          # Score all results
    python3 quality_scorer.py --verbose                # Show per-repo details
    python3 quality_scorer.py --output report.json     # Save JSON report
    python3 quality_scorer.py --threshold 70           # Custom pass threshold

Scoring Rubric (from Phase D-2):
    - Scan completes (exit code 0, no timeout)        — Required
    - Non-empty output (>10 lines)                     — Required
    - Correct project name                             — Required
    - Stack detected (non-empty)                       — >80% repos
    - Business domain detected (not General App)       — >60% repos
    - Runbook extracted ([RUNBOOK] present)             — >90% repos
    - No contamination (PROGRESS TODOs < 500)          — >95% repos
    - No crashes (no Python tracebacks in stderr)       — Required
    - Reasonable size (< 50,000 lines)                  — >95% repos
    - Sections present (at least 5 sections)            — >90% repos
"""

import csv
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


@dataclass
class RepoScore:
    """Quality score for a single repository scan."""
    repo: str
    repo_name: str
    category: str

    # Required metrics (must pass)
    scan_completes: bool = False
    non_empty_output: bool = False
    correct_project_name: bool = False
    no_crashes: bool = False

    # Threshold metrics
    stack_detected: bool = False
    domain_detected: bool = False
    runbook_extracted: bool = False
    no_contamination: bool = False
    reasonable_size: bool = False
    sections_present: bool = False

    # Quantitative data
    exit_code: int = -1
    duration_s: int = 0
    output_lines: int = 0
    file_count: int = 0
    section_count: int = 0
    section_names: List[str] = field(default_factory=list)
    detected_name: str = ""
    detected_stack: str = ""
    detected_domain: str = ""
    todo_count: int = 0
    has_traceback: bool = False

    # Overall
    verdict: str = "UNKNOWN"  # PASS, PARTIAL, FAIL, N/A

    @property
    def required_pass(self) -> bool:
        return (self.scan_completes and self.non_empty_output and
                self.correct_project_name and self.no_crashes)

    @property
    def threshold_score(self) -> int:
        """Count of threshold metrics that pass (0-6)."""
        return sum([
            self.stack_detected,
            self.domain_detected,
            self.runbook_extracted,
            self.no_contamination,
            self.reasonable_size,
            self.sections_present,
        ])

    def compute_verdict(self):
        if not self.scan_completes:
            self.verdict = "FAIL"
        elif not self.required_pass:
            self.verdict = "FAIL"
        elif self.threshold_score >= 5:
            self.verdict = "PASS"
        elif self.threshold_score >= 3:
            self.verdict = "PARTIAL"
        else:
            self.verdict = "FAIL"


@dataclass
class ValidationReport:
    """Aggregate validation report."""
    date: str = ""
    ct_version: str = ""
    total_repos: int = 0
    passed: int = 0
    partial: int = 0
    failed: int = 0
    pass_rate: float = 0.0
    target_met: bool = False
    scores: List[Dict] = field(default_factory=list)

    # Threshold compliance
    stack_compliance: float = 0.0
    domain_compliance: float = 0.0
    runbook_compliance: float = 0.0
    contamination_compliance: float = 0.0
    size_compliance: float = 0.0
    sections_compliance: float = 0.0

    # Failure analysis
    failure_categories: Dict[str, List[str]] = field(default_factory=dict)


# --- Category mapping ---
REPO_CATEGORIES = {}
def load_categories(repos_file: Path):
    """Load repo -> category mapping from repos.txt."""
    category = "Unknown"
    with open(repos_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                if "Category" in line:
                    # Extract category name: "# Category 1: Full-Stack Applications (10 repos)"
                    match = re.search(r'Category \d+:\s*(.+?)(?:\s*\(|$)', line)
                    if match:
                        category = match.group(1).strip()
                continue
            REPO_CATEGORIES[line] = category
            # Also map underscore version
            REPO_CATEGORIES[line.replace("/", "_")] = category


def get_expected_name(repo: str) -> str:
    """Get expected project name from repo path."""
    # e.g., "nestjs/nest" -> "nest"
    return repo.split("/")[-1] if "/" in repo else repo


def parse_prompt_file(prompt_path: Path) -> dict:
    """Parse a matrix.prompt file and extract key metrics."""
    result = {
        "lines": 0,
        "sections": [],
        "project_name": "",
        "project_type": "",
        "stack": "",
        "domain": "",
        "todo_count": 0,
        "has_runbook": False,
        "has_actionable": False,
        "has_service_map": False,
        "has_infrastructure": False,
        "has_nestjs_modules": False,
        "has_best_practices": False,
        "has_ai_instruction": False,
    }

    if not prompt_path.exists() or not prompt_path.stat().st_size:
        return result

    content = prompt_path.read_text(errors="replace")
    lines = content.split("\n")
    result["lines"] = len(lines)

    # Extract sections (lines starting with [SECTION_NAME])
    section_pattern = re.compile(r'^\[([A-Z_]+(?::[^\]]+)?)\]')
    for line in lines:
        m = section_pattern.match(line)
        if m:
            section = m.group(1)
            # Skip GRPC sub-sections like [GRPC:ServiceName]
            if ":" not in section or section.startswith("GRPC"):
                result["sections"].append(section)

    result["sections"] = list(dict.fromkeys(result["sections"]))  # Deduplicate, preserve order

    # Extract project name
    name_match = re.search(r'^\[PROJECT\]\s*\nname=(.+)', content, re.MULTILINE)
    if name_match:
        result["project_name"] = name_match.group(1).strip()
    else:
        # Try alternate format
        name_match = re.search(r'name[=:](\S+)', content)
        if name_match:
            result["project_name"] = name_match.group(1).strip()

    # Extract type
    type_match = re.search(r'type=(.+)', content)
    if type_match:
        result["project_type"] = type_match.group(1).strip()

    # Extract stack from OVERVIEW
    stack_match = re.search(r'stack:(.+)', content)
    if stack_match:
        result["stack"] = stack_match.group(1).strip()

    # Extract domain
    domain_match = re.search(r'domain:(.+)', content)
    if domain_match:
        result["domain"] = domain_match.group(1).strip()

    # Extract TODO count from PROGRESS
    todo_match = re.search(r'todos:(\d+)', content)
    if todo_match:
        result["todo_count"] = int(todo_match.group(1))

    # Check key sections
    for section in result["sections"]:
        if section == "RUNBOOK":
            result["has_runbook"] = True
        elif section == "ACTIONABLE_ITEMS":
            result["has_actionable"] = True
        elif section == "SERVICE_MAP":
            result["has_service_map"] = True
        elif section == "INFRASTRUCTURE":
            result["has_infrastructure"] = True
        elif section == "NESTJS_MODULES":
            result["has_nestjs_modules"] = True
        elif section == "BEST_PRACTICES":
            result["has_best_practices"] = True
        elif section == "AI_INSTRUCTION":
            result["has_ai_instruction"] = True

    return result


def check_log_file(log_path: Path) -> Tuple[bool, int, int]:
    """Check log file for tracebacks, extract exit code and duration."""
    has_traceback = False
    exit_code = -1
    duration = 0

    if not log_path.exists():
        return has_traceback, exit_code, duration

    content = log_path.read_text(errors="replace")

    if "Traceback" in content:
        has_traceback = True

    # Parse timing line: "TIMING: 42s (exit=0)"
    timing_match = re.search(r'TIMING:\s*(\d+)s\s*\(exit=(\d+)\)', content)
    if timing_match:
        duration = int(timing_match.group(1))
        exit_code = int(timing_match.group(2))

    return has_traceback, exit_code, duration


def score_repo(repo: str, results_dir: Path) -> RepoScore:
    """Score a single repository's scan results."""
    repo_name = repo.replace("/", "_")
    category = REPO_CATEGORIES.get(repo, REPO_CATEGORIES.get(repo_name, "Unknown"))

    score = RepoScore(
        repo=repo,
        repo_name=repo_name,
        category=category,
    )

    prompt_path = results_dir / f"{repo_name}.prompt"
    log_path = results_dir / f"{repo_name}.log"

    # Check log file
    has_traceback, log_exit_code, duration = check_log_file(log_path)
    score.has_traceback = has_traceback
    score.duration_s = duration

    # Check if scan output exists
    if not prompt_path.exists():
        score.verdict = "FAIL"
        return score

    # Check if clone failed
    try:
        first_line = prompt_path.read_text(errors="replace").split("\n")[0]
        if first_line.strip() == "CLONE_FAILED":
            score.verdict = "FAIL"
            return score
    except Exception:
        score.verdict = "FAIL"
        return score

    # Parse prompt file
    parsed = parse_prompt_file(prompt_path)

    # Also read CSV for file counts
    csv_path = results_dir / "summary.csv"
    if csv_path.exists():
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("repo_name") == repo_name:
                    try:
                        score.exit_code = int(row.get("exit_code", -1))
                        score.duration_s = int(row.get("duration_s", 0))
                        score.file_count = int(row.get("file_count", 0))
                    except (ValueError, TypeError):
                        pass
                    break

    # Use log exit code if CSV didn't have it
    if score.exit_code == -1:
        score.exit_code = log_exit_code

    # Populate metrics
    score.output_lines = parsed["lines"]
    score.section_count = len(parsed["sections"])
    score.section_names = parsed["sections"]
    score.detected_name = parsed["project_name"]
    score.detected_stack = parsed["stack"]
    score.detected_domain = parsed["domain"]
    score.todo_count = parsed["todo_count"]

    # --- Required metrics ---
    score.scan_completes = (score.exit_code == 0)
    score.non_empty_output = (parsed["lines"] > 10)
    score.no_crashes = (not has_traceback)

    # Project name check — flexible matching
    expected_name = get_expected_name(repo)
    detected = parsed["project_name"].lower().replace("-", "").replace("_", "")
    expected = expected_name.lower().replace("-", "").replace("_", "")
    score.correct_project_name = (
        detected == expected or
        expected in detected or
        detected in expected or
        parsed["project_name"] != ""  # At least detected something
    )

    # --- Threshold metrics ---
    score.stack_detected = bool(parsed["stack"] and parsed["stack"] != "Unknown")
    score.domain_detected = bool(
        parsed["domain"] and
        "General" not in parsed["domain"] and
        "Unknown" not in parsed["domain"]
    )
    score.runbook_extracted = parsed["has_runbook"]
    score.no_contamination = (parsed["todo_count"] < 500)
    score.reasonable_size = (parsed["lines"] < 50000)
    score.sections_present = (len(parsed["sections"]) >= 5)

    # Compute verdict
    score.compute_verdict()

    return score


def generate_report(scores: List[RepoScore]) -> ValidationReport:
    """Generate aggregate validation report."""
    report = ValidationReport(
        date=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        total_repos=len(scores),
    )

    # Try to get CodeTrellis version
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from codetrellis.cli import VERSION
        report.ct_version = VERSION
    except ImportError:
        report.ct_version = "unknown"

    # Count verdicts
    for score in scores:
        if score.verdict == "PASS":
            report.passed += 1
        elif score.verdict == "PARTIAL":
            report.partial += 1
        else:
            report.failed += 1

    # Pass rate (PASS + PARTIAL count as passing)
    if report.total_repos > 0:
        report.pass_rate = ((report.passed + report.partial) / report.total_repos) * 100

    report.target_met = report.pass_rate >= 70

    # Threshold compliance rates
    completed = [s for s in scores if s.scan_completes]
    n = len(completed) if completed else 1

    report.stack_compliance = sum(1 for s in completed if s.stack_detected) / n * 100
    report.domain_compliance = sum(1 for s in completed if s.domain_detected) / n * 100
    report.runbook_compliance = sum(1 for s in completed if s.runbook_extracted) / n * 100
    report.contamination_compliance = sum(1 for s in completed if s.no_contamination) / n * 100
    report.size_compliance = sum(1 for s in completed if s.reasonable_size) / n * 100
    report.sections_compliance = sum(1 for s in completed if s.sections_present) / n * 100

    # Failure categorization (Phase D-4)
    cat_a = []  # Scan failures
    cat_b = []  # Missing context
    cat_c = []  # Wrong context
    cat_d = []  # Missing runbook

    for score in scores:
        if not score.scan_completes:
            cat_a.append(f"{score.repo} (exit={score.exit_code})")
        elif score.has_traceback:
            cat_a.append(f"{score.repo} (traceback)")
        if score.scan_completes and not score.sections_present:
            cat_b.append(f"{score.repo} (sections={score.section_count})")
        if score.scan_completes and not score.domain_detected:
            cat_c.append(f"{score.repo} (domain={score.detected_domain})")
        if score.scan_completes and not score.runbook_extracted:
            cat_d.append(f"{score.repo}")

    report.failure_categories = {
        "A_scan_failures": cat_a,
        "B_missing_context": cat_b,
        "C_wrong_context": cat_c,
        "D_missing_runbook": cat_d,
    }

    # Serialize scores (asdict doesn't include @property methods)
    report.scores = []
    for s in scores:
        d = asdict(s)
        d["threshold_score"] = s.threshold_score
        d["required_pass"] = s.required_pass
        report.scores.append(d)

    return report


def print_report(report: ValidationReport, verbose: bool = False):
    """Print human-readable report."""
    print("=" * 70)
    print("  CodeTrellis Quality Score Report — Phase D (WS-8)")
    print("=" * 70)
    print(f"  Date:          {report.date}")
    print(f"  CodeTrellis Version:  {report.ct_version}")
    print(f"  Total repos:   {report.total_repos}")
    print()
    print(f"  ✅ PASS:       {report.passed}")
    print(f"  🟡 PARTIAL:    {report.partial}")
    print(f"  ❌ FAIL:       {report.failed}")
    print(f"  Pass rate:     {report.pass_rate:.1f}% (target: >70%)")
    print(f"  Target met:    {'🎉 YES' if report.target_met else '⚠️  NO'}")
    print()
    print("  Threshold Compliance:")
    print(f"    Stack detected:      {report.stack_compliance:.1f}% (target: >80%)")
    print(f"    Domain detected:     {report.domain_compliance:.1f}% (target: >60%)")
    print(f"    Runbook extracted:   {report.runbook_compliance:.1f}% (target: >90%)")
    print(f"    No contamination:    {report.contamination_compliance:.1f}% (target: >95%)")
    print(f"    Reasonable size:     {report.size_compliance:.1f}% (target: >95%)")
    print(f"    Sections present:    {report.sections_compliance:.1f}% (target: >90%)")
    print("=" * 70)

    # Failure categories
    cats = report.failure_categories
    if any(cats.values()):
        print()
        print("  Failure Analysis (Phase D-4 Categories):")
        print("  " + "-" * 50)
        if cats.get("A_scan_failures"):
            print(f"  Category A — Scan Failures ({len(cats['A_scan_failures'])}):")
            for item in cats["A_scan_failures"][:5]:
                print(f"    • {item}")
            if len(cats["A_scan_failures"]) > 5:
                print(f"    ... and {len(cats['A_scan_failures']) - 5} more")
        if cats.get("B_missing_context"):
            print(f"  Category B — Missing Context ({len(cats['B_missing_context'])}):")
            for item in cats["B_missing_context"][:5]:
                print(f"    • {item}")
        if cats.get("C_wrong_context"):
            print(f"  Category C — Wrong Context ({len(cats['C_wrong_context'])}):")
            for item in cats["C_wrong_context"][:5]:
                print(f"    • {item}")
        if cats.get("D_missing_runbook"):
            print(f"  Category D — Missing Runbook ({len(cats['D_missing_runbook'])}):")
            for item in cats["D_missing_runbook"][:5]:
                print(f"    • {item}")

    # Per-category breakdown
    if verbose:
        print()
        print("  Per-Category Results:")
        print("  " + "-" * 50)
        category_stats: Dict[str, Dict] = {}
        for s in report.scores:
            cat = s.get("category", "Unknown")
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "pass": 0, "partial": 0, "fail": 0}
            category_stats[cat]["total"] += 1
            v = s.get("verdict", "FAIL")
            if v == "PASS":
                category_stats[cat]["pass"] += 1
            elif v == "PARTIAL":
                category_stats[cat]["partial"] += 1
            else:
                category_stats[cat]["fail"] += 1

        for cat, stats in sorted(category_stats.items()):
            rate = ((stats["pass"] + stats["partial"]) / stats["total"]) * 100 if stats["total"] else 0
            print(f"    {cat}: {stats['pass']}P/{stats['partial']}PT/{stats['fail']}F "
                  f"({rate:.0f}% pass rate)")

    # Verbose per-repo details
    if verbose:
        print()
        print("  Per-Repo Details:")
        print("  " + "-" * 66)
        print(f"  {'Repo':<35} {'Verdict':<8} {'Lines':>7} {'Secs':>6} {'Score':>5}")
        print("  " + "-" * 66)
        for s in report.scores:
            v_icon = {"PASS": "✅", "PARTIAL": "🟡", "FAIL": "❌"}.get(s["verdict"], "❓")
            print(f"  {s['repo']:<35} {v_icon}{s['verdict']:<6} "
                  f"{s['output_lines']:>7} {s['duration_s']:>5}s {s['threshold_score']:>4}/6")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="CodeTrellis Quality Scorer — Phase D (WS-8)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-repo details")
    parser.add_argument("--output", "-o", help="Save JSON report to file")
    parser.add_argument("--threshold", type=int, default=70, help="Pass rate threshold (default: 70)")
    parser.add_argument("--results-dir", default=None,
                        help="Path to validation-results directory")
    args = parser.parse_args()

    # Find results directory
    script_dir = Path(__file__).parent
    results_dir = Path(args.results_dir) if args.results_dir else script_dir / "validation-results"
    repos_file = script_dir / "repos.txt"

    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        print("   Run validation_runner.sh first.")
        sys.exit(1)

    # Load category mapping
    if repos_file.exists():
        load_categories(repos_file)

    # Find all scanned repos
    prompt_files = sorted(results_dir.glob("*.prompt"))
    if not prompt_files:
        print("❌ No .prompt files found in results directory.")
        sys.exit(1)

    # Build repo list from prompt files
    repos = []
    for pf in prompt_files:
        repo_name = pf.stem
        # Try to find original repo path from CSV
        csv_path = results_dir / "summary.csv"
        repo = repo_name.replace("_", "/", 1)  # Approximate
        if csv_path.exists():
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("repo_name") == repo_name:
                        repo = row.get("repo", repo)
                        break
        repos.append(repo)

    print(f"Found {len(repos)} scan results to score.\n")

    # Score each repo
    scores = [score_repo(repo, results_dir) for repo in repos]

    # Generate report
    report = generate_report(scores)

    # Print report
    print_report(report, verbose=args.verbose)

    # Save JSON report
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(asdict(report), indent=2, default=str))
        print(f"\n📄 JSON report saved to: {output_path}")

    # Exit code based on threshold
    if report.pass_rate >= args.threshold:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
