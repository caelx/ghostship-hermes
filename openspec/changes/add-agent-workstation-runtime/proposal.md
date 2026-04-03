## Why

The current image is still documented and structured like a replaceable container runtime with curated tools, but the desired product is a persistent agent workstation that survives rebuilds and restarts with minimal disruption. The workstation needs the latest agent apps and mutable agent environment state to evolve over time, while keeping invocation latency local and cached instead of depending on live updates during every command.

## What Changes

- **BREAKING** Reframe the container from an `s6`-supervised Hermes runtime into a persistent agent workstation whose durable source of truth is the full `/home/hermes` profile.
- **BREAKING** Replace the current `s6` service model with a `systemd`-based runtime that supports both system-level services and `hermes` user services/timers living under the persisted home profile.
- Add a workstation home-state contract that treats `/home/hermes` as durable state across rebuilds and restarts, including app installs, configs, skills, plugins/extensions, updater metadata, and Hermes state.
- Reuse Hermes' native profile model and service-install behavior where possible so profile aliases and persistent gateway services stay aligned with upstream expectations under `systemd`.
- Add a workstation seeding flow that mirrors the repo-managed subset of the user's develop environment into `/home/hermes` non-destructively on boot.
- Add boot-time and timer-driven update services that keep `codex`, `gemini-cli`, `opencode`, `openspec`, `skills`, installed skills, plugins/extensions, and the opencode OpenRouter free-model config current without doing live refreshes in the invocation hot path.
- Rewrite the documentation around the new mental model: this image is an agent workstation optimized for maximum enablement and minimal disruption, not a mostly stateless appliance.
- Require local persistence validation that proves the workstation survives container restart and replacement when `/home/hermes` is reused.

## Capabilities

### New Capabilities
- `agent-workstation-home-state`: Define `/home/hermes` as the persistent workstation state root and document the single-writer, full-home persistence contract.
- `agent-workstation-runtime`: Run the workstation on `systemd`, including support for `hermes` user services and timers stored under the persisted home profile.
- `agent-workstation-seeding`: Mirror the selected develop-environment defaults into the workstation home on boot without clobbering user-managed state.
- `agent-workstation-updates`: Keep installed agent apps and mutable agent assets current through boot-time and timer-driven updates while keeping invocation-time behavior local and cached.

### Modified Capabilities

## Impact

- Container init, supervisor, and service layout under `packages/hermes-image/`
- Runtime persistence and directory contracts for `/home/hermes`
- Bootstrapping and update logic for `codex`, `gemini-cli`, `opencode`, `openspec`, and `skills`
- Repo-managed skill/config seed content and how it is copied into the workstation home
- Documentation in `README.md`, `CHANGELOG.md`, `AGENTS.md`, and runtime guidance skills
- Local verification workflows for rebuild/restart persistence with a reused workstation home
