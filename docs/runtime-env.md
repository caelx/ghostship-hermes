# Runtime Environment Contract

This image has two env layers:

1. fixed image defaults baked into the Docker image
2. downstream operator env passed at container runtime

Downstream should treat the fixed image defaults as part of the image contract. The operator-facing env vars are the values you pass with `--env`, `--env-file`, or Compose `environment:`.

On boot, the image projects the supported Hermes-facing env inventory into both:

- `/run/ghostship/hermes.env` for the live managed gateway/dashboard service environment
- `/home/hermes/.hermes/.env` for persisted home-state visibility inside Hermes

`/home/hermes/.hermes/.env` is merge-preserved: managed keys are refreshed from the current runtime env, while unrelated pre-existing keys remain intact.

## Fixed Image Defaults

These are internal image-owned variables. They are already set in the image, and downstream must not set or override them.

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
- `DISCORD_AUTO_THREAD=true`
- `GHOSTSHIP_TTYD_SOCKET=/run/user/3000/ttyd.sock`
- `GHOSTSHIP_TTYD_BASE_PATH=/terminal`
- `GHOSTSHIP_TERMINAL_CWD=/workspace`

These variables are internal because they define:

- the canonical persisted home layout
- the XDG layout under `/home/hermes`
- where npm/cargo/rustup write mutable userland state
- the internal dashboard/router/ttyd topology

Downstream override of any of these values is unsupported.

The image also bakes a PATH that prefers:

- `/home/hermes/.local/bin`
- `/home/hermes/.cargo/bin`
- `/home/hermes/.nix-profile/bin`
- `/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin`
- `/opt/ghostship/bin`
- `/opt/hermes/venv/bin`
- `/opt/ghostship-router/venv/bin`

Notes:

- `/home/hermes/.nix-profile/bin` may be empty on first boot until the operator or Hermes installs something through Nix.
- `/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin` is the image-managed Nix baseline. Boot reconciles it for reused non-empty `/nix` mounts without touching the user profile.
- Node-native CLIs that ship by default are installed with npm under `/home/hermes/.local/bin`.

Do not set these in downstream runtime env:

- `HOME`
- `HERMES_HOME`
- `XDG_CONFIG_HOME`
- `XDG_CACHE_HOME`
- `XDG_DATA_HOME`
- `NPM_CONFIG_PREFIX`
- `CARGO_HOME`
- `RUSTUP_HOME`
- `NIXPKGS_ALLOW_UNFREE`
- `NIX_CONFIG`
- `GHOSTSHIP_WORKSPACE_ROOT`
- `GHOSTSHIP_WEB_PORT`
- `GHOSTSHIP_DASHBOARD_HOST`
- `GHOSTSHIP_DASHBOARD_PORT`
- `GHOSTSHIP_ROUTER_HOST`
- `GHOSTSHIP_ROUTER_PORT`
- `GHOSTSHIP_ROUTER_URL`
- `GHOSTSHIP_NIX_DEFAULT_PROFILE`
- `GHOSTSHIP_TTYD_SOCKET`
- `GHOSTSHIP_TTYD_BASE_PATH`
- `GHOSTSHIP_TERMINAL_CWD`

## Downstream Operator Env

These are the variables downstream may set when the deployment needs them.

### Required For Useful Model Execution

These provider credentials should be present for the default Ghostship runtime:

- `OPENCODE_GO_API_KEY`
- `GOOGLE_AI_STUDIO_API_KEY`

The local router can additionally use any configured provider credential:

- `NVIDIA_BUILD_API_KEY`
- `OPENCODE_ZEN_API_KEY` or legacy `OPENCODE_API_KEY`
- `ZENMUX_API_KEY`
- `ELECTRON_HUB_API_KEY`
- `OPENROUTER_API_KEY`

Notes:

- `NVIDIA_BUILD_API_KEY` enables free NVIDIA Build equivalents in the local router.
- `OPENCODE_ZEN_API_KEY`, `ZENMUX_API_KEY`, `ELECTRON_HUB_API_KEY`, and `OPENROUTER_API_KEY` enable explicit free-provider equivalents when they are seeded for the requested OpenCode Go model id.
- `OPENCODE_GO_API_KEY` backs the router paid fallback lane for exposed OpenCode Go model IDs.
- Router free-provider RPM defaults are NVIDIA Build 30, OpenCode Zen 30, ZenMux 10, Electron Hub 5, and OpenRouter 20; override them with `GHOSTSHIP_ROUTER_PROVIDER_RPM_*` env vars.
- Router free-provider attempts default to a 10s non-stream timeout, 8s streaming first-byte timeout, and 24s total free-provider budget before same-model OpenCode Go fallback; override with `GHOSTSHIP_ROUTER_FREE_ATTEMPT_TIMEOUT_SECONDS`, `GHOSTSHIP_ROUTER_FREE_STREAM_FIRST_BYTE_TIMEOUT_SECONDS`, `GHOSTSHIP_ROUTER_FREE_TOTAL_BUDGET_SECONDS`, and `GHOSTSHIP_ROUTER_FALLBACK_TIMEOUT_SECONDS`. Large Hermes `stream+tools+tool_history+reasoning` requests use `GHOSTSHIP_ROUTER_PRIMARY_SERVED_MODEL` / `GHOSTSHIP_ROUTER_FALLBACK_SERVED_MODEL` plus `GHOSTSHIP_ROUTER_OPENCODE_GO_LARGE_TOOL_HISTORY_PRIMARY_TIMEOUT_SECONDS` and `GHOSTSHIP_ROUTER_OPENCODE_GO_LARGE_TOOL_HISTORY_FALLBACK_TIMEOUT_SECONDS` to fail unhealthy primary routes quickly while allowing the configured fallback longer to complete.
- `GOOGLE_AI_STUDIO_API_KEY` is required because the runtime uses Gemini-backed supplemental tasks.
- Codex auth is not an env var; it is persisted in `/home/hermes/.hermes/auth.json` for the forced Codex channel.

### Required When Discord Gateway Is Enabled

- `DISCORD_BOT_TOKEN`
- `DISCORD_ALLOWED_USERS`
- `DISCORD_HOME_CHANNEL`
- `DISCORD_FREE_RESPONSE_CHANNELS`
- `GHOSTSHIP_CODEX_CHANNEL`
- `DISCORD_WEBHOOK_CHANNEL`

Channel behavior:

- `DISCORD_HOME_CHANNEL` is the downstream-owned Discord home channel id; set it to `#assistant`.
- `DISCORD_REACTIONS` and `DISCORD_REQUIRE_MENTION` are image-owned and default to `false`; `DISCORD_AUTO_THREAD` is image-owned and defaults to `true`.
- `DISCORD_FREE_RESPONSE_CHANNELS` is the upstream Hermes comma-separated free-response channel list.
- `GHOSTSHIP_CODEX_CHANNEL` pins replies to `openai-codex/gpt-5.5`; set it to `#foodstamps`.
- `DISCORD_FREE_RESPONSE_CHANNELS` must include the `#foodstamps` channel id.
- `DISCORD_WEBHOOK_CHANNEL` defaults Hermes-created Discord webhook subscriptions to `#webhooks` when `hermes webhook subscribe --deliver discord` omits `--deliver-chat-id`.
- `/model` cannot override Codex-pinned `#foodstamps` sessions, including sessions inside Discord threads.
- The managed gateway retires closed, archived, locked, deleted, or inaccessible Discord thread sessions after 05:00 local Hermes time while preserving historical SQLite transcripts.

### Recommended Optional Operator Env

- `WEBHOOK_SECRET`
- `BW_CLIENTID`, `BW_CLIENTSECRET`, and `BW_PASSWORD` for model-authored Bitwarden workflows
- `BITWARDENCLI_APPDATA_DIR=/home/hermes/.local/state/bitwarden-cli`
- `GITHUB_TOKEN`

