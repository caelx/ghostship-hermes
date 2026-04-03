## Context

The repo currently packages Hermes and curated agent tooling into an image that runs under `s6`, seeds default skills into `~/.hermes/skills`, and expects the image to provide most of the operator environment. That model is good for a reproducible appliance, but it is not the model the user wants. The target system is a persistent agent workstation whose state, installed tools, configs, skills, plugins, and learned environment survive rebuilds and restarts with minimal disruption.

Upstream Hermes Docker guidance also reinforces the persistent-state model: Hermes treats its mounted data directory as the single source of truth and expects image upgrades to preserve that mounted state. This image should generalize that idea from an app data directory into a full home-backed workstation rooted at `/home/hermes`.

Upstream Hermes profile guidance also matters here. Hermes already scopes profiles through `HERMES_HOME`, installs per-profile command aliases under `~/.local/bin`, and exposes a native `gateway install` path that creates a profile-scoped `systemd` or launchd service. That means the workstation should reuse Hermes' own profile and gateway service mechanisms where possible instead of replacing them wholesale with bespoke profile-service generation.

The user's local NixOS develop setup already captures the desired agent environment shape: Codex, Gemini CLI, Opencode, OpenSpec, `skills`, a shared `.agents` tree, generated Opencode model config, and automatic refreshes for skills and OpenSpec. The important translation work is to move that behavior out of invocation-time wrappers and into boot-time plus timer-driven workstation maintenance, while preserving state locally under the workstation home profile.

## Goals / Non-Goals

**Goals:**
- Treat the full `/home/hermes` profile as the durable workstation state that survives rebuilds and restarts.
- Replace the current `s6` runtime with a `systemd` runtime that can host both system services and `hermes` user services/timers.
- Install `codex`, `gemini-cli`, `opencode`, `openspec`, and `skills` as normal apps for the workstation, not as wrapper-driven one-off commands.
- Mirror the selected subset of the user's develop-environment defaults into the workstation home without overwriting user-managed edits.
- Keep apps, skills, plugins/extensions, OpenSpec instructions, and opencode model config current through boot-time and timer-driven refresh.
- Keep invocation-time behavior local and cached, with no mandatory live update on every command.
- Validate locally that a rebuilt or restarted container with the same persisted `/home/hermes` retains the workstation state and resumes correctly.

**Non-Goals:**
- Preserving the existing `s6` service model.
- Keeping the image strictly reproducible at the expense of workstation continuity.
- Copying the user's WSL-oriented wrapper scripts directly into the container runtime.
- Supporting concurrent multi-container access to the same persisted workstation home.

## Decisions

### Make `/home/hermes` the durable workstation root

The system should explicitly document and implement `/home/hermes` as the durable workstation profile, not only `~/.hermes`. All app installs, configs, user services, skills, extensions, updater metadata, and Hermes state should live under that home so container rebuilds and restarts can reuse the entire workstation.

Alternative considered: persist only `~/.hermes` or a curated subset of home. Rejected because the user explicitly wants workstation continuity for installed apps, configs, and evolving agent assets, not only Hermes application data.

### Switch from `s6` to `systemd` for the workstation runtime

The runtime should move to `systemd` so the workstation can run both system services and a `hermes` user manager with persisted user services/timers under `~/.config/systemd/user`. That matches the home-first workstation model better than hand-managed loop services under `s6`.

Alternative considered: keep `s6` and add scheduler loops. Rejected because the runtime goal has shifted from “simple service supervision” to “durable workstation with user-owned automation,” where `systemd` timers and user services are a better fit.

### Reuse Hermes' native profile aliases and gateway install flow

The workstation should preserve Hermes' upstream profile model: profile command aliases remain `HERMES_HOME`-scoped wrappers, and profile gateway persistence should lean on Hermes' native `gateway install` behavior where it fits the workstation runtime. The container should not replace that model with a completely separate profile-service abstraction unless upstream capabilities are missing.

Alternative considered: keep a wholly custom profile service generator for every profile terminal and gateway workflow. Rejected because it drifts from upstream Hermes behavior at the same moment the runtime is moving closer to upstream systemd assumptions.

