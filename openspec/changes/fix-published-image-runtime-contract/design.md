## Context

The repo already has the correct single-agent bootstrap behavior in the final NixOS image module: it rewrites `/home/hermes/.hermes/.env`, seeds `/home/hermes/.hermes/skills`, and manages `/home/hermes/.hermes/SOUL.md`. Local image validation imports the explicit `ghostship-hermes-image` bundle, so it exercises that path correctly.

The publish workflow diverged when it started optimizing GHCR publication around a reusable `ghostship-hermes-base` image plus an overlay bundle. That overlay carries package store paths and `/opt/ghostship-overlay`, but it is not the same artifact as the final NixOS image bundle. As a result, the published image can preserve the base image's upstream Hermes activation behavior while missing the repo-owned final runtime wiring.

## Goals / Non-Goals

**Goals:**
- Make the published `ghostship-hermes` image tags match the explicit `ghostship-hermes-image` contract.
- Preserve exact-repeat immutable image reuse so no-op republish runs can still retag an already-published final image.
- Keep the true-base image split intact without requiring the final GHCR tags to be assembled from the overlay path.

**Non-Goals:**
- Rework the internal Nix image split between `ghostship-hermes-base` and the final image module.
- Redesign the root bootstrap logic, env allowlist, or seed semantics themselves.
- Preserve the current overlay-based final publication path if it continues to produce a runtime-different artifact.

## Decisions

### Publish final GHCR tags from the explicit image bundle

The workflow will build and export `packages.<system>.ghostship-hermes-image` for the final architecture-specific tags and immutable content tags. This is the artifact the repo already documents and the one the smoke test imports locally, so using it for GHCR publication removes the contract split.

Alternative considered: keep the overlay-based final publish path and teach it to reconstruct the final NixOS runtime closure and system wiring. Rejected because it is more complex, more fragile, and recreates exactly the class of drift this bug exposed.

### Derive immutable final-image reuse from the explicit final artifact

The immutable final-image reuse key will be derived from the explicit publishable image artifact's derivation path instead of the pair of base-image and overlay-bundle derivations. This keeps the reuse optimization aligned with the actual shipped artifact.

Alternative considered: keep hashing the base and overlay derivations while adding extra guard logic. Rejected because it still treats a sidecar assembly path as the source of truth for the published image.

### Keep the reusable base image as a separate concern

The repo can continue to publish and document `ghostship-hermes-base` as its own reusable/base-validation artifact, but the final `ghostship-hermes` tags should no longer depend on reconstructing the publishable final image from that path.

Alternative considered: remove the base image entirely. Rejected because it is not necessary to fix the runtime-contract bug.

## Risks / Trade-offs

- [Cold publish time may increase when the final artifact changes] -> Mitigate by preserving immutable exact-repeat reuse for unchanged final-image artifacts.
- [Docs and workflow semantics can drift again if a future optimization bypasses the explicit image bundle] -> Mitigate by tightening the publication specs around the explicit final artifact and the managed runtime contract.
- [Maintainers may assume the base image still accelerates final GHCR publication directly] -> Mitigate by updating README language to separate base-image reuse from final-image publication semantics.

## Migration Plan

1. Update the publish workflow to export and publish `ghostship-hermes-image` for final tags.
2. Merge the change and run the publish workflow once on `main`.
3. Pull the new image on `chill-penguin` and verify `/home/hermes/.hermes/.env`, root-seeded skills, and seeded `SOUL.md` match the documented managed runtime contract.

## Open Questions

- None.
