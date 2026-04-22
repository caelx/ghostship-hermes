# ghostship-hermes

`ghostship-hermes` builds and publishes `ghcr.io/caelx/ghostship-hermes`, an Ubuntu 24.04 Hermes workstation image with:

- upstream Hermes `0.9` dashboard
- upstream Hermes gateway runtime
- repo-owned `ghostship-hermes-router`
- repo-owned Discord forced-channel routing patch
- repo-owned dashboard `Terminal` entry backed by same-origin `ttyd`
- persisted `/home/hermes`, `/workspace`, and `/nix`

The image is intentionally not NixOS. Docker owns container lifecycle. `s6-overlay` owns in-container supervision. Hermes owns `~/.hermes`.

## Runtime Contract

- Base image: `ubuntu:24.04`
- PID 1: `s6-overlay`
- Runtime user: `hermes` (`3000:3000`)
- Hermes core: `/opt/hermes`
- Router: `/opt/ghostship-router`
- Canonical persisted home: `/home/hermes`
- Canonical Hermes home: `/home/hermes/.hermes`
- Canonical workspace: `/workspace`
- Canonical userland Nix store: `/nix`
- Public web surface: `0.0.0.0:7681`
- Internal services:
  - dashboard: `127.0.0.1:9119`
  - router: `127.0.0.1:8788`
  - ttyd: unix socket at `/run/user/3000/ttyd.sock`

This is a workstation container. Use `terminal.backend: local`. Do not use nested Docker terminal sandboxes for the normal path.

## What The Image Owns

Immutable image-owned layer:

- Ubuntu base OS
- Hermes core in `/opt/hermes`
- router in `/opt/ghostship-router`
- `s6`, `nginx`, `ttyd`
- repo-owned Hermes patches:
  - Discord router-pinned channel
  - dashboard `Terminal` entry
- baked fixed environment defaults

Persistent downstream-owned layer:

- `/home/hermes`
  - `~/.hermes`
  - `~/.config`
  - `~/.local`
  - `~/.npm`
  - `~/.cargo`
  - `~/.rustup`
  - `~/.codex`
  - `~/.opencode`
  - `~/.ssh`
  - shell history and other userland state
- `/workspace`
- `/nix`

Package ownership split:

- image: Hermes core, router, full repo `ghostship-*` CLI layer, and the operator utility bundle for the workstation contract
- native npm seed in persisted home: `codex`, `gemini-cli`, `agent-browser`, `opencode`
- image-managed Nix defaults: `bws`, `gh`, `gcloud`, `gws`, `blogwatcher-cli`
- image-managed local browser tooling: native CloakBrowser under `/opt/ghostship` launched through `agent-browser`, with the persistent Chrome profile rooted at `/home/hermes/.local/state/cloakbrowser`
- persisted Nix user profile: extra downstream or Hermes-installed packages on top of the image defaults

## Build

The Dockerfile is intentionally split into two stages:

- `base`: Ubuntu + Hermes core + system/runtime dependencies only, with no Ghostship-specific overlay content
- `final`: Ghostship router, dashboard patch, runtime rootfs, seeded userland defaults, exported managed Nix default-tool closure, and other repo-owned overlay content

Local image build:

```fish
docker build \
  --target final \
  --build-arg HERMES_REF=(string trim < packages/hermes-image/hermes-release.txt) \
  --tag ghostship-hermes:dev \
  --file packages/hermes-image/Dockerfile \
  .
```

Or use the helper:

```fish
scripts/export_publishable_image.sh ghostship-hermes:dev
```

Python utility build/test flow stays unchanged:

```fish
python3 scripts/python_utility.py lock packages/searxng-cli
python3 scripts/python_utility.py test packages/searxng-cli
python3 scripts/python_utility.py build packages/searxng-cli
```

## How The Container Runs

The container is intentionally not a single-process `CMD` wrapper. It is a workstation-style container with Docker/Podman owning the outer lifecycle and `s6` owning the in-container long-running services.

