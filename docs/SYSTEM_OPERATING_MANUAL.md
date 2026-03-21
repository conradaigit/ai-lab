# SYSTEM OPERATING MANUAL

## Purpose

This document explains how the local-first AI lab works, where things belong, how agents should operate, and how the system should evolve without losing rebuildability or reliability.

## Core goal

Build a local-first Python development system where:

- work happens directly on the laptop
- AI agents can read the real repo and project documents
- important project context lives in files, not only in chat history
- the laptop is replaceable if lost, wiped, or destroyed
- Git holds the canonical text/code system
- Azure holds durable large outputs, artifacts, and datasets
- the architecture can later grow into cloud-backed research, paper trading, and tightly controlled live execution

## Core principles

### Replaceable laptop principle

The laptop is a working environment, not the canonical home of the system.

Anything important must be recoverable from:
- Git
- Azure
- documented rebuild instructions
- documented environment and secrets setup

### Canonical source principle

Git is the source of truth for:

- code
- docs
- configs
- prompts
- schemas
- tests
- infra definitions
- workspace memory files
- project notes and plans
- typed memory objects

### Durable artifact principle

Azure is the source of truth for:

- recorded run manifests
- full run output folders
- logs
- plots
- reports
- parquet datasets
- preserved historical data
- expensive-to-recreate caches
- paper-trading artifacts later
- execution audit records later

### Rebuildability principle

No critical part of the system should depend on memory alone.

If something matters, it must be:
- written down in the repo
- or stored durably in Azure
- or both

### Same-code-path principle

A workflow should use the same underlying code whether run:
- locally for development
- in the cloud for scale
- later in paper-trading or execution contexts

### Separation-of-concerns principle

The system is separated into:
- Research plane
- Orchestration plane
- Execution plane

Research code should not be casually mixed with broker execution code.

## Local operating model

The local system uses four layers:

- Windows 11 = operator cockpit
- Ubuntu in WSL = primary development environment
- Git = canonical code/docs/memory store
- Azure = durable large-file and artifact store

Mental model:

- Windows = control room
- Ubuntu/WSL = workshop
- Git = memory and source of truth
- Azure = durable warehouse

Windows and Ubuntu/WSL run at the same time.
This is not dual boot.

## What belongs where

### Git / repo

Should contain:

- source code
- docs
- configs
- prompts
- schemas
- tests
- infra definitions
- workspace memory files
- project state files
- scripts
- runbooks
- ADRs
- typed memory objects
- lightweight plans and operating notes

Should not contain:

- secrets
- large datasets
- bulky generated artifacts
- large caches
- disposable scratch files

### Azure

Should contain:

- recorded run manifests
- full run output folders
- logs
- plots
- reports
- parquet datasets
- preserved historical data
- expensive-to-recreate caches
- paper-trading artifacts later
- execution audit records later

### Local-only content

May remain local unless promoted:

- temporary scratch outputs
- disposable caches
- one-off experiments
- staging files
- temporary transfer files

## Database strategy

Do not start with a database for everything.

Use:
- repo files for code/docs/lightweight state
- JSON/TOML/YAML/manifests for structured lightweight state
- Parquet and Azure Blob / ADLS for large data and artifacts

Add PostgreSQL later only when it is genuinely needed for structured operational state such as:
- run registry tables
- signal history
- paper-trading ledger
- orders
- fills
- positions
- reconciliation state
- execution events

Rule of thumb:

- code/docs/state files -> Git
- large files/datasets/artifacts -> Azure Blob / ADLS
- queryable operational records -> PostgreSQL later

## Memory model

The system uses layered memory.

### Layer 1: stable human-readable docs

Long-lived truth belongs in docs such as:

- `docs/SYSTEM_OPERATING_MANUAL.md`
- `docs/ARCHITECTURE.md`
- `docs/REPO_MAP.md`
- `docs/REBUILD_FROM_ZERO.md`
- `docs/ENVIRONMENTS.md`
- `docs/DATA_CATALOG.md`
- `docs/SECRETS_INVENTORY.md`
- `docs/RUNBOOKS/`
- `docs/ADR/`

These are primarily for architecture, strategy, runbooks, and durable operating knowledge.

### Layer 2: rolling workspace memory

Live project context belongs in:

- `workspace/CURRENT_CONTEXT.md`
- `workspace/global/gotchas.md`
- `workspace/global/patterns.md`
- `workspace/global/improvements.md`
- `workspace/global/last_context.json`
- `workspace/projects/<project>/state.json`
- `workspace/projects/<project>/tasks.json`
- `workspace/projects/<project>/constraints.md`
- `workspace/projects/<project>/ops.md`
- `workspace/projects/<project>/active_plan.md`
- `workspace/projects/<project>/progress.md`
- `workspace/projects/<project>/failure_registry.md`
- `workspace/projects/<project>/sessions/`

### Layer 3: typed machine-readable memory

Atomic reusable memory should be stored as typed objects when practical.

Recommended categories:

- decisions
- tasks
- lessons
- artifacts
- entities
- relations

Recommended path:

- `memory/objects/decision/`
- `memory/objects/task/`
- `memory/objects/lesson/`
- `memory/objects/artifact/`
- `memory/objects/entity/`
- `memory/objects/relation/`

These objects should be small, structured, and linkable.

### Layer 4: durable run artifacts

Meaningful runs should produce:

- `manifest.json`
- `config_used.json`
- `result.json`
- `checks.json`
- `review.md`
- `logs.jsonl`
- plots and supporting outputs

If the run matters, it should be durably stored.

### Layer 5: later operational database

Only after the system truly needs queryable operational state.

## Machine-readable-first rule

