## Why

The image currently hardcodes a two-profile Hermes layout centered on `operations` and `coder`, but the intended long-running operator model is now `assistant`, `operations`, and `supervisor`. We need a Nix-first scaffolding change that establishes those three profiles, makes `assistant` the sticky default, and gives us a safe place to iteratively bake in the final Hermes settings without treating mutable runtime skills or secrets as image content.

## What Changes

- Add a Nix-first Hermes profile scaffold for `assistant`, `operations`, and `supervisor`, with `assistant` as the sticky default profile.
- Introduce a single declarative profile matrix in the image module that drives generated profile config skeletons, env file paths, skill roots, and long-running gateway services.
- Keep the root Hermes config minimal and non-authoritative so the named profiles become the real baked-in operating surface.
- Preserve shared skills and profile-specific skills as runtime-seeded content under `/workspace/skills/...`, copied once into Hermes-owned skill trees without overwriting existing destinations.
- Add an explicit audit pass for the Hermes setting surface so we can decide, setting by setting, whether each option belongs in Nix, runtime env, or later Hermes-owned mutable state.
- Make the first implementation step only generate the basic scaffold so later tasks can tune model, auth, terminal, and persona settings from a stable base.

## Capabilities

### New Capabilities
- `hermes-profile-scaffold`: Nix-first scaffolding for the three long-running Hermes profiles, shared/profile skill seeding, minimal root config, and the profile-setting audit workflow.

### Modified Capabilities
- None.

## Impact

- Affected code: `packages/hermes-image`, `packages/hermes-dashboard`, image validation scripts, and supporting docs.
- Affected runtime systems: Hermes profile bootstrap, long-running profile gateway services, dashboard profile metadata, and skill seeding paths.
- Affected operational model: moves the image toward `assistant` / `operations` / `supervisor` as the stable baked-in workflow scaffold while keeping skills and secrets runtime-owned.
