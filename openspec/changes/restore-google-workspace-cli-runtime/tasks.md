## 1. Package The CLI

- [x] 1.1 Add the pinned `googleworkspace/cli` flake input and expose `gws` through local per-system package wiring
- [x] 1.2 Add `gws` to the default Hermes image package set so it is available on `PATH` automatically
- [x] 1.3 Keep package and image evaluation working for both supported publish architectures

## 2. Align Docs And Policy

- [x] 2.1 Update `README.md` to describe Google Workspace support as a preinstalled CLI with no bundled skills
- [x] 2.2 Update `AGENTS.md` and `CHANGELOG.md` to reflect the restored `gws` package and the explicit no-skills policy

## 3. Verify The Runtime Contract

- [x] 3.1 Verify the repo flake evaluates the `gws` integration for the default image outputs on the supported systems
- [x] 3.2 Verify a built runtime exposes `gws` on `PATH` without seeding Google Workspace skills
