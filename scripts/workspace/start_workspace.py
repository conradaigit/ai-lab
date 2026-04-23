#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import uuid
from datetime import datetime, timedelta, timezone
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


def stale_after_24h(generated_at: str) -> str:
    return (datetime.fromisoformat(generated_at) + timedelta(hours=24)).isoformat()


def compute_context_hash(payload: dict[str, Any]) -> str:
    # Canonical subset excludes volatile fields: generated_at, stale_after, session_id.
    subset = {
        "schema_version": payload["schema_version"],
        "contract_version": payload["contract_version"],
        "project_slug": payload["project_slug"],
        "project_type": payload["project_type"],
        "repo_context_mode": payload["repo_context_mode"],
        "canonical_layer": payload["canonical_layer"],
        "drive_context": payload["drive_context"],
        "repo_snapshot": payload["repo_snapshot"],
        "codex_published_state": payload["codex_published_state"],
        "startup_brief": payload["startup_brief"],
        "execution_gate": payload["execution_gate"],
    }
    canonical_json = json.dumps(subset, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def derive_project_paths(project_abs_root: Path) -> dict[str, Path]:
    return {
        "profile": project_abs_root / "profile.json",
        "goals": project_abs_root / "goals.md",
        "milestones": project_abs_root / "milestones.json",
        "timeline": project_abs_root / "timeline.json",
        "sessions_log": project_abs_root / "sessions.log.jsonl",
        "reasoning_notes_dir": project_abs_root / "reasoning_notes",
        "repo_snapshot_json": project_abs_root / "repo_snapshot" / "latest_interpreter_snapshot.json",
        "repo_snapshot_md": project_abs_root / "repo_snapshot" / "latest_interpreter_snapshot.md",
        "drive_published_state_json": project_abs_root / "repo_snapshot" / "latest_codex_published_state.v1.json",
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


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


def first_nonempty_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str):
            candidate = value.strip()
            if candidate:
                return candidate
    return None


def normalize_string_list(values: Any, limit: int) -> list[str]:
    if not isinstance(values, list):
        return []
    normalized = [str(item).strip() for item in values if str(item).strip()]
    return normalized[:limit]


def latest_session_close_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for entry in reversed(events):
        if isinstance(entry, dict) and entry.get("event_type") == "session_close":
            return entry
    return None


def derive_startup_brief(
    project_item: dict[str, Any],
    drive_context: dict[str, Any],
    repo_snapshot_payload: dict[str, Any] | None,
    codex_published_state: dict[str, Any] | None,
    execution_gate: dict[str, Any],
) -> dict[str, Any]:
    profile = drive_context.get("profile") if isinstance(drive_context.get("profile"), dict) else {}
    timeline_recent = drive_context.get("timeline_recent") if isinstance(drive_context.get("timeline_recent"), list) else []
    latest_close = latest_session_close_event(timeline_recent)
    latest_close_summary = profile.get("latest_close_summary") if isinstance(profile.get("latest_close_summary"), dict) else {}

    next_session_focus = first_nonempty_string(drive_context.get("next_session_focus"))
    repo_focus = first_nonempty_string(repo_snapshot_payload.get("current_focus")) if isinstance(repo_snapshot_payload, dict) else None
    published_active_task = first_nonempty_string(codex_published_state.get("active_task")) if isinstance(codex_published_state, dict) else None
    close_focus = first_nonempty_string(
        latest_close_summary.get("current_focus"),
        latest_close.get("current_focus") if isinstance(latest_close, dict) else None,
    )

    current_focus = first_nonempty_string(
        close_focus,
        next_session_focus,
        repo_focus,
        published_active_task,
    )
    if current_focus is None:
        current_focus = "Review latest continuity state and define immediate focus."

    next_actions = normalize_string_list(latest_close_summary.get("next_actions"), 3)
    if not next_actions and isinstance(latest_close, dict):
        next_actions = normalize_string_list(latest_close.get("next_actions"), 3)
    if not next_actions and isinstance(repo_snapshot_payload, dict):
        next_actions = normalize_string_list(repo_snapshot_payload.get("next_1_3_actions"), 3)
    if not next_actions:
        next_actions = [current_focus]

    recent_completions = normalize_string_list(latest_close_summary.get("recent_completions"), 5)
    if not recent_completions and isinstance(latest_close, dict):
        recent_completions = normalize_string_list(latest_close.get("completed"), 5)
    if not recent_completions and isinstance(codex_published_state, dict):
        recent_completions = normalize_string_list(codex_published_state.get("recent_completions"), 5)
    if not recent_completions and isinstance(repo_snapshot_payload, dict):
        recent_completions = normalize_string_list(repo_snapshot_payload.get("last_completed_work"), 5)

    issues_or_blockers = normalize_string_list(latest_close_summary.get("issues_or_blockers"), 5)
    if not issues_or_blockers and isinstance(latest_close, dict):
        issues_or_blockers = normalize_string_list(latest_close.get("issues"), 5)
    if not issues_or_blockers and isinstance(codex_published_state, dict):
        issues_or_blockers = normalize_string_list(codex_published_state.get("blockers"), 5)

    return {
        "project_launched": {
            "project_slug": project_item["project_slug"],
            "display_name": project_item["display_name"],
        },
        "current_focus": current_focus,
        "next_actions": next_actions,
        "project_type": project_item["project_type"],
        "recent_completions": recent_completions,
        "issues_or_blockers": issues_or_blockers,
        "execution_gate": execution_gate,
    }


def build_session_agent_contract() -> dict[str, Any]:
    return {
        "required_next_step": "summarize_startup_brief_then_choose_next_step",
        "required_steps": [
            "1.) summarize project_launched, current_focus, and next_actions concisely.",
            "2.) if useful, include project_type, recent_completions, issues_or_blockers, and execution_gate.",
            "3.) then ask a neutral next-step question: continue planning here, or prepare a handoff for the next step.",
        ],
        "required_summary_fields": [
            "project_launched",
            "current_focus",
            "next_actions",
        ],
        "optional_summary_fields": [
            "project_type",
            "recent_completions",
            "issues_or_blockers",
            "execution_gate",
        ],
        "default_next_step": "continue_planning_in_chat",
        "avoid": [
            "long_architecture_restatement_without_need",
            "jumping_directly_to_tool_specific_handoff_by_default",
            "mentioning_codex_without_context_or_user_request",
        ],
    }


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
    session_id = payload.get("session_id")
    require(isinstance(session_id, str) and session_id, "SESSION_CONTEXT_JSON requires non-empty session_id.")
    try:
        parsed = uuid.UUID(session_id)
    except (ValueError, TypeError):
        raise ValueError("SESSION_CONTEXT_JSON session_id must be a valid UUID.") from None
    require(parsed.version == 4, "SESSION_CONTEXT_JSON session_id must be UUIDv4.")
    context_hash = payload.get("context_hash")
    require(isinstance(context_hash, str) and len(context_hash) == 64, "SESSION_CONTEXT_JSON context_hash must be 64-char hex.")
    agent_expected_behavior = payload.get("agent_expected_behavior")
    require(
        isinstance(agent_expected_behavior, str) and bool(agent_expected_behavior.strip()),
        "SESSION_CONTEXT_JSON requires non-empty agent_expected_behavior.",
    )
    agent_contract = payload.get("agent_contract")
    require(isinstance(agent_contract, dict), "SESSION_CONTEXT_JSON requires agent_contract object.")
    for required_key in (
        "required_next_step",
        "required_steps",
        "required_summary_fields",
        "optional_summary_fields",
        "default_next_step",
        "avoid",
    ):
        require(required_key in agent_contract, f"SESSION_CONTEXT_JSON agent_contract missing {required_key}.")
    startup_brief = payload.get("startup_brief")
    require(isinstance(startup_brief, dict), "SESSION_CONTEXT_JSON requires startup_brief object.")
    require("project_launched" in startup_brief, "startup_brief.project_launched is required.")
    require("current_focus" in startup_brief, "startup_brief.current_focus is required.")
    require("next_actions" in startup_brief, "startup_brief.next_actions is required.")
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
    next_session_focus = profile.get("next_session_focus")
    if not isinstance(next_session_focus, str) or not next_session_focus.strip():
        next_session_focus = None
    drive_context = {
        "project_root": project_item["drive_paths"]["project_root"],
        "profile": profile,
        "goals_markdown": goals_markdown,
        "milestones": milestones,
        "timeline_recent": timeline_recent,
        "latest_reasoning_note": note,
        "next_session_focus": next_session_focus,
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
            "next_session_focus": None,
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


def command_edit(args: argparse.Namespace, registry: dict[str, Any], registry_path: Path) -> int:
    item = get_project(registry, args.project)
    project_type = item["project_type"]

    if args.display_name is not None:
        value = args.display_name.strip()
        require(bool(value), "--display-name cannot be empty.")
        item["display_name"] = value

    if args.status is not None:
        item["status"] = args.status

    if args.tags is not None:
        item["tags"] = [str(tag).strip() for tag in args.tags if str(tag).strip()]

    if args.project_root is not None:
        value = args.project_root.strip()
        require(value.startswith("_ai/projects/"), "--project-root must start with _ai/projects/.")
        item["drive_paths"]["project_root"] = value

    repo_fields_provided = any(
        value is not None
        for value in (
            args.repo_url,
            args.default_branch,
            args.workspace_path,
            args.repo_project_key,
        )
    )
    if repo_fields_provided:
        require(project_type == "repo_backed", "Repo binding fields can only be edited for repo_backed projects.")
        repo_binding = item.get("repo_binding")
        if not isinstance(repo_binding, dict):
            repo_binding = {}
            item["repo_binding"] = repo_binding
        if args.repo_url is not None:
            value = args.repo_url.strip()
            require(bool(value), "--repo-url cannot be empty.")
            repo_binding["repo_url"] = value
        if args.default_branch is not None:
            value = args.default_branch.strip()
            require(bool(value), "--default-branch cannot be empty.")
            repo_binding["default_branch"] = value
        if args.workspace_path is not None:
            value = args.workspace_path.strip()
            if value:
                repo_binding["workspace_path"] = value
            elif "workspace_path" in repo_binding:
                del repo_binding["workspace_path"]
        if args.repo_project_key is not None:
            value = args.repo_project_key.strip()
            if value:
                repo_binding["repo_project_key"] = value
            elif "repo_project_key" in repo_binding:
                del repo_binding["repo_project_key"]

    item["updated_at"] = now_utc()
    validate_project_item(item)
    save_registry(registry_path, registry)
    print(json.dumps(item, indent=2))
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

    session_id = str(uuid.uuid4())
    append_session_log(
        log_path=paths["sessions_log"],
        project_slug=item["project_slug"],
        event_type="launcher_start",
        session_id=session_id,
        metadata={
            "runtime": args.runtime,
            "project_type": item["project_type"],
            "repo_context_mode": repo_mode,
        },
    )
    execution_gate = {"chatgpt_planning_required_before_codex_execution": True}
    startup_brief = derive_startup_brief(
        project_item=item,
        drive_context=drive_context,
        repo_snapshot_payload=repo_snapshot_payload,
        codex_published_state=codex_published_state,
        execution_gate=execution_gate,
    )
    generated_at = now_utc()
    payload = {
        "schema_version": "1",
        "contract_version": "1.0",
        "session_id": session_id,
        "generated_at": generated_at,
        "stale_after": stale_after_24h(generated_at),
        "project_slug": item["project_slug"],
        "project_type": item["project_type"],
        "repo_context_mode": repo_mode,
        "canonical_layer": item["canonical_layer"],
        "drive_context": drive_context,
        "repo_snapshot": repo_snapshot_payload,
        "codex_published_state": codex_published_state,
        "execution_gate": execution_gate,
        "startup_brief": startup_brief,
        "agent_expected_behavior": "summarize_then_choose_next_step",
        "agent_contract": build_session_agent_contract(),
    }
    payload["context_hash"] = compute_context_hash(payload)
    validate_session_context(payload)
    serialized = json.dumps(payload, indent=2)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized + "\n", encoding="utf-8")
    append_session_log(
        log_path=paths["sessions_log"],
        project_slug=item["project_slug"],
        event_type="launcher_emit",
        session_id=session_id,
        metadata={
            "repo_context_mode": repo_mode,
            "stale_after": payload["stale_after"],
            "context_hash": payload["context_hash"],
        },
    )
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

    edit_parser = subparsers.add_parser("edit", help="Edit an existing project.")
    edit_parser.add_argument("--project", required=True)
    edit_parser.add_argument("--display-name", default=None)
    edit_parser.add_argument("--status", choices=["active", "paused", "archived"], default=None)
    edit_parser.add_argument("--tags", nargs="*", default=None)
    edit_parser.add_argument("--project-root", default=None)
    edit_parser.add_argument("--repo-url", default=None)
    edit_parser.add_argument("--default-branch", default=None)
    edit_parser.add_argument("--workspace-path", default=None)
    edit_parser.add_argument("--repo-project-key", default=None)

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
    if args.command == "edit":
        return command_edit(args, registry, registry_path)
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
