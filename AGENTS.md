# Agent Directives: ghostship-hermes

## Purpose

- Build and publish `ghcr.io/caelx/ghostship-hermes`: a GHCR container image for Hermes with curated tools and repo-managed default skills.
- Treat this repo as a monorepo for the Hermes image, Python CLI utilities, and bundled skills.

## Project Invariants

- Run Hermes as a non-root runtime user. Do not grant general `sudo` in-container.
- Include Nix in the runtime for ad hoc `nix shell` usage.
- Keep `HERMES_HOME=/opt/data` to match upstream Hermes Docker behavior.
- Treat `/opt/data` as the canonical persisted Hermes root, `/opt/data/home` as the persisted home facade exposed through `/home/hermes`, and `/workspace` as the separate persisted work-products mount.
- Persist `/nix` whenever the deployment expects user-installed Nix software or build outputs to survive container replacement, but do not hide the image store behind a brand-new empty Docker volume.
- Default browser entrypoint is a Caddy dashboard on port `7681` that proxies same-origin `ttyd` terminals.
- Keep CLI access available for admin and debug workflows.
- Discord gateway is a later optional interface, not the v1 default.
- Seed default skills into `~/.hermes/skills/` on first start without overwriting user-managed content.
- Seed the mirrored develop-environment defaults into persisted state under `/opt/data` and `/opt/data/home` without overwriting user edits.
- Install Hermes at container runtime with the upstream manual `uv` + `npm` flow against a pinned upstream release tag.
- Follow upstream profile layout: default profile at `~/.hermes`, named profiles at `~/.hermes/profiles/<name>`.
- Generate profile-scoped `ttyd` terminals dynamically from discovered profiles without restarting the container.
- Keep the steady-state runtime on a persisted `hermes` user `systemd` manager with boot jobs and timers under `~/.config/systemd/user`.
- Install `codex`, `gemini-cli`, `opencode`, `openspec`, and `skills` as normal workstation apps under the persisted home and update them on boot and timers.
- Keep the first utility scaffold focused on SearXNG.
- Watch upstream Hermes releases and update `packages/hermes-image/hermes-release.txt`.
- Publish multi-arch `amd64` and `arm64` images plus manifest lists for the documented release channels.
- Prefix repo-owned utilities with `ghostship-`.
- All CLI utilities must emit native JSON by default. Do not add table-first or other human-formatted default output.

## CI, Docs, And Release Hygiene