Backend state should be optimized for machine-readable consumption wherever practical.

Human-readable prose is still required for:
- architecture
- strategy
- runbooks
- ADRs
- top-level operating guidance

But operational memory should prefer structured formats whenever practical.

That means:
- state should be structured
- tasks should be structured
- manifests should be structured
- checks should be structured
- atomic memory objects should be structured

## Session start workflow

The intended start-session flow is:

1. Agent reads `AGENTS.md`
2. Agent reads `docs/SYSTEM_OPERATING_MANUAL.md`
3. Agent reads `workspace/CURRENT_CONTEXT.md`
4. Agent asks: `Which project are we working on today?`
5. Once the user answers, agent reads:

   - `workspace/projects/<project>/state.json`
   - `workspace/projects/<project>/tasks.json`
   - `workspace/projects/<project>/constraints.md`
   - `workspace/projects/<project>/ops.md`
   - `workspace/projects/<project>/active_plan.md` if present
   - `workspace/projects/<project>/progress.md` if present
   - `workspace/projects/<project>/failure_registry.md` if present
   - latest project session note

6. Agent summarizes current project state
7. Agent proposes today's 1–3 tasks
8. Agent states the intended verification/check step
9. Work begins

The agent must not assume the active project without explicit confirmation unless the user already clearly specified it in the current session.

## Context retrieval policy

Preferred retrieval order:

1. stable operating docs
2. current workspace brief
3. project state and task files
4. active project plan
5. progress and failure records
6. latest session notes
7. typed memory objects
8. recorded runs, manifests, and checks

This keeps context focused without relying on hidden memory.

## Work loop

The preferred work loop is:

1. orient
2. retrieve the minimum necessary context
3. define the next narrow task
4. make the change
5. verify the result
6. write back state and lessons
7. continue or stop cleanly

For complex work, the system should prefer an explicit active plan plus bounded steps over large vague autonomous runs.

## Verification contract

Every meaningful task should have an explicit verification step.

Examples:

- command executes successfully
- test passes
- file exists with expected contents
- lint/type checks pass
- artifact was written
- manifest/check file was produced
- result matches expected schema

Never declare success before verifying.

## Active plan

Each meaningful project should have an `active_plan.md`.

Purpose:
- define the current objective
- define scope boundaries
- define assumptions
- define success criteria
- define ordered substeps
- define the current step
- define the next verification action

This is the live execution contract for the current body of work.

## Progress log

Each meaningful project should have a `progress.md`.

Purpose:
- record what was completed
- record partial results
- record failed approaches
- record why a failure occurred
- record what should be tried next

Failed approaches are important memory and should not be discarded.

## Failure registry

Each meaningful project should have a `failure_registry.md`.

Purpose:
- avoid repeating dead ends
- preserve lessons learned
- record why an approach failed
- record how the failure was detected
- record suggested alternatives

## Close-session workflow

When the user says `Close session`, the intended flow is:

- capture the objective
- capture completed work
- capture important decisions
- capture blockers/issues
- capture next actions
- update memory files
- update project `state.json`
- update project `tasks.json` if needed
- update `active_plan.md` if needed
- update `progress.md` if needed
- update `failure_registry.md` if needed
- run the health check if appropriate
- commit meaningful completed work
- push to GitHub
- append a project session note
- append a global session note only if cross-project learning matters
- refresh `workspace/CURRENT_CONTEXT.md`

## Distillation rule

After meaningful work, do not only save raw notes.

Distill reusable outputs into:
- tasks
- decisions
- lessons
- artifacts
- linked references to runs or files

This makes future agent retrieval more reliable.

## Orchestration rule

Session-scoped looping inside a live agent session is a convenience only.

Durable automation must live in:
- scripts
- local schedulers
- GitHub Actions
- Azure jobs
- other explicit orchestration layers

Do not depend on a chat session remaining open for durable operations.

## Repo structure

High-level structure:

- `src/` core application code
- `jobs/` runnable workflows
- `configs/` local, cloud, paper, live configs
- `docs/` manuals, runbooks, ADRs
- `workspace/` rolling AI/operator memory
- `memory/` typed machine-readable memory objects
- `scripts/` bootstrap, dev, workspace, cloud, recovery helpers
- `infra/` infrastructure definitions
- `tests/` test suite
- `schemas/` structured file contracts
- `outputs/` local outputs
- `data/` local data staging

## Naming conventions

### Files

Use lowercase snake_case for most files, for example:

- `rebuild_from_zero.md`
- `start_session.py`
- `close_session.py`
- `failure_registry.md`

Use conventional uppercase where appropriate:

- `README.md`
- `AGENTS.md`

### Directories

Use lowercase snake_case, for example:

- `paper_trading`
- `execution`
- `recovery`
- `feature_sets`

### Configs

Pattern:

`<domain>_<purpose>_<environment>.json`

Examples:

- `finance_backtest_local.json`
- `finance_signal_cloud.json`
- `execution_paper_ibkr.json`

### ADR files

Pattern:

`ADR-XXXX_short_title.md`

### Run IDs

Pattern:

`YYYYMMDD_HHMMSS_<job>_<shortsha>`

## Recovery standard

A full rebuild should eventually be possible from:

- Git repository
- Azure storage
- documented secrets inventory
- rebuild instructions in docs

Rebuilding must not depend on remembering past chats.

## Current operating rule

Develop locally.
Run code primarily in Ubuntu/WSL.
Use Windows as the control surface.
Store code/docs/workspace memory in Git.
Store meaningful outputs and large data durably in Azure.
Keep the laptop replaceable.
Move toward cloud-backed research first, then paper trading, then tightly controlled execution.
