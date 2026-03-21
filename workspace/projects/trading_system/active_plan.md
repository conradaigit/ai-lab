# trading_system active plan

## Objective
Stand up the local-first architecture so a coding agent can operate reliably with explicit repo memory, verification, lightweight reliability hardening, and minimal operator friction.

## Current scope
- keep the core operating docs aligned
- verify and normalize the WSL-backed VS Code + Codex workflow
- preserve rebuildability and reliability

## Success criteria
- Phase 1 local-first foundation is complete and reflected in workspace memory
- `schemas/memory_object_base.json` exists
- `docs/SECRETS_INVENTORY.md` exists
- `AGENTS.md` reflects the single-writer rule
- `scripts/dev/health_check.py` exists and runs
- `start_session.py` warns on incomplete prior close if needed
- `close_session.py` records receipt progress
- repo state remains coherent and machine-readable
- VS Code opens `~/dev/ai-lab` from WSL
- Codex can operate inside `~/dev/ai-lab`
- current-state workspace files reflect the completed Phase 1.5 work and current workflow focus

## Ordered next steps
1. verify the repo opens from WSL with `code .`
2. verify and normalize Codex startup behavior against `AGENTS.md`
3. record any workflow adjustments back into workspace memory

## Current step
Step 1-3: verify and normalize WSL-backed VS Code + Codex
