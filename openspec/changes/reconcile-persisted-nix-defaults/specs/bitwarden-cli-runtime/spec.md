## MODIFIED Requirements

### Requirement: Hermes image ships the official Bitwarden CLI
The workstation contract SHALL document the official `bw` Bitwarden Password Manager CLI as part of the baseline image-managed helper set delivered through the reconciled managed Nix default profile. The runtime docs SHALL still describe its persisted home-state convention under `/home/hermes/.local/state/bitwarden-cli`.

#### Scenario: Docs describe the shipped `bw` runtime path
- **WHEN** maintainers inspect the runtime docs
- **THEN** the docs state that `bw` is part of the baseline image-managed helper set
- **AND** the docs describe that `bw` resolves through the managed Nix default profile that is reconciled into persisted `/nix`
- **AND** the docs do not describe `bw` as a downstream-only manual install
