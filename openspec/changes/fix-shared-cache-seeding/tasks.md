## 1. Restore real cache seeding

- [ ] 1.1 Move shared-cache planning in `publish-image` to a pre-build step and persist the plan file for later upload.
- [ ] 1.2 Keep cache planning and cache publication non-fatal so image publication still succeeds when the shared cache is unavailable.
- [ ] 1.3 Update `scripts/shared_nix_cache.sh` or related workflow wiring so the saved pre-build plan is the input to post-build cache publication.

## 2. Verify cache behavior

- [ ] 2.1 Run a cold `publish-image` workflow and confirm it creates or updates `cache-index` in `caelx/ghostship-cache`.
- [ ] 2.2 Run an unchanged follow-up `publish-image` workflow and confirm bootstrap detects the shared cache before `nix build`.
- [ ] 2.3 Capture log evidence showing whether the warm run reused cached store paths or fell back to uncached behavior.

## 3. Document the fixed contract

- [ ] 3.1 Update the shared-cache docs and changelog to explain that pre-build planning is required for the current dry-run-based seeding path.
- [ ] 3.2 Record before/after warm-cache timing evidence and note any residual limits if the cache still does not materially speed the build.
