## Why

The current image has accumulated a large Ghostship-managed workstation layer around Hermes: custom runtime bootstrap code, curated skill seeding, Codex/Gemini/Opencode installs and update loops, honcho compatibility handling, and a profile-aware dashboard stack. That makes the image heavier, more opinionated, and less aligned with Hermes' upstream NixOS deployment model than intended.

This change resets the image around upstream Hermes container-mode expectations first. The immediate goal is to build and validate a minimal declaratively configured Hermes container that boots cleanly, uses the upstream `/data` contract for `HERMES_HOME`, proves the correct runtime user and persistence layout, and then rebuild Ghostship-specific additions only where they are still required.

## What Changes

- Rebuild the Hermes image around the upstream Hermes Nix flake and NixOS module/container-mode semantics instead of the current repo-managed runtime bootstrap layer.
- Change the canonical persisted Hermes root from `/opt/data` to `/data` so `HERMES_HOME` aligns with upstream container-mode expectations.
- Add an explicit discovery-and-validation phase as one of the first implementation tasks: build a minimal Hermes container, boot it with a minimal declarative config, and inspect actual runtime paths, user identity, and persistence behavior before wider refactoring.
- Keep only the custom behavior still required for Ghostship:
  - all `ghostship-*` utilities remain installed
  - a minimal browser dashboard remains available
  - `ttyd` sessions are launched and closed on demand and are not persistent services
  - the persisted home facade remains, but it must be as thin as possible
- Remove Ghostship-managed workstation behavior that diverges from upstream Hermes:
  - **BREAKING** remove Codex, Gemini CLI, Opencode, OpenSpec, and `skills` app installation/update flows from the image runtime
  - **BREAKING** remove all custom default skill content from the image, including repo-managed Ghostship skills, vendored Google Workspace skills, and the broader custom local skill inventory
  - **BREAKING** remove honcho compatibility handling and any image-managed honcho layout behavior
  - **BREAKING** remove the custom profile reconciler and per-profile persistent dashboard terminals
  - **BREAKING** remove repo-managed app/asset refresh timers and related systemd user services
- Reduce the preinstalled package set to a lean base centered on upstream Hermes requirements, runtime Nix support, `ttyd`, the minimal dashboard stack, and the retained `ghostship-*` utilities.
- Rework persistence rules to preserve broad common HOME-backed state under `/data/home` rather than only a small package-specific subset, while still validating the actual directories Hermes and retained tools need.
- Rework persistence rules to preserve upstream Hermes profile state under `~/.hermes` through `/data/home` while keeping the canonical managed `HERMES_HOME` at `/data/.hermes`.
- Rework persistence rules so the persisted home facade keeps not only broad common HOME-backed state under `/data/home`, but also the config/state locations expected by coding-agent utilities that are no longer preinstalled by default and may be installed later by the operator or by Hermes.
- Validate that persisted `/nix` supports user-level `nix profile install` and that installed packages survive container replacement when `/nix` is reused.
- Ensure the runtime prepares `/nix/var/nix/daemon-socket` and starts `nix-daemon.socket` so user-level Nix installs actually work in the running container.
- If the rebuilt image uses a dedicated `hermes` user, run it as UID/GID `3000:3000` and validate that this identity works cleanly with the upstream-aligned layout and persisted volumes.
- Replace the current documentation and tests so they describe and verify the new upstream-aligned runtime model instead of the current workstation model.
- Treat this change as incomplete until the final image is built, the full persistence and dashboard validation matrix passes, and a final locally runnable container is left ready for manual dashboard inspection.

## Capabilities

### New Capabilities
- `lean-runtime-package-set`: Defines the minimal preinstalled package inventory for the image, including upstream Hermes prerequisites, the dashboard/`ttyd` surface, runtime Nix support, and the retained `ghostship-*` utilities.
- `minimal-hermes-dashboard`: Defines the smallest supported browser surface for the image: a static dashboard that can launch non-persistent `ttyd` terminal sessions on demand without the current profile-reconciler architecture.

### Modified Capabilities
- `agent-workstation-runtime`: Replace the current custom workstation runtime with an upstream-aligned Hermes container-mode runtime, canonical `/data` state paths, minimal declarative config, and a validation-first bootstrap path.
- `agent-workstation-home-state`: Change the persistence contract to align with `/data`, preserve `/workspace` and `/nix`, and persist broad common HOME-backed state under `/data/home` through a thin facade.
- `agent-workstation-seeding`: Remove repo-managed workstation seeding for Codex/Gemini/Opencode/OpenSpec/skills and limit any remaining seeding to only what the rebuilt minimal image still needs.
- `agent-workstation-updates`: Remove Ghostship-managed app and mutable-asset update loops, timers, and persisted toolchain refresh behavior from the default image runtime.
- `bitwarden-cli-runtime`: Reevaluate the image package set so non-ghostship utilities such as `bws` are no longer assumed to be preinstalled by default.
- `bitwarden-cli-skill`: Remove the image's dependency on repo-managed Bitwarden skill content as part of the general no-custom-skills reset.
- `feed-monitoring`: Reevaluate whether upstream `feed` remains bundled by default in the lean image package set and remove the image's dependency on a repo-managed `feed` skill.
- `google-workspace-cli-runtime`: Remove the assumption that the image ships the pinned upstream `gws` CLI by default in the lean runtime.
- `google-workspace-skills`: Remove vendored Google Workspace skills and the requirement that the image seeds them into Hermes profiles.
- `changedetection-skill`: Remove the image's dependency on repo-managed Ghostship skill payloads as part of the broader no-custom-skills reset.

## Impact

- Affected code:
  - `flake.nix`
  - `packages/hermes-image/*`
  - `packages/feed/*` and non-ghostship package wiring retained only if still justified
  - `skills/`
  - `vendor/googleworkspace-cli/`
  - image/dashboard assets and image tests
- Affected systems:
  - image build composition
  - runtime identity and path layout
  - persistence contract and volume guidance
  - future user-installed coding-agent config/state persistence
  - browser access model
  - runtime documentation and test coverage
- External dependencies:
  - upstream `NousResearch/hermes-agent` flake/module behavior becomes the primary source of truth for runtime structure
- Risks:
  - container-mode and shipped-image persistence models are not identical, so the repo must validate how to adapt upstream semantics without reintroducing a large custom runtime
  - switching to `/data` is a breaking persistence/layout change and will require updated migration/documentation guidance
