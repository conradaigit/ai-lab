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

## Close order (repo_backed)

1. Codex updates repo memory.
2. Codex commits.
3. Codex pushes.
4. Codex exports snapshot.
5. Codex exports handoff.
6. Close Workspace consumes handoff and updates Drive continuity files.
