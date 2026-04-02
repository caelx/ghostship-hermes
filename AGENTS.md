# Agent Directives: ghostship-hermes

## Purpose

- Build and publish `ghcr.io/caelx/ghostship-hermes`: a GHCR container image for Hermes with curated tools and repo-managed default skills.
- Treat this repo as a monorepo for the Hermes image, Python CLI utilities, and bundled skills.

## Project Invariants

- Run Hermes as a non-root runtime user. Do not grant general `sudo` in-container.
- Include Nix in the runtime for ad hoc `nix shell` usage.
- Persist Hermes state under the user home. Treat `/nix` persistence as deployment-specific, not a default Docker named volume.
- Default browser entrypoint is a Caddy dashboard on port `7681` that proxies same-origin `ttyd` terminals.
- Keep CLI access available for admin and debug workflows.
- Discord gateway is a later optional interface, not the v1 default.
- Seed default skills into `~/.hermes/skills/` on first start without overwriting user-managed content.
- Install Hermes at container runtime with the upstream manual `uv` + `npm` flow against a pinned upstream release tag.
- Follow upstream profile layout: default profile at `~/.hermes`, named profiles at `~/.hermes/profiles/<name>`.
- Generate profile-scoped `ttyd` terminals and gateway services dynamically from discovered profiles without restarting the container.
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
- Hermes `v2026.3.30` already pins `honcho-ai` `2.0.1` through the upstream `honcho` extra; container support only needs the SDK available in the Hermes Python environment.
- Create `~/.honcho` lazily and only when compatibility state exists. Primary persisted config stays at `$HERMES_HOME/honcho.json`.
- Hermes has no documented primary web UI today; the official UX is CLI/TUI plus messaging gateway workflows.
- Hermes browser automation docs describe `agent-browser` in Browserbase-style cloud terms, not a local Chrome/CDP-first stack.
- Hermes skills live in `~/.hermes/skills/`; container behavior should mirror upstream skill copying.
- `agent-browser` in this repo should come from the Hermes-side `npm install`, not from nixpkgs.
- Install Hermes into the final `/home/hermes/.hermes/hermes-agent` path, not an editable temp checkout. Editable installs leave launchers pointing at dead `/tmp/...` paths and tmux sessions exit.
- `hermes chat` exits immediately with no provider configured. Browser sessions must fall back to a real shell instead of an empty tmux session.
- Hermes `v2026.3.28` lacks native profiles; `v2026.3.30` adds `hermes profile ...` and `-p/--profile`, which the multi-profile dashboard depends on.

### Container And Supervisor Behavior

- A practical container needs a root init phase to prepare `/home/hermes/.hermes` and `/nix` permissions before dropping to the `hermes` user.
- Hermes bootstrap also needs writable `/tmp` plus `SSL_CERT_FILE` and `NIX_SSL_CERT_FILE`; otherwise `mktemp`, `git clone`, and Nix fetches fail.
- Under the current `s6` layout, `ttyd` is the primary browser terminal and the gateway watcher polls `~/.hermes/.env`; when credentials appear, it should run `hermes gateway run --replace` without restart.
- Caddy does not auto-discover local `ttyd` processes. Generate route tables and iframe manifests from the Hermes profile set.
- `s6-svscan` does not notice new service directories automatically after startup. The profile reconciler must call `s6-svscanctl -a`.
- For this container, the supported `agent-browser` path is CloakBrowser-backed profiles only: two default profiles plus one default VPN-backed profile that is more CAPTCHA-prone.
- Mounting an empty Docker volume over `/nix` on a fresh Nix-built image is unsafe: it can hide or copy the image store and stall `docker run`.
- In bash with `set -e`, helper functions that stream via `while read` must end with `return 0`, or the final `read` can terminate reconciliation loops after state truncation.
- In bash with `set -e`, idempotent helpers like `write_if_changed` must also return `0` on no-op paths.

### Platform And CI

- Scheduled GitHub release polling must authenticate with `GITHUB_TOKEN` or `GH_TOKEN`; anonymous `api.github.com` release queries can hit rate limits and break Actions.
- Hermes is not packaged in the inspected `nixos-25.11` nixpkgs tree, while `ttyd`, `codex`, `gemini-cli`, and `opencode` are.
- On the current `x86_64` dev host, `nix flake check` does not build `aarch64-linux` outputs. Use `nix eval` locally to keep the arm64 image derivation wired correctly and rely on arm64 runners for full arm builds.
- Git worktrees do not carry ignored local `.envrc` files by default. Live-test helpers should check the current worktree first, then another repo worktree with `.envrc`.
- Cloudflare Access service-token headers are test-only. Use `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID` and `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET` in utilities, and derive them from local `.envrc` values in the live-test harness.

### Service And API Integration

- `docs/api/` follows a hybrid rule: every `ghostship-*` utility needs a canonical Markdown API reference, and services with upstream machine-readable specs should also keep the mirrored raw JSON artifact beside it.
- RomM v4.7.0 auth uses `POST /api/token` with the OAuth password grant (`username`, `password`, `grant_type=password`), not a static token flow.
- CloakBrowser Manager auth uses the server `AUTH_TOKEN` as `Authorization: Bearer <token>`; `/api/status` stays unauthenticated for health checks.
- `ghostship-cloakbrowser` previously built URLs without the slash before `api`; valid credentials still failed until that was fixed.
- qBittorrent WebUI automation uses cookie auth at `/api/v2/auth/login`, not a static API key.
- NZBGet automation uses JSON-RPC over `/jsonrpc` with HTTP Basic auth, not a REST resource model.
- Synology has official PDF docs for DSM login and File Station. DSM docs cover `enable_syno_token=yes`, `sid`, `synotoken`, and `SynoToken`; File Station docs cover the broader namespace inventory.
- Grimmory source-of-truth is the official `grimmory-tools/grimmory` repository. It is the BookLore successor; document its API from that repo’s controllers, not unrelated `grimoire` services.
- PriceBuddy exposes authenticated API docs at `/docs/api`, but the raw OpenAPI export is effectively token-gated. If no authenticated export is available, document the surface from upstream tests and handlers instead of inventing a spec mirror.
- RSS-Bridge is action-driven, not CRUD-driven. “Create a feed” means generating a canonical `action=display` URL from bridge schema, not persisting a server-side object.
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
