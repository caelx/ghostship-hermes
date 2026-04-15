# ghostship-hermes-router

Local `FastAPI` model router for `ghostship-hermes`.

Current scope:

- exposes Hermes-style health endpoints at `GET /health` and `GET /v1/health`
- exposes stable logical aliases at `GET /v1/models`
- accepts `POST /v1/chat/completions` with OpenAI-style JSON responses and SSE streaming
- accepts Hermes-compatible `POST /v1/responses` with sync responses, streamed `responses.stream(...)`, and stored `GET /v1/responses/{id}` / `DELETE /v1/responses/{id}`
- persists inventory, route health, provider health, rankings, overrides, cooldowns, and recent events in SQLite
- persists stored `responses` objects and lightweight chat session continuity state in SQLite
- serves previously persisted inventory and rankings immediately on startup, then refreshes inventory and reruns ranking in the background
- triggers a forced inventory refresh when a backend model disappears
- exposes debug surfaces at `GET /debug/state`, `GET /debug/events`, `GET /debug/providers`, `GET /debug/routes/{alias}`, `GET /debug/rankings/{alias}`, and `GET /debug/models/{provider}/{model}`
- exposes Prometheus-style metrics at `GET /metrics`
- reads local credentials from environment
- refreshes inventory from OpenRouter, OpenCode Zen, and optional curated NVIDIA Build inventory
- enriches OpenCode Zen inventory with matched public OpenRouter metadata when normalized ids line up closely enough
- routes and fails over between concrete backend models instead of alias-level buckets
- keeps paid models in inventory and debug state, but only free models can become route candidates
- treats NVIDIA Build as a curated free-only provider with a repo-owned allowlist instead of broad catalog discovery
- if persisted inventory exists, startup reuses it immediately; otherwise the router stays unready until the first background discovery pass classifies free models into `auxiliary`, `coding`, `agentic`, `vision`, and `tts`
- dynamic bucketing prefers an OpenCode Zen free text worker when available and falls back to OpenRouter when Zen cannot supply a usable worker
- when provider metadata exposes capabilities, `coding`, `agentic`, and `auxiliary` candidates must support tool calling with text-only outputs, `vision` candidates must accept image or video input with text output, and `tts` candidates must expose speech-style audio output while excluding music-generation models such as Lyria
- coding, agentic, and auxiliary candidates all get alias-specific family orderings based on repo-maintained benchmark guidance, then receive relative rank bonuses only among families that are actually present; newer models get a strong recency lift after capability filtering; exact id/name family matches beat description-only matches; `coding`, `agentic`, and `vision` add only a modest global size-rank bonus and only penalize smaller variants when a larger sibling exists in the same family or inferred subfamily, while `auxiliary` intentionally prefers smaller helper models
- alias routing keeps only the top 3 scored models per provider for each bucket before cross-provider interleaving
- provider-priority policy is explicit and defaults to `nvidia-build` ahead of `opencode-zen` ahead of `openrouter` when remaining scores are otherwise comparable
- preferred-model pins may use `openrouter/`, `opencode/`, `nvidia/`, or `nvidia-build/` prefixes in config, but backend dispatch must normalize them back to the provider's real model id before routing
- supports OpenCode Zen mixed endpoint families and normalizes them back to local `chat/completions`
- records total latency and best-effort first-text latency per backend model
- returns `X-Hermes-Session-Id` on chat completions and can reuse that session id on later requests
- tracks rolling model and provider health so broad provider failures can temporarily suppress a provider without losing model-level failover
- uses a healthy free text model for background ranking and selective reranking outside the request hot path
- supports durable provider and model overrides plus alias pinning
- supports optional internal bearer auth through `_GHOSTSHIP_ROUTER_API_KEY`
- supports optional browser CORS allowlists through `GHOSTSHIP_ROUTER_CORS_ORIGINS` or `API_SERVER_CORS_ORIGINS`

The package is intentionally standalone first so it can be built and tested before Hermes image integration.

## Environment

Primary router validation inputs (not required for the current Hermes scaffold unless you are using the router):

- `OPENROUTER_API_KEY`
- `OPENCODE_API_KEY` or `OPENCODE_GO_API_KEY`
- `NVIDIA_BUILD_API_KEY`

Optional router-specific inputs:

- `GHOSTSHIP_ROUTER_HOST`
- `GHOSTSHIP_ROUTER_PORT`
- `GHOSTSHIP_ROUTER_CORS_ORIGINS`
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
- `GHOSTSHIP_ROUTER_NVIDIA_BUILD_MODELS`
- `GHOSTSHIP_ROUTER_NVIDIA_BUILD_MIN_REQUEST_SPACING_SECONDS`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_AUXILIARY`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_CODING`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_AGENTIC`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_VISION`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_TTS`
- `GHOSTSHIP_ROUTER_AUXILIARY_MODELS`
- `GHOSTSHIP_ROUTER_CODING_MODELS`
- `GHOSTSHIP_ROUTER_AGENTIC_MODELS`
- `GHOSTSHIP_ROUTER_VISION_MODELS`
- `GHOSTSHIP_ROUTER_TTS_MODELS`

Hermes-compatible aliases:

- `API_SERVER_HOST`
- `API_SERVER_PORT`
- `API_SERVER_CORS_ORIGINS`

Compatibility note:

- `chat/completions` streaming is true SSE
- `chat/completions` streaming now preserves usage chunks plus reasoning and tool-call deltas when the backend provider emits them
- `responses` now supports Hermes/OpenAI SDK streaming with `response.created`, `response.output_item.added`, `response.output_text.delta`, `response.function_call_arguments.delta`, and `response.completed`
- `responses` stores and returns richer response objects with message, reasoning, and function-call output items
- OpenCode Zen mixed endpoint families still normalize back to the local `chat/completions` surface before the router builds the `responses` envelope
- Hermes can use `base_url` `http://127.0.0.1:8788/v1` directly as a generic OpenAI-compatible endpoint
- Hermes also works with bare `http://127.0.0.1:8788`; the router exposes both `/v1/...` and bare OpenAI endpoint aliases
- The workstation image auto-generates `_GHOSTSHIP_ROUTER_API_KEY` at boot and shares it internally between Hermes and the local router
- The router also accepts `OPENCODE_GO_API_KEY` as an alias for `OPENCODE_API_KEY` so the Hermes Minimax fallback credential name can be shared without a second env var
- The router also accepts `NVIDIA_API_KEY` as a compatibility alias for `NVIDIA_BUILD_API_KEY`
- `GOOGLE_AI_STUDIO_API_KEY` remains Hermes-direct only for now; the router does not consume it until a native Google provider exists

Current curated NVIDIA Build inventory:

- `moonshotai/kimi-k2-instruct`
- `mistralai/mistral-nemotron`
- `deepseek-ai/deepseek-r1`

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
