## Context

The current image carries two overlapping Hermes surfaces:

- the root managed home at `/home/hermes/.hermes`
- the repo-owned named profile fleet under `/home/hermes/.hermes/profiles/<name>`

In practice, the named profiles are the authoritative surface. The image module generates a profile matrix, bootstrap creates and prunes profile directories, runtime env is rewritten into per-profile `.env` files, three repo-owned systemd services supervise three long-running gateways, the dashboard reports profile topology, and validation asserts multi-profile behavior. The docs mirror that split model across README, runtime guidance, dashboard docs, and multiple OpenSpec capabilities.

That architecture is now the main source of complexity:

- root and named profiles have different responsibilities
- auth, config, env, gateway, `SOUL.md`, and skills all have profile-specific variants
- Discord, webhook, and browser CDP contracts multiply across profiles
- tests and docs must explain both root and named-profile behavior
- stale specs still talk about older `operations`/`coder` variants while current runtime uses `assistant`/`operations`/`supervisor`

The requested direction is a full simplification, not a compatibility layer: one profile, one set of skills, one SOUL, one managed agent surface everywhere.

## Goals / Non-Goals

**Goals:**

- Make `/home/hermes/.hermes` the single authoritative managed Hermes runtime surface.
- Remove the repo-owned named-profile topology from runtime behavior, tests, and documentation.
- Converge config, auth, env, gateway state, skills, and `SOUL.md` onto one managed location.
- Replace the three gateway services and their restart/watch graph with one managed gateway service.
- Define one operator-facing runtime env contract for Discord, webhook, browser CDP, provider credentials, and installed utility env.
- Replace shared-plus-profile skill seeding with one managed skill tree and one seed-managed `SOUL.md`.
- Update dashboard APIs and UI so they describe one managed agent without profile cards or default-profile assumptions.
- Rewrite validation to prove the single-agent contract through build, boot, persistence, and dashboard checks.
- Overhaul README, changelog, and supporting docs so the repo no longer documents removed profile behavior anywhere.

**Non-Goals:**

- Reintroduce compatibility aliases that preserve the three-profile runtime as a supported steady-state model.
- Add new personas, new long-running gateways, or a replacement multi-agent abstraction in the same change.
- Change the approved extra CLI inventory unless required to finish the single-agent migration.
- Redesign the router itself; this change only realigns the Hermes runtime, dashboard, and validation surfaces around the single-agent topology.

## Decisions

### 1. Root managed home becomes the only authoritative agent surface

The repo will treat `/home/hermes/.hermes` as the single managed agent home. The current “minimal root plus authoritative named profiles” split goes away.

Rationale:

- It removes the root-vs-profile ambiguity that currently leaks into docs, bootstrap, and CLI guidance.
- It matches the user request for one profile and one runtime surface.
- It reduces every path question to one canonical location: config, env, auth, skills, SOUL, pidfiles, and state all live under one tree.

Alternatives considered:

- Keep one named profile such as `assistant` and continue treating root as minimal. Rejected because it preserves the two-surface model and still requires `hermes -p ...` everywhere.
- Keep named profiles internally but expose only one in docs. Rejected because that would hide complexity rather than remove it.

### 2. The repo-owned gateway topology collapses to one managed gateway service

The image will replace `ghostship-hermes-profile-*` services, restart helpers, and watched path units with one repo-owned managed gateway service and one restart/watch contract.

Planned steady-state contract:

- one gateway service
- one `gateway.pid`
- one watched config/env/auth/SOUL set
- one dashboard-reported runtime identity

Rationale:

- Service supervision is currently the sharpest expression of the multi-profile contract.
- One service aligns with one operator mental model, one status path, and one liveness marker.
- The current path/watch graph becomes much easier to validate after persistence and replacement.

Alternatives considered:

- Reuse the upstream `hermes-agent.service` as the only runtime service. Rejected because the repo still needs explicit control over managed boot ordering, liveness markers, and restart wiring.
- Keep multiple repo-owned services but point them at one profile. Rejected because it keeps needless coordination and port contention logic.

### 3. One managed env contract replaces all profile-specific env projection

The operator-facing runtime env contract will converge on one managed `.env` file at the root managed Hermes home. Bootstrap will project the approved allowlist into that file and the managed gateway service will read it through `EnvironmentFile`.

The steady-state operator-facing sources will become singular:

- one managed `.env`
- one browser CDP input using `BROWSER_CDP_URL`
- one Discord input set using generic names such as `DISCORD_BOT_TOKEN`, `DISCORD_ALLOWED_USERS`, `DISCORD_FREE_RESPONSE_CHANNELS`, and `DISCORD_HOME_CHANNEL`
- one webhook secret/input set using `WEBHOOK_SECRET`

Rationale:

- The current env contract is the largest profile-specific surface in the repo.
- One file makes operator edits, restart wiring, docs, and tests significantly simpler.
- This preserves the repo’s preference for env/config-managed local topology while removing redundant per-profile copies.
- The chosen rollout is a hard break, so the new contract should not keep old profile-scoped source vars alive.

Alternatives considered:

- Drop generated env files entirely and load raw container env directly in the gateway service. Rejected because the repo already depends on a managed operator-facing file contract and watched rewrite path.
- Keep per-profile env files but generate only one active file. Rejected because that would leave dead contracts and dead docs in place.
- Keep a temporary compatibility bridge from old profile-scoped source vars to the new generic names. Rejected because the chosen migration is an intentional hard break rather than a compatibility rollout.

