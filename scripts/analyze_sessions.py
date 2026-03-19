#!/usr/bin/env python3
"""Analyze Copilot chat sessions to find patterns, anti-patterns, and generate learning rules."""

import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

WORKSPACE_STORAGE = Path(os.path.expanduser(
    "~/Library/Application Support/Code/User/workspaceStorage"
))


def find_chat_dir_for_project(project_name: str = "codetrellis-matrix") -> Path:
    """Auto-detect the VS Code workspace storage chatSessions dir for a project."""
    for d in WORKSPACE_STORAGE.iterdir():
        ws_file = d / "workspace.json"
        if ws_file.exists():
            try:
                data = json.loads(ws_file.read_text())
                if project_name in data.get("folder", ""):
                    chat_dir = d / "chatSessions"
                    if chat_dir.exists():
                        return chat_dir
            except (json.JSONDecodeError, OSError):
                continue
    raise FileNotFoundError(f"No workspace found matching '{project_name}'")


def analyze_sessions(chat_dir: Path):
    sessions = []

    for f in chat_dir.iterdir():
        if f.suffix not in (".jsonl", ".json"):
            continue
        try:
            first_line = f.open(errors="replace").readline()
            obj = json.loads(first_line)
            if not isinstance(obj, dict) or obj.get("kind") != 0:
                continue
            v = obj["v"]
            title = v.get("customTitle", "Untitled")
            ts = v.get("creationDate", 0)
            reqs = v.get("requests", [])
            n_reqs = len(reqs)
            model = reqs[0].get("modelId", "") if reqs else ""

            # Extract user messages
            user_messages = []
            assistant_snippets = []
            cancelled = 0
            for r in reqs:
                msg = r.get("message", {})
                if isinstance(msg, dict):
                    user_text = msg.get("text", "")
                    if user_text:
                        user_messages.append(user_text)

                resp = r.get("response", [])
                if not resp or (len(resp) == 1 and isinstance(resp[0], dict) and resp[0].get("kind") == "mcpServersStarting"):
                    cancelled += 1

                for part in resp:
                    if isinstance(part, dict) and "value" in part and isinstance(part["value"], str):
                        assistant_snippets.append(part["value"][:500])

            size_mb = f.stat().st_size / 1024 / 1024
            date = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M") if ts else "Unknown"

            sessions.append({
                "file": f.name,
                "title": title,
                "date": date,
                "ts": ts,
                "model": model.split("/")[-1] if model else "?",
                "n_reqs": n_reqs,
                "cancelled": cancelled,
                "size_mb": size_mb,
                "user_messages": user_messages,
                "assistant_snippets": assistant_snippets,
            })
        except Exception:
            pass

    sessions.sort(key=lambda s: s["ts"])
    return sessions


