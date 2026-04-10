## Context

The default image already bakes in a small immutable runtime layer plus a larger managed user-facing tool surface. In the current implementation, `git`, `nodejs`, and `ripgrep` are exposed through the shared image/runtime wiring, while `gh` and the OpenSSH client tools are absent from the default PATH. The repo also keeps a policy distinction between approved extra CLIs that are intentionally present in the default image and fast-moving tools that should remain outside the immutable image layer.

This change is small in code size but cross-cuts three surfaces:
- the image/runtime package wiring in the NixOS module
- the default-image capability contract in OpenSpec
- operator/runtime policy documentation that names which extra CLIs are approved in the image

## Goals / Non-Goals

**Goals:**
- Make `gh`, `ssh`, and `scp` available in the default Hermes image without requiring runtime installation.
- Keep the implementation aligned with the repo's existing Nix/image wiring patterns.
- Keep the policy/docs synchronized with the actual baked image contract.
- Preserve the current decision to leave Chromium and ffmpeg out of the image.

**Non-Goals:**
- Introducing a general-purpose expansion of the default immutable package set.
- Changing how fast-moving CLIs such as Codex or Opencode are managed.
- Adding browser runtimes, media tooling, or other unrelated operator utilities.
- Reworking the image architecture, entrypoint, or profile bootstrap flow.

## Decisions

### Add `gh` and `openssh` through the existing image/runtime package lists

The image should expose `gh` and `openssh` through the same NixOS-module package wiring that already projects default runtime tools onto PATH. This keeps the tools available both to service-managed workflows and to interactive admin/debug shells without introducing a separate install path or bootstrap side effect.

Alternatives considered:
- Install `gh` and OpenSSH through the mutable user-managed layer.
  Rejected because these are core admin/debug tools that should be present immediately on first boot and should not depend on a networked convergence step.
- Add them only to the dev shell.
  Rejected because the ask is specifically about the runtime image contract, not local development ergonomics.

### Treat this as an explicit image capability, not an undocumented side effect

The change should create a dedicated spec for `gh`, `ssh`, and `scp`, mirroring the existing pattern used for `gcloud` and `gws`. That keeps future image-policy decisions legible and testable.

Alternatives considered:
- Fold the entire change into `agent-workstation-runtime` without a dedicated capability.
  Rejected because that broader spec is about runtime layering behavior, and a dedicated tool-contract spec is clearer for future maintenance.

### Keep the immutable runtime layer still intentionally narrow

Adding `gh` and `openssh` should be described as a targeted exception for approved admin CLIs, not a reversal of the broader minimum-system-layer policy. The design should preserve the distinction between a narrow baked image contract and the wider mutable/user-managed tool surface.

Alternatives considered:
- Reframe the image as the primary home for most user-facing tooling.
  Rejected because that would conflict with the current managed-runtime direction and would widen this change far beyond the request.

## Risks / Trade-offs

- [Policy drift between docs and image wiring] → Update the runtime policy/docs in the same change so the approved extra-CLI list matches the actual image contract.
- [Ambiguity around which package list owns PATH exposure] → Implement through the existing shared runtime/image package wiring rather than inventing a separate package projection path.
- [Future image bloat through one-off additions] → Scope the spec and proposal narrowly to `gh` and OpenSSH client tools, and explicitly keep Chromium and ffmpeg out of scope.

## Migration Plan

1. Add `gh` and `openssh` to the default image/runtime package wiring.
2. Update the runtime policy/docs to include them in the approved default-image CLI set.
3. Add or update verification that the built image/runtime exposes `gh`, `ssh`, and `scp` on PATH.
4. Roll back by removing the package wiring and reverting the corresponding spec/doc updates if the added tools prove problematic.

## Open Questions

- Whether the implementation should place `gh` and `openssh` only in the fallback/user-facing runtime package set or also in the smaller immutable `systemPackages` set can be decided during apply, as long as the final PATH contract remains explicit and testable.
