## Why

The Hermes image already distinguishes between a minimal immutable system layer and a mutable managed Hermes-user tooling layer. `blogtato` fits the second category: it is useful operator tooling, but adding it to the baked image would broaden the repo's approved default-image CLI surface without a boot or supervision need.

Adding `blogtato` through the managed runtime keeps the runtime contract consistent while making the `blog` CLI available by default to Hermes sessions and interactive shells after managed tooling convergence.

## What Changes

- Add a repo-packaged `blogtato` derivation so the project can install the upstream Rust CLI declaratively through Nix.
- Extend the managed Hermes-user tooling profile to install `blogtato`, exposing the `blog` command from the dedicated managed Nix profile.
- Update managed-runtime documentation and validation to describe and verify `blog` as managed operator tooling rather than an immutable image-layer CLI.
- Keep the immutable image CLI policy unchanged; this change does not add `blogtato` to the baked default-image exception list.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `managed-runtime-tooling`: broaden the managed helper CLI contract so the managed Hermes-user profile installs and exposes `blog`.
- `agent-workstation-runtime`: broaden the normal invocation contract so `blog` resolves from the managed layered toolchain without requiring manual post-boot installation.

## Impact

- Affected code: `flake.nix`, `packages/` packaging for a new `blogtato` derivation, `packages/hermes-image/nixos-module.nix`, and runtime validation/docs such as `README.md`.
- Dependencies: one new upstream Rust CLI source (`kantord/blogtato`) packaged through the repo's Nix graph.
- Systems: managed user-tooling convergence, Hermes-user PATH behavior, image/runtime documentation, and runtime validation coverage.
