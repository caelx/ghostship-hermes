# Agent Directives: ghostship-hermes

## Purpose

- Build and publish `ghcr.io/caelx/ghostship-hermes`.
- Treat this repo as a monorepo for the Hermes workstation image, Ghostship Router, and supporting runtime packages.

## Project Invariants

- Base image is `ubuntu:24.04`.
- PID 1 is `s6-overlay`.
- Hermes runs as non-root `hermes` (`3000:3000`).
- `HOME=/home/hermes` is the canonical persisted state root.
- `HERMES_HOME=/home/hermes/.hermes`.
- `/workspace` is the separate persisted work-products mount.
- `/nix` persists user-installed Nix packages across container replacement.
- Hermes core lives in `/opt/hermes` and is image-owned.
- Router lives in `/opt/ghostship-router` and is image-owned.
- Dashboard is upstream Hermes `0.9` with one repo-owned `Terminal` entry patch.
- `ttyd` is a sidecar service, not a native Hermes PTY implementation.
- Router is mandatory.
- Discord forced-channel routing is mandatory.
- The only repo-owned Hermes patches are:
  - Discord Codex-pinned channel
  - dashboard `Terminal` entry
- Do not add extra Hermes service/doctor compatibility patches unless upstream behavior changes and there is no cleaner workaround.
- Do not use `hermes gateway install` inside the container runtime. `s6` owns service supervision.
- Use Cloudflare Access or another outer layer for access control. Do not add in-container basic auth.
- Keep repo-owned runtime commands prefixed with `ghostship-`.

## Build And Test Commands

```fish
docker build --build-arg HERMES_REF=(string trim < packages/hermes-image/hermes-release.txt) --tag ghostship-hermes:dev --file packages/hermes-image/Dockerfile .
tests/hermes-image/single-agent-dashboard.sh ghostship-hermes:dev
```

## CI And Release Hygiene

