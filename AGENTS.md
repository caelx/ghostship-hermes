# Agent Directives: ghostship-hermes

## Project Facts

- Repository name: `ghostship-hermes`
- Product goal: build and publish a GHCR container image for Hermes with a curated tool bundle and repo-managed default skills
- Monorepo from the start: Hermes image, Python CLI utilities, and skills live in this repository
- Primary published image target: `ghcr.io/caelx/ghostship-hermes`
- Runtime user should be non-root; do not grant general `sudo` inside the container
- Runtime should include Nix for ad hoc `nix shell` usage
- Persist Hermes state in the user home volume and persist `/nix` on a separate volume
- Primary browser interface should be a Caddy dashboard on port `7681` that proxies same-origin `ttyd` terminals for the default and named Hermes profiles
- CLI access remains available for admin/debug workflows inside the running container
- Discord gateway remains an optional later interface, not the v1 default
- Default skills should seed into the standard Hermes runtime skill directory on first start without overwriting user-managed content
- The first utility scaffold should target SearXNG
- Build on every push/PR; publish the full mutable tag set from `main`, and limit non-main `workflow_dispatch` runs to immutable `sha-*` tags
- Hermes is installed at container runtime using the upstream manual `uv` plus `npm` flow against a pinned upstream release tag
- Hermes profile discovery should follow the upstream layout: default profile at `~/.hermes`, named profiles under `~/.hermes/profiles/<name>`
- Profile-scoped `ttyd` terminals and profile-scoped gateway services should be generated dynamically from the Hermes profile set, without requiring a container restart
- Scheduled automation should watch upstream Hermes releases and update `packages/hermes-image/hermes-release.txt`
- Publish multi-arch `amd64` and `arm64` image tags plus manifest lists for the documented release channels
- Repo-owned utilities should use a `ghostship-` prefix to avoid clobbering upstream or system package names
- All CLI utilities MUST output native JSON by default to ensure they are agent-friendly and easily machine-readable. Human-readable formatting (like tables) should be avoided in favor of raw JSON output.
- After Docker-based testing, clean up old images, dead test containers, and temporary test artifacts; keep only the current image and any still-needed live validation container.

## Lessons Learned

