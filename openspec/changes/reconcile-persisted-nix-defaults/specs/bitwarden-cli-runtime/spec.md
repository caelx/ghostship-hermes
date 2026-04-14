## MODIFIED Requirements

### Requirement: Hermes image ships the official Bitwarden CLI
The workstation contract SHALL document the official `bws` Bitwarden Secrets Manager CLI as part of the baseline image-managed helper set delivered through the reconciled managed Nix default profile. The runtime docs SHALL still describe its persisted home-state conventions under `/home/hermes`.

#### Scenario: Docs describe the shipped `bws` runtime path
- **WHEN** maintainers inspect the runtime docs
- **THEN** the docs state that `bws` is part of the baseline image-managed helper set
- **AND** the docs describe that `bws` resolves through the managed Nix default profile that is reconciled into persisted `/nix`
- **AND** the docs do not describe `bws` as a downstream-only manual install
