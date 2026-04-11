## 1. Managed Runtime Contract

- [x] 1.1 Update the managed Hermes config scaffold so the image ships `opencode-go/minimax-m2.7` as primary and router alias `agentic` as fallback.
- [x] 1.2 Keep `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free` as the managed router default and verify router fallback auth still uses `OPENAI_API_KEY`.

## 2. Dashboard Runtime Validation Surface

- [x] 2.1 Extend dashboard status parsing to expose both primary and fallback agent config details from the managed Hermes config.
- [x] 2.2 Update the dashboard UI and fixtures so operators can see the managed primary/fallback contract and liveness markers directly.
- [x] 2.3 Add end-to-end browser validation for opening an on-demand ttyd terminal from the dashboard surface.

## 3. Health And Liveness

- [ ] 3.1 Verify the managed gateway pidfile fix is present in the shipped image and survives `hermes doctor` on the deployed host.
- [x] 3.2 Remove the avoidable cold-start healthcheck race so the first failing probe reflects a real dashboard outage.
- [ ] 3.3 Validate that the direct `opencode-go` path is healthy enough for the shipped primary model contract.

## 4. Publish And Live Proof

- [ ] 4.1 Publish the rebuilt image and inspect the published artifact to confirm it contains the intended model contract and dashboard/runtime changes.
- [ ] 4.2 Deploy on `chill-penguin-root2` and verify the live config, router env, dashboard config display, and terminal-open behavior.
- [ ] 4.3 Re-run live validation after `hermes doctor` to confirm `gateway.pid` remains present and health/reporting surfaces stay correct.

## 5. Docs And Memory

- [x] 5.1 Update `README.md`, `docs/runtime-env.md`, `AGENTS.md`, and `CHANGELOG.md` to match the final live-image contract and validation flow.
