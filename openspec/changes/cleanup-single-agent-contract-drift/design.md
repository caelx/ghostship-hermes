## Context

The single-agent runtime work is already reflected in the image module, bootstrap flow, gateway service graph, dashboard payload, and validation behavior. The remaining drift is contractual and descriptive: several live OpenSpec files still describe `hermes -p <profile>` workflows, profile-fleet gateway behavior, and named-profile feed isolation, while a dashboard README and smoke-test name still use profile-era terminology.

This cleanup crosses specs, docs, and test naming, but it is not a second runtime redesign. The design constraint is to make the written contract match the current runtime without reopening settled behavior or adding compatibility layers back into the supported model.

## Goals / Non-Goals

**Goals:**
- Make the active OpenSpec requirements describe the current single-agent image topology.
- Remove stale named-profile wording from runtime invocation, gateway health, state-marker, and feed-persistence contracts.
- Align maintainer-facing docs and smoke-test naming with the existing single-agent dashboard/runtime contract.
- Keep the cleanup narrow enough that it can be reviewed as contract drift removal rather than a functional image change.

**Non-Goals:**
- Rework the image module, bootstrap logic, or dashboard API shape beyond tiny support edits needed by renamed tests/docs.
- Rename every historical capability or archived change that still contains the word `profile`.
- Introduce new single-agent behavior that is not already present in the runtime.

## Decisions

### 1. Treat the current image runtime as the source of truth

The design anchors on the runtime that already exists in `packages/hermes-image` and `packages/hermes-dashboard`. The cleanup will update OpenSpec and docs to match that behavior rather than proposing further topology changes.

Rationale:
- The repo already has one managed home, one gateway service, and one dashboard agent surface.
- Using the runtime as truth keeps this change bounded and avoids reopening the single-agent migration itself.

Alternatives considered:
- Expand the change into another runtime refactor. Rejected because the user asked for cleanup, not more topology work.
- Preserve profile-era wording as compatibility documentation. Rejected because it obscures the supported contract.

### 2. Limit spec edits to the capabilities that still contradict the runtime

Only the capabilities with active profile-era contradictions will get delta specs: `agent-workstation-runtime`, `agent-workstation-updates`, `feed-monitoring`, and `hermes-runtime-state-markers`.

Rationale:
- Those are the places where the current contract still materially misstates supported behavior.
- Other profile-named capabilities may remain oddly named, but if their requirement text already matches the single-agent runtime, renaming them is churn rather than cleanup.

Alternatives considered:
- Sweep every spec file containing the word `profile`. Rejected because many references are domain-level or historical and not part of the image topology drift.

### 3. Keep documentation and test cleanup coupled to the spec cleanup

The dashboard README and the dashboard smoke-test naming will be updated in the same change as the spec deltas.

Rationale:
- Maintainers use those files as the practical contract for local verification.
- Leaving a profile-era smoke-test name in place undermines the point of fixing the specs.

Alternatives considered:
- Fix OpenSpec now and docs/tests later. Rejected because that would keep the repo split between “formal” and “practical” contracts.

## Risks / Trade-offs

- [Risk] A wording cleanup could accidentally change requirement meaning instead of just clarifying it. → Mitigation: keep the deltas tied to already-shipped runtime behavior and avoid adding new obligations that the current image does not meet.
- [Risk] Some remaining profile references outside this scoped set may still exist after the change. → Mitigation: treat this change as cleanup of the known contract drift identified in exploration, not a repo-wide text purge.
- [Risk] Renaming the smoke test could break maintainer habits or README commands. → Mitigation: update README references in the same change and keep the test behavior itself unchanged.

## Migration Plan

1. Update the affected OpenSpec capability files with deltas that remove stale named-profile runtime assumptions.
2. Rename or rewrite the dashboard smoke-test references so the practical validation path reads as single-agent.
3. Update the dashboard README and any nearby maintainer docs that still describe “declared profiles” as the runtime surface.
4. Verify the resulting change by checking the generated OpenSpec status and reviewing the diff for scope.

Rollback strategy:
- Revert the cleanup change. No persisted runtime state or deployment migration is involved because the change updates contract text and naming, not the managed image topology itself.

## Open Questions

- None. The runtime behavior being described is already present; this change is only aligning the contract and maintainer-facing naming with that state.
