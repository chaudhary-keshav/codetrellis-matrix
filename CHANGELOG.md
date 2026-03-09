# Changelog

All notable changes to CodeTrellis will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
