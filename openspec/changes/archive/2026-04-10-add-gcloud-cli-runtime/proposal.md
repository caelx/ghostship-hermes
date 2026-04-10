## Why

The image already ships a small set of approved non-`ghostship-*` CLIs through declarative Nix package wiring, but it does not currently include the Google Cloud CLI. Adding `gcloud` now lets operators use Google Cloud workflows inside the Hermes image without introducing an ad hoc installer path or drifting away from the repo's image-build model.

## What Changes

- Add the `gcloud` CLI to the default Hermes image from `nixpkgs` so it is available on `PATH` automatically at runtime.
- Extend the repo's approved extra-CLI policy and docs to include `gcloud` alongside the existing explicitly allowed non-`ghostship-*` tools.
- Verify that the package wiring remains part of the normal flake/image evaluation path for both supported publish architectures.

## Capabilities

### New Capabilities
- `google-cloud-cli-runtime`: define the default-image contract for shipping `gcloud` through the repo's normal Nix/image package wiring.

### Modified Capabilities
- None.

## Impact

- `flake.nix` and image package wiring that determine which utilities ship on the runtime `PATH`
- Runtime policy and operator guidance in `AGENTS.md`, `README.md`, and `CHANGELOG.md`
- A new OpenSpec capability describing the Google Cloud CLI runtime contract