def find_patterns(sessions):
    """Analyze patterns across all sessions."""
    findings = {
        "total_sessions": len(sessions),
        "total_size_mb": sum(s["size_mb"] for s in sessions),
        "models_used": Counter(),
        "session_outcomes": {"completed": 0, "cancelled": 0, "partial": 0},
        "repeated_prompts": [],
        "prompt_length_issues": [],
        "model_switching": [],
        "rapid_retry_clusters": [],
        "vague_requests": [],
        "mega_prompts": [],
        "context_loss_indicators": [],
        "session_titles": [],
    }

    # Model usage
    for s in sessions:
        findings["models_used"][s["model"]] += 1
        findings["session_titles"].append(s["title"])

        if s["cancelled"] > 0 and s["cancelled"] == s["n_reqs"]:
            findings["session_outcomes"]["cancelled"] += 1
        elif s["cancelled"] > 0:
            findings["session_outcomes"]["partial"] += 1
        else:
            findings["session_outcomes"]["completed"] += 1

        # Detect vague requests
        for msg in s["user_messages"]:
            if len(msg) < 50 and any(w in msg.lower() for w in ["see attached", "fix", "check", "do it"]):
                findings["vague_requests"].append((s["date"], s["title"], msg[:100]))

            # Detect mega-prompts (>2000 chars)
            if len(msg) > 2000:
                findings["mega_prompts"].append((s["date"], s["title"], len(msg)))

    # Detect rapid-fire retries (same prompt within short time)
    for i in range(1, len(sessions)):
        prev, curr = sessions[i - 1], sessions[i]
        if prev["ts"] and curr["ts"]:
            gap_minutes = (curr["ts"] - prev["ts"]) / 60000
            if gap_minutes < 15:  # Less than 15 minutes apart
                # Check if similar title or prompt
                title_sim = prev["title"] == curr["title"]
                prompt_sim = False
                if prev["user_messages"] and curr["user_messages"]:
                    p1 = prev["user_messages"][0][:200]
                    p2 = curr["user_messages"][0][:200]
                    if p1 == p2 or (len(p1) > 50 and p1[:100] == p2[:100]):
                        prompt_sim = True
                if title_sim or prompt_sim:
                    findings["rapid_retry_clusters"].append({
                        "date": curr["date"],
                        "gap_min": round(gap_minutes, 1),
                        "title": curr["title"],
                        "prev_model": prev["model"],
                        "curr_model": curr["model"],
                        "prev_cancelled": prev["cancelled"] > 0,
                    })

    # Detect model switching for same task
    title_groups = {}
    for s in sessions:
        base_title = re.sub(r"\s*\d+$", "", s["title"]).strip()
        if base_title not in title_groups:
            title_groups[base_title] = []
        title_groups[base_title].append(s)

    for title, group in title_groups.items():
        if len(group) > 1:
            models = set(s["model"] for s in group)
            if len(models) > 1:
                findings["model_switching"].append({
                    "title": title,
                    "sessions": len(group),
                    "models": list(models),
                    "dates": [s["date"] for s in group],
                })

    # Detect repeated near-identical prompts
    prompt_hashes = {}
    for s in sessions:
        for msg in s["user_messages"]:
            key = msg[:300].strip()
            if key not in prompt_hashes:
                prompt_hashes[key] = []
            prompt_hashes[key].append(s["date"])

    for key, dates in prompt_hashes.items():
        if len(dates) > 1:
            findings["repeated_prompts"].append({
                "prompt_preview": key[:150],
                "times_used": len(dates),
                "dates": dates,
            })

    return findings


