# Workstation Image Deployment

This document is the downstream deployment contract for the Ubuntu workstation image.

## Required Persistent Mounts

Persist all three:

- `/home/hermes`
- `/workspace`
- `/nix`

Why:

- `/home/hermes` preserves Hermes config, Codex auth, sessions, memories, skills, XDG state, npm-installed CLIs, shell history, and user config.
- `/workspace` preserves projects and work products.
- `/nix` preserves optional user-installed Nix packages and build outputs across restart and full container replacement.

## `/nix` Persistence

Use one persistent volume or bind mount for `/nix` and keep reusing it with replacement containers.

Do:

- create the `/nix` volume once
- mount it at `/nix` on every new container
- keep the same volume when replacing the container image

Do not:

- delete or recreate the `/nix` volume if you expect `nix profile add` installs to survive
- mount different fresh `/nix` volumes on each deployment

First-boot behavior:

- if `/nix/store` is empty, the container seeds it from `/opt/ghostship/nix-seed.tar.zst`
- later boots reuse the existing persisted store

That means downstream does not need a separate manual `/nix` bootstrap step for a brand-new empty persistent volume.

## Required Vs Fixed Environment Variables

Fixed image defaults are already baked into the image:

- `HOME=/home/hermes`
- `HERMES_HOME=/home/hermes/.hermes`
- XDG paths under `/home/hermes`
- npm/cargo/rustup roots under `/home/hermes`
- router/dashboard/ttyd internal ports and paths

These are internal image-owned variables and paths. Downstream must not override them through runtime env.

Downstream should pass only the operator-facing runtime env vars. The full list lives in [runtime-env.md](/home/nixos/dev/ghostship-hermes/docs/runtime-env.md).

The common downstream set for the default Ghostship runtime is:

- `OPENCODE_GO_API_KEY`
- `OPENROUTER_API_KEY`
- `GOOGLE_AI_STUDIO_API_KEY`
- `DISCORD_BOT_TOKEN`
- `DISCORD_ALLOWED_USERS`
- `DISCORD_HOME_CHANNEL`
- `DISCORD_FREE_RESPONSE_CHANNELS`
- `GHOSTSHIP_ROUTER_CHANNEL`
- `GHOSTSHIP_CODEX_CHANNEL`
- `WEBHOOK_SECRET`

Discord channel contract:

- `DISCORD_HOME_CHANNEL` is the downstream-owned Discord home channel id.
- `DISCORD_FREE_RESPONSE_CHANNELS` is the upstream Hermes comma-separated free-response channel list.
- `DISCORD_FREE_RESPONSE_CHANNELS` should include the router-pinned and Codex-pinned channels.
- `GHOSTSHIP_ROUTER_CHANNEL` pins one free-response channel to the local router `agentic` lane.
- `GHOSTSHIP_CODEX_CHANNEL` pins one free-response channel to Codex `gpt-5.4` with high reasoning.
- `GHOSTSHIP_ROUTER_CHANNEL` must be included in `DISCORD_FREE_RESPONSE_CHANNELS`.
- `GHOSTSHIP_CODEX_CHANNEL` must be included in `DISCORD_FREE_RESPONSE_CHANNELS`.

Internal-only runtime auth is auto-generated:

- `_GHOSTSHIP_ROUTER_API_KEY`

Codex OAuth is not set by env var. Authenticate once inside the persisted home:

```fish
docker exec -it --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env PATH=/opt/ghostship-utils/venv/bin:/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc '/opt/hermes/venv/bin/hermes auth'
```

That writes `/home/hermes/.hermes/auth.json`, which persists with the home volume.

## Docker Compose Example

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
      - hermes-home:/home/hermes
      - hermes-workspace:/workspace
      - hermes-nix:/nix

volumes:
  hermes-home: {}
  hermes-workspace: {}
  hermes-nix: {}
```

## Direct `docker run`

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

## Public Access Model

The image binds the web surface to `0.0.0.0:7681`.

The dashboard and ttyd do not add built-in auth. The intended deployment pattern is:

- expose only `:7681`
- put Cloudflare Access or another upstream access-control layer in front of it

No basic auth is configured in the container.

## Native Hermes Management Inside The Container

Manage Hermes like a normal host install:

- `hermes setup`
- `hermes model`
- `hermes auth`
- edit `~/.hermes/config.yaml`
- edit `~/.hermes/.env`

Do not use:

- `hermes gateway install`

The container already supervises the gateway with `s6`.

## Persistence Validation

Quick smoke:

```fish
curl -fsS http://127.0.0.1:7681/api/status | jq
docker exec --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env PATH=/opt/ghostship-utils/venv/bin:/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc '/opt/hermes/venv/bin/hermes gateway status'
docker exec ghostship-hermes sh -lc 'command -v nix git rg jq fd yq uv gh gws bws gcloud blogtato agent-browser ghostship-sonarr ghostship-hermes-router'
```

Prove `/nix` survives replacement:

```fish
docker exec --user 3000:3000 --env HOME=/home/hermes --env PATH=/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc 'nix --extra-experimental-features "nix-command flakes" profile add nixpkgs#hello'
docker exec --user 3000:3000 --env HOME=/home/hermes --env PATH=/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc 'hello'
```

Replace the container with the same `/home/hermes`, `/workspace`, and `/nix` mounts. `hello` should still exist.

## Utility Installation Policy

Default image behavior:

- Hermes/runtime-required Linux tools ship in the image.
- The full repo `ghostship-*` CLI layer ships in the image.
- The operator utility bundle ships in the image.
- Node-native agent tools ship through npm in persisted home state.
- Nix stays available for extra downstream or Hermes-installed packages on top of the image defaults.

Current preinstalled npm tools:

- `codex`
- `gemini-cli`
- `agent-browser`
- `opencode`

Known upstream caveat:

- `hermes doctor` in Hermes `0.9` looks for `agent-browser` under Hermes' own `node_modules` tree rather than checking the npm-global CLI path. In this image `agent-browser` is intentionally installed the native way with npm under `/home/hermes/.local/bin`, so `command -v agent-browser` is the authoritative validation until upstream broadens that check.