- Build on every push and PR.
- From `main`, publish the full mutable tag set.
- For non-`main` `workflow_dispatch`, publish immutable `sha-*` tags only.
- Keep repo identity and OSS maintenance files present: `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `.github/` metadata.
- Document how to build and test Python CLI utilities in this repo.
- After Docker-based verification, remove stale images, dead test containers, and temporary artifacts. Leave only the current image and any still-needed live validation container.

## Build And Test Commands

```fish
python3 scripts/python_utility.py lock packages/searxng-cli
python3 scripts/python_utility.py test packages/searxng-cli
python3 scripts/python_utility.py build packages/searxng-cli
nix build .#packages.x86_64-linux.ghostship-hermes-runtime
nix build .#packages.aarch64-linux.ghostship-hermes-image
```

## Shared CLI Contract

- Keep `ghostship-*` command names aligned with API and client operation names. Do not add compatibility aliases. Use generic passthrough commands like `request` or `call` only as fallback escape hatches.
- Honor a default hard timeout of `30` seconds via `--timeout`.
- Use the shared JSON error and exit-code envelope.
- Expose `--dry-run` on write and delete commands so agents can inspect the exact request object before mutation.
- In `BaseHttpClient.request_json()`, call the base transport path directly with `BaseHttpClient.request(self, spec)`. Do not route through service overrides like `self.request(spec)`.

## Durable Lessons

### Hermes Runtime

- Hermes Honcho resolution is profile-local first: prefer `$HERMES_HOME/honcho.json` before the legacy shared compatibility path.
- Hermes `v2026.3.30` already pins `honcho-ai` `2.0.1` through the upstream `honcho` extra, so the container does not need to bundle a separate `honcho-ai` package.
- Create `~/.honcho` lazily and only when compatibility state exists. Primary persisted config stays at `$HERMES_HOME/honcho.json`.
- Hermes has no documented primary web UI today; the official UX is CLI/TUI plus messaging gateway workflows.
- Hermes browser automation docs describe `agent-browser` in Browserbase-style cloud terms, not a local Chrome/CDP-first stack.
- Hermes skills live in `~/.hermes/skills/`; container behavior should mirror upstream skill copying.
- `agent-browser` in this repo should come from the Hermes-side `npm install`, not from nixpkgs.
- Install Hermes into the final `/opt/data/hermes-agent` path, not an editable temp checkout. Editable installs leave launchers pointing at dead `/tmp/...` paths and tmux sessions exit.
- `hermes chat` exits immediately with no provider configured. Browser sessions must fall back to a real shell instead of an empty tmux session.
- Hermes `v2026.3.28` lacks native profiles; `v2026.3.30` adds `hermes profile ...` and `-p/--profile`, which the multi-profile dashboard depends on.
- The repo `skills/agent-browser/SKILL.md` is intentionally copied from upstream unchanged; keep container-specific browser setup guidance in separate repo skills instead of patching the upstream skill body.

### Container And Supervisor Behavior

- A practical workstation container needs a root init phase to prepare `/opt/data`, `/opt/data/home`, `/workspace`, `/nix`, and the `/home/hermes` facade before dropping to the `hermes` user.
- Hermes bootstrap also needs writable `/tmp` plus `SSL_CERT_FILE` and `NIX_SSL_CERT_FILE`; otherwise `mktemp`, `git clone`, and Nix fetches fail.
- The steady-state runtime should be a `hermes` user `systemd` manager, not `s6`.
- `ttyd` is still the primary browser terminal surface, but per-profile terminals are managed as generated user services under the persisted home.
- Prefer Hermes' own `gateway install` systemd flow for persistent messaging gateways instead of a repo-specific gateway watcher.
- Caddy does not auto-discover local `ttyd` processes. Generate route tables and iframe manifests from the Hermes profile set.
- Persisted user `systemd` units belong under `/opt/data/home/.config/systemd/user` and are exposed through `/home/hermes/.config/systemd/user`; repo-managed units should be installed as managed symlinks so local overrides can replace them cleanly.
- For this container, the supported `agent-browser` path is CloakBrowser-backed profiles only: two default profiles plus one default VPN-backed profile that is more CAPTCHA-prone.
- Skills copied from a Nix-store source tree inherit read-only modes unless the runtime explicitly `chmod`s the copied files writable. Skill seeding must leave `~/.hermes/skills` user-editable after first start.
- Mounting an empty Docker volume over `/nix` on a fresh Nix-built image is unsafe: it can hide or copy the image store and stall `docker run`.
- The official Hermes Docker image does not create a `~/.hermes -> /opt/data` symlink; it sets `HERMES_HOME=/opt/data` directly. Named profiles, wrappers, and user services are still HOME-anchored, so this repo must provide the persisted home facade itself.
- Home-managed agent apps should install into versioned directories and flip stable symlinks only after a successful validation step.
- In bash with `set -e`, helper functions that stream via `while read` must end with `return 0`, or the final `read` can terminate reconciliation loops after state truncation.
- In bash with `set -e`, idempotent helpers like `write_if_changed` must also return `0` on no-op paths.

### Skill Authoring

- Repo-managed service skills should stay short, trigger-rich, and workflow-oriented: prioritize start-here guidance plus inspect -> dry-run -> mutate -> verify sequences over command dumps.
- Use family-level structure for service wrappers, but keep domain-specific ordering and failure guidance inside each skill instead of mass-applying identical wording.

### Platform And CI

- Scheduled GitHub release polling must authenticate with `GITHUB_TOKEN` or `GH_TOKEN`; anonymous `api.github.com` release queries can hit rate limits and break Actions.
- Hermes is not packaged in the inspected `nixos-25.11` nixpkgs tree, while `ttyd`, `codex`, `gemini-cli`, and `opencode` are.
- `googleworkspace/cli` already ships a usable upstream flake and a large upstream `skills/` tree. Keep the pinned flake input revision and the vendored `vendor/googleworkspace-cli/skills/` snapshot aligned to the same upstream commit.
- Upstream `feed` fits the image best as a direct flake-managed utility, not a `ghostship-*` wrapper. Keep its SQLite state under `$HERMES_HOME/feed/feed.db` so subscriptions and unread state stay profile-scoped.
- Local flake evaluation only sees git-tracked files. Stage new Nix files and vendored trees before relying on `nix flake check` or `nix build` in a worktree.
- On the current `x86_64` dev host, `nix flake check` does not build `aarch64-linux` outputs. Use `nix eval` locally to keep the arm64 image derivation wired correctly and rely on arm64 runners for full arm builds.
- Git worktrees do not carry ignored local `.envrc` files by default. Live-test helpers should check the current worktree first, then another repo worktree with `.envrc`.
- Cloudflare Access service-token headers are test-only. Use `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID` and `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET` in utilities, and derive them from local `.envrc` values in the live-test harness.

### Service And API Integration

- The Bitwarden Secrets Manager CLI fits this container best as an env-driven workflow: inject `BWS_ACCESS_TOKEN` from the operator, let `bws` use its normal HOME-based defaults, and persist that state through the `/opt/data/home` symlinked home tree instead of custom config-path overrides.
- `docs/api/` follows a hybrid rule: every `ghostship-*` utility needs a canonical Markdown API reference, and services with upstream machine-readable specs should also keep the mirrored raw JSON artifact beside it.
- For a dedicated personal Gmail account on an unverified testing-mode OAuth app, `gws auth login` should use narrow scopes like `gmail` or `gmail,calendar,drive`; the broad upstream `recommended` preset can fail consent.
- RomM v4.7.0 auth uses `POST /api/token` with the OAuth password grant (`username`, `password`, `grant_type=password`), not a static token flow.
- CloakBrowser Manager auth uses the server `AUTH_TOKEN` as `Authorization: Bearer <token>`; `/api/status` stays unauthenticated for health checks.
- `ghostship-cloakbrowser` previously built URLs without the slash before `api`; valid credentials still failed until that was fixed.
- qBittorrent WebUI automation uses cookie auth at `/api/v2/auth/login`, not a static API key.
- NZBGet automation uses JSON-RPC over `/jsonrpc` with HTTP Basic auth, not a REST resource model.
- Synology has official PDF docs for DSM login and File Station. DSM docs cover `enable_syno_token=yes`, `sid`, `synotoken`, and `SynoToken`; File Station docs cover the broader namespace inventory.
- Grimmory source-of-truth is the official `grimmory-tools/grimmory` repository. It is the BookLore successor; document its API from that repo’s controllers, not unrelated `grimoire` services.
- PriceBuddy exposes authenticated API docs at `/docs/api`, but the raw OpenAPI export is effectively token-gated. If no authenticated export is available, document the surface from upstream tests and handlers instead of inventing a spec mirror.
- RSS-Bridge is action-driven, not CRUD-driven. “Create a feed” means generating a canonical `action=display` URL from bridge schema, not persisting a server-side object.
- For RSS workflows in this image, keep `ghostship-rss-bridge` as the canonical feed URL generation layer and `feed` as the persistent subscription, fetch, search, and triage layer.
- changedetection.io's stable upstream API source of truth is `docs/api-spec.yaml` in the official repo. Persist the repo mirror as `docs/api/changedetection-openapi.json`; treat `/api/v1/full-spec` as the live merged instance-specific extension surface.
- The deployed RSS-Bridge instance returns two parameter shapes: a dict of contexts or a legacy list of parameter groups that should be treated as the global context.

### Testing And Known Service Conditions

- The live integration suite should skip service-side read-only constraints instead of reporting them as client regressions.
- Current known skips and caveats:
  - RomM credentials only allow `heartbeat` and `config`.
  - Grimmory is more stable when a bearer token is cached once per session instead of re-authing every CLI call.
  - pyLoad may still return `401 Invalid API credentials` without valid API auth.
  - FlareSolverr may be absent from DNS.
  - Prowlarr search may time out on upstream indexer latency.

### Python Packaging

- Build the shared `ghostship-cli-contract` package from the same Python package set as each consuming CLI package. Mixing `python3` with `python311Packages` can pass local package tests and still fail `nix flake check` in GitHub.
