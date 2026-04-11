## Why

The repo now has a correct free-only multi-arch publish path, but the first successful `publish-image` run for the current architecture split still took roughly 35 minutes on `amd64` and 30 minutes on `arm64`. That is too slow for repeated publish validations, reruns, and workflow-only releases, especially when the image contents have not changed and GHCR already holds equivalent immutable images.

## What Changes

- Define a focused publish optimization that keeps the per-architecture GHCR base image reusable across overlay-only repo changes instead of keying it to the raw Nix derivation path.
- Record the free-only publish strategy explicitly: stable base-image reuse from tracked base inputs first, immutable content-addressed final-image reuse second, native rebuild only when neither reusable image exists.
- Measure and document whether the base-image reuse boundary materially reduces the slow `Ensure base image tag exists` step on repeated publishes.
- Keep the existing native multi-arch correctness checks and published `ghostship-hermes` image contract intact while tightening the reuse rules around the slow-changing base layer.

## Capabilities

### New Capabilities
- `repeat-image-publish-reuse`: Define the free-only GHCR-backed reuse strategy for repeat image publication, including stable base-image lookup, immutable final-image lookup, fallback behavior, and timing expectations.

### Modified Capabilities
- `image-publication-contract`: Clarify that internal publication may retag previously published immutable architecture images when their evaluated content matches, while preserving the documented consumer-facing `ghostship-hermes` contract.

## Impact

- Affected workflows: `.github/workflows/publish-image.yml`
- Affected documentation: `README.md`, `CHANGELOG.md`, `docs/github-actions-build-optimization.md`
- Affected systems: GHCR image publication flow, GitHub Actions publish reruns, immutable architecture tag strategy
- Expected outcome: overlay-only publish changes stop forcing a base-image rebuild, and repeat publishes reuse both the stable base tag and the immutable final-image tag whenever the actual image content matches
