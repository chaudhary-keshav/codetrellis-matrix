# CodeTrellis PyPI Launch — Master Implementation Program

# ═══════════════════════════════════════════════════════════════

# Session-Based Implementation with Quality Gates

# ═══════════════════════════════════════════════════════════════

#

# This is the executable implementation plan derived from the

# Multi-Agent Validated Plan (PYPI_LAUNCH_PLAN_VALIDATED.md).

#

# Each session is a standalone AI chat + commit.

# Quality gates validate each phase before moving forward.

#

# Date: 14 March 2026

# Status: IN PROGRESS

## Execution Update — 14 March 2026

- Sessions 1–3 were completed in small-session mode and locally validated.
- Local checks passed: version consistency, clean build, `twine check`, wheel YAML inclusion, wheel exclusions, clean venv install, and `pytest tests/ -x -q` (`7264 passed, 101 skipped`).
- Remaining work is still pending. Some later-session file drafts exist in the worktree, but they are not counted complete in this execution log.

---

# ═══════════════════════════════════════════════════════════════

# PRE-FLIGHT CHECKS

# ═══════════════════════════════════════════════════════════════

Before starting any session, confirm these:

```bash
# 1. Tests pass
pytest tests/ -x -q
# Expected: 7264+ passed

# 2. Venv is active
which python3

# 3. Git is clean
git status
# Expected: clean working tree (commit or stash first)

# 4. Check PyPI name availability
pip install codetrellis 2>&1 | head -3
# Expected: "No matching distribution" = name is available
# If taken, use "code-trellis" throughout all sessions
```

---

# ═══════════════════════════════════════════════════════════════

# PHASE 1: VERSION & BUILD HYGIENE (Sessions 1–4)

# ═══════════════════════════════════════════════════════════════

## Session 1 [⚡ Quick] [🤖 AI-heavy] — Version Sync & Dependency Restructure ✅ DONE

**Duration:** ~30m | **Depends on:** Nothing (first session)

**What you build:**

- `pyproject.toml` — version → `1.0.0`, restructured optional deps
- `codetrellis/__init__.py` — version → `1.0.0`
- `codetrellis/py.typed` — PEP 561 marker (empty file)

**What to ask the AI:**

> I'm publishing CodeTrellis to PyPI. I need these changes:
>
> 1. **`pyproject.toml`**: Change `version = "4.16.0"` to `version = "1.0.0"`. Restructure `[project.optional-dependencies]` to have these groups:
>    ```toml
>    [project.optional-dependencies]
>    ast = ["tree-sitter>=0.22.0", "tree-sitter-java>=0.23.0", "tree-sitter-python>=0.23.0", "tree-sitter-typescript>=0.23.0"]
>    yaml = ["pyyaml>=6.0"]
>    color = ["colorama>=0.4.6"]
>    tokens = ["tiktoken>=0.5.0"]
>    all = ["codetrellis[ast,yaml,color,tokens]"]
>    dev = ["pytest>=8.0.0", "pytest-cov>=4.0.0", "pytest-timeout>=2.3.0", "black>=24.0.0", "ruff>=0.1.0", "mypy>=1.8.0", "numpy>=2.0.0"]
>    ```
>    Also add these keywords: "mcp", "model-context-protocol", "code-context", "github-copilot", "claude", "cursor", "ai-context", "code-scanner"
> 2. **`codetrellis/__init__.py`**: Change `__version__ = "4.16.0"` to `__version__ = "1.0.0"`. Also update any Version docstring.
> 3. **Create `codetrellis/py.typed`**: Empty file (PEP 561 marker).
> 4. **Verify**: No other files under `codetrellis/` reference `4.16.0` as a hardcoded string (excluding cache path patterns which should remain dynamic). Search for version references.
>
> DO NOT change any test files, docs, or other files in this session.

**Exit check:**

```bash
# Version consistency
grep -c '"1.0.0"' pyproject.toml codetrellis/__init__.py
# Expected: 1 per file

# py.typed exists
test -f codetrellis/py.typed && echo "✅ py.typed" || echo "❌ MISSING"

# Optional deps structured
python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    d = tomllib.load(f)
deps = d['project']['optional-dependencies']
for g in ['ast', 'yaml', 'color', 'tokens', 'all', 'dev']:
    print(f'  {g}: {\"✅\" if g in deps else \"❌ MISSING\"}')"

# Tests still pass
pytest tests/ -x -q
```

**Commit:** `build: set version 1.0.0 and restructure optional dependencies`

---

## Session 2 [⚡ Quick] [🤖 AI-heavy] — CI/CD Workflow Fixes ✅ DONE

**Duration:** ~30m | **Depends on:** Session 1

**What you build:**

- `.github/workflows/ci.yml` — trigger on push + PR (not just workflow_dispatch)
- `.github/workflows/release.yml` — complete publish-pypi job, trigger on tag push

**What to ask the AI:**

> Fix the CI/CD workflows for PyPI publishing:
>
> 1. **`.github/workflows/ci.yml`**:
>    - Change trigger from `workflow_dispatch` to: push to `main`, pull requests to `main`
>    - Keep workflow_dispatch as additional trigger
>    - In the test job, update install command to use `pip install -e ".[dev]"` (which now includes test deps)
>    - Add a version-consistency check step after lint:
>      ```yaml
>      - name: Version consistency check
>        run: |
>          PYPROJECT_VER=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
>          INIT_VER=$(python3 -c "from codetrellis import __version__; print(__version__)")
>          if [ "$PYPROJECT_VER" != "$INIT_VER" ]; then
>            echo "❌ Version mismatch: pyproject.toml=$PYPROJECT_VER, __init__.py=$INIT_VER"
>            exit 1
>          fi
>          echo "✅ Version consistent: $PYPROJECT_VER"
>      ```
> 2. **`.github/workflows/release.yml`**:
>    - Change trigger to: push tags matching `v*` (keep workflow_dispatch too)
>    - Complete the `publish-pypi` job that's currently cut off:
>      ```yaml
>      publish-pypi:
>        runs-on: ubuntu-latest
>        needs: [build, publish-test]
>        environment: pypi
>        permissions:
>          id-token: write
>        steps:
>          - uses: actions/download-artifact@v4
>            with:
>              name: dist
>              path: dist/
>          - name: Publish to PyPI
>            uses: pypa/gh-action-pypi-publish@release/v1
>      ```
>    - Add version-from-tag validation step in build job
>
> Follow existing code style. Do not change any Python files.

