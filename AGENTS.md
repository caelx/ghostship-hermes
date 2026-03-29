# Agent Directives: ghostship-hermes

## Project Facts

- Repository name: `ghostship-hermes`
- Product goal: build and publish a GHCR container image for Hermes with a curated tool bundle and repo-managed default skills
- Monorepo from the start: Hermes image, Python CLI utilities, and skills live in this repository
- Primary published image target: `ghcr.io/<owner>/ghostship-hermes`
- Runtime user should be non-root; do not grant general `sudo` inside the container
- Runtime should include Nix for ad hoc `nix shell` usage
- Persist Hermes state in the user home volume and persist `/nix` on a separate volume
- Primary v1 interface should be `ttyd` serving Hermes for browser access
- CLI access remains available for admin/debug workflows inside the running container
- Discord gateway remains an optional later interface, not the v1 default
- Default skills should seed into the standard Hermes runtime skill directory on first start without overwriting user-managed content
- The first utility scaffold should target SearXNG
- Build on every push/PR; only publish from `main`
- Hermes is installed at container runtime using the upstream manual `uv` plus `npm` flow against a pinned upstream release tag
- Scheduled automation should watch upstream Hermes releases and update `packages/hermes-image/hermes-release.txt`
- Publish only an `linux/arm64` image for v1
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
- On the current x86_64 development host, `nix flake check` does not build `aarch64-linux` outputs. Use `nix eval` locally to keep the arm64 image derivation wired up and rely on arm64 runners for the full image build.

## Documentation Requirements

- Document how to build and test Python CLI utilities in this repository.
- Keep repo identity and OSS maintenance files present from the start: `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `.github/` metadata.
- Python utility build/test loop:
  - `python3 scripts/python_utility.py lock packages/searxng-cli`
  - `python3 scripts/python_utility.py test packages/searxng-cli`
  - `python3 scripts/python_utility.py build packages/searxng-cli`
  - `nix build .#packages.x86_64-linux.ghostship-hermes-runtime`
  - `nix build .#packages.aarch64-linux.ghostship-hermes-image`
