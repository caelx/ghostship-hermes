# ghostship-hermes

`ghostship-hermes` builds and publishes `ghcr.io/caelx/ghostship-hermes`, a lean NixOS-based Hermes container image aligned to the upstream Hermes NixOS module with a repo-approved whole-home persistence model.

Canonical image references:

- Pull ref: `ghcr.io/caelx/ghostship-hermes`
- GitHub package page: <https://github.com/caelx/ghostship-hermes/pkgs/container/ghostship-hermes>

## Runtime Model

- Hermes is configured declaratively through the upstream Hermes NixOS module.
- `HERMES_HOME=/home/hermes/.hermes`
- `HOME=/home/hermes`
- `/home/hermes` is the canonical persisted runtime mount.
- `/workspace` remains the separate persisted work-products mount.
- `/nix` should be persisted when mutable `nix profile install`, `nix shell`, or build outputs must survive container replacement.
- The runtime user is `hermes` at `3000:3000`.
- The public browser surface is a HUDUI-aligned dashboard on port `7681`.
- The published image advertises `STOPSIGNAL SIGRTMIN+3` so container shutdown reaches the inner `systemd` PID 1 correctly.
- The dashboard exposes HUDUI tabs for runtime inspection and adds one Ghostship-specific `Console` tab backed by on-demand same-origin `ttyd`.
- Browser terminals start in `/workspace`.
- The image now exposes one managed Hermes agent, not a repo-owned profile fleet.
- The managed config lives at `/home/hermes/.hermes/config.yaml`, the managed env file at `/home/hermes/.hermes/.env`, the managed auth file at `/home/hermes/.hermes/auth.json`, the managed skill tree at `/home/hermes/.hermes/skills`, the managed prompt at `/home/hermes/.hermes/SOUL.md`, and the managed gateway liveness marker at `/home/hermes/.hermes/gateway.pid`.
- The primary model path is direct MiniMax on OpenCode Go: `provider = opencode-go`, `default = minimax-m2.7`.
- The fallback model is Codex OAuth on `openai-codex/gpt-5.4-mini`.
- The local router is exposed separately as one named Hermes custom provider, `ghostship-router`, pointing at `http://127.0.0.1:8788/v1` with `OPENAI_API_KEY` as the router bearer token.
- Auxiliary and compression tasks still use Gemini 3.1 Flash-Lite Preview through the Google OpenAI-compatible endpoint, and the managed router still blocks the exact backend id `openrouter/free` from route selection.

Upstream note:

- This image intentionally deviates from the upstream container-mode split between state and HOME.
- Upstream normally keeps managed state under `${stateDir}/.hermes` with a separate home directory.
- Here, the repo sets `stateDir = "/home/hermes"`, so the managed Hermes home lives inside the persisted home mount.

This image intentionally does not ship the old Ghostship workstation layer. Google Workspace support stays CLI-only: `gws` is preinstalled on `PATH`, but the image does not vendor or seed Google Workspace skills. The default image also preinstalls `gcloud`, `gh`, `ssh`, `scp`, and `ssh-keygen` from `nixpkgs`. `blog` is not part of that baked image CLI exception set; it is installed through the managed Hermes-user profile.

The immutable image no longer tries to be the full operator workstation layer. Instead, boot-time runtime convergence reconciles the repo-owned persisted user-layer runtime contract under `/home/hermes`, removing stale managed entries and reapplying the current image-owned toolchain/config state on replacement:

- user Nix profile tools: `hermes`, `git`, `gh`, `ssh`, `scp`, `ssh-keygen`, `curl`, `jq`, `nix`, `ripgrep`, `fd`, `uv`, `yq`, `tmux`, `blog`, `python3`, `pip`, `node`, `npm`
- managed Python contract: `python3`, `pip`, and `python3 -m pip` all resolve from the same managed Nix profile environment
- npm-managed agent CLIs: `codex`, `gemini`, `opencode`
- image-managed browser CLI: `agent-browser`

