## Why

The current image is built around a repo-owned multi-profile topology, but that complexity now dominates the runtime contract: bootstrap, env projection, gateway supervision, dashboard status, validation, and operator docs all revolve around profile-specific behavior instead of one clear Hermes agent surface. We want to simplify the product to one managed Hermes agent so the runtime, docs, and operational model all describe the same thing.

This change is needed now because the repo has already accumulated profile-specific Discord, webhook, browser CDP, skills, SOUL, gateway, and validation contracts that make further work harder to reason about. A single-agent overhaul reduces moving parts, removes split authority between root and named profiles, and gives the repo one canonical runtime path to document and maintain.

## What Changes

- **BREAKING** Remove the repo-owned multi-profile topology (`assistant`, `operations`, `supervisor`) and replace it with one managed Hermes agent runtime surface.
- **BREAKING** Replace profile-scoped bootstrap, env, auth, gateway, skills, SOUL, webhook, Discord, browser CDP, and liveness contracts with single-agent equivalents.
- **BREAKING** Replace profile-scoped runtime env source names with a hard-break single-agent env contract built around generic names such as `DISCORD_BOT_TOKEN`, `DISCORD_ALLOWED_USERS`, `DISCORD_FREE_RESPONSE_CHANNELS`, `DISCORD_HOME_CHANNEL`, `WEBHOOK_SECRET`, and `BROWSER_CDP_URL`.
- **BREAKING** Replace profile-state migration with a destructive managed-state reset and clean single-agent reinitialization.
- Make one managed Hermes home the authoritative runtime surface instead of keeping the root config minimal and the named profiles authoritative.
- Replace the three repo-owned profile gateway services, restart helpers, and watched path units with one managed gateway service and one liveness/restart contract.
- Collapse profile-specific env projection into one operator-facing managed env file and one approved single-agent env inventory.
- Collapse skill staging and seed management to one root-only seed layout, one managed skill tree, and one managed `SOUL.md`.
- Update router-primary configuration, browser/dashboard status reporting, and health surfaces to describe one managed agent rather than root-plus-profiles or multiple peer profiles.
- **BREAKING** Remove the profile-oriented dashboard API contract instead of keeping a profile-compatibility shim.
- Rewrite image validation and persistence testing to prove the single-agent runtime contract instead of multi-profile behavior.
- Overhaul user-facing and maintainer-facing documentation so README, Nix/runtime docs, validation guidance, and changelog entries consistently describe one profile, one skill tree, one SOUL, one gateway, and one set of env/config paths.

## Capabilities

### New Capabilities
- `single-hermes-agent-runtime`: Defines the repo-owned single-agent topology, including one authoritative managed Hermes surface, one gateway lifecycle, one env/auth/skills/SOUL contract, and one operational model for the image.

### Modified Capabilities
- `agent-workstation-runtime`: Change the managed runtime identity, invocation, gateway control, and env contract from profile-scoped behavior to one managed agent surface.
- `agent-workstation-updates`: Change doctor/status and replacement-convergence expectations so health and warning reduction target the single managed agent instead of managed profile fleets.
- `agent-workstation-seeding`: Change runtime seeding from shared-plus-profile trees to one managed skill tree and one managed `SOUL.md`.
- `feed-monitoring`: Change persisted `feed` state from profile-scoped storage assumptions to one managed Hermes runtime state path.
- `hermes-profile-env-contract`: Replace the profile `.env` contract with a single managed env contract covering the same supported operator-facing runtime inputs.
- `hermes-profile-webhook-listeners`: Replace per-profile webhook listeners and per-profile secrets with a single managed webhook listener contract.
- `hermes-display-defaults`: Change the display-default requirement from “every managed profile” to the single managed agent config.
- `hermes-runtime-state-markers`: Change `gateway.pid` and related liveness markers from per-profile files to one managed gateway liveness contract.
- `mmx-hermes-dashboard`: Change dashboard runtime reporting and legacy compatibility behavior so the browser surface centers on one managed agent rather than discovered profile topology.
- `router-primary-hermes-runtime`: Change router-primary defaults, startup ordering, and validation from root-plus-profile contracts to the single managed agent runtime.

## Impact

- Affected code: [packages/hermes-image/nixos-module.nix](/home/nixos/dev/ghostship-hermes/packages/hermes-image/nixos-module.nix), [packages/hermes-dashboard/src/hermes_dashboard/app.py](/home/nixos/dev/ghostship-hermes/packages/hermes-dashboard/src/hermes_dashboard/app.py), [packages/hermes-dashboard/src/hermes_dashboard/static/app.js](/home/nixos/dev/ghostship-hermes/packages/hermes-dashboard/src/hermes_dashboard/static/app.js), [packages/hermes-dashboard/src/hermes_dashboard/static/index.html](/home/nixos/dev/ghostship-hermes/packages/hermes-dashboard/src/hermes_dashboard/static/index.html), [scripts/validate_workstation_persistence.sh](/home/nixos/dev/ghostship-hermes/scripts/validate_workstation_persistence.sh), and [tests/hermes-image/profiles-dashboard.sh](/home/nixos/dev/ghostship-hermes/tests/hermes-image/profiles-dashboard.sh).
- Affected runtime systems: Hermes bootstrap, managed env projection, managed user tooling convergence, gateway supervision, router ordering, dashboard status APIs, webhook wiring, Discord/browser CDP wiring, feed persistence, and runtime state markers.
- Affected docs and specs: README, changelog, Nix/runtime docs, dashboard docs, and the OpenSpec capabilities listed above all need coordinated updates so the repo stops describing the removed multi-profile model anywhere.
