# ghostship-hermes-router

Local `FastAPI` model router for `ghostship-hermes`.

Current scope:

- exposes stable logical aliases at `GET /v1/models`
- accepts `POST /v1/chat/completions`
- persists inventory, route health, cooldowns, and recent events in SQLite
- refreshes inventory on startup and on a background interval
- triggers a forced inventory refresh when a backend model disappears
- exposes debug surfaces at `GET /debug/state`, `GET /debug/events`, and `GET /debug/routes/{alias}`
- reads local credentials from environment
- refreshes inventory from OpenRouter and OpenCode Zen
- routes and fails over between concrete backend models instead of alias-level buckets
- supports OpenCode Zen mixed endpoint families and normalizes them back to local `chat/completions`
- records total latency and best-effort first-text latency per backend model
- can use a configured free model for background bucket classification when `GHOSTSHIP_ROUTER_ASSISTED_BUCKET_MODEL` is set

The package is intentionally standalone first so it can be built and tested before Hermes image integration.

## Environment

Primary local validation inputs:

- `OPENROUTER_API_KEY`
- `OPENCODE_API_KEY`

Optional router-specific inputs:

- `GHOSTSHIP_ROUTER_HOST`
- `GHOSTSHIP_ROUTER_PORT`
- `GHOSTSHIP_ROUTER_API_KEY`
- `GHOSTSHIP_ROUTER_CORS_ORIGINS`
- `GHOSTSHIP_ROUTER_STATE_DIR`
- `GHOSTSHIP_ROUTER_DB_PATH`
- `GHOSTSHIP_ROUTER_REFRESH_INTERVAL`
- `GHOSTSHIP_ROUTER_ASSISTED_BUCKET_MODEL`
- `GHOSTSHIP_ROUTER_LIGHTWEIGHT_MODELS`
- `GHOSTSHIP_ROUTER_CODING_MODELS`
- `GHOSTSHIP_ROUTER_HEAVYWEIGHT_MODELS`

Hermes API-server-compatible aliases are also accepted:

- `API_SERVER_HOST`
- `API_SERVER_PORT`
- `API_SERVER_KEY`
- `API_SERVER_CORS_ORIGINS`

Standalone local runs default router state to `${XDG_STATE_HOME:-~/.local/state}/ghostship-hermes/router`. The Hermes image overrides that to `/home/hermes/.local/state/ghostship-hermes/router`.

In the Hermes image, the router is managed by `ghostship-hermes-router.service` and listens on `127.0.0.1:8788` by default.

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
