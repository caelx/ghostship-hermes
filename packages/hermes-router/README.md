# ghostship-hermes-router

Local `FastAPI` model router for `ghostship-hermes`.

Current contract:

- exposes Hermes/OpenAI-compatible health, `chat/completions`, and `responses` endpoints
- exposes one logical alias at `GET /v1/models`: `agentic`
- persists inventory, route health, provider health, cooldowns, overrides, recent events, chat sessions, and stored `responses` objects in SQLite
- refreshes inventory from `nvidia-build`, `opencode-zen`, and `openrouter`
- discovers NVIDIA Build inventory live from the filtered `build.nvidia.com/models?filters=nimType%3Anim_type_preview` page, filters out deprecated free endpoints, deduplicates repeated model ids, and normalizes them into canonical `publisher/model` ids
- routes only explicitly ranked `agentic` models
- keeps a top-five reserve per provider and chooses the best three currently eligible models from that reserve
- never routes uncategorized discovered models; they are exposed only through debug inventory surfaces
- exposes operator debug surfaces at `GET /debug/state`, `GET /debug/events`, `GET /debug/providers`, `GET /debug/routes/{alias}`, `GET /debug/rankings/{alias}`, `GET /debug/inventory/{category}`, and `GET /debug/models/{provider}/{model}`
- exposes a compact tuning surface at `GET /debug/summary`
- exposes Prometheus-style metrics at `GET /metrics`
- supports optional internal bearer auth through `_GHOSTSHIP_ROUTER_API_KEY`

Provider policy:

- provider order is fixed: `nvidia-build -> opencode-zen -> openrouter`
- provider failover is exhaustion-gated; ordinary retryable model failures stay inside the active provider
- repeated exhaustion evidence can suppress a provider for a longer daily-limit style window
- chat sessions keep provider/model stickiness once a session lands on a healthy route

Seed ranked usable sets:

- `nvidia-build`
  - `minimaxai/minimax-m2.7`
  - `qwen/qwen3-coder-480b-a35b-instruct`
  - `moonshotai/kimi-k2-thinking`
  - `deepseek-ai/deepseek-v3.2`
  - `z-ai/glm-4.7`
- `opencode-zen`
  - `big-pickle`
  - `minimax-m2.5-free`
  - `trinity-large-preview-free`
  - `nemotron-3-super-free`
  - `gpt-5-nano`
- `openrouter`
  - `nvidia/nemotron-3-super-120b-a12b:free`
  - `minimax/minimax-m2.5:free`
  - `arcee-ai/trinity-large-preview:free`
  - `google/gemma-4-31b-it:free`
  - `qwen/qwen3-coder:free`

`google/gemma-4-31b-it:free` remains intentionally ranked even though the current `agentic` filter usually skips it because it advertises image/video input.

Compatibility notes:

- `chat/completions` streaming is true SSE and preserves provider-emitted usage, reasoning, and tool-call deltas
- `responses` supports Hermes/OpenAI SDK streaming and richer stored response objects
- Hermes may use either `http://127.0.0.1:8788/v1` or the bare root; both surfaces are exposed
- `NVIDIA_API_KEY` remains a compatibility alias for `NVIDIA_BUILD_API_KEY`
- `OPENCODE_GO_API_KEY` remains a compatibility alias for `OPENCODE_API_KEY`

## Environment

Required provider creds for full local validation:

- `OPENROUTER_API_KEY`
- `OPENCODE_API_KEY` or `OPENCODE_GO_API_KEY`
- `NVIDIA_BUILD_API_KEY`

Common router env:

- `GHOSTSHIP_ROUTER_HOST`
- `GHOSTSHIP_ROUTER_PORT`
- `GHOSTSHIP_ROUTER_CORS_ORIGINS`
- `GHOSTSHIP_ROUTER_STATE_DIR`
- `GHOSTSHIP_ROUTER_DB_PATH`
- `GHOSTSHIP_ROUTER_REFRESH_INTERVAL`
- `GHOSTSHIP_ROUTER_PROVIDER_COOLDOWN_SECONDS`
- `GHOSTSHIP_ROUTER_PROVIDER_FAILURE_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_RATE_LIMIT_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_TIMEOUT_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_EXHAUSTION_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_RESERVE_LIMIT`
- `GHOSTSHIP_ROUTER_PROVIDER_ACTIVE_CANDIDATE_LIMIT`
- `GHOSTSHIP_ROUTER_AGENTIC_MODELS`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_AGENTIC`
- `GHOSTSHIP_ROUTER_NVIDIA_BUILD_UNUSED_MODELS`
- `GHOSTSHIP_ROUTER_OPENCODE_ZEN_UNUSED_MODELS`
- `GHOSTSHIP_ROUTER_OPENROUTER_UNUSED_MODELS`

Hermes-compatible aliases:

- `API_SERVER_HOST`
- `API_SERVER_PORT`
- `API_SERVER_CORS_ORIGINS`

Standalone local runs default router state to `${XDG_STATE_HOME:-~/.local/state}/ghostship-hermes/router`. The workstation image overrides that to `/home/hermes/.local/state/ghostship-hermes/router`.

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
