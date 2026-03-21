# ENVIRONMENTS

## Purpose

This document describes the environments used by the repo today, the roles of those environments, and the boundaries between local development, repo state, and future cloud-hosted infrastructure.

## Exists Now

### Environment model overview

The current environment model is intentionally simple:

- Windows 11 is the operator-facing host environment
- Ubuntu in WSL is the primary development environment
- VS Code connects into WSL and operates against the real repo
- Git holds canonical code, docs, configs, and lightweight workspace memory

### Current environments

#### Windows 11 host

Role:

- operator desktop
- GUI applications
- host for WSL and VS Code

This is not the canonical home of project state.

#### Ubuntu in WSL

Role:

- primary shell environment
- primary development environment
- place where scripts and repo commands are run

This is the main working environment for the repo today.

#### VS Code + WSL remote

Role:

- editor and IDE surface for the repo
- WSL-backed project window
- path used for the current local Codex workflow

The intended path is to open the repo from WSL with `code .` and work against `/home/conradunix/dev/ai-lab`.

The expected state is a VS Code repo window connected as `[WSL: Ubuntu]`.

### Canonical development environment

The canonical day-to-day development environment today is:

- Ubuntu in WSL
- repo rooted at `~/dev/ai-lab`
- VS Code connected through WSL
- startup guided by `AGENTS.md` and the workspace/project memory files

### Tooling expectations today

Current expected tooling includes:

- `bash`
- `git`
- `python3`
- VS Code
- WSL remote workflow
- Codex working against the live repo and workspace memory

### Data, config, and secrets boundaries

#### In repo

Allowed in the repo:

- code
- docs
- configs
- prompts
- schemas
- tests
- lightweight workspace memory

#### Out of repo

Not allowed in Git:

- secrets
- large durable data
- bulky generated outputs
- large caches

For secret handling, see `docs/SECRETS_INVENTORY.md`.

### Verification and health

The current lightweight environment checks are:

- `git status`
- `python3 scripts/dev/health_check.py`
- `python3 scripts/workspace/start_session.py trading_system`

### Known current pitfalls

Observed or documented local pitfalls include:

- large multiline paste problems in older terminal flows
- the need to prefer Windows Terminal for WSL usage
- display scaling issues can affect terminal usability on the local machine setup

## Planned / Not Yet Implemented

### Azure-backed artifact environment

Azure is part of the target operating model for durable artifacts, but it is not yet described here as a fully implemented development environment.

### Cloud-backed research environment

Cloud-backed research workflows are a future direction, not a current operating requirement.

### Paper-trading and live execution environments

The repo contains future-oriented structure for paper-trading and execution concerns, but those environments are not currently active or defined as operational.

### Database-backed operational environment

There is no current database-backed operational environment. A database comes later only if structured operational state truly requires it.

## Environment rules

- work locally first
- keep the repo as the continuity layer
- keep secrets out of Git
- keep large durable artifacts out of Git
- prefer the same underlying code path across local and future cloud/paper/live contexts
- do not casually mix research logic with execution logic
