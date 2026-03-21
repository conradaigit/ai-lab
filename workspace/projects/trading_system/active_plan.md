# trading_system active plan

## Objective
Stand up the local-first architecture so a coding agent can operate reliably with explicit repo memory, verification, lightweight reliability hardening, and minimal operator friction.

## Current scope
- keep the core operating docs aligned
- complete the Phase 1.5 reliability hardening layer
- commit the reliability hardening changes cleanly
- move into VS Code + Codex from WSL
- preserve rebuildability and reliability

## Success criteria
- `schemas/memory_object_base.json` exists
- `docs/SECRETS_INVENTORY.md` exists
- `AGENTS.md` reflects the single-writer rule
- `scripts/dev/health_check.py` exists and runs
- `start_session.py` warns on incomplete prior close if needed
- `close_session.py` records receipt progress
- repo state remains coherent and machine-readable
- VS Code opens `~/dev/ai-lab` from WSL
- Codex can operate inside `~/dev/ai-lab`

## Ordered next steps
1. review the Phase 1.5 changes
2. commit the Phase 1.5 reliability hardening work
3. open the repo from WSL with `code .`
4. install/configure Codex
5. verify Codex reads the startup files and follows `AGENTS.md`

## Current step
Step 7–9: verification, commit, then VS Code + Codex
