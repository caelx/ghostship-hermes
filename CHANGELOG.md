# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Pinned Hermes release updated to `v2026.3.28`.
- Expanded the README with `caelx` image links, Hermes CLI usage guidance, runtime layout notes, and tag documentation.
- Simplified the publish workflow so manifest tags and per-arch tags are published with the documented `latest`, `sha-<git-sha>`, and `hermes-<release>` naming scheme, with `buildx` explicitly configured before manifest creation and non-main manual runs limited to immutable `sha-*` tags.
- Bootstrapped the `ghostship-hermes` flake and arm64 image layout.
- Added the first tested Python utility scaffold for SearXNG.
- Added runtime Hermes bootstrap logic based on the upstream manual install flow.
- Fixed the image rootfs so `/home/hermes` exists before the entrypoint runs.
- Added `gh` to the published tool bundle and arm64 image derivation evaluation to CI.