The immutable image stays focused on boot, supervision, and the repo-owned runtime surface:

- NixOS/container runtime
- `ttyd`
- `tirith`
- `ghostship-hermes-router`
- packaged HUDUI dashboard
- all `ghostship-*` utilities

Boot-time runtime convergence re-applies the repo-owned mutable toolchain and config surface under `/home/hermes` on replacement:

- user Nix profile tools: `hermes`, `git`, `gh`, `ssh`, `scp`, `ssh-keygen`, `curl`, `jq`, `nix`, `ripgrep`, `fd`, `uv`, `yq`, `tmux`, `blog`, `python3`, `pip`, `node`, `npm`
- managed Python contract: `python3`, `pip`, and `python3 -m pip` all resolve from the same managed Nix profile environment
- npm-managed agent CLIs: `codex`, `gemini`, `opencode`
- image-managed browser CLI: `agent-browser`

## Persistent Paths

Canonical persistent roots:

- `/home/hermes`
- `/home/hermes/.hermes`
- `/workspace`
- `/nix`

Persisting the whole home mount keeps browser and agent tooling state durable across container replacement. That includes XDG state, `~/.agents`, `~/.agent-browser`, `~/.codex`, `~/.copilot`, `~/.npm`, `~/.bun`, `~/.ssh`, `~/.gnupg`, and future tool state created under `/home/hermes`.

## `/home/hermes` Layout

Inside the running container:

- `/home/hermes` is both the interactive home directory and the persisted state mount
- `/home/hermes/.hermes` is the single managed Hermes runtime surface
- `/home/hermes/seeds/skills/<skill>/...` is the optional repo-seeded skill source tree, copied into `/home/hermes/.hermes/skills/<skill>` on first boot
- `/home/hermes/seeds/SOUL.md` is the optional repo-seeded prompt source
- `/workspace` remains the separate persisted work directory

The repo-specific deviation is that the managed NixOS-module state now lives inside the persisted home volume instead of a separate `/data` mount.

## Systemd Layout

The container uses a small NixOS-managed unit graph:

- `ghostship-storage.service`
  prepares `/home/hermes`, `/home/hermes/.hermes`, `/workspace`, and `/nix` before user-facing services start
- `hermes-agent.service`
  remains installed from the upstream Hermes NixOS module but is not started by default
- `ghostship-hermes-user-tooling.service`
  converges the repo-owned persisted user-layer runtime contract on boot, ensures the in-container Nix daemon is available first, repairs only drifted entries in the dedicated `/home/hermes/.local/state/nix/profiles/ghostship-managed` profile instead of removing and re-adding the full managed toolchain on every boot, reruns `npm install` only when the declared npm layer changed or required bins are missing, refreshes the managed npm CLIs and symlinks under `/home/hermes/.local/bin`, and does not own the main gateway startup dependency chain
- `ghostship-hermes-user-tooling-refresh.timer`
  reruns the mutable tooling refresh flow daily and once shortly after boot
- `ghostship-hermes-bootstrap.service`
  performs the single-agent managed-state convergence, deletes the old repo-owned profile tree during migration, rewrites `/home/hermes/.hermes/.env` atomically from the approved allowlist, seeds `/home/hermes/.hermes/skills` and `/home/hermes/.hermes/SOUL.md`, and mirrors `/etc/ghostship-hermes-release` into `/home/hermes/.ghostship-hermes-release`
- `hermes-gateway.service`
  is enabled as a real `systemd --user` service for `hermes`, auto-starts at boot without interactive login, keeps the one managed Hermes gateway running with `hermes gateway run --replace`, and now carries explicit upstream-aligned stop policy (`KillMode=mixed`, `KillSignal=SIGTERM`, `TimeoutStopSec=60s`)
- `ghostship-hermes-gateway-restart.path`
  runs in the Hermes user manager, watches `/home/hermes/.hermes/config.yaml` plus `.env`, and triggers a managed gateway restart only when those managed runtime inputs change; `auth.json` and `SOUL.md` remain durable managed state but are intentionally not automatic restart triggers