**Exit check:**

```bash
# CI triggers include push
grep -A3 "^on:" .github/workflows/ci.yml | grep -c "push\|pull_request"
# Expected: ≥ 2

# Release triggers include tags
grep -A5 "^on:" .github/workflows/release.yml | grep "tags"
# Expected: shows tag pattern

# publish-pypi job exists and is complete
grep -c "publish-pypi" .github/workflows/release.yml
# Expected: ≥ 2 (job name + needs reference)

# YAML is valid
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('✅ ci.yml valid')"
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); print('✅ release.yml valid')"
```

**Commit:** `ci: automate CI on push/PR and complete release pipeline`

---

## Session 3 [🔨 Build] [🤖 AI-heavy] — Wheel Content Verification & Package Exclusions ✅ DONE

**Duration:** ~45m | **Depends on:** Session 1

**What you build:**

- `MANIFEST.in` — explicit include/exclude rules
- `pyproject.toml` — package-data and exclusion rules
- Verified wheel with correct contents

**What to ask the AI:**

> I need to verify and fix the wheel content for PyPI publishing:
>
> 1. **Create `MANIFEST.in`** with these rules:
>    ```
>    include LICENSE
>    include README.md
>    include CHANGELOG.md
>    include codetrellis/py.typed
>    recursive-include codetrellis *.py *.yaml *.yml *.json
>    recursive-exclude tests *
>    recursive-exclude docs *
>    recursive-exclude build *
>    recursive-exclude scripts *
>    exclude generate_letterhead.py
>    exclude requirements*.txt
>    exclude .gitignore
>    prune .codetrellis
>    prune .github
>    prune best_practices
>    prune lsp
>    prune codetrellis.egg-info
>    ```
> 2. **Update `pyproject.toml`** `[tool.setuptools]` section to ensure:
>    - `include-package-data = true`
>    - Package data includes `*.yaml`, `*.yml`, `*.json`, `py.typed`
>    - Exclude patterns for tests, docs, scripts
> 3. **Build and verify:**
>    ```bash
>    python3 -m build
>    # Check wheel contents
>    unzip -l dist/codetrellis-1.0.0-py3-none-any.whl | head -50
>    unzip -l dist/codetrellis-1.0.0-py3-none-any.whl | grep -c "\.yaml"
>    unzip -l dist/codetrellis-1.0.0-py3-none-any.whl | grep -E "tests/|docs/|scripts/"
>    # Check sdist
>    tar tzf dist/codetrellis-1.0.0.tar.gz | grep -E "tests/|docs/" | head -5
>    ```
> 4. **Test install in clean venv:**
>    ```bash
>    python3 -m venv /tmp/ct-wheel-test
>    source /tmp/ct-wheel-test/bin/activate
>    pip install dist/codetrellis-1.0.0-py3-none-any.whl
>    python -c "import codetrellis; print(codetrellis.__version__)"
>    codetrellis --help
>    deactivate
>    rm -rf /tmp/ct-wheel-test
>    ```

**Exit check:**

```bash
# Build succeeds
python3 -m build && echo "✅ Build OK" || echo "❌ Build FAILED"

# twine validates
twine check dist/* && echo "✅ Twine OK" || echo "❌ Twine FAILED"

# YAML files present in wheel
YAML_COUNT=$(unzip -l dist/*.whl 2>/dev/null | grep -c "\.yaml")
[ "$YAML_COUNT" -gt 0 ] && echo "✅ $YAML_COUNT YAML files in wheel" || echo "❌ No YAML files"

# No test/docs in wheel
TEST_COUNT=$(unzip -l dist/*.whl 2>/dev/null | grep -c "tests/")
[ "$TEST_COUNT" -eq 0 ] && echo "✅ No test files in wheel" || echo "❌ $TEST_COUNT test files found"

# Wheel size reasonable
ls -lh dist/*.whl
# Expected: < 5MB

# Clean venv install works
python3 -m venv /tmp/ct-verify
source /tmp/ct-verify/bin/activate
pip install dist/*.whl
python -c "import codetrellis; print(f'✅ Version: {codetrellis.__version__}')"
codetrellis --help > /dev/null && echo "✅ CLI works" || echo "❌ CLI broken"
deactivate && rm -rf /tmp/ct-verify
```

**Commit:** `build: configure package exclusions and verify wheel content`

---

## Session 4 [⚡ Quick] [🤖 AI-heavy] — Version Reference Cleanup ✅ DONE

**Duration:** ~20m | **Depends on:** Session 1

**What you build:**

- `README.md` — version references updated
- `CHANGELOG.md` — add `1.0.0` entry
- `STATUS.md` — add public release note

**What to ask the AI:**

