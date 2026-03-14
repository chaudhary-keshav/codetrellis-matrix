# Multi-Agent Plan Validation: CodeTrellis PyPI Launch

# =====================================================================

# Purpose: Validate the plan to publish CodeTrellis to PyPI, fix version chaos,

# polish documentation, and establish the project for public consumption.

#

# Date: 14 March 2026

# Author: Keshav Chaudhary

# Project: CodeTrellis — PyPI Publication & Public Launch

## Execution Update — 14 March 2026

- Small-session implementation completed for Sessions 1–3.
- Local validation passed: version consistency, clean build, `twine check`, wheel YAML inclusion, wheel exclusions, clean wheel install, and `pytest tests/ -x -q` (`7264 passed, 101 skipped`).
- Remaining work is still pending before TestPyPI/PyPI publication.

---

# ═══════════════════════════════════════════════════════════════

# SECTION A: THE PLAN (v1.0 — Draft for Review)

# ═══════════════════════════════════════════════════════════════

## Plan Name: CodeTrellis PyPI Launch & Public Readiness

## Executive Summary

Publish CodeTrellis to PyPI as `pip install codetrellis`, fix all version inconsistencies, polish README for first impressions, automate CI/CD for releases, and set up GitHub Sponsors. This is Phase 0 from the monetization analysis — the prerequisite work that enables everything else.

## Problem Statement

CodeTrellis is a fully functional tool with 120+ parsers and 7,264 passing tests, but:

- **Not on PyPI** — impossible to `pip install`
- **Version chaos** — `4.16.0` in `pyproject.toml`/`__init__.py`, `5.1.0` in README, `5.7.0` in STATUS.md
- **CI not triggered automatically** — workflows use `workflow_dispatch` only
- **README is developer-facing, not user-facing** — too long, features-heavy, no quick demo
- **No SECURITY.md, CODE_OF_CONDUCT.md** — enterprise red flags
- **CHANGELOG incomplete** — only one version entry
- **Optional dependencies not structured** — `requirements.txt` has deps not in `pyproject.toml`
- **No `__main__.py` entry for `python -m codetrellis`** verification

## Proposed Solution

A structured 3-phase approach to make CodeTrellis publicly installable, trustworthy, and discoverable.

## Implementation Phases

### Phase 1: Version & Build Hygiene — Day 1–2

1. **Fix version numbers** — Canonicalize to `1.0.0` (reset for public launch)
2. **Sync `pyproject.toml`** — Move optional deps from `requirements.txt` into `[project.optional-dependencies]`
3. **Update `__init__.py`** — Single source of truth version
4. **Fix CI workflow** — Trigger on push/PR, add tag-based release
5. **Validate build** — `python -m build && twine check dist/*`
6. **Test install** — `pip install dist/*.whl` in clean venv

### Phase 2: Documentation & Trust Signals — Day 3–5

1. **Rewrite README.md** — Problem → Solution → Install → Quick Start → Features (under 3 min read)
2. **Update CHANGELOG.md** — Add `1.0.0` release entry consolidating all work
3. **Create SECURITY.md** — Responsible disclosure policy
4. **Create CODE_OF_CONDUCT.md** — Standard Contributor Covenant
5. **Polish CONTRIBUTING.md** — Already exists, review & update
6. **Create `.github/FUNDING.yml`** — GitHub Sponsors setup
7. **Add badges to README** — PyPI version, Python versions, tests, license

### Phase 3: Release Automation & PyPI Publish — Day 6–7

1. **Fix `release.yml`** — Trigger on tag push (`v*`), complete the publish-pypi job
2. **Set up PyPI Trusted Publishing** — Configure OIDC in PyPI project settings
3. **Test with TestPyPI first** — Publish to test.pypi.org, verify install
4. **Publish to PyPI** — Tag `v1.0.0`, push, let CI publish
5. **Verify** — `pip install codetrellis` from PyPI in a fresh environment
6. **Set up GitHub Sponsors** — Complete the profile

## Success Metrics

| Metric                          | Target                             | How Measured                    |
| ------------------------------- | ---------------------------------- | ------------------------------- |
| `pip install codetrellis` works | Yes/No                             | Install in clean venv from PyPI |
| Version consistency             | 1 version string everywhere        | `grep -r` across all files      |
| Tests pass in CI                | 7,264+ pass, 0 fail                | GitHub Actions badges           |
| README read time                | < 3 minutes to first `pip install` | Manual timing                   |
| Build reproducible              | `twine check` passes               | CI package job                  |
| PyPI metadata correct           | All classifiers, URLs, description | PyPI project page               |

