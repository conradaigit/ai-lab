# CURRENT_CONTEXT

## Active project
trading_system

## Current focus
Select required Polygon paid tier for archive depth and index/futures coverage

## Last completed work
- Validated POLYGON_API_KEY visibility and authenticated Polygon request without exposing key
- Ran cross-asset coverage probe for stocks grouped-daily short-data indices forex crypto and futures
- Ran history-depth probe across representative windows and resolved 429 ambiguity with paced retries
- Confirmed entitlement blocks on deeper history plus index/futures access and produced paid-vs-current recommendations

## Next 1-3 actions
1. Select required Polygon paid tier for archive depth and index/futures coverage
2. Finalize canonical asset universe and historical windows for backtesting ingestion
3. Implement rate-limit-aware downloader manifests and checks for incremental backfill

## Important files to review first
- `AGENTS.md`
- `docs/SYSTEM_OPERATING_MANUAL.md`
- `workspace/projects/trading_system/state.json`
- `workspace/projects/trading_system/tasks.json`
- `workspace/projects/trading_system/constraints.md`
- `workspace/projects/trading_system/ops.md`
- `workspace/projects/trading_system/active_plan.md`
- `workspace/projects/trading_system/progress.md`
- `workspace/projects/trading_system/failure_registry.md`

## Notes
Updated by `scripts/workspace/close_session.py`.
