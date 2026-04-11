## Why

The current GitHub `publish-image` workflow regained the correct managed-runtime behavior for the published image, but it did so by building the full final `ghostship-hermes-image` derivation for every non-reused content publish. That bypasses the intended base-plus-overlay acceleration path, so the content leg now pays the cost of the full final NixOS tarball again.

## What Changes

- Restore GitHub final-image assembly to the reusable `ghostship-hermes-base` plus `ghostship-hermes-overlay-bundle` path for non-reused content publishes.
- Add a GitHub-side runtime-contract verification step that exercises the exact architecture image built from that layered path before the workflow pushes it to GHCR.
- Update the image publication and repeat-reuse specs so the fast path is only valid when it verifies the actual image destined for publication.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `image-publication-contract`: Clarify that faster internal assembly is allowed only when the workflow verifies the exact publish-bound image against the managed runtime contract.
- `repeat-image-publish-reuse`: Restore immutable final-image reuse to the base-plus-overlay content identity used by the GitHub publish path.
- `github-actions-build-optimization`: Require workflow-side verification for optimized internal image assembly paths.

## Impact

- `.github/workflows/publish-image.yml`
- `tests/hermes-image/`
- `README.md`
- `CHANGELOG.md`
- `AGENTS.md`
- OpenSpec publication/reuse/optimization specs
