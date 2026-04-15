# ops

## Startup order (repo_backed)

1. Codex starts in canonical repo.
2. Codex reads repo startup files.
3. Codex exports fresh interpreter snapshot.
4. Start Workspace loads Drive memory and Drive-mirrored snapshot.
5. Start Workspace emits `SESSION_CONTEXT_JSON`.
6. ChatGPT plans.
7. Codex executes after planning.

## Close order (repo_backed)

1. Codex updates repo memory.
2. Codex commits.
3. Codex pushes.
4. Codex exports snapshot.
5. Codex exports handoff.
6. Close Workspace consumes handoff and updates Drive continuity files.
