## Why

The Hermes image currently scaffolds three long-running managed profile gateways, but it does not give each profile its own inbound webhook listener contract. Enabling upstream Hermes webhook support naively would fail because all three gateways would contend for the same default webhook port and there is no repo-owned per-profile secret wiring yet.

## What Changes

- Add repo-owned scaffolding for the Hermes webhook adapter on all managed profiles: `assistant`, `operations`, and `supervisor`.
- Assign a distinct webhook listener port to each managed profile so all three gateway services can run concurrently without socket conflicts.
- Define a profile-specific secret env contract for each webhook listener and project the matching secret into that profile's managed `.env` only when the container provides it.
- Keep webhook enablement and port assignment repo-managed inside the Hermes image scaffold while leaving secret material external to the repo for deployment-specific secret management.
- Document the managed per-profile webhook listener contract and its dependency on external secret provisioning.

## Capabilities

### New Capabilities
- `hermes-profile-webhook-listeners`: Scaffold one webhook listener per managed Hermes profile, with distinct ports and profile-local secret wiring.

### Modified Capabilities
- `hermes-profile-env-contract`: Expand the managed profile `.env` contract so bootstrap rewrites per-profile webhook runtime inputs alongside the existing profile-facing env surface.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, README/runtime documentation, and related image validation coverage.
- Affected systems: managed Hermes bootstrap, managed profile `.env` generation, and the three repo-owned profile gateway services.
- External dependencies: deployment configuration must provide `WEBHOOK_ASSISTANT_SECRET`, `WEBHOOK_OPERATIONS_SECRET`, and `WEBHOOK_SUPERVISOR_SECRET`.
