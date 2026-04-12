## Why

The live `ghostship-hermes` image still has contract gaps after publish. Source changes have not always been proven in the published image, the dashboard does not fully expose the managed agent model contract, the terminal flow is not validated at the browser level, the managed gateway pidfile can disappear after `hermes doctor`, and the default model/runtime contract on the live host has drifted from what the repo intends to ship.

This proposal needs to cover the full failure set instead of one symptom at a time.

## What Changes

- Fix the managed runtime contract so the shipped image uses direct `opencode-go/minimax-m2.7` as primary and the local router `agentic` alias as fallback.
- Keep `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free` as the default blocked backend id in the managed router environment.
- Extend dashboard status/UI so it surfaces the managed agent configuration that operators actually need to validate, including primary model, fallback model, endpoint details, and liveness markers.
- Add end-to-end dashboard validation for opening an on-demand ttyd terminal from the browser surface, not only via raw API calls.
- Require the published image and deployed host to be inspected directly so pushed source changes are proven live.
- Verify the managed gateway pidfile survives `hermes doctor` and remains the authoritative liveness marker for dashboard and Hermes health surfaces.
- Tighten cold-start and provider-path validation so a healthy published image does not advertise a broken primary lane or fail boot probes because of avoidable runtime-path races.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `router-primary-hermes-runtime`: Replace the old router-primary contract with the intended direct MiniMax primary plus router `agentic` fallback contract, and validate the published image/live host state.
- `hermes-runtime-state-markers`: Prove the managed gateway pidfile remains present for the running gateway even after `hermes doctor`.
- `agent-workstation-updates`: Make the dashboard/operator-facing runtime view show the real managed agent config and support end-to-end terminal validation.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, `packages/hermes-dashboard/src/hermes_dashboard/app.py`, `packages/hermes-dashboard/src/hermes_dashboard/static/app.js`, dashboard tests, image smoke/live validation, and runtime docs.
- Affected systems: managed Hermes model configuration, managed router env defaults, dashboard status and terminal UX, managed gateway liveness reporting, publication validation, and deploy-time checks on `chill-penguin-root2`.
- Operational impact: one proposal covers the full live-image readiness gap instead of shipping partial fixes that are not proven in GHCR or on the deployed host.
