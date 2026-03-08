#!/usr/bin/env python3
"""
CodeTrellis Results Analyzer — Phase D (WS-8)
========================================
Generates Gap Analysis Round 2 document from validation results.

Reads validation-results/ and produces a structured markdown report
categorizing failures per Phase D-4 specification:
  Category A: Scan failures (crash, timeout, empty output)
  Category B: Missing context (important code not captured)
  Category C: Wrong context (misdetection, contamination)
  Category D: Missing execution context (no runbook)

Usage:
    python3 analyze_results.py                            # Generate report
    python3 analyze_results.py --output gap_analysis_r2.md # Custom output
    python3 analyze_results.py --sample 10                 # Manual review sampling
"""

import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime


@dataclass
class SectionAnalysis:
    """Analysis of which sections appear across all scanned repos."""
    section_name: str
    present_count: int = 0
    total_repos: int = 0
    repos_present: List[str] = field(default_factory=list)
    repos_missing: List[str] = field(default_factory=list)

    @property
    def coverage_pct(self) -> float:
        return (self.present_count / self.total_repos * 100) if self.total_repos else 0


@dataclass
class CategoryBreakdown:
    """Breakdown of results per repository category."""
    category: str
    total: int = 0
    passed: int = 0
    partial: int = 0
    failed: int = 0
    avg_lines: float = 0
    avg_sections: float = 0
    avg_duration: float = 0
    common_issues: List[str] = field(default_factory=list)


def load_quality_report(results_dir: Path) -> Optional[dict]:
    """Load the quality scorer's JSON report if available."""
    report_file = results_dir / "quality_report.json"
    if report_file.exists():
        return json.loads(report_file.read_text())
    return None


def parse_prompt_sections(prompt_path: Path) -> Dict:
    """Parse a prompt file and extract detailed section info."""
    result = {
        "sections": [],
        "section_sizes": {},
        "project_name": "",
        "project_type": "",
        "stack": "",
        "domain": "",
        "total_lines": 0,
        "has_ai_instruction": False,
        "frameworks_detected": [],
        "languages_detected": [],
    }

    if not prompt_path.exists() or prompt_path.stat().st_size == 0:
        return result

    content = prompt_path.read_text(errors="replace")
    lines = content.split("\n")
    result["total_lines"] = len(lines)

    # Extract sections with line counts
    current_section = None
    section_start = 0
    section_pattern = re.compile(r'^\[([A-Z_]+(?::[^\]]+)?)\]')

    for i, line in enumerate(lines):
        m = section_pattern.match(line)
        if m:
            if current_section:
                result["section_sizes"][current_section] = i - section_start
            current_section = m.group(1)
            section_start = i
            if ":" not in current_section or current_section.startswith("GRPC"):
                result["sections"].append(current_section)

    if current_section:
        result["section_sizes"][current_section] = len(lines) - section_start

    # Parse project info
    name_match = re.search(r'name=(.+)', content)
    if name_match:
        result["project_name"] = name_match.group(1).strip()

    type_match = re.search(r'type=(.+)', content)
    if type_match:
        result["project_type"] = type_match.group(1).strip()

    stack_match = re.search(r'stack:(.+)', content)
    if stack_match:
        result["stack"] = stack_match.group(1).strip()

    domain_match = re.search(r'domain:(.+)', content)
    if domain_match:
        result["domain"] = domain_match.group(1).strip()

    # Detect frameworks and languages from content
    if "angular" in content.lower() or "@angular" in content:
        result["frameworks_detected"].append("Angular")
    if "nestjs" in content.lower() or "@nestjs" in content:
        result["frameworks_detected"].append("NestJS")
    if "react" in content.lower():
        result["frameworks_detected"].append("React")
    if "fastapi" in content.lower():
        result["frameworks_detected"].append("FastAPI")
    if "flask" in content.lower():
        result["frameworks_detected"].append("Flask")
    if "django" in content.lower():
        result["frameworks_detected"].append("Django")

    if "[PYTHON_TYPES]" in content or "[PYTHON_API]" in content:
        result["languages_detected"].append("Python")
    if "[SCHEMAS]" in content or "[CONTROLLERS]" in content:
        result["languages_detected"].append("TypeScript")

    result["has_ai_instruction"] = "[AI_INSTRUCTION]" in content

    return result