> Update version references across documentation files for the `1.0.0` public launch:
>
> 1. **`README.md`**:
>    - Change `> **Version:** 5.1.0` to `> **Version:** 1.0.0`
>    - Change `## Features (v5.1.0)` to `## Features`
>    - Keep all `NEW in v4.x` notes as-is (they reference when features were added internally)
> 2. **`CHANGELOG.md`**:
>    - Add a new `## [1.0.0] - 2026-03-XX` entry above the existing `[4.16.0]` entry
>    - In it, write:
>
>      ```
>      ### 🎉 First Public Release
>
>      First public PyPI release. Consolidates 83 internal development sessions.
>
>      ### Highlights
>      - 120+ language and framework parsers
>      - MCP server for AI context injection
>      - JIT context engine for file-level queries
>      - Best Practices Library with 4,500+ practices
>      - Build contracts and quality gates
>      - Support for Python, TypeScript, Go, Rust, Java, C#, and 100+ more
>      - Works with GitHub Copilot, Claude, Cursor, and Windsurf
>
>      ### Internal History
>      Developed through sessions 1–83 (versions 4.9.0–5.7.0 internally).
>      See STATUS.md for detailed session history.
>      ```
>
> 3. **`STATUS.md`**: Add at the very top (line 1, before existing content):
>
>    ```
>    > **Public Release Version:** 1.0.0 (PyPI)
>    > Internal development tracked as v4.9.0–v5.7.0 across 83 sessions.
>    > This file contains internal development history.
>
>    ---
>    ```
>
> Do NOT change any Python source files.

**Exit check:**

```bash
# No more 5.1.0 in README header
grep -c "Version.*5\.1\.0" README.md
# Expected: 0

# 1.0.0 in CHANGELOG
grep -c "\[1.0.0\]" CHANGELOG.md
# Expected: 1

# STATUS has public release note
head -5 STATUS.md | grep -c "1.0.0"
# Expected: 1
```

**Commit:** `docs: update version references to 1.0.0 for public launch`

---

## ═══════════════════════════════════════════════════

## PHASE 1 QUALITY GATE — MUST PASS BEFORE PHASE 2

## ═══════════════════════════════════════════════════

```bash
echo "=== QG-1: Version Consistency ==="
PYPROJECT_VER=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
INIT_VER=$(python3 -c "
import re
with open('codetrellis/__init__.py') as f:
    m = re.search(r'__version__\s*=\s*\"([^\"]+)\"', f.read())
    print(m.group(1))
")
if [ "$PYPROJECT_VER" = "$INIT_VER" ] && [ "$PYPROJECT_VER" = "1.0.0" ]; then
    echo "✅ QG-1 PASS: Version $PYPROJECT_VER consistent"
else
    echo "❌ QG-1 FAIL: pyproject=$PYPROJECT_VER, init=$INIT_VER"
    exit 1
fi

echo ""
echo "=== QG-2: Build Integrity ==="
rm -rf dist/ build/
python3 -m build 2>&1 | tail -3
twine check dist/* 2>&1 | grep -E "PASSED|FAILED"

echo ""
echo "=== QG-3: Wheel Content ==="
YAML_COUNT=$(unzip -l dist/*.whl 2>/dev/null | grep -c "\.yaml")
TEST_COUNT=$(unzip -l dist/*.whl 2>/dev/null | grep -c "/tests/")
DOCS_COUNT=$(unzip -l dist/*.whl 2>/dev/null | grep -c "/docs/")
echo "YAML files: $YAML_COUNT (want > 0)"
echo "Test files: $TEST_COUNT (want 0)"
echo "Doc files: $DOCS_COUNT (want 0)"
[ "$YAML_COUNT" -gt 0 ] && [ "$TEST_COUNT" -eq 0 ] && [ "$DOCS_COUNT" -eq 0 ] && echo "✅ QG-3 PASS" || echo "❌ QG-3 FAIL"

echo ""
echo "=== QG-4: Install Gate ==="
python3 -m venv /tmp/ct-qg && source /tmp/ct-qg/bin/activate
pip install dist/*.whl -q
VER=$(python -c "import codetrellis; print(codetrellis.__version__)")
CLI=$(codetrellis --help 2>&1 | head -1)
deactivate && rm -rf /tmp/ct-qg
echo "Version: $VER"
echo "CLI: $CLI"
[ "$VER" = "1.0.0" ] && echo "✅ QG-4 PASS" || echo "❌ QG-4 FAIL"

echo ""
echo "=== QG-5: Test Suite ==="
RESULT=$(pytest tests/ -x -q 2>&1 | tail -1)
echo "$RESULT"
echo "$RESULT" | grep -q "passed" && echo "✅ QG-5 PASS" || echo "❌ QG-5 FAIL"

echo ""
echo "=== QG-6: CI Triggers ==="
grep -q "push:" .github/workflows/ci.yml && echo "✅ ci.yml push trigger" || echo "❌ ci.yml missing push"
grep -q "tags:" .github/workflows/release.yml && echo "✅ release.yml tag trigger" || echo "❌ release.yml missing tags"
grep -q "publish-pypi" .github/workflows/release.yml && echo "✅ publish-pypi job exists" || echo "❌ publish-pypi missing"

echo ""
echo "══════════════════════════════════════════"
echo "PHASE 1 GATE: Check all results above"
echo "ALL must be ✅ before proceeding to Phase 2"
echo "══════════════════════════════════════════"
```

---

# ═══════════════════════════════════════════════════════════════

# PHASE 2: DOCUMENTATION & TRUST SIGNALS (Sessions 5–8)

# ═══════════════════════════════════════════════════════════════

## Session 5 [🔨 Build] [🤝 Collaborative] — README Restructure

**Duration:** ~60m | **Depends on:** Session 1 (version), Session 3 (build verified)

**What you build:**

- `README.md` — restructured for user conversion
- `docs/FEATURES.md` — full features table moved here

**What to ask the AI:**

