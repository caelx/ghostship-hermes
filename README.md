# ghostship-hermes

`ghostship-hermes` builds and publishes `ghcr.io/caelx/ghostship-hermes`, a lean NixOS-based Hermes container image aligned to the upstream Hermes NixOS module with a repo-approved whole-home persistence model.

Canonical image references:

- Pull ref: `ghcr.io/caelx/ghostship-hermes`
- GitHub package page: <https://github.com/caelx/ghostship-hermes/pkgs/container/ghostship-hermes>

## Runtime Model

- Hermes is configured declaratively through the upstream Hermes NixOS module.
- `HERMES_HOME=/home/hermes/.hermes`
- `HOME=/home/hermes`
- `/home/hermes` itself is the persisted volume.
- `/workspace` remains a separate persisted working directory.
- `/nix` should be persisted when you want user-level `nix profile install`, `nix shell`, and related outputs to survive container replacement.
- The runtime user is `hermes` at `3000:3000`.
- The public browser surface is the packaged MMX dashboard on port `7681`.
- The dashboard can launch as many ephemeral `ttyd` sessions as needed, tracks them as left-rail tabs, opens new tabs immediately with a loading state while `ttyd` starts, labels tabs from the shell cwd or current command, and returns to a blank home state when the active terminal is closed and no sessions remain.
- Switching between open tabs keeps each live `ttyd` session attached instead of dropping back to ttyd's reconnect prompt.
- Browser terminals start in `/workspace`.
- The image currently scaffolds three long-running Hermes profiles, `assistant`, `operations`, and `supervisor`, at `~/.hermes/profiles/...`.
- `assistant` is the primary managed profile, and repo-owned runtime commands address it explicitly with `-p assistant` instead of relying on `~/.hermes/active_profile`.
- The root Hermes config stays minimal; the scaffolded profiles carry the current Nix-managed defaults.
- Each scaffolded profile currently uses `openai-codex/gpt-5.4`, with a Hermes-native `fallback_model` of `opencode-go/minimax-m2.7` and direct Gemini 3.1 Flash-Lite Preview overrides for the configured auxiliary tasks.

Upstream note:

- This image intentionally deviates from the upstream container-mode split between state and HOME.
- Upstream normally keeps managed state under `${stateDir}/.hermes` with a separate home directory.
- Here, the repo sets `stateDir = "/home/hermes"`, so managed Hermes state and the CLI profile tree both live under `/home/hermes/.hermes` on the persisted home volume.

This image intentionally does not ship the old Ghostship workstation layer. Google Workspace support is CLI-only: `gws` is preinstalled on `PATH`, but the image does not vendor or seed Google Workspace skills. The default image also preinstalls `gcloud`, `gh`, `ssh`, `scp`, and `ssh-keygen` from `nixpkgs` on `PATH`.

The immutable image no longer tries to be the full operator workstation layer. Instead, boot-time runtime convergence reconciles the repo-owned persisted user-layer runtime contract under `/home/hermes`, removing stale managed entries and reapplying the current image-owned toolchain/config state on replacement:

- user Nix profile tools: `hermes`, `git`, `gh`, `ssh`, `scp`, `ssh-keygen`, `curl`, `jq`, `python3`, `nix`, `ripgrep`, `node`, `npm`
- npm-managed agent CLIs: `codex`, `opencode`
- image-managed browser CLI: `agent-browser`

The immutable layer stays focused on boot/supervision plus the repo-owned runtime surface:

- NixOS/container runtime
- `ttyd`
- `tirith`
- `ghostship-hermes-router`
- packaged MMX dashboard controller
- all `ghostship-*` utilities

## Persistent Paths

Canonical persistent roots:

- `/home/hermes`
- `/home/hermes/.hermes`
- `/workspace`
- `/nix`

Persisting the whole home mount keeps browser and agent tooling state persistent across container replacement. That includes XDG state, `~/.agents`, `~/.agent-browser`, `~/.codex`, `~/.copilot`, `~/.npm`, `~/.bun`, `~/.ssh`, `~/.gnupg`, and any other future tool state created under `/home/hermes`.

## `/home/hermes` Layout

Inside the running container:

- `/home/hermes` is both the interactive home directory and the persisted state mount
- `/home/hermes/.hermes` is the managed Hermes service state written by the upstream NixOS module
- named profiles live under `/home/hermes/.hermes/profiles/assistant`, `/home/hermes/.hermes/profiles/operations`, and `/home/hermes/.hermes/profiles/supervisor`
- `/workspace` remains a separate persisted work directory and is not folded into the home facade
- optional shared skills can be staged under `/home/hermes/seeds/shared/skills/<skill>/...` and optional profile skills under `/home/hermes/seeds/profiles/<profile>/skills/<skill>/...` plus an optional profile `SOUL.md` at `/home/hermes/seeds/profiles/<profile>/SOUL.md`

This layout is important:

- managed service state: `/home/hermes/.hermes`
- default CLI/home profile root: `/home/hermes/.hermes`
- named CLI profiles: `/home/hermes/.hermes/profiles/<name>`

That matches upstream Hermes CLI behavior for profiles. The repo-specific deviation is that the managed NixOS-module state now lives inside the persisted home volume instead of a separate `/data` mount.

## Systemd Layout

The container uses a small NixOS-managed unit graph:

- `ghostship-storage.service`
  prepares `/home/hermes`, `/home/hermes/.hermes`, `/workspace`, and `/nix` before user-facing services start
