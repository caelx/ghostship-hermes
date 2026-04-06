## Context

The current Hermes image is built around two managed profiles, `operations` and `coder`, with `operations` as the sticky default. Bootstrap creates those profiles from Nix-managed shell logic, stages optional shared and per-profile skills from `/home/hermes/seeds/...`, and keeps one gateway service per managed profile. The next configuration phase needs to move to three long-running profiles: `assistant`, `operations`, and `supervisor`.

This design is intentionally Nix-first. The image should define stable structure, generated profile config skeletons, service topology, and the copy-once skill seeding contract. Personal skills, ops runbooks, and profile secrets should continue to come from the runtime environment and become Hermes-owned after first seed. The current scaffold already carries the first shared settings pass: GPT-5.4 primary model routing with Minimax fallback, Gemini auxiliary tasks, Holographic memory, Discord gateway defaults, Tirith, and browser defaults anchored on local `agent-browser`. The first implementation step should only generate the scaffold so later tweaks can fill in the full Hermes settings matrix deliberately.

## Goals / Non-Goals

**Goals:**
- Define a single declarative Nix scaffold for `assistant`, `operations`, and `supervisor`.
- Make `assistant` the sticky default profile.
- Keep the root Hermes config minimal so named profiles become the real operator-facing surface.
- Preserve the shared-skill and per-profile skill seeding model, including the copy-once, never-overwrite behavior.
- Create a structured place to audit and bake Hermes settings over time, preferring Nix configuration before custom mutable config.
- Make the initial implementation safe by generating the scaffold first and deferring detailed tuning to later tasks.

**Non-Goals:**
- Finalize every Hermes setting in the first implementation pass.
- Bake personal or operational skills directly into the image artifact.
- Bake runtime secrets or personal account credentials into Nix.
- Rework the router contract as part of this scaffolding step.

## Decisions

### Use one declarative profile matrix in Nix
The image module should define one structured source of truth for managed profile names, default-profile status, terminal defaults, env destinations, skill destinations, and gateway-service metadata. This avoids hand-maintained duplicated lists across bootstrap, dashboard, and systemd unit generation.

Alternative considered: keep separate hardcoded lists for bootstrap, dashboard, and services. Rejected because the current two-profile setup already shows how easy it is for these lists to drift.

### Keep root config minimal and non-authoritative
The root Hermes config should only provide the minimal runtime baseline required for Hermes to start. The named profiles should carry the meaningful baked-in operator behavior, and `assistant` should be activated as the sticky default profile at bootstrap.

Alternative considered: use root config as the main default and override it per profile. Rejected because the user explicitly does not want the root config to be the real working surface.

### Keep skills runtime-seeded, not image-baked
Shared skills and profile-specific skills should continue to seed from `/home/hermes/seeds/shared/skills/<skill>` and `/home/hermes/seeds/profiles/<profile>/skills/<skill>`, with optional per-profile `SOUL.md` files at `/home/hermes/seeds/profiles/<profile>/SOUL.md`. Bootstrap should copy them into `~/.hermes/...` only when the destination file or skill does not already exist. This keeps the image structural while allowing Hermes to own profile state after first seed.

Alternative considered: bake default skills into Nix. Rejected because the desired skills are expected to evolve quickly and are closer to runtime state than platform state.

### Stage the migration by scaffolding first
The first implementation task should only add the scaffolding data model and generation path. Only after that scaffold exists should later tasks migrate live profile names, gateway services, dashboard expectations, and the rest of the Hermes settings matrix.

Alternative considered: switch directly from the current two-profile runtime to the final three-profile behavior in one step. Rejected because too many settings are still being decided.

### Audit Hermes settings explicitly before baking them
The change should include a deliberate pass over the Hermes settings surface to decide, option by option, whether each setting should live in generated Nix config, runtime env, or later mutable Hermes-owned state.

Alternative considered: bake settings opportunistically during implementation. Rejected because the user wants a careful final configuration pass rather than incremental drift.

## Risks / Trade-offs

- [Scaffold and live runtime diverge during the transition] → Keep the first task strictly additive, then migrate runtime behavior only after the scaffold is in place.
- [Profile metadata drifts between bootstrap, services, and dashboard] → Generate all profile-facing outputs from one Nix data structure.
- [Upstream Hermes `profile create` seeds unexpected default content] → Accept that behavior for the initial scaffold, document it, and only add cleanup if it causes real friction.
- [Too many settings get deferred and the scaffold stalls] → Add a dedicated settings-audit task group with explicit categories so the proposal keeps momentum.
- [Runtime-provided skills and secrets are mistaken for image defaults] → Document clearly that the image bakes only structure while `/home/hermes/seeds/...` and env files remain runtime-owned inputs.

## Migration Plan

1. Introduce the declarative three-profile scaffold while leaving the current runtime behavior understandable.
2. Generate the new profile config skeletons, env destinations, and skill destination rules from that scaffold.
3. Migrate the managed profile services, dashboard metadata, and bootstrap default-profile behavior to `assistant`, `operations`, and `supervisor`.
4. Work through the Hermes settings matrix and bake decisions into the scaffold iteratively.
5. Update validation and docs once the new profile scaffold becomes the active runtime contract.

## Open Questions

- What is the exact upstream Hermes config shape we want for the shared default provider/model path once the setting audit reaches model/auth configuration?
- Should `operations` and `supervisor` share `/workspace` as their default terminal cwd, or should they get separate workspace roots?
- Which upstream Hermes-created profile defaults, if any, should be tolerated versus cleaned up during bootstrap?
- Which settings should remain shared across all three profiles versus intentionally diverge by profile?
- Whether any future browser-provider defaults beyond local `agent-browser` should be declared in Nix, given that Hermes only documents one active `BROWSER_CDP_URL` target and manual `/browser connect` attachment.
