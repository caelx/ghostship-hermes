## Why

GitHub Actions currently spends too much time in `publish-image`, and the work to optimize it has fragmented into three overlapping OpenSpec tracks: broad workflow optimization, repeat-publish reuse, and the true base-image split. They are all parts of the same problem and should be tracked as one change.

## What Changes

- Keep one consolidated GitHub Actions image-optimization change that covers publish gating, cache/reuse strategy, immutable repeat-publish reuse, and the true Hermes base-image split.
- Preserve the free-only optimization strategy by using GHCR-backed reuse instead of paid cache services.
- Keep the publish workflow focused on three layers of reuse: skip irrelevant publishes, reuse a stable per-architecture base image when the base payload is unchanged, and reuse immutable per-architecture final images when the full content is unchanged.
- Keep the base image limited to upstream Hermes/core runtime behavior plus the approved shared dependency closures that materially reduce overlay churn.
- Measure the remaining cold, base-reuse, and warm-repeat publish paths so the final result is evidenced instead of guessed.

## Capabilities

### New Capabilities
- `github-actions-build-optimization`: Define how the repo measures, iterates, and validates GitHub Actions image-performance changes across multiple optimization rounds with explicit timing baselines and regression checks.
- `repeat-image-publish-reuse`: Define the free-only GHCR-backed reuse strategy for repeat image publication, including stable base-image lookup, immutable final-image lookup, fallback behavior, and timing expectations.
- `true-hermes-base-image`: Define the internal image architecture where the reusable base image contains only the Hermes runtime/core container contract plus approved shared dependencies, while repo-owned router/dashboard/utility content is added in the final image layer.

### Modified Capabilities
- `image-publication-contract`: Clarify that GitHub Actions publication may skip irrelevant pushes, reuse stable base images, retag immutable architecture images when their content matches, and assemble the final `ghostship-hermes` image from a true Hermes base layer without changing the consumer-facing contract.

## Impact

- Affected workflows: `.github/workflows/ci.yml`, `.github/workflows/publish-image.yml`, `.github/workflows/update-hermes-release.yml`
- Affected build/image code: `flake.nix`, `packages/hermes-image/*`, and any helper scripts used for image publication
- Affected documentation: `README.md`, `CHANGELOG.md`, `docs/github-actions-build-optimization.md`, `AGENTS.md`
- Expected outcome: fewer unnecessary publish runs, a more reusable base-image boundary, materially smaller overlays, and measured evidence for cold/base-reuse/warm-repeat publish behavior
