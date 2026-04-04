# ghostship-hermes

`ghostship-hermes` builds and publishes `ghcr.io/caelx/ghostship-hermes`, a lean NixOS-based Hermes container image aligned to the upstream Hermes NixOS module with a repo-approved whole-home persistence model.

Canonical image references:

- Pull ref: `ghcr.io/caelx/ghostship-hermes`
- GitHub package page: <https://github.com/caelx/ghostship-hermes/pkgs/container/ghostship-hermes>

## Runtime Model

- Hermes is configured declaratively through the upstream Hermes NixOS module.
- `HERMES_HOME=/home/hermes/.hermes`
- `HOME=/home/hermes`
- `/home/hermes` itself is the persisted volume.
- `/workspace` remains a separate persisted working directory.
- `/nix` should be persisted when you want user-level `nix profile install`, `nix shell`, and related outputs to survive container replacement.
- The runtime user is `hermes` at `3000:3000`.
- The public browser surface is a minimal dashboard on port `7681`.
- The dashboard can launch as many ephemeral `ttyd` sessions as needed, tracks them as left-rail tabs, opens new tabs immediately with a loading state while `ttyd` starts, labels tabs from the shell cwd or current command, and returns to a blank home state when the active terminal is closed and no sessions remain.
- Browser terminals start in `/home/hermes`.
- The image bootstraps two Hermes profiles, `test` and `coder`, at `~/.hermes/profiles/...` so the upstream profile layout is ready to inspect immediately.

Upstream note:

- This image intentionally deviates from the upstream container-mode split between state and HOME.
- Upstream normally keeps managed state under `${stateDir}/.hermes` with a separate home directory.
- Here, the repo sets `stateDir = "/home/hermes"`, so managed Hermes state and the CLI profile tree both live under `/home/hermes/.hermes` on the persisted home volume.

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
- `tirith`
- `ttyd`
- minimal dashboard controller
- all `ghostship-*` utilities

## Persistent Paths

Canonical persistent roots:

- `/home/hermes`
- `/home/hermes/.hermes`
- `/workspace`
- `/nix`

Persisting the whole home mount keeps later-installed coding agents and browser tooling persistent without preinstalling them in the base image. That includes XDG state, `~/.agents`, `~/.agent-browser`, `~/.codex`, `~/.gemini`, `~/.copilot`, `~/.npm`, `~/.bun`, `~/.ssh`, `~/.gnupg`, and any other future tool state created under `/home/hermes`.

## `/home/hermes` Layout

Inside the running container:

- `/home/hermes` is both the interactive home directory and the persisted state mount
- `/home/hermes/.hermes` is the managed Hermes service state written by the upstream NixOS module
- named profiles live under `/home/hermes/.hermes/profiles/test` and `/home/hermes/.hermes/profiles/coder`
- `/workspace` remains a separate persisted work directory and is not folded into the home facade

This layout is important:

- managed service state: `/home/hermes/.hermes`
- default CLI/home profile root: `/home/hermes/.hermes`
- named CLI profiles: `/home/hermes/.hermes/profiles/<name>`

That matches upstream Hermes CLI behavior for profiles. The repo-specific deviation is that the managed NixOS-module state now lives inside the persisted home volume instead of a separate `/data` mount.

## Systemd Layout

The container uses a small NixOS-managed unit graph:

- `ghostship-storage.service`
  prepares `/home/hermes`, `/home/hermes/.hermes`, `/workspace`, and `/nix` before user-facing services start
- `hermes-agent.service`
  is the upstream Hermes NixOS-module service, running as `hermes`
- `ghostship-hermes-bootstrap.service`
  is a repo-specific NixOS oneshot that creates the approved `test` and `coder` profiles after the managed Hermes config exists
- `ghostship-dashboard-controller.service`
  serves the static dashboard and proxies on-demand ephemeral `ttyd` sessions on port `7681`

The profile bootstrap unit is an approved custom deviation from upstream. Upstream Hermes does not currently expose named profiles as a declarative NixOS-module option, so the profile names are declared in Nix here and materialized by a NixOS-managed oneshot service.

## Running The Image

```fish
docker run \
  --rm \
  --name ghostship-hermes \
  --publish 7681:7681 \
  --volume ghostship-hermes-home:/home/hermes \
  --volume ghostship-hermes-workspace:/workspace \
  --volume /nix:/nix \
  ghcr.io/caelx/ghostship-hermes:latest
```

Notes:

- Reuse `/nix` only when it already contains compatible Nix state you want to keep. Do not hide a fresh Nix-built image behind a brand-new empty `/nix` volume.
- If you mount `/nix` to a persistent volume, prepopulate that volume with the image's `/nix` contents before first boot. A brand-new empty volume can hide the image store and break startup or Nix operations.
- Fix the per-user Nix ownership on the persisted volume before expecting mutable Nix workflows to work for `hermes`. In practice, `hermes` needs usable paths under `/nix/var/nix/profiles/per-user/hermes` and `/nix/var/nix/gcroots/per-user/hermes`.
- Persisting `/home/hermes` directly is the intended way to keep Hermes managed state, Hermes CLI profiles, XDG state, and later-installed agent tooling across container replacement.
- The dashboard is the intended browser entrypoint.
- Hermes starts with a minimal declarative config so the gateway process comes up cleanly even before you add your own provider or messaging settings.

After startup:

1. Open `http://localhost:7681`.
2. Use `Open Terminal` to launch a new shell-backed `ttyd` session rooted at `/home/hermes`.
3. Each new terminal appears as a focused tab in the left rail immediately, even before the underlying `ttyd` process is ready.
4. Tab labels follow the active shell state, showing `/home/hermes` at the prompt and the current command name while work is running.
5. Use `Close Terminal` to remove the active tab. When no terminals remain, the dashboard returns to the blank home state.

## Hermes Configuration

The image is intentionally declarative-first:

- Hermes managed config is written into `/home/hermes/.hermes`.
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

- `HERMES_HOME=/home/hermes/.hermes`
- `HOME=/home/hermes`
- `hermes` runs as `3000:3000`
- `test` and `coder` are present under `~/.hermes/profiles/...`
- `/home/hermes` itself is the persisted home volume
- the NixOS unit graph comes up in the expected order for storage, Hermes, profile bootstrap, and dashboard
- no custom default skills are seeded
- removed workstation tools are absent by default
- `ghostship-*` utilities remain available
- HOME-backed state survives container replacement
- `nix profile install` survives container replacement with reused `/nix`
- later-installed tool state remains updateable
- `opencode` install plus XDG state survives replacement
- the dashboard can open and close an ephemeral terminal before and after replacement
- the dashboard can manage multiple independent terminal tabs
- the bootstrap `test` and `coder` profiles are available under `~/.hermes/profiles/...`

## Python Utility Workflow

For the standardized Python utility workflow, see [docs/python-utilities.md](docs/python-utilities.md).
