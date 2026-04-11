## Context

The current single-agent image already has the right topology: `ghostship-hermes-gateway.service` is the only managed gateway service, the dashboard points at that service, and the managed Hermes home is rooted at `/home/hermes/.hermes`. The remaining live defect is narrower: the service can be active while `/home/hermes/.hermes/gateway.pid` is absent, which causes downstream status surfaces to report a false negative even though the gateway is actually running.

The repo already encodes `gateway.pid` as the managed liveness contract, and the dashboard test suite expects `has_gateway_pid` to become true when that file exists. The work therefore needs to repair the lifecycle seam where the running gateway process and the liveness marker can drift apart, then lock the fix down with validation.

## Goals / Non-Goals

**Goals:**
- Make the single-agent managed gateway reliably publish `gateway.pid` while the systemd service is active.
- Ensure stale pidfiles are removed on stop and replacement.
- Make operator-facing status surfaces reflect the repaired pidfile contract.
- Add validation that catches pidfile regressions before or immediately after deploy.

**Non-Goals:**
- Rework the dashboard UI or the router-primary model path.
- Change the single-agent topology or introduce new gateway units.
- Solve unrelated auth or provider-health warnings.

## Decisions

### 1. Keep `gateway.pid` as the single source of managed gateway liveness
The fix should preserve `/home/hermes/.hermes/gateway.pid` as the repo-owned liveness contract instead of switching consumers to `gateway_state.json` or raw systemd inspection.

Rationale:
- The dashboard and the existing spec/test surface already key off `gateway.pid`.
- The file is the narrowest integration seam between the running service and operator-facing health checks.
- Replacing every consumer would widen the change without solving the underlying lifecycle drift.

Alternative considered: treat `gateway_state.json` as authoritative. Rejected because it changes the existing contract and still leaves the repo's current dashboard/doctor expectations unsatisfied.

### 2. Make the gateway launcher own pidfile creation, with pre/post lifecycle cleanup around it
The code path that knows the long-running gateway PID should write `gateway.pid`, while pre-start and post-stop hooks should only clear stale state before a new run and after shutdown.

Rationale:
- The active service PID is only trustworthy in the launcher path immediately before `exec`.
- Pre-start cleanup is still useful for crash/replacement recovery, but it should not be the only state owner.
- Post-stop cleanup keeps later health checks from seeing a dead process as live.

Alternative considered: write the pidfile entirely from pre-start. Rejected because pre-start does not own the final long-running process identity.

### 3. Validate the pidfile at both unit-test and image-validation layers
The repo should validate this contract in both the dashboard/runtime tests and the image validation path.

Rationale:
- The regression escaped despite unit-level intent already existing in the dashboard tests.
- Image/runtime validation needs to verify the real built service lifecycle with persisted state.
- Live post-deploy validation should explicitly assert `gateway.pid` presence while the service is active.

Alternative considered: rely only on live validation. Rejected because that would catch regressions too late and make the published image the first integration test again.

## Risks / Trade-offs

- [Launcher changes could write a stale or wrapper PID instead of the effective service PID] → Keep the pidfile write adjacent to the final `exec` path and validate the recorded process against the active unit during tests.
- [Cleanup changes could accidentally remove the pidfile during healthy restarts] → Cover restart/replacement scenarios in the image validation flow rather than only cold boot.
- [Status surfaces might still drift if they add separate service inference later] → Keep the validation focused on the shared pidfile-backed contract and avoid introducing a second liveness source.

## Migration Plan

1. Update the managed gateway launcher/cleanup scripts in the image module.
2. Add or adjust tests so the built runtime proves `gateway.pid` exists while the service is active.
3. Publish a new image and redeploy it to `chill-penguin-root2`.
4. Re-run live validation to confirm:
   - `ghostship-hermes-gateway.service` is active
   - `/home/hermes/.hermes/gateway.pid` exists
   - dashboard `/api/status` reports `has_gateway_pid: true`
   - Hermes health/status surfaces no longer report the gateway as absent when it is running

Rollback is straightforward: revert the launcher/cleanup changes, rebuild, and redeploy the previous image behavior.

## Open Questions

- Is the current missing pidfile caused by the gateway process replacing the wrapper in a way that drops the file, or by some later Hermes-side cleanup during startup?
- Should the live validation harness also assert the pid inside `gateway.pid` matches the active gateway unit's main PID, or is file presence sufficient for the supported contract?
