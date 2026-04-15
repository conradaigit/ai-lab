# CURRENT_CONTEXT

## Active project
workspace_system

## Current focus
Frozen v1 workspace contracts and scripts are implemented. Immediate focus is wiring the notebook cells and running real Drive end-to-end validation.

## Last completed work
- Added frozen v1 schemas for registry/session context/codex handoff/close receipt
- Implemented repo exporter outputs in `scripts/workspace/export_repo_context.py`
- Implemented Start Workspace flow in `scripts/workspace/start_workspace.py`
- Implemented Close Workspace flow in `scripts/workspace/close_workspace.py`
- Verified dry-runs for both `repo_backed` and `drive_native` branches with `py_compile` passing

## Next 1-3 actions
1. Integrate script-equivalent logic into actual Colab Start Workspace notebook cells
2. Integrate script-equivalent logic into actual Colab Close Workspace notebook cells
3. Run one real Drive end-to-end trial for both project types and confirm the `SESSION_CONTEXT_JSON`/handoff loop

## Important files to review first
- `AGENTS.md`
- `docs/SYSTEM_OPERATING_MANUAL.md`
- `workspace/registry/projects.json`
- `schemas/workspace/projects_registry.v1.json`
- `schemas/workspace/session_context.v1.json`
- `schemas/workspace/codex_handoff.v1.json`
- `schemas/workspace/close_workspace_receipt.v1.json`
- `workspace/projects/workspace_system/state.json`
- `workspace/projects/workspace_system/tasks.json`

## Notes
- Runtime path mapping should resolve Drive-relative roots per environment:
  - Colab: `/content/drive/MyDrive/...`
  - WSL: `/mnt/g/My Drive/...`
- Runtime exporter files remain local runtime artifacts and are intentionally ignored in Git.
