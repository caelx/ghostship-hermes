# GitHub Actions Build Notes

This document is historical.

The current CI and publish contract is:

- `ci.yml` keeps flake-evaluation and Python utility checks, then builds the Ubuntu workstation image from `packages/hermes-image/Dockerfile` and runs the smoke test.
- `publish-image.yml` builds and pushes `linux/amd64` and `linux/arm64` directly from the Dockerfile and publishes the manifest list tags.

The old NixOS image-bundle and shared-cache optimization notes no longer describe the active publication path.