- `ghostship-hermes-startup.service`
  starts the HUDUI browser, router, the Hermes user manager, and the enabled `hermes-gateway.service` after storage preparation and bootstrap; a failed mutable tooling refresh must not block the main runtime boot
- `ghostship-hermes-hudui.service`
  serves the packaged HUDUI browser on port `7681`, watches `/home/hermes/.hermes` plus `/workspace`, and proxies the `Console` tab to on-demand ephemeral `ttyd` sessions
- `ghostship-hermes-router.service`
  runs the local model router on `127.0.0.1:8788`, persists router state under `/home/hermes/.local/state/ghostship-hermes/router`, and serves the approved alias set

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

- For Podman deployments that want the image-managed hostname and `/etc/hosts` contract, run the container with `--no-hostname --no-hosts` so Podman does not inject conflicting files into `/etc`.
- For systemd-as-PID-1 container shutdown, set the runtime stop signal to `SIGRTMIN+3` and use a stop timeout that covers inner `systemd` shutdown work rather than Podman's default 10 seconds.
- Reuse `/nix` only when it already contains compatible Nix state you want to keep. Do not hide a fresh Nix-built image behind a brand-new empty `/nix` volume.
- If you mount `/nix` to a persistent volume, prepopulate that volume with the image's `/nix` contents before first boot.
- Fix the per-user Nix ownership on the persisted volume before expecting mutable Nix workflows to work for `hermes`.
- Persisting `/home/hermes` directly is the intended way to keep Hermes managed state, XDG state, and later-installed agent tooling across container replacement.
- The dashboard is the intended browser entrypoint.
- The full managed env allowlist is documented in [docs/runtime-env.md](docs/runtime-env.md).
- The single-agent inputs are `DISCORD_BOT_TOKEN`, `DISCORD_ALLOWED_USERS`, `GHOSTSHIP_ROUTER_CHANNEL`, `DISCORD_HOME_CHANNEL`, `WEBHOOK_SECRET`, and `BROWSER_CDP_URL`.
- The required provider inputs are `OPENCODE_GO_API_KEY` for the primary MiniMax path, Codex OAuth in `/home/hermes/.hermes/auth.json` for the `openai-codex` fallback path, `OPENAI_API_KEY` for manual `ghostship-router` calls, and `GOOGLE_AI_STUDIO_API_KEY` for the direct auxiliary tasks. Gemini CLI is a separate npm-managed runtime tool and does not replace or configure that auxiliary provider path.
- If you are validating the local router, source the repo `.envrc` before `docker run` so the router can use `OPENROUTER_API_KEY` plus either `OPENCODE_API_KEY` or `OPENCODE_GO_API_KEY`.

After startup:

1. Open `http://localhost:7681`.
2. Use the HUDUI tabs to inspect health, projects, profiles, sessions, and the rest of the managed runtime surface.
3. Open the `Console` tab to start a same-origin shell-backed `ttyd` session rooted at `/workspace`.
4. Close the session from the `Console` tab when you want the backing `ttyd` process torn down.

Dashboard contract:

- The browser contract now follows HUDUI endpoints such as `/api/health`, `/api/profiles`, `/api/projects`, and `/api/console`.
- The HUDUI `Projects` panel is rooted at `/workspace`, and the root managed profile is rendered as `Managed Agent`.
- The published image now carries a store-stable container `HEALTHCHECK` that curls the dashboard with `curl` from its own store path instead of relying on `/run/current-system/sw/bin/curl` during early boot.
- Container-mode activation now disables root channel seeding and leaves Podman-managed `/etc/hosts` alone. The hostname contract remains explicit in Nix, so `/etc/hostname` cleanup still belongs in the host/runtime configuration if Podman continues injecting that file.
- OCI image metadata now includes `org.opencontainers.image.source` and `org.opencontainers.image.revision` in addition to the title, description, and version labels.