- Build on every push and PR.
- From `main`, publish `latest`, `sha-*`, and `hermes-*` tags.
- For non-`main` `workflow_dispatch`, publish only immutable `sha-*` tags.
- Build and publish both `amd64` and `arm64`.
- Keep `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `.github/` metadata current with the workstation-image contract.

## Durable Lessons

### Hermes Runtime

- Hermes `0.9` has an upstream web dashboard. Use that as the primary browser surface.
- The runtime is a workstation container, not a NixOS module container. Hermes state is user-owned under `/home/hermes/.hermes`.
- The correct service split is Docker for container lifecycle and `s6` for in-container supervision.
- `terminal.backend: local` is the right backend for this image. Nested Docker terminal sandboxes are the wrong model here.
- Hermes core must stay outside `/home/hermes`; keep it in `/opt/hermes` so replacing the image actually replaces Hermes.
- Downstream persistence contract is `/home/hermes`, `/workspace`, and `/nix`.
- Empty persisted `/nix` volumes are safe because the cont-init phase seeds `/nix` from `/opt/ghostship/nix-seed.tar.zst` on first boot.
- Reused non-empty `/nix` volumes must be reconciled on boot with the image-managed default Nix profile at `/nix/var/nix/profiles/per-user/hermes/ghostship-defaults`; do not rely on raw `/opt/ghostship/bin -> /nix/store/...` symlinks for image-managed defaults.
- Persisting `/home/hermes` preserves Hermes config, Codex auth, npm CLIs, XDG state, and other tool state in the way workstation users expect.
- Upstream bundled Hermes skills must be copied into the image home seed under `.hermes/skills`; `hermes skills list` alone does not seed them. Use file-granular seeding so downstream custom skills survive while missing defaults are added.
- Treat `HOME`, `HERMES_HOME`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME`, `NPM_CONFIG_PREFIX`, `CARGO_HOME`, `RUSTUP_HOME`, `GHOSTSHIP_WORKSPACE_ROOT`, `GHOSTSHIP_WEB_PORT`, `GHOSTSHIP_DASHBOARD_HOST`, `GHOSTSHIP_DASHBOARD_PORT`, `GHOSTSHIP_ROUTER_HOST`, `GHOSTSHIP_ROUTER_PORT`, `GHOSTSHIP_ROUTER_URL`, `GHOSTSHIP_NIX_DEFAULT_PROFILE`, `GHOSTSHIP_TTYD_SOCKET`, `GHOSTSHIP_TTYD_BASE_PATH`, and `GHOSTSHIP_TERMINAL_CWD` as internal image-owned variables. Do not expose them as downstream-facing env knobs and do not override them from runtime env.
- `nix` itself must stay reachable even when `/home/hermes` is replaced by a fresh persisted mount. Keep `/usr/local/bin/nix` symlinked to the installed binary.
- Upstream `hermes gateway status` shells out to `ps eww -ax -o pid=,command=`. Ubuntu `procps` rejects that exact argument order in this container. Keep the narrow `/usr/local/bin/ps` wrapper that rewrites only that invocation to `ps axeww -o pid=,command=`.
- `ttyd` should bind a unix socket under `/run/user/3000`, not `/run`, because the runtime service runs as `hermes`.
- `ttyd` should be backed by `tmux new -A -s webterm` so browser reconnects do not kill the terminal session.
- Keep ttyd styling aligned to the dashboard palette.
- Bind the public web surface to `0.0.0.0:7681`, but keep internal dashboard and router listeners on localhost.
- Hermes browser tools should use the stock local `agent-browser` lane by exposing native CloakBrowser as the standard `google-chrome` binary that `agent-browser` already probes on Linux.
- Build-time image prep must install native CloakBrowser under `/opt/ghostship` and prefetch its browser binary so runtime launches do not depend on first-boot network access.
- The wrapper at `/usr/local/bin/google-chrome` must inject CloakBrowser's default stealth args on each launch, default raw Chrome calls to `/home/hermes/.local/state/cloakbrowser` only when callers omit `--user-data-dir`, preserve explicit `--user-data-dir` values, and default Chrome to `--log-level=3` unless the caller supplies a log level.
- The wrapper must drop `--disable-extensions` by default so managed uBlock Origin Lite policy still applies even when browser automation supplies extension-disabling Chromium defaults.
- Do not set image-wide `AGENT_BROWSER_PROFILE` or wrap `agent-browser`; native `agent-browser --session` must control its own profile/session behavior.
- Fresh homes must pre-create `/home/hermes/.local/state/cloakbrowser` as `hermes`; browser launches must not leave root-owned state behind in that tree.
- Managed Chrome/Chromium policy must force-install uBlock Origin Lite for CloakBrowser and smoke-test actual ad-network blocking, not just extension installation.
- Upstream Hermes `web/src/App.tsx` ships in three currently supported released shapes: the older static nav/page map, the intermediate `BUILTIN_NAV` plus explicit `<Route>` layout, and the newer `BUILTIN_ROUTES` plus `BUILTIN_NAV` route-table layout. Keep `prepare_upstream_hermes.py` patching all three shapes so upstream dashboard bumps do not break the image build.
- Upstream Hermes `gateway/run.py` currently ships in two supported `_resolve_turn_agent_config` shapes: the older smart-routing helper and the newer direct runtime/route builder. Keep `prepare_upstream_hermes.py` patching both shapes so the Codex-pinned Discord channel behavior survives Hermes pin bumps.
- Install high-backtracking upstream Hermes extras in the Dockerfile with `uv pip` plus constraints; broad messaging, matrix, Daytona, OpenTelemetry, Alibaba/DingTalk, Mistral, and related ranges can make pip hit `resolution-too-deep` before it finds valid leaves.
- Do not install upstream Hermes in the Dockerfile base stage; the final stage owns the repo-patched Hermes install, and duplicating it doubles resolver/build exposure.
- Build `tirith` from the repo flake's pinned `.#tirith` package, not from ad-hoc `nixpkgs#tirith`, so exact-source Docker builds stay deterministic and do not depend on live `nixpkgs-unstable` GitHub API lookups.
- When the workstation smoke fails after the browser block, dump the concrete `/home/hermes` non-hermes ownership list and the CloakBrowser profile tree, otherwise CI hides the actual failing late-stage check.
- The managed Hermes runtime primary lane is `custom:ghostship-router/deepseek-v4-pro`, fallback is `custom:ghostship-router/minimax-m2.7`, and managed agent defaults are `reasoning_effort = "high"` and `max_turns = 500`.
- The image-managed Bitwarden tool is the Password Manager CLI `bw`; persist its state under `/home/hermes/.local/state/bitwarden-cli` with `BITWARDENCLI_APPDATA_DIR`. Higher-level Bitwarden workflow helpers are model-authored, not image-owned.
- Export `BITWARDENCLI_APPDATA_DIR` at the image/global env layer too; raw `bw` commands otherwise fall back to `~/.config/Bitwarden CLI`.
- Hermes runtime env passthrough should default-allow downstream vars and exclude only image-owned or other-service-only env; do not maintain Hermes plugin env allowlists.
- Managed Hermes-facing env must be emitted to both `/run/ghostship/hermes.env` and `/home/hermes/.hermes/.env`; preserve unrelated persisted `.env` keys while refreshing the managed subset from current runtime env.
- The router service must hard-code its image-owned `127.0.0.1:8788` bind target; do not let downstream `GHOSTSHIP_ROUTER_HOST` or `GHOSTSHIP_ROUTER_PORT` runtime env move it.

