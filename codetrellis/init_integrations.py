"""
CodeTrellis AI Integration Initializer
======================================

Generates AI tool integration files for any project so that every
AI coding assistant (Copilot, Claude, Cursor, etc.) automatically
gets pre-loaded project context via the CodeTrellis Matrix.

Generated files:
  .vscode/mcp.json                — MCP server for Copilot / VS Code
  .vscode/tasks.json              — Watch, scan, verify, test tasks
  .github/copilot-instructions.md — Copilot auto-loaded instructions
  CLAUDE.md                       — Claude Code auto-loaded memory
  .cursorrules                    — Cursor auto-loaded rules

Strategy:
  The scan runs FIRST, producing a matrix with 34+ sections of deep
  project knowledge. Then we read the matrix sections and inject real
  project-specific details (types, APIs, commands, architecture,
  business domain) into every AI config file — producing far richer
  context than basic file detection alone.

Usage:
  codetrellis init /path/to/project          # .codetrellis/ config only
  codetrellis init /path/to/project --ai     # scan + generate AI files

Part of CodeTrellis v4.68 — AI Integration Initializer
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from . import __version__ as VERSION
from .language_config import (
    ALWAYS_INCLUDE_ALIASES,
    ALIAS_MAP as _LC_ALIAS_MAP,
    BY_KEY as _LC_BY_KEY,
    EXT_TO_LANG,
    LANGUAGES,
    LINTER_LANG as _LC_LINTER_LANG,
    MANIFEST_TO_LANG,
    TEST_TOOL_LANG as _LC_TEST_LANG,
    TYPE_CHECKER_LANG as _LC_TYCHECK_LANG,
    LanguageInfo,
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ProjectInfo:
    """Detected project information used to populate templates."""
    name: str
    root: Path
    project_type: str = "Unknown"
    detected_languages: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)
    has_tests: bool = False
    test_command: str = ""
    has_pyproject: bool = False
    has_package_json: bool = False
    has_cargo_toml: bool = False
    has_go_mod: bool = False
    python_executable: str = sys.executable


@dataclass
class MatrixContext:
    """Rich project context extracted from the scanned matrix.

    Populated AFTER scan completes — contains real project data,
    not just file-detection guesses.
    """
    project_name: str = ""
    project_type: str = ""
    business_domain: str = ""
    business_purpose: str = ""
    overview: str = ""
    runbook: str = ""
    cli_commands: str = ""
    project_structure: str = ""
    infrastructure: str = ""
    actionable_items: str = ""
    best_practices: str = ""
    best_practices_parsed: List[Dict[str, object]] = field(default_factory=list)
    project_profile: str = ""
    primary_language: str = ""
    primary_type_section: str = ""
    python_version: str = ""
    version_source: str = ""
    ci_jobs: List[str] = field(default_factory=list)
    ci_triggers: str = ""
    test_frameworks: str = ""
    build_system: str = ""
    contributing_steps: List[str] = field(default_factory=list)
    data_flow_pattern: str = ""
    type_count: int = 0
    api_endpoint_count: int = 0
    total_files: int = 0
    sections: List[str] = field(default_factory=list)
    section_count: int = 0


@dataclass
class GeneratedFile:
    """A file to be written during init."""
    path: Path
    content: str
    description: str
    overwritten: bool = False


def detect_project(project_root: Path) -> ProjectInfo:
    """
    Auto-detect project type, languages, frameworks, and test commands
    by inspecting manifest files and directory structure.

    Uses ``language_config.LANGUAGES`` as the single source of truth for
    manifest → language mapping, test commands, and project-type labels.

    Args:
        project_root: Absolute path to the project root.

    Returns:
        A populated ProjectInfo dataclass.
    """
    info = ProjectInfo(name=project_root.name, root=project_root)

    # Detect languages via manifest files defined in language_config
    for lang in LANGUAGES:
        for mf in lang.manifest_files:
            if "*" in mf:
                # Glob pattern (e.g. *.csproj)
                if list(project_root.glob(mf)):
                    if lang.display_name not in info.detected_languages:
                        info.detected_languages.append(lang.display_name)
                    if info.project_type == "Unknown" and lang.project_type_label:
                        info.project_type = lang.project_type_label
                    break
            elif (project_root / mf).exists():
                if lang.display_name not in info.detected_languages:
                    info.detected_languages.append(lang.display_name)
                if info.project_type == "Unknown" and lang.project_type_label:
                    info.project_type = lang.project_type_label
                # Set convenience flags for backward compat
                if mf == "pyproject.toml":
                    info.has_pyproject = True
                elif mf == "package.json":
                    info.has_package_json = True
                elif mf == "Cargo.toml":
                    info.has_cargo_toml = True
                elif mf == "go.mod":
                    info.has_go_mod = True
                break  # one manifest match per language is enough

    # Framework-specific deep detection (kept separate — too specialised)
    if "Python" in info.detected_languages:
        _detect_python_frameworks(project_root, info)
    pkg_json = project_root / "package.json"
    if pkg_json.exists():
        _detect_node_frameworks(pkg_json, info)

    # --- Tests ---
    tests_dir = project_root / "tests"
    test_dir = project_root / "test"
    spec_dir = project_root / "spec"
    if tests_dir.is_dir() or test_dir.is_dir():
        info.has_tests = True
    if spec_dir.is_dir():
        info.has_tests = True

    # Determine test command from first matching language
    if not info.test_command:
        for lang in LANGUAGES:
            if lang.display_name in info.detected_languages and lang.test_command:
                info.test_command = lang.test_command
                break

    # Fallback
    if not info.detected_languages:
        info.detected_languages.append("Unknown")
    if info.project_type == "Unknown" and info.detected_languages:
        info.project_type = f"{info.detected_languages[0]} Project"

    return info


def _detect_python_frameworks(project_root: Path, info: ProjectInfo) -> None:
    """Detect Python frameworks from common imports or config files."""
    indicators = {
        "FastAPI": ["fastapi"],
        "Django": ["django", "manage.py"],
        "Flask": ["flask"],
        "PyTorch": ["torch"],
        "SQLAlchemy": ["sqlalchemy"],
        "Pydantic": ["pydantic"],
        "Celery": ["celery"],
    }
    # Quick scan of pyproject.toml or requirements.txt for framework names
    for manifest in ["pyproject.toml", "requirements.txt", "requirements.in"]:
        manifest_path = project_root / manifest
        if manifest_path.exists():
            try:
                content = manifest_path.read_text(errors="ignore").lower()
                for framework, keywords in indicators.items():
                    if any(kw in content for kw in keywords):
                        if framework not in info.detected_frameworks:
                            info.detected_frameworks.append(framework)
            except OSError:
                pass


def _detect_node_frameworks(package_json_path: Path, info: ProjectInfo) -> None:
    """Detect Node.js / TypeScript frameworks from package.json."""
    try:
        data = json.loads(package_json_path.read_text(errors="ignore"))
        all_deps = {}
        all_deps.update(data.get("dependencies", {}))
        all_deps.update(data.get("devDependencies", {}))

        framework_map = {
            "@angular/core": "Angular",
            "react": "React",
            "vue": "Vue.js",
            "next": "Next.js",
            "svelte": "Svelte",
            "@nestjs/core": "NestJS",
            "express": "Express",
        }
        for dep, name in framework_map.items():
            if dep in all_deps and name not in info.detected_frameworks:
                info.detected_frameworks.append(name)

        # Detect TypeScript
        if "typescript" in all_deps and "TypeScript" not in info.detected_languages:
            info.detected_languages.append("TypeScript")

    except (json.JSONDecodeError, OSError):
        pass


# ---------------------------------------------------------------------------
# Matrix context extraction (post-scan, rich)
# ---------------------------------------------------------------------------

def extract_matrix_context(project_root: Path) -> Optional[MatrixContext]:
    """
    Read the matrix.prompt file produced by a scan and extract
    structured project knowledge from its sections.

    Returns None if no matrix is found.
    """
    cache_base = project_root / ".codetrellis" / "cache"
    if not cache_base.exists():
        return None

    matrix_path = None
    # Search for matrix.prompt in project cache directory
    for sub_dir in sorted(cache_base.iterdir(), reverse=True):
        if sub_dir.is_dir():
            candidate = sub_dir / "matrix.prompt"
            if candidate.exists():
                matrix_path = candidate
                break
            # Also check for legacy versioned layout (cache/VERSION/project/)
            for nested_dir in sorted(sub_dir.iterdir(), reverse=True):
                if nested_dir.is_dir():
                    candidate = nested_dir / "matrix.prompt"
                    if candidate.exists():
                        matrix_path = candidate
                        break
            if matrix_path:
                break

    if not matrix_path:
        return None

    try:
        content = matrix_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None

    ctx = MatrixContext()

    # Extract all section names
    ctx.sections = list(dict.fromkeys(re.findall(r'^\[([A-Z_]+)\]', content, re.MULTILINE)))
    ctx.section_count = len(ctx.sections)

    # Extract specific sections
    ctx.project_name = _extract_field(content, "PROJECT", "name") or project_root.name
    ctx.project_type = _extract_field(content, "PROJECT", "type") or ""
    ctx.overview = _extract_section(content, "OVERVIEW")
    ctx.runbook = _extract_section(content, "RUNBOOK")
    ctx.business_domain = _extract_field(content, "BUSINESS_DOMAIN", "domain") or ""
    ctx.business_purpose = _extract_field(content, "BUSINESS_DOMAIN", "purpose") or ""
    ctx.cli_commands = _extract_section(content, "CLI_COMMANDS")
    ctx.infrastructure = _extract_section(content, "INFRASTRUCTURE")
    ctx.actionable_items = _extract_section(content, "ACTIONABLE_ITEMS")
    ctx.best_practices = _extract_section(content, "BEST_PRACTICES")
    ctx.project_profile = _extract_section(content, "PROJECT_PROFILE")
    ctx.data_flow_pattern = _extract_field(content, "DATA_FLOWS", "primary-pattern") or ""

    # Parse project structure from OVERVIEW dirs line (PROJECT_STRUCTURE
    # section doesn't exist — the directory info is in OVERVIEW)
    if ctx.overview:
        dirs_match = re.search(r'dirs:(.+)', ctx.overview)
        if dirs_match:
            ctx.project_structure = dirs_match.group(1).strip()

    # Detect primary language from PROJECT_PROFILE or OVERVIEW
    if ctx.project_profile:
        lang_field = _extract_field_from_text(ctx.project_profile, "languages")
        if lang_field:
            ctx.primary_language = lang_field.split(",")[0].strip()
        test_field = _extract_field_from_text(ctx.project_profile, "testing")
        if test_field:
            ctx.test_frameworks = test_field
        build_field = _extract_field_from_text(ctx.project_profile, "build")
        if build_field:
            ctx.build_system = build_field

    # Detect primary type section name for this project
    _TYPE_SECTION_MAP = {
        "python": "PYTHON_TYPES",
        "typescript": "TS_TYPES",
        "javascript": "JS_TYPES",
        "java": "JAVA_TYPES",
        "go": "GO_TYPES",
        "rust": "RUST_TYPES",
        "csharp": "CSHARP_TYPES",
        "c#": "CSHARP_TYPES",
        "dart": "DART_TYPES",
    }
    if ctx.primary_language:
        ctx.primary_type_section = _TYPE_SECTION_MAP.get(
            ctx.primary_language.lower(), ""
        )
    # Fallback: find the first type section that exists
    if not ctx.primary_type_section:
        for section_name in _TYPE_SECTION_MAP.values():
            if section_name in ctx.sections:
                ctx.primary_type_section = section_name
                break

    # Parse RUNBOOK for CI, version, and contributing info
    if ctx.runbook:
        # CI jobs
        for ci_match in re.finditer(r'ci:[^|]+\|[^|]*\|jobs:(.+)', ctx.runbook):
            jobs = [j.strip() for j in ci_match.group(1).split(",")]
            ctx.ci_jobs.extend(jobs)
        # CI triggers
        trigger_match = re.search(r'triggers:([^\n|]+)', ctx.runbook)
        if trigger_match:
            ctx.ci_triggers = trigger_match.group(1).strip()
        # Python version requirement
        py_ver_match = re.search(r'Python:([^\n]+)', ctx.runbook)
        if py_ver_match:
            ctx.python_version = py_ver_match.group(1).strip()
        # Contributing steps
        contrib_lines = re.findall(
            r'^\s+\d+\.\s+(.+)$', ctx.runbook, re.MULTILINE
        )
        if contrib_lines:
            ctx.contributing_steps = contrib_lines

    # Parse BEST_PRACTICES into structured list
    if ctx.best_practices:
        ctx.best_practices_parsed = _parse_best_practices(ctx.best_practices)

    # Detect version source using language_config
    for lang in LANGUAGES:
        if not lang.version_file:
            continue
        if "*" in lang.version_file:
            matches = list(project_root.glob(lang.version_file))
            candidate = matches[0] if matches else None
        else:
            candidate = project_root / lang.version_file
        if candidate and candidate.exists():
            try:
                text = candidate.read_text(encoding="utf-8", errors="ignore")
                if lang.version_regex is None:
                    # JSON-based version (e.g. package.json)
                    data = json.loads(text)
                    if "version" in data:
                        ctx.version_source = (
                            f"{candidate.name} (version = \"{data['version']}\")"
                        )
                        break
                else:
                    ver_match = re.search(lang.version_regex, text, re.MULTILINE)
                    if ver_match:
                        ctx.version_source = (
                            f"{candidate.name} (version = \"{ver_match.group(1)}\")"
                        )
                        break
            except (json.JSONDecodeError, OSError):
                pass

    # Count types and APIs from relevant sections
    for section_name in ["PYTHON_TYPES", "TS_TYPES", "JAVA_TYPES",
                         "GO_TYPES", "RUST_TYPES", "CSHARP_TYPES"]:
        types_section = _extract_section(content, section_name)
        if types_section:
            ctx.type_count += types_section.count("\n")
            break  # Only count primary language

    for section_name in ["PYTHON_API", "API_ENDPOINTS", "ROUTES_SEMANTIC",
                         "ROUTES", "HTTP_API", "TS_API", "JS_API"]:
        api_section = _extract_section(content, section_name)
        if api_section:
            ctx.api_endpoint_count += api_section.count("\n")
            break

    # Read metadata for file count
    meta_path = matrix_path.parent / "_metadata.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            ctx.total_files = meta.get("stats", {}).get("totalFiles", 0)
        except (json.JSONDecodeError, OSError):
            pass

    return ctx


def _extract_section(content: str, section_name: str) -> str:
    """Extract the full text of a matrix section."""
    pattern = rf'\[{section_name}\]\n(.*?)(?=\n\[[A-Z_]+\]|$)'
    m = re.search(pattern, content, re.DOTALL)
    return m.group(1).strip() if m else ""


def _extract_field(content: str, section_name: str, field_name: str) -> Optional[str]:
    """Extract a specific field=value from a matrix section."""
    section = _extract_section(content, section_name)
    if not section:
        return None
    m = re.search(rf'{field_name}[=:](.+?)(?:\n|$)', section)
    return m.group(1).strip() if m else None


def _extract_field_from_text(text: str, field_name: str) -> Optional[str]:
    """Extract a field=value from arbitrary text (not section-scoped)."""
    m = re.search(rf'{field_name}=(.+?)(?:\n|$)', text)
    return m.group(1).strip() if m else None


def _parse_best_practices(raw: str) -> List[Dict[str, object]]:
    """Parse BEST_PRACTICES section into structured dicts.

    Input format: ``language:category|use:x,y,z|avoid:a,b,c``
    Returns list of dicts with keys: lang, category, use, avoid.
    """
    results: List[Dict[str, object]] = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        entry: Dict[str, object] = {"lang": "", "category": "", "use": [], "avoid": []}
        for part in parts:
            part = part.strip()
            if part.startswith("use:"):
                entry["use"] = [x.strip() for x in part[4:].split(",") if x.strip()]
            elif part.startswith("avoid:"):
                entry["avoid"] = [x.strip() for x in part[6:].split(",") if x.strip()]
            elif ":" in part and not entry["lang"]:
                lang_cat = part.split(":", 1)
                entry["lang"] = lang_cat[0].strip()
                entry["category"] = lang_cat[1].strip() if len(lang_cat) > 1 else ""
            elif not entry["lang"]:
                entry["lang"] = part.strip()
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# Shared template building blocks
# ---------------------------------------------------------------------------

def _build_conventions_block(
    info: ProjectInfo,
    ctx: Optional[MatrixContext],
    *,
    include_header: bool = True,
) -> str:
    """Build a conventions / best-practices block from matrix data."""
    lines: List[str] = []
    if include_header:
        lines.append("## Key Conventions")
        lines.append("")

    languages = ", ".join(info.detected_languages)

    # Language-aware conventions from BEST_PRACTICES
    if ctx and ctx.best_practices_parsed:
        # Filter best practices to only include languages detected in the project
        detected_lower = {lang.lower() for lang in info.detected_languages}
        # Expand detected languages with aliases from language_config
        expanded_detected = set(detected_lower)
        for lang_key, aliases in _LC_ALIAS_MAP.items():
            if lang_key in detected_lower or (detected_lower & aliases):
                expanded_detected.update(aliases)

        idx = 1
        for bp in ctx.best_practices_parsed:
            lang = str(bp.get("lang", "")).lower()
            # Skip if language is not relevant to this project
            if lang and lang not in expanded_detected and lang not in ALWAYS_INCLUDE_ALIASES:
                continue
            use_items = bp.get("use", [])
            avoid_items = bp.get("avoid", [])
            cat = str(bp.get("category", ""))
            label = f"{bp.get('lang', lang)}" + (f" ({cat})" if cat else "")
            parts = []
            if use_items:
                parts.append(f"use {', '.join(str(u) for u in use_items)}")
            if avoid_items:
                parts.append(f"avoid {', '.join(str(a) for a in avoid_items)}")
            if parts:
                lines.append(f"{idx}. **{label}:** {'; '.join(parts)}.")
                idx += 1
    else:
        lines.append(f"1. **Language:** {languages}. Follow existing patterns.")
        lines.append("2. **Error handling:** Follow the project's established patterns.")

    # Contributing steps from RUNBOOK
    if ctx and ctx.contributing_steps:
        lines.append("")
        lines.append("### Contributing (new code integration)")
        lines.append("")
        for i, step in enumerate(ctx.contributing_steps, 1):
            lines.append(f"{i}. {step}")

    if info.test_command:
        lines.append("")
        lines.append(f"Run tests: `{info.test_command}`")

    return "\n".join(lines) + "\n"


def _build_quality_gates_block(
    info: ProjectInfo,
    ctx: Optional[MatrixContext],
) -> str:
    """Build quality gates section from CI and best-practices data."""
    if not ctx:
        return ""

    lines = ["## Quality Gates (CI enforced)", ""]
    idx = 1

    # Detect linting tools from best practices — language-filtered
    linters = set()
    test_tools = set()
    detected_lower = {lang.lower() for lang in info.detected_languages}
    if ctx.best_practices_parsed:
        for bp in ctx.best_practices_parsed:
            for tool in bp.get("use", []):
                tool_str = str(tool).lower()
                # Only include linters relevant to detected languages
                if tool_str in _LC_LINTER_LANG:
                    needed_langs = _LC_LINTER_LANG[tool_str]
                    if needed_langs & detected_lower or tool_str == "shellcheck":
                        linters.add(str(tool))
                elif tool_str in _LC_TEST_LANG:
                    needed_langs = _LC_TEST_LANG[tool_str]
                    if needed_langs & detected_lower:
                        test_tools.add(str(tool))

    for linter in sorted(linters):
        lines.append(f"{idx}. **{linter}** lint must pass")
        idx += 1

    # Type checking (mypy/tsc) — language-filtered
    for bp in (ctx.best_practices_parsed or []):
        for tool in bp.get("use", []):
            tool_str = str(tool).lower()
            if tool_str in _LC_TYCHECK_LANG:
                needed = _LC_TYCHECK_LANG[tool_str]
                if needed & detected_lower:
                    lines.append(f"{idx}. **{tool}** type-check (advisory)")
                    idx += 1

    # Version consistency
    if ctx.version_source:
        lines.append(f"{idx}. **Version consistency** — "
                      f"{ctx.version_source.split('(')[0].strip()} must be single source of truth")
        idx += 1

    # Tests
    if info.test_command:
        py_ver = ""
        if ctx.python_version:
            py_ver = f" (Python {ctx.python_version})"
        lines.append(f"{idx}. **Tests** — `{info.test_command}`{py_ver}")
        idx += 1

    if idx == 1:
        return ""  # Nothing detected

    return "\n".join(lines) + "\n"


def _build_version_block(
    info: ProjectInfo,
    ctx: Optional[MatrixContext],
) -> str:
    """Build version & release section."""
    if not ctx or not ctx.version_source:
        return ""

    lines = ["## Version & Release", ""]

    # Determine the file and current version
    ver_file = ctx.version_source.split("(")[0].strip()
    ver_match = re.search(r'"([^"]+)"', ctx.version_source)
    current_ver = ver_match.group(1) if ver_match else "X.Y.Z"

    lines.append(f"**Single source of truth:** `{ver_file}` — `version = \"{current_ver}\"`")
    lines.append("")

    # Language-specific version workflow from language_config
    lang_info: Optional[LanguageInfo] = None
    for lang in LANGUAGES:
        if lang.version_file and lang.version_file.rstrip("*").rstrip(".") in ver_file:
            lang_info = lang
            break

    if lang_info and lang_info.version_bump_hint:
        # Use per-language release guidance
        if lang_info.key == "python":
            lines.append("`__init__.py` reads via `importlib.metadata` — never edit it manually.")
        lines.append("- Release: push `v*` tag → CI runs tests → build → publish.")
        lines.append(f"- Tag version MUST match {ver_file} version.")
        lines.append("")
        lines.append("```bash")
        lines.append(lang_info.version_bump_hint)
        lines.append("```")
    else:
        lines.append("- Release: bump version → push tag → CI publishes.")
        lines.append(f"- Edit `{ver_file}` to bump version.")

    return "\n".join(lines) + "\n"


def _build_lifecycle_block(
    info: ProjectInfo,
    ctx: Optional[MatrixContext],
) -> str:
    """Build lifecycle guidance section from matrix data."""
    lines = ["## Lifecycle Guidance", ""]

    test_cmd = info.test_command or "run tests"

    # Detect linter command — language-filtered via language_config
    lint_cmd = ""
    detected_lower = {lang.lower() for lang in info.detected_languages}
    # Map common linter names to their CLI invocations
    _LINT_COMMANDS: Dict[str, str] = {
        "ruff": "ruff check", "eslint": "npx eslint .",
        "clippy": "cargo clippy", "golangci-lint": "golangci-lint run",
        "rubocop": "rubocop", "phpstan": "phpstan analyse",
        "swiftlint": "swiftlint", "dart analyze": "dart analyze",
        "detekt": "detekt", "credo": "mix credo",
        "shellcheck": "shellcheck",
    }
    if ctx and ctx.best_practices_parsed:
        for bp in ctx.best_practices_parsed:
            for tool in bp.get("use", []):
                tool_str = str(tool).lower()
                if tool_str in _LC_LINTER_LANG and tool_str in _LINT_COMMANDS:
                    needed = _LC_LINTER_LANG[tool_str]
                    if needed & detected_lower:
                        lint_cmd = _LINT_COMMANDS[tool_str]
                        break
            if lint_cmd:
                break

    verify = f" → `{lint_cmd}`" if lint_cmd else ""

    lines.append(f"- **Bugfix:** Read matrix context → fix root cause → "
                 f"`{test_cmd}`{verify}")

    # Feature / new code guidance
    if ctx and ctx.contributing_steps:
        steps_short = " → ".join(ctx.contributing_steps[:3])
        lines.append(f"- **New feature:** {steps_short} → run full test suite")
    else:
        lines.append(f"- **New feature:** Follow existing patterns → add tests → `{test_cmd}`")

    lines.append(f"- **Refactor:** Use `get_context_for_file()` first → preserve "
                 f"public API → `{test_cmd}`")

    # Release guidance
    if ctx and ctx.version_source:
        ver_file = ctx.version_source.split("(")[0].strip()
        lines.append(f"- **Release:** Bump version in {ver_file} ONLY → verify → push tag")
    else:
        lines.append("- **Release:** Bump version → verify → push tag")

    return "\n".join(lines) + "\n"


def _build_known_pitfalls_block(
    info: ProjectInfo,
    ctx: Optional[MatrixContext],
) -> str:
    """Build known pitfalls section from project analysis."""
    pitfalls: List[str] = []

    if ctx:
        # Cache path pitfall
        pitfalls.append(
            f"- Cache path: `.codetrellis/cache/{ctx.project_name}/` — no version prefix."
        )

        # Python-specific pitfalls
        if "pyproject.toml" in (ctx.version_source or ""):
            pitfalls.append(
                "- `__init__.py` version is read-only (via importlib.metadata) — "
                "editing it directly causes CI version mismatch."
            )

        # Build timestamp
        if "CODETRELLIS_BUILD_TIMESTAMP" in (ctx.runbook or ""):
            pitfalls.append(
                "- `CODETRELLIS_BUILD_TIMESTAMP` env var must be set for "
                "deterministic CI builds."
            )

        # Contributing steps (e.g., parser 4-step integration)
        if len(ctx.contributing_steps) >= 3:
            step_count = len(ctx.contributing_steps)
            pitfalls.append(
                f"- New code integration requires {step_count} coordinated "
                f"changes (see Contributing section)."
            )

    if not pitfalls:
        return ""

    lines = ["## Known Pitfalls", ""]
    lines.extend(pitfalls)
    return "\n".join(lines) + "\n"


def _build_architecture_block(
    info: ProjectInfo,
    ctx: Optional[MatrixContext],
) -> str:
    """Build project architecture / structure block from OVERVIEW data."""
    if not ctx:
        return ""

    lines: List[str] = []

    # Directory structure from OVERVIEW dirs line
    if ctx.project_structure:
        lines.append("## Project Structure")
        lines.append("")
        lines.append("```")
        # Parse dirs:codetrellis(756),scripts(15),...
        dir_entries = ctx.project_structure.split(",")
        for entry in dir_entries:
            entry = entry.strip()
            m = re.match(r'(\S+)\((\d+)\)', entry)
            if m:
                dirname, count = m.group(1), m.group(2)
                lines.append(f"  {dirname}/  ({count} files)")
            elif entry:
                lines.append(f"  {entry}/")
        lines.append("```")

    # Data flow pattern
    if ctx.data_flow_pattern:
        lines.append("")
        lines.append(f"**Primary pattern:** {ctx.data_flow_pattern}")

    if not lines:
        return ""

    return "\n".join(lines) + "\n"


def _build_mcp_tools_block(
    info: ProjectInfo,
    ctx: Optional[MatrixContext],
) -> str:
    """Build the MCP tools reference block."""
    section_count = ctx.section_count if ctx else 34

    # Build example section list from actual sections
    _PREFERRED = [
        "OVERVIEW", "PROJECT", "PYTHON_TYPES", "TS_TYPES", "JS_TYPES",
        "JAVA_TYPES", "GO_TYPES", "RUST_TYPES", "ROUTES", "ROUTES_SEMANTIC",
        "HTTP_API", "RUNBOOK", "BUSINESS_DOMAIN", "CLI_COMMANDS",
        "IMPLEMENTATION_LOGIC", "INFRASTRUCTURE", "BEST_PRACTICES",
    ]
    if ctx and ctx.sections:
        examples = [s for s in _PREFERRED if s in ctx.sections]
        section_examples = ", ".join(examples[:8]) + ", etc." if examples else "OVERVIEW, RUNBOOK, etc."
    else:
        section_examples = "OVERVIEW, RUNBOOK, BEST_PRACTICES, etc."

    cache_name = ctx.project_name if ctx else info.name

    return f"""## CodeTrellis Matrix