### 4. One skill tree and one `SOUL.md` replace shared-plus-profile seeding

Bootstrap seeding will converge on one runtime-owned skill tree and one seed-managed `SOUL.md`. The current split between shared skills and per-profile skills/SOUL files will be removed from the runtime contract and replaced with one canonical root seed layout:

- `/home/hermes/seeds/skills/<skill>/...`
- `/home/hermes/seeds/SOUL.md`

Those seeds will converge into one canonical runtime destination under `/home/hermes/.hermes`, and the implementation must verify that skills are actually copied to the intended managed destination instead of only rewriting the source layout.

Rationale:

- “One set of skills, one soul” is a direct product requirement for this refactor.
- The current profile seed tree complicates bootstrap logic, migration, and documentation.
- One canonical destination makes copy-if-missing and seed-hash update rules easier to explain and verify.

Alternatives considered:

- Keep the shared skill tree and only remove per-profile skill trees. Rejected because it still forces docs and bootstrap to explain two seeding concepts.
- Stop repo-managed seeding entirely. Rejected because the repo still wants a declarative starting scaffold for the managed runtime.

### 5. Dashboard APIs will stop treating profiles as the primary runtime abstraction

The dashboard backend and frontend will be rewritten so the home view and status payload describe one managed agent runtime. The profile-oriented API contract will be removed rather than preserved as a compatibility shim.

Rationale:

- The current dashboard backend still computes and emits profile topology.
- The frontend still treats “profiles” as a visible operator concept.
- A single-agent runtime should present one managed agent, not one-item profile lists that keep old terminology alive.
- The chosen rollout is a hard break, so keeping a profile-shaped compatibility API would dilute the new contract.

Alternatives considered:

- Preserve the dashboard profile model with a singleton entry. Rejected as the primary contract because it keeps the wrong abstraction and leaks implementation history into the UI.
- Keep a temporary legacy `/api/profiles.json` shim. Rejected because the chosen migration explicitly removes profile-oriented API behavior.

### 6. Documentation overhaul is part of the implementation, not cleanup

The migration will update README, changelog, runtime docs, dashboard docs, validation guidance, and capability specs in the same change set as the runtime code.

Rationale:

- The current documentation is saturated with profile-specific guidance.
- Shipping code without rewriting docs would leave the repo internally contradictory.
- This refactor changes the product contract, so the docs are part of the deliverable.

Alternatives considered:

- Land runtime changes first and rewrite docs later. Rejected because it would leave operators with invalid instructions for the new image.

## Risks / Trade-offs

- [Risk] Persisted homes may contain named-profile data that the new runtime no longer reads. → Mitigation: make the rollout explicit as a destructive managed-state reset, document that old managed Hermes state is deleted, and reinitialize the runtime cleanly under the new single-agent contract.
- [Risk] Changing env names from profile-specific sources to one single-agent contract can break existing deployment configuration. → Mitigation: document the new env contract exhaustively and decide whether bootstrap should perform a one-time migration read from old profile-scoped source vars during rollout.
- [Risk] Removing profile-specific services changes health, restart, and status expectations. → Mitigation: update systemd naming, pidfile rules, dashboard status payloads, and validation together so they move atomically.
- [Risk] Legacy browser clients may still call profile-oriented dashboard endpoints. → Mitigation: keep a temporary compatibility shim for legacy profile payloads during the transition while changing the primary API and UI terminology to one managed agent.
- [Risk] Feed, Discord, webhook, and browser CDP behavior may accidentally retain hidden profile assumptions in downstream scripts or docs. → Mitigation: include those surfaces explicitly in spec deltas, implementation tasks, and documentation audit steps.
- [Risk] The proposal touches many existing OpenSpec capabilities, which increases archive/review complexity. → Mitigation: keep one coherent change that rewrites all affected contracts together rather than scattering partial changes across multiple smaller proposals.

## Migration Plan

1. Define the new single-agent contract in proposal/spec/design artifacts before implementation starts.
2. Replace the image module’s profile matrix, profile bootstrap loops, profile env projection, and per-profile service graph with a root-managed single-agent topology.
3. Replace the old managed Hermes state with a destructive reset, then reinitialize skill seeding, `SOUL.md`, auth, pidfile, and restart wiring under the new root-managed locations and verify that runtime seeds are copied into the intended managed destination under `/home/hermes/.hermes`.
4. Rewrite dashboard backend/frontend status modeling, remove profile-oriented API behavior, and update validation to assert one managed agent rather than multiple profiles.
5. Overhaul repo docs to describe the new path layout, env contract, gateway contract, skills contract, and operator workflows.
6. During rollout, delete the old managed Hermes state and reinitialize the runtime under the new single-agent topology instead of carrying forward profile-local state.
7. Validate build, boot, dashboard, persistence, and managed status behavior on the new topology.

Rollback strategy:

- Because the change is fully breaking at the runtime-contract layer, rollback is “revert to the prior image and specs” rather than “toggle a flag.”
- Because rollout deletes the old managed Hermes state, rollback must assume a fresh reinitialization of the prior runtime contract rather than restoration from transformed profile-local state.

## Open Questions

- None for proposal scope. The managed-state reset and reinitialization policy resolves the profile-state migration ambiguity.
