## 1. Repair shutdown and activation behavior

- [x] 1.1 Update the managed `hermes-gateway.service` rendering in `packages/hermes-image/nixos-module.nix` so the unit exposes explicit graceful-stop fields aligned with the intended container shutdown contract.
- [x] 1.2 Adjust the image/container activation path so boot no longer emits the known `/etc/hostname`, `/etc/hosts`, or `/root/.nix-defexpr/channels/channels` write failures under the supported Podman deployment.
- [ ] 1.3 Rebuild or locally boot the image and verify that a supported stop/restart flow exits without Podman `SIGKILL`.

## 2. Optimize managed user-tooling convergence

- [x] 2.1 Refactor `ghostship-hermes-user-tooling` so the managed Nix profile reconciler mutates only changed entries instead of removing and re-adding the whole managed profile on every boot.
- [x] 2.2 Add a no-op fast path for the managed npm tool layer so unchanged declared dependencies do not rerun `npm install` on steady-state boots while drifted state still converges correctly.
- [ ] 2.3 Validate that a second steady-state boot avoids the current full tooling churn while an intentionally drifted managed entry is still repaired.

## 3. Extend metadata and validation coverage

- [x] 3.1 Update `packages/hermes-image/image.nix` so the publishable image carries OCI source and revision provenance labels alongside the existing title, description, and version metadata.
- [x] 3.2 Extend image-focused validation and/or live runtime checks to assert clean stop behavior, absence of the known activation warnings, and presence of the OCI provenance labels.
- [ ] 3.3 Re-run the relevant image tests and a live-host verification pass, then document the runtime-contract fix in `README.md` and `CHANGELOG.md`.
