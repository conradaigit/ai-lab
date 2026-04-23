#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
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


def resolve_drive_root(runtime: str, drive_root_override: str | None) -> Path:
    if drive_root_override:
        return Path(drive_root_override)
    if runtime == "colab":
        return DEFAULT_COLAB_DRIVE_ROOT
    return DEFAULT_WSL_DRIVE_ROOT


def resolve_path(path_value: str, repo_root: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def is_uuid4(value: str) -> bool:
    try:
        parsed = uuid.UUID(value)
    except (ValueError, TypeError):
        return False
    return parsed.version == 4 and str(parsed) == value.lower()


def normalize_items(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [item.strip() for item in values if item and item.strip()]


def validate_project_item(item: dict[str, Any]) -> None:
    slug = item.get("project_slug")
    project_type = item.get("project_type")
    canonical = item.get("canonical_layer", {})
    require(isinstance(slug, str) and slug, "project_slug is required.")
    require(project_type in {"repo_backed", "drive_native"}, f"{slug}: invalid project_type.")
    require(canonical.get("continuity_pm_state") == "drive", f"{slug}: continuity_pm_state must be drive.")
    drive_paths = item.get("drive_paths", {})
    require(isinstance(drive_paths.get("project_root"), str), f"{slug}: drive_paths.project_root is required.")

    repo_binding = item.get("repo_binding")
    if project_type == "repo_backed":
        require(canonical.get("implementation_state") == "repo", f"{slug}: repo implementation_state required.")
        require(isinstance(repo_binding, dict), f"{slug}: repo_backed requires repo_binding.")
    else:
        require(canonical.get("implementation_state") == "drive", f"{slug}: drive implementation_state required.")
        require(repo_binding in (None, {}), f"{slug}: drive_native repo_binding must be null/absent.")


def load_registry(path: Path) -> dict[str, Any]:
    registry = load_json(path)
    require(registry.get("schema_version") == "1", "registry schema_version must be '1'.")
    projects = registry.get("projects")
    require(isinstance(projects, list), "registry.projects must be a list.")
    for item in projects:
        validate_project_item(item)
    return registry


def save_registry(path: Path, payload: dict[str, Any]) -> None:
    save_json(path, payload)


def get_project(registry: dict[str, Any], slug: str) -> dict[str, Any]:
    for item in registry.get("projects", []):
        if item.get("project_slug") == slug:
            return item
    raise ValueError(f"Project '{slug}' not found.")


def derive_project_paths(project_abs_root: Path) -> dict[str, Path]:
    return {
        "profile": project_abs_root / "profile.json",
        "milestones": project_abs_root / "milestones.json",
        "timeline": project_abs_root / "timeline.json",
        "sessions_log": project_abs_root / "sessions.log.jsonl",
        "reasoning_notes_dir": project_abs_root / "reasoning_notes",
        "repo_handoff_json": project_abs_root / "repo_snapshot" / "latest_codex_handoff.json",
    }


def load_handoff(path: Path, project_slug: str) -> dict[str, Any]:
    require(path.exists(), f"Missing codex handoff: {path}")
    payload = load_json(path)
    require(payload.get("schema_version") == "1", "codex_handoff schema_version must be '1'.")
    require(payload.get("project_type") == "repo_backed", "codex_handoff project_type must be repo_backed.")
    require(payload.get("project_slug") == project_slug, "codex_handoff project_slug mismatch.")
    checks = payload.get("repo_close_checks", {})
    for key in ("repo_memory_updated", "commit_created", "push_completed", "snapshot_exported"):
        require(checks.get(key) is True, f"codex_handoff repo_close_checks.{key} must be true.")
    return payload


def append_session_log(
    log_path: Path,
    project_slug: str,
    event_type: str,
    session_id: str,
    metadata: dict[str, Any],
) -> None:
    entry = {
        "timestamp": now_utc(),
        "project_slug": project_slug,
        "event_type": event_type,
        "session_id": session_id,
        "metadata": metadata,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, separators=(",", ":"), ensure_ascii=False) + "\n")


def write_reasoning_note(
    reasoning_dir: Path,
    timestamp_slug: str,
    generated_at: str,
    objective: str,
    completed: list[str],
    decisions: list[str],
    issues: list[str],
    next_actions: list[str],
    repo_handoff_ref: str | None,
) -> Path:
    reasoning_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Session Reasoning - {timestamp_slug}",
        "",
        f"- generated_at: {generated_at}",
        "",
        "## Objective",
        objective,
        "",
        "## Completed",
    ]
    lines.extend([f"- {item}" for item in completed] or ["- none recorded"])
    lines.extend(["", "## Decisions"])
    lines.extend([f"- {item}" for item in decisions] or ["- none recorded"])
    lines.extend(["", "## Issues"])
    lines.extend([f"- {item}" for item in issues] or ["- none recorded"])
    lines.extend(["", "## Next Actions"])
    lines.extend([f"- {item}" for item in next_actions] or ["- none recorded"])
    if repo_handoff_ref:
        lines.extend(["", "## Repo Handoff", repo_handoff_ref])
    content = "\n".join(lines) + "\n"
    note_path = reasoning_dir / f"{timestamp_slug}_session.md"
    note_path.write_text(content, encoding="utf-8")
    return note_path


