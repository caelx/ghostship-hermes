## Why

The published `ghostship-hermes:latest` image can diverge from the repo's documented single-agent runtime contract even when `main` and the local image smoke test are correct. The current publish workflow assembles the final GHCR artifact from a reusable base image plus an overlay bundle, and that fast path can omit the final NixOS runtime wiring that rewrites `/home/hermes/.hermes/.env` and consumes the root seed content.

## What Changes

- Update the GHCR publish workflow so the final `ghostship-hermes` tags are built and published from the explicit `ghostship-hermes-image` bundle instead of a sidecar base-plus-overlay reconstruction path.
- Derive immutable final-image reuse identifiers from the explicit publishable image artifact so exact-repeat publishes stay reusable without publishing a runtime-different artifact.
- Refresh the publication docs and change log so the documented publish path matches the shipped image behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `image-publication-contract`: Tighten the publishable-image contract so GHCR publication must preserve the final managed runtime bootstrap behavior, not just container metadata.
- `repeat-image-publish-reuse`: Tighten immutable final-image reuse so the reuse key comes from the explicit publishable image artifact rather than a sidecar assembly path that can drift from it.

## Impact

- `.github/workflows/publish-image.yml`
- `README.md`
- `CHANGELOG.md`
- OpenSpec publication/reuse specs
