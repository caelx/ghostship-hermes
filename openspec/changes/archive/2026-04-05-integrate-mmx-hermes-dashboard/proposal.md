## Why

The repo already contains a new MMX-style dashboard package in `packages/hermes-dashboard`, but the image, tests, and docs still carry stale assumptions from the older dashboard contract. That leaves the canonical UI only partially integrated: systemd wiring exists, but the runtime path, package/export contract, and smoke tests are not aligned around the packaged dashboard that should actually ship in the Hermes image.

## What Changes

- Make `packages/hermes-dashboard` the canonical dashboard implementation for the Hermes image.
- Build and install the dashboard package through the flake/image path so the container runs the packaged `hermes-dashboard` entrypoint under systemd.
- Remove stale legacy dashboard seams in the image runtime that still reference the deleted old dashboard asset path.
- Align image tests and repo docs with the MMX UI contract instead of the older dashboard markup and copy.
- Verify and document the packaged dashboard runtime contract, including bundled static assets, systemd startup, and on-demand `ttyd` proxy behavior inside the container.

## Capabilities

### New Capabilities
- `mmx-hermes-dashboard`: Defines the canonical packaged MMX dashboard contract for the Hermes image, including bundled static assets, MMX UI entrypoint behavior, and same-origin `ttyd` terminal proxying.

### Modified Capabilities
- `agent-workstation-runtime`: Update the workstation runtime requirements so the browser-facing dashboard path is specifically satisfied by the packaged MMX dashboard running under systemd in the image.

## Impact

- Affected code: `packages/hermes-dashboard`, `packages/hermes-image/*`, `flake.nix`, dashboard smoke tests, and repo runtime documentation.
- Affected systems: Nix package outputs, NixOS image module wiring, container systemd startup, and local/CI dashboard validation.
- Affected dependencies: Python packaging of dashboard static assets and the container runtime path that supplies `ttyd` and the packaged dashboard binary.
