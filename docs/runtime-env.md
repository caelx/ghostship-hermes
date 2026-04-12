# Runtime Environment Contract

This image's managed runtime environment is the generated file:

- `/home/hermes/.hermes/.env`

Bootstrap rewrites that file from the allowlists in
`packages/hermes-image/nixos-module.nix`
on every managed boot.

Rules:

- Only approved keys are copied into the managed `.env`.
- Unset keys are omitted.
- `TERMINAL_CWD=/workspace` is always written.
- `WEBHOOK_ENABLED=true` and `WEBHOOK_PORT=8644` are always written.
- If `OPENCODE_API_KEY` is unset but `OPENCODE_GO_API_KEY` is set, bootstrap also writes `OPENCODE_API_KEY` with the same value.
- The managed scaffold uses Codex OAuth for the `openai-codex` fallback path and uses `OPENAI_API_KEY` as the bearer token input for manual `ghostship-router` calls.

## Single-Agent Inputs

- `DISCORD_BOT_TOKEN`
- `DISCORD_ALLOWED_USERS`
- `GHOSTSHIP_ROUTER_CHANNEL`
- `DISCORD_HOME_CHANNEL`
- `BROWSER_CDP_URL`
- `WEBHOOK_SECRET`

When `GHOSTSHIP_ROUTER_CHANNEL` is set, the managed advisory hook treats that Discord channel as a Ghostship Router guidance lane. It does not block replies or modify gateway dispatch; it only warns users to switch with `/model custom:ghostship-router:<model>` when the session is not already tracked as a router-backed model.

## Provider, Auth, And Integration Inputs

- `GOOGLE_AI_STUDIO_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL`
- `OPENROUTER_HTTP_REFERER`
- `OPENROUTER_TITLE`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENCODE_API_KEY`
- `OPENCODE_GO_API_KEY`
- `OPENCODE_BASE_URL`
- `GITHUB_TOKEN`
- `GH_TOKEN`
- `HASS_TOKEN`
- `HASS_URL`
- `BWS_ACCESS_TOKEN`
- `BWS_SERVER_URL`

## Browser-Provider Inputs

- `BROWSERBASE_API_KEY`
- `BROWSERBASE_PROJECT_ID`
- `BROWSER_USE_API_KEY`
- `BROWSERBASE_PROXIES`
- `BROWSERBASE_ADVANCED_STEALTH`
- `BROWSERBASE_KEEP_ALIVE`
- `BROWSERBASE_SESSION_TIMEOUT`
- `BROWSER_INACTIVITY_TIMEOUT`
- `CAMOFOX_URL`

## Utility And Service Inputs

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
- `PYLOAD_USER`
- `PYLOAD_PASS`
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

## Intentionally Not Copied Into The Managed `.env`

These values are not part of the managed single-agent runtime contract and should
not be expected in `/home/hermes/.hermes/.env`:

- `CHAPTARR_API_PATH`
- `CHAPTARR_API_VERSION`
- `N8N_PUBLIC_API_ENDPOINT`
- `N8N_PUBLIC_API_VERSION`
- `GHOSTSHIP_ROUTER_API_KEY`
- `API_SERVER_HOST`
- `API_SERVER_PORT`
- `API_SERVER_KEY`

The general rule is that fixed path/version selectors, router-daemon internals,
container boot plumbing, and test-only headers stay outside the managed Hermes
runtime env file.
