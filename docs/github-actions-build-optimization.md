# GitHub Actions Build Notes

This document is historical.

The current CI and publish contract is:

- `ci.yml` keeps flake-evaluation and focused Python checks, then builds the Ubuntu workstation image from `packages/hermes-image/Dockerfile` and runs the smoke test.
- `ci.yml` uses Buildx GitHub Actions layer cache (`type=gha`) for the amd64 smoke-build path.
- `publish-image.yml` builds and pushes `linux/amd64` and `linux/arm64` directly from the Dockerfile, reusing and refreshing a per-architecture GHCR Buildx cache (`buildcache-amd64`, `buildcache-arm64`) before publishing the manifest list tags.

The old NixOS image-bundle and shared-cache optimization notes no longer describe the active publication path.
