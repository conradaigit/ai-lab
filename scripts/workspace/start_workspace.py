#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_WSL_DRIVE_ROOT = Path("/mnt/g/My Drive")
DEFAULT_COLAB_DRIVE_ROOT = Path("/content/drive/MyDrive")
RECENT_TIMELINE_LIMIT = 20


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


def derive_project_paths(project_abs_root: Path) -> dict[str, Path]:
    return {
        "profile": project_abs_root / "profile.json",
        "goals": project_abs_root / "goals.md",
        "milestones": project_abs_root / "milestones.json",
        "timeline": project_abs_root / "timeline.json",
        "reasoning_notes_dir": project_abs_root / "reasoning_notes",
        "repo_snapshot_json": project_abs_root / "repo_snapshot" / "latest_interpreter_snapshot.json",
        "repo_snapshot_md": project_abs_root / "repo_snapshot" / "latest_interpreter_snapshot.md",
        "drive_published_state_json": project_abs_root / "repo_snapshot" / "latest_codex_published_state.v1.json",
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_registry_payload(registry: dict[str, Any]) -> None:
    require(registry.get("schema_version") == "1", "registry schema_version must be '1'.")
    projects = registry.get("projects")
    require(isinstance(projects, list), "registry.projects must be a list.")
    for item in projects:
        validate_project_item(item)


def validate_project_item(item: dict[str, Any]) -> None:
    slug = item.get("project_slug")
    require(isinstance(slug, str) and slug, "project_slug is required.")
    project_type = item.get("project_type")
    require(project_type in {"repo_backed", "drive_native"}, f"Invalid project_type for {slug}.")
    canonical = item.get("canonical_layer", {})
    require(canonical.get("continuity_pm_state") == "drive", f"{slug}: continuity_pm_state must be 'drive'.")
    drive_paths = item.get("drive_paths", {})
    project_root = drive_paths.get("project_root")
    require(isinstance(project_root, str) and project_root.startswith("_ai/projects/"), f"{slug}: invalid project_root.")

    repo_binding = item.get("repo_binding")
    if project_type == "repo_backed":
        require(canonical.get("implementation_state") == "repo", f"{slug}: repo_backed implementation_state must be repo.")
        require(isinstance(repo_binding, dict), f"{slug}: repo_backed requires repo_binding.")
        require(bool(repo_binding.get("repo_url")), f"{slug}: repo_binding.repo_url is required.")
        require(bool(repo_binding.get("default_branch")), f"{slug}: repo_binding.default_branch is required.")
    else:
        require(canonical.get("implementation_state") == "drive", f"{slug}: drive_native implementation_state must be drive.")
        require(repo_binding in (None, {}), f"{slug}: drive_native repo_binding must be null/absent.")


def load_registry(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    validate_registry_payload(payload)
    return payload


def save_registry(path: Path, payload: dict[str, Any]) -> None:
    validate_registry_payload(payload)
    save_json(path, payload)


def get_project(registry: dict[str, Any], project_slug: str) -> dict[str, Any]:
    for item in registry["projects"]:
        if item["project_slug"] == project_slug:
            return item
    raise ValueError(f"Project '{project_slug}' not found.")


def first_summary_line(text: str) -> str:
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        return line
    return ""


def latest_reasoning_note(reasoning_dir: Path, project_root_rel: str) -> dict[str, Any] | None:
    if not reasoning_dir.exists():
        return None
    notes = sorted(p for p in reasoning_dir.glob("*.md") if p.is_file())
    if not notes:
        return None
    latest = notes[-1]
    summary = first_summary_line(latest.read_text(encoding="utf-8")) or "Reasoning note recorded."
    mtime = datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()
    relative_path = f"{project_root_rel}/reasoning_notes/{latest.name}"
    return {"path": relative_path, "timestamp": mtime, "summary": summary}


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = load_json(path)
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def load_published_state(
    drive_published_state_path: Path,
    repo_published_state_path: Path,
) -> tuple[dict[str, Any] | None, str]:
    payload = load_optional_json(drive_published_state_path)
    if payload is not None:
        return payload, "drive_mirror"
    payload = load_optional_json(repo_published_state_path)
    if payload is not None:
        return payload, "repo_local_fallback"
    return None, "null"


def parse_milestones(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = load_json(path)
    if isinstance(payload, dict):
        milestones = payload.get("milestones", [])
        return milestones if isinstance(milestones, list) else []
    if isinstance(payload, list):
        return payload
    return []


def parse_timeline_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = load_json(path)
    if isinstance(payload, dict):
        events = payload.get("events", [])
        events_list = events if isinstance(events, list) else []
    elif isinstance(payload, list):
        events_list = payload
    else:
        events_list = []
    return events_list[-RECENT_TIMELINE_LIMIT:]


def normalize_repo_snapshot(snapshot: dict[str, Any], source_path: str) -> dict[str, Any]:
    required_keys = [
        "project",
        "snapshot_generated_at",
        "branch",
        "head_commit",
        "dirty_clean",
        "current_focus",
        "last_completed_work",
        "next_1_3_actions",
        "task_summary",
        "active_plan_summary",
        "progress_summary",
        "latest_session_summary",
    ]
    missing = [key for key in required_keys if key not in snapshot]
    require(not missing, f"Missing snapshot keys: {', '.join(missing)}")
    return {"source_path": source_path, **{key: snapshot[key] for key in required_keys}}


def validate_session_context(payload: dict[str, Any]) -> None:
    require(payload.get("schema_version") == "1", "SESSION_CONTEXT_JSON schema_version must be '1'.")
    require(payload.get("contract_version") == "1.0", "SESSION_CONTEXT_JSON contract_version must be '1.0'.")
    project_type = payload.get("project_type")
    repo_mode = payload.get("repo_context_mode")
    repo_snapshot = payload.get("repo_snapshot")

    if project_type == "repo_backed":
        require(repo_mode == "required", "repo_backed requires repo_context_mode='required'.")
        require(isinstance(repo_snapshot, dict), "repo_backed requires repo_snapshot object.")
    elif project_type == "drive_native":
        require(repo_mode == "absent", "drive_native requires repo_context_mode='absent'.")
        require(repo_snapshot is None, "drive_native requires repo_snapshot=null.")
    else:
        raise ValueError(f"Unsupported project_type: {project_type}")


def load_drive_context(project_item: dict[str, Any], project_abs_root: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    paths = derive_project_paths(project_abs_root)
    profile = load_json(paths["profile"]) if paths["profile"].exists() else {}
    goals_markdown = paths["goals"].read_text(encoding="utf-8") if paths["goals"].exists() else ""
    milestones = parse_milestones(paths["milestones"])
    timeline_recent = parse_timeline_events(paths["timeline"])
    note = latest_reasoning_note(paths["reasoning_notes_dir"], project_item["drive_paths"]["project_root"])
    drive_context = {
        "project_root": project_item["drive_paths"]["project_root"],
        "profile": profile,
        "goals_markdown": goals_markdown,
        "milestones": milestones,
        "timeline_recent": timeline_recent,
        "latest_reasoning_note": note,
    }
    return drive_context, paths


def command_list(registry: dict[str, Any]) -> int:
    projects = [
        {
            "project_slug": item["project_slug"],
            "display_name": item["display_name"],
            "project_type": item["project_type"],
            "status": item["status"],
            "canonical_implementation": item["canonical_layer"]["implementation_state"],
            "last_session_at": item.get("last_session_at"),
        }
        for item in registry["projects"]
    ]
    print(json.dumps({"schema_version": "1", "projects": projects}, indent=2))
    return 0


def initialize_project_memory(
    project_item: dict[str, Any],
    project_abs_root: Path,
) -> None:
    paths = derive_project_paths(project_abs_root)
    project_abs_root.mkdir(parents=True, exist_ok=True)
    paths["reasoning_notes_dir"].mkdir(parents=True, exist_ok=True)
    if project_item["project_type"] == "repo_backed":
        (project_abs_root / "repo_snapshot").mkdir(parents=True, exist_ok=True)

    profile_path = paths["profile"]
    if not profile_path.exists():
        profile_payload = {
            "schema_version": "1",
            "project_slug": project_item["project_slug"],
            "display_name": project_item["display_name"],
            "project_type": project_item["project_type"],
            "status": project_item["status"],
            "canonical_layer": project_item["canonical_layer"],
            "created_at": project_item["created_at"],
            "updated_at": project_item["updated_at"],
            "last_session_at": project_item.get("last_session_at"),
        }
        save_json(profile_path, profile_payload)
    if not paths["goals"].exists():
        paths["goals"].write_text("# goals\n\n", encoding="utf-8")
    if not paths["milestones"].exists():
        save_json(paths["milestones"], {"schema_version": "1", "milestones": []})
    if not paths["timeline"].exists():
        save_json(paths["timeline"], {"schema_version": "1", "events": []})


def command_add(args: argparse.Namespace, registry: dict[str, Any], registry_path: Path, drive_root: Path) -> int:
    slug = args.project
    existing = [item["project_slug"] for item in registry["projects"]]
    require(slug not in existing, f"Project '{slug}' already exists.")
    project_root = args.project_root or f"_ai/projects/{slug}"
    now = now_utc()
    project_type = args.project_type
    canonical = {"implementation_state": "repo" if project_type == "repo_backed" else "drive", "continuity_pm_state": "drive"}
    repo_binding: dict[str, Any] | None = None
    if project_type == "repo_backed":
        require(bool(args.repo_url), "--repo-url is required for repo_backed.")
        require(bool(args.default_branch), "--default-branch is required for repo_backed.")
        repo_binding = {
            "repo_url": args.repo_url,
            "default_branch": args.default_branch,
        }
        if args.workspace_path:
            repo_binding["workspace_path"] = args.workspace_path
        if args.repo_project_key:
            repo_binding["repo_project_key"] = args.repo_project_key

    entry: dict[str, Any] = {
        "project_slug": slug,
        "display_name": args.display_name,
        "project_type": project_type,
        "status": "active",
        "canonical_layer": canonical,
        "drive_paths": {"project_root": project_root},
        "last_session_at": None,
        "tags": args.tags or [],
        "created_at": now,
        "updated_at": now,
    }
    if repo_binding is not None:
        entry["repo_binding"] = repo_binding
    else:
        entry["repo_binding"] = None

    validate_project_item(entry)
    registry["projects"].append(entry)
    save_registry(registry_path, registry)

    if args.init_memory:
        project_abs_root = drive_root / project_root
        initialize_project_memory(entry, project_abs_root)

    print(json.dumps(entry, indent=2))
    return 0


def command_archive(args: argparse.Namespace, registry: dict[str, Any], registry_path: Path) -> int:
    item = get_project(registry, args.project)
    item["status"] = "archived"
    item["updated_at"] = now_utc()
    save_registry(registry_path, registry)
    print(json.dumps({"archived": args.project, "updated_at": item["updated_at"]}, indent=2))
    return 0


def command_delete(args: argparse.Namespace, registry: dict[str, Any], registry_path: Path, drive_root: Path) -> int:
    require(args.confirm == args.project, "Delete confirmation must match the project slug.")
    item = get_project(registry, args.project)
    project_root_rel = item["drive_paths"]["project_root"]
    registry["projects"] = [p for p in registry["projects"] if p["project_slug"] != args.project]
    save_registry(registry_path, registry)

    deleted_drive_root = None
    if args.delete_drive_files:
        deleted_drive_root = drive_root / project_root_rel
        if deleted_drive_root.exists():
            shutil.rmtree(deleted_drive_root)

    response = {"deleted_project": args.project}
    if deleted_drive_root:
        response["deleted_drive_root"] = str(deleted_drive_root)
    print(json.dumps(response, indent=2))
    return 0


def command_start(args: argparse.Namespace, registry: dict[str, Any], drive_root: Path, output_path: Path | None) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    item = get_project(registry, args.project)
    validate_project_item(item)
    project_root_rel = item["drive_paths"]["project_root"]
    project_abs_root = drive_root / project_root_rel
    drive_context, paths = load_drive_context(item, project_abs_root)

    repo_snapshot_payload: dict[str, Any] | None
    repo_mode: str
    codex_published_state: dict[str, Any] | None = None
    published_state_path = repo_root / "workspace" / "projects" / item["project_slug"] / "codex_published_state.v1.json"
    if item["project_type"] == "repo_backed":
        require(paths["repo_snapshot_json"].exists(), f"Missing snapshot: {paths['repo_snapshot_json']}")
        raw_snapshot = load_json(paths["repo_snapshot_json"])
        source_path = f"{project_root_rel}/repo_snapshot/latest_interpreter_snapshot.json"
        repo_snapshot_payload = normalize_repo_snapshot(raw_snapshot, source_path)
        repo_mode = "required"
        codex_published_state, _codex_published_state_source = load_published_state(
            drive_published_state_path=paths["drive_published_state_json"],
            repo_published_state_path=published_state_path,
        )
    else:
        repo_snapshot_payload = None
        repo_mode = "absent"
        codex_published_state = None

    payload = {
        "schema_version": "1",
        "contract_version": "1.0",
        "generated_at": now_utc(),
        "project_slug": item["project_slug"],
        "project_type": item["project_type"],
        "repo_context_mode": repo_mode,
        "canonical_layer": item["canonical_layer"],
        "drive_context": drive_context,
        "repo_snapshot": repo_snapshot_payload,
        "codex_published_state": codex_published_state,
        "execution_gate": {"chatgpt_planning_required_before_codex_execution": True},
    }
    validate_session_context(payload)
    serialized = json.dumps(payload, indent=2)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Start Workspace flow for Drive + repo context.")
    parser.add_argument("--registry", default="workspace/registry/projects.json")
    parser.add_argument("--runtime", choices=["wsl", "colab"], default="wsl")
    parser.add_argument("--drive-root", default=None)

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="Show project list.")

    add_parser = subparsers.add_parser("add", help="Add a project to registry.")
    add_parser.add_argument("--project", required=True)
    add_parser.add_argument("--display-name", required=True)
    add_parser.add_argument("--project-type", choices=["repo_backed", "drive_native"], required=True)
    add_parser.add_argument("--project-root", default=None)
    add_parser.add_argument("--repo-url", default=None)
    add_parser.add_argument("--default-branch", default=None)
    add_parser.add_argument("--workspace-path", default=None)
    add_parser.add_argument("--repo-project-key", default=None)
    add_parser.add_argument("--tags", nargs="*", default=[])
    add_parser.add_argument("--init-memory", action="store_true", default=True)
    add_parser.add_argument("--no-init-memory", dest="init_memory", action="store_false")

    archive_parser = subparsers.add_parser("archive", help="Archive a project.")
    archive_parser.add_argument("--project", required=True)

    delete_parser = subparsers.add_parser("delete", help="Delete a project.")
    delete_parser.add_argument("--project", required=True)
    delete_parser.add_argument("--confirm", required=True)
    delete_parser.add_argument("--delete-drive-files", action="store_true")

    start_parser = subparsers.add_parser("start", help="Emit SESSION_CONTEXT_JSON for a selected project.")
    start_parser.add_argument("--project", required=True)
    start_parser.add_argument("--output", default=None)

    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    registry_path = resolve_path(args.registry, repo_root)
    drive_root = resolve_drive_root(args.runtime, args.drive_root)
    registry = load_registry(registry_path)

    if args.command == "list":
        return command_list(registry)
    if args.command == "add":
        return command_add(args, registry, registry_path, drive_root)
    if args.command == "archive":
        return command_archive(args, registry, registry_path)
    if args.command == "delete":
        return command_delete(args, registry, registry_path, drive_root)
    if args.command == "start":
        output_path = resolve_path(args.output, repo_root) if args.output else None
        return command_start(args, registry, drive_root, output_path)
    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