def append_timeline_event(
    timeline_path: Path,
    generated_at: str,
    objective: str,
    current_focus: str,
    completed: list[str],
    decisions: list[str],
    issues: list[str],
    next_actions: list[str],
    repo_handoff_ref: str | None,
) -> None:
    payload: dict[str, Any]
    if timeline_path.exists():
        parsed = load_json(timeline_path)
        if isinstance(parsed, dict):
            payload = parsed
        else:
            payload = {"schema_version": "1", "events": []}
    else:
        payload = {"schema_version": "1", "events": []}

    if payload.get("schema_version") != "1":
        payload["schema_version"] = "1"
    events = payload.get("events")
    if not isinstance(events, list):
        events = []

    event = {
        "timestamp": generated_at,
        "event_type": "session_close",
        "objective": objective,
        "current_focus": current_focus,
        "completed": completed,
        "decisions": decisions,
        "issues": issues,
        "next_actions": next_actions,
        "execution_gate": {"chatgpt_planning_required_before_codex_execution": True},
        "repo_handoff_ref": repo_handoff_ref,
    }
    events.append(event)
    payload["events"] = events
    save_json(timeline_path, payload)


def update_profile(
    profile_path: Path,
    project_item: dict[str, Any],
    generated_at: str,
    session_id: str,
    status_override: str | None,
    next_session_focus: str,
    objective: str,
    completed: list[str],
    issues: list[str],
    next_actions: list[str],
) -> None:
    if profile_path.exists():
        profile = load_json(profile_path)
    else:
        profile = {
            "schema_version": "1",
            "project_slug": project_item["project_slug"],
            "display_name": project_item["display_name"],
            "project_type": project_item["project_type"],
            "canonical_layer": project_item["canonical_layer"],
            "created_at": project_item["created_at"],
        }
    profile["schema_version"] = "1"
    profile["updated_at"] = generated_at
    profile["last_session_at"] = generated_at
    profile["status"] = status_override or project_item.get("status", "active")
    profile["next_session_focus"] = next_session_focus
    profile["latest_close_summary"] = {
        "updated_at": generated_at,
        "session_id": session_id,
        "objective": objective,
        "current_focus": next_session_focus,
        "recent_completions": completed[:5],
        "issues_or_blockers": issues,
        "next_actions": next_actions[:3],
        "execution_gate": {"chatgpt_planning_required_before_codex_execution": True},
    }
    save_json(profile_path, profile)


def apply_milestone_updates(milestones_path: Path, updates_file: Path | None, confirmed: bool) -> bool:
    if updates_file is None:
        return False
    require(confirmed, "Milestone updates require --confirm-milestone-updates.")
    updates = load_json(updates_file)
    if isinstance(updates, dict) and "milestones" in updates:
        payload = {"schema_version": "1", "milestones": updates.get("milestones", [])}
    elif isinstance(updates, list):
        payload = {"schema_version": "1", "milestones": updates}
    else:
        raise ValueError("Milestone update payload must be a list or an object containing 'milestones'.")
    save_json(milestones_path, payload)
    return True


def ensure_milestones_initialized(milestones_path: Path) -> None:
    if milestones_path.exists():
        return
    save_json(milestones_path, {"schema_version": "1", "milestones": []})