## Hermes Configuration

The image is declarative-first:

- Hermes managed config lives in `/home/hermes/.hermes`.
- The default runtime does not let Hermes self-apply the system flake.
- User-level Nix remains available for mutable runtime installs such as `nix profile install`, and the image uses a dedicated managed profile at `/home/hermes/.local/state/nix/profiles/ghostship-managed` to keep the baked `hermes` toolchain updateable on boot and during daily refreshes without colliding with the operator's default `~/.nix-profile`.
- The default Hermes-user PATH includes `/home/hermes/.local/bin`, `/home/hermes/.local/state/nix/profiles/ghostship-managed/bin`, and `/home/hermes/.nix-profile/bin` ahead of the fallback system toolchain so login shells and Hermes runtime commands discover the persisted mutable tool layers by default.
- The managed profile now also provides the repo-approved helper CLI set (`fd`, `uv`, `yq`, `tmux`, `blog`) plus a shared Python environment where `python3`, `pip`, and `python3 -m pip` all work without extra activation. That Python environment is installed at a higher Nix profile priority than `hermes-agent-wrapped` so both packages can coexist even though they both ship `bin/python`.
- Fast-moving agent CLIs continue to come from the persisted npm tooling project under `/home/hermes/.hermes/hermes-agent`; the supported set is `codex`, `gemini`, and `opencode`, while `agent-browser` remains the image-managed exception.
- The image keeps package docs, man pages, info pages, and NixOS docs available locally so Hermes can inspect in-image reference material.
- The managed config sets `timezone = "Pacific/Honolulu"`, `agent.max_turns = 110`, `agent.reasoning_effort = "high"`, `agent.verbose = false`, `memory.provider = holographic`, transcript compression, checkpoints, compact streaming display defaults, and `approvals.mode = "off"`.
- Browser defaults remain `cloud_provider = "local"`, `inactivity_timeout = 120`, `command_timeout = 30`, and `record_sessions = false`.
- `agent-browser` is the documented local-browser default unless an operator provides `BROWSER_CDP_URL`.
- Discord defaults remain `require_mention = true`, `auto_thread = false`, `reactions = true`, and `group_sessions_per_user = true`.
- The managed gateway always writes `/home/hermes/.hermes/gateway.pid`, and `hermes gateway status` now follows the upstream `systemd --user` `hermes-gateway.service` flow.
- The managed env file is `/home/hermes/.hermes/.env`. Bootstrap writes only the approved runtime allowlist into that file, omits unset values, always writes `WEBHOOK_ENABLED=true`, `WEBHOOK_PORT=8644`, and `TERMINAL_CWD=/workspace`, and intentionally excludes router/container plumbing plus the fixed Chaptarr and n8n path/version selectors.
- The full managed env contract, including every copied key and the intentionally excluded keys, is documented in [docs/runtime-env.md](docs/runtime-env.md).
- Seeded skills come from `/home/hermes/seeds/skills`, and the seeded prompt comes from `/home/hermes/seeds/SOUL.md`. Bootstrap copies missing skill directories only into `/home/hermes/.hermes/skills`, runs `hermes skills list` once to materialize the runtime skills hub, normalizes the full live skills tree to writable Hermes-owned runtime permissions, does not seed any `~/.hermes/profiles/...` tree, replaces the known unmanaged upstream default `SOUL.md` during single-agent migration, and only refreshes later seeded updates while the live file still matches the last seeded hash.

### Codex OAuth

The `openai-codex` provider path relies on Codex OAuth (device-code flow) instead of a static API key. Run `hermes model`, choose `OpenAI Codex`, and complete the login flow. Hermes stores that state in `/home/hermes/.hermes/auth.json`.

### Router Channel Guidance

