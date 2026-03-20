#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def latest_session_note(project_sessions_dir: Path) -> Path | None:
    notes = sorted(project_sessions_dir.glob("*.md"))
    return notes[-1] if notes else None


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    workspace = repo_root / "workspace"
    projects_dir = workspace / "projects"

    project = sys.argv[1] if len(sys.argv) > 1 else input("Project name: ").strip()
    if not project:
        print("No project provided.")
        return 1

    project_dir = projects_dir / project
    if not project_dir.exists():
        print(f"Project not found: {project_dir}")
        return 1

    state_path = project_dir / "state.json"
    tasks_path = project_dir / "tasks.json"
    constraints_path = project_dir / "constraints.md"
    ops_path = project_dir / "ops.md"
    current_context_path = workspace / "CURRENT_CONTEXT.md"
    last_context_path = workspace / "global" / "last_context.json"
    sessions_dir = project_dir / "sessions"

    state = load_json(state_path)
    tasks = load_json(tasks_path)
    latest_note = latest_session_note(sessions_dir)

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    last_context = load_json(last_context_path)
    last_context["last_opened_project"] = project
    last_context["last_started_at_utc"] = now
    if state.get("current_focus"):
        last_context["current_focus"] = state["current_focus"]
    save_json(last_context_path, last_context)

    print("=" * 72)
    print("AI LAB SESSION START")
    print("=" * 72)
    print(f"Repo root   : {repo_root}")
    print(f"Project     : {project}")
    print(f"Started UTC : {now}")
    print()
    print("Read first:")
    print(f"- {repo_root / 'AGENTS.md'}")
    print(f"- {repo_root / 'docs' / 'SYSTEM_OPERATING_MANUAL.md'}")
    print(f"- {current_context_path}")
    print(f"- {state_path}")
    print(f"- {tasks_path}")
    print(f"- {constraints_path}")
    print(f"- {ops_path}")
    if latest_note:
        print(f"- {latest_note}")
    print()

    print("Project state summary:")
    print(f"- status        : {state.get('status', 'unknown')}")
    print(f"- phase         : {state.get('phase', 'unknown')}")
    print(f"- objective     : {state.get('objective', '')}")
    print(f"- current_focus : {state.get('current_focus', '')}")
    print()

    print("Top tasks:")
    for task in tasks.get("tasks", [])[:3]:
        print(f"- {task.get('id', '?')} [{task.get('status', '?')}] {task.get('title', '')}")

    print()
    print("Next step:")
    print("Propose today's 1-3 tasks before making major changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())