- `hermes-agent.service`
  remains installed from the upstream Hermes NixOS module but is not started by default
- `ghostship-hermes-user-tooling.service`
  converges the repo-owned persisted user-layer runtime contract on boot, ensures the in-container Nix daemon is available first, removes stale managed entries from the dedicated `/home/hermes/.local/state/nix/profiles/ghostship-managed` profile before re-adding the current image-owned toolchain, rewrites the managed npm project to the declared CLI set, refreshes the managed npm CLIs and symlinks under `/home/hermes/.local/bin`, and does not own the main gateway startup dependency chain
- `ghostship-hermes-user-tooling-refresh.timer`
  runs the same mutable toolchain refresh flow daily and also once shortly after boot
- `ghostship-hermes-bootstrap.service`
  is a repo-specific NixOS oneshot that reconciles the approved `assistant`, `operations`, and `supervisor` profiles after the managed Hermes config exists, writes the managed runtime env into each profile `.env`, copies any staged shared/profile skill directories into the matching Hermes skill trees only when the destination skill does not already exist, and uses explicit `-p assistant` calls for assistant-facing bootstrap work instead of relying on `~/.hermes/active_profile`
- `ghostship-hermes-profile-assistant.service`
  keeps the `assistant` gateway running with `hermes -p assistant gateway run --replace`
- `ghostship-hermes-profile-operations.service`
  keeps the `operations` gateway running with `hermes -p operations gateway run --replace`
- `ghostship-hermes-profile-supervisor.service`
  keeps the `supervisor` gateway running with `hermes -p supervisor gateway run --replace`
- `ghostship-hermes-startup.service`
  starts the dashboard, router, and the three profile gateways automatically after storage preparation and profile bootstrap; a failed mutable tooling refresh should not block the main runtime boot
- `ghostship-hermes-profile-*-restart.path`
  watches each profile's `config.yaml`, `.env`, `auth.json`, and `SOUL.md`, then triggers a matching oneshot restart helper so profile-facing changes roll the affected gateway without a manual `systemctl restart`
- `ghostship-dashboard-controller.service`
  serves the packaged MMX dashboard and proxies on-demand ephemeral `ttyd` sessions on port `7681`
- `ghostship-hermes-router.service`
  runs the local model router on `127.0.0.1:8788`, persists router state under `/home/hermes/.local/state/ghostship-hermes/router`, and exposes OpenAI-style alias routing plus debug endpoints for local tools and Hermes profiles
  Startup serves the last persisted inventory and rankings immediately, then refreshes inventory and reruns ranking in the background so the router listener is available before longer warm-up work finishes.

The profile bootstrap unit and the persistent per-profile gateway services are approved custom deviations from upstream. Upstream Hermes does not currently expose named profiles as a declarative NixOS-module option, so the profile names are declared in Nix here, materialized by a NixOS-managed oneshot, and then supervised by repo-managed systemd units.

ttyd note:

- The dashboard proxies terminals from `:7681` to internal `ttyd` listeners on localhost.
- Do not enable ttyd `--check-origin` for those sessions. The browser origin is the dashboard port, so ttyd origin-checking rejects the proxied websocket and drops the terminal into a reconnect overlay.
- The iframe sandbox is the intended browser-side safety control here; it blocks popup escape without breaking the proxied websocket.

## Running The Image

```fish
docker run \
  --rm \
  --name ghostship-hermes \
  --publish 7681:7681 \
  --volume ghostship-hermes-home:/home/hermes \
  --volume ghostship-hermes-workspace:/workspace \
  --volume /nix:/nix \
  ghcr.io/caelx/ghostship-hermes:latest
```

Notes:

- Reuse `/nix` only when it already contains compatible Nix state you want to keep. Do not hide a fresh Nix-built image behind a brand-new empty `/nix` volume.
- If you mount `/nix` to a persistent volume, prepopulate that volume with the image's `/nix` contents before first boot. A brand-new empty volume can hide the image store and break startup or Nix operations.
- Fix the per-user Nix ownership on the persisted volume before expecting mutable Nix workflows to work for `hermes`. In practice, `hermes` needs usable paths under `/nix/var/nix/profiles/per-user/hermes` and `/nix/var/nix/gcroots/per-user/hermes`.
- Persisting `/home/hermes` directly is the intended way to keep Hermes managed state, Hermes CLI profiles, XDG state, and later-installed agent tooling across container replacement.
- The dashboard is the intended browser entrypoint.
- For the current Hermes scaffold, the model-related runtime inputs are `OPENCODE_GO_API_KEY` for the main fallback model and `GOOGLE_AI_STUDIO_API_KEY` for all direct auxiliary tasks. The primary `openai-codex/gpt-5.4` path is expected to use Codex OAuth runtime state instead of an env var.
- If you are also validating the local router, source the repo `.envrc` before `docker run` so the router can use `OPENROUTER_API_KEY` plus either `OPENCODE_API_KEY` or the Hermes-aligned `OPENCODE_GO_API_KEY` for live inference against OpenRouter and OpenCode Zen.
- The shipped Hermes defaults do not depend on a separate `OPENROUTER_TEST_MODEL` override; validation should check the router aliases directly.

After startup:

1. Open `http://localhost:7681`.
2. Use the `+` button in the left rail to launch a new shell-backed `ttyd` session rooted at `/home/hermes`.
3. Each new terminal appears as a focused tab in the left rail immediately, even before the underlying `ttyd` process is ready.
4. The Hermes home screen shows only current runtime facts: paths, detected provider configuration, and the declared Hermes profiles. Use the Hermes logo in the rail to return to that view without closing running terminals.
5. The terminal fills the stage, the outer dashboard stays non-scrolling, and ttyd owns terminal scrolling and resize behavior.
6. Use the floating `×` in the top-right corner of the terminal stage to remove the active tab. When no terminals remain, the dashboard returns to the blank home state.

