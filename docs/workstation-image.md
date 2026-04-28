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
- `/nix` preserves the image-managed Nix default profile plus optional user-installed Nix packages and build outputs across restart and full container replacement.

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
- every boot reconciles the image-managed default Nix profile at `/nix/var/nix/profiles/per-user/hermes/ghostship-defaults` if the current image expects store paths that are missing from a reused non-empty `/nix`

That means downstream does not need a separate manual `/nix` bootstrap step for a brand-new empty persistent volume.
It also means existing non-empty `/nix` mounts are a supported upgrade path for image-managed defaults like `bw`, `gh`, `gcloud`, `gws`, and `blogwatcher-cli`, while image-managed CloakBrowser binaries stay under `/opt/ghostship` and the persistent browser profile stays under `/home/hermes/.local/state/cloakbrowser`.

## Required Vs Fixed Environment Variables

Fixed image defaults are already baked into the image:

- `HOME=/home/hermes`
- `HERMES_HOME=/home/hermes/.hermes`
- XDG paths under `/home/hermes`
- npm/cargo/rustup roots under `/home/hermes`
- `GHOSTSHIP_NIX_DEFAULT_PROFILE=/nix/var/nix/profiles/per-user/hermes/ghostship-defaults`
- router/dashboard/ttyd internal ports and paths

These are internal image-owned variables and paths. Downstream must not override them through runtime env.

Downstream should pass only the operator-facing runtime env vars. The full list lives in [runtime-env.md](/home/nixos/dev/ghostship-hermes/docs/runtime-env.md).

The common downstream set for the default Ghostship runtime is:

- `OPENCODE_GO_API_KEY`
- `OPENCODE_ZEN_API_KEY`
- `NVIDIA_BUILD_API_KEY`
- `ZENMUX_API_KEY`
- `ELECTRON_HUB_API_KEY`
- `OPENROUTER_API_KEY`
- `GOOGLE_AI_STUDIO_API_KEY`
- `DISCORD_BOT_TOKEN`
- `DISCORD_ALLOWED_USERS`
- `DISCORD_HOME_CHANNEL`
- `DISCORD_FREE_RESPONSE_CHANNELS`
- `GHOSTSHIP_CODEX_CHANNEL`
- `DISCORD_WEBHOOK_CHANNEL`
- `WEBHOOK_SECRET`

Discord channel contract:

- `DISCORD_HOME_CHANNEL` is the downstream-owned Discord home channel id; set it to `#assistant`.
- `DISCORD_REACTIONS` and `DISCORD_REQUIRE_MENTION` default to `false`; `DISCORD_AUTO_THREAD` defaults to `true` inside the image.
- `DISCORD_FREE_RESPONSE_CHANNELS` is the upstream Hermes comma-separated free-response channel list.
- `GHOSTSHIP_CODEX_CHANNEL` pins `#foodstamps`, including its Discord threads, to `openai-codex/gpt-5.5`.
- `DISCORD_FREE_RESPONSE_CHANNELS` must include the `#foodstamps` channel id.
- `DISCORD_WEBHOOK_CHANNEL` points at `#webhooks` and is the default channel used when Hermes creates a Discord webhook subscription without an explicit `--deliver-chat-id`.
- The managed gateway retires closed Discord thread sessions after 05:00 local Hermes time and keeps their historical SQLite transcripts.

Internal-only runtime auth may be auto-generated for Hermes compatibility:

- `_GHOSTSHIP_ROUTER_API_KEY`

Router free-provider defaults are RPM-limited before the paid OpenCode Go fallback: NVIDIA Build 30, OpenCode Zen 30, ZenMux 10, Electron Hub 5, and OpenRouter 20. Free attempts are also bounded by adaptive shape-aware health and timeout budgets. Override RPM with `GHOSTSHIP_ROUTER_PROVIDER_RPM_*`; override timeout budgets with `GHOSTSHIP_ROUTER_FREE_ATTEMPT_TIMEOUT_SECONDS`, `GHOSTSHIP_ROUTER_FREE_STREAM_FIRST_BYTE_TIMEOUT_SECONDS`, `GHOSTSHIP_ROUTER_FREE_TOTAL_BUDGET_SECONDS`, and `GHOSTSHIP_ROUTER_FALLBACK_TIMEOUT_SECONDS`.