This project uses **CodeTrellis** for AI context injection. The full project matrix is available via:

- **MCP Server:** Registered in `.vscode/mcp.json` — provides tools to query the entire project.
- **Matrix file:** `.codetrellis/cache/{cache_name}/matrix.prompt`

### ⚠️ IMPORTANT: Always use the CodeTrellis MCP tools FIRST

**Before running `find`, `grep`, `ls`, or reading files manually**, use the CodeTrellis MCP server
tools below. They return the full project context in one call and save hundreds of file reads.

### MCP Server Tools

| Tool | When to Use |
|------|-------------|
| `search_matrix(query)` | **Use FIRST** for any question — searches all {section_count} sections |
| `get_section(name)` | Get a specific section: {section_examples} |
| `get_context_for_file(path)` | **Before editing any file** — returns types, deps, APIs for that file |
| `get_skills()` | List auto-generated AI skills |
| `get_cache_stats()` | Cache optimization statistics |
"""

def generate_copilot_instructions(info: ProjectInfo, ctx: Optional[MatrixContext] = None) -> str:
    """Generate .github/copilot-instructions.md with real project data."""
    languages = ", ".join(info.detected_languages)

    # Project description
    if ctx and ctx.project_type:
        project_desc = f"**{ctx.project_name}** — {ctx.project_type}"
    else:
        project_desc = f"**{info.name}** — {info.project_type}"

    # Stats
    key_stats = ""
    if ctx:
        stats_parts = []
        if ctx.total_files:
            stats_parts.append(f"{ctx.total_files} files scanned")
        if ctx.type_count:
            stats_parts.append(f"{ctx.type_count} types extracted")
        if ctx.section_count:
            stats_parts.append(f"{ctx.section_count} matrix sections")
        if stats_parts:
            key_stats = f"\n**Matrix Stats:** {', '.join(stats_parts)}\n"

    # Domain
    domain_section = ""
    if ctx and ctx.business_domain and ctx.business_purpose:
        domain_section = f"""
