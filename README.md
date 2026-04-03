# ghostship-hermes

`ghostship-hermes` is a Nix-first monorepo for building and publishing the `caelx` Hermes container image. The image is a persistent agent workstation: it runs Hermes behind a Caddy dashboard on port `7681`, keeps `HERMES_HOME=/opt/data` to match upstream Hermes Docker behavior, exposes a persisted home facade through `/opt/data/home`, persists work products separately in `/workspace`, and keeps agent tooling current on boot and on timers.

Canonical image references:

- Pull ref: `ghcr.io/caelx/ghostship-hermes`
- GitHub package page: <https://github.com/caelx/ghostship-hermes/pkgs/container/ghostship-hermes>

## What This Image Changes

- Hermes is prepackaged in a container runtime instead of installed directly on the host.
- Caddy on port `7681` is the public interface. It serves a profile dashboard and reverse-proxies same-origin `ttyd` terminals for each Hermes profile.
- Hermes is bootstrapped at container start from the pinned upstream release in `packages/hermes-image/hermes-release.txt`.
- Hermes is installed into the final `/opt/data/hermes-agent` path during bootstrap so the generated launchers and imports do not depend on a temporary build directory.
- Repo-managed and vendored Hermes skills are seeded into `~/.hermes/skills` on first start without overwriting user-managed content.
- A repo-managed workstation seed mirrors the selected develop-environment defaults for `.agents`, Codex, Gemini CLI, Opencode, OpenSpec commands/skills, and user `systemd` units into persisted state under `/opt/data` and `/opt/data/home` without clobbering local edits.
- The seeded OpenSpec `propose`, `apply`, and `archive` workflows are sourced from the repo-managed Codex, Gemini CLI, and Opencode trees so the workstation image stays aligned with the develop-environment overrides.
- `/opt/data` is the canonical persisted Hermes volume. `/opt/data/home` backs the persisted home facade that is symlinked into `/home/hermes` on boot.
- Persist `/workspace` as a separate work-products volume for repos, downloads, build artifacts, and long-lived work items.
- Persist `/nix` as well if you want `nix build`, `nix shell`, and `nix profile install` outputs to survive container replacement. Use a safe pre-populated `/nix` mount such as a bind mount from an existing Nix host store, not a brand-new empty Docker volume over `/nix`.
- The runtime now uses a `hermes` user `systemd` manager. Caddy is still the only public web service, profile-specific `ttyd` terminals are generated dynamically for the default and named Hermes profiles, and agent tooling is updated on boot and on timers instead of on every invocation.
- `codex`, `gemini`, `opencode`, `openspec`, and `skills` are installed as normal workstation apps under the persisted home and updated with atomic versioned installs plus stable symlink flips in `~/.local/bin`.
- The runtime includes curated `ghostship-*` utilities so Hermes can call them from the same environment.
- The runtime includes upstream `feed` as the main persistent RSS reader and monitoring engine, with profile-scoped SQLite state under Hermes storage.
- The runtime includes the Bitwarden Secrets Manager CLI `bws` with a repo-managed Bitwarden skill, a persistent config file at `/home/hermes/.hermes/bws/config`, and Hermes-managed state under `/home/hermes/.hermes/bws/state` for machine-account secret retrieval.
- The runtime also includes the upstream Google Workspace CLI `gws`, packaged from a pinned flake input and paired with a broad vendored Google Workspace skill set.
- Upstream Hermes Honcho support remains available for connecting Hermes to an external Honcho instance, but the image no longer bundles a separate `honcho-ai` package.

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
- `ghostship-changedetection`: full changedetection.io watch, tag, notification, import, history, and live-spec automation
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
  --volume ghostship-hermes-data:/opt/data \
  --volume ghostship-hermes-workspace:/workspace \
  --volume /nix:/nix \
  ghcr.io/caelx/ghostship-hermes:latest
```

If you want Nix-built software and user profiles to survive container replacement as well, reuse a persistent `/nix` mount that already contains the image store and profile state. Do not start by hiding `/nix` behind a brand-new empty Docker volume.

After the container starts:

1. Open `http://localhost:7681`.
2. The dashboard opens the default Hermes profile in a same-origin iframe backed by a private `ttyd` session.
3. If Hermes is not configured yet, that profile falls back to a shell so the browser terminal still stays live instead of showing a dead reconnect prompt.
4. For first-time provider or gateway setup, open a separate shell and run `docker exec -it ghostship-hermes bash -lc 'hermes setup'`.
5. Create additional Hermes profiles with `docker exec -it ghostship-hermes bash -lc 'hermes profile create coder --clone'`. The dashboard picks them up automatically without restarting the container.
6. Return to the dashboard and switch between profiles from the left-hand panel.

The workstation model is:

- persist `/opt/data` always
- persist `/workspace` always
- persist `/nix` when you want Nix-installed utilities and build outputs to survive container replacement
- let boot-time and timer-driven jobs update mutable workstation state in the background
- keep normal agent invocations local and cached

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

