# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Split the image build contract into an explicit publishable `ghostship-hermes-image` bundle and a separate `ghostship-hermes-rootfs` tarball, added `scripts/export_publishable_image.sh` as the shared Docker materialization helper, updated the GHCR publish workflow and dashboard smoke test to use that bundle, and kept the full persistence validation on the low-level rootfs path.
- Rebuilt the Hermes image around the upstream Hermes NixOS module with `HERMES_HOME=/home/hermes/.hermes`, `HOME=/home/hermes`, a dedicated `hermes` user at `3000:3000`, a persisted whole-home volume, and a lean default package set that keeps only Hermes, runtime Nix support, the dashboard stack, and the `ghostship-*` utilities.
- Removed the remaining Ghostship workstation baggage from both the image and the repo tree, including repo-managed skills, vendored Google Workspace assets, `feed`, `honcho-ai`, the old `rootfs`, and the old workstation seed payloads.
- Reworked the dashboard into a darker multi-terminal tab UI that keeps the old Hermes logo, removes the old inspect panel, serves directly from the controller process, opens each browser terminal at `/home/hermes`, creates focused tabs immediately with a loading state, labels sessions from the shell cwd or current command, allows unlimited ephemeral `ttyd` sessions, sandboxes the terminal iframe, and returns to a blank home state when all tabs are closed.
- Replaced the old bootstrap profiles with declarative `operations` and `coder` profiles, kept both gateways running through repo-managed systemd units, and made `operations` the sticky default CLI profile.
- Wired the bootstrap flow to consume `OPENROUTER_API_KEY` and `OPENROUTER_TEST_MODEL` from the runtime environment so both declared profiles come up with the same test provider configuration.
- Updated the image tests and validation flow to prove the final runtime contract, including gateway boot, `/home/hermes` persistence, multi-profile layout, multi-terminal dashboard behavior, persisted `/nix` installs, and later-installed tool state persistence across container replacement.
- Fixed the dashboard terminal websocket path so tab switching keeps the live `ttyd` session attached instead of falling into ttyd's reconnect overlay.
