## 1. Rebase The Runtime Topology

- [ ] 1.1 Replace the multi-profile scaffold in `packages/hermes-image/nixos-module.nix` with one authoritative managed Hermes runtime surface rooted at `/home/hermes/.hermes`
- [ ] 1.2 Remove the repo-owned profile matrix, default-profile logic, profile bootstrap loops, and profile-specific path generation from the image module
- [ ] 1.3 Converge the managed config defaults, fallback model, auxiliary overrides, browser defaults, Discord defaults, display defaults, and other shared settings onto the single managed agent config

## 2. Converge Managed State, Env, Skills, And SOUL

- [ ] 2.1 Replace per-profile `.env` generation with one managed `.env` contract at the root managed Hermes home
- [ ] 2.2 Replace profile-specific Discord, webhook, and browser CDP source mapping with the hard-break single-agent env contract built on generic names only
- [ ] 2.3 Replace shared-plus-profile skill seeding with the root-only seed layout under `/home/hermes/seeds/skills` plus `/home/hermes/seeds/SOUL.md`
- [ ] 2.4 Verify bootstrap copies seeded skills and `SOUL.md` into the intended managed runtime destinations under `/home/hermes/.hermes`
- [ ] 2.5 Converge auth, `gateway.pid`, and other runtime-owned state paths onto the single managed agent layout
- [ ] 2.6 Implement the destructive managed-state reset so old profile-based Hermes state is deleted before the new single-agent runtime is reinitialized

## 3. Replace Gateway Supervision And Health Contracts

- [ ] 3.1 Replace the three repo-owned `ghostship-hermes-profile-*` services with one managed gateway service and one restart/watch contract
- [ ] 3.2 Update managed gateway status, restart guidance, and liveness marker handling to match the single-agent service model
- [ ] 3.3 Update router ordering, webhook wiring, and doctor/health assumptions so the single managed gateway boots cleanly and reports correct status

## 4. Rewrite Dashboard And Browser Runtime Surfaces

- [ ] 4.1 Update the dashboard backend status model in `packages/hermes-dashboard/src/hermes_dashboard/app.py` to report one managed agent instead of profile topology
- [ ] 4.2 Update the dashboard frontend UI so the browser surface uses single-agent terminology and layout
- [ ] 4.3 Remove the profile-oriented dashboard API contract and replace profile-specific tests and API expectations with single-agent assertions

## 5. Update Validation And Persistence Coverage

- [ ] 5.1 Rewrite `tests/hermes-image/profiles-dashboard.sh` for the single-agent runtime contract, including status, terminal, router, and managed gateway assertions
- [ ] 5.2 Rewrite `scripts/validate_workstation_persistence.sh` for the new root-managed paths, env file, skills, SOUL, auth, and liveness-marker behavior
- [ ] 5.3 Add or update verification that persisted installs survive replacement without reviving removed profile assumptions

## 6. Overhaul Documentation And Operator Guidance

- [ ] 6.1 Rewrite `README.md` so the runtime model, path layout, systemd graph, env contract, dashboard behavior, and operator workflows all describe one managed Hermes agent
- [ ] 6.2 Rewrite `docs/nix-setup.md` and any affected package docs so managed mode, runtime paths, and gateway guidance no longer describe named-profile behavior
- [ ] 6.3 Update `CHANGELOG.md` and supporting documentation to record the breaking removal of the multi-profile topology and the move to one profile, one skill tree, and one `SOUL.md`

## 7. Finalize The Spec And Repository Contract

- [ ] 7.1 Verify all OpenSpec deltas remain consistent with the implemented runtime, dashboard, validation, and docs behavior
- [ ] 7.2 Run the relevant repo checks or smoke validations for the single-agent runtime and capture any follow-up fixes needed before apply is considered complete
- [ ] 7.3 Prepare the change for implementation review with a clean diff across specs, runtime code, validation, and documentation surfaces