def generate_report(sessions, findings):
    """Generate the analysis report."""
    lines = []
    lines.append("# Copilot Session Analysis — Patterns & Anti-Patterns")
    lines.append("")
    lines.append(f"**Analyzed:** {findings['total_sessions']} sessions, {findings['total_size_mb']:.0f} MB total")
    lines.append(f"**Date range:** {sessions[0]['date']} — {sessions[-1]['date']}")
    lines.append("")

    # Overview stats
    lines.append("## 1. Overview Statistics")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total sessions | {findings['total_sessions']} |")
    lines.append(f"| Completed | {findings['session_outcomes']['completed']} |")
    lines.append(f"| Cancelled/no response | {findings['session_outcomes']['cancelled']} |")
    lines.append(f"| Partial (some cancelled) | {findings['session_outcomes']['partial']} |")
    lines.append(f"| Total data | {findings['total_size_mb']:.0f} MB |")
    lines.append("")

    lines.append("### Models Used")
    lines.append("")
    for model, count in findings["models_used"].most_common():
        lines.append(f"- **{model}**: {count} sessions")
    lines.append("")

    # Anti-pattern 1: Rapid retries
    lines.append("## 2. Anti-Pattern: Rapid-Fire Retries")
    lines.append("")
    if findings["rapid_retry_clusters"]:
        lines.append(f"**Found {len(findings['rapid_retry_clusters'])} instances** of opening a new session within 15 minutes (often with the same or near-identical prompt):")
        lines.append("")
        for r in findings["rapid_retry_clusters"]:
            lines.append(f"- **{r['date']}** — \"{r['title']}\" ({r['gap_min']} min gap, {r['prev_model']}→{r['curr_model']}, prev cancelled: {r['prev_cancelled']})")
        lines.append("")
        lines.append("**Impact:** Each new session loses all accumulated context. The model starts from scratch, wastes tokens re-reading files, and often hits the same failure point again.")
        lines.append("")
    else:
        lines.append("None detected.")
        lines.append("")

    # Anti-pattern 2: Repeated identical prompts
    lines.append("## 3. Anti-Pattern: Repeated Identical Prompts")
    lines.append("")
    repeated = [r for r in findings["repeated_prompts"] if r["times_used"] > 2]
    if repeated:
        lines.append(f"**Found {len(repeated)} prompts** used 3+ times with identical or near-identical text:")
        lines.append("")
        for r in repeated:
            lines.append(f"- Used **{r['times_used']}x**: \"{r['prompt_preview'][:100]}...\"")
            lines.append(f"  Dates: {', '.join(r['dates'])}")
        lines.append("")
        lines.append("**Impact:** Copy-pasting the same mega-prompt across sessions means the model isn't learning from prior failures. Each session restarts the same audit→implement→validate cycle from zero.")
        lines.append("")
    else:
        lines.append("No prompts used 3+ times detected.")
        lines.append("")

    # Anti-pattern 3: Model switching
    lines.append("## 4. Anti-Pattern: Model Switching for Same Task")
    lines.append("")
    if findings["model_switching"]:
        for ms in findings["model_switching"]:
            lines.append(f"- **\"{ms['title']}\"**: {ms['sessions']} sessions across models {', '.join(ms['models'])}")
        lines.append("")
        lines.append("**Impact:** Different models have different strengths. Switching mid-task without clear rationale creates inconsistent outputs and wasted context.")
        lines.append("")
    else:
        lines.append("None detected.")
        lines.append("")

    # Anti-pattern 4: Vague requests
    lines.append("## 5. Anti-Pattern: Vague/Underspecified Requests")
    lines.append("")
    if findings["vague_requests"]:
        for date, title, msg in findings["vague_requests"]:
            lines.append(f"- **{date}** ({title}): \"{msg}\"")
        lines.append("")
        lines.append("**Impact:** Vague requests like 'see attached and fix' force the model to guess what 'the issue' is, leading to broad unfocused analysis instead of targeted fixes.")
        lines.append("")
    else:
        lines.append("None detected.")
        lines.append("")

    # Anti-pattern 5: Mega-prompts
    lines.append("## 6. Pattern: Mega-Prompts (>2000 chars)")
    lines.append("")
    if findings["mega_prompts"]:
        lines.append(f"**Found {len(findings['mega_prompts'])} mega-prompts** (>2000 characters):")
        lines.append("")
        for date, title, length in findings["mega_prompts"]:
            lines.append(f"- **{date}** ({title}): {length:,} chars")
        lines.append("")
        lines.append("**Assessment:** Long, detailed prompts with clear constraints (like the PyPI launch plan) are actually **good** — they prevent ambiguity. However, when the same mega-prompt is reused across cancelled sessions, the effort is wasted.")
        lines.append("")
    else:
        lines.append("None detected.")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    project = sys.argv[1] if len(sys.argv) > 1 else "codetrellis-matrix"

    print(f"Finding workspace for '{project}'...")
    chat_dir = find_chat_dir_for_project(project)
    print(f"Chat dir: {chat_dir}")

    print("Analyzing sessions...")
    sessions = analyze_sessions(chat_dir)
    print(f"Found {len(sessions)} sessions")

    print("Finding patterns...")
    findings = find_patterns(sessions)

    print("Generating report...")
    report = generate_report(sessions, findings)

    output = Path(__file__).parent.parent / "session_analysis.md"
    output.write_text(report)
    print(f"Report written to {output}")
    print(f"Size: {output.stat().st_size / 1024:.1f} KB")
