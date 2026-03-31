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

## Lessons Learned

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

## Documentation Requirements

- Document how to build and test Python CLI utilities in this repository.
- Keep repo identity and OSS maintenance files present from the start: `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `.github/` metadata.
- Python utility build/test loop:
  - `python3 scripts/python_utility.py lock packages/searxng-cli`
  - `python3 scripts/python_utility.py test packages/searxng-cli`
  - `python3 scripts/python_utility.py build packages/searxng-cli`
  - `nix build .#packages.x86_64-linux.ghostship-hermes-runtime`
  - `nix build .#packages.aarch64-linux.ghostship-hermes-image`
