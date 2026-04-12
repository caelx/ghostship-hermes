## ADDED Requirements

### Requirement: Managed tooling convergence is no-op on steady-state reruns
The managed user-tooling refresh SHALL leave an already-converged managed profile and npm tool tree in place instead of rebuilding it on every run.

#### Scenario: Immediate rerun skips destructive profile churn
- **WHEN** `ghostship-hermes-user-tooling.service` runs again after a successful convergence with no managed-tooling drift
- **THEN** it does not remove and re-add the same managed Nix profile entries
- **AND** it does not perform npm dependency installation work solely because the service ran again

### Requirement: Managed tooling refresh repairs only actual drift
The managed user-tooling refresh SHALL mutate only the managed entries or shims that are missing, stale, or no longer match the declared runtime contract.

#### Scenario: One drifted managed profile entry is repaired without rebuilding the rest
- **WHEN** exactly one declared managed Nix profile entry drifts from the approved runtime contract
- **THEN** the next managed user-tooling convergence repairs that drifted entry
- **AND** it leaves the other already-converged managed profile entries untouched

#### Scenario: Stale managed shim is removed without disturbing valid runtime tools
- **WHEN** a stale managed shim under `/home/hermes/.local/bin` points at an outdated managed npm or profile tool path
- **THEN** the next managed user-tooling convergence removes or rewrites that stale shim
- **AND** it does not remove unrelated valid shims or re-install unaffected managed tools
