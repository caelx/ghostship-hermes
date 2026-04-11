## Context

The repo has two distinct image assembly stories:

- the explicit `ghostship-hermes-image` bundle, which wraps the full final NixOS rootfs tarball and is consumed by local export/test flows
- the faster GitHub publication architecture, which historically built a reusable base image once and then layered the repo-owned overlay bundle on top

The previous fix moved the GitHub final-image path back to the explicit bundle because the overlay-based final image had drifted from the managed bootstrap contract. That corrected correctness, but it also removed the practical benefit of the true-base split during content publishes because `ghostship-hermes-image` depends on the full final tarball.

The underlying problem for this regression is narrower: the workflow stopped using the layered publish path that the base split was designed to accelerate. The full `ghostship-hermes-image` bundle is still the right explicit local artifact, but it is too expensive to use as the GitHub publication path when the goal is to reuse the already-published base layer.

## Goals / Non-Goals

**Goals:**
- Restore base-plus-overlay acceleration for non-reused GitHub content publishes.
- Make the GitHub content build explicitly resolve and build from the reusable `BASE_REF` tag.
- Keep the explicit `ghostship-hermes-image` bundle as the documented external contract for local export and test flows.

**Non-Goals:**
- Rework the flake outputs so `ghostship-hermes-image` itself becomes a layered artifact.
- Remove the reusable base image or the overlay bundle.
- Rework the repo's existing dashboard or persistence validation suites as part of this speed fix.

## Decisions

### Keep the explicit external artifact contract and optimize the GitHub internals separately

The repo will continue to document `ghostship-hermes-image` as the explicit publishable artifact contract, while the GitHub publish workflow regains a faster internal assembly path using `ghostship-hermes-base` plus `ghostship-hermes-overlay-bundle`.

Alternative considered: redefine `ghostship-hermes-image` itself as a layered bundle and route every local/test workflow through that new format. Rejected for now because it is a larger artifact-contract change than needed to recover the GitHub optimization.

### Make the layered GitHub path consume the reusable base tag directly

The workflow will keep the fast content path in GitHub by resolving or publishing `BASE_REF`, pulling that exact tag, and then building the final architecture image from `ghostship-hermes-overlay-bundle` with `BASE_IMAGE=${BASE_REF}`. That keeps the speed benefit tied to the reusable base artifact instead of falling back to the full final rootfs export path.

Alternative considered: keep using `ghostship-hermes-image` in GitHub and accept the extra publish latency. Rejected because it defeats the base-layer split during every non-reused content publish.

## Risks / Trade-offs

- [The workflow still has two image stories: the explicit local bundle and the faster GitHub layered path] -> Mitigate by documenting that distinction explicitly and keeping the immutable content hash tied to the actual layered publish inputs.
- [A GHCR pull could briefly lag right after publishing a new base tag] -> Mitigate by making the content step pull `BASE_REF` with retries before starting the overlay build.

## Migration Plan

1. Restore the GitHub content-image build step to the base-plus-overlay assembly path.
2. Make the content step pull and build from `BASE_REF` explicitly before publishing the layered image.
3. Merge the change and compare the next GitHub publish timing against the current regression baseline.

## Open Questions

- None.
