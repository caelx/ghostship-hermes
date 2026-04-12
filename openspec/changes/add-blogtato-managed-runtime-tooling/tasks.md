## 1. Package blogtato

- [ ] 1.1 Add a repo-local Nix package for upstream `kantord/blogtato` under `packages/` with pinned source and cargo dependency metadata.
- [ ] 1.2 Expose the `blogtato` package through `flake.nix` so it evaluates on the supported Linux architectures.

## 2. Wire blogtato into the managed runtime

- [ ] 2.1 Add `blogtato` to the managed Hermes-user tooling convergence path in `packages/hermes-image/nixos-module.nix`.
- [ ] 2.2 Verify the managed Hermes-user PATH contract continues to source `blog` from the managed Nix profile without expanding the immutable image package set.

## 3. Update docs and validation

- [ ] 3.1 Update runtime docs to describe `blog` as managed Hermes-user tooling rather than a baked image CLI.
- [ ] 3.2 Extend runtime validation or smoke coverage to execute a non-destructive `blog` command from the managed Hermes-user PATH.