If `GHOSTSHIP_ROUTER_CHANNEL` is set to a Discord channel ID, the managed gateway stages a supported advisory hook in `/home/hermes/.hermes/hooks/ghostship-router-channel-guidance`. That hook warns in the configured channel on normal message start and after `/reset` whenever the current session is not using a `ghostship-router` model selected through `/model`. The warning is advisory only, uses a bold heading, and includes one copy-paste `/model custom:ghostship-router:<model>` command for every model currently exposed by the local router.

### Skills Initialization

Bootstrap runs `hermes skills list` under the managed runtime user during startup so the skills hub directories and lockfile exist before the image begins serving traffic.

## Manual Provider Configuration

To change the managed agent provider defaults after the server/container is running:

1. Edit `packages/hermes-image/nixos-module.nix`.
2. Update `managedAgentConfig.model` for the primary router or direct-provider path.
3. Update the surrounding auxiliary and fallback values when the change needs a different direct endpoint or fallback model.
4. Add any new supported runtime env names to the managed allowlists so bootstrap can project them into `/home/hermes/.hermes/.env`.
5. Rebuild the image and restart the container. The root-managed runtime contract is re-applied on boot; do not rely on manual edits inside `/home/hermes/.hermes/config.yaml`.

This keeps the provider wiring in Nix so every redeploy regenerates the same config and the services stay in sync.

- Router-compatible provider vars such as `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `OPENCODE_API_KEY`, and `OPENCODE_GO_API_KEY` are part of the managed env allowlist; the local router can reuse them when the managed agent points at `http://127.0.0.1:8788/v1`.

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
arm64 release leg, keeps x86-host validation paths at `nix eval`, and only runs
automatically for image-affecting `main` pushes.
The scheduled `update-hermes-release` workflow tracks the upstream
`NousResearch/hermes-agent` release feed, updates the pinned flake input and
lockfile when a new tag lands, and then explicitly dispatches
`publish-image.yml` so the new Hermes build is published even though the pin
bump commit itself is created by GitHub Actions. The publish workflow path-gates
automatic runs and always publishes the final `ghostship-hermes` architecture
tags from the explicit `ghostship-hermes-image` bundle so the managed
runtime/systemd contract ships exactly as tested.
Inside a running container, the `hermes` user tooling refresh path keeps an
offline bootstrap package for first boot, but refreshes Hermes itself from
`github:caelx/ghostship-hermes#hermes-agent-wrapped` by default so an already
built image can move forward to the latest wrapped Hermes package without
replacing the whole container image. That managed Nix toolchain now lives in
`/home/hermes/.local/state/nix/profiles/ghostship-managed`, which avoids
collisions with older or operator-owned entries in `~/.nix-profile`. Override
that source with `GHOSTSHIP_HERMES_RUNTIME_FLAKE_REF` if you need to point at a
fork or branch.

Base/final layering:

- `ghostship-hermes-base` now carries the upstream Hermes runtime, the core container contract, the shared system/runtime toolchain (`bashInteractive`, `cacert`, `coreutils`, `curl`, `findutils`, `git`, `gh`, `gnugrep`, `gnused`, `jq`, `nix`, `nodejs_22`, `openssh`, `procps`, `ripgrep`, `tirith`, `ttyd`, and `util-linux`), the shared Python runtime dependency closure used across Ghostship services (`ghostship-cli-contract`, `httpx`, `typer`, `fastapi`, `uvicorn`, `websockets`, `pydantic`, `pydantic-core`, `starlette`, `click`, `shellingham`, `annotated-types`, `typing-extensions`, `typing-inspection`, `python-dotenv`, `python-multipart`, `watchfiles`, `urllib3`, `yarl`, `anyio`, `httpcore`, `certifi`, `charset-normalizer`, `idna`, `sniffio`, `aiohttp`, `aiohappyeyeballs`, `aiosignal`, `attrs`, `frozenlist`, `multidict`, and `propcache` from one overridden Python package set), and the stable external utility closures that would otherwise bloat every overlay (`agent-browser`, `bws`, `gcloud`, and `gws`).
- The repo-owned command surfaces stay in the final layer: `ghostship-hermes-router`, `ghostship-hermes-runtime`, `hermes-dashboard`, and the `ghostship-*` utilities are copied in through `/opt/ghostship-overlay` instead of living in the base closure. The shared `ghostship-cli-contract` library now lives in the base-side Python runtime closure with the other reused Python dependencies.
- The overlay bundle now skips any Nix store paths that are already present in the base closure. After the dependency audit, the realized overlay store paths are down to Ghostship-owned packages plus the small overlay assembly env, rather than re-copying shared Python libraries or stable external tool closures into that internal overlay artifact.

