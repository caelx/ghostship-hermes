## Context

The current publish pipeline is now correct, free-only, and GHCR-backed, but the first successful run after the architecture split still spends most of its time rebuilding two native images. That first-run cost is acceptable when the actual image content changes, but it is wasteful for repeated publish validations, reruns, and workflow-only republishes where the evaluated base image and overlay bundle are unchanged. The repo already accepts internal publication architecture changes so long as downstream consumers still receive the same `ghostship-hermes` multi-arch tags and runtime metadata.

## Goals / Non-Goals

**Goals:**
- Reuse already published immutable architecture images when their evaluated content is unchanged.
- Keep the strategy free-only by using GHCR and existing GitHub workflow permissions rather than paid binary-cache services.
- Preserve the documented `ghostship-hermes` consumer contract and native multi-arch publication flow.
- Make the warm-repeat publish path materially faster than the cold-content publish path and measure that distinction explicitly.

**Non-Goals:**
- Reducing the first cold-content publish to the 10-minute stretch goal by itself.
- Changing the consumer-facing mutable tag set or manifest semantics.
- Introducing a new paid cache backend, registry, or external state service.

## Decisions

### 1. Use content-addressed immutable final-image tags in GHCR

Each architecture leg will derive an immutable content tag from the evaluated base-image derivation and overlay-bundle derivation, then check GHCR for that tag before rebuilding. If the tag already exists, the workflow may safely retag that immutable image into the normal architecture publish tags without repeating the build.

Alternatives considered:
- Rebuild on every publish and rely only on base-image reuse: simpler, but it still pays the overlay build and image publication cost for identical content.
- Use GitHub Actions cache for final-image reuse: free, but too vulnerable to repository-wide cache throttling and eviction for these large native image jobs.

### 2. Keep base-image reuse as the second fallback layer

If the immutable final image does not exist yet, the workflow should still reuse the already published per-architecture base image when possible. This keeps the publication stack layered: final-image reuse first, base-image reuse second, native rebuild last.

Alternatives considered:
- Skip the base-image layer once final-image reuse exists: lower complexity, but it throws away a useful fallback when only the overlay content changes.

### 3. Measure warm-repeat publish behavior separately from cold-content publishes

The workflow optimization note and change tasks should distinguish between cold-content publishes, which must still do the expensive native build work, and warm-repeat publishes, which are expected to collapse mostly into registry lookups plus retagging. This prevents judging the repeat-publish optimization against the wrong latency envelope.

Alternatives considered:
- Keep one aggregate publish metric only: simpler reporting, but it hides whether the repeat-publish optimization is actually delivering value.

## Risks / Trade-offs

- [Immutable content tag derivation is incomplete] -> Derive the tag from both the base-image and overlay-bundle derivations so the workflow only reuses images when the publish-relevant evaluated content matches.
- [GHCR lookup or tag reuse semantics drift] -> Keep the mutable consumer-facing tags unchanged and use the immutable content tag only as an internal reuse key.
- [First-run publish time remains high] -> Treat this change as a warm-repeat optimization and continue measuring the cold-content path separately.
- [Registry state grows with immutable images] -> Use compact content tags tied directly to evaluated derivations and rely on GHCR retention or future cleanup policy work if accumulation becomes material.

## Migration Plan

1. Add immutable content-tag calculation to the publish workflow for each architecture.
2. Check GHCR for an existing immutable image before starting any rebuild work.
3. If found, retag the immutable image into the standard architecture tags and continue to manifest publication.
4. If not found, fall back to the existing base-image reuse plus native final-image build path.
5. Record cold-content and warm-repeat publish timing evidence after rollout.

Rollback strategy:
- Remove the immutable final-image reuse check and return to the base-image-only reuse path if GHCR lookup or retag behavior proves unreliable.

## Open Questions

- How much warm-repeat improvement do we actually get on an immediate rerun of the same SHA?
- Does GHCR accumulation from immutable content tags warrant a later retention or garbage-collection change?
