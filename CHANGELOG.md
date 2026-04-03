# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Defined a repo-wide secrets/config policy: `BWS_ACCESS_TOKEN` remains the bootstrap secret, Bitwarden Secrets Manager is now the documented default source of truth for service and automation-compatible website credentials, local topology such as URLs and ports stays in env/config by default, and the docs and repo-managed skills now describe utility env vars as the runtime interface rather than the durable secret store.
- Fixed the Hermes runtime OpenSpec propose override to keep refreshed image instructions on `.worktrees/<name>/`, and removed the retired `brainstorming` skill from the curated workstation seed defaults shipped by the image.
- Made `scripts/validate_workstation_persistence.sh` executable again and added a fast Docker-daemon preflight so the documented local validation command fails immediately with a clear message when Docker is installed but unusable from the current shell, including common WSL integration setups.
- Pinned Hermes release updated to `v2026.4.3`.
- Fixed the workstation-seed derivation overlay to make the copied seed tree writable before replacing the OpenSpec Codex/Gemini/Opencode subtrees, resolving the `Permission denied` failure that broke the `ghostship-hermes-workstation-seed` CI and image builds.
- Kept the workstation image's OpenSpec `propose`, `apply`, and `archive` workflows aligned with the develop-environment overrides by sourcing the seeded Codex/Gemini/Opencode instruction trees from the repo-managed copies and reapplying the Ghostship override blocks after `openspec update` refreshes.
- Reframed the image as a Hermes-native persistent agent workstation: `HERMES_HOME=/opt/data` now matches upstream Hermes Docker behavior, `/opt/data/home` backs the symlinked persisted home facade under `/home/hermes`, `/workspace` is a separate persisted work-products mount, the steady-state runtime stays on a persisted `hermes` user `systemd` manager with the custom dashboard stack, and local Docker validation now proves that reused `/opt/data`, `/workspace`, and a safe persisted `/nix` mount survive restart/replacement.
- Added upstream `feed` as a pinned flake-managed image dependency, wired `FEED_DB_PATH` to profile-scoped Hermes storage under `$HERMES_HOME/feed/feed.db`, and added a repo-managed `feed` skill that pairs RSS-Bridge feed URL generation with durable RSS monitoring and triage workflows.
- Replaced the bundled Bitwarden Password Manager CLI `bw` with the Bitwarden Secrets Manager CLI `bws`, rewrote the repo `bitwarden` skill and docs around machine-account project secrets with default HOME-based config persistence via the `/opt/data/home` symlinked home tree, and added `ghostship-changedetection` with the mirrored stable upstream OpenAPI snapshot, full API CLI coverage, and a repo-managed changedetection workflow skill.
- Rewrote the repo-managed Hermes skill pack into workflow-oriented operator guides, keeping service skills short and trigger-rich around inspect, diagnose, mutate, and verify flows, preserving bespoke environment skills, and replacing the repo `agent-browser` skill with the upstream file unchanged.
- Added the upstream Google Workspace CLI `gws` as a pinned flake-managed image dependency, vendored the full upstream Google Workspace skill catalog into `vendor/googleworkspace-cli/skills`, exposed a combined `ghostship-hermes-skills` flake output for seeded defaults, rewrote `hermes-nix` to be explicitly flake-first, and documented narrow-scope Gmail auth guidance for dedicated testing-mode personal accounts.
- Fixed the GitHub Actions flake/image build regression by pinning `ghostship-flaresolverr` to the same `python311Packages` set as the shared `ghostship-cli-contract`, eliminating the Python 3.13 vs 3.11 package-set mismatch that broke `nix flake check` and image evaluation on GitHub.
- Standardized the `ghostship-*` CLI contract around exact snake_case API/client method names with no compatibility aliases, a shared `--timeout` flag with a `30` second default, consistent JSON error envelopes and exit codes, and `--dry-run` request rendering for write/delete operations.
- Expanded the remaining service CLIs to use the shared contract package, refreshed their package READMEs and skills, and updated the live suite to use the canonical commands.
- Added first-wave full-surface utilities for PriceBuddy and RSS-Bridge, including typed clients, CLI help/docs, RSS-Bridge feed URL generation, local `.envrc` stubs, new service skills, and initial live coverage with token-gated PriceBuddy write-path checks.
- Added a broad non-writing live integration suite under `tests/live/` for the deployed Ghostship services, fixed the Synology and Prowlarr client regressions it exposed, cached Grimmory bearer auth once per test session, and isolated Cloudflare Access headers behind test-only `GHOSTSHIP_TEST_CF_ACCESS_*` env vars so the runtime container does not depend on them.
- Fixed the scheduled Hermes release updater to authenticate GitHub API requests with `GITHUB_TOKEN`, avoiding anonymous release-API rate limit failures in GitHub Actions.
- Documented that Hermes' upstream Honcho support remains available against external Honcho instances without bundling a separate `honcho-ai` package in the image, while still lazily persisting the Honcho compatibility config under Hermes storage.
- Refined the Hermes profile dashboard branding by adding the upstream Hermes logo, bottom-aligning the `ghostship-hermes` wordmark beside it, renaming the gateway status labels to `Gateway On` and `Gateway Off`, and stopping the 5-second profile poll from reloading the active terminal iframe unnecessarily.
- Replaced the single public `ttyd` entrypoint with a Caddy dashboard that proxies same-origin per-profile Hermes terminals, and added a Docker integration test covering multiple profiles, iframe routing, and profile-scoped gateway startup.
- Stopped advertising `/nix` as an automatic Docker volume because mounting an empty volume over `/nix` on a fresh Nix-built image hides or copies the store and can stall container startup.
- Pinned Hermes to `v2026.3.30` so the container can use the upstream native profile model (`hermes profile ...`, `hermes -p ...`) for multi-agent routing.
- Added the repo-managed `hermes-nix`, `agent-browser`, and `current-environment` skills so Hermes can learn the container’s Nix-first workflow, CloakBrowser-only browser automation path, and persistence/runtime model from inside the image.
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
