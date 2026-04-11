## 1. OpenSpec Contract Cleanup

- [ ] 1.1 Update the active `agent-workstation-runtime` spec text so runtime invocation, browser wording, and gateway guidance no longer describe named-profile behavior.
- [ ] 1.2 Update the active `agent-workstation-updates` spec text so doctor/status wording refers to the single managed runtime and gateway.
- [ ] 1.3 Update the active `feed-monitoring` and `hermes-runtime-state-markers` specs so feed persistence and `gateway.pid` behavior are rooted in `/home/hermes/.hermes` without named-profile assumptions.

## 2. Docs And Validation Naming Cleanup

- [ ] 2.1 Update the dashboard package README so the home view describes the managed single-agent runtime instead of declared profiles.
- [ ] 2.2 Rename or rewrite the dashboard smoke-test path and nearby README references so the test name reflects the single-agent dashboard/runtime contract.
- [ ] 2.3 Review the touched maintainer-facing docs for nearby profile-era wording introduced by the renamed smoke-test path and fix those references in the same change.

## 3. Verification

- [ ] 3.1 Review the final diff to confirm the change stays scoped to contract, docs, and test naming cleanup rather than introducing new runtime behavior.
- [ ] 3.2 Run the relevant OpenSpec status/check commands and verify the change artifacts remain apply-ready after the cleanup edits.
