## Why

The live `ghostship-hermes` container on `chill-penguin-root` still fails its shutdown contract: Podman sends `SIGTERM`, waits for the container stop timeout, and then escalates to `SIGKILL` even when given more than the default 10-second grace period. The same image also emits repeatable startup-time defects in stage-2 activation and lacks enough OCI provenance metadata to make source alignment obvious when inspecting a deployed image.

## What Changes

- Repair the container stop path so the managed Hermes image exits cleanly on `SIGTERM` within the declared container stop budget instead of relying on Podman `SIGKILL`.
- Align the repo-owned managed gateway stop behavior with the upstream Hermes user-service contract where it materially affects shutdown semantics.
- Remove the known container-mode boot noise around `/etc/hostname`, `/etc/hosts`, and root channel symlink creation under `/root/.nix-defexpr`.
- Optimize the managed user-tooling convergence path so normal boots do not remove and re-add the entire managed Nix profile and npm layer when the desired state is already current.
- Extend runtime validation so image-level and live-host checks cover clean stop behavior and the absence of the current non-fatal activation defects.
- Add richer OCI labels for the published image so operators can verify the source repo and revision directly from the deployed artifact.

## Capabilities

### New Capabilities
- `hermes-container-runtime-contract`: Defines the required stop behavior, activation compatibility, boot-time tooling convergence, and container-mode runtime invariants for the published Hermes image.

### Modified Capabilities
- `image-publication-contract`: The published image metadata contract now includes source and revision provenance labels in addition to the existing title, description, and version labels.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, `packages/hermes-image/image.nix`, host/image validation scripts, and any image tests that assert startup and shutdown behavior.
- Affected systems: the NixOS container activation path, the managed Hermes gateway user service, Podman-managed restarts on live hosts, and GHCR image metadata inspection.
- Dependencies: current upstream Hermes gateway service expectations, Podman stop-timeout behavior, and existing image publication/validation workflows.