- **Domain:** {ctx.business_domain}
- **Purpose:** {ctx.business_purpose}
"""

    # Build shared blocks
    mcp_block = _build_mcp_tools_block(info, ctx)
    conventions_block = _build_conventions_block(info, ctx)
    quality_gates_block = _build_quality_gates_block(info, ctx)
    version_block = _build_version_block(info, ctx)
    lifecycle_block = _build_lifecycle_block(info, ctx)
    architecture_block = _build_architecture_block(info, ctx)
    pitfalls_block = _build_known_pitfalls_block(info, ctx)

    # CLI commands
    commands_section = ""
    if ctx and ctx.cli_commands:
        # Parse into a compact table
        cmd_lines = ctx.cli_commands.strip().split("\n")
        table_rows = []
        for line in cmd_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Format: "  command - description|file.py"
            m = re.match(r'\s*(\S+)\s*-\s*(.+?)(?:\|.*)?$', line)
            if m:
                table_rows.append(f"| `{m.group(1)}` | {m.group(2).strip()} |")
        if table_rows:
            commands_section = "\n## CLI Commands (key subset)\n\n"
            commands_section += "| Command | Purpose |\n| ------- | ------- |\n"
            # Limit to 12 most important commands
            commands_section += "\n".join(table_rows[:12]) + "\n"

    # Runbook (only if no quality gates were detected — otherwise it's redundant)
    runbook_section = ""
    if ctx and ctx.runbook and not quality_gates_block:
        runbook_section = f"""