`hermes gateway` remains available for upstream compatibility, but this image uses the Caddy dashboard and profile `ttyd` terminals as the default browser-facing interface. For persistent messaging gateways, prefer Hermes' upstream `gateway install` flow from inside the profile terminal. The workstation keeps a real user `systemd` manager with units persisted through `/opt/data/home/.config/systemd/user`, so profile-scoped gateway services can live in persisted state like the rest of the workstation. For the full current command inventory, use the upstream CLI reference linked below.

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
- **Hermes**: Installed into the durable workstation home from a pinned upstream release
- **Interface**: Caddy on port `7681` serves a profile dashboard and same-origin proxied `ttyd` terminals
- **Persistence**: `/opt/data` is the Hermes state root, `/opt/data/home` stores the persisted home-dotdir facade that gets symlinked into `/home/hermes`, `/workspace` is the separate persisted work/projects volume, and `/nix` should also be persisted when you want Nix-managed installs and build outputs to survive container replacement
- **Runtime Model**: A systemd-based NixOS container bootstraps storage, then starts both system services and a persisted `hermes` user manager so `~/.config/systemd/user` survives under `/opt/data/home/.config/systemd/user`
- **Updates**: `codex`, `gemini`, `opencode`, `openspec`, `skills`, global `skills.sh` skills, Gemini extensions, OpenSpec instruction trees with the Ghostship `propose`/`apply`/`archive` overrides reapplied after refresh, and opencode's generated OpenRouter free-model config are refreshed on boot and on timers while preserving the last working local state on failures
- **Bootstrap Resilience**: Bootstrap creates `/tmp` and defaults `SSL_CERT_FILE`/`NIX_SSL_CERT_FILE` to `/etc/ssl/certs/ca-bundle.crt` so bootstrap `git`, `uv`, npm, and Nix operations inherit a working CA bundle
- **Tooling**: Comprehensive bundle including `git`, `curl`, `uv`, `nix`, `bws`, `feed`, `gws`, `rg`, `jq`, `python`, `gh`, `tmux`, `procps`, `dnsutils`, `shellcheck`, `bats`, `systemd`, and more
- **Output Standard**: All `ghostship-` utilities output native JSON. Use `--pretty` for human-readable output.

## Local Validation

Use the repo validation script to prove the workstation model locally against a reused home directory:

```bash
scripts/validate_workstation_persistence.sh
```

The script requires a working Docker daemon from the current shell. On WSL 2, enable Docker Desktop integration for this distro first.

The script builds the runtime/seed outputs, seeds a fresh workstation home, updates the managed agent apps, generates the opencode programming-model cache, installs a Nix profile package, reruns the boot seeding against the same home, and verifies that the local edit, Hermes state, app links, generated config, and Nix profile still work.

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
| `ghostship-changedetection` | `CHANGEDETECTION_URL`, `CHANGEDETECTION_API_KEY` |
| `ghostship-rss-bridge` | `RSS_BRIDGE_URL` |

Canonical API references for every `ghostship-*` utility now live in [docs/api/README.md](docs/api/README.md), using raw upstream specs where available and repo-owned full reference sheets everywhere else.

All `ghostship-*` CLIs now follow one contract: dedicated commands mirror the underlying client/API method names exactly in snake_case, generic passthrough (`request` or `call`) is only the escape hatch for uncovered endpoints, every invocation accepts `--timeout` with a default hard timeout of `30` seconds, and write/delete commands expose `--dry-run` to print the exact request object without touching the remote service.

## Bitwarden Secrets Manager CLI

The image ships the official Bitwarden Secrets Manager CLI as `bws` from nixpkgs. It is available directly on `PATH`, and its normal HOME-based config/state locations persist because the relevant home directories are symlinked into `/opt/data/home`.

Inside the container, use `bws` directly:

```fish
set -x BWS_ACCESS_TOKEN <machine-account-access-token>

bws project list
bws secret list <project-id>
bws secret get <secret-id>
```

If the account uses a self-hosted Bitwarden server, set the server URL before the first request:

```fish
set -x BWS_SERVER_URL https://vault.example.com
```

The repo-managed `bitwarden` skill now assumes Secrets Manager semantics only: machine-account access tokens, projects, and secrets. It does not use `bw`, `BW_SESSION`, Password Manager item retrieval, or shared-collection vault flows.

## changedetection.io CLI

The image ships `ghostship-changedetection` for the full stable upstream changedetection.io API surface, plus the unauthenticated live merged `/api/v1/full-spec` endpoint.

Use `bws` to materialize the service secrets, then call the typed utility:

```fish
set -x CHANGEDETECTION_URL (bws secret get <changedetection-url-secret-id> | jq -r '.value')
set -x CHANGEDETECTION_API_KEY (bws secret get <changedetection-api-key-secret-id> | jq -r '.value')

ghostship-changedetection get_system_info --pretty
ghostship-changedetection list_watches --pretty
ghostship-changedetection get_full_api_spec --pretty
```

All stable upstream endpoints have dedicated snake_case wrappers. Use `request` only for future or deployment-specific parameters that are not covered by a dedicated command yet.

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

- `bitwarden`: how to authenticate with `bws`, list projects and secrets, and export service credentials from Bitwarden Secrets Manager
- `changedetection`: how to fetch changedetection credentials from `bws` and run the full inspect, `--dry-run`, mutate, and verify workflow with `ghostship-changedetection`
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
5. Build the flake-exposed Bitwarden Secrets Manager CLI package: `nix build .#bws`
6. Build the flake-packaged changedetection CLI: `nix build .#ghostship-changedetection`
7. Build the flake-packaged `feed` CLI: `nix build .#feed`
8. Build the flake-packaged Google Workspace CLI: `nix build .#gws`
9. Build the combined seeded skill tree: `nix build .#packages.x86_64-linux.ghostship-hermes-skills`
10. Build the image: `nix build .#packages.x86_64-linux.ghostship-hermes-image`

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
