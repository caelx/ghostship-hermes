## Why

The repo has a written router concept but no surviving implementation, so Hermes still depends on direct upstream provider configuration instead of a stable local routing layer. Reintroducing the router as a small `FastAPI` service now gives the repo a concrete path toward free-first model selection, controlled failover, and a localhost API that other Hermes components can adopt incrementally.

## What Changes

- Add a new Python service package at `packages/hermes-router` built with `FastAPI` and served with `uvicorn`.
- Define a stable localhost API for logical model aliases, chat/completions-style inference, and router health/readiness inspection.
- Implement the router in staged phases so a minimal usable service lands first, with later phases adding background refresh, persistent routing state, and richer failover behavior.
- Add provider adapter boundaries so free-model backends, optional free-model-assisted bucketing/ranking, and Gemini fallback can evolve without rewriting the API layer.
- Use environment-loaded provider credentials for local validation so the router can be exercised against the repo's existing `.envrc`-managed OpenRouter and Opencode access without committing secrets into the package.
- Plan for eventual runtime wiring into the Hermes image and workstation services after the standalone package shape is verified.

## Capabilities

### New Capabilities
- `model-router-service`: A shared local router service that exposes stable logical model aliases and routes requests across free-model pools with explicit Gemini fallback.

### Modified Capabilities

## Impact

- Affected code:
  - `packages/hermes-router/` new Python package, tests, and packaging metadata
  - `flake.nix` package wiring and any related Python/runtime composition
  - `packages/hermes-image/` service integration in a later stage
  - repo docs for router API, configuration, and staged rollout
- Affected APIs:
  - new localhost router API with model-list, inference, and health/readiness endpoints
- Dependencies:
  - `fastapi`
  - `uvicorn`
  - provider-facing HTTP client support
  - local persistent storage for later phases