### Supported But Not Recommended For Downstream

- `BROWSERBASE_API_KEY`
- `BROWSERBASE_PROJECT_ID`
- `BROWSER_USE_API_KEY`

### Model-Authored Service Tool Inputs

The old image-baked service CLIs are retired, but the env contract remains available for agents or user-authored tools created in persisted state.

- `SEARXNG_URL`
- `SONARR_URL`
- `SONARR_API_KEY`
- `RADARR_URL`
- `RADARR_API_KEY`
- `PROWLARR_URL`
- `PROWLARR_API_KEY`
- `PLEX_URL`
- `PLEX_TOKEN`
- `ROMM_URL`
- `ROMM_TOKEN`
- `ROMM_USERNAME`
- `ROMM_PASSWORD`
- `NZBGET_URL`
- `NZBGET_USER`
- `NZBGET_PASS`
- `QBITTORRENT_URL`
- `QBITTORRENT_USER`
- `QBITTORRENT_PASS`
- `GRIMMORY_URL`
- `GRIMMORY_TOKEN`
- `GRIMMORY_USERNAME`
- `GRIMMORY_PASSWORD`
- `TAUTULLI_URL`
- `TAUTULLI_API_KEY`
- `BAZARR_URL`
- `BAZARR_API_KEY`
- `SYNOLOGY_URL`
- `SYNOLOGY_USER`
- `SYNOLOGY_PASS`
- `SYNOLOGY_VERIFY_SSL`
- `FLARESOLVERR_URL`
- `PYLOAD_URL`
- `PYLOAD_API_KEY`
- `PRICEBUDDY_URL`
- `PRICEBUDDY_TOKEN`
- `RSS_BRIDGE_URL`
- `CHANGEDETECTION_URL`
- `CHANGEDETECTION_API_KEY`
- `CHAPTARR_URL`
- `CHAPTARR_API_KEY`
- `N8N_URL`
- `N8N_API_KEY`

### Internal Runtime Env

These are internal image-owned or boot-generated variables. Downstream must not set them.

- `_GHOSTSHIP_ROUTER_API_KEY`

Notes:

- `_GHOSTSHIP_ROUTER_API_KEY` is optional router auth.
- the image may auto-generate it at boot and share it between Hermes and the local router
- it is not a public/downstream credential and should never appear in deployment env files

## Codex Auth Is Not An Env Var

Codex OAuth is persisted in:

- `/home/hermes/.hermes/auth.json`

That file survives container replacement as long as `/home/hermes` is persisted.

The forced `#foodstamps` Codex channel depends on that persisted auth. It does not use a downstream env key.

## No In-Container Auth Layer

The dashboard and ttyd do not add basic auth. Protect the container at the proxy or access-control layer instead. Current expected deployment is Cloudflare Access in front of the public `:7681` surface.

## Image-Baked Utility Layer

These commands are expected to exist in the image without downstream installation:

- `blogwatcher-cli`
- `bw`
- `codex`
- `gemini`
- `agent-browser`
- `opencode`
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

For the Nix-backed defaults, the image guarantees them through the managed profile at `/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin`, not through raw `/opt/ghostship/bin -> /nix/store/...` symlinks.

The image exposes native CloakBrowser as the standard `google-chrome` binary that `agent-browser` already probes on Linux, so Hermes' stock local browser path launches it without an executable-path override. The persistent browser profile root is `/home/hermes/.local/state/cloakbrowser`; raw Chrome launches use it when no profile is supplied, while explicit `agent-browser` profile paths are preserved so native `agent-browser --session` isolation is not bypassed. `AGENT_BROWSER_EXTENSIONS` points at `/opt/ghostship/extensions/ublock-origin-lite` so agent-browser sessions load the baked uBlock Origin Lite extension without Chrome managed install policy.