Codex OAuth is not set by env var. Authenticate once inside the persisted home for the forced `#foodstamps` Codex channel:

```fish
docker exec -it --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env GHOSTSHIP_NIX_DEFAULT_PROFILE=/nix/var/nix/profiles/per-user/hermes/ghostship-defaults --env PATH=/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc '/opt/hermes/venv/bin/hermes auth'
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
- inspect or extend `~/.hermes/.env`

Boot projects the supported Hermes env inventory into both:

- `/run/ghostship/hermes.env` for the live gateway/dashboard service environment
- `~/.hermes/.env` for persisted home-state visibility

Non-managed keys already present in `~/.hermes/.env` are preserved.

Do not use:

- `hermes gateway install`

The container already supervises the gateway with `s6`.

## Persistence Validation

Quick smoke:

```fish
curl -fsS http://127.0.0.1:7681/api/status | jq
docker exec --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env GHOSTSHIP_NIX_DEFAULT_PROFILE=/nix/var/nix/profiles/per-user/hermes/ghostship-defaults --env PATH=/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc '/opt/hermes/venv/bin/hermes gateway status'
docker exec ghostship-hermes sh -lc 'command -v nix git rg jq fd yq uv gh gws bw gcloud blogwatcher-cli agent-browser ghostship-hermes-router'
docker exec ghostship-hermes sh -lc 'test -d /home/hermes/.local/state/cloakbrowser && command -v google-chrome'
```

Prove `/nix` survives replacement:

```fish
docker exec --user 3000:3000 --env HOME=/home/hermes --env GHOSTSHIP_NIX_DEFAULT_PROFILE=/nix/var/nix/profiles/per-user/hermes/ghostship-defaults --env PATH=/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc 'nix --extra-experimental-features "nix-command flakes" profile add nixpkgs#hello'
docker exec --user 3000:3000 --env HOME=/home/hermes --env GHOSTSHIP_NIX_DEFAULT_PROFILE=/nix/var/nix/profiles/per-user/hermes/ghostship-defaults --env PATH=/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ghostship-hermes /bin/sh -lc 'hello'
```

Replace the container with the same `/home/hermes`, `/workspace`, and `/nix` mounts. `hello` should still exist.

## Utility Installation Policy

Default image behavior:

- Hermes/runtime-required Linux tools ship in the image.
- The old service-specific `ghostship-*` CLI layer is retired from the image.
- The operator utility bundle ships as an image-managed Nix default profile exported from the Ghostship-specific final image phase and reconciled into persisted `/nix` on every boot.
- native CloakBrowser ships in the image and is exposed as the standard `google-chrome` binary that `agent-browser` already probes on Linux, with the persistent browser profile rooted at `/home/hermes/.local/state/cloakbrowser`.
- Node-native agent tools ship through npm in persisted home state.
- Nix stays available for extra downstream or Hermes-installed packages through `/home/hermes/.nix-profile/bin` on top of the image-managed defaults.
- bundled upstream Hermes skills are seeded into `/home/hermes/.hermes/skills` on boot without overwriting downstream custom skills that already exist there.

Current preinstalled npm tools:

- `codex`
- `gemini-cli`
- `agent-browser`
- `opencode`

Separate from those npm CLIs, the image exposes native CloakBrowser as `google-chrome`, so Hermes browser skills keep using the standard local Chrome path without a sidecar browser service or executable-path override. The image also sets `AGENT_BROWSER_PROFILE=/home/hermes/.local/state/cloakbrowser` internally so `agent-browser` reuses the persistent CloakBrowser profile instead of switching to a temp launch directory.

Known upstream caveat:

- `hermes doctor` in Hermes `0.9` looks for `agent-browser` under Hermes' own `node_modules` tree rather than checking the npm-global CLI path. In this image `agent-browser` is intentionally installed the native way with npm under `/home/hermes/.local/bin`, so `command -v agent-browser` is the authoritative validation until upstream broadens that check.
