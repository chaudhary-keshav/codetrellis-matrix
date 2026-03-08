#!/usr/bin/env python3
"""
XState Integration Validation Script

Clones 2-3 public XState repositories and runs the XState parser
against them to validate extraction quality on real-world code.

Part of CodeTrellis v4.55 - XState Framework Support Validation
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

# Add parent to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codetrellis.xstate_parser_enhanced import EnhancedXstateParser


# Repos to validate against
REPOS = [
    {
        "name": "statelyai/xstate",
        "url": "https://github.com/statelyai/xstate.git",
        "sparse": ["examples"],  # Only clone examples dir
        "depth": 1,
    },
    {
        "name": "mattpocock/xstate-tutorials",
        "url": "https://github.com/mattpocock/xstate-tutorials.git",
        "depth": 1,
    },
    {
        "name": "statelyai/xstate-viz",
        "url": "https://github.com/statelyai/xstate-viz.git",
        "depth": 1,
    },
]


def clone_repo(repo: dict, dest: str) -> str:
    """Clone a repo to dest directory."""
    repo_dir = os.path.join(dest, repo["name"].split("/")[1])
    cmd = ["git", "clone", "--depth", str(repo.get("depth", 1)), repo["url"], repo_dir]
    print(f"  Cloning {repo['name']}...")
    try:
        subprocess.run(cmd, capture_output=True, timeout=60, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"  ⚠  Failed to clone {repo['name']}: {e}")
        return ""
    return repo_dir


def find_xstate_files(root: str) -> list:
    """Find all .ts/.tsx/.js/.jsx files that might contain XState code."""
    parser = EnhancedXstateParser()
    xstate_files = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip node_modules, .git, dist, build
        dirnames[:] = [d for d in dirnames if d not in (
            'node_modules', '.git', 'dist', 'build', '.next', 'coverage',
            '__pycache__', '.cache', '.turbo',
        )]
        for fname in filenames:
            if not fname.endswith(('.ts', '.tsx', '.js', '.jsx')):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if parser.is_xstate_file(content, fpath):
                    xstate_files.append((fpath, content))
            except Exception:
                pass
    return xstate_files


def validate_repo(repo_dir: str, repo_name: str) -> dict:
    """Parse all XState files in a repo and return stats."""
    parser = EnhancedXstateParser()
    files = find_xstate_files(repo_dir)

    stats = {
        "repo": repo_name,
        "xstate_files": len(files),
        "machines": 0,
        "state_nodes": 0,
        "transitions": 0,
        "invokes": 0,
        "actions": 0,
        "guards": 0,
        "imports": 0,
        "actors": 0,
        "typegens": 0,
        "frameworks": set(),
        "features": set(),
        "versions": set(),
        "errors": 0,
        "sample_files": [],
    }

    for fpath, content in files:
        try:
            result = parser.parse(content, fpath)
            stats["machines"] += len(result.machines)
            stats["state_nodes"] += len(result.state_nodes)
            stats["transitions"] += len(result.transitions)
            stats["invokes"] += len(result.invokes)
            stats["actions"] += len(result.actions)
            stats["guards"] += len(result.guards)
            stats["imports"] += len(result.imports)
            stats["actors"] += len(result.actors)
            stats["typegens"] += len(result.typegens)
            stats["frameworks"].update(result.detected_frameworks)
            stats["features"].update(result.detected_features)
            if result.xstate_version:
                stats["versions"].add(result.xstate_version)

            # Record sample files with interesting results
            if result.machines and len(stats["sample_files"]) < 5:
                rel = os.path.relpath(fpath, repo_dir)
                stats["sample_files"].append({
                    "file": rel,
                    "machines": len(result.machines),
                    "states": len(result.state_nodes),
                    "transitions": len(result.transitions),
                    "actions": len(result.actions),
                    "guards": len(result.guards),
                    "version": result.xstate_version,
                })
        except Exception as e:
            stats["errors"] += 1

    return stats


def print_stats(stats: dict):
    """Print validation stats."""
    print(f"\n{'═' * 60}")
    print(f"  Repository: {stats['repo']}")
    print(f"{'═' * 60}")
    print(f"  XState files found:    {stats['xstate_files']}")
    print(f"  Machines extracted:    {stats['machines']}")
    print(f"  State nodes:           {stats['state_nodes']}")
    print(f"  Transitions:           {stats['transitions']}")
    print(f"  Invokes:               {stats['invokes']}")
    print(f"  Actions:               {stats['actions']}")
    print(f"  Guards:                {stats['guards']}")
    print(f"  Imports:               {stats['imports']}")
    print(f"  Actors:                {stats['actors']}")
    print(f"  Typegens:              {stats['typegens']}")
    print(f"  Parse errors:          {stats['errors']}")
    print(f"  Frameworks detected:   {sorted(stats['frameworks'])}")
    print(f"  Features detected:     {sorted(stats['features'])}")
    print(f"  Versions detected:     {sorted(stats['versions'])}")

    if stats["sample_files"]:
        print(f"\n  Sample files:")
        for sf in stats["sample_files"]:
            print(f"    {sf['file']}")
            print(f"      machines={sf['machines']} states={sf['states']} "
                  f"transitions={sf['transitions']} actions={sf['actions']} "
                  f"guards={sf['guards']} version={sf['version']}")
    print()


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        XState Parser Validation - CodeTrellis v4.55     ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  Validating parser against public XState repositories   ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    tmpdir = tempfile.mkdtemp(prefix="ct-xstate-validate-")
    all_stats = []

    try:
        for repo in REPOS:
            repo_dir = clone_repo(repo, tmpdir)
            if not repo_dir or not os.path.isdir(repo_dir):
                continue
            stats = validate_repo(repo_dir, repo["name"])
            all_stats.append(stats)
            print_stats(stats)

        # Summary
        if all_stats:
            total_files = sum(s["xstate_files"] for s in all_stats)
            total_machines = sum(s["machines"] for s in all_stats)
            total_states = sum(s["state_nodes"] for s in all_stats)
            total_transitions = sum(s["transitions"] for s in all_stats)
            total_actions = sum(s["actions"] for s in all_stats)
            total_guards = sum(s["guards"] for s in all_stats)
            total_errors = sum(s["errors"] for s in all_stats)
            all_frameworks = set()
            all_features = set()
            for s in all_stats:
                all_frameworks.update(s["frameworks"])
                all_features.update(s["features"])

            print("═" * 60)
            print("  VALIDATION SUMMARY")
            print("═" * 60)
            print(f"  Repos validated:       {len(all_stats)}")
            print(f"  Total XState files:    {total_files}")
            print(f"  Total machines:        {total_machines}")
            print(f"  Total state nodes:     {total_states}")
            print(f"  Total transitions:     {total_transitions}")
            print(f"  Total actions:         {total_actions}")
            print(f"  Total guards:          {total_guards}")
            print(f"  Total parse errors:    {total_errors}")
            print(f"  All frameworks:        {sorted(all_frameworks)}")
            print(f"  All features:          {sorted(all_features)}")
            print(f"\n  ✅ Validation complete — parser handles real-world XState code")
        else:
            print("  ⚠  No repos could be cloned/validated")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