- Hermes Honcho resolution is profile-local first: it prefers `$HERMES_HOME/honcho.json` before the legacy shared compatibility config path, so per-profile Honcho config can live inside persisted profile state without changing `HOME`.
- Hermes `v2026.3.30` already pins `honcho-ai` `2.0.1` as the upstream `honcho` extra, so container support only needs the SDK available in the Hermes Python environment.
- The container should create the legacy Honcho compatibility path `~/.honcho` lazily only when compatibility state exists; the primary persisted config path remains profile-local `$HERMES_HOME/honcho.json`.
- Scheduled GitHub release polling must authenticate GitHub API requests with `GITHUB_TOKEN` or `GH_TOKEN`; anonymous `api.github.com` release queries can hit rate limits and break Actions even for small hourly jobs.
- Hermes does not currently present a documented primary web UI. The official docs describe a CLI/TUI and a messaging gateway workflow.
- Hermes browser automation docs describe `agent-browser` via Browserbase-style cloud/browser tooling rather than a local Chrome/CDP-first setup.
- Hermes skills are stored in `~/.hermes/skills/`, and bundled skills are copied there on install; the container should mirror that behavior.
- The current v1 direction is a `ttyd`-served Hermes interface rather than Discord as the default entrypoint.
- Hermes is not packaged in the locally inspected `nixos-25.11` nixpkgs source tree, while `ttyd`, `codex`, `gemini-cli`, and `opencode` are present there.
- In this repo, `agent-browser` is expected to come from the Hermes-side `npm install` step, making it available under the Hermes install tree rather than as a stable nixpkgs package.
- A practical container needs a root init phase to prepare `/home/hermes/.hermes` and `/nix` volume permissions before dropping to the non-root `hermes` user.
- Hermes bootstrap also depends on a writable `/tmp` and a default CA bundle exported through `SSL_CERT_FILE` and `NIX_SSL_CERT_FILE`, otherwise `mktemp`, `git clone`, and Nix HTTP fetches can fail at runtime.
- Hermes bootstrap must install the package into the final `/home/hermes/.hermes/hermes-agent` path, not an editable temp-tree checkout, because the generated launchers and `__editable__` import map otherwise point at a dead `/tmp/...` build path and tmux sessions exit immediately.
- `hermes chat` exits immediately when no provider is configured, so the browser session must fall back to a real shell instead of attaching `ttyd` to an empty tmux session.
- Under the current `s6` layout, `ttyd` is supervised as the primary browser terminal and the gateway watcher polls `~/.hermes/.env`; as soon as gateway credentials appear, it launches `hermes gateway run --replace` without requiring a container restart.
- Hermes `v2026.3.28` does not yet have native profile support; `v2026.3.30` adds `hermes profile ...` and `-p/--profile`, which the multi-profile dashboard design depends on.
- Caddy does not auto-discover local `ttyd` processes; the container must generate its own route table and iframe manifest from the Hermes profile set.
- `s6-svscan` does not automatically pick up newly created service directories after startup unless the runtime explicitly signals it, so the profile reconciler must call `s6-svscanctl -a` after creating new per-profile services.
- For this container, the supported `agent-browser` path is CloakBrowser-backed profiles only, with two default profiles available initially and one default VPN-backed profile that is more likely to hit CAPTCHA.
- Mounting an empty Docker volume over `/nix` on a fresh Nix-built image is not a safe default: it hides or triggers a copy of the image’s Nix store and can make `docker run` stall before the container starts. Treat `/nix` persistence as deployment-specific rather than a generic Docker named-volume mount.
- In bash with `set -e`, helper functions that stream records via `while read` should end with an explicit `return 0`; otherwise the final `read` returns `1` and can kill reconciliation loops after they already truncated runtime state files.
- In bash with `set -e`, idempotent helper functions like `write_if_changed` must also return `0` on the no-op path; returning `1` for “unchanged” will still crash long-running service loops.
- On the current x86_64 development host, `nix flake check` does not build `aarch64-linux` outputs. Use `nix eval` locally to keep the arm64 image derivation wired up and rely on arm64 runners for the full image build.
- RomM v4.7.0 auth is not a repo-managed static token flow. The supported bearer token path is `POST /api/token` with the OAuth password grant (`username`, `password`, `grant_type=password`).
- CloakBrowser Manager auth is a static shared secret configured on the server via `AUTH_TOKEN`; API callers reuse that same value as `Authorization: Bearer <token>`, and `/api/status` remains unauthenticated for health checks.
- `ghostship-cloakbrowser` originally built request URLs without the slash before `api`, so even valid manager credentials could not reach `/api/...` endpoints.
- `docs/api/` now follows a hybrid coverage rule: every `ghostship-*` utility must have a canonical Markdown API reference, and services with upstream machine-readable specs should also keep the mirrored raw JSON artifact in the same directory.
- qBittorrent’s supported WebUI automation contract is cookie-based auth at `/api/v2/auth/login`, not a static API key.
- NZBGet’s automation contract is JSON-RPC over `/jsonrpc` with HTTP Basic auth rather than a REST resource model.
- Synology has official PDF guides for both DSM login and File Station. The DSM guide explicitly documents `enable_syno_token=yes`, `sid`, `synotoken`, and `SynoToken`, while the File Station guide provides the broader namespace inventory beyond the subset used by `ghostship-synology`.
- Grimmory source-of-truth is the official `grimmory-tools/grimmory` repository. It is the successor to BookLore, and its backend API surface should be documented from that repo's controllers rather than from unrelated `grimoire` services.
- CLI contract rule: `ghostship-*` command names must mirror the API/client operation names directly so agents can map utility help to the API docs one-to-one. Do not introduce compatibility aliases or renamed convenience commands; keep generic passthrough commands like `request`/`call` only as fallback escape hatches.
- Git worktrees do not carry ignored local `.envrc` files by default. Live test helpers should look for credentials in the current worktree first and then fall back to another repo worktree that has `.envrc`, rather than assuming secrets exist in every worktree.
- Cloudflare Access service-token headers for Ghostship app probes should stay test-only: use `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID` and `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET` in the utilities, and let the live-test harness derive them from local-only `.envrc` values instead of making the runtime container depend on Cloudflare headers.
- The live integration suite should distinguish real client bugs from service-side conditions. The current Ghostship deployment exposes several read-only constraints that should skip rather than fail utility regression tests: RomM credentials only allow `heartbeat` and `config`, Grimmory becomes more stable when a bearer is cached once per session instead of logging in on every CLI call, pyLoad still returns `401 Invalid API credentials` without valid API auth, FlareSolverr may be absent from DNS, and Prowlarr search can time out on upstream indexer latency.
- User preference: always clean up old Docker test containers and stale local Docker artifacts after verification work, and leave local Docker state tidy when tests are complete.

- PriceBuddy publishes authenticated API docs at `/docs/api`, but the raw OpenAPI export is token-gated in practice; when no token-authenticated export is available, document the surface from upstream tests and handlers instead of inventing a spec mirror.
- RSS-Bridge is action-driven rather than CRUD-driven. For this repo, “create a feed” means generating a canonical `action=display` URL from the bridge schema, not persisting a server-side feed object.
- The deployed RSS-Bridge instance does not use one uniform parameter schema shape. Some bridges expose `parameters` as a dict of contexts, while others return a legacy list of parameter groups that should be treated as the global context; `ghostship-rss-bridge` needs to support both.

## Documentation Requirements

- Document how to build and test Python CLI utilities in this repository.
- Keep repo identity and OSS maintenance files present from the start: `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `.github/` metadata.
- Python utility build/test loop:
  - `python3 scripts/python_utility.py lock packages/searxng-cli`
  - `python3 scripts/python_utility.py test packages/searxng-cli`
  - `python3 scripts/python_utility.py build packages/searxng-cli`
  - `nix build .#packages.x86_64-linux.ghostship-hermes-runtime`
  - `nix build .#packages.aarch64-linux.ghostship-hermes-image`
