## Context

The repo already separates operator tooling into two layers:

- a minimal immutable image layer for boot, supervision, dashboard/router services, and a small approved CLI exception set
- a managed Hermes-user tooling layer under `/home/hermes/.local/state/nix/profiles/ghostship-managed` for updateable operator commands

`blogtato` is a standalone Rust CLI RSS reader that exposes the `blog` command. It is not needed for container boot or managed service supervision, and adding it to the immutable layer would widen the documented default-image CLI policy. At the same time, the tool is useful enough that asking operators to install it manually would break the repo's goal of shipping a converged managed runtime toolchain.

This repo does not currently show an existing Rust packaging pattern under `packages/`, so the change needs to introduce one in a way that fits the flake-driven package graph and both supported image architectures.

## Goals / Non-Goals

**Goals:**
- Package `blogtato` declaratively in the repo's Nix graph.
- Expose `blog` from the managed Hermes-user profile after managed tooling convergence.
- Keep the immutable image CLI policy unchanged.
- Update runtime documentation and validation so the managed `blog` contract is explicit and testable.

**Non-Goals:**
- Adding `blogtato` to `environment.systemPackages` or the approved baked default-image CLI list.
- Creating a Ghostship wrapper around `blogtato`.
- Adding feed seeds, repo-managed subscriptions, or runtime bootstrap content for `blogtato`.
- Changing the managed npm tool contract; `blogtato` should come from Nix, not npm.

## Decisions

### 1. Package `blogtato` in-repo and install it through `managedUserPackages`

The change should create a dedicated Nix package for upstream `kantord/blogtato`, then add that package to the managed user-tooling convergence list in `packages/hermes-image/nixos-module.nix`.

Rationale:

- The repo already treats stable operator tools as managed-profile content when they are not boot-critical.
- This preserves the current immutable-image boundary while still making the tool available by default.
- Installing through the managed profile means image replacement and refresh convergence keep `blog` aligned with the currently declared runtime contract.

Alternatives considered:

- Add `blogtato` to the immutable image package set. Rejected because it unnecessarily broadens the baked CLI policy.
- Install via Cargo or a bootstrap script. Rejected because it creates a second package-management path outside the repo's Nix graph.

### 2. Keep the operator-facing contract on the existing managed PATH

The tool should resolve from the same managed Hermes-user PATH that already exposes `hermes`, `fd`, `uv`, `tmux`, and the Python environment.

Rationale:

- The existing runtime contract already says normal invocation should use the managed profile or managed npm prefix.
- No extra shell glue or symlink strategy is needed if the Nix profile installs the package directly.
- The user-facing behavior stays simple: after boot-time convergence, `blog` is just present.

Alternatives considered:

- Add a separate bespoke symlink or wrapper in `/home/hermes/.local/bin`. Rejected because the managed Nix profile already solves command projection and replacement cleanly.

### 3. Treat this as a runtime-contract change, not just a package addition

The change should update OpenSpec/runtime docs and add validation that exercises the `blog` command from the managed Hermes-user PATH.

Rationale:

- The repo has already learned that path presence alone is not a sufficient contract for managed runtime tools.
- `blog` is operator-facing tooling, so the behavior needs to be documented where the rest of the managed tool inventory is described.
- Validation should prove that the command resolves from the supported managed runtime layer and launches successfully with a non-destructive smoke command.

Alternatives considered:

- Add the package silently without spec/docs updates. Rejected because it would recreate policy drift between the runtime contract and the actual managed inventory.

## Risks / Trade-offs

- [Introducing the repo's first Rust CLI package may add new flake/package maintenance overhead] -> Keep the package narrow and use standard Nix Rust packaging primitives rather than inventing a custom workflow.
- [The upstream package may need cargo dependency hashing and periodic refreshes] -> Treat it like any other pinned repo-managed package and keep the package definition isolated under `packages/`.
- [Managed-profile growth can slowly blur the line between runtime tooling and a full workstation] -> Keep the change limited to `blogtato` itself and do not expand into seeded feeds, wrappers, or adjacent CLI bundles.
- [Validation that only checks command discovery could miss a broken binary] -> Add a command-level smoke test such as `blog --help` from the managed Hermes-user PATH.

## Migration Plan

1. Add a repo-local Nix package for `blogtato`.
2. Wire that package into the flake outputs and the managed user-tooling convergence path.
3. Update the managed runtime docs/specs to describe `blog` as managed tooling.
4. Extend runtime validation to exercise `blog` from the managed Hermes-user PATH.

Rollback strategy:

- Remove the package from the managed profile contract and flake outputs, then revert the docs/spec updates together.
- Because the tool lives in the managed profile rather than the immutable image, rollback remains a convergence-layer change instead of an image-boundary rollback.

## Open Questions

- None for the proposal scope. The main implementation detail is the concrete Nix Rust package definition, not the runtime contract direction.
