## Why

The managed Hermes image currently restarts `hermes-gateway.service` when `/home/hermes/.hermes/auth.json` or `/home/hermes/.hermes/SOUL.md` changes. That makes normal OAuth token refreshes and prompt edits unnecessarily disruptive, and it drifts from the repo's tighter `.env`-centric restart contract.

## What Changes

- Narrow the managed gateway restart path so it reacts only to runtime inputs that should actually reload the gateway, rather than restarting on `auth.json` or `SOUL.md` churn.
- Make the restart surface explicit in the single-agent runtime contract, including which files are restart-triggering and which managed state files are intentionally non-restarting.
- Add validation that proves OAuth/auth updates and `SOUL.md` edits do not bounce the managed gateway, while `.env` and managed config changes still do.
- Align operator-facing docs and change history with the narrowed restart surface so the published image contract and the documented contract match.
- Tighten image stability coverage around managed bootstrap idempotence and safe mutable state so routine runtime mutations do not cause avoidable service flaps.

## Capabilities

### New Capabilities
- `managed-gateway-restart-surface`: Defines the exact file-level restart triggers for the managed single-agent gateway and explicitly excludes non-restart state such as `auth.json` and `SOUL.md`.

### Modified Capabilities
- `hermes-profile-env-contract`: Clarify that the managed `.env` remains the operator-facing restart surface for runtime env and that idempotent `.env` rewrites are part of restart stability.
- `agent-workstation-updates`: Require validation coverage that proves safe managed-state edits do not trigger avoidable gateway restarts while supported restart-triggering edits still work.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, image validation scripts, and operator-facing docs such as `README.md` and `CHANGELOG.md`.
- Affected systems: managed `systemd --user` gateway restart wiring, managed bootstrap/runtime state convergence, and single-agent image validation.
- Affected runtime behavior: OAuth refreshes and `SOUL.md` edits stop causing managed gateway restarts; `.env` and managed config changes remain restart-triggering.
