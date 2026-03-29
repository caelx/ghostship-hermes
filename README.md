# ghostship-hermes

`ghostship-hermes` is a Nix-first monorepo for building and publishing the `caelx` Hermes container image. The image runs Hermes behind `ttyd` on port `7681`, seeds repo-managed skills on first start, persists Hermes state in `/home/hermes/.hermes` and `/nix`, and bundles repo-owned `ghostship-*` utilities for agent-friendly operator workflows.

Canonical image references:

- Pull ref: `ghcr.io/caelx/ghostship-hermes`
- GitHub package page: <https://github.com/caelx/ghostship-hermes/pkgs/container/ghostship-hermes>

## What This Image Changes

- Hermes is prepackaged in a container runtime instead of installed directly on the host.
- `ttyd` on port `7681` is the default interface, so the primary v1 workflow is browser-to-terminal rather than a messaging gateway.
- Hermes is bootstrapped at container start from the pinned upstream release in `packages/hermes-image/hermes-release.txt`.
- Repo-managed skills are seeded into `~/.hermes/skills` on first start without overwriting user-managed content.
- Hermes state is persisted in `/home/hermes/.hermes`, and `/nix` is mounted separately so ad hoc `nix shell` usage survives container restarts.
- The runtime includes curated `ghostship-*` utilities so Hermes can call them from the same environment.

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

## Getting Started

### Running the Image

```bash
docker run \
  --rm \
  --name ghostship-hermes \
  --publish 7681:7681 \
  --volume ghostship-hermes-home:/home/hermes/.hermes \
  --volume ghostship-hermes-nix:/nix \
  ghcr.io/caelx/ghostship-hermes:latest
```

After the container starts:

1. Open `http://localhost:7681`.
2. The browser session opens directly into Hermes inside tmux.
3. For first-time provider or gateway setup, open a separate shell and run `docker exec -it ghostship-hermes bash -lc 'hermes setup'`.
4. Return to the browser session and keep chatting there, or use `/model` in-session and `hermes model` from an exec shell whenever you want to switch providers or models.

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

`hermes gateway` remains available for upstream compatibility, but this image uses `ttyd` as the default browser-facing interface. If you do want to use upstream messaging workflows, run `hermes gateway setup` or `hermes gateway start` from inside the running container. For the full current command inventory, use the upstream CLI reference linked below.

## Hermes Docs

The upstream Hermes documentation still applies to CLI behavior and features inside this image:

- <https://hermes-agent.nousresearch.com/docs/>
- <https://hermes-agent.nousresearch.com/docs/user-guide/cli>
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
- **Interface**: `ttyd` on port `7681` launches the default Hermes session
- **Persistence**: `/home/hermes/.hermes` and `/nix` are mounted as volumes
- **Bootstrap Resilience**: The entrypoint creates `/tmp` and defaults `SSL_CERT_FILE`/`NIX_SSL_CERT_FILE` to `/etc/ssl/certs/ca-bundle.crt` so bootstrap `git`, `uv`, and Nix operations inherit a working CA bundle
- **Tooling**: Comprehensive bundle including `git`, `curl`, `uv`, `nix`, etc.
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

Canonical API references for every `ghostship-*` utility now live in [docs/api/README.md](docs/api/README.md), using raw upstream specs where available and repo-owned full reference sheets everywhere else.

## Skills

Default skills are stored in `skills/` and seeded into the Hermes runtime `~/.hermes/skills` on first start without overwriting user-managed content. Each skill document provides detailed instructions for Hermes on how to use the corresponding CLI utility.

## Local Development

1. Enter the shell: `direnv allow`
2. Lock a utility: `python3 scripts/python_utility.py lock packages/<utility>-cli`
3. Test a utility: `python3 scripts/python_utility.py test packages/<utility>-cli`
4. Build a utility: `python3 scripts/python_utility.py build packages/<utility>-cli`

## Security

- Runs as non-root `hermes` user.
- No in-container `sudo`.
- Secrets should be provided via mounted `.env` or environment variables.
