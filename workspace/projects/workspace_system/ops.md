# ops

## Startup order (repo_backed)

1. Codex starts in canonical repo.
2. Codex reads repo startup files.
3. Start Workspace reads the last saved Drive continuity state and mirrored repo artifacts:
   - `_ai/projects/<project_slug>/repo_snapshot/latest_interpreter_snapshot.json`
   - `_ai/projects/<project_slug>/repo_snapshot/latest_codex_published_state.v1.json` (with repo-local fallback)
4. Start Workspace emits `SESSION_CONTEXT_JSON`.
5. ChatGPT plans.
6. Codex executes after planning.

Refresh policy:
- Do not regenerate startup artifacts by default.
- Regenerate only if artifacts are missing, stale, invalid, or explicitly requested.

Stable operating contract path (Drive continuity lane):
- `_ai/projects/<project_slug>/operating_rules.md`

Append-only action trail path:
- `_ai/projects/<project_slug>/sessions.log.jsonl`

## Close order (repo_backed)

1. Codex updates repo memory.
2. Codex commits.
3. Codex pushes.
4. Codex exports snapshot.
5. Codex exports handoff.
6. Close Workspace consumes handoff and updates Drive continuity files.

## Strategy -> Codex task contract v1

Task location:
- `_ai/projects/<project_slug>/codex_tasks/`

Filename convention:
- `<created_at_compact>__<task_id>.codex_task.v1.json`
- example: `20260423T001500Z__ctask_workspace_system_001.codex_task.v1.json`

Contract:
- schema: `schemas/workspace/codex_task.v1.json`
- required priority: `low | normal | high | urgent`
- status lifecycle: `ready -> accepted -> in_progress -> completed` with terminal alternatives `blocked` or `cancelled`

In this pass, the Strategy -> Codex task contract is formalized (v1 schema, location, naming, and lifecycle), but operating usage remains human-mediated/paste-driven; no automated queue processor is introduced.

## Artifact roles: codex_published_state vs codex_handoff

- `codex_published_state`:
  - produced by: `scripts/workspace/export_repo_context.py publish-state`
  - startup/current code-domain status artifact
  - startup consumption: Start Workspace reads this artifact (Drive mirror first, repo-local fallback)
  - authorship/placement: repo-authored, mirrored to Drive for strategy-side reading
  - close consumption: not consumed by Close Workspace

- `codex_handoff`:
  - produced by: `scripts/workspace/export_repo_context.py handoff`
  - close/session-end continuity handoff artifact
  - startup consumption: not consumed by Start Workspace
  - close consumption: required input for repo_backed close flow

The two artifacts are independent artifacts, not delta/patch versions of each other.
