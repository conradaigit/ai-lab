# Launcher Agent Contract

This contract defines the startup handoff between the launcher notebook and the AI agent.

## Block 1

- Block 1 emits `LAUNCHER_READINESS_PACKET` only.
- The notebook is not the conversational layer.
- The AI agent is the human-facing selection layer.

Required AI-agent menu behavior:
- Present a numbered menu for non-archived/open projects.
- If one open project exists, option 1 should continue that project.
- If multiple open projects exist, option 1 should continue an existing project and list available open slugs.
- If no open projects exist, omit continue and start with new/add.

Required menu options:
- `1.) continue <best default open project>`
- `2.) start/add a new project`
- `3.) edit an existing project`
- `4.) manage archived/delete/list projects`

## Block 2

- Block 2 behavior is action-dependent:
  - `continue`/`start` -> `SESSION_CONTEXT_JSON`
  - `list`/`archive`/`delete`/`add`/`edit` -> direct command-result JSON

After Block 2:
- The AI agent must interpret returned JSON according to the action type.
- For `SESSION_CONTEXT_JSON`, the AI agent should summarize context and continue planning.
- For command-result JSON, the AI agent should report result and ask for next action.

## Context Rule

- Do not rely on prior chat context.
- Treat launcher packet outputs as sufficient structured handoff for a fresh agent session.
