# ghostship-hermes Design

Date: 2026-03-28

## Summary

`ghostship-hermes` will be a Nix-first monorepo that builds and publishes a `full` GHCR container image for Hermes. The image will target both `linux/amd64` and `linux/arm64`, run as a non-root `hermes` user, include a curated tool bundle and runtime Nix, and use `ttyd` serving Hermes as the primary v1 interface.

The repository will also host Python-based CLI utility packages for API wrappers, default repo-managed Hermes skills, and GitHub Actions workflows that build on every push and publish from `main`. A scheduled workflow will watch upstream Hermes releases and only publish updated images when the pinned stable Nixpkgs branch contains the matching Hermes version.

## Goals

- Build a reproducible GHCR image for Hermes using stable Nixpkgs
- Ship Hermes plus a curated default tool bundle in a single `full` image
- Support both `linux/amd64` and `linux/arm64`
- Run Hermes as a dedicated non-root user
- Make Hermes state and runtime Nix persistent across container restarts
- Seed repo-managed default skills into the standard Hermes skill path
- Provide a Python utility/package pattern for API-wrapper CLIs
- Bootstrap the repository with standard OSS files and GitHub best practices

## Non-Goals

- A browser-native Hermes UI in v1
- In-container general-purpose `sudo`
- Multiple image variants in v1
- Tracking `nixos-unstable` in production
- Following the upstream Hermes `main` branch

## Recommended Approach

Use a single monorepo with one flake as the source of truth for packages, the OCI image, shared Nix code, and automation. Hermes should come from a pinned stable Nixpkgs release branch, while the scheduled release workflow uses upstream `nousresearch/hermes-agent` tags/releases as the trigger source and Nixpkgs package availability as the publication gate.

Python should be the default language for repo-hosted CLI utilities. The main reasons are API-integration ergonomics, strong testing support, and a good fit for machine-readable CLI patterns required by agents. Node remains an acceptable exception for SDK-driven cases, but not the default.

## Architecture

### Monorepo Structure

The initial repository layout should be:

- `flake.nix` and `flake.lock` for Nix outputs and pinning
- `packages/hermes-image/` for image-specific scripts and entrypoint logic
- `packages/searxng-cli/` as the first Python utility skeleton
- `packages/<future-cli>/` for additional Python utility packages
- `lib/` or `modules/` for shared Nix functions and image/package composition
- `skills/` for repo-managed default Hermes skills
- `docs/` for design and operational documentation
- `.github/` for workflows, templates, and repository metadata

### Python Utility Conventions

Each utility package should:

- use `src/` layout
- define metadata in `pyproject.toml`
- use `uv` for dependency management
- use `ruff` for linting/formatting
- use `mypy` with strict settings where practical
- include both unit and integration tests
- expose a stable, agent-friendly CLI interface

The default CLI contract should follow this shape:

- `tool <resource> <action>`
- `--json` for machine-readable output
- non-interactive behavior only
- stable flag names
- meaningful exit codes

### Image Composition

The published image should be a single `full` image including:

- Hermes from stable Nixpkgs
- runtime Nix
- `git`
- `curl`
- `jq`
- `yq-go`
- `ripgrep`
- `gh`
- `uv`
- `python3`
- `bash`
- `nodejs`
- `coreutils`
- `wget`
- `lsof`
- `strace`
- `psmisc`
- `file`
- `tree`
- `bubblewrap`
- `binutils`
- `tmux`
- `zip`
- `unzip`
- `p7zip`
- `ripgrep-all`
- `fd`
- `codex`
- `gemini-cli`
- `opencode`
- `agent-browser`

Package duplicates should be normalized during implementation.

## Runtime Design

### Process Model

The container should run a small entrypoint that starts a persistent `tmux` session for Hermes and serves it through `ttyd`. This browser-served terminal is the primary v1 interface. Direct CLI access remains available inside the running container for administration and debugging.

The `tmux` session should preserve the Hermes process across browser disconnects so the web terminal behaves like a durable admin console rather than a fragile one-shot shell. Discord gateway support can be added later as a separate runtime mode if needed.

### User, Permissions, and Persistence

The runtime user should be a dedicated non-root `hermes` user. The image should not grant general-purpose `sudo` inside the container. Any privileged administration should happen from outside the container through normal container orchestration or `docker exec -u 0` style access when explicitly needed.

Persistent volumes should be mounted for:

- the Hermes home directory, such as `/home/hermes/.hermes`
- `/nix` for the Nix store and downloaded dependencies

Hermes configuration and secrets should be accepted through both environment variables and mounted configuration files.

The `ttyd` endpoint should be exposed without built-in auth in the container, with the assumption that access control is handled by an external reverse proxy, VPN, or similar network boundary.

### Skills

Repo-managed default skills should be stored in the repository and seeded into the standard Hermes runtime path `~/.hermes/skills/` on first start. The seeding process should only copy missing defaults and must not overwrite user-managed skills already present in the persistent volume.

This mirrors Hermes’ documented runtime layout and avoids inventing a parallel skill path.

## Release and Update Strategy

### Source of Truth

The upstream source of truth for Hermes versions should be:

- `https://github.com/nousresearch/hermes-agent`

This repository should follow upstream tags/releases only, not upstream branch heads.

### Nixpkgs Policy

The flake should pin to the current latest stable NixOS release branch, not `nixos-unstable`. Updates to the stable Nixpkgs pin should happen explicitly through controlled repository changes.

### Publication Rules

GitHub Actions should:

- build and test on every push and pull request
- publish only from `main`
- publish image tags:
  - `latest`
  - `sha-<commit>`
  - `hermes-<upstream-version>` when applicable

### Scheduled Release Gate

The scheduled workflow should:

1. inspect the latest upstream Hermes release
2. inspect the version available in the pinned stable Nixpkgs branch
3. only update/build/publish when the versions match

This prevents breakage caused by upstream tagging a release before the stable Nixpkgs branch has packaged it.

## Testing Strategy

Testing should be layered:

- unit tests for each Python CLI utility
- integration tests for each utility against mocked or controlled API boundaries
- image-level validation for the built container

The image-level validation should confirm at minimum:

- Hermes is installed and runnable
- the `ttyd` entrypoint resolves correctly
- the persistent `tmux` Hermes session is created correctly
- the default tool bundle is present on `PATH`
- seeded default skills land in the correct Hermes path
- the runtime user and persistence expectations are wired correctly

## GitHub Best Practices Bootstrap

The repository should include, from the beginning:

- `README.md`
- `LICENSE` (MIT by default unless changed)
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `.github/` issue templates
- `.github/` pull request templates
- CI workflows for linting, tests, image builds, and publishing

The README should explain:

- what the image is for
- how Hermes is run through `ttyd` and `tmux`
- how persistence is expected to be mounted
- how the browser terminal should be exposed safely behind external network protection
- how Python CLI utilities are developed, tested, and packaged

The project `AGENTS.md` should document repository-specific build and test guidance for the utility packages.

## Open Questions Resolved

- Artifact type: OCI/Docker image built from Nix packages, not a NixOS system image
- Interface: `ttyd` serving Hermes for v1
- Runtime user: non-root
- In-container privilege escalation: none in v1
- Runtime Nix: included and persistent
- Architectures: `linux/amd64` and `linux/arm64`
- Image variants: single `full` image only
- First utility scaffold: SearXNG

## Implementation Notes

Implementation should prefer small, composable Nix outputs and avoid a monolithic flake file where possible. The first follow-up after spec approval should be a written implementation plan covering repository bootstrap, flake structure, image build, Python utility scaffolding, skill seeding, and CI workflow design.
