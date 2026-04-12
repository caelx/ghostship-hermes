## Why

The shared `ghostship-cache` rollout did not actually seed a reusable cache. `publish-image` currently plans cache uploads after the real `nix build`, so the upstream dry-run planner sees no remaining build work, emits zero paths, and never writes a `cache-index` for later runs to consume.

## What Changes

- Fix the `publish-image` shared-cache publication flow so a cold build can still seed `caelx/ghostship-cache`.
- Move cache publication planning to a pre-build point where the upstream dry-run planner can still detect the paths that need to be cached.
- Keep image publication non-blocking when cache planning or upload fails, but ensure successful cold runs can create the cache index required for later warm-cache reuse.
- Add explicit verification and operator-facing evidence that a seeded run creates `cache-index` and that a later unchanged run consumes the shared cache instead of silently falling back to uncached builds.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `shared-nix-binary-cache`: Refine the cache publication contract so successful cold runs seed a usable `cache-index` and later runs can consume the shared cache.
- `image-publication-contract`: Refine `publish-image` so cache planning happens early enough to support later warm-cache reuse without changing the explicit `ghostship-hermes-image` artifact contract.

## Impact

- Affected code: `.github/workflows/publish-image.yml`, `scripts/shared_nix_cache.sh`, and shared-cache documentation/runbooks.
- Affected systems: GitHub Actions `publish-image`, `caelx/ghostship-cache`, GHCR-backed cache index publication, and warm-cache verification.
- Dependencies: existing `nixcache-oci` integration, GHCR package write permissions, and the current shared-cache signing configuration.
