# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Fixed the RomM and Grimmory CLIs to authenticate via their live login flows by default, while still accepting direct bearer token overrides.
- Fixed `ghostship-cloakbrowser` request URL construction and clarified that its auth token is a static server-side `AUTH_TOKEN`, not a generated session token.
- Added curated API/auth spec sheets for RomM, Grimmory/BookLore, and CloakBrowser Manager under `docs/api/`.
- Expanded `docs/api/` into a hybrid full-coverage API reference set for every `ghostship-*` utility, combining official raw specs with repo-owned companion and full reference sheets.
- Hardened Hermes bootstrap by creating `/tmp` before runtime setup and defaulting `SSL_CERT_FILE`/`NIX_SSL_CERT_FILE` to the system CA bundle for `git`, `uv`, and Nix tooling.
- Pinned Hermes release updated to `v2026.3.28`.
- Expanded the README with `caelx` image links, Hermes CLI usage guidance, runtime layout notes, and tag documentation.
- Simplified the publish workflow so manifest tags and per-arch tags are published with the documented `latest`, `sha-<git-sha>`, and `hermes-<release>` naming scheme, with `buildx` explicitly configured before manifest creation and non-main manual runs limited to immutable `sha-*` tags.
- Bootstrapped the `ghostship-hermes` flake and arm64 image layout.
- Added the first tested Python utility scaffold for SearXNG.
- Added runtime Hermes bootstrap logic based on the upstream manual install flow.
- Fixed the image rootfs so `/home/hermes` exists before the entrypoint runs.
- Added `gh` to the published tool bundle and arm64 image derivation evaluation to CI.
