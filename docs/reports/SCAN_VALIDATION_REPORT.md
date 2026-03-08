# CodeTrellis v4.9 — Multi-Repository Scan Validation Report

## Methodology

For each repository:

1. Run `codetrellis scan <repo> --optimal` to generate matrix.prompt
2. Manually deep-analyze the codebase (read key files, trace architecture)
3. Compare scanner output against manual findings across 15 evaluation categories
4. Score coverage per category (0–100%)
5. Classify gaps as: MISSING, PARTIAL, GOOD, EXCELLENT

---

## Repository 1: gotify/server

**Profile**: Go web server (66% Go, 32% TypeScript) with embedded React UI, REST API, WebSocket streaming, GORM ORM, plugin system, multi-DB support (SQLite/MySQL/Postgres), Gin framework, 14.6k stars, 116 Go files + 63 TS files.

**Scan Output**: 771 lines | ~23,345 tokens

### Category-by-Category Analysis

---

### 1. PROJECT OVERVIEW — Score: 70/100 ⚠️ PARTIAL

**Scanner says**: `name:gotify-server|type:Go Web Service|stack:Go Web Service`
**Dirs**: `ui(56),plugin(21),api(12),model(9),database(7),auth(5)`
**Patterns**: `websocket`

**What's missing**:

- ❌ **Stack should include**: "Go + React/TypeScript + Gin + GORM + WebSocket + MobX" — currently just "Go Web Service"
- ❌ **Multi-DB support** not mentioned (SQLite3, MySQL, PostgreSQL)
- ❌ **Plugin system** not called out as architectural pattern
- ⚠️ Dirs are correct but `test(1)` is misleading — test/ has testdb/ subdirectory with multiple files
- ✅ WebSocket pattern correctly detected

**Root cause**: Overview extractor generates generic stack label, doesn't analyze go.mod imports to infer framework stack. Doesn't look at `ui/package.json` for frontend stack.

---

### 2. ROUTES / API SURFACE — Score: 55/100 ⚠️ PARTIAL

**Scanner detected (GO_API section)**:

```
GET:/              GET:/index.html       GET:/manifest.json
GET:/static/*any   GET:/echo             GET:/swagger
GET:/docs          GET:/plugin           GET:/:id/config
POST:/:id/config   GET:/:id/display      POST:/:id/enable
POST:/:id/disable  OPTIONS:/*any         GET:version
POST:/:id/image    DELETE:/:id/image     PUT:/:id
DELETE:/:id         GET:/stream          GET:current/user
POST:current/user/password              GET:/:id
POST:/:id
```

**What's ACTUALLY in router.go (my manual count = 31 routes)**:

```
GET:/health                     ← MISSING (uses g.Match not g.GET)
GET:/swagger                    ✅
GET:/docs                       ✅
GET:/image/*                    ← MISSING (StaticFS)
GET:/plugin                     ✅
GET:/plugin/:id/config          ✅ (partial path)
POST:/plugin/:id/config         ✅ (partial path)
GET:/plugin/:id/display         ✅ (partial path)
POST:/plugin/:id/enable         ✅ (partial path)
POST:/plugin/:id/disable        ✅ (partial path)
POST:/user                      ← MISSING
OPTIONS:/*any                   ✅
GET:/version                    ✅
POST:/message                   ← MISSING (different group)
GET:/application                ← path shows as empty
POST:/application               ← path shows as empty
POST:/application/:id/image     ← MISSING full path
DELETE:/application/:id/image   ← MISSING full path
PUT:/application/:id            ← MISSING full path
DELETE:/application/:id         ← MISSING full path
GET:/application/:id/message    ← MISSING full path
DELETE:/application/:id/message ← MISSING full path
GET:/client                     ← path shows as empty
POST:/client                    ← path shows as empty
DELETE:/client/:id              ← MISSING full path
PUT:/client/:id                 ← MISSING full path
GET:/message                    ← path shows as empty
DELETE:/message                 ← path shows as empty
DELETE:/message/:id             ← MISSING full path
GET:/stream                     ✅
GET:/current/user               ✅ (but missing leading /)
POST:/current/user/password     ✅ (but missing leading /)
GET:/user (admin)               ← correctly detected
DELETE:/user/:id                ← MISSING
GET:/user/:id                   ✅
POST:/user/:id                  ✅
```

**Critical gaps**:

- ❌ `g.Match([]string{"GET", "HEAD"}, "/health", ...)` — `g.Match()` not recognized
- ❌ `g.StaticFS("/image", ...)` — StaticFS not recognized as route
- ❌ Group-prefixed routes lose their prefix: `/application`, `/client`, `/message` groups → routes show as `/:id`, not `/application/:id`
- ❌ `g.Group("/").Use(...).POST("/message", ...)` — group with "/" prefix loses the message path
- ❌ Auth middleware not shown per-route (which routes are admin-only vs client-only vs app-token)
- ⚠️ No swagger spec integration — docs/spec.json has 44 API endpoints fully documented but scanner ignores it

