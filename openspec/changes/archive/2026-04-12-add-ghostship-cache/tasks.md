## 1. ghostship-cache repo contract

- [x] 1.1 Add `README.md` in `ghostship-cache` describing it as the shared GHCR-backed Nix binary cache for Ghostship repos.
- [x] 1.2 Add `AGENTS.md` in `ghostship-cache` documenting publisher policy, consumer expectations, signing requirements, and the fact that this repo is infrastructure rather than an app repo.
- [x] 1.3 Document the initial phase-1 scope: `ghostship-hermes` `publish-image` is the first consumer/publisher, while other repos remain future adopters.

## 2. Signed cache wiring

- [x] 2.1 Define the `nixcache-oci` layout and runbook for `caelx/ghostship-cache`, including the GHCR package namespace and required GitHub permissions.
- [x] 2.2 Establish the shared Ghostship cache signing model and document how consumer repos trust the public key.
- [x] 2.3 Document the workflow secrets/config needed for `ghostship-hermes` to publish cache entries safely.

## 3. ghostship-hermes publish integration

- [x] 3.1 Update `publish-image` to bootstrap a runner-local `nixcache-oci` proxy backed by `caelx/ghostship-cache` before `nix build`.
- [x] 3.2 Configure the workflow to consume the shared cache during `nix build` while preserving the explicit `ghostship-hermes-image` host-side build and export path.
- [x] 3.3 Ensure cache bootstrap failure or cache cold-start conditions fall back to the existing full host-side build instead of failing the publish workflow.
- [x] 3.4 Ensure trust/signature mismatches fail the workflow instead of silently disabling verification.

## 4. Verification and measurement

- [x] 4.1 Add workflow or runbook verification that a cold publish still succeeds with an empty cache.
- [x] 4.2 Add verification that a warm repeat publish reuses cached store paths from `caelx/ghostship-cache`.
- [ ] 4.3 Record before/after timing evidence for the warm-cache publish path so maintainers can tell whether the shared cache materially helps.
