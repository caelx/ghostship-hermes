# Image Build

## Base Contract

- Base image: `ubuntu:24.04`.
- PID 1: `s6-overlay`.
- Runtime user: `hermes` (`3000:3000`).
- Image-owned Hermes core: `/opt/hermes`.
- Persisted home/work/store: `/home/hermes`, `/workspace`, `/nix`.

## Build Inputs

The Docker build downloads the pinned upstream Hermes tarball from
`packages/hermes-image/hermes-release.txt`, applies repo-owned patches, builds the
dashboard, installs Hermes into `/opt/hermes/venv`, bakes CloakBrowser/uBO Lite,
and seeds `/opt/ghostship/home-seed`.

Repo-owned upstream Hermes patches include Discord channel routing, the dashboard
Terminal entry, direct OpenCode Go reasoning/tool replay compatibility, and
fallback failure logging.

## Home Seeding

`/opt/ghostship/home-seed` is copied into `/home/hermes` with `--skip-old-files`
so downstream custom state survives. The Ghostship wiki is different: it is synced
from `/opt/ghostship/ghostship-wiki` on each boot and overwrites only managed wiki
files, while preserving agent-created files.
