# ghostship-hermes

`ghostship-hermes` is a Nix-first monorepo for building and publishing an arm64 OCI image that runs Hermes behind `ttyd`, ships a curated operator tool bundle, seeds repo-managed default skills, and hosts specialized API-wrapper utilities under the `ghostship-` prefix.

## Overview

This repository provides a unified environment for running Hermes with a pre-configured set of CLI utilities for popular self-hosted applications and services. All utilities are designed to be agent-friendly, outputting native JSON by default.

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

## Architecture

- **Base Image**: Stable NixOS (`nixos-25.11`)
- **Hermes**: Installed at container runtime from pinned upstream release
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
| `ghostship-romm` | `ROMM_URL`, `ROMM_TOKEN` |
| `ghostship-nzbget` | `NZBGET_URL`, `NZBGET_USER`, `NZBGET_PASS` |
| `ghostship-qbittorrent` | `QBITTORRENT_URL`, `QBITTORRENT_USER`, `QBITTORRENT_PASS` |
| `ghostship-grimmory` | `GRIMMORY_URL`, `GRIMMORY_TOKEN` |
| `ghostship-tautulli` | `TAUTULLI_URL`, `TAUTULLI_API_KEY` |
| `ghostship-bazarr` | `BAZARR_URL`, `BAZARR_API_KEY` |
| `ghostship-synology` | `SYNOLOGY_URL`, `SYNOLOGY_USER`, `SYNOLOGY_PASS`, `SYNOLOGY_VERIFY_SSL` |
| `ghostship-flaresolverr` | `FLARESOLVERR_URL` |
| `ghostship-pyload-ng` | `PYLOAD_URL`, `PYLOAD_USER`, `PYLOAD_PASS` |
| `ghostship-cloakbrowser` | `CLOAKBROWSER_URL`, `CLOAKBROWSER_TOKEN` |

## Skills

Default skills are stored in `skills/` and seeded into the Hermes runtime `~/.hermes/skills` on first start. Each skill document provides detailed instructions for Hermes on how to use the corresponding CLI utility.

## Getting Started

### Local Development

1. Enter the shell: `direnv allow`
2. Lock a utility: `python3 scripts/python_utility.py lock packages/<utility>-cli`
3. Test a utility: `python3 scripts/python_utility.py test packages/<utility>-cli`
4. Build a utility: `python3 scripts/python_utility.py build packages/<utility>-cli`

### Running the Image

```bash
docker run \
  --rm \
  --publish 7681:7681 \
  --volume ghostship-hermes-home:/home/hermes/.hermes \
  --volume ghostship-hermes-nix:/nix \
  ghcr.io/<owner>/ghostship-hermes:latest
```

## Security

- Runs as non-root `hermes` user.
- No in-container `sudo`.
- Secrets should be provided via mounted `.env` or environment variables.
