## Why

Hermes `v0.9.0` now ships a native local dashboard with upstream-supported pages for status, config, env, sessions, logs, analytics, cron, and skills. This repo currently maintains a separate packaged FastAPI/React dashboard plus a browser-only `ttyd` console contract, which duplicates upstream surface area, increases drift, and forces Ghostship-specific browser behavior that Hermes no longer needs to own.

## What Changes

- Replace the repo-owned `packages/hermes-dashboard` browser with the upstream Hermes native dashboard from the pinned Hermes release.
- **BREAKING** Change the published browser entrypoint from the repo-owned `7681` contract to the upstream Hermes dashboard port `9119`.
- **BREAKING** Remove the Ghostship-specific browser contract for `/api/health`, `/api/profiles`, `/api/projects`, `/api/console`, the `Console` tab, same-origin `ttyd` proxying, and the `/workspace` Projects panel as first-class dashboard requirements.
- Rework image startup, packaging, health checks, smoke tests, and runtime validation around the upstream dashboard command/API surface instead of the custom dashboard package.
- Preserve or add the runtime/header behavior needed for the native dashboard to be embedded and used inside a cross-origin iframe on the deployed host.
- Preserve the repo’s single managed Hermes agent, non-root runtime, persisted `/home/hermes`, router service, and CLI/debug workflows while letting browser management come from upstream Hermes.
- Update docs, changelog, AGENTS memory, and OpenSpec contracts so the repo stops describing the retired custom dashboard anywhere.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `mmx-hermes-dashboard`: Replace the custom MMX/HUDUI browser and browser-terminal requirements with the upstream Hermes native dashboard contract.
- `live-image-runtime-gaps`: Change live image validation from custom dashboard payloads and browser terminal checks to the upstream dashboard’s managed-runtime pages and APIs.
- `agent-workstation-runtime`: Change the managed browser runtime/process contract to launch the upstream Hermes dashboard command on its native port and remove the repo-owned dashboard controller from the runtime surface.
- `true-hermes-base-image`: Remove the assumption that the final image must layer a repo-owned `hermes-dashboard` package onto the base image, and align the image split with the upstream Hermes dashboard shipping inside the Hermes runtime/toolchain.

## Impact

- Affected code: `packages/hermes-image/*`, `packages/hermes-agent-wrapped/*`, `flake.nix`, and deletion or retirement of `packages/hermes-dashboard/*`.
- Affected runtime systems: `ghostship-hermes-hudui.service`, browser port/publication changing from `7681` to `9119`, container `HEALTHCHECK`, startup ordering, firewall expectations, iframe/header behavior, and validation scripts.
- Affected docs/specs: `README.md`, `CHANGELOG.md`, `AGENTS.md`, dashboard smoke tests, workstation persistence validation, and the listed OpenSpec capabilities.
- Affected operator workflows: browser config/env/session inspection remains, but browser terminal launch and Ghostship-specific dashboard panels are removed from the supported contract.
