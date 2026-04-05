## Context

The current `publish-image` workflow runs a two-entry matrix on `ubuntu-24.04` for both `x86_64-linux` and `aarch64-linux`. The amd64 leg succeeds, but the arm64 leg attempts to build true `aarch64-linux` Nix derivations on an x86 runner and fails with `required system or feature not available`. The repo already documents the intended rule: x86 hosts may evaluate arm64 derivations, but full arm64 builds belong on arm64 runners.

The workflow should therefore be corrected to match the repo contract instead of trying to stretch Docker QEMU or Nix `extra-platforms` past what they actually guarantee. The publish stage itself is not the problem; it already consumes explicit per-architecture artifacts and assembles manifest tags correctly once both artifacts exist.

## Goals / Non-Goals

**Goals:**
- Make `publish-image` produce amd64 and arm64 artifacts on environments that can actually build each target system.
- Preserve the explicit `ghostship-hermes-image` bundle contract and the existing publish-stage tag assembly.
- Keep x86-only validation lightweight by evaluating arm64 wiring instead of attempting full arm64 builds where that cannot succeed.
- Align workflow behavior, docs, and maintainer expectations around one cross-architecture publication contract.

**Non-Goals:**
- Redesign the image artifact format or replace the existing export/publish helper flow.
- Change image metadata, entrypoint, runtime volumes, or GHCR tag naming.
- Introduce emulation-first arm64 publication as the primary release path.
- Expand the scope into broader CI refactors unrelated to image publication.

## Decisions

### Use native execution environments for each published architecture

The publish workflow should map `x86_64-linux` builds to an x86 Linux runner and `aarch64-linux` builds to an arm64-capable runner or configured arm64 builder.

Rationale:
- the failing job shows the current x86-hosted arm64 build path is not executable
- the repo already expects native arm64 infrastructure for full arm64 builds
- this keeps the workflow honest about what it is validating and publishing

Alternative considered:
- keep the current x86 runner and rely on QEMU plus `extra-platforms`. Rejected because that combination does not satisfy native `aarch64-linux` Nix build requirements for this image build.

### Keep the explicit publishable artifact contract unchanged

The workflow should continue to produce the existing publishable `ghostship-hermes-image` bundle per architecture, upload both artifacts, and let the publish job assemble tags and manifests from those artifacts.

Rationale:
- the current explicit artifact contract is already captured in the spec and working for amd64
- the failure is in where the arm64 build runs, not in the publishable artifact shape
- minimizing artifact-format churn reduces release risk and keeps existing helpers valid

Alternative considered:
- replace the artifact contract while fixing the runner problem. Rejected because it mixes an infrastructure correction with an unrelated artifact change.

### Treat arm64 evaluation and arm64 builds as different CI responsibilities

PR and x86-only validation paths should keep arm64 checks at `nix eval` or equivalent wiring validation, while full arm64 image builds should occur only on executable arm64 infrastructure.

Rationale:
- this matches the repo's documented guidance and the local reproduction of the failure
- it keeps fast validation paths available on x86 hosts without pretending to prove full arm64 buildability
- it makes the publication workflow, not ad hoc x86 emulation, the authoritative arm64 release path

Alternative considered:
- make every workflow attempt full arm64 builds. Rejected because it would keep failing on x86-only environments and would slow down validation unnecessarily even after the publish fix.

## Risks / Trade-offs

- [Risk] Native arm64 GitHub Actions capacity or runner label availability could vary. -> Mitigation: choose a supported arm64 runner label or documented arm64 builder configuration and keep the workflow logic explicit about that dependency.
- [Risk] Splitting architecture execution can make the workflow YAML more verbose than the current two-entry matrix. -> Mitigation: keep artifact names and publish-stage inputs stable so the complexity stays localized to the build jobs.
- [Risk] Maintainers may still try local x86 full arm64 builds and misread the failure as an image regression. -> Mitigation: update docs to state clearly that x86 hosts use `nix eval` for arm64 wiring and arm64 infrastructure for full builds.

## Migration Plan

1. Update the publish workflow to map each target system to an execution environment that can build it.
2. Remove workflow settings that imply x86-hosted emulation is sufficient for native arm64 Nix image builds.
3. Keep the publish job consuming the same per-architecture artifact names so GHCR publication logic remains stable.
4. Refresh README and changelog guidance so maintainers understand the arm64 runner requirement and the x86 `nix eval` fallback.
5. Validate the workflow structure and run the next publication on `main` to confirm both architecture artifacts are produced.

Rollback:
- restore the previous publish workflow mapping if the chosen arm64 runner path proves unavailable
- keep the artifact contract unchanged so rollback stays limited to workflow infrastructure

## Open Questions

- Should the repo standardize on a GitHub-hosted arm64 runner label, or leave room for an equivalent self-hosted or remote-builder arm64 path if availability or minutes become a constraint?
- Do we want the publish workflow to fail immediately with an explicit preflight message when no arm64-capable execution environment is configured, or is queued-job failure sufficient?
