## Why

The router now has the core service shape, persistence, mixed OpenCode Zen support, and model-level failover, but its ranking and observability are still thin. It mostly scores candidates with name heuristics and a few last-seen counters, which is not strong enough for unattended free-first routing across unstable model inventories.

## What Changes

- Add richer model- and provider-level health state so routing can reason about rolling latency, recent failures, rate-limit bursts, cooldowns, and likely quota exhaustion instead of relying mostly on static heuristics.
- Add a background ranking workflow that uses a currently healthy free model from the `lightweight` pool to classify and rerank candidates outside the request hot path.
- Add provider-wide disablement and recovery behavior in addition to the existing concrete-model cooldown logic.
- Add durable operator override state for force-enable, force-disable, force-weight, and alias pinning without requiring code edits.
- Add a stable metrics surface plus richer debug views for candidate ranking, provider health, and latency over time.
- Keep the Hermes-facing API stable while making model sorting and failover decisions more observable and tunable.

## Capabilities

### New Capabilities

### Modified Capabilities
- `model-router-service`: Extend router requirements to cover lightweight-model-assisted ranking, provider-wide health state, durable overrides, and a metrics surface for model sorting and failover behavior.

## Impact

- Affected code:
  - `packages/hermes-router/` routing engine, state store, background jobs, provider health tracking, and observability surfaces
  - `packages/hermes-image/` runtime env wiring for any new router config
  - repo docs and changelog entries for router ranking, metrics, and operations
- Affected APIs:
  - `model-router-service` debug and metrics surfaces
  - internal background ranking behavior and persisted router state
- Dependencies:
  - existing OpenRouter and OpenCode Zen credentials
  - SQLite schema changes for rolling stats, provider state, and overrides
