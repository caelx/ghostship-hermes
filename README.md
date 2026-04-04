# ghostship-hermes

`ghostship-hermes` builds and publishes `ghcr.io/caelx/ghostship-hermes`, a lean NixOS-based Hermes container image aligned to the upstream Hermes NixOS module and `/data` runtime contract.

Canonical image references:

- Pull ref: `ghcr.io/caelx/ghostship-hermes`
- GitHub package page: <https://github.com/caelx/ghostship-hermes/pkgs/container/ghostship-hermes>

## Runtime Model

- Hermes is configured declaratively through the upstream Hermes NixOS module.
- `HERMES_HOME=/data/.hermes`
- `HOME=/home/hermes`
- `/data/home` stores persisted HOME-backed state behind a thin `/home/hermes` facade.
- `/workspace` remains a separate persisted working directory.
- `/nix` should be persisted when you want user-level `nix profile install`, `nix shell`, and related outputs to survive container replacement.
- The runtime user is `hermes` at `3000:3000`.
- The public browser surface is a minimal dashboard on port `7681`.
- The dashboard can launch and close an ephemeral `ttyd` session on demand. Terminals are not persistent services.

This image intentionally does not ship the old Ghostship workstation layer.

Removed from the default image:

- Codex
- Gemini CLI
- Opencode
- OpenSpec
- `skills`
- `gws`
- `bws`
- `feed`
- repo-managed skill seeding
- honcho compatibility wiring
- profile reconciler and persistent per-profile terminals
- app/update timers for mutable workstation tooling

Retained in the default image:

- upstream Hermes
- Nix runtime support
- `ttyd`
- Caddy
- all `ghostship-*` utilities

## Persistent Paths

Canonical persistent roots:

- `/data`
- `/data/.hermes`
- `/data/home`
- `/workspace`
- `/nix`

The runtime persists these top-level HOME-backed directories through `/data/home`:

- `~/.hermes`
- `~/.config`
- `~/.local`
- `~/.cache`
- `~/.agent-browser`
- `~/.agents`
- `~/.codex`
- `~/.gemini`
- `~/.copilot`
- `~/.npm`
- `~/.bun`
- `~/.ssh`
- `~/.gnupg`
- `~/.pki`

That keeps later-installed coding agents and browser tooling persistent without preinstalling them in the base image. `~/.hermes` is persisted separately from `HERMES_HOME=/data/.hermes` because upstream Hermes stores named profiles under `~/.hermes/profiles/...` even when the active managed home is elsewhere.

## Running The Image

```fish
docker run \
  --rm \
  --name ghostship-hermes \
  --publish 7681:7681 \
  --volume ghostship-hermes-data:/data \
  --volume ghostship-hermes-workspace:/workspace \
  --volume /nix:/nix \
  ghcr.io/caelx/ghostship-hermes:latest
```

Notes:

- Reuse `/nix` only when it already contains compatible Nix state you want to keep. Do not hide a fresh Nix-built image behind a brand-new empty `/nix` volume.
- The dashboard is the intended browser entrypoint.
- Hermes starts with a minimal declarative config so the gateway process comes up cleanly even before you add your own provider or messaging settings.

After startup:

1. Open `http://localhost:7681`.
2. Use `Open Terminal` to launch an ephemeral shell-backed `ttyd` session.
3. Use `Close Terminal` to tear it down.

## Hermes Configuration

The image is intentionally declarative-first:

- Hermes managed config is written into `/data/.hermes`.
- The default runtime does not let Hermes self-apply the system flake.
- User-level Nix remains available for mutable runtime installs such as `nix profile install`.

Upstream Hermes docs still apply for CLI behavior:

- <https://hermes-agent.nousresearch.com/docs/>
- <https://hermes-agent.nousresearch.com/docs/getting-started/nix-setup/>
- <https://hermes-agent.nousresearch.com/docs/reference/cli-commands>

## Ghostship Utilities

The image still bundles the repo-managed service CLIs:

- `ghostship-bazarr`
- `ghostship-changedetection`
- `ghostship-cloakbrowser`
- `ghostship-flaresolverr`
- `ghostship-grimmory`
- `ghostship-nzbget`
- `ghostship-plex`
- `ghostship-pricebuddy`
- `ghostship-prowlarr`
- `ghostship-pyload-ng`
- `ghostship-qbittorrent`
- `ghostship-radarr`
- `ghostship-romm`
- `ghostship-rss-bridge`
- `ghostship-searxng`
- `ghostship-sonarr`
- `ghostship-synology`
- `ghostship-tautulli`

All `ghostship-*` utilities emit native JSON by default.

## Local Validation

Build the image locally:

```fish
mkdir -p .nix-local-store
nix --store "$PWD/.nix-local-store" build .#packages.x86_64-linux.ghostship-hermes-image -L
```

Run the dashboard smoke test:

```fish
set tarball "$PWD/.nix-local-store/nix/store/(basename (nix --store "$PWD/.nix-local-store" path-info .#packages.x86_64-linux.ghostship-hermes-image))/tarball/nixos-system-x86_64-linux.tar.xz"
GHOSTSHIP_NIX_STORE="$PWD/.nix-local-store" bash tests/hermes-image/profiles-dashboard.sh $tarball
```

Run the full persistence validation:

```fish
GHOSTSHIP_NIX_STORE="$PWD/.nix-local-store" bash scripts/validate_workstation_persistence.sh
```

The persistence suite validates:

- `HERMES_HOME=/data/.hermes`
- `HOME=/home/hermes`
- `hermes` runs as `3000:3000`
- no custom default skills are seeded
- removed workstation tools are absent by default
- `ghostship-*` utilities remain available
- HOME-backed state survives container replacement
- `nix profile install` survives container replacement with reused `/nix`
- later-installed tool state remains updateable
- `opencode` install plus XDG state survives replacement
- the dashboard can open and close an ephemeral terminal before and after replacement

## Python Utility Workflow

For the standardized Python utility workflow, see [docs/python-utilities.md](docs/python-utilities.md).