## Runbook (Build / Run / Test)

```
{ctx.runbook}
```
"""

    return f"""# GitHub Copilot — Project Instructions for {info.name}

> Auto-generated by CodeTrellis (`codetrellis init --ai`), enhanced with matrix-derived project context.
> Read automatically by GitHub Copilot in VS Code for every chat and inline completion.

## Project Overview

{project_desc}

- **Languages:** {languages}
{key_stats}{domain_section}
{mcp_block}
{conventions_block}
{quality_gates_block}
{version_block}
{lifecycle_block}
{architecture_block}
{commands_section}
{pitfalls_block}
{runbook_section}"""


def generate_vscode_mcp(info: ProjectInfo, ctx: Optional[MatrixContext] = None) -> str:
    """Generate .vscode/mcp.json content."""
    config = {
        "servers": {
            "codetrellis": {
                "type": "stdio",
                "command": info.python_executable,
                "args": [
                    "-m",
                    "codetrellis",
                    "mcp",
                    str(info.root),
                ],
                "env": {},
            }
        }
    }
    return json.dumps(config, indent=2) + "\n"


def generate_vscode_tasks(info: ProjectInfo, ctx: Optional[MatrixContext] = None) -> str:
    """Generate .vscode/tasks.json content."""
    tasks = [
        {
            "label": "CodeTrellis: Watch Mode",
            "type": "shell",
            "command": f"codetrellis watch {info.root}",
            "isBackground": True,
            "problemMatcher": [],
            "group": "build",
            "presentation": {
                "echo": True,
                "reveal": "silent",
                "focus": False,
                "panel": "dedicated",
                "showReuseMessage": False,
            },
            "runOptions": {"runOn": "folderOpen"},
        },
        {
            "label": "CodeTrellis: Scan (Optimal)",
            "type": "shell",
            "command": f"codetrellis scan {info.root} --optimal",
            "group": "build",
            "problemMatcher": [],
            "presentation": {"echo": True, "reveal": "always", "panel": "shared"},
        },
        {
            "label": "CodeTrellis: Scan (Incremental)",
            "type": "shell",
            "command": f"codetrellis scan {info.root} --incremental",
            "group": "build",
            "problemMatcher": [],
            "presentation": {"echo": True, "reveal": "always", "panel": "shared"},
        },
        {
            "label": "CodeTrellis: Verify Build",
            "type": "shell",
            "command": f"codetrellis verify {info.root}",
            "group": "test",
            "problemMatcher": [],
            "presentation": {"echo": True, "reveal": "always", "panel": "shared"},
        },
    ]

    # Add project-specific test task
    if info.test_command:
        tasks.append({
            "label": f"{info.name}: Run Tests",
            "type": "shell",
            "command": info.test_command,
            "group": "test",
            "problemMatcher": [],
            "presentation": {"echo": True, "reveal": "always", "panel": "shared"},
        })

    config = {"version": "2.0.0", "tasks": tasks}
    return json.dumps(config, indent=2) + "\n"


def generate_claude_md(info: ProjectInfo, ctx: Optional[MatrixContext] = None) -> str:
    """Generate CLAUDE.md with real project data from the matrix."""
    languages = ", ".join(info.detected_languages)

    # Project description
    if ctx and ctx.project_type:
        project_desc = f"**{ctx.project_name}** ({ctx.project_type})"
    else:
        project_desc = f"**{info.name}** ({info.project_type})"

    # Stats + domain
    stats_line = ""
    domain_section = ""
    if ctx:
        stats_parts = []
        if ctx.total_files:
            stats_parts.append(f"{ctx.total_files} files")
        if ctx.type_count:
            stats_parts.append(f"{ctx.type_count} types")
        if ctx.section_count:
            stats_parts.append(f"{ctx.section_count} matrix sections")
        if stats_parts:
            stats_line = f"\n- **Scale:** {', '.join(stats_parts)}"
        if ctx.business_domain and ctx.business_purpose:
            domain_section = f"\n- **Domain:** {ctx.business_domain} — {ctx.business_purpose}"

    # Dynamic type section / file examples
    type_section_name = "PYTHON_TYPES"
    example_file = "codetrellis/scanner.py"
    if ctx:
        if ctx.primary_type_section:
            type_section_name = ctx.primary_type_section
        if ctx.primary_language:
            lang = ctx.primary_language.lower()
            ext_map = {"python": ".py", "typescript": ".ts", "javascript": ".js",
                       "java": ".java", "go": ".go", "rust": ".rs", "c#": ".cs",
                       "ruby": ".rb", "php": ".php", "swift": ".swift", "kotlin": ".kt"}
            ext = ext_map.get(lang, ".py")
            dir_map = {"python": "src/", "typescript": "src/", "javascript": "src/",
                       "java": "src/main/java/", "go": "cmd/", "rust": "src/",
                       "c#": "src/", "ruby": "lib/", "php": "src/"}
            prefix = dir_map.get(lang, "src/")
            example_file = f"{prefix}example{ext}"

    # Build shared blocks
    architecture_block = _build_architecture_block(info, ctx)
    conventions_block = _build_conventions_block(info, ctx)
    quality_gates_block = _build_quality_gates_block(info, ctx)
    version_block = _build_version_block(info, ctx)
    lifecycle_block = _build_lifecycle_block(info, ctx)
    pitfalls_block = _build_known_pitfalls_block(info, ctx)

    # Quick commands — language-aware
    test_cmd = info.test_command or "pytest tests/ -x -q --timeout=120"
    quick_cmds = f"""```bash
# Scan project (generates matrix)
codetrellis scan . --optimal

# Incremental rebuild (only changed files)
codetrellis scan . --incremental

# Update AI files after upgrading CodeTrellis (no re-scan)
codetrellis init . --update-ai

# Watch mode (auto-rebuild on save)
codetrellis watch

# Get prompt-ready matrix
codetrellis prompt

# Run tests
{test_cmd}
```"""

    # CI/CD section from runbook
    ci_section = ""
    if ctx and ctx.ci_jobs:
        ci_section = "\n## CI/CD Pipelines\n\n"
        if ctx.ci_triggers:
            ci_section += f"**Triggers:** {ctx.ci_triggers}\n\n"
        ci_section += "**Jobs:**\n"
        for i, job in enumerate(ctx.ci_jobs, 1):
            ci_section += f"{i}. **{job}**\n"

    return f"""# CLAUDE.md — {info.name} Project Memory

