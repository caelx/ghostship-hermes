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
- Scheduled automation should watch upstream Hermes releases and only publish when the pinned stable Nixpkgs branch contains the matching Hermes version

## Lessons Learned

- Hermes does not currently present a documented primary web UI. The official docs describe a CLI/TUI and a messaging gateway workflow.
- Hermes browser automation docs describe `agent-browser` via Browserbase-style cloud/browser tooling rather than a local Chrome/CDP-first setup.
- Hermes skills are stored in `~/.hermes/skills/`, and bundled skills are copied there on install; the container should mirror that behavior.
- The current v1 direction is a `ttyd`-served Hermes interface rather than Discord as the default entrypoint.

## Documentation Requirements

- Document how to build and test Python CLI utilities in this repository.
- Keep repo identity and OSS maintenance files present from the start: `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `.github/` metadata.