## Hermes Configuration

The image is intentionally declarative-first:

- Hermes managed config is written into `/home/hermes/.hermes`.
- The default runtime does not let Hermes self-apply the system flake.
- User-level Nix remains available for mutable runtime installs such as `nix profile install`, and the image uses a dedicated managed profile at `/home/hermes/.local/state/nix/profiles/ghostship-managed` to keep the baked `hermes` toolchain updateable on boot and during daily refreshes without colliding with the operator's default `~/.nix-profile`.
- The default Hermes-user PATH includes `/home/hermes/.local/bin`, `/home/hermes/.local/state/nix/profiles/ghostship-managed/bin`, and `/home/hermes/.nix-profile/bin` ahead of the fallback system toolchain so login shells and Hermes runtime commands discover the persisted mutable tool layers by default.
- The image keeps package docs, man pages, info pages, and NixOS docs available locally so Hermes can inspect in-image reference material.
- The root Hermes config is intentionally minimal in the current scaffold.
- The declared profiles are `assistant`, `operations`, and `supervisor`, and repo-owned assistant runtime calls use `hermes -p assistant` explicitly instead of a sticky active-profile file.
- The current Nix scaffold gives each profile `provider = openai-codex` with `model.default = gpt-5.4`, plus a Hermes-native `fallback_model` of `opencode-go/minimax-m2.7`.
- The current Nix scaffold also sets the shared Hermes timezone to `Pacific/Honolulu`.
- The shared scaffold now also sets `agent.max_turns = 110`, `agent.reasoning_effort = "high"`, and `agent.verbose = false` for all three profiles.
- Each profile now also enables Hermes external memory with `memory.provider = holographic`, keeps built-in memory and user-profile memory enabled, sets `nudge_interval = 10` and `flush_min_turns = 6`, and uses the local `hermes-memory-store` plugin at `$HERMES_HOME/memory_store.db` with `auto_extract = false` and `default_trust = 0.5`.
- The shared scaffold also enables transcript compression with `threshold = 0.50`, `target_ratio = 0.25`, and `protect_last_n = 20` for long-running sessions.
- The shared scaffold explicitly keeps `session_reset.mode = "none"`, while still recording placeholder idle/daily values (`idle_minutes = 1440`, `at_hour = 4`) for future policy changes.
- The shared scaffold also configures Hermes browser defaults with `cloud_provider = "local"`, `inactivity_timeout = 120`, `command_timeout = 30`, and `record_sessions = false`.
- `agent-browser` is the documented local-browser default when Browserbase, Browser Use, Camofox, and manual `/browser connect` CDP attachment are not in use, but the supported runtime path comes from the image-managed package rather than the mutable npm tooling layer. The image does not preinstall Chrome or Chromium. For the managed `assistant`, `operations`, and `supervisor` profiles, remote CDP is configured per profile through `BROWSER_ASSISTANT_CDP_URL`, `BROWSER_OPERATIONS_CDP_URL`, and `BROWSER_SUPERVISOR_CDP_URL`, which bootstrap translates into each profile's local `BROWSER_CDP_URL`.
- The shared scaffold now also sets `approvals.mode = "off"` for a trusted, non-interactive runtime posture.
- The shared scaffold also enables Hermes secret redaction and Tirith integration (`tirith_enabled = true`, `tirith_fail_open = true`) while leaving the website blocklist scaffold disabled by default.
- The shared scaffold also enables Hermes checkpoints with `max_snapshots = 50` so file mutations retain rollback history.
- The shared scaffold also enables gateway streaming updates with `transport = "edit"`, `edit_interval = 0.3`, and `buffer_threshold = 40`.
- The shared scaffold also sets display defaults with `compact = false`, `streaming = true`, `tool_preview_length = 0`, `tool_progress = "verbose"`, and `background_process_notifications = "result"`. In Hermes, this `display.streaming` flag controls CLI token streaming, while the top-level `streaming` block above controls progressive gateway message edits.
- The shared scaffold explicitly disables STT with `stt.enabled = false`.
- The shared scaffold also disables artificial response delay with `human_delay.mode = "off"`.
- Each profile config now also scaffolds Hermes `discord` defaults with `require_mention = true`, `auto_thread = false`, `reactions = true`, and `group_sessions_per_user = true`. The gateway service then maps profile-specific env vars into Hermes' standard Discord env names so a shared `DISCORD_GENERAL_CHANNEL_ID` stays mention-only while each profile's `DISCORD_<PROFILE>_CHANNEL_ID` becomes that bot's free-response role channel without opening new Discord threads automatically.
- Each managed profile gateway now also enables the Hermes webhook adapter with a fixed per-profile port map: `assistant` on `8644`, `operations` on `8645`, and `supervisor` on `8646`.
- Hermes does not have a native per-profile Discord icon field. If you want distinct icons, each profile needs its own Discord application/bot, and you set the avatar/banner in the Discord Developer Portal for that bot.
- All Hermes auxiliary tasks are pinned to Gemini 3.1 Flash-Lite Preview through the Google Gemini OpenAI-compatible endpoint using `${GOOGLE_AI_STUDIO_API_KEY}`. TTS is still intentionally left unconfigured for now.
- The bootstrap writes the managed runtime env into each profile `.env` at `~/.hermes/profiles/<profile>/.env`. Each profile `.env` is the single operator-facing source of truth for that profile, and any managed env contract change must update the bootstrap writer so the regenerated `.env` files stay in sync.
- Supported shared and profile-specific Discord runtime inputs are projected into the matching profile `.env` files during bootstrap when those values are present on the container, and bootstrap rewrites those files atomically from the current container env so managed gateway restarts do not race a partial `.env`.
- Bootstrap also writes per-profile webhook listener env into each managed profile `.env`: `WEBHOOK_ENABLED=true`, a fixed `WEBHOOK_PORT`, and `WEBHOOK_SECRET` projected from the matching deployment-provided profile secret only for that profile.
- The image publishes `/etc/ghostship-hermes-release` as the authoritative booted image release marker, and managed bootstrap mirrors that value into the persisted `/home/hermes/.ghostship-hermes-release` file on every boot so reused home state reflects the live image version.
- Each managed profile gateway now owns `~/.hermes/profiles/<profile>/gateway.pid` through the repo-managed service wrapper and lifecycle hooks, and the wrapper writes the final JSON pid record itself before `exec` so all three managed profiles keep a stable profile-local liveness marker even when Hermes' default-profile helpers disagree. Hermes doctor/status uses that pidfile as the live gateway health signal.
- Shared skills still seed from `/home/hermes/seeds/shared/skills/<skill>` and profile-specific skills still seed from `/home/hermes/seeds/profiles/<profile>/skills/<skill>`, copying only missing skill directories into Hermes-owned state. Per-profile `SOUL.md` files still seed from `/home/hermes/seeds/profiles/<profile>/SOUL.md`, but bootstrap now treats them as seed-managed files: it replaces the old Hermes-generated generic prompt during migration and keeps future seed updates in sync only while the live profile `SOUL.md` still matches the last seeded hash. Once an operator or agent edits the live profile `SOUL.md`, bootstrap stops overwriting it.