> Auto-generated by CodeTrellis (`codetrellis init --ai`), enhanced with matrix-derived project context.
> Read by Claude Code at the start of every session.

## Project

{project_desc}

- **Languages:** {languages}{domain_section}{stats_line}

## ⚠️ CRITICAL — Read the Matrix FIRST

Before exploring files manually, **read the full project matrix**:

```bash
cat .codetrellis/cache/{info.name}/matrix.prompt
```

This file contains the ENTIRE project context compressed for AI consumption.
**Always read the matrix before running `find`, `grep`, or `ls` commands.**

Get specific sections:

```bash
# Get types
codetrellis export . --section {type_section_name}

# Get project overview
codetrellis export . --section OVERVIEW

# Get context for a specific file you're editing
codetrellis context . --file {example_file}
```

{architecture_block}

## Quick Commands

{quick_cmds}
{ci_section}
{quality_gates_block}
{conventions_block}
{lifecycle_block}
{version_block}
{pitfalls_block}
"""


def generate_cursorrules(info: ProjectInfo, ctx: Optional[MatrixContext] = None) -> str:
    """Generate .cursorrules with real project data — at parity with copilot-instructions."""
    languages = ", ".join(info.detected_languages)

    # Project description
    if ctx and ctx.project_type:
        project_desc = f"**{ctx.project_name}** — {ctx.project_type}"
    else:
        project_desc = f"**{info.name}** — {info.project_type}"

    # Stats + domain
    stats_line = ""
    domain_section = ""
    if ctx:
        stats_parts = []
        if ctx.total_files:
            stats_parts.append(f"{ctx.total_files} files")
        if ctx.type_count:
            stats_parts.append(f"{ctx.type_count} types")
        if ctx.section_count:
            stats_parts.append(f"{ctx.section_count} matrix sections")
        if stats_parts:
            stats_line = f"\n- **Scale:** {', '.join(stats_parts)}"
        if ctx.business_domain and ctx.business_purpose:
            domain_section = f"\n- **Domain:** {ctx.business_domain} — {ctx.business_purpose}"

    # Build shared blocks
    mcp_block = _build_mcp_tools_block(info, ctx)
    architecture_block = _build_architecture_block(info, ctx)
    conventions_block = _build_conventions_block(info, ctx)
    quality_gates_block = _build_quality_gates_block(info, ctx)
    version_block = _build_version_block(info, ctx)
    lifecycle_block = _build_lifecycle_block(info, ctx)
    pitfalls_block = _build_known_pitfalls_block(info, ctx)

    return f"""# Cursor Rules — {info.name}

