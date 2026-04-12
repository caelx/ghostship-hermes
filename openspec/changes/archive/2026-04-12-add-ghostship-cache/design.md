## Context

`ghostship-hermes` tried two free acceleration paths before landing back on unconditional full native builds: GHCR image-layer reuse and a later daily full-image OCI parent path. Both approaches attacked Docker/image assembly more than the real Nix bottleneck, and the daily-image path additionally failed on raw imported image runtime mismatches (`libnixcmd.so`, OpenSSL loader mismatches, shell/path differences). The repo now needs a free cache design that accelerates Nix store reuse directly without weakening the explicit `ghostship-hermes-image` publication contract.

The user has created a dedicated infrastructure repo at `caelx/ghostship-cache`. That repo is intended to be a shared cache backend for multiple Ghostship Nix projects, not a Hermes-only implementation detail.

## Goals / Non-Goals

**Goals:**
- Use `caelx/ghostship-cache` as a shared GHCR-backed Nix binary cache for Ghostship repos.
- Scope phase 1 to `ghostship-hermes` GitHub `publish-image` consumption/publication only.
- Keep `publish-image` building the explicit `ghostship-hermes-image` bundle on the runner host.
- Use a signed cache trust model instead of unsigned global verification bypasses.
- Preserve publication reliability when the cache is cold, empty, or temporarily unavailable.

**Non-Goals:**
- Reintroduce image-parent or in-container daily build tricks.
- Change the published `ghostship-hermes` image contract or switch to a different image artifact.
- Roll out cache consumption to runtime hosts, local developer machines, or every Ghostship repo in the first round.
- Solve cache GC, retention tuning, or multi-repo onboarding for every future project in phase 1.

## Decisions

### 1. Treat `caelx/ghostship-cache` as shared infrastructure, not app-specific state
The cache repo should be documented and operated as one shared Ghostship binary-cache backend. `ghostship-hermes` is only the first client.

This keeps cache policy, signing, and GHCR-backed storage separate from application repos and makes later reuse across multiple Ghostship Nix projects straightforward.

Alternative considered: using `ghostship-hermes` itself as the cache repo. Rejected because it mixes application release concerns with cache infrastructure and makes multi-project reuse messier.

### 2. Use a runner-local `nixcache-oci` proxy in GitHub Actions
`publish-image` should start or connect to a runner-local `nixcache-oci` proxy that fronts `caelx/ghostship-cache`, then add that local endpoint as a Nix substituter during the build.

This attacks the real bottleneck: store-path reuse during `nix build`. It avoids relying on OCI images as fake Nix caches and does not require a separate always-on external proxy service in phase 1.

Alternative considered: hosting a long-lived shared proxy service elsewhere. Rejected for phase 1 because it adds infrastructure and availability dependencies before proving the repo-local workflow integration.

### 3. Use signed cache trust from the start
The shared cache should have one Ghostship cache signing identity. Consumer repos trust the corresponding public key; publisher workflows use the signing secret needed to populate the cache.

Alternative considered: unsigned mode. Rejected because the upstream tool warns that unsigned mode effectively weakens signature verification broadly, which is not a good default for shared infrastructure.

### 4. Keep `publish-image` on host-side full builds with cache-assisted reuse
The workflow should continue to build `.#packages.<system>.ghostship-hermes-image` on the runner host, export it with `scripts/export_publishable_image.sh`, and publish the explicit artifact contract to GHCR.

The shared cache is an acceleration layer for Nix dependency reuse, not a different image assembly contract.

Alternative considered: another internal publication architecture change tied to the cache. Rejected because the repo has already paid the complexity cost of multiple failed publication-path experiments.

### 5. Fail open on cache availability, fail closed on trust violations
If the shared cache is empty or the proxy/bootstrap path is unavailable before the build starts, the workflow should continue with the current full host-side build. If the cache responds with trust/signature mismatches, the workflow should fail rather than silently accepting untrusted artifacts.

This keeps publication reliable without turning cache configuration mistakes into hidden integrity regressions.

## Risks / Trade-offs

- [Cross-repo cache secrets and signing become shared infrastructure] → Keep phase 1 narrow, document publisher repos explicitly, and centralize cache-key handling in `ghostship-cache` runbooks.
- [A local proxy layer adds workflow complexity] → Keep the rest of `publish-image` unchanged so only the Nix-cache bootstrap path is new.
- [Cache misses may still look like “no speedup” on cold runs] → Record warm-repeat timing separately and compare against the current full-build baseline.
- [GHCR-backed cache growth can create retention pressure] → Document that `ghostship-cache` needs explicit retention/GC policy, but leave aggressive tuning for later phases.

## Migration Plan

1. Define and document `caelx/ghostship-cache` as the shared Ghostship Nix binary cache repo.
2. Add signed `nixcache-oci` publisher/consumer wiring for `ghostship-hermes` `publish-image` only.
3. Validate both paths in GitHub Actions:
   - cold build with empty cache still succeeds
   - warm build reuses cached store paths from `ghostship-cache`
4. Record before/after publish timing evidence for warm-cache publishes.
5. After phase 1 is stable, decide whether to extend the same cache to `ci` and to additional Ghostship repos.

## Open Questions

- Should `ghostship-cache` use one publisher credential shared by approved Ghostship repos, or one per publishing repo with the same signing identity?
- Should `ghostship-hermes` `ci` consume the shared cache in phase 1 as well, or should that wait until `publish-image` proves stable and useful?
- What retention and GC policy does `ghostship-cache` need before a second consumer repo is onboarded?