Current scaffold env vars:

Discord per-profile env vars:

- Shared mention-only channel: `DISCORD_GENERAL_CHANNEL_ID`
- Assistant bot: `DISCORD_ASSISTANT_BOT_TOKEN`, `DISCORD_ASSISTANT_ALLOWED_USERS`, `DISCORD_ASSISTANT_CHANNEL_ID`
- Operations bot: `DISCORD_OPERATIONS_BOT_TOKEN`, `DISCORD_OPERATIONS_ALLOWED_USERS`, `DISCORD_OPERATIONS_CHANNEL_ID`
- Supervisor bot: `DISCORD_SUPERVISOR_BOT_TOKEN`, `DISCORD_SUPERVISOR_ALLOWED_USERS`, `DISCORD_SUPERVISOR_CHANNEL_ID`

Webhook per-profile env vars:

- Assistant listener: fixed `WEBHOOK_PORT=8644`, secret source `WEBHOOK_ASSISTANT_SECRET`
- Operations listener: fixed `WEBHOOK_PORT=8645`, secret source `WEBHOOK_OPERATIONS_SECRET`
- Supervisor listener: fixed `WEBHOOK_PORT=8646`, secret source `WEBHOOK_SUPERVISOR_SECRET`
- The image scaffold always writes `WEBHOOK_ENABLED=true` for all three managed profile gateways.
- This repo does not generate or persist webhook secrets. Downstream deployment config such as `nixos-config` must supply the three `WEBHOOK_*_SECRET` values.

- Required for the planned Hermes model setup: `OPENCODE_GO_API_KEY` and `GOOGLE_AI_STUDIO_API_KEY`
- Recommended shared runtime env for doctor-clean supported features: `OPENROUTER_API_KEY`, `GITHUB_TOKEN` or `GH_TOKEN`, `HASS_URL`, `HASS_TOKEN`
- Optional browser-provider env vars passed through to Hermes and written into each profile `.env`: `CAMOFOX_URL`, `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID`, `BROWSER_USE_API_KEY`, `BROWSERBASE_PROXIES`, `BROWSERBASE_ADVANCED_STEALTH`, `BROWSERBASE_KEEP_ALIVE`, `BROWSERBASE_SESSION_TIMEOUT`, `BROWSER_INACTIVITY_TIMEOUT`
- Optional remote CDP env passthrough for managed profiles: `BROWSER_ASSISTANT_CDP_URL`, `BROWSER_OPERATIONS_CDP_URL`, and `BROWSER_SUPERVISOR_CDP_URL`. Bootstrap projects each source into only that profile's local `BROWSER_CDP_URL` when you want remote Chrome instead of local `agent-browser`.
- No extra secret is required for Holographic memory; it is local SQLite state under `$HERMES_HOME`
- `OPENCODE_GO_API_KEY` backs the Hermes-native `fallback_model = opencode-go/minimax-m2.7`
- `GOOGLE_AI_STUDIO_API_KEY` backs the direct Google Gemini OpenAI-compatible endpoint used for all configured auxiliary tasks
- Optional secrets bootstrap: `BWS_ACCESS_TOKEN` for Bitwarden Secrets Manager workflows inside the running profiles
- Not required for the primary model path: `OPENAI_API_KEY`; the scaffold assumes `openai-codex/gpt-5.4` uses Hermes-managed Codex OAuth runtime state rather than a static env key. Run `hermes -p assistant model`, `hermes -p operations model`, or `hermes -p supervisor model`, choose `OpenAI Codex`, and complete the device-code flow. Hermes stores that auth state in `~/.hermes/profiles/<profile>/auth.json`.

