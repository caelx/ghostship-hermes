# Agent Directives: ghostship-hermes

## Purpose

- Build and publish `ghcr.io/caelx/ghostship-hermes`.
- Treat this repo as a monorepo for the Hermes workstation image and the `ghostship-*` Python CLIs.

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
  - Discord router-pinned channel
  - dashboard `Terminal` entry
- Do not add extra Hermes service/doctor compatibility patches unless upstream behavior changes and there is no cleaner workaround.
- Do not use `hermes gateway install` inside the container runtime. `s6` owns service supervision.
- Use Cloudflare Access or another outer layer for access control. Do not add in-container basic auth.
- Keep repo-owned utilities prefixed with `ghostship-`.
- All CLI utilities emit JSON by default.

## Build And Test Commands

```fish
python3 scripts/python_utility.py lock packages/searxng-cli
python3 scripts/python_utility.py test packages/searxng-cli
python3 scripts/python_utility.py build packages/searxng-cli
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
- Treat `HOME`, `HERMES_HOME`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME`, `NPM_CONFIG_PREFIX`, `CARGO_HOME`, `RUSTUP_HOME`, `GHOSTSHIP_WORKSPACE_ROOT`, `GHOSTSHIP_WEB_PORT`, `GHOSTSHIP_DASHBOARD_HOST`, `GHOSTSHIP_DASHBOARD_PORT`, `GHOSTSHIP_ROUTER_HOST`, `GHOSTSHIP_ROUTER_PORT`, `GHOSTSHIP_ROUTER_URL`, `GHOSTSHIP_NIX_DEFAULT_PROFILE`, `GHOSTSHIP_TTYD_SOCKET`, `GHOSTSHIP_TTYD_BASE_PATH`, `GHOSTSHIP_TERMINAL_CWD`, `CAMOFOX_URL`, `CAMOFOX_PORT`, `GHOSTSHIP_CAMOFOX_VNC_PORT`, `GHOSTSHIP_CAMOFOX_WEB_PORT`, `CAMOUFOX_CACHE_DIR`, and `PLAYWRIGHT_BROWSERS_PATH` as internal image-owned variables. Do not expose them as downstream-facing env knobs and do not override them from runtime env.
- `nix` itself must stay reachable even when `/home/hermes` is replaced by a fresh persisted mount. Keep `/usr/local/bin/nix` symlinked to the installed binary.
- Upstream `hermes gateway status` shells out to `ps eww -ax -o pid=,command=`. Ubuntu `procps` rejects that exact argument order in this container. Keep the narrow `/usr/local/bin/ps` wrapper that rewrites only that invocation to `ps axeww -o pid=,command=`.
- `ttyd` should bind a unix socket under `/run/user/3000`, not `/run`, because the runtime service runs as `hermes`.
- `ttyd` should be backed by `tmux new -A -s webterm` so browser reconnects do not kill the terminal session.
- Keep ttyd styling aligned to the dashboard palette.
- Bind the public web surface to `0.0.0.0:7681`, but keep internal dashboard and router listeners on localhost.
- Hermes browser tools should default to local Camofox mode in this image by running `camofox-browser` on `127.0.0.1:9377` and setting image-owned `CAMOFOX_URL` to that endpoint.
- Fresh homes need `~/.cache/camoufox` linked to the image-owned Camofox binary cache under `/opt/ghostship`, otherwise upstream `camofox-browser` fails on `/tabs` because it looks for `version.json` under the home cache.
- The `~/.cache/camoufox` symlink created during cont-init must itself be owned by `hermes`; a root-owned symlink is enough to fail the `/home/hermes` ownership smoke even when the target cache contents are correct.
- `camoufox-js fetch` does not reliably honor the image's custom cache-dir env during build. Fetch into the upstream default cache under `/root/.cache/camoufox`, then mirror that tree into `/opt/ghostship/camoufox-cache` and assert `version.json` exists there before shipping the image.
- The `camofox-browser` service must create its persisted profile and cookie directories owned by `hermes` before dropping privileges; creating them as root trips the `/home/hermes` ownership smoke.
- For `camofox-browser`, explicitly create and re-own the full `$HOME/.local/state/camofox-browser` tree, not just the leaf profile/cookie directories; otherwise the parent state directory still appears as `root:root` after first browser use and CI fails the home-ownership check.
- Do that Camofox state-tree ownership work in both places: pre-create `/home/hermes/.local/state/camofox-browser/{profiles,cookies}` during cont-init and then `mkdir/chown` the same tree again in the service with numeric `3000:3000`, because fresh persisted homes and stale exact-source images both exposed root-owned drift there.
- The `camofox-vnc` sidecar must also create its persisted state directory under `/home/hermes/.local/state/ghostship-hermes/camofox` as `hermes`; a root-owned VNC state dir silently trips the same `/home/hermes` ownership smoke after browser checks pass.
- Camofox cold starts on CI can exceed the upstream default 30s handler timeout. Keep the internal `camofox-browser` service timeouts raised (`HANDLER_TIMEOUT_MS=90000`, `NAVIGATE_TIMEOUT_MS=60000`) so the first local navigate does not fail during image smoke.
- The dashboard should embed the live browser view through the same origin at `/camofox/vnc.html?autoconnect=1&resize=remote&path=camofox/websockify`, backed by internal `x11vnc` and `noVNC` sidecars.
- Upstream Hermes `web/src/App.tsx` ships in two currently supported released shapes: the older static nav/page map and the newer `BUILTIN_NAV` plus explicit `<Route>` layout. Keep `prepare_upstream_hermes.py` patching both shapes so upstream dashboard bumps do not break the image build.
- Build `tirith` from the repo flake's pinned `.#tirith` package, not from ad-hoc `nixpkgs#tirith`, so exact-source Docker builds stay deterministic and do not depend on live `nixpkgs-unstable` GitHub API lookups.
- When the workstation smoke fails after the browser block, dump the concrete `/home/hermes` non-hermes ownership list and add step markers around the silent post-browser assertions; otherwise CI hides the actual failing late-stage check behind the generic Camofox trap output.
- The managed Hermes runtime primary lane is Codex `gpt-5.4` with `agent.reasoning_effort = "medium"`, and the configured fallback lane is direct `opencode-go/minimax-m2.7`.

