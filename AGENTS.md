# AGENTS.md

This repository uses explicit repo-native memory.
Do not rely on old chat history as the primary source of truth.

## Core operating rule

Start every meaningful session by orienting yourself from repo files.
Do not make hidden assumptions about the current project, current task, or prior decisions.

## Non-negotiables

- The laptop is a working environment, not the canonical home of the system.
- Git is the source of truth for code, docs, configs, prompts, schemas, infra definitions, and lightweight workspace memory.
- Azure is the durable home for large artifacts, datasets, logs, manifests, reports, and other expensive-to-recreate outputs.
- PostgreSQL or another database comes later only when structured operational state truly needs query/update behavior.
- Research, orchestration, and execution concerns must stay clearly separated.
- If something matters, write it down in the repo or store it durably.

## Session start protocol

Before doing meaningful work:

1. Read `AGENTS.md`
2. Read `docs/SYSTEM_OPERATING_MANUAL.md`
3. Read `workspace/CURRENT_CONTEXT.md`
4. Ask the user: `Which project are we working on today?`

Only after the user answers, read the selected project's files:

- `workspace/projects/<project>/state.json`
- `workspace/projects/<project>/tasks.json`
- `workspace/projects/<project>/constraints.md`
- `workspace/projects/<project>/ops.md`
- `workspace/projects/<project>/active_plan.md` if present
- `workspace/projects/<project>/progress.md` if present
- `workspace/projects/<project>/failure_registry.md` if present
- latest file in `workspace/projects/<project>/sessions/`

Then:

5. Summarize the current state in plain language
6. Run the lightweight health check if available
7. Propose today's 1–3 concrete tasks
8. State the intended verification/check step
9. Begin work

Do not skip step 4 unless the active project is already explicitly provided in the current session.

## Context retrieval order

When gathering context, prefer this order:

1. Stable operating docs
2. Current workspace context
3. Project state and task files
4. Active project plan
5. Project progress and failure records
6. Latest session notes
7. Typed machine-readable memory objects when present
8. Recorded run manifests and checks when relevant

If two sources conflict, prefer the newer structured source unless the user explicitly overrides it.

## Machine-readable-first rule

Prefer machine-readable state wherever practical.

Use human-readable prose mainly for:
- architecture
- strategy
- runbooks
- ADRs
- high-level operating guidance

Prefer machine-readable formats for:
- project state
- tasks
- memory objects
- run manifests
- checks
- registries
- status summaries
- configuration

When adding new operational memory, prefer a structured object first and a prose summary second.

## Working rules

- Propose narrow, testable steps instead of vague large plans.
- Prefer explicit files over hidden state.
- Prefer reversible changes.
- Prefer updating existing canonical files over inventing redundant notes.
- Do not put secrets in the repo.
- Do not treat temporary local files as durable memory.
- Do not introduce unnecessary infrastructure early.
- Keep the same underlying code path usable locally and later in cloud/paper/live contexts.

## Verification rule

Every meaningful change should have a verification step.

Examples:
- command runs successfully
- test passes
- file was created or updated correctly
- structured output exists
- manifest/check file matches expectations

Before declaring success, verify the result.

## Write-back rule

When work changes project state, the agent must update the relevant memory layer.

Typical write-back targets:
- `workspace/CURRENT_CONTEXT.md`
- `workspace/projects/<project>/state.json`
- `workspace/projects/<project>/tasks.json`
- `workspace/projects/<project>/active_plan.md`
- `workspace/projects/<project>/progress.md`
- `workspace/projects/<project>/failure_registry.md`
- project session note
- typed memory objects when present

## Single-writer workspace rule

Only one agent should write to workspace memory files in a given session unless explicit coordination is in place.

This applies especially to:
- `workspace/CURRENT_CONTEXT.md`
- `workspace/projects/<project>/state.json`
- `workspace/projects/<project>/tasks.json`
- `workspace/projects/<project>/active_plan.md`
- `workspace/projects/<project>/progress.md`
- `workspace/projects/<project>/failure_registry.md`

Other agents may read these files, but workspace writes should have one active owner per session.

## Session brief rule

A generated `session_brief.md` is allowed as a convenience artifact, but it is derived output only.

It is not a source of truth.
Canonical truth remains in the underlying repo files.

## Close-session rule

When closing a session:

- capture the objective
- capture completed work
- capture important decisions
- capture blockers/issues
- capture next actions
- update memory files
- update project state
- update tasks if needed
- refresh current context
- run the health check if appropriate
- commit meaningful completed work
- push to GitHub
- append project session note
- record cross-project lessons only if they are genuinely reusable

## Safety rule

Execution-related code must remain minimal, explicit, auditable, and heavily logged.
Do not casually mix research logic with broker/execution logic.
