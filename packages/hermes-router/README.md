# ghostship-hermes-router

Local `FastAPI` model router for `ghostship-hermes`.

Current contract:

- exposes Hermes/OpenAI-compatible health, `chat/completions`, and `responses` endpoints
- uses OpenCode Go as the canonical served-model catalog
- exposes only OpenCode Go model ids with dynamically discovered free-provider equivalents
- routes discovered free equivalents first with shape- and size-aware health plus bounded free-provider deadlines, then falls back to `opencode-go/<same model id>`
- reports `free_provider_count`, free provider names, availability, and RPM state in `/v1/models` metadata
- persists inventory, route health, provider health, shape-and-size-specific health, cooldowns, overrides, recent events, chat sessions, and stored `responses` objects in SQLite
- refreshes inventory from configured free providers (`nvidia-build`, `opencode-zen`, `zenmux`, `electron-hub`, and `openrouter`) plus paid fallback provider `opencode-go`
- never exposes OpenCode Go models without at least one discovered free equivalent
- exposes operator debug surfaces at `GET /debug/state`, `GET /debug/events`, `GET /debug/route-events`, `GET /debug/health`, `GET /debug/providers`, `GET /debug/routes/{model}?shape_key=...&size_bucket=...`, `GET /debug/rankings/{model}`, `GET /debug/inventory/{seeded|configured|unconfigured|inventory}`, and `GET /debug/models/{provider}/{model}`
- exposes a compact tuning surface at `GET /debug/summary`
- exposes Prometheus-style metrics at `GET /metrics`
- supports optional internal bearer auth through `_GHOSTSHIP_ROUTER_API_KEY`

Provider policy:

- `opencode-go` is the paid fallback and is never counted as a free provider
- `opencode-zen` is a free-provider candidate only when its live catalog has a matching free model for the requested OpenCode Go model id
- NVIDIA Build is a free-provider candidate through live catalog discovery
- ZenMux is a free-provider candidate through live catalog discovery and defaults to 10 RPM
- Electron Hub is a free-provider candidate through live catalog discovery and defaults to 5 RPM
- OpenRouter is a free-provider candidate only for live catalog models marked free
- OpenRouter defaults to 20 RPM when configured, assuming the account has a maintained balance
- NVIDIA Build and OpenCode Zen default to 30 RPM
- free providers are selected by RPM-weighted deficit round robin with per-shape health scoring; `opencode-go` is used only after eligible free equivalents are exhausted, rate-limited, unavailable, failed, suppressed, or the request's free-provider budget is spent
- request health is keyed by provider, backend model, shape, and message-count size bucket (`small`, `medium`, or `large`), so large Hermes tool-history failures do not poison plain text traffic
- for large `stream+tools+tool_history+reasoning` requests, the configured primary served model defaults to a 25 second OpenCode Go attempt and the configured fallback served model defaults to a 75 second OpenCode Go attempt

Default Hermes models:

- Hermes config is pinned to `deepseek-v4-pro` with `minimax-m2.7` fallback.
- The router can expose any OpenCode Go catalog model whose normalized id matches at least one discovered free-provider model.
- Free-provider model ids are not hardcoded in the router defaults.

Compatibility notes:

- `chat/completions` streaming is true SSE and preserves provider-emitted usage, reasoning, and tool-call deltas
- `responses` supports Hermes/OpenAI SDK streaming and richer stored response objects
- Hermes may use either `http://127.0.0.1:8788/v1` or the bare root; both surfaces are exposed
- `NVIDIA_API_KEY` remains a compatibility alias for `NVIDIA_BUILD_API_KEY`
- `OPENCODE_API_KEY` remains a compatibility alias for `OPENCODE_ZEN_API_KEY`; use `OPENCODE_GO_API_KEY` for the paid fallback provider

## Environment

Required provider creds for full local validation:

- `OPENCODE_GO_API_KEY`
- `OPENCODE_ZEN_API_KEY` or legacy `OPENCODE_API_KEY`
- `NVIDIA_BUILD_API_KEY`
- `ZENMUX_API_KEY`
- `ELECTRON_HUB_API_KEY`

Optional mapped provider creds:

- `OPENROUTER_API_KEY`

Common router env:

- `GHOSTSHIP_ROUTER_HOST`
- `GHOSTSHIP_ROUTER_PORT`
- `GHOSTSHIP_ROUTER_CORS_ORIGINS`
- `GHOSTSHIP_ROUTER_STATE_DIR`
- `GHOSTSHIP_ROUTER_DB_PATH`
- `GHOSTSHIP_ROUTER_REFRESH_INTERVAL`
- `GHOSTSHIP_ROUTER_PROVIDER_RPM_NVIDIA_BUILD`
- `GHOSTSHIP_ROUTER_PROVIDER_RPM_OPENCODE_ZEN`
- `GHOSTSHIP_ROUTER_PROVIDER_RPM_ZENMUX`
- `GHOSTSHIP_ROUTER_PROVIDER_RPM_ELECTRON_HUB`
- `GHOSTSHIP_ROUTER_PROVIDER_RPM_OPENROUTER`
- `GHOSTSHIP_ROUTER_PROVIDER_COOLDOWN_SECONDS`
- `GHOSTSHIP_ROUTER_PROVIDER_FAILURE_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_RATE_LIMIT_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_TIMEOUT_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_EXHAUSTION_THRESHOLD`
- `GHOSTSHIP_ROUTER_FREE_ATTEMPT_TIMEOUT_SECONDS`
- `GHOSTSHIP_ROUTER_FREE_STREAM_FIRST_BYTE_TIMEOUT_SECONDS`
- `GHOSTSHIP_ROUTER_FREE_TOTAL_BUDGET_SECONDS`
- `GHOSTSHIP_ROUTER_FALLBACK_TIMEOUT_SECONDS`
- `GHOSTSHIP_ROUTER_PRIMARY_SERVED_MODEL`
- `GHOSTSHIP_ROUTER_FALLBACK_SERVED_MODEL`
- `GHOSTSHIP_ROUTER_OPENCODE_GO_LARGE_TOOL_HISTORY_PRIMARY_TIMEOUT_SECONDS`
- `GHOSTSHIP_ROUTER_OPENCODE_GO_LARGE_TOOL_HISTORY_FALLBACK_TIMEOUT_SECONDS`
- `GHOSTSHIP_ROUTER_TRACE_ROUTING`
