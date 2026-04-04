# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Rebuilt the Hermes image around the upstream Hermes NixOS module with `HERMES_HOME=/home/hermes/.hermes`, `HOME=/home/hermes`, a dedicated `hermes` user at `3000:3000`, a persisted whole-home volume, and a lean default package set that keeps only Hermes, runtime Nix support, the dashboard stack, and the `ghostship-*` utilities.
- Removed the remaining Ghostship workstation baggage from both the image and the repo tree, including repo-managed skills, vendored Google Workspace assets, `feed`, `honcho-ai`, the old `rootfs`, and the old workstation seed payloads.
- Reworked the dashboard into a multi-terminal tab UI that keeps the old Hermes logo, serves directly from the controller process, opens each browser terminal at `/home/hermes`, allows unlimited ephemeral `ttyd` sessions, and returns to a blank home state when all tabs are closed.
- Bootstrapped `test` and `coder` Hermes profiles from NixOS-managed startup so the upstream `~/.hermes/profiles/...` layout is immediately available for inspection.
- Updated the image tests and validation flow to prove the final runtime contract, including gateway boot, `/home/hermes` persistence, multi-profile layout, multi-terminal dashboard behavior, persisted `/nix` installs, and later-installed tool state persistence across container replacement.
