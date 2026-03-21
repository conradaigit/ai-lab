# CURRENT_CONTEXT

## Active project
trading_system

## Current focus
Phase 1.5 reliability hardening is complete. The immediate next step is opening the repo in VS Code from WSL and configuring Codex.

## Last completed work
- Defined the base memory object schema
- Added `docs/SECRETS_INVENTORY.md`
- Updated `AGENTS.md` with the single-writer workspace rule
- Added `scripts/dev/health_check.py`
- Updated `scripts/workspace/start_session.py` for receipt-aware startup guidance
- Updated `scripts/workspace/close_session.py` for receipt-aware close behavior
- Verified health check output
- Verified start-session behavior
- Verified close-session receipt behavior

## Next 1-3 actions
1. Review `git diff` and commit the Phase 1.5 reliability hardening changes
2. Open `~/dev/ai-lab` in VS Code from WSL using `code .`
3. Install/configure Codex and verify it follows `AGENTS.md`

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
`workspace/close_session_receipt.json` is a rolling runtime reliability file and should not be committed.
