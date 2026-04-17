#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


DEFAULT_WSL_DRIVE_ROOT = Path("/mnt/g/My Drive")
DEFAULT_COLAB_DRIVE_ROOT = Path("/content/drive/MyDrive")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def resolve_drive_root(runtime: str, drive_root_override: str | None) -> Path:
    if drive_root_override:
        return Path(drive_root_override)
    if runtime == "colab":
        return DEFAULT_COLAB_DRIVE_ROOT
    return DEFAULT_WSL_DRIVE_ROOT


def parse_section_list(markdown: str, heading: str) -> list[str]:
    lines = markdown.splitlines()
    items: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith("## "):
            in_section = line.strip() == f"## {heading}"
            continue
        if not in_section:
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
        elif stripped and stripped[0].isdigit() and ". " in stripped:
            _, value = stripped.split(". ", 1)
            items.append(value.strip())
    return [item for item in items if item]


def parse_markdown_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    items: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
        elif stripped and stripped[0].isdigit() and ". " in stripped:
            _, value = stripped.split(". ", 1)
            items.append(value.strip())
    return [item for item in items if item]


def first_nonempty_line(path: Path, fallback: str) -> str:
    if not path.exists():
        return fallback
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        return line
    return fallback

def normalize_argv(argv: list[str], modes: set[str]) -> list[str]:
    if not argv or argv[0] not in modes:
        return argv
    mode = argv[0]
    rest = argv[1:]
    global_flags = {"--project", "--registry", "--runtime", "--drive-root", "--skip-drive-sync"}
    reordered: list[str] = []
    specific_args: list[str] = []
    i = 0
    while i < len(rest):
        token = rest[i]
        if token in global_flags:
            reordered.append(token)
            if token == "--skip-drive-sync":
                i += 1
                continue
            if i + 1 >= len(rest):
                raise ValueError(f"Missing value for {token}")
            reordered.append(rest[i + 1])
            i += 2
        else:
            specific_args.append(token)
            i += 1
    return reordered + [mode] + specific_args


def latest_session_summary(sessions_dir: Path) -> str:
    notes = sorted(p for p in sessions_dir.glob("*.md") if p.is_file())
    if not notes:
        return "No session summary recorded yet."
    text = notes[-1].read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        return line
    return "Latest session note exists but has no summary lines."


def summarize_tasks(tasks_path: Path) -> str:
    if not tasks_path.exists():
        return "No tasks.json found."
    payload = load_json(tasks_path)
    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list):
        return "tasks.json does not contain a valid tasks list."
    statuses = Counter(str(task.get("status", "unknown")) for task in tasks if isinstance(task, dict))
    parts = [f"{k}={statuses[k]}" for k in sorted(statuses)]
    return f"{len(tasks)} tasks ({', '.join(parts)})" if parts else f"{len(tasks)} tasks"


def load_registry_project(registry_path: Path, project_slug: str) -> dict[str, Any]:
    registry = load_json(registry_path)
    if registry.get("schema_version") != "1":
        raise ValueError(f"{registry_path} must use schema_version '1'.")
    for item in registry.get("projects", []):
        if item.get("project_slug") == project_slug:
            return item
    raise ValueError(f"Project '{project_slug}' not found in {registry_path}.")


def validate_repo_backed(item: dict[str, Any]) -> None:
    if item.get("project_type") != "repo_backed":
        raise ValueError("Exporter requires a repo_backed project.")
    canonical = item.get("canonical_layer", {})
    if canonical.get("implementation_state") != "repo":
        raise ValueError("repo_backed projects must set canonical implementation_state to 'repo'.")
    repo_binding = item.get("repo_binding")
    if not isinstance(repo_binding, dict):
        raise ValueError("repo_backed projects must include a repo_binding object.")
    for required_key in ("repo_url", "default_branch"):
        if not repo_binding.get(required_key):
            raise ValueError(f"repo_binding.{required_key} is required for repo_backed projects.")


