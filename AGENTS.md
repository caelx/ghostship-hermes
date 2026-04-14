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
  - Discord `#deepthink` pinned to Codex `gpt-5.4` with high reasoning
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
- Persisting `/home/hermes` preserves Hermes config, Codex auth, npm CLIs, XDG state, and other tool state in the way workstation users expect.
- `nix` itself must stay reachable even when `/home/hermes` is replaced by a fresh persisted mount. Keep `/usr/local/bin/nix` symlinked to the installed binary.
- Upstream `hermes gateway status` shells out to `ps eww -ax -o pid=,command=`. Ubuntu `procps` rejects that exact argument order in this container. Keep the narrow `/usr/local/bin/ps` wrapper that rewrites only that invocation to `ps axeww -o pid=,command=`.
- `ttyd` should bind a unix socket under `/run/user/3000`, not `/run`, because the runtime service runs as `hermes`.
- `ttyd` should be backed by `tmux new -A -s webterm` so browser reconnects do not kill the terminal session.
- Keep ttyd styling aligned to the dashboard palette.
- Bind the public web surface to `0.0.0.0:7681`, but keep internal dashboard and router listeners on localhost.

### Discord Routing

- `GHOSTSHIP_ROUTER_CHANNEL` pins replies to the local router `agentic` lane.
- `GHOSTSHIP_DEEPTHINK_CHANNEL` pins replies to Codex `gpt-5.4` with `reasoning.effort = high`.
- Forced channels must ignore per-session `/model` overrides.
- The `#deepthink` lane depends on persisted Codex OAuth in `/home/hermes/.hermes/auth.json`, not on `OPENAI_API_KEY`.

### Packaging Split

- Image-owned layer is Hermes core plus true runtime dependencies only.
- Generic operator tools belong in persistent userland Nix.
- Node-native CLIs such as `codex`, `gemini-cli`, and `opencode` belong in npm under `/home/hermes`.
- Avoid convenience-driven image bloat. If a binary is not required by boot, supervision, router, dashboard, ttyd, or native Hermes runtime, move it out of base.

### Testing

- Live validation on `chill-penguin` is the real deployment proof path.
- The smoke test should cover:
  - dashboard `/api/status`
  - router readiness
  - terminal path `/terminal/`
  - native `hermes gateway status`
  - `hermes doctor` as far as upstream supports without repo shims
  - persistence across restart and full container recreation for `/home/hermes`, `/workspace`, and `/nix`

### Python Utilities

- Build the shared `ghostship-cli-contract` package from the same Python package set as its consuming CLIs.
- Keep `ghostship-*` CLI names aligned to API/client operation names.
- Keep JSON-first output and the shared error envelope.