### Discord Routing

- `DISCORD_HOME_CHANNEL` is part of the downstream Discord contract.
- `GHOSTSHIP_ROUTER_CHANNEL` pins replies to the local router `coding` lane.
- `DISCORD_FREE_RESPONSE_CHANNELS` is part of the downstream Discord contract and must include the router-pinned free-response channel.
- The router-pinned forced channel must ignore per-session `/model` overrides.
- Keep the managed Discord defaults at `require_mention = false` and `reactions = false`. Do not flip them back unless the user explicitly changes the contract.
- `DISCORD_REACTIONS=false`, `DISCORD_REQUIRE_MENTION=false`, and `DISCORD_AUTO_THREAD=false` are image-owned defaults. Treat them as optional for downstream and do not make downstream set them unless the contract changes.
- The default Codex primary lane depends on persisted Codex OAuth in `/home/hermes/.hermes/auth.json`.
- Do not use `OPENAI_API_KEY` anywhere in this repo's active runtime contract.
- Do not expose router auth as a downstream env knob. If the router needs a token for Hermes integration, it must be an internal auto-generated underscore-prefixed env such as `_GHOSTSHIP_ROUTER_API_KEY`.

### Router Policy

- `NVIDIA_BUILD_API_KEY` enables the repo-owned `nvidia-build` provider.
- The NVIDIA provider must stay curated and free-only; do not switch it to broad catalog discovery by default.
- Normal alias routing keeps only the top 3 scored models per provider for each bucket before cross-provider interleaving.
- Default provider priority is `nvidia-build` ahead of `opencode-zen` ahead of `openrouter` when remaining score inputs are otherwise comparable.

### Packaging Split

- Image-owned layer is Hermes core plus true runtime dependencies only.
- Prefer the utility's native package manager when one is the expected upstream install path.
- Persisted `/nix` has two lanes: an image-managed default profile for baseline Nix tools and the user-managed `/home/hermes/.nix-profile` for extra installs.
- `camofox-browser` should run as an internal sidecar with browser binaries/caches under `/opt/ghostship`, while persisted profiles/cookies live under `/home/hermes/.local/state/camofox-browser`.
- Use the same iframe sandbox policy for the live browser tab as the terminal tab: `allow-same-origin allow-scripts allow-forms`, no modal permission.
- Node-native CLIs such as `codex`, `gemini-cli`, `agent-browser`, and `opencode` belong in npm under `/home/hermes`.
- Avoid convenience-driven image bloat. If a binary is not required by boot, supervision, router, dashboard, ttyd, native Hermes runtime, or upstream doctor/runtime expectations, move it out of base.

### Testing

- Live validation on `chill-penguin` is the real deployment proof path.
- The smoke test should cover:
  - dashboard `/api/status`
  - router readiness
  - terminal path `/terminal/`
  - browser live-view path `/camofox/vnc.html?autoconnect=1&resize=remote&path=camofox/websockify`
  - native `hermes gateway status`
  - `hermes doctor` as far as upstream supports without repo shims
  - persistence across restart and full container recreation for `/home/hermes`, `/workspace`, and `/nix`

### Python Utilities

- Build the shared `ghostship-cli-contract` package from the same Python package set as its consuming CLIs.
- Keep `ghostship-*` CLI names aligned to API/client operation names.
- Keep JSON-first output and the shared error envelope.
