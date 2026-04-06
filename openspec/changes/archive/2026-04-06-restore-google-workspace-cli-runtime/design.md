## Context

The repo already has a live `google-workspace-cli-runtime` spec that describes a pinned `gws` package on the default image `PATH`, but the implementation and docs were later moved back to a lean runtime that removed `gws`. At the same time, the live `google-workspace-skills` spec still describes vendored upstream skills and first-start seeding, which conflicts with the current repo invariant that the image must not ship Ghostship-managed default skills or preinstalled `skills`.

The user intent is narrower than the older archived Google Workspace change: ship `gws` automatically in the image, but do not vendor, seed, or otherwise surface Google Workspace skills. The design therefore needs to restore the CLI package without reintroducing the earlier workstation-style skill catalog.

## Goals / Non-Goals

**Goals:**
- Restore `gws` in the default Hermes image as a pinned upstream flake package.
- Keep the image/runtime contract CLI-only, with no vendored Google Workspace skill tree.
- Make the repo specs and documentation agree on that CLI-only integration.
- Keep the package visible through normal flake evaluation and image wiring on supported systems.

**Non-Goals:**
- Vendoring upstream Google Workspace skills, personas, or recipes.
- Seeding any Google Workspace skills into `~/.hermes/skills` or another default skill tree.
- Adding Ghostship-specific wrappers around `gws`.
- Reintroducing workstation-layer defaults such as `skills`, `codex`, or related agent tooling.

## Decisions

### Use the upstream flake package directly for the CLI

The repo will add `googleworkspace/cli` as a pinned flake input and bind `packages.${system}.gws` into the local package graph. This keeps the integration declarative and matches the repo's current image build pattern.

Alternative considered: install `gws` through `npm` or a release tarball. Rejected because it creates a second packaging path outside the flake and weakens reproducibility.

### Keep Google Workspace integration strictly CLI-only

The image will expose only the `gws` executable. No vendored upstream skills, no repo-managed Google Workspace skill snapshot, and no runtime seeding step will be part of this change.

Alternative considered: revive the archived combined CLI-plus-skills design. Rejected because it conflicts with the current runtime policy and expands scope well beyond the requested outcome.

### Resolve the spec drift by narrowing the skills contract, not by deleting Google Workspace integration entirely

The active specs should continue to describe the intended steady state. `google-workspace-cli-runtime` will remain the runtime contract for the packaged CLI, while `google-workspace-skills` will be rewritten to state that the default image/runtime does not include Google Workspace skills.

Alternative considered: remove the skills spec entirely. Rejected because the repo already has an active capability name for this concern, and an explicit negative contract is clearer than silent absence.

### Keep image availability automatic through the existing package-set path

`gws` should enter the same package set that the Hermes image already projects onto the runtime `PATH`, rather than being added through a one-off activation hook or post-build mutation.

Alternative considered: install `gws` during bootstrap or first start. Rejected because it would make availability depend on mutable runtime state rather than the built image contents.

## Risks / Trade-offs

- [Restoring `gws` weakens the current lean-runtime exclusion list] -> Keep the exception narrow and document that it is CLI-only, not a broader tool-bundle rollback.
- [Upstream `googleworkspace/cli` package shape may change] -> Pin the upstream flake revision and wire it through explicit local package bindings.
- [The old skills spec could continue to confuse future maintainers] -> Replace it with explicit no-skills requirements in this change rather than leaving the older behavior implied.
- [Multi-arch packaging could fail if the upstream CLI package is not available for one system] -> Verify both supported system package bindings during implementation and keep the current arm64 evaluation expectations in mind.

## Migration Plan

1. Add the pinned upstream `googleworkspace/cli` flake input and expose `gws` through local per-system packages.
2. Add `gws` to the default Hermes image package set so it is present on the runtime `PATH`.
3. Update docs and repo guidance to describe Google Workspace support as CLI-only.
4. Replace the old Google Workspace skills requirements with explicit no-skills requirements.
5. Verify image/package evaluation and runtime availability on the supported architectures.
6. If rollback is needed, remove the flake input and image package wiring while keeping the no-skills contract intact.

## Open Questions

- None at proposal time. The main decision is scope, and the requested scope is clear: package the CLI, exclude the skills.
