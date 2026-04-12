## Why

The managed Hermes runtime contract is still pointed at the wrong fallback lane, and prior pushes did not reliably prove that the published image reflected the source contract. The intended model order is direct `opencode-go/minimax-m2.7` first, with the local router used only as fallback through the stronger `agentic` alias rather than the current `coding` alias. The rollout also still needs to prove that the managed gateway pidfile survives `hermes doctor`, because the live image has been deleting `/home/hermes/.hermes/gateway.pid` even while the gateway service stays up.

## What Changes

- Switch the managed single-agent Hermes scaffold to keep `opencode-go/minimax-m2.7` as the primary model path and change the configured router fallback alias from `coding` to `agentic`.
- Keep the router fallback on the local OpenAI-compatible endpoint at `http://127.0.0.1:8788/v1` with `OPENAI_API_KEY` as the bearer-token input.
- Set `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free` by default for the managed router service so that exact backend id is excluded from selection.
- Extend validation so the published image and deployed host are checked for the intended config contract instead of assuming a source-only change reached GHCR.
- Verify the deployed image preserves `/home/hermes/.hermes/gateway.pid` after `hermes doctor` so the already-landed pidfile fix is proven live.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `router-primary-hermes-runtime`: Change the managed runtime contract from router-primary `coding` to direct MiniMax primary with router `agentic` fallback, and extend validation to assert the new fallback contract plus the default blocked backend id.
- `hermes-runtime-state-markers`: Require live validation to prove the managed gateway pidfile remains present after `hermes doctor` on the published image.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, Hermes dashboard test fixtures, image smoke validation, and runtime/operator docs.
- Affected systems: managed Hermes model configuration, managed router default env, published-image validation, and live gateway pidfile verification for the single-agent runtime.
- Operational impact: aligns the source contract with the intended primary/fallback order and requires publish-plus-live proof before treating the rollout as complete.
