## Why

Hermes in this container currently depends on direct upstream provider configuration and has no shared local routing layer for free-first model selection. Adding a long-lived router service now creates a stable local endpoint that can manage volatile free-model inventories, health, and failover without requiring Hermes or operator workflows to track those details directly.

## What Changes

- Add a new shared model-router service to the workstation runtime as a long-lived `hermes` user `systemd` unit.
- Expose a stable local chat/completions-style API with logical aliases such as `lightweight`, `coding`, and `heavyweight`.
- Implement background model discovery, classification, health tracking, routing, retry, cooldown, and Gemini fallback inside the router.
- Persist router inventory, routing state, health observations, overrides, and metrics-oriented state across restarts in the existing persisted workstation home/state layout.
- Add router-specific configuration, health/readiness surfaces, structured logging, and a background refresh timer so the service can run unattended in the container.

## Capabilities

### New Capabilities
- `model-router-service`: A shared long-lived local model router that exposes stable logical aliases, manages free-model pools, and falls back to Gemini when free backends are unavailable.

### Modified Capabilities

## Impact

- Affected code:
  - `packages/hermes-image/` runtime, workstation seed, and service/timer wiring
  - New router implementation code and packaging under the repo's Python/runtime structure
  - Documentation for the new shared router service
- Affected systems:
  - Persisted `hermes` user `systemd` manager
  - Shared workstation state and logs under `/opt/data/home` / XDG state paths
  - Upstream model-provider APIs used for discovery and inference
- Dependencies:
  - Python web/service stack for the router
  - Local persistent storage, likely SQLite
  - Existing provider credentials supplied through runtime env/config