### Expected doctor warnings

The image only tries to clear `hermes doctor` warnings for the supported runtime surface. Optional integrations such as generic web-search providers, RL, image generation, and other unused third-party features remain intentionally out of scope. Remaining preview warnings should only come from intentionally unconfigured features or missing real runtime credentials, not from the packaged `agent-browser` path, the persisted CLI discovery path, or supported profile `.env` projection.

For messaging specifically, `hermes doctor` only reports the toolset as available when the profile gateway is actually running. Projecting the supported Discord env into the managed profile `.env` removes the config gap that keeps the gateway unconfigured, and the repo-managed gateway wrapper keeps `gateway.pid` aligned with the live service so health checks do not depend on stale pidfile state. A gateway that is genuinely stopped or failed will still leave the messaging warning in place.

The local preview container is intentionally bare unless you pass the same deployment env vars into it. `hermes doctor` on that preview will still report missing `OPENROUTER_API_KEY`, `GITHUB_TOKEN`/`GH_TOKEN`, `HASS_URL`, and `HASS_TOKEN` until you provide them; that is expected and does not mean the managed tooling layer failed.

### Codex OAuth tokens

The `openai-codex` provider relies on Codex OAuth (device-code flow) instead of a static API key. Use `hermes -p assistant model`, `hermes -p operations model`, or `hermes -p supervisor model`, choose `OpenAI Codex`, and complete the printed device-code login flow. Hermes stores that auth state in the selected profile at `~/.hermes/profiles/<profile>/auth.json`. Use `hermes -p <profile> auth list` to inspect active credentials. Because Hermes keeps the tokens on disk, no `OPENAI_API_KEY` env var is required for the primary profile unless you later add a custom provider that explicitly expects it.

### Skills initialization

Hermes does not fully materialize its skills hub state until you exercise it once. Run `hermes -p <profile> skills list` under the Hermes runtime user after first boot to create the profile skills directories and lockfile. That is expected and should be part of first-time runtime initialization for each declared profile you plan to use.

### Managed env files

Each profile has one operator-facing source of truth for managed runtime env: `~/.hermes/profiles/<profile>/.env`. The managed gateway services load that file with `EnvironmentFile`, and bootstrap rewrites it on every reconcile. If you change the managed runtime env contract, update the bootstrap writer in `packages/hermes-image/nixos-module.nix` so the regenerated profile `.env` files match the new contract. The root `~/.hermes/.env` is not used by the managed profile gateways in this image.

Treat the profile `.env` as the canonical place for profile-facing runtime configuration: Hermes provider credentials, browser configuration, Discord settings, webhook listener settings, Bitwarden access, and the utility/service env inherited by the installed `ghostship-*` CLIs and router-invoked utility calls. Do not copy router-daemon configuration or other image/container plumbing into the profile `.env` files.

Full managed profile `.env` contract:

- Written into every managed profile `.env` unchanged when set: `GOOGLE_AI_STUDIO_API_KEY`, `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_HTTP_REFERER`, `OPENROUTER_TITLE`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENCODE_API_KEY`, `OPENCODE_GO_API_KEY`, `OPENCODE_BASE_URL`, `GITHUB_TOKEN`, `GH_TOKEN`, `HASS_URL`, `HASS_TOKEN`, `BWS_ACCESS_TOKEN`, `BWS_SERVER_URL`, `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID`, `BROWSER_USE_API_KEY`, `BROWSERBASE_PROXIES`, `BROWSERBASE_ADVANCED_STEALTH`, `BROWSERBASE_KEEP_ALIVE`, `BROWSERBASE_SESSION_TIMEOUT`, `BROWSER_INACTIVITY_TIMEOUT`, `CAMOFOX_URL`, `SEARXNG_URL`, `SONARR_URL`, `SONARR_API_KEY`, `RADARR_URL`, `RADARR_API_KEY`, `PROWLARR_URL`, `PROWLARR_API_KEY`, `PLEX_URL`, `PLEX_TOKEN`, `ROMM_URL`, `ROMM_TOKEN`, `ROMM_USERNAME`, `ROMM_PASSWORD`, `NZBGET_URL`, `NZBGET_USER`, `NZBGET_PASS`, `QBITTORRENT_URL`, `QBITTORRENT_USER`, `QBITTORRENT_PASS`, `GRIMMORY_URL`, `GRIMMORY_TOKEN`, `GRIMMORY_USERNAME`, `GRIMMORY_PASSWORD`, `TAUTULLI_URL`, `TAUTULLI_API_KEY`, `BAZARR_URL`, `BAZARR_API_KEY`, `SYNOLOGY_URL`, `SYNOLOGY_USER`, `SYNOLOGY_PASS`, `SYNOLOGY_VERIFY_SSL`, `FLARESOLVERR_URL`, `PYLOAD_URL`, `PYLOAD_USER`, `PYLOAD_PASS`, `CLOAKBROWSER_URL`, `CLOAKBROWSER_TOKEN`, `PRICEBUDDY_URL`, `PRICEBUDDY_TOKEN`, `RSS_BRIDGE_URL`, `CHANGEDETECTION_URL`, `CHANGEDETECTION_API_KEY`, `CHAPTARR_URL`, `CHAPTARR_API_KEY`, `CHAPTARR_API_PATH`, `CHAPTARR_API_VERSION`, `N8N_URL`, `N8N_API_KEY`, `N8N_PUBLIC_API_ENDPOINT`, `N8N_PUBLIC_API_VERSION`
- Translated into profile-local names: `DISCORD_GENERAL_CHANNEL_ID` -> `DISCORD_HOME_CHANNEL` in every profile; `DISCORD_ASSISTANT_BOT_TOKEN`, `DISCORD_ASSISTANT_ALLOWED_USERS`, `DISCORD_ASSISTANT_CHANNEL_ID` -> `DISCORD_BOT_TOKEN`, `DISCORD_ALLOWED_USERS`, `DISCORD_FREE_RESPONSE_CHANNELS` in `assistant/.env`; `DISCORD_OPERATIONS_BOT_TOKEN`, `DISCORD_OPERATIONS_ALLOWED_USERS`, `DISCORD_OPERATIONS_CHANNEL_ID` -> the same three Hermes-facing keys in `operations/.env`; `DISCORD_SUPERVISOR_BOT_TOKEN`, `DISCORD_SUPERVISOR_ALLOWED_USERS`, `DISCORD_SUPERVISOR_CHANNEL_ID` -> the same three Hermes-facing keys in `supervisor/.env`; `WEBHOOK_ASSISTANT_SECRET`, `WEBHOOK_OPERATIONS_SECRET`, `WEBHOOK_SUPERVISOR_SECRET` -> `WEBHOOK_SECRET` in the matching profile `.env`; `BROWSER_ASSISTANT_CDP_URL`, `BROWSER_OPERATIONS_CDP_URL`, `BROWSER_SUPERVISOR_CDP_URL` -> `BROWSER_CDP_URL` in only the matching profile `.env`
- Generated into every managed profile `.env`: `TERMINAL_CWD=/workspace`, `WEBHOOK_ENABLED=true`, `WEBHOOK_PORT=8644` for `assistant`, `WEBHOOK_PORT=8645` for `operations`, `WEBHOOK_PORT=8646` for `supervisor`, and `OPENCODE_API_KEY=<OPENCODE_GO_API_KEY>` when `OPENCODE_API_KEY` is otherwise unset
- Kept container-only and excluded from profile `.env`: `HOME`, `HERMES_HOME`, `SSL_CERT_FILE`, `NIX_SSL_CERT_FILE`, `GHOSTSHIP_TERMINAL_CWD`, `GHOSTSHIP_HERMES_PROJECT_ROOT`, `GHOSTSHIP_HERMES_RUNTIME_FLAKE_REF`, `GHOSTSHIP_HERMES_PROFILES`, `GHOSTSHIP_HERMES_DEFAULT_PROFILE`, `GHOSTSHIP_HERMES_MANAGED_PROFILE`, `GHOSTSHIP_HERMES_SHARED_SKILLS_DIR`, `GHOSTSHIP_HERMES_PROFILE_SKILLS_ROOT`, `GHOSTSHIP_TOOLING_MODE`, `GHOSTSHIP_DASHBOARD_HOST`, all router daemon/listener env (`GHOSTSHIP_ROUTER_*`, `API_SERVER_*`), and test-only utility headers `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID` / `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET`

## Manual provider configuration per profile

Every named profile (`assistant`, `operations`, `supervisor`) is rendered from the declarative scaffold in `packages/hermes-image/nixos-module.nix`. To change the provider backends manually after the server/container is running:

1. Edit `packages/hermes-image/nixos-module.nix` inside the repo checkout.
2. Locate the `profileScaffold` map near the top and update `modelProvider` + `modelDefault` for the profile you want to customize. For example, to point `supervisor` at OpenRouter:

   ```nix
   profileScaffold.supervisor = profileScaffold.supervisor // {
     modelProvider = "openrouter";
     modelDefault = "openrouter/anthropic/claude-4o-mini";
   };
   ```

3. If a profile needs a different auxiliary base URL, API key, or fallback model, adjust the surrounding helper values (`auxiliaryBaseUrl`, `auxiliaryApiKeyRef`, `mkProfileConfig`’s `fallback_model` block) so the generated config reflects the desired provider (e.g., point `fallback_model` at `openrouter` or add a new `auxiliary` entry).
4. Add any new secret names (for example `OPENROUTER_API_KEY` or `CUSTOM_PROVIDER_KEY`) to the managed env-key lists in `packages/hermes-image/nixos-module.nix` so the bootstrap service knows to copy them into each profile `~/.hermes/profiles/<profile>/.env`. Supply the actual values via the container `environment`/`environmentFiles` or by exporting them before starting the container.
5. Rebuild the image (e.g., `nix build .#packages.x86_64-linux.ghostship-hermes-image`) and restart the container from the new build, or run `sudo nixos-rebuild switch` if you are on a full NixOS host. Because the bootstrap rewrites `/home/hermes/.hermes/profiles/<profile>/config.yaml`, manual edits to those files do not persist.

This keeps the provider wiring in Nix so every redeploy regenerates the same config and the services stay in sync.

- Router provider vars such as `OPENROUTER_API_KEY` and `OPENCODE_API_KEY` remain router-only, but the router now also accepts the Hermes-facing `OPENCODE_GO_API_KEY` alias so the Minimax fallback credential name can be shared between Hermes and the router

Upstream Hermes docs still apply for CLI behavior:

- <https://hermes-agent.nousresearch.com/docs/>
- <https://hermes-agent.nousresearch.com/docs/getting-started/nix-setup/>
- <https://hermes-agent.nousresearch.com/docs/reference/cli-commands>

## Ghostship Utilities

