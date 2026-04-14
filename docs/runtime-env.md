# Runtime Environment Contract

This image has two env layers:

1. fixed image defaults baked into the Docker image
2. downstream operator env passed at container runtime

Downstream should treat the fixed image defaults as part of the image contract. The operator-facing env vars are the values you pass with `--env`, `--env-file`, or Compose `environment:`.

## Fixed Image Defaults

These are already set in the image. Downstream normally should not override them.

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

The image also bakes a PATH that prefers:

- `/home/hermes/.local/bin`
- `/home/hermes/.cargo/bin`
- `/home/hermes/.nix-profile/bin`
- `/opt/hermes/venv/bin`
- `/opt/ghostship-router/venv/bin`

## Downstream Operator Env

These are the variables downstream should set when the deployment needs them.

### Core Runtime

- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`

Notes:

- `OPENAI_API_KEY` is the compatibility bearer token Hermes uses when talking to the local router through the OpenAI-compatible endpoint.
- `OPENROUTER_API_KEY` lets the local router talk to OpenRouter-backed models.

### Direct Provider Lanes

- `OPENCODE_GO_API_KEY`
- `GOOGLE_AI_STUDIO_API_KEY`

Use these when the runtime needs direct provider access outside the local router path.

### Discord Gateway

- `DISCORD_BOT_TOKEN`
- `DISCORD_ALLOWED_USERS`
- `DISCORD_HOME_CHANNEL`
- `GHOSTSHIP_ROUTER_CHANNEL`
- `GHOSTSHIP_DEEPTHINK_CHANNEL`

Channel behavior:

- `GHOSTSHIP_ROUTER_CHANNEL` pins replies to `ghostship-router` `agentic`.
- `GHOSTSHIP_DEEPTHINK_CHANNEL` pins replies to Codex `gpt-5.4` with high reasoning.

### Webhook / Workflow Secrets

- `WEBHOOK_SECRET`
- `BWS_ACCESS_TOKEN`
- `BWS_SERVER_URL`
- `GITHUB_TOKEN`
- `GH_TOKEN`

### Browser / Remote Browser Options

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

## Codex Auth Is Not An Env Var

Codex OAuth is persisted in:

- `/home/hermes/.hermes/auth.json`

That file survives container replacement as long as `/home/hermes` is persisted.

`#deepthink` depends on that persisted auth. It does not use `OPENAI_API_KEY`.

## No In-Container Auth Layer

The dashboard and ttyd do not add basic auth. Protect the container at the proxy or access-control layer instead. Current expected deployment is Cloudflare Access in front of the public `:7681` surface.
