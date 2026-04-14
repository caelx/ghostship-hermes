## MODIFIED Requirements

### Requirement: Hermes image ships a pinned Google Workspace CLI
The workstation contract SHALL treat the upstream `gws` executable as part of the baseline image-managed helper set delivered through the reconciled managed Nix default profile, and that packaged runtime SHALL remain sourced from a pinned upstream revision rather than an ad hoc runtime download.

#### Scenario: Docs describe the shipped `gws` runtime path
- **WHEN** maintainers inspect the runtime docs
- **THEN** the docs state that `gws` is part of the baseline image-managed helper set
- **AND** the docs describe that `gws` resolves through the managed Nix default profile that is reconciled into persisted `/nix`
- **AND** the docs do not describe `gws` as a downstream-only manual install

#### Scenario: Upstream revision remains pinned in repo wiring
- **WHEN** maintainers inspect the repo package wiring for the baseline `gws` tool
- **THEN** the `gws` package source resolves from a pinned upstream revision
- **AND** the baseline workstation contract does not depend on an ad hoc runtime download to provide it
