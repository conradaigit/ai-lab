# CURRENT_CONTEXT

## Active project
trading_system

## Current focus
Phase 1 local-first foundation and Phase 1.5 reliability hardening are complete. The immediate current focus is to verify and normalize the local VS Code + Codex workflow from WSL.

## Last completed work
- Completed Phase 1 local-first foundation
- Defined the base memory object schema
- Added `docs/SECRETS_INVENTORY.md`
- Updated `AGENTS.md` with the single-writer workspace rule
- Added `scripts/dev/health_check.py`
- Updated `scripts/workspace/start_session.py` for receipt-aware startup guidance
- Updated `scripts/workspace/close_session.py` for receipt-aware close behavior
- Verified health check output
- Verified start-session behavior
- Verified close-session receipt behavior
- Committed the Phase 1.5 reliability hardening changes

## Next 1-3 actions
1. Verify `code .` opens `~/dev/ai-lab` correctly from WSL
2. Verify and normalize Codex startup behavior against `AGENTS.md`
3. Record any workflow adjustments back into workspace memory

## Important files to review first
- `AGENTS.md`
- `docs/SYSTEM_OPERATING_MANUAL.md`
- `docs/SECRETS_INVENTORY.md`
- `schemas/memory_object_base.json`
- `workspace/projects/trading_system/state.json`
- `workspace/projects/trading_system/tasks.json`
- `workspace/projects/trading_system/active_plan.md`
- `workspace/projects/trading_system/progress.md`

## Notes
- `git status --short` was clean before this refresh
`workspace/close_session_receipt.json` is a rolling runtime reliability file and should not be committed.
