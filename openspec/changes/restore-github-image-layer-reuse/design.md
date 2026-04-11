## Context

The repo has two distinct image assembly stories:

- the explicit `ghostship-hermes-image` bundle, which wraps the full final NixOS rootfs tarball and is consumed by local export/test flows
- the faster GitHub publication architecture, which historically built a reusable base image once and then layered the repo-owned overlay bundle on top

The previous fix moved the GitHub final-image path back to the explicit bundle because the overlay-based final image had drifted from the managed bootstrap contract. That corrected correctness, but it also removed the practical benefit of the true-base split during content publishes because `ghostship-hermes-image` depends on the full final tarball.

The underlying problem is not that layered publication is impossible. The problem is that the workflow lacked a verification step tied to the exact image it was publishing. That let the fast internal path drift silently from the runtime contract while local tests continued to validate a different artifact.

## Goals / Non-Goals

**Goals:**
- Restore base-plus-overlay acceleration for non-reused GitHub content publishes.
- Verify the exact image built by the GitHub fast path before it is pushed to GHCR.
- Keep the explicit `ghostship-hermes-image` bundle as the documented external contract for local export and test flows.

**Non-Goals:**
- Rework the flake outputs so `ghostship-hermes-image` itself becomes a layered artifact.
- Remove the reusable base image or the overlay bundle.
- Turn the heavy GitHub publish workflow into a full local-equivalence test suite with live provider dependencies.

## Decisions

### Keep the explicit external artifact contract and optimize the GitHub internals separately

The repo will continue to document `ghostship-hermes-image` as the explicit publishable artifact contract, while the GitHub publish workflow regains a faster internal assembly path using `ghostship-hermes-base` plus `ghostship-hermes-overlay-bundle`.

Alternative considered: redefine `ghostship-hermes-image` itself as a layered bundle and route every local/test workflow through that new format. Rejected for now because it is a larger artifact-contract change than needed to recover the GitHub optimization.

### Verify the exact GitHub-built image before publication

The workflow will run a dedicated runtime-contract smoke test against the already-built `ghostship-hermes:ci-<arch>` image before copying it to GHCR. The test will focus on the managed bootstrap contract that previously drifted: root `.env` rewriting, root skill seeding, root `SOUL.md` seeding, and the presence of the repo-owned managed bootstrap units.

Alternative considered: rely on the existing local `ghostship-hermes-image` smoke test as proof that the layered GitHub image is equivalent. Rejected because that validates a different build path and is exactly how the earlier drift escaped.

### Keep the GitHub smoke test provider-independent

The publish-path verification will avoid router/provider inventory assertions so the workflow can validate the managed bootstrap contract without needing external model-provider secrets or live remote dependencies.

Alternative considered: reusing the full dashboard/router smoke test in publish-image. Rejected because it couples publication to provider credentials and network-dependent runtime behavior that are not necessary to prove the bootstrap/seed/env contract.

## Risks / Trade-offs

- [The new smoke test could still miss a future layered/runtime drift outside the bootstrap contract] -> Mitigate by centering it on the specific contract that previously drifted and expanding it when new layered-only regressions are discovered.
- [The workflow regains some complexity by separating external artifact contract from internal publication path] -> Mitigate by documenting that distinction explicitly and enforcing it through the publish-side smoke test.
- [A lightweight runtime-contract test adds some time back to the publish workflow] -> Mitigate by keeping it provider-independent and much narrower than the full dashboard smoke test.

## Migration Plan

1. Restore the GitHub content-image build step to the base-plus-overlay assembly path.
2. Add a publish-path smoke test that runs against the exact built image before `skopeo copy`.
3. Merge the change and compare the next GitHub publish timing against the current regression baseline.

## Open Questions

- None.
