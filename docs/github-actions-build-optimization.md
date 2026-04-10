# GitHub Actions Build Optimization

This note captures the measured optimization baseline for the `optimize-github-actions-image-builds` change and the acceptance metrics used for each implementation round.

## Baseline

Captured on 2026-04-10 UTC from recent successful GitHub Actions runs:

- `ci`: approximately `9.5` minutes average over the last 10 successful runs
- `publish-image`: approximately `36.9` minutes average over the last 10 successful runs
- Latest successful `publish-image` job breakdown:
  - `build (x86_64-linux, ubuntu-24.04)`: approximately `33.5` minutes
  - `build (aarch64-linux, ubuntu-24.04-arm)`: approximately `26.4` minutes
  - `publish`: approximately `4.9` minutes

The current long pole is the native multi-arch publish path, not the lightweight `ci` verification path.

## Acceptance Metrics

Use these metrics for each optimization round:

- `publish-image` runner frequency: how often the workflow runs after path gating lands
- `publish-image` warm-cache elapsed time: the main steady-state success metric
- `publish-image` cold-cache elapsed time: to confirm worst-case behavior remains reasonable
- `ci` elapsed time: to verify Python utility setup changes reduce overhead without weakening checks
- Whole-workflow elapsed time and major job timings: to distinguish build bottlenecks from workflow overhead

The stretch target for this change remains approximately `10` minutes end-to-end for `publish-image`, but the evaluation should distinguish between cold-cache and warm-cache results.

## Workflow Strategy

Optimization rounds are implemented in this order:

1. Conservative publish gating so docs-only and OpenSpec-only `main` pushes do not publish images.
2. Cache-backed reuse:
   - optional Cachix-backed Nix substitution via `vars.CACHIX_CACHE_NAME` and `secrets.CACHIX_AUTH_TOKEN`
   - native `uv` caching for the Python utility steps in `ci`
3. Architectural publish optimization by pushing architecture-specific images directly from the build jobs and reserving the final manifest job for manifest creation only.

## Measuring Again

Use the repo helper script after each round:

```fish
python3 scripts/github_actions_timings.py --include-latest-jobs
```

If you want to target one workflow only:

```fish
python3 scripts/github_actions_timings.py --workflow publish-image.yml --include-latest-jobs
```

## Cache Notes

Cachix is optional so the workflows still function in forks or repos without cache credentials.

- Set repository variable `CACHIX_CACHE_NAME` to enable pull access to a named cache.
- Set repository secret `CACHIX_AUTH_TOKEN` to allow GitHub Actions to push newly built store paths.
- When the cache is disabled or cold, the workflows should still complete correctly; only performance changes.
- `uv` cache keys are derived from the tracked Python utility inputs and lockfiles, so dependency changes create a new cache key automatically.
