# ARCHITECTURE

## Purpose

This document describes the operating architecture of the local-first AI lab as it exists today, along with the boundaries that should remain stable as the system grows.

It is intentionally focused on:

- operating model
- source-of-truth rules
- memory layers
- separation of concerns
- current versus planned architecture

It is not a claim that cloud, database, scheduling, or execution infrastructure is already implemented.

## Exists Now

### Core operating model

The system currently operates as a local-first development environment built around four practical layers:

- Windows 11 as the operator cockpit
- Ubuntu in WSL as the primary development environment
- Git as the canonical store for code, docs, configs, prompts, schemas, tests, infra definitions, and lightweight workspace memory
- the repo itself as the working surface for project state, plans, and agent-readable operating context

This means the laptop is where work happens, but the repo is where important text and lightweight operational state must live.

### Current canonical startup path

The current startup path for meaningful work is:

1. `AGENTS.md`
2. `docs/SYSTEM_OPERATING_MANUAL.md`
3. `workspace/CURRENT_CONTEXT.md`
4. project-specific files under `workspace/projects/<project>/`

For the active project, the project-specific layer currently includes:

- `workspace/projects/trading_system/state.json`
- `workspace/projects/trading_system/tasks.json`
- `workspace/projects/trading_system/constraints.md`
- `workspace/projects/trading_system/ops.md`
- `workspace/projects/trading_system/active_plan.md`
- `workspace/projects/trading_system/progress.md`
- `workspace/projects/trading_system/failure_registry.md`
- the latest session note in `workspace/projects/trading_system/sessions/`

This startup path is part of the operating architecture, not just a convenience workflow.

### Current architectural boundaries

The repo is organized around explicit boundaries:

- stable operating docs live in `docs/`
- live workspace memory lives in `workspace/`
- typed reusable memory is intended to live in `memory/objects/`
- schemas live in `schemas/`
- scripts live in `scripts/`
- application and domain code live under `src/`
- tests live under `tests/`

The architecture also preserves a conceptual separation between:

- research
- orchestration
- execution

That separation is already a rule, even though execution infrastructure is not yet built out.

### Memory layers

The current architecture uses layered memory.

#### Layer 1: Stable human-readable docs

These explain durable operating knowledge, architecture, runbooks, and rebuild instructions.

Current examples:

- `docs/SYSTEM_OPERATING_MANUAL.md`
- `docs/SECRETS_INVENTORY.md`

#### Layer 2: Rolling workspace memory

These files capture live project state and session-level operational context.

Current examples:

- `workspace/CURRENT_CONTEXT.md`
- `workspace/global/*.md`
- `workspace/global/last_context.json`
- `workspace/projects/trading_system/*.json`
- `workspace/projects/trading_system/*.md`

`workspace/close_session_receipt.json` is not part of historical memory. It is a rolling runtime reliability file used by session-close/start behavior and should not be committed.

#### Layer 3: Typed machine-readable memory

The repo already has the typed memory scaffolding and a base schema.

Current examples:

- `memory/objects/decision/`
- `memory/objects/task/`
- `memory/objects/lesson/`
- `memory/objects/artifact/`
- `memory/objects/entity/`
- `memory/objects/relation/`
- `schemas/memory_object_base.json`

#### Layer 4: Durable run artifacts

This layer is part of the architecture but is not fully established yet as a durable workflow. The repo reserves local areas such as `outputs/` and `data/`, but the durable artifact pattern is still future-facing.

### Current implemented operational helpers

The current repo includes lightweight operational support, not a full automation platform.

Implemented now:

- `scripts/dev/health_check.py`
- `scripts/workspace/start_session.py`
- `scripts/workspace/close_session.py`

These support session startup, session close behavior, and local health verification.

### Current development path

The current intended development path is:

- work in Ubuntu/WSL
- open the repo in VS Code through the WSL remote flow
- use Codex against the real repo and real workspace memory
- verify work before claiming success
- write back meaningful state changes into workspace memory

## Planned / Not Yet Implemented

### Durable artifact storage in Azure

Azure is the intended durable home for:

- recorded manifests
- logs
- reports
- plots
- preserved datasets
- expensive-to-recreate artifacts

That storage model is part of the target architecture, but the repo does not yet present it as a fully implemented workflow.

### Operational database

PostgreSQL or another database is planned only for the point where structured operational state truly requires query/update behavior.

Examples of later candidates:

- run registries
- signal history
- paper-trading ledger
- orders, fills, and positions
- reconciliation state
- execution events

This is not a current dependency.

### Cloud-backed research and controlled execution

The repo includes placeholder areas such as:

- `infra/azure/`
- `infra/broker/`
- `jobs/research/`
- `jobs/reporting/`
- `jobs/paper_trading/`
- `jobs/execution/`

These indicate intended growth paths, not already-operational services.

## Architectural guardrails

The following guardrails should remain true:

- the laptop is a working environment, not the canonical home
- Git is the canonical source of text, code, configs, and lightweight memory
- secrets do not belong in the repo
- large durable artifacts do not belong in Git
- research logic should not be casually mixed with broker or execution logic
- the same underlying code path should remain usable locally first, then later in cloud or paper/live contexts
- if something matters, it should be written down in the repo or stored durably
