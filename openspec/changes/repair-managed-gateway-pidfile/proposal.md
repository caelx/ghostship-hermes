## Why

The live `ghostship-hermes` image on `chill-penguin-root2` is now healthy in most respects, but the managed gateway still fails one core runtime contract: `ghostship-hermes-gateway.service` can be running while `/home/hermes/.hermes/gateway.pid` is missing. That leaves the dashboard status payload and Hermes health/reporting surfaces with a false negative for the only remaining broken live-image invariant.

## What Changes

- Repair the single-agent managed gateway pidfile lifecycle so the running gateway always publishes `/home/hermes/.hermes/gateway.pid` and stale pidfiles are removed on stop or replacement.
- Align operator-facing managed status surfaces with that pidfile contract so the dashboard and Hermes health reporting agree with the live systemd service state.
- Add validation coverage for gateway pidfile presence during boot, restart, and post-deploy live checks.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `hermes-runtime-state-markers`: Tighten the single-agent managed gateway pidfile lifecycle so the root managed Hermes home always exposes the live gateway marker while the service is active.
- `agent-workstation-updates`: Tighten managed health/status reporting and validation so the healthy single-agent gateway does not present a false negative when the service is running.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, the managed gateway start/stop helper scripts, dashboard/runtime validation, and any live-image validation scripts that check gateway readiness.
- Affected systems: single-agent managed gateway supervision, dashboard status reporting, Hermes doctor/status surfaces, and live deploy validation.
- Operational impact: removes the last misleading runtime-health signal from the current live image and makes post-deploy validation deterministic.
