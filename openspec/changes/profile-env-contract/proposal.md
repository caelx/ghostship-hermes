## Why

The Hermes image already treats each managed profile `.env` file as the operator-facing source of truth for profile runtime configuration, but the actual projection contract is still implicit and incomplete. The bootstrap writer persists only a curated subset of container-wide environment variables, the translation rules from repo-owned container env names to profile-local Hermes env names are not fully documented, and the repo does not yet capture a single explicit inventory of which upstream Hermes and repo-owned env inputs belong in profile `.env`.

This matters now because the runtime contract is widening beyond the original Discord-only projection. Operators need one precise source of truth for which container env supplied by `nixos-config` must be copied into each profile `.env`, which values must be translated into profile-local names, and which image, router-daemon, and container boot plumbing values must stay container-only.

## What Changes

- Define the full managed profile `.env` contract for the Hermes image, including the exact supported shared env keys, profile-scoped env keys, and upstream Hermes-facing translations that bootstrap must materialize into each managed profile `.env`.
- Capture the translation rules from repo-owned container env names to profile-local Hermes-facing names, including Discord profile inputs, webhook secret inputs, and compatibility aliases where the container source name differs from the profile-local runtime name.
- Add explicit per-profile browser CDP env names for the managed `assistant`, `operations`, and `supervisor` profiles and map those profile-scoped container env values into the corresponding profile-local `BROWSER_CDP_URL`.
- Classify which container-wide env remain intentionally outside profile `.env` because they are image infrastructure, router-daemon internals, or container boot plumbing rather than profile-facing runtime configuration, with router service variables explicitly excluded from the profile contract.
- Require bootstrap env projection to stay idempotent so unchanged container env does not rewrite profile `.env` files or trigger unnecessary restarts.
- Align the env inventory, bootstrap pass-through contract, and operator-facing docs around one explicit allowlist instead of scattered implicit behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `hermes-profile-env-contract`: Expand the spec to define the complete managed profile `.env` inventory, the shared versus profile-scoped translation rules, the compatibility aliases that bootstrap must normalize into Hermes-facing env names, and the exclusions that remain container-only.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, especially the bootstrap `PassEnvironment` contract and `write_profile_env()` projection logic.
- Affected docs: operator-facing guidance that describes profile `.env`, the Hermes image env contract, and supported runtime configuration.
- Affected validation: image/bootstrap checks that assert profile `.env` contents and restart behavior.
- Affected behavior: managed profile `.env` generation, profile gateway restart visibility, and operator expectations for which `nixos-config` environment variables become profile-local runtime env.
