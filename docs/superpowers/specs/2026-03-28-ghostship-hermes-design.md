# ghostship-hermes Design

Date: 2026-03-28

## Summary

`ghostship-hermes` is a Nix-first monorepo that builds and publishes a `full` GHCR container image for Hermes. The image targets `linux/arm64`, runs as a non-root `hermes` user, includes a curated tool bundle and runtime Nix, and use `ttyd` serving Hermes as the primary v1 interface.

The repository hosts multiple Python-based CLI utility packages for API wrappers (e.g., Sonarr, Radarr, Plex, Synology, qBittorrent, NZBGet), default repo-managed Hermes skills, and GitHub Actions workflows that build on every push and publish from `main`. All CLI utilities are designed to be agent-friendly, outputting native JSON by default.

## Goals

- Build a reproducible GHCR image for Hermes using stable Nixpkgs for the base toolchain and a pinned upstream Hermes release for the application itself
- Ship Hermes plus a curated default tool bundle in a single `full` image
- Support `linux/arm64`
- Run Hermes as a dedicated non-root user
- Make Hermes state and runtime Nix persistent across container restarts
- Seed repo-managed default skills into the standard Hermes skill path
- Provide a standardized Python utility pattern for API-wrapper CLIs that output native JSON
- Support a wide range of self-hosted services via specialized, fully featured CLIs

## Non-Goals

- A browser-native Hermes UI in v1
- In-container general-purpose `sudo`
- Multiple image variants in v1
- Tracking `nixos-unstable` in production
- Following the upstream Hermes `main` branch

## Recommended Approach

Use a single monorepo with one flake as the source of truth for packages, the OCI image, shared Nix code, and automation. The base image and curated tool bundle should come from a pinned stable Nixpkgs release branch, while Hermes itself should be installed in the container via the documented upstream `uv` plus `npm` flow against a pinned upstream release tag.

Python is the default language for repo-hosted CLI utilities. All utilities follow a strict "JSON-first" output mandate to ensure they are easily consumed by AI agents like Hermes. Utilities are developed after researching official API specifications to ensure comprehensive feature support.

## Architecture

### Monorepo Structure

The repository layout is:

- `flake.nix` and `flake.lock` for Nix outputs and pinning
- `packages/hermes-image/` for image-specific scripts and entrypoint logic
- `packages/<service>-cli/` for specialized API-wrapper utilities
- `skills/` for repo-managed default Hermes skills mapped to the CLI utilities
- `docs/` for design and operational documentation
- `.github/` for workflows, templates, and repository metadata

### Python Utility Conventions

Each utility package:

- uses `src/` layout
- defines metadata in `pyproject.toml`
- uses `uv` for dependency management
- uses `ruff` for linting/formatting (recommended)
- includes unit tests with mocks
- **Outputs native JSON by default** to stdout
- Supports `--pretty` for formatted JSON output
- Uses environment variables for all sensitive configuration (URL, API Keys, Tokens)

The default CLI contract follows this shape:

- `ghostship-<service> <action> [args]`
- Output is ALWAYS valid JSON
- Non-interactive behavior only
- Stable flag names
- Meaningful exit codes

### Implemented Utilities (Comprehensive)

- `ghostship-searxng`: Web search
- `ghostship-sonarr`: TV series management (series, lookup, episodes, queue, history, commands)
- `ghostship-radarr`: Movie management (movies, lookup, queue, history, commands)
- `ghostship-prowlarr`: Indexer management and search
- `ghostship-plex`: Plex Media Server management (libraries, metadata, sessions, tasks)
- `ghostship-romm`: ROM library management (games, platforms, scans, collections, heartbeat)
- `ghostship-nzbget`: NZBGet management (queue, history, files, rate, shutdown, config)
- `ghostship-qbittorrent`: qBittorrent management (torrents, search, RSS, logs, prefs, transfer)
- `ghostship-grimmory`: Book library management (books, scans)
- `ghostship-tautulli`: Plex monitoring (activity, history)
- `ghostship-bazarr`: Subtitle management (series, info)
- `ghostship-synology`: Synology File Station management (shares, files, search, mkdir, rename, rm, download)
- `ghostship-flaresolverr`: Cloudflare protection bypass (get, post, sessions)

### Image Composition

The published image includes:

- runtime Nix
- A curated operator tool bundle (`git`, `curl`, `jq`, `ripgrep`, `uv`, etc.)
- All implemented `ghostship-` CLI utilities
- `agent-browser` for local browser automation

## Runtime Design

### Process Model

The container runs an entrypoint that ensures Hermes is installed, seeds repo-managed skills, and starts `ttyd` serving a persistent `tmux` session for Hermes.

### User, Permissions, and Persistence

The runtime user is a dedicated non-root `hermes` user. Persistent volumes are mounted for `/home/hermes/.hermes` and `/nix`.

### Skills

Repo-managed skills are seeded into `~/.hermes/skills/` on first start. Each skill teaches Hermes how to use one of the `ghostship-` CLI utilities effectively, emphasizing JSON output and environment configuration.

## Release and Update Strategy

- **Source of Truth**: Upstream tags/releases of `nousresearch/hermes-agent`.
- **Nixpkgs Policy**: Pin to current latest stable NixOS release branch.
- **Publication**: Automate GHCR image builds for `linux/arm64`.

## Testing Strategy

- Unit tests for each Python CLI utility using mocks.
- Image-level validation to confirm Hermes and tools are functional.

## Open Questions Resolved

- Output format: Native JSON by default for all utilities.
- Configuration: Environment variables only, no hardcoded secrets.
- Browser automation: `agent-browser` included in the image.
- Feature coverage: Utilities are implemented to match official API specifications.
