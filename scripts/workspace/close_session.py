#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def prompt_list(label: str) -> list[str]:
    raw = input(f"{label} (separate items with ; ): ").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(";") if item.strip()]


def write_current_context(
    path: Path,
    project: str,
    focus: str,
    completed: list[str],
    next_actions: list[str],
) -> None:
    completed_lines = "\n".join(f"- {item}" for item in completed) if completed else "- none recorded"
    next_lines = "\n".join(
        f"{i}. {item}" for i, item in enumerate(next_actions[:3], start=1)
    ) if next_actions else "1. Review project state and decide next actions"

    content = f"""# CURRENT_CONTEXT

## Active project
{project}

## Current focus
{focus or "Review project state and continue planned work."}

## Last completed work
{completed_lines}

## Next 1-3 actions
{next_lines}

## Important files to review first
- `AGENTS.md`
- `docs/SYSTEM_OPERATING_MANUAL.md`
- `workspace/projects/{project}/state.json`
- `workspace/projects/{project}/tasks.json`
- `workspace/projects/{project}/constraints.md`
- `workspace/projects/{project}/ops.md`

## Notes
Updated by `scripts/workspace/close_session.py`.
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=None)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    workspace = repo_root / "workspace"
    last_context_path = workspace / "global" / "last_context.json"
    last_context = load_json(last_context_path)

    project = args.project or last_context.get("last_opened_project") or input("Project name: ").strip()
    if not project:
        print("No project provided.")
        return 1

    project_dir = workspace / "projects" / project
    sessions_dir = project_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    state_path = project_dir / "state.json"
    current_context_path = workspace / "CURRENT_CONTEXT.md"
    global_sessions_dir = workspace / "global" / "sessions"
    global_sessions_dir.mkdir(parents=True, exist_ok=True)

    objective = input("Session objective: ").strip()
    completed = prompt_list("Completed work")
    decisions = prompt_list("Important decisions")
    blockers = prompt_list("Blockers/issues")
    next_actions = prompt_list("Next actions")
    global_learning = input("Cross-project/global learning note (optional): ").strip()

    now = datetime.now(timezone.utc).replace(microsecond=0)
    now_iso = now.isoformat()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    session_note = f"""# Session Note - {stamp}

## Project
{project}

## Closed at UTC
{now_iso}

## Objective
{objective or "Not recorded"}

## Completed work
""" + ("\n".join(f"- {item}" for item in completed) if completed else "- none recorded") + """

## Important decisions
""" + ("\n".join(f"- {item}" for item in decisions) if decisions else "- none recorded") + """

## Blockers/issues
""" + ("\n".join(f"- {item}" for item in blockers) if blockers else "- none recorded") + """

## Next actions
""" + ("\n".join(f"- {item}" for item in next_actions) if next_actions else "- none recorded") + "\n"

    session_path = sessions_dir / f"{stamp}.md"
    session_path.write_text(session_note, encoding="utf-8")

    state = load_json(state_path)
    state["last_closed_at_utc"] = now_iso
    if objective:
        state["objective"] = objective
    if completed:
        state["last_completed"] = completed
    state["blockers"] = blockers
    state["next_actions"] = next_actions
    if next_actions:
        state["current_focus"] = next_actions[0]
    save_json(state_path, state)

    last_context["last_opened_project"] = project
    last_context["last_closed_at_utc"] = now_iso
    if completed:
        last_context["last_completed_work"] = completed
    if next_actions:
        last_context["next_actions"] = next_actions[:3]
        last_context["current_focus"] = next_actions[0]
    save_json(last_context_path, last_context)

    write_current_context(
        current_context_path,
        project=project,
        focus=next_actions[0] if next_actions else state.get("current_focus", ""),
        completed=completed,
        next_actions=next_actions,
    )

    if global_learning:
        global_note = f"""# Global Session Note - {stamp}

## Source project
{project}

## Recorded at UTC
{now_iso}

## Cross-project learning
{global_learning}
"""
        (global_sessions_dir / f"{stamp}.md").write_text(global_note, encoding="utf-8")

    print(f"Session note written: {session_path}")
    print(f"State updated      : {state_path}")
    print(f"Context updated    : {current_context_path}")
    if global_learning:
        print(f"Global note added  : {global_sessions_dir / f'{stamp}.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())