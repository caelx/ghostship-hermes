## Why

The Hermes image already treats each managed profile `.env` file as the operator-facing source of truth for profile runtime configuration, but the actual projection contract is still implicit and incomplete. The bootstrap writer persists only a curated subset of container-wide environment variables, the translation rules from repo-owned container env names to profile-local Hermes env names are not fully documented, and the repo does not yet capture a single explicit inventory of which upstream Hermes and repo-owned env inputs belong in profile `.env`.

This matters now because the runtime contract is widening beyond the original Discord-only projection. Operators need one precise source of truth for which container env supplied by `nixos-config` must be copied into each profile `.env`, which values must be translated into profile-local names, and which image, router-daemon, and container boot plumbing values must stay container-only.

## What Changes

- Define the full managed profile `.env` contract for the Hermes image, including the exact supported shared env keys, profile-scoped env keys, and upstream Hermes-facing translations that bootstrap must materialize into each managed profile `.env`.
- Capture the translation rules from repo-owned container env names to profile-local Hermes-facing names, including Discord profile inputs, webhook secret inputs, and compatibility aliases where the container source name differs from the profile-local runtime name.
- Add explicit per-profile browser CDP env names for the managed `assistant`, `operations`, and `supervisor` profiles and map those profile-scoped container env values into the corresponding profile-local `BROWSER_CDP_URL`.
- Classify which container-wide env remain intentionally outside profile `.env` because they are image infrastructure, router-daemon internals, or container boot plumbing rather than profile-facing runtime configuration, with router service variables explicitly excluded from the profile contract.
- Require bootstrap env projection to stay idempotent so unchanged container env does not rewrite profile `.env` files or trigger unnecessary restarts.
- Align the env inventory, bootstrap pass-through contract, and operator-facing docs around one explicit allowlist instead of scattered implicit behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `hermes-profile-env-contract`: Expand the spec to define the complete managed profile `.env` inventory, the shared versus profile-scoped translation rules, the compatibility aliases that bootstrap must normalize into Hermes-facing env names, and the exclusions that remain container-only.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, especially the bootstrap `PassEnvironment` contract and `write_profile_env()` projection logic.
- Affected docs: operator-facing guidance that describes profile `.env`, the Hermes image env contract, and supported runtime configuration.
- Affected validation: image/bootstrap checks that assert profile `.env` contents and restart behavior.
- Affected behavior: managed profile `.env` generation, profile gateway restart visibility, and operator expectations for which `nixos-config` environment variables become profile-local runtime env.


## Full Managed Profile `.env` Contract

Written into every managed profile `.env` unchanged when set on the container:

- Provider and workflow env: `GOOGLE_AI_STUDIO_API_KEY`, `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_HTTP_REFERER`, `OPENROUTER_TITLE`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENCODE_API_KEY`, `OPENCODE_GO_API_KEY`, `OPENCODE_BASE_URL`, `GITHUB_TOKEN`, `GH_TOKEN`, `HASS_URL`, `HASS_TOKEN`, `BWS_ACCESS_TOKEN`, `BWS_SERVER_URL`
- Browser env: `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID`, `BROWSER_USE_API_KEY`, `BROWSERBASE_PROXIES`, `BROWSERBASE_ADVANCED_STEALTH`, `BROWSERBASE_KEEP_ALIVE`, `BROWSERBASE_SESSION_TIMEOUT`, `BROWSER_INACTIVITY_TIMEOUT`, `CAMOFOX_URL`
- Utility env inherited by profiles and router-invoked utilities: `SEARXNG_URL`, `SONARR_URL`, `SONARR_API_KEY`, `RADARR_URL`, `RADARR_API_KEY`, `PROWLARR_URL`, `PROWLARR_API_KEY`, `PLEX_URL`, `PLEX_TOKEN`, `ROMM_URL`, `ROMM_TOKEN`, `ROMM_USERNAME`, `ROMM_PASSWORD`, `NZBGET_URL`, `NZBGET_USER`, `NZBGET_PASS`, `QBITTORRENT_URL`, `QBITTORRENT_USER`, `QBITTORRENT_PASS`, `GRIMMORY_URL`, `GRIMMORY_TOKEN`, `GRIMMORY_USERNAME`, `GRIMMORY_PASSWORD`, `TAUTULLI_URL`, `TAUTULLI_API_KEY`, `BAZARR_URL`, `BAZARR_API_KEY`, `SYNOLOGY_URL`, `SYNOLOGY_USER`, `SYNOLOGY_PASS`, `SYNOLOGY_VERIFY_SSL`, `FLARESOLVERR_URL`, `PYLOAD_URL`, `PYLOAD_USER`, `PYLOAD_PASS`, `CLOAKBROWSER_URL`, `CLOAKBROWSER_TOKEN`, `PRICEBUDDY_URL`, `PRICEBUDDY_TOKEN`, `RSS_BRIDGE_URL`, `CHANGEDETECTION_URL`, `CHANGEDETECTION_API_KEY`, `CHAPTARR_URL`, `CHAPTARR_API_KEY`, `CHAPTARR_API_PATH`, `CHAPTARR_API_VERSION`, `N8N_URL`, `N8N_API_KEY`, `N8N_PUBLIC_API_ENDPOINT`, `N8N_PUBLIC_API_VERSION`

Translated into profile-local names:

- `DISCORD_GENERAL_CHANNEL_ID` -> `DISCORD_HOME_CHANNEL` in every managed profile `.env`
- `DISCORD_ASSISTANT_BOT_TOKEN` -> `DISCORD_BOT_TOKEN` in `assistant/.env`
- `DISCORD_ASSISTANT_ALLOWED_USERS` -> `DISCORD_ALLOWED_USERS` in `assistant/.env`
- `DISCORD_ASSISTANT_CHANNEL_ID` -> `DISCORD_FREE_RESPONSE_CHANNELS` in `assistant/.env`
- `DISCORD_OPERATIONS_BOT_TOKEN` -> `DISCORD_BOT_TOKEN` in `operations/.env`
- `DISCORD_OPERATIONS_ALLOWED_USERS` -> `DISCORD_ALLOWED_USERS` in `operations/.env`
- `DISCORD_OPERATIONS_CHANNEL_ID` -> `DISCORD_FREE_RESPONSE_CHANNELS` in `operations/.env`
- `DISCORD_SUPERVISOR_BOT_TOKEN` -> `DISCORD_BOT_TOKEN` in `supervisor/.env`
- `DISCORD_SUPERVISOR_ALLOWED_USERS` -> `DISCORD_ALLOWED_USERS` in `supervisor/.env`
- `DISCORD_SUPERVISOR_CHANNEL_ID` -> `DISCORD_FREE_RESPONSE_CHANNELS` in `supervisor/.env`
- `WEBHOOK_ASSISTANT_SECRET` -> `WEBHOOK_SECRET` in `assistant/.env`
- `WEBHOOK_OPERATIONS_SECRET` -> `WEBHOOK_SECRET` in `operations/.env`
- `WEBHOOK_SUPERVISOR_SECRET` -> `WEBHOOK_SECRET` in `supervisor/.env`
- `BROWSER_ASSISTANT_CDP_URL` -> `BROWSER_CDP_URL` in `assistant/.env`
- `BROWSER_OPERATIONS_CDP_URL` -> `BROWSER_CDP_URL` in `operations/.env`
- `BROWSER_SUPERVISOR_CDP_URL` -> `BROWSER_CDP_URL` in `supervisor/.env`

Generated into every managed profile `.env`:

- `TERMINAL_CWD=/workspace`
- `WEBHOOK_ENABLED=true`
- `WEBHOOK_PORT=8644` in `assistant/.env`
- `WEBHOOK_PORT=8645` in `operations/.env`
- `WEBHOOK_PORT=8646` in `supervisor/.env`
- Compatibility alias: when `OPENCODE_API_KEY` is unset and `OPENCODE_GO_API_KEY` is set, bootstrap also writes `OPENCODE_API_KEY=<OPENCODE_GO_API_KEY>`

Explicitly excluded from profile `.env` and kept container-only:

- Image and bootstrap plumbing: `HOME`, `HERMES_HOME`, `SSL_CERT_FILE`, `NIX_SSL_CERT_FILE`, `GHOSTSHIP_TERMINAL_CWD`, `GHOSTSHIP_HERMES_PROJECT_ROOT`, `GHOSTSHIP_HERMES_RUNTIME_FLAKE_REF`, `GHOSTSHIP_HERMES_PROFILES`, `GHOSTSHIP_HERMES_DEFAULT_PROFILE`, `GHOSTSHIP_HERMES_MANAGED_PROFILE`, `GHOSTSHIP_HERMES_SHARED_SKILLS_DIR`, `GHOSTSHIP_HERMES_PROFILE_SKILLS_ROOT`, `GHOSTSHIP_TOOLING_MODE`, `GHOSTSHIP_DASHBOARD_HOST`
- Router listener and daemon config: `GHOSTSHIP_ROUTER_HOST`, `GHOSTSHIP_ROUTER_PORT`, `GHOSTSHIP_ROUTER_LOG_LEVEL`, `GHOSTSHIP_ROUTER_STATE_DIR`, `GHOSTSHIP_ROUTER_DB_PATH`, `GHOSTSHIP_ROUTER_API_KEY`, `GHOSTSHIP_ROUTER_CORS_ORIGINS`, `GHOSTSHIP_ROUTER_TIMEOUT`, `GHOSTSHIP_ROUTER_INVENTORY_TTL`, `GHOSTSHIP_ROUTER_REFRESH_INTERVAL`, `GHOSTSHIP_ROUTER_ALIAS_MODEL_LIMIT`, `GHOSTSHIP_ROUTER_ALLOW_DIRECT_MODELS`, `GHOSTSHIP_ROUTER_ALLOW_MODELS`, `GHOSTSHIP_ROUTER_BLOCK_MODELS`, `GHOSTSHIP_ROUTER_DEBUG_EVENT_LIMIT`, `GHOSTSHIP_ROUTER_ROLLING_WINDOW_SECONDS`, `GHOSTSHIP_ROUTER_RANKING_ENABLED`, `GHOSTSHIP_ROUTER_RANKING_INTERVAL`, `GHOSTSHIP_ROUTER_RANKING_WORKER_MODEL`, `GHOSTSHIP_ROUTER_RANKING_SHORTLIST_SIZE`, `GHOSTSHIP_ROUTER_PROVIDER_COOLDOWN_SECONDS`, `GHOSTSHIP_ROUTER_PROVIDER_FAILURE_THRESHOLD`, `GHOSTSHIP_ROUTER_PROVIDER_RATE_LIMIT_THRESHOLD`, `GHOSTSHIP_ROUTER_PROVIDER_TIMEOUT_THRESHOLD`, `GHOSTSHIP_ROUTER_PROVIDER_EXHAUSTION_THRESHOLD`, `GHOSTSHIP_ROUTER_ASSISTED_BUCKET_MODEL`, `GHOSTSHIP_ROUTER_ASSISTED_BUCKET_BATCH_SIZE`, `GHOSTSHIP_ROUTER_DISABLED_PROVIDERS`, `GHOSTSHIP_ROUTER_DISABLED_MODELS`, `GHOSTSHIP_ROUTER_PROVIDER_WEIGHT_OVERRIDES`, `GHOSTSHIP_ROUTER_MODEL_WEIGHT_OVERRIDES`, `GHOSTSHIP_ROUTER_ALIAS_PIN_AUXILIARY`, `GHOSTSHIP_ROUTER_ALIAS_PIN_CODING`, `GHOSTSHIP_ROUTER_ALIAS_PIN_AGENTIC`, `GHOSTSHIP_ROUTER_ALIAS_PIN_VISION`, `GHOSTSHIP_ROUTER_ALIAS_PIN_TTS`, `GHOSTSHIP_ROUTER_AUXILIARY_MODELS`, `GHOSTSHIP_ROUTER_CODING_MODELS`, `GHOSTSHIP_ROUTER_AGENTIC_MODELS`, `GHOSTSHIP_ROUTER_VISION_MODELS`, `GHOSTSHIP_ROUTER_TTS_MODELS`, `API_SERVER_HOST`, `API_SERVER_PORT`, `API_SERVER_KEY`, `API_SERVER_CORS_ORIGINS`
- Test-only utility headers: `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID`, `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET`
