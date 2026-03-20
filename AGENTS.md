# AGENTS.md

This repository uses repo-native memory. Do not rely on chat history as the primary source of truth.

## Required read order before meaningful changes

1. `docs/SYSTEM_OPERATING_MANUAL.md`
2. `workspace/CURRENT_CONTEXT.md`

If a project is selected, then also read:

3. `workspace/projects/<project>/state.json`
4. `workspace/projects/<project>/tasks.json`
5. `workspace/projects/<project>/constraints.md`
6. `workspace/projects/<project>/ops.md`
7. latest file in `workspace/projects/<project>/sessions/`

## Expected session behavior

- Ask which project we are working on if it is not obvious
- Propose the next 1-3 concrete tasks before large edits
- Keep research code separate from broker/execution code
- Prefer simple, explicit, inspectable files over hidden state
- Do not put secrets in the repo
- Do not treat local scratch files as durable system memory
- When closing a session, update project state, tasks, and session notes

## Source-of-truth rules

- Git repo is the source of truth for code, docs, configs, and workspace memory
- Azure is for durable large outputs, artifacts, logs, and datasets later
- The laptop is a working environment, not the canonical home of the system

## Naming rules

- Use lowercase snake_case for most files and directories
- Use conventional uppercase only where appropriate, such as `README.md` and `AGENTS.md`

## Safety rules

- Keep execution code minimal, explicit, and auditable
- Do not casually mix research and execution concerns
- Prefer reversible changes
- Record important decisions in docs or session notes
