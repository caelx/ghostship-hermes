## MODIFIED Requirements

### Requirement: Hermes image ships the GitHub and OpenSSH client CLIs
The workstation contract SHALL document `gh` as part of the baseline image-managed helper set delivered through the reconciled managed Nix default profile, while `ssh`, `scp`, and `ssh-keygen` remain available from the immutable OS layer.

#### Scenario: Docs describe the shipped GitHub CLI runtime path
- **WHEN** maintainers inspect the runtime docs
- **THEN** the docs state that `gh` is part of the baseline image-managed helper set
- **AND** the docs describe that `gh` resolves through the managed Nix default profile that is reconciled into persisted `/nix`
- **AND** the docs keep the OpenSSH client tools documented as immutable OS-layer tools rather than downstream-only installs
