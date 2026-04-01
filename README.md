# ghostship-hermes

`ghostship-hermes` is a Nix-first monorepo for building and publishing the `caelx` Hermes container image. The image runs Hermes behind a Caddy dashboard on port `7681`, seeds repo-managed skills on first start, persists Hermes state in `/home/hermes/.hermes` and `/nix`, and bundles repo-owned `ghostship-*` utilities plus a curated operator toolchain for agent-friendly workflows.

Canonical image references:

- Pull ref: `ghcr.io/caelx/ghostship-hermes`
- GitHub package page: <https://github.com/caelx/ghostship-hermes/pkgs/container/ghostship-hermes>

## What This Image Changes

- Hermes is prepackaged in a container runtime instead of installed directly on the host.
- Caddy on port `7681` is the public interface. It serves a profile dashboard and reverse-proxies same-origin `ttyd` terminals for each Hermes profile.
- Hermes is bootstrapped at container start from the pinned upstream release in `packages/hermes-image/hermes-release.txt`.
- Hermes is installed into the final `/home/hermes/.hermes/hermes-agent` path during bootstrap so the generated launchers and imports do not depend on a temporary build directory.
- Repo-managed skills are seeded into `~/.hermes/skills` on first start without overwriting user-managed content.
- Hermes state is persisted in `/home/hermes/.hermes`, and `/nix` is mounted separately so ad hoc `nix shell` usage survives container restarts.
- The runtime is supervised by `s6`: Caddy is the only public web service, profile-specific `ttyd` terminals are created dynamically for the default and named Hermes profiles, profile-specific gateways start automatically when messaging credentials appear, and unconfigured profiles fall back to a shell instead of a dead reconnect screen.
- The runtime includes curated `ghostship-*` utilities so Hermes can call them from the same environment.
- Upstream Hermes Honcho support is available in the container out of the box for connecting Hermes to an external Honcho instance, with the `honcho-ai` SDK available to Hermes and env-first configuration preferred for container use.

## Overview

This repository provides a unified environment for running Hermes with a pre-configured set of CLI utilities for popular self-hosted applications and services. All utilities are designed to be agent-friendly and output native JSON by default.

### Implemented Utilities

- `ghostship-searxng`: Web search via SearXNG
- `ghostship-sonarr`: TV series management
- `ghostship-radarr`: Movie management
- `ghostship-prowlarr`: Indexer management and search
- `ghostship-plex`: Plex Media Server management
- `ghostship-romm`: ROM library management (v4.7.0+ API)
- `ghostship-nzbget`: NZBGet download management
- `ghostship-qbittorrent`: qBittorrent transfer management
- `ghostship-grimmory`: Book library management
- `ghostship-tautulli`: Plex monitoring and history
- `ghostship-bazarr`: Subtitle management
- `ghostship-synology`: Synology File Station management (search, mkdir, rm, etc.)
- `ghostship-flaresolverr`: Cloudflare protection bypass
- `ghostship-cloakbrowser`: CloakBrowser profile management
- `ghostship-pricebuddy`: typed PriceBuddy product, source, store, and tag automation
- `ghostship-rss-bridge`: typed RSS-Bridge discovery, schema inspection, feed URL generation, and wrapped display fetching

## Getting Started

### Running the Image

```bash
docker run \
  --rm \
  --name ghostship-hermes \
  --publish 7681:7681 \
  --volume ghostship-hermes-home:/home/hermes/.hermes \
  ghcr.io/caelx/ghostship-hermes:latest
```

After the container starts:

1. Open `http://localhost:7681`.
2. The dashboard opens the default Hermes profile in a same-origin iframe backed by a private `ttyd` session.
3. If Hermes is not configured yet, that profile falls back to a shell so the browser terminal still stays live instead of showing a dead reconnect prompt.
4. For first-time provider or gateway setup, open a separate shell and run `docker exec -it ghostship-hermes bash -lc 'hermes setup'`.
5. Create additional Hermes profiles with `docker exec -it ghostship-hermes bash -lc 'hermes profile create coder --clone'`. The dashboard picks them up automatically without restarting the container.
6. Return to the dashboard and switch between profiles from the left-hand panel.

`/nix` is part of the intended persistent runtime model, but do not blindly mount an empty Docker volume over `/nix` on a fresh Nix-built image. That hides or forces Docker to copy the image’s Nix store. If you need `/nix` persistence, use a deployment strategy that keeps the existing store available rather than replacing `/nix` with an empty volume.

### Profiles Dashboard