### Keep agent apps installed as normal apps, updated at boot and on timers

`codex`, `gemini-cli`, `opencode`, `openspec`, and `skills` should be installed like normal apps for the workstation and updated automatically on boot and during the day. Invocation-time behavior should use the already-installed local versions and should not need wrapper-triggered refreshes.

Alternative considered: keep image-baked versions only, or keep the current wrapper-driven `npx` model. Rejected because the user wants latest binaries on boot and during the day, and the wrapper model exists for non-persistent WSL environments rather than this persistent workstation container.

### Use versioned installs plus atomic symlink flips under the workstation home

The updater should install app versions into versioned directories under a workstation-managed subtree and flip stable symlinks only after a successful install and validation. Failed updates should leave the previous working version in place.

Alternative considered: in-place mutation of a single install directory. Rejected because it makes partial updates and interrupted installs more disruptive during boot and timer refreshes.

### Mirror a repo-managed develop seed tree rather than reading the host NixOS tree at runtime

The repo should carry a workstation seed representation of the selected develop-environment defaults: `.agents/AGENTS.md`, desired skills/plugins, Codex config, Gemini settings, Opencode base config, extension inventories, and related workstation defaults. Boot-time seeding should copy missing or managed content from that repo-managed tree into `/home/hermes`.

Alternative considered: read `/home/nixos/nixos-config/modules/develop` directly at runtime. Rejected because the container should not depend on the host filesystem layout, and the workstation bootstrap needs to work on any server deployment.

### Separate boot seeding from periodic refresh jobs

Boot should do a one-shot convergence pass so the workstation is ready immediately after restart, while periodic timers should handle app updates, mutable asset refresh, OpenSpec refresh, and opencode model regeneration later. The hot path for agent invocations should never block on those network operations.

Alternative considered: refresh mutable state on every app invocation. Rejected because it slows the hot path and duplicates work in a persistent environment.

### Treat local persistence testing as a design requirement, not an optional verification

The implementation should prove locally that a reused `/home/hermes` keeps the workstation intact across container restart and replacement, including seeded configs, installed apps, user timers, and mutable state. This validation must be part of the change tasks and docs.

Alternative considered: rely on reasoning and unit-level checks only. Rejected because the user explicitly wants the workstation persistence theory validated against a real local reuse flow.

## Risks / Trade-offs

- [Switching init systems increases runtime migration complexity] -> Keep the migration scoped to the workstation model, document service ownership clearly, and verify system plus user units locally before removing the old supervisor path.
- [Full-home persistence can accumulate stale state and disk growth] -> Document the home-first model explicitly, keep updater state organized under dedicated subtrees, and prefer atomic versioned installs over ad hoc mutable directories.
- [Live network update failures could disrupt boot] -> Treat boot updates as best-effort convergence that preserves the previously working local install and cached state on every failure.
- [User timers and mutable installs make behavior depend on persisted state] -> Embrace that model in the docs, keep the image as a repair/bootstrap substrate, and validate continuity with real persisted-home tests.
- [Concurrent use of the same workstation home can corrupt state] -> Document a single-writer rule and treat one persisted `/home/hermes` as belonging to one active workstation container at a time.

## Migration Plan

1. Define and document the workstation home-state contract around persisted `/home/hermes`.
2. Introduce the systemd-based runtime with the required system services and `hermes` user manager, preserving Hermes-native profile and gateway service behavior where possible.
3. Add the workstation seed tree and boot-time seeding flow for develop-environment defaults.
4. Add updater services/timers for apps, mutable assets, OpenSpec refresh, and opencode model config refresh.
5. Rewrite the docs and environment guidance around the agent workstation mental model.
6. Validate locally that a persisted `/home/hermes` survives restart and container replacement without losing workstation state.
7. Remove or retire the old `s6` assumptions once the new runtime path is verified.

## Open Questions

- Which subset of the user's develop environment should be mirrored into the repo-managed workstation seed tree on day one, versus deferred to later workstation expansion?
- Should app update timers run on distinct schedules per app category, or should there be one shared workstation updater service with per-category phases and lock management?
- How much of the previous image-baked toolchain should remain as fallback tooling once the home-managed app install path is in place?
