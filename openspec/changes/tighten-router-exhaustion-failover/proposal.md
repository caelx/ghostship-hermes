## Why

The router's current health logic is too coarse for free-model exhaustion and transient provider throttling. A single model-level `429` can currently suppress an entire provider for a short cooldown, while the router lacks an explicit sequence-aware rule for recognizing broader provider exhaustion and escalating cooldowns across repeated failures.

## What Changes

- Tighten router failover so retryable exhaustion stays transparent within a request while still respecting the ranked candidate priority list.
- Replace the current one-size-fits-all failure cooldown behavior with an escalating per-model exhaustion cooldown ladder.
- Add explicit provider-wide exhaustion detection based on repeated zero-output exhaustion failures across distinct models on the same provider within a short window.
- Add longer provider disablement and probe-style recovery behavior so repeated provider-wide exhaustion does not cause thrashing.
- Distinguish provider-specific exhaustion semantics for OpenRouter free-model limits and OpenCode Zen balance or limit exhaustion.

## Capabilities

### New Capabilities

### Modified Capabilities

- `model-router-service`: Change failover, cooldown, and provider suppression requirements so exhaustion handling is sequence-aware, provider-aware, and transparent within the request path.

## Impact

- Affected code: `packages/hermes-router/src/hermes_router/{service,state,config}.py`, provider adapters, and router tests.
- Affected systems: local router request routing, provider health state, debug and metrics surfaces, and runtime behavior for OpenRouter and OpenCode Zen failover.
- External behavior: callers should continue to see one transparent request outcome while operators gain clearer exhaustion and provider-disable semantics.