Service topology:

- `nginx` binds `0.0.0.0:7681`
- upstream Hermes dashboard listens on `127.0.0.1:9119`
- `ghostship-hermes-router` listens on `127.0.0.1:8788`
- `ttyd` listens on unix socket `/run/user/3000/ttyd.sock`
- `nginx` proxies:
  - `/` -> upstream Hermes dashboard
  - `/terminal/` -> same-origin `ttyd`
- Hermes gateway runs in-container and is supervised by `s6`

Operational consequences:

- do not run `hermes gateway install` in the container
- do not install systemd units in the container
- use `terminal.backend: local`
- protect `:7681` with Cloudflare Access or equivalent upstream auth; the image does not add its own auth layer

## Run

Minimal `docker run`:

```fish
docker run -d \
  --name ghostship-hermes \
  --restart unless-stopped \
  --publish 7681:7681 \
  --env-file ./.env \
  --volume ghostship-hermes-home:/home/hermes \
  --volume ghostship-hermes-workspace:/workspace \
  --volume ghostship-hermes-nix:/nix \
  ghcr.io/caelx/ghostship-hermes:latest
```

Podman works too:

```fish
podman run -d \
  --name ghostship-hermes \
  --restart unless-stopped \
  --publish 7681:7681 \
  --env-file ./.env \
  --volume ghostship-hermes-home:/home/hermes \
  --volume ghostship-hermes-workspace:/workspace \
  --volume ghostship-hermes-nix:/nix \
  ghcr.io/caelx/ghostship-hermes:latest
```

Example `docker compose` service:

```yaml
services:
  hermes:
    image: ghcr.io/caelx/ghostship-hermes:latest
    container_name: ghostship-hermes
    restart: unless-stopped
    ports:
      - "7681:7681"
    env_file:
      - .env
    volumes:
      - ghostship-hermes-home:/home/hermes
      - ghostship-hermes-workspace:/workspace
      - ghostship-hermes-nix:/nix

volumes:
  ghostship-hermes-home:
  ghostship-hermes-workspace:
  ghostship-hermes-nix:
```

## Persistence

Downstream must persist all three of these together:

- `/home/hermes`
- `/workspace`
- `/nix`

What each mount owns:

- `/home/hermes`
  - Hermes config, sessions, memories, skills, logs
  - `/home/hermes/.hermes/auth.json`
  - npm-installed CLIs and user config under `.local`, `.config`, `.npm`, `.codex`, `.opencode`, `.ssh`, and similar
- `/workspace`
  - project checkouts and work products
- `/nix`
  - image-managed Nix default-tool profile payload
  - operator-installed or Hermes-installed Nix packages and build outputs

Rules for coherent persistence:

- persist the whole `/home/hermes` tree, not selected dot-directories
- reuse the same `/home/hermes`, `/workspace`, and `/nix` mounts together when you recreate the container
- keep the runtime user ownership coherent; bind mounts should be writable by UID/GID `3000:3000`
- do not delete or replace `/nix` if you expect `nix profile add` installs to survive container replacement
- do not point multiple unrelated Hermes deployments at the same `/home/hermes`
- do not move Hermes core into `/home/hermes`; `/opt/hermes` stays image-owned so image replacement cleanly updates Hermes itself

First boot behavior:

- the image creates the home/runtime directories it needs under `/home/hermes`
- the image seeds the home defaults and npm CLIs into the persisted home if they are missing
- the image auto-seeds an empty persisted `/nix` from the image on first boot
- the image reconciles the current image-managed Nix default profile into reused non-empty `/nix` mounts on every boot without deleting user-managed Nix content

Detailed downstream persistence guidance still lives in [docs/workstation-image.md](/home/nixos/dev/ghostship-hermes/docs/workstation-image.md).

## Environment Variables

Two env layers exist:

1. Fixed image defaults baked into the image
2. Downstream operator env supplied at runtime

