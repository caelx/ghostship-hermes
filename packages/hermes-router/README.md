# ghostship-hermes-router

Local `FastAPI` model router for `ghostship-hermes`.

Current scope:

- exposes stable logical aliases at `GET /v1/models`
- accepts `POST /v1/chat/completions`
- persists inventory, route health, provider health, rankings, overrides, cooldowns, and recent events in SQLite
- refreshes inventory on startup and on a background interval
- triggers a forced inventory refresh when a backend model disappears
- exposes debug surfaces at `GET /debug/state`, `GET /debug/events`, `GET /debug/providers`, `GET /debug/routes/{alias}`, `GET /debug/rankings/{alias}`, and `GET /debug/models/{provider}/{model}`
- exposes Prometheus-style metrics at `GET /metrics`
- reads local credentials from environment
- refreshes inventory from OpenRouter and OpenCode Zen
- routes and fails over between concrete backend models instead of alias-level buckets
- supports OpenCode Zen mixed endpoint families and normalizes them back to local `chat/completions`
- records total latency and best-effort first-text latency per backend model
- tracks rolling model and provider health so broad provider failures can temporarily suppress a provider without losing model-level failover
- uses a healthy free model from the `lightweight` pool for background ranking and selective reranking outside the request hot path
- supports durable provider and model overrides plus alias pinning

The package is intentionally standalone first so it can be built and tested before Hermes image integration.

## Environment

Primary local validation inputs:

- `OPENROUTER_API_KEY`
- `OPENCODE_API_KEY`

Optional router-specific inputs:

- `GHOSTSHIP_ROUTER_HOST`
- `GHOSTSHIP_ROUTER_PORT`
- `GHOSTSHIP_ROUTER_STATE_DIR`
- `GHOSTSHIP_ROUTER_DB_PATH`
- `GHOSTSHIP_ROUTER_REFRESH_INTERVAL`
- `GHOSTSHIP_ROUTER_RANKING_ENABLED`
- `GHOSTSHIP_ROUTER_RANKING_INTERVAL`
- `GHOSTSHIP_ROUTER_RANKING_WORKER_MODEL`
- `GHOSTSHIP_ROUTER_RANKING_SHORTLIST_SIZE`
- `GHOSTSHIP_ROUTER_ROLLING_WINDOW_SECONDS`
- `GHOSTSHIP_ROUTER_PROVIDER_COOLDOWN_SECONDS`
- `GHOSTSHIP_ROUTER_PROVIDER_FAILURE_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_RATE_LIMIT_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_TIMEOUT_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_EXHAUSTION_THRESHOLD`
- `GHOSTSHIP_ROUTER_ASSISTED_BUCKET_MODEL`
- `GHOSTSHIP_ROUTER_ASSISTED_BUCKET_BATCH_SIZE`
- `GHOSTSHIP_ROUTER_DISABLED_PROVIDERS`
- `GHOSTSHIP_ROUTER_DISABLED_MODELS`
- `GHOSTSHIP_ROUTER_PROVIDER_WEIGHT_OVERRIDES`
- `GHOSTSHIP_ROUTER_MODEL_WEIGHT_OVERRIDES`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_LIGHTWEIGHT`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_CODING`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_HEAVYWEIGHT`
- `GHOSTSHIP_ROUTER_LIGHTWEIGHT_MODELS`
- `GHOSTSHIP_ROUTER_CODING_MODELS`
- `GHOSTSHIP_ROUTER_HEAVYWEIGHT_MODELS`

Standalone local runs default router state to `${XDG_STATE_HOME:-~/.local/state}/ghostship-hermes/router`. The Hermes image overrides that to `/home/hermes/.local/state/ghostship-hermes/router`.

## Local Development

```fish
cd packages/hermes-router
uv sync --extra dev
.venv/bin/python -m pytest -q
.venv/bin/python -m hermes_router.app
```

Build through the repo flake:

```fish
nix build .#ghostship-hermes-router
```
