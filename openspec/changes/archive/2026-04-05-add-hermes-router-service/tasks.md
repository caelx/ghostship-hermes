## 1. Package scaffold and local service entrypoint

- [x] 1.1 Create `packages/hermes-router` with `pyproject.toml`, `package.nix`, lockfile, and `src/hermes_router/` module layout.
- [x] 1.2 Add `FastAPI` and `uvicorn` service bootstrap with a runnable entrypoint for local development.
- [x] 1.3 Wire the package into `flake.nix` and the repo Python environment so the router can be built and tested independently.

## 2. Minimal API contract and configuration

- [x] 2.1 Implement the initial localhost API surface for `GET /healthz`, `GET /readyz`, `GET /v1/models`, and `POST /v1/chat/completions`.
- [x] 2.2 Add request and response schemas that expose stable logical aliases `lightweight`, `coding`, and `heavyweight`.
- [x] 2.3 Implement configuration loading for provider settings, alias buckets, fallback policy, operator allow or block controls, and environment-based credentials including `OPENROUTER_API_KEY` and `OPENCODE_API_KEY`.

## 3. Provider adapters and free-first routing

- [x] 3.1 Define the provider adapter contract for model discovery, chat inference, and normalized error handling.
- [x] 3.2 Implement the first free-model provider adapter and the Gemini fallback adapter.
- [x] 3.3 Implement candidate selection, retryable-failure handling, transparent failover, and explicit fallback accounting.
- [x] 3.4 If model-assisted bucketing or ranking is added, route that maintenance work through a configured free model instead of Gemini.

## 4. Inventory, persistence, and observability

- [x] 4.1 Add a state-store interface and implement the SQLite-backed registry for inventory, health observations, cooldowns, and overrides.
- [x] 4.2 Implement startup refresh, scheduled background refresh, and forced refresh on stale-model failures outside the request hot path.
- [x] 4.3 Add structured logging plus health, readiness, and debug surfaces that explain backend choice, retry behavior, and fallback usage.

## 5. Verification, runtime integration, and rollout docs

- [x] 5.1 Add unit and integration coverage for alias discovery, routing decisions, retry behavior, fallback, refresh, restart-state restoration, and any free-model-assisted bucketing logic.
- [x] 5.2 Integrate the router package into the Hermes runtime and add service supervision only after the standalone package is verified.
- [x] 5.3 Document router configuration, local execution, API surface, `.envrc`-driven validation with `OPENROUTER_API_KEY` and `OPENCODE_API_KEY`, staged rollout, and operational debugging in repo docs and changelog entries.

## 6. Provider follow-up adjustments

- [x] 6.1 Remove Gemini fallback wiring from the router package, runtime integration, and docs.
- [x] 6.2 Add an OpenCode Zen provider adapter that refreshes Zen inventory and contributes Zen models to alias routing.
- [x] 6.3 Support Zen mixed endpoint families, including model-level endpoint-family caching and normalized chat-completions responses.
- [x] 6.4 Keep routing health, failover, and cooldown behavior explicitly model-level across providers and expose best-effort first-text latency in state/debug surfaces.
- [x] 6.5 Extend tests, docs, and live verification for the Zen provider and model-level latency tracking.
