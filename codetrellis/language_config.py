"""
Centralised language configuration for CodeTrellis.
====================================================

Single source of truth for every language-aware mapping used across the
project: file extensions, manifest files, linters, test tools, type
checkers, version sources, display names, and alias groups.

Consumers
---------
- ``init_integrations.py``  — AI instruction file generation
- ``extractors/discovery_extractor.py`` — language & sub-project detection
- ``scanner.py``            — file classification & project structure
- ``cross_language_types.py`` — (uses its own type maps; canonical
  language set validated against ``LANGUAGES`` here)

Adding a new language
---------------------
1. Add an entry to ``LANGUAGES`` below.
2. Run ``pytest tests/unit/test_language_config.py -x -q`` to verify.
3. Everything else (init_integrations, discovery_extractor, scanner)
   picks it up automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set


# ------------------------------------------------------------------
# Per-language descriptor
# ------------------------------------------------------------------

@dataclass(frozen=True)
class LanguageInfo:
    """Everything CodeTrellis needs to know about one programming language."""

    # Canonical lowercase key (must match cross_language_types keys)
    key: str

    # Human-readable display name (e.g. "TypeScript", "C#", "Go")
    display_name: str

    # File extensions that belong to this language (lowercase, with dot)
    extensions: tuple[str, ...] = ()

    # Manifest / project files that signal this language
    manifest_files: tuple[str, ...] = ()

    # Version file and regex used to extract version string.
    # ``version_file`` is the primary manifest (e.g. "pyproject.toml").
    # ``version_regex`` is a raw regex with one capture group, applied
    # with ``re.MULTILINE``.  ``None`` ⇒ use JSON key ``"version"``.
    version_file: Optional[str] = None
    version_regex: Optional[str] = None  # None → JSON .version

    # Version bump hint shown in generated AI instructions
    version_bump_hint: str = ""

    # Alternative names / abbreviations that should match this language
    # in best-practice filtering (all lowercase).
    aliases: frozenset[str] = frozenset()

    # Linters commonly used with this language (tool names, lowercase)
    linters: tuple[str, ...] = ()

    # Static type / compiler checkers
    type_checkers: tuple[str, ...] = ()

    # Default test invocation command
    test_command: str = ""

    # Test tool names (lowercase) — used for best-practice matching
    test_tools: tuple[str, ...] = ()

    # Default project type label (used in ``detect_project()``)
    project_type_label: str = ""


# ------------------------------------------------------------------
# The registry — one entry per language
# ------------------------------------------------------------------

LANGUAGES: tuple[LanguageInfo, ...] = (
    # ── Python ──────────────────────────────────────────────────────
    LanguageInfo(
        key="python",
        display_name="Python",
        extensions=(".py", ".pyi", ".pyw"),
        manifest_files=("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"),
        version_file="pyproject.toml",
        version_regex=r'^version\s*=\s*"([^"]+)"',
        version_bump_hint=(
            "# Version bump workflow:\n"
            '# 1. Edit pyproject.toml version\n'
            '# 2. pip install -e . --quiet\n'
            '# 3. Verify: python -c "import <pkg>; print(<pkg>.__version__)"'
        ),
        aliases=frozenset({"python", "py"}),
        linters=("ruff", "flake8", "pylint", "black", "isort"),
        type_checkers=("mypy", "pyright"),
        test_command="pytest tests/ -x -q",
        test_tools=("pytest", "unittest", "nose2"),
        project_type_label="Python Library",
    ),
    # ── TypeScript ──────────────────────────────────────────────────
    LanguageInfo(
        key="typescript",
        display_name="TypeScript",
        extensions=(".ts", ".tsx", ".mts", ".cts"),
        manifest_files=("package.json",),
        version_file="package.json",
        version_regex=None,  # JSON .version
        version_bump_hint=(
            "# Version bump workflow:\n"
            "# 1. npm version <major|minor|patch>\n"
            "# 2. Verify: node -e \"console.log(require('./package.json').version)\""
        ),
        aliases=frozenset({"typescript", "ts", "javascript", "js", "node"}),
        linters=("eslint", "biome", "stylelint"),
        type_checkers=("tsc",),
        test_command="npm test",
        test_tools=("jest", "vitest", "mocha", "ava", "tap"),
        project_type_label="Node.js Project",
    ),
    # ── JavaScript ──────────────────────────────────────────────────
    LanguageInfo(
        key="javascript",
        display_name="JavaScript",
        extensions=(".js", ".jsx", ".mjs", ".cjs"),
        manifest_files=("package.json",),
        version_file="package.json",
        version_regex=None,
        version_bump_hint=(
            "# Version bump workflow:\n"
            "# 1. npm version <major|minor|patch>\n"
            "# 2. Verify: node -e \"console.log(require('./package.json').version)\""
        ),
        aliases=frozenset({"javascript", "js", "typescript", "ts", "node"}),
        linters=("eslint", "biome", "stylelint"),
        type_checkers=(),
        test_command="npm test",
        test_tools=("jest", "vitest", "mocha", "ava", "tap"),
        project_type_label="Node.js Project",
    ),
    # ── Go ──────────────────────────────────────────────────────────
    LanguageInfo(
        key="go",
        display_name="Go",
        extensions=(".go",),
        manifest_files=("go.mod",),
        version_file=None,  # Go modules don't store app version in go.mod
        version_bump_hint="",
        aliases=frozenset({"go", "golang"}),
        linters=("golangci-lint", "golint", "staticcheck", "go vet"),
        type_checkers=("go vet",),
        test_command="go test ./...",
        test_tools=("go test",),
        project_type_label="Go Project",
    ),
    # ── Rust ────────────────────────────────────────────────────────
    LanguageInfo(
        key="rust",
        display_name="Rust",
        extensions=(".rs",),
        manifest_files=("Cargo.toml",),
        version_file="Cargo.toml",
        version_regex=r'^version\s*=\s*"([^"]+)"',
        version_bump_hint=(
            "# Version bump workflow:\n"
            "# 1. Edit Cargo.toml version\n"
            "# 2. cargo build\n"
            "# 3. Verify: cargo pkgid | cut -d# -f2"
        ),
        aliases=frozenset({"rust", "rs"}),
        linters=("clippy", "rustfmt"),
        type_checkers=("cargo check",),
        test_command="cargo test",
        test_tools=("cargo test",),
        project_type_label="Rust Project",
    ),
    # ── Java ────────────────────────────────────────────────────────
    LanguageInfo(
        key="java",
        display_name="Java",
        extensions=(".java",),
        manifest_files=("pom.xml", "build.gradle", "build.gradle.kts"),
        version_file="pom.xml",
        version_regex=r"<version>([^<]+)</version>",
        version_bump_hint=(
            "# Version bump workflow:\n"
            "# 1. Edit pom.xml / build.gradle version\n"
            "# 2. ./mvnw verify  OR  ./gradlew build"
        ),
        aliases=frozenset({"java", "kotlin"}),
        linters=("checkstyle", "spotbugs", "pmd", "detekt"),
        type_checkers=("javac",),
        test_command="./mvnw test",
        test_tools=("junit", "testng", "maven-surefire"),
        project_type_label="Java Project",
    ),
    # ── Kotlin ──────────────────────────────────────────────────────
    LanguageInfo(
        key="kotlin",
        display_name="Kotlin",
        extensions=(".kt", ".kts"),
        manifest_files=("build.gradle.kts", "build.gradle"),
        version_file="build.gradle.kts",
        version_regex=r'version\s*=\s*"([^"]+)"',
        aliases=frozenset({"kotlin", "java"}),
        linters=("detekt", "ktlint"),
        type_checkers=("kotlinc",),
        test_command="./gradlew test",
        test_tools=("junit", "kotest"),
        project_type_label="Kotlin Project",
    ),
    # ── C# ──────────────────────────────────────────────────────────
    LanguageInfo(
        key="csharp",
        display_name="C#",
        extensions=(".cs",),
        manifest_files=("*.csproj", "*.sln"),
        version_file="*.csproj",
        version_regex=r"<Version>([^<]+)</Version>",
        version_bump_hint=(
            "# Version bump workflow:\n"
            "# 1. Edit .csproj <Version> element\n"
            "# 2. dotnet build"
        ),
        aliases=frozenset({"csharp", "c#", ".net", "dotnet"}),
        linters=("roslyn-analyzers", "stylecop"),
        type_checkers=("dotnet build",),
        test_command="dotnet test",
        test_tools=("xunit", "nunit", "mstest"),
        project_type_label="C# Project",
    ),
    # ── Ruby ────────────────────────────────────────────────────────
    LanguageInfo(
        key="ruby",
        display_name="Ruby",
        extensions=(".rb", ".rake", ".gemspec", ".ru"),
        manifest_files=("Gemfile", "*.gemspec"),
        version_file="*.gemspec",
        version_regex=r'\.version\s*=\s*["\']([^"\']+)',
        aliases=frozenset({"ruby", "rb"}),
        linters=("rubocop", "standard"),
        type_checkers=("sorbet", "steep"),
        test_command="bundle exec rspec",
        test_tools=("rspec", "minitest"),
        project_type_label="Ruby Project",
    ),
    # ── PHP ─────────────────────────────────────────────────────────
    LanguageInfo(
        key="php",
        display_name="PHP",
        extensions=(".php", ".phtml"),
        manifest_files=("composer.json",),
        version_file="composer.json",
        version_regex=None,
        aliases=frozenset({"php"}),
        linters=("phpstan", "phpcs", "psalm"),
        type_checkers=("phpstan", "psalm"),
        test_command="./vendor/bin/phpunit",
        test_tools=("phpunit", "pest"),
        project_type_label="PHP Project",
    ),
    # ── Swift ───────────────────────────────────────────────────────
    LanguageInfo(
        key="swift",
        display_name="Swift",
        extensions=(".swift",),
        manifest_files=("Package.swift",),
        version_file="Package.swift",
        version_regex=r'\.version\s*\(\s*"([^"]+)"',
        aliases=frozenset({"swift"}),
        linters=("swiftlint",),
        type_checkers=("swiftc",),
        test_command="swift test",
        test_tools=("xctest",),
        project_type_label="Swift Project",
    ),
    # ── Dart / Flutter ──────────────────────────────────────────────
    LanguageInfo(
        key="dart",
        display_name="Dart",
        extensions=(".dart",),
        manifest_files=("pubspec.yaml",),
        version_file="pubspec.yaml",
        version_regex=r'^version:\s*(.+)$',
        aliases=frozenset({"dart", "flutter"}),
        linters=("dart analyze", "dart format"),
        type_checkers=("dart analyze",),
        test_command="dart test",
        test_tools=("dart test", "flutter_test"),
        project_type_label="Dart Project",
    ),
    # ── Scala ───────────────────────────────────────────────────────
    LanguageInfo(
        key="scala",
        display_name="Scala",
        extensions=(".scala", ".sc", ".sbt"),
        manifest_files=("build.sbt",),
        version_file="build.sbt",
        version_regex=r'version\s*:=\s*"([^"]+)"',
        aliases=frozenset({"scala"}),
        linters=("scalafix", "scalafmt", "wartremover"),
        type_checkers=("scalac",),
        test_command="sbt test",
        test_tools=("scalatest", "munit", "specs2"),
        project_type_label="Scala Project",
    ),
    # ── Elixir ──────────────────────────────────────────────────────
    LanguageInfo(
        key="elixir",
        display_name="Elixir",
        extensions=(".ex", ".exs"),
        manifest_files=("mix.exs",),
        version_file="mix.exs",
        version_regex=r'version:\s*"([^"]+)"',
        aliases=frozenset({"elixir"}),
        linters=("credo", "dialyzer"),
        type_checkers=("dialyzer",),
        test_command="mix test",
        test_tools=("exunit",),
        project_type_label="Elixir Project",
    ),
    # ── C ───────────────────────────────────────────────────────────
    LanguageInfo(
        key="c",
        display_name="C",
        extensions=(".c", ".h"),
        manifest_files=("CMakeLists.txt", "Makefile", "meson.build"),
        aliases=frozenset({"c"}),
        linters=("cppcheck", "clang-tidy"),
        type_checkers=("gcc", "clang"),
        test_command="make test",
        test_tools=("cunit", "cmocka", "check"),
        project_type_label="C Project",
    ),
    # ── C++ ─────────────────────────────────────────────────────────
    LanguageInfo(
        key="cpp",
        display_name="C++",
        extensions=(".cpp", ".cxx", ".cc", ".c++", ".hpp", ".hxx", ".hh", ".h++", ".ipp", ".inl", ".tpp"),
        manifest_files=("CMakeLists.txt", "Makefile", "meson.build"),
        aliases=frozenset({"cpp", "c++", "cxx"}),
        linters=("cppcheck", "clang-tidy", "cpplint"),
        type_checkers=("g++", "clang++"),
        test_command="make test",
        test_tools=("gtest", "catch2", "doctest"),
        project_type_label="C++ Project",
    ),
    # ── Lua ─────────────────────────────────────────────────────────
    LanguageInfo(
        key="lua",
        display_name="Lua",
        extensions=(".lua",),
        manifest_files=(),
        aliases=frozenset({"lua"}),
        linters=("luacheck",),
        type_checkers=(),
        test_command="busted",
        test_tools=("busted", "luaunit"),
        project_type_label="Lua Project",
    ),
    # ── R ───────────────────────────────────────────────────────────
    LanguageInfo(
        key="r",
        display_name="R",
        extensions=(".r", ".R", ".Rmd", ".Rnw"),
        manifest_files=("DESCRIPTION",),
        version_file="DESCRIPTION",
        version_regex=r'^Version:\s*(.+)$',
        aliases=frozenset({"r"}),
        linters=("lintr",),
        type_checkers=(),
        test_command="Rscript -e 'testthat::test_dir(\"tests\")'",
        test_tools=("testthat",),
        project_type_label="R Project",
    ),
    # ── PowerShell ──────────────────────────────────────────────────
    LanguageInfo(
        key="powershell",
        display_name="PowerShell",
        extensions=(".ps1", ".psm1", ".psd1", ".ps1xml"),
        manifest_files=(),
        aliases=frozenset({"powershell", "pwsh"}),
        linters=("psscriptanalyzer",),
        type_checkers=(),
        test_command="Invoke-Pester",
        test_tools=("pester",),
        project_type_label="PowerShell Project",
    ),
    # ── F# ──────────────────────────────────────────────────────────
    LanguageInfo(
        key="fsharp",
        display_name="F#",
        extensions=(".fs", ".fsx", ".fsi"),
        manifest_files=("*.fsproj",),
        aliases=frozenset({"fsharp", "f#"}),
        linters=("fantomas",),
        type_checkers=("dotnet build",),
        test_command="dotnet test",
        test_tools=("expecto", "xunit"),
        project_type_label="F# Project",
    ),
    # ── Bash / Shell ────────────────────────────────────────────────
    LanguageInfo(
        key="bash",
        display_name="Bash",
        extensions=(".sh", ".bash", ".zsh", ".ksh"),
        manifest_files=(),
        aliases=frozenset({"bash", "shell", "sh", "zsh"}),
        linters=("shellcheck", "shfmt"),
        type_checkers=(),
        test_command="bats tests/",
        test_tools=("bats",),
        project_type_label="Shell Scripts",
    ),
    # ── Perl ────────────────────────────────────────────────────────
    LanguageInfo(
        key="perl",
        display_name="Perl",
        extensions=(".pl", ".pm"),
        manifest_files=("Makefile.PL", "dist.ini", "cpanfile"),
        aliases=frozenset({"perl"}),
        linters=("perlcritic", "perltidy"),
        type_checkers=(),
        test_command="prove -l t/",
        test_tools=("test::more",),
        project_type_label="Perl Project",
    ),
    # ── Haskell ─────────────────────────────────────────────────────
    LanguageInfo(
        key="haskell",
        display_name="Haskell",
        extensions=(".hs",),
        manifest_files=("*.cabal", "stack.yaml", "package.yaml"),
        aliases=frozenset({"haskell", "hs"}),
        linters=("hlint",),
        type_checkers=("ghc",),
        test_command="stack test",
        test_tools=("hspec", "hunit", "quickcheck"),
        project_type_label="Haskell Project",
    ),
    # ── Clojure ─────────────────────────────────────────────────────
    LanguageInfo(
        key="clojure",
        display_name="Clojure",
        extensions=(".clj", ".cljs", ".cljc", ".edn"),
        manifest_files=("deps.edn", "project.clj"),
        aliases=frozenset({"clojure", "clj"}),
        linters=("clj-kondo",),
        type_checkers=(),
        test_command="lein test",
        test_tools=("clojure.test",),
        project_type_label="Clojure Project",
    ),
    # ── Erlang ──────────────────────────────────────────────────────
    LanguageInfo(
        key="erlang",
        display_name="Erlang",
        extensions=(".erl", ".hrl"),
        manifest_files=("rebar.config",),
        aliases=frozenset({"erlang"}),
        linters=("elvis",),
        type_checkers=("dialyzer",),
        test_command="rebar3 ct",
        test_tools=("eunit", "common_test"),
        project_type_label="Erlang Project",
    ),
    # ── OCaml ───────────────────────────────────────────────────────
    LanguageInfo(
        key="ocaml",
        display_name="OCaml",
        extensions=(".ml", ".mli"),
        manifest_files=("dune-project",),
        aliases=frozenset({"ocaml"}),
        linters=("ocamlformat",),
        type_checkers=("ocamlc",),
        test_command="dune runtest",
        test_tools=("alcotest", "ounit"),
        project_type_label="OCaml Project",
    ),
    # ── Zig ─────────────────────────────────────────────────────────
    LanguageInfo(
        key="zig",
        display_name="Zig",
        extensions=(".zig",),
        manifest_files=("build.zig",),
        aliases=frozenset({"zig"}),
        linters=(),
        type_checkers=("zig build",),
        test_command="zig build test",
        test_tools=("zig test",),
        project_type_label="Zig Project",
    ),
    # ── Nim ─────────────────────────────────────────────────────────
    LanguageInfo(
        key="nim",
        display_name="Nim",
        extensions=(".nim",),
        manifest_files=("*.nimble",),
        aliases=frozenset({"nim"}),
        linters=(),
        type_checkers=("nim check",),
        test_command="nimble test",
        test_tools=("testament",),
        project_type_label="Nim Project",
    ),
    # ── Crystal ─────────────────────────────────────────────────────
    LanguageInfo(
        key="crystal",
        display_name="Crystal",
        extensions=(".cr",),
        manifest_files=("shard.yml",),
        aliases=frozenset({"crystal", "cr"}),
        linters=("ameba",),
        type_checkers=("crystal build",),
        test_command="crystal spec",
        test_tools=("crystal spec",),
        project_type_label="Crystal Project",
    ),
    # ── V ───────────────────────────────────────────────────────────
    LanguageInfo(
        key="v",
        display_name="V",
        extensions=(".v",),
        manifest_files=("v.mod",),
        aliases=frozenset({"vlang", "v"}),
        linters=(),
        type_checkers=(),
        test_command="v test .",
        test_tools=("v test",),
        project_type_label="V Project",
    ),
    # ── Solidity ────────────────────────────────────────────────────
    LanguageInfo(
        key="solidity",
        display_name="Solidity",
        extensions=(".sol",),
        manifest_files=("hardhat.config.ts", "hardhat.config.js", "foundry.toml"),
        aliases=frozenset({"solidity", "sol"}),
        linters=("solhint",),
        type_checkers=("solc",),
        test_command="npx hardhat test",
        test_tools=("hardhat", "forge test"),
        project_type_label="Solidity Project",
    ),
    # ── Protobuf ────────────────────────────────────────────────────
    LanguageInfo(
        key="protobuf",
        display_name="Protobuf",
        extensions=(".proto",),
        manifest_files=(),
        aliases=frozenset({"protobuf", "proto", "grpc"}),
        linters=("buf",),
        type_checkers=("protoc",),
        test_command="",
        test_tools=(),
        project_type_label="",
    ),
    # ── CSS (markup, always-include bucket) ─────────────────────────
    LanguageInfo(
        key="css",
        display_name="CSS",
        extensions=(".css", ".scss", ".sass", ".less", ".pcss"),
        manifest_files=(),
        aliases=frozenset({"css", "scss", "sass", "less"}),
        linters=("stylelint",),
        type_checkers=(),
        test_command="",
        test_tools=(),
        project_type_label="",
    ),
    # ── HTML (markup, always-include bucket) ────────────────────────
    LanguageInfo(
        key="html",
        display_name="HTML",
        extensions=(".html", ".htm"),
        manifest_files=(),
        aliases=frozenset({"html"}),
        linters=("htmlhint",),
        type_checkers=(),
        test_command="",
        test_tools=(),
        project_type_label="",
    ),
    # ── SQL (always-include bucket) ─────────────────────────────────
    LanguageInfo(
        key="sql",
        display_name="SQL",
        extensions=(".sql",),
        manifest_files=(),
        aliases=frozenset({"sql"}),
        linters=("sqlfluff",),
        type_checkers=(),
        test_command="",
        test_tools=(),
        project_type_label="",
    ),
)


# ------------------------------------------------------------------
# Derived look-up dicts (built once at import time)
# ------------------------------------------------------------------

def _build_by_key() -> Dict[str, LanguageInfo]:
    return {lang.key: lang for lang in LANGUAGES}

def _build_ext_to_lang() -> Dict[str, str]:
    """Extension → canonical language key  (e.g. '.py' → 'python')."""
    m: Dict[str, str] = {}
    for lang in LANGUAGES:
        for ext in lang.extensions:
            m[ext] = lang.key
    return m

def _build_manifest_to_lang() -> Dict[str, str]:
    """Manifest filename → canonical language key."""
    m: Dict[str, str] = {}
    for lang in LANGUAGES:
        for mf in lang.manifest_files:
            if "*" not in mf:          # skip glob patterns (*.csproj)
                m[mf] = lang.key
    return m

def _build_ext_to_display() -> Dict[str, str]:
    """Extension → display name  (e.g. '.py' → 'Python')."""
    m: Dict[str, str] = {}
    for lang in LANGUAGES:
        for ext in lang.extensions:
            m[ext] = lang.display_name
    return m

def _build_alias_map() -> Dict[str, Set[str]]:
    """Detected-language display name (lowered) → set of alias strings
    that should match best-practice entries for that language.

    E.g.  {"typescript": {"typescript", "ts", "javascript", "js", "node"}}
    """
    m: Dict[str, Set[str]] = {}
    for lang in LANGUAGES:
        m[lang.display_name.lower()] = set(lang.aliases)
    return m

def _build_linter_lang() -> Dict[str, Set[str]]:
    """Linter tool name → set of canonical language keys it belongs to."""
    m: Dict[str, Set[str]] = {}
    for lang in LANGUAGES:
        for linter in lang.linters:
            m.setdefault(linter, set()).add(lang.key)
    return m

def _build_type_checker_lang() -> Dict[str, Set[str]]:
    """Type-checker tool name → set of canonical language keys it belongs to."""
    m: Dict[str, Set[str]] = {}
    for lang in LANGUAGES:
        for tc in lang.type_checkers:
            m.setdefault(tc, set()).add(lang.key)
    return m

def _build_test_tool_lang() -> Dict[str, Set[str]]:
    """Test tool name → set of canonical language keys it belongs to."""
    m: Dict[str, Set[str]] = {}
    for lang in LANGUAGES:
        for tt in lang.test_tools:
            m.setdefault(tt, set()).add(lang.key)
    return m


# Materialised caches (module-level singletons)
BY_KEY:             Dict[str, LanguageInfo]  = _build_by_key()
EXT_TO_LANG:        Dict[str, str]           = _build_ext_to_lang()
MANIFEST_TO_LANG:   Dict[str, str]           = _build_manifest_to_lang()
EXT_TO_DISPLAY:     Dict[str, str]           = _build_ext_to_display()
ALIAS_MAP:          Dict[str, Set[str]]      = _build_alias_map()
LINTER_LANG:        Dict[str, Set[str]]      = _build_linter_lang()
TYPE_CHECKER_LANG:  Dict[str, Set[str]]      = _build_type_checker_lang()
TEST_TOOL_LANG:     Dict[str, Set[str]]      = _build_test_tool_lang()

# Set of alias groups that are always shown in conventions regardless
# of detected project language (lowercase keys).
ALWAYS_INCLUDE_ALIASES: FrozenSet[str] = frozenset({
    "bash", "shell", "docker", "git", "ci", "general",
})