- `/` serves the Caddy dashboard.
- `/profiles/default/` serves the default Hermes profile terminal.
- `/profiles/<slug>/` serves a named profile terminal through the same origin.
- Profile routes stay private behind Caddy; the individual `ttyd` backends bind only to loopback inside the container.
- Hermes profile discovery follows the upstream layout:
  - default profile: `~/.hermes`
  - named profiles: `~/.hermes/profiles/<name>`
- Profile commands use upstream Hermes behavior:
  - `hermes profile create coder`
  - `hermes profile create research --clone`
  - `hermes -p coder chat`
  - `hermes profile list`

## Honcho

- `hermes honcho ...` is available in the container without extra host setup, but it connects to an external Honcho instance rather than running a local Honcho daemon in this image.
- Honcho is not active by default. It only becomes active after you actually configure it in a profile with `HONCHO_API_KEY`, optional `HONCHO_BASE_URL`, and optional `HONCHO_ENVIRONMENT`, or by writing a profile-local `honcho.json`.
- Prefer environment variables in the relevant Hermes profile `.env` so each Hermes profile can opt in independently.
- Profile-local Honcho config can live at `HERMES_HOME/honcho.json`, which persists with each Hermes profile under `~/.hermes`.
- The legacy compatibility path `~/.honcho/config.json` is also persisted under Hermes storage at `~/.hermes/shared/honcho/config.json`, but it is created lazily only when compatibility state exists and is kept as a fallback rather than the primary configuration path.

## Hermes Usage

The image includes the upstream Hermes CLI and its common subcommands. Common commands from the upstream README include:

```text
hermes
hermes model
hermes tools
hermes config set
hermes gateway
hermes setup
hermes claw migrate
hermes update
hermes doctor
```

Common shared slash commands from the upstream README include:

```text
/new
/reset
/model
/personality
/retry
/undo
/compress
/usage
/insights
/skills
/platforms
```

`hermes gateway` remains available for upstream compatibility, but this image uses the Caddy dashboard and profile `ttyd` terminals as the default browser-facing interface. The container runs a background watcher under `s6` that starts `hermes gateway run --replace` automatically for each profile once that profile’s messaging credentials are present, so you only need to run `hermes gateway setup` when you actually want messaging enabled. For the full current command inventory, use the upstream CLI reference linked below.

## Hermes Docs

The upstream Hermes documentation still applies to CLI behavior and features inside this image:

- <https://hermes-agent.nousresearch.com/docs/>
- <https://hermes-agent.nousresearch.com/docs/user-guide/cli>
- <https://hermes-agent.nousresearch.com/docs/user-guide/profiles/>
- <https://hermes-agent.nousresearch.com/docs/user-guide/messaging>
- <https://hermes-agent.nousresearch.com/docs/reference/cli-commands>

## Image Tags

The published manifest list and per-architecture image tags follow the same naming scheme. CI builds on push and pull request; GHCR pushes the full mutable tag set only from `main`, while manual `workflow_dispatch` runs on non-main refs publish only immutable `sha-*` tags.

- Manifest tags:
  - `latest`
  - `sha-<git-sha>`
  - `hermes-<release>`
- Per-arch tags:
  - `latest-amd64`
  - `latest-arm64`
  - `sha-<git-sha>-amd64`
  - `sha-<git-sha>-arm64`
  - `hermes-<release>-amd64`
  - `hermes-<release>-arm64`

## Architecture

- **Base Image**: Stable NixOS (`nixos-25.11`)
- **Hermes**: Installed at container runtime from a pinned upstream release
- **Interface**: Caddy on port `7681` serves a profile dashboard and same-origin proxied `ttyd` terminals
- **Persistence**: `/home/hermes/.hermes` is the safe default Docker volume; `/nix` persistence is deployment-specific because replacing `/nix` with an empty Docker volume hides or copies the image’s Nix store
- **Bootstrap Resilience**: The entrypoint creates `/tmp` and defaults `SSL_CERT_FILE`/`NIX_SSL_CERT_FILE` to `/etc/ssl/certs/ca-bundle.crt` so bootstrap `git`, `uv`, and Nix operations inherit a working CA bundle
- **Tooling**: Comprehensive bundle including `git`, `curl`, `uv`, `nix`, `rg`, `jq`, `python`, `gh`, `tmux`, `procps`, `dnsutils`, `shellcheck`, `bats`, and more
- **Output Standard**: All `ghostship-` utilities output native JSON. Use `--pretty` for human-readable output.

## Python Utility Workflow

For the standardized Python utility workflow, see [docs/python-utilities.md](docs/python-utilities.md).

### Conventions

