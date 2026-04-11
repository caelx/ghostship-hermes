## Why

The current `ghostship-hermes-base` image is still a repo-specific image contract with shim binaries standing in for the real router, dashboard, runtime, and `ghostship-*` utilities. That keeps the base layer too tightly coupled to repo-owned runtime wiring and limits how much reuse we get from the base image when only overlay content changes.

## What Changes

- Split the current image definition into a true Hermes base layer and a repo-content layer instead of reusing one NixOS module with shim binaries.
- Keep the base image focused on the upstream Hermes runtime, core OS contract, container boot requirements, and every stable shared dependency closure that the Ghostship router, dashboard, runtime, wrapped Hermes layer, and `ghostship-*` utilities repeatedly need.
- Remove all Ghostship-owned runtime packages and managed service wiring from the base image, including `wrappedHermesAgent`, Ghostship bootstrap/tooling units, `ghostship-*`, `ghostship-hermes-router`, `ghostship-hermes-runtime`, and `hermes-dashboard`.
- Verify the split from the built base image and its realized closure, not just from source-level module boundaries.
- Treat the current approved base-side shared dependency set as part of the proposal acceptance criteria: the shared Python service deps (`httpx`, `typer`, `fastapi`, `uvicorn`, `websockets`) and the stable external utility closures (`agent-browser`, `bws`, `gcloud`, `gws`) belong in base unless a later audit shows they cause unacceptable base churn.
- Preserve the published `ghostship-hermes` consumer contract and multi-arch publish flow while making the internal base/content boundary materially cleaner and more reusable.

## Capabilities

### New Capabilities
- `true-hermes-base-image`: Define the internal image architecture where the reusable base image contains only the Hermes runtime and core container contract, while repo-owned router/dashboard/utility content is added in the final image layer.

### Modified Capabilities
- `image-publication-contract`: Clarify that the publish pipeline may build the final `ghostship-hermes` image by layering repo-owned content onto a true Hermes base image, while preserving the existing consumer-facing artifact semantics.

## Impact

- Affected workflows: `.github/workflows/publish-image.yml`
- Affected flake/image code: `flake.nix`, `packages/hermes-image/*`, and any split NixOS modules introduced for base vs final image composition
- Affected docs: `README.md`, `CHANGELOG.md`, `docs/github-actions-build-optimization.md`, `AGENTS.md`
- Affected systems: GHCR base/final image publication flow, NixOS image composition, systemd/runtime wiring inside the published image
