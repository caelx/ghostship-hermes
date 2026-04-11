## Context

The current publish pipeline is now correct, free-only, and GHCR-backed, but the first successful run after the architecture split still spends most of its time rebuilding two native images. The measured long pole is the base-image path, and the current workflow keys that base reuse to the raw Nix derivation path. That is too sensitive: overlay-only repo changes can perturb the derivation path and force a new base tag even when the slow-changing base payload is still identical. The repo already accepts internal publication architecture changes so long as downstream consumers still receive the same `ghostship-hermes` multi-arch tags and runtime metadata.

## Goals / Non-Goals

**Goals:**
- Reuse already published per-architecture base images when the tracked base payload is unchanged.
- Reuse already published immutable final architecture images when their evaluated content is unchanged.
- Keep the strategy free-only by using GHCR and existing GitHub workflow permissions rather than paid binary-cache services.
- Preserve the documented `ghostship-hermes` consumer contract and native multi-arch publication flow.
- Remove unnecessary base-image rebuilds from overlay-only publish runs and measure that distinction explicitly.

**Non-Goals:**
- Reducing the first cold-content publish to the 10-minute stretch goal by itself.
- Changing the consumer-facing mutable tag set or manifest semantics.
- Introducing a new paid cache backend, registry, or external state service.

## Decisions

### 1. Derive the reusable base-image tag from tracked base inputs

Each architecture leg will derive its reusable base tag from the tracked files that actually affect the slow-changing base payload rather than from the raw base-image derivation path. That keeps overlay-only repo changes from invalidating the published `ghostship-hermes-base` tag and forcing another native base build.

Alternatives considered:
- Keep deriving the base tag from `base_drv`: simpler, but it keeps forcing rebuilds whenever unrelated source changes perturb the derivation path.
- Split the NixOS image into even more layers first: potentially useful later, but it is a larger architectural change than needed to stop the immediate base rebuild churn.

### 2. Keep immutable final-image reuse on top of stable base reuse

If the immutable final image already exists, the workflow should still reuse it immediately. If it does not exist yet, the workflow should fall back to the now-stable per-architecture base image and only rebuild the final overlay assembly. This keeps the publication stack layered: final-image reuse first, stable base-image reuse second, native base rebuild last.

Alternatives considered:
- Drop immutable final-image reuse and rely only on stable base reuse: simpler, but it still pays the final Docker build and publication cost for exact repeats.

### 3. Measure base reuse separately from cold-content publishes

The workflow optimization note and change tasks should distinguish between cold-content publishes, overlay-only publishes that should reuse the base image, and exact repeats that should reuse the immutable final image. This prevents judging the base-reuse optimization against the wrong latency envelope.

Alternatives considered:
- Keep one aggregate publish metric only: simpler reporting, but it hides whether the stable base boundary is actually delivering value.

## Risks / Trade-offs

- [Base tag derivation is still too broad] -> Derive the base tag from an explicit tracked base-input set so overlay-only changes do not invalidate the reusable base image.
- [GHCR lookup or tag reuse semantics drift] -> Keep the mutable consumer-facing tags unchanged and use the immutable content tag only as an internal reuse key.
- [First-run publish time remains high] -> Treat this change as a base-boundary optimization and continue measuring the cold-content path separately.
- [Registry state grows with immutable images] -> Use compact content tags tied directly to evaluated derivations and rely on GHCR retention or future cleanup policy work if accumulation becomes material.

## Migration Plan

1. Add stable base-tag calculation to the publish workflow for each architecture from tracked base inputs.
2. Keep immutable final-image lookup before any rebuild work.
3. If the immutable final image is missing, check GHCR for the stable base image tag before starting a native base rebuild.
4. If the stable base tag exists, reuse it and rebuild only the final overlay assembly.
5. Record cold-content, base-reuse, and exact-repeat timing evidence after rollout.

Rollback strategy:
- Revert to derivation-based tags if the tracked-input base key proves unreliable, or remove the immutable final-image reuse check and return to the earlier base-image-only path if GHCR retag behavior proves unreliable.

## Open Questions

- How much improvement do we actually get on an overlay-only publish after the stable base key lands?
- How much warm-repeat improvement do we actually get on an immediate rerun of the same SHA after the stable base key lands?
- Does GHCR accumulation from immutable content tags warrant a later retention or garbage-collection change?
