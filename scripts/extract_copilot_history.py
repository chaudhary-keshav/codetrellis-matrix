#!/usr/bin/env python3
"""Extract all Copilot chat history from VS Code local storage into a readable Markdown file."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


WORKSPACE_STORAGE = Path.home() / "Library/Application Support/Code/User/workspaceStorage"
OUTPUT_FILE = Path(__file__).parent.parent / "copilot_chat_history.md"


def find_workspace_dirs(filter_project: str | None = None) -> list[tuple[str, Path]]:
    """Find all workspace storage directories, optionally filtering by project name."""
    results = []
    for d in WORKSPACE_STORAGE.iterdir():
        ws_file = d / "workspace.json"
        if ws_file.exists():
            try:
                data = json.loads(ws_file.read_text())
                folder = data.get("folder", "")
                if filter_project is None or filter_project.lower() in folder.lower():
                    results.append((folder, d))
            except (json.JSONDecodeError, OSError):
                continue
    return results


def extract_text_from_response(response_parts: list) -> str:
    """Extract readable text from response parts."""
    texts = []
    for part in response_parts:
        if isinstance(part, dict):
            if "value" in part and isinstance(part["value"], str):
                val = part["value"].strip()
                if val and part.get("kind") != "mcpServersStarting":
                    if part.get("kind") == "thinking":
                        texts.append(f"<thinking>{val}</thinking>")
                    else:
                        texts.append(val)
            elif "text" in part and isinstance(part["text"], str):
                texts.append(part["text"].strip())
    return "\n\n".join(t for t in texts if t)


def extract_session(filepath: Path) -> dict | None:
    """Extract a single chat session from a .jsonl or .json file."""
    try:
        content = filepath.read_text(errors="replace")
    except OSError:
        return None

    session_data = None
    updates = {}

    for line in content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(obj, dict):
            continue

        if obj.get("kind") == 0:
            session_data = obj.get("v", {})
        elif obj.get("kind") == 1:
            key_path = obj.get("k", [])
            value = obj.get("v")
            updates[tuple(key_path)] = value

    if session_data is None:
        # Try as plain JSON (older format)
        try:
            session_data = json.loads(content)
            if isinstance(session_data, dict) and "requests" not in session_data:
                session_data = session_data.get("v", session_data)
        except json.JSONDecodeError:
            return None

    if not session_data or not isinstance(session_data, dict):
        return None

    title = session_data.get("customTitle", "Untitled Session")
    session_id = session_data.get("sessionId", filepath.stem)
    creation_ts = session_data.get("creationDate", 0)
    if creation_ts:
        creation_date = datetime.fromtimestamp(creation_ts / 1000).strftime("%Y-%m-%d %H:%M")
    else:
        creation_date = "Unknown"

    requests = session_data.get("requests", [])
    model_id = ""
    conversations = []

    for i, req in enumerate(requests):
        msg = req.get("message", {})
        user_text = ""
        if isinstance(msg, dict):
            user_text = msg.get("text", "")
            if not user_text:
                parts = msg.get("parts", [])
                for p in parts:
                    if isinstance(p, dict) and "text" in p:
                        user_text = p["text"]
                        break

        if not model_id:
            model_id = req.get("modelId", "")

        response_parts = req.get("response", [])
        assistant_text = extract_text_from_response(response_parts)

        # Check for updates that might have the full response
        for key_path, value in updates.items():
            if len(key_path) >= 3 and key_path[0] == "requests" and key_path[1] == i:
                if key_path[2] == "response" and isinstance(value, list):
                    updated = extract_text_from_response(value)
                    if len(updated) > len(assistant_text):
                        assistant_text = updated

        if user_text or assistant_text:
            conversations.append({
                "user": user_text.strip() if user_text else "(no user message)",
                "assistant": assistant_text.strip() if assistant_text else "(no response / cancelled)",
            })

    if not conversations:
        return None

    return {
        "title": title,
        "session_id": session_id,
        "creation_date": creation_date,
        "creation_ts": creation_ts,
        "model": model_id,
        "conversations": conversations,
        "file": str(filepath),
    }


def main():
    project_filter = None
    if len(sys.argv) > 1:
        project_filter = sys.argv[1]

    workspaces = find_workspace_dirs(project_filter)

    if not workspaces:
        print(f"No workspaces found{f' matching {project_filter!r}' if project_filter else ''}.")
        sys.exit(1)

    all_sessions = []

    for folder_uri, ws_dir in workspaces:
        chat_dir = ws_dir / "chatSessions"
        if not chat_dir.exists():
            continue

        project_name = folder_uri.split("/")[-1] if "/" in folder_uri else folder_uri

        for f in chat_dir.iterdir():
            if f.suffix in (".jsonl", ".json"):
                session = extract_session(f)
                if session:
                    session["project"] = project_name
                    all_sessions.append(session)

    # Sort by creation date
    all_sessions.sort(key=lambda s: s.get("creation_ts", 0))

    # Write output
    lines = []
    lines.append("# Copilot Chat History Export")
    lines.append("")
    lines.append(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Total sessions:** {len(all_sessions)}")
    if project_filter:
        lines.append(f"**Filter:** {project_filter}")
    lines.append(f"**Workspaces:** {len(workspaces)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")
    for i, session in enumerate(all_sessions, 1):
        anchor = f"session-{i}"
        date_str = session["creation_date"]
        title = session["title"]
        n_msgs = len(session["conversations"])
        lines.append(f"{i}. [{title}](#{anchor}) — {date_str} ({n_msgs} exchanges)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Full sessions
    for i, session in enumerate(all_sessions, 1):
        lines.append(f"## Session {i}: {session['title']}")
        lines.append("")
        lines.append(f"- **Date:** {session['creation_date']}")
        lines.append(f"- **Project:** {session['project']}")
        if session["model"]:
            lines.append(f"- **Model:** {session['model']}")
        lines.append(f"- **Session ID:** `{session['session_id']}`")
        lines.append("")

        for j, conv in enumerate(session["conversations"], 1):
            lines.append(f"### Exchange {j}")
            lines.append("")
            lines.append("**User:**")
            lines.append("")
            # Truncate very long user messages
            user_msg = conv["user"]
            if len(user_msg) > 3000:
                user_msg = user_msg[:3000] + "\n\n... (message truncated, was {} chars)".format(len(conv["user"]))
            lines.append(user_msg)
            lines.append("")
            lines.append("**Assistant:**")
            lines.append("")
            assistant_msg = conv["assistant"]
            if len(assistant_msg) > 5000:
                assistant_msg = assistant_msg[:5000] + "\n\n... (response truncated, was {} chars)".format(len(conv["assistant"]))
            lines.append(assistant_msg)
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("")

    output = "\n".join(lines)
    OUTPUT_FILE.write_text(output)
    print(f"Exported {len(all_sessions)} sessions to {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
