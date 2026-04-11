## Why

The current GitHub `publish-image` workflow regained the correct managed-runtime behavior for the published image, but it did so by building the full final `ghostship-hermes-image` derivation for every non-reused content publish. That bypasses the intended base-plus-overlay acceleration path, so the content leg now pays the cost of the full final NixOS tarball again.

## What Changes

- Restore GitHub final-image assembly to the reusable `ghostship-hermes-base` plus `ghostship-hermes-overlay-bundle` path for non-reused content publishes.
- Make the immutable final-image reuse key follow that same layered GitHub assembly path again.
- Update the image publication and repeat-reuse specs so the layered GitHub path and the explicit local bundle contract are documented separately.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `image-publication-contract`: Clarify that GitHub publication may use a faster layered internal assembly path while local export and smoke flows keep using the explicit `ghostship-hermes-image` bundle.
- `repeat-image-publish-reuse`: Restore immutable final-image reuse to the base-plus-overlay content identity used by the GitHub publish path.
- `github-actions-build-optimization`: Keep the optimization contract focused on the layered GitHub path instead of the full final rootfs bundle.

## Impact

- `.github/workflows/publish-image.yml`
- `README.md`
- `CHANGELOG.md`
- `AGENTS.md`
- OpenSpec publication/reuse/optimization specs