Image output contract:

GitHub Actions publication behavior:

- Every publish still rebuilds the explicit `ghostship-hermes-image` bundle on the runner host before export and GHCR publication.
- `publish-image` now treats `caelx/ghostship-cache` as a signed shared Nix binary cache. When a `cache-index` already exists, the workflow starts a runner-local `nixcache-oci` proxy before `nix build` and adds it as a substituter with the documented public key.
- On a cold cache with no published index yet, normal push builds still complete the uncached host-side build; cache refresh is gated to the daily scheduled `publish-image` run at `14:00 UTC` or an explicit `workflow_dispatch` run with `publish_shared_cache=true`.
- If the shared cache serves a trust or signature mismatch, the Nix build fails; the workflow does not disable signature verification.
- On a cache-refresh run, `publish-image` signs and uploads the locally built store paths captured by the pre-build dry-run planner into `ghcr.io/caelx/ghostship-cache/nix-cache`.
- The `ci` workflow still uses the official `uv` setup action with dependency-aware cache keys for the Python utility steps.
- Shared-cache setup, verification, and timing guidance now live in [docs/shared-nix-cache.md](docs/shared-nix-cache.md). The 2026-04-11 timing snapshot in [docs/github-actions-build-optimization.md](docs/github-actions-build-optimization.md) is the pre-shared-cache baseline.

- `hermes-dashboard` is the direct packaged MMX dashboard artifact used by the image runtime.
- `ghostship-hermes-image` is the explicit publishable image bundle consumed by `scripts/export_publishable_image.sh`, local image-loading flows, and the dashboard smoke test.
- `ghostship-hermes-rootfs` is the lower-level NixOS rootfs tarball used for `/init`-oriented persistence validation.

Run the dashboard smoke test:

```fish
# Run this from a shell where ../../.envrc has already exported
# OPENROUTER_API_KEY and either OPENCODE_API_KEY or OPENCODE_GO_API_KEY for the local router.
bash tests/hermes-image/single-agent-dashboard.sh $image_bundle ghostship-hermes:single-agent
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
- the root Hermes config uses `provider = opencode-go` with `default = minimax-m2.7`
- one managed agent is rooted at `~/.hermes`
- the managed config uses `provider = opencode-go`, `default = minimax-m2.7`, `fallback_model.provider = openai-codex`, and `fallback_model.model = gpt-5.4-mini`; the named `ghostship-router` custom provider points at `http://127.0.0.1:8788/v1` and the managed router disables the exact backend id `openrouter/free`
- `/home/hermes` itself is the persisted home volume
- the NixOS unit graph comes up in the expected order for storage, managed bootstrap, the router, the managed gateway, and the dashboard
 - no repo-managed default skills are seeded by default
- optional skill trees staged under `/home/hermes/seeds/skills/...` are copied once without overwriting existing Hermes-managed skill directories
- removed workstation tools other than `gws`, `gcloud`, `gh`, and approved OpenSSH client tools are absent by default
- `ghostship-*` utilities remain available
- HOME-backed state survives container replacement
- `nix profile install` survives container replacement with reused `/nix`
- later-installed tool state remains updateable
- `opencode` install plus XDG state survives replacement
- the dashboard can open and close an ephemeral terminal before and after replacement
- the dashboard can manage multiple independent terminal tabs
- switching between open tabs keeps the live terminal session attached
- the old repo-owned profile tree is removed during migration and does not reappear after replacement
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
