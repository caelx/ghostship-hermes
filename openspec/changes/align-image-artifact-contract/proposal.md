## Why

The workstation refactor changed `ghostship-hermes-image` from a Docker archive-style artifact to a NixOS tarball output, but the repo's publish workflow, test helpers, and image assumptions were not updated together. As a result, image CI now fails after a successful Nix build, and the repo no longer has a single explicit contract for what build artifact downstream consumers should use.

## What Changes

- Define a canonical build artifact contract for `ghostship-hermes` so flake outputs, CI publishing, and local validation all agree on what `ghostship-hermes-image` represents.
- Add a repo-owned path for turning the current workstation-oriented NixOS image output into a publishable container image with the required runtime metadata, instead of relying on mismatched ad hoc assumptions in workflows and tests.
- Update GitHub Actions image publishing to use the canonical artifact path and publish the expected GHCR tags from the same image format that local validation consumes.
- Update repo test helpers and docs so they describe and exercise the same artifact contract used by CI.
- Make the image output naming and consumption flow explicit enough that future runtime refactors cannot silently break publishing again.

## Capabilities

### New Capabilities
- `image-publication-contract`: Define the canonical `ghostship-hermes` image artifact, the conversion/publication path to GHCR, and the aligned expectations for CI and local validation consumers.

### Modified Capabilities

## Impact

- Affected code: `flake.nix`, `packages/hermes-image/`, `.github/workflows/publish-image.yml`, validation and image-test scripts
- Affected systems: multi-arch image publishing, local Docker validation, repo image test harnesses, and image build output naming
- Affected docs: `README.md`, `CHANGELOG.md`, and any repo guidance that describes how maintainers build, validate, or publish the image
