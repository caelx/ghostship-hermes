## Why

The live image still carries stale repo-owned managed config from the earlier router-primary contract, so Hermes sends the supposed primary `opencode-go/minimax-m2.7` lane to the local router and only succeeds after fallback. The gateway side has the same kind of contract drift: the image runs a repo-owned system unit that happens to run as `hermes`, while upstream Hermes expects a real `systemd --user` `hermes-gateway.service` in the Hermes user manager.

## What Changes

- Reconcile persisted repo-owned managed Hermes config on boot so retired keys from older image contracts do not survive across replacement.
- Remove the stale root-managed `model.base_url` when the managed primary model contract is direct `opencode-go` instead of router-primary.
- Replace the repo-owned system gateway unit with an upstream-aligned Hermes user service: `systemd --user` `hermes-gateway.service` owned by `hermes`.
- Remove or minimize the Ghostship-specific gateway CLI shim so `hermes gateway status/start/stop/restart` follow upstream user-service behavior again.
- Extend validation so maintainers prove the direct primary lane works without hidden fallback rescue and confirm Hermes gateway state surfaces match the live upstream-style user service.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `router-primary-hermes-runtime`: change the managed runtime contract from router-primary to direct `opencode-go/minimax-m2.7` primary with router `agentic` fallback, and require validation that stale router-primary config does not survive.
- `agent-workstation-runtime`: require managed convergence to clean up retired repo-owned config keys and change the managed gateway service contract from a repo-owned system unit to the upstream-style Hermes user service with truthful status/control behavior.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, `packages/hermes-agent-wrapped/package.nix`, Hermes validation scripts, and live validation helpers.
- Affected systems: managed `/home/hermes/.hermes/config.yaml` convergence, Hermes interactive runtime resolution, Hermes user-manager boot wiring, and operator-facing gateway health/status output.
- Affected rollout path: image replacement with persisted `/home/hermes` must migrate stale managed config safely, provision the Hermes user service correctly, and be revalidated on the live host.