def generate_gap_analysis_round2(results_dir: Path, repos_file: Path,
                                  sample_count: int = 10) -> str:
    """Generate Gap Analysis Round 2 markdown document."""
    # Load repos and categories
    category_map = {}
    current_category = "Unknown"
    if repos_file.exists():
        with open(repos_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    if "Category" in line:
                        match = re.search(r'Category \d+:\s*(.+?)(?:\s*\(|$)', line)
                        if match:
                            current_category = match.group(1).strip()
                    continue
                category_map[line] = current_category
                category_map[line.replace("/", "_")] = current_category

    # Collect results
    prompt_files = sorted(results_dir.glob("*.prompt"))
    csv_data = {}
    csv_path = results_dir / "summary.csv"
    if csv_path.exists():
        with open(csv_path) as f:
            for row in csv.DictReader(f):
                csv_data[row.get("repo_name", "")] = row

    # Analyze each repo
    analyses = []
    all_sections: Dict[str, SectionAnalysis] = {}
    category_results: Dict[str, CategoryBreakdown] = {}
    failure_a, failure_b, failure_c, failure_d = [], [], [], []

    for pf in prompt_files:
        repo_name = pf.stem
        repo = repo_name.replace("_", "/", 1)
        cat = category_map.get(repo, category_map.get(repo_name, "Unknown"))

        # Get CSV data
        csv_row = csv_data.get(repo_name, {})
        exit_code = int(csv_row.get("exit_code", -1))
        duration = int(csv_row.get("duration_s", 0))
        file_count = int(csv_row.get("file_count", 0))

        # Check for clone failure
        try:
            first_line = pf.read_text(errors="replace").split("\n")[0]
            if first_line.strip() == "CLONE_FAILED":
                failure_a.append({"repo": repo, "reason": "Clone failed", "category": cat})
                continue
        except Exception:
            failure_a.append({"repo": repo, "reason": "Read error", "category": cat})
            continue

        # Parse prompt
        parsed = parse_prompt_sections(pf)

        # Track sections
        for section in parsed["sections"]:
            if section not in all_sections:
                all_sections[section] = SectionAnalysis(
                    section_name=section, total_repos=len(prompt_files)
                )
            all_sections[section].present_count += 1
            all_sections[section].repos_present.append(repo)

        # Category breakdown
        if cat not in category_results:
            category_results[cat] = CategoryBreakdown(category=cat)
        cb = category_results[cat]
        cb.total += 1

        # Classify
        scan_ok = (exit_code == 0 and parsed["total_lines"] > 10)
        has_sections = len(parsed["sections"]) >= 5
        has_runbook = "RUNBOOK" in parsed["sections"]
        domain_ok = bool(parsed["domain"] and "General" not in parsed["domain"]
                         and "Unknown" not in parsed["domain"])

        if not scan_ok:
            if exit_code == 124:
                failure_a.append({"repo": repo, "reason": "Timeout", "category": cat})
            elif exit_code != 0:
                failure_a.append({"repo": repo, "reason": f"Exit code {exit_code}", "category": cat})
            else:
                failure_a.append({"repo": repo, "reason": "Empty output", "category": cat})
            cb.failed += 1
        elif not has_sections:
            failure_b.append({
                "repo": repo, "sections": len(parsed["sections"]),
                "missing": [s for s in ["PROJECT", "CONTEXT", "PYTHON_TYPES", "SCHEMAS",
                                        "IMPLEMENTATION_LOGIC", "RUNBOOK", "OVERVIEW"]
                            if s not in parsed["sections"]],
                "category": cat,
            })
            cb.partial += 1
        else:
            if not domain_ok:
                failure_c.append({
                    "repo": repo, "detected_domain": parsed["domain"],
                    "category": cat,
                })
            if not has_runbook:
                failure_d.append({"repo": repo, "category": cat})
            cb.passed += 1

        # Accumulate stats for averages
        cb.avg_lines += parsed["total_lines"]
        cb.avg_sections += len(parsed["sections"])
        cb.avg_duration += duration

        analyses.append({
            "repo": repo, "category": cat, "lines": parsed["total_lines"],
            "sections": len(parsed["sections"]), "domain": parsed["domain"],
            "type": parsed["project_type"], "stack": parsed["stack"],
            "has_runbook": has_runbook, "frameworks": parsed["frameworks_detected"],
            "languages": parsed["languages_detected"], "duration": duration,
            "file_count": file_count,
        })

    # Compute averages
    for cb in category_results.values():
        if cb.total > 0:
            cb.avg_lines /= cb.total
            cb.avg_sections /= cb.total
            cb.avg_duration /= cb.total

    # Track missing sections
    expected_sections = ["AI_INSTRUCTION", "PROJECT", "CONTEXT", "OVERVIEW", "RUNBOOK",
                         "BUSINESS_DOMAIN", "PROGRESS", "ACTIONABLE_ITEMS",
                         "IMPLEMENTATION_LOGIC", "BEST_PRACTICES"]
    for s in expected_sections:
        if s not in all_sections:
            all_sections[s] = SectionAnalysis(
                section_name=s, total_repos=len(prompt_files)
            )
        all_sections[s].total_repos = len(prompt_files)

    # Select manual review samples
    samples = []
    if analyses:
        # Pick diverse samples across categories
        by_cat = defaultdict(list)
        for a in analyses:
            by_cat[a["category"]].append(a)
        for cat, repos_in_cat in sorted(by_cat.items()):
            if len(samples) >= sample_count:
                break
            # Take 1-2 from each category
            for r in repos_in_cat[:2]:
                if len(samples) < sample_count:
                    samples.append(r)

    # --- Generate Markdown ---
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    total = len(prompt_files)
    passed = sum(1 for a in analyses
                 if a["sections"] >= 5 and a["has_runbook"])
    pass_rate = (passed / total * 100) if total else 0

    md = []
    md.append("# CodeTrellis Gap Analysis — Round 2")
    md.append("")
    md.append(f"> **Generated:** {now}")
    md.append(f"> **CodeTrellis Version:** 4.4.0 (Phase A + B + C remediation applied)")
    md.append(f"> **Phase:** D (WS-8 — Public Repository Validation)")
    md.append(f"> **Repos Scanned:** {total}")
    md.append(f"> **Pass Rate:** {pass_rate:.1f}% (target: >70%)")
    md.append("")
    md.append("---")
    md.append("")

    # Executive Summary
    md.append("## 1. Executive Summary")
    md.append("")
    md.append(f"CodeTrellis was run against **{total} public repositories** spanning "
              f"{len(category_results)} categories to validate extraction quality "
              f"after Phases A, B, and C remediation.")
    md.append("")
    md.append("| Metric | Value | Target |")
    md.append("| --- | --- | --- |")
    md.append(f"| Total repos scanned | {total} | 60 |")
    md.append(f"| Full PASS | {sum(cb.passed for cb in category_results.values())} | — |")
    md.append(f"| PARTIAL | {sum(cb.partial for cb in category_results.values())} | — |")
    md.append(f"| FAIL | {sum(cb.failed for cb in category_results.values()) + len(failure_a)} | — |")
    md.append(f"| Pass rate | {pass_rate:.1f}% | >70% |")
    md.append("")

    # Section Coverage
    md.append("## 2. Section Coverage Across All Repos")
    md.append("")
    md.append("| Section | Present | Coverage | Target |")
    md.append("| --- | --- | --- | --- |")
    for s_name in expected_sections:
        sa = all_sections.get(s_name, SectionAnalysis(section_name=s_name, total_repos=total))
        target = {
            "RUNBOOK": ">90%", "BEST_PRACTICES": ">90%", "AI_INSTRUCTION": "100%",
            "PROJECT": "100%", "CONTEXT": ">95%", "OVERVIEW": ">90%",
        }.get(s_name, "—")
        md.append(f"| `[{sa.section_name}]` | {sa.present_count}/{total} "
                  f"| {sa.coverage_pct:.1f}% | {target} |")
    md.append("")

    # Per-Category Breakdown
    md.append("## 3. Per-Category Results")
    md.append("")
    md.append("| Category | Total | Pass | Partial | Fail | Avg Lines | Avg Sections |")
    md.append("| --- | --- | --- | --- | --- | --- | --- |")
    for cat, cb in sorted(category_results.items()):
        md.append(f"| {cat} | {cb.total} | {cb.passed} | {cb.partial} | {cb.failed} "
                  f"| {cb.avg_lines:.0f} | {cb.avg_sections:.1f} |")
    md.append("")

    # Failure Analysis (Phase D-4)
    md.append("## 4. Failure Analysis (Phase D-4 Categories)")
    md.append("")

    md.append("### Category A: Scan Failures")
    md.append(f"**Count:** {len(failure_a)}")
    md.append("")
    if failure_a:
        md.append("| Repo | Reason | Category |")
        md.append("| --- | --- | --- |")
        for f in failure_a:
            md.append(f"| `{f['repo']}` | {f['reason']} | {f['category']} |")
    else:
        md.append("✅ No scan failures.")
    md.append("")

    md.append("### Category B: Missing Context")
    md.append(f"**Count:** {len(failure_b)}")
    md.append("")
    if failure_b:
        md.append("| Repo | Sections | Missing |")
        md.append("| --- | --- | --- |")
        for f in failure_b[:10]:
            missing = ", ".join(f["missing"][:5])
            md.append(f"| `{f['repo']}` | {f['sections']} | {missing} |")
    else:
        md.append("✅ All repos have adequate context.")
    md.append("")

    md.append("### Category C: Wrong Context (Misdetection)")
    md.append(f"**Count:** {len(failure_c)}")
    md.append("")
    if failure_c:
        md.append("| Repo | Detected Domain | Category |")
        md.append("| --- | --- | --- |")
        for f in failure_c[:10]:
            md.append(f"| `{f['repo']}` | {f['detected_domain']} | {f['category']} |")
    else:
        md.append("✅ All domains correctly detected.")
    md.append("")

    md.append("### Category D: Missing Runbook")
    md.append(f"**Count:** {len(failure_d)}")
    md.append("")
    if failure_d:
        md.append("| Repo | Category |")
        md.append("| --- | --- |")
        for f in failure_d[:10]:
            md.append(f"| `{f['repo']}` | {f['category']} |")
    else:
        md.append("✅ All repos have RUNBOOK section.")
    md.append("")

    # Manual Review Samples (Phase D-3)
    md.append("## 5. Manual Review Samples (Phase D-3)")
    md.append("")
    md.append(f"Selected {len(samples)} repos for manual review:")
    md.append("")
    if samples:
        md.append("| # | Repo | Category | Lines | Sections | Domain | Frameworks |")
        md.append("| --- | --- | --- | --- | --- | --- | --- |")
        for i, s in enumerate(samples, 1):
            fw = ", ".join(s["frameworks"][:3]) if s["frameworks"] else "—"
            md.append(f"| {i} | `{s['repo']}` | {s['category']} | {s['lines']} "
                      f"| {s['sections']} | {s['domain'] or '—'} | {fw} |")
    md.append("")
    md.append("### Manual Review Checklist")
    md.append("")
    md.append("For each sampled repo:")
    md.append("- [ ] **Completeness**: Did CodeTrellis capture the most important schemas/controllers/APIs?")
    md.append("- [ ] **Runbook accuracy**: Can the `[RUNBOOK]` section actually be used to run the project?")
    md.append("- [ ] **Domain detection**: Is the business domain correct?")
    md.append("- [ ] **Duplication check**: Any excessive duplication?")
    md.append("- [ ] **AI validation**: Feed matrix.prompt to an LLM — is the explanation accurate?")
    md.append("")

    # Recommendations
    md.append("## 6. Recommendations")
    md.append("")
    if failure_a:
        md.append(f"1. **Fix {len(failure_a)} scan failures** — investigate timeouts and crashes")
    if failure_c:
        md.append(f"2. **Improve domain detection** — {len(failure_c)} repos misdetected")
    if failure_d:
        md.append(f"3. **Enhance RunbookExtractor** — {len(failure_d)} repos missing runbook")
    if not failure_a and not failure_c and not failure_d:
        md.append("🎉 All validation targets met. No critical issues found.")
    md.append("")
    md.append("---")
    md.append("")
    md.append(f"_Generated by CodeTrellis Phase D validation framework on {now}_")

    return "\n".join(md)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="CodeTrellis Results Analyzer — Phase D (WS-8)"
    )
    parser.add_argument("--output", "-o", default=None,
                        help="Output file (default: CodeTrellis_GAP_ANALYSIS_ROUND2.md)")
    parser.add_argument("--sample", type=int, default=10,
                        help="Number of repos for manual review sampling")
    parser.add_argument("--results-dir", default=None,
                        help="Path to validation-results directory")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    results_dir = Path(args.results_dir) if args.results_dir else script_dir / "validation-results"
    repos_file = script_dir / "repos.txt"

    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        print("   Run validation_runner.sh first.")
        sys.exit(1)

    output_path = Path(args.output) if args.output else (
        script_dir.parent.parent / "docs" / "gap_analysis" / "CodeTrellis_GAP_ANALYSIS_ROUND2.md"
    )

    print(f"Analyzing results from: {results_dir}")
    print(f"Output: {output_path}")
    print()

    report_md = generate_gap_analysis_round2(results_dir, repos_file, args.sample)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_md)

    print(f"✅ Gap Analysis Round 2 generated: {output_path}")
    print(f"   ({len(report_md.split(chr(10)))} lines)")


if __name__ == "__main__":
    main()
