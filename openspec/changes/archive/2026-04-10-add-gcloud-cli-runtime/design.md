## Context

The Hermes image already exposes a curated set of utilities through the repo's normal flake-driven package graph. Today that flow includes repo-owned `ghostship-*` CLIs, the upstream-pinned `gws` package, and `bws` from `nixpkgs`. The requested change is to add the Google Cloud CLI without introducing a second installation mechanism such as Google's tarball installer, apt repository setup, or bootstrap-time mutation.

The repo also has an explicit policy boundary around non-`ghostship-*` tools in the default image. That means this change is not just package wiring; it must also update the documented runtime contract so the implementation and policy stay aligned.

## Goals / Non-Goals

**Goals:**
- Ship `gcloud` in the default Hermes image so it is available on `PATH` automatically.
- Keep the integration inside the existing flake and image package-set flow.
- Align repo policy and docs with the new approved extra CLI.
- Keep the package wiring visible to normal flake evaluation for both supported publish architectures.

**Non-Goals:**
- Installing the Google Cloud CLI through Google's tarball installer, apt repository, or bootstrap scripts.
- Adding Ghostship-specific wrappers around `gcloud`.
- Managing Google Cloud authentication state beyond relying on the repo's persisted `/home/hermes` runtime model.
- Expanding scope to additional Google Cloud optional components unless they are already part of the selected `nixpkgs` package.

## Decisions

### Use `pkgs.google-cloud-sdk` from `nixpkgs`

The change should source `gcloud` from `nixpkgs` as `pkgs.google-cloud-sdk`, then add that package to the same `allUtilities` list that already feeds the image runtime `PATH`.

This matches the repo's existing declarative image-build model and avoids introducing a special-case external installer flow for one tool.

Alternative considered: install via Google's documented tarball or apt instructions. Rejected because those flows mutate the environment outside the flake, create a second dependency-management path, and make the image contract less reproducible.

### Keep the runtime contract CLI-only

The image should expose the packaged Google Cloud CLI and nothing more. The repo does not need a Ghostship-managed wrapper, special bootstrap logic, or service-side configuration model to make this useful.

Alternative considered: add a repo-owned helper wrapper or first-boot initialization step. Rejected because the current ask is only to make `gcloud` available in the image, and the existing persisted home model already gives the CLI a place to store operator state.

### Treat this as a policy-and-docs change as well as a package change

The implementation must update the repo's explicit approved-extra-CLI policy so `gcloud` is allowed alongside the currently documented exceptions.

Alternative considered: add the package quietly and leave the policy text unchanged. Rejected because it would immediately recreate spec and documentation drift.

## Risks / Trade-offs

- [Adding another non-`ghostship-*` CLI broadens the lean-runtime exception list] -> Keep the change narrow, document it explicitly, and avoid bundling related workstation tooling.
- [The `nixpkgs` package contents may differ from Google's installer defaults] -> Define the contract in terms of the packaged `gcloud` executable being present on `PATH`, not in terms of every optional upstream component.
- [Multi-arch image evaluation could regress if the package is not wired cleanly] -> Verify the package path through the repo's normal flake evaluation for both `x86_64-linux` and `aarch64-linux`.

## Migration Plan

1. Add `pkgs.google-cloud-sdk` to the utility package set that feeds the image runtime environment.
2. Update repo guidance and changelog entries to include `gcloud` in the approved default-image CLI set.
3. Verify flake evaluation and image package wiring on the supported architectures.
4. If rollback is needed, remove the package from the utility set and revert the policy/docs change together.

## Open Questions

- None at proposal time. The requested scope is narrow: package `gcloud` in the image through the repo's normal Nix wiring.
