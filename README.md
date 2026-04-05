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
- The public browser surface is a minimal dashboard on port `7681`.
- The dashboard can launch as many ephemeral `ttyd` sessions as needed, tracks them as left-rail tabs, opens new tabs immediately with a loading state while `ttyd` starts, labels tabs from the shell cwd or current command, and returns to a blank home state when the active terminal is closed and no sessions remain.
- Switching between open tabs keeps each live `ttyd` session attached instead of dropping back to ttyd's reconnect prompt.
- Browser terminals start in `/home/hermes`.
- The image bootstraps two Hermes profiles, `operations` and `coder`, at `~/.hermes/profiles/...` and keeps a persistent gateway service running for each one.

Upstream note:

- This image intentionally deviates from the upstream container-mode split between state and HOME.
- Upstream normally keeps managed state under `${stateDir}/.hermes` with a separate home directory.
- Here, the repo sets `stateDir = "/home/hermes"`, so managed Hermes state and the CLI profile tree both live under `/home/hermes/.hermes` on the persisted home volume.

This image intentionally does not ship the old Ghostship workstation layer.

Removed from the default image:

- Codex
- Gemini CLI
- Opencode
- OpenSpec
- `skills`
- `gws`
- `bws`
- `feed`
- repo-managed skill seeding
- honcho compatibility wiring
- profile reconciler and persistent per-profile terminals
- app/update timers for mutable workstation tooling

Retained in the default image:

- upstream Hermes
- Nix runtime support
- `tirith`
- `ttyd`
- `ghostship-hermes-router`
- minimal dashboard controller
- all `ghostship-*` utilities

## Persistent Paths

Canonical persistent roots:

- `/home/hermes`
- `/home/hermes/.hermes`
- `/workspace`
- `/nix`

Persisting the whole home mount keeps later-installed coding agents and browser tooling persistent without preinstalling them in the base image. That includes XDG state, `~/.agents`, `~/.agent-browser`, `~/.codex`, `~/.gemini`, `~/.copilot`, `~/.npm`, `~/.bun`, `~/.ssh`, `~/.gnupg`, and any other future tool state created under `/home/hermes`.

## `/home/hermes` Layout

Inside the running container:

- `/home/hermes` is both the interactive home directory and the persisted state mount
- `/home/hermes/.hermes` is the managed Hermes service state written by the upstream NixOS module
- named profiles live under `/home/hermes/.hermes/profiles/operations` and `/home/hermes/.hermes/profiles/coder`
- `/workspace` remains a separate persisted work directory and is not folded into the home facade

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
- `ghostship-hermes-bootstrap.service`
  is a repo-specific NixOS oneshot that reconciles the approved `operations` and `coder` profiles after the managed Hermes config exists, writes their `.env` files from the runtime OpenRouter env, and sets the sticky default profile to `operations`
- `ghostship-hermes-profile-operations.service`
  keeps the `operations` gateway running with `hermes -p operations gateway run --replace`
- `ghostship-hermes-profile-coder.service`
  keeps the `coder` gateway running with `hermes -p coder gateway run --replace`
- `ghostship-dashboard-controller.service`
  serves the static dashboard and proxies on-demand ephemeral `ttyd` sessions on port `7681`
- `ghostship-hermes-router.service`
  runs the local model router on `127.0.0.1:8788`, persists router state under `/home/hermes/.local/state/ghostship-hermes/router`, and exposes OpenAI-style alias routing plus debug endpoints for local tools and Hermes profiles

The profile bootstrap unit and the two persistent per-profile gateway services are approved custom deviations from upstream. Upstream Hermes does not currently expose named profiles as a declarative NixOS-module option, so the profile names are declared in Nix here, materialized by a NixOS-managed oneshot, and then supervised by repo-managed systemd units.

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
- For local validation, source the repo `.envrc` before `docker run` so `OPENROUTER_API_KEY` and `OPENROUTER_TEST_MODEL` are passed into the bootstrap oneshot and written into the declared profiles.
- The local model router uses `OPENROUTER_API_KEY` and `OPENCODE_API_KEY` for live inference against OpenRouter and OpenCode Zen. Router-local validation does not depend on `OPENROUTER_TEST_MODEL`.

After startup:

1. Open `http://localhost:7681`.
2. Use `Open Terminal` to launch a new shell-backed `ttyd` session rooted at `/home/hermes`.
3. Each new terminal appears as a focused tab in the left rail immediately, even before the underlying `ttyd` process is ready.
4. Tab labels follow the active shell state, showing `/home/hermes` at the prompt and the current command name while work is running.
5. Use `Close Terminal` to remove the active tab. When no terminals remain, the dashboard returns to the blank home state.

## Hermes Configuration

The image is intentionally declarative-first:

- Hermes managed config is written into `/home/hermes/.hermes`.
- The default runtime does not let Hermes self-apply the system flake.
- User-level Nix remains available for mutable runtime installs such as `nix profile install`.
- The declared `operations` and `coder` profiles inherit the runtime `OPENROUTER_API_KEY` and `OPENROUTER_TEST_MODEL` values during bootstrap so both gateways come up with the same test provider configuration.

Upstream Hermes docs still apply for CLI behavior:

- <https://hermes-agent.nousresearch.com/docs/>
- <https://hermes-agent.nousresearch.com/docs/getting-started/nix-setup/>
- <https://hermes-agent.nousresearch.com/docs/reference/cli-commands>

## Ghostship Utilities

The image still bundles the repo-managed service CLIs:

- `ghostship-bazarr`
- `ghostship-changedetection`
- `ghostship-cloakbrowser`
- `ghostship-flaresolverr`
- `ghostship-grimmory`
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

All `ghostship-*` utilities emit native JSON by default.

## Hermes Router

The image now includes a standalone local router service:

- listen address: `127.0.0.1:8788`
- model aliases: `lightweight`, `coding`, `heavyweight`
- Hermes-compatible health endpoints: `GET /health`, `GET /v1/health`
- router health endpoints: `GET /healthz`, `GET /readyz`
- primary OpenAI-style endpoints: `GET /v1/models`, `POST /v1/chat/completions`, `POST /v1/responses`, `GET /v1/responses/{id}`, `DELETE /v1/responses/{id}`
- metrics endpoint: `GET /metrics`
- debug endpoints: `GET /debug/state`, `GET /debug/events`, `GET /debug/providers`, `GET /debug/routes/{alias}`, `GET /debug/rankings/{alias}`, `GET /debug/models/{provider}/{model}`
- persistent state: `/home/hermes/.local/state/ghostship-hermes/router/router.db`
- inventory sources: OpenRouter and OpenCode Zen
- Zen request families: `/chat/completions`, `/responses`, `/messages`, and Google-style model endpoints are normalized back into the local `chat/completions` surface
- routing state: model-level health, provider-level health, cooldown, ranking, failover, total latency, best-effort first-text latency, durable overrides, stored `responses`, and lightweight chat session continuity
- ranking worker: a healthy free model from the `lightweight` pool performs coarse ranking and selective reranking outside the request hot path
- override controls: provider and model disablement, provider and model weight overrides, and alias pinning
- optional auth: `GHOSTSHIP_ROUTER_API_KEY` or `API_SERVER_KEY`
- optional browser CORS allowlist: `GHOSTSHIP_ROUTER_CORS_ORIGINS` or `API_SERVER_CORS_ORIGINS`

Outside the container, standalone router runs default state to `${XDG_STATE_HOME:-~/.local/state}/ghostship-hermes/router` unless `GHOSTSHIP_ROUTER_STATE_DIR` or `GHOSTSHIP_ROUTER_DB_PATH` is set.

Optional runtime env for the router:

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
- `GHOSTSHIP_ROUTER_ALIAS_PIN_LIGHTWEIGHT`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_CODING`
- `GHOSTSHIP_ROUTER_ALIAS_PIN_HEAVYWEIGHT`

If `GHOSTSHIP_ROUTER_ASSISTED_BUCKET_MODEL` or `GHOSTSHIP_ROUTER_RANKING_WORKER_MODEL` is set, it must resolve to a healthy free model ID from the current router inventory.

## Local Validation

Build the publishable image bundle and the low-level rootfs locally:

```fish
mkdir -p .nix-local-store
set store "local?root=$PWD/.nix-local-store/nix"
nix build --store $store .#packages.x86_64-linux.ghostship-hermes-image .#packages.x86_64-linux.ghostship-hermes-rootfs -L
set image_bundle (nix path-info --store $store .#packages.x86_64-linux.ghostship-hermes-image)
set rootfs_output (nix path-info --store $store .#packages.x86_64-linux.ghostship-hermes-rootfs)
set rootfs_tar (find $rootfs_output -type f -name '*.tar.xz' | head -n 1)
```

Image output contract:

- `ghostship-hermes-image` is the explicit publishable image bundle consumed by `scripts/export_publishable_image.sh`, the GHCR publish workflow, and the dashboard smoke test.
- `ghostship-hermes-rootfs` is the lower-level NixOS rootfs tarball used for `/init`-oriented persistence validation.

Run the dashboard smoke test:

```fish
# Run this from a shell where ../../.envrc has already exported
# OPENROUTER_API_KEY and OPENROUTER_TEST_MODEL.
GHOSTSHIP_NIX_VOLUME_ROOT="$PWD/.nix-local-store/nix/nix" bash tests/hermes-image/profiles-dashboard.sh $image_bundle ghostship-hermes:ops-coder
```

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
- `operations` and `coder` are present under `~/.hermes/profiles/...`
- `/home/hermes` itself is the persisted home volume
- the NixOS unit graph comes up in the expected order for storage, profile bootstrap, the two profile gateways, and the dashboard
- no custom default skills are seeded
- removed workstation tools are absent by default
- `ghostship-*` utilities remain available
- HOME-backed state survives container replacement
- `nix profile install` survives container replacement with reused `/nix`
- later-installed tool state remains updateable
- `opencode` install plus XDG state survives replacement
- the dashboard can open and close an ephemeral terminal before and after replacement
- the dashboard can manage multiple independent terminal tabs
- switching between open tabs keeps the live terminal session attached
- the bootstrap `operations` and `coder` profiles are available under `~/.hermes/profiles/...`

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