> Auto-generated by CodeTrellis (`codetrellis init --ai`), enhanced with matrix-derived project context.

## Project Context

{project_desc}

- **Languages:** {languages}{domain_section}{stats_line}

{mcp_block}
{architecture_block}
{conventions_block}
{quality_gates_block}
{version_block}
{lifecycle_block}
{pitfalls_block}
"""


# ---------------------------------------------------------------------------
# Agent file generation
# ---------------------------------------------------------------------------

def _build_agent_project_context(info: ProjectInfo, ctx: Optional[MatrixContext] = None) -> str:
    """Build a compact project context block for agent files."""
    parts: List[str] = []
    if ctx and ctx.data_flow_pattern:
        parts.append(f"- **Architecture:** {ctx.data_flow_pattern}")
    if ctx and ctx.primary_language:
        parts.append(f"- **Primary language:** {ctx.primary_language}")
    if ctx and ctx.python_version:
        parts.append(f"- **Python:** {ctx.python_version}")
    if ctx and ctx.version_source:
        parts.append(f"- **Version source:** {ctx.version_source}")
    if not parts:
        languages = ", ".join(info.detected_languages)
        parts.append(f"- **Languages:** {languages}")
    return "\n".join(parts)


def generate_agent_files(
    info: ProjectInfo, ctx: Optional[MatrixContext] = None,
) -> List[tuple]:
    """Generate agent .md files for the .github/agents/ directory.

    Returns list of (relative_path, content, description) tuples.
    """
    project_context = _build_agent_project_context(info, ctx)

    # Build quality checks from best practices
    quality_checks = ""
    if ctx and ctx.best_practices_parsed:
        checks: List[str] = []
        for bp in ctx.best_practices_parsed:
            for item in bp.get("use", []):
                if any(kw in item.lower() for kw in ["lint", "check", "test", "mypy", "ruff", "eslint", "pytest"]):
                    checks.append(f"- `{item}`")
        if checks:
            quality_checks = "\n## Post-Change Quality Checks\n\n" + "\n".join(checks[:6])
    if not quality_checks and info.test_command:
        quality_checks = f"\n## Post-Change Quality Checks\n\n- `{info.test_command}`"

    # Key conventions
    conventions_summary = ""
    if ctx and ctx.contributing_steps:
        steps = [f"- {s}" for s in ctx.contributing_steps[:5]]
        conventions_summary = "\n## Key Conventions\n\n" + "\n".join(steps)

    agents = [
        (
            ".github/agents/ct-research.agent.md",
            f"""---
