## 1. Managed Runtime Contract

- [ ] 1.1 Update the managed Hermes config scaffold so `opencode-go/minimax-m2.7` remains the primary model path and the configured router fallback alias changes from `coding` to `agentic`.
- [ ] 1.2 Keep `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free` as the managed router default and ensure the runtime wiring still uses `OPENAI_API_KEY` for router fallback auth.

## 2. Validation And Docs

- [ ] 2.1 Update the dashboard fixture and image smoke validation to assert direct MiniMax primary, router `agentic` fallback, and the default blocked backend id.
- [ ] 2.2 Update `README.md`, `AGENTS.md`, `docs/runtime-env.md`, and `CHANGELOG.md` so the documented runtime contract matches the new primary/fallback order.

## 3. Publish And Live Proof

- [ ] 3.1 Publish the rebuilt image and inspect the published artifact to confirm it contains the intended managed model config and router disabled-model default.
- [ ] 3.2 Deploy on `chill-penguin-root2` and verify `/home/hermes/.hermes/config.yaml` shows direct MiniMax primary with router `agentic` fallback.
- [ ] 3.3 Run `hermes doctor` on the deployed host and verify `/home/hermes/.hermes/gateway.pid` remains present afterward.
- [ ] 3.4 Re-run live validation to confirm the managed router environment disables `openrouter/free` and the direct `opencode-go` path is healthy enough for the new primary lane.
