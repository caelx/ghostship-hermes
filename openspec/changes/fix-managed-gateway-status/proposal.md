## Why

The managed Hermes image keeps the dashboard, router, and per-profile gateway services running correctly, but interactive `hermes` commands do not reliably recognize that the runtime is Nix-managed when they target named profiles. That causes `gateway status`, `start`, `stop`, and `restart` to report false negatives or offer upstream user-service guidance that does not match the repo-managed service topology, which is confusing for operators and risks accidental drift.

## What Changes

- Make managed-mode detection visible to profile-scoped interactive Hermes invocations, not only the root `HERMES_HOME` and running systemd services.
- Ensure gateway control and status commands for managed profiles either resolve the repo-owned `ghostship-hermes-profile-*` services correctly or fail fast with managed-runtime guidance instead of falling back to upstream user-service assumptions.
- Keep `doctor` and related operator-facing runtime reporting aligned with the actual managed gateway state so healthy managed profiles do not look broken.
- Add validation coverage for managed profile gateway status and control-path behavior in the image/runtime test flow.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `agent-workstation-runtime`: The managed workstation runtime must expose the correct managed-state and gateway-service identity to interactive Hermes commands for the root profile and named managed profiles.
- `agent-workstation-updates`: Operator-facing health and doctor reporting must reflect the actual managed gateway runtime instead of reporting false gateway failures for healthy managed profiles.

## Impact

- Affected code: [packages/hermes-image/nixos-module.nix](/home/nixos/dev/ghostship-hermes/packages/hermes-image/nixos-module.nix), [packages/hermes-agent-wrapped/package.nix](/home/nixos/dev/ghostship-hermes/packages/hermes-agent-wrapped/package.nix), and managed-runtime validation scripts/tests.
- Affected systems: interactive Hermes CLI behavior inside the managed container, per-profile gateway supervision, and operator diagnosis workflows.
- Documentation impact: managed-runtime guidance should clarify how gateway control behaves inside the image and what is intentionally repo-managed versus upstream-native.
