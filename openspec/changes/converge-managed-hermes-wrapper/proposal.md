## Why

The current Hermes image can boot with a newer baked runtime contract while persisted user-layer state still carries older repo-managed CLI or config content forward. That split-brain lets healthy runtime services look broken to operators, and it also risks preserving unwanted repo-managed profile settings such as Discord auto-threading after the intended runtime contract has changed.

## What Changes

- Converge repo-managed persisted user-layer system state with the image-baked runtime contract on replacement or boot, starting with `hermes-agent-wrapped` and other repo-owned managed runtime config that must track the current image.
- Prevent stale persisted `hermes-agent-wrapped` profile installs from shadowing newer baked gateway-status, doctor, and managed-runtime behavior after an image update.
- Ensure repo-managed profile scaffold settings also converge when the intended runtime contract changes, including disabling Discord auto-thread creation for `assistant`, `operations`, and `supervisor` across all channels.
- Tighten runtime validation so image replacement checks prove the active interactive `hermes` binary and the managed profile scaffold/config both reflect the current runtime generation rather than older persisted state.
- Keep the mutable managed profile flow for supported user tooling, but make convergence behavior explicit for repo-owned system config instead of depending on missing-package bootstrap only.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `agent-workstation-runtime`: The managed runtime must converge repo-managed persisted user-layer system state with the image/runtime generation after replacement so baked runtime fixes are not hidden by stale profile installs or stale managed scaffold values.
- `agent-workstation-updates`: Operator-facing doctor and gateway reporting must stay aligned with the currently booted image/runtime generation even when `/home/hermes` persists across replacement.
- `hermes-profile-env-contract`: Managed profile-facing Discord and related runtime config must converge to the current repo-owned scaffold on bootstrap, including disabling Discord auto-thread creation for the managed profiles.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, `packages/hermes-agent-wrapped/package.nix`, managed bootstrap/user-tooling convergence logic, and image/runtime validation coverage.
- Affected systems: managed user tooling convergence, interactive `hermes` CLI resolution, managed profile scaffold/config convergence, Discord runtime defaults, managed gateway status/doctor reporting, and persisted-home image replacement behavior.
- Operational impact: image rollouts should converge repo-managed persisted system config predictably instead of leaving CLI behavior or managed profile defaults pinned to older user-layer state.
