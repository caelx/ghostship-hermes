## Why

The current workstation image ships image-managed helper utilities from Nix by writing `/opt/ghostship/bin/*` symlinks directly to build-time `/nix/store/...` paths. That works on a fresh `/nix` seed, but it breaks on reused persisted `/nix` volumes because existing non-empty mounts are not reconciled to the new image's expected store paths.

## What Changes

- Add a managed Nix default-tool profile that the image exports and the boot sequence reconciles into persisted `/nix` on every start.
- Replace direct `/opt/ghostship/bin -> /nix/store/...` helper symlinks for Nix-backed defaults with a managed per-image Nix profile path that survives reused `/nix` mounts.
- Define the baseline image-managed Nix helper set as part of the workstation contract for tools such as `bws`, `gws`, `gh`, `gcloud`, and `blogtato`.
- Document and validate upgrade behavior for reused non-empty `/nix` mounts so downstream operators understand how image updates refresh the managed default tool set without deleting user-installed Nix packages.
- **BREAKING**: Existing runtime/tooling docs and specs that describe these utilities as downstream-only optional installs will be updated to match the current image-managed utility contract.

## Capabilities

### New Capabilities
- `managed-nix-default-tool-profile`: Export, import, and reconcile an image-managed Nix profile for baseline helper utilities across persisted `/nix` reuse.

### Modified Capabilities
- `managed-runtime-tooling`: Change the workstation helper-tool contract from direct Nix store symlinks to a reconciled managed Nix default profile, and define which helper tools are guaranteed by the image.
- `agent-workstation-home-state`: Change the persisted `/nix` guidance so reused non-empty mounts are a supported upgrade path only when the runtime reconciles the managed default profile on boot.
- `bitwarden-cli-runtime`: Change the `bws` contract from optional downstream install to image-managed default availability through the reconciled Nix profile.
- `github-and-ssh-cli-runtime`: Change the `gh` availability contract to image-managed default availability through the reconciled Nix profile while keeping SSH client tooling in the immutable OS layer.
- `google-cloud-cli-runtime`: Change the `gcloud` availability contract from optional downstream install to image-managed default availability through the reconciled Nix profile.
- `google-workspace-cli-runtime`: Change the `gws` availability contract from optional downstream install to image-managed default availability through the reconciled Nix profile.

## Impact

- Affected code: `packages/hermes-image/Dockerfile`, `packages/hermes-image/rootfs/etc/cont-init.d/10-ghostship-prepare`, smoke/runtime validation, and workstation docs.
- Affected systems: image boot reconciliation, persisted `/nix` upgrade behavior, helper CLI discovery on the Hermes-user `PATH`, and downstream deployment guidance.
- Affected specs/docs: runtime tooling, persisted-home `/nix` guidance, Bitwarden/GitHub/Google Cloud/Google Workspace CLI runtime contracts, and README/runtime deployment documentation.
