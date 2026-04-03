# ghostship-hermes

`ghostship-hermes` is a Nix-first monorepo for building and publishing the `caelx` Hermes container image. The image runs Hermes behind a Caddy dashboard on port `7681`, seeds repo-managed and vendored skills on first start, persists Hermes state in `/home/hermes/.hermes` and `/nix`, and bundles repo-owned `ghostship-*` utilities plus a curated operator toolchain for agent-friendly workflows.

Canonical image references:

- Pull ref: `ghcr.io/caelx/ghostship-hermes`
- GitHub package page: <https://github.com/caelx/ghostship-hermes/pkgs/container/ghostship-hermes>

## What This Image Changes

- Hermes is prepackaged in a container runtime instead of installed directly on the host.
- Caddy on port `7681` is the public interface. It serves a profile dashboard and reverse-proxies same-origin `ttyd` terminals for each Hermes profile.
- Hermes is bootstrapped at container start from the pinned upstream release in `packages/hermes-image/hermes-release.txt`.
- Hermes is installed into the final `/home/hermes/.hermes/hermes-agent` path during bootstrap so the generated launchers and imports do not depend on a temporary build directory.
- Repo-managed and vendored skills are seeded into `~/.hermes/skills` on first start without overwriting user-managed content.
- Hermes state is persisted in `/home/hermes/.hermes`, and `/nix` is mounted separately so ad hoc `nix shell` usage survives container restarts.
- The runtime is supervised by `s6`: Caddy is the only public web service, profile-specific `ttyd` terminals are created dynamically for the default and named Hermes profiles, profile-specific gateways start automatically when messaging credentials appear, and unconfigured profiles fall back to a shell instead of a dead reconnect screen.
- The runtime includes curated `ghostship-*` utilities so Hermes can call them from the same environment.
- The runtime includes upstream `feed` as the main persistent RSS reader and monitoring engine, with profile-scoped SQLite state under Hermes storage.
- The runtime includes the official Bitwarden CLI `bw` with a repo-managed Bitwarden skill and a persistent appdata directory under `/home/hermes/.hermes/bitwarden-cli` for env-driven secret retrieval.
- The runtime also includes the upstream Google Workspace CLI `gws`, packaged from a pinned flake input and paired with a broad vendored Google Workspace skill set.
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

Additional bundled upstream tools include:

- `feed`: persistent RSS subscription, fetch, search, and triage engine for Hermes workflows

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
- **Tooling**: Comprehensive bundle including `git`, `curl`, `uv`, `nix`, `bw`, `feed`, `gws`, `rg`, `jq`, `python`, `gh`, `tmux`, `procps`, `dnsutils`, `shellcheck`, `bats`, and more
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

All `ghostship-*` CLIs now follow one contract: dedicated commands mirror the underlying client/API method names exactly in snake_case, generic passthrough (`request` or `call`) is only the escape hatch for uncovered endpoints, every invocation accepts `--timeout` with a default hard timeout of `30` seconds, and write/delete commands expose `--dry-run` to print the exact request object without touching the remote service.

## Bitwarden CLI

The image ships the official Bitwarden CLI as `bw` from nixpkgs. It is available directly on `PATH`, and the runtime defaults `BITWARDENCLI_APPDATA_DIR` to `/home/hermes/.hermes/bitwarden-cli` so local Bitwarden CLI state persists with Hermes.

Inside the container, use `bw` directly:

```fish
bw status --response
```

For a dedicated agent account, inject the login secrets through the environment and use the official noninteractive flow:

```fish
set -x BW_CLIENTID <client-id>
set -x BW_CLIENTSECRET <client-secret>
set -x BW_PASSWORD <master-password>

bw login --apikey --nointeraction
set -x BW_SESSION (bw unlock --passwordenv BW_PASSWORD --raw --nointeraction)
bw sync --session "$BW_SESSION" --response
```

Use shared collections to deliver credentials to the dedicated agent account, then sync before reading newly shared items:

```fish
bw list collections --response --session "$BW_SESSION"
bw list items --collectionid <collection-id> --response --session "$BW_SESSION"
bw get item <item-id> --response --session "$BW_SESSION"
bw get password <item-id-or-uri> --raw --session "$BW_SESSION"
```

If the account uses a self-hosted Bitwarden server, configure it once before login:

```fish
bw config server https://vault.example.com
```

When the session is no longer needed:

```fish
bw lock
set -e BW_SESSION
```

