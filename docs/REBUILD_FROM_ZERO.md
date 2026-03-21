# REBUILD_FROM_ZERO

## Purpose

This document describes how to rebuild the local working environment for this repo from a fresh machine without relying on chat history or undocumented local state.

It is a first-pass rebuild guide for the current local-first stage of the project.

## Exists Now

### Rebuild goal

A successful rebuild today means:

- a Windows 11 machine is available
- Ubuntu in WSL is installed and usable
- the repo is cloned locally
- the repo opens from WSL in VS Code
- the canonical startup path can be followed from repo files
- the lightweight health check runs successfully

### Assumptions

This guide assumes:

- the canonical repo is available in Git
- the operator has access to any required accounts
- secrets are provided out-of-band and are not recovered from the repo
- the current project is `trading_system`

### Minimal rebuild sequence

1. Install or enable WSL on Windows 11.
2. Install Ubuntu in WSL.
3. Install VS Code on Windows.
4. Install the VS Code WSL extension.
5. Install Git in the WSL environment if needed.
6. Clone the repo into a working path such as `~/dev/ai-lab`.
7. Ensure Python 3 is available in WSL.
8. Open a WSL shell in the repo root.
9. Open the repo from WSL using `code .`
10. Read the canonical startup files.
11. Run the lightweight verification commands.

### Canonical startup after clone

Once the repo is present, orient using:

1. `AGENTS.md`
2. `docs/SYSTEM_OPERATING_MANUAL.md`
3. `workspace/CURRENT_CONTEXT.md`
4. the selected project's files under `workspace/projects/<project>/`

### Post-rebuild verification commands

Run these from the repo root:

```bash
git status
python3 scripts/dev/health_check.py
python3 scripts/workspace/start_session.py trading_system
```

### What each command verifies

- `git status`
  Confirms the repo is present and shows the current working-tree state.
- `python3 scripts/dev/health_check.py`
  Confirms the basic repo health checks pass.
- `python3 scripts/workspace/start_session.py trading_system`
  Confirms the session startup helper runs against the current project.

### Environment and secrets notes

Secrets are not restored from the repo.

Use:

- `docs/SECRETS_INVENTORY.md` for the documented secrets pattern
- local environment variables
- optional non-committed `.env` files when needed

### Verification checklist

A rebuild is in a good state when:

- the repo is available under WSL
- VS Code opens the repo through WSL
- the startup path can be followed from repo files
- `git status` works
- the health check returns a healthy result
- the session-start helper runs without unexpected failure

## Planned / Not Yet Implemented

### Azure-backed artifact rebuild

The broader operating model expects durable artifacts to live in Azure later, but this repo does not yet provide a complete automated restore flow for Azure-hosted artifacts.

### Full environment automation

This repo does not yet claim:

- one-command machine bootstrap
- automated package installation across all tools
- automatic secret provisioning
- automated restoration of cloud resources
- automatic restoration of paper/live execution infrastructure

### Future rebuild improvements

Likely future improvements include:

- more detailed package prerequisites
- explicit VS Code extension guidance
- scripted bootstrap helpers
- artifact restore guidance for Azure
- fuller environment receipts or manifests

## Rebuild principles

The rebuild process should continue to preserve these rules:

- Git remains the canonical source for code, docs, configs, and lightweight memory
- secrets remain outside the repo
- durable large artifacts belong in Azure later, not in Git
- rebuild instructions should stay explicit and auditable
- no critical workflow should depend only on memory