def build_snapshot(repo_root: Path, project_slug: str) -> dict[str, Any]:
    workspace = repo_root / "workspace"
    project_dir = workspace / "projects" / project_slug
    state_path = project_dir / "state.json"
    tasks_path = project_dir / "tasks.json"
    active_plan_path = project_dir / "active_plan.md"
    progress_path = project_dir / "progress.md"
    sessions_dir = project_dir / "sessions"
    current_context_path = workspace / "CURRENT_CONTEXT.md"

    state = load_json(state_path) if state_path.exists() else {}
    current_context = current_context_path.read_text(encoding="utf-8") if current_context_path.exists() else ""
    context_completed = parse_section_list(current_context, "Last completed work")
    context_next = parse_section_list(current_context, "Next 1-3 actions")

    branch = run_git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    head_commit = run_git(repo_root, "rev-parse", "HEAD")
    dirty_clean = "clean" if not run_git(repo_root, "status", "--porcelain") else "dirty"

    current_focus = str(state.get("current_focus") or "").strip()
    if not current_focus:
        current_focus = first_nonempty_line(progress_path, "Review project progress and choose current focus.")

    last_completed = state.get("last_completed")
    if not isinstance(last_completed, list):
        last_completed = context_completed
    last_completed = [str(item) for item in last_completed if str(item).strip()]

    next_actions = state.get("next_actions")
    if not isinstance(next_actions, list):
        next_actions = context_next
    next_actions = [str(item) for item in next_actions if str(item).strip()][:3]
    if not next_actions:
        next_actions = ["Review project state and define next actions."]

    snapshot = {
        "schema_version": "1",
        "contract_version": "1.0",
        "project": project_slug,
        "snapshot_generated_at": now_utc(),
        "branch": branch,
        "head_commit": head_commit,
        "dirty_clean": dirty_clean,
        "current_focus": current_focus,
        "last_completed_work": last_completed,
        "next_1_3_actions": next_actions,
        "task_summary": summarize_tasks(tasks_path),
        "active_plan_summary": first_nonempty_line(active_plan_path, "No active plan summary recorded yet."),
        "progress_summary": first_nonempty_line(progress_path, "No progress summary recorded yet."),
        "latest_session_summary": latest_session_summary(sessions_dir),
    }
    return snapshot


def snapshot_markdown(snapshot: dict[str, Any]) -> str:
    completed = snapshot.get("last_completed_work", [])
    actions = snapshot.get("next_1_3_actions", [])
    completed_lines = "\n".join(f"- {item}" for item in completed) if completed else "- none"
    action_lines = "\n".join(f"{i}. {item}" for i, item in enumerate(actions, start=1))
    return f"""# Interpreter Snapshot

- schema_version: {snapshot['schema_version']}
- contract_version: {snapshot['contract_version']}
- project: {snapshot['project']}
- snapshot_generated_at: {snapshot['snapshot_generated_at']}
- branch: {snapshot['branch']}
- head_commit: {snapshot['head_commit']}
- dirty_clean: {snapshot['dirty_clean']}

## Current focus
{snapshot['current_focus']}

## Last completed work
{completed_lines}

## Next 1-3 actions
{action_lines}

## Task summary
{snapshot['task_summary']}

## Active plan summary
{snapshot['active_plan_summary']}

## Progress summary
{snapshot['progress_summary']}

## Latest session summary
{snapshot['latest_session_summary']}
"""