### Fixed Image Defaults

These are internal image-owned variables. Downstream must not set or override them through `--env`, `--env-file`, Compose `environment:`, or a persisted `.env`.

- `HOME=/home/hermes`
- `HERMES_HOME=/home/hermes/.hermes`
- `XDG_CONFIG_HOME=/home/hermes/.config`
- `XDG_CACHE_HOME=/home/hermes/.cache`
- `XDG_DATA_HOME=/home/hermes/.local/share`
- `NPM_CONFIG_PREFIX=/home/hermes/.local`
- `CARGO_HOME=/home/hermes/.cargo`
- `RUSTUP_HOME=/home/hermes/.rustup`
- `NIXPKGS_ALLOW_UNFREE=1`
- `NIX_CONFIG=experimental-features = nix-command flakes`
- `GHOSTSHIP_WORKSPACE_ROOT=/workspace`
- `GHOSTSHIP_WEB_PORT=7681`
- `GHOSTSHIP_DASHBOARD_HOST=127.0.0.1`
- `GHOSTSHIP_DASHBOARD_PORT=9119`
- `GHOSTSHIP_ROUTER_HOST=127.0.0.1`
- `GHOSTSHIP_ROUTER_PORT=8788`
- `GHOSTSHIP_ROUTER_URL=http://127.0.0.1:8788/v1`
- `GHOSTSHIP_NIX_DEFAULT_PROFILE=/nix/var/nix/profiles/per-user/hermes/ghostship-defaults`
- `DISCORD_REACTIONS=false`
- `DISCORD_REQUIRE_MENTION=false`
- `DISCORD_AUTO_THREAD=false`
- `GHOSTSHIP_TTYD_SOCKET=/run/user/3000/ttyd.sock`
- `GHOSTSHIP_TTYD_BASE_PATH=/terminal`
- `GHOSTSHIP_TERMINAL_CWD=/workspace`

These variables are internal because they define the persisted home layout, XDG layout, native tool install roots, and internal service topology for the workstation container. Overriding them makes the persistence contract incoherent and is unsupported.

The image `PATH` prefers:

- `/home/hermes/.local/bin`
- `/home/hermes/.cargo/bin`
- `/home/hermes/.nix-profile/bin`
- `/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin`
- `/opt/ghostship-utils/venv/bin`
- `/opt/ghostship/bin`
- `/opt/hermes/venv/bin`
- `/opt/ghostship-router/venv/bin`

### Where Downstream Env Vars Go

Downstream-owned env vars should go in exactly one of these places:

- preferred: the container runtime env, via `--env-file ./.env`, Compose `env_file:`, or Compose `environment:`
- optional: `/home/hermes/.hermes/.env` if you intentionally want Hermes to read them from persisted home state

Important rule:

- the image does not regenerate `/home/hermes/.hermes/.env`
- if you choose runtime env, keep using runtime env consistently
- if you choose persisted `.hermes/.env`, treat that file as downstream-owned state

### Downstream Operator Env Summary

Required for the default direct runtime lane:

- `OPENCODE_GO_API_KEY`
- `GOOGLE_AI_STUDIO_API_KEY`

Optional router-provider credentials:

- `NVIDIA_BUILD_API_KEY`
- `OPENROUTER_API_KEY`

Required when Discord gateway is enabled:

- `DISCORD_BOT_TOKEN`
- `DISCORD_ALLOWED_USERS`
- `DISCORD_HOME_CHANNEL`
- `DISCORD_FREE_RESPONSE_CHANNELS`
- `GHOSTSHIP_ROUTER_CHANNEL`

Recommended optional operator env:

- `WEBHOOK_SECRET`
- `BWS_ACCESS_TOKEN`
- `GITHUB_TOKEN`

Supported but not recommended for downstream:

- `BWS_SERVER_URL`
- `BROWSERBASE_API_KEY`
- `BROWSERBASE_PROJECT_ID`
- `BROWSER_USE_API_KEY`