name: ct-research
description: "Use when: exploring the codebase, collecting evidence, identifying architecture paths, and preparing context for another agent."
tools: ["search", "fetch", "runCommands", "codetrellis/*"]
user-invocable: false
---

# CodeTrellis Research Agent

You are a read-heavy specialist for the **{info.name}** project.

## Primary Responsibilities

- identify relevant files and subsystems
- extract architecture and dependency relationships
- find existing implementation patterns
- gather evidence before edits are attempted

## Rules

- Start with CodeTrellis MCP tools (`search_matrix`, `get_section`, `get_context_for_file`).
- Read `.codetrellis/cache/{info.name}/matrix.prompt` before manual exploration.
- Prefer targeted retrieval over broad file dumps.
- Return concise findings with concrete file paths.
- Do not edit files unless explicitly instructed by the parent agent.

## Project Context

{project_context}

## Output Format

Return:

1. relevant files
2. key findings
3. assumptions
4. recommended next action
""",
            "Research agent — codebase exploration and evidence gathering",
        ),
        (
            ".github/agents/ct-implement.agent.md",
            f"""---
name: ct-implement
description: "Use when: writing or modifying code after the task scope is clear and relevant context has already been gathered."
tools: ["search", "edit", "runCommands", "runTasks", "codetrellis/*"]
user-invocable: false
---

