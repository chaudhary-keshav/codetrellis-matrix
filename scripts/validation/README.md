# CodeTrellis Public Repository Validation Framework

> **Phase D — WS-8 (Workstream 8)**
> **Purpose:** Validate CodeTrellis extraction quality against diverse public repositories

## Overview

This framework runs CodeTrellis scans against **60 public GitHub repositories** across 6 categories to ensure the tool produces accurate, useful context for any project type.

## Quick Start

```bash
# 1. Run validation (all 60 repos)
chmod +x validation_runner.sh
./validation_runner.sh

# 2. Score results
python3 quality_scorer.py --verbose

# 3. Generate Gap Analysis Round 2
python3 analyze_results.py
```

## Scripts

| Script                 | Purpose                                        |
| ---------------------- | ---------------------------------------------- |
| `validation_runner.sh` | Clones repos and runs CodeTrellis `--optimal` scans   |
| `quality_scorer.py`    | Scores each scan against Phase D-2 rubric      |
| `analyze_results.py`   | Generates Gap Analysis Round 2 markdown report |
| `repos.txt`            | List of 60 repositories to validate against    |

## Usage Examples

### Run subset of repos

```bash
# First 5 repos only
./validation_runner.sh --max 5

# Only category 2 (Microservices & Backend)
./validation_runner.sh --category 2

# Single repo
./validation_runner.sh --repo nestjs/nest

# Resume interrupted run
./validation_runner.sh --resume

# Cleanup cloned repos after scan
./validation_runner.sh --cleanup
```

### Score with custom threshold

```bash
# Default threshold: 70% pass rate
python3 quality_scorer.py --verbose --output quality_report.json

# Custom threshold
python3 quality_scorer.py --threshold 80
```

### Generate analysis report

```bash
# Default output: docs/gap_analysis/CodeTrellis_GAP_ANALYSIS_ROUND2.md
python3 analyze_results.py

# Custom output
python3 analyze_results.py --output my_report.md --sample 15
```

## Repository Categories

| #   | Category                  | Repos | Coverage Purpose                            |
| --- | ------------------------- | ----- | ------------------------------------------- |
| 1   | Full-Stack Applications   | 10    | Monorepos, mixed stacks, CI/CD              |
| 2   | Microservices & Backend   | 10    | NestJS, FastAPI, Flask, gRPC, multi-service |
| 3   | AI/ML Projects            | 10    | Python-heavy, notebooks, training scripts   |
| 4   | DevTools & Infrastructure | 10    | Go, Rust, Terraform, Docker-heavy           |
| 5   | Frontend Frameworks       | 10    | Angular, React, Vue, Svelte, component libs |
| 6   | Specialized & Edge Cases  | 10    | Multi-language, unusual structures, Rust    |

## Quality Scoring Rubric

### Required (must pass all)

- ✅ Scan completes (exit code 0)
- ✅ Non-empty output (>10 lines)
- ✅ Correct project name detected
- ✅ No Python tracebacks in stderr

### Threshold Metrics (scored 0-6)

- Stack detected (non-empty) — target >80% repos
- Business domain detected (not "General Application") — target >60% repos
- `[RUNBOOK]` section present — target >90% repos
- No contamination (PROGRESS TODOs < 500) — target >95% repos
- Reasonable size (<50,000 lines) — target >95% repos
- At least 5 sections present — target >90% repos

### Verdict

- **PASS**: Required + threshold ≥ 5/6
- **PARTIAL**: Required + threshold ≥ 3/6
- **FAIL**: Missing required or threshold < 3/6

## Output Files

```
validation-results/
├── summary.csv              # Per-repo CSV: exit_code, duration, lines
├── summary.txt              # Human-readable summary
├── quality_report.json      # Detailed quality scoring (from quality_scorer.py)
├── <repo_name>.prompt       # CodeTrellis matrix.prompt output
├── <repo_name>.json         # CodeTrellis JSON output (if available)
└── <repo_name>.log          # Stderr + timing log
```

## Phase D-4: Failure Categories

The analyzer categorizes failures into 4 types:

| Category | Description                            | Root Cause Fix Location         |
| -------- | -------------------------------------- | ------------------------------- |
| A        | Scan failures (crash, timeout, empty)  | Extractors, scanner             |
| B        | Missing context (code not captured)    | New extractor or blind spot fix |
| C        | Wrong context (misdetection)           | Detection heuristics, filtering |
| D        | Missing execution context (no runbook) | RunbookExtractor for new types  |
