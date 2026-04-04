# Agent Directives: ghostship-hermes

## Purpose

- Build and publish `ghcr.io/caelx/ghostship-hermes`: a GHCR container image for Hermes with a lean upstream-aligned runtime plus the repo's `ghostship-*` service utilities.
- Treat this repo as a monorepo for the Hermes image and Python CLI utilities.

## Project Invariants

- Run Hermes as a non-root runtime user. Do not grant general `sudo` in-container.
- Include Nix in the runtime for ad hoc `nix shell` usage.
- Keep `HERMES_HOME=/data/.hermes` to match the upstream Hermes NixOS module container-mode layout.
- Treat `/data` as the canonical persisted Hermes root, `/data/home` as the persisted home facade exposed through `/home/hermes`, and `/workspace` as the separate persisted work-products mount.
- Persist `/nix` whenever the deployment expects user-installed Nix software or build outputs to survive container replacement, but do not hide the image store behind a brand-new empty Docker volume.
- Default browser entrypoint is a Caddy dashboard on port `7681` that proxies same-origin `ttyd` terminals.
- Keep CLI access available for admin and debug workflows.
- Discord gateway is a later optional interface, not the v1 default.
- Configure Hermes declaratively through the upstream Hermes NixOS module.
- Do not seed Ghostship-managed default skills or develop-environment workstation content into the image runtime.
- Do not preinstall Codex, Gemini CLI, Opencode, OpenSpec, `skills`, `gws`, `bws`, or `feed` in the default image.
- Keep the browser surface minimal: one dashboard, on-demand ephemeral `ttyd`, no persistent per-profile terminal services.
- Persist the needed top-level HOME-backed directories under `/data/home`: `.hermes`, `.config`, `.local`, `.cache`, `.agent-browser`, `.agents`, `.codex`, `.gemini`, `.copilot`, `.npm`, `.bun`, `.ssh`, `.gnupg`, and `.pki`.
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

- Hermes has no documented primary web UI today; the official UX is CLI/TUI plus messaging gateway workflows.
- Hermes managed config for the NixOS module lives under `${stateDir}/.hermes`; with this image that means `HERMES_HOME=/data/.hermes` and `stateDir=/data`.
- The upstream module can run cleanly with `HOME=/home/hermes` as long as `HERMES_HOME` still points at `/data/.hermes`.
- Upstream Hermes profiles are anchored to `~/.hermes/profiles/...` regardless of `HERMES_HOME`, so the home facade must persist `~/.hermes` separately from `/data/.hermes`.
- A minimal declarative gateway config is enough to boot the Hermes service even before operator-specific provider or messaging settings are added.

### Container And Supervisor Behavior

- The runtime needs a root init phase to prepare `/data`, `/data/.hermes`, `/data/home`, `/workspace`, `/nix`, and the `/home/hermes` facade before dropping to the `hermes` user.
- Mounting an empty Docker volume over `/nix` on a fresh Nix-built image is unsafe: it can hide or copy the image store and stall `docker run`.
- Docker validation against a repo-local Nix store must mount that same store root into the container at `/nix`; binding the host `/nix` while the image was built in `.nix-local-store` hides the needed store paths.
- Imported NixOS images may not expose `bash` through `docker exec bash`; image tests should use `/bin/sh` plus an explicit PATH to the NixOS system profile.
- The docker-container NixOS profile leaves the firewall active inside the container; published dashboard traffic requires explicitly allowing TCP `7681`.
- Persisted `/nix` must include a writable `/nix/var/nix/daemon-socket` path and the image must start `nix-daemon.socket` after storage preparation, or user-level `nix profile install` will fail even though `nix` is installed.

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
- Treat `BWS_ACCESS_TOKEN` as the bootstrap secret, Bitwarden Secrets Manager as the default source of truth for service credentials and automation-compatible website credentials, and utility env vars as the runtime interface rather than the durable storage layer for those secrets.
- Keep local topology such as service URLs, hostnames, ports, profile names, and workspace paths in env/config by default unless the value itself contains credential material.
- Prefer per-command secret materialization from `bws` over exporting a broad long-lived shell environment with every service secret loaded at once.
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
