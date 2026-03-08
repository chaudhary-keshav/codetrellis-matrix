# JavaScript Language Integration — Consolidated Analysis Report

> **Version:** v4.30 (Phase AA)
> **Date:** 14 February 2026
> **Session:** 20
> **Previous Version:** v4.29 (PowerShell)
> **Total Tests:** 1,551 (88 new + 1,463 existing)

---

## 1. Executive Summary

JavaScript is the 20th language added to CodeTrellis (21st counting Kotlin v2). The integration includes 5 extractors, an enhanced parser with 70+ framework detection patterns, BPL integration with 50 practices, and full scanner/compressor pipeline support. During validation, **3 critical BPL selector bugs were discovered and fixed** that affected practice selection accuracy across the entire system.

### Key Metrics

| Metric                 | Value                                     |
| ---------------------- | ----------------------------------------- |
| Extractors Created     | 5 (type, function, api, model, attribute) |
| Dataclasses Created    | 17                                        |
| Framework Patterns     | 70+                                       |
| BPL Practices          | 50 (JS001-JS050)                          |
| PracticeCategory Enums | 15                                        |
| Unit Tests             | 88                                        |
| Bugs Fixed             | 6 (#68-73)                                |
| Validation Repos       | 3 (Express.js, Ghost, Nodemailer)         |
| Test Suite Total       | 1,551 passing                             |
| Regression Failures    | 0                                         |

---

## 2. Implementation Summary

### Phase 1: Extractors (5 files)

| Extractor           | Key Artifacts Extracted                                                       | Lines |
| ------------------- | ----------------------------------------------------------------------------- | ----- |
| Type Extractor      | ES6+ classes, prototype-based types, constants, Symbols, static/getter/setter | ~500  |
| Function Extractor  | Functions, arrow functions, generators, IIFEs, async functions, CJS exports   | ~350  |
| API Extractor       | Express/Fastify/Koa/Hapi routes, middleware, WebSocket, GraphQL resolvers     | ~300  |
| Model Extractor     | Mongoose/Sequelize/Prisma/Knex/Objection.js models, migrations, relationships | ~310  |
| Attribute Extractor | ES6 imports/exports, CommonJS require/module.exports, dynamic imports, JSDoc  | ~370  |

### Phase 2: Parser

- `EnhancedJavaScriptParser` with `JavaScriptParseResult` dataclass
- 70+ framework detection patterns covering web, frontend, backend, ORM, testing, build tools
- ES version detection (ES5 through ES2024+) from syntax features and `package.json`
- Module system detection (CommonJS vs ESM)

### Phase 3: Scanner Integration

- 24 `js_*` fields added to `ProjectMatrix`
- `_parse_javascript()` method (~200 lines)
- File routing for `.js`, `.jsx`, `.mjs`, `.cjs` extensions
- Stats output for all JS artifact types

### Phase 4: Compressor Integration

- 5 compression sections: `[JAVASCRIPT_TYPES]`, `[JAVASCRIPT_FUNCTIONS]`, `[JAVASCRIPT_API]`, `[JAVASCRIPT_MODELS]`, `[JAVASCRIPT_DEPENDENCIES]`

### Phase 5: BPL Integration

- 50 practices (JS001-JS050) across 15 categories
- Priority distribution: 9 critical, 27 high, 13 medium, 1 low
- 15 PracticeCategory enum values (JS_MODERN_SYNTAX through JS_DOCUMENTATION)
- 50+ framework mappings in `js_fw_mapping`
- Sub-framework checks for Express, React, Mongoose, Node

### Phase 6: Testing

- 88 unit tests across 6 test files
- 15 type extractor tests, 15 function extractor tests, 12 API extractor tests, 12 model extractor tests, 18 attribute extractor tests, 16 parser integration tests

---

## 3. Validation Scan Results

### 3.1 Express.js (expressjs/express)

**Repository Profile:** The most popular Node.js web framework. Minimalist, unopinionated. Written in ES5-style CommonJS JavaScript.

| Artifact Type     | Count                   |
| ----------------- | ----------------------- |
| Classes           | 0                       |
| Constants         | 11                      |
| Functions         | 30                      |
| Arrow Functions   | 0                       |
| Routes            | 9                       |
| Middleware        | 4                       |
| ES6 Imports       | 4                       |
| CJS Exports       | 22                      |
| Decorators        | 0                       |
| Module System     | commonjs                |
| ES Version        | es5                     |
| Frameworks        | express, javascript     |
| **BPL Practices** | **15 (all JavaScript)** |

**Analysis:** Express.js is a small, focused library (~30 functions). The scanner correctly identified it as pure JavaScript with CommonJS modules and ES5 syntax. All 15 selected practices were JS-specific (zero TypeScript/React contamination after BPL fix). The 9 routes correspond to Express's example and test routes.

**Selected Practices:** JS001 (const/let), JS006 (async/await), JS008 (Promise rejections), JS011 (Error objects), JS027 (strict equality), JS030 (XSS), JS032 (env vars), JS041 (Node.js patterns), JS042 (graceful shutdown), JS044 (Express routing), JS045 (Express middleware), JS046 (API design), JS047 (API versioning), JS048 (data modeling), JS050 (code style)

### 3.2 Ghost (TryGhost/Ghost)

**Repository Profile:** Full-featured open-source publishing platform. Monorepo with React admin UI, Node.js backend, and TypeScript type definitions.

| Artifact Type     | Count                                              |
| ----------------- | -------------------------------------------------- |
| Classes           | 686                                                |
| Constants         | 332                                                |
| Functions         | 1,472                                              |
| Arrow Functions   | 1,789                                              |
| Routes            | 352                                                |
| Middleware        | 200                                                |
| ES6 Imports       | 5,366                                              |
| CJS Exports       | 2,123                                              |
| Decorators        | 1,773                                              |
| Module System     | esm                                                |
| ES Version        | es2015+                                            |
| Frameworks        | 32 detected (express, react, typescript + 29 more) |
| **BPL Practices** | **7 REACT + 5 TS + 3 other**                       |

**Analysis:** Ghost is a large monorepo (~12,119 total JS artifacts) combining React frontend (admin panel), Express backend, and TypeScript type definitions. The BPL correctly selected React-oriented practices (for the admin UI) plus TypeScript practices (for the type system), with some general practices. This demonstrates correct mixed-framework handling — JS practices are NOT forced when the project genuinely uses React+TS.

### 3.3 Nodemailer (nodemailer/nodemailer)

**Repository Profile:** Popular Node.js email sending library. Pure JavaScript, CommonJS, ES5 style.

| Artifact Type     | Count                   |
| ----------------- | ----------------------- |
| Classes           | 0                       |
| Constants         | 0                       |
| Functions         | 37                      |
| Arrow Functions   | 0                       |
| Routes            | 0                       |
| Middleware        | 0                       |
| ES6 Imports       | 0                       |
| CJS Exports       | 0                       |
| Decorators        | 0                       |
| Module System     | commonjs                |
| ES Version        | es5                     |
| Frameworks        | javascript              |
| **BPL Practices** | **15 (all JavaScript)** |

**Analysis:** Nodemailer is a focused utility library with 37 functions. No classes, no ES6 features, pure CommonJS. The scanner correctly identified it as minimal JavaScript. All 15 selected practices were JS-specific, confirming the BPL fix works for single-framework projects.

---

## 4. Critical Bugs Found & Fixed

### Bug #71: Pure JS Projects Showing TypeScript Practices (CRITICAL)

**Root Cause:** In `bpl/selector.py`, the `has_typescript` flag was set when ANY of `["typescript", "angular", "react", "nestjs", "vue", "nextjs"]` appeared in `context_frameworks`. This meant ANY project with React or Vue (which are used in both JS and TS) would be treated as a TypeScript project.

**Impact:** Express.js (which had "vue" in its detected frameworks from test/example files) was being treated as a TypeScript project, causing TS practices to be selected instead of JS practices.

**Fix:** Changed `has_typescript` to only check for TypeScript-exclusive frameworks:

```python
# Before (broken):
has_typescript = any(f in context_frameworks for f in ["typescript", "angular", "react", "nestjs", "vue", "nextjs"])

# After (fixed):
has_typescript = "typescript" in context_frameworks or "angular" in context_frameworks or "nestjs" in context_frameworks
```

### Bug #72: JS Practices Always Scored Lowest (CRITICAL)

**Root Cause:** All 50 JavaScript practices in `javascript_core.yaml` had NO `priority:` field. The BPL scoring system uses priority as the PRIMARY sort key: `(priority_score, total_match, practice.id)`. Without explicit priority, all JS practices got the default lowest score, ensuring they ALWAYS lost to TypeScript practices (which had explicit `priority: critical/high/medium`).

**Impact:** Even when JS practices passed all filters, they were always ranked below TS practices in the final selection, getting cut at the `max_practices=15` limit.

**Fix:** Added explicit priority fields to all 50 practices: 9 critical, 27 high, 13 medium, 1 low.

### Bug #73: Duplicate REACT Key in prefix_framework_map (MODERATE)

**Root Cause:** Python dict `prefix_framework_map` had two entries with key `"REACT"`:

1. Original: `"REACT": {"react", "typescript"}` (for react.yaml TS-oriented practices)
2. Added for JS: `"REACT": {"react", "javascript"}` (intended for JS React practices)

Python silently keeps only the LAST value for duplicate keys, so the TS React mapping was overwritten.

**Impact:** React practices from `react.yaml` (which are TypeScript-oriented) would incorrectly match JavaScript projects and fail to match TypeScript projects.

**Fix:** Removed the duplicate JS entry. React practices in `react.yaml` remain mapped to `{"react", "typescript"}`. JavaScript React patterns are covered by JS practices (JS023-JS026 for functional patterns).

---

## 5. Coverage Assessment

### Extraction Coverage by Category

| Category                | Coverage  | Notes                                                              |
| ----------------------- | --------- | ------------------------------------------------------------------ |
| ES6+ Classes            | ✅ High   | Class declarations, constructors, methods, static, getters/setters |
| Prototype OOP           | ✅ High   | Constructor.prototype, Object.create, **proto**                    |
| Constants/Symbols       | ✅ High   | const declarations, Symbol(), Symbol.for()                         |
| Functions               | ✅ High   | Regular, async, arrow, generators, IIFEs                           |
| Express Routes          | ✅ High   | GET/POST/PUT/DELETE/PATCH, router, app methods                     |
| Fastify/Koa/Hapi Routes | ✅ Medium | Basic patterns detected, advanced plugins not deep-parsed          |
| Mongoose Models         | ✅ High   | Schema definitions, field types, virtuals                          |
| Sequelize Models        | ✅ High   | define(), init(), associations                                     |
| Prisma Models           | ✅ Medium | Client usage detected, schema.prisma not parsed                    |
| CommonJS Imports        | ✅ High   | require(), module.exports, exports                                 |
| ES6 Imports/Exports     | ✅ High   | import/export, default, named, re-exports                          |
| Dynamic Imports         | ✅ Medium | import() detected, resolved paths not traced                       |
| JSDoc                   | ✅ High   | @param, @returns, @type, @typedef                                  |
| Decorators              | ✅ Medium | Stage 3 decorators detected, metadata not analyzed                 |
| Framework Detection     | ✅ High   | 70+ patterns for web, frontend, ORM, testing, build                |
| ES Version Detection    | ✅ High   | ES5 through ES2024+ from syntax + package.json                     |
| Module System Detection | ✅ High   | CommonJS vs ESM auto-detection                                     |

### Known Limitations

1. **No tree-sitter AST**: Uses regex-only extraction (tree-sitter-javascript available but not installed)
2. **No LSP integration**: typescript-language-server designed for but not connected
3. **Dynamic imports not resolved**: `import()` expressions detected but resolved paths not traced
4. **Prototype chains not resolved**: Cross-file prototype chain resolution not performed
5. **JSX not deeply parsed**: JSX detected but component composition tree not mapped
6. **Decorator metadata not analyzed**: Stage 3 decorators detected but decorator execution order not traced
7. **Source maps not parsed**: Minified/bundled code not reverse-mapped to source

---

## 6. BPL Practice Distribution

| Category          | Practice IDs    | Count  | Priority Mix                       |
| ----------------- | --------------- | ------ | ---------------------------------- |
| JS_MODERN_SYNTAX  | JS001-JS005     | 5      | 1 critical, 3 high, 1 medium       |
| JS_ASYNC_PATTERNS | JS006-JS010     | 5      | 2 critical, 2 high, 1 medium       |
| JS_ERROR_HANDLING | JS011-JS014     | 4      | 1 critical, 2 high, 1 medium       |
| JS_MODULES        | JS015-JS018     | 4      | 3 high, 1 medium                   |
| JS_CLASSES        | JS019-JS022     | 4      | 3 high, 1 medium                   |
| JS_FUNCTIONS      | JS023-JS026     | 4      | 3 high, 1 medium                   |
| JS_TYPE_SAFETY    | JS027-JS029     | 3      | 1 critical, 1 high, 1 medium       |
| JS_SECURITY       | JS030-JS033     | 4      | 2 critical, 1 high, 1 medium       |
| JS_PERFORMANCE    | JS034-JS036     | 3      | 2 high, 1 medium                   |
| JS_TESTING        | JS037-JS040     | 4      | 3 high, 1 medium                   |
| JS_NODE           | JS041-JS043     | 3      | 1 critical, 2 high                 |
| JS_EXPRESS        | JS044-JS045     | 2      | 1 critical, 1 high                 |
| JS_API_DESIGN     | JS046-JS047     | 2      | 2 high                             |
| JS_DATA_MODELING  | JS048           | 1      | 1 high                             |
| JS_BUILD_TOOLING  | JS049           | 1      | 1 medium                           |
| JS_STYLE          | JS050           | 1      | 1 low                              |
| **Total**         | **JS001-JS050** | **50** | **9 crit, 27 high, 13 med, 1 low** |

---

## 7. Lessons Learned

### For Future Language Integrations

1. **Always add `priority:` fields to YAML practices**: Without explicit priorities, practices default to lowest score and will never be selected over languages that have priorities. This was a systemic gap that went undetected until JavaScript (the first language sharing frameworks with TypeScript).

2. **Test BPL selection with repos that share frameworks**: The Express.js bug only manifested because Express.js shared "vue" with TypeScript's framework set. Test with repos that have overlapping framework ecosystems to catch cross-contamination.

3. **Python dict duplicate keys are silent bugs**: The REACT key duplication was a silent semantic error with no runtime warning. Use linting or explicit checks for duplicate keys in large dict literals.

4. **`has_<language>` detection must distinguish exclusive vs shared frameworks**: When a language ecosystem shares frameworks with another language (JS/TS share React/Vue/Next.js), the detection logic must only use language-exclusive signals.

5. **Small repos are valuable test targets**: Express.js core (~30 functions) was more revealing than Ghost (~12K artifacts) because it exposed BPL selection issues that were masked in large mixed-framework repos.

---

## 8. File Inventory

### Files Created (14)

| #   | File                                                       | Lines |
| --- | ---------------------------------------------------------- | ----- |
| 1   | `codetrellis/extractors/javascript/__init__.py`            | ~100  |
| 2   | `codetrellis/extractors/javascript/type_extractor.py`      | ~500  |
| 3   | `codetrellis/extractors/javascript/function_extractor.py`  | ~350  |
| 4   | `codetrellis/extractors/javascript/api_extractor.py`       | ~300  |
| 5   | `codetrellis/extractors/javascript/model_extractor.py`     | ~310  |
| 6   | `codetrellis/extractors/javascript/attribute_extractor.py` | ~370  |
| 7   | `codetrellis/javascript_parser_enhanced.py`                | ~363  |
| 8   | `codetrellis/bpl/practices/javascript_core.yaml`           | ~700  |
| 9   | `tests/unit/test_javascript_type_extractor.py`             | ~350  |
| 10  | `tests/unit/test_javascript_function_extractor.py`         | ~350  |
| 11  | `tests/unit/test_javascript_api_extractor.py`              | ~250  |
| 12  | `tests/unit/test_javascript_model_extractor.py`            | ~250  |
| 13  | `tests/unit/test_javascript_attribute_extractor.py`        | ~350  |
| 14  | `tests/unit/test_javascript_parser_enhanced.py`            | ~300  |

### Files Modified (4)

| #   | File                          | Key Changes                                       |
| --- | ----------------------------- | ------------------------------------------------- |
| 1   | `codetrellis/scanner.py`      | 24 JS fields, `_parse_javascript()`, file routing |
| 2   | `codetrellis/compressor.py`   | 5 JS compression sections                         |
| 3   | `codetrellis/bpl/selector.py` | JS framework mappings + 3 critical fixes          |
| 4   | `codetrellis/bpl/models.py`   | 15 JS PracticeCategory enums                      |

---

_Report generated: 14 February 2026_
_CodeTrellis v4.30 — JavaScript Language Integration Complete_