> Restructure the README.md for the PyPI launch. The goal is: a new user understands what CodeTrellis does and has it installed within 3 minutes.
>
> **Rules:**
>
> - DO NOT delete existing content — move it
> - Time-box: edit what's there, don't rewrite from scratch
>
> **New structure (top to bottom):**
>
> 1. **Title + one-liner**: `# CodeTrellis — Give AI Full Project Awareness`
>    Subtitle: "Scan your codebase, compress to ~1K tokens, inject into every AI prompt."
> 2. **Badges row**: PyPI version, Python versions, License, Tests
>    ```md
>    [![PyPI](https://img.shields.io/pypi/v/codetrellis)](https://pypi.org/project/codetrellis/)
>    [![Python](https://img.shields.io/pypi/pyversions/codetrellis)](https://pypi.org/project/codetrellis/)
>    [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
>    [![Tests](https://img.shields.io/badge/tests-7264%20passing-brightgreen)]()
>    ```
> 3. **Works With** section:
>    "Works with: GitHub Copilot | Claude | Cursor | Windsurf | any MCP-compatible AI"
> 4. **The Problem** (keep existing, trim to 4 bullet points max)
> 5. **Quick Start** (installation + first scan in < 5 lines):
>    ```bash
>    pip install codetrellis
>    codetrellis scan /path/to/project --optimal
>    codetrellis init . --ai  # sets up Copilot/Claude/Cursor integration
>    ```
> 6. **How It Works** (keep existing diagram, it's good)
> 7. **Top Features** — Pick the 8 most impressive:
>    - 120+ language/framework parsers
>    - MCP server for real-time AI context
>    - JIT context engine
>    - Incremental builds
>    - Best Practices Library (4,500+ practices)
>    - Works across Python, TypeScript, Go, Rust, Java, C#, and more
>    - Output tiers (compact to full)
>    - CI/CD mode for pipelines
>      Link: "📋 [Full feature list](docs/FEATURES.md)"
> 8. **Output Tiers** table (keep as-is, it's useful)
> 9. **CLI Commands** — Keep the quick reference
> 10. **Contributing** link
> 11. **License**
>
> **Also create `docs/FEATURES.md`**: Move the complete ~50 row features table there with the heading "# CodeTrellis — Complete Feature List". Include the full table unchanged.

**Exit check:**

```bash
# README has install command near top (within first 50 lines)
head -50 README.md | grep -c "pip install codetrellis"
# Expected: ≥ 1

# Badges present
head -20 README.md | grep -c "img.shields.io"
# Expected: ≥ 2

# FEATURES.md exists with full table
wc -l docs/FEATURES.md
# Expected: > 50 lines

# README links to FEATURES.md
grep -c "FEATURES.md" README.md
# Expected: ≥ 1

# No old version in README header
head -10 README.md | grep -c "5\.1\.0"
# Expected: 0
```

**Commit:** `docs: restructure README for PyPI launch and create FEATURES.md`

---

## Session 6 [⚡ Quick] [🤖 AI-heavy] — Trust Signal Files

**Duration:** ~20m | **Depends on:** Nothing

**What you build:**

- `SECURITY.md` — Responsible disclosure policy
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1
- `.github/FUNDING.yml` — GitHub Sponsors

**What to ask the AI:**

> Create three standard open-source trust signal files for CodeTrellis:
>
> 1. **`SECURITY.md`**: Standard responsible disclosure policy. Include:
>    - Supported versions table (only `1.0.x` for now)
>    - Report via email: `security@nsbrain.ai` (or GitHub Security Advisory)
>    - Response SLA: acknowledge within 72 hours
>    - Disclosure policy: coordinate before public disclosure
>    - Explicitly note: this tool only reads source code, it does not execute it
> 2. **`CODE_OF_CONDUCT.md`**: Contributor Covenant v2.1.
>    - Use the standard template from https://www.contributor-covenant.org/version/2/1/code_of_conduct/
>    - Contact: `conduct@nsbrain.ai`
> 3. **`.github/FUNDING.yml`**:
>    ```yaml
>    github: [chaudhary-keshav]
>    ```
>
> Use standard formatting. These are template files — don't over-customize.

**Exit check:**

```bash
for f in SECURITY.md CODE_OF_CONDUCT.md .github/FUNDING.yml; do
    [ -f "$f" ] && echo "✅ $f exists" || echo "❌ $f MISSING"
done

# SECURITY.md mentions version
grep -c "1.0" SECURITY.md
# Expected: ≥ 1
```

**Commit:** `docs: add SECURITY.md, CODE_OF_CONDUCT.md, and FUNDING.yml`

---

## Session 7 [⚡ Quick] [🤖 AI-heavy] — CHANGELOG & CONTRIBUTING Polish

**Duration:** ~20m | **Depends on:** Session 4 (CHANGELOG updated)

**What you build:**

- `CONTRIBUTING.md` — reviewed and updated for 1.0.0
- `CHANGELOG.md` — final polish

**What to ask the AI:**

> Review and update `CONTRIBUTING.md` for the 1.0.0 public launch:
>
> 1. **`CONTRIBUTING.md`**:
>    - Update "Clone and install" to use `pip install -e ".[dev]"` (not `pip install -r requirements-test.txt`)
>    - Verify architecture overview is still accurate
>    - Add a "Reporting Issues" section
>    - Add a "Pull Request Process" section (run tests, follow conventions, one parser per PR)
>    - Reference CODE_OF_CONDUCT.md
> 2. **`CHANGELOG.md`**:
>    - Review the `1.0.0` entry (added in session 4)
>    - Ensure the date is filled in (use today's date if publishing today)
>    - Ensure links at bottom of file point to correct comparison URLs
>
> Follow existing formatting.

**Exit check:**

```bash
# CONTRIBUTING references new install method
grep -c '\[dev\]' CONTRIBUTING.md
# Expected: ≥ 1

# CONTRIBUTING references code of conduct
grep -c "CODE_OF_CONDUCT" CONTRIBUTING.md
# Expected: ≥ 1

# CHANGELOG has dated 1.0.0 entry
grep "^\#\# \[1.0.0\]" CHANGELOG.md
# Expected: shows date
```

**Commit:** `docs: polish CONTRIBUTING.md and finalize CHANGELOG for 1.0.0`

---

## Session 8 [⚡ Quick] [🤖 AI-heavy] — PyPI Metadata Enhancement

**Duration:** ~15m | **Depends on:** Session 1

**What you build:**

- `pyproject.toml` — enhanced classifiers and metadata

**What to ask the AI:**

> Enhance the `pyproject.toml` metadata for maximum PyPI discoverability:
>
> 1. **Add/update classifiers:**
>    ```python
>    "Development Status :: 5 - Production/Stable",  # upgrade from Beta
>    "Topic :: Software Development :: Quality Assurance",
>    "Topic :: Software Development :: Libraries :: Python Modules",
>    "Typing :: Typed",  # since we have py.typed
>    ```
> 2. **Add/update keywords** (append to existing):
>    ```python
>    "mcp", "model-context-protocol", "code-context",
>    "github-copilot", "claude", "cursor", "windsurf",
>    "ai-context", "code-scanner", "code-intelligence",
>    "ast-parser", "framework-parser"
>    ```
> 3. **Add project URLs:**
>    ```toml
>    [project.urls]
>    Homepage = "https://github.com/chaudhary-keshav/codetrellis-matrix"
>    Repository = "https://github.com/chaudhary-keshav/codetrellis-matrix"
>    Changelog = "https://github.com/chaudhary-keshav/codetrellis-matrix/blob/main/CHANGELOG.md"
>    Documentation = "https://github.com/chaudhary-keshav/codetrellis-matrix/blob/main/README.md"
>    "Bug Tracker" = "https://github.com/chaudhary-keshav/codetrellis-matrix/issues"
>    ```
>
> Keep all existing content. Only add/update the items listed.

**Exit check:**

```bash
# Production status
grep -c "Production/Stable" pyproject.toml
# Expected: 1

# MCP keyword present
grep -c "model-context-protocol" pyproject.toml
# Expected: 1

# Bug tracker URL
grep -c "Bug Tracker" pyproject.toml
# Expected: 1

# Still builds
python3 -m build 2>&1 | tail -2
```

**Commit:** `build: enhance PyPI metadata for discoverability`

---

## ═══════════════════════════════════════════════════

## PHASE 2 QUALITY GATE — MUST PASS BEFORE PHASE 3

## ═══════════════════════════════════════════════════

```bash
echo "=== QG-7: Documentation Gate ==="
for f in README.md CHANGELOG.md CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md LICENSE .github/FUNDING.yml docs/FEATURES.md; do
    [ -f "$f" ] && echo "  ✅ $f" || echo "  ❌ MISSING: $f"
done

echo ""
echo "=== QG-8: README Quality ==="
INSTALL_LINE=$(grep -n "pip install codetrellis" README.md | head -1 | cut -d: -f1)
echo "  First 'pip install' at line: $INSTALL_LINE"
[ "$INSTALL_LINE" -lt 50 ] && echo "  ✅ Install command is near top" || echo "  ❌ Install command too far down"

BADGE_COUNT=$(head -20 README.md | grep -c "img.shields.io")
echo "  Badges in first 20 lines: $BADGE_COUNT"
[ "$BADGE_COUNT" -ge 2 ] && echo "  ✅ Badges present" || echo "  ❌ Missing badges"

echo ""
echo "=== QG-9: Build + Full Test ==="
rm -rf dist/ build/
python3 -m build 2>&1 | tail -2
twine check dist/* 2>&1 | grep -E "PASSED|FAILED"
pytest tests/ -x -q 2>&1 | tail -1

echo ""
echo "=== QG-10: Metadata Quality ==="
python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    d = tomllib.load(f)
kw = d['project'].get('keywords', [])
urls = d['project'].get('urls', {})
classifiers = d['project'].get('classifiers', [])
print(f'  Keywords: {len(kw)} (want ≥ 10)')
print(f'  URLs: {len(urls)} (want ≥ 4)')
print(f'  Classifiers: {len(classifiers)} (want ≥ 8)')
for needed in ['mcp', 'copilot', 'claude']:
    found = any(needed in k.lower() for k in kw)
    print(f'  Keyword \"{needed}\": {\"✅\" if found else \"❌ MISSING\"}')"

echo ""
echo "══════════════════════════════════════════"
echo "PHASE 2 GATE: Check all results above"
echo "ALL must be ✅ before proceeding to Phase 3"
echo "══════════════════════════════════════════"
```

---

# ═══════════════════════════════════════════════════════════════

# PHASE 3: PUBLISH & VERIFY (Sessions 9–12)

# ═══════════════════════════════════════════════════════════════

## Session 9 [🔨 Build] [👤 Human-heavy] — PyPI Account & TestPyPI Publish

**Duration:** ~45m | **Depends on:** Phase 1 + Phase 2 complete

**What you do (human steps):**

1. **Verify PyPI name availability:**

   ```bash
   pip index versions codetrellis 2>&1
   # If "No matching distribution" → name is available
   # If package exists → use "code-trellis" and update pyproject.toml name
   ```

2. **Create PyPI account** (if not already):
   - Go to https://pypi.org/account/register/
   - Enable 2FA

3. **Create TestPyPI account** (if not already):
   - Go to https://test.pypi.org/account/register/

4. **Set up Trusted Publishing on TestPyPI:**
   - Go to https://test.pypi.org/manage/account/publishing/
   - Add pending publisher:
     - Owner: `chaudhary-keshav`
     - Repository: `codetrellis-matrix`
     - Workflow: `release.yml`
     - Environment: `test-pypi`

5. **Set up Trusted Publishing on PyPI:**
   - Go to https://pypi.org/manage/account/publishing/
   - Add pending publisher:
     - Owner: `chaudhary-keshav`
     - Repository: `matrix`
     - Workflow: `release.yml`
     - Environment: `pypi`

6. **Manual TestPyPI publish** (to verify before CI):

   ```bash
   python3 -m build
   twine upload --repository testpypi dist/*
   # Enter TestPyPI credentials when prompted
   ```

7. **Verify TestPyPI install:**
   ```bash
   python3 -m venv /tmp/ct-testpypi
   source /tmp/ct-testpypi/bin/activate
   pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ codetrellis
   python -c "import codetrellis; print(codetrellis.__version__)"
   codetrellis --help
   deactivate && rm -rf /tmp/ct-testpypi
   ```

**Exit check:**

```bash
# TestPyPI page exists
curl -s "https://test.pypi.org/project/codetrellis/" | grep -c "codetrellis"
# Expected: > 0

# TestPyPI install works
python3 -m venv /tmp/ct-verify-test
source /tmp/ct-verify-test/bin/activate
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ codetrellis
VER=$(python -c "import codetrellis; print(codetrellis.__version__)")
echo "TestPyPI version: $VER"
deactivate && rm -rf /tmp/ct-verify-test
```

**Commit:** (no code changes — this is infrastructure setup)

---

## Session 10 [🔨 Build] [👤 Human-heavy] — PyPI Production Publish

**Duration:** ~30m | **Depends on:** Session 9

**What you do (human steps):**

1. **Final pre-flight check:**

   ```bash
   # All tests pass
   pytest tests/ -x -q

   # Build is clean
   rm -rf dist/ build/
   python3 -m build
   twine check dist/*

   # Version is correct
   python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"
   # Must print: 1.0.0

   # Git is clean
   git status
   ```

2. **Tag and push:**

   ```bash
   git tag -a v1.0.0 -m "🎉 First public release — CodeTrellis 1.0.0"
   git push origin main --tags
   ```

3. **Option A — CI publishes (preferred):**
   - Watch the `Release to PyPI` workflow run in GitHub Actions
   - Verify all jobs pass: test → build → publish-test → publish-pypi

4. **Option B — Manual publish (fallback):**

   ```bash
   twine upload dist/*
   # Enter PyPI credentials
   ```

5. **Verify production install:**

   ```bash
   # Wait 2-3 minutes for PyPI to index
   python3 -m venv /tmp/ct-prod
   source /tmp/ct-prod/bin/activate
   pip install codetrellis
   python -c "import codetrellis; print(codetrellis.__version__)"
   codetrellis --help

   # Quick functional test
   mkdir /tmp/ct-demo && cd /tmp/ct-demo
   echo 'def hello(): return "world"' > main.py
   codetrellis scan . --optimal
   cat .codetrellis/cache/*/matrix.prompt | head -20

   deactivate
   rm -rf /tmp/ct-prod /tmp/ct-demo
   ```

**Exit check:**

```bash
# PyPI page exists
curl -s "https://pypi.org/project/codetrellis/" | grep -c "codetrellis"
# Expected: > 0

# pip install works globally
pip install codetrellis 2>&1 | grep -i "successfully"
# Expected: "Successfully installed codetrellis-1.0.0"
```

**Commit:** (tag only — no code changes)

---

## Session 11 [⚡ Quick] [👤 Human-heavy] — GitHub Sponsors Setup

**Duration:** ~15m | **Depends on:** Nothing

**What you do (human steps):**

1. Go to https://github.com/sponsors/
2. Set up your sponsor profile:
   - Profile description: "Building CodeTrellis — AI context injection for every codebase"
   - Tiers: $5/mo, $15/mo, $50/mo (or whatever feels right)
3. Verify the "Sponsor" button appears on the repo

**Exit check:**

```bash
# FUNDING.yml exists
cat .github/FUNDING.yml
# Expected: shows github username

# Sponsor page accessible
curl -s "https://github.com/sponsors/chaudhary-keshav" | grep -c "Sponsor"
# Expected: > 0
```

**Commit:** (no code changes)

---

## Session 12 [🔨 Build] [🤝 Collaborative] — Final Validation & Smoke Test

**Duration:** ~30m | **Depends on:** All previous sessions

**What you do:**

Run the complete end-to-end validation suite:

```bash
#!/bin/bash
# ═══════════════════════════════════════════════════
# FINAL VALIDATION SUITE
# ═══════════════════════════════════════════════════

PASS=0
FAIL=0

check() {
    if [ $? -eq 0 ]; then
        echo "  ✅ $1"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $1"
        FAIL=$((FAIL + 1))
    fi
}

echo "═══════════════════════════════════════"
echo "  CodeTrellis 1.0.0 — Final Validation"
echo "═══════════════════════════════════════"
echo ""

echo "── Version Consistency ──"
V1=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
V2=$(python3 -c "import re; print(re.search(r'__version__\s*=\s*\"([^\"]+)\"', open('codetrellis/__init__.py').read()).group(1))")
[ "$V1" = "1.0.0" ] && [ "$V2" = "1.0.0" ]; check "Version consistent ($V1)"

echo ""
echo "── Required Files ──"
for f in README.md CHANGELOG.md CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md LICENSE .github/FUNDING.yml docs/FEATURES.md codetrellis/py.typed MANIFEST.in; do
    [ -f "$f" ]; check "$f exists"
done

echo ""
echo "── Build ──"
rm -rf dist/ build/ *.egg-info
python3 -m build > /dev/null 2>&1; check "python3 -m build"
twine check dist/* > /dev/null 2>&1; check "twine check"

echo ""
echo "── Wheel Content ──"
YAML_COUNT=$(unzip -l dist/*.whl 2>/dev/null | grep -c "\.yaml")
[ "$YAML_COUNT" -gt 0 ]; check "YAML files in wheel ($YAML_COUNT)"
TEST_COUNT=$(unzip -l dist/*.whl 2>/dev/null | grep -c "/tests/")
[ "$TEST_COUNT" -eq 0 ]; check "No test files in wheel"
WHEEL_SIZE=$(ls -l dist/*.whl | awk '{print $5}')
[ "$WHEEL_SIZE" -lt 10000000 ]; check "Wheel size < 10MB ($(echo "scale=1; $WHEEL_SIZE / 1048576" | bc)MB)"

echo ""
echo "── Clean Install ──"
python3 -m venv /tmp/ct-final-check
source /tmp/ct-final-check/bin/activate
pip install dist/*.whl -q 2>/dev/null; check "Wheel installs"
python -c "import codetrellis" 2>/dev/null; check "Import works"
VER=$(python -c "from codetrellis import __version__; print(__version__)" 2>/dev/null)
[ "$VER" = "1.0.0" ]; check "Installed version is 1.0.0"
codetrellis --help > /dev/null 2>&1; check "CLI --help works"
deactivate
rm -rf /tmp/ct-final-check

echo ""
echo "── Test Suite ──"
RESULT=$(pytest tests/ -x -q 2>&1 | tail -1)
echo "$RESULT" | grep -q "passed"; check "Tests pass: $RESULT"

echo ""
echo "── CI Configuration ──"
grep -q "push:" .github/workflows/ci.yml; check "CI triggers on push"
grep -q "tags:" .github/workflows/release.yml; check "Release triggers on tags"
grep -q "publish-pypi" .github/workflows/release.yml; check "publish-pypi job exists"

echo ""
echo "── README Quality ──"
head -50 README.md | grep -q "pip install codetrellis"; check "Install in first 50 lines"
head -20 README.md | grep -q "img.shields.io"; check "Badges present"
grep -q "FEATURES.md" README.md; check "Links to FEATURES.md"

echo ""
echo "── PyPI Metadata ──"
python3 -c "
import tomllib, sys
d = tomllib.load(open('pyproject.toml','rb'))
kw = d['project'].get('keywords', [])
sys.exit(0 if len(kw) >= 10 else 1)"; check "≥10 keywords"
python3 -c "
import tomllib, sys
d = tomllib.load(open('pyproject.toml','rb'))
urls = d['project'].get('urls', {})
sys.exit(0 if len(urls) >= 4 else 1)"; check "≥4 project URLs"

echo ""
echo "═══════════════════════════════════════"
echo "  RESULTS: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════"
if [ "$FAIL" -eq 0 ]; then
    echo "  🎉 ALL GATES PASSED — Ready for launch!"
else
    echo "  ⚠️  FIX $FAIL failures before publishing"
fi
```

**Commit:** (no code changes — validation only)

---

# ═══════════════════════════════════════════════════════════════

# SESSION SUMMARY DASHBOARD

# ═══════════════════════════════════════════════════════════════

| Session   | Phase | Duration | Type | Key Deliverable                  | Files                                              |
| --------- | ----- | -------- | ---- | -------------------------------- | -------------------------------------------------- |
| 1         | P1    | ~30m     | ⚡🤖 | Version 1.0.0 + deps restructure | `pyproject.toml`, `__init__.py`, `py.typed`        |
| 2         | P1    | ~30m     | ⚡🤖 | CI/CD workflow fixes             | `ci.yml`, `release.yml`                            |
| 3         | P1    | ~45m     | 🔨🤖 | Wheel content verification       | `MANIFEST.in`, `pyproject.toml`                    |
| 4         | P1    | ~20m     | ⚡🤖 | Version ref cleanup in docs      | `README.md`, `CHANGELOG.md`, `STATUS.md`           |
| —         | —     | —        | —    | **PHASE 1 QUALITY GATE**         | QG 1-6                                             |
| 5         | P2    | ~60m     | 🔨🤝 | README restructure + FEATURES.md | `README.md`, `docs/FEATURES.md`                    |
| 6         | P2    | ~20m     | ⚡🤖 | Trust signal files               | `SECURITY.md`, `CODE_OF_CONDUCT.md`, `FUNDING.yml` |
| 7         | P2    | ~20m     | ⚡🤖 | CONTRIBUTING + CHANGELOG polish  | `CONTRIBUTING.md`, `CHANGELOG.md`                  |
| 8         | P2    | ~15m     | ⚡🤖 | PyPI metadata enhancement        | `pyproject.toml`                                   |
| —         | —     | —        | —    | **PHASE 2 QUALITY GATE**         | QG 7-10                                            |
| 9         | P3    | ~45m     | 🔨👤 | TestPyPI publish + verify        | Infrastructure                                     |
| 10        | P3    | ~30m     | 🔨👤 | Production PyPI publish          | Tag + publish                                      |
| 11        | P3    | ~15m     | ⚡👤 | GitHub Sponsors setup            | Infrastructure                                     |
| 12        | P3    | ~30m     | 🔨🤝 | Final validation suite           | Validation script                                  |
| **TOTAL** |       | **~6h**  |      | **Published on PyPI**            | **~15 files**                                      |

---

# ═══════════════════════════════════════════════════════════════

# SESSION TRACKING TABLE

# ═══════════════════════════════════════════════════════════════

| Session | Estimated | Actual | Status         | Notes                                                                               |
| ------- | --------- | ------ | -------------- | ----------------------------------------------------------------------------------- |
| 1       | 30m       | ~20m   | ✅ Complete    | Version sync, optional deps, `py.typed`, stale Python version refs cleaned          |
| 2       | 30m       | ~15m   | ✅ Complete    | CI trigger fixes retained; release workflow now validates tag version               |
| 3       | 45m       | ~25m   | ✅ Complete    | MANIFEST/package data verified; wheel contains YAML and excludes tests/docs/scripts |
| 4       | 20m       | ~15m   | ✅ Complete    | Version refs updated: README, CHANGELOG 1.0.0 entry, STATUS.md public release note  |
| QG P1   | 10m       | ~5m    | ✅ Complete    | Local gate passed: build, twine, clean install, tests, workflow trigger presence    |
| 5       | 60m       | ~30m   | ✅ Complete    | README restructured for user conversion; docs/FEATURES.md created with full table   |
| 6       | 20m       | ~10m   | ✅ Complete    | SECURITY.md, CODE_OF_CONDUCT.md (Contributor Covenant v2.1), .github/FUNDING.yml    |
| 7       | 20m       | ~15m   | ✅ Complete    | CONTRIBUTING.md polished (dev install, PR process, COC ref); CHANGELOG finalized    |
| 8       | 15m       | ~10m   | ✅ Complete    | 19 keywords, 14 classifiers, 5 URLs; Production/Stable, Typing::Typed added         |
| QG P2   | 10m       | ~10m   | ✅ Complete    | All 10 quality gates passed (validated 14 Mar 2026)                                 |
| 9       | 45m       |        | ⬜ Not Started | Human: PyPI/TestPyPI accounts, Trusted Publishing OIDC, TestPyPI upload             |
| 10      | 30m       |        | ⬜ Not Started | Human: Tag v1.0.0, push, CI publishes or manual `twine upload`                      |
| 11      | 15m       |        | ⬜ Not Started | Human: GitHub Sponsors profile setup                                                |
| 12      | 30m       |        | ⬜ Not Started | Human: End-to-end validation after PyPI publication                                 |

---

# ═══════════════════════════════════════════════════════════════

# MEGA-PROMPT OPTION (Marathon Approach)

# ═══════════════════════════════════════════════════════════════

If you prefer to do this in fewer, larger sessions:

```
Morning (~2.5h): Phase 1 — Version & Build
├─ Mega 1: Sessions 1+3 — Version sync + wheel verification (~1.5h)
├─ Mega 2: Sessions 2+4 — CI fixes + doc version cleanup (~1h)
└─ Run Phase 1 Quality Gate

Afternoon (~2h): Phase 2 — Documentation
├─ Mega 3: Sessions 5+8 — README restructure + metadata (~1.5h)
├─ Mega 4: Sessions 6+7 — Trust files + CONTRIBUTING polish (~30m)
└─ Run Phase 2 Quality Gate

Evening (~1.5h): Phase 3 — Publish
├─ Session 9: TestPyPI publish (~45m)
├─ Session 10: Production publish (~30m)
├─ Session 11+12: Sponsors + final validation (~15m)
└─ 🎉 Launch complete
```

### Mega-Prompt 1 — Version & Build (Sessions 1+3)

> I'm publishing CodeTrellis to PyPI. This is a batch edit for version sync and build verification.
>
> **1. `pyproject.toml`**: Change version to `1.0.0`. Add optional dependency groups: `ast` (tree-sitter packages), `yaml` (pyyaml), `color` (colorama), `tokens` (tiktoken), `all` (combines all), `dev` (test/lint tools). Add keywords: mcp, model-context-protocol, github-copilot, claude, cursor, ai-context. Configure package-data to include `*.yaml`, `*.yml`, `*.json`, `py.typed`.
>
> **2. `codetrellis/__init__.py`**: Change `__version__` to `1.0.0`.
>
> **3. Create `codetrellis/py.typed`**: Empty file.
>
> **4. Create `MANIFEST.in`**: Include LICENSE, README, CHANGELOG, py.typed. Recursive-include `codetrellis/**/*.py *.yaml *.yml *.json`. Exclude tests, docs, scripts, build, .codetrellis, .github.
>
> **5. Verify build**: Run `python3 -m build`, `twine check dist/*`, inspect wheel with `unzip -l`, install in clean venv.

### Mega-Prompt 2 — CI & Doc Versions (Sessions 2+4)

> Fix CI/CD and version references:
>
> **1. `.github/workflows/ci.yml`**: Trigger on push/PR (not just workflow_dispatch). Add version consistency check step.
>
> **2. `.github/workflows/release.yml`**: Trigger on tag push `v*`. Complete the publish-pypi job with OIDC trusted publishing.
>
> **3. `README.md`**: Change version from 5.1.0 to 1.0.0.
>
> **4. `CHANGELOG.md`**: Add 1.0.0 entry as first public release.
>
> **5. `STATUS.md`**: Add note at top that public version is 1.0.0.

### Mega-Prompt 3 — README & Metadata (Sessions 5+8)

> Restructure README for PyPI launch and enhance metadata:
>
> **1. `README.md`**: Reorder to: title → badges → Works With → Problem → Quick Start (pip install codetrellis) → How It Works diagram → Top 8 features → Output Tiers → CLI → Contributing → License. Move full features table to `docs/FEATURES.md`.
>
> **2. `pyproject.toml`**: Upgrade status to Production/Stable. Add Typing::Typed. Add Bug Tracker and Documentation URLs.

### Mega-Prompt 4 — Trust Files (Sessions 6+7)

> Create trust signal files for the CodeTrellis open-source launch:
>
> **1. `SECURITY.md`**: Responsible disclosure, supported versions (1.0.x), security@nsbrain.ai.
> **2. `CODE_OF_CONDUCT.md`**: Contributor Covenant v2.1.
> **3. `.github/FUNDING.yml`**: GitHub Sponsors for chaudhary-keshav.
> **4. `CONTRIBUTING.md`**: Update install to use `.[dev]`, add PR process, reference CODE_OF_CONDUCT.

---

# ═══════════════════════════════════════════════════════════════

# POST-LAUNCH CHECKLIST (After Session 12)

# ═══════════════════════════════════════════════════════════════

After successful PyPI publication, these are the next actions from the monetization analysis:

- [ ] Write first blog post: "How CodeTrellis gives GitHub Copilot full project context via MCP"
- [ ] Share on r/programming, Hacker News, dev.to
- [ ] Post in Python Discord, AI dev-tools communities
- [ ] Engage with MCP ecosystem (Anthropic community)
- [ ] Monitor PyPI download stats: https://pypistats.org/packages/codetrellis
- [ ] Respond to any GitHub issues within 48 hours
- [ ] Plan v1.1.0 based on user feedback (first 30 days)

---

_This plan is derived from the Multi-Agent Validated Plan (PYPI_LAUNCH_PLAN_VALIDATED.md) and the Monetization Analysis (monetization-analysis.md). All 6 agents approved. Execute sessions sequentially, run quality gates between phases._
