# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Added direct Honcho support to the Hermes image by shipping the `honcho-ai` SDK in the container, enabling `hermes honcho ...` against external Honcho instances without extra host installs, persisting the Honcho compatibility config under Hermes storage, and documenting explicit env-first per-profile Honcho setup.
- Refined the Hermes profile dashboard branding by adding the upstream Hermes logo, bottom-aligning the `ghostship-hermes` wordmark beside it, renaming the gateway status labels to `Gateway On` and `Gateway Off`, and stopping the 5-second profile poll from reloading the active terminal iframe unnecessarily.
- Replaced the single public `ttyd` entrypoint with a Caddy dashboard that proxies same-origin per-profile Hermes terminals, and added a Docker integration test covering multiple profiles, iframe routing, and profile-scoped gateway startup.
- Stopped advertising `/nix` as an automatic Docker volume because mounting an empty volume over `/nix` on a fresh Nix-built image hides or copies the store and can stall container startup.
- Pinned Hermes to `v2026.3.30` so the container can use the upstream native profile model (`hermes profile ...`, `hermes -p ...`) for multi-agent routing.
- Added the repo-managed `hermes-nix`, `hermes-agent-browser`, and `current-environment` skills so Hermes can learn the container’s Nix-first workflow, CloakBrowser-only browser automation path, and persistence/runtime model from inside the image.
- Expanded the image bundle with common operator tools and debuggers, including `rg`, `jq`, `python`, `gh`, `tmux`, `procps`, `dnsutils`, `shellcheck`, `bats`, `fzf`, `entr`, and related utilities.
- Fixed the RomM and Grimmory CLIs to authenticate via their live login flows by default, while still accepting direct bearer token overrides.
- Fixed `ghostship-cloakbrowser` request URL construction and clarified that its auth token is a static server-side `AUTH_TOKEN`, not a generated session token.
- Added curated API/auth spec sheets for RomM, Grimmory/BookLore, and CloakBrowser Manager under `docs/api/`.
- Expanded `docs/api/` into a hybrid full-coverage API reference set for every `ghostship-*` utility, combining official raw specs with repo-owned companion and full reference sheets.
- Hardened Hermes bootstrap by creating `/tmp` before runtime setup and defaulting `SSL_CERT_FILE`/`NIX_SSL_CERT_FILE` to the system CA bundle for `git`, `uv`, and Nix tooling.
- Fixed Hermes bootstrap to install the package into the final runtime path instead of leaving editable launchers and imports pinned to the temporary build directory.
- Made the web terminal fall back to a live shell when Hermes is not configured yet, so pressing Enter no longer lands on a dead reconnect screen.
- Switched the Hermes container runtime to `s6`, with `ttyd` supervised as the default session and a polling gateway watcher that starts `hermes gateway run --replace` whenever messaging credentials appear in `~/.hermes/.env`.
- Expanded the README with `caelx` image links, Hermes CLI usage guidance, runtime layout notes, and tag documentation.
- Simplified the publish workflow so manifest tags and per-arch tags are published with the documented `latest`, `sha-<git-sha>`, and `hermes-<release>` naming scheme, with `buildx` explicitly configured before manifest creation and non-main manual runs limited to immutable `sha-*` tags.
- Bootstrapped the `ghostship-hermes` flake and arm64 image layout.
- Added the first tested Python utility scaffold for SearXNG.
- Added runtime Hermes bootstrap logic based on the upstream manual install flow.
- Fixed the image rootfs so `/home/hermes` exists before the entrypoint runs.
- Added `gh` to the published tool bundle and arm64 image derivation evaluation to CI.
