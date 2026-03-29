# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Pinned Hermes release updated to `v2026.3.28`.

- Bootstrapped the `ghostship-hermes` flake and arm64 image layout.
- Added the first tested Python utility scaffold for SearXNG.
- Added runtime Hermes bootstrap logic based on the upstream manual install flow.
- Fixed the image rootfs so `/home/hermes` exists before the entrypoint runs.
- Added `gh` to the published tool bundle and arm64 image derivation evaluation to CI.
