## 1. Persisted Release Marker

- [x] 1.1 Update the managed runtime bootstrap to refresh `/home/hermes/.ghostship-hermes-release` from `/etc/ghostship-hermes-release` on every boot.
- [x] 1.2 Add or update validation so reused `/home/hermes` state is checked against the booted image release marker after replacement or restart.

## 2. Managed Gateway PID Contract

- [x] 2.1 Update the repo-owned managed profile gateway service lifecycle to clear stale `gateway.pid` files before start and after stop.
- [x] 2.2 Update the managed gateway wrapper flow so each profile writes a live `gateway.pid` that matches the long-running Hermes gateway process.
- [x] 2.3 Add validation that managed gateway marker files align with the live `assistant`, `operations`, and `supervisor` gateway services and stop producing false-negative health results.

## 3. Managed Profile Env Refresh

- [x] 3.1 Tighten the bootstrap `.env` rewrite path so current Discord env is projected into each managed profile `.env` whenever those container env vars are present.
- [x] 3.2 Add regression coverage or validation for the rewritten profile `.env` contract, including removal of stale projected Discord values when the source env is absent.

## 4. Documentation And Release Notes

- [x] 4.1 Update the relevant runtime documentation to describe the authoritative image release marker and the persisted home mirror behavior.
- [x] 4.2 Update CHANGELOG and any affected operator notes to call out the managed gateway pidfile fix and runtime-state marker repair.
