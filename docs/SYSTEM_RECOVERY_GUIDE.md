# SYSTEM_RECOVERY_GUIDE

Version: 2.0

## Purpose

This guide describes disaster recovery for the current local-first workspace so the system can be rebuilt without relying on chat history or undocumented local state.

Recovery now requires two lanes:

- Repo lane:
  - GitHub repository
  - local clone at `~/dev/ai-lab`
  - WSL + VS Code + Codex
- Continuity lane:
  - Google Drive `My Drive/_ai`
  - Google Drive `My Drive/Colab Notebooks`
  - launcher/close notebook workflow
  - Drive-mirrored repo artifacts for `repo_backed` projects

Repo recovery alone is no longer sufficient for full workflow recovery. Drive continuity and notebook access must also be restored.

## Exists Now

### What must already exist for recovery to work

- GitHub repository with latest pushed repo state
- access to the correct Google account and Drive containing:
  - `My Drive/_ai`
  - `My Drive/Colab Notebooks`
- a separate secrets restoration method
- Windows 11 hardware
- internet access

Storage roles in current architecture:

- GitHub stores repo/code/docs/scripts/schemas and repo-native project state
- Drive stores continuity memory and notebook UI layer
- secrets are not stored in the repo or this recovery guide

### Recovery outcome

A successful recovery now means all of the following are true:

- Windows 11 is running
- WSL + Ubuntu are installed
- VS Code is installed and opens the repo in WSL mode
- repo is cloned at `~/dev/ai-lab`
- Codex works in the WSL-backed repo
- Google Drive is accessible on Windows
- WSL can access Google Drive at `/mnt/g/My Drive`
- continuity files exist under `/mnt/g/My Drive/_ai`
- notebook files exist under `/mnt/g/My Drive/Colab Notebooks`
- launcher/close workflow can run again

### Minimal rebuild sequence

1. Install or enable WSL on Windows 11.
2. Install Ubuntu in WSL.
3. Install VS Code on Windows.
4. Install the VS Code WSL extension.
5. Install Google Drive for desktop on Windows.
6. Sign into the correct Google account.
7. Confirm `My Drive` is available on Windows (current setup typically uses `G:`).
8. In WSL, ensure the Drive mount path exists:

```bash
sudo mkdir -p /mnt/g
```

9. Ensure `/etc/fstab` contains:

```text
G: /mnt/g drvfs defaults 0 0
```

10. Mount and verify Drive visibility from WSL:

```bash
sudo mount -a
ls "/mnt/g/My Drive"
ls "/mnt/g/My Drive/_ai"
ls "/mnt/g/My Drive/Colab Notebooks"
```

11. Install Git in WSL if needed.
12. Clone repo to `~/dev/ai-lab`.
13. Ensure Python 3 is available in WSL.
14. Open repo from WSL using `code .`.

Recovery is incomplete if WSL cannot see `My Drive/_ai` and `My Drive/Colab Notebooks`.

### Canonical startup files after clone

Once repo is present, orient using:

1. `AGENTS.md`
2. `docs/SYSTEM_OPERATING_MANUAL.md`
3. `workspace/CURRENT_CONTEXT.md`
4. selected project files under `workspace/projects/<project>/`

### Post-rebuild verification

Run from repo root:

```bash
cd ~/dev/ai-lab
git status
python3 scripts/dev/health_check.py
git remote -v
git branch --show-current
```

Verify Drive continuity paths:

```bash
ls "/mnt/g/My Drive/_ai/projects"
ls "/mnt/g/My Drive/Colab Notebooks"
```

### Notebook/workflow verification

- open `AI_Workspace_Launcher.ipynb` in Colab
- run Block 1 successfully
- confirm it emits a launcher readiness packet
- open `CLOSE_Workspace.ipynb` in Colab
- run Block 1 successfully
- confirm it emits a close readiness packet

## Startup Workflow After Recovery

### Repo-backed project startup

1. Open Codex in the WSL repo.
2. Codex can remain idle until planning.
3. Open `AI_Workspace_Launcher.ipynb` in Colab.
4. Run Launcher Block 1.
5. Launcher reads:
   - Drive continuity state
   - `latest_interpreter_snapshot.json`
   - `latest_codex_published_state.v1.json`
6. Paste readiness packet to planning agent.
7. Planning agent returns `LAUNCH SUMMARY V1`.
8. Paste `LAUNCH SUMMARY V1` into Launcher Block 2.
9. Launcher emits `SESSION_CONTEXT_JSON`.
10. Planning happens before execution.

### Drive-native project startup

- same launcher flow
- Codex optional

Startup reads the last saved state by default.
Refresh only if artifacts are missing, stale, invalid, or explicitly requested.

### Codex startup convenience selector

```text
Choose a project action:
1. Continue an open project
2. Start a new project
3. Edit an existing project
4. Manage archived or delete a project
```

This is a Codex-side convenience selector only. It does not replace launcher/start-packet flow.

## Recovery Checklist

Recovery is complete only when all are true:

- Windows 11 is working
- Ubuntu in WSL is working
- repo exists at `~/dev/ai-lab`
- GitHub remote is connected
- VS Code opens repo in WSL mode
- Codex is installed and functioning
- `python3 scripts/dev/health_check.py` passes
- WSL can access `/mnt/g/My Drive`
- continuity files exist under `/mnt/g/My Drive/_ai`
- notebook files exist under `/mnt/g/My Drive/Colab Notebooks`
- `AI_Workspace_Launcher.ipynb` Block 1 runs successfully
- `CLOSE_Workspace.ipynb` Block 1 runs successfully

## What Is Recoverable Right Now

### Recoverable from GitHub

- code
- docs
- repo scripts
- schemas
- repo-native project state

### Recoverable from Drive

- continuity memory in `_ai`
- notebook files
- Drive-mirrored repo artifacts used by launcher/close flow

### Not automatically recoverable unless separately stored

- secrets
- local `.env` files
- arbitrary uncommitted local files
- anything not pushed to GitHub or present in Drive

## Environment and secrets notes

Secrets are not restored from the repo.

Use:

- `docs/SECRETS_INVENTORY.md` for documented secrets handling patterns
- local environment variables
- optional non-committed `.env` files when needed

Security hygiene:

- never store live tokens or PATs in this guide
- never commit secrets
- treat any pasted token in chat/docs as compromised and rotate it immediately

## Planned / Not Yet Implemented

### Full environment automation

This repo does not yet claim:

- one-command machine bootstrap
- automatic package installation across all tools
- automatic secret provisioning
- automatic restoration of cloud resources
- automatic restoration of paper/live execution infrastructure

## Bottom line

- repo continuity comes from GitHub
- workflow continuity comes from Drive `_ai` + Colab notebooks
- secrets come from separate restoration
- the laptop is replaceable only if both repo lane and continuity lane are restorable
