#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_FILES = [
    "AGENTS.md",
    "docs/SYSTEM_OPERATING_MANUAL.md",
    "workspace/CURRENT_CONTEXT.md",
    "workspace/global/last_context.json",
    "workspace/projects/trading_system/state.json",
    "workspace/projects/trading_system/tasks.json",
    "workspace/projects/trading_system/constraints.md",
    "workspace/projects/trading_system/ops.md",
    "workspace/projects/trading_system/active_plan.md",
    "workspace/projects/trading_system/progress.md",
    "workspace/projects/trading_system/failure_registry.md",
    "schemas/memory_object_base.json",
    "docs/SECRETS_INVENTORY.md",
]


def add_result(bucket: dict[str, list[str]], level: str, message: str) -> None:
    bucket[level].append(message)


def parse_json_file(path: Path) -> tuple[bool, str | None]:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True, None
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]

    results: dict[str, list[str]] = {
        "error": [],
        "warning": [],
        "info": [],
    }

    for rel in REQUIRED_FILES:
        path = repo_root / rel
        if not path.exists():
            add_result(results, "error", f"Missing required file: {rel}")

    current_context = repo_root / "workspace" / "CURRENT_CONTEXT.md"
    if current_context.exists():
        text = current_context.read_text(encoding="utf-8").strip()
        if not text:
            add_result(results, "error", "workspace/CURRENT_CONTEXT.md exists but is empty.")

    json_candidates: list[Path] = []
    for base in [repo_root / "workspace", repo_root / "memory" / "objects", repo_root / "schemas"]:
        if base.exists():
            json_candidates.extend(base.rglob("*.json"))

    for path in sorted(json_candidates):
        ok, err = parse_json_file(path)
        rel = path.relative_to(repo_root)
        if not ok:
            add_result(results, "error", f"Invalid JSON in {rel}: {err}")

    receipt_path = repo_root / "workspace" / "close_session_receipt.json"
    if receipt_path.exists():
        ok, err = parse_json_file(receipt_path)
        if ok:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            status = receipt.get("status")
            if status in {"in_progress", "failed"}:
                add_result(
                    results,
                    "warning",
                    f"close_session_receipt.json is in '{status}' state. Previous close may have been incomplete."
                )
        else:
            add_result(results, "error", f"Invalid JSON in workspace/close_session_receipt.json: {err}")
    else:
        add_result(results, "info", "No close_session_receipt.json present yet.")

    current_context_mtime = None
    if current_context.exists():
        current_context_mtime = datetime.fromtimestamp(
            current_context.stat().st_mtime,
            tz=timezone.utc,
        )
        age_days = (datetime.now(timezone.utc) - current_context_mtime).days
        if age_days > 7:
            add_result(
                results,
                "warning",
                f"workspace/CURRENT_CONTEXT.md is {age_days} days old. Review for staleness."
            )

    summary = {
        "status": "error" if results["error"] else "ok",
        "checked_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "results": results,
    }

    print(json.dumps(summary, indent=2))
    return 1 if results["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
