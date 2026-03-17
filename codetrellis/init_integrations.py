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

    Args:
        project_root: Absolute path to the project root.

    Returns:
        A populated ProjectInfo dataclass.
    """
    info = ProjectInfo(name=project_root.name, root=project_root)

    # --- Python ---
    pyproject = project_root / "pyproject.toml"
    setup_py = project_root / "setup.py"
    requirements = project_root / "requirements.txt"
    if pyproject.exists():
        info.has_pyproject = True
        info.detected_languages.append("Python")
        info.project_type = "Python Library"
        _detect_python_frameworks(project_root, info)
    elif setup_py.exists() or requirements.exists():
        info.detected_languages.append("Python")
        info.project_type = "Python Project"
        _detect_python_frameworks(project_root, info)

    # --- Node.js / TypeScript ---
    package_json = project_root / "package.json"
    if package_json.exists():
        info.has_package_json = True
        if "TypeScript" not in info.detected_languages:
            info.detected_languages.append("TypeScript")
        if not info.detected_languages or info.project_type == "Unknown":
            info.project_type = "Node.js Project"
        _detect_node_frameworks(package_json, info)

    # --- Go ---
    go_mod = project_root / "go.mod"
    if go_mod.exists():
        info.has_go_mod = True
        info.detected_languages.append("Go")
        if info.project_type == "Unknown":
            info.project_type = "Go Project"

    # --- Rust ---
    cargo_toml = project_root / "Cargo.toml"
    if cargo_toml.exists():
        info.has_cargo_toml = True
        info.detected_languages.append("Rust")
        if info.project_type == "Unknown":
            info.project_type = "Rust Project"

    # --- Java / Kotlin ---
    if (project_root / "pom.xml").exists() or (project_root / "build.gradle").exists():
        info.detected_languages.append("Java")
        if info.project_type == "Unknown":
            info.project_type = "Java Project"

    # --- C# ---
    if list(project_root.glob("*.csproj")) or list(project_root.glob("*.sln")):
        info.detected_languages.append("C#")
        if info.project_type == "Unknown":
            info.project_type = "C# Project"

    # --- Tests ---
    tests_dir = project_root / "tests"
    test_dir = project_root / "test"
    spec_dir = project_root / "spec"
    if tests_dir.is_dir() or test_dir.is_dir():
        info.has_tests = True
    if spec_dir.is_dir():
        info.has_tests = True

    # Determine test command
    if "Python" in info.detected_languages:
        info.test_command = "pytest tests/ -x -q"
    elif info.has_package_json:
        info.test_command = "npm test"
    elif info.has_go_mod:
        info.test_command = "go test ./..."
    elif info.has_cargo_toml:
        info.test_command = "cargo test"

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
    ctx.project_structure = _extract_section(content, "PROJECT_STRUCTURE")
    ctx.infrastructure = _extract_section(content, "INFRASTRUCTURE")
    ctx.actionable_items = _extract_section(content, "ACTIONABLE_ITEMS")

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


# ---------------------------------------------------------------------------
# Template generators (enriched with matrix context)
# ---------------------------------------------------------------------------

def generate_copilot_instructions(info: ProjectInfo, ctx: Optional[MatrixContext] = None) -> str:
    """Generate .github/copilot-instructions.md with real project data."""
    languages = ", ".join(info.detected_languages)
    frameworks = ", ".join(info.detected_frameworks) if info.detected_frameworks else "None detected"

    # --- Build enriched sections from matrix ---
    project_desc = f"**{info.name}** — {info.project_type}"
    domain_section = ""
    architecture_section = ""
    runbook_section = ""
    commands_section = ""
    key_stats = ""

    if ctx:
        if ctx.project_type:
            project_desc = f"**{ctx.project_name}** — {ctx.project_type}"
        if ctx.business_domain and ctx.business_purpose:
            domain_section = f"""
## Business Domain

- **Domain:** {ctx.business_domain}
- **Purpose:** {ctx.business_purpose}
"""
        if ctx.project_structure:
            # Truncate to first 30 lines to keep file readable
            structure_lines = ctx.project_structure.split("\n")[:30]
            structure_text = "\n".join(structure_lines)
            if len(ctx.project_structure.split("\n")) > 30:
                structure_text += "\n..."
            architecture_section = f"""
## Project Structure

```
{structure_text}
```
"""
        if ctx.runbook:
            runbook_section = f"""
## Runbook (Build / Run / Test)

```
{ctx.runbook}
```
"""
        if ctx.cli_commands:
            commands_section = f"""
