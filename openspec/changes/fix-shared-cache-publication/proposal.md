## Why

`publish-image` still does not produce a consumable shared cache even after the pre-build planning correction. The latest publish runs prove the remaining blocker is the cache publication path itself: the uploader crashes before it can write `cache-index`, and later runs still cold-start from scratch.

## What Changes

- Fix shared-cache publication so successful cold runs can finish writing `cache-index` instead of failing in the upstream index-update path.
- Harden shared-cache bootstrap and proxy wiring so public-cache reads keep working and authenticated reads remain available as a fallback without changing the normal fast path.
- Remove or avoid redundant cache-side workflow probes that add network roundtrips without improving publish correctness.
- Keep `publish-image` fail-open for cache bootstrap and cache upload failures so image publication still completes.
- Treat cache proof as an operator/manual validation flow driven from run logs, not as an added workflow verification step that slows normal publishes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `shared-nix-binary-cache`: Refine the shared cache contract so successful publication must complete `cache-index` updates, bootstrap supports the public-cache fast path with authenticated fallback, and consumer wiring does not depend on extra workflow-only probes.
- `image-publication-contract`: Refine `publish-image` so cache publication fixes do not add new steady-state workflow drag and warm-cache proof can be established manually from existing run evidence.

## Impact

- Affected code: `.github/workflows/publish-image.yml`, `scripts/shared_nix_cache.sh`, and the pinned `nixcache-oci` helper integration path.
- Affected systems: GitHub Actions `publish-image`, `caelx/ghostship-cache`, GHCR-backed cache publication, and runner-local shared-cache bootstrap.
- Validation impact: proof will require manual comparison of seeded and repeat `workflow_dispatch` runs rather than adding new workflow jobs or checks.