Other service-specific `ghostship-*` utility vars are optional and recommended only when that service integration is actually in use.

Internal-only runtime env:

- `_GHOSTSHIP_ROUTER_API_KEY`

Important behavior:

- `DISCORD_HOME_CHANNEL` is the downstream-owned Discord home channel id.
- `DISCORD_REACTIONS`, `DISCORD_REQUIRE_MENTION`, and `DISCORD_AUTO_THREAD` default to `false` in the image. Downstream normally should not set them unless the contract intentionally changes.
- `DISCORD_FREE_RESPONSE_CHANNELS` is the upstream Hermes comma-separated free-response channel list.
- `GHOSTSHIP_ROUTER_CHANNEL` pins replies to router alias `agentic`
- `DISCORD_FREE_RESPONSE_CHANNELS` should include the router-pinned free-response channel.
- `GHOSTSHIP_ROUTER_CHANNEL` must be included in `DISCORD_FREE_RESPONSE_CHANNELS`
- `/model` cannot override the router-pinned forced channel
- `_GHOSTSHIP_ROUTER_API_KEY` is optional internal router auth. The image may still auto-generate it for Hermes integration, but the router does not require it to run.

Codex OAuth is not an env var. Run `hermes auth` or `hermes model` in the container. Hermes stores Codex auth in `/home/hermes/.hermes/auth.json`, so it persists with the home volume and backs the default `openai-codex/gpt-5.4` primary lane.

The full fixed env contract is also documented in [docs/runtime-env.md](/home/nixos/dev/ghostship-hermes/docs/runtime-env.md).

## Dashboard, Router, And Forced Channels

Dashboard:

- upstream Hermes dashboard is the primary UI
- repo patch adds one `Terminal` entry only
- `Terminal` renders an embedded iframe for `/terminal/`, which is served by `ttyd`

Router:

- `ghostship-hermes-router` is mandatory
- it listens on `127.0.0.1:8788`
- Hermes default config uses Codex `gpt-5.4` as the primary lane and `opencode-go/minimax-m2.7` as the configured fallback
- the managed Hermes config also exposes `ghostship-router` as a local custom provider pinned to alias `agentic`
- when configured, NVIDIA Build participates through live free-endpoint catalog discovery and outranks Zen/OpenRouter by default
- router normal routing is `agentic`-only, keeps a top-five reserve per provider, and uses the best three currently eligible models from that reserve

Forced Discord channels:

- `GHOSTSHIP_ROUTER_CHANNEL` pins replies to the local router `agentic` lane
- `/model` does not override that forced channel

## Native Hermes Management

Inside the container, manage Hermes like a normal host install:

- `hermes setup`
- `hermes model`
- `hermes auth`
- edit `/home/hermes/.hermes/config.yaml`
- edit `/home/hermes/.hermes/.env`

Do not use `hermes gateway install` inside the container. `s6` already supervises `hermes gateway run`, `hermes dashboard`, `ghostship-hermes-router`, `ttyd`, and `nginx`.

## Post-Setup Checklist

After the first successful container boot:

1. authenticate Codex so the default primary lane can run
2. verify provider and gateway env are present
3. inspect `config.yaml` once and confirm the expected Codex-primary and OpenCode-fallback defaults
4. run `hermes doctor`
5. open the dashboard and confirm `/terminal/` works through the same origin

Recommended post-setup flow:

```fish
docker exec --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env PATH=/opt/ghostship-utils/venv/bin:/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc '/opt/hermes/venv/bin/hermes auth'

docker exec --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env PATH=/opt/ghostship-utils/venv/bin:/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc '/opt/hermes/venv/bin/hermes doctor'

docker exec --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env PATH=/opt/ghostship-utils/venv/bin:/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc 'sed -n "1,220p" /home/hermes/.hermes/config.yaml'
```

Expected config shape after first boot:

- Hermes home at `/home/hermes/.hermes`
- `terminal.backend: local`
- `terminal.cwd: /workspace`
- root model uses direct `opencode-go/minimax-m2.7`
- `fallback_model` uses Codex `gpt-5.4-mini`
- `custom_providers` includes `ghostship-router` pinned to `agentic`
- Discord forced-channel behavior controlled by runtime env, not by hardcoding channel ids into `config.yaml`

## Verification

Local smoke:

```fish
tests/hermes-image/single-agent-dashboard.sh ghostship-hermes:dev
```

Useful live checks:

```fish
curl -fsS http://127.0.0.1:7681/api/status | jq
curl -fsS http://127.0.0.1:7681/terminal/ >/dev/null
docker exec ghostship-hermes sh -lc 'command -v nix git rg jq fd yq uv gh gws bws gcloud blogwatcher-cli agent-browser ghostship-sonarr ghostship-hermes-router'
docker exec ghostship-hermes sh -lc 'test -d /home/hermes/.local/state/cloakbrowser && command -v google-chrome'
docker exec --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env PATH=/opt/ghostship-utils/venv/bin:/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc '/opt/hermes/venv/bin/hermes gateway status'
docker exec --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env PATH=/opt/ghostship-utils/venv/bin:/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc '/opt/hermes/venv/bin/hermes doctor'
```

## CI And Release

- `ci.yml` evaluates the flake for repo package wiring, runs Python utility tests/builds, builds the Ubuntu Docker image, and runs the smoke test.
- `publish-image.yml` builds and pushes `amd64` and `arm64` images from `packages/hermes-image/Dockerfile` and then publishes the multi-arch manifest tags.
- `main` publishes `latest`, `sha-*`, and `hermes-*` tags.
- non-`main` manual publish runs publish only immutable `sha-*` tags.

## Ghostship Utilities

The image ships the full `ghostship-*` CLI utility layer. They remain JSON-first and keep their repo-owned API docs under `docs/api/`.

Current bundled family:

- `ghostship-bazarr`
- `ghostship-bookstack`
- `ghostship-changedetection`
- `ghostship-chaptarr`
- `ghostship-flaresolverr`
- `ghostship-grimmory`
- `ghostship-n8n`
- `ghostship-nzbget`
- `ghostship-plex`
- `ghostship-pricebuddy`
- `ghostship-prowlarr`
- `ghostship-pyload-ng`
- `ghostship-qbittorrent`
- `ghostship-radarr`
- `ghostship-romm`
- `ghostship-rss-bridge`
- `ghostship-searxng`
- `ghostship-sonarr`
- `ghostship-synology`
- `ghostship-tautulli`

Additional baked operator utilities:

- `blogwatcher-cli`
- `bws`
- `fd`
- `gcloud`
- `gh`
- `git`
- `gws`
- `jq`
- `rg`
- `tmux`
- `ttyd`
- `uv`
- `yq`

The image bakes native CloakBrowser into `/opt/ghostship` and exposes it as the standard `google-chrome` binary that `agent-browser` already probes on Linux, so Hermes keeps using the stock local Chrome lane without an executable-path override. The image also pins `AGENT_BROWSER_PROFILE=/home/hermes/.local/state/cloakbrowser`, so `agent-browser` stops replacing the browser profile with a temp directory on each launch. The `google-chrome` wrapper injects CloakBrowser's default stealth args on each launch and keeps the persistent browser profile at `/home/hermes/.local/state/cloakbrowser`.

Bundled upstream Hermes skills are seeded into `/home/hermes/.hermes/skills` from the image on boot, but seeding is file-granular. Existing downstream custom skills are preserved, and only missing default skill files are added.

## Upstream References

- [Hermes dashboard docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard)
- [Hermes Docker docs](https://hermes-agent.nousresearch.com/docs/user-guide/docker)
- [Hermes CLI docs](https://hermes-agent.nousresearch.com/docs/reference/cli-commands)
