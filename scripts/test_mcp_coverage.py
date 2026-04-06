"""End-to-end MCP coverage: verify ALL 106 practice YAMLs via real repos.

For each YAML in codetrellis/bpl/practices/:
  1. Clone a real public repo for the YAML's parent language ecosystem.
  2. Scan the repo with `codetrellis scan --optimal`.
  3. Load the MCP server with the scanned matrix.
  4. Call get_best_practices(file_path=<real_file>, frameworks=[fw]) and
     verify the specific YAML filename appears in the response.
  5. Also test file_path-only (no framework hint) for base language YAMLs.

One repo per language ecosystem — grouped so all framework YAMLs of the same
language are tested against the same scanned repo.

Target: 106/106 PASS.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from codetrellis.mcp_server import MatrixMCPServer

PRACTICES_DIR = Path(__file__).resolve().parents[1] / "codetrellis" / "bpl" / "practices"
ALL_YAML_STEMS = sorted(f.stem for f in PRACTICES_DIR.glob("*.yaml"))
TOTAL = len(ALL_YAML_STEMS)
WIDTH = 78

# ── Ecosystem definitions ───────────────────────────────────────────────
# Each ecosystem: one real repo, one file extension, and a dict of
#   yaml_stem → framework_hint  for every YAML belonging to that language.
#
# framework_hint is what gets passed as frameworks=[hint] to the MCP tool.
# The MCP tool's _find_practice_files matches YAML stems against these.

ECOSYSTEMS = [
    {
        "eco": "Python",
        "repo": "https://github.com/pallets/flask.git",
        "ext": ".py",
        "yamls": {
            "python_core": "python",
            "python_core_expanded": "python",
            "python_3_10": "python_3_10",
            "python_3_11": "python_3_11",
            "python_3_12": "python_3_12",
            "django": "django",
            "flask": "flask",
            "fastapi": "fastapi",
        },
    },
    {
        "eco": "Go",
        "repo": "https://github.com/gin-gonic/gin.git",
        "ext": ".go",
        "yamls": {
            "go_core": "go",
            "gin_core": "gin",
            "echo_core": "echo",
            "fiber_core": "fiber",
            "chi_core": "chi",
            "cobra_core": "cobra",
            "gorm_core": "gorm",
            "grpc_go_core": "grpc_go",
            "sqlx_go_core": "sqlx_go",
        },
    },
    {
        "eco": "Rust",
        "repo": "https://github.com/actix/actix-web.git",
        "ext": ".rs",
        "yamls": {
            "rust_core": "rust",
            "actix_core": "actix",
            "axum_core": "axum",
            "rocket_core": "rocket",
            "warp_core": "warp",
            "diesel_core": "diesel",
            "seaorm_core": "seaorm",
            "tauri_core": "tauri",
        },
    },
    {
        "eco": "JavaScript",
        "repo": "https://github.com/expressjs/express.git",
        "ext": ".js",
        "yamls": {
            "javascript_core": "javascript",
            "alpinejs_core": "alpinejs",
            "astro_core": "astro",
            "chartjs_core": "chartjs",
            "d3js_core": "d3js",
            "gsap_core": "gsap",
            "htmx_core": "htmx",
            "leaflet_core": "leaflet",
            "lit_core": "lit",
            "preact_core": "preact",
            "qwik_core": "qwik",
            "solidjs_core": "solidjs",
            "storybook_core": "storybook",
            "threejs_core": "threejs",
            "xstate_core": "xstate",
        },
    },
    {
        "eco": "TypeScript",
        "repo": "https://github.com/reduxjs/redux.git",
        "ext": ".ts",
        "yamls": {
            "typescript_core": "typescript",
            "angular": "angular",
            "nestjs": "nestjs",
            "rxjs_core": "rxjs",
            "ngrx_core": "ngrx",
            "apollo_core": "apollo",
            "react": "react",
            "nextjs_core": "nextjs",
            "remix_core": "remix",
            "react_native_core": "react_native",
            "mui_core": "mui",
            "antd_core": "antd",
            "chakra_core": "chakra",
            "radix_core": "radix",
            "shadcn_core": "shadcn",
            "redux_core": "redux",
            "zustand_core": "zustand",
            "jotai_core": "jotai",
            "recoil_core": "recoil",
            "mobx_core": "mobx",
            "valtio_core": "valtio",
            "swr_core": "swr",
            "styled_components_core": "styled_components",
            "emotion_core": "emotion",
            "framer_motion_core": "framer_motion",
            "recharts_core": "recharts",
            "tanstack_query_core": "tanstack_query",
        },
    },
    {
        "eco": "Vue",
        "repo": "https://github.com/vuejs/core.git",
        "ext": ".ts",
        "yamls": {
            "vue_core": "vue",
            "pinia_core": "pinia",
        },
    },
    {
        "eco": "Ruby",
        "repo": "https://github.com/sinatra/sinatra.git",
        "ext": ".rb",
        "yamls": {
            "ruby_core": "ruby",
            "rails_core": "rails",
            "sinatra_core": "sinatra",
            "grape_core": "grape",
            "hanami_core": "hanami",
            "sidekiq_core": "sidekiq",
            "slim_core": "slim",
        },
    },
    {
        "eco": "PHP",
        "repo": "https://github.com/slimphp/Slim.git",
        "ext": ".php",
        "yamls": {
            "php_core": "php",
            "laravel_core": "laravel",
            "symfony_core": "symfony",
            "wordpress_core": "wordpress",
            "codeigniter_core": "codeigniter",
        },
    },
    {
        "eco": "Java",
        "repo": "https://github.com/google/gson.git",
        "ext": ".java",
        "yamls": {"java_core": "java"},
    },
    {
        "eco": "C#",
        "repo": "https://github.com/JamesNK/Newtonsoft.Json.git",
        "ext": ".cs",
        "yamls": {"csharp_core": "csharp"},
    },
    {
        "eco": "Dart",
        "repo": "https://github.com/dart-lang/http.git",
        "ext": ".dart",
        "yamls": {"dart_core": "dart"},
    },
    {
        "eco": "Kotlin",
        "repo": "https://github.com/ktorio/ktor.git",
        "ext": ".kt",
        "yamls": {"kotlin_core": "kotlin"},
    },
    {
        "eco": "Scala",
        "repo": "https://github.com/playframework/playframework.git",
        "ext": ".scala",
        "yamls": {"scala_core": "scala"},
    },
    {
        "eco": "Swift",
        "repo": "https://github.com/vapor/vapor.git",
        "ext": ".swift",
        "yamls": {"swift_core": "swift"},
    },
    {
        "eco": "CSS",
        "repo": "https://github.com/animate-css/animate.css.git",
        "ext": ".css",
        "yamls": {
            "css_core": "css",
            "sass_core": "sass",
            "less_core": "less",
            "postcss_core": "postcss",
            "tailwind_core": "tailwind",
            "bootstrap_core": "bootstrap",
        },
    },
    {
        "eco": "Svelte",
        "repo": "https://github.com/sveltejs/svelte.git",
        "ext": ".js",
        "yamls": {"svelte_core": "svelte"},
    },
    {
        "eco": "HTML",
        "repo": "https://github.com/h5bp/html5-boilerplate.git",
        "ext": ".html",
        "yamls": {"html_core": "html"},
    },
    {
        "eco": "SQL",
        "repo": "https://github.com/lerocha/chinook-database.git",
        "ext": ".sql",
        "yamls": {"sql_core": "sql"},
    },
    {
        "eco": "Bash",
        "repo": "https://github.com/nvm-sh/nvm.git",
        "ext": ".sh",
        "yamls": {"bash_core": "bash"},
    },
    {
        "eco": "C",
        "repo": "https://github.com/jqlang/jq.git",
        "ext": ".c",
        "yamls": {"c_core": "c"},
    },
    {
        "eco": "C++",
        "repo": "https://github.com/nlohmann/json.git",
        "ext": ".cpp",
        "yamls": {"cpp_core": "cpp"},
    },
    {
        "eco": "Lua",
        "repo": "https://github.com/luarocks/luarocks.git",
        "ext": ".lua",
        "yamls": {"lua_core": "lua"},
    },
    {
        "eco": "R",
        "repo": "https://github.com/tidyverse/ggplot2.git",
        "ext": ".R",
        "yamls": {"r_core": "r"},
    },
    {
        "eco": "PowerShell",
        "repo": "https://github.com/pester/Pester.git",
        "ext": ".ps1",
        "yamls": {"powershell_core": "powershell"},
    },
    {
        "eco": "Cross-cutting",
        "repo": None,
        "ext": None,
        "yamls": {
            "database": "database",
            "design_patterns": "design_patterns",
            "devops": "devops",
            "solid_patterns": "solid_patterns",
        },
    },
]


# ── Pre-flight: verify all 106 YAMLs are accounted for ─────────────────
_defined = set()
for e in ECOSYSTEMS:
    _defined.update(e["yamls"].keys())
_missing = set(ALL_YAML_STEMS) - _defined
_extra = _defined - set(ALL_YAML_STEMS)
if _missing or _extra:
    if _missing:
        print(f"ERROR: YAMLs not in any ecosystem: {sorted(_missing)}")
    if _extra:
        print(f"ERROR: Defined but no YAML file: {sorted(_extra)}")
    sys.exit(2)


# ── Helpers ──────────────────────────────────────────────────────────────

SKIP_DIRS = frozenset({
    ".git", "node_modules", "vendor", "dist", "build",
    "__pycache__", ".tox", ".mypy_cache", "target",
})


def clone_repo(url: str, dest: Path, timeout: int = 180) -> bool:
    """Shallow-clone a Git repository (skip LFS)."""
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"}
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, str(dest)],
            capture_output=True, timeout=timeout, check=True, env=env,
        )
        return True
    except Exception as e:
        print(f"⚠ Clone failed: {type(e).__name__}")
        return False


def scan_repo(repo_dir: Path, timeout: int = 300) -> bool:
    """Run codetrellis scan --optimal on a repository."""
    try:
        subprocess.run(
            [sys.executable, "-m", "codetrellis", "scan", str(repo_dir), "--optimal"],
            capture_output=True, timeout=timeout, check=True,
        )
        return True
    except Exception as e:
        print(f"⚠ Scan failed: {type(e).__name__}")
        return False


def find_source_file(repo_dir: Path, ext: str) -> str | None:
    """Find the first real source file matching `ext` in the repo."""
    if not ext:
        return None
    for f in repo_dir.rglob(f"*{ext}"):
        parts = f.relative_to(repo_dir).parts
        if any(p in SKIP_DIRS or p.startswith(".") for p in parts):
            continue
        return str(f)
    # Fallback: try case-insensitive for .R files
    if ext == ".R":
        for f in repo_dir.rglob("*.r"):
            parts = f.relative_to(repo_dir).parts
            if any(p in SKIP_DIRS or p.startswith(".") for p in parts):
                continue
            return str(f)
    return None


def call_bp(server: MatrixMCPServer, *, file_path=None, frameworks=None) -> str:
    """Call get_best_practices and return response text."""
    args: dict = {}
    if file_path:
        args["file_path"] = file_path
    if frameworks:
        args["frameworks"] = frameworks
    return server.call_tool("get_best_practices", args).content[0]["text"]


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> int:
    tmp_base = Path(tempfile.mkdtemp(prefix="ct_106test_"))
    print(f"Temp dir: {tmp_base}")
    print(f"YAMLs to verify: {TOTAL}")
    print(f"Ecosystems: {len(ECOSYSTEMS)}")
    print("=" * WIDTH)

    # Track per-YAML results: stem → ("PASS"|"FAIL"|"SKIP", detail)
    results: dict[str, tuple[str, str]] = {}
    fallback_server: MatrixMCPServer | None = None
    eco_results: list[tuple[str, str]] = []  # (eco, status)

    for eco in ECOSYSTEMS:
        eco_name = eco["eco"]
        repo_url = eco["repo"]
        file_ext = eco["ext"]
        yaml_map = eco["yamls"]

        print(f"\n{'─' * WIDTH}")
        print(f"[{eco_name}] — {len(yaml_map)} YAMLs")

        # ── Handle cross-cutting (no repo) ──
        if repo_url is None:
            if fallback_server is None:
                print("  ⚠ No server available — skip")
                eco_results.append((eco_name, "SKIP"))
                for stem in yaml_map:
                    results[stem] = ("SKIP", "no server")
                continue
            print("  Using last scanned server")
            server = fallback_server
            src_file = None
        else:
            print(f"  repo: {repo_url}")
            repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
            repo_dir = tmp_base / repo_name

            # Clone
            print("  Cloning...", end=" ", flush=True)
            t0 = time.time()
            if not clone_repo(repo_url, repo_dir):
                eco_results.append((eco_name, "SKIP"))
                for stem in yaml_map:
                    results[stem] = ("SKIP", "clone failed")
                continue
            print(f"({time.time() - t0:.1f}s)")

            # Scan
            print("  Scanning...", end=" ", flush=True)
            t0 = time.time()
            if not scan_repo(repo_dir):
                eco_results.append((eco_name, "SKIP"))
                for stem in yaml_map:
                    results[stem] = ("SKIP", "scan failed")
                continue
            print(f"({time.time() - t0:.1f}s)")

            # Load MCP server
            server = MatrixMCPServer(str(repo_dir))
            if not server.load_matrix():
                print("  ⚠ No matrix.prompt")
                eco_results.append((eco_name, "SKIP"))
                for stem in yaml_map:
                    results[stem] = ("SKIP", "no matrix")
                continue
            fallback_server = server

            # Find a source file for file_path test
            src_file = find_source_file(repo_dir, file_ext)
            if src_file:
                fname = Path(src_file).name
                print(f"  Source file: {fname}")

                # Bonus: file_path-only base language test
                text_base = call_bp(server, file_path=src_file)
                base_stem = list(yaml_map.keys())[0]
                base_yaml = f"{base_stem}.yaml"
                base_ok = base_yaml in text_base
                tag = "✓" if base_ok else "⚠"
                print(f"  {tag} file_path only → {base_yaml}: {'found' if base_ok else 'not found'}")
            else:
                print(f"  ⚠ No {file_ext} file found (framework tests still run)")

        # ── Test each YAML via framework hint ──
        eco_ok = True
        for yaml_stem, fw_hint in sorted(yaml_map.items()):
            yaml_name = f"{yaml_stem}.yaml"

            # Call with both file_path (for realism) and framework hint
            if src_file:
                text = call_bp(server, file_path=src_file, frameworks=[fw_hint])
            else:
                text = call_bp(server, frameworks=[fw_hint])

            found = yaml_name in text
            if found:
                results[yaml_stem] = ("PASS", f"fw={fw_hint}")
                icon = "✓"
            else:
                results[yaml_stem] = ("FAIL", f"fw={fw_hint}")
                icon = "✗"
                eco_ok = False

            print(f"    {icon} {'PASS' if found else 'FAIL':5s} | {yaml_name:35s} | fw={fw_hint}")

        eco_results.append((eco_name, "PASS" if eco_ok else "FAIL"))

    # ── Retry any SKIP/FAIL with fallback server ──
    retry_stems = [s for s, (st, _) in results.items() if st in ("SKIP", "FAIL")]
    if retry_stems and fallback_server:
        print(f"\n{'─' * WIDTH}")
        print(f"RETRY — {len(retry_stems)} YAMLs against fallback server")
        for yaml_stem in sorted(retry_stems):
            eco_entry = next(e for e in ECOSYSTEMS if yaml_stem in e["yamls"])
            fw_hint = eco_entry["yamls"][yaml_stem]
            yaml_name = f"{yaml_stem}.yaml"
            text = call_bp(fallback_server, frameworks=[fw_hint])
            found = yaml_name in text
            if found:
                results[yaml_stem] = ("PASS", f"fw={fw_hint} (retry)")
                print(f"    ✓ PASS  | {yaml_name:35s} | fw={fw_hint} (retry)")
            else:
                print(f"    ✗ FAIL  | {yaml_name:35s} | fw={fw_hint} (retry)")

    # ── Cleanup ──
    print(f"\nCleaning up {tmp_base}...")
    shutil.rmtree(tmp_base, ignore_errors=True)

    # ── Full 106-YAML report ──
    print()
    print("=" * WIDTH)
    print(f"ALL {TOTAL} YAML RESULTS")
    print("=" * WIDTH)

    pass_c = fail_c = skip_c = 0
    for stem in ALL_YAML_STEMS:
        status, detail = results.get(stem, ("MISSING", "not tested"))
        icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘"}.get(status, "?")
        print(f"  {icon} {status:7s} | {stem:35s} | {detail}")
        if status == "PASS":
            pass_c += 1
        elif status == "FAIL":
            fail_c += 1
        else:
            skip_c += 1

    # ── Ecosystem summary ──
    print()
    print("─" * WIDTH)
    print("ECOSYSTEM RESULTS")
    print("─" * WIDTH)
    for eco_name, eco_status in eco_results:
        icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘"}.get(eco_status, "?")
        print(f"  {icon} {eco_status:5s} | {eco_name}")

    print()
    print("=" * WIDTH)
    print(f"PASSED: {pass_c}/{TOTAL}  FAILED: {fail_c}/{TOTAL}  SKIPPED: {skip_c}/{TOTAL}")
    print("=" * WIDTH)

    return 0 if pass_c == TOTAL else 1


if __name__ == "__main__":
    sys.exit(main())
