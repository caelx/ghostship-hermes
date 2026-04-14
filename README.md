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
  - Discord `#deepthink` pinned to Codex `gpt-5.4` with high reasoning
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

- image: Hermes core plus only true runtime dependencies
- userland Nix: generic Linux/operator tools such as `git`, `jq`, `ripgrep`, `gh`, `gcloud`, `gws`, `bws`, `fd`, `tmux`, `uv`, `yq`
- native npm: `codex`, `gemini-cli`, `opencode`

## Build

Local image build:

```fish
docker build \
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

No built-in auth is added to the dashboard or ttyd. Put the container behind Cloudflare Access or an equivalent upstream access-control layer before exposing it publicly.

Detailed downstream deployment guidance lives in [docs/workstation-image.md](/home/nixos/dev/ghostship-hermes/.worktrees/adopt-ubuntu-native-workstation-image/docs/workstation-image.md).

## Persistence

Downstream must persist:

- `/home/hermes`
- `/workspace`
- `/nix`

Behavior:

- `/home/hermes` preserves Hermes config, auth, sessions, memories, skills, npm-installed CLIs, and user config.
- `/workspace` preserves projects and work products.
- `/nix` preserves user-installed Nix packages and build outputs across restart and container replacement.

The container auto-seeds an empty persisted `/nix` volume from the image on first boot. Do not delete that volume if you expect `nix profile add` installs to survive container recreation.

## Environment Variables

Two env layers exist:

1. Fixed image defaults baked into the container
2. Downstream operator env passed at runtime

Downstream should not override the fixed image defaults unless there is a specific reason. The fixed contract and the downstream operator inputs are documented in [docs/runtime-env.md](/home/nixos/dev/ghostship-hermes/.worktrees/adopt-ubuntu-native-workstation-image/docs/runtime-env.md).

Important downstream-managed inputs:

- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENCODE_GO_API_KEY`
- `GOOGLE_AI_STUDIO_API_KEY`
- `DISCORD_BOT_TOKEN`
- `DISCORD_ALLOWED_USERS`
- `DISCORD_HOME_CHANNEL`
- `GHOSTSHIP_ROUTER_CHANNEL`
- `GHOSTSHIP_DEEPTHINK_CHANNEL`
- `WEBHOOK_SECRET`
- `BWS_ACCESS_TOKEN`

Codex OAuth is not an env var. Run `hermes auth` or `hermes model` in the container. Hermes stores Codex auth in `/home/hermes/.hermes/auth.json`, so it persists with the home volume.

## Dashboard, Router, And Forced Channels

Dashboard:

- upstream Hermes dashboard is the primary UI
- repo patch adds one `Terminal` entry only
- `Terminal` opens `/terminal/`, which is served by `ttyd`

Router:

- `ghostship-hermes-router` is mandatory
- it listens on `127.0.0.1:8788`
- Hermes default config points at the local router

Forced Discord channels:

- `GHOSTSHIP_ROUTER_CHANNEL` pins replies to the local router `agentic` lane
- `GHOSTSHIP_DEEPTHINK_CHANNEL` pins replies to Codex `gpt-5.4` with high reasoning
- `/model` does not override either forced channel

## Native Hermes Management

Inside the container, manage Hermes like a normal host install:

- `hermes setup`
- `hermes model`
- `hermes auth`
- edit `/home/hermes/.hermes/config.yaml`
- edit `/home/hermes/.hermes/.env`

Do not use `hermes gateway install` inside the container. `s6` already supervises `hermes gateway run`, `hermes dashboard`, `ghostship-hermes-router`, `ttyd`, and `nginx`.

## Verification

Local smoke:

```fish
tests/hermes-image/single-agent-dashboard.sh ghostship-hermes:dev
```

Useful live checks:

```fish
curl -fsS http://127.0.0.1:7681/api/status | jq
curl -fsS http://127.0.0.1:7681/terminal/ >/dev/null
docker exec ghostship-hermes sh -lc 'command -v nix git rg'
docker exec ghostship-hermes sh -lc 'su -s /bin/sh hermes -c "HOME=/home/hermes HERMES_HOME=/home/hermes/.hermes PATH=/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin /opt/hermes/venv/bin/hermes gateway status"'
docker exec ghostship-hermes sh -lc 'su -s /bin/sh hermes -c "HOME=/home/hermes HERMES_HOME=/home/hermes/.hermes PATH=/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin /opt/hermes/venv/bin/hermes doctor"'
```

## CI And Release

- `ci.yml` evaluates the flake for repo package wiring, runs Python utility tests/builds, builds the Ubuntu Docker image, and runs the smoke test.
- `publish-image.yml` builds and pushes `amd64` and `arm64` images from `packages/hermes-image/Dockerfile` and then publishes the multi-arch manifest tags.
- `main` publishes `latest`, `sha-*`, and `hermes-*` tags.
- non-`main` manual publish runs publish only immutable `sha-*` tags.

## Ghostship Utilities

The repo still ships the `ghostship-*` CLI utilities. They remain JSON-first and keep their repo-owned API docs under `docs/api/`.

Current bundled family:

- `ghostship-bazarr`
- `ghostship-changedetection`
- `ghostship-chaptarr`
- `ghostship-cloakbrowser`
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

## Upstream References

- [Hermes dashboard docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard)
- [Hermes Docker docs](https://hermes-agent.nousresearch.com/docs/user-guide/docker)
- [Hermes CLI docs](https://hermes-agent.nousresearch.com/docs/reference/cli-commands)