## Risks

| Risk                                  | Impact                      | Mitigation                                                       |
| ------------------------------------- | --------------------------- | ---------------------------------------------------------------- |
| Name `codetrellis` taken on PyPI      | Blocks publication          | Check PyPI now; fallback: `code-trellis`                         |
| Large package size (120+ parsers)     | Slow install, user friction | Measure wheel size; extractors are pure Python so should be fine |
| Missing `__init__.py` in sub-packages | ImportError on install      | Test wheel install in clean venv                                 |
| Optional deps cause install failures  | User abandons tool          | Only `watchdog` as core dep; rest in extras                      |
| PyPI Trusted Publishing OIDC setup    | Manual token fallback       | Can use API token if OIDC fails                                  |

## Timeline

3 phases across 7 working days.

## Dependencies

- PyPI account registered and project name reserved
- GitHub repo made public (or ready to make public)
- CI secrets configured for PyPI publishing

---

# ═══════════════════════════════════════════════════════════════

# SECTION B: ROUND 1 — INDEPENDENT AGENT REVIEWS

# ═══════════════════════════════════════════════════════════════

## 🔴 AGENT 1: THE SKEPTIC

### Verdict: CONDITIONAL PASS

### ✅ Agreements

- Version chaos is the #1 blocker. Fixing it first is correct.
- Publishing to PyPI is high-leverage: one action unlocks entire ecosystem.
- Keeping `watchdog` as sole required dependency is smart — minimal install surface.
- 7,264 passing tests means the code works. This isn't vaporware.

### ⚠️ Concerns

1. **Resetting to `1.0.0`**: STATUS.md references `v5.7.0`. If anyone has ever seen these version numbers, jumping to `1.0.0` looks like a downgrade. Consider `5.0.0` instead if there's any prior public exposure.
2. **README rewrite scope creep**: "Under 3 minutes" is a goal, not a deliverable. The current README is ~200 lines. Don't spend 2 days wordsmithing.
3. **OIDC Trusted Publishing**: Nice but fiddly. If it doesn't work in 30 minutes, fall back to API token and move on.
4. **Package size**: 120+ parser files in pure Python. The wheel could be 2-5MB. That's fine, but verify the `MANIFEST.in` or `pyproject.toml` excludes test files, docs, `.codetrellis/cache/`.

### ❌ Won't Work

- Nothing is fundamentally broken here. The plan is straightforward.

### 💡 Alternatives

- Skip SECURITY.md/CODE_OF_CONDUCT.md for now — they're nice-to-have for a 0-star project. Focus on pip install working.
- Don't rewrite README from scratch. Edit the existing one: move install to the top, add GIF, cut the features table in half.

---

## 🟢 AGENT 2: THE ARCHITECT

### Verdict: PASS

### ✅ Agreements

- Single source of truth for version in `__init__.py` with `pyproject.toml` reading from it (or vice versa) is the right pattern.
- `[project.optional-dependencies]` with groups (`ast`, `lsp`, `dev`, `yaml`) is correct Python packaging practice.
- CI trigger on push + tag-based release is standard.
- The existing `pyproject.toml` is well-structured — mostly needs version sync and optional deps.

### ⚠️ Concerns

1. **Dynamic versioning**: Consider using `setuptools-scm` or `importlib.metadata` pattern to avoid maintaining version in two places. But for v1.0 launch, hardcoded is fine.
2. **Package data**: The `bpl/practices/*.yaml` files need to be included in the wheel. Verify `include-package-data = true` captures them.
3. **Entry point**: `codetrellis = "codetrellis.cli:main"` is correct. Verify `__main__.py` also works for `python -m codetrellis`.
4. **Namespace packages**: With 120+ parser files at the top level of `codetrellis/`, importing is flat. This is fine for now but document that extractors are under `codetrellis/extractors/`.

### ❌ Won't Work

- Nothing structurally wrong.

### 💡 Alternatives

- Add a `py.typed` marker file to signal PEP 561 type hint support — free credibility with enterprise users.
- Consider a `codetrellis[all]` extra that installs everything (tree-sitter, tiktoken, pyyaml).

---

## 🔵 AGENT 3: THE USER ADVOCATE