### Discord Routing

- `DISCORD_HOME_CHANNEL` is part of the downstream Discord contract and should point at `#assistant`.
- `GHOSTSHIP_CODEX_CHANNEL` pins `#foodstamps` replies to `openai-codex/gpt-5.5`, including replies in Discord threads whose parent channel is `#foodstamps`.
- `DISCORD_FREE_RESPONSE_CHANNELS` is part of the downstream Discord contract and must include the `#foodstamps` Codex-pinned channel.
- `DISCORD_WEBHOOK_CHANNEL` is part of the downstream Discord contract and defaults Hermes-created Discord webhook subscriptions to `#webhooks`.
- The Codex-pinned forced channel must ignore per-session `/model` overrides.
- Keep the managed Discord defaults at `require_mention = false` and `reactions = false`. Do not flip them back unless the user explicitly changes the contract.
- `DISCORD_REACTIONS=false`, `DISCORD_REQUIRE_MENTION=false`, and `DISCORD_AUTO_THREAD=true` are image-owned defaults. Treat them as optional for downstream and do not make downstream set them unless the contract changes.
- The managed gateway retires closed Discord thread sessions after 05:00 local Hermes time by removing only the live `sessions.json` mapping and preserving SQLite transcripts.
- The forced Codex channel depends on persisted Codex OAuth in `/home/hermes/.hermes/auth.json`.
- Do not use `OPENAI_API_KEY` anywhere in this repo's active runtime contract.
- Do not expose router auth as a downstream env knob. If Hermes uses a router token, keep it internal as an underscore-prefixed env such as `_GHOSTSHIP_ROUTER_API_KEY`; the router itself must treat that auth as optional.

### Router Policy

