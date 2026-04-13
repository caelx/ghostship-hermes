## MODIFIED Requirements

### Requirement: Managed `.env` changes remain visible to service restart wiring
The Hermes image SHALL keep supported runtime env in `/home/hermes/.hermes/.env` so bootstrap rewrites and operator edits both remain the file-level change surface for managed gateway restart wiring, while other mutable managed state files do not inherit restart behavior merely because they live under the same home.

#### Scenario: Bootstrap rewrite stays on the watched `.env` path
- **WHEN** managed bootstrap refreshes `/home/hermes/.hermes/.env` with changed supported runtime env
- **THEN** the rewrite occurs at the same managed `.env` path already watched by the repo-owned restart unit
- **AND** the managed gateway continues to load its operator-facing runtime env from that `.env` path

#### Scenario: Managed gateway restart reads the rewritten `.env`
- **WHEN** the managed gateway is restarted after `/home/hermes/.hermes/.env` changes
- **THEN** the restarted service reads the rewritten managed `.env` through the existing `EnvironmentFile` contract
- **AND** the runtime does not require hidden service-only env overrides to restore supported configuration

#### Scenario: Non-env managed state does not become restart-triggering through the env contract
- **WHEN** `/home/hermes/.hermes/auth.json` or `/home/hermes/.hermes/SOUL.md` changes without a concurrent `.env` or `config.yaml` change
- **THEN** the managed env restart contract does not treat that state change as a gateway restart trigger
- **AND** the runtime preserves `.env` as the operator-facing restart surface for supported runtime env