## CLI Commands

```
{ctx.cli_commands}
```
"""
        stats_parts = []
        if ctx.total_files:
            stats_parts.append(f"{ctx.total_files} files scanned")
        if ctx.type_count:
            stats_parts.append(f"{ctx.type_count} types extracted")
        if ctx.section_count:
            stats_parts.append(f"{ctx.section_count} matrix sections")
        if stats_parts:
            key_stats = f"\n**Matrix Stats:** {', '.join(stats_parts)}\n"

    test_line = ""
    if info.test_command:
        test_line = f"3. **Testing:** Run tests with `{info.test_command}`.\n"

    section_count = ctx.section_count if ctx else 34

    # Build a dynamic list of example section names from actual matrix sections
    # Prioritise well-known sections the user is most likely to request
    _PREFERRED_EXAMPLES = [
        "OVERVIEW", "PROJECT", "PYTHON_TYPES", "TS_TYPES", "JS_TYPES",
        "JAVA_TYPES", "GO_TYPES", "RUST_TYPES", "ROUTES", "ROUTES_SEMANTIC",
        "HTTP_API", "COMPONENTS", "INTERFACES", "TYPES", "SCHEMAS", "ENUMS",
        "RUNBOOK", "BUSINESS_DOMAIN", "CLI_COMMANDS", "IMPLEMENTATION_LOGIC",
        "INFRASTRUCTURE", "ERROR_HANDLING", "CONTROLLERS", "ANGULAR_SERVICES",
        "NESTJS_MODULES", "CONTEXT", "ACTIONABLE_ITEMS",
    ]
    if ctx and ctx.sections:
        example_sections = [s for s in _PREFERRED_EXAMPLES if s in ctx.sections]
        # Cap at ~8 examples to keep the table readable
        section_examples = ", ".join(example_sections[:8]) + ", etc." if example_sections else "OVERVIEW, RUNBOOK, etc."
    else:
        section_examples = "OVERVIEW, PYTHON_TYPES, TS_TYPES, ROUTES, HTTP_API, RUNBOOK, BUSINESS_DOMAIN, CLI_COMMANDS, etc."

    return f"""# GitHub Copilot — Project Instructions for {info.name}

> Auto-generated by CodeTrellis (`codetrellis init --ai`).
> Read automatically by GitHub Copilot in VS Code for every chat and inline completion.

## Project Overview

{project_desc}
- **Languages:** {languages}
- **Frameworks:** {frameworks}
{key_stats}{domain_section}
## CodeTrellis Matrix

This project uses **CodeTrellis** for AI context injection. The full project matrix is available via:
- **MCP Server:** Registered in `.vscode/mcp.json` — provides tools to query the entire project.
- **Matrix file:** `.codetrellis/cache/{info.name}/matrix.prompt`

### ⚠️ IMPORTANT: Always use the CodeTrellis MCP tools FIRST

**Before running `find`, `grep`, `ls`, or reading files manually**, use the CodeTrellis MCP server
tools below. They return the full project context in one call and save hundreds of file reads.
Prefer the CodeTrellis MCP tools for all project exploration and code understanding tasks.

### MCP Server Tools

| Tool | When to Use |
|------|-------------|
| `search_matrix(query)` | **Use FIRST** for any question about the project — searches all {section_count} sections |
| `get_section(name)` | Get a specific section: {section_examples} |
| `get_context_for_file(path)` | **Use before editing any file** — returns types, deps, and APIs relevant to that file |
| `get_skills()` | List auto-generated AI skills for this project |
| `get_cache_stats()` | Cache optimization statistics |

## Key Conventions

1. **Language:** {languages}. Follow existing patterns in the codebase.
2. **Error handling:** Follow the project's established error handling patterns.
{test_line}{architecture_section}{runbook_section}{commands_section}"""


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
    frameworks = ", ".join(info.detected_frameworks) if info.detected_frameworks else "None detected"

    # Enriched sections
    domain_line = ""
    purpose_line = ""
    structure_section = ""
    runbook_block = ""
    stats_line = ""
    proj_type = info.project_type

    if ctx:
        if ctx.project_type:
            proj_type = ctx.project_type
        if ctx.business_domain:
            domain_line = f"\n- **Domain:** {ctx.business_domain}"
        if ctx.business_purpose:
            purpose_line = f"\n- **Purpose:** {ctx.business_purpose}"
        if ctx.project_structure:
            structure_lines = ctx.project_structure.split("\n")[:25]
            structure_text = "\n".join(structure_lines)
            if len(ctx.project_structure.split("\n")) > 25:
                structure_text += "\n..."
            structure_section = f"""