# CodeTrellis Implementation Agent

You are the execution specialist for the **{info.name}** project.

## Primary Responsibilities

- apply the smallest correct code change
- preserve project style and public APIs unless the task requires change
- update docs or tests only when necessary for the task

## Rules

- Assume the parent agent already narrowed the scope.
- Re-check file-specific context with `get_context_for_file(path)` before editing.
- Fix the root cause instead of layering workaround logic.
- Avoid unrelated cleanup.
- Provide a short summary of what changed and what still needs verification.
{conventions_summary}
{quality_checks}

## Output Format

Return:

1. files changed
2. root-cause fix summary
3. tests or checks run
4. known risks or follow-ups
""",
            "Implementation agent — code changes and fixes",
        ),
        (
            ".github/agents/ct-verify.agent.md",
            f"""---
name: ct-verify
description: "Use when: validating a plan or implementation for correctness, regressions, missing tests, and unsupported claims."
tools: ["search", "runCommands", "runTasks", "codetrellis/*"]
user-invocable: false
---

# CodeTrellis Verification Agent

You are the quality gate for the **{info.name}** project.

## Primary Responsibilities

- confirm code correctness
- spot regressions or missing test coverage
- validate claims made by other agents
- check for security and performance issues

## Rules

- Run applicable quality checks before approving.
- Cross-reference changes against `get_context_for_file(path)` output.
- Flag any drift from established patterns.
- Never approve changes blindly — read the diff.

## Project Context

{project_context}
{quality_checks}

## Output Format

Return:

1. pass / fail verdict
2. issues found (with file + line)
3. tests status
4. recommendations
""",
            "Verification agent — quality gate validation",
        ),
        (
            ".github/agents/ct-orchestrator.agent.md",
            f"""---
name: ct-orchestrator
description: "Use when: coordinating one task across research, implementation, and verification agents with shared context and a single final answer."
tools: ["search", "edit", "runCommands", "runTasks", "codetrellis/*"]
user-invocable: true
---

# CodeTrellis Orchestrator Agent

You coordinate multi-step tasks for the **{info.name}** project by delegating to specialized agents.

## Workflow

1. **Research phase** — delegate to `ct-research` to gather context
2. **Implementation phase** — delegate to `ct-implement` with narrowed scope
3. **Verification phase** — delegate to `ct-verify` to validate changes

## Rules

- Always start by reading `.codetrellis/cache/{info.name}/matrix.prompt`.
- Use MCP tools (`search_matrix`, `get_section`, `get_context_for_file`) for project context.
- Break complex tasks into discrete, verifiable steps.
- Maintain shared context between agent phases.
- Return a single consolidated answer to the user.

## Project Context

{project_context}

## Output Format

Return:

1. task breakdown
2. phase results (research → implementation → verification)
3. final answer
4. follow-up recommendations
""",
            "Orchestrator agent — multi-step task coordination",
        ),
    ]

    return agents


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_ai_integrations(
    project_root: Path,
    force: bool = False,
) -> List[GeneratedFile]:
    """
    Generate all AI integration files, enriched with matrix data if available.

    This should be called AFTER scan completes so the matrix provides
    real project knowledge to the templates.

    Args:
        project_root: Absolute path to the project root.
        force: If True, overwrite existing files.

    Returns:
        List of GeneratedFile objects describing what was created.
    """
    info = detect_project(project_root)

    # Try to load matrix context (will exist if scan ran first)
    ctx = extract_matrix_context(project_root)
    if ctx:
        print(f"  📊 Matrix loaded: {ctx.section_count} sections, {ctx.total_files} files, {ctx.type_count} types")
    else:
        print("  ⚠️  No matrix found — generating basic templates (run scan first for richer output)")

    results: List[GeneratedFile] = []

    # All generators accept (info, ctx) — ctx can be None for basic mode
    file_specs = [
        (
            project_root / ".vscode" / "mcp.json",
            generate_vscode_mcp(info, ctx),
            "VS Code MCP server config (Copilot + MCP integration)",
        ),
        (
            project_root / ".github" / "copilot-instructions.md",
            generate_copilot_instructions(info, ctx),
            "GitHub Copilot auto-loaded project instructions",
        ),
        (
            project_root / ".vscode" / "tasks.json",
            generate_vscode_tasks(info, ctx),
            "VS Code tasks (watch, scan, verify, test)",
        ),
        (
            project_root / "CLAUDE.md",
            generate_claude_md(info, ctx),
            "Claude Code auto-loaded project memory",
        ),
        (
            project_root / ".cursorrules",
            generate_cursorrules(info, ctx),
            "Cursor auto-loaded project rules",
        ),
    ]

    # Add agent files
    for rel_path, content, description in generate_agent_files(info, ctx):
        file_specs.append((
            project_root / rel_path,
            content,
            description,
        ))

    for file_path, content, description in file_specs:
        gf = GeneratedFile(path=file_path, content=content, description=description)

        if file_path.exists() and not force:
            print(f"  ⏭️  {file_path.relative_to(project_root)} (exists, use --force to overwrite)")
            continue

        if file_path.exists():
            gf.overwritten = True

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        results.append(gf)

        status = "🔄 overwritten" if gf.overwritten else "✅ created"
        print(f"  {status}  {file_path.relative_to(project_root)}")

    return results
