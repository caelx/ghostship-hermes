## Why

GitHub Actions currently spends roughly 9 to 10 minutes in `ci` and 35 to 42 minutes in `publish-image` for each `main` push, with the full publish path rebuilding both native image variants even for many non-runtime changes. That cost is high enough to slow iteration, delay release confidence, and make the image pipeline materially more expensive than the actual code-change risk often warrants.

## What Changes

- Add a measured GitHub Actions build optimization workflow that captures a baseline, applies changes in rounds, and compares each round against explicit timing goals.
- Add workflow gating so image publication runs only when image-affecting files or release events require it, instead of on every `main` push.
- Introduce binary-cache-backed build reuse for Nix and package-manager caches for Python utility test setup so repeated runs avoid rebuilding or redownloading unchanged dependencies.
- Restructure image publication so the workflow can take materially faster architectural paths when they preserve the repo's explicit image contract, including prebuilt intermediate artifacts, reused image closures, or alternative assembly/publish flows.
- Define a stretch performance target of approximately 10 minutes end-to-end for the publish path, while preserving correctness, multi-arch publication, and the explicit `ghostship-hermes-image` contract.

## Capabilities

### New Capabilities
- `github-actions-build-optimization`: Define how the repo measures, iterates, and validates CI/build-performance changes across multiple optimization rounds with explicit timing baselines and regression checks.

### Modified Capabilities
- `image-publication-contract`: Tighten the image publication requirements so GitHub Actions publication can skip irrelevant pushes, reuse prior build outputs through supported caches, and adopt faster architecture-preserving assembly paths without breaking the publishable image contract.

## Impact

- Affected workflows: `.github/workflows/ci.yml`, `.github/workflows/publish-image.yml`, `.github/workflows/update-hermes-release.yml`
- Affected build definitions and helper scripts: `flake.nix`, `scripts/export_publishable_image.sh`, and any new timing/cache helper scripts introduced by the change
- Affected systems: GitHub Actions runners, GHCR publication flow, Nix substituter/binary cache configuration, Python utility test environment setup
- Expected outcome: fewer unnecessary publish runs and lower build/publish latency for runs that remain necessary