The image still bundles the repo-managed service CLIs:

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

`ghostship-chaptarr` integrates with a Chaptarr instance over `/api/<version>` and requires `CHAPTARR_URL`/`CHAPTARR_API_KEY` in the runtime environment; optional `CHAPTARR_API_PATH` and `CHAPTARR_API_VERSION` allow non-standard base paths.

All `ghostship-*` utilities emit native JSON by default. Canonical API docs and raw upstream mirrors live under `docs/api/`.

## Hermes Router

The image now includes a standalone local router service:

- listen address: `127.0.0.1:8788`
- systemd unit: `ghostship-hermes-router.service`
- model aliases: `auxiliary`, `coding`, `agentic`, `vision`, `tts`
- Hermes-compatible health endpoints: `GET /health`, `GET /v1/health`
- router health endpoints: `GET /healthz`, `GET /readyz`
- primary OpenAI-style endpoints: `GET /v1/models`, `POST /v1/chat/completions`, `POST /v1/responses`, `GET /v1/responses/{id}`, `DELETE /v1/responses/{id}`
- streaming contract: `chat/completions` SSE plus Hermes/OpenAI SDK-compatible `responses.stream(...)`
- metrics endpoint: `GET /metrics`
- debug endpoints: `GET /debug/state`, `GET /debug/events`, `GET /debug/providers`, `GET /debug/routes/{alias}`, `GET /debug/rankings/{alias}`, `GET /debug/models/{provider}/{model}`
- persistent state: `/home/hermes/.local/state/ghostship-hermes/router/router.db`
- inventory sources: OpenRouter and OpenCode Zen
- Zen enrichment: when a Zen model confidently matches an OpenRouter model id after normalization, the router reuses OpenRouter description, created timestamp, and modality/tool metadata for Zen scoring
- Zen request families: `/chat/completions`, `/responses`, `/messages`, and Google-style model endpoints are normalized back into the local `chat/completions` surface
- routing state: model-level health, provider-level health, cooldown, ranking, failover, total latency, best-effort first-text latency, durable overrides, stored `responses`, and lightweight chat session continuity
- startup behavior: the router serves the last persisted inventory and rankings immediately when they exist; otherwise it stays unready until the first background discovery pass completes
- ranking worker: a healthy free OpenCode Zen text model is preferred for coarse ranking and selective reranking outside the request hot path, with OpenRouter fallback
- routing filter: when provider metadata exposes modalities and supported parameters, `coding`, `agentic`, and `auxiliary` require tool calling with text output, `vision` requires image or video input with text output, and `tts` requires speech-style audio output while excluding music-generation models such as Lyria
- recency bias: newer models get a strong score lift after free-only and capability filters, but alias-specific family preference now comes from relative rank bonuses among the families that are actually present, with exact id/name family matches beating description-only hints
- size bias: `coding`, `agentic`, and `vision` apply a modest global size-rank bonus for models with parsed parameter counts, and only apply a smaller-model penalty when a larger sibling exists in the same family or a more specific inferred subfamily; `auxiliary` keeps a smaller-is-better size penalty so helper lanes stay compact
- override controls: provider and model disablement, provider and model weight overrides, and alias pinning
- optional auth: `GHOSTSHIP_ROUTER_API_KEY`, `API_SERVER_KEY`, or `OPENAI_API_KEY`
- optional browser CORS allowlist: `GHOSTSHIP_ROUTER_CORS_ORIGINS` or `API_SERVER_CORS_ORIGINS`

Outside the container, standalone router runs default state to `${XDG_STATE_HOME:-~/.local/state}/ghostship-hermes/router` unless `GHOSTSHIP_ROUTER_STATE_DIR` or `GHOSTSHIP_ROUTER_DB_PATH` is set.

Router-only runtime env (separate from the current Hermes scaffold):

- `GHOSTSHIP_ROUTER_RANKING_ENABLED`
- `GHOSTSHIP_ROUTER_RANKING_INTERVAL`
- `GHOSTSHIP_ROUTER_RANKING_WORKER_MODEL`
- `GHOSTSHIP_ROUTER_RANKING_SHORTLIST_SIZE`
- `GHOSTSHIP_ROUTER_ROLLING_WINDOW_SECONDS`
- `GHOSTSHIP_ROUTER_PROVIDER_COOLDOWN_SECONDS`
- `GHOSTSHIP_ROUTER_PROVIDER_FAILURE_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_RATE_LIMIT_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_TIMEOUT_THRESHOLD`
- `GHOSTSHIP_ROUTER_PROVIDER_EXHAUSTION_THRESHOLD`
- `GHOSTSHIP_ROUTER_ASSISTED_BUCKET_MODEL`
- `GHOSTSHIP_ROUTER_ASSISTED_BUCKET_BATCH_SIZE`
- `GHOSTSHIP_ROUTER_DISABLED_PROVIDERS`
- `GHOSTSHIP_ROUTER_DISABLED_MODELS`
- `GHOSTSHIP_ROUTER_PROVIDER_WEIGHT_OVERRIDES`
- `GHOSTSHIP_ROUTER_MODEL_WEIGHT_OVERRIDES`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_AUXILIARY`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_CODING`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_AGENTIC`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_VISION`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_TTS`

If `GHOSTSHIP_ROUTER_ASSISTED_BUCKET_MODEL` or `GHOSTSHIP_ROUTER_RANKING_WORKER_MODEL` is set, it must resolve to a healthy free model ID from the current router inventory.

Hermes OpenAI-compatible endpoint compatibility:

- use `base_url: http://127.0.0.1:8788/v1`, or bare `http://127.0.0.1:8788` if you prefer
- use a router alias like `coding`, `vision`, `tts`, or `auxiliary` as the model id
- if router auth is enabled, Hermes can send the same bearer token through `OPENAI_API_KEY`

