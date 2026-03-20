# SYSTEM OPERATING MANUAL

## Purpose

This document explains how the local-first AI lab works, where things belong, and how sessions should be run and recovered.

## Core goal

Build a local-first Python development system where:

- work happens directly on the laptop
- AI agents can read the real repo and project documents
- important project context lives in files, not only in chat history
- the laptop is replaceable if lost, wiped, or destroyed
- Git stores canonical code and docs
- Azure later stores durable large outputs, artifacts, and datasets
- the architecture can evolve toward research, paper trading, and tightly controlled execution

## Operating model

The local system uses four layers:

- Windows 11 = operator cockpit
- Ubuntu in WSL = primary development environment
- Git = canonical code/docs/workspace memory store
- Azure = durable large-file and artifact store later

Mental model:

- Windows = control room
- Ubuntu/WSL = workshop
- Git = memory and source of truth
- Azure = durable warehouse

## What belongs where

### Git / repo

Should contain:

- source code
- docs
- configs
- schemas
- tests
- infra definitions
- workspace memory files
- project state files
- scripts
- runbooks
- ADRs

Should not contain:

- secrets
- large datasets
- bulky artifacts
- large caches
- disposable scratch files

### Azure later

Should contain:

- recorded run manifests
- full run output folders
- logs
- plots
- parquet datasets
- preserved historical data
- expensive-to-recreate caches
- paper-trading artifacts later
- execution audit records later

## System planes

### Research plane

Purpose:

- gather data
- run backtests
- generate signals
- test ideas
- produce reports

This plane does not place live trades.

### Orchestration plane

Purpose:

- schedule jobs
- manage job execution
- move artifacts
- promote results
- manage automation flow

### Execution plane

Purpose:

- broker connectivity
- order creation
- order submission
- fills and reconciliation
- risk controls
- kill switch behavior

This plane must be minimal, explicit, auditable, and heavily logged.

## Repo structure

- `src/` core application code
- `jobs/` runnable workflows
- `configs/` local, cloud, paper, live configs
- `docs/` manuals, runbooks, ADRs
- `workspace/` rolling AI/operator memory
- `scripts/` bootstrap, dev, workspace, cloud, recovery helpers
- `infra/` infrastructure definitions
- `tests/` test suite
- `schemas/` structured file contracts
- `outputs/` local outputs
- `data/` local data staging

## Stable memory vs rolling memory

### Stable memory

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

### Rolling memory

Live session context belongs in:

- `workspace/CURRENT_CONTEXT.md`
- `workspace/global/gotchas.md`
- `workspace/global/patterns.md`
- `workspace/global/improvements.md`
- `workspace/global/last_context.json`
- `workspace/projects/<project>/state.json`
- `workspace/projects/<project>/tasks.json`
- `workspace/projects/<project>/constraints.md`
- `workspace/projects/<project>/ops.md`
- `workspace/projects/<project>/sessions/`

## Session workflow

### Start session

Read in this order:

1. `AGENTS.md`
2. `docs/SYSTEM_OPERATING_MANUAL.md`
3. `workspace/CURRENT_CONTEXT.md`

Then identify the project and read:

4. `workspace/projects/<project>/state.json`
5. `workspace/projects/<project>/tasks.json`
6. `workspace/projects/<project>/constraints.md`
7. `workspace/projects/<project>/ops.md`
8. latest project session note

Then propose today's 1-3 tasks.

### Close session

On close:

- capture the objective
- capture completed work
- capture important decisions
- capture blockers
- capture next actions
- update `state.json`
- update `tasks.json` if needed
- append a project session note
- append a global session note if cross-project learning matters
- refresh `workspace/CURRENT_CONTEXT.md`

## Naming conventions

### Files

Use lowercase snake_case for most files, for example:

- `rebuild_from_zero.md`
- `start_session.py`
- `close_session.py`

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

## Recorded run contract

A meaningful recorded run should eventually look like:

`outputs/<run_id>/`

With files such as:

- `manifest.json`
- `config_used.json`
- `result.json`
- `checks.json`
- `review.md`
- `logs.jsonl`
- `plots/`

## Recovery standard

A full rebuild should eventually be possible from:

- Git repository
- Azure storage
- documented secrets inventory
- rebuild instructions in docs

No critical part of the system should depend on memory alone.

## Current rule

Develop locally, keep repo memory explicit, keep the laptop replaceable, and add cloud and execution layers only after the local-first foundation is clean and working.