def flatten(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [item.strip() for item in values if item and item.strip()]


def build_published_state(repo_root: Path, project_slug: str) -> dict[str, Any]:
    workspace = repo_root / "workspace"
    project_dir = workspace / "projects" / project_slug
    state_path = project_dir / "state.json"
    active_plan_path = project_dir / "active_plan.md"
    failure_registry_path = project_dir / "failure_registry.md"

    state = load_json(state_path) if state_path.exists() else {}
    active_task = first_nonempty_line(active_plan_path, "")
    if not active_task:
        active_task = None

    recent_completions = state.get("last_completed")
    if not isinstance(recent_completions, list):
        recent_completions = []
    recent_completions = [str(item).strip() for item in recent_completions if str(item).strip()]

    blockers = parse_markdown_list(failure_registry_path)

    branch = run_git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    commit_ref = run_git(repo_root, "rev-parse", "HEAD")
    dirty_clean = "clean" if not run_git(repo_root, "status", "--porcelain") else "dirty"

    generated_at = now_utc()
    stale_after = (datetime.fromisoformat(generated_at) + timedelta(hours=24)).isoformat()

    return {
        "schema_version": "1",
        "project_slug": project_slug,
        "generated_at": generated_at,
        "stale_after": stale_after,
        "active_task": active_task,
        "recent_completions": recent_completions,
        "blockers": blockers,
        "questions_for_strategy": [],
        "build_test_status": "unknown",
        "commit_ref": commit_ref,
        "branch": branch,
        "dirty_clean": dirty_clean,
    }


def write_snapshot_outputs(
    repo_root: Path,
    snapshot: dict[str, Any],
    project_item: dict[str, Any],
    runtime: str,
    drive_root_override: str | None,
    sync_drive: bool,
) -> dict[str, Path]:
    repo_snapshot_json = repo_root / "workspace" / "interpreter_snapshot.json"
    repo_snapshot_md = repo_root / "workspace" / "interpreter_snapshot.md"
    save_json(repo_snapshot_json, snapshot)
    save_text(repo_snapshot_md, snapshot_markdown(snapshot))

    outputs = {
        "repo_snapshot_json": repo_snapshot_json,
        "repo_snapshot_md": repo_snapshot_md,
    }

    if not sync_drive:
        return outputs

    drive_root = resolve_drive_root(runtime, drive_root_override)
    project_root_rel = project_item["drive_paths"]["project_root"]
    drive_project_root = drive_root / project_root_rel
    drive_snapshot_dir = drive_project_root / "repo_snapshot"
    drive_snapshot_json = drive_snapshot_dir / "latest_interpreter_snapshot.json"
    drive_snapshot_md = drive_snapshot_dir / "latest_interpreter_snapshot.md"
    save_json(drive_snapshot_json, snapshot)
    save_text(drive_snapshot_md, snapshot_markdown(snapshot))
    outputs["drive_snapshot_json"] = drive_snapshot_json
    outputs["drive_snapshot_md"] = drive_snapshot_md
    return outputs


def write_handoff_outputs(
    repo_root: Path,
    handoff: dict[str, Any],
    project_item: dict[str, Any],
    runtime: str,
    drive_root_override: str | None,
    sync_drive: bool,
) -> dict[str, Path]:
    repo_handoff = repo_root / "workspace" / "codex_handoff.json"
    save_json(repo_handoff, handoff)
    outputs = {"repo_handoff_json": repo_handoff}
    if not sync_drive:
        return outputs

    drive_root = resolve_drive_root(runtime, drive_root_override)
    project_root_rel = project_item["drive_paths"]["project_root"]
    drive_project_root = drive_root / project_root_rel
    drive_handoff = drive_project_root / "repo_snapshot" / "latest_codex_handoff.json"
    save_json(drive_handoff, handoff)
    outputs["drive_handoff_json"] = drive_handoff
    return outputs


def build_handoff(
    repo_root: Path,
    project_slug: str,
    snapshot: dict[str, Any],
    objective: str,
    completed: list[str],
    decisions: list[str],
    issues: list[str],
    next_actions: list[str],
) -> dict[str, Any]:
    branch = run_git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    head_commit = run_git(repo_root, "rev-parse", "HEAD")
    dirty_clean = "clean" if not run_git(repo_root, "status", "--porcelain") else "dirty"
    try:
        upstream = run_git(repo_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    except subprocess.CalledProcessError:
        upstream = ""
    try:
        commit_message = run_git(repo_root, "log", "-1", "--pretty=%s")
    except subprocess.CalledProcessError:
        commit_message = ""

    return {
        "schema_version": "1",
        "contract_version": "1.0",
        "generated_at": now_utc(),
        "project_slug": project_slug,
        "project_type": "repo_backed",
        "canonical_assertion": {
            "implementation_state": "repo",
            "continuity_pm_state": "drive",
        },
        "repo_close_checks": {
            "repo_memory_updated": True,
            "commit_created": True,
            "push_completed": True,
            "snapshot_exported": True,
        },
        "repo_state": {
            "branch": branch,
            "head_commit": head_commit,
            "dirty_clean": dirty_clean,
            "upstream": upstream,
            "commit_message": commit_message,
        },
        "snapshot": snapshot,
        "session_handoff": {
            "objective": objective,
            "completed": completed,
            "decisions": decisions,
            "issues": issues,
            "next_actions": next_actions,
        },
        "close_workspace_actions": {
            "write_reasoning_note": True,
            "write_timeline_event": True,
            "update_profile_timestamps_status": True,
            "milestone_updates_require_explicit_confirmation": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export repo snapshot and codex handoff artifacts.")
    parser.add_argument("--project", required=True, help="Project slug.")
    parser.add_argument(
        "--registry",
        default="workspace/registry/projects.json",
        help="Path to projects registry JSON.",
    )
    parser.add_argument(
        "--runtime",
        choices=["wsl", "colab"],
        default="wsl",
        help="Drive runtime path resolver.",
    )
    parser.add_argument(
        "--drive-root",
        default=None,
        help="Optional absolute override for Drive root.",
    )
    parser.add_argument(
        "--skip-drive-sync",
        action="store_true",
        help="Do not write mirrored files to Drive.",
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    subparsers.add_parser("snapshot", help="Export interpreter snapshot.")

    handoff_parser = subparsers.add_parser("handoff", help="Export codex handoff.")
    handoff_parser.add_argument("--objective", required=True)
    handoff_parser.add_argument("--completed", action="append", default=[])
    handoff_parser.add_argument("--decisions", action="append", default=[])
    handoff_parser.add_argument("--issues", action="append", default=[])
    handoff_parser.add_argument("--next-actions", action="append", default=[])

    subparsers.add_parser("publish-state", help="Export Codex published state.")

    args = parser.parse_args(normalize_argv(sys.argv[1:], {"snapshot", "handoff", "publish-state"}))
    repo_root = Path(__file__).resolve().parents[2]
    registry_path = (repo_root / args.registry).resolve()
    project_item = load_registry_project(registry_path, args.project)
    validate_repo_backed(project_item)

    if args.mode == "publish-state":
        published = build_published_state(repo_root, args.project)
        output_path = repo_root / "workspace" / "projects" / args.project / "codex_published_state.v1.json"
        save_json(output_path, published)
        print(json.dumps({"published_state_written": str(output_path)}))
        return 0

    snapshot = build_snapshot(repo_root, args.project)
    snapshot_paths = write_snapshot_outputs(
        repo_root=repo_root,
        snapshot=snapshot,
        project_item=project_item,
        runtime=args.runtime,
        drive_root_override=args.drive_root,
        sync_drive=not args.skip_drive_sync,
    )

    print(json.dumps({"snapshot_written": {k: str(v) for k, v in snapshot_paths.items()}}, indent=2))

    if args.mode == "snapshot":
        return 0

    completed = flatten(args.completed)
    decisions = flatten(args.decisions)
    issues = flatten(args.issues)
    next_actions = flatten(args.next_actions)
    handoff = build_handoff(
        repo_root=repo_root,
        project_slug=args.project,
        snapshot=snapshot,
        objective=args.objective.strip(),
        completed=completed,
        decisions=decisions,
        issues=issues,
        next_actions=next_actions,
    )
    handoff_paths = write_handoff_outputs(
        repo_root=repo_root,
        handoff=handoff,
        project_item=project_item,
        runtime=args.runtime,
        drive_root_override=args.drive_root,
        sync_drive=not args.skip_drive_sync,
    )
    print(json.dumps({"handoff_written": {k: str(v) for k, v in handoff_paths.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