- `NVIDIA_BUILD_API_KEY` enables the repo-owned `nvidia-build` provider.
- `ZENMUX_API_KEY` enables the repo-owned `zenmux` free-provider lane; default RPM is 10.
- `ELECTRON_HUB_API_KEY` enables the repo-owned `electron-hub` free-provider lane; default RPM is 5.
- NVIDIA free inventory discovery should use the filtered `build.nvidia.com/models?filters=nimType%3Anim_type_preview` catalog page and dedupe repeated model ids before persisting inventory.
- Normal router routing exposes OpenCode Go model IDs only when explicit free-provider equivalents are configured.
- Free providers route only through explicit equivalence entries for an exposed OpenCode Go model id.
- Free-provider lanes must still classify individual backend models by actual free metadata or `:free`/`-free` ids; do not force all models on ZenMux/OpenCode Zen/Electron Hub to free.
- Normal routing must not use alias/family/top-five reserve selection. Use only the requested OpenCode Go model id's explicit equivalence table.
- Default free-provider RPMs are NVIDIA Build 30, OpenCode Zen 30, ZenMux 10, Electron Hub 5, and OpenRouter 20.
- Candidate selection is RPM-weighted deficit round robin across eligible free equivalents, adjusted by shape-aware health and bounded free-provider timeouts, then `opencode-go/<same model id>` as paid fallback.
- Router health must include Hermes request shape and message-count size; large `stream+tools+tool_history+reasoning` failures must not poison simple text traffic or other OpenCode Go fallback models.
- Provider-origin route failures should surface as non-retryable `424`; reserve router `400` for local request validation failures before routing.
- Fast route exhaustion with no eligible candidates must still create a sanitized `router`/`route_exhausted` route event so live 424s can be debugged after the request.
- Post-attempt route exhaustion must also create a sanitized `router`/`route_exhausted` route event with attempted providers, attempt errors, and skipped fallback reasons.
- OpenCode-compatible providers need assistant tool-call history arguments normalized to JSON-object strings before upstream calls.
- `opencode-go` is the canonical model catalog and paid fallback; it is never counted as a free provider.

### Packaging Split

- Image-owned layer is Hermes core plus true runtime dependencies only.
- Prefer the utility's native package manager when one is the expected upstream install path.
- Persisted `/nix` has two lanes: an image-managed default profile for baseline Nix tools and the user-managed `/home/hermes/.nix-profile` for extra installs.
- Native CloakBrowser should be image-owned under `/opt/ghostship`, while the persisted browser profile root lives under `/home/hermes/.local/state/cloakbrowser`.
- Use the same iframe sandbox policy for the live browser tab as the terminal tab: `allow-same-origin allow-scripts allow-forms`, no modal permission.
- Node-native CLIs such as `codex`, `gemini-cli`, `agent-browser`, and `opencode` belong in npm under `/home/hermes`.
- Avoid convenience-driven image bloat. If a binary is not required by boot, supervision, router, dashboard, ttyd, native Hermes runtime, or upstream doctor/runtime expectations, move it out of base.

### Testing

- Live validation on `chill-penguin` is the real deployment proof path.
- Router changes need Hermes-shaped replay tests with tool history, reasoning, streaming, and fallback behavior before publish; direct provider smoke alone is not enough.
- Rootless Podman on `chill-penguin` can hand `pasta` an already-occupied published host port during rapid recreate tests, even when the host port is auto-assigned. The workstation smoke should let the container engine choose the published port, query the selected port after startup, and retry recreate startup on `Address already in use`.
- After container restart or recreation, dashboard `/api/status` can return before the persisted hermes user Nix profile is fully callable again. The workstation smoke should retry a user-profile command such as `hello` separately instead of assuming API readiness implies `~/.nix-profile` readiness.
- On GitHub Actions Docker runners, the host-published random dashboard port can flap across container restart even while the in-container dashboard at `127.0.0.1:7681` is healthy. Keep the external host-port assertion on initial startup, but use container-internal dashboard readiness checks for restart and recreate persistence phases.
- The smoke test should cover:
  - dashboard `/api/status`
  - router readiness
  - terminal path `/terminal/`
  - native local browser launch against the dashboard origin `/`
  - native `hermes gateway status`
  - `hermes doctor` as far as upstream supports without repo shims
  - browser profile persistence across restart and full container recreation at `/home/hermes/.local/state/cloakbrowser`
  - persistence across restart and full container recreation for `/home/hermes`, `/workspace`, and `/nix`
- Browser persistence smoke should write and read durable state from the public dashboard origin `127.0.0.1:7681` with `localStorage`; do not use `/api/status` or session cookies as the persistence proof. Drive the image-owned `google-chrome`/CloakBrowser wrapper directly for this probe because `agent-browser open` can wait too long in CI.

### Retired Utility Platform

- The old shared `ghostship-cli-contract` package and service-specific `ghostship-*` Python CLIs are retired from active repo/image support.
- Do not reintroduce baked service API wrappers unless the user explicitly asks for a new supported image-owned tool.
