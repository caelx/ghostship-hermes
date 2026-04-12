## Context

`ghostship-hermes` already has a shared-cache rollout in flight through `caelx/ghostship-cache`, but the first successful publish run never created a usable `cache-index`. GitHub Actions logs show why: cold runs skip cache consumption, then build the image, then run cache planning after the build. The pinned upstream `nixcache-oci` planner determines upload candidates by running `nix build --dry-run` and parsing the `will be built` set. After the real build has already succeeded on that runner, the dry-run planner sees no remaining work, returns zero paths, and the subsequent publish step becomes a no-op.

This is a cross-cutting workflow issue rather than a package bug. It affects the publish workflow order, the helper contract in `scripts/shared_nix_cache.sh`, the meaning of successful cache seeding, and the operator evidence maintainers rely on when deciding whether warm-cache reuse is working.

## Goals / Non-Goals

**Goals:**
- Make a successful cold `publish-image` run seed a real `cache-index` in `caelx/ghostship-cache`.
- Preserve the existing reliability rule that image publication must still succeed when cache bootstrap, planning, or publication is unavailable.
- Keep the explicit host-side `ghostship-hermes-image` build and publication contract unchanged.
- Produce verification evidence that distinguishes cache seeding from actual warm-cache consumption.

**Non-Goals:**
- Replace `nixcache-oci` with a different cache backend.
- Reintroduce image-parent, daily-image, or in-container build acceleration paths.
- Change the `ghostship-hermes-image` artifact contract or the GHCR image tag strategy.
- Expand shared-cache rollout to more repos or to runtime hosts in this fix.

## Decisions

### 1. Plan cache uploads before the real build
The workflow should run cache planning before `nix build`, then carry the resulting plan forward to the post-build upload step.

This matches how the pinned upstream planner works today: it uses `nix build --dry-run` to detect what would need to be built on that runner. Running that planner before the real build preserves the information needed to seed the cache.

Alternative considered: keep planning after the build and teach `scripts/shared_nix_cache.sh` to derive upload candidates from the realized closure instead of dry-run output. Rejected for this fix because it is more invasive, duplicates upstream cache-builder logic, and creates more room for closure-selection mistakes.

### 2. Keep planning and publication best-effort
Pre-build cache planning should never block the actual image build. If planning fails, the workflow should clear the plan file, mark cache publication disabled for that leg, and continue to publish the image normally. Post-build cache upload should remain non-fatal as well.

Alternative considered: fail the publish when planning fails. Rejected because the repo explicitly chose a fail-open availability model for cache cold-start and infrastructure problems.

### 3. Treat `cache-index` creation as the cold-run success signal
A run only counts as cache seeding if it both computes a non-empty upload plan and publishes enough entries to create or update the OCI `cache-index` manifest in `caelx/ghostship-cache`. Workflow docs and verification notes should say that plainly.

Alternative considered: treat a successful `Publish shared cache entries` step as sufficient evidence. Rejected because the current bug proved that a no-op upload can still exit successfully without creating a consumable cache.

### 4. Verify warm-cache reuse from workflow logs, not only from elapsed time
Warm-cache verification should look for explicit evidence that the shared cache bootstrap succeeded and that subsequent `nix build` reused store paths through the configured cache path, instead of relying only on wall-clock comparisons. Timing still matters, but it is secondary evidence.

Alternative considered: use duration deltas alone as proof. Rejected because runner variance and cancellation can easily hide or mimic speedups.

## Risks / Trade-offs

- [Pre-build dry-run planning may take extra time] -> Keep it narrow, bounded, and non-fatal so it adds a small fixed cost without threatening publication reliability.
- [The upstream planner may still exclude paths that are already available from `cache.nixos.org`] -> Accept that behavior; the goal is to seed Ghostship-specific gaps and shared non-upstream paths, not mirror all public cache content.
- [Logs may still be noisy or incomplete for proving substitution use] -> Document the exact bootstrap and reuse signals maintainers should check in GitHub Actions before judging whether the cache is working.

## Migration Plan

1. Move cache planning ahead of the real `ghostship-hermes-image` build while keeping the upload step after publication.
2. Preserve the current non-fatal fallback path for planning and upload failures.
3. Run one cold publish to seed `cache-index` in `caelx/ghostship-cache`.
4. Run one unchanged follow-up publish and record whether bootstrap uses the shared cache and whether warm-cache reuse is visible in the build logs and timing.
5. If the warm run still does not show meaningful reuse, investigate cache contents or substitution wiring separately instead of reverting the artifact contract again.

## Open Questions

- Do we want `scripts/shared_nix_cache.sh` to grow a second planning mode based on realized closures later, or is the upstream dry-run contract sufficient once the workflow order is corrected?
- How much timing improvement should count as material enough to close the measurement task for `add-ghostship-cache`?