**Root cause**: Cross-file prefix resolution (Fix #4) works for function calls but NOT for inline `g.Group(prefix)` within the same file. The scanner resolves `.Group("/application")` but the routes under it show without the group prefix. Also `g.Match()` and `g.StaticFS()` are not recognized.

---

### 3. MIDDLEWARE — Score: 65/100 ⚠️ PARTIAL

**Scanner detected**:

```
generic:  func(ctx *gin.Context) — socket IP mapping
logging:  gin.LoggerWithFormatter, 2x func(ctx *gin.Context) — SSL redirect + response headers
auth:     cors.New(...), authentication.RequireClient(), authentication.RequireAdmin()
```

**What's ACTUALLY there (from router.go)**:

1. ✅ Socket IP normalization middleware
2. ✅ Logger with formatter + Recovery + error handler + location
3. ⚠️ SSL redirect (detected as "logging" — miscategorized)
4. ✅ Response headers middleware
5. ✅ CORS middleware
6. ✅ RequireClient() auth
7. ✅ RequireAdmin() auth
8. ❌ **MISSING**: RequireApplicationToken() — used for message creation
9. ❌ **MISSING**: Optional() auth — used for user registration

**Root cause**: Middleware categorization is heuristic-based. `RequireApplicationToken` and `Optional()` are auth middleware used inline on specific groups but not detected by the middleware extractor.

---

### 4. AUTHENTICATION / SECURITY MODEL — Score: 40/100 ❌ WEAK

**Scanner says**: Nothing in particular about auth model — just the middleware names.

**What's ACTUALLY there**:

- **3 auth levels**: Admin, Client, ApplicationToken — each with different permissions
- **Token sources**: X-Gotify-Key header, Bearer token, query param `?token=`, Basic Auth
- **Custom header**: `X-Gotify-Key`
- **Password**: bcrypt with configurable strength
- **CORS**: configurable per-origin with regex support
- **WebSocket origin**: separate CORS-like config for WS connections
- **Security contacts**: gotify@protonmail.com (from SECURITY.md)
- **swagger.json**: Documents full auth scheme with clientToken, appToken, basicAuth

**What scanner captures**: Only the middleware names (`RequireAdmin`, `RequireClient`). Zero understanding of the actual security model.

**Root cause**: No security-model extractor exists. Auth patterns (header extraction, token validation, bcrypt) could be generically detected.

---

### 5. DATABASE / ORM — Score: 45/100 ❌ WEAK

**Scanner says**: Shows `GormDatabase` struct and 40 methods. Shows GORM dependency. But nothing about:

**What's ACTUALLY there**:

- ❌ **3 database dialects**: SQLite3, MySQL, PostgreSQL — NOT documented
- ❌ **AutoMigrate models**: User, Application, Message, Client, PluginConf — NOT listed
- ❌ **Connection pooling**: MaxOpenConns=10 (1 for SQLite), ConnMaxLifetime=9min for MySQL — NOT captured
- ❌ **Migration strategy**: GORM AutoMigrate + custom `fillMissingSortKeys` — NOT documented
- ❌ **Transaction usage**: `db.Transaction(fillMissingSortKeys, &sql.TxOptions{Isolation: sql.LevelSerializable})` — NOT captured
- ❌ **Default user creation**: Creates admin/admin on first run — NOT documented
- ✅ GormDatabase methods correctly extracted
- ✅ Model structs with GORM tags extracted

**Root cause**: No database-config extractor. GORM `AutoMigrate`, `gorm.Open(dialect)`, connection pool settings are standard patterns that could be generically detected.

---

### 6. CONFIGURATION — Score: 35/100 ❌ WEAK

**Scanner says**: 4 env vars (GOTIFY_EXE, GOTIFY_SERVER_PORT, NODE_ENV, PUBLIC_URL — all from UI test setup).

**What's ACTUALLY there**:

- ❌ **GOTIFY\_ env prefix** — configor loads from env with `ENVPrefix: "GOTIFY"` — means ALL config fields can be set via `GOTIFY_SERVER_PORT`, `GOTIFY_DATABASE_DIALECT`, etc.
- ❌ **config.yml** — primary configuration method, with 30+ settings
- ❌ **config.example.yml** — 3.2KB comprehensive example — NOT extracted
- ❌ **Configuration struct** — 30+ nested fields with defaults — NOT surfaced as config
- ❌ **Config sources**: config.yml file + /etc/gotify/config.yml + GOTIFY\_\* env vars
- ✅ 4 env vars detected from source (but these are test-time vars, not the real config)

**Root cause**: The scanner extracts env vars from source code patterns but doesn't understand Go config libraries (`configor`, `viper`, `envconfig`). It doesn't parse `config.example.yml` or `.yml` config templates. The Configuration struct is extracted as a Go type but not flagged as "this IS the project's configuration schema."

---

### 7. ENVIRONMENT VARIABLES — Score: 30/100 ❌ WEAK

Overlaps with #6. The 4 detected env vars are from UI test files, not production config.

**Real production env vars** (via GOTIFY\_ prefix): GOTIFY_SERVER_PORT, GOTIFY_SERVER_LISTENADDR, GOTIFY_DATABASE_DIALECT, GOTIFY_DATABASE_CONNECTION, GOTIFY_DEFAULTUSER_NAME, GOTIFY_DEFAULTUSER_PASS, GOTIFY_PASSSTRENGTH, GOTIFY_UPLOADEDIMAGESDIR, GOTIFY_PLUGINSDIR, GOTIFY_REGISTRATION, GOTIFY_SERVER_SSL_ENABLED, GOTIFY_SERVER_SSL_PORT, etc.

**Root cause**: `configor` uses a naming convention (ENVPrefix + struct field path) to derive env var names. This is a common Go pattern. Scanner doesn't understand it.

---

### 8. CI/CD — Score: 70/100 ⚠️ PARTIAL

**Scanner says**: `ci:github-actions|triggers:push,pull_request|jobs:gotify`

**What's ACTUALLY there**:

- ✅ Trigger detection correct
- ✅ Job name correct
- ❌ **Build steps not documented**: go test, golangci-lint, swagger check, codecov, Docker build+push, release upload
- ❌ **Release process**: Tag-triggered → LD_FLAGS → cross-compile → Docker multiarch → GitHub releases — NOT captured
- ❌ **Makefile targets**: build, test, check, format, build-docker, package-zip — only partially captured (in Runbook commands section, good)
- ⚠️ Makefile commands ARE captured well in RUNBOOK section

**Root cause**: CI/CD extractor captures workflow name/trigger/job but not step details or release pipeline logic.

---

### 9. TESTING — Score: 50/100 ⚠️ PARTIAL

**Scanner says**: Nothing explicit about testing patterns.

**What's ACTUALLY there**:

- 30+ `_test.go` files across all packages
- Test utilities in `test/` package (testdb, auth helpers, asserts)
- `test/testdb/database.go` — shared test database setup
- `--race` flag used in CI
- `coverprofile` coverage in CI
- JS tests via `yarn test` with custom GOTIFY_EXE setup
- `leaktest` for goroutine leak detection
- `stretchr/testify` for assertions

**What scanner captures**: Shows test dependencies (testify, leaktest). `test/` dir visible in structure but file count is wrong (shows 1 file but has 10+).

**Root cause**: Test file counting uses glob that doesn't recurse into subdirectories properly. No test-pattern extractor to identify testing strategies, helpers, or utilities.

---

### 10. FRONTEND / UI — Score: 25/100 ❌ WEAK

**Scanner says**: `ui(56)` in dir counts. Frontend TS files are NOT extracted (no TypeScript extractor in use for this project). One error-handling mention from `AppStore.ts`.

**What's ACTUALLY there**:

- React 19 + MobX + Material UI (MUI) + React Router
- Vite bundler
- WebSocket integration (WebSocketStore.ts)
- Plugin management UI
- Message management UI
- User management UI
- Application management UI
- Client management UI
- Drag-and-drop sorting (@dnd-kit)
- CodeMirror editor integration
- Markdown rendering

**Root cause**: No TypeScript/React extraction happens because `tsconfig.json` is in `ui/` subdirectory, not root. LSP extraction requires Node.js and a root tsconfig. The scanner detects it's a Go project and doesn't deep-analyze the embedded frontend.

---

### 11. WEBSOCKET — Score: 60/100 ⚠️ PARTIAL

**Scanner says**: `patterns:websocket` in overview. WebSocket functions visible in `stream.go` logic (API.Handle, API.Notify, client.startReading, etc.).

**What's missing**:

- ❌ WebSocket message format (sends model.MessageExternal as JSON)
- ❌ Ping/pong protocol (configurable intervals)
- ❌ Origin validation logic
- ❌ Connection lifecycle (upgrade → register → read/write goroutines → remove)
- ✅ Functions and their flow logic are captured

---

### 12. BUSINESS DOMAIN — Score: 20/100 ❌ WEAK

**Scanner says**: `domain:Developer Tools` — **WRONG**

**What it ACTUALLY is**: Push notification service. Self-hosted message server with REST API for sending and WebSocket for receiving notifications. Has applications (senders), clients (receivers), messages, plugins.

**Root cause**: Business domain extractor uses heuristics that misclassify this as "Developer Tools" because of build/test infrastructure presence. Should detect from README keywords: "sending and receiving messages", "notifications", "push".

---

### 13. PLUGIN SYSTEM — Score: 55/100 ⚠️ PARTIAL

**Scanner captures**: Plugin struct, Manager, PluginInstance interface, PluginV1 compatibility, example plugins (echo, clock, minimal). Plugin API methods. Plugin database methods.

**What's missing**:

- ❌ Plugin architecture not explicitly documented: load from directory → wrap → versioned interface → per-user instances
- ❌ Plugin capabilities system (Messenger, Configurer, Storager, Webhooker, Displayer)
- ❌ Plugin lifecycle (load → initialize per user → enable/disable → webhook registration)
- ❌ plugin-api v1 interface contract

---

### 14. SWAGGER / API DOCUMENTATION — Score: 5/100 ❌ MISSING

**Scanner says**: Shows `GET:/swagger` and `GET:/docs` as routes.

**What's ACTUALLY there**: Full Swagger 2.0 spec in `docs/spec.json` with:

- 44 API endpoints fully documented
- Request/response schemas
- Authentication schemes (3 types)
- Error response formats
- Model definitions

**Root cause**: No swagger/OpenAPI spec extractor exists. This is a gold mine of structured API information that the scanner completely ignores.

---

### 15. DEPENDENCIES — Score: 80/100 ✅ GOOD

**Scanner captures**: 20 direct dependencies correctly categorized as [web], [db], [auth], [testing], [other].

**What's missing**:

- ⚠️ `github.com/jinzhu/configor` should be tagged as [config] — it's the config loading library
- ⚠️ `github.com/gorilla/websocket` should be tagged as [websocket] not [other]
- ✅ Overall dependency extraction is good

---

### OVERALL GOTIFY/SERVER SCORE: 47/100

| Category            | Score   | Status     |
| ------------------- | ------- | ---------- |
| 1. Overview         | 70%     | ⚠️ PARTIAL |
| 2. Routes           | 55%     | ⚠️ PARTIAL |
| 3. Middleware       | 65%     | ⚠️ PARTIAL |
| 4. Auth/Security    | 40%     | ❌ WEAK    |
| 5. Database/ORM     | 45%     | ❌ WEAK    |
| 6. Configuration    | 35%     | ❌ WEAK    |
| 7. Env Vars         | 30%     | ❌ WEAK    |
| 8. CI/CD            | 70%     | ⚠️ PARTIAL |
| 9. Testing          | 50%     | ⚠️ PARTIAL |
| 10. Frontend/UI     | 25%     | ❌ WEAK    |
| 11. WebSocket       | 60%     | ⚠️ PARTIAL |
| 12. Business Domain | 20%     | ❌ WEAK    |
| 13. Plugin System   | 55%     | ⚠️ PARTIAL |
| 14. Swagger/OpenAPI | 5%      | ❌ MISSING |
| 15. Dependencies    | 80%     | ✅ GOOD    |
| **AVERAGE**         | **47%** |            |

---

## Key Findings — Generic Gaps (not gotify-specific)

### GAP-1: Same-file group prefix resolution broken

**Severity**: HIGH
**Affects**: Any Go project using Gin, Echo, Chi with `g.Group("/prefix")`
**Fix**: The cross-file resolution (Fix #4) resolved function-call prefixes, but inline `clientAuth.Group("/application")` within the same router file doesn't propagate prefixes to child routes.

### GAP-2: `g.Match()`, `g.StaticFS()`, `g.Static()` not recognized as routes

**Severity**: MEDIUM
**Affects**: Any Go project using Gin
**Fix**: Add patterns for `g.Match()`, `g.StaticFS()`, `g.Static()` in api_extractor.

### GAP-3: No OpenAPI/Swagger spec extraction

**Severity**: HIGH
**Affects**: Any project with swagger.json, openapi.yaml, spec.json
**Fix**: Add SwaggerExtractor that parses OpenAPI 2.0/3.0 specs → extracts endpoints, models, auth schemes.

### GAP-4: No config-file template extraction (YAML/TOML/INI)

**Severity**: HIGH
**Affects**: Any Go/Python/Node project with config.example.yml, .env.example, etc.
**Fix**: Add config template parser that extracts structured config fields with defaults and comments.

### GAP-5: Go config library env var inference

**Severity**: MEDIUM
**Affects**: Any Go project using configor/viper/envconfig with ENVPrefix
**Fix**: Detect `configor.New(&configor.Config{ENVPrefix: "X"})` → infer all env vars from struct fields.

### GAP-6: Business domain misclassification

**Severity**: MEDIUM
**Affects**: All projects — domain extractor is too heuristic-based
**Fix**: Weight README.md content more heavily. Look for keywords in first 500 chars of README.

### GAP-7: Database dialect/migration not extracted

**Severity**: MEDIUM
**Affects**: Any Go project using GORM, sqlx, database/sql
**Fix**: Detect `gorm.Open(dialect)`, `AutoMigrate(models...)`, connection pool config.

### GAP-8: Frontend stack in embedded UIs not analyzed

**Severity**: MEDIUM
**Affects**: Monorepo or embedded-frontend Go projects
**Fix**: Detect `ui/package.json` or `frontend/package.json` and extract key deps for overview.

### GAP-9: Auth model not extracted

**Severity**: HIGH
**Affects**: Any web service with authentication
**Fix**: Detect auth patterns: token extraction from headers/query, bcrypt, JWT, session management.

---

## Repository 2: photoprism/photoprism

**Profile**: AI-Powered Photos App (39.2k stars). Go backend + Vue 3 frontend + TensorFlow/ONNX ML pipeline. Gin framework, GORM ORM (MySQL/MariaDB/SQLite), WebDAV, WebSocket, face recognition, image classification, NSFW detection, OIDC/OAuth2, ACL-based RBAC (10 roles), cluster mode, 2249 Go files + 94 Vue files + 171 JS files.

**Scan Output**: 4183 lines | ~125,000 tokens

### Category-by-Category Analysis

---

### 1. PROJECT OVERVIEW — Score: 40/100 ❌ WEAK

**Scanner says**: `name:photoprism|type:Go Web Service|stack:Go Web Service`
**Dirs**: `internal(1033),pkg(347),frontend(168),scripts(6),docker(3),assets(2)`

**What's missing**:

- ❌ **Stack should include**: "Go + Vue 3 + Vuetify + Gin + GORM + TensorFlow + WebDAV + WebSocket + OIDC + Cluster" — just says "Go Web Service"
- ❌ **AI/ML stack completely invisible**: TensorFlow, ONNX, face detection, classification, NSFW detection — none mentioned in overview
- ❌ **Vue 3 + Vuetify frontend** not mentioned (it's in `frontend/package.json`)
- ❌ **WebDAV server** not mentioned as a core capability
- ❌ **Multi-DB** (MySQL/MariaDB/SQLite with PostgreSQL planned) not shown
- ❌ **Cluster mode** not shown (cluster/portal/node architecture)
- ⚠️ Dir counts reasonable but `assets(2)` is misleading — assets has 1995 files total

**Root cause**: Same as gotify — overview extractor generates generic "Go Web Service", doesn't inspect go.mod for ML libraries, doesn't check frontend/package.json for UI framework.

---

### 2. ROUTES / API SURFACE — Score: 75/100 ⚠️ PARTIAL

**Scanner detected**: 156 HTTP routes in GO_API section

**What's ACTUALLY there (manual count)**:

- 157 routes registered in `internal/api/` via individual handler files (scanner got 156 — nearly perfect!)
- ~27 additional non-API routes in `internal/server/` package:
  - ❌ Health endpoints: `router.Any("/livez")`, `router.Any("/health")`, `router.Any("/healthz")`, `router.Any("/readyz")` — NOT detected
  - ❌ Well-known endpoints: `/.well-known/oauth-authorization-server`, `/.well-known/openid-configuration`, `/.well-known/jwks.json` — NOT detected
  - ❌ WebDAV mounts: `router.Group("/originals")`, `router.Group("/import")` with PROPFIND/MKCOL/COPY/MOVE methods — NOT detected
  - ❌ Sharing routes: `router.Group("/s")` → ShareToken, ShareTokenShared, SharePreview — NOT detected
  - ❌ Static/UI routes: `/robots.txt`, `/_rainbow`, `/_splash`, manifest — NOT detected
  - ❌ WebApp routes: `conf.LibraryUri("/*path")` — NOT detected

**Critical gaps**:

- ❌ `router.Any()` — not recognized as a multi-method route registration
- ❌ `router.Handle(MethodPropfind, ...)` — WebDAV methods (PROPFIND, MKCOL, COPY, MOVE, LOCK, UNLOCK, PROPPATCH) not recognized
- ❌ Routes registered on `router` (engine-level) vs `APIv1` (group-level) — engine-level routes are invisible
- ❌ `conf.BaseUri(path)` — dynamic path prefix not resolved (all routes use configurable base URI)
- ✅ API routes (the main 157) are nearly perfectly extracted — excellent work on the individual handler pattern

**Root cause**: Scanner focuses on `router.GET/POST/PUT/DELETE/PATCH` patterns on RouterGroup. Routes registered on `gin.Engine` via `router.Any()` or `router.Handle()` are not detected. Also `conf.BaseUri()` produces a dynamic prefix that the scanner can't resolve.

---

### 3. MIDDLEWARE — Score: 60/100 ⚠️ PARTIAL

**Scanner detected**: 4 middleware: Recovery(), Logger(), gzip.Gzip(), Security(conf)

**What's ACTUALLY there**:

1. ✅ `Recovery()` — panic recovery
2. ✅ `Logger()` — request logging (conditional on debug mode — condition NOT captured)
3. ✅ `gzip.Gzip(gzip.DefaultCompression)` — compression
4. ✅ `Security(conf)` — security headers
5. ❌ **MISSING**: `APIMiddleware(conf)` — applied to the entire APIv1 group (auth, session, rate limiting)
6. ❌ **MISSING**: `WebDAVAuth(conf)` — WebDAV authentication middleware
7. ❌ **MISSING**: Rate limiter (`server/limiter` package) — per-endpoint rate limiting
8. ❌ **MISSING**: Conditional middleware — Logger only applied when `conf.Debug()` is true

**Root cause**: Middleware detection looks for `router.Use()` calls but doesn't detect middleware applied via `router.Group(path, middleware)` syntax (second argument to Group is middleware). `APIMiddleware` is passed as argument to `router.Group()`, not via `.Use()`.

---

### 4. AUTHENTICATION / SECURITY MODEL — Score: 25/100 ❌ WEAK

**Scanner says**: Nothing explicit about auth model. OAuth/OIDC route functions are listed but not analyzed for security semantics.

**What's ACTUALLY there**:

- **10 ACL roles**: default, admin, user, viewer, guest, visitor, app, service, portal, client
- **ACL system**: Resource → Role → Permission matrix (`auth/acl/` package)
- **Auth methods**: Password, OIDC (OpenID Connect), OAuth2, API tokens, passkeys/passcodes
- **OAuth2 endpoints**: /oauth/authorize, /oauth/token, /oauth/revoke, /oauth/userinfo
- **OIDC endpoints**: /oidc/login, /oidc/redirect
- **JWT**: Full JWT issuer/verifier with JWKS endpoint for cluster verification
- **Session management**: Server-side sessions with configurable maxage/timeout/cache
- **Passkeys/2FA**: Passcode creation, confirmation, activation, deactivation
- **Rate limiting**: Per-endpoint via `server/limiter` package
- **Security headers**: Custom Security middleware
- **CORS**: Configurable origin, headers, methods
- **Trusted proxies**: X-Forwarded-For, custom client header support

**What scanner captures**: Route names (CreateSession, OAuthAuthorize, OIDCLogin, etc.) but zero understanding of security model, role hierarchy, or auth flow.

**Root cause**: Same as gotify — no security-model extractor. But the gap is even more severe here due to the sophisticated multi-method auth system.

---

### 5. DATABASE / ORM — Score: 40/100 ❌ WEAK

**Scanner says**: Shows entity structs with JSON tags. Shows GORM as dependency. But no database architecture.

**What's ACTUALLY there**:

- ❌ **34+ database entity models**: User, Password, Passcode, Session, Client, Service, Photo, PhotoUser, Album, AlbumUser, PhotoAlbum, Label, Category, PhotoLabel, File, FileShare, FileSync, Place, Cell, Camera, Lens, Country, Keyword, PhotoKeyword, Link, Subject, Face, Marker, Reaction, UserShare, UserDetails, UserSettings, Folder, Duplicate, Details — NOT enumerated as DB models
- ❌ **3 database dialects**: MySQL/MariaDB, SQLite3 (PostgreSQL planned) — NOT documented
- ❌ **Migration system**: `entity/migrate` package with versioned migrations, auto-migrate, deprecated table dropping — NOT captured
- ❌ **Connection settings**: From config flags: DatabaseConns, DatabaseConnsIdle, DatabaseTimeout, DatabaseSsl — NOT extracted
- ❌ **Test database**: Full test DB initialization with fixtures and index regeneration — NOT captured
- ❌ **Entity cache system**: FlushCaches() with per-entity caches (Album, Camera, Lens, Country, Label, Session) — NOT captured
- ⚠️ Entity struct fields ARE extracted with JSON tags — good for API comprehension
- ✅ GORM dependency detected

**Root cause**: Scanner extracts structs but doesn't identify which are ORM entities (AutoMigrate list). Doesn't detect `gorm.Open()`, connection pool config, or migration patterns.

---

### 6. CONFIGURATION — Score: 20/100 ❌ WEAK

**Scanner says**: 5 env vars from frontend JS (CHROME_BIN, CUSTOM_NAME, CUSTOM_SRC, GETTEXT_MERGE, SRC)

**What's ACTUALLY there**:

- ❌ **217 configuration flags** defined in `internal/config/flags.go` using `urfave/cli/v2`
- ❌ **PHOTOPRISM\_ env prefix**: ALL flags exposed as `PHOTOPRISM_*` env vars (via `clean.EnvVar()`)
- ❌ **Config categories**: Auth (18 flags), OIDC (13 flags), Session (3), Logging (6), Database (12), Storage (20+), AI/ML (15+), HTTP (10+), Cluster (15+), Backup (5+), etc.
- ❌ **options.yml**: YAML config file support via `OptionsYaml()` + `DefaultsYaml()`
- ❌ **Settings**: Runtime settings in `customize.Settings` stored in DB
- ❌ **Config struct**: 950-line config.go with 300+ methods — NOT recognized as config system
- ✅ Some Makefile-exported vars detected (GO111MODULE, NPM_CONFIG_IGNORE_SCRIPTS)

**Root cause**: Scanner doesn't understand `urfave/cli/v2` flag pattern (`&cli.StringFlag{Name: "x", EnvVars: EnvVars("Y")}`). Doesn't detect `EnvVars()` helper function that converts flag names to PHOTOPRISM\_\* env vars. This is a massive miss — 217 production env vars vs 5 detected.

---

### 7. ENVIRONMENT VARIABLES — Score: 10/100 ❌ MISSING

**Scanner detected**: 5 env vars from frontend JavaScript files only.

**What's ACTUALLY there**: 217+ production env vars all prefixed with `PHOTOPRISM_`:

- PHOTOPRISM_AUTH_MODE, PHOTOPRISM_AUTH_SECRET
- PHOTOPRISM_ADMIN_USER, PHOTOPRISM_ADMIN_PASSWORD
- PHOTOPRISM_DATABASE_DRIVER, PHOTOPRISM_DATABASE_DSN, PHOTOPRISM_DATABASE_SERVER
- PHOTOPRISM_SITE_URL, PHOTOPRISM_SITE_TITLE, PHOTOPRISM_SITE_CAPTION
- PHOTOPRISM_OIDC_URI, PHOTOPRISM_OIDC_CLIENT, PHOTOPRISM_OIDC_SECRET
- PHOTOPRISM_UPLOAD_NSFW, PHOTOPRISM_DETECT_NSFW
- PHOTOPRISM_DISABLE_TENSORFLOW, PHOTOPRISM_DISABLE_FACES
- PHOTOPRISM_HTTP_PORT, PHOTOPRISM_HTTP_HOST, PHOTOPRISM_HTTP_COMPRESSION
- ... 200+ more

**Root cause**: The `urfave/cli` + `EnvVars()` helper pattern is completely invisible to the scanner. This is the single biggest coverage gap — 97.7% of env vars are missed.

---

### 8. CI/CD — Score: 65/100 ⚠️ PARTIAL

**Scanner says**: `ci:github-actions|triggers:push|jobs:analyze` — detects CodeQL analysis workflow.

**What's ACTUALLY there**:

- ✅ GitHub Actions (CodeQL) detected
- ❌ **Makefile-driven build system** is the primary CI/CD — `make build`, `make test`, `make release` — make targets ARE in RUNBOOK section (12 commands captured, decent)
- ❌ **Docker multi-arch builds**: 20+ Dockerfiles across `docker/` subdirs (demo, develop, photoprism, tensorflow, goproxy variants for multiple distros) — only 1 Dockerfile extracted
- ❌ **Docker Compose**: demo/compose.yaml with 4 services (demo, traefik, scheduler, watchtower) — scanner found a different compose file with 8 services
- ❌ **Versioning system**: Semver from .semver file, `SEMVER_MAJOR.SEMVER_MINOR.SEMVER_PATCH`, git describe — NOT captured
- ❌ **Cross-compilation**: ARM, AMD64 builds — NOT captured
- ⚠️ Makefile commands in RUNBOOK are useful but miss testing targets (test-api, test-entity, test-pkg, test-ai, etc.)

**Root cause**: CI/CD extractor focuses on `.github/workflows/` but this project's CI is primarily Makefile-driven with docker. Many Makefile targets are captured but categorization is limited.

---

### 9. TESTING — Score: 45/100 ❌ WEAK

**Scanner says**: Testing dependencies detected. No explicit test analysis.

**What's ACTUALLY there**:

- **927 test files** (`*_test.go`) — massive test suite
- Test categories: unit, integration, acceptance (TestCafe with Chromium)
- Makefile targets: test-go, test-js, test-api, test-entity, test-pkg, test-ai, test-hub, test-video, acceptance-run-chromium
- Test databases: SQLite test DB with fixtures
- Acceptance tests: Browser-based with TestCafe, sqlite/mariadb variants
- Frontend tests: vitest with coverage
- Vulnerability scanning: `govulncheck` for Go deps
- Race detection: `-race` flag
- Security scanning: npm audit, v-html detection

**What scanner captures**: None of the test strategy. Shows `vitest` in frontend scripts.

**Root cause**: No test-strategy extractor. This project has one of the most comprehensive test suites (927 test files) but the scanner provides zero insight into testing patterns.

---

### 10. FRONTEND / UI — Score: 20/100 ❌ WEAK

**Scanner says**: `frontend(168)` in dir count. No frontend stack analysis.

**What's ACTUALLY there**:

- **Vue 3** with `@vitejs/plugin-vue`
- **Vuetify 3** (Material Design)
- **Vue Router 4** (SPA routing)
- **Axios** (HTTP client)
- **Luxon** (date/time)
- **Sockette** (WebSocket client)
- **webpack** (bundler, not Vite despite Vite test plugin)
- **vue-gettext** (i18n/translations)
- **@mdi/font** (Material Design Icons)
- **TestCafe** (E2E testing)
- **vitest** (unit testing)
- **ESLint + Prettier** (code quality)
- Frontend scripts: build, test, watch, lint, gettext-extract/compile, security scans

**What scanner captures**: Frontend dir count. Nothing about Vue/Vuetify stack.

**Root cause**: Same as gotify — `frontend/package.json` is in a subdirectory, not root. No automatic detection of embedded frontend stacks.

---

### 11. WEBSOCKET — Score: 50/100 ⚠️ PARTIAL

**Scanner says**: `GET:/ws|func` route detected. gorilla/websocket visible in dependencies.

**What's ACTUALLY there**:

- ❌ **WebSocket implementation** in `internal/api/websocket.go`: Full upgrader with CheckOrigin, auth per connection, user→session mapping, ping/pong, timeout management (wsTimeout = 90s)
- ❌ **Event system**: WebSocket used for real-time event broadcast to connected clients
- ❌ **Auth per WS connection**: `wsAuth` maps connection IDs to users and sessions
- ✅ Route `/ws` detected
- ✅ gorilla/websocket dependency detected

**Root cause**: Scanner detects the route and dependency but doesn't analyze the WebSocket handler's implementation for connection lifecycle, auth, or message protocol.

---

### 12. BUSINESS DOMAIN — Score: 15/100 ❌ WEAK

**Scanner says**: `domain:General Application` — **CRITICALLY WRONG**

**What it ACTUALLY is**: AI-Powered Photos App. Self-hosted photo/video management platform with:

- Photo/video indexing and browsing
- Face recognition and people tagging
- Image classification (labels, categories)
- NSFW detection
- Geographic mapping (places, cells, countries)
- Album management
- Sharing via links
- WebDAV file access
- Computer vision API endpoints
- Cluster mode for multi-node deployments
- OIDC/OAuth2 for enterprise SSO

The `frontend/package.json` literally says `"description": "AI-Powered Photos App"`.

**Root cause**: Domain extractor doesn't check package.json description field, doesn't weight README content for domain keywords. "AI-Powered Photos App" is the literal description but scanner says "General Application".

---

### 13. AI/ML PIPELINE — Score: 30/100 ❌ WEAK (NEW CATEGORY for photoprism)

**Scanner says**: No explicit AI/ML section. Some AI-related functions visible in IMPLEMENTATION_LOGIC.

**What's ACTUALLY there**:

- **TensorFlow integration**: `internal/ai/tensorflow/` — model loading, inference
- **Face detection/recognition**: `internal/ai/face/` — cascade detection, embeddings, clustering (face detection, face recognition, face clustering with configurable distances/scores)
- **Image classification**: `internal/ai/classify/` — label classification with rules engine
- **NSFW detection**: `internal/ai/nsfw/` — content safety
- **Computer Vision API**: `internal/ai/vision/` with Ollama and OpenAI backends, schema definitions
- **Vision API endpoints**: POST /vision/labels, POST /vision/nsfw, POST /vision/face, POST /vision/caption
- **ML config**: FaceEngine, FaceSize, FaceScore, FaceOverlap, VisionApi, VisionUri, VisionKey, NasnetModelPath, FacenetModelPath, NsfwModelPath
- **ONNX runtime**: dependency for alternative inference

**Root cause**: No AI/ML extractor exists. The scanner doesn't identify TensorFlow/ONNX model loading, inference patterns, or ML pipeline architecture.

---

### 14. SWAGGER / API DOCUMENTATION — Score: 10/100 ❌ MISSING

**Scanner says**: Some `@Router`, `@Summary`, `@Tags` Swagger annotations are visible in function comments (detected by implementation logic extractor).

**What's ACTUALLY there**:

- Swagger 2.0 annotations (`@Router /api/v1/session [post]`, `@Summary create a session`, `@Tags Authentication`) on many API handlers
- Auto-generated swagger spec (registerAPIDocs function pointer)
- `.well-known` service discovery endpoints for OAuth2/OIDC

**What scanner captures**: Swagger comment annotations are visible inline with function signatures but not parsed or structured.

**Root cause**: Same as gotify — no swagger/OpenAPI spec extractor. But here the annotations are in source code, making them potentially extractable even without a spec file.

---

### 15. DEPENDENCIES — Score: 75/100 ⚠️ PARTIAL

**Scanner captures**: Go dependencies listed in GO_DEPENDENCIES section.

**What's missing**:

- ⚠️ No categorization of ML-specific deps (tensorflow, onnxruntime)
- ⚠️ Frontend deps from `frontend/package.json` not analyzed
- ⚠️ No version conflict or security analysis
- ✅ Go module dependencies correctly extracted

---

### 16. CLUSTER / DISTRIBUTED SYSTEM — Score: 20/100 ❌ WEAK (NEW CATEGORY for photoprism)

**Scanner says**: Cluster routes visible (ClusterGetTheme, ClusterNodesRegister, ClusterListNodes, etc.)

**What's ACTUALLY there**:

- **Cluster mode**: Portal → Node architecture with registration, provisioning, metrics
- **JWT-based inter-node auth**: JWKS endpoint, cluster-scoped JWT tokens
- **Node roles**: Portal (primary) and Node (worker) with separate config paths
- **Cluster API**: 8 endpoints for node registration, management, metrics, health, theme
- **Service discovery**: Well-known endpoints for OAuth/OIDC across cluster
- **Database provisioning**: Cluster can provision database credentials to joining nodes
- **Health checks**: /livez, /health, /healthz, /readyz endpoints

**Root cause**: Scanner captures the route names but doesn't understand the distributed system architecture pattern.

---

### OVERALL PHOTOPRISM SCORE: 37/100

| Category                | Score   | Status     |
| ----------------------- | ------- | ---------- |
| 1. Overview             | 40%     | ❌ WEAK    |
| 2. Routes               | 75%     | ⚠️ PARTIAL |
| 3. Middleware           | 60%     | ⚠️ PARTIAL |
| 4. Auth/Security        | 25%     | ❌ WEAK    |
| 5. Database/ORM         | 40%     | ❌ WEAK    |
| 6. Configuration        | 20%     | ❌ WEAK    |
| 7. Env Vars             | 10%     | ❌ MISSING |
| 8. CI/CD                | 65%     | ⚠️ PARTIAL |
| 9. Testing              | 45%     | ❌ WEAK    |
| 10. Frontend/UI         | 20%     | ❌ WEAK    |
| 11. WebSocket           | 50%     | ⚠️ PARTIAL |
| 12. Business Domain     | 15%     | ❌ WEAK    |
| 13. AI/ML Pipeline      | 30%     | ❌ WEAK    |
| 14. Swagger/API Docs    | 10%     | ❌ MISSING |
| 15. Dependencies        | 75%     | ⚠️ PARTIAL |
| 16. Cluster/Distributed | 20%     | ❌ WEAK    |
| **AVERAGE**             | **37%** |            |

---

### New Generic Gaps from photoprism (adding to gotify findings)

### GAP-10: `router.Any()` not recognized as route registration

**Severity**: HIGH
**Affects**: Any Gin project using `router.Any(path, handler)` for health checks, well-known endpoints
**Fix**: Add `router.Any()` pattern to api_extractor — emits as ALL methods or as a special "ANY" method.

### GAP-11: `router.Handle(method, path, handler)` not recognized

**Severity**: MEDIUM
**Affects**: Any Gin project using custom HTTP methods (WebDAV: PROPFIND, MKCOL, COPY, MOVE, LOCK, UNLOCK)
**Fix**: Add `router.Handle()` pattern extraction.

### GAP-12: Engine-level vs Group-level route registration

**Severity**: HIGH
**Affects**: Projects that register routes on both `gin.Engine` and `gin.RouterGroup` — engine-level routes invisible
**Fix**: Scanner currently only follows routes registered on RouterGroup variables. Need to also detect routes on the engine itself (`router.GET(...)` where router is `*gin.Engine`).

### GAP-13: Middleware passed as Group() argument not detected

**Severity**: MEDIUM
**Affects**: Any Gin project using `router.Group(path, middleware1, middleware2)` pattern
**Fix**: Detect middleware in Group() call's second+ arguments, not just `.Use()` calls.

### GAP-14: `urfave/cli` flag → env var pattern not detected

**Severity**: HIGH
**Affects**: Many Go CLI applications using urfave/cli for config (very popular library)
**Fix**: Detect `&cli.StringFlag{..., EnvVars: EnvVars("X")}` pattern → extract env var names. Also detect helper functions like `EnvVar(flag) → PREFIX + flag`.

### GAP-15: AI/ML pipeline not extracted

**Severity**: MEDIUM
**Affects**: Go/Python projects with ML inference (TensorFlow, PyTorch, ONNX)
**Fix**: Detect model loading patterns, inference functions, ML config fields. Surface as a dedicated section.

### GAP-16: Frontend package.json description not used for domain classification

**Severity**: LOW
**Affects**: All projects with package.json
**Fix**: Read `description` field from package.json(s) and use as strong signal for business domain.

### GAP-17: Swagger annotations in source code not parsed

**Severity**: MEDIUM
**Affects**: Go projects using swaggo/swag annotations (`@Router`, `@Summary`, `@Tags`)
**Fix**: Parse `// @Router /path [method]` comments to build structured route documentation.

### GAP-18: Dynamic path prefix functions not resolved

**Severity**: LOW
**Affects**: Projects using `conf.BaseUri(path)` or similar config-driven path prefixes
**Fix**: Detect common patterns like `conf.BaseUri()`, `config.Prefix +`, etc. Document that routes use configurable prefixes.

## Repository 3: caddyserver/caddy

**Profile**: Fast, multi-platform web server with automatic HTTPS (61.5k stars). Pure Go, config-driven architecture (Caddyfile + JSON API), pluggable module system (124+ modules via `caddy.RegisterModule()`), net/http-based (no framework), admin API with mux routing, automatic TLS via certmagic/Let's Encrypt, 291 Go files, 79 test files.

**Scan Output**: 1741 lines | ~52,000 tokens

### Architecture Difference

Caddy is architecturally distinct from gotify and photoprism:

- **No web framework** (no Gin/Echo/Chi) — uses `net/http` stdlib mux
- **No traditional routes** — HTTP serving is config-driven (Caddyfile or JSON), not code-defined
- **Module/plugin system** — 124+ modules registered via `caddy.RegisterModule()` in init() blocks
- **Admin API only** — the admin API (config CRUD, debug/pprof) uses `mux.Handle(pattern, handler)` — not a framework router
- **Config-as-code** — routes, middleware, matchers, handlers are all JSON config, not Go code

This tests the scanner against a fundamentally different pattern.

### Category-by-Category Analysis

---

### 1. PROJECT OVERVIEW — Score: 45/100 ❌ WEAK

**Scanner says**: `name:caddy|type:Go Web Service|stack:Go Web Service`
**Dirs**: `modules(146),caddyconfig(22),cmd(11),internal(8),notify(3),caddytest(1)`

**What's missing**:

- ❌ **Not a "Go Web Service"** — it's a **web server / reverse proxy / load balancer** with automatic HTTPS
- ❌ **Module system** not highlighted — 124+ registered modules (the core architectural pattern)
- ❌ **Caddyfile** config format not mentioned
- ❌ **Auto-HTTPS / Let's Encrypt** not mentioned (Caddy's signature feature)
- ❌ **Admin API** not mentioned
- ✅ Dir counts are reasonable

**Root cause**: Overview extractor defaults to "Go Web Service" for any Go project with `net/http`. Doesn't detect web server / reverse proxy patterns. Doesn't identify `caddy.RegisterModule()` as a module registration pattern.

---

### 2. ROUTES / API SURFACE — Score: 5/100 ❌ MISSING

**Scanner detected**: 1 route: `GET::protocol|anonymous`

**What's ACTUALLY there**:

- **Admin API routes** (registered via `mux.Handle()` in admin.go):
  - `/config/` → Config CRUD (GET/POST/PUT/PATCH/DELETE)
  - `/id/` → Config by ID
  - `/stop` → Graceful shutdown
  - `/debug/pprof/` → Profiling (6 endpoints)
  - `/debug/vars` → Expvar
  - `/pki/ca/:id` → CA info (from caddypki module)
  - `/pki/ca/:id/certificates` → CA certs (from caddypki module)
  - Dynamic routes from `admin.api` module namespace

**Critical gap**: 0% of admin API routes detected. The scanner looks for Gin/Echo/Chi/Gorilla patterns but Caddy uses stdlib `mux.Handle(pattern, handler)`. This is a **complete blindspot** for non-framework Go projects.

**Root cause**: The Go API extractor only recognizes framework-specific patterns (`.GET()`, `.POST()`, `.Handle()` on router groups). It doesn't detect `http.ServeMux.Handle()` or `mux.Handle()` patterns.

---

### 3. MIDDLEWARE — Score: 5/100 ❌ MISSING

**Scanner detected**: 4 "generic middleware" — all false positives (actually cobra command registrations)

**What's ACTUALLY there**:

- **HTTP Middleware modules** (registered as caddy modules, configured via JSON/Caddyfile):
  - `encode` — gzip, brotli, zstd compression
  - `headers` — response header manipulation
  - `rewrite` — URL rewriting
  - `reverse_proxy` — reverse proxy with load balancing (9+ selection policies)
  - `tracing` — OpenTelemetry tracing
  - `intercept` — response interception
  - `templates` — template rendering
  - `file_server` — static file serving
  - `subroute` — sub-routing
  - `proxyprotocol` — PROXY protocol listener
- **Matchers**: MatchRemoteIP, MatchClientIP, VarsMatcher, MatchVarsRE, CEL matchers
- **All middleware is config-driven**, not code-defined

**Root cause**: Scanner detects middleware via `router.Use()` or function wrapping patterns. Caddy's middleware is registered as modules and composed via JSON config — a completely different pattern.

---

### 4. AUTHENTICATION / SECURITY MODEL — Score: 20/100 ❌ WEAK

**Scanner says**: Nothing about auth.

**What's ACTUALLY there**:

- **Admin API auth**: Mutual TLS (mTLS) for admin endpoint, configurable listen address
- **Auto-HTTPS**: Automatic TLS certificate provisioning via Let's Encrypt/ACME
- **certmagic**: Full ACME client for certificate management
- **TLS modules**: `caddytls` with configurable connection policies, client auth, OCSP stapling
- **Admin identity**: Admin endpoint identity verification
- **HTTP auth modules**: Basic auth, forward auth (via plugins)

**Root cause**: No auth-pattern extractor. Auto-HTTPS/ACME is a unique security model that the scanner doesn't recognize.

---

### 5. CONFIGURATION — Score: 30/100 ❌ WEAK

**Scanner says**: 13 env vars detected from source (CADDY*ADMIN, HOME, XDG*\*, NO_COLOR, TERM, USERAGENT, LISTEN_FDNAMES)

**What's ACTUALLY there**:

- ✅ **Source env vars well detected** — 13 env vars from `os.Getenv()`/`os.LookupEnv()` calls are correctly captured
- ❌ **Caddyfile** — Caddy's primary config format (DSL-based) — NOT mentioned
- ❌ **JSON config API** — Admin API accepts JSON config at runtime — NOT documented
- ❌ **Config adapters** — Caddyfile, nginx, TOML adapters — NOT detected
- ❌ **Config struct** — `caddy.Config` with Admin, Logging, Storage, Apps — NOT flagged as config
- ❌ **Runtime config management** — Load, run, stop, adapt config at runtime — NOT captured

**Root cause**: Scanner doesn't understand config-adapter patterns or runtime config APIs. Env vars from Go source are actually well-detected for this project (unlike the urfave/cli pattern in photoprism).

---

### 6. ENVIRONMENT VARIABLES — Score: 70/100 ⚠️ PARTIAL

**Scanner detected**: 13 env vars (CADDY_ADMIN, HOME, HOMEDRIVE, HOMEPATH, LISTEN_FDNAMES, NOTIFY_SOCKET, NO_COLOR, TERM, USERAGENT, USERPROFILE, XDG_CACHE_HOME, XDG_CONFIG_HOME, XDG_DATA_HOME)

**What's actually there**: Scanner captured most of them well. Only missing:

- ⚠️ `{env.*}` placeholder system — Caddy can reference ANY env var via `{env.VAR_NAME}` in Caddyfile/config, but this is a runtime pattern, hard to statically detect
- ⚠️ `AppData` (Windows) env var missed

**Assessment**: This is actually one of the BEST env var extractions across all 3 repos. The `os.Getenv()` pattern works well for Caddy because it uses direct env var access, not a config library.

---

### 7. CI/CD — Score: 75/100 ⚠️ PARTIAL

**Scanner says**: 7 GitHub Actions workflows detected with triggers and job names.

**What's ACTUALLY there**:

- ✅ CI workflows well-detected (ci.yml, lint.yml, cross-build.yml, release.yml, etc.)
- ✅ Triggers (push, pull_request, release, workflow_dispatch) correctly captured
- ❌ **GoReleaser** for release builds — NOT captured
- ❌ **Cross-build** (multi-platform) — NOT detailed
- ❌ **Scorecard** security analysis — NOT highlighted
- ⚠️ No Makefile analysis (no Makefile in Caddy? Actually there isn't one — command-based)

**Assessment**: Good CI/CD detection. Better than gotify and photoprism because more workflows are captured.

---

### 8. BUSINESS DOMAIN — Score: 20/100 ❌ WEAK

**Scanner says**: `domain:Developer Tools` — **WRONG**

**What it ACTUALLY is**: Web Server / Reverse Proxy / Load Balancer with automatic HTTPS. The README literally says: "Caddy is a powerful, extensible platform to serve your sites, services, and apps."

**Root cause**: Same pattern as gotify and photoprism — domain extractor misclassifies projects with build/infrastructure code.

---

### 9. MODULE/PLUGIN SYSTEM — Score: 15/100 ❌ WEAK

**Scanner says**: Shows some module types (App, Config) but not the module system itself.

**What's ACTUALLY there**:

- **124+ registered modules** via `caddy.RegisterModule()` in init() blocks
- **Module namespaces**: http.handlers._, http.matchers._, tls._, storage._, logging.\*, etc.
- **Module lifecycle**: New() → Provision() → Validate() → Start() → Cleanup()
- **Module interface**: `caddy.Module` with `CaddyModule() ModuleInfo`
- **Admin API modules**: `admin.api` namespace for extending admin endpoints
- **Dynamic module loading**: Modules discovered and instantiated from JSON config

**Root cause**: No module/plugin system extractor. `caddy.RegisterModule()` is a clear pattern that could be detected to enumerate all available modules.

---

### 10. DEPENDENCIES — Score: 75/100 ⚠️ PARTIAL

**Scanner captures**: Go dependencies listed. Key deps visible (certmagic, zap, cobra, etc.)

**What's missing**:

- ⚠️ `certmagic` should be tagged [tls/acme] — it's the auto-HTTPS engine
- ⚠️ `cobra/pflag` should be tagged [cli] — CLI framework
- ⚠️ `prometheus` should be tagged [metrics]
- ✅ Dependencies correctly extracted

---

### OVERALL CADDY SCORE: 33/100

| Category           | Score   | Status     |
| ------------------ | ------- | ---------- |
| 1. Overview        | 45%     | ❌ WEAK    |
| 2. Routes          | 5%      | ❌ MISSING |
| 3. Middleware      | 5%      | ❌ MISSING |
| 4. Auth/Security   | 20%     | ❌ WEAK    |
| 5. Configuration   | 30%     | ❌ WEAK    |
| 6. Env Vars        | 70%     | ⚠️ PARTIAL |
| 7. CI/CD           | 75%     | ⚠️ PARTIAL |
| 8. Business Domain | 20%     | ❌ WEAK    |
| 9. Module System   | 15%     | ❌ WEAK    |
| 10. Dependencies   | 75%     | ⚠️ PARTIAL |
| **AVERAGE**        | **33%** |            |

---

### New Generic Gaps from Caddy

### GAP-19: `http.ServeMux.Handle()` / `mux.Handle()` not detected as route registration

**Severity**: HIGH
**Affects**: Any Go project using stdlib net/http without a web framework
**Fix**: Add patterns for `mux.Handle(pattern, handler)`, `http.HandleFunc(pattern, handler)`, `http.Handle(pattern, handler)` in api_extractor.

### GAP-20: `caddy.RegisterModule()` / init()-based module registration not detected

**Severity**: MEDIUM
**Affects**: Any Go project using plugin/module registration patterns in init() blocks
**Fix**: Detect `RegisterModule()`, `Register()`, `RegisterPlugin()` patterns to enumerate available modules/plugins.

### GAP-21: Cobra/pflag CLI commands not extracted

**Severity**: LOW
**Affects**: Go CLI tools using cobra/pflag (extremely popular)
**Fix**: Detect `&cobra.Command{Use: "name", ...}` patterns to enumerate CLI subcommands.

### GAP-22: Config-driven architecture not recognized

**Severity**: MEDIUM
**Affects**: Projects where HTTP routes/middleware are config-defined, not code-defined (Caddy, Traefik, Envoy)
**Fix**: Detect config adapter patterns. Document that the project uses runtime/config-driven routing.

---

## Consolidated Cross-Repository Analysis

### Score Summary

| Category        | gotify (Gin) | photoprism (Gin) | Caddy (stdlib) | Average |
| --------------- | :----------: | :--------------: | :------------: | :-----: |
| Overview        |     70%      |       40%        |      45%       | **52%** |
| Routes/API      |     55%      |       75%        |       5%       | **45%** |
| Middleware      |     65%      |       60%        |       5%       | **43%** |
| Auth/Security   |     40%      |       25%        |      20%       | **28%** |
| Database/ORM    |     45%      |       40%        |      N/A       | **43%** |
| Configuration   |     35%      |       20%        |      30%       | **28%** |
| Env Vars        |     30%      |       10%        |      70%       | **37%** |
| CI/CD           |     70%      |       65%        |      75%       | **70%** |
| Business Domain |     20%      |       15%        |      20%       | **18%** |
| Dependencies    |     80%      |       75%        |      75%       | **77%** |
| Testing         |     50%      |       45%        |      N/A       | **48%** |
| Frontend/UI     |     25%      |       20%        |      N/A       | **23%** |
| WebSocket       |     60%      |       50%        |      N/A       | **55%** |
| Module/Plugin   |     55%      |       N/A        |      15%       | **35%** |
| **OVERALL**     |   **47%**    |     **37%**      |    **33%**     | **39%** |

### Strongest Areas (≥60% average)

1. **Dependencies** (77%) — Go module parsing works well
2. **CI/CD** (70%) — GitHub Actions detection is solid
3. **Overview** (52%) — Acceptable but needs stack enrichment

### Weakest Areas (<30% average)

1. **Business Domain** (18%) — Consistently misclassified across ALL repos
2. **Auth/Security** (28%) — No security model extractor exists
3. **Configuration** (28%) — Config library patterns not understood
4. **Frontend/UI** (23%) — Embedded frontend stacks invisible

---

### All Identified Generic Gaps — Consolidated & Prioritized

#### TIER 1 — HIGH SEVERITY, AFFECTS MULTIPLE REPOS (Fix First)

| ID     | Gap                                          | Repos Affected     | Impact                                                                 |
| ------ | -------------------------------------------- | ------------------ | ---------------------------------------------------------------------- |
| GAP-1  | Same-file group prefix resolution broken     | gotify, photoprism | Routes lose `/application`, `/client` etc. prefix                      |
| GAP-6  | Business domain misclassification            | ALL 3              | Every repo classified wrong ("Developer Tools", "General Application") |
| GAP-10 | `router.Any()` not recognized                | photoprism         | Health/well-known/sharing endpoints invisible                          |
| GAP-12 | Engine-level vs Group-level route invisible  | photoprism         | ~27 non-API routes missed                                              |
| GAP-14 | `urfave/cli` flag→env var pattern            | photoprism         | 217 env vars missed (97.7% loss)                                       |
| GAP-19 | `mux.Handle()` / stdlib routing not detected | Caddy              | 0% route coverage on non-framework projects                            |

#### TIER 2 — MEDIUM SEVERITY, CLEAR FIX PATH

| ID     | Gap                                                      | Repos Affected     | Impact                               |
| ------ | -------------------------------------------------------- | ------------------ | ------------------------------------ |
| GAP-2  | `g.Match()`, `g.StaticFS()`, `g.Static()` not recognized | gotify             | Special Gin methods invisible        |
| GAP-3  | No OpenAPI/Swagger spec extraction                       | gotify, photoprism | Structured API docs ignored          |
| GAP-4  | No config-file template extraction                       | gotify             | config.example.yml not parsed        |
| GAP-8  | Frontend stack in embedded UIs                           | gotify, photoprism | React/Vue stacks invisible           |
| GAP-9  | Auth model not extracted                                 | gotify, photoprism | Security architecture invisible      |
| GAP-11 | `router.Handle(method, path)` not recognized             | photoprism         | WebDAV methods invisible             |
| GAP-13 | Middleware in Group() argument                           | photoprism         | APIMiddleware invisible              |
| GAP-16 | package.json description for domain                      | photoprism         | "AI-Powered Photos App" ignored      |
| GAP-17 | Swagger annotations in source not parsed                 | photoprism         | @Router/@Summary annotations ignored |
| GAP-20 | Module registration patterns                             | Caddy              | 124+ modules invisible               |

#### TIER 3 — LOW SEVERITY, NICE-TO-HAVE

| ID     | Gap                                            | Repos Affected     | Impact                      |
| ------ | ---------------------------------------------- | ------------------ | --------------------------- |
| GAP-5  | Go config library env var inference (configor) | gotify             | Config library pattern      |
| GAP-7  | Database dialect/migration extraction          | gotify, photoprism | DB architecture invisible   |
| GAP-15 | AI/ML pipeline extraction                      | photoprism         | TensorFlow/ONNX invisible   |
| GAP-18 | Dynamic path prefix functions                  | photoprism         | `conf.BaseUri()` unresolved |
| GAP-21 | Cobra/pflag CLI commands                       | Caddy              | CLI subcommands invisible   |
| GAP-22 | Config-driven architecture recognition         | Caddy              | Runtime routing invisible   |

---

### Recommended Fix Order (by ROI)

**Phase 1 — Quick Wins (high impact, relatively easy)**

1. **GAP-6: Business domain fix** — Weight README first paragraph + package.json description. Estimated: 2-3 hours.
2. **GAP-10 + GAP-11: `router.Any()` + `router.Handle()`** — Add method patterns to Go API extractor. Estimated: 1-2 hours.
3. **GAP-2: `g.Match()`, `g.StaticFS()`, `g.Static()`** — Add Gin-specific method patterns. Estimated: 1 hour.
4. **GAP-8 + GAP-16: Frontend detection** — Read `*/package.json` for description + key deps. Estimated: 2 hours.

**Phase 2 — Medium Effort (significant coverage improvement)** 5. **GAP-1: Same-file group prefix resolution** — Fix inline `g.Group(prefix)` → propagate to child routes. Estimated: 3-4 hours. 6. **GAP-19: stdlib `mux.Handle()` detection** — Add `http.Handle()`, `mux.Handle()`, `http.HandleFunc()` patterns. Estimated: 2-3 hours. 7. **GAP-12 + GAP-13: Engine-level routes + Group() middleware** — Detect routes on `*gin.Engine` not just `*gin.RouterGroup`, and middleware in Group() args. Estimated: 3-4 hours. 8. **GAP-14: `urfave/cli` env var detection** — Parse `EnvVars: EnvVars("X")` patterns in flag definitions. Estimated: 2-3 hours.

**Phase 3 — New Extractors (requires new pipeline components)** 9. **GAP-3: OpenAPI/Swagger extractor** — Parse swagger.json / openapi.yaml → routes, models, auth. Estimated: 4-6 hours. 10. **GAP-9: Auth model extractor** — Detect token extraction, password hashing, session management, role definitions. Estimated: 6-8 hours. 11. **GAP-4: Config template extractor** — Parse config.example.yml, .env.example. Estimated: 3-4 hours. 12. **GAP-7: Database config extractor** — Detect `gorm.Open()`, `AutoMigrate()`, connection pools. Estimated: 3-4 hours.

**Estimated total for Phase 1**: ~6-8 hours → Expected score improvement: +8-12% across all repos
**Estimated total for Phase 1+2**: ~17-24 hours → Expected score improvement: +15-25% across all repos
**Estimated total for all phases**: ~35-50 hours → Expected score improvement: +25-40% across all repos

---

## Phase 1 Fix Results (v4.9.1)

### Fixes Implemented

| GAP        | Fix Description                                                                                                                                                                                                                                                                                       | Files Changed                  |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| **GAP-6**  | Added `MEDIA_PHOTO` and `WEB_SERVER` domain categories with indicator keywords                                                                                                                                                                                                                        | `business_domain_extractor.py` |
| **GAP-6**  | Stripped HTML tags/markdown links from README before word extraction (badge URLs were polluting signals)                                                                                                                                                                                              | `business_domain_extractor.py` |
| **GAP-6**  | Removed over-generic indicators from DEVTOOLS (`plugin`, `extension`, `workspace`, `project`, `cli`, `config`, `schema`) and INFRASTRUCTURE (`auth`, `admin`, `hook`, `middleware`, `plugin`, `storage`, `email`, `template`, `token`, `collection`, `record`, `serve`, `backup`, `function`, `node`) | `business_domain_extractor.py` |
| **GAP-6**  | Added `push`, `websocket`, `notify`, `alert`, `sms`, `email`, `smtp`, `imap` to COMMUNICATION indicators                                                                                                                                                                                              | `business_domain_extractor.py` |
| **GAP-6**  | Boosted README first-paragraph words with 4x weight (project tagline is strongest domain signal), filtered out project-name words                                                                                                                                                                     | `business_domain_extractor.py` |
| **GAP-16** | Added `package.json` description + keywords scanning with 4x weight (scans root + `frontend/`, `ui/`, `web/`, `client/` subdirs)                                                                                                                                                                      | `business_domain_extractor.py` |
| **GAP-10** | Added `router.Any()` and `router.Match()` patterns to GENERIC_ROUTE_PATTERN                                                                                                                                                                                                                           | `go/api_extractor.py`          |
| **GAP-2**  | Added `StaticFS`, `Static`, `StaticFile` extraction as dedicated STATIC_ROUTE_PATTERN                                                                                                                                                                                                                 | `go/api_extractor.py`          |
| **GAP-1**  | Added `group_prefixes` parameter to `_extract_gin_routes`, `_extract_echo_routes`, `_extract_chi_routes` — routes now resolve group prefixes                                                                                                                                                          | `go/api_extractor.py`          |
| **GAP-19** | Enhanced `HANDLE_PATTERN` to match chained patterns like `muxWrap.mux.Handle()` and `serveMux.Handle()`                                                                                                                                                                                               | `go/api_extractor.py`          |
| **GAP-19** | Added `ADD_ROUTE_FUNC_PATTERN` for custom wrapper functions (`addRoute`, `addRouteWithMetrics`, `registerRoute`, `registerHandler`)                                                                                                                                                                   | `go/api_extractor.py`          |

### Post-Fix Scan Results

| Metric              |             gotify (Before → After)              |             photoprism (Before → After)             |          caddy (Before → After)           |
| ------------------- | :----------------------------------------------: | :-------------------------------------------------: | :---------------------------------------: |
| **Domain**          | Developer Tools → **Communication/Messaging** ✅ | General Application → **Media/Photo Management** ✅ | Developer Tools → **Web Server/Proxy** ✅ |
| **API Endpoints**   |                   25 → **29**                    |                    156 → **158**                    |               1 → **10** ✅               |
| **Route Paths**     |     Missing group prefixes → **Resolved** ✅     |                    Already good                     |         0 → **9 admin routes** ✅         |
| **Semantic Routes** |                        33                        |                         155                         |                     0                     |

### Updated Score Estimates

| Category           | gotify (Before → After) | photoprism (Before → After) | Caddy (Before → After) |
| ------------------ | :---------------------: | :-------------------------: | :--------------------: |
| Business Domain    |      20% → **85%**      |        15% → **90%**        |     20% → **90%**      |
| Routes/API         |      55% → **70%**      |        75% → **78%**        |      5% → **45%**      |
| **OVERALL (est.)** |      **47% → 55%**      |        **37% → 45%**        |     **33% → 42%**      |

### Remaining Gaps for Phase 2

| Priority | GAP    | Description                                                                |
| -------- | ------ | -------------------------------------------------------------------------- |
| HIGH     | GAP-12 | `urfave/cli` env var extraction (photoprism: 217 env vars still invisible) |
| HIGH     | GAP-9  | Auth model extraction (ACL roles, permissions invisible)                   |
| MEDIUM   | GAP-3  | OpenAPI/Swagger spec extraction                                            |
| MEDIUM   | GAP-4  | Config template extraction (YAML/TOML)                                     |
| MEDIUM   | GAP-11 | Non-APIv1 router groups (WebDAV, sharing, well-known sub-routes)           |
| MEDIUM   | GAP-17 | Module/plugin registration patterns (Caddy: 124+ modules undetected)       |
| LOW      | GAP-7  | Database dialect/migration extraction                                      |
| LOW      | GAP-15 | AI/ML subsystem detection                                                  |
| LOW      | GAP-20 | Cobra command middleware false positives                                   |
