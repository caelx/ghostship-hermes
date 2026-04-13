## Context

The current runtime contract splits operator tooling across three delivery paths:

- the immutable image layer for boot-critical services and a small approved baked CLI exception set
- the managed Hermes-user Nix profile at `/home/hermes/.local/state/nix/profiles/ghostship-managed` for stable mutable user tooling and runtime dependencies such as `nodejs_22`
- the managed npm prefix under `/home/hermes/.local/bin` for fast-moving agent CLIs that intentionally live outside the Nix closure

`codex` already uses that second-and-third-layer split: `nodejs_22` comes from the managed Nix profile, while `@openai/codex` is installed by the managed user-tooling refresh into the persisted npm project at `/home/hermes/.hermes/hermes-agent`, and the `codex` binary is projected onto PATH through a symlink in `/home/hermes/.local/bin`.

Gemini CLI used to exist in that managed npm layer and was later removed when the repo narrowed its default agent-CLI surface. The user now wants it restored the same way `codex` works. That means the design needs to restore Gemini CLI through the managed npm tooling flow, keep the immutable image and seeding policies unchanged, preserve the existing Gemini auxiliary-provider runtime env contract, and update validation/docs so the runtime contract stays explicit.

## Goals / Non-Goals

**Goals:**

- Expose `gemini` from the managed persisted npm tool prefix after user-tooling convergence.
- Keep `gemini-cli` out of the immutable image CLI exception set.
- Mirror the existing `codex` delivery model: Node from the managed Nix profile, Gemini CLI from the managed npm project and `.local/bin` symlink projection.
- Update docs and smoke validation so the runtime contract clearly describes `gemini` as managed npm user-layer tooling.

**Non-Goals:**

- Reintroducing Gemini CLI as seeded workstation content under `/home/hermes` or any Ghostship-managed default skill/workstation tree.
- Changing Gemini auxiliary-task provider wiring or the `GOOGLE_AI_STUDIO_API_KEY` env contract.
- Broadening the managed npm tooling model to include Gemini again.
- Reworking the broader split between image-managed, Nix-profile-managed, and npm-managed runtime tooling.

## Decisions

### 1. Install Gemini CLI through `managedNpmPackages`, the same way `codex` is installed

The runtime should restore Gemini CLI by adding `@google/gemini-cli` to the existing managed npm package list in `packages/hermes-image/nixos-module.nix`, so boot-time and timer-based tooling refresh install it into the persisted tooling project and project its `gemini` binary into `/home/hermes/.local/bin`.

Rationale:

- The user explicitly asked to follow the current `codex` model.
- The repo already has a working delivery path for fast-moving agent CLIs through the persisted npm project and `.local/bin` symlinks.
- Reusing that path keeps Gemini CLI aligned with the existing agent-CLI update flow instead of inventing a new special case.

Alternatives considered:

- Install Gemini CLI through `managedUserPackages`. Rejected because that would not match the current `codex` mechanism the user asked to mirror.
- Add Gemini CLI to the immutable image. Rejected because it would widen the baked default-image CLI policy for a non-boot-critical tool.

### 2. Keep Node in the managed Nix profile and the `gemini` binary in the managed npm prefix

The change should preserve the current split used by `codex`: `nodejs_22` remains part of the managed Nix profile, while the actual Gemini CLI package lives in the managed npm project and resolves from `/home/hermes/.local/bin/gemini`.

Rationale:

- This matches the current runtime shape exactly instead of partially copying it.
- The managed npm prefix is already first on the Hermes-user PATH, so operator-facing invocation stays simple.
- The user-tooling refresh code already knows how to create and normalize these symlinks.

Alternatives considered:

- Move `codex` and Gemini together into the managed Nix profile. Rejected because it broadens the current change far beyond the request and abandons the repo's existing fast-moving npm CLI workflow.
- Add a bespoke wrapper outside the managed npm bin projection. Rejected because the existing symlink projection already solves the path problem cleanly.

### 3. Treat this as a contract change across runtime docs, refresh behavior, and validation

The implementation should update the runtime documentation, the managed user-tooling refresh contract, and the Hermes-image validation suite so the supported `gemini` command is described and smoke-tested as part of the managed npm tool set.

Rationale:

- The repo already has archived history for removing Gemini CLI; reintroducing it without current contract updates would recreate policy drift.
- Validation should prove the command resolves from the supported PATH source and launches successfully with a non-destructive smoke command.
- The docs need to remain precise about the difference between the Gemini CLI surface and the separate Gemini API-backed auxiliary model path.
- The update contract needs to remain explicit that Gemini follows the same persisted npm refresh flow as `codex`.

Alternatives considered:

- Add the package silently and rely on implementation readers to infer the new contract. Rejected because the managed runtime contract is operator-facing and needs explicit documentation.

## Risks / Trade-offs

- [Risk] Reintroducing Gemini CLI through npm could accidentally reintroduce broader retired workstation assumptions. → Mitigation: keep the change limited to the same managed npm contract currently used for `codex` and `opencode`, without reviving seeding or image-layer installation.
- [Risk] Older persisted home-local `gemini` shims could point at stale installs. → Mitigation: rely on the existing symlink-normalization behavior in managed tooling refresh and validate the resolved command path.
- [Risk] Reintroducing Gemini CLI could blur the repo's earlier decision to remove it from the default runtime surface. → Mitigation: keep the scope explicit that this is a managed npm user-tooling addition only, with no image-layer or seeding-policy change.
- [Risk] Docs could conflate Gemini CLI with Gemini auxiliary-provider usage. → Mitigation: update operator-facing docs to describe those as separate concerns in the same change.

## Migration Plan

1. Extend `managedNpmPackages` and `managedNpmBins` so the managed tooling refresh installs Gemini CLI into the persisted npm project and projects `gemini` into `/home/hermes/.local/bin`.
2. Keep the existing managed `nodejs_22` dependency in the Hermes-user Nix profile so the npm-managed CLI has its runtime.
3. Update runtime docs and validation to describe and exercise `gemini` from the managed npm user-layer PATH.
4. Verify the managed refresh behavior remains aligned with the existing `codex`/`opencode` workflow.

Rollback strategy:

- Remove the Gemini CLI npm package/bin entries and revert the related docs/spec/validation changes.
- Because the tool lives in the managed user-layer tooling flow rather than the immutable image, rollback remains a convergence-layer change instead of a base-image contract change.

## Open Questions

- None for proposal scope. The requested direction is now explicit: Gemini CLI should follow the existing `codex` managed npm workflow.