### Verdict: CONDITIONAL PASS

### ✅ Agreements

- "Problem → Solution → Install → Quick Start" README structure is correct.
- `pip install codetrellis` is the only thing that matters for first-time users.
- Minimal required dependencies (`watchdog` only) means fast install.

### ⚠️ Concerns

1. **First 30 seconds**: A user lands on the GitHub page. What do they see? The README needs:
   - One-line description
   - A GIF or screenshot showing before/after (AI without CodeTrellis vs. with)
   - `pip install codetrellis && codetrellis scan .` — done in 2 commands
   - Everything else is secondary
2. **Feature table is overwhelming**: 50+ features in the current README. Users don't read tables. Show 5 top features, link to docs for the rest.
3. **No examples directory**: A `examples/` folder with a small demo project would help. Not required for launch but should be in Phase 2.
4. **Error messages on missing optional deps**: When a user scans a Java project but doesn't have `tree-sitter-java`, the error should say "Install tree-sitter-java for better Java parsing: `pip install codetrellis[ast]`" — not a traceback.

### ❌ Won't Work

- The current README will not convert visitors to users. It reads like internal documentation, not a landing page.

### 💡 Alternatives

- Create a separate `docs/FEATURES.md` for the exhaustive feature table. Keep README lean.
- Add a `--doctor` command that checks which optional deps are installed and recommends extras.

---

## 🟡 AGENT 4: THE BUSINESS STRATEGIST

### Verdict: PASS

### ✅ Agreements

- Phase 0 (publish first, monetize later) is the right sequence.
- MIT license is correct for maximum adoption.
- GitHub Sponsors is zero-cost to set up — do it immediately.
- The name "CodeTrellis" is strong and memorable.

### ⚠️ Concerns

1. **PyPI name availability**: Check `pip install codetrellis` right now. If taken, alternatives: `code-trellis`, `codetrellis-ai`, `ct-matrix`.
2. **SEO and discoverability**: PyPI keywords need work. Add: "mcp", "model-context-protocol", "code-context", "github-copilot", "claude", "cursor", "ai-context", "code-scanner".
3. **First blog post**: Must be published within 1 week of PyPI launch. Without a narrative, the package sits at 0 downloads.
4. **Timing**: MCP protocol awareness is growing fast (March 2026). CodeTrellis is one of the few tools with a production MCP server. This is the differentiator to lead with.

### ❌ Won't Work

- Nothing blocks this plan from a business perspective.

### 💡 Alternatives

- Lead the README with MCP integration, not "120+ parsers." Users care about "make Copilot/Claude smarter" not parser count.
- Add "Works with: Copilot | Claude | Cursor | Windsurf" badges or logos.

---

## 🟣 AGENT 5: THE DOMAIN EXPERT (CodeTrellis Matrix Expert)

### Verdict: PASS

### ✅ Agreements

- The matrix architecture (scan → compress → inject) is proven with 7,264 tests.
- 120+ parsers covering every major framework is a genuine technical achievement.
- MCP server, JIT context, and cache optimizer are production-ready features.
- Build contracts (H1-H7) and quality gates (G1-G7) show engineering maturity.

### ⚠️ Concerns

1. **Version decision**: The internal version progression was 4.9.0 → 4.16.0 → 5.1.0 → 5.7.0 over 83 sessions. For PyPI launch:
   - `1.0.0` signals "this is the first public release" — clean start
   - `5.0.0` signals "this is mature software" — but may confuse when there's no 1.x-4.x history
   - **Recommendation**: Use `1.0.0` for PyPI. The internal version was never public.
2. **YAML practices files**: The `bpl/practices/*.yaml` files (4,500+ practices) must be included in the wheel. Test with `python -m build && pip install dist/*.whl && python -c "import codetrellis; print(codetrellis.__version__)"`.
3. **`requirements.txt` vs `pyproject.toml`**: The `requirements.txt` lists `tiktoken`, `tree-sitter`, `pyyaml`, `colorama` as separate installs. These should become optional dependency groups in `pyproject.toml`.
4. **Cache paths**: The cache dir pattern `.codetrellis/cache/4.16.0/` includes the version. After switching to `1.0.0`, ensure `codetrellis clean` properly handles old version caches.

### ❌ Won't Work

- Nothing is structurally wrong with the current codebase for packaging.

### 💡 Alternatives

