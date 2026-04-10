## Context

The current Hermes image manages a mixed mutable toolchain under `/home/hermes`, including npm-installed agent CLIs. That managed npm set still includes Gemini CLI even though the intended operator workflow has narrowed to Codex and OpenCode.

At the same time, the image still intentionally uses Google's API-backed Gemini model path for Hermes auxiliary tasks. The user explicitly wants to remove only the installed Gemini CLI surface, not the direct Gemini provider wiring or the `GOOGLE_AI_STUDIO_API_KEY` env contract that supports those auxiliary tasks.

This makes the change mostly a contract-alignment cleanup across three surfaces:

- the image-managed npm package list and expected bin set
- current runtime/docs text that describes installed managed CLIs
- live OpenSpec requirements that still name Gemini CLI as part of the current workstation contract

## Goals / Non-Goals

**Goals:**

- Remove Gemini CLI from the image-managed npm toolchain.
- Ensure the current runtime contract advertises only the managed installed CLIs that remain supported.
- Keep the live documentation precise about the distinction between Gemini CLI and Gemini API-backed auxiliary task usage.
- Limit the change to current runtime code and current spec/doc surfaces that define the active contract.

**Non-Goals:**

- Removing or replacing Gemini auxiliary-task model usage.
- Removing `GOOGLE_AI_STUDIO_API_KEY` from the runtime env contract.
- Reworking router behavior, fallback models, or provider selection.
- Rewriting archived change history unless a follow-up explicitly requests archive scrubbing.

## Decisions

### Remove Gemini CLI only from the managed npm layer

The image will stop installing `@google/gemini-cli` and will stop advertising `gemini` as a managed runtime binary. This is the minimal implementation that satisfies the requested change without altering unrelated provider behavior.

Alternative considered: also remove Gemini provider usage from Hermes auxiliary tasks. Rejected because it broadens the scope beyond the requested CLI removal and would change the active model/runtime contract.

### Preserve Gemini API-backed auxiliary task configuration

Current Hermes auxiliary configuration and `GOOGLE_AI_STUDIO_API_KEY` remain unchanged. Documentation must be updated so references to Gemini remain only where they describe that provider path rather than the removed CLI.

Alternative considered: scrub all Gemini references from current docs. Rejected because it would make current provider documentation inaccurate while the image still depends on Gemini for auxiliary tasks.

### Update only live contract surfaces, not archived history

The change will update current code, current docs, and current live OpenSpec capability specs. Archived OpenSpec changes and historical changelog text are out of scope for this proposal unless maintainers later decide they want a repo-history cleanup pass.

Alternative considered: remove all historical Gemini CLI mentions from archived specs and change records. Rejected because it rewrites historical context and is not required to make the active runtime contract correct.

## Risks / Trade-offs

- [Docs accidentally remove valid Gemini provider guidance] -> Mitigate by reviewing each Gemini mention and only removing references that describe the installed CLI surface.
- [Implementation drifts from live OpenSpec contract] -> Mitigate by updating the runtime and seeding capability specs in the same change.
- [Operators assume Gemini is fully removed from the image] -> Mitigate by stating clearly in proposal, design, and docs that Gemini API-backed auxiliary tasks remain supported and unchanged.

## Migration Plan

1. Remove `@google/gemini-cli` and the `gemini` bin from the Hermes image managed npm definitions.
2. Update current repo docs and current AGENTS guidance so managed installed CLI lists contain only the remaining supported CLIs.
3. Update live OpenSpec delta specs for the runtime and seeding capabilities.
4. Verify the repo no longer advertises Gemini CLI as an installed managed runtime tool while still documenting the auxiliary Gemini API path where applicable.

Rollback is straightforward: restore the npm package/bin entries and revert the contract/documentation edits.

## Open Questions

- None for this proposal. The requested scope is now explicit: remove Gemini CLI only and preserve the existing Gemini auxiliary provider path.