## Project Structure

```
{structure_text}
```
"""
        if ctx.runbook:
            runbook_block = f"""
## Runbook

```
{ctx.runbook}
```
"""
        stats_parts = []
        if ctx.total_files:
            stats_parts.append(f"{ctx.total_files} files")
        if ctx.type_count:
            stats_parts.append(f"{ctx.type_count} types")
        if ctx.section_count:
            stats_parts.append(f"{ctx.section_count} matrix sections")
        if stats_parts:
            stats_line = f"\n- **Scale:** {', '.join(stats_parts)}"

    test_line = ""
    if info.test_command:
        test_line = f"\n# Run tests\n{info.test_command}\n"

    return f"""# CLAUDE.md — {info.name} Project Memory

> Auto-generated by CodeTrellis (`codetrellis init --ai`).
> Read by Claude Code at the start of every session.

## Project

**{info.name}** — {proj_type}
- **Languages:** {languages}
- **Frameworks:** {frameworks}{domain_line}{purpose_line}{stats_line}

## ⚠️ CRITICAL — Read the Matrix FIRST

Before exploring files manually, **read the full project matrix**:

```bash
cat .codetrellis/cache/{info.name}/matrix.prompt
```

This file contains the ENTIRE project context: all types, APIs, routes, schemas,
implementation logic, infrastructure, business domain, best practices, and TODOs.
It is compressed into ~15K tokens and saves you hundreds of file reads.

**Always read the matrix before running `find`, `grep`, or `ls` commands.**

You can also get specific sections:
```bash
# Get just types
codetrellis export . --section TS_TYPES

# Get just the project overview
codetrellis export . --section OVERVIEW

# Get context for a specific file you're editing
codetrellis context . --file src/path/to/file.ts
```

## Quick Commands

```bash
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
{test_line}```
{structure_section}{runbook_block}
## Conventions

- Follow existing patterns in the codebase.
- Follow the project's established error handling patterns.
- Write tests for new code.
"""


def generate_cursorrules(info: ProjectInfo, ctx: Optional[MatrixContext] = None) -> str:
    """Generate .cursorrules with real project data."""
    languages = ", ".join(info.detected_languages)
    frameworks = ", ".join(info.detected_frameworks) if info.detected_frameworks else "None detected"

    domain_line = ""
    purpose_line = ""
    structure_section = ""
    stats_line = ""
    proj_type = info.project_type

    if ctx:
        if ctx.project_type:
            proj_type = ctx.project_type
        if ctx.business_domain:
            domain_line = f"\n- **Domain:** {ctx.business_domain}"
        if ctx.business_purpose:
            purpose_line = f"\n- **Purpose:** {ctx.business_purpose}"
        if ctx.project_structure:
            structure_lines = ctx.project_structure.split("\n")[:25]
            structure_text = "\n".join(structure_lines)
            if len(ctx.project_structure.split("\n")) > 25:
                structure_text += "\n..."
            structure_section = f"""
## Project Structure

```
{structure_text}
```
"""
        stats_parts = []
        if ctx.total_files:
            stats_parts.append(f"{ctx.total_files} files")
        if ctx.type_count:
            stats_parts.append(f"{ctx.type_count} types")
        if ctx.section_count:
            stats_parts.append(f"{ctx.section_count} sections in matrix")
        if stats_parts:
            stats_line = f"\n- **Scale:** {', '.join(stats_parts)}"

    return f"""# Cursor Rules — {info.name}

## Project Context

**{info.name}** — {proj_type}
- **Languages:** {languages}
- **Frameworks:** {frameworks}{domain_line}{purpose_line}{stats_line}

## ⚠️ CRITICAL — Read the Matrix FIRST

Before exploring files manually, **read the full project matrix**:

```
.codetrellis/cache/{info.name}/matrix.prompt
```

This file contains the ENTIRE project context compressed into ~15K tokens.
Read it before running file searches. It has all types, APIs, routes, schemas,
implementation logic, infrastructure, business domain, best practices, and TODOs.

If MCP tools are available, use `search_matrix`, `get_section`, and `get_context_for_file`
from the CodeTrellis MCP server (registered in `.vscode/mcp.json`).
{structure_section}
## Conventions

- Follow existing patterns in the codebase.
- Follow the project's established error handling patterns.
- Write tests for new code.
"""


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
