# Shared Nix Cache

This document is historical.

The current image publication path no longer builds and exports a NixOS image bundle. `ghostship-hermes` now publishes directly from `packages/hermes-image/Dockerfile` with Docker Buildx on `amd64` and `arm64`.

Nix still matters at runtime:

- the image ships userland Nix
- `/nix` is a required persisted mount when downstream expects user-installed Nix packages to survive container replacement

For current deployment guidance, use:

- [README.md](/home/nixos/dev/ghostship-hermes/README.md)
- [docs/workstation-image.md](/home/nixos/dev/ghostship-hermes/docs/workstation-image.md)
- [docs/runtime-env.md](/home/nixos/dev/ghostship-hermes/docs/runtime-env.md)
