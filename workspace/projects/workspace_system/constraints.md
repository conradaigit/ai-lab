# constraints

- Keep `repo_backed` implementation canonical in repo; do not duplicate as Drive canonical state.
- Keep `drive_native` canonical state in Drive.
- Emit exactly one machine-readable `SESSION_CONTEXT_JSON` payload from Start Workspace.
- Emit one machine-readable close receipt from Close Workspace.
- Do not modify `/mnt/g/My Drive/_ai` directly during development verification without explicit user approval.