def main() -> int:
    parser = argparse.ArgumentParser(description="Close Workspace flow for Drive continuity updates.")
    parser.add_argument("--registry", default="workspace/registry/projects.json")
    parser.add_argument("--runtime", choices=["wsl", "colab"], default="wsl")
    parser.add_argument("--drive-root", default=None)
    parser.add_argument("--project", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--completed", action="append", default=[])
    parser.add_argument("--decisions", action="append", default=[])
    parser.add_argument("--issues", action="append", default=[])
    parser.add_argument("--next-actions", action="append", default=[])
    parser.add_argument("--next-session-focus", default=None)
    parser.add_argument("--status", choices=["active", "paused", "archived"], default=None)
    parser.add_argument("--milestone-updates-json", default=None)
    parser.add_argument("--confirm-milestone-updates", action="store_true")
    parser.add_argument("--handoff-path", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    registry_path = resolve_path(args.registry, repo_root)
    drive_root = resolve_drive_root(args.runtime, args.drive_root)
    registry = load_registry(registry_path)
    project_item = get_project(registry, args.project)
    validate_project_item(project_item)

    objective = args.objective.strip()
    completed = normalize_items(args.completed)
    decisions = normalize_items(args.decisions)
    issues = normalize_items(args.issues)
    next_actions = normalize_items(args.next_actions)
    require(objective, "objective is required.")
    require(next_actions, "At least one next action is required.")
    session_id = args.session_id.strip().lower()
    require(session_id, "--session-id is required.")
    require(is_uuid4(session_id), "--session-id must be a UUIDv4 string.")
    next_session_focus = args.next_session_focus.strip() if args.next_session_focus else next_actions[0]

    generated_at = now_utc()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    project_root_rel = project_item["drive_paths"]["project_root"]
    project_abs_root = drive_root / project_root_rel
    paths = derive_project_paths(project_abs_root)

    repo_handoff_ref: str | None = None
    repo_handoff_consumed = False
    repo_context_mode = "required" if project_item["project_type"] == "repo_backed" else "absent"
    if project_item["project_type"] == "repo_backed":
        handoff_path = resolve_path(args.handoff_path, repo_root) if args.handoff_path else paths["repo_handoff_json"]
        load_handoff(handoff_path, project_item["project_slug"])
        repo_handoff_ref = f"{project_root_rel}/repo_snapshot/latest_codex_handoff.json"
        repo_handoff_consumed = True
    append_session_log(
        log_path=paths["sessions_log"],
        project_slug=project_item["project_slug"],
        event_type="close_start",
        session_id=session_id,
        metadata={
            "runtime": args.runtime,
            "project_type": project_item["project_type"],
            "repo_context_mode": repo_context_mode,
        },
    )

    note_path = write_reasoning_note(
        reasoning_dir=paths["reasoning_notes_dir"],
        timestamp_slug=stamp,
        generated_at=generated_at,
        objective=objective,
        completed=completed,
        decisions=decisions,
        issues=issues,
        next_actions=next_actions,
        repo_handoff_ref=repo_handoff_ref,
    )
    append_timeline_event(
        timeline_path=paths["timeline"],
        generated_at=generated_at,
        objective=objective,
        current_focus=next_session_focus,
        completed=completed,
        decisions=decisions,
        issues=issues,
        next_actions=next_actions,
        repo_handoff_ref=repo_handoff_ref,
    )
    update_profile(
        profile_path=paths["profile"],
        project_item=project_item,
        generated_at=generated_at,
        session_id=session_id,
        status_override=args.status,
        next_session_focus=next_session_focus,
        objective=objective,
        completed=completed,
        issues=issues,
        next_actions=next_actions,
    )

    ensure_milestones_initialized(paths["milestones"])
    milestone_updates_file = resolve_path(args.milestone_updates_json, repo_root) if args.milestone_updates_json else None
    milestones_updated = apply_milestone_updates(
        milestones_path=paths["milestones"],
        updates_file=milestone_updates_file,
        confirmed=args.confirm_milestone_updates,
    )

    project_item["updated_at"] = generated_at
    project_item["last_session_at"] = generated_at
    if args.status:
        project_item["status"] = args.status
    save_registry(registry_path, registry)

    receipt = {
        "schema_version": "1",
        "contract_version": "1.0",
        "session_id": session_id,
        "generated_at": generated_at,
        "project_slug": project_item["project_slug"],
        "project_type": project_item["project_type"],
        "repo_context_mode": repo_context_mode,
        "writes": {
            "reasoning_note_written": True,
            "timeline_updated": True,
            "profile_updated": True,
            "milestones_updated": milestones_updated,
        },
        "inputs_captured": {
            "objective": objective,
            "completed_count": len(completed),
            "decisions_count": len(decisions),
            "issues_count": len(issues),
            "next_actions_count": len(next_actions),
        },
        "repo_handoff_consumed": repo_handoff_consumed,
        "next_session_focus": next_session_focus,
        "reasoning_note_path": str(note_path),
    }

    serialized = json.dumps(receipt, indent=2)
    output_path = resolve_path(args.output, repo_root) if args.output else None
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized + "\n", encoding="utf-8")
    append_session_log(
        log_path=paths["sessions_log"],
        project_slug=project_item["project_slug"],
        event_type="close_emit",
        session_id=session_id,
        metadata={
            "repo_context_mode": repo_context_mode,
            "repo_handoff_consumed": repo_handoff_consumed,
            "next_session_focus": next_session_focus,
        },
    )
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