- Add `codetrellis doctor` command to verify installation health (parser availability, optional deps, cache status).
- Include a minimal `conftest.py` stub so third-party plugin developers can test against the public API.

---

## 🟠 AGENT 6: THE SECURITY & RELIABILITY AGENT

### Verdict: CONDITIONAL PASS

### ✅ Agreements

- MIT license is appropriate and properly configured.
- Pure Python with minimal dependencies reduces supply chain risk.
- Tests run across Python 3.9-3.12 — good matrix coverage.
- `twine check` validates package metadata.

### ⚠️ Concerns

1. **No SECURITY.md**: Enterprise security teams look for this. Create a basic responsible disclosure policy.
2. **PyPI Trusted Publishing**: Use OIDC (already partially configured in `release.yml`). Never store PyPI tokens in GitHub secrets if avoidable.
3. **Dependency pinning in CI**: `requirements.txt` has `>=` pins which could break. For CI, consider adding a `constraints.txt` or lockfile.
4. **Test coverage**: 7,264 tests pass but what's the coverage percentage? Add `--cov` flag and set a minimum threshold (e.g., 80%).
5. **Sensitive data in package**: Ensure `.codetrellis/cache/`, `build/`, `*.egg-info`, test fixtures, and docs don't end up in the wheel. Check `MANIFEST.in` or `[tool.setuptools.packages.find]` excludes.

### ❌ Won't Work

1. **The `release.yml` publish-pypi job is incomplete** — the file cuts off after the TestPyPI step. Must complete it before any release.

### 💡 Alternatives

- Add `bandit` or `safety` to CI for security scanning.
- Pin GitHub Actions to SHA hashes instead of tags (`actions/checkout@<sha>`) for supply chain security.
- Add `Dependabot` configuration for automated dependency updates.

---

# ═══════════════════════════════════════════════════════════════

# ROUND 1 SUMMARY TABLE

# ═══════════════════════════════════════════════════════════════

| Agent            | Verdict          | Key Demand                                                             |
| ---------------- | ---------------- | ---------------------------------------------------------------------- |
| 🔴 Skeptic       | CONDITIONAL PASS | Don't over-polish README; verify package excludes test/docs            |
| 🟢 Architect     | PASS             | Include YAML data files; add `py.typed` marker                         |
| 🔵 User Advocate | CONDITIONAL PASS | README must convert in 30 seconds; GIF/screenshot essential            |
| 🟡 Strategist    | PASS             | Lead with MCP + AI integration, not parser count; check PyPI name      |
| 🟣 Domain Expert | PASS             | Use `1.0.0`; structure optional deps properly; verify YAML in wheel    |
| 🟠 Security      | CONDITIONAL PASS | Complete `release.yml`; add SECURITY.md; verify no data leaks in wheel |

### Unanimous Agreements (LOCKED ✅)

1. Fix version numbers before anything else — single version everywhere
2. Publish to PyPI as the highest-leverage action
3. Keep `watchdog` as sole required dependency — everything else optional
4. MIT license is correct
5. CI must trigger automatically on push/tags

### Majority Agreements (4+ agents)

1. Use `1.0.0` as the public version (clean start, no history to confuse)
2. README needs restructuring but not a full rewrite
3. YAML practice files must be verified in the wheel
4. Optional dependency groups should be structured in `pyproject.toml`
5. `release.yml` must be completed

### Disagreements (FLAGGED for Round 2)

1. **README scope**: Skeptic says "edit minimally" vs. User Advocate says "it needs significant restructuring"
2. **SECURITY.md/CODE_OF_CONDUCT.md priority**: Skeptic says skip, Security Agent says required
3. **Version number**: Skeptic suggests `5.0.0` if prior exposure exists vs. Domain Expert recommends `1.0.0`

---

# ═══════════════════════════════════════════════════════════════

# SECTION C: ROUND 2 — CROSS-AGENT DEBATE

# ═══════════════════════════════════════════════════════════════

## DEBATE 1: README Scope

### Skeptic's Position:

The current README has all required content. Move install to the top, add 1 GIF, trim the features table. 2 hours max. "Perfect is the enemy of shipped."

### User Advocate's Rebuttal:

I agree we shouldn't rewrite from scratch. But the current README fails the "30-second test." A user should see: problem → `pip install codetrellis` → `codetrellis scan .` → result. The features table with 50+ rows actively hurts — users see it and think "this is complex."

### Other Agents Weigh In:

- **Strategist**: Lead with MCP integration angle, not features list. The README is a sales page.
- **Architect**: The features table belongs in a separate FEATURES.md.

### 🤝 RESOLUTION:

**Edit (don't rewrite) the README.** Time-box to 3 hours:

1. Move install + quick start to top (above features)
2. Replace 50+ feature table with "Top 5 Features" + link to full [FEATURES.md](docs/FEATURES.md)
3. Add a code block showing before/after (AI without vs with CodeTrellis)
4. Add "Works with: Copilot | Claude | Cursor | Windsurf" section
5. Keep everything else as-is below the fold

---

## DEBATE 2: SECURITY.md / CODE_OF_CONDUCT.md Priority

### Skeptic's Position:

Nobody checks these on a project with 0 stars. Time spent here is time not spent on publishing. Add them later when there are actual users.

### Security Agent's Rebuttal:

Enterprise security teams evaluate OSS projects with checklists. Missing SECURITY.md is a checkmark against adoption. It takes 10 minutes to create from a template.

### Other Agents Weigh In:

- **Strategist**: If the monetization plan targets enterprise (Tier 3), these files matter. Worth 10 minutes now.
- **Domain Expert**: Agree with Security. Templates are copy-paste. No reason to skip.

### 🤝 RESOLUTION:

**Create both files using standard templates.** Budget 15 minutes total. Use:

- SECURITY.md: Standard responsible disclosure template
- CODE_OF_CONDUCT.md: Contributor Covenant v2.1
  The Skeptic accepts this because 15 minutes is negligible.

---

## DEBATE 3: Version Number Choice

### Skeptic's Position:

STATUS.md says v5.7.0. If anyone has seen this (even in screenshots, docs, or conversations), jumping to `1.0.0` looks like a regression. Use `5.0.0`.

### Domain Expert's Rebuttal:

The internal version was never on PyPI or in any public package registry. No external user has ever `pip install`'d any version. STATUS.md is an internal tracking document. `1.0.0` is semantically correct: it's the first public release.

### Other Agents Weigh In:

- **Architect**: `1.0.0` follows semantic versioning correctly. The internal numbering was session-based, not SemVer.
- **Strategist**: `1.0.0` is a stronger marketing signal: "We just launched." `5.0.0` with no prior versions is confusing.
- **User Advocate**: Users seeing `5.0.0` with no download history will be suspicious.

### 🤝 RESOLUTION:

**Use `1.0.0` for the PyPI publication.** The internal version was never public. STATUS.md can note "Internal development versions: v4.x-5.x → Public release: v1.0.0" for context. All agents accept.

---

# ═══════════════════════════════════════════════════════════════

# ROUND 2 CONSENSUS

# ═══════════════════════════════════════════════════════════════

## Architecture Decisions (LOCKED)

| Decision        | Resolution                                          | Agreed By                         |
| --------------- | --------------------------------------------------- | --------------------------------- |
| Version number  | `1.0.0` for public launch                           | All 6 agents                      |
| README approach | Edit existing, time-box 3 hours                     | All 6 agents                      |
| SECURITY.md     | Create from template (15 min)                       | All 6 agents                      |
| Optional deps   | Groups: `ast`, `lsp`, `yaml`, `color`, `all`, `dev` | Architect, Domain Expert, Skeptic |
| CI trigger      | Push + tag-based release                            | All 6 agents                      |

## Must-Have Additions (from Agent Reviews)

1. Verify YAML practice files included in wheel
2. Complete the `release.yml` publish-pypi job
3. Check PyPI name availability immediately
4. Add `py.typed` marker file
5. Verify wheel excludes test files, docs, cache, build artifacts
6. Add more PyPI keywords (mcp, claude, copilot, cursor)
7. Top-5 features in README, full list in FEATURES.md
8. FUNDING.yml for GitHub Sponsors

---

# ═══════════════════════════════════════════════════════════════

# SECTION D: THE PLAN (v2.0 — FINAL VALIDATED)

# ═══════════════════════════════════════════════════════════════

## Plan Name: CodeTrellis PyPI Launch v2.0 (VALIDATED)

## Executive Summary (Updated)

Publish CodeTrellis `1.0.0` to PyPI with a clean, user-focused README, proper version numbers, automated CI/CD, and all trust signals for enterprise evaluation. This is the prerequisite for all monetization paths identified in the analysis.

## Architecture (Updated)

**Version Strategy:**

- Canonical version: `1.0.0` in `pyproject.toml` (single source of truth)
- `__init__.py` reads from `importlib.metadata` or hardcodes `1.0.0`
- All README/docs references updated to `1.0.0`
- STATUS.md gets a note: "Internal dev versions (v4.x-5.x) → Public: v1.0.0"

**Dependency Strategy:**

```toml
[project]
dependencies = ["watchdog>=3.0.0"]

[project.optional-dependencies]
ast = ["tree-sitter>=0.22.0", "tree-sitter-java>=0.23.0", "tree-sitter-python>=0.23.0", "tree-sitter-typescript>=0.23.0"]
yaml = ["pyyaml>=6.0"]
color = ["colorama>=0.4.6"]
tokens = ["tiktoken>=0.5.0"]
all = ["codetrellis[ast,yaml,color,tokens]"]
dev = ["pytest>=8.0.0", "pytest-cov>=4.0.0", "pytest-timeout>=2.3.0", "black>=24.0.0", "ruff>=0.1.0", "mypy>=1.8.0", "numpy>=2.0.0"]
```

**CI/CD Strategy:**

- `ci.yml`: Trigger on push to `main` and PRs
- `release.yml`: Trigger on tag push `v*` → Test → Build → TestPyPI → PyPI

## Implementation Phases (Updated)

### Phase 1: Version & Build Hygiene (Day 1–2)

| Task                                      | Files                                       | Exit Check                                               |
| ----------------------------------------- | ------------------------------------------- | -------------------------------------------------------- |
| Set version to `1.0.0` everywhere         | `pyproject.toml`, `codetrellis/__init__.py` | `grep -r "1.0.0" pyproject.toml codetrellis/__init__.py` |
| Structure optional deps in pyproject.toml | `pyproject.toml`                            | `pip install -e ".[all]"` works                          |
| Add `py.typed` marker                     | `codetrellis/py.typed`                      | File exists                                              |
| Update README version refs                | `README.md`                                 | No old version strings                                   |
| Verify YAML files in wheel                | build + inspect                             | `unzip -l dist/*.whl \| grep yaml` shows practice files  |
| Verify wheel excludes test/docs/cache     | build + inspect                             | `unzip -l dist/*.whl \| grep -c test` = 0                |
| Fix CI triggers                           | `.github/workflows/ci.yml`                  | Push triggers workflow                                   |
| Complete release.yml                      | `.github/workflows/release.yml`             | Full publish-pypi job exists                             |
| Run full test suite                       | -                                           | `pytest tests/ -x -q` → 7,264+ pass                      |

### Phase 2: Documentation & Trust Signals (Day 3–4)

| Task                                                    | Files                 | Exit Check                      |
| ------------------------------------------------------- | --------------------- | ------------------------------- |
| Edit README (top: install, quick start, top-5 features) | `README.md`           | < 3 min to first `pip install`  |
| Move features table to FEATURES.md                      | `docs/FEATURES.md`    | File exists, README links to it |
| Update CHANGELOG for 1.0.0                              | `CHANGELOG.md`        | Entry exists                    |
| Create SECURITY.md                                      | `SECURITY.md`         | File exists                     |
| Create CODE_OF_CONDUCT.md                               | `CODE_OF_CONDUCT.md`  | File exists                     |
| Create FUNDING.yml                                      | `.github/FUNDING.yml` | File exists                     |
| Add PyPI keywords (mcp, claude, copilot)                | `pyproject.toml`      | Keywords present                |
| Review CONTRIBUTING.md                                  | `CONTRIBUTING.md`     | No broken refs                  |

### Phase 3: Publish & Verify (Day 5–7)

| Task                                       | Files               | Exit Check                                                 |
| ------------------------------------------ | ------------------- | ---------------------------------------------------------- |
| Check PyPI name availability               | -                   | `pip install codetrellis` response                         |
| Register PyPI project + Trusted Publishing | PyPI settings       | OIDC configured                                            |
| Publish to TestPyPI                        | CI release          | `pip install -i https://test.pypi.org/simple/ codetrellis` |
| Verify TestPyPI install                    | clean venv          | `codetrellis scan .` works                                 |
| Tag v1.0.0 and push                        | git tag             | Tag exists                                                 |
| Publish to PyPI                            | CI release          | `pip install codetrellis` works                            |
| Final verification in clean env            | fresh machine/venv  | Full scan works                                            |
| Set up GitHub Sponsors                     | github.com/sponsors | Profile active                                             |

## Success Metrics (Outcome-Based)

| Metric                  | Target                              | How Measured              |
| ----------------------- | ----------------------------------- | ------------------------- |
| PyPI install works      | `pip install codetrellis` → success | Fresh venv test           |
| Version consistency     | Single version `1.0.0` in all files | `grep -r` audit           |
| CI passes on push       | Green badge                         | GitHub Actions            |
| Package size            | < 5MB wheel                         | `ls -lh dist/*.whl`       |
| YAML practices in wheel | All `.yaml` files present           | `unzip -l` inspection     |
| No test/docs in wheel   | 0 test/doc files                    | `unzip -l` inspection     |
| PyPI page quality       | Rendered README, classifiers, links | Manual inspection         |
| GitHub Sponsors         | Profile live                        | github.com/sponsors check |

## Risks & Mitigations (Updated)

| Risk                          | Impact                     | Mitigation                          | Owner   |
| ----------------------------- | -------------------------- | ----------------------------------- | ------- |
| PyPI name `codetrellis` taken | High — blocks launch       | Check now; fallback: `code-trellis` | Keshav  |
| YAML files missing from wheel | High — BPL broken          | Test with `unzip -l` before publish | CI gate |
| OIDC Trusted Publishing fails | Low — use API token        | Have API token as backup            | Keshav  |
| Broken install on Python 3.9  | Medium — loses users       | CI tests 3.9-3.12 matrix            | CI gate |
| Version references missed     | Low — looks unprofessional | grep audit as CI step               | CI gate |

## Timeline (Realistic)

- **Day 1–2**: Phase 1 (Version & Build)
- **Day 3–4**: Phase 2 (Documentation)
- **Day 5–7**: Phase 3 (Publish)

## Validation Summary

| Agent            | Final Verdict                          |
| ---------------- | -------------------------------------- |
| 🔴 Skeptic       | PASS — with time-boxing on README      |
| 🟢 Architect     | PASS                                   |
| 🔵 User Advocate | PASS — with 30-second test requirement |
| 🟡 Strategist    | PASS                                   |
| 🟣 Domain Expert | PASS                                   |
| 🟠 Security      | PASS — with release.yml completion     |

**Consensus: 6/6 agents approve.**

---

# ═══════════════════════════════════════════════════════════════

# QUALITY GATES

# ═══════════════════════════════════════════════════════════════

## QG-1: Version Consistency Gate

```bash
# Must return exactly 1 unique version
grep -roh '"1\.0\.0"' pyproject.toml codetrellis/__init__.py | sort -u | wc -l
# Expected: 1
```

## QG-2: Build Integrity Gate

```bash
python3 -m build
twine check dist/*
# Expected: PASSED for both sdist and wheel
```

## QG-3: Wheel Content Gate

```bash
# YAML practices included
unzip -l dist/*.whl | grep -c "\.yaml"
# Expected: > 0

# No test files
unzip -l dist/*.whl | grep -c "/tests/"
# Expected: 0

# No docs
unzip -l dist/*.whl | grep -c "/docs/"
# Expected: 0
```

## QG-4: Install Gate

```bash
python3 -m venv /tmp/ct-test && source /tmp/ct-test/bin/activate
pip install dist/*.whl
python -c "import codetrellis; print(codetrellis.__version__)"
codetrellis --help
deactivate && rm -rf /tmp/ct-test
# Expected: version prints "1.0.0", help shows commands
```

## QG-5: Test Suite Gate

```bash
pytest tests/ -x -q
# Expected: 7264+ passed, 0 failed
```

## QG-6: CI Gate

```bash
# Push to branch, verify CI workflow triggers and passes
# Check: lint ✅, test (3.9-3.12) ✅, package ✅
```

## QG-7: PyPI Publication Gate

```bash
pip install codetrellis
python -c "import codetrellis; print(codetrellis.__version__)"
codetrellis scan /tmp/some-test-project --optimal
# Expected: Installs, imports, scans successfully
```

## QG-8: Documentation Gate

```bash
# All required files exist
for f in README.md CHANGELOG.md CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md LICENSE .github/FUNDING.yml; do
  [ -f "$f" ] && echo "✅ $f" || echo "❌ MISSING: $f"
done
# Expected: All ✅
```