## Local Validation

Build the publishable image bundle and the low-level rootfs locally:

```fish
mkdir -p .nix-local-store
set store "local?root=$PWD/.nix-local-store/nix"
nix build --store $store .#packages.x86_64-linux.hermes-dashboard .#packages.x86_64-linux.ghostship-hermes-image .#packages.x86_64-linux.ghostship-hermes-rootfs -L
set image_bundle (nix path-info --store $store .#packages.x86_64-linux.ghostship-hermes-image)
set rootfs_output (nix path-info --store $store .#packages.x86_64-linux.ghostship-hermes-rootfs)
set rootfs_tar (find $rootfs_output -type f -name '*.tar.xz' | head -n 1)
```

On `x86_64` hosts, keep arm64 validation at derivation-evaluation scope:

```fish
nix eval .#packages.aarch64-linux.ghostship-hermes-image.drvPath --raw
```

Full `aarch64-linux` publishable image builds require an arm64-capable runner or
builder. The GitHub `publish-image` workflow uses `ubuntu-24.04-arm` for the
arm64 release leg and keeps x86-host validation paths at `nix eval`.
The scheduled `update-hermes-release` workflow tracks the upstream
`NousResearch/hermes-agent` release feed, updates the pinned flake input and
lockfile when a new tag lands, and then explicitly dispatches
`publish-image.yml` so the new Hermes build is published even though the pin
bump commit itself is created by GitHub Actions.
Inside a running container, the `hermes` user tooling refresh path keeps an
offline bootstrap package for first boot, but refreshes Hermes itself from
`github:caelx/ghostship-hermes#hermes-agent-wrapped` by default so an already
built image can move forward to the latest wrapped Hermes package without
replacing the whole container image. That managed Nix toolchain now lives in
`/home/hermes/.local/state/nix/profiles/ghostship-managed`, which avoids
collisions with older or operator-owned entries in `~/.nix-profile`. Override
that source with `GHOSTSHIP_HERMES_RUNTIME_FLAKE_REF` if you need to point at a
fork or branch.

Image output contract:

- `hermes-dashboard` is the direct packaged MMX dashboard artifact used by the image runtime.
- `ghostship-hermes-image` is the explicit publishable image bundle consumed by `scripts/export_publishable_image.sh`, the GHCR publish workflow, and the dashboard smoke test.
- `ghostship-hermes-rootfs` is the lower-level NixOS rootfs tarball used for `/init`-oriented persistence validation.

Run the dashboard smoke test:

```fish
# Run this from a shell where ../../.envrc has already exported
# OPENROUTER_API_KEY and OPENCODE_API_KEY for the local router.
bash tests/hermes-image/profiles-dashboard.sh $image_bundle ghostship-hermes:assistant-ops-supervisor
```

The dashboard smoke test no longer bind-mounts `/nix` by default. If you need
to exercise a persisted host store explicitly, set
`GHOSTSHIP_TEST_BIND_NIX=1 GHOSTSHIP_NIX_VOLUME_ROOT=...`.

Run the full persistence validation:

```fish
set -a
source ../../.envrc >/dev/null 2>&1
GHOSTSHIP_ROOTFS_TAR="$rootfs_tar" GHOSTSHIP_NIX_VOLUME_ROOT="$PWD/.nix-local-store/nix/nix" bash scripts/validate_workstation_persistence.sh
```

The persistence suite validates:

- `HERMES_HOME=/home/hermes/.hermes`
- `HOME=/home/hermes`
- `hermes` runs as `3000:3000`
- the root Hermes config uses `http://127.0.0.1:8788/v1` with `coding`
- `assistant`, `operations`, and `supervisor` are present under `~/.hermes/profiles/...`
- the current scaffold gives each profile a direct `openai` provider placeholder with `gpt-5.4`
- `/home/hermes` itself is the persisted home volume
- the NixOS unit graph comes up in the expected order for storage, profile bootstrap, the router, the two profile gateways, and the dashboard
 - no repo-managed default skills are seeded by default
- optional shared and profile skill trees staged under `/home/hermes/seeds/...` are copied once without overwriting existing Hermes-managed skill directories
- removed workstation tools other than `gws`, `gcloud`, `gh`, and approved OpenSSH client tools are absent by default
- `ghostship-*` utilities remain available
- HOME-backed state survives container replacement
- `nix profile install` survives container replacement with reused `/nix`
- later-installed tool state remains updateable
- `opencode` install plus XDG state survives replacement
- the dashboard can open and close an ephemeral terminal before and after replacement
- the dashboard can manage multiple independent terminal tabs
- switching between open tabs keeps the live terminal session attached
- the bootstrap `assistant`, `operations`, and `supervisor` profiles are available under `~/.hermes/profiles/...`
- the router alias inventory exposes `auxiliary`, `coding`, `agentic`, `vision`, and `tts`

Router package validation:

```fish
cd packages/hermes-router
uv sync --extra dev
.venv/bin/python -m pytest -q
set -a
source ../../.envrc >/dev/null 2>&1
.venv/bin/python -m hermes_router.app
```

## Python Utility Workflow

For the standardized Python utility workflow, see [docs/python-utilities.md](docs/python-utilities.md).