## Google Workspace CLI

The image ships the upstream Google Workspace CLI as `gws`, built from the repo flake through the pinned `googleworkspace/cli` input. The vendored skill snapshot that matches that CLI lives under `vendor/googleworkspace-cli/skills/`, with pinned source metadata in `vendor/googleworkspace-cli/source.json`.

Inside the container, use `gws` directly:

```fish
gws --help
gws gmail +triage
```

Use the repo flake only when maintaining or verifying the packaged integration from the repository checkout:

```fish
nix build .#gws
nix build .#packages.x86_64-linux.ghostship-hermes-skills
```

For a dedicated agent Gmail account, prefer a narrow-scope login instead of the broad preset:

```fish
gws auth login -s gmail
gws auth login -s gmail,calendar,drive
```

If the Google OAuth app is still in testing mode and the account is a personal `@gmail.com` address, avoid the upstream `recommended` preset. Google can reject the consent flow when too many scopes are requested from an unverified app. Use only the scopes the agent actually needs.

You can also provide credentials non-interactively:

```fish
set -x GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE /home/hermes/.config/gws/credentials.json
gws gmail +triage
```

When refreshing this integration, update the pinned flake input and the vendored `vendor/googleworkspace-cli/skills/` snapshot together so the seeded skills stay aligned with the packaged CLI.

## Feed CLI

The image ships upstream `feed` as the main persistent RSS reader and monitoring utility. The runtime defaults `FEED_DB_PATH` to `$HERMES_HOME/feed/feed.db`, so each Hermes profile gets its own durable feed database under Hermes-managed storage.

Inside the container, use `feed` directly:

```fish
feed get stats
feed get entries --limit 25
feed search "ai agents"
```

To monitor a source through RSS-Bridge, build or discover the canonical feed URL first, then store it in `feed`:

```fish
ghostship-rss-bridge find_feed https://example.com
feed add feed <rss-or-rss-bridge-url>
feed get feeds
```

`ghostship-rss-bridge` remains the feed URL generation layer; `feed` is the durable subscription, fetch, search, and triage layer.

## Skills

Default skills are sourced from the repo-local `skills/` tree and the vendored `vendor/googleworkspace-cli/skills/` tree, then seeded into the Hermes runtime `~/.hermes/skills` on first start without overwriting user-managed content.

The repo-managed Ghostship pack treats service skills as short operator workflows instead of flat command catalogs: each service skill is written around inspect, diagnose, mutate, and verify sequences with trigger-rich descriptions and passthrough guidance only when the typed CLI does not cover an endpoint.

The local Ghostship skills continue to cover container-specific guidance:

In addition to the service-specific skills, the image ships:

- `bitwarden`: how to authenticate with the official `bw` client, sync shared collections, and retrieve shared credentials with env-driven sessions
- `feed`: how to turn direct or RSS-Bridge-generated feed URLs into durable monitored sources, scan unread entries, search history, and read full posts
- `hermes-nix`: how to choose between one-off `nix shell` usage, durable `nix profile` installs, and repo/image rebuilds without root
- `agent-browser`: the upstream browser automation skill copied through unchanged for general browser control workflows
- `current-environment`: how the Caddy dashboard, `ttyd`, `s6`, persistence, and safe container recovery behavior work here

When browser automation needs container-specific setup, pair the upstream `agent-browser` skill with the repo `cloakbrowser` and `current-environment` skills for profile lifecycle and runtime constraints.

The vendored Google Workspace set adds the upstream `gws-*` service skills plus the upstream persona and recipe skills for Gmail, Drive, Calendar, Docs, Sheets, and related workflows.

## Local Development

1. Enter the shell: `direnv allow`
2. Lock a utility: `python3 scripts/python_utility.py lock packages/<utility>-cli`
3. Test a utility: `python3 scripts/python_utility.py test packages/<utility>-cli`
4. Build a utility: `python3 scripts/python_utility.py build packages/<utility>-cli`
5. Build the flake-exposed Bitwarden CLI package: `nix build .#bw`
6. Build the flake-packaged `feed` CLI: `nix build .#feed`
7. Build the flake-packaged Google Workspace CLI: `nix build .#gws`
8. Build the combined seeded skill tree: `nix build .#packages.x86_64-linux.ghostship-hermes-skills`
9. Build the image: `nix build .#packages.x86_64-linux.ghostship-hermes-image`

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