- **Native JSON**: Utilities MUST output native JSON to stdout.
- **Pretty Printing**: All utilities support `--pretty` for formatted JSON.
- **Environment Config**: Utilities use environment variables (e.g., `SONARR_API_KEY`, `PLEX_TOKEN`) for configuration.
- **No Rich Formatting**: Human-readable tables and colors are avoided in favor of raw data.

## Environment Variables

All `ghostship-` utilities require specific environment variables. Set these before running commands.

| Utility | Variables |
|---------|------------|
| `ghostship-searxng` | `SEARXNG_URL` |
| `ghostship-sonarr` | `SONARR_URL`, `SONARR_API_KEY` |
| `ghostship-radarr` | `RADARR_URL`, `RADARR_API_KEY` |
| `ghostship-prowlarr` | `PROWLARR_URL`, `PROWLARR_API_KEY` |
| `ghostship-plex` | `PLEX_URL`, `PLEX_TOKEN` |
| `ghostship-romm` | `ROMM_URL`, `ROMM_USERNAME`, `ROMM_PASSWORD` or `ROMM_TOKEN` |
| `ghostship-nzbget` | `NZBGET_URL`, `NZBGET_USER`, `NZBGET_PASS` |
| `ghostship-qbittorrent` | `QBITTORRENT_URL`, `QBITTORRENT_USER`, `QBITTORRENT_PASS` |
| `ghostship-grimmory` | `GRIMMORY_URL`, `GRIMMORY_USERNAME`, `GRIMMORY_PASSWORD` or `GRIMMORY_TOKEN` |
| `ghostship-tautulli` | `TAUTULLI_URL`, `TAUTULLI_API_KEY` |
| `ghostship-bazarr` | `BAZARR_URL`, `BAZARR_API_KEY` |
| `ghostship-synology` | `SYNOLOGY_URL`, `SYNOLOGY_USER`, `SYNOLOGY_PASS`, `SYNOLOGY_VERIFY_SSL` |
| `ghostship-flaresolverr` | `FLARESOLVERR_URL` |
| `ghostship-pyload-ng` | `PYLOAD_URL`, `PYLOAD_USER`, `PYLOAD_PASS` |
| `ghostship-cloakbrowser` | `CLOAKBROWSER_URL`, optional `CLOAKBROWSER_TOKEN` matching manager `AUTH_TOKEN` |
| `ghostship-pricebuddy` | `PRICEBUDDY_URL`, `PRICEBUDDY_TOKEN` |
| `ghostship-rss-bridge` | `RSS_BRIDGE_URL` |

Canonical API references for every `ghostship-*` utility now live in [docs/api/README.md](docs/api/README.md), using raw upstream specs where available and repo-owned full reference sheets everywhere else.

## Skills

Default skills are stored in `skills/` and seeded into the Hermes runtime `~/.hermes/skills` on first start without overwriting user-managed content. In addition to service-specific skills, the image now ships:

- `hermes-nix`: how to run missing tools, do `nix profile` user installs, and rebuild repo tools without root
- `hermes-agent-browser`: how to use `agent-browser` only through CloakBrowser-backed profiles
- `current-environment`: how the Caddy dashboard, `ttyd`, `s6`, persistence, and safe self-restart behavior work in this container

## Local Development

1. Enter the shell: `direnv allow`
2. Lock a utility: `python3 scripts/python_utility.py lock packages/<utility>-cli`
3. Test a utility: `python3 scripts/python_utility.py test packages/<utility>-cli`
4. Build a utility: `python3 scripts/python_utility.py build packages/<utility>-cli`

## Live Integration Tests

The repo also includes a read-only live integration suite for the deployed Ghostship services:

```bash
nix develop -c python -m pytest tests/live/test_live_services.py -q
```

Notes:

- Keep `.envrc` local-only; it is intentionally ignored by Git.
- The live harness sources `.envrc` directly and maps any local `CF_ACCESS_CLIENT_ID` / `CF_ACCESS_CLIENT_SECRET` values into test-only `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID` / `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET` env vars for subprocesses. The runtime container does not depend on those headers.
- The suite is non-writing by policy for the existing utilities. The new `ghostship-pricebuddy` live coverage is allowed to create, update, and delete disposable test resources when `PRICEBUDDY_TOKEN` is configured.
- `ghostship-rss-bridge` live coverage remains read-only because the upstream service is action-driven and does not persist feed objects server-side.

## Security

- Runs as non-root `hermes` user.
- No in-container `sudo`.
- Secrets should be provided via mounted `.env` or environment variables.
- Runtime UID/GID is configurable with `HERMES_UID` and `HERMES_GID`; mounted volumes should be writable by the chosen identity.
