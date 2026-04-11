## Why

The image runtime is already single-agent, but parts of the repo still describe the old profile-oriented model. That leaves the code, tests, docs, and OpenSpec contract out of sync and makes it harder to tell whether a remaining `profile` reference is intentional compatibility or just stale wording.

## What Changes

- Update stale OpenSpec requirements that still describe named-profile runtime behavior where the image now has one managed agent.
- Remove profile-fleet language from the remaining runtime health, gateway, and feed-persistence contracts so they match the current single-agent image.
- Rename or rewrite profile-era validation/docs references that now exercise or describe the single-agent dashboard/runtime contract.
- Keep the change scoped to contract and naming cleanup; do not introduce new runtime behavior unless a spec fix requires a tiny supporting adjustment.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `agent-workstation-runtime`: remove named-profile gateway and invocation requirements that no longer match the supported image topology.
- `agent-workstation-updates`: replace lingering profile-scoped doctor/gateway wording with the managed single-agent runtime contract.
- `feed-monitoring`: remove named-profile persistence assumptions and keep the contract rooted in the one managed Hermes home.
- `hermes-runtime-state-markers`: rewrite liveness-marker requirements around the single managed gateway service and root `gateway.pid`.

## Impact

- Affected specs: `openspec/specs/agent-workstation-runtime`, `openspec/specs/agent-workstation-updates`, `openspec/specs/feed-monitoring`, and `openspec/specs/hermes-runtime-state-markers`.
- Affected docs/tests: `packages/hermes-dashboard/README.md`, `README.md` references to the dashboard smoke test, and `tests/hermes-image/profiles-dashboard.sh` naming/copy.
- Affected systems: OpenSpec contract clarity, dashboard/test naming, and maintainer-facing documentation for the existing single-agent image.
