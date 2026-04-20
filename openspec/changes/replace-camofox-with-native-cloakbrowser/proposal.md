## Why

The current browser path is overbuilt for the actual product goal. The image ships a Camofox HTTP shim, a custom VNC/noVNC live-view stack, and a repo-owned `ghostship-cloakbrowser` manager wrapper even though the desired operator outcome is only a working Hermes local browser backed by one persistent Chrome profile.

This change is needed now because the repo already has the pieces to run CloakBrowser as a Chromium-compatible local browser for `agent-browser`, and continuing to carry the Camofox and manager layers keeps the image larger, the dashboard more custom, and the browser contract farther from upstream Hermes than necessary.

## What Changes

- **BREAKING** Remove the internal Camofox browser service, its cache/bootstrap logic, the Camofox VNC/noVNC sidecars, and the published `/camofox/` dashboard path.
- **BREAKING** Remove the repo-owned `ghostship-cloakbrowser` CLI package, docs, tests, and any runtime contract that treats CloakBrowser Manager as a supported workstation surface.
- Install CloakBrowser natively in the image and make Hermes local browser workflows use it through stock `agent-browser` execution, with CloakBrowser presented as the effective local Chrome/Chromium executable.
- Keep one persistent browser profile rooted in persisted Hermes home state so local browser sessions retain login state and normal Chrome profile data across restart and container replacement.
- Simplify the dashboard browser contract so the supported Ghostship dashboard patch remains the `Terminal` entry only; browser automation stays available through Hermes' native browser tooling rather than a repo-owned live-view iframe.
- Update image validation and docs so publication proves the supported native CloakBrowser path and no longer checks retired Camofox or CloakBrowser Manager behavior.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `agent-workstation-home-state`: extend the persisted home-state contract to include the single supported CloakBrowser profile path under `/home/hermes`.
- `agent-workstation-runtime`: change the local browser runtime contract to use image-native CloakBrowser through stock `agent-browser` with one persisted Chrome profile and no Camofox service layer.
- `agent-workstation-updates`: change runtime validation so browser-path proof covers native CloakBrowser launch and persistent-profile behavior rather than only command discovery or Camofox-specific health assumptions.
- `hermes-profile-env-contract`: remove any supported operator-facing browser env contract for Camofox or CloakBrowser Manager and keep the local browser path image-owned instead of downstream-configured.
- `mmx-hermes-dashboard`: remove the repo-owned Browser live-view patch so the dashboard contract keeps only the `Terminal` entry as the supported Ghostship UI delta.
- `live-image-runtime-gaps`: change the live runtime validation surface to prove the upstream Hermes dashboard plus terminal path without the retired `/camofox/` browser iframe path.
- `image-publication-contract`: change publication validation and deployment guidance so the published image contract covers native CloakBrowser-backed Hermes browser automation instead of Camofox or Manager-specific behavior.

## Impact

- Affected image/runtime areas: `packages/hermes-image/Dockerfile`, `packages/hermes-image/rootfs/`, `packages/hermes-image/build/init_home.py`, `packages/hermes-image/build/prepare_upstream_hermes.py`, and the managed runtime Nix module.
- Affected validation and docs: Hermes image smoke tests, live CLI/runtime tests, README/runtime docs, API docs, changelog, and AGENTS memory.
- Affected removed package surface: `packages/cloakbrowser-cli` and references to `ghostship-cloakbrowser`.
- External dependency shape changes: add native CloakBrowser installation/runtime wiring; remove Camofox and CloakBrowser Manager support from the workstation image contract.
