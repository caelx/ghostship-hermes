# Runtime Environment Contract

This image has two env layers:

1. fixed image defaults baked into the Docker image
2. downstream operator env passed at container runtime

Downstream should treat the fixed image defaults as part of the image contract. The operator-facing env vars are the values you pass with `--env`, `--env-file`, or Compose `environment:`.

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
- `GHOSTSHIP_WORKSPACE_ROOT=/workspace`
- `GHOSTSHIP_WEB_PORT=7681`
- `GHOSTSHIP_DASHBOARD_HOST=127.0.0.1`
- `GHOSTSHIP_DASHBOARD_PORT=9119`
- `GHOSTSHIP_ROUTER_HOST=127.0.0.1`
- `GHOSTSHIP_ROUTER_PORT=8788`
- `GHOSTSHIP_ROUTER_URL=http://127.0.0.1:8788/v1`
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
- `/opt/hermes/venv/bin`
- `/opt/ghostship-router/venv/bin`

Notes:

- `/home/hermes/.nix-profile/bin` may be empty on first boot until the operator or Hermes installs something through Nix.
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
- `GHOSTSHIP_WORKSPACE_ROOT`
- `GHOSTSHIP_WEB_PORT`
- `GHOSTSHIP_DASHBOARD_HOST`
- `GHOSTSHIP_DASHBOARD_PORT`
- `GHOSTSHIP_ROUTER_HOST`
- `GHOSTSHIP_ROUTER_PORT`
- `GHOSTSHIP_ROUTER_URL`
- `GHOSTSHIP_TTYD_SOCKET`
- `GHOSTSHIP_TTYD_BASE_PATH`
- `GHOSTSHIP_TERMINAL_CWD`

## Downstream Operator Env

These are the variables downstream may set when the deployment needs them.

### Required For Useful Model Execution

Both provider credentials should be present for the default Ghostship runtime lane:

- `OPENCODE_GO_API_KEY`
- `OPENROUTER_API_KEY`
- `GOOGLE_AI_STUDIO_API_KEY`

Notes:

- `OPENCODE_GO_API_KEY` is the preferred direct credential for the default Ghostship lane.
- `OPENROUTER_API_KEY` enables OpenRouter-backed candidates in the local router.
- `GOOGLE_AI_STUDIO_API_KEY` is required because the runtime uses Gemini-backed supplemental tasks.

### Required When Discord Gateway Is Enabled

- `DISCORD_BOT_TOKEN`
- `DISCORD_ALLOWED_USERS`
- `DISCORD_FREE_RESPONSE_CHANNELS`
- `GHOSTSHIP_ROUTER_CHANNEL`
- `GHOSTSHIP_CODEX_CHANNEL`

Channel behavior:

- `DISCORD_FREE_RESPONSE_CHANNELS` is the upstream Hermes comma-separated free-response channel list.
- `DISCORD_FREE_RESPONSE_CHANNELS` should include the router-pinned and Codex-pinned channels.
- `GHOSTSHIP_ROUTER_CHANNEL` pins replies to `ghostship-router` `agentic`.
- `GHOSTSHIP_CODEX_CHANNEL` pins replies to Codex `gpt-5.4` with high reasoning.
- `GHOSTSHIP_ROUTER_CHANNEL` must be included in `DISCORD_FREE_RESPONSE_CHANNELS`.
- `GHOSTSHIP_CODEX_CHANNEL` must be included in `DISCORD_FREE_RESPONSE_CHANNELS`.

### Recommended Optional Operator Env

- `WEBHOOK_SECRET`
- `BWS_ACCESS_TOKEN`
- `GITHUB_TOKEN`

### Supported But Not Recommended For Downstream

- `BWS_SERVER_URL`
- `BROWSER_CDP_URL`
- `BROWSERBASE_API_KEY`
- `BROWSERBASE_PROJECT_ID`
- `BROWSER_USE_API_KEY`
- `CAMOFOX_URL`

### Service Utility Inputs

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
- `CLOAKBROWSER_URL`
- `CLOAKBROWSER_TOKEN`
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

- `_GHOSTSHIP_ROUTER_API_KEY` is auto-generated at boot.
- the image shares it between Hermes and the local router only
- it is not a public/downstream credential and should never appear in deployment env files

## Codex Auth Is Not An Env Var

Codex OAuth is persisted in:

- `/home/hermes/.hermes/auth.json`

That file survives container replacement as long as `/home/hermes` is persisted.

The Discord Codex lane depends on that persisted auth. It does not use a downstream env key.

## No In-Container Auth Layer

The dashboard and ttyd do not add basic auth. Protect the container at the proxy or access-control layer instead. Current expected deployment is Cloudflare Access in front of the public `:7681` surface.
