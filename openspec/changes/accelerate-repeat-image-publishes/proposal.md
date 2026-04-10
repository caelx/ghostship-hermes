## Why

The repo now has a correct free-only multi-arch publish path, but the first successful `publish-image` run for the current architecture split still took roughly 35 minutes on `amd64` and 30 minutes on `arm64`. That is too slow for repeated publish validations, reruns, and workflow-only releases, especially when the image contents have not changed and GHCR already holds equivalent immutable images.

## What Changes

- Define a focused repeat-publish optimization that prefers reusing already published immutable images in GHCR before rebuilding them.
- Record the free-only publish strategy explicitly: immutable content-addressed final-image reuse first, reusable per-architecture base-image reuse second, native rebuild only when neither reusable image exists.
- Measure and document the warm-repeat publish behavior separately from the cold-content publish path so maintainers can judge whether reruns and workflow-only publishes meet a materially lower latency target.
- Keep the existing native multi-arch correctness checks and published `ghostship-hermes` image contract intact while tightening the reuse rules around immutable content tags.

## Capabilities

### New Capabilities
- `repeat-image-publish-reuse`: Define the free-only GHCR-backed reuse strategy for repeat image publication, including immutable content-addressed image lookup, fallback behavior, and measurement expectations for warm-repeat publishes.

### Modified Capabilities
- `image-publication-contract`: Clarify that internal publication may retag previously published immutable architecture images when their evaluated content matches, while preserving the documented consumer-facing `ghostship-hermes` contract.

## Impact

- Affected workflows: `.github/workflows/publish-image.yml`
- Affected documentation: `README.md`, `CHANGELOG.md`, `docs/github-actions-build-optimization.md`
- Affected systems: GHCR image publication flow, GitHub Actions publish reruns, immutable architecture tag strategy
- Expected outcome: warm-repeat publish runs and workflow-only republish flows avoid redundant native rebuilds when GHCR already contains the exact immutable image content
