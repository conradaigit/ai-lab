# REPO_MAP

## Purpose

This document is a practical map of the repository. It explains where things live today, which paths matter first, and which directories are present mainly as scaffolding for later work.

## Exists Now

### Top-level paths

- `AGENTS.md`
  Session operating rules and startup protocol.
- `docs/`
  Stable human-readable operating documents and reference docs.
- `workspace/`
  Rolling workspace memory and project state.
- `memory/`
  Typed memory object scaffolding.
- `schemas/`
  Shared schemas, including the base memory object schema.
- `scripts/`
  Operational scripts and helpers.
- `src/`
  Application and domain code areas.
- `tests/`
  Test area.
- `configs/`
  Configuration area, with local/cloud/paper/live subdivisions present.
- `infra/`
  Infrastructure-oriented placeholders and definitions.
- `jobs/`
  Job-oriented placeholders grouped by domain.
- `data/`
  Local data area; ignored by Git except for keep-files.
- `outputs/`
  Local output area; ignored by Git except for keep-files.

### Memory-layer distinction

- `docs/`
  Stable human-readable operating knowledge.
- `workspace/`
  Live rolling memory for current context, project state, plans, and session continuity.
- `memory/`
  Typed reusable machine-readable memory.

### Canonical files to read first

For meaningful work, start with:

1. `AGENTS.md`
2. `docs/SYSTEM_OPERATING_MANUAL.md`
3. `workspace/CURRENT_CONTEXT.md`
4. project-specific files under `workspace/projects/<project>/`

### Docs map

- `docs/SYSTEM_OPERATING_MANUAL.md`
  Stable operating model and system rules.
- `docs/SECRETS_INVENTORY.md`
  Secrets handling policy and inventory placeholders.
- `docs/ADR/`
  Reserved for architecture decision records.
- `docs/RUNBOOKS/`
  Reserved for runbooks.

### Workspace map

- `workspace/CURRENT_CONTEXT.md`
  Cross-session rolling context for the currently active work.
- `workspace/global/gotchas.md`
  Reusable pitfalls and operational cautions.
- `workspace/global/patterns.md`
  Reusable patterns.
- `workspace/global/improvements.md`
  Workspace-wide improvement ideas.
- `workspace/global/last_context.json`
  Machine-readable rolling context.
- `workspace/projects/trading_system/state.json`
  Structured project state.
- `workspace/projects/trading_system/tasks.json`
  Structured task list.
- `workspace/projects/trading_system/constraints.md`
  Project constraints.
- `workspace/projects/trading_system/ops.md`
  Project operating guidance.
- `workspace/projects/trading_system/active_plan.md`
  Current project plan.
- `workspace/projects/trading_system/progress.md`
  Project progress summary.
- `workspace/projects/trading_system/failure_registry.md`
  Recorded failures and mitigations.
- `workspace/projects/trading_system/sessions/`
  Historical session notes.

### Typed memory map

- `memory/objects/decision/`
- `memory/objects/task/`
- `memory/objects/lesson/`
- `memory/objects/artifact/`
- `memory/objects/entity/`
- `memory/objects/relation/`

These directories currently exist as scaffolding for small structured memory objects.

### Schema map

- `schemas/memory_object_base.json`
  Base schema for typed memory objects.

### Scripts map

- `scripts/dev/health_check.py`
  Lightweight repo health check.
- `scripts/workspace/start_session.py`
  Session startup helper.
- `scripts/workspace/close_session.py`
  Session close helper.
- `scripts/bootstrap/`
- `scripts/cloud/`
- `scripts/recovery/`

The last three script directories exist, but are not yet populated with substantial implemented workflows.

### Runtime-only / non-committed files

These files may exist locally but are not intended as durable repo memory:

- `workspace/close_session_receipt.json`
  Rolling runtime receipt file used by session-close/start behavior. It should not be committed.
- local `.env` files if used
- generated caches such as `__pycache__/`
- local data under `data/`
- local outputs under `outputs/`

## Planned / Not Yet Implemented

### Planned-but-lightly-populated areas

The following paths exist as placeholders or future-oriented structure and should not be treated as fully implemented systems:

- `configs/cloud/`
- `configs/paper/`
- `configs/live/`
- `infra/azure/`
- `infra/broker/`
- `jobs/research/`
- `jobs/reporting/`
- `jobs/paper_trading/`
- `jobs/execution/`

### Future docs expected by the operating model

The operating model expects docs such as:

- `docs/ARCHITECTURE.md`
- `docs/REPO_MAP.md`
- `docs/REBUILD_FROM_ZERO.md`
- `docs/ENVIRONMENTS.md`
- `docs/DATA_CATALOG.md`

Some of these are being added now; others remain future documentation targets.

## Placement rules

When adding new material:

- stable operating guidance goes in `docs/`
- rolling current state goes in `workspace/`
- typed reusable memory goes in `memory/objects/`
- shared schemas go in `schemas/`
- operational helpers go in `scripts/`
- source code goes in `src/`
- tests go in `tests/`
- large outputs or scratch artifacts should stay out of Git

## Things that should not go in Git

- secrets
- committed runtime receipts
- bulky generated outputs
- large datasets
- large caches
- disposable scratch files
