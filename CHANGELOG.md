# Changelog

All notable changes to CodeTrellis will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2026-04-06

### Added

- **MCP `get_best_practices` tool** — new MCP tool that returns framework/language-specific coding practices on demand. Supports 3 modes: file_path (auto-detects from extension), explicit frameworks list, or project-detected stack. Includes task-type hints (bug_fix, pr_review, feature, security_audit, refactor) for category prioritization.
- **Auto-built practice lookup maps** from centralized configs — replaces hardcoded `_EXT_TO_FRAMEWORKS` with `_ensure_bp_maps()` classmethod that lazily builds 4 maps from `language_config.LANGUAGES` and `PracticeSelector._FRAMEWORK_TO_LANGUAGE`
- **Python dependency extraction** in scanner — parses `requirements*.txt` and `pyproject.toml` (including optional-dependencies) into `matrix.python_dependencies`
- **Full npm dependency capture** — scanner now collects ALL `dependencies` + `devDependencies` from `package.json` (was only 4 hardcoded keys)
- **Django artifact detection** in BPL selector — 8 Django-specific matrix fields (`python_django_models`, `python_django_views`, etc.) now contribute to `python_count` and framework detection

### Fixed

- **Django/Python practices missing in monorepo scans** — 3 bugs fixed: `python_dependencies` never populated, Django artifacts not detected in `from_matrix()`, Django artifacts missing from `python_count`
- **Ruff lint** — removed extraneous f-string prefix in mcp_server.py

### Verified

- **106/106 practice YAMLs** reachable via MCP tool — tested against 24 real public repos (Django, Flask, FastAPI, Express, Angular, Vue, Gin, Fiber, Actix, Axum, Rails, Laravel, Spring Boot, Flutter, Svelte, Ktor, Play, Vapor, Tailwind, and more)

## [1.2.0] - 2026-02-07

### Added

- **Auto-generated prefix→framework map** from YAML practice files via `_build_prefix_framework_map()` — replaces the manually maintained 160-entry `_PREFIX_FRAMEWORK_MAP` with auto-scanning at first use
- **`_FRAMEWORK_TO_LANGUAGE` mapping** (~220 entries): canonical framework→root language lookup used by the auto-builder
- **`_PREFIX_OVERRIDES`** (14 entries): minimal overrides for prefixes whose YAML practices lack `applicability.frameworks`
- **Proportional language allocation** in BPL selector — distributes practice slots fairly across detected languages, preventing frontend practices from crowding out backend in monorepo scans
- **Security practice boost** — security practices receive a guaranteed allocation floor regardless of language distribution
- **CLI language grouping** — `--include-practices` output now groups practices by language (e.g., `## PYTHON (5)`, `## TYPESCRIPT (3)`)
- **Framework fallback resolution** — unknown prefixes (e.g., SPRING, FLUTTER) resolve via `applicability.frameworks` → `_FRAMEWORK_TO_LANGUAGE` lookup
- **Canonical prefix matching** — CHARTJS→javascript, XSTATE→javascript (fixes incorrect resolution to typescript)
- **CSS ecosystem fixes** — LESS/SASS/PCSS correctly resolve to css; Bootstrap mapped to css instead of javascript
- 22 new unit tests for proportional allocation, language derivation, security detection, and framework fallback

### Changed

- Updated integration docs (CHECKLIST.md, GUIDE.md) to reflect v6.0 auto-build architecture

### Removed

- `_PREFIX_FRAMEWORK_MAP` class attribute (replaced by auto-built map from YAML + `_PREFIX_OVERRIDES`)

## [1.0.0] - 2026-03-14

### 🎉 First Public Release

First public PyPI release. Consolidates 83 internal development sessions.

### Highlights

- 120+ language and framework parsers
- MCP server for AI context injection
- JIT context engine for file-level queries
- Best Practices Library with 4,500+ practices
- Build contracts and quality gates
- Support for Python, TypeScript, Go, Rust, Java, C#, and 100+ more
- Works with GitHub Copilot, Claude, Cursor, and Windsurf

### Internal History

Developed through sessions 1–83 (versions 4.9.0–5.7.0 internally).
See STATUS.md for detailed session history.

## [4.16.0] - 2026-01-31

### Added

- MCP server for AI context injection (`codetrellis mcp`)
- JIT context engine for file-level queries (`codetrellis context --file`)
- AI skills generation from matrix (`codetrellis skills`)
- Matrix embeddings support for semantic search
- JSON-LD matrix export for structured data
- Matrix diff for incremental change detection
- Matrix navigator for interactive exploration
- MatrixBench scorer for quality benchmarking
- Plugin system with discovery and management (`codetrellis plugins`)
- Distributed matrix generation across component folders
- Interactive onboarding guide (`codetrellis onboard`)
- Progress tracking with TODOs and blockers (`codetrellis progress`)
- Cross-language type resolution
- Cache optimizer for build performance
- Parallel extraction with async support
- 80+ language/framework parsers including:
  - Web: React, Vue, Svelte, Angular, Astro, Lit, Alpine.js, HTMX
  - Backend: FastAPI, Flask, Django, Express, Fastify, Hono, Koa, Hapi, Litestar
  - Systems: Go, Rust, C, C++, Zig
  - JVM: Java, Kotlin, Scala (with Spring Boot, Hibernate, Jakarta EE)
  - .NET: C#, ASP.NET Core, Entity Framework, Dapper, MassTransit, Hangfire
  - Mobile: Swift, Dart/Flutter, React Native
  - Data: SQL, Prisma, tRPC, GraphQL
  - Styling: CSS, SCSS, Less, Tailwind, Emotion, Styled Components, Chakra UI
  - Config: YAML, TOML, Dockerfile, Terraform, Nginx
  - Other: Lua, Bash, R, Perl, Zig, Solidity

### Changed

- Build contract system with advanced validation (D1)
- Compression levels from L0 (raw) to L5 (ultra)
- Semantic extraction for routes, APIs, and business domain
- File classification with confidence scoring
- Init integrations for Copilot, Cursor, Windsurf, and Claude

### Fixed

- Phase 1: Test reliability — eliminated flaky tests, fixed 6,775 test baseline
- Phase 2: Technical debt — centralized error handling, structured error codes
- Phase 3: Parser quality — robust fallback paths, graceful degradation
- Phase 4: DX improvements — help text, error messages, documentation

## [4.15.0]

### Added

- Initial public release
- Project scanning with `codetrellis scan`
- Matrix compression pipeline
- CLI interface with scan, show, prompt, watch commands
- Python, JavaScript, TypeScript parser support

---

[1.0.0]: https://github.com/chaudhary-keshav/codetrellis-matrix/releases/tag/v1.0.0
[4.16.0]: https://github.com/chaudhary-keshav/codetrellis-matrix/compare/v4.15.0...v4.16.0
[4.15.0]: https://github.com/chaudhary-keshav/codetrellis-matrix/releases/tag/v4.15.0
