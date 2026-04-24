# trading_system active plan

## Objective
Define the backtesting data-access baseline on the current Polygon/Massive account and map which planned datasets require paid upgrades before full archive ingestion begins.

## Current scope
- validate authenticated access using safe key handling
- probe representative asset classes and endpoint families for entitlement coverage
- measure practical historical depth reachable on the current plan using low-cost sample requests
- convert probe outcomes into concrete paid-vs-current planning decisions for archive build-out

## Success criteria
- env var visibility and authenticated request are verified without exposing secrets
- access coverage is validated for stocks, grouped daily, short data, indices, forex, crypto, and futures representative probes
- historical depth limits are sampled across recent, ~5y, ~10y, and ~20y windows where applicable
- entitlement-blocked datasets are explicitly identified with 403 evidence
- a concrete next-step plan exists for paid tier selection and archive ingestion design

## Ordered next steps
1. choose the Polygon/Massive paid tier needed for target history depth and index/futures coverage
2. finalize canonical asset universe plus required lookback windows for the backtesting archive
3. implement a rate-limit-aware, manifest-driven ingestion/backfill workflow with verification checks

## Current step
Step 1: lock paid-tier decision from the validated entitlement matrix